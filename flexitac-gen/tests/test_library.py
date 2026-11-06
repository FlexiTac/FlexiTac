"""The Library (web/library/, the user's requests of 2026-11-05): static checks of its data that need no browser.

- Files: every file of web/library/ is a third-party file of its NOTICE.md table, whose SHA-256 re-hashes, or one of
  this project's own (NOTICE.md, parts.json, entries.json, fits/<id>.json, the pictures shots/<id>.exploded.webp,
  shots/<id>.assembled.webp, shots/<id>.exploded.card.webp and shots/manifest.json); every tabled file
  exists; no file anywhere under web/ is one of the deny-list's vendor models (Robotiq 2F-85 and 3F, the xArm
  gripper), and no id, title or file name names them; web/library/ stays within its 12 MB budget, its pictures within
  theirs (8 MB, the grid's first screen about 1 MB).
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
  label, at most 45 characters), the shelf headings name the pitches in one wording ('Four pitches, 1 to 3 mm.', the
  user's decision of 2026-11-05), 'start' holds each part's 2 mm sensor (the page's layout of 2026-11-06: one card per
  gripper but the UMI finger, opening its 2 mm sensor, then the UMI finger's shelf).
- The page's request: every fit's request is the one the page sends (library_write.compose of the part, the variant
  and index.html's options; the mesh's file name, no unit, 32 rows and columns at most, numbers as the browser writes
  them), the UMI finger's 2 mm one the page's shipped default fit itself; the options are exactly the Resolution
  step's enabled controls (a parser of this module's own) at their defaults, but the pitch, the fill and the part's
  own, each one the control takes (min, max, step, in decimal).
- Product rules on every committed proposal #1, without fitting: one tail pin per line (reader none), field-only
  containment, the tails centred and ending together, a symmetric face's sensor centred, a build with no error or
  warning and the same build id; rules() names each broken rule on tampered replies.
- Staleness: each part's 2 mm sensor fitted again gives the committed reply, and one tapered tip's (the site build
  re-fits them all).
- The tapered tips (the family umi-tapers, cut by the private tools/library_tips.py): the family complete (two shapes
  by five tip widths, each once, its default one of them) and closing the UMI finger's shelf, no shelf or card of its
  own; each tip's change a tip cut tabled as a modified file; its setup the video's (the contact face grown
  flat from a facet of it under the face point, the base at the mount end, no border, the page's options).
- tools/library_write.py is public (export_public.PUBLIC) and tools/library_import.py and tools/library_tips.py are
  not (the tips' tool needs trimesh and manifold3d: never imported here); the deny-list is the writer's, equal to this
  module's, and the importer keeps no copy of its own but takes the writer's; the new files parse as Python 3.9.

- The page (library.html, library.js, library.css): its one script and three style sheets by relative URLs, nothing
  inline, unique ids; its header the generator's (the title block and the community links byte for byte, the mode
  switch as two links); the header's Library link on both pages (index.html: a new tab; library.html: the current
  page), its style in dated blocks beside the header's rules; never "CAD"; no IntersectionObserver, scroll timeline,
  smooth scrolling, window scroll listener or absolute URL in the script, no transition, animation, fixed or sticky box
  in the style sheet, the action blue only on Open in Gen by Surface, a sensor's picture 3:1 below 900 px (the
  user's decision of 2026-11-05: Open in a phone's first screen) and 16:10 elsewhere; node --check when node is there.
- main.js's ./?part=<id>: DEFAULT_PART and runFit's shipped test as they were, the index and the parameter read, the
  sensor built from its fit's own request, the user's own file and Remove model leaving it, the file note's prefix.
- app.py serves /library.html (any query) with its security headers and the header's counts; POST is a 405; its
  pictures as image/webp (the merge of 2026-11-05).
- tools/build_static_site.py: library.html with the site's head tags and counts, neither page copied under static/, the
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

BUDGET_BYTES = 12_000_000
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
    "6c59aabbd22823819af1face17752cfd5b32f43529ed08da9596148770de332f": "xArm (Gripper G1 3D File (With).stl)",
    # The MakerMods Metal Arm's gripper body, not cleared (2026-11-05: its tips are drawn on the project's own rail).
    "19ab43c406f349d62dc7a9932b66fb28053cf96152ab00d71a93945a43ddd8cd": "MakerMods Metal Arm (gripper_base.STL): not cleared",
    "3c813623f4c273bfb6f4fd483fc8ee23dc4325de32e9d89d7c44cb1a0e97c033": "MakerMods Metal Arm (link7.STL): not cleared",
    "62d0ed4072aea7e4d0655e16edbf8243317e3e106996f00f06e72afc78d091ec": "MakerMods Metal Arm (link8.STL): not cleared",
}
DENIED_NAME = re.compile(r"robotiq|xarm|ufactory", re.IGNORECASE)
NOTICE_ROW = re.compile(r"^\| `([\w./-]+)` \|([^|\n]*)\|([^|\n]*)\|([^|\n]*)\| `([0-9a-f]{64})` \|$", re.MULTILINE)
# Since the 3D view of 2026-11-05 (docs/LIBRARY_VIEW.md): each sensor's art, the scenes and the MakerMods scene's rail,
# drawn by the project (the grippers' other bodies are third-party files, tabled in NOTICE.md).
OWN_FILE = re.compile(r"^(NOTICE\.md|parts\.json|entries\.json|fits/[a-z0-9.-]+\.json|shots/manifest\.json"
                      r"|shots/[a-z0-9.-]+\.(exploded|assembled|exploded\.card)\.webp"
                      r"|art/[a-z0-9.-]+\.json\.gz|scenes/[a-z0-9-]+\.json|bodies/makermods-metal/rail\.stl)$")
# The pictures' budgets (2026-11-05): the whole set (126 files of 42 sensors), and the grid's first screen: since the
# layout of 2026-11-06 every card of the grid (the grippers' seven, then the UMI shelf's four pitches and its Tapered
# tips card), all asked for as the page opens (it is short; library_checks part_pictures measures the bytes).
SHOTS_BUDGET_BYTES = 8_000_000
FIRST_SCREEN_BYTES = 1_000_000
FIXTURES = ROOT / "tests" / "fixtures"
# The contract of the pictures (the Library's UI and tools/browser/library_shots.py were built against it, 2026-11-05).
IMAGE_OF_WIDOWX = {"exploded": {"src": "shots/widowx-250-2mm.exploded.webp", "card": "shots/widowx-250-2mm.exploded.card.webp",
                                "width": 1280, "height": 800},
                   "assembled": {"src": "shots/widowx-250-2mm.assembled.webp", "width": 1280, "height": 800},
                   "alt": "WidowX 250, 2 mm on the part"}
NOTE_PREFIX = "From the Library: "
NOTE_MAX = 45
# main.js reads the index here (LIBRARY_INDEX, static/ being web/).
LIBRARY_INDEX_PATH = "library/entries.json"
# The tapered tips (tools/library_tips.py): the family, its shapes and tip widths, and the video's face and base.
TAPERS = "umi-tapers"
TAPER_SHAPES = {"trap": "trapezoid", "convex": "convex arc"}
TAPER_TIPS = ("21.8", "17.8", "13.8", "9.8", "5.8")
FACE_POINT = (0.0, -12.9, -62.7)
MOUNT_BASE = {"point_xyz": [0, -12.9, -3]}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def grid_cards(entries: dict) -> list:
    """The sensors whose card pictures the grid shows (library.js, the layout of 2026-11-06), in the page's order: one
    card per gripper but the shelved (its default, the 2 mm sensor), then each shelved part's (the UMI finger's, and any
    a family closes) variants and its families' defaults."""
    shelved = {"umi-finray"} | {family["shelf"] for family in entries["families"].values()}
    cards = [entries["parts"][part]["default"] for part in entries["order"] if part not in shelved]
    for part in (part for part in entries["order"] if part in shelved):
        cards += entries["parts"][part]["variants"] + [family["default"] for family in entries["families"].values() if family["shelf"] == part]
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
                             "ghost_cover_min": 0.02}}
