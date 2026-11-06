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
  corner tolerance at every convex corner, section 24, 696 before section 26) on a leg with the narrow tip, not the cut corner's
  (at the default fill 0.5 the 68 mm leg, side 7, a 6.2 mm tip, 35 x 34; at fill 0.7 the 70 mm leg, side 6, 13.9 mm),
  Whole board the masked 563 of 30 x 33 (549 at fill 0.7; Field shape rectangle's 17 x 18 = 306 before section 26.16).
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
- Field only on the soft finger (side 0; the default containment): 708 taxels against the whole board's 480 (a masked
  50 x 12, 470 at fill 0.7; the 45 x 8 rectangle's 360 before masked fields took the rectangles' caps, P5-diagonal-bus.md section 21); the
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
  14 x 18 (252) and maps with field_corner_overhang; with 5 mm corners the masked 250 stays first (248 at fill 0.7).
- The template is app.js state (no fetch shim): CAD Generate -> Rectangular -> Generate -> CAD reports the template
  mismatch (never "verified"); the form's own Generate after a fit sends the default template.
- Form limits of the surface template: with /api/default?template= served (an app.py feature), Max columns goes to
  64 and a 58-column proposal builds and maps; without it, Max columns stops at 32.  A design outside the limits never
  overwrites the form.
