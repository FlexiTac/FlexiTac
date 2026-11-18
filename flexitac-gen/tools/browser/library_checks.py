"""The Library (the first page, index.html, since the user's decision of 2026-11-16; library.html before; web/library.js;
the user's requests of 2026-11-05) in the browser.

Against a running app.py (FPC_PORT, as the other checks), or with --site a built static site (tools/build_static_site.py;
served here under /flexitac-gen/ on FPC_STATIC_PORT, default FPC_PORT + 1, as GitHub Pages serves a project site):

- part_layout (the layout of 2026-11-06: the user's "其他夹爪的话,不需要每个夹爪一row,你就每个row放4个夹爪就好了", "只有
  umi finger在首页而可以显示重复,其他的夹爪后面就只出现一次,然后标注一下点进去我们有1-3mm customization" and "UMI
  Fin-Ray Gripper. ... 这个section可以放在夹爪的后面"): at 1440, 1100, 900, 768, 744, 735, 734, 600, 390, 360 and 320 px
  no horizontal page overflow (320 px since the header's below-360 rules of 2026-11-05); no tile and no "Start here.";
  the showcase's card (2026-11-12; showcase_checks.py part_page), then the grippers' section ('Grippers. <their count>, each
  fitted at four pitches.', the count entries.json's, a word as library.js writes it: 'Seven' before the grippers of
  2026-11-16..17), its cards in the parts' order (the LeFlexiTac's first)
  (gripper-<part>, opening #<part>-2mm, named by the gripper, its two grey lines its range, '1 to 3 mm', and 'Pick your
  pitch', no badge line), four to a row from 735 px and two below, the last row the rest (rows_of_cards()), never wider than the UMI
  shelf's cards from 735 px and as wide from 1100 px, every grey line on one line and no text past its card's box down
  to 320 px; then the UMI finger's shelf, since the user's request of 2026-11-16 one card per finger shape (its pitches
  by pitch, closed by the tapered tips' family card, before): 'Straight finger' (its 2 mm sensor, '1 to 3 mm', 'Pick
  your pitch', no grid id), then the family's cards in their order ('Short taper', 'Convex arc tip', 'Trapezoid tip',
  'Concave arc tip', 'Pointed tip', each its sensor and its two lines), no badge line, each name and line on one line
  from 1440 to 320 px, four cards in view from 1100 px, three from 735 px, 78 % of the row below, its six
  overflowing with their arrows at 1440 px, 56 px below the grid's last row; at 390 px its row overflows (never the
  page), '<' is off at its start and '>' moves it by one card, and an arrow Tabbed to shows its focus ring inside the
  window at 390 and 360 px, each of its cards Tabbed to whole inside the row's gutters (the review of 2026-11-06) and its
  focus ring inside the window with room under it (the verification of 2026-11-06);
  both headings ('Grippers. <their count>, each fitted at four pitches.', the count entries.json's; 'UMI Fin-Ray Gripper. Six finger shapes, straight to
  pointed.'), one line at 1440 and 1280 px, never splitting a range or 'straight to pointed', at most two lines at
  900 px broken between phrases.
- part_first_screen (the user's decision of 2026-11-05: the picture may be squashed): below 900 px a sensor's picture
  is 3:1 above Open (16:10 beside it from 900 px), shown, its drawing contained and centred; Open's bottom in the
  window at 390 x 844 on every sensor's page and the Tapered tips page (#umi-tapers), at 360 x 740 on every gripper's sensor page,
  since the window of 2026-11-15 (a sheet, no header above the page) at 375 x 667, 360 x 740 and 320 x 640 on every
  page too, and reported at every phone size (at 320 x 568 the tapered tips' below the first screen; the Short taper's the
  sample of two controls since 2026-11-16); since the pictures of
  2026-11-05 in both cases (CASES): with pictures (the picture and its Exploded | Assembled control inside the frame
  above Open, the picture contained and centred) and with none (the placeholder's drawing, as before); since the 3D
  view of 2026-11-05 the pictures' case with every sensor's view set and with none (VIEW_CASES), with views each
  phone's two sample pages measured again once the view is drawn over the picture: nothing moves, the view's box the
  slot's.
- part_pictures (the on-part figure on the cards and a sensor's page, the user's request of 2026-11-05; the pictures'
  contract: entries.json's "image", shots/<id>.exploded.webp, .assembled.webp and .exploded.card.webp): the tree's own
  pictures when entries.json names them, else stand-ins drawn here in the browser and served for the contract's
  "image" (nothing committed).  Every card of the grid (the grippers', each its 2 mm sensor's, the UMI shelf's six shapes,
  each its sensor's: the grippers' count and six; 13 before the grippers of 2026-11-16..17, 12 before the shapes of 2026-11-16) shows its sensor's Exploded card picture, contained and
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
  own lens shift) and, written as the shots tool writes a picture (its webp(), not centred again), its picture (colours
  within 1.5 levels on average, 99 % within 16), where the picture was shot from the view (its record has art, or its part has no scene); a drag, ArrowLeft
  and ArrowUp turn it, 0 and a double click bring it home; the Exploded | Assembled switch drives it both ways; Tab
  reaches it with its focus ring; at 390 px a vertical swipe scrolls the page and leaves the view at home, a sideways one turns the view; no
  request for the API, py/, Pyodide, backend.js or app.js, no console error; the UMI finger drawn after the gripper on
  the same page (one view, the stage's scene taken down) as on a page of its own; without WebGL, without
  DecompressionStream, its art a 404 or with Save-Data (no three.js then) the picture stays, no uncaught error; in the
  dark scheme the view drawn in the picture's light box.
  Its drag hint (2026-11-15): never shown while the view loads, shown once drawn, its size the view's, its sway, a right
  click leaving it, a drag begun on it turning the view and hiding it, hidden through 0, the keys, a double click and
  another pitch, shown again on another gripper's page; on Trossen WidowX AI's page from its card (hint_paths, the
  review of 2026-11-15): a lost and restored context before and after a use, a phone's vertical swipe leaving it and a
  sideways one hiding it, Back then Forward showing it again.
- part_view_hint_sizes (the review of 2026-11-15): the drag hint the view's size at nine windows from 1440 x 900 to
  320 x 640, Unitree Dex1's view and the showcase's.
- part_view_race (the review of 2026-11-06): the view asked for again and again while its files load, on a 400 kbit/s,
  150 ms network (five pitch and part changes with four mode toggles during each load; Back and Forward between the grid
  and two grippers' pages; Unitree Dex1's sensor left for Franka Hand's, which is drawn first): each time the sensor
  asked last drawn at its home exactly as a fresh page draws it, every pixel, its state that sensor's, no error.
- part_looks (the looks, the user's request of 2026-11-12: every gripper coloured after photos of the real product;
  docs/LIBRARY_VIEW.md "The looks"; the reviews of 2026-11-12: nothing in the browser had asserted them), at 1440 x 900,
  on the first gripper whose scene has looks (Franka Hand's 2 mm sensor; none: said and left out): the view drawn with
  no console error or warning, its stage's looks the scene's (#libViewState stage.looks: the bodies' looks by name, the
  part's, the crease angle, and the part's corners sharing as many points as its file has at 1 um); at each home its
  picture (as part_view compares one) where the picture was shot from the view; far from the same scene served without
  its looks (the one grey of before); the UMI finger drawn after it on the same page exactly as on a page of its own
  (the part's material put back, every pixel) and the gripper drawn again after the UMI exactly as on a fresh page; its
  WebGL context lost and back: drawn again exactly as before (the gripper studio made again); and on Unitree Dex1's
  sensor, whose part's file is in metres, its scene served with a look for the part and a crease angle: the part's
  corners share its file's points at 1 um, not at 1 mm.
- part_pad (the UMI pad's tint, the rules' part_pad: the user's decision of 2026-11-14, "you can do it darken"; skipped
  where the rules give none), at 1440 x 900, on the UMI finger's 2 mm sensor against the same served without the tint,
  at both homes in the pictures' pane: no console error; Exploded every pixel as without it; Assembled the same outline,
  the pixels the tint changes (5 % of the drawing at least) from the amber board to the photos' dark olive-brown (their
  median's hue 30 to 55 degrees, its value 0.55 at most, 0.7 or more without the tint).
- part_placeholders (no picture: every "image" null): every slot the drawing of its field (its rows and columns), no
  image, no view control and no request for a picture, as before the pictures.
- part_family (the tapered tips, 2026-11-05; since the user's request of 2026-11-16 one card per shape): the UMI
  shelf's cards (Straight finger, then Short taper, Convex arc tip, Trapezoid tip, Concave arc tip and Pointed tip,
  their lines and pages), no tip with a shelf or a card but its shape's; the Short taper's card opens its 9.8 mm
  trapezoid's page with Shape and Tip width in place of the pitch, its Tip fact over the last 40 mm; a change of either
  replaces the address (no history entry) with the card's sensor, that control focused; Back returns to the grid, the
  card focused; the Concave arc tip's page its Tip width alone, the Pointed tip's no control; a tip's id or part id
  opens its page directly, its window's X (its back link until 2026-11-15) going to the UMI shelf; the action blue only
  on Open in Gen by Surface.
- part_grid (2026-11-06): each gripper's card opens its 2 mm sensor's page, whose Pitch reaches its four pitches, the
  UMI shelf's Straight finger its 2 mm page with its four pitches, each shape's card its sensor's page with the card's
  axes of more than one choice, and every one of the sensors' pages (58 before the grippers of 2026-11-16..17) is
  reached by clicks alone (the cards, the Pitch, Shape and Tip width); the window's X (a page's back link to
  #gripper-<part> until 2026-11-15) leaves the grid where it was with its card focused; the older addresses land
  sensibly: #shelf-<gripper> on its card (the address #gripper-<part>, no history entry), #shelf-start at the top with
  no hash (opened anew, and typed with the grid scrolled down), #shelf-umi-finray and #grippers on their sections, the
  UMI finger's removed cards' (#umi-finray-1mm, -1.5mm, -3mm) and #umi-tapers their pages with their X to the UMI shelf.
- part_window (the user's request of 2026-11-15: "after we click for all cards to details, we may not jump to a new
  page. lets bump our to a large window, and if you click the "x" of right top conrner, it will close and back show
  lib"): at 1440 x 900, 900 x 900 and 390 x 844, light and dark, each opener (a gripper's card, the UMI shelf's
  Straight finger and a shape's card, the showcase's Details and picture) opens its page in the modal window over the grid, which
  neither moves (its cards' boxes) nor scrolls, the window's page at its top, its title focused, the tab named after
  it; the window's box (min(1200 px, the screen less two gutters) wide, centred, a gutter from the top; a sheet with no
  shadow below 735 px), the cards' look, the dim backdrop; the X round, grey, named Close, in the Tab order and in sight
  with the window's page at its end; the page under it never scrolling (the wheel over the window and the backdrop, End,
  PageDown, Space); Tab and Shift+Tab keeping the focus inside; the X, Escape and a press and release on the backdrop
  closing it to the grid's place with the opener focused and no history entry added, a drag of the 3D view or of a
  selection released over the backdrop, a press on it released inside and a card double-clicked where the backdrop
  then lies keeping it; Back closing it, Forward opening it again; a window's address opened anew showing the Library
  with the window over it; the blue only on Open; no console error; the window's history (window_history(), the review
  of 2026-11-15: after an earlier page, a close request as Android's Back sends one, a cancel then its close, a shared
  link's close request, a pitch, an address typed over the window, Back, Forward and the X over two windows' entries, a
  reload's X: each close to its card focused with no entry added, the next Back the earlier page).  Screenshots:
  library_window_*.png.
- part_window_edges (the review of 2026-11-15, where the other parts' browser does not go): scroll bars that take room
  (Chromium without --hide-scrollbars) at 1440 x 900, light and dark: the window opening over the grid with nothing
  moving, the bar's width made up on the right, the screen's right edge as dim as the backdrop, the page as before once
  it closes; a phone held sideways (844 x 390, 740 x 360) and a dark 390 x 844 phone: the window a sheet with no shadow
  and no hairline frame.
- part_routes: a gripper's card opens its sensor's page in the window at its top, the grid where it was under it, with
  its title focused and the tab named after it,
  Open in Gen by Surface at gen.html?part=<id>, at least as wide as each download pill; another pitch replaces the address
  (no history entry); Back returns to the grid where it was, the card that opened it focused, the tab the Library's
  again; Back and Forward against the back links (the review of 2026-11-06, since 2026-11-15 the window's X: the
  WidowX 250 card, its X, the MakerMods card, Back to the grid where it was with MakerMods focused, Forward to the
  MakerMods window, the ARX X5 card's place typed over it, Back to the MakerMods window, its X to the MakerMods card,
  Forward and Back to the grid where it was, MakerMods focused); the page split evenly from 900 px (each fact on one
  line at 900, 1280 and 1440 px, the pills side by side at 1100, 1280 and 1440 px); #shelf-widowx-250 typed on the ARX X5 page
  its card; #<part> shows its 2 mm sensor with the address kept, #shelf-arx-x5 opened anew its card, #bogus the grid
  with a note, an unknown id typed with the grid scrolled down its note in sight; the X of a window opened directly
  goes to its card; opened at an address of its own with library.js 0.8 s and entries.json 0.4 s late (the reviews of
  2026-11-06), every frame from the first paint read: a sensor's page never paints the grid's title nor the footer
  before its window opens, then shows the Library (its title and footer) under the window; #gripper-<part> and #shelf-umi-finray the title and the footer;
  the Library alone (./) its title at once, as before; entries.json at 500 the title, the footer and the status.
- part_downloads: under app.py the two Gerber ZIPs are app.py's exports of the sensor's design (the fit's proposal #1),
  byte for byte under its names; on the site they are the prebuilt files (files.json, which lists every sensor);
  the part's STL is the mesh, the licence is served (a tapered tip's ZIPs too).
- part_isolation: only the site's own requests (none to py/, a worker, backend.js or app.js; three.js and the web/cad
  modules on a sensor's page with its 3D view only, never on the grid), no console error; the page never says CAD (its
  text, titles, labels) and is English; in light and dark, with every view set and with none, the action blue fills
  only Open in Gen by Surface, nothing green, and scrolling changes nothing.
- part_errors: entries.json missing: the page says so and the header still works; on the site, files.json missing:
  the downloads give way to the note.
- part_first_page (the user's decisions of 2026-11-15 and 2026-11-16, "是的 be first page"): the Library at ./, the
  generator at gen.html; every address of rp.FORWARDS (the generator's of before, library.html's, the Library's own)
  where it should end, its query and hash kept, one history entry, Back the earlier page, nothing of a forwarding
  page painted; the first page's header, Gen by Surface, Rectangular and Open in Gen by Surface going to gen.html in
  this tab and Back to the Library.  Since the same decisions the action blue's second use, the showcase's Design
  your own, is allowed beside Open (blues()).
"Dark" is the page's dark look as the header's toggle leaves it (its stored choice, rp.DARK_CHOICE; 2026-11-06: the page
opens light whatever the system's scheme, which stays light here).
Screenshots go to $FPC_BROWSER_OUT/shots (library_*.png; the pictures' library_pictures_* and library_placeholders_*:
the grid at 1440 and 900 px light and dark, a sensor's page Exploded and Assembled and the Short taper's page at 1440 px
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
import math
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

from rp import (CARD, DARK_CHOICE, FORWARDS, GITHUB_API, GITHUB_ASKED, GITHUB_CARD, PORT, SCRATCH, SHOTS, URL, answer_github, check,  # noqa: E402
                forwarding, summary, wait_until)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import library_shots  # noqa: E402
import library_write  # noqa: E402
# The ordering's two rows of a sensor's window (2026-11-17; web/boards.js): each label, its value's text and its links
# [href, download, target].
BOARDS_GUIDE = "https://docs.google.com/document/d/1bvz6AL7BUkhj4Dj7n9DFXTjnGIX4-ziN8-smiCKpVZU/edit?tab=t.0#heading=h.kk7d14qme9db"
BOARDS_FOLDER = "static/vendor/flexitac-reader/"
ORDER_ROWS = """() => [...document.querySelectorAll('#libDetail .lib-order dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent,
  [...dt.nextElementSibling.querySelectorAll('a')].map(a => [a.getAttribute('href'), a.getAttribute('download'), a.getAttribute('target')])])"""
# The board's dots (the review of 2026-11-17): each "\u00a0· " on the line of the piece before it (a dot never starts a
# line), as [the dot's top, the piece's top] in px.
BOARD_DOTS = """() => [...document.querySelectorAll('#libDetail .lib-board')].flatMap(dd => [...dd.childNodes].filter(node => node.nodeType === 3)
  .map(node => { const range = document.createRange(); const at = node.data.indexOf('·'); range.setStart(node, at); range.setEnd(node, at + 1);
    return [node.data, Math.round(range.getBoundingClientRect().top), Math.round(node.previousSibling.getBoundingClientRect().top)]; }))"""

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
COUNTS = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
          "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty")


def count_word(count: int) -> str:
    """A heading's count as library.js words it: COUNTS's word up to twenty (twelve until the final merge of 2026-11-17: the grid's nineteen cards read 'Nineteen'), its digits past (the review of 2026-11-17 of
    the hands' merge: the grippers' heading is computed from entries.json, and eleven cards or more had raised an
    IndexError here where the page writes 'Eleven' or '13')."""

    return COUNTS[count] if 0 <= count < len(COUNTS) else str(count)
# The grid (the user's requests of 2026-11-06; library.js SHELVED): the grippers' section, one card per part but the
# shelved (the UMI finger, and any part a family closes), each opening its 2 mm sensor, then each shelved part's shelf;
# GRID_CARDS: the sensors whose card pictures the grid shows, in its order (13 since the UMI shelf's shapes of
# 2026-11-16, the grippers' count and six since the grippers of 2026-11-16..17), all asked for as the page opens (it is short), within FIRST_SCREEN_BYTES (test_library's).
SHELVED = ["umi-finray"] + [family["shelf"] for family in ENTRIES["families"].values() if family["shelf"] != "umi-finray"]
CARDED = [part for part in ENTRIES["order"] if part not in SHELVED]
SHELVES = [part for part in ENTRIES["order"] if part in SHELVED]
FAMILIES_OF = {part: [name for name, family in ENTRIES["families"].items() if family["shelf"] == part] for part in ENTRIES["order"]}
GRID_CARDS = library_shots.grid_cards(ENTRIES)


def rows_of_cards(count: int, per_row: int) -> list:
    """The grid's rows of ``count`` cards, ``per_row`` a row, the last one the rest ([4, 4, 2] for ten four to a row)."""

    return [per_row] * (count // per_row) + ([count % per_row] if count % per_row else [])


FIRST_SCREEN_BYTES = 1_000_000
# The tallest sensor's page (a three-line title and two controls: Shape and Tip width): the Short taper's card's sensor
# since the UMI finger's shapes of 2026-11-16 (the Tapered tips page, #umi-tapers, before, whose sensor is the
# Trapezoid tip's card's now, with Tip width alone).
SHORT_TAPER = next(card["default"] for family in ENTRIES["families"].values() for card in family["cards"]
                   if sum(len(axis["choices"]) > 1 for axis in card["axes"]) > 1)


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
# A UMI card's likeness to its Exploded picture enlarged and cut as the shoot cuts it (card_framing()): the mean colour
# difference over the pixels both draw opaque, of 255.  A coarse guard (the review of 2026-11-16): the enlarged 1x picture
# is softer than the card's own render, so the 30 cards score 4.1 to 6.1 at 1.25 as they are; of two cards shot again
# (4.0 and 6.4 before WebP), with the Exploded camera a degree higher they score 5.0 and 6.0, a degree less tilted 7.8
# and 11.3: a degree of elevation passes.  The direction itself is held exactly by the shoot (library_shots.shoot():
# the stage's report at the card's read the Exploded read's, word for word).
LIKENESS_MAX = 8
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
    if case == "placeholders":
        # The Library as before its pictures: the showcase's card too (2026-11-12) without its picture, the drawing of
        # its pad's field in its place (showcase.json's "image" with no file named).
        showcase = LIBRARY / "showcase.json"
        document = dict(json.loads(showcase.read_text(encoding="utf-8")), image={}) if showcase.is_file() else None
        page.route("**/static/library/showcase.json", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(document)))
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
  const textPast = card => { const text = card.querySelector('.lib-card-text'); const box = text.getBoundingClientRect(); const style = getComputedStyle(text);
    const [left, right] = [box.left + parseFloat(style.paddingLeft), box.right - parseFloat(style.paddingRight)];
    return Math.round(Math.max(0, ...[...text.children].flatMap(span => { const range = document.createRange(); range.selectNodeContents(span);
      return [...range.getClientRects()].filter(r => r.width > 0).map(r => Math.max(left - r.left, r.right - right)); })) * 10) / 10; };
  const content = (m => { const r = m.getBoundingClientRect(); const style = getComputedStyle(m);
    return [r.left + parseFloat(style.paddingLeft), r.right - parseFloat(style.paddingRight)]; })(document.querySelector('main.lib'));
  // A shelf (since the review of 2026-11-16 a grid as the grippers' section, no row that scrolls): its cards, their
  // boxes (left and right against the content's edges, top on the page), the grid's width and gap, its rows of cards.
  const rows = [...document.querySelectorAll('#libShelves .lib-shelf')].map(shelf => { const grid = shelf.querySelector('.lib-cards');
    const cards = [...grid.querySelectorAll('.lib-card')]; const style = getComputedStyle(grid); const boxes = cards.map(card => card.getBoundingClientRect());
    const tops = [...new Set(boxes.map(r => Math.round(r.top + scrollY)))].sort((a, b) => a - b);
    return {id: shelf.id, cards: cards.map(card => card.dataset.variant || `family:${card.dataset.family}`), grid: grid.tagName && grid.className,
            scrolls: [...shelf.querySelectorAll('*')].some(n => ['auto', 'scroll'].includes(getComputedStyle(n).overflowX) && n.scrollWidth > n.clientWidth + 1),
            arrows: shelf.querySelectorAll('button').length, inner: grid.clientWidth, gap: parseFloat(style.columnGap), card: boxes[0].width,
            widths: boxes.map(r => Math.round(r.width * 10) / 10), perRow: tops.map(top => boxes.filter(r => Math.round(r.top + scrollY) === top).length),
            inside: boxes.every(r => r.left >= content[0] - 0.5 && r.right <= content[1] + 0.5), past: cards.map(textPast),
            names: cards.map(card => card.querySelector('.lib-card-name').textContent.replace(/\u2011/g, '-')),
            hrefs: cards.map(card => card.getAttribute('href')), shapes: cards.map(card => card.dataset.card || null),
            lines: cards.map(card => [...card.querySelectorAll('.lib-card-line')].map(n => n.textContent.replace(/\u00a0/g, ' '))),
            lineRows: cards.map(card => [card.querySelector('.lib-card-name'), ...card.querySelectorAll('.lib-card-line')].map(rowsOf)),
            badges: cards.filter(card => card.dataset.variant).map(card => card.querySelector('.lib-badge')?.textContent ?? null),
            ids: cards.map(card => card.id || null), heading: shelf.querySelector('h3').textContent.replace(/\u00a0/g, ' '),
            shots: cards.map(card => { const r = card.querySelector('.lib-shot').getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; })}; });
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
              lineRows: [...card.querySelectorAll('.lib-card-line')].map(rowsOf), top: Math.round(r.top + scrollY), width: r.width, past: Math.round(past * 10) / 10,
              shot: (s => [Math.round(s.width * 10) / 10, Math.round(s.height * 10) / 10])(card.querySelector('.lib-shot').getBoundingClientRect())}; })};
  const main = document.querySelector('main.lib');
  return {overflow: de.scrollWidth - de.clientWidth, main: main.scrollWidth - main.clientWidth, rows, grid,
          order: [...document.getElementById('libShelves').children].map(n => n.id || n.className), tiles: document.querySelectorAll('.lib-tile, #libTiles').length}; }"""
# The title's line (the review of 2026-11-05; since the user's request of 2026-11-15 its three steps with arrows): each of
# its rows' right end (a step's box, its arrow included) against the content's right edge (the gutter), its rows, its
# steps' words, the arrow after each, and whether a step is split over two lines (null: not three steps).
HERO = """() => { const tag = document.querySelector('.lib-tagline'); const main = document.querySelector('main.lib');
  const edge = main.getBoundingClientRect().right - parseFloat(getComputedStyle(main).paddingRight);
  const steps = [...tag.querySelectorAll('li')]; const rows = {};
  for (const li of steps) { const r = li.getBoundingClientRect(); const k = Math.round(r.top); rows[k] = Math.max(rows[k] ?? -1e9, r.right); }
  const split = steps.length === 3 ? steps.some(li => { const range = document.createRange(); range.selectNodeContents(li);
    return new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size > 1; }) : null;
  return {lines: Object.keys(rows).length, ends: Object.values(rows).map(right => Math.round(edge - right)), split, tag: tag.tagName,
          words: steps.map(li => li.textContent), arrows: steps.map(li => getComputedStyle(li, '::after').content),
          arrow: steps[0] ? getComputedStyle(steps[0], '::after').color : null, size: getComputedStyle(tag).fontSize}; }"""
# Each section's room below its cards (to the next heading) and its heading's lines (the review of 2026-11-05; since
# 2026-11-06 the grippers' section, then the UMI shelf; whether its arrows showed too until the UMI shelf was a grid,
# 2026-11-16).
SPACING = """() => [...document.querySelectorAll('#libShelves > .lib-shelf, #libShelves > .lib-section')].map((shelf, i, all) => {
  const bottom = Math.max(...[...shelf.querySelectorAll('.lib-card')].map(card => card.getBoundingClientRect().bottom));
  const heading = shelf.querySelector('h3'); const range = document.createRange(); range.selectNodeContents(heading);
  const lines = new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size;
  return [shelf.id, all[i + 1] ? Math.round(all[i + 1].querySelector('h3').getBoundingClientRect().top - bottom) : null, lines]; })"""
# Each shelf heading's lines, as text (the user's decision of 2026-11-05 on its one wording: the range '1 to 3 mm' on one
# line, and since 2026-11-16 the UMI shelf's 'straight to pointed'; a two-line heading broken between its phrases).
HEADING_LINES = """() => [...document.querySelectorAll('#libShelves .lib-shelf h3, #libShelves .lib-section h3')].map(heading => { const lines = []; let top = null;
  const walker = document.createTreeWalker(heading, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) { const text = walker.currentNode;
    for (let i = 0; i < text.data.length; i += 1) { const range = document.createRange(); range.setStart(text, i); range.setEnd(text, i + 1);
      const box = [...range.getClientRects()].find(r => r.width > 0); if (!box) { if (lines.length) lines[lines.length - 1] += text.data[i]; continue; }
      if (Math.round(box.top) !== top) { lines.push(''); top = Math.round(box.top); } lines[lines.length - 1] += text.data[i]; } }
  return [heading.closest('.lib-shelf, .lib-section').id, lines.map(line => line.replace(/\u00a0/g, ' ').trim())]; })"""
# The window's page at its top (since 2026-11-15 the page scrolls in the window, which leaves the grid where it was).
WINDOW_TOP = "() => { document.getElementById('libWindowBody').scrollTop = 0; }"
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
          screen: innerHeight, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          inner: (body => body.scrollWidth - body.clientWidth)(document.getElementById('libWindowBody'))}; }"""
