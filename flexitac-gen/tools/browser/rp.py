"""Shared Playwright helpers of the browser checks (see README.md; not part of the unittest suite).

FPC_PORT is the port of a running ``python3 app.py --port <port>`` (default 8008);
screenshots and downloads go to FPC_BROWSER_OUT (default: <temp>/fpc-browser-checks).
"""
from __future__ import annotations

import contextlib
import json
import math
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

PORT = int(os.environ.get("FPC_PORT", "8008"))
URL = f"http://127.0.0.1:{PORT}/"
# The app opens in CAD mode (the user's default of 2026-10-30); the Rectangular mode's checks open it at #rect.
RECT_URL = URL + "#rect"
SCRATCH = os.environ.get("FPC_BROWSER_OUT", str(Path(tempfile.gettempdir()) / "fpc-browser-checks"))
SHOTS = f"{SCRATCH}/shots"
Path(SHOTS).mkdir(parents=True, exist_ok=True)
Path(SCRATCH, "downloads").mkdir(parents=True, exist_ok=True)
DONE = ("() => ['is-ok','is-error','is-warning'].some(c => document.querySelector('#status').classList.contains(c))"
        " && !document.querySelector('#generate').disabled")

RESULTS = {"pass": 0, "fail": 0, "failures": []}

# The interface folds what goes beyond the basic flow (web/index.html: the form's More options, CAD mode's File details,
# Selection settings, More options and Proposal details, step 7's Check details, the design checks, the stacked view's
# notes and the ordering notes), hides the rectangular form in CAD mode and CAD mode's results until it has generated a
# build.  The checks reach every control with every fold open, the form shown and the results in sight (an init script
# of their pages, unfold()); part_clean_interface (ui_checks.py) and part_clean_cad (cad_checks.py) check the folded
# default on pages without it.
OPEN_FOLDS = """(() => {
  const open = node => { if (node.tagName === 'DETAILS') node.open = true; node.querySelectorAll?.('details').forEach(item => { item.open = true; }); };
  new MutationObserver(records => records.forEach(record => record.addedNodes.forEach(node => { if (node.nodeType === 1) open(node); })))
    .observe(document, {childList: true, subtree: true});
  document.addEventListener('DOMContentLoaded', () => {
    open(document.documentElement);
    const style = document.createElement('style');
    // Gen by Surface: the form shown beside the workbench, the guide above both (part_default_cad checks it in place).
    style.textContent = 'body[data-mode="cad"] main { grid-template-columns:minmax(270px,340px) minmax(0,1fr) !important; }'
      + ' body[data-mode="cad"] .flow-guide { grid-column:1 / -1; position:static !important; height:auto !important; border-right:0 !important; }'
      + ' body[data-mode="cad"] .controls { display:block !important; } body.cad-no-build #results { display:block !important; }';
    document.head.append(style);
  });
})();"""


def unfold(target):
    """Every fold open, the form shown in CAD mode and its results in sight (OPEN_FOLDS) on a page or context."""
    target.add_init_script(OPEN_FOLDS)


# The page's look (the user's request of 2026-11-06): light for every visitor whatever the system's scheme, dark once the
# header's toggle (#themeToggle, web/theme.js) is turned on, the choice kept in localStorage under THEME_KEY for both
# pages.  The checks turn the toggle (set_look) or store its choice (DARK_CHOICE, an init script: the page opens dark as
# after a visit that turned it on), never the system's scheme.
THEME_KEY = "fpc-customizer.theme"
DARK_CHOICE = f"try {{ window.localStorage.setItem('{THEME_KEY}', 'dark'); }} catch (error) {{ /* no storage: light */ }}"
SET_LOOK = """(look) => { if (document.documentElement.dataset.theme !== look) document.getElementById('themeToggle').click();
    return document.documentElement.dataset.theme; }"""


def set_look(page, look):
    """The header's toggle clicked (its own click, the page not scrolled) until the page's look is ``look``."""
    theme = page.evaluate(SET_LOOK, look)
    if theme != look:
        raise RuntimeError(f"the header's toggle left the page {theme}, not {look}")
    page.wait_for_timeout(100)
    return theme