- Selection presets: Custom angles send every value (no hidden blend radius); the Surface preset and list.
- The sensor on the part (the user's request of 2026-11-05; part_on_part): beside the registration the stacked card shows
  the part with the bottom FPC, the film and the top FPC draped on it and exploded, drawn from the map (its build id),
  the boards' outlines, the field and the taxels where the map puts them (to 5 um), every sheet facing out, the top FPC
  mirrored (its polyimide outward, the bottom FPC's copper), the art in the page's look on both sides (Diagram: copper
  at the taxels; Photo: ENIG gold), split beside the left figure at 1440, 1100 and 900 and stacked at 1000 and 390, a
  drag, the arrow keys, 0, a double click and Reset view, the wheel scrolling the page, Exploded and Assembled, hidden
  in Rectangular mode and empty after Remove model; on the masked crank and the curved soft-finger wrap too.
- A tail edit keeps the placement download in step with the mapped build; a rounded pad takes a picked point as
  the base; empty, oversized and odd ASCII files; double Generate submits once.
- The 3D view's look (part_view_look; the user's request of 2026-11-05: the sensor on the part's light and shade in every
  3D view, web/cad/studio.js): the default part's selected area at its home view mirrors the studio, tone mapped, in its
  orange about as light as before; the markers (the border, the base edge, the taxels, the hover, the handles) unlit in
  their own colours over the view's grey; at Fit its grey faces toward the key lighter than those turned from it, a faint
  soft reflection; the look again after a drag; light in dark mode; no texture left by three models; a lost context back
  with its studio; without half-float render targets one warning and the lights alone.
- The Library (part_library, 2026-11-05): every sensor of web/library/entries.json opens at ./?part=<id> from its
  shipped fit with its build id, the file note naming it; ./?part=<part>, an unknown id, the mode switch, the user's
  own file and Remove model (?part and the options it set dropped, the user's own edits kept), a click and Undo.
- A browser without Element.checkVisibility (part_older_browser, the review of 2026-11-06: iOS and iPadOS before 17.4):
  Rectangular's Generate and Gen by Surface's default build shown as with it, at 1440 and 390 px.
- The stacked card's foot (part_stack_feet, the verification of 2026-11-06): in both modes, at 1440 and 390 px, light and
  dark, the last row's figures rounded as the card's foot (17 px inside its 18 px), the others square.
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

from rp import DARK_CHOICE, DONE, RECT_URL, SCRATCH, SHOTS, URL, check, figure_controls, pin1_shapes, pin1_strokes, set_look, stacked_bare, stacked_pin1, summary, unfold, wait_until  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOFT = ROOT / "asset" / "soft_gripper_finger.stl"
CRANK = ROOT / "asset" / "crank_gripper" / "tip_left.stl"
WXAI = ROOT / "asset" / "Trossen-WidowXAI" / "WXAI-LEFT-Gripper-sock.stl"
DOWNLOADS = Path(SCRATCH) / "downloads"
WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
# A trace width and spacing (mm) at which the crank's masked proposal no longer routes (E_MASK_ROUTING).
MASK_BREAKING_TRACE = "0.127"
STATE = "() => JSON.parse(document.getElementById('cadState').textContent)"
IDLE = "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0; }"
# The sensor on the part (main.js 7b): drawn, or settled on a state with nothing to draw.
ON_PART_DRAWN = "() => JSON.parse(document.getElementById('cadState').textContent).on_part?.state === 'drawn'"
ON_PART_SETTLED = ("() => ['drawn', 'unavailable', 'failed', 'empty', 'off'].includes("
                   "JSON.parse(document.getElementById('cadState').textContent).on_part?.state)")
ON_PART_DRAWN_CHECK = "on part: drawn for the generated build"
# Files served in place of the page's own on every page of new_page: (URL pattern, content type, body); tools/browser/
# mutants.py's "cad" kind serves a mutated web/cad/drape.js through it.
ROUTES = []


def served(content_type, body):
    # A route handler of one argument (Playwright passes the request too to a handler that takes two).
    def handler(route):
        route.fulfill(status=200, content_type=content_type, body=body)
    return handler


def new_page(browser, width=1440, height=900, folded=False):
    context = browser.new_context(viewport={"width": width, "height": height}, accept_downloads=True)
    if not folded:
        unfold(context)
    page = context.new_page()
    for pattern, content_type, body in ROUTES:
        page.route(pattern, served(content_type, body))
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
    and its sensor built first.  ?probe: the sensor on the part's figure measured for the checks (main.js ON_PART_PROBE:
    its comparison with the map, its pixels read; a visitor's page does neither, the review of 2026-11-05)."""
    if not default_part:
        page.route(DEFAULT_PART, lambda route: route.fulfill(status=404, content_type="text/plain", body="not in this check"))
    page.goto(URL + "?probe#cad")
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
    figure = page.evaluate("() => [document.querySelector('#sensorOnPart canvas')?.hidden ?? true, document.querySelector('#sensorOnPart .on-part-note').textContent]")
    check("remove: the sensor on the part is gone with the part (its note asks for one), the registration stays",
          s["on_part"]["state"] == "empty" and figure == [True, "Load a part to see the sensor on it."]
          and page.evaluate("() => document.querySelectorAll('#stackedPreview .assembly-board').length") == 2, (s["on_part"], figure))
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
    model loaded has no face selected (the user's request of 2026-11-06), a click on its largest flat face selects it and
    Generate sensor builds it."""
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
          and s["verification"]["ok"] and s["quick"]["kind"] == "ok" and s["quick"]["text"].startswith("90 taxels in a 19 × 31 field") and not s["quick"]["generate"],
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
        check("one step: a model loaded has no face selected (the user's request of 2026-11-06), nothing generated, Generate sensor "
              "off, it and the status asking for the face",
              s["mesh"]["name"] == SOFT.name and s["selection"] is None and s["ops"] == 0 and s["generated_build_id"] == built and not s["quick"]["generate"]
              and s["quick"]["text"] == "Click the face the sensor goes on, then Generate sensor."
              and page.get_attribute("#cadStatus", "title").endswith(" facets. Click the face the sensor goes on."), (s["selection"], s["quick"]))
        candidate(page, 1); at_rest(page)
        s = state(page)
        check("one step: a click on its largest flat face (the soft finger's 3087.7 mm2) selects that face alone, nothing generated",
              s["selection"] and round(s["selection"]["area_mm2"], 1) == 3087.7 and s["ops"] == 1 and s["generated_build_id"] == built
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
    figure = page.evaluate("() => [document.querySelector('.stack-figure.is-on-part').checkVisibility(), document.getElementById('sensorOnPart').checkVisibility(),"
                           " getComputedStyle(document.querySelector('.stacked-review')).containerType]")
    check("rect: the stacked card as before: no sensor on the part beside it, no container to split it (2026-11-05)",
          figure == [False, False, "normal"] and info["state"]["on_part"]["state"] == "off", (figure, info["state"]["on_part"]))
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
    on_part_exact(page, "soft", s["generated_build_id"])
    on_part_aligned(page, "soft")
    on_part_film(state(page)["on_part"].get("pixels") or {}, "soft: Exploded home")
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
    faded = page.evaluate("() => getComputedStyle(document.getElementById('sensorOnPart')).opacity")
    check("soft: stale, the sensor on the part stays drawn, faded as the registration is", s["on_part"]["state"] == "drawn" and faded == "0.5", (s["on_part"]["state"], faded))
    page.click("#regenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.map_error !== null; }", 120)
    s = state(page)
    check("soft: a changed design reports E_SURFACE_PLACEMENT_MISMATCH: fit again", s["map_error"] == "E_SURFACE_PLACEMENT_MISMATCH"
          and "fit again" in page.inner_text("#cadStatus") and "fit again" in page.inner_text("#cadVerify"), (s["map_error"], page.inner_text("#cadStatus")))
    check("soft: the unmapped build leaves no sensor on the part (the earlier build's is gone)", s["on_part"]["state"] == "empty"
          and page.evaluate("() => document.querySelector('#sensorOnPart canvas').hidden"), s["on_part"])
    page.click("#cadGenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && s.verification !== null; }", 120)
    s = state(page)
    check("soft: Generate again restores the mapped, verified build", s["verification"]["ok"] and s["downloads"] and s["generated_build_id"] == build, s)
    on_part_exact(page, "soft, generated again", build)
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
          "(696 before section 26; 563 whole board, 549 at fill 0.7)",
          page.locator("#cadShape").count() == 0 and page.input_value("#cadContainment") == "field" and s["proposal"]["masked"]
          and s["proposal"]["taxels"] == 688 and s["proposal"]["containment"] == "field", s["proposal"])
    # At the default fill 0.5 (the user's of 2026-11-06) the 68 mm leg's field (side 7: 688 of 35 x 34, a 6.2 mm tip) holds within
    # 1 % of the most and has the narrowest tip, so the narrow-tip rule chooses that leg; at fill 0.7 it had been the 70 mm leg
    # (side 6: 688 of 34 x 34, a 13.9 mm tip), as test_field_fit's crank pins with the fill of before.
    check("crank: with the automatic exit the narrow tip wins (a leg, the 68 mm one at fill 0.5, side 7: a 6.2 mm tip, not the cut "
          "corner's; the 70 mm leg's 13.9 mm at fill 0.7)",
          s["proposal"]["base_side"] == 7 and s["proposal"]["tip_mm"] < 10.0, (s["proposal"]["base_side"], s["proposal"]["tip_mm"]))
    page.screenshot(path=f"{SHOTS}/cad_crank_fit_1440.png")
    page.locator("#cadWorkspace").screenshot(path=f"{SHOTS}/cad_crank_workspace_1440.png")
    page.select_option("#cadContainment", "board")
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 30)
    s = state(page)
    check("crank: Containment Whole board proposes the masked field of 563 taxels of 30 x 33 (549 at fill 0.7)", s["proposal"]["masked"] and s["proposal"]["taxels"] == 563
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
    on_part_exact(page, "crank fill", s["generated_build_id"])
    on_part_framed(page, "crank fill")
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
    check("field soft: Whole board fits the masked 50 x 12 (480; 470 at fill 0.7) across side 0 (the 45 x 8 rectangle, 360, before section 21)",
          s["proposal"] and s["proposal"]["containment"] == "board" and s["proposal"]["masked"]
          and (s["proposal"]["rows"], s["proposal"]["columns"], board) == (50, 12, 480) and s["fit_options"].get("containment") == "board", s["proposal"])
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
    check("field soft: Field only proposes at least 700 taxels (708, 59 x 12), 1.45 times the whole board's 480 or more (1.5 times its "
          "470 at fill 0.7, 1.9 times its rectangle before section 21)",
          proposal["containment"] == "field" and taxels >= 700
          and taxels >= 1.45 * board and s["fit_options"]["containment"] == "field" and s["fit_options"]["row_sides"] == "both", (proposal, board))
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
    check("field soft: the card gives its figures to its own precision, two decimals at most (the field's clearance 0.18 mm at fill "
          "0.5, 0.028157 mm at fill 0.7, 0.278157 before section 26.18 put the 708 0.25 mm nearer its tip, printed so before "
          "P5-diagonal-bus.md section 27.5)",
          "the taxel field on the surface (0.18 mm clear)" in card and re.findall(r"\d\.\d{3,}", card) == [], card)
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
    # The stacked view without its notes since the user's request of 2026-11-06 (they had said the tails' stacking, the Row
    # pins and the shared outline, which the proposal card and the map panel say): both boards drawn, and the build's Row
    # bus the proposal's (one outline down to the tail roots, the tails stacked).
    boxes = page.evaluate("() => [...document.querySelectorAll('#stackedPreview .assembly-board')].map(b => b.dataset.role)")
    bus = ((result.get("boards") or {}).get("row") or {}).get("construction", {}).get("row_bus") or {}
    check("field soft: the stacked view shows both boards, and the build's Row bus shares one outline down to the tail roots, its tails stacked",
          sorted(boxes) == ["columns", "rows"] and bus.get("tails") == "stacked" and bus.get("tail_position") == "centred"
          and abs(float(bus.get("shared_outline_below_field_mm", "nan")) - shared) < 1e-6, (boxes, bus.get("tails"), bus.get("shared_outline_below_field_mm"), shared))
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
    order = page.inner_text("#cadRowOrderNote") if page.query_selector("#cadRowOrderNote") else ""
    check("review: with Scan order Reverse the map's Row pins start at ROW_02 (from the pads)", (s["map_row_pin_order"] or [None])[0] == "ROW_02"
          and "Row pins 1–59 (from the pads" in order and ": ROW_02, ROW_04" in order, (s["map_row_pin_order"][:3] if s["map_row_pin_order"] else None, order))
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
        # The build's Row bus (the stacked view's note that named it went on 2026-11-06).
        bus = ((result.get("boards") or {}).get("row") or {}).get("construction", {}).get("row_bus") or {}
        check(f"row sides: the build's Row bus is the {side} side's, its Row tail centred under the field",
              bus.get("sides") == side and bus.get("tail_position") == "centred", {key: bus.get(key) for key in ("sides", "tail_position", "tails")})
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
    on_part_exact(page, "wrap", s["generated_build_id"])
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
# The 3D view's help line: shown or not, its text, the view's description, and the room between the view and Generate
# sensor's row (the help line's height while it shows, else none).
HELP_LINE = """() => { const help = document.getElementById('cadHelp'); const wrap = document.querySelector('.cad-view-wrap').getBoundingClientRect();
    const quick = document.getElementById('cadQuick').getBoundingClientRect();
    return {shown: help.checkVisibility(), text: help.textContent, described: document.getElementById('cadView').getAttribute('aria-describedby'),
            gap: Math.round((quick.top - wrap.bottom) * 10) / 10, height: Math.round(help.getBoundingClientRect().height * 10) / 10}; }"""


def part_clean_cad(browser):
    """CAD mode as the user sees it (no unfold()): the rectangular form hidden (CAD mode has its own steps) and the shared
    results (a rectangular build) hidden until CAD mode generates; the file, the view's tools and the sensor's line in
    sight, the rest under Advanced Customization (2026-11-02); opened, its basic options in sight, File details, Selection
    settings and More options folded; the 3D view's help line hidden, folded and open (2026-11-06: Generate sensor's row
    right under the view; the line the view's description still), shown with the border editor's keys only while the
    border is edited; after Fit and Generate on the soft finger the results in sight, step 7 one line
    ("all N checks pass") with its checks folded, the proposal's details folded; back in Rectangular mode the form."""
    if not SOFT.exists():
        print("SKIP clean CAD: asset/soft_gripper_finger.stl is absent")
        return
    page = new_page(browser, folded=True)
    open_cad(page)
    check("clean CAD: the rectangular form and the results (the rectangular default build) are hidden before a CAD build",
          not page.is_visible("#designForm") and not page.is_visible("#results") and not page.is_visible("#status"))
    quick = page.evaluate(HELP_LINE)
    check("clean CAD: folded, the 3D view's help line takes no row either (2026-11-06): hidden, Generate sensor's row right under the view, "
          "the line (the quick mode's) still the view's description", not quick["shown"] and quick["gap"] == 0 and quick["described"] == "cadHelp"
          and quick["text"].endswith("click the face the sensor goes on."), quick)
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
    help_line = page.evaluate(HELP_LINE)
    check("clean CAD: the 3D view's help line takes no row (the user's request of 2026-11-06): hidden, Generate sensor's row right "
          "under the view, the line (Advanced Customization's) still the view's description", not help_line["shown"] and help_line["gap"] == 0
          and help_line["described"] == "cadHelp" and help_line["text"].startswith("Drag: rotate")
          and help_line["text"].endswith("click it again to deselect it."), help_line)
    load(page, SOFT)
    candidate(page, 1)
    page.click("#cadEditBorder"); page.wait_for_timeout(200)
    editing = page.evaluate(HELP_LINE)
    page.click("#cadEditBorder"); page.wait_for_timeout(200)
    done = page.evaluate(HELP_LINE)
    check("clean CAD: while the border is edited the help line shows its keys in a row under the view, hidden again on Done editing",
          editing["shown"] and editing["text"].startswith("Editing the border:") and editing["gap"] == editing["height"] > 20
          and not done["shown"] and done["gap"] == 0 and done["text"].startswith("Drag: rotate"), (editing, done))
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
    corners the masked 250 stays first (248 at fill 0.7; Field shape Rectangle's full 238 is no CAD option since section 26.16)."""
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
    check("corners: with 5 mm corners the masked 250 of 18 x 14 stays first (coverage first; 248 at fill 0.7)",
          s["proposal"] and s["proposal"]["taxels"] == 250 and s["proposal"]["masked"], s["proposal"])
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


def on_part_exact(page, label, build_id):
    """The sensor on the part drawn for ``build_id`` where the map puts it: the outlines, the field and the taxels within
    5 um, every sheet over the field facing out, no tear, the bottom FPC above the part; returns on_part."""
    wait_until(page, ON_PART_SETTLED, 120)
    op = state(page)["on_part"]
    # tools/browser/mutants.py counts a run without this as invalid (nothing of the figure was checked).
    check(f"{ON_PART_DRAWN_CHECK} ({label})", op["state"] == "drawn" and op["build_id"] == build_id, {key: op.get(key) for key in ("state", "build_id", "note")})
    errors = [op.get("taxel_error_mm"), op.get("field_error_mm"), *(op.get("outline_error_mm") or {}).values()]
    check(f"{label}: the sensor on the part is drawn for the build, its outlines, field and taxels where the map puts them "
          "(within 0.005 mm), every sheet over the field facing out, no cell torn (stretch under 3), the bottom FPC above the part",
          op["state"] == "drawn" and op["build_id"] == build_id and len(errors) == 4 and all(isinstance(e, (int, float)) and e < 0.005 for e in errors)
          and op["front_out"] == 1 and op["max_stretch"] < 3 and op["min_clearance_mm"] > 0 and op["normal_agrees"],
          {key: op.get(key) for key in ("state", "build_id", "outline_error_mm", "field_error_mm", "taxel_error_mm", "front_out", "max_stretch",
                                        "min_clearance_mm", "normal_agrees", "explode", "note")})
    return op


def on_part_framed(page, label):
    """The sensor on the part framed whole as it opens, exploded and assembled: nothing drawn on the pane's outermost
    pixels (the crank's tip, the I2RT YAM recipe's part, ran off the pane: the review of 2026-11-05); no seam round the
    outlines over the part and the look's pixels (on_part_look), exploded and assembled."""
    exploded = state(page)["on_part"].get("pixels") or {}
    page.click("button[data-on-part-mode=assembled]")
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).on_part?.mode === 'assembled'", 10)
    assembled = state(page)["on_part"].get("pixels") or {}
    page.locator("#sensorOnPart").screenshot(path=f"{SHOTS}/cad_on_part_{label.replace(' ', '_')}_assembled.png")
    page.click("button[data-on-part-mode=exploded]")
    check(f"{label}: the sensor on the part framed whole at home, exploded and assembled (no drawn pixel on the pane's edge)",
          exploded.get("edge_px") == 0 and assembled.get("edge_px") == 0, (exploded, assembled))
    check(f"{label}: no seam round the outlines over the part, exploded and assembled", exploded.get("seam_px") == 0 and assembled.get("seam_px") == 0,
          (exploded.get("seam_px"), assembled.get("seam_px")))
    on_part_look(exploded, f"{label}: Exploded home", exploded=True)
    on_part_look(assembled, f"{label}: Assembled home", exploded=False)
    on_part_aligned(page, label)


# The left figure as it opens (app.js's exploded stack; the sensor on the part opens as it does, the user's decision of
# 2026-11-05): its tilt and spin and the screen directions (x right, y down) of the bottom FPC's SVG x and y and of the
# stack's normal by .assembly-camera's composed CSS transform (its computed matrix, rotateX(tilt) rotateZ(spin) scale:
# the image of each unit vector), and, through its perspective, the bottom FPC's field centre, a step either side of it
# along its SVG x and y (CENTRE_STEP_SHARE of the field's narrower side, drape.js's) and the top FPC's field centre (the
# turned-over board's own, mirrored about its flip axis), each a probe point read back by getBoundingClientRect.
CENTRE_STEP_SHARE = 0.05
LEFT_AXES = """(share) => {
  const pane = document.getElementById('stackedPreview');
  const lower = pane.querySelector('.assembly-board.is-lower'); const upper = pane.querySelector('.assembly-board.is-upper');
  const camera = pane.querySelector('.assembly-camera');
  if (!lower || !upper || !camera || pane.dataset.mode === 'plan') return null;
  const m = new DOMMatrix(getComputedStyle(camera).transform);
  const numbers = text => text.trim().split(/[\\s,]+/).map(Number);
  const centre = board => { const svg = board.querySelector('.assembly-face > svg'); const box = numbers(svg.getAttribute('viewBox'));
    const field = numbers(svg.getAttribute('data-active-region'));
    return {x: (field[0] + field[2] / 2 - box[0]) / box[2], y: (field[1] + field[3] / 2 - box[1]) / box[3], step: share * Math.min(field[2], field[3]) * board.offsetWidth / box[2]}; };
  const low = centre(lower); const high = centre(upper);
  const x = upper.classList.contains('flip-y') ? 1 - high.x : high.x; const y = upper.classList.contains('flip-x') ? 1 - high.y : high.y;
  const made = [];
  const dot = (board, at, transform) => { const node = document.createElement('div');
    node.style.cssText = `position:absolute; left:calc(${100 * at[0]}% - 0.5px); top:calc(${100 * at[1]}% - 0.5px); width:1px; height:1px; transform:${transform}; pointer-events:none;`;
    board.append(node); made.push(node); return node; };
  const at = [low.x, low.y]; const s = low.step;
  const dots = {centre: dot(lower, at, 'none'), x0: dot(lower, at, `translateX(${-s}px)`), x1: dot(lower, at, `translateX(${s}px)`),
    y0: dot(lower, at, `translateY(${-s}px)`), y1: dot(lower, at, `translateY(${s}px)`), top: dot(upper, [x, y], 'none')};
  const box = pane.getBoundingClientRect();
  const screen = Object.fromEntries(Object.entries(dots).map(([name, node]) => { const r = node.getBoundingClientRect();
    return [name, [r.left + r.width / 2 - box.left, r.top + r.height / 2 - box.top]]; }));
  made.forEach(node => node.remove());
  const degrees = Math.PI / 180;
  return {tilt_deg: Math.atan2(-m.m32, m.m33) / degrees, spin_deg: Math.atan2(-m.m21, m.m11) / degrees,
    axes: {x: [m.m11, m.m12], y: [m.m21, m.m22], n: [m.m31, m.m32]}, screen, orbit: pane.dataset.orbit || null};
}"""
AXES = ("x", "y", "n")


def screen_angle(vector):
    # The direction of a screen vector (x right, y down), degrees.
    return math.degrees(math.atan2(vector[1], vector[0]))


def angle_apart(a, b):
    return abs((a - b + 180) % 360 - 180)


def lens_axes(screen):
    """Through a figure's lens at the field's centre (LEFT_AXES's screen, onpart.js cameraRead's): the directions of the
    bottom FPC's SVG x and y and of the explode (its field centre to the top FPC's), degrees, and the field's
    foreshortening there (the smaller over the larger singular value of the 2 x 2 map from the field's x and y to the
    screen: the cosine of the tilt in a lens without perspective)."""
    sub = lambda a, b: [a[0] - b[0], a[1] - b[1]]
    x, y, n = sub(screen["x1"], screen["x0"]), sub(screen["y1"], screen["y0"]), sub(screen["top"], screen["centre"])
    a, c, b, d = x[0], x[1], y[0], y[1]
    total = a * a + b * b + c * c + d * d; det = abs(a * d - b * c)
    big = math.sqrt((total + math.sqrt(max(0.0, total * total - 4 * det * det))) / 2)
    return {"x": screen_angle(x), "y": screen_angle(y), "n": screen_angle(n), "foreshortening": det / (big * big) if big else 0.0}


def on_part_aligned(page, label):
    """The sensor on the part at its Exploded home as the left figure opens (the user's decision of 2026-11-05, 初始角度
    和左边的对齐; drape.js HOME_TILT_DEG and HOME_SPIN_DEG, app.js ORBIT_HOME): both at their homes, its tilt and spin the
    left figure's, and the screen directions of the bottom FPC's SVG x and y and of the stack's normal by each camera's
    rotation within 2 degrees of each other.  Through each lens at the field's centre the directions also bear each
    figure's own perspective (the 30 degree lens of both, the field's centre at its own place in each pane, the right's
    set by the part's framing): printed with the field's foreshortening in both, not checked.  Returns the camera read."""
    left = page.evaluate(LEFT_AXES, CENTRE_STEP_SHARE)
    op = state(page)["on_part"]
    camera = op.get("camera") or {}
    ok = bool(left and camera.get("axes")) and not op.get("moved")
    apart = {axis: round(angle_apart(screen_angle(camera["axes"][axis]), screen_angle(left["axes"][axis])), 3) for axis in AXES} if ok else None
    check(f"{label}: the sensor on the part opens as the left figure (both at their homes): its tilt and spin the left's (within 0.01 "
          "degrees), the screen directions of the bottom FPC's SVG x and y and of the stack's normal by each camera's rotation within 2 degrees",
          ok and abs(camera["tilt_deg"] - left["tilt_deg"]) <= 0.01 and abs(camera["spin_deg"] - left["spin_deg"]) <= 0.01
          and max(apart.values()) <= 2, {"left": left and {key: left[key] for key in ("tilt_deg", "spin_deg", "axes", "orbit")},
                                         "right": {key: camera.get(key) for key in ("tilt_deg", "spin_deg", "axes")}, "apart": apart, "moved": op.get("moved")})
    if ok and camera.get("screen"):
        ours, theirs = lens_axes(camera["screen"]), lens_axes(left["screen"])
        print(f"    {label}: through each lens at the field's centre (right - left, degrees): x {screen_angle_delta(ours['x'], theirs['x'])}, "
              f"y {screen_angle_delta(ours['y'], theirs['y'])}, explode {screen_angle_delta(ours['n'], theirs['n'])}; the field's foreshortening "
              f"{ours['foreshortening']:.3f} on the part, {theirs['foreshortening']:.3f} on the left (cos {left['tilt_deg']:.0f} degrees = "
              f"{math.cos(math.radians(left['tilt_deg'])):.3f} without perspective)", flush=True)
    return camera


def screen_angle_delta(a, b):
    return round((a - b + 180) % 360 - 180, 2)


def on_part_camera(page):
    """onpart.js cameraRead's tilt and spin (degrees) and whether the view is turned from its home."""
    op = state(page)["on_part"]
    camera = op.get("camera") or {}
    return camera.get("tilt_deg"), camera.get("spin_deg"), op.get("moved")


def split_rings(page, label):
    """The registration in the split's half-width pane, in the plan and the exploded view: its pin-1 rings right
    (rp.stacked_pin1: apart, neither taking in the other's triangle, each round its own, within the view), no caption
    (rp.stacked_bare; the user's request of 2026-11-06, "“Exploded 3D registration review…” 小字去掉") and the scene
    centred in the pane (the room the plan view kept at the pane's foot for the caption's two lines, the review of
    2026-11-05, gone with it).  Ends in the exploded view."""
    seen = {}
    for view in ("plan", "exploded"):
        page.click(f'[data-assembly-mode="{view}"]')
        page.wait_for_timeout(250)
        problems, _ = stacked_pin1(page)
        bare, pane = stacked_bare(page)
        pane.update(page.evaluate("""() => { const pane = document.getElementById('stackedPreview'); const box = pane.getBoundingClientRect();
            const scene = pane.querySelector(':scope > .assembly-scene').getBoundingClientRect();
            return {padding: getComputedStyle(pane).paddingBottom,
                    off_centre: Math.round(Math.abs((scene.top + scene.bottom) / 2 - (box.top + box.bottom) / 2) * 10) / 10}; }"""))
        seen[view] = (problems, bare, pane)
    check(f"{label}: the registration's pin-1 rings right in the plan and the exploded view, no caption in either, the scene "
          "centred in the pane", all(problems == [] and bare and pane["padding"] == "0px" and pane["off_centre"] <= 1
                                     for problems, bare, pane in seen.values()), seen)


def boxes(page, selectors):
    return page.evaluate("""(selectors) => selectors.map(s => { const n = document.querySelector(s); if (!n) return null;
        const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })""", selectors)


def part_on_part(browser):
    """The sensor on the part (the user's request of 2026-11-05): Gen by Surface's stacked card holds, beside the
    registration, the part with the bottom FPC, the film and the top FPC draped on it and exploded (web/cad/drape.js,
    onpart.js), drawn from the map; the default part as the page opens, folded, 1440 x 900."""
    page = new_page(browser, folded=True)
    open_cad(page, caps=None, default_part=True)
    wait_until(page, ON_PART_SETTLED, 120)
    s = state(page)
    # tools/browser/mutants.py counts a run without this as invalid (the figure was not drawn: nothing was checked).
    check(ON_PART_DRAWN_CHECK, s["on_part"]["state"] == "drawn" and s["on_part"]["build_id"] == s["generated_build_id"], s["on_part"])
    op = on_part_exact(page, "on part", s["generated_build_id"])
    check("on part: four layers (the part, the bottom FPC, the film, the top FPC; the Row FPC on top), each board's art "
          "a texture of its view box at 12 px/mm, the art's look rules ASCII and small",
          op["top_board"] == "rows" and op["bottom_board"] == "columns" and all(op["vertices"][k] > 100 for k in ("bottom", "film", "top"))
          and op["texture_px"]["row"] == [418, 1730] and op["art_css"]["ascii"] and 200 < op["art_css"]["bytes"] < 4096,
          {key: op.get(key) for key in ("top_board", "bottom_board", "vertices", "texture_px", "art_css")})
    routing = s["map_routing"]
    check("on part: each board's share on the surface as the map's (within 0.03)", routing and all(abs(op["on_surface"][k] - routing[k]) < 0.03 for k in ("row", "column")),
          (op["on_surface"], routing))
    check("on part: one rigid explode along the face's normal (13 mm or more per layer on the UMI finger), nested 0.25 mm",
          op["explode"] == "shift" and op["gap_mm"] > 13 and op["nest_mm"] == 0.25 and op["spread_deg"] < 10, op)
    ratio = lambda rgba: rgba[1] / max(1, rgba[0])
    faces = op["faces"] or {}
    # The first taxel is a corner one: at the default fill 0.5 its centre is 1.0 mm from the Row board's outline (1.2 mm at
    # fill 0.7), so at the home's distance the top FPC's mipmapped alpha there takes in the transparent texels beyond the
    # outline (146, not 255).  Its colour still says which side faces out; the boards' opaque faces at the taxels' centres
    # (taxel_median, every taxel's median: the pads of the bottom FPC, the top FPC's polyimide over its copper) say the same.
    taxels = ((op.get("pixels") or {}).get("taxel_median") or {})
    check("on part: from outside, the bottom FPC shows its copper side (ENIG gold at the first taxel and at the taxels' centres) "
          "and the top FPC, turned over, its polyimide (the copper seen through it: orange)",
          faces.get("bottom", [0, 0, 0, 0])[3] == 255 and faces.get("top", [0, 0, 0, 0])[3] >= 96
          and ratio(faces["bottom"]) > 0.75 and ratio(faces["top"]) < 0.65 and len(taxels.get("bottom") or []) >= 3
          and len(taxels.get("top") or []) >= 3 and ratio(taxels["bottom"]) > 0.75 and ratio(taxels["top"]) < 0.65, (faces, taxels))
    check("on part: Photo: the art's ENIG at a taxel (green 120 or more; the bare copper's is 106): the look's rules and paints reach the texture",
          op["look"] == "photo" and op["look_rgb"][1] >= 120 and op["look_rgb"][3] == 255, op["look_rgb"])
    pixels = op.get("pixels") or {}
    check("on part: the outlines antialiased (a quarter or more of the film's outline pixels drawn in part: alpha to coverage; "
          "an alpha test alone draws none so) and nothing on the pane's edge at home",
          (pixels.get("film_soft") or 0) >= 0.25 and pixels.get("film_outline_px", 0) > 100 and pixels.get("edge_px") == 0, pixels)
    # The review of 2026-11-05: the coverage's alpha had let the pane's grey through round every outline over the part
    # (a light seam, 191 such pixels exploded and 1,205 assembled); and the tails' end had come 18 px off the pane.
    margin = pixels.get("margin_px") or [0, 0, 0, 0]
    check("on part: no seam (no pixel the part covers whole left in part transparent by an outline over it), and framed "
          "with room: 4 % of the pane or more on every side, as much above the figure as below it (within a quarter)",
          pixels.get("seam_px") == 0 and min(margin) >= 0.04 * min(pixels.get("buffer") or [0])
          and abs(margin[1] - margin[3]) <= 0.25 * max(margin[1], margin[3]), pixels)
    # The look (the look lab of 2026-11-05: the film's flat black had read as a hole cut in the stack).
    on_part_look(pixels, "on part: Exploded home", exploded=True)
    # The user's decision of 2026-11-05: the Exploded home is the left figure's as it opens.
    home = on_part_aligned(page, "on part")
    layout = page.evaluate("""() => ({first: document.querySelector('.stacked-canvas').id, boards: document.querySelectorAll('#stackedPreview .assembly-board').length,
        rings: document.querySelectorAll('#stackedPreview .pin1-ring').length, labelled: document.querySelectorAll('svg[aria-label]').length,
        view: document.querySelectorAll('#cadView canvas').length, figure: document.querySelectorAll('#sensorOnPart canvas').length,
        touch: getComputedStyle(document.querySelector('#sensorOnPart canvas')).touchAction, reset: document.getElementById('onPartReset').disabled,
        cursor: getComputedStyle(document.querySelector('#sensorOnPart canvas')).cursor})""")
    check("on part: the registration's figure as before (the first lightbox, its two boards and pin-1 rings), still six labelled SVGs, "
          "one canvas each in the 3D view and the sensor on the part (a vertical swipe scrolls the page, a grab cursor as over "
          "the left figure), Reset view enabled",
          layout == {"first": "stackedPreview", "boards": 2, "rings": 2, "labelled": 6, "view": 1, "figure": 1, "touch": "pan-y", "reset": False,
                     "cursor": "grab"}, layout)
    left, right, card = boxes(page, ["#stackedPreview", "#sensorOnPart", ".stacked-review"])
    check("on part: 1440: the two figures side by side and level, each at least 340 px wide and 560 px tall",
          abs(left[1] - right[1]) <= 1 and right[0] >= left[0] + left[2] - 1 and min(left[2], right[2]) >= 340 and min(left[3], right[3]) >= 560, (left, right, card))
    split_rings(page, "on part: 1440")
    page.locator(".stacked-review").scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    page.locator(".stacked-review").screenshot(path=f"{SHOTS}/cad_on_part_1440.png")
    page.locator("#sensorOnPart").screenshot(path=f"{SHOTS}/cad_on_part_figure.png")
    # The look: Diagram's copper at every taxel's centre on both boards' copper sides; back in Photo.
    draws = op["draws"]
    page.click("button[data-look=diagram]")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent).on_part; return s.state === 'drawn' && s.look === 'diagram'; }", 60)
    op = state(page)["on_part"]
    check("on part: Diagram: drawn again in that look, the copper (#d9672b) at the taxels' centres on both boards' art (95 % or more)",
          op["draws"] == draws + 1 and op["copper_share"] and min(op["copper_share"].values()) >= 0.95, (op["draws"], op["copper_share"]))
    # Exploded and Assembled: Assembled clicked while the Photo drawing is under way, its art loading, holds once it is
    # drawn (show() had put back the mode of its start: the review of 2026-11-05).  The art's images held here
    # (HTMLImageElement.decode) until the check lets them go, after the click and its read: the click lands while show()
    # waits for them whatever the load (a hold of 800 ms had let a drawing on a loaded host end first, the review of
    # 2026-11-05).
    page.evaluate("""() => { const decode = HTMLImageElement.prototype.decode; window.__decode = decode;
        const gate = new Promise(open => { window.__releaseDecode = open; });
        HTMLImageElement.prototype.decode = function () { return decode.call(this).then(value => gate.then(() => value)); }; }""")
    page.click("button[data-look=photo]")
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).on_part?.state === 'drawing'", 10)
    page.click("button[data-on-part-mode=assembled]")
    during = state(page)["on_part"]["state"]
    page.evaluate("() => { HTMLImageElement.prototype.decode = window.__decode; window.__releaseDecode(); }")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent).on_part; return s.state === 'drawn' && s.look === 'photo'; }", 60)
    page.wait_for_timeout(300)
    op = state(page)["on_part"]
    pressed = page.evaluate("() => [...document.querySelectorAll('[data-on-part-mode]')].map(b => b.getAttribute('aria-pressed'))")
    check("on part: Assembled clicked while it is drawn again: once drawn, the layers on the part as the switch says (no legend under it "
          "since 2026-11-06)", during == "drawing" and op["mode"] == "assembled" and op["drawn_mode"] == "assembled" and pressed == ["false", "true"]
          and op["draws"] == draws + 2 and page.query_selector("#onPartLegend") is None, (during, op["mode"], op.get("drawn_mode"), pressed, op["draws"]))
    check("on part: Assembled: no seam round the boards' outlines on the part", (op.get("pixels") or {}).get("seam_px") == 0, op.get("pixels"))
    tilt, spin, moved = on_part_camera(page)
    check("on part: Assembled's home the left figure's spin, nearer the stack's normal (30 to 40 degrees off it: the field nearly face-on)",
          home.get("spin_deg") is not None and abs(spin - home["spin_deg"]) <= 0.01 and 30 <= tilt <= 40 and not moved, (tilt, spin, moved, home.get("spin_deg")))
    on_part_look(op.get("pixels") or {}, "on part: Assembled home", exploded=False)
    page.locator("#sensorOnPart").screenshot(path=f"{SHOTS}/cad_on_part_assembled.png")
    page.click("button[data-on-part-mode=exploded]")
    page.wait_for_timeout(200)
    again = state(page)["on_part"]
    check("on part: Exploded again, as drawn, no new drawing", again["drawn_mode"] == "exploded" and again["draws"] == draws + 2,
          again.get("drawn_mode"))
    check("on part: Exploded again: no contact shade, though Assembled made it (the layers float clear of the part)",
          (again.get("pixels") or {}).get("contact_px") == 0, {key: (again.get("pixels") or {}).get(key) for key in ("contact_px", "contact_max")})
    # Turning: a drag, Reset view, the arrow keys, 0, a double click; the wheel scrolls the page.
    box = page.locator("#sensorOnPart").bounding_box()
    centre = (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.move(*centre)
    page.mouse.down()
    page.mouse.move(centre[0] + 120, centre[1] + 50, steps=6)
    page.mouse.up()
    page.wait_for_timeout(200)
    turned = state(page)["on_part"]["moved"]
    dragged = on_part_camera(page)
    page.click("#onPartReset")
    page.wait_for_timeout(150)
    reset = state(page)["on_part"]["moved"]
    reset_camera = on_part_camera(page)
    page.focus("#sensorOnPart")
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(150)
    keyed = state(page)["on_part"]["moved"]
    left_key = on_part_camera(page)
    page.keyboard.press("0")
    page.wait_for_timeout(150)
    zero = state(page)["on_part"]["moved"]
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(150)
    up_key = on_part_camera(page)
    page.mouse.dblclick(*centre)
    page.wait_for_timeout(150)
    double = state(page)["on_part"]["moved"]
    double_camera = on_part_camera(page)
    check("on part: a drag turns it, Reset view brings it home, the arrow keys turn it, 0 and a double click bring it home",
          [turned, reset, keyed, zero, double] == [True, False, True, False, False], [turned, reset, keyed, zero, double])
    # The left figure's sense (app.js attachOrbit), the same drag over it: across turns the stack about its normal (the
    # spin), down tilts it toward the view from above; ArrowLeft raises the spin by 5 degrees, ArrowUp the tilt.
    stack = page.locator("#stackedPreview").bounding_box()
    middle = (stack["x"] + stack["width"] / 2, stack["y"] + stack["height"] / 2)
    page.mouse.move(*middle)
    page.mouse.down()
    page.mouse.move(middle[0] + 120, middle[1] + 50, steps=6)
    page.mouse.up()
    page.wait_for_timeout(200)
    orbit = [float(value) for value in (page.evaluate("() => document.getElementById('stackedPreview').dataset.orbit") or "nan,nan").split(",")]
    page.mouse.dblclick(*middle)
    page.wait_for_timeout(200)
    home_tilt, home_spin = home.get("tilt_deg"), home.get("spin_deg")
    sense = lambda value: (value > 0) - (value < 0)
    check("on part: turned as the left figure: the same drag lowers the spin and the tilt of both, ArrowLeft raises the spin by 5 degrees "
          "and ArrowUp the tilt by 5, as the left's keys, Reset view and a double click back at its home",
          home_tilt is not None and sense(dragged[1] - home_spin) == sense(orbit[1] - home_spin) == -1 and sense(dragged[0] - home_tilt) == sense(orbit[0] - home_tilt) == -1
          and abs(left_key[1] - home_spin - 5) <= 0.01 and abs(left_key[0] - home_tilt) <= 0.01 and abs(up_key[0] - home_tilt - 5) <= 0.01
          and abs(up_key[1] - home_spin) <= 0.01 and all(abs(read[0] - home_tilt) <= 0.01 and abs(read[1] - home_spin) <= 0.01 for read in (reset_camera, double_camera)),
          {"home": (home_tilt, home_spin), "dragged": dragged, "left figure dragged": orbit, "ArrowLeft": left_key, "ArrowUp": up_key, "reset": reset_camera,
           "double click": double_camera})
    before = page.evaluate("() => scrollY")
    page.mouse.move(*centre)
    page.mouse.wheel(0, 300)
    page.wait_for_timeout(300)
    after = page.evaluate("() => scrollY")
    check("on part: the wheel over it scrolls the page (no zoom)", after > before and not state(page)["on_part"]["moved"], (before, after))
    page.locator("#sensorOnPart").scroll_into_view_if_needed()
    page.focus("#sensorOnPart")
    for key in ("ArrowLeft", "ArrowLeft", "ArrowDown"):
        page.keyboard.press(key)
    page.wait_for_timeout(150)
    kept = [on_part_camera(page)]
    for mode in ("assembled", "exploded"):
        page.click(f"button[data-on-part-mode={mode}]")
        page.wait_for_timeout(300)
        kept.append(on_part_camera(page))
    page.click("#onPartReset")
    page.wait_for_timeout(150)
    kept.append(on_part_camera(page))
    page.click("button[data-on-part-mode=assembled]")
    page.wait_for_timeout(300)
    kept.append(on_part_camera(page))
    page.click("button[data-on-part-mode=exploded]")
    page.wait_for_timeout(300)
    kept.append(on_part_camera(page))
    check("on part: a turned view kept through Assembled and back (the camera where it was), Reset view at the Exploded home, "
          "Assembled from there its own home, and Exploded the left figure's again",
          home_tilt is not None and kept[0][2] and all(read == kept[0] for read in kept[1:3]) and abs(kept[0][1] - home_spin - 10) <= 0.01 and abs(kept[0][0] - home_tilt + 5) <= 0.01
          and kept[3] == kept[5] == (kept[3][0], kept[3][1], False) and abs(kept[3][0] - home_tilt) <= 0.01 and abs(kept[3][1] - home_spin) <= 0.01
          and not kept[4][2] and abs(kept[4][1] - home_spin) <= 0.01 and kept[4][0] < home_tilt, kept)
    # Widths: the card's container query (split at 720 px or more).
    for width, split in ((1100, True), (1000, False), (900, True), (390, False)):
        page.set_viewport_size({"width": width, "height": 900})
        page.wait_for_timeout(500)
        left, right = boxes(page, ["#stackedPreview", "#sensorOnPart"])
        overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
        placed = (abs(left[1] - right[1]) <= 1 and right[0] >= left[0] + left[2] - 1) if split else (right[1] >= left[1] + left[3] and abs(left[0] - right[0]) <= 1)
        check(f"on part: {width} px: {'side by side' if split else 'one under the other'}, no horizontal overflow, the figure "
              "still drawn", placed and overflow <= 0 and state(page)["on_part"]["state"] == "drawn" and right[2] > 0, (left, right, overflow))
        if split:
            split_rings(page, f"on part: {width} px")
        if width == 390:
            framed = []
            for mode in ("assembled", "exploded"):
                page.click(f"button[data-on-part-mode={mode}]")
                page.wait_for_timeout(400)
                framed.append((state(page)["on_part"].get("pixels") or {}).get("edge_px"))
            check("on part: 390 px: framed whole at home, assembled and exploded (no drawn pixel on the pane's edge)", framed == [0, 0], framed)
            on_part_aligned(page, "on part: 390 px")
            page.locator("#sensorOnPart").scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            page.screenshot(path=f"{SHOTS}/cad_on_part_390.png")
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(300)
    # Dark mode (the header's toggle on, 2026-11-06): the figure's pane stays a light lightbox, its drawing on it unchanged
    # (the canvas transparent over it).  The pane centred in the window (scrolled "if needed" from the 390 px run it had
    # stayed 6 px above the window's top since its controls went into its frame on 2026-11-06, its top rows black in the shot).
    set_look(page, "dark")
    page.evaluate("() => document.getElementById('sensorOnPart').scrollIntoView({block: 'center'})")
    page.wait_for_timeout(400)
    corners = pane_corners(page, "#sensorOnPart", f"{SHOTS}/cad_on_part_dark.png")
    set_look(page, "light")
    page.wait_for_timeout(200)
    check("on part: dark: the figure's pane stays light (its four corners' mean sRGB 220 or more), the figure drawn over it",
          len(corners) == 4 and min(corners) >= 220 and state(page)["on_part"]["state"] == "drawn", corners)
    # Rectangular mode: the registration alone at the card's width; back in Gen by Surface, drawn again at once.
    draws = state(page)["on_part"]["draws"]
    page.click("label:has(#modeRect)")
    page.wait_for_timeout(300)
    rect = page.evaluate("() => [document.querySelector('.stack-figure.is-on-part').checkVisibility(), document.getElementById('stackedPreview').getBoundingClientRect().width,"
                         " document.querySelector('.stacked-review').getBoundingClientRect().width]")
    off = state(page)["on_part"]["state"]
    check("on part: Rectangular mode hides it (off), the registration at the card's width", not rect[0] and rect[1] >= rect[2] - 4 and off == "off", (rect, off))
    page.click("label:has(#modeCad)")
    wait_until(page, ON_PART_SETTLED, 60)
    back = state(page)["on_part"]
    check("on part: back in Gen by Surface it is shown again, the same drawing (not drawn again)", back["state"] == "drawn" and back["draws"] == draws, back)
    check("on part: no console errors", not errors_of(page), errors_of(page))
    check("on part: no console warning of the figure's or three.js's (the studio's extensions exist here: no fallback, no shader edit missed)",
          not look_warnings(page), look_warnings(page))
    page.close()


def part_figure_controls(browser):
    """The figures' controls in their frames (the user's request of 2026-11-06), Gen by Surface with its default part as
    the page opens at 1440, 900, 390 and 360 px wide (side by side at 1440 and 900, one under the other below): each
    frame's controls in one row 12 px from its top left (the board cards' "3D view" and "2D view" and the zoom, the
    registration's "3D view" and "2D view", the sensor on the part's Exploded and Assembled, its title gone), Reset view
    12 px from both stacked figures' top right, 24 px targets, and at each view's home nothing drawn under them
    (rp.figure_controls): the finger's tall boards' 2D windows start under the controls (their band), the plan view's
    scene shrinks off them where it must (--plan-fit), the sensor on the part's canvas starts under its controls (its
    pane's 40 px band at the top, the pane's size as before); no layer legend under the board cards and no caption under
    the registration (2026-11-06)."""
    for width in (1440, 900, 390, 360):
        page = new_page(browser, width=width, height=900, folded=True)
        open_cad(page, caps=None, default_part=True)
        wait_until(page, ON_PART_SETTLED, 120)
        page.wait_for_timeout(400)
        problems, data = figure_controls(page)
        labels = {name: item["labels"] for name, item in data.items()}
        check(f"figure controls {width}: Gen by Surface: in one row 12 px in, Reset view top right on both stacked figures, 24 px targets, nothing "
              "drawn under them", problems == [] and labels == {"row": [["3D view", "2D view"], ["−", "+", "Reset"]], "column": [["3D view", "2D view"], ["−", "+", "Reset"]],
                                                              "registration": [["3D view", "2D view"]], "onPart": [["Exploded", "Assembled"]]}
              and len(data["registration"]["reset"]) == len(data["onPart"]["reset"]) == 1 and state(page)["on_part"]["state"] == "drawn", (problems, labels, data))
        pane = page.evaluate("""() => { const pane = document.getElementById('sensorOnPart').getBoundingClientRect(); const canvas = document.querySelector('#sensorOnPart canvas').getBoundingClientRect();
            return {pane: [Math.round(pane.width), Math.round(pane.height)], canvas: [Math.round(canvas.width), Math.round(canvas.height), Math.round(canvas.top - pane.top)],
                    bands: ['#rowPreview svg', '#columnPreview svg'].map(s => document.querySelector(s).style.paddingTop), title: document.querySelector('.on-part-title'),
                    legends: document.querySelectorAll('.layer-legend, #rowLegend, #columnLegend, .swatch').length}; }""")
        check(f"figure controls {width}: the sensor on the part's pane as before ({'560' if width > 980 else '480'} px tall), its canvas the 40 px under its "
              "controls' band; the finger's 2D views start 52 px down (under the controls' row); no layer legend under the board cards",
              pane["pane"][1] == (560 if width > 980 else 480)
              and pane["canvas"] == [pane["pane"][0], pane["pane"][1] - 40, 40] and pane["bands"] == ["52px", "52px"] and pane["title"] is None
              and pane["legends"] == 0, pane)
        page.click('[data-assembly-mode="plan"]'); page.wait_for_timeout(300)
        problems, data = figure_controls(page)
        fit = page.evaluate("() => document.querySelector('#stackedPreview .assembly-scene').style.getPropertyValue('--plan-fit')")
        check(f"figure controls {width}: the plan view's boards off its switch (its scene {fit or 'as styles.css sizes it'}), no Reset view",
              problems == [] and data["registration"]["reset"] == [] and (fit == "" or 0.9 < float(fit) < 1), (problems, fit, data["registration"]))
        bare = [stacked_bare(page)]
        if width == 900:
            page.locator(".stacked-review").screenshot(path=f"{SHOTS}/cad_figure_controls_plan_900.png")
        page.click('[data-assembly-mode="exploded"]'); page.wait_for_timeout(150)
        bare.append(stacked_bare(page))
        check(f"figure controls {width}: no caption under the registration in the plan or the exploded view (2026-11-06)", all(ok for ok, _ in bare), bare)
        page.click("#rowTab3d"); page.click("#columnTab3d"); page.wait_for_timeout(400)
        problems, data = figure_controls(page)
        check(f"figure controls {width}: the oblique views' tabs alone, nothing drawn under them", problems == [] and data["row"]["labels"] == [["3D view", "2D view"]], (problems, data["row"]))
        page.click("#rowTab2d"); page.click("#columnTab2d"); page.wait_for_timeout(150)
        if width in (1440, 390):
            page.locator(".stacked-review").screenshot(path=f"{SHOTS}/cad_figure_controls_stacked_{width}.png")
        check(f"figure controls {width}: no console errors", not errors_of(page), errors_of(page))
        page.close()


# A browser without the page's newest DOM API (the review of 2026-11-06: app.js's unguarded Element.checkVisibility, which
# Safari has only since 17.4 and Firefox since 106, had failed every build there, in both modes): deleted before the
# page runs.
OLDER_BROWSER = "(() => { delete Element.prototype.checkVisibility; })();"
# What a build shows: its status, both boards' 2D views (their view box and the band under the controls), the
# registration's boards and both DRC tables' rows; and whether the page has checkVisibility.
BUILT = """() => ({api: typeof Element.prototype.checkVisibility, status: document.getElementById('status').textContent.trim(),
  boards: ['rowPreview', 'columnPreview'].map(id => { const svg = document.querySelector('#' + id + ' > svg');
    return svg && svg.querySelector('.outline') ? [svg.getAttribute('viewBox'), svg.style.paddingTop] : null; }),
  stacked: document.querySelectorAll('#stackedPreview .assembly-board').length,
  drc: ['row', 'column'].map(key => document.querySelectorAll('#drc-' + key + ' tbody tr').length)})"""


def part_older_browser(browser):
    """A browser without Element.checkVisibility (OLDER_BROWSER: iOS and iPadOS before 17.4, Firefox before 106; the review
    of 2026-11-06), at 1440 and 390 px: Rectangular's build after Generate (13 rows) and Gen by Surface's default build
    each shown as in a browser with it: valid, both boards' 2D views as there (the same view box and the same band under
    the controls: the finger's tall boards start under them), the registration's two boards and both DRC tables; no
    console error."""
    for width in (1440, 390):
        for label, url in (("Rectangular", RECT_URL), ("Gen by Surface", URL)):
            seen = {}
            for older in (False, True):
                page = new_page(browser, width=width, height=900, folded=True)
                if older:
                    page.add_init_script(OLDER_BROWSER)
                page.goto(url)
                wait_until(page, DONE, 60)
                if url == URL:
                    wait_until(page, DEFAULT_SETTLED, 120)
                else:
                    page.fill("#rows", "13"); page.click("#generate"); page.wait_for_timeout(60)
                    wait_until(page, DONE, 60)
                page.wait_for_timeout(400)
                seen[older] = dict(page.evaluate(BUILT), build=state(page)["default_build"] if url == URL else None, errors=errors_of(page))
                page.close()
            new, old = seen[False], seen[True]
            same = {key: value for key, value in old.items() if key != "api"} == {key: value for key, value in new.items() if key != "api"}
            check(f"older browser {width}: {label}'s build without Element.checkVisibility shown as with it (valid, both boards' 2D views, "
                  "the registration's boards, both DRC tables, no console error)",
                  old["api"] == "undefined" and new["api"] == "function" and same and old["status"].startswith("Valid build")
                  and all(old["boards"]) and old["stacked"] == 2 and all(old["drc"]) and not old["errors"]
                  and old["build"] == ("done" if url == URL else None), (old, new))


# The stacked card's figures: each shown one's corners (top left, top right, bottom right, bottom left), how far its
# bottom is from the card's and the card's own bottom radius.
STACK_FEET = """() => { const card = document.querySelector('.stacked-review'); const box = card.getBoundingClientRect();
  return {card: getComputedStyle(card).borderBottomLeftRadius, theme: document.documentElement.dataset.theme || 'light',
    figures: [...card.querySelectorAll('.stack-figure > .stacked-canvas')].filter(node => node.getClientRects().length).map(node => {
      const s = getComputedStyle(node); const r = node.getBoundingClientRect();
      return {id: node.id, corners: [s.borderTopLeftRadius, s.borderTopRightRadius, s.borderBottomRightRadius, s.borderBottomLeftRadius],
              foot: Math.round(box.bottom - r.bottom)}; })}; }"""


def part_stack_feet(browser):
    """The stacked card's foot (the verification of 2026-11-06: the figures' light gradient, radius 0, reached the card's
    rounded foot with square corners standing out, most in dark): in Rectangular and Gen by Surface, at 1440 and 390 px,
    light and dark, the figures of its last row rounded as the card's foot (the card's 18 px less its 1 px edge), every
    other corner square: Rectangular's registration alone both; at 1440 px Gen by Surface's two side by side, the
    registration's bottom left and the sensor on the part's bottom right; at 390 px the sensor on the part under the
    registration both, the registration none."""
    seen = {}
    for scheme in ("light", "dark"):
        for width in (1440, 390):
            for label, url in (("Rectangular", RECT_URL), ("Gen by Surface", URL)):
                page = new_page(browser, width=width, height=900, folded=True)
                if scheme == "dark":
                    page.add_init_script(DARK_CHOICE)
                page.goto(url)
                wait_until(page, DONE, 60)
                if url == URL:
                    wait_until(page, DEFAULT_SETTLED, 120)
                page.wait_for_timeout(300)
                seen[(scheme, width, label)] = dict(page.evaluate(STACK_FEET), errors=errors_of(page))
                if scheme == "dark":
                    page.locator(".stacked-review").screenshot(path=f"{SHOTS}/cad_stack_feet_{'rect' if url == RECT_URL else 'cad'}_{width}_dark.png")
                page.close()
    for (scheme, width, label), got in seen.items():
        foot = f"{float(got['card'].rstrip('px')) - 1:g}px"
        if label == "Rectangular":
            want = {"stackedPreview": ["0px", "0px", foot, foot]}
        elif width == 1440:
            want = {"stackedPreview": ["0px", "0px", "0px", foot], "sensorOnPart": ["0px", "0px", foot, "0px"]}
        else:
            want = {"stackedPreview": ["0px"] * 4, "sensorOnPart": ["0px", "0px", foot, foot]}
        last = [figure for figure in got["figures"] if figure["foot"] <= 1]
        check(f"stack feet {label} {width} {scheme}: the last row's figures rounded as the card's foot ({foot}), the other corners square",
              got["card"] == "18px" and got["theme"] == scheme and {figure["id"]: figure["corners"] for figure in got["figures"]} == want
              and {figure["id"] for figure in last} == {key for key, corners in want.items() if corners[2] != "0px" or corners[3] != "0px"}
              and not got["errors"], got)

def look_warnings(page):
    # The figure's own warnings (onpart.js warnOnce: "On the part: ...") and three.js's ("THREE.").
    return [entry[1] for entry in page.logs if entry[0] == "warning" and (entry[1].startswith("On the part:") or "THREE." in entry[1])]


def pane_corners(page, selector, path):
    # The mean sRGB level of 8 x 8 device px at each corner of a pane, 6 px in (a screenshot of it, saved at ``path``).
    from PIL import Image
    page.locator(selector).screenshot(path=path)
    image = Image.open(path).convert("RGB")
    width, height = image.size
    means = []
    for x, y in ((6, 6), (width - 14, 6), (6, height - 14), (width - 14, height - 14)):
        values = list(image.crop((x, y, x + 8, y + 8)).tobytes())
        means.append(round(math.fsum(values) / len(values), 1))
    return means


def on_part_look(pixels, label, exploded):
    """The look's pixels (onpart.js pixels, ?probe; the look lab of 2026-11-05): the boards' colours, the edge bands drawn,
    the contact shade in Assembled only, and exploded the film a satin sheet (a gradient from its top to its foot), not
    the flat black that read as a hole."""
    ratio = lambda rgb: rgb[1] / max(1, rgb[0]) if rgb else 0
    median = pixels.get("board_median") or {}; taxels = pixels.get("taxel_median") or {}
    area = (pixels.get("buffer") or [0, 0])[0] * (pixels.get("buffer") or [0, 0])[1]
    check(f"{label}: the top FPC's polyimide amber (its median G/R under 0.65), the bottom FPC's ENIG pale at its taxels "
          "(their median G/R over 0.75), both mirroring the studio", ratio(median.get("top")) < 0.65 and ratio(taxels.get("bottom")) > 0.75
          and pixels.get("studio") is True, {key: pixels.get(key) for key in ("board_median", "taxel_median", "studio")})
    check(f"{label}: the edge bands drawn (they change {'0.4' if exploded else '0.1'} % of the pane or more)",
          (pixels.get("band_px") or 0) >= (0.004 if exploded else 0.001) * area, (pixels.get("band_px"), area))
    if exploded:
        on_part_film(pixels, label)
        check(f"{label}: no contact shade (the layers float clear of the part)", pixels.get("contact_px") == 0, pixels.get("contact_px"))
    else:
        check(f"{label}: the contact shade beside the stack's edge on the part (0.15 % of the pane or more darker by 8 levels "
              "or more than without it, the darkest by 20 or more)", (pixels.get("contact_px") or 0) >= 0.0015 * area and (pixels.get("contact_max") or 0) >= 20,
              {key: pixels.get(key) for key in ("contact_px", "contact_max")})


def on_part_film(pixels, label):
    """The film at the Exploded home (onpart.js pixels, ?probe): a satin black sheet catching its own lamp (FILM_LAMP; the
    user's of 2026-11-05, 再调一下你说的黑色压阻膜), a soft highlight at its top fading toward its foot, not the flat black
    that read as a hole, nor a glossy spot.  Its face's mean sRGB level in six bands from its top to its foot: above 45 on
    average, falling by 15 or more, its brightest band under 120.  At the left figure's home (the user's decision of
    2026-11-05) without the lamp (its studio's reflections at 0.8 then) the film had mirrored the room between the
    studio's back softbox and its sheen lamp, set for the home before: 44 to 38 on the UMI finger and 39 to 35 on the masked crank (85 to 54 and 64 to 47 at the home
    before; above 30, falling by 3 or more, was the check in between); with it 88 to 64, 74 to 47, 84 to 42 on the soft
    finger and 99 to 70, 88 to 46 and 95 to 62 on the Library's I2RT YAM 1 mm, Trossen WidowX AI 2 mm and 13.8 mm tapered
    UMI tip.  The flat unlit black of F/on-part-film-flat reads 6.3 in every band, the film without its lamp
    (F/on-part-film-unlit) 50 to 44 on the UMI finger, 45 to 40 on the crank and 49 to 38 on the soft finger."""
    bands = pixels.get("film_bands") or []
    level = math.fsum(bands) / len(bands) if bands and None not in bands else 0
    check(f"{label}: the film a satin black catching its lamp, not flat, not glossy: its face's mean sRGB level in six bands from its "
          "top to its foot above 45 on average, falling by 15 or more, the brightest under 120",
          len(bands) == 6 and level > 45 and bands[0] - bands[-1] >= 15 and max(bands) < 120,
          {"film_bands": bands, "mean": round(level, 1)})


HIDE_HALF_FLOAT = """(() => {
  const hidden = new Set(['EXT_color_buffer_float', 'EXT_color_buffer_half_float']);
  for (const proto of [WebGL2RenderingContext.prototype, WebGLRenderingContext.prototype]) {
    const get = proto.getExtension; const list = proto.getSupportedExtensions;
    proto.getExtension = function (name) { return hidden.has(name) ? null : get.call(this, name); };
    proto.getSupportedExtensions = function () { return (list.call(this) || []).filter(name => !hidden.has(name)); };
  }
})();"""
STUDIO_MEASURES = "() => performance.getEntriesByType('measure').filter(m => m.name === 'on-part studio').length"


def gl_invalid(page, since=0):
    # The browser's WebGL errors of a delete in the wrong context ("WebGL: INVALID_OPERATION: delete: object does not
    # belong to this context", and any other INVALID_OPERATION) logged since entry ``since``: the 3D view's context is
    # never lost here, so they are the figure's.
    return [entry[1] for entry in page.logs[since:] if "INVALID_OPERATION" in entry[1]]


def part_on_part_studio(browser):
    """The look's studio (onpart.js studioFor; the look lab of 2026-11-05): made once as the figure is made, and again
    when a lost WebGL context comes back (the figure drawn again, as before; what the lost context drew dropped, not
    disposed: no INVALID_OPERATION of a delete in the new context, the review of 2026-11-05, also after a drawing that
    disposes the new context's); on a device without half-float render targets, skipped with one warning, the sheets lit
    by the lights alone and still drawn.  The default part, folded."""
    page = new_page(browser, folded=True)
    open_cad(page, caps=None, default_part=True)
    wait_until(page, ON_PART_DRAWN, 120)
    before = page.evaluate(STUDIO_MEASURES)
    logged = len(page.logs)
    lost = page.evaluate("""async () => {
      const gl = document.querySelector('#sensorOnPart canvas').getContext('webgl2');
      const lose = gl && gl.getExtension('WEBGL_lose_context');
      if (!lose) return 'no WEBGL_lose_context';
      lose.loseContext();
      await new Promise(resolve => setTimeout(resolve, 400));
      const state = JSON.parse(document.getElementById('cadState').textContent).on_part.state;
      lose.restoreContext();
      return state;
    }""")
    page.wait_for_timeout(500)
    wait_until(page, ON_PART_DRAWN, 120)
    op = state(page)["on_part"]
    after = page.evaluate(STUDIO_MEASURES)
    check("on part studio: made once with the figure; the context lost (the figure unavailable), then back: the studio made "
          "again and the figure drawn again with it", before == 1 and lost == "unavailable" and after == 2 and op["state"] == "drawn"
          and (op.get("pixels") or {}).get("studio") is True, (before, lost, after, op["state"], (op.get("pixels") or {}).get("studio")))
    page.wait_for_timeout(300)
    restored = gl_invalid(page, logged)
    # A drawing on the restored context (the Diagram look): it disposes what that context drew, which is its own.
    draws = op["draws"]
    page.click("button[data-look=diagram]")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent).on_part; return s.state === 'drawn' && s.look === 'diagram'; }", 60)
    page.click("button[data-on-part-mode=assembled]")
    page.wait_for_timeout(300)
    again = state(page)["on_part"]
    invalid = gl_invalid(page, logged)
    check("on part studio: the lost context's sheets, part and studio dropped, not disposed: no INVALID_OPERATION of a delete "
          "logged after the context came back, nor after a drawing on it (Diagram, then Assembled)",
          not restored and not invalid and again["draws"] == draws + 1 and again["drawn_mode"] == "assembled", (len(restored), len(invalid), invalid[:3], again["draws"], draws))
    check("on part studio: no console error and no warning of the figure's", not errors_of(page) and not look_warnings(page), (errors_of(page), look_warnings(page)))
    page.close()
    page = new_page(browser, folded=True)
    page.add_init_script(HIDE_HALF_FLOAT)
    open_cad(page, caps=None, default_part=True)
    wait_until(page, ON_PART_SETTLED, 120)
    op = state(page)["on_part"]
    pixels = op.get("pixels") or {}
    warnings = look_warnings(page)
    ours = [text for text in warnings if text.startswith("On the part:")]
    # three.js's own note of the missing extension is expected here; nothing else.
    others = [text for text in warnings if not text.startswith("On the part:") and "EXT_color_buffer_float extension not supported" not in text]
    bands = pixels.get("film_bands") or []
    check("on part studio: no half-float render target: one warning of the figure's, no studio, the sheets still drawn (lit by the lights)",
          op["state"] == "drawn" and len(ours) == 1 and "half-float" in ours[0] and not others and pixels.get("studio") is False
          and page.evaluate(STUDIO_MEASURES) == 0 and len(bands) == 6 and None not in bands, (op["state"], warnings, pixels.get("studio"), bands))
    check("on part studio: no half-float: no console error", not errors_of(page), errors_of(page))
    page.locator("#sensorOnPart").screenshot(path=f"{SHOTS}/cad_on_part_no_studio.png")
    page.close()


