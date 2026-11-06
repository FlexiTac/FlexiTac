"""The thumbnails of Gen by Surface's samples (web/samples/samples.json, the step guide's "Try a sample"; the user's
request of 2026-11-06): each sample's part drawn once in the 3D view's look and written as web/samples/thumbs/<id>.webp.

    FPC_PORT=19400 /tmp/fpc-browser-venv/bin/python tools/browser/sample_thumbs.py              # every sample
    ... sample_thumbs.py --only arx-x5,widowx-250-gripper                                    # some
    ... sample_thumbs.py --check                                                             # draw again, compare
    ... sample_thumbs.py --out /tmp/thumbs --sheet /tmp/thumbs/sheet.png                     # elsewhere, with a sheet

Against a running app.py (--port, else FPC_PORT) serving this project, in headless Chromium on SwiftShader (as
cad_checks.py), for each sample in samples.json's order:
1. a page of the server's origin (served by this tool through Playwright's routing, so no change to the app) imports
   the page's own web/cad/viewer.js and stl.js and makes the 3D view (createViewer) in a RENDER_CSS box at DPR 1: the
   part's grey, the studio's lights and reflections, the tone mapping and the view's #f5f5f7, exactly as Gen by Surface
   draws a model; only its axes helper is left out (three.js's Object3D.add skips an AxesHelper on this page);
2. the sample's mesh (a Library finger's web/library/meshes/ file, a whole gripper's web/samples/ file, each in its
   unit: a Library part's entries.json record) is parsed by stl.js, turned so that its thumb.view's dir (toward the
   camera, in the mesh's axes) faces the camera and its up is the picture's up, shown with no facet hidden and framed
   by the view's lookAt (the part's bounding sphere);
3. the view is screenshot, the part's drawn pixels found (more than 6 sRGB levels off the background), cropped with
   MARGIN of the larger side around them, padded with the background to THUMB's aspect, scaled (Lanczos) to THUMB and
   written by Pillow as lossy WebP (QUALITY, method 6).
The thumbnails are drawn on the 3D view's grey, a lightbox like the view itself in the dark scheme too (web/theme.css).
The same code gives the same bytes on the same Chromium and Pillow: --check draws again and compares each file, writing
nothing.  About 1 s a sample.  Needs Playwright and Pillow (the checks' environment).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
SAMPLES = WEB / "samples"
WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
RENDER_CSS = (720, 480)
THUMB = (240, 110)
MARGIN = 0.06
QUALITY = 82
BACKGROUND = (0xF5, 0xF5, 0xF7)
PAGE = "/__sample_thumbs.html"
# The drawing page: the page's own viewer in a box of RENDER_CSS, show() drawing one mesh turned to its view.
HTML = """<!doctype html><html><head><meta charset="utf-8"><title>sample thumbnails</title>
<style>html,body{margin:0;background:#fff}#host{position:relative;width:%dpx;height:%dpx}</style></head>
<body><div id="host"></div><script type="module">
import * as THREE from "./static/vendor/three/three.module.js";
const add = THREE.Object3D.prototype.add;
THREE.Object3D.prototype.add = function (...objects) {
  const kept = objects.filter(object => object?.type !== "AxesHelper");
  return kept.length ? add.apply(this, kept) : this;
};
const {createViewer} = await import("./static/cad/viewer.js");
const {parseStl} = await import("./static/cad/stl.js");
const viewer = createViewer(document.getElementById("host"));
const norm = v => { const l = Math.hypot(...v); return v.map(x => x / l); };
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
window.show = async ([url, scale, view]) => {
  const parsed = parseStl(await (await fetch(url)).arrayBuffer());
  // The view's frame (right, up, toward the camera) onto the 3D view's -y view: x right, z up, the camera on -y.
  const back = norm(view.dir); const up = norm(view.up.map((x, i) => x - dot(view.up, back) * back[i])); const right = cross(up, back);
  const p = parsed.positions; const turned = new Float32Array(p.length);
  const low = [Infinity, Infinity, Infinity]; const high = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < p.length; i += 3) {
    const v = [p[i] * scale, p[i + 1] * scale, p[i + 2] * scale];
    const t = [dot(right, v), -dot(back, v), dot(up, v)];
    for (let k = 0; k < 3; k += 1) { turned[i + k] = t[k]; low[k] = Math.min(low[k], t[k]); high[k] = Math.max(high[k], t[k]); }
  }
  viewer.setMesh(turned, 1, []);
  const centre = [0, 1, 2].map(k => (low[k] + high[k]) / 2);
  viewer.lookAt(centre, [0, -1, 0], 0.5 * Math.hypot(high[0] - low[0], high[1] - low[1], high[2] - low[2]));
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  return {facets: parsed.facets, info: viewer.info()};
};
window.thumbsReady = true;
</script></body></html>""" % RENDER_CSS


class ThumbError(Exception):
    pass


def samples() -> list:
    return json.loads((SAMPLES / "samples.json").read_text(encoding="utf-8"))["samples"]


def mesh_of(sample: dict, entries: dict) -> tuple:
    """(the mesh's URL on the server, its scale to mm) of one sample."""

    if "mesh" in sample:
        return f"static/samples/{sample['mesh']['file']}", 1000 if sample["mesh"]["unit"] == "m" else 1
    part = entries["parts"][entries["variants"][sample["library"]]["part"]]
    return f"static/library/{part['mesh']['file']}", 1000 if part["mesh"]["unit"] == "m" else 1


def encode(png: bytes) -> bytes:
    """The thumbnail (WebP) of one screenshot: the drawn part cropped, padded to THUMB's aspect and scaled."""

    from PIL import Image, ImageChops

    image = Image.open(io.BytesIO(png)).convert("RGB")
    plain = Image.new("RGB", image.size, BACKGROUND)
    difference = ImageChops.difference(image, plain).convert("L").point(lambda value: 255 if value > 6 else 0)
    box = difference.getbbox()
    if box is None:
        raise ThumbError("nothing drawn")
    if box[0] == 0 or box[1] == 0 or box[2] == image.size[0] or box[3] == image.size[1]:
        raise ThumbError(f"the part reaches the view's edge ({box}): it is cut")
    width, height = box[2] - box[0], box[3] - box[1]
    margin = MARGIN * max(width, height)
    aspect = THUMB[0] / THUMB[1]
    out_w = max(width + 2 * margin, (height + 2 * margin) * aspect)
    out_h = out_w / aspect
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    left, top = round(cx - out_w / 2), round(cy - out_h / 2)
    canvas = Image.new("RGB", (round(out_w), round(out_h)), BACKGROUND)
    canvas.paste(image.crop((max(0, left), max(0, top), min(image.size[0], left + round(out_w)), min(image.size[1], top + round(out_h)))),
                 (max(0, -left), max(0, -top)))
    thumb = canvas.resize(THUMB, Image.LANCZOS)
    buffer = io.BytesIO()
    thumb.save(buffer, "WEBP", quality=QUALITY, method=6)
    return buffer.getvalue()


def draw(port: int, chosen: list) -> dict:
    """{sample id: its WebP bytes}."""

    from playwright.sync_api import sync_playwright

    entries = json.loads((WEB / "library" / "entries.json").read_text(encoding="utf-8"))
    out = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=WEBGL_ARGS)
        context = browser.new_context(viewport={"width": RENDER_CSS[0] + 40, "height": RENDER_CSS[1] + 40}, device_scale_factor=1, color_scheme="light")
        page = context.new_page()
        errors = []
        page.on("console", lambda message: errors.append(message.text) if message.type in ("error", "warning") else None)
        page.on("pageerror", lambda error: errors.append(str(error)))
        origin = f"http://127.0.0.1:{port}"
        page.route(origin + PAGE, lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8", body=HTML))
        page.goto(origin + PAGE)
        for _ in range(300):
            if page.evaluate("() => window.thumbsReady === true"):
                break
            page.wait_for_timeout(50)
        else:
            raise ThumbError(f"the drawing page did not start: {errors[:3]}")
        for sample in chosen:
            url, scale = mesh_of(sample, entries)
            drawn = page.evaluate("(args) => show(args)", [url, scale, sample["thumb"]["view"]])
            if not drawn["facets"]:
                raise ThumbError(f"{sample['id']}: no facet drawn")
            out[sample["id"]] = encode(page.locator("#host").screenshot())
        browser.close()
    if errors:
        raise ThumbError(f"console errors or warnings: {errors[:3]}")
    return out


def sheet(files: dict, path: Path) -> None:
    from PIL import Image

    images = [Image.open(io.BytesIO(data)).convert("RGB") for data in files.values()]
    board = Image.new("RGB", (2 * THUMB[0] + 30, (len(images) + 1) // 2 * (THUMB[1] + 10) + 10), "white")
    for index, image in enumerate(images):
        board.paste(image, (10 + (index % 2) * (THUMB[0] + 10), 10 + (index // 2) * (THUMB[1] + 10)))
    board.save(path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--port", type=int, default=int(os.environ.get("FPC_PORT", "8008")))
    parser.add_argument("--only", help="comma-separated sample ids (default: every sample)")
    parser.add_argument("--check", action="store_true", help="draw again and compare; write nothing")
    parser.add_argument("--out", type=Path, default=SAMPLES / "thumbs", help="the folder to write (default web/samples/thumbs)")
    parser.add_argument("--sheet", type=Path, help="also write a contact sheet (PNG) of the thumbnails drawn")
    args = parser.parse_args(argv)
    listed = samples()
    wanted = set(args.only.split(",")) if args.only else {sample["id"] for sample in listed}
    unknown = wanted - {sample["id"] for sample in listed}
    if unknown:
        print(f"sample_thumbs: no sample is named {', '.join(sorted(unknown))}", file=sys.stderr)
        return 1
    chosen = [sample for sample in listed if sample["id"] in wanted]
    try:
        files = draw(args.port, chosen)
    except ThumbError as error:
        print(f"sample_thumbs: {error}", file=sys.stderr)
        return 1
    differ = []
    for sample in chosen:
        data = files[sample["id"]]
        path = args.out / Path(sample["thumb"]["src"]).name
        if args.check:
            same = path.is_file() and path.read_bytes() == data
            if not same:
                differ.append(sample["id"])
            print(f"{sample['id']}: {'same' if same else 'differs'} ({len(data)} bytes)")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"{sample['id']}: wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path} ({len(data)} bytes)")
    if args.sheet:
        sheet(files, args.sheet)
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main())
