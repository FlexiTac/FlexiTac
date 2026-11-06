"""The Library (library.html, web/library.js; the user's requests of 2026-11-05) in the browser.

Against a running app.py (FPC_PORT, as the other checks), or with --site a built static site (tools/build_static_site.py;
served here under /flexitac-gen/ on FPC_STATIC_PORT, default FPC_PORT + 1, as GitHub Pages serves a project site):

- part_layout (the layout of 2026-11-06: the user's "其他夹爪的话,不需要每个夹爪一row,你就每个row放4个夹爪就好了", "只有
  umi finger在首页而可以显示重复,其他的夹爪后面就只出现一次,然后标注一下点进去我们有1-3mm customization" and "UMI
  Fin-Ray Gripper. ... 这个section可以放在夹爪的后面"): at 1440, 1100, 900, 768, 744, 735, 734, 600, 390, 360 and 320 px
  no horizontal page overflow (320 px since the header's below-360 rules of 2026-11-05); no tile and no "Start here.";
  the grippers' section first ('Grippers. Seven, each fitted at four pitches.'), its seven cards in the parts' order
  (gripper-<part>, opening #<part>-2mm, named by the gripper, its two grey lines its range, '1 to 3 mm', and 'Pick your
  pitch', no badge line), four to a row from 735 px (4 + 3) and two below (2 + 2 + 2 + 1), never wider than the UMI
  shelf's cards from 735 px and as wide from 1100 px, every grey line on one line and no text past its card's box down
  to 320 px; then the UMI finger's shelf, its pitches by pitch ('1 mm pitch', 'Fine' on the 1 mm one) closed by the
  tapered tips' family card, four cards in view from 1100 px, three from 735 px, 78 % of the row below, its five
  overflowing with their arrows at 1440 px, 56 px below the grid's last row; at 390 px its row overflows (never the
  page), '<' is off at its start and '>' moves it by one card, and an arrow Tabbed to shows its focus ring inside the
  window at 390 and 360 px; both headings in the shelves' one wording ('UMI Fin-Ray Gripper. Four pitches, 1 to 3 mm,
  and tapered tips.'; the user's decision of 2026-11-05), one line at 1440 and 1280 px, never splitting a range or a
  family's clause, at most two lines at 900 px broken between phrases.
- part_first_screen (the user's decision of 2026-11-05: the picture may be squashed): below 900 px a sensor's picture
  is 3:1 above Open (16:10 beside it from 900 px), shown, its drawing contained and centred; Open's bottom in the
  window at 390 x 844 on every sensor's page and the Tapered tips page, at 360 x 740 on every gripper's sensor page,
  and reported at 375 x 667, 320 x 640 and 320 x 568 (the header alone is 239 px there); since the pictures of
  2026-11-05 in both cases (CASES): with pictures (the picture and its Exploded | Assembled control inside the frame
  above Open, the picture contained and centred) and with none (the placeholder's drawing, as before); since the 3D
  view of 2026-11-05 the pictures' case with every sensor's view set and with none (VIEW_CASES), with views each
  phone's two sample pages measured again once the view is drawn over the picture: nothing moves, the view's box the
  slot's.
- part_pictures (the on-part figure on the cards and a sensor's page, the user's request of 2026-11-05; the pictures'
  contract: entries.json's "image", shots/<id>.exploded.webp, .assembled.webp and .exploded.card.webp): the tree's own
  pictures when entries.json names them, else stand-ins drawn here in the browser and served for the contract's
  "image" (nothing committed).  Every card of the grid (the grippers' seven, each its 2 mm sensor's, the UMI shelf's
  and its Tapered tips card with its default tip's: 12) shows its sensor's Exploded card picture, contained and
  centred in its light box, lazy, decoded async, its width and height set (no card moves as they arrive), its alt the
  entry's, the bytes asked for as the page opens within the first screen's 1 MB; a sensor's page shows the Exploded
  picture (eager) with a
  grey "Exploded | Assembled" control under it (a group named View, two radios, never blue, no transition) that swaps
  the picture in place (the address, the history and the focus kept; the arrow keys too), the view kept across the
  pitch, Shape and Tip width (the picture the new sensor's) and the Exploded one again on each page opened; the light
  box light in the dark scheme too; no sideways scroll from 1440 to 320 px; a picture that does not load gives way to
  its placeholder (never a broken image or an empty box), the control kept while a view is left and gone once both
  failed, no console error but those files' 404s; with every sensor's 3D view set and with none (VIEW_CASES).
- part_view (a sensor's page in 3D, the user's request of 2026-11-05: "lib 点进去具体的每个夹爪的时候, 那个图也做成可以三维
  旋转的"; web/cad/library_view.js over the picture's slot, docs/LIBRARY_VIEW.md): with every variant's "view" set (the
  art the tree's own, or made by the generator's page under app.py as the shots tool makes it, nothing written; the
  scenes the tree's), at 1440 x 900 and a 390 x 844 phone (touch, DPR 3), on Trossen WidowX AI's 2 mm sensor (a whole
  gripper, its other finger see-through in both views, its stack assembled) and the UMI finger's (?probe: #libViewState
  read): the grid loads no three.js and no web/cad module; the picture first (eager, loaded, shown; the view hidden), then the view drawn over
  it (the picture hidden), never neither, the picture's box and Open never moving, the view's host and canvas the slot's
  box; nothing renders at rest (no frame asked for, no WebGL draw over 500 ms: COUNTERS); a group named by the picture's
  alt, in the tab order, described by its hint, its canvas aria-hidden with touch-action pan-y; at each home, its host at
  the pictures' pane (640 x 400 CSS px, 1280 x 800), the drawing where its picture's is (margins within 1 px; the view's
  own lens shift) and, written as the shots tool writes a picture, its picture (colours within 1 level on average, 99 %
  within 16), where the picture was shot from the view (its record has art, or its part has no scene); a drag, ArrowLeft
  and ArrowUp turn it, 0 and a double click bring it home; the Exploded | Assembled switch drives it both ways; Tab
  reaches it with its focus ring; at 390 px a vertical swipe scrolls the page and a sideways one turns the view; no
  request for the API, py/, Pyodide, backend.js or app.js, no console error; the UMI finger drawn after the gripper on
  the same page (one view, the stage's scene taken down) as on a page of its own; without WebGL, without
  DecompressionStream, its art a 404 or with Save-Data (no three.js then) the picture stays, no uncaught error; in the
  dark scheme the view drawn in the picture's light box.
- part_placeholders (no picture: every "image" null): every slot the drawing of its field (its rows and columns), no
  image, no view control and no request for a picture, as before the pictures.
- part_family (the tapered tips, 2026-11-05): the family card ends the UMI shelf ('Tapered tips', its two lines), no
  tip has a shelf or another card; it opens #umi-tapers, the default tip's page (the 13.8 mm trapezoid) with Shape
  and Tip width in place of the pitch; a change of either replaces the address (no history entry) with the grid's
  sensor, that control focused; Back returns to the grid, the family card focused; a tip's id or part id opens its
  page directly, its back link going to the UMI shelf; the action blue only on Open in Gen by Surface.
- part_grid (2026-11-06): each gripper's card opens its 2 mm sensor's page, whose Pitch reaches its four pitches, and
  every one of the 42 sensors' pages is reached by clicks alone (the cards, the Pitch, the tapered tips' Shape and Tip
  width); a page's back link (#gripper-<part>) puts the grid back where it was with its card focused; the older
  addresses land sensibly: #shelf-<gripper> on its card (the address #gripper-<part>, no history entry), #shelf-start
  at the top with no hash (opened anew, and typed with the grid scrolled down), #shelf-umi-finray and #grippers on
  their sections.
- part_routes: a gripper's card opens its sensor's page at the top with its title focused and the tab named after it,
  Open in Gen by Surface at ./?part=<id>, at least as wide as each download pill; another pitch replaces the address
  (no history entry); Back returns to the grid where it was, the card that opened it focused, the tab the Library's
  again; Back and Forward against the back links (the review of 2026-11-06: the WidowX 250 card, its back link, the
  MakerMods card, Back to the grid where it was with MakerMods focused, Back to the WidowX page, its back link to the
  WidowX card, Back and Forward to the grid where it was, WidowX focused); #shelf-widowx-250 typed on the ARX X5 page
  its card; #<part> shows its 2 mm sensor with the address kept, #shelf-arx-x5 opened anew its card, #bogus the grid
  with a note, an unknown id typed with the grid scrolled down its note in sight; the back link of a page opened
  directly goes to its card.
- part_downloads: under app.py the two Gerber ZIPs are app.py's exports of the sensor's design (the fit's proposal #1),
  byte for byte under its names; on the site they are the prebuilt files (files.json, which lists every sensor);
  the part's STL is the mesh, the licence is served (a tapered tip's ZIPs too).
- part_isolation: only the site's own requests (none to py/, a worker, backend.js or app.js; three.js and the web/cad
  modules on a sensor's page with its 3D view only, never on the grid), no console error; the page never says CAD (its
  text, titles, labels) and is English; in light and dark, with every view set and with none, the action blue fills
  only Open in Gen by Surface, nothing green, and scrolling changes nothing.
- part_errors: entries.json missing: the page says so and the header still works; on the site, files.json missing:
  the downloads give way to the note.
"Dark" is the page's dark look as the header's toggle leaves it (its stored choice, rp.DARK_CHOICE; 2026-11-06: the page
opens light whatever the system's scheme, which stays light here).
Screenshots go to $FPC_BROWSER_OUT/shots (library_*.png; the pictures' library_pictures_* and library_placeholders_*:
the grid at 1440 and 900 px light and dark, a sensor's page Exploded and Assembled and the Tapered tips page at 1440 px
and 390 x 844, library_pictures_view_* with the 3D view; the 3D view's library_view_*: each sensor at its home, dragged,
Assembled, focused and, at 390 px, swiped, without WebGL and dark).  Chromium runs on SwiftShader (WebGL, as
cad_checks.py) for every part.

    FPC_PORT=18920 python3 tools/browser/library_checks.py
    FPC_PORT=18920 python3 tools/browser/library_checks.py --site site/
"""
from __future__ import annotations

import argparse
import base64
import functools
import io
import json
import os
import re
import sys
import threading
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.sync_api import sync_playwright  # noqa: E402

from rp import DARK_CHOICE, PORT, SCRATCH, SHOTS, URL, check, summary, wait_until  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import library_shots  # noqa: E402
import library_write  # noqa: E402

LIBRARY = ROOT / "web" / "library"
ENTRIES = json.loads((LIBRARY / "entries.json").read_text(encoding="utf-8"))
# WebGL on SwiftShader (as cad_checks.py and the shots tool): a sensor's page draws its 3D view.
WEBGL_ARGS = ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
STATIC_PORT = int(os.environ.get("FPC_STATIC_PORT", str(PORT + 1)))
SUBPATH = "flexitac-gen"
SITE = {"base": URL, "root": None}
READY = "() => document.querySelectorAll('.lib-card').length > 0 || document.getElementById('libStatus').textContent !== ''"
# 768 to 734 px: the grippers' grid turns from four to a row to two at the UMI shelf's own 735 px (2026-11-06).
WIDTHS = (1440, 1100, 900, 768, 744, 735, 734, 600, 390, 360, 320)
COUNTS = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten")
# The grid (the user's requests of 2026-11-06; library.js SHELVED): the grippers' section, one card per part but the
# shelved (the UMI finger, and any part a family closes), each opening its 2 mm sensor, then each shelved part's shelf;
# GRID_CARDS: the sensors whose card pictures the grid shows, in its order (12), all asked for as the page opens (it is
# short), within FIRST_SCREEN_BYTES (test_library's).
SHELVED = ["umi-finray"] + [family["shelf"] for family in ENTRIES["families"].values() if family["shelf"] != "umi-finray"]
CARDED = [part for part in ENTRIES["order"] if part not in SHELVED]
SHELVES = [part for part in ENTRIES["order"] if part in SHELVED]
FAMILIES_OF = {part: [name for name, family in ENTRIES["families"].items() if family["shelf"] == part] for part in ENTRIES["order"]}
GRID_CARDS = library_shots.grid_cards(ENTRIES)
FIRST_SCREEN_BYTES = 1_000_000


def pitch_range(part):
    """A gripper card's first grey line: its pitches' range ('1 to 3 mm', '1 to 2.5 mm')."""
    pitches = sorted(ENTRIES["variants"][key]["pitch_mm"] for key in ENTRIES["parts"][part]["variants"])
    return f"{pitches[0]:g} mm" if pitches[0] == pitches[-1] else f"{pitches[0]:g} to {pitches[-1]:g} mm"


# The phones of the first-screen check (part_first_screen): Open in the first screen at 390 x 844 on every page, at
# 360 x 740 on every gripper's; at the others its place is reported (the header alone is 239 px there).
PHONES = ((390, 844), (375, 667), (360, 740), (320, 640), (320, 568))
# The pictures (the user's request of 2026-11-05: the cards show the finger and the sensor on it, the generator's
# on-part figure; their contract with tools/library_write.py and the shots tool): a variant's "image" is null or
# image_record()'s, its files in web/library/shots/.  PICTURED: whether this tree's entries.json names any (once the
# shots tool has run).  Each check of the pictures runs in both CASES whatever the tree holds: "pictures" serves the
# contract's record for every sensor when the tree has none, its files stand-ins drawn here in the browser (STAND_IN:
# a part and a sensor, the Exploded view's sensor amber and the Assembled one's dark, so a swap shows; nothing is
# committed), and "placeholders" serves entries.json with every image null when the tree has pictures.
PICTURED = any(variant["image"] for variant in ENTRIES["variants"].values())
CASES = ("pictures", "placeholders")
CARD_SIZE = (640, 400)
SHOT_SIZE = (1280, 800)
STAND_IN = """([width, height, tone]) => { const canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
  const g = canvas.getContext('2d'); const s = width / 1280;
  g.fillStyle = '#c7c8cc'; g.beginPath(); g.roundRect(440 * s, 380 * s, 400 * s, 380 * s, 36 * s); g.fill();
  g.fillStyle = tone; g.beginPath(); g.roundRect(480 * s, 100 * s, 320 * s, 240 * s, 14 * s); g.fill();
  return canvas.toDataURL('image/webp', 0.9); }"""
STAND_INS = {}


def image_record(identifier):
    """The contract's "image" of a sensor (tools/library_write.py writes it from web/library/shots/manifest.json)."""
    return {"exploded": {"src": f"shots/{identifier}.exploded.webp", "card": f"shots/{identifier}.exploded.card.webp",
                         "width": SHOT_SIZE[0], "height": SHOT_SIZE[1]},
            "assembled": {"src": f"shots/{identifier}.assembled.webp", "width": SHOT_SIZE[0], "height": SHOT_SIZE[1]},
            "alt": f"{ENTRIES['variants'][identifier]['label']} on the part"}


# Each sensor's picture in the "pictures" case: the tree's own (null where it has none), or the contract's record.
IMAGES = {key: (variant["image"] if PICTURED else image_record(key)) for key, variant in ENTRIES["variants"].items()}
# The 3D view of a sensor's page (the user's request of 2026-11-05, "lib 点进去具体的每个夹爪的时候, 那个图也做成可以三维旋转
# 的"; docs/LIBRARY_VIEW.md): a variant's "view" is null (the picture alone) or {"art": "art/<id>.json.gz", "scene": its
# part's scene or null}, written by tools/library_write.py for a sensor shot from the view.  The pictures' checks run with
# every view set (VIEW_CASES True: the art the tree's own, web/library/art/, or, before the shoot commits it, made here
# by the generator's page under app.py as the shots tool makes it, nothing written; the scenes the tree's) and with every
# view null.  VIEWED: whether this tree's entries.json sets any.
SCENES = library_write.scenes_index(LIBRARY).get("scenes") or {}
VIEWED = any(variant.get("view") for variant in ENTRIES["variants"].values())
VIEW_CASES = (True, False)
ARTS = {}


def arts(browser):
    """{id: its art file's bytes, or None} of every sensor: the tree's own art/<id>.json.gz, else (under app.py) the art
    the shots tool would write, made by the generator's page (library_shots.art_document; nothing written), else None
    (a built site without the shoot's art: the view's cases are left out)."""
    if not ARTS:
        for key in ENTRIES["variants"]:
            path = LIBRARY / library_write.art_path(key)
            ARTS[key] = path.read_bytes() if path.is_file() else None
        missing = [key for key, data in ARTS.items() if data is None]
        if missing and SITE["root"] is None:
            started = time.monotonic()
            page = library_shots.art_page(browser)
            try:
                for key in missing:
                    ARTS[key] = library_write.art_bytes(library_shots.art_document(page, URL, key, ENTRIES["variants"][key]))
            finally:
                page.context.close()
            print(f"    the art of {len(missing)} sensors made by the generator's page in {time.monotonic() - started:.0f} s "
                  "(the shoot's stand-ins: nothing written)", flush=True)
    return ARTS


def view_of(key):
    """entries.json's "view" of a sensor in the cases with views: its art and its part's scene (null without its art)."""
    if not ARTS.get(key):
        return None
    return {"art": library_write.art_path(key), "scene": SCENES.get(ENTRIES["variants"][key]["part"])}


