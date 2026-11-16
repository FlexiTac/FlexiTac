"""The Library's showcase: the original, hand-designed FlexiTac sensor on the UMI finger, drawn by the Library's own 3D
view from a placed record (docs/LIBRARY_VIEW.md "A placed sensor"; the user's request of 2026-11-12), checked and shot;
and the showcase's card and page on the Library itself (part_page).

    FPC_PORT=18801 /tmp/fpc-browser-venv/bin/python tools/browser/showcase_checks.py                   # every part
    ... showcase_checks.py part_wrap part_view                                                         # some
    ... showcase_checks.py part_shots --out /tmp/showcase                                              # the pictures
    ... showcase_checks.py part_page --out /tmp/showcase                                               # the Library's page

Against a running app.py (FPC_PORT) serving this project, in headless Chromium on SwiftShader (as cad_checks.py); with
--url (a site built by tools/build_static_site.py and served from its folder) part_page checks that site instead.  The
pad alone, without its gripper, has no page, so for part_wrap, part_view and part_shots this tool serves one of the
server's origin itself through Playwright's routing (PROBE_HTML and PROBE_JS at static/showcase-probe.html, no change to the app): the Library's style sheets, a sensor page's stage
(.lib-stage with its .lib-shot-detail box and the view's host, .lib-live) and one module that imports the page's own
web/cad/library_view.js, fetches the placed record (web/vendor/flexitac-v2/umi-finray.placed.json: the UMI finger of
web/vendor/umi/, the showcase's art, the pad's face on the finger and its wrap) and calls
createLibraryView(host, {probe: true}).show({base: "library/", id, placed, mode}), as the showcase's page will: no
fit, no entries.json, no engine.  Its state is <pre id="showcaseState">.

- part_wrap: drape.js wrapMapper on the finger, in the page (wrap_checks.js, which tests/test_showcase.py runs under
  node where there is one): the face is the face's plane to the last bit and its normal the face's; no step along or
  across the sheet tears (every step of 0.02 mm at most 1.5 times as long on the part); up to the fold line the roll
  is rigid, and a level line keeps its length all the way round; no point of the roll is inside the finger's section;
  the sheet lifted off the face (the explode) is the sheet at 0, the face's plane lifted, and hangs beside the finger
  once lifted past its reach; the stack (placedStack) explodes by that lift, shows its film through the slots, has no
  vertex inside the finger in either mode, its exploded normals the lifted sheet's own, and can be respaced (the
  Library's stage); on a slab thinner than the bend the sheet turns once, without a tear; where the pad lands: the A's two arms and the Top FPC's tail on the
  side face as level straps, both sets of gold fingers behind the finger, the A's foot 66 to 71 mm and the Top FPC's tab
  70 to 81 mm from the fingertip.
- part_tails: the pad's two tails behind the finger as the view lays them (Assembled), against the numbers the
  showcase's extender board and its sockets are placed by (tools/library_showcase.py): past the roll both lie in
  TAILS_PLANE (within 0.35 mm), the A's foot ends at TAIL_END and the Top FPC's tab at TAB_END (each within 0.3 mm).
- part_view: the view drawn for the placed record in both modes with no console error: the state, no build id, no
  gripper; the canvas shows the boards (amber) and the finger; a mode switch and Reset view keep it drawn; a record
  whose mesh unit the page does not know is refused, and the record itself is drawn again after it.
- part_shots: the pictures (--out DIR, default the checks' scratch folder): Exploded and Assembled, from the front (the
  sensing face, the fingertip up), the side the tails cross, the back, obliquely over that side (as the project page's
  photo of the assembled sensor) and the far side (the straps through the fin's windows), in the light and the dark
  scheme, each the page's stage as a visitor would see it (the view turned with the arrow keys from its home, 5 degrees
  a press, framed again; the picture turned so the fingertip is up and cut to the drawing): <mode>.<view>.<scheme>.png,
  and sheet.<scheme>.png of the ten on the page's background (the stage is a light box in both schemes).
- part_page: the showcase on the Library (./, the first page since 2026-11-16; web/library/showcase.json): at 1440 px the grid's first section
  is the showcase's one card, as wide as the row, its picture (one image, the card file, 4:5, no canvas and no three.js
  on the grid) beside its label, its title and its line; reached with Tab and opened with Enter it gives the showcase's
  own page in the window over the grid (since 2026-11-15), its title focused: the 3D view drawn over the picture from the
  placed record (no build, the scene's gripper, Assembled at its home, the scene's looks and camera, the fingers orange,
  the boards amber), its box 4:5; the window's Tab order (its X first), the Exploded | Assembled control worked with the
  arrow keys, the view turned with them and brought back with 0; the tutorial's link and the two notices (each answered
  by the server); no Open in Gen by Surface, no download; the window's X back to the card, its Details focused.  At 390 px, light and dark: the card stacked within the window, nothing scrolling sideways, the
  page's view drawn in its light box; no console error anywhere.  --out DIR: the pages' screenshots.
  Design your own (the user's decisions of 2026-11-15 and 2026-11-16: "在flexitac on xarm的details 后面，多一个按钮，generate
  sensor by yourself with cad file", named "Design your own"): on the card right after Details, on its line, as tall and
  as round, its type, the page's action blue (light and dark), white words, named "Design your own sensor in Gen by
  Surface", in this tab (no target); the Tab order the picture out of it, Details, then Design your own, its focus ring
  the page's; pressed, Gen by Surface (gen.html) in this tab with no other page, the generator's default part loading,
  and Back the Library; at 390 px (light and dark) and 360 and 320 px side by side within the card where they fit, else
  under Details on its left, its own width; card.<width>.<scheme>.png, the card at 1440 and 390 px, light and dark.
"""
from __future__ import annotations

