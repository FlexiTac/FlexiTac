#!/usr/bin/env python3
"""Run the local deterministic Tactile FPC Customizer web application.

This server intentionally uses only Python's standard library.  It binds to
localhost by default, serves no telemetry, and has no chatbot or cloud API
dependency.  The only design-generation boundary is ``engine.generate_design``.

Routes: ``GET /``, ``/static/*``, ``/api/default``, ``/api/schema``;
``POST /api/validate``, ``/api/generate[?view=compact]``,
``/api/export/{project,top-gerber,bottom-gerber,easyeda-pro}`` and the CAD-mode routes
``/api/surface/{inspect,select,fit,map}`` (a framed body: JSON header plus
mesh bytes, see ``surface.api``).  Every failure is answered with
``{"ok": false, "code": ..., "error": ...}`` JSON; nothing is answered with
an empty reply.

The answers themselves need no HTTP (``answer``): the static site
(``tools/build_static_site.py``) imports this module in the browser with
Pyodide and serves the same replies to the page without a server.
"""

from __future__ import annotations

import argparse
import errno
import io
import ipaddress
import json
import mimetypes
import re
import socket
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import parse_qsl, urlsplit

from engine import (
    BuildCache,
    DesignJSONError,
    check_design,
    default_design,
    design_schema,
    generate_design,
    input_limits,
    issue_codes,
    load_design_json,
    load_profile,
    result_view,
)
from engine.core import SURFACE_TEMPLATE_ID, TEMPLATE_ID, TEMPLATE_VERSIONS
from engine.schema import row_bus_profile
from engine.profile import ProfileError, copper_weight_oz, fabrication_minimum, order_requirements
from exporters import ExportError, artifact_filenames, build_easyeda_exports, build_exports, easyeda_filenames
from surface import api as surface_api
from surface.errors import SURFACE_ERROR_CODES, SurfaceError


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
MAX_REQUEST_BYTES = 128 * 1024
# CAD mode: a surface request carries the whole mesh (STL) next to its JSON header.
MAX_SURFACE_BYTES = 64 * 1024 * 1024
SURFACE_CONTENT_TYPE = "application/x-tactile-surface"
# Unread request bytes discarded before closing, so the reply is not lost to a TCP reset.
MAX_DRAIN_BYTES = 1024 * 1024
MAX_DRAIN_S = 2
SOCKET_TIMEOUT_S = 30
# A whole request (line, headers and body) must arrive within this, however slowly it trickles in.
REQUEST_DEADLINE_S = 60
MAX_CONCURRENT_GENERATIONS = 2
# CAD-mode requests run in their own slot, so they never hold up the rectangular mode.
MAX_CONCURRENT_SURFACE = 1
# A surface body this far over its limit is still read and dropped after the 413.
MAX_SURFACE_DRAIN_BYTES = MAX_SURFACE_BYTES
MAX_SURFACE_DRAIN_S = 10
RETRY_AFTER_S = 1
BUILD_CACHE_SIZE = 16
LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "[::1]")
SECURITY_HEADERS = (
    ("X-Content-Type-Options", "nosniff"),
    (
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "base-uri 'none'; form-action 'self'",
    ),
    ("Referrer-Policy", "no-referrer"),
    ("Cache-Control", "no-store"),
)
EXPORT_ROUTES = {
    "/api/export/project": "project_review_bundle_zip",
    "/api/export/top-gerber": "top_fpc_gerber_zip",
    "/api/export/bottom-gerber": "bottom_fpc_gerber_zip",
}
# The EasyEDA Pro projects (exporters/easyeda_pro.py): an archive of its own, so the three above keep their bytes.
EASYEDA_ROUTES = {"/api/export/easyeda-pro": "easyeda_pro_zip"}
# Fixed types for the UI's own files: on Windows mimetypes reads the registry, which
# can map .js to text/plain, and browsers refuse such a script under nosniff.
STATIC_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}
SURFACE_ROUTES = {
    "/api/surface/inspect": surface_api.inspect,
    "/api/surface/select": surface_api.select_surface,
    "/api/surface/fit": surface_api.fit,
    "/api/surface/map": surface_api.map_placement,
}
POST_ROUTES = frozenset({"/api/validate", "/api/generate", *EXPORT_ROUTES, *EASYEDA_ROUTES, *SURFACE_ROUTES})
GET_ROUTES = frozenset({"/", "/index.html", "/api/default", "/api/schema"})
QUERY_PARAMETERS = {
    "/api/generate": {"view": ("full", "compact")},
    # The design template whose defaults and profile the form uses (CAD mode: the surface template).
    "/api/default": {"template": tuple(TEMPLATE_VERSIONS)},
}
TEMPLATE_NAMES = {TEMPLATE_ID: "Generic Matrix v1", SURFACE_TEMPLATE_ID: "Surface Matrix v1"}
# Error codes of the HTTP layer; engine issue codes are listed by /api/schema.
HTTP_ERROR_CODES = {
    "E_HTTP_BAD_REQUEST": "400: malformed request line, header or query parameter; a missing (HTTP/1.1), duplicate or malformed Host.",
    "E_HTTP_INVALID_JSON": "400: the body is not strict UTF-8 JSON (NaN/Infinity, duplicate keys, too deep, number too long).",
    "E_HTTP_BODY_NOT_OBJECT": "400: the body is empty or not a JSON object.",
    "E_HTTP_CONTENT_LENGTH": "400: malformed, duplicate or short Content-Length.",
    "E_HTTP_FORBIDDEN_ORIGIN": "403: a POST from another origin (not http:// or https:// of its Host, nor an --allow-host name).",
    "E_HTTP_NOT_FOUND": "404: unknown route or static file.",
    "E_HTTP_METHOD_NOT_ALLOWED": "405: the route exists for other methods (see Allow).",
    "E_HTTP_TIMEOUT": f"408: the request stalled for {SOCKET_TIMEOUT_S} s or was not complete within {REQUEST_DEADLINE_S} s.",
    "E_HTTP_LENGTH_REQUIRED": "411: a POST body without Content-Length (chunked uploads are not supported).",
    "E_HTTP_BODY_TOO_LARGE": f"413: the body exceeds {MAX_REQUEST_BYTES} bytes ({MAX_SURFACE_BYTES} bytes on the surface routes).",
    "E_HTTP_URI_TOO_LONG": "414: request line too long.",
    "E_HTTP_UNSUPPORTED_MEDIA_TYPE": f"415: a POST whose Content-Type is not application/json (UTF-8), or not {SURFACE_CONTENT_TYPE} on the surface routes.",
    "E_HTTP_MISDIRECTED_HOST": "421: Host is not a loopback name, the configured --host or an --allow-host name.",
    "E_EXPORT_BLOCKED": "422: the design does not validate; the reply carries validation.",
    "E_EXPORT_FAILED": "422: the exporter rejected the generated geometry.",
    "E_SURFACE": "422: a surface route rejected the mesh, the selection or the fit; the reply's code is one of x-surface-error-codes.",
    "E_HTTP_HEADERS_TOO_LARGE": "431: too many or too long header lines.",
    "E_INTERNAL": "500: unexpected server error (details are in the server log).",
    "E_PROFILE_INVALID": "500: the bundled manufacturing profile is inconsistent.",
    "E_HTTP_NOT_IMPLEMENTED": "501: unsupported method.",
    "E_HTTP_BUSY": f"503: {MAX_CONCURRENT_GENERATIONS} generations (or {MAX_CONCURRENT_SURFACE} surface request) are running; retry after Retry-After seconds.",
    "E_HTTP_VERSION_NOT_SUPPORTED": "505: unsupported HTTP version.",
}
_STATUS_CODES = {
    400: "E_HTTP_BAD_REQUEST", 404: "E_HTTP_NOT_FOUND", 408: "E_HTTP_TIMEOUT", 414: "E_HTTP_URI_TOO_LONG",
    431: "E_HTTP_HEADERS_TOO_LARGE", 500: "E_INTERNAL", 501: "E_HTTP_NOT_IMPLEMENTED", 505: "E_HTTP_VERSION_NOT_SUPPORTED",
}
_CONTENT_LENGTH = re.compile(r"[0-9]{1,16}\Z")
# Host = uri-host [":" port] (RFC 9110 section 7.2, RFC 3986 section 3.2.2).
_HOST = re.compile(r"(?:\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9\-._~!$&'()*+,;=%]*)(?::[0-9]*)?\Z")
# --allow-host NAME: a DNS name or IPv4 address; a leading dot also allows the subdomains.
_ALLOW_HOST = re.compile(r"\.?[a-z0-9_-]+(?:\.[a-z0-9_-]+)*\Z")
_ABSOLUTE_TARGET = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://")
# Control characters are escaped in log lines (as CPython 3.12 does).
_LOG_ESCAPES = {code: f"\\x{code:02x}" for code in (*range(0x20), *range(0x7F, 0xA0))}
_LOG_ESCAPES[ord("\\")] = "\\\\"
_TRACEBACK_ESCAPES = {code: text for code, text in _LOG_ESCAPES.items() if code != ord("\n")}