def view_cases(browser):
    """VIEW_CASES this run can serve: with every view set only where there is art for it."""
    available = any(arts(browser).values())
    if not available:
        print("    no art for the 3D view (a built site without the shoot's art/): its cases left out", flush=True)
    return tuple(view for view in VIEW_CASES if view is False or available)


def stand_ins(browser):
    """The stand-in WebPs by their names' ends (drawn once in a blank page; WebP with alpha, as the shots are)."""
    if not STAND_INS:
        context = browser.new_context()
        page = context.new_page()
        for end, (width, height), tone in ((".exploded.card.webp", CARD_SIZE, "#d97b06"), (".exploded.webp", SHOT_SIZE, "#d97b06"),
                                           (".assembled.webp", SHOT_SIZE, "#2f3136")):
            url = page.evaluate(STAND_IN, [width, height, tone])
            if not url.startswith("data:image/webp;base64,"):
                raise RuntimeError(f"this Chromium writes no WebP ({url[:30]})")
            STAND_INS[end] = base64.b64decode(url.split(",", 1)[1])
        context.close()
    return STAND_INS


def library_case(page, case, missing=(), view=False):
    """The page served for a case of CASES: entries.json with the contract's pictures or with none, and in the pictures'
    case each variant's "view" set (``view``: its art served from arts()) or null; the pictures' files the tree's or the
    stand-ins, those named in ``missing`` (their file names, an art file's too) a 404."""
    served = json.loads(json.dumps(ENTRIES))
    if view:
        arts(page.context.browser)
    for key, variant in served["variants"].items():
        if case == "placeholders":
            variant["image"] = None
        elif not PICTURED:
            variant["image"] = IMAGES[key]
        variant["view"] = view_of(key) if view and case == "pictures" else None
    body = json.dumps(served)
    page.route("**/static/library/entries.json", lambda route: route.fulfill(status=200, content_type="application/json", body=body))
    if view:
        def art(route):
            name = route.request.url.split("?")[0].rsplit("/", 1)[-1]
            data = ARTS.get(name[:-len(".json.gz")]) if name.endswith(".json.gz") else None
            if name in missing or not data:
                route.fulfill(status=404, content_type="text/plain", body="not here")
            else:
                route.fulfill(status=200, content_type="application/gzip", body=data)
        page.route("**/static/library/art/**", art)
    if case != "pictures":
        return
    files = stand_ins(page.context.browser) if not PICTURED else {}

    def shot(route):
        name = route.request.url.split("?")[0].rsplit("/", 1)[-1]
        if name in missing:
            route.fulfill(status=404, content_type="text/plain", body="not here")
        elif PICTURED:
            route.continue_()
        else:
            route.fulfill(status=200, content_type="image/webp", body=next(body for end, body in files.items() if name.endswith(end)))
    page.route("**/static/library/shots/**", shot)
# The grid's sections in order, the shelves' rows (each row's cards and arrows, their sizes against the row's inner
# width) and the grippers' cards (2026-11-06: each one's address, jump, name, grey lines and the rows each takes, its
# top and width, and how far its text runs past its card's text box, the box's padding off).
LAYOUT = """() => { const de = document.documentElement;
  const rowsOf = node => { const range = document.createRange(); range.selectNodeContents(node);
    return new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size; };
  const rows = [...document.querySelectorAll('#libShelves .lib-shelf')].map(shelf => { const track = shelf.querySelector('.lib-track');
    const cards = [...track.querySelectorAll('.lib-card')]; const style = getComputedStyle(track);
    const inner = track.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    return {id: shelf.id, cards: cards.map(card => card.dataset.variant || `family:${card.dataset.family}`), over: track.scrollWidth > track.clientWidth + 1,
            arrows: !shelf.querySelector('.lib-arrows').hidden, inner, gap: parseFloat(style.columnGap), card: cards[0].getBoundingClientRect().width,
            names: cards.map(card => card.querySelector('.lib-card-name').textContent),
            badges: cards.filter(card => card.dataset.variant).map(card => card.querySelector('.lib-badge')?.textContent ?? null),
            heading: shelf.querySelector('h3').textContent.replace(/\u00a0/g, ' ')}; });
  const section = document.getElementById('grippers');
  const grid = section && {heading: section.querySelector('h3').textContent.replace(/\u00a0/g, ' '), badges: section.querySelectorAll('.lib-badge').length,
    cards: [...section.querySelectorAll('.lib-cards > .lib-card')].map(card => { const text = card.querySelector('.lib-card-text');
      const box = text.getBoundingClientRect(); const style = getComputedStyle(text);
      const [left, right] = [box.left + parseFloat(style.paddingLeft), box.right - parseFloat(style.paddingRight)];
      const past = Math.max(0, ...[...text.children].flatMap(span => { const range = document.createRange(); range.selectNodeContents(span);
        return [...range.getClientRects()].filter(r => r.width > 0).map(r => Math.max(left - r.left, r.right - right)); }));
      const r = card.getBoundingClientRect();
      return {id: card.id, href: card.getAttribute('href'), variant: card.dataset.variant, name: card.querySelector('.lib-card-name').textContent.replace(/\u2011/g, '-'),
              nameRows: rowsOf(card.querySelector('.lib-card-name')), lines: [...card.querySelectorAll('.lib-card-line')].map(n => n.textContent.replace(/\u00a0/g, ' ')),
              lineRows: [...card.querySelectorAll('.lib-card-line')].map(rowsOf), top: Math.round(r.top + scrollY), width: r.width, past: Math.round(past * 10) / 10}; })};
  const main = document.querySelector('main.lib');
  return {overflow: de.scrollWidth - de.clientWidth, main: main.scrollWidth - main.clientWidth, rows, grid,
          order: [...document.getElementById('libShelves').children].map(n => n.id), tiles: document.querySelectorAll('.lib-tile, #libTiles').length}; }"""
# The title's line (the review of 2026-11-05): each of its lines' right end against the content's right edge (the gutter),
# its lines, and whether "open-source" (its no-break hyphen) or the mode's name "Gen by Surface" (with spaces or its
# no-break spaces; the integration's review of 2026-11-05: "Gen by" / "Surface" from 860 to 1024 px and at 600 px) is
# split over two lines (null: one of them missing).
HERO = """() => { const tag = document.querySelector('.lib-tagline'); const main = document.querySelector('main.lib');
  const edge = main.getBoundingClientRect().right - parseFloat(getComputedStyle(main).paddingRight);
  const rows = {}; const walker = document.createTreeWalker(tag, NodeFilter.SHOW_TEXT); const splits = {};
  while (walker.nextNode()) { const node = walker.currentNode; const range = document.createRange(); range.selectNodeContents(node);
    for (const r of range.getClientRects()) { if (r.width <= 0) continue; const k = Math.round(r.top); rows[k] = Math.max(rows[k] ?? -1e9, r.right); }
    for (const [word, pattern] of [['open-source', /open\u2011source/], ['Gen by Surface', /Gen[ \u00a0]by[ \u00a0]Surface/]]) {
      const found = pattern.exec(node.data); if (!found) continue;
      const one = document.createRange(); one.setStart(node, found.index); one.setEnd(node, found.index + found[0].length);
      splits[word] = new Set([...one.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size > 1; } }
  const split = Object.keys(splits).length === 2 ? Object.values(splits).some(Boolean) : null;
  return {lines: Object.keys(rows).length, ends: Object.values(rows).map(right => Math.round(edge - right)), split}; }"""
# Each section's room below its cards (to the next heading), its heading's lines and whether its arrows show (the review
# of 2026-11-05; since 2026-11-06 the grippers' section, then the UMI shelf).
SPACING = """() => [...document.querySelectorAll('#libShelves > .lib-shelf, #libShelves > .lib-section')].map((shelf, i, all) => {
  const bottom = Math.max(...[...shelf.querySelectorAll('.lib-card')].map(card => card.getBoundingClientRect().bottom));
  const heading = shelf.querySelector('h3'); const range = document.createRange(); range.selectNodeContents(heading);
  const lines = new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size;
  return [shelf.id, all[i + 1] ? Math.round(all[i + 1].querySelector('h3').getBoundingClientRect().top - bottom) : null, lines,
          Boolean(shelf.querySelector('.lib-arrows')) && !shelf.querySelector('.lib-arrows').hidden]; })"""
# Each shelf heading's lines, as text (the user's decision of 2026-11-05 on its one wording: the range '1 to 3 mm' and a
# family's clause 'and tapered tips' each on one line, a two-line heading broken between its phrases).
HEADING_LINES = """() => [...document.querySelectorAll('#libShelves .lib-shelf h3, #libShelves .lib-section h3')].map(heading => { const lines = []; let top = null;
  const walker = document.createTreeWalker(heading, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) { const text = walker.currentNode;
    for (let i = 0; i < text.data.length; i += 1) { const range = document.createRange(); range.setStart(text, i); range.setEnd(text, i + 1);
      const box = [...range.getClientRects()].find(r => r.width > 0); if (!box) { if (lines.length) lines[lines.length - 1] += text.data[i]; continue; }
      if (Math.round(box.top) !== top) { lines.push(''); top = Math.round(box.top); } lines[lines.length - 1] += text.data[i]; } }
  return [heading.closest('.lib-shelf, .lib-section').id, lines.map(line => line.replace(/\u00a0/g, ' ').trim())]; })"""
# A sensor's page at the window's top: Open's box, the picture's box (its frame's and the slot's) and what draws in it,
# the window, the page's overflow; the picture's fit (its own, or, for the placeholder's drawing, that of an <img> put
# in the slot as a picture would be), whether a picture has loaded, and the box of its view control (null: none).
FIRST_SCREEN = """() => { const box = node => { const r = node.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom].map(v => Math.round(v * 10) / 10); };
  const shot = document.querySelector('#libDetail .lib-shot'); const drawing = shot.firstElementChild; const open = document.querySelector('.lib-open');
  const pictured = drawing.tagName === 'IMG'; const img = pictured ? drawing : document.createElement('img');
  if (!pictured) { img.width = 1280; img.height = 800; img.alt = ''; shot.append(img); }
  const style = getComputedStyle(img); const fitted = [style.objectFit, style.objectPosition]; if (!pictured) img.remove();
  const frame = shot.closest('.lib-frame'); const view = frame.querySelector('.lib-view .lib-seg-track');
  const host = frame.querySelector('.lib-live'); const live = host && host.querySelector('canvas') && host.checkVisibility({visibilityProperty: true}) ? box(host) : null;
  return {open: box(open), frame: box(frame), shot: box(shot), drawing: [drawing.tagName.toLowerCase(), ...box(drawing)], live,
          meet: drawing.getAttribute('preserveAspectRatio'), visible: shot.checkVisibility() && drawing.checkVisibility(), fitted,
          loaded: pictured ? drawing.complete && drawing.naturalWidth > 0 : null, view: view ? box(view) : null, children: shot.children.length,
          screen: innerHeight, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth}; }"""
# A sensor's page's 3D view drawn over its picture (its host and canvas shown).
LIVE_SHOWN = """() => { const host = document.querySelector('#libDetail .lib-live'); const canvas = host && host.querySelector('canvas');
  return Boolean(canvas) && host.checkVisibility({visibilityProperty: true}) && canvas.checkVisibility({visibilityProperty: true}); }"""
# A sensor's page's picture loaded (or its placeholder drawn in its place).
PICTURE_SETTLED = """() => { const shot = document.querySelector('#libDetail .lib-shot'); const img = shot && shot.querySelector('img');
  return Boolean(shot) && (!img || (img.complete && img.naturalWidth > 0)); }"""
FOCUS = """() => { const node = document.activeElement; return {id: node.id, variant: node.dataset?.variant || null,
  shelf: node.closest('.lib-shelf, .lib-section')?.id || null}; }"""
# A card of the grid in the window (its box and its focus ring's 4 px inside it) and the window's scroll.
IN_VIEW = """(id) => { const r = document.getElementById(id).getBoundingClientRect();
  return {inside: r.top - 4 >= 0 && r.bottom + 4 <= innerHeight, top: Math.round(r.top), bottom: Math.round(r.bottom), y: Math.round(scrollY)}; }"""
VIEW = """() => ({hash: location.hash, detail: !document.getElementById('libDetail').hidden, grid: !document.getElementById('libGrid').hidden,
  y: Math.round(scrollY), history: history.length, tab: document.title, note: document.getElementById('libNote').hidden ? null : document.getElementById('libNote').textContent,
  checked: document.querySelector('input[name="libPitch"]:checked')?.value || null, title: document.getElementById('libDetailTitle')?.textContent.replace(/\u2011/g, '-') || null,
  open: document.querySelector('.lib-open')?.getAttribute('href') || null})"""
# Where the window is and where a jump to the shelf puts it (its top at its scroll margin, or the page's end: the last
# shelves cannot reach the top), and the page's scroll-behavior.
SHELF_TOP = """(id) => { const shelf = document.getElementById(id); const de = document.documentElement;
  const target = shelf.getBoundingClientRect().top + scrollY - parseFloat(getComputedStyle(shelf).scrollMarginTop);
  return [scrollY, Math.max(0, Math.min(target, de.scrollHeight - innerHeight)), getComputedStyle(de).scrollBehavior]; }"""
# Fills of every visible element larger than 12 px: the action blue (or any blue) and green.
FILLS = r"""() => { const parse = s => { const m = s && s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const blue = c => c && c.a > 0 && c.b > c.r + 80 && c.b > c.g + 40; const green = c => c && c.a >= .5 && c.g > c.r + 40 && c.g > c.b + 40;
  const found = {blue: [], green: []};
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('svg') || !el.checkVisibility()) continue;
    const r = el.getBoundingClientRect(); if (r.width <= 12 || r.height <= 12) continue;
    const c = parse(getComputedStyle(el).backgroundColor); const name = el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ').join('.') : '');
    if (blue(c)) found.blue.push(name); if (green(c)) found.green.push(name); }
  return found; }"""
SNAPSHOT = """() => ({nodes: [...document.querySelectorAll('body, body *')].filter(n => !n.closest('svg') || n.tagName.toLowerCase() === 'svg').map(n => { const s = getComputedStyle(n);
  return [s.opacity, s.transform, s.visibility, s.filter, n.className && typeof n.className === 'string' ? n.className : ''].join('|'); }),
  animations: document.getAnimations().length})"""
WORDS = """() => [document.title, document.body.innerText, ...[...document.querySelectorAll('[title], [aria-label]')].flatMap(n => [n.getAttribute('title') || '', n.getAttribute('aria-label') || ''])]"""


def new_page(browser, width=1440, height=900, scheme="light"):
    # ``scheme`` the page's look: "dark" the header's toggle on (its stored choice, DARK_CHOICE; 2026-11-06), the system's
    # own scheme light either way (the page no longer follows it).
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme="light", accept_downloads=True)
    if scheme == "dark":
        context.add_init_script(DARK_CHOICE)
    page = context.new_page()
    page.logs, page.requests = [], []
    page.on("console", lambda m: page.logs.append((m.type, m.text, (m.location or {}).get("url", ""))))
    page.on("pageerror", lambda e: page.logs.append(("pageerror", str(e), "")))
    page.on("request", lambda r: page.requests.append(r.url))
    return page


def errors_of(page, allowed=()):
    """Console errors, but the 404 of a resource a check answered so (``allowed``: the URL's end)."""
    return [entry[:2] for entry in page.logs if entry[0] in ("error", "pageerror")
            and not (any(entry[2].endswith(end) for end in allowed) and "status of 404" in entry[1])]


def open_library(page, fragment=""):
    page.goto(SITE["base"] + "library.html" + fragment)
    wait_until(page, READY, 30)
    page.wait_for_timeout(150)


