"""The Library's pictures and each sensor's art: every sensor of web/library/entries.json shot from the Library's own 3D
view (the user's requests of 2026-11-05: "卡片上的图为手指+传感器叠加", the cards show the finger with the sensor on it;
the seven grippers that are not UMI fingers shown whole, a sensor on both fingers, the jaws open; and "lib 点进去具体的每个
夹爪的时候, 那个图也做成可以三维旋转的", each sensor's page a 3D view to turn, its picture that view at its homes) into
web/library/shots/ with shots/manifest.json, and the generator's art of each sensor's two boards, which that view draws,
into web/library/art/<id>.json.gz (docs/LIBRARY_VIEW.md).  tools/library_write.py writes each variant's "image" and
"view" in entries.json from the manifest.

    FPC_PORT=18801 /tmp/fpc-browser-venv/bin/python tools/browser/library_shots.py            # every sensor
    ... library_shots.py --only widowx-250-1mm,i2rt-yam-2mm                                   # some; the others kept
    ... library_shots.py --check                                                              # shoot again, compare
    ... library_shots.py --check-generator umi-finray-2mm,umi-trap-tip5.8-2mm                 # Gen by Surface's figure
    ... library_shots.py --out /tmp/shots --sheet /tmp/shots/contact_sheet.png                # elsewhere, with a sheet

Against a running app.py (--port, else FPC_PORT) that serves this project (its entries.json and scenes/scenes.json must
be this tree's), in headless Chromium on SwiftShader (as cad_checks.py), one sensor at a time (app.py serves one surface
request at a time):
1. the art: one page per run, the generator's (index.html#rect).  For each sensor its fit's proposal #1 design is built
   by POST api/generate (the build id must be the entry's: else the fit is stale), and that page's app.js answers
   "fpc:board-art" {boards, px_per_mm: ART_PX_PER_MM, max_px: ART_MAX_PX} in its default look (Photo), as it answers
   Gen by Surface's figure: each board's eight keys (its copper and polyimide sides as SVG documents, the look's styles
   inlined), to which the build's board outline is added; the document (library_write.ART_FORMAT) is written by
   library_write.art_bytes() (canonical JSON, gzip with no name and time 0);
2. the pictures, from the Library's 3D view (web/cad/library_view.js: Gen by Surface's figure, web/cad/onpart.js, and for a
   gripper of scenes/scenes.json its stage, web/cad/library_stage.js), each sensor in a new browser context at VIEWPORT,
   DPR 2, the light scheme: library.html?probe=shoot#<id>, its entries.json and the sensor's art served by this tool
   (page.route: every variant's "view" as library_write writes it, the art fresh from step 1), so nothing need be
   written in web/ before the shoot and --check writes nothing; waited for until #libViewState says the view is drawn
   for the entry's build (?probe=shoot: the view leaves the drawing where the figure frames it, and a gripper's stage
   measures its numbers); the view's host (.lib-live) set to PANE_CSS, 640 x 400 CSS px (16:10): onpart.js's
   ResizeObserver gives its renderer a 1280 x 800 buffer and frames the scene again at that aspect;
3. at the Exploded home, then the Assembled home (the page's own Exploded | Assembled switch, then 0, which is Reset view
   on the view), the canvas alone is read in the frame it is drawn in (toDataURL in a requestAnimationFrame callback
   after the figure's own: three.js keeps no drawing buffer): a PNG with the canvas's alpha, the drawing alone on a
   transparent background; #libViewState must say that mode, drawn, not turned and not moved to the middle;
4. each drawing is checked whole (no drawn pixel on the buffer's edge: the part cut by the frame refuses the sensor),
   moved by whole pixels to the middle of its picture (centred(): frameView balances only the axis that binds, the
   height at 16:10, so across the width the UMI finger stood up to 72 px left of the middle, Unitree Dex1 assembled up
   to 85 px; its margins after the move are recorded) and written by Pillow as lossy WebP with lossless alpha (QUALITY,
   method 6): <id>.exploded.webp and <id>.assembled.webp at 1280 x 800, <id>.exploded.card.webp at 640 x 400 for the
   grid's cards (the Exploded drawing downscaled, Lanczos on premultiplied alpha: finer than the view drawn at 640 x 400).
   The visitor's view moves its drawing to the middle by the same whole pixels (a lens shift), so the page's live view
   stands where its picture stood;
5. for a gripper, the stage's numbers (#libViewState stage.numbers, docs/LIBRARY_VIEW.md) checked against the rules of
   scenes/scenes.json ("checks": rule_breaches()); a sensor whose numbers break one is refused.
manifest.json (library_write.SHOTS_FORMAT) holds for each sensor each file's path (relative to web/library/, as the
fits'), bytes and SHA-256, the entry's fit_sha256 and build_id it was shot from, the hashes of the figure's sources
(library_write.figure_sha256: onpart.js and the web/cad modules it imports) and of the Library view's own
(view_sha256: library_write.VIEW_SOURCES), both as the server served them, the look, the drawings' margins in px [left,
top, right, bottom], the art (its path, bytes, SHA-256, the SHA-256 of its document's canonical JSON, json_sha256, and
its build id) and, for a gripper, its stage (the scene's path, library_write.scene_sha256 of the scene and the rules,
and the numbers).  A sensor shot from another fit, or with art of another build, is the wrong sensor pictured, which
library_write --check, the site build and tests/test_library.py refuse; one shot from older figure or view sources is
only a warning there (the public CI runs no browser): re-shoot it here.

The same code gives the same bytes (SwiftShader draws the same pixels, Pillow's libwebp writes them the same way, the
stage's measures are a software raster): --check shoots again and compares every picture with the manifest's, the art's
document by json_sha256 (never its gzip bytes, which another zlib may write otherwise) with the manifest's and with the
art file's, and each gripper's stage (its scene hash and numbers), writing nothing.  The art goes into web/library/art/,
or with --out into an art/ folder beside that folder (the manifest's paths stay relative to their parent: shots/...,
art/...).  A full run removes the pictures and the art of sensors no longer listed; --only keeps the others' records.
--check-generator ID,... shoots those sensors in Gen by Surface instead (./?part=<id>, the figure on its own, the
fingertip: generator_shoot(), as the pictures were shot until the 3D view) and compares their three files with the
folder's: for the UMI finger and its tapered tips, whose Library view is the figure with no stage, every byte must agree
(Gen by Surface unchanged, and the Library's view equal to it); a gripper's picture is its whole scene there, so it
differs.  --sheet writes a contact sheet (PNG) of every sensor's Exploded card in the manifest, in the Library's order,
each in the page's light box.  About 6 to 10 s a sensor, the art 0.6 to 1.6 s of it (the 42 in 5.4 minutes on a shared
host, 2026-11-05, with the scenes of the design: 126 files, 3.70 MB; the first screen's cards 0.21 MB; the art 0.41 MB).

The pictures and the art are not committed on a branch that changes the figure, the view, the scenes or the Library's
sensors: shoot them once those are merged, with the final look, then run tools/library_write.py.  Needs Playwright and
Pillow (the checks' environment).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import library_write  # noqa: E402

LIBRARY = ROOT / "web" / "library"
OUT = LIBRARY / "shots"
WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
# The page's window and its pixel ratio (the figure's renderer takes the device's up to 2), and the view's pane: 16:10,
# 640 x 400 CSS px, a 1280 x 800 buffer.
VIEWPORT = {"width": 1440, "height": 900}
DPR = 2
PANE_CSS = (library_write.SHOT_SIZE[0] // DPR, library_write.SHOT_SIZE[1] // DPR)
MODES = ("exploded", "assembled")
# WebP: lossy at this quality, the alpha lossless (alpha_quality 100), method 6 (the slowest, smallest); the 42 sensors'
# 126 files came to 3.45 MB (the set's budget 8 MB), the grid's first screen (then the eight 'Start here.' cards; since
# the layout of 2026-11-06 the grid's 12 cards: grid_cards()) to 0.15 MB (its budget about 1 MB) on the provisional set
# of 2026-11-05: a 1280 x 800
# picture 25 to 42 KB, a card 14 to 23 KB (quality 95 about 4.5 MB, 80 about 2.5 MB, scaled from the WidowX 250's 2 mm
# sensor encoded at each: 90 keeps the film's satin gradient and the boards' traces in the card well inside the budget).
QUALITY = 90
TIMEOUT_S = 180
# The art's file names (art/<id>.json.gz) and each board's keys as app.js answers "fpc:board-art" (docs/LIBRARY_VIEW.md).
ART_NAME = re.compile(r"^[a-z0-9.-]+\.json\.gz$")
ART_KEYS = ("role", "physical_side", "view_box", "region", "active_outline", "px", "front", "back")
BOARD_KEYS = ("row", "column")
# The generator's page answers "fpc:board-art" (app.js sets detail.result to a promise; an empty request rejects).
ART_READY = """() => { const detail = {}; document.dispatchEvent(new CustomEvent('fpc:board-art', {detail}));
  if (!detail.result) return false; detail.result.catch(() => null); return true; }"""
# The answer as JSON text (the browser's own serialisation, read back by json.loads), or the reason it failed.
ART = """async ({boards, px_per_mm, max_px}) => { const detail = {boards, px_per_mm, max_px};
  document.dispatchEvent(new CustomEvent('fpc:board-art', {detail}));
  if (!detail.result) return {error: 'the page did not answer "fpc:board-art"'};
  try { return {text: JSON.stringify(await detail.result)}; } catch (error) { return {error: String(error && error.message || error)}; } }"""
# The Library view drawn for the entry's build ("drawn"), a state it will not leave ("failed: ..."), or not yet.
VIEW_DRAWN = """(build) => { const node = document.getElementById('libViewState'); if (!node || !node.textContent) return null;
  let s = null; try { s = JSON.parse(node.textContent); } catch (error) { return null; }
  if (s.state === 'drawn' && s.build_id === build) return 'drawn';
  return ['off', 'failed', 'unavailable', 'lost'].includes(s.state) ? `${s.state}: ${s.note}` : null; }"""
# The view's host out of the page's flow at PANE_CSS (its content box: the canvas fills it, inset 0); its size read back.
PANE = """([width, height]) => { const host = document.querySelector('.lib-live'); if (!host) return null;
  const style = {position: 'fixed', left: '0px', top: '0px', right: 'auto', bottom: 'auto', width: `${width}px`, height: `${height}px`,
    margin: '0', padding: '0', border: '0', 'box-sizing': 'content-box', 'aspect-ratio': 'auto', 'min-width': '0', 'min-height': '0',
    'max-width': 'none', 'max-height': 'none', 'border-radius': '0', transform: 'none', 'z-index': '2147483647'};
  for (const [key, value] of Object.entries(style)) host.style.setProperty(key, value, 'important');
  return [host.clientWidth, host.clientHeight]; }"""
BUFFER = """([width, height]) => { const canvas = document.querySelector('.lib-live canvas');
  return Boolean(canvas && !canvas.hidden && canvas.width === width && canvas.height === height); }"""
TWO_FRAMES = "() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(true))))"
# One mode at its home: the page's switch (its radio), two frames, then 0 (Reset view: onpart.js reset(), a render in
# the figure's requestAnimationFrame callback) and the canvas read in ours, registered after it in the same frame; the
# probe state as text.
SHOT = """async (mode) => {
  const host = document.querySelector('.lib-live');
  const canvas = host.querySelector('canvas');
  const frame = () => new Promise(resolve => requestAnimationFrame(resolve));
  const radio = document.querySelector(`input[name="libView"][value="${mode}"]`);
  if (!radio) return {error: 'no Exploded | Assembled switch on the page'};
  if (!radio.checked) radio.click();
  await frame(); await frame();
  host.dispatchEvent(new KeyboardEvent('keydown', {key: '0', bubbles: true, cancelable: true}));
  const url = await new Promise(resolve => requestAnimationFrame(() => resolve(canvas.toDataURL('image/png'))));
  return {url, buffer: [canvas.width, canvas.height], state: document.getElementById('libViewState').textContent};
}"""
# Gen by Surface (--check-generator): the sensor on the part drawn for the entry's build, its pane, one mode's read.
GENERATOR_STATE = "() => JSON.parse(document.getElementById('cadState').textContent)"
GENERATOR_DRAWN = """(build) => { let s = null;
  try { s = JSON.parse(document.getElementById('cadState')?.textContent || 'null'); } catch (error) { return null; }
  const op = s?.on_part; if (!op) return null;
  if (op.state === 'drawn' && op.build_id === build) return 'drawn';
  return ['unavailable', 'failed'].includes(op.state) ? `${op.state}: ${op.note}` : null; }"""
GENERATOR_PANE = """([width, height]) => { const host = document.getElementById('sensorOnPart');
  const style = {position: 'fixed', left: '0px', top: '0px', width: `${width}px`, height: `${height}px`, margin: '0', padding: '0',
    border: '0', 'box-sizing': 'content-box', 'min-width': '0', 'min-height': '0', 'max-width': 'none', 'max-height': 'none', 'z-index': '2147483647'};
  for (const [key, value] of Object.entries(style)) host.style.setProperty(key, value, 'important');
  return [host.clientWidth, host.clientHeight]; }"""
GENERATOR_BUFFER = """([width, height]) => { const canvas = document.querySelector('#sensorOnPart canvas');
  return Boolean(canvas && !canvas.hidden && canvas.width === width && canvas.height === height); }"""
GENERATOR_SHOT = """async (mode) => {
  const host = document.getElementById('sensorOnPart');
  const canvas = host.querySelector('canvas');
  const frame = () => new Promise(resolve => requestAnimationFrame(resolve));
  document.querySelector(`button[data-on-part-mode="${mode}"]`).click();
  await frame(); await frame();
  host.dispatchEvent(new KeyboardEvent('keydown', {key: '0', bubbles: true, cancelable: true}));
  const url = await new Promise(resolve => requestAnimationFrame(() => resolve(canvas.toDataURL('image/png'))));
  const op = JSON.parse(document.getElementById('cadState').textContent).on_part;
  return {url, buffer: [canvas.width, canvas.height], mode: op.mode, drawn_mode: op.drawn_mode, moved: op.moved, look: op.look,
          build_id: op.build_id, state: op.state};
}"""
# The stage's numbers (docs/LIBRARY_VIEW.md; their names frozen with the design of 2026-11-05).
STAGE_NUMBERS = ("jaw_gap_mm", "step_mm", "drape_step_mm", "face_tilt_deg", "visible_min", "opaque_max", "assembled_opaque",
                 "ghost_cover", "clearance_mm", "card_px", "band_css", "near_seen", "stacks_apart_px")


class ShotError(Exception):
    pass


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as reply:
        return reply.read()


def poll(page, script, argument, timeout):
    # The page's CSP refuses a string function (wait_for_function): its value polled with evaluate.
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = page.evaluate(script, argument)
        if value:
            return value
        page.wait_for_timeout(100)
    return None


def console_errors(page, errors: list, allowed=()) -> None:
    """Collect ``page``'s console errors and uncaught exceptions into ``errors``, but a 404 of a URL containing one of
    ``allowed``."""

    def seen(message):
        if message.type != "error":
            return
        where = (message.location or {}).get("url", "")
        if "status of 404" in message.text and any(part in where for part in allowed):
            return
        errors.append(message.text)

    page.on("console", seen)
    page.on("pageerror", lambda error: errors.append(str(error)))


# -- 1. the art: the generator's answer to "fpc:board-art" for the sensor's build ------------------------------------

def generate(url: str, design: dict) -> dict:
    """app.py's /api/generate reply for ``design`` (a busy server's 503 waited out, as the page does)."""

    body = json.dumps(design).encode("utf-8")
    for attempt in range(1, 61):
        request = urllib.request.Request(url + "api/generate", data=body, method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=300) as reply:
                return json.loads(reply.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 503 and attempt < 60:
                time.sleep(min(5.0, float(error.headers.get("Retry-After") or 1)))
                continue
            raise ShotError(f"api/generate answered HTTP {error.code}: {error.read()[:300]!r}") from None
    raise ShotError("api/generate stayed busy")


def art_page(browser):
    """A page of its own for the generator's (index.html#rect: Rectangular, no surface request), its console errors
    kept."""

    context = browser.new_context(viewport=VIEWPORT, color_scheme="light")
    page = context.new_page()
    page.art_errors = []
    console_errors(page, page.art_errors)
    return page


def open_art_page(page, url: str) -> None:
    """The generator's page loaded anew and settled (its own first build drawn: the network idle), once it answers
    "fpc:board-art".  app.js numbers its look's masks and clips over a page's life (lookSerial: 'lk-mask-7'), so each
    sensor's art is a fresh page's first answer, the same whichever sensors were asked for before it (--only, --check)."""

    page.goto("about:blank")  # (a goto of the same address with its #rect would only move to the fragment)
    page.goto(f"{url}index.html#rect", wait_until="networkidle")
    if not poll(page, ART_READY, None, 60):
        raise ShotError("the generator's page (index.html) does not answer \"fpc:board-art\"")


def art_document(page, url: str, identifier: str, variant: dict) -> dict:
    """The art document of one sensor (docs/LIBRARY_VIEW.md): its fit's design built, the art of that build as the
    generator's page, loaded anew, answers it first."""

    fit = json.loads((LIBRARY / variant["fit"]).read_text(encoding="utf-8"))
    reply = generate(url, fit["reply"]["proposals"][0]["design"])
    open_art_page(page, url)
    built = (reply.get("manifest") or {}).get("build_id")
    if built != variant["build_id"]:
        raise ShotError(f"the fit's design builds {built}, not the entry's {variant['build_id']}: the fit is stale (run tools/library_write.py)")
    boards = reply.get("boards") or {}
    if sorted(boards) != sorted(BOARD_KEYS):
        raise ShotError(f"api/generate gave the boards {sorted(boards)}, not {list(BOARD_KEYS)}")
    errors = len(page.art_errors)
    answer = page.evaluate(ART, {"boards": boards, "px_per_mm": library_write.ART_PX_PER_MM, "max_px": library_write.ART_MAX_PX})
    if "error" in answer or len(page.art_errors) > errors:
        raise ShotError(f"the generator's page gave no art: {answer.get('error') or page.art_errors[errors:][:3]}")
    art = json.loads(answer["text"])
    document = {"format": library_write.ART_FORMAT, "id": identifier, "build_id": variant["build_id"], "look": art.get("look"),
                "px_per_mm": library_write.ART_PX_PER_MM, "max_px": library_write.ART_MAX_PX, "boards": {}}
    for key in BOARD_KEYS:
        board = (art.get("boards") or {}).get(key) or {}
        if sorted(board) != sorted(ART_KEYS):
            raise ShotError(f"the {key} board's art has the keys {sorted(board)}, not {sorted(ART_KEYS)}")
        outline = boards[key].get("outline") or {}
        if not outline.get("points"):
            raise ShotError(f"api/generate gave the {key} board no outline")
        document["boards"][key] = dict(board, outline={"points": outline["points"], "cutouts": outline.get("cutouts") or []})
    if not isinstance(document["look"], str) or not document["look"]:
        raise ShotError(f"the art's look is {document['look']!r}")
    return document