def profile_for_ui(profile: Mapping[str, Any] | None = None, template_id: str = TEMPLATE_ID) -> dict[str, Any]:
    """Locked rules for the UI: display text, form limits, issue codes and the
    JLCPCB order requirements (the manufacturing note), all from the profile
    of the design template (the generic one by default).

    The generic template builds its diagonal Row bus with the surface profile
    (``engine.core.rules_template``): ``row_bus`` names that profile and its
    display rules, and the limits are the bus's where they differ, with the
    straight Row channel's under each field's ``channel``
    (``engine.input_limits``); the browser shows the ones of its Row traces.
    """

    profile = load_profile(template_id) if profile is None else profile
    answer = {
        "id": profile["id"],
        "revision": profile["revision"],
        "name": f"{TEMPLATE_NAMES[template_id]} · {profile['id']} ({profile['revision']})",
        "display_rules": display_rules(profile, default_design(template_id)),
        "limits": input_limits(profile),
        "issue_codes": issue_codes(),
        "order_requirements": order_requirements(profile, default_design(template_id)),
    }
    bus = row_bus_profile(profile)
    if bus is not None:
        answer["row_bus"] = {
            "id": bus["id"],
            "revision": bus["revision"],
            "name": f"{TEMPLATE_NAMES[template_id]} · diagonal Row bus: {bus['id']} ({bus['revision']})",
            "display_rules": display_rules(bus, default_design(template_id)),
        }
    return answer