# A sensor's page's 3D view drawn over its picture (its host and canvas shown).
LIVE_SHOWN = """() => { const host = document.querySelector('#libDetail .lib-live'); const canvas = host && host.querySelector('canvas');
  return Boolean(canvas) && host.checkVisibility({visibilityProperty: true}) && canvas.checkVisibility({visibilityProperty: true}); }"""
# A sensor's page's picture loaded (or its placeholder drawn in its place).
PICTURE_SETTLED = """() => { const shot = document.querySelector('#libDetail .lib-shot'); const img = shot && shot.querySelector('img');
  return Boolean(shot) && (!img || (img.complete && img.naturalWidth > 0)); }"""
FOCUS = """() => { const node = document.activeElement; return {id: node.id, variant: node.dataset?.variant || null,
  shelf: node.closest('.lib-shelf, .lib-section')?.id || null}; }"""
# The card focused on its shelf: how far inside the window it lies on either side, and its focus ring (4 px round it)
# inside the window above and below (px; negative: cut).  (Inside its row's gutters while the UMI shelf was a row that
# scrolled sideways, until 2026-11-16.)
CARD_IN_WINDOW = """() => { const card = document.activeElement; if (!card.closest('.lib-shelf .lib-cards')) return null; const box = card.getBoundingClientRect();
  return {card: card.dataset.variant || card.getAttribute('href'), left: Math.round(box.left), right: Math.round(document.documentElement.clientWidth - box.right),
          top: Math.round(box.top - 4), bottom: Math.round(innerHeight - box.bottom - 4)}; }"""
# A card of the grid in the window (its box and its focus ring's 4 px inside it) and the window's scroll.
IN_VIEW = """(id) => { const r = document.getElementById(id).getBoundingClientRect();
  return {inside: r.top - 4 >= 0 && r.bottom + 4 <= innerHeight, top: Math.round(r.top), bottom: Math.round(r.bottom), y: Math.round(scrollY)}; }"""
# Since the window of 2026-11-15: detail the window open, grid the grid shown and not under the window, y the page's
# scroll (the grid's, which the window leaves where it was), top the window's own.
VIEW = """() => ({hash: location.hash, detail: document.getElementById('libWindow').open,
  grid: !document.getElementById('libGrid').hidden && !document.getElementById('libWindow').open,
  y: Math.round(scrollY), top: Math.round(document.getElementById('libWindowBody').scrollTop), history: history.length, tab: document.title, note: document.getElementById('libNote').hidden ? null : document.getElementById('libNote').textContent,
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
# Since the user's decisions of 2026-11-15 and 2026-11-16 the showcase card's Design your own (on the grid, and under a
# window over it) is the action blue's second use, beside Open in Gen by Surface (both lead to Gen by Surface).
DESIGN_BLUE = "a.lib-pill.lib-design"


def blues(page, *rest):
    """The blue fills FILLS should find: the showcase card's Design your own where the grid shows it, then ``rest``."""
    return ([DESIGN_BLUE] if page.evaluate("() => Boolean(document.querySelector('.lib-design')?.checkVisibility())") else []) + list(rest)


SNAPSHOT = """() => ({nodes: [...document.querySelectorAll('body, body *')].filter(n => !n.closest('svg') || n.tagName.toLowerCase() === 'svg').map(n => { const s = getComputedStyle(n);
  return [s.opacity, s.transform, s.visibility, s.filter, n.className && typeof n.className === 'string' ? n.className : ''].join('|'); }),
  animations: document.getAnimations().length})"""
WORDS = """() => [document.title, document.body.innerText, ...[...document.querySelectorAll('[title], [aria-label]')].flatMap(n => [n.getAttribute('title') || '', n.getAttribute('aria-label') || ''])]"""


def new_page(browser, width=1440, height=900, scheme="light"):
    # ``scheme`` the page's look: "dark" the header's toggle on (its stored choice, DARK_CHOICE; 2026-11-06), the system's
    # own scheme light either way (the page no longer follows it).
    # ROUTES (mutants.py's lib kind) served here too.
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme="light", accept_downloads=True)
    for glob, content_type, body in ROUTES:
        context.route(glob, served(content_type, body))
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
    page.goto(SITE["base"] + fragment)
    wait_until(page, READY, 30)
    page.wait_for_timeout(150)