def onpart_served():
    """web/cad/onpart.js as these checks serve it: tools/browser/mutants.py's (ROUTES) when it serves one, else the tree's."""
    for pattern, _content_type, body in ROUTES:
        if pattern.endswith("/onpart.js"):
            return body
    return (ROOT / "web" / "cad" / "onpart.js").read_text(encoding="utf-8")


# onpart.js's outlines' coverage (its patched() edit of three.js's alphatest_fragment) and its contact footprint.
COVERAGE_ANCHOR = 'const COVERAGE_EDITS = [["#include <alphatest_fragment>",'
CONTACT_FIELD = "function contactField(sheets, footprints, nest) {\n"
CONTACT_FIELDS = "() => window.__contactFields || 0"


def part_on_part_patches(browser):
    """The look's fallbacks (onpart.js patched(); the review of 2026-11-05), with onpart.js served altered: one of the
    shader texts it edits worded otherwise (the outlines' coverage, as a later three.js might word it), the figure still
    drawn, with exactly one warning of the figure's (once for every material it compiles), no seam and no console error
    (three.js's own alpha test then; a GLSL compile error would be one); and a stack without a contact footprint
    (contactField's null, counted) whose none is made once a drawing, not again at each Assembled, and made again for
    the next drawing.  The default part, folded."""
    body = onpart_served()
    assert body.count(COVERAGE_ANCHOR) == 1 and body.count(CONTACT_FIELD) == 1
    body = body.replace(COVERAGE_ANCHOR, COVERAGE_ANCHOR.replace("<alphatest_fragment>", "<alphatest_fragment_of_a_later_three>"))
    body = body.replace(CONTACT_FIELD, CONTACT_FIELD + "  window.__contactFields = (window.__contactFields || 0) + 1;\n  return null;\n")
    page = new_page(browser, folded=True)
    page.route("**/static/cad/onpart.js", served("text/javascript", body))
    open_cad(page, caps=None, default_part=True)
    wait_until(page, ON_PART_SETTLED, 120)
    op = state(page)["on_part"]
    pixels = op.get("pixels") or {}
    warnings = look_warnings(page)
    ours = [text for text in warnings if text.startswith("On the part:")]
    check(f"{ON_PART_DRAWN_CHECK}: with the outlines' coverage text not found, the figure still drawn, with one warning of the "
          "figure's naming it, nothing else of three.js's, no seam, no console error",
          op["state"] == "drawn" and len(ours) == 1 and "alphatest_fragment_of_a_later_three" in ours[0] and "the outlines' coverage" in ours[0]
          and len(warnings) == 1 and pixels.get("seam_px") == 0 and not errors_of(page), (op["state"], warnings, pixels.get("seam_px"), errors_of(page)))
    exploded = page.evaluate(CONTACT_FIELDS)
    counts = []
    for mode in ("assembled", "exploded", "assembled"):
        page.click(f"button[data-on-part-mode={mode}]")
        page.wait_for_timeout(300)
        counts.append(page.evaluate(CONTACT_FIELDS))
    shaded = (state(page)["on_part"].get("pixels") or {}).get("contact_px")
    draws = state(page)["on_part"]["draws"]
    page.click("button[data-look=diagram]")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent).on_part; return s.state === 'drawn' && s.look === 'diagram'; }", 60)
    redrawn = state(page)["on_part"]
    counts.append(page.evaluate(CONTACT_FIELDS))
    check("on part patches: no contact footprint: looked for on the first Assembled only, not again at the next Assembled, "
          "and again for the next drawing (Diagram, drawn assembled); no shade drawn",
          exploded == 0 and counts == [1, 1, 1, 2] and shaded == 0 and redrawn["draws"] == draws + 1 and redrawn["drawn_mode"] == "assembled",
          (exploded, counts, shaded, redrawn["draws"], draws, redrawn.get("drawn_mode")))
    check("on part patches: no console error, still one warning of the figure's", not errors_of(page) and len(look_warnings(page)) == 1,
          (errors_of(page), look_warnings(page)))
    page.close()


