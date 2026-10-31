"""Browser checks of the static site (tools/build_static_site.py): the app with its API answered in the browser.

Builds the site (or takes --site, a built one), serves it with a plain static file server under /flexitac-gen/, as
GitHub Pages serves a project site, and checks it against a running app.py (FPC_PORT, as the other checks):

* every API answer of the page's in-browser engine (window.apiFetch: Pyodide in a Web Worker) equals app.py's, byte
  for byte with its status and headers: the defaults, the schema, validate, generate, the four exports, a surface
  fit of the UMI finger and the error replies (400, 404, 405, 413-free malformed bodies, 415, 422);
* the page opens under the subpath without a console error, a failed request or a request outside its folder, and
  no request reaches the file server's /api/ (the API never leaves the browser);
* the default part's sensor is built (Gen by Surface, the shipped fit) and its downloads equal app.py's exports of
  the same design, under the same names.

    FPC_PORT=18801 python3 tools/browser/static_checks.py [--site DIR | --pyodide-archive pyodide-core-0.27.8.tar.bz2]
"""
from __future__ import annotations

import argparse
import base64
import functools
import hashlib
import json
import os
import struct
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402
from rp import PORT, SCRATCH, check, summary, wait_until  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_static_site  # noqa: E402
from engine.core import SURFACE_TEMPLATE_ID  # noqa: E402

SERVER = f"http://127.0.0.1:{PORT}"
STATIC_PORT = int(os.environ.get("FPC_STATIC_PORT", str(PORT + 1)))
SUBPATH = "flexitac-gen"
SITE_URL = f"http://127.0.0.1:{STATIC_PORT}/{SUBPATH}/"
UMI = ROOT / "web" / "vendor" / "umi"
SURFACE_TYPE = "application/x-tactile-surface"
SETTLED = """() => { const s = JSON.parse(document.getElementById('cadState').textContent);
    return ['done', 'stopped', 'failed'].includes(s.default_build) && s.busy.length === 0 && s.pending_build === null; }"""
# One request through the page's apiFetch; the reply as the checks compare it.
API_FETCH = """async ([path, method, type, text, base64]) => {
  const body = base64 !== null ? Uint8Array.from(atob(base64), c => c.charCodeAt(0)) : text;
  const init = {method};
  if (body !== null) { init.body = body; init.headers = {'Content-Type': type}; }
  const reply = await window.apiFetch(path, init);
  const bytes = new Uint8Array(await reply.arrayBuffer());
  let binary = ''; for (let i = 0; i < bytes.length; i += 32768) binary += String.fromCharCode(...bytes.subarray(i, i + 32768));
  return {status: reply.status, headers: Object.fromEntries(reply.headers), body: btoa(binary)};
}"""
COMPARED_HEADERS = ("content-type", "content-disposition", "x-build-id", "x-design-sha256", "allow")


class QuietFiles(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".wasm": "application/wasm", ".js": "text/javascript", ".mjs": "text/javascript"}
    seen: list = []

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        QuietFiles.seen.append(self.path)
        super().do_GET()

    def do_POST(self):
        QuietFiles.seen.append(self.path)
        self.send_error(405)


