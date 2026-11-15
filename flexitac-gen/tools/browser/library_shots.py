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
    ... library_shots.py --check-generator                                                    # Gen by Surface's figure
    ... library_shots.py --check-generator umi-finray-2mm,umi-trap-tip5.8-2mm                 # ... of some sensors
    ... library_shots.py --pin-generator                                                      # ... pinned anew
    ... library_shots.py --out /tmp/shots --sheet /tmp/shots/contact_sheet.png                # elsewhere, with a sheet
    ... library_shots.py --showcase [--check]                                                 # the showcase's pictures

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
and the numbers); for a part without a scene that the rules give a look (their part_looks), part_look_sha256.  A sensor shot from another fit, or with art of another build, is the wrong sensor pictured, which
library_write --check, the site build and tests/test_library.py refuse; one shot from older figure or view sources is
only a warning there (the public CI runs no browser): re-shoot it here.

The same code gives the same bytes (SwiftShader draws the same pixels, Pillow's libwebp writes them the same way, the
stage's measures are a software raster): --check shoots again and compares every picture with the manifest's, the art's
document by json_sha256 (never its gzip bytes, which another zlib may write otherwise) with the manifest's and with the
art file's, and each gripper's stage (its scene hash and numbers), writing nothing.  The art goes into web/library/art/,
or with --out into an art/ folder beside that folder (the manifest's paths stay relative to their parent: shots/...,
art/...).  A full run removes the pictures and the art of sensors no longer listed; --only keeps the others' records.
--check-generator [ID,...] is the proof that Gen by Surface is as it was and that the Library's view of a part without a
scene (the UMI finger and its tapered tips; every such sensor without ID) is that figure but for the part's look (since
2026-11-12 scenes.json's rules draw those parts in the real finger's orange TPU, where the Library's pictures had been
Gen by Surface's figure byte for byte; Gen by Surface keeps its grey part).  For each sensor, writing nothing:
1. Gen by Surface's figure (./?part=<id>, the figure on its own: generator_shoot(), as the pictures were shot until the
   3D view) is the picture pinned for it in tools/browser/generator_figure.json (its three files' bytes and SHA-256, of
   the entry's fit and build: the Library's pictures of before the look, so the figure of today is the figure of then);