# The keys that turn the sensor on the part from its Exploded home (57, -20) to spin 45 and tilt 32, the direction of
# the Assembled home before the user's decision of 2026-11-05 (part_on_part_contact).
CONTACT_TURN = (("ArrowLeft", 13), ("ArrowDown", 5))


def part_on_part_contact(browser):
    """The contact shade along the stack's edge on a curved part (the review of 2026-11-05): the Trossen WXAI sock, its
    candidate #1, whose footprint ends a texel or so beyond the stack's edge band, so that a core outside the footprint
    only had left a light line 2 device px wide between the band and its shade.  In Assembled, the part's pixels along
    the stack's edge darkened by the shade (onpart.js pixels' contact_edge, ?probe), no seam; exploded, none.  Seen as
    the Assembled home before the user's decision of 2026-11-05 saw it (spin 45, tilt 32: CONTACT_TURN from the Exploded
    home, which Assembled keeps): from the new home, at the left figure's spin, less of the part along the stack's edge
    lies where the shade's core reaches, and the light line moves the share by little (0.32 with the fix, 0.29 without)."""
    if not WXAI.exists():
        print("SKIP on part contact: asset/Trossen-WidowXAI/WXAI-LEFT-Gripper-sock.stl is absent")
        return
    page = new_page(browser)
    open_cad(page)
    load(page, WXAI)
    candidate(page, 1)
    page.click("#cadFit"); settle(page)
    wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).preview_taxels !== null", 60)
    s = generate_and_wait(page)
    wait_until(page, ON_PART_SETTLED, 120)
    s = state(page)
    check(f"{ON_PART_DRAWN_CHECK}: the WXAI sock's candidate #1", s["on_part"]["state"] == "drawn" and s["on_part"]["build_id"] == s["generated_build_id"], s["on_part"])
    page.locator("#sensorOnPart").scroll_into_view_if_needed()
    page.focus("#sensorOnPart")
    for key, count in CONTACT_TURN:
        for _ in range(count):
            page.keyboard.press(key)
    page.wait_for_timeout(150)
    page.click("button[data-on-part-mode=assembled]")
    page.wait_for_timeout(300)
    pixels = state(page)["on_part"].get("pixels") or {}
    turned = on_part_camera(page)
    # Measured at 1440 x 900, so turned, at the default fill 0.5 (the user's of 2026-11-06; the field's electrodes narrower,
    # its footprint's edge farther in): 0.417 with the core outside the footprint only (the light line, catalogue's
    # M/web-on-part-contact-inner), 0.545 with it.  At fill 0.7: 0.29 and 0.46 (0.32 and 0.49 at the Assembled home before
    # the user's decision of 2026-11-05, 22 / -20 about the field's y), so the 0.4 of then let the light line through at 0.5.
    check("on part contact: the WXAI sock assembled, turned to spin 45 and tilt 32 (kept from Exploded): 0.48 or more of the "
          "part's pixels along the stack's edge darkened by the contact shade (no light line between the edge band and the shade), "
          "the shade drawn, no seam", turned[0] is not None and abs(turned[0] - 32) <= 0.01 and abs(turned[1] - 45) <= 0.01 and turned[2]
          and (pixels.get("contact_edge") or 0) >= 0.48 and (pixels.get("contact_px") or 0) > 0 and pixels.get("seam_px") == 0,
          {"camera": turned, **{key: pixels.get(key) for key in ("contact_edge", "contact_px", "contact_max", "seam_px")}})
    page.click("button[data-on-part-mode=exploded]")
    page.wait_for_timeout(300)
    pixels = state(page)["on_part"].get("pixels") or {}
    check("on part contact: exploded, no contact shade along the edge", pixels.get("contact_edge") == 0 and pixels.get("contact_px") == 0,
          {key: pixels.get(key) for key in ("contact_edge", "contact_px")})
    check("on part contact: no console errors", not errors_of(page), errors_of(page))
    page.close()