def part_layout(browser):
    page = new_page(browser)
    open_library(page)
    # The UMI finger's shelf, closed by the tapered tips' family card; the grippers' cards before it (2026-11-06).
    expected_rows = [(f"shelf-{part}", ENTRIES["parts"][part]["variants"] + [f"family:{name}" for name in FAMILIES_OF[part]]) for part in SHELVES]
    expected_cards = [{"id": f"gripper-{part}", "href": f"#{ENTRIES['parts'][part]['default']}", "variant": ENTRIES["parts"][part]["default"],
                       "name": ENTRIES["parts"][part]["title"], "lines": [pitch_range(part), "Pick your pitch"]} for part in CARDED]
    rows_of, sizes_of, text_of = {}, {}, {}
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(120)
        layout = page.evaluate(LAYOUT)
        check(f"layout {width}: no horizontal page overflow", layout["overflow"] <= 0, layout["overflow"])
        per_view = 4 if width >= 1100 else 3 if width >= 735 else None
        sizes = []
        for row in layout["rows"]:
            expected = (row["inner"] - (per_view - 1) * row["gap"]) / per_view if per_view else 0.78 * row["inner"]
            sizes.append(abs(row["card"] - expected) <= 1)
        check(f"layout {width}: {per_view or '78 % of the row:'} {'cards in view' if per_view else 'a card'} on the UMI shelf", all(sizes) and layout["rows"],
              [(row["id"], round(row["card"], 1), round(row["inner"], 1)) for row in layout["rows"]][:3])
        cards = layout["grid"]["cards"] if layout["grid"] else []
        tops = sorted({card["top"] for card in cards})
        rows_of[width] = [sum(1 for card in cards if card["top"] == top) for top in tops]
        umi = layout["rows"][0]["card"] if layout["rows"] else 0
        sizes_of[width] = (round(max(card["width"] for card in cards), 1) if cards else None, round(umi, 1))
        text_of[width] = [(card["name"], card["lineRows"], card["past"]) for card in cards if any(rows != 1 for rows in card["lineRows"]) or card["past"] > 0.5]
        # The review of 2026-11-05: a shelf with its arrows hidden keeps their room; the grippers' section (no arrows)
        # as far from the UMI shelf's heading (its cards' 28 px and the shelf's) as the hero is from its own heading.
        spacing = page.evaluate(SPACING)
        check(f"layout {width}: the UMI shelf's heading 56 px below the grippers' last row", [(name, gap) for name, gap, _, _ in spacing if gap is not None] == [("grippers", 56)],
              [(name, gap, arrows) for name, gap, _, arrows in spacing])
        if width == 1440:
            check("layout: no tile and no 'Start here.'; the grippers' section, then the UMI finger's shelf",
                  layout["tiles"] == 0 and layout["order"] == ["grippers"] + [f"shelf-{part}" for part in SHELVES] and not page.query_selector("#shelf-start"),
                  (layout["tiles"], layout["order"]))
            check("layout: the UMI shelf with its variants by pitch, closed by the Tapered tips card",
                  [(row["id"], row["cards"]) for row in layout["rows"]] == expected_rows, [(row["id"], row["cards"]) for row in layout["rows"]])
            got = [{key: card[key] for key in ("id", "href", "variant", "name", "lines")} for card in cards]
            check("layout: the grippers' section a card per gripper in the parts' order (gripper-<part>, opening its 2 mm sensor, its name, "
                  "'1 to 3 mm' (its own range) and 'Pick your pitch'), no badge line",
                  got == expected_cards and layout["grid"]["badges"] == 0 and len(got) == 7
                  and {card["name"]: card["lines"][0] for card in got}.get("Franka Hand") == "1 to 2.5 mm",
                  [(one, other) for one, other in zip(got, expected_cards) if one != other][:2] or got[:2])
            headings = {row["id"]: row["heading"] for row in layout["rows"]}
            headings["grippers"] = layout["grid"]["heading"]
            # One wording on every heading (the user's decision of 2026-11-05): '<title>. <count> pitches, <finest> to
            # <coarsest> mm.', a shelf closing with families naming them after the range (the UMI finger's ', and tapered
            # tips'), here from entries.json's pitches, not its headings; the grippers' section its count and theirs.
            expected_headings = {"grippers": f"Grippers. {COUNTS[len(CARDED)]}, each fitted at {COUNTS[4].lower()} pitches."}
            for part in SHELVES:
                pitches = sorted(ENTRIES["variants"][key]["pitch_mm"] for key in ENTRIES["parts"][part]["variants"])
                clauses = "".join(f", and {ENTRIES['families'][name]['title'].lower()}" for name in FAMILIES_OF[part])
                expected_headings[f"shelf-{part}"] = (f"{ENTRIES['parts'][part]['title']}. {COUNTS[len(pitches)]} pitches, "
                                                      f"{pitches[0]:g} to {pitches[-1]:g} mm{clauses}.")
            check("layout: both headings in one wording, their bold half and their grey half ('Grippers. Seven, each fitted at four pitches.', "
                  "'UMI Fin-Ray Gripper. Four pitches, 1 to 3 mm, and tapered tips.')",
                  headings == expected_headings and headings["grippers"] == "Grippers. Seven, each fitted at four pitches."
                  and headings["shelf-umi-finray"] == "UMI Fin-Ray Gripper. Four pitches, 1 to 3 mm, and tapered tips."
                  and not [text for text in headings.values() if re.search(r"\b(fine|coarse)\b", text)],
                  {key: value for key, value in headings.items() if value != expected_headings.get(key)} or headings)
            # The review of 2026-11-05: a gripper's own shelf (its heading names the gripper) names its cards by their pitch.
            names = {row["id"]: row["names"] for row in layout["rows"]}
            expected_names = {f"shelf-{part}": [f"{ENTRIES['variants'][key]['pitch_mm']} mm pitch" for key in ENTRIES["parts"][part]["variants"]]
                              + [ENTRIES["families"][name]["title"] for name in FAMILIES_OF[part]] for part in SHELVES}
            check("layout: the UMI shelf's cards named by their pitch ('1 mm pitch'), its family card by its title",
                  names == expected_names, [(key, value) for key, value in names.items() if value != expected_names.get(key)][:3])
            check("layout 1440: the UMI shelf's five overflow, its arrows shown",
                  all(row["over"] and row["arrows"] and len(row["cards"]) == 5 for row in layout["rows"]),
                  [(row["id"], len(row["cards"]), row["over"], row["arrows"]) for row in layout["rows"]])
            # The second review of 2026-11-05: the UMI shelf's cards each with a badge line (empty but on the 1 mm one: the
            # names line up); a gripper's name never splits at a hyphen (U+2011: 'Dex1-1' whole).
            badges = {row["id"]: row["badges"] for row in layout["rows"]}
            check("layout 1440: a badge line on each card of the UMI shelf ('Fine', in capitals, on the 1 mm one)",
                  all(badges[f"shelf-{part}"] == [ENTRIES["variants"][key]["badge"] or "" for key in ENTRIES["parts"][part]["variants"]] for part in SHELVES)
                  and badges["shelf-umi-finray"][0] == "Fine", badges)
            page.screenshot(path=f"{SHOTS}/library_grid_1440.png")
        if width == 390:
            row = next(row for row in layout["rows"] if row["id"] == "shelf-umi-finray")
            arrows = page.evaluate("""() => { const s = document.getElementById('shelf-umi-finray'); const [l, r] = s.querySelectorAll('.lib-arrow');
                return [s.querySelector('.lib-track').scrollLeft, l.disabled, r.disabled]; }""")
            page.click("#shelf-umi-finray .lib-arrow[aria-label='Scroll right']"); page.wait_for_timeout(400)
            moved = page.evaluate("() => document.querySelector('#shelf-umi-finray .lib-track').scrollLeft")
            left = page.evaluate("() => document.querySelector('#shelf-umi-finray .lib-arrow[aria-label=\"Scroll left\"]').disabled")
            check("layout 390: the UMI shelf's row overflows inside itself (arrows shown), '<' off at its start, '>' moves it by one card",
                  row["over"] and row["arrows"] and arrows == [0, True, False] and abs(moved - (row["card"] + row["gap"])) <= 2 and left is False,
                  (row["over"], row["arrows"], arrows, moved, row["card"] + row["gap"], left))
            page.evaluate("() => { document.querySelector('#shelf-umi-finray .lib-track').scrollLeft = 0; }"); page.wait_for_timeout(100)
            page.screenshot(path=f"{SHOTS}/library_grid_390.png")
    check("layout: the grippers four to a row from 735 px (4 + 3), two below (2 + 2 + 2 + 1), never three",
          all(rows_of[width] == ([4, 3] if width >= 735 else [2, 2, 2, 1]) for width in WIDTHS), rows_of)
    check("layout: from 735 px a gripper's card never wider than the UMI shelf's, as wide from 1100 px",
          all(grid <= umi + 0.5 for width, (grid, umi) in sizes_of.items() if width >= 735)
          and all(abs(grid - umi) <= 1 for width, (grid, umi) in sizes_of.items() if width >= 1100), sizes_of)
    check("layout: from 1440 to 320 px every grey line of a gripper's card on one line, no text past its card's box",
          not any(text_of.values()), {width: found for width, found in text_of.items() if found})
    # Tabbed to, the UMI shelf's arrow shows its whole focus ring in the window (the review of 2026-11-06: at 390 x 844
    # it sat on the window's bottom edge, its ring cut).
    rings = {}
    for width, height in ((390, 844), (360, 740)):
        page.set_viewport_size({"width": width, "height": height}); page.wait_for_timeout(120)
        page.evaluate("() => scrollTo(0, 0)")
        page.focus("#shelf-umi-finray .lib-track > .lib-card:last-child"); page.wait_for_timeout(150)
        page.keyboard.press("Tab"); page.wait_for_timeout(150)
        rings[(width, height)] = page.evaluate("""() => { const node = document.activeElement; const r = node.getBoundingClientRect();
            return {arrow: node.classList.contains('lib-arrow'), top: Math.round(r.top - 4), bottom: Math.round(r.bottom + 4), screen: innerHeight}; }""")
    check("layout 390 and 360: an arrow of the UMI shelf, Tabbed to, shows its focus ring inside the window",
          all(ring["arrow"] and ring["top"] >= 0 and ring["bottom"] <= ring["screen"] for ring in rings.values()), rings)
    # The review of 2026-11-05: from 1280 px every shelf heading is one line (the UMI finger's, balanced, took two of
    # half the row at 1440 px), and the title's line ends on the gutter at every width from 735 px (right-aligned beside
    # the title: left-aligned, its balanced lines left a third of the hero empty from 1024 to 1280 px) with
    # "open-source" never split at its hyphen.
    headings = {}
    for width in (1440, 1280):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(120)
        headings[width] = [(name, lines) for name, _, lines, _ in page.evaluate(SPACING) if lines != 1]
    check("layout: at 1440 and 1280 px both headings one line", headings == {1440: [], 1280: []}, headings)
    # The one wording's lines (the user's decision of 2026-11-05): at no width does a heading split its range ('1 to 3 mm')
    # or a family's clause ('and tapered tips'); at 900 px each is at most two lines, its second line a phrase of its own
    # (the first ends at a comma or a full stop: text-wrap pretty, the range and the clause kept whole, so the UMI
    # heading breaks as '..., 1 to 3 mm, / and tapered tips.' there, not '..., and / tapered tips.').
    lines, split = {}, []
    for width in WIDTHS + (1280,):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(80)
        lines[width] = dict(page.evaluate(HEADING_LINES))
        for name, rows in lines[width].items():
            text = " ".join(rows)
            whole = re.findall(r"\d[\d.]* to \d[\d.]* mm|and tapered tips", text)
            if not whole and name.startswith("shelf-") or any(not any(phrase in row for row in rows) for phrase in whole):
                split.append((width, name, rows))
    check("layout: at every width from 1440 to 320 px no heading splits its range or a family's clause", not split, split[:4])
    check("layout: at 900 px both headings at most two lines, a second line a phrase of its own (the UMI's '..., 1 to 3 mm, / and tapered tips.')",
          all(len(rows) <= 2 and (len(rows) == 1 or rows[0].endswith((",", "."))) for rows in lines[900].values())
          and lines[900]["shelf-umi-finray"] == ["UMI Fin-Ray Gripper. Four pitches, 1 to 3 mm,", "and tapered tips."],
          {name: rows for name, rows in lines[900].items() if len(rows) > 1})
    heroes = {}
    for width in (1440, 1366, 1280, 1200, 1150, 1100, 1024, 900, 820, 735, 600, 410, 390, 320):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(80)
        heroes[width] = page.evaluate(HERO)
    check("layout: the title's line ends on the gutter from 735 px (each line within 1 px of the content's edge), 'open-source' and 'Gen by Surface' never split",
          all(all(abs(end) <= 1 for end in hero["ends"]) for width, hero in heroes.items() if width >= 735)
          and all(hero["split"] is False for hero in heroes.values()),
          {width: hero for width, hero in heroes.items() if hero["split"] is not False or (width >= 735 and any(abs(end) > 1 for end in hero["ends"]))})
    check("layout: the title's line two lines at 1440 px and from 1200 to 1279 px (21 px there), at most four lines from 735 px",
          heroes[1440]["lines"] == 2 and heroes[1200]["lines"] == 2 and all(hero["lines"] <= 4 for width, hero in heroes.items() if width >= 735),
          {width: hero["lines"] for width, hero in heroes.items()})
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(80)
    check("layout: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()


def part_grid(browser):
    """The grid of 2026-11-06: each gripper's card opens its 2 mm sensor's page, whose Pitch reaches its pitches; every
    sensor's page reached by clicks alone; a page's back link back to its card where the grid was; the older addresses."""
    page = new_page(browser)
    open_library(page)
    reached, opened, wrong = set(), {}, []
    for part in CARDED:
        record = ENTRIES["parts"][part]
        page.click(f"#gripper-{part}"); page.wait_for_timeout(120)
        seen = page.evaluate(VIEW)
        radios = page.evaluate("() => [...document.querySelectorAll('input[name=\"libPitch\"]')].map(input => input.value)")
        opened[part] = (seen["hash"], seen["checked"], radios)
        if (seen["hash"], seen["checked"], radios) != (f"#{record['default']}", record["default"], record["variants"]) or not seen["detail"]:
            wrong.append((part, seen, radios))
        for key in record["variants"]:
            page.click(f".lib-seg label:has(input[value='{key}'])"); page.wait_for_timeout(80)
            if page.evaluate(VIEW)["hash"] == f"#{key}":
                reached.add(key)
        page.go_back(); page.wait_for_timeout(150)
    check("grid: each gripper's card opens its 2 mm sensor's page, its Pitch the gripper's four pitches",
          not wrong and len(opened) == 7, wrong[:2] or opened)
    # The UMI shelf's cards and the Tapered tips card, its Shape and Tip width: every tip.
    for key in ENTRIES["parts"]["umi-finray"]["variants"]:
        page.click(f"#shelf-umi-finray .lib-card[data-variant='{key}']"); page.wait_for_timeout(100)
        if page.evaluate(VIEW)["hash"] == f"#{key}":
            reached.add(key)
        page.go_back(); page.wait_for_timeout(120)
    for name, family in ENTRIES["families"].items():
        page.click(f".lib-card[data-family='{name}']"); page.wait_for_timeout(120)
        shape, tip = family["axes"]
        for first in shape["choices"]:
            page.click(f"label:has(input[name='libAxis-{shape['key']}'][value='{first['value']}'])"); page.wait_for_timeout(60)
            for second in tip["choices"]:
                page.click(f"label:has(input[name='libAxis-{tip['key']}'][value='{second['value']}'])"); page.wait_for_timeout(60)
                key = family["grid"][f"{first['value']}|{second['value']}"]
                if page.evaluate(VIEW)["hash"] == f"#{key}" and not page.locator("#libDetail").is_hidden():
                    reached.add(key)
        page.go_back(); page.wait_for_timeout(120)
    check(f"grid: every sensor's page reached by clicks alone ({len(reached)} of {len(ENTRIES['variants'])}: the cards, the Pitch, Shape and Tip width)",
          reached == set(ENTRIES["variants"]), sorted(set(ENTRIES["variants"]) - reached)[:5])
    # A page's back link: the grid where it was, its card focused (opened from the grid, scrolled down).
    page.evaluate("() => scrollTo(0, 0)")
    page.click("#gripper-makermods-metal"); page.wait_for_timeout(150)
    page.go_back(); page.wait_for_timeout(150)
    page.evaluate("() => scrollTo(0, 200)"); page.wait_for_timeout(60)
    before = page.evaluate(VIEW)
    page.click("#gripper-unitree-dex1"); page.wait_for_timeout(150)
    page.click(".lib-back"); page.wait_for_timeout(150)
    back, focus = page.evaluate(VIEW), page.evaluate(FOCUS)
    check("grid: a page's back link (#gripper-<part>) puts the grid back where it was, its card focused",
          back["hash"] == "#gripper-unitree-dex1" and back["grid"] and abs(back["y"] - before["y"]) <= 1
          and focus == {"id": "gripper-unitree-dex1", "variant": "unitree-dex1-2mm", "shelf": "grippers"}, (before["y"], back, focus))
    check("grid: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()
    # The older addresses (before 2026-11-06): #shelf-<gripper> its card, the address replaced (no history entry);
    # #shelf-start the top with no hash, opened anew and typed with the grid scrolled down; the sections' own.
    page = new_page(browser, 1440, 700)
    open_library(page, "#shelf-arx-x5")
    old = page.evaluate(VIEW)
    focus, sight = page.evaluate(FOCUS), page.evaluate(IN_VIEW, "gripper-arx-x5")
    check("grid: #shelf-arx-x5 opened anew lands on its card (the address #gripper-arx-x5), in the window and focused",
          old["hash"] == "#gripper-arx-x5" and old["grid"] and focus["id"] == "gripper-arx-x5" and sight["inside"], (old, focus, sight))
    page.evaluate("() => { location.hash = '#shelf-widowx-250'; }"); page.wait_for_timeout(150)
    typed = page.evaluate(VIEW)
    focus, sight = page.evaluate(FOCUS), page.evaluate(IN_VIEW, "gripper-widowx-250")
    page.go_back(); page.wait_for_timeout(150)
    previous = page.evaluate(VIEW)
    check("grid: #shelf-widowx-250 typed lands on its card, its address replaced by #gripper-widowx-250 (one history entry: Back is the ARX X5 card's)",
          typed["hash"] == "#gripper-widowx-250" and typed["history"] == old["history"] + 1 and focus["id"] == "gripper-widowx-250" and sight["inside"]
          and previous["hash"] == "#gripper-arx-x5", (typed, focus, sight, previous["hash"]))
    open_library(page, "#shelf-start")
    fresh = page.evaluate(VIEW)
    page.evaluate("() => scrollTo(0, 400)"); page.wait_for_timeout(60)
    page.evaluate("() => { location.hash = '#shelf-start'; }"); page.wait_for_timeout(150)
    typed = page.evaluate(VIEW)
    check("grid: #shelf-start lands at the top with no hash, opened anew and typed with the grid scrolled down",
          fresh["hash"] == "" and fresh["y"] == 0 and fresh["note"] is None and typed["hash"] == "" and typed["y"] == 0 and typed["note"] is None, (fresh, typed))
    jumps = {}
    for place in ("grippers", "shelf-umi-finray"):
        open_library(page, f"#{place}")
        at, target, behavior = page.evaluate(SHELF_TOP, place)
        jumps[place] = (round(at, 1), round(target, 1), behavior, page.evaluate(VIEW)["hash"])
    check("grid: #grippers and #shelf-umi-finray opened anew show their sections (their top at the window's, or the page's end)",
          all(abs(at - target) <= 1 and behavior == "auto" and hash_ == f"#{place}" for place, (at, target, behavior, hash_) in jumps.items())
          and jumps["shelf-umi-finray"][0] > jumps["grippers"][0], jumps)
    check("grid: no console error (the older addresses)", not errors_of(page), errors_of(page)[:5])
    page.context.close()


def part_routes(browser):
    page = new_page(browser, 1440, 700)
    open_library(page, "#gripper-widowx-250")
    before = page.evaluate(VIEW)
    page.click("#gripper-widowx-250"); page.wait_for_timeout(200)
    shown = page.evaluate(VIEW)
    focus = page.evaluate(FOCUS)
    check("routes: a gripper's card opens its 2 mm sensor's page at the top, its title focused, Open in Gen by Surface at ./?part=<id>",
          shown["hash"] == "#widowx-250-2mm" and shown["detail"] and not shown["grid"] and shown["y"] == 0 and focus["id"] == "libDetailTitle"
          and shown["title"] == "WidowX 250" and shown["open"] == "./?part=widowx-250-2mm" and shown["checked"] == "widowx-250-2mm"
          and shown["history"] == before["history"] + 1 and shown["tab"] == "WidowX 250, 2 mm · Library · FlexiTac-Gen", (shown, focus))
    page.click(".lib-seg label:has(input[value='widowx-250-1mm'])"); page.wait_for_timeout(150)
    fine = page.evaluate(VIEW)
    check("routes: its Pitch's 1 mm replaces the address (no history entry) and shows that sensor, the tab named after it",
          fine["hash"] == "#widowx-250-1mm" and fine["history"] == shown["history"] and fine["checked"] == "widowx-250-1mm"
          and fine["tab"] == "WidowX 250, 1 mm · Library · FlexiTac-Gen", fine)
    facts = page.inner_text(".lib-facts")
    check("routes: the page's facts (26 rows × 27 columns · 664 taxels, 1 mm · fill 0.50, the field, the tails, reader none, the build)",
          "26 rows × 27 columns · 664 taxels" in facts and "1 mm · fill 0.50" in facts and "surface-26x27-62928ed42a39" in facts
          and "none (one tail pin per line)" in facts, facts)
    widths = page.evaluate("() => [document.querySelector('.lib-open'), ...document.querySelectorAll('.lib-pill')].map(n => n.getBoundingClientRect().width)")
    check("routes: Open in Gen by Surface, the primary action, at least as wide as each download pill (1440 px)",
          len(widths) == 3 and all(widths[0] >= width - 0.5 for width in widths[1:]), widths)
    page.screenshot(path=f"{SHOTS}/library_detail_1440.png")
    # The second review of 2026-11-05: from 900 to 1279 px a sensor's page splits evenly, so at 900 px each fact is on
    # one line and at 1100 px the two download pills are side by side (at 7 to 5 the facts wrapped and the pills stacked).
    narrow = {}
    for width in (900, 1100):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(150)
        narrow[width] = page.evaluate("""() => { const lines = node => { const range = document.createRange(); range.selectNodeContents(node);
            return new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size; };
          const columns = [...document.querySelector('.lib-detail-body').children].map(n => Math.round(n.getBoundingClientRect().width));
          return {columns, facts: [...document.querySelectorAll('.lib-facts dd')].map(lines), pills: [...document.querySelectorAll('.lib-pill')].map(n => Math.round(n.getBoundingClientRect().top))}; }""")
        page.screenshot(path=f"{SHOTS}/library_detail_{width}.png")
    # The review of 2026-11-05: below 900 px Open in Gen by Surface and the downloads come before the facts, so on a
    # 390 x 844 phone Open is in the first screen; from 900 px the facts stay before it.
    order = {}
    for width, height in ((390, 844), (899, 900), (900, 900)):
        page.set_viewport_size({"width": width, "height": height}); page.wait_for_timeout(150)
        page.evaluate("() => scrollTo(0, 0)")
        order[width] = page.evaluate("""() => { const top = selector => Math.round(document.querySelector(selector).getBoundingClientRect().top);
          return {open: top('.lib-open'), bottom: Math.round(document.querySelector('.lib-open').getBoundingClientRect().bottom), downloads: top('.lib-downloads'),
                  facts: top('.lib-facts'), pitch: top('.lib-seg'), screen: innerHeight}; }""")
        if width == 390:
            page.screenshot(path=f"{SHOTS}/library_detail_390.png")
    check("routes: below 900 px Open and the downloads come right after the pitch, before the facts (Open in a 390 x 844 phone's first screen); "
          "from 900 px the facts before Open", all(order[width]["pitch"] < order[width]["open"] < order[width]["downloads"] < order[width]["facts"] for width in (390, 899))
          and order[390]["bottom"] <= order[390]["screen"] and order[900]["facts"] < order[900]["open"], order)
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(150)
    check("routes: from 900 to 1279 px a sensor's page splits evenly: each fact on one line at 900 px, the two Gerber pills side by side at 1100 px",
          all(len(view["columns"]) == 2 and abs(view["columns"][0] - view["columns"][1]) <= 1 for view in narrow.values())
          and all(count == 1 for count in narrow[900]["facts"]) and len(narrow[1100]["pills"]) == 2 and narrow[1100]["pills"][0] == narrow[1100]["pills"][1], narrow)
    page.click(".lib-seg label:has(input[value='widowx-250-2mm'])"); page.wait_for_timeout(150)
    pitched = page.evaluate(VIEW)
    check("routes: another pitch replaces the address (no history entry) and shows that sensor, its segment focused",
          pitched["hash"] == "#widowx-250-2mm" and pitched["history"] == shown["history"] and pitched["checked"] == "widowx-250-2mm"
          and pitched["open"] == "./?part=widowx-250-2mm" and page.evaluate("() => document.activeElement.value") == "widowx-250-2mm", pitched)
    page.go_back(); page.wait_for_timeout(200)
    back = page.evaluate(VIEW)
    focus = page.evaluate(FOCUS)
    check("routes: Back returns to the grid where it was, the card that opened the page focused, the tab the Library's",
          back["grid"] and not back["detail"] and back["hash"] == "#gripper-widowx-250" and abs(back["y"] - before["y"]) <= 1
          and focus == {"id": "gripper-widowx-250", "variant": "widowx-250-2mm", "shelf": "grippers"} and back["tab"] == "Library · FlexiTac-Gen", (before["y"], back, focus))
    # An unknown id typed with the grid scrolled down: its note (above the grid) in sight.
    page.evaluate("() => scrollTo(0, 600)"); page.wait_for_timeout(60)
    down = page.evaluate(VIEW)["y"]
    page.evaluate("() => { location.hash = '#nope'; }"); page.wait_for_timeout(150)
    typed = page.evaluate(VIEW)
    top = page.evaluate("() => document.getElementById('libNote').getBoundingClientRect().top")
    check("routes: an unknown id typed with the grid scrolled down shows its note in sight (the window at the top)",
          down > 200 and typed["note"] == "No sensor in the library is named nope." and typed["y"] == 0 and 0 <= top < 700, (down, typed, top))
    page.context.close()
    # Back and Forward against the back links (the review of 2026-11-06: the back link of a page reached by Back focused
    # another card): the WidowX 250 card, its back link, the MakerMods card, Back (the grid where it was, MakerMods
    # focused), Back (the WidowX page), its back link (the WidowX card focused, in view), Back and Forward (the grid
    # where it was, WidowX focused).
    page = new_page(browser, 1440, 700)
    open_library(page)
    steps = {}
    page.click("#gripper-widowx-250"); page.wait_for_timeout(150)
    page.click(".lib-back"); page.wait_for_timeout(150)
    steps["back link"] = (page.evaluate(VIEW)["hash"], page.evaluate(FOCUS)["id"])
    page.locator("#gripper-makermods-metal").scroll_into_view_if_needed(); page.wait_for_timeout(60)
    page.evaluate("() => scrollBy(0, 40)"); page.wait_for_timeout(60)
    grid_y = page.evaluate(VIEW)["y"]
    page.click("#gripper-makermods-metal"); page.wait_for_timeout(150)
    page.go_back(); page.wait_for_timeout(150)
    steps["Back to the grid"] = (page.evaluate(VIEW)["hash"], page.evaluate(FOCUS)["id"], page.evaluate(VIEW)["y"] - grid_y)
    page.go_back(); page.wait_for_timeout(150)
    steps["Back to WidowX"] = (page.evaluate(VIEW)["hash"], page.evaluate(VIEW)["detail"])
    page.click(".lib-back"); page.wait_for_timeout(150)
    sight = page.evaluate(IN_VIEW, "gripper-widowx-250")
    steps["its back link"] = (page.evaluate(VIEW)["hash"], page.evaluate(FOCUS)["id"], sight["inside"])
    page.evaluate("() => scrollBy(0, 30)"); page.wait_for_timeout(60)
    left_y = page.evaluate(VIEW)["y"]
    page.go_back(); page.wait_for_timeout(150)
    page.go_forward(); page.wait_for_timeout(150)
    steps["Back and Forward"] = (page.evaluate(VIEW)["hash"], page.evaluate(FOCUS)["id"], page.evaluate(VIEW)["y"] - left_y)
    check("routes: Back and Forward put the grid back where it was with the card clicked focused; a back link its own card",
          steps == {"back link": ("#gripper-widowx-250", "gripper-widowx-250"), "Back to the grid": ("#gripper-widowx-250", "gripper-makermods-metal", 0),
                    "Back to WidowX": ("#widowx-250-2mm", True), "its back link": ("#gripper-widowx-250", "gripper-widowx-250", True),
                    "Back and Forward": ("#gripper-widowx-250", "gripper-widowx-250", 0)}, steps)
    # An older address typed on another gripper's page: that card, not the one that opened the page.
    page.click("#gripper-arx-x5"); page.wait_for_timeout(150)
    page.evaluate("() => { location.hash = '#shelf-widowx-250'; }"); page.wait_for_timeout(150)
    sight = page.evaluate(IN_VIEW, "gripper-widowx-250")
    check("routes: #shelf-widowx-250 typed on the ARX X5 page shows the grid, the WidowX 250 card focused and in view",
          page.evaluate(VIEW)["hash"] == "#gripper-widowx-250" and page.evaluate(FOCUS)["id"] == "gripper-widowx-250" and sight["inside"], (page.evaluate(VIEW), sight))
    check("routes: no console error (Back and Forward)", not errors_of(page), errors_of(page)[:5])
    page.context.close()
    page = new_page(browser)
    open_library(page, "#widowx-250")
    direct = page.evaluate(VIEW)
    check("routes: #widowx-250 shows its 2 mm sensor, the address kept", direct["detail"] and direct["checked"] == "widowx-250-2mm" and direct["hash"] == "#widowx-250", direct)
    page.click(".lib-back"); page.wait_for_timeout(200)
    sight = page.evaluate(IN_VIEW, "gripper-widowx-250")
    check("routes: the back link of a page opened directly goes to its card, in view and focused",
          page.evaluate(VIEW)["hash"] == "#gripper-widowx-250" and page.evaluate(FOCUS)["id"] == "gripper-widowx-250" and sight["inside"], sight)
    page.context.close()
    page = new_page(browser)
    open_library(page, "#shelf-arx-x5")
    check("routes: #shelf-arx-x5 opened anew shows its card (#gripper-arx-x5)",
          page.evaluate(VIEW)["grid"] and page.evaluate(VIEW)["hash"] == "#gripper-arx-x5" and page.evaluate(FOCUS)["id"] == "gripper-arx-x5", page.evaluate(VIEW))
    open_library(page, "#bogus")
    bogus = page.evaluate(VIEW)
    check("routes: #bogus shows the grid with a note", bogus["grid"] and not bogus["detail"] and bogus["note"] == "No sensor in the library is named bogus.", bogus)
    check("routes: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()


def part_first_screen(browser):
    """The user's decision of 2026-11-05 (the picture may be squashed): below 900 px a sensor's page is one column, its
    picture above Open, and that picture is 3:1, not 16:10, so Open is in a phone's first screen.  Every sensor's page
    and the Tapered tips page (#umi-tapers) at each phone size of PHONES, opened at the window's top, in both CASES:
    with pictures (the picture loaded, and its Exploded | Assembled control in the frame, above Open) and with none."""
    keys = list(ENTRIES["variants"]) + list(ENTRIES["families"])
    tips = {key for key, variant in ENTRIES["variants"].items() if ENTRIES["parts"][variant["part"]]["family"]} | set(ENTRIES["families"])
    grippers = [key for key in ENTRIES["variants"] if key not in tips]
    # Since the 3D view (2026-11-05): the pictures' case with every view set and with none; with views, the sample
    # pages' first screen measured again once the view is drawn over the picture (nothing may move).
    for case, view in [(case, view) for case in CASES for view in (view_cases(browser) if case == "pictures" else (False,))]:
        label, tag = (f"{case}, 3D view", f"{case}_view") if view else (case, case)
        found, errors, lives = {}, {}, {}
        for width, height in PHONES + ((899, 900), (900, 900), (1440, 900)):
            page = new_page(browser, width, height)
            library_case(page, case, view=view)
            open_library(page)
            for key in keys if width < 900 else ("widowx-250-1mm", "umi-tapers"):
                page.evaluate("(key) => { location.hash = '#' + key; }", key)
                wait_until(page, "(key) => location.hash === '#' + key && !document.getElementById('libDetail').hidden", 10, key)
                wait_until(page, PICTURE_SETTLED, 10)
                page.evaluate("() => scrollTo(0, 0)")
                found[(width, height, key)] = page.evaluate(FIRST_SCREEN)
            for key in ("trossen-widowx-ai-2mm", "umi-tapers"):
                if (width, height) in PHONES:
                    page.evaluate("(key) => { location.hash = '#' + key; }", key); page.wait_for_timeout(100)
                    wait_until(page, PICTURE_SETTLED, 10)
                    page.evaluate("() => scrollTo(0, 0)")
                    if view:
                        before = page.evaluate(FIRST_SCREEN)
                        drawn = library_shots.poll(page, LIVE_SHOWN, None, 120)
                        page.evaluate("() => scrollTo(0, 0)")
                        lives[(width, height, key)] = (drawn, before, page.evaluate(FIRST_SCREEN))
                    page.screenshot(path=f"{SHOTS}/library_first_screen_{tag}_{key}_{width}x{height}.png")
            errors[(width, height)] = errors_of(page)
            page.context.close()

        def below(size, chosen):
            return [key for key in chosen if found[size + (key,)]["open"][3] > found[size + (key,)]["screen"]]

        def lowest(size, chosen):
            return max((found[size + (key,)]["open"][3], key) for key in chosen)

        check(f"first screen ({label}) 390 x 844: Open's bottom in the window on every sensor's page ({len(ENTRIES['variants'])}) and on the Tapered tips page",
              not below((390, 844), keys), (below((390, 844), keys)[:4], lowest((390, 844), grippers), lowest((390, 844), tips)))
        check(f"first screen ({label}) 360 x 740: Open's bottom in the window on every gripper's sensor page ({len(grippers)})",
              not below((360, 740), grippers), (below((360, 740), grippers)[:4], lowest((360, 740), grippers)))
        # At 375 x 667, 320 x 640 and 320 x 568 (and a tapered tip's page at 360 x 740) Open stays below the first screen
        # on some pages, the header alone 239 px there (library.css: a two-line title's would need a picture of at most
        # 58 px at 375 px, a tapered tip's none at all): its place is reported, the lowest Open's bottom on a gripper's
        # page and on a tapered tip's, and how many pages have it in the window.
        report = {f"{width}x{height}": {"gripper": lowest((width, height), grippers), "tip": lowest((width, height), tips),
                                        "inside": f"{len(keys) - len(below((width, height), keys))}/{len(keys)}"} for width, height in PHONES}
        print(f"    first screen ({label}): {report}", flush=True)
        shapes, wrong = {}, []
        for (width, height, key), seen in found.items():
            shot_w, shot_h = seen["shot"][2] - seen["shot"][0], seen["shot"][3] - seen["shot"][1]
            aspect = 3 if width < 900 else 1.6
            shapes[(width, height)] = round(shot_w / shot_h, 3)
            drawing = seen["drawing"][1:]
            # Above Open in one column (from 900 px the facts' column is beside the picture).
            above = seen["frame"][3] <= seen["open"][1] if width < 900 else seen["frame"][2] < seen["open"][0]
            # The pictures' case: the picture itself (loaded, contained and centred) and its view control under it in
            # the frame; the placeholders': the field's drawing meeting the box, and no control.
            pictured = case == "pictures" and IMAGES[ENTRIES["families"][key]["default"] if key in ENTRIES["families"] else key] is not None
            shown = (seen["drawing"][0] == "img" and seen["loaded"] and seen["view"] is not None and seen["shot"][3] <= seen["view"][1]
                     and seen["view"][3] <= seen["frame"][3]) if pictured else (seen["drawing"][0] == "svg" and seen["meet"] is None and seen["view"] is None)
            if not (abs(shot_w - aspect * shot_h) <= 1.5 and above and seen["visible"] and shot_h > 80 and shown and seen["children"] == 1
                    and all(abs(a - b) <= 0.5 for a, b in zip(drawing, seen["shot"])) and seen["fitted"] == ["contain", "50% 50%"] and seen["overflow"] <= 0):
                wrong.append(((width, height), key, seen))
        what = ("the picture loaded, contained and centred, and its Exploded | Assembled control under it in the frame" if case == "pictures"
                else "its field drawn to meet the box (centred) and an image in it contained and centred, no view control")
        check(f"first screen ({label}): below 900 px a sensor's picture 3:1 above Open (from 900 px 16:10 beside it), shown, {what}; no sideways scroll",
              not wrong, wrong[:2] or {"aspects": shapes})
        if view:
            moved = {size: (drawn, [name for name in ("open", "frame", "shot", "drawing") if any(abs(a - b) > 0.5 for a, b in zip(
                         before[name][-4:], after[name][-4:]))], after["live"], after["shot"])
                     for size, (drawn, before, after) in lives.items()}
            check(f"first screen ({label}): at each phone the 3D view drawn over the picture (Trossen WidowX AI's 2 mm, the Tapered tips), "
                  "nothing moved (Open, the frame, the slot, the picture), the view's box the slot's",
                  len(lives) == 2 * len(PHONES) and all(drawn and not names and live is not None and all(abs(a - b) <= 0.5 for a, b in zip(live, shot))
                                                        for drawn, names, live, shot in moved.values()),
                  {size: value for size, value in moved.items() if not value[0] or value[1] or value[2] is None} or len(lives))
        check(f"first screen ({label}): no console error", not any(errors.values()), {size: found for size, found in errors.items() if found})


# Every visible picture slot: its owner (a card's variant or family, or the sensor's page), its box and
# background, its children, the placeholder's drawing (its field and its lines), and an image's attributes, computed fit,
# box within the slot and whether it has loaded (or broken: loaded with no picture).
SLOTS = """() => [...document.querySelectorAll('.lib-shot')].filter(shot => shot.checkVisibility()).map(shot => {
  const owner = shot.closest('.lib-card'); const img = shot.querySelector('img'); const r = shot.getBoundingClientRect();
  const round = v => Math.round(v * 10) / 10;
  return {owner: owner ? owner.dataset.variant || 'family:' + owner.dataset.family : 'detail',
    box: [round(r.width), round(r.height)], background: getComputedStyle(shot).backgroundColor, children: [...shot.children].map(n => n.tagName.toLowerCase()),
    field: shot.querySelector('svg .lib-field') !== null, lines: shot.querySelectorAll('svg .lib-lines line').length,
    img: img && {src: img.getAttribute('src'), alt: img.getAttribute('alt'), loading: img.getAttribute('loading'), decoding: img.getAttribute('decoding'),
      size: [img.getAttribute('width'), img.getAttribute('height')], fit: [getComputedStyle(img).objectFit, getComputedStyle(img).objectPosition],
      box: (b => [round(b.left - r.left), round(b.top - r.top), round(b.width), round(b.height)])(img.getBoundingClientRect()),
      loaded: img.complete && img.naturalWidth > 0, broken: img.complete && img.naturalWidth === 0, natural: [img.naturalWidth, img.naturalHeight]}}; })"""
# Every card's, shelf's and section's box in the document (the pictures move none of them as they arrive).
GEOMETRY = """() => [...document.querySelectorAll('.lib-card, .lib-shelf, .lib-section, .lib-footer')].map(n => { const r = n.getBoundingClientRect();
  const track = n.closest('.lib-track'); return [Math.round((r.left + (track ? track.scrollLeft : 0)) * 10) / 10, Math.round((r.top + scrollY) * 10) / 10,
    Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; })"""
# A sensor's page's picture and its view control: the picture's attributes and state, the placeholder's drawing, the boxes
# of the slot, the frame and the control's track, the control's legend, radios, colours, segments and transitions, and
# the focus, the address, the history's length and the running animations.
DETAIL_PICTURE = """() => { const frame = document.querySelector('#libDetail .lib-frame'); const shot = frame.querySelector('.lib-shot'); const img = shot.querySelector('img');
  const view = frame.querySelector('fieldset.lib-view'); const round = v => Math.round(v * 10) / 10;
  const box = n => (r => [r.left, r.top, r.right, r.bottom].map(round))(n.getBoundingClientRect());
  return {src: img ? img.getAttribute('src') : null, loading: img ? img.getAttribute('loading') : null, decoding: img ? img.getAttribute('decoding') : null,
    alt: img ? img.getAttribute('alt') : null, size: img ? [img.getAttribute('width'), img.getAttribute('height')] : null,
    loaded: img ? img.complete && img.naturalWidth > 0 : null, natural: img ? [img.naturalWidth, img.naturalHeight] : null,
    field: shot.querySelector('svg .lib-field') !== null, children: shot.children.length, shot: box(shot), frame: box(frame), background: getComputedStyle(shot).backgroundColor,
    view: view && {legend: view.querySelector('legend')?.textContent ?? null, track: box(view.querySelector('.lib-seg-track')),
      radios: [...view.querySelectorAll('input')].map(i => [i.type, i.name, i.value, i.checked, i.closest('label').textContent]),
      thumb: getComputedStyle(view.querySelector('input:checked + span')).backgroundColor, fill: getComputedStyle(view.querySelector('.lib-seg-track')).backgroundColor,
      segments: [...view.querySelectorAll('span')].map(s => round(s.getBoundingClientRect().width)),
      transitions: [...view.querySelectorAll('*')].map(n => getComputedStyle(n).transitionDuration).filter(d => d.split(', ').some(x => x !== '0s'))},
    focus: [document.activeElement.name || null, document.activeElement.value || null], hash: location.hash, history: history.length,
    animations: document.getAnimations().length, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth}; }"""
# A sensor's page's picture done: loaded, broken (a file that failed, left in place) or none (its placeholder).
DETAIL_DONE = """() => { const shot = document.querySelector('#libDetail .lib-shot'); const img = shot && shot.querySelector('img');
  return Boolean(shot) && (!img || img.complete); }"""
# The picture of a sensor's page shown and loaded from this address's end (or its placeholder, for a file that fails).
DETAIL_SHOWS = """(end) => { const img = document.querySelector('#libDetail .lib-shot img');
  return end === null ? img === null && document.querySelector('#libDetail .lib-shot svg') !== null
    : img !== null && img.getAttribute('src').endsWith(end) && img.complete && img.naturalWidth > 0; }"""


def card_owner(owner):
    """The sensor whose card picture a grid slot shows and whether it carries the entry's alt text (every card's does)."""
    if owner.startswith("family:"):
        return ENTRIES["families"][owner[len("family:"):]]["default"], True
    return owner, True


def placeholder_wrong(slot):
    """None when a slot holds its sensor's placeholder alone (the field's drawing, a line per row and column), else the slot."""
    key = card_owner(slot["owner"])[0] if slot["owner"] != "detail" else None
    variant = ENTRIES["variants"].get(key) if key else None
    lines = variant["rows"] + variant["columns"] if variant else slot["lines"]
    return None if slot["children"] == ["svg"] and slot["field"] and slot["img"] is None and slot["lines"] == lines and slot["lines"] > 0 else slot


def card_picture_wrong(slot):
    """None when a grid slot shows its sensor's Exploded card picture as the contract and library.css have it, else why not."""
    key, alt = card_owner(slot["owner"])
    image = IMAGES[key]
    if image is None:  # a sensor of this tree without a picture yet
        return placeholder_wrong(slot)
    img = slot["img"] or {}
    want = {"src": f"static/library/{image['exploded']['card']}", "alt": image["alt"] if alt else "", "loading": "lazy", "decoding": "async",
            "size": [str(CARD_SIZE[0]), str(CARD_SIZE[1])], "fit": ["contain", "50% 50%"], "loaded": True, "natural": list(CARD_SIZE)}
    got = {name: img.get(name) for name in want}
    filled = img.get("box") and all(abs(a - b) <= 0.5 for a, b in zip(img["box"], [0, 0] + slot["box"]))
    return None if got == want and slot["children"] == ["img"] and filled else (slot["owner"], {k: v for k, v in got.items() if v != want[k]}, img.get("box"), slot["box"])


def load_grid(page):
    """Every section brought into sight and each shelf's row scrolled to its end, then back: every lazy picture asked for."""
    page.evaluate("""() => { for (const shelf of document.querySelectorAll('.lib-section, .lib-shelf')) { shelf.scrollIntoView({block: 'center'});
        const track = shelf.querySelector('.lib-track'); if (track) track.scrollLeft = track.scrollWidth; } }""")
    page.wait_for_timeout(150)
    page.evaluate("""() => { for (const shelf of [...document.querySelectorAll('.lib-section, .lib-shelf')].reverse()) { shelf.scrollIntoView({block: 'center'});
        const track = shelf.querySelector('.lib-track'); if (track) track.scrollLeft = 0; } scrollTo(0, 0); }""")
    wait_until(page, "() => [...document.querySelectorAll('#libGrid .lib-shot img')].every(img => img.complete)", 30)


def part_pictures(browser):
    """The on-part figure on the Library (the user's request of 2026-11-05: the cards show the finger and the sensor on
    it), its pictures the tree's or, before any is committed, stand-ins served for the contract's "image"; since the 3D
    view (2026-11-05) with every sensor's view set (its page's picture under the view drawn over it) and with none."""
    for view in view_cases(browser):
        pictures_case(browser, view)


def pictures_case(browser, view):
    """part_pictures with every view set (``view``) or null."""
    tag, suffix = (" (3D view)", "_view") if view else ("", "")
    # The grid at 1440 px and on a 390 x 844 phone: every card's picture lazy, and the bytes asked for as the page opens
    # (all 12 at 1440 px: the page is short) within the first screen's budget; then, once every section has been in
    # sight, every card's Exploded card picture shown in its light box.
    stand = stand_ins(browser) if not PICTURED else {}

    def bytes_of(url):
        name = url.split("?")[0].rsplit("/", 1)[-1]
        return (LIBRARY / "shots" / name).stat().st_size if PICTURED else len(next(body for end, body in stand.items() if name.endswith(end)))
    opened = {}
    for width, height in ((390, 844), (1440, 900)):
        page = new_page(browser, width, height)
        library_case(page, "pictures", view=view)
        open_library(page)
        page.wait_for_timeout(600)
        asked = sorted({url.split("?")[0] for url in page.requests if "/static/library/shots/" in url})
        opened[f"{width}x{height}"] = (len(asked), sum(map(bytes_of, asked)))
        if width == 390:
            page.context.close()
    print(f"    pictures{tag}: asked for as the page opens (pictures, bytes): {opened}", flush=True)
    check(f"pictures{tag}: the pictures asked for as the page opens within the first screen's {FIRST_SCREEN_BYTES / 1e6:g} MB, at 1440 x 900 and 390 x 844",
          all(0 < count <= len(GRID_CARDS) and size <= FIRST_SCREEN_BYTES for count, size in opened.values()), opened)
    load_grid(page)
    slots = page.evaluate(SLOTS)
    wrong = [result for result in map(card_picture_wrong, slots) if result is not None]
    owners = [slot["owner"] for slot in slots]
    check(f"pictures{tag}: every card (the grippers' seven, each its 2 mm sensor's, the UMI shelf's, the Tapered tips card its default tip's: "
          f"{len(GRID_CARDS)}) shows its sensor's Exploded card picture (the contract's card file, 640 x 400), contained and centred in its light box, "
          "lazy, decoded async, its width and height set, its alt the entry's",
          not wrong and [card_owner(owner)[0] for owner in owners] == GRID_CARDS and "family:umi-tapers" in owners, wrong[:3] or owners)
    pictured = page.evaluate(GEOMETRY)
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_grid_1440_light.png")
    page.set_viewport_size({"width": 900, "height": 900}); page.wait_for_timeout(120)
    load_grid(page)
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_grid_900_light.png")
    page.context.close()
    bare = new_page(browser)
    library_case(bare, "placeholders")
    open_library(bare)
    placeholders = bare.evaluate(GEOMETRY)
    bare.context.close()
    check(f"pictures{tag}: no card, section, shelf or the footer stands elsewhere or another size with the pictures than with the placeholders (no layout shift)",
          len(pictured) == len(placeholders) and all(abs(a - b) <= 0.5 for one, other in zip(pictured, placeholders) for a, b in zip(one, other)),
          [(one, other) for one, other in zip(pictured, placeholders) if one != other][:3])
    # A sensor's page: the Exploded picture (eager) and the grey Exploded | Assembled control under it, a group named View.
    page = new_page(browser)
    library_case(page, "pictures", view=view)
    open_library(page)
    page.click("#gripper-widowx-250")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["widowx-250-2mm"]["exploded"]["src"])
    page.click(".lib-seg label:has(input[value='widowx-250-1mm'])")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["widowx-250-1mm"]["exploded"]["src"])
    seen = page.evaluate(DETAIL_PICTURE)
    image = IMAGES["widowx-250-1mm"]
    group = page.get_by_role("group", name="View")
    named = [group.count()] + ([group.get_by_role("radio", name=name).is_checked() for name in ("Exploded", "Assembled")] if group.count() == 1 else [])
    view = seen["view"] or {}
    centre = (seen["shot"][0] + seen["shot"][2]) / 2
    check(f"pictures{tag}: a sensor's page shows its Exploded picture (eager, decoded async, 1280 x 800, its alt), a group named View under it in the frame with two "
          "radios, Exploded chosen; the two segments one width, centred under the picture",
          seen["src"] == f"static/library/{image['exploded']['src']}" and seen["loading"] is None and seen["decoding"] == "async" and seen["alt"] == image["alt"]
          and seen["size"] == ["1280", "800"] and seen["loaded"] and seen["natural"] == list(SHOT_SIZE) and seen["children"] == 1
          and named == [1, True, False] and view.get("legend") == "View"
          and view.get("radios") == [["radio", "libView", "exploded", True, "Exploded"], ["radio", "libView", "assembled", False, "Assembled"]]
          and view["track"][1] >= seen["shot"][3] and view["track"][3] <= seen["frame"][3] and abs((view["track"][0] + view["track"][2]) / 2 - centre) <= 1
          and abs(view["segments"][0] - view["segments"][1]) <= 0.5, (seen, named))
    fills = page.evaluate(FILLS)
    check(f"pictures{tag}: the control is grey (its chosen view a white thumb on the fill), never blue, nothing green, no transition or animation",
          view.get("thumb") == "rgb(255, 255, 255)" and view.get("fill") == "rgba(118, 118, 128, 0.12)" and view.get("transitions") == []
          and seen["animations"] == 0 and fills["blue"] == ["a.lib-open"] and fills["green"] == [], (view, fills))
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_detail_exploded_1440.png")
    before = page.locator("#libDetail .lib-shot").screenshot()
    page.click("#libDetail .lib-view label:has(input[value='assembled'])")
    wait_until(page, DETAIL_SHOWS, 10, image["assembled"]["src"])
    swapped = page.evaluate(DETAIL_PICTURE)
    after = page.locator("#libDetail .lib-shot").screenshot()
    check(f"pictures{tag}: Assembled swaps the picture in place (another picture on the screen), the address, the history and the focus (its radio) kept",
          swapped["src"] == f"static/library/{image['assembled']['src']}" and swapped["hash"] == seen["hash"] == "#widowx-250-1mm"
          and swapped["history"] == seen["history"] and swapped["focus"] == ["libView", "assembled"] and before != after
          and [radio[3] for radio in swapped["view"]["radios"]] == [False, True] and swapped["animations"] == 0, swapped)
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_detail_assembled_1440.png")
    page.keyboard.press("ArrowLeft")
    wait_until(page, DETAIL_SHOWS, 10, image["exploded"]["src"])
    keyed = page.evaluate(DETAIL_PICTURE)
    page.keyboard.press("ArrowRight")
    wait_until(page, DETAIL_SHOWS, 10, image["assembled"]["src"])
    check(f"pictures{tag}: the arrow keys move between the views (ArrowLeft Exploded, ArrowRight Assembled again), the focus on the chosen one",
          keyed["focus"] == ["libView", "exploded"] and page.evaluate(DETAIL_PICTURE)["focus"] == ["libView", "assembled"], keyed["focus"])
    page.click(".lib-seg label:has(input[value='widowx-250-2mm'])")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["widowx-250-2mm"]["assembled"]["src"])
    pitched = page.evaluate(DETAIL_PICTURE)
    check(f"pictures{tag}: another pitch shows that sensor's picture in the view chosen (Assembled kept)",
          pitched["hash"] == "#widowx-250-2mm" and [radio[3] for radio in pitched["view"]["radios"]] == [False, True], pitched)
    page.go_back(); page.wait_for_timeout(200)
    page.click("#gripper-widowx-250")
    wait_until(page, "() => location.hash === '#widowx-250-2mm'", 10); page.wait_for_timeout(100)
    wait_until(page, DETAIL_DONE, 10)
    opened = page.evaluate(DETAIL_PICTURE)
    check(f"pictures{tag}: each sensor's page opened shows the Exploded picture first (the WidowX 250 card again, after Assembled)",
          opened["src"] == f"static/library/{IMAGES['widowx-250-2mm']['exploded']['src']}" and [radio[3] for radio in (opened["view"] or {}).get("radios", [])] == [True, False],
          (opened["src"], opened["view"]))
    # The Tapered tips page: Shape and Tip width swap the picture with the sensor, the view kept.
    open_library(page, "#umi-tapers")
    tapers = ENTRIES["families"]["umi-tapers"]
    wait_until(page, DETAIL_SHOWS, 10, IMAGES[tapers["default"]]["exploded"]["src"])
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_tapers_1440.png")
    page.click("label:has(input[name='libAxis-shape'][value='convex'])")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["umi-convex-tip13.8-2mm"]["exploded"]["src"])
    page.click("#libDetail .lib-view label:has(input[value='assembled'])")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["umi-convex-tip13.8-2mm"]["assembled"]["src"])
    page.click("label:has(input[name='libAxis-tip_mm'][value='5.8'])")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["umi-convex-tip5.8-2mm"]["assembled"]["src"])
    check(f"pictures{tag}: on the Tapered tips page Shape and Tip width show the chosen tip's picture (the convex 13.8 mm, then 5.8 mm Assembled)",
          page.evaluate(DETAIL_PICTURE)["hash"] == "#umi-convex-tip5.8-2mm", page.evaluate(DETAIL_PICTURE)["src"])
    check(f"pictures{tag}: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()
    # Phones and every width: the page never scrolls sideways; the picture 3:1 at 390 x 844 (part_first_screen checks Open).
    overflow = {}
    page = new_page(browser, 390, 844)
    library_case(page, "pictures", view=view)
    for fragment, name in (("#widowx-250-1mm", "detail"), ("#umi-tapers", "tapers")):
        open_library(page, fragment)
        wait_until(page, PICTURE_SETTLED, 10)
        page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_{name}_exploded_390x844.png")
        if name == "detail":
            page.click("#libDetail .lib-view label:has(input[value='assembled'])")
            wait_until(page, DETAIL_SHOWS, 10, IMAGES["widowx-250-1mm"]["assembled"]["src"])
            page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_detail_assembled_390x844.png")
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(80)
        for fragment in ("", "#umi-tapers"):
            page.evaluate("(fragment) => { location.hash = fragment; }", fragment); page.wait_for_timeout(80)
            overflow[(width, fragment or "grid")] = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check(f"pictures{tag}: no sideways scroll from 1440 to 320 px (the grid and the Tapered tips page)", all(value <= 0 for value in overflow.values()),
          {key: value for key, value in overflow.items() if value > 0})
    page.context.close()
    # The dark scheme: the pictures' boxes light (#f5f5f7) on the grid and a sensor's page, the control's thumb grey.
    page = new_page(browser, scheme="dark")
    library_case(page, "pictures", view=view)
    open_library(page)
    load_grid(page)
    grounds = {slot["background"] for slot in page.evaluate(SLOTS)}
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_grid_1440_dark.png")
    page.set_viewport_size({"width": 900, "height": 900}); page.wait_for_timeout(120)
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_grid_900_dark.png")
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(120)
    open_library(page, "#widowx-250-1mm")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["widowx-250-1mm"]["exploded"]["src"])
    dark = page.evaluate(DETAIL_PICTURE)
    fills = page.evaluate(FILLS)
    check(f"pictures{tag} (dark): every picture's box stays light (#f5f5f7), the control's thumb grey, the blue only on Open",
          grounds == {"rgb(245, 245, 247)"} and dark["background"] == "rgb(245, 245, 247)" and dark["view"]["thumb"] == "rgb(99, 99, 102)"
          and fills["blue"] == ["a.lib-open"] and fills["green"] == [], (grounds, dark["background"], dark["view"]["thumb"], fills))
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_detail_dark.png")
    page.context.close()
    # A picture that does not load: its placeholder in its place (never a broken image or an empty box); on a sensor's
    # page the control kept while a view is left, gone once both failed.
    card, one, both = "widowx-250-2mm", "arx-x5-2mm", "franka-hand-1mm"
    missing = {f"{card}.exploded.card.webp", f"{one}.exploded.webp", f"{both}.exploded.webp", f"{both}.assembled.webp"}
    page = new_page(browser)
    library_case(page, "pictures", missing, view=view)
    open_library(page)
    load_grid(page)
    slots = page.evaluate(SLOTS)
    failed = [slot for slot in slots if slot["owner"] == card]
    check(f"pictures{tag}: a card picture that does not load ({card}'s) gives way to the placeholder, the field's drawing alone; no slot holds a broken image",
          failed and all(placeholder_wrong(slot) is None for slot in failed) and not [slot for slot in slots if (slot["img"] or {}).get("broken")]
          and not [result for result in map(card_picture_wrong, (slot for slot in slots if slot["owner"] != card)) if result is not None], failed[:1])
    open_library(page, f"#{one}")
    wait_until(page, DETAIL_DONE, 10); page.wait_for_timeout(100)
    exploded = page.evaluate(DETAIL_PICTURE)
    assembled = None
    if exploded["view"] is not None:
        page.click("#libDetail .lib-view label:has(input[value='assembled'])")
        page.wait_for_timeout(300); wait_until(page, DETAIL_DONE, 10)
        assembled = page.evaluate(DETAIL_PICTURE)
    check(f"pictures{tag}: a sensor's Exploded picture that does not load ({one}) gives way to the placeholder, the control kept, its Assembled picture shown",
          exploded["field"] and exploded["children"] == 1 and exploded["view"] is not None and assembled is not None
          and assembled["src"] == f"static/library/{IMAGES[one]['assembled']['src']}" and assembled["loaded"], (exploded, assembled))
    open_library(page, f"#{both}")
    wait_until(page, DETAIL_DONE, 10); page.wait_for_timeout(100)
    if page.query_selector("#libDetail .lib-view"):
        page.click("#libDetail .lib-view label:has(input[value='assembled'])")
        page.wait_for_timeout(300); wait_until(page, DETAIL_DONE, 10)
    gone = page.evaluate(DETAIL_PICTURE)
    check(f"pictures{tag}: when both views fail ({both}) the placeholder stays and the control goes", gone["field"] and gone["children"] == 1 and gone["view"] is None, gone)
    ends = [f"/static/library/shots/{name}" for name in missing]
    check(f"pictures{tag}: no console error but the missing pictures' 404s", not errors_of(page, ends), errors_of(page, ends)[:5])
    page.context.close()


