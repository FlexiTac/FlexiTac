#!/usr/bin/env python3
"""Build the Library's showcase: the xArm Gripper G1's meshes, the UMI finger holder and the showcase's scene.

The showcase (the project owner's decision of 2026-11-12; tools/library_write.py SHOWCASE_ID) is the hand-designed
FlexiTac sensor on UFACTORY's xArm Gripper G1 with UMI soft fingers, as the FlexiTac Tactile Demo shows the gripper.
This tool makes its geometry, to the same bytes on every run (standard library only; tools/mesh_decimate.py):

- web/vendor/ufactory-g1/<name>.stl, twelve meshes: UFACTORY's 3D model "Gripper G1 3D File (With).stl" (one closed
  file, millimetres, the fingers closed) split as the Tactile Demo splits it and each piece decimated to within
  0.1 mm.  The split: the file's connected components (triangles sharing an edge; corners the same floats) go by their
  boxes' centres to the four links and the two fingers (GROUPS, within 0.6 mm), the rest to the body; the body's
  components (corners merged at 0.0001 mm) are the shell (the largest), the flange (below y -35), the pivot pins
  (under 7 mm in x and y) and the frame (the rest); a sliver under the shell's face (thinner than 1 mm, never seen) is
  left out; each finger loses its fingertip (the components wholly above y 94 that reach within 12.9 mm of the
  middle plane: the pad and its screws) and is cut at y 96, where the UMI holder sits (the cut left open), and what
  remains is the coupler (its largest component) and its pins.  The decimation: mesh_decimate.decimate, half-edge
  collapses under quadric costs, gated by the two-way deviation it measures.  Binary STL in millimetres, in the file's
  own axes; the 80-byte header says what was changed.
- web/library/bodies/flexitac-g1/umi-right-finger-holder.stl: HandUMI's UMI-RIGHT-Finger-Holder.stl (Apache-2.0),
  decimated the same way; the left holder is drawn as its mirror image.
- web/library/bodies/flexitac-g1/drawn-<name>.stl: what the owner's photo of the gripper shows and the models have
  only as holes, or not at all, drawn by the project as plain boxes and cylinders (DRAWN; tools/library_split.py's
  shapes and header: no vendor's geometry): a shell screw's head, a holder bolt's head and its nut, the black block
  in the shell's top slot, and behind each finger the extender board on the pad's tails, its two sockets (each round a
  tail's end) and a stub of the flat cable.  They need no source and are drawn again on every run.
- web/library/scenes/flexitac-g1.json: the scene, in the scenes' format with the looks of 2026-11-12
  (docs/LIBRARY_VIEW.md), about the Library's UMI finger (web/vendor/umi/) as the gripper's left finger: every matrix
  in that finger's file axes in millimetres.  The pose is the Tactile Demo's: the links turned until the two sensors'
  centres are 55 mm apart (24.35 degrees), the fingers only translating (a parallel four-bar); the soft finger bolted
  to the holder by its three holes (a rigid fit in the plane, which leans it 0.93 degrees), the holder on the cut
  coupler; the other finger the mirror image across the gripper's middle plane.  The looks are the Library's base
  looks, each body's chosen after photos of the real gripper, and seven of the showcase's own (OWN_LOOKS: the shell's
  gloss, the printed parts' white, the pins' steel, the screws' black, the fingers' orange, the drawn boards and
  cables); the camera is the
  showcase's own (CAMERA), and no finger is see-through.

The sources are read from a folder given on the command line and never copied: the vendor's file must be the one
whose SHA-256 is pinned (library_write.SHOWCASE_SOURCE), and so must the holder's (HOLDER_SHA256, the file of
handumi-hw at its pinned commit).  Every output's SHA-256 is pinned in tools/library_write.py (SHOWCASE_VENDOR_FILES,
SHOWCASE_BODIES), so --check proves the committed files without the sources; a build that gives other bytes says so
and writes nothing unless --repin is given (then update the pins and the notices' rows by hand: --notice prints them).

    python3 tools/library_showcase.py                              # the drawn shapes and the scene, from the committed meshes
    python3 tools/library_showcase.py --check                      # the committed meshes, shapes, scene, notices and page
    python3 tools/library_showcase.py --sources DIR --check        # and a rebuild from the sources, byte for byte
    python3 tools/library_showcase.py --sources DIR                # rebuild; writes what changed (the pins must hold)
    python3 tools/library_showcase.py --sources DIR --repin --notice
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import library_split  # noqa: E402
import library_write  # noqa: E402
import mesh_decimate  # noqa: E402

WEB = ROOT / "web"
LIBRARY = WEB / "library"
TOLERANCE_MM = library_write.SHOWCASE_TOLERANCE_MM
SOURCE_NAME, SOURCE_SHA256, SOURCE_BYTES = library_write.SHOWCASE_SOURCE
# HandUMI's holder: hardware/STL/gripper_tips/UMI-Gripper/UMI-RIGHT-Finger-Holder.stl of handumi-hw at HANDUMI_COMMIT
# (fetched and hashed on 2026-11-12; the Tactile Demo's copy is the same bytes).
HOLDER_NAME = "UMI-RIGHT-Finger-Holder.stl"
HOLDER_SHA256 = "80ebab13e5d84a4e83d80e4ff21fa660223fd98f0f83dc45055d7015b4e71c00"
HOLDER_PATH = "hardware/STL/gripper_tips/UMI-Gripper/UMI-RIGHT-Finger-Holder.stl"
HANDUMI_COMMIT = "144827862d4e2d5cd2d331ce7eed1374d3c769df"
HOLDER_BODY = "bodies/flexitac-g1/umi-right-finger-holder.stl"

# -- the split (the Tactile Demo's; the file's axes: x across the jaws, y along the fingers, z through the body) --------

# A component whose box's centre (x, y) is within GROUP_REACH of one of a group's centres is that group's.
GROUP_REACH = 0.6
FINGER_CENTRES = ((23.0, 97.5), (10.5, 115.0), (7.5, 115.25), (32.0, 74.0), (17.0, 89.0), (19.95, 91.95), (13.8, 105.0), (13.8, 117.0))
GROUPS = (
    ("link_r_outer", ((36.9, 39.1),)),
    ("link_r_inner", ((18.5, 61.55),)),
    ("link_l_outer", ((-36.9, 39.1),)),
    ("link_l_inner", ((-18.5, 61.55),)),
    ("finger_r", FINGER_CENTRES),
    ("finger_l", tuple((-x, y) for x, y in FINGER_CENTRES)),
)
FLANGE_TOP_Y = -35.0        # the flange lies wholly below it
SLIVER_MM = 1.0             # the sliver under the shell's face is thinner
PIN_MM = 7.0                # a pivot pin's extent in x and in y is less
FINGERTIP_Y = 94.0          # a fingertip's component lies wholly above it
FINGERTIP_X = 12.9          # and reaches nearer the middle plane than this
CUT_Y = 96.0                # the finger is cut here: the UMI holder's bottom
# Each mesh: its file's stem, what it is (the notice's words) and whether the cut made it.
MESHES = (
    ("body_shell", "the housing shell", False),
    ("body_frame", "the inner frame", False),
    ("body_flange", "the mounting flange", False),
    ("body_pins", "the body's four pivot pins", False),
    ("link_r_outer", "the right outer link", False),
    ("link_r_inner", "the right inner link", False),
    ("link_l_outer", "the left outer link", False),
    ("link_l_inner", "the left inner link", False),
    ("finger_r_coupler", "the right finger's coupler, the stock finger cut where the UMI holder sits", True),
    ("finger_r_pins", "the right coupler's pins", False),
    ("finger_l_coupler", "the left finger's coupler, the stock finger cut where the UMI holder sits", True),
    ("finger_l_pins", "the left coupler's pins", False),
)
HEADER = "modified (split, decimated <= 0.1 mm) by FlexiTac-Gen 2026, see NOTICE.md"
HEADER_CUT = "modified (split, cut, decimated <= 0.1 mm) by FlexiTac-Gen 2026, see NOTICE.md"
HEADER_HOLDER = "modified (decimated <= 0.1 mm) by FlexiTac-Gen 2026, see NOTICE.md"

# -- the pose (the Tactile Demo's four-bar and mounting, mm, the vendor file's axes) --------------------------------------

PIVOT_OUTER = (35.0, 19.1)          # the right links' pivots on the body (the left ones': x negated)
PIVOT_INNER = (20.0, 34.1)
LINK = (-3.0, 54.9)                 # a right link's pivot to its tip, closed
LIMIT_DEG = 45.0                    # the links' travel
SENSOR_GAP_MM = 55.0                # the two sensors' centres apart: the opening shown
# The holder on the right coupler, a shift of its file: its contact side (x 40) on the stock pad's face (x 6), its
# base (y 71.2) on the cut (y 96), the middle of its two flanges (z -2.4) on the gripper's middle plane.
HOLDER_SHIFT = (6.0 - 40.0, CUT_Y - 71.2, 2.4)
HOLDER_MID_Z = -2.4
# The soft finger's three bolt holes (its file's x and -z) and the holder's flange holes they sit on (its x, y).
FINGER_HOLES = ((5.0, 5.0), (35.0, 5.0), (35.0, 40.0))
HOLDER_HOLES = ((45.0, 82.5), (74.99, 82.99), (74.43, 117.98))
FINGER_THICK_MM = 25.8
# The sensor's centre on the finger's contact face (the plane x = 0 of its file): the middle of its thickness, 30 mm
# (half of 30 taxels at 2 mm) and 0.5 mm from the face's tip end (z -122.36).
SENSOR_CENTRE = (0.0, -12.9, -91.86)

# -- the looks -----------------------------------------------------------------------------------------------------------

# Which material each body is comes from photos of the real gripper (the owner's own unit and UFACTORY's pictures): a
# white gloss shell under a clear coat, black anodized links and flange, a white frame, polished steel pins, white printed
# couplers and holders, orange TPU fingers - the Tactile Demo's five materials.  The numbers are the Library's base
# looks' (docs/LIBRARY_VIEW.md "The looks"; tools/library_looks/base.json): in a scene a base name always means the
# base's numbers, so BASE_LOOKS are that table's, unchanged (tests/test_library_showcase.py compares them with the
# table), and a look of the showcase's own (OWN_LOOKS, as the grippers' look files have them) is a base look under
# another name with the numbers that differ and the evidence for them.
BASE_LOOKS = {
    "pcb-green": {"color": "#1f6b3a", "metalness": 0, "roughness": 0.5},
    "plastic-white-gloss": {"color": "#e2e4e6", "metalness": 0, "roughness": 0.3, "clearcoat": 0.6, "clearcoat_roughness": 0.15},
    "plastic-white-satin": {"color": "#e6e8ea", "metalness": 0, "roughness": 0.45},
    "anodized-black": {"color": "#232428", "metalness": 0.6, "roughness": 0.45, "env_intensity": 2.4},
    "steel-polished": {"color": "#c8cacc", "metalness": 1, "roughness": 0.18},
    "tpu-orange": {"color": "#f2601c", "metalness": 0, "roughness": 0.6},
}
# A look of the showcase's own is a base look under another name with the numbers that differ and its evidence.  Four
# are of the gripper's own bodies.  The base looks were tuned at the showcase's home only; the reviews of 2026-11-12
# turned the view half-way round, to the side of the logo's face that the owner's photo of the gripper was taken from,
# and found the shell and the holders all but lost in the card's #f5f5f7 ground there (#e9ebee and #e4e6e9), the pins'
# flat ends white discs (#f6f8fa) and the screws a mid grey (#6c6d72).  So each of these four is judged at the home
# and turned 60, 120, 180, 240 and 300 degrees (sRGB medians of each body's own pixels, found by drawing the bodies
# once in flat colours; the Assembled stage at the showcase's camera):
# - shell-white-gloss: in the studio, which turns with the camera, an upright face mirrors the front bounce low behind
#   the camera, so from the logo's side the whole face was a reflection of it, near the ground, whatever its colour
#   (#d2d4d6 left it at #e2e4e6).  A smoother skin under a full, sharper coat (roughness 0.1, clear coat 1 at 0.02)
#   with seven tenths of the studio draws the face #c3c5c8 at the home and #dbdddf half-way round (the base white:
#   #cfd2d5 and #e9ebee), so it stands off the card from every side, and its rounded top and side edges carry a
#   bright line, as the photo's shell, #c4bfbb on its face, carries the windows' streak (#eae6e3) on its top edge.
# - print-white: the frame's channel, the couplers and the holders, white printed parts.  The base satin white drew a
#   holder's face #d5d8db at the home and #e4e6e9 from the logo's side; at #d8dadc it is #c8cace and #d9dbde, as the
#   photo's holders (#c8c9ca) stand beside its shell.
# - steel-pin: the pivot pins' flat ends mirror one softbox whole.  A brushed face (roughness 0.7) darker than the
#   base polished steel (#a0a2a4) with half of the studio is #7a7c7e from the logo's side under a lighter chamfer, as the
#   photo's pin ends, and the Phillips heads on the home's side are a mid steel grey (#585a5c), lighter than the links.
# - screw-black: the drawn screws, bolts and nuts.  The base anodized black is a metal lifted by the studio
#   (env_intensity 2.4), so a screw's small flat head, mirroring one direction of it, was #212228 at the home and
#   #6c6d72 from the logo's side, a mid grey.  Black oxide is matte: no metal, roughness 0.9, the studio at 1.9 gives
#   #25262b at the home and #2e2f33 half-way round, near-black from both sides and no darker than the film (the
#   Library's convention for blacks; with the studio at 1 a head was #0b0d13 at the home).
# - umi-tpu-orange: the soft fingers, in the UMI rows' own orange (scenes.json's rules give the Library's UMI finger
#   and its tips this look under this name, with these numbers; tests/test_library_showcase.py holds the two equal).
#   The owner's photo of the gripper reads #d85623, #c94917 and #8f1601 on its fingers (sRGB medians of the brightest
#   quarter, the middle half and the darkest quarter of their orange pixels).  The base orange (#f2601c with all of
#   the studio) drew the fingers #f17c5b, #e15c28 and #d2571b in the Assembled picture (the near finger's lit back
#   #f08265, a salmon); the UMI rows' orange draws them #cd5d3c, #ba460b and #a53e0a (that back #cc6346), and the
#   showcase's fingers are the same orange as the UMI rows below them (the merge of 2026-11-13).  The verification of
#   2026-11-13 found that back still a washed salmon beside the photo's lit orange (#cb654a, hue 13 degrees, saturation
#   0.64; the photo #d44a1b, hue 15, 0.87), the direct lights' white sheen on the faces turned up to them, and the same
#   in the UMI rows' fin windows a third of a turn round; at roughness 0.85 (a printed TPU's broad matte sheen) that
#   back is #c44b17 (hue 18, 0.88), the salmon pixels of the Assembled home a ninth of what they were (10316 to 1194)
#   and of the UMI finger's Exploded view turned 120 degrees a twentieth (15635 to 813), the homes' other pixels as
#   they were.
# The other two are of what the project draws behind the fingers.
OWN_LOOKS = {
    "shell-white-gloss": {"base": "plastic-white-gloss", "roughness": 0.1, "clearcoat": 1, "clearcoat_roughness": 0.02, "env_intensity": 0.7,
                          "evidence": "the owner's photo of the gripper: the shell's face is #c4bfbb as photographed and its top "
                                      "edge carries the windows' sharp streak, #eae6e3, a high gloss under a clear coat"},
    "print-white": {"base": "plastic-white-satin", "color": "#d8dadc",
                    "evidence": "the owner's photo of the gripper: the printed holders' faces are #c8c9ca as photographed, as light "
                                "as the shell's face beside them"},
    "steel-pin": {"base": "steel-polished", "color": "#a0a2a4", "roughness": 0.7, "env_intensity": 0.5,
                  "evidence": "the owner's photo of the gripper: the pivot pins' flat ends are brushed mid-grey discs under a "
                              "bright rim, #524b47 as photographed (luminance 46 to 149)"},
    "screw-black": {"base": "anodized-black", "metalness": 0, "roughness": 0.9, "env_intensity": 1.9,
                    "evidence": "the owner's photo of the gripper: the shell's screws and the holders' bolts and nuts are "
                                "matte black, #080708 and near it as photographed from the logo's side"},
    "pcb-yellow": {"base": "pcb-green", "color": "#a08616",
                   "evidence": "the owner's photo of the gripper: the extender boards' yellow solder mask reads #806d0f as photographed "
                               "(#967f12 at the white print's exposure)"},
    "ffc-white": {"base": "plastic-white-satin", "color": "#dedcd8", "roughness": 0.5,
                  "evidence": "the owner's photo of the gripper and the project page's photo of the sensor: the flat cables are a warm "
                              "white, #cac5bf where the light falls on them"},
    "umi-tpu-orange": {"base": "tpu-orange", "color": "#e85a1c", "roughness": 0.85, "env_intensity": 0.3,
                       "evidence": "the photos of the UMI soft finger (and the owner's photo of the gripper, its fingers #d85623 where "
                                   "lit, #d44a1b at saturation 0.87 on their upturned faces): orange TPU, #ec660e lit and #c14809 in "
                                   "the mid-tones, a matte print with no white sheen; the UMI rows' look of scenes.json's rules"},
}
# The scene's looks in the order it lists them.
LOOK_ORDER = ("shell-white-gloss", "print-white", "anodized-black", "steel-pin", "screw-black", "umi-tpu-orange", "pcb-yellow", "ffc-white")


def resolved_looks() -> dict:
    """{name: look} of the scene: the base looks its bodies and its part name, and its own (each its base look with
    the numbers that differ), in the order the scene lists them."""

    looks = {}
    for name in LOOK_ORDER:
        if name in OWN_LOOKS:
            given = OWN_LOOKS[name]
            looks[name] = dict(BASE_LOOKS[given["base"]], **{key: value for key, value in given.items() if key not in ("base", "evidence")})
        else:
            looks[name] = dict(BASE_LOOKS[name])
    return looks


LOOKS = resolved_looks()
PART_LOOK = "umi-tpu-orange"
SMOOTH_DEG = 35
MESH_LOOKS = {"body_shell": "shell-white-gloss", "body_frame": "print-white", "body_flange": "anodized-black",
              "body_pins": "steel-pin", "link_r_outer": "anodized-black", "link_r_inner": "anodized-black",
              "link_l_outer": "anodized-black", "link_l_inner": "anodized-black", "finger_r_coupler": "print-white",
              "finger_r_pins": "steel-pin", "finger_l_coupler": "print-white", "finger_l_pins": "steel-pin"}
HOLDER_LOOK = "print-white"
PICTURE = "on both soft fingers of the open gripper"
# The showcase's own camera (a scene's override of the rules', within their bounds; its reason in the scene's about): a
# three-quarter view from the side of the shell's face without the logo, in which the far finger's pad is seen on its
# face, the straps crossing both fingers' side faces, the near finger's back with the gold ends, and the gripper's body.
# Exploded, from the same side, higher and further off the pad's normal (70 degrees, 40 up): at the Assembled camera the
# lifted layers stood almost edge-on, a column 90 px wide, so that only 8 % of the drawing's pixels told Exploded from
# Assembled (the verification of 2026-11-13; 46 to 70 % on the grippers' pictures); from here the boards' and the film's
# faces are seen apart, the lift across the view.
CAMERA = {"exploded": {"tilt_deg": 70, "elevation_deg": 40, "front": -1},
          "assembled": {"tilt_deg": 60, "elevation_deg": 20, "front": -1}}
# Both fingers are drawn solid: the near finger hides nothing of the far one's pad from this camera (the jaws are 55 mm
# apart), and the showcase is the gripper as built.
SEE_THROUGH = []


# -- what the project draws ----------------------------------------------------------------------------------------------

# The owner's photo of the gripper shows parts the vendor's model and HandUMI's holder have only as holes: the shell's
# twelve black screws in their wells, the holders' black bolts and nuts, and the small black block in the shell's top
# slot.  They are drawn here as plain shapes (tools/library_split.py's box and cylinder, written with its header of a
# shape the project drew: no vendor's geometry, no row of NOTICE.md), each one file of bodies/flexitac-g1/ drawn as many
# times as the scene places it; their SHA-256 are pinned with the holder's (library_write.SHOWCASE_BODIES).
# name: (what it stands for, its look, its shapes in its own axes, mm).
DRAWN = {
    "shell-screw": ("a shell screw's head in its well", "screw-black",
                    [{"cylinder": {"from": [0, 0, 0], "to": [0, 0, 1.8], "radius": 2.6, "segments": 16}}]),
    "holder-bolt": ("a holder bolt's socket head in its counterbore", "screw-black",
                    [{"cylinder": {"from": [0, 0, 0], "to": [0, 0, 2.8], "radius": 2.75, "segments": 16}}]),
    "holder-nut": ("a holder bolt's hex nut in its pocket", "screw-black",
                   [{"cylinder": {"from": [0, 0, 0], "to": [0, 0, 2.2], "radius": 3.2, "segments": 6}}]),
    "slot-block": ("the black block and its round cap in the shell's top slot", "anodized-black",
                   [{"box": [[-14.5, 52.0, -6.5], [14.5, 57.6, 6.5]]},
                    {"cylinder": {"from": [0, 57.6, 0], "to": [0, 58.5, 0], "radius": 5.2, "segments": 24}}]),
    # Behind each finger, by eye from the photos, in axes of their own (board_place(), cable_place()): the yellow
    # extender board over the pad's two tails; its two white sockets, each round a tail's end (the upper one at the
    # board's edge round the wide tail's stiffened end, the lower one through the board round the Top FPC's tab); and a
    # short stub of the white flat cable from the lower socket down the finger's back.
    "extender": ("the yellow extender board behind a finger", "pcb-yellow", [{"box": [[0.35, -28.9, 3.6], [1.95, -5.4, 17.4]]}]),
    "extender-sockets": ("the extender board's two white sockets", "ffc-white",
                         [{"box": [[-0.7, -25.3, -0.4], [2.6, -5.8, 5.3]]}, {"box": [[-0.7, -24.9, 11.4], [2.6, -6.3, 16.6]]}]),
    "cable-stub": ("a short stub of the white flat cable", "ffc-white", [{"box": [[0.0, -23.85, 0.0], [0.35, -7.35, 35.7]]}]),
}
# The shapes drawn behind each finger and the axes each is drawn in: on the sensor finger through that place, on the
# mate through the mate's matrix too.
FINGER_DRAWN = ("extender", "extender-sockets", "cable-stub")
FINGER_PLACES = {"extender": "board", "extender-sockets": "board", "cable-stub": "cable"}
# Where the pad's two tails end behind the sensor finger, in the part's axes (x 40 is the finger's flat back above its
# base, y its thickness from -25.8 to 0, -z toward the fingertip), as the Library's view lays the placed pad
# (web/cad/drape.js placedStack on web/vendor/flexitac-v2/umi-finray.placed.json; measured there on 2026-11-12, and held
# in the browser by tools/browser/showcase_checks.py part_tails).  Past the fold both tails lie in one plane, which
# leaves the fin's sloping back and bridges to the base: x = TAILS_PLANE[0] + TAILS_PLANE[1] z (within 0.3 mm), 21.7
# degrees to the finger's length.  The wide tail (the A's foot, its stiffened gold end the last 4.4 mm) ends at
# TAIL_END's z over its y; the Top FPC's strap crosses the back from there toward the base and its tab ends at TAB_END.
TAILS_PLANE = (58.603, 0.398)
TAIL_END = ((-24.54, -8.26), -52.77)
TAB_END = ((-18.86, -12.73), -42.76)
# The board's axes: x off the tails' plane (outward), y the finger's thickness, z along the plane toward the base from
# the plane's point at the part's z BOARD_FROM_Z, where the wide tail's stiffened end begins.  So in DRAWN the upper
# socket (x -0.7 to 2.6, z -0.4 to 5.3) holds the wide tail's end (z 0.3 to 5.1 on the plane); the board (x 0.35 to
# 1.95, z 3.6 to 17.4) lies over the Top FPC's strap, which leaves the side face's roll at z 4 and crosses the back to
# its tab; and the lower socket (x -0.7 to 2.6, z 11.4 to 16.6), through the board, holds the tab's end (z 11.4 to 15.9
# on the plane, 6.2 mm wide).
BOARD_FROM_Z = -57.5
# The cable's axes: x its thickness, y the finger's thickness, z its length, from CABLE_FROM in the board's axes (inside
# the lower socket) straight to CABLE_TO in the part's (on the finger's flat back, above its base, between the holder's
# flanges): a stub that begins in a socket, leaves the board's lower edge and ends on the finger.
CABLE_FROM = (2.4, 0.0, 16.0)
CABLE_TO = (40.3, 0.0, -8.0)
# The shell's screw wells, the vendor file's axes: (x, y) of the right half's three on each face (the left half's: x
# negated) and the z of a head's flat end there (the well's floor on the face without the logo, z 21.0; on the logo's
# face the head's outer end, 1.8 mm above the floor at z -22.5).
SHELL_SCREWS = (((41.25, 38.5), (41.25, 12.0), (33.5, -15.0), 21.0), ((41.25, 38.5), (41.25, 3.75), (33.5, -15.0), -24.3))
# The holder's three bolts (HOLDER_HOLES, its file's x and y): a head's inner end in the counterbore of the flange at
# +z (z 13.6), a nut's outer end in the hex pocket of the flange at -z (z -21.2).
HOLDER_BOLT_Z = 13.6
HOLDER_NUT_Z = -21.2


class ShowcaseError(Exception):
    pass


# -- the split ---------------------------------------------------------------------------------------------------------

def float32(value: float) -> float:
    """``value`` as the float32 nearest it (what a binary STL holds)."""

    return struct.unpack("<f", struct.pack("<f", value))[0]


def numbered(triangles: list, scale) -> list:
    """Each triangle's corners as vertex numbers, [a, b, c]: corners are one vertex where their coordinates times
    ``scale`` round to the same integers (None: where they are the same floats)."""

    index, faces = {}, []
    for t in triangles:
        face = []
        for k in (0, 3, 6):
            point = (t[k], t[k + 1], t[k + 2])
            key = point if scale is None else (round(point[0] * scale), round(point[1] * scale), round(point[2] * scale))
            face.append(index.setdefault(key, len(index)))
        faces.append(face)
    return faces


def pieces(triangles: list, scale, pairs: bool = False) -> list:
    """The triangles' connected components (sharing an edge; with ``pairs``, an edge of exactly two triangles), each
    the list of its triangles' numbers, rising, in the order of their first triangles."""

    return mesh_decimate.components(numbered(triangles, scale), pairs)