# The 3D view's look (viewer.js pixels, ?probe: main.js answers "fpc:view-look" with them), its studio's measures, and
# viewer.js COLORS of the markers in sRGB (drawn unlit: their own colours).
VIEW_LOOK = "() => { const detail = {}; document.dispatchEvent(new CustomEvent('fpc:view-look', {detail})); return detail.result ?? null; }"
VIEW_STUDIO_MEASURES = "() => performance.getEntriesByType('measure').filter(m => m.name === '3d-view studio').length"
MARKER_RGB = {"border": [30, 136, 229], "side": [194, 24, 91], "overlay": [26, 127, 60], "handles": [255, 255, 255]}
VIEW_GREY = [245, 245, 247]


def luma(rgb):
    """The sRGB luma (Rec. 709 weights) of an [r, g, b] (None for None)."""
    return None if rgb is None else round(0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2], 1)


def view_warnings(page):
    # The 3D view's own warnings (viewer.js through studio.js lookOf: "3D view: ...").
    return [entry[1] for entry in page.logs if entry[0] == "warning" and entry[1].startswith("3D view:")]


def view_drag(page, dx=120, dy=40, steps=10):
    """A left drag across the middle of the 3D view (OrbitControls turns it), the view then at rest."""
    page.locator("#cadView").scroll_into_view_if_needed()
    box = page.locator("#cadView").bounding_box()
    x, y = box["x"] + 0.55 * box["width"], box["y"] + 0.55 * box["height"]
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx, y + dy, steps=steps)
    page.mouse.up()
    page.wait_for_timeout(300)


