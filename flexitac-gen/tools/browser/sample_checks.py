"""The samples of Gen by Surface (index.html #samplePalette, web/samples/samples.json; the user's request of 2026-11-06:
"在这个索引的下方,放置两列stl,这个stl可以从左边拖到右边的框里面 ... 主要要做出 能从左边把cad 拖到右边框然后开始生成").

    FPC_PORT=19400 /tmp/fpc-browser-venv/bin/python tools/browser/sample_checks.py               # every part
    ... sample_checks.py part_drag part_phones                                                    # some

Against a running app.py (FPC_PORT; one browser job a server: it takes one surface request at a time) serving this
project, in headless Chromium on SwiftShader, as a visitor sees the page (no fold opened):
- part_palette: under the guide's three steps "Try a sample", its hint and eight tiles in two columns (samples.json's
  order, names and pictures loaded), all in a 1440 x 900 window's first screen; nothing else of the page moved (the
  steps, the 3D view, the workspace as without the palette, its bottom within the window).
- part_sizes (the review of 2026-11-06), the page with the palette against the page without it (taken out before
  main.js runs), scrollbars shown: on laptop windows (1366 x 768, 1280 x 720, 1440 x 790, 1024 x 768) the guide no
  scroller of its own, its steps' boxes as without the palette, the eight tiles in the first screen, no name cut; on a
  tall one (1920 x 1080) the tiles a thumbnail over the name; with Advanced Customization open at 1280 x 720 the
  steps' boxes as without the palette (the palette's grid, not the guide, gives way); on narrow pages (900 x 900,
  768 x 1024: beside the steps) the page's scroll after the default part's build, the 3D view's top and the guide's
  height as without the palette; on phones (390 x 844, 375 x 667) the palette at most 80 px high, the 3D view lower by
  no more than it.
- part_drag: each of the eight tiles dragged onto the 3D view with the mouse (Chromium's own drag and drop: dragstart
  on the tile, dragover and drop on the view; three of them dropped on the tools drawn over it, the surface menu, the
  camera row and the status): the view lit as for a file while the drag is over it, the sample loaded
  and its sensor generated at once (the Library sensor's build id, mapped with every check passing, the design's DRC
  passing: "Valid build"), its tile the one shown (aria-current), ./?sample=<id> in the address, the file note, the
  fit shipped for a Library finger and the server's for a whole gripper, no console error; a reload of ./?sample=<id>
  shows it again; an unknown one the UMI finger with a warning, ?sample dropped.
- part_keys: a click, Enter and Space on a tile load it as a drop does; a tile's focus ring.
- part_race: a sample dropped while another one loads (and again while its build is under way): the newer wins, its own
  build mapped, no placement mismatch, the older never shown at the end; the same sample twice is loaded once, and
  pressed twice 200 ms apart (one mesh fetched, one inspect); the sample shown pressed again is framed, not reloaded;
  the user's own file dropped after a sample and Remove model drop ?sample and the options it set; a sample pressed,
  then the user's own file or Remove model, then the sample again loads it.
- part_errors (the review of 2026-11-06): the user's own file during a sample's build (Generate sensor not left busy,
  the build stopped, not running); a sample whose mesh is refused (404) while the shown one builds (that build lands,
  its warning stays, no tile busy, no veil; once served, a press loads it); samples.json refused (500) and then
  served; Rectangular chosen while a sample is fetched (not loaded, the part shown kept) or built (stopped, not done,
  and a press builds it).
- part_rect: in Rectangular mode the guide and so the palette are hidden; back in Gen by Surface it is there.
- part_phones: at 390 x 844 and 360 x 740 (touch) the palette one sideways row under the steps, at most 80 px high,
  the hint saying tap, the page no wider than the window, every tile at least 24 x 24 CSS px, the first tile's focus
  ring inside the row; a tap loads a sample and brings the 3D view into sight (at once under reduced motion).
- part_firefox (with FPC_FIREFOX=1 and Playwright's Firefox installed): two tiles dragged onto the 3D view in Firefox,
  one onto the surface menu, each built (Chromium alone runs the other parts).
- part_static (with FPC_STATIC_SITE, a site built by tools/build_static_site.py; served under /flexitac-gen/ on
  FPC_STATIC_PORT as GitHub Pages serves it): a Library finger and a whole gripper dragged onto the 3D view, their sensors
  generated in the browser's engine (Pyodide), the samples' files static, no request for /api/ or outside the site.
- part_schemes: light and dark: the tiles on the surface colour with the text colour, the thumbnails on the 3D view's
  #f5f5f7 in both, the shown tile edged in the action blue; screenshots of the guide with the palette at 1440 x 900,
  1920 x 1080, 1366 x 768 and 390 in both, a drag over the view and a generated sample, to $FPC_BROWSER_OUT/shots
  (samples_*.png).
"""
from __future__ import annotations

import functools
import json
import os
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

from rp import SCRATCH, SHOTS, URL, check, summary, wait_until  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
SAMPLES = json.loads((WEB / "samples" / "samples.json").read_text(encoding="utf-8"))["samples"]
ENTRIES = json.loads((WEB / "library" / "entries.json").read_text(encoding="utf-8"))
BUILD = {sample["id"]: ENTRIES["variants"][sample["library"]]["build_id"] for sample in SAMPLES}
STATE = "() => JSON.parse(document.getElementById('cadState').textContent)"
# The default part (or a ?sample's) loaded and built, nothing in flight.
SETTLED = """() => { const s = JSON.parse(document.getElementById('cadState').textContent);
    return ['loaded', 'skipped', 'failed'].includes(s.default_part) && !['pending', 'running'].includes(s.default_build) && s.busy.length === 0
      && s.pending_build === null && s.sample.pending === null && s.loading === null; }"""
# One sample shown with its sensor built and mapped (its build id the argument's), nothing in flight.
BUILT = """([id, build]) => { const s = JSON.parse(document.getElementById('cadState').textContent);
    return s.sample.shown === id && s.sample.pending === null && s.busy.length === 0 && s.pending_build === null && s.loading === null
      && s.generated_build_id === build && s.verification !== null && s.overlay?.build_id === build; }"""