2. the Library's view with the rules' looks served away is that figure, pixel for pixel (the same part, sheets, lights,
   camera and frame: without a look the Library's view of such a part is the figure);
3. the Library's view as the rules are gives the folder's three pictures, byte for byte (for a part the rules give no
   look these are the figure's own files, the equality of before);
4. for a part with a look, the view shot once more with that look in another colour (every channel half the range off):
   the drawing's alpha is the figure's at every pixel (the same outline), and every drawn pixel that the part's colour
   does not reach (the same in both colours: the sheets, and their edges on the ground) is the figure's pixel (the look
   touches the part alone); the pixels it does reach (the part's) and the others must each be PART_SHARE_MIN and
   SHEETS_SHARE_MIN of the drawing at least, so that neither statement is empty.
A gripper's sensor is refused (its picture is the whole scene).  --pin-generator [ID,...] writes the pin from Gen by
Surface's figure as it is now, saying which pictures changed: only for a deliberate change of the figure, or a sensor's
new build.  Four drawings a sensor: 43 to 57 s on the shared host of 2026-11-12 (a shoot's one drawing 8 to 18 s there).
--sheet writes a contact sheet (PNG) of every sensor's Exploded card in the manifest, in the Library's order,
each in the page's light box.  About 6 to 10 s a sensor, the art 0.6 to 1.6 s of it (the 42 in 5.4 minutes on a shared
host, 2026-11-05, with the scenes of the design: 126 files, 3.70 MB; the first screen's cards 0.21 MB; the art 0.41 MB).

--showcase shoots the Library's showcase instead (the hand-designed FlexiTac sensor on the xArm gripper; no sensor of
entries.json): its own page, library.html?probe=shoot#<its id>, with web/library/showcase.json served by this tool (the
pad's placed record fresh, with the showcase's scene), the view's pane 640 x 800 CSS px (4:5: a 1280 x 1600 buffer, so
the upright gripper fills the picture), each mode read, checked whole and centred as a sensor's; written to
web/library/showcase/ (<id>.exploded.webp, <id>.assembled.webp, and <id>.card.webp, the Assembled drawing at 800 x 1000)
with showcase.json's "placed", "image" (each file's bytes and SHA-256) and "shot" (the hashes of the scene with the
rules, the art, the placed record, the figure's and the view's sources, the look, the margins and the stage's numbers);
--check shoots again and compares the three keys and every file's bytes, writing nothing.  tools/library_write.py
--check then holds the document and the files (showcase_page()).

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
# The stage's numbers (docs/LIBRARY_VIEW.md; their names frozen with the design of 2026-11-05): the writer's.
STAGE_NUMBERS = library_write.STAGE_NUMBERS


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
    """The rules of scenes/scenes.json's "checks" that a gripper's stage numbers break, one line each (none: []):
    library_write.stage_problems(), the one copy of the rules (docs/LIBRARY_VIEW.md; the review of 2026-11-06: a copy of
    its own here had taken a jaw gap of 0 or below and an extra number, which the writer's --check and the site's gate
    then refused), so the shots tool refuses exactly the sensors whose record the writer would refuse."""

    return library_write.stage_problems(numbers, checks, see_through or (), explode_stacks)


def shoot(browser, url: str, identifier: str, variant: dict, served: dict) -> dict:
    """{mode: the Library view's PNG at its home, "stage": the stage's numbers or None} of one sensor (a new context,
    closed after).  ``served``: {"entries": entries.json's text with every view, "art": this sensor's art file (None:
    the server's own), "gripper": whether its part has a scene, "scenes": scenes/scenes.json's text in place of the
    server's (--check-generator: the rules with another look for the part, or none)}."""

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

    if served.get("art") is not None:
        page.route("**/static/library/art/**", art)
    if served.get("scenes") is not None:
        page.route(f"**/static/library/{library_write.SCENES_INDEX}", lambda route: route.fulfill(status=200, content_type="application/json", body=served["scenes"]))
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


# -- the showcase (the Library's first card and its page; docs/LIBRARY_VIEW.md "The showcase's page") ------------------------

SHOWCASE_PANE_CSS = (library_write.SHOWCASE_SHOT_SIZE[0] // DPR, library_write.SHOWCASE_SHOT_SIZE[1] // DPR)
# One transparent pixel (a PNG).
PIXEL_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def showcase_shoot(browser, url: str, document: dict) -> dict:
    """{mode: the Library view's PNG at its home, "numbers": the stage's} of the showcase, from its own page as a visitor
    opens it (library.html?probe=shoot#<its id>: the placed record drawn on the scene's gripper), ``document`` served as
    its showcase.json (the placed record fresh, the pictures named as they will be).  The view's host at SHOWCASE_PANE_CSS, 640 x 800 CSS px (4:5): a 1280 x 1600 buffer, the scene framed
    again at that aspect, so the upright gripper fills the picture."""

    context = browser.new_context(viewport=VIEWPORT, device_scale_factor=DPR, color_scheme="light")
    page = context.new_page()
    errors = []
    console_errors(page, errors)
    page.route("**/static/library/showcase.json", lambda route: route.fulfill(status=200, content_type="application/json",
                                                                               body=library_write.showcase_text(document)))
    # Its pictures as the page asks for them (under the view, never seen in the shot): one transparent pixel each, so
    # the first shoot, with none written yet, keeps the page's Exploded | Assembled switch (the page drops it once both
    # of a page's pictures have failed to load).
    page.route("**/static/library/showcase/*.webp", lambda route: route.fulfill(status=200, content_type="image/png", body=PIXEL_PNG))
    size = list(library_write.SHOWCASE_SHOT_SIZE)
    try:
        page.goto(f"{url}library.html?probe=shoot#{document['id']}")
        drawn = poll(page, VIEW_DRAWN, None, TIMEOUT_S)
        if drawn != "drawn":
            raise ShotError(f"the Library's 3D view is not drawn for the showcase: {drawn or 'timed out'}")
        pane = page.evaluate(PANE, list(SHOWCASE_PANE_CSS))
        if pane != list(SHOWCASE_PANE_CSS) or not poll(page, BUFFER, size, 60):
            raise ShotError(f"the view's pane is {pane} CSS px, its buffer not {size}")
        page.evaluate(TWO_FRAMES)
        shots, state = {}, {}
        for mode in MODES:
            read = page.evaluate(SHOT, mode)
            if "error" in read:
                raise ShotError(f"{mode}: {read['error']}")
            state = json.loads(read["state"])
            offset = state.get("offset") or [0, 0]
            if (state.get("state"), state.get("id"), state.get("build_id"), state.get("mode"), state.get("drawn_mode"), state.get("moved"),
                    read["buffer"], list(offset[:2])) != ("drawn", document["id"], None, mode, mode, False, size, [0, 0]):
                raise ShotError(f"{mode}: not at its home as drawn, unmoved: {dict(state, stage=None)} buffer {read['buffer']}")
            shots[mode] = {"png": base64.b64decode(read["url"].split(",", 1)[1])}
        if not state.get("gripper"):
            raise ShotError("the view drew no gripper's scene for the showcase")
        shots["numbers"] = ((state.get("stage") or {}).get("numbers")) or None
        if not shots["numbers"]:
            raise ShotError(f"the stage measured no numbers (#libViewState stage {state.get('stage')!r}): is the page's ?probe=shoot honoured?")
    finally:
        context.close()
    if errors:
        raise ShotError(f"console errors: {errors[:3]}")
    return shots


def showcase_encode(shots: dict) -> tuple:
    """({kind: WebP bytes}, {mode: margins px}) of the showcase's drawings, each checked whole and centred as a sensor's
    (encode()); the card the Assembled drawing downscaled (library_write.SHOWCASE_SHOTS)."""

    from PIL import Image

    images, margins = {}, {}
    for mode in MODES:
        image = Image.open(io.BytesIO(shots[mode]["png"]))
        image.load()
        width, height = image.size
        if (image.mode, image.size) != ("RGBA", library_write.SHOWCASE_SHOT_SIZE):
            raise ShotError(f"{mode}: the canvas read as {image.mode} {image.size}")
        box = image.getchannel("A").getbbox()
        if box is None:
            raise ShotError(f"{mode}: nothing drawn")
        drawn = [box[0], box[1], width - box[2], height - box[3]]
        if min(drawn) == 0:
            raise ShotError(f"{mode}: the drawing reaches the frame's edge (margins {drawn} px): the gripper is cut")
        images[mode], margins[mode] = centred(image, box, drawn)
    files = {}
    for kind, (_, size, mode) in library_write.SHOWCASE_SHOTS.items():
        files[kind] = webp(images[mode] if images[mode].size == size else images[mode].resize(size, Image.LANCZOS))
        if library_write.webp_info(files[kind]) != (size[0], size[1], True):
            raise ShotError(f"{kind}: Pillow wrote {library_write.webp_info(files[kind])}, not a {size} WebP with alpha")
    return files, margins


def showcase_run(url: str, port: int, check: bool, out: Path) -> int:
    """--showcase: the showcase's three pictures shot from its own page and written into ``out`` (web/library/showcase/)
    with showcase.json's "placed", "image" and "shot"; with ``check`` shot again and compared, nothing written."""

    path = LIBRARY / library_write.SHOWCASE_FILE
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"library_shots: {path} is missing or not JSON ({error}): write its words first (docs/LIBRARY_VIEW.md)", file=sys.stderr)
        return 2
    placed = library_write.showcase_placed(LIBRARY)
    if placed is None:
        print(f"library_shots: web/{library_write.SHOWCASE_PLACED} is missing or not JSON", file=sys.stderr)
        return 2
    try:
        figure = library_write.figure_sha256(library_write.figure_sources(lambda name: fetch(url + "static/" + name)))
        view = library_write.view_sha256(library_write.view_sources(lambda name: fetch(url + "static/" + name)))
        same = all(fetch(url + "static/library/" + relative) == (LIBRARY / relative).read_bytes()
                   for relative in (library_write.SHOWCASE_SCENE, library_write.SCENES_INDEX, placed["art"], placed["mesh"]["file"]))
    except OSError as error:
        print(f"library_shots: app.py does not answer on port {port}, or does not serve the showcase's files: {error}", file=sys.stderr)
        return 2
    if not same:
        print(f"library_shots: the server on port {port} serves another showcase than this tree's (its scene, rules, art or finger "
              "differs): start app.py from this project", file=sys.stderr)
        return 2
    # The page's document for the shoot: the placed record fresh, the pictures named as they will be.
    stub = {kind: {"src": relative, "width": size[0], "height": size[1]} for kind, (relative, size, _) in library_write.SHOWCASE_SHOTS.items()}
    served = dict(document, placed=placed, image=dict(stub, alt=library_write.SHOWCASE_ALT))
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    started = time.monotonic()
    files = problem = None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=WEBGL_ARGS)
        try:
            for attempt in (1, 2):
                try:
                    drawn = showcase_shoot(browser, url, served)
                    files, margins = showcase_encode(drawn)
                    break
                except (ShotError, PlaywrightError) as error:
                    problem = error
                    if attempt == 1:
                        print(f"retry the showcase: {error}", flush=True)
        finally:
            browser.close()
    if files is None:
        print(f"FAIL the showcase: {problem}", flush=True)
        return 1
    # The stage's numbers within the rules' checks and the showcase's own bounds, or nothing is written.
    unsound = library_write.showcase_numbers(drawn["numbers"], library_write.scenes_index(LIBRARY).get("rules"))
    if unsound:
        print(f"FAIL the showcase: {'; '.join(unsound)} (library_write.SHOWCASE_BOUNDS)", flush=True)
        return 1
    look = library_write.read_art((LIBRARY / placed["art"]).read_bytes()).get("look")
    fresh = dict(document, placed=placed, image=library_write.showcase_image(files),
                 shot=dict(library_write.showcase_shot(LIBRARY, figure, view), look=look, margins_px=margins, numbers=drawn["numbers"]))
    sizes = " ".join(f"{kind} {len(data) / 1024:.1f} KB" for kind, data in files.items())
    took = f"{time.monotonic() - started:.1f} s"
    if check:
        unlike = [key for key in ("placed", "image", "shot") if document.get(key) != fresh[key]]
        unlike += [relative for kind, (relative, _, _) in library_write.SHOWCASE_SHOTS.items()
                   if not (out / Path(relative).name).is_file() or (out / Path(relative).name).read_bytes() != files[kind]]
        print(f"{'DIFFERS' if unlike else 'same'} the showcase ({took}): {sizes}" + (f"; differ: {', '.join(unlike)}" if unlike else ""), flush=True)
        return 1 if unlike else 0
    out.mkdir(parents=True, exist_ok=True)
    for kind, (relative, _, _) in library_write.SHOWCASE_SHOTS.items():
        target = out / Path(relative).name
        if not target.is_file() or target.read_bytes() != files[kind]:
            target.write_bytes(files[kind])
    text = library_write.showcase_text(fresh)
    if path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    print(f"shot the showcase ({took}): {sizes}, margins {margins['exploded']} / {margins['assembled']} px", flush=True)
    print(f"library_shots: now run tools/library_write.py --check ({library_write.SHOWCASE_FILE}'s pictures and what they were shot from)")
    return 0


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
           stage=None, part_look=None) -> dict:
    """The manifest's record of one sensor's pictures; shot from the Library's 3D view, with ``view`` (view_sha256 of
    its modules), ``art`` (art_record()) and, for a gripper, ``stage`` ({scene, scene_sha256, numbers}); for a part
    without a scene that scenes.json's rules give a look, ``part_look`` (library_write.part_look_sha256())."""

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
    if part_look is not None:
        entry["part_look_sha256"] = part_look
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