def part_placeholders(browser):
    """No picture (every "image" null, as before the shots tool's run): every slot the drawing of its field, no image,
    no view control and no request for a picture, as the page was before the pictures."""
    page = new_page(browser)
    library_case(page, "placeholders")
    open_library(page)
    load_grid(page)
    slots = page.evaluate(SLOTS)
    wrong = [slot for slot in slots if placeholder_wrong(slot) is not None]
    check("placeholders: without pictures every card's slot is the drawing of its sensor's field (a line per row and column), no image",
          not wrong and len(slots) == len(GRID_CARDS), wrong[:2] or len(slots))
    page.screenshot(path=f"{SHOTS}/library_placeholders_grid_1440_light.png")
    page.set_viewport_size({"width": 900, "height": 900}); page.wait_for_timeout(120)
    page.screenshot(path=f"{SHOTS}/library_placeholders_grid_900_light.png")
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(120)
    pages = {}
    for fragment in ("#widowx-250-1mm", "#umi-tapers"):
        open_library(page, fragment)
        pages[fragment] = page.evaluate(DETAIL_PICTURE)
        page.screenshot(path=f"{SHOTS}/library_placeholders_{'tapers' if fragment == '#umi-tapers' else 'detail'}_1440.png")
    check("placeholders: a sensor's page and the Tapered tips page show the field's drawing in the frame, no view control (the frame its slot and its padding)",
          all(seen["field"] and seen["children"] == 1 and seen["view"] is None and abs((seen["frame"][3] - seen["frame"][1]) - (seen["shot"][3] - seen["shot"][1]) - 12) <= 0.5
              for seen in pages.values()), pages)
    asked = [url for url in page.requests if "/static/library/shots/" in url]
    check("placeholders: no picture asked for, no console error", not asked and not errors_of(page), (asked[:3], errors_of(page)[:3]))
    page.context.close()
    page = new_page(browser, scheme="dark")
    library_case(page, "placeholders")
    open_library(page)
    page.screenshot(path=f"{SHOTS}/library_placeholders_grid_1440_dark.png")
    page.set_viewport_size({"width": 900, "height": 900}); page.wait_for_timeout(120)
    page.screenshot(path=f"{SHOTS}/library_placeholders_grid_900_dark.png")
    page.context.close()
    page = new_page(browser, 390, 844)
    library_case(page, "placeholders")
    for fragment, name in (("#widowx-250-1mm", "detail"), ("#umi-tapers", "tapers")):
        open_library(page, fragment)
        page.screenshot(path=f"{SHOTS}/library_placeholders_{name}_390x844.png")
    page.context.close()