def taken(triangles: list, groups: list) -> list:
    """The triangles of ``groups`` (lists of numbers) together, in the file's order."""

    return [triangles[number] for number in sorted(number for group in groups for number in group)]


def box(triangles: list) -> tuple:
    """(low, high): the triangles' box."""

    low = [min(min(t[k], t[k + 3], t[k + 6]) for t in triangles) for k in range(3)]
    high = [max(max(t[k], t[k + 3], t[k + 6]) for t in triangles) for k in range(3)]
    return low, high


def grouped(triangles: list) -> dict:
    """The closed file's triangles by GROUPS (each group's in the file's order), the rest under "body"."""

    groups = {name: [] for name, _ in GROUPS}
    groups["body"] = []
    for piece in pieces(triangles, None, pairs=True):
        low, high = box(taken(triangles, [piece]))
        x, y = (low[0] + high[0]) / 2, (low[1] + high[1]) / 2
        chosen = "body"
        for name, centres in GROUPS:
            if any(abs(x - cx) < GROUP_REACH and abs(y - cy) < GROUP_REACH for cx, cy in centres):
                chosen = name
                break
        groups[chosen].append(piece)
    return {name: taken(triangles, held) for name, held in groups.items()}


def body_parts(triangles: list) -> dict:
    """The body's components by what they are: shell, frame, flange, pins; the sliver under the shell's face dropped."""

    found = pieces(triangles, mesh_decimate.WELD_SCALE)
    largest = max(range(len(found)), key=lambda number: (len(found[number]), -number))
    parts = {"shell": [], "frame": [], "flange": [], "pins": [], "sliver": []}
    for number, piece in enumerate(found):
        low, high = box(taken(triangles, [piece]))
        extent = [high[k] - low[k] for k in range(3)]
        if number == largest:
            name = "shell"
        elif high[1] < FLANGE_TOP_Y:
            name = "flange"
        elif min(extent) < SLIVER_MM:
            name = "sliver"
        elif extent[0] < PIN_MM and extent[1] < PIN_MM:
            name = "pins"
        else:
            name = "frame"
        parts[name].append(piece)
    missing = [name for name, held in parts.items() if not held]
    if missing:
        raise ShowcaseError(f"the body's {', '.join(missing)} not found: another file?")
    del parts["sliver"]
    return {name: taken(triangles, held) for name, held in parts.items()}


