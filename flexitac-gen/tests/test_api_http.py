"""HTTP API and hardening (audit L1, L2, L11 cache and response size, M14; decisions D15, D16).

Each test talks to ``app.AppServer`` on an ephemeral loopback port, through
``http.client`` or raw sockets for malformed requests.  Every request must get
a complete reply; every error is ``{"ok": false, "code", "error"}`` JSON.
"""

from __future__ import annotations

import http.client
import io
import json
import select
import socket
import threading
import time
import unittest
from unittest import mock

import app
from engine import default_design, generate_design
from engine import core as engine_core
from engine.profile import ProfileError, order_requirements

try:
    from test_api_identity import BROWSER_DEFAULT_PAYLOAD
except ImportError:  # run as a package
    from tests.test_api_identity import BROWSER_DEFAULT_PAYLOAD

# No frame-ancestors: VS Code's port preview (Simple Browser) shows the page in a frame.
CSP = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; base-uri 'none'; form-action 'self'"
JSON = {"Content-Type": "application/json"}


class _Server:
    def __init__(self, handler: type = app.AppHandler, allow_hosts: tuple[str, ...] = ()) -> None:
        self.httpd = app.AppServer(("127.0.0.1", 0), handler, allow_hosts=allow_hosts)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(5)


class _Reply:
    def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.status, self.headers, self.body = status, headers, body

    def json(self):
        return json.loads(self.body)


def _parse(data: bytes) -> _Reply:
    head, _, body = data.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n")
    status = int(lines[0].split()[1])
    headers = {}
    for line in lines[1:]:
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()
    return _Reply(status, headers, body)


class HttpTestCase(unittest.TestCase):
    handler: type = app.AppHandler
    allow_hosts: tuple[str, ...] = ()

    def setUp(self) -> None:
        self.stderr = io.StringIO()
        patcher = mock.patch("sys.stderr", self.stderr)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.server = _Server(self.handler, self.allow_hosts)
        self.addCleanup(self.server.close)

    def request(self, method: str, path: str, body=None, headers=None) -> _Reply:
        connection = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=30)
        try:
            if isinstance(body, (dict, list)):
                body = json.dumps(body)
            connection.request(method, path, body=body, headers=dict(JSON if body is not None else {}, **(headers or {})))
            response = connection.getresponse()
            return _Reply(response.status, {name.lower(): value for name, value in response.getheaders()}, response.read())
        finally:
            connection.close()

    def raw(self, data: bytes, timeout: float = 30, half_close: bool = False) -> bytes:
        with socket.create_connection(("127.0.0.1", self.server.port), timeout=timeout) as sock:
            sock.sendall(data)
            if half_close:
                sock.shutdown(socket.SHUT_WR)
            chunks = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)

    def post_raw(self, body: bytes, path: str = "/api/generate", extra: bytes = b"") -> _Reply:
        head = f"POST {path} HTTP/1.1\r\nHost: 127.0.0.1:{self.server.port}\r\nContent-Type: application/json\r\n".encode()
        return _parse(self.raw(head + extra + f"Content-Length: {len(body)}\r\n\r\n".encode() + body))

    def assertError(self, reply: _Reply, status: int, code: str) -> dict:
        self.assertEqual(reply.status, status, reply.body[:300])
        self.assertTrue(reply.headers.get("content-type", "").startswith("application/json"), reply.headers)
        data = reply.json()
        self.assertEqual((data["ok"], data["code"]), (False, code), data)
        self.assertIsInstance(data["error"], str)
        return data