def part_layout(browser):
    page = new_page(browser)
    open_library(page)
    # The UMI finger's shelf (since the user's request of 2026-11-16 one card per finger shape: the straight finger's,
    # its 2 mm sensor, then each card of the tapered tips' family, its sensor); the grippers' cards before it (2026-11-06).
    expected_rows = [(f"shelf-{part}", [ENTRIES["parts"][part]["default"]] + [card["default"] for name in FAMILIES_OF[part] for card in ENTRIES["families"][name]["cards"]])
                     for part in SHELVES]
    shapes_of = {part: [card for name in FAMILIES_OF[part] for card in ENTRIES["families"][name]["cards"]] for part in SHELVES}
    expected_cards = [{"id": f"gripper-{part}", "href": f"#{ENTRIES['parts'][part]['default']}", "variant": ENTRIES["parts"][part]["default"],
                       "name": ENTRIES["parts"][part]["title"], "lines": [pitch_range(part), "Pick your pitch"]} for part in CARDED]
    rows_of, sizes_of, text_of, shelf_text_of, shelf_rows_of = {}, {}, {}, {}, {}
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(120)
        layout = page.evaluate(LAYOUT)
        check(f"layout {width}: no horizontal page overflow", layout["overflow"] <= 0, layout["overflow"])
        # The UMI shelf a grid since the review of 2026-11-16 (its shapes side by side; a row that scrolled sideways
        # before): since the user's request of that day the grippers' grid, four to a row from 735 px (three until
        # then), two below, each card its column's width, all inside the content's edges, no row scrolling and no arrows.
        per_row = 4 if width >= 735 else 2
        sizes = []
        for row in layout["rows"]:
            expected = (row["inner"] - (per_row - 1) * row["gap"]) / per_row
            sizes.append(all(abs(card - expected) <= 1 for card in row["widths"]) and row["inside"] and not row["scrolls"] and row["arrows"] == 0)
        check(f"layout {width}: the UMI shelf's cards {per_row} to a row, each its column's width, inside the content's edges, nothing scrolling sideways",
              all(sizes) and layout["rows"], [(row["id"], row["widths"][:2], round(row["inner"], 1), row["inside"], row["scrolls"], row["arrows"]) for row in layout["rows"]])
        shelf_rows_of[width] = {row["id"]: row["perRow"] for row in layout["rows"]}
        cards = layout["grid"]["cards"] if layout["grid"] else []
        tops = sorted({card["top"] for card in cards})
        rows_of[width] = [sum(1 for card in cards if card["top"] == top) for top in tops]
        umi = layout["rows"][0]["card"] if layout["rows"] else 0
        # Each card's width and its picture's box (the user's request of 2026-11-16: "确保你要和上面的card大小保持一致"):
        # every gripper's and every UMI card's, one size.
        sizes_of[width] = (sorted({(round(card["width"], 1), tuple(card["shot"])) for card in cards}),
                           sorted({(width_, tuple(shot)) for row in layout["rows"] for width_, shot in zip(row["widths"], row["shots"])}))
        text_of[width] = [(card["name"], card["lineRows"], card["past"]) for card in cards if any(rows != 1 for rows in card["lineRows"]) or card["past"] > 0.5]
        # The UMI shelf's cards (2026-11-16): each one's name and grey lines on one line each from 900 px; below, at most
        # two lines each (balanced: 'Concave / arc tip', 'Pick shape / and width', as the grippers' 'Franka / Hand'), never
        # past the card's box: four to a row from 735 px since the user's request of that day (the grippers' 150 to 190 px
        # cards; three to a row, from its review that day, had kept them on one line from 735 px), two on a phone.
        most = 1 if width >= 900 else 2
        shelf_text_of[width] = [(row["id"], name, rows, past) for row in layout["rows"] for name, rows, past in zip(row["names"], row["lineRows"], row["past"])
                                if any(n > most for n in rows) or past > 0.5]
        # The review of 2026-11-05: the grippers' section as far from the UMI shelf's heading (its cards' 28 px and the
        # shelf's) as the hero is from its own heading.
        spacing = page.evaluate(SPACING)
        check(f"layout {width}: the UMI shelf's heading 56 px below the grippers' last row", [(name, gap) for name, gap, _ in spacing if gap is not None] == [("grippers", 56)],
              spacing)
        if width == 1440:
            # (Since 2026-11-12 the showcase's one card comes first, in a section of its own: showcase_checks part_page.)
            check("layout: no tile and no 'Start here.'; the showcase's card, the grippers' section, then the UMI finger's shelf",
                  layout["tiles"] == 0 and layout["order"] == ["lib-showcased", "grippers"] + [f"shelf-{part}" for part in SHELVES]
                  and not page.query_selector("#shelf-start"), (layout["tiles"], layout["order"]))
            check("layout: the UMI shelf one card per finger shape: the straight finger's (its 2 mm sensor), then each shape's card (its sensor), "
                  "in the family's order", [(row["id"], row["cards"]) for row in layout["rows"]] == expected_rows, [(row["id"], row["cards"]) for row in layout["rows"]])
            got = [{key: card[key] for key in ("id", "href", "variant", "name", "lines")} for card in cards]
            check("layout: the grippers' section a card per gripper in the parts' order (gripper-<part>, opening its 2 mm sensor, its name, "
                  "'1 to 3 mm' (its own range) and 'Pick your pitch'), no badge line",
                  got == expected_cards and layout["grid"]["badges"] == 0 and len(got) == len(CARDED) and got[0]["id"] == "gripper-leflexitac"
                  and {card["name"]: card["lines"][0] for card in got}.get("Franka Hand") == "1 to 2.5 mm"
                  and {card["name"]: card["lines"][0] for card in got}.get("YUBI Gripper") == "1 to 2.5 mm"
                  and {card["name"]: card["lines"][0] for card in got}.get("Unitree Dex3-1") == "1 to 2.5 mm",
                  [(one, other) for one, other in zip(got, expected_cards) if one != other][:2] or got[:2])
            headings = {row["id"]: row["heading"] for row in layout["rows"]}
            headings["grippers"] = layout["grid"]["heading"]
            # The grippers' section in one wording (the user's decision of 2026-11-05): its count and their pitches; the UMI
            # finger's shelf, since the user's request of 2026-11-16, its shapes: the part's own (straight) and each card's,
            # the last one's named ('Six finger shapes, straight to pointed.'), here from entries.json's cards, not its
            # headings.
            expected_headings = {"grippers": f"Grippers. {count_word(len(CARDED))}, each fitted at {COUNTS[4].lower()} pitches."}
            for part in SHELVES:
                last = shapes_of[part][-1]["axes"][0]["choices"][-1]["label"].lower()
                expected_headings[f"shelf-{part}"] = f"{ENTRIES['parts'][part]['title']}. {count_word(1 + len(shapes_of[part]))} finger shapes, straight to {last}."
            check(f"layout: both headings, their bold half and their grey half ('{expected_headings['grippers']}', "
                  "'UMI Fin-Ray Gripper. Six finger shapes, straight to pointed.')",
                  headings == expected_headings
                  and headings["shelf-umi-finray"] == "UMI Fin-Ray Gripper. Six finger shapes, straight to pointed."
                  and not [text for text in headings.values() if re.search(r"\b(fine|coarse)\b", text)],
                  {key: value for key, value in headings.items() if value != expected_headings.get(key)} or headings)
            # Each card of the UMI shelf named by its shape, its two grey lines in the grippers' cards' style (the straight
            # finger's its range and 'Pick your pitch', each shape's card its own), opening its sensor's page; the
            # straight finger's card no grid id (its place is the shelf's), each shape's card its key.
            expected_cards_of = {f"shelf-{part}": [(ENTRIES["parts"][part]["card"], [pitch_range(part), "Pick your pitch"], f"#{ENTRIES['parts'][part]['default']}", None)]
                                 + [(card["title"], card["lines"], f"#{card['default']}", card["key"]) for card in shapes_of[part]] for part in SHELVES}
            got_cards_of = {row["id"]: list(zip(row["names"], row["lines"], row["hrefs"], row["shapes"])) for row in layout["rows"]}
            check("layout: the UMI shelf's cards: 'Straight finger' ('1 to 3 mm', 'Pick your pitch'), then 'Short taper' ('5.8 to 21.8 mm', "
                  "'Pick shape and width'), 'Convex arc tip', 'Trapezoid tip', 'Concave arc tip' ('Pick your tip width') and 'Pointed tip' "
                  "('2 mm tip', '2 mm pitch'), each opening its sensor's page",
                  got_cards_of == expected_cards_of and [name for name, *_ in got_cards_of["shelf-umi-finray"]]
                  == ["Straight finger", "Short taper", "Convex arc tip", "Trapezoid tip", "Concave arc tip", "Pointed tip"]
                  and all(card_id is None for row in layout["rows"] for card_id in row["ids"]),
                  got_cards_of)
            check("layout 1440: the UMI shelf's six cards in the grippers' grid, four and two, all in the window's width (the user's request of "
                  "2026-11-16; two rows of three since its review that day, a row that scrolled sideways before)",
                  all(row["perRow"] == [4, 2] and row["inside"] and len(row["cards"]) == 6 for row in layout["rows"]),
                  [(row["id"], row["perRow"], row["inside"]) for row in layout["rows"]])
            # Since 2026-11-16 no card of the UMI shelf has a badge line (the pitch cards had one, 'Fine' on the 1 mm one,
            # so their names lined up).
            badges = {row["id"]: row["badges"] for row in layout["rows"]}
            check("layout 1440: no badge line on the UMI shelf's cards", all(badge is None for found in badges.values() for badge in found), badges)
            page.screenshot(path=f"{SHOTS}/library_grid_1440.png")
        if width == 390:
            page.screenshot(path=f"{SHOTS}/library_grid_390.png")
    # Rows of four from 735 px, of two below, the last one the rest (2026-11-17, the grippers and the hands added: the
    # count entries.json's; 4 + 3 and 2 + 2 + 2 + 1 with the seven grippers before them).
    check(f"layout: the grippers four to a row from 735 px ({' + '.join(map(str, rows_of_cards(len(CARDED), 4)))}), two below "
          f"({' + '.join(map(str, rows_of_cards(len(CARDED), 2)))}), never three",
          all(rows_of[width] == rows_of_cards(len(CARDED), 4 if width >= 735 else 2) for width in WIDTHS), rows_of)
    check("layout: the UMI shelf four to a row from 735 px (4 + 2), two below (2 + 2 + 2), as the grippers'",
          all(found == {"shelf-umi-finray": [4, 2] if width >= 735 else [2, 2, 2]} for width, found in shelf_rows_of.items()), shelf_rows_of)
    check("layout: at every width from 1440 to 320 px each UMI shelf's card a gripper's card's size, its width and its picture's box (one size "
          f"for all {len(CARDED) + 6}; the user's request of 2026-11-16: the shelf's cards had been a third of the row)",
          all(len(grid) == 1 and umi == grid for grid, umi in sizes_of.values()), {width: sizes for width, sizes in sizes_of.items() if width in (1440, 1100, 768, 390)})
    check("layout: from 1440 to 320 px every grey line of a gripper's card on one line, no text past its card's box",
          not any(text_of.values()), {width: found for width, found in text_of.items() if found})
    check("layout: from 1440 to 900 px each name and grey line of the UMI shelf's cards on one line; below, at most two, none past its card",
          not any(shelf_text_of.values()), {width: found for width, found in shelf_text_of.items() if found})
    # Tabbed to from the grippers' last card, each of the UMI shelf's six cards whole in the window (the review of
    # 2026-11-06: a browser scrolls a focused element into view only when none of it shows, so at 390 px the 1.5 mm and
    # the 3 mm cards had 192 of their 273 px past the window in their row; six shape cards since 2026-11-16, in a grid
    # since its review that day: no row to move, no arrow to Tab to).
    count = len(expected_rows[0][1])
    tabbed = {}
    for width, height in ((390, 844), (360, 740)):
        page.set_viewport_size({"width": width, "height": height}); page.wait_for_timeout(120)
        page.evaluate("() => scrollTo(0, 0)"); page.wait_for_timeout(80)
        page.focus(f"#gripper-{CARDED[-1]}")  # the grippers' last card
        tabbed[width] = []
        for _ in range(count):
            page.keyboard.press("Tab"); page.wait_for_timeout(100)
            tabbed[width].append(page.evaluate(CARD_IN_WINDOW))
    check("layout 390 and 360: each card of the UMI shelf, Tabbed to in its order, whole in the window's width",
          all(len(seen) == count and all(card and card["left"] >= 0 and card["right"] >= 0 for card in seen)
              and [card["card"] for card in seen] == expected_rows[0][1] for seen in tabbed.values()), tabbed)
    # And its focus ring inside the window with room under it, as the grippers' cards (the verification of 2026-11-06:
    # the first card had stopped flush with the window's bottom, its ring cut; scroll-margin 16 px leaves 12 px).
    check("layout 390 and 360: each card of the UMI shelf, Tabbed to, its focus ring inside the window above and below, 8 px or more",
          all(len(seen) == count and all(card and card["top"] >= 8 and card["bottom"] >= 8 for card in seen) for seen in tabbed.values()), tabbed)
    # The review of 2026-11-05: from 1280 px every shelf heading is one line (the UMI finger's, balanced, took two of
    # half the row at 1440 px), and the title's line ends on the gutter at every width from 735 px (right-aligned beside
    # the title: left-aligned, its balanced lines left a third of the hero empty from 1024 to 1280 px) with
    # "open-source" never split at its hyphen.
    headings = {}
    for width in (1440, 1280):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(120)
        headings[width] = [(name, lines) for name, _, lines in page.evaluate(SPACING) if lines != 1]
    check("layout: at 1440 and 1280 px both headings one line", headings == {1440: [], 1280: []}, headings)
    # The headings' lines (the user's decision of 2026-11-05; the UMI shelf's shapes since 2026-11-16): at no width does a
    # heading split a range ('1 to 3 mm') or the UMI shelf's 'straight to pointed'; at 900 px each is at most two lines,
    # its second line a phrase of its own (the first ends at a comma or a full stop: text-wrap pretty, the phrases kept
    # whole, so the UMI heading breaks as '... Six finger shapes, / straight to pointed.' there).
    lines, split = {}, []
    for width in WIDTHS + (1280,):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(80)
        lines[width] = dict(page.evaluate(HEADING_LINES))
        for name, rows in lines[width].items():
            text = " ".join(rows)
            whole = re.findall(r"\d[\d.]* to \d[\d.]* mm|straight to [a-z ]+(?=\.)", text)
            if not whole and name.startswith("shelf-") or any(not any(phrase in row for row in rows) for phrase in whole):
                split.append((width, name, rows))
    check("layout: at every width from 1440 to 320 px no heading splits its range or the UMI shelf's 'straight to pointed'", not split, split[:4])
    check("layout: at 900 px both headings at most two lines, a second line a phrase of its own (the UMI's '... Six finger shapes, / straight to pointed.')",
          all(len(rows) <= 2 and (len(rows) == 1 or rows[0].endswith((",", "."))) for rows in lines[900].values())
          and lines[900]["shelf-umi-finray"] in (["UMI Fin-Ray Gripper. Six finger shapes, straight to pointed."],
                                                 ["UMI Fin-Ray Gripper. Six finger shapes,", "straight to pointed."]),
          {name: rows for name, rows in lines[900].items() if len(rows) > 1})
    heroes = {}
    for width in (1440, 1366, 1280, 1200, 1150, 1100, 1024, 900, 820, 735, 600, 410, 390, 320):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(80)
        heroes[width] = page.evaluate(HERO)
    check("layout: the title's line ends on the gutter from 735 px (each row within 1 px of the content's edge), no step split",
          all(all(abs(end) <= 1 for end in hero["ends"]) for width, hero in heroes.items() if width >= 735)
          and all(hero["split"] is False for hero in heroes.values()),
          {width: hero for width, hero in heroes.items() if hero["split"] is not False or (width >= 735 and any(abs(end) > 1 for end in hero["ends"]))})
    # The user's request of 2026-11-15: "Pre-generated examples · Download Gerbers · Send to fab" as a small heading with
    # arrows: a list of the three steps, an arrow (hidden from screen readers) after each but the last, 21 px (19 px below
    # 1100 px, 17 px on a phone), one line from 1280 px, at most two from 735 px and three below.
    words = ["Pre\u2011generated examples", "Download Gerbers", "Send to fab"]
    check("layout: the title's line the three steps as a list, a grey arrow after the first two, 21 px (19 px below 1100 px, 17 px below 735 px)",
          all(hero["tag"] == "OL" and hero["words"] == words and [("\u2192" in arrow) for arrow in hero["arrows"]] == [True, True, False]
              and hero["size"] == ("21px" if width >= 1100 else "19px" if width >= 735 else "17px") for width, hero in heroes.items())
          and heroes[1440]["arrow"] in ("rgb(134, 134, 139)", "rgb(142, 142, 147)"),
          {width: {k: hero[k] for k in ("tag", "words", "arrows", "arrow", "size")} for width, hero in list(heroes.items())[:1] + list(heroes.items())[-1:]})
    check("layout: the title's line one line from 1280 px, at most two from 735 px, at most three below",
          all(hero["lines"] == 1 for width, hero in heroes.items() if width >= 1280)
          and all(hero["lines"] <= (2 if width >= 735 else 3) for width, hero in heroes.items()),
          {width: hero["lines"] for width, hero in heroes.items()})
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(80)
    check("layout: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()


def part_grid(browser):
    """The grid of 2026-11-06: each gripper's card opens its 2 mm sensor's page, whose Pitch reaches its pitches; every
    sensor's page reached by clicks alone; the window's X (the page's back link until 2026-11-15) back to its card where
    the grid was; the older addresses."""
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
    # Eight gripper cards since the Galaxea R1 Lite of 2026-11-17 (its review: the count here had stayed at seven).
    check("grid: each gripper's card opens its 2 mm sensor's page, its Pitch the gripper's four pitches",
          not wrong and len(opened) == len(CARDED), wrong[:2] or opened)
    # The UMI shelf (one card per finger shape since the user's request of 2026-11-16): the straight finger's card opens
    # its 2 mm page, whose Pitch reaches its four pitches; each shape's card its sensor's page, whose controls are the
    # card's axes of more than one choice (Tip width; the Short taper's Shape too; none on the Pointed tip's), which
    # reach every tip of the card.
    record = ENTRIES["parts"]["umi-finray"]
    page.click("#shelf-umi-finray .lib-card[data-part='umi-finray']"); page.wait_for_timeout(120)
    seen = page.evaluate(VIEW)
    radios = page.evaluate("() => [...document.querySelectorAll('input[name=\"libPitch\"]')].map(input => input.value)")
    straight = (seen["hash"], seen["checked"], radios, seen["detail"])
    for key in record["variants"]:
        page.click(f".lib-seg label:has(input[value='{key}'])"); page.wait_for_timeout(80)
        if page.evaluate(VIEW)["hash"] == f"#{key}":
            reached.add(key)
    page.go_back(); page.wait_for_timeout(120)
    check("grid: the UMI shelf's Straight finger opens its 2 mm sensor's page, its Pitch the finger's four pitches",
          straight == (f"#{record['default']}", record["default"], record["variants"], True), straight)
    shown, wrong = {}, []
    for name, family in ENTRIES["families"].items():
        for card in family["cards"]:
            page.click(f"#shelf-umi-finray .lib-card[data-card='{card['key']}']"); page.wait_for_timeout(120)
            seen = page.evaluate(VIEW)
            groups = page.evaluate("() => [...document.querySelectorAll('#libDetail .lib-seg legend')].map(n => n.textContent)")
            shown[card["key"]] = (seen["hash"], groups)
            if (seen["hash"], seen["detail"], groups) != (f"#{card['default']}", True, [axis["label"] for axis in card["axes"] if len(axis["choices"]) > 1]):
                wrong.append((card["key"], seen["hash"], groups))
            for key, identifier in card["grid"].items():
                for axis, value in zip(card["axes"], key.split("|")):
                    if len(axis["choices"]) > 1:
                        page.click(f"label:has(input[name='libAxis-{axis['key']}'][value='{value}'])"); page.wait_for_timeout(60)
                if page.evaluate(VIEW)["hash"] == f"#{identifier}" and page.evaluate(VIEW)["detail"]:
                    reached.add(identifier)
            page.go_back(); page.wait_for_timeout(120)
    check("grid: each shape's card opens its sensor's page with its axes of more than one choice (Short taper: Shape and Tip width; "
          "Convex arc, Trapezoid and Concave arc tips: Tip width; Pointed tip: none)", not wrong and len(shown) == 5, wrong or shown)
    check(f"grid: every sensor's page reached by clicks alone ({len(reached)} of {len(ENTRIES['variants'])}: the cards, the Pitch, Shape and Tip width)",
          reached == set(ENTRIES["variants"]), sorted(set(ENTRIES["variants"]) - reached)[:5])
    # The window's X (the page's back link until 2026-11-15): the grid where it was, its card focused (opened from the
    # grid, scrolled down).
    page.evaluate("() => scrollTo(0, 0)")
    page.click("#gripper-makermods-metal"); page.wait_for_timeout(150)
    page.go_back(); page.wait_for_timeout(150)
    # (The card in the window before the click, which then scrolls nothing: since the showcase's card of 2026-11-12 the
    # grippers' lower row is below a 900 px window's first screen.)
    page.evaluate("() => { document.getElementById('gripper-unitree-dex1').scrollIntoView({block: 'center'}); scrollBy(0, 40); }"); page.wait_for_timeout(60)
    before = page.evaluate(VIEW)
    page.click("#gripper-unitree-dex1"); page.wait_for_timeout(150)
    page.click("#libClose"); page.wait_for_timeout(150)
    back, focus = page.evaluate(VIEW), page.evaluate(FOCUS)
    check("grid: the window's X (to #gripper-<part>) leaves the grid where it was, its card focused",
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
    # The UMI finger's removed cards (2026-11-16: the 1, 1.5 and 3 mm cards, one card per shape since) and the Tapered
    # tips card's address: each opened anew shows its page in the window (its pitch checked, the address kept), the
    # Library under it; its X closes to the UMI shelf.
    removed = {}
    for identifier in [key for key in ENTRIES["parts"]["umi-finray"]["variants"] if key != ENTRIES["parts"]["umi-finray"]["default"]] + list(ENTRIES["families"]):
        open_library(page, f"#{identifier}")
        wait_until(page, "() => document.getElementById('libWindow').open", 10)
        seen = page.evaluate(VIEW)
        axes = page.evaluate("() => [...document.querySelectorAll('#libDetail .lib-seg input:checked')].map(n => n.value)")
        page.click("#libClose"); page.wait_for_timeout(150)
        removed[identifier] = (seen["hash"], seen["detail"], seen["checked"], axes, page.evaluate(VIEW)["hash"])
    family = next(iter(ENTRIES["families"].values()))
    check("grid: the removed cards' addresses (#umi-finray-1mm, -1.5mm, -3mm) and #umi-tapers opened anew show their pages, the address kept, "
          "their X the UMI shelf (#umi-tapers the 13.8 mm trapezoid's page)",
          all(seen[:3] == (f"#{key}", True, key) and seen[4] == "#shelf-umi-finray" for key, seen in removed.items() if key not in ENTRIES["families"])
          and all(seen[:2] == (f"#{key}", True) and seen[2] is None and seen[3] == ["13.8"] and seen[4] == "#shelf-umi-finray"
                  for key, seen in removed.items() if key in ENTRIES["families"])
          and family["default"] == "umi-trap-tip13.8-2mm" and len(removed) == 4, removed)
    check("grid: no console error (the older addresses)", not errors_of(page), errors_of(page)[:5])
    page.context.close()


def part_routes(browser):
    page = new_page(browser, 1440, 700)
    open_library(page, "#gripper-widowx-250")
    before = page.evaluate(VIEW)
    page.click("#gripper-widowx-250"); page.wait_for_timeout(200)
    shown = page.evaluate(VIEW)
    focus = page.evaluate(FOCUS)
    check("routes: a gripper's card opens its 2 mm sensor's page in the window at its top, the grid where it was under it, its title focused, "
          "Open in Gen by Surface at gen.html?part=<id>",
          shown["hash"] == "#widowx-250-2mm" and shown["detail"] and not shown["grid"] and shown["y"] == before["y"] and shown["top"] == 0
          and focus["id"] == "libDetailTitle"
          and shown["title"] == "WidowX 250" and shown["open"] == "gen.html?part=widowx-250-2mm" and shown["checked"] == "widowx-250-2mm"
          and shown["history"] == before["history"] + 1 and shown["tab"] == "WidowX 250, 2 mm · Library · FlexiTac-Gen", (shown, focus))
    page.click(".lib-seg label:has(input[value='widowx-250-1mm'])"); page.wait_for_timeout(150)
    fine = page.evaluate(VIEW)
    check("routes: its Pitch's 1 mm replaces the address (no history entry) and shows that sensor, the tab named after it",
          fine["hash"] == "#widowx-250-1mm" and fine["history"] == shown["history"] and fine["checked"] == "widowx-250-1mm"
          and fine["tab"] == "WidowX 250, 1 mm · Library · FlexiTac-Gen", fine)
    facts = page.inner_text(".lib-facts")
    check("routes: the page's facts (26 rows × 27 columns · 664 taxels, 1 mm · fill 0.50, the field, the tails, the build; no Reader row since "
          "2026-11-17)", "26 rows × 27 columns · 664 taxels" in facts and "1 mm · fill 0.50" in facts and "surface-26x27-7112a7cc7ced" in facts
          and "Reader" not in facts and "tail pin" not in facts, facts)
    # The user's request of 2026-11-17 ("所有的card加上一条：ordering and fabrication：放上instruction link；reading board
    # download"): under the facts, the guide in a new tab and the board its lines take (26 x 27: the 32 x 32), its bundle
    # and its notice (web/boards.js).
    order = page.evaluate(ORDER_ROWS)
    named = page.get_attribute(".lib-board a[download]", "aria-label")
    check("routes: under the facts, Ordering and fabrication (the FlexiTac fabrication guide, a new tab) and Reading board (26 x 27: "
          "'32 × 32 · ZIP, 93 kB · CC BY-NC 4.0', a no-break space before each dot, the bundle downloaded under its name and named in full to a "
          "screen reader, the notice in a new tab)",
          order == [["Ordering and fabrication", "FlexiTac fabrication guide", [[BOARDS_GUIDE, None, "_blank"]]],
                    ["Reading board", "32 × 32\u00a0· ZIP, 93 kB\u00a0· CC BY-NC 4.0", [[f"{BOARDS_FOLDER}FlexiTac_reading_board_32x32.zip", "FlexiTac_reading_board_32x32.zip", None],
                                                                                      [f"{BOARDS_FOLDER}NOTICE.md", None, "_blank"]]]]
          and named == "Reading board 32 × 32, ZIP, 93 kB", (order, named))
    # (The page's pills: the grid's own, the showcase's Details since 2026-11-15, are under the window.)
    widths = page.evaluate("() => [document.querySelector('.lib-open'), ...document.querySelectorAll('#libDetail .lib-pill')].map(n => n.getBoundingClientRect().width)")
    check("routes: Open in Gen by Surface, the primary action, at least as wide as each download pill (1440 px)",
          len(widths) == 3 and all(widths[0] >= width - 0.5 for width in widths[1:]), widths)
    page.screenshot(path=f"{SHOTS}/library_detail_1440.png")
    # The second review of 2026-11-05: from 900 to 1279 px a sensor's page splits evenly, so at 900 px each fact is on
    # one line and at 1100 px the two download pills are side by side (at 7 to 5 the facts wrapped and the pills stacked);
    # in the window (the review of 2026-11-15) evenly at 1280 and 1440 px too, each fact on one line and the pills side
    # by side there (at 7 to 5 the facts' column was 440 px at 1440 px, the pills stacked).
    narrow = {}
    for width in (900, 1100, 1280, 1440):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(150)
        narrow[width] = page.evaluate("""() => { const lines = node => { const range = document.createRange(); range.selectNodeContents(node);
            return new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top))).size; };
          const columns = [...document.querySelector('.lib-detail-body').children].map(n => Math.round(n.getBoundingClientRect().width));
          const left = node => Math.round(node.getBoundingClientRect().left); const body = document.getElementById('libWindowBody');
          return {columns, facts: [...document.querySelectorAll('.lib-facts dd')].map(lines), pills: [...document.querySelectorAll('#libDetail .lib-pill')].map(n => Math.round(n.getBoundingClientRect().top)),
                  order: [...document.querySelectorAll('.lib-order dd')].map(lines), pieces: [...document.querySelectorAll('.lib-board > *')].map(lines),
                  values: [...new Set([...document.querySelectorAll('.lib-facts dd')].map(left))], ordered: [...new Set([...document.querySelectorAll('.lib-order dd')].map(left))],
                  hairline: getComputedStyle(document.querySelector('.lib-facts')).borderBottomWidth, over: body.scrollHeight - body.clientHeight}; }""")
        page.screenshot(path=f"{SHOTS}/library_detail_{width}.png")
    # The review of 2026-11-05: below 900 px Open in Gen by Surface and the downloads come before the facts, so on a
    # 390 x 844 phone Open is in the first screen; from 900 px the facts stay before it.
    order = {}
    for width, height in ((390, 844), (899, 900), (900, 900)):
        page.set_viewport_size({"width": width, "height": height}); page.wait_for_timeout(150)
        page.evaluate(WINDOW_TOP)
        order[width] = page.evaluate("""() => { const top = selector => Math.round(document.querySelector(selector).getBoundingClientRect().top);
          return {open: top('.lib-open'), bottom: Math.round(document.querySelector('.lib-open').getBoundingClientRect().bottom), downloads: top('.lib-downloads'),
                  facts: top('.lib-facts'), pitch: top('.lib-seg'), screen: innerHeight}; }""")
        if width == 390:
            page.screenshot(path=f"{SHOTS}/library_detail_390.png")
    check("routes: below 900 px Open and the downloads come right after the pitch, before the facts (Open in a 390 x 844 phone's first screen); "
          "from 900 px the facts before Open", all(order[width]["pitch"] < order[width]["open"] < order[width]["downloads"] < order[width]["facts"] for width in (390, 899))
          and order[390]["bottom"] <= order[390]["screen"] and order[900]["facts"] < order[900]["open"], order)
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(150)
    check("routes: a sensor's page in the window splits evenly from 900 px: each fact on one line at 900, 1280 and 1440 px, the two Gerber pills "
          "side by side at 1100, 1280 and 1440 px",
          all(len(view["columns"]) == 2 and abs(view["columns"][0] - view["columns"][1]) <= 1 for view in narrow.values())
          and all(count == 1 for width in (900, 1280, 1440) for count in narrow[width]["facts"])
          and all(len(narrow[width]["pills"]) == 2 and narrow[width]["pills"][0] == narrow[width]["pills"][1] for width in (1100, 1280, 1440)), narrow)
    # The ordering's two rows (2026-11-17): one line each at 1280 and 1440 px (their labels' column at most 40 %: at 900 px
    # "Ordering and fabrication" takes two lines and the board's value may), the board's pieces never split.
    check("routes: Ordering and fabrication and Reading board one line each at 1280 and 1440 px; the board's size, ZIP and licence never split "
          "(900 to 1440 px)", all(narrow[width]["order"] == [1, 1] for width in (1280, 1440))
          and all(len(narrow[width]["pieces"]) == 3 and set(narrow[width]["pieces"]) == {1} for width in narrow), narrow)
    # The review of 2026-11-17: from 1200 px the facts and the two rows one table (one values' column, no hairline between),
    # so a plain sensor's window fits 1440 x 900 again (the two rows for the Reader row: one row taller, 747 px of 756);
    # below, the facts' 72 px labels and the rows' own column under a hairline, as before.
    check("routes: from 1200 px the facts and the ordering's rows one table (one values' column, no hairline between them), the 1440 x 900 window "
          "with no scroll; at 900 and 1100 px the rows' own column under a hairline",
          all(len(narrow[width]["values"]) == 1 and narrow[width]["ordered"] == narrow[width]["values"] and narrow[width]["hairline"] == "0px" for width in (1280, 1440))
          and narrow[1440]["over"] == 0
          and all(narrow[width]["ordered"][0] > narrow[width]["values"][0] and narrow[width]["hairline"] == "1px" for width in (900, 1100)), narrow)
    # A phone's narrowest windows (the review of 2026-11-17: at 320 to 326 px the second dot had started a line).
    dots = {}
    for width in (320, 322, 324, 326, 390):
        page.set_viewport_size({"width": width, "height": 800}); page.wait_for_timeout(150)
        dots[width] = page.evaluate(BOARD_DOTS)
    check("routes: from 320 to 390 px each of the board's dots on the line of the piece before it (never starting a line)",
          all(len(seen) == 2 and all(text == "\u00a0· " and top == before for text, top, before in seen) for seen in dots.values()), dots)
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(150)
    page.click(".lib-seg label:has(input[value='widowx-250-2mm'])"); page.wait_for_timeout(150)
    pitched = page.evaluate(VIEW)
    check("routes: another pitch replaces the address (no history entry) and shows that sensor, its segment focused",
          pitched["hash"] == "#widowx-250-2mm" and pitched["history"] == shown["history"] and pitched["checked"] == "widowx-250-2mm"
          and pitched["open"] == "gen.html?part=widowx-250-2mm" and page.evaluate("() => document.activeElement.value") == "widowx-250-2mm", pitched)
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
    # another card; since 2026-11-15 the window's X, which closes to the back link's place, going back over the window's
    # entry since its review): the WidowX 250 card, its X, the MakerMods card, Back (the grid where it was, MakerMods
    # focused), Forward (the MakerMods window), the ARX X5 card's place typed over it, Back (the MakerMods window, reached
    # by Back), its X (the MakerMods card focused, in view, not the ARX X5's), Forward and Back (the grid where it was,
    # MakerMods focused).
    page = new_page(browser, 1440, 700)
    open_library(page)
    steps = {}
    page.click("#gripper-widowx-250"); page.wait_for_timeout(150)
    page.click("#libClose"); page.wait_for_timeout(150)
    steps["its X"] = (page.evaluate(VIEW)["hash"], page.evaluate(FOCUS)["id"])
    page.locator("#gripper-makermods-metal").scroll_into_view_if_needed(); page.wait_for_timeout(60)
    page.evaluate("() => scrollBy(0, 40)"); page.wait_for_timeout(60)
    grid_y = page.evaluate(VIEW)["y"]
    page.click("#gripper-makermods-metal"); page.wait_for_timeout(150)
    page.go_back(); page.wait_for_timeout(150)
    steps["Back to the grid"] = (page.evaluate(VIEW)["hash"], page.evaluate(FOCUS)["id"], page.evaluate(VIEW)["y"] - grid_y)
    page.go_forward(); page.wait_for_timeout(150)
    page.evaluate("() => { location.hash = '#gripper-arx-x5'; }"); page.wait_for_timeout(150)
    page.go_back(); page.wait_for_timeout(150)
    steps["Back to MakerMods"] = (page.evaluate(VIEW)["hash"], page.evaluate(VIEW)["detail"])
    page.click("#libClose"); page.wait_for_timeout(150)
    sight = page.evaluate(IN_VIEW, "gripper-makermods-metal")
    steps["the MakerMods X"] = (page.evaluate(VIEW)["hash"], page.evaluate(FOCUS)["id"], sight["inside"])
    page.evaluate("() => scrollBy(0, 30)"); page.wait_for_timeout(60)
    left_y = page.evaluate(VIEW)["y"]
    page.go_forward(); page.wait_for_timeout(150)
    page.go_back(); page.wait_for_timeout(150)
    steps["Forward and Back"] = (page.evaluate(VIEW)["hash"], page.evaluate(FOCUS)["id"], page.evaluate(VIEW)["y"] - left_y)
    check("routes: Back and Forward put the grid back where it was with the card clicked focused; a window's X its own card, also a window reached by Back",
          steps == {"its X": ("#gripper-widowx-250", "gripper-widowx-250"), "Back to the grid": ("#gripper-widowx-250", "gripper-makermods-metal", 0),
                    "Back to MakerMods": ("#makermods-metal-2mm", True), "the MakerMods X": ("#gripper-makermods-metal", "gripper-makermods-metal", True),
                    "Forward and Back": ("#gripper-makermods-metal", "gripper-makermods-metal", 0)}, steps)
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
    page.click("#libClose"); page.wait_for_timeout(200)
    sight = page.evaluate(IN_VIEW, "gripper-widowx-250")
    check("routes: the X of a window opened directly goes to its card, in view and focused",
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
    routes_opened_directly(browser)


# Every frame from the document's creation (a requestAnimationFrame callback runs before each paint): whether the grid's
# title or the footer is rendered, whether a sensor's page is shown and whether <html> is marked data-lib-place.
FRAMES = """(() => { const frames = []; Object.defineProperty(window, '__libFrames', {value: frames});
  const rendered = node => Boolean(node) && node.getClientRects().length > 0;
  const step = () => { const detail = document.getElementById('libWindow');
    frames.push({hero: rendered(document.getElementById('libHero')), footer: rendered(document.querySelector('.lib-footer')),
                 detail: Boolean(detail) && detail.open, marked: document.documentElement.hasAttribute('data-lib-place')});
    if (frames.length < 3000) requestAnimationFrame(step); };
  requestAnimationFrame(step); })();"""
# The page as it settled: the grid's title, the footer, the status (rendered), and the mark.
SETTLED = """() => ({hero: document.getElementById('libHero').getClientRects().length > 0, footer: document.querySelector('.lib-footer').getClientRects().length > 0,
  status: document.getElementById('libStatus').textContent, detail: document.getElementById('libWindow').open,
  marked: document.documentElement.hasAttribute('data-lib-place'), hash: location.hash})"""
LATE_S = {"library.js": 0.8, "entries.json": 0.4}


def late(seconds):
    # A route handler answering ``seconds`` late (the browser paints meanwhile), then as it would have (the next route,
    # ROUTES' or the server's).
    def handler(route):
        time.sleep(seconds)
        route.fallback()
    return handler


def open_late(browser, fragment, width, height, entries=None):
    """The Library (./)``fragment`` opened anew, library.js and entries.json late (LATE_S; ``entries``: entries.json's status
    instead): its frames (FRAMES) and the page as it settled (SETTLED)."""
    page = new_page(browser, width, height)
    page.add_init_script(FRAMES)
    page.route("**/static/library.js", late(LATE_S["library.js"]))
    if entries is None:
        page.route("**/static/library/entries.json", late(LATE_S["entries.json"]))
    else:
        page.route("**/static/library/entries.json", lambda route: route.fulfill(status=entries, content_type="text/plain", body="not here"))
    page.goto(SITE["base"] + fragment)
    wait_until(page, READY, 30)
    page.wait_for_timeout(200)
    frames, settled = page.evaluate("() => window.__libFrames.slice()"), page.evaluate(SETTLED)
    errors = errors_of(page) if entries is None else [entry for entry in errors_of(page) if "entries.json" not in entry[1] and "status of 500" not in entry[1]]
    page.context.close()
    return frames, settled, errors


def routes_opened_directly(browser):
    """The page opened at an address of its own (the reviews of 2026-11-06: a shared link or a reload had painted the
    grid's title and tagline over the footer before the sensor's page; library.js's hiding of them, run late, had left
    the footer hidden unchecked): with library.js 0.8 s and entries.json 0.4 s late (LATE_S), so the page paints before
    either arrives, at 1440 x 900 and 390 x 844, a sensor's page shows no frame of the grid's title and no frame of the
    footer before its window opens, then (since the window of 2026-11-15) the Library, its title and footer, under it; #gripper-<part> and #shelf-umi-finray show the grid's title and the footer;
    the Library alone (./) paints the grid's title before library.js arrives, as before (no mark); entries.json failing (500)
    on a sensor's address shows the title, the footer and the status; Gen by Surface is never marked."""
    for width, height in ((1440, 900), (390, 844)):
        frames, settled, errors = open_late(browser, "#widowx-250-2mm", width, height)
        before = [frame for frame in frames if not frame["detail"]]
        check(f"routes {width}: a sensor's page opened directly paints no frame of the grid's title nor of the footer before its window opens, "
              f"then the Library under the window ({len(before)} frames before it, library.js {LATE_S['library.js']} s late)",
              len(before) >= 10 and not any(frame["hero"] or frame["footer"] for frame in before)
              and before[0]["marked"] and settled == {"hero": True, "footer": True, "status": "", "detail": True, "marked": False, "hash": "#widowx-250-2mm"}
              and not errors, (len(frames), len(before), [frame for frame in before if frame["hero"] or frame["footer"]][:3], settled, errors[:3]))
        for fragment in ("#gripper-arx-x5", "#shelf-umi-finray"):
            frames, settled, errors = open_late(browser, fragment, width, height)
            check(f"routes {width}: {fragment} opened directly shows the grid's title and the footer once it is routed",
                  frames and frames[0]["marked"] and settled == {"hero": True, "footer": True, "status": "", "detail": False, "marked": False, "hash": fragment}
                  and not errors, (settled, errors[:3]))
    frames, settled, errors = open_late(browser, "", 1440, 900)
    early = [frame for frame in frames[:20] if frame["hero"] and frame["footer"]]
    check("routes: the Library alone (./) paints the grid's title and the footer before library.js arrives, as before (never marked)",
          early and not any(frame["marked"] for frame in frames) and settled["hero"] and settled["footer"] and not errors, (frames[:3], settled, errors[:3]))
    frames, settled, errors = open_late(browser, "#widowx-250-2mm", 390, 844, entries=500)
    check("routes: a sensor's address with entries.json failing (500) shows the grid's title, the footer and the status",
          settled["hero"] and settled["footer"] and settled["status"].startswith("The library could not be loaded (HTTP 500).") and not settled["marked"]
          and not errors, (settled, errors[:3]))
    page = new_page(browser)
    page.goto(SITE["base"] + "gen.html#rect", wait_until="domcontentloaded")
    check("routes: Gen by Surface opened at an address (#rect) is never marked data-lib-place",
          page.evaluate("() => document.documentElement.hasAttribute('data-lib-place')") is False)
    page.context.close()


# The first page (the user's decisions of 2026-11-15 and 2026-11-16: "我觉得之后可以让lib作为第一次点击进入时候使用的界面",
# "是的 be first page"): the Library at ./, the generator at gen.html, the addresses of before forwarded (rp.FORWARDS).
def part_first_page(browser):
    """The first page (2026-11-16), on app.py or the built site (--site): every address of rp.FORWARDS opened after an
    earlier page, its target held 0.6 s: the generator's addresses of before (./?part=<id>, ./#rect, ./#cad, ?sample,
    ?debug, its anchors, at ./ and ./index.html) at gen.html and library.html's at ./ (#<id> the Library with that
    window), their query and hash kept, with no history entry of their own (Back the earlier page) and nothing of the
    old address's page painted; the Library's own addresses (its sensors, a part, a family, its places, the showcase,
    ?probe) staying, painted, unmarked.  Then the first page itself: ./ the Library (its title, its grid, its header's
    Rectangular at gen.html#rect, Gen by Surface at gen.html, the Library link ./ the current page), its mode links and
    a sensor's Open in Gen by Surface going to the generator in this tab (gen.html, gen.html#rect, gen.html?part=<id>,
    the generator's title and mode), Back coming back to the Library (the window again for Open's).  Since the review of
    2026-11-16: an address of before reached by its hash over the open Library (./#rect typed over ./, #cad over a
    sensor's window, #drc-row over ./?probe) going on to gen.html as at a load, and, on the built site, the Library's
    header counts refreshed from GitHub's API (answered here) and kept for the tab."""
    seen = forwarding(browser, SITE["base"])
    for address, target in FORWARDS:
        s = seen[address]
        if target is None:
            check(f"first page: {address or './'} is the Library's own: it stays, painted ({s['frames']} frames, {s['shown']} things shown), "
                  "unmarked, no history entry of its own, Back the earlier page",
                  s["url"] == s["final"] and s["frames"] > 0 and s["shown"] and s["marks"] == ["None"] and s["added"] == 1 and s["back"]
                  and s["title"].endswith("Library · FlexiTac-Gen"), s)
        else:
            check(f"first page: {address} goes to ./{target} (its query and hash kept) with no history entry of its own, Back the earlier "
                  f"page, and nothing of its own page painted ({s['frames']} frames)",
                  s["url"] == s["final"] and s["added"] == 1 and s["back"] and not s["shown"]
                  and s["title"] == ("FlexiTac-Gen" if target.startswith("gen.html") else s["title"]) and s["title"].endswith("FlexiTac-Gen"), s)
    page = new_page(browser)
    open_library(page)
    first = page.evaluate("""() => ({title: document.title, cards: document.querySelectorAll('.lib-card').length,
        modes: [...document.querySelectorAll('.mode-links a')].map(a => [a.textContent.trim(), a.getAttribute('href'), a.target]),
        library: (a => [a.getAttribute('href'), a.getAttribute('aria-current'), a.target])(document.querySelector('.masthead-library'))})""")
    check("first page: ./ is the Library (its title, its grid), its header's Rectangular at gen.html#rect and Gen by Surface at gen.html in "
          "this tab, its Library link ./ the current page",
          first["title"] == "Library · FlexiTac-Gen" and first["cards"] >= 12
          and first["modes"] == [["Rectangular", "gen.html#rect", ""], ["Gen by Surface", "gen.html", ""]] and first["library"] == ["./", "page", ""], first)
    went = []
    for name, expected, mode in (("Gen by Surface", "gen.html", "cad"), ("Rectangular", "gen.html#rect", "rect")):
        with page.expect_navigation():
            page.click(f".mode-links a:has-text('{name}')")
        page.wait_for_load_state("domcontentloaded")
        wait_until(page, "() => Boolean(document.body && document.body.dataset.mode)", 60)
        went.append([name, page.url == SITE["base"] + expected, page.title(), page.evaluate("() => document.body.dataset.mode") == mode])
        page.go_back()
        wait_until(page, READY, 30)
        went[-1].append(page.url == SITE["base"])
    check("first page: the Library's Gen by Surface and Rectangular open the generator in this tab at gen.html and gen.html#rect, in that mode; "
          "Back comes back to the Library", all(row[1:] == [True, "FlexiTac-Gen", True, True] for row in went), went)
    page.click('.lib-card[href="#widowx-250-2mm"], #gripper-widowx-250')
    wait_until(page, "() => document.getElementById('libWindow').open && document.querySelector('.lib-open')", 30)
    href = page.evaluate("() => document.querySelector('.lib-open').getAttribute('href')")
    with page.expect_navigation():
        page.click(".lib-open")
    page.wait_for_load_state("domcontentloaded")
    opened = [page.url, page.title()]
    page.go_back()
    wait_until(page, "() => document.getElementById('libWindow').open", 30)
    back = [page.url, page.title()]
    check("first page: a sensor's Open in Gen by Surface goes to gen.html?part=<id> in this tab; Back comes back to the Library with its window",
          href == "gen.html?part=widowx-250-2mm" and opened == [SITE["base"] + href, "FlexiTac-Gen"]
          and back == [SITE["base"] + "#widowx-250-2mm", "WidowX 250, 2 mm · Library · FlexiTac-Gen"], (href, opened, back))
    check("first page: no console error", not errors_of(page), errors_of(page)[:3])
    page.context.close()
    # The Library already open (the review of 2026-11-16): an address of before reached by its hash alone (typed over
    # it, an old bookmark or a link followed from it: a navigation within the page, which runs no script again) goes on
    # to gen.html as at a load, its query kept, the hash's one entry replaced (no other), the Library never saying "No
    # sensor in the library is named rect."; Back the Library where it was, shown.
    went = []
    for start, then, target in (("", "#rect", "gen.html#rect"), ("#widowx-250-2mm", "#cad", "gen.html#cad"), ("?probe", "#drc-row", "gen.html?probe#drc-row")):
        page = new_page(browser)
        notes = []
        page.on("console", lambda message: notes.append(message.text[9:]) if message.text.startswith("fpc-note ") else None)
        open_library(page, start)
        if start.startswith("#"):
            wait_until(page, "() => document.getElementById('libWindow').open", 30)
        length = page.evaluate("() => history.length")
        page.evaluate("""hash => { const note = document.getElementById('libNote');
            new MutationObserver(() => console.debug('fpc-note ' + note.textContent)).observe(note, {childList: true, characterData: true, subtree: true});
            location.hash = hash; }""", then)
        try:
            page.wait_for_url(SITE["base"] + target, timeout=30_000)
            page.wait_for_load_state("domcontentloaded")
        except Exception:  # noqa: BLE001 - reported below as where it ended
            pass
        row = [start or "./", then, page.url == SITE["base"] + target, page.evaluate("() => history.length") - length, page.title(), notes]
        page.go_back(wait_until="commit")
        page.wait_for_load_state("domcontentloaded")
        wait_until(page, READY, 30)
        page.wait_for_timeout(200)
        row += [page.url == SITE["base"] + start, page.evaluate("() => getComputedStyle(document.documentElement).visibility"),
                page.evaluate("() => document.getElementById('libNote').textContent"),
                page.evaluate("() => document.getElementById('libWindow').open") == start.startswith("#"), errors_of(page)]
        went.append(row)
        page.context.close()
    check("first page: an address of before reached by its hash over the open Library (./#rect, #cad over a sensor's window, #drc-row over "
          "./?probe) goes on to gen.html, the query kept, one history entry (the hash's own), no note of an unknown sensor; Back the Library "
          "where it was, shown", all(row[2:6] == [True, 1, "FlexiTac-Gen", []] and row[6:] == [True, "visible", "", True, []] for row in went), went)
    if SITE["root"] is not None:
        # The built site (the review of 2026-11-16): the Library, the first page, refreshes the header's star and fork
        # counts from GitHub's API as the generator does (web/counts.js; answered here, answer_github), kept for the tab.
        asked = len(GITHUB_ASKED)
        page = new_page(browser)
        open_library(page)
        wait_until(page, "() => !document.querySelector('[data-gh-stats]').hidden", 15)
        library = page.evaluate(CARD)
        with page.expect_navigation():
            page.click(".mode-links a:has-text('Gen by Surface')")
        page.wait_for_load_state("domcontentloaded")
        wait_until(page, "() => !document.querySelector('[data-gh-stats]').hidden", 15)
        generator = page.evaluate(CARD)
        check("first page: on the built site the Library (./) shows the header's counts from GitHub's API (1.2k, 56), asked once; the generator "
              "in the same tab shows them without asking again", library == GITHUB_CARD and generator == GITHUB_CARD and GITHUB_ASKED[asked:] == [SITE["base"]],
              (library, generator, GITHUB_ASKED[asked:]))
        page.context.close()


def part_first_screen(browser):
    """The user's decision of 2026-11-05 (the picture may be squashed): below 900 px a sensor's page is one column, its
    picture above Open, and that picture is 3:1, not 16:10, so Open is in a phone's first screen.  Every sensor's page
    and the Tapered tips page (#umi-tapers) at each phone size of PHONES, opened at the window's top, in both CASES:
    with pictures (the picture loaded, and its Exploded | Assembled control in the frame, above Open) and with none; the
    samples (from 900 px, and with the 3D view) the Short taper's page, the tallest (SHORT_TAPER)."""
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
            for key in keys if width < 900 else ("widowx-250-1mm", SHORT_TAPER):
                page.evaluate("(key) => { location.hash = '#' + key; }", key)
                wait_until(page, "(key) => location.hash === '#' + key && document.getElementById('libWindow').open", 10, key)
                wait_until(page, PICTURE_SETTLED, 10)
                page.evaluate(WINDOW_TOP)
                found[(width, height, key)] = page.evaluate(FIRST_SCREEN)
            for key in ("trossen-widowx-ai-2mm", SHORT_TAPER):
                if (width, height) in PHONES:
                    page.evaluate("(key) => { location.hash = '#' + key; }", key); page.wait_for_timeout(100)
                    wait_until(page, PICTURE_SETTLED, 10)
                    page.evaluate(WINDOW_TOP)
                    if view:
                        before = page.evaluate(FIRST_SCREEN)
                        drawn = library_shots.poll(page, LIVE_SHOWN, None, 120)
                        page.evaluate(WINDOW_TOP)
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
        # Since the window of 2026-11-15 (a sheet: no header above the page, which had taken 239 px of these phones' first
        # screen) Open is in the first screen at 375 x 667, 360 x 740 and 320 x 640 on every page too (the tapered tips'
        # had been below it at all three, a gripper's two-line title's at the first and the last); at 320 x 568 not on
        # the tapered tips' (a three-line title and two controls: the Short taper's since 2026-11-16): its place is
        # reported there, as at every phone size, the lowest Open's bottom on a gripper's page and on a tapered tip's, and
        # how many pages have it in the window.
        check(f"first screen ({label}) 375 x 667, 360 x 740 and 320 x 640 (the window a sheet): Open's bottom in the window on every page ({len(keys)})",
              not any(below(size, keys) for size in ((375, 667), (360, 740), (320, 640))),
              {f"{width}x{height}": (below((width, height), keys)[:4], lowest((width, height), keys)) for width, height in ((375, 667), (360, 740), (320, 640))})
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
                    and all(abs(a - b) <= 0.5 for a, b in zip(drawing, seen["shot"])) and seen["fitted"] == ["contain", "50% 50%"] and seen["overflow"] <= 0
                    and seen["inner"] <= 0):
                wrong.append(((width, height), key, seen))
        what = ("the picture loaded, contained and centred, and its Exploded | Assembled control under it in the frame" if case == "pictures"
                else "its field drawn to meet the box (centred) and an image in it contained and centred, no view control")
        check(f"first screen ({label}): below 900 px a sensor's picture 3:1 above Open (from 900 px 16:10 beside it), shown, {what}; no sideways scroll "
              "(the page's nor the window's)",
              not wrong, wrong[:2] or {"aspects": shapes})
        if view:
            moved = {size: (drawn, [name for name in ("open", "frame", "shot", "drawing") if any(abs(a - b) > 0.5 for a, b in zip(
                         before[name][-4:], after[name][-4:]))], after["live"], after["shot"])
                     for size, (drawn, before, after) in lives.items()}
            check(f"first screen ({label}): at each phone the 3D view drawn over the picture (Trossen WidowX AI's 2 mm, the Short taper's), "
                  "nothing moved (Open, the frame, the slot, the picture), the view's box the slot's",
                  len(lives) == 2 * len(PHONES) and all(drawn and not names and live is not None and all(abs(a - b) <= 0.5 for a, b in zip(live, shot))
                                                        for drawn, names, live, shot in moved.values()),
                  {size: value for size, value in moved.items() if not value[0] or value[1] or value[2] is None} or len(lives))
        check(f"first screen ({label}): no console error", not any(errors.values()), {size: found for size, found in errors.items() if found})


# Every visible picture slot: its owner (a card's variant or family, the showcase's card, or the sensor's page), its box and
# background, its children, the placeholder's drawing (its field and its lines), and an image's attributes, computed fit,
# box within the slot and whether it has loaded (or broken: loaded with no picture).
SLOTS = """() => [...document.querySelectorAll('.lib-shot')].filter(shot => shot.checkVisibility()).map(shot => {
  const owner = shot.closest('.lib-card'); const img = shot.querySelector('img'); const r = shot.getBoundingClientRect();
  const round = v => Math.round(v * 10) / 10;
  return {owner: owner ? (owner.classList.contains('lib-showcase') ? 'showcase' : owner.dataset.variant || 'family:' + owner.dataset.family) : 'detail',
    shelf: shot.closest('.lib-shelf') !== null, tip: shot.classList.contains('lib-shot-tip'), clips: getComputedStyle(shot).overflow, box: [round(r.width), round(r.height)], background: getComputedStyle(shot).backgroundColor, children: [...shot.children].map(n => n.tagName.toLowerCase()),
    field: shot.querySelector('svg .lib-field') !== null, lines: shot.querySelectorAll('svg .lib-lines line').length,
    img: img && {src: img.getAttribute('src'), alt: img.getAttribute('alt'), loading: img.getAttribute('loading'), decoding: img.getAttribute('decoding'),
      size: [img.getAttribute('width'), img.getAttribute('height')], fit: [getComputedStyle(img).objectFit, getComputedStyle(img).objectPosition],
      box: (b => [round(b.left - r.left), round(b.top - r.top), round(b.width), round(b.height)])(img.getBoundingClientRect()),
      transform: [getComputedStyle(img).transform, getComputedStyle(img).transformOrigin],
      loaded: img.complete && img.naturalWidth > 0, broken: img.complete && img.naturalWidth === 0, natural: [img.naturalWidth, img.naturalHeight]}}; })"""
# Every card's, shelf's and section's box in the document (the pictures move none of them as they arrive).
GEOMETRY = """() => [...document.querySelectorAll('.lib-card, .lib-shelf, .lib-section, .lib-footer')].map(n => { const r = n.getBoundingClientRect();
  return [Math.round(r.left * 10) / 10, Math.round((r.top + scrollY) * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; })"""
# A sensor's page's picture and its view control: the picture's attributes and state, the placeholder's drawing, the boxes
# of the slot, the frame and the control's track, the control's legend, radios, colours, segments and transitions, and
# the focus, the address, the history's length and the running animations (but the 3D view's drag hint's, the page's one
# motion of its own since 2026-11-15: part_view checks it).
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
    animations: document.getAnimations().filter(a => !a.effect?.target?.closest?.('.lib-drag')).length, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth}; }"""
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
    """None when a grid slot shows its sensor's Exploded card picture as the contract and library.css have it, filling its
    light box (every card, the UMI shelf's too since the user's request of 2026-11-16; from the lead's review that day
    until then its Assembled picture framed on the fingertip), else why not."""
    key, alt = card_owner(slot["owner"])
    image = IMAGES[key]
    if image is None:  # a sensor of this tree without a picture yet
        return placeholder_wrong(slot)
    img = slot["img"] or {}
    size, src = list(CARD_SIZE), f"static/library/{image['exploded']['card']}"
    want = {"src": src, "alt": image["alt"] if alt else "", "loading": "lazy", "decoding": "async",
            "size": [str(size[0]), str(size[1])], "fit": ["contain", "50% 50%"], "loaded": True, "natural": size}
    got = {name: img.get(name) for name in want}
    width, height = slot["box"]
    filled = img.get("box") and all(abs(a - b) <= 1 for a, b in zip(img["box"], [0, 0, width, height]))
    return None if got == want and slot["children"] == ["img"] and filled and not slot.get("tip") else (
        slot["owner"], {k: v for k, v in got.items() if v != want[k]}, img.get("box"), slot.get("tip"))


def load_grid(page):
    """Every section brought into sight, its end then its start, then back to the top: every lazy picture asked for (each
    shelf's row was scrolled to its end too while the UMI shelf was one, until 2026-11-16)."""
    page.evaluate("""() => { for (const shelf of document.querySelectorAll('.lib-section, .lib-shelf')) { shelf.scrollIntoView({block: 'end'});
        shelf.scrollIntoView({block: 'start'}); } }""")
    page.wait_for_timeout(150)
    page.evaluate("""() => { for (const shelf of [...document.querySelectorAll('.lib-section, .lib-shelf')].reverse()) shelf.scrollIntoView({block: 'center'});
        scrollTo(0, 0); }""")
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
    # (all of them at 1440 px: the page is short) within the first screen's budget; then, once every section has been in
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
    # The showcase's large card (2026-11-12) is the grid's first slot, a picture of its own kind: its own card file at its
    # own size, loaded at once (showcase_checks part_page has its checks); the sensors' cards after it are as they were.
    hero = [slot for slot in slots if slot["owner"] == "showcase"]
    slots = [slot for slot in slots if slot["owner"] != "showcase"]
    check(f"pictures{tag}: the showcase's card is the grid's one slot that is no sensor's, its picture loaded in the same light box",
          len(hero) == 1 and (hero[0]["img"] or {}).get("loaded") and hero[0]["children"] == ["img"] and hero[0]["background"] == "rgb(245, 245, 247)", hero[:1])
    wrong = [result for result in map(card_picture_wrong, slots) if result is not None]
    owners = [slot["owner"] for slot in slots]
    shelf = [card_owner(item["owner"])[0] for item in slots if item["shelf"]]
    check(f"pictures{tag}: every card (the grippers' {len(CARDED)}, each its 2 mm sensor's, the UMI shelf's six shapes, each its sensor's: "
          f"{len(GRID_CARDS)}) shows its sensor's Exploded card file (640 x 400) filling its light box, the UMI shelf's as the grippers' (the user's "
          "request of 2026-11-16; their Assembled picture framed on the fingertip from the review that day), contained and centred, lazy, "
          "decoded async, its width and height set, its alt the entry's",
          not wrong and [card_owner(owner)[0] for owner in owners] == GRID_CARDS and len(GRID_CARDS) == len(CARDED) + 6 and shelf == GRID_CARDS[len(CARDED):],
          wrong[:3] or owners)
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
    check(f"pictures{tag}: the control is grey (its chosen view a white thumb on the fill), never blue, nothing green, no transition or animation "
          "(but the drag hint's)",
          view.get("thumb") == "rgb(255, 255, 255)" and view.get("fill") == "rgba(118, 118, 128, 0.12)" and view.get("transitions") == []
          and seen["animations"] == 0 and fills["blue"] == blues(page, "a.lib-open") and fills["green"] == [], (view, fills))
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
    # The Short taper's page (its Shape and Tip width; the Tapered tips page until 2026-11-16): opened Exploded, the view
    # its card shows as a gripper's (the user's request of 2026-11-16; Assembled from the review that day until then);
    # each control swaps the picture with the sensor, the view kept.
    open_library(page, f"#{SHORT_TAPER}")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES[SHORT_TAPER]["exploded"]["src"])
    first = page.evaluate(DETAIL_PICTURE)
    page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_tapers_1440.png")
    page.click("label:has(input[name='libAxis-shape'][value='convex'])")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["umi-short-convex-tip9.8-2mm"]["exploded"]["src"])
    page.click("#libDetail .lib-view label:has(input[value='assembled'])")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["umi-short-convex-tip9.8-2mm"]["assembled"]["src"])
    page.click("label:has(input[name='libAxis-tip_mm'][value='5.8'])")
    wait_until(page, DETAIL_SHOWS, 10, IMAGES["umi-short-convex-tip5.8-2mm"]["assembled"]["src"])
    check(f"pictures{tag}: the Short taper's page opens Exploded (its card's view, as a gripper's); Shape and Tip width show the chosen tip's "
          "picture (the convex 9.8 mm Exploded, then Assembled, then 5.8 mm Assembled)",
          [radio[3] for radio in (first["view"] or {}).get("radios", [])] == [True, False] and page.evaluate(DETAIL_PICTURE)["hash"] == "#umi-short-convex-tip5.8-2mm",
          (first["src"], page.evaluate(DETAIL_PICTURE)["src"]))
    check(f"pictures{tag}: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()
    # Phones and every width: the page never scrolls sideways; the picture 3:1 at 390 x 844 (part_first_screen checks Open).
    overflow = {}
    page = new_page(browser, 390, 844)
    library_case(page, "pictures", view=view)
    for fragment, name in (("#widowx-250-1mm", "detail"), (f"#{SHORT_TAPER}", "tapers")):
        open_library(page, fragment)
        wait_until(page, PICTURE_SETTLED, 10)
        page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_{name}_exploded_390x844.png")
        if name == "detail":
            page.click("#libDetail .lib-view label:has(input[value='assembled'])")
            wait_until(page, DETAIL_SHOWS, 10, IMAGES["widowx-250-1mm"]["assembled"]["src"])
            page.screenshot(path=f"{SHOTS}/library_pictures{suffix}_detail_assembled_390x844.png")
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(80)
        for fragment in ("", f"#{SHORT_TAPER}"):
            page.evaluate("(fragment) => { location.hash = fragment; }", fragment); page.wait_for_timeout(80)
            overflow[(width, fragment or "grid")] = page.evaluate("() => Math.max(document.documentElement.scrollWidth - document.documentElement.clientWidth, "
                                                                   "(body => body.scrollWidth - body.clientWidth)(document.getElementById('libWindowBody')))")
    check(f"pictures{tag}: no sideways scroll from 1440 to 320 px (the grid, and the Short taper's page in its window)", all(value <= 0 for value in overflow.values()),
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
          and fills["blue"] == blues(page, "a.lib-open") and fills["green"] == [], (grounds, dark["background"], dark["view"]["thumb"], fills))
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
    slots = [slot for slot in page.evaluate(SLOTS) if slot["owner"] != "showcase"]
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
    hero = [slot for slot in slots if slot["owner"] == "showcase"]
    slots = [slot for slot in slots if slot["owner"] != "showcase"]
    wrong = [slot for slot in slots if placeholder_wrong(slot) is not None]
    check("placeholders: without pictures every card's slot is the drawing of its sensor's field (a line per row and column), no image",
          not wrong and len(slots) == len(GRID_CARDS), wrong[:2] or len(slots))
    check("placeholders: the showcase's card too: the drawing of its pad's field (12 columns and 32 rows), no image",
          len(hero) == 1 and hero[0]["children"] == ["svg"] and hero[0]["field"] and hero[0]["img"] is None and hero[0]["lines"] == 44, hero[:1])
    page.screenshot(path=f"{SHOTS}/library_placeholders_grid_1440_light.png")
    page.set_viewport_size({"width": 900, "height": 900}); page.wait_for_timeout(120)
    page.screenshot(path=f"{SHOTS}/library_placeholders_grid_900_light.png")
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(120)
    pages = {}
    for fragment in ("#widowx-250-1mm", f"#{SHORT_TAPER}"):
        open_library(page, fragment)
        pages[fragment] = page.evaluate(DETAIL_PICTURE)
        page.screenshot(path=f"{SHOTS}/library_placeholders_{'detail' if fragment == '#widowx-250-1mm' else 'tapers'}_1440.png")
    check("placeholders: a sensor's page and the Short taper's page show the field's drawing in the frame, no view control (the frame its slot and its padding)",
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
    for fragment, name in (("#widowx-250-1mm", "detail"), (f"#{SHORT_TAPER}", "tapers")):
        open_library(page, fragment)
        page.screenshot(path=f"{SHOTS}/library_placeholders_{name}_390x844.png")
    page.context.close()


# A family sensor's page: the address, the checked choice of each axis, the title, Open, the pitch control.
FAMILY_VIEW = """() => ({hash: location.hash, detail: document.getElementById('libWindow').open,
  grid: !document.getElementById('libGrid').hidden && !document.getElementById('libWindow').open,
  y: Math.round(scrollY), top: Math.round(document.getElementById('libWindowBody').scrollTop), history: history.length, title: document.getElementById('libDetailTitle')?.textContent.replace(/\u2011/g, '-') || null,
  shape: document.querySelector('input[name="libAxis-shape"]:checked')?.value || null, tip: document.querySelector('input[name="libAxis-tip_mm"]:checked')?.value || null,
  legends: [...document.querySelectorAll('#libDetail .lib-seg legend')].map(l => l.textContent), pitch: document.querySelector('input[name="libPitch"]') !== null,
  view: document.querySelector('#libDetail input[name="libView"]:checked')?.value || null,
  open: document.querySelector('.lib-open')?.getAttribute('href') || null,
  focus: [document.activeElement.id, document.activeElement.name || null, document.activeElement.value || null, document.activeElement.dataset?.card || null,
          document.activeElement.closest('.lib-shelf')?.id || null],
  note: document.getElementById('libNote').hidden ? null : document.getElementById('libNote').textContent})"""


def part_family(browser):
    """The tapered tips (2026-11-05), since the user's request of 2026-11-16 one card per shape after the straight finger
    on the UMI shelf: the shelf's cards, the Short taper's page (Shape and Tip width), the Concave arc and Pointed tips'
    pages, a tip's id, part id and window's X."""
    family = ENTRIES["families"]["umi-tapers"]
    members = [part for part, record in ENTRIES["parts"].items() if record["family"] == "umi-tapers"]
    shapes = {card["key"]: card for card in family["cards"]}
    page = new_page(browser)
    open_library(page, "#shelf-umi-finray")
    cards = page.evaluate("""() => [...document.querySelectorAll('#shelf-umi-finray .lib-card')].map(card => [card.dataset.variant, card.dataset.card || null,
        card.getAttribute('href'), [...card.querySelectorAll('.lib-card-name, .lib-card-line')].map(n => n.textContent.replace(/\\u00a0/g, ' '))])""")
    everywhere = page.evaluate("() => [...document.querySelectorAll('.lib-card')].map(n => n.dataset.variant || n.dataset.family || n.getAttribute('href'))")
    expected = [["umi-finray-2mm", None, "#umi-finray-2mm", ["Straight finger", "1 to 3 mm", "Pick your pitch"]]] + [
        [card["default"], card["key"], f"#{card['default']}", [card["title"], *card["lines"]]] for card in family["cards"]]
    check("family: the UMI shelf's cards, one per shape: Straight finger, then Short taper, Convex arc tip, Trapezoid tip, Concave arc tip "
          "and Pointed tip, each its two lines and its sensor's page",
          cards == expected and [card[3][0] for card in cards] == ["Straight finger", "Short taper", "Convex arc tip", "Trapezoid tip", "Concave arc tip", "Pointed tip"],
          cards)
    check("family: no tip has a shelf, and none a card but its shape's (each card's own sensor)",
          sorted(item for item in everywhere if any(str(item).startswith(member + "-") for member in members)) == sorted(card["default"] for card in family["cards"])
          and not page.query_selector_all(", ".join(f"[id='shelf-{member}']" for member in members)), everywhere)
    page.locator("#shelf-umi-finray").screenshot(path=f"{SHOTS}/library_family_card.png")
    before = page.evaluate(FAMILY_VIEW)
    short = shapes["short"]
    page.click(".lib-card[data-card='short']"); page.wait_for_timeout(200)
    shown = page.evaluate(FAMILY_VIEW)
    facts = page.inner_text(".lib-facts")
    default = ENTRIES["variants"][short["default"]]
    # (Its title the card's shape since the review of 2026-11-16, 'UMI Fin-Ray Gripper, tapered tip' before; its view the
    # card's, Exploded as a gripper's since the user's request of that day, Assembled from the review until then.)
    check("family: the Short taper's card opens its 9.8 mm trapezoid's page in the window at its top, the grid where it was under it, its title "
          "('UMI Fin-Ray Gripper, short taper') focused, Exploded as its card, Shape and Tip width in place of the pitch",
          shown["hash"] == f"#{short['default']}" and short["default"] == "umi-short-trap-tip9.8-2mm" and shown["detail"] and shown["y"] == before["y"]
          and shown["top"] == 0 and shown["focus"][0] == "libDetailTitle" and shown["title"] == "UMI Fin-Ray Gripper, short taper" and shown["view"] in ("exploded", None)
          and (shown["shape"], shown["tip"]) == ("trap", "9.8") and shown["legends"] == ["Shape", "Tip width (mm)"] and not shown["pitch"]
          and shown["open"] == f"gen.html?part={short['default']}" and shown["history"] == before["history"] + 1, shown)
    check(f"family: its facts (the tip over the last 40 mm, {default['rows']} rows × {default['columns']} columns · {default['taxels']} taxels, 2 mm · fill 0.50, the build)",
          "Trapezoid, 9.8 mm at the tip, over the last 40 mm" in facts and f"{default['rows']} rows × {default['columns']} columns · {default['taxels']} taxels" in facts
          and "2 mm · fill 0.50" in facts and default["build_id"] in facts, facts)
    page.screenshot(path=f"{SHOTS}/library_family_detail.png")
    page.click("label:has(input[name='libAxis-shape'][value='convex'])"); page.wait_for_timeout(150)
    convex = page.evaluate(FAMILY_VIEW)
    # The review of 2026-11-05: the line under the title ('Soft fin-ray finger, short convex arc tip · UMI ...') never
    # starts a line with its separator (a no-break space joins it to the word before it).
    starts = {}
    for width in (1440, 1100, 900, 390, 320):
        page.set_viewport_size({"width": width, "height": 900}); page.wait_for_timeout(100)
        starts[width] = page.evaluate("""() => { const text = document.querySelector('.lib-detail-line').firstChild; const lines = [];
          for (let i = 0, top = null; i < text.data.length; i += 1) { const range = document.createRange(); range.setStart(text, i); range.setEnd(text, i + 1);
            const box = [...range.getClientRects()].find(r => r.width > 0); if (!box) continue;
            if (Math.round(box.top) !== top) { lines.push(''); top = Math.round(box.top); } lines[lines.length - 1] += text.data[i]; }
          return lines.map(line => line.trim()); }""")
    page.set_viewport_size({"width": 1440, "height": 900}); page.wait_for_timeout(100)
    check("family: the short convex arc tip's line under the title never starts a line with its '·'",
          all(not line.startswith("\u00b7") for lines in starts.values() for line in lines) and any(len(lines) > 1 for lines in starts.values()), starts)
    page.click("label:has(input[name='libAxis-tip_mm'][value='5.8'])"); page.wait_for_timeout(150)
    narrow = page.evaluate(FAMILY_VIEW)
    check("family: Shape and Tip width replace the address (no history entry) with the card's sensor, the changed control focused",
          (convex["hash"], convex["shape"], convex["tip"], convex["open"], convex["focus"][1:3]) == ("#umi-short-convex-tip9.8-2mm", "convex", "9.8", "gen.html?part=umi-short-convex-tip9.8-2mm", ["libAxis-shape", "convex"])
          and (narrow["hash"], narrow["shape"], narrow["tip"], narrow["open"], narrow["focus"][1:3]) == ("#umi-short-convex-tip5.8-2mm", "convex", "5.8", "gen.html?part=umi-short-convex-tip5.8-2mm", ["libAxis-tip_mm", "5.8"])
          and convex["history"] == narrow["history"] == shown["history"] and "Convex arc, 5.8 mm at the tip, over the last 40 mm" in page.inner_text(".lib-facts"),
          (convex, narrow))
    fills = page.evaluate(FILLS)
    check("family: the action blue fills only Open in Gen by Surface on its page (the controls' thumbs are grey), nothing green",
          fills["blue"] == blues(page, "a.lib-open") and fills["green"] == [], fills)
    page.go_back(); page.wait_for_timeout(200)
    back = page.evaluate(FAMILY_VIEW)
    check("family: Back returns to the grid where it was, the Short taper's card focused",
          back["grid"] and not back["detail"] and abs(back["y"] - before["y"]) <= 1 and back["focus"][3:] == ["short", "shelf-umi-finray"], (before["y"], back))
    # The new shapes' own pages: the concave arc (Tip width alone, its five widths) and the point (no control).
    pages = {}
    for key, fact in (("concave", "Concave arc, 9.8 mm at the tip, over the last 75 mm"), ("pointed", "Pointed, 2 mm at the tip, over the last 50 mm")):
        page.click(f".lib-card[data-card='{key}']"); page.wait_for_timeout(200)
        seen = page.evaluate(FAMILY_VIEW)
        tips = page.evaluate("() => [...document.querySelectorAll('input[name=\"libAxis-tip_mm\"]')].map(n => n.value)")
        pages[key] = (seen["hash"], seen["legends"], tips, seen["tip"], fact in page.inner_text(".lib-facts"), seen["pitch"], seen["title"], seen["view"])
        page.screenshot(path=f"{SHOTS}/library_family_{key}.png")
        page.go_back(); page.wait_for_timeout(200)
    # Each titled by its card and opened Exploded as its card shows it (the user's request of 2026-11-16).
    viewed = "exploded" if IMAGES["umi-concave-tip9.8-2mm"] else None
    check("family: the Concave arc tip's page its Tip width alone (21.8 to 5.8 mm, 9.8 checked), the Pointed tip's no control, each its Tip fact, "
          "titled by its card ('UMI Fin-Ray Gripper, concave arc tip', '..., pointed tip') and opened Exploded",
          pages == {"concave": ("#umi-concave-tip9.8-2mm", ["Tip width (mm)"], ["21.8", "17.8", "13.8", "9.8", "5.8"], "9.8", True, False,
                                "UMI Fin-Ray Gripper, concave arc tip", viewed),
                    "pointed": ("#umi-pointed-tip2-2mm", [], [], None, True, False, "UMI Fin-Ray Gripper, pointed tip", viewed)}, pages)
    page.context.close()
    page = new_page(browser)
    open_library(page, "#umi-convex-tip9.8-2mm")
    direct = page.evaluate(FAMILY_VIEW)
    check("family: a tip's id opens its page (the Convex arc tip's card, 9.8 mm)",
          direct["detail"] and (direct["shape"], direct["tip"], direct["legends"]) == (None, "9.8", ["Tip width (mm)"]), direct)
    page.click("#libClose"); page.wait_for_timeout(200)
    at, target, _ = page.evaluate(SHELF_TOP, "shelf-umi-finray")
    closed = page.evaluate(FAMILY_VIEW)
    check("family: the X of a tip's window (opened directly) goes to the UMI shelf (the back link's place until 2026-11-15)",
          closed["hash"] == "#shelf-umi-finray" and closed["grid"] and abs(at - target) <= 1, (closed, at, target))
    open_library(page, "#umi-trap-tip5.8")
    part = page.evaluate(FAMILY_VIEW)
    check("family: a tip's part id opens its one sensor, the address kept", part["detail"] and (part["tip"], part["hash"]) == ("5.8", "#umi-trap-tip5.8"), part)
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
    # The reading board (2026-11-17): the 26 x 27 sensor's, the 32 x 32 board's bundle as served (tools/flexitac_downloads.py).
    with page.expect_download(timeout=60000) as info:
        page.click(".lib-board a[download]")
    download = info.value
    path = downloads / f"library-{download.suggested_filename}"
    download.save_as(path)
    check("downloads: the reading board's ZIP is the 32 x 32 bundle as served, under its name",
          path.read_bytes() == (ROOT / "web" / "vendor" / "flexitac-reader" / "FlexiTac_reading_board_32x32.zip").read_bytes()
          and download.suggested_filename == "FlexiTac_reading_board_32x32.zip", download.suggested_filename)
    licence = page.get_attribute(".lib-links a[target='_blank']", "href")
    reply = page.request.get(SITE["base"] + licence)
    check("downloads: the licence text is served (BSD-3-Clause)", reply.status == 200 and reply.body() == (LIBRARY / part["license"]["text"]).read_bytes()
          and "Licence (BSD-3-Clause)" in page.inner_text(".lib-links"), (licence, reply.status))
    # (2026-11-17) The LeFlexiTac's files state no licence and are shared with its authors' permission
    # (tools/library_write.py PERMITTED_LICENCES): its page's one link, to the project's note, says so.
    open_library(page, "#leflexitac-2mm")
    links = page.inner_text(".lib-links")
    note = page.get_attribute(".lib-links a[target='_blank']", "href")
    reply = page.request.get(SITE["base"] + note)
    check("downloads: the LeFlexiTac's page links its note as 'Shared with the authors' permission'",
          "Shared with the authors' permission" in links and "Licence" not in links and reply.status == 200
          and reply.body() == (LIBRARY / "licenses" / "leflexitac.txt").read_bytes(), (links, note, reply.status))
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
            grid_blue = blues(page)
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
            check(f"isolation {tag}: the action blue fills only Open in Gen by Surface and the showcase's Design your own, nothing green (the grid "
                  f"and a sensor's page{', its 3D view drawn' if view else ''})",
                  grid["blue"] == grid_blue and detail["blue"] == blues(page, "a.lib-open") and grid["green"] == detail["green"] == [] and (drawn or not view), (grid, detail, drawn))
            page.screenshot(path=f"{SHOTS}/library_detail_{scheme}{'_view' if view else ''}.png")
            words = page.evaluate(WORDS)
            open_library(page)
            words += page.evaluate(WORDS)
            check(f"isolation {tag}: the page never says CAD and is English (its text, titles and labels)",
                  not [text for text in words if re.search(r"\bCAD\b", text)] and not [text for text in words if re.search(r"[Ѐ-ӿ　-鿿가-힯]", text)],
                  [text[:80] for text in words if re.search(r"\bCAD\b", text)])
            base = SITE["base"]
            # (GitHub's API for the header's counts on the built site, answered here: web/counts.js, 2026-11-16.)
            foreign = [url for url in page.requests if not url.startswith(base) and url != GITHUB_API]
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


# -- the window (part_window) ---------------------------------------------------------------------------------------
# The user's request of 2026-11-15 ("after we click for all cards to details, we may not jump to a new page. lets bump our
# to a large window, and if you click the "x" of right top conrner, it will close and back show lib"): every card's page
# in a large window over the Library (library.js raise() and closeWindow(), library.css .lib-window).
# The window as it stands: open and modal, the address, the tab, the page's scroll and the window's own, its box, its
# look and the backdrop's, the X's box and look, the root's overflow, the focus (inside the window, or the page's body:
# the browser's own controls between two rounds of Tab), and the Library under it (its title and cards rendered).
WINDOW_STATE = """() => { const dialog = document.getElementById('libWindow'); const body = document.getElementById('libWindowBody'); const close = document.getElementById('libClose');
  const box = n => (r => [r.left, r.top, r.width, r.height].map(v => Math.round(v * 10) / 10))(n.getBoundingClientRect());
  const style = getComputedStyle(dialog); const active = document.activeElement; const x = getComputedStyle(close);
  return {open: dialog.open, modal: dialog.matches(':modal'), hash: location.hash, tab: document.title, y: Math.round(scrollY), top: Math.round(body.scrollTop),
    box: box(dialog), close: box(close), scroll: [body.scrollHeight, body.clientHeight], radius: style.borderTopLeftRadius, background: style.backgroundColor,
    shadow: style.boxShadow, backdrop: getComputedStyle(dialog, '::backdrop').backgroundColor, root: getComputedStyle(document.documentElement).overflowY,
    focus: active === document.body || !active ? 'body' : (active.id || active.className || active.tagName), inside: dialog.contains(active),
    x: {radius: x.borderTopLeftRadius, image: x.backgroundImage, colour: x.backgroundColor, label: close.getAttribute('aria-label'), type: close.type,
        tab: close.tabIndex, hit: close.contains(document.elementFromPoint(...(r => [r.left + r.width / 2, r.top + r.height / 2])(close.getBoundingClientRect())))},
    inner: innerWidth, high: innerHeight, client: document.body.getBoundingClientRect().width, length: history.length,
    hero: document.getElementById('libHero').checkVisibility(), cards: [...document.querySelectorAll('#libGrid .lib-card')].filter(n => n.checkVisibility()).length}; }"""
# The grid's cards' boxes in the window (viewport px): opening the window moves none of them.
GRID_BOXES = """() => [...document.querySelectorAll('#libGrid .lib-card')].map(n => (r => [r.left, r.top, r.width, r.height].map(v => Math.round(v * 10) / 10))(n.getBoundingClientRect()))"""
# The openers (the user's "all cards"): a gripper's card, the UMI shelf's Straight finger and a shape's card (its 1.5 mm
# card and the Tapered tips card until the shapes of 2026-11-16), the showcase's Details and its picture; what each opens
# and what is focused once the window closes.
OPENERS = (("a gripper's card", "#gripper-franka-hand", "#franka-hand-2mm", "gripper-franka-hand"),
           ("the UMI shelf's Straight finger", "#shelf-umi-finray .lib-card[data-part='umi-finray']", "#umi-finray-2mm", "lib-card"),
           ("a shape's card", "#shelf-umi-finray .lib-card[data-card='concave']", "#umi-concave-tip9.8-2mm", "lib-card"),
           ("the showcase's Details", ".lib-showcase-details", None, "lib-pill lib-showcase-details"),
           ("the showcase's picture", ".lib-showcase-pic", None, "lib-pill lib-showcase-details"))


def window_gutter(width):
    """library.css --lib-gutter at a window ``width`` (100vw: the scroll bar's room included): clamp(24px, 5vw, 76px), 20 px
    up to 520 px."""
    return 20 if width <= 520 else max(24, min(76, 0.05 * width))


def window_box_wrong(state, width, height):
    """None when the window stands as library.css has it at ``width`` x ``height`` (CSS px), else what it is: below 735 px,
    and on a screen less than 501 px tall (the review of 2026-11-15), a sheet over the whole screen (no corners, no
    shadow); else min(1200 px, 100vw less two gutters) wide, centred, its top a gutter down, at most the screen's height
    less two gutters, the cards' 18 px corners."""
    left, top, box_width, box_height = state["box"]
    if width < 735 or height <= 500:
        sheet = (left, top, box_width, box_height, state["radius"], state["shadow"]) == (0, 0, width, height, "0px", "none")
        return None if sheet else {"box": state["box"], "radius": state["radius"], "shadow": state["shadow"]}
    gutter = window_gutter(width)
    wide = min(1200, width - 2 * gutter)
    good = (abs(box_width - wide) <= 1 and abs(left - (state["client"] - box_width) / 2) <= 1 and abs(top - gutter) <= 1
            and box_height <= height - 2 * gutter + 1 and state["radius"] == "18px")
    return None if good else {"box": state["box"], "wide": wide, "gutter": gutter, "radius": state["radius"]}


def part_window(browser):
    """The details window (2026-11-15): at 1440 x 900, 900 x 900 and 390 x 844, light and dark, each opener (a gripper's
    card, the UMI shelf's Straight finger and a shape's card, the showcase's Details and its picture) opens its page in the window
    over the grid, which neither moves nor scrolls (its cards where they were, the page's scroll kept, the root not
    scrolling: the wheel over the backdrop and over the window, the keys inside it), the window's page at its top with its
    title focused, the tab named after it; the window's box (a sheet below 735 px), the cards' look and the dim backdrop;
    the X round, grey, named Close, Tab-reachable and in sight with the window's page scrolled to its end; the focus kept
    inside the window by Tab and Shift+Tab; the X, Escape and a press and release on the backdrop close it to the grid's
    place with its opener focused; a drag of the 3D view (or of a selection) released over the backdrop, and a press on the
    backdrop released inside, keep it; Back closes it and Forward opens it again; a window's address opened anew shows the
    Library with the window over it; the action blue only on Open in Gen by Surface; no console error.  Screenshots:
    library_window_<what>_<width>_<scheme>.png."""
    for width, height in ((1440, 900), (900, 900), (390, 844)):
        for scheme in ("light", "dark"):
            tag = f"window {width} {scheme}"
            page = new_page(browser, width, height, scheme)
            page.goto(SITE["base"] + "?probe")
            wait_until(page, READY, 30)
            page.wait_for_timeout(150)
            # Each opener, from the grid scrolled to bring it in sight (the window opens over the grid where it is).
            opened, closed, boxes, looks = {}, {}, {}, {}
            for name, selector, address, focused in OPENERS:
                page.locator(selector).first.evaluate("node => { node.scrollIntoView({block: 'center'}); scrollBy(0, 7); }"); page.wait_for_timeout(60)
                grid, before = page.evaluate(GRID_BOXES), page.evaluate(WINDOW_STATE)
                page.locator(selector).first.click(); page.wait_for_timeout(250)
                state = page.evaluate(WINDOW_STATE)
                expected = address or f"#{json.loads((LIBRARY / 'showcase.json').read_text(encoding='utf-8'))['id']}"
                opened[name] = (state["open"] and state["modal"] and state["hash"] == expected and state["y"] == before["y"] and state["top"] == 0
                                and state["focus"] == "libDetailTitle" and page.evaluate(GRID_BOXES) == grid and state["hero"] and state["cards"] > 0
                                and state["tab"] != "Library · FlexiTac-Gen" and state["tab"].endswith(" · Library · FlexiTac-Gen") and state["root"] == "hidden")
                if not opened[name]:
                    opened[name] = state
                boxes[name] = window_box_wrong(state, width, height)
                looks[name] = state
                page.click("#libClose"); page.wait_for_timeout(200)
                after = page.evaluate(WINDOW_STATE)
                closed[name] = (not after["open"] and after["y"] == before["y"] and after["focus"] == focused and after["tab"] == "Library · FlexiTac-Gen"
                                and page.evaluate(GRID_BOXES) == grid and after["root"] != "hidden") or after
            check(f"{tag}: each opener (a gripper's card, the UMI shelf's Straight finger and a shape's card, the showcase's Details and picture) opens its page in "
                  "the window (modal) over the grid, which does not move (its cards, the page's scroll), the window's page at its top, its title focused, "
                  "the tab named after it, the root not scrolling",
                  all(value is True for value in opened.values()), {key: value for key, value in opened.items() if value is not True})
            check(f"{tag}: the window " + ("a sheet over the whole screen" if width < 735 else "min(1200 px, the screen less two gutters) wide, centred, "
                  "a gutter from the top, within the screen less two gutters, its corners 18 px"),
                  not any(boxes.values()), {key: value for key, value in boxes.items() if value})
            check(f"{tag}: the X closes it to the grid where it was, its opener focused (the showcase's Details for its picture too), the tab the Library's",
                  all(value is True for value in closed.values()), {key: value for key, value in closed.items() if value is not True})
            look = looks["a gripper's card"]
            surface = "rgb(28, 28, 30)" if scheme == "dark" else "rgb(255, 255, 255)"
            sheet = width < 735
            check(f"{tag}: the cards' look (the window {surface}, " + ("no shadow: a sheet" if sheet else "a shadow") + "), the backdrop a dim black; "
                  "the X round and grey, named Close, a button in the Tab order",
                  look["background"] == surface and (look["shadow"] == "none") == sheet and look["backdrop"] == "rgba(0, 0, 0, 0.45)"
                  and look["x"]["radius"] == "50%" and "gradient" in look["x"]["image"] and look["x"]["colour"] == surface
                  and (look["x"]["label"], look["x"]["type"], look["x"]["tab"]) == ("Close", "button", 0), (look["background"], look["shadow"], look["backdrop"], look["x"]))
            # A gripper's window: screenshots, the blue, the X in sight and the page held while the window's page scrolls.
            page.evaluate("() => scrollTo(0, 0)"); page.wait_for_timeout(60)
            page.locator("#gripper-franka-hand").scroll_into_view_if_needed(); page.wait_for_timeout(60)
            page.click("#gripper-franka-hand")
            library_shots.poll(page, LIVE_SHOWN, None, 120)
            page.wait_for_timeout(200)
            page.screenshot(path=f"{SHOTS}/library_window_gripper_{width}_{scheme}.png")
            fills = page.evaluate(FILLS)
            start = page.evaluate(WINDOW_STATE)
            x_box = start["close"]
            moves = {}
            outside = (min(20, start["box"][0] / 2), height / 2) if width >= 735 else None
            for where, point in (("over the window", (start["box"][0] + start["box"][2] / 2, start["box"][1] + start["box"][3] - 40)), ("over the backdrop", outside)):
                if point is None:
                    continue
                page.mouse.move(*point); page.mouse.wheel(0, 1200); page.wait_for_timeout(250)
                moves[f"wheel {where}"] = page.evaluate(WINDOW_STATE)["y"] - start["y"]
            page.focus("#libDetailTitle")
            for key in ("End", "PageDown", "Space"):
                page.keyboard.press(key); page.wait_for_timeout(120)
                moves[key] = page.evaluate(WINDOW_STATE)["y"] - start["y"]
            page.evaluate("() => { const body = document.getElementById('libWindowBody'); body.scrollTop = body.scrollHeight; }"); page.wait_for_timeout(100)
            end = page.evaluate(WINDOW_STATE)
            page.screenshot(path=f"{SHOTS}/library_window_gripper_end_{width}_{scheme}.png")
            check(f"{tag}: the page under the window never scrolls (the wheel over the window and the backdrop, End, PageDown, Space), the window's page does",
                  not any(moves.values()) and (end["top"] > 0 or end["scroll"][0] <= end["scroll"][1]) and end["open"], (moves, end["top"], end["scroll"]))
            check(f"{tag}: the X stays in sight at the window's top right with its page scrolled to its end",
                  end["close"] == x_box and end["x"]["hit"] and x_box[0] + x_box[2] <= start["box"][0] + start["box"][2] - 11
                  and x_box[1] >= start["box"][1] + 11 and x_box[1] + x_box[3] <= start["box"][1] + 60, (x_box, end["close"], end["x"]["hit"], start["box"]))
            check(f"{tag}: the action blue fills only Open in Gen by Surface, nothing green (the window and the grid under it)",
                  fills["blue"] == blues(page, "a.lib-open") and fills["green"] == [], fills)
            # The focus kept inside: Tab and Shift+Tab, 30 presses each, never reach the grid (the page's body is the
            # browser's own controls between two rounds); the X among the stops.
            page.evaluate("() => { document.getElementById('libWindowBody').scrollTop = 0; }")
            page.focus("#libDetailTitle")
            stops = []
            for key in ("Tab", "Shift+Tab"):
                for _ in range(30):
                    page.keyboard.press(key)
                    state = page.evaluate(WINDOW_STATE)
                    stops.append((state["focus"], state["inside"] or state["focus"] == "body"))
            check(f"{tag}: Tab and Shift+Tab keep the focus inside the window (30 presses each), the X one of its stops",
                  all(inside for _, inside in stops) and "libClose" in [focus for focus, _ in stops] and page.evaluate(WINDOW_STATE)["open"],
                  [stop for stop in stops if not stop[1]][:4] or sorted({focus for focus, _ in stops}))
            # Escape closes it, its opener focused, with no new history entry (back over its entry to the grid's, whose
            # address is then its card's: the review of 2026-11-15); Forward opens it again, Back closes it, Forward opens it
            # again and its X closes it, still no entry added.
            length = page.evaluate(WINDOW_STATE)["length"]
            steps = []
            for action in ("Escape", "Forward", "Back", "Forward", "X"):
                if action == "Escape":
                    page.keyboard.press("Escape")
                elif action == "Forward":
                    page.go_forward()
                elif action == "Back":
                    page.go_back()
                else:
                    page.click("#libClose")
                page.wait_for_timeout(300)
                state = page.evaluate(WINDOW_STATE)
                steps.append((action, state["open"], state["hash"], state["focus"], state["y"], state["length"] - length))
            closed = ("#gripper-franka-hand", "gripper-franka-hand", start["y"], 0)
            opened_again = ("#franka-hand-2mm", "libDetailTitle", start["y"], 0)
            check(f"{tag}: Escape closes it to #gripper-<part>, its card focused, no history entry added; Forward opens it again, Back closes it, "
                  "Forward opens it again, its X closes it; the grid where it was throughout",
                  [step[1:] for step in steps] == [(False, *closed), (True, *opened_again), (False, *closed), (True, *opened_again), (False, *closed)], steps)
            # The backdrop (from 735 px; a phone's sheet has none): a press and release on it closes the window; a drag of
            # the 3D view, or a selection's drag, begun inside and released over it, and a press on it released inside,
            # keep the window open.
            if width >= 735:
                page.click("#gripper-franka-hand"); library_shots.poll(page, LIVE_SHOWN, None, 120); page.wait_for_timeout(150)
                box = page.evaluate(CANVAS_BOX)
                centre = (box[0] + box[2] / 2, box[1] + box[3] / 2)
                kept = {}
                page.mouse.move(*centre); page.mouse.down(); page.mouse.move(*outside, steps=10); page.mouse.up(); page.wait_for_timeout(200)
                kept["the 3D view dragged out"] = (page.evaluate(WINDOW_STATE)["open"], page.evaluate(LIB_STATE)["moved"])
                info = page.evaluate("() => (r => [r.left + 8, r.top + 8])(document.querySelector('#libDetail .lib-facts dd').getBoundingClientRect())")
                page.mouse.move(*info); page.mouse.down(); page.mouse.move(*outside, steps=6); page.mouse.up(); page.wait_for_timeout(200)
                kept["a selection dragged out"] = page.evaluate(WINDOW_STATE)["open"]
                page.mouse.move(*outside); page.mouse.down(); page.mouse.move(*info, steps=6); page.mouse.up(); page.wait_for_timeout(200)
                kept["a press on the backdrop released inside"] = page.evaluate(WINDOW_STATE)["open"]
                page.mouse.click(*outside); page.wait_for_timeout(250)
                shut = page.evaluate(WINDOW_STATE)
                check(f"{tag}: a drag of the 3D view (turning it) or of a selection released over the backdrop, and a press on the backdrop released "
                      "inside, keep the window; a press and release on the backdrop closes it, its card focused",
                      kept == {"the 3D view dragged out": (True, True), "a selection dragged out": True, "a press on the backdrop released inside": True}
                      and (shut["open"], shut["hash"], shut["focus"]) == (False, "#gripper-franka-hand", "gripper-franka-hand"), (kept, shut["open"], shut["focus"]))
                # A card (the grippers' last) double-clicked where the backdrop then lies (below the window, which ends a gutter or more above the
                # screen's foot): the window opens and stays, one history entry (the review of 2026-11-15: the second click,
                # on the backdrop, had closed it at once).
                shelf_card = page.locator("#libGrid .lib-cards .lib-card").last
                foot = height - window_gutter(width) / 2
                shelf_card.evaluate("(node, y) => { const r = node.getBoundingClientRect(); scrollBy(0, r.top - y); }", foot - 14); page.wait_for_timeout(80)
                card_box = shelf_card.bounding_box()
                point = (card_box["x"] + card_box["width"] / 2, foot)
                page.mouse.click(*point); page.wait_for_timeout(150)
                page.mouse.down(click_count=2); page.mouse.up(click_count=2); page.wait_for_timeout(300)
                double = page.evaluate(WINDOW_STATE)
                page.go_back(); page.wait_for_timeout(300)
                backed = page.evaluate(WINDOW_STATE)
                check(f"{tag}: a card double-clicked where the backdrop then lies (below the window) opens the window and keeps it, one history entry "
                      "(one Back closes it)",
                      double["open"] and double["hash"] == shelf_card.get_attribute("href") and not backed["open"] and backed["hash"] == "#gripper-franka-hand"
                      and card_box["y"] < point[1] < card_box["y"] + card_box["height"] and double["box"][1] + double["box"][3] < point[1],
                      (double["open"], double["hash"], backed["open"], backed["hash"], double["box"], card_box, point))
            # The showcase's window and the Short taper's (screenshots; the Tapered tips' until 2026-11-16), then each address
            # opened anew: the Library with the window over it.
            for what, selector in (("showcase", ".lib-showcase-details"), ("tapers", ".lib-card[data-card='short']")):
                page.locator(selector).scroll_into_view_if_needed(); page.wait_for_timeout(60)
                page.click(selector)
                library_shots.poll(page, LIVE_SHOWN, None, 120)
                page.wait_for_timeout(250)
                page.screenshot(path=f"{SHOTS}/library_window_{what}_{width}_{scheme}.png")
                if what == "showcase":
                    showcase_fills, showcase_blue = page.evaluate(FILLS), blues(page)
                page.click("#libClose"); page.wait_for_timeout(150)
            check(f"{tag}: no blue in the showcase's window (no Open in Gen by Surface there; the grid's Design your own under it), nothing green",
                  showcase_fills["blue"] == showcase_blue and showcase_fills["green"] == [], showcase_fills)
            direct = {}
            for address in ("#widowx-250-1mm", "#umi-tapers", f"#{json.loads((LIBRARY / 'showcase.json').read_text(encoding='utf-8'))['id']}"):
                page.goto(SITE["base"] + address)
                wait_until(page, READY, 30); page.wait_for_timeout(200)
                state = page.evaluate(WINDOW_STATE)
                direct[address] = (state["open"] and state["modal"] and state["hash"] == address and state["y"] == 0 and state["hero"] and state["cards"] > 0
                                   and state["focus"] == "libDetailTitle" and window_box_wrong(state, width, height) is None) or state
            check(f"{tag}: an address of a window opened anew (a sensor's, the Tapered tips', the showcase's) shows the Library with the window over it",
                  all(value is True for value in direct.values()), {key: value for key, value in direct.items() if value is not True})
            check(f"{tag}: no console error", not errors_of(page), errors_of(page)[:5])
            page.context.close()
            window_history(browser, width, height, scheme, tag)


# The window's history as window_history() reads it: open, the address (with its query), the history's length, the focus.
HISTORY_STATE = """() => ({open: document.getElementById('libWindow')?.open ?? null, url: location.search + location.hash, length: history.length,
  focus: document.activeElement?.id || document.activeElement?.value || ''})"""
# A close request as Android's Back makes one while a modal dialog is open (its CloseWatcher; Escape's on a desktop):
# the dialog's requestClose() where the browser has it (its cancel, then its close unless cancelled), else its cancel.
CLOSE_REQUEST = """() => { const dialog = document.getElementById('libWindow');
  if (typeof dialog.requestClose === 'function') dialog.requestClose(); else dialog.dispatchEvent(new Event('cancel', {cancelable: true})); }"""
# A cancel the browser does not let be cancelled (Android's Back with no activation since the last), then the dialog's
# close by the browser: one close, not two.
CANCEL_THEN_CLOSE = """() => { const dialog = document.getElementById('libWindow');
  dialog.dispatchEvent(new Event('cancel', {cancelable: false})); dialog.close(); }"""


def window_history(browser, width, height, scheme, tag):
    """The review of 2026-11-15: closing the window makes no history entry, so a Back after a close goes where it went
    before the window opened (with Android's Back a close request while the window is open, a new entry had made each
    Back close it and the next open it again, for ever, from the grid and from a shared link).  After an earlier page
    (./?before): a window opened from the grid, closed by a close request (CLOSE_REQUEST) and by a cancel then
    its close (CANCEL_THEN_CLOSE: one entry back, not two), each to its card's place with its card focused and the
    history's length unchanged, the next Back the earlier page; a pitch chosen, another sensor's address typed over the
    window, Back to the first window (its entry's mark kept through the pitch) and its X: the grid, its card focused;
    Forward twice to the typed one and its X: back over both windows' entries to the grid, that sensor's card focused;
    a shared link's window closed by a close request (its entry replaced by its card's place), and after a reload of a
    window opened from the grid its X (in place: the grid's entry under it another document's); each time the next Back
    the earlier page."""
    page = new_page(browser, width, height, scheme)
    page.goto(SITE["base"] + "?before")
    wait_until(page, READY, 30)

    def go(address):
        page.goto(SITE["base"] + address)
        wait_until(page, READY, 30)
        page.wait_for_timeout(150)

    def act(how):
        if how == "X":
            page.click("#libClose")
        elif how == "Back":
            page.go_back()
        elif how == "Forward":
            page.go_forward()
        elif how == "reload":
            page.reload()
            wait_until(page, READY, 30)
        elif how.startswith("#"):
            page.evaluate("(hash) => { location.hash = hash; }", how)
        elif how.startswith("pitch "):
            page.click(f".lib-seg label:has(input[value='{how[6:]}'])")
        else:
            page.evaluate(how)
        page.wait_for_timeout(300)
        state = page.evaluate(HISTORY_STATE)
        return (state["open"], state["url"], state["focus"], state["length"])

    results = {}
    for name, closing in (("a close request", CLOSE_REQUEST), ("a cancel, then its close", CANCEL_THEN_CLOSE)):
        go("")
        opened = act("() => document.getElementById('gripper-franka-hand').click()")
        closed = act(closing)
        results[f"from the grid, {name}"] = (opened[:2], closed[:3], closed[3] - opened[3], act("Back")[1])
    want = {f"from the grid, {name}": ((True, "#franka-hand-2mm"), (False, "#gripper-franka-hand", "gripper-franka-hand"), 0, "?before")
            for name in ("a close request", "a cancel, then its close")}
    go("")
    act("() => document.getElementById('gripper-franka-hand').click()")
    sequence = [(how, act(how)) for how in ("pitch franka-hand-1mm", "#widowx-250-1mm", "Back", "X", "Forward", "Forward", "X", "Back")]
    results["a pitch, a typed address, Back and the X; Forward twice and the X"] = [(how, state[:3]) for how, state in sequence]
    want["a pitch, a typed address, Back and the X; Forward twice and the X"] = [
        ("pitch franka-hand-1mm", (True, "#franka-hand-1mm", "franka-hand-1mm")), ("#widowx-250-1mm", (True, "#widowx-250-1mm", "libDetailTitle")),
        ("Back", (True, "#franka-hand-1mm", "libDetailTitle")), ("X", (False, "#gripper-franka-hand", "gripper-franka-hand")),
        ("Forward", (True, "#franka-hand-1mm", "libDetailTitle")), ("Forward", (True, "#widowx-250-1mm", "libDetailTitle")),
        ("X", (False, "#gripper-widowx-250", "gripper-widowx-250")), ("Back", (False, "?before", ""))]
    go("#franka-hand-1mm")
    opened = page.evaluate(HISTORY_STATE)
    closed = act(CLOSE_REQUEST)
    results["a shared link, a close request"] = (opened["open"], closed[:3], closed[3] - opened["length"], act("Back")[1])
    want["a shared link, a close request"] = (True, (False, "#gripper-franka-hand", "gripper-franka-hand"), 0, "?before")
    go("")
    act("() => document.getElementById('gripper-franka-hand').click()")
    reloaded = act("reload")
    closed = act("X")
    results["reloaded, the X"] = (reloaded[:2], closed[:3], closed[3] - reloaded[3])
    want["reloaded, the X"] = ((True, "#franka-hand-2mm"), (False, "#gripper-franka-hand", "gripper-franka-hand"), 0)
    wrong = {key: (value, want[key]) for key, value in results.items() if value != want[key]}
    check(f"{tag}: closing the window adds no history entry, so the next Back leaves the grid (a close request and a cancel then its close from "
          "the grid, a shared link's close request, two windows' entries gone back over, a reload's X in place), each close to its card focused",
          not wrong, wrong)
    check(f"{tag}: no console error (the window's history)", not errors_of(page), errors_of(page)[:5])
    page.context.close()


# The grid's boxes and the header's (viewport px), for scroll bars that take room.
PAGE_BOXES = """() => [...document.querySelectorAll('#libGrid .lib-card, .masthead, #libHero')].map(n => (r => [r.left, r.top, r.width].map(v => Math.round(v * 10) / 10))(n.getBoundingClientRect()))"""


def part_window_edges(browser):
    """The review of 2026-11-15 where the other parts' browser does not go.  Scroll bars that take room (Chromium without
    --hide-scrollbars, as desktop Windows and Linux draw them), at 1440 x 900, light and dark: the Franka Hand's card
    (the grid scrolled to it) and the showcase's Details open the window with none of the grid's cards, the header or
    the title moving, the bar's width made up on the page's right (--lib-bar), the screen's right edge as dim as the
    backdrop elsewhere (scrollbar-gutter's room had stayed bright), the bar and the page as they were once it closes.
    A phone held sideways (844 x 390 and 740 x 360, touch) and a 390 x 844 phone in the dark scheme: the window a sheet
    over the whole screen with no shadow, its edges its own colour (the dark scheme's hairline had framed the screen)."""
    from PIL import Image

    bars = browser.browser_type.launch(args=WEBGL_ARGS, ignore_default_args=["--hide-scrollbars"])
    try:
        for scheme in ("light", "dark"):
            page = new_page(bars, 1440, 900, scheme)
            open_library(page)
            found = {}
            for selector in ("#gripper-franka-hand", ".lib-showcase-details"):
                page.locator(selector).first.evaluate("node => node.scrollIntoView({block: 'center'})"); page.wait_for_timeout(80)
                bar, before = page.evaluate("() => innerWidth - document.documentElement.clientWidth"), page.evaluate(PAGE_BOXES)
                page.locator(selector).first.click(); page.wait_for_timeout(400)
                during = page.evaluate(PAGE_BOXES)
                room = page.evaluate("() => getComputedStyle(document.documentElement).paddingRight")
                shot = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
                edge, left = shot.getpixel((1440 - 3, 450)), shot.getpixel((20, 450))
                if selector == "#gripper-franka-hand":
                    page.screenshot(path=f"{SHOTS}/library_window_bar_1440_{scheme}.png")
                page.click("#libClose"); page.wait_for_timeout(300)
                after, bar_after = page.evaluate(PAGE_BOXES), page.evaluate("() => innerWidth - document.documentElement.clientWidth")
                found[selector] = (bar > 0 and during == before and room == f"{bar}px" and max(abs(a - b) for a, b in zip(edge, left)) <= 1 and edge[0] < 200
                                   and after == before and bar_after == bar) or {"bar": bar, "moved": [(b, d) for b, d in zip(before, during) if b != d][:3],
                                                                                 "room": room, "edge": edge, "left": left, "after": after == before, "bar after": bar_after}
            check(f"bars {scheme}: with scroll bars that take room the window opens over the grid with nothing moving (cards, header, title), the bar's "
                  "width made up on the right, the screen's right edge as dim as the backdrop, the bar and the page as before once it closes",
                  all(value is True for value in found.values()), {key: value for key, value in found.items() if value is not True})
            check(f"bars {scheme}: no console error", not errors_of(page), errors_of(page)[:5])
            page.context.close()
    finally:
        bars.close()
    sheets = {}
    for width, height, scheme in ((844, 390, "light"), (740, 360, "dark"), (390, 844, "dark")):
        context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, is_mobile=True, has_touch=True, color_scheme="light")
        if scheme == "dark":
            context.add_init_script(DARK_CHOICE)
        page = context.new_page()
        page.goto(SITE["base"] + "#arx-x5-2mm")
        wait_until(page, READY, 30); page.wait_for_timeout(300)
        state = page.evaluate(WINDOW_STATE)
        shot = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        page.screenshot(path=f"{SHOTS}/library_window_sheet_{width}x{height}_{scheme}.png")
        inner = shot.getpixel((shot.width // 2, shot.height - 4))
        edges = [shot.getpixel(point) for point in ((0, shot.height // 2), (shot.width - 1, shot.height // 2), (shot.width // 2, shot.height - 1))]
        sheets[f"{width} x {height} {scheme}"] = (state["open"] and window_box_wrong(state, width, height) is None and all(edge == inner for edge in edges)) or {
            "box": window_box_wrong(state, width, height), "edges": edges, "inner": inner}
        context.close()
    check("sheets: a phone held sideways (844 x 390, 740 x 360) and a 390 x 844 phone in the dark scheme: the window a sheet over the whole "
          "screen, no shadow, its edges its own colour (no hairline frame)", all(value is True for value in sheets.values()),
          {key: value for key, value in sheets.items() if value is not True})


def part_errors(browser):
    page = new_page(browser)
    page.route("**/static/library/entries.json", lambda route: route.fulfill(status=404, content_type="text/plain", body="not here"))
    page.goto(SITE["base"])
    wait_until(page, READY, 30)
    status = page.evaluate("() => [document.getElementById('libStatus').textContent, document.getElementById('libStatus').getAttribute('role'), document.getElementById('libGrid').hidden]")
    check("errors: without entries.json the page says so (role alert), the grid hidden",
          status == ["The library could not be loaded (HTTP 404). Gen by Surface and Rectangular still work.", "alert", True], status)
    links = page.evaluate("() => [...document.querySelectorAll('.mode-links a, .masthead-library')].map(a => a.getAttribute('href'))")
    check("errors: the header's links still work (the generator at gen.html, the Library at ./ since 2026-11-16)", links == ["gen.html#rect", "gen.html", "./"], links)
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
          note == "The prebuilt Gerbers were not found; open the sensor in Gen by Surface to download them." and not page.query_selector("#libDetail .lib-pill"), note)
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
  const hint = host ? host.querySelector('.lib-drag') : null;
  return {state: s.state || null, build: s.build_id || null, img: Boolean(img), loading: img ? img.getAttribute('loading') : null,
    loaded: Boolean(img) && img.complete && img.naturalWidth > 0, picture: seen(img), live: seen(host) && seen(canvas),
    shot: box(shot), open: box(open), host: box(host), canvas: box(canvas), hint: hint ? Number(getComputedStyle(hint).opacity) : null}; }"""
CANVAS_BOX = "() => { const r = document.querySelector('#libDetail .lib-live canvas').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }"
ARIA = """() => { const host = document.querySelector('#libDetail .lib-live'); const img = document.querySelector('#libDetail .lib-shot-detail img');
  const hint = document.getElementById(host.getAttribute('aria-describedby') || ''); const canvas = host.querySelector('canvas');
  return {role: host.getAttribute('role'), label: host.getAttribute('aria-label'), alt: img ? img.getAttribute('alt') : null, tab: host.tabIndex,
          hint: hint ? hint.textContent : null, inside: Boolean(hint) && host.contains(hint), canvas: canvas ? canvas.getAttribute('aria-hidden') : null,
          touch: canvas ? getComputedStyle(canvas).touchAction : null, cursor: canvas ? getComputedStyle(canvas).cursor : null}; }"""
# The drag hint (the user's request of 2026-11-15: "箭头能不能做成像schetchfab一样的动画"): its opacity and visibility, its
# screen-reader state, its box against the host's (inside it, its bottom's distance, its centre's from the host's middle),
# what lies under its middle for the pointer (the view's canvas: a drag passes through it), its sway (the playing states
# of its lib-drag-sway animation), its label, its transition, and the host's is-used and its is-gone (null: no hint).
DRAG_HINT = """() => { const host = document.querySelector('#libDetail .lib-live'); const hint = host && host.querySelector('.lib-drag');
  if (!hint) return null; const r = hint.getBoundingClientRect(); const h = host.getBoundingClientRect(); const style = getComputedStyle(hint);
  const label = hint.querySelector('.lib-drag-label'); const x = r.left + r.width / 2, y = r.top + r.height / 2; const under = document.elementFromPoint(x, y);
  return {opacity: Number(style.opacity), visible: style.visibility === 'visible' && getComputedStyle(hint.querySelector('svg')).visibility === 'visible',
          hidden: hint.getAttribute('aria-hidden'), centre: [x, y], size: [Math.round(r.width), Math.round(r.height)],
          inside: r.left >= h.left && r.right <= h.right && r.top >= h.top && r.bottom <= h.bottom, bottom: Math.round(h.bottom - r.bottom),
          offset: Math.round((x - (h.left + h.width / 2)) * 10) / 10, through: Boolean(under) && under.tagName === 'CANVAS' && host.contains(under),
          sway: hint.getAnimations().filter(a => a.animationName === 'lib-drag-sway').map(a => a.playState), label: label && label.checkVisibility() ? label.textContent : null,
          transition: style.transitionDuration, used: host.classList.contains('is-used'), gone: hint.classList.contains('is-gone'),
          view: Math.round(h.height * 10) / 10, drawing: (d => [Math.round(d.width * 10) / 10, Math.round(d.height * 10) / 10])(hint.querySelector('svg').getBoundingClientRect())}; }"""
# The drag hint's size from its view's (library.css .lib-drag, the review of 2026-11-15): for a view ``height`` px tall, the
# drawing's height (13.4 % of it between 28 and 44 px; its width the viewBox's 84:44), its distance from the view's bottom
# and its sway's reach in proportion (14 and 30 px at 44), and its label shown on a view 270 px tall or more (over 269 px:
# @container lib-live (max-height:269px) hides it).
def hint_size(height):
    drawing = min(44.0, max(28.0, 0.134 * height))
    return {"drawing": [drawing * 84 / 44, drawing], "bottom": drawing * 14 / 44, "reach": drawing * 30 / 44, "label": height > 269}


def hint_fits(hint, size=None):
    """Whether ``hint`` (DRAG_HINT) has the size of its view's (hint_size), within a pixel."""
    size = size or hint_size(hint["view"])
    return (all(abs(a - b) <= 1 for a, b in zip(hint["drawing"], size["drawing"])) and abs(hint["bottom"] - size["bottom"]) <= 1
            and (hint["label"] == "Drag to rotate") == size["label"] and hint["inside"])


# The hint's centre from the host's middle at its sway's start, a quarter and a half of the way (paused there, then played).
HINT_SWAY = """() => { const host = document.querySelector('#libDetail .lib-live'); const hint = host.querySelector('.lib-drag');
  const sway = hint.getAnimations().find(a => a.animationName === 'lib-drag-sway'); if (!sway) return null; const h = host.getBoundingClientRect();
  const at = time => { sway.pause(); sway.currentTime = time; const r = hint.getBoundingClientRect(); return Math.round((r.left + r.width / 2 - (h.left + h.width / 2)) * 10) / 10; };
  const out = [at(0), at(1250), at(2500)]; sway.play(); return out; }"""
RING = """() => { const host = document.querySelector('#libDetail .lib-live'); const style = getComputedStyle(host);
  return {focused: document.activeElement === host, visible: host.matches(':focus-visible'), style: style.outlineStyle,
          width: parseFloat(style.outlineWidth), colour: style.outlineColor}; }"""
GROUNDS = """() => ({slot: getComputedStyle(document.querySelector('#libDetail .lib-shot-detail')).backgroundColor,
  host: getComputedStyle(document.querySelector('#libDetail .lib-live')).backgroundColor})"""
SHOTS_MANIFEST = (json.loads((LIBRARY / library_write.SHOTS_MANIFEST).read_text(encoding="utf-8")).get("shots", {})
                  if (LIBRARY / library_write.SHOTS_MANIFEST).is_file() else {})


# Routes of the view's pages: (glob, content type, body), each served in place of the server's file (tools/browser/
# mutants.py's lib kind: library_view.js or library_stage.js mutated).
ROUTES = []


def served(content_type, body):
    return lambda route, request=None: route.fulfill(status=200, content_type=content_type, body=body)


def view_page(browser, width=1440, height=900, scheme="light", scripts=(), mobile=False):
    """A page as new_page's, its frames and draws counted (COUNTERS), ``scripts`` run first; ``mobile``: a phone's
    (touch, DPR 3), else DPR 2."""
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme="light", device_scale_factor=3 if mobile else 2,
                                  is_mobile=mobile, has_touch=mobile)
    for glob, content_type, body in ROUTES:
        context.route(glob, served(content_type, body))
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
    page.goto(SITE["base"] + f"?probe#{key}")
    wait_until(page, READY, 30)
    return view_settled(page, key) if settle else None


def load_samples(page, key):
    """``key``'s page opened with ?probe, what it shows sampled every few ms until its view settles."""
    page.goto(SITE["base"] + f"?probe#{key}")
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


# A turn of ``presses`` times ArrowLeft (5 degrees each) on the view, then the canvas read in the frame it is drawn in
# (the turn asks for that frame; three.js keeps no drawing buffer, so a frame later the read is blank).
TURNED_READ = """async (presses) => {
  const host = document.querySelector('#libDetail .lib-live');
  const canvas = host.querySelector('canvas');
  for (let k = 0; k < presses; k += 1) host.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowLeft', bubbles: true, cancelable: true}));
  const url = await new Promise(resolve => requestAnimationFrame(() => resolve(canvas.toDataURL('image/png'))));
  return {url, moved: JSON.parse(document.getElementById('libViewState').textContent).moved};
}"""


def edge_pixels(png):
    """How many pixels of a canvas read (a PNG with the drawing's alpha) are drawn on its two outer rows and columns, or
    None for a read with nothing drawn (a frame missed: no proof of anything)."""
    from PIL import Image
    alpha = Image.open(io.BytesIO(png)).getchannel("A")
    if alpha.getbbox() is None:
        return None
    width, height = alpha.size
    rows = [(x, y) for y in (0, 1, height - 2, height - 1) for x in range(width)]
    columns = [(x, y) for x in (0, 1, width - 2, width - 1) for y in range(2, height - 2)]
    return sum(1 for point in rows + columns if alpha.getpixel(point) > 0)


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
    return {"margins": [margins(one), margins(two)], "mean": round(math.fsum(mean) / 3, 3) if count else None, "share": round(count / max(1, total), 4),
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
                  "never neither; the drag hint never shown before the view is drawn (the review of 2026-11-15)",
                  shown and drawn and loaded and loaded[0] <= drawn[0] and shown[0]["loading"] is None and shown[0]["img"]
                  and all(not sample["live"] and (sample["picture"] or not sample["loaded"]) and not sample["hint"] for sample in before)
                  and last["state"] == "drawn" and last["live"] and not last["picture"],
                  {"samples": len(samples), "first": shown[0] if shown else None, "last": last,
                   "hint before drawn": [sample["hint"] for sample in before if sample["hint"]][:3]})
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
            # centred()): the drawing, already in the middle, is written as the shots tool writes a picture (its webp(), so
            # the picture's lossy WebP is on both sides) and compared with it, never centred a second time (the review of
            # 2026-11-06: encode()'s centred() had moved UMI 2 mm's Assembled drawing down 1 px for two pixels of alpha 18
            # in a row above it, mean 3.656 against 0.975 unmoved).  An odd lens shift antialiases the edges at other places
            # than the shots tool's whole-pixel paste: over the 42 sensors' 84 homes, unmoved, the mean up to 1.27 levels,
            # 99.7 % or more of the pixels within 16.
            if comparable(key):
                reads = home_reads(page)
                compared = {mode: None for mode in library_shots.MODES}
                if sorted(reads) == sorted(library_shots.MODES):
                    from PIL import Image
                    files = {mode: library_shots.webp(Image.open(io.BytesIO(reads[mode]["png"]))) for mode in library_shots.MODES}
                    for mode in library_shots.MODES:
                        picture = page.request.get(SITE["base"] + "static/library/" + IMAGES[key][mode]["src"]).body()
                        compared[mode] = dict(likeness(files[mode], picture), margins=likeness(reads[mode]["png"], picture)["margins"],
                                              same=files[mode] == picture, offset=reads[mode]["state"].get("offset"),
                                              home=(reads[mode]["state"].get("drawn_mode"), reads[mode]["state"].get("moved")))
                check(f"view {name}: at each home the view's drawing stands where its picture's does (margins within 1 px, at the pictures' 1280 x 800, "
                      "moved to the middle by its own lens shift) and is its picture (written as the shots tool writes one: the colours of the pixels "
                      "both draw opaque within 1.5 levels on average, 99 % of them within 16, over 99 % of the picture's)",
                      all(item and item["margins"] and all(abs(a - b) <= 1 for a, b in zip(*item["margins"])) and item["mean"] is not None
                          and item["mean"] < 1.5 and item["close"] >= 0.99 and item["share"] >= 0.99 and item["home"] == (mode, False)
                          for mode, item in compared.items()), compared)
            else:
                print(f"    view {name}: its picture is not its 3D view's (shot before the view): drawing and picture not compared", flush=True)
            box = page.evaluate(CANVAS_BOX)
            centre = (box[0] + box[2] / 2, box[1] + box[3] / 2)
            state = lambda: page.evaluate(LIB_STATE)  # noqa: E731
            turned = {}
            # The drag hint (the user's request of 2026-11-15): shown once the view is drawn (faded in), at the view's bottom
            # centre, swaying side to side; a drag begun on it turns the view and hides it (faded out, its sway then stopped).
            page.wait_for_timeout(300)
            hint = page.evaluate(DRAG_HINT)
            sway = page.evaluate(HINT_SWAY) if hint else None
            page.screenshot(path=f"{SHOTS}/library_view_{key}_{size}_hint.png")
            on_hint = right = None
            if hint:
                # A right click turns nothing, so leaves it (the review of 2026-11-15).
                page.mouse.click(box[0] + box[2] / 2, box[1] + box[3] / 3, button="right"); page.wait_for_timeout(1100)
                right = page.evaluate(DRAG_HINT)
                page.mouse.move(*hint["centre"]); page.mouse.down(); page.mouse.move(hint["centre"][0] - min(120, box[2] / 3), hint["centre"][1] - 10, steps=8)
                page.mouse.up(); page.wait_for_timeout(150)
                on_hint = state()["moved"]
                page.wait_for_timeout(1100)
                gone = page.evaluate(DRAG_HINT)
                page.focus("#libDetail .lib-live"); page.keyboard.press("0"); page.wait_for_timeout(120)
            # Its size the view's (the view 330 px tall at 1440 x 900: the drawing 84 x 44, 14 px up, 30 px either way, its label;
            # 113 px at 390 x 844: 54 x 28 at its floor, about 9 px up, 19 px either way, no label).
            want = hint_size(hint["view"]) if hint else None
            expected = (want["drawing"][1] == 44 and want["label"]) if width >= 900 else (want["drawing"][1] == 28 and not want["label"]) if want else False
            check(f"view {name}: the drag hint shown once the view is drawn (opacity 1), hidden from a screen reader, at the view's bottom centre, inside it, "
                  f"sized by the view ({hint and hint['view']} px tall: the drawing {want and [round(v, 1) for v in want['drawing']]} px, "
                  f"{want and round(want['bottom'], 1)} px up, label {want and want['label']}, swaying {want and round(want['reach'], 1)} px either way, running); "
                  "a right click leaving it; over the canvas yet letting a drag through (a drag begun on it turns the view), which hides it (faded out, its sway stopped)",
                  bool(hint) and expected and hint["opacity"] == 1 and hint["visible"] and hint["hidden"] == "true" and hint_fits(hint)
                  and hint["sway"] == ["running"] and hint["through"] and not hint["used"]
                  and sway and abs(sway[0] + want["reach"]) <= 1.5 and abs(sway[1]) <= 1 and abs(sway[2] - want["reach"]) <= 1.5
                  and right and right["opacity"] == 1 and not right["used"] and right["sway"] == ["running"]
                  and on_hint is True and gone["opacity"] == 0 and gone["used"] and gone["gone"] and gone["sway"] == [],
                  {"hint": hint, "want": want, "sway": sway, "right click": right, "on hint": on_hint, "after": hint and gone})
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
            still = page.evaluate(DRAG_HINT)
            check(f"view {name}: the drag hint stays hidden on the page through 0, the arrow keys and a double click (no sway)",
                  still and still["opacity"] == 0 and still["sway"] == [], still)
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
            # Turned, the drawing kept whole (library_view.js fitLens; the verification of 2026-11-13: half-way round, the UMI
            # finger's Assembled tip left the canvas, a third of the way round the YAM's base): in each mode, turned 120,
            # 180 and 240 degrees with ArrowLeft, no drawn pixel on the drawing buffer's two outer rows and columns.
            edges = {}
            for mode in ("assembled", "exploded"):
                page.click(f"#libDetail .lib-view label:has(input[value='{mode}'])")
                library_shots.poll(page, "(mode) => { const s = JSON.parse(document.getElementById('libViewState').textContent); return s.drawn_mode === mode; }", mode, 10)
                for deg, turn in ((120, 24), (180, 12), (240, 12)):
                    read = page.evaluate(TURNED_READ, turn)
                    edges[f"{mode} {deg}"] = edge_pixels(base64.b64decode(read["url"].split(",", 1)[1])) if read["moved"] else None
                page.focus("#libDetail .lib-live"); page.keyboard.press("0"); page.wait_for_timeout(120)
            check(f"view {name}: turned 120, 180 and 240 degrees in both modes, the drawing stays whole on the canvas (no drawn pixel on its edge)",
                  len(edges) == 6 and all(count == 0 for count in edges.values()), edges)
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
                # The review of 2026-11-06: the few pointermoves before the browser took a vertical swipe for the page's
                # scroll had turned the view (a gripper edge-on after one swipe); from home, two vertical swipes (one in
                # steps of 4 px, under the figure's slop) leave it at home, a sideways one turns it.  Since the window of
                # 2026-11-15 the swipe scrolls the window's page, never the grid under it.
                page.focus("#libDetail .lib-live"); page.keyboard.press("0"); page.wait_for_timeout(120)
                page.evaluate("() => { document.activeElement?.blur(); document.getElementById('libWindowBody').scrollTop = 0; }"); page.wait_for_timeout(100)
                before = state()["moved"]
                box = page.evaluate(CANVAS_BOX)
                top, grid_y = page.evaluate("() => [document.getElementById('libWindowBody').scrollTop, scrollY]")
                swipe(page, (box[0] + box[2] / 2, box[1] + box[3] / 2 + 20), (0, -12))
                page.wait_for_timeout(400)
                scrolled, grid_moved = page.evaluate("([top, y]) => [document.getElementById('libWindowBody').scrollTop - top, scrollY - y]", [top, grid_y])
                page.evaluate(WINDOW_TOP); page.wait_for_timeout(150)
                box = page.evaluate(CANVAS_BOX)
                swipe(page, (box[0] + box[2] / 2 + 2, box[1] + box[3] / 2 + 20), (1, -4), count=12)
                page.wait_for_timeout(400)
                stayed = state()["moved"]
                page.evaluate(WINDOW_TOP); page.wait_for_timeout(150)
                box = page.evaluate(CANVAS_BOX)
                swipe(page, (box[0] + box[2] / 2 - 60, box[1] + box[3] / 2), (15, 0))
                page.wait_for_timeout(300)
                page.screenshot(path=f"{SHOTS}/library_view_{key}_{size}_swiped.png")
                check(f"view {name}: a vertical swipe on the view scrolls the window's page (never the grid under it) and leaves the view at home, "
                      "a sideways one turns the view",
                      scrolled >= 40 and grid_moved == 0 and before is False and stayed is False and state()["moved"] is True,
                      {"scrolled": scrolled, "grid moved": grid_moved, "home before": not before, "turned by the vertical swipes": stayed, "turned": state()["moved"]})
            # The drag hint as the page has it: another pitch of the same gripper keeps it hidden; another gripper's page shows
            # it again, a turning key hides it; under reduced motion, back on the first page, it shows still (no sway, no
            # fade) and a press hides it at once.
            page.focus("#libDetail .lib-live")
            page.click("#libDetail input[name='libPitch']:not(:checked)")
            pitch = page.evaluate("() => decodeURIComponent(location.hash.slice(1))")
            view_settled(page, pitch); page.wait_for_timeout(300)
            pitched = page.evaluate(DRAG_HINT)
            other = VIEW_UMI if key == VIEW_GRIPPER else VIEW_GRIPPER
            page.evaluate("(key) => { location.hash = '#' + key; }", other)
            view_settled(page, other); page.wait_for_timeout(300)
            again = page.evaluate(DRAG_HINT)
            page.focus("#libDetail .lib-live"); page.keyboard.press("ArrowLeft"); page.wait_for_timeout(150)
            keyed = (state()["moved"], page.evaluate(DRAG_HINT)["used"])
            page.wait_for_timeout(1100)
            keyed += (page.evaluate(DRAG_HINT)["opacity"],)
            page.emulate_media(reduced_motion="reduce")
            page.evaluate("(key) => { location.hash = '#' + key; }", key)
            view_settled(page, key); page.wait_for_timeout(60)
            still_hint = page.evaluate(DRAG_HINT)
            box = page.evaluate(CANVAS_BOX)
            page.mouse.move(box[0] + box[2] / 2, box[1] + box[3] / 3); page.mouse.down(); page.mouse.up(); page.wait_for_timeout(60)
            pressed = page.evaluate(DRAG_HINT)
            page.emulate_media(reduced_motion="no-preference")
            check(f"view {name}: the drag hint stays hidden for another pitch of the gripper, shows again (swaying) on another gripper's page, where "
                  "a turning key hides it; under reduced motion shown still (no sway, no transition) and hidden at once by a press",
                  pitched and pitched["opacity"] == 0 and pitched["used"] and again and again["opacity"] == 1 and again["sway"] == ["running"] and not again["used"]
                  and keyed == (True, True, 0) and still_hint and still_hint["opacity"] == 1 and still_hint["sway"] == [] and still_hint["transition"] == "0s"
                  and pressed["opacity"] == 0 and pressed["used"],
                  {"pitch": pitch, "pitched": pitched, "again": again, "keyed": keyed, "reduced": still_hint, "pressed": pressed})
            engine = [url for url in page.requests if re.search(r"/api/|/py/|pyodide|backend\.js|(^|/)app\.js", url)]
            check(f"view {name}: no request for the server's API, py/, Pyodide, backend.js or app.js; no console error",
                  not engine and not errors_of(page), (engine[:3], errors_of(page)[:3]))
            page.context.close()
        hint_paths(browser, width, height, mobile)
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
              and (then or {}).get("gripper") is False and ((then or {}).get("stage") or {}).get("numbers", 0) is None
              and ((then or {}).get("stage") or {}).get("home") == ((own or {}).get("stage") or {}).get("home")
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


# A lost WebGL context for the drag hint's paths (the extension's loseContext, then its restoreContext, on the view's canvas;
# part_looks's LOSE_CONTEXT does both at once).
HINT_LOSE = """() => { const canvas = document.querySelector('#libDetail .lib-live canvas'); const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
  window.__libLose = gl.getExtension('WEBGL_lose_context'); window.__libLose.loseContext(); }"""
HINT_RESTORE = "() => { window.__libLose.restoreContext(); }"
STAGE_LIVE = "() => Boolean(document.querySelector('#libDetail .lib-stage.is-live'))"
# The view of ``key`` (a variant's or the showcase's id) drawn.
DRAWN_ID = "(key) => { const node = document.getElementById('libViewState'); const s = node && node.textContent ? JSON.parse(node.textContent) : null; return Boolean(s) && s.id === key && s.state === 'drawn'; }"


def hint_paths(browser, width, height, mobile):
    """The drag hint's paths its review of 2026-11-15 found unchecked, on Trossen WidowX AI's page opened from its card: a
    lost WebGL context hides it with the view and, restored, shows it again while the view was not used; on a phone a
    vertical swipe that scrolls the window leaves it and a sideways one (a touch's turn) hides it (elsewhere a turning
    key); restored after that use, it stays hidden; Back (the grid) then Forward (the window opened again) shows it."""
    size = f"{width}"
    page = view_page(browser, width, height, mobile=mobile)
    library_case(page, "pictures", view=True)
    page.goto(SITE["base"] + "?probe")
    wait_until(page, READY, 30)
    page.click("#gripper-trossen-widowx-ai")
    view_settled(page, VIEW_GRIPPER); page.wait_for_timeout(300)
    state = lambda: page.evaluate(LIB_STATE)  # noqa: E731

    def round_trip():
        # Lost (the picture shown again, the hint with the view), then restored and drawn again.
        page.evaluate(HINT_LOSE); page.wait_for_timeout(300)
        lost = (state()["state"], page.evaluate(STAGE_LIVE), page.evaluate(DRAG_HINT)["opacity"])
        page.evaluate(HINT_RESTORE)
        library_shots.poll(page, DRAWN_ID, VIEW_GRIPPER, 60); page.wait_for_timeout(400)
        return lost, (state()["state"], page.evaluate(STAGE_LIVE), page.evaluate(DRAG_HINT))

    before = round_trip()
    if mobile:
        page.evaluate(WINDOW_TOP); page.wait_for_timeout(150)
        box = page.evaluate(CANVAS_BOX)
        top = page.evaluate("() => document.getElementById('libWindowBody').scrollTop")
        swipe(page, (box[0] + box[2] / 2, box[1] + box[3] / 2 + 10), (0, -10))
        page.wait_for_timeout(1100)
        vertical = (page.evaluate("() => document.getElementById('libWindowBody').scrollTop") - top, state()["moved"], page.evaluate(DRAG_HINT))
        page.evaluate(WINDOW_TOP); page.wait_for_timeout(150)
        box = page.evaluate(CANVAS_BOX)
        swipe(page, (box[0] + box[2] / 2 - 60, box[1] + box[3] / 2), (15, 0))
        page.wait_for_timeout(1100)
        use = (state()["moved"], page.evaluate(DRAG_HINT))
        check(f"view {size}: on a phone a vertical swipe over the view that scrolls the window leaves the drag hint (shown, swaying, the view at "
              "home: the review of 2026-11-15); a sideways one turns the view and hides it (faded out, its sway stopped)",
              vertical[0] >= 40 and vertical[1] is False and vertical[2]["opacity"] == 1 and not vertical[2]["used"] and vertical[2]["sway"] == ["running"]
              and use[0] is True and use[1]["opacity"] == 0 and use[1]["used"] and use[1]["gone"] and use[1]["sway"] == [],
              {"vertical (scrolled, turned, hint)": vertical, "sideways (turned, hint)": use})
    else:
        page.focus("#libDetail .lib-live"); page.keyboard.press("ArrowLeft"); page.wait_for_timeout(1100)
        use = (state()["moved"], page.evaluate(DRAG_HINT))
    after = round_trip()
    check(f"view {size}: a lost WebGL context hides the drag hint with the view (the picture shown); restored and drawn again, the hint shows "
          "while the view was not used (swaying), stays hidden once it was",
          before[0] == ("lost", False, 0) and before[1][:2] == ("drawn", True) and before[1][2]["opacity"] == 1 and not before[1][2]["used"]
          and before[1][2]["sway"] == ["running"] and use[0] is True and use[1]["used"]
          and after[0] == ("lost", False, 0) and after[1][:2] == ("drawn", True) and after[1][2]["opacity"] == 0 and after[1][2]["used"],
          {"before a use (lost, restored)": before, "used": use, "after a use (lost, restored)": after})
    page.go_back(); page.wait_for_timeout(300)
    grid = page.evaluate("() => document.getElementById('libWindow').open")
    page.go_forward()
    view_settled(page, VIEW_GRIPPER); page.wait_for_timeout(300)
    again = page.evaluate(DRAG_HINT)
    check(f"view {size}: after a use, Back (the grid) then Forward (the window opened again) shows the drag hint again (swaying)",
          grid is False and again and again["opacity"] == 1 and not again["used"] and again["sway"] == ["running"], {"window open after Back": grid, "hint": again})
    check(f"view {size}: the drag hint's paths with no console error", not errors_of(page), errors_of(page)[:3])
    page.context.close()


def part_view_hint_sizes(browser):
    """The drag hint sized by its view, not the window (the review of 2026-11-15: by the window's width, below 900 px a
    tablet's wide 3:1 view 685 x 228 px and the showcase's tall one on a phone had the small hint without its label, and a
    900 px window's 355 x 222 px view the full one over its gripper's base): Unitree Dex1's view (16:10 from 900 px, 3:1
    below) and the showcase's (4:5) at nine windows, the drawing, its distance from the bottom, its label and its reach
    the view's (hint_size), inside it."""
    if not any(arts(browser).values()):
        check("view sizes: the 3D view's art is there for the sensors entries.json gives a view", not VIEWED, "a built site before the shoot")
        return
    windows = ((1440, 900, False), (1280, 800, False), (1100, 800, False), (1024, 768, False), (900, 900, False), (820, 1180, True),
               (1180, 820, True), (390, 844, True), (320, 640, True))
    for key in ("unitree-dex1-2mm", "flexitac-g1"):
        rows = []
        for width, height, mobile in windows:
            page = view_page(browser, width, height, mobile=mobile)
            library_case(page, "pictures", view=True)
            page.goto(SITE["base"] + f"?probe#{key}")
            wait_until(page, READY, 30)
            library_shots.poll(page, DRAWN_ID, key, 150)
            page.wait_for_timeout(300)
            hint = page.evaluate(DRAG_HINT)
            sway = page.evaluate(HINT_SWAY) if hint else None
            want = hint_size(hint["view"]) if hint else None
            rows.append((f"{width}x{height}", bool(hint) and hint_fits(hint, want) and hint["opacity"] == 1 and sway is not None
                         and abs(sway[0] + want["reach"]) <= 1.5 and abs(sway[2] - want["reach"]) <= 1.5,
                         hint and hint["view"], hint and hint["drawing"], hint and hint["bottom"], hint and hint["label"], sway))
            page.context.close()
        by_view = {row[0]: (row[2], row[3][1] if row[3] else None, row[5]) for row in rows}
        check(f"view sizes, {key}: at nine windows the drag hint the view's (the drawing 13.4 % of its height, 28 to 44 px; its distance, label "
              "(on a view 270 px tall or more) and reach in proportion), inside it",
              all(row[1] for row in rows), {"failed": [row for row in rows if not row[1]], "by window (view height, drawing height, label)": by_view})


# The race (the review of 2026-11-06): a sensor's page whose view is asked for again and again while its files load (a slow
# network: 400 kbit/s, 150 ms), each time another sensor's or the other mode, ends with the last one asked drawn exactly as a
# fresh page draws it (library_view.js: a later show wins; the stage's scene of a gripper taken down for the next).  In the
# last, a sensor whose files are slow to come (Unitree Dex1's part and bodies, 1.4 MB) is left for one already drawn
# (Franka Hand's, whose bodies the view keeps), which is drawn first: the files of the one left land after it.
RACE_PITCHES = ("trossen-widowx-ai-1.5mm", VIEW_UMI, "trossen-widowx-ai-3mm", "arx-x5-2mm", VIEW_GRIPPER)
RACE_GRID = (("click", "#gripper-trossen-widowx-ai"), ("back", None), ("forward", None), ("back", None), ("click", "#gripper-arx-x5"),
             ("back", None), ("forward", None), ("back", None), ("click", "#gripper-trossen-widowx-ai"))
RACE_SLOW, RACE_FAST = "unitree-dex1-2mm", "franka-hand-2mm"


def throttled(page, on):
    session = page.context.new_cdp_session(page)
    session.send("Network.enable")
    session.send("Network.emulateNetworkConditions", {"offline": False, "latency": 150 if on else 0, "downloadThroughput": 400 * 1024 / 8 if on else -1,
                                                      "uploadThroughput": 400 * 1024 / 8 if on else -1})
    return session


def race_read(page, key):
    """The view of ``key`` at its Exploded home as a PNG (its host at the pictures' pane), with its state, or (None, state)."""
    settled = view_settled(page, key, 240) or {}
    if settled.get("state") != "drawn":
        return None, settled
    page.click("#libDetail .lib-view label:has(input[value='exploded'])")
    page.wait_for_timeout(300)
    page.focus("#libDetail .lib-live"); page.keyboard.press("0"); page.wait_for_timeout(200)
    reads = home_reads(page)
    return (reads.get("exploded") or {}).get("png"), page.evaluate(LIB_STATE)


def part_view_race(browser):
    """The Library's 3D view asked for again and again while its files load (the review of 2026-11-06): on a slow network,
    five pitch and part changes with four mode toggles during each load, Back and Forward between the grid and two
    grippers' pages, and a slow sensor left for one drawn at once; each time the sensor asked last is drawn as a fresh
    page draws it (every pixel), its state that sensor's, no error."""
    if not any(arts(browser).values()):
        check("view race: the 3D view's art is there for the sensors entries.json gives a view", not VIEWED, "a built site without the shoot's art/")
        return
    from PIL import Image, ImageChops

    references = {}
    for key in (VIEW_GRIPPER, RACE_FAST):
        page = view_page(browser)
        library_case(page, "pictures", view=True)
        open_view(page, key)
        references[key], _ = race_read(page, key)
        page.context.close()
    for scenario, last in (("pitches", VIEW_GRIPPER), ("grid", VIEW_GRIPPER), ("slow first", RACE_FAST)):
        page = view_page(browser)
        library_case(page, "pictures", view=True)
        if scenario == "slow first":
            open_view(page, RACE_FAST)
        session = throttled(page, True)
        if scenario == "pitches":
            page.goto(SITE["base"] + "?probe#trossen-widowx-ai-1mm")
            page.wait_for_selector("#libDetail .lib-seg input[name=libPitch]", state="attached", timeout=60000)
            for target in RACE_PITCHES:
                page.wait_for_timeout(350)
                page.evaluate("(target) => { location.hash = target; }", target)
                page.wait_for_timeout(120)
                for mode in ("assembled", "exploded", "assembled", "exploded"):
                    radio = page.query_selector(f"#libDetail .lib-view label:has(input[value='{mode}'])")
                    if radio:
                        radio.click()
                    page.wait_for_timeout(30)
        elif scenario == "grid":
            page.goto(SITE["base"] + "?probe")
            page.wait_for_selector("#gripper-trossen-widowx-ai", timeout=60000)
            for action, target in RACE_GRID:
                if action == "click":
                    page.click(target)
                elif action == "back":
                    page.go_back()
                else:
                    page.go_forward()
                page.wait_for_timeout(200)
        else:
            page.evaluate("(target) => { location.hash = target; }", RACE_SLOW)
            page.wait_for_timeout(300)
            page.evaluate("(target) => { location.hash = target; }", RACE_FAST)
            view_settled(page, RACE_FAST, 120)
        session.send("Network.emulateNetworkConditions", {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})
        if scenario == "slow first":
            page.wait_for_timeout(3000)  # the slow sensor's files land
        test, settled = race_read(page, last)
        same = None
        if references[last] and test:
            one, two = (Image.open(io.BytesIO(data)).convert("RGBA") for data in (references[last], test))
            same = one.size == two.size and ImageChops.difference(one, two).getbbox() is None
        check(f"view race ({scenario}): the sensor asked last ({last}) drawn at its home exactly as a fresh page draws it (every pixel), "
              "its state that sensor's, no console error",
              same is True and settled.get("id") == last and settled.get("drawn_mode") == "exploded" and not settled.get("moved")
              and not errors_of(page), ({key: settled.get(key) for key in ("state", "id", "drawn_mode", "moved", "gripper")}, same, errors_of(page)[:3]))
        page.context.close()


# The looks (docs/LIBRARY_VIEW.md "The looks"; the user's request of 2026-11-12).  LOOK_GRIPPER: the first gripper's 2 mm
# sensor whose committed scene has looks (None before any has); LOOK_METRE: a gripper whose part's file is in metres (the
# stage welds the part's corners for its smooth normals in mm: the review of 2026-11-12), its scene served here with a
# look for the part and a crease angle.
def looked_gripper():
    for part in ENTRIES["order"]:
        path = SCENES.get(part)
        if path and (LIBRARY / path).is_file() and "looks" in json.loads((LIBRARY / path).read_text(encoding="utf-8")) and f"{part}-2mm" in ENTRIES["variants"]:
            return f"{part}-2mm"
    return None


LOOK_METRE = "unitree-dex1-2mm"
LOOK_METRE_SCENE = {"looks": {"metal": {"color": "#c9ccd0", "metalness": 1, "roughness": 0.45}}, "part_look": "metal", "smooth_deg": 35}
UNIT_SCALES_MM = {"m": 1000, "cm": 10, "mm": 1, "in": 25.4}
LOSE_CONTEXT = """async () => {
  const gl = document.querySelector('#libDetail .lib-live canvas').getContext('webgl2');
  const lose = gl && gl.getExtension('WEBGL_lose_context');
  if (!lose) return 'no WEBGL_lose_context';
  lose.loseContext();
  await new Promise(resolve => setTimeout(resolve, 400));
  const state = JSON.parse(document.getElementById('libViewState').textContent).state;
  lose.restoreContext();
  return state;
}"""


def part_points(part):
    """How many points the corners of a part's mesh share at 1 um (the stage's weld for its smooth normals: each
    coordinate in mm times 1000, rounded as JavaScript rounds)."""
    import struct

    mesh = ENTRIES["parts"][part]["mesh"]
    data = (LIBRARY / mesh["file"]).read_bytes()
    cell = 1e3 * UNIT_SCALES_MM[mesh["unit"]]
    points = set()
    for index in range(struct.unpack_from("<I", data, 80)[0]):
        values = struct.unpack_from("<9f", data, 84 + 50 * index + 12)
        for corner in range(3):
            points.add(tuple(math.floor(value * cell + 0.5) for value in values[3 * corner:3 * corner + 3]))
    return len(points)


def same_drawings(one, two):
    """Whether two home_reads() are the same drawings at both homes, every pixel (likeness: the margins, the colours,
    the opaque pixels)."""
    compared = {mode: mode in one and mode in two and likeness(one[mode]["png"], two[mode]["png"]) for mode in library_shots.MODES}
    return all(item and item["margins"][0] == item["margins"][1] and item["mean"] == 0 and item["share"] == 1 for item in compared.values()), compared


def part_looks(browser):
    """The looks of a gripper's scene in the 3D view (the user's request of 2026-11-12; the reviews of 2026-11-12: the
    stage's look code had no check in a browser)."""
    if not any(arts(browser).values()):
        check("looks: the 3D view's art is there for the sensors entries.json gives a view", not VIEWED, "a built site without the shoot's art/")
        return
    from PIL import Image

    key = looked_gripper()
    if key is None:
        print("    looks: no gripper's scene has looks yet: its checks left out", flush=True)
    else:
        variant = ENTRIES["variants"][key]
        name = variant["label"]
        scene = json.loads((LIBRARY / SCENES[variant["part"]]).read_text(encoding="utf-8"))
        page = view_page(browser)
        library_case(page, "pictures", view=True)
        settled = open_view(page, key) or {}
        looks = (settled.get("stage") or {}).get("looks")
        expected = {"bodies": sorted({body["look"] for body in scene["bodies"] if body.get("look")}), "part": scene.get("part_look"),
                    "smooth_deg": scene.get("smooth_deg"), "part_points": part_points(variant["part"]) if "smooth_deg" in scene else None}
        noise = [entry[:2] for entry in page.logs if entry[0] in ("error", "pageerror") or (entry[0] == "warning" and "GL Driver Message" not in entry[1])]
        check(f"looks {name}: the view drawn, its stage's looks the scene's (the bodies' looks by name, the part's, the crease angle, the part's "
              "corners sharing its file's points at 1 um); no console error or warning",
              settled.get("state") == "drawn" and looks == expected and not noise, (settled.get("state"), looks, expected, noise[:3]))
        fresh = home_reads(page)
        page.screenshot(path=f"{SHOTS}/library_looks_{key}_home.png")
        if comparable(key):
            compared = {mode: None for mode in library_shots.MODES}
            if sorted(fresh) == sorted(library_shots.MODES):
                for mode in library_shots.MODES:
                    picture = page.request.get(SITE["base"] + "static/library/" + IMAGES[key][mode]["src"]).body()
                    compared[mode] = dict(likeness(library_shots.webp(Image.open(io.BytesIO(fresh[mode]["png"]))), picture),
                                          margins=likeness(fresh[mode]["png"], picture)["margins"])
            check(f"looks {name}: at each home the view's drawing is its picture (as part_view compares one: margins within 1 px, the colours "
                  "within 1.5 levels on average, 99 % of them within 16, over 99 % of the picture's)",
                  all(item and item["margins"] and all(abs(a - b) <= 1 for a, b in zip(*item["margins"])) and item["mean"] is not None
                      and item["mean"] < 1.5 and item["close"] >= 0.99 and item["share"] >= 0.99 for item in compared.values()), compared)
        else:
            print(f"    looks {name}: its picture is not its 3D view's: drawing and picture not compared", flush=True)
        # Its WebGL context lost and back: drawn again as before (the gripper studio is a render target of the context).
        lost = page.evaluate(LOSE_CONTEXT)
        page.wait_for_timeout(500)
        again = view_settled(page, key) or {}
        back = home_reads(page) if again.get("state") == "drawn" else {}
        same, detail = same_drawings(fresh, back)
        check(f"looks {name}: its WebGL context lost (the picture shown) and back: drawn again exactly as before (every pixel at both homes), "
              "no console error", lost == "lost" and again.get("state") == "drawn" and same and not errors_of(page), (lost, again.get("state"), detail, errors_of(page)[:3]))
        page.context.close()
        # The same scene without its looks: the one grey of before, far from the drawing with them.
        plain = {name_: value for name_, value in scene.items() if name_ not in ("looks", "part_look", "smooth_deg")}
        plain["bodies"] = [{name_: value for name_, value in body.items() if name_ != "look"} for body in scene["bodies"]]
        page = view_page(browser)
        library_case(page, "pictures", view=True)
        page.route(f"**/static/library/{SCENES[variant['part']]}", served("application/json", json.dumps(plain)))
        bare = open_view(page, key) or {}
        grey = home_reads(page)
        apart = {mode: mode in fresh and mode in grey and likeness(fresh[mode]["png"], grey[mode]["png"]) for mode in library_shots.MODES}
        check(f"looks {name}: the same scene served without its looks draws the one grey of before (its stage naming no look), far from the "
              "drawing with them (the colours of the pixels both draw 10 levels apart or more on average, at both homes)",
              bare.get("state") == "drawn" and (bare.get("stage") or {}).get("looks") == {"bodies": [], "part": None, "smooth_deg": None, "part_points": None}
              and all(item and item["mean"] is not None and item["mean"] >= 10 for item in apart.values()), ((bare.get("stage") or {}).get("looks"), apart))
        page.context.close()
        # The UMI finger after the gripper on the same page as on a page of its own (the part's material put back, its
        # facets flat), and the gripper again after it as on a fresh page.
        page = view_page(browser)
        library_case(page, "pictures", view=True)
        open_view(page, VIEW_UMI)
        alone = home_reads(page)
        page.context.close()
        page = view_page(browser)
        library_case(page, "pictures", view=True)
        open_view(page, key)
        page.evaluate("(key) => { location.hash = '#' + key; }", VIEW_UMI)
        then = view_settled(page, VIEW_UMI) or {}
        same, detail = same_drawings(alone, home_reads(page) if then.get("state") == "drawn" else {})
        check(f"looks {name}: the UMI finger drawn after it on the same page draws exactly as on a page of its own (the part's own material "
              "put back: every pixel at both homes)", then.get("state") == "drawn" and then.get("gripper") is False and same, (then.get("state"), detail))
        page.evaluate("(key) => { location.hash = '#' + key; }", key)
        once_more = view_settled(page, key) or {}
        same, detail = same_drawings(fresh, home_reads(page) if once_more.get("state") == "drawn" else {})
        check(f"looks {name}: drawn again after the UMI finger exactly as on a fresh page (every pixel at both homes); no console error",
              once_more.get("state") == "drawn" and same and not errors_of(page), (once_more.get("state"), detail, errors_of(page)[:3]))
        page.context.close()
    # A part whose file is in metres: its corners welded in mm for the smooth normals.  Its scene as committed once it
    # has a crease angle of its own, else served with one and a look for the part.
    part = ENTRIES["variants"][LOOK_METRE]["part"]
    scene = json.loads((LIBRARY / SCENES[part]).read_text(encoding="utf-8"))
    if "smooth_deg" not in scene:
        scene = dict(scene, looks=dict(scene.get("looks") or {}, **LOOK_METRE_SCENE["looks"]), part_look=LOOK_METRE_SCENE["part_look"],
                     smooth_deg=LOOK_METRE_SCENE["smooth_deg"])
    page = view_page(browser)
    library_case(page, "pictures", view=True)
    page.route(f"**/static/library/{SCENES[part]}", served("application/json", json.dumps(scene)))
    settled = open_view(page, LOOK_METRE) or {}
    looks = (settled.get("stage") or {}).get("looks") or {}
    points = part_points(part)
    page.screenshot(path=f"{SHOTS}/library_looks_{LOOK_METRE}_part_smooth.png")
    check(f"looks {ENTRIES['variants'][LOOK_METRE]['label']} (its part's file in {ENTRIES['parts'][part]['mesh']['unit']}): with a look for the part and a "
          f"crease angle, the part's corners share its file's {points} points at 1 um (in mm, whatever the file's unit); no console error",
          settled.get("state") == "drawn" and looks.get("smooth_deg") is not None and looks.get("part_points") == points and not errors_of(page),
          (settled.get("state"), looks, points, errors_of(page)[:3]))
    page.context.close()


# The UMI pad's tint (the rules' part_pad; the user's decision of 2026-11-14, "you can do it darken"): every photo of the
# built sensor shows a dark olive-brown pad on the orange finger.  PAD_LOOK: what the pixels the tint changes must read
# at the Assembled home, their median (hue in degrees, HSV value 0-1) with it and without it, and their least share of
# the drawing.  (The amber before it at least 0.6 since the grippers' homes of 2026-11-16, 0.7 before: seen 57 degrees
# off the face's normal, the figure's 35 until then, the board's median reads value 0.659, the tint's 0.349, hue 32.9
# and 43.7.)
PAD_LOOK = {"hue": (30, 55), "value_most": 0.55, "value_before_least": 0.6, "share_least": 0.05}


def pad_reads(tinted, bare):
    """{mode: {drawn, alpha, changed, median, before}} of two home_reads() of one sensor, with the pad's tint and without
    it: the drawn pixels, those of another alpha, those changed, and the changed pixels' median colour with the tint and
    without it ([hue degrees, value], None with none changed)."""
    import colorsys

    from PIL import Image

    def median(pixels):
        if not pixels:
            return None
        rgb = [sorted(pixel[c] for pixel in pixels)[len(pixels) // 2] / 255 for c in range(3)]
        hue, _, value = colorsys.rgb_to_hsv(*rgb)
        return [round(hue * 360, 1), round(value, 3)]

    out = {}
    for mode in library_shots.MODES:
        if mode not in tinted or mode not in bare:
            out[mode] = None
            continue
        one, two = (Image.open(io.BytesIO(read[mode]["png"])).convert("RGBA").tobytes() for read in (tinted, bare))
        drawn, alpha, changed, before = 0, 0, [], []
        for k in range(0, len(one), 4):
            if one[k + 3] != two[k + 3]:
                alpha += 1
            if not one[k + 3]:
                continue
            drawn += 1
            if one[k:k + 4] != two[k:k + 4]:
                changed.append(one[k:k + 3])
                before.append(two[k:k + 3])
        out[mode] = {"drawn": drawn, "alpha": alpha, "changed": len(changed), "median": median(changed), "before": median(before)}
    return out


def part_pad(browser):
    """The UMI pad's tint in the 3D view (the rules' part_pad; docs/LIBRARY_VIEW.md "Parts without a scene"): the UMI
    finger's sensor as the rules are against the same served without the tint, at both homes."""
    if not any(arts(browser).values()):
        check("pad: the 3D view's art is there for the sensors entries.json gives a view", not VIEWED, "a built site without the shoot's art/")
        return
    index = json.loads((LIBRARY / library_write.SCENES_INDEX).read_text(encoding="utf-8"))
    if index["rules"].get("part_pad") is None:
        print("    pad: the rules give the pad no tint: its checks left out", flush=True)
        return
    page = view_page(browser)
    library_case(page, "pictures", view=True)
    settled = open_view(page, VIEW_UMI) or {}
    tinted = home_reads(page)
    noise = errors_of(page)
    page.screenshot(path=f"{SHOTS}/library_pad_{VIEW_UMI}.png")
    page.context.close()
    plain = dict(index, rules={key: value for key, value in index["rules"].items() if key != "part_pad"})
    page = view_page(browser)
    library_case(page, "pictures", view=True)
    page.route(f"**/static/library/{library_write.SCENES_INDEX}", served("application/json", json.dumps(plain)))
    again = open_view(page, VIEW_UMI) or {}
    bare = home_reads(page)
    page.context.close()
    reads = pad_reads(tinted, bare)
    exploded, assembled = reads["exploded"], reads["assembled"]
    check("pad: the UMI finger's sensor drawn with the rules' pad tint and served without it, no console error",
          settled.get("state") == "drawn" and again.get("state") == "drawn" and not noise, (settled.get("state"), again.get("state"), noise[:3]))
    check("pad: Exploded draws exactly as without the tint (the sheets apart in their own look)",
          bool(exploded) and exploded["alpha"] == 0 and exploded["changed"] == 0, exploded)
    check(f"pad: Assembled, the tint changes {PAD_LOOK['share_least']:g} of the drawing at least, the same outline, from the amber board (value "
          f"{PAD_LOOK['value_before_least']:g} or more) to the photos' dark olive-brown (hue {PAD_LOOK['hue'][0]} to {PAD_LOOK['hue'][1]} degrees, "
          f"value {PAD_LOOK['value_most']:g} at most)",
          bool(assembled) and assembled["alpha"] == 0 and assembled["changed"] >= PAD_LOOK["share_least"] * assembled["drawn"] and assembled["median"] is not None
          and PAD_LOOK["hue"][0] <= assembled["median"][0] <= PAD_LOOK["hue"][1] and assembled["median"][1] <= PAD_LOOK["value_most"]
          and assembled["before"][1] >= PAD_LOOK["value_before_least"], assembled)


class QuietFiles(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def home_frame(stage, mode):
    """The camera's home of ``mode`` in the drawing's own frame (the probe's stage: its home's direction toward the camera
    and its up, the fingers' approach axis; the face's normal the world's z): {elevation_deg: above the plane across the
    approach axis, tilt_deg: off the face's normal, front: the side of the face the camera turns from (+1: up x the
    normal's part across the approach, a gripper's front), left: the normal's share of the screen's leftward direction,
    upright: the approach's share of the screen's up}, rounded to 0.01."""
    d, up, n = stage["home"][mode], stage["up"], (0.0, 0.0, 1.0)
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))  # noqa: E731
    cross = lambda a, b: (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])  # noqa: E731
    unit = lambda a: tuple(x / math.sqrt(dot(a, a)) for x in a)  # noqa: E731
    c = unit(tuple(x - dot(n, up) * u for x, u in zip(n, up)))
    right = unit(cross(up, d))
    screen_up = cross(d, right)
    return {"elevation_deg": round(math.degrees(math.asin(dot(d, up))), 2), "tilt_deg": round(math.degrees(math.acos(dot(d, n))), 2),
            "front": 1 if dot(d, cross(up, c)) > 0 else -1, "left": round(-dot(n, right), 2), "upright": round(dot(up, screen_up), 2)}


def part_aligned(browser):
    """The user's request of 2026-11-16 ("你做成和这个finger一样的空间角度 ... 这样所有card都是对齐的，大小对齐，空间朝向对齐"): every
    gripper's 2 mm sensor and every UMI shelf's card's sensor at its homes, read from the probe's stage, in the drawing's
    own frame: the grippers' common convention (the rules' camera, no scene overriding it: elevation 30 degrees above the
    plane across the approach axis, 65 degrees off the face's normal Exploded and 57 Assembled, from the front; the face
    to the screen's left, the approach up), and the UMI finger and its tips at the same homes (scenes.json's part_homes)."""
    rules = json.loads((LIBRARY / "scenes" / "scenes.json").read_text(encoding="utf-8"))["rules"]
    page = view_page(browser)
    library_case(page, "pictures", view=True)
    shelf = [ENTRIES["parts"][part]["default"] for part in SHELVES] + [card["default"] for part in SHELVES for name in FAMILIES_OF[part] for card in ENTRIES["families"][name]["cards"]]
    read = {}
    for key in [ENTRIES["parts"][part]["default"] for part in CARDED] + shelf:
        state = open_view(page, key) or {}
        stage = state.get("stage") or {}
        read[key] = {mode: home_frame(stage, mode) for mode in library_shots.MODES} if state.get("state") == "drawn" and stage.get("home") and stage.get("up") else state.get("state")
        if key in shelf and isinstance(read[key], dict):
            read[key]["explode_share"] = stage.get("explode_share")
    want = {mode: (rules["camera"][mode]["elevation_deg"], rules["camera"][mode]["tilt_deg"], rules["camera"][mode]["front"]) for mode in library_shots.MODES}
    held = {key: all(isinstance(found, dict) and (found[mode]["elevation_deg"], found[mode]["tilt_deg"], found[mode]["front"]) == want[mode]
                     and found[mode]["left"] > 0.5 and found[mode]["upright"] > 0.8 for mode in library_shots.MODES) for key, found in read.items()}
    print(f"    aligned: {json.dumps({key: found for key, found in read.items() if key in shelf[:1] + [ENTRIES['parts'][CARDED[0]]['default']]})}", flush=True)
    check("aligned: every gripper's 2 mm sensor at the rules' homes in its own frame (30 degrees up, 65 / 57 off the face's normal, from the front; "
          "the face to the screen's left, the approach up)", all(held[ENTRIES["parts"][part]["default"]] for part in CARDED),
          {key: found for key, found in read.items() if not held[key] and key not in shelf})
    check("aligned: the UMI finger and its five shapes at the same homes (scenes.json's part_homes: the approach its tip's way), exploded 0.8 of the "
          "boards' narrower side a layer", all(held[key] and read[key].get("explode_share") == 0.8 for key in shelf),
          {key: found for key, found in read.items() if key in shelf and not (held[key] and isinstance(found, dict) and found.get("explode_share") == 0.8)})
    # The UMI shelf's cards zoomed on the tip (the user's decisions of 2026-11-16: "你可以show gripper的angle但是zoom in了，
    # 就是方向还是那个方向，但是用zoom in +exploded,那就可以tell了"; of zoom 2, "你现在zoom in 的太过了，tactile的tail都看不到"):
    # each card file the home above zoomed (library_write.CARD_FRAMES), the tip 6 % below its top, the tails' ends off its
    # bottom, inside its sides, the finger's base clear of the bottom (the review of 2026-11-16: at 1.35 it lay on the
    # edge), and the same drawing as the sensor's Exploded picture cut there and enlarged as much (the same direction,
    # explode and look); every gripper's card the whole drawing, clear of every edge.
    # (Every UMI sensor's card file, the 30: the shelf shows six.)
    parts = json.loads((LIBRARY / "parts.json").read_text(encoding="utf-8"))
    umi = [key for key, variant in ENTRIES["variants"].items() if library_write.card_frame(parts, variant["part"])]
    framed = {key: card_framing(key) for key in umi}
    check("aligned: each UMI card the Exploded home zoomed on the tip (the tip 6 % below its top, the tails' ends off its bottom, inside its sides), "
          "the same drawing as its Exploded picture enlarged there", len(umi) == 30 and set(shelf) <= set(umi) and all(found["sound"] for found in framed.values()),
          (len(umi), {key: found for key, found in framed.items() if not found["sound"]}))
    bases = [found.get("base") for found in framed.values()]
    check("aligned: each UMI card's finger (its rightmost object) ending at least 0.05 of the card's height above its bottom edge, as its record's base_px",
          all(found.get("base") is not None and found["base"] >= 0.05 * CARD_SIZE[1] and found["base_agrees"] for found in framed.values()),
          {"least": min(bases), "most": max(bases), "off": {key: (found.get("base"), found.get("base_agrees")) for key, found in framed.items()
                                                            if not (found["base"] >= 0.05 * CARD_SIZE[1] and found["base_agrees"])}})
    whole = {key: card_framing(key) for key in (ENTRIES["parts"][part]["default"] for part in CARDED)}
    check("aligned: every gripper's card the whole Exploded drawing, clear of every edge", all(found["whole"] for found in whole.values()),
          {key: found for key, found in whole.items() if not found["whole"]})
    # On the grid, each UMI card the grippers' size, its picture its card file; opened from its card, its page the whole
    # drawing Exploded at the same home (no zoom on the page: the view has no zoom control, and a zoomed home would hide
    # the tails for ever).
    page.goto(SITE["base"] + "?probe")
    wait_until(page, READY, 30)
    load_grid(page)
    boxes = page.evaluate("""() => [...document.querySelectorAll('.lib-cards > .lib-card')].map(card => { const shot = card.querySelector('.lib-shot');
      const img = shot.querySelector('img'); const r = shot.getBoundingClientRect();
      return [card.closest('.lib-shelf') ? 'umi' : 'gripper', Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, img && img.getAttribute('src'),
              img && [img.naturalWidth, img.naturalHeight]]; })""")
    sizes = {(kind, width, height) for kind, width, height, _, _ in boxes}
    srcs = [src for kind, *_, src, _ in boxes if kind == "umi"]
    check("aligned: the UMI cards' pictures the grippers' size, each its card file (640 x 400)",
          len({(width, height) for _, width, height in sizes}) == 1 and srcs == [f"static/library/{IMAGES[key]['exploded']['card']}" for key in shelf]
          and all(natural == list(CARD_SIZE) for kind, *_, natural in boxes if kind == "umi"), (sorted(sizes), srcs))
    opened = {}
    for key in shelf:
        page.goto(SITE["base"] + "?probe")
        wait_until(page, READY, 30)
        load_grid(page)
        page.click(f'#shelf-umi-finray a[href="#{key}"]')
        state = view_settled(page, key) or {}
        read = page.evaluate(library_shots.SHOT, "exploded") if state.get("state") == "drawn" else {}
        after = json.loads(read["state"]) if "state" in read else {}
        edges = edge_pixels(base64.b64decode(read["url"].split(",", 1)[1])) if "url" in read else None
        stage = after.get("stage") or {}
        opened[key] = {"mode": state.get("mode"), "drawn": after.get("drawn_mode"), "moved": after.get("moved"), "edges": edges,
                       "home": home_frame(stage, "exploded") if stage.get("home") and stage.get("up") else None}
    check("aligned: each UMI page opened from its card the whole drawing (nothing on the canvas's edge), Exploded at the card's home",
          all(found["mode"] == "exploded" and found["drawn"] == "exploded" and found["moved"] is False and found["edges"] == 0
              and found["home"] and (found["home"]["elevation_deg"], found["home"]["tilt_deg"], found["home"]["front"]) == want["exploded"]
              for found in opened.values()), {key: found for key, found in opened.items()})
    check("aligned: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()


def card_framing(key):
    """What ``key``'s card file (the tree's) is: {sound: the tip framing of library_write.CARD_FRAMES (its opaque drawing
    0.06 of its height below its top within 1 px, on its bottom edge, CARD_SIDE_MIN of its width from each side) and the
    Exploded picture's drawing (library_shots.card_top() and card_left() on it enlarged ``zoom`` times, cut and brought
    down to the card: a mean colour difference under LIKENESS_MAX of 255 over 0.9 of the pixels both draw opaque), whole:
    its opaque drawing clear of every edge, base: the rows between its finger's base (library_shots.card_base() on its
    opaque drawing: the rightmost object) and its bottom edge, base_agrees: that half the record's base_px within 2 px,
    box, likeness}."""
    from PIL import Image, ImageChops, ImageStat

    record = SHOTS_MANIFEST.get(key) or {}
    frame = library_write.card_frame(json.loads((LIBRARY / "parts.json").read_text(encoding="utf-8")), ENTRIES["variants"][key]["part"])
    card = Image.open(LIBRARY / record["files"]["card"]["path"]).convert("RGBA")
    width, height = card.size
    box = card.getchannel("A").point(lambda value: 255 if value > 128 else 0).getbbox()
    whole = bool(box) and box[0] > 0 and box[1] > 0 and box[2] < width and box[3] < height
    if frame is None or not box:
        return {"sound": False, "whole": whole, "box": box}
    exploded = Image.open(LIBRARY / record["files"]["exploded"]["path"]).convert("RGBA")
    big = exploded.resize((round(exploded.width * frame["zoom"]), round(exploded.height * frame["zoom"])), Image.LANCZOS)
    alpha = big.getchannel("A")
    top = library_shots.card_top(alpha.getbbox(), frame)
    left = library_shots.card_left(alpha.crop((0, top, big.width, min(big.height, top + exploded.height))).getbbox(), big.size)
    cut = big.crop((left, top, left + exploded.width, top + exploded.height)).resize(card.size, Image.LANCZOS)
    solid = [image.getchannel("A").point(lambda value: 255 if value == 255 else 0) for image in (card, cut)]
    both = ImageChops.multiply(*solid)
    count = both.histogram()[255]
    mean = math.fsum(ImageStat.Stat(ImageChops.difference(card.convert("RGB"), cut.convert("RGB")), mask=both).mean) / 3 if count else None
    likeness = {"mean": None if mean is None else round(mean, 2), "share": round(count / max(1, solid[0].histogram()[255]), 3)}
    sound = (abs(box[1] - frame["top"] * height) <= 1 and box[3] == height and min(box[0], width - box[2]) >= library_write.CARD_SIDE_MIN * width
             and likeness["mean"] is not None and likeness["mean"] < LIKENESS_MAX and likeness["share"] > 0.9)
    base = library_shots.card_base(card.getchannel("A").point(lambda value: 255 if value > 128 else 0))
    recorded = (record.get("card_frame") or {}).get("base_px")
    agrees = isinstance(recorded, int) and abs(base - recorded * height / library_write.SHOT_SIZE[1]) <= 2
    return {"sound": sound, "whole": whole, "box": box, "likeness": likeness, "base": base, "base_agrees": agrees}


def part_hands(browser):
    """A hand's further fingers (a scene's extra_fingers, one mechanism for the hands since their merge of 2026-11-17,
    the user's requests that day, a sensor on every finger: the LEAP Hand's since the Allegro Hand and the Unitree Dex3-1
    were removed at the user's word that day, and the Unitree Dex3-1's again since 2026-11-18; the reviews of 2026-11-17,
    which found them drawn but never measured): every gripper's 2 mm sensor's stage
    (?probe) draws exactly its scene's further fingers (none on a two-finger gripper); and each hand's, shot as the
    shots tool shoots it (?probe=shoot), measures each further stack: its top FPC seen in both modes (extra_seen at least
    the rules' near_seen_min) and its field's clearance to every body and finger but its own fingertip and its own links
    (a body's finger "extra<k>": the LEAP Hand's) (stack3_body, ... at least clearance_min_mm in
    both modes; with its own fingertip counted it would be under 1 mm, with the LEAP Hand's own distal link 2.7 mm)."""
    rules = json.loads((LIBRARY / "scenes" / "scenes.json").read_text(encoding="utf-8"))["rules"]
    counts = {}
    for part in CARDED:
        scene = json.loads((LIBRARY / "scenes" / f"{part}.json").read_text(encoding="utf-8"))
        counts[part] = len(scene.get("extra_fingers") or [])
    page = view_page(browser)
    library_case(page, "pictures", view=True)
    drawn = {}
    for part in CARDED:
        state = open_view(page, ENTRIES["parts"][part]["default"]) or {}
        drawn[part] = (state.get("stage") or {}).get("extra_fingers", 0) if state.get("state") == "drawn" else state.get("state")
    check("hands: every gripper's stage draws exactly its scene's further fingers (the Unitree Dex3-1's middle fingertip, the LEAP "
          "Hand's middle and ring fingertips; none on a two-finger gripper)",
          drawn == counts and any(counts.values()), drawn)
    measured = {}
    for part in [part for part in CARDED if counts[part]]:
        key = ENTRIES["parts"][part]["default"]
        page.goto(SITE["base"] + f"?probe=shoot#{key}")
        wait_until(page, READY, 30)
        stage = (view_settled(page, key) or {}).get("stage") or {}
        clearance = (stage.get("measures") or {}).get("clearance") or {}
        labels = [f"stack{k + 3}" for k in range(counts[part])]
        measured[key] = {"extra_seen": (stage.get("numbers") or {}).get("extra_seen"),
                         "cover": {mode: [((stage.get("measures") or {}).get("cover") or {}).get(mode, {}).get(f"{label}.top", {}).get("visible") for label in labels]
                                   for mode in library_shots.MODES},
                         "clearance": {mode: [clearance.get(mode, {}).get(f"{label}_body") for label in labels] for mode in library_shots.MODES}}
    reach = lambda value: 12 if isinstance(value, str) and value.startswith(">") else value  # noqa: E731 (the stage's '>12': beyond its reach)
    check("hands: each hand's further stacks measured (?probe=shoot): their top FPCs seen in both modes, extra_seen their least and at least "
          f"near_seen_min ({rules['checks']['near_seen_min']}); each one's field at least clearance_min_mm ({rules['checks']['clearance_min_mm']} mm) "
          "from every body and finger but its own fingertip and links, in both modes",
          bool(measured) and all(isinstance(found["extra_seen"], (int, float)) and found["extra_seen"] >= rules["checks"]["near_seen_min"]
                                 and found["extra_seen"] == min(value for mode in library_shots.MODES for value in found["cover"][mode])
                                 and all(isinstance(reach(value), (int, float)) and reach(value) >= rules["checks"]["clearance_min_mm"]
                                         for mode in library_shots.MODES for value in found["clearance"][mode])
                                 for found in measured.values()), measured)
    check("hands: no console error", not errors_of(page), errors_of(page)[:5])
    page.context.close()


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
    print(f"the Library at {SITE['base']}", flush=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=WEBGL_ARGS)
            if SITE["root"] is not None:
                answer_github(browser)  # the built site's pages ask GitHub's API for the header's counts (web/counts.js)
            parts = (part_layout, part_grid, part_routes, part_window, part_window_edges, part_first_screen, part_pictures, part_view, part_view_hint_sizes,
                     part_view_race, part_looks, part_pad, part_aligned, part_hands,
                     part_placeholders, part_family, part_downloads, part_isolation, part_errors, part_first_page)
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