NOTE = "() => document.getElementById('cadFileNote').textContent"
STATUS = "() => document.getElementById('status').textContent"
TILES = """() => [...document.querySelectorAll('#samplePalette [data-sample]')].map(tile => { const box = tile.getBoundingClientRect();
    const img = tile.querySelector('img');
    return {id: tile.dataset.sample, name: tile.querySelector('.sample-name').textContent, left: Math.round(box.left), top: Math.round(box.top),
            width: Math.round(box.width), height: Math.round(box.height), shown: tile.checkVisibility(), loaded: img.complete && img.naturalWidth === 240,
            current: tile.getAttribute('aria-current'), busy: tile.getAttribute('aria-busy')}; })"""


def new_page(browser, width=1440, height=900, scheme="light", touch=False, reduced=False, scale=1):
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, has_touch=touch, is_mobile=touch,
                                  device_scale_factor=scale, reduced_motion="reduce" if reduced else "no-preference")
    page = context.new_page()
    page.logs = []
    page.refused = []
    page.on("console", lambda m: page.logs.append((m.type, m.text)))
    page.on("pageerror", lambda e: page.logs.append(("pageerror", str(e))))
    page.on("response", lambda r: page.refused.append((r.status, r.url)) if "/api/" in r.url and r.status >= 400 else None)
    return page


def errors_of(page, allowed=()):
    return [entry for entry in page.logs if entry[0] in ("error", "pageerror") and not any(text in entry[1] for text in allowed)]


def state(page):
    return page.evaluate(STATE)


def open_page(page, query=""):
    page.goto(URL + query)
    wait_until(page, "() => document.getElementById('cadState')?.textContent.startsWith('{')", 60)
    wait_until(page, SETTLED, 180)
    page.wait_for_timeout(150)


def built(page, sample_id, timeout=180):
    wait_until(page, BUILT, timeout, arg=[sample_id, BUILD[sample_id]])
    page.wait_for_timeout(100)
    return state(page)


def sample_ok(page, sample_id):
    """What a sample shown should be, and the misses (empty when it is so)."""
    s = state(page)
    sample = next(item for item in SAMPLES if item["id"] == sample_id)
    variant = ENTRIES["variants"][sample["library"]]
    mesh = sample["mesh"]["name"] if "mesh" in sample else ENTRIES["parts"][variant["part"]]["mesh"]["name"]
    note = page.evaluate(NOTE)
    want_note = f"Sample: {sample['name']}, whole gripper" if "mesh" in sample else f"From the Library: {variant['label']}"
    got = {"mesh": (s["mesh"] or {}).get("name"), "build": s["generated_build_id"], "proposal": (s["proposal"] or {}).get("build_id"),
           "checks": (s["verification"] or {}).get("ok"), "drc": page.evaluate(STATUS).startswith(f"Valid build {variant['build_id']}"),
           "fit": s["fit_source"], "address": page.evaluate("() => new URLSearchParams(location.search).get('sample')"),
           "note": note.replace(" ", " "), "current": [tile["id"] for tile in page.evaluate(TILES) if tile["current"] == "true"],
           "status": s["status"]["kind"], "error": s["error"]}
    want = {"mesh": mesh, "build": variant["build_id"], "proposal": variant["build_id"], "checks": True, "drc": True,
            "fit": "server" if "mesh" in sample else "shipped", "address": sample_id, "note": want_note, "current": [sample_id],
            "status": "ok", "error": None}
    return {key: (got[key], want[key]) for key in want if got[key] != want[key]}


def view_box(page):
    return page.evaluate("() => { const r = document.getElementById('cadView').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")


# Where on the 3D view's window a drag ends: its middle, or a tool drawn over it (the review of 2026-11-06: the menu on
# its left, where a tile dragged from the guide comes in, the camera row, the status had refused the drop).
TARGETS = {"centre": "() => { const r = document.getElementById('cadView').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }",
           "menu": "() => { const r = document.getElementById('cadTools').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 3]; }",
           "camera": "() => { const r = document.querySelector('.cad-views').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }",
           "status": "() => { const r = document.getElementById('cadStatus').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }"}


def drag_tile(page, sample_id, shot=None, onto="centre"):
    """A tile dragged onto the 3D view's window with the mouse (the browser's drag and drop), the view's highlight read
    over it, the element under the drop point named."""
    tile = page.locator(f'#samplePalette [data-sample="{sample_id}"]')
    tile.scroll_into_view_if_needed()
    box = tile.bounding_box()
    left, top, width, height = view_box(page)
    x, y = page.evaluate(TARGETS[onto])
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + 20, box["y"] + box["height"] / 2, steps=3)
    page.mouse.move(left + width / 2, top + height / 2, steps=8)
    page.mouse.move(x, y, steps=6)
    page.mouse.move(x + 3, y + 3, steps=2)
    page.dropped_on = page.evaluate("([x, y]) => { const node = document.elementFromPoint(x, y); return node ? (node.closest('#cadTools, .cad-views, #cadStatus, #cadView')?.id || node.closest('.cad-views') && 'cad-views' || node.tagName) : null; }", [x + 3, y + 3])
    lit = page.evaluate("() => document.getElementById('cadView').classList.contains('is-dropping')")
    if shot:
        page.screenshot(path=shot)
    page.mouse.up()
    page.wait_for_timeout(50)
    unlit = not page.evaluate("() => document.getElementById('cadView').classList.contains('is-dropping')")
    return lit, unlit


