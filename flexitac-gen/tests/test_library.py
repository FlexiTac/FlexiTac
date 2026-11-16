"""The Library (web/library/, the user's requests of 2026-11-05): static checks of its data that need no browser.

- Files: every file of web/library/ is a third-party file of its NOTICE.md table, whose SHA-256 re-hashes, or one of
  this project's own (NOTICE.md, parts.json, entries.json, fits/<id>.json, the pictures shots/<id>.exploded.webp,
  shots/<id>.assembled.webp, shots/<id>.exploded.card.webp and shots/manifest.json); every tabled file
  exists; no file anywhere under web/ is one of the deny-list's vendor models (Robotiq 2F-85 and 3F, the video's
  split of the xArm gripper, the MakerMods body), and no id, title or file name names them; web/library/ stays within
  its 17 MB budget (12 MB until the UMI finger's shapes of 2026-11-16), its pictures within theirs (8 MB, the grid's
  first screen about 1 MB).
- The showcase (the project owner's decision of 2026-11-12: the hand-designed FlexiTac sensor on UFACTORY's xArm
  Gripper G1, the one vendor model shown): an explicit category (library_write.showcase): web/vendor/ufactory-g1/
  holds exactly its twelve meshes at their pinned SHA-256 (this module's list, equal to the writer's) and its notice,
  within a byte budget of its own; the notice says whose the model is, why it is here and what was changed ("3D
  model", never CAD) and tables every file; only the showcase's own scene (scenes/flexitac-g1.json, about the UMI
  finger, with the looks of 2026-11-12) names the folder: no part, entry, fit, picture record, sample or other scene;
  the vendor's own file, unsplit and undecimated, out of the deny-list since that day, still refused anywhere under
  web/; the holder a body of the Library with its open licence; on a copy of the committed files, each of these
  broken and named; the site's copy and the public export carry the folder.  Since its second stage that day: the
  scene as built (the part the gripper's left finger, a camera of its own, no finger see-through) with the seven plain
  shapes the project draws, each at its pin; the showcase's page's document (showcase.json, library_write.showcase_page:
  its words, the label's two claims, the placed record, the tutorial, the two notices, its three pictures and what
  they were shot from, stale with another scene, rules, art or placed record) in every gate; and on the page, the
  grid's first card and its own page with no generator action.
- The pictures (shots/, tools/browser/library_shots.py; the user's request of 2026-11-05: the cards show the finger with
  the sensor on it): each sensor's "image" the one shots/manifest.json gives (library_write.pictures: null without a
  shot), none of another fit (the wrong sensor pictured), one of older figure sources a warning only (the public CI runs
  no browser); since the set of 2026-11-05 every sensor of the shipped Library pictured by a shot of its own fit and
  build, each drawing centred in its picture (the shots tool's centring()); on a fixture of two tiny WebPs: the WebP
  format with alpha at the contract's sizes, entries.json's image exactly the contract's, a stale fit and a broken file
  refused, older sources a warning, the tool's records taken by the writer, library_write --check refusing a sensor
  without its picture (writing only reporting it), the site build's gate refusing a picture of another fit or an image
  the manifest does not give.
- Licences: each part's is Apache-2.0, MIT or BSD-3-Clause, its text a tabled licence file, its source a URL pinned to
  a commit (the NOTICE row's), its change stated (Franka's the convex hull).
- entries.json is tools/library_write.py's entries() of parts.json and the committed fits (recomputed, no fitting),
  with each mesh's bytes, SHA-256 and facets; the labels fit the file note of Gen by Surface ('From the Library: ' +
  label, at most 46 characters), the shelf headings name the pitches in one wording ('Four pitches, 1 to 3 mm.', the
  user's decision of 2026-11-05) but the UMI finger's, which names its shapes ('Six finger shapes, straight to
  pointed.', 2026-11-16), 'start' holds each part's 2 mm sensor (the page's layout of 2026-11-06: one card per
  gripper but the UMI finger, opening its 2 mm sensor, then the UMI finger's shelf).
- The page's request: every fit's request is the one the page sends (library_write.compose of the part, the variant
  and gen.html's options (index.html's until 2026-11-16); the mesh's file name, no unit, 32 rows and columns at most, numbers as the browser writes
  them), the UMI finger's 2 mm one the page's shipped default fit itself; the options are exactly the Resolution
  step's enabled controls (a parser of this module's own) at their defaults, but the pitch, the fill and the part's
  own, each one the control takes (min, max, step, in decimal).
- Product rules on every committed proposal #1, without fitting: one tail pin per line (reader none), field-only
  containment, the tails centred and ending together, a symmetric face's sensor centred, a build with no error or
  warning and the same build id; rules() names each broken rule on tampered replies.
- Staleness: each part's 2 mm sensor fitted again gives the committed reply, and one tapered tip's (the site build
  re-fits them all).
- The tapered tips (the family umi-tapers, cut by the private tools/library_tips.py): since the user's request of
  2026-11-16 the family's cards on the UMI finger's shelf, one per shape (Short taper: trapezoid and convex arc over
  40 mm; Convex arc, Trapezoid and Concave arc tips over 75 mm; the Pointed tip, a 50 mm ogive to 2 mm), each complete
  (its shapes by its tip widths, each once, its picture's sensor one of them, its lines), every tip on one card, the
  family's default its own address's (the 13.8 mm trapezoid), no shelf or card of a tip's own; each tip's change a tip
  cut tabled as a modified file; its setup the video's (the contact face grown flat from a facet of it under the face
  point, the base at the mount end, no border, the page's options); since the review of 2026-11-16 each tip's mesh
  measured against its kind's profile (the tool's three, copied here and pinned to the tool's own where it is).
- tools/library_write.py is public (export_public.PUBLIC) and tools/library_import.py and tools/library_tips.py are
  not (the tips' tool needs trimesh and manifold3d: never imported here); the deny-list is the writer's, equal to this
  module's, and the importer keeps no copy of its own but takes the writer's; the new files parse as Python 3.9.

- The page (index.html since 2026-11-16, library.html before; library.js, library.css): its scripts (forward.js, then
  theme.js, then its own) and three style sheets by relative URLs, nothing inline, unique ids; its header the
  generator's (the title block and the community links byte for byte, the mode switch as two links to gen.html); the
  header's Library link on both pages (gen.html: the same tab since 2026-11-15; index.html: the current page), at ./, its style in dated blocks beside the header's rules; never "CAD"; no IntersectionObserver, scroll timeline,
  smooth scrolling, window scroll listener or absolute URL in the script, no transition, animation, fixed or sticky box
  in the style sheet, the action blue only on Open in Gen by Surface, a sensor's picture 3:1 below 900 px (the
  user's decision of 2026-11-05: Open in a phone's first screen) and 16:10 elsewhere; node --check when node is there.
- main.js's gen.html?part=<id> (./?part=<id> until 2026-11-16): DEFAULT_PART and runFit's shipped test as they were, the index and the parameter read, the
  sensor built from its fit's own request, the user's own file and Remove model leaving it, the file note's prefix.
- app.py serves the Library at / and /index.html (any query) and the generator at /gen.html with its security headers
  and the header's counts, library.html (a forwarding page) with the headers alone; POST is a 405; its pictures as
  image/webp (the merge of 2026-11-05).
- tools/build_static_site.py: index.html (the Library) and gen.html with the site's head tags and counts, library.html
  with the head tags alone, none of the pages copied under static/, the
  Library's gate (ZIPs byte for byte app.answer's exports, files.json's record of them) and a stale fit stopping it.

- The 3D view (the user's requests of 2026-11-05, docs/LIBRARY_VIEW.md: each sensor's page turns in 3D, the grippers
  drawn whole): the committed scenes current (library_write.scenes) and as the user approved them (every gripper but
  the UMI finger and its tips with its scene, both fingers, the jaws fully open, the mate turned or mirrored, the near
  finger see-through on every gripper, in both views, its stack assembled, the MakerMods tips on the project's own
  rail, the rules of Exploded 65 and Assembled 57 degrees and the 0.28 see-through, one stack exploding: the user's
  decision of 2026-11-06); on tiny scenes built here, every check of scenes()
  naming its problem (the formats, the part's mesh, a unit approach, rigid matrices and the mate's kind by its
  determinant, the bodies' files and notices, the overrides' bounds and reasons, the deny-list, the private importer's
  inputs); each sensor's "view" the one shots/manifest.json gives (pictures(): its art and a gripper's stage), and on
  tiny art: the transition both ways (VIEW_REQUIRED), an art of another build or of broken bytes refused, a stage of
  another scene or rules, breaking a rule or recorded for a fingertip refused, older view sources a warning, the alt
  text of a whole gripper; the art and the bodies the files the entries and the scenes name, within their budgets
  (0.6 MB, 2.5 MB); the site build stopped by a stale art, view or scene and publishing art/, scenes/ and bodies/;
  tools/library_scenes.py private.

The browser checks are tools/browser/library_checks.py (and part_library of cad_checks); tools/library_write.py
--check and the site build check every fit.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import gzip
import hashlib
import importlib.util
import inspect
import io
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import warnings
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
LIBRARY = WEB / "library"
sys.path.append(str(ROOT / "tools"))
import build_static_site  # noqa: E402
import export_public  # noqa: E402
import library_write  # noqa: E402

try:
    from test_api_http import HttpTestCase
    from test_web_theme import parse_css, subject
except ImportError:  # run as a package
    from tests.test_api_http import HttpTestCase
    from tests.test_web_theme import parse_css, subject

# All of web/library/ but its pictures (shots/, showcase/: their own budgets below): 12 MB until the UMI finger's shapes
# of 2026-11-16 (the user's request: one card per shape), whose sixteen tips (their meshes, 3.8 MB, their fits and art)
# took it from 11.66 to 16.41 MB.
BUDGET_BYTES = 17_000_000
SPDX = {"Apache-2.0", "MIT", "BSD-3-Clause"}
# Vendor models that may not be redistributed (the video's recipes: user-provided, shown for illustration).
DENIED_SHA256 = {
    "b0df0eaca944c7401185ada85d22e3111b477c3484c6fa3fd915fce6d6811aaf": "Robotiq 2F-85 (2F85_Opened.stl)",
    "49e96f7fceab20ebcf13b5c8467bf83d70716a846a109ad37818bc06d798f7a7": "Robotiq 3F (ROBOTIQ_AGS-001-XXXX.stl)",
    "acbae34a4329e9079b7550af0fe6624cc8277f02c2317d4df7e9950589efc24c": "xArm (finger_r.stl)",
    # The other six meshes split from the same closed xArm file as finger_r.stl (the review of 2026-11-05).
    "a61abac9746d0319a6e6ab82ba27a7d16afe6f303bc2bac863449b05c27c0661": "xArm (finger_l.stl)",
    "4101e1a6a1d1983727470eeacde4225031c53309ae9f5cee7b2f2d2bc3e70bb5": "xArm (body.stl)",
    "676df24e40f8dbd84d760226d9605fc8d27171c4f392e26b0fcdb47d808ec227": "xArm (link_l_inner.stl)",
    "3d82a29a55c7fca3f08eeb441a97667d34e675901bc0fab8c22fec6e41ead7bd": "xArm (link_l_outer.stl)",
    "f256d6ca99bca7c32e991080ca5988015c96a535bf1edc14840ff5643f864904": "xArm (link_r_inner.stl)",
    "c97e95bafd0b0f5a66dfcccf5f398956ddae2facca3d4509f1754a0ba138888b": "xArm (link_r_outer.stl)",
    # 2026-11-12: "xArm (Gripper G1 3D File (With).stl)" left this list by the project owner's decision of that day (the
    # showcase's notice names it); the file itself is still refused anywhere under web/ (SHOWCASE_SOURCE below).
    # The same file split as the FlexiTac Tactile Demo splits it, not decimated (the review of 2026-11-12): its seven
    # first pieces and the nine further pieces of its body and fingers.
    "e18c8d350dd92e480cdcedc0c59d56369aa60c2b80f0e6d05198a9e657fb4e5d": "xArm Gripper G1, not decimated (body.stl)",
    "fdab9b44c248c7b8cd738b9c3ca25c7abd8b36d27156078a585f4b13e970b43e": "xArm Gripper G1, not decimated (finger_r.stl)",
    "303363c45801cc09e08daf2be914b9f9a237b671e455fe67ceb73e2e1fbeec16": "xArm Gripper G1, not decimated (finger_l.stl)",
    "375ecfd2ebda0c82e73758c7d336cb139208c666cb10805d56dac85dbbca6b4b": "xArm Gripper G1, not decimated (link_r_outer.stl)",
    "7190fb20f73f857dffa37ca44c373933213c6b9019133844e74d449fd274cef7": "xArm Gripper G1, not decimated (link_r_inner.stl)",
    "c68097e5a999c4a858ab15a2b175072db1f4378eabb0875c50ac3f6351401f17": "xArm Gripper G1, not decimated (link_l_outer.stl)",
    "7d2be86623b0e6ed83cca042e16980363fe30a5d8fab17b51866899ece960743": "xArm Gripper G1, not decimated (link_l_inner.stl)",
    "8cf40e4911d8e30fc18a223ff9b2f4e06667b854b5da741520fafa0b21dabce1": "xArm Gripper G1, not decimated (body_shell.stl)",
    "29c2cf986ead35efeace70442b253428962716784ada51254123eca9c0e81932": "xArm Gripper G1, not decimated (body_frame.stl)",
    "1fc90b2f5e0a5e98f6ea419487f83bdf1176ce559e079370fe645276dbfd97dc": "xArm Gripper G1, not decimated (body_flange.stl)",
    "51558812030bb692137d6bea813af792ee833569b4d38c763b14700af03877ff": "xArm Gripper G1, not decimated (body_pins.stl)",
    "eba81d3da9a11fbbb1287c7a7d95f9d85c87d4d7ec1ff40384f40177d2d139f0": "xArm Gripper G1, not decimated (body_logo.stl)",
    "2e938d7af2767bb811c97d37f1b2170b421390f93320345ec3cb61dbf6a04bf9": "xArm Gripper G1, not decimated (finger_r_coupler.stl)",
    "fe62f783f423e575608cd2701106ee036ee6f2d1b061ed31236702e54db05f78": "xArm Gripper G1, not decimated (finger_r_pins.stl)",
    "c4f8214b64116588b4c6d6aec3d07e268350e73b669a35efa89aa6bee6067991": "xArm Gripper G1, not decimated (finger_l_coupler.stl)",
    "f6b588d88bd3f4788b237899092c8008119b8b5d3f7cdb8ec0c35d4f9742aa72": "xArm Gripper G1, not decimated (finger_l_pins.stl)",
    # The MakerMods Metal Arm's gripper body, not cleared (2026-11-05: its tips are drawn on the project's own rail).
    "19ab43c406f349d62dc7a9932b66fb28053cf96152ab00d71a93945a43ddd8cd": "MakerMods Metal Arm (gripper_base.STL): not cleared",
    "3c813623f4c273bfb6f4fd483fc8ee23dc4325de32e9d89d7c44cb1a0e97c033": "MakerMods Metal Arm (link7.STL): not cleared",
    "62d0ed4072aea7e4d0655e16edbf8243317e3e106996f00f06e72afc78d091ec": "MakerMods Metal Arm (link8.STL): not cleared",
}
DENIED_NAME = re.compile(r"robotiq|xarm|ufactory", re.IGNORECASE)
NOTICE_ROW = re.compile(r"^\| `([\w./-]+)` \|([^|\n]*)\|([^|\n]*)\|([^|\n]*)\| `([0-9a-f]{64})` \|$", re.MULTILINE)
# The showcase (the project owner's decision of 2026-11-12; library_write.SHOWCASE_*): UFACTORY's 3D model of the xArm
# Gripper G1, split and decimated, in a folder of its own beside the Library: exactly these files at these hashes (the
# same list as the writer's), within this budget and nowhere else under web/; the file they are made from (its
# SHA-256 and bytes; the SHA-256 of its bytes after the 80-byte header), never under web/; the holder, a body.
SHOWCASE = WEB / "vendor" / "ufactory-g1"
SHOWCASE_SCENE = "scenes/flexitac-g1.json"
SHOWCASE_SOURCE = ("Gripper G1 3D File (With).stl", "6c59aabbd22823819af1face17752cfd5b32f43529ed08da9596148770de332f", 6347684)
SHOWCASE_SOURCE_TRIANGLES = "6fedf322985477e914f3160228e2b3c1fa7226843dc6f58e4ea19e9914d53393"
SHOWCASE_FILES = {
    "body_shell.stl": "17f20591f7ad00a5c19f8f915404df71b9332e971007f5afd58dc0ee83196000",
    "body_frame.stl": "c3fac3ded9752ee3101a4eb0752d687404ff87989601ed853ce9dbde1fe1201c",
    "body_flange.stl": "53d5b7376b3b15bae4974e93f60fc565d487d32337c88163718ef9e58071038f",
    "body_pins.stl": "0e36e3e656bc3a5b684f20fe87aa1e76d3956eb7cd52e60fb638de4d2458424f",
    "link_r_outer.stl": "a30b4e83a108cdc8d3cafbbcdf4dc87e2c33828440f28776e2a601ce4ab40588",
    "link_r_inner.stl": "6d095d76626f53a5a7af281e86051fe18665dca5a56f5e03c9c83a19ffa66299",
    "link_l_outer.stl": "6ab58ca8f67ed33fd07016a82c606938c142ca283bc7ab04218b772783d7376c",
    "link_l_inner.stl": "93f51a6a5713d5ccec58ec8548ef63855d7e20561dd152dc81f273e20b3f8ea0",
    "finger_r_coupler.stl": "a8526adbd71aaaad6bfd7b109baabc7eeaecfccc40fedb42624210455f3d5c8b",
    "finger_r_pins.stl": "8af3cc1ad160fcac75e4db0f5a1b2b5546aeecdcecb639dd87fdf5f678c3ddf0",
    "finger_l_coupler.stl": "b9c13ced96553fb2ee8038ccb78354f1a1ad1098818c2d9e8084bd524d0de849",
    "finger_l_pins.stl": "be9bd6efe4aa156542836c82b13603a544760a88bab3e03f02afa8721841da9c",
}
SHOWCASE_BUDGET_BYTES = 2_200_000
SHOWCASE_HOLDER = ("bodies/flexitac-g1/umi-right-finger-holder.stl", "bed7997d234957cd874aecec2be76e133ab14b4cd652abe4c0491ee06fe469dd")
# The plain shapes the project draws for the showcase after the owner's photo of the gripper (tools/library_showcase.py
# DRAWN; the same pins as the writer's): screw and bolt heads, nuts, the block in the top slot, the extender boards with
# their sockets and the cable stubs.  In the scene's order of them.
SHOWCASE_DRAWN = {
    "bodies/flexitac-g1/drawn-shell-screw.stl": "3e9be6a39e4c3324539b799a027ff2d11da071427abc9fdc4b18bbd11d218cdb",
    "bodies/flexitac-g1/drawn-holder-bolt.stl": "4065ad795ec729b88544255a84ee9372498d6d8b7874504c1ecacbb9b119d3d8",
    "bodies/flexitac-g1/drawn-holder-nut.stl": "19dfdb4cfc52e2aca385209251c9ae8bd063fcee2f776a8dc5540fc6e9ab7dcb",
    "bodies/flexitac-g1/drawn-slot-block.stl": "4c931930fd990b0e76da2facd08e69b7d795b371264d58196b80b3b056685f0d",
    "bodies/flexitac-g1/drawn-extender.stl": "ce9e3d2b69f27cb92a941e0580e2cd25c717f341515e9f022b3f5a8814b54559",
    "bodies/flexitac-g1/drawn-extender-sockets.stl": "1fb0ee61d901a42382ed3ba2004b6e80912e45c99c31caff7e1ac7bbfd0fa042",
    "bodies/flexitac-g1/drawn-cable-stub.stl": "13d5a943386e3cb4a92e55d8b135a99a0ff3b765496633cd774c46f9757ac1e5",
}
SHOWCASE_BODIES = dict([SHOWCASE_HOLDER], **SHOWCASE_DRAWN)
# The showcase's page (2026-11-12): its document beside entries.json, its three pictures in a folder of their own.
SHOWCASE_FILE = "showcase.json"
SHOWCASE_PICTURES = ("showcase/flexitac-g1.exploded.webp", "showcase/flexitac-g1.assembled.webp", "showcase/flexitac-g1.card.webp")
REBUILD_SHOWCASE = "rebuild the showcase with tools/library_showcase.py"
# Since the 3D view of 2026-11-05 (docs/LIBRARY_VIEW.md): each sensor's art, the scenes and the MakerMods scene's rail,
# drawn by the project (the grippers' other bodies are third-party files, tabled in NOTICE.md).
OWN_FILE = re.compile(r"^(NOTICE\.md|parts\.json|entries\.json|fits/[a-z0-9.-]+\.json|shots/manifest\.json"
                      r"|shots/[a-z0-9.-]+\.(exploded|assembled|exploded\.card)\.webp"
                      r"|art/[a-z0-9.-]+\.json\.gz|scenes/[a-z0-9-]+\.json|bodies/makermods-metal/rail\.stl"
                      # Since the looks of 2026-11-12: a plain shape tools/library_split.py drew where a model lacks a component.
                      r"|bodies/[a-z0-9-]+/drawn-[a-z0-9-]+\.stl"
                      # The showcase's page (2026-11-12): its document and its three pictures.
                      r"|showcase\.json|showcase/flexitac-g1\.(exploded|assembled|card)\.webp)$")
# The pictures' budgets (2026-11-05): the whole set (126 files of 42 sensors; 174 of 58 since 2026-11-16), and the grid's
# first screen: since the layout of 2026-11-06 every card of the grid (the grippers' seven, then the UMI shelf's cards:
# since 2026-11-16 its six shapes, before its four pitches and its Tapered tips card), all asked for as the page opens
# (it is short; library_checks part_pictures measures the bytes).
SHOTS_BUDGET_BYTES = 8_000_000
FIRST_SCREEN_BYTES = 1_000_000
FIXTURES = ROOT / "tests" / "fixtures"
# The contract of the pictures (the Library's UI and tools/browser/library_shots.py were built against it, 2026-11-05).
IMAGE_OF_WIDOWX = {"exploded": {"src": "shots/widowx-250-2mm.exploded.webp", "card": "shots/widowx-250-2mm.exploded.card.webp",
                                "width": 1280, "height": 800},
                   "assembled": {"src": "shots/widowx-250-2mm.assembled.webp", "width": 1280, "height": 800},
                   "alt": "WidowX 250, 2 mm on the part"}
NOTE_PREFIX = "From the Library: "
NOTE_MAX = 46
# main.js reads the index here (LIBRARY_INDEX, static/ being web/).
LIBRARY_INDEX_PATH = "library/entries.json"
# The tapered tips (tools/library_tips.py): the family, its kinds and its cards, and the video's face and base.  A
# kind (the key of its parts' ids, umi-<key>-tip<w>): its words in the label ('UMI trapezoid tip, 13.8 mm'), its
# profile's words in the licence's change, its taper's height and its tip widths (the user's of 2026-11-05; the
# shapes of 2026-11-16: the concave arc, the short taper and the point).
TAPERS = "umi-tapers"
TAPER_TIPS = ("21.8", "17.8", "13.8", "9.8", "5.8")
TAPER_KINDS = {"short-trap": ("short trapezoid", "trapezoid", 40, TAPER_TIPS), "short-convex": ("short convex", "convex arc", 40, TAPER_TIPS),
               "convex": ("convex arc tip", "convex arc", 75, TAPER_TIPS), "trap": ("trapezoid tip", "trapezoid", 75, TAPER_TIPS),
               "concave": ("concave arc tip", "concave arc", 75, TAPER_TIPS), "pointed": ("pointed tip", "convex arc", 50, ("2",))}
# The UMI shelf's cards after the straight finger, in its order (the user's request of 2026-11-16: one card per
# shape): key, title, its kinds with their Shape labels, the sensor its picture shows.
TAPER_CARDS = (("short", "Short taper", (("short-trap", "trap", "Trapezoid"), ("short-convex", "convex", "Convex arc")), "umi-short-trap-tip9.8-2mm"),
               ("convex", "Convex arc tip", (("convex", "convex", "Convex arc"),), "umi-convex-tip9.8-2mm"),
               ("trap", "Trapezoid tip", (("trap", "trap", "Trapezoid"),), "umi-trap-tip9.8-2mm"),
               ("concave", "Concave arc tip", (("concave", "concave", "Concave arc"),), "umi-concave-tip9.8-2mm"),
               ("pointed", "Pointed tip", (("pointed", "pointed", "Pointed"),), "umi-pointed-tip2-2mm"))
FACE_POINT = (0.0, -12.9, -62.7)
MOUNT_BASE = {"point_xyz": [0, -12.9, -3]}
# A kind's profile, as its words in the licence's change name it (tools/library_tips.py PROFILES).
TAPER_PROFILES = {"trapezoid": "trap", "convex arc": "convex", "concave arc": "concave"}


TAPER_FACE_MM, TAPER_TIP_Z = 25.8, -123.36   # the contact face's width and the tip's end (z), mm


def _half_width(s: float, profile: str, h: float, tip: float) -> float:
    """Half the face's width ``s`` mm below the start of a taper ``h`` mm high to a tip ``tip`` mm wide: tools/library_tips.py's
    half_width(), its three profiles (d = (25.8 - tip) / 2, R = (h² + d²) / 2d): ``trap`` straight sides, ``convex``
    circular arcs tangent to the full-width edge where the taper starts, ``concave`` arcs tangent to the axis at the tip."""

    a, b = TAPER_FACE_MM / 2, tip / 2
    d = a - b
    if d <= 0:
        return a
    if profile == "trap":
        return a - d * s / h
    r = (h * h + d * d) / (2 * d)
    if profile == "convex":
        return a - r + math.sqrt(max(r * r - s * s, 0))
    if profile == "concave":
        return b + r - math.sqrt(max(r * r - (h - s) ** 2, 0))
    raise ValueError(profile)


def _tool_profile():
    """(half_width, W, Z_TIP) of the private tools/library_tips.py, read from its source and run on floats (the tool needs
    numpy and trimesh, so it is never imported here; the three numpy calls its half_width() makes are math's on one
    number), or None in a copy without it (the public one)."""

    path = ROOT / "tools" / "library_tips.py"
    if not path.exists():
        return None

    class Numbers:
        ndarray = float
        sqrt = staticmethod(math.sqrt)
        maximum = staticmethod(max)
        full_like = staticmethod(lambda s, value: value)

    namespace = {"np": Numbers}
    tree = ast.parse(path.read_text(encoding="utf-8"))
    wanted = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "half_width"
              or isinstance(node, ast.Assign) and [getattr(target, "id", None) for target in node.targets] in (["W"], ["Z_TIP"])]
    exec(compile(ast.Module(wanted, type_ignores=[]), "tools/library_tips.py", "exec"), namespace)
    return namespace["half_width"], namespace["W"], namespace["Z_TIP"]


def _stl_triangles(data: bytes) -> list:
    """A binary STL's triangles, each its nine coordinates (x, y, z of its three corners)."""

    (count,) = struct.unpack_from("<I", data, 80)
    if len(data) != 84 + 50 * count:
        raise ValueError("not a binary STL")
    return [struct.unpack_from("<9f", data, 84 + 50 * k + 12) for k in range(count)]


def _span_at(triangles: list, z: float) -> tuple:
    """(min, max) of y where the plane at height z cuts the part: its width at z (the finger is as wide as its face)."""

    found = []
    for corners in triangles:
        for i, j in ((0, 1), (1, 2), (2, 0)):
            za, zb = corners[3 * i + 2], corners[3 * j + 2]
            if za != zb and (za - z) * (zb - z) <= 0:
                ya, yb = corners[3 * i + 1], corners[3 * j + 1]
                found.append(ya + (z - za) / (zb - za) * (yb - ya))
    return min(found), max(found)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def shelf_cards(entries: dict) -> list:
    """The sensors of grid_cards() on a shelf (the UMI finger's: its own card's and its families' cards'), whose cards show
    their Assembled picture (library.js SHELF_VIEW, the lead's review of the UMI shelf's shapes, 2026-11-16)."""
    shelved = {"umi-finray"} | {family["shelf"] for family in entries["families"].values()}
    return grid_cards(entries)[sum(1 for part in entries["order"] if part not in shelved):]


def grid_cards(entries: dict) -> list:
    """The sensors whose card pictures the grid shows (library.js, the layout of 2026-11-06), in the page's order: one
    card per gripper but the shelved (its default, the 2 mm sensor), then each shelved part's (the UMI finger's, and any
    a family's cards follow) own card (its default) and its families' cards (each its default; the user's request of
    2026-11-16: one card per shape, where the UMI finger's four pitches had been four cards)."""
    shelved = {"umi-finray"} | {family["shelf"] for family in entries["families"].values()}
    cards = [entries["parts"][part]["default"] for part in entries["order"] if part not in shelved]
    for part in (part for part in entries["order"] if part in shelved):
        cards += [entries["parts"][part]["default"]] + [card["default"] for family in entries["families"].values() if family["shelf"] == part
                                                         for card in family["cards"]]
    return cards


def _canonical(value) -> str:
    # This module's own: sorted keys, no rewriting of the numbers (2.0 stays 2.0, which the browser never sends).
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _plan(parts: dict) -> list:
    return library_write.plan(parts)


def _notice() -> dict:
    text = (LIBRARY / "NOTICE.md").read_text(encoding="utf-8")
    return {row[0]: row for row in NOTICE_ROW.findall(text)}


def _shots_tool():
    """tools/browser/library_shots.py, loaded from its file (it needs Playwright and Pillow only to shoot, not to write
    its records); its global no-bytecode switch put back."""

    kept = sys.dont_write_bytecode
    spec = importlib.util.spec_from_file_location("library_shots", ROOT / "tools" / "browser" / "library_shots.py")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = kept
    return module


SHOTS_TOOL = _shots_tool()
# The fixture: two tiny WebPs as library_shots.webp writes them (Pillow, lossy with lossless alpha: an amber board over
# a grey block on a transparent background), 1280 x 800 and its 640 x 400 card.
SHOT = (FIXTURES / "library_shot.webp").read_bytes()
SHOT_CARD = (FIXTURES / "library_shot.card.webp").read_bytes()


# The 3D view (docs/LIBRARY_VIEW.md): the budgets of the grippers' bodies and the sensors' art, and the scenes as the
# user approved them on 2026-11-05 (the prototype's pictures: the jaws fully open, a sensor on both fingers, the other
# finger turned or mirrored; the MakerMods tips on a rail) and decided on 2026-11-06 ("每一个夹爪只用爆炸一个sensor,
# 靠近外面的finger透明, 夹爪不爆炸; 靠近里面的finger不透明, 夹爪爆炸"): the finger nearer the camera see-through in both
# views, its stack assembled; the far finger's stack exploded (gap share 0.42, its stacks apart in mm and on screen).
BODIES_BUDGET_BYTES = 2_500_000
ART_BUDGET_BYTES = 600_000
APPROVED_RULES = {"gap_share": 0.42, "min_step_mm": 2, "ghost_opacity": 0.28, "measure_px": [1280, 800], "depth_tol_mm": 0.1,
                  "explode_stacks": ["sensor"], "see_through_modes": ["exploded", "assembled"],
                  "camera": {"exploded": {"tilt_deg": 65, "elevation_deg": 30, "front": 1},
                             "assembled": {"tilt_deg": 57, "elevation_deg": 30, "front": 1}},
                  "checks": {"opaque_cover_max": 0.1, "layer_visible_min": 0.25, "clearance_min_mm": 3, "stacks_apart_min_g": 0.2,
                             "stacks_apart_min_mm": 3, "stacks_apart_min_px": 20, "near_seen_min": 0.5, "card_min_px": 20,
                             "ghost_cover_min": 0.02},
                  # The UMI finger and its tapered tips in the real finger's orange TPU (the user's request of 2026-11-12:
                  # every gripper coloured after photos of the real product): a look of the rules' own, umi-tpu-orange,
                  # tuned on the finger in the stage against its photos (the base look tpu-orange is left as it was: the
                  # base table and the showcase's copy of it are not this change's), with flat facets (no part_smooth_deg:
                  # at 35 degrees under 0.46 % of the pane's pixels change at all and under 0.05 % by more than 14 of
                  # 255, at most 28, a highlight along the mount block's rounded corner; docs/LIBRARY_VIEW.md).  Roughness 0.85
                  # since the verification of 2026-11-13 (0.6 drew the faces turned up to the lights a washed salmon).
                  "looks": {"umi-tpu-orange": {"color": "#e85a1c", "metalness": 0, "roughness": 0.85, "env_intensity": 0.3}},
                  "part_looks": {"umi-finray": "umi-tpu-orange", "umi-tapers": "umi-tpu-orange"},
                  # Their assembled sensor's pad over the film in the photos' dark olive-brown (the user's decision of
                  # 2026-11-14, "you can do it darken": the amber top board had read as one block with the orange finger),
                  # a tint tuned in the stage against flexitac.github.io's photo of the built sensor (docs/LIBRARY_VIEW.md).
                  "part_pad": {"color": "#545a3a", "opacity": 0.65}}
# The near finger (the mate) see-through on every gripper (the user's decision of 2026-11-06).
SEE_THROUGH = {"franka-hand": ["mate"], "widowx-250": ["mate"], "trossen-widowx-ai": ["mate"], "arx-x5": ["mate"], "i2rt-yam": ["mate"],
               "unitree-dex1": ["mate"], "makermods-metal": ["mate"]}
MATE_KINDS = {"franka-hand": "turned", "widowx-250": "turned", "trossen-widowx-ai": "mirror", "arx-x5": "mirror", "i2rt-yam": "mirror",
              "unitree-dex1": "turned", "makermods-metal": "turned"}
PICTURE = "on both fingers of the open gripper"
RAIL = "bodies/makermods-metal/rail.stl"
# Since its body drawn by eye (the user's decision of 2026-11-14) the MakerMods picture is the open gripper's too.
PICTURES = {"makermods-metal": "on both fingertips of the open gripper"}
IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
TURNED = [[-1, 0, 0, 0], [0, -1, 0, -80], [0, 0, 1, 0], [0, 0, 0, 1]]
MIRROR = [[-1, 0, 0, -88], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
# The hash of the Library view's modules the tiny records are shot with (pictures(view=...): the modules need not exist).
VIEW = "5" * 64
REBUILD = "rebuild the scenes with the private tools/library_scenes.py"
# A scene's looks are tools/library_split.py's to write (the review of 2026-11-12: their problems had named the scene builder).
RELOOK = "write the scene's looks again with tools/library_split.py (the part's look file, tools/library_looks/<part>.json)"
# Stage numbers that keep every rule (a gripper's record's, docs/LIBRARY_VIEW.md).
NUMBERS = {"jaw_gap_mm": 80.0, "step_mm": 10.0, "drape_step_mm": 2.0, "face_tilt_deg": 0.0, "visible_min": 0.5, "opaque_max": 0.01,
           "assembled_opaque": 0.0, "ghost_cover": 0.1, "clearance_mm": {"bodies": 12, "other_finger": 12, "stacks": 30},
           "card_px": [40, 30], "band_css": {"contain": [20, 10], "cover": [40, 20]}, "near_seen": 1.0, "stacks_apart_px": 100}


# The pictures' own tests (their fixture's records carry no art): run as before the shoot that writes every sensor's art,
# whatever VIEW_REQUIRED is (ViewTests test both ways).
PICTURES_ONLY = mock.patch.object(library_write, "VIEW_REQUIRED", False)


def _stl(triangles: int = 1, seed: int = 0) -> bytes:
    """A binary STL of ``triangles`` facets (``seed`` another file)."""

    facet = struct.pack("<12fH", 0, 0, 1, seed, 0, 0, seed + 1, 0, 0, seed, 1, 0, 0)
    return b"tiny".ljust(80, b"\0") + struct.pack("<I", triangles) + facet * triangles


def _write_json(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def _scene_library(library: Path, parts: dict) -> Path:
    """``library`` holding a tiny scene of each gripper part (scenes/<part>.json: one body, a binary STL of one facet in
    bodies/<part>/, tabled in NOTICE.md with an open licence and its text; the MakerMods Metal Arm's the project's own
    rail), the mate turned or mirrored and the see-through fingers as approved, and scenes.json with the committed rules
    (the approved ones) and a scene for each."""

    index = _json(LIBRARY / library_write.SCENES_INDEX)
    index["scenes"] = {}
    rows = []
    (library / "licenses").mkdir(parents=True, exist_ok=True)
    (library / "licenses" / "tiny.txt").write_text("A licence.\n", encoding="utf-8")
    for number, part_id in enumerate(library_write.gripper_parts(parts)):
        mesh = RAIL if part_id == "makermods-metal" else f"bodies/{part_id}/body.stl"
        data = _stl(seed=number)
        (library / mesh).parent.mkdir(parents=True, exist_ok=True)
        (library / mesh).write_bytes(data)
        if mesh != RAIL:
            rows.append(f"| `{mesh}` | tiny `0123456`, body.stl | MIT, Tiny, `licenses/tiny.txt` | unchanged | `{hashlib.sha256(data).hexdigest()}` |")
        _write_json(library / "scenes" / f"{part_id}.json", {
            "format": library_write.SCENE_FORMAT, "part": part_id, "part_mesh_sha256": parts["parts"][part_id]["mesh"]["sha256"],
            "about": f"A tiny scene of {part_id}.", "frame": library_write.SCENE_FRAME, "approach": [0, 0, 1],
            "opening": {"q_mm": 40, "limit_mm": 40, "joint": "the fingers' slide", "source": "a tiny model"},
            "mate": {"kind": MATE_KINDS[part_id], "matrix": MIRROR if MATE_KINDS[part_id] == "mirror" else TURNED, "part": True},
            "bodies": [{"mesh": mesh, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "triangles": 1, "matrix": IDENTITY,
                        "finger": None}],
            "see_through": SEE_THROUGH[part_id], "picture": PICTURES.get(part_id, PICTURE)})
        index["scenes"][part_id] = f"scenes/{part_id}.json"
    _write_json(library / library_write.SCENES_INDEX, index)
    (library / "NOTICE.md").write_text("# Tiny\n\n| File | Source at commit | Licence and holder | Change | SHA-256 |\n| --- | --- | --- | --- | --- |\n"
                                       + "".join(row + "\n" for row in rows), encoding="utf-8")
    return library


def _showcase_web(folder: Path) -> Path:
    """``folder``/web holding a copy of the committed files the showcase's checks read (web/library/'s parts, entries,
    notice, licences, scenes, bodies, fits and the pictures' manifest, and the showcase's document and pictures;
    web/vendor/ufactory-g1/, web/vendor/umi/ and the pad's web/vendor/flexitac-v2/; web/samples/'s index and notice);
    returns its library."""

    web = folder / "web"
    for relative in ("library/parts.json", "library/entries.json", "library/NOTICE.md", "library/shots/manifest.json",
                     f"library/{SHOWCASE_FILE}", "samples/samples.json", "samples/NOTICE.md"):
        (web / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(WEB / relative, web / relative)
    for relative in ("library/licenses", "library/scenes", "library/bodies", "library/fits", "library/showcase", "vendor/ufactory-g1",
                     "vendor/umi", "vendor/flexitac-v2"):
        shutil.copytree(WEB / relative, web / relative)
    return web / "library"


def _edit_scene(library: Path, part_id: str, edit) -> None:
    """``edit`` (the scene's document -> None) applied to scenes/<part>.json."""

    path = library / "scenes" / f"{part_id}.json"
    document = _json(path)
    edit(document)
    _write_json(path, document)


def _art(identifier: str, build_id: str, **changes) -> dict:
    """A tiny art document of a sensor's boards (docs/LIBRARY_VIEW.md), ``changes`` over it."""

    board = {"role": "rows", "physical_side": "bottom", "view_box": [0, 0, 10, 20], "region": [0, 0, 10, 20],
             "active_outline": [[0, 0], [10, 0], [10, 20]], "px": [120, 240], "front": "<svg/>", "back": "<svg/>",
             "outline": {"points": [[0, 0], [10, 0], [10, 20]], "cutouts": []}}
    return dict({"format": library_write.ART_FORMAT, "id": identifier, "build_id": build_id, "look": "photo",
                 "px_per_mm": library_write.ART_PX_PER_MM, "max_px": library_write.ART_MAX_PX,
                 "boards": {"row": board, "column": dict(board, role="columns", physical_side="top")}}, **changes)


def _view_library(library: Path, variants: dict, parts: dict, identifiers=("widowx-250-2mm", "umi-finray-2mm"), art=True,
                  stage=True, edit=None) -> Path:
    """``library`` with the tiny scenes (_scene_library) and the fixture's pictures of ``identifiers`` (_shot_library)
    whose records, as the shots tool writes them, carry their art (art/<id>.json.gz, a tiny document of the sensor's
    build), the Library view's hash (VIEW) and a gripper's stage (its scene's and the rules' hash, NUMBERS); ``edit``
    (records, library -> None) over the records before the manifest is written."""

    _scene_library(library, parts)
    _shot_library(library, variants, identifiers=identifiers)
    index = _json(library / library_write.SCENES_INDEX)
    records = _json(library / library_write.SHOTS_MANIFEST)["shots"]
    for identifier in identifiers:
        variant = variants[identifier]
        if art:
            data = library_write.art_bytes(_art(identifier, variant["build_id"]))
            (library / "art").mkdir(exist_ok=True)
            (library / library_write.art_path(identifier)).write_bytes(data)
            records[identifier].update(art=library_write.art_record(identifier, data, variant["build_id"]), view_sha256=VIEW)
        scene = index["scenes"].get(variant["part"])
        if stage and scene:
            numbers = dict(NUMBERS, ghost_cover=0.1 if SEE_THROUGH[variant["part"]] else None)
            records[identifier]["stage"] = {"scene": scene, "numbers": numbers,
                                            "scene_sha256": library_write.scene_sha256((library / scene).read_bytes(), index["rules"])}
    if edit:
        edit(records, library)
    (library / library_write.SHOTS_MANIFEST).write_text(SHOTS_TOOL.manifest_text(records), encoding="utf-8")
    return library


def _shot_library(library: Path, variants: dict, identifiers=("widowx-250-2mm",), files=None, **changes) -> Path:
    """``library``/shots/ holding the fixture as the pictures of ``identifiers`` (``files`` {kind: bytes} in its place),
    with the manifest the tool writes for them (its record() and manifest_text(), at the figure's sources of now, a
    part without a scene in the look the library's rules give it), ``changes`` over each record."""

    (library / "shots").mkdir(parents=True, exist_ok=True)
    records = {}
    # A part without a scene in the look the library's rules give it (the UMI finger's orange; none in a library
    # without scenes), read as pictures() reads it: the library's scenes.json and its parts.json, if any.
    index = library_write.scenes_index(library)
    families = _json(library / "parts.json") if (library / "parts.json").is_file() else {"parts": {}}
    for identifier in identifiers:
        data = dict({"exploded": SHOT, "assembled": SHOT, "card": SHOT_CARD}, **(files or {}))
        for kind, payload in data.items():
            (library / library_write.shot_files(identifier)[kind][0]).write_bytes(payload)
        margins = {"exploded": [590, 240, 590, 240], "assembled": [590, 240, 590, 240]}
        look = library_write.part_look_sha256(library_write.part_look(index, families, variants[identifier]["part"]))
        records[identifier] = dict(SHOTS_TOOL.record(identifier, variants[identifier], data, margins, library_write.figure_sha256(), "photo",
                                                     part_look=look), **changes)
    (library / library_write.SHOTS_MANIFEST).write_text(SHOTS_TOOL.manifest_text(records), encoding="utf-8")
    return library


class _Controls(HTMLParser):
    """The [data-option] controls inside #cadConfig with their attributes, and each select's options (a second reader,
    so a defect of library_write's cannot hide itself)."""

    VOID = {"input", "meta", "link", "br", "img", "hr", "source", "area", "base", "col", "embed", "param", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.controls: dict = {}
        self.depth = 0
        self.current = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if self.depth == 0 and attributes.get("id") == "cadConfig":
            self.depth = 1
            return
        if self.depth:
            if "data-option" in attributes:
                self.current = attributes["data-option"]
                self.controls[self.current] = (tag, attributes, [])
            elif tag == "option" and self.current is not None:
                self.controls[self.current][2].append(attributes)
            if tag not in self.VOID:
                self.depth += 1

    def handle_startendtag(self, tag, attrs):
        # <input ... />: a start tag with no end (HTMLParser's default would also end it).
        self.handle_starttag(tag, attrs)
        if self.depth and tag not in self.VOID:
            self.depth -= 1

    def handle_endtag(self, tag):
        if self.depth and tag not in self.VOID:
            self.depth -= 1
            if tag == "select":
                self.current = None


def _controls() -> dict:
    parser = _Controls()
    parser.feed((WEB / "gen.html").read_text(encoding="utf-8"))
    return parser.controls


class LibraryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parts = _json(LIBRARY / "parts.json")
        cls.entries = _json(LIBRARY / "entries.json")
        cls.plan = _plan(cls.parts)
        cls.fits = {identifier: (LIBRARY / library_write.fit_path(identifier, variant)).read_bytes()
                    for identifier, _, _, variant in cls.plan}


class FileTests(LibraryTestCase):
    def test_every_file_is_tabled_in_the_notice_or_the_projects_own(self) -> None:
        rows = _notice()
        self.assertGreaterEqual(len(rows), 12, "the seven meshes and the five licence texts")
        for path in sorted(LIBRARY.rglob("*")):
            if path.is_dir():
                continue
            relative = path.relative_to(LIBRARY).as_posix()
            with self.subTest(file=relative):
                if relative in rows:
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), rows[relative][4])
                else:
                    self.assertRegex(relative, OWN_FILE, "a file neither tabled in NOTICE.md nor this project's own")
        for relative in rows:
            with self.subTest(row=relative):
                self.assertTrue((LIBRARY / relative).is_file(), "a NOTICE row whose file is missing")

    def test_the_fits_and_images_are_exactly_the_entries(self) -> None:
        listed = {variant["fit"] for variant in self.entries["variants"].values() if variant["fit"].startswith("fits/")}
        on_disk = {path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "fits").glob("*")}
        self.assertEqual(on_disk, listed, "a fit of no variant, or a variant with no fit: run tools/library_write.py")
        # The pictures: each sensor's three files where entries.json names them, and the manifest when there is one.
        images = {path for variant in self.entries["variants"].values() if variant["image"]
                  for path in (variant["image"]["exploded"]["src"], variant["image"]["exploded"]["card"], variant["image"]["assembled"]["src"])}
        on_disk = {path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "shots").glob("*")} if (LIBRARY / "shots").is_dir() else set()
        self.assertEqual(on_disk - {library_write.SHOTS_MANIFEST}, images, "a picture of no sensor, or a sensor's picture missing: "
                         "re-shoot with tools/browser/library_shots.py, then run tools/library_write.py")
        self.assertEqual(library_write.SHOTS_MANIFEST in on_disk, bool(images))

    def test_the_art_scenes_and_bodies_are_the_files_the_entries_and_scenes_name(self) -> None:
        # The 3D view's files (docs/LIBRARY_VIEW.md): each sensor's art where its view names it and no other; scenes/
        # the index and the scenes it maps; every body a file a scene names, tabled in NOTICE.md or the project's own rail
        # (the scene builder's other inputs never committed).
        listed = {variant["view"]["art"] for variant in self.entries["variants"].values() if variant["view"]}
        on_disk = {path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "art").glob("*")} if (LIBRARY / "art").is_dir() else set()
        self.assertEqual(on_disk, listed, "an art of no sensor's view, or a view's art missing: re-shoot with tools/browser/library_shots.py, "
                         "then run tools/library_write.py")
        index = _json(LIBRARY / library_write.SCENES_INDEX)
        scenes = {path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "scenes").glob("*")}
        self.assertEqual(scenes, {library_write.SCENES_INDEX, *index["scenes"].values(), SHOWCASE_SCENE})
        named = {body["mesh"] for path in index["scenes"].values() for body in _json(LIBRARY / path)["bodies"]}
        # The showcase's own scene (no part's: not in the index) and its bodies of the Library (the vendor's are
        # beside it, web/vendor/ufactory-g1/: ShowcaseTests).
        named |= {body["mesh"] for body in _json(LIBRARY / SHOWCASE_SCENE)["bodies"] if not body["mesh"].startswith("../")}
        bodies = {path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "bodies").rglob("*") if path.is_file()} if (LIBRARY / "bodies").is_dir() else set()
        self.assertEqual(bodies, named)
        rows = _notice()
        for mesh in sorted(named):
            with self.subTest(body=mesh):
                self.assertTrue(mesh in rows or library_write.own_body(mesh, (LIBRARY / mesh).read_bytes()),
                                "a body neither tabled in NOTICE.md nor the project's own (the rail, a shape tools/library_split.py drew)")
                self.assertFalse(mesh in rows and library_write.own_body(mesh), "the project's own drawing has no row")
        self.assertNotIn(RAIL, rows, "the rail is the project's own (NOTICE.md says so, with no row)")
        # Each view's scene its part's (a gripper's), a fingertip's none.
        for identifier, variant in self.entries["variants"].items():
            if variant["view"]:
                with self.subTest(view=identifier):
                    self.assertEqual(variant["view"], library_write.view_record(identifier, index["scenes"].get(variant["part"])))

    def test_no_vendor_model_of_the_deny_list(self) -> None:
        places = {pinned: f"vendor/ufactory-g1/{name}" for name, pinned in SHOWCASE_FILES.items()}
        self.assertEqual(len(places), len(SHOWCASE_FILES))
        seen = set()
        for path in sorted(WEB.rglob("*")):
            if path.is_file():
                relative = path.relative_to(WEB).as_posix()
                with self.subTest(file=relative):
                    data = path.read_bytes()
                    digest = hashlib.sha256(data).hexdigest()
                    self.assertNotIn(digest, DENIED_SHA256)
                    # The showcase's vendor file itself, unsplit and undecimated (out of the list since 2026-11-12),
                    # under its own header or another.
                    self.assertNotEqual(digest, SHOWCASE_SOURCE[1], "the vendor's own file is never published")
                    if len(data) == SHOWCASE_SOURCE[2]:
                        self.assertNotEqual(hashlib.sha256(data[80:]).hexdigest(), SHOWCASE_SOURCE_TRIANGLES, "nor under another header")
                    # The showcase's meshes are in their folder alone: no copy under another name anywhere under web/.
                    if digest in places:
                        self.assertEqual(relative, places[digest], "a copy of a mesh of the vendor's folder")
                        seen.add(digest)
                    if LIBRARY in path.parents:
                        self.assertIsNone(DENIED_NAME.search(path.name))
        self.assertEqual(seen, set(places), "each mesh of the vendor's folder once, in its place")
        names = [*self.entries["order"], *self.entries["variants"]]
        for part in self.parts["parts"].values():
            names += [part["title"], part["mesh"]["file"], part["mesh"]["name"]]
        for name in names:
            with self.subTest(name=name):
                self.assertIsNone(DENIED_NAME.search(name))

    def test_the_library_stays_within_its_budget(self) -> None:
        # Its pictures have their own (below): the sensors' (shots/) and, since 2026-11-12, the showcase's three
        # (showcase/: 217 KB, which the 12 MB of the fits, meshes, bodies and art had no room to spare for).
        pictures = (LIBRARY / "shots", LIBRARY / "showcase")
        size = sum(path.stat().st_size for path in LIBRARY.rglob("*") if path.is_file() and path.parent not in pictures)
        self.assertLessEqual(size, BUDGET_BYTES, f"web/library/ is {size} bytes")

    def test_the_pictures_stay_within_their_budget(self) -> None:
        shots = [path for folder in ("shots", "showcase") for path in sorted((LIBRARY / folder).glob("*"))]
        size = sum(path.stat().st_size for path in shots)
        self.assertLessEqual(size, SHOTS_BUDGET_BYTES, f"web/library/shots/ and showcase/ are {size} bytes")
        # The grid's first screen: every card's picture, the showcase's large card's with them (it is the first); the UMI
        # shelf's cards their Assembled picture's full file since 2026-11-16 (shelf_cards()).
        shelf = set(shelf_cards(self.entries))
        first = sum((LIBRARY / (image["assembled"]["src"] if identifier in shelf else image["exploded"]["card"])).stat().st_size
                    for identifier in grid_cards(self.entries) for image in [self.entries["variants"][identifier]["image"]] if image)
        first += (LIBRARY / _json(LIBRARY / SHOWCASE_FILE)["image"]["card"]["src"]).stat().st_size
        self.assertLessEqual(first, FIRST_SCREEN_BYTES, f"the grid's first screen's pictures are {first} bytes")
        self.assertLess(sum(path.stat().st_size for path in (LIBRARY / "showcase").glob("*")), 300_000, "the showcase's three pictures")

    def test_the_page_never_says_cad(self) -> None:
        # The page's word is Gen by Surface; the Library shows these texts (its notice is linked from its footer).
        for path in (LIBRARY / "NOTICE.md", LIBRARY / "parts.json", LIBRARY / "entries.json", SHOWCASE / "NOTICE.md"):
            with self.subTest(file=path.relative_to(WEB).as_posix()):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"\bCAD\b")


class LicenceTests(LibraryTestCase):
    def test_each_parts_licence_is_open_tabled_pinned_and_states_its_change(self) -> None:
        rows = _notice()
        umi_rows = dict(re.findall(r"^\| `([\w.-]+)` \|[^|]*\| `([0-9a-f]{64})` \|$",
                                   (WEB / "vendor" / "umi" / "NOTICE.md").read_text(encoding="utf-8"), re.MULTILINE))
        for part_id in self.parts["order"]:
            part = self.parts["parts"][part_id]
            licence = part["license"]
            with self.subTest(part=part_id):
                self.assertIn(licence["spdx"], SPDX)
                self.assertTrue(licence["holder"])
                self.assertTrue(licence["text"].startswith("licenses/") and licence["text"] in rows, licence["text"])
                commit = re.search(r"/([0-9a-f]{40})/", licence["source"])
                self.assertIsNotNone(commit, "the source is pinned to a commit")
                self.assertTrue(licence["source"].startswith("https://github.com/"))
                self.assertTrue(licence["change"])
                mesh = part["mesh"]["file"]
                if mesh.startswith("../vendor/umi/"):
                    # The page's default part: tabled in web/vendor/umi/NOTICE.md, with the same licence's bytes.
                    self.assertEqual(umi_rows[mesh.rpartition("/")[2]], part["mesh"]["sha256"])
                    self.assertEqual((LIBRARY / licence["text"]).read_bytes(), (WEB / "vendor" / "umi" / "LICENSE").read_bytes())
                    self.assertEqual(licence["change"], "unchanged")
                    continue
                row = rows[mesh]
                self.assertEqual(row[4], part["mesh"]["sha256"])
                self.assertIn(commit.group(1)[:7], row[1], "the NOTICE row's commit is the source's")
                self.assertIn(licence["spdx"], row[2])
                self.assertIn(licence["text"], row[2])
                if part_id == "franka-hand":
                    self.assertIn("convex hull", licence["change"])
                    self.assertIn("modified: convex hull", row[3])
                elif part.get("family") == TAPERS:
                    # Cut from the page's own UMI finger (its source, its licence), a modified file (Apache 4(b)).
                    kind, tip = re.fullmatch(r"umi-([a-z-]+)-tip([\d.]+)", part_id).groups()
                    _, profile, height, _ = TAPER_KINDS[kind]
                    self.assertEqual(licence["change"], f"tip cut ({profile}, h {height} mm, tip {tip} mm) from UMI-Soft-Gripper-Finger.stl")
                    self.assertEqual(row[3].strip(), f"modified: {licence['change']}")
                    self.assertEqual(licence["source"], self.parts["parts"]["umi-finray"]["license"]["source"])
                else:
                    self.assertEqual(licence["change"], "unchanged")
                    self.assertEqual(row[3].strip(), "unchanged")

    def test_each_bodys_licence_is_open_tabled_pinned_and_states_its_change(self) -> None:
        # The grippers' bodies of the 3D view (NOTICE.md's rows of bodies/, 2026-11-05): each a third-party file at a pinned
        # commit, its licence open with its text tabled, its change stated (the decimation: a modified file); the rail
        # the project's own, said to be no MakerMods hardware; the mirror pairs' other board the mirror image.
        rows = _notice()
        text = (LIBRARY / "NOTICE.md").read_text(encoding="utf-8")
        bodies = {path: row for path, row in rows.items() if path.startswith("bodies/")}
        index = _json(LIBRARY / library_write.SCENES_INDEX)
        if index["scenes"]:
            self.assertTrue(bodies, "the scenes' bodies tabled")
            self.assertIn("rail.stl", text)
            self.assertIn("not MakerMods hardware", text)
            self.assertIn("mirror", text)
        for path, row in sorted(bodies.items()):
            with self.subTest(body=path):
                self.assertTrue([licence for licence in SPDX if licence in row[2]], row[2])
                texts = re.findall(r"`(licenses/[\w.-]+)`", row[2])
                self.assertTrue(texts)
                for licence in texts:
                    self.assertIn(licence, rows)
                self.assertRegex(row[1], r"`[0-9a-f]{7}`", "the source pinned to a commit")
                self.assertRegex(row[3].strip(), r"^(unchanged|modified: .+)$")
                self.assertTrue(path.endswith(".stl"))

    def test_each_licence_text_is_tabled_unchanged_at_a_commit(self) -> None:
        rows = _notice()
        texts = {path for path in rows if path.startswith("licenses/")}
        # The parts' texts and, since the whole-gripper scenes of 2026-11-05, those the rows of the scenes' bodies name.
        named = {part["license"]["text"] for part in self.parts["parts"].values()}
        named |= {text for path, row in rows.items() if not path.startswith("licenses/") for text in re.findall(r"`(licenses/[\w.-]+)`", row[2])}
        self.assertEqual(texts, named)
        for path in texts:
            with self.subTest(text=path):
                self.assertEqual(rows[path][3].strip(), "unchanged")
                self.assertRegex(rows[path][1], r"`[0-9a-f]{7}`")


class EntriesTests(LibraryTestCase):
    def test_entries_json_is_the_writers_of_parts_and_the_fits(self) -> None:
        document = library_write.entries(self.parts, self.fits)
        self.assertEqual(self.entries, document, "entries.json is stale: run tools/library_write.py")
        self.assertEqual((LIBRARY / "entries.json").read_text(encoding="utf-8"), library_write.entries_text(document))
        self.assertEqual(self.entries["format"], "flexitac-library/v1")

    def test_each_mesh_is_the_file_with_its_facts(self) -> None:
        for part_id, part in self.entries["parts"].items():
            with self.subTest(part=part_id):
                data = (LIBRARY / part["mesh"]["file"]).read_bytes()
                (facets,) = struct.unpack("<I", data[80:84])
                self.assertEqual(len(data), 84 + 50 * facets, "a binary STL")
                self.assertEqual((part["mesh"]["bytes"], part["mesh"]["sha256"], part["mesh"]["facets"]),
                                 (len(data), hashlib.sha256(data).hexdigest(), facets))
                self.assertEqual(part["mesh"]["sha256"], self.parts["parts"][part_id]["mesh"]["sha256"])
                expected = "UMI-Soft-Gripper-Finger.stl" if part_id == "umi-finray" else f"{part_id}.stl"
                self.assertEqual(part["mesh"]["name"], expected)

    def test_ids_labels_shelves_and_the_start_shelf(self) -> None:
        for identifier, variant in self.entries["variants"].items():
            part = self.entries["parts"][variant["part"]]
            with self.subTest(variant=identifier):
                pitch = variant["pitch_mm"]
                written = str(pitch) if isinstance(pitch, int) else repr(pitch)
                self.assertEqual(identifier, f"{variant['part']}-{written}mm")
                self.assertRegex(identifier, r"^[a-z0-9]+(-[a-z0-9.]+)*-[0-9]+(\.[0-9]+)?mm$")
                self.assertLessEqual(len(variant["label"]), library_write.LABEL_MAX)
                self.assertLessEqual(len(NOTE_PREFIX + variant["label"]), NOTE_MAX)
                if part["family"] == TAPERS:
                    # A tip's own label (its one pitch is the family's): 'UMI trapezoid tip, 13.8 mm', 'UMI short convex, 9.8 mm'.
                    tip = re.fullmatch(r"umi-([a-z-]+)-tip([\d.]+)", variant["part"])
                    self.assertEqual(variant["label"], f"UMI {TAPER_KINDS[tip.group(1)][0]}, {tip.group(2)} mm")
                else:
                    self.assertEqual(variant["label"], f"{part['title']}, {written} mm")
                self.assertEqual(variant["badge"], "Fine" if pitch == 1 else None)
                # The page's default fill at every pitch since the user's decision of 2026-11-06 ("默认的pitch/trace大小,现在都是
                # 0.7,直接都改成0.5"; 0.65 at 1 mm and 0.7 elsewhere before).
                self.assertEqual(variant["fill"], 0.5)
        words = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        for part_id, part in self.entries["parts"].items():
            with self.subTest(part=part_id):
                pitches = [self.entries["variants"][identifier]["pitch_mm"] for identifier in part["variants"]]
                self.assertEqual(pitches, sorted(pitches))
                self.assertEqual(self.entries["variants"][part["default"]]["pitch_mm"], 2)
                if part["family"]:
                    self.assertIsNone(part["shelf"], "a family's part has no shelf of its own")
                    continue
                if any(family["shelf"] == part_id for family in self.entries["families"].values()):
                    continue  # the UMI finger's shelf names its shapes (below)
                # One wording on every shelf (the user's decision of 2026-11-05, 最好统一): the count and the range;
                # every gripper's pitches begin at 1 mm.
                shelf = re.fullmatch(r"(\w+) pitches, ([\d.]+) to ([\d.]+) mm\.", part["shelf"])
                self.assertIsNotNone(shelf, part["shelf"])
                self.assertEqual((words[shelf.group(1)], float(shelf.group(2)), float(shelf.group(3))),
                                 (len(pitches), min(pitches), max(pitches)))
                self.assertEqual(min(pitches), 1)
        self.assertEqual({part_id: part["shelf"] for part_id, part in self.entries["parts"].items() if part_id in self.entries["order"]},
                         {"umi-finray": "Six finger shapes, straight to pointed.", "franka-hand": "Four pitches, 1 to 2.5 mm.",
                          "widowx-250": "Four pitches, 1 to 3 mm.", "trossen-widowx-ai": "Four pitches, 1 to 3 mm.", "arx-x5": "Four pitches, 1 to 4 mm.",
                          "i2rt-yam": "Four pitches, 1 to 4 mm.", "unitree-dex1": "Four pitches, 1 to 3 mm.", "makermods-metal": "Four pitches, 1 to 3 mm."})
        # The writer's wording itself, on shelves the Library does not have: one pitch, two with no family, a family of
        # two cards (the part's own shape and its cards': the last card's shape named).
        family = {"cards": [{"axes": [{"choices": [{"label": "Trapezoid"}, {"label": "Convex arc"}]}]},
                            {"axes": [{"choices": [{"label": "Concave arc"}]}]}]}
        self.assertEqual([library_write.shelf([{"pitch_mm": 2}]), library_write.shelf([{"pitch_mm": 2.5}, {"pitch_mm": 1.5}]),
                          library_write.shelf([{"pitch_mm": 2}, {"pitch_mm": 1}, {"pitch_mm": 4}], [family])],
                         ["One pitch, 2 mm.", "Two pitches, 1.5 to 2.5 mm.", "Three finger shapes, straight to concave arc."])
        # The shelf's own card is named by its shape (a shelved part's card, the UMI finger's 'Straight finger'); no
        # other part has one.
        self.assertEqual({part_id: part["card"] for part_id, part in self.entries["parts"].items() if part["card"]}, {"umi-finray": "Straight finger"})
        # The grid's cards and shelves are the grippers' (the family's parts are one card on the UMI shelf); "start" is
        # each one's 2 mm sensor, the sensor its card opens (the page's layout of 2026-11-06).
        self.assertEqual(self.entries["order"], [part for part in self.parts["order"] if not self.parts["parts"][part].get("family")])
        self.assertEqual(self.entries["order"], ["umi-finray", "franka-hand", "widowx-250", "trossen-widowx-ai", "arx-x5", "i2rt-yam",
                                                 "unitree-dex1", "makermods-metal"])
        self.assertEqual(self.entries["start"], [self.entries["parts"][part]["default"] for part in self.entries["order"]])
        self.assertEqual(len(self.entries["variants"]), 58, "8 grippers by 4 pitches and 26 tapered tips")


class PictureTests(LibraryTestCase):
    """The pictures (shots/; tools/browser/library_shots.py shoots them, tools/library_write.py writes "image" from its
    manifest; the user's request of 2026-11-05: the cards show the finger with the sensor on it)."""

    def test_the_committed_pictures_are_of_their_sensors_fits(self) -> None:
        images, problems, older, views = library_write.pictures(self.entries["variants"])
        self.assertEqual(problems, [], "the wrong sensor pictured, or a broken picture: re-shoot with tools/browser/library_shots.py, "
                                       "then run tools/library_write.py")
        self.assertEqual(images, {identifier: variant["image"] for identifier, variant in self.entries["variants"].items()})
        # Each sensor's 3D view the one its record gives (its art, a gripper's stage; null before the shoot).
        self.assertEqual(views, {identifier: variant["view"] for identifier, variant in self.entries["variants"].items()})
        if older:
            # A warning only: the public CI cannot run a browser to shoot them again.
            warnings.warn(library_write.older_note(older))

    def test_every_sensor_of_the_library_has_its_own_picture(self) -> None:
        # The requirement since the set of 2026-11-05 (shot once with the approved look, every card the finger with the
        # sensor on it): every sensor of the shipped Library pictured, its shot of its own fit and build (the wrong
        # sensor never pictured), its image the contract's; no shot of a sensor the Library does not list.
        manifest = _json(LIBRARY / library_write.SHOTS_MANIFEST)
        self.assertEqual(sorted(manifest["shots"]), sorted(self.entries["variants"]),
                         "a sensor without its picture: re-shoot with tools/browser/library_shots.py, then run tools/library_write.py")
        for identifier, variant in self.entries["variants"].items():
            with self.subTest(sensor=identifier):
                shot = manifest["shots"][identifier]
                self.assertEqual((shot["fit_sha256"], shot["build_id"]), (variant["fit_sha256"], variant["build_id"]))
                self.assertEqual(variant["fit_sha256"], hashlib.sha256((LIBRARY / variant["fit"]).read_bytes()).hexdigest())
                # A picture of the whole gripper (its record's stage) says so in its alt text (its scene's words).
                picture = _json(LIBRARY / shot["stage"]["scene"])["picture"] if shot.get("stage") else None
                self.assertEqual(variant["image"], library_write.image_record(identifier, variant["label"], picture))

    def test_every_sensor_of_the_library_has_its_3d_view(self) -> None:
        # The requirement since the shoot of 2026-11-06 (the one explode and the fill 0.5 merged): every sensor's art
        # written and each gripper's stage recorded, so VIEW_REQUIRED is set and a record without them is refused
        # (tools/library_write.py --check, the site build); every sensor's page turns in 3D (the user's request of
        # 2026-11-05), a gripper's drawn whole by its scene, the UMI finger's and its tapered tips' at the fingertip.
        self.assertIs(library_write.VIEW_REQUIRED, True, "the shoot wrote every sensor's art and each gripper's stage")
        manifest = _json(LIBRARY / library_write.SHOTS_MANIFEST)
        scenes = _json(LIBRARY / library_write.SCENES_INDEX)["scenes"]
        grippers = library_write.gripper_parts(self.parts)
        self.assertEqual(sorted(scenes), sorted(grippers))
        for identifier, variant in self.entries["variants"].items():
            with self.subTest(sensor=identifier):
                shot = manifest["shots"][identifier]
                self.assertEqual((shot["art"]["path"], shot["art"]["build_id"]), (library_write.art_path(identifier), variant["build_id"]))
                scene = scenes.get(variant["part"])
                self.assertEqual(variant["view"], library_write.view_record(identifier, scene))
                if variant["part"] in grippers:
                    self.assertEqual(shot["stage"]["scene"], scene)
                    self.assertIsInstance(shot["stage"]["numbers"], dict)
                else:
                    self.assertNotIn("stage", shot)

    @PICTURES_ONLY
    def test_the_writers_check_wants_every_sensors_picture(self) -> None:
        # tools/library_write.py --check on a copy of the Library (its fits read, none fitted: only=[]) whose pictures
        # are the fixture's: current with every sensor's, stale with one sensor's gone though entries.json says so
        # (its image null, as the writer writes it), which writing only reports.
        dropped = "widowx-250-1mm"
        with tempfile.TemporaryDirectory() as folder:
            library = Path(folder) / "library"
            for name in ("meshes", "fits"):
                shutil.copytree(LIBRARY / name, library / name)
            shutil.copy(LIBRARY / "parts.json", library / "parts.json")
            shutil.copytree(WEB / "vendor" / "umi", Path(folder) / "vendor" / "umi")

            # The grippers' tiny scenes (the 3D view's: scenes() wants each gripper's), the pictures without a 3D view.
            _scene_library(library, self.parts)

            def run(identifiers, check=True):
                shutil.rmtree(library / "shots", ignore_errors=True)
                _shot_library(library, self.entries["variants"], identifiers=tuple(identifiers))
                document = library_write.entries(self.parts, self.fits, library)
                (library / "entries.json").write_text(library_write.entries_text(document), encoding="utf-8")
                said = []
                return library_write.run(only=[], check=check, library=library, out=said.append), said

            # The sensors in the Library's order (the plan's: parts.json's, each part's by pitch), as the warning names them.
            ordered = [row[0] for row in self.plan]
            unviewed = f"library_write: warning: {library_write.view_note(ordered)}"
            self.assertEqual(run(self.entries["variants"]), (0, [unviewed, "library_write: 58 sensors, all current, each with its picture, 0 with a 3D view"]))
            others = [identifier for identifier in ordered if identifier != dropped]
            self.assertEqual(run(others), (1, [
                f"stale: picture {dropped}: no picture: re-shoot with tools/browser/library_shots.py --only {dropped}",
                f"library_write: warning: {library_write.view_note(others)}",
                "library_write: the library's pictures are stale: re-shoot with tools/browser/library_shots.py, then run tools/library_write.py"]))
            code, said = run(others, check=False)
            self.assertEqual((code, said[0]), (0, f"library_write: picture {dropped}: no picture: re-shoot with tools/browser/library_shots.py --only {dropped}"))

    def test_the_shots_tool_centres_each_drawing(self) -> None:
        # library_shots.py centring() (2026-11-05: frameView balances only the axis that binds, the height at 16:10, so
        # the UMI finger's drawing stood 72 px left of the middle on its 3 mm sensor): half of each axis's difference,
        # toward the larger margin, an odd one's pixel right or below; nothing cut (each margin its axis's mean).
        centring = SHOTS_TOOL.centring
        self.assertEqual(centring([405, 51, 548, 52]), (71, 0))
        self.assertEqual(centring([476, 51, 463, 52]), (-7, 0))
        self.assertEqual(centring([340, 50, 404, 41]), (32, -5))
        for margins in ([405, 51, 548, 52], [476, 51, 463, 52], [340, 50, 404, 41], [30, 30, 30, 30], [1, 2, 3, 900]):
            with self.subTest(margins=margins):
                dx, dy = centring(margins)
                left, top, right, bottom = margins
                after = [left + dx, top + dy, right - dx, bottom - dy]
                self.assertIn(after[2] - after[0], (0, 1))
                self.assertIn(after[3] - after[1], (0, 1))
                self.assertGreaterEqual(min(after), min(margins))
        # The committed pictures as the tool wrote them: each drawing centred, none cut.
        for identifier, shot in _json(LIBRARY / library_write.SHOTS_MANIFEST)["shots"].items():
            for mode, (left, top, right, bottom) in shot["margins_px"].items():
                with self.subTest(sensor=identifier, mode=mode):
                    self.assertEqual((right - left in (0, 1), bottom - top in (0, 1), min(left, top, right, bottom) > 0), (True, True, True))

    def test_gen_by_surface_s_figure_is_pinned_apart_from_the_library_s_look(self) -> None:
        # Until 2026-11-12 the Library's pictures of the UMI finger and its tapered tips were Gen by Surface's figure byte
        # for byte (library_shots.py --check-generator).  The Library now draws those parts in the real finger's orange;
        # Gen by Surface keeps its grey part, and its figure of each such sensor is pinned (tools/browser/
        # generator_figure.json: the three pictures as the shots tool encodes them, of the entry's fit and build), which
        # --check-generator holds it to in the browser.  Here, without one: the pin is of exactly these sensors, and the
        # Library's pictures are the figure's own files where the rules give the part no look, other files where they do.
        tool = SHOTS_TOOL
        index = _json(LIBRARY / library_write.SCENES_INDEX)
        pin = tool.read_pin()
        fingertips = tool.fingertip_sensors(self.entries, index["scenes"])
        self.assertEqual(sorted(fingertips), sorted(identifier for identifier, variant in self.entries["variants"].items() if variant["part"].startswith("umi-")))
        self.assertEqual(len(fingertips), 30, "the UMI finger's four pitches and its 26 tips")
        self.assertEqual(tool.pin_problems(pin, self.entries, index["scenes"]), [])
        self.assertEqual(tool.GENERATOR_PIN.read_text(encoding="utf-8"), tool.pin_text(pin["shots"], pin["figure_sha256"]), "as --pin-generator writes it")
        self.assertRegex(pin["figure_sha256"], r"^[0-9a-f]{64}$")
        shots = _json(LIBRARY / library_write.SHOTS_MANIFEST)["shots"]
        for identifier in fingertips:
            variant = self.entries["variants"][identifier]
            pictured = {kind: {"bytes": item["bytes"], "sha256": item["sha256"]} for kind, item in shots[identifier]["files"].items()}
            with self.subTest(sensor=identifier):
                self.assertEqual((pin["shots"][identifier]["fit_sha256"], pin["shots"][identifier]["build_id"]), (variant["fit_sha256"], variant["build_id"]))
                self.assertEqual(tool.figure_record(variant, {kind: b"abc" for kind in pictured})["files"]["card"],
                                 {"bytes": 3, "sha256": hashlib.sha256(b"abc").hexdigest()})
                if library_write.part_look(index, self.parts, variant["part"]) is None:
                    self.assertEqual(pictured, pin["shots"][identifier]["files"], "no look: the Library's pictures are Gen by Surface's figure")
                else:
                    for kind, item in pictured.items():
                        self.assertNotEqual(item["sha256"], pin["shots"][identifier]["files"][kind]["sha256"], f"{kind}: in its look, not the grey figure's")
        # What makes a pin not this library's.
        first, gripper = fingertips[0], "widowx-250-2mm"
        fix = "pin Gen by Surface's figure again with tools/browser/library_shots.py --pin-generator"

        def problems(edit) -> list:
            changed = json.loads(json.dumps(pin))
            edit(changed)
            return tool.pin_problems(changed, self.entries, index["scenes"])

        other = "surface-32x12-000000000000"
        self.assertEqual(problems(lambda document: document.update(format="flexitac-generator-figure/v0")),
                         ["the pin's format is 'flexitac-generator-figure/v0', not flexitac-generator-figure/v1"])
        self.assertEqual(problems(lambda document: document["shots"].pop(first)), [f"{first}: Gen by Surface's figure is not pinned: {fix} {first}"])
        self.assertEqual(problems(lambda document: document["shots"][first].update(build_id=other)),
                         [f"{first}: the pin is of another fit or build than the entry's ({other}, not {self.entries['variants'][first]['build_id']}): {fix} {first}"])
        self.assertEqual(len(problems(lambda document: document["shots"][first].update(fit_sha256="0" * 64))), 1)
        missing = f"{first}: the pin has not the bytes and SHA-256 of its exploded, assembled, card pictures: {fix} {first}"
        self.assertEqual(problems(lambda document: document["shots"][first]["files"].pop("card")), [missing])
        self.assertEqual(problems(lambda document: document["shots"][first]["files"]["card"].update(sha256="0" * 63)), [missing])
        self.assertEqual(problems(lambda document: document["shots"][first]["files"]["card"].update(bytes=0)), [missing])
        self.assertEqual(problems(lambda document: document["shots"].update({gripper: document["shots"][first]})),
                         [f"{gripper}: pinned, but no sensor of a part without a scene: {fix}"])
        self.assertEqual(tool.read_pin(Path("no-such-folder") / "generator_figure.json")["shots"], {})

    def test_the_look_is_held_to_the_part_s_pixels(self) -> None:
        # library_shots.py --check-generator's fourth comparison (view_differences(), view_problems()): the Library's view
        # of a part in its look against Gen by Surface's figure, with the view in that look's other colour as the witness
        # of which pixels the part's colour reaches.  Tiny drawings: RGBA, one row; g the grey part, o its orange, b the
        # other colour, s a sheet's pixel, e a sheet's edge on the ground (half alpha), _ the transparent ground.
        tool = SHOTS_TOOL
        pixel = {"g": (200, 204, 206, 255), "o": (232, 90, 5, 255), "b": (104, 218, 133, 255), "s": (207, 121, 0, 255), "t": (30, 30, 31, 255),
                 "e": (207, 121, 0, 128), "_": (0, 0, 0, 0), "x": (1, 2, 3, 255), "h": (232, 90, 5, 128)}
        drawing = lambda text: bytes(value for letter in text for value in pixel[letter])  # noqa: E731
        figure, look, other = drawing("_gggssste_"), drawing("_ooossste_"), drawing("_bbbssste_")
        counts = tool.view_differences(figure, look, other)
        self.assertEqual(counts, {"drawn": 8, "alpha": 0, "part": 3, "sheets": 5, "wrong": 0})
        self.assertEqual(tool.view_problems(counts), [])
        # A sheet's pixel drawn otherwise in the look (the look not the part's alone): the same in both colours, not the figure's.
        counts = tool.view_differences(figure, drawing("_oooxsste_"), drawing("_bbbxsste_"))
        self.assertEqual(counts, {"drawn": 8, "alpha": 0, "part": 3, "sheets": 5, "wrong": 1})
        self.assertEqual(tool.view_problems(counts), ["1 of the 5 px the part's colour does not reach are not the figure's (the look is not the part's alone)"])
        # Another outline: a pixel drawn where the figure draws none, one not drawn where it does, an edge of another alpha.
        counts = tool.view_differences(figure, drawing("ooooss_teh"), drawing("bbbbss_teh"))
        self.assertEqual((counts["alpha"], counts["drawn"]), (3, 9))
        self.assertEqual(tool.view_problems(counts)[0], "3 px of another alpha than the figure's (another outline)")
        # The look not drawn (the view the grey figure in both colours): the part's colour reaches nothing.
        counts = tool.view_differences(figure, figure, figure)
        self.assertEqual(counts, {"drawn": 8, "alpha": 0, "part": 0, "sheets": 8, "wrong": 0})
        self.assertEqual(tool.view_problems(counts), ["the part's colour reaches 0 of the 8 px drawn, under 0.1 of them (is the look drawn?)"])
        # Everything drawn otherwise: nothing left to hold to the figure.
        counts = tool.view_differences(drawing("gggggggs"), drawing("ooooooos"), drawing("bbbbbbbs"))
        self.assertEqual(tool.view_problems(counts), ["the part's colour reaches all but 1 of the 8 px drawn, under 0.25 of them left (the sheets drawn otherwise too?)"])
        self.assertEqual((tool.PART_SHARE_MIN, tool.SHEETS_SHARE_MIN), (0.1, 0.25))
        with self.assertRaises(tool.ShotError):
            tool.view_differences(figure, look, other[:-4])
        # The other colour: every channel half the range off, whatever the colour (a mid grey too); the rest of the look kept.
        orange = {"color": "#e85a1c", "metalness": 0, "roughness": 0.6, "env_intensity": 0.3}
        self.assertEqual(tool.other_look(orange), dict(orange, color="#68da9c"))
        self.assertEqual((tool.other_look({"color": "#808080"}), tool.other_look({"color": "#00ff7f"})), ({"color": "#000000"}, {"color": "#807fff"}))
        # scenes.json as the check serves it: the rules without their looks (the part as Gen by Surface draws it), or with
        # one look for the one part; the scenes and every other rule as they are.
        index = _json(LIBRARY / library_write.SCENES_INDEX)
        plain = dict(index, rules={key: value for key, value in index["rules"].items() if key not in library_write.RULES_OPTIONAL})
        self.assertEqual(json.loads(tool.served_scenes(index, "umi-finray", None)), plain)
        given = {"look": tool.other_look(orange), "smooth_deg": None}
        self.assertEqual(json.loads(tool.served_scenes(index, "umi-trap-tip5.8", given)),
                         dict(plain, rules=dict(plain["rules"], part_looks={"umi-trap-tip5.8": given["look"]})))
        self.assertEqual(json.loads(tool.served_scenes(index, "umi-finray", dict(given, smooth_deg=35)))["rules"]["part_smooth_deg"], 35)
        self.assertEqual(library_write.part_look(json.loads(tool.served_scenes(index, "umi-trap-tip5.8", given)), self.parts, "umi-trap-tip5.8"), given)
        self.assertIsNone(library_write.part_look(json.loads(tool.served_scenes(index, "umi-finray", None)), self.parts, "umi-finray"))

    def test_the_pad_s_tint_is_held_to_the_assembled_sheets(self) -> None:
        # library_shots.py --check-generator's fifth comparison (pad_differences(), pad_problems()), where the rules give
        # the assembled pad a tint (part_pad, the user's decision of 2026-11-14): the Library's view with the tint (the
        # pictures') against the view without it, with the view without it in the look's other colour as the witness of
        # the part's pixels.  Tiny drawings: RGBA, one row; o the part's orange, b its other colour, s a sheet's pixel, d
        # the pad's dark olive over it, e a sheet's edge on the ground (half alpha), _ the transparent ground.
        tool = SHOTS_TOOL
        pixel = {"o": (232, 90, 5, 255), "b": (104, 218, 133, 255), "s": (207, 121, 0, 255), "d": (111, 84, 19, 255), "e": (207, 121, 0, 128),
                 "_": (0, 0, 0, 0)}
        drawing = lambda text: bytes(value for letter in text for value in pixel[letter])  # noqa: E731
        look, other = drawing("_ooossssse_"), drawing("_bbbssssse_")
        counts = tool.pad_differences(look, drawing("_ooosdddse_"), other)
        self.assertEqual(counts, {"drawn": 9, "alpha": 0, "pad": 3, "part": 0})
        self.assertEqual((tool.pad_problems("assembled", counts), tool.pad_problems("exploded", counts)),
                         ([], ["the pad changes 3 px in exploded (it is the assembled sensor's alone)"]))
        # Exploded as without the tint: nothing changed, and nothing asked of it.
        counts = tool.pad_differences(look, look, other)
        self.assertEqual((counts, tool.pad_problems("exploded", counts)), ({"drawn": 9, "alpha": 0, "pad": 0, "part": 0}, []))
        self.assertEqual(tool.pad_problems("assembled", counts), ["the pad changes 0 of the 9 px drawn, under 0.05 of them (is the pad drawn?)"])
        # The tint on the part's pixels (the part's colour reaches them), and an outline of another alpha.
        counts = tool.pad_differences(look, drawing("_oddsddsse_"), other)
        self.assertEqual(counts, {"drawn": 9, "alpha": 0, "pad": 4, "part": 2})
        self.assertEqual(tool.pad_problems("assembled", counts), ["the pad changes 2 px of the part (the pad is not the sheets' alone)"])
        counts = tool.pad_differences(look, drawing("_ooosdddsd_"), other)
        self.assertEqual((counts["alpha"], counts["pad"]), (1, 4))
        self.assertEqual(tool.pad_problems("assembled", counts), ["1 px of another alpha with the pad than without it (another outline)"])
        self.assertEqual(tool.PAD_SHARE_MIN, 0.05)
        with self.assertRaises(tool.ShotError):
            tool.pad_differences(look, look, other[:-4])
        # Served: the look with its pad for the one part (the pictures'), or without it (the fourth comparison's).
        index = _json(LIBRARY / library_write.SCENES_INDEX)
        given = library_write.part_look(index, self.parts, "umi-finray")
        self.assertEqual(given["pad"], index["rules"]["part_pad"])
        served = json.loads(tool.served_scenes(index, "umi-finray", given))["rules"]
        self.assertEqual((served["part_looks"], served["part_pad"]), ({"umi-finray": given["look"]}, given["pad"]))
        self.assertEqual(library_write.part_look(json.loads(tool.served_scenes(index, "umi-finray", given)), self.parts, "umi-finray"), given)
        self.assertEqual(tool.unpadded(given), {"look": given["look"], "smooth_deg": None})
        self.assertNotIn("part_pad", json.loads(tool.served_scenes(index, "umi-finray", tool.unpadded(given)))["rules"])
        self.assertNotIn("part_pad", json.loads(tool.served_scenes(index, "umi-finray", None))["rules"])

    def test_a_picture_is_a_webp_with_alpha_of_its_size(self) -> None:
        info = library_write.webp_info
        # The fixture as the tool's encoder writes it: the extended layout (VP8X), its canvas and its alpha flag.
        self.assertEqual((SHOT[12:16], info(SHOT), info(SHOT_CARD)), (b"VP8X", (1280, 800, True), (640, 400, True)))

        def riff(chunk: bytes, body: bytes) -> bytes:
            body += b"\0" * max(0, 10 - len(body))
            return b"RIFF" + struct.pack("<I", 12 + len(body)) + b"WEBP" + chunk + struct.pack("<I", len(body)) + body

        def lossless(width: int, height: int, alpha: int) -> bytes:
            return riff(b"VP8L", bytes([0x2F]) + ((width - 1) | (height - 1) << 14 | alpha << 28).to_bytes(4, "little"))

        # The extended layout without its alpha flag (a picture on an opaque background), and the lossless one.
        self.assertEqual(info(riff(b"VP8X", bytes(4) + (1279).to_bytes(3, "little") + (799).to_bytes(3, "little"))), (1280, 800, False))
        self.assertEqual(info(lossless(640, 400, 1)), (640, 400, True))
        self.assertEqual(info(lossless(640, 400, 0)), (640, 400, False))
        self.assertEqual(info(riff(b"VP8 ", b"\x30\x01\x00\x9d\x01\x2a" + (1280).to_bytes(2, "little") + (800).to_bytes(2, "little"))),
                         (1280, 800, False), "the simple lossy layout has no alpha")
        for name, data in (("cut short", SHOT[:-1]), ("the header alone", SHOT[:24]), ("a PNG", b"\x89PNG\r\n\x1a\n" + bytes(40)),
                           ("an unknown chunk", riff(b"VP9X", bytes(10)))):
            with self.subTest(data=name):
                self.assertIsNone(info(data))

    @PICTURES_ONLY
    def test_the_writer_writes_each_image_from_the_manifest(self) -> None:
        identifier = "widowx-250-2mm"
        variant = self.entries["variants"][identifier]
        with tempfile.TemporaryDirectory() as folder:
            # A copy of web/library/'s meshes (the UMI finger's beside it, as ../vendor/umi/), its shots/ the fixture.
            library = Path(folder) / "library"
            shutil.copytree(LIBRARY / "meshes", library / "meshes")
            shutil.copytree(WEB / "vendor" / "umi", Path(folder) / "vendor" / "umi")
            _shot_library(library, self.entries["variants"])
            document = library_write.entries(self.parts, self.fits, library)
            self.assertEqual(document["variants"][identifier]["image"], IMAGE_OF_WIDOWX)
            self.assertEqual([key for key, item in document["variants"].items() if item["image"]], [identifier], "null without a shot")
            self.assertEqual(library_write.pictures(document["variants"], library),
                             ({key: item["image"] for key, item in document["variants"].items()}, [], [], {key: None for key in document["variants"]}))
            self.assertEqual([key for key, item in document["variants"].items() if item["view"]], [], "no 3D view without its art")
            # The manifest as the tool writes it: each file's path, bytes, SHA-256 and size; the fit and build id shot.
            manifest = _json(library / library_write.SHOTS_MANIFEST)
            shot = manifest["shots"][identifier]
            self.assertEqual((manifest["format"], sorted(manifest["shots"])), ("flexitac-library-shots/v1", [identifier]))
            self.assertEqual((shot["fit_sha256"], shot["build_id"], shot["figure_sha256"]),
                             (variant["fit_sha256"], variant["build_id"], library_write.figure_sha256()))
            self.assertEqual(shot["files"], {
                "exploded": {"path": f"shots/{identifier}.exploded.webp", "bytes": len(SHOT), "sha256": hashlib.sha256(SHOT).hexdigest(), "width": 1280, "height": 800},
                "assembled": {"path": f"shots/{identifier}.assembled.webp", "bytes": len(SHOT), "sha256": hashlib.sha256(SHOT).hexdigest(), "width": 1280, "height": 800},
                "card": {"path": f"shots/{identifier}.exploded.card.webp", "bytes": len(SHOT_CARD), "sha256": hashlib.sha256(SHOT_CARD).hexdigest(), "width": 640, "height": 400}})
        # The tool's pane at its pixel ratio is the pictures' size; the writer's names are the contract's.
        self.assertEqual(tuple(side * SHOTS_TOOL.DPR for side in SHOTS_TOOL.PANE_CSS), library_write.SHOT_SIZE)
        self.assertEqual((library_write.SHOT_SIZE, library_write.CARD_SIZE), ((1280, 800), (640, 400)))
        self.assertEqual(library_write.image_record(identifier, variant["label"]), IMAGE_OF_WIDOWX)

    @PICTURES_ONLY
    def test_a_picture_of_another_fit_is_refused(self) -> None:
        # The wrong sensor pictured: a shot of another fit, or of another build, has no image and is a problem.
        for key in ("fit_sha256", "build_id"):
            with self.subTest(changed=key), tempfile.TemporaryDirectory() as folder:
                library = _shot_library(Path(folder), self.entries["variants"], **{key: "another"})
                images, problems, older, _ = library_write.pictures(self.entries["variants"], library)
                self.assertEqual((images["widowx-250-2mm"], older), (None, []))
                self.assertEqual(problems, [("widowx-250-2mm", "widowx-250-2mm: its pictures are of another fit (the wrong sensor pictured): "
                                                               "re-shoot with tools/browser/library_shots.py --only widowx-250-2mm")])

    @PICTURES_ONLY
    def test_a_picture_of_older_figure_sources_is_a_warning_only(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            library = _shot_library(Path(folder), self.entries["variants"], identifiers=("widowx-250-2mm", "i2rt-yam-1mm"), figure_sha256="0" * 64)
            images, problems, older, _ = library_write.pictures(self.entries["variants"], library)
            self.assertEqual((images["widowx-250-2mm"], problems, older), (IMAGE_OF_WIDOWX, [], ["i2rt-yam-1mm", "widowx-250-2mm"]))
            self.assertEqual(library_write.older_note(older), "the pictures of i2rt-yam-1mm, widowx-250-2mm are of older figure sources "
                             "(web/cad/onpart.js and the modules it imports, or the Library view's own: web/cad/library_view.js, "
                             "web/cad/library_stage.js, web/cad/stl.js): re-shoot with tools/browser/library_shots.py")
        # The hash follows each of the sources.
        sources = library_write.figure_sources()
        for path in sources:
            with self.subTest(changed=path):
                self.assertNotEqual(library_write.figure_sha256(dict(sources, **{path: sources[path] + b"\n"})), library_write.figure_sha256(sources))

    def test_the_figure_sources_are_onpart_and_the_modules_it_imports(self) -> None:
        sources = library_write.figure_sources()
        self.assertLessEqual({"cad/onpart.js", "cad/drape.js", "cad/studio.js"}, set(sources))
        self.assertTrue(set(sources).isdisjoint({"cad/main.js", "app.js"}), "the page's controller and the boards' art are not the figure's")
        for path, data in sources.items():
            with self.subTest(source=path):
                imported = re.findall(r'^import [^;]*?from "\./([\w.-]+\.js)";', data.decode("utf-8"), re.MULTILINE | re.DOTALL)
                self.assertLessEqual({f"cad/{name}" for name in imported}, set(sources))
        self.assertEqual(library_write.figure_sources(lambda path: (WEB / path).read_bytes()), sources)

    @PICTURES_ONLY
    def test_a_broken_picture_is_refused(self) -> None:
        identifier = "widowx-250-2mm"
        exploded = library_write.shot_files(identifier)["exploded"][0]

        def check(library: Path, problem) -> None:
            images, problems, _, _ = library_write.pictures(self.entries["variants"], library)
            self.assertIn(problem, problems)
            if problem[0]:
                self.assertIsNone(images[problem[0]])

        cases = {
            "a file changed": (lambda library: (library / exploded).write_bytes(SHOT_CARD),
                               (identifier, f"{identifier}: {exploded} is not the file shots/manifest.json names")),
            "a file missing": (lambda library: (library / exploded).unlink(), (identifier, f"{identifier}: {exploded} is missing")),
            "a stray file": (lambda library: (library / "shots" / "notes.txt").write_text("x", encoding="utf-8"),
                             (None, "shots/notes.txt: not a picture of shots/manifest.json")),
            "no manifest": (lambda library: (library / library_write.SHOTS_MANIFEST).unlink(),
                            (None, "shots/ holds files but no manifest.json: re-shoot with tools/browser/library_shots.py")),
        }
        for name, (breaking, problem) in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as folder:
                library = _shot_library(Path(folder), self.entries["variants"])
                breaking(library)
                check(library, problem)
        with tempfile.TemporaryDirectory() as folder:
            # The card's picture where the Exploded one goes, the manifest naming it as it is: not its size.
            library = _shot_library(Path(folder), self.entries["variants"], files={"exploded": SHOT_CARD})
            check(library, (identifier, f"{identifier}: {exploded} is not a 1280 x 800 WebP with alpha"))
        with tempfile.TemporaryDirectory() as folder:
            variants = dict(self.entries["variants"], **{"nothing-1mm": self.entries["variants"][identifier]})
            library = _shot_library(Path(folder), variants, identifiers=(identifier, "nothing-1mm"))
            check(library, (None, "nothing-1mm: a picture of no sensor of entries.json: re-shoot with tools/browser/library_shots.py"))


class SceneTests(LibraryTestCase):
    """The grippers' scenes of the 3D view (scenes/, bodies/; the user's requests of 2026-11-05, docs/LIBRARY_VIEW.md):
    the committed ones current and as the user approved them, and library_write.scenes() on tiny scenes built here."""

    def test_the_committed_scenes_are_current(self) -> None:
        index, problems = library_write.scenes(self.parts)
        self.assertEqual(problems, [], f"the scenes are stale: {REBUILD}")
        self.assertEqual(index, _json(LIBRARY / library_write.SCENES_INDEX))

    def test_every_gripper_is_drawn_whole_as_the_user_approved(self) -> None:
        # The prototype the user approved on 2026-11-05: the seven grippers whole (Franka's whole hand), each with its
        # scene, the UMI finger and its tapered tips none (their fingertip scene); both fingers, the jaws fully open, the
        # other finger turned (the same part: the same board) or mirrored (the mirror-image board); the MakerMods tips on
        # the project's own plain rail, never its body's file.  The user's decision of 2026-11-06: the near finger (the mate)
        # see-through on every gripper, in both views, its stack assembled, the sensor finger's alone exploded.
        index = _json(LIBRARY / library_write.SCENES_INDEX)
        grippers = library_write.gripper_parts(self.parts)
        self.assertEqual(grippers, ["franka-hand", "widowx-250", "trossen-widowx-ai", "arx-x5", "i2rt-yam", "unitree-dex1", "makermods-metal"])
        self.assertEqual(index["scenes"], {part: f"scenes/{part}.json" for part in grippers})
        self.assertEqual(index["rules"], APPROVED_RULES)
        for part_id in grippers:
            scene = _json(LIBRARY / index["scenes"][part_id])
            with self.subTest(part=part_id):
                self.assertEqual((scene["part"], scene["format"], scene["frame"]), (part_id, "flexitac-library-scene/v1", "the part's file axes, mm"))
                self.assertEqual(scene["see_through"], SEE_THROUGH[part_id])
                self.assertEqual(scene["mate"]["kind"], MATE_KINDS[part_id])
                self.assertEqual(scene["opening"]["q_mm"], scene["opening"]["limit_mm"], "the jaws fully open")
                self.assertEqual(scene["picture"], PICTURES.get(part_id, PICTURE))
                meshes = [body["mesh"] for body in scene["bodies"]]
                if part_id == "makermods-metal":
                    # Since the looks of 2026-11-12: the rail, then the shapes the project drew round it
                    # (bodies/makermods-metal/drawn-*.stl: since 2026-11-14 the gripper's body by eye), all its own drawing.
                    self.assertEqual(meshes[0], RAIL, "the project's own rail, no MakerMods body")
                    for mesh in meshes[1:]:
                        self.assertRegex(mesh, r"^bodies/makermods-metal/drawn-[a-z0-9-]+\.stl$")
                        self.assertTrue(library_write.own_body(mesh, (LIBRARY / mesh).read_bytes()), mesh)
                    self.assertIn("not MakerMods hardware", scene["about"])
                    rail_meshes = meshes
                else:
                    self.assertNotIn(RAIL, meshes)
                self.assertNotIn("camera", scene, "the approved homes (Exploded 65, Assembled 57 degrees)")
                self.assertNotIn("explode", scene, "the approved explode (the rules' gap share)")
        self.assertEqual(sorted(path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "bodies" / "makermods-metal").iterdir()),
                         sorted(rail_meshes), "the folder holds the scene's meshes and nothing else")

    def test_the_makermods_body_is_the_project_s_drawing_by_eye(self) -> None:
        # The user's decision of 2026-11-14 ("makermods, yes, you can do it by eye"): the Metal Arm's body drawn round the
        # project's own rail after the maker's photos, no MakerMods file: the beam no longer than the open jaws need (their
        # bases at full opening and a few mm for the end stops), every shape the project drew credited in NOTICE.md as its
        # own drawing by eye, the scene's about saying it is not MakerMods' 3D model or hardware.
        def points(data: bytes, scale: float = 1.0) -> list:
            count = struct.unpack_from("<I", data, 80)[0]
            out = []
            for k in range(count):
                record = struct.unpack_from("<12f", data, 84 + 50 * k)
                out += [[record[3 * j + 3 + a] * scale for a in range(3)] for j in range(3)]
            return out

        scene = _json(LIBRARY / "scenes" / "makermods-metal.json")
        part = self.parts["parts"]["makermods-metal"]
        self.assertEqual(_json(LIBRARY / "fits" / "makermods-metal-2mm.json")["reply"]["mesh"]["unit"], "m", "the tip's file in metres")
        tip = points((LIBRARY / part["mesh"]["file"]).read_bytes(), 1000.0)
        mate = scene["mate"]["matrix"]
        turned = [[math.fsum(mate[r][c] * p[c] for c in range(3)) + mate[r][3] for r in range(3)] for p in tip]
        jaws = (min(p[0] for p in tip + turned), max(p[0] for p in tip + turned))
        rail = points((LIBRARY / RAIL).read_bytes())
        beam = (min(p[0] for p in rail), max(p[0] for p in rail))
        self.assertTrue(beam[0] <= jaws[0] and jaws[1] <= beam[1], f"the jaws {jaws} on the beam {beam} at full opening")
        self.assertLessEqual(max(jaws[0] - beam[0], beam[1] - jaws[1]), 4.0, f"the beam {beam} no longer than the open jaws {jaws} need")
        text = (LIBRARY / "NOTICE.md").read_text(encoding="utf-8")
        drawn = sorted(path.name for path in (LIBRARY / "bodies" / "makermods-metal").iterdir() if path.name != "rail.stl")
        self.assertGreaterEqual(len(drawn), 5, "the beam's shapes, the housing and the camera's mount")
        for name in drawn:
            with self.subTest(drawn=name):
                self.assertRegex(name, r"^drawn-[a-z0-9-]+\.stl$")
                self.assertIn(f"`bodies/makermods-metal/{name}`", text, "credited as the project's own drawing")
                extent = points((LIBRARY / "bodies" / "makermods-metal" / name).read_bytes())
                self.assertTrue(all(beam[0] - 4.5 <= p[0] <= beam[1] + 4.5 for p in extent), f"{name} within the beam and its end stops")
        self.assertIn("no MakerMods model was used, traced or measured", text)
        self.assertIn("not MakerMods' 3D model, geometry or hardware", text)
        about = scene["about"]
        self.assertIn("No MakerMods file is used", about)
        self.assertIn("by eye", about)
        self.assertIn("not MakerMods' 3D model or hardware", about)

    def test_one_stack_explodes_and_the_near_finger_is_see_through_in_both_views(self) -> None:
        # The user's decision of 2026-11-06 ("每一个夹爪只用爆炸一个sensor, 靠近外面的finger透明, 夹爪不爆炸; 靠近里面的finger
        # 不透明, 夹爪爆炸"): the committed rules explode the sensor finger's stack alone and ghost the scenes' see-through
        # fingers in both modes; every scene lists the near finger, the mate; one gap share for all (no override).
        rules = _json(LIBRARY / library_write.SCENES_INDEX)["rules"]
        self.assertEqual(rules["explode_stacks"], ["sensor"])
        self.assertEqual(sorted(rules["see_through_modes"]), list(library_write.CAMERA_MODES))
        self.assertEqual(rules["gap_share"], 0.42)
        for part_id in library_write.gripper_parts(self.parts):
            with self.subTest(part=part_id):
                scene = _json(LIBRARY / "scenes" / f"{part_id}.json")
                self.assertEqual(scene["see_through"], ["mate"])
                self.assertNotIn("explode", scene)
        # The stage reads both rules with no default (it draws no gripper without them) and ghosts in their modes; the
        # shots tool records and checks the writer's numbers.
        stage = (ROOT / "web" / "cad" / "library_stage.js").read_text(encoding="utf-8")
        for text in ("new Set(rules.explode_stacks)", "!Array.isArray(rules.see_through_modes)", "throw new Error(`library stage: explode_stacks",
                     "state.info.seeModes.has(mode)", "state.info.seeModes.has(view.mode)", "near_seen: info.explodeMate ? null",
                     "stacks_apart_px: measures.screen.stacks_apart_px"):
            self.assertIn(text, stage)
        self.assertEqual(SHOTS_TOOL.STAGE_NUMBERS, library_write.STAGE_NUMBERS)
        checks = rules["checks"]
        # One copy of the rules (the review of 2026-11-06: the shots tool's own copy had taken a jaw gap of 0 or below and
        # an extra number, which the writer then refused): the shots tool refuses what the writer refuses, in its words.
        cases = [(NUMBERS, ["sensor"], []),
                 (dict(NUMBERS, near_seen=0.4), ["sensor"], ["near_seen 0.4 breaks the rule near_seen_min: not >= 0.5"]),
                 (dict(NUMBERS, stacks_apart_px=19), ["sensor"], ["stacks_apart_px 19 breaks the rule stacks_apart_min_px: not >= 20"]),
                 (dict(NUMBERS, jaw_gap_mm=10, clearance_mm={"bodies": 12, "other_finger": 12, "stacks": 2.9}), ["sensor"],
                  ["clearance_mm.stacks 2.9 breaks the rule stacks_apart_min_mm: not >= 3"]),
                 (NUMBERS, ["sensor", "mate"], ["near_seen is 1.0, with the mate's stack exploding"]),
                 (dict(NUMBERS, near_seen=None), ["sensor", "mate"], []),
                 (dict(NUMBERS, jaw_gap_mm=0), ["sensor"], ["jaw_gap_mm (0) is not a positive number"]),
                 (dict(NUMBERS, jaw_gap_mm=-5.0), ["sensor"], ["jaw_gap_mm (-5.0) is not a positive number"]),
                 (dict(NUMBERS, extra=1), ["sensor"], [f"its stage's numbers are not {', '.join(library_write.STAGE_NUMBERS)}"])]
        for numbers, explode, problems in cases:
            with self.subTest(numbers=numbers, explode=explode):
                self.assertEqual(SHOTS_TOOL.rule_breaches(numbers, checks, ["mate"], explode), problems)
                self.assertEqual(library_write.stage_problems(numbers, checks, ["mate"], explode), problems)

    def test_the_bodies_and_the_art_stay_within_their_budgets(self) -> None:
        for folder, budget in (("bodies", BODIES_BUDGET_BYTES), ("art", ART_BUDGET_BYTES)):
            with self.subTest(folder=folder):
                size = sum(path.stat().st_size for path in (LIBRARY / folder).rglob("*") if path.is_file()) if (LIBRARY / folder).is_dir() else 0
                self.assertLessEqual(size, budget, f"web/library/{folder}/ is {size} bytes")

    def test_tiny_scenes_have_no_problem(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            library = _scene_library(Path(folder), self.parts)
            index, problems = library_write.scenes(self.parts, library)
            self.assertEqual(problems, [])
            self.assertEqual(sorted(index["scenes"]), sorted(library_write.gripper_parts(self.parts)))
            # The project's own rail has no NOTICE row; every other body has one.
            self.assertNotIn(RAIL, (library / "NOTICE.md").read_text(encoding="utf-8"))

    def problems(self, edit, part_id=None) -> list:
        """scenes()' problems of the tiny scenes with ``edit`` applied (the library -> None, or, with ``part_id``, that
        part's scene document -> None)."""

        with tempfile.TemporaryDirectory() as folder:
            library = _scene_library(Path(folder), self.parts)
            if part_id:
                _edit_scene(library, part_id, edit)
            else:
                edit(library)
            return library_write.scenes(self.parts, library)[1]

    def test_the_mate_s_kind_is_its_determinant_s_sign(self) -> None:
        # A mirror pair's other finger is the mirror image (a matrix of determinant -1: the mirror-image board), a turned
        # one the same part turned (+1: the same board); the kind the page says is the matrix's.
        name = "scenes/trossen-widowx-ai.json"
        self.assertEqual(self.problems(lambda scene: scene["mate"].update(kind="turned"), "trossen-widowx-ai"),
                         [("trossen-widowx-ai", f"{name}: its mate is 'turned', but its matrix's determinant is -1: {REBUILD}")])
        self.assertEqual(self.problems(lambda scene: scene["mate"].update(kind="mirror"), "widowx-250"),
                         [("widowx-250", f"scenes/widowx-250.json: its mate is 'mirror', but its matrix's determinant is +1: {REBUILD}")])
        self.assertEqual((library_write.determinant(TURNED), library_write.determinant(MIRROR), library_write.determinant(IDENTITY)), (1, -1, 1))

    def test_every_matrix_is_rigid(self) -> None:
        cases = {
            "not orthonormal": ([[2, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "is not orthonormal (its upper 3 x 3)"),
            "sheared": ([[1, 0.01, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "is not orthonormal (its upper 3 x 3)"),
            "a last row": ([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 1, 1]], "has a last row other than 0, 0, 0, 1"),
            "three rows": (IDENTITY[:3], "is not a 4 x 4 array of numbers"),
            "a string": ([[1, 0, 0, "0"], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "is not a 4 x 4 array of numbers"),
        }
        for case, (matrix, problem) in cases.items():
            with self.subTest(case=case):
                self.assertEqual(self.problems(lambda scene: scene["mate"].update(matrix=matrix), "franka-hand"),
                                 [("franka-hand", f"scenes/franka-hand.json: its mate's matrix {problem}: {REBUILD}")])
                self.assertEqual(self.problems(lambda scene: scene["bodies"][0].update(matrix=matrix), "franka-hand"),
                                 [("franka-hand", f"scenes/franka-hand.json: body 1's matrix {problem}: {REBUILD}")])
        # Within 1e-6: a rotation's floats as a scene builder writes them.
        turn = math.radians(30)
        rotation = [[round(math.cos(turn), 9), -round(math.sin(turn), 9), 0, 1.5], [round(math.sin(turn), 9), round(math.cos(turn), 9), 0, 0],
                    [0, 0, 1, 0], [0, 0, 0, 1]]
        self.assertIsNone(library_write._rigid(rotation))
        self.assertEqual(self.problems(lambda scene: scene["bodies"][0].update(matrix=rotation), "franka-hand"), [])

    def test_the_part_its_mesh_and_the_frame_are_pinned(self) -> None:
        name = "scenes/arx-x5.json"
        cases = (
            (lambda scene: scene.update(part_mesh_sha256="0" * 64), f"{name} is drawn about another mesh of arx-x5 than parts.json's (part_mesh_sha256)"),
            (lambda scene: scene.update(part="i2rt-yam"), f"{name} is the scene of 'i2rt-yam'"),
            (lambda scene: scene.update(format="flexitac-library-scene/v0"), f"{name}: the format is 'flexitac-library-scene/v0', not flexitac-library-scene/v1"),
            (lambda scene: scene.update(frame="metres"), f"{name}: its frame is not \"the part's file axes, mm\""),
            (lambda scene: scene.update(approach=[0, 0, 1.000001]), f"{name}: its approach [0, 0, 1.000001] is not a unit vector"),
            (lambda scene: scene.update(opening={"q_mm": 41, "limit_mm": 40}), f"{name}: its opening is not {{q_mm, limit_mm, joint, source}} with 0 < q_mm <= limit_mm"),
            (lambda scene: scene.update(picture=" "), f"{name}: its picture (the alt text's words) is empty"),
            (lambda scene: scene.update(see_through=["sensor", "other"]), f"{name}: its see_through ['sensor', 'other'] is not a subset of ['sensor', 'mate']"),
            (lambda scene: scene.update(cad=True), f"{name} has not the keys {', '.join(library_write.SCENE_KEYS)} (and any of camera, explode, looks, part_look, smooth_deg)"),
            (lambda scene: scene["mate"].update(part="yes"), f"{name}: its mate's part is not true or false"),
            (lambda scene: scene["mate"].update(part=False), f"{name}: its mate draws no part and no body is the mate's finger"),
            (lambda scene: scene["bodies"][0].update(finger="left"), f"{name}: body 1's finger 'left' is not sensor, mate or null"),
        )
        for edit, problem in cases:
            with self.subTest(problem=problem):
                self.assertEqual(self.problems(edit, "arx-x5"), [("arx-x5", f"{problem}: {REBUILD}")])
        # The mate drawn by a body of the mate's finger (the I2RT YAM's other tip is another part).
        self.assertEqual(self.problems(lambda scene: (scene["mate"].update(part=False), scene["bodies"][0].update(finger="mate")), "arx-x5"), [])

    def test_each_body_is_its_file_tabled_and_open(self) -> None:
        name, mesh = "scenes/widowx-250.json", "bodies/widowx-250/body.stl"
        for key, value in (("sha256", "0" * 64), ("bytes", 1), ("triangles", 2)):
            with self.subTest(changed=key):
                self.assertEqual(self.problems(lambda scene: scene["bodies"][0].update({key: value}), "widowx-250"), [("widowx-250",
                                 f"{name}: body 1: {mesh} is not the file its scene names (its SHA-256, bytes or triangles; a binary STL): {REBUILD}")])
        self.assertEqual(self.problems(lambda library: (library / mesh).unlink()),
                         [("widowx-250", f"{name}: body 1: {mesh} is missing: {REBUILD}")])
        self.assertEqual(self.problems(lambda scene: scene["bodies"][0].update(mesh="bodies/arx-x5/body.stl"), "widowx-250"),
                         [("widowx-250", f"{name}: body 1's mesh 'bodies/arx-x5/body.stl' is not a file of bodies/widowx-250/: {REBUILD}"),
                          (None, f"{mesh}: a file of no scene: {REBUILD}")])

        def untabled(library: Path) -> None:
            notice = library / "NOTICE.md"
            notice.write_text("".join(line for line in notice.read_text(encoding="utf-8").splitlines(True) if mesh not in line), encoding="utf-8")

        self.assertEqual(self.problems(untabled), [("widowx-250", f"{name}: body 1: {mesh} has no row of NOTICE.md with its SHA-256: {REBUILD}")])

        def closed(library: Path) -> None:
            notice = library / "NOTICE.md"
            notice.write_text(notice.read_text(encoding="utf-8").replace(f"`{mesh}` | tiny `0123456`, body.stl | MIT,", f"`{mesh}` | tiny `0123456`, body.stl | All rights reserved,"), encoding="utf-8")

        self.assertEqual(self.problems(closed), [("widowx-250", f"{name}: body 1: {mesh}'s NOTICE row names no open licence (Apache-2.0, MIT, BSD-3-Clause) with its text: {REBUILD}")])
        # Its licence's text gone: every tabled body's row refused (the rail, the project's own, has none).
        self.assertEqual(self.problems(lambda library: (library / "licenses" / "tiny.txt").unlink()),
                         [(part, f"scenes/{part}.json: body 1: bodies/{part}/body.stl's NOTICE row names no open licence (Apache-2.0, MIT, BSD-3-Clause) "
                                 f"with its text: {REBUILD}") for part in sorted(library_write.gripper_parts(self.parts)) if part != "makermods-metal"])
        # A file of no scene, in scenes/ or bodies/.
        self.assertEqual(self.problems(lambda library: ((library / "bodies" / "widowx-250" / "old.stl").write_bytes(_stl()),
                                                        (library / "scenes" / "old.json").write_text("{}", encoding="utf-8"))),
                         [(None, f"scenes/old.json: a file of no scene: {REBUILD}"), (None, f"bodies/widowx-250/old.stl: a file of no scene: {REBUILD}")])

    def test_the_overrides_are_bounded_and_explained(self) -> None:
        name = "scenes/i2rt-yam.json"
        explained = lambda scene, **changes: scene.update(about=scene["about"] + " The reason: its tips sit low.", **changes)  # noqa: E731
        self.assertEqual(self.problems(lambda scene: explained(scene, camera={"exploded": {"tilt_deg": 60}}, explode={"gap_share": 0.3}), "i2rt-yam"), [])
        cases = (
            (lambda scene: explained(scene, camera={"exploded": {"tilt_deg": 75}}),
             f"{name}: its camera override {{'exploded': {{'tilt_deg': 75}}}} is not {{exploded or assembled: elevation_deg, front, tilt_deg}} "
             "within tilt_deg 45 to 70, elevation_deg 15 to 45, front 1 or -1"),
            (lambda scene: explained(scene, camera={"assembled": {"elevation_deg": 10}}),
             f"{name}: its camera override {{'assembled': {{'elevation_deg': 10}}}} is not {{exploded or assembled: elevation_deg, front, tilt_deg}} "
             "within tilt_deg 45 to 70, elevation_deg 15 to 45, front 1 or -1"),
            (lambda scene: explained(scene, camera={"exploded": {"front": 0}}),
             f"{name}: its camera override {{'exploded': {{'front': 0}}}} is not {{exploded or assembled: elevation_deg, front, tilt_deg}} "
             "within tilt_deg 45 to 70, elevation_deg 15 to 45, front 1 or -1"),
            (lambda scene: explained(scene, explode={"gap_share": 0.5}), f"{name}: its explode override {{'gap_share': 0.5}} is not {{gap_share}} within 0.25 to 0.45"),
            (lambda scene: scene.update(explode={"gap_share": 0.3}), f"{name}: its override (explode) has no reason in its about"),
        )
        for edit, problem in cases:
            with self.subTest(problem=problem):
                self.assertEqual(self.problems(edit, "i2rt-yam"), [("i2rt-yam", f"{problem}: {REBUILD}")])

    def test_every_gripper_and_only_the_grippers_have_a_scene(self) -> None:
        def unmapped(library: Path) -> None:
            index = _json(library / library_write.SCENES_INDEX)
            del index["scenes"]["unitree-dex1"]
            _write_json(library / library_write.SCENES_INDEX, index)
            (library / "scenes" / "unitree-dex1.json").unlink()
            shutil.rmtree(library / "bodies" / "unitree-dex1")

        self.assertEqual(self.problems(unmapped), [("unitree-dex1", f"unitree-dex1: no scene in scenes/scenes.json (every gripper is drawn whole): {REBUILD}")])
        for part_id, kept in (("umi-finray", True), ("umi-trap-tip13.8", True), ("robot-x", False)):
            with self.subTest(part=part_id):
                def mapped(library: Path) -> None:
                    index = _json(library / library_write.SCENES_INDEX)
                    index["scenes"][part_id] = f"scenes/{part_id}.json"
                    _write_json(library / library_write.SCENES_INDEX, index)

                self.assertEqual(self.problems(mapped), [(part_id if kept else None, f"{part_id}: a scene for "
                                                          f"{'a part that keeps the fingertip scene' if kept else 'no part of parts.json'}: {REBUILD}")])
        self.assertEqual(library_write.gripper_parts(self.parts), [part for part in self.parts["order"] if part != "umi-finray" and not part.startswith("umi-")])

    def test_the_index_is_the_frozen_one(self) -> None:
        def index_edit(edit):
            def change(library: Path) -> None:
                index = _json(library / library_write.SCENES_INDEX)
                edit(index)
                _write_json(library / library_write.SCENES_INDEX, index)
            return change

        cases = (
            (lambda index: index.update(format="x"), "scenes/scenes.json: the format is 'x', not flexitac-library-scenes/v1"),
            (lambda index: index["rules"].pop("ghost_opacity"), "scenes/scenes.json: its rules have not the keys camera, checks, depth_tol_mm, explode_stacks, "
             "gap_share, ghost_opacity, measure_px, min_step_mm, see_through_modes (and any of looks, part_looks, part_smooth_deg, part_pad)"),
            (lambda index: index["rules"].pop("explode_stacks"), "scenes/scenes.json: its rules have not the keys camera, checks, depth_tol_mm, explode_stacks, "
             "gap_share, ghost_opacity, measure_px, min_step_mm, see_through_modes (and any of looks, part_looks, part_smooth_deg, part_pad)"),
            (lambda index: index["rules"].update(gap_share=-1), "scenes/scenes.json: its rule gap_share (-1) is not a positive number"),
            (lambda index: index["rules"]["camera"]["exploded"].update(tilt_deg=80), "scenes/scenes.json: its rules' camera is not {exploded, assembled} each of elevation_deg, front, tilt_deg within their bounds"),
            (lambda index: index["rules"]["checks"].pop("card_min_px"), "scenes/scenes.json: its rules' checks are not card_min_px, clearance_min_mm, ghost_cover_min, "
             "layer_visible_min, near_seen_min, opaque_cover_max, stacks_apart_min_g, stacks_apart_min_mm, stacks_apart_min_px of numbers"),
            (lambda index: index["rules"]["checks"].pop("near_seen_min"), "scenes/scenes.json: its rules' checks are not card_min_px, clearance_min_mm, ghost_cover_min, "
             "layer_visible_min, near_seen_min, opaque_cover_max, stacks_apart_min_g, stacks_apart_min_mm, stacks_apart_min_px of numbers"),
            (lambda index: index.update(notes="x"), "scenes/scenes.json has not the keys about, format, rules, scenes"),
        )
        for edit, problem in cases:
            with self.subTest(problem=problem):
                self.assertEqual(self.problems(index_edit(edit))[0], (None, f"{problem}: {REBUILD}"))
        self.assertEqual(self.problems(lambda library: (library / library_write.SCENES_INDEX).unlink())[0],
                         (None, f"scenes/scenes.json is missing: {REBUILD}"))
        # The stacks that explode and the see-through's modes (the user's decision of 2026-11-06): the sensor finger's
        # among them, distinct, of the two fingers; the modes distinct, of the two, at least one.
        stacks = ("scenes/scenes.json: its rule explode_stacks ({!r}) is not the fingers whose stacks explode (distinct, of sensor, mate, "
                  "the sensor's among them)")
        modes = ("scenes/scenes.json: its rule see_through_modes ({!r}) is not the modes the see-through fingers are ghosted in "
                 "(distinct, of assembled, exploded, at least one)")
        for value in (["mate"], ["sensor", "sensor"], ["sensor", "other"], [], "sensor"):
            with self.subTest(explode_stacks=value):
                self.assertEqual(self.problems(index_edit(lambda index: index["rules"].update(explode_stacks=value))),
                                 [(None, f"{stacks.format(value)}: {REBUILD}")])
        for value in (["other"], [], ["exploded", "exploded"], "exploded"):
            with self.subTest(see_through_modes=value):
                self.assertEqual(self.problems(index_edit(lambda index: index["rules"].update(see_through_modes=value))),
                                 [(None, f"{modes.format(value)}: {REBUILD}")])
        # Both stacks exploding (as before the decision) and the see-through in Exploded only are still the formats'.
        self.assertEqual(self.problems(index_edit(lambda index: index["rules"].update(explode_stacks=["sensor", "mate"], see_through_modes=["exploded"]))), [])

    def test_no_denied_model_and_none_of_the_importer_s_inputs(self) -> None:
        name, mesh = "scenes/arx-x5.json", "bodies/arx-x5/body.stl"
        with tempfile.TemporaryDirectory() as folder:
            library = _scene_library(Path(folder), self.parts)
            digest = hashlib.sha256((library / mesh).read_bytes()).hexdigest()
            # A body that is a denied vendor model (by its SHA-256): refused, and the NOTICE row naming it too.
            with mock.patch.dict(library_write.DENIED_SHA256, {digest: "a vendor body (x.stl): not cleared"}):
                problems = library_write.scenes(self.parts, library)[1]
            self.assertEqual(problems, [("arx-x5", f"{name}: body 1: {mesh} is a vendor model of the deny-list (a vendor body (x.stl): not cleared): never in the Library: {REBUILD}"),
                                        (None, f"NOTICE.md names a vendor body (x.stl): not cleared ({digest[:12]}), a vendor model of the deny-list: never in the Library")])
        # A NOTICE row naming the MakerMods body it was made from (its upstream file, in the Change column).
        denied = "19ab43c406f349d62dc7a9932b66fb28053cf96152ab00d71a93945a43ddd8cd"
        self.assertEqual(self.problems(lambda library: (library / "NOTICE.md").write_text((library / "NOTICE.md").read_text(encoding="utf-8").replace(
            f"`{mesh}` | tiny `0123456`, body.stl | MIT, Tiny, `licenses/tiny.txt` | unchanged",
            f"`{mesh}` | tiny `0123456`, body.stl | MIT, Tiny, `licenses/tiny.txt` | modified: decimated from `{denied}`"), encoding="utf-8")),
            [(None, f"NOTICE.md names MakerMods Metal Arm (gripper_base.STL): not cleared ({denied[:12]}), a vendor model of the deny-list: never in the Library")])
        # A body named as a denied maker's.
        def named(library: Path) -> None:
            (library / mesh).rename(library / "bodies" / "arx-x5" / "xarm_body.stl")
            _edit_scene(library, "arx-x5", lambda scene: scene["bodies"][0].update(mesh="bodies/arx-x5/xarm_body.stl"))
            (library / "NOTICE.md").write_text((library / "NOTICE.md").read_text(encoding="utf-8").replace(mesh, "bodies/arx-x5/xarm_body.stl"), encoding="utf-8")

        self.assertEqual(self.problems(named), [("arx-x5", f"{name}: body 1: bodies/arx-x5/xarm_body.stl is a vendor model of the deny-list "
                                                           f"(bodies/arx-x5/xarm_body.stl): never in the Library: {REBUILD}")])
        # The private importer's inputs: its asset folders, the recipes, a recipe's key, an absolute path.
        for text, found in (("from asset/arx.stl", "asset/"), ("see outputs/gripper_sensors", "outputs/"), ("tools/gripper_recipes/arx_x5.json", "gripper_recipes"),
                            ("as its recipe says", "recipe"), ("/home/someone/arx.stl", "/home/"), ("C:/arx.stl", "C:/"), ("~/arx.stl", "~/")):
            with self.subTest(text=text):
                problems = self.problems(lambda scene: scene.update(about=text), "arx-x5")
                self.assertIn(("arx-x5", f"{name} names {found!r}, the private importer's inputs: {REBUILD}"), problems)
        self.assertEqual(self.problems(lambda scene: scene.update(about="arx_x5's scene"), "arx-x5"),
                         [("arx-x5", f"{name} names the recipe key 'arx_x5', the private importer's input: {REBUILD}")])
        # Upstream names are no recipe key ("assets/", menagerie's model folders).
        self.assertEqual(self.problems(lambda scene: scene.update(about="menagerie franka_emika_panda/assets/hand.obj, trossen_wxai"), "arx-x5"), [])

    # -- the looks (docs/LIBRARY_VIEW.md "The looks"; the amendment of 2026-11-12) ------------------------------------------

    LOOKS = {"anodized-black": {"color": "#1c1d20", "metalness": 0.6, "roughness": 0.45, "env_intensity": 1.5},
             "shell": {"color": "#eceef0", "metalness": 0, "roughness": 0.3, "clearcoat": 0.6, "clearcoat_roughness": 0.15},
             "pad": {"color": "#232325", "metalness": 0, "roughness": 0.92}}

    def looked(self, scene: dict, **changes) -> None:
        """The tiny scene with looks: its one body the shell, its part the pad, smooth normals; ``changes`` over it."""

        scene["bodies"][0]["look"] = "shell"
        scene.update(looks={name: dict(look) for name, look in self.LOOKS.items() if name != "anodized-black"}, part_look="pad", smooth_deg=35)
        scene.update(changes)

    def test_a_scene_may_name_its_looks(self) -> None:
        # Every key is optional: the committed scenes without them stay sound (test_the_committed_scenes_are_current), and
        # a scene with them is sound when each name is a look of the scene, each look is used, the numbers are in range.
        name = "scenes/franka-hand.json"
        self.assertEqual(self.problems(self.looked, "franka-hand"), [])
        self.assertEqual(self.problems(lambda scene: scene.update(smooth_deg=35), "franka-hand"), [], "smooth normals alone")
        self.assertEqual(self.problems(lambda scene: scene.update(looks={"pad": self.LOOKS["pad"]}, part_look="pad"), "franka-hand"), [], "the part alone")
        self.assertEqual(library_write.SCENE_OPTIONAL, ("camera", "explode", "looks", "part_look", "smooth_deg"))
        self.assertEqual(library_write.BODY_OPTIONAL, ("look",))
        self.assertEqual((library_write.LOOK_KEYS, library_write.LOOK_OPTIONAL), (("color", "metalness", "roughness"), ("clearcoat", "clearcoat_roughness", "env_intensity")))
        look = lambda **changes: (lambda scene: (self.looked(scene), scene["looks"]["shell"].update(changes)))  # noqa: E731
        cases = (
            (lambda scene: (self.looked(scene), scene["bodies"][0].update(look="steel")), f"{name}: body 1 names the look 'steel', which is not one of its looks",
             f"{name}: its look 'shell' is used by nothing"),
            (lambda scene: self.looked(scene, part_look="steel"), f"{name}: its part_look names the look 'steel', which is not one of its looks",
             f"{name}: its look 'pad' is used by nothing"),
            (lambda scene: scene["bodies"][0].update(look="shell"), f"{name}: its looks are not a map of names to looks"),
            (lambda scene: scene.update(part_look="pad"), f"{name}: its looks are not a map of names to looks"),
            (lambda scene: self.looked(scene, looks=dict(scene.get("looks", {}), shell=self.LOOKS["shell"], pad=self.LOOKS["pad"], spare=self.LOOKS["pad"])),
             f"{name}: its look 'spare' is used by nothing"),
            (look(color="#ECEEF0"), f"{name}: its look shell has the colour '#ECEEF0', not an sRGB #rrggbb in lower case"),
            (look(color="white"), f"{name}: its look shell has the colour 'white', not an sRGB #rrggbb in lower case"),
            (look(metalness=1.2), f"{name}: its look shell has the metalness 1.2, not a number 0 to 1"),
            (look(roughness=-0.1), f"{name}: its look shell has the roughness -0.1, not a number 0 to 1"),
            (look(roughness=True), f"{name}: its look shell has the roughness True, not a number 0 to 1"),
            (look(clearcoat=2), f"{name}: its look shell has the clearcoat 2, not a number 0 to 1"),
            (look(env_intensity=-1), f"{name}: its look shell has the env_intensity -1, not a number of 0 or more"),
            (look(emissive="#ffffff"), f"{name}: its look shell has not the keys color, metalness, roughness (and any of clearcoat, clearcoat_roughness, env_intensity)"),
            (lambda scene: (self.looked(scene), scene["looks"]["shell"].pop("roughness")),
             f"{name}: its look shell has not the keys color, metalness, roughness (and any of clearcoat, clearcoat_roughness, env_intensity)"),
            (lambda scene: (self.looked(scene), scene["looks"]["shell"].pop("clearcoat")), f"{name}: its look shell has a clearcoat_roughness without a clearcoat"),
            (lambda scene: (self.looked(scene), scene["looks"]["pad"].update(clearcoat=0.5)),
             f"{name}: its look pad has a clear coat, which the part's own material cannot take (a body's look can)"),
            (lambda scene: (self.looked(scene), scene["looks"].update({"Shell_1": scene["looks"].pop("shell")}), scene["bodies"][0].update(look="Shell_1")),
             f"{name}: its look 'Shell_1' is not named in lower case, digits and hyphens"),
            (lambda scene: self.looked(scene, smooth_deg=0), f"{name}: its smooth_deg (0) is not a crease angle of 1 to 90 degrees"),
            (lambda scene: self.looked(scene, smooth_deg="35"), f"{name}: its smooth_deg ('35') is not a crease angle of 1 to 90 degrees"),
        )
        for edit, *expected in cases:
            with self.subTest(problem=expected[0]):
                self.assertEqual(self.problems(edit, "franka-hand"), [("franka-hand", f"{problem}: {RELOOK}") for problem in expected])
        # A look's problem names the tool that writes the looks; a body's key that is none stays the scene builder's.
        self.assertEqual((library_write.RELOOK, library_write.REBUILD), (RELOOK, REBUILD))
        self.assertEqual(self.problems(lambda scene: scene["bodies"][0].update(colour="#ffffff"), "franka-hand"),
                         [("franka-hand", f"{name}: body 1 has not the keys {', '.join(library_write.BODY_KEYS)} (and look): {REBUILD}")])

    def test_the_stage_draws_the_looks_and_puts_the_figure_back(self) -> None:
        # web/cad/library_stage.js (docs/LIBRARY_VIEW.md "The looks"): a studio of its own for the looks (studio.js's is
        # the sheets' and Gen by Surface's: its numbers are pinned by test_surface_web), made again when a lost context
        # comes back; the part's own material and normals changed in place for a drawing and put back when it goes, the
        # looks' materials disposed; one ghost material per colour, a copy of ghostLook (so the rules' opacity reaches
        # each); the view hands a part without a scene the rules' look.
        stage = (ROOT / "web" / "cad" / "library_stage.js").read_text(encoding="utf-8")
        view = (ROOT / "web" / "cad" / "library_view.js").read_text(encoding="utf-8")
        for text in ('import {lookOf, measure as timed} from "./studio.js";', "const GRIPPER_STUDIO = {",
                     "      if (state.studio !== undefined) state.studio = gripperStudio(renderer);\n",
                     "        normal.array.set(kept.normals);\n        normal.needsUpdate = true;\n",
                     "      dress(null);\n      smoothPart(null);\n",
                     "        extras.looks.forEach(material => material.dispose());\n        extras.ghostLooks.forEach(material => material.dispose());\n",
                     "      const material = ghostLook.clone();\n",
                     "        const mesh = new THREE.Mesh(geometryOf(body.positions, smooth), looks.get(body.look) || partLook);\n",
                     "          if (!given) return figure.show(args);\n",
                     # The pad's tint (the rules' part_pad): the film's sheet laid again over the top FPC, in Assembled
                     # alone, taken down (its texture the figure's: never disposed here) with the drawing.
                     "      for (let i = 0; i < position.length; i += 1) position[i] = film.assembled[i] + lift * film.normals[i];\n",
                     "      if (state.pad) state.pad.visible = view.mode === \"assembled\";\n",
                     "      if (dispose) { pad.geometry.dispose(); pad.material.dispose(); }\n",
                     "      clearPad(dispose);\n", "          if (given.pad) layPad(args.stack, given.pad);\n"):
            self.assertIn(text, stage)
        self.assertEqual(len(re.findall(r'setAttribute\("normal"', stage)), 4,
                         "a body's own geometry, the still stack's two and the pad's own; never the part's drawn geometry")
        self.assertNotIn("map.dispose()", stage, "the pad's texture is the film's, the figure's to dispose")
        self.assertNotRegex(stage, r"\bSTUDIO\.(room|panels)\b|LIGHTS\b|toneMapping", "studio.js's own numbers are not the stage's to change")
        self.assertIn("partLook: given || placed ? null : partLookOf(rules, variant.part, part.family)", view)
        self.assertIn("scenePath || placed ? null : rulesOf(base)", view)
        self.assertIn("pad: rules.part_pad || null};", view)

    def test_the_rules_may_give_a_part_without_a_scene_its_look(self) -> None:
        # The UMI finger and its tapered tips have no scene: scenes.json's rules may name their look (part_looks: a part
        # or its family -> a name of the rules' looks, or a look), without a clear coat (the part's own material), and a
        # crease angle; never a gripper's (its scene's looks).  The committed rules give the finger and its tips'
        # family one look of their own, umi-tpu-orange, and no crease angle (the UMI coloured, 2026-11-12).
        def rules_edit(**changes):
            def change(library: Path) -> None:
                index = _json(library / library_write.SCENES_INDEX)
                for key, value in changes.items():
                    if value is None:
                        index["rules"].pop(key, None)
                    else:
                        index["rules"][key] = value
                _write_json(library / library_write.SCENES_INDEX, index)
            return change

        orange = {"color": "#e85a1c", "metalness": 0, "roughness": 0.85, "env_intensity": 0.3}
        index = _json(LIBRARY / library_write.SCENES_INDEX)
        self.assertEqual(library_write.RULES_OPTIONAL, ("looks", "part_looks", "part_smooth_deg", "part_pad"))
        self.assertEqual((index["rules"]["looks"], index["rules"]["part_looks"]),
                         ({"umi-tpu-orange": orange}, {"umi-finray": "umi-tpu-orange", "umi-tapers": "umi-tpu-orange"}))
        self.assertNotIn("part_smooth_deg", index["rules"], "flat facets, as Gen by Surface draws the part")
        # A base name means the base's numbers in the rules too (docs/LIBRARY_VIEW.md "The base looks"): a look of the
        # rules' own, as the committed one is, has another name.
        base = _json(ROOT / "tools" / "library_looks" / "base.json")["looks"]
        for name, look in index["rules"]["looks"].items():
            with self.subTest(look=name):
                if name in base:
                    self.assertEqual(look, {key: value for key, value in base[name].items() if key != "for"})
        self.assertNotIn("umi-tpu-orange", base)
        self.assertEqual(self.problems(rules_edit()), [], "the committed rules")
        self.assertEqual(self.problems(rules_edit(looks={"tpu-orange": orange}, part_looks={"umi-finray": "tpu-orange", "umi-tapers": "tpu-orange"}, part_smooth_deg=35)), [])
        self.assertEqual(self.problems(rules_edit(looks=None, part_looks={"umi-finray": orange})), [], "a look given in place")
        self.assertEqual(self.problems(rules_edit(looks=None, part_looks=None, part_pad=None)), [], "no look: the parts as Gen by Surface draws them")
        cases = (
            (dict(looks=None, part_looks={"umi-finray": "tpu-orange"}), "scenes/scenes.json: its looks are not a map of names to looks"),
            (dict(looks={"tpu-red": orange}, part_looks={"umi-finray": "tpu-red", "umi-tapers": "tpu-orange"}),
             "scenes/scenes.json: its rule part_looks (umi-tapers) names the look 'tpu-orange', which is not one of its looks"),
            (dict(looks={"tpu-orange": orange, "spare": orange}, part_looks={"umi-finray": "tpu-orange"}), "scenes/scenes.json: its look 'spare' is used by nothing"),
            (dict(part_looks=None, part_pad=None), "scenes/scenes.json: its look 'umi-tpu-orange' is used by nothing"),
            (dict(looks={"tpu-orange": dict(orange, clearcoat=1)}, part_looks={"umi-finray": "tpu-orange"}),
             "scenes/scenes.json: its look tpu-orange has a clear coat, which the part's own material cannot take (a body's look can)"),
            (dict(looks=None, part_looks={"umi-finray": dict(orange, color="orange")}),
             "scenes/scenes.json: its rule part_looks: the look of umi-finray has the colour 'orange', not an sRGB #rrggbb in lower case"),
            (dict(looks=None, part_looks={}), "scenes/scenes.json: its rule part_looks is not a map of parts (or families) to looks"),
            (dict(looks=None, part_looks={"umi-finray": orange}, part_smooth_deg=120), "scenes/scenes.json: its rule part_smooth_deg (120) is not a crease angle of 1 to 90 degrees"),
            (dict(looks=None, part_looks=None, part_pad=None, part_smooth_deg=35), "scenes/scenes.json: its rule part_smooth_deg without part_looks"),
            (dict(colours={}), "scenes/scenes.json: its rules have not the keys camera, checks, depth_tol_mm, explode_stacks, gap_share, ghost_opacity, measure_px, "
                               "min_step_mm, see_through_modes (and any of looks, part_looks, part_smooth_deg, part_pad)"),
        )
        for changes, problem in cases:
            with self.subTest(problem=problem):
                self.assertEqual(self.problems(rules_edit(**changes)), [(None, f"{problem}: {REBUILD}")])
        # A gripper's look is its scene's; a name that is no part and no family is refused too.
        self.assertEqual(self.problems(rules_edit(looks=None, part_looks={"franka-hand": orange})),
                         [(None, "scenes/scenes.json: its rule part_looks names 'franka-hand', not a part without a scene or its family (a gripper's look is its scene's)")])
        # part_look(): the part's id before its family's, a gripper none; its hash the record's.  The committed rules:
        # the finger by its id, each tip by its family, in the one orange, flat, with the pad's tint (part_pad: below).
        pad = index["rules"]["part_pad"]
        for part_id in ("umi-finray", "umi-convex-tip5.8", "umi-trap-tip21.8"):
            with self.subTest(part=part_id):
                self.assertEqual(library_write.part_look(index, self.parts, part_id), {"look": orange, "smooth_deg": None, "pad": pad})
        self.assertIsNone(library_write.part_look(index, self.parts, "franka-hand"))
        index["rules"].update(looks={"tpu-orange": orange, "tip": dict(orange, roughness=0.5)}, part_looks={"umi-tapers": "tpu-orange", "umi-trap-tip5.8": "tip"},
                              part_smooth_deg=35)
        index["rules"].pop("part_pad")
        self.assertEqual(library_write.part_look(index, self.parts, "umi-convex-tip5.8"), {"look": orange, "smooth_deg": 35})
        self.assertEqual(library_write.part_look(index, self.parts, "umi-trap-tip5.8"), {"look": dict(orange, roughness=0.5), "smooth_deg": 35})
        self.assertIsNone(library_write.part_look(index, self.parts, "umi-finray"))
        self.assertIsNone(library_write.part_look(index, self.parts, "franka-hand"))
        for key in library_write.RULES_OPTIONAL:
            index["rules"].pop(key, None)
        self.assertIsNone(library_write.part_look(index, self.parts, "umi-finray"), "no rule: the part as Gen by Surface draws it")
        self.assertIsNone(library_write.part_look_sha256(None))
        self.assertRegex(library_write.part_look_sha256({"look": orange, "smooth_deg": None}), r"^[0-9a-f]{64}$")
        self.assertNotEqual(library_write.part_look_sha256({"look": orange, "smooth_deg": None}), library_write.part_look_sha256({"look": orange, "smooth_deg": 35}))

    def test_the_rules_may_tint_the_assembled_pad_on_those_parts(self) -> None:
        # The user's decision of 2026-11-14 on the UMI pad ("you can do it darken"): every photo of the built sensor shows
        # a dark olive-brown pad on the orange finger (the film seen through the top board's amber polyimide), where the
        # Library's Assembled view drew the amber board alone, one block with the finger.  The rules' part_pad is the
        # tint the stage lays over the film's field in Assembled on a part the rules give a look (docs/LIBRARY_VIEW.md
        # "Parts without a scene"): a colour as a look's and an opacity above 0 and at most 1, only with part_looks;
        # part_look() hands it on, so a fingertip's record of its look is of its pad too (pictures of another pad, or of
        # none, stale).  Committed: #545a3a at 0.65, tuned in the stage against the photo (its pad #725013 to #665318,
        # the stage's #6f5413 at the Assembled home).
        def rules_edit(**changes):
            def change(library: Path) -> None:
                index = _json(library / library_write.SCENES_INDEX)
                for key, value in changes.items():
                    if value is None:
                        index["rules"].pop(key, None)
                    else:
                        index["rules"][key] = value
                _write_json(library / library_write.SCENES_INDEX, index)
            return change

        index = _json(LIBRARY / library_write.SCENES_INDEX)
        pad = {"color": "#545a3a", "opacity": 0.65}
        self.assertEqual((library_write.PAD_KEYS, index["rules"]["part_pad"]), (("color", "opacity"), pad))
        self.assertEqual(self.problems(rules_edit(part_pad=dict(pad, opacity=1))), [], "a tint that hides the board's traces is still a tint")
        self.assertEqual(self.problems(rules_edit(part_pad=None)), [], "no pad: the sheets' own look in Assembled too")
        bad = "scenes/scenes.json: its rule part_pad ({!r}) is not a tint: an sRGB #rrggbb in lower case and an opacity above 0 and at most 1"
        cases = (dict(pad, opacity=0), dict(pad, opacity=1.5), dict(pad, opacity=True), dict(pad, opacity="0.6"), dict(pad, color="#545A3A"),
                 dict(pad, color="olive"), {"color": "#545a3a"}, dict(pad, roughness=0.4), [pad])
        for value in cases:
            with self.subTest(pad=value):
                self.assertEqual(self.problems(rules_edit(part_pad=value)), [(None, f"{bad.format(value)}: {REBUILD}")])
        self.assertEqual(self.problems(rules_edit(looks=None, part_looks=None)),
                         [(None, f"scenes/scenes.json: its rule part_pad without part_looks: {REBUILD}")])
        # part_look() carries the pad where the rules give one, and its hash is of it.
        given = library_write.part_look(index, self.parts, "umi-finray")
        self.assertEqual(given["pad"], pad)
        hashes = {library_write.part_look_sha256(dict(given, pad=value)) for value in (pad, dict(pad, opacity=0.5), dict(pad, color="#000000"))}
        hashes.add(library_write.part_look_sha256({key: value for key, value in given.items() if key != "pad"}))
        self.assertEqual(len(hashes), 4, "another tint, or none, is another look of the part's pictures")
        index["rules"].pop("part_pad")
        self.assertNotIn("pad", library_write.part_look(index, self.parts, "umi-finray"), "no pad: the look's record as before the tint")
        self.assertIsNone(library_write.part_look(dict(index, rules=dict(index["rules"], part_pad=pad)), self.parts, "franka-hand"), "a gripper: its scene's")

    def test_a_shape_the_project_drew_needs_no_row_but_says_so(self) -> None:
        # tools/library_split.py draws plain shapes where a model lacks a component: bodies/<part>/drawn-<name>.stl, the
        # project's own (no NOTICE row), its header saying so; a file so named whose header does not is refused, and any
        # other body still needs its row.
        name, mesh = "scenes/arx-x5.json", "bodies/arx-x5/drawn-screw.stl"
        own = b"FlexiTac-Gen: screw, drawn by the project, not a vendor's part, mm".ljust(80, b" ") + _stl()[80:]

        def drawn(data: bytes, path: str = mesh):
            def change(library: Path) -> None:
                (library / path).write_bytes(data)
                _edit_scene(library, "arx-x5", lambda scene: scene["bodies"].append(
                    {"mesh": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "triangles": 1, "matrix": IDENTITY, "finger": None}))
            return change

        self.assertEqual(self.problems(drawn(own)), [])
        self.assertTrue(library_write.own_body(mesh, own))
        self.assertTrue(library_write.own_body(RAIL))
        self.assertFalse(library_write.own_body("bodies/arx-x5/screw.stl", own))
        self.assertFalse(library_write.own_body("bodies/arx-x5/drawn-Screw 1.stl", own))
        self.assertEqual(self.problems(drawn(_stl(seed=9))), [("arx-x5", f"{name}: body 2: {mesh} is named as the project's own drawing, but its header does "
                         f"not say so (FlexiTac-Gen: ... drawn by the project): draw it with tools/library_split.py: {REBUILD}")])
        self.assertEqual(self.problems(drawn(own, "bodies/arx-x5/screw.stl")),
                         [("arx-x5", f"{name}: body 2: bodies/arx-x5/screw.stl has no row of NOTICE.md with its SHA-256: {REBUILD}")])


class ShowcaseTests(LibraryTestCase):
    """The showcase (the project owner's decision of 2026-11-12: the hand-designed FlexiTac sensor on UFACTORY's xArm
    Gripper G1, the one vendor model the Library shows): the committed files as the decision has them, and
    library_write.showcase() naming each way they could stop being so, on a copy of them."""

    def test_the_showcase_is_committed_and_current(self) -> None:
        self.assertEqual(library_write.showcase(self.parts), ([], set(SHOWCASE_BODIES)))
        # The same pins here and in the writer: the folder, its files, the budget, the file they are made from.
        self.assertEqual(WEB / library_write.SHOWCASE_VENDOR, SHOWCASE)
        self.assertEqual(library_write.SHOWCASE_VENDOR_FILES, SHOWCASE_FILES)
        self.assertEqual(library_write.SHOWCASE_VENDOR_BUDGET_BYTES, SHOWCASE_BUDGET_BYTES)
        self.assertEqual(library_write.SHOWCASE_SOURCE, SHOWCASE_SOURCE)
        self.assertEqual(library_write.SHOWCASE_SOURCE_TRIANGLES, SHOWCASE_SOURCE_TRIANGLES)
        self.assertEqual(library_write.SHOWCASE_BODIES, SHOWCASE_BODIES)
        # The drawn shapes are the project's own by their names and headers (no row of NOTICE.md), each a few triangles.
        for mesh in SHOWCASE_DRAWN:
            with self.subTest(drawn=mesh):
                data = (LIBRARY / mesh).read_bytes()
                self.assertTrue(library_write.own_body(mesh, data))
                self.assertNotIn(mesh, _notice())
                self.assertLessEqual(len(data), 6_000, "a plain shape: 50 bytes a triangle")
        self.assertEqual((library_write.SHOWCASE_SCENE, library_write.SHOWCASE_ID), (SHOWCASE_SCENE, "flexitac-g1"))
        self.assertNotIn(SHOWCASE_SOURCE[1], library_write.DENIED_SHA256, "out of the deny-list since 2026-11-12, refused by showcase()")
        self.assertIsNone(DENIED_NAME.search(library_write.SHOWCASE_ID), "the showcase's id is no vendor's name")
        # Exactly its meshes and its notice, each mesh the pinned bytes, a binary STL whose header says what was changed.
        held = {path.relative_to(SHOWCASE).as_posix(): path.read_bytes() for path in SHOWCASE.rglob("*") if path.is_file()}
        self.assertEqual(sorted(held), sorted([*SHOWCASE_FILES, "NOTICE.md"]))
        for name, pinned in SHOWCASE_FILES.items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256(held[name]).hexdigest(), pinned)
                self.assertIsNotNone(library_write.stl_triangles(held[name]))
                self.assertRegex(held[name][:80].decode("ascii"), r"^modified \(split(, cut)?, decimated <= 0\.1 mm\) by FlexiTac-Gen 2026, see NOTICE\.md *$")
                self.assertRegex(name, r"^[a-z0-9_]+\.stl$", "no space or parenthesis in a published name")
        size = sum(len(data) for data in held.values())
        self.assertLessEqual(size, SHOWCASE_BUDGET_BYTES, f"web/vendor/ufactory-g1/ is {size} bytes")
        self.assertGreater(size, SHOWCASE_BUDGET_BYTES - 50_000, "the budget is just above the folder as built")
        # The folder is beside the Library, outside its 12 MB budget and its bodies' 2.5 MB.
        self.assertNotIn(LIBRARY, SHOWCASE.parents)

    def test_the_notice_says_whose_the_model_is(self) -> None:
        text = (SHOWCASE / "NOTICE.md").read_text(encoding="utf-8")
        folded = " ".join(text.split())
        for words in ("3D model", "the property of UFACTORY", "UFACTORY's download centre", "used by the project owner's decision of 2026-11-12",
                      "not covered by this repository's Apache-2.0 licence", "split", "decimated", "by FlexiTac-Gen 2026",
                      SHOWCASE_SOURCE[0], SHOWCASE_SOURCE[1], "unsplit and undecimated, is not published"):
            with self.subTest(words=words):
                self.assertIn(words, folded)
        self.assertNotRegex(text, r"\bCAD\b")
        self.assertNotRegex(text, r"https?://", "no address is recorded that was not confirmed")
        rows = {row[0]: row for row in NOTICE_ROW.findall(text)}
        self.assertEqual(sorted(rows), sorted(SHOWCASE_FILES))
        for name, row in rows.items():
            with self.subTest(row=name):
                self.assertEqual(row[4], SHOWCASE_FILES[name])
                self.assertEqual(row[2].strip(), "the property of UFACTORY, not Apache-2.0")
                change = re.fullmatch(r"modified: split(, cut at the holder)?, decimated \(quadric error metrics, (0\.\d+) mm\)", row[3].strip())
                self.assertIsNotNone(change, row[3])
                self.assertLessEqual(float(change.group(2)), 0.1)
                self.assertEqual(bool(change.group(1)), name.endswith("_coupler.stl"), "the couplers are the cut fingers")
                self.assertFalse(SPDX & set(re.findall(r"[\w.-]+", row[2])) - {"Apache-2.0"}, "no open licence is claimed")
        # The Library's notice links it, and tables the holder (HandUMI's, Apache-2.0) as it does every body.
        library = (LIBRARY / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("(../vendor/ufactory-g1/NOTICE.md)", library)
        self.assertIn("the property of UFACTORY", " ".join(library.split()))
        holder = _notice()[SHOWCASE_HOLDER[0]]
        self.assertEqual(holder[4], SHOWCASE_HOLDER[1])
        self.assertIn("Apache-2.0", holder[2])
        self.assertIn("`licenses/handumi-hw.txt`", holder[2])
        self.assertIn("`1448278`", holder[1])
        self.assertIn("UMI-RIGHT-Finger-Holder.stl", holder[1])
        self.assertRegex(holder[3].strip(), r"^modified: decimated \(quadric error metrics, 0\.\d+ mm\)$")

    def test_only_the_showcase_s_scene_names_the_folder(self) -> None:
        # No part, entry, fit, picture record, art, sample or other scene: nothing the generator fits, draws or offers.
        readers = [path for folder in (LIBRARY, WEB / "samples", WEB / "vendor" / "umi") for path in sorted(folder.rglob("*"))
                   if path.is_file() and path.suffix in (".json", ".md", ".gz")]
        self.assertGreater(len(readers), 90, "the fits, the art, the scenes, the indexes and the notices")
        for path in readers:
            relative = path.relative_to(WEB).as_posix()
            data = path.read_bytes()
            text = (gzip.decompress(data) if path.suffix == ".gz" else data).decode("utf-8")
            with self.subTest(file=relative):
                if relative == f"library/{SHOWCASE_FILE}":
                    # The showcase's page names the folder once: its sources' link to the folder's notice.
                    self.assertEqual(re.findall(r"[^\s\"]*ufactory-g1[^\s\"]*", text, re.IGNORECASE), ["../vendor/ufactory-g1/NOTICE.md"])
                elif relative in (f"library/{SHOWCASE_SCENE}", "library/NOTICE.md"):
                    self.assertIn("ufactory-g1", text)
                else:
                    self.assertNotIn("ufactory-g1", text.lower())
        # Nor is the showcase a part, an entry or a scene of the index: it has no fit and none of the generator's files.
        self.assertNotIn("flexitac-g1", self.parts["parts"])
        self.assertNotIn("flexitac-g1", self.entries["parts"])
        self.assertFalse([identifier for identifier in self.entries["variants"] if identifier.startswith("flexitac-g1")])
        self.assertNotIn("flexitac-g1", _json(LIBRARY / library_write.SCENES_INDEX)["scenes"])

    def test_the_scene_is_the_tactile_demo_s_gripper_about_the_umi_finger(self) -> None:
        scene = _json(LIBRARY / SHOWCASE_SCENE)
        umi = self.parts["parts"]["umi-finray"]
        self.assertEqual((scene["format"], scene["part"], scene["part_mesh_sha256"], scene["frame"]),
                         ("flexitac-library-scene/v1", "umi-finray", umi["mesh"]["sha256"], "the part's file axes, mm"))
        # Both fingers solid (the showcase is the gripper as built; from its camera the near finger hides nothing of the
        # far one's pad), seen by a camera of its own: from the side of the shell's face without the logo (front -1 with
        # the part the left finger), 60 degrees off the pad's normal, 20 degrees up; exploded 70 off and 40 up, the
        # lifted layers seen apart (the verification of 2026-11-13: edge-on at the Assembled camera).
        self.assertEqual((scene["mate"]["kind"], scene["mate"]["part"], scene["see_through"]), ("mirror", True, []))
        self.assertAlmostEqual(library_write.determinant(scene["mate"]["matrix"]), -1, places=8)
        self.assertEqual(scene["camera"], {"exploded": {"tilt_deg": 70, "elevation_deg": 40, "front": -1},
                                           "assembled": {"tilt_deg": 60, "elevation_deg": 20, "front": -1}})
        # Twice the holder (the sensor finger's, the gripper's left: HandUMI's right one as its mirror image; then the
        # mate's, as it is), then the vendor's twelve, then the shapes the project draws: the shell's twelve screws,
        # each holder's three bolt heads and three nuts, the block in the top slot, and behind each finger the extender
        # board, its sockets and the cable stub.
        meshes = [body["mesh"] for body in scene["bodies"]]
        drawn = (["shell-screw"] * 12 + (["holder-bolt"] * 3 + ["holder-nut"] * 3) * 2 + ["slot-block"]
                 + ["extender", "extender-sockets", "cable-stub"] * 2)
        self.assertEqual(meshes, [SHOWCASE_HOLDER[0]] * 2 + [f"../vendor/ufactory-g1/{name}" for name in SHOWCASE_FILES]
                         + [f"bodies/flexitac-g1/drawn-{name}.stl" for name in drawn])
        self.assertEqual({mesh for mesh in meshes if not mesh.startswith("../")}, set(SHOWCASE_BODIES))
        self.assertEqual([round(library_write.determinant(body["matrix"])) for body in scene["bodies"]],
                         [-1, 1] + [1] * 12 + [1] * 12 + [-1] * 6 + [1] * 6 + [1] + [1] * 3 + [-1] * 3)
        fingers = {body["mesh"].rpartition("/")[2]: body["finger"] for body in scene["bodies"][2:14]}
        self.assertEqual(fingers, {name: "sensor" if name.startswith("finger_l") else "mate" if name.startswith("finger_r") else None
                                   for name in SHOWCASE_FILES})
        self.assertEqual([body["finger"] for body in scene["bodies"][:2]], ["sensor", "mate"])
        self.assertEqual([body["finger"] for body in scene["bodies"][14:]],
                         [None] * 12 + ["sensor"] * 6 + ["mate"] * 6 + [None] + ["sensor"] * 3 + ["mate"] * 3)
        # The pose: the two sensors' centres 55 mm apart (the Tactile Demo's), each on its finger's contact face.
        centre = [0.0, -12.9, -91.86]
        matrix = scene["mate"]["matrix"]
        other = [math.fsum(matrix[row][axis] * centre[axis] for axis in range(3)) + matrix[row][3] for row in range(3)]
        self.assertAlmostEqual(math.dist(centre, other), 55.0, places=6)
        self.assertLess(scene["opening"]["q_mm"], scene["opening"]["limit_mm"], "not fully open: the Tactile Demo's opening")
        self.assertIn("55 mm apart", scene["opening"]["source"])
        # The looks of 2026-11-12: every body and the part with one of the scene's own, the shell alone clear-coated;
        # base looks under their names (the links' and the flange's black) and seven looks of the showcase's own: the
        # shell's gloss, the printed parts' white, the pins' steel and the drawn screws' black (each judged at the home
        # and turned round to the side the owner's photo was taken from), the fingers' orange (the UMI rows' look of the
        # rules, since the merge of 2026-11-13), and the boards' yellow and the cables' white behind the fingers (the
        # builder's tests hold the numbers).
        looks = scene["looks"]
        self.assertEqual(scene["smooth_deg"], 35)
        self.assertEqual(scene["part_look"], "umi-tpu-orange")
        self.assertEqual({body["look"] for body in scene["bodies"]} | {scene["part_look"]}, set(looks))
        self.assertEqual(sorted(looks), ["anodized-black", "ffc-white", "pcb-yellow", "print-white", "screw-black",
                                         "shell-white-gloss", "steel-pin", "umi-tpu-orange"])
        self.assertEqual([name for name, look in looks.items() if "clearcoat" in look], ["shell-white-gloss"])
        by_look = {}
        for body in scene["bodies"]:
            by_look.setdefault(body["look"], set()).add(body["mesh"].rpartition("/")[2])
        self.assertEqual(by_look, {
            "shell-white-gloss": {"body_shell.stl"},
            # (The frame white, as the photo's channel in the top slot is; the black block in it is drawn.)
            "print-white": {"body_frame.stl", "finger_r_coupler.stl", "finger_l_coupler.stl", "umi-right-finger-holder.stl"},
            "anodized-black": {"body_flange.stl", "link_r_outer.stl", "link_r_inner.stl", "link_l_outer.stl", "link_l_inner.stl",
                               "drawn-slot-block.stl"},
            "steel-pin": {"body_pins.stl", "finger_r_pins.stl", "finger_l_pins.stl"},
            "screw-black": {"drawn-shell-screw.stl", "drawn-holder-bolt.stl", "drawn-holder-nut.stl"},
            "pcb-yellow": {"drawn-extender.stl"},
            "ffc-white": {"drawn-extender-sockets.stl", "drawn-cable-stub.stl"}})
        self.assertEqual(looks["steel-pin"]["metalness"], 1)
        # (A matte black: the screws are near-black from both sides, where a metal's flat head mirrors the studio.)
        self.assertEqual((looks["screw-black"]["metalness"], looks["screw-black"]["color"]), (0, looks["anodized-black"]["color"]))
        self.assertEqual(looks["umi-tpu-orange"]["metalness"], 0)
        # (The UMI rows' orange: the showcase's fingers and the Library's UMI finger drawn in one look.)
        self.assertEqual(looks["umi-tpu-orange"], _json(LIBRARY / library_write.SCENES_INDEX)["rules"]["looks"]["umi-tpu-orange"])
        for words in ("hand-designed", "the property of UFACTORY", "project owner's decision of 2026-11-12", "Apache-2.0", "handumi-hw 1448278",
                      "drawn as the mirror image", "as the Tactile Demo draws it", "The gripper as built differs there",
                      "the Library's base looks", "looks of the showcase's own", "Drawn by the project", "no vendor's geometry",
                      "for this reason", "the gripper's left finger", "is not drawn", "which no photo shows",
                      "each tail's end in one of its two sockets", "one small board for each tail", "each judged from both sides"):
            with self.subTest(about=words):
                self.assertIn(words, scene["about"])
        # What the other sensor is (the same board turned, or its mirror image) is not this scene's to say.
        self.assertNotIn("mirror-image board", scene["about"])
        self.assertNotRegex(json.dumps(scene), r"\bCAD\b")

    # What a changed scene or changed rules always add (ShowcasePageTests has it): the showcase's pictures are stale.
    STALE = (f"{SHOWCASE_FILE}: its pictures are of another scene or rules than the files now (scene_sha256): "
             "re-shoot with tools/browser/library_shots.py --showcase")

    def problems(self, edit, patch=None, stale: bool = False) -> list:
        """showcase()'s problems of a copy of the committed files with ``edit`` (the copy's web folder -> None) applied,
        under ``patch`` (a context manager) when given; without the pictures' staleness that any change of the scene
        brings (STALE) unless ``stale``."""

        with tempfile.TemporaryDirectory() as folder, (patch or contextlib.nullcontext()):
            library = _showcase_web(Path(folder))
            edit(library.parent)
            found = library_write.showcase(self.parts, library)[0]
            return found if stale else [message for message in found if message != self.STALE]

    @staticmethod
    def edit_scene(edit):
        def apply(web: Path) -> None:
            path = web / "library" / SHOWCASE_SCENE
            document = _json(path)
            edit(document)
            path.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
        return apply

    @staticmethod
    def edit_notice(edit):
        def apply(web: Path) -> None:
            path = web / "vendor" / "ufactory-g1" / "NOTICE.md"
            path.write_text(edit(path.read_text(encoding="utf-8")), encoding="utf-8")
        return apply

    def test_a_copy_of_the_committed_files_has_no_problem(self) -> None:
        self.assertEqual(self.problems(lambda web: None), [])
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(library_write.scenes(self.parts, _showcase_web(Path(folder)))[1], [])
        # A library without the showcase (neither its scene nor its folder: the tests' tiny ones) has nothing to check.
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(library_write.showcase(self.parts, _scene_library(Path(folder) / "library", self.parts)), ([], set()))

    def test_the_folder_holds_its_pinned_files_alone_within_its_budget(self) -> None:
        folder = "web/vendor/ufactory-g1"
        self.assertEqual(self.problems(lambda web: (web / "vendor" / "ufactory-g1" / "extra.stl").write_bytes(_stl())),
                         [f"{folder}/extra.stl is no file of the showcase (its meshes and its notice alone): remove it"])
        self.assertEqual(self.problems(lambda web: (web / "vendor" / "ufactory-g1" / "more").mkdir() or (web / "vendor" / "ufactory-g1" / "more" / "README.md").write_text("x")),
                         [f"{folder}/more/README.md is no file of the showcase (its meshes and its notice alone): remove it"])
        self.assertEqual(self.problems(lambda web: (web / "vendor" / "ufactory-g1" / "body_pins.stl").unlink()), [f"{folder}/body_pins.stl is missing"])

        def changed(web: Path) -> None:
            path = web / "vendor" / "ufactory-g1" / "link_r_outer.stl"
            path.write_bytes(b"M" + path.read_bytes()[1:])

        self.assertEqual(self.problems(changed), [
            f"{folder}/link_r_outer.stl is not the showcase's pinned file (its SHA-256; a binary STL)",
            f"{SHOWCASE_SCENE}: body 7: ../vendor/ufactory-g1/link_r_outer.stl is not the file its scene names (its SHA-256, bytes or triangles; a binary STL)"])
        size = sum(path.stat().st_size for path in SHOWCASE.rglob("*") if path.is_file())
        self.assertEqual(self.problems(lambda web: None, mock.patch.object(library_write, "SHOWCASE_VENDOR_BUDGET_BYTES", size - 1)),
                         [f"{folder}/ is {size} bytes, over its budget of {size - 1}"])
        self.assertEqual(self.problems(lambda web: None, mock.patch.object(library_write, "SHOWCASE_VENDOR_BUDGET_BYTES", size)), [])
        # The whole folder gone while its scene stays: every file missing (and nothing drawn from it is checked twice).
        self.assertEqual(self.problems(lambda web: shutil.rmtree(web / "vendor" / "ufactory-g1")),
                         [f"{folder}/{name} is missing" for name in sorted([*SHOWCASE_FILES, "NOTICE.md"])]
                         + [f"{SHOWCASE_FILE}: its source's notice ../vendor/ufactory-g1/NOTICE.md is missing"])

    def test_the_notice_s_wording_and_rows_are_checked(self) -> None:
        name = "web/vendor/ufactory-g1/NOTICE.md"

        def without(words: str):
            return self.edit_notice(lambda text: re.sub(r"\s+".join(re.escape(word) for word in words.split()), "it", text))

        for words in ("UFACTORY's download centre", "used by the project owner's decision of 2026-11-12",
                      "not covered by this repository's Apache-2.0 licence", "by FlexiTac-Gen 2026"):
            with self.subTest(words=words):
                self.assertEqual(self.problems(without(words)), [f"{name} does not say {words!r}"])
        # Whose it is: said in the text and in every row.
        found = self.problems(without("the property of UFACTORY"))
        self.assertEqual(found, [f"{name} does not say 'the property of UFACTORY'"]
                         + [f"{name}: the row of {path} does not say 'the property of UFACTORY, not Apache-2.0'" for path in sorted(SHOWCASE_FILES)])
        # Every wording, the file's name and SHA-256 and every row, of a notice that says nothing.
        empty = library_write.showcase_notice_problems("")
        self.assertEqual(empty, [f"{name} does not say {words!r}" for words in library_write.SHOWCASE_WORDS]
                         + [f"{name} does not name the file its meshes are made from ({words})" for words in SHOWCASE_SOURCE[:2]]
                         + [f"{name} has no row of {path} with its pinned SHA-256" for path in sorted(SHOWCASE_FILES)])
        self.assertEqual(library_write.SHOWCASE_WORDS, ("3D model", "the property of UFACTORY", "UFACTORY's download centre",
                                                        "used by the project owner's decision of 2026-11-12",
                                                        "not covered by this repository's Apache-2.0 licence", "split", "decimated", "by FlexiTac-Gen 2026"))
        self.assertEqual(self.problems(self.edit_notice(lambda text: text + "\nThe CAD file.\n")), [f"{name} says CAD (the page's words are 3D model)"])
        self.assertEqual(self.problems(without(SHOWCASE_SOURCE[1])), [f"{name} does not name the file its meshes are made from ({SHOWCASE_SOURCE[1]})"])
        row = "| `body_frame.stl` | the inner frame | the property of UFACTORY, not Apache-2.0 | modified: split, decimated (quadric error metrics, 0.058 mm) |"
        self.assertIn(row, (SHOWCASE / "NOTICE.md").read_text(encoding="utf-8"))
        cases = (
            (row.replace("the property of UFACTORY, not Apache-2.0", "Apache-2.0, UFACTORY"),
             [f"{name}: the row of body_frame.stl does not say 'the property of UFACTORY, not Apache-2.0'"]),
            (row.replace("0.058 mm", "0.2 mm"), [f"{name}: the row of body_frame.stl does not say how it was modified (split, decimated within 0.1 mm)"]),
            (row.replace("modified: split, decimated (quadric error metrics, 0.058 mm)", "unchanged"),
             [f"{name}: the row of body_frame.stl does not say how it was modified (split, decimated within 0.1 mm)"]),
            (row.replace("`body_frame.stl`", "`body_logo.stl`"),
             [f"{name} tables body_logo.stl, no file of the showcase", f"{name} has no row of body_frame.stl with its pinned SHA-256"]),
        )
        for changed, problems in cases:
            with self.subTest(row=changed[:60]):
                self.assertEqual(self.problems(self.edit_notice(lambda text: text.replace(row, changed))), problems)
        self.assertEqual(self.problems(self.edit_notice(lambda text: text.replace(SHOWCASE_FILES["body_frame.stl"], "0" * 64))),
                         [f"{name} has no row of body_frame.stl with its pinned SHA-256"])
        denied = "b0df0eaca944c7401185ada85d22e3111b477c3484c6fa3fd915fce6d6811aaf"
        self.assertEqual(self.problems(self.edit_notice(lambda text: text + f"\nAlso `{denied}`.\n")),
                         [f"{name} names Robotiq 2F-85 (2F85_Opened.stl) (b0df0eaca944), a vendor model of the deny-list"])

    def test_the_vendor_s_own_file_is_never_under_web(self) -> None:
        # The file itself, by its size and SHA-256 (a stand-in here: the real one is no file of this repository's tests).
        data = _stl(3, seed=9)
        stand_in = mock.patch.object(library_write, "SHOWCASE_SOURCE", ("Gripper.stl", hashlib.sha256(data).hexdigest(), len(data)))
        for relative in ("samples/whole.stl", "vendor/ufactory-g1/body_shell.stl", "library/meshes/finger.stl", "cad/x.bin"):
            def placed(web: Path, relative=relative) -> None:
                (web / relative).parent.mkdir(parents=True, exist_ok=True)
                (web / relative).write_bytes(data)
            with self.subTest(file=relative):
                found = self.problems(placed, stand_in)
                self.assertIn(f"web/{relative} is Gripper.stl itself, unsplit and undecimated: never published: remove it", found)
        # Under another 80-byte header it is the file still (its size and the SHA-256 of its triangles); a file of its
        # size with other triangles is not, nor is one of the same triangles and another length.
        renamed = b"exported by another program".ljust(80, b" ") + data[80:]
        triangles = mock.patch.object(library_write, "SHOWCASE_SOURCE_TRIANGLES", hashlib.sha256(data[80:]).hexdigest())

        def files(found: list) -> list:
            # Without the notice's (it names the real file, not the stand-in).
            return [message for message in found if not message.startswith("web/vendor/ufactory-g1/NOTICE.md ")]

        with stand_in, triangles:
            self.assertEqual(files(self.problems(lambda web: (web / "cad").mkdir() or (web / "cad" / "x.stl").write_bytes(renamed))),
                             ["web/cad/x.stl is Gripper.stl itself, unsplit and undecimated: never published: remove it"])
            self.assertEqual(files(self.problems(lambda web: (web / "samples" / "x.stl").write_bytes(_stl(3, seed=8)))), [])
            self.assertEqual(files(self.problems(lambda web: (web / "samples" / "x.stl").write_bytes(renamed + b"\0"))), [])
        self.assertEqual(files(self.problems(lambda web: (web / "samples" / "x.stl").write_bytes(renamed), stand_in)), [],
                         "the real file's triangles are not the stand-in's")
        # Its notice may name the real one (it does); the committed web/ holds no file of its size.
        self.assertFalse([path for path in WEB.rglob("*") if path.is_file() and path.stat().st_size == SHOWCASE_SOURCE[2]])

    def test_the_folder_s_meshes_are_nowhere_else_under_web(self) -> None:
        # A byte copy of a mesh of the folder under another name needs no name of the folder: refused by its SHA-256,
        # wherever it is put (the review of 2026-11-12: as another gripper's body with an open-licence row it passed).
        folder = "web/vendor/ufactory-g1"
        for relative, name in (("vendor/umi/link.stl", "link_r_outer.stl"), ("cad/link.bin", "link_r_outer.stl"), ("samples/frame.stl", "body_frame.stl"),
                               ("library/meshes/shell.stl", "body_shell.stl"), ("library/bodies/arx-x5/frame.stl", "body_frame.stl")):
            def copied(web: Path, relative=relative, name=name) -> None:
                (web / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(web / "vendor" / "ufactory-g1" / name, web / relative)
            with self.subTest(file=relative):
                self.assertEqual(self.problems(copied), [f"web/{relative} is a copy of {folder}/{name}: the vendor's 3D model is shown in {folder}/ alone: remove it"])

        # In the folder itself: a mesh under another's name, or a second copy beside it.
        def swapped(web: Path) -> None:
            shutil.copyfile(web / "vendor" / "ufactory-g1" / "link_r_outer.stl", web / "vendor" / "ufactory-g1" / "extra.stl")

        size = sum(path.stat().st_size for path in SHOWCASE.rglob("*") if path.is_file()) + (SHOWCASE / "link_r_outer.stl").stat().st_size
        self.assertEqual(self.problems(swapped), [f"{folder}/extra.stl is no file of the showcase (its meshes and its notice alone): remove it",
                                                  f"{folder}/ is {size} bytes, over its budget of {SHOWCASE_BUDGET_BYTES}",
                                                  f"{folder}/extra.stl is a copy of {folder}/link_r_outer.stl: the vendor's 3D model is shown in {folder}/ alone: remove it"])

        # As another gripper's body, tabled with an open licence and drawn by its scene: its scene's check passes it
        # (a body with a row), the showcase's refuses it, and so library_write --check and the site build stop.
        with tempfile.TemporaryDirectory() as scratch:
            library = _showcase_web(Path(scratch))
            data = (library.parent / "vendor" / "ufactory-g1" / "body_frame.stl").read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            (library / "bodies" / "arx-x5" / "frame.stl").write_bytes(data)
            notice = library / "NOTICE.md"
            notice.write_text(notice.read_text(encoding="utf-8") + f"\n| `bodies/arx-x5/frame.stl` | a frame | BSD-3-Clause, "
                              f"`licenses/mujoco_menagerie-arx_l5.txt` | unchanged | `{digest}` |\n", encoding="utf-8")
            first = _json(library / "scenes" / "arx-x5.json")["bodies"][0]
            _edit_scene(library, "arx-x5", lambda scene: scene["bodies"].append(
                dict(first, mesh="bodies/arx-x5/frame.stl", sha256=digest, bytes=len(data), triangles=library_write.stl_triangles(data))))
            self.assertEqual(library_write.scenes(self.parts, library)[1], [
                (None, f"web/library/bodies/arx-x5/frame.stl is a copy of {folder}/body_frame.stl: the vendor's 3D model is shown in {folder}/ alone: remove it")])

        # A model of the deny-list anywhere under web/ (the undecimated pieces of the vendor's file are on it).
        stand = _stl(2, seed=5)
        with mock.patch.dict(library_write.DENIED_SHA256, {hashlib.sha256(stand).hexdigest(): "xArm Gripper G1, not decimated (body.stl)"}):
            self.assertEqual(self.problems(lambda web: (web / "samples" / "body.stl").write_bytes(stand)),
                             ["web/samples/body.stl is a vendor model of the deny-list (xArm Gripper G1, not decimated (body.stl)): never published: remove it"])
        undecimated = {label for label in DENIED_SHA256.values() if label.startswith("xArm Gripper G1, not decimated (")}
        self.assertEqual(len(undecimated), 16, "the Tactile Demo's seven first pieces and the nine of its body and fingers")
        self.assertFalse(set(DENIED_SHA256) & set(SHOWCASE_FILES.values()), "the decimated pieces are the ones shown")

    def test_nothing_else_may_name_the_folder(self) -> None:
        def naming(relative: str):
            def apply(web: Path) -> None:
                path = web / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = path.read_text(encoding="utf-8") if path.is_file() else "{}\n"
                path.write_text(text + '{"mesh": "../vendor/ufactory-g1/body_shell.stl"}\n', encoding="utf-8")
            return apply

        for relative in ("library/parts.json", "library/entries.json", "library/shots/manifest.json", "library/fits/widowx-250-2mm.json",
                         "library/fits/new-part-2mm.json", "library/scenes/arx-x5.json", "library/scenes/scenes.json", "samples/samples.json",
                         "samples/NOTICE.md", "vendor/umi/default-fit.json"):
            with self.subTest(file=relative):
                self.assertEqual(self.problems(naming(relative)),
                                 [f"web/{relative} names the showcase's folder (web/vendor/ufactory-g1/): only {SHOWCASE_SCENE} may"])
        # In any case of its letters; the Library's notice, which links the folder's own, may.
        self.assertEqual(self.problems(lambda web: (web / "library" / "fits" / "x.json").write_text('"UFACTORY-G1"', encoding="utf-8")),
                         [f"web/library/fits/x.json names the showcase's folder (web/vendor/ufactory-g1/): only {SHOWCASE_SCENE} may"])
        self.assertIn("ufactory-g1", (LIBRARY / "NOTICE.md").read_text(encoding="utf-8"))
        # A gripper's scene drawing a vendor's mesh: refused as a body of its own folder's, and as a name of the folder.
        with tempfile.TemporaryDirectory() as folder:
            library = _showcase_web(Path(folder))
            first = json.loads((library / "scenes" / "arx-x5.json").read_text(encoding="utf-8"))["bodies"][0]["mesh"]
            _edit_scene(library, "arx-x5", lambda scene: scene["bodies"][0].update(mesh="../vendor/ufactory-g1/body_shell.stl"))
            self.assertEqual(library_write.scenes(self.parts, library)[1], [
                ("arx-x5", f"scenes/arx-x5.json: body 1's mesh '../vendor/ufactory-g1/body_shell.stl' is not a file of bodies/arx-x5/: {REBUILD}"),
                (None, f"web/library/scenes/arx-x5.json names the showcase's folder (web/vendor/ufactory-g1/): only {SHOWCASE_SCENE} may: {REBUILD_SHOWCASE}"),
                (None, f"{first}: a file of no scene: {REBUILD}")])

    def test_the_scene_draws_the_folder_s_files_and_the_holder(self) -> None:
        name = SHOWCASE_SCENE
        shell = "../vendor/ufactory-g1/body_shell.stl"
        cases = (
            (lambda scene: scene["bodies"][2].update(mesh="../vendor/umi/UMI-Soft-Gripper-Finger.stl"),
             [f"{name}: body 3's mesh '../vendor/umi/UMI-Soft-Gripper-Finger.stl' is not a file of the showcase's folder (../vendor/ufactory-g1/)",
              f"{name} does not draw web/vendor/ufactory-g1/body_shell.stl"]),
            (lambda scene: scene["bodies"][2].update(mesh="../vendor/ufactory-g1/../umi/LICENSE"),
             [f"{name}: body 3's mesh '../vendor/ufactory-g1/../umi/LICENSE' is not a file of the showcase's folder (../vendor/ufactory-g1/)",
              f"{name} does not draw web/vendor/ufactory-g1/body_shell.stl"]),
            (lambda scene: scene["bodies"].pop(13), [f"{name} does not draw web/vendor/ufactory-g1/finger_l_pins.stl"]),
            (lambda scene: scene["bodies"][2].update(sha256="0" * 64),
             [f"{name}: body 3: {shell} is not the file its scene names (its SHA-256, bytes or triangles; a binary STL)"]),
            (lambda scene: scene["bodies"][2].update(triangles=3),
             [f"{name}: body 3: {shell} is not the file its scene names (its SHA-256, bytes or triangles; a binary STL)"]),
            (lambda scene: scene["bodies"][2].update(matrix=[[2, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
             [f"{name}: body 3's matrix is not orthonormal (its upper 3 x 3)"]),
            (lambda scene: scene["bodies"][2].update(finger="left"), [f"{name}: body 3's finger 'left' is not sensor, mate or null"]),
            (lambda scene: scene["bodies"][2].update(colour="white"), [f"{name}: body 3 has not the keys {', '.join(library_write.BODY_KEYS)}"]),
            (lambda scene: scene.update(part="arx-x5"), [f"{name} is the scene of 'arx-x5'"]),
            (lambda scene: scene.update(part_mesh_sha256="0" * 64), [f"{name} is drawn about another mesh of umi-finray than parts.json's (part_mesh_sha256)"]),
            (lambda scene: scene["mate"].update(kind="turned"), [f"{name}: its mate is 'turned', but its matrix's determinant is -1"]),
            (lambda scene: scene["bodies"][0].update(mesh="bodies/umi-finray/holder.stl"),
             [f"{name}: body 1's mesh 'bodies/umi-finray/holder.stl' is not a file of bodies/flexitac-g1/"]),
            (lambda scene: scene["bodies"][0].update(sha256="0" * 64),
             [f"{name}: body 1: {SHOWCASE_HOLDER[0]} is not the file its scene names (its SHA-256, bytes or triangles; a binary STL)"]),
        )
        for edit, problems in cases:
            with self.subTest(problems=problems[0]):
                self.assertEqual(self.problems(self.edit_scene(edit)), problems)
        self.assertEqual(self.problems(lambda web: (web / "library" / SHOWCASE_SCENE).unlink()), [f"{name} is missing or not JSON"])

        # The holder: the pinned file, tabled in the Library's notice with its open licence, as every body.
        def other(web: Path) -> None:
            path = web / "library" / SHOWCASE_HOLDER[0]
            path.write_bytes(_stl())
            data = path.read_bytes()
            self.edit_scene(lambda scene: [body.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), triangles=1)
                                           for body in scene["bodies"][:2]])(web)

        self.assertEqual(self.problems(other), [f"{name}: body 1: {SHOWCASE_HOLDER[0]} has no row of NOTICE.md with its SHA-256",
                                                f"{name}: body 2: {SHOWCASE_HOLDER[0]} has no row of NOTICE.md with its SHA-256",
                                                f"{name}: {SHOWCASE_HOLDER[0]} is not the showcase's pinned file (its SHA-256)"])

        def another(web: Path) -> None:
            shutil.copyfile(web / "library" / SHOWCASE_HOLDER[0], web / "library" / "bodies" / "flexitac-g1" / "other.stl")
            notice = web / "library" / "NOTICE.md"
            notice.write_text(notice.read_text(encoding="utf-8").replace(f"`{SHOWCASE_HOLDER[0]}`", "`bodies/flexitac-g1/other.stl`"), encoding="utf-8")
            self.edit_scene(lambda scene: [body.update(mesh="bodies/flexitac-g1/other.stl") for body in scene["bodies"][:2]])(web)

        self.assertEqual(self.problems(another), [f"{name}: bodies/flexitac-g1/other.stl is not a body of the showcase ({', '.join(SHOWCASE_BODIES)})"])

        # A shape the project drew: its header says so and its bytes are the pinned ones, or it is refused (a mesh under
        # a drawn shape's name, a shape the showcase's tool does not draw).
        def redrawn(web: Path) -> None:
            path = web / "library" / "bodies" / "flexitac-g1" / "drawn-slot-block.stl"
            data = library_write.OWN_HEADER + b"slot-block, drawn by the project, not a vendor's part, mm".ljust(66) + _stl()[80:]
            path.write_bytes(data)
            self.edit_scene(lambda scene: [body.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), triangles=1)
                                           for body in scene["bodies"] if body["mesh"].endswith("drawn-slot-block.stl")])(web)

        self.assertEqual(self.problems(redrawn), [f"{name}: bodies/flexitac-g1/drawn-slot-block.stl is not the showcase's pinned file (its SHA-256)"])

        def unlabelled(web: Path) -> None:
            path = web / "library" / "bodies" / "flexitac-g1" / "drawn-slot-block.stl"
            data = _stl()
            path.write_bytes(data)
            self.edit_scene(lambda scene: [body.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), triangles=1)
                                           for body in scene["bodies"] if body["mesh"].endswith("drawn-slot-block.stl")])(web)

        found = self.problems(unlabelled)
        self.assertEqual(len(found), 2, found)
        self.assertIn("drawn-slot-block.stl is named as the project's own drawing, but its header does not say so", found[0])
        self.assertEqual(found[1], f"{name}: bodies/flexitac-g1/drawn-slot-block.stl is not the showcase's pinned file (its SHA-256)")

    def test_the_scene_s_looks_are_the_amendment_s(self) -> None:
        # The looks of 2026-11-12, by the Library's one rule (scene_look_problems(), as every gripper's scene), over all
        # the scene's bodies, the vendor's too: a name a look of the scene, a look a colour and numbers within their
        # ranges, every look used, no clear coat on the part's own, the crease angle 1 to 90 degrees.
        name = SHOWCASE_SCENE
        cases = (
            (lambda scene: scene.update(part_look="gold"),
             [f"{name}: its part_look names the look 'gold', which is not one of its looks", f"{name}: its look 'umi-tpu-orange' is used by nothing"]),
            (lambda scene: scene["bodies"][5].update(look="gold"), [f"{name}: body 6 names the look 'gold', which is not one of its looks"]),
            (lambda scene: scene["bodies"][0].update(look="gold"), [f"{name}: body 1 names the look 'gold', which is not one of its looks"]),
            (lambda scene: scene["bodies"][2].update(look=["shell-white-gloss"]),
             [f"{name}: body 3 names the look ['shell-white-gloss'], which is not one of its looks", f"{name}: its look 'shell-white-gloss' is used by nothing"]),
            (lambda scene: scene["looks"]["umi-tpu-orange"].update(color="orange"), [f"{name}: its look umi-tpu-orange has the colour 'orange', not an sRGB #rrggbb in lower case"]),
            (lambda scene: scene["looks"]["umi-tpu-orange"].update(color="#E85A1C"), [f"{name}: its look umi-tpu-orange has the colour '#E85A1C', not an sRGB #rrggbb in lower case"]),
            (lambda scene: scene["looks"]["steel-pin"].update(metalness=2), [f"{name}: its look steel-pin has the metalness 2, not a number 0 to 1"]),
            (lambda scene: scene["looks"]["steel-pin"].update(metalness=True), [f"{name}: its look steel-pin has the metalness True, not a number 0 to 1"]),
            (lambda scene: scene["looks"]["steel-pin"].pop("roughness"),
             [f"{name}: its look steel-pin has not the keys color, metalness, roughness (and any of clearcoat, clearcoat_roughness, env_intensity)"]),
            (lambda scene: scene["looks"]["steel-pin"].update(texture="brushed"),
             [f"{name}: its look steel-pin has not the keys color, metalness, roughness (and any of clearcoat, clearcoat_roughness, env_intensity)"]),
            (lambda scene: scene["looks"]["shell-white-gloss"].update(env_intensity=-1),
             [f"{name}: its look shell-white-gloss has the env_intensity -1, not a number of 0 or more"]),
            (lambda scene: scene["looks"]["shell-white-gloss"].pop("clearcoat"), [f"{name}: its look shell-white-gloss has a clearcoat_roughness without a clearcoat"]),
            (lambda scene: scene["looks"]["umi-tpu-orange"].update(clearcoat=0.5),
             [f"{name}: its look umi-tpu-orange has a clear coat, which the part's own material cannot take (a body's look can)"]),
            (lambda scene: scene["looks"].update(gold={"color": "#c9a45c", "metalness": 1, "roughness": 0.35}), [f"{name}: its look 'gold' is used by nothing"]),
            (lambda scene: scene["looks"].update(Gold=scene["looks"].pop("steel-pin")),
             [f"{name}: its look 'Gold' is not named in lower case, digits and hyphens"]
             + [f"{name}: body {number} names the look 'steel-pin', which is not one of its looks" for number in (6, 12, 14)]
             + [f"{name}: its look 'Gold' is used by nothing"]),
            (lambda scene: scene.update(smooth_deg="35"), [f"{name}: its smooth_deg ('35') is not a crease angle of 1 to 90 degrees"]),
            (lambda scene: scene.update(smooth_deg=0), [f"{name}: its smooth_deg (0) is not a crease angle of 1 to 90 degrees"]),
            (lambda scene: scene.update(looks=[]), [f"{name}: its looks are not a map of names to looks"]),
            (lambda scene: scene.pop("looks"), [f"{name}: its looks are not a map of names to looks"]),
            (lambda scene: scene.update(shine=1),
             [f"{name} has not the keys {', '.join(library_write.SCENE_KEYS)} (and any of {', '.join(library_write.SCENE_OPTIONAL)})"]),
        )
        for edit, problems in cases:
            with self.subTest(problems=problems[0]):
                self.assertEqual(self.problems(self.edit_scene(edit)), problems)
        self.assertEqual(self.problems(self.edit_scene(lambda scene: scene["looks"]["shell-white-gloss"].update(env_intensity=1.5))), [])
        # The same function as the grippers' scenes: the showcase has no check of the looks of its own.
        with tempfile.TemporaryDirectory() as folder:
            library = _showcase_web(Path(folder))
            scene = _json(library / SHOWCASE_SCENE)
            scene["bodies"][5]["look"] = "gold"
            self.assertEqual(library_write.scene_look_problems("umi-finray", scene, scene="flexitac-g1"),
                             [f"{name}: body 6 names the look 'gold', which is not one of its looks"])
            self.assertEqual(library_write.scene_look_problems("umi-finray", scene),
                             ["scenes/umi-finray.json: body 6 names the look 'gold', which is not one of its looks"])

    def test_the_scenes_check_takes_the_showcase_in(self) -> None:
        def problems(edit) -> list:
            with tempfile.TemporaryDirectory() as folder:
                library = _showcase_web(Path(folder))
                edit(library)
                return library_write.scenes(self.parts, library)[1]

        def indexed(library: Path) -> None:
            index = _json(library / library_write.SCENES_INDEX)
            index["scenes"]["flexitac-g1"] = SHOWCASE_SCENE
            (library / library_write.SCENES_INDEX).write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")

        # The showcase is no part: its scene is not the index's.
        self.assertEqual(problems(indexed), [(None, f"flexitac-g1: a scene for no part of parts.json: {REBUILD}")])
        self.assertEqual(problems(lambda library: (library / "bodies" / "flexitac-g1" / "old.stl").write_bytes(_stl())),
                         [(None, f"bodies/flexitac-g1/old.stl: a file of no scene: {REBUILD}")])
        self.assertEqual(problems(lambda library: (library / SHOWCASE_SCENE).unlink()),
                         [(None, f"{SHOWCASE_SCENE} is missing or not JSON: {REBUILD_SHOWCASE}")]
                         + [(None, f"{mesh}: a file of no scene: {REBUILD}") for mesh in sorted(SHOWCASE_BODIES)])
        self.assertEqual(problems(lambda library: (library.parent / "vendor" / "ufactory-g1" / "extra.stl").write_bytes(_stl())),
                         [(None, f"web/vendor/ufactory-g1/extra.stl is no file of the showcase (its meshes and its notice alone): remove it")])

        # No host path or private input in the scene or the folder's notice, as in every scene.
        def pathed(library: Path) -> None:
            notice = library.parent / "vendor" / "ufactory-g1" / "NOTICE.md"
            notice.write_text(notice.read_text(encoding="utf-8") + "\nRead from /home/someone/files.\n", encoding="utf-8")

        self.assertEqual(problems(pathed), [(None, f"../vendor/ufactory-g1/NOTICE.md names '/home/', the private importer's inputs: {REBUILD}")])
        # library_write --check and the site build stop on them (scenes()' problems with no part).
        with tempfile.TemporaryDirectory() as folder:
            library = _showcase_web(Path(folder))
            (library.parent / "vendor" / "ufactory-g1" / "extra.stl").write_bytes(_stl())
            _, found = library_write.scenes(self.parts, library)
            self.assertEqual([part for part, _ in found], [None])


class ShowcasePageTests(LibraryTestCase):
    """The showcase's page's document (showcase.json, 2026-11-12; docs/LIBRARY_VIEW.md "The showcase's page"): the
    committed one current, and library_write.showcase_page() naming each way it could stop being so, on a copy."""

    RESHOOT = "re-shoot with tools/browser/library_shots.py --showcase"

    def test_the_committed_document_is_current(self) -> None:
        self.assertEqual(library_write.showcase_page(self.parts), ([], False))
        document = _json(LIBRARY / SHOWCASE_FILE)
        self.assertEqual(sorted(document), list(library_write.SHOWCASE_KEYS))
        self.assertEqual((document["format"], document["id"], document["title"]), ("flexitac-library-showcase/v1", "flexitac-g1", "FlexiTac on xArm"))
        # The user's request of 2026-11-12 (labelled as hand-designed, not auto-generated), worded again on 2026-11-15
        # ("pre-agent hand design version, original flexitac ... using flexitac PCB to making the tactile sensor
        # accessible, reliable, and standarlized"): the label, the card's one line; the page's line of detail keeps the
        # sensor's size and fingers. The line was chosen again the same day ("Using flexible PCB to make tactile sensors
        # accessible, reliable and standardized."): it names the flexible PCB technology FlexiTac is built on, not FlexiTac.
        self.assertEqual(document["label"], "Original FlexiTac \u00b7 Hand-designed, pre-agent")
        self.assertEqual(document["text"], "Using flexible PCB to make tactile sensors accessible, reliable and standardized.")
        self.assertEqual(document["detail"], "The original FlexiTac sensor, 12 \u00d7 32 taxels at 2 mm, on the xArm gripper's soft fingers.")
        self.assertNotRegex(json.dumps(document), r"\bCAD\b")
        # It is no entry: no fit, no build, no download of the generator's; its id is no part's, variant's or family's.
        for key in ("fit", "build_id", "files", "variants", "pitch_mm"):
            self.assertNotIn(key, document)
        for names in (self.entries["variants"], self.entries["parts"], self.entries.get("families") or {}):
            self.assertNotIn(document["id"], names)
        self.assertIsNone(DENIED_NAME.search(document["id"]))
        # The placed record: the pad's own, with the showcase's scene; the finger the Library's UMI finger.
        placed = _json(WEB / library_write.SHOWCASE_PLACED)
        self.assertIsNone(placed["scene"], "the pad's own record names no scene")
        self.assertEqual(document["placed"], dict(placed, scene=SHOWCASE_SCENE))
        self.assertEqual(document["placed"]["mesh"]["sha256"], self.parts["parts"]["umi-finray"]["mesh"]["sha256"])
        self.assertEqual(_json(LIBRARY / SHOWCASE_SCENE)["part_mesh_sha256"], document["placed"]["mesh"]["sha256"])
        self.assertEqual(document["sensor"], {"rows": 32, "columns": 12, "pitch_mm": 2, "field_mm": [23, 63]})
        # The tutorial: the address the pad's notice records for its Gerbers.
        self.assertIn(f"`{document['tutorial']['href']}`", (WEB / library_write.SHOWCASE_PAD_NOTICE).read_text(encoding="utf-8"))
        self.assertIn("tutorial", document["tutorial"]["label"])
        # The sources: UFACTORY's 3D model by the owner's decision, the FlexiTac V2 design and its licence, each with
        # its notice, a file of the site.
        self.assertEqual([item["notice"] for item in document["sources"]], ["../vendor/ufactory-g1/NOTICE.md", "../vendor/flexitac-v2/NOTICE.md"])
        self.assertIn("project owner's decision", document["sources"][0]["text"])
        self.assertIn("CC BY-NC 4.0", document["sources"][1]["text"])
        for item in document["sources"]:
            self.assertTrue((LIBRARY / item["notice"]).is_file())
        # The pictures: 4:5 (the gripper upright), WebP with alpha, in showcase/ alone, the bytes the document names.
        image = document["image"]
        self.assertEqual(sorted(path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "showcase").rglob("*") if path.is_file()), sorted(SHOWCASE_PICTURES))
        self.assertEqual([image[kind]["src"] for kind in ("exploded", "assembled", "card")], list(SHOWCASE_PICTURES))
        self.assertEqual((library_write.SHOWCASE_SHOT_SIZE, library_write.SHOWCASE_CARD_SIZE), ((1280, 1600), (800, 1000)))
        for kind in ("exploded", "assembled", "card"):
            with self.subTest(picture=kind):
                data = (LIBRARY / image[kind]["src"]).read_bytes()
                self.assertEqual((image[kind]["bytes"], image[kind]["sha256"]), (len(data), hashlib.sha256(data).hexdigest()))
                self.assertEqual(library_write.webp_info(data), (image[kind]["width"], image[kind]["height"], True))
                self.assertEqual(image[kind]["width"] * 5, image[kind]["height"] * 4)
                self.assertLess(len(data), 200_000)
        self.assertIn("hand-designed", image["alt"])
        # What they were shot from: this scene and these rules, this art, this placed record; the gripper fills the
        # picture's height (its margins above and below under a tenth of it), in the middle.
        shot = document["shot"]
        self.assertEqual({key: shot[key] for key in ("scene", "scene_sha256", "art_sha256", "placed_sha256", "figure_sha256", "view_sha256")},
                         library_write.showcase_shot())
        for mode in ("exploded", "assembled"):
            left, top, right, bottom = shot["margins_px"][mode]
            with self.subTest(margins=mode):
                self.assertLess(max(top, bottom), 160)
                self.assertLessEqual(abs(left - right), 1)
                self.assertLessEqual(abs(top - bottom), 1)
        self.assertTrue(53 < shot["numbers"]["jaw_gap_mm"] < 55, "the two pads' faces: their centres 55 mm apart")
        self.assertIsNone(shot["numbers"]["ghost_cover"], "no finger is see-through")
        self.assertTrue((LIBRARY / SHOWCASE_FILE).read_text(encoding="utf-8").isascii())
        self.assertEqual((LIBRARY / SHOWCASE_FILE).read_text(encoding="utf-8"), library_write.showcase_text(document))

    def problems(self, edit=None, files=None, older: bool = False):
        """showcase_page()'s problems (``older``: its second value) of a copy of the committed files with ``edit``
        (showcase.json's document -> None) and ``files`` (the copy's library -> None) applied."""

        with tempfile.TemporaryDirectory() as folder:
            library = _showcase_web(Path(folder))
            if edit:
                document = _json(library / SHOWCASE_FILE)
                edit(document)
                (library / SHOWCASE_FILE).write_text(library_write.showcase_text(document), encoding="utf-8")
            if files:
                files(library)
            found = library_write.showcase_page(self.parts, library)
            return found[1] if older else found[0]

    def test_its_words_are_checked(self) -> None:
        name = SHOWCASE_FILE
        self.assertEqual(self.problems(), [])
        cases = (
            (lambda d: d.update(format="flexitac-library-showcase/v2"), [f"{name}: the format is 'flexitac-library-showcase/v2', not flexitac-library-showcase/v1"]),
            (lambda d: d.update(id="umi-finray"), [f"{name}: its id is not flexitac-g1, or a part or a family has that id"]),
            (lambda d: d.update(note="x"), [f"{name} has not the keys {', '.join(library_write.SHOWCASE_KEYS)}"]),
            (lambda d: d.pop("tutorial"), [f"{name} has not the keys {', '.join(library_write.SHOWCASE_KEYS)}"]),
            (lambda d: d.update(title=""), [f"{name}: its title is not one line of 1 to 40 characters"]),
            (lambda d: d.update(title="FlexiTac on xArm\nand more"), [f"{name}: its title is not one line of 1 to 40 characters"]),
            (lambda d: d.update(text="x" * 141), [f"{name}: its text is not one line of 1 to 140 characters"]),
            (lambda d: d.update(detail="x" * 141), [f"{name}: its detail is not one line of 1 to 140 characters"]),
            (lambda d: d.update(detail="12 x 32 taxels\nat 2 mm"), [f"{name}: its detail is not one line of 1 to 140 characters"]),
            (lambda d: d.pop("detail"), [f"{name} has not the keys {', '.join(library_write.SHOWCASE_KEYS)}"]),
            # The label says all three: the original FlexiTac, hand-designed, pre-agent (2026-11-15).
            (lambda d: d.update(label="Hand-designed, pre-agent"), [f"{name}: its label does not say original, hand-designed, pre-agent"]),
            (lambda d: d.update(label="Original FlexiTac, pre-agent"), [f"{name}: its label does not say original, hand-designed, pre-agent"]),
            (lambda d: d.update(label="Original FlexiTac, hand-designed"), [f"{name}: its label does not say original, hand-designed, pre-agent"]),
            (lambda d: d.update(text="The original CAD of the sensor."), [f"{name} says CAD (the page's words are 3D model)"]),
            (lambda d: d.update(text="Read from /home/someone/files."), [f"{name} names '/home/', the private importer's inputs"]),
            (lambda d: d["sensor"].update(field_mm=[24, 64]), [f"{name}: its sensor's field [24, 64] mm is not the art's ([23, 63])"]),
            (lambda d: d["sensor"].update(rows=0), [f"{name}: its sensor is not {{rows, columns, pitch_mm, field_mm}}"]),
            (lambda d: d["tutorial"].update(href="https://example.com/tutorial"), [f"{name}: its tutorial's address is not the one web/vendor/flexitac-v2/NOTICE.md records"]),
            (lambda d: d["tutorial"].update(href="//docs.google.com/document/d/1bvz6AL7BUkhj4Dj7n9DFXTjnGIX4-ziN8-smiCKpVZU/"),
             [f"{name}: its tutorial's address is not the one web/vendor/flexitac-v2/NOTICE.md records"]),
            (lambda d: d["tutorial"].pop("label"), [f"{name}: its tutorial is not {{label, href}}"]),
            (lambda d: d["sources"].reverse(), [f"{name}: its sources are not [{{text, notice}}] of ../vendor/ufactory-g1/NOTICE.md and ../vendor/flexitac-v2/NOTICE.md"]),
            (lambda d: d["sources"][1].update(notice="../vendor/umi/NOTICE.md"),
             [f"{name}: its sources are not [{{text, notice}}] of ../vendor/ufactory-g1/NOTICE.md and ../vendor/flexitac-v2/NOTICE.md"]),
            (lambda d: d["sources"][0].update(text="Gripper: a model of the gripper"), [f"{name}: its source of ../vendor/ufactory-g1/NOTICE.md does not say UFACTORY and 3D model"]),
            (lambda d: d["sources"][1].update(text="Sensor: the FlexiTac V2 design"), [f"{name}: its source of ../vendor/flexitac-v2/NOTICE.md does not say FlexiTac and CC BY-NC 4.0"]),
            # The vendor's folder named only as its notice: not as a mesh, a picture or a word of the text.
            (lambda d: d.update(text="See ../vendor/ufactory-g1/body_shell.stl."), [f"{name} names the showcase's folder (web/vendor/ufactory-g1/) elsewhere than as its notice"]),
        )
        for edit, problems in cases:
            with self.subTest(problems=problems[0]):
                self.assertEqual(self.problems(edit), problems)

    def test_its_placed_record_is_the_pad_s_own_on_the_showcase_s_scene(self) -> None:
        name = SHOWCASE_FILE
        other = f"{name}: its placed record is not web/vendor/flexitac-v2/umi-finray.placed.json with the scene scenes/flexitac-g1.json: {self.RESHOOT}"
        self.assertEqual(self.problems(lambda d: d["placed"].update(scene=None)), [other])
        self.assertEqual(self.problems(lambda d: d["placed"].update(scene="scenes/arx-x5.json")), [other])
        self.assertEqual(self.problems(lambda d: d["placed"]["wrap"].update(side="right")), [other])
        self.assertEqual(self.problems(lambda d: d.update(placed=None)), [other])

        # The pad's own record changed under it: the document's copy is no longer it, and the pictures are of another.
        def moved(library: Path) -> None:
            path = library.parent / library_write.SHOWCASE_PLACED
            record = _json(path)
            record["face"]["origin"][2] -= 1
            _write_json(path, record)

        self.assertEqual(self.problems(files=moved), [other, f"{name}: its pictures are of another placed record than the files now (placed_sha256): {self.RESHOOT}"])
        self.assertEqual(self.problems(files=lambda library: (library.parent / library_write.SHOWCASE_PLACED).unlink())[0],
                         "web/vendor/flexitac-v2/umi-finray.placed.json is missing or not JSON")

        # The pad's own record about another finger's mesh, the document's copy with it (the review of 2026-11-12: no
        # test held this guard): the record is the pad's own, but not about the Library's UMI finger.
        def other_mesh(library: Path) -> None:
            path = library.parent / library_write.SHOWCASE_PLACED
            record = _json(path)
            record["mesh"]["sha256"] = "0" * 64
            _write_json(path, record)
            document = _json(library / SHOWCASE_FILE)
            document["placed"]["mesh"]["sha256"] = "0" * 64
            (library / SHOWCASE_FILE).write_text(library_write.showcase_text(document), encoding="utf-8")

        self.assertEqual(self.problems(files=other_mesh), [f"{name}: its placed record is about another mesh than umi-finray's (parts.json)",
                                                           f"{name}: its pictures are of another placed record than the files now (placed_sha256): {self.RESHOOT}"])

    def test_its_pictures_are_the_files_it_names(self) -> None:
        name = SHOWCASE_FILE
        card = SHOWCASE_PICTURES[2]
        self.assertEqual(self.problems(lambda d: d.update(image=None, shot=None)), [f"{name}: no pictures yet: {self.RESHOOT}"])
        self.assertEqual(self.problems(lambda d: d["image"].pop("alt")),
                         [f"{name}: its image is not {{exploded, assembled, card: {{src, width, height, bytes, sha256}}, alt}}: {self.RESHOOT}"])
        self.assertEqual(self.problems(lambda d: d["image"]["card"].update(width=640, height=800)), [f"{name}: its card picture is not {card} at 800 x 1000: {self.RESHOOT}"])
        self.assertEqual(self.problems(lambda d: d["image"]["card"].update(src="shots/umi-finray-2mm.exploded.card.webp")),
                         [f"{name}: its card picture is not {card} at 800 x 1000: {self.RESHOOT}"])
        self.assertEqual(self.problems(files=lambda library: (library / card).unlink()), [f"{card} is missing: {self.RESHOOT}"])

        def changed(library: Path) -> None:
            (library / card).write_bytes((library / card).read_bytes() + b"\0")

        self.assertEqual(self.problems(files=changed), [f"{card} is not the file {name} names: {self.RESHOOT}"])

        # Another picture under its name, recorded as it is: not a WebP with alpha of the card's size.
        def other(library: Path) -> None:
            data = (LIBRARY / "shots" / "umi-finray-2mm.exploded.card.webp").read_bytes()
            (library / card).write_bytes(data)
            document = _json(library / SHOWCASE_FILE)
            document["image"]["card"].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            (library / SHOWCASE_FILE).write_text(library_write.showcase_text(document), encoding="utf-8")

        self.assertEqual(self.problems(files=other), [f"{card} is not a 800 x 1000 WebP with alpha: {self.RESHOOT}"])
        self.assertEqual(self.problems(files=lambda library: (library / "showcase" / "old.webp").write_bytes(b"x")), [f"showcase/old.webp: not a picture of {name}"])

    def test_its_pictures_go_stale_with_what_they_were_shot_from(self) -> None:
        name = SHOWCASE_FILE

        def stale(what: str, key: str) -> list:
            return [f"{name}: its pictures are of another {what} than the files now ({key}): {self.RESHOOT}"]

        self.assertEqual(stale("scene or rules", "scene_sha256"), [ShowcaseTests.STALE])
        self.assertEqual(self.problems(lambda d: d["shot"].update(scene_sha256="0" * 64)), stale("scene or rules", "scene_sha256"))
        self.assertEqual(self.problems(lambda d: d["shot"].update(art_sha256="0" * 64)), stale("art", "art_sha256"))
        self.assertEqual(self.problems(lambda d: d["shot"].update(placed_sha256="0" * 64)), stale("placed record", "placed_sha256"))
        self.assertEqual(self.problems(lambda d: d["shot"].pop("numbers")),
                         [f"{name}: its shot is not {{{', '.join(library_write.SHOWCASE_SHOT_KEYS)}}}: {self.RESHOOT}"])
        # The scene itself changed (a look), or the rules every scene is drawn by.
        self.assertEqual(self.problems(files=lambda library: _edit_scene(library, "flexitac-g1", lambda scene: scene["looks"]["umi-tpu-orange"].update(roughness=0.5))),
                         stale("scene or rules", "scene_sha256"))

        def ruled(library: Path) -> None:
            index = _json(library / library_write.SCENES_INDEX)
            index["rules"]["gap_share"] = 0.4
            _write_json(library / library_write.SCENES_INDEX, index)

        self.assertEqual(self.problems(files=ruled), stale("scene or rules", "scene_sha256"))
        # Older figure or view sources: still shown, a warning (the public CI runs no browser), as a sensor's pictures.
        self.assertFalse(self.problems(older=True))
        self.assertEqual(self.problems(lambda d: d["shot"].update(view_sha256="0" * 64)), [])
        self.assertTrue(self.problems(lambda d: d["shot"].update(view_sha256="0" * 64), older=True))
        self.assertTrue(self.problems(lambda d: d["shot"].update(figure_sha256="0" * 64), older=True))

    def test_its_stage_numbers_hold_the_rules_and_its_own_bounds(self) -> None:
        # The stage's numbers recorded with the pictures (the review of 2026-11-12: no gate looked at them, so a scene or
        # a camera that hid the pad would pass): four held to the rules' checks as any gripper's, three to the
        # showcase's own bounds (its fingers solid, its tails behind its finger); the committed ones within all.
        name = SHOWCASE_FILE
        numbers = _json(LIBRARY / SHOWCASE_FILE)["shot"]["numbers"]
        rules = _json(LIBRARY / library_write.SCENES_INDEX)["rules"]
        self.assertEqual(library_write.showcase_numbers(numbers, rules), [])
        self.assertEqual([key for key, _ in library_write.SHOWCASE_RULED], ["visible_min", "clearance_mm", "stacks_apart_px", "card_px"])
        self.assertEqual(library_write.SHOWCASE_BOUNDS, (("assembled_opaque", "below", 0.25), ("opaque_max", "below", 0.75), ("near_seen", "at least", 0.25)))
        bounds = "(the scene or its camera hides the pad, or the bounds are no longer the showcase's: SHOWCASE_BOUNDS)"
        cases = (
            ({"visible_min": 0.2}, "the stage's visible_min is 0.2, not at least 0.25"),
            ({"clearance_mm": {"bodies": 2, "other_finger": 12, "stacks": 30.9}}, "the stage's clearance_mm is [2, 12, 30.9], not at least 3"),
            ({"stacks_apart_px": 19}, "the stage's stacks_apart_px is 19, not at least 20"),
            ({"card_px": [82, 19]}, "the stage's card_px is [82, 19], not at least 20"),
            ({"assembled_opaque": 0.25}, "the stage's assembled_opaque is 0.25, not below 0.25"),
            ({"opaque_max": 0.8}, "the stage's opaque_max is 0.8, not below 0.75"),
            ({"near_seen": 0.2}, "the stage's near_seen is 0.2, not at least 0.25"),
            ({"near_seen": None}, "the stage's near_seen is None, not at least 0.25"),
        )
        for change, problem in cases:
            with self.subTest(problem=problem):
                self.assertEqual(library_write.showcase_numbers(dict(numbers, **change), rules), [problem])
                self.assertEqual(self.problems(lambda d: d["shot"]["numbers"].update(change)), [f"{name}: {problem} {bounds}"])
        self.assertEqual(library_write.showcase_numbers(None, rules), ["the stage's numbers are missing"])
        # The rules' own numbers, not copies: a stricter rule refuses what the committed numbers are.
        self.assertEqual(library_write.showcase_numbers(numbers, dict(rules, checks=dict(rules["checks"], layer_visible_min=0.6))),
                         [f"the stage's visible_min is {numbers['visible_min']!r}, not at least 0.6"])
        # The shots tool writes nothing of a shoot whose numbers are not sound.
        source = (ROOT / "tools" / "browser" / "library_shots.py").read_text(encoding="utf-8")
        held = source.index('    unsound = library_write.showcase_numbers(drawn["numbers"], library_write.scenes_index(LIBRARY).get("rules"))\n'
                            '    if unsound:\n')
        self.assertLess(held, source.index("    fresh = dict(document, placed=placed, image=library_write.showcase_image(files),"))

    def test_the_writer_says_the_showcase_s_own_fixes(self) -> None:
        # tools/library_write.py run() on a copy of web/ (its fits read, none fitted: only=[]): current; a warning, not a
        # failure, for pictures of older figure or view sources (the review of 2026-11-12: no test held that line); and
        # a problem of the showcase alone closed by the showcase's own fixes, not the private scene builder's (that
        # review: a changed card picture ended with "rebuild the scenes with the private tools/library_scenes.py").
        reshoot = "re-shoot with tools/browser/library_shots.py --showcase"
        with tempfile.TemporaryDirectory() as folder:
            web = Path(folder) / "web"
            for relative in ("library", "vendor", "samples"):
                shutil.copytree(WEB / relative, web / relative)
            library = web / "library"
            done = "library_write: 58 sensors, all current, each with its picture, 58 with a 3D view"

            def run(check: bool = True):
                said = []
                return library_write.run(only=[], check=check, library=library, out=said.append), said

            self.assertEqual(run(), (0, [done]))
            path = library / SHOWCASE_FILE
            kept = path.read_text(encoding="utf-8")
            document = json.loads(kept)
            document["shot"]["view_sha256"] = "0" * 64
            path.write_text(library_write.showcase_text(document), encoding="utf-8")
            self.assertEqual(run(), (0, [f"library_write: warning: the showcase's pictures are of older figure or view sources: {reshoot}", done]))
            path.write_text(kept, encoding="utf-8")
            card = library / SHOWCASE_PICTURES[2]
            picture = card.read_bytes()
            card.write_bytes(picture + b"\0")
            self.assertEqual(run(), (1, [f"stale: scene {SHOWCASE_PICTURES[2]} is not the file {SHOWCASE_FILE} names: {reshoot}",
                                         f"library_write: {library_write.SHOWCASE_STALE}"]))
            self.assertEqual(run(check=False)[1], [f"library_write: scene {SHOWCASE_PICTURES[2]} is not the file {SHOWCASE_FILE} names: {reshoot}",
                                                   "library_write: 0 fitted, 0 written, 58 sensors, 58 with a 3D view"])
            card.write_bytes(picture)
            # A file no tool writes (here a copy of a vendor mesh in the samples) says its own fix, its removal, and no
            # closing line of a rebuild or a shoot (the review of 2026-11-13: it said to rebuild the showcase).
            copy = web / "samples" / "frame.stl"
            shutil.copyfile(web / "vendor" / "ufactory-g1" / "body_frame.stl", copy)
            self.assertEqual(run(), (1, ["stale: scene web/samples/frame.stl is a copy of web/vendor/ufactory-g1/body_frame.stl: "
                                         "the vendor's 3D model is shown in web/vendor/ufactory-g1/ alone: remove it"]))
            copy.unlink()
            # A gripper's scene's problem is the scene builder's, and of the two closing lines only that one is said (its
            # pictures and entries.json are stale with it, each with a line of its own).
            _edit_scene(library, "widowx-250", lambda scene: scene["bodies"][0].update(sha256="0" * 64))
            code, said = run()
            self.assertEqual(code, 1)
            self.assertIn(f"library_write: the library's scenes are stale: {library_write.REBUILD}", said)
            self.assertNotIn(f"library_write: {library_write.SHOWCASE_STALE}", said)

    def test_every_gate_takes_it_in(self) -> None:
        # showcase() carries the page's problems, so scenes(), library_write --check and the site build stop on them,
        # each with its own fix (the scene's with the scene builder's).
        with tempfile.TemporaryDirectory() as folder:
            library = _showcase_web(Path(folder))
            self.assertEqual(library_write.scenes(self.parts, library)[1], [])
            (library / SHOWCASE_FILE).unlink()
            missing = f"{SHOWCASE_FILE} is missing or not JSON: write it (docs/LIBRARY_VIEW.md), then {self.RESHOOT}"
            self.assertEqual(library_write.showcase(self.parts, library)[0], [missing])
            self.assertEqual(library_write.scenes(self.parts, library)[1], [(None, missing)])
        with tempfile.TemporaryDirectory() as folder:
            library = _showcase_web(Path(folder))
            _edit_scene(library, "flexitac-g1", lambda scene: scene["looks"]["umi-tpu-orange"].update(roughness=0.5))
            self.assertEqual(library_write.scenes(self.parts, library)[1], [(None, ShowcaseTests.STALE)])
            self.assertEqual(library_write.showcase(self.parts, library)[0], [ShowcaseTests.STALE])
        # A library without the showcase (the tests' tiny ones) has no page to check.
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(library_write.showcase(self.parts, _scene_library(Path(folder) / "library", self.parts)), ([], set()))


class ViewTests(LibraryTestCase):
    """Each sensor's 3D view in entries.json (library_write.pictures(): its record's art and a gripper's stage, the user's
    request of 2026-11-05, docs/LIBRARY_VIEW.md), on tiny scenes and art built here (no browser)."""

    GRIPPER, FINGERTIP = "widowx-250-2mm", "umi-finray-2mm"

    def pictures(self, require_view=False, **options) -> tuple:
        with tempfile.TemporaryDirectory() as folder:
            library = _view_library(Path(folder), self.entries["variants"], self.parts, **options)
            return library_write.pictures(self.entries["variants"], library, view=VIEW, require_view=require_view)

    def refused(self, identifier: str, problem: str, require_view=False, **options) -> None:
        """The sensor's record refused with ``problem`` alone: no image and no view."""

        images, problems, _, views = self.pictures(require_view, **options)
        self.assertEqual(problems, [(identifier, f"{identifier}: {problem}")])
        self.assertEqual((images[identifier], views[identifier]), (None, None))

    def test_a_current_record_has_its_view_and_its_words(self) -> None:
        images, problems, older, views = self.pictures(require_view=True)
        self.assertEqual((problems, older), ([], []))
        self.assertEqual(views[self.GRIPPER], {"art": "art/widowx-250-2mm.json.gz", "scene": "scenes/widowx-250.json"})
        self.assertEqual(views[self.FINGERTIP], {"art": "art/umi-finray-2mm.json.gz", "scene": None})
        self.assertEqual(library_write.view_record(self.GRIPPER, "scenes/widowx-250.json"), views[self.GRIPPER])
        # The whole gripper's picture says so; the fingertip's is "on the part" as before.
        self.assertEqual(images[self.GRIPPER], dict(IMAGE_OF_WIDOWX, alt="WidowX 250, 2 mm on both fingers of the open gripper"))
        self.assertEqual(images[self.FINGERTIP]["alt"], "UMI Fin-Ray Gripper, 2 mm on the part")
        self.assertEqual(library_write.image_record(self.GRIPPER, "WidowX 250, 2 mm", PICTURE)["alt"], "WidowX 250, 2 mm on both fingers of the open gripper")
        self.assertEqual(library_write.image_record(self.GRIPPER, "WidowX 250, 2 mm"), IMAGE_OF_WIDOWX)
        self.assertEqual([identifier for identifier, view in views.items() if view], sorted([self.FINGERTIP, self.GRIPPER]))

    def test_the_writer_writes_each_view(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            library = Path(folder) / "library"
            shutil.copytree(LIBRARY / "meshes", library / "meshes")
            shutil.copytree(WEB / "vendor" / "umi", Path(folder) / "vendor" / "umi")
            _view_library(library, self.entries["variants"], self.parts)
            with mock.patch.object(library_write, "view_sha256", return_value=VIEW):
                document = library_write.entries(self.parts, self.fits, library)
            self.assertEqual({key: item["view"] for key, item in document["variants"].items() if item["view"]},
                             {self.GRIPPER: {"art": "art/widowx-250-2mm.json.gz", "scene": "scenes/widowx-250.json"},
                              self.FINGERTIP: {"art": "art/umi-finray-2mm.json.gz", "scene": None}})
            self.assertEqual(document["variants"][self.GRIPPER]["image"]["alt"], "WidowX 250, 2 mm on both fingers of the open gripper")
            # The art as the shots tool writes it: its document's canonical JSON, gzip at level 9 with no name and time 0.
            data = (library / "art" / "widowx-250-2mm.json.gz").read_bytes()
            self.assertEqual((data[:4], data[4:8], data[9], library_write.read_art(data)["id"]), (b"\x1f\x8b\x08\x00", bytes(4), 3, self.GRIPPER))
            self.assertEqual(library_write.art_bytes(library_write.read_art(data)), data)

    def test_the_transition_both_ways(self) -> None:
        # Before the shoot (VIEW_REQUIRED false) a record without its art, or a gripper's without its stage, is pictured
        # with no 3D view (its view null, a warning); after it, each is refused.
        for require_view in (False, True):
            with self.subTest(require_view=require_view):
                images, problems, _, views = self.pictures(require_view, art=False)
                self.assertEqual(views, {identifier: None for identifier in self.entries["variants"]})
                if require_view:
                    fix = "re-shoot with tools/browser/library_shots.py --only"
                    self.assertEqual(problems, [(self.FINGERTIP, f"{self.FINGERTIP}: no 3D view: its record names no art: {fix} {self.FINGERTIP}"),
                                                (self.GRIPPER, f"{self.GRIPPER}: no 3D view: its record names no art: {fix} {self.GRIPPER}")])
                    self.assertEqual((images[self.GRIPPER], images[self.FINGERTIP]), (None, None))
                else:
                    self.assertEqual(problems, [])
                    # The whole gripper pictured (its stage), its view only waiting for its art.
                    self.assertEqual(images[self.GRIPPER]["alt"], "WidowX 250, 2 mm on both fingers of the open gripper")
                images, problems, _, views = self.pictures(require_view, stage=False)
                self.assertEqual((views[self.GRIPPER], views[self.FINGERTIP]), (None, {"art": "art/umi-finray-2mm.json.gz", "scene": None}))
                if require_view:
                    self.assertEqual(problems, [(self.GRIPPER, f"{self.GRIPPER}: no 3D view of the whole gripper: its record has no stage "
                                                               f"(scenes/widowx-250.json): re-shoot with tools/browser/library_shots.py --only {self.GRIPPER}")])
                else:
                    self.assertEqual((problems, images[self.GRIPPER]), ([], IMAGE_OF_WIDOWX))
        self.assertIs(library_write.VIEW_REQUIRED, True, "since the shoot of 2026-11-06 that wrote every sensor's art and stage")
        self.assertEqual(library_write.view_note(["a-1mm", "b-2mm"]), "the pictures of a-1mm, b-2mm have no 3D view (their records name no art, "
                         "or a gripper's no stage): re-shoot with tools/browser/library_shots.py, then run tools/library_write.py")

    def test_an_art_of_another_sensor_or_build_is_refused(self) -> None:
        fix = f"re-shoot with tools/browser/library_shots.py --only {self.GRIPPER}"
        problem = f"its art is of another sensor or build than its fit's (the wrong boards drawn): {fix}"
        other = "surface-13x13-000000000000"

        def redraw(**changes):
            def edit(records, library):
                data = library_write.art_bytes(dict(_art(self.GRIPPER, self.entries["variants"][self.GRIPPER]["build_id"]), **changes))
                (library / library_write.art_path(self.GRIPPER)).write_bytes(data)
                records[self.GRIPPER]["art"] = library_write.art_record(self.GRIPPER, data, self.entries["variants"][self.GRIPPER]["build_id"])
            return edit

        # The art drawn from another build (its record the variant's), of another sensor, or recorded as another build.
        self.refused(self.GRIPPER, problem, edit=redraw(build_id=other))
        self.refused(self.GRIPPER, problem, edit=redraw(id="widowx-250-1mm"))
        self.refused(self.GRIPPER, problem, edit=lambda records, library: records[self.GRIPPER]["art"].update(build_id=other))
        self.refused(self.GRIPPER, f"art/widowx-250-2mm.json.gz is drawn at 10 px per mm and 4096 px at most, not the figure's 12 and 4096: {fix}",
                     edit=redraw(px_per_mm=10))
        self.refused(self.GRIPPER, f"art/widowx-250-2mm.json.gz has not the two boards' art with their outlines: {fix}",
                     edit=redraw(boards={"row": _art(self.GRIPPER, "x")["boards"]["row"]}))
        self.refused(self.GRIPPER, f"art/widowx-250-2mm.json.gz is not a flexitac-library-art/v1 document: {fix}", edit=redraw(format="x"))

    def test_an_art_not_the_records_bytes_is_refused(self) -> None:
        relative = "art/widowx-250-2mm.json.gz"
        fix = f"re-shoot with tools/browser/library_shots.py --only {self.GRIPPER}"

        def rewrite(data_of):
            return lambda records, library: (library / relative).write_bytes(data_of(library / relative))

        # The same document gzipped otherwise (another time stamp): not the bytes the record names.
        self.refused(self.GRIPPER, f"{relative} is not the file shots/manifest.json names: {fix}",
                     edit=rewrite(lambda path: gzip.compress(gzip.decompress(path.read_bytes()), compresslevel=9, mtime=1)))
        self.refused(self.GRIPPER, f"{relative} is missing: {fix}", edit=lambda records, library: (library / relative).unlink())

        def recorded(data: bytes):
            def edit(records, library):
                (library / relative).write_bytes(data)
                records[self.GRIPPER]["art"].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            return edit

        self.refused(self.GRIPPER, f"{relative} is not a gzip of a JSON document: {fix}", edit=recorded(b"not gzip"))
        self.refused(self.GRIPPER, f"{relative} is not a gzip of a JSON document: {fix}", edit=recorded(gzip.compress(b"{x", mtime=0)))
        self.refused(self.GRIPPER, f"{relative} is not a gzip of a JSON document: {fix}", edit=recorded(gzip.compress(b"{}", mtime=0)[:-6]))
        self.refused(self.GRIPPER, f"{relative}'s document is not the one shots/manifest.json names: {fix}",
                     edit=recorded(library_write.art_bytes(_art(self.GRIPPER, self.entries["variants"][self.GRIPPER]["build_id"], look="flat"))))
        self.refused(self.GRIPPER, f"its art is not {relative}: {fix}", edit=lambda records, library: records[self.GRIPPER]["art"].update(path="art/x.json.gz"))
        # An art of no record: a stray file.
        images, problems, _, views = self.pictures(edit=lambda records, library: (library / "art" / "old.json.gz").write_bytes(b""))
        self.assertEqual(problems, [(None, "art/old.json.gz: not an art of shots/manifest.json: re-shoot with tools/browser/library_shots.py")])

    def test_a_stage_of_another_scene_or_rules_is_refused(self) -> None:
        fix = f"re-shoot with tools/browser/library_shots.py --only {self.GRIPPER}"
        problem = f"its stage is of another scene or other rules than scenes/widowx-250.json and scenes/scenes.json's now: {fix}"
        # The scene rebuilt since the shot (another opening), and the rules changed since (the see-through's opacity):
        # either is hashed into the record.
        self.refused(self.GRIPPER, problem, edit=lambda records, library: _edit_scene(library, "widowx-250", lambda scene: scene["opening"].update(q_mm=36)))

        def ruled(records, library):
            index = _json(library / library_write.SCENES_INDEX)
            index["rules"]["ghost_opacity"] = 0.3
            _write_json(library / library_write.SCENES_INDEX, index)

        self.refused(self.GRIPPER, problem, edit=ruled)
        self.assertNotEqual(library_write.scene_sha256(b"{}", APPROVED_RULES), library_write.scene_sha256(b"{}", dict(APPROVED_RULES, ghost_opacity=0.3)))
        self.assertNotEqual(library_write.scene_sha256(b"{}", APPROVED_RULES), library_write.scene_sha256(b"{ }", APPROVED_RULES))
        self.refused(self.GRIPPER, f"its stage is not of its part's scene scenes/widowx-250.json: {fix}",
                     edit=lambda records, library: records[self.GRIPPER]["stage"].update(scene="scenes/arx-x5.json"))

    def test_a_stage_for_a_fingertip_is_refused(self) -> None:
        # The UMI finger and its tips keep the fingertip scene: a stage in their record is not theirs.
        def staged(records, library):
            records[self.FINGERTIP]["stage"] = dict(records[self.GRIPPER]["stage"])

        self.refused(self.FINGERTIP, "its record has a stage, but its part umi-finray keeps the fingertip scene (no scene in scenes/scenes.json): "
                                     f"re-shoot with tools/browser/library_shots.py --only {self.FINGERTIP}", edit=staged)

    def test_numbers_breaking_a_rule_are_refused(self) -> None:
        checks = APPROVED_RULES["checks"]
        self.assertEqual(library_write.stage_problems(NUMBERS, checks, ["mate"]), [])
        cases = (
            ({"visible_min": 0.2}, "visible_min 0.2 breaks the rule layer_visible_min: not >= 0.25"),
            ({"opaque_max": 0.1}, "opaque_max 0.1 breaks the rule opaque_cover_max: not < 0.1"),
            ({"assembled_opaque": 0.2}, "assembled_opaque 0.2 breaks the rule opaque_cover_max: not < 0.1"),
            ({"clearance_mm": {"bodies": 2.9, "other_finger": 12, "stacks": 30}}, "clearance_mm.bodies 2.9 breaks the rule clearance_min_mm: not >= 3"),
            ({"clearance_mm": {"bodies": 12, "other_finger": 1, "stacks": 30}}, "clearance_mm.other_finger 1 breaks the rule clearance_min_mm: not >= 3"),
            ({"clearance_mm": {"bodies": 12, "other_finger": 12, "stacks": 15}}, "clearance_mm.stacks 15 breaks the rule stacks_apart_min_g x jaw_gap_mm: not >= 16.0"),
            # A small gap, where the floor in mm binds (0.20 x 10 = 2 holds there).
            ({"jaw_gap_mm": 10, "clearance_mm": {"bodies": 12, "other_finger": 12, "stacks": 2.9}}, "clearance_mm.stacks 2.9 breaks the rule stacks_apart_min_mm: not >= 3"),
            ({"stacks_apart_px": 19}, "stacks_apart_px 19 breaks the rule stacks_apart_min_px: not >= 20"),
            ({"stacks_apart_px": None}, "stacks_apart_px (None) or its rule stacks_apart_min_px (20) is not a number"),
            ({"near_seen": 0.4}, "near_seen 0.4 breaks the rule near_seen_min: not >= 0.5"),
            ({"near_seen": None}, "near_seen (None) or its rule near_seen_min (0.5) is not a number"),
            ({"card_px": [19, 40]}, "card_px 19 breaks the rule card_min_px: not >= 20"),
            ({"ghost_cover": 0.01}, "ghost_cover 0.01 breaks the rule ghost_cover_min: not >= 0.02"),
            ({"ghost_cover": None}, "ghost_cover (None) or its rule ghost_cover_min (0.02) is not a number"),
            ({"jaw_gap_mm": 0, "clearance_mm": {"bodies": 12, "other_finger": 12, "stacks": 3}}, "jaw_gap_mm (0) is not a positive number"),
        )
        for change, problem in cases:
            with self.subTest(problem=problem):
                self.assertEqual(library_write.stage_problems(dict(NUMBERS, **change), checks, ["mate"]), [problem])
        self.assertEqual(library_write.stage_problems(NUMBERS, checks, []), ["ghost_cover is 0.1, with no see-through finger in its scene"])
        self.assertEqual(library_write.stage_problems(dict(NUMBERS, ghost_cover=None), checks, []), [])
        self.assertEqual(library_write.stage_problems({"jaw_gap_mm": 80}, checks, []), [f"its stage's numbers are not {', '.join(library_write.STAGE_NUMBERS)}"])
        # near_seen, the near stack's, is null exactly when the mate's stack explodes too (explode_stacks): a number
        # there is refused, and a null with the sensor's stack alone exploding.
        both = ("sensor", "mate")
        self.assertEqual(library_write.stage_problems(dict(NUMBERS, near_seen=None), checks, ["mate"], both), [])
        self.assertEqual(library_write.stage_problems(NUMBERS, checks, ["mate"], both), ["near_seen is 1.0, with the mate's stack exploding"])
        self.assertEqual(library_write.stage_problems(dict(NUMBERS, near_seen=None), checks, ["mate"], ("sensor",)),
                         ["near_seen (None) or its rule near_seen_min (0.5) is not a number"])
        self.assertEqual(library_write.stage_problems(NUMBERS, checks, ["mate"], ("sensor",)), [])
        # In a record: refused, each rule named.
        fix = f"re-shoot with tools/browser/library_shots.py --only {self.GRIPPER}"
        self.refused(self.GRIPPER, f"its stage breaks a rule of scenes/scenes.json: visible_min 0.2 breaks the rule layer_visible_min: not >= 0.25: {fix}",
                     edit=lambda records, library: records[self.GRIPPER]["stage"]["numbers"].update(visible_min=0.2))
        # The rules' explode_stacks reach the record's check (staging): with both stacks exploding, a near_seen is refused.
        def both_exploding(records, library):
            index = _json(library / library_write.SCENES_INDEX)
            index["rules"]["explode_stacks"] = ["sensor", "mate"]
            _write_json(library / library_write.SCENES_INDEX, index)
            records[self.GRIPPER]["stage"]["scene_sha256"] = library_write.scene_sha256((library / "scenes" / "widowx-250.json").read_bytes(), index["rules"])

        self.refused(self.GRIPPER, f"its stage breaks a rule of scenes/scenes.json: near_seen is 1.0, with the mate's stack exploding: {fix}",
                     edit=both_exploding)

    def test_an_older_view_is_a_warning_only(self) -> None:
        # The Library view's modules changed since the shot (view_sha256): still pictured, its view kept, a warning.
        images, problems, older, views = self.pictures(edit=lambda records, library: records[self.GRIPPER].update(view_sha256="0" * 64))
        self.assertEqual((problems, older), ([], [self.GRIPPER]))
        self.assertEqual(views[self.GRIPPER], {"art": "art/widowx-250-2mm.json.gz", "scene": "scenes/widowx-250.json"})
        self.assertIsNotNone(images[self.GRIPPER])
        # The hash follows each of the view's modules (as the figure's).
        sources = {path: path.encode("ascii") for path in library_write.VIEW_SOURCES}
        for path in sources:
            with self.subTest(changed=path):
                self.assertNotEqual(library_write.view_sha256(dict(sources, **{path: b"x"})), library_write.view_sha256(sources))
        self.assertEqual(library_write.VIEW_SOURCES, ("cad/library_view.js", "cad/library_stage.js", "cad/stl.js"))

    def test_a_fingertip_s_pictures_follow_the_rules_look_of_its_part(self) -> None:
        # A part without a scene whose look scenes.json's rules give (part_looks; docs/LIBRARY_VIEW.md "The looks"): its
        # record keeps the look's hash (the shots tool's part_look_sha256), so pictures of another look, of none where
        # one is given, or of one where none is given are refused; a gripper's record never has it.  The committed rules
        # give the UMI finger its orange: the fixture's record (_shot_library) is of it.
        orange = {"color": "#e85a1c", "metalness": 0, "roughness": 0.85, "env_intensity": 0.3}
        fix = f"re-shoot with tools/browser/library_shots.py --only {self.FINGERTIP}"
        stale = f"its pictures are of another look of its part than scenes/scenes.json's rules give now (part_looks): {fix}"
        of = lambda look: library_write.part_look_sha256({"look": look, "smooth_deg": None})  # noqa: E731

        def looked(rule_look, record_look):
            def change(records, library):
                index = _json(library / library_write.SCENES_INDEX)
                for key in library_write.RULES_OPTIONAL:
                    index["rules"].pop(key, None)
                if rule_look is not None:
                    index["rules"]["part_looks"] = {"umi-finray": rule_look}
                _write_json(library / library_write.SCENES_INDEX, index)
                records[self.GRIPPER]["stage"]["scene_sha256"] = library_write.scene_sha256((library / "scenes" / "widowx-250.json").read_bytes(), index["rules"])
                records[self.FINGERTIP].pop("part_look_sha256", None)
                if record_look is not None:
                    records[self.FINGERTIP]["part_look_sha256"] = of(record_look)
            return change

        index = _json(LIBRARY / library_write.SCENES_INDEX)
        images, problems, _, views = self.pictures(require_view=True, edit=lambda records, library: self.assertEqual(
            (records[self.FINGERTIP]["part_look_sha256"], "part_look_sha256" in records[self.GRIPPER]),
            (library_write.part_look_sha256(library_write.part_look(index, self.parts, "umi-finray")), False)))
        self.assertEqual(problems, [])
        pad = index["rules"]["part_pad"]
        self.assertEqual(library_write.part_look_sha256(library_write.part_look(index, self.parts, "umi-finray")),
                         library_write.part_look_sha256({"look": orange, "smooth_deg": None, "pad": pad}))
        # The pad's tint is of the look's record too (the user's decision of 2026-11-14): a record of the look without it
        # is stale where the rules give one.
        self.refused(self.FINGERTIP, stale, edit=lambda records, library: records[self.FINGERTIP].update(part_look_sha256=of(orange)))
        images, problems, _, views = self.pictures(require_view=True, edit=looked(dict(orange, color="#102030"), dict(orange, color="#102030")))
        self.assertEqual(problems, [], "a look given in place, the record of it")
        self.assertEqual(views[self.FINGERTIP], {"art": "art/umi-finray-2mm.json.gz", "scene": None})
        self.assertEqual(self.pictures(require_view=True, edit=looked(None, None))[1], [], "no look: no hash")
        self.refused(self.FINGERTIP, stale, edit=looked(orange, None))
        self.refused(self.FINGERTIP, stale, edit=looked(None, orange))
        self.refused(self.FINGERTIP, stale, edit=looked(orange, dict(orange, roughness=0.5)))
        self.refused(self.FINGERTIP, stale, edit=lambda records, library: records[self.FINGERTIP].pop("part_look_sha256"))
        self.refused(self.FINGERTIP, stale, edit=lambda records, library: records[self.FINGERTIP].update(part_look_sha256="0" * 64))
        self.refused(self.GRIPPER, stale.replace(self.FINGERTIP, self.GRIPPER), edit=lambda records, library: records[self.GRIPPER].update(part_look_sha256="0" * 64))
        # The shots tool writes the key only with a look.
        record = SHOTS_TOOL.record(self.FINGERTIP, self.entries["variants"][self.FINGERTIP], {}, {}, "f" * 64, "photo")
        self.assertNotIn("part_look_sha256", record)
        self.assertEqual(SHOTS_TOOL.record(self.FINGERTIP, self.entries["variants"][self.FINGERTIP], {}, {}, "f" * 64, "photo", part_look="a" * 64)["part_look_sha256"], "a" * 64)


class RequestTests(LibraryTestCase):
    def test_every_fit_is_of_the_request_the_page_sends(self) -> None:
        options = library_write.page_options((WEB / "gen.html").read_text(encoding="utf-8"))
        rows = {identifier: (part, variant) for identifier, _, part, variant in self.plan}
        for identifier, data in self.fits.items():
            part, variant = rows[identifier]
            document = json.loads(data.decode("utf-8"))
            request = document["request"]
            with self.subTest(variant=identifier):
                self.assertEqual(_canonical(request), _canonical(library_write.compose(part, variant, options)))
                self.assertEqual(request["name"], part["mesh"]["name"])
                self.assertNotIn("unit", request)
                self.assertEqual((request["options"]["max_rows"], request["options"]["max_columns"]), (32, 32))
                self.assertEqual((request["options"]["pitch_mm"], request["options"]["fill"]), (variant["pitch_mm"], variant["fill"]))
                self.assertEqual(document["mesh_sha256"], part["mesh"]["sha256"])
                # Numbers as the browser writes them: no integral float (2.0) anywhere in the request.
                stack = [request]
                while stack:
                    value = stack.pop()
                    if isinstance(value, dict):
                        stack += value.values()
                    elif isinstance(value, list):
                        stack += value
                    else:
                        self.assertFalse(isinstance(value, float) and value.is_integer(), value)
                if variant.get("fit"):
                    continue
                self.assertEqual(data, library_write.fit_document(request, part["mesh"]["sha256"], document["reply"]),
                                 "a fit file in the writer's compact form")

    def test_the_umi_fingers_2_mm_sensor_is_the_pages_default_fit(self) -> None:
        shipped = _json(WEB / "vendor" / "umi" / "default-fit.json")
        part = self.parts["parts"]["umi-finray"]
        (variant,) = [variant for variant in part["variants"] if variant["pitch_mm"] == 2]
        self.assertEqual(variant["fit"], "../vendor/umi/default-fit.json")
        self.assertEqual(self.entries["variants"]["umi-finray-2mm"]["fit"], "../vendor/umi/default-fit.json")
        options = library_write.page_options((WEB / "gen.html").read_text(encoding="utf-8"))
        # The request the browser recorded (tools/browser/write_default_fit.py) is the one composed here.
        self.assertEqual(_canonical(library_write.compose(part, variant, options)), _canonical(shipped["request"]))
        self.assertEqual(part["mesh"]["file"], "../vendor/umi/UMI-Soft-Gripper-Finger.stl")

    def test_the_options_are_the_pages_enabled_controls_at_their_defaults(self) -> None:
        controls = _controls()
        main = (WEB / "cad" / "main.js").read_text(encoding="utf-8")
        # syncObjective: under Resolution (pitch), the default objective, Smallest pitch is disabled (sends nothing).
        self.assertIn('$("cadMinPitch").disabled = fixed;', main)
        objective = controls["objective"]
        self.assertEqual([option.get("value") for option in objective[2]][0], "fixed_pitch")
        self.assertFalse(any("selected" in option for option in objective[2]))
        enabled = set(controls) - {"min_pitch_mm"}
        for identifier, _, part, variant in self.plan:
            request = json.loads(self.fits[identifier].decode("utf-8"))["request"]
            options = request["options"]
            with self.subTest(variant=identifier):
                self.assertEqual(set(options), enabled)
                own = part["setup"]["options"]
                self.assertTrue(set(own) <= {"rotation"}, own)
                for key, value in options.items():
                    tag, attributes, choices = controls[key]
                    if key in ("pitch_mm", "fill"):
                        expected = variant[key]
                    elif key in own:
                        expected = own[key]
                    elif tag == "select":
                        expected = [choice.get("value") for choice in choices if "disabled" not in choice][0]
                    else:
                        expected = float(attributes["value"])
                    self.assertEqual(value, expected, key)
                    if tag == "select":
                        self.assertIn(value, [choice.get("value") for choice in choices if "disabled" not in choice], key)
                        continue
                    # The control takes the value: min <= value <= max, a whole number of steps from min (in decimal,
                    # as the browser checks it: (0.7 - 0.05) / 0.01 is not 65 in binary floating point).
                    number, low, high, step = (Decimal(str(value)), Decimal(attributes["min"]), Decimal(attributes["max"]),
                                               Decimal(attributes["step"]))
                    self.assertTrue(low <= number <= high, (key, value))
                    self.assertEqual((number - low) % step, 0, (key, value))
                    self.assertTrue(library_write.valid({"min": attributes["min"], "max": attributes["max"], "step": attributes["step"]}, value))

    def test_the_writer_reads_the_controls_as_the_browser_does(self) -> None:
        found = library_write.controls((WEB / "gen.html").read_text(encoding="utf-8"))
        self.assertEqual(set(found), set(_controls()))
        self.assertEqual(found["row_sides"]["choices"], ["both", "left", "right"], "the disabled 'channel' is never sent")
        self.assertEqual((found["pitch_mm"]["default"], found["max_rows"]["default"], found["strain_limit"]["default"]), (2, 32, 0.003))
        for key, value, expected in (("fill", 0.7, True), ("fill", 0.65, True), ("fill", 0.95, True), ("fill", 0.705, False),
                                     ("fill", 0.04, False), ("fill", 0.96, False), ("pitch_mm", 2.5, True), ("pitch_mm", 0.59, False)):
            with self.subTest(option=key, value=value):
                self.assertEqual(library_write.valid(found[key], value), expected)
        self.assertEqual([library_write.js_string(pitch) for pitch in (1, 1.0, 1.5, 2.5)], ["1", "1", "1.5", "2.5"])

    def test_a_control_disabled_in_the_page_is_not_sent(self) -> None:
        # readOptions skips a disabled control; Pitch, Smallest pitch and Row traces are main.js's own to turn on and
        # off (syncObjective, syncContainment), whatever gen.html says (the review of 2026-11-05).
        html = (WEB / "gen.html").read_text(encoding="utf-8")
        self.assertFalse(any(control["disabled"] for control in library_write.controls(html).values()))
        for key, element in (("edge_margin_mm", 'id="cadEdgeMargin"'), ("pitch_mm", 'id="cadPitch"'), ("row_sides", 'id="cadRowSides"')):
            with self.subTest(option=key):
                self.assertEqual(html.count(element), 1)
                options = library_write.page_options(html.replace(element, f"{element} disabled", 1))
                self.assertEqual(key in options, key in library_write.SYNCED)

    def test_compose_refuses_what_the_page_would_send_otherwise(self) -> None:
        # parts.json is edited by hand: a setup main.js buildDefaultSensor would send another way is refused, not
        # composed (only the browser checks would see it: the writer, the tests and the site build would agree).
        options = library_write.page_options((WEB / "gen.html").read_text(encoding="utf-8"))
        part = self.parts["parts"]["widowx-250"]
        variant = part["variants"][0]
        for identifier, _, each, _ in self.plan:
            base = each["setup"]["base"]
            if isinstance(base, dict):
                with self.subTest(variant=identifier):
                    # choosePoint's round6 keeps every committed base point as written.
                    self.assertEqual([library_write.round6(value) for value in base["point_xyz"]], base["point_xyz"])
        self.assertEqual([library_write.round6(value) for value in (0.0000005, -0.0000005, 1.23456749, 2.5e-7)], [0.000001, 0.0, 1.234567, 0.0])
        point = list(part["setup"]["base"]["point_xyz"])
        cases = {
            "seven decimals": {"base": {"point_xyz": [point[0] + 1e-7, point[1], point[2]]}},
            "a side": {"base": {"side": 0}},
            "a point with a border": {"border": {"uv": [[0, 0], [1, 0], [1, 1], [0, 1]]}},
            "another objective": {"options": {**part["setup"]["options"], "objective": "max_taxels"}},
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                changed = copy.deepcopy(part)
                changed["setup"].update(change)
                with self.assertRaises(library_write.LibraryError):
                    library_write.compose(changed, variant, options)
        # Under Whole board the page disables Row traces: no row_sides is sent.
        board = copy.deepcopy(part)
        board["setup"]["options"] = {**part["setup"]["options"], "containment": "board"}
        self.assertNotIn("row_sides", library_write.compose(board, variant, options)["options"])
        self.assertIn("row_sides", library_write.compose(part, variant, options)["options"])


class RuleTests(LibraryTestCase):
    def test_every_proposal_one_keeps_the_product_rules(self) -> None:
        from engine import generate_design

        for identifier, data in self.fits.items():
            reply = json.loads(data.decode("utf-8"))["reply"]
            first = reply["proposals"][0]
            metrics = first["metrics"]
            with self.subTest(variant=identifier):
                self.assertEqual(library_write.rules(reply, build=False), [])
                self.assertEqual(reply["request"]["options"]["reader"], "none")
                self.assertEqual(first["design"]["connector"], {"row_pins": None, "column_pins": None}, "one tail pin per line")
                self.assertEqual(metrics["containment"], "field")
                self.assertEqual(metrics["row_bus"]["tail_position"], "centred")
                self.assertEqual(metrics["row_tail_mm"], metrics["column_tail_mm"])
                symmetry = metrics.get("symmetry") or {}
                if symmetry.get("face"):
                    self.assertTrue(symmetry.get("field"))
                result = generate_design(first["design"])
                self.assertEqual((result["validation"]["errors"], result["validation"]["warnings"]), ([], []))
                self.assertEqual(result["manifest"]["build_id"], first["build_id"])
                entry = self.entries["variants"][identifier]
                self.assertEqual((entry["build_id"], entry["rows"], entry["columns"], entry["taxels"]),
                                 (first["build_id"], metrics["rows"], metrics["columns"], metrics["taxels"]))
                self.assertEqual(entry["centred"], bool(symmetry.get("field")))

    def test_rules_name_each_broken_rule(self) -> None:
        reply = json.loads(self.fits["widowx-250-2mm"].decode("utf-8"))["reply"]
        self.assertEqual(library_write.rules(reply), [])

        def broken(edit, build: bool) -> list:
            tampered = copy.deepcopy(reply)
            edit(tampered["proposals"][0])
            return library_write.rules(tampered, build=build)

        # Each edit breaks one rule; those of the design are checked without the build (which they change as well).
        cases = (
            ("reader none", lambda p: p["design"]["connector"].update(row_pins=16), False),
            ("field containment", lambda p: p["metrics"].update(containment="board"), True),
            ("centred tails", lambda p: p["metrics"]["row_bus"].update(tail_position="side"), True),
            ("tails ending together", lambda p: p["metrics"].update(row_tail_mm=p["metrics"]["row_tail_mm"] + 1), True),
            ("a symmetric face's sensor centred", lambda p: p["metrics"]["symmetry"].update(field=False), True),
            ("the same build", lambda p: p.update(build_id="surface-13x13-000000000000"), True),
            ("a clean build", lambda p: p["design"]["matrix"].update(taxel_width_mm=1.9, taxel_height_mm=1.9), True),
        )
        for rule, edit, build in cases:
            with self.subTest(rule=rule):
                messages = broken(edit, build)
                if rule == "a clean build":
                    messages = [message for message in messages if not message.startswith("the same build")]
                self.assertEqual(len(messages), 1, messages)
                self.assertTrue(messages[0].startswith(rule), messages)
        self.assertEqual(library_write.rules({"ok": True, "proposals": []}), ["a proposal: the fit has none"])
        # A sensor whose tails merely fit a reader (32 x 16: the FlexiTac's 32 and 16 pins) keeps reader none, the reader
        # recorded beside it.  No sensor of the Library has such tails since the default fill 0.5 (the user's decision of
        # 2026-11-06: the UMI finger's 1.5 mm sensor, 32 x 16 at fill 0.7, is 32 x 17), so a reply that says so stands in.
        fitting = copy.deepcopy(reply)
        fitting["proposals"][0]["metrics"]["reader"] = "32x16"
        self.assertEqual(library_write.rules(fitting, build=False), [])
        identifier, part_id, part, variant = next(row for row in self.plan if row[0] == "widowx-250-2mm")
        record = library_write.summary(part_id, part, variant, "fits/widowx-250-2mm.json", json.dumps({"reply": fitting}).encode("utf-8"))
        self.assertEqual((record["reader"], record["fits_reader"]), ("none", "32x16"))
        self.assertEqual({variant["fits_reader"] for variant in self.entries["variants"].values()}, {None})


class StalenessTests(LibraryTestCase):
    def test_each_parts_2_mm_sensor_is_the_engines(self) -> None:
        # A sample (about 6 s): each gripper's 2 mm sensor and the tapered tips' default; the site build and
        # tools/library_write.py --check fit every variant.
        rows = {identifier: (part, variant) for identifier, _, part, variant in self.plan}
        for identifier in self.entries["start"] + [self.entries["families"][TAPERS]["default"]]:
            part, variant = rows[identifier]
            document = json.loads(self.fits[identifier].decode("utf-8"))
            mesh = (LIBRARY / part["mesh"]["file"]).read_bytes()
            with self.subTest(variant=identifier):
                reply = library_write.fit(document["request"], mesh)
                self.assertEqual(reply, document["reply"], "the library is stale: run tools/library_write.py")


class FamilyTests(LibraryTestCase):
    """The tapered tips (the user's requests of 2026-11-05): since the user's request of 2026-11-16 ("我在这里更多想要体现
    umi不同shape我们都可以fit") the family's cards, one per shape, after the straight finger on the UMI finger's shelf."""

    def test_the_family_is_its_cards_each_complete(self) -> None:
        family = self.entries["families"][TAPERS]
        self.assertEqual(list(self.entries["families"]), [TAPERS])
        # The family's own address (#umi-tapers, ?part=umi-tapers) opens the 13.8 mm trapezoid, as before its cards.
        self.assertEqual((sorted(family), family["shelf"], family["default"]), (["cards", "default", "shelf"], "umi-finray", "umi-trap-tip13.8-2mm"))
        self.assertEqual([(card["key"], card["title"], card["default"]) for card in family["cards"]],
                         [(key, title, default) for key, title, _, default in TAPER_CARDS])
        shown = []
        for card, (key, title, kinds, default) in zip(family["cards"], TAPER_CARDS):
            with self.subTest(card=key):
                shape, tip = card["axes"]
                widths = TAPER_KINDS[kinds[0][0]][3]
                self.assertEqual((shape["key"], shape["label"], [(choice["value"], choice["label"]) for choice in shape["choices"]]),
                                 ("shape", "Shape", [(value, label) for _, value, label in kinds]))
                self.assertEqual((tip["key"], tip["label"], [choice["value"] for choice in tip["choices"]]), ("tip_mm", "Tip width (mm)", list(widths)))
                grid = {f"{value}|{width}": f"umi-{kind}-tip{width}-2mm" for kind, value, _ in kinds for width in widths}
                self.assertEqual(card["grid"], grid, "its shapes by its tip widths, each once")
                self.assertEqual(card["h_mm"], TAPER_KINDS[kinds[0][0]][2])
                self.assertIn(default, grid.values())
                shown += grid.values()
        # The cards' lines in the grippers' style: a range and what is picked on the card's page; one sensor its tip
        # and pitch.
        self.assertEqual([card["lines"] for card in family["cards"]],
                         [["5.8 to 21.8 mm", "Pick shape and width"]] + [["5.8 to 21.8 mm", "Pick your tip width"]] * 3 + [["2 mm tip", "2 mm pitch"]])
        # Every tip on one card once; every card's sensor a tip's.
        members = sorted(part_id for part_id, part in self.entries["parts"].items() if part["family"] == TAPERS)
        self.assertEqual(sorted(shown), sorted(f"{part_id}-2mm" for part_id in members))
        self.assertEqual(len(shown), 26)
        self.assertEqual(sorted(identifier for part in members for identifier in self.entries["parts"][part]["variants"]), sorted(shown))
        self.assertIn(family["default"], shown)
        self.assertEqual(family, library_write.family_record(TAPERS, self.parts["families"][TAPERS], self.parts, self.plan))
        for part_id in members:
            with self.subTest(part=part_id):
                self.assertNotIn(part_id, self.entries["order"], "no card or shelf of its own")
                self.assertNotIn(self.entries["parts"][part_id]["default"], self.entries["start"])
                self.assertEqual(self.entries["parts"][part_id]["title"], "UMI Fin-Ray Gripper, tapered tip")
                self.assertEqual(self.entries["variants"][f"{part_id}-2mm"]["pitch_mm"], 2)

    def test_an_incomplete_family_is_refused(self) -> None:
        def card(key):
            return lambda family: next(item for item in family["cards"] if item["key"] == key)
        for edit, message in ((lambda family: card("convex")(family)["grid"].pop("convex|5.8"), "every choice"),
                              (lambda family: card("short")(family)["grid"].update({"convex|13.8": "umi-trap-tip13.8-2mm"}), "cards and its parts"),
                              (lambda family: card("trap")(family).update(default="umi-convex-tip9.8-2mm"), "default"),
                              (lambda family: family.update(default="umi-finray-2mm"), "default"),
                              (lambda family: family.update(shelf="umi-trap-tip5.8"), "shelf"),
                              (lambda family: family["cards"].pop(), "cards and its parts"),
                              (lambda family: family["cards"].append(copy.deepcopy(family["cards"][0])), "two of one key"),
                              (lambda family: card("trap")(family)["axes"].reverse(), "axes shape and tip_mm"),
                              (lambda family: card("pointed")(family)["grid"].update({"pointed|2": "umi-finray-2mm"}), "not of its parts"),
                              (lambda family: card("concave")(family)["axes"][1]["choices"].append({"value": "1.8", "label": "1.8"}), "every choice")):
            with self.subTest(message=message):
                parts = copy.deepcopy(self.parts)
                edit(parts["families"][TAPERS])
                with self.assertRaisesRegex(library_write.LibraryError, message):
                    library_write.family_record(TAPERS, parts["families"][TAPERS], parts, library_write.plan(parts))

    def test_each_tips_setup_is_the_videos_on_its_contact_face(self) -> None:
        # The whole contact face (x = 0, facing -x) grown flat from the facet under the face point, the base at the
        # mount end, no border (a cut face is not the four-sided face the 65 mm border is drawn on), the page's options.
        from surface import api, select

        for part_id, part in self.parts["parts"].items():
            if part.get("family") != TAPERS:
                continue
            with self.subTest(part=part_id):
                setup = part["setup"]
                (op,) = setup["selection"]["ops"]
                self.assertEqual({key: value for key, value in op.items() if key != "seed_facet"}, {"op": "grow", "mode": "add", "preset": "flat"})
                self.assertEqual((setup["base"], setup["border"], setup["options"]), (MOUNT_BASE, None, {}))
                self.assertEqual((part["mesh"]["file"], part["mesh"]["name"]), (f"meshes/{part_id}.stl", f"{part_id}.stl"))
                mesh = api.load_mesh({"name": part["mesh"]["name"]}, (LIBRARY / part["mesh"]["file"]).read_bytes())
                self.assertEqual(mesh.unit, "mm")
                facet = op["seed_facet"]
                points = mesh.facet_points(facet)
                self.assertLess(mesh.normals[facet][0], -0.999999)
                self.assertLessEqual(max(abs(point[0]) for point in points), 1e-6)
                self.assertLessEqual(select.point_triangle_distance(FACE_POINT, *points), 1e-6)

    def test_each_tip_is_cut_by_its_profile(self) -> None:
        # The review of 2026-11-16: the meshes were checked only by their hashes, so a concave file cut with the convex
        # profile, or two kinds' files swapped, would have passed.  Each tip's mesh measured as tools/library_tips.py's
        # check measures it: its width (where a plane at that height cuts it) 1, 5 and 20 mm above the tip and halfway
        # up the taper the width of the tool's profile for its kind (its profile, height and tip width; _half_width(),
        # the tool's own read from its source where the private tool is: the two one), within 0.05 mm, centred on the
        # face's middle (y = -12.9), and the full 25.8 mm just above the taper; halfway up the profiles differ by more
        # than the tolerance, so the measures tell them apart.
        half_width, width, z_tip = _half_width, TAPER_FACE_MM, TAPER_TIP_Z
        tool = _tool_profile()
        if tool is not None:
            self.assertEqual(tool[1:], (width, z_tip))
            for _, words, height, tips in TAPER_KINDS.values():
                for tip in tips:
                    for k in range(11):
                        at = height * k / 10
                        self.assertAlmostEqual(tool[0](at, TAPER_PROFILES[words], height, float(tip)), half_width(at, TAPER_PROFILES[words], height, float(tip)),
                                               places=9, msg=f"{words}, h {height}, tip {tip}, s {at}: the tool's profile is this one")
        for part_id, part in self.parts["parts"].items():
            if part.get("family") != TAPERS:
                continue
            match = re.fullmatch(r"umi-([a-z-]+)-tip([\d.]+)", part_id)
            _, words, height, tips = TAPER_KINDS[match.group(1)]
            self.assertIn(match.group(2), tips)
            profile, tip = TAPER_PROFILES[words], float(match.group(2))
            triangles = [corners for corners in _stl_triangles((LIBRARY / part["mesh"]["file"]).read_bytes()) if min(corners[2::3]) < z_tip + height + 1]
            with self.subTest(part=part_id):
                for above in (1.0, 5.0, 20.0, height / 2):
                    low, high = _span_at(triangles, z_tip + above)
                    expected = 2 * half_width(height - above, profile, height, tip)
                    self.assertAlmostEqual(high - low, expected, delta=0.05, msg=f"{above} mm above the tip")
                    self.assertAlmostEqual((high + low) / 2, -width / 2, delta=0.05, msg=f"centred {above} mm above the tip")
                    others = [2 * half_width(height - above, other, height, tip) for other in TAPER_PROFILES.values() if other != profile]
                    if above == height / 2:
                        self.assertGreater(min(abs(value - expected) for value in others), 0.1, "the profiles told apart halfway up")
                low, high = _span_at(triangles, z_tip + height + 0.05)
                self.assertAlmostEqual(high - low, width, delta=0.05, msg="full width above the taper")


class PublicTests(unittest.TestCase):
    def test_the_writer_is_public_and_the_importer_private(self) -> None:
        def covered(relative: str) -> bool:
            return any(relative == path or relative.startswith(path + "/") for path in export_public.PUBLIC)

        self.assertTrue(covered("tools/library_write.py"))
        self.assertTrue(covered("web/library/entries.json"))
        # The pictures' tool too (tools/browser: the checks' environment), and the pictures with web/.
        self.assertTrue(covered("tools/browser/library_shots.py"))
        self.assertTrue(covered("web/library/shots/manifest.json"))
        self.assertFalse(covered("tools/library_import.py"))
        self.assertFalse(covered("tools/library_tips.py"))
        # The grippers' scene builder (2026-11-05: it reads the private recipes and needs numpy and trimesh) is private;
        # its scenes and bodies are public with web/, and the documents name it in backticks only (no link).
        self.assertFalse(covered("tools/library_scenes.py"))
        self.assertTrue(covered("web/library/scenes/scenes.json"))
        # The showcase's builder and its decimator (2026-11-12, stdlib) are public, with the folder they write.
        for shipped in ("tools/library_showcase.py", "tools/mesh_decimate.py", "web/vendor/ufactory-g1/NOTICE.md", f"web/library/{SHOWCASE_SCENE}"):
            self.assertTrue(covered(shipped), shipped)
        for document in (ROOT / "README.md", ROOT / "tools" / "README.md", ROOT / "docs" / "LIBRARY_VIEW.md", ROOT / "docs" / "INTEGRATION.md"):
            with self.subTest(document=document.name):
                self.assertNotRegex(document.read_text(encoding="utf-8"), r"\]\([^)]*library_scenes\.py")
        self.assertIn("`library_write.py`", (ROOT / "tools" / "README.md").read_text(encoding="utf-8"))
        self.assertIn("`library_shots.py`", (ROOT / "tools" / "browser" / "README.md").read_text(encoding="utf-8"))

    def test_the_deny_list_is_this_ones(self) -> None:
        # The importer refuses the same vendor models by SHA-256 and by name (the review of 2026-11-05: its list lacked
        # the six other xArm split meshes this one has).  The one list is the public writer's, so the public copy checks
        # it too; the private importer, read from its source when present (not imported), takes it from there and keeps
        # no copy of its own (the integration's review of 2026-11-05: a mutant of that copy broke the public --check).
        self.assertEqual(library_write.DENIED_SHA256, DENIED_SHA256)
        self.assertEqual((library_write.DENIED_NAME.pattern, library_write.DENIED_NAME.flags & re.IGNORECASE),
                         (DENIED_NAME.pattern, re.IGNORECASE))
        self.assertEqual(DENIED_NAME.flags & re.IGNORECASE, re.IGNORECASE)
        path = ROOT / "tools" / "library_import.py"
        if not path.exists():
            return  # the importer is private: not in the public copy
        assigned, imported = set(), set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    assigned.update(name.id for name in ast.walk(target) if isinstance(name, ast.Name))
            elif isinstance(node, ast.ImportFrom) and node.module == "library_write":
                imported.update(alias.name for alias in node.names if alias.asname is None)
        self.assertEqual({"DENIED_SHA256", "DENIED_NAME"} & assigned, set())
        self.assertLessEqual({"DENIED_SHA256", "DENIED_NAME"}, imported)

    def test_the_new_files_are_python_3_9(self) -> None:
        # CI runs the suite on 3.9 too: no match, parenthesised context managers or other later syntax.
        for path in (ROOT / "tools" / "library_write.py", ROOT / "tools" / "library_import.py", ROOT / "tools" / "library_tips.py",
                     ROOT / "tools" / "library_scenes.py", ROOT / "tools" / "browser" / "library_shots.py",
                     ROOT / "tools" / "library_showcase.py", ROOT / "tools" / "mesh_decimate.py", Path(__file__)):
            if not path.exists():
                continue  # the importer, the tips' tool and the scene builder are private: not in the public copy
            with self.subTest(file=path.name):
                source = path.read_text(encoding="utf-8")
                ast.parse(source, filename=str(path), feature_version=(3, 9))
                self.assertIn("from __future__ import annotations", source)
                self.assertNotRegex(source, r"\bmatch \w+:|zip\([^)]*strict=|\.bit_count\(")



# -- the page stage: the Library's page (index.html since 2026-11-16, library.html before), the header's link, main.js's
# gen.html?part=<id> (./?part=<id> before), app.py's route, the site build ------------------------------------------

class _Page(HTMLParser):
    """A page's elements: (tag, attributes) in order, with the text between them, and its scripts and style sheets."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list = []
        self.inline: list = []
        self._tag = None

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
        self._tag = tag

    handle_startendtag = handle_starttag

    def handle_data(self, data):
        if self._tag in ("script", "style") and data.strip():
            self.inline.append(self._tag)

    def handle_endtag(self, tag):
        self._tag = None


def _page(name: str) -> _Page:
    page = _Page()
    page.feed((WEB / name).read_text(encoding="utf-8"))
    return page


def _block(text: str, start: str, end: str) -> str:
    """The text from ``start`` to the first ``end`` after it, both included (the header's blocks, byte for byte)."""
    begin = text.index(start)
    return text[begin:text.index(end, begin) + len(end)]


def _function(source: str, name: str) -> str:
    """A top-level function of main.js, from its line to the next top-level function."""
    begin = re.search(r"^(async )?function %s\(" % re.escape(name), source, re.M).start()
    after = re.compile(r"^(async )?function \w+\(", re.M).search(source, begin + 1)
    return source[begin:after.start() if after else len(source)]


def _inner(source: str, name: str) -> str:
    """A function of library.js (inside its one closure, two spaces in), from its line to the line that closes it."""
    begin = re.search(r"^  (async )?function %s\(" % re.escape(name), source, re.M).start()
    return source[begin:source.index("\n  }\n", begin) + 4]


class PageTests(unittest.TestCase):
    """The Library's page, library.js and library.css as the spec of 2026-11-05 has them (the browser checks:
    library_checks).  Since the user's decision of 2026-11-16 ("是的 be first page") the Library is index.html and the
    generator gen.html: ``html``/``page`` are the Library's, ``index_html``/``index`` the generator's (named for its
    file of before)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.index_html = (WEB / "gen.html").read_text(encoding="utf-8")
        cls.script = (WEB / "library.js").read_text(encoding="utf-8")
        cls.style = (WEB / "library.css").read_text(encoding="utf-8")
        cls.page = _page("index.html")
        cls.index = _page("gen.html")

    def test_its_one_script_and_three_style_sheets_by_relative_urls(self) -> None:
        scripts = [(attributes.get("src"), attributes.get("type")) for tag, attributes in self.page.elements if tag == "script"]
        # The generator's addresses of before sent on first (web/forward.js, 2026-11-16: the Library is the first page),
        # the look's choice, in <head> (web/theme.js, 2026-11-06), the header's counts refreshed on the static site
        # (web/counts.js, the review of 2026-11-16: the first page's counts had stayed the build's), then the page's own.
        self.assertEqual(scripts, [("static/forward.js", None), ("static/theme.js", None), ("static/counts.js", None), ("static/library.js", None)],
                         "no backend.js, Pyodide or three.js on the Library")
        sheets = [attributes.get("href") for tag, attributes in self.page.elements if tag == "link" and attributes.get("rel") == "stylesheet"]
        self.assertEqual(sheets, ["static/styles.css", "static/theme.css", "static/library.css"])
        self.assertEqual(self.page.inline, [], "no inline script or style (the page's CSP)")
        self.assertNotIn("<style", self.html)
        for tag, attributes in self.page.elements:
            with self.subTest(tag=tag, attributes=sorted(attributes)):
                self.assertFalse([name for name in attributes if name.startswith("on")], "no inline event handler")
                self.assertNotIn("style", attributes)
                for name in ("src", "href"):
                    self.assertFalse((attributes.get(name) or "").startswith("/"), "a relative URL (the site lives under a subpath)")
        ids = [attributes["id"] for _, attributes in self.page.elements if "id" in attributes]
        self.assertEqual(sorted({identifier for identifier in ids if ids.count(identifier) > 1}), [])
        self.assertIn("<title>Library · FlexiTac-Gen</title>", self.html)
        for identifier in ("libHero", "libNote", "libGrid", "libShelves", "libWindow", "libClose", "libWindowBody", "libDetail", "libStatus"):
            self.assertIn(identifier, ids)
        self.assertNotIn("libTiles", ids, "no tiles since the layout of 2026-11-06")
        # The title's line since the user's request of 2026-11-15 ("Pre-generated examples · Download Gerbers · Send to
        # fab", a small heading with arrows): the three steps as a list, a grey arrow after each but the last, hidden from
        # screen readers, a step never broken inside.
        self.assertIn('<ol class="lib-tagline lib-steps"><li>Pre&#8209;generated examples</li><li>Download Gerbers</li><li>Send to fab</li></ol>', self.html)
        self.assertNotIn("Sensors already fitted to open&#8209;source gripper fingers.", self.html)
        css = (WEB / "library.css").read_text(encoding="utf-8")
        self.assertIn('.lib-steps li:not(:last-child)::after { content:"\\2192"; content:"\\2192" / ""; margin:0 .5em; color:var(--text-3); font-weight:400; }', css)
        self.assertIn(".lib-steps li { white-space:nowrap; }", css)

    def test_its_header_is_the_generators(self) -> None:
        # The title block and the header's right (the look's toggle and the community links, 2026-11-06) byte for byte (so
        # app.py and the build fill the counts once), the mode switch as two links in its segments, the Library link the
        # current page.
        for start, end in (('      <div class="masthead-title">', "      </div>\n"), ("      <!-- The header's right", "\n      </div>\n"),
                           ("        <!-- The FlexiTac community", "        </nav>\n")):
            with self.subTest(block=start.strip()[:30]):
                self.assertEqual(_block(self.html, start, end), _block(self.index_html, start, end))
        modes = [(tag, attributes) for tag, attributes in self.page.elements if "mode-links" in (attributes.get("class") or "").split()]
        self.assertEqual(modes, [("nav", {"class": "mode-picker mode-links", "aria-label": "Mode"})])
        links = re.search(r'<nav class="mode-picker mode-links" aria-label="Mode">(.*?)</nav>', self.html).group(1)
        # The generator's two modes at gen.html since 2026-11-16 (./#rect and ./ before).
        self.assertEqual(re.findall(r'<a href="([^"]+)"[^>]*><span>([^<]+)</span></a>', links), [("gen.html#rect", "Rectangular"), ("gen.html", "Gen by Surface")])

    def test_the_team_footer_is_the_same_on_both_pages(self) -> None:
        # The user's request of 2026-11-15 ("在我们这个flexitac gen的三个页面底部（lib,gen by surface,regtangular）下面都加上
        # flexitac team的标注，类似于awesome flexitac最下面"): Awesome-FlexiTac's footer word for word, one <footer> on each page
        # (index.html's under both modes, after <main>), its main block byte for byte the same, as the header's blocks are;
        # the Library's fine print (the makers' trademarks, its sources and licences) its first row there.  Every link
        # in a new tab (the community's rel noopener noreferrer, as the header's; the team's site noopener), the mail a
        # mailto: link.
        start, end = '      <div class="site-footer-main">', "\n    </footer>\n"
        self.assertEqual(_block(self.html, start, end), _block(self.index_html, start, end))
        for name, text in (("gen.html", self.index_html), ("index.html", self.html)):
            with self.subTest(page=name):
                self.assertEqual(text.count("<footer"), 1)
                self.assertEqual(text.count('<footer class="site-footer">'), 1)
                self.assertLess(text.index("</main>"), text.index('<footer class="site-footer">'))
        block = _block(self.index_html, start, end)
        words = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", block)).strip()
        self.assertEqual(words, "Maintained by the FlexiTac Team An open-source, scalable tactile solution for robotic systems. "
                         "© 2026 FlexiTac Research Community. Community GitHub Discord YouTube Contact binghao.huang@columbia.edu "
                         "Email for any questions.")
        links = re.findall(r'<a href="([^"]+)"([^>]*)>([^<]+)</a>', block)
        self.assertEqual(links, [
            ("https://flexitac.github.io/", ' target="_blank" rel="noopener"', "Maintained by the FlexiTac Team"),
            ("https://github.com/FlexiTac/FlexiTac", ' target="_blank" rel="noopener noreferrer"', "GitHub"),
            ("https://discord.gg/6gw887Vxms", ' target="_blank" rel="noopener noreferrer"', "Discord"),
            ("https://www.youtube.com/watch?v=HYmMbsrwWFA", ' target="_blank" rel="noopener noreferrer"', "YouTube"),
            ("mailto:binghao.huang@columbia.edu", "", "binghao.huang@columbia.edu")])
        self.assertEqual(re.findall(r"<h2[^>]*>(?:<a[^>]*>)?([^<]+)", block), ["Maintained by the FlexiTac Team", "Community", "Contact"])
        self.assertIn("    <footer class=\"site-footer\">\n      <p class=\"lib-footer\">Part names are their makers' trademarks; FlexiTac is not affiliated with them. "
                      '<a href="static/library/NOTICE.md">Sources and licences</a></p>\n' + start, self.html)
        self.assertNotIn("lib-footer", self.index_html)
        # Its look is the theme's (theme.css section 15, both pages); the fine print's a footnote over a hairline.
        rules, _ = parse_css(self.style)
        fine = {name: value for rule in rules if ".site-footer .lib-footer" in rule.selectors and not rule.conditions for name, value, _ in rule.declarations}
        self.assertEqual((fine.get("border-bottom"), fine.get("font-size"), fine.get("color")), ("1px solid var(--hairline)", "12px", "var(--text-2)"))

    def test_the_library_link_on_both_pages(self) -> None:
        # In the same tab from the generator since the user's request of 2026-11-15 ("从gen by surface跳到lib,会重开一个页面，
        # 这个改掉，改成直接跳过去 不重开页面"): no target, no rel, its title without "(opens in a new tab)"; the Library's own
        # the current page.  At ./ since the user's decision of 2026-11-16 (the Library the first page; library.html before).
        for name, page, expected in (("gen.html", self.index, {"href": "./", "target": None, "rel": None, "aria-current": None,
                                                               "title": "Sensors already fitted to open-source grippers"}),
                                     ("index.html", self.page, {"href": "./", "target": None, "aria-current": "page"})):
            with self.subTest(page=name):
                found = [(index, attributes) for index, (tag, attributes) in enumerate(page.elements)
                         if tag == "a" and attributes.get("class") == "masthead-library"]
                self.assertEqual(len(found), 1)
                index, attributes = found[0]
                self.assertEqual({key: attributes.get(key) for key in expected}, expected)
                # Not a masthead-link (the community's pills keep their checks); after the mode switch (gen.html: the
                # switch stays the title block's next sibling).
                self.assertNotIn("masthead-link", attributes["class"].split())
                before = [attributes for _, attributes in page.elements[:index] if "mode-picker" in (attributes.get("class") or "").split()]
                self.assertEqual(len(before), 1)
        text = (WEB / "gen.html").read_text(encoding="utf-8")
        self.assertLess(text.index('id="modePicker"'), text.index('class="masthead-library"'))
        self.assertIn("</fieldset>\n      <!-- The Library (the user's requests of 2026-11-05;", text)
        self.assertIn('<a class="masthead-library" href="./" title="Sensors already fitted to open-source grippers"><svg', text)

    def test_the_header_links_style_is_in_dated_blocks_beside_the_header_rules(self) -> None:
        # Not at the files' ends (where the on-part figure's rules go): styles.css's right after the mode switch's,
        # theme.css's right after the header's community links.
        styles = (WEB / "styles.css").read_text(encoding="utf-8")
        theme = (WEB / "theme.css").read_text(encoding="utf-8")
        self.assertLess(styles.index(".mode-picker input:focus-visible + span"), styles.index(".masthead-library {"))
        self.assertLess(styles.index(".masthead-library {"), styles.index(".cad-workspace {"))
        # Two lines at 1100 px and below, as before the link; from 1101 to 1130 px the one line with the grid's gaps 18 px
        # (the review of 2026-11-05).  Below 360 px the title and the mode switch smaller (theme.css: its type sizes).
        self.assertIn("@media (max-width:1100px) { .masthead { display:flex;", styles)
        self.assertIn("@media (min-width:1101px) and (max-width:1130px) { .masthead { column-gap:18px; } .masthead-library { margin-left:-6px; } }", styles)
        self.assertLess(theme.index(".masthead-library {"), theme.index("@media (max-width:359px) { .masthead h1 {"))
        self.assertLess(theme.index("@media (max-width:359px) { .masthead h1 {"), theme.index("/* 10. The guide"))
        self.assertLess(theme.index(".masthead-gh-stats {"), theme.index(".masthead-library {"))
        self.assertLess(theme.index(".masthead-library {"), theme.index("/* 10. The guide"))
        # More contrast underlines every link but the community's pills; the Library link's own text-decoration none
        # outranks the theme's `a` rule, so it is underlined again there.
        self.assertIn("@media (prefers-contrast: more) { .masthead-library { text-decoration:underline; } }", theme)

    def test_the_page_never_says_cad_in_its_own_files(self) -> None:
        for name, text in (("index.html", self.html), ("library.js", self.script), ("library.css", self.style)):
            with self.subTest(file=name):
                self.assertNotRegex(text, r"\bCAD\b")

    def test_its_script_neither_observes_nor_smooths_nor_leaves_the_site(self) -> None:
        source = self.script
        for word in ("IntersectionObserver", "ScrollTimeline", "ViewTimeline", "smooth", "scrollBehavior", "scroll-behavior", "innerHTML",
                     "backend.js", "apiFetch", "pyodide"):
            self.assertNotIn(word, source, word)
        self.assertIsNone(re.search(r"(window|document)\.addEventListener\(\s*[\"']scroll", source), "no window or document scroll listener")
        # No scroll listener at all since the review of 2026-11-16 (the UMI shelf a grid: its row's arrows had the one).
        self.assertEqual(len(re.findall(r"addEventListener\(\s*[\"']scroll", source)), 0, "no scroll listener")
        self.assertEqual([url for url in re.findall(r"https?://[^\s\"'`]+", source) if url != "http://www.w3.org/2000/svg"], [])
        self.assertIn('const BASE = "static/library/";', source)
        self.assertIn("fetch(`api/export/${kind}`", source)
        self.assertEqual(re.findall(r"""\bfetch\(\s*[`"']/""", source), [], "relative fetches only")
        self.assertIn('history.scrollRestoration = "manual";', source)
        self.assertIn('"use strict";', source)

    def test_its_style_sheet_moves_nothing_and_blue_fills_only_open(self) -> None:
        # Nothing moves on its own, with one exception, the user's request of 2026-11-15 ("箭头能不能做成像schetchfab一样的
        # 动画"): the 3D view's drag hint (.lib-drag) sways (its one @keyframes, on the drawn view only) and fades in and
        # out (opacity alone), and under reduced motion neither (its every transition and animation off there).  No other
        # transition or animation, no scroll behaviour or will-change.  Its one container query (its label by the view's
        # height, the review of 2026-11-15) the sheet's only one.
        rules, at_rules = parse_css(self.style)
        self.assertEqual({at.split()[0] for at in at_rules} - {"@media", "@keyframes", "@container"}, set(), "no @import, @font-face, @supports or @layer")
        self.assertEqual([at for at in at_rules if at.startswith("@keyframes")], ["@keyframes lib-drag-sway"])
        self.assertEqual([at for at in at_rules if at.startswith("@container")], ["@container lib-live (max-height:269px)"])
        declarations = [(selector, name, value, rule.conditions) for rule in rules for name, value, _ in rule.declarations for selector in rule.selectors]
        self.assertTrue(declarations)
        moving = [(selector, name, value, conditions) for selector, name, value, conditions in declarations
                  if name.startswith(("transition", "animation")) or name in ("scroll-behavior", "will-change")]
        reduced = ("@media (prefers-reduced-motion: reduce)",)
        self.assertEqual(sorted((selector, name, value) for selector, name, value, conditions in moving if conditions != reduced), [
            (".lib-drag", "transition", "opacity .2s ease"),
            (".lib-live.is-used .lib-drag", "transition", "opacity .5s ease .5s"),
            (".lib-stage.is-live .lib-drag", "animation", "lib-drag-sway 5s ease-in-out infinite"),
            (".lib-stage.is-live .lib-drag.is-gone", "animation", "none")])
        self.assertEqual(sorted((selector, name, value) for selector, name, value, conditions in moving if conditions == reduced), [
            (".lib-drag", "transition", "none"), (".lib-live.is-used .lib-drag", "transition", "none"), (".lib-stage.is-live .lib-drag", "animation", "none")])
        # The sway as Sketchfab's: side to side and back, 30 px at most (in proportion to the hint, the view's: library.css).
        self.assertIn("@keyframes lib-drag-sway { 0%, 100% { transform:translateX(calc(-1 * var(--lib-sway))); } 50% { transform:translateX(var(--lib-sway)); } }",
                      self.style)
        for selector, name, value, conditions in declarations:
            with self.subTest(selector=selector, property=name):
                if name == "position":
                    self.assertIn(value, ("relative", "absolute"))
                for url in re.findall(r"url\(\s*[\"']?([^\"')]*)", value):
                    self.assertTrue(url.startswith("data:"), url)
                if "var(--accent" in value:
                    # Since the user's decision of 2026-11-16 the showcase's Design your own too (both lead to Gen by Surface).
                    self.assertTrue(re.search(r"\.lib-open\b", subject(selector)) or re.match(r"\.lib \.lib-showcase \.lib-design(:hover|:active)?$", selector),
                                    f"the action blue only on Open in Gen by Surface and Design your own: {selector}")
        self.assertTrue([selector for selector, name, value, _ in declarations if "var(--accent)" in value and ".lib-open" in selector])
        self.assertTrue([selector for selector, name, value, _ in declarations if "var(--accent)" in value and ".lib-design" in selector])
        self.assertEqual(self.style.count("@keyframes"), 1)
        # Nothing scrolls sideways since the review of 2026-11-16 (the UMI shelf a grid, as the grippers').
        self.assertNotIn("scroll-snap", self.style)
        self.assertNotIn("overflow-x:auto", self.style)

    def test_a_sensors_picture_is_3_to_1_in_one_column(self) -> None:
        # The user's decision of 2026-11-05 (可压扁: the picture may be squashed): below 900 px, where a sensor's page is
        # one column with its picture above Open, that picture is 3:1, so Open is in a 390 x 844 phone's first screen on
        # every sensor's page (library_checks part_first_screen measures it); every other picture, and this one from
        # 900 px, 16:10.  Its drawing or image contained and centred, never hidden.
        rules, _ = parse_css(self.style)
        aspects = [(selector, value, rule.conditions) for rule in rules for selector in rule.selectors
                   for name, value, _ in rule.declarations if name == "aspect-ratio" and selector != ".lib-drag svg"]
        # (The drag hint's drawing keeps its viewBox's 84:44: test_the_3d_view_is_a_named_group_over_the_picture.)
        # Since 2026-11-12 the showcase's two boxes are 4:5 (its large card's, and its own page's at every width): the
        # gripper stands upright, and at 16:10 four fifths of its picture were empty; its page has no Open to keep in a
        # phone's first screen, so its box is not squashed there.
        self.assertEqual(aspects, [(".lib-shot", "16 / 10", ()), (".lib-shot-detail", "3 / 1", ("@media (max-width:899px)",)),
                                   (".lib-shot-showcase", "4 / 5", ()), (".lib-detail-showcase .lib-shot-detail", "4 / 5", ())])
        fitted = {name: value for rule in rules if ".lib-shot > img" in rule.selectors and not rule.conditions for name, value, _ in rule.declarations}
        self.assertEqual((fitted.get("object-fit"), fitted.get("width"), fitted.get("height")), ("contain", "100%", "100%"))
        # No rule hides a picture, moves its image off the centre or sets a box's height past its aspect.
        for rule in rules:
            for selector in [item for item in rule.selectors if re.search(r"\.lib-(shot|frame)\b", item)]:
                with self.subTest(selector=selector):
                    inner = selector.endswith(("> svg", "> img"))
                    self.assertEqual([(name, value) for name, value, _ in rule.declarations
                                      if (name, value) in (("display", "none"), ("visibility", "hidden"))
                                      or (name in ("object-position", "max-height", "height") and not inner)], [])
        self.assertIn('className: `lib-shot lib-shot-${kind}`', self.script)
        self.assertIn('let box = slot(variant, "detail", state.picture, missed);\n    const frame = el("div", {className: "lib-frame"}, box);', _inner(self.script, "gallery"))
        self.assertIn("        gallery(variant),\n", _inner(self.script, "renderDetail"))

    def test_the_pictures_are_the_contracts_with_their_placeholder(self) -> None:
        # The pictures (the user's request of 2026-11-05: the cards show the finger and the sensor on it, the generator's
        # on-part figure; the contract with tools/library_write.py and the shots tool): a variant's "image" null or
        # {exploded: {src, card, width, height}, assembled: {src, width, height}, alt}, its paths relative to
        # static/library/.  A card shows the Exploded card file (640 x 400) lazily, decoded async, sized (no layout
        # shift), the alt the entry's; a sensor's page the view asked
        # for, eager; without a picture, or when its file fails, the placeholder (field()), never a broken image.
        self.assertIn("const CARD = [640, 400];", self.script)
        self.assertIn('const VIEWS = [["exploded", "Exploded"], ["assembled", "Assembled"]];', self.script)
        slot = _inner(self.script, "slot")
        # (Since 2026-11-12 a third kind, the showcase's large card: its own card file at its own size, loaded at once,
        # being the grid's first picture; a card's and a sensor's page's as they were.  Since the lead's review of the UMI
        # shelf's shapes, 2026-11-16, a shelf's card asks for its Assembled picture, its full file at its size: SHELF_VIEW.)
        self.assertIn('const assembledCard = kind === "card" && view === "assembled";', slot)
        self.assertIn('const src = kind === "detail" ? image?.[view]?.src : kind === "showcase" ? image?.card?.src\n'
                      '      : assembledCard ? image?.assembled?.src : image?.exploded?.card;', slot)
        self.assertIn("if (!src) {\n      box.append(field(variant));\n      return box;\n    }", slot)
        self.assertIn('const [width, height] = kind === "detail" ? [image[view].width, image[view].height] '
                      ': kind === "showcase" ? [image.card.width, image.card.height]\n'
                      '      : assembledCard ? [image.assembled.width, image.assembled.height] : CARD;', slot)
        self.assertIn('el("img", {src: BASE + src, width, height, alt: image.alt || "", decoding: "async",\n'
                      '      loading: kind === "card" ? "lazy" : null});', slot)
        self.assertIn('shown.addEventListener("error", () => {\n      shown.replaceWith(field(variant));\n      missed?.(view);\n    }, {once: true});', slot)
        self.assertIn("return drawing;", _inner(self.script, "field"))
        # Every picture is slot()'s: a family's cards (each its sensor's: the UMI shelf's shapes since 2026-11-16), a
        # gripper's card and a shelved part's own (its part's default); the shelf's in its view (SHELF_VIEW, Assembled)
        # framed on the fingertip (tipShot(), the review of 2026-11-16), a gripper's Exploded.
        self.assertIn("      tipShot(state.index.variants[shape.default]),\n", _inner(self.script, "shapeCard"))
        self.assertIn('shelved ? tipShot(state.index.variants[part.default]) : slot(state.index.variants[part.default], "card"),', _inner(self.script, "gripperCard"))
        self.assertIn('const box = slot(variant, "card", SHELF_VIEW);\n    box.classList.add("lib-shot-tip");\n    return box;', _inner(self.script, "tipShot"))
        self.assertIn('slot(entry, "showcase", SHOWCASE_VIEW)', _inner(self.script, "showcaseCard"))
        self.assertNotIn('"tile"', self.script)
        self.assertEqual(len(re.findall(r'el\("img"', self.script)), 1, "one image: slot()'s")

    def test_a_sensors_page_switches_its_picture_between_its_views(self) -> None:
        # A sensor's page (2026-11-05): the Exploded picture and, with both views, a small grey "Exploded | Assembled"
        # control under it in its frame: radios in a fieldset with a legend (a group named View: the arrow keys and a
        # screen reader), swapping the picture in place (no address or history change), the view kept across the
        # pitch, Shape and Tip width, its card's view again on each page opened (Exploded; a UMI shelf's sensor's
        # Assembled since the review of 2026-11-16, SHELF_VIEW), the control gone once both views failed.
        gallery = _inner(self.script, "gallery")
        self.assertIn('control = el("fieldset", {className: "lib-view"}, el("legend", {}, "View"),', gallery)
        self.assertIn('el("input", {type: "radio", name: "libView", value, checked: value === state.picture}),', gallery)
        self.assertIn("if (views.length < 2) return frame;", gallery)
        self.assertIn("        box.replaceWith(next);\n        box = next;\n", gallery)
        self.assertIn("if (state.picture !== view || !box.isConnected) return;", gallery)
        self.assertIn("if (control && failed.size === views.length) control.remove();", gallery)
        self.assertNotIn("history", gallery)
        self.assertNotIn("renderDetail", gallery)
        self.assertIn("    state.picture = isShelved(homeOf(id)) ? SHELF_VIEW : VIEWS[0][0];\n    setNote(\"\");", _inner(self.script, "showDetail"))
        self.assertNotIn("state.picture", _inner(self.script, "segments"))
        # Its style: the pitch's control made small, its legend for a screen reader only, its thumb grey (theme_checks
        # and library_checks see it never blue), and below 900 px the page tighter with it only, so Open stays in a
        # 390 x 844 phone's first screen (library_checks part_first_screen) and the page without pictures as before.
        rules, _ = parse_css(self.style)
        styled = {selector: {name: value for name, value, _ in rule.declarations} for rule in rules for selector in rule.selectors
                  if selector.startswith(".lib-view") and not rule.conditions}
        self.assertEqual(styled[".lib-view legend"].get("clip"), "rect(0 0 0 0)")
        self.assertEqual(styled[".lib-view input:checked + span"].get("background"), "var(--thumb)")
        self.assertEqual(styled[".lib-view .lib-seg-track"].get("background"), "var(--fill)")
        roomy = sorted(selector for rule in rules if rule.conditions == ("@media (max-width:899px)",) for selector in rule.selectors
                       if ".lib-view" in selector)
        # (The page's top and the room under its back link tightened too until the window of 2026-11-15, which has neither.)
        self.assertEqual(roomy, [".lib-detail:has(.lib-view) .lib-detail-body", ".lib-detail:has(.lib-view) .lib-info"])

    def test_a_sensors_page_turns_in_3d_and_only_there(self) -> None:
        # The user's request of 2026-11-05 (lib 点进去具体的每个夹爪的时候, 那个图也做成可以三维旋转的; docs/LIBRARY_VIEW.md): a
        # sensor's page draws its 3D view over its picture where its variant names one ("view") and the visitor asked for
        # no reduced data; three.js comes with ./cad/library_view.js, the one dynamic import, made on a sensor's page only
        # (never as the page loads, never on the grid), once for the page.
        script = self.script
        self.assertEqual(re.findall(r"\bimport\s*\(\s*([^)]*)\)", script), ['"./cad/library_view.js"'])
        self.assertIsNone(re.search(r"(?m)^\s*import\s", script), "a classic script: no static import")
        self.assertIn('if (!live.load) live.load = import("./cad/library_view.js");', _inner(script, "draw"))
        self.assertIn("load: null,", script[script.index("const live = {"):script.index("};", script.index("const live = {"))])
        present = _inner(script, "present")
        self.assertIn("if (!variant.view || navigator.connection?.saveData || live.off) {", present)
        self.assertLess(present.index("navigator.connection?.saveData"), present.index("draw();"))
        # present() from a sensor's page and, since 2026-11-12, from the showcase's own page (its 3D view is the same
        # one, drawn from its placed record); the grid takes the view down (rest()) and draws none.
        self.assertEqual(len(re.findall(r"\bpresent\(id\);", script)), 2)
        self.assertIn("    present(id);\n", _inner(script, "renderDetail"))
        self.assertIn("    present(id);\n", _inner(script, "renderShowcase"))
        self.assertIn("rest();", _inner(script, "showGrid"))
        for name in ("renderGrid", "shelf", "gripperCard", "grippers", "shapeCard", "showcaseCard", "slot", "gallery"):
            with self.subTest(function=name):
                self.assertNotRegex(_inner(script, name), r"\b(present|draw|import)\(")
        # Drawn, the stage shows the view and hides the picture under it (is-live): only once it is drawn.
        self.assertIn('stage.classList.add("is-live");', _inner(script, "draw"))

    def test_the_3d_view_is_a_named_group_over_the_picture(self) -> None:
        # Its host: a group the arrow keys and a drag turn (tabindex 0), named by the picture's alt, described by a hint
        # for a screen reader; laid over the picture's slot exactly, hidden until drawn; drawn, the picture hidden by
        # visibility alone (nothing moves); its focus ring the page's; no transition or animation (the style sheet's own
        # test); the probe state with ?probe only.
        host = _inner(self.script, "liveHost")
        self.assertIn('el("div", {className: "lib-live", tabindex: 0, role: "group", "aria-describedby": "libLiveHint"},', host)
        self.assertIn('el("span", {className: "lib-live-hint", id: "libLiveHint"}, "Drag, or use the arrow keys, to turn the sensor; 0 brings it back.")', host)
        self.assertIn('live.host.setAttribute("aria-label", variant.image?.alt || variant.label);', host)
        rules, _ = parse_css(self.style)
        styled = {}
        for rule in rules:
            if not rule.conditions:
                for selector in rule.selectors:
                    styled.setdefault(selector, {}).update({name: value for name, value, _ in rule.declarations})
        self.assertEqual(styled[".lib-stage"].get("position"), "relative")
        self.assertEqual((styled[".lib-live"].get("position"), styled[".lib-live"].get("inset"), styled[".lib-live"].get("visibility")),
                         ("absolute", "0", "hidden"))
        self.assertEqual(styled[".lib-stage.is-live > .lib-live"].get("visibility"), "visible")
        self.assertEqual(styled[".lib-stage.is-live img"], {"visibility": "hidden"})
        self.assertEqual(styled[".lib-stage.is-live svg"], {"visibility": "hidden"})
        self.assertIn("var(--focus)", styled[".lib-live:focus-visible"].get("outline", ""))
        self.assertEqual(styled[".lib-live-hint"].get("clip"), "rect(0 0 0 0)")
        for rule in rules:
            for selector in rule.selectors:
                if "lib-stage" in selector or "lib-live" in selector:
                    with self.subTest(selector=selector):
                        self.assertNotIn(("display", "none"), [(name, value) for name, value, _ in rule.declarations])
        state = _inner(self.script, "setLive")
        self.assertIn("if (PROBE === null) return;", state)
        self.assertLess(state.index("if (PROBE === null) return;"), state.index('el("pre", {id: "libViewState", hidden: true})'))
        self.assertIn('const PROBE = new URLSearchParams(location.search).get("probe");', self.script)
        self.assertIn('shoot: PROBE === "shoot"', _inner(self.script, "draw"))
        # The drag hint (the user's request of 2026-11-15: "箭头能不能做成像schetchfab一样的动画", in place of the turn's mark
        # of that day): in the host, so on every sensor's page and the showcase's (none on the shots tool's page); for the
        # eye alone; the page's own drawing (a hand between two arrows) over "Drag to rotate"; shown once the view is drawn
        # (is-live), at the bottom centre of the view, inside it; hidden at the visitor's first use of the view (used(): a
        # drawn view's): a mouse's or a pen's press of the main button (never a right or middle click, which turns
        # nothing), a turning key, a double click, a touch once it has turned the view (never a vertical swipe that
        # scrolls the window: the review of 2026-11-15); its sway stopped once faded out (is-gone); the pointer passing
        # through it; shown again on another gripper's page or with the window opened again (rest() forgets the page),
        # never for a pitch, a shape or a tip of the same page.
        self.assertNotIn("lib-turn", self.style + self.script)
        self.assertNotIn("is-turned", self.style + self.script)
        self.assertIn('      live.hint = PROBE === "shoot" ? null : dragHint();\n', host)
        self.assertIn('        live.hint);\n      live.host.addEventListener("pointerdown", event => {\n'
                      '        if (event.pointerType !== "touch" && event.button === 0) used();\n      });\n'
                      '      live.host.addEventListener("dblclick", used);\n', host)
        self.assertIn('      if (!live.used && live.view?.info().moved) used();\n      setLive();\n', _inner(self.script, "viewNews"))
        self.assertIn("        if (TURN_KEYS.includes(event.key) && !event.altKey && !event.ctrlKey && !event.metaKey) used();\n", host)
        self.assertIn('    live.host.classList.toggle("is-used", live.used);\n    live.hint?.classList.toggle("is-gone", live.used);\n', host)
        self.assertIn('const TURN_KEYS = ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"];', self.script)
        hint = _inner(self.script, "dragHint")
        self.assertIn('const hint = el("span", {className: "lib-drag", "aria-hidden": "true"}, drawing, el("span", {className: "lib-drag-label"}, "Drag to rotate"));', hint)
        self.assertIn('svg("svg", {viewBox: "0 0 84 44", "aria-hidden": "true", focusable: "false"})', hint)
        self.assertEqual(re.findall(r'class: "(lib-drag-[a-z]+)"', hint), ["lib-drag-arrow", "lib-drag-hand", "lib-drag-crease"])
        self.assertIn('if (event.propertyName === "opacity" && live.used) hint.classList.add("is-gone");', hint)
        self.assertEqual(_inner(self.script, "used").split("\n")[-4:], [
            '    if (live.used || !live.stage?.classList.contains("is-live")) return;', "    live.used = true;", '    live.host.classList.add("is-used");', "  }"])
        present = _inner(self.script, "present")
        self.assertIn("    const page = pageOf(id);\n    if (page !== live.page) {\n      live.page = page;\n      live.used = false;\n    }\n", present)
        self.assertLess(present.index("pageOf(id)"), present.index("liveHost(variant)"))
        self.assertIn("    live.page = null;\n", _inner(self.script, "rest"))
        self.assertIn("const pageOf = id => (state.showcase?.id === id ? id : state.index.parts[state.index.variants[id].part].family || state.index.variants[id].part);",
                      self.script)
        self.assertNotIn("live.used", _inner(self.script, "segments") + _inner(self.script, "renderDetail"))
        drag = styled[".lib-drag"]
        self.assertEqual((drag.get("position"), drag.get("left"), drag.get("right"), drag.get("margin"), drag.get("pointer-events"), drag.get("opacity")),
                         ("absolute", "0", "0", "0 auto", "none", "0"))
        self.assertEqual(styled[".lib-stage.is-live .lib-drag"].get("opacity"), "1")
        self.assertEqual(styled[".lib-live.is-used .lib-drag"].get("opacity"), "0")
        self.assertEqual(styled[".lib-stage.is-live .lib-drag svg"], {"visibility": "inherit"})
        self.assertLess(self.style.index(".lib-stage.is-live .lib-drag {"), self.style.index(".lib-live.is-used .lib-drag {"), "used wins over drawn")
        # Light in either scheme over the view's light box: no token (the dark scheme's would be light ink).  The arrows the
        # hand's material, one white cursor edged in ink (the review of 2026-11-15: the ink's arrows had been grey on the
        # black bases), in the same rule.
        for selector in (".lib-drag-hand", ".lib-drag-crease", ".lib-drag-arrow", ".lib-drag-label"):
            self.assertFalse([value for value in styled[selector].values() if "var(" in value], selector)
        self.assertEqual(styled[".lib-drag-arrow"], {"fill": "rgba(255,255,255,.94)", "stroke": "#1d1d1f", "stroke-width": "1.5", "stroke-linejoin": "round"})
        self.assertEqual(styled[".lib-drag-hand"], styled[".lib-drag-arrow"])
        self.assertIn(".lib-drag-hand,.lib-drag-arrow {", self.style)
        # Its size the view's, never the window's (the review of 2026-11-15): the host a size container, the drawing 13.4 %
        # of its height between 28 and 44 px (84 x 44 at most), its distance from the bottom and its sway in proportion,
        # its label only on a view 270 px tall or more; no rule of the hint's by the window's width.
        self.assertEqual(styled[".lib-live"].get("container"), "lib-live / size")
        self.assertEqual((drag.get("--lib-hint"), drag.get("bottom"), drag.get("--lib-sway")),
                         ("clamp(28px,13.4cqh,44px)", "calc(var(--lib-hint) * 14 / 44)", "calc(var(--lib-hint) * 30 / 44)"))
        drawing = styled[".lib-drag svg"]
        self.assertEqual((drawing.get("width"), drawing.get("height"), drawing.get("aspect-ratio")), ("auto", "var(--lib-hint)", "84 / 44"))
        self.assertIn('viewBox: "0 0 84 44"', hint)
        short = {selector: {name: value for name, value, _ in rule.declarations} for rule in rules
                 if rule.conditions == ("@container lib-live (max-height:269px)",) for selector in rule.selectors}
        self.assertEqual(short, {".lib-drag-label": {"display": "none"}})
        by_window = [(selector, rule.conditions) for rule in rules for selector in rule.selectors if ".lib-drag" in selector
                     and any("width" in condition or "height" in condition for condition in rule.conditions if condition.startswith("@media"))]
        self.assertEqual(by_window, [])

    def test_the_grid_is_the_grippers_cards_then_the_umi_shelf(self) -> None:
        # The user's requests of 2026-11-06 ("其他夹爪的话,不需要每个夹爪一row,你就每个row放4个夹爪就好了"; "只有umi finger在首页
        # 而可以显示重复,其他的夹爪后面就只出现一次,然后标注一下点进去我们有1-3mm customization"; "UMI Fin-Ray Gripper. ...
        # 这个section可以放在夹爪的后面"): no tiles and no "Start here."; one section of the grippers but the UMI finger, a
        # card each, four to a row from 735 px and two below, each its range and "Pick your pitch", opening its 2 mm
        # sensor; then the UMI finger's shelf (a part a family closes keeps a shelf, so the family keeps its card).
        script = self.script
        self.assertIn('const SHELVED = ["umi-finray"];', script)
        self.assertIn("const isShelved = part => SHELVED.includes(part) || familiesOf(part).length > 0;", script)
        self.assertIn("const carded = () => state.index.order.filter(part => !isShelved(part));", script)
        card = _inner(script, "gripperCard")
        self.assertIn('const lines = [pitchRange(part), "Pick your pitch"];', card)
        self.assertIn('id: shelved ? null : `gripper-${partId}`, href: `#${part.default}`', card)
        self.assertIn('heading("grippers", "Grippers.", `${word(parts.length)}${each}.`)', _inner(script, "grippers"))
        # Each gripper's card made with its part alone (map()'s index as gripperCard's ``shelved`` had dropped every id
        # but the first's: the card a shelved part's own, its place lost).
        self.assertIn('el("div", {className: "lib-cards"}, parts.map(part => gripperCard(part))));', _inner(script, "grippers"))
        grid = _inner(script, "renderGrid")
        self.assertLess(grid.index("grippers(parts)"), grid.index("...shelvedParts().map("), "the grippers' section first, the UMI shelf after it")
        for word in ("lib-tile", "libTiles", "index.start"):
            self.assertNotIn(word, script, word)
        # Its back links (since 2026-11-15 the window's X, which closes to the same place): the UMI finger's pages (its
        # tips' too) to its shelf, another gripper's to its card.
        self.assertIn("    state.place = placeOf(home);\n", _inner(script, "renderDetail"))
        self.assertIn('const placeOf = part => (isShelved(part) ? `shelf-${part}` : `gripper-${part}`);', script)
        # The older addresses: #shelf-start the top, #shelf-<gripper> its card; Back and Forward (an entry the page has
        # marked) put the grid back where it was, a link to another card goes to that card.
        route = _inner(script, "route")
        self.assertIn('const traversed = mark?.library === true;', route)
        self.assertIn('if (place !== id) history.replaceState(history.state, "", place ? `#${place}` : location.pathname + location.search);', route)
        self.assertIn('if (id === "shelf-start") place = "";', route)
        self.assertIn('else if (id.startsWith("shelf-") && carded().includes(id.slice(6))) place = `gripper-${id.slice(6)}`;', route)
        self.assertIn('if (!known || id === "shelf-start") window.scrollTo(0, 0);', route)
        self.assertIn("if (back && state.fromGrid && (traversed || !target || target.contains(state.opener))) {", _inner(script, "showGrid"))
        rules, _ = parse_css(self.style)
        columns = sorted((rule.conditions, value) for rule in rules if ".lib-cards" in rule.selectors
                         for name, value, _ in rule.declarations if name == "grid-template-columns")
        self.assertEqual(columns, [((), "repeat(4,minmax(0,1fr))"), (("@media (max-width:734px)",), "repeat(2,minmax(0,1fr))")])
        narrow = {name: value for rule in rules if rule.conditions == ("@media (max-width:359px)",) and ".lib-cards .lib-card-text" in rule.selectors
                  for name, value, _ in rule.declarations}
        self.assertEqual(narrow, {"padding-left": "6px", "padding-right": "6px"})
        self.assertNotIn(".lib-tile", self.style)
        # The writer's data the cards read: each gripper part's default its 2 mm sensor, at four pitches from 1 mm.
        entries = _json(LIBRARY / "entries.json")
        carded = [part for part in entries["order"] if part != "umi-finray" and part not in {f["shelf"] for f in entries["families"].values()}]
        self.assertEqual(len(carded), 7)
        for part in carded:
            with self.subTest(part=part):
                record = entries["parts"][part]
                self.assertEqual(entries["variants"][record["default"]]["pitch_mm"], 2)
                self.assertEqual(min(entries["variants"][key]["pitch_mm"] for key in record["variants"]), 1)
        self.assertEqual(len(grid_cards(entries)), 13, "the grippers' seven cards and the UMI shelf's six shapes (its four pitches and "
                         "its Tapered tips card until 2026-11-16)")

    def test_the_umi_shelf_is_one_card_per_shape(self) -> None:
        # The user's request of 2026-11-16, of the UMI shelf's 1, 1.5, 2 and 3 mm cards: "后面这三种不是重复了吗，在第一个umi
        # 1mm点进去，config就可以选择毫米数量；我在这里更多想要体现umi不同shape我们都可以fit,你现在只有一个shape变体" (the pitch is
        # chosen on the page; the shelf shows the finger's shapes), and the shapes chosen (concave arc, pointed, short
        # taper).  A shelved part's shelf: its own card, a gripper's card named by its shape ('Straight finger', its range,
        # 'Pick your pitch', its 2 mm page with no grid id of its own), then its families' cards in their order, each the
        # picture of its sensor, its title and two lines, opening that sensor's page.
        script = self.script
        shelf = _inner(script, "shelf")
        # Since its review the same day a grid as the grippers' section, three to a row from 735 px (two rows: 4 + 2
        # would leave a row half empty) and two below: the shapes side by side (a row that scrolled sideways showed four
        # at 1440 px, one on a phone).
        self.assertIn("el(\"div\", {className: \"lib-cards\"}, gripperCard(partId, true),\n"
                      "        families.flatMap(familyId => state.index.families[familyId].cards.map(shape => shapeCard(familyId, shape)))));", shelf)
        self.assertIn("heading(id, `${part.title}.`, part.shelf)", shelf)
        rules, _ = parse_css(self.style)
        shelved = sorted((rule.conditions, value) for rule in rules if ".lib-shelf > .lib-cards" in rule.selectors
                         for name, value, _ in rule.declarations if name == "grid-template-columns")
        self.assertEqual(shelved, [(("@media (min-width:735px)",), "repeat(3,minmax(0,1fr))")])
        # Each card's picture framed on the fingertip (the review of 2026-11-16: at the Assembled home the taper was a
        # third of the picture's width, the shapes alike at a card's size): the same Assembled file scaled about the
        # tip's corner inside its clipping box, the placeholder unframed.
        framed = {name: value for rule in rules if rule.selectors == (".lib-shot-tip > img",) and not rule.conditions for name, value, _ in rule.declarations}
        self.assertEqual(framed, {"transform": "scale(2.2)", "transform-origin": "41% 3%"})
        clipped = {name: value for rule in rules if rule.selectors == (".lib-shot",) and not rule.conditions for name, value, _ in rule.declarations}
        self.assertEqual(clipped.get("overflow"), "hidden")
        self.assertEqual(script.count("tipShot("), 3, "tipShot() and the shelf's two kinds of card")
        # Its heading's count of shapes one unit too (the review of 2026-11-16: 'Six / finger shapes,' at 390 px).
        self.assertIn('const keep = text => String(text).replace(/\\b(\\w+) finger shapes\\b/g, "$1\\u00a0finger\\u00a0shapes")', script)
        # A shape's page titled by its card (every tip's part is 'UMI Fin-Ray Gripper, tapered tip'), and opened in the
        # view its card shows (Assembled: from Exploded the tapered end lay under the exploded layers).
        self.assertIn("const title = shape ? `${index.parts[home].title}, ${shape.title.toLowerCase()}` : part.title;", _inner(script, "renderDetail"))
        self.assertIn('el("h2", {className: "lib-detail-title", id: "libDetailTitle", tabindex: "-1"}, whole(title)),', _inner(script, "renderDetail"))
        card = _inner(script, "gripperCard")
        self.assertIn("const name = shelved ? part.card || part.title : part.title;", card)
        shape = _inner(script, "shapeCard")
        self.assertIn('return el("a", {className: "lib-card", href: `#${shape.default}`, "data-variant": shape.default, "data-family": familyId, "data-card": shape.key,', shape)
        self.assertIn('el("span", {className: "lib-card-name"}, shape.title),\n        shape.lines.map(line => el("span", {className: "lib-card-line"}, keep(line)))', shape)
        # The shelf's cards in the Assembled view (the lead's review of 2026-11-16: from the Exploded home the tapered end was
        # foreshortened under the exploded layers, the six shapes alike); the grippers' cards Exploded.
        self.assertIn('const SHELF_VIEW = "assembled";', script)
        self.assertEqual(shelf_cards(_json(LIBRARY / "entries.json")), ["umi-finray-2mm"] + [default for *_, default in TAPER_CARDS])
        # The heading's range of shapes one unit, as a range of pitches ('straight to pointed' broke from 735 to 900 px).
        self.assertIn('.replace(/(\\d|\\bstraight) to (\\w)/g, "$1\\u00a0to\\u00a0$2");', script)
        # The pitch cards and their badge line are gone (no card of the grid has a badge; the showcase's label is its own).
        self.assertNotIn("function card(", script)
        self.assertNotIn("function familyCard(", script)
        self.assertEqual(script.count('className: "lib-badge"'), 2, "the showcase's card and page only")
        # A family's sensor: its card's axes of more than one choice (Tip width; the Short taper's Shape too), its Tip
        # fact over the card's taper height.
        self.assertIn("const cardOf = (family, id) => family.cards.find(shape => Object.values(shape.grid).includes(id));", script)
        controls = _inner(script, "familyControls")
        self.assertIn("axis.choices.length < 2 ? null : segments(axis.label, `libAxis-${axis.key}`,", controls)
        detail = _inner(script, "renderDetail")
        self.assertIn("const shape = family ? cardOf(family, id) : null;", detail)
        self.assertIn("mm at the tip, over the last ${shape.h_mm} mm`]] : [];", detail)
        # The family's own address opens its default (#umi-tapers, as before its cards).
        self.assertIn("if (Object.hasOwn(state.index.families || {}, id)) { showDetail(state.index.families[id].default); return; }", _inner(script, "route"))
        # The writer's data the shelf reads: the UMI finger's heading and card name, its cards in the shelf's order.
        entries = _json(LIBRARY / "entries.json")
        umi = entries["parts"]["umi-finray"]
        self.assertEqual((umi["shelf"], umi["card"], umi["default"]), ("Six finger shapes, straight to pointed.", "Straight finger", "umi-finray-2mm"))
        self.assertEqual([(card["title"], card["default"]) for card in entries["families"][TAPERS]["cards"]],
                         [(title, default) for _, title, _, default in TAPER_CARDS])
        self.assertEqual(grid_cards(entries)[7:], ["umi-finray-2mm"] + [default for *_, default in TAPER_CARDS])

    def test_the_showcase_is_the_grid_s_first_card_and_a_page_of_its_own(self) -> None:
        # The user's request of 2026-11-12 ("在lib最上面一栏放置flexitac+xarm gripper的原始版本的visualization; 这个版本是人手
        # design的不是autogenerate"): the grid's first section is one large card from showcase.json, a picture as every
        # card (slot(): no 3D on the grid), its label, its title and one line; it opens the showcase's own page, where the
        # 3D view of a sensor's page is drawn from the placed record.  The showcase is no entry: no pitch, no Open in Gen
        # by Surface, no download of the generator's.  Without showcase.json the Library is the one of before.
        script = self.script
        self.assertIn(f'const SHOWCASE_FORMAT = "{library_write.SHOWCASE_FORMAT}";', script)
        self.assertIn('const SHOWCASE_VIEW = "assembled";', script)
        start = _inner(script, "start")
        self.assertIn("const [index, showcase] = await Promise.all([json(`${BASE}entries.json`), json(`${BASE}showcase.json`).catch(() => null)]);", start)
        self.assertIn("state.showcase = Object.hasOwn(index.variants, showcase?.id) || Object.hasOwn(index.parts, showcase?.id) ? null : showcaseOf(showcase);", start)
        of = _inner(script, "showcaseOf")
        self.assertIn('if (data?.format !== SHOWCASE_FORMAT || typeof data.id !== "string" || !data.placed || !data.image || !data.tutorial?.href '
                      '|| !Array.isArray(data.sources)) return null;', of)
        self.assertIn("build_id: null, view: {scene: data.placed.scene, placed: data.placed}", of)
        grid = _inner(script, "renderGrid")
        self.assertIn("      ...(state.showcase ? [showcaseCard()] : []),\n      ...(parts.length ? [grippers(parts)] : []),\n", grid)
        card = _inner(script, "showcaseCard")
        # The user's request of 2026-11-15 ("make only the image that can click to the details ... a button called
        # details"): the card is no link; its picture and its Details pill open the page, the picture's link out of the
        # Tab order and hidden from assistive technology (it repeats Details').
        self.assertIn('el("div", {className: "lib-card lib-showcase", id: "showcase"},', card)
        self.assertIn('el("a", {className: "lib-showcase-pic", href: `#${id}`, tabindex: "-1", "aria-hidden": "true"}, slot(entry, "showcase", SHOWCASE_VIEW)),', card)
        self.assertIn('el("a", {className: "lib-pill lib-showcase-details", href: `#${id}`, "data-showcase": id, "aria-label": `Details: ${data.title}`}, "Details")', card)
        # Design your own after Details (the user's decisions of 2026-11-15 and 2026-11-16) opens Gen by Surface.
        self.assertEqual(re.findall(r"href: ([^,]+),", card), ["`#${id}`", "`#${id}`", '"gen.html"'])
        # Its words: the label, the title and one line, each showcase.json's, and Details, the card's one word of its own
        # (with Design your own and its name for a screen reader since 2026-11-16).
        code = re.sub(r"^\s*//.*\n", "", card, flags=re.M)
        self.assertEqual(re.findall(r"data\.(\w+)", code), ["label", "title", "text", "title"])
        self.assertEqual(re.findall(r'"([A-Z][^"]*)"', code), ["Details", "Design your own sensor in Gen by Surface", "Design your own"])
        self.assertEqual(re.findall(r'el\("\w+", \{className: "([^"]+)"', card), ["lib-showcased", "lib-card lib-showcase", "lib-showcase-pic", "lib-card-text",
                                                                                     "lib-badge", "lib-showcase-title", "lib-showcase-line", "lib-pills",
                                                                                     "lib-pill lib-showcase-details", "lib-pill lib-design"])
        # Back to the grid focuses the link that opened the page; the showcase's card, no link, gives its Details.
        grid_code = _inner(script, "renderGrid")
        self.assertIn('const opener = event.target.closest("a.lib-card, .lib-showcase");\n      if (opener) state.opener = opener.querySelector(".lib-showcase-details") || opener;', grid_code)
        self.assertIn('state.opener = target.querySelector(".lib-showcase-details") || target;', _inner(script, "showGrid"))
        # The routes: its page at its id (before the variants: showcase.json's id is none of them), its card a place.
        route = _inner(script, "route")
        self.assertIn("    if (state.showcase?.id === id) { showShowcase(); return; }\n    if (Object.hasOwn(variants, id)) { showDetail(id); return; }", route)
        self.assertIn('const places = new Set([...(state.showcase ? ["showcase"] : []), "grippers",', route)
        shown = _inner(script, "showShowcase")
        self.assertIn("    state.picture = SHOWCASE_VIEW;\n", shown)
        self.assertIn("    renderShowcase();\n    raise();\n", shown)
        # Its page: the picture's frame with the Exploded | Assembled control (gallery()), the 3D view over it
        # (present()), its card the window's place (its X closes to it: the page's back link until 2026-11-15), the
        # tutorial (the address is showcase.json's: the script names none) as a grey pill opened in a new tab, the
        # sources' notices as files of the site.
        page = _inner(script, "renderShowcase")
        self.assertIn('    state.place = "showcase";\n', page)
        self.assertIn('el("div", {className: "lib-detail-body lib-detail-showcase"},\n        gallery(entry),', page)
        self.assertIn('el("a", {className: "lib-pill", href: data.tutorial.href, target: "_blank", rel: "noopener noreferrer"}, data.tutorial.label)', page)
        self.assertIn('el("a", {href: BASE + source.notice, target: "_blank", rel: "noopener"}, "notice")', page)
        self.assertIn('el("h2", {className: "lib-detail-title", id: "libDetailTitle", tabindex: "-1"}, whole(data.title)),', page)
        # Its line, then its line of detail (the sensor's size and fingers: the card's line no longer says them, 2026-11-15).
        self.assertIn('el("p", {className: "lib-detail-line"}, keep(data.text)),\n          el("p", {className: "lib-showcase-detail"}, keep(data.detail)),', page)
        # No generator downloads, no Open in Gen by Surface, no pitch, no facts, no prose of its own.
        for word in ("lib-open", "?part=", "renderDownloads", "lib-downloads", "lib-facts", "segments(", "lib-detail-note", "api/export", "Gerber ZIP"):
            with self.subTest(absent=word):
                self.assertNotIn(word, page)
        self.assertEqual(re.findall(r'"([A-Z][^"]*)"', page), [], "no word of its own (the back link's \"Library\" went with it, 2026-11-15)")
        # The 3D view: the one of a sensor's page, drawn from the placed record (docs/LIBRARY_VIEW.md "A placed sensor").
        self.assertIn("if (variant.view.placed) return live.view.show({base: BASE, id, placed: variant.view.placed, mode: state.picture});", _inner(script, "draw"))
        self.assertIn("const shown = id => (id && state.showcase?.id === id ? state.showcase.entry : state.index.variants[id]);", script)
        for name in ("present", "draw", "setLive"):
            with self.subTest(function=name):
                self.assertIn("shown(", _inner(script, name))
                self.assertNotIn("state.index.variants[", _inner(script, name))
        # Its style: the card as wide as the row, its picture beside its words from 735 px and above them below; the
        # cards' own look (no rule of its own for a background, a shadow or the blue); its page's box beside its words
        # from 900 px, never wider than 440 px in one column.
        rules, _ = parse_css(self.style)
        styled = {}
        for rule in rules:
            for selector in rule.selectors:
                if "showcase" in selector:
                    styled.setdefault((selector, rule.conditions), {}).update({name: value for name, value, _ in rule.declarations})
        self.assertEqual(styled[(".lib .lib-showcase", ())].get("flex-direction"), "row")
        self.assertEqual(styled[(".lib .lib-showcase", ("@media (max-width:734px)",))].get("flex-direction"), "column")
        # The picture first, on the left, in every width (2026-11-15: "picture put to the left, and the words just next to
        # the picture"; on the right before), the words close beside it.
        self.assertEqual(re.findall(r'el\("\w+", \{className: "(lib-showcase-pic|lib-card-text)"', card), ["lib-showcase-pic", "lib-card-text"])
        self.assertNotIn("order", styled[(".lib-showcase-pic", ())])
        self.assertNotIn("order", styled[(".lib-showcase-pic", ("@media (max-width:734px)",))])
        self.assertEqual(styled[(".lib-showcase .lib-card-text", ())].get("padding"), "24px clamp(24px,3vw,40px)")
        # Smaller since 2026-11-15 ("xarm can be smaller"): a fifth of the row within 220 to 300 px, 60 % of a phone's card.
        self.assertEqual((styled[(".lib-showcase-pic", ())].get("width"), styled[(".lib-showcase-pic", ("@media (max-width:734px)",))].get("width")),
                         ("clamp(220px, 20%, 300px)", "60%"))
        self.assertEqual(styled[(".lib-shot-showcase", ())].get("aspect-ratio"), "4 / 5")
        # Details its own size in every width (a sensor's page's pills fill the column below 900 px).
        self.assertEqual(styled[(".lib .lib-showcase .lib-pill", ())], {"align-self": "flex-start", "width": "auto"})
        self.assertEqual(styled[(".lib-detail-body.lib-detail-showcase", ("@media (min-width:900px)",))], {"grid-template-columns": "minmax(0,5fr) minmax(0,7fr)"})
        self.assertEqual(styled[(".lib-detail-showcase .lib-frame", ("@media (max-width:899px)",))].get("max-width"), "440px")
        for (selector, _), declarations in styled.items():
            if ".lib-design" in selector:
                continue  # Design your own's action blue (2026-11-16: DesignYourOwnTests), not the card's
            with self.subTest(selector=selector):
                self.assertFalse({"background", "background-color", "box-shadow", "border", "transition", "animation"} & set(declarations))
        # The committed document: its id an address of its own (the name rule: lower case, digits, hyphens; no part's,
        # variant's, family's or place's), its pictures the contract's sizes.
        document = _json(LIBRARY / "showcase.json")
        entries = _json(LIBRARY / "entries.json")
        self.assertRegex(document["id"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        taken = {*entries["variants"], *entries["parts"], *entries["families"], "showcase", "grippers", "shelf-start",
                 *(f"gripper-{part}" for part in entries["parts"]), *(f"shelf-{part}" for part in entries["parts"])}
        self.assertNotIn(document["id"], taken)
        self.assertEqual({kind: (document["image"][kind]["width"], document["image"][kind]["height"]) for kind in ("exploded", "assembled", "card")},
                         {"exploded": (1280, 1600), "assembled": (1280, 1600), "card": (800, 1000)})

    def test_a_card_s_details_open_in_a_window_over_the_library(self) -> None:
        # The user's request of 2026-11-15 ("after we click for all cards to details, we may not jump to a new page. lets
        # bump our to a large window, and if you click the "x" of right top conrner, it will close and back show lib"):
        # every card's page (a gripper's, the UMI shelf's, the tapered tips', the showcase's) opens in a large window over
        # the Library, a modal dialog (showModal(): the top layer, the page behind inert, Escape its cancel), the grid where
        # it was under it, the page not scrolling while it is open; its X at its top right closes it, as Escape and a
        # press and release on its backdrop do (never a drag begun inside it, nor a double-click's second click), to the
        # grid's place of its sensor (the page's back link's address, no native jump) with the card that opened it
        # focused; the address is the page's #<id>, so Back closes it and Forward opens it again.  The back link is gone.
        # Since the review of 2026-11-15 a close makes no history entry (with Android's Back a close request while the
        # window is open, a new entry there had made each Back close it and the next open it again): opened from the grid
        # it goes back over the window's entries, opened at its own address it replaces its entry.
        # (library_checks.py part_window sees it in the browser.)
        elements = self.page.elements
        ids = [attributes.get("id") for _, attributes in elements]
        at = ids.index("libWindow")
        self.assertEqual(elements[at], ("dialog", {"class": "lib-window", "id": "libWindow", "aria-labelledby": "libDetailTitle"}))
        self.assertEqual(elements[at + 1], ("button", {"type": "button", "class": "lib-close", "id": "libClose", "aria-label": "Close"}))
        self.assertEqual((elements[at + 2][0], elements[at + 2][1].get("aria-hidden"), elements[at + 2][1].get("focusable")), ("svg", "true", "false"))
        self.assertFalse([attributes for _, attributes in elements[at + 2:ids.index("libWindowBody")] if "stroke" in attributes], "a filled mark, as the toggle's")
        self.assertEqual(elements[ids.index("libWindowBody")], ("div", {"class": "lib-window-body", "id": "libWindowBody"}))
        self.assertEqual(elements[ids.index("libWindowBody") + 1], ("div", {"class": "lib-detail", "id": "libDetail"}), "shown by the window, never hidden itself")
        self.assertLess(ids.index("libGrid"), at)
        self.assertLess(at, ids.index("libStatus"), "in main.lib: the page's .lib rules")
        for name, text in (("index.html", self.html), ("library.js", self.script), ("library.css", self.style)):
            with self.subTest(file=name):
                self.assertNotIn("lib-back", text)
        script = self.script
        self.assertIn('  const WINDOW = $("libWindow");\n', script)
        self.assertEqual(script.count(".showModal("), 1, "one place opens it")
        # (The width a scroll bar takes measured first, --lib-bar: made up on the page's right while it cannot scroll, so
        # the grid keeps its width and place and the backdrop covers the screen; an overlay one, a phone's or the checks'
        # headless browser's, 0, which a kept room would narrow the grid by.  The review of 2026-11-15: scrollbar-gutter's
        # room had stayed bright and shrunk 100vw.)
        self.assertIn('    if (!WINDOW.open) {\n      ROOT.style.setProperty("--lib-bar", `${Math.max(0, window.innerWidth - ROOT.clientWidth)}px`);\n'
                      '      WINDOW.showModal();\n    }\n    $("libWindowBody").scrollTop = 0;\n    $("libDetailTitle").focus({preventScroll: true});\n',
                      _inner(script, "raise"))
        for name in ("showDetail", "showShowcase"):
            with self.subTest(function=name):
                shown = _inner(script, name)
                self.assertIn("    opening();\n", shown)
                self.assertTrue(shown.endswith("    raise();\n  }"), shown[-80:])
                self.assertNotRegex(shown, r"scrollTo|\.hidden|libHero|libGrid")
        opening = _inner(script, "opening")
        self.assertIn('    if (state.view === "grid") {\n      state.gridY = window.scrollY;\n      state.fromGrid = true;\n    }\n    state.view = "detail";\n', opening)
        grid = _inner(script, "showGrid")
        self.assertIn("    rest();\n    if (WINDOW.open) WINDOW.close();\n", grid)
        # (The rows' arrows were set as the grid was laid out until the review of 2026-11-16: no row scrolls now.)
        self.assertNotIn("syncs", script)
        self.assertNotRegex(grid, r"\.hidden|libHero|libGrid|libDetail")
        close = _inner(script, "closeWindow")
        self.assertIn('    if (state.view !== "detail" || state.closing) return;\n    if (state.depth > 0) {\n      state.closing = state.place;\n'
                      '      history.go(-state.depth);\n      return;\n    }\n    history.replaceState(null, "", `#${state.place}`);\n    route();\n', close)
        self.assertNotIn("location.hash", close, "no native jump to the place (the grid stays where it is)")
        self.assertNotIn("pushState", script, "no close makes a history entry")
        # Each entry's depth (route()): the window's entries of this visit over the grid's, so a close goes back over them;
        # a close come back to the grid's entry makes its address the window's place; the Pitch's, Shape's and Tip
        # width's replaced address keeps the entry's mark.
        route = _inner(script, "route")
        self.assertIn("    const mark = history.state;\n    const traversed = mark?.library === true;\n    const closing = state.closing;\n    state.closing = null;\n", route)
        self.assertIn('    if (closing && !windowed) {\n', route)
        self.assertIn('      history.replaceState(mark, "", `#${closing}`);\n      id = closing;\n    }\n', route)
        self.assertIn("    showGrid(place && known ? $(place) : null, traversed && !closing);\n", route)
        self.assertIn("    if (!windowed) state.depth = 0;\n    else if (traversed) state.depth = mark.visit === VISIT ? mark.depth || 0 : 0;\n"
                      '    else state.depth = state.view === "grid" ? 1 : state.view === "detail" && state.depth > 0 ? state.depth + 1 : 0;\n'
                      '    if (!traversed) history.replaceState({library: true, visit: VISIT, depth: state.depth}, "");\n', route)
        self.assertLess(route.index("const windowed = "), route.index("if (state.showcase?.id === id) { showShowcase(); return; }"))
        self.assertIn('    const windowed = state.showcase?.id === id || [variants, parts, state.index.families || {}].some(kind => Object.hasOwn(kind, id));\n', route)
        self.assertIn('  const VISIT = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;\n', script)
        self.assertIn('      history.replaceState(history.state, "", `#${target}`);\n', _inner(script, "segments"))
        events = _inner(script, "windowEvents")
        self.assertIn('    $("libClose").addEventListener("click", closeWindow);\n', events)
        self.assertIn('    WINDOW.addEventListener("cancel", event => {\n      event.preventDefault();\n      closeWindow();\n    });\n', events)
        self.assertIn('    WINDOW.addEventListener("close", () => { if (!WINDOW.open && state.view === "detail") closeWindow(); });\n', events)
        self.assertIn("      return event.target === WINDOW && (event.clientX < box.left || event.clientX >= box.right || event.clientY < box.top || event.clientY >= box.bottom);\n", events)
        self.assertIn('    WINDOW.addEventListener("pointerdown", event => { pressed = outside(event); });\n', events)
        self.assertIn("      if (pressed && event.detail < 2 && outside(event)) closeWindow();\n      pressed = false;\n", events)
        self.assertIn('    windowEvents();\n    window.addEventListener("hashchange", route);\n', _inner(script, "start"))
        # Its style: the cards' own look, large, its page scrolling inside it, the root not scrolling while it is open
        # (its scroll bar's width made up on its right), a sheet with no shadow below 735 px and on a screen less than
        # 501 px tall (a phone held sideways; the review of 2026-11-15); the X the header's toggle's round grey button over
        # its top right corner, opaque, with the page's focus ring; no blue.
        rules, _ = parse_css(self.style)
        styled = {}
        for rule in rules:
            for selector in rule.selectors:
                if "lib-window" in selector or "lib-close" in selector:
                    styled.setdefault((selector, rule.conditions), {}).update({name: value for name, value, _ in rule.declarations})
        window = styled[(".lib-window", ())]
        self.assertEqual({key: window.get(key) for key in ("width", "max-width", "max-height", "height", "margin", "padding", "border", "border-radius", "background",
                                                           "box-shadow", "overflow")},
                         {"width": "min(1200px, calc(100vw - 2 * var(--lib-gutter)))", "max-width": "none", "max-height": "calc(100dvh - 2 * var(--lib-gutter))",
                          "height": "fit-content", "margin": "var(--lib-gutter) auto auto", "padding": "0", "border": "0", "border-radius": "var(--r-lg)",
                          "background": "var(--surface)", "box-shadow": "var(--shadow-float)", "overflow": "hidden"})
        self.assertEqual(styled[(".lib-window[open]", ())], {"display": "flex", "flex-direction": "column"})
        body = styled[(".lib-window-body", ())]
        self.assertEqual({key: body.get(key) for key in ("flex", "min-height", "overflow-y", "overscroll-behavior")},
                         {"flex": "1 1 auto", "min-height": "0", "overflow-y": "auto", "overscroll-behavior": "contain"})
        # (Its page's top leaves the X its room, its 16 + 36 px and more; its sides at most 40 px, so its facts' column is
        # as wide as the page's was: the review of 2026-11-15.)
        self.assertEqual(body.get("padding"), "56px clamp(20px,2.5vw,40px) 40px")
        self.assertEqual(styled[(":root:has(.lib-window[open])", ())], {"overflow": "hidden", "padding-right": "var(--lib-bar,0px)"})
        self.assertFalse([rule.selectors for rule in rules for name, _, _ in rule.declarations if name == "scrollbar-gutter"])
        self.assertNotIn("libBar", script)
        self.assertEqual(styled[(".lib-window::backdrop", ())], {"background": "rgba(0,0,0,.45)"})
        sheet = ("@media (max-width:734px), (max-height:500px)",)
        self.assertEqual(styled[(".lib-window", sheet)], {"width": "100vw", "height": "100%", "max-height": "none", "margin": "0", "border-radius": "0", "box-shadow": "none"})
        self.assertEqual(styled[(':where(:root[data-theme="dark"]) .lib-window', sheet)], {"box-shadow": "none"}, "no hairline framing the screen")
        self.assertLess(self.style.index(':where(:root[data-theme="dark"]) .lib-window { box-shadow:inset'),
                        self.style.index('@media (max-width:734px), (max-height:500px) { :where(:root[data-theme="dark"]) .lib-window { box-shadow:none; } }'),
                        "after the dark window's hairline, which it overrides")
        # A sensor's page in it two even columns from 900 px (the window at most 1200 px wide: at 7 to 5 its facts' column
        # was 440 px at 1440 px, its pills stacked; the review of 2026-11-15), the showcase's 5 to 7.
        split = sorted((rule.conditions, value) for rule in rules for selector in rule.selectors if selector.startswith(".lib-detail-body")
                       for name, value, _ in rule.declarations if name == "grid-template-columns")
        self.assertEqual(split, [((), "minmax(0,1fr) minmax(0,1fr)"), (("@media (max-width:899px)",), "minmax(0,1fr)"),
                                 (("@media (min-width:900px)",), "minmax(0,5fr) minmax(0,7fr)")])
        close = styled[(".lib .lib-close", ())]
        self.assertEqual({key: close.get(key) for key in ("position", "top", "right", "width", "height", "border-radius", "background", "color")},
                         {"position": "absolute", "top": "16px", "right": "16px", "width": "36px", "height": "36px", "border-radius": "50%",
                          "background": "linear-gradient(var(--fill),var(--fill)) var(--surface)", "color": "var(--text)"})
        self.assertIn("var(--focus)", styled[(".lib-close:focus-visible", ())].get("outline", ""))
        self.assertEqual(sorted(selector for selector, _ in styled if "lib-close:" in selector and "focus" not in selector), [".lib .lib-close:active", ".lib .lib-close:hover"])
        for (selector, _), declarations in styled.items():
            with self.subTest(selector=selector):
                self.assertFalse([value for value in declarations.values() if "accent" in value], "no blue")

    def test_a_page_opened_at_its_address_paints_no_frame_of_the_grid_s_title(self) -> None:
        # The reviews of 2026-11-06: a sensor's page shared or reloaded had first painted the grid's title and tagline
        # over the footer; library.js, deferred, hid them too late, and nothing checked that its first route shows the
        # footer again.  Now theme.js, the one script before the first paint, marks <html data-lib-place> on the
        # Library (its meta) at an address of its own, library.css hides the title and the footer under it, and the
        # first route (or entries.json's failure) clears it (library_checks part_routes, with library.js late).
        head = self.html[:self.html.index("</head>")]
        self.assertLess(head.index('<meta name="flexitac-page" content="library" />'), head.index('<script src="static/theme.js"></script>'))
        self.assertNotIn("flexitac-page", self.index_html, "Gen by Surface is never marked")
        theme = (WEB / "theme.js").read_text(encoding="utf-8")
        self.assertIn("""  if (location.hash.length > 1 && document.querySelector('meta[name="flexitac-page"][content="library"]')) root.dataset.libPlace = "";\n""", theme)
        rules, _ = parse_css(self.style)
        # (The footer the FlexiTac team's since 2026-11-15, the fine print in it.)
        hidden = [(rule.conditions, rule.declarations) for rule in rules if rule.selectors == (":root[data-lib-place] #libHero", ":root[data-lib-place] .site-footer")]
        self.assertEqual(hidden, [((), [("display", "none", False)])])
        script = self.script
        self.assertIn('  const ROOT = document.documentElement;\n  if (location.hash.length > 1) ROOT.dataset.libPlace = "";\n', script)
        self.assertEqual(_inner(script, "opened"), "  function opened() {\n    delete ROOT.dataset.libPlace;\n  }")
        # (route() idle, too, at a hash web/forward.js sends on to gen.html: the review of 2026-11-16.)
        route = [line for line in _inner(script, "route").splitlines() if not line.strip().startswith("//")]
        self.assertEqual(route[:3], ["  function route() {", '    if (!state.index || document.documentElement.hasAttribute("data-forward")) return;', "    opened();"])
        self.assertIn('      $("libHero").hidden = false;\n      opened();\n      $("libStatus").textContent', _inner(script, "start"))
        self.assertEqual(script.count("opened();"), 2)

    def test_a_card_tabbed_to_is_shown_whole_in_its_row(self) -> None:
        # The review of 2026-11-06: a browser scrolls a focused element into view only when none of it shows, so at 390 px
        # a UMI card Tabbed to that its row showed in part stayed cut; its row then moved the least that showed it whole.
        # Since the review of 2026-11-16 the UMI shelf is a grid as the grippers' section (its six shapes side by side):
        # no row, no arrows, every card as wide as its column (library_checks part_layout).
        self.assertNotIn("function scroller(", self.script)
        self.assertNotIn("lib-track", self.script + self.style)
        self.assertNotIn("lib-arrow", self.script + self.style)
        self.assertNotIn("scrollBy", self.script)
        shelf = _inner(self.script, "shelf")
        self.assertIn('el("div", {className: "lib-cards"}, gripperCard(partId, true),', shelf)

    def test_a_card_tabbed_to_comes_into_the_window_with_room_round_it(self) -> None:
        # The verification of 2026-11-06: at 390 and 360 px the UMI shelf's card Tabbed to stopped flush with the window's
        # bottom, its focus ring (2 px, 2 px off) cut.  Every card of the grid has room above and below (scroll-margin
        # 16 px), the UMI shelf's too since it is a grid (2026-11-16; its row's own rule before), at every width
        # (library_checks part_layout).
        rules, _ = parse_css(self.style)
        margins = {rule.selectors: [(rule.conditions, value) for name, value, _ in rule.declarations if name == "scroll-margin"]
                   for rule in rules if any(name == "scroll-margin" for name, _, _ in rule.declarations)}
        self.assertEqual(margins.get((".lib .lib-cards > .lib-card",)), [((), "16px 0")])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_node_check(self) -> None:
        # A classic script: any node can check it (main.js's ES modules need node 22, test_surface_web).
        run = subprocess.run(["node", "--check", str(WEB / "library.js")], capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)


class GeneratorTests(unittest.TestCase):
    """web/cad/main.js's ./?part=<id> (the browser checks: cad_checks part_library)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.main = (WEB / "cad" / "main.js").read_text(encoding="utf-8")

    def test_the_default_part_and_the_shipped_fit_test_are_unchanged(self) -> None:
        self.assertIn('const DEFAULT_PART = {url: "static/vendor/umi/UMI-Soft-Gripper-Finger.stl", name: "UMI-Soft-Gripper-Finger.stl",\n'
                      '  fit: "static/vendor/umi/default-fit.json", tipSide: 2, borderMm: 65};', self.main)
        # runFit takes a shipped reply only for the shipped request, key by key: a Library sensor's is the request its
        # fit was made of (tools/library_write.py compose), so its fit_source is "shipped" too.
        self.assertEqual(self.main.count("const shipped = cad.defaultFile && cad.defaultFit && canonical(header(extra)) === canonical(cad.defaultFit.request);"), 1)

    def test_the_part_parameter_and_the_index(self) -> None:
        self.assertIn('const LIBRARY_INDEX = "static/library/entries.json";', self.main)
        self.assertIn('const LIBRARY_ID = new URLSearchParams(location.search).get("part") || "";', self.main)
        self.assertEqual((WEB / LIBRARY_INDEX_PATH).is_file(), True)
        part = _function(self.main, "libraryPart")
        self.assertIn("`static/library/${part.mesh.file}`", part)
        self.assertIn("`static/library/${variant.fit}`", part)
        self.assertIn("dropPartParameter();", part)
        # A variant, a part (its default) or a family (its default), as the Library's route takes them (the review of
        # 2026-11-05: ./?part=umi-tapers fell back to the UMI finger with a warning).
        self.assertIn("Object.hasOwn(index.variants || {}, id) ? id : Object.hasOwn(index.parts || {}, id) ? index.parts[id].default\n"
                      "      : Object.hasOwn(index.families || {}, id) ? index.families[id].default : \"\";", part)

    def test_the_users_own_file_and_remove_model_leave_the_library(self) -> None:
        self.assertIn("if (!isDefault) leaveLibrary();", _function(self.main, "loadFile"))
        self.assertIn("leaveLibrary();", _function(self.main, "removeModel"))
        leave = _function(self.main, "leaveLibrary")
        for needle in ("control.value !== value", "control.value = controlDefault(control);", "dropPartParameter();", "libraryNote();"):
            self.assertIn(needle, leave)
        default = _function(self.main, "controlDefault")
        for needle in ("control.defaultValue", "option.defaultSelected", "control.options[0]"):
            self.assertIn(needle, default)

    def test_each_option_off_its_default_is_recorded_whoever_wrote_it(self) -> None:
        # applyLibraryOptions records an option the sensor sets against its control's own default, not against the value
        # the control holds: a browser's restored form (Firefox's reload) leaves the sensor's values there before main.js
        # runs, and leaveLibrary must still put the defaults back (the review of 2026-11-05; cad_checks part_library).
        apply = _function(self.main, "applyLibraryOptions")
        self.assertIn("    if (!same(control.value)) control.value = value;\n    if (!same(controlDefault(control))) changed[control.id] = control.value;\n", apply)
        self.assertNotIn("changed[control.id] = control.value; }", apply)

    def test_a_library_sensor_is_built_from_its_requests_own_setup(self) -> None:
        build = _function(self.main, "buildDefaultSensor")
        for needle in ("const plan = cad.entry && cad.defaultFit ? cad.defaultFit.request : null;", "applyLibraryOptions(plan.options || {});",
                       "structuredClone(plan.selection.ops)", "commitBorder(structuredClone(plan.border.uv), {side: \"auto\"})",
                       "choosePoint(plan.base.point_xyz)", "defaultBorder()", 'cad.defaultBuild = "stopped";'):
            self.assertIn(needle, build)
        # The file note's prefix is the one test_library's labels are measured with.
        note = _function(self.main, "libraryNote")
        # Its link to the Library in the same tab, as the header's (the user's request of 2026-11-15), at ./#<id> since
        # the Library is the first page (the user's decision of 2026-11-16; library.html#<id> before).
        self.assertIn('note.replaceChildren("From the ", el("a", {href: `./#${cad.entry.id}`}, "Library"), '
                      '`: ${cad.entry.label.replace(/ mm$/, "\\u00a0mm")}`);', note)
        self.assertEqual("From the " + "Library" + ": ", NOTE_PREFIX)


# -- the first page (the user's decisions of 2026-11-15 and 2026-11-16: "我觉得之后可以让lib作为第一次点击进入时候使用的界面",
# "是的 be first page"): the Library is index.html at ./, the generator gen.html, and the addresses of before forwarded by
# web/forward.js (the browser checks: library_checks part_first_page, static_checks part_first_page) ------------------

# forward.js run under node on a page of each kind (the Library: <meta name="flexitac-page" content="library">; the
# forwarding page library.html: "forward"; the generator's page: none) at an address: the address location.replace was
# given (null: none), the mark on <html>, its visibility, and any other way it left (location.assign, location.href).
FORWARD_DRIVER = r"""
const vm = require("vm");
const fs = require("fs");
const source = fs.readFileSync(process.argv[2], "utf8");
const out = [];
for (const [page, href, steps = []] of JSON.parse(process.argv[3])) {
  const url = new URL(href);
  const left = {replaced: [], other: []};
  const listeners = [];
  const style = {setProperty: (name, value) => { style[name] = value; }};
  const root = {dataset: {}, style, hasAttribute: name => name === "data-forward" && Object.hasOwn(root.dataset, "forward"),
    setAttribute: (name, value) => { root.dataset[name] = value; }};
  const location = {get search() { return url.search; }, get hash() { return url.hash; }, get pathname() { return url.pathname; },
    origin: url.origin, toString: () => url.href,
    replace: target => left.replaced.push(String(target)), assign: target => left.other.push(String(target)), reload: () => left.other.push("reload")};
  Object.defineProperty(location, "href", {get: () => url.href, set: target => left.other.push(String(target))});
  const document = {documentElement: root, querySelector: selector => (page && selector.includes('name="flexitac-page"') ? {content: page} : null)};
  const context = {URLSearchParams, URL, location, document, window: null, history: {replaceState: () => left.other.push("replaceState"), pushState: () => left.other.push("pushState")},
    addEventListener: (type, listener) => listeners.push([type, listener])};
  context.window = context;
  vm.runInNewContext(source, context);
  // Then, in order: ["hash", "#x"], the address's hash changed within the page (its hashchange); ["pageshow", persisted],
  // the page shown again (by the back-forward cache: true) at its address then.
  for (const [kind, value] of steps) {
    if (kind === "hash") url.hash = value;
    const event = kind === "hash" ? {type: "hashchange"} : {type: "pageshow", persisted: value};
    for (const [type, listener] of listeners) if (type === event.type) listener(event);
  }
  out.push({replaced: left.replaced.length === 1 ? left.replaced[0] : left.replaced.length ? left.replaced : null, other: left.other,
            forward: root.dataset.forward ?? null, visibility: style.visibility ?? null, listening: listeners.map(([type]) => type)});
}
process.stdout.write(JSON.stringify(out));
"""
# (page, address after the site's folder, where it goes: None stays).  The generator's addresses of before on the
# Library, their query and hash kept; the Library's own (its sensors, parts, families, places, the showcase, ?probe)
# staying; library.html's to ./, or straight to gen.html for a generator's; the generator's own page never forwarded.
FORWARD_CASES = (
    ("library", "", None), ("library", "index.html", None), ("library", "?part=widowx-250-1mm", "gen.html?part=widowx-250-1mm"),
    ("library", "index.html?part=umi-tapers#rect", "gen.html?part=umi-tapers#rect"), ("library", "#rect", "gen.html#rect"),
    ("library", "#cad", "gen.html#cad"), ("library", "?probe#cad", "gen.html?probe#cad"), ("library", "?sample=franka-hand", "gen.html?sample=franka-hand"),
    ("library", "?debug", "gen.html?debug"), ("library", "?part=widowx-250-1mm&debug#cad", "gen.html?part=widowx-250-1mm&debug#cad"),
    ("library", "?part=", "gen.html?part="), ("library", "#drc-row", "gen.html#drc-row"), ("library", "#drc-column", "gen.html#drc-column"),
    ("library", "#maskNote", "gen.html#maskNote"), ("library", "#widowx-250-2mm", None), ("library", "#widowx-250", None),
    ("library", "#umi-tapers", None), ("library", "#gripper-arx-x5", None), ("library", "#shelf-umi-finray", None), ("library", "#shelf-start", None),
    ("library", "#showcase", None), ("library", "#grippers", None), ("library", "#flexitac-g1", None), ("library", "?probe", None),
    ("library", "?probe=shoot#widowx-250-2mm", None), ("library", "#rectangle", None), ("library", "#bogus", None),
    ("forward", "library.html", "./"), ("forward", "library.html#widowx-250-2mm", "./#widowx-250-2mm"),
    ("forward", "library.html?probe=shoot#flexitac-g1", "./?probe=shoot#flexitac-g1"), ("forward", "library.html#gripper-arx-x5", "./#gripper-arx-x5"),
    ("forward", "library.html#rect", "gen.html#rect"), ("forward", "library.html?part=widowx-250-1mm", "gen.html?part=widowx-250-1mm"),
    (None, "gen.html", None), (None, "gen.html?part=widowx-250-1mm#rect", None), (None, "gen.html#rect", None),
)
# The Library already open (the review of 2026-11-16): (address, its hash then changed within the page, where it goes:
# None stays).  A generator's hash of before sent on at its hashchange as at a load, the query kept; the Library's own
# hashes left to library.js.
FORWARD_HASH_CASES = (
    ("", "#rect", "gen.html#rect"), ("", "#cad", "gen.html#cad"), ("#widowx-250-2mm", "#rect", "gen.html#rect"),
    ("?probe", "#drc-row", "gen.html?probe#drc-row"), ("index.html", "#maskNote", "gen.html#maskNote"),
    ("", "#widowx-250-2mm", None), ("#widowx-250-2mm", "#gripper-arx-x5", None), ("", "#showcase", None), ("", "#rectangle", None),
    ("#rect", "#widowx-250-2mm", "gen.html#rect"),
)


def _forward_constants() -> tuple:
    source = (WEB / "forward.js").read_text(encoding="utf-8")
    keys = re.search(r"const GEN_KEYS = \[([^\]]*)\];", source).group(1)
    hashes = re.search(r"const GEN_HASHES = \[([^\]]*)\];", source).group(1)
    return re.findall(r'"([^"]+)"', keys), re.findall(r'"([^"]+)"', hashes)


class FirstPageTests(unittest.TestCase):
    """The Library is the first page and the generator's addresses of before keep working (the user's decisions of
    2026-11-15 and 2026-11-16): index.html the Library, gen.html the generator, library.html a forwarding page; web/
    forward.js sends the old addresses on with location.replace, their query and hash kept, before anything paints."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.forward = (WEB / "forward.js").read_text(encoding="utf-8")
        cls.library = (WEB / "index.html").read_text(encoding="utf-8")
        cls.forwarding = (WEB / "library.html").read_text(encoding="utf-8")
        cls.generator = (WEB / "gen.html").read_text(encoding="utf-8")

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_each_address_goes_where_it_should(self) -> None:
        base = "http://127.0.0.1:8008/flexitac-gen/"
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "driver.js").write_text(FORWARD_DRIVER, encoding="utf-8")
            cases = [[page, base + address] for page, address, _ in FORWARD_CASES]
            run = subprocess.run(["node", "driver.js", str(WEB / "forward.js"), json.dumps(cases)], cwd=folder, capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        for (page, address, target), seen in zip(FORWARD_CASES, json.loads(run.stdout)):
            with self.subTest(page=page, address=address):
                # Once, by location.replace (no history entry), and by nothing else; hidden from the first paint by
                # visibility (the page's background still painted) and marked for library.js.
                self.assertEqual(seen["replaced"], target)
                self.assertEqual(seen["other"], [])
                self.assertEqual((seen["forward"], seen["visibility"]), (None, None) if target is None else (target.split("?")[0].split("#")[0], "hidden"))

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_a_hash_of_before_on_the_open_library_goes_too(self) -> None:
        # The review of 2026-11-16: ./#rect typed over the open Library (or an old bookmark, a link) is a navigation
        # within the page, which runs forward.js no more; its hashchange listener sends it on as a load does (once, by
        # location.replace), and the Library alone listens (not the forwarding page, which has left, nor the generator).
        base = "http://127.0.0.1:8008/flexitac-gen/"
        cases = [["library", base + address, [["hash", then]]] for address, then, _ in FORWARD_HASH_CASES]
        cases += [["forward", base + "library.html", [["hash", "#rect"]]], [None, base + "gen.html", [["hash", "#rect"]]],
                  # Shown again by the back-forward cache (Back from gen.html#rect to the Library's entry before it): shown,
                  # and sent on again only at an address that asks; a page shown again by a load is left as it is.
                  ["library", base, [["hash", "#rect"], ["hash", ""], ["pageshow", True]]],
                  ["library", base, [["hash", "#rect"], ["pageshow", True]]],
                  ["library", base, [["hash", "#rect"], ["hash", ""], ["pageshow", False]]],
                  ["library", base, [["pageshow", True]]]]
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "driver.js").write_text(FORWARD_DRIVER, encoding="utf-8")
            run = subprocess.run(["node", "driver.js", str(WEB / "forward.js"), json.dumps(cases)], cwd=folder, capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        seen = json.loads(run.stdout)
        for (address, then, target), result in zip(FORWARD_HASH_CASES, seen):
            with self.subTest(address=address, then=then):
                self.assertEqual(result["replaced"], target)
                self.assertEqual(result["other"], [])
                self.assertEqual((result["forward"], result["visibility"]), (None, None) if target is None else ("gen.html", "hidden"))
                self.assertEqual(result["listening"], ["hashchange", "pageshow"])
        forwarding, generator, restored, again, loaded, fresh = seen[len(FORWARD_HASH_CASES):]
        self.assertEqual((forwarding["replaced"], forwarding["listening"]), ("./", []))
        self.assertEqual((generator["replaced"], generator["listening"], generator["forward"]), (None, [], None))
        self.assertEqual((restored["replaced"], restored["forward"], restored["visibility"]), ("gen.html#rect", None, ""))
        self.assertEqual((again["replaced"], again["forward"], again["visibility"]), (["gen.html#rect"] * 2, "gen.html", "hidden"))
        self.assertEqual((loaded["replaced"], loaded["forward"], loaded["visibility"]), ("gen.html#rect", "gen.html", "hidden"))
        self.assertEqual((fresh["replaced"], fresh["forward"], fresh["visibility"]), (None, None, None))

    def test_the_text_of_its_one_way_out(self) -> None:
        # Where node is not installed the test above is skipped: its essentials by their text.
        self.assertEqual(self.forward.count("location.replace("), 1)
        self.assertIn("  location.replace(target + location.search + location.hash);\n", self.forward)
        self.assertIn('  root.style.visibility = "hidden";\n', self.forward)
        self.assertNotRegex(self.forward, r"location\.(assign|href\s*=)|history\.|window\.stop|document\.write")
        self.assertIn('  const target = generator ? "gen.html" : page === "forward" ? "./" : null;\n', self.forward)
        self.assertIn("  const generator = GEN_KEYS.some(key => query.has(key)) || GEN_HASHES.includes(location.hash);\n", self.forward)
        # At a load, then on the Library at each hashchange (the review of 2026-11-16) and at a page shown again by the
        # back-forward cache while it was being sent on.
        self.assertIn('  forward();\n  if (page !== "library") return;\n  window.addEventListener("hashchange", forward);\n', self.forward)
        self.assertIn('    if (!event.persisted || !root.hasAttribute("data-forward")) return;\n    delete root.dataset.forward;\n'
                      '    root.style.visibility = "";\n    forward();\n', self.forward)
        run = subprocess.run(["node", "--check", str(WEB / "forward.js")], capture_output=True, text=True) if shutil.which("node") else None
        self.assertTrue(run is None or run.returncode == 0, run and run.stderr)

    def test_its_keys_and_hashes_are_the_generators(self) -> None:
        # GEN_KEYS: the query keys the generator reads (main.js and app.js) but ?probe, the checks' reads on both pages,
        # the Library's at ./; GEN_HASHES: Rectangular's #rect, #cad (CAD mode's name before 2026-10-30, docs/CAD_MODE.md:
        # still Gen by Surface) and the generator's own anchors, its design checks' links (app.js issueItem).
        keys, hashes = _forward_constants()
        scripts = "\n".join((WEB / name).read_text(encoding="utf-8") for name in ("app.js", "backend.js", "cad/main.js"))
        read = set(re.findall(r'URLSearchParams\(location\.search\)\.(?:get|has)\("(\w+)"\)', scripts))
        read |= {key for pairs in re.findall(r'\[((?:"\w+", )*"\w+")\]\.includes\(pair\.split\("="\)\[0\]\)', scripts) for key in re.findall(r'"(\w+)"', pairs)}
        self.assertEqual(sorted(read - {"probe"}), sorted(keys))
        self.assertIn('location.hash === "#rect"', scripts)
        anchors = {"#" + target for target in re.findall(r'el\("a", \{href: "#(\w+)"', scripts)}
        anchors |= {f"#drc-{board}" for board in ("row", "column")} if 'href: `#drc-${board[1]}`' in scripts and "/^boards\\.(row|column)\\b/" in scripts else set()
        self.assertEqual(sorted(hashes), sorted({"#rect", "#cad"} | anchors))
        self.assertIn("`#cad` still names CAD mode", (ROOT / "docs" / "CAD_MODE.md").read_text(encoding="utf-8"))

    def test_the_librarys_own_addresses_are_none_of_the_generators(self) -> None:
        # Every id the Library's route takes (its sensors, parts, families, the showcase) and every place of its grid.
        _, hashes = _forward_constants()
        entries = _json(LIBRARY / "entries.json")
        ids = {*entries["variants"], *entries["parts"], *entries.get("families", {}), library_write.SHOWCASE_ID}
        places = {"showcase", "grippers", "shelf-start", *(f"gripper-{part}" for part in entries["parts"]), *(f"shelf-{part}" for part in entries["parts"])}
        self.assertEqual(sorted(f"#{name}" for name in ids | places if f"#{name}" in hashes), [])

    def test_the_pages_load_it_first_and_the_forwarding_page_is_small(self) -> None:
        # The Library: its page's mark, then forward.js, the first script (before theme.js, which it may leave the
        # page before), no defer; the forwarding page: its mark, the same script, the look's (its background in the
        # visitor's look meanwhile) and a plain link to ./ for a browser without scripts, no header; the generator none.
        for name, text, mark, scripts in (("index.html", self.library, "library", ["static/forward.js", "static/theme.js", "static/counts.js", "static/library.js"]),
                                          ("library.html", self.forwarding, "forward", ["static/forward.js", "static/theme.js"]),
                                          ("gen.html", self.generator, None, None)):
            with self.subTest(page=name):
                page = _page(name)
                head = text.split("</head>", 1)[0]
                if mark is None:
                    self.assertNotIn("forward.js", text)
                    self.assertNotIn('name="flexitac-page"', head)
                    continue
                self.assertEqual([attributes["src"] for tag, attributes in page.elements if tag == "script"], scripts)
                self.assertLess(head.index(f'<meta name="flexitac-page" content="{mark}" />'), head.index('<script src="static/forward.js"></script>'))
                self.assertLess(head.index('<script src="static/forward.js"></script>'), head.index('<script src="static/theme.js"></script>'))
                self.assertLess(head.index('<script src="static/forward.js"></script>'), head.index("<link"))
                self.assertEqual(page.inline, [])
        self.assertNotIn("masthead", self.forwarding)
        self.assertEqual(re.findall(r'<a href="([^"]+)">([^<]+)</a>', self.forwarding), [("./", "open the Library")])
        self.assertIn("<title>Library · FlexiTac-Gen</title>", self.forwarding)
        self.assertLess(len(self.forwarding), 2000)

    def test_library_js_does_nothing_on_a_page_being_forwarded(self) -> None:
        # Its first statement: no route, no replaceState over the address forward.js is sending on.
        script = (WEB / "library.js").read_text(encoding="utf-8")
        body = script[script.index("(() => {\n") + len("(() => {\n"):]
        code = [line for line in body.splitlines() if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(code[0], '  if (document.documentElement.hasAttribute("data-forward")) return;')
        # Nor its route() at a hash forward.js sends on over the open Library (its hashchange listener the page's first;
        # the review of 2026-11-16): no note of an unknown sensor, no replaceState over that address.
        route = _inner(script, "route")
        lines = [line for line in route.splitlines()[1:] if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(lines[0], '    if (!state.index || document.documentElement.hasAttribute("data-forward")) return;')

    def test_every_link_follows(self) -> None:
        # The Library's header to the generator's modes and to itself (./), the generator's header and step 1's note to
        # the Library (./, ./#<id>), Open in Gen by Surface to gen.html?part=<id>; nothing links library.html or the
        # generator at ./ any more.
        library_js = (WEB / "library.js").read_text(encoding="utf-8")
        main = (WEB / "cad" / "main.js").read_text(encoding="utf-8")
        self.assertIn('el("a", {className: "lib-open", href: `gen.html?part=${encodeURIComponent(id)}`}, "Open in Gen by Surface")', library_js)
        self.assertIn('el("a", {href: `./#${cad.entry.id}`}, "Library")', main)
        for name, text in (("index.html", self.library), ("gen.html", self.generator), ("library.js", library_js), ("main.js", main),
                           ("app.js", (WEB / "app.js").read_text(encoding="utf-8"))):
            with self.subTest(file=name):
                code = re.sub(r"<!--.*?-->", "", re.sub(r"^\s*//.*$", "", text, flags=re.M), flags=re.S)
                self.assertNotRegex(code, r'href(?:=|: )["`](?:library\.html|index\.html|\./\?|\./#rect)')
        header = self.library.split("<main", 1)[0].split("<header", 1)[1]
        self.assertEqual([href for href in re.findall(r'href="([^"]*)"', header) if not href.startswith("https:")], ["gen.html#rect", "gen.html", "./"])


class DesignYourOwnTests(unittest.TestCase):
    """The showcase's Design your own (the user's decisions of 2026-11-15 and 2026-11-16: "在flexitac on xarm的details 后面，
    多一个按钮，generate sensor by yourself with cad file", its name chosen: "Design your own"): after Details on the card,
    Gen by Surface (gen.html) in this tab, where the visitor loads their own 3D model; the page's action blue (its second
    use: Open in Gen by Surface leads there too) in Details' pill and size, named for where it goes (the browser checks:
    showcase_checks part_page, library_checks part_window, theme_checks part_library)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = (WEB / "library.js").read_text(encoding="utf-8")
        cls.style = (WEB / "library.css").read_text(encoding="utf-8")

    def test_it_follows_details_on_the_card_alone(self) -> None:
        card = _inner(self.script, "showcaseCard")
        details = 'el("a", {className: "lib-pill lib-showcase-details", href: `#${id}`, "data-showcase": id, "aria-label": `Details: ${data.title}`}, "Details")'
        pill = 'el("a", {className: "lib-pill lib-design", href: "gen.html", "aria-label": "Design your own sensor in Gen by Surface"}, "Design your own")'
        # In Details' pills, right after it, the card's last element; a link (no button), in this tab (no target).
        self.assertIn(f'el("div", {{className: "lib-pills"}},\n            {details},\n            {pill}))));\n  }}', card)
        # The card's only: not on the showcase's own page, nor a sensor's.
        code = re.sub(r"^\s*//.*\n", "", self.script, flags=re.M)
        self.assertEqual(code.count("lib-design"), 1)
        self.assertEqual(code.count('"Design your own"'), 1)

    def test_its_look_is_details_pill_in_the_action_blue(self) -> None:
        rules, _ = parse_css(self.style)
        own = {selector: dict((name, value) for name, value, _ in rule.declarations) for rule in rules for selector in rule.selectors
               if "lib-design" in selector}
        self.assertEqual(own, {".lib .lib-showcase .lib-design": {"background": "var(--accent)", "color": "#fff"},
                               ".lib .lib-showcase .lib-design:hover": {"background": "var(--accent-hover)"},
                               ".lib .lib-showcase .lib-design:active": {"background": "var(--accent-press)"}},
                         "its size, shape, type and focus ring Details' (.lib-pill), nothing of its own but the colour")
        pill = {name: value for rule in rules if ".lib .lib-pill" in rule.selectors and not rule.conditions for name, value, _ in rule.declarations}
        self.assertEqual((pill["min-height"], pill["padding"], pill["font-size"], pill["border-radius"]), ("36px", "0 18px", "15px", "var(--r-pill)"))
        self.assertIn(".lib-pill:focus-visible { outline:2px solid var(--focus); outline-offset:2px; }", self.style)
        # Beside Details where they fit, else wrapped under it, each its own width: the showcase's pills a row that wraps
        # at every width (not the column of a sensor's page below 900 px).
        self.assertIn(".lib-pills { display:flex; flex-wrap:wrap; gap:10px; }", self.style)
        self.assertIn(".lib-showcase .lib-pills { flex-direction:row; margin-top:8px; }", self.style)
        self.assertIn(".lib .lib-showcase .lib-pill { align-self:flex-start; width:auto; }", self.style)


class RouteTests(HttpTestCase):
    """app.py serves the pages: SECURITY_HEADERS, the header's counts, the query ignored.  Since the user's decision of
    2026-11-16 ("是的 be first page") the Library at / and /index.html, the generator at /gen.html, and at /library.html
    (the Library's address before) the forwarding page, which has no header to count in."""

    def test_the_pages_with_the_counts(self) -> None:
        import app

        counts = {"stars": 1234, "forks": 56}
        for name, paths in (("index.html", ("/", "/index.html", "/?x=1", "/index.html?part=widowx-250-1mm")),
                            ("gen.html", ("/gen.html", "/gen.html?part=widowx-250-1mm")), ("library.html", ("/library.html", "/library.html?x=1"))):
            page = (app.WEB_ROOT / name).read_bytes()
            for path in paths:
                with self.subTest(path=path):
                    self.server.httpd.github_counts = None
                    reply = self.request("GET", path)
                    self.assertEqual((reply.status, reply.headers["content-type"], reply.body), (200, "text/html; charset=utf-8", page))
                    for header, value in app.SECURITY_HEADERS:
                        self.assertEqual(reply.headers[header.lower()], value)
                    self.server.httpd.github_counts = counts
                    reply = self.request("GET", path)
                    if name == "library.html":
                        # No header: the page as it is.
                        self.assertEqual(reply.body, page)
                        self.assertNotIn(b"data-gh-badge", page)
                    else:
                        self.assertEqual(reply.body.decode("utf-8"), app.fill_github_counts(page.decode("utf-8"), counts))
                        self.assertIn("<span data-gh-stars>1.2k</span>", reply.body.decode("utf-8"))
                    for header, value in app.SECURITY_HEADERS:
                        self.assertEqual(reply.headers[header.lower()], value)
                    head = self.request("HEAD", path)
                    self.assertEqual((head.status, head.body, int(head.headers["content-length"])), (200, b"", len(reply.body)))
                    wrong = self.request("POST", path.split("?")[0], {})
                    self.assertEqual((wrong.status, wrong.headers.get("allow"), wrong.json()["code"]), (405, "GET, HEAD", "E_HTTP_METHOD_NOT_ALLOWED"))
                    # The in-browser API answers /api/ only: the pages are the site's files.
                    self.assertEqual(app.answer("GET", path.split("?")[0]).status, 404)
        self.assertEqual(app.PAGES, {"/": "index.html", "/index.html": "index.html", "/gen.html": "gen.html", "/library.html": "library.html"})

    def test_the_forwarding_page_is_never_counted(self) -> None:
        # The review of 2026-11-16: library.html (FORWARD_PAGE) is sent as it is because it is the forwarding page, not
        # because fill_github_counts finds no card in it: one with the header's card still goes out unfilled, while the
        # Library's page in the same folder is counted.
        import app

        self.assertEqual(app.FORWARD_PAGE, "library.html")
        self.assertEqual(build_static_site.FORWARD, app.FORWARD_PAGE)
        card = (app.WEB_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<span data-gh-stars></span>', card)
        with tempfile.TemporaryDirectory() as folder:
            for name in ("index.html", "library.html"):
                (Path(folder) / name).write_text(card, encoding="utf-8")
            self.server.httpd.github_counts = {"stars": 1234, "forks": 56}
            with mock.patch.object(app, "WEB_ROOT", Path(folder)):
                forwarding = self.request("GET", "/library.html")
                library = self.request("GET", "/")
        self.assertEqual((forwarding.status, forwarding.body), (200, card.encode("utf-8")))
        self.assertIn("<span data-gh-stars>1.2k</span>", library.body.decode("utf-8"))

    def test_the_pictures_are_served_as_webp(self) -> None:
        # The Library's pictures (web/library/shots/, the merge of 2026-11-05) as image/webp under nosniff, whatever the
        # host's mimetypes knows (STATIC_TYPES; this host's Python 3.12 had them application/octet-stream).
        import app

        with tempfile.TemporaryDirectory() as folder:
            shots = Path(folder) / "library" / "shots"
            shots.mkdir(parents=True)
            (shots / "widowx-250-2mm.exploded.webp").write_bytes(SHOT)
            with mock.patch.object(app, "WEB_ROOT", Path(folder)):
                reply = self.request("GET", "/static/library/shots/widowx-250-2mm.exploded.webp")
        self.assertEqual((reply.status, reply.headers["content-type"], reply.body), (200, "image/webp", SHOT))
        self.assertEqual(reply.headers["x-content-type-options"], "nosniff")

    def test_the_art_is_served_as_the_gzip_it_is(self) -> None:
        # The 3D view's art (web/library/art/<id>.json.gz, the merge of 2026-11-05) as application/gzip with no
        # Content-Encoding, as GitHub Pages sends it (the page inflates it itself), under nosniff, not as the host's
        # mimetypes guesses it (JSON).
        import app

        data = library_write.art_bytes(_art("widowx-250-2mm", "surface-13x13-000000000000"))
        with tempfile.TemporaryDirectory() as folder:
            art = Path(folder) / "library" / "art"
            art.mkdir(parents=True)
            (art / "widowx-250-2mm.json.gz").write_bytes(data)
            with mock.patch.object(app, "WEB_ROOT", Path(folder)):
                reply = self.request("GET", "/static/library/art/widowx-250-2mm.json.gz")
        self.assertEqual((reply.status, reply.headers["content-type"], reply.body), (200, "application/gzip", data))
        self.assertNotIn("content-encoding", reply.headers)
        self.assertEqual(reply.headers["x-content-type-options"], "nosniff")

class SiteBuildTests(unittest.TestCase):
    """tools/build_static_site.py: the Library's page (index.html, the first page since 2026-11-16) with the site's head
    tags, the Library's gate and its prebuilt ZIPs."""

    def test_the_library_page_has_the_sites_head_tags_and_counts(self) -> None:
        # The first page since the user's decision of 2026-11-16, its default; the generator (gen.html) the same tags and
        # counts; library.html, the forwarding page, the tags alone (no header, no counts, even when the build has them).
        self.assertEqual(build_static_site.PAGES, ("index.html", "gen.html", "library.html"))
        self.assertEqual(build_static_site.FORWARD, "library.html")
        for name, title in (("index.html", "Library · FlexiTac-Gen"), ("gen.html", "FlexiTac-Gen"), ("library.html", "Library · FlexiTac-Gen")):
            with self.subTest(page=name):
                built = build_static_site.page(name=name)
                head = built.split("</head>", 1)[0]
                self.assertTrue(head.startswith('<!doctype html>\n<html lang="en">\n  <head>\n    <meta charset="utf-8" />\n    <meta http-equiv="Content-Security-Policy"'))
                self.assertEqual(head.count("Content-Security-Policy"), 1)
                self.assertEqual(head.count('<meta name="flexitac-backend" content="browser" />'), 1)
                self.assertIn(f"<title>{title}</title>", head)
                counted = build_static_site.page({"stars": 159, "forks": 17}, name)
                if name == "library.html":
                    self.assertEqual(counted, built)
                    continue
                self.assertIn('<span data-gh-stars>159</span>', counted)
                self.assertNotIn("data-gh-stats hidden>", counted)
        self.assertEqual(build_static_site.page(), build_static_site.page(name="index.html"))
        self.assertIn("Library · FlexiTac-Gen", build_static_site.page())
        # The Library's gate reads the generator's defaults from its page.
        self.assertEqual(inspect.signature(build_static_site.library).parameters["index"].default, WEB / "gen.html")
        self.assertEqual(library_write.INDEX, WEB / "gen.html")

    def test_the_pages_are_not_copied_under_static(self) -> None:
        with mock.patch.object(build_static_site.shutil, "copytree") as copy:
            build_static_site.copy_web(Path("static"))
        ignore = copy.call_args.kwargs["ignore"]
        # The Library's pictures are published with web/ (static/library/shots/); the forwarding script is (static/).
        names = ["index.html", "gen.html", "library.html", "forward.js", "library.js", "library.css", "theme.js", "app.py", "__pycache__", "entries.json", "manifest.json",
                 "widowx-250-2mm.exploded.webp", "widowx-250-2mm.exploded.card.webp",
                 # The 3D view's files (2026-11-05): the art, the scenes and their bodies, the view's modules.
                 "widowx-250-2mm.json.gz", "scenes.json", "widowx-250.json", "rail.stl", "library_view.js", "library_stage.js"]
        self.assertEqual(sorted(ignore(str(WEB), names)), ["__pycache__", "app.py", "gen.html", "index.html", "library.html"])

    def test_the_site_holds_the_3d_views_files(self) -> None:
        # The Library's 3D view draws from the site's own files (no engine, no API): web/library/'s art, scenes and
        # bodies under static/library/, with the view's modules under static/cad/.
        entries = _json(LIBRARY / "entries.json")
        index = _json(LIBRARY / library_write.SCENES_INDEX)
        with tempfile.TemporaryDirectory() as folder:
            static = Path(folder) / "static"
            build_static_site.copy_web(static)
            self.assertEqual((static / "library" / library_write.SCENES_INDEX).read_bytes(), (LIBRARY / library_write.SCENES_INDEX).read_bytes())
            for path in index["scenes"].values():
                with self.subTest(scene=path):
                    self.assertEqual((static / "library" / path).read_bytes(), (LIBRARY / path).read_bytes())
                    for body in _json(LIBRARY / path)["bodies"]:
                        self.assertEqual(hashlib.sha256((static / "library" / body["mesh"]).read_bytes()).hexdigest(), body["sha256"])
            for identifier, variant in entries["variants"].items():
                if variant["view"]:
                    with self.subTest(art=identifier):
                        self.assertEqual((static / "library" / variant["view"]["art"]).read_bytes(), (LIBRARY / variant["view"]["art"]).read_bytes())
            for path in library_write.VIEW_SOURCES:
                if (WEB / path).is_file():
                    self.assertTrue((static / path).is_file(), path)
            # The showcase (2026-11-12): its scene, the holder and the vendor's folder, whole and nothing more, where the
            # scene's paths find them (static/library/../vendor/ufactory-g1/).
            scene = _json(static / "library" / SHOWCASE_SCENE)
            self.assertEqual((static / "library" / SHOWCASE_SCENE).read_bytes(), (LIBRARY / SHOWCASE_SCENE).read_bytes())
            for body in scene["bodies"]:
                with self.subTest(showcase=body["mesh"]):
                    self.assertEqual(hashlib.sha256((static / "library" / body["mesh"]).read_bytes()).hexdigest(), body["sha256"])
            self.assertEqual({path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (static / "vendor" / "ufactory-g1").iterdir()
                              if path.name != "NOTICE.md"}, SHOWCASE_FILES)
            self.assertEqual((static / "vendor" / "ufactory-g1" / "NOTICE.md").read_bytes(), (SHOWCASE / "NOTICE.md").read_bytes())
            # Its page's document and pictures, and what the document's paths name, each found from static/library/ as
            # the page asks for it: the placed record's art and finger, the two notices.
            document = _json(static / "library" / SHOWCASE_FILE)
            self.assertEqual((static / "library" / SHOWCASE_FILE).read_bytes(), (LIBRARY / SHOWCASE_FILE).read_bytes())
            for kind in ("exploded", "assembled", "card"):
                with self.subTest(picture=kind):
                    self.assertEqual(hashlib.sha256((static / "library" / document["image"][kind]["src"]).read_bytes()).hexdigest(), document["image"][kind]["sha256"])
            for path in (document["placed"]["art"], document["placed"]["mesh"]["file"], document["placed"]["scene"],
                         *(item["notice"] for item in document["sources"])):
                with self.subTest(named=path):
                    self.assertTrue((static / "library" / path).is_file())
            self.assertEqual(hashlib.sha256((static / "library" / document["placed"]["mesh"]["file"]).read_bytes()).hexdigest(), document["placed"]["mesh"]["sha256"])

    def test_the_gate_writes_the_exports_and_their_record(self) -> None:
        import app

        entries = _json(LIBRARY / "entries.json")
        with tempfile.TemporaryDirectory() as folder:
            static = Path(folder) / "static"
            record = build_static_site.library(static, only=["umi-finray-2mm", "widowx-250-1mm"])
            files = _json(static / "library" / "files.json")
            self.assertEqual(record, {"variants": 2, "files_json_sha256": hashlib.sha256((static / "library" / "files.json").read_bytes()).hexdigest(),
                                      "pictured": sum(1 for identifier in ("umi-finray-2mm", "widowx-250-1mm") if entries["variants"][identifier]["image"]),
                                      "viewed": sum(1 for identifier in ("umi-finray-2mm", "widowx-250-1mm") if entries["variants"][identifier]["view"]),
                                      "showcase": "flexitac-g1"})
            self.assertEqual((files["format"], sorted(files["variants"])), ("flexitac-library-files/v1", ["umi-finray-2mm", "widowx-250-1mm"]))
            for identifier, listed in files["variants"].items():
                variant = entries["variants"][identifier]
                design = json.loads((LIBRARY / variant["fit"]).read_text(encoding="utf-8"))["reply"]["proposals"][0]["design"]
                self.assertEqual(listed["build_id"], variant["build_id"])
                for kind in ("top-gerber", "bottom-gerber"):
                    with self.subTest(variant=identifier, kind=kind):
                        answer = app.answer("POST", f"/api/export/{kind}", "application/json", json.dumps(design).encode("utf-8"))
                        name = re.search(r'filename="([^"]+)"', dict(answer.headers)["Content-Disposition"]).group(1)
                        data = (static / "library" / listed[kind]["path"]).read_bytes()
                        self.assertEqual(data, answer.body)
                        self.assertEqual(listed[kind], {"path": f"files/{identifier}/{name}", "name": name, "bytes": len(data),
                                                        "sha256": hashlib.sha256(data).hexdigest()})
            self.assertEqual(sorted(path.name for path in (static / "library" / "files").iterdir()), ["umi-finray-2mm", "widowx-250-1mm"])

    def test_a_stale_showcase_stops_the_build(self) -> None:
        # The showcase is no sensor: whichever sensors are built, a problem of its scene, its folder or its page
        # (library_write.showcase(), carried by scenes() with no part) stops the build and nothing is written; pictures of
        # older figure or view sources are published with a warning (the build runs no browser).
        with tempfile.TemporaryDirectory() as folder:
            static = Path(folder) / "static"
            with mock.patch.object(library_write, "showcase", return_value=([ShowcaseTests.STALE], set(SHOWCASE_BODIES))):
                with self.assertRaisesRegex(build_static_site.BuildError, re.escape(
                        "the library's scenes are stale (showcase.json: its pictures are of another scene or rules than the files now")):
                    build_static_site.library(static, only=["widowx-250-1mm"])
            self.assertFalse((static / "library" / "files.json").exists(), "nothing written")
            said = io.StringIO()
            with mock.patch.object(library_write, "showcase_page", return_value=([], True)), contextlib.redirect_stderr(said):
                record = build_static_site.library(static, only=["widowx-250-1mm"])
            self.assertEqual(record["showcase"], "flexitac-g1")
            self.assertIn("build_static_site: warning: the showcase's pictures are of older figure or view sources: "
                          "re-shoot with tools/browser/library_shots.py --showcase\n", said.getvalue())
        # A library without the showcase's document (the tests' own) has none.
        self.assertIn('showcase = library_write.SHOWCASE_ID if (source / library_write.SHOWCASE_FILE).is_file() else None',
                      (ROOT / "tools" / "build_static_site.py").read_text(encoding="utf-8"))

    def test_a_stale_fit_stops_the_build(self) -> None:
        # A copy of one sensor's files (not the UMI finger's: its fit and mesh live in web/vendor/umi): its reply changed
        # with entries.json naming the changed file (the fit again differs), then the file alone changed.
        identifier = "widowx-250-2mm"
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "library"
            (source / "fits").mkdir(parents=True)
            (source / "meshes").mkdir()
            shutil.copy(LIBRARY / "meshes" / "widowx-250.stl", source / "meshes" / "widowx-250.stl")
            shutil.copy(LIBRARY / "parts.json", source / "parts.json")
            _scene_library(source, _json(LIBRARY / "parts.json"))
            entries = _json(LIBRARY / "entries.json")
            # The copy holds no pictures and no art: its sensor has neither (else the gate stops at its image or, once the
            # shoot has given it a 3D view, at its view first).
            entries["variants"][identifier]["image"] = None
            entries["variants"][identifier]["view"] = None
            document = _json(LIBRARY / "fits" / f"{identifier}.json")
            document["reply"]["proposals"][0]["metrics"]["taxels"] += 1
            data = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
            (source / "fits" / f"{identifier}.json").write_bytes(data)
            entries["variants"][identifier]["fit_sha256"] = hashlib.sha256(data).hexdigest()
            (source / "entries.json").write_text(json.dumps(entries), encoding="utf-8")
            with self.assertRaisesRegex(build_static_site.BuildError, r"the library is stale \(widowx-250-2mm\): run tools/library_write.py"):
                build_static_site.library(Path(folder) / "static", source=source, only=[identifier])
            entries["variants"][identifier]["fit_sha256"] = _json(LIBRARY / "entries.json")["variants"][identifier]["fit_sha256"]
            (source / "entries.json").write_text(json.dumps(entries), encoding="utf-8")
            with self.assertRaisesRegex(build_static_site.BuildError, "stale"):
                build_static_site.library(Path(folder) / "static", source=source, only=[identifier])
            self.assertFalse((Path(folder) / "static" / "library" / "files.json").exists(), "nothing written")
            with self.assertRaisesRegex(build_static_site.BuildError, "no sensor named nothing-1mm"):
                build_static_site.library(Path(folder) / "static", source=source, only=["nothing-1mm"])

    @PICTURES_ONLY
    def test_a_picture_of_another_fit_stops_the_build(self) -> None:
        # One sensor's files (as test_a_stale_fit_stops_the_build) and its pictures (the fixture): a picture of another
        # fit stops the build, so does an image in entries.json that is not its picture's; a picture of older figure
        # sources is published with a warning (the build runs no browser to shoot it again).
        identifier = "widowx-250-2mm"
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "library"
            (source / "fits").mkdir(parents=True)
            (source / "meshes").mkdir()
            shutil.copy(LIBRARY / "meshes" / "widowx-250.stl", source / "meshes" / "widowx-250.stl")
            shutil.copy(LIBRARY / "parts.json", source / "parts.json")
            shutil.copy(LIBRARY / "fits" / f"{identifier}.json", source / "fits" / f"{identifier}.json")
            _scene_library(source, _json(LIBRARY / "parts.json"))
            entries = _json(LIBRARY / "entries.json")
            entries["variants"][identifier]["image"] = IMAGE_OF_WIDOWX
            entries["variants"][identifier]["view"] = None
            (source / "entries.json").write_text(json.dumps(entries), encoding="utf-8")
            static = Path(folder) / "static"
            _shot_library(source, entries["variants"], fit_sha256="another")
            with self.assertRaisesRegex(build_static_site.BuildError, re.escape(
                    "the library's pictures are stale (widowx-250-2mm: its pictures are of another fit (the wrong sensor pictured)")):
                build_static_site.library(static, source=source, only=[identifier])
            _shot_library(source, entries["variants"])
            entries["variants"][identifier]["image"] = None
            (source / "entries.json").write_text(json.dumps(entries), encoding="utf-8")
            with self.assertRaisesRegex(build_static_site.BuildError, re.escape(
                    "the library is stale (widowx-250-2mm: its image is not the one shots/manifest.json gives): run tools/library_write.py")):
                build_static_site.library(static, source=source, only=[identifier])
            self.assertFalse((static / "library" / "files.json").exists(), "nothing written")
            entries["variants"][identifier]["image"] = IMAGE_OF_WIDOWX
            (source / "entries.json").write_text(json.dumps(entries), encoding="utf-8")
            _shot_library(source, entries["variants"], figure_sha256="0" * 64)
            said = io.StringIO()
            with contextlib.redirect_stderr(said):
                record = build_static_site.library(static, source=source, only=[identifier])
            self.assertEqual((record["pictured"], record["viewed"]), (1, 0))
            # The picture's record names no art: published without its 3D view, a warning too.
            self.assertEqual(said.getvalue(), f"build_static_site: warning: {library_write.older_note([identifier])}\n"
                                              f"build_static_site: warning: {library_write.view_note([identifier])}\n")

    def test_a_stale_3d_view_stops_the_build(self) -> None:
        # One gripper's sensor with its pictures, its art and its stage (the tiny ones): published with its 3D view; an
        # art not the record's, a view in entries.json not the manifest's or a scene that scenes() refuses stops the build
        # (the scenes of the parts not built aside); nothing written.
        identifier = "widowx-250-2mm"
        parts = _json(LIBRARY / "parts.json")
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "library"
            (source / "fits").mkdir(parents=True)
            (source / "meshes").mkdir()
            shutil.copy(LIBRARY / "meshes" / "widowx-250.stl", source / "meshes" / "widowx-250.stl")
            shutil.copy(LIBRARY / "parts.json", source / "parts.json")
            shutil.copy(LIBRARY / "fits" / f"{identifier}.json", source / "fits" / f"{identifier}.json")
            entries = _json(LIBRARY / "entries.json")
            _view_library(source, entries["variants"], parts, identifiers=(identifier,))
            entries["variants"][identifier]["image"] = dict(IMAGE_OF_WIDOWX, alt=f"WidowX 250, 2 mm {PICTURE}")
            entries["variants"][identifier]["view"] = {"art": f"art/{identifier}.json.gz", "scene": "scenes/widowx-250.json"}
            (source / "entries.json").write_text(json.dumps(entries), encoding="utf-8")
            static = Path(folder) / "static"
            notice = (source / "NOTICE.md").read_text(encoding="utf-8")

            def build(**changes):
                with mock.patch.object(library_write, "view_sha256", return_value=VIEW):
                    return build_static_site.library(static, source=source, only=[identifier])

            # Another part's scene refused does not stop this sensor's build.
            (source / "NOTICE.md").write_text("".join(line for line in notice.splitlines(True) if "bodies/arx-x5/" not in line), encoding="utf-8")
            record = build()
            self.assertEqual((record["pictured"], record["viewed"]), (1, 1))
            shutil.rmtree(static)
            (source / "NOTICE.md").write_text("".join(line for line in notice.splitlines(True) if "bodies/widowx-250/" not in line), encoding="utf-8")
            with self.assertRaisesRegex(build_static_site.BuildError, re.escape(
                    "the library's scenes are stale (scenes/widowx-250.json: body 1: bodies/widowx-250/body.stl has no row of NOTICE.md with its SHA-256")):
                build()
            (source / "NOTICE.md").write_text(notice, encoding="utf-8")
            entries["variants"][identifier]["view"] = None
            (source / "entries.json").write_text(json.dumps(entries), encoding="utf-8")
            with self.assertRaisesRegex(build_static_site.BuildError, re.escape(
                    f"the library is stale ({identifier}: its 3D view is not the one shots/manifest.json gives): run tools/library_write.py")):
                build()
            art = source / "art" / f"{identifier}.json.gz"
            art.write_bytes(gzip.compress(gzip.decompress(art.read_bytes()), mtime=1))
            with self.assertRaisesRegex(build_static_site.BuildError, re.escape(
                    f"the library's pictures are stale ({identifier}: art/{identifier}.json.gz is not the file shots/manifest.json names: "
                    f"re-shoot with tools/browser/library_shots.py --only {identifier})")):
                build()
            self.assertFalse((static / "library" / "files.json").exists(), "nothing written")

    def test_a_fit_of_a_request_the_page_no_longer_sends_stops_the_build(self) -> None:
        # The review of 2026-11-05: with a page default changed (Proposals 4, not 5) the committed fit still re-fits to
        # its own reply, but Gen by Surface would send another request and fit again in place of the shipped fit.
        index = (WEB / "gen.html").read_text(encoding="utf-8")
        control = 'data-option="proposals" value="5"'
        self.assertEqual(index.count(control), 1)
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "gen.html"
            changed.write_text(index.replace(control, 'data-option="proposals" value="4"'), encoding="utf-8")
            with self.assertRaisesRegex(build_static_site.BuildError,
                                        r"the library is stale \(widowx-250-2mm\): run tools/library_write.py \(its request is not the one the page sends\)"):
                build_static_site.library(Path(folder) / "static", only=["widowx-250-2mm"], index=changed)
            self.assertFalse((Path(folder) / "static" / "library" / "files.json").exists(), "nothing written")


if __name__ == "__main__":
    unittest.main()