def part_view_look(browser):
    """The 3D view's look (viewer.js, studio.js; the user's request of 2026-11-05: the sensor on the part's light and shade
    in every 3D view): the default part as the page opens (folded, ?probe), its selection framed face-on.  At the home view
    the part mirrors the studio and is tone mapped, the selected area keeps its orange about as light as before the look
    (its luma 160 to 190; 178.6 before: the old sun lay along the view), the markers are drawn unlit in their own colours
    (the border, the base edge, the taxels) over the view's grey; at Fit (the iso camera) the part is not flat (its grey
    faces toward the key, up and to the left, lighter by 50 levels or more than those turned from it, which stay out of the
    dark: luma 110 or more, and under the view's grey), and its reflection faint and soft (the studio lightens half its
    pixels or more, by 1 to 10 levels on average and 40 at most); the hover (the Base edge tool) and the handles (Edit
    border) in their colours; after a drag the look again (a software renderer draws a drag's frames without the studio's
    reflections: viewer.js SOFTWARE_RENDERER); the drawing stays light in dark mode; three models loaded leave no texture
    behind (renderer.info); a lost context comes back with its studio made again, nothing deleted in the wrong context;
    and on a device without half-float render targets one warning of the view's, the part still drawn, lit by the lights
    alone.  No console error, no warning of the view's otherwise."""
    page = new_page(browser, folded=True)
    open_cad(page, caps=None, default_part=True)
    wait_until(page, ON_PART_SETTLED, 120)
    page.locator("#cadView").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    home = page.evaluate(VIEW_LOOK) or {}
    page.locator("#cadView").screenshot(path=f"{SHOTS}/cad_view_look_home.png")
    selected = (home.get("classes") or {}).get("selected") or {}
    rgb = selected.get("rgb") or [0, 0, 0]
    check("view look: at the home view the part mirrors the studio and the tone mapping draws it (every pixel of the selected area "
          "changed by the tone mapping, the studio's reflection on half of them or more)",
          home.get("studio") is True and selected.get("px", 0) > 5000 and (selected.get("toned") or 0) >= 0.9
          and ((selected.get("sheen") or {}).get("share") or 0) >= 0.5, {"studio": home.get("studio"), "buffer": home.get("buffer"), "selected": selected})
    check("view look: the selected area in its orange at the home view, about as light as before the look (R over G over B, R - B 110 or "
          "more; luma 160 to 190, 178.6 before)", rgb[0] > rgb[1] > rgb[2] and rgb[0] - rgb[2] >= 110 and 160 <= luma(rgb) <= 190, (rgb, luma(rgb)))
    markers = home.get("markers") or {}
    drawn = {name: (markers.get(name) or {}).get("rgb") for name in ("border", "side", "overlay")}
    check("view look: the markers drawn unlit in their own colours (the border, the base edge, the taxels: viewer.js COLORS in sRGB, within "
          "a level) over the view's grey (#f5f5f7)",
          all(drawn[name] and max(abs(a - b) for a, b in zip(drawn[name], MARKER_RGB[name])) <= 1 for name in drawn)
          and home.get("background") == VIEW_GREY, (drawn, home.get("background")))
    page.click('[data-cad-view="iso"]')
    page.wait_for_timeout(300)
    fit = page.evaluate(VIEW_LOOK) or {}
    page.locator("#cadView").screenshot(path=f"{SHOTS}/cad_view_look_fit.png")
    base = (fit.get("classes") or {}).get("base") or {}
    toward, away = luma(base.get("toward")), luma(base.get("away"))
    check("view look: the part is not flat: at Fit its grey faces toward the key (up and to the left) lighter by 50 levels or more than "
          "those turned from it, those under the view's grey, these out of the dark (luma 110 or more)",
          toward is not None and away is not None and base.get("toward_px", 0) > 500 and base.get("away_px", 0) > 500
          and toward - away >= 50 and toward < luma(VIEW_GREY) - 3 and away >= 110, {"toward": toward, "away": away, "px": [base.get("toward_px"), base.get("away_px")]})
    sheen = base.get("sheen") or {}
    check("view look: a faint soft reflection on the part's grey at Fit: the studio lightens half its pixels or more, by 1 to 10 levels on "
          "average and 40 at most", (sheen.get("share") or 0) >= 0.5 and 1 <= (sheen.get("mean") or 0) <= 10 and 0 < (sheen.get("max") or 0) <= 40, sheen)
    page.click('[data-cad-view="selection"]')
    page.wait_for_timeout(300)
    # The hover: the Base edge tool over a side of the selection's outline (border_checks' way); the handles: Edit border.
    page.click("#cadCustomize > summary")
    page.wait_for_timeout(300)
    ends = side_ends(page)
    page.click('#cadTools label:has(input[value="edge"])')
    hovered = None
    for k, (start, end) in enumerate(ends):
        middle = probe(page, [(a + b) / 2 for a, b in zip(start, end)])
        if middle:
            page.mouse.move(middle[0] + 1, middle[1] + 1)
            page.wait_for_timeout(250)
            if state(page)["hover_edge"] is not None:
                hovered = k
                break
    hover = (page.evaluate(VIEW_LOOK) or {}).get("markers", {}).get("hover") or {}
    page.locator("#cadView").screenshot(path=f"{SHOTS}/cad_view_look_hover.png")
    # The hover's pink at its opacity 0.55 over the black part of the read: 0.55 x (255, 79, 163).
    check("view look: the hover drawn in its own colour, unlit (its pink at 0.55 over the read's black part, within 2 levels)",
          hovered is not None and hover.get("px", 0) > 50 and hover.get("rgb") and max(abs(a - b) for a, b in zip(hover["rgb"], [140, 43, 90])) <= 2,
          (hovered, hover))
    page.mouse.move(5, 5)
    page.click('#cadTools label:has(input[value="grow"])')
    page.click("#cadEditBorder")
    page.wait_for_timeout(400)
    handles = (page.evaluate(VIEW_LOOK) or {}).get("markers", {}).get("handles") or {}
    page.locator("#cadView").screenshot(path=f"{SHOTS}/cad_view_look_handles.png")
    check("view look: the border's handles drawn white, unlit", handles.get("px", 0) > 100 and handles.get("rgb") == MARKER_RGB["handles"], handles)
    page.click("#cadEditBorder")
    page.wait_for_timeout(200)
    # After a drag: the look again (the studio's reflection on the selected area, tone mapped).
    view_drag(page)
    after = (page.evaluate(VIEW_LOOK) or {}).get("classes", {})
    shown = [cls for cls in after.values() if cls.get("px", 0) > 2000]
    check("view look: after a drag the part drawn with its look again (the studio's reflection on half its pixels or more, tone mapped)",
          shown and all(((cls.get("sheen") or {}).get("share") or 0) >= 0.5 and (cls.get("toned") or 0) >= 0.9 for cls in shown),
          {name: (cls.get("px"), cls.get("sheen"), cls.get("toned")) for name, cls in after.items()})
    set_look(page, "dark")  # the header's toggle (2026-11-06)
    page.wait_for_timeout(300)
    dark = page.evaluate(VIEW_LOOK) or {}
    page.locator("#cadView").screenshot(path=f"{SHOTS}/cad_view_look_dark.png")
    check("view look: dark mode: the drawing stays light (the view's grey behind the part)", dark.get("background") == VIEW_GREY, dark.get("background"))
    set_look(page, "light")
    # Three models loaded (the asset meshes), then the first again: no texture left behind (the studio made once).
    memory = [(page.evaluate(VIEW_LOOK) or {}).get("memory")]
    for path in (SOFT, CRANK, SOFT):
        if path.exists():
            load(page, path)
            page.wait_for_timeout(300)
            memory.append((page.evaluate(VIEW_LOOK) or {}).get("memory"))
    check("view look: models loaded one after another leave no texture behind (renderer.info's textures the same after each; the studio "
          "made once, never with a model)", len(memory) >= 2 and all(entry and entry["textures"] == memory[0]["textures"] for entry in memory)
          and page.evaluate(VIEW_STUDIO_MEASURES) == 1, (memory, page.evaluate(VIEW_STUDIO_MEASURES)))
    # A lost context comes back: the studio made again, the lost one dropped (no delete in the wrong context).
    logged = len(page.logs)
    lost = page.evaluate("""async () => {
      const gl = document.querySelector('#cadView canvas').getContext('webgl2');
      const lose = gl && gl.getExtension('WEBGL_lose_context');
      if (!lose) return 'no WEBGL_lose_context';
      lose.loseContext();
      await new Promise(resolve => setTimeout(resolve, 400));
      lose.restoreContext();
      await new Promise(resolve => setTimeout(resolve, 600));
      return 'restored';
    }""")
    page.wait_for_timeout(300)
    again = page.evaluate(VIEW_LOOK) or {}
    lit = [cls for cls in (again.get("classes") or {}).values() if cls.get("px", 0) > 2000]
    check("view look: the context lost and back: the studio made again (its second measure) and mirrored, nothing deleted in the wrong "
          "context (no INVALID_OPERATION logged)", lost == "restored" and again.get("studio") is True and page.evaluate(VIEW_STUDIO_MEASURES) == 2
          and lit and all(((cls.get("sheen") or {}).get("share") or 0) >= 0.5 for cls in lit) and not gl_invalid(page, logged),
          (lost, again.get("studio"), page.evaluate(VIEW_STUDIO_MEASURES), [cls.get("sheen") for cls in lit], gl_invalid(page, logged)[:3]))
    check("view look: no console error and no warning of the view's", not errors_of(page) and not view_warnings(page), (errors_of(page), view_warnings(page)))
    page.close()
    # No half-float render target: one warning of the view's, the part drawn by the lights alone (no studio, no reflection).
    page = new_page(browser, folded=True)
    page.add_init_script(HIDE_HALF_FLOAT)
    open_cad(page, caps=None, default_part=True)
    wait_until(page, ON_PART_SETTLED, 120)
    page.locator("#cadView").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    plain = page.evaluate(VIEW_LOOK) or {}
    selected = (plain.get("classes") or {}).get("selected") or {}
    ours = view_warnings(page)
    check("view look: no half-float render target: one warning of the view's naming it, the part still drawn (its selected area, tone "
          "mapped) without the studio's reflection", len(ours) == 1 and "half-float" in ours[0] and plain.get("studio") is False
          and selected.get("px", 0) > 5000 and (selected.get("toned") or 0) >= 0.9 and (selected.get("sheen") or {}).get("share") == 0
          and page.evaluate(VIEW_STUDIO_MEASURES) == 0, (ours, plain.get("studio"), selected))
    check("view look: no half-float: no console error", not errors_of(page), errors_of(page))
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
    page.click("#cadGenerate")
    wait_until(page, "() => { const s = JSON.parse(document.getElementById('cadState').textContent); return s.busy.length === 0 && (s.verification !== null || s.map_error !== null); }", 120)
    wait_until(page, ON_PART_SETTLED, 60)
    s = state(page)
    note = page.evaluate("() => [document.querySelector('#sensorOnPart .on-part-note').textContent, document.querySelectorAll('#sensorOnPart canvas').length]")
    check("no WebGL: the sensor on the part says it needs WebGL (no canvas, no error of its own), the build maps",
          s["on_part"]["state"] == "unavailable" and note == ["This view needs WebGL, which is off in this browser.", 0] and s["verification"]["ok"], (s["on_part"], note))
    errors = errors_of(page, allowed=("WebGL", "THREE.WebGLRenderer"))
    check("no WebGL: no other console errors", not errors, errors)
    browser.close()