# The near finger (the mate) see-through on every gripper (the user's decision of 2026-11-06).
SEE_THROUGH = {"franka-hand": ["mate"], "widowx-250": ["mate"], "trossen-widowx-ai": ["mate"], "arx-x5": ["mate"], "i2rt-yam": ["mate"],
               "unitree-dex1": ["mate"], "makermods-metal": ["mate"]}
MATE_KINDS = {"franka-hand": "turned", "widowx-250": "turned", "trossen-widowx-ai": "mirror", "arx-x5": "mirror", "i2rt-yam": "mirror",
              "unitree-dex1": "turned", "makermods-metal": "turned"}
PICTURE = "on both fingers of the open gripper"
RAIL = "bodies/makermods-metal/rail.stl"
PICTURES = {"makermods-metal": "on both fingertips on a plain rail"}
IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
TURNED = [[-1, 0, 0, 0], [0, -1, 0, -80], [0, 0, 1, 0], [0, 0, 0, 1]]
MIRROR = [[-1, 0, 0, -88], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
# The hash of the Library view's modules the tiny records are shot with (pictures(view=...): the modules need not exist).
VIEW = "5" * 64
REBUILD = "rebuild the scenes with the private tools/library_scenes.py"
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
    with the manifest the tool writes for them (its record() and manifest_text(), at the figure's sources of now),
    ``changes`` over each record."""

    (library / "shots").mkdir(parents=True, exist_ok=True)
    records = {}
    for identifier in identifiers:
        data = dict({"exploded": SHOT, "assembled": SHOT, "card": SHOT_CARD}, **(files or {}))
        for kind, payload in data.items():
            (library / library_write.shot_files(identifier)[kind][0]).write_bytes(payload)
        margins = {"exploded": [590, 240, 590, 240], "assembled": [590, 240, 590, 240]}
        records[identifier] = dict(SHOTS_TOOL.record(identifier, variants[identifier], data, margins, library_write.figure_sha256(), "photo"),
                                   **changes)
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
    parser.feed((WEB / "index.html").read_text(encoding="utf-8"))
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
        self.assertEqual(scenes, {library_write.SCENES_INDEX, *index["scenes"].values()})
        named = {body["mesh"] for path in index["scenes"].values() for body in _json(LIBRARY / path)["bodies"]}
        bodies = {path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "bodies").rglob("*") if path.is_file()} if (LIBRARY / "bodies").is_dir() else set()
        self.assertEqual(bodies, named)
        rows = _notice()
        for mesh in sorted(named):
            with self.subTest(body=mesh):
                self.assertTrue(mesh in rows or mesh == RAIL, "a body neither tabled in NOTICE.md nor the project's own rail")
        self.assertNotIn(RAIL, rows, "the rail is the project's own (NOTICE.md says so, with no row)")
        # Each view's scene its part's (a gripper's), a fingertip's none.
        for identifier, variant in self.entries["variants"].items():
            if variant["view"]:
                with self.subTest(view=identifier):
                    self.assertEqual(variant["view"], library_write.view_record(identifier, index["scenes"].get(variant["part"])))

    def test_no_vendor_model_of_the_deny_list(self) -> None:
        for path in sorted(WEB.rglob("*")):
            if path.is_file():
                with self.subTest(file=path.relative_to(WEB).as_posix()):
                    self.assertNotIn(hashlib.sha256(path.read_bytes()).hexdigest(), DENIED_SHA256)
                    if LIBRARY in path.parents:
                        self.assertIsNone(DENIED_NAME.search(path.name))
        names = [*self.entries["order"], *self.entries["variants"]]
        for part in self.parts["parts"].values():
            names += [part["title"], part["mesh"]["file"], part["mesh"]["name"]]
        for name in names:
            with self.subTest(name=name):
                self.assertIsNone(DENIED_NAME.search(name))

    def test_the_library_stays_within_its_budget(self) -> None:
        # Its pictures have their own (below).
        size = sum(path.stat().st_size for path in LIBRARY.rglob("*") if path.is_file() and path.parent != LIBRARY / "shots")
        self.assertLessEqual(size, BUDGET_BYTES, f"web/library/ is {size} bytes")

    def test_the_pictures_stay_within_their_budget(self) -> None:
        shots = sorted((LIBRARY / "shots").glob("*")) if (LIBRARY / "shots").is_dir() else []
        size = sum(path.stat().st_size for path in shots)
        self.assertLessEqual(size, SHOTS_BUDGET_BYTES, f"web/library/shots/ is {size} bytes")
        first = sum((LIBRARY / self.entries["variants"][identifier]["image"]["exploded"]["card"]).stat().st_size
                    for identifier in grid_cards(self.entries) if self.entries["variants"][identifier]["image"])
        self.assertLessEqual(first, FIRST_SCREEN_BYTES, f"the grid's first screen's pictures are {first} bytes")

    def test_the_page_never_says_cad(self) -> None:
        # The page's word is Gen by Surface; the Library shows these texts (its notice is linked from its footer).
        for path in (LIBRARY / "NOTICE.md", LIBRARY / "parts.json", LIBRARY / "entries.json"):
            with self.subTest(file=path.name):
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
                    self.assertRegex(licence["change"], r"^tip cut \((trapezoid|convex arc), h 75 mm, tip [\d.]+ mm\) from UMI-Soft-Gripper-Finger\.stl$")
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
                    # A tip's own label (its one pitch is the family's): 'UMI trapezoid tip, 13.8 mm'.
                    tip = re.fullmatch(r"umi-(trap|convex)-tip([\d.]+)", variant["part"])
                    self.assertEqual(variant["label"], f"UMI {TAPER_SHAPES[tip.group(1)]} tip, {tip.group(2)} mm")
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
                hosted = "".join(f", and {family['title'].lower()}" for family in self.entries["families"].values() if family["shelf"] == part_id)
                # One wording on every shelf (the user's decision of 2026-11-05, 最好统一): the count and the range, a
                # shelf closing with families naming them after it; every gripper's pitches begin at 1 mm.
                shelf = re.fullmatch(r"(\w+) pitches, ([\d.]+) to ([\d.]+) mm%s\." % re.escape(hosted), part["shelf"])
                self.assertIsNotNone(shelf, part["shelf"])
                self.assertEqual((words[shelf.group(1)], float(shelf.group(2)), float(shelf.group(3))),
                                 (len(pitches), min(pitches), max(pitches)))
                self.assertEqual(min(pitches), 1)
        self.assertEqual({part_id: part["shelf"] for part_id, part in self.entries["parts"].items() if part_id in self.entries["order"]},
                         {"umi-finray": "Four pitches, 1 to 3 mm, and tapered tips.", "franka-hand": "Four pitches, 1 to 2.5 mm.",
                          "widowx-250": "Four pitches, 1 to 3 mm.", "trossen-widowx-ai": "Four pitches, 1 to 3 mm.", "arx-x5": "Four pitches, 1 to 4 mm.",
                          "i2rt-yam": "Four pitches, 1 to 4 mm.", "unitree-dex1": "Four pitches, 1 to 3 mm.", "makermods-metal": "Four pitches, 1 to 3 mm."})
        # The writer's wording itself, on shelves the Library does not have: one pitch, two with no family, one family.
        family = {"title": "Tapered tips"}
        self.assertEqual([library_write.shelf([{"pitch_mm": 2}]), library_write.shelf([{"pitch_mm": 2.5}, {"pitch_mm": 1.5}]),
                          library_write.shelf([{"pitch_mm": 2}, {"pitch_mm": 1}, {"pitch_mm": 4}], [family])],
                         ["One pitch, 2 mm.", "Two pitches, 1.5 to 2.5 mm.", "Three pitches, 1 to 4 mm, and tapered tips."])
        # The grid's cards and shelves are the grippers' (the family's parts are one card on the UMI shelf); "start" is
        # each one's 2 mm sensor, the sensor its card opens (the page's layout of 2026-11-06).
        self.assertEqual(self.entries["order"], [part for part in self.parts["order"] if not self.parts["parts"][part].get("family")])
        self.assertEqual(self.entries["order"], ["umi-finray", "franka-hand", "widowx-250", "trossen-widowx-ai", "arx-x5", "i2rt-yam",
                                                 "unitree-dex1", "makermods-metal"])
        self.assertEqual(self.entries["start"], [self.entries["parts"][part]["default"] for part in self.entries["order"]])
        self.assertEqual(len(self.entries["variants"]), 42, "8 grippers by 4 pitches and 10 tapered tips")


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
            self.assertEqual(run(self.entries["variants"]), (0, [unviewed, "library_write: 42 sensors, all current, each with its picture, 0 with a 3D view"]))
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
        # the project's own plain rail, never its body.  The user's decision of 2026-11-06: the near finger (the mate)
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
                    self.assertEqual(meshes, [RAIL], "the project's own rail, no MakerMods body")
                    self.assertIn("not MakerMods hardware", scene["about"])
                else:
                    self.assertNotIn(RAIL, meshes)
                self.assertNotIn("camera", scene, "the approved homes (Exploded 65, Assembled 57 degrees)")
                self.assertNotIn("explode", scene, "the approved explode (the rules' gap share)")
        self.assertEqual(sorted(path.relative_to(LIBRARY).as_posix() for path in (LIBRARY / "bodies" / "makermods-metal").iterdir()), [RAIL])

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
            (lambda scene: scene.update(cad=True), f"{name} has not the keys {', '.join(library_write.SCENE_KEYS)} (and camera, explode)"),
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
             "gap_share, ghost_opacity, measure_px, min_step_mm, see_through_modes"),
            (lambda index: index["rules"].pop("explode_stacks"), "scenes/scenes.json: its rules have not the keys camera, checks, depth_tol_mm, explode_stacks, "
             "gap_share, ghost_opacity, measure_px, min_step_mm, see_through_modes"),
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
            self.assertEqual((data[:4], data[4:8], library_write.read_art(data)["id"]), (b"\x1f\x8b\x08\x00", bytes(4), self.GRIPPER))
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


class RequestTests(LibraryTestCase):
    def test_every_fit_is_of_the_request_the_page_sends(self) -> None:
        options = library_write.page_options((WEB / "index.html").read_text(encoding="utf-8"))
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
        options = library_write.page_options((WEB / "index.html").read_text(encoding="utf-8"))
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
        found = library_write.controls((WEB / "index.html").read_text(encoding="utf-8"))
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
        # off (syncObjective, syncContainment), whatever index.html says (the review of 2026-11-05).
        html = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertFalse(any(control["disabled"] for control in library_write.controls(html).values()))
        for key, element in (("edge_margin_mm", 'id="cadEdgeMargin"'), ("pitch_mm", 'id="cadPitch"'), ("row_sides", 'id="cadRowSides"')):
            with self.subTest(option=key):
                self.assertEqual(html.count(element), 1)
                options = library_write.page_options(html.replace(element, f"{element} disabled", 1))
                self.assertEqual(key in options, key in library_write.SYNCED)

    def test_compose_refuses_what_the_page_would_send_otherwise(self) -> None:
        # parts.json is edited by hand: a setup main.js buildDefaultSensor would send another way is refused, not
        # composed (only the browser checks would see it: the writer, the tests and the site build would agree).
        options = library_write.page_options((WEB / "index.html").read_text(encoding="utf-8"))
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
    """The tapered tips (the user's requests of 2026-11-05): one family card closing the UMI finger's shelf."""

    def test_the_family_is_complete_with_its_default(self) -> None:
        family = self.entries["families"][TAPERS]
        self.assertEqual(list(self.entries["families"]), [TAPERS])
        self.assertEqual((family["title"], family["shelf"], family["h_mm"], family["default"]),
                         ("Tapered tips", "umi-finray", 75, "umi-trap-tip13.8-2mm"))
        shape, tip = family["axes"]
        self.assertEqual((shape["key"], [(choice["value"], choice["label"]) for choice in shape["choices"]]),
                         ("shape", [("trap", "Trapezoid"), ("convex", "Convex arc")]))
        self.assertEqual((tip["key"], [choice["value"] for choice in tip["choices"]]), ("tip_mm", list(TAPER_TIPS)))
        grid = {f"{a}|{b}": f"umi-{a}-tip{b}-2mm" for a in TAPER_SHAPES for b in TAPER_TIPS}
        self.assertEqual(family["grid"], grid, "two shapes by five tip widths, each once")
        members = sorted(part_id for part_id, part in self.entries["parts"].items() if part["family"] == TAPERS)
        self.assertEqual(members, sorted(identifier[:-4] for identifier in grid.values()))
        self.assertEqual(sorted(identifier for part in members for identifier in self.entries["parts"][part]["variants"]), sorted(grid.values()))
        self.assertIn(family["default"], self.entries["variants"])
        self.assertEqual(family["lines"], ["Trapezoid or convex arc", "5 tip widths · 2 mm pitch"])
        self.assertEqual(family, library_write.family_record(TAPERS, self.parts["families"][TAPERS], self.parts, self.plan))
        for part_id in members:
            with self.subTest(part=part_id):
                self.assertNotIn(part_id, self.entries["order"], "no card or shelf of its own")
                self.assertNotIn(self.entries["parts"][part_id]["default"], self.entries["start"])
                self.assertEqual(self.entries["parts"][part_id]["title"], "UMI Fin-Ray Gripper, tapered tip")
                self.assertEqual(self.entries["variants"][f"{part_id}-2mm"]["pitch_mm"], 2)

    def test_an_incomplete_family_is_refused(self) -> None:
        for edit, message in ((lambda family: family["grid"].pop("convex|5.8"), "every choice"),
                              (lambda family: family.update(default="umi-finray-2mm"), "default"),
                              (lambda family: family.update(shelf="umi-trap-tip5.8"), "shelf"),
                              (lambda family: family["axes"][1]["choices"].append({"value": "1.8", "label": "1.8"}), "every choice")):
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
                     ROOT / "tools" / "library_scenes.py", ROOT / "tools" / "browser" / "library_shots.py", Path(__file__)):
            if not path.exists():
                continue  # the importer, the tips' tool and the scene builder are private: not in the public copy
            with self.subTest(file=path.name):
                source = path.read_text(encoding="utf-8")
                ast.parse(source, filename=str(path), feature_version=(3, 9))
                self.assertIn("from __future__ import annotations", source)
                self.assertNotRegex(source, r"\bmatch \w+:|zip\([^)]*strict=|\.bit_count\(")



# -- the page stage: library.html, the header's link, main.js's ./?part=<id>, app.py's route, the site build -----------

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
    """library.html, library.js and library.css as the spec of 2026-11-05 has them (the browser checks: library_checks)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (WEB / "library.html").read_text(encoding="utf-8")
        cls.index_html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.script = (WEB / "library.js").read_text(encoding="utf-8")
        cls.style = (WEB / "library.css").read_text(encoding="utf-8")
        cls.page = _page("library.html")
        cls.index = _page("index.html")

    def test_its_one_script_and_three_style_sheets_by_relative_urls(self) -> None:
        scripts = [(attributes.get("src"), attributes.get("type")) for tag, attributes in self.page.elements if tag == "script"]
        # The look's choice first, in <head> (web/theme.js, 2026-11-06), then the page's own.
        self.assertEqual(scripts, [("static/theme.js", None), ("static/library.js", None)], "no backend.js, Pyodide or three.js on the Library")
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
        for identifier in ("libHero", "libNote", "libGrid", "libShelves", "libDetail", "libStatus"):
            self.assertIn(identifier, ids)
        self.assertNotIn("libTiles", ids, "no tiles since the layout of 2026-11-06")

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
        self.assertEqual(re.findall(r'<a href="([^"]+)"[^>]*><span>([^<]+)</span></a>', links), [("./#rect", "Rectangular"), ("./", "Gen by Surface")])

    def test_the_library_link_on_both_pages(self) -> None:
        for name, page, expected in (("index.html", self.index, {"href": "library.html", "target": "_blank", "rel": "noopener"}),
                                     ("library.html", self.page, {"href": "library.html", "aria-current": "page"})):
            with self.subTest(page=name):
                found = [(index, attributes) for index, (tag, attributes) in enumerate(page.elements)
                         if tag == "a" and attributes.get("class") == "masthead-library"]
                self.assertEqual(len(found), 1)
                index, attributes = found[0]
                self.assertEqual({key: attributes.get(key) for key in expected}, expected)
                # Not a masthead-link (the community's pills keep their checks); after the mode switch (index.html: the
                # switch stays the title block's next sibling).
                self.assertNotIn("masthead-link", attributes["class"].split())
                before = [attributes for _, attributes in page.elements[:index] if "mode-picker" in (attributes.get("class") or "").split()]
                self.assertEqual(len(before), 1)
        text = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertLess(text.index('id="modePicker"'), text.index('class="masthead-library"'))
        self.assertIn("</fieldset>\n      <!-- The Library (library.html;", text)
        self.assertIn('title="Sensors already fitted to open-source grippers (opens in a new tab)"', text)

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
        for name, text in (("library.html", self.html), ("library.js", self.script), ("library.css", self.style)):
            with self.subTest(file=name):
                self.assertNotRegex(text, r"\bCAD\b")

    def test_its_script_neither_observes_nor_smooths_nor_leaves_the_site(self) -> None:
        source = self.script
        for word in ("IntersectionObserver", "ScrollTimeline", "ViewTimeline", "smooth", "scrollBehavior", "scroll-behavior", "innerHTML",
                     "backend.js", "apiFetch", "pyodide"):
            self.assertNotIn(word, source, word)
        self.assertIsNone(re.search(r"(window|document)\.addEventListener\(\s*[\"']scroll", source), "no window or document scroll listener")
        self.assertEqual(len(re.findall(r"addEventListener\(\s*[\"']scroll", source)), 1, "the one scroll listener: each track's arrows")
        self.assertEqual([url for url in re.findall(r"https?://[^\s\"'`]+", source) if url != "http://www.w3.org/2000/svg"], [])
        self.assertIn('const BASE = "static/library/";', source)
        self.assertIn("fetch(`api/export/${kind}`", source)
        self.assertEqual(re.findall(r"""\bfetch\(\s*[`"']/""", source), [], "relative fetches only")
        self.assertIn('history.scrollRestoration = "manual";', source)
        self.assertIn('"use strict";', source)

    def test_its_style_sheet_moves_nothing_and_blue_fills_only_open(self) -> None:
        rules, at_rules = parse_css(self.style)
        self.assertEqual({at.split()[0] for at in at_rules} - {"@media"}, set(), "no @import, @font-face, @supports or @layer")
        declarations = [(selector, name, value) for rule in rules for name, value, _ in rule.declarations for selector in rule.selectors]
        self.assertTrue(declarations)
        for selector, name, value in declarations:
            with self.subTest(selector=selector, property=name):
                self.assertFalse(name.startswith(("transition", "animation")) or name in ("scroll-behavior", "will-change"))
                if name == "position":
                    self.assertIn(value, ("relative", "absolute"))
                for url in re.findall(r"url\(\s*[\"']?([^\"')]*)", value):
                    self.assertTrue(url.startswith("data:"), url)
                if "var(--accent" in value:
                    self.assertRegex(subject(selector), r"\.lib-open\b", "the action blue only on Open in Gen by Surface")
        self.assertTrue([selector for selector, name, value in declarations if "var(--accent)" in value and ".lib-open" in selector])
        self.assertNotIn("@keyframes", self.style)
        self.assertIn("scroll-snap-type:x mandatory", self.style)

    def test_a_sensors_picture_is_3_to_1_in_one_column(self) -> None:
        # The user's decision of 2026-11-05 (可压扁: the picture may be squashed): below 900 px, where a sensor's page is
        # one column with its picture above Open, that picture is 3:1, so Open is in a 390 x 844 phone's first screen on
        # every sensor's page (library_checks part_first_screen measures it); every other picture, and this one from
        # 900 px, 16:10.  Its drawing or image contained and centred, never hidden.
        rules, _ = parse_css(self.style)
        aspects = [(selector, value, rule.conditions) for rule in rules for selector in rule.selectors
                   for name, value, _ in rule.declarations if name == "aspect-ratio"]
        self.assertEqual(aspects, [(".lib-shot", "16 / 10", ()), (".lib-shot-detail", "3 / 1", ("@media (max-width:899px)",))])
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
        self.assertIn('const src = kind === "detail" ? image?.[view]?.src : image?.exploded?.card;', slot)
        self.assertIn("if (!src) {\n      box.append(field(variant));\n      return box;\n    }", slot)
        self.assertIn('const [width, height] = kind === "detail" ? [image[view].width, image[view].height] : CARD;', slot)
        self.assertIn('el("img", {src: BASE + src, width, height, alt: image.alt || "", decoding: "async",\n'
                      '      loading: kind === "detail" ? null : "lazy"});', slot)
        self.assertIn('shown.addEventListener("error", () => {\n      shown.replaceWith(field(variant));\n      missed?.(view);\n    }, {once: true});', slot)
        self.assertIn("return drawing;", _inner(self.script, "field"))
        # Every picture is slot()'s: the shelf's cards, the family card (its default sensor's), a gripper's card (its
        # part's default).
        self.assertIn('slot(variant, "card")', _inner(self.script, "card"))
        self.assertIn('slot(state.index.variants[family.default], "card")', _inner(self.script, "familyCard"))
        self.assertIn('slot(state.index.variants[part.default], "card")', _inner(self.script, "gripperCard"))
        self.assertNotIn('"tile"', self.script)
        self.assertEqual(len(re.findall(r'el\("img"', self.script)), 1, "one image: slot()'s")

    def test_a_sensors_page_switches_its_picture_between_its_views(self) -> None:
        # A sensor's page (2026-11-05): the Exploded picture and, with both views, a small grey "Exploded | Assembled"
        # control under it in its frame: radios in a fieldset with a legend (a group named View: the arrow keys and a
        # screen reader), swapping the picture in place (no address or history change), the view kept across the
        # pitch, Shape and Tip width, Exploded again on each page opened, the control gone once both views failed.
        gallery = _inner(self.script, "gallery")
        self.assertIn('control = el("fieldset", {className: "lib-view"}, el("legend", {}, "View"),', gallery)
        self.assertIn('el("input", {type: "radio", name: "libView", value, checked: value === state.picture}),', gallery)
        self.assertIn("if (views.length < 2) return frame;", gallery)
        self.assertIn("        box.replaceWith(next);\n        box = next;\n", gallery)
        self.assertIn("if (state.picture !== view || !box.isConnected) return;", gallery)
        self.assertIn("if (control && failed.size === views.length) control.remove();", gallery)
        self.assertNotIn("history", gallery)
        self.assertNotIn("renderDetail", gallery)
        self.assertIn("    state.picture = VIEWS[0][0];\n    setNote(\"\");", _inner(self.script, "showDetail"))
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
        self.assertEqual(roomy, [".lib-detail:has(.lib-view)", ".lib-detail:has(.lib-view) .lib-detail-body", ".lib-detail:has(.lib-view) .lib-info"])

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
        # present() from a sensor's page alone; the grid takes the view down (rest()) and draws none.
        self.assertEqual(len(re.findall(r"\bpresent\(id\);", script)), 1)
        self.assertIn("    present(id);\n", _inner(script, "renderDetail"))
        self.assertIn("rest();", _inner(script, "showGrid"))
        for name in ("renderGrid", "card", "gripperCard", "grippers", "familyCard", "slot", "gallery"):
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
        self.assertIn('id: `gripper-${partId}`, href: `#${part.default}`', card)
        self.assertIn('heading("grippers", "Grippers.", `${word(parts.length)}${each}.`)', _inner(script, "grippers"))
        grid = _inner(script, "renderGrid")
        self.assertLess(grid.index("grippers(parts)"), grid.index("...shelvedParts().map("), "the grippers' section first, the UMI shelf after it")
        for word in ("lib-tile", "libTiles", "index.start"):
            self.assertNotIn(word, script, word)
        # Its back links: the UMI finger's pages (its tips' too) to its shelf, another gripper's to its card.
        self.assertIn('el("a", {className: "lib-back", href: `#${placeOf(home)}`}', _inner(script, "renderDetail"))
        self.assertIn('const placeOf = part => (isShelved(part) ? `shelf-${part}` : `gripper-${part}`);', script)
        # The older addresses: #shelf-start the top, #shelf-<gripper> its card; Back and Forward (an entry the page has
        # marked) put the grid back where it was, a link to another card goes to that card.
        route = _inner(script, "route")
        self.assertIn('const traversed = history.state?.library === true;\n    if (!traversed) history.replaceState({library: true}, "");', route)
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
        self.assertEqual(len(grid_cards(entries)), 12, "the grippers' seven cards, the UMI shelf's four and its Tapered tips card")

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
        # A variant, a part (its default) or a family (its default), as library.html's route takes them (the review of
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
        self.assertIn('note.replaceChildren("From the ", el("a", {href: `library.html#${cad.entry.id}`, target: "_blank", rel: "noopener"}, "Library"), '
                      '`: ${cad.entry.label.replace(/ mm$/, "\\u00a0mm")}`);', note)
        self.assertEqual("From the " + "Library" + ": ", NOTE_PREFIX)


class RouteTests(HttpTestCase):
    """app.py serves library.html as it serves the page: SECURITY_HEADERS, the header's counts, its query ignored."""

    def test_the_library_page_with_the_counts(self) -> None:
        import app

        page = (app.WEB_ROOT / "library.html").read_bytes()
        for path in ("/library.html", "/library.html?x=1"):
            with self.subTest(path=path):
                reply = self.request("GET", path)
                self.assertEqual((reply.status, reply.headers["content-type"], reply.body), (200, "text/html; charset=utf-8", page))
                for name, value in app.SECURITY_HEADERS:
                    self.assertEqual(reply.headers[name.lower()], value)
        self.server.httpd.github_counts = {"stars": 1234, "forks": 56}
        reply = self.request("GET", "/library.html")
        self.assertEqual(reply.body.decode("utf-8"), app.fill_github_counts(page.decode("utf-8"), {"stars": 1234, "forks": 56}))
        self.assertIn("<span data-gh-stars>1.2k</span>", reply.body.decode("utf-8"))
        head = self.request("HEAD", "/library.html")
        self.assertEqual((head.status, head.body, int(head.headers["content-length"])), (200, b"", len(reply.body)))
        wrong = self.request("POST", "/library.html", {})
        self.assertEqual((wrong.status, wrong.headers.get("allow"), wrong.json()["code"]), (405, "GET, HEAD", "E_HTTP_METHOD_NOT_ALLOWED"))
        # The in-browser API answers /api/ only: the pages are the site's files.
        self.assertEqual(app.answer("GET", "/library.html").status, 404)

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
    """tools/build_static_site.py: library.html with the site's head tags, the Library's gate and its prebuilt ZIPs."""

    def test_the_library_page_has_the_sites_head_tags_and_counts(self) -> None:
        built = build_static_site.page(name="library.html")
        head = built.split("</head>", 1)[0]
        self.assertTrue(head.startswith('<!doctype html>\n<html lang="en">\n  <head>\n    <meta charset="utf-8" />\n    <meta http-equiv="Content-Security-Policy"'))
        self.assertEqual(head.count("Content-Security-Policy"), 1)
        self.assertEqual(head.count('<meta name="flexitac-backend" content="browser" />'), 1)
        self.assertIn("<title>Library · FlexiTac-Gen</title>", head)
        counted = build_static_site.page({"stars": 159, "forks": 17}, "library.html")
        self.assertIn('<span data-gh-stars>159</span>', counted)
        self.assertNotIn("data-gh-stats hidden>", counted)
        self.assertEqual(build_static_site.page(), build_static_site.page(name="index.html"))

    def test_the_pages_are_not_copied_under_static(self) -> None:
        with mock.patch.object(build_static_site.shutil, "copytree") as copy:
            build_static_site.copy_web(Path("static"))
        ignore = copy.call_args.kwargs["ignore"]
        # The Library's pictures are published with web/ (static/library/shots/).
        names = ["index.html", "library.html", "library.js", "library.css", "theme.js", "app.py", "__pycache__", "entries.json", "manifest.json",
                 "widowx-250-2mm.exploded.webp", "widowx-250-2mm.exploded.card.webp",
                 # The 3D view's files (2026-11-05): the art, the scenes and their bodies, the view's modules.
                 "widowx-250-2mm.json.gz", "scenes.json", "widowx-250.json", "rail.stl", "library_view.js", "library_stage.js"]
        self.assertEqual(sorted(ignore(str(WEB), names)), ["__pycache__", "app.py", "index.html", "library.html"])

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

    def test_the_gate_writes_the_exports_and_their_record(self) -> None:
        import app

        entries = _json(LIBRARY / "entries.json")
        with tempfile.TemporaryDirectory() as folder:
            static = Path(folder) / "static"
            record = build_static_site.library(static, only=["umi-finray-2mm", "widowx-250-1mm"])
            files = _json(static / "library" / "files.json")
            self.assertEqual(record, {"variants": 2, "files_json_sha256": hashlib.sha256((static / "library" / "files.json").read_bytes()).hexdigest(),
                                      "pictured": sum(1 for identifier in ("umi-finray-2mm", "widowx-250-1mm") if entries["variants"][identifier]["image"]),
                                      "viewed": sum(1 for identifier in ("umi-finray-2mm", "widowx-250-1mm") if entries["variants"][identifier]["view"])})
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
        index = (WEB / "index.html").read_text(encoding="utf-8")
        control = 'data-option="proposals" value="5"'
        self.assertEqual(index.count(control), 1)
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "index.html"
            changed.write_text(index.replace(control, 'data-option="proposals" value="4"'), encoding="utf-8")
            with self.assertRaisesRegex(build_static_site.BuildError,
                                        r"the library is stale \(widowx-250-2mm\): run tools/library_write.py \(its request is not the one the page sends\)"):
                build_static_site.library(Path(folder) / "static", only=["widowx-250-2mm"], index=changed)
            self.assertFalse((Path(folder) / "static" / "library" / "files.json").exists(), "nothing written")


if __name__ == "__main__":
    unittest.main()