# -- Gen by Surface's figure and the Library's view of a part without a scene (--check-generator, --pin-generator) -----
# The pin: Gen by Surface's figure of each sensor of a part without a scene, as encode() writes its three pictures (each
# file's bytes and SHA-256), with the fit and the build it is of.  Written from the Library's pictures of before the
# look (2026-11-12), which were that figure byte for byte, so the figure of today is held to the figure of then.
GENERATOR_PIN = Path(__file__).resolve().parent / "generator_figure.json"
GENERATOR_FORMAT = "flexitac-generator-figure/v1"
GENERATOR_ABOUT = ("Gen by Surface's sensor on the part (./?part=<id>: web/cad/onpart.js with no stage, the part in the "
                   "generator's grey) for each sensor of a Library part without a scene (the UMI finger and its tapered "
                   "tips), as tools/browser/library_shots.py shoots and encodes it: the three pictures' bytes and SHA-256, "
                   "the fit and the build they are of, and the hash of the figure's sources they were pinned from "
                   "(figure_sha256: a record only; the pictures are what is held).  Until 2026-11-12 the Library's own "
                   "pictures of these sensors were these files byte for byte; since then the Library draws the part in "
                   "its look (scenes/scenes.json's rules) and library_shots.py --check-generator holds Gen by Surface's "
                   "figure to this pin.  Written by --pin-generator, only for a deliberate change of the figure or a "
                   "sensor's new build.")