def json_sha256(document: dict) -> str:
    """The SHA-256 of a document's canonical JSON (library_write.canonical_json): the art's json_sha256."""

    return hashlib.sha256(library_write.canonical_json(document).encode("ascii")).hexdigest()


def art_record(identifier: str, data: bytes, document: dict) -> dict:
    """The manifest's art record of an art file (``data``, written by library_write.art_bytes(``document``))."""

    return {"path": library_write.art_path(identifier), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "json_sha256": json_sha256(document), "build_id": document["build_id"]}


# -- 2. the pictures, from the Library's 3D view ---------------------------------------------------------------------

def rule_breaches(numbers: dict, checks: dict, see_through, explode_stacks=("sensor",)) -> list:
    """The rules of scenes/scenes.json's "checks" that a gripper's stage numbers break, one line each (none: []).

    The numbers (docs/LIBRARY_VIEW.md; the user's decision of 2026-11-06: one stack exploded, the sensor finger's, the
    near finger see-through in both views, its stack assembled): visible_min, the least visible share of any exploding
    layer's field in Exploded (rule layer_visible_min); opaque_max and assembled_opaque, the most of a layer's field the
    bodies and the fingers not drawn see-through cover in Exploded (every layer drawn there), and of stack 1's top FPC
    in Assembled (each below opaque_cover_max); clearance_mm's bodies and other_finger, each field's least distance to a
    body and to the other finger (at least clearance_min_mm) and its stacks, the exploded stack's to the other finger's
    stack in Exploded (at least stacks_apart_min_g of the jaws' gap, jaw_gap_mm, and stacks_apart_min_mm);
    stacks_apart_px, the two stacks' silhouettes apart on screen in Exploded (at least stacks_apart_min_px); card_px,
    stack 1's top FPC in the card (its shorter side at least card_min_px); ghost_cover, the most a see-through finger
    veils (at least ghost_cover_min where the scene draws one see-through, null where none); near_seen, the least share
    of the still stack's bottom FPC seen in Exploded and Assembled (at least near_seen_min; null exactly when
    ``explode_stacks``, the rules' explode_stacks, has the mate's stack exploding too)."""

    if not isinstance(numbers, dict):
        return [f"the stage gave no numbers ({numbers!r})"]
    missing = [name for name in STAGE_NUMBERS if name not in numbers]
    if missing:
        return [f"the stage's numbers lack {', '.join(missing)}"]
    clearance = numbers["clearance_mm"] if isinstance(numbers["clearance_mm"], dict) else {}

    def value(number):
        return number if isinstance(number, (int, float)) and not isinstance(number, bool) else None

    broken = []

    def rule(name, number, holds, text):
        threshold = checks.get(name)
        if value(threshold) is None:
            broken.append(f"{name}: scenes.json's rules have no such check")
        elif value(number) is None or not holds(number, threshold):
            broken.append(f"{name}: {text} {number!r} (rule {threshold})")

    rule("layer_visible_min", numbers["visible_min"], lambda got, rule_: got >= rule_, "a layer's field visible only")
    rule("opaque_cover_max", numbers["opaque_max"], lambda got, rule_: got < rule_, "a layer's field covered (Exploded)")
    rule("opaque_cover_max", numbers["assembled_opaque"], lambda got, rule_: got < rule_, "stack 1's top FPC covered (Assembled)")
    rule("clearance_min_mm", clearance.get("bodies"), lambda got, rule_: got >= rule_, "a field to a body, mm")
    rule("clearance_min_mm", clearance.get("other_finger"), lambda got, rule_: got >= rule_, "a field to the other finger, mm")
    gap = value(numbers["jaw_gap_mm"])
    rule("stacks_apart_min_g", clearance.get("stacks"), lambda got, rule_: gap is not None and got >= rule_ * gap,
         f"the exploded stack to the other finger's stack (the jaws' gap {gap} mm), mm")
    rule("stacks_apart_min_mm", clearance.get("stacks"), lambda got, rule_: got >= rule_, "the exploded stack to the other finger's stack, mm")
    rule("stacks_apart_min_px", numbers["stacks_apart_px"], lambda got, rule_: got >= rule_, "the stacks apart on screen, px")
    card = numbers["card_px"]
    rule("card_min_px", min(card) if isinstance(card, list) and card and all(value(side) is not None for side in card) else None,
         lambda got, rule_: got >= rule_, "stack 1's top FPC's shorter side in the card, px")
    if see_through:
        rule("ghost_cover_min", numbers["ghost_cover"], lambda got, rule_: got >= rule_, "a see-through finger veils")
    elif numbers["ghost_cover"] is not None:
        broken.append(f"ghost_cover: {numbers['ghost_cover']!r} where the scene draws no finger see-through")
    if "mate" in (explode_stacks or ()):
        if numbers["near_seen"] is not None:
            broken.append(f"near_seen: {numbers['near_seen']!r} with the mate's stack exploding")
    else:
        rule("near_seen_min", numbers["near_seen"], lambda got, rule_: got >= rule_, "the near stack's bottom FPC seen only")
    return broken


