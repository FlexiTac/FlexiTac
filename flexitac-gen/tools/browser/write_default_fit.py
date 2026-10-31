"""Write web/vendor/umi/default-fit.json: the fit of CAD mode's default part, shipped so its sensor shows at once.

The app opens in CAD mode ("Gen by Surface") with the UMI finger loaded and its sensor generated on a border of its
contact face (web/cad/main.js DEFAULT_PART, buildDefaultSensor).  Its fit is the slow step, so the page ships it: when
the browser's fit request is this file's ``request`` (compared key by key), it takes this file's ``reply`` instead of
asking the server.  This writer opens the app against a running app.py (FPC_PORT, as the other browser checks), with
the shipped file refused so the fit goes to the server, and records the request the browser sent and the reply.

tests/test_surface_web.py checks the file against the engine (the reply of surface.api.fit for the request); re-run this
after a change of the fit, the surface template or the default part's settings (the page's defaults among them), and the
browser check cad_checks.part_default_cad confirms that the page takes it (fit_source "shipped").

    FPC_PORT=8008 python3 tools/browser/write_default_fit.py
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402
from rp import URL, wait_until  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
UMI = ROOT / "web" / "vendor" / "umi"
OUT = UMI / "default-fit.json"
MESH = UMI / "UMI-Soft-Gripper-Finger.stl"
WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
SETTLED = """() => { const s = JSON.parse(document.getElementById('cadState').textContent);
    return ['done', 'stopped'].includes(s.default_build) && s.busy.length === 0 && s.pending_build === null; }"""


def main() -> int:
    recorded = {}

    def on_request(request):
        if request.url.endswith("/api/surface/fit") and request.method == "POST":
            body = request.post_data_buffer
            (length,) = struct.unpack(">I", body[:4])
            recorded["request"] = json.loads(body[4:4 + length].decode("utf-8"))
            recorded["mesh_sha256"] = hashlib.sha256(body[4 + length:]).hexdigest()

    def on_response(response):
        if response.url.endswith("/api/surface/fit") and response.request.method == "POST" and response.status == 200:
            recorded["reply"] = response.json()

    with sync_playwright() as p:
        browser = p.chromium.launch(args=WEBGL_ARGS)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.route("**/static/vendor/umi/default-fit.json", lambda route: route.fulfill(status=404, content_type="text/plain", body="being written"))
        page.on("request", on_request)
        page.on("response", on_response)
        page.goto(URL)
        wait_until(page, SETTLED, 120)
        state = json.loads(page.evaluate("() => document.getElementById('cadState').textContent"))
        browser.close()
    if state["default_build"] != "done" or state["fit_source"] != "server" or set(recorded) != {"request", "mesh_sha256", "reply"}:
        print(f"The default sensor was not built from a server fit: {state['default_build']}, {state['fit_source']}, {sorted(recorded)}")
        return 1
    if recorded["mesh_sha256"] != hashlib.sha256(MESH.read_bytes()).hexdigest():
        print("The fit was not of the vendored default part.")
        return 1
    document = {
        "about": "The fit of CAD mode's default part (web/cad/main.js DEFAULT_PART): the request the browser sends and the "
                 "server's reply, taken when the request is this one.  Written by tools/browser/write_default_fit.py; "
                 "tests/test_surface_web.py checks the reply against surface.api.fit.",
        "mesh_sha256": recorded["mesh_sha256"],
        "request": recorded["request"],
        "reply": recorded["reply"],
    }
    OUT.write_text(json.dumps(document, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")
    proposal = recorded["reply"]["proposals"][0]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(recorded['reply']['proposals'])} proposals, #1 {proposal['build_id']} "
          f"({proposal['metrics']['rows']} x {proposal['metrics']['columns']}), {OUT.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