def check(name, condition, detail=""):
    """Record one check; print PASS/FAIL with an optional detail."""
    ok = bool(condition)
    RESULTS["pass" if ok else "fail"] += 1
    if not ok:
        RESULTS["failures"].append(name)
    text = f"{'PASS' if ok else 'FAIL'} {name}"
    if detail != "":
        text += f" :: {detail}"
    print(text, flush=True)
    return ok


def summary():
    print(f"\n{RESULTS['pass']} passed, {RESULTS['fail']} failed", flush=True)
    for name in RESULTS["failures"]:
        print("  failed:", name)
    return RESULTS["fail"] == 0


@contextlib.contextmanager
def browser_page(width=1600, height=1000, scale=1):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale, accept_downloads=True)
        unfold(context)
        page = context.new_page()
        page.logs = []
        page.on("console", lambda m: page.logs.append((m.type, m.text)))
        page.on("pageerror", lambda e: page.logs.append(("pageerror", str(e))))
        try:
            yield page
        finally:
            browser.close()


def wait_until(page, expression, timeout=40.0, arg=None):
    """Poll with page.evaluate (CDP), ``arg`` its argument if given; in-page polling would need eval, which the CSP forbids."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if page.evaluate(expression) if arg is None else page.evaluate(expression, arg):
            return
        page.wait_for_timeout(40)
    raise TimeoutError(expression)


def open_app(page):
    page.goto(RECT_URL)
    wait_until(page, DONE)
    page.wait_for_timeout(150)


def set_fields(page, **fields):
    for control_id, value in fields.items():
        tag = page.eval_on_selector(f"#{control_id}", "e => e.tagName")
        if tag == "SELECT":
            page.select_option(f"#{control_id}", str(value))
        else:
            page.fill(f"#{control_id}", "" if value is None else str(value))


def generate(page, **fields):
    """Set form controls by id, submit, and wait for the build to settle."""
    set_fields(page, **fields)
    page.click("#generate")
    page.wait_for_timeout(60)
    wait_until(page, "() => (" + DONE[6:] + ") && !document.querySelector('#status').textContent.startsWith('Deriving')")
    page.wait_for_timeout(120)


def api(path, body=None):
    """Call the server directly (JSON in, JSON out)."""
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(URL.rstrip("/") + path, data=data, method="GET" if body is None else "POST",
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read() or b"null"), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"null"), dict(error.headers)


def capture_generate(page):
    """Return a list that collects (request body, response JSON) of /api/generate calls."""
    seen = []

    def on_response(response):
        if "/api/generate" in response.url and response.request.method == "POST":
            try:
                seen.append((json.loads(response.request.post_data or "null"), response.json()))
            except Exception as error:  # noqa: BLE001 - scratch diagnostics
                seen.append((None, {"error": str(error)}))
    page.on("response", on_response)
    return seen


STACKED_PIN1 = """() => [...document.querySelectorAll('#stackedPreview .pin1-ring')].map(ring => {
    const box = ring.getBoundingClientRect(); const board = ring.closest('.assembly-board');
    const marker = ring.ownerSVGElement.querySelector('.pin1-marker')?.getBoundingClientRect();
    const frame = document.getElementById('stackedPreview').getBoundingClientRect();
    return {layer: ring.classList.contains('is-upper') ? 'upper' : ring.classList.contains('is-lower') ? 'lower' : '', side: board?.dataset.physicalSide,
            x: box.left + box.width / 2, y: box.top + box.height / 2, d: box.width, h: box.height, stroke: getComputedStyle(ring).stroke,
            step: ring.dataset.step ?? null, triangle: marker ? [marker.left, marker.top, marker.right, marker.bottom] : null,
            frame: [frame.left, frame.top, frame.right, frame.bottom]}; })"""


def stacked_pin1(page, margin=0.0):
    """The stacked view's pin-1 rings as drawn in its current view (``(problems, rings)``; P5-diagonal-bus.md section
    27.3: the tails end together, so the two boards' pin-1 contacts may lie side by side): one ring per board, the top
    FPC's (``is-upper``) and the bottom FPC's (``is-lower``) in different colours, each at least 17 px across, apart by
    more than their radii and strokes (no overlap), neither taking in any of the other board's pin-1 triangle (its box),
    each round its own triangle (its centre within one ring radius of the triangle's: section 27.5, the plan view's
    rings stepped a ring diameter off their triangles had left them marking nothing) and nearer its own triangle's
    centre than the other's, so each marks its own pin-1 pad only, and both within the view (it clips; the view has no
    caption since 2026-11-06).  The exploded view tilts the boards about the screen's x axis, so its rings are ellipses
    along the screen's axes, alike: distances are measured with y scaled by their aspect.  ``margin`` (px): the gap the
    rings keep beyond their strokes and a ring beyond the other triangle (app.js steps them at 2, half its
    PIN1_RING_GAP_PX: apart by the gap, each by half of it clear of the other triangle)."""
    rings = page.evaluate(STACKED_PIN1)
    problems = []
    if sorted((ring["layer"], ring["side"]) for ring in rings) != [("lower", "bottom"), ("upper", "top")]:
        problems.append(("rings", [(ring["layer"], ring["side"]) for ring in rings]))
        return problems, rings
    upper, lower = sorted(rings, key=lambda ring: ring["layer"] != "upper")
    if upper["stroke"] == lower["stroke"]:
        problems.append(("same colour", upper["stroke"]))
    if min(upper["d"], lower["d"]) < 17:
        problems.append(("small", upper["d"], lower["d"]))
    aspect = upper["d"] / upper["h"] if upper["h"] > 0 else 1.0
    gap = ((upper["x"] - lower["x"]) ** 2 + ((upper["y"] - lower["y"]) * aspect) ** 2) ** 0.5 - (upper["d"] + lower["d"]) / 2 - 2
    if gap < margin:
        problems.append(("overlap", round(gap, 2)))
    for ring, other in ((upper, lower), (lower, upper)):
        if other["triangle"]:
            left, top, right, bottom = other["triangle"]
            near = (min(max(ring["x"], left), right) - ring["x"], (min(max(ring["y"], top), bottom) - ring["y"]) * aspect)
            if (near[0] ** 2 + near[1] ** 2) ** 0.5 < ring["d"] / 2 + margin:
                problems.append(("takes in the other triangle", ring["layer"]))
    for ring in (upper, lower):
        if ring["triangle"]:
            left, top, right, bottom = ring["triangle"]
            if ((left + right) / 2 - ring["x"]) ** 2 + (((top + bottom) / 2 - ring["y"]) * aspect) ** 2 >= (ring["d"] / 2) ** 2:
                problems.append(("off its own triangle", ring["layer"]))
    for ring, other in ((upper, lower), (lower, upper)):
        if ring["triangle"] and other["triangle"]:
            mine, theirs = [((t[0] + t[2]) / 2, (t[1] + t[3]) / 2) for t in (ring["triangle"], other["triangle"])]
            if (mine[0] - ring["x"]) ** 2 + ((mine[1] - ring["y"]) * aspect) ** 2 >= (theirs[0] - ring["x"]) ** 2 + ((theirs[1] - ring["y"]) * aspect) ** 2:
                problems.append(("nearer the other triangle", ring["layer"]))
    for ring in (upper, lower):
        box = (ring["x"] - ring["d"] / 2, ring["y"] - ring["h"] / 2, ring["x"] + ring["d"] / 2, ring["y"] + ring["h"] / 2)
        left, top, right, bottom = ring["frame"]
        if box[0] < left or box[1] < top or box[2] > right or box[3] > bottom:
            problems.append(("outside the view", ring["layer"]))
    return problems, rings


# The stacked view's own children and what it shows outside its scene: the scene and the rings' overlay only, no caption
# (the user's request of 2026-11-06, "“Exploded 3D registration review…” 小字去掉": the small caption at its bottom left,
# in both modes and both views).
STACKED_BARE = """() => { const pane = document.getElementById('stackedPreview');
    return {children: [...pane.children].map(node => node.getAttribute('class')), captions: document.querySelectorAll('.assembly-caption').length,
            text: [...pane.children].filter(node => !node.matches('.assembly-scene, .pin1-overlay')).map(node => node.textContent),
            words: ['registration review', 'visual spacing only', 'Plan view ·'].filter(word => document.body.innerText.includes(word))}; }"""


def stacked_bare(page):
    """``(ok, data)``: the stacked view holds its scene and its rings' overlay only, no caption, and the page says none of
    the caption's words (STACKED_BARE)."""
    data = page.evaluate(STACKED_BARE)
    return data == {"children": ["assembly-scene", "pin1-overlay"], "captions": 0, "text": [], "words": []}, data