def part_palette(browser):
    page = new_page(browser)
    open_page(page)
    tiles = page.evaluate(TILES)
    layout = page.evaluate("""() => { const box = id => { const r = document.getElementById(id).getBoundingClientRect(); return [Math.round(r.top), Math.round(r.bottom), Math.round(r.left), Math.round(r.right)]; };
        return {guide: box('flowGuide'), steps: box('cadGuide'), palette: box('samplePalette'), view: box('cadView'), workspace: box('cadWorkspace'),
                title: document.getElementById('samplePaletteTitle').textContent, hint: document.getElementById('samplePaletteHint').innerText,
                width: document.documentElement.scrollWidth}; }""")
    check("palette: 'Try a sample' and its hint under the guide's steps, inside the guide",
          layout["title"] == "Try a sample" and layout["hint"] == "Drag onto the 3D view, or click." and layout["palette"][0] >= layout["steps"][1]
          and layout["guide"][2] <= layout["palette"][2] and layout["palette"][3] <= layout["guide"][3], layout)
    columns = sorted({tile["left"] for tile in tiles})
    check("palette: eight tiles in two columns of four, in samples.json's order with its names, every picture loaded",
          [tile["id"] for tile in tiles] == [sample["id"] for sample in SAMPLES] and [tile["name"] for tile in tiles] == [sample["name"] for sample in SAMPLES]
          and len(columns) == 2 and [tile["left"] for tile in tiles] == columns * 4 and len({tile["top"] for tile in tiles}) == 4
          and all(tile["loaded"] and tile["shown"] for tile in tiles), tiles)
    check("palette: all eight in a 1440 x 900 window's first screen, the page no wider than the window",
          max(tile["top"] + tile["height"] for tile in tiles) <= 900 and layout["width"] == 1440, (max(tile["top"] + tile["height"] for tile in tiles), layout["width"]))
    # The rest of the page where it is without the palette (the palette taken out of the page, then put back), the
    # guide a sticky column of the window's height.
    BOXES = """() => { const box = id => { const r = document.getElementById(id).getBoundingClientRect(); return [r.top, r.bottom, r.left, r.right].map(Math.round); };
        return [box('flowGuide'), box('cadGuide'), box('cadView'), box('cadWorkspace'), box('cadQuick'), document.documentElement.scrollHeight]; }"""
    with_palette = page.evaluate(BOXES)
    without = page.evaluate("(boxes) => { const palette = document.getElementById('samplePalette'); const place = palette.nextSibling; const parent = palette.parentNode;"
                            " palette.remove(); const out = (" + BOXES + ")(); parent.insertBefore(palette, place); return out; }")
    check("palette: nothing else moved (the guide, its steps, the 3D view, the workspace, Generate sensor and the page's height as "
          "without the palette; the guide the window's height)", with_palette == without and layout["guide"][1] - layout["guide"][0] == 900,
          (with_palette, without))
    check("palette: the default part's sensor as before (no sample shown, no ?sample)",
          state(page)["sample"] == {"pending": None, "shown": None} and page.evaluate("() => location.search") == "", state(page)["sample"])
    check("palette: no console errors", not errors_of(page), errors_of(page)[:4])
    page.close()


# The page as without the palette (taken out before main.js runs), for part_sizes.
NO_PALETTE = "document.addEventListener('DOMContentLoaded', () => document.getElementById('samplePalette')?.remove());"
GEOMETRY = """() => { const box = node => { if (!node) return null; const r = node.getBoundingClientRect(); return [r.left, r.top, r.width, r.height].map(Math.round); };
    const guide = document.getElementById('flowGuide'); const palette = document.getElementById('samplePalette');
    const tiles = [...document.querySelectorAll('#samplePalette [data-sample]')].map(tile => tile.getBoundingClientRect());
    return {scrollY: Math.round(scrollY), guide: box(guide), own_scroller: guide.scrollHeight > guide.clientHeight || guide.offsetWidth - guide.clientWidth > 1,
            steps: [...document.querySelectorAll('#cadGuide > .flow-step > button')].map(node => box(node).map((v, i) => i === 1 ? v - box(guide)[1] : i === 0 ? v - box(guide)[0] : v)),
            view: box(document.getElementById('cadView')), palette: box(palette),
            seen: tiles.filter(r => r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth).length,
            cut: [...document.querySelectorAll('#samplePalette .sample-name')].filter(n => n.scrollWidth > n.clientWidth + 1 || n.scrollHeight > n.clientHeight + 1).map(n => n.textContent),
            row: palette ? getComputedStyle(palette.querySelector('.sample')).flexDirection : null}; }"""


def part_sizes(browser):
    """The palette moves nothing at the common window sizes (the review of 2026-11-06), scrollbars shown as on Windows
    and Linux desktops: each size measured with the palette and without it."""
    shown = browser.browser_type.launch(args=WEBGL_ARGS, ignore_default_args=["--hide-scrollbars"])

    def measure(width, height, touch=False, without=False, customize=False):
        context = shown.new_context(viewport={"width": width, "height": height}, has_touch=touch, is_mobile=touch)
        page = context.new_page()
        if without:
            page.add_init_script(NO_PALETTE)
        page.goto(URL)
        wait_until(page, "() => document.getElementById('cadState')?.textContent.startsWith('{')", 60)
        wait_until(page, SETTLED, 180)
        page.wait_for_timeout(900)  # the build's scroll into sight (smooth) lands
        if customize:
            page.click("#guideCustomize")
            page.wait_for_timeout(900)
        out = page.evaluate(GEOMETRY)
        if (width, height) == (1366, 768) and not without and not customize:
            page.locator("#flowGuide").screenshot(path=f"{SHOTS}/samples_guide_1366x768_scrollbars.png")
        context.close()
        return out

    try:
        for width, height in ((1366, 768), (1280, 720), (1440, 790), (1024, 768)):
            got, bare = measure(width, height), measure(width, height, without=True)
            check(f"sizes {width} x {height}: the guide no scroller of its own, its steps' boxes as without the palette, the eight tiles "
                  "in the first screen, compact (a thumbnail beside its name), no name cut",
                  not got["own_scroller"] and got["steps"] == bare["steps"] and got["seen"] == 8 and got["row"] == "row" and not got["cut"]
                  and got["view"] == bare["view"], {key: got[key] for key in ("own_scroller", "seen", "row", "cut", "palette")})
        got = measure(1920, 1080)
        check("sizes 1920 x 1080: the tiles a thumbnail over the name, all eight in the first screen, no scroller of the guide's own",
              got["row"] == "column" and got["seen"] == 8 and not got["own_scroller"] and not got["cut"], {key: got[key] for key in ("row", "seen", "cut", "palette")})
        got, bare = measure(1280, 720, customize=True), measure(1280, 720, without=True, customize=True)
        check("sizes 1280 x 720 with Advanced Customization open: the guide's steps as without the palette (the palette gives way, not the steps)",
              got["steps"] == bare["steps"] and not got["own_scroller"], (got["steps"], bare["steps"], got["own_scroller"]))
        for width, height in ((900, 900), (768, 1024)):
            got, bare = measure(width, height, touch=width < 800), measure(width, height, touch=width < 800, without=True)
            check(f"sizes {width} x {height}: the palette beside the steps, the guide's height, the page's scroll after the build and "
                  "the 3D view's top as without the palette",
                  got["guide"][3] == bare["guide"][3] and got["scrollY"] == bare["scrollY"] and got["view"] == bare["view"]
                  and got["palette"][0] - got["guide"][0] > got["steps"][0][0] + got["steps"][0][2] and not got["cut"],
                  {"with": {key: got[key] for key in ("scrollY", "guide", "view", "palette")}, "without": {key: bare[key] for key in ("scrollY", "guide", "view")}})
        for width, height in ((390, 844), (375, 667)):
            got, bare = measure(width, height, touch=True), measure(width, height, touch=True, without=True)
            lower = (got["view"][1] + got["scrollY"]) - (bare["view"][1] + bare["scrollY"])
            check(f"sizes {width} x {height}: the palette one row of at most 80 px, the 3D view lower by no more than it",
                  got["palette"][3] <= 80 and 0 <= lower <= got["palette"][3] + 12, (got["palette"], lower))
    finally:
        shown.close()