# A family sensor's page: the address, the checked choice of each axis, the title, Open, the back link, the pitch control.
FAMILY_VIEW = """() => ({hash: location.hash, detail: !document.getElementById('libDetail').hidden, grid: !document.getElementById('libGrid').hidden,
  y: Math.round(scrollY), history: history.length, title: document.getElementById('libDetailTitle')?.textContent.replace(/\u2011/g, '-') || null,
  shape: document.querySelector('input[name="libAxis-shape"]:checked')?.value || null, tip: document.querySelector('input[name="libAxis-tip_mm"]:checked')?.value || null,
  legends: [...document.querySelectorAll('#libDetail .lib-seg legend')].map(l => l.textContent), pitch: document.querySelector('input[name="libPitch"]') !== null,
  open: document.querySelector('.lib-open')?.getAttribute('href') || null, back: [document.querySelector('.lib-back')?.getAttribute('href'), document.querySelector('.lib-back')?.textContent],
  focus: [document.activeElement.id, document.activeElement.name || null, document.activeElement.value || null, document.activeElement.dataset?.family || null,
          document.activeElement.closest('.lib-shelf')?.id || null],
  note: document.getElementById('libNote').hidden ? null : document.getElementById('libNote').textContent})"""


def part_family(browser):
    family = ENTRIES["families"]["umi-tapers"]
    members = [part for part, record in ENTRIES["parts"].items() if record["family"] == "umi-tapers"]
    page = new_page(browser)
    open_library(page, "#shelf-umi-finray")
    cards = page.evaluate("""() => [...document.querySelectorAll('#shelf-umi-finray .lib-card')].map(card => [card.dataset.variant || card.dataset.family,
        card.getAttribute('href'), [...card.querySelectorAll('.lib-card-name, .lib-card-line')].map(n => n.textContent)])""")
    everywhere = page.evaluate("() => [...document.querySelectorAll('.lib-card')].map(n => n.dataset.variant || n.dataset.family || n.getAttribute('href'))")
    check("family: its card ends the UMI shelf ('Tapered tips', 'Trapezoid or convex arc', '5 tip widths · 2 mm pitch', #umi-tapers)",
          cards[-1] == ["umi-tapers", "#umi-tapers", ["Tapered tips", "Trapezoid or convex arc", "5 tip widths · 2 mm pitch"]]
          and [card[0] for card in cards[:-1]] == ENTRIES["parts"]["umi-finray"]["variants"], cards)
    check("family: no tip has a shelf or a card of its own (the family's card is its one)",
          not [item for item in everywhere if any(member in str(item) for member in members)]
          and not page.query_selector_all(", ".join(f"[id='shelf-{member}']" for member in members)), everywhere)
    page.locator("#shelf-umi-finray .lib-track").evaluate("track => track.scrollLeft = track.scrollWidth")
    page.wait_for_timeout(60)
    page.locator("#shelf-umi-finray").screenshot(path=f"{SHOTS}/library_family_card.png")
    before = page.evaluate(FAMILY_VIEW)
    page.click(".lib-card[data-family='umi-tapers']"); page.wait_for_timeout(200)
    shown = page.evaluate(FAMILY_VIEW)
    facts = page.inner_text(".lib-facts")
    default = ENTRIES["variants"][family["default"]]
    check("family: its card opens #umi-tapers, the 13.8 mm trapezoid's page at the top, its title focused, Shape and Tip width in place of the pitch",
          shown["hash"] == "#umi-tapers" and shown["detail"] and shown["y"] == 0 and shown["focus"][0] == "libDetailTitle"
          and shown["title"] == "UMI Fin-Ray Gripper, tapered tip" and (shown["shape"], shown["tip"]) == ("trap", "13.8")
          and shown["legends"] == ["Shape", "Tip width (mm)"] and not shown["pitch"] and shown["open"] == "./?part=umi-trap-tip13.8-2mm"
          and shown["history"] == before["history"] + 1 and shown["back"] == ["#shelf-umi-finray", "UMI Fin-Ray Gripper"], shown)
    check("family: its facts (the tip, 32 rows × 11 columns · 276 taxels, 2 mm · fill 0.50, the build)",
          "Trapezoid, 13.8 mm at the tip, over the last 75 mm" in facts and f"{default['rows']} rows × {default['columns']} columns · {default['taxels']} taxels" in facts
          and "2 mm · fill 0.50" in facts and default["build_id"] in facts, facts)
    page.screenshot(path=f"{SHOTS}/library_family_detail.png", full_page=True)
    page.click("label:has(input[name='libAxis-shape'][value='convex'])"); page.wait_for_timeout(150)
    convex = page.evaluate(FAMILY_VIEW)
    # The review of 2026-11-05: the line under the title ('Soft fin-ray finger, convex arc tip · UMI ...') never starts a
    # line with its separator (a no-break space joins it to the word before it).
    starts = {}
    for width in (1440, 1100, 900, 390, 320):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(100)
        starts[width] = page.evaluate("""() => { const text = document.querySelector('.lib-detail-line').firstChild; const lines = [];
          for (let i = 0, top = null; i < text.data.length; i += 1) { const range = document.createRange(); range.setStart(text, i); range.setEnd(text, i + 1);
            const box = [...range.getClientRects()].find(r => r.width > 0); if (!box) continue;
            if (Math.round(box.top) !== top) { lines.push(''); top = Math.round(box.top); } lines[lines.length - 1] += text.data[i]; }
          return lines.map(line => line.trim()); }""")
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(100)
    check("family: the convex arc tip's line under the title never starts a line with its '·'",
          all(not line.startswith("\u00b7") for lines in starts.values() for line in lines) and any(len(lines) > 1 for lines in starts.values()), starts)
    page.click("label:has(input[name='libAxis-tip_mm'][value='5.8'])"); page.wait_for_timeout(150)
    narrow = page.evaluate(FAMILY_VIEW)
    check("family: Shape and Tip width replace the address (no history entry) with the grid's sensor, the changed control focused",
          (convex["hash"], convex["shape"], convex["tip"], convex["open"], convex["focus"][1:3]) == ("#umi-convex-tip13.8-2mm", "convex", "13.8", "./?part=umi-convex-tip13.8-2mm", ["libAxis-shape", "convex"])
          and (narrow["hash"], narrow["shape"], narrow["tip"], narrow["open"], narrow["focus"][1:3]) == ("#umi-convex-tip5.8-2mm", "convex", "5.8", "./?part=umi-convex-tip5.8-2mm", ["libAxis-tip_mm", "5.8"])
          and convex["history"] == narrow["history"] == shown["history"] and "Convex arc, 5.8 mm at the tip" in page.inner_text(".lib-facts"), (convex, narrow))
    fills = page.evaluate(FILLS)
    check("family: the action blue fills only Open in Gen by Surface on its page (the controls' thumbs are grey), nothing green",
          fills["blue"] == ["a.lib-open"] and fills["green"] == [], fills)
    page.go_back(); page.wait_for_timeout(200)
    back = page.evaluate(FAMILY_VIEW)
    check("family: Back returns to the grid where it was, the family card focused",
          back["grid"] and not back["detail"] and abs(back["y"] - before["y"]) <= 1 and back["focus"][3:] == ["umi-tapers", "shelf-umi-finray"], (before["y"], back))
    page.context.close()
    page = new_page(browser)
    open_library(page, "#umi-convex-tip9.8-2mm")
    direct = page.evaluate(FAMILY_VIEW)
    check("family: a tip's id opens its page (Convex arc, 9.8 mm)", direct["detail"] and (direct["shape"], direct["tip"]) == ("convex", "9.8"), direct)
    page.click(".lib-back"); page.wait_for_timeout(200)
    at, target, _ = page.evaluate(SHELF_TOP, "shelf-umi-finray")
    check("family: the back link of a tip's page goes to the UMI shelf", page.evaluate(FAMILY_VIEW)["hash"] == "#shelf-umi-finray" and abs(at - target) <= 1, (at, target))
    open_library(page, "#umi-trap-tip5.8")
    part = page.evaluate(FAMILY_VIEW)
    check("family: a tip's part id opens its one sensor, the address kept", part["detail"] and (part["shape"], part["tip"], part["hash"]) == ("trap", "5.8", "#umi-trap-tip5.8"), part)
    open_library(page, "#shelf-umi-trap-tip5.8")
    shelfless = page.evaluate(FAMILY_VIEW)
    check("family: a tip has no shelf (#shelf-umi-trap-tip5.8 is the grid with a note)",
          shelfless["grid"] and shelfless["note"] == "No sensor in the library is named shelf-umi-trap-tip5.8.", shelfless)
    check("family: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()


def server_export(kind, design):
    request = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/export/{kind}", data=json.dumps(design).encode("utf-8"),
                                     method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as reply:
        return reply.read(), re.search(r'filename="([^"]+)"', reply.headers["Content-Disposition"]).group(1)


def part_downloads(browser):
    page = new_page(browser)
    downloads = Path(SCRATCH) / "downloads"
    site = SITE["root"] is not None
    if site:
        files = json.loads((SITE["root"] / "static" / "library" / "files.json").read_text(encoding="utf-8"))
        check("downloads (site): files.json lists every sensor with its build id", sorted(files["variants"]) == sorted(ENTRIES["variants"])
              and all(files["variants"][key]["build_id"] == value["build_id"] for key, value in ENTRIES["variants"].items()), sorted(files["variants"])[:5])
    for identifier in ("widowx-250-1mm", "umi-finray-2mm", "umi-convex-tip5.8-2mm"):
        open_library(page, f"#{identifier}")
        wait_until(page, "() => document.querySelectorAll('.lib-pill[data-export]:not(:disabled)').length === 2", 30)
        variant = ENTRIES["variants"][identifier]
        design = json.loads((LIBRARY / variant["fit"]).read_text(encoding="utf-8"))["reply"]["proposals"][0]["design"]
        for kind in ("top-gerber", "bottom-gerber"):
            with page.expect_download(timeout=120000) as info:
                page.click(f".lib-pill[data-export='{kind}']")
            download = info.value
            path = downloads / f"library-{download.suggested_filename}"
            download.save_as(path)
            expected, name = server_export(kind, design)
            check(f"downloads: {identifier}'s {kind} is app.py's export of its design, under its name{' (prebuilt)' if site else ''}",
                  path.read_bytes() == expected and download.suggested_filename == name, (download.suggested_filename, name))
    part = ENTRIES["parts"]["widowx-250"]
    open_library(page, "#widowx-250-1mm")
    with page.expect_download(timeout=60000) as info:
        page.click(".lib-links a[download]")
    download = info.value
    path = downloads / f"library-{download.suggested_filename}"
    download.save_as(path)
    check("downloads: the part's STL is its mesh (widowx-250.stl, 22 kB)", path.read_bytes() == (LIBRARY / part["mesh"]["file"]).read_bytes()
          and download.suggested_filename == "widowx-250.stl" and "Part STL (22 kB)" in page.inner_text(".lib-links"), download.suggested_filename)
    licence = page.get_attribute(".lib-links a[target='_blank']", "href")
    reply = page.request.get(SITE["base"] + licence)
    check("downloads: the licence text is served (BSD-3-Clause)", reply.status == 200 and reply.body() == (LIBRARY / part["license"]["text"]).read_bytes()
          and "Licence (BSD-3-Clause)" in page.inner_text(".lib-links"), (licence, reply.status))
    check("downloads: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()


def part_isolation(browser):
    """Only the site's own requests, nothing for the engine; three.js and the web/cad modules only on a sensor's page
    with its 3D view (the grid never; with every view null, never), in light and dark."""
    for scheme in ("light", "dark"):
        for view in view_cases(browser):
            tag = f"{scheme}{', 3D view' if view else ''}"
            page = new_page(browser, scheme=scheme)
            library_case(page, "pictures", view=view)
            open_library(page)
            grid = page.evaluate(FILLS)
            before = page.evaluate(SNAPSHOT)
            height = page.evaluate("() => document.documentElement.scrollHeight")
            for y in range(0, height, 400):
                page.evaluate(f"() => scrollTo(0, {y})"); page.wait_for_timeout(15)
            page.evaluate("() => scrollTo(0, 0)"); page.wait_for_timeout(60)
            after = page.evaluate(SNAPSHOT)
            check(f"isolation {tag}: scrolling the page changes nothing (no class, opacity, transform or animation)",
                  before == after and after["animations"] == 0, (len(before["nodes"]), len(after["nodes"]), after["animations"]))
            page.screenshot(path=f"{SHOTS}/library_grid_{scheme}{'_view' if view else ''}.png")
            grid_requests = list(page.requests)
            open_library(page, "#trossen-widowx-ai-1mm")
            drawn = library_shots.poll(page, LIVE_SHOWN, None, 120) if view else None
            detail = page.evaluate(FILLS)
            check(f"isolation {tag}: the action blue fills only Open in Gen by Surface, nothing green (the grid and a sensor's page"
                  f"{', its 3D view drawn' if view else ''})",
                  grid["blue"] == [] and detail["blue"] == ["a.lib-open"] and grid["green"] == detail["green"] == [] and (drawn or not view), (grid, detail, drawn))
            page.screenshot(path=f"{SHOTS}/library_detail_{scheme}{'_view' if view else ''}.png")
            words = page.evaluate(WORDS)
            open_library(page)
            words += page.evaluate(WORDS)
            check(f"isolation {tag}: the page never says CAD and is English (its text, titles and labels)",
                  not [text for text in words if re.search(r"\bCAD\b", text)] and not [text for text in words if re.search(r"[Ѐ-ӿ　-鿿가-힯]", text)],
                  [text[:80] for text in words if re.search(r"\bCAD\b", text)])
            base = SITE["base"]
            foreign = [url for url in page.requests if not url.startswith(base)]
            engine = [url for url in page.requests if re.search(r"/py/|worker|backend\.js|app\.js", url)]
            # The 3D view's modules (the user's request of 2026-11-05): three.js and web/cad on a sensor's page with a view only.
            three_d = [url for url in page.requests if re.search(r"three|/cad/", url)]
            outside = [url for url in three_d if not url.startswith((base + "static/vendor/three/", base + "static/cad/"))]
            on_grid = [url for url in grid_requests if re.search(r"three|/cad/", url)]
            check(f"isolation {tag}: only the site's own requests, none for the engine (py/, a worker, backend.js, app.js); three.js and the "
                  f"web/cad modules {'on the sensor page with its 3D view only (never the grid)' if view else 'never (no view)'}",
                  not foreign and not engine and not on_grid and not outside and bool(three_d) == view,
                  (foreign[:4], engine[:4], on_grid[:3], outside[:3], len(three_d)))
            check(f"isolation {tag}: no console error", not errors_of(page), errors_of(page)[:5])
            page.context.close()


def part_errors(browser):
    page = new_page(browser)
    page.route("**/static/library/entries.json", lambda route: route.fulfill(status=404, content_type="text/plain", body="not here"))
    page.goto(SITE["base"] + "library.html")
    wait_until(page, READY, 30)
    status = page.evaluate("() => [document.getElementById('libStatus').textContent, document.getElementById('libStatus').getAttribute('role'), document.getElementById('libGrid').hidden]")
    check("errors: without entries.json the page says so (role alert), the grid hidden",
          status == ["The library could not be loaded (HTTP 404). Gen by Surface and Rectangular still work.", "alert", True], status)
    links = page.evaluate("() => [...document.querySelectorAll('.mode-links a, .masthead-library')].map(a => a.getAttribute('href'))")
    check("errors: the header's links still work", links == ["./#rect", "./", "library.html"], links)
    check("errors: no console error but entries.json's 404", not errors_of(page, ["/static/library/entries.json"]), errors_of(page, ["/static/library/entries.json"])[:5])
    page.context.close()
    if SITE["root"] is None:
        return
    page = new_page(browser)
    page.route("**/static/library/files.json", lambda route: route.fulfill(status=404, content_type="text/plain", body="not here"))
    open_library(page, "#widowx-250-1mm")
    wait_until(page, "() => document.querySelector('.lib-downloads .lib-download-note') !== null", 30)
    note = page.inner_text(".lib-downloads")
    check("errors (site): without files.json the downloads give way to the note",
          note == "The prebuilt Gerbers were not found; open the sensor in Gen by Surface to download them." and not page.query_selector(".lib-pill"), note)
    check("errors (site): no console error but files.json's 404", not errors_of(page, ["/static/library/files.json"]), errors_of(page, ["/static/library/files.json"])[:5])
    page.context.close()


# -- a sensor's page in 3D (part_view) ------------------------------------------------------------------------------
# The user's request of 2026-11-05, "lib 点进去具体的每个夹爪的时候, 那个图也做成可以三维旋转的": each sensor's page turns in
# 3D (web/cad/library_view.js over the picture's slot; docs/LIBRARY_VIEW.md).  Its sensors here: a gripper of a scene
# (Trossen WidowX AI: a mirror pair, its other finger see-through in both views, its stack assembled, its own 3.77 MB
# part) and the UMI finger (its fingertip, no stage).
VIEW_GRIPPER = "trossen-widowx-ai-2mm"
VIEW_UMI = "umi-finray-2mm"
SETTLED_STATES = ("drawn", "failed", "unavailable", "off", "lost")
# The page's frames and WebGL draws counted (nothing may render at rest: no animation loop, no idle redraw).
COUNTERS = """(() => { const counts = {frames: 0, draws: 0};
  Object.defineProperty(window, '__libCounts', {value: counts});
  const frame = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = callback => { counts.frames += 1; return frame(callback); };
  for (const kind of ['WebGLRenderingContext', 'WebGL2RenderingContext']) {
    const proto = window[kind] && window[kind].prototype; if (!proto) continue;
    for (const name of ['drawElements', 'drawArrays', 'drawElementsInstanced', 'drawArraysInstanced', 'drawRangeElements']) {
      const original = proto[name]; if (typeof original !== 'function') continue;
      proto[name] = function (...args) { counts.draws += 1; return original.apply(this, args); }; } } })();"""
FRAME_COUNTS = "() => ({...window.__libCounts})"
# A browser without WebGL (the 2D canvas kept), without DecompressionStream, and one asking to save data.
NO_WEBGL = """(() => { const original = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (kind, ...rest) { return /webgl/i.test(String(kind)) ? null : original.call(this, kind, ...rest); }; })();"""
NO_DECOMPRESSION = "(() => { delete window.DecompressionStream; })();"
SAVE_DATA = "(() => { Object.defineProperty(Navigator.prototype, 'connection', {configurable: true, get: () => ({saveData: true, effectiveType: '4g'})}); })();"
LIB_STATE = "() => { const node = document.getElementById('libViewState'); return node && node.textContent ? JSON.parse(node.textContent) : null; }"
# The view of ``build`` settled (one of SETTLED_STATES), or not yet.
VIEW_SETTLED = """(build) => { const node = document.getElementById('libViewState'); if (!node || !node.textContent) return null;
  const s = JSON.parse(node.textContent); return s.build_id === build && ['drawn', 'failed', 'unavailable', 'off', 'lost'].includes(s.state) ? s.state : null; }"""
# What a sensor's page shows as it loads: the probe state, the picture (eager, loaded, shown), the view (its canvas shown),
# the boxes of the slot, Open, the view's host and its canvas.
LOAD_SAMPLE = """() => { const shot = document.querySelector('#libDetail .lib-shot-detail'); const img = shot ? shot.querySelector('img') : null;
  const host = document.querySelector('#libDetail .lib-live'); const canvas = host ? host.querySelector('canvas') : null;
  const open = document.querySelector('#libDetail .lib-open'); const node = document.getElementById('libViewState');
  const s = node && node.textContent ? JSON.parse(node.textContent) : {};
  const box = n => n ? (r => [r.left, r.top + scrollY, r.width, r.height].map(v => Math.round(v * 10) / 10))(n.getBoundingClientRect()) : null;
  const seen = n => Boolean(n) && n.checkVisibility({visibilityProperty: true, opacityProperty: true});
  return {state: s.state || null, build: s.build_id || null, img: Boolean(img), loading: img ? img.getAttribute('loading') : null,
    loaded: Boolean(img) && img.complete && img.naturalWidth > 0, picture: seen(img), live: seen(host) && seen(canvas),
    shot: box(shot), open: box(open), host: box(host), canvas: box(canvas)}; }"""
CANVAS_BOX = "() => { const r = document.querySelector('#libDetail .lib-live canvas').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }"
ARIA = """() => { const host = document.querySelector('#libDetail .lib-live'); const img = document.querySelector('#libDetail .lib-shot-detail img');
  const hint = document.getElementById(host.getAttribute('aria-describedby') || ''); const canvas = host.querySelector('canvas');
  return {role: host.getAttribute('role'), label: host.getAttribute('aria-label'), alt: img ? img.getAttribute('alt') : null, tab: host.tabIndex,
          hint: hint ? hint.textContent : null, inside: Boolean(hint) && host.contains(hint), canvas: canvas ? canvas.getAttribute('aria-hidden') : null,
          touch: canvas ? getComputedStyle(canvas).touchAction : null, cursor: canvas ? getComputedStyle(canvas).cursor : null}; }"""
RING = """() => { const host = document.querySelector('#libDetail .lib-live'); const style = getComputedStyle(host);
  return {focused: document.activeElement === host, visible: host.matches(':focus-visible'), style: style.outlineStyle,
          width: parseFloat(style.outlineWidth), colour: style.outlineColor}; }"""
GROUNDS = """() => ({slot: getComputedStyle(document.querySelector('#libDetail .lib-shot-detail')).backgroundColor,
  host: getComputedStyle(document.querySelector('#libDetail .lib-live')).backgroundColor})"""
SHOTS_MANIFEST = (json.loads((LIBRARY / library_write.SHOTS_MANIFEST).read_text(encoding="utf-8")).get("shots", {})
                  if (LIBRARY / library_write.SHOTS_MANIFEST).is_file() else {})


def view_page(browser, width=1440, height=900, scheme="light", scripts=(), mobile=False):
    """A page as new_page's, its frames and draws counted (COUNTERS), ``scripts`` run first; ``mobile``: a phone's
    (touch, DPR 3), else DPR 2."""
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme="light", device_scale_factor=3 if mobile else 2,
                                  is_mobile=mobile, has_touch=mobile)
    for script in (COUNTERS,) + ((DARK_CHOICE,) if scheme == "dark" else ()) + tuple(scripts):
        context.add_init_script(script)
    page = context.new_page()
    page.logs, page.requests = [], []
    page.on("console", lambda m: page.logs.append((m.type, m.text, (m.location or {}).get("url", ""))))
    page.on("pageerror", lambda e: page.logs.append(("pageerror", str(e), "")))
    page.on("request", lambda r: page.requests.append(r.url))
    return page


def view_settled(page, key, timeout=150):
    """The probe state of ``key``'s view once settled (SETTLED_STATES), or None."""
    if not library_shots.poll(page, VIEW_SETTLED, ENTRIES["variants"][key]["build_id"], timeout):
        return None
    return page.evaluate(LIB_STATE)


def open_view(page, key, settle=True):
    """``key``'s page opened with ?probe (the view's state read; the visitor's view otherwise), its view settled."""
    page.goto(SITE["base"] + f"library.html?probe#{key}")
    wait_until(page, READY, 30)
    return view_settled(page, key) if settle else None


def load_samples(page, key):
    """``key``'s page opened with ?probe, what it shows sampled every few ms until its view settles."""
    page.goto(SITE["base"] + f"library.html?probe#{key}")
    samples, end, build = [], time.monotonic() + 150, ENTRIES["variants"][key]["build_id"]
    while time.monotonic() < end:
        sample = page.evaluate(LOAD_SAMPLE)
        samples.append(sample)
        if sample["build"] == build and sample["state"] in SETTLED_STATES:
            break
        page.wait_for_timeout(25)
    return samples


def comparable(key):
    """Whether ``key``'s picture is its 3D view's drawing (shot from it: its record has art; or a part with no scene,
    which the view draws as Gen by Surface's figure did)."""
    return PICTURED and (bool(SHOTS_MANIFEST.get(key, {}).get("art")) or ENTRIES["variants"][key]["part"] not in SCENES)


def home_reads(page):
    """{mode: the view's canvas as a PNG at its home} with its host at the pictures' pane (library_shots.PANE: 640 x 400
    CSS px, a 1280 x 800 buffer) on a visitor's page (the view's own move to the middle), the host put back after."""
    style = page.evaluate("() => document.querySelector('#libDetail .lib-live').getAttribute('style')")
    size = page.evaluate(library_shots.PANE, list(library_shots.PANE_CSS))
    reads = {}
    if size == list(library_shots.PANE_CSS) and library_shots.poll(page, library_shots.BUFFER, list(library_write.SHOT_SIZE), 30):
        page.evaluate(library_shots.TWO_FRAMES)
        for mode in library_shots.MODES:
            read = page.evaluate(library_shots.SHOT, mode)
            if "url" in read and read["buffer"] == list(library_write.SHOT_SIZE):
                reads[mode] = {"png": base64.b64decode(read["url"].split(",", 1)[1]), "state": json.loads(read["state"])}
    page.evaluate("(style) => { const host = document.querySelector('#libDetail .lib-live'); if (style === null) host.removeAttribute('style'); "
                  "else host.setAttribute('style', style); }", style)
    page.click("#libDetail .lib-view label:has(input[value='exploded'])")
    page.wait_for_timeout(100)
    return reads


def likeness(live, picture):
    """{margins: [the view's, the picture's] px, mean: the mean difference of the colours (0-255) over the pixels both
    draw opaque, share: those pixels' share of the picture's opaque ones} of two 1280 x 800 drawings."""
    from PIL import Image, ImageChops, ImageStat

    one, two = (Image.open(io.BytesIO(data)).convert("RGBA") for data in (live, picture))
    if one.size != two.size:
        return {"margins": None, "mean": None, "share": 0, "sizes": [one.size, two.size]}

    def margins(image):
        box = image.getchannel("A").getbbox() or (0, 0, 0, 0)
        return [box[0], box[1], image.size[0] - box[2], image.size[1] - box[3]]

    solid = [image.getchannel("A").point(lambda value: 255 if value == 255 else 0) for image in (one, two)]
    both = ImageChops.multiply(*solid)
    count, total = both.histogram()[255], solid[1].histogram()[255]
    difference = ImageChops.difference(one.convert("RGB"), two.convert("RGB"))
    mean = ImageStat.Stat(difference, mask=both).mean
    # Each pixel's largest channel difference, over the pixels both draw opaque: how many are within 16 levels.
    largest = ImageChops.lighter(ImageChops.lighter(*difference.split()[:2]), difference.split()[2])
    histogram = largest.histogram(mask=both)
    return {"margins": [margins(one), margins(two)], "mean": round(sum(mean) / 3, 3) if count else None, "share": round(count / max(1, total), 4),
            "close": round(sum(histogram[:17]) / max(1, count), 4)}


def swipe(page, start, step, count=8):
    """A one-finger swipe from ``start`` by ``count`` steps of ``step`` (CSS px), as a phone's touch events."""
    session = page.context.new_cdp_session(page)
    x, y = start
    session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    for k in range(1, count + 1):
        session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + step[0] * k, "y": y + step[1] * k}]})
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    session.detach()