# -- the Library's sensors (library.html; the user's requests of 2026-11-05) ------------------------------------------
LIBRARY_ENTRIES = json.loads((ROOT / "web" / "library" / "entries.json").read_text(encoding="utf-8"))
# Step 1's file note: its text (its no-break space before 'mm' read as a space), its link, and its lines (the distinct
# tops of its text's boxes).
FILE_NOTE = """() => { const note = document.getElementById('cadFileNote'); const link = note.querySelector('a'); const range = document.createRange();
    range.selectNodeContents(note); const tops = new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top)));
    return {text: note.textContent.replace(/\u00a0/g, ' '), href: link?.getAttribute('href') || null, target: link?.target || null, rel: link?.rel || null, lines: tops.size,
            search: location.search, generate: Math.round(document.getElementById('cadQuickGenerate').getBoundingClientRect().bottom * 10) / 10}; }"""
OPTIONS = "() => ['cadPitch', 'cadFill', 'cadRotation'].map(id => document.getElementById(id).value)"
# The Library's sensors whose figure part_library compares with the left figure's (on_part_aligned): a gripper's tip
# whose part reaches far beside the stack, a curved sock, a tapered tip.
LIBRARY_ALIGNED = ("i2rt-yam-1mm", "trossen-widowx-ai-2mm", "umi-trap-tip13.8-2mm")


def open_part(page, query):
    """Gen by Surface at ./<query> (?part=<id>...), its Library sensor (or the default part) loaded and built."""
    page.surface.clear()
    page.goto("about:blank")  # a new document each time (the same address with a hash would only scroll)
    page.goto(URL + query)
    wait_until(page, DONE, 60)
    wait_until(page, DEFAULT_SETTLED, 180)
    page.wait_for_timeout(200)
    return state(page)