def part_drag(browser):
    page = new_page(browser)
    open_page(page, "?debug")
    misses, lights, timings = [], [], []
    ontos = {2: "menu", 3: "camera", 5: "status"}
    for index, sample in enumerate(SAMPLES):
        started = time.monotonic()
        lit, unlit = drag_tile(page, sample["id"], shot=f"{SHOTS}/samples_drag_1440.png" if index == 6 else None, onto=ontos.get(index, "centre"))
        built(page, sample["id"])
        timings.append((sample["id"], round(time.monotonic() - started, 1)))
        lights.append((sample["id"], ontos.get(index, "centre"), page.dropped_on, lit, unlit))
        miss = sample_ok(page, sample["id"])
        if miss:
            misses.append((sample["id"], miss))
        if index == 7:
            page.screenshot(path=f"{SHOTS}/samples_generated_1440.png")
    print("    timings:", ", ".join(f"{name} {seconds} s" for name, seconds in timings), flush=True)
    check("drag: each tile lights the 3D view while dragged over it, as a file does, over the tools drawn on it too (the surface "
          "menu, the camera row, the status: each the element under the drop), and the light goes on the drop",
          all(lit and unlit for _, _, _, lit, unlit in lights)
          and [(onto, on) for onto, on in [(item[1], item[2]) for item in lights] if onto != "centre"] == [("menu", "cadTools"), ("camera", "cad-views"), ("status", "cadStatus")],
          lights)
    check("drag: each of the eight samples dragged onto the 3D view is loaded and its sensor generated at once: the Library sensor's "
          "build, mapped with every check passing, its DRC passing, the address ./?sample=<id>, the file note, its tile current, the "
          "fit shipped for a finger and the server's for a whole gripper", misses == [], misses[:4])
    check("drag: no console errors, no request refused", not errors_of(page) and not page.refused, (errors_of(page)[:4], page.refused[:4]))
    # A reload of ./?sample=<id> shows it again (the address says the sample shown).
    # A whole gripper's sensor in sight from its sample's camera (main.js sampleView), not hidden by the other finger that
    # faces it (?probe: the 3D view's pixels, viewer.js pixels(): the overlay's taxels drawn over the part, the face's own).
    for sample_id in ("widowx-250-gripper", "franka-hand-gripper", "umi-convex-tip13.8"):
        open_page(page, f"?sample={sample_id}&debug&probe")
        built(page, sample_id)
        miss = sample_ok(page, sample_id)
        check(f"drag: ./?sample={sample_id} as the page opens shows it with its sensor", miss == {}, miss)
        if sample_id.endswith("-gripper"):
            page.wait_for_timeout(300)
            look = page.evaluate("() => { const detail = {}; document.dispatchEvent(new CustomEvent('fpc:view-look', {detail})); const x = detail.result;"
                                 " return x && {overlay: x.markers.overlay?.px || 0, face: x.classes.selected?.px || 0}; }")
            check(f"drag: {sample_id}'s sensor in sight past the other finger (its taxels and its face drawn in the 3D view)",
                  look and look["overlay"] >= 3000 and look["face"] >= 5000, look)
    open_page(page, "?sample=bogus&debug")
    try:
        wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).status.kind === 'warning'", 15)
    except TimeoutError:
        pass
    s = state(page)
    check("drag: ./?sample=bogus shows the UMI finger with a warning, ?sample dropped (?debug kept)",
          (s["mesh"] or {}).get("name") == "UMI-Soft-Gripper-Finger.stl" and s["status"]["kind"] == "warning"
          and s["status"]["shown"] == "No sample is shown (no sample is named bogus); the UMI finger is shown."
          and page.evaluate("() => location.search") == "?debug" and s["sample"]["shown"] is None, (s["status"], page.evaluate("() => location.search")))
    check("drag: no console errors after the reloads", not errors_of(page), errors_of(page)[:4])
    page.close()


def part_keys(browser):
    page = new_page(browser)
    open_page(page)
    page.click('#samplePalette [data-sample="arx-x5"]')
    built(page, "arx-x5")
    clicked = sample_ok(page, "arx-x5")
    page.focus('#samplePalette [data-sample="i2rt-yam"]')
    page.keyboard.press("Enter")
    built(page, "i2rt-yam")
    entered = sample_ok(page, "i2rt-yam")
    page.focus('#samplePalette [data-sample="widowx-250-gripper"]')
    page.keyboard.press("Space")
    built(page, "widowx-250-gripper")
    spaced = sample_ok(page, "widowx-250-gripper")
    check("keys: a click, Enter and Space on a tile load its sample and generate its sensor", clicked == entered == spaced == {}, (clicked, entered, spaced))
    # Tab from the guide's last step to the first tile: its focus ring (outline) drawn.
    page.focus('#cadGuide .flow-step[data-step="3"] button')
    page.keyboard.press("Tab")
    ring = page.evaluate("""() => { const node = document.activeElement; const style = getComputedStyle(node);
        return {id: node.dataset?.sample || null, outline: style.outlineStyle, width: parseFloat(style.outlineWidth), visible: node.matches(':focus-visible')}; }""")
    check("keys: Tab from the guide's last step reaches the first tile, its focus ring drawn (2 px)",
          ring["id"] == SAMPLES[0]["id"] and ring["outline"] == "solid" and ring["width"] >= 2 and ring["visible"], ring)
    check("keys: no console errors", not errors_of(page), errors_of(page)[:4])
    page.close()