class RouteTests(HttpTestCase):
    def test_default_schema_and_static_routes(self) -> None:
        default = self.request("GET", "/api/default")
        self.assertEqual(default.status, 200)
        data = default.json()
        self.assertEqual(data["design"], default_design())
        profile = data["profile"]
        self.assertEqual(set(profile), {"id", "revision", "name", "display_rules", "limits", "issue_codes", "order_requirements", "row_bus"})
        # The generic template's diagonal Row bus is built with the surface profile (P5-diagonal-bus.md section 20).
        self.assertEqual((profile["row_bus"]["id"], set(profile["row_bus"])), ("jlc-fpc-surface-v1", {"id", "revision", "name", "display_rules"}))
        self.assertIn("connector.column_pins", profile["limits"])
        # The manufacturing note of the browser: the profile's JLCPCB order requirements.
        self.assertEqual(profile["order_requirements"], order_requirements(app.load_profile(), default_design()))
        self.assertIn("+/-0.05 mm (special request", {item["id"]: item["requirement"] for item in profile["order_requirements"]}["outline_tolerance"])
        self.assertIn("E_UNKNOWN_FIELD", profile["issue_codes"]["errors"])
        schema = self.request("GET", "/api/schema").json()
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("E_HTTP_BUSY", schema["x-http-error-codes"])
        head = self.request("HEAD", "/api/default")
        self.assertEqual((head.status, head.body), (200, b""))
        self.assertEqual(int(head.headers["content-length"]), len(default.body))
        page = self.request("GET", "/")
        self.assertEqual(page.status, 200)
        self.assertTrue(page.headers["content-type"].startswith("text/html"))
        script = self.request("GET", "/static/app.js?v=1")
        self.assertEqual(script.status, 200)
        self.assertIn("javascript", script.headers["content-type"])

    def test_generate_full_and_compact_views(self) -> None:
        full = self.request("POST", "/api/generate", {})
        self.assertEqual(full.status, 200)
        data = full.json()
        self.assertTrue(data["ok"])
        self.assertNotIn("derived_layout", data)
        self.assertEqual(set(data), {"ok", "design", "profile", "validation", "boards", "manifest"})
        self.assertIn("<svg", data["boards"]["row"]["svg"])
        self.assertEqual(data["manifest"]["layout_format"], "tactile-fpc-layout/v3")
        compact = self.request("POST", "/api/generate?view=compact", {})
        summary = compact.json()
        self.assertEqual(set(summary), {"ok", "design", "validation", "manifest", "boards"})
        for board in summary["boards"].values():
            self.assertEqual(set(board), {"id", "role", "physical_side", "units", "tail", "grid_registration", "metrics", "verification"})
            self.assertIn("checks", board["verification"])
        self.assertNotIn(b"<svg", compact.body)
        self.assertEqual(summary["manifest"], data["manifest"])
        self.assertLess(len(compact.body) * 2, len(full.body))
        self.assertEqual(self.request("POST", "/api/generate?view=full", {}).body, full.body)
        for query in ("view=svg", "view=compact&view=full", "include=layout", "view", "view=compact&x=1"):
            with self.subTest(query=query):
                self.assertError(self.request("POST", f"/api/generate?{query}", {}), 400, "E_HTTP_BAD_REQUEST")
        self.assertError(self.request("GET", "/api/default?view=compact"), 400, "E_HTTP_BAD_REQUEST")

    def test_browser_payload_has_the_default_build_id(self) -> None:
        reply = self.request("POST", "/api/generate", BROWSER_DEFAULT_PAYLOAD)
        self.assertEqual(reply.json()["manifest"]["build_id"], generate_design(default_design())["manifest"]["build_id"])

    def test_validate_route_returns_the_check_without_geometry(self) -> None:
        valid = self.request("POST", "/api/validate", {"rows": 8})
        self.assertEqual(valid.status, 200)
        data = valid.json()
        self.assertEqual(set(data), {"ok", "design", "validation", "identity"})
        self.assertTrue(data["ok"])
        self.assertEqual(data["identity"]["build_id"], generate_design({"rows": 8})["manifest"]["build_id"])
        invalid = self.request("POST", "/api/validate", {"matrix": {"colums": 3}}).json()
        self.assertFalse(invalid["ok"])
        self.assertEqual(invalid["validation"]["errors"][0]["field"], "matrix.colums")

    def test_export_reuses_the_cached_generation(self) -> None:
        cache = self.server.httpd.build_cache
        with mock.patch.object(engine_core, "_build_boards", wraps=engine_core._build_boards) as build:
            generated = self.request("POST", "/api/generate", BROWSER_DEFAULT_PAYLOAD).json()
            exported = self.request("POST", "/api/export/top-gerber", generated["design"])
            bundle = self.request("POST", "/api/export/project", generated["design"])
        self.assertEqual(build.call_count, 1)
        # Each export looks the build up twice: for the request, and when the
        # exporter checks the result against the engine's generation (D17).
        self.assertEqual((cache.misses, cache.hits), (1, 4))
        build_id = generated["manifest"]["build_id"]
        self.assertEqual(exported.status, 200)
        self.assertEqual(exported.headers["content-type"], "application/zip")
        self.assertEqual(exported.headers["content-disposition"], f'attachment; filename="{build_id}-top-rows-direct-gerber.zip"')
        self.assertEqual(bundle.headers["content-disposition"], f'attachment; filename="{build_id}-project-review.zip"')
        self.assertEqual(exported.headers["x-build-id"], build_id)
        self.assertEqual(exported.headers["x-design-sha256"], generated["manifest"]["design_sha256"])
        self.assertEqual(exported.body[:2], b"PK")
        # The cached build exports the same bytes as a fresh one.
        from exporters import build_exports

        self.assertEqual(exported.body, build_exports(generate_design(default_design()))["top_fpc_gerber_zip"])

    def test_the_build_cache_holds_the_16_most_recent_builds(self) -> None:
        # docs/API.md: "A build cache of 16 builds" (least recently used out).
        cache = self.server.httpd.build_cache
        self.assertEqual((app.BUILD_CACHE_SIZE, cache.maxsize), (16, 16))
        designs = [{"rows": rows, "columns": 1} for rows in range(1, 18)]
        for design in designs[:16]:
            self.assertEqual(self.request("POST", "/api/generate?view=compact", design).status, 200)
        self.assertEqual((cache.misses, cache.hits), (16, 0))
        # The oldest of the 16 is still cached: its export generates nothing.
        self.assertEqual(self.request("POST", "/api/export/top-gerber", designs[0]).status, 200)
        self.assertEqual((cache.misses, cache.hits), (16, 2))
        # A 17th build evicts the least recently used one (rows 2), which is built again.
        self.request("POST", "/api/generate?view=compact", designs[16])
        self.request("POST", "/api/generate?view=compact", designs[1])
        self.assertEqual((cache.misses, cache.hits), (18, 2))

    def test_export_of_an_invalid_or_wrapped_design_is_blocked(self) -> None:
        whole = self.request("POST", "/api/generate", {"rows": 4}).json()
        blocked = self.assertError(self.request("POST", "/api/export/bottom-gerber", whole), 422, "E_EXPORT_BLOCKED")
        self.assertIn("E_UNKNOWN_FIELD", {issue["code"] for issue in blocked["validation"]["errors"]})
        invalid = self.assertError(self.request("POST", "/api/export/project", {"matrix": {"pitch_x_mm": 1.0, "taxel_width_mm": 0.9}}), 422, "E_EXPORT_BLOCKED")
        self.assertIn("E_ELECTRODE_GAP", {issue["code"] for issue in invalid["validation"]["errors"]})