import argparse
import base64
import colorsys
import io
import json
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
import rp  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PLACED = "vendor/flexitac-v2/umi-finray.placed.json"
WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
PROBE_PATH = "static/showcase-probe.html"
PROBE_HTML = """<!doctype html>
<html lang="en"{theme}>
  <head>
    <meta charset="utf-8" />
    <title>FlexiTac showcase probe</title>
    <link rel="stylesheet" href="styles.css" />
    <link rel="stylesheet" href="theme.css" />
    <link rel="stylesheet" href="library.css" />
    <script type="module" src="showcase-probe.js"></script>
  </head>
  <body>
    <main class="lib" style="padding:24px">
      <div class="lib-stage is-live" style="width:960px"><div class="lib-shot lib-shot-detail"></div><div class="lib-live" tabindex="0"></div></div>
      <pre id="showcaseState" hidden></pre>
    </main>
  </body>
</html>
"""
# The checks of the wrap (wrap_checks.js beside this file: one function, wrapChecks, with no import or export), which the
# probe's module carries and tests/test_showcase.py runs under node where there is one.
WRAP_CHECKS_JS = (Path(__file__).resolve().parent / "wrap_checks.js").read_text(encoding="utf-8")
PROBE_JS = """import {createLibraryView} from "./cad/library_view.js";
import * as D from "./cad/drape.js";
import {parseStl} from "./cad/stl.js";
""" + WRAP_CHECKS_JS + """
const state = document.getElementById("showcaseState");
const say = value => { state.textContent = JSON.stringify(value); };
const query = new URLSearchParams(location.search);
const showcase = {view: null, placed: null, D, wrapChecks, parseStl, error: null};
window.showcase = showcase;
(async () => {
  try {
    showcase.placed = await (await fetch(query.get("placed"))).json();
    showcase.view = createLibraryView(document.querySelector(".lib-live"), {probe: true, onState: what => say({state: "drawn", news: what, ...showcase.view.info()})});
    const drawn = await showcase.view.show({base: "library/", id: showcase.placed.id, placed: showcase.placed, mode: query.get("mode") || "exploded"});
    say({state: drawn ? "drawn" : "superseded", ...showcase.view.info()});
  } catch (error) {
    showcase.error = String(error && error.stack || error);
    say({state: "failed", note: String(error && error.message || error)});
  }
})();
"""
STATE = "() => { const text = document.getElementById('showcaseState')?.textContent; return text ? JSON.parse(text) : null; }"
WRAP = """async () => {
  const {D, wrapChecks, parseStl, placed} = window.showcase;
  const positions = parseStl(await (await fetch('library/' + placed.mesh.file)).arrayBuffer()).positions;
  const bytes = await (await fetch('library/' + placed.art)).arrayBuffer();
  const art = JSON.parse(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text());
  return wrapChecks(D, positions, placed, art);
}"""
# The canvas at the mode's home, read in the frame it is drawn in (three.js keeps no drawing buffer: Reset view asks for
# a render in the figure's requestAnimationFrame callback, ours comes after it), as library_shots.py reads it.
CANVAS = """() => { window.showcase.view.reset(); return new Promise(resolve => requestAnimationFrame(() => {
  const canvas = document.querySelector('.lib-live canvas'); resolve({url: canvas.toDataURL('image/png'), size: [canvas.width, canvas.height]}); })); }"""
KEY = """(key) => { document.querySelector('.lib-live').dispatchEvent(new KeyboardEvent('keydown', {key, bubbles: true, cancelable: true})); }"""
FRAMES = "() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(true))))"
MODES = ("exploded", "assembled")
# Each view from a mode's home (drape.js homeDirection: Exploded 57 degrees off the face's normal, Assembled 35, both
# turned -20 about it; the camera's up the normal): the presses of the arrow keys (onpart.js: 5 degrees each, ArrowLeft
# and ArrowRight about the normal, ArrowDown toward it) and the quarter turns clockwise that bring the fingertip up in
# the picture.  front: 7 (Assembled 5) degrees off the normal from the base's side, the fingertip up as it is.  side: 87
# (85) degrees off it, from the side the tails cross.  back: 172 (170) degrees off it, from behind, over that side.
# oblique: 47 (45) degrees off it over that side, as the project page's photo of the assembled sensor is taken.  far:
# 87 (85) degrees off it from the other side, the straps seen through the fin's windows, as in the photo of the pair.
VIEWS = {
    "front": {"keys": {"exploded": ["ArrowLeft"] * 4 + ["ArrowDown"] * 10, "assembled": ["ArrowLeft"] * 4 + ["ArrowDown"] * 6}, "turns": 0},
    "side": {"keys": {"exploded": ["ArrowRight"] * 14 + ["ArrowUp"] * 6, "assembled": ["ArrowRight"] * 14 + ["ArrowUp"] * 10}, "turns": 1},
    "back": {"keys": {"exploded": ["ArrowRight"] * 14 + ["ArrowUp"] * 23, "assembled": ["ArrowRight"] * 14 + ["ArrowUp"] * 27}, "turns": 1},
    "oblique": {"keys": {"exploded": ["ArrowRight"] * 14 + ["ArrowDown"] * 2, "assembled": ["ArrowRight"] * 14 + ["ArrowUp"] * 2}, "turns": 1},
    "far": {"keys": {"exploded": ["ArrowLeft"] * 22 + ["ArrowUp"] * 6, "assembled": ["ArrowLeft"] * 22 + ["ArrowUp"] * 10}, "turns": 3},
}
SCHEMES = ("light", "dark")