DROP = """(ids) => { const view = document.getElementById('cadView');
    for (const id of ids) { const data = new DataTransfer(); data.setData('application/x-flexitac-sample', id);
      view.dispatchEvent(new DragEvent('dragover', {dataTransfer: data, bubbles: true, cancelable: true}));
      view.dispatchEvent(new DragEvent('drop', {dataTransfer: data, bubbles: true, cancelable: true})); } }"""


DROP_WHILE_BUILDING = """(id) => new Promise(resolve => { const node = document.getElementById('cadState'); const view = document.getElementById('cadView');
    const drop = () => { const data = new DataTransfer(); data.setData('application/x-flexitac-sample', id);
      view.dispatchEvent(new DragEvent('dragover', {dataTransfer: data, bubbles: true, cancelable: true}));
      view.dispatchEvent(new DragEvent('drop', {dataTransfer: data, bubbles: true, cancelable: true})); };
    let observer = null; let timer = null;
    const look = () => { if (JSON.parse(node.textContent).pending_build === null) return false; observer?.disconnect(); clearTimeout(timer); drop(); resolve(true); return true; };
    if (look()) return;
    observer = new MutationObserver(look); observer.observe(node, {childList: true, characterData: true, subtree: true});
    timer = setTimeout(() => { observer.disconnect(); resolve(false); }, 60000); })"""


def part_race(browser):
    page = new_page(browser)
    open_page(page, "?debug")
    seen = []
    page.on("console", lambda m: seen.append(m.text) if "mismatch" in m.text.lower() else None)
    # Two drops in one go (the second while the first is fetched): the newer wins.
    page.evaluate(DROP, ["franka-hand-gripper", "unitree-dex1"])
    built(page, "unitree-dex1")
    first = (sample_ok(page, "unitree-dex1"), state(page)["sample"])
    # A drop while the shown sample's build is under way: that build lands, the newer sample's is built and mapped.
    # (Dropped in the page as the build starts: a shipped fit's build is under way some 50 ms, under a poll's reach.)
    page.evaluate(DROP, ["umi-trap-tip5.8"])
    during = page.evaluate(DROP_WHILE_BUILDING, "makermods-metal")
    built(page, "makermods-metal")
    page.wait_for_timeout(600)
    second = (sample_ok(page, "makermods-metal"), state(page)["map_error"], page.evaluate(STATUS)[:60])
    check("race: two samples dropped at once and one dropped while the other's build is under way: the newer wins, its own build "
          "mapped with every check passing, no placement mismatch", first[0] == {} and second[0] == {} and second[1] is None
          and not any("mismatch" in text.lower() for text in seen) and during, (first, second, during, seen[:3]))
    # The same sample twice: loaded once (one inspect request for it).
    page.surface = []
    page.on("request", lambda r: page.surface.append(r.url) if "/api/surface/inspect" in r.url else None)
    page.evaluate(DROP, ["i2rt-yam", "i2rt-yam"])
    built(page, "i2rt-yam")
    check("race: the same sample dropped twice at once is loaded once", len(page.surface) == 1 and sample_ok(page, "i2rt-yam") == {}, page.surface)
    # Pressed twice 200 ms apart: one mesh fetched, one inspect (it is on its way until its build returns).
    fetched = []
    page.on("request", lambda r: fetched.append(r.url.rsplit("/", 1)[-1]) if r.url.endswith("/unitree-dex1.stl") or "/api/surface/inspect" in r.url else None)
    page.click('#samplePalette [data-sample="unitree-dex1"]')
    page.wait_for_timeout(200)
    page.click('#samplePalette [data-sample="unitree-dex1"]')
    built(page, "unitree-dex1")
    page.wait_for_timeout(300)
    check("race: a tile pressed twice 200 ms apart loads its sample once (one mesh fetched, one inspect)",
          fetched == ["unitree-dex1.stl", "inspect"] and sample_ok(page, "unitree-dex1") == {}, fetched)
    # The sample shown pressed again: framed, not reloaded (no request; what the visitor changed stays).
    fetched.clear()
    before = page.evaluate("() => document.getElementById('cadFill').value")
    page.evaluate("() => { const c = document.getElementById('cadFill'); c.value = String(Number(c.value) - 0.05); c.dispatchEvent(new Event('input', {bubbles: true})); }")
    changed = page.evaluate("() => document.getElementById('cadFill').value")
    page.click('#samplePalette [data-sample="unitree-dex1"]')
    page.wait_for_timeout(1200)
    s = state(page)
    check("race: the sample shown pressed again is not reloaded (no request, its build as it was, the visitor's change kept)",
          fetched == [] and s["sample"] == {"pending": None, "shown": "unitree-dex1"} and s["generated_build_id"] == BUILD["unitree-dex1"]
          and page.evaluate("() => document.getElementById('cadFill').value") == changed, (fetched, s["sample"], changed))
    page.evaluate("(value) => { const c = document.getElementById('cadFill'); c.value = value; c.dispatchEvent(new Event('input', {bubbles: true})); }", before)
    # The user's own file after a sample: ?sample and the options it set go, the note is its own.
    own = Path(SCRATCH) / "downloads" / "my-finger.stl"
    own.parent.mkdir(parents=True, exist_ok=True)
    own.write_bytes((WEB / "vendor" / "umi" / "UMI-Soft-Gripper-Finger.stl").read_bytes())
    page.set_input_files("#cadFile", str(own))
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.mesh?.name === 'my-finger.stl' && s.busy.length === 0; }", 60)
    s = state(page)
    check("race: the user's own file after a sample drops ?sample (?debug kept), no tile current, the note its own",
          page.evaluate("() => location.search") == "?debug" and s["sample"] == {"pending": None, "shown": None}
          and page.evaluate(NOTE) == "or drag an STL file onto the 3D view below", (page.evaluate("() => location.search"), s["sample"], page.evaluate(NOTE)))
    page.evaluate(DROP, ["arx-x5"])
    built(page, "arx-x5")
    page.click("#cadRemove")
    page.wait_for_timeout(300)
    s = state(page)
    check("race: Remove model after a sample drops ?sample and the tile's mark", page.evaluate("() => location.search") == "?debug"
          and s["sample"]["shown"] is None and s["mesh"] is None, (page.evaluate("() => location.search"), s["sample"]))
    # A sample pressed, then the user's own file (or Remove model) while it is fetched, then the sample again: loaded.
    page.route("**/library/meshes/arx-x5.stl", lambda route: (page.wait_for_timeout(1500), route.continue_()))
    page.click('#samplePalette [data-sample="arx-x5"]')
    page.wait_for_timeout(200)
    page.set_input_files("#cadFile", str(own))
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).mesh?.name === 'my-finger.stl'", 60)
    midway = state(page)["sample"]
    page.click('#samplePalette [data-sample="arx-x5"]')
    built(page, "arx-x5")
    after_file = (midway, sample_ok(page, "arx-x5"))
    page.route("**/library/meshes/i2rt-yam.stl", lambda route: (page.wait_for_timeout(1500), route.continue_()))
    page.click('#samplePalette [data-sample="i2rt-yam"]')
    page.wait_for_timeout(200)
    page.click("#cadRemove")
    page.click('#samplePalette [data-sample="i2rt-yam"]')
    built(page, "i2rt-yam")
    check("race: a sample pressed, then the user's own file or Remove model while it is fetched, then the sample again: it loads "
          "(the first press, replaced, neither busy nor swallowing the second)",
          after_file[0] == {"pending": None, "shown": None} and after_file[1] == {} and sample_ok(page, "i2rt-yam") == {}, (after_file, sample_ok(page, "i2rt-yam")))
    page.unroute("**/library/meshes/arx-x5.stl")
    page.unroute("**/library/meshes/i2rt-yam.stl")
    # A request sent while an aborted one still runs on the server is answered 503 (it takes one surface request at a
    # time) and retried by web/cad/api.js: the only console error a race may leave.
    check("race: no console errors (but the server's busy answer, retried)", not errors_of(page, allowed=("status of 503",)), errors_of(page)[:4])
    page.close()