def cut_below(triangles: list, limit: float) -> list:
    """The part of the triangles at y <= ``limit``: those wholly below, then those across it cut (each a polygon
    clipped against the plane and fanned from its first corner, the winding kept; a new corner a float32); the cut is
    left open."""

    whole, cut = [], []
    for t in triangles:
        corners = (t[0:3], t[3:6], t[6:9])
        inside = [corner[1] <= limit for corner in corners]
        if all(inside):
            whole.append(t)
        elif any(inside):
            polygon = []
            for k in range(3):
                a, b = corners[k], corners[(k + 1) % 3]
                if inside[k]:
                    polygon.append(a)
                if inside[k] != inside[(k + 1) % 3]:
                    polygon.append(tuple(float32(a[axis] + (b[axis] - a[axis]) * (limit - a[1]) / (b[1] - a[1])) for axis in range(3)))
            cut += [polygon[0] + polygon[k] + polygon[k + 1] for k in range(1, len(polygon) - 1)]
    return whole + cut


def finger_parts(triangles: list, side: str) -> tuple:
    """(coupler, pins) of a finger: its fingertip's components dropped (the pad, glued to its rubber, and the pad's
    screws), the rest cut at CUT_Y; the largest component left is the coupler, the others its pins."""

    kept, dropped = [], 0
    for piece in pieces(triangles, mesh_decimate.WELD_SCALE):
        held = taken(triangles, [piece])
        if box(held)[0][1] > FINGERTIP_Y and min(min(abs(t[0]), abs(t[3]), abs(t[6])) for t in held) < FINGERTIP_X:
            dropped += 1
        else:
            kept.append(piece)
    if dropped < 2:
        raise ShowcaseError(f"finger_{side}: the fingertip (the pad and its screws) not found: another file?")
    below = cut_below(taken(triangles, kept), CUT_Y)
    found = pieces(below, mesh_decimate.WELD_SCALE)
    largest = max(range(len(found)), key=lambda number: (len(found[number]), -number))
    return taken(below, [found[largest]]), taken(below, [piece for number, piece in enumerate(found) if number != largest])