def part_library(browser):
    """./?part=<id> (web/cad/main.js; the Library's Open in Gen by Surface): every sensor of web/library/entries.json loads its
    part and builds its sensor from its shipped fit (fit_source shipped, no fit request; the entry's build id and mesh
    name), drawn on its part beside the stacked view (the two lines' integration of 2026-11-05), step 1's file note
    "From the Library: <label>" on one line with the Library in a new tab; ?part=<part> its
    2 mm sensor, ?part=<family> (umi-tapers) its default tip's (the review of 2026-11-05); an unknown id the UMI finger
    with a warning and ?part dropped; ?part kept across Rectangular and back (and ?part=<id>#rect loads on the first
    switch); the user's own file and Remove model drop ?part and put back the options the sensor set (pitch, fill,
    rotation), a fill the user changed kept, the note its own again, and so with a restored form too (the controls
    holding the sensor's values before main.js runs, as Firefox's reload leaves them; the review of 2026-11-05); on the
    WidowX 250 (eight disk operations) a click on the face and Undo behave, no request refused."""
    page = new_page(browser, folded=True)
    page.refused = []
    page.on("response", lambda response: page.refused.append((response.status, response.url)) if "/api/" in response.url and response.status >= 400 else None)
    misses, timings, figures, cut = [], [], [], []
    for identifier, variant in LIBRARY_ENTRIES["variants"].items():
        started = time.monotonic()
        s = open_part(page, f"?part={identifier}&debug&probe")
        timings.append((identifier, round(time.monotonic() - started, 1)))
        # The sensor on the part (fpc-stack-on-part, merged with the Library on 2026-11-05) drawn for the entry's build,
        # framed whole at its Exploded home (the left figure's since the user's decision of 2026-11-05; the Library's cards
        # will show it).
        wait_until(page, ON_PART_SETTLED, 60)
        figure = state(page)["on_part"]
        if (figure["state"], figure["build_id"]) != ("drawn", variant["build_id"]):
            figures.append([identifier, figure["state"], figure["build_id"], figure["note"]])
        elif (figure.get("pixels") or {}).get("edge_px") != 0:
            cut.append([identifier, (figure.get("pixels") or {}).get("edge_px"), (figure.get("pixels") or {}).get("margin_px")])
        if identifier in LIBRARY_ALIGNED:
            on_part_aligned(page, f"library: {identifier}")
            on_part_film(figure.get("pixels") or {}, f"library: {identifier}: Exploded home")
        s = state(page)
        note = page.evaluate(FILE_NOTE)
        mesh = LIBRARY_ENTRIES["parts"][variant["part"]]["mesh"]
        got = (s["default_part"], s["default_build"], s["fit_source"], (s["proposal"] or {}).get("build_id"), s["generated_build_id"], (s["mesh"] or {}).get("name"),
               note["text"], note["href"], note["target"], note["lines"], any(url.endswith("/api/surface/fit") for url in page.surface), (s["verification"] or {}).get("ok"))
        want = ("loaded", "done", "shipped", variant["build_id"], variant["build_id"], mesh["name"], f"From the Library: {variant['label']}",
                f"library.html#{identifier}", "_blank", 1, False, True)
        if got != want:
            misses.append([identifier, [pair for pair in zip(got, want) if pair[0] != pair[1]]])
    print("    timings:", ", ".join(f"{name} {seconds} s" for name, seconds in timings), flush=True)
    check(f"library: each of the {len(LIBRARY_ENTRIES['variants'])} sensors opens at ./?part=<id> from its shipped fit (no fit request), "
          "its build id and mesh the entry's, built and mapped (every check passes), the note 'From the Library: <label>' on one line, "
          "the Library in a new tab at it", misses == [], misses[:6])
    check(f"library: each of the {len(LIBRARY_ENTRIES['variants'])} sensors drawn on its part beside the stacked view (on_part drawn for its build)",
          figures == [], figures[:6])
    check(f"library: each of the {len(LIBRARY_ENTRIES['variants'])} sensors framed whole on its part at the Exploded home, 1440 px "
          "(no drawn pixel on the pane's edge)", cut == [], cut[:6])
    widest = max(LIBRARY_ENTRIES["variants"], key=lambda key: len(LIBRARY_ENTRIES["variants"][key]["label"]))
    open_part(page, f"?part={widest}")
    note = page.evaluate(FILE_NOTE)
    check(f"library: with the longest label ({widest}) Generate sensor's bottom at most 857.1 px (850.1 without the Library)",
          note["lines"] == 1 and note["generate"] <= 857.1, note)
    page.screenshot(path=f"{SHOTS}/cad_library_{widest}.png")
    # At 390 px (reported, not checked: the file bar's line there is a phone's): each label's note, as libraryNote writes it.
    page.set_viewport_size({"width": 390, "height": 900}); page.wait_for_timeout(200)
    wrapped = page.evaluate("""(labels) => { const note = document.getElementById('cadFileNote'); const kept = [...note.childNodes];
        const out = labels.filter(label => { note.replaceChildren('From the ', Object.assign(document.createElement('a'), {href: '#', textContent: 'Library'}), `: ${label.replace(/ mm$/, '\u00a0mm')}`);
          const range = document.createRange(); range.selectNodeContents(note);
          return new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size > 1; });
        note.replaceChildren(...kept); return out; }""", sorted({variant["label"] for variant in LIBRARY_ENTRIES["variants"].values()}))
    print(f"    the file note on two lines at 390 px: {', '.join(wrapped) or 'none'}", flush=True)
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(200)
    s = open_part(page, "?part=widowx-250")
    check("library: ?part=widowx-250 opens its 2 mm sensor", s["proposal"] and s["proposal"]["build_id"] == LIBRARY_ENTRIES["variants"]["widowx-250-2mm"]["build_id"]
          and page.evaluate(FILE_NOTE)["text"] == "From the Library: WidowX 250, 2 mm", s["proposal"])
    # A family's id, as library.html#<family> takes it: its default sensor (the tapered tips' 13.8 mm trapezoid).
    family = LIBRARY_ENTRIES["families"]["umi-tapers"]["default"]
    s = open_part(page, "?part=umi-tapers")
    note = page.evaluate(FILE_NOTE)
    check(f"library: ?part=umi-tapers opens the tapered tips' default ({family}) from its shipped fit, no warning",
          (s["proposal"] or {}).get("build_id") == LIBRARY_ENTRIES["variants"][family]["build_id"] and s["fit_source"] == "shipped"
          and s["status"]["kind"] != "warning" and note["text"] == f"From the Library: {LIBRARY_ENTRIES['variants'][family]['label']}"
          and note["href"] == f"library.html#{family}" and note["search"] == "?part=umi-tapers", (s["proposal"], s["fit_source"], s["status"], note))
    s = open_part(page, "?part=bogus&debug")
    # The warning comes once the build is mapped (main.js loadDefaultPart waits for the map on a 40 ms timer, after the
    # map's own status): settled, the page may still be drawing (with the sensor on the part, three.js in SwiftShader
    # held that timer back up to 1.2 s; the review of 2026-11-05), so it is waited for, up to 10 s, and its delay said.
    started = time.monotonic()
    try:
        wait_until(page, "() => JSON.parse(document.getElementById('cadState').textContent).status.kind === 'warning'", 10)
    except TimeoutError:
        pass
    print(f"    ?part=bogus: the warning {round(1000 * (time.monotonic() - started))} ms after the build settled", flush=True)
    s = state(page)
    note = page.evaluate(FILE_NOTE)
    check("library: ?part=bogus shows the UMI finger with a warning, ?part dropped (?debug kept as written), the note its own",
          (s["mesh"] or {}).get("name") == "UMI-Soft-Gripper-Finger.stl" and s["default_build"] == "done" and s["status"]["kind"] == "warning"
          and s["status"]["shown"] == "No library sensor is named bogus; the UMI finger is shown." and note["search"] == "?debug"
          and note["text"] == "or drag an STL file onto the 3D view below", (s["status"], note))
    s = open_part(page, "?part=widowx-250-1mm")
    page.click("label:has(#modeRect)"); page.wait_for_timeout(300)
    rect = page.evaluate("() => [location.search, location.hash]")
    page.click("label:has(#modeCad)"); page.wait_for_timeout(500)
    s = state(page)
    check("library: ?part survives Rectangular and back (the sensor still the Library's)", rect == ["?part=widowx-250-1mm", "#rect"]
          and page.evaluate(FILE_NOTE)["search"] == "?part=widowx-250-1mm" and s["fit_source"] == "shipped" and page.evaluate(OPTIONS) == ["1", "0.5", "none"], (rect, s["fit_source"]))
    page.surface.clear()
    page.goto("about:blank")
    page.goto(URL + "?part=widowx-250-1mm#rect")
    wait_until(page, DONE, 60)
    page.wait_for_timeout(300)
    idle = state(page)["default_part"]
    page.click("label:has(#modeCad)")
    wait_until(page, DEFAULT_SETTLED, 180)
    s = state(page)
    check("library: ?part=<id>#rect loads the sensor on the first switch to Gen by Surface", idle == "idle" and s["fit_source"] == "shipped"
          and s["proposal"]["build_id"] == LIBRARY_ENTRIES["variants"]["widowx-250-1mm"]["build_id"], (idle, s["fit_source"]))
    # The user's own file, and Remove model: ?part goes, the options the sensor set come back, the note is its own (the
    # 1 mm sensor's fill is the page's default 0.5 since the user's decision of 2026-11-06: its pitch and rotation).
    own = DOWNLOADS / "my-finger.stl"
    own.write_bytes(DEFAULT_PART_FILE.read_bytes())
    for leave in ("file", "remove"):
        open_part(page, "?part=widowx-250-1mm&debug#cad")
        before = page.evaluate(OPTIONS)
        if leave == "file":
            load(page, own)
        else:
            page.click("#cadRemove"); page.wait_for_timeout(300)
        note = page.evaluate(FILE_NOTE)
        check(f"library: {'the user’s own file' if leave == 'file' else 'Remove model'} drops ?part (?debug and the hash kept), puts back pitch, fill and "
              "rotation (2.0, 0.5, auto) and the note", before == ["1", "0.5", "none"] and page.evaluate(OPTIONS) == ["2.0", "0.5", "auto"]
              and note["search"] == "?debug" and page.evaluate("() => location.hash") == "#cad" and note["text"] == "or drag an STL file onto the 3D view below",
              (before, page.evaluate(OPTIONS), note))
    open_part(page, "?part=widowx-250-1mm")
    page.evaluate("() => { const fill = document.getElementById('cadFill'); fill.value = '0.6'; fill.dispatchEvent(new Event('input', {bubbles: true})); fill.dispatchEvent(new Event('change', {bubbles: true})); }")
    load(page, own)
    check("library: a fill the user changed stays (pitch and rotation back)", page.evaluate(OPTIONS) == ["2.0", "0.6", "auto"], page.evaluate(OPTIONS))
    # A restored form (the review of 2026-11-05): Firefox puts a reloaded page's control values back while it parses,
    # before main.js runs, so the sensor's pitch, fill and rotation are there already; here they are set when parsing
    # ends (readyState interactive, before the deferred module scripts).  The user's own file still puts back the defaults.
    restored = new_page(browser, folded=True)
    restored.add_init_script("""document.addEventListener('readystatechange', () => { if (document.readyState !== 'interactive') return;
        for (const [id, value] of [['cadPitch', '1'], ['cadFill', '0.5'], ['cadRotation', 'none']]) {
          const control = document.getElementById(id); if (control) control.value = value; } });""")  # about:blank (open_part goes there first) has none
    s = open_part(restored, "?part=widowx-250-1mm")
    before = restored.evaluate(OPTIONS)
    load(restored, own)
    check("library: with a restored form (the sensor's values in the controls before main.js runs) the user's own file still puts back "
          "pitch, fill and rotation (2.0, 0.5, auto)", s["fit_source"] == "shipped" and before == ["1", "0.5", "none"]
          and restored.evaluate(OPTIONS) == ["2.0", "0.5", "auto"], (s["fit_source"], before, restored.evaluate(OPTIONS)))
    check("library: no console errors with a restored form", not errors_of(restored), errors_of(restored)[:5])
    restored.close()
    page.reload(); wait_until(page, DONE, 60)
    # The WidowX 250's face is eight disk operations: a click on it (quick mode: that face alone) and Undo back to them.
    page.refused.clear()
    s = open_part(page, "?part=widowx-250-2mm")
    facets = s["selection"]["facets"]
    pick(page, s["candidates"]["flat"][0])
    clicked = state(page)
    page.click("#cadUndo"); settle(page)
    undone = state(page)
    check("library: on the WidowX 250 (eight disk operations) a click on the face and Undo behave, no request refused",
          s["ops"] == 8 and clicked["selection"] is not None and clicked["error"] is None and undone["ops"] == 8
          and undone["selection"]["facets"] == facets and not page.refused, (s["ops"], clicked["ops"], clicked["error"], undone["ops"], page.refused[:4]))
    check("library: no console errors", not errors_of(page), errors_of(page)[:5])
    page.close()


def main():
    global SERVED
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    SERVED = template_served()
    print(f"/api/default?template= {'served' if SERVED else 'not served (app.js keeps the default limits)'}", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=WEBGL_ARGS)
        parts = (part_rect_unchanged, part_default_cad, part_on_part, part_on_part_studio, part_on_part_patches, part_on_part_contact, part_view_look, part_one_step, part_remove_model, part_clean_cad, part_soft, part_crank, part_crank_fill, part_no_rectangle_controls, part_field_soft, part_row_sides, part_review_fixes, part_tail_card, part_wrap_flexitac,
                 part_ascii_and_narrow, part_drop, part_template_roundtrip, part_columns, part_presets, part_tail_edit, part_rounded_base,
                 part_rounded_corners, part_files)
        parts += (part_library,)  # the Library's ./?part=<id> (2026-11-05)
        parts += (part_figure_controls,)  # the figures' controls in their frames (2026-11-06)
        parts += (part_older_browser,)  # a browser without Element.checkVisibility (the review of 2026-11-06)
        parts += (part_stack_feet,)  # the stacked card's figures rounded at its foot (the verification of 2026-11-06)
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