def part_view(browser):
    """A sensor's page in 3D (the user's request of 2026-11-05), at 1440 x 900 and at a 390 x 844 phone, every view set
    (library_case with views: the art the tree's or made here, the scenes the tree's)."""
    if not any(arts(browser).values()):
        # A built site before the shoot (no art/, no view in entries.json): nothing to turn yet; after it, a failure.
        check("view: the 3D view's art is there for the sensors entries.json gives a view", not VIEWED, "a built site without the shoot's art/")
        return
    # The grid: no three.js, no web/cad module, whatever the sensors' views.
    page = view_page(browser)
    library_case(page, "pictures", view=True)
    open_library(page)
    load_grid(page)
    loaded = [url for url in page.requests if re.search(r"three|/cad/", url)]
    check("view: the grid (every shelf and card in sight) loads no three.js and no web/cad module", not loaded and len(page.requests) > 10, loaded[:4])
    page.context.close()
    for width, height, mobile in ((1440, 900, False), (390, 844, True)):
        size = f"{width}"
        for key in (VIEW_GRIPPER, VIEW_UMI):
            variant = ENTRIES["variants"][key]
            name = f"{size}, {variant['label']}"
            page = view_page(browser, width, height, mobile=mobile)
            library_case(page, "pictures", view=True)
            samples = load_samples(page, key)
            shown = [sample for sample in samples if sample["shot"] is not None]
            last = samples[-1]
            before = [sample for sample in shown if sample["state"] != "drawn" or sample["build"] != variant["build_id"]]
            drawn = [index for index, sample in enumerate(shown) if sample["state"] == "drawn" and sample["build"] == variant["build_id"]]
            loaded = [index for index, sample in enumerate(shown) if sample["loaded"]]
            check(f"view {name}: the picture first (eager, loaded, shown; the view hidden), then the view drawn over it (the picture hidden), "
                  "never neither",
                  shown and drawn and loaded and loaded[0] <= drawn[0] and shown[0]["loading"] is None and shown[0]["img"]
                  and all(not sample["live"] and (sample["picture"] or not sample["loaded"]) for sample in before)
                  and last["state"] == "drawn" and last["live"] and not last["picture"],
                  {"samples": len(samples), "first": shown[0] if shown else None, "last": last})
            moved = [sample for sample in shown if any(abs(a - b) > 0.5 for a, b in zip(sample["shot"] + sample["open"], shown[0]["shot"] + shown[0]["open"]))]
            check(f"view {name}: the picture's box and Open never move as the view arrives; the view's host and canvas the slot's box",
                  not moved and all(abs(a - b) <= 0.5 for a, b in zip(last["host"] or [], last["shot"])) and last["host"]
                  and all(abs(a - b) <= 1 for a, b in zip(last["canvas"] or [], last["shot"])) and last["canvas"], (moved[:1], last))
            page.wait_for_timeout(400)
            rest = page.evaluate(FRAME_COUNTS)
            page.wait_for_timeout(500)
            still = page.evaluate(FRAME_COUNTS)
            check(f"view {name}: nothing renders at rest (no frame asked for, no WebGL draw over 500 ms)", rest == still and rest["draws"] > 0, (rest, still))
            page.screenshot(path=f"{SHOTS}/library_view_{key}_{size}_home.png")
            aria = page.evaluate(ARIA)
            named = page.get_by_role("group", name=aria["alt"] or "?", exact=True).count() if aria["alt"] else 0
            check(f"view {name}: the view a group named by the picture's alt ('{aria['alt']}'), in the tab order, described by its hint "
                  "(drag, the arrow keys, 0); its canvas hidden from a screen reader, a vertical swipe the page's (touch-action pan-y)",
                  aria["role"] == "group" and aria["label"] == aria["alt"] and aria["alt"] and named == 1 and aria["tab"] == 0 and aria["hint"]
                  and all(re.search(word, aria["hint"], re.IGNORECASE) for word in (r"\bdrag", r"\barrow", r"\b0\b")) and aria["canvas"] == "true"
                  and aria["touch"] == "pan-y", (aria, named))
            # The live drawing at its homes against the picture (the pictures' pane: 1280 x 800), when the picture is its.
            # The visitor's view moves its drawing to the middle by a lens shift, the pictures by whole pixels (library_shots
            # centred()): the drawing is written as the shots tool writes a picture (its encode()) and compared with it, so
            # the picture's lossy WebP is on both sides (the canvases differ only where the shift rounds an edge otherwise).
            if comparable(key):
                reads = home_reads(page)
                compared = {mode: None for mode in library_shots.MODES}
                if sorted(reads) == sorted(library_shots.MODES):
                    files, _ = library_shots.encode(reads)
                    for mode in library_shots.MODES:
                        picture = page.request.get(SITE["base"] + "static/library/" + IMAGES[key][mode]["src"]).body()
                        compared[mode] = dict(likeness(files[mode], picture), margins=likeness(reads[mode]["png"], picture)["margins"],
                                              same=files[mode] == picture, offset=reads[mode]["state"].get("offset"),
                                              home=(reads[mode]["state"].get("drawn_mode"), reads[mode]["state"].get("moved")))
                check(f"view {name}: at each home the view's drawing stands where its picture's does (margins within 1 px, at the pictures' 1280 x 800, "
                      "moved to the middle by its own lens shift) and is its picture (written as the shots tool writes one: the colours of the pixels "
                      "both draw opaque within 1 level on average, 99 % of them within 16, over 99 % of the picture's)",
                      all(item and item["margins"] and all(abs(a - b) <= 1 for a, b in zip(*item["margins"])) and item["mean"] is not None
                          and item["mean"] < 1 and item["close"] >= 0.99 and item["share"] >= 0.99 and item["home"] == (mode, False)
                          for mode, item in compared.items()), compared)
            else:
                print(f"    view {name}: its picture is not its 3D view's (shot before the view): drawing and picture not compared", flush=True)
            box = page.evaluate(CANVAS_BOX)
            centre = (box[0] + box[2] / 2, box[1] + box[3] / 2)
            state = lambda: page.evaluate(LIB_STATE)  # noqa: E731
            turned = {}
            page.mouse.move(*centre); page.mouse.down(); page.mouse.move(centre[0] + min(120, box[2] / 3), centre[1] + 20, steps=8); page.mouse.up()
            page.wait_for_timeout(150)
            turned["drag"] = state()["moved"]
            page.screenshot(path=f"{SHOTS}/library_view_{key}_{size}_dragged.png")
            page.focus("#libDetail .lib-live")
            page.keyboard.press("0"); page.wait_for_timeout(120)
            turned["0"] = state()["moved"]
            page.keyboard.press("ArrowLeft"); page.wait_for_timeout(120)
            turned["ArrowLeft"] = state()["moved"]
            page.keyboard.press("0"); page.wait_for_timeout(120)
            page.keyboard.press("ArrowUp"); page.wait_for_timeout(120)
            turned["ArrowUp"] = state()["moved"]
            page.mouse.dblclick(*centre); page.wait_for_timeout(150)
            turned["dblclick"] = state()["moved"]
            check(f"view {name}: a drag turns the view, 0 brings it home, ArrowLeft and ArrowUp turn it, a double click brings it home",
                  turned == {"drag": True, "0": False, "ArrowLeft": True, "ArrowUp": True, "dblclick": False}, turned)
            modes = {}
            for mode in ("assembled", "exploded"):
                page.click(f"#libDetail .lib-view label:has(input[value='{mode}'])")
                library_shots.poll(page, "(mode) => { const s = JSON.parse(document.getElementById('libViewState').textContent); return s.drawn_mode === mode; }", mode, 10)
                now = state()
                modes[mode] = (now["mode"], now["drawn_mode"], now["moved"], now["state"])
                if mode == "assembled":
                    page.screenshot(path=f"{SHOTS}/library_view_{key}_{size}_assembled.png")
            check(f"view {name}: the Exploded | Assembled switch drives the view both ways (its mode drawn, at its home)",
                  modes == {"assembled": ("assembled", "assembled", False, "drawn"), "exploded": ("exploded", "exploded", False, "drawn")}, modes)
            page.focus("#libDetailTitle")
            for _ in range(20):
                page.keyboard.press("Tab")
                if page.evaluate("() => document.activeElement.classList.contains('lib-live')"):
                    break
            ring = page.evaluate(RING)
            page.screenshot(path=f"{SHOTS}/library_view_{key}_{size}_focus.png")
            check(f"view {name}: Tab reaches the view, its focus ring shown (:focus-visible, an outline)",
                  ring["focused"] and ring["visible"] and ring["style"] not in ("none", "") and ring["width"] >= 1, ring)
            if mobile:
                page.evaluate("() => scrollTo(0, 0)"); page.wait_for_timeout(100)
                box = page.evaluate(CANVAS_BOX)
                top = page.evaluate("() => scrollY")
                swipe(page, (box[0] + box[2] / 2, box[1] + box[3] / 2 + 20), (0, -12))
                page.wait_for_timeout(400)
                scrolled = page.evaluate("() => scrollY") - top
                stayed = state()["moved"]
                page.evaluate("() => scrollTo(0, 0)"); page.wait_for_timeout(150)
                box = page.evaluate(CANVAS_BOX)
                swipe(page, (box[0] + box[2] / 2 - 60, box[1] + box[3] / 2), (15, 0))
                page.wait_for_timeout(300)
                page.screenshot(path=f"{SHOTS}/library_view_{key}_{size}_swiped.png")
                check(f"view {name}: a vertical swipe on the view scrolls the page, a sideways one turns the view",
                      scrolled >= 40 and state()["moved"] is True, {"scrolled": scrolled, "turned by the vertical swipe": stayed, "turned": state()["moved"]})
            engine = [url for url in page.requests if re.search(r"/api/|/py/|pyodide|backend\.js|(^|/)app\.js", url)]
            check(f"view {name}: no request for the server's API, py/, Pyodide, backend.js or app.js; no console error",
                  not engine and not errors_of(page), (engine[:3], errors_of(page)[:3]))
            page.context.close()
        # A UMI sensor drawn after a gripper on the same page (the one view, its stage taken down) as on a page of its own.
        first = view_page(browser, width, height, mobile=mobile)
        library_case(first, "pictures", view=True)
        own = open_view(first, VIEW_UMI)
        alone = home_reads(first)
        first.context.close()
        after = view_page(browser, width, height, mobile=mobile)
        library_case(after, "pictures", view=True)
        gripper = open_view(after, VIEW_GRIPPER)
        after.evaluate("(key) => { location.hash = '#' + key; }", VIEW_UMI)
        then = view_settled(after, VIEW_UMI)
        followed = home_reads(after)
        same = {mode: mode in alone and mode in followed and likeness(alone[mode]["png"], followed[mode]["png"]) for mode in library_shots.MODES}
        check(f"view {size}: the UMI finger drawn after Trossen WidowX AI's whole gripper (one view, the stage's scene taken down) "
              "draws as on a page of its own (the same margins and colours at both homes)",
              (own or {}).get("state") == (gripper or {}).get("state") == (then or {}).get("state") == "drawn" and (gripper or {}).get("gripper") is True
              and (then or {}).get("gripper") is False and (then or {}).get("stage") is None
              and all(item and item["margins"][0] == item["margins"][1] and item["mean"] == 0 and item["share"] == 1 for item in same.values()), same)
        after.context.close()
        # Without WebGL, without DecompressionStream, its art a 404 or asked to save data: the picture stays.
        art = Path(library_write.art_path(VIEW_GRIPPER)).name
        for case, scripts, missing, states in (("without WebGL", (NO_WEBGL,), (), ("unavailable", "failed")),
                                               ("without DecompressionStream", (NO_DECOMPRESSION,), (), ("unavailable", "failed")),
                                               ("its art a 404", (), (art,), ("failed",)), ("with Save-Data", (SAVE_DATA,), (), ("off",))):
            page = view_page(browser, width, height, scripts=scripts, mobile=mobile)
            library_case(page, "pictures", missing=missing, view=True)
            settled = open_view(page, VIEW_GRIPPER) or {}
            page.wait_for_timeout(300)
            seen = page.evaluate(LOAD_SAMPLE)
            allowed = [f"/static/library/art/{art}"] if missing else []
            errors = errors_of(page, allowed)
            if case == "without WebGL":  # three.js says why it has no renderer (console.error), which the page catches
                errors = [entry for entry in errors if not (entry[0] == "error" and "WebGL context" in entry[1])]
            three_d = [url for url in page.requests if re.search(r"three|/cad/", url)]
            check(f"view {size}: {case} the picture stays (shown, loaded), no view; no uncaught error"
                  + (", three.js and web/cad never loaded" if case == "with Save-Data" else ""),
                  settled.get("state") in states and seen["picture"] and seen["loaded"] and not seen["live"] and not errors
                  and (case != "with Save-Data" or not three_d), (settled.get("state"), settled.get("note"), seen, errors[:3], three_d[:2]))
            if case == "without WebGL":
                page.screenshot(path=f"{SHOTS}/library_view_no_webgl_{size}.png")
            page.context.close()
        # The dark scheme: the view's box stays light (the picture's), the view over it.
        page = view_page(browser, width, height, scheme="dark", mobile=mobile)
        library_case(page, "pictures", view=True)
        settled = open_view(page, VIEW_GRIPPER) or {}
        grounds = page.evaluate(GROUNDS)
        look = page.evaluate("() => document.documentElement.dataset.theme")
        page.screenshot(path=f"{SHOTS}/library_view_dark_{size}.png")
        check(f"view {size} (dark): the view drawn in the picture's light box (#f5f5f7), its host transparent over it",
              look == "dark" and settled.get("state") == "drawn" and grounds == {"slot": "rgb(245, 245, 247)", "host": "rgba(0, 0, 0, 0)"} and not errors_of(page),
              (look, settled.get("state"), grounds))
        page.context.close()


