"""Browser checks of the static site (tools/build_static_site.py): the app with its API answered in the browser.

Builds the site (or takes --site, a built one), serves it with a plain static file server under /flexitac-gen/, as
GitHub Pages serves a project site, and checks it against a running app.py (FPC_PORT, as the other checks):

* every API answer of the page's in-browser engine (window.apiFetch: Pyodide in a Web Worker) equals app.py's, byte
  for byte with its status and headers: the defaults, the schema, validate, generate, the four exports, a surface
  fit of the UMI finger and the error replies (400, 404, 405, 413-free malformed bodies, 415, 422);
* the page opens under the subpath without a console error, a failed request or a request outside its folder, and
  no request reaches the file server's /api/ (the API never leaves the browser);
* the Library (part_library_site, 2026-11-05): the Library (./, the first page since 2026-11-16) and a sensor's page
  without a 4xx or a request for the engine, files.json listing every sensor, four sensors' prebuilt ZIPs app.py's
  exports (a tapered tip's among them), the FlexiTac hardware's four files (2026-11-17: the pad's Gerber ZIPs and the
  reading boards' bundles) served at their pins as BUILD.json records them, gen.html?part=<id> built from its shipped fit in the browser's engine with its
  own downloads the prebuilt files (three sensors, a tapered tip's among them, timed);
* the default part's sensor is built (Gen by Surface, the shipped fit) and its downloads equal app.py's exports of
  the same design, under the same names; the sensor on the part beside the stacked view (2026-11-05) is drawn there
  too, its art through data: URLs under the site's CSP;
* the FlexiTac team's footer (2026-11-15) closes both built pages with Awesome-FlexiTac's links;
* the first page (part_first_page, the user's decision of 2026-11-16, "是的 be first page"): the site's folder shows
  the Library, the generator is gen.html, and every address of before (rp.FORWARDS: ./?part=<id>, ./#rect, ...,
  library.html#<id>) is forwarded with its query and hash, no history entry of its own and nothing of its page painted,
  the Library's own addresses staying; the Library refreshes the header's counts from GitHub's API as the generator
  does (web/counts.js, the review of 2026-11-16: the first page had kept the build's counts), every context of the run
  answering GitHub's API here (rp.answer_github; part_page's own answer counts its page's asks).

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
from rp import CARD, FORWARDS, GITHUB_ASKED, GITHUB_CARD, PORT, SCRATCH, answer_github, check, forwarding, summary, wait_until  # noqa: E402

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
    # The header's GitHub counts (web/counts.js since 2026-11-16, web/backend.js before): answered here, as GitHub's API
    # would (its hourly limit stays out of the check).
    asked = []
    page.route(build_static_site.GITHUB_API, lambda route: (asked.append(route.request.url), route.fulfill(
        status=200, content_type="application/json", body=json.dumps({"stargazers_count": 1234, "forks_count": 56})))[-1])
    started = time.monotonic()
    # ?probe: the sensor on the part compared with the map (main.js ON_PART_PROBE; a visitor's page skips it).  The
    # generator's page is gen.html since the user's decision of 2026-11-16 (the Library the first page).
    page.goto(SITE_URL + "gen.html?probe")
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
    wait_until(page, "() => ['drawn', 'failed', 'unavailable', 'empty'].includes(JSON.parse(document.getElementById('cadState').textContent).on_part?.state)", 120)
    timings["sensor on the part drawn"] = time.monotonic() - started
    on_part = json.loads(page.evaluate("() => document.getElementById('cadState').textContent"))["on_part"]
    check("the sensor on the part is drawn for the default build, where the map puts it (within 0.005 mm)",
          on_part["state"] == "drawn" and on_part["build_id"] == state.get("generated_build_id") and on_part["taxel_error_mm"] < 0.005
          and max(on_part["outline_error_mm"].values()) < 0.005, {key: on_part.get(key) for key in ("state", "note", "build_id", "taxel_error_mm", "outline_error_mm")})
    downloads = {}
    page.click("#moreFiles > summary")  # the other files are folded (2026-11-02)
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
    footer = page.evaluate(FOOTER)
    check("the FlexiTac team's footer (2026-11-15) closes the built page: Awesome-FlexiTac's links, in a new tab but the mail", footer == FOOTER_LINKS, footer)
    check("no console error, failed request or HTTP error", not problems, problems[:8])
    card = page.evaluate("() => [document.querySelector('[data-gh-stars]').textContent, document.querySelector('[data-gh-forks]').textContent, document.querySelector('[data-gh-stats]').hidden, document.querySelector('[data-gh-badge]').getAttribute('aria-label')]")
    check("the header's GitHub card shows the repository's stars and forks from GitHub's API (1.2k, 56), as flexitac.github.io",
          asked == [build_static_site.GITHUB_API] and card == ["1.2k", "56", False, "FlexiTac on GitHub: 1234 stars, 56 forks"], (asked, card))
    check(f"every request stays under /{SUBPATH}/ (relative URLs; no other host but GitHub's API for those counts)",
          [url for url in outside if url != build_static_site.GITHUB_API] == [], outside[:8])
    context.close()



LIBRARY = ROOT / "web" / "library"
# The FlexiTac team's footer (the user's request of 2026-11-15) on both built pages: its links (text, address, target).
FOOTER = "() => [...document.querySelectorAll('footer.site-footer .site-footer-main a')].map(a => [a.textContent, a.getAttribute('href'), a.target])"
FOOTER_LINKS = [["Maintained by the FlexiTac Team", "https://flexitac.github.io/", "_blank"], ["GitHub", "https://github.com/FlexiTac/FlexiTac", "_blank"],
                ["Discord", "https://discord.gg/6gw887Vxms", "_blank"], ["YouTube", "https://www.youtube.com/watch?v=HYmMbsrwWFA", "_blank"],
                ["binghao.huang@columbia.edu", "mailto:binghao.huang@columbia.edu", ""]]


def part_library_site(browser, site, timings):
    """The Library on the static site (the user's requests of 2026-11-05): the Library (./) and a sensor's page load with no
    4xx and no request for the engine (py/); files.json lists every sensor; the prebuilt Gerber ZIPs of four sensors are
    app.py's exports of their designs, under the same names (one a tapered tip, the narrowest convex arc); gen.html?part=<id> in
    Pyodide builds its sensor from the shipped fit and its own two Gerber downloads are the prebuilt files (the WidowX 250
    at 1 mm, the Trossen sock of 75,400 facets, and the tapered tips' default, the 13.8 mm trapezoid, timed)."""
    entries = json.loads((LIBRARY / "entries.json").read_text(encoding="utf-8"))
    files = json.loads((site / "static" / "library" / "files.json").read_text(encoding="utf-8"))
    check("library: files.json lists every sensor of entries.json with its build id", sorted(files["variants"]) == sorted(entries["variants"])
          and all(files["variants"][key]["build_id"] == value["build_id"] for key, value in entries["variants"].items()), sorted(files["variants"])[:4])
    for identifier in ("umi-finray-2mm", "widowx-250-1mm", "i2rt-yam-4mm", "umi-convex-tip5.8-2mm"):
        design = json.loads((LIBRARY / entries["variants"][identifier]["fit"]).read_text(encoding="utf-8"))["reply"]["proposals"][0]["design"]
        for kind in ("top-gerber", "bottom-gerber"):
            record = files["variants"][identifier][kind]
            reply = server_reply(f"/api/export/{kind}", "POST", "application/json", json.dumps(design).encode("utf-8"))
            data = (site / "static" / "library" / record["path"]).read_bytes()
            check(f"library: {identifier}'s prebuilt {kind} is app.py's export of its design, under its name",
                  reply["status"] == 200 and data == reply["body"] and f'filename="{record["name"]}"' in reply["headers"].get("content-disposition", ""), record["name"])
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    page = context.new_page()
    problems, engine = [], []
    page.on("console", lambda message: problems.append(f"console {message.type}: {message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: problems.append(f"pageerror: {error}"))
    page.on("response", lambda response: problems.append(f"HTTP {response.status}: {response.url}") if response.status >= 400 else None)
    page.on("request", lambda request: engine.append(request.url) if "/py/" in request.url or "backend.js" in request.url else None)
    for fragment in ("", "#umi-tapers", "#widowx-250-1mm"):
        page.goto(SITE_URL + fragment)
        wait_until(page, "() => document.querySelectorAll('.lib-card').length > 0", 30)
    wait_until(page, "() => document.querySelectorAll('a.lib-pill[data-export]').length === 2", 30)
    links = page.evaluate("() => [...document.querySelectorAll('a.lib-pill[data-export]')].map(a => [a.getAttribute('href'), a.getAttribute('download')])")
    record = files["variants"]["widowx-250-1mm"]
    footer = page.evaluate(FOOTER)
    check("library: the FlexiTac team's footer (2026-11-15) closes the Library too, the generator's links", footer == FOOTER_LINKS, footer)
    check("library: the Library (./) and a sensor's page load with no 4xx and no request for the engine; its ZIPs are plain links to the prebuilt files",
          not problems and not engine and links == [[f"static/library/{record[kind]['path']}", record[kind]["name"]] for kind in ("top-gerber", "bottom-gerber")],
          (problems[:4], engine[:4], links))
    # The FlexiTac hardware's files (2026-11-17; web/boards.js, tools/flexitac_downloads.py): served by the site's file
    # server at their pins, each the one BUILD.json records, the reading board's link on the sensor's page among them.
    import flexitac_downloads
    hardware = json.loads((site / "static" / "py" / "BUILD.json").read_text(encoding="utf-8")).get("hardware") or {}
    served = {}
    for path, digest in hardware.items():
        with urllib.request.urlopen(SITE_URL + path, timeout=60) as answer:
            served[path] = (answer.status, hashlib.sha256(answer.read()).hexdigest() == digest)
    pins = {f"static/vendor/{flexitac_downloads.FPC_FOLDER}/{name}": pin[0] for name, pin in flexitac_downloads.FPC_FILES.items()}
    pins.update({f"static/vendor/{flexitac_downloads.READER_FOLDER}/{board['bundle'][0]}": board["bundle"][1] for board in flexitac_downloads.BOARDS.values()})
    board = page.get_attribute(".lib-board a[download]", "href")
    check("library: the FlexiTac hardware's four files served at their pins (BUILD.json's hardware), the sensor's reading board among them",
          hardware == pins and served == {path: (200, True) for path in pins} and board in pins, (served, board))
    for identifier in ("widowx-250-1mm", "trossen-widowx-ai-2mm", "umi-trap-tip13.8-2mm"):
        started = time.monotonic()
        page.goto(SITE_URL + f"gen.html?part={identifier}")
        wait_until(page, SETTLED, 300)
        seconds = time.monotonic() - started
        timings[f"?part={identifier} built"] = seconds
        state = json.loads(page.evaluate("() => document.getElementById('cadState').textContent"))
        check(f"library: gen.html?part={identifier} in the browser's engine builds its sensor from the shipped fit, its build id [{seconds:.1f} s, at most 240 s]",
              state.get("default_build") == "done" and state.get("fit_source") == "shipped" and seconds <= 240
              and (state.get("proposal") or {}).get("build_id") == entries["variants"][identifier]["build_id"],
              {key: state.get(key) for key in ("default_part", "default_build", "fit_source")})
        if identifier != "widowx-250-1mm":
            continue
        for kind in ("top-gerber", "bottom-gerber"):
            with page.expect_download(timeout=180000) as info:
                page.click(f'[data-export="{kind}"]')
            download = info.value
            path = Path(SCRATCH) / "downloads" / f"static-library-{download.suggested_filename}"
            download.save_as(path)
            check(f"library: the generator's own {kind} download of {identifier} is the prebuilt file, under its name",
                  path.read_bytes() == (site / "static" / "library" / record[kind]["path"]).read_bytes() and download.suggested_filename == record[kind]["name"],
                  download.suggested_filename)
    check("library: no console error or HTTP error on the site's Library and gen.html?part", not problems, problems[:6])
    context.close()

def part_first_page(browser):
    """The first page on the built site (the user's decisions of 2026-11-15 and 2026-11-16: "是的 be first page"): the
    site's folder (index.html) is the Library, gen.html the generator, library.html a forwarding page; every address of
    rp.FORWARDS opened after an earlier page ends where it should, its query and hash kept, with no history entry of
    its own (Back the earlier page) and nothing of its own page painted; the Library's own addresses stay."""
    seen = forwarding(browser, SITE_URL)
    wrong = {address: seen[address] for address, target in FORWARDS
             if not (seen[address]["url"] == seen[address]["final"] and seen[address]["added"] == 1 and seen[address]["back"]
                     and (bool(seen[address]["shown"]) if target is None else not seen[address]["shown"]))}
    check(f"first page: each of the {len(FORWARDS)} addresses of rp.FORWARDS on the built site: the generator's of before (./?part=<id>, ./#rect, "
          "./#cad, ?sample, ?debug, its anchors, ./index.html's) at gen.html and library.html's at ./, their query and hash kept, no history "
          "entry of their own and nothing of their page painted; the Library's own (its sensors, places, the showcase, ?probe) staying, painted",
          wrong == {}, wrong)
    check("first page: the site's folder is the Library and gen.html the generator",
          seen[""]["title"] == "Library · FlexiTac-Gen" and seen["#rect"]["title"] == "FlexiTac-Gen", (seen[""]["title"], seen["#rect"]["title"]))
    # The header's counts on the first page (the review of 2026-11-16): refreshed from GitHub's API (answered here) as on
    # the generator, asked once by the Library's page, kept for the tab (gen.html in it asks no more).
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    asked = len(GITHUB_ASKED)
    page.goto(SITE_URL)
    wait_until(page, "() => !document.querySelector('[data-gh-stats]').hidden", 15)
    library = page.evaluate(CARD)
    page.goto(SITE_URL + "gen.html#rect")
    wait_until(page, "() => !document.querySelector('[data-gh-stats]').hidden", 15)
    generator = page.evaluate(CARD)
    check("first page: the Library at the site's folder refreshes the header's counts from GitHub's API (1.2k, 56), asked once; gen.html in "
          "the same tab shows them without asking again", library == GITHUB_CARD and generator == GITHUB_CARD and GITHUB_ASKED[asked:] == [SITE_URL],
          (library, generator, GITHUB_ASKED[asked:]))
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
            # A local site served from a scratch folder, never published: it may hold files pending a licence (the
            # review of 2026-11-17, the LeFlexiTac; tools/build_static_site.py --allow-pending-licences).
            build_static_site.build(site, args.pyodide_archive, allow_pending=True)
        else:
            site.symlink_to(args.site.resolve(), target_is_directory=True)
        files = serve(root)
        timings = {}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader"])
                answer_github(browser)  # both built pages ask GitHub's API for the header's counts (web/counts.js)
                part_page(browser, timings)
                part_library_site(browser, site, timings)  # the Library (2026-11-05)
                part_first_page(browser)  # the Library the first page (2026-11-16)
                browser.close()
        finally:
            files.shutdown()
        check("the file server got no /api/ request (the API never leaves the browser)",
              not [path for path in QuietFiles.seen if "/api/" in path], [path for path in QuietFiles.seen if "/api/" in path][:5])
        print("timings:", ", ".join(f"{name} {seconds:.1f} s" for name, seconds in timings.items()))
    return 0 if summary() else 1


if __name__ == "__main__":
    sys.exit(main())