def shoot(browser, url: str, identifier: str, variant: dict, served: dict) -> dict:
    """{mode: the Library view's PNG at its home, "stage": the stage's numbers or None} of one sensor (a new context,
    closed after).  ``served``: {"entries": entries.json's text with every view, "art": this sensor's art file,
    "gripper": whether its part has a scene, "pictured": the shots/ files this tree has}."""

    context = browser.new_context(viewport=VIEWPORT, device_scale_factor=DPR, color_scheme="light")
    page = context.new_page()
    errors = []
    # A picture this tree does not have yet (a sensor never shot) is the page's placeholder after its 404.
    console_errors(page, errors, allowed=("/static/library/shots/",))
    page.route("**/static/library/entries.json", lambda route: route.fulfill(status=200, content_type="application/json", body=served["entries"]))
    art_name = Path(library_write.art_path(identifier)).name

    def art(route):
        if route.request.url.split("?")[0].endswith(f"/static/library/art/{art_name}"):
            route.fulfill(status=200, content_type="application/gzip", body=served["art"])
        else:
            route.continue_()

    page.route("**/static/library/art/**", art)
    build = variant["build_id"]
    try:
        page.goto(f"{url}library.html?probe=shoot#{identifier}")
        drawn = poll(page, VIEW_DRAWN, build, TIMEOUT_S)
        if drawn != "drawn":
            raise ShotError(f"the Library's 3D view is not drawn for build {build}: {drawn or 'timed out'}")
        size = page.evaluate(PANE, list(PANE_CSS))
        if size != list(PANE_CSS) or not poll(page, BUFFER, list(library_write.SHOT_SIZE), 30):
            raise ShotError(f"the view's pane is {size} CSS px, its buffer not {library_write.SHOT_SIZE}")
        page.evaluate(TWO_FRAMES)
        shots, state = {}, {}
        for mode in MODES:
            read = page.evaluate(SHOT, mode)
            if "error" in read:
                raise ShotError(f"{mode}: {read['error']}")
            state = json.loads(read["state"])
            offset = state.get("offset") or [0, 0]
            if (state.get("state"), state.get("build_id"), state.get("mode"), state.get("drawn_mode"), state.get("moved"), read["buffer"],
                    list(offset[:2])) != ("drawn", build, mode, mode, False, list(library_write.SHOT_SIZE), [0, 0]):
                raise ShotError(f"{mode}: not at its home as drawn, unmoved: {dict(state, stage=None)} buffer {read['buffer']}")
            shots[mode] = {"png": base64.b64decode(read["url"].split(",", 1)[1])}
        if bool(state.get("gripper")) != served["gripper"]:
            raise ShotError(f"the view {'drew no' if served['gripper'] else 'drew a'} gripper's scene (its part {variant['part']})")
        stage = state.get("stage") or None
        if served["gripper"]:
            shots["stage"] = (stage or {}).get("numbers")
            if not shots["stage"]:
                raise ShotError(f"the stage measured no numbers (#libViewState stage {stage!r}): is the page's ?probe=shoot honoured?")
        elif stage:
            raise ShotError(f"a stage on a sensor with no scene: {stage!r}")
        else:
            shots["stage"] = None
    finally:
        context.close()
    if errors:
        raise ShotError(f"console errors: {errors[:3]}")
    return shots