def serve(root: Path):
    server = ThreadingHTTPServer(("127.0.0.1", STATIC_PORT), functools.partial(QuietFiles, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def server_reply(path, method="GET", content_type=None, body=None):
    request = urllib.request.Request(SERVER + path, data=body, method=method, headers={"Content-Type": content_type} if content_type else {})
    try:
        with urllib.request.urlopen(request, timeout=300) as reply:
            return {"status": reply.status, "headers": {k.lower(): v for k, v in reply.headers.items()}, "body": reply.read()}
    except urllib.error.HTTPError as error:
        return {"status": error.code, "headers": {k.lower(): v for k, v in error.headers.items()}, "body": error.read()}


def page_reply(page, path, method="GET", content_type=None, body=None):
    text = body.decode("utf-8") if isinstance(body, bytes) and content_type == "application/json" else None
    binary = base64.b64encode(body).decode("ascii") if isinstance(body, bytes) and text is None else None
    answer = page.evaluate(API_FETCH, [path, method, content_type, text, binary])
    answer["body"] = base64.b64decode(answer["body"])
    return answer


def same(name, path, method="GET", content_type=None, body=None, page=None):
    """One request both ways: status, compared headers and body bytes equal."""
    started = time.monotonic()
    browser = page_reply(page, path, method, content_type, body)
    seconds = time.monotonic() - started
    server = server_reply(path, method, content_type, body)
    headers = {key: (browser["headers"].get(key), server["headers"].get(key)) for key in COMPARED_HEADERS}
    differs = {key: pair for key, pair in headers.items() if pair[0] != pair[1]}
    ok = browser["status"] == server["status"] and not differs and browser["body"] == server["body"]
    detail = "" if ok else [browser["status"], server["status"], differs, browser["body"][:300], server["body"][:300]]
    check(f"api: {name} ({method} {path}: {server['status']}, {len(server['body'])} bytes) is app.py's, byte for byte [{seconds:.2f} s in the browser]", ok, detail)
    return browser


def frame(header, mesh):
    data = json.dumps(header).encode("utf-8")
    return struct.pack(">I", len(data)) + data + mesh


def part_api(page):
    design = json.dumps(json.loads(server_reply("/api/default")["body"])["design"]).encode("utf-8")
    same("the defaults", "/api/default", page=page)
    same("the surface template's defaults", f"/api/default?template={SURFACE_TEMPLATE_ID}", page=page)
    same("the schema", "/api/schema", page=page)
    same("validate", "/api/validate", "POST", "application/json", design, page=page)
    same("generate (compact)", "/api/generate?view=compact", "POST", "application/json", design, page=page)
    same("generate (full)", "/api/generate", "POST", "application/json", design, page=page)
    for kind in ("top-gerber", "bottom-gerber", "project", "easyeda-pro"):
        same(f"the {kind} export", f"/api/export/{kind}", "POST", "application/json", design, page=page)
    shipped = json.loads((UMI / "default-fit.json").read_text(encoding="utf-8"))
    mesh = (UMI / "UMI-Soft-Gripper-Finger.stl").read_bytes()
    same("the default part's surface fit", "/api/surface/fit", "POST", SURFACE_TYPE, frame(shipped["request"], mesh), page=page)
    same("a surface inspect", "/api/surface/inspect", "POST", SURFACE_TYPE, frame({"name": "UMI-Soft-Gripper-Finger.stl"}, mesh), page=page)
    # The error replies.
    same("an unknown query parameter (400)", "/api/default?view=compact", page=page)
    same("an unknown route (404)", "/api/nothing", page=page)
    same("GET of a POST route (405, Allow)", "/api/generate", page=page)
    same("POST of a GET route (405, Allow)", "/api/default", "POST", "application/json", b"{}", page=page)
    same("a body that is not JSON (400)", "/api/generate", "POST", "application/json", b"{", page=page)
    same("a JSON array body (400)", "/api/validate", "POST", "application/json", b"[]", page=page)
    same("a body sent as text/plain (415)", "/api/validate", "POST", "text/plain", b"{}", page=page)
    same("an export blocked by validation (422)", "/api/export/top-gerber", "POST", "application/json",
         json.dumps({"matrix": {"pitch_x_mm": 1.0, "taxel_width_mm": 0.9}}).encode("utf-8"), page=page)
    same("a JSON body on a surface route (415)", "/api/surface/fit", "POST", "application/json", b"{}", page=page)
    same("a malformed surface frame (422)", "/api/surface/fit", "POST", SURFACE_TYPE, b"\x00\x00", page=page)


def part_page(browser, timings):
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    page = context.new_page()
    problems, outside = [], []
    page.on("console", lambda message: problems.append(f"console {message.type}: {message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: problems.append(f"pageerror: {error}"))
    page.on("requestfailed", lambda request: problems.append(f"failed: {request.url}"))
    page.on("response", lambda response: problems.append(f"HTTP {response.status}: {response.url}") if response.status >= 400 else None)
    page.on("request", lambda request: outside.append(request.url) if request.url.startswith("http") and not request.url.startswith(SITE_URL) else None)
    started = time.monotonic()
    page.goto(SITE_URL)
    wait_until(page, "() => window.apiBackend !== undefined", 20)
    check("the page runs its API in the browser (the build's flexitac-backend meta)", page.evaluate("() => window.apiBackend.mode") == "browser")
    ready = page.evaluate("() => window.apiBackend.ready")
    timings["engine ready"] = time.monotonic() - started
    check("the in-browser engine loads (Pyodide and engine.zip)", ready is True)
    wait_until(page, SETTLED, 180)
    timings["default sensor built"] = time.monotonic() - started
    state = json.loads(page.evaluate("() => document.getElementById('cadState').textContent"))
    check("the default part's sensor is built, with the shipped fit", state.get("default_build") == "done" and state.get("fit_source") == "shipped",
          {key: state.get(key) for key in ("default_part", "default_build", "fit_source")})
    check("the status reports a valid build", "is-ok" in page.get_attribute("#status", "class"), page.inner_text("#status")[:160])
    downloads = {}
    for selector in ('[data-download="design"]', '[data-export="top-gerber"]', '[data-export="bottom-gerber"]', '[data-export="project"]', '[data-export="easyeda-pro"]'):
        with page.expect_download(timeout=120000) as info:
            page.click(selector)
        download = info.value
        path = Path(SCRATCH) / "downloads" / f"static-{download.suggested_filename}"
        download.save_as(path)
        downloads[selector] = (download.suggested_filename, path.read_bytes())
    design = downloads['[data-download="design"]'][1]
    for kind in ("top-gerber", "bottom-gerber", "project", "easyeda-pro"):
        name, data = downloads[f'[data-export="{kind}"]']
        reply = server_reply(f"/api/export/{kind}", "POST", "application/json", design)
        check(f"the page's {kind} download is app.py's export of its design, under its name",
              reply["status"] == 200 and data == reply["body"] and f'filename="{name}"' in reply["headers"].get("content-disposition", ""),
              [name, reply["status"], reply["headers"].get("content-disposition"), hashlib.sha256(data).hexdigest()[:12], hashlib.sha256(reply["body"]).hexdigest()[:12]])
    part_api(page)
    check("no console error, failed request or HTTP error", not problems, problems[:8])
    check(f"every request stays under /{SUBPATH}/ (relative URLs; no other host)", not outside, outside[:8])
    context.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--site", type=Path, default=None, help="a site tools/build_static_site.py built (default: build one)")
    parser.add_argument("--pyodide-archive", type=Path, default=None, help="passed to the build")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="flexitac-site-") as scratch:
        root = Path(scratch)
        site = root / SUBPATH
        if args.site is None:
            build_static_site.build(site, args.pyodide_archive)
        else:
            site.symlink_to(args.site.resolve(), target_is_directory=True)
        files = serve(root)
        timings = {}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader"])
                part_page(browser, timings)
                browser.close()
        finally:
            files.shutdown()
        check("the file server got no /api/ request (the API never leaves the browser)",
              not [path for path in QuietFiles.seen if "/api/" in path], [path for path in QuietFiles.seen if "/api/" in path][:5])
        print("timings:", ", ".join(f"{name} {seconds:.1f} s" for name, seconds in timings.items()))
    return 0 if summary() else 1


if __name__ == "__main__":
    sys.exit(main())