# The least share of a drawing's pixels that the part's colour must reach, and that it must not (--check-generator's
# fourth comparison: with fewer of either, one of its two statements would be about almost nothing).  Measured on the
# fourteen sensors of 2026-11-12: the part's 44 to 52 % of the Exploded drawing and 26 to 41 % of the Assembled one.
PART_SHARE_MIN = 0.1
SHEETS_SHARE_MIN = 0.25
PIN_PROBLEM = "pin Gen by Surface's figure again with tools/browser/library_shots.py --pin-generator"


def fingertip_sensors(entries: dict, staged: dict) -> list:
    """The sensors, in the Library's order, of the parts without a scene (``staged``: scenes.json's scenes map): the
    ones whose Library view is Gen by Surface's figure with no stage."""

    return [identifier for identifier in order(entries) if entries["variants"][identifier]["part"] not in staged]


def figure_record(variant: dict, files: dict) -> dict:
    """The pin's record of one sensor's figure: the fit and the build it is of, each picture's bytes and SHA-256."""

    return {"fit_sha256": variant["fit_sha256"], "build_id": variant["build_id"],
            "files": {kind: {"bytes": len(files[kind]), "sha256": hashlib.sha256(files[kind]).hexdigest()} for kind in library_write.SHOT_KINDS}}