def generator_shoot(browser, url: str, identifier: str, variant: dict) -> dict:
    """{mode: Gen by Surface's figure's PNG at its home} of one sensor (a new context, closed after): ./?part=<id>, the
    sensor on the part drawn for the entry's build from its shipped fit, the pane set to PANE_CSS, each mode's button and
    0, the canvas read in the frame it is drawn in (the pictures' shoot until the Library's 3D view, kept for
    --check-generator)."""

    context = browser.new_context(viewport=VIEWPORT, device_scale_factor=DPR, color_scheme="light")
    page = context.new_page()
    errors = []
    console_errors(page, errors)
    try:
        page.goto(f"{url}?part={identifier}")
        drawn = poll(page, GENERATOR_DRAWN, variant["build_id"], TIMEOUT_S)
        if drawn != "drawn":
            raise ShotError(f"the sensor on the part is not drawn for build {variant['build_id']}: {drawn or 'timed out'}")
        source = page.evaluate(GENERATOR_STATE)["fit_source"]
        if source != "shipped":
            raise ShotError(f"the sensor was built from a fit of its own ({source}), not the shipped one")
        size = page.evaluate(GENERATOR_PANE, list(PANE_CSS))
        if size != list(PANE_CSS) or not poll(page, GENERATOR_BUFFER, list(library_write.SHOT_SIZE), 30):
            raise ShotError(f"the figure's pane is {size} CSS px, its buffer not {library_write.SHOT_SIZE}")
        page.evaluate(TWO_FRAMES)
        shots = {}
        for mode in MODES:
            read = page.evaluate(GENERATOR_SHOT, mode)
            if (read["state"], read["build_id"], read["mode"], read["drawn_mode"], read["moved"], read["buffer"]) \
                    != ("drawn", variant["build_id"], mode, mode, False, list(library_write.SHOT_SIZE)):
                raise ShotError(f"{mode}: not at its home as drawn: {dict(read, url=None)}")
            shots[mode] = {"png": base64.b64decode(read["url"].split(",", 1)[1]), "look": read["look"]}
    finally:
        context.close()
    if errors:
        raise ShotError(f"console errors: {errors[:3]}")
    return shots