# Each ring as the overlay draws it: ``samples`` points along its centre line on screen (frame pixels), its stroke.
PIN1_STROKE_RINGS = """([samples]) => { const frame = document.getElementById('stackedPreview').getBoundingClientRect();
    return [...document.querySelectorAll('#stackedPreview .pin1-overlay .pin1-ring-drawn')].map(drawn => {
      const [cx, cy, rx, ry] = ['cx', 'cy', 'rx', 'ry'].map(name => Number(drawn.getAttribute(name)));
      const ctm = drawn.getScreenCTM(); const points = [];
      for (let k = 0; ctm && k < samples; k += 1) {
        const angle = 2 * Math.PI * k / samples;
        const point = new DOMPoint(cx + rx * Math.cos(angle), cy + ry * Math.sin(angle)).matrixTransform(ctm);
        points.push([point.x - frame.left, point.y - frame.top]); }
      return {layer: drawn.classList.contains('is-upper') ? 'upper' : 'lower', points, width: frame.width,
              stroke: (getComputedStyle(drawn).stroke.match(/\\d+/g) || []).slice(0, 3).map(Number)}; }); }"""
# Hides every ring (the boards' own and the ones drawn over them), and with ``board`` that board too, for the backgrounds.
PIN1_HIDE = """([board]) => { let style = document.getElementById('pin1-check-hide');
    if (!style) { style = document.createElement('style'); style.id = 'pin1-check-hide'; document.head.append(style); }
    style.textContent = '#stackedPreview .pin1-ring, #stackedPreview .pin1-ring-drawn { visibility:hidden !important; }'
      + (board ? `#stackedPreview .assembly-board.is-${board} { visibility:hidden !important; }` : ''); }"""