def split(triangles: list) -> dict:
    """{mesh name: triangles} of the closed file's triangles: MESHES' twelve, before any decimation."""

    groups = grouped(triangles)
    out = {f"body_{name}": held for name, held in body_parts(groups["body"]).items()}
    for name in ("link_r_outer", "link_r_inner", "link_l_outer", "link_l_inner"):
        if not groups[name]:
            raise ShowcaseError(f"{name} not found: another file?")
        out[name] = groups[name]
    for side in "rl":
        out[f"finger_{side}_coupler"], out[f"finger_{side}_pins"] = finger_parts(groups[f"finger_{side}"], side)
    return {name: out[name] for name, _, _ in MESHES}


# -- the build ---------------------------------------------------------------------------------------------------------

def source(folder: Path, name: str, digest: str) -> bytes:
    """The bytes of ``folder``/``name``, which must be the pinned file."""

    path = folder / name
    if not path.is_file():
        raise ShowcaseError(f"{name} is not in the sources' folder")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ShowcaseError(f"{name} is not the pinned file (SHA-256 {digest[:12]}...): another file is refused")
    return data


def build(folder: Path, out=print) -> tuple:
    """({path under web/: bytes}, {path: report}) of the showcase's meshes from the sources in ``folder``: the
    vendor's twelve and the holder, each decimated to TOLERANCE_MM and gated (mesh_decimate.decimate's report)."""

    files, reports = {}, {}
    parts = split(mesh_decimate.read_stl(source(folder, SOURCE_NAME, SOURCE_SHA256)))
    work = [(f"{library_write.SHOWCASE_VENDOR}/{name}.stl", parts[name], HEADER_CUT if cut else HEADER) for name, _, cut in MESHES]
    work.append((f"library/{HOLDER_BODY}", mesh_decimate.read_stl(source(folder, HOLDER_NAME, HOLDER_SHA256)), HEADER_HOLDER))
    for path, triangles, header in work:
        result, report = mesh_decimate.decimate(triangles, TOLERANCE_MM)
        files[path] = mesh_decimate.stl_bytes(result, header.encode("ascii"))
        reports[path] = report
        out(f"{path}: {report['triangles_in']} -> {report['triangles_out']} triangles, {len(files[path])} bytes, the source within "
            f"{report['source_to_result_mm']:.3f} mm of it and it within {report['result_to_source_mm']:.3f} mm of the source")
    return files, reports