def encode(shots: dict) -> tuple:
    """({kind: WebP bytes}, {mode: margins px}) of one sensor's drawings, each checked whole and centred."""

    from PIL import Image

    files, margins = {}, {}
    for mode in MODES:
        image = Image.open(io.BytesIO(shots[mode]["png"]))
        image.load()
        width, height = image.size
        if (image.mode, image.size) != ("RGBA", library_write.SHOT_SIZE):
            raise ShotError(f"{mode}: the canvas read as {image.mode} {image.size}")
        box = image.getchannel("A").getbbox()
        if box is None:
            raise ShotError(f"{mode}: nothing drawn")
        drawn = [box[0], box[1], width - box[2], height - box[3]]
        if min(drawn) == 0:
            raise ShotError(f"{mode}: the drawing reaches the frame's edge (margins {drawn} px): the part is cut")
        image, margins[mode] = centred(image, box, drawn)
        files[mode] = webp(image)
        if mode == "exploded":
            files["card"] = webp(image.resize(library_write.CARD_SIZE, Image.LANCZOS))
    for kind, (_, size) in library_write.SHOT_KINDS.items():
        if library_write.webp_info(files[kind]) != (size[0], size[1], True):
            raise ShotError(f"{kind}: Pillow wrote {library_write.webp_info(files[kind])}, not a {size} WebP with alpha")
    return files, margins


def centring(margins: list) -> tuple:
    """(dx, dy) in px that put a drawing of these margins [left, top, right, bottom] in the middle of its picture: half
    the difference of each axis's two margins, toward the larger (an odd difference leaves its pixel right or below)."""

    left, top, right, bottom = margins
    return (right - left) // 2, (bottom - top) // 2