def display_rules(profile: Mapping[str, Any], design: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Short human-readable rule summary generated from the locked profile.

    The bundle traces are a design input: their width and spacing come from
    ``design`` (the default design when ``None``), the finger width and
    JLCPCB's minimum from the profile.
    """

    stackup = profile["stackup"]
    routing = profile["routing"]
    connector = profile["connector"]
    coverlay = profile["coverlay"]
    fanout = profile["fanout"]
    limits = profile["limits"]
    bundle = (design or default_design())["routing"]
    per_lane = int(fanout["maximum_channels_per_lane"])
    lanes = int(fanout["maximum_lanes"])
    columns = min(int(limits["maximum_columns"]), lanes * per_lane)
    fan_out = f"≤{per_lane}: one lane"
    if lanes > 1 and columns > per_lane:
        fan_out += f" · {per_lane + 1}–{columns}: {lanes} lanes → one connector"
    minimum_width, minimum_space = fabrication_minimum(profile)
    width, space = float(bundle["trace_width_mm"]), float(bundle["trace_space_mm"])
    return {
        "Copper construction": (
            f"{stackup['construction'].replace('_', ' ')} · {stackup['copper_layer'].replace('_', ' ')} "
            f"{stackup['copper_thickness_mm']:.3f} mm"
        ),
        # The browser shows the generated design's values in this entry.
        "Bundle traces": f"{_mm(width)} / {_mm(space)} mm width / spacing (pitch {_mm(width + space)} mm)",
        "Bundle range": (
            f"width {_mm(limits['minimum_trace_width_mm'])}–{_mm(limits['maximum_trace_width_mm'])} mm · "
            f"spacing {_mm(limits['minimum_trace_space_mm'])}–{_mm(limits['maximum_trace_space_mm'])} mm"
        ),
        "Gold-finger traces": (
            f"{_mm(routing['finger_trace_width_mm'])} mm at the {_mm(connector['pad_pitch_mm'])} mm contact pitch, "
            "widened below every fan-out bend"
        ),
        "JLC trace minimum": (
            f"{_mm(minimum_width)} / {_mm(minimum_space)} mm for {copper_weight_oz(profile):g} oz copper "
            f"({round(minimum_width / 0.0254, 2):g}/{round(minimum_space / 0.0254, 2):g} mil) · "
            f"width ±{profile['fabrication']['trace_width_tolerance_fraction'] * 100:g}%"
        ),
        "Connector": (
            f"{connector['pad_pitch_mm']:.1f} mm pitch ZIF · {connector['pad_width_mm']:.2f} × "
            f"{connector['contact_length_mm']:.2f} mm contacts · up to {connector['maximum_pins']} pins"
        ),
        "Column fan-out": fan_out,
        "Copper to edge": f"≥ {routing['copper_to_edge_mm']:.2f} mm (slots ≥ {routing['copper_to_cutout_mm']:.2f} mm)",
        "Coverlay": (
            f"{stackup['coverlay']} {stackup['coverlay_thickness_mm']:.3f} mm · {coverlay['coverlay_expansion_mm']:.2f} mm "
            f"expansion · bridges ≥ {coverlay['coverlay_min_bridge_mm']:.2f} mm"
        ),
        "PI stiffener": (
            f"{stackup['stiffener_side'].capitalize()} {stackup['stiffener_material']} · "
            f"{stackup['stiffener_thickness_mm']:.3f} mm · {profile['tail']['stiffener_length_mm']:.1f} mm connector zone"
        ),
        "Board size limit": f"{limits['maximum_outline_short_side_mm']:g} × {limits['maximum_outline_long_side_mm']:g} mm",
    }


def _mm(value: float) -> str:
    """A length on the 1e-6 mm grid with at least three decimals (as the browser shows it)."""

    whole, _, fraction = f"{round(float(value), 6):.6f}".rstrip("0").partition(".")
    return f"{whole}.{fraction.ljust(3, '0')}"


def api_schema() -> dict[str, Any]:
    """The design JSON Schema plus the HTTP layer's error codes."""

    schema = design_schema()
    schema["x-http-error-codes"] = dict(HTTP_ERROR_CODES)
    schema["x-surface-error-codes"] = dict(SURFACE_ERROR_CODES)
    return schema


# -- the API's answers, without HTTP -----------------------------------------------
# AppHandler sends them; the static site's worker (web/py/worker.js) runs
# ``answer`` in the browser (Pyodide) and hands the page the same replies.


@dataclass(frozen=True)
class Reply:
    status: int
    content_type: str
    body: bytes
    headers: tuple[tuple[str, str], ...] = ()


def json_reply(status: int, payload: Any, headers: Iterable[tuple[str, str]] = ()) -> Reply:
    body = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    return Reply(int(status), "application/json; charset=utf-8", body, tuple(headers))


def error_reply(status: int, code: str, message: str, *, headers: Iterable[tuple[str, str]] = (), **extra: Any) -> Reply:
    return json_reply(status, {"ok": False, "code": code, "error": message, **extra}, headers)


def wrong_method(path: str) -> Reply:
    """405 (with Allow) for a route used with another method, else 404."""

    if path in POST_ROUTES:
        allow = "POST"
    elif path in GET_ROUTES or path.startswith("/static/"):
        allow = "GET, HEAD"
    else:
        return error_reply(HTTPStatus.NOT_FOUND, "E_HTTP_NOT_FOUND", "Route not found.")
    return error_reply(HTTPStatus.METHOD_NOT_ALLOWED, "E_HTTP_METHOD_NOT_ALLOWED", f"Use {allow} for this route.", headers=(("Allow", allow),))


def query_values(path: str, query: str) -> dict[str, str] | Reply:
    """Query parameters of an API route (unknown names or values are a 400)."""

    allowed = QUERY_PARAMETERS.get(path, {})
    try:
        pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=bool(query), max_num_fields=len(allowed) or None)
    except ValueError:
        pairs = None
    values = dict(pairs or ())
    if pairs is None or len(values) != len(pairs) or any(name not in allowed or value not in allowed[name] for name, value in values.items()):
        choices = "; ".join(f"{name}={'|'.join(options)}" for name, options in allowed.items()) or "none"
        return error_reply(HTTPStatus.BAD_REQUEST, "E_HTTP_BAD_REQUEST", f"Unsupported query parameters; accepted: {choices}.")
    return values


def json_type_refused(content_type: str) -> Reply | None:
    """The 415 for a body not sent as application/json (UTF-8), else None."""

    media_type, _, parameters = content_type.partition(";")
    charset = dict(
        (name.strip().lower(), item.strip().strip('"').lower()) for name, _, item in (part.partition("=") for part in parameters.split(";") if part.strip())
    ).get("charset", "utf-8")
    if media_type.strip().lower() != "application/json" or charset not in ("utf-8", "utf8"):
        return error_reply(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "E_HTTP_UNSUPPORTED_MEDIA_TYPE", "POST bodies must be sent as Content-Type: application/json (UTF-8).")
    return None