QUICK = "() => { const b = document.getElementById('cadQuickGenerate'); return {disabled: b.disabled, title: b.title}; }"
IDLE = """() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.pending_build === null && s.loading === null
    && !['pending', 'running'].includes(s.default_build) && s.sample.pending === null; }"""


def part_errors(browser):
    """The review of 2026-11-06: a sample's build superseded, a sample not loaded, the Rectangular mode meanwhile."""
    page = new_page(browser)
    open_page(page, "?debug")
    own = Path(SCRATCH) / "downloads" / "my-finger.stl"
    own.parent.mkdir(parents=True, exist_ok=True)
    own.write_bytes((WEB / "vendor" / "umi" / "UMI-Soft-Gripper-Finger.stl").read_bytes())
    # The user's own file while a sample's sensor is built: the build stops (not left running), Generate sensor free.
    page.click('#samplePalette [data-sample="widowx-250-gripper"]')
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).default_build === 'running'", 60)
    page.set_input_files("#cadFile", str(own))
    wait_until(page, IDLE, 90)
    page.wait_for_timeout(600)
    s, quick = state(page), page.evaluate(QUICK)
    check("errors: the user's own file during a sample's build stops it (stopped, not running), Generate sensor enabled, no tile busy or current",
          (s["mesh"] or {}).get("name") == "my-finger.stl" and s["default_build"] == "stopped" and not quick["disabled"] and "Working" not in quick["title"]
          and s["sample"] == {"pending": None, "shown": None} and s["selection"] is not None, (s["default_build"], quick, s["sample"]))
    # A sample whose mesh is refused while the shown one builds: that build lands, the warning stays after it.
    page.click('#samplePalette [data-sample="widowx-250-gripper"]')
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).default_build === 'running'", 60)
    page.route("**/samples/franka-hand-gripper.stl", lambda route: route.fulfill(status=404, body="not here"))
    page.click('#samplePalette [data-sample="franka-hand-gripper"]')
    wait_until(page, IDLE, 120)
    page.wait_for_timeout(600)
    s, quick = state(page), page.evaluate(QUICK)
    busy = page.evaluate("() => [...document.querySelectorAll('#samplePalette [aria-busy]')].map(tile => tile.dataset.sample)")
    check("errors: a sample refused (404) while the shown one builds: that sensor lands as it was, the warning stays, no veil, no tile busy, "
          "Generate sensor not left busy", sample_ok(page, "widowx-250-gripper") == {"status": ("warning", "ok")}
          and s["status"]["shown"] == "The sample Franka Hand was not loaded (HTTP 404)." and s["loading"] is None and busy == [] and "Working" not in quick["title"],
          (sample_ok(page, "widowx-250-gripper"), s["status"], busy, quick))
    page.unroute("**/samples/franka-hand-gripper.stl")
    page.click('#samplePalette [data-sample="franka-hand-gripper"]')
    built(page, "franka-hand-gripper")
    check("errors: once served, a press loads it", sample_ok(page, "franka-hand-gripper") == {}, sample_ok(page, "franka-hand-gripper"))
    page.close()
    # samples.json refused, then served (a page of its own: the index is read once a page).
    page = new_page(browser)
    page.route("**/samples/samples.json", lambda route: route.fulfill(status=500, body="no"))
    open_page(page, "?debug")
    page.click('#samplePalette [data-sample="arx-x5"]')
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).status.kind === 'warning'", 30)
    wait_until(page, IDLE, 60)
    s = state(page)
    first = ((s["mesh"] or {}).get("name"), s["generated_build_id"], s["status"]["shown"], s["loading"], s["sample"])
    page.unroute("**/samples/samples.json")
    page.click('#samplePalette [data-sample="arx-x5"]')
    built(page, "arx-x5")
    check("errors: samples.json refused (500): a warning, the UMI finger and its sensor kept, no veil; once served, a press loads the sample",
          first[0] == "UMI-Soft-Gripper-Finger.stl" and first[2] == "The sample ARX X5 was not loaded (HTTP 500)." and first[3] is None
          and first[4] == {"pending": None, "shown": None} and sample_ok(page, "arx-x5") == {}, first)
    # Rectangular chosen while a sample is fetched: not loaded, the part shown kept; while it is built: stopped (not
    # done), and back in Gen by Surface a press builds it.
    page.route("**/library/meshes/unitree-dex1.stl", lambda route: (page.wait_for_timeout(1500), route.continue_()))
    page.click('#samplePalette [data-sample="unitree-dex1"]')
    page.wait_for_timeout(200)
    page.click("label:has(#modeRect)")
    page.wait_for_timeout(2500)
    s = state(page)
    fetched = ((s["mesh"] or {}).get("name"), s["sample"], s["status"]["shown"], page.evaluate("() => new URLSearchParams(location.search).get('sample')"))
    page.click("label:has(#modeCad)")
    page.wait_for_timeout(300)
    page.unroute("**/library/meshes/unitree-dex1.stl")
    page.click('#samplePalette [data-sample="unitree-dex1"]')
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).default_build === 'running'", 60)
    page.click("label:has(#modeRect)")
    wait_until(page, IDLE, 60)
    page.wait_for_timeout(300)
    stopped = state(page)["default_build"]
    page.click("label:has(#modeCad)")
    page.wait_for_timeout(300)
    page.click('#samplePalette [data-sample="unitree-dex1"]')
    built(page, "unitree-dex1")
    check("errors: Rectangular chosen while a sample is fetched: not loaded (the part shown kept, said so); while it is built: stopped, "
          "not done; back in Gen by Surface a press builds it",
          fetched[0] == "arx-x5.stl" and fetched[1] == {"pending": None, "shown": "arx-x5"} and fetched[2].startswith("The sample Unitree Dex1-1 was not loaded")
          and fetched[3] == "arx-x5" and stopped == "stopped" and sample_ok(page, "unitree-dex1") == {}, (fetched, stopped))
    # Back in Gen by Surface after Rectangular cut a build short, main.js setMode maps the last build generated onto the
    # part shown (a build of the other mode's, its own design) and the server refuses it as a mismatch (422), which the
    # status reports; as before the samples, for any part.
    check("errors: no console errors (but the refused files, the server's busy answer, retried, and the mismatch of the last build "
          "mapped on the way back from Rectangular)",
          not errors_of(page, allowed=("status of 503", "status of 500", "status of 404", "status of 422"))
          and all(url.endswith("/api/surface/map") for status, url in page.refused if status == 422), (errors_of(page)[:4], page.refused[:4]))
    page.close()