def centred(image, box: tuple, margins: list) -> tuple:
    """(the picture, its drawing's margins) with the drawing (``box``, its alpha's bounding box) moved by whole pixels to
    the middle of the picture on its transparent ground (2026-11-05, the Library's pictures shot with the approved look).

    The figure frames the stack with drape.js frameView, which balances the margins of the axis that binds only: at
    16:10 the height binds on every sensor, so across the width the drawing stood off the middle (of 1280 px, the first
    full set): Exploded, the UMI finger's 61 to 72 px left of it ([405, 51, 548, 52] px on its 3 mm sensor), its tapered
    tips' 50 to 65 px, Franka Hand's 37 to 60 px; Assembled, Unitree Dex1's 79 to 85 px; and the Library's light box,
    which centres the picture, showed it off its middle on the cards.  The figure is left as the generator shows it
    (its framing is the user's approved view): the move is the picture's, a translation of the pixels the canvas gave,
    so nothing is resampled, cut (each margin becomes its axis's mean, never less than the smaller) or drawn anew."""

    dx, dy = centring(margins)
    if (dx, dy) == (0, 0):
        return image, list(margins)
    from PIL import Image

    moved = Image.new("RGBA", image.size, (0, 0, 0, 0))
    moved.paste(image.crop(box), (box[0] + dx, box[1] + dy))
    left, top, right, bottom = margins
    return moved, [left + dx, top + dy, right - dx, bottom - dy]


def webp(image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "WEBP", quality=QUALITY, method=6, alpha_quality=100, exact=False)
    return buffer.getvalue()