def json_payload(body: bytes) -> dict[str, Any] | Reply:
    """The design a JSON body carries, or the 400 for a body that is not one JSON object."""

    if not body.strip():
        return error_reply(HTTPStatus.BAD_REQUEST, "E_HTTP_BODY_NOT_OBJECT", "A JSON object body (the design) is required.", field="$")
    try:
        payload = load_design_json(body)
    except DesignJSONError as error:
        return error_reply(HTTPStatus.BAD_REQUEST, "E_HTTP_INVALID_JSON", f"The request body is not strict JSON: {error}", field="$")
    if not isinstance(payload, dict):
        return error_reply(HTTPStatus.BAD_REQUEST, "E_HTTP_BODY_NOT_OBJECT", "The request body must be a JSON object (the design).", field="$")
    return payload


def get_reply(path: str, values: Mapping[str, str]) -> Reply:
    """GET /api/default[?template=] or /api/schema."""

    if path == "/api/default":
        template = values.get("template", TEMPLATE_ID)
        return json_reply(HTTPStatus.OK, {"design": default_design(template), "profile": profile_for_ui(template_id=template)})
    return json_reply(HTTPStatus.OK, api_schema())


def design_reply(path: str, options: Mapping[str, str], payload: dict[str, Any], cache: BuildCache | None = None) -> Reply:
    """POST /api/validate, /api/generate or an export route for the design ``payload``."""

    if path == "/api/validate":
        return json_reply(HTTPStatus.OK, check_design(payload))
    result = generate_design(payload, cache=cache)
    if path == "/api/generate":
        return json_reply(HTTPStatus.OK, result_view(result, options.get("view", "full")))
    if result["ok"] is not True:
        return error_reply(
            HTTPStatus.UNPROCESSABLE_ENTITY, "E_EXPORT_BLOCKED", "Export is blocked by geometry validation.",
            validation=result["validation"], manifest=result["manifest"],
        )
    try:
        if path in EXPORT_ROUTES:
            # The exporter checks the result against the engine's generation of
            # its build, which the cache already holds (D16, D17).
            key, artifacts = EXPORT_ROUTES[path], build_exports(result, cache=cache)
            # The exporter's names, which its review manifest records (D17).
            names = artifact_filenames(result)
        else:
            key, artifacts = EASYEDA_ROUTES[path], build_easyeda_exports(result, cache=cache)
            names = easyeda_filenames(result)
    except ExportError as error:
        return error_reply(HTTPStatus.UNPROCESSABLE_ENTITY, "E_EXPORT_FAILED", str(error))
    manifest = result["manifest"]
    return Reply(
        int(HTTPStatus.OK),
        "application/zip",
        artifacts[key],
        (
            ("Content-Disposition", f'attachment; filename="{names[key]}"'),
            ("X-Build-Id", manifest["build_id"]),
            ("X-Design-Sha256", manifest["design_sha256"]),
        ),
    )


def surface_type_refused(content_type: str) -> Reply | None:
    """The 415 for a surface body not sent as SURFACE_CONTENT_TYPE, else None."""

    media_type = content_type.partition(";")[0].strip().lower()
    if media_type != SURFACE_CONTENT_TYPE:
        return error_reply(
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "E_HTTP_UNSUPPORTED_MEDIA_TYPE",
            f"Surface requests must be sent as Content-Type: {SURFACE_CONTENT_TYPE} (a framed JSON header and mesh).",
        )
    return None


def surface_request(body: bytes) -> tuple[dict[str, Any], bytes] | Reply:
    """The JSON header and the mesh of a framed surface body, or the 422 for a malformed one."""

    try:
        header_bytes, mesh_bytes = surface_api.split_body(body)
        try:
            header = load_design_json(header_bytes)
        except DesignJSONError as error:
            raise SurfaceError("E_SURFACE_REQUEST", f"The JSON header is not strict JSON: {error}") from error
        if not isinstance(header, dict):
            raise SurfaceError("E_SURFACE_REQUEST", "The JSON header must be an object.")
    except SurfaceError as error:
        return surface_refused(error)
    return header, mesh_bytes


def surface_reply(path: str, header: dict[str, Any], mesh: bytes, cache: BuildCache | None = None) -> Reply:
    """A CAD-mode route (``surface.api``) for a parsed request, answered as JSON."""

    try:
        return json_reply(HTTPStatus.OK, SURFACE_ROUTES[path](header, mesh, cache=cache))
    except SurfaceError as error:
        return surface_refused(error)


def surface_refused(error: SurfaceError) -> Reply:
    return error_reply(HTTPStatus.UNPROCESSABLE_ENTITY, error.code, error.message, **({"details": error.details} if error.details else {}))


def answer(method: str, target: str, content_type: str = "", body: bytes = b"", cache: BuildCache | None = None) -> Reply:
    """One API request without HTTP: the static site's worker hands every request
    of the page here.  Routes, checks and replies are the server's; what only
    a connection has (Host, Origin, Content-Length, time limits, the busy
    slots: the worker answers one request at a time) is left out.  The page and
    its files are the site's own, so only /api/ routes are answered."""

    path, _, query = target.split("#", 1)[0].partition("?")
    if not path.startswith("/api/"):
        return error_reply(HTTPStatus.NOT_FOUND, "E_HTTP_NOT_FOUND", "Route not found.")
    if method == "GET" and path in GET_ROUTES:
        values = query_values(path, query)
        return values if isinstance(values, Reply) else get_reply(path, values)
    if method != "POST" or path not in POST_ROUTES:
        return wrong_method(path)
    options = query_values(path, query)
    if isinstance(options, Reply):
        return options
    surface = path in SURFACE_ROUTES
    refused = surface_type_refused(content_type) if surface else json_type_refused(content_type)
    if refused is not None:
        return refused
    limit = MAX_SURFACE_BYTES if surface else MAX_REQUEST_BYTES
    if len(body) > limit:
        return error_reply(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "E_HTTP_BODY_TOO_LARGE", f"The request body exceeds {limit} bytes.")
    if surface:
        request = surface_request(body)
        return request if isinstance(request, Reply) else surface_reply(path, *request, cache=cache)
    payload = json_payload(body)
    return payload if isinstance(payload, Reply) else design_reply(path, options, payload, cache)