def pin_text(shots: dict, figure: str) -> str:
    document = {"format": GENERATOR_FORMAT, "about": GENERATOR_ABOUT, "figure_sha256": figure, "shots": shots}
    return json.dumps(document, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


def read_pin(path: Path = GENERATOR_PIN) -> dict:
    """The pin's document, or an empty one where there is none."""

    if not path.is_file():
        return {"format": GENERATOR_FORMAT, "figure_sha256": None, "shots": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def pin_problems(pin: dict, entries: dict, staged: dict) -> list:
    """What makes the pin not the pin of this library's sensors, one line each (none: []): another format, a sensor of
    a part without a scene not pinned or pinned for another fit or build (the figure of another sensor), a record
    without the three pictures' bytes and SHA-256, a record of no such sensor."""

    if pin.get("format") != GENERATOR_FORMAT:
        return [f"the pin's format is {pin.get('format')!r}, not {GENERATOR_FORMAT}"]
    found, shots = [], pin.get("shots") or {}
    wanted = fingertip_sensors(entries, staged)
    for identifier in wanted:
        record, variant = shots.get(identifier), entries["variants"][identifier]
        if record is None:
            found.append(f"{identifier}: Gen by Surface's figure is not pinned: {PIN_PROBLEM} {identifier}")
        elif (record.get("fit_sha256"), record.get("build_id")) != (variant["fit_sha256"], variant["build_id"]):
            found.append(f"{identifier}: the pin is of another fit or build than the entry's ({record.get('build_id')}, not {variant['build_id']}): "
                         f"{PIN_PROBLEM} {identifier}")
        elif (sorted(record.get("files") or {}) != sorted(library_write.SHOT_KINDS)
              or not all(isinstance(item, dict) and isinstance(item.get("bytes"), int) and item["bytes"] > 0
                         and re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256"))) for item in record["files"].values())):
            found.append(f"{identifier}: the pin has not the bytes and SHA-256 of its {', '.join(library_write.SHOT_KINDS)} pictures: {PIN_PROBLEM} {identifier}")
    found += [f"{identifier}: pinned, but no sensor of a part without a scene: {PIN_PROBLEM}" for identifier in sorted(set(shots) - set(wanted))]
    return found


def other_look(look: dict) -> dict:
    """``look`` in another colour: every channel half the range off (#e85a1c -> #68da9c), so that every pixel the
    part's colour reaches is drawn otherwise, whatever the colour."""

    return dict(look, color="#" + "".join(f"{(int(look['color'][k:k + 2], 16) + 128) % 256:02x}" for k in (1, 3, 5)))


def served_scenes(index: dict, part_id: str, given: dict | None) -> str:
    """scenes/scenes.json's text as --check-generator serves it: the rules without their looks (``given`` None: the part
    as Gen by Surface draws it) or with ``given`` ({"look", "smooth_deg"}, as library_write.part_look() gives it) for
    ``part_id`` alone; everything else as it is."""

    served = json.loads(json.dumps(index))
    for key in library_write.RULES_OPTIONAL:
        served["rules"].pop(key, None)
    if given is not None:
        served["rules"]["part_looks"] = {part_id: given["look"]}
        if given.get("smooth_deg") is not None:
            served["rules"]["part_smooth_deg"] = given["smooth_deg"]
    return json.dumps(served)


def view_differences(figure: bytes, look: bytes, other: bytes) -> dict:
    """The Library's view of a part in its look against Gen by Surface's figure, pixel by pixel: three drawings of one
    size as RGBA bytes (four a pixel): the figure, the view in the part's look, the view in that look's other colour
    (other_look()).  {"drawn": the view's drawn pixels (alpha above 0), "alpha": the pixels whose alpha is not the
    figure's (another outline), "part": the drawn pixels the part's colour reaches (not the same in both colours),
    "sheets": the drawn pixels it does not reach (the same in both: the sheets, and their edges on the ground),
    "wrong": those of the sheets' pixels that are not the figure's}."""

    if not (len(figure) == len(look) == len(other)) or len(look) % 4:
        raise ShotError(f"the drawings are not RGBA of one size ({len(figure)}, {len(look)} and {len(other)} bytes)")
    counts = {"drawn": 0, "alpha": 0, "part": 0, "sheets": 0, "wrong": 0}
    for k in range(3, len(look), 4):
        if look[k] != figure[k]:
            counts["alpha"] += 1
        if not look[k]:
            continue
        counts["drawn"] += 1
        pixel = look[k - 3:k + 1]
        if pixel != other[k - 3:k + 1]:
            counts["part"] += 1
            continue
        counts["sheets"] += 1
        if pixel != figure[k - 3:k + 1]:
            counts["wrong"] += 1
    return counts


def view_problems(counts: dict) -> list:
    """What view_differences()'s counts show that the Library's view of a part in its look is not Gen by Surface's
    figure with the part alone drawn otherwise, one line each (none: [])."""

    found = []
    if counts["alpha"]:
        found.append(f"{counts['alpha']} px of another alpha than the figure's (another outline)")
    if counts["wrong"]:
        found.append(f"{counts['wrong']} of the {counts['sheets']} px the part's colour does not reach are not the figure's (the look is not the part's alone)")
    if counts["part"] < PART_SHARE_MIN * counts["drawn"]:
        found.append(f"the part's colour reaches {counts['part']} of the {counts['drawn']} px drawn, under {PART_SHARE_MIN:g} of them (is the look drawn?)")
    if counts["sheets"] < SHEETS_SHARE_MIN * counts["drawn"]:
        found.append(f"the part's colour reaches all but {counts['sheets']} of the {counts['drawn']} px drawn, under {SHEETS_SHARE_MIN:g} of them left "
                     "(the sheets drawn otherwise too?)")
    return found


def rgba(png: bytes) -> bytes:
    """A canvas's PNG as RGBA bytes (SHOT_SIZE)."""

    from PIL import Image

    image = Image.open(io.BytesIO(png))
    image.load()
    if (image.mode, image.size) != ("RGBA", library_write.SHOT_SIZE):
        raise ShotError(f"the canvas read as {image.mode} {image.size}")
    return image.tobytes()


def twice(what: str, shot):
    """``shot()``, once again after a ShotError or a Playwright error (a load that a busy host held back)."""

    from playwright.sync_api import Error as PlaywrightError

    try:
        return shot()
    except (ShotError, PlaywrightError) as error:
        print(f"retry {what}: {error}", flush=True)
    return shot()


def check_generator(browser, url: str, out: Path, entries: dict, chosen: list, index: dict, parts: dict, pin: dict) -> int:
    """--check-generator (the module's docstring): for each sensor of a part without a scene, Gen by Surface's figure
    against its pin, the Library's view without the rules' looks against that figure, the view as the rules are against
    the folder's pictures, and for a part with a look the view against the figure pixel by pixel (view_differences());
    writes nothing."""

    from playwright.sync_api import Error as PlaywrightError

    staged = index.get("scenes") or {}
    entries_text = viewed_entries(entries, staged)
    differ, failed, started = [], [], time.monotonic()
    for number, identifier in enumerate(chosen, 1):
        begun = time.monotonic()
        variant = entries["variants"][identifier]
        given = library_write.part_look(index, parts, variant["part"])

        def viewed(look, identifier=identifier, variant=variant):
            return shoot(browser, url, identifier, variant, {"entries": entries_text, "art": None, "gripper": False,
                                                              "scenes": served_scenes(index, variant["part"], look)})

        try:
            figure = twice(identifier, lambda: generator_shoot(browser, url, identifier, variant))
            bare = twice(identifier, lambda: viewed(None))
            looked = twice(identifier, lambda: viewed(given)) if given else bare
            other = twice(identifier, lambda: viewed(dict(given, look=other_look(given["look"])))) if given else None
            files, _ = encode(figure)
            pictures, _ = encode(looked)
            unlike = []
            # 1. Gen by Surface's figure is its pin.
            pinned = (pin.get("shots") or {}).get(identifier) or {}
            if (pinned.get("fit_sha256"), pinned.get("build_id")) != (variant["fit_sha256"], variant["build_id"]):
                unlike.append(f"the figure is not pinned for the entry's build {variant['build_id']} ({PIN_PROBLEM} {identifier})")
            else:
                kinds = [kind for kind, item in figure_record(variant, files)["files"].items() if item != (pinned.get("files") or {}).get(kind)]
                if kinds:
                    unlike.append(f"Gen by Surface's figure is not the pinned one ({', '.join(kinds)})")
            # 2. The Library's view without the rules' looks is the figure.
            pixels = {mode: {"figure": rgba(figure[mode]["png"]), "bare": rgba(bare[mode]["png"])} for mode in MODES}
            for mode in MODES:
                if pixels[mode]["bare"] != pixels[mode]["figure"]:
                    apart = sum(1 for k in range(0, len(pixels[mode]["bare"]), 4) if pixels[mode]["bare"][k:k + 4] != pixels[mode]["figure"][k:k + 4])
                    unlike.append(f"{mode}: the Library's view without the look is not the figure ({apart} px)")
            # 3. The Library's view as the rules are gives the folder's pictures.
            paths = library_write.shot_files(identifier)
            kinds = [kind for kind, data in pictures.items()
                     if not (out / Path(paths[kind][0]).name).is_file() or (out / Path(paths[kind][0]).name).read_bytes() != data]
            if kinds:
                unlike.append(f"the folder's pictures are not the Library's view ({', '.join(kinds)})")
            # 4. In its look, the view differs from the figure on the part's pixels alone.
            said = "no look: the pictures are the figure's"
            if given:
                counted = {mode: view_differences(pixels[mode]["figure"], rgba(looked[mode]["png"]), rgba(other[mode]["png"])) for mode in MODES}
                unlike += [f"{mode}: {problem}" for mode in MODES for problem in view_problems(counted[mode])]
                said = "; ".join(f"{mode} {counted[mode]['part']} of {counted[mode]['drawn']} px the part's, the other {counted[mode]['sheets']} the figure's"
                                 for mode in MODES)
        except (ShotError, PlaywrightError) as error:
            failed.append(identifier)
            print(f"FAIL {identifier}: {error}", flush=True)
            continue
        if unlike:
            differ.append(identifier)
        print(f"{'DIFFERS' if unlike else 'same'} {identifier} ({number}/{len(chosen)}, {time.monotonic() - begun:.1f} s): "
              + ("; ".join(unlike) if unlike else f"the figure as pinned, the view without a look the figure, the pictures the view's; {said}"), flush=True)
    print(f"library_shots: Gen by Surface's figure and the Library's view of it checked for {len(chosen) - len(failed)} of {len(chosen)} sensors in "
          f"{time.monotonic() - started:.0f} s; {len(differ)} differ" + (f": {', '.join(differ)}" if differ else ""))
    return 1 if failed or differ else 0


def pin_generator(browser, url: str, entries: dict, chosen: list, pin: dict, figure: str, path: Path = GENERATOR_PIN) -> int:
    """--pin-generator: Gen by Surface's figure of each sensor as it is now written into the pin (the others' records
    kept, a record of no sensor of a part without a scene dropped), each change said."""

    from playwright.sync_api import Error as PlaywrightError

    shots = {identifier: record for identifier, record in (pin.get("shots") or {}).items() if identifier in entries["variants"]}
    failed = []
    for number, identifier in enumerate(chosen, 1):
        variant = entries["variants"][identifier]
        try:
            files, _ = encode(twice(identifier, lambda: generator_shoot(browser, url, identifier, variant)))
        except (ShotError, PlaywrightError) as error:
            failed.append(identifier)
            print(f"FAIL {identifier}: {error}", flush=True)
            continue
        fresh = figure_record(variant, files)
        was = shots.get(identifier)
        print(f"{'kept' if was == fresh else 'pinned anew' if was else 'pinned'} {identifier} ({number}/{len(chosen)})"
              + ("" if was in (None, fresh) else ": " + ", ".join(kind for kind in fresh["files"] if fresh["files"][kind] != (was.get("files") or {}).get(kind))
                 + (" (another build)" if was.get("build_id") != fresh["build_id"] else "")), flush=True)
        shots[identifier] = fresh
    if failed:
        print(f"library_shots: {len(failed)} sensors not shot; the pin is not written", file=sys.stderr)
        return 1
    text = pin_text(shots, figure)
    if not path.is_file() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    print(f"library_shots: {len(chosen)} sensors pinned in {path.name} ({len(shots)} in all)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=int(os.environ["FPC_PORT"]) if os.environ.get("FPC_PORT") else None,
                        help="the port of a running app.py serving this project (default FPC_PORT)")
    parser.add_argument("--only", default=None, metavar="ID,...", help="shoot only these sensors (the others' records kept)")
    parser.add_argument("--out", type=Path, default=OUT, help=f"the pictures' folder (default {OUT.relative_to(ROOT)}; the art goes "
                        "into an art/ folder beside it)")
    parser.add_argument("--check", action="store_true", help="shoot again and compare with the manifest and the art; write nothing")
    parser.add_argument("--check-generator", default=None, nargs="?", const="", metavar="ID,...",
                        help="Gen by Surface's figure of these sensors (of every part without a scene) against its pin, and the Library's "
                        "view against that figure; write nothing")
    parser.add_argument("--pin-generator", default=None, nargs="?", const="", metavar="ID,...",
                        help="write Gen by Surface's figure of these sensors (of every part without a scene) into the pin")
    parser.add_argument("--sheet", type=Path, default=None, help="write a contact sheet (PNG) of the manifest's Exploded cards")
    parser.add_argument("--showcase", action="store_true",
                        help="shoot the showcase's three pictures from its own page instead (into web/library/showcase/, with "
                             "showcase.json's placed, image and shot); with --check compare and write nothing")
    args = parser.parse_args(argv)
    if args.port is None:
        parser.error("give --port (or FPC_PORT): the port of a running app.py serving this project")
    url = f"http://127.0.0.1:{args.port}/"
    if args.showcase:
        if args.only is not None or args.check_generator is not None or args.pin_generator is not None or args.sheet is not None:
            parser.error("--showcase shoots the showcase alone (with --check and --out only)")
        return showcase_run(url, args.port, args.check, (LIBRARY / "showcase") if args.out == OUT else args.out.resolve())
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
    generator = args.check_generator if args.check_generator is not None else args.pin_generator
    listed = generator if generator is not None else args.only
    chosen = order(entries) if not listed else [item for item in re.split(r"[,\s]+", listed) if item]
    unknown = [identifier for identifier in chosen if identifier not in entries["variants"]]
    if unknown or not chosen:
        print(f"library_shots: no sensor is named {', '.join(unknown) or repr(listed)}", file=sys.stderr)
        return 2
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

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
    # parts.json's parts (their families): a part without a scene may take a look from the rules (part_looks).
    parts = json.loads((LIBRARY / "parts.json").read_text(encoding="utf-8"))
    if generator is not None:
        # Gen by Surface's figure: of the sensors of parts without a scene (a gripper's picture is its whole scene).
        fingertips = fingertip_sensors(entries, scenes.get("scenes") or {})
        chosen = chosen if generator else fingertips
        whole = [identifier for identifier in chosen if identifier not in fingertips]
        if whole:
            print(f"library_shots: {', '.join(whole)}: a gripper's sensor, pictured as its whole scene: Gen by Surface's figure is compared for "
                  "the parts without a scene only", file=sys.stderr)
            return 2
        pin = read_pin()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=WEBGL_ARGS)
            try:
                if args.pin_generator is not None:
                    return pin_generator(browser, url, entries, chosen, pin, figure)
                return check_generator(browser, url, out, entries, chosen, scenes, parts, pin)
            finally:
                browser.close()
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
                           view=view, stage=stage, part_look=library_write.part_look_sha256(library_write.part_look(scenes, parts, variant["part"])))
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
                same_stage = kept.get("stage") == fresh.get("stage") and kept.get("part_look_sha256") == fresh.get("part_look_sha256")
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