class QuietFiles(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--site", type=Path, default=None, help="a site tools/build_static_site.py built, served here (default: app.py at FPC_PORT)")
    parser.add_argument("parts", nargs="*", help="only these parts (e.g. part_routes)")
    args = parser.parse_args(argv)
    server = None
    if args.site is not None:
        root = args.site.resolve()
        scratch = Path(SCRATCH) / "library-site"
        scratch.mkdir(parents=True, exist_ok=True)
        link = scratch / SUBPATH
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(root, target_is_directory=True)
        server = ThreadingHTTPServer(("127.0.0.1", STATIC_PORT), functools.partial(QuietFiles, directory=str(scratch)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        SITE.update(base=f"http://127.0.0.1:{STATIC_PORT}/{SUBPATH}/", root=root)
    print(f"the Library at {SITE['base']}library.html", flush=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=WEBGL_ARGS)
            parts = (part_layout, part_grid, part_routes, part_first_screen, part_pictures, part_view, part_placeholders, part_family,
                     part_downloads, part_isolation, part_errors)
            for part in parts:
                if args.parts and part.__name__ not in args.parts:
                    continue
                print(f"--- {part.__name__}", flush=True)
                started = time.monotonic()
                try:
                    part(browser)
                except Exception as error:  # noqa: BLE001 - report and continue
                    check(f"{part.__name__} ran to completion", False, repr(error))
                print(f"    ({time.monotonic() - started:.0f} s)", flush=True)
            browser.close()
    finally:
        if server is not None:
            server.shutdown()
    return 0 if summary() else 1


if __name__ == "__main__":
    sys.exit(main())