def pins() -> dict:
    """{path under web/: its pinned SHA-256} of every mesh this tool writes and every shape it draws
    (tools/library_write.py's)."""

    out = {f"{library_write.SHOWCASE_VENDOR}/{name}": digest for name, digest in library_write.SHOWCASE_VENDOR_FILES.items()}
    out.update({f"library/{path}": digest for path, digest in library_write.SHOWCASE_BODIES.items()})
    return out


# -- the scene ---------------------------------------------------------------------------------------------------------

IDENTITY = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
MIRROR_X = [[-1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
# Half a turn about the gripper's axis (the vendor file's y): the right finger's place onto the left one's.
HALF_TURN_Y = [[-1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
# The part (the sensor finger, whose pad is the placed record's) is the gripper's LEFT finger, the UMI finger's file
# turned half a turn about the gripper's axis from the right finger's place (the finger is its own mirror image through
# the middle of its thickness, so it is the same finger there).  With the pad as the FlexiTac team mount it (its tails
# leaving to the viewer's left, the fingertip up) its straps then cross the side face that looks the way of the shell's
# face without the logo, and so do the mirror-image mate's: the owner's photo of the gripper, taken from the logo's
# side, shows both fingers' straps on the far side, through the fin's windows.
PART_SIDE = "l"
MATE_SIDE = "r"


def product(*matrices) -> list:
    """The product of 4 x 4 matrices (rows, applied to column vectors), left to right."""

    out = matrices[0]
    for other in matrices[1:]:
        out = [[math.fsum(out[i][k] * other[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
    return out


def inverse(matrix: list) -> list:
    """The inverse of a rigid matrix (a turn or a mirror image, then a shift): its 3 x 3 transposed, the shift undone."""

    turn = [[matrix[j][i] for j in range(3)] for i in range(3)]
    return [turn[i] + [-math.fsum(turn[i][k] * matrix[k][3] for k in range(3))] for i in range(3)] + [[0.0, 0.0, 0.0, 1.0]]


def shift(x: float, y: float, z: float = 0.0) -> list:
    return [[1.0, 0.0, 0.0, x], [0.0, 1.0, 0.0, y], [0.0, 0.0, 1.0, z], [0.0, 0.0, 0.0, 1.0]]


def about_z(angle: float, pivot: tuple) -> list:
    """A turn by ``angle`` (radians, counter-clockwise seen from +z) about the line through ``pivot`` (x, y) along z."""

    c, s = math.cos(angle), math.sin(angle)
    x, y = pivot
    return [[c, -s, 0.0, x - (c * x - s * y)], [s, c, 0.0, y - (s * x + c * y)], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def finger_on_holder() -> tuple:
    """(matrix, residual mm, lean degrees): the soft finger's file into the holder's: its length (-z) along the
    holder's +y, its contact normal (-x) along the holder's -x, its thickness (y) along the holder's z, centred
    between the flanges; in the plane, the rigid fit of its three holes onto the holder's (least squares)."""

    count = len(FINGER_HOLES)
    centre = [math.fsum(point[k] for point in FINGER_HOLES) / count for k in range(2)]
    onto = [math.fsum(point[k] for point in HOLDER_HOLES) / count for k in range(2)]
    pairs = [((p[0] - centre[0], p[1] - centre[1]), (q[0] - onto[0], q[1] - onto[1])) for p, q in zip(FINGER_HOLES, HOLDER_HOLES)]
    angle = math.atan2(math.fsum(p[0] * q[1] - p[1] * q[0] for p, q in pairs), math.fsum(p[0] * q[0] + p[1] * q[1] for p, q in pairs))
    c, s = math.cos(angle), math.sin(angle)
    move = (onto[0] - (c * centre[0] - s * centre[1]), onto[1] - (s * centre[0] + c * centre[1]))
    residual = max(max(abs(c * p[0] - s * p[1] + move[0] - q[0]), abs(s * p[0] + c * p[1] + move[1] - q[1]))
                   for p, q in zip(FINGER_HOLES, HOLDER_HOLES))
    # The finger's (x, -z) are the plane's axes: the matrix's first and third columns.
    matrix = [[c, 0.0, s, move[0]], [s, 0.0, -c, move[1]], [0.0, 1.0, 0.0, HOLDER_MID_Z + FINGER_THICK_MM / 2], [0.0, 0.0, 0.0, 1.0]]
    return matrix, residual, math.degrees(angle)


def finger_shift(angle: float) -> tuple:
    """A right finger's shift (x, y) with its links turned by ``angle`` (radians): its link tip's displacement."""

    c, s = math.cos(angle), math.sin(angle)
    return ((c - 1.0) * LINK[0] + s * LINK[1], -s * LINK[0] + (c - 1.0) * LINK[1])


def pose() -> dict:
    """The showcase's pose: the links' angle (radians) at which the sensors' centres are SENSOR_GAP_MM apart, the
    right finger's shift there and at the links' limit, and the soft finger's file into the vendor file's axes as the
    right finger with the fingers closed (closed) and at the pose (finger), and as the left finger at the pose
    (part: the right one turned half a turn about the gripper's axis, PART_SIDE)."""

    seat, residual, lean = finger_on_holder()
    closed = product(shift(*HOLDER_SHIFT), seat)
    centre = [math.fsum(closed[i][k] * SENSOR_CENTRE[k] for k in range(3)) + closed[i][3] for i in range(3)]
    # The right sensor's centre is x from the middle plane: the shift that leaves the two SENSOR_GAP_MM apart, and the
    # links' angle that gives it ((cos q - 1) Lx + sin q Ly = shift).
    wanted = SENSOR_GAP_MM / 2 - centre[0]
    angle = math.atan2(-LINK[0], LINK[1]) + math.asin((wanted + LINK[0]) / math.hypot(LINK[0], LINK[1]))
    moved = finger_shift(angle)
    finger = product(shift(*moved), closed)
    return {"angle": angle, "shift": moved, "limit": finger_shift(math.radians(LIMIT_DEG)), "closed": closed,
            "finger": finger, "part": product(HALF_TURN_Y, finger), "residual": residual, "lean": lean, "sensor": centre}


def rounded(matrix: list) -> list:
    """A matrix as the scene holds it: nine decimals (a rigid matrix to 1e-6 still), its last row exact."""

    return [[round(value, 9) + 0.0 for value in row] for row in matrix[:3]] + [[0.0, 0.0, 0.0, 1.0]]


def matrices() -> dict:
    """{mesh name, "holder_r", "holder_l", "mate": matrix} in the UMI finger's file axes (mm), and "approach"."""

    at = pose()
    into = inverse(at["part"])
    angle, (dx, dy) = at["angle"], at["shift"]
    out = {name: into for name in ("body_shell", "body_frame", "body_flange", "body_pins")}
    out["link_r_outer"] = product(into, about_z(-angle, PIVOT_OUTER))
    out["link_r_inner"] = product(into, about_z(-angle, PIVOT_INNER))
    out["link_l_outer"] = product(into, about_z(angle, (-PIVOT_OUTER[0], PIVOT_OUTER[1])))
    out["link_l_inner"] = product(into, about_z(angle, (-PIVOT_INNER[0], PIVOT_INNER[1])))
    for part in ("coupler", "pins"):
        out[f"finger_r_{part}"] = product(into, shift(dx, dy))
        out[f"finger_l_{part}"] = product(into, shift(-dx, dy))
    out["mate"] = product(into, MIRROR_X, at["part"])
    out["holder_r"] = product(into, shift(dx, dy), shift(*HOLDER_SHIFT))
    out["holder_l"] = product(out["mate"], out["holder_r"])
    out["approach"] = [into[k][1] for k in range(3)]
    return out


def along(direction: tuple, origin: tuple) -> list:
    """Axes into the part's: z along ``direction`` (a unit vector (x, z) in the plane of the finger's length and its
    back's normal), x across it (outward where z runs toward the base), y the finger's thickness, from ``origin`` (x, z)."""

    (ux, uz), (x, z) = direction, origin
    return [[uz, 0.0, ux, x], [0.0, 1.0, 0.0, 0.0], [-ux, 0.0, uz, z], [0.0, 0.0, 0.0, 1.0]]


def board_place() -> list:
    """The extender board's axes into the part's (BOARD_FROM_Z): z along the tails' plane toward the base."""

    reach = math.hypot(1.0, TAILS_PLANE[1])
    return along((TAILS_PLANE[1] / reach, 1.0 / reach), (TAILS_PLANE[0] + TAILS_PLANE[1] * BOARD_FROM_Z, BOARD_FROM_Z))


def cable_place() -> list:
    """The cable stub's axes into the part's: z from CABLE_FROM (the board's axes) straight toward CABLE_TO."""

    board = board_place()
    start = [math.fsum(board[i][k] * CABLE_FROM[k] for k in range(3)) + board[i][3] for i in range(3)]
    run = (CABLE_TO[0] - start[0], CABLE_TO[2] - start[2])
    reach = math.hypot(*run)
    return along((run[0] / reach, run[1] / reach), (start[0], start[2]))


def drawn_path(name: str) -> str:
    """A drawn shape's file, relative to web/library/."""

    return f"bodies/{library_write.SHOWCASE_ID}/drawn-{name}.stl"


def drawn_files() -> dict:
    """{path under web/: bytes} of DRAWN's shapes: each a binary STL of its boxes and cylinders under the header of a
    shape the project drew (tools/library_split.py own_header(): library_write.own_body() reads it)."""

    files = {}
    for name, (_, _, shapes) in DRAWN.items():
        records = [record for number, shape in enumerate(shapes) for record in library_split.drawn(shape, f"{name}: shape {number + 1}")]
        files[f"library/{drawn_path(name)}"] = library_split.stl(library_split.own_header(name), records)
    return files


def drawn_placements(placed: dict) -> list:
    """[(DRAWN's name, matrix into the part's axes, finger)] of every drawn shape the scene places, in the scene's
    order: the shell's twelve screws, each holder's three bolt heads and three nuts (the sensor finger's holder first),
    the block in the top slot."""

    into = placed["body_shell"]
    out = []
    for (*holes, z) in SHELL_SCREWS:
        for x, y in holes:
            out += [("shell-screw", product(into, shift(sign * x, y, z)), None) for sign in (1.0, -1.0)]
    for side, finger in ((PART_SIDE, "sensor"), (MATE_SIDE, "mate")):
        for name, z in (("holder-bolt", HOLDER_BOLT_Z), ("holder-nut", HOLDER_NUT_Z)):
            out += [(name, product(placed[f"holder_{side}"], shift(x, y, z)), finger) for x, y in HOLDER_HOLES]
    out.append(("slot-block", into, None))
    places = {"board": board_place(), "cable": cable_place()}
    for matrix, finger in ((IDENTITY, "sensor"), (placed["mate"], "mate")):
        out += [(name, product(matrix, places[FINGER_PLACES[name]]), finger) for name in FINGER_DRAWN]
    return out


def body(path: str, data: bytes, matrix: list, finger, look: str) -> dict:
    return {"mesh": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "triangles": library_write.stl_triangles(data), "matrix": rounded(matrix), "finger": finger, "look": look}


def scene_document(files: dict, parts: dict) -> dict:
    """The showcase's scene from its meshes (``files``: {path under web/: bytes}) and parts.json."""

    at = pose()
    placed = matrices()
    holder = files[f"library/{HOLDER_BODY}"]
    bodies = [body(HOLDER_BODY, holder, placed[f"holder_{PART_SIDE}"], "sensor", HOLDER_LOOK),
              body(HOLDER_BODY, holder, placed[f"holder_{MATE_SIDE}"], "mate", HOLDER_LOOK)]
    for name, _, _ in MESHES:
        finger = {f"finger_{PART_SIDE}": "sensor", f"finger_{MATE_SIDE}": "mate"}.get(name[:8])
        path = f"{library_write.SHOWCASE_VENDOR}/{name}.stl"
        bodies.append(body(f"../{path}", files[path], placed[name], finger, MESH_LOOKS[name]))
    for name, matrix, finger in drawn_placements(placed):
        bodies.append(body(drawn_path(name), files[f"library/{drawn_path(name)}"], matrix, finger, DRAWN[name][1]))
    degrees = math.degrees(at["angle"])
    stroke, limit = at["shift"][0], at["limit"][0]
    about = (
        "FlexiTac on the xArm Gripper G1 with UMI soft fingers: the hand-designed setup, not a generated fit, posed as the "
        f"FlexiTac Tactile Demo shows it: the links turned {degrees:.2f} degrees, so that the two sensors' centres are "
        f"{SENSOR_GAP_MM:g} mm apart (each finger {stroke:.2f} mm out, of {limit:.2f} mm at the links' {LIMIT_DEG:g} degrees).  "
        f"The gripper's twelve bodies (../{library_write.SHOWCASE_VENDOR}/) are UFACTORY's 3D model of the Gripper G1, the "
        "property of UFACTORY, used by the project owner's decision of 2026-11-12 and not covered by this repository's "
        "Apache-2.0 licence, split and decimated to within 0.1 mm by FlexiTac-Gen 2026 (that folder's NOTICE.md): the shell, "
        "the frame, the flange, the pivot pins, the four links, and each finger's coupler (the stock finger cut where the "
        "holder sits) and pins.  The two finger holders are HandUMI's UMI-RIGHT-Finger-Holder.stl (handumi-hw "
        f"{HANDUMI_COMMIT[:7]}, Apache-2.0), decimated to within 0.1 mm, the left one its mirror image.  The part is the "
        "Library's UMI fin-ray finger as the gripper's left finger, bolted to the holder by its three holes (a rigid fit of "
        f"the holes in the plane, {at['residual']:.3f} mm, which leans the finger {at['lean']:.2f} degrees): with the pad "
        "mounted as the FlexiTac team mount it, its straps cross the side face that looks the way of the shell's face "
        "without the logo, as on the gripper as built.  The linkage is a parallel four-bar: the "
        f"right links turn about ({PIVOT_OUTER[0]:g}, {PIVOT_OUTER[1]:g}) and ({PIVOT_INNER[0]:g}, {PIVOT_INNER[1]:g}) mm of the "
        f"model, their tips ({LINK[0]:g}, {LINK[1]:g}) mm from the pivots, and the fingers only translate; the numbers are the "
        "model's, not the real gripper's encoder positions.  The other finger is drawn as the mirror image across the "
        "gripper's middle plane, as the Tactile Demo draws it.  The gripper as built differs there (the owner's photo of "
        "it): its two holders are plain printed blocks that read as one part used twice, the second turned half a turn "
        "about the gripper's axis (bolt heads where the first shows its nuts), not HandUMI's holder and its mirror image.  "
        "Drawn by the project, as plain boxes and cylinders and no vendor's geometry (the files named drawn-): the heads of "
        "the shell's twelve black screws in their wells (the six on the logo's face as that photo shows them; the six on "
        "the other face, which no photo shows, in the wells the model has there), each holder's three bolt heads and nuts, "
        "the black block with its round cap in the shell's top slot, and behind each finger, placed by eye, a yellow "
        "extender board on the pad's two tails, each tail's end in one of its two sockets (the wide tail's at the board's "
        "upper edge; the Top FPC's tab through the board, which covers the strap that carries it), and from the lower "
        "socket a short stub of the white flat cable down the finger's back to its base.  The gripper as built has one "
        "small board for each tail.  "
        "The looks are the Library's base looks, each body's chosen after photos of the real gripper (black anodized links "
        "and flange), and seven looks of the showcase's own, each judged from both sides of the gripper: "
        "the shell's gloss white under a sharper clear coat, the printed parts' white (the frame's channel, the couplers "
        "and the holders), the pivot pins' brushed steel, the screws' matte black, the soft fingers' orange TPU (the "
        "Library's UMI rows' own), the extender boards' yellow and the flat cables' white.  "
        "The camera is the showcase's own, for this reason: at the rules' camera the far finger's pad is "
        "seen edge-on and its straps are on its far side; from the side of the shell's face without the logo, 60 degrees "
        "off the pad's normal and 20 degrees up, the pad's face, the straps crossing both fingers' side faces and the "
        "gripper's body are all seen; exploded, from the same side 70 degrees off the normal and 40 degrees up, so that the "
        "lifted layers are seen apart, not edge-on.  No finger is drawn see-through: the near finger hides nothing of the "
        "far one's pad from there.  The logo on the shell's other face is not drawn.")
    return {
        "format": library_write.SCENE_FORMAT,
        "part": library_write.UMI_FINGER,
        "part_mesh_sha256": parts["parts"][library_write.UMI_FINGER]["mesh"]["sha256"],
        "about": about,
        "frame": library_write.SCENE_FRAME,
        "approach": [round(value, 12) + 0.0 for value in placed["approach"]],
        "opening": {"q_mm": round(stroke, 3), "limit_mm": round(limit, 3), "joint": "the four-bar's links (each finger's shift across the jaws)",
                    "source": f"the FlexiTac Tactile Demo's pose: the sensors' centres {SENSOR_GAP_MM:g} mm apart, the links at "
                              f"{degrees:.2f} of {LIMIT_DEG:g} degrees"},
        "mate": {"kind": "mirror", "matrix": rounded(placed["mate"]), "part": True},
        "bodies": bodies,
        "see_through": SEE_THROUGH,
        "picture": PICTURE,
        "camera": CAMERA,
        "looks": LOOKS,
        "part_look": PART_LOOK,
        "smooth_deg": SMOOTH_DEG,
    }


def scene_text(document: dict) -> str:
    """The scene's file: JSON as the scenes are written (indent 1, ASCII, a trailing newline)."""

    return json.dumps(document, indent=1, ensure_ascii=True) + "\n"


# -- the notices' rows ---------------------------------------------------------------------------------------------------

def notice(files: dict, reports: dict) -> str:
    """The rows and notes of the two notices (web/vendor/ufactory-g1/NOTICE.md's table; web/library/NOTICE.md's row
    and note of the holder), from a build's files and reports."""

    lines = ["| File | What it is | Owner | Change | SHA-256 |", "| --- | --- | --- | --- | --- |"]
    notes = []
    for name, what, cut in MESHES:
        path = f"{library_write.SHOWCASE_VENDOR}/{name}.stl"
        report = reports[path]
        worst = max(report["source_to_result_mm"], report["result_to_source_mm"])
        change = f"modified: split{', cut at the holder' if cut else ''}, decimated (quadric error metrics, {worst:.3f} mm)"
        lines.append(f"| `{name}.stl` | {what} | {library_write.SHOWCASE_OWNER} | {change} | `{hashlib.sha256(files[path]).hexdigest()}` |")
        notes.append(f"- `{name}.stl`: {what}; from {report['triangles_in']} to {report['triangles_out']} triangles, "
                     f"{len(files[path])} bytes, within {worst:.3f} mm.")
    path = f"library/{HOLDER_BODY}"
    report = reports[path]
    worst = max(report["source_to_result_mm"], report["result_to_source_mm"])
    lines += ["", *notes, "", f"| `{HOLDER_BODY}` | handumi-hw `{HANDUMI_COMMIT[:7]}`, `{HOLDER_PATH}` | Apache-2.0, BrikHMP18 (HandUMI), "
              f"`licenses/handumi-hw.txt` | modified: decimated (quadric error metrics, {worst:.2f} mm) | `{hashlib.sha256(files[path]).hexdigest()}` |",
              "", f"the holder: from {report['triangles_in']} to {report['triangles_out']} triangles, {len(files[path])} bytes, within {worst:.3f} mm"]
    return "\n".join(lines) + "\n"


# -- the tool ----------------------------------------------------------------------------------------------------------

def committed() -> dict:
    """{path under web/: bytes} of the committed files this tool writes (those that are there)."""

    return {path: (WEB / path).read_bytes() for path in pins() if (WEB / path).is_file()}


def run(sources=None, check: bool = False, repin: bool = False, show_notice: bool = False, out=print) -> int:
    parts = json.loads((LIBRARY / "parts.json").read_text(encoding="utf-8"))
    pinned = pins()
    # The shapes the project draws need no source: drawn again on every run, held to their pins as the meshes are.
    drawn = drawn_files()
    differences = []
    if sources is not None:
        files, reports = build(Path(sources), out)
        if show_notice:
            out(notice(files, reports))
    else:
        files = {path: data for path, data in committed().items() if path not in drawn}
        meshes = sorted(set(pinned) - set(drawn))
        differences += [f"web/{path} is missing" for path in meshes if path not in files]
        differences += [f"web/{path} is not the pinned file (SHA-256)" for path, data in sorted(files.items())
                        if hashlib.sha256(data).hexdigest() != pinned[path]]
        if differences:
            out("\n".join(differences))
            out("library_showcase: the committed meshes are not the pinned ones: rebuild with --sources DIR")
            return 1
    files.update(drawn)
    unpinned = sorted(path for path, data in files.items() if hashlib.sha256(data).hexdigest() != pinned.get(path))
    for path in unpinned:
        out(f"library_showcase: web/{path} is {'drawn' if path in drawn else 'built'} as {hashlib.sha256(files[path]).hexdigest()}, "
            f"not the pinned {pinned.get(path)}")
    if unpinned and not repin:
        out("library_showcase: the build is not the pinned one: nothing written (--repin writes it; then update "
            "tools/library_write.py's pins and the notices' rows)")
        return 1
    files[f"library/{library_write.SHOWCASE_SCENE}"] = scene_text(scene_document(files, parts)).encode("ascii")
    for path, data in sorted(files.items()):
        target = WEB / path
        if not target.is_file() or target.read_bytes() != data:
            differences.append(f"web/{path}")
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    if differences:
        out(("would change: " if check else "wrote: ") + ", ".join(differences))
    if check:
        # The guards' own view of it (the folder's files and notice, the scene, anything else naming the folder, the
        # showcase's page: its pictures are stale once the scene is another).
        found, _ = library_write.showcase(parts, LIBRARY)
        for message in found:
            out(f"stale: {message}")
        if differences or found:
            return 1
        out(f"library_showcase: {len(pinned) - len(drawn)} meshes and {len(drawn)} drawn shapes at their pinned SHA-256, the scene and "
            "the notices current" + (", and the sources build them byte for byte" if sources is not None else ""))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", type=Path, default=None, metavar="DIR",
                        help=f"the folder holding {SOURCE_NAME!r} and {HOLDER_NAME} (read only): rebuild the meshes from them")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 naming each difference")
    parser.add_argument("--repin", action="store_true", help="write a build whose bytes are not the pinned ones")
    parser.add_argument("--notice", action="store_true", help="print the notices' rows and notes of a build")
    args = parser.parse_args(argv)
    try:
        return run(args.sources, args.check, args.repin, args.notice)
    except (ShowcaseError, mesh_decimate.MeshError, library_write.LibraryError, OSError, KeyError, ValueError) as error:
        print(f"library_showcase: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