def part_rect(browser):
    page = new_page(browser)
    open_page(page)
    page.click("label:has(#modeRect)")
    page.wait_for_timeout(300)
    hidden = page.evaluate("() => [document.getElementById('flowGuide').checkVisibility(), document.getElementById('samplePalette').checkVisibility()]")
    page.screenshot(path=f"{SHOTS}/samples_rect_1440.png")
    page.click("label:has(#modeCad)")
    page.wait_for_timeout(500)
    shown = page.evaluate("() => document.getElementById('samplePalette').checkVisibility()")
    page.click('#samplePalette [data-sample="widowx-250-gripper"]')
    built(page, "widowx-250-gripper")
    check("rect: in Rectangular mode the guide and its palette are hidden; back in Gen by Surface the palette is there and works",
          hidden == [False, False] and shown and sample_ok(page, "widowx-250-gripper") == {}, (hidden, shown))
    check("rect: no console errors", not errors_of(page), errors_of(page)[:4])
    page.close()


def part_phones(browser):
    for width, height in ((390, 844), (360, 740)):
        for reduced in (False, True):
            page = new_page(browser, width, height, touch=True, reduced=reduced, scale=2)
            open_page(page)
            tiles = page.evaluate(TILES)
            layout = page.evaluate("""() => { const p = document.getElementById('samplePalette').getBoundingClientRect(); const s = document.getElementById('cadGuide').getBoundingClientRect();
                const grid = document.querySelector('.sample-grid'); const g = grid.getBoundingClientRect(); const first = grid.querySelector('.sample').getBoundingClientRect();
                return {below: p.top >= s.bottom, width: document.documentElement.scrollWidth, rows: new Set([...grid.children].map(li => Math.round(li.getBoundingClientRect().top))).size,
                        scrolls: grid.scrollWidth > grid.clientWidth, height: Math.round(p.height), hint: document.getElementById('samplePaletteHint').innerText,
                        ring_room: Math.round(Math.min(first.left - g.left, first.top - g.top))}; }""")
            if not reduced:
                page.screenshot(path=f"{SHOTS}/samples_guide_{width}_light.png")
            check(f"phones {width} x {height}: the palette one sideways row under the steps ({layout['height']} px, at most 80), the hint "
                  "saying tap, the page no wider than the window, every tile at least 24 x 24 px, the first tile's focus ring "
                  "(3 px out) inside the row",
                  layout["below"] and layout["rows"] == 1 and layout["scrolls"] and layout["width"] == width and layout["height"] <= 80
                  and layout["hint"] == "Drag onto the 3D view, or tap." and layout["ring_room"] >= 3
                  and all(tile["width"] >= 24 and tile["height"] >= 24 for tile in tiles), (layout, [(t["width"], t["height"]) for t in tiles]))
            # A tap from the top of the page (the guide in sight, the view below it): the sample loads, the 3D view comes
            # into sight, at once under reduced motion.
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(200)
            page.evaluate("() => document.querySelector('.sample-grid').scrollLeft = 0")
            page.tap('#samplePalette [data-sample="umi-trap-tip5.8"]')
            page.wait_for_timeout(30)
            soon = page.evaluate("() => window.scrollY")
            built(page, "umi-trap-tip5.8")
            page.wait_for_timeout(800)
            seen = page.evaluate("() => { const r = document.getElementById('cadView').getBoundingClientRect(); return Math.min(r.bottom, innerHeight) - Math.max(r.top, 0) >= r.height / 2; }")
            check(f"phones {width} x {height}{' (reduced motion)' if reduced else ''}: a tap loads the sample and brings the 3D view into sight"
                  f"{' at once' if reduced else ''}", sample_ok(page, "umi-trap-tip5.8") == {} and seen and (not reduced or soon > 0), (sample_ok(page, "umi-trap-tip5.8"), seen, soon))
            check(f"phones {width} x {height}: no console errors", not errors_of(page), errors_of(page)[:4])
            page.close()