class AppServer(ThreadingHTTPServer):
    """Threaded server with a deeper listen backlog, an allow-list of Host
    names, a bounded number of concurrent generations and a build cache.

    ``allow_hosts`` are further Host names (``--allow-host``) for a tunnel, a
    proxy or a LAN name; ``.example.com`` allows the domain and its
    subdomains.  Pages served under these names may also post from them
    when a proxy rewrites the Host header."""

    request_queue_size = 64
    daemon_threads = True

    def __init__(self, address: tuple[str, int], handler: type | None = None, allow_hosts: Iterable[str] = ()) -> None:
        extra = {_allow_host_argument(name) for name in allow_hosts}  # checked before binding
        self.address_family = _address_family(address[0])
        super().__init__(address, handler or AppHandler)
        self.extra_hosts = frozenset(name for name in extra if not name.startswith("."))
        self.extra_domains = frozenset(name[1:] for name in extra if name.startswith("."))
        # The configured name and the address actually bound (e.g. 127.000.000.002 binds 127.0.0.2).
        bound = (_bind_host_name(address[0]), _bind_host_name(self.server_address[0]))
        self.allowed_hosts = frozenset({*LOOPBACK_HOSTS, *bound, *self.extra_hosts})
        self.generation_slots = threading.BoundedSemaphore(MAX_CONCURRENT_GENERATIONS)
        self.surface_slots = threading.BoundedSemaphore(MAX_CONCURRENT_SURFACE)
        self.build_cache = BuildCache(BUILD_CACHE_SIZE)

    def host_allowed(self, name: str) -> bool:
        name = _bind_host_name(name)  # an IP literal in one notation, however the client wrote it
        return name in self.allowed_hosts or self.extra_host(name)

    def extra_host(self, name: str) -> bool:
        """Whether ``name`` is an ``--allow-host`` name or under an ``--allow-host`` domain."""

        name = _bind_host_name(name)
        return name in self.extra_hosts or any(name == domain or name.endswith("." + domain) for domain in self.extra_domains)

    def handle_error(self, request: Any, client_address: Any) -> None:
        error = sys.exc_info()[1]
        if isinstance(error, (ConnectionError, socket.timeout)):
            return  # the client went away or stalled; nothing useful to log
        sys.stderr.write("[tactile-fpc] connection error\n" + traceback.format_exc().translate(_TRACEBACK_ESCAPES))


