#!/usr/bin/env python3
"""Fit the Library's sensors as the page asks for them: web/library/fits/<id>.json and web/library/entries.json.

The Library (library.html, the user's requests of 2026-11-05) lists sensors already fitted to open-source gripper
fingers; each opens in Gen by Surface at ./?part=<id> with its sensor built at once from a shipped fit, as the page's
default part does (web/cad/main.js takes a shipped reply only when the request it would send is the shipped one, key
by key).  So each fit here is made from the request the page sends for it, not from one of our own:

- web/library/parts.json (hand-maintained; a private importer wrote it once from the multi-gripper video's
  recipes) gives each part's mesh, the face the page selects (the request's selection with seed facets, its base
  and, for the UMI finger, its border) and its variants: a pitch and a fill, the only options a variant sets, beside
  the part's own (rotation none on four recipes);
- every other option is the page's default, read from web/index.html's Resolution step as main.js readOptions reads
  it (each [data-option] control of #cadConfig, a disabled one sending nothing: under the default objective
  fixed_pitch that is Smallest pitch); numbers are written as the browser writes them (2, not 2.0), no unit is sent
  (the page's Auto) and the name is the mesh's file name, as a dropped file's;
- surface.api.fit gives the reply, round-tripped through JSON as the server sends it; its proposal #1 (the page
  chooses proposal 0 after every fit) must keep the product rules (rules(): one tail pin per line, field-only
  containment, the tails centred and ending together, a symmetric face's sensor centred, a build with no error or
  warning and the same build id), or the variant is rejected, naming the rule, and nothing is written.

Each variant's fit goes to fits/<id>.json ({about, mesh_sha256, request, reply}, compact), its summary to entries.json,
the one index library.html and main.js read.  A part of a family (parts.json families: the UMI finger's tapered tips,
cut by the private tools/library_tips.py) has no card or shelf of its own: entries.json's order and "start" (each
part's default) are the grippers', and the family is one card closing its shelf's part (family_record(): its axes,
the grid of their choices to variant ids, complete, and its default).  The UMI finger's 2 mm sensor is the page's default part's: its fit is
web/vendor/umi/default-fit.json (the request the browser recorded, tools/browser/write_default_fit.py), only checked
here, never written.  Only changed files are written; fits of variants no longer listed are removed.  A variant's id
is <part>-<pitch>mm with the pitch as the browser writes it (1, 1.5, 2).  tests/test_library.py checks the committed
files against this module (the request, the product rules, a staleness sample) and the site build re-fits every one.

Each variant's picture (entries.json's "image", the cards' and the sensor page's) is the generator's sensor on the part
(web/cad/onpart.js) at its Exploded and Assembled homes, shot in a browser by tools/browser/library_shots.py into
web/library/shots/ with shots/manifest.json (each file's bytes and SHA-256, the fit and build id it was shot from, a
hash of the figure's sources); this writer only reads it (pictures()): "image" is null for a shot of another fit (the
wrong sensor pictured), which --check, the site build and tests/test_library.py refuse, and for a sensor with no shot,
which --check and tests/test_library.py refuse (every sensor of the Library has its picture since the set of
2026-11-05); a shot of older figure sources is pictured with a warning only (re-shoot it: the public CI runs no
browser).  Writing only reports a missing or stale picture: after a re-fit or a new sensor, write, shoot, write again.

Each sensor's page turns in 3D (the user's request of 2026-11-05, docs/LIBRARY_VIEW.md): entries.json's "view" names
the files the Library's 3D view draws it from, its art (art/<id>.json.gz, the generator's art of its two boards, written
by the shots tool beside its pictures) and, for a gripper drawn whole, its scene (scenes/<part>.json, its bodies in
bodies/<part>/); pictures() writes it for a sensor whose record is current with its art (and a gripper's with its stage)
and refuses an art or a stage that is not the sensor's own; scenes() checks the scenes themselves (their format, their
matrices, their bodies' files and notices, the deny-list).  Since the shoot of 2026-11-06 that wrote every sensor's
art and each gripper's stage (VIEW_REQUIRED), a record without them is refused (before it, a picture without them was
shown with no 3D view, a warning).

The Library's first section is a showcase (the project owner's decision of 2026-11-12): the hand-designed FlexiTac
sensor on UFACTORY's xArm Gripper G1, no part or entry of this writer's (no fit, no build).  Its files are written by
tools/library_showcase.py; this module holds its guards (SHOWCASE_*, showcase(), reported by scenes()): the one vendor
model the Library shows, in its own folder beside the Library with its own notice, pinned file by file, named by the
showcase's scene alone, and the vendor's own file never published.

Stdlib only.  Re-run it after any change of the page's defaults (they are every sensor's request; the site build
refuses a fit of another request) and after any change of the engine, the surface template or the profile that moves
a build id:

    python3 tools/library_write.py                       # fit every variant, write what changed
    python3 tools/library_write.py --only widowx-250-1mm,widowx-250-2mm
    python3 tools/library_write.py --check               # write nothing; exit 1 listing the stale ids
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
import os
import re
import struct
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WEB = ROOT / "web"
LIBRARY = WEB / "library"
INDEX = WEB / "index.html"
FORMAT = "flexitac-library/v1"
PARTS_FORMAT = "flexitac-library-parts/v1"
# The page's default pitch: each part's default variant (the sensor its card opens on the Library, ./?part=<part>).
DEFAULT_PITCH = 2
# 'From the Library: ' + the label is the file note of Gen by Surface's step 1 (web/cad/main.js), one line at 1440 and
# 390 px when the label has at most this many characters (measured with the widest, 'UMI Fin-Ray Gripper, 1.5 mm').
LABEL_MAX = 27
COUNT_WORDS = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten")
FIT_ABOUT = ("The fit of a Library sensor (web/library/entries.json): the request the page sends for it and the "
             "engine's reply, which the page takes when its request is this one.  Written by tools/library_write.py; "
             "tests/test_library.py and the site build check it against surface.api.fit.")
ENTRIES_ABOUT = ("The Library's index (library.html; Gen by Surface's ./?part=<id>): each part with its mesh and licence, "
                 "each variant's sensor (proposal #1 of its fit) and the files of its fit.  Written by "
                 "tools/library_write.py from parts.json and the fits; do not edit by hand.")
# Vendor models that never go into the Library (no open licence: "vendor models, user-provided, shown for illustration"
# in the video's recipes), by SHA-256 and by name.  The one list: the private importer (tools/library_import.py) takes
# it from here, and tests/test_library.py holds the same list and asserts this one equal to it.  It lives in this
# public module so that the public copy's tests and mutation catalogue check it too (the integration's review of
# 2026-11-05: the importer's own copy, outside export_public.PUBLIC, broke the public copy's mutation --check).
# Since the project owner's decision of 2026-11-12 one vendor model is shown, in one place: UFACTORY's Gripper G1 in
# the Library's showcase (SHOWCASE_* below, web/vendor/ufactory-g1/ with its own notice).  Nothing else changes: the
# names stay refused in every part, entry, fit and sample, and the Robotiq models, the MakerMods body and the seven
# meshes of the video's split of the xArm file stay denied by SHA-256; so do, since the review of that day, the
# pieces of the same file before any decimation (the FlexiTac Tactile Demo's split: together they are the whole file).
DENIED_SHA256 = {
    "b0df0eaca944c7401185ada85d22e3111b477c3484c6fa3fd915fce6d6811aaf": "Robotiq 2F-85 (2F85_Opened.stl)",
    "49e96f7fceab20ebcf13b5c8467bf83d70716a846a109ad37818bc06d798f7a7": "Robotiq 3F (ROBOTIQ_AGS-001-XXXX.stl)",
    "acbae34a4329e9079b7550af0fe6624cc8277f02c2317d4df7e9950589efc24c": "xArm (finger_r.stl)",
    # The other six meshes split from the same closed xArm file as finger_r.stl.
    "a61abac9746d0319a6e6ab82ba27a7d16afe6f303bc2bac863449b05c27c0661": "xArm (finger_l.stl)",
    "4101e1a6a1d1983727470eeacde4225031c53309ae9f5cee7b2f2d2bc3e70bb5": "xArm (body.stl)",
    "676df24e40f8dbd84d760226d9605fc8d27171c4f392e26b0fcdb47d808ec227": "xArm (link_l_inner.stl)",
    "3d82a29a55c7fca3f08eeb441a97667d34e675901bc0fab8c22fec6e41ead7bd": "xArm (link_l_outer.stl)",
    "f256d6ca99bca7c32e991080ca5988015c96a535bf1edc14840ff5643f864904": "xArm (link_r_inner.stl)",
    "c97e95bafd0b0f5a66dfcccf5f398956ddae2facca3d4509f1754a0ba138888b": "xArm (link_r_outer.stl)",
    # 2026-11-12: "xArm (Gripper G1 3D File (With).stl)", 6c59aabb...de332f, left this list by the project owner's
    # decision of that day, so that the showcase's notice may name the file its meshes are split from.  The file itself,
    # unsplit and undecimated, is still refused anywhere under web/: SHOWCASE_SOURCE, showcase().
    # The same file split as the FlexiTac Tactile Demo splits it, not decimated (its seven first pieces, and the nine
    # further pieces of its body and fingers; the links are in both): the review of 2026-11-12.  Only the decimated
    # pieces of SHOWCASE_VENDOR_FILES are shown, in their folder.
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
    # The MakerMods Metal Arm's gripper body (metal-python-ros: its package.xml says "Business", no licence file), not
    # cleared for redistribution: the Library's whole-gripper scene draws its HandUMI tips on a plain rail of the
    # project's own instead (the user's decision of 2026-11-05, docs/LIBRARY_VIEW.md).
    "19ab43c406f349d62dc7a9932b66fb28053cf96152ab00d71a93945a43ddd8cd": "MakerMods Metal Arm (gripper_base.STL): not cleared",
    "3c813623f4c273bfb6f4fd483fc8ee23dc4325de32e9d89d7c44cb1a0e97c033": "MakerMods Metal Arm (link7.STL): not cleared",
    "62d0ed4072aea7e4d0655e16edbf8243317e3e106996f00f06e72afc78d091ec": "MakerMods Metal Arm (link8.STL): not cleared",
}
DENIED_NAME = re.compile(r"robotiq|xarm|ufactory", re.IGNORECASE)
# The Library's showcase (the project owner's decision of 2026-11-12; the lead's spec of that day): the hand-designed
# FlexiTac sensor on the xArm Gripper G1 with UMI soft fingers, at the top of the Library.  It is not a part or an
# entry (no fit, no build, none of the generator's Gerbers): it has one scene of its own, scenes/flexitac-g1.json, in
# the scenes' format, drawn about the UMI finger.  Its gripper is UFACTORY's 3D model, the one vendor model the Library
# shows: the Tactile Demo's split of "Gripper G1 3D File (With).stl", each piece decimated to within 0.1 mm
# (tools/library_showcase.py), in web/vendor/ufactory-g1/ beside its own NOTICE.md, outside web/library/ and its
# budget.  The category is explicit so that nothing else can use it (showcase()):
# - the folder holds exactly SHOWCASE_VENDOR_FILES, each at its pinned SHA-256, and its notice, within a byte budget of
#   its own;
# - the notice says whose the model is and why it is here (SHOWCASE_WORDS), never "CAD", and tables every file;
# - only the showcase's scene names the folder: no part, entry, fit, sample or other scene (SHOWCASE_REFERENCE);
# - the folder's meshes are nowhere else under web/ (by SHA-256: a copy under another name, as another gripper's body
#   or a sample's part, would need no name of the folder);
# - the file itself, unsplit and undecimated (SHOWCASE_SOURCE: its name, SHA-256 and bytes; SHOWCASE_SOURCE_TRIANGLES:
#   the SHA-256 of its bytes after the 80-byte header, so a copy under another header is the file still), is never
#   under web/, nor is any model of DENIED_SHA256 (its undecimated pieces among them).
# The UMI finger holder the scene draws beside them is HandUMI's (Apache-2.0), a body of the Library as any other
# (bodies/flexitac-g1/, a row of NOTICE.md), its SHA-256 pinned too (SHOWCASE_BODIES).
SHOWCASE_ID = "flexitac-g1"
SHOWCASE_SCENE = f"scenes/{SHOWCASE_ID}.json"
SHOWCASE_VENDOR = "vendor/ufactory-g1"
SHOWCASE_NOTICE = "NOTICE.md"
SHOWCASE_SOURCE = ("Gripper G1 3D File (With).stl", "6c59aabbd22823819af1face17752cfd5b32f43529ed08da9596148770de332f", 6347684)
SHOWCASE_SOURCE_TRIANGLES = "6fedf322985477e914f3160228e2b3c1fa7226843dc6f58e4ea19e9914d53393"
SHOWCASE_VENDOR_FILES = {
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
# Just above the folder as built (the twelve meshes, 2,175,608 bytes, and the notice): nothing grows it unseen.
SHOWCASE_VENDOR_BUDGET_BYTES = 2_200_000
# Its bodies in the Library's own folder: HandUMI's holder, and the plain shapes the project draws after the owner's
# photo of the gripper (tools/library_showcase.py DRAWN: screw and bolt heads, nuts, the block in the top slot, the
# extender boards and cable stubs; each under the header of a shape the project drew, with no row of NOTICE.md).  The
# tool draws them again on every run and --check; their pins here are what lets them stand without a look file
# (tools/library_split.py unowned()).
SHOWCASE_BODIES = {
    "bodies/flexitac-g1/umi-right-finger-holder.stl": "bed7997d234957cd874aecec2be76e133ab14b4cd652abe4c0491ee06fe469dd",
    "bodies/flexitac-g1/drawn-shell-screw.stl": "3e9be6a39e4c3324539b799a027ff2d11da071427abc9fdc4b18bbd11d218cdb",
    "bodies/flexitac-g1/drawn-holder-bolt.stl": "4065ad795ec729b88544255a84ee9372498d6d8b7874504c1ecacbb9b119d3d8",
    "bodies/flexitac-g1/drawn-holder-nut.stl": "19dfdb4cfc52e2aca385209251c9ae8bd063fcee2f776a8dc5540fc6e9ab7dcb",
    "bodies/flexitac-g1/drawn-slot-block.stl": "4c931930fd990b0e76da2facd08e69b7d795b371264d58196b80b3b056685f0d",
    "bodies/flexitac-g1/drawn-extender.stl": "ce9e3d2b69f27cb92a941e0580e2cd25c717f341515e9f022b3f5a8814b54559",
    "bodies/flexitac-g1/drawn-extender-sockets.stl": "1fb0ee61d901a42382ed3ba2004b6e80912e45c99c31caff7e1ac7bbfd0fa042",
    "bodies/flexitac-g1/drawn-cable-stub.stl": "13d5a943386e3cb4a92e55d8b135a99a0ff3b765496633cd774c46f9757ac1e5",
}
# The notice's wording, each found in its text (white space folded): whose the model is, where the file comes from,
# why it is here, that the repository's licence does not cover it, and what was changed, by whom.
SHOWCASE_WORDS = ("3D model", "the property of UFACTORY", "UFACTORY's download centre",
                  "used by the project owner's decision of 2026-11-12", "not covered by this repository's Apache-2.0 licence",
                  "split", "decimated", "by FlexiTac-Gen 2026")
# Its table's rows (NOTICE_ROW's columns): the owner's column, and the change's with the deviation measured (mm).
SHOWCASE_OWNER = "the property of UFACTORY, not Apache-2.0"
SHOWCASE_CHANGE = re.compile(r"modified: split(?:, cut at the holder)?, decimated \(quadric error metrics, (0\.\d+) mm\)")
SHOWCASE_TOLERANCE_MM = 0.1
SHOWCASE_REFERENCE = re.compile(r"ufactory-g1", re.IGNORECASE)
REBUILD_SHOWCASE = "rebuild the showcase with tools/library_showcase.py"
# The fix of a file no tool writes and none may publish (the vendor's own file, a model of the deny-list, a copy of one
# of the folder's meshes outside its place, a stranger in the folder): removing it, not a rebuild (the review of
# 2026-11-13: a rebuild of the showcase leaves such a file where it is).
REMOVE_FILE = "remove it"
# The showcase's page (library.html's first card and its own page at #flexitac-g1; docs/LIBRARY_VIEW.md "The showcase's
# page"): showcase.json beside entries.json, a document of its own format.  Its words are written by hand (the title,
# the label that it is hand-designed and not auto-generated, one line, the sensor's size, the link to the FlexiTac
# hardware tutorial for the Gerbers, the sources with their notices); its "placed" is the pad's placed record
# (SHOWCASE_PLACED, a file of the pad's own folder) with the showcase's scene; its "image" and "shot" are written by
# tools/browser/library_shots.py --showcase: the three pictures in showcase/ (their sizes below: 4:5, the gripper
# upright), each with its bytes and SHA-256, and what they were shot from.  showcase_page() checks all of it.
SHOWCASE_FILE = "showcase.json"
SHOWCASE_FORMAT = "flexitac-library-showcase/v1"
SHOWCASE_KEYS = ("about", "format", "id", "image", "label", "placed", "sensor", "shot", "sources", "text", "title", "tutorial")
SHOWCASE_PLACED = "vendor/flexitac-v2/umi-finray.placed.json"
SHOWCASE_PAD_NOTICE = "vendor/flexitac-v2/NOTICE.md"
SHOWCASE_SHOT_SIZE = (1280, 1600)
SHOWCASE_CARD_SIZE = (800, 1000)
# kind: (the file relative to web/library/, its size, the mode it shows).
SHOWCASE_SHOTS = {"exploded": (f"showcase/{SHOWCASE_ID}.exploded.webp", SHOWCASE_SHOT_SIZE, "exploded"),
                  "assembled": (f"showcase/{SHOWCASE_ID}.assembled.webp", SHOWCASE_SHOT_SIZE, "assembled"),
                  "card": (f"showcase/{SHOWCASE_ID}.card.webp", SHOWCASE_CARD_SIZE, "assembled")}
SHOWCASE_SHOT_KEYS = ("art_sha256", "figure_sha256", "look", "margins_px", "numbers", "placed_sha256", "scene", "scene_sha256", "view_sha256")
# The label's words (the user's request of 2026-11-12: "这个版本是人手design的不是autogenerate") and the sources' notices,
# in the page's order: the gripper's (the one place showcase.json names the vendor's folder) and the pad's.
SHOWCASE_LABEL_WORDS = ("hand-designed", "not auto-generated")
SHOWCASE_NOTICES = (f"../{SHOWCASE_VENDOR}/{SHOWCASE_NOTICE}", f"../{SHOWCASE_PAD_NOTICE}")
SHOWCASE_SOURCE_WORDS = (("UFACTORY", "3D model"), ("FlexiTac", "CC BY-NC 4.0"))
SHOWCASE_ALT = "The hand-designed FlexiTac sensor on both soft fingers of the xArm gripper"
RESHOOT_SHOWCASE = "re-shoot with tools/browser/library_shots.py --showcase"
# The stage's numbers of the showcase's shoot (showcase.json's "shot"."numbers"; the rules' table of
# docs/LIBRARY_VIEW.md).  Four of the rules' checks hold of the showcase as of any gripper (SHOWCASE_RULED: a number, the
# rule it is held to).  Three cannot: both its fingers are drawn solid and its pad's tails wrap behind its finger, so it
# has bounds of its own for them (SHOWCASE_BOUNDS), each a little past what was measured (2026-11-13, the shoot of the
# scene of that day, and the same scene with one finger see-through, by a route), so that a scene or a camera that
# hides more of the pad is refused:
# - assembled_opaque, how much of the far (sensor) finger's top FPC the solid bodies cover in Assembled: 0.19, its own
#   tails behind its own finger and their ends under the extender board (0 with that finger see-through);
# - opaque_max, the same of any layer in Exploded: 0.679, the near finger's own pad behind its own finger (0.017 with
#   that finger see-through);
# - near_seen, what is seen of the near finger's bottom FPC: 0.321, its straps on the side face (0.858 with that
#   finger see-through).
SHOWCASE_RULED = (("visible_min", "layer_visible_min"), ("clearance_mm", "clearance_min_mm"), ("stacks_apart_px", "stacks_apart_min_px"),
                  ("card_px", "card_min_px"))
SHOWCASE_BOUNDS = (("assembled_opaque", "below", 0.25), ("opaque_max", "below", 0.75), ("near_seen", "at least", 0.25))
# How the lines of a stale showcase end (each says its own fix: REBUILD_SHOWCASE or RESHOOT_SHOWCASE).
SHOWCASE_STALE = "the showcase is stale: tools/library_showcase.py writes its scene, tools/browser/library_shots.py --showcase its pictures"


class LibraryError(Exception):
    pass


# -- the page's request -------------------------------------------------------------------------------------------

class _Controls(HTMLParser):
    """The [data-option] controls inside #cadConfig, in order, with their attributes and each select's options."""

    VOID = {"input", "meta", "link", "br", "img", "hr", "source", "area", "base", "col", "embed", "param", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.controls: list = []
        self._stack: list = []
        self._select = None

    def _inside(self) -> bool:
        return any(element_id == "cadConfig" for _, element_id in self._stack)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if self._inside():
            if "data-option" in attributes:
                control = {"tag": tag, "attributes": attributes, "options": []}
                self.controls.append(control)
                self._select = control if tag == "select" else None
            elif tag == "option" and self._select is not None:
                self._select["options"].append(attributes)
        if tag not in self.VOID:
            self._stack.append((tag, attributes.get("id")))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "select":
            self._select = None
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                break


def js(value):
    """A JSON value with integral floats as integers, as the browser writes numbers (JSON.stringify(2.0) is 2)."""

    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {key: js(item) for key, item in value.items()}
    if isinstance(value, list):
        return [js(item) for item in value]
    return value


def js_string(number) -> str:
    """String(number) in the browser, for the pitches of the ids (1, 1.5, 2.5)."""

    number = js(number)
    return str(number) if isinstance(number, int) else repr(number)


def controls(index_html: str) -> dict:
    """The Resolution step's fit options: {option: {tag, default, min, max, step, choices, disabled}} (main.js
    readOptions).

    An input's default is Number(value), rounded when its step is 1, as the browser sends it; a select's default is its
    selected option, else its first one that is not disabled (a disabled option is a display state, never sent).
    disabled: the control itself is disabled in the page (readOptions sends nothing for it, unless main.js turns it on:
    page_options)."""

    parser = _Controls()
    parser.feed(index_html)
    parser.close()
    out = {}
    for control in parser.controls:
        attributes = control["attributes"]
        key = attributes["data-option"]
        if key in out:
            raise LibraryError(f"web/index.html: two controls send {key}")
        if control["tag"] == "select":
            choices = [option.get("value") for option in control["options"] if "disabled" not in option]
            chosen = [option.get("value") for option in control["options"] if "selected" in option]
            out[key] = {"tag": "select", "default": (chosen or choices)[0], "choices": choices}
        else:
            value = float(attributes["value"])
            step = attributes.get("step", "")
            out[key] = {"tag": "input", "default": js(float(round(value)) if step == "1" else value),
                        "min": attributes.get("min"), "max": attributes.get("max"), "step": step}
        out[key]["disabled"] = "disabled" in attributes
    return out


# The controls whose disabled state main.js sets itself as the page starts, whatever index.html says: syncObjective
# (Pitch and Smallest pitch, by the objective) and syncContainment (Row traces, off under Whole board).
SYNCED = ("pitch_mm", "min_pitch_mm", "row_sides")


def page_options(index_html: str) -> dict:
    """The options the page sends untouched: each control's default, but the one syncObjective disables (Smallest
    pitch under Resolution (pitch), the default objective; Pitch under the others) and any other control disabled in
    index.html (readOptions skips it; the review of 2026-11-05)."""

    found = controls(index_html)
    disabled = "min_pitch_mm" if found["objective"]["default"] == "fixed_pitch" else "pitch_mm"
    return {key: control["default"] for key, control in found.items()
            if key != disabled and (key in SYNCED or not control["disabled"])}


def round6(number: float) -> float:
    """main.js round6 (Math.round(number * 1e6) / 1e6: halves up, as Math.round rounds)."""

    return math.floor(number * 1e6 + 0.5) / 1e6


def valid(control: dict, value) -> bool:
    """Whether the browser takes ``value`` in this number input (min, max and step, in decimal as the browser does)."""

    try:
        number = Decimal(str(value))
        low = Decimal(control["min"]) if control.get("min") else None
        high = Decimal(control["max"]) if control.get("max") else None
        step = control.get("step") or "1"
        if (low is not None and number < low) or (high is not None and number > high):
            return False
        return step == "any" or ((number - (low if low is not None else 0)) % Decimal(step)) == 0
    except (InvalidOperation, TypeError, ValueError):
        return False


def variant_id(part_id: str, variant: dict) -> str:
    return f"{part_id}-{js_string(variant['pitch_mm'])}mm"


def compose(part: dict, variant: dict, options: dict) -> dict:
    """The fit request the page sends for one variant: the part's selection, base and border, the page's options
    (``options``, page_options()) with the part's and the variant's over them, the mesh's file name, no unit.

    What main.js buildDefaultSensor would send otherwise is refused (LibraryError), not composed (the review of
    2026-11-05: parts.json is edited by hand, and only the browser checks would see the difference): a base other than
    "auto" or {point_xyz} (it chooses a point only), a base point with a border (the border's edge is the base), a
    point whose coordinates choosePoint's round6 changes, and an objective other than Resolution (pitch) (a variant's
    pitch is sent only under it).  Under Whole board the page disables Row traces (syncContainment), so none is sent."""

    setup = part["setup"]
    sent = dict(options)
    sent.update(setup.get("options") or {})
    sent.update(pitch_mm=variant["pitch_mm"], fill=variant["fill"])
    base = setup["base"]
    if base != "auto":
        point = base.get("point_xyz") if isinstance(base, dict) and set(base) == {"point_xyz"} else None
        if not (isinstance(point, list) and len(point) == 3 and all(isinstance(value, (int, float)) for value in point)):
            raise LibraryError(f"base {base!r}: the page sends 'auto' or {{point_xyz: [x, y, z]}} for a Library sensor")
        if setup.get("border"):
            raise LibraryError("a base point with a border: the page sends the border's edge as the base")
        if [round6(value) for value in point] != point:
            raise LibraryError(f"base point {point}: main.js choosePoint rounds it to 6 decimals (round6); write it so")
    if sent.get("objective", "fixed_pitch") != "fixed_pitch":
        raise LibraryError(f"objective {sent['objective']!r}: a Library sensor's pitch is sent under Resolution (pitch) only")
    request = {"name": part["mesh"]["name"][:200], "selection": copy.deepcopy(setup["selection"]),
               "base": copy.deepcopy(base), "options": sent}
    if setup.get("border"):
        # readOptions: with a border, field-only containment is sent (the select is held at Field only).
        request["border"] = copy.deepcopy(setup["border"])
        sent["containment"] = "field"
    if sent.get("containment", "field") != "field":
        sent.pop("row_sides", None)
    return js(request)


def canonical(value) -> str:
    """Sorted-key JSON, as main.js compares a request with the shipped one."""

    return json.dumps(js(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


# -- the fit and its rules ----------------------------------------------------------------------------------------

def fit(request: dict, mesh: bytes) -> dict:
    """surface.api.fit's reply to the request, as the server sends it (JSON, no NaN)."""

    from surface import api

    return json.loads(json.dumps(api.fit(request, mesh), allow_nan=False))


def rules(reply: dict, build: bool = True) -> list:
    """The product rules broken by proposal #1 of a fit (none: the list is empty), each message naming its rule.

    The Library's sensors are made as the page makes them, so they keep what the page keeps (the user's rules of
    2026-10-20..11-02): a tail pin per line (reader none: no connector size in the design), only the taxel field on the surface (containment field), both
    tails centred on the base edge and ending together, a sensor on a symmetric face centred on it, and a build with
    no error or warning whose build id is the proposal's (``build``: generate_design, about 0.1 s)."""

    proposals = reply.get("proposals") or []
    if not reply.get("ok") or not proposals:
        return ["a proposal: the fit has none"]
    first = proposals[0]
    metrics = first["metrics"]
    broken = []
    # Reader none: one tail pin per line (the design's connector sizes nothing).  metrics.reader may still name a
    # reader, the one whose connectors those tails happen to fit (surface.reader.of_readout: a 32 x 16 readout's
    # tails of 32 and 16 pins are the FlexiTac reader's); that is a fact about the sensor, not a broken rule.
    connector = first["design"].get("connector") or {}
    if connector.get("row_pins") is not None or connector.get("column_pins") is not None:
        broken.append(f"reader none: #1's tails are sized to a reader ({connector.get('row_pins')} and {connector.get('column_pins')} pins)")
    if metrics.get("containment") != "field":
        broken.append(f"field containment: #1 has {metrics.get('containment')}")
    bus = metrics.get("row_bus") or {}
    if bus.get("tail_position") != "centred":
        broken.append(f"centred tails: #1's tails are {bus.get('tail_position')}")
    if metrics.get("row_tail_mm") != metrics.get("column_tail_mm"):
        broken.append(f"tails ending together: #1's are {metrics.get('row_tail_mm')} and {metrics.get('column_tail_mm')} mm")
    symmetry = metrics.get("symmetry") or {}
    if symmetry.get("face") and not symmetry.get("field"):
        broken.append("a symmetric face's sensor centred: #1 is not")
    if build:
        from engine import generate_design

        result = generate_design(first["design"])
        validation = result["validation"]
        codes = [issue.get("code") for issue in validation["errors"] + validation["warnings"]]
        if codes:
            broken.append(f"a clean build: #1 builds with {', '.join(codes)}")
        if result["manifest"]["build_id"] != first["build_id"]:
            broken.append(f"the same build: #1 builds as {result['manifest']['build_id']}, not {first['build_id']}")
    return broken


def fit_document(request: dict, mesh_sha256: str, reply: dict) -> bytes:
    """A fits/<id>.json file: compact sorted JSON (ASCII) with a final newline."""

    document = {"about": FIT_ABOUT, "mesh_sha256": mesh_sha256, "request": request, "reply": reply}
    return (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


# -- entries.json ---------------------------------------------------------------------------------------------------

def plan(parts: dict) -> list:
    """[(variant id, part id, part, variant)] in the parts' order, each part's variants by pitch."""

    if parts.get("format") != PARTS_FORMAT:
        raise LibraryError(f"parts.json: the format is {parts.get('format')!r}, not {PARTS_FORMAT}")
    out, seen = [], set()
    for part_id in parts["order"]:
        part = parts["parts"][part_id]
        for variant in sorted(part["variants"], key=lambda item: item["pitch_mm"]):
            identifier = variant_id(part_id, variant)
            if identifier in seen:
                raise LibraryError(f"parts.json: two variants are {identifier}")
            seen.add(identifier)
            out.append((identifier, part_id, part, variant))
    if set(parts["order"]) != set(parts["parts"]):
        raise LibraryError("parts.json: order and parts name different parts")
    return out


def fit_path(identifier: str, variant: dict) -> str:
    """The variant's fit file, relative to web/library/ (fits/<id>.json, or the file its parts.json entry names)."""

    return variant.get("fit") or f"fits/{identifier}.json"


def label(part: dict, variant: dict) -> str:
    """The sensor's name in Gen by Surface's file note: the part's title and the pitch ('WidowX 250, 1 mm'), or a
    family member's own label (a tapered tip's: 'UMI trapezoid tip, 13.8 mm', its one pitch the family's)."""

    return part.get("label") or f"{part['title']}, {js_string(variant['pitch_mm'])} mm"


def shelf(variants: list, families: list = ()) -> str:
    """A part's shelf heading after its name, in one wording on every shelf: the count and the range of its pitches
    ('Four pitches, 1 to 3 mm.'), and on a shelf that closes with families those after the range (the UMI finger's:
    'Four pitches, 1 to 3 mm, and tapered tips.').  The user's decision of 2026-11-05 (最好统一, best unified): the
    seven other shelves said 'Four pitches, from fine 1 mm to coarse 3 mm.' and the UMI finger's the range alone, as
    the review of the same day had made it (the long form took two lines at 1440 px there, balanced to half the row).
    Every gripper's four pitches begin at 1 mm (1 to 2.5, 3 or 4 mm), so the range alone is honest on each; every
    heading is one line from 1280 px."""

    pitches = sorted(variant["pitch_mm"] for variant in variants)
    count = COUNT_WORDS[len(pitches)] if len(pitches) < len(COUNT_WORDS) else str(len(pitches))
    if len(pitches) == 1:
        text = f"{count} pitch, {js_string(pitches[0])} mm"
    else:
        text = f"{count} pitches, {js_string(pitches[0])} to {js_string(pitches[-1])} mm"
    for family in families:
        text += f", and {family['title'].lower()}"
    return text + "."


def family_record(family_id: str, family: dict, parts: dict, table: list) -> dict:
    """entries.json's record of a family: parts.json's (title, shelf, h_mm, axes, grid, default) checked, with the card's
    two lines ('Trapezoid or convex arc', '5 tip widths · 2 mm pitch').  The grid holds every combination of the axes'
    choices ('trap|13.8') once, each a variant of a part of this family, and every such variant is in it."""

    record = copy.deepcopy(family)
    axes = record["axes"]
    members = {row[0]: row for row in table if row[2].get("family") == family_id}
    if not members:
        raise LibraryError(f"parts.json: the family {family_id} has no part")
    if record["shelf"] not in parts["parts"] or parts["parts"][record["shelf"]].get("family"):
        raise LibraryError(f"parts.json: the family {family_id}'s shelf {record['shelf']} is not a gripper's part")
    keys = [""]
    for axis in axes:
        values = [choice["value"] for choice in axis["choices"]]
        if not values or len(set(values)) != len(values) or not all(isinstance(value, str) and "|" not in value for value in values):
            raise LibraryError(f"parts.json: the family {family_id}'s axis {axis.get('key')} has no distinct choices")
        keys = [f"{key}|{value}" if key else value for key in keys for value in values]
    if sorted(record["grid"]) != sorted(keys):
        raise LibraryError(f"parts.json: the family {family_id}'s grid is not every choice of its axes once")
    if sorted(record["grid"].values()) != sorted(members):
        raise LibraryError(f"parts.json: the family {family_id}'s grid and its parts' variants differ")
    if record["default"] not in members:
        raise LibraryError(f"parts.json: the family {family_id}'s default {record['default']} is not one of its sensors")
    pitches = sorted({row[3]["pitch_mm"] for row in members.values()})
    first = [choice["label"] for choice in axes[0]["choices"]]
    words = " or ".join([first[0]] + [word[:1].lower() + word[1:] for word in first[1:]])
    rest = " · ".join(f"{len(axis['choices'])} {re.sub(r' [(].*', '', axis['label']).lower()}s" for axis in axes[1:])
    pitch = " or ".join(f"{js_string(value)} mm" for value in pitches)
    record["lines"] = [words, " · ".join(item for item in (rest, f"{pitch} pitch") if item)]
    return record


def summary(part_id: str, part: dict, variant: dict, path: str, data: bytes) -> dict:
    """entries.json's record of one variant: its sensor (proposal #1 of its fit) and its fit file."""

    reply = json.loads(data.decode("utf-8"))["reply"]
    first = reply["proposals"][0]
    metrics = first["metrics"]
    symmetry = metrics.get("symmetry") or {}
    return {
        "part": part_id, "label": label(part, variant), "pitch_mm": variant["pitch_mm"], "fill": variant["fill"],
        "badge": variant.get("badge"), "fit": path, "fit_sha256": hashlib.sha256(data).hexdigest(),
        "build_id": first["build_id"], "rows": metrics["rows"], "columns": metrics["columns"], "taxels": metrics["taxels"],
        "field_mm": metrics["field_mm"], "row_tail_mm": metrics["row_tail_mm"], "column_tail_mm": metrics["column_tail_mm"],
        "symmetric_face": bool(symmetry.get("face")), "centred": bool(symmetry.get("field")),
        # The reader asked for (rules(): one tail pin per line) and the reader those tails fit anyway, if any (a 32 x 16
        # sensor's tails plug into the FlexiTac reader, surface.reader.of_readout).
        "reader": "none", "fits_reader": metrics.get("reader"),
        # The card's picture (library.js slot()): the on-part figure from shots/manifest.json (entries() sets it:
        # pictures()), else null and a placeholder drawn by the page.
        "image": None,
        # The sensor page's 3D view (view_record(): its art and its gripper's scene), set by entries() as "image" is
        # for a sensor whose record is current with its art; null: the page shows the picture only.
        "view": None,
    }


def entries(parts: dict, fits: dict, library: Path = LIBRARY) -> dict:
    """entries.json from parts.json and the fit files ({variant id: the file's bytes}), with each mesh's facts (its
    bytes and SHA-256 from the file, its facets and the guessed unit from the fits' replies, which must agree)."""

    from engine import GENERATOR_VERSION

    table = plan(parts)
    families = {family_id: family_record(family_id, family, parts, table) for family_id, family in (parts.get("families") or {}).items()}
    for part_id in parts["order"]:
        if parts["parts"][part_id].get("family") and parts["parts"][part_id]["family"] not in families:
            raise LibraryError(f"parts.json: {part_id}'s family {parts['parts'][part_id]['family']} is not listed")
    # The grid's cards and shelves are the grippers' (a family's parts are one card on its shelf's part).
    grippers = [part_id for part_id in parts["order"] if not parts["parts"][part_id].get("family")]
    document = {"format": FORMAT, "about": ENTRIES_ABOUT, "generator_version": GENERATOR_VERSION,
                "order": grippers, "start": [], "parts": {}, "families": families, "variants": {}}
    for part_id in parts["order"]:
        part = parts["parts"][part_id]
        own = [row for row in table if row[1] == part_id]
        mesh = (library / part["mesh"]["file"]).read_bytes()
        digest = hashlib.sha256(mesh).hexdigest()
        seen = set()
        for identifier, _, _, variant in own:
            reply_mesh = json.loads(fits[identifier].decode("utf-8"))["reply"]["mesh"]
            if reply_mesh["sha256"] != digest:
                raise LibraryError(f"{identifier}: its fit is of another mesh than {part['mesh']['file']}")
            seen.add((reply_mesh["facets"], reply_mesh["unit"]))
        if len(seen) != 1:
            raise LibraryError(f"{part_id}: its fits disagree on the mesh's facets or unit: {sorted(seen)}")
        ((facets, unit),) = seen
        default = next((row[0] for row in own if row[3]["pitch_mm"] == DEFAULT_PITCH), own[0][0])
        if part_id in grippers:
            document["start"].append(default)
        hosted = [family for family in families.values() if family["shelf"] == part_id]
        document["parts"][part_id] = {
            "title": part["title"], "maker": part["maker"], "finger": part["finger"],
            "shelf": None if part.get("family") else shelf([row[3] for row in own], hosted),
            "mesh": {"file": part["mesh"]["file"], "name": part["mesh"]["name"], "bytes": len(mesh), "sha256": digest,
                     "facets": facets, "unit": unit},
            "license": copy.deepcopy(part["license"]), "default": default, "variants": [row[0] for row in own],
            "family": part.get("family"),
        }
        for identifier, _, _, variant in own:
            document["variants"][identifier] = summary(part_id, part, variant, fit_path(identifier, variant), fits[identifier])
    images, _, _, views = pictures(document["variants"], library)
    for identifier, image in images.items():
        document["variants"][identifier]["image"] = image
        document["variants"][identifier]["view"] = views[identifier]
    return document


def entries_text(document: dict) -> str:
    return json.dumps(document, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


# -- the pictures ---------------------------------------------------------------------------------------------------
# The user's request of 2026-11-05 ("卡片上的图为手指+传感器叠加": the cards show the finger with the sensor on it, the
# generator's on-part figure, once it was approved: "现在这个view可以"; and "lib 点进去具体的每个夹爪的时候, 那个图也做成可以
# 三维旋转的": the pictures are the Library's own 3D view at its homes): tools/browser/library_shots.py shoots each sensor
# at library.html?probe=shoot#<id> (web/cad/library_view.js: the generator's on-part figure, web/cad/onpart.js, and a
# gripper's whole scene, web/cad/library_stage.js) into shots/, its art into art/, and writes shots/manifest.json; this
# module reads it, writes each variant's "image" and "view" from it and says where it no longer pictures the sensor.
# The pictures are WebP with alpha (the figure alone on a transparent background, for the page's light boxes): each
# sensor's Exploded and Assembled homes at 1280 x 800 (16:10, the figure framed by its own frameView at that aspect: its
# pane 640 x 400 CSS px at DPR 2) and the Exploded one at 640 x 400 for the grid's cards.  Paths relative to
# web/library/, as "fit".
SHOTS_FORMAT = "flexitac-library-shots/v1"
SHOTS_MANIFEST = "shots/manifest.json"
SHOTS_ABOUT = ("The Library's pictures (library.html's cards and sensor pages): each sensor of entries.json "
               "drawn by the Library's own 3D view (web/cad/library_view.js: Gen by Surface's sensor on the part, "
               "web/cad/onpart.js, and for a gripper its whole scene, web/cad/library_stage.js) at its Exploded "
               "and Assembled homes, with each file's bytes and SHA-256, the fit and build id it was shot from, "
               "the hashes of the figure's and the view's sources, the sensor's art (art/<id>.json.gz) and, for "
               "a gripper, its stage (its scene's hash and numbers).  A gripper is drawn whole (scenes/), the sensor "
               "finger's stack exploded and the near finger see-through in both views, its stack assembled.  "
               "Written by tools/browser/library_shots.py; tools/library_write.py writes entries.json's image and "
               "view from it.")
SHOT_SIZE = (1280, 800)
CARD_SIZE = (640, 400)
# kind: (the file's name after the id, its size).
SHOT_KINDS = {"exploded": ("exploded.webp", SHOT_SIZE), "assembled": ("assembled.webp", SHOT_SIZE),
              "card": ("exploded.card.webp", CARD_SIZE)}
SHOT_NAME = re.compile(r"^[a-z0-9.-]+\.(exploded|assembled|exploded\.card)\.webp$")
# The figure's sources: web/cad/onpart.js and the web/cad modules it imports, transitively (drape.js, studio.js,
# viewer.js for the part's grey, border.js under drape.js).  main.js, which calls it, and app.js, which gives the boards'
# art, are left out: both change for much else, and a picture of older sources is only a warning.
FIGURE_MODULE = "cad/onpart.js"
_IMPORT = re.compile(r"""^\s*import\s[^"';]*?\bfrom\s*["']\./([\w.-]+\.js)["']""", re.MULTILINE)
RESHOOT = "re-shoot with tools/browser/library_shots.py"


def shot_files(identifier: str) -> dict:
    """{kind: (the file relative to web/library/, its (width, height))} of one sensor's pictures."""

    return {kind: (f"shots/{identifier}.{name}", size) for kind, (name, size) in SHOT_KINDS.items()}


def image_record(identifier: str, label_text: str, picture: str | None = None) -> dict:
    """entries.json's "image" of a sensor with a current shot (library.js reads it; a family's card takes its default
    sensor's): the Exploded picture and its card, the Assembled picture, the text for the picture: its label and
    ``picture``, the words of its gripper's scene for a picture of the whole gripper (a record with its stage: 'on both
    fingers of the open gripper'), else 'on the part' (docs/LIBRARY_VIEW.md); the sensor page's 3D view takes it too."""

    files = shot_files(identifier)
    return {"exploded": {"src": files["exploded"][0], "card": files["card"][0], "width": SHOT_SIZE[0], "height": SHOT_SIZE[1]},
            "assembled": {"src": files["assembled"][0], "width": SHOT_SIZE[0], "height": SHOT_SIZE[1]},
            "alt": f"{label_text} {picture or 'on the part'}"}


def webp_info(data: bytes):
    """(width, height, alpha) of a WebP file's canvas, or None when ``data`` is not one: its RIFF header and size, then
    the extended layout (VP8X: the canvas and its alpha flag; what Pillow writes for a lossy picture with alpha), the
    lossless one (VP8L: its alpha bit) or the simple lossy one (VP8: never alpha)."""

    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP" or struct.unpack("<I", data[4:8])[0] + 8 != len(data):
        return None
    chunk, body = data[12:16], data[20:]
    if chunk == b"VP8X":
        return 1 + int.from_bytes(body[4:7], "little"), 1 + int.from_bytes(body[7:10], "little"), bool(body[0] & 0x10)
    if chunk == b"VP8L" and body[0] == 0x2F:
        bits = int.from_bytes(body[1:5], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1, bool((bits >> 28) & 1)
    if chunk == b"VP8 " and body[3:6] == b"\x9d\x01\x2a":
        return int.from_bytes(body[6:8], "little") & 0x3FFF, int.from_bytes(body[8:10], "little") & 0x3FFF, False
    return None


def figure_sources(read=None) -> dict:
    """{path relative to web/: its bytes} of the figure's sources (FIGURE_MODULE and what it imports from web/cad,
    transitively); ``read`` (path -> bytes) reads them from elsewhere (library_shots.py: from the server it shoots)."""

    read = read or (lambda path: (WEB / path).read_bytes())
    found, todo = {}, [FIGURE_MODULE]
    while todo:
        path = todo.pop()
        if path in found:
            continue
        found[path] = read(path)
        todo += [f"cad/{name}" for name in _IMPORT.findall(found[path].decode("utf-8"))]
    return dict(sorted(found.items()))


def figure_sha256(sources: dict | None = None) -> str:
    """The hash of the figure's sources: the SHA-256 of their sha256sum lines ('<hex>  web/<path>'), by path."""

    sources = figure_sources() if sources is None else sources
    lines = "".join(f"{hashlib.sha256(data).hexdigest()}  web/{path}\n" for path, data in sorted(sources.items()))
    return hashlib.sha256(lines.encode("ascii")).hexdigest()


def pictures(variants: dict, library: Path = LIBRARY, figure: str | None = None, view: str | None = None,
             require_view: bool | None = None) -> tuple:
    """(images, problems, older, views) of entries.json's variants ({id: summary()}) from shots/manifest.json:

    - images {id: image_record(), or None}: None without a shot, and for a shot with a problem; a record with its stage
      (the whole gripper pictured) takes its alt text from its scene's "picture";
    - problems [(id or None, message)]: a shot of another fit or build than the variant's (the wrong sensor pictured), a
      file missing, not the manifest's bytes or not a WebP with alpha of its size, a shot of no variant, a file of
      shots/ the manifest does not name; the 3D view's (docs/LIBRARY_VIEW.md): an art missing, not the manifest's
      bytes or document, not a gzip of an art document, or of another sensor or build (art_problems()), a file of art/
      the manifest does not name, a gripper's stage of another scene or rules (scene_sha256) or whose numbers break the
      rules' checks (stage_problems()), a stage recorded for a part that keeps the fingertip scene (the UMI finger and
      its tips), such a part's pictures of another look than the rules' part_looks give it now (part_look_sha256), and with ``require_view`` (VIEW_REQUIRED by default) a record without its art or a gripper's without
      its stage (library_write --check, the site build and tests/test_library.py refuse them);
    - older [id]: a current shot whose figure's sources (figure_sha256, or ``figure``) or 3D view's own modules
      (view_sha256, or ``view``) have changed since: still pictured, a warning only (re-shoot it; the public CI cannot);
    - views {id: view_record(), or None}: the 3D view of a current record with its art (and a gripper's with its stage);
      None for the others, which are pictured with no 3D view while ``require_view`` is false (a warning: view_note())."""

    require_view = VIEW_REQUIRED if require_view is None else require_view
    images = {identifier: None for identifier in variants}
    views = {identifier: None for identifier in variants}
    problems, older = [], []
    folder = library / "shots"
    path = library / SHOTS_MANIFEST
    if not path.is_file():
        if folder.is_dir() and any(folder.iterdir()):
            problems.append((None, f"shots/ holds files but no manifest.json: {RESHOOT}"))
        return images, problems + _stray_art(library, set()), older, views
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("format") != SHOTS_FORMAT:
        return images, [(None, f"{SHOTS_MANIFEST}: the format is {manifest.get('format')!r}, not {SHOTS_FORMAT}")], older, views
    index = scenes_index(library)
    staged = index.get("scenes") or {}
    # parts.json's parts (their families: a look the rules give a family), where the library has it.
    families = json.loads((library / "parts.json").read_text(encoding="utf-8")) if (library / "parts.json").is_file() else {"parts": {}}
    named, arts = {SHOTS_MANIFEST}, set()
    for identifier, shot in sorted((manifest.get("shots") or {}).items()):
        files = shot_files(identifier)
        named.update(relative for relative, _ in files.values())
        if identifier not in variants:
            problems.append((None, f"{identifier}: a picture of no sensor of entries.json: {RESHOOT}"))
            continue
        variant = variants[identifier]
        broken = []
        if (shot.get("fit_sha256"), shot.get("build_id")) != (variant["fit_sha256"], variant["build_id"]):
            broken.append(f"its pictures are of another fit (the wrong sensor pictured): {RESHOOT} --only {identifier}")
        for kind, (relative, size) in files.items():
            record = (shot.get("files") or {}).get(kind) or {}
            target = library / relative
            if not target.is_file():
                broken.append(f"{relative} is missing")
                continue
            data = target.read_bytes()
            if (record.get("path"), record.get("bytes"), record.get("sha256")) != (relative, len(data), hashlib.sha256(data).hexdigest()):
                broken.append(f"{relative} is not the file {SHOTS_MANIFEST} names")
            elif webp_info(data) != (size[0], size[1], True):
                broken.append(f"{relative} is not a {size[0]} x {size[1]} WebP with alpha")
        # The 3D view (docs/LIBRARY_VIEW.md): the art shot with, and a gripper's stage (its scene, as staged.get(part)).
        art, stage, scene, picture = shot.get("art"), shot.get("stage"), staged.get(variant["part"]), None
        fix = f"{RESHOOT} --only {identifier}"
        if art is not None:
            arts.add(art_path(identifier))
            broken += art_problems(identifier, variant, art, library)
        elif require_view:
            broken.append(f"no 3D view: its record names no art: {fix}")
        # A part without a scene whose look scenes.json's rules give (part_look()): its pictures are of that look.
        expected = part_look_sha256(part_look(index, families, variant["part"]))
        if shot.get("part_look_sha256") != expected:
            broken.append(f"its pictures are of another look of its part than {SCENES_INDEX}'s rules give now (part_looks): {fix}")
        if stage is not None and scene is None:
            broken.append(f"its record has a stage, but its part {variant['part']} keeps the fingertip scene (no scene in {SCENES_INDEX}): {fix}")
        elif stage is not None:
            found, picture = staging(identifier, stage, scene, index, library)
            broken += found
        elif scene is not None and require_view:
            broken.append(f"no 3D view of the whole gripper: its record has no stage ({scene}): {fix}")
        if broken:
            problems += [(identifier, f"{identifier}: {message}") for message in broken]
            continue
        images[identifier] = image_record(identifier, variant["label"], picture)
        figure = figure or figure_sha256()
        if shot.get("figure_sha256") != figure:
            older.append(identifier)
        if art is not None and (scene is None or stage is not None):
            views[identifier] = view_record(identifier, scene)
            view = view or view_sha256()
            if shot.get("view_sha256") != view and identifier not in older:
                older.append(identifier)
    for file in sorted(folder.iterdir()):
        if f"shots/{file.name}" not in named:
            problems.append((None, f"shots/{file.name}: not a picture of {SHOTS_MANIFEST}"))
    return images, problems + _stray_art(library, arts), older, views


# -- the Library's 3D view (the user's request of 2026-11-05: a sensor's page turns in 3D; docs/LIBRARY_VIEW.md) --------
# Its files' formats are frozen in docs/LIBRARY_VIEW.md: each sensor's art (art/<id>.json.gz, the generator's art of its
# two boards, written by the shots tool), the grippers' scenes (scenes/scenes.json and scenes/<part>.json, their bodies
# in bodies/<part>/) and the manifest's records of them.  VIEW_REQUIRED is set by the shoot that wrote every sensor's art
# and each gripper's stage (2026-11-06, the one explode and the fill 0.5 merged): a record without them is refused since
# (before it, such a record was pictured with no 3D view, a warning).
VIEW_REQUIRED = True
ART_FORMAT = "flexitac-library-art/v1"
SCENES_FORMAT = "flexitac-library-scenes/v1"
SCENE_FORMAT = "flexitac-library-scene/v1"
SCENES_INDEX = "scenes/scenes.json"
# The art's raster as Gen by Surface asks for it (web/cad/main.js ON_PART_PX_PER_MM, onpart.js's texture cap).
ART_PX_PER_MM = 12
ART_MAX_PX = 4096
# The Library view's own modules beside the figure's sources (figure_sources()): a picture of older ones is a warning.
VIEW_SOURCES = ("cad/library_view.js", "cad/library_stage.js", "cad/stl.js")


def art_path(identifier: str) -> str:
    """A sensor's art file, relative to web/library/ (as its fit)."""

    return f"art/{identifier}.json.gz"


def canonical_json(document) -> str:
    """JSON with sorted keys, compact and ASCII: the art's document and the rules as hashed."""

    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def art_bytes(document: dict) -> bytes:
    """The art file of its document: the canonical JSON, gzip at level 9 with no name, time 0 and OS byte 3 (Unix).

    Python before 3.11 writes the header's OS byte as 255 (unknown) and 3.11 on as 3, so the byte is set here: the
    same document gives the same bytes on every Python the project runs on (3.9 is CI's floor)."""

    data = gzip.compress(canonical_json(document).encode("ascii"), compresslevel=9, mtime=0)
    return data[:9] + b"\x03" + data[10:]


def read_art(data: bytes) -> dict:
    """The document of an art file."""

    return json.loads(gzip.decompress(data).decode("ascii"))


def view_sources(read=None) -> dict:
    """{path relative to web/: its bytes} of VIEW_SOURCES; ``read`` (path -> bytes) reads them from elsewhere."""

    read = read or (lambda path: (WEB / path).read_bytes())
    return {path: read(path) for path in VIEW_SOURCES}


def view_sha256(sources: dict | None = None) -> str:
    """The hash of the Library view's own modules, as figure_sha256 is of the figure's."""

    return figure_sha256(view_sources() if sources is None else sources)


def scene_sha256(scene: bytes, rules: dict) -> str:
    """A gripper's record's scene hash: the SHA-256 of the sha256sum lines of its scene file and of the rules'
    canonical JSON (scenes.json's "rules")."""

    lines = (f"{hashlib.sha256(scene).hexdigest()}  scene\n"
             f"{hashlib.sha256(canonical_json(rules).encode('ascii')).hexdigest()}  rules\n")
    return hashlib.sha256(lines.encode("ascii")).hexdigest()


def scenes_index(library: Path = LIBRARY) -> dict:
    """scenes/scenes.json, or an empty index (no rules, no scenes) where there is none."""

    path = library / SCENES_INDEX
    if not path.is_file():
        return {"format": SCENES_FORMAT, "rules": {}, "scenes": {}}
    return json.loads(path.read_text(encoding="utf-8"))


# The UMI finger (the page's default part) and its family's tapered tips keep the fingertip scene; every other part of
# the Library is a gripper, drawn whole on its sensor's page and in its pictures (the user's requests of 2026-11-05).
UMI_FINGER = "umi-finray"
# The bodies drawn by the project itself (no NOTICE row): the plain rail the MakerMods Metal Arm's two HandUMI tips stand
# on, not MakerMods hardware (its gripper body is not cleared: DENIED_SHA256).
OWN_BODIES = ("bodies/makermods-metal/rail.stl",)
# And, since the looks of 2026-11-12, the plain shapes tools/library_split.py draws where a model lacks a component the
# photos show (a screw head, a rail strip): bodies/<part>/drawn-<name>.stl, whose 80-byte header says so (OWN_HEADER and
# OWN_WORDS), never a vendor's geometry.  The header is a label, not the guard: tools/library_split.py --check draws
# each again from the numbers of its part's look file and refuses a scene that has a drawn body, a look or a crease
# angle without a look file (library_split.unowned(); tests/test_library_split.py runs it on the committed library).
OWN_BODY = re.compile(r"bodies/[a-z0-9-]+/drawn-[a-z0-9-]+\.stl")
OWN_HEADER = b"FlexiTac-Gen: "
OWN_WORDS = b"drawn by the project"
OPEN_LICENCES = ("Apache-2.0", "MIT", "BSD-3-Clause")
# NOTICE.md's tables: | `file` | source at commit | licence and holder | change | `sha256` |.
NOTICE_ROW = re.compile(r"^\| `([\w./-]+)` \|([^|\n]*)\|([^|\n]*)\|([^|\n]*)\| `([0-9a-f]{64})` \|$", re.MULTILINE)
REBUILD = "rebuild the scenes with the private tools/library_scenes.py"
# A scene's looks are written by the public tools/library_split.py from the part's look file, not by the scene builder.
RELOOK = "write the scene's looks again with tools/library_split.py (the part's look file, tools/library_looks/<part>.json)"
# The frozen keys (docs/LIBRARY_VIEW.md): scenes.json's, its rules', a scene's (and its optional overrides, within
# these bounds), a body's, the art document's and each of its boards'.
SCENES_KEYS = ("about", "format", "rules", "scenes")
RULE_NUMBERS = ("depth_tol_mm", "gap_share", "ghost_opacity", "min_step_mm")
RULES_KEYS = RULE_NUMBERS + ("camera", "checks", "explode_stacks", "measure_px", "see_through_modes")
CAMERA_MODES = ("assembled", "exploded")
CAMERA_KEYS = ("elevation_deg", "front", "tilt_deg")
CHECK_KEYS = ("card_min_px", "clearance_min_mm", "ghost_cover_min", "layer_visible_min", "near_seen_min", "opaque_cover_max",
              "stacks_apart_min_g", "stacks_apart_min_mm", "stacks_apart_min_px")
SCENE_KEYS = ("about", "approach", "bodies", "format", "frame", "mate", "opening", "part", "part_mesh_sha256", "picture", "see_through")
SCENE_FRAME = "the part's file axes, mm"
# A camera's bounds (the rules' and a scene's override: the angle off the face normal and the elevation, in degrees;
# front, which side of the gripper is its front, a sign) and an explode override's.
CAMERA_BOUNDS = {"tilt_deg": (45, 70), "elevation_deg": (15, 45)}
EXPLODE_BOUNDS = {"gap_share": (0.25, 0.45)}
BODY_KEYS = ("bytes", "finger", "matrix", "mesh", "sha256", "triangles")
FINGERS = ("sensor", "mate")
# The looks (docs/LIBRARY_VIEW.md "The looks"; the amendment of 2026-11-12, the user's request that every gripper be
# coloured after photos of the real product): optional keys of a scene ("looks": {name: look}, "part_look", "smooth_deg"),
# of a body ("look") and of scenes.json's rules ("looks", "part_looks", "part_smooth_deg": the parts without a scene).  A
# look is LOOK_KEYS and any of LOOK_OPTIONAL: an sRGB colour "#rrggbb" (lower case), numbers 0 to 1 (LOOK_UNIT), an
# env_intensity of 0 or more; a name is LOOK_NAME (lower case, digits, hyphens).  A crease angle is SMOOTH_BOUNDS degrees.
SCENE_OPTIONAL = ("camera", "explode", "looks", "part_look", "smooth_deg")
BODY_OPTIONAL = ("look",)
RULES_OPTIONAL = ("looks", "part_looks", "part_smooth_deg")
LOOK_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
LOOK_COLOR = re.compile(r"#[0-9a-f]{6}")
LOOK_KEYS = ("color", "metalness", "roughness")
LOOK_OPTIONAL = ("clearcoat", "clearcoat_roughness", "env_intensity")
LOOK_UNIT = ("metalness", "roughness", "clearcoat", "clearcoat_roughness")
LOOK_COAT = ("clearcoat", "clearcoat_roughness")
SMOOTH_BOUNDS = (1, 90)
ART_BOARD_KEYS = ("active_outline", "back", "front", "outline", "physical_side", "px", "region", "role", "view_box")
# A unit vector's length (a scene's approach) within UNIT_TOL of 1; a rigid matrix's rows' within ORTHONORMAL_TOL of
# 1 and their dot products of 0 (a scene builder writes its rotations' floats rounded).
UNIT_TOL = 1e-9
ORTHONORMAL_TOL = 1e-6
# Names that only the private importer's inputs carry (the design review of 2026-11-05: no scene, notice row or about
# may name them): its asset folders, the recipes and an absolute path; a part's id with underscores is its recipe's key.
PRIVATE_TEXT = re.compile(r"(?<![\w-])asset/|(?<![\w-])outputs/|gripper_recipes|\brecipes?\b"
                          r"|(?<![\w.~-])/(?:home|Users|tmp|root|mnt|opt|var|private|srv|media)/|\b[A-Za-z]:[\\/]|~/")


def look_problem(look, coat: bool = True) -> str | None:
    """Why ``look`` is not a look (docs/LIBRARY_VIEW.md "The looks"), or None: its keys LOOK_KEYS and any of
    LOOK_OPTIONAL, its colour an sRGB "#rrggbb" in lower case, its metalness, roughness and clear coat numbers 0 to 1,
    its env_intensity a number of 0 or more, a clearcoat_roughness only with a clearcoat; ``coat`` false: no clear coat
    at all (the part's own material is the figure's standard one: the stage cannot coat it)."""

    if not isinstance(look, dict) or not set(LOOK_KEYS) <= set(look) <= set(LOOK_KEYS) | set(LOOK_OPTIONAL):
        return f"has not the keys {', '.join(LOOK_KEYS)} (and any of {', '.join(LOOK_OPTIONAL)})"
    if not (isinstance(look["color"], str) and LOOK_COLOR.fullmatch(look["color"])):
        return f"has the colour {look['color']!r}, not an sRGB #rrggbb in lower case"
    for key in LOOK_UNIT:
        if key in look and not (_number(look[key]) and 0 <= look[key] <= 1):
            return f"has the {key} {look[key]!r}, not a number 0 to 1"
    if "env_intensity" in look and not (_number(look["env_intensity"]) and look["env_intensity"] >= 0):
        return f"has the env_intensity {look['env_intensity']!r}, not a number of 0 or more"
    if "clearcoat_roughness" in look and "clearcoat" not in look:
        return "has a clearcoat_roughness without a clearcoat"
    if not coat and any(key in look for key in LOOK_COAT):
        return "has a clear coat, which the part's own material cannot take (a body's look can)"
    return None


def looks_problems(looks, used: dict, uncoated=()) -> list:
    """Why a set of looks and their uses are not sound: ``looks`` {name: look} (LOOK_NAME, look_problem()), ``used``
    {what names it: the name}, each naming a look of ``looks``; the looks named ``uncoated`` (a part's own) without a
    clear coat; and every look used (a look nothing names is left out of the file)."""

    if not isinstance(looks, dict) or not looks:
        return ["its looks are not a map of names to looks"]
    found = []
    for name, look in looks.items():
        if not (isinstance(name, str) and LOOK_NAME.fullmatch(name)):
            found.append(f"its look {name!r} is not named in lower case, digits and hyphens")
            continue
        problem = look_problem(look, coat=name not in uncoated)
        if problem:
            found.append(f"its look {name} {problem}")
    for what, name in used.items():
        if not (isinstance(name, str) and name in looks):
            found.append(f"{what} names the look {name!r}, which is not one of its looks")
    for name in sorted(set(looks) - {name for name in used.values() if isinstance(name, str)}):
        found.append(f"its look {name!r} is used by nothing")
    return found


def own_body(mesh: str, data: bytes | None = None) -> bool:
    """Whether a scene's body is the project's own drawing (no NOTICE row): the rail (OWN_BODIES), or a shape of
    tools/library_split.py named bodies/<part>/drawn-<name>.stl whose header (``data``'s first 80 bytes, when given)
    says so."""

    if mesh in OWN_BODIES:
        return True
    if not (isinstance(mesh, str) and OWN_BODY.fullmatch(mesh)):
        return False
    return data is None or (data[:80].startswith(OWN_HEADER) and OWN_WORDS in data[:80])


def part_look(index: dict, parts: dict, part_id: str):
    """The look scenes.json's rules give a part without a scene (the UMI finger and its tapered tips; docs/LIBRARY_VIEW.md
    "The looks"): {"look": the look, "smooth_deg": the rules' part_smooth_deg or None}, by the part's id, else by its
    family's, in the rules' "part_looks" (a name of the rules' "looks", or the look itself); None without a rule (the
    part as Gen by Surface draws it) and for a gripper (its scene's looks)."""

    rules = index.get("rules") if isinstance(index, dict) else None
    named = (rules or {}).get("part_looks")
    if not isinstance(named, dict) or part_id in (index.get("scenes") or {}):
        return None
    family = parts["parts"].get(part_id, {}).get("family")
    chosen = named.get(part_id, named.get(family) if family else None)
    if chosen is None:
        return None
    look = (rules.get("looks") or {}).get(chosen) if isinstance(chosen, str) else chosen
    return {"look": look, "smooth_deg": rules.get("part_smooth_deg")}


def part_look_sha256(given) -> str | None:
    """A record's part_look_sha256: the SHA-256 of part_look()'s canonical JSON (None without a look)."""

    return None if given is None else hashlib.sha256(canonical_json(given).encode("ascii")).hexdigest()


def view_record(identifier: str, scene: str | None = None) -> dict:
    """entries.json's "view" of a sensor whose record is current with its art (pictures()): the art and, for a gripper
    drawn whole, its scene (scenes.json's path); a fingertip's scene is null (docs/LIBRARY_VIEW.md)."""

    return {"art": art_path(identifier), "scene": scene}


def art_record(identifier: str, data: bytes, build_id: str) -> dict:
    """The manifest's "art" of an art file (docs/LIBRARY_VIEW.md): its path, bytes, SHA-256, its document's canonical
    JSON's SHA-256 and the build it was drawn from."""

    return {"path": art_path(identifier), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "json_sha256": hashlib.sha256(canonical_json(read_art(data)).encode("ascii")).hexdigest(), "build_id": build_id}


def art_problems(identifier: str, variant: dict, record, library: Path = LIBRARY) -> list:
    """Why a record's art (the manifest's "art") is not the sensor's own: its file missing, not the bytes the record
    names, not a gzip of JSON, not the record's document, not an art document, of another sensor or build than the
    variant's, at another raster than the figure's, without the two boards and their outlines."""

    relative = art_path(identifier)
    fix = f"{RESHOOT} --only {identifier}"
    if not isinstance(record, dict) or record.get("path") != relative:
        return [f"its art is not {relative}: {fix}"]
    target = library / relative
    if not target.is_file():
        return [f"{relative} is missing: {fix}"]
    data = target.read_bytes()
    if (record.get("bytes"), record.get("sha256")) != (len(data), hashlib.sha256(data).hexdigest()):
        return [f"{relative} is not the file {SHOTS_MANIFEST} names: {fix}"]
    try:
        document = read_art(data)
        text = canonical_json(document)
    except (OSError, EOFError, ValueError, zlib.error):
        return [f"{relative} is not a gzip of a JSON document: {fix}"]
    if record.get("json_sha256") != hashlib.sha256(text.encode("ascii")).hexdigest():
        return [f"{relative}'s document is not the one {SHOTS_MANIFEST} names: {fix}"]
    if not isinstance(document, dict) or document.get("format") != ART_FORMAT:
        return [f"{relative} is not a {ART_FORMAT} document: {fix}"]
    if (record.get("build_id"), document.get("id"), document.get("build_id")) != (variant["build_id"], identifier, variant["build_id"]):
        return [f"its art is of another sensor or build than its fit's (the wrong boards drawn): {fix}"]
    if (document.get("px_per_mm"), document.get("max_px")) != (ART_PX_PER_MM, ART_MAX_PX):
        return [f"{relative} is drawn at {document.get('px_per_mm')} px per mm and {document.get('max_px')} px at most, "
                f"not the figure's {ART_PX_PER_MM} and {ART_MAX_PX}: {fix}"]
    boards = document.get("boards")
    if not isinstance(boards, dict) or sorted(boards) != ["column", "row"] or any(
            not isinstance(board, dict) or sorted(board) != list(ART_BOARD_KEYS) or not (board.get("outline") or {}).get("points")
            for board in boards.values()):
        return [f"{relative} has not the two boards' art with their outlines: {fix}"]
    return []


def _stray_art(library: Path, named: set) -> list:
    """art/'s files that no record of the manifest names (pictures()' problems)."""

    folder = library / "art"
    return [(None, f"art/{file.name}: not an art of {SHOTS_MANIFEST}: {RESHOOT}") for file in sorted(folder.iterdir())
            if f"art/{file.name}" not in named] if folder.is_dir() else []


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


# The stage's numbers a record keeps (docs/LIBRARY_VIEW.md, measured by the stage with ?probe=shoot).
STAGE_NUMBERS = ("jaw_gap_mm", "step_mm", "drape_step_mm", "face_tilt_deg", "visible_min", "opaque_max", "assembled_opaque",
                 "ghost_cover", "clearance_mm", "card_px", "band_css", "near_seen", "stacks_apart_px")


def stage_problems(numbers, checks: dict, see_through=(), explode_stacks=("sensor",)) -> list:
    """The rules of scenes.json's "checks" that a gripper's recorded stage numbers break, each named: every exploding
    layer (the stacks of ``explode_stacks``: the sensor finger's) at least ``layer_visible_min`` visible in Exploded, the
    bodies and the other finger covering less than ``opaque_cover_max`` of a layer drawn there (and of stack 1's top FPC
    in Assembled), the bodies and the other finger ``clearance_min_mm`` from the field, the exploded stack
    ``stacks_apart_min_g`` of the jaw gap and ``stacks_apart_min_mm`` from the other finger's stack, their silhouettes
    ``stacks_apart_min_px`` apart on screen, the card's top FPC ``card_min_px`` wide and tall, a see-through finger
    veiling at least ``ghost_cover_min`` (and none without one), and the near stack, assembled when the mate's stack
    does not explode, at least ``near_seen_min`` seen in both modes (null exactly when it explodes)."""

    if not isinstance(numbers, dict) or sorted(numbers) != sorted(STAGE_NUMBERS):
        return [f"its stage's numbers are not {', '.join(STAGE_NUMBERS)}"]
    clearance = numbers["clearance_mm"] if isinstance(numbers["clearance_mm"], dict) else {}
    card = numbers["card_px"] if isinstance(numbers["card_px"], list) and len(numbers["card_px"]) == 2 else [None]
    gap, share = numbers["jaw_gap_mm"], checks.get("stacks_apart_min_g")
    found = []
    rules = [("visible_min", numbers["visible_min"], ">=", "layer_visible_min", checks.get("layer_visible_min")),
             ("opaque_max", numbers["opaque_max"], "<", "opaque_cover_max", checks.get("opaque_cover_max")),
             ("assembled_opaque", numbers["assembled_opaque"], "<", "opaque_cover_max", checks.get("opaque_cover_max")),
             ("clearance_mm.bodies", clearance.get("bodies"), ">=", "clearance_min_mm", checks.get("clearance_min_mm")),
             ("clearance_mm.other_finger", clearance.get("other_finger"), ">=", "clearance_min_mm", checks.get("clearance_min_mm")),
             ("clearance_mm.stacks", clearance.get("stacks"), ">=", "stacks_apart_min_g x jaw_gap_mm",
              share * gap if _number(share) and _number(gap) else None),
             ("card_px", min(card) if all(_number(side) for side in card) else None, ">=", "card_min_px", checks.get("card_min_px")),
             ("clearance_mm.stacks", clearance.get("stacks"), ">=", "stacks_apart_min_mm", checks.get("stacks_apart_min_mm")),
             ("stacks_apart_px", numbers["stacks_apart_px"], ">=", "stacks_apart_min_px", checks.get("stacks_apart_min_px"))]
    if "mate" in (explode_stacks or ()):
        if numbers["near_seen"] is not None:
            found.append(f"near_seen is {numbers['near_seen']}, with the mate's stack exploding")
    else:
        rules.append(("near_seen", numbers["near_seen"], ">=", "near_seen_min", checks.get("near_seen_min")))
    if see_through:
        rules.append(("ghost_cover", numbers["ghost_cover"], ">=", "ghost_cover_min", checks.get("ghost_cover_min")))
    elif numbers["ghost_cover"] is not None:
        found.append(f"ghost_cover is {numbers['ghost_cover']}, with no see-through finger in its scene")
    for name, value, sign, rule, limit in rules:
        if not (_number(value) and _number(limit)):
            found.append(f"{name} ({value!r}) or its rule {rule} ({limit!r}) is not a number")
        elif not (value >= limit if sign == ">=" else value < limit):
            found.append(f"{name} {value} breaks the rule {rule}: not {sign} {round(limit, 6)}")
    if not (_number(gap) and gap > 0):
        found.append(f"jaw_gap_mm ({gap!r}) is not a positive number")
    return found


def staging(identifier: str, stage, scene: str, index: dict, library: Path = LIBRARY) -> tuple:
    """(problems, picture) of a gripper's record's stage: its scene the part's (scenes.json), its scene_sha256 the scene
    file's and the rules' now, its numbers keeping the rules' checks; picture: the scene's words for the alt text."""

    fix = f"{RESHOOT} --only {identifier}"
    if not isinstance(stage, dict) or sorted(stage) != ["numbers", "scene", "scene_sha256"] or stage.get("scene") != scene:
        return [f"its stage is not of its part's scene {scene}: {fix}"], None
    try:
        data = (library / scene).read_bytes()
        document = json.loads(data.decode("utf-8"))
        picture, see_through = document.get("picture"), document.get("see_through")
    except (OSError, ValueError, AttributeError):
        return [f"its scene {scene} cannot be read: {REBUILD}, then {fix}"], None
    rules = index.get("rules") or {}
    if stage.get("scene_sha256") != scene_sha256(data, rules):
        return [f"its stage is of another scene or other rules than {scene} and {SCENES_INDEX}'s now: {fix}"], None
    found = [f"its stage breaks a rule of {SCENES_INDEX}: {message}: {fix}"
             for message in stage_problems(stage.get("numbers"), rules.get("checks") or {}, see_through, rules.get("explode_stacks"))]
    return found, picture if isinstance(picture, str) and picture else None


def _rigid(matrix) -> str | None:
    """Why ``matrix`` is not a rigid 4 x 4 (rows applied to column vectors: its last row 0, 0, 0, 1 and its upper 3 x 3
    orthonormal, to ORTHONORMAL_TOL, in pure Python), or None."""

    if not (isinstance(matrix, list) and len(matrix) == 4
            and all(isinstance(row, list) and len(row) == 4 and all(_number(value) for value in row) for row in matrix)):
        return "is not a 4 x 4 array of numbers"
    if matrix[3] != [0, 0, 0, 1]:
        return "has a last row other than 0, 0, 0, 1"
    for first in range(3):
        for second in range(3):
            dot = math.fsum(matrix[first][axis] * matrix[second][axis] for axis in range(3))
            if abs(dot - (1 if first == second else 0)) > ORTHONORMAL_TOL:
                return "is not orthonormal (its upper 3 x 3)"
    return None


def determinant(matrix) -> float:
    """The determinant of a 4 x 4's upper 3 x 3: +1 for a turn, -1 for a mirror image (a rigid matrix's)."""

    (a, b, c), (d, e, f), (g, h, i) = (row[:3] for row in matrix[:3])
    return math.fsum((a * e * i, -a * f * h, -b * d * i, b * f * g, c * d * h, -c * e * g))


def stl_triangles(data: bytes):
    """The facet count of a binary STL (84 + 50 n bytes), or None when ``data`` is not one."""

    if len(data) < 84:
        return None
    (count,) = struct.unpack("<I", data[80:84])
    return count if len(data) == 84 + 50 * count else None


def gripper_parts(parts: dict) -> list:
    """The parts drawn whole, in parts.json's order: all but the UMI finger and its family's tapered tips."""

    return [part_id for part_id in parts["order"] if part_id != UMI_FINGER and not parts["parts"][part_id].get("family")]


def _camera(group, whole: bool = True) -> bool:
    """Whether ``group`` is a camera (CAMERA_KEYS: all of them, or with ``whole`` false some) within CAMERA_BOUNDS and
    its front a sign."""

    if not (isinstance(group, dict) and group and set(group) <= set(CAMERA_KEYS) and (not whole or sorted(group) == list(CAMERA_KEYS))):
        return False
    return all(_number(group[key]) and (group[key] in (1, -1) if key == "front" else CAMERA_BOUNDS[key][0] <= group[key] <= CAMERA_BOUNDS[key][1])
               for key in group)


def _index_problems(index) -> list:
    """Why scenes.json is not the frozen index (docs/LIBRARY_VIEW.md): its keys, its format, its rules' keys and numbers."""

    if not isinstance(index, dict) or sorted(index) != list(SCENES_KEYS):
        return [f"{SCENES_INDEX} has not the keys {', '.join(SCENES_KEYS)}"]
    if index["format"] != SCENES_FORMAT:
        return [f"{SCENES_INDEX}: the format is {index['format']!r}, not {SCENES_FORMAT}"]
    rules = index["rules"]
    if not isinstance(rules, dict) or not set(RULES_KEYS) <= set(rules) <= set(RULES_KEYS) | set(RULES_OPTIONAL):
        return [f"{SCENES_INDEX}: its rules have not the keys {', '.join(sorted(RULES_KEYS))} (and any of {', '.join(RULES_OPTIONAL)})"]
    found = [f"{SCENES_INDEX}: its rule {key} ({rules[key]!r}) is not a positive number"
             for key in RULE_NUMBERS if not (_number(rules[key]) and rules[key] > 0)]
    size = rules["measure_px"]
    if not (isinstance(size, list) and len(size) == 2 and all(_number(side) and side > 0 for side in size)):
        found.append(f"{SCENES_INDEX}: its rule measure_px ({size!r}) is not a width and a height")
    camera = rules["camera"]
    if not (isinstance(camera, dict) and sorted(camera) == list(CAMERA_MODES) and all(_camera(camera[mode]) for mode in camera)):
        found.append(f"{SCENES_INDEX}: its rules' camera is not {{exploded, assembled}} each of {', '.join(CAMERA_KEYS)} within their bounds")
    checks = rules["checks"]
    if not (isinstance(checks, dict) and sorted(checks) == list(CHECK_KEYS) and all(_number(value) for value in checks.values())):
        found.append(f"{SCENES_INDEX}: its rules' checks are not {', '.join(CHECK_KEYS)} of numbers")
    # The user's decision of 2026-11-06: the stacks that explode (the sensor finger's among them; ["sensor"] the decision,
    # ["sensor", "mate"] int4's two) and the modes the scenes' see-through fingers are ghosted in.
    stacks = rules["explode_stacks"]
    if not (isinstance(stacks, list) and all(isinstance(name, str) for name in stacks) and len(set(stacks)) == len(stacks)
            and "sensor" in stacks and set(stacks) <= set(FINGERS)):
        found.append(f"{SCENES_INDEX}: its rule explode_stacks ({stacks!r}) is not the fingers whose stacks explode "
                     f"(distinct, of {', '.join(FINGERS)}, the sensor's among them)")
    modes = rules["see_through_modes"]
    if not (isinstance(modes, list) and modes and all(isinstance(mode, str) for mode in modes) and len(set(modes)) == len(modes)
            and set(modes) <= set(CAMERA_MODES)):
        found.append(f"{SCENES_INDEX}: its rule see_through_modes ({modes!r}) is not the modes the see-through fingers are "
                     f"ghosted in (distinct, of {', '.join(CAMERA_MODES)}, at least one)")
    if not isinstance(index["scenes"], dict):
        found.append(f"{SCENES_INDEX}: its scenes is not a map of parts to scene files")
    # The looks of the parts without a scene (the amendment of 2026-11-12): part_looks {part or family: a name of the
    # rules' looks, or a look}, no clear coat (the part's own material), every look of the rules used; a crease angle.
    named = rules.get("part_looks")
    if "part_looks" in rules and not (isinstance(named, dict) and named and all(isinstance(key, str) for key in named)):
        found.append(f"{SCENES_INDEX}: its rule part_looks is not a map of parts (or families) to looks")
        named = None
    for key, value in (named or {}).items():
        problem = None if isinstance(value, str) else look_problem(value, coat=False)
        if problem:
            found.append(f"{SCENES_INDEX}: its rule part_looks: the look of {key} {problem}")
    by_name = {f"its rule part_looks ({key})": value for key, value in (named or {}).items() if isinstance(value, str)}
    if "looks" in rules or by_name:
        found += [f"{SCENES_INDEX}: {message}" for message in looks_problems(rules.get("looks"), by_name, set(by_name.values()))]
    if "part_smooth_deg" in rules:
        angle = rules["part_smooth_deg"]
        if not (_number(angle) and SMOOTH_BOUNDS[0] <= angle <= SMOOTH_BOUNDS[1]):
            found.append(f"{SCENES_INDEX}: its rule part_smooth_deg ({angle!r}) is not a crease angle of {SMOOTH_BOUNDS[0]} to {SMOOTH_BOUNDS[1]} degrees")
        if "part_looks" not in rules:
            found.append(f"{SCENES_INDEX}: its rule part_smooth_deg without part_looks")
    return found


def scene_problems(part_id: str, document, parts: dict, library: Path, rows: dict, scene: str | None = None) -> list:
    """Why one gripper's scene (scenes/<part>.json) is not drawable as docs/LIBRARY_VIEW.md has it: its keys and format,
    its part and the part's mesh (parts.json's SHA-256), its frame, a unit approach, the mate (a rigid matrix whose
    determinant's sign is its kind, and a body for it when the part's own mesh is not drawn there), each body (its file
    in bodies/<part>/, its bytes, SHA-256 and triangles, a rigid matrix, its finger), the see-through fingers, the
    alt text's words, the overrides within their bounds with their reason in "about", each body file tabled in
    NOTICE.md (``rows``) with an open licence or the project's own, and no denied model among them.  ``scene``: the
    scene's own name where it is not its part's (the showcase's, drawn about the UMI finger: scenes/<scene>.json, its
    bodies in bodies/<scene>/)."""

    scene = scene or part_id
    name = f"scenes/{scene}.json"
    if not isinstance(document, dict) or not set(SCENE_KEYS) <= set(document) <= set(SCENE_KEYS) | set(SCENE_OPTIONAL):
        return [f"{name} has not the keys {', '.join(SCENE_KEYS)} (and any of {', '.join(SCENE_OPTIONAL)})"]
    found = []
    if document["format"] != SCENE_FORMAT:
        found.append(f"{name}: the format is {document['format']!r}, not {SCENE_FORMAT}")
    if document["part"] != part_id:
        found.append(f"{name} is the scene of {document['part']!r}")
    if document["part_mesh_sha256"] != parts["parts"][part_id]["mesh"]["sha256"]:
        found.append(f"{name} is drawn about another mesh of {part_id} than parts.json's (part_mesh_sha256)")
    if document["frame"] != SCENE_FRAME:
        found.append(f"{name}: its frame is not {SCENE_FRAME!r}")
    approach = document["approach"]
    if not (isinstance(approach, list) and len(approach) == 3 and all(_number(value) for value in approach)
            and abs(math.fsum(value * value for value in approach) - 1) <= UNIT_TOL):
        found.append(f"{name}: its approach {approach!r} is not a unit vector")
    opening = document["opening"]
    if not (isinstance(opening, dict) and set(opening) <= {"q_mm", "limit_mm", "joint", "source"}
            and _number(opening.get("q_mm")) and _number(opening.get("limit_mm")) and 0 < opening["q_mm"] <= opening["limit_mm"]):
        found.append(f"{name}: its opening is not {{q_mm, limit_mm, joint, source}} with 0 < q_mm <= limit_mm")
    mate = document["mate"]
    bodies = document["bodies"] if isinstance(document["bodies"], list) else None
    if not isinstance(mate, dict) or sorted(mate) != ["kind", "matrix", "part"]:
        found.append(f"{name}: its mate is not {{kind, matrix, part}}")
    else:
        problem = _rigid(mate["matrix"])
        if problem:
            found.append(f"{name}: its mate's matrix {problem}")
        elif mate["kind"] != ("turned" if determinant(mate["matrix"]) > 0 else "mirror"):
            found.append(f"{name}: its mate is {mate['kind']!r}, but its matrix's determinant is {determinant(mate['matrix']):+.0f}")
        if not isinstance(mate["part"], bool):
            found.append(f"{name}: its mate's part is not true or false")
        elif not mate["part"] and not any(isinstance(body, dict) and body.get("finger") == "mate" for body in bodies or []):
            found.append(f"{name}: its mate draws no part and no body is the mate's finger")
    if bodies is None or not bodies:
        found.append(f"{name}: its bodies are not a list of bodies")
    for number, body in enumerate(bodies or []):
        label = f"{name}: body {number + 1}"
        if not isinstance(body, dict) or not set(BODY_KEYS) <= set(body) <= set(BODY_KEYS) | set(BODY_OPTIONAL):
            found.append(f"{label} has not the keys {', '.join(BODY_KEYS)} (and look)")
            continue
        mesh = body["mesh"]
        if not (isinstance(mesh, str) and re.fullmatch(rf"bodies/{re.escape(scene)}/[\w.-]+\.stl", mesh)):
            found.append(f"{label}'s mesh {mesh!r} is not a file of bodies/{scene}/")
            continue
        target = library / mesh
        if not target.is_file():
            found.append(f"{label}: {mesh} is missing")
            continue
        data = target.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if (body["sha256"], body["bytes"], body["triangles"]) != (digest, len(data), stl_triangles(data)):
            found.append(f"{label}: {mesh} is not the file its scene names (its SHA-256, bytes or triangles; a binary STL)")
        if digest in DENIED_SHA256 or DENIED_NAME.search(mesh):
            found.append(f"{label}: {mesh} is a vendor model of the deny-list ({DENIED_SHA256.get(digest, mesh)}): never in the Library")
        if OWN_BODY.fullmatch(mesh) and not own_body(mesh, data):
            found.append(f"{label}: {mesh} is named as the project's own drawing, but its header does not say so "
                         f"({OWN_HEADER.decode('ascii')}... {OWN_WORDS.decode('ascii')}): draw it with tools/library_split.py")
        elif not own_body(mesh, data):
            row = rows.get(mesh)
            if row is None or row[4] != digest:
                found.append(f"{label}: {mesh} has no row of NOTICE.md with its SHA-256")
            elif not any(licence in row[2] for licence in OPEN_LICENCES) or not re.findall(r"`(licenses/[\w.-]+)`", row[2]) or not all(
                    (library / text).is_file() for text in re.findall(r"`(licenses/[\w.-]+)`", row[2])):
                found.append(f"{label}: {mesh}'s NOTICE row names no open licence ({', '.join(OPEN_LICENCES)}) with its text")
        problem = _rigid(body["matrix"])
        if problem:
            found.append(f"{label}'s matrix {problem}")
        if body["finger"] is not None and body["finger"] not in FINGERS:
            found.append(f"{label}'s finger {body['finger']!r} is not sensor, mate or null")
    see_through = document["see_through"]
    if not (isinstance(see_through, list) and len(set(see_through)) == len(see_through) and set(see_through) <= set(FINGERS)):
        found.append(f"{name}: its see_through {see_through!r} is not a subset of {list(FINGERS)}")
    if not (isinstance(document["picture"], str) and document["picture"].strip()):
        found.append(f"{name}: its picture (the alt text's words) is empty")
    if not isinstance(document["about"], str) or not document["about"].strip():
        found.append(f"{name}: its about is empty")
    overrides = [key for key in ("camera", "explode") if key in document]
    camera = document.get("camera")
    if "camera" in overrides and not (isinstance(camera, dict) and camera and set(camera) <= set(CAMERA_MODES)
                                      and all(_camera(camera[mode], whole=False) for mode in camera)):
        found.append(f"{name}: its camera override {camera!r} is not {{exploded or assembled: {', '.join(CAMERA_KEYS)}}} "
                     "within tilt_deg 45 to 70, elevation_deg 15 to 45, front 1 or -1")
    explode = document.get("explode")
    if "explode" in overrides and not (isinstance(explode, dict) and sorted(explode) == ["gap_share"] and _number(explode["gap_share"])
                                       and EXPLODE_BOUNDS["gap_share"][0] <= explode["gap_share"] <= EXPLODE_BOUNDS["gap_share"][1]):
        found.append(f"{name}: its explode override {explode!r} is not {{gap_share}} within 0.25 to 0.45")
    if overrides and "reason" not in str(document["about"]):
        found.append(f"{name}: its override ({', '.join(overrides)}) has no reason in its about")
    return found


def scene_look_problems(part_id: str, document, scene: str | None = None) -> list:
    """Why one gripper's scene's looks are not sound (the amendment of 2026-11-12, docs/LIBRARY_VIEW.md "The looks"):
    every name a body or part_look gives is a look of the scene, every look is used, the part's has no clear coat (a
    body's look or a part_look without looks is refused as a name of none), smooth_deg a crease angle.  These are
    tools/library_split.py's to write (RELOOK), not the scene builder's.  ``scene``: the scene's own name where it is
    not its part's (the showcase's, as scene_problems() has it; its looks are tools/library_showcase.py's to write)."""

    name = f"scenes/{scene or part_id}.json"
    if not isinstance(document, dict):
        return []
    found = []
    bodies = document["bodies"] if isinstance(document.get("bodies"), list) else None
    used = {f"body {number + 1}": body["look"] for number, body in enumerate(bodies or []) if isinstance(body, dict) and "look" in body}
    if "part_look" in document:
        used["its part_look"] = document["part_look"]
    if "looks" in document or used:
        part_name = document.get("part_look") if isinstance(document.get("part_look"), str) else None
        found += [f"{name}: {message}" for message in looks_problems(document.get("looks"), used, {part_name})]
    if "smooth_deg" in document:
        angle = document["smooth_deg"]
        if not (_number(angle) and SMOOTH_BOUNDS[0] <= angle <= SMOOTH_BOUNDS[1]):
            found.append(f"{name}: its smooth_deg ({angle!r}) is not a crease angle of {SMOOTH_BOUNDS[0]} to {SMOOTH_BOUNDS[1]} degrees")
    return found


def showcase_notice_problems(text: str) -> list:
    """Why the vendor showcase's notice (web/vendor/ufactory-g1/NOTICE.md) is not the one the decision of 2026-11-12
    asks for: each wording of SHOWCASE_WORDS in its text (white space folded), never the word CAD, the source file's
    name and SHA-256, a row for each file of SHOWCASE_VENDOR_FILES and no other (NOTICE_ROW's columns: the file, what
    it is, SHOWCASE_OWNER, SHOWCASE_CHANGE with a deviation within the tolerance, its pinned SHA-256), and no hash of
    the deny-list."""

    name = f"web/{SHOWCASE_VENDOR}/{SHOWCASE_NOTICE}"
    folded = " ".join(text.split())
    found = [f"{name} does not say {words!r}" for words in SHOWCASE_WORDS if words not in folded]
    if re.search(r"\bCAD\b", text):
        found.append(f"{name} says CAD (the page's words are 3D model)")
    for words in SHOWCASE_SOURCE[:2]:
        if words not in folded:
            found.append(f"{name} does not name the file its meshes are made from ({words})")
    rows = {row[0]: row for row in NOTICE_ROW.findall(text)}
    for path in sorted(set(rows) - set(SHOWCASE_VENDOR_FILES)):
        found.append(f"{name} tables {path}, no file of the showcase")
    for path, pinned in sorted(SHOWCASE_VENDOR_FILES.items()):
        row = rows.get(path)
        if row is None or row[4] != pinned:
            found.append(f"{name} has no row of {path} with its pinned SHA-256")
            continue
        if row[2].strip() != SHOWCASE_OWNER:
            found.append(f"{name}: the row of {path} does not say {SHOWCASE_OWNER!r}")
        change = SHOWCASE_CHANGE.fullmatch(row[3].strip())
        if not change or float(change.group(1)) > SHOWCASE_TOLERANCE_MM:
            found.append(f"{name}: the row of {path} does not say how it was modified (split, decimated within {SHOWCASE_TOLERANCE_MM} mm)")
    for digest in sorted(set(re.findall(r"\b[0-9a-f]{64}\b", text)) & set(DENIED_SHA256)):
        found.append(f"{name} names {DENIED_SHA256[digest]} ({digest[:12]}), a vendor model of the deny-list")
    return found


def showcase(parts: dict, library: Path = LIBRARY, rows: dict | None = None) -> tuple:
    """(problems, bodies) of the Library's showcase (the comment at SHOWCASE_ID): nothing of a library without it
    (neither its scene nor its folder: the tests' own libraries); else problems, the messages library_write --check,
    the site build and tests/test_library.py refuse, and bodies, the files of bodies/ its scene draws:

    - the vendor's folder (``library``/../vendor/ufactory-g1/) holding other files than SHOWCASE_VENDOR_FILES and its
      notice, one of them not at its pinned SHA-256 (a binary STL), the folder over its byte budget;
    - the notice not the decision's (showcase_notice_problems());
    - the vendor's file itself (SHOWCASE_SOURCE: its SHA-256, or its size and its triangles' under another header),
      a model of the deny-list (DENIED_SHA256) or a copy of one of the folder's meshes outside its place, anywhere
      under ``library``/../ (every file there is hashed);
    - a part, entry, fit, picture record, sample or other scene naming the folder (SHOWCASE_REFERENCE);
    - the scene (scenes/flexitac-g1.json) missing or not drawable: a scene of the UMI finger as scene_problems() has
      every scene, its own bodies in bodies/flexitac-g1/ (tabled in NOTICE.md with an open licence, or a shape the
      project drew; at their pinned SHA-256, SHOWCASE_BODIES), and the vendor's as "../vendor/ufactory-g1/<file>": a
      file of the folder, the body's bytes, SHA-256 and triangles the file's, a rigid matrix, its finger; every file of
      the folder drawn;
    - the showcase's page's document (showcase.json), its placed record and its pictures (showcase_page())."""

    web = library.parent
    folder = web / SHOWCASE_VENDOR
    target = library / SHOWCASE_SCENE
    if not target.is_file() and not folder.is_dir():
        return [], set()
    found = []
    held = sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_file()) if folder.is_dir() else []
    allowed = sorted([*SHOWCASE_VENDOR_FILES, SHOWCASE_NOTICE])
    for name in sorted(set(held) - set(allowed)):
        found.append(f"web/{SHOWCASE_VENDOR}/{name} is no file of the showcase (its meshes and its notice alone): {REMOVE_FILE}")
    for name in sorted(set(allowed) - set(held)):
        found.append(f"web/{SHOWCASE_VENDOR}/{name} is missing")
    files = {}
    for name, pinned in sorted(SHOWCASE_VENDOR_FILES.items()):
        if name in held:
            files[name] = (folder / name).read_bytes()
            if hashlib.sha256(files[name]).hexdigest() != pinned or stl_triangles(files[name]) is None:
                found.append(f"web/{SHOWCASE_VENDOR}/{name} is not the showcase's pinned file (its SHA-256; a binary STL)")
    size = sum(path.stat().st_size for path in folder.rglob("*") if path.is_file()) if folder.is_dir() else 0
    if size > SHOWCASE_VENDOR_BUDGET_BYTES:
        found.append(f"web/{SHOWCASE_VENDOR}/ is {size} bytes, over its budget of {SHOWCASE_VENDOR_BUDGET_BYTES}")
    if SHOWCASE_NOTICE in held:
        found += showcase_notice_problems((folder / SHOWCASE_NOTICE).read_text(encoding="utf-8"))
    # Every file under web/, by its SHA-256.  The vendor's own file, unsplit and undecimated, is never published (the
    # file, or its triangles under another 80-byte header), nor is a model of the deny-list (the file's undecimated
    # pieces among them); and the folder's meshes are nowhere but in their places: a copy elsewhere would be the
    # vendor's 3D model outside its category, with no name of the folder to give it away (the review of 2026-11-12).
    places = {pinned: f"{SHOWCASE_VENDOR}/{name}" for name, pinned in SHOWCASE_VENDOR_FILES.items()}
    for path in sorted(web.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(web).as_posix()
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest == SHOWCASE_SOURCE[1] or (len(data) == SHOWCASE_SOURCE[2] and hashlib.sha256(data[80:]).hexdigest() == SHOWCASE_SOURCE_TRIANGLES):
            found.append(f"web/{relative} is {SHOWCASE_SOURCE[0]} itself, unsplit and undecimated: never published: {REMOVE_FILE}")
        if digest in DENIED_SHA256:
            found.append(f"web/{relative} is a vendor model of the deny-list ({DENIED_SHA256[digest]}): never published: {REMOVE_FILE}")
        if digest in places and relative != places[digest]:
            found.append(f"web/{relative} is a copy of web/{places[digest]}: the vendor's 3D model is shown in web/{SHOWCASE_VENDOR}/ alone: "
                         f"{REMOVE_FILE}")
    # Only the showcase's own scene names the folder: nothing the generator fits or draws may.
    readers = [library / "parts.json", library / "entries.json", library / SHOTS_MANIFEST, *sorted((library / "fits").glob("*.json")),
               *sorted(path for path in (library / "scenes").glob("*.json") if path != target),
               *sorted(path for path in (web / "samples").rglob("*") if path.suffix in (".json", ".md")),
               *sorted((web / "vendor" / "umi").glob("*.json"))]
    for path in readers:
        if path.is_file() and SHOWCASE_REFERENCE.search(path.read_text(encoding="utf-8", errors="replace")):
            found.append(f"web/{path.relative_to(web).as_posix()} names the showcase's folder (web/{SHOWCASE_VENDOR}/): only {SHOWCASE_SCENE} may")
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return found + [f"{SHOWCASE_SCENE} is missing or not JSON"], set()
    listed = document.get("bodies") if isinstance(document, dict) and isinstance(document.get("bodies"), list) else []
    prefix = f"../{SHOWCASE_VENDOR}/"
    vendor = [(number, body) for number, body in enumerate(listed)
              if isinstance(body, dict) and isinstance(body.get("mesh"), str) and body["mesh"].startswith("../")]
    beside = {number for number, _ in vendor}
    own = [body for number, body in enumerate(listed) if number not in beside]
    if rows is None:
        notice = (library / "NOTICE.md").read_text(encoding="utf-8") if (library / "NOTICE.md").is_file() else ""
        rows = {row[0]: row for row in NOTICE_ROW.findall(notice)}
    # The scene's looks by the Library's one rule (scene_look_problems(), as every gripper's: every name a look of the
    # scene, every look used, the part's without a clear coat; the crease angle), over all its bodies, the vendor's
    # too; then the scene as any gripper's (scene_problems()), about the UMI finger, with its own bodies (the scene
    # lists them first, so a body's number is its place in the scene); then the vendor's bodies.
    found += scene_look_problems(UMI_FINGER, document, scene=SHOWCASE_ID)
    if isinstance(document, dict) and listed:
        found += scene_problems(UMI_FINGER, dict(document, bodies=own), parts, library, rows, scene=SHOWCASE_ID)
    else:
        found += scene_problems(UMI_FINGER, document, parts, library, rows, scene=SHOWCASE_ID)
    bodies = {body["mesh"] for body in own if isinstance(body, dict) and isinstance(body.get("mesh"), str)
              and body["mesh"].startswith(f"bodies/{SHOWCASE_ID}/")}
    for mesh in sorted(bodies):
        if mesh not in SHOWCASE_BODIES:
            found.append(f"{SHOWCASE_SCENE}: {mesh} is not a body of the showcase ({', '.join(SHOWCASE_BODIES)})")
        elif (library / mesh).is_file() and hashlib.sha256((library / mesh).read_bytes()).hexdigest() != SHOWCASE_BODIES[mesh]:
            found.append(f"{SHOWCASE_SCENE}: {mesh} is not the showcase's pinned file (its SHA-256)")
    drawn = set()
    for number, body in vendor:
        label = f"{SHOWCASE_SCENE}: body {number + 1}"
        mesh = body["mesh"]
        name = mesh[len(prefix):]
        if not mesh.startswith(prefix) or name not in SHOWCASE_VENDOR_FILES:
            found.append(f"{label}'s mesh {mesh!r} is not a file of the showcase's folder ({prefix})")
            continue
        drawn.add(name)
        if sorted(key for key in body if key != "look") != list(BODY_KEYS):
            found.append(f"{label} has not the keys {', '.join(BODY_KEYS)}")
            continue
        data = files.get(name)
        if data is None:
            continue  # missing: said above
        if (body["sha256"], body["bytes"], body["triangles"]) != (hashlib.sha256(data).hexdigest(), len(data), stl_triangles(data)):
            found.append(f"{label}: {mesh} is not the file its scene names (its SHA-256, bytes or triangles; a binary STL)")
        problem = _rigid(body["matrix"])
        if problem:
            found.append(f"{label}'s matrix {problem}")
        if body["finger"] is not None and body["finger"] not in FINGERS:
            found.append(f"{label}'s finger {body['finger']!r} is not sensor, mate or null")
    for name in sorted(set(SHOWCASE_VENDOR_FILES) - drawn):
        found.append(f"{SHOWCASE_SCENE} does not draw web/{SHOWCASE_VENDOR}/{name}")
    # The showcase's page: its document, its placed record and its pictures (showcase_page()).
    found += showcase_page(parts, library)[0]
    return found, bodies


def showcase_placed(library: Path = LIBRARY):
    """The showcase's placed record: the pad's own (SHOWCASE_PLACED, beside the Library) with the showcase's scene; None
    where that file is missing or not JSON."""

    try:
        record = json.loads((library.parent / SHOWCASE_PLACED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dict(record, scene=SHOWCASE_SCENE) if isinstance(record, dict) else None


def showcase_image(files: dict) -> dict:
    """showcase.json's "image" from its pictures ({kind: bytes}): each one's path, size, bytes and SHA-256, and the
    alt text."""

    image = {kind: {"src": path, "width": size[0], "height": size[1], "bytes": len(files[kind]), "sha256": hashlib.sha256(files[kind]).hexdigest()}
             for kind, (path, size, _) in SHOWCASE_SHOTS.items()}
    image["alt"] = SHOWCASE_ALT
    return image


def showcase_shot(library: Path = LIBRARY, figure: str | None = None, view: str | None = None) -> dict:
    """What the showcase's pictures are of, as the files are now: the scene (its path and scene_sha256() with the rules),
    the art's file and the placed record (their SHA-256), the figure's and the view's sources (figure_sha256(),
    view_sha256(), or the ones given: the shots tool's, as the server served them).  showcase.json's "shot" holds these
    beside the shoot's own look, margins and numbers."""

    placed = showcase_placed(library) or {}
    art = library / str(placed.get("art", ""))
    scene = library / SHOWCASE_SCENE
    try:
        rules = scenes_index(library).get("rules")
    except (OSError, ValueError, AttributeError):
        rules = None  # (scenes() says what is wrong with the index)
    return {"scene": SHOWCASE_SCENE,
            "scene_sha256": scene_sha256(scene.read_bytes(), rules) if scene.is_file() and isinstance(rules, dict) else None,
            "art_sha256": hashlib.sha256(art.read_bytes()).hexdigest() if art.is_file() else None,
            "placed_sha256": hashlib.sha256(canonical_json(placed).encode("ascii")).hexdigest(),
            "figure_sha256": figure or figure_sha256(), "view_sha256": view or view_sha256()}


def showcase_numbers(numbers, rules) -> list:
    """Why the stage's numbers of a shoot of the showcase are not sound ([] when they are): each number of
    SHOWCASE_RULED at least its rule of ``rules`` (scenes.json's; a list's or a map's least value), each of
    SHOWCASE_BOUNDS within the showcase's own bound."""

    if not isinstance(numbers, dict):
        return ["the stage's numbers are missing"]
    checks = rules.get("checks") if isinstance(rules, dict) and isinstance(rules.get("checks"), dict) else {}
    held = [(key, "at least", checks.get(rule)) for key, rule in SHOWCASE_RULED] + list(SHOWCASE_BOUNDS)
    found = []
    for key, sense, bound in held:
        value = numbers.get(key)
        if isinstance(value, dict):
            value = list(value.values())
        least = min(value) if isinstance(value, list) and value and all(_number(item) for item in value) else value
        if not (_number(least) and _number(bound) and (least >= bound if sense == "at least" else least < bound)):
            found.append(f"the stage's {key} is {value!r}, not {sense} {bound!r}")
    return found


def showcase_text(document: dict) -> str:
    """showcase.json's file: JSON as the Library's other documents are written (indent 1, ASCII, a newline at its end)."""

    return json.dumps(document, indent=1, ensure_ascii=True) + "\n"


def showcase_page(parts: dict, library: Path = LIBRARY) -> tuple:
    """(problems, older) of the showcase's page's document (showcase.json; docs/LIBRARY_VIEW.md "The showcase's page"):
    problems, the messages showcase() adds to its own (so library_write --check, the site build and the tests refuse
    them), and older, whether its pictures are of older figure or view sources (still shown: a warning, as a sensor's).

    - the file missing or not JSON, its keys, its format, its id (SHOWCASE_ID: no part's, entry's or family's);
    - its title, label and text not short plain strings, the label without its words (SHOWCASE_LABEL_WORDS), the word CAD;
    - its sensor not {rows, columns, pitch_mm, field_mm} with the art's field;
    - its placed record not the pad's own with the showcase's scene, or about another mesh than the UMI finger's;
    - its tutorial not {label, href} with the address the pad's notice records;
    - its sources not the two notices in order (the gripper's, the pad's), each a file, each text with its words; the
      vendor's folder named anywhere but in that one notice's path;
    - its pictures: "image" not {exploded, assembled, card: {src, width, height, bytes, sha256}, alt}, a file missing,
      not the bytes named or not a WebP with alpha of its size, a file of showcase/ it does not name;
    - "shot" not the record of what the pictures were shot from, or of another scene, rules, art or placed record than
      the files now (stale: shoot again), or its stage's numbers outside the rules' checks and the showcase's own bounds
      (showcase_numbers())."""

    path = library / SHOWCASE_FILE
    name = SHOWCASE_FILE
    try:
        text = path.read_text(encoding="utf-8")
        document = json.loads(text)
    except (OSError, ValueError):
        return [f"{name} is missing or not JSON: write it (docs/LIBRARY_VIEW.md), then {RESHOOT_SHOWCASE}"], False
    if not isinstance(document, dict) or sorted(document) != list(SHOWCASE_KEYS):
        return [f"{name} has not the keys {', '.join(SHOWCASE_KEYS)}"], False
    found = []
    if document["format"] != SHOWCASE_FORMAT:
        found.append(f"{name}: the format is {document['format']!r}, not {SHOWCASE_FORMAT}")
    families = parts.get("families") or {}
    if document["id"] != SHOWCASE_ID or SHOWCASE_ID in parts["parts"] or SHOWCASE_ID in families:
        found.append(f"{name}: its id is not {SHOWCASE_ID}, or a part or a family has that id")
    for key, most in (("title", 40), ("label", 60), ("text", 140), ("about", 2000)):
        value = document[key]
        if not (isinstance(value, str) and value.strip() == value and 0 < len(value) <= most and "\n" not in value):
            found.append(f"{name}: its {key} is not one line of 1 to {most} characters")
    if isinstance(document["label"], str) and not all(words in document["label"].lower() for words in SHOWCASE_LABEL_WORDS):
        found.append(f"{name}: its label does not say {' and '.join(SHOWCASE_LABEL_WORDS)}")
    said = re.search(r"\bCAD\b", text)
    if said:
        found.append(f"{name} says CAD (the page's words are 3D model)")
    for match in PRIVATE_TEXT.finditer(text):
        found.append(f"{name} names {match.group(0)!r}, the private importer's inputs")
    # The placed record and, from its art, the pad's field.
    placed = showcase_placed(library)
    if placed is None:
        found.append(f"web/{SHOWCASE_PLACED} is missing or not JSON")
    elif document["placed"] != placed:
        found.append(f"{name}: its placed record is not web/{SHOWCASE_PLACED} with the scene {SHOWCASE_SCENE}: {RESHOOT_SHOWCASE}")
    elif (placed.get("mesh") or {}).get("sha256") != parts["parts"][UMI_FINGER]["mesh"]["sha256"]:
        found.append(f"{name}: its placed record is about another mesh than {UMI_FINGER}'s (parts.json)")
    sensor = document["sensor"]
    region = None
    try:
        region = read_art((library / placed["art"]).read_bytes())["boards"]["row"]["region"][2:4] if placed else None
    except (OSError, ValueError, KeyError, TypeError, EOFError):
        found.append(f"{name}: its placed record's art is missing or not an art document")
    if not (isinstance(sensor, dict) and sorted(sensor) == ["columns", "field_mm", "pitch_mm", "rows"]
            and all(isinstance(sensor[key], int) and not isinstance(sensor[key], bool) and sensor[key] > 0 for key in ("rows", "columns"))
            and _number(sensor["pitch_mm"]) and sensor["pitch_mm"] > 0
            and isinstance(sensor["field_mm"], list) and len(sensor["field_mm"]) == 2 and all(_number(value) and value > 0 for value in sensor["field_mm"])):
        found.append(f"{name}: its sensor is not {{rows, columns, pitch_mm, field_mm}}")
    elif region is not None and [round6(value) for value in sensor["field_mm"]] != [round6(value) for value in region]:
        found.append(f"{name}: its sensor's field {sensor['field_mm']} mm is not the art's ({region})")
    # The tutorial: the address the pad's own notice records for its Gerbers.
    tutorial = document["tutorial"]
    notice = library.parent / SHOWCASE_PAD_NOTICE
    recorded = notice.read_text(encoding="utf-8") if notice.is_file() else ""
    if not (isinstance(tutorial, dict) and sorted(tutorial) == ["href", "label"] and all(isinstance(tutorial[key], str) and tutorial[key].strip() for key in tutorial)):
        found.append(f"{name}: its tutorial is not {{label, href}}")
    elif not tutorial["href"].startswith("https://") or f"`{tutorial['href']}`" not in recorded:
        found.append(f"{name}: its tutorial's address is not the one web/{SHOWCASE_PAD_NOTICE} records")
    sources = document["sources"]
    if not (isinstance(sources, list) and all(isinstance(item, dict) and sorted(item) == ["notice", "text"]
                                               and all(isinstance(item[key], str) and item[key].strip() for key in item) for item in sources)
            and [item["notice"] for item in sources] == list(SHOWCASE_NOTICES)):
        found.append(f"{name}: its sources are not [{{text, notice}}] of {' and '.join(SHOWCASE_NOTICES)}")
    else:
        for item, words in zip(sources, SHOWCASE_SOURCE_WORDS):
            if not (library / item["notice"]).is_file():
                found.append(f"{name}: its source's notice {item['notice']} is missing")
            if not all(word in item["text"] for word in words):
                found.append(f"{name}: its source of {item['notice']} does not say {' and '.join(words)}")
    if len(SHOWCASE_REFERENCE.findall(text)) != text.count(SHOWCASE_NOTICES[0]):
        found.append(f"{name} names the showcase's folder (web/{SHOWCASE_VENDOR}/) elsewhere than as its notice")
    # The pictures.
    image = document["image"]
    named = {relative for relative, _, _ in SHOWCASE_SHOTS.values()}
    if image is None:
        found.append(f"{name}: no pictures yet: {RESHOOT_SHOWCASE}")
    elif not (isinstance(image, dict) and sorted(image) == sorted([*SHOWCASE_SHOTS, "alt"]) and image["alt"] == SHOWCASE_ALT
              and all(isinstance(image[kind], dict) and sorted(image[kind]) == ["bytes", "height", "sha256", "src", "width"] for kind in SHOWCASE_SHOTS)):
        found.append(f"{name}: its image is not {{{', '.join(SHOWCASE_SHOTS)}: {{src, width, height, bytes, sha256}}, alt}}: {RESHOOT_SHOWCASE}")
    else:
        for kind, (relative, size, _) in SHOWCASE_SHOTS.items():
            record = image[kind]
            target = library / relative
            if (record["src"], record["width"], record["height"]) != (relative, size[0], size[1]):
                found.append(f"{name}: its {kind} picture is not {relative} at {size[0]} x {size[1]}: {RESHOOT_SHOWCASE}")
            elif not target.is_file():
                found.append(f"{relative} is missing: {RESHOOT_SHOWCASE}")
            else:
                data = target.read_bytes()
                if (record["bytes"], record["sha256"]) != (len(data), hashlib.sha256(data).hexdigest()):
                    found.append(f"{relative} is not the file {name} names: {RESHOOT_SHOWCASE}")
                elif webp_info(data) != (size[0], size[1], True):
                    found.append(f"{relative} is not a {size[0]} x {size[1]} WebP with alpha: {RESHOOT_SHOWCASE}")
    folder = library / "showcase"
    for file in sorted(folder.rglob("*")) if folder.is_dir() else []:
        if file.is_file() and file.relative_to(library).as_posix() not in named:
            found.append(f"{file.relative_to(library).as_posix()}: not a picture of {name}")
    # What the pictures were shot from.
    shot = document["shot"]
    older = False
    if image is not None and not (isinstance(shot, dict) and sorted(shot) == list(SHOWCASE_SHOT_KEYS)):
        found.append(f"{name}: its shot is not {{{', '.join(SHOWCASE_SHOT_KEYS)}}}: {RESHOOT_SHOWCASE}")
    elif image is not None:
        now = showcase_shot(library)
        for key, what in (("scene", "scene"), ("scene_sha256", "scene or rules"), ("art_sha256", "art"), ("placed_sha256", "placed record")):
            if shot[key] != now[key]:
                found.append(f"{name}: its pictures are of another {what} than the files now ({key}): {RESHOOT_SHOWCASE}")
        older = (shot["figure_sha256"], shot["view_sha256"]) != (now["figure_sha256"], now["view_sha256"])
        try:
            rules = scenes_index(library).get("rules")
        except (OSError, ValueError, AttributeError):
            rules = None  # (scenes() says what is wrong with the index)
        if isinstance(rules, dict):
            found += [f"{name}: {problem} (the scene or its camera hides the pad, or the bounds are no longer the showcase's: "
                      f"SHOWCASE_BOUNDS)" for problem in showcase_numbers(shot["numbers"], rules)]
    return found, older


def showcase_said(problem: str) -> bool:
    """Whether a message of scenes() is the showcase's own (showcase(): of its page's document or pictures, or ending
    with the showcase tool or the file's removal as its fix), not a gripper's scene's."""

    return problem.startswith((SHOWCASE_FILE, "showcase/")) or problem.endswith((REBUILD_SHOWCASE, REMOVE_FILE))


def scenes(parts: dict, library: Path = LIBRARY) -> tuple:
    """(index, problems) of the grippers' scenes (scenes/scenes.json, scenes/<part>.json, bodies/<part>/): index the
    scenes.json document (scenes_index()), problems [(part or None, message)] (library_write --check, the site build and
    tests/test_library.py refuse them):

    - scenes.json not the frozen index (its keys, format, rules: _index_problems());
    - a gripper part (gripper_parts()) without its scene at scenes/<part>.json, a scene for the UMI finger, a tapered tip
      or a part the Library does not have;
    - a scene not drawable (scene_problems(): its keys, part, the part's mesh, frame, approach, the mate's kind and
      matrix, the bodies' files and matrices, see_through, the overrides, the bodies' notices);
    - a file of scenes/ or bodies/ no scene names;
    - a vendor model of the deny-list named in NOTICE.md (by SHA-256: the bodies' upstream files too), any text of the
      private importer's inputs (PRIVATE_TEXT, a recipe's key) in a scene, in scenes.json or in a body's NOTICE row;
    - the showcase's (showcase(): its scene, the vendor's folder and notice, anything else naming that folder)."""

    index = scenes_index(library)
    problems = []
    if not (library / SCENES_INDEX).is_file():
        problems.append((None, f"{SCENES_INDEX} is missing: {REBUILD}"))
    problems += [(None, f"{message}: {REBUILD}") for message in _index_problems(index)]
    staged = index.get("scenes") if isinstance(index, dict) and isinstance(index.get("scenes"), dict) else {}
    grippers = gripper_parts(parts)
    # The rules' part_looks name parts without a scene (the UMI finger, a tapered tip) or their family: a gripper's look
    # is its scene's.
    rules = index.get("rules") if isinstance(index, dict) and isinstance(index.get("rules"), dict) else {}
    plain = {part_id for part_id in parts["parts"] if part_id not in grippers}
    families = {parts["parts"][part_id].get("family") for part_id in plain} - {None}
    for key in sorted(rules["part_looks"]) if isinstance(rules.get("part_looks"), dict) else ():
        if key not in plain | families:
            problems.append((None, f"{SCENES_INDEX}: its rule part_looks names {key!r}, not a part without a scene or its family "
                                   f"(a gripper's look is its scene's)"))
    notice = (library / "NOTICE.md").read_text(encoding="utf-8") if (library / "NOTICE.md").is_file() else ""
    rows = {row[0]: row for row in NOTICE_ROW.findall(notice)}
    keys = re.compile(r"\b(" + "|".join(re.escape(part_id.replace("-", "_")) for part_id in parts["parts"]) + r")\b")
    texts = [(None, SCENES_INDEX, (library / SCENES_INDEX).read_text(encoding="utf-8") if (library / SCENES_INDEX).is_file() else "")]
    named, used = {SCENES_INDEX}, set()
    for part_id in grippers:
        if part_id not in staged:
            problems.append((part_id, f"{part_id}: no scene in {SCENES_INDEX} (every gripper is drawn whole): {REBUILD}"))
    for part_id, path in sorted(staged.items()):
        if part_id not in grippers:
            kept = part_id in parts["parts"]
            problems.append((part_id if kept else None, f"{part_id}: a scene for {'a part that keeps the fingertip scene' if kept else 'no part of parts.json'}: {REBUILD}"))
            continue
        if path != f"scenes/{part_id}.json":
            problems.append((part_id, f"{part_id}: its scene is {path!r}, not scenes/{part_id}.json: {REBUILD}"))
            continue
        named.add(path)
        target = library / path
        try:
            text = target.read_text(encoding="utf-8")
            document = json.loads(text)
        except (OSError, ValueError):
            problems.append((part_id, f"{path} is missing or not JSON: {REBUILD}"))
            continue
        texts.append((part_id, path, text))
        problems += [(part_id, f"{message}: {REBUILD}") for message in scene_problems(part_id, document, parts, library, rows)]
        problems += [(part_id, f"{message}: {RELOOK}") for message in scene_look_problems(part_id, document)]
        used.update(body.get("mesh") for body in document.get("bodies") or [] if isinstance(body, dict))
    # The showcase (2026-11-12): its own scene, no part's, with its bodies and the vendor's folder beside the Library.
    shown, bodies = showcase(parts, library, rows)
    # (The page's own problems say their own fix: its words are written by hand, its pictures shot.)
    problems += [(None, message if message.startswith((SHOWCASE_FILE, "showcase/")) or message.endswith(REMOVE_FILE) else f"{message}: {REBUILD_SHOWCASE}")
                 for message in shown]
    if (library / SHOWCASE_SCENE).is_file():
        named.add(SHOWCASE_SCENE)
        used.update(bodies)
        texts.append((None, SHOWCASE_SCENE, (library / SHOWCASE_SCENE).read_text(encoding="utf-8", errors="replace")))
    if (library.parent / SHOWCASE_VENDOR / SHOWCASE_NOTICE).is_file():
        texts.append((None, f"../{SHOWCASE_VENDOR}/{SHOWCASE_NOTICE}",
                      (library.parent / SHOWCASE_VENDOR / SHOWCASE_NOTICE).read_text(encoding="utf-8", errors="replace")))
    for folder, kept in (("scenes", named), ("bodies", used)):
        if (library / folder).is_dir():
            for file in sorted((library / folder).rglob("*")):
                relative = file.relative_to(library).as_posix()
                if file.is_file() and relative not in kept:
                    problems.append((None, f"{relative}: a file of no scene: {REBUILD}"))
    texts += [(None, "NOTICE.md", "|".join(row)) for path, row in sorted(rows.items()) if path.startswith("bodies/")]
    for part_id, path, text in texts:
        for match in PRIVATE_TEXT.finditer(text):
            problems.append((part_id, f"{path} names {match.group(0)!r}, the private importer's inputs: {REBUILD}"))
        for match in keys.finditer(text):
            problems.append((part_id, f"{path} names the recipe key {match.group(0)!r}, the private importer's input: {REBUILD}"))
    for digest in sorted(set(re.findall(r"\b[0-9a-f]{64}\b", notice)) & set(DENIED_SHA256)):
        problems.append((None, f"NOTICE.md names {DENIED_SHA256[digest]} ({digest[:12]}), a vendor model of the deny-list: never in the Library"))
    return index, problems


def older_note(identifiers: list) -> str:
    """The warning for pictures of older figure or 3D view sources (pictures()' older)."""

    shown = ", ".join(identifiers[:6]) + (f" and {len(identifiers) - 6} more" if len(identifiers) > 6 else "")
    return (f"the pictures of {shown} are of older figure sources (web/{FIGURE_MODULE} and the modules it imports, or the "
            f"Library view's own: {', '.join(f'web/{path}' for path in VIEW_SOURCES)}): {RESHOOT}")


def view_note(identifiers: list) -> str:
    """The warning for pictures with no 3D view while VIEW_REQUIRED is false (pictures()' views None of a picture)."""

    shown = ", ".join(identifiers[:6]) + (f" and {len(identifiers) - 6} more" if len(identifiers) > 6 else "")
    return (f"the pictures of {shown} have no 3D view (their records name no art, or a gripper's no stage): {RESHOOT}, "
            "then run tools/library_write.py")


# -- the writer -----------------------------------------------------------------------------------------------------

def _fit_job(job: tuple) -> tuple:
    """(id, the reply, the broken rules) of one variant: a worker process's job."""

    identifier, request, mesh_path = job
    reply = fit(request, Path(mesh_path).read_bytes())
    return identifier, reply, rules(reply)


def run(only=None, check: bool = False, jobs: int = 1, library: Path = LIBRARY, index: Path = INDEX, out=print) -> int:
    parts = json.loads((library / "parts.json").read_text(encoding="utf-8"))
    html = index.read_text(encoding="utf-8")
    found = controls(html)
    options = page_options(html)
    table = plan(parts)
    known = {row[0] for row in table}
    chosen = known if only is None else set(only)
    unknown = sorted(chosen - known)
    if unknown:
        out(f"library_write: no variant is named {', '.join(unknown)}")
        return 2
    problems, work, requests, meshes = [], [], {}, {}
    for identifier, part_id, part, variant in table:
        if len(label(part, variant)) > LABEL_MAX:
            problems.append(f"{identifier}: its label {label(part, variant)!r} is longer than {LABEL_MAX} characters")
        for key in ("pitch_mm", "fill"):
            if not valid(found[key], variant[key]):
                problems.append(f"{identifier}: the page does not take {key} {variant[key]}")
        if identifier not in chosen:
            continue
        mesh_path = library / part["mesh"]["file"]
        if part_id not in meshes:
            meshes[part_id] = hashlib.sha256(mesh_path.read_bytes()).hexdigest()
            if meshes[part_id] != part["mesh"]["sha256"]:
                problems.append(f"{part_id}: {part['mesh']['file']} is not the file parts.json names (SHA-256)")
        try:
            requests[identifier] = compose(part, variant, options)
        except LibraryError as error:
            problems.append(f"{identifier}: {error}")
            continue
        work.append((identifier, requests[identifier], str(mesh_path)))
    if problems:
        out("\n".join(problems))
        return 1
    if jobs > 1 and len(work) > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            results = list(pool.map(_fit_job, work))
    else:
        results = [_fit_job(job) for job in work]
    rows = {row[0]: row for row in table}
    rejected, stale, fits, writes = [], [], {}, {}
    for identifier, reply, broken in results:
        _, part_id, part, variant = rows[identifier]
        if broken:
            rejected.append(f"{identifier}: rejected, {'; '.join(broken)}")
            continue
        path = fit_path(identifier, variant)
        target = library / path
        if path.startswith("fits/"):
            data = fit_document(requests[identifier], meshes[part_id], reply)
            if not target.exists() or target.read_bytes() != data:
                writes[path] = data
                stale.append(identifier)
        else:
            # A fit this writer does not own (the page's default part's, web/vendor/umi/default-fit.json): checked only.
            data = target.read_bytes()
            shipped = json.loads(data.decode("utf-8"))
            if canonical(shipped["request"]) != canonical(requests[identifier]) or shipped["reply"] != reply \
                    or shipped["mesh_sha256"] != meshes[part_id]:
                rejected.append(f"{identifier}: {path} is stale: re-run tools/browser/write_default_fit.py")
                continue
        fits[identifier] = data
    if rejected:
        out("\n".join(rejected))
        out("library_write: nothing written")
        return 1
    for identifier, _, _, variant in table:
        if identifier not in fits:
            target = library / fit_path(identifier, variant)
            if not target.exists():
                out(f"library_write: {identifier} has no fit yet: run without --only")
                return 1
            fits[identifier] = target.read_bytes()
    document = entries(parts, fits, library)
    text = entries_text(document)
    entries_path = library / "entries.json"
    entries_stale = not entries_path.exists() or entries_path.read_text(encoding="utf-8") != text
    listed = {fit_path(identifier, variant) for identifier, _, _, variant in table}
    orphans = sorted(path.relative_to(library).as_posix() for path in (library / "fits").glob("*.json")
                     if path.relative_to(library).as_posix() not in listed) if (library / "fits").is_dir() and only is None else []
    # The pictures (shots/manifest.json): a shot of another fit has no image (entries()) and fails --check; one of older
    # figure sources is pictured, with a warning.  A re-fit leaves its sensor's shot of the old fit: write first, then
    # re-shoot (the page shoots the fit written here) and write again.
    images, unpictured, older, views = pictures(document["variants"], library)
    for _, problem in unpictured:
        out(f"{'stale' if check else 'library_write'}: picture {problem}")
    # The grippers' scenes (scenes(): the 3D view's whole grippers, drawn from scenes/ and bodies/, written by the
    # private scene builder): a problem fails --check as a stale picture does; writing only reports it.
    _, unscened = scenes(parts, library)
    for _, problem in unscened:
        out(f"{'stale' if check else 'library_write'}: scene {problem}")
    # Every sensor of the Library has its picture (since the set of 2026-11-05, shot with the approved look: the cards
    # show the finger with the sensor on it, the user's request that day): a sensor with no shot at all, a new one or
    # one whose shot went, fails --check as one of another fit does (here, not in pictures(): the site build and the
    # tests' fixtures take a library of fewer pictures); writing only says so (write, shoot it, write again).
    broken = {identifier for identifier, _ in unpictured}
    unshot = [identifier for identifier, image in images.items() if image is None and identifier not in broken]
    for identifier in unshot:
        out(f"{'stale' if check else 'library_write'}: picture {identifier}: no picture: {RESHOOT} --only {identifier}")
    if older:
        out(f"library_write: warning: {older_note(older)}")
    if (library / SHOWCASE_FILE).is_file() and showcase_page(parts, library)[1]:
        out(f"library_write: warning: the showcase's pictures are of older figure or view sources: {RESHOOT_SHOWCASE}")
    # A picture with no 3D view (no art in its record, or a gripper's no stage) while VIEW_REQUIRED is false: its
    # sensor's page shows the picture only (entries.json's view null), a warning.
    unviewed = [identifier for identifier, image in images.items() if image is not None and views[identifier] is None]
    if unviewed:
        out(f"library_write: warning: {view_note(unviewed)}")
    viewed = len([identifier for identifier, view in views.items() if view is not None])
    if check:
        for identifier in stale:
            out(f"stale: {identifier}")
        if entries_stale:
            out("stale: entries.json")
        for path in orphans:
            out(f"stale: {path} (no variant)")
        if unpictured or unshot:
            out(f"library_write: the library's pictures are stale: {RESHOOT}, then run tools/library_write.py")
        # (The showcase's lines say their own fixes: the scene builder is not one of them.)
        shown = [problem for _, problem in unscened if showcase_said(problem)]
        if len(unscened) > len(shown):
            out(f"library_write: the library's scenes are stale: {REBUILD}")
        if [problem for problem in shown if not problem.endswith(REMOVE_FILE)]:
            out(f"library_write: {SHOWCASE_STALE}")
        if stale or entries_stale or orphans:
            out("library_write: the library is stale: run tools/library_write.py")
        if stale or entries_stale or orphans or unpictured or unshot or unscened:
            return 1
        out(f"library_write: {len(table)} sensors, all current, each with its picture, {viewed} with a 3D view")
        return 0
    (library / "fits").mkdir(exist_ok=True)
    for path, data in writes.items():
        (library / path).write_bytes(data)
        out(f"wrote web/library/{path} ({len(data)} bytes)")
    for path in orphans:
        (library / path).unlink()
        out(f"removed web/library/{path} (no variant)")
    if entries_stale:
        entries_path.write_text(text, encoding="utf-8")
        out(f"wrote web/library/entries.json ({len(table)} sensors)")
    out(f"library_write: {len(results)} fitted, {len(writes)} written, {len(table)} sensors, {viewed} with a 3D view")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", default=None, metavar="ID,...", help="fit only these variants (the others' fits are read)")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 listing the stale ids")
    parser.add_argument("--jobs", type=int, default=max(1, min(8, os.cpu_count() or 1)), help="fits in parallel processes")
    args = parser.parse_args(argv)
    only = None if args.only is None else [item for item in re.split(r"[,\s]+", args.only) if item]
    try:
        return run(only=only, check=args.check, jobs=args.jobs)
    except (LibraryError, OSError, KeyError, ValueError) as error:
        print(f"library_write: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
