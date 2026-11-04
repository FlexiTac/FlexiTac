"""CAD-mode checks (web/cad/): mode switch, STL loading, surface selection, base edge, fit, Generate, mapping, downloads.

Against a running app.py (FPC_PORT) with the example meshes in asset/ (skipped when absent):
- Rectangular mode is untouched: no CAD request, no WebGL canvas, the six labelled SVGs, no console error.
- Soft finger: candidate #1 is the 3087.7 mm2 planar face; the tools on the 3D view's left; a click selects, a click again deselects, Undo; base side 0 (radio) and
  side 1 (Base edge tool on the model); fit gives proposals; #1 previews rows x columns taxels; Generate writes the
  form and runs /api/generate once with the proposal's build id; DRC passes; the map overlay has rows x columns
  taxels and every verification record passes; the four downloads are non-empty and named by the build id;
  editing the form greys the overlay and disables the downloads; regenerating a changed design reports
  E_SURFACE_PLACEMENT_MISMATCH ("fit again").
- Crank tip_left: candidate #1 is the 2957.3 mm2 developable pad; base auto; the default fit (Containment: Field
  only; the field follows the selected area, no Field shape since P5-diagonal-bus.md section 26.16) proposes a masked field of 688 taxels (34 x 34, the tip-first field of P5-diagonal-bus.md
  section 26, the 696 next; 666 of 32 x 32 before shaped fields took the rectangles' caps, section 21, 683 before the
  corner tolerance at every convex corner, section 24, 696 before section 26) on the 70 mm leg with the narrow tip (13.9 mm, not the cut corner's), Whole board the 549 of phase P4
  (Field shape rectangle's 17 x 18 = 306 before section 26.16).
- Masked crank (Containment: Whole board): the proposal is a masked field (its field polygon has more than 4 points,
  the table shows "N of R x C", the preview and the overlay have its N taxels); Generate sends the mask with the
  form and builds the proposal's build id; the summary badge reads "N of R x C taxels active"; the map has its
  readout; the taxel CSV lists every R x C position with its active flag; CAD -> Rectangular -> CAD keeps the mask
  (the form still builds the proposal, downloads stay ready); a rows edit clears the mask with a note and the
  regenerated build no longer matches the placement; a trace edit the mask no longer fits blocks Generate with
  E_MASK_ROUTING shown in the mask's note, and "Use the full field" drops the mask.
- No rectangle controls (P5-diagonal-bus.md section 26.16, the user's decision: what CAD generates depends only on the
  selected area): no Field shape, no Board rules, no Largest rectangle in the border editor; the fit request names
  none of shape, template or rectangle_preference_pct, and Containment and Row traces stay the user's.
- Field only on the soft finger (side 0; the default containment): 708 taxels against the whole board's 470 (a masked
  50 x 12; the 45 x 8 rectangle's 360 before masked fields took the rectangles' caps, P5-diagonal-bus.md section 21); the
  proposal card shows the tip, the bands, each board's share on the surface and the overhang; the tip equals the Row
  outline's width at ROW_01's centre in the flat view; the boards are dotted off the surface; Generate sends
  routing.row_sides with the form and builds the proposal's build id; every map record passes (field_clearance),
  the routing report and the folded Row order are shown; the card and the stacked view say both boards share one
  outline over the field (the Column FPC overhangs the sides as the Row FPC does); the stacked view names the
  stacked tails (the Row tail over the Column tail); the taxel CSV's Row pins follow the pads.
- Row traces Left and Right round-trip through Fit and Generate with their build ids; a form edit of the Row
  traces is a placement mismatch; Rectangular mode shows the field and sends it (P5-diagonal-bus.md section 18: the
  diagonal Row bus with both, Straight channel as "channel").
- The P5d/P5e reviews' findings: a changed option makes the proposals stale (Generate waits for a new fit and
  says so; back at the fitted value they are current); Fit again after Generate maps the build without a busy
  server; Scan order Reverse lists the Row pins from ROW_02 in the map panel and the stacked view; a Whole-board
  proposal generated after a Field-only one builds its own build id without Row traces; Whole board and back keeps
  the Row traces chosen; three rows list their pins once; the tail extension's range is the server's; a full field
  has no masked badge and its CSV no active column; the overhang is the bands', the tails end together
  (P5-diagonal-bus.md section 27.3) at least the extension past the edge, the 3D view says what it leaves out; the
  stacked view's plan has the two FPCs' pin-1 rings apart, in each side mode.
- ASCII STL: the same facets and candidate as the binary file.
- 1024 x 768: no horizontal page overflow, the proposals table fits without scrolling, the view stays in sight after
  Fit; WebGL disabled: "WebGL unavailable", the rest still works.
- The corner tolerance (P5-diagonal-bus.md section 16): a 30 x 38 mm plate with 4 mm corners takes the full
  14 x 18 (252) and maps with field_corner_overhang; with 5 mm corners the masked 248 stays first.
- The template is app.js state (no fetch shim): CAD Generate -> Rectangular -> Generate -> CAD reports the template
  mismatch (never "verified"); the form's own Generate after a fit sends the default template.
- Form limits of the surface template: with /api/default?template= served (an app.py feature), Max columns goes to
  64 and a 58-column proposal builds and maps; without it, Max columns stops at 32.  A design outside the limits never
  overwrites the form.
- Selection presets: Custom angles send every value (no hidden blend radius); the Surface preset and list.
- A tail edit keeps the placement download in step with the mapped build; a rounded pad takes a picked point as
  the base; empty, oversized and odd ASCII files; double Generate submits once.
Screenshots go to $FPC_BROWSER_OUT/shots (cad_*.png).
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
import struct
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

from rp import DONE, RECT_URL, SCRATCH, SHOTS, URL, check, pin1_shapes, pin1_strokes, stacked_pin1, summary, unfold, wait_until  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOFT = ROOT / "asset" / "soft_gripper_finger.stl"
CRANK = ROOT / "asset" / "crank_gripper" / "tip_left.stl"
DOWNLOADS = Path(SCRATCH) / "downloads"
WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
# A trace width and spacing (mm) at which the crank's masked proposal no longer routes (E_MASK_ROUTING).
MASK_BREAKING_TRACE = "0.127"
STATE = "() => JSON.parse(document.getElementById('cadState').textContent)"
IDLE = "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0; }"


def new_page(browser, width=1440, height=900, folded=False):
    context = browser.new_context(viewport={"width": width, "height": height}, accept_downloads=True)
    if not folded:
        unfold(context)
    page = context.new_page()
    page.logs = []
    page.surface = []
    page.generate = []
    page.on("console", lambda m: page.logs.append((m.type, m.text, (m.location or {}).get("url", ""))))
    page.on("pageerror", lambda e: page.logs.append(("pageerror", str(e), "")))
    page.on("request", lambda r: page.surface.append(r.url) if "/api/surface/" in r.url else None)

    def on_response(response):
        if response.url.endswith("/api/generate") and response.request.method == "POST":
            try:
                page.generate.append((json.loads(response.request.post_data or "null"), response.json()))
            except Exception as error:  # noqa: BLE001 - diagnostics only
                page.generate.append((None, {"error": str(error)}))
    page.on("response", on_response)
    return page


def template_served():
    """Whether this app.py serves /api/default?template= (else app.js keeps the default limits)."""
    try:
        with urllib.request.urlopen(f"{URL}api/default?template=surface_matrix_v1", timeout=30) as response:
            return response.status == 200
    except urllib.error.HTTPError:
        return False


SERVED = None


def errors_of(page, allowed=()):
    # Without the app.py feature, app.js's request for the surface template's profile is answered 400 (expected); the
    # default part's 404 is open_cad's (default_part=False).
    def expected(entry):
        return ((not SERVED and "/api/default?template=" in entry[2] and "status of 400" in entry[1])
                or (entry[2].endswith(DEFAULT_PART_PATH) and "status of 404" in entry[1]))
    return [entry[:2] for entry in page.logs if entry[0] in ("error", "pageerror") and not expected(entry) and not any(a in entry[1] for a in allowed)]


def state(page):
    return page.evaluate(STATE)


def status_of(page):
    return page.inner_text("#status")


def settle(page, timeout=90):
    page.wait_for_timeout(60)
    wait_until(page, IDLE, timeout)
    page.wait_for_timeout(60)


DEFAULT_PART_PATH = "/static/vendor/umi/UMI-Soft-Gripper-Finger.stl"
DEFAULT_PART_FILE = ROOT / "web" / "vendor" / "umi" / "UMI-Soft-Gripper-Finger.stl"
DEFAULT_PART = "**" + DEFAULT_PART_PATH
# The default part loaded (or not) and its sensor built (or stopped), nothing in flight.
DEFAULT_SETTLED = """() => { const s = JSON.parse(document.getElementById('cadState').textContent);
    return ['loaded', 'skipped', 'failed'].includes(s.default_part) && !['pending', 'running'].includes(s.default_build) && s.busy.length === 0
      && s.pending_build === null && (s.default_part !== 'loaded' || s.mesh !== null); }"""


def set_caps(page, caps):
    # Max rows / columns as a user sets them (marked edited, so the template's limits keep them).
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).limits_served !== null", 30)
    page.evaluate("""caps => ['cadMaxRows', 'cadMaxColumns'].forEach(id => { const c = document.getElementById(id);
        c.value = String(caps); c.dispatchEvent(new Event('input', {bubbles: true})); })""", caps)


def open_cad(page, caps=64, default_part=False):
    """CAD mode at #cad as the checks were written: without the default part (its request answered 404: no mesh, no
    surface request, no build of its own; part_default_cad checks it), the fit's caps at ``caps`` (64, the template's
    maximum, as before the user's default of 32; None keeps the default).  ``default_part=True``: the default part loaded
    and its sensor built first."""
    if not default_part:
        page.route(DEFAULT_PART, lambda route: route.fulfill(status=404, content_type="text/plain", body="not in this check"))
    page.goto(URL + "#cad")
    wait_until(page, DONE, 60)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).webgl !== 'not loaded'", 30)
    wait_until(page, DEFAULT_SETTLED, 120)
    if caps is not None:
        set_caps(page, caps)


# One step (index.html #cadQuick, #cadCustomize): what the row under the view holds (Generate sensor alone since the
# user's request of 2026-11-02), whether the button is in sight and enabled and its title, whether Advanced Customization is open and
# whether its controls are in sight.
QUICK = """() => { const button = document.getElementById('cadQuickGenerate');
    return {row: [...document.getElementById('cadQuick').querySelectorAll('button, p, a')].map(node => node.textContent.trim()),
            shown: button.checkVisibility(), generate: !button.disabled, title: button.title, customize: document.getElementById('cadCustomize').open,
            hidden: Object.fromEntries(['cadSides', 'cadPitch', 'cadFit', 'cadProposalWrap', 'cadGenerate'].map(id => [id, document.getElementById(id).checkVisibility()]))}; }"""
# The 3D view's status and loading veil (index.html #cadStatus, #cadLoading): the status's text (None when hidden),
# whether it lies in the view's bottom-right corner (within 20 px of its right and bottom edges), the veil and its text,
# and whether the workspace's header holds a status.
STATUS_PLACE = """() => { const status = document.getElementById('cadStatus'); const veil = document.getElementById('cadLoading');
    const view = document.getElementById('cadView').getBoundingClientRect(); const box = status.getBoundingClientRect();
    return {text: status.hidden ? null : status.textContent, corner: !status.hidden && view.right - box.right >= 0 && view.right - box.right <= 20
              && view.bottom - box.bottom >= 0 && view.bottom - box.bottom <= 20,
            veil: !veil.hidden, veilText: document.getElementById('cadLoadingText').textContent,
            inHeader: document.querySelector('#cadWorkspace > header .cad-status') !== null}; }"""


def part_remove_model(browser):
    """Remove model, in the 3D view's tools (the user's request of 2026-10-31): the model, its selection, border, base edge,
    proposals and map leave (the drop zone back, the button and the tools that need a model disabled, the status says
    which file went); a build already generated stays below; the default part does not come back (not on a mode switch
    either); a file chosen then loads as before.  Pressed while the default part is still on its way, the load stops and
    the part is dropped when it arrives."""
    page = new_page(browser, folded=True)
    page.goto(URL)
    wait_until(page, DONE, 60)
    wait_until(page, DEFAULT_SETTLED, 120)
    page.wait_for_timeout(300)
    s = state(page)
    built = s["generated_build_id"]
    check("remove: enabled with the default part and its sensor (a build generated)", not page.is_disabled("#cadRemove") and s["mesh"] is not None and built, (s["mesh"], built))
    page.click("#cadRemove")
    page.wait_for_timeout(300)
    s = state(page)
    status = page.evaluate(STATUS_PLACE)
    check("remove: the model and everything on it leave (mesh, selection, border, proposals, map, overlay), the drop zone is back",
          s["mesh"] is None and s["selection"] is None and s["border"] is None and s["proposals"] == 0 and s["overlay"] is None
          and s["verification"] is None and s["side"] == "auto" and page.is_visible("#cadDrop"), s)
    check("remove: the status says which file went; Remove model, Edit border, Undo and Clear are disabled",
          status["text"] == "UMI-Soft-Gripper-Finger.stl removed." and all(page.is_disabled(f"#{name}") for name in ("cadRemove", "cadEditBorder", "cadUndo", "cadClear")), status)
    shown = page.evaluate("() => !document.body.classList.contains('cad-no-build')")
    check("remove: the build already generated stays below (its results shown)", s["generated_build_id"] == built and shown, (s["generated_build_id"], shown))
    page.click("label:has(#modeRect)")
    page.wait_for_timeout(200)
    page.click("label:has(#modeCad)")
    page.wait_for_timeout(1500)
    s = state(page)
    check("remove: the default part does not come back (Rectangular and back)", s["mesh"] is None and s["loading"] is None, (s["mesh"], s["loading"], s["default_part"]))
    load(page, DEFAULT_PART_FILE)
    s = state(page)
    check("remove: a file chosen afterwards loads as before (\"... loaded\", Remove model enabled again)",
          s["mesh"]["name"] == DEFAULT_PART_FILE.name and s["status"]["shown"] == f"{DEFAULT_PART_FILE.name} loaded" and not page.is_disabled("#cadRemove"), s["status"])
    check("remove: no console errors", not errors_of(page), errors_of(page))
    page.close()
    # Pressed while the default part is on its way.
    page = new_page(browser, folded=True)
    page.held = []
    page.route(DEFAULT_PART, lambda route: page.held.append(route))
    page.goto(URL)
    wait_until(page, DONE, 60)
    end = time.monotonic() + 30
    while not page.held and time.monotonic() < end:
        page.wait_for_timeout(40)
    enabled = not page.is_disabled("#cadRemove")
    page.click("#cadRemove")
    page.wait_for_timeout(200)
    veil = page.evaluate(STATUS_PLACE)
    page.held[0].continue_()
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).default_part === 'skipped'", 30)
    page.wait_for_timeout(500)
    s = state(page)
    check("remove while loading: enabled during the load; the veil goes, the status says the load stopped and the part, when "
          "it arrives, is dropped (no mesh, no sensor)", enabled and not veil["veil"] and veil["text"] == "Loading stopped." and s["mesh"] is None
          and s["default_build"] == "stopped" and page.is_visible("#cadDrop"), (enabled, veil, s["mesh"], s["default_build"], s["default_part"]))
    check("remove while loading: no console errors", not errors_of(page), errors_of(page))
    page.close()


# At rest: nothing in flight, Generate sensor not at work, no model loading, the default part's build over.
AT_REST = """() => { const s = JSON.parse(document.getElementById('cadState').textContent);
    return s.busy.length === 0 && s.pending_build === null && !s.step_running && !s.loading && !['pending', 'running'].includes(s.default_build); }"""


def at_rest(page, timeout=120):
    # Twice: a step that follows another (the map after Generate's form request) starts a moment later.
    for _ in range(2):
        wait_until(page, AT_REST, timeout)
        page.wait_for_timeout(500)
    wait_until(page, AT_REST, timeout)


def facet_centroid(path, facet):
    data = Path(path).read_bytes()
    values = struct.unpack("<9f", data[84 + 50 * facet + 12:84 + 50 * facet + 48])
    return [round((values[k] + values[k + 3] + values[k + 6]) / 3, 3) for k in range(3)]


def part_one_step(browser):
    """One step to a sensor (the user's requests of 2026-11-02): the default part's sensor is generated at once; then a
    click on another face (Advanced Customization folded) selects that face alone and builds nothing, the line under the
    view saying so and Generate sensor lit (the Gerber buttons off); Generate sensor fits it and generates its proposal
    #1, mapped onto the part; a click on the selected face does nothing; Undo brings the contact face back, again only
    chosen; with Advanced Customization open an option changed runs nothing, and closed again only Generate sensor applies it; a
    model loaded gets its largest flat face selected, generated with Generate sensor."""
    page = new_page(browser, folded=True)
    page.goto(URL)
    wait_until(page, DONE, 60)
    wait_until(page, DEFAULT_SETTLED, 120)
    at_rest(page)
    first = state(page)
    check("one step: the default part's sensor is generated at once, Generate sensor off (nothing to generate)",
          first["default_build"] == "done" and first["quick"]["kind"] == "ok" and not first["quick"]["generate"], first["quick"])
    page.evaluate("() => document.querySelector('.cad-diagnostics').open = true")
    page.evaluate("() => document.getElementById('cadView').scrollIntoView({block: 'center'})")
    page.click("[data-cad-view='-y']"); page.wait_for_timeout(500)
    page.fill("#cadProbe", ",".join(map(str, facet_centroid(DEFAULT_PART_FILE, 935)))); page.dispatch_event("#cadProbe", "input"); page.wait_for_timeout(100)
    x, y = (float(value) for value in page.inner_text("#cadProbeOut").split(","))
    builds = len(page.generate)
    page.mouse.click(x, y); page.wait_for_timeout(300); at_rest(page)
    s = state(page)
    off = page.get_attribute("#cadQuickGenerate", "title") == s["quick"]["text"]
    check("one step: a click on another face selects that face alone (the fin's side, 1823.0 mm2) and builds nothing; Generate "
          "sensor lit, its title saying so",
          s["ops"] == 1 and s["selection"] and round(s["selection"]["area_mm2"], 1) == 1823.0 and s["proposals"] == 0 and len(page.generate) == builds
          and s["generated_build_id"] == first["generated_build_id"] and s["quick"]["kind"] == "todo"
          and s["quick"]["text"] == "Face selected (1823.0 mm²): Generate sensor to put the sensor on it." and s["quick"]["generate"] and off, (s["selection"], s["quick"], off))
    page.click("#cadQuickGenerate"); page.wait_for_timeout(300); at_rest(page)
    s = state(page)
    check("one step: Generate sensor fits the face and generates its proposal #1, mapped onto the part, every check passing; the "
          "line says what the sensor is, Generate sensor off again",
          s["proposal"] and s["proposal"]["rank"] == 1 and s["generated_build_id"] == s["proposal"]["build_id"] != first["generated_build_id"]
          and s["verification"]["ok"] and s["quick"]["kind"] == "ok" and s["quick"]["text"].startswith("86 taxels in a 17 × 29 field") and not s["quick"]["generate"],
          (s["generated_build_id"], s["quick"]))
    moved = s["generated_build_id"]
    builds = len(page.generate)
    page.mouse.click(x, y); page.wait_for_timeout(600); at_rest(page)
    s = state(page)
    check("one step: a click on the selected face does nothing", s["generated_build_id"] == moved and len(page.generate) == builds and s["ops"] == 1
          and s["proposals"] > 0, (s["generated_build_id"], len(page.generate), s["proposals"]))
    page.click("#cadUndo"); page.wait_for_timeout(300); at_rest(page)
    s = state(page)
    check("one step: Undo brings the contact face back (3088.6 mm2), only chosen (Generate sensor lit, the sensor as it was)",
          s["selection"] and round(s["selection"]["area_mm2"], 1) == 3088.6 and s["generated_build_id"] == moved and s["quick"]["generate"]
          and s["quick"]["kind"] == "todo", (s["selection"], s["generated_build_id"], s["quick"]))
    page.click("#cadQuickGenerate"); page.wait_for_timeout(300); at_rest(page)
    s = state(page)
    undone = s["generated_build_id"]
    check("one step: Generate sensor puts a sensor of its own on it", undone not in (moved, None) and s["verification"]["ok"] and s["quick"]["kind"] == "ok", s["quick"])
    page.click("#cadCustomize > summary"); page.wait_for_timeout(300)
    page.fill("#cadPitch", "3"); page.wait_for_timeout(1000)
    s = state(page)
    check("one step: with Advanced Customization open a changed option runs nothing (the proposals stale, the sensor as it was)",
          s["customize"] and s["fit_stale"] and s["generated_build_id"] == undone, (s["customize"], s["fit_stale"], s["generated_build_id"]))
    page.click("#cadCustomize > summary"); page.wait_for_timeout(1000)
    s = state(page)
    check("one step: closed again, still nothing runs; the line says the settings changed, Generate sensor lit",
          not s["customize"] and s["fit_stale"] and s["generated_build_id"] == undone and s["quick"]["text"] == "Settings changed: Generate sensor to update it."
          and s["quick"]["generate"], s["quick"])
    page.click("#cadQuickGenerate"); page.wait_for_timeout(300); at_rest(page)
    s = state(page)
    check("one step: Generate sensor applies the option (3.0 mm pitch, generated and mapped)",
          not s["fit_stale"] and s["generated_build_id"] not in (undone, None) and s["fit_options"]["pitch_mm"] == 3
          and s["verification"]["ok"] and "· 3.0 mm pitch ·" in s["quick"]["text"], (s["generated_build_id"], s["quick"]))
    page.evaluate("() => { const c = document.getElementById('cadPitch'); c.value = '2'; c.dispatchEvent(new Event('input', {bubbles: true})); }")
    if SOFT.exists():
        built = s["generated_build_id"]
        load(page, SOFT); at_rest(page)
        s = state(page)
        check("one step: a model loaded gets its largest flat face selected (the soft finger's 3087.7 mm2), nothing generated",
              s["mesh"]["name"] == SOFT.name and s["selection"] and round(s["selection"]["area_mm2"], 1) == 3087.7 and s["generated_build_id"] == built
              and s["quick"]["generate"], (s["selection"], s["quick"]))
        page.click("#cadQuickGenerate"); page.wait_for_timeout(300); at_rest(page)
        s = state(page)
        check("one step: Generate sensor puts the sensor on it, generated and mapped",
              s["generated_build_id"] == s["proposal"]["build_id"] != built and s["verification"]["ok"] and s["quick"]["kind"] == "ok", s["quick"])
    check("one step: no console errors", not errors_of(page), errors_of(page))
    page.close()


def load(page, path):
    # The file is loaded once the state names it (the default part may be the mesh until then).
    page.set_input_files("#cadFile", str(path))
    wait_until(page, "(name) => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.mesh !== null && s.mesh.name === name && s.busy.length === 0; }",
               60, Path(path).name)
    page.wait_for_timeout(150)


def pick(page, seed, preset="flat"):
    # A click on the surface of a seed facet, through the diagnostics input (main.js pickSurface).
    page.evaluate("""([seed, preset]) => { const input = document.getElementById('cadPick'); input.value = `${seed}:${preset}`;
        input.dispatchEvent(new Event('change', {bubbles: true})); }""", [seed, preset])
    settle(page)


def candidate(page, rank=1, kind="flat"):
    # The server's candidate surface of that rank (the page lists none since 2026-10-30), picked as a click on it.
    pick(page, state(page)["candidates"][kind][rank - 1], kind)


def view_center(page):
    page.locator("#cadView").scroll_into_view_if_needed()
    box = page.locator("#cadView").bounding_box()
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def probe(page, point):
    # The probe sits in the collapsed Diagnostics block: set it without opening it.
    text = page.evaluate("""text => { const input = document.getElementById('cadProbe'); input.value = text;
        input.dispatchEvent(new Event('input', {bubbles: true})); return document.getElementById('cadProbeOut').textContent; }""",
                         ", ".join(f"{value:.6f}" for value in point))
    return [float(value) for value in text.split(",")] if text else None


def save(page, selector):
    with page.expect_download() as info:
        page.click(selector)
    download = info.value
    target = DOWNLOADS / download.suggested_filename
    download.save_as(str(target))
    return download.suggested_filename, target.read_bytes()


def ascii_copy(binary: Path, target: Path) -> None:
    """Write the binary STL as ASCII, facet order kept."""
    data = binary.read_bytes()
    count = struct.unpack("<I", data[80:84])[0]
    lines = ["solid copy"]
    for index in range(count):
        values = struct.unpack("<12f", data[84 + 50 * index: 84 + 50 * index + 48])
        lines.append(f"  facet normal {values[0]:.9g} {values[1]:.9g} {values[2]:.9g}")
        lines.append("    outer loop")
        for corner in range(3):
            x, y, z = values[3 + 3 * corner: 6 + 3 * corner]
            lines.append(f"      vertex {x:.9g} {y:.9g} {z:.9g}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid copy")
    target.write_text("\n".join(lines) + "\n", encoding="ascii")


# ---------------------------------------------------------------------------

def part_rect_unchanged(browser):
    page = new_page(browser, 1600, 1000)
    page.goto(RECT_URL)
    wait_until(page, DONE, 60)
    page.wait_for_timeout(300)
    info = page.evaluate("""() => ({mode: document.body.dataset.mode, hidden: document.getElementById('cadWorkspace').hidden,
        canvases: document.querySelectorAll('canvas').length, labelled: document.querySelectorAll('svg[aria-label]').length,
        tablists: document.querySelectorAll('[role=tablist]').length, hash: location.hash,
        state: JSON.parse(document.getElementById('cadState').textContent)})""")
    check("rect: body[data-mode=rect], CAD workspace hidden, #rect", info["mode"] == "rect" and info["hidden"] and info["hash"] == "#rect", info)
    check("rect: no canvas (no WebGL context) and three.js not loaded", info["canvases"] == 0 and info["state"]["webgl"] == "not loaded", info)
    check("rect: no surface request, one /api/generate at boot", not page.surface and len(page.generate) == 1, (page.surface, len(page.generate)))
    check("rect: six labelled SVGs and the four preview tablists, as before", info["labelled"] == 6 and info["tablists"] == 2, info)
    body = page.generate[0][0] if page.generate else {}
    check("rect: the boot payload keeps its keys, and the Row traces (both: the diagonal Row bus, section 18)",
          list(body) == ["schema_version", "template_id", "name", "rows", "columns", "pitch_x_mm", "pitch_y_mm",
                         "row_electrode_width_mm", "column_electrode_width_mm", "top_tail_length_mm",
                         "bottom_tail_length_mm", "connector_side", "row_fpc_position", "scan_order",
                         "trace_width_mm", "trace_space_mm", "connector", "routing"] and body.get("routing") == {"row_sides": "both"}, list(body))
    page.click("#modeCad")
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).webgl !== 'not loaded'", 30)
    switched = page.evaluate("() => [document.body.dataset.mode, document.getElementById('cadWorkspace').hidden, location.hash, document.querySelectorAll('#cadView canvas').length]")
    check("switch to CAD: data-mode cad, workspace shown, no hash (CAD mode is the default), one canvas", switched == ["cad", False, "", 1], switched)
    wait_until(page, DEFAULT_SETTLED, 60)
    page.click("#modeRect")
    back = page.evaluate("() => [document.body.dataset.mode, document.getElementById('cadWorkspace').hidden, location.hash]")
    check("switch back: data-mode rect, workspace hidden, #rect", back == ["rect", True, "#rect"], back)
    check("rect part: no console errors", not errors_of(page), errors_of(page))
    page.close()


NO_CAD = """() => [document.title, document.body.innerText, ...[...document.querySelectorAll('[title], [aria-label], [placeholder]')]
    .flatMap(node => ['title', 'aria-label', 'placeholder'].map(name => node.getAttribute(name) || ''))].filter(text => /\\bCAD\\b/i.test(text))"""


def part_default_cad(browser):
    """The app opens in Gen by Surface (CAD mode; the user's defaults of 2026-10-30): no hash, the workspace shown, the UMI
    fin-ray finger loaded (web/vendor/umi: 3624 facets, mm) and named in the 3D view's status ("... loaded", at its bottom
    right; the workspace's header holds none since 2026-10-31, the file step hints at dragging a file in), and its sensor
    already generated:
    the first flat candidate (the contact face, 3088.6 mm2) selected, fitted within Max rows and Max columns 32 (the
    template allows 64) and the first proposal generated (32 x 12) and mapped onto the part, its results shown; the page
    never says "CAD"; Rectangular at #rect, kept across a reload; a file chosen before the default part arrives is kept
    (the default part and its sensor dropped)."""
    page = new_page(browser, folded=True)  # the page as it opens (no fold opened, no form shown beside it)
    page.goto(URL)
    wait_until(page, DONE, 60)
    wait_until(page, DEFAULT_SETTLED, 120)
    page.wait_for_timeout(300)
    s = state(page)
    info = page.evaluate("() => [document.body.dataset.mode, document.getElementById('cadWorkspace').hidden, location.hash, document.getElementById('modeCad').checked]")
    check("default: the app opens in Gen by Surface (no hash, the workspace shown, Gen by Surface checked)", info == ["cad", False, "", True], info)
    check("default: the UMI fin-ray finger is loaded (UMI-Soft-Gripper-Finger.stl, 3624 facets, mm, watertight)",
          s["default_part"] == "loaded" and s["mesh"] is not None and s["mesh"]["name"] == "UMI-Soft-Gripper-Finger.stl"
          and s["mesh"]["facets"] == 3624 and s["mesh"]["unit"] == "mm" and s["mesh"]["watertight"], (s["default_part"], s["mesh"]))
    status = page.evaluate(STATUS_PLACE)
    check("default: the 3D view's status says the model is loaded (\"UMI-Soft-Gripper-Finger.stl loaded\") at the view's bottom "
          "right, no loading veil, no status in the workspace's header",
          status["text"] == "UMI-Soft-Gripper-Finger.stl loaded" and status["corner"] and not status["veil"] and not status["inHeader"]
          and s["status"]["kind"] == "ok" and s["loading"] is None, (status, s["status"], s["loading"]))
    note = page.inner_text("#cadFileNote")
    check("default: the file step hints that an STL can also be dragged onto the view", note == "or drag an STL file onto the 3D view below", note)
    caps = page.evaluate("() => ['cadMaxRows', 'cadMaxColumns'].map(id => [document.getElementById(id).value, document.getElementById(id).max])")
    check("default: Max rows and Max columns are 32 (within the template's limits)",
          caps == [["32", "64"], ["32", "64" if SERVED else "32"]], caps)
    check("default: its contact face is selected (the first flat candidate, 3088.6 mm2, planar, 4 sides)",
          s["selection"] is not None and abs(s["selection"]["area_mm2"] - 3088.58) < 0.01 and s["selection"]["kind"] == "planar"
          and s["selection"]["sides"] == 4 and s["ops"] == 1, s["selection"])
    # The user's border of 2026-10-30: 65 mm of the face from the tip (side 2), its full width (25.8 mm), the exit Auto.
    uv = s["border"]["uv"] if s["border"] else []
    edges = [math.dist(uv[k], uv[(k + 1) % len(uv)]) for k in range(len(uv))]
    check("default: its border is 65 mm of the face from the tip, the face's full width (25.8 mm), the exit Auto",
          s["border"] is not None and s["border"]["edited"] and len(uv) == 4 and [round(edge, 3) for edge in edges] == [25.8, 65.0, 25.8, 65.0]
          and s["side"] == "auto", (s["border"], edges, s["side"]))
    # One step (the user's requests of 2026-11-02): under the view Generate sensor alone (no line, no downloads: those are
    # the Downloads section's); everything else under Advanced Customization, folded.
    quick = page.evaluate(QUICK)
    check("default: under the 3D view Generate sensor alone, in sight and off (nothing to generate), its title saying what the "
          "sensor is (\"32 × 12 = 384 taxels · 2.0 mm pitch · all 12 checks pass on the part.\"); Advanced Customization folded, the "
          "base edge, the settings, Fit, the proposals and Generate out of sight",
          quick["row"] == ["Generate sensor"] and quick["shown"] and quick["generate"] is False
          and quick["title"] == "32 × 12 = 384 taxels · 2.0 mm pitch · all 12 checks pass on the part." and s["quick"]["kind"] == "ok"
          and not quick["customize"] and not any(quick["hidden"].values()) and s["customize"] is False, quick)
    page.click("#cadCustomize > summary"); page.wait_for_timeout(300)
    auto = page.inner_text('#cadSides label:has(input[value="auto"])').strip()
    check("default: Auto names its edge only: 'Auto (Border edge 0)', the edge across the face toward the mount (how it chooses in its tooltip)",
          auto == "Auto (Border edge 0)" and "chosen: Border edge 0" in page.get_attribute('#cadSides label:has(input[value="auto"])', "title"), auto)
    # Its fit is shipped (web/vendor/umi/default-fit.json): no fit request goes to the server, the sensor shows at once.
    check("default: its fit is the shipped one (no /api/surface/fit request)",
          s["fit_source"] == "shipped" and not any(url.endswith("/api/surface/fit") for url in page.surface), (s["fit_source"], page.surface))
    check("default: its sensor is fitted within 32 rows and 32 columns: the first proposal, 32 x 12 (384 taxels), out across border edge 0",
          s["proposal"] is not None and s["proposal"]["rank"] == 1 and (s["proposal"]["rows"], s["proposal"]["columns"]) == (32, 12)
          and (s["proposal"]["base_kind"], s["proposal"]["base_side"]) == ("border", 0)
          and (s["fit_options"] or {}).get("max_rows") == 32 and (s["fit_options"] or {}).get("max_columns") == 32, (s["proposal"], s["fit_options"]))
    shown = page.evaluate("() => !document.body.classList.contains('cad-no-build') && document.querySelectorAll('#stackedPreview .assembly-board').length")
    check("default: its sensor is generated as the default build (the proposal's build id, valid, mapped onto the part, the results shown)",
          s["default_build"] == "done" and s["generated_build_id"] == s["proposal"]["build_id"] and status_of(page).startswith(f"Valid build {s['proposal']['build_id']}")
          and s["verification"] is not None and s["verification"]["ok"] and shown == 2 and len(page.generate) == 2,
          (s["default_build"], s["generated_build_id"], status_of(page)[:80], s["verification"] and s["verification"]["ok"], shown, len(page.generate)))
    heading = page.evaluate("() => [document.getElementById('cadTitle').textContent, document.getElementById('cadStepFile').textContent]")
    check("default: the workspace is step 1, 'Load your gripper', its file '3D model'", heading == ["1Load your gripper", "3D model"], heading)
    # The order of work on the page's left in Gen by Surface (the user's requests of 2026-10-30; three steps since
    # 2026-11-02): the title and three steps, the first two done once the default sensor is built and mapped, the last one
    # next; in sight from the top of the page to its end, the step whose part is in view lit, each step scrolling to its part.
    GUIDE = """() => { const box = document.getElementById('flowGuide').getBoundingClientRect(); const work = document.getElementById('cadWorkspace').getBoundingClientRect();
        const steps = [...document.querySelectorAll('#cadGuide .flow-step')];
        return {title: document.getElementById('flowGuideTitle').textContent, steps: steps.map(li => li.querySelector('strong').textContent),
                classes: steps.map(li => li.classList.contains('is-done') ? 'done' : li.classList.contains('is-next') ? 'next' : 'todo'),
                here: steps.findIndex(li => li.classList.contains('is-here')) + 1, left: box.right <= work.left + 1, top: Math.round(box.top), height: Math.round(box.height),
                current: document.querySelector('#cadGuide [aria-current=step] strong')?.textContent}; }"""
    guide = page.evaluate(GUIDE)
    check("default: on the page's left the guide 'Design a FlexiTac sensor for your own robot': Load your gripper, Generate the sensor, "
          "Send to manufacture, the first two done and the last one next, step 1 in view",
          guide["title"] == "Design a FlexiTac sensor for your own robot" and guide["left"]
          and guide["steps"] == ["Load your gripper", "Generate the sensor", "Send to manufacture"]
          and guide["classes"] == s["guide"] == ["done", "done", "next"] and guide["current"] == "Send to manufacture" and guide["here"] == 1, (guide, s["guide"]))
    walked = []
    for step, target in ((2, "cadQuick"), (3, "downloadsTitle")):
        page.click(f'#cadGuide .flow-step[data-step="{step}"] button'); page.wait_for_timeout(1200)
        seen = page.evaluate("(id) => Math.round(document.getElementById(id).getBoundingClientRect().top)", target)
        walked.append([step, seen, page.evaluate(GUIDE)])
    check("default: each step of the guide scrolls to its part (the sensor's line under the view, the downloads), lit as it comes in "
          "view (the downloads, at the page's end, in sight), the guide in sight from top to bottom (0 px from the window's top, the window's height)",
          all(here["here"] == step and here["top"] == 0 and here["height"] == 900 and 0 <= seen < (900 if step == 3 else 300) for step, seen, here in walked),
          [(step, seen, here["here"], here["top"], here["height"]) for step, seen, here in walked])
    # The guide's Advanced Customization and the fold on the right are one switch (the user's request of 2026-11-02): either
    # opens both, the guide then showing step 2's own steps, Fit and Generate (each done or next), each scrolling to its part.
    SYNC = """() => [document.getElementById('cadCustomize').open, document.getElementById('guideCustomize').getAttribute('aria-expanded') === 'true',
        [...document.querySelectorAll('#guideSubsteps .flow-substep')].filter(li => li.checkVisibility()).map(li => li.dataset.substep)]"""
    sync = []
    for click in ("#cadCustomize > summary", "#guideCustomize", "#guideCustomize", "#cadCustomize > summary"):
        page.click(click); page.wait_for_timeout(900)
        sync.append(page.evaluate(SYNC))
    s = state(page)
    check("default: the guide's Advanced Customization and the fold on the right open and fold together, from either side; open, "
          "the guide shows Fit and Generate under step 2, both done",
          sync == [[False, False, []], [True, True, ["fit", "generate"]], [False, False, []], [True, True, ["fit", "generate"]]]
          and s["guide_customize"] == {"open": True, "substeps": ["done", "done"]}, (sync, s["guide_customize"]))
    page.click('#guideSubsteps [data-substep="generate"] button'); page.wait_for_timeout(1200)
    seen = page.evaluate("() => [Math.round(document.getElementById('cadStepGenerate').getBoundingClientRect().top), document.querySelector('#guideSubsteps [data-substep=\"generate\"]').classList.contains('is-here')]")
    check("default: the guide's Generate scrolls to its part, lit as it comes in view", 0 <= seen[0] < 300 and seen[1], seen)
    page.evaluate("() => window.scrollTo(0, 0)"); page.wait_for_timeout(300)
    # The camera in the 3D view's window, top right (no row of its own); the steps' titles larger (the user's requests).
    camera = page.evaluate("""() => { const view = document.getElementById('cadView').getBoundingClientRect();
        const buttons = [...document.querySelectorAll('[data-cad-view]')].map(b => b.getBoundingClientRect());
        return {inside: buttons.length === 8 && buttons.every(r => r.top >= view.top && r.bottom <= view.top + 90 && r.right <= view.right && r.left >= view.left + view.width / 2),
                rows: document.querySelectorAll('.cad-toolbar').length, title: parseFloat(getComputedStyle(document.getElementById('cadStepConfig')).fontSize)}; }""")
    check("default: the camera buttons stand in the 3D view's top right (no toolbar row), the steps' titles at least 17 px",
          camera["inside"] and camera["rows"] == 0 and camera["title"] >= 17, camera)
    # Step 2 side by side (the user's request of 2026-10-30; under the fold since 2026-11-02, Advanced Customization since 2026-11-04): the settings,
    # Fit and the proposals left, the flattened map right, in sight while the left scrolls.
    page.evaluate("() => document.getElementById('cadStepConfig').scrollIntoView({block: 'start'})"); page.wait_for_timeout(1200)
    side = page.evaluate("""() => { const main = document.querySelector('.cad-resolution-main').getBoundingClientRect(); const map = document.getElementById('cadFlatFigure').getBoundingClientRect();
        const fit = document.getElementById('cadFit').getBoundingClientRect(); const table = document.getElementById('cadProposalWrap').getBoundingClientRect();
        return {right: map.left >= main.right - 1, settings: fit.right <= main.right && table.right <= main.right + 1, top: Math.round(map.top), height: Math.round(map.height),
                wide: Math.round(map.width)}; }""")
    held = page.evaluate("() => { const style = getComputedStyle(document.getElementById('cadFlatFigure')); return [style.position, style.top]; }")
    check("default: Find best resolution side by side: the settings, Fit and the proposals left, the flattened map right (at least 300 px wide), "
          "sticky (held in sight while a longer left column scrolls)",
          side["right"] and side["settings"] and side["wide"] >= 300 and side["top"] >= 0 and held == ["sticky", "14px"], (side, held))
    columns = page.evaluate("() => getComputedStyle(document.querySelector('.cad-resolution-main .cad-grid')).gridTemplateColumns.split(' ').length")
    notes = page.evaluate("""() => [getComputedStyle(document.getElementById('cadFitNote')).display, document.getElementById('cadFlatCaption').classList.contains('cad-sr-only'),
        Boolean(document.getElementById('cadFitFacts').closest('#cadProposalMore')) && document.getElementById('cadFitFacts').textContent.includes('Inside your border')]""")
    check("default: two settings a row; no fit account under the proposals nor caption under the map (the account under Proposal details, "
          "the caption for screen readers)", columns == 2 and notes == ["none", True, True], (columns, notes))
    size = "() => { const r = document.getElementById('cadFlatFigure').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }"
    first = page.evaluate(size)
    page.click('input[name=cadProposal][value="1"]'); settle(page); page.wait_for_timeout(300)
    second = page.evaluate(size)
    page.click('input[name=cadProposal][value="0"]'); settle(page); page.wait_for_timeout(300)
    check("default: the map's window keeps its size from one proposal to the other (32 x 12, then 12 x 32)", first == second and first[1] >= 400, (first, second))
    # Step 3 side by side (the user's request of 2026-10-30): Generate left, the build on the part and its files right.
    build = page.evaluate("""() => { const gen = document.querySelector('.cad-generate').getBoundingClientRect(); const part = document.querySelector('.cad-build > .cad-verify').getBoundingClientRect();
        const files = [...document.querySelectorAll('.cad-download-actions button')].map(b => b.getBoundingClientRect());
        return {beside: part.left >= gen.right - 1 && Math.abs(part.top - gen.top) < 1, height: Math.round(document.querySelector('.cad-build').getBoundingClientRect().height),
                oneRow: files.every(r => Math.abs(r.top - files[0].top) < 1), button: Math.round(document.getElementById('cadGenerate').getBoundingClientRect().height)}; }""")
    check("default: Click to generate side by side: Generate left (its button on one line), the build on the part and its four files in a row right, "
          "under 230 px tall", build["beside"] and build["oneRow"] and build["button"] < 60 and build["height"] < 230, build)
    page.evaluate("() => document.getElementById('cadStepConfig').scrollIntoView({block: 'start'})"); page.wait_for_timeout(300)
    # While a fit runs the map's window keeps its place and size, empty, saying so (the user's request of 2026-11-02: it
    # used to vanish, the settings widening and narrowing again).
    page.evaluate("""() => { window.__boxes = []; window.__stop = false; const tick = () => {
        const f = document.getElementById('cadFlatFigure'); const r = f.getBoundingClientRect(); const m = document.querySelector('.cad-resolution-main').getBoundingClientRect();
        window.__boxes.push([Math.round(r.width), Math.round(r.height), Math.round(m.width), f.className, document.getElementById('cadFlatEmpty').textContent]);
        if (!window.__stop) requestAnimationFrame(tick); }; tick(); }""")
    page.fill("#cadPitch", "1.5"); page.click("#cadFit"); page.wait_for_timeout(200); settle(page, 180); page.wait_for_timeout(300)
    boxes = page.evaluate("() => { window.__stop = true; return window.__boxes; }")
    sizes = sorted({tuple(box[:3]) for box in boxes})
    fitting = any("is-fitting" in box[3] and box[4] == "Fitting the sensor…" for box in boxes)
    check("default: while a fit runs the map's window keeps its place and size (and the settings theirs), empty, saying "
          "\"Fitting the sensor…\"; the map drawn in it again after", len(sizes) == 1 and fitting and "is-empty" not in boxes[-1][3],
          (sizes, fitting, boxes[-1][3:]))
    page.fill("#cadPitch", "2.0")
    page.evaluate("() => window.scrollTo(0, 0)"); page.wait_for_timeout(300)
    base = page.evaluate("""() => { const view = document.getElementById('cadView').getBoundingClientRect();
        const pills = [...document.querySelectorAll('#cadSides .cad-side')].map(label => label.getBoundingClientRect());
        return {below: pills.every(r => r.top >= view.bottom), left: pills.every(r => r.left >= view.left && r.right <= view.right),
                across: pills.some((r, k) => k > 0 && Math.abs((r.top + r.bottom) - (pills[k - 1].top + pills[k - 1].bottom)) < 3 && r.left > pills[k - 1].right),
                count: pills.length}; }""")
    check("default: the base edge's choices lie under the 3D view, across it (Auto and the sides as pills, side by side where they fit)",
          base["below"] and base["left"] and base["across"] and base["count"] == 5, base)
    # The page never says "CAD" (the user's request of 2026-10-30): its text in sight, the tab, tooltips and labels.
    words = page.evaluate(NO_CAD)
    check("default: the page never says CAD (its text in sight, the tab, tooltips and labels)", words == [], [word[:200] for word in words])
    page.click("#modeRect"); page.wait_for_timeout(200)
    page.reload(); wait_until(page, DONE, 60); page.wait_for_timeout(300)
    kept = page.evaluate("() => [document.body.dataset.mode, location.hash, document.getElementById('cadWorkspace').hidden]")
    check("default: Rectangular is #rect and is kept across a reload", kept == ["rect", "#rect", True], kept)
    check("default part: no console errors", not errors_of(page), errors_of(page))
    page.close()
    if SOFT.exists():
        page = new_page(browser)
        page.held = []
        page.route(DEFAULT_PART, lambda route: page.held.append(route))
        page.goto(URL)
        wait_until(page, DONE, 60)
        end = time.monotonic() + 30
        while not page.held and time.monotonic() < end:
            page.wait_for_timeout(40)
        veil = page.evaluate(STATUS_PLACE)
        check("default: while the default part is on its way the 3D view shows \"Loading UMI-Soft-Gripper-Finger.stl…\" over it "
              "(the drop zone hidden, no status)", veil["veil"] and veil["veilText"] == "Loading UMI-Soft-Gripper-Finger.stl…"
              and not page.is_visible("#cadDrop") and veil["text"] is None, veil)
        load(page, SOFT)
        page.held[0].continue_()
        wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).default_part === 'skipped'", 30)
        page.wait_for_timeout(300)
        s = state(page)
        check("default: a file chosen before the default part arrives is kept (the default part and its sensor dropped)",
              s["mesh"]["name"] == SOFT.name and s["status"]["shown"] == f"{SOFT.name} loaded" and s["loading"] is None and s["default_build"] == "stopped"
              and s["selection"] is None and len(page.generate) == 1, (s["mesh"], s["status"], s["loading"], s["default_build"], len(page.generate)))
        check("default part (a file first): no console errors", not errors_of(page), errors_of(page))
        page.close()


def part_soft(browser):
    if not SOFT.exists():
        print("SKIP soft finger: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    check("soft: WebGL renderer created", state(page)["webgl"] == "ok", state(page)["webgl"])
    page.screenshot(path=f"{SHOTS}/cad_empty_1440.png")
    load(page, SOFT)
    s = state(page)
    check("soft: inspect gives 1944 facets in m, browser parse agrees", s["mesh"]["facets"] == 1944 and s["mesh"]["browser_facets"] == 1944 and s["mesh"]["unit"] == "m", s["mesh"])
    facts = page.inner_text("#cadMeshFacts")
    check("soft: mesh facts list unit, extent, facets, watertight, hidden facets",
          all(word in facts for word in ("m (guessed)", "40.0 × 25.8 × 123.4 mm", "1,944", "Watertight", "Hidden facets")), facts)
    candidate(page, 1)
    s = state(page)
    check("soft: candidate #1 selects the 3087.7 mm2 planar face (34 facets)",
          s["selection"] and abs(s["selection"]["area_mm2"] - 3087.7) < 0.05 and s["selection"]["kind"] == "planar" and s["selection"]["facets"] == 34, s["selection"])
    # The tools in the 3D view's window, on its left, larger than before (the user's requests of 2026-10-30): Select a
    # surface, Base edge, Edit border, Undo and Clear in a column over the view, Remove model under them (2026-10-31); no
    # Add / Subtract switch, no Disk tool, no Clean up and no candidate list.
    tools = page.evaluate("""() => { const view = document.getElementById('cadView').getBoundingClientRect();
        return [...document.querySelectorAll('#cadViewTools label span, #cadViewTools button')].map(node => { const r = node.getBoundingClientRect();
          return [node.textContent.trim(), Math.round(r.left - view.left), Math.round(r.top - view.top), Math.round(r.height),
                  r.right <= view.left + view.width / 3 && r.bottom <= view.bottom]; }); }""")
    check("soft: Select a surface, Base edge, Edit border, Undo, Clear and Remove model stand in a column on the 3D view's left, "
          "at least 32 px tall (no Disk, no Clean up, no candidate list)",
          [name for name, *_ in tools] == ["Select a surface", "Base edge", "Edit border", "Undo", "Clear", "Remove model"]
          and page.locator("#cadDiskRadius, #cadCleanup, #cadCandidates, #cadCandidateKind").count() == 0
          and all(0 <= left < 30 and inside and height >= 32 for _, left, _, height, inside in tools)
          and [top for _, _, top, _, _ in tools] == sorted(top for _, _, top, _, _ in tools) and page.locator("#cadOpMode").count() == 0, tools)
    # Clear, then click the middle of the view (the camera looks at the face): a click selects the surface under it, a
    # click on a selected surface deselects it (the operation that added it removed: no refused request).
    page.click("#cadClear"); settle(page)
    check("soft: Clear empties the selection", state(page)["selection"] is None and state(page)["ops"] == 0, state(page))
    x, y = view_center(page)
    # The default grow preset is Surface (the user's request of 2026-11-02): the face without its fillet strips (the
    # blends under 4 mm radius); the flat preset takes the strips the candidate has.
    preset = page.input_value("#cadPreset")
    page.mouse.click(x, y); settle(page)
    s = state(page)
    check("soft: with the default preset (Surface) a click selects the face without its fillet strips (3079.6 mm2, 32 facets)",
          preset == "surface" and s["selection"] and round(s["selection"]["area_mm2"], 1) == 3079.6 and s["selection"]["facets"] == 32 and s["ops"] == 1,
          (preset, s["selection"]))
    page.click("#cadClear"); settle(page)
    page.select_option("#cadPreset", "flat"); page.wait_for_timeout(100)
    page.mouse.click(x, y); settle(page)
    s = state(page)
    check("soft: a click on the face selects the same 3087.7 mm2 face (flat preset)",
          s["selection"] and abs(s["selection"]["area_mm2"] - 3087.7) < 0.05 and s["ops"] == 1, s["selection"])
    refused = len(errors_of(page))
    page.mouse.click(x, y); settle(page)
    s = state(page)
    check("soft: a second click on the selected face deselects it (the selection empty, no error, no refused request)",
          s["selection"] is None and s["ops"] == 0 and s["error"] is None and len(errors_of(page)) == refused, (s["selection"], s["ops"], s["error"], errors_of(page)))
    page.click("#cadUndo"); settle(page)
    s = state(page)
    check("soft: Undo brings the deselected face back", s["selection"] and abs(s["selection"]["area_mm2"] - 3087.7) < 0.05 and s["ops"] == 1 and s["error"] is None, s)
    candidate(page, 1)
    check("soft: a click on a selected candidate removes it as well", state(page)["selection"] is None and state(page)["ops"] == 0, state(page)["selection"])
    candidate(page, 1)
    check("soft: and a click on it again selects it", state(page)["selection"] and abs(state(page)["selection"]["area_mm2"] - 3087.7) < 0.05, state(page)["selection"])
    page.click('#cadTools label:has(input[value="edge"])'); page.click('#cadTools label:has(input[value="grow"])'); settle(page)
    check("soft: clicks on the tools over the view select nothing on the part", state(page)["ops"] == 1, state(page)["ops"])
    sides = page.evaluate("() => [...document.querySelectorAll('input[name=cadSide]')].map(i => i.value)")
    # Ranked by length since the border editor (docs/CAD_BORDER.md): Auto first, then the longest side (1, the mount end's).
    check("soft: the side list holds Auto and the 4 sides, longest first (and no stray text)", sides == ["auto", "1", "3", "0", "2"] and "null" not in page.inner_text("#cadSides"), sides)
    # The Base edge tool: click the projected middle of side 1 on the model.
    page.click('#cadTools label:has(input[value="edge"])')
    page.click('[data-cad-view="selection"]')
    page.wait_for_timeout(200)
    ends = side_ends(page)
    middle = [(a + b) / 2 for a, b in zip(*ends[1])]
    screen = probe(page, middle)
    if screen:
        page.mouse.click(screen[0], screen[1])
        page.wait_for_timeout(150)
    check("soft: the Base edge tool picks side 1 on the model", state(page)["side"] == 1, (screen, state(page)["side"]))
    page.click('#cadTools label:has(input[value="grow"])')
    page.check('input[name=cadSide][value="0"]')
    page.wait_for_timeout(100)
    check("soft: side 0 chosen from the list", state(page)["side"] == 0, state(page)["side"])
    page.click("#cadFit"); settle(page)
    s = state(page)
    check("soft: fit on side 0 gives proposals, #1 chosen", s["proposals"] >= 1 and s["proposal"] and s["proposal"]["rank"] == 1 and s["proposal"]["base_side"] == 0, s)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    s = state(page)
    rows, columns, taxels = s["proposal"]["rows"], s["proposal"]["columns"], s["proposal"]["taxels"]
    check("soft: the proposal preview maps the proposal's taxels onto the part", s["preview_taxels"] == taxels and s["overlay"]["source"] == "proposal", s)
    table = page.evaluate("() => [...document.querySelectorAll('#cadProposals tbody tr')].length")
    check("soft: the proposals table lists every proposal", table == s["proposals"], table)
    flat = page.evaluate("() => { const svg = document.getElementById('cadFlat'); return [svg.hasAttribute('aria-label'), svg.querySelectorAll('polygon').length, svg.querySelectorAll('circle').length, document.querySelectorAll('svg[aria-label]').length]; }")
    check("soft: flat preview SVG (no aria-label) with outlines and taxels; still six labelled SVGs",
          flat[0] is False and flat[1] >= 4 and flat[2] == taxels and flat[3] == 6, flat)
    page.screenshot(path=f"{SHOTS}/cad_soft_fit_1440.png", full_page=False)
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_soft_workspace_1440.png")
    before = len(page.generate)
    # Two clicks in a row (the second while the first is pending) submit one build.
    page.evaluate("() => { const button = document.getElementById('cadGenerate'); button.click(); button.click(); }")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.pending_build === null && (s.verification !== null || s.map_error !== null); }", 120)
    page.wait_for_timeout(300)
    s = state(page)
    sent, result = page.generate[-1] if len(page.generate) > before else (None, {})
    check("soft: Generate (clicked twice) runs /api/generate exactly once through the form", len(page.generate) == before + 1, len(page.generate) - before)
    check("soft: the generated build is the proposal's build (every field written)",
          result.get("manifest", {}).get("build_id") == s["proposal"]["build_id"] == s["generated_build_id"], (result.get("manifest", {}).get("build_id"), s["proposal"]))
    check("soft: the build passes every DRC check", result.get("ok") is True and all(board["verification"]["all_checks_passed"] for board in result.get("boards", {}).values()),
          result.get("validation", {}).get("errors"))
    check("soft: the form shows the proposal (rows, columns, tails bottom) and the request carries its template",
          sent and sent["rows"] == rows and sent["columns"] == columns and sent["connector_side"] == "bottom"
          and sent["template_id"] == result.get("design", {}).get("template_id") == "surface_matrix_v1", sent)
    check("soft: map overlay has the proposal's taxels and every verification record passes",
          s["overlay"] and s["overlay"]["source"] == "build" and s["overlay"]["taxels"] == taxels and s["verification"]["ok"]
          and s["verification"]["passed"] == s["verification"]["total"] > 0, s)
    check("soft: the verification table shows all checks passing", "checks pass" in page.inner_text("#cadVerify") and not page.query_selector("#cadVerifyTable tr.is-fail"),
          page.inner_text("#cadVerify")[:200])
    check("soft: the stack note gives the contact offset in mm (no raw key)", "contact_offset_mm" not in page.inner_text("#cadVerify")
          and " mm further out" in page.inner_text("#cadVerify"), page.inner_text("#cadVerify")[-200:])
    badge = page.inner_text("#profileBadge")
    check("soft: the badge names the build's template (surface profile, or its id when the server does not send it)",
          ("surface" in badge.lower()) and (SERVED is False or "jlc-fpc-surface" in badge), badge)
    page.screenshot(path=f"{SHOTS}/cad_soft_generated_1440.png", full_page=False)
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_soft_generated_workspace_1440.png")
    build = s["generated_build_id"]
    saved = {}
    for selector in ("#cadSavePlacement", "#cadSaveMap", "#cadSaveCsv", "#cadSaveWrap"):
        name, data = save(page, selector)
        saved[selector] = (name, data)
    names = [name for name, _ in saved.values()]
    check("soft: four downloads named by the build id", names == [f"{build}-surface-placement.json", f"{build}-taxel-map.json", f"{build}-taxel-map.csv", f"{build}-wrap-template.svg"], names)
    check("soft: downloads are non-empty", all(len(data) > 100 for _, data in saved.values()), [len(data) for _, data in saved.values()])
    placement = json.loads(saved["#cadSavePlacement"][1])
    taxel_map = json.loads(saved["#cadSaveMap"][1])
    rows_csv = list(csv.reader(saved["#cadSaveCsv"][1].decode().splitlines()))
    check("soft: placement JSON is the sidecar document of the proposal", placement.get("format") == "tactile-surface-placement/v1" and placement.get("build_id") == build, placement.get("format"))
    check("soft: taxel map JSON has the build id and the proposal's taxels", taxel_map.get("format") == "tactile-taxel-map/v1" and len(taxel_map.get("taxels", [])) == taxels and "wrap_svg" not in taxel_map, taxel_map.get("format"))
    check("soft: taxel CSV header and one line per taxel", rows_csv[0][:13] == ["row", "column", "row_net", "column_net", "row_pin", "column_pin", "x", "y", "z", "nx", "ny", "nz", "facet"]
          and len(rows_csv) == taxels + 1, rows_csv[0])
    check("soft: wrap template is an SVG", saved["#cadSaveWrap"][1].startswith(b"<svg"), saved["#cadSaveWrap"][1][:40])
    # The shared Downloads row serves CAD mode too: the mapped build's EasyEDA Pro projects.
    ready = not page.is_disabled('[data-export="easyeda-pro"]')
    name, data = save(page, '[data-export="easyeda-pro"]') if ready else ("", b"")
    members = zipfile.ZipFile(io.BytesIO(data)).namelist() if data else []
    check("soft: the build's EasyEDA Pro projects ZIP downloads in CAD mode (two .epro2 and README_EASYEDA.txt, named by the build id)",
          ready and name == f"{build}-easyeda-pro.zip" and len([member for member in members if member.endswith(".epro2")]) == 2
          and "easyeda_pro/README_EASYEDA.txt" in members, (ready, name, members))
    # Stale: an edited form greys the overlay and disables the CAD downloads.
    page.fill("#rows", str(rows - 1))
    page.wait_for_timeout(200)
    s = state(page)
    disabled = page.evaluate("() => ['cadSavePlacement', 'cadSaveMap', 'cadSaveCsv', 'cadSaveWrap'].map(id => document.getElementById(id).disabled)")
    check("soft: editing the form marks CAD stale and disables its downloads", s["stale"] and not s["downloads"] and all(disabled)
          and page.evaluate("() => document.getElementById('cadVerify').classList.contains('is-stale')"), (s["stale"], disabled))
    page.click("#regenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.map_error !== null; }", 120)
    s = state(page)
    check("soft: a changed design reports E_SURFACE_PLACEMENT_MISMATCH: fit again", s["map_error"] == "E_SURFACE_PLACEMENT_MISMATCH"
          and "fit again" in page.inner_text("#cadStatus") and "fit again" in page.inner_text("#cadVerify"), (s["map_error"], page.inner_text("#cadStatus")))
    page.click("#cadGenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.verification !== null; }", 120)
    s = state(page)
    check("soft: Generate again restores the mapped, verified build", s["verification"]["ok"] and s["downloads"] and s["generated_build_id"] == build, s)
    # 422s on purpose: the empty selection (Subtract) and the placement mismatch.
    check("soft part: no unexpected console errors", not errors_of(page, allowed=("status of 422",)), errors_of(page, allowed=("status of 422",)))
    page.close()


def side_ends(page):
    """[from_xyz, to_xyz] of each listed side of the selection by side index (data attributes of the side radios; the list
    is ranked by length, so the radios are sorted by value: ends[k] is side k)."""
    return page.evaluate("""() => [...document.querySelectorAll('input[name=cadSide]')].filter(i => /^\\d+$/.test(i.value))
        .sort((a, b) => Number(a.value) - Number(b.value))
        .map(i => [i.dataset.from.split(',').map(Number), i.dataset.to.split(',').map(Number)])""")


def part_crank(browser):
    if not CRANK.exists():
        print("SKIP crank: asset/crank_gripper/tip_left.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, CRANK)
    s = state(page)
    check("crank: inspect agrees with the browser parse", s["mesh"]["facets"] == s["mesh"]["browser_facets"] > 0, s["mesh"])
    candidate(page, 1)
    s = state(page)
    check("crank: candidate #1 is the 2957.3 mm2 developable pad", s["selection"] and abs(s["selection"]["area_mm2"] - 2957.3) < 0.05 and s["selection"]["kind"] == "developable", s["selection"])
    check("crank: base edge auto", s["side"] == "auto", s["side"])
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    s = state(page)
    check("crank: fit gives proposals and previews #1 on the part", s["proposals"] >= 1 and s["preview_taxels"] == s["proposal"]["taxels"], s)
    check("crank: the default is Containment Field only (no Field shape); #1 is a masked field of 688 taxels, the tip-first field "
          "(696 before section 26; 549 whole board)",
          page.locator("#cadShape").count() == 0 and page.input_value("#cadContainment") == "field" and s["proposal"]["masked"]
          and s["proposal"]["taxels"] == 688 and s["proposal"]["containment"] == "field", s["proposal"])
    check("crank: with the automatic exit the narrow tip wins (the 70 mm leg, side 6: a 13.9 mm tip, not the cut corner's)",
          s["proposal"]["base_side"] == 6 and s["proposal"]["tip_mm"] < 20.0, (s["proposal"]["base_side"], s["proposal"]["tip_mm"]))
    page.screenshot(path=f"{SHOTS}/cad_crank_fit_1440.png")
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_crank_workspace_1440.png")
    page.select_option("#cadContainment", "board")
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    s = state(page)
    check("crank: Containment Whole board proposes the masked field of 549 taxels of phase P4", s["proposal"]["masked"] and s["proposal"]["taxels"] == 549
          and s["proposal"]["containment"] == "board", s["proposal"])
    check("crank part: no console errors", not errors_of(page), errors_of(page))
    page.close()


def part_crank_fill(browser):
    """The crank pad's masked field: a masked proposal through Generate, the map and the downloads."""
    if not CRANK.exists():
        print("SKIP crank fill: asset/crank_gripper/tip_left.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, CRANK)
    candidate(page, 1)
    check("crank fill: no Field shape select (the field follows the selected area: masked fields too)", page.locator("#cadShape").count() == 0, "")
    # The straight channel's masked field (phase P4): the whole board on the pad, so a trace edit can leave a mask it
    # cannot route (the diagonal Row bus of Field only routes every mask).
    page.select_option("#cadContainment", "board")
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 60)
    s = state(page)
    proposal = s["proposal"]
    rows, columns, taxels = proposal["rows"], proposal["columns"], proposal["taxels"]
    check("crank fill: #1 is a masked field (fewer taxels than positions, a field polygon of more than 4 points)",
          proposal["masked"] and taxels < proposal["positions"] == rows * columns and proposal["field_points"] > 4, proposal)
    check("crank fill: more taxels than the rectangular fit's 306", taxels > 306, taxels)
    cell = page.inner_text("#cadProposals tbody tr:first-child td[data-taxels]")
    check("crank fill: the proposals table shows 'N of R x C'", cell == f"{taxels} of {rows} × {columns}", cell)
    check("crank fill: the preview maps the proposal's taxels (only the active crossings)", s["preview_taxels"] == taxels and s["overlay"]["taxels"] == taxels, s)
    caption = page.inner_text("#cadFlatCaption")
    check("crank fill: the flat view's caption gives N of R x C positions and the sampled share", f"{taxels} of {rows} × {columns} positions" in caption and "% sampled" in caption, caption)
    flat = page.evaluate("() => document.querySelector('#cadFlat polygon.flat-field').getAttribute('points').trim().split(/\\s+/).length")
    check("crank fill: the flat view draws the field polygon (not its bounding rectangle)", flat > 4, flat)
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_crank_fill_1440.png")
    before = len(page.generate)
    s = generate_and_wait(page)
    sent, result = page.generate[-1] if len(page.generate) > before else (None, {})
    mask = (sent or {}).get("matrix", {}).get("mask")
    check("crank fill: Generate sends the proposal's mask with the form (matrix.mask) and builds the proposal's build id",
          mask is not None and len(mask) == rows and result.get("manifest", {}).get("build_id") == proposal["build_id"] == s["generated_build_id"], (bool(mask), result.get("manifest", {}).get("build_id"), proposal["build_id"]))
    check("crank fill: the build passes every DRC check", result.get("ok") is True and all(board["verification"]["all_checks_passed"] for board in result.get("boards", {}).values()),
          result.get("validation", {}).get("errors"))
    check("crank fill: the map overlay has the N taxels and every record passes", s["overlay"] and s["overlay"]["source"] == "build" and s["overlay"]["taxels"] == taxels
          and s["verification"]["ok"] and s["verification"]["passed"] == s["verification"]["total"] > 0, s)
    badge = page.inner_text("#maskBadge") if page.query_selector("#maskBadge") else ""
    check("crank fill: the summary badge reads 'N of R x C taxels active'", badge.startswith(f"{taxels} of {rows} × {columns} taxels active"), badge)
    check("crank fill: the form's note names the masked field", not page.evaluate("() => document.getElementById('maskNote').hidden")
          and f"{taxels} of {rows} × {columns}" in page.inner_text("#maskNote"), page.inner_text("#maskNote"))
    _, data = save(page, "#cadSaveMap")
    taxel_map = json.loads(data)
    check("crank fill: the taxel map JSON carries the readout", taxel_map.get("readout", {}).get("positions") == rows * columns
          and taxel_map["readout"]["active"] == taxels == len(taxel_map["taxels"]), taxel_map.get("readout"))
    _, data = save(page, "#cadSaveCsv")
    lines = list(csv.reader(data.decode().splitlines()))
    active = [line for line in lines[1:] if line[-1] == "1"]
    check("crank fill: the taxel CSV lists every readout position with its active flag", lines[0][-1] == "active" and len(lines) == rows * columns + 1
          and len(active) == taxels, (lines[0], len(lines), len(active)))
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_crank_fill_generated_1440.png")
    # A rows edit clears the mask (it would no longer match): the note says so and the build mismatches the placement.
    page.fill("#rows", str(rows - 1))
    page.wait_for_timeout(200)
    check("crank fill: a rows edit clears the masked field with a note", "Masked field from Gen by Surface cleared" in page.inner_text("#maskNote"), page.inner_text("#maskNote"))
    before = len(page.generate)
    page.click("#regenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.map_error !== null; }", 120)
    sent = page.generate[-1][0] if len(page.generate) > before else {}
    check("crank fill: the regenerated form carries no mask and is a placement mismatch", "matrix" not in sent and state(page)["map_error"] == "E_SURFACE_PLACEMENT_MISMATCH",
          (sorted(sent), state(page)["map_error"]))
    s = generate_and_wait(page)
    check("crank fill: Generate again restores the masked build and its verification", s["generated_build_id"] == proposal["build_id"] and s["verification"]["ok"], s)
    # CAD -> Rectangular -> CAD (review: the round trip dropped the mask): the form still builds the proposal.
    page.click("#modeRect")
    wait_until(page, "() => !document.getElementById('staleBanner').hidden", 10)
    check("crank fill: in Rectangular mode the note keeps the masked field for Gen by Surface (CAD mode)", "kept for Gen by Surface" in page.inner_text("#maskNote"), page.inner_text("#maskNote"))
    page.click("#modeCad")
    wait_until(page, "() => document.getElementById('staleBanner').hidden", 10)
    settle(page)
    s = state(page)
    check("crank fill: back in CAD mode the mask is still in the form: not stale, the downloads ready, the note names it",
          s["downloads"] and not s["stale"] and s["generated_build_id"] == proposal["build_id"] and f"{taxels} of {rows} × {columns}" in page.inner_text("#maskNote")
          and page.evaluate("() => document.getElementById('clearMask').hidden === false"), (s, page.inner_text("#maskNote")))
    # A trace edit the mask no longer fits (review: blocked with nothing marked and no way to drop the mask).
    page.fill("#traceWidth", MASK_BREAKING_TRACE)
    page.fill("#traceSpace", MASK_BREAKING_TRACE)
    before = len(page.generate)
    with page.expect_response(lambda response: response.url.endswith("/api/generate") and response.request.method == "POST", timeout=120_000):
        page.click("#regenerate")
    wait_until(page, "() => !document.getElementById('generate').disabled", 30)
    page.wait_for_timeout(300)
    sent, result = page.generate[-1] if len(page.generate) > before else ({}, {})
    codes = [issue["code"] for issue in result.get("validation", {}).get("errors", [])]
    check("crank fill: a trace edit the mask cannot take is blocked with E_MASK_ROUTING (the mask was sent)",
          "matrix" in sent and result.get("ok") is False and "E_MASK_ROUTING" in codes, (sorted(sent), codes))
    note = page.inner_text("#maskNote")
    check("crank fill: the mask's note lists the issue, is marked and offers the full field",
          "E_MASK_ROUTING" in page.inner_text("#maskIssues") and page.evaluate("() => document.getElementById('maskNote').classList.contains('is-invalid')")
          and page.is_visible("#clearMask"), note)
    status = page.inner_text("#status")
    check("crank fill: the status names the masked field and how to go on", "masked field from Gen by Surface does not fit" in status and "full field" in status, status)
    page.locator("#maskNote").screenshot(path=f"{SHOTS}/cad_mask_routing_note.png")
    page.click("#clearMask")
    page.wait_for_timeout(200)
    check("crank fill: Use the full field clears the mask with a note", "Masked field from Gen by Surface cleared" in page.inner_text("#maskNote")
          and page.evaluate("() => document.getElementById('clearMask').hidden"), page.inner_text("#maskNote"))
    before = len(page.generate)
    page.click("#regenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.map_error !== null; }", 120)
    sent, result = page.generate[-1] if len(page.generate) > before else ({}, {})
    check("crank fill: the full field generates (no mask sent) and is a placement mismatch", "matrix" not in sent and result.get("ok") is True
          and state(page)["map_error"] == "E_SURFACE_PLACEMENT_MISMATCH", (sorted(sent), result.get("ok"), state(page)["map_error"]))
    s = generate_and_wait(page)
    check("crank fill: CAD Generate brings the proposal's mask back", s["generated_build_id"] == proposal["build_id"] and s["verification"]["ok"]
          and f"{taxels} of {rows} × {columns}" in page.inner_text("#maskNote"), s)
    check("crank fill part: no unexpected console errors", not errors_of(page, allowed=("status of 422",)), errors_of(page, allowed=("status of 422",)))
    page.close()


def part_no_rectangle_controls(browser):
    """No Field shape, no Board rules, no Largest rectangle (P5-diagonal-bus.md section 26.16): the fit names none of them."""
    if not SOFT.exists():
        print("SKIP no rectangle controls: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, SOFT)
    candidate(page, 1)
    check("no rectangle controls: neither Field shape nor Board rules in Configure, nor Largest rectangle in the border editor",
          all(page.locator(f"#{name}").count() == 0 for name in ("cadShape", "cadTemplate", "cadBorderRect"))
          and "Largest rectangle" not in page.inner_text("#cadWorkspace") and "Board rules" not in page.inner_text("#cadConfig"),
          [name for name in ("cadShape", "cadTemplate", "cadBorderRect") if page.locator(f"#{name}").count()])
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.preview_taxels !== null || s.error !== null; }", 60)
    s = state(page)
    options = s["fit_options"] or {}
    check("no rectangle controls: the fit names none of shape, template or rectangle_preference_pct; Containment Field only and Row traces both, enabled",
          not {"shape", "template", "rectangle_preference_pct"} & set(options) and options.get("containment") == "field" and options.get("row_sides") == "both"
          and not page.is_disabled("#cadContainment") and not page.is_disabled("#cadRowSides"), options)
    check("no rectangle controls: the fit proposes the selected area's field (no error)", s["error"] is None and s["proposals"] >= 1
          and s["proposal"]["template_id"] == "surface_matrix_v1", (s["error"], s["proposal"]))
    page.click("#cadEditBorder")
    page.wait_for_timeout(200)
    check("no rectangle controls: the border bar holds Surface outline and Inset, not Largest rectangle",
          page.is_visible("#cadBorderReset") and page.is_visible("#cadBorderInset") and page.locator("#cadBorderBar button", has_text="Largest").count() == 0,
          page.inner_text("#cadBorderBar"))
    check("no rectangle controls part: no console errors", not errors_of(page), errors_of(page))
    page.close()


def flat_tip(page, height):
    """The Row board's width in the flat view at ROW_01's centre: P's top less half the row electrode (the boards' frame, mm)."""
    return page.evaluate("""height => {
        const parse = node => node.getAttribute('points').trim().split(/\\s+/).map(p => p.split(',').map(Number)).map(([x, y]) => [x, -y]);
        const field = parse(document.querySelector('#cadFlat polygon.flat-field'));
        const row = parse(document.querySelector('#cadFlat polygon.flat-row:not(.is-off)'));
        const y = Math.max(...field.map(p => p[1])) - height / 2;
        const xs = [];
        row.forEach((a, i) => {
            const b = row[(i + 1) % row.length];
            if (a[1] === b[1]) { if (a[1] === y) xs.push(a[0], b[0]); return; }
            if (Math.min(a[1], b[1]) <= y && y <= Math.max(a[1], b[1])) xs.push(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]));
        });
        return xs.length ? Math.max(...xs) - Math.min(...xs) : null;
    }""", height)


def flat_tail_ends(page):
    """How far each board's lowest point lies past the base edge in the flat view (the boards' frame, mm): measured on
    the drawn outlines, independent of the fit's tail_reach_mm."""
    return page.evaluate("""() => {
        const parse = node => node.getAttribute('points').trim().split(/\\s+/).map(p => p.split(',').map(Number)).map(([x, y]) => [x, -y]);
        const base = document.querySelector('#cadFlat line.flat-base');
        if (!base) return null;
        const [ax, ay, bx, by] = ['x1', 'y1', 'x2', 'y2'].map(key => Number(base.getAttribute(key))).map((v, i) => (i % 2 ? -v : v));
        const length = Math.hypot(bx - ax, by - ay);
        const side = ([x, y]) => ((bx - ax) * (ay - y) - (by - ay) * (ax - x)) / length;
        // The side of the base line away from the field is positive.
        const field = parse(document.querySelector('#cadFlat polygon.flat-field'));
        const sign = field.reduce((sum, point) => sum + side(point), 0) > 0 ? -1 : 1;
        const past = point => sign * side(point);
        const out = {};
        for (const key of ['row', 'column']) {
            const node = document.querySelector(`#cadFlat polygon.flat-${key}.is-off`);
            out[key] = node ? Math.max(...parse(node).map(past)) : null;
        }
        return out;
    }""")


def part_field_soft(browser):
    """Field-only containment on the soft finger (P5e): many more taxels than the whole board, the Row bus's tip and
    bands on the proposal, the parts off the surface dotted, Generate with routing.row_sides, every map record passing."""
    if not SOFT.exists():
        print("SKIP field soft: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, SOFT)
    candidate(page, 1)
    page.check('input[name=cadSide][value="0"]')
    check("field soft: Containment starts at Field only (the server's default) with Row traces Both",
          page.input_value("#cadContainment") == "field" and page.input_value("#cadRowSides") == "both" and not page.is_disabled("#cadRowSides"),
          (page.input_value("#cadContainment"), page.input_value("#cadRowSides")))
    page.select_option("#cadContainment", "board")
    page.wait_for_timeout(100)
    check("field soft: Whole board disables Row traces (board containment ignores them)", page.is_disabled("#cadRowSides"), page.is_disabled("#cadRowSides"))
    page.click("#cadFit"); settle(page)
    s = state(page)
    board = s["proposal"]["taxels"] if s["proposal"] else 0
    check("field soft: Whole board fits the masked 50 x 12 (470) across side 0 (the 45 x 8 rectangle, 360, before section 21)",
          s["proposal"] and s["proposal"]["containment"] == "board" and s["proposal"]["masked"]
          and (s["proposal"]["rows"], s["proposal"]["columns"], board) == (50, 12, 470) and s["fit_options"].get("containment") == "board", s["proposal"])
    check("field soft: a whole-board proposal's card says so and shows no Row bus", "whole board" in page.inner_text("#cadProposalCard")
          and "straight Row channel" in page.inner_text("#cadProposalCard"), page.inner_text("#cadProposalCard"))
    page.select_option("#cadContainment", "field")
    page.wait_for_timeout(100)
    check("field soft: Field only enables Row traces (Both) and says that only the taxel field stays on the surface",
          not page.is_disabled("#cadRowSides") and page.input_value("#cadRowSides") == "both" and "Only the taxel field" in page.inner_text("#cadConfigHint"),
          page.inner_text("#cadConfigHint"))
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    s = state(page)
    proposal = s["proposal"]
    rows, taxels = proposal["rows"], proposal["taxels"]
    check("field soft: Field only proposes at least 700 taxels (708, 59 x 12), 1.5 times the whole board's (1.9 times its rectangle before section 21)",
          proposal["containment"] == "field" and taxels >= 700
          and taxels >= 1.5 * board and s["fit_options"]["containment"] == "field" and s["fit_options"]["row_sides"] == "both", (proposal, board))
    check("field soft: the proposal is a diagonal Row bus on both sides", proposal["row_sides"] == "both" and proposal["tip_mm"] and proposal["on_surface"], proposal)
    card = page.inner_text("#cadProposalCard")
    check("field soft: the face is symmetric about its base edge's axis and so is the field, centred on it; the card says so (P5 section 22)",
          (proposal["symmetry"] or {}).get("face") is True and proposal["symmetry"].get("field") is True and proposal["symmetry"].get("field_offset_mm") == 0
          and "so is every row of the field" in card, (proposal["symmetry"], card))
    tip = proposal["tip_mm"]
    check("field soft: the card shows the tip, the bands, each board's share on the surface and the overhang",
          f"{tip:.2f} mm wide at ROW_01" in card and f"{proposal['band_mm']['near']:.2f} mm on ROW_01's side" in card
          and f"Row FPC {100 * proposal['on_surface']['row']:.0f} %" in card and f"Column FPC {100 * proposal['on_surface']['column']:.0f} %" in card
          and "Overhang" in card and "past the base edge" in card and "folded, pin 1 first: ROW_01, ROW_03" in card and "both end" in card, card)
    overhang = proposal["overhang"]["row"]
    column = proposal["overhang"]["column"]
    check("field soft: the overhang beside the surface is the Row bands' (about 6-8 mm), the Column FPC's the same (one outline "
          "over the field since diagonal-bus/4; none with diagonal-bus/3), not the tails' (46 mm before the fix); past the base edge "
          "both FPCs reach as far (one outline down to the tail roots, diagonal-bus/8)",
          0 < overhang["left"] < 10 and 0 < overhang["right"] < 10 and abs(column["left"] - overhang["left"]) < 0.01
          and abs(column["right"] - overhang["right"]) < 0.01 and 0 < column["exit"] and abs(column["exit"] - overhang["exit"]) < 0.01, proposal["overhang"])
    check("field soft: the card gives its figures to its own precision, two decimals at most (the field's clearance 0.028157 mm, "
          "0.278157 before section 26.18 put the 708 0.25 mm nearer its tip, printed so before P5-diagonal-bus.md section 27.5)",
          "the taxel field on the surface (0.03 mm clear)" in card and re.findall(r"\d\.\d{3,}", card) == [], card)
    shared = proposal["shared_outline_mm"]
    check("field soft: the card says both FPCs share one outline down to their tail roots, so they align by their edges",
          shared is not None and shared > 0.5
          and f"one outline for both FPCs down to their tail roots ({shared:.1f} mm below the taxel field), so they align by their edges" in card,
          (shared, card))
    check("field soft: both tails end together (equal lengths below their shared root), at least the 20 mm asked past the base edge "
          "(P5-diagonal-bus.md section 27.3)", proposal["tail_reach_mm"] >= 20.0 and proposal["row_tail_mm"] == proposal["column_tail_mm"]
          and "both end together, their contacts in line, 20.0 mm or more past the base edge" in card,
          (proposal["tail_reach_mm"], proposal["row_tail_mm"], proposal["column_tail_mm"], card))
    ends = flat_tail_ends(page) or {}
    check("field soft: drawn in the flat view, both stacked tails end 20 mm past the base edge",
          ends.get("row") is not None and ends.get("column") is not None and abs(ends["row"] - 20.0) < 0.01 and abs(ends["column"] - 20.0) < 0.01,
          (ends, proposal["row_tail_mm"], proposal["column_tail_mm"]))
    check("field soft: the card says the Row traces meet in a funnel into the Row tail centred under the field and the tails are stacked, "
          "both centred on the field",
          proposal["tail_position"] == "centred" and proposal["tails"] == "stacked" and "a funnel into the Row tail centred under the field" in card
          and "stacked: the Row tail over the Column tail, both centred on the field; they part to their own connectors" in card
          and "Column tail" + chr(10) not in card and " moved " not in card.replace("not moved", ""), (proposal["tail_position"], card))
    note = page.inner_text("#cadViewNote") if page.is_visible("#cadViewNote") else ""
    check("field soft: the 3D view says which parts it leaves out and where the markers are", "Off the surface" in note and "dark purple dots" in note, note)
    cell = page.inner_text("#cadProposals tbody tr:first-child td[data-tip]")
    check("field soft: the table's Tip column shows the tip", cell == f"{tip:.1f} mm", cell)
    width = flat_tip(page, proposal["taxel_height_mm"])
    check("field soft: the proposal's tip equals the Row outline's width at the top row's centre (flat view)", width is not None and abs(width - tip) < 2e-3, (width, tip))
    flat = page.evaluate("""() => [document.querySelectorAll('#cadFlat polygon.is-off').length, document.querySelectorAll('#cadFlat polygon[clip-path]').length,
        document.querySelectorAll('#cadFlat clipPath#cadFlatOn path').length]""")
    check("field soft: the flat view draws each board dotted off the surface and solid on it (clipped to the surface)", flat == [2, 2, 1], flat)
    check("field soft: the flat caption names the dotted parts", "dotted where they leave the surface" in page.inner_text("#cadFlatCaption"), page.inner_text("#cadFlatCaption"))
    if s["webgl"] == "ok":
        check("field soft: the 3D overlay marks where the boards leave the surface", (s["overlay"] or {}).get("edge_markers", 0) > 0, s["overlay"])
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_field_soft_fit_1440.png")
    before = len(page.generate)
    s = generate_and_wait(page)
    sent, result = page.generate[-1] if len(page.generate) > before else ({}, {})
    check("field soft: Generate sends routing.row_sides both with the form and builds the proposal's build id",
          (sent.get("routing") or {}).get("row_sides") == "both" and result.get("manifest", {}).get("build_id") == proposal["build_id"] == s["generated_build_id"]
          and s["generated_row_sides"] == "both", (sent.get("routing"), result.get("manifest", {}).get("build_id"), proposal["build_id"]))
    check("field soft: a full field gets no masked badge (the bus records its full mask)", page.query_selector("#maskBadge") is None,
          page.inner_text("#summary") if page.query_selector("#summary") else "")
    check("field soft: the build passes every DRC check and the registration", result.get("ok") is True
          and all(board["verification"]["all_checks_passed"] for board in result.get("boards", {}).values())
          and result["boards"]["row"]["verification"]["registration"]["passed"], result.get("validation", {}).get("errors"))
    check("field soft: the form shows the Row traces of the build (Diagonal, both sides)", page.input_value("#rowSides") == "both" and page.is_visible("#rowSides"),
          page.input_value("#rowSides"))
    rules = page.evaluate("() => [...document.querySelectorAll('#cadVerifyTable tbody tr')].map(r => [r.dataset.rule, r.classList.contains('is-pass')])")
    check("field soft: every map record passes, field_clearance among them (no board_clearance)", s["verification"]["ok"] and s["verification"]["passed"] == s["verification"]["total"] > 0
          and ["field_clearance", True] in rules and not any(rule == "board_clearance" for rule, _ in rules), rules)
    check("field soft: the overlay has the taxels, the routing report its shares and the readout the folded Row order", s["overlay"]["taxels"] == taxels
          and s["map_routing"] == proposal["on_surface"] and s["map_row_contact_order"] == rows and "Routing on the surface" in page.inner_text("#cadRoutingNote")
          and "ROW_01, ROW_03" in page.inner_text("#cadRowOrderNote"), (s["map_routing"], s["map_row_contact_order"]))
    legend = page.inner_text("#assemblyRowBus") if page.query_selector("#assemblyRowBus") else ""
    boxes = page.evaluate("() => [...document.querySelectorAll('#stackedPreview .assembly-board')].map(b => b.dataset.role)")
    check("field soft: the stacked view shows both boards with the tails stacked, the Row tail over the Column tail", sorted(boxes) == ["columns", "rows"]
          and "both tails leave bottom, stacked: the Row tail over the Column tail, 6.500 mm of their width on each other, both centred on the "
          "field, ending together, their contacts in line" in legend
          and "they part to their own connectors" in legend and "side by side" not in legend and "Row pins 1–59: ROW_01, ROW_03" in legend, (boxes, legend))
    # The note's lengths to three decimals, as its other figures (P5-diagonal-bus.md section 27.5: "1.893896 mm below the
    # taxel field" beside "1.500 mm of their width" before).
    check("field soft: the stacked view says the boards share one outline down to their tail roots and align by it",
          f"Both boards share one outline down to their tail roots ({shared:.3f} mm below the taxel field), so they "
          "align by their edges; only the tails differ" in legend
          and abs(float(page.get_attribute("#assemblyRowBus", "data-shared-outline") or "nan") - shared) < 1e-6, legend)
    page.click('[data-assembly-mode="plan"]')
    page.wait_for_timeout(200)
    page.locator(".stacked-review").screenshot(path=f"{SHOTS}/cad_field_soft_stack_plan.png")
    problems, rings = stacked_pin1(page)
    check("field soft: in the plan view the stacked tails' pin-1 rings (the top FPC's teal, the bottom FPC's orange) differ in colour, "
          "do not overlap and neither takes in the other board's triangle (P5-diagonal-bus.md section 27.3)", problems == [], (problems, rings))
    covered, counts = pin1_strokes(page)
    check("field soft: in the plan view both pin-1 rings are drawn above both boards (each ring's stroke its own colour over the other "
          "board: P5-diagonal-bus.md section 27.8)", covered == [], (covered, counts))
    shaped, shapes = pin1_shapes(page)
    check("field soft: in the plan view each pin-1 ring drawn as its board's ring lies on screen (each semi-axis within 5 %, the centre "
          "within 1 px: section 27.9)", shaped == [], (shaped, shapes))
    page.click('[data-assembly-mode="exploded"]')
    page.wait_for_timeout(200)
    problems, rings = stacked_pin1(page)
    check("field soft: and in the exploded view", problems == [], (problems, rings))
    covered, counts = pin1_strokes(page)
    check("field soft: and in the exploded view both rings above both boards", covered == [], (covered, counts))
    shaped, shapes = pin1_shapes(page)
    check("field soft: and in the exploded view each ring drawn as its board's ring lies on screen", shaped == [], (shaped, shapes))
    _, data = save(page, "#cadSaveCsv")
    lines = list(csv.reader(data.decode().splitlines()))
    head = lines[0]
    check("field soft: the CSV of the full field lists its taxels only (no active column)", "active" not in head and len(lines) - 1 == taxels, (head[-3:], len(lines)))
    pins = {line[head.index("row")]: line[head.index("row_pin")] for line in lines[1:]}
    check("field soft: the taxel CSV's Row pins follow the pads (ROW_01 on pin 1, ROW_02 on the last pin)", pins.get("1") == "1" and pins.get("2") == str(rows)
          and pins.get("3") == "2", {key: pins.get(key) for key in ("1", "2", "3")})
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_field_soft_generated_1440.png")
    check("field soft: no request was retried for a busy server", state(page)["retries"] == 0, state(page)["retries"])
    check("field soft part: no console errors", not errors_of(page), errors_of(page))
    page.close()


def part_review_fixes(browser):
    """The P5d/P5e reviews' browser findings: a stale Generate, a Whole-board build after a Field-only one, the kept
    Containment, the disabled controls' reasons, the Row pins with Scan order Reverse, a refit after Generate without
    a busy server, short pin lists of a few rows, the tail extension's range."""
    if not SOFT.exists():
        print("SKIP review fixes: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, SOFT)
    candidate(page, 1)
    page.check('input[name=cadSide][value="0"]')
    page.wait_for_timeout(100)
    check("review: the tail extension takes the server's range (6.5-72.5 mm)", (page.get_attribute("#cadTailExtension", "min"), page.get_attribute("#cadTailExtension", "max"))
          == ("6.5", "72.5"), (page.get_attribute("#cadTailExtension", "min"), page.get_attribute("#cadTailExtension", "max")))
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    fitted = state(page)["proposal"]
    # 1. A changed option makes the proposals stale: Generate waits for a new fit (it built the old Row traces).
    page.select_option("#cadRowSides", "left")
    page.wait_for_timeout(150)
    s = state(page)
    label = page.inner_text("#cadGenerate")
    check("review: after Row traces Left, Generate waits for a new fit (disabled, says why) and the note says the settings changed",
          s["fit_stale"] and page.is_disabled("#cadGenerate") and "Fit again first" in label and "Settings changed" in page.inner_text("#cadFitNote"), (s["fit_stale"], label))
    page.select_option("#cadRowSides", "both")
    page.wait_for_timeout(150)
    check("review: back at the fitted Both, the proposals are current again", not state(page)["fit_stale"] and not page.is_disabled("#cadGenerate")
          and f"proposal #{fitted['rank']}" in page.inner_text("#cadGenerate"), page.inner_text("#cadGenerate"))
    page.fill("#cadTailExtension", "25")
    page.wait_for_timeout(150)
    check("review: an edited number makes them stale too", state(page)["fit_stale"] and page.is_disabled("#cadGenerate"), state(page)["fit_stale"])
    page.fill("#cadTailExtension", "20")
    page.wait_for_timeout(150)
    # 2. Field only, generated; then the Row pins with Scan order Reverse (pin 1 carries ROW_02).
    s = generate_and_wait(page)
    check("review: the Field-only proposal builds and maps", s["generated_build_id"] == fitted["build_id"] and s["verification"]["ok"], (s["generated_build_id"], fitted["build_id"]))
    retries = s["retries"]
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.verification !== null && s.busy.length === 0; }", 60)
    s = state(page)
    check("review: Fit again after Generate maps the generated proposal without a busy server (one map request at a time)",
          s["retries"] == retries and "busy" not in page.inner_text("#cadStatus") and s["verification"]["ok"], (s["retries"], page.inner_text("#cadStatus")))
    # The regenerated build is another one (the scan order is in its identity): wait for its own map.
    mapped = "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.verification !== null && s.overlay && s.overlay.build_id === s.generated_build_id && s.generated_build_id !== %s; }"
    forward = s["generated_build_id"]
    page.select_option("#scanOrder", "reverse")
    page.wait_for_timeout(200)
    page.click("#regenerate")
    wait_until(page, mapped % json.dumps(forward), 120)
    page.wait_for_timeout(300)
    s = state(page)
    legend = page.inner_text("#assemblyRowBus") if page.query_selector("#assemblyRowBus") else ""
    order = page.inner_text("#cadRowOrderNote") if page.query_selector("#cadRowOrderNote") else ""
    check("review: with Scan order Reverse the map's Row pins start at ROW_02 (from the pads)", (s["map_row_pin_order"] or [None])[0] == "ROW_02"
          and "Row pins 1–59 (from the pads" in order and ": ROW_02, ROW_04" in order, (s["map_row_pin_order"][:3] if s["map_row_pin_order"] else None, order))
    check("review: and the stacked view's Row pins too", "Row pins 1–59: ROW_02, ROW_04" in legend, legend)
    reverse = s["generated_build_id"]
    page.select_option("#scanOrder", "forward")
    page.wait_for_timeout(200)
    page.click("#regenerate")
    wait_until(page, mapped % json.dumps(reverse), 120)
    page.wait_for_timeout(300)
    # 3. A Whole-board proposal generated after the Field-only one: the form drops the Row traces, the build is the proposal's.
    page.select_option("#cadContainment", "board")
    page.wait_for_timeout(150)
    check("review: under Whole board, Row traces show the straight channel (disabled, not sent)", page.input_value("#cadRowSides") == "channel" and page.is_disabled("#cadRowSides")
          and "straight channel" in page.inner_text("#cadConfigHint"), (page.input_value("#cadRowSides"), page.inner_text("#cadConfigHint")))
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    board = state(page)["proposal"]
    before = len(page.generate)
    s = generate_and_wait(page)
    sent, result = page.generate[-1] if len(page.generate) > before else ({}, {})
    rules = [record[0] for record in page.evaluate("() => [...document.querySelectorAll('#cadVerifyTable tbody tr')].map(r => [r.dataset.rule])")]
    check("review: a Whole-board proposal generated after a Field-only one builds its own build id with the Straight channel in the form",
          board["containment"] == "board" and result.get("manifest", {}).get("build_id") == board["build_id"] == s["generated_build_id"]
          and (sent.get("routing") or {}).get("row_sides") == "channel" and "row_sides" not in result.get("design", {}).get("routing", {})
          and page.input_value("#rowSides") == "channel" and s["verification"]["ok"] and "board_clearance" in rules,
          (board["build_id"], result.get("manifest", {}).get("build_id"), sent.get("routing"), page.input_value("#rowSides")))
    # 4. Whole board and back: the Row traces chosen under Field only come back (the straight channel shown in between).
    page.select_option("#cadContainment", "field")
    page.select_option("#cadRowSides", "right")
    page.select_option("#cadContainment", "board")
    page.wait_for_timeout(150)
    check("review: under Whole board the Row traces show the straight channel again", page.input_value("#cadRowSides") == "channel" and page.is_disabled("#cadRowSides"),
          page.input_value("#cadRowSides"))
    page.select_option("#cadContainment", "field")
    page.wait_for_timeout(150)
    check("review: and Field only with the Row traces chosen before (Right)", page.input_value("#cadContainment") == "field" and page.input_value("#cadRowSides") == "right"
          and not page.is_disabled("#cadRowSides"), (page.input_value("#cadContainment"), page.input_value("#cadRowSides")))
    # 5. A few rows: the Row pins name every row, none twice.
    page.select_option("#cadRowSides", "both")
    page.fill("#cadMaxRows", "3")
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    s = state(page)
    pins = page.inner_text('#cadProposalFacts dd[data-fact="row-pins"]') if page.query_selector('#cadProposalFacts dd[data-fact="row-pins"]') else ""
    check("review: three rows list their pins once each (ROW_01, ROW_03, ROW_02)", s["proposal"]["rows"] == 3 and pins.endswith("ROW_01, ROW_03, ROW_02") and "…" not in pins,
          (s["proposal"]["rows"], pins))
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_review_fixes_1440.png")
    check("review fixes part: no unexpected console errors", not errors_of(page), errors_of(page))
    page.close()


def _tails_fact(page):
    node = page.query_selector('#cadProposalFacts dd[data-fact="tails"]')
    return node.inner_text() if node else ""


def part_tail_card(browser):
    """The proposal card's Tails line (P5-diagonal-bus.md section 27.3's review): both tails end on the nearest line on
    which each is at least the shortest tail long and ends at least the extension past the base edge under it.  Asked
    20 mm on the soft finger the extension sets the line (the nearer end just that far, no reason given); asked 6.5 mm
    the shortest tail sets it, and the card says so with the tail roots' depth past the base edge from the fit's
    metrics (the old text read the reach less the shorter tail as how far the Row bus reached and that tail as the
    shortest).  The roots above the edge (the fit's reply edited: 7.5 mm tails, the nearer end 7.0 mm past) read as
    such."""
    if not SOFT.exists():
        print("SKIP tail card: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, SOFT)
    candidate(page, 1)
    page.check('input[name=cadSide][value="0"]')
    page.click("#cadFit"); settle(page)
    proposal, tails = state(page)["proposal"], _tails_fact(page)
    check("tail card: asked 20 mm, the extension sets the line: the nearer end 20.0 mm past the base edge, no reason given",
          abs(proposal["tail_reach_mm"] - 20.0) < 2e-3 and "20.0 mm or more past the base edge; Row" in tails and "asked" not in tails, (proposal["tail_reach_mm"], tails))
    page.fill("#cadTailExtension", "6.5")
    page.click("#cadFit"); settle(page)
    proposal, tails = state(page)["proposal"], _tails_fact(page)
    length, reach = proposal["row_tail_mm"], proposal["tail_reach_mm"]
    expected = (f"{reach:.1f} mm or more past the base edge (asked 6.5 mm: a tail is at least 7.5 mm long, which sets the line, and the tail "
                f"roots already lie {reach - length:.1f} mm past the base edge); Row 7.5 mm, Column 7.5 mm long")
    check("tail card: asked 6.5 mm on the soft finger the shortest tail (7.5 mm) sets the line, its roots that far past the base edge",
          length == proposal["column_tail_mm"] == 7.5 and reach > 6.5 + 1.0 and expected in tails, (length, reach, tails))

    def edited(route):
        response = route.fetch()
        body = response.json()
        for item in body.get("proposals", []):
            item["metrics"].update(row_tail_mm=7.5, column_tail_mm=7.5, tail_reach_mm=7.0)
        route.fulfill(response=response, json=body)
    page.route("**/api/surface/fit*", edited)
    page.click("#cadFit"); settle(page)
    tails = _tails_fact(page)
    check("tail card: the roots above the edge read as such (the fit's reply edited: 7.5 mm tails, the nearer end 7.0 mm past)",
          "7.0 mm or more past the base edge (asked 6.5 mm: a tail is at least 7.5 mm long, which sets the line, and the tail roots lie "
          "only 0.5 mm above the base edge)" in tails, tails)
    page.unroute("**/api/surface/fit*")
    check("tail card part: no unexpected console errors", not errors_of(page), errors_of(page))
    page.close()


def part_row_sides(browser):
    """The Row traces choice round-trips through Fit, Generate and the build id; the form's select; Rectangular mode."""
    if not SOFT.exists():
        print("SKIP row sides: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, SOFT)
    candidate(page, 1)
    page.check('input[name=cadSide][value="0"]')
    page.select_option("#cadContainment", "field")
    builds = {}
    for side in ("left", "right"):
        page.select_option("#cadRowSides", side)
        page.click("#cadFit"); settle(page)
        s = state(page)
        check(f"row sides: Row traces {side} fits proposals built with routing.row_sides {side}", s["fit_options"]["row_sides"] == side and s["proposal"]
              and s["proposal"]["row_sides"] == side and s["proposal"]["containment"] == "field", (s["fit_options"], s["proposal"]))
        check(f"row sides: the card names the {side} side", f"diagonal bus, {side} side" in page.inner_text("#cadProposalCard"), page.inner_text("#cadProposalCard"))
        card = page.inner_text("#cadProposalCard")
        check(f"row sides: the {side} card's Row traces fan in under the field into the centred Row tail and its Bands line names the one band, "
              "the Row tail no longer under it (diagonal-bus/10)",
              f"diagonal bus, {side} side: fanning in under the field into the Row tail centred under it" in card
              and f"mm on the {side} side (none on the other) beyond the field" in card and "with the Row tail" not in card, card)
        before = len(page.generate)
        s = generate_and_wait(page)
        sent, result = page.generate[-1] if len(page.generate) > before else ({}, {})
        builds[side] = s["proposal"]["build_id"]
        check(f"row sides: Generate round-trips {side}: sent with the form, the build id is the proposal's, the map verifies",
              (sent.get("routing") or {}).get("row_sides") == side and result.get("manifest", {}).get("build_id") == s["proposal"]["build_id"] == s["generated_build_id"]
              and s["generated_row_sides"] == side and page.input_value("#rowSides") == side and s["verification"]["ok"],
              (sent.get("routing"), result.get("manifest", {}).get("build_id"), s["proposal"]["build_id"], page.input_value("#rowSides")))
        legend = page.inner_text("#assemblyRowBus") if page.query_selector("#assemblyRowBus") else ""
        check(f"row sides: the stacked view names the {side} side and an unfolded Row order, the traces fanning in under the field into the "
              "centred Row tail", f"the {side} side" in legend and "folded" not in legend
              and "fan in under the field into the Row tail centred under it" in legend and "both centred on the field" in legend, legend)
        page.click('[data-assembly-mode="plan"]')
        page.wait_for_timeout(200)
        problems, rings = stacked_pin1(page)
        check(f"row sides: {side}, the plan view's pin-1 rings of the two FPCs differ in colour, do not overlap and neither takes in the other "
              "board's triangle", problems == [], (problems, rings))
        covered, counts = pin1_strokes(page)
        check(f"row sides: {side}, the plan view's pin-1 rings drawn above both boards", covered == [], (covered, counts))
        shaped, shapes = pin1_shapes(page)
        check(f"row sides: {side}, the plan view's pin-1 rings drawn as their boards' rings lie on screen", shaped == [], (shaped, shapes))
        page.locator(".stacked-review").screenshot(path=f"{SHOTS}/cad_row_sides_{side}_stack_plan.png")
        page.click('[data-assembly-mode="exploded"]')
        page.wait_for_timeout(200)
        problems, rings = stacked_pin1(page)
        check(f"row sides: {side}, and in the exploded view", problems == [], (problems, rings))
        covered, counts = pin1_strokes(page)
        check(f"row sides: {side}, and in the exploded view both rings above both boards", covered == [], (covered, counts))
        shaped, shapes = pin1_shapes(page)
        check(f"row sides: {side}, and in the exploded view drawn as their boards' rings lie on screen", shaped == [], (shaped, shapes))
    check("row sides: left and right are different builds", builds["left"] != builds["right"], builds)
    # A form edit of the Row traces is a different design: the placement no longer matches.
    page.select_option("#rowSides", "both")
    page.wait_for_timeout(200)
    check("row sides: editing the form's Row traces marks the build stale", state(page)["stale"] and not state(page)["downloads"], state(page)["stale"])
    page.click("#regenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.map_error !== null; }", 120)
    s = state(page)
    check("row sides: the edited Row traces build another design, reported as E_SURFACE_PLACEMENT_MISMATCH", s["map_error"] == "E_SURFACE_PLACEMENT_MISMATCH"
          and s["generated_row_sides"] == "both", (s["map_error"], s["generated_row_sides"]))
    # Rectangular mode (P5-diagonal-bus.md section 18): the generic template takes routing.row_sides too: the field is
    # shown and sent (the kept Both builds the diagonal Row bus; Straight channel sends "channel", no bus).
    page.click("#modeRect")
    wait_until(page, "() => !document.getElementById('staleBanner').hidden", 10)
    check("row sides: Rectangular mode shows the Row traces field with the kept choice", page.is_visible("#rowSides") and not page.is_disabled("#rowSides")
          and page.input_value("#rowSides") == "both", (page.is_visible("#rowSides"), page.input_value("#rowSides")))
    # The generic template's bus is diagonal-bus/11 (CAD mode's rule set and construction, P5-diagonal-bus.md sections 20, 24,
    # 27 and 27.8).
    for choice, bus in (("both", "diagonal-bus/11"), ("channel", None)):
        page.select_option("#rowSides", choice)
        page.wait_for_timeout(150)
        before = len(page.generate)
        page.click("#generate")
        wait_until(page, DONE, 60)
        page.wait_for_timeout(300)
        sent, result = page.generate[-1] if len(page.generate) > before else ({}, {})
        check(f"row sides: Rectangular Generate sends routing.row_sides {choice} and builds it on the generic template",
              (sent.get("routing") or {}).get("row_sides") == choice and sent.get("template_id") == "generic_matrix_v1" and result.get("ok") is True
              and result.get("design", {}).get("routing", {}).get("row_sides") == choice and result.get("manifest", {}).get("row_bus") == bus,
              (sent.get("routing"), result.get("ok"), result.get("manifest", {}).get("row_bus")))
    page.select_option("#rowSides", "both")
    page.wait_for_timeout(150)
    page.click("#modeCad")
    page.wait_for_timeout(300); settle(page)
    check("row sides: back in CAD mode the field shows the kept choice", page.is_visible("#rowSides") and page.input_value("#rowSides") == "both", page.input_value("#rowSides"))
    s = generate_and_wait(page)
    sent = page.generate[-1][0]
    check("row sides: CAD Generate rebuilds the proposal's side (right) and verifies it", (sent.get("routing") or {}).get("row_sides") == "right"
          and s["generated_build_id"] == builds["right"] and s["verification"]["ok"] and s["downloads"], (sent.get("routing"), s["generated_build_id"]))
    check("row sides part: no unexpected console errors", not errors_of(page, allowed=("status of 422",)), errors_of(page, allowed=("status of 422",)))
    page.close()


def part_ascii_and_narrow(browser):
    if not SOFT.exists():
        print("SKIP ascii: asset/soft_gripper_finger.stl is absent")
        return
    ascii_path = Path(SCRATCH) / "soft_finger_ascii.stl"
    ascii_copy(SOFT, ascii_path)
    page = new_page(browser, 1024, 768)
    open_cad(page)
    load(page, ascii_path)
    s = state(page)
    check("ascii: server and browser read the 1944 facets of the ASCII copy", s["mesh"]["format"] == "ascii" and s["mesh"]["facets"] == s["mesh"]["browser_facets"] == 1944, s["mesh"])
    candidate(page, 1)
    s = state(page)
    check("ascii: candidate #1 is the same 3087.7 mm2 face", s["selection"] and abs(s["selection"]["area_mm2"] - 3087.7) < 0.05, s["selection"])
    page.click("#cadClear"); settle(page)
    page.select_option("#cadPreset", "flat"); page.wait_for_timeout(100)
    x, y = view_center(page)
    page.mouse.click(x, y); settle(page)
    s = state(page)
    check("ascii: click-grow picks the same face (facet ids agree)", s["selection"] and abs(s["selection"]["area_mm2"] - 3087.7) < 0.05, s["selection"])
    page.click("#cadFit"); settle(page)
    page.wait_for_timeout(800)  # the view may scroll back into sight (smooth)
    overflow = page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
    check("1024x768: no horizontal page overflow in CAD mode", overflow <= 0, overflow)
    table = page.evaluate("() => { const w = document.getElementById('cadProposalWrap'); return [w.scrollWidth, w.clientWidth]; }")
    check("1024x768: the proposals table fits its column (low-value columns dropped, no inner scroll)", table[0] <= table[1] + 1, table)
    seen = page.evaluate("""() => { const r = document.getElementById('cadView').getBoundingClientRect();
        return (Math.min(r.bottom, innerHeight) - Math.max(r.top, 0)) / r.height; }""")
    check("1024x768: the 3D view is in sight after Fit (the proposal is drawn on it)", seen >= 0.3, seen)
    page.screenshot(path=f"{SHOTS}/cad_soft_fit_1024.png")
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_soft_workspace_1024.png")
    check("ascii/narrow part: no console errors", not errors_of(page), errors_of(page))
    page.close()


def part_wrap_flexitac(browser):
    """The soft finger's curved wrap (smooth preset) with FlexiTac connectors: pins through the form, reader lines in the CSV."""
    if not SOFT.exists():
        print("SKIP wrap: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, SOFT)
    candidate(page, 1, "smooth")
    s = state(page)
    # The candidate lists 7646.3 mm2 (250 facets); the chart keeps 7640.8 mm2 (248 facets).
    check("wrap: smooth candidate #1 is the ~7640 mm2 wrap, unrolled (developable)",
          s["selection"] and abs(s["selection"]["area_mm2"] - 7646.3) < 0.01 * 7646.3 and s["selection"]["kind"] == "developable", s["selection"])
    page.select_option("#cadReader", "32x16")
    page.click("#cadFit"); settle(page)
    s = state(page)
    check("wrap: fit with FlexiTac connectors gives proposals", s["proposals"] >= 1, s)
    page.click("#cadGenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && (s.verification !== null || s.map_error !== null); }", 120)
    s = state(page)
    sent = page.generate[-1][0]
    check("wrap: the form sends the FlexiTac pins (16/32) and builds the proposal",
          sorted(sent["connector"].values()) == [16, 32] and s["generated_build_id"] == s["proposal"]["build_id"], (sent.get("connector"), s["generated_build_id"]))
    check("wrap: the build maps onto the curved surface and passes", s["verification"] and s["verification"]["ok"]
          and s["overlay"]["taxels"] == s["proposal"]["taxels"], s)
    check("wrap: the proposal reports the FlexiTac reader (32 x 16)", s["proposal"]["reader"] == "32x16", s["proposal"])
    name, data = save(page, "#cadSaveCsv")
    lines = list(csv.reader(data.decode().splitlines()))
    header = lines[0]
    columns = [header.index(name) for name in ("sense_line", "drive_line", "frame_index")] if {"sense_line", "drive_line", "frame_index"} <= set(header) else None
    first = [[line[k] for k in columns] for line in lines[1:]] if columns else []
    check("wrap: the taxel CSV carries the reader lines (SR1, SC1 at frame index 0)", columns is not None and ["SR1", "SC1", "0"] in first, header)
    page.click('[data-cad-view="selection"]')
    page.wait_for_timeout(250)
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_soft_wrap_flexitac_1440.png")
    check("wrap part: no console errors", not errors_of(page), errors_of(page))
    page.close()


def box_stl(size=20.0) -> bytes:
    """A closed box as a binary STL in mm (12 facets)."""
    s = size
    corners = [(x, y, z) for x in (0, s) for y in (0, s) for z in (0, s)]
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    triangles = []
    for a, b, c, d in quads:
        triangles += [(corners[a], corners[b], corners[c]), (corners[a], corners[c], corners[d])]
    body = b"".join(struct.pack("<12fH", 0, 0, 0, *triangle[0], *triangle[1], *triangle[2], 0) for triangle in triangles)
    return b"box".ljust(80, b"\0") + struct.pack("<I", len(triangles)) + body


def part_drop(browser):
    page = new_page(browser)
    open_cad(page)
    page.evaluate("""bytes => {
        const file = new File([new Uint8Array(bytes)], 'box.stl', {type: 'model/stl'});
        const data = new DataTransfer(); data.items.add(file);
        const view = document.getElementById('cadView');
        view.dispatchEvent(new DragEvent('dragover', {dataTransfer: data, bubbles: true, cancelable: true}));
        view.dispatchEvent(new DragEvent('drop', {dataTransfer: data, bubbles: true, cancelable: true}));
    }""", list(box_stl()))
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.mesh !== null && s.mesh.name === 'box.stl' && s.busy.length === 0; }", 30)
    s = state(page)
    check("drop: a dropped STL is inspected (box: 12 facets, mm guessed, watertight)",
          s["mesh"]["facets"] == 12 and s["mesh"]["unit"] == "mm" and s["mesh"]["watertight"] and s["mesh"]["name"] == "box.stl", s["mesh"])
    candidate(page, 1)
    s = state(page)
    check("drop: a box face is a 400 mm2 planar selection with 4 sides", s["selection"] and abs(s["selection"]["area_mm2"] - 400) < 1e-6
          and s["selection"]["kind"] == "planar" and s["selection"]["sides"] == 4, s["selection"])
    page.fill("#cadEdgeMargin", "20")
    page.click("#cadFit"); settle(page)
    s = state(page)
    check("drop: an impossible setting (20 mm edge margin on a 20 mm face) reports E_SURFACE_NO_FIT with the rejected candidates",
          s["error"] == "E_SURFACE_NO_FIT" and s["proposals"] == 0 and "Rejected candidates" in page.inner_text("#cadFitNote"), (s["error"], page.inner_text("#cadFitNote")))
    page.fill("#cadEdgeMargin", "0")
    page.select_option("#cadUnit", "cm")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.mesh.unit === 'cm' && s.selection; }", 30)
    s = state(page)
    check("drop: unit override cm re-inspects and re-selects (area x100)", abs(s["selection"]["area_mm2"] - 40000) < 1e-3, s["selection"])
    page.evaluate("""() => {
        const file = new File([new TextEncoder().encode('not a mesh at all')], 'bad.stl');
        const data = new DataTransfer(); data.items.add(file);
        document.getElementById('cadView').dispatchEvent(new DragEvent('drop', {dataTransfer: data, bubbles: true, cancelable: true}));
    }""")
    page.wait_for_timeout(300)
    s = state(page)
    check("drop: a file that is not an STL is refused with a message, the loaded mesh stays",
          s["error"] == "E_CLIENT_STL" and s["mesh"]["name"] == "box.stl" and "not loaded" in page.inner_text("#cadStatus"), (s["error"], page.inner_text("#cadStatus")))
    check("drop part: no unexpected console errors", not errors_of(page, allowed=("status of 422",)), errors_of(page, allowed=("status of 422",)))
    page.close()


def generate_and_wait(page):
    page.click("#cadGenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.pending_build === null && (s.verification !== null || s.map_error !== null); }", 120)
    page.wait_for_timeout(200)
    return state(page)


def soft_fit(page, side="0"):
    open_cad(page)
    load(page, SOFT)
    candidate(page, 1)
    if side is not None:
        page.check(f'input[name=cadSide][value="{side}"]')
        page.wait_for_timeout(100)
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)


# Max rows and Max columns in sight after the tail since 2026-10-30 (the user's request).
# One step (2026-11-02): the file, the 3D view's tools and the sensor's line in sight; the basic options under Advanced Customization.
CAD_STEP = ["cadFile", "cadFileNote", "cadTools", "cadRemove", "cadQuickGenerate"]
CAD_BASIC = ["cadPitch", "cadFill", "cadRowSides", "cadTailExtension", "cadMaxRows", "cadMaxColumns", "cadFit", "cadGenerate", "cadSides"]
CAD_FOLDED = ["cadUnit", "cadPreset", "cadThetaD", "cadObjective", "cadContainment", "cadReader", "cadStrainLimit"]
SHOWN = """(ids) => ids.map(id => { const node = document.getElementById(id); return [id, Boolean(node && node.checkVisibility())]; })"""


def part_clean_cad(browser):
    """CAD mode as the user sees it (no unfold()): the rectangular form hidden (CAD mode has its own steps) and the shared
    results (a rectangular build) hidden until CAD mode generates; the file, the view's tools and the sensor's line in
    sight, the rest under Advanced Customization (2026-11-02); opened, its basic options in sight, File details, Selection
    settings and More options folded; after Fit and Generate on the soft finger the results in sight, step 7 one line
    ("all N checks pass") with its checks folded, the proposal's details folded; back in Rectangular mode the form."""
    if not SOFT.exists():
        print("SKIP clean CAD: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser, folded=True)
    open_cad(page)
    check("clean CAD: the rectangular form and the results (the rectangular default build) are hidden before a CAD build",
          not page.is_visible("#designForm") and not page.is_visible("#results") and not page.is_visible("#status"))
    shown = dict(page.evaluate(SHOWN, CAD_STEP + CAD_BASIC + CAD_FOLDED))
    check("clean CAD: the file, its drag hint, the view's tools and the sensor's line in sight; the options, Fit and Generate under "
          "Advanced Customization, folded", all(shown[name] for name in CAD_STEP) and not any(shown[name] for name in CAD_BASIC + CAD_FOLDED)
          and not page.evaluate("() => document.getElementById('cadCustomize').open"), shown)
    page.click("#cadCustomize > summary"); page.wait_for_timeout(200)
    shown = dict(page.evaluate(SHOWN, CAD_BASIC + CAD_FOLDED))
    check("clean CAD: opened, Advanced Customization shows the basic options, the rest folded (File details, Selection settings, More options)",
          all(shown[name] for name in CAD_BASIC) and not any(shown[name] for name in CAD_FOLDED), shown)
    sizes = page.evaluate("() => ['#cadConfigMore > summary', '#cadFileMore > summary'].map(s => parseFloat(getComputedStyle(document.querySelector(s)).fontSize))")
    check("clean CAD: 'More options' is larger than the other folds' summaries (15 px or more)", sizes[0] >= 15 and sizes[0] > sizes[1], sizes)
    page.click("#cadConfigMore > summary"); page.wait_for_timeout(100)
    check("clean CAD: More options shows the other fit options", page.is_visible("#cadContainment") and page.is_visible("#cadStrainLimit"))
    page.click("#cadConfigMore > summary"); page.wait_for_timeout(100)
    load(page, SOFT)
    candidate(page, 1)
    page.check('input[name=cadSide][value="0"]'); page.wait_for_timeout(100)
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    check("clean CAD: the proposal's details folded under its title", page.is_visible("#cadProposalCardTitle") and not page.is_visible("#cadProposalFacts"))
    s = generate_and_wait(page)
    line = page.inner_text("#cadVerifyLine") if page.query_selector("#cadVerifyLine") else ""
    check("clean CAD: after Generate the results are in sight and step 7 says the build's checks in one line, folded",
          page.is_visible("#results") and page.inner_text("#status").startswith("Valid build") and re.search(r"✓ all \d+ checks pass", line)
          and not page.is_visible("#cadVerifyTable") and s["verification"]["ok"], (line, page.inner_text("#status")))
    page.click("#cadVerifyMore > summary"); page.wait_for_timeout(100)
    check("clean CAD: Check details shows the checks on the part", page.is_visible("#cadVerifyTable"))
    page.check("#modeRect"); page.wait_for_timeout(300)
    check("clean CAD: Rectangular mode shows the form again", page.is_visible("#designForm") and page.is_visible("#rows"))
    check("clean CAD part: no console errors", not errors_of(page), errors_of(page))
    page.close()


def part_template_roundtrip(browser):
    """The template is app.js state: a Rectangular build is never 'verified on the part' (review: critical)."""
    if not SOFT.exists():
        print("SKIP roundtrip: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    soft_fit(page)
    # The form's own Generate after a fit (no CAD Generate yet) builds the default template: nothing rewrites it.
    before = len(page.generate)
    page.click("#generate")
    wait_until(page, DONE, 60); settle(page)
    sent = page.generate[-1][0] if len(page.generate) > before else {}
    check("roundtrip: after a fit, the form's own Generate sends the default template (no fetch rewrite)", sent.get("template_id") == "generic_matrix_v1", sent.get("template_id"))
    s = generate_and_wait(page)
    proposal_build = s["proposal"]["build_id"]
    check("roundtrip: CAD Generate builds the proposal with its template and verifies it",
          s["generated_build_id"] == proposal_build and s["generated_template_id"] == "surface_matrix_v1" and s["verification"]["ok"], s)
    page.click("#modeRect")
    wait_until(page, "() => !document.getElementById('staleBanner').hidden", 10)
    badge = page.inner_text("#profileBadge")
    check("roundtrip: Rectangular mode restores the default template: badge, and the surface build is marked stale",
          "Generic" in badge and not page.evaluate("() => document.getElementById('staleBanner').hidden"), badge)
    before = len(page.generate)
    page.click("#generate")
    wait_until(page, DONE, 60)
    page.wait_for_timeout(300)
    sent, result = page.generate[-1] if len(page.generate) > before else ({}, {})
    check("roundtrip: Rectangular Generate of the unchanged form sends the default template", sent.get("template_id") == "generic_matrix_v1"
          and result.get("design", {}).get("template_id") == "generic_matrix_v1", sent.get("template_id"))
    generic_build = result.get("manifest", {}).get("build_id")
    page.click("#modeCad")
    page.wait_for_timeout(400); settle(page)
    s = state(page)
    check("roundtrip: back in CAD, the Rectangular build is reported as a template mismatch, never verified, no downloads",
          s["generated_build_id"] == generic_build != proposal_build and s["map_error"] == "E_CLIENT_TEMPLATE_MISMATCH" and s["verification"] is None
          and not s["downloads"] and "Downloads are ready" not in page.inner_text("#cadStatus"), (s, page.inner_text("#cadStatus")))
    check("roundtrip: CAD mode takes its template back, so the form is stale against the generic build",
          not page.evaluate("() => document.getElementById('staleBanner').hidden") and "surface" in page.inner_text("#profileBadge").lower(), page.inner_text("#profileBadge"))
    s = generate_and_wait(page)
    check("roundtrip: Generate again rebuilds the proposal and verifies it", s["generated_build_id"] == proposal_build and s["verification"]["ok"] and s["downloads"], s)
    check("roundtrip part: no unexpected console errors", not errors_of(page), errors_of(page))
    page.close()


def part_columns(browser):
    """Max columns follows the surface template's form limits; a proposal outside them never overwrites the form (review: major)."""
    if not SOFT.exists():
        print("SKIP columns: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page, caps=None)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).limits_served !== null", 30)
    s = state(page)
    expected = 64 if SERVED else 32
    check(f"columns: Max columns is capped at the template's form limit ({expected}), 32 by default (the user's default)",
          s["max_columns"] == expected and page.input_value("#cadMaxColumns") == "32"
          and s["limits_served"] is SERVED, (s["max_columns"], page.input_value("#cadMaxColumns"), s["limits_served"]))
    if SERVED:
        set_caps(page, 64)
    check("columns: the limits note is shown exactly when the server does not send the template's limits",
          page.evaluate("() => document.getElementById('cadLimitsNote').hidden") is SERVED, page.inner_text("#cadLimitsNote") if not SERVED else "")
    load(page, SOFT)
    candidate(page, 1)
    if not SERVED:
        # Force a fit beyond the form's limits (as before the repair) to check the guard of the form.
        page.evaluate("() => { const c = document.getElementById('cadMaxColumns'); c.max = '64'; c.value = '64'; }")
    page.click("#cadFit"); settle(page)
    # Field only (the default) ranks the 59 x 12 field through the mount end first; its 12 x 59 alternative (59 columns,
    # tails across the long side) is the surface template's gain over the form's 32 columns.
    wide = page.evaluate("""() => [...document.querySelectorAll('#cadProposals tbody tr')].findIndex(row =>
        Number(row.children[2].textContent.split('×')[1]) > 32)""")
    if wide > 0:
        page.click(f'input[name=cadProposal][value="{wide}"]')
        settle(page)
    s = state(page)
    check("columns: the auto-base fit proposes more than 32 columns (the surface template's gain)", s["proposal"] and s["proposal"]["columns"] > 32, (wide, s["proposal"]))
    form_before = page.evaluate("() => ['rows', 'columns', 'name', 'topTailLength'].map(id => document.getElementById(id).value)")
    before = len(page.generate)
    page.click("#cadGenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.pending_build === null && (s.verification !== null || s.map_error !== null || s.error === 'E_CLIENT_FORM'); }", 120)
    page.wait_for_timeout(300)
    s = state(page)
    form_after = page.evaluate("() => ['rows', 'columns', 'name', 'topTailLength'].map(id => document.getElementById(id).value)")
    if SERVED:
        check("columns: a 33-64 column proposal builds through the form and maps onto the part",
              len(page.generate) == before + 1 and s["generated_build_id"] == s["proposal"]["build_id"] and s["verification"]["ok"], s)
    else:
        check("columns: a proposal outside the form's limits is refused before the form is touched (no request, form unchanged)",
              len(page.generate) == before and s["error"] == "E_CLIENT_FORM" and form_after == form_before
              and page.evaluate("() => document.getElementById('staleBanner').hidden"), (s["error"], form_before, form_after, page.inner_text("#cadStatus")))
    # The app.js hook itself: a design outside any template's limits is refused and the form is left alone.
    outcome = page.evaluate("""async () => {
        const before = ['rows', 'columns'].map(id => document.getElementById(id).value);
        const detail = {design: {template_id: 'surface_matrix_v1', matrix: {rows: 65, columns: 70}}};
        document.dispatchEvent(new CustomEvent('fpc:apply-design', {detail}));
        const result = await detail.result;
        return {result, same: JSON.stringify(before) === JSON.stringify(['rows', 'columns'].map(id => document.getElementById(id).value))};
    }""")
    check("columns: fpc:apply-design refuses a design outside the limits and leaves the form", outcome["result"]["ok"] is False and outcome["same"]
          and any("matrix.columns" in problem for problem in outcome["result"]["problems"]), outcome)
    check("columns part: no unexpected console errors", not errors_of(page), errors_of(page))
    page.close()


def part_presets(browser):
    """Custom angles send every value; the Surface preset and its candidates (review: major)."""
    if not SOFT.exists():
        print("SKIP presets: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, SOFT)
    surfaces = state(page)["candidates"]["surface"]
    check("presets: the server lists its 'surface' candidates (the page shows no list since 2026-10-30)", len(surfaces) > 0, surfaces)
    candidate(page, 1, "surface")
    check("presets: a Surfaces candidate selects a region", state(page)["selection"] is not None, state(page)["selection"])
    page.click("#cadClear"); settle(page)
    x, y = view_center(page)
    areas = {}
    for preset, values in (("smooth", None), ("custom", ("30", "180", "0")), ("surface", None), ("custom", ("30", "180", "4"))):
        page.evaluate("() => { const button = document.getElementById('cadClear'); if (!button.disabled) button.click(); }"); settle(page)
        if values:
            # Moving a control switches the preset to Custom.
            page.fill("#cadMinRadius", values[2])
            page.evaluate("""([d, c]) => { for (const [id, value] of [['cadThetaD', d], ['cadThetaC', c]]) { const input = document.getElementById(id);
                input.value = value; input.dispatchEvent(new Event('input', {bubbles: true})); } }""", list(values[:2]))
        else:
            page.select_option("#cadPreset", preset)
        page.mouse.click(x, y); settle(page)
        areas[(preset, values)] = (state(page)["selection"] or {}).get("area_mm2")
    # Custom sends every value: 30/180 with no blend radius is the Smooth region, not the server's default 'surface' preset.
    check("presets: Custom 30/180/0 equals Smooth, Custom 30/180/4 equals Surface (no hidden blend radius)", areas[("smooth", None)] == areas[("custom", ("30", "180", "0"))]
          and areas[("surface", None)] == areas[("custom", ("30", "180", "4"))] and areas[("smooth", None)] is not None
          and areas[("smooth", None)] != areas[("surface", None)], areas)
    check("presets part: no unexpected console errors", not errors_of(page, allowed=("status of 422",)), errors_of(page, allowed=("status of 422",)))
    page.close()


def part_tail_edit(browser):
    """A tail edit after Generate: the placement download describes the mapped build (review: major)."""
    if not SOFT.exists():
        print("SKIP tail edit: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser)
    soft_fit(page)
    s0 = generate_and_wait(page)
    top = float(page.input_value("#topTailLength"))
    page.fill("#topTailLength", f"{top + 5:.3f}")
    page.click("#regenerate")
    wait_until(page, DONE, 60)
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.verification !== null && s.generated_build_id !== s.proposal.build_id; }", 120)
    s = state(page)
    check("tail edit: the edited build maps and verifies (tails may differ from the fit)", s["verification"]["ok"] and s["downloads"] and s["generated_build_id"] != s0["generated_build_id"], s)
    if s["downloads"]:
        name, data = save(page, "#cadSavePlacement")
        document = json.loads(data)
        check("tail edit: the placement JSON names the mapped build and carries its tail lengths",
              name.startswith(s["generated_build_id"]) and document.get("build_id") == s["generated_build_id"] == s["placement_build_id"]
              and abs(document["design"]["tail"]["top_length_mm"] - (top + 5)) < 1e-6, (name, document.get("build_id"), document.get("design", {}).get("tail")))
    check("tail edit part: no unexpected console errors", not errors_of(page), errors_of(page))
    page.close()


def cylinder_stl(radius=20.0, height=30.0, segments=64) -> bytes:
    """A closed cylinder (binary STL, mm): its caps are rounded pads of many 2 mm sides."""
    triangles = []
    for i in range(segments):
        a0, a1 = 2 * math.pi * i / segments, 2 * math.pi * ((i + 1) % segments) / segments
        p0 = (radius * math.cos(a0), radius * math.sin(a0)); p1 = (radius * math.cos(a1), radius * math.sin(a1))
        triangles.append(((0, 0, height), (p0[0], p0[1], height), (p1[0], p1[1], height)))
        triangles.append(((0, 0, 0), (p1[0], p1[1], 0), (p0[0], p0[1], 0)))
        triangles.append(((p0[0], p0[1], 0), (p1[0], p1[1], 0), (p1[0], p1[1], height)))
        triangles.append(((p0[0], p0[1], 0), (p1[0], p1[1], height), (p0[0], p0[1], height)))
    body = b"".join(struct.pack("<12fH", 0, 0, 0, *t[0], *t[1], *t[2], 0) for t in triangles)
    return b"cylinder".ljust(80, b"\0") + struct.pack("<I", len(triangles)) + body


def part_rounded_base(browser):
    """A rounded pad: short sides are not listed; the Base edge tool picks a point and the fit uses an arc (review: major)."""
    path = Path(SCRATCH) / "cylinder_r20.stl"
    path.write_bytes(cylinder_stl())
    page = new_page(browser)
    open_cad(page)
    load(page, path)
    candidate(page, 1)
    s = state(page)
    sides = page.evaluate("() => [...document.querySelectorAll('input[name=cadSide]')].map(i => i.value)")
    check("rounded: a cap of 2 mm sides lists only Auto, with a note on the short sides", s["selection"] and s["selection"]["sides"] > 20 and sides == ["auto"]
          and "not listed" in page.inner_text("#cadSides") and "null" not in page.inner_text("#cadSides"), (s["selection"], sides, page.inner_text("#cadSides")))
    page.click('#cadTools label:has(input[value="edge"])')
    page.click('[data-cad-view="selection"]')
    page.wait_for_timeout(250)
    rim = page.evaluate("() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s; }")
    # A rim point of the selected cap (z = 0 or 30): pick the one the camera sees.
    point = None
    for z in (30.0, 0.0):
        screen = probe(page, [20.0, 0.0, z])
        if screen:
            page.mouse.click(screen[0], screen[1])
            page.wait_for_timeout(150)
            if isinstance(state(page)["side"], dict):
                point = state(page)["side"]["point_xyz"]
                break
    check("rounded: the Base edge tool on the rim picks a point base (the 'At the picked point' entry)", point is not None
          and page.evaluate("() => document.querySelector('input[name=cadSide][value=point]')?.checked === true"), (rim["side"], point))
    page.click('#cadTools label:has(input[value="grow"])')
    page.click("#cadFit"); settle(page)
    s = state(page)
    check("rounded: the fit with the picked point gives proposals (an arc exit)", s["proposals"] >= 1 and s["error"] is None, (s["proposals"], s["error"], page.inner_text("#cadStatus")))
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_rounded_base_1440.png")
    check("rounded part: no unexpected console errors", not errors_of(page), errors_of(page))
    page.close()


def plate_stl(outline, thickness=3.0) -> bytes:
    """A closed plate over a counter-clockwise outline (binary STL, mm): its top face is one planar pad."""
    cx, cy = sum(p[0] for p in outline) / len(outline), sum(p[1] for p in outline) / len(outline)
    triangles = []
    for i in range(len(outline)):
        a, b = outline[i], outline[(i + 1) % len(outline)]
        triangles.append(((cx, cy, thickness), (a[0], a[1], thickness), (b[0], b[1], thickness)))
        triangles.append(((cx, cy, 0.0), (b[0], b[1], 0.0), (a[0], a[1], 0.0)))
        triangles.append(((a[0], a[1], 0.0), (b[0], b[1], 0.0), (b[0], b[1], thickness)))
        triangles.append(((a[0], a[1], 0.0), (b[0], b[1], thickness), (a[0], a[1], thickness)))
    body = b"".join(struct.pack("<12fH", 0, 0, 0, *t[0], *t[1], *t[2], 0) for t in triangles)
    return b"plate".ljust(80, b"\0") + struct.pack("<I", len(triangles)) + body


def rounded_outline(width, height, radius, segments=12):
    points = []
    for cx, cy, start in ((width - radius, radius, -90), (width - radius, height - radius, 0), (radius, height - radius, 90), (radius, radius, 180)):
        for k in range(segments + 1):
            angle = math.radians(start + 90 * k / segments)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def part_rounded_corners(browser):
    """The user's corner tolerance (P5-diagonal-bus.md section 16): a 30 x 38 mm plate with 4 mm corners takes the full
    14 x 18 rectangle (252, its corners' margin within 0.5 mm off the face), mapped with field_corner_overhang; with 5 mm
    corners the masked 248 stays first (Field shape Rectangle's full 238 is no CAD option since section 26.16)."""
    page = new_page(browser)
    open_cad(page)
    four = Path(SCRATCH) / "rounded_plate_r4.stl"
    four.write_bytes(plate_stl(rounded_outline(30.0, 38.0, 4.0)))
    load(page, four)
    candidate(page, 1)
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 60)
    s = state(page)
    proposal = s["proposal"]
    check("corners: the 4 mm corners take the full 14 x 18 rectangle (252 taxels, not masked, Field only)",
          proposal and proposal["taxels"] == 252 and not proposal["masked"] and sorted((proposal["rows"], proposal["columns"])) == [14, 18]
          and proposal["containment"] == "field", proposal)
    s = generate_and_wait(page)
    rules = {row[0]: row[1] for row in page.evaluate("() => [...document.querySelectorAll('#cadVerifyTable tbody tr')].map(r => [r.dataset.rule, r.textContent])")}
    check("corners: Generate maps it with every record passing, field_corner_overhang among them", s["verification"] and s["verification"]["ok"]
          and "field_corner_overhang" in rules and "field_clearance" in rules, (s["verification"], sorted(rules)))
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_rounded_corners_r4_1440.png")
    five = Path(SCRATCH) / "rounded_plate_r5.stl"
    five.write_bytes(plate_stl(rounded_outline(30.0, 38.0, 5.0)))
    load(page, five)
    candidate(page, 1)
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 60)
    s = state(page)
    check("corners: with 5 mm corners the masked 248 stays first (coverage first)",
          s["proposal"] and s["proposal"]["taxels"] == 248 and s["proposal"]["masked"], s["proposal"])
    check("corners part: no console errors", not errors_of(page), errors_of(page))
    page.close()


def part_files(browser):
    """Empty, oversized and odd files; the browser reads what the server reads (review: minors).  Without the default
    part (its request held), as when nothing was loaded yet."""
    page = new_page(browser)
    open_cad(page, caps=None)
    empty = Path(SCRATCH) / "empty.stl"
    empty.write_bytes(b"\0" * 80 + struct.pack("<I", 0))
    page.set_input_files("#cadFile", str(empty))
    page.wait_for_timeout(400)
    s = state(page)
    check("files: a 0-facet STL is refused in the browser (no request, the drop zone stays)", s["error"] == "E_CLIENT_STL" and s["mesh"] is None and not page.surface
          and page.is_visible("#cadDrop") and "no facet" in page.inner_text("#cadStatus"), (s["error"], page.inner_text("#cadStatus")))
    large = Path(SCRATCH) / "large_1000001.stl"
    count = 1_000_001
    if not large.exists() or large.stat().st_size != 84 + 50 * count:
        record = struct.pack("<12fH", 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0)
        with open(large, "wb") as handle:
            handle.write(b"large".ljust(80, b"\0") + struct.pack("<I", count))
            for _ in range(count // 1000):
                handle.write(record * 1000)
            handle.write(record * (count % 1000))
    page.set_input_files("#cadFile", str(large))
    wait_until(page, "() => document.getElementById('cadStatus').textContent.includes('large_1000001.stl was not loaded')", 90)
    check("files: more than 1,000,000 facets is refused in the browser before anything is drawn or sent",
          "at most 1,000,000" in page.inner_text("#cadStatus") and not page.surface, page.inner_text("#cadStatus"))
    tricky = Path(SCRATCH) / "tricky_name.stl"
    lines = ["solid part vertex 1 2 3 vertex 4 5 6 vertex 7 8 9"]
    for triangle in struct.iter_unpack("<12fH", box_stl()[84:]):
        lines += ["facet normal 0 0 0", "outer loop"] + [f"vertex {triangle[3 + 3 * k]} {triangle[4 + 3 * k]} {triangle[5 + 3 * k]}" for k in range(3)] + ["endloop", "endfacet"]
    lines.append("endsolid part")
    tricky.write_text("\n".join(lines) + "\n", encoding="ascii")
    load(page, tricky)
    s = state(page)
    check("files: an ASCII solid named with 'vertex' words reads 12 facets in the browser and on the server", s["mesh"]["facets"] == s["mesh"]["browser_facets"] == 12
          and s["facet_mismatch"] is False, s["mesh"])
    check("files part: no unexpected console errors (no THREE NaN warning)", not errors_of(page, allowed=("status of 422",))
          and not any("NaN" in entry[1] for entry in page.logs), errors_of(page, allowed=("status of 422",)))
    page.close()


def part_no_webgl(playwright):
    if not SOFT.exists():
        return
    browser = playwright.chromium.launch(args=["--disable-3d-apis", "--disable-gpu"])
    page = new_page(browser)
    open_cad(page, caps=None)
    s = state(page)
    check("no WebGL: the view reports 'WebGL unavailable'", s["webgl"] == "unavailable" and "WebGL unavailable" in page.inner_text("#cadView"), s["webgl"])
    load(page, SOFT)
    candidate(page, 1)
    page.click("#cadFit"); settle(page)
    s = state(page)
    check("no WebGL: candidates and fit still work", s["selection"] and s["proposals"] >= 1, s)
    errors = errors_of(page, allowed=("WebGL", "THREE.WebGLRenderer"))
    check("no WebGL: no other console errors", not errors, errors)
    browser.close()


def main():
    global SERVED
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    SERVED = template_served()
    print(f"/api/default?template= {'served' if SERVED else 'not served (app.js keeps the default limits)'}", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=WEBGL_ARGS)
        parts = (part_rect_unchanged, part_default_cad, part_one_step, part_remove_model, part_clean_cad, part_soft, part_crank, part_crank_fill, part_no_rectangle_controls, part_field_soft, part_row_sides, part_review_fixes, part_tail_card, part_wrap_flexitac,
                 part_ascii_and_narrow, part_drop, part_template_roundtrip, part_columns, part_presets, part_tail_edit, part_rounded_base,
                 part_rounded_corners, part_files)
        chosen = [part for part in parts if len(sys.argv) < 2 or part.__name__ in sys.argv[1:]]
        for part in chosen:
            print(f"--- {part.__name__}", flush=True)
            try:
                part(browser)
            except Exception as error:  # noqa: BLE001 - report and continue
                check(f"{part.__name__} ran to completion", False, repr(error))
        browser.close()
        if len(sys.argv) < 2 or "part_no_webgl" in sys.argv[1:]:
            print("--- part_no_webgl", flush=True)
            try:
                part_no_webgl(p)
            except Exception as error:  # noqa: BLE001 - report and continue
                check("part_no_webgl ran to completion", False, repr(error))
    return summary()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