def serve(page, scheme: str) -> None:
    """The probe's page and module at the server's origin (Playwright's routing: nothing is added to the app)."""

    html = PROBE_HTML.format(theme=' data-theme="dark"' if scheme == "dark" else "")
    page.route(re.compile(r"/static/showcase-probe\.html(\?|$)"), lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8", body=html))
    page.route(re.compile(r"/static/showcase-probe\.js$"), lambda route: route.fulfill(status=200, content_type="text/javascript; charset=utf-8", body=PROBE_JS))


def open_probe(browser, scheme: str = "light", mode: str = "exploded", scale: int = 2):
    """A page with the showcase drawn (its state "drawn"), its console errors kept in page.errors."""

    context = browser.new_context(viewport={"width": 1200, "height": 760}, device_scale_factor=scale, color_scheme="dark" if scheme == "dark" else "light")
    page = context.new_page()
    page.errors = []
    page.on("console", lambda message: page.errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page.errors.append(str(error)))
    serve(page, scheme)
    page.goto(f"{rp.URL}{PROBE_PATH}?placed={PLACED}&mode={mode}")
    end = time.monotonic() + 120
    state = None
    while time.monotonic() < end:
        state = page.evaluate(STATE)
        if state and state.get("state") in ("drawn", "failed"):
            break
        page.wait_for_timeout(100)
    page.state = state
    return page


def part_wrap(browser) -> None:
    page = open_probe(browser)
    try:
        rp.check("the probe's page drew the showcase", (page.state or {}).get("state") == "drawn", page.state if (page.state or {}).get("state") != "drawn" else "")
        out = page.evaluate(WRAP)
        rp.check("the wrap has no problem (the face its plane, no tear, level lines and the roll up to the fold line rigid, outside the finger)",
                 out["problems"] == [], out["problems"] or f"{out['steps']} steps: stretch {out['stretch']:.4f}, "
                 f"level {out['level']:.1e}, rigid {out['rigid']:.1e}; the fold line {out['fold']} corners")
        rp.check("the finger's side edge and the explode width are the UMI finger's (12.9 and 25.8 mm)",
                 abs(out["edge_mm"] - 12.9) < 1e-5 and abs(out["width_mm"] - 25.8) < 1e-5 and abs(out["tip_mm"] - 37) < 1e-5,
                 (out["edge_mm"], out["width_mm"], out["tip_mm"]))
        rp.check("the A's two arms and the Top FPC's tail cross the side face as level straps", all(out["straps"].values()), out["straps"])
        stack = out["stack"] or {}
        rp.check("the stack explodes by the lift over the finger's width, the Bottom FPC outermost, its film seen through the slots",
                 (stack.get("explode"), stack.get("film_seen"), stack.get("bottom"), stack.get("top")) == ("lift", True, "column", "row")
                 and abs(stack.get("width_mm", 0) - 25.8) < 1e-5 and abs(stack.get("gap_mm", 0) - 0.55 * 25.8) < 1e-5, stack)
        row, column = out["landing"]["row"], out["landing"]["column"]
        rp.check("the A's gold end lies behind the finger, 66 to 71 mm from the fingertip", row["end_behind"] and 66 <= row["end_tip_mm"][0] and row["end_tip_mm"][1] <= 71.1, row)
        rp.check("the Top FPC's gold end lies behind the finger, 70 to 81 mm from the fingertip", column["end_behind"] and 70 <= column["end_tip_mm"][0] and column["end_tip_mm"][1] <= 81, column)
        rp.check("no console error (wrap)", not page.errors, page.errors[:3])
    finally:
        page.context.close()


# The placed pad's two sheets as the view lays them (drape.js placedStack, Assembled), in the finger's file axes: each
# sheet's points behind the finger (x past 30 mm), the boards' own (the sheets' inside points).
TAILS = """async () => {
  const {D, parseStl, placed} = window.showcase;
  const positions = parseStl(await (await fetch('library/' + placed.mesh.file)).arrayBuffer()).positions;
  const bytes = await (await fetch('library/' + placed.art)).arrayBuffer();
  const art = JSON.parse(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text());
  const low = [Infinity, Infinity, Infinity]; const high = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < positions.length; i += 1) { low[i % 3] = Math.min(low[i % 3], positions[i]); high[i % 3] = Math.max(high[i % 3], positions[i]); }
  const boards = {row: {outline: art.boards.row.outline}, column: {outline: art.boards.column.outline}};
  const stack = D.placedStack({placed, vertices: {positions, scale: 1}, arts: art, boards, partBox: [low, high]});
  const m = stack.partMatrix;
  const into = p => { const d = [p[0] - m[12], p[1] - m[13], p[2] - m[14]];
    return [m[0] * d[0] + m[1] * d[1] + m[2] * d[2], m[4] * d[0] + m[5] * d[1] + m[6] * d[2], m[8] * d[0] + m[9] * d[1] + m[10] * d[2]]; };
  const out = {};
  for (const name of ['top', 'bottom']) {
    const sheet = stack.sheets[name]; const back = [];
    for (let k = 0; k < sheet.count; k += 1) if (sheet.inside[k]) {
      const p = into([sheet.assembled[3 * k], sheet.assembled[3 * k + 1], sheet.assembled[3 * k + 2]]);
      if (p[0] > 30) back.push(p);
    }
    out[name] = back;
  }
  return out;
}"""


def part_tails(browser) -> None:
    """Where the pad's tails end behind the sensor finger, as the view lays them, against the numbers the showcase's
    builder places the extender board and its sockets by (tools/library_showcase.py TAILS_PLANE, TAIL_END, TAB_END)."""

    if str(ROOT / "tools") not in sys.path:
        sys.path.insert(0, str(ROOT / "tools"))
    import library_showcase

    page = open_probe(browser, mode="assembled")
    try:
        rp.check("the probe's page drew the showcase (tails)", (page.state or {}).get("state") == "drawn", page.state if (page.state or {}).get("state") != "drawn" else "")
        sheets = page.evaluate(TAILS)
        at, slope = library_showcase.TAILS_PLANE
        # Past the roll over the side face (y above -23.5) both tails lie in the board's plane.
        flat = [p for name in ("top", "bottom") for p in sheets[name] if p[1] > -23.5]
        worst = max((abs(p[0] - (at + slope * p[2])) for p in flat), default=None)
        rp.check("behind the finger both tails lie in TAILS_PLANE (within 0.35 mm)", bool(flat) and worst < 0.35, f"{len(flat)} points, {worst}")
        for name, (ys, z), what in (("top", library_showcase.TAIL_END, "the A's foot (the wide tail)"), ("bottom", library_showcase.TAB_END, "the Top FPC's tab")):
            points = sheets[name]
            end = max((p[2] for p in points), default=None)
            across = [p[1] for p in points if end is not None and p[2] > end - 0.05]
            sound = end is not None and abs(end - z) < 0.3 and abs(min(across) - ys[0]) < 0.3 and abs(max(across) - ys[1]) < 0.3
            rp.check(f"{what} ends where the board's socket is placed (z {z}, y {ys[0]} to {ys[1]})", sound,
                     (end, (min(across), max(across)) if across else None))
        rp.check("no console error (tails)", not page.errors, page.errors[:3])
    finally:
        page.context.close()


def canvas_image(page):
    from PIL import Image
    import base64

    read = page.evaluate(CANVAS)
    return Image.open(io.BytesIO(base64.b64decode(read["url"].split(",", 1)[1]))).convert("RGBA")


def hue_band(r: int, g: int, b: int, low: float, high: float, value: float) -> bool:
    """Whether an sRGB pixel is a saturated colour (saturation above 0.6, value above ``value``) of a hue from ``low``
    up to ``high`` degrees."""

    hue, saturation, brightness = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return saturation > 0.6 and brightness > value and low <= hue * 360 < high


def share(image, test) -> float:
    """The share of the drawn pixels (alpha above 0) that ``test(r, g, b)`` takes."""

    data = image.tobytes()
    pixels = [(data[k], data[k + 1], data[k + 2]) for k in range(0, len(data), 4) if data[k + 3] > 0]
    return sum(1 for r, g, b in pixels if test(r, g, b)) / max(1, len(pixels))


def part_view(browser) -> None:
    page = open_probe(browser, scale=1)
    try:
        state = page.state or {}
        rp.check("the view is drawn for the placed record: its id, no build, no gripper, Exploded at its home",
                 (state.get("state"), state.get("id"), state.get("build_id"), state.get("gripper"), state.get("mode"), state.get("drawn_mode"), state.get("moved"))
                 == ("drawn", "flexitac-v2-on-umi-finray", None, False, "exploded", "exploded", False), state)
        amber = lambda r, g, b: r > 150 and 60 < g < 190 and b < 90  # noqa: E731
        for mode in MODES:
            page.evaluate("(mode) => { window.showcase.view.setMode(mode); }", mode)
            page.evaluate(FRAMES)
            image = canvas_image(page)
            drawn = sum(1 for alpha in image.tobytes()[3::4] if alpha > 0) / (image.width * image.height)
            info = page.evaluate("() => window.showcase.view.info()")
            rp.check(f"{mode}: the canvas shows the finger and the boards (amber)", info["drawn_mode"] == mode and drawn > 0.05 and share(image, amber) > 0.05,
                     f"drawn {drawn:.3f} of the pane, amber {share(image, amber):.3f} of it")
        page.evaluate("() => { window.showcase.view.reset(); }")
        info = page.evaluate("() => window.showcase.view.info()")
        rp.check("Reset view keeps it drawn at its home", info["id"] == "flexitac-v2-on-umi-finray" and info["moved"] is False, info)
        rp.check("no console error (view)", not page.errors, page.errors[:3])
        # A record whose mesh unit the page does not know is refused (it would be drawn as millimetres); the view then
        # draws the record itself again.
        refused = page.evaluate("""async () => { const {view, placed} = window.showcase;
          try { await view.show({base: 'library/', id: placed.id, placed: {...placed, mesh: {...placed.mesh, unit: 'furlong'}}, mode: 'exploded'}); return null; }
          catch (error) { return String(error && error.message || error); } }""")
        again = page.evaluate("async () => { const {view, placed} = window.showcase; return view.show({base: 'library/', id: placed.id, placed, mode: 'exploded'}); }")
        info = page.evaluate("() => window.showcase.view.info()")
        rp.check("a placed record of an unknown mesh unit is refused, and the record itself is drawn again after it",
                 bool(refused) and "furlong" in refused and again is True and info["id"] == "flexitac-v2-on-umi-finray" and info["drawn_mode"] == "exploded",
                 (refused, again, info["id"], info["drawn_mode"]))
    finally:
        page.context.close()


def shoot(page, mode: str, name: str):
    """The stage's picture in ``mode`` from the view ``name``: the page's stage (its pane and the drawing), turned so the
    fingertip is up."""

    from PIL import Image

    view = VIEWS[name]
    page.evaluate("(mode) => { const view = window.showcase.view; view.setMode(mode); view.reset(); }", mode)
    for key in view["keys"][mode]:
        page.evaluate(KEY, key)
    # Framed again from where it was turned to (the figure frames on a resize), then back to the stage's size.
    page.evaluate("() => { document.querySelector('.lib-stage').style.width = '958px'; }")
    page.evaluate(FRAMES)
    page.evaluate("() => { document.querySelector('.lib-stage').style.width = '960px'; }")
    page.evaluate(FRAMES)
    box = page.evaluate("() => { const r = document.querySelector('.lib-stage').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
    margin = 0
    data = page.screenshot(clip={"x": box[0] - margin, "y": box[1] - margin, "width": box[2] + 2 * margin, "height": box[3] + 2 * margin})
    image = Image.open(io.BytesIO(data)).convert("RGB")
    for _ in range(view["turns"]):
        image = image.transpose(Image.ROTATE_270)
    return cropped(image)


def cropped(image, margin: int = 40):
    """The picture cut to its drawing (what differs from the pane's own colour, the picture's middle left pixel's, by
    more than 6 levels) with ``margin`` px round it."""

    from PIL import Image, ImageChops

    pane = image.getpixel((margin, image.height // 2))
    change = ImageChops.difference(image, Image.new("RGB", image.size, pane)).convert("L").point(lambda level: 255 if level > 6 else 0)
    inner = change.crop((margin, margin, image.width - margin, image.height - margin)).getbbox()
    if not inner:
        return image
    box = (max(0, inner[0]), max(0, inner[1]), min(image.width, inner[2] + 2 * margin), min(image.height, inner[3] + 2 * margin))
    return image.crop(box)


def part_shots(browser, out: Path) -> None:
    from PIL import Image

    out.mkdir(parents=True, exist_ok=True)
    for scheme in SCHEMES:
        page = open_probe(browser, scheme)
        try:
            rp.check(f"{scheme}: the probe's page drew the showcase", (page.state or {}).get("state") == "drawn", page.state)
            # The page's own background round each picture of the sheet (the pane is a lightbox in both schemes).
            around = tuple(page.evaluate("() => getComputedStyle(document.body).backgroundColor.match(/[0-9.]+/g).slice(0, 3).map(Number)"))
            rows = []
            for mode in MODES:
                rows.append([])
                for name in VIEWS:
                    image = shoot(page, mode, name)
                    image.save(out / f"{mode}.{name}.{scheme}.png")
                    rows[-1].append(image)
            height, gap = 900, 12
            rows = [[tile.resize((round(tile.width * height / tile.height), height), Image.LANCZOS) for tile in row] for row in rows]
            sheet = Image.new("RGB", (max(sum(tile.width + gap for tile in row) for row in rows) + gap, len(rows) * (height + gap) + gap), around)
            for index, row in enumerate(rows):
                x = gap
                for tile in row:
                    sheet.paste(tile, (x, gap + index * (height + gap)))
                    x += tile.width + gap
            sheet.save(out / f"sheet.{scheme}.png")
            rp.check(f"{scheme}: {len(MODES) * len(VIEWS)} pictures and their sheet written, no console error", not page.errors,
                     page.errors[:3] or str(out / f"sheet.{scheme}.png"))
        finally:
            page.context.close()


# -- part_page: the showcase's card and page on the Library itself ---------------------------------------------------------

LIBRARY = ROOT / "web" / "library"
VIEW_STATE = "() => { const text = document.getElementById('libViewState')?.textContent; return text ? JSON.parse(text) : null; }"
GRID = """() => {
  const shelves = document.getElementById('libShelves'); const first = shelves.firstElementChild; const card = document.getElementById('showcase');
  if (!first || !card) return null;
  const box = element => { const r = element.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };
  const image = card.querySelector('img'); const shot = card.querySelector('.lib-shot'); const text = card.querySelector('.lib-card-text');
  const pic = card.querySelector('a.lib-showcase-pic'); const details = card.querySelector('a.lib-showcase-details'); const design = card.querySelector('a.lib-design');
  return {first: first.className, inFirst: first.contains(card), cards: first.querySelectorAll('.lib-card').length, tag: card.tagName,
    hrefs: [...card.querySelectorAll('a')].map(a => a.getAttribute('href')), href: card.getAttribute('href'),
    pic: pic ? [pic.getAttribute('tabindex'), pic.getAttribute('aria-hidden'), pic.contains(shot)] : null,
    details: details ? [details.textContent, getComputedStyle(details).backgroundColor, box(details)] : null,
    design: design ? {text: design.textContent, href: design.getAttribute('href'), target: design.target, named: design.getAttribute('aria-label'), box: box(design),
      fill: getComputedStyle(design).backgroundColor, color: getComputedStyle(design).color, round: getComputedStyle(design).borderRadius,
      type: [getComputedStyle(design).fontSize, getComputedStyle(design).fontWeight], detailsType: [getComputedStyle(details).fontSize, getComputedStyle(details).fontWeight],
      detailsRound: getComputedStyle(details).borderRadius, next: details.nextElementSibling === design, last: !design.nextElementSibling} : null,
    label: card.querySelector('.lib-badge')?.textContent, title: card.querySelector('.lib-showcase-title')?.textContent,
    line: card.querySelector('.lib-showcase-line')?.textContent, named: details?.getAttribute('aria-label'),
    images: card.querySelectorAll('img').length, src: image?.getAttribute('src'), natural: image ? [image.naturalWidth, image.naturalHeight] : null,
    complete: Boolean(image?.complete), alt: image?.alt, loading: image?.getAttribute('loading'),
    card: box(card), shot: box(shot), text: box(text), row: box(shelves), next: first.nextElementSibling?.id,
    below: first.nextElementSibling ? Math.round(first.nextElementSibling.querySelector('h3').getBoundingClientRect().top - card.getBoundingClientRect().bottom) : null,
    ground: getComputedStyle(shot).backgroundColor,
    canvases: document.querySelectorAll('canvas').length, wide: document.scrollingElement.scrollWidth, window: innerWidth,
    scripts: performance.getEntriesByType('resource').map(entry => entry.name).filter(name => /three|library_view|onpart/.test(name))};
}"""
PAGE = """() => {
  const detail = document.getElementById('libDetail'); const stage = detail.querySelector('.lib-stage'); const live = detail.querySelector('.lib-live');
  const box = element => { if (!element) return null; const r = element.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };
  const pill = detail.querySelector('.lib-pills a');
  const dialog = document.getElementById('libWindow');
  return {windowed: dialog.open, covered: dialog.open && !document.getElementById('libGrid').hidden, hash: location.hash, title: document.title,
    focused: document.activeElement?.id || document.activeElement?.className, heading: detail.querySelector('#libDetailTitle')?.textContent,
    label: detail.querySelector('.lib-badge')?.textContent, line: detail.querySelector('.lib-detail-line')?.textContent,
    detail: detail.querySelector('.lib-showcase-detail')?.textContent,
    live: Boolean(stage?.classList.contains('is-live')),
    stage: box(stage), canvas: box(live?.querySelector('canvas')), frame: box(detail.querySelector('.lib-frame')), info: box(detail.querySelector('.lib-info')),
    ground: stage ? getComputedStyle(stage.querySelector('.lib-shot')).backgroundColor : null,
    views: [...detail.querySelectorAll('input[name=libView]')].map(input => [input.value, input.checked]),
    pill: pill ? [pill.getAttribute('href'), pill.target, pill.rel, pill.textContent, getComputedStyle(pill).backgroundColor] : null,
    notices: [...detail.querySelectorAll('.lib-provenance a')].map(a => a.getAttribute('href')), sources: detail.querySelector('.lib-provenance')?.textContent,
    open: detail.querySelectorAll('.lib-open').length, downloads: detail.querySelectorAll('[data-export], a[download], .lib-downloads').length,
    pitch: detail.querySelectorAll('.lib-seg, .lib-facts').length, wide: document.scrollingElement.scrollWidth, window: innerWidth,
    page: getComputedStyle(document.body).backgroundColor};
}"""
# The page's canvas at its home, read in the frame it is drawn in (0 is Reset view; as library_shots.py reads it).
PAGE_CANVAS = """() => { const host = document.querySelector('.lib-live'); const canvas = host.querySelector('canvas');
  host.dispatchEvent(new KeyboardEvent('keydown', {key: '0', bubbles: true, cancelable: true}));
  return new Promise(resolve => requestAnimationFrame(() => resolve(canvas.toDataURL('image/png')))); }"""


def library_page(browser, url: str, width: int, height: int, scheme: str = "light", scale: int = 1):
    """A page of the Library (?probe=1, the first page; library.html?probe=1 until 2026-11-16) at ``url``, its console errors and warnings kept in page.errors."""

    context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale, color_scheme="light")
    if scheme == "dark":
        context.add_init_script(rp.DARK_CHOICE)
    page = context.new_page()
    page.errors = []
    # (Chromium's own note of a slow read of the canvas, which the view's centring does on purpose, is no error.)
    page.on("console", lambda message: page.errors.append(f"{message.type}: {message.text}")
            if message.type in ("error", "warning") and "GPU stall due to ReadPixels" not in message.text else None)
    page.on("pageerror", lambda error: page.errors.append(str(error)))
    page.goto(f"{url}?probe=1", wait_until="networkidle")
    return page


def view_state(page, wanted, timeout: float = 150):
    """#libViewState once ``wanted`` (state -> bool) holds, or the last state read."""

    end = time.monotonic() + timeout
    state = None
    while time.monotonic() < end:
        state = page.evaluate(VIEW_STATE)
        if state and (wanted(state) or state.get("state") in ("failed", "unavailable")):
            break
        page.wait_for_timeout(100)
    return state


def near(a, b, tol: float = 1.0) -> bool:
    return abs(a - b) <= tol


def part_page(browser, url: str, out: Path) -> None:
    from PIL import Image

    document = json.loads((LIBRARY / "showcase.json").read_text(encoding="utf-8"))
    scene = json.loads((LIBRARY / document["placed"]["scene"]).read_text(encoding="utf-8"))
    identifier = document["id"]
    out.mkdir(parents=True, exist_ok=True)
    drawn = lambda mode: (lambda state: state.get("state") == "drawn" and state.get("drawn_mode") == mode)  # noqa: E731

    # -- 1440 px, light: the grid's first card, the keyboard's way to the page, the page ---------------------------------
    page = library_page(browser, url, 1440, 900)
    try:
        grid = page.evaluate(GRID)
        page.screenshot(path=str(out / "grid.1440.light.png"))
        rp.check("1440: the grid's first section is the showcase's one card, before the grippers",
                 bool(grid) and "lib-showcased" in grid["first"] and grid["inFirst"] and grid["cards"] == 1 and grid["next"] == "grippers",
                 grid and (grid["first"], grid["cards"], grid["next"]))
        # The user's request of 2026-11-15: the card no link; its picture and its Details open the page, the picture's
        # link out of the Tab order and hidden from assistive technology; Details a grey pill, not the action blue.
        rp.check("1440: the card is no link; its picture and its Details open the page, the picture out of the Tab order",
                 grid["tag"] == "DIV" and grid["href"] is None and grid["hrefs"] == [f"#{identifier}", f"#{identifier}", "gen.html"]
                 and grid["pic"] == ["-1", "true", True] and grid["details"][0] == "Details"
                 and grid["details"][1] not in ("rgb(0, 113, 227)", "rgb(41, 151, 255)"), (grid["tag"], grid["hrefs"], grid["pic"], grid["details"]))
        rp.check("1440: its words are showcase.json's: the label, the title, one line, and Details named after the title",
                 (grid["label"], grid["title"], " ".join(grid["line"].split())) == (document["label"], document["title"], document["text"])
                 and grid["named"] == f"Details: {document['title']}", (grid["label"], grid["title"], grid["line"], grid["named"]))
        card = document["image"]["card"]
        rp.check("1440: its picture is one image, the card file at its size, loaded at once; no canvas and no three.js on the grid",
                 grid["images"] == 1 and grid["src"] == f"static/library/{card['src']}" and grid["natural"] == [card["width"], card["height"]]
                 and grid["complete"] and grid["loading"] is None and grid["alt"] == document["image"]["alt"] and grid["canvases"] == 0
                 and grid["scripts"] == [], (grid["images"], grid["src"], grid["natural"], grid["loading"], grid["canvases"], grid["scripts"]))
        rp.check("1440: the card is as wide as the row, its picture a 4:5 light box on the left, its words just beside it, a fifth of the row, nothing past the window",
                 near(grid["card"][2], grid["row"][2]) and near(grid["shot"][2] * 5, grid["shot"][3] * 4, 4)
                 and grid["shot"][0] < grid["text"][0] and 0 <= grid["text"][0] - (grid["shot"][0] + grid["shot"][2]) <= 1
                 and 220 <= grid["shot"][2] <= 300 and grid["ground"] == "rgb(245, 245, 247)" and grid["wide"] <= grid["window"],
                 (grid["card"], grid["shot"], grid["text"], grid["ground"]))
        rp.check("1440: the grippers' heading 56 px below the card, as the UMI shelf's is below the grippers' last row, and in a 900 px window's first screen",
                 grid["below"] == 56 and grid["card"][1] + grid["card"][3] + 56 < 900, (grid["below"], grid["card"][1] + grid["card"][3]))
        # The keyboard: Tab from the page's top to the card's Details, its one stop (the header's links come first; the
        # picture's link is no stop), Enter opens its page.
        presses = 0
        stops = []
        while presses < 30 and not page.evaluate("() => document.activeElement?.matches('.lib-showcase-details')"):
            page.keyboard.press("Tab")
            presses += 1
            stops.append(page.evaluate("() => document.activeElement?.className"))
        ring = page.evaluate("() => { const s = getComputedStyle(document.activeElement); return [document.activeElement.className, s.outlineStyle, s.outlineWidth, document.activeElement.matches(':focus-visible')]; }")
        rp.check("1440: Tab reaches the card's Details, the page's first card's first stop, with the page's focus ring, never its picture",
                 ring == ["lib-pill lib-showcase-details", "solid", "2px", True] and "lib-showcase-pic" not in stops, (presses, ring))
        # Design your own (2026-11-16): the next stop after Details, its ring the page's; Shift+Tab back to Details.
        page.keyboard.press("Tab")
        after = page.evaluate("() => { const s = getComputedStyle(document.activeElement); return [document.activeElement.className, s.outlineStyle, s.outlineWidth, s.outlineColor, s.outlineOffset, document.activeElement.matches(':focus-visible')]; }")
        page.keyboard.press("Shift+Tab")
        rp.check("1440: the card's Tab order: the picture out of it, Details, then Design your own with the page's focus ring (2 px, the focus blue, 2 px out)",
                 after == ["lib-pill lib-design", "solid", "2px", "rgb(0, 113, 227)", "2px", True]
                 and page.evaluate("() => document.activeElement?.className") == "lib-pill lib-showcase-details", after)
        design_ok(grid, "1440 light", document)
        page.keyboard.press("Enter")
        state = view_state(page, drawn("assembled"))
        info = page.evaluate(PAGE)
        rp.check("1440: Enter opens the showcase's own page in the window over the grid, its title focused, the tab named after it",
                 (info["hash"], info["windowed"], info["covered"], info["focused"], info["heading"]) == (f"#{identifier}", True, True, "libDetailTitle", document["title"])
                 and info["title"].startswith(f"{document['title']} · "), (info["hash"], info["windowed"], info["covered"], info["focused"], info["heading"], info["title"]))
        rp.check("1440: the 3D view is drawn from the placed record: no build, the scene's gripper, Assembled at its home",
                 bool(state) and (state.get("state"), state.get("id"), state.get("build_id"), state.get("gripper"), state.get("mode"), state.get("drawn_mode"), state.get("moved"))
                 == ("drawn", identifier, None, True, "assembled", "assembled", False) and info["live"],
                 state and {key: state.get(key) for key in ("state", "note", "id", "build_id", "gripper", "mode", "drawn_mode", "moved")})
        stage = (state or {}).get("stage") or {}
        looks = stage.get("looks") or {}
        rp.check("1440: the stage draws the scene's looks and its own camera, no finger see-through",
                 looks.get("bodies") == sorted({body["look"] for body in scene["bodies"]}) and looks.get("part") == scene["part_look"]
                 and stage.get("camera") == scene["camera"] and stage.get("see_through") == [], (looks, stage.get("camera"), stage.get("see_through")))
        rp.check("1440: the view's box is 4:5 beside the page's words and within the window, its canvas filling it, the Assembled view chosen",
                 near(info["stage"][2] * 5, info["stage"][3] * 4, 4) and near(info["canvas"][2], info["stage"][2]) and near(info["canvas"][3], info["stage"][3])
                 and info["info"][0] > info["frame"][0] + info["frame"][2] and info["views"] == [["exploded", False], ["assembled", True]]
                 and info["stage"][1] + info["stage"][3] <= 900, (info["stage"], info["canvas"], info["views"]))
        image = Image.open(io.BytesIO(base64.b64decode(page.evaluate(PAGE_CANVAS).split(",", 1)[1]))).convert("RGBA")
        # By hue (the merge of 2026-11-13: the fingers in the UMI rows' orange, whose mid-tones are darker than the base
        # orange's): the fingers' orange 8 to 26 degrees, the boards' amber 26 to 45, both saturated and lit.
        orange = share(image, lambda r, g, b: hue_band(r, g, b, 8, 26, 0.4))
        amber = share(image, lambda r, g, b: hue_band(r, g, b, 26, 45, 0.35))
        white = share(image, lambda r, g, b: min(r, g, b) > 190 and max(r, g, b) - min(r, g, b) < 12)
        black = share(image, lambda r, g, b: max(r, g, b) < 70)
        rp.check("1440: the canvas shows the orange fingers, the amber boards, the white shell and holders and the black links",
                 orange > 0.08 and amber > 0.03 and white > 0.25 and black > 0.03, f"orange {orange:.3f}, amber {amber:.3f}, white {white:.3f}, black {black:.3f}")
        page.screenshot(path=str(out / "page.assembled.1440.light.png"))
        rp.check("1440: the page's words: the label, one line, the line of detail, the tutorial for the Gerbers (a grey pill, a new tab), the two notices",
                 (info["label"], " ".join(info["line"].split()), " ".join((info["detail"] or "").split())) == (document["label"], document["text"], document["detail"])
                 and info["pill"][:4] == [document["tutorial"]["href"], "_blank", "noopener noreferrer", document["tutorial"]["label"]]
                 and info["notices"] == [f"static/library/{item['notice']}" for item in document["sources"]]
                 and all(item["text"] in info["sources"] for item in document["sources"]), (info["label"], info["pill"], info["notices"]))
        answered = page.evaluate("async (paths) => Promise.all(paths.map(async path => { const answer = await fetch(path); return [answer.status, (await answer.text()).length > 200]; }))", info["notices"])
        rp.check("1440: both notices are files the site serves", answered == [[200, True], [200, True]], answered)
        rp.check("1440: no Open in Gen by Surface, no download, no pitch or facts; the pill is not the action blue",
                 (info["open"], info["downloads"], info["pitch"]) == (0, 0, 0) and info["pill"][4] not in ("rgb(0, 113, 227)", "rgb(41, 151, 255)"),
                 (info["open"], info["downloads"], info["pitch"], info["pill"][4]))
        # The keyboard on the page.  Its Tab order is the window's order: its X (since 2026-11-15; the page's back link
        # before), the view, the Exploded | Assembled control, then the words' links; the title, focused as the page opens, comes after the control, so Shift+Tab
        # from it reaches the control (the arrow keys choose) and then the view (the arrow keys turn it, 0 brings it back).
        presses = 0
        while presses < 6 and page.evaluate("() => document.activeElement?.name") != "libView":
            page.keyboard.press("Shift+Tab")
            presses += 1
        page.keyboard.press("ArrowLeft")
        state = view_state(page, drawn("exploded"))
        rp.check("1440: the arrow keys on the control switch the view to Exploded, drawn at its home",
                 bool(state) and (state.get("mode"), state.get("drawn_mode"), state.get("moved")) == ("exploded", "exploded", False)
                 and page.evaluate("() => document.activeElement?.value") == "exploded", state and (state.get("mode"), state.get("drawn_mode"), presses))
        page.wait_for_timeout(400)
        page.screenshot(path=str(out / "page.exploded.1440.light.png"))
        page.keyboard.press("Shift+Tab")
        focused = page.evaluate("() => [document.activeElement?.className, document.activeElement?.getAttribute('aria-label'), document.activeElement?.getAttribute('role')]")
        for _ in range(4):
            page.keyboard.press("ArrowRight")
        turned = view_state(page, lambda state: state.get("moved") is True, 20)
        page.keyboard.press("0")
        back = view_state(page, lambda state: state.get("moved") is False, 20)
        # (Each by its first class: the view's host is "lib-live is-used" once the arrow keys have turned it, its drag hint
        # hidden since 2026-11-15.)
        order = page.evaluate("""() => [...document.querySelectorAll('#libWindow button, #libWindow a, #libWindow input, #libWindow [tabindex="0"]')]
          .map(node => node.classList[0] || node.name || node.textContent)""")
        rp.check("1440: the window's Tab order: its X, the view, the control's two views, the tutorial, the two notices",
                 order == ["lib-close", "lib-live", "libView", "libView", "lib-pill", "notice", "notice"], order)
        rp.check("1440: the keyboard reaches the view (a group named by the picture's alt); the arrow keys turn it and 0 brings it back",
                 focused == ["lib-live", document["image"]["alt"], "group"] and bool(turned) and turned.get("moved") is True and bool(back) and back.get("moved") is False,
                 (focused, turned and turned.get("moved"), back and back.get("moved")))
        # The window's X (the page's back link until 2026-11-15): the grid where it was, the card's Details focused.
        page.click("#libClose")
        page.wait_for_timeout(300)
        after = page.evaluate("() => [location.hash, document.getElementById('libWindow').open, document.activeElement?.className, document.title]")
        off = page.evaluate(VIEW_STATE)
        rp.check("1440: the window's X comes back to the grid, the showcase's Details focused, the view taken down",
                 after[:3] == ["#showcase", False, "lib-pill lib-showcase-details"] and after[3].startswith("Library") and (off or {}).get("state") == "off",
                 (after, (off or {}).get("state")))
        # The picture opens the page too (by the mouse), and Back comes back to Details.
        page.click(".lib-showcase-pic")
        state = view_state(page, drawn("assembled"))
        opened = page.evaluate("() => [location.hash, document.getElementById('libWindow').open]")
        page.go_back()
        page.wait_for_timeout(300)
        again = page.evaluate("() => [location.hash, document.getElementById('libWindow').open, document.activeElement?.className]")
        rp.check("1440: a click on the picture opens the page in the window; Back closes it, the card's Details focused",
                 opened == [f"#{identifier}", True] and bool(state) and state.get("state") == "drawn" and again[1] is False
                 and again[2] == "lib-pill lib-showcase-details", (opened, state and state.get("state"), again))
        rp.check("1440: no console error or warning", not page.errors, page.errors[:3])
    finally:
        page.context.close()

    # -- Design your own (2026-11-16): pressed, Gen by Surface in this tab; the card at 1440 px dark too ---------------
    design_page(browser, url, out)

    # -- 390 px, light and dark: the card stacked, the page's view in its light box ----------------------------------------
    for scheme in SCHEMES:
        page = library_page(browser, url, 390, 844, scheme, scale=2)
        try:
            grid = page.evaluate(GRID)
            page.screenshot(path=str(out / f"grid.390.{scheme}.png"))
            rp.check(f"390 {scheme}: the card within the window, its picture above its words, a 4:5 light box, centred, 60 % of the card, nothing scrolling sideways",
                     bool(grid) and grid["card"][0] >= 0 and grid["card"][0] + grid["card"][2] <= 390 and near(grid["card"][2], grid["row"][2])
                     and grid["shot"][1] + grid["shot"][3] <= grid["text"][1] + 1 and near(grid["shot"][2] * 5, grid["shot"][3] * 4, 4)
                     and near(grid["shot"][0] + grid["shot"][2] / 2, grid["card"][0] + grid["card"][2] / 2, 1) and near(grid["shot"][2], 0.6 * (grid["card"][2] - 12), 2)
                     and grid["ground"] == "rgb(245, 245, 247)" and grid["wide"] <= 390 and grid["complete"],
                     grid and (grid["card"], grid["shot"], grid["text"], grid["ground"], grid["wide"]))
            rp.check(f"390 {scheme}: Details its own size under the words, not the column's width",
                     bool(grid["details"]) and grid["details"][2][2] < 0.5 * grid["card"][2] and grid["details"][2][1] >= grid["text"][1],
                     grid["details"] and grid["details"][2])
            design_ok(grid, f"390 {scheme}", document, scheme)
            page.locator("#showcase").screenshot(path=str(out / f"card.390.{scheme}.png"))
            page.click(".lib-showcase-pic")
            state = view_state(page, drawn("assembled"))
            info = page.evaluate(PAGE)
            page.wait_for_timeout(300)
            page.screenshot(path=str(out / f"page.assembled.390.{scheme}.png"))
            rp.check(f"390 {scheme}: the showcase's page in one column (the window a sheet), its view drawn in a 4:5 light box above its words, nothing scrolling sideways",
                     bool(state) and state.get("state") == "drawn" and state.get("drawn_mode") == "assembled" and info["live"]
                     and near(info["stage"][2] * 5, info["stage"][3] * 4, 4) and info["stage"][0] >= 0 and info["stage"][0] + info["stage"][2] <= 390
                     and info["info"][1] >= info["frame"][1] + info["frame"][3] and info["ground"] == "rgb(245, 245, 247)" and info["wide"] <= 390,
                     (state and (state.get("state"), state.get("note")), info["stage"], info["info"], info["ground"], info["wide"]))
            dark = sum(int(value) for value in re.findall(r"\d+", info["page"])[:3]) < 120
            rp.check(f"390 {scheme}: the page is {scheme}", dark == (scheme == "dark"), info["page"])
            page.evaluate("() => document.querySelector('input[name=libView][value=exploded]').click()")
            state = view_state(page, drawn("exploded"))
            rp.check(f"390 {scheme}: Exploded is drawn there too", bool(state) and state.get("drawn_mode") == "exploded", state and (state.get("state"), state.get("drawn_mode")))
            rp.check(f"390 {scheme}: no console error or warning", not page.errors, page.errors[:3])
        finally:
            page.context.close()


# Design your own (the user's decisions of 2026-11-15 and 2026-11-16: "在flexitac on xarm的details 后面，多一个按钮，generate
# sensor by yourself with cad file", named "Design your own"): the page's action blue in each scheme, white words.
ACTION_BLUE = {"light": "rgb(0, 113, 227)", "dark": "rgb(0, 113, 227)"}


def design_ok(grid, where, document, scheme="light"):
    """Design your own on the card as GRID reads it: right after Details, the card's last; its words, name and link (gen.html,
    this tab); the action blue with white words; Details' height, roundness and type; beside Details on its line within the
    card, or (where the two do not fit) under it on its left, its own width."""
    design, details, card = grid["design"], grid["details"], grid["card"]
    rp.check(f"{where}: Design your own right after Details, the card's last: Gen by Surface (gen.html) in this tab, named for where it goes",
             bool(design) and design["next"] and design["last"] and (design["text"], design["href"], design["target"], design["named"])
             == ("Design your own", "gen.html", "", "Design your own sensor in Gen by Surface"), design)
    if not design:
        return
    box, other = design["box"], details[2]
    beside = abs(box[1] - other[1]) < 0.5 and 9.5 <= box[0] - (other[0] + other[2]) <= 10.5
    under = abs(box[0] - other[0]) < 0.5 and 9.5 <= box[1] - (other[1] + other[3]) <= 10.5
    rp.check(f"{where}: Design your own the action blue ({design['fill']}) with white words, as tall, as round and in the same type as Details, "
             f"{'beside it' if beside else 'under it'} within the card",
             design["fill"] == ACTION_BLUE[scheme] and design["color"] == "rgb(255, 255, 255)" and abs(box[3] - other[3]) < 0.5
             and design["round"] == design["detailsRound"] and design["type"] == design["detailsType"] and (beside or under)
             and box[0] + box[2] <= card[0] + card[2] - 12 + 0.5 and box[2] < card[2] * 0.8, (design, other, card))


def design_page(browser, url, out):
    """Design your own pressed: Gen by Surface (gen.html) in this tab, no other page, the generator's default part on its
    way; Back the Library.  The card at 1440 px in the dark scheme; at 360 and 320 px the two pills within the card."""
    page = library_page(browser, url, 1440, 900)
    try:
        page.locator("#showcase").screenshot(path=str(out / "card.1440.light.png"))
        pages = []
        page.context.on("page", lambda opened: pages.append(opened))
        with page.expect_navigation():
            page.click(".lib-design")
        page.wait_for_load_state("domcontentloaded")
        rp.wait_until(page, "() => Boolean(document.body && document.body.dataset.mode)", 60)
        there = [page.url, page.title(), page.evaluate("() => document.body.dataset.mode")]
        page.go_back()
        rp.wait_until(page, "() => document.querySelectorAll('.lib-card').length > 0", 30)
        rp.check("1440: Design your own opens Gen by Surface (gen.html) in this tab, no other page; Back comes back to the Library",
                 there == [f"{url}gen.html", "FlexiTac-Gen", "cad"] and not pages and page.url.split("?")[0] == url and page.title() == "Library · FlexiTac-Gen",
                 (there, len(pages), page.url))
    finally:
        page.context.close()
    document = json.loads((LIBRARY / "showcase.json").read_text(encoding="utf-8"))
    page = library_page(browser, url, 1440, 900, "dark")
    try:
        grid = page.evaluate(GRID)
        design_ok(grid, "1440 dark", document, "dark")
        page.locator("#showcase").screenshot(path=str(out / "card.1440.dark.png"))
    finally:
        page.context.close()
    for width in (360, 320):
        page = library_page(browser, url, width, 740)
        try:
            grid = page.evaluate(GRID)
            design_ok(grid, f"{width} light", document)
            page.locator("#showcase").screenshot(path=str(out / f"card.{width}.light.png"))
            rp.check(f"{width}: nothing scrolls sideways", grid["wide"] <= width, grid["wide"])
        finally:
            page.context.close()


PARTS = ("part_wrap", "part_tails", "part_view", "part_shots", "part_page")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("parts", nargs="*", help=f"only these parts ({', '.join(PARTS)})")
    parser.add_argument("--out", type=Path, default=Path(rp.SHOTS) / "showcase", help="part_shots' and part_page's folder")
    parser.add_argument("--url", default=None, help="part_page on another site than app.py's (a built static site, served from its "
                        "folder): its address, with the slash at its end")
    args = parser.parse_args(argv)
    unknown = [part for part in args.parts if part not in PARTS]
    if unknown:
        parser.error(f"no part is named {', '.join(unknown)}")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=WEBGL_ARGS)
        try:
            for part in args.parts or PARTS:
                if part == "part_shots":
                    part_shots(browser, args.out.resolve())
                elif part == "part_page":
                    part_page(browser, args.url or rp.URL, args.out.resolve())
                else:
                    globals()[part](browser)
        finally:
            browser.close()
    return 0 if rp.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