def make_server(host: str = "127.0.0.1", port: int = 8008, allow_hosts: Iterable[str] = ()) -> AppServer:
    return AppServer((host, port), allow_hosts=allow_hosts)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "TactileFPC"
    timeout = SOCKET_TIMEOUT_S
    request_deadline = REQUEST_DEADLINE_S

    # -- request lifecycle ---------------------------------------------------

    def setup(self) -> None:
        super().setup()
        # Requests are read through a reader that also enforces request_deadline.
        self.rfile.close()
        self._reader = _DeadlineReader(self.connection, self.timeout)
        self.rfile = io.BufferedReader(self._reader)

    def handle_one_request(self) -> None:
        self._response_started = False
        self._unread_body = False
        self._drain = (MAX_DRAIN_BYTES, MAX_DRAIN_S)
        self._authority = None
        self._reader.deadline = None
        self.connection.settimeout(self.timeout)
        try:
            if not self.connection.recv(1, socket.MSG_PEEK):
                self.close_connection = True  # closed without a request
                return
        except socket.timeout:
            self.close_connection = True  # an idle connection: nothing to answer
            return
        self._reader.deadline = time.monotonic() + self.request_deadline
        super().handle_one_request()
        if not self._response_started:
            # A request had started but stalled; the stdlib would close the
            # connection without a reply.
            self.command, self.requestline, self.request_version = None, "", "HTTP/1.0"
            self.close_connection = True
            self._timed_out()
            self._unread_body = True  # the client may still be sending
        if self._unread_body or self._input_waiting():
            # Also bytes beyond Content-Length: closing with unread input would reset the connection.
            self._discard_unread_input()

    def do_GET(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler spelling
        self._dispatch(self._get)

    def do_HEAD(self) -> None:  # noqa: N802
        self._dispatch(self._get)

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch(self._post)

    def do_PUT(self) -> None:  # noqa: N802
        self._dispatch(lambda: self._send(wrong_method(self._target()[0])))

    do_DELETE = do_PATCH = do_OPTIONS = do_PUT

    def _dispatch(self, handler: Callable[[], None]) -> None:
        """The single exception boundary: every failure becomes structured JSON."""

        self._unread_body = bool(self.headers.get("Transfer-Encoding")) or self.headers.get("Content-Length", "0").strip() not in ("", "0")
        try:
            if self._check_host():
                handler()
        except ConnectionError:
            self.close_connection = True  # the client went away
        except socket.timeout:
            self.close_connection = True
            if not self._response_started:
                self._timed_out()
        except ProfileError:
            self._fail(HTTPStatus.INTERNAL_SERVER_ERROR, "E_PROFILE_INVALID", "The bundled manufacturing profile is inconsistent; see the server log.")
        except Exception:
            self._fail(HTTPStatus.INTERNAL_SERVER_ERROR, "E_INTERNAL", "Unexpected server error; see the server log.")

    def _timed_out(self) -> None:
        self._error(
            HTTPStatus.REQUEST_TIMEOUT, "E_HTTP_TIMEOUT",
            f"The request did not arrive in time ({self.timeout} s without data or {self.request_deadline} s in total).",
        )

    def _fail(self, status: HTTPStatus, code: str, message: str) -> None:
        sys.stderr.write(f"[tactile-fpc] {code}\n" + traceback.format_exc().translate(_TRACEBACK_ESCAPES))
        self.close_connection = True
        if not self._response_started:
            self._error(status, code, message)

    # -- routes ----------------------------------------------------------------

    def _get(self) -> None:
        path, query = self._target()
        if path in ("/", "/index.html"):
            self._send_file(WEB_ROOT / "index.html")
        elif path.startswith("/static/"):
            self._send_static(path[len("/static/"):])
        elif path not in GET_ROUTES:
            self._send(wrong_method(path))
        else:
            values = query_values(path, query)
            self._send(values if isinstance(values, Reply) else get_reply(path, values))

    def _post(self) -> None:
        path, query = self._target()
        if path not in POST_ROUTES:
            self._send(wrong_method(path))
            return
        options = query_values(path, query)
        if isinstance(options, Reply):
            self._send(options)
            return
        if not self._same_origin():
            return
        if path in SURFACE_ROUTES:
            self._post_surface(path)
            return
        refused = json_type_refused(self.headers.get("Content-Type", ""))
        if refused is not None:
            self._send(refused)
            return
        body = self._read_body(MAX_REQUEST_BYTES)
        if body is _ANSWERED:
            return
        payload = json_payload(body)
        if isinstance(payload, Reply):
            self._send(payload)
            return
        if path == "/api/validate":
            self._send(design_reply(path, options, payload))
            return
        slots = self.server.generation_slots
        if not self._take_generation_slot():
            return
        try:
            reply = design_reply(path, options, payload, self.server.build_cache)
        finally:
            slots.release()
        self._send(reply)

    def _post_surface(self, path: str) -> None:
        """A CAD-mode route: framed JSON header plus mesh bytes, answered as JSON."""

        refused = surface_type_refused(self.headers.get("Content-Type", ""))
        if refused is not None:
            self._send(refused)
            return
        body = self._read_body(MAX_SURFACE_BYTES)
        if body is _ANSWERED:
            return
        request = surface_request(body)
        if isinstance(request, Reply):
            self._send(request)
            return
        slots = self.server.surface_slots
        if not self._take_slot(slots, f"{MAX_CONCURRENT_SURFACE} surface request is already running; retry shortly."):
            return
        try:
            reply = surface_reply(path, *request, cache=self.server.build_cache)
        finally:
            slots.release()
        self._send(reply)

    def _take_generation_slot(self) -> bool:
        """One of the bounded generation slots, or a 503 (with Retry-After) when all are busy."""

        return self._take_slot(self.server.generation_slots, f"{MAX_CONCURRENT_GENERATIONS} generations are already running; retry shortly.")

    def _take_slot(self, slots: threading.BoundedSemaphore, busy: str) -> bool:
        if not slots.acquire(blocking=False):
            self._error(HTTPStatus.SERVICE_UNAVAILABLE, "E_HTTP_BUSY", busy, headers=(("Retry-After", str(RETRY_AFTER_S)),))
            return False
        return True

    # -- request checks --------------------------------------------------------

    def _target(self) -> tuple[str, str]:
        """Path and query of the request target (an absolute-form target included)."""

        target = self.path
        if _ABSOLUTE_TARGET.match(target):
            parts = urlsplit(target)
            target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        path, _, query = target.split("#", 1)[0].partition("?")
        return path, query

    def _check_host(self) -> bool:
        """RFC 9112 Host rules (else 400), then the allow-list of host names (else 421)."""

        hosts = [value.strip() for value in self.headers.get_all("Host") or []]
        if len(hosts) > 1 or not all(_HOST.match(host) for host in hosts) or (not hosts and _http_version(self.request_version) >= (1, 1)):
            self._error(HTTPStatus.BAD_REQUEST, "E_HTTP_BAD_REQUEST", "Send one well-formed Host header (required from HTTP/1.1 on).")
            return False
        # HTTP/1.0 clients may omit Host; browsers always send it.
        self._authority = hosts[0] if hosts else None
        if _ABSOLUTE_TARGET.match(self.path):
            # An absolute-form target names the host itself (RFC 9112 section 3.2.2).
            parts = urlsplit(self.path)
            if parts.scheme.lower() != "http" or not _HOST.match(parts.netloc):
                self._error(HTTPStatus.BAD_REQUEST, "E_HTTP_BAD_REQUEST", "An absolute request target must be an http:// URL of this server.")
                return False
            self._authority = parts.netloc
        name = None if self._authority is None else _host_header_name(self._authority)
        if name is not None and not self.server.host_allowed(name):
            self._error(
                HTTPStatus.MISDIRECTED_REQUEST,
                "E_HTTP_MISDIRECTED_HOST",
                f"Host {name[:253]!r} is not served: use a loopback name or the configured --host, "
                "or start app.py with --allow-host for this name (a tunnel, proxy or LAN name).",
            )
            return False
        return True

    def _same_origin(self) -> bool:
        """An Origin, when present, must be this request's own (http:// or, behind
        a TLS proxy or tunnel, https:// with the Host authority) or name an
        --allow-host host (a proxy that rewrites Host)."""

        origins = self.headers.get_all("Origin") or []
        if origins and (len(origins) != 1 or not self._origin_allowed(origins[0].strip().lower())):
            self._error(HTTPStatus.FORBIDDEN, "E_HTTP_FORBIDDEN_ORIGIN", "Cross-origin requests are not accepted.")
            return False
        return True

    def _origin_allowed(self, origin: str) -> bool:
        host = self._authority
        if host is not None and origin in (f"http://{host.lower()}", f"https://{host.lower()}"):
            return True
        scheme, _, authority = origin.partition("://")
        return scheme in ("http", "https") and bool(authority) and _HOST.match(authority) is not None and self.server.extra_host(_host_header_name(authority))

    def _read_body(self, limit: int) -> Any:
        """The request body (at most ``limit`` bytes), or _ANSWERED after an error reply."""

        if self.headers.get("Transfer-Encoding") is not None:
            self._error(HTTPStatus.LENGTH_REQUIRED, "E_HTTP_LENGTH_REQUIRED", "Chunked request bodies are not supported; send Content-Length.")
            return _ANSWERED
        lengths = self.headers.get_all("Content-Length") or []
        if not lengths:
            self._error(HTTPStatus.LENGTH_REQUIRED, "E_HTTP_LENGTH_REQUIRED", "Content-Length is required.")
            return _ANSWERED
        if len(lengths) != 1 or not _CONTENT_LENGTH.match(lengths[0].strip()):
            self._error(HTTPStatus.BAD_REQUEST, "E_HTTP_CONTENT_LENGTH", "Content-Length must be one decimal byte count.")
            return _ANSWERED
        size = int(lengths[0])
        if size > limit:
            if limit == MAX_SURFACE_BYTES and size <= limit + MAX_SURFACE_DRAIN_BYTES:
                # A mesh just over the limit: read it to the end, so the 413 arrives.
                self._drain = (size, MAX_SURFACE_DRAIN_S)
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "E_HTTP_BODY_TOO_LARGE", f"The request body exceeds {limit} bytes.")
            return _ANSWERED
        body = self.rfile.read(size)
        self._unread_body = False
        if len(body) != size:
            self.close_connection = True
            self._error(HTTPStatus.BAD_REQUEST, "E_HTTP_CONTENT_LENGTH", "The request body is shorter than Content-Length.")
            return _ANSWERED
        return body

    # -- responses ---------------------------------------------------------------

    def _send_static(self, name: str) -> None:
        try:
            candidate = (WEB_ROOT / name).resolve()
            found = WEB_ROOT.resolve() in candidate.parents and candidate.is_file()
        except (OSError, ValueError):
            found = False
        if not found:
            self._error(HTTPStatus.NOT_FOUND, "E_HTTP_NOT_FOUND", "Static file not found.")
            return
        self._send_file(candidate)

    def _send_file(self, path: Path) -> None:
        try:
            body = path.read_bytes()
        except OSError:
            self._error(HTTPStatus.NOT_FOUND, "E_HTTP_NOT_FOUND", "Static file not found.")
            return
        content_type = STATIC_TYPES.get(path.suffix.lower())
        if content_type is None:
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type.endswith(("javascript", "json", "svg+xml")):
                content_type += "; charset=utf-8"
        self._send_bytes(HTTPStatus.OK, content_type, body)

    def _send(self, reply: Reply) -> None:
        self._send_bytes(reply.status, reply.content_type, reply.body, reply.headers)

    def _error(self, status: int, code: str, message: str, *, headers: Iterable[tuple[str, str]] = (), **extra: Any) -> None:
        self._send(error_reply(status, code, message, headers=headers, **extra))

    def _send_bytes(self, status: int, content_type: str, body: bytes, headers: Iterable[tuple[str, str]] = ()) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_response(self, code: int, message: str | None = None) -> None:
        self._response_started = True
        super().send_response(code, message)

    def parse_request(self) -> bool:
        # RFC 9112 section 2.2: ignore empty lines before the request line.
        for _ in range(_MAX_LEADING_EMPTY_LINES):
            if self.raw_requestline not in (b"\r\n", b"\n"):
                break
            self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536 or not self.raw_requestline.strip():
            # The stdlib would close a blank request line (or empty lines and
            # then the end of the input) without any reply.
            self.command, self.requestline, self.request_version = None, "", "HTTP/1.0"
            too_long = len(self.raw_requestline) > 65536
            self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG if too_long else HTTPStatus.BAD_REQUEST, None if too_long else "Empty request line.")
            return False
        if not super().parse_request():
            return False
        if self.request_version == "HTTP/0.9":
            self.send_error(HTTPStatus.BAD_REQUEST, "HTTP/0.9 requests are not supported.")
            return False
        return True

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """JSON instead of the stdlib HTML page (malformed requests, unknown methods)."""

        self.log_error("code %d, message %s", code, message)
        self.close_connection = True
        self._unread_body = True  # the rest of a rejected request may still be arriving
        if self.request_version == "HTTP/0.9":
            # Malformed request lines default to HTTP/0.9, which has no status line.
            self.request_version = "HTTP/1.0"
        try:
            phrase = HTTPStatus(code).phrase
        except ValueError:
            phrase = "Error"
        self._error(code, _STATUS_CODES.get(code, f"E_HTTP_{code}"), message or phrase)

    def end_headers(self) -> None:
        for name, value in SECURITY_HEADERS:
            self.send_header(name, value)
        super().end_headers()

    def version_string(self) -> str:
        return self.server_version

    def log_message(self, format: str, *args: Any) -> None:
        # Request lines are client data: escape control characters.
        message = (format % args).translate(_LOG_ESCAPES)
        sys.stderr.write(f"[tactile-fpc] {self.address_string()} [{self.log_date_time_string()}] {message}\n")

    def _input_waiting(self) -> bool:
        """Whether request bytes are still unread in the socket (a non-blocking peek)."""

        try:
            self.connection.settimeout(0)
            return bool(self.connection.recv(1, socket.MSG_PEEK))
        except OSError:  # BlockingIOError: nothing is waiting
            return False
        finally:
            self.connection.settimeout(self.timeout)

    def _discard_unread_input(self) -> None:
        """Finish the reply, then read and drop what the client still sends (a lingering close)."""

        try:
            self.wfile.flush()
            self.connection.shutdown(socket.SHUT_WR)
            remaining, seconds = getattr(self, "_drain", (MAX_DRAIN_BYTES, MAX_DRAIN_S))
            end = time.monotonic() + seconds
            while remaining > 0:
                left = end - time.monotonic()
                if left <= 0:
                    break
                self.connection.settimeout(min(1.0, left))
                chunk = self.connection.recv(min(65536, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
        except OSError:
            pass


_ANSWERED = object()  # sentinel: an error reply was already sent
_MAX_LEADING_EMPTY_LINES = 8


class _DeadlineReader(io.RawIOBase):
    """Socket reads with the per-read timeout and, once ``deadline`` is set, an overall deadline."""

    def __init__(self, connection: socket.socket, timeout: float | None) -> None:
        super().__init__()
        self._connection = connection
        self._timeout = timeout
        self.deadline: float | None = None

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        if self.deadline is not None:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise socket.timeout("the request did not arrive within the request deadline")
            self._connection.settimeout(remaining if self._timeout is None else min(self._timeout, remaining))
        return self._connection.recv_into(buffer)


def _http_version(text: str) -> tuple[int, ...]:
    """``(major, minor)`` of an HTTP-version token such as ``HTTP/1.1``."""

    try:
        return tuple(int(part) for part in text.split("/", 1)[1].split("."))
    except (IndexError, ValueError):
        return (0, 9)


def _address_family(host: str) -> int:
    try:
        return socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)[0][0]
    except (OSError, UnicodeError):
        return socket.AF_INET


def _host_header_name(value: str) -> str:
    """Host name of a Host header value (or of a bind address), lower case, IPv6 in brackets."""

    value = value.strip().lower()
    if value.startswith("["):
        return value.split("]", 1)[0] + "]"
    if value.count(":") > 1:  # a bare IPv6 address
        return f"[{value}]"
    return value.split(":", 1)[0]


def _bind_host_name(host: str) -> str:
    """One notation for a bind address or a Host name: an IP literal with IPv6
    compressed, in brackets and without a zone id, and IPv4-mapped as IPv4; a
    name in lower case."""

    try:
        address = ipaddress.ip_address(host.strip().strip("[]"))
    except ValueError:
        return _host_header_name(host)
    if address.version == 6 and address.ipv4_mapped is not None:
        address = address.ipv4_mapped  # what IPv4 clients send; str() of a mapped address differs between Python versions
    if address.version == 6:
        return f"[{ipaddress.IPv6Address(int(address))}]"  # compressed, without a zone id, which no Host header carries
    return str(address)


def _allow_host_argument(value: str) -> str:
    """An ``--allow-host`` name, lower case: a DNS name or IPv4 address, or an
    IPv6 address in brackets, without scheme, port or path.  A leading dot
    allows a domain of at least two labels and its subdomains."""

    name = value.strip().lower()
    if name.startswith("[") or name.count(":") > 1:
        try:
            address = ipaddress.IPv6Address(name[1:-1] if name.startswith("[") and name.endswith("]") else name)
        except ValueError:
            pass
        else:
            # Browsers send neither zone ids nor the dotted form of IPv4-mapped addresses.
            if "%" in name or address.ipv4_mapped is not None:
                raise argparse.ArgumentTypeError(f"{value!r}: give a scoped or IPv4-mapped address as a plain IPv4 or IPv6 address")
            return f"[{address}]"
    elif _ALLOW_HOST.match(name):
        if name.startswith(".") and "." not in name[1:]:
            raise argparse.ArgumentTypeError(f"{value!r} would allow every name under a top-level domain; give the tunnel or LAN domain itself")
        last = name.rsplit(".", 1)[-1]
        if not name.startswith(".") and (last.isdigit() or last.startswith("0x")):
            # Browsers read a name ending in a number as IPv4 and send it as four decimal numbers (127.1 -> 127.0.0.1).
            try:
                canonical = str(ipaddress.IPv4Address(name)) == name
            except ValueError:
                canonical = False
            if not canonical:
                raise argparse.ArgumentTypeError(f"{value!r}: give an IPv4 address as browsers send it, four decimal numbers without leading zeros (e.g. 192.168.1.5)")
        return name
    raise argparse.ArgumentTypeError(f"{value!r} is not a host name or IP address (give it without scheme, port or path)")


def _port_argument(value: str) -> int:
    try:
        port = int(value)
    except ValueError:
        port = -1
    if not 0 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"{value!r} is not a port number (0-65535)")
    return port