def record(identifier: str, variant: dict, files: dict, margins: dict, figure: str, look: str, *, art=None, view=None,
           stage=None) -> dict:
    """The manifest's record of one sensor's pictures; shot from the Library's 3D view, with ``view`` (view_sha256 of
    its modules), ``art`` (art_record()) and, for a gripper, ``stage`` ({scene, scene_sha256, numbers})."""

    paths = library_write.shot_files(identifier)
    entry = {"fit_sha256": variant["fit_sha256"], "build_id": variant["build_id"], "figure_sha256": figure, "look": look,
             "margins_px": margins,
             "files": {kind: {"path": paths[kind][0], "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                              "width": paths[kind][1][0], "height": paths[kind][1][1]} for kind, data in files.items()}}
    if view is not None:
        entry["view_sha256"] = view
    if art is not None:
        entry["art"] = art
    if stage is not None:
        entry["stage"] = stage
    return entry


def manifest_text(shots: dict) -> str:
    document = {"format": library_write.SHOTS_FORMAT, "about": library_write.SHOTS_ABOUT, "shots": shots}
    return json.dumps(document, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


def grid_cards(entries: dict) -> list:
    """The sensors whose card pictures the Library's grid shows, in its order (library.js, the layout of 2026-11-06): one
    card per gripper but the shelved (its 2 mm sensor), then each shelved part's shelf (the UMI finger's, and any part a
    family closes): its sensors and its families' defaults.  All of them are asked for as the page opens (it is short)."""
    shelved = {"umi-finray"} | {family["shelf"] for family in entries["families"].values()}
    cards = [entries["parts"][part]["default"] for part in entries["order"] if part not in shelved]
    for part in (part for part in entries["order"] if part in shelved):
        cards += entries["parts"][part]["variants"] + [family["default"] for family in entries["families"].values() if family["shelf"] == part]
    return cards


def order(entries: dict) -> list:
    """The sensors in the Library's order: each gripper's shelf by pitch, then the family parts' (the tapered tips)."""

    parts = list(entries["order"]) + sorted(part for part in entries["parts"] if part not in entries["order"])
    return [identifier for part in parts for identifier in entries["parts"][part]["variants"]]


def viewed_entries(entries: dict, scenes: dict) -> str:
    """entries.json as the shoot serves it: every variant's "view" as library_write writes it for a current record
    ({"art": art/<id>.json.gz, "scene": its part's scene or null}), and a sensor never pictured given the contract's
    "image" (its files a 404 until shot: the page's placeholder), so its page mounts the view."""

    viewed = json.loads(json.dumps(entries))
    for identifier, variant in viewed["variants"].items():
        variant["view"] = {"art": library_write.art_path(identifier), "scene": scenes.get(variant["part"])}
        if not variant.get("image"):
            variant["image"] = library_write.image_record(identifier, variant["label"])
    return json.dumps(viewed)


SHEET_CSS = """
body { margin:0; padding:24px; background:#fff; color:#1d1d1f; font:14px/1.35 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
h1 { font-size:18px; margin:0 0 4px; } p.meta { color:#6e6e73; margin:0 0 16px; font-size:13px; }
.grid { display:grid; grid-template-columns:repeat(6, 640px); gap:20px 16px; }
figure { margin:0; } .box { width:640px; height:400px; border-radius:12px; background-image:linear-gradient(155deg,#f5f5f7,#e8e8ed); }
.box img { display:block; width:640px; height:400px; } figcaption { margin-top:6px; font-size:13px; } figcaption span { color:#6e6e73; }
"""


def contact_sheet(browser, out: Path, entries: dict, shots: dict, sheet: Path) -> None:
    """Every sensor's Exploded card of the manifest at 1:1 in the page's light box (the Library's), six a row."""

    cells = []
    for identifier in [identifier for identifier in order(entries) if identifier in shots]:
        card = shots[identifier]["files"]["card"]
        data = (out / Path(card["path"]).name).read_bytes()
        margins = shots[identifier]["margins_px"]["exploded"]
        cells.append(f"<figure><div class='box'><img alt='' src='data:image/webp;base64,{base64.b64encode(data).decode('ascii')}'></div>"
                     f"<figcaption>{html.escape(entries['variants'][identifier]['label'])} <span>{html.escape(identifier)} · card "
                     f"{card['bytes'] / 1024:.1f} KB · margins {margins}</span></figcaption></figure>")
    total = sum(item["bytes"] for shot in shots.values() for item in shot["files"].values())
    page_html = (f"<!doctype html><html><head><meta charset='utf-8'><title>Library pictures</title><style>{SHEET_CSS}</style></head><body>"
                 f"<h1>The Library's pictures: the Exploded cards, 640 x 400</h1><p class='meta'>{len(cells)} sensors · the set "
                 f"{total / 1e6:.2f} MB · WebP quality {QUALITY} · {html.escape(str(out))}</p><div class='grid'>{''.join(cells)}</div></body></html>")
    context = browser.new_context(viewport={"width": 6 * 640 + 5 * 16 + 48, "height": 900}, device_scale_factor=1)
    page = context.new_page()
    page.set_content(page_html)
    page.evaluate("() => Promise.all([...document.images].map(image => image.decode().catch(() => null)))")
    sheet.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(sheet), full_page=True)
    context.close()


def check_generator(browser, url: str, out: Path, entries: dict, chosen: list) -> int:
    """--check-generator: each sensor shot in Gen by Surface (generator_shoot()) and its three files compared with
    ``out``'s; writes nothing."""

    from playwright.sync_api import Error as PlaywrightError

    differ, failed, started = [], [], time.monotonic()
    for number, identifier in enumerate(chosen, 1):
        begun = time.monotonic()
        files = None
        for attempt in (1, 2):
            try:
                files, _ = encode(generator_shoot(browser, url, identifier, entries["variants"][identifier]))
                break
            except (ShotError, PlaywrightError) as error:
                problem = error
                if attempt == 1:
                    print(f"retry {identifier}: {error}", flush=True)
        if files is None:
            failed.append(identifier)
            print(f"FAIL {identifier}: {problem}", flush=True)
            continue
        paths = library_write.shot_files(identifier)
        unlike = [kind for kind, data in files.items()
                  if not (out / Path(paths[kind][0]).name).is_file() or (out / Path(paths[kind][0]).name).read_bytes() != data]
        if unlike:
            differ.append(identifier)
        print(f"{'DIFFERS' if unlike else 'same'} {identifier} ({number}/{len(chosen)}, {time.monotonic() - begun:.1f} s)"
              + (f": {', '.join(unlike)}" if unlike else ""), flush=True)
    print(f"library_shots: Gen by Surface's figure shot for {len(chosen) - len(failed)} of {len(chosen)} sensors in "
          f"{time.monotonic() - started:.0f} s; {len(differ)} differ from {out}" + (f": {', '.join(differ)}" if differ else ""))
    return 1 if failed or differ else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=int(os.environ["FPC_PORT"]) if os.environ.get("FPC_PORT") else None,
                        help="the port of a running app.py serving this project (default FPC_PORT)")
    parser.add_argument("--only", default=None, metavar="ID,...", help="shoot only these sensors (the others' records kept)")
    parser.add_argument("--out", type=Path, default=OUT, help=f"the pictures' folder (default {OUT.relative_to(ROOT)}; the art goes "
                        "into an art/ folder beside it)")
    parser.add_argument("--check", action="store_true", help="shoot again and compare with the manifest and the art; write nothing")
    parser.add_argument("--check-generator", default=None, metavar="ID,...",
                        help="shoot these sensors in Gen by Surface and compare their files with the folder's; write nothing")
    parser.add_argument("--sheet", type=Path, default=None, help="write a contact sheet (PNG) of the manifest's Exploded cards")
    args = parser.parse_args(argv)
    if args.port is None:
        parser.error("give --port (or FPC_PORT): the port of a running app.py serving this project")
    url = f"http://127.0.0.1:{args.port}/"
    out = args.out.resolve()
    art_dir = out.parent / "art"
    local = (LIBRARY / "entries.json").read_bytes()
    try:
        served = fetch(url + "static/library/entries.json")
        figure = library_write.figure_sha256(library_write.figure_sources(lambda path: fetch(url + "static/" + path)))
    except OSError as error:
        print(f"library_shots: app.py does not answer on port {args.port}: {error}", file=sys.stderr)
        return 2
    if served != local:
        print(f"library_shots: the server on port {args.port} serves another library than this tree's (its entries.json "
              "differs): start app.py from this project", file=sys.stderr)
        return 2
    entries = json.loads(local.decode("utf-8"))
    listed = args.check_generator if args.check_generator is not None else args.only
    chosen = order(entries) if listed is None else [item for item in re.split(r"[,\s]+", listed) if item]
    unknown = [identifier for identifier in chosen if identifier not in entries["variants"]]
    if unknown or not chosen:
        print(f"library_shots: no sensor is named {', '.join(unknown) or repr(listed)}", file=sys.stderr)
        return 2
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    if args.check_generator is not None:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=WEBGL_ARGS)
            try:
                return check_generator(browser, url, out, entries, chosen)
            finally:
                browser.close()
    # The Library view's modules and the scenes as the server serves them (its scenes.json this tree's).
    try:
        view = library_write.view_sha256(library_write.view_sources(lambda path: fetch(url + "static/" + path)))
        index = fetch(url + "static/library/" + library_write.SCENES_INDEX)
    except OSError as error:
        print(f"library_shots: the server on port {args.port} does not serve the Library's 3D view ({', '.join(library_write.VIEW_SOURCES)}, "
              f"library/{library_write.SCENES_INDEX}): {error}", file=sys.stderr)
        return 2
    scenes = json.loads(index.decode("utf-8"))
    if scenes != library_write.scenes_index(LIBRARY):
        print(f"library_shots: the server on port {args.port} serves other scenes than this tree's (its {library_write.SCENES_INDEX} "
              "differs): start app.py from this project", file=sys.stderr)
        return 2
    rules = scenes.get("rules") or {}
    scene_files = {}
    for part in sorted({entries["variants"][identifier]["part"] for identifier in chosen} & set(scenes.get("scenes") or {})):
        relative = scenes["scenes"][part]
        try:
            data = fetch(url + "static/library/" + relative)
        except OSError as error:
            print(f"library_shots: the server does not serve {relative}: {error}", file=sys.stderr)
            return 2
        scene_files[part] = {"path": relative, "bytes": data, "see_through": json.loads(data.decode("utf-8")).get("see_through")}
    entries_text = viewed_entries(entries, scenes.get("scenes") or {})
    path = out / "manifest.json"
    known = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"format": library_write.SHOTS_FORMAT, "shots": {}}
    if known.get("format") != library_write.SHOTS_FORMAT:
        print(f"library_shots: {path} is not a {library_write.SHOTS_FORMAT} manifest", file=sys.stderr)
        return 2
    shots = dict(known["shots"])
    failed, differ, started, timings = [], [], time.monotonic(), []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=WEBGL_ARGS)
        generator = art_page(browser)
        try:
            open_art_page(generator, url)
        except (ShotError, PlaywrightError) as error:
            print(f"library_shots: {error}", file=sys.stderr)
            browser.close()
            return 2
        for number, identifier in enumerate(chosen, 1):
            variant = entries["variants"][identifier]
            scene = scene_files.get(variant["part"])
            begun = time.monotonic()
            files = document = art = None
            art_s = shot_s = 0.0
            for attempt in (1, 2):
                try:
                    if document is None:
                        art_begun = time.monotonic()
                        document = art_document(generator, url, identifier, variant)
                        art = library_write.art_bytes(document)
                        art_s = time.monotonic() - art_begun
                    shot_begun = time.monotonic()
                    drawn = shoot(browser, url, identifier, variant, {"entries": entries_text, "art": art, "gripper": scene is not None})
                    if scene is not None:
                        broken = rule_breaches(drawn["stage"], rules.get("checks") or {}, scene["see_through"], rules.get("explode_stacks"))
                        if broken:
                            raise ShotError(f"the stage breaks scenes.json's rules: {'; '.join(broken)}")
                    files, margins = encode(drawn)
                    shot_s = time.monotonic() - shot_begun
                    break
                except (ShotError, PlaywrightError) as error:
                    # Once again in a new context (a load that a busy host held back), then reported.
                    problem = error
                    if attempt == 1:
                        print(f"retry {identifier}: {error}", flush=True)
            if files is None:
                failed.append(f"{identifier}: {problem}")
                print(f"FAIL {identifier}: {problem}", flush=True)
                continue
            stage = None if scene is None else {"scene": scene["path"], "scene_sha256": library_write.scene_sha256(scene["bytes"], rules),
                                                "numbers": drawn["stage"]}
            fresh = record(identifier, variant, files, margins, figure, document["look"], art=art_record(identifier, art, document),
                           view=view, stage=stage)
            timings.append((identifier, time.monotonic() - begun, art_s, shot_s))
            sizes = " ".join(f"{kind} {len(data) / 1024:.1f} KB" for kind, data in files.items()) + f", art {len(art) / 1024:.1f} KB"
            took = f"{time.monotonic() - begun:.1f} s: art {art_s:.2f} s, view {shot_s:.1f} s"
            if args.check:
                kept = shots.get(identifier) or {}
                same_files = kept.get("files") == fresh["files"] and all(
                    (out / Path(item["path"]).name).is_file() and (out / Path(item["path"]).name).read_bytes() == files[kind]
                    for kind, item in kept["files"].items())
                kept_art = kept.get("art") or {}
                art_file = art_dir / Path(kept_art.get("path") or "missing").name
                same_art = ({key: kept_art.get(key) for key in ("path", "json_sha256", "build_id")}
                            == {key: fresh["art"][key] for key in ("path", "json_sha256", "build_id")}
                            and art_file.is_file() and json_sha256(library_write.read_art(art_file.read_bytes())) == fresh["art"]["json_sha256"])
                same_stage = kept.get("stage") == fresh.get("stage")
                unlike = [name for name, same in (("pictures", same_files), ("art", same_art), ("stage", same_stage)) if not same]
                if unlike:
                    differ.append(identifier)
                print(f"{'DIFFERS' if unlike else 'same'} {identifier} ({number}/{len(chosen)}, {took}): {sizes}"
                      + (f"; differ: {', '.join(unlike)}" if unlike else ""), flush=True)
                continue
            out.mkdir(parents=True, exist_ok=True)
            for kind, data in files.items():
                target = out / Path(fresh["files"][kind]["path"]).name
                if not target.is_file() or target.read_bytes() != data:
                    target.write_bytes(data)
            art_dir.mkdir(parents=True, exist_ok=True)
            target = art_dir / Path(fresh["art"]["path"]).name
            if not target.is_file() or target.read_bytes() != art:
                target.write_bytes(art)
            shots[identifier] = fresh
            print(f"shot {identifier} ({number}/{len(chosen)}, {took}): {sizes}, margins {margins['exploded']} / {margins['assembled']} px",
                  flush=True)
        generator.context.close()
        if not args.check:
            if args.only is None:
                # A full run: the pictures and the art of sensors no longer listed go (only files named as theirs).
                for identifier in [identifier for identifier in shots if identifier not in entries["variants"]]:
                    del shots[identifier]
                pictures = {Path(item["path"]).name for shot in shots.values() for item in shot["files"].values()}
                arts = {Path(shot["art"]["path"]).name for shot in shots.values() if shot.get("art")}
                for folder, names, pattern in ((out, pictures, library_write.SHOT_NAME), (art_dir, arts, ART_NAME)):
                    if folder.is_dir():
                        for file in sorted(folder.iterdir()):
                            if pattern.match(file.name) and file.name not in names:
                                file.unlink()
                                print(f"removed {folder.name}/{file.name} (no sensor)", flush=True)
            if shots:
                text = manifest_text(shots)
                if not path.is_file() or path.read_text(encoding="utf-8") != text:
                    path.write_text(text, encoding="utf-8")
        if args.sheet is not None and shots:
            contact_sheet(browser, out, entries, shots, args.sheet.resolve())
            print(f"contact sheet: {args.sheet.resolve()}", flush=True)
        browser.close()
    total = sum(item["bytes"] for shot in shots.values() for item in shot["files"].values())
    arts = sum(shot["art"]["bytes"] for shot in shots.values() if shot.get("art"))
    first = sum(shots[identifier]["files"]["card"]["bytes"] for identifier in grid_cards(entries) if identifier in shots)
    if timings:
        seconds = sorted(item[1] for item in timings)
        print(f"library_shots: a sensor in {seconds[0]:.1f} to {seconds[-1]:.1f} s (the art {min(item[2] for item in timings):.2f} to "
              f"{max(item[2] for item in timings):.2f} s of it, the view {min(item[3] for item in timings):.1f} to {max(item[3] for item in timings):.1f} s)")
    print(f"library_shots: {len(chosen) - len(failed)} of {len(chosen)} sensors shot in {time.monotonic() - started:.0f} s; "
          f"the set {len(shots)} sensors, {total / 1e6:.2f} MB; the grid's first screen (its {len(grid_cards(entries))} cards) {first / 1e6:.2f} MB; "
          f"the art {arts / 1e6:.2f} MB")
    if args.check:
        print(f"library_shots: {len(differ)} sensors differ from {path}" + (f": {', '.join(differ)}" if differ else ""))
    elif not failed:
        print("library_shots: now run tools/library_write.py (entries.json's image and view from the manifest)")
    return 1 if failed or differ else 0


if __name__ == "__main__":
    sys.exit(main())