def part_schemes(browser):
    looks = {}
    for scheme in ("light", "dark"):
        page = new_page(browser, scheme=scheme)
        open_page(page)
        page.click('#samplePalette [data-sample="franka-hand-gripper"]')
        built(page, "franka-hand-gripper")
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        looks[scheme] = page.evaluate("""() => { const tile = document.querySelector('#samplePalette [data-sample="arx-x5"]'); const current = document.querySelector('#samplePalette .is-current');
            const s = getComputedStyle(tile); const img = getComputedStyle(tile.querySelector('img'));
            return {surface: s.backgroundColor, text: s.color, thumb: img.backgroundColor, edge: getComputedStyle(current).borderTopColor,
                    guide: getComputedStyle(document.getElementById('flowGuide')).backgroundColor}; }""")
        page.locator("#flowGuide").screenshot(path=f"{SHOTS}/samples_guide_1440_{scheme}.png")
        page.screenshot(path=f"{SHOTS}/samples_page_1440_{scheme}.png")
        check(f"schemes: no console errors ({scheme})", not errors_of(page), errors_of(page)[:4])
        page.close()
        for width, height in ((1920, 1080), (1366, 768), (900, 900)):
            page = new_page(browser, width, height, scheme=scheme)
            open_page(page)
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            (page.locator("#flowGuide") if width > 980 else page).screenshot(path=f"{SHOTS}/samples_guide_{width}x{height}_{scheme}.png")
            page.close()
        page = new_page(browser, 390, 844, scheme=scheme, touch=True, scale=2)
        open_page(page)
        page.locator("#flowGuide").screenshot(path=f"{SHOTS}/samples_guide_390_{scheme}.png")
        page.close()
    check("schemes: the tiles on the surface colour with the text colour in each scheme, the thumbnails on the 3D view's #f5f5f7 in "
          "both, the shown tile edged in the action blue",
          looks["light"]["surface"] == "rgb(255, 255, 255)" and looks["dark"]["surface"] == "rgb(28, 28, 30)"
          and looks["light"]["text"] == "rgb(29, 29, 31)" and looks["dark"]["text"] == "rgb(245, 245, 247)"
          and looks["light"]["thumb"] == looks["dark"]["thumb"] == "rgb(245, 245, 247)"
          and looks["light"]["edge"] == looks["dark"]["edge"] == "rgb(0, 113, 227)", looks)


class SiteFiles(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".wasm": "application/wasm", ".js": "text/javascript", ".mjs": "text/javascript",
                      ".webp": "image/webp"}
    seen: list = []

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        SiteFiles.seen.append(self.path)
        super().do_GET()

    def do_POST(self):
        SiteFiles.seen.append(self.path)
        self.send_error(405)


def part_static(browser):
    site = os.environ.get("FPC_STATIC_SITE")
    if not site:
        print("    skipped: FPC_STATIC_SITE (a built site: tools/build_static_site.py --out <dir>) is not set", flush=True)
        return
    folder = Path(site).resolve()
    port = int(os.environ.get("FPC_STATIC_PORT", "19403"))
    server = ThreadingHTTPServer(("127.0.0.1", port), functools.partial(SiteFiles, directory=str(folder.parent)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}/{folder.name}/"
    try:
        page = new_page(browser)
        outside = []
        # The header's counts are the one request outside the site (web/backend.js refreshes them from GitHub's API).
        page.on("request", lambda request: outside.append(request.url) if request.url.startswith("http") and not request.url.startswith(base)
                and not request.url.startswith("https://api.github.com/") else None)
        SiteFiles.seen.clear()
        page.goto(base + "?debug")
        wait_until(page, "() => document.getElementById('cadState')?.textContent.startsWith('{')", 120)
        wait_until(page, SETTLED, 600)
        timings = []
        for sample_id in ("i2rt-yam", "franka-hand-gripper"):
            started = time.monotonic()
            lit, unlit = drag_tile(page, sample_id)
            built(page, sample_id, timeout=600)
            timings.append((sample_id, round(time.monotonic() - started, 1)))
            miss = sample_ok(page, sample_id)
            check(f"static: {sample_id} dragged onto the 3D view on the static site: its sensor generated in the browser's engine", lit and miss == {}, (lit, miss))
        print("    timings:", ", ".join(f"{name} {seconds} s" for name, seconds in timings), flush=True)
        api = [path for path in SiteFiles.seen if "/api/" in path]
        files = sorted({path.split("?")[0] for path in SiteFiles.seen if "/static/samples/" in path})
        check("static: the samples are static files of the site (its index, the thumbnails, the whole gripper's mesh), no request for "
              "/api/ or outside the site", not api and not outside and f"/{folder.name}/static/samples/samples.json" in files
              and f"/{folder.name}/static/samples/franka-hand-gripper.stl" in files and sum(1 for path in files if path.endswith(".webp")) == 8,
              (api[:3], outside[:3], files))
        page.screenshot(path=f"{SHOTS}/samples_static_1440.png")
        check("static: no console errors", not errors_of(page), errors_of(page)[:4])
        page.close()
    finally:
        server.shutdown()


def part_firefox(browser):
    """Two tiles dragged onto the 3D view in Firefox, one onto the surface menu over it (FPC_FIREFOX=1)."""
    if os.environ.get("FPC_FIREFOX") != "1":
        print("    skipped: FPC_FIREFOX=1 is not set (Playwright's Firefox, PLAYWRIGHT_BROWSERS_PATH where it is)", flush=True)
        return
    firefox = PLAYWRIGHT.firefox.launch()
    try:
        page = firefox.new_page(viewport={"width": 1440, "height": 900})
        page.logs = []
        page.on("console", lambda m: page.logs.append((m.type, m.text)))
        page.on("pageerror", lambda e: page.logs.append(("pageerror", str(e))))
        open_page(page, "?debug")
        for sample_id, onto in (("arx-x5", "centre"), ("widowx-250-gripper", "menu")):
            lit, unlit = drag_tile(page, sample_id, onto=onto)
            built(page, sample_id)
            check(f"firefox {firefox.version}: {sample_id} dragged onto the 3D view ({onto}) lights it and is built", lit and unlit and sample_ok(page, sample_id) == {},
                  (lit, unlit, sample_ok(page, sample_id)))
        check("firefox: no console errors", not errors_of(page), errors_of(page)[:4])
    finally:
        firefox.close()


PARTS = (part_palette, part_sizes, part_drag, part_keys, part_race, part_errors, part_rect, part_phones, part_schemes, part_static, part_firefox)
PLAYWRIGHT = None


def main():
    global PLAYWRIGHT
    with sync_playwright() as playwright:
        PLAYWRIGHT = playwright
        browser = playwright.chromium.launch(args=WEBGL_ARGS)
        for part in [part for part in PARTS if len(sys.argv) < 2 or part.__name__ in sys.argv[1:]]:
            print(f"--- {part.__name__}", flush=True)
            try:
                part(browser)
            except Exception as error:  # noqa: BLE001 - report and continue
                check(f"{part.__name__} ran to completion", False, repr(error))
        browser.close()
    return summary()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