class RobustnessTests(HttpTestCase):
    def test_malformed_bodies_get_structured_400s(self) -> None:
        cases = {
            b"null": "E_HTTP_BODY_NOT_OBJECT",
            b"[]": "E_HTTP_BODY_NOT_OBJECT",
            b'"design"': "E_HTTP_BODY_NOT_OBJECT",
            b"5": "E_HTTP_BODY_NOT_OBJECT",
            b"": "E_HTTP_BODY_NOT_OBJECT",
            b"   ": "E_HTTP_BODY_NOT_OBJECT",
            b'{"rows": NaN}': "E_HTTP_INVALID_JSON",
            b'{"rows": Infinity}': "E_HTTP_INVALID_JSON",
            b'{"rows": -Infinity}': "E_HTTP_INVALID_JSON",
            b'{"pitch_x_mm": 1e400}': "E_HTTP_INVALID_JSON",
            b'{"rows": 4, "rows": 8}': "E_HTTP_INVALID_JSON",
            b'{"rows": 1' + b"0" * 5000 + b"}": "E_HTTP_INVALID_JSON",
            b"[" * 60000 + b"]" * 60000: "E_HTTP_INVALID_JSON",
            b'{"a":' * 20000 + b"1" + b"}" * 20000: "E_HTTP_INVALID_JSON",
            b'{"rows": 4': "E_HTTP_INVALID_JSON",
            b"\xff\xfe{}": "E_HTTP_INVALID_JSON",
            b'{"project_name": "\xc3"}': "E_HTTP_INVALID_JSON",
        }
        for body, code in cases.items():
            with self.subTest(body=body[:40]):
                self.assertError(self.post_raw(body), 400, code)
        # Values that parse are reported by the engine, field by field.
        huge = self.post_raw(b'{"matrix": {"rows": 1' + b"0" * 400 + b', "pitch_x_mm": 1' + b"0" * 400 + b"}}")
        self.assertEqual(huge.status, 200)
        errors = {(issue["code"], issue["field"]) for issue in huge.json()["validation"]["errors"]}
        self.assertEqual(errors, {("E_ROWS_INTEGER", "matrix.rows"), ("E_NUMERIC", "matrix.pitch_x_mm")})
        surrogate = self.post_raw(b'{"project_name": "\\ud800 x"}')
        self.assertEqual(surrogate.status, 200)
        self.assertEqual(surrogate.json()["validation"]["errors"][0]["code"], "E_PROJECT_NAME")
        unicode_name = self.post_raw('{"project_name": "触觉传感器"}'.encode("utf-8"))
        self.assertTrue(unicode_name.json()["ok"])
        self.assertEqual(unicode_name.json()["design"]["project_name"], "触觉传感器")
        self.assertTrue(unicode_name.body.isascii())

    def test_request_framing_errors(self) -> None:
        port = self.server.port
        head = f"POST /api/generate HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nContent-Type: application/json\r\n"
        chunked = _parse(self.raw((head + "Transfer-Encoding: chunked\r\n\r\n2\r\n{}\r\n0\r\n\r\n").encode()))
        self.assertError(chunked, 411, "E_HTTP_LENGTH_REQUIRED")
        # Both framings at once (a request-smuggling shape) are refused, not read by length.
        both = _parse(self.raw((head + "Transfer-Encoding: chunked\r\nContent-Length: 2\r\n\r\n{}").encode()))
        self.assertError(both, 411, "E_HTTP_LENGTH_REQUIRED")
        self.assertError(_parse(self.raw((head + "\r\n").encode())), 411, "E_HTTP_LENGTH_REQUIRED")
        for value in ("abc", "-5", "+2", "1_0", " 2x", "99999999999999999999"):
            with self.subTest(content_length=value):
                self.assertError(_parse(self.raw((head + f"Content-Length: {value}\r\n\r\n{{}}").encode())), 400, "E_HTTP_CONTENT_LENGTH")
        duplicate = _parse(self.raw((head + "Content-Length: 2\r\nContent-Length: 2\r\n\r\n{}").encode()))
        self.assertError(duplicate, 400, "E_HTTP_CONTENT_LENGTH")
        # A body shorter than announced, then a half-close by the client.
        with socket.create_connection(("127.0.0.1", port), timeout=30) as sock:
            sock.sendall((head + "Content-Length: 50\r\n\r\n{}").encode())
            sock.shutdown(socket.SHUT_WR)
            reply = b"".join(iter(lambda: sock.recv(65536), b""))
        self.assertError(_parse(reply), 400, "E_HTTP_CONTENT_LENGTH")
        # An oversized body is answered with 413 (and drained, so no reset).
        big = b'{"project_name": "' + b"x" * 200000 + b'"}'
        self.assertError(self.post_raw(big), 413, "E_HTTP_BODY_TOO_LARGE")

    def test_a_rejected_body_is_drained_after_the_reply(self) -> None:
        # The server answers before reading the body, then keeps reading what
        # the client still sends (a lingering close): no reset hits a client
        # that writes its whole body before it reads the reply.
        head = "POST /api/generate HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: text/plain\r\nContent-Length: 300000\r\n\r\n"
        with socket.create_connection(("127.0.0.1", self.server.port), timeout=30) as sock:
            sock.sendall(head.encode())
            reply = b""
            while b"}" not in reply:
                chunk = sock.recv(65536)
                if not chunk:
                    break  # closed without a reply
                reply += chunk
            for _ in range(6):
                time.sleep(0.05)
                sock.sendall(b"x" * 50000)  # raises once the server has closed
            sock.shutdown(socket.SHUT_WR)
            reply += b"".join(iter(lambda: sock.recv(65536), b""))
        self.assertError(_parse(reply), 415, "E_HTTP_UNSUPPORTED_MEDIA_TYPE")

    def test_bytes_beyond_the_request_are_drained_before_closing(self) -> None:
        # Closing with unread input makes the kernel reset the connection,
        # which can destroy a reply still in the send buffer.
        calls = []
        real = app.AppHandler._discard_unread_input

        def spy(handler) -> None:
            calls.append(handler.path)
            real(handler)

        with mock.patch.object(app.AppHandler, "_discard_unread_input", spy):
            self.assertEqual(self.post_raw(b"{}", path="/api/validate").status, 200)
            self.assertEqual(calls, [])
            head = b"POST /api/validate HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}"
            reply = _parse(self.raw(head + b"x" * 50000))
        self.assertEqual(reply.status, 200)
        self.assertTrue(reply.json()["ok"])
        self.assertEqual(calls, ["/api/validate"])

    def test_the_drain_after_a_rejected_request_is_bounded_in_time(self) -> None:
        # A client that keeps trickling a rejected body cannot hold the thread in the drain.
        head = b"POST /api/generate HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: text/plain\r\nContent-Length: 100000\r\n\r\n"
        with mock.patch.object(app, "MAX_DRAIN_S", 0.5), socket.create_connection(("127.0.0.1", self.server.port), timeout=10) as sock:
            sock.sendall(head)
            reply = b""
            while b"}" not in reply:
                chunk = sock.recv(65536)
                if not chunk:
                    break  # closed without a reply
                reply += chunk
            start = time.monotonic()
            closed = False
            while not closed and time.monotonic() - start < 5:
                time.sleep(0.2)
                try:
                    sock.sendall(b"x")  # fails once the server has closed the connection
                except OSError:
                    closed = True
            elapsed = time.monotonic() - start
        self.assertError(_parse(reply), 415, "E_HTTP_UNSUPPORTED_MEDIA_TYPE")
        self.assertTrue(closed, "the server kept draining a trickling client")
        self.assertLess(elapsed, 3)

    def test_blank_request_lines(self) -> None:
        # RFC 9112: empty lines before the request line are ignored.
        self.assertEqual(_parse(self.raw(b"\r\n\nGET /api/default HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")).status, 200)
        for request in (b"   \r\n\r\n", b"\r\n" * 12, b"\t\r\nHost: x\r\n\r\n"):
            with self.subTest(request=request):
                self.assertError(_parse(self.raw(request)), 400, "E_HTTP_BAD_REQUEST")
        # Empty lines and then the end of the input: a 400 at once, not a timeout.
        for request in (b"\r\n", b"\r\n\r\n", b"\n\n\n"):
            with self.subTest(request=request):
                start = time.monotonic()
                self.assertError(_parse(self.raw(request, half_close=True)), 400, "E_HTTP_BAD_REQUEST")
                self.assertLess(time.monotonic() - start, 5)

    def test_host_header_and_request_target_rules(self) -> None:
        port = self.server.port

        def get(target: str, *headers: str, version: str = "HTTP/1.1") -> _Reply:
            return _parse(self.raw(f"GET {target} {version}\r\n{''.join(line + chr(13) + chr(10) for line in headers)}\r\n".encode()))

        # RFC 9112 section 3.2: an HTTP/1.1 request needs exactly one well-formed Host.
        for headers in ((), ("Host: 127.0.0.1", "Host: 127.0.0.1"), (f"Host: localhost:{port}@evil.example",),
                        ("Host: localhost:abc",), ("Host: local host",), ("Host: [::1",)):
            with self.subTest(headers=headers):
                self.assertError(get("/api/default", *headers), 400, "E_HTTP_BAD_REQUEST")
        self.assertEqual(get("/api/default", version="HTTP/1.0").status, 200)  # HTTP/1.0 may omit Host
        self.assertEqual(get("/api/default", "Host: localhost:").status, 200)
        # An absolute-form target names the host itself (section 3.2.2); Host is then ignored.
        self.assertError(get("http://evil.example/api/default", "Host: 127.0.0.1"), 421, "E_HTTP_MISDIRECTED_HOST")
        self.assertEqual(get(f"http://127.0.0.1:{port}/api/default", "Host: evil.example").status, 200)
        for target in (f"https://127.0.0.1:{port}/api/default", f"http://user@127.0.0.1:{port}/api/default"):
            with self.subTest(target=target):
                self.assertError(get(target, "Host: 127.0.0.1"), 400, "E_HTTP_BAD_REQUEST")
        # Routing uses the path itself: "//host/..." is not a different spelling of a route.
        self.assertError(get("//x/api/default", "Host: 127.0.0.1"), 404, "E_HTTP_NOT_FOUND")
        # The Origin of a POST is compared with the effective host.
        body = "{}"
        origin = f"Origin: http://127.0.0.1:{port}"
        post = f"POST http://127.0.0.1:{port}/api/validate HTTP/1.1\r\nHost: other.example\r\n{origin}\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{body}"
        self.assertEqual(_parse(self.raw(post.encode())).status, 200)

    def test_host_origin_and_content_type_checks(self) -> None:
        port = self.server.port
        for host in ("evil.example", f"evil.example:{port}", f"127.0.0.1.evil:{port}", f"localhost.:{port}"):
            with self.subTest(host=host):
                self.assertError(self.request("GET", "/api/default", headers={"Host": host}), 421, "E_HTTP_MISDIRECTED_HOST")
                self.assertError(self.request("POST", "/api/generate", {}, headers={"Host": host}), 421, "E_HTTP_MISDIRECTED_HOST")
        for host in (f"localhost:{port}", f"LOCALHOST:{port}", f"[::1]:{port}", "127.0.0.1"):
            with self.subTest(host=host):
                self.assertEqual(self.request("GET", "/api/default", headers={"Host": host}).status, 200)
        for origin in ("http://evil.example", "https://evil.example", "null", f"http://localhost:{port}", f"http://127.0.0.1:{port}/",
                       f"http://127.0.0.1:{port + 1 if port < 65535 else port - 1}", f"ftp://127.0.0.1:{port}"):
            with self.subTest(origin=origin):
                self.assertError(self.request("POST", "/api/generate", {}, headers={"Origin": origin}), 403, "E_HTTP_FORBIDDEN_ORIGIN")
        # The page's own origin; https:// when a TLS proxy or tunnel in front of the app keeps the Host.
        for origin in (f"http://127.0.0.1:{port}", f"https://127.0.0.1:{port}", f"HTTP://127.0.0.1:{port}"):
            with self.subTest(origin=origin):
                self.assertEqual(self.request("POST", "/api/validate", {}, headers={"Origin": origin}).status, 200)
        for content_type in ("text/plain", "text/plain;charset=UTF-8", "application/x-www-form-urlencoded", "application/json; charset=latin-1", ""):
            with self.subTest(content_type=content_type):
                reply = self.request("POST", "/api/generate", "{}", headers={"Content-Type": content_type})
                self.assertError(reply, 415, "E_HTTP_UNSUPPORTED_MEDIA_TYPE")
        for content_type in ("application/json; charset=utf-8", "Application/JSON;charset=UTF-8"):
            self.assertEqual(self.request("POST", "/api/validate", "{}", headers={"Content-Type": content_type}).status, 200)

    def test_static_types_do_not_depend_on_the_mimetypes_registry(self) -> None:
        # On Windows, mimetypes reads the registry, which can map .js to text/plain; under
        # nosniff the browser would then refuse the script and the UI would never start.
        with mock.patch.object(app.mimetypes, "guess_type", return_value=("text/plain", None)):
            for path, content_type in (("/", "text/html; charset=utf-8"), ("/static/app.js", "text/javascript; charset=utf-8"),
                                       ("/static/styles.css", "text/css; charset=utf-8")):
                with self.subTest(path=path):
                    reply = self.request("GET", path)
                    self.assertEqual(reply.status, 200)
                    self.assertEqual(reply.headers["content-type"], content_type)

    def test_security_headers_on_every_kind_of_reply(self) -> None:
        replies = {
            "html": self.request("GET", "/"),
            "json": self.request("POST", "/api/validate", {}),
            "zip": self.request("POST", "/api/export/top-gerber", {}),
            "error": self.request("GET", "/missing"),
            "stdlib error": _parse(self.raw(b"FOO / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")),
        }
        for name, reply in replies.items():
            with self.subTest(reply=name):
                self.assertEqual(reply.headers["x-content-type-options"], "nosniff")
                self.assertEqual(reply.headers["content-security-policy"], CSP)
                self.assertEqual(reply.headers["referrer-policy"], "no-referrer")
                self.assertEqual(reply.headers["cache-control"], "no-store")
                self.assertEqual(reply.headers["server"], "TactileFPC")

    def test_security_headers_allow_framing_by_the_editor_preview(self) -> None:
        reply = self.request("GET", "/")
        self.assertEqual(reply.status, 200)
        self.assertNotIn("frame-ancestors", reply.headers["content-security-policy"])
        self.assertNotIn("x-frame-options", reply.headers)

    def test_methods_and_paths(self) -> None:
        for method, path, allow in (("GET", "/api/generate", "POST"), ("PUT", "/api/generate", "POST"), ("DELETE", "/api/export/project", "POST"),
                                    ("POST", "/api/default", "GET, HEAD"), ("OPTIONS", "/api/schema", "GET, HEAD"), ("PATCH", "/static/app.js", "GET, HEAD")):
            with self.subTest(method=method, path=path):
                reply = self.request(method, path, {} if method == "POST" else None)
                self.assertError(reply, 405, "E_HTTP_METHOD_NOT_ALLOWED")
                self.assertEqual(reply.headers["allow"], allow)
        self.assertError(_parse(self.raw(b"FOO /api/generate HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")), 501, "E_HTTP_NOT_IMPLEMENTED")
        for path in ("/missing", "/static/../app.py", "/static//etc/passwd", "/static/%2e%2e/app.py", "/static/" + "x" * 300, "/static/a\x00b", "/static/"):
            with self.subTest(path=path):
                reply = _parse(self.raw(f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n".encode("latin-1")))
                self.assertError(reply, 404, "E_HTTP_NOT_FOUND")
        self.assertError(_parse(self.raw(b"GET /" + b"a" * 70000 + b" HTTP/1.1\r\n\r\n")), 414, "E_HTTP_URI_TOO_LONG")
        self.assertError(_parse(self.raw(b"GARBAGE\r\n\r\n")), 400, "E_HTTP_BAD_REQUEST")
        self.assertError(_parse(self.raw(b"GET /\r\n\r\n")), 400, "E_HTTP_BAD_REQUEST")  # HTTP/0.9
        self.assertError(_parse(self.raw(b"GET / HTTP/1.1\r\n" + b"X-A: b\r\n" * 150 + b"\r\n")), 431, "E_HTTP_HEADERS_TOO_LARGE")

    def test_unexpected_failures_are_500_json_and_the_server_keeps_serving(self) -> None:
        with mock.patch.object(app, "generate_design", side_effect=RuntimeError("boom \x1b[2J")):
            reply = self.assertError(self.request("POST", "/api/generate", {}), 500, "E_INTERNAL")
        self.assertNotIn("boom", reply["error"])
        with mock.patch.object(app, "generate_design", side_effect=ProfileError("broken")):
            self.assertError(self.request("POST", "/api/export/project", {}), 500, "E_PROFILE_INVALID")
        self.assertEqual(self.request("POST", "/api/generate", {}).status, 200)
        self.assertIn("RuntimeError", self.stderr.getvalue())
        self.assertNotIn("\x1b", self.stderr.getvalue())

    def test_log_lines_escape_control_characters(self) -> None:
        self.raw(b"GET /\x1b[2J\x1b[31mFAKE HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        log = self.stderr.getvalue()
        self.assertNotIn("\x1b", log)
        self.assertIn("\\x1b[2J", log)
        self.assertIn("127.0.0.1", log)


class CapacityTests(HttpTestCase):
    def test_generations_beyond_the_limit_get_503_with_retry_after(self) -> None:
        self.assertEqual(app.MAX_CONCURRENT_GENERATIONS, 2)
        entered = threading.Semaphore(0)
        release = threading.Event()
        real = app.generate_design

        def slow(payload, cache=None):
            entered.release()
            release.wait(30)
            return real(payload, cache=cache)

        replies = []
        with mock.patch.object(app, "generate_design", side_effect=slow):
            workers = [threading.Thread(target=lambda: replies.append(self.request("POST", "/api/generate", {}))) for _ in range(2)]
            for worker in workers:
                worker.start()
            for _ in workers:
                self.assertTrue(entered.acquire(timeout=30))
            busy = self.request("POST", "/api/export/project", {})
            # Validation is not a generation and stays available.
            validate = self.request("POST", "/api/validate", {})
            release.set()
            for worker in workers:
                worker.join(30)
        self.assertError(busy, 503, "E_HTTP_BUSY")
        self.assertEqual(busy.headers["retry-after"], "1")
        self.assertEqual(validate.status, 200)
        self.assertEqual([reply.status for reply in replies], [200, 200])
        self.assertEqual(self.request("POST", "/api/generate?view=compact", {}).status, 200)

    def test_no_connection_is_dropped_under_concurrent_load(self) -> None:
        self.assertEqual(app.AppServer.request_queue_size, 64)
        results = []
        lock = threading.Lock()

        def client(index: int) -> None:
            try:
                if index % 3 == 0:
                    reply = self.request("POST", "/api/generate?view=compact", {"rows": 1 + index % 7})
                elif index % 3 == 1:
                    reply = self.request("POST", "/api/validate", {"rows": index})
                else:
                    reply = self.request("GET", "/api/default")
                outcome = (reply.status, reply.json()["ok"] if reply.status != 200 else True)
            except Exception as error:  # a dropped connection
                outcome = ("dropped", repr(error))
            with lock:
                results.append(outcome)

        threads = [threading.Thread(target=client, args=(index,)) for index in range(48)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(60)
        self.assertEqual(len(results), 48)
        self.assertEqual([outcome for outcome in results if outcome[0] == "dropped"], [])
        self.assertTrue({status for status, _ in results} <= {200, 503}, results)


class _ShortTimeout(app.AppHandler):
    timeout = 0.5
    request_deadline = 1.5


class TimeoutTests(HttpTestCase):
    handler = _ShortTimeout

    def test_socket_timeout(self) -> None:
        self.assertEqual(app.AppHandler.timeout, 30)
        head = "POST /api/generate HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nContent-Length: 10\r\n\r\n{}"
        start = time.monotonic()
        reply = _parse(self.raw(head.encode(), timeout=10))
        self.assertLess(time.monotonic() - start, 5)
        self.assertError(reply, 408, "E_HTTP_TIMEOUT")
        # A request line or header block that stalls is answered too.
        for partial in (b"POST /api/gen", b"POST /api/generate HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Ty"):
            with self.subTest(partial=partial):
                self.assertError(_parse(self.raw(partial, timeout=10)), 408, "E_HTTP_TIMEOUT")
        # An idle connection is closed after the timeout instead of pinning a thread.
        with socket.create_connection(("127.0.0.1", self.server.port), timeout=10) as sock:
            start = time.monotonic()
            self.assertEqual(sock.recv(10), b"")
            self.assertLess(time.monotonic() - start, 5)

    def test_a_timed_out_request_is_drained_before_closing(self) -> None:
        # The stalled client may resume sending; reading on for a moment keeps
        # the 408 from being lost to a connection reset.
        calls = []
        real = app.AppHandler._discard_unread_input

        def spy(handler) -> None:
            calls.append(handler.requestline)
            real(handler)

        with mock.patch.object(app.AppHandler, "_discard_unread_input", spy):
            self.assertError(_parse(self.raw(b"POST /api/gen", timeout=10)), 408, "E_HTTP_TIMEOUT")
        self.assertEqual(len(calls), 1)

    def test_a_trickling_request_is_cut_off_at_the_request_deadline(self) -> None:
        self.assertEqual(app.AppHandler.request_deadline, 60)
        request = b"POST /api/generate HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}"
        start = time.monotonic()
        with socket.create_connection(("127.0.0.1", self.server.port), timeout=10) as sock:
            # One byte every 0.2 s: each read is well within the 0.5 s socket timeout.
            for byte in request:
                if select.select([sock], [], [], 0.2)[0]:
                    break
                sock.sendall(bytes([byte]))
            reply = b"".join(iter(lambda: sock.recv(65536), b""))
        elapsed = time.monotonic() - start
        self.assertError(_parse(reply), 408, "E_HTTP_TIMEOUT")
        self.assertGreater(elapsed, _ShortTimeout.request_deadline - 0.1)
        self.assertLess(elapsed, 6)


class AllowHostTests(HttpTestCase):
    """--allow-host: more Host names (a tunnel, proxy or LAN name) without opening the server to every Host."""

    allow_hosts = ("FPC.example.test", ".devtunnels.ms", "fe80::1")

    def test_allowed_names_and_domains(self) -> None:
        port = self.server.port
        for host in ("fpc.example.test", "FPC.Example.Test:443", "abc-8008.usw2.devtunnels.ms", "devtunnels.ms:443",
                     "[fe80::1]:8008", "[fe80:0:0:0::1]:8008", f"localhost:{port}", "127.0.0.1"):
            with self.subTest(host=host):
                self.assertEqual(self.request("GET", "/api/default", headers={"Host": host}).status, 200)
        for host in ("evil.example", "notdevtunnels.ms", "devtunnels.ms.evil.example", "fpc.example.test.evil",
                     "sub.fpc.example.test", "[fe80::2]"):
            with self.subTest(host=host):
                reply = self.request("GET", "/api/default", headers={"Host": host})
                self.assertError(reply, 421, "E_HTTP_MISDIRECTED_HOST")
                self.assertIn(repr(app._host_header_name(host)), reply.json()["error"])
                self.assertIn("--allow-host", reply.json()["error"])

    def test_origins_of_allowed_names(self) -> None:
        port = self.server.port
        tunnel = "abc-8008.usw2.devtunnels.ms"
        accepted = (
            (tunnel, f"https://{tunnel}"),
            (tunnel, f"http://{tunnel}"),
            (f"{tunnel}:443", f"https://{tunnel}:443"),
            # A proxy that rewrites Host to the loopback address keeps the browser's Origin.
            (f"127.0.0.1:{port}", f"https://{tunnel}"),
            (f"localhost:{port}", "https://fpc.example.test"),
        )
        for host, origin in accepted:
            with self.subTest(host=host, origin=origin):
                self.assertEqual(self.request("POST", "/api/validate", {}, headers={"Host": host, "Origin": origin}).status, 200)
        refused = (
            (tunnel, "https://evil.example"),
            (tunnel, f"https://{tunnel}/"),
            (tunnel, f"https://user@{tunnel}"),
            (tunnel, f"ftp://{tunnel}"),
            (tunnel, "null"),
            (f"127.0.0.1:{port}", "https://localhost:9999"),  # loopback names only as the request's own origin
            (f"127.0.0.1:{port}", "https://notdevtunnels.ms"),
        )
        for host, origin in refused:
            with self.subTest(host=host, origin=origin):
                reply = self.request("POST", "/api/validate", {}, headers={"Host": host, "Origin": origin})
                self.assertError(reply, 403, "E_HTTP_FORBIDDEN_ORIGIN")

    def test_names_are_checked(self) -> None:
        for value, name in (("X.Example", "x.example"), (" .Devtunnels.MS ", ".devtunnels.ms"), ("192.168.1.5", "192.168.1.5"),
                            ("::1", "[::1]"), ("[FE80:0:0:0:0:0:0:1]", "[fe80::1]"), ("lan_host", "lan_host")):
            with self.subTest(value=value):
                self.assertEqual(app._allow_host_argument(value), name)
        for value in ("", " ", ".", "*", "*.example.com", "http://x.example", "x.example:8008", "x.example/", "[::1]:80",
                      "..x", "a..b", "x.", "[nonsense]", "user@x.example", "x example", ".com", ".local",
                      "fe80::1%eth0", "[fe80::1%25eth0]", "::ffff:1.2.3.4", "[::ffff:102:304]",
                      "127.1", "192.168.001.005", "10.1", "0", "2130706433", "0x7f.1"):
            with self.subTest(value=value):
                with self.assertRaises(app.argparse.ArgumentTypeError):
                    app._allow_host_argument(value)
        # Bad names are refused before the server binds its port.
        with self.assertRaises(app.argparse.ArgumentTypeError):
            app.AppServer(("127.0.0.1", 0), allow_hosts=["http://x.example"])


class MainTests(unittest.TestCase):
    def test_non_loopback_bind_prints_a_warning(self) -> None:
        class Fake:
            server_address = ("0.0.0.0", 8008)

            def serve_forever(self) -> None:
                raise KeyboardInterrupt

            def server_close(self) -> None:
                pass

        for host, warned in (("0.0.0.0", True), ("192.168.1.5", True), ("127.0.0.1", False), ("localhost", False), ("::1", False),
                             ("::ffff:127.0.0.1", False), ("::ffff:192.168.1.5", True)):
            with self.subTest(host=host), mock.patch.object(app, "make_server", return_value=Fake()), \
                    mock.patch("sys.stderr", new_callable=io.StringIO) as stderr, mock.patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(app.main(["--host", host]), 0)
                self.assertEqual("WARNING" in stderr.getvalue(), warned)
        # The start-up line names the form the Host check allows.
        for host, shown in (("2001:db8:0:0::5", "[2001:db8::5]"), ("::ffff:127.0.0.2", "127.0.0.2"), ("0.0.0.0", "127.0.0.1"), ("::", "[::1]")):
            with self.subTest(host=host), mock.patch.object(app, "make_server", return_value=Fake()), \
                    mock.patch("sys.stderr", new_callable=io.StringIO), mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(app.main(["--host", host]), 0)
                self.assertIn(f"Tactile FPC Customizer: http://{shown}:8008", stdout.getvalue())

    def test_allow_host_option(self) -> None:
        class Fake:
            server_address = ("127.0.0.1", 8008)

            def serve_forever(self) -> None:
                raise KeyboardInterrupt

            def server_close(self) -> None:
                pass

        with mock.patch.object(app, "make_server", return_value=Fake()) as make, \
                mock.patch("sys.stderr", new_callable=io.StringIO), mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(app.main(["--allow-host", "abc-8008.usw2.devtunnels.ms", "--allow-host", ".Example.LAN"]), 0)
        make.assert_called_once_with("127.0.0.1", 8008, ["abc-8008.usw2.devtunnels.ms", ".example.lan"])
        self.assertIn("Also serving the Host names: .example.lan, abc-8008.usw2.devtunnels.ms", stdout.getvalue())
        for argv, message in ((["--allow-host", "https://abc.devtunnels.ms"], "is not a host name or IP address"),
                              (["--allow-host", ".local"], "top-level domain"),
                              (["--port", "70000"], "is not a port number (0-65535)"),
                              (["--port", "65536"], "is not a port number (0-65535)"),
                              (["--port", "http"], "is not a port number (0-65535)")):
            with self.subTest(argv=argv):
                with mock.patch.object(app, "make_server") as make, mock.patch("sys.stdout", new_callable=io.StringIO), \
                        mock.patch("sys.stderr", new_callable=io.StringIO) as stderr, self.assertRaises(SystemExit) as raised:
                    app.main(argv)
                self.assertEqual(raised.exception.code, 2)
                self.assertIn(message, stderr.getvalue())
                make.assert_not_called()
        for port in ("0", "65535"):
            with self.subTest(port=port), mock.patch.object(app, "make_server", return_value=Fake()) as make, \
                    mock.patch("sys.stderr", new_callable=io.StringIO), mock.patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(app.main(["--port", port]), 0)
            make.assert_called_once_with("127.0.0.1", int(port), [])

    def test_a_port_in_use_is_reported_without_a_traceback(self) -> None:
        with socket.socket() as busy:
            busy.bind(("127.0.0.1", 0))
            busy.listen()
            port = busy.getsockname()[1]
            with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr, mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(app.main(["--port", str(port)]), 1)
        self.assertIn(f"Cannot listen on 127.0.0.1 port {port}", stderr.getvalue())
        self.assertIn("--port", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")

    def test_a_non_default_bind_address_is_served_under_its_own_name(self) -> None:
        # One notation per address: IPv6 compressed in brackets, no zone id, IPv4-mapped as IPv4.
        for host, name in (("2001:db8:0:0::5", "[2001:db8::5]"), ("[2001:DB8::5]", "[2001:db8::5]"), ("::", "[::]"),
                           ("fe80::1%eth0", "[fe80::1]"), ("::ffff:127.0.0.2", "127.0.0.2"),
                           ("192.168.1.5", "192.168.1.5"), ("Example.LAN", "example.lan")):
            with self.subTest(host=host):
                self.assertEqual(app._bind_host_name(host), name)
        # The server allows that form (not bound: the address need not exist on this host).
        with mock.patch.object(app.ThreadingHTTPServer, "server_bind"), mock.patch.object(app.ThreadingHTTPServer, "server_activate"):
            server = app.AppServer(("2001:db8:0:0::5", 0))
        try:
            self.assertTrue(server.host_allowed("[2001:db8::5]"))
            self.assertTrue(server.host_allowed("[2001:db8:0:0::5]"))  # urllib and http.client send the literal as typed
            self.assertFalse(server.host_allowed("[2001:db8::6]"))
        finally:
            server.server_close()
        # A name, or a literal the resolver rewrites, binds another address: both are served.
        def bind(server: app.AppServer) -> None:
            server.server_address = ("192.168.1.5", 0)

        with mock.patch.object(app, "_address_family", return_value=socket.AF_INET), \
                mock.patch.object(app.ThreadingHTTPServer, "server_bind", bind), mock.patch.object(app.ThreadingHTTPServer, "server_activate"):
            server = app.AppServer(("FPC-Box.LAN", 0))
        try:
            self.assertTrue(server.host_allowed("fpc-box.lan"))
            self.assertTrue(server.host_allowed("192.168.1.5"))
            self.assertTrue(server.host_allowed("[::ffff:c0a8:105]"))  # what browsers send for http://[::ffff:192.168.1.5]/
            self.assertFalse(server.host_allowed("192.168.1.6"))
        finally:
            server.server_close()
        try:
            server = app.AppServer(("127.0.0.2", 0))
        except OSError:
            self.skipTest("127.0.0.2 is not a loopback address on this host")
        try:
            self.assertTrue(server.host_allowed("127.0.0.2"))
            self.assertTrue(server.host_allowed("[::ffff:7f00:2]"))  # what browsers send for http://[::ffff:127.0.0.2]/
            self.assertFalse(server.host_allowed("127.0.0.3"))
        finally:
            server.server_close()

    def test_configured_host_is_accepted_in_the_host_header(self) -> None:
        server = app.AppServer(("127.0.0.1", 0))
        try:
            self.assertEqual(server.allowed_hosts, {"localhost", "127.0.0.1", "[::1]"})
        finally:
            server.server_close()
        self.assertEqual(app._host_header_name("[::1]:8008"), "[::1]")
        self.assertEqual(app._host_header_name("::1"), "[::1]")
        self.assertEqual(app._host_header_name("Example.LAN:80"), "example.lan")


if __name__ == "__main__":
    unittest.main()