PIN1_SHOW = "() => document.getElementById('pin1-check-hide')?.remove()"


def pin1_strokes(page, samples=120, tolerance=28, share=0.95):
    """Each of the stacked view's pin-1 rings drawn above both boards (P5-diagonal-bus.md section 27.8: the bottom FPC's
    ring, drawn inside its board, lay under the top FPC's translucent face, its stroke broken where it crossed the gold
    fingers): ``(problems, counts)``.  Along each ring's centre line as drawn (``samples`` points of the overlay's
    ellipse; pin1_shapes checks that it is the ring as it lies on screen) the points over the other board (where the view
    without the rings differs with that board hidden) must show the ring's own stroke colour (a pixel of the 3 x 3 around
    each within ``tolerance`` per channel), at ``share`` of them or more; ``counts``: per ring the points over the other
    board and those showing the stroke."""
    import io

    from PIL import Image

    # The element's screenshots scroll it into view: the page's scroll is put back after them, so the rings' positions
    # on screen (which other checks compare) are as before.
    scroll = page.evaluate("() => [window.scrollX, window.scrollY]")
    rings = page.evaluate(PIN1_STROKE_RINGS, [samples])

    def shot():
        return Image.open(io.BytesIO(page.locator("#stackedPreview").screenshot())).convert("RGB")

    shown = shot()
    page.evaluate(PIN1_HIDE, [""])
    bare = shot()
    others = {}
    for board in ("upper", "lower"):
        page.evaluate(PIN1_HIDE, [board])
        others[board] = shot()
    page.evaluate(PIN1_SHOW)
    page.evaluate("([x, y]) => window.scrollTo(x, y)", scroll)
    problems, counts = [], {}
    for ring in rings:
        scale = shown.width / ring["width"] if ring["width"] else 1.0
        other = others["lower" if ring["layer"] == "upper" else "upper"]
        over, stroked = 0, 0
        for px, py in ring["points"]:
            x, y = int(round(px * scale)), int(round(py * scale))
            if not (1 <= x < shown.width - 1 and 1 <= y < shown.height - 1):
                continue
            if max(abs(a - b) for a, b in zip(bare.getpixel((x, y)), other.getpixel((x, y)))) <= 8:
                continue  # not over the other board
            over += 1
            if any(max(abs(a - b) for a, b in zip(shown.getpixel((x + dx, y + dy)), ring["stroke"])) <= tolerance
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                stroked += 1
        counts[ring["layer"]] = (over, stroked)
        if over and stroked < share * over:
            problems.append(("covered", ring["layer"], over, stroked))
    if sorted(counts) != ["lower", "upper"]:
        problems.append(("rings", sorted(counts)))
    return problems, counts



# The rings filled, nothing else shown (the shadows and the faces' opacity off, and each face drawn from both sides: the
# top FPC's copper side, which holds its ring, faces away from above): the top FPC's red, the bottom FPC's blue, on
# white; ``{rings}`` the boards' own rings or the overlay's.
PIN1_SHAPE_CSS = """#stackedPreview { background:#fff !important; }
#stackedPreview * { visibility:hidden !important; filter:none !important; opacity:1 !important; backface-visibility:visible !important; }
#stackedPreview {rings} { visibility:visible !important; stroke:none !important; }
#stackedPreview {rings}.is-upper { fill:#ff0000 !important; }
#stackedPreview {rings}.is-lower { fill:#0000ff !important; }"""
PIN1_SHAPE_SET = """([css]) => { let style = document.getElementById('pin1-check-shape');
    if (!style) { style = document.createElement('style'); style.id = 'pin1-check-shape'; document.head.append(style); }
    style.textContent = css; }"""
PIN1_SHAPE_CLEAR = "() => document.getElementById('pin1-check-shape')?.remove()"


def _filled_ellipses(image, scale):
    """The red and the blue filled shapes of ``image`` (on white), each by its coverage-weighted moments: ``{layer: (x,
    y, a, b, angle)}`` in CSS pixels, its centroid, its semi-axes (``a`` the longer; a filled ellipse's second moments
    are a quarter of its squared semi-axes) and the angle of ``a`` (degrees, clockwise from the x axis)."""
    from PIL import ImageChops, Image

    # The view's edge rows and columns (its frame's antialiased edge) left out.
    image = image.crop((1, 1, image.width - 1, image.height - 1))
    box = ImageChops.difference(image, Image.new("RGB", image.size, (255, 255, 255))).getbbox()
    sums = {layer: [0.0] * 6 for layer in ("upper", "lower")}
    if box:
        left, top, right, bottom = box
        data = image.crop(box).load()
        for j in range(bottom - top):
            for i in range(right - left):
                red, green, blue = data[i, j]
                weight = (255 - green) / 255
                # On the line from white to red (the top FPC's) or to blue (the bottom FPC's): an edge pixel's coverage.
                layer = ("upper" if max(255 - red, abs(green - blue)) <= 12 else
                         "lower" if max(255 - blue, abs(red - green)) <= 12 else None)
                if weight < 0.05 or layer is None:
                    continue
                x, y = (left + i + 1.5) / scale, (top + j + 1.5) / scale
                total = sums[layer]
                for index, value in enumerate((1.0, x, y, x * x, y * y, x * y)):
                    total[index] += weight * value
    shapes = {}
    for layer, (m, sx, sy, sxx, syy, sxy) in sums.items():
        if m < 4:
            continue
        x, y = sx / m, sy / m
        cxx, cyy, cxy = sxx / m - x * x, syy / m - y * y, sxy / m - x * y
        half = math.hypot((cxx - cyy) / 2, cxy)
        large, small = (cxx + cyy) / 2 + half, max((cxx + cyy) / 2 - half, 0.0)
        shapes[layer] = (x, y, 2 * math.sqrt(large), 2 * math.sqrt(small), math.degrees(0.5 * math.atan2(2 * cxy, cxx - cyy)))
    return shapes


def pin1_shapes(page, size=0.05, centre=1.0):
    """Each of the stacked view's pin-1 rings drawn as the ring in its board lies on screen (P5-diagonal-bus.md section
    27.9: the exploded view had drawn each at its ring's box on screen, about 1.28 times the ring, the boards turned in
    their plane before the tilt): ``(problems, shapes)``.  The boards' own rings (unseen in the app) and the overlay's,
    each filled, alone on white: each drawn ring's semi-axes within ``size`` of its ring's and its centre within
    ``centre`` px; ``shapes``: per ring the ring's and the drawn one's (x, y, a, b, angle), CSS pixels in the view."""
    import io

    from PIL import Image

    scroll = page.evaluate("() => [window.scrollX, window.scrollY]")
    width = page.evaluate("() => document.getElementById('stackedPreview').getBoundingClientRect().width")
    measured = {}
    for label, rings in (("ring", ".assembly-board .pin1-ring"), ("drawn", ".pin1-overlay .pin1-ring-drawn")):
        page.evaluate(PIN1_SHAPE_SET, [PIN1_SHAPE_CSS.replace("{rings}", rings)])
        image = Image.open(io.BytesIO(page.locator("#stackedPreview").screenshot())).convert("RGB")
        measured[label] = _filled_ellipses(image, image.width / width if width else 1.0)
    page.evaluate(PIN1_SHAPE_CLEAR)
    page.evaluate("([x, y]) => window.scrollTo(x, y)", scroll)
    problems, shapes = [], {}
    for layer in ("upper", "lower"):
        ring, drawn = measured["ring"].get(layer), measured["drawn"].get(layer)
        shapes[layer] = {"ring": ring and tuple(round(value, 2) for value in ring), "drawn": drawn and tuple(round(value, 2) for value in drawn)}
        if not ring or not drawn:
            problems.append(("missing", layer, "ring" if not ring else "drawn"))
            continue
        ratios = (drawn[2] / ring[2], drawn[3] / ring[3]) if ring[3] > 0 else (math.inf, math.inf)
        if any(abs(ratio - 1) > size for ratio in ratios):
            problems.append(("size", layer, tuple(round(ratio, 3) for ratio in ratios)))
        if math.hypot(drawn[0] - ring[0], drawn[1] - ring[1]) > centre:
            problems.append(("centre", layer, round(math.hypot(drawn[0] - ring[0], drawn[1] - ring[1]), 2)))
    return problems, shapes


# The figures' controls in their frames (the user's request of 2026-11-06, index.html .figure-tools): per frame shown,
# its box, its chips (the controls' groups) and Reset view (where shown) relative to it, every button's size, and the
# boxes of what the figure draws under its controls' row (a 2D view's outline, label and pin-1 ring; a 3D view's
# outlines as projected; the plan view's outlines and drawn rings; the sensor on the part's canvas), all in CSS px.
FIGURE_CONTROLS = """() => { const box = node => { const r = node.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  const shown = node => node && !node.hidden && node.checkVisibility() && node.getBoundingClientRect().width > 0;
  const boxes = (scope, selector) => [...(scope ? scope.querySelectorAll(selector) : [])].filter(shown).map(box);
  const front = '.assembly-face > svg:not(.board-shadow)';
  const frames = {
    row: ['#rowCard .canvas-wrap', () => boxes(document.querySelector('#rowPreview:not([hidden])'), 'svg .outline, svg .view-label, svg > .pin1-ring')
      .concat(boxes(document.querySelector('#rowPreview3d:not([hidden])'), '.oblique-board > svg:not(.board-shadow) .outline'))],
    column: ['#columnCard .canvas-wrap', () => boxes(document.querySelector('#columnPreview:not([hidden])'), 'svg .outline, svg .view-label, svg > .pin1-ring')
      .concat(boxes(document.querySelector('#columnPreview3d:not([hidden])'), '.oblique-board > svg:not(.board-shadow) .outline'))],
    registration: ['.stack-figure.is-registration', () => boxes(document.getElementById('stackedPreview'), `${front} .outline, .pin1-overlay .pin1-ring-drawn`)],
    onPart: ['.stack-figure.is-on-part', () => boxes(document.getElementById('sensorOnPart'), 'canvas')],
  };
  const out = {};
  for (const [name, [selector, drawn]] of Object.entries(frames)) {
    const frame = document.querySelector(selector);
    if (!shown(frame)) continue;
    const [fl, ft] = box(frame); const rel = ([l, t, r, b]) => [l - fl, t - ft, r - fl, b - ft].map(v => Math.round(v * 10) / 10);
    const chips = [...frame.querySelectorAll(':scope > .figure-tools > *')].filter(shown);
    const reset = [...frame.querySelectorAll(':scope > .figure-reset')].filter(shown);
    out[name] = {frame: rel(box(frame)), chips: chips.map(chip => rel(box(chip))), reset: reset.map(node => rel(box(node))),
      buttons: [...chips, ...reset].flatMap(node => node.matches('button') ? [node] : [...node.querySelectorAll('button')]).filter(shown)
        .map(button => [button.textContent.trim(), Math.round(button.getBoundingClientRect().width * 10) / 10, Math.round(button.getBoundingClientRect().height * 10) / 10]),
      labels: chips.map(chip => [...chip.querySelectorAll('button')].filter(shown).map(button => button.textContent.trim())),
      drawn: drawn().map(rel)};
  }
  return out; }"""


def figure_controls(page, wrap=False):
    """The figures' controls in their frames (FIGURE_CONTROLS), ``(problems, data)``: each frame's chips in one row (two
    where ``wrap``), the first 12 px from its top and left, all inside it; Reset view 12 px from its top and right; every
    button 24 x 24 px or more; nothing the figure draws under a chip or Reset view (the sensor on the part's canvas
    starting under them)."""
    data = page.evaluate(FIGURE_CONTROLS)
    problems = []
    for name, item in data.items():
        frame, chips, reset = item["frame"], item["chips"], item["reset"]
        if not chips:
            problems.append((name, "no controls"))
            continue
        if abs(chips[0][0] - 12) > 1 or abs(chips[0][1] - 12) > 1:
            problems.append((name, "first chip not 12 px in", chips[0]))
        rows = sorted({round(chip[1]) for chip in chips})
        if len(rows) > (2 if wrap else 1):
            problems.append((name, "rows", rows))
        if any(chip[2] > frame[2] - 12 + 1 or chip[0] < 11 for chip in chips):
            problems.append((name, "chip outside the frame's 12 px", chips, frame))
        for node in reset:
            if abs(node[1] - 12) > 1 or abs(frame[2] - node[2] - 12) > 1:
                problems.append((name, "Reset view not 12 px from the top right", node, frame))
        small = [button for button in item["buttons"] if button[1] < 24 or button[2] < 24]
        if small:
            problems.append((name, "buttons under 24 x 24 px", small))
        over = [[drawn, control] for drawn in item["drawn"] for control in chips + reset
                if drawn[0] < control[2] and drawn[2] > control[0] and drawn[1] < control[3] and drawn[3] > control[1]]
        if name == "onPart":
            over = [[drawn, control] for drawn in item["drawn"] for control in chips + reset if drawn[1] < control[3] - 0.5]
        if over:
            problems.append((name, "drawn under the controls", over[:3]))
        if not item["drawn"]:
            problems.append((name, "nothing drawn"))
    return problems, data


if __name__ == "__main__":
    sys.exit(0)