def _is_loopback(host: str) -> bool:
    if host.strip().lower() == "localhost":
        return True
    try:
        address = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    return (getattr(address, "ipv4_mapped", None) or address).is_loopback  # 3.12.3 calls ::ffff:127.0.0.1 not loopback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1", help="local bind address (default: %(default)s)")
    parser.add_argument("--port", default=8008, type=_port_argument, help="local port (default: %(default)s)")
    parser.add_argument(
        "--allow-host",
        action="append",
        default=[],
        type=_allow_host_argument,
        metavar="NAME",
        help="also serve this Host name, e.g. a tunnel or LAN name ('.example.com' allows its subdomains); repeatable",
    )
    args = parser.parse_args(argv)
    if not _is_loopback(args.host):
        print(
            f"WARNING: --host {args.host} is not a loopback address. The API has no authentication; "
            "anyone who can reach this port can run generations. Requests must name this host (or an --allow-host name) in their Host header.",
            file=sys.stderr,
        )
    try:
        httpd = make_server(args.host, args.port, args.allow_host)
    except OSError as error:
        hint = " (is the customizer already running there? Open it, or start this one with --port <another port>)" if error.errno == errno.EADDRINUSE else ""
        print(f"Cannot listen on {args.host} port {args.port}: {error.strerror or error}{hint}.", file=sys.stderr)
        return 1
    shown = "127.0.0.1" if args.host in ("0.0.0.0", "") else ("[::1]" if args.host == "::" else _bind_host_name(args.host))
    print(f"Tactile FPC Customizer: http://{shown}:{httpd.server_address[1]}", flush=True)
    if args.allow_host:
        print("Also serving the Host names: " + ", ".join(sorted(set(args.allow_host))), flush=True)
    print("Local deterministic mode; no external API is used.", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Tactile FPC Customizer.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
