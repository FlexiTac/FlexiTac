"""The diagonal Row bus: the construction ``diagonal-bus/10`` behind ``routing.row_sides`` (masked-field phases P5b and P5f).

A surface design that names ``routing.row_sides`` (``left``, ``right`` or
``both``, seen from outside the stack with the tails down) is built by
``engine/diagonal.py``: every row trace runs as a slant from its electrode's
end, the lanes hug the field's boundary at the bundle pitch (diagonal-bus/1's
bands, turned down on the field's bottom edge, around the windows alone: the
boards overlap outside the field; on a receding field they follow it inward
down to its bottom edge), ``both`` splits the rows
(ROW_01, 03, ... on one side) and folds the Row contact order, and below the
field every Row trace turns once into a fan and once into its contact, then
runs straight down the tail, centred on the field in every side mode as the
Column tail (diagonal-bus/10, the user's request of the plan's section 27:
the tails within the sensor's width): with ``both`` the two sides meet in a
funnel into it, with one side they fan in under the field.  The Column
board has the copper of the straight one of the same design without
``routing.row_sides`` (its tail centred) with its V capped at 80 degrees
where that roots the tails no deeper, and the tails are stacked: the Row tail lies on the Column tail where they meet,
both leave on one side.  Down to the tails' roots (the deeper of the two
boards' own, below the outline's fillets into the tails; the shallower tail's
contact columns run on down to it) the two boards have one outline in the
stack (the union of their own); below it each is its own tail.  Both
outlines are regular: no vertex outside the fillets and the tails turns by
less than 5 degrees.  Outside the taxel field the two boards overlap freely
(claude/specs/masked-field/P5-diagonal-bus.md, sections 2-5, 12-15, 20 and 27).
These tests build through ``generate_design`` and measure with predicates of
their own:

- the named corpus (rectangle 32x12, soft finger 59x12 and the crank,
  equilateral and disk masks of ``tests/fixtures/diagonal_bus_masks.json``
  at 2 mm, fill 0.7, 4 mil, rows on top), each with ``both``, ``left`` and
  ``right``: every DRC record and the registration with every stack key,
  strict record 14, route-route exactly the trace space, at most two bends
  per Row and per Column trace below its field and each trace entering its
  tail straight, no trace part over the other board's electrodes or field
  window, the tails on one side, both centred on the field (the Row tail
  within a nanometre, its contacts the tail's positions 1..R from its
  canonical left: at its far end from the band where mirrored), the
  fans crossing the Column copper at 5 degrees or more and Row-on-Column runs
  off the stacked contact columns short, the two outlines one down to the
  tails' roots in the stack (our own predicates), the bands beside the field (the
  outline before it is made regular) never farther out than
  diagonal-bus/1's by more than 0.15 mm at any row but where the shared
  outline takes the Column board's own body, beside a field that does not
  recede never farther in either, and its tip never narrower
  (``tests/fixtures/diagonal_bus_v1_bands.json``); beside a receding field
  (the disk) the Row traces within their bundle and 1.5 mm of the field; the
  relative narrow tip, no flat lanes, and pinned tips, widths, the Row
  funnel's depth, the tails' roots, areas, the tails' overlap and the Column
  board's width and bands (within 0.01);
- the shared outline: on the named corpus, regressions of the design
  workflow judge's corpus and the user's CAD fits
  (``tests/fixtures/diagonal_bus_shared_outline.json``), both boards' copper
  and their outlines more than 1.0 mm below the shared level are those each
  board has with its own outline; both tails leave the shared body's bottom
  edge; the registration fails outlines that differ down to the tails' roots;
- the Column board: the straight Column board's copper planned with its V
  capped at 80 degrees (or the profile's own V where that roots the tails
  higher), its tail's root lowered to the shared bottom edge
  (the same centre lines, contacts and stiffener), under the shared outline;
- chamfered notches (diagonal-bus/6, the plan's section 16): no outline
  vertex inside a masked field's shallow notch, on every masked build
  checked (_check_clean) and on notched fields of every side mode against
  the staircase build (the copper equal, its outline inside);
- convex sides (diagonal-bus/9, the plan's section 24): on every build
  checked (_check_clean) no dent of a side from its tip corner down to its
  widest point at most a two-cell step deep but where bridging it would
  flatten that corner (_convex_problems); against the build without them
  the old outline inside the new one, the new within the bound of it, the
  copper, the widest and the narrow tip kept; the rule on a synthetic ring
  (the crank's kink bridged, a deeper pocket and an anchored dent kept);
- regular outlines (diagonal-bus/5): on the named corpus, the fixture's
  designs (the user's CAD fits among them) and the regressions, no vertex of
  either outline above its tail root turns by less than 5 degrees but on a
  fillet (our own predicate: a circle of the fillet radius or a halving
  through it); each board's outline contains the one built without the
  regularization (to the fillets' steps), keeps its copper and its
  relative narrow tip; the regularization on its own (a bent edge becomes
  one straight edge outside the bend, corners of 5 degrees or more and
  anchors stay, a smooth curve becomes a polygon of such corners);
- the sides and the folded contact order, in the stack and on the pads,
  with the tails on every side;
- a seeded random corpus of 100 designs (both role mappings, pitch
  0.8-4 mm, trace width and space 0.1016-0.2 mm, masks and rectangles, both
  and one side), a fine-pitch corpus (0.6-0.9 mm, with W_STACK_TRACE_WINDOW
  counted), reader tails of 16, 32, 48 and 64 pins, narrow and tiny fields,
  and the regression designs of the design workflow judge and the reviews
  (Row funnels bounded by diagonal-bus/1's and diagonal-bus/2's Row roots,
  where the prototypes went 50-113 mm deep, and the cost of the centred tail
  one-sided; the bands of the onion and the tips; mirrored reader tails);
- the centred Row tail (diagonal-bus/10): one side and both, an asymmetric
  field, a reader tail wider than the field (one side's inner flank slanting
  out to it below F's bottom) and the mirrored contacts;
- the stack registration keys on hand-edited pairs (stacked tails register,
  tails on two sides, traces over the other board's electrodes or window and
  outlines that differ down to the tails' roots do not), and the DRC gate;
- the contract (the field, its codes, the identity extra) and the pair cache;
- determinism: a pinned digest, the same on Python 3.9 and 3.12 and with
  any hash seed, and no float ``sum()`` or ordered set in the construction,
  its registration or its contract.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import io
import json
import math
import os
import random
import re
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from engine import ROW_BUS_VERSION, check_design, generate_design, load_profile, mask_class, validate_design
from engine import core, diagonal, drc
from engine import geometry as engine_geometry
from engine.core import IDENTITY_EXTRAS, _canonical_json, template_identity
from engine.drc import stack_frame, verify_board, verify_registration
from exporters import build_exports, direct_gerber

try:
    from geometry_checks import bounds, edges, point_in_polygon, point_segment_distance, polygon_inside, segment_distance, turns_degrees
    from test_mask_layout import _determinism_problems
except ImportError:  # run as tests.test_diagonal_bus
    from tests.geometry_checks import bounds, edges, point_in_polygon, point_segment_distance, polygon_inside, segment_distance, turns_degrees
    from tests.test_mask_layout import _determinism_problems

ROOT = Path(__file__).resolve().parents[1]
SURFACE = "surface_matrix_v1"
PROFILE = load_profile(SURFACE)
MASKS = json.loads((ROOT / "tests" / "fixtures" / "diagonal_bus_masks.json").read_text(encoding="utf-8"))
REGRESSIONS = json.loads((ROOT / "tests" / "fixtures" / "diagonal_bus_regressions.json").read_text(encoding="utf-8"))
V1_BANDS = json.loads((ROOT / "tests" / "fixtures" / "diagonal_bus_v1_bands.json").read_text(encoding="utf-8"))
SHARED = json.loads((ROOT / "tests" / "fixtures" / "diagonal_bus_shared_outline.json").read_text(encoding="utf-8"))["cases"]
SHARED_REGRESSIONS = json.loads((ROOT / "tests" / "fixtures" / "diagonal_bus_shared_regressions.json").read_text(encoding="utf-8"))
EPSILON = 1e-6
# The Row tail is centred on the field within the layout grid's step (diagonal-bus/10: its corner rounded to the grid).
CENTRED_NM = 1e-6
SIDES = ("both", "left", "right")
# The electrode overhang, the active-edge margin, the coverlay expansion and the opening-to-trace rule; the taper cap
# of the surface profile.
OVERHANG, MARGIN, EXPANSION, OPENING = 0.2, 0.5, 0.1, 0.15
TAPER_CAP = 85.0
# The fans never cross the Column copper closer to parallel than this (degrees: the entry-angle guard), and no Row net
# runs on a Column net for longer than this but on the stacked contact columns (mm; reported only, the registration's
# trace_overlap_mm: a Row trace on a Column trace is copper facing copper across the film, a parasitic crossing of that
# row and column, so a long run along the Column diagonals would add to one taxel's signal: the prototype C had 55 mm
# runs; the tails' contact columns, both at the 0.5 mm pitch, may lie on each other from the tails up to the last bends,
# 5.5 mm on reader:014).  Since diagonal-bus/8 a shallower tail's contact columns run on down to the shared bottom edge
# and may lie longer on the other board's raised stubs: 5.25 mm on the seeded corpus's design 28 (30 x 30 at 4 mm,
# masked, left), 2.9 mm at most elsewhere on the judge's 400 and that corpus.  Since diagonal-bus/10 one side's lanes run
# straight down beside the field to their fans under it and may lie on a straight Column trace there, straight on
# straight as the stacked contact columns: a wider Column tail's contact columns rising to its V (5.667 mm, a 32 x 3 at 4
# mm with a 64-pin Column tail; 0.0 under the band) or a Column trace dropping beside a narrowing field (5.529 mm, a 35 x
# 38 at 4 mm; 1.06): the most on 700 seeded designs and the harness's 2706 builds (P5-diagonal-bus.md section 27.3).
FAN_CROSSING_DEG = 5.0
RUN_BOUND_MM = 5.7
BAND_TOLERANCE = 0.15
STACK_KEYS = (
    "trace_over_other_electrode_count", "trace_over_other_window_count", "row_trace_to_column_window_mm",
    "column_trace_to_row_window_mm", "trace_crossing_count", "trace_crossing_pairs", "trace_crossing_min_angle_deg",
    "tail_sides_match", "tail_overlap_width_mm", "shared_outline_below_field_mm", "outline_deviation_over_field_mm",
    "outlines_coincide_over_field",
)
# Below the shared level a board steps in along it, or a fillet radius lower, and fillets that corner: its own outline
# more than two fillet radii below the level is diagonal-bus/3's.
JOIN_DEPTH = 1.0
# The registration keys of diagonal-bus/2's side-by-side tails, gone with the stacked tails.
GONE_KEYS = ("tail_gap_mm", "row_board_to_column_tail_mm", "column_board_to_row_tail_mm", "trace_beside_mm", "row_trace_to_column_trace_mm")

# The named corpus: tip width, the outline's width, the Row funnel's depth (its traces' last bends) and the tails' roots
# below the field, the outline areas above the roots, the stacked tails' overlap across them (tails down, in the stack)
# and the Column board's width, the widest band beyond F on the board's west and east sides (canonical frame, bottom
# tails), and whether the tip is the narrowest relative to F.  diagonal-bus/8 (P5-diagonal-bus.md section 20): both
# boards share one outline down to their tail roots, the deeper of the two boards' own roots lowered below the union's
# fillets into the tails (the Column board's width and area are the Row board's: the rectangle's Column board 31.335 ->
# 31.521 mm wide, the Row board 31.497 -> 31.521 where the Column fan-out reaches beyond the funnel), and the Column V is
# capped at 80 degrees where that roots the tails no deeper (so the Row fans keep 85 off its entry; the disk with both
# and the crank, the equilateral and the disk one-sided keep the profile's own V, 84 degrees): the funnels 0.1-3.4 mm
# shallower than diagonal-bus/7's Row roots (the crank's 9.132 -> 5.696), the tails' roots 3.9-6.5 mm below the field
# (the Column V's root, or the funnel's, below the fillets).  The earlier history:  The outlines are regular (diagonal-bus/5): the widths and bands are those of the regular outline, the
# tips diagonal-bus/1's but the equilateral's with both (0.57 mm wider: its slanted side one straight edge, GROWTH) and
# 1 micrometre at most elsewhere, the bands before the outline is made regular diagonal-bus/1's beside a field that does
# not recede (_check_bands); with both the Row roots lie 6.3-13.2 mm higher (the funnel against /1's corridor),
# one-sided 1.5-8.0 mm higher but for the soft finger (one inward run of 58 lanes under the band at 66 degrees, 1.06 mm
# deeper than /1's tail beside the centred Column tail).  The disk recedes below its equator: its lanes follow it inward to its bottom edge (no Column copper in their
# keep-out), so its Row roots lie 2.0-4.1 mm higher than diagonal-bus/4's first build (6.833, 3.781) and its Row tails
# move under the field, onto the Column tail one-sided; the outline over the field still takes the Column body's lower
# corners, 20 mm beyond the bottom rows (the Column traces drop straight down beside them).  The Column board's root is
# the straight one's (the design without routing.row_sides); over the field its outline is the shared one, so its width
# is the stack's above its root and its area the shared body's with its own fan-out.  With rows on top ROW_01's side is
# the stack's right, so ``left`` is the mirrored build.  diagonal-bus/6 crosses a masked field's shallow notches on F's hull
# (ChamferTests): the disk's tip 14.808 -> 17.208 mm with both and right (13.939 -> 14.800 left; its top rows step by two
# cells), the equilateral's 3.117 -> 4.317 (both), 3.089 -> 3.600 (left), 2.563 -> 3.763 (right), the one-sided inner
# flanks of the crank and the equilateral 1.2-1.6 mm beyond F (its notches' chamfers), the areas a little larger; the
# crank's tip with both and left and every width and root the same.  diagonal-bus/7 makes each side from the tip corner
# down to its widest point one straight line where one encloses it within 1.0 mm (StraightSideTests): the rectangle's
# and the soft finger's tips 24.468 -> 24.902 mm with both (0.234 and 0.200 mm per side at ROW_01), 24.652 one-sided,
# the crank's 8.468 -> 8.702 (both) and 8.652 (right; its long side a polyline: no line within 1.0 mm), the areas
# 0.3-1.3 mm2 larger, every width, root and band the same; the equilateral, the disk and the crank with left unchanged.
# The review of section 20 (the plan's 20.1): one-sided, the equilateral's side meets its flush Row tail on the shared
# level straight (it reached the level 16 um outside the tail's edge and stepped back), 61.587 -> 61.570 mm wide, the
# areas 0.6-0.7 mm2 larger (the tail's edge runs on up to the side's last corner).  Rewritten by section 24 (diagonal-bus/9,
# convex sides): each side's dents from the tip corner down to its widest point bridged where no deeper than a two-cell
# step (ConvexSideTests): the tips wider where a kink or a short step below the tip corner is bridged (the crank 8.702 ->
# 10.405 with both, 9.089 -> 11.306 left; the equilateral 4.317 -> 4.376, 3.600 -> 3.899, 3.763 -> 4.756; the disk 17.208
# -> 19.254, 14.800 -> 18.864, 17.208 -> 19.061), the areas 0.5-14.5 mm2 larger, the equilateral's west band 4.765 ->
# 4.775 with both; every width and root, the rectangle, the soft finger and the crank with right the same.  Rewritten by
# section 27 (diagonal-bus/10, the user's request of 2026-10-26: "some tails are not within the sensor's width"): the Row
# tail centred on the field in every side mode, on the centred Column tail, so the tails' overlap is the narrower one's
# width (one-sided 0-6.5 -> 6.5-16.5 mm; with both the disk's and the crank's 12.455 / 16.455 -> 12.5 / 16.5, their
# funnels' split 0.045 mm off the field's centre line before).  One side's whole bundle fans inward under the field, so
# its funnel lies 2.6-4.4 mm deeper (the rectangle 4.557 -> 7.206, the soft finger 8.125 -> 12.052, the crank 4.557 ->
# 8.955, the equilateral 3.502 -> 7.149, the disk 1.026-1.493 -> 4.893) and the tails' roots with it (the Column V
# capped there too), the areas above them 22-211 mm2 larger; the one-sided widths 0.148 mm narrower (the Row tail under
# the band reached that far beyond its band) but the disk's, the same, and the soft finger's, 2.652 mm wider (its 30 mm
# Row tail centred under its 23.4 mm field); with both the funnels and the roots within 0.091 mm, the areas within 2.4 mm2;
# the tips and the bands the same.  Re-pinned by section 27.8 (diagonal-bus/11, the convex flank: the multi-gripper
# video's notch below the field's outline corner on the side without the bus bridged): the one-sided areas 0.23-0.24 mm2
# larger (the soft finger's 1.06: its 30 mm Row tail wider than the field, the side slanting out from F's corner), every
# tip, width, funnel, root, overlap and band the same; with both nothing.
PINNED = {
    ("rectangle", "both"): (24.902, 31.521, 3.950, 4.730, 1927.77, 1927.77, 6.5, 31.521, 3.457, 3.355, True),
    ("rectangle", "left"): (24.652, 31.052, 7.206, 7.986, 1988.45, 1988.45, 6.5, 31.052, 0.0, 6.586, True),
    ("rectangle", "right"): (24.652, 31.052, 7.206, 7.986, 1988.45, 1988.45, 6.5, 31.052, 6.586, 0.0, True),
    ("soft finger", "both"): (24.903, 37.088, 5.893, 6.435, 3857.75, 3857.75, 6.5, 37.088, 6.204, 6.102, True),
    ("soft finger", "left"): (24.652, 39.338, 12.052, 12.716, 4076.85, 4076.85, 6.5, 39.338, 0.0, 12.101, True),
    ("soft finger", "right"): (24.652, 39.338, 12.052, 12.716, 4076.85, 4076.85, 6.5, 39.338, 12.101, 0.0, True),
    ("crank", "both"): (10.405, 71.521, 5.700, 6.480, 3394.56, 3394.56, 16.5, 71.521, 3.457, 6.232, True),
    ("crank", "left"): (11.306, 71.052, 8.955, 9.736, 3535.16, 3535.16, 16.5, 71.052, 0.0, 9.949, True),
    ("crank", "right"): (8.652, 71.052, 8.955, 9.736, 3379.94, 3379.94, 16.5, 71.052, 6.586, 1.2, True),
    ("equilateral", "both"): (4.376, 61.558, 4.709, 5.401, 1913.57, 1913.57, 12.5, 61.558, 4.775, 5.194, True),
    ("equilateral", "left"): (3.899, 61.422, 7.149, 7.841, 1932.44, 1932.44, 12.5, 61.422, 1.600, 7.953, True),
    ("equilateral", "right"): (4.756, 61.422, 7.149, 7.841, 1925.77, 1925.77, 12.5, 61.422, 6.976, 1.2, True),
    ("disk", "both"): (19.254, 51.772, 2.418, 3.919, 2298.67, 2298.67, 12.5, 51.772, 20.0, 20.0, True),
    ("disk", "left"): (18.864, 51.394, 4.893, 5.533, 2334.13, 2334.13, 12.5, 51.394, 20.0, 20.0, True),
    ("disk", "right"): (19.061, 51.597, 4.893, 5.533, 2337.02, 2337.02, 12.5, 51.597, 20.0, 20.0, True),
}
# diagonal-bus/2's Row roots below the field (its tails side by side, the Column fan-out moved beside the Row tail):
# the Row funnel (its last bends, _funnel_depth) never lies deeper, but where the straight Column fan-out enters at a smaller angle than the moved one
# (the rectangle with both: 84 degrees, the moved one 85) the entry-angle guard leaves the fans the 78-degree cap, not
# the 79-degree one (V2_ALLOWANCE).
V2_ROOTS = {
    ("rectangle", "both"): 4.797, ("rectangle", "left"): 4.798, ("rectangle", "right"): 4.798,
    ("soft finger", "both"): 6.043, ("soft finger", "left"): 8.366, ("soft finger", "right"): 8.366,
    ("crank", "both"): 9.132, ("crank", "left"): 4.798, ("crank", "right"): 4.798,
    ("equilateral", "both"): 7.875, ("equilateral", "left"): 3.743, ("equilateral", "right"): 3.743,
    ("disk", "both"): 6.833, ("disk", "left"): 3.781, ("disk", "right"): 3.781,
}
# diagonal-bus/10 (the plan's section 27, the user's request of 2026-10-26: "some tails are not within the sensor's
# width"): one side's Row tail is centred on the field, so the whole bundle fans inward under the field (half a funnel),
# not into a tail under the band: its funnel lies deeper than diagonal-bus/2's by this much (measured: the rectangle
# 2.408 mm, the soft finger 3.686, the crank 4.157, the equilateral 3.406, the disk 1.112), the cost of the tails within
# the sensor's width.
V2_ALLOWANCE = {
    ("rectangle", "both"): 0.09, ("rectangle", "left"): 2.41, ("rectangle", "right"): 2.41, ("soft finger", "left"): 3.69,
    ("soft finger", "right"): 3.69, ("crank", "left"): 4.16, ("crank", "right"): 4.16, ("equilateral", "left"): 3.41,
    ("equilateral", "right"): 3.41, ("disk", "left"): 1.12, ("disk", "right"): 1.12,
}
# diagonal-bus/1 on the named corpus (measured on its last build): the outline's overhang beyond the electrodes at the
# field's bottom edge (west, east; canonical frame) and its Row root below the field.  The bands keep within 0.15 mm
# of these (and of its bands at every row, V1_BANDS), and with both the Row root is never more than 1.0 mm deeper.
V1 = {
    ("rectangle", "both"): (3.7287, 3.691, 11.8141), ("rectangle", "left"): (0.3, 6.9518, 6.2778),
    ("rectangle", "right"): (6.9518, 0.3, 6.2778), ("soft finger", "both"): (6.5862, 6.3422, 19.1914),
    ("soft finger", "left"): (0.3, 12.4382, 7.3076), ("soft finger", "right"): (12.4382, 0.3, 7.3076),
    ("crank", "both"): (3.7287, 3.691, 17.7377), ("crank", "left"): (0.3, 6.9518, 11.8619),
    ("crank", "right"): (6.9518, 0.3, 11.8619), ("equilateral", "both"): (2.9008, 2.8725, 14.1665),
    ("equilateral", "left"): (0.3, 5.3239, 9.9516), ("equilateral", "right"): (5.3239, 0.3, 9.9516),
    ("disk", "both"): (2.1625, 1.9386, 13.6805), ("disk", "left"): (-19.7, 4.377, 9.2401), ("disk", "right"): (4.377, -19.7, 9.2401),
}
# The rows whose lanes leave flat (flat_lane_rows): none on the named corpus.  With the stacked Column copper in the
# lanes' keep-out (diagonal-bus/4's first build) the disk's rows enclosed by raised Column stubs escaped flat across them:
# 16-24 with both, 15-24 with left.
FLAT_ROWS: dict = {}
# The Row traces beside the field keep within their bundle (the lanes of the larger side at the bundle pitch) and this
# of a Row electrode (mm; our own _stray_from_field): the disk's lanes follow it inward (diagonal-bus/4's first build put
# them 11.1 mm from the disk's lower rows with both, against a bound of 3.94 mm).
STRAY_ALLOWANCE = 1.5


def _request(rows: int, columns: int, mask=None, *, sides="both", pitch=2.0, cell=1.4, trace=0.1016, space=0.1016,
             top="rows", pins=(None, None), tails=(12.0, 7.5)) -> dict:
    matrix = {"rows": rows, "columns": columns, "pitch_x_mm": pitch, "pitch_y_mm": pitch, "taxel_width_mm": cell, "taxel_height_mm": cell}
    if mask is not None:
        matrix["mask"] = [list(span) for span in mask]
    routing = {"trace_width_mm": trace, "trace_space_mm": space}
    if sides is not None:
        routing["row_sides"] = sides
    return {
        "schema_version": "tactile-fpc-design/v1", "template_id": SURFACE, "matrix": matrix, "routing": routing,
        "role_mapping": {"top": top, "bottom": "columns" if top == "rows" else "rows"},
        "tail": {"top_length_mm": tails[0], "bottom_length_mm": tails[1]},
        "connector": {"row_pins": pins[0], "column_pins": pins[1]},
    }


def _named(name: str, sides: str) -> dict:
    if name == "rectangle":
        return _request(32, 12, sides=sides)
    if name == "soft finger":
        return _request(59, 12, sides=sides)
    entry = MASKS[name]
    return _request(entry["rows"], entry["columns"], entry["mask"], sides=sides)


def _flipped(design: dict) -> bool:
    """The one-sided bus opposite ROW_01's side with both (the mirrored build): rows on top put that side right."""

    sides = design["routing"]["row_sides"]
    near = "right" if design["role_mapping"]["top"] == "rows" else "left"
    return sides != "both" and sides != near


def _at_the_level(design: dict, **patches) -> dict:
    """The design built with ``engine.diagonal``'s functions replaced (``patches``: name -> replacement) but at the full
    build's shared level (its tails' roots: the level is chosen below the union's fillets into the tails, which the
    replaced functions may move), so the two builds have the same copper; the pair cache cleared around it."""

    depth = generate_design(copy.deepcopy(design))["boards"]["row"]["construction"]["row_bus"]["shared_outline_below_field_mm"]
    original = diagonal._share_outline

    def share(geo, owns, column, plan, level, probe=False):
        return -depth if probe else original(geo, owns, column, plan, level)

    diagonal._pair_text.cache_clear()
    try:
        with mock.patch.multiple(diagonal, _share_outline=mock.DEFAULT, **{name: mock.DEFAULT for name in patches}) as mocks:
            mocks["_share_outline"].side_effect = share
            for name, replacement in patches.items():
                mocks[name].side_effect = replacement
            return generate_design(copy.deepcopy(design))
    finally:
        diagonal._pair_text.cache_clear()


def _no_convex(ring, level, rounded, anchors, depth):
    return ring, []


def _plain(design: dict) -> dict:
    """The design built without the regularization, the straight sides and the convex sides (diagonal-bus/5's outlines
    before their flat runs become straight edges: every ``_regular``, ``_straight_sides`` and ``_convex_sides`` an
    identity), at the full build's shared level (:func:`_at_the_level`)."""

    return _at_the_level(design, _regular=lambda ring, anchors: [[float(p[0]), float(p[1])] for p in ring],
                         _straight_sides=lambda ring, level, run, rings, rounded=None: ring, _convex_sides=_no_convex)


def _unstraight(design: dict) -> dict:
    """The design built without the straight sides and the convex sides (diagonal-bus/6's outlines: ``_straight_sides``
    and ``_convex_sides`` identities), at the full build's shared level (:func:`_at_the_level`)."""

    return _at_the_level(design, _straight_sides=lambda ring, level, run, rings, rounded=None: ring, _convex_sides=_no_convex)


def _unconvex(design: dict) -> dict:
    """The design built without the convex sides (diagonal-bus/8's outlines: ``_convex_sides`` an identity), at the full
    build's shared level (:func:`_at_the_level`)."""

    return _at_the_level(design, _convex_sides=_no_convex)


def _unflanked(design: dict) -> dict:
    """The design built without the convex flank (diagonal-bus/10's outlines: ``_convex_flank`` changing nothing), at the
    full build's shared level (:func:`_at_the_level`)."""

    return _at_the_level(design, _convex_flank=lambda ring, level, anchors, y_field, rules: None)


# --------------------------------------------------------------------------
# Predicates of our own (no engine geometry).
# --------------------------------------------------------------------------


def _crossings(ring, y: float) -> list[float]:
    return sorted(
        a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) for a, b in edges(ring) if (a[1] > y) != (b[1] > y)
    )


def _area_above(ring, y: float) -> float:
    """The area of the ring's part above the height ``y`` (the ring clipped to the half plane, shoelace)."""

    clipped = []
    count = len(ring)
    for index in range(count):
        a, b = ring[index], ring[(index + 1) % count]
        if a[1] >= y:
            clipped.append(a)
        if (a[1] >= y) != (b[1] >= y):
            t = (y - a[1]) / (b[1] - a[1])
            clipped.append([a[0] + (b[0] - a[0]) * t, y])
    return abs(math.fsum(p[0] * q[1] - q[0] * p[1] for p, q in edges(clipped))) / 2


def _root(board) -> float:
    tail = board["tail"]["bounds"]
    return tail["y"] + tail["height"]


def _funnel_depth(row) -> float:
    """Our own: how far below the taxel field (tails down) the Row traces make their last bend, into their contact
    columns: the Row funnel's (or one side's fans') depth, the Row tail root before diagonal-bus/8 moved both tails' roots
    to the deeper of the two boards' (its tail root lies a junction drop or more below it)."""

    turn = _down(row)
    region = row["grid_registration"]["active_region"]
    bottom = min(turn(corner)[1] for corner in ((region["x"], region["y"]), (region["x"] + region["width"], region["y"] + region["height"])))
    lowest = bottom
    for path in _net_paths(row).values():  # the contact upward
        for a, b, c in zip(path, path[1:], path[2:]):
            ux, uy, vx, vy = b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1]
            if abs(math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy))) > 1.0:
                lowest = min(lowest, b[1])
                break
    return bottom - lowest


def _rows(board) -> dict:
    """net -> its electrode box."""

    return {electrode["net"]: bounds(electrode) for electrode in board["layers"]["top_copper"]["electrodes"]}


def _measure(result) -> tuple:
    """The PINNED tuple of a bottom-tail build (canonical frame): the Row funnel's depth and the tails' shared roots below
    the field (the Column board's root; the Row board's is the same, _check_clean)."""

    row, column = result["boards"]["row"], result["boards"]["column"]
    ring = row["outline"]["points"]
    electrodes = _rows(row)
    rows = len(electrodes)
    region, column_region = row["grid_registration"]["active_region"], column["grid_registration"]["active_region"]
    tip_box = electrodes["ROW_01"]
    hits = _crossings(ring, (tip_box[1] + tip_box[3]) / 2)
    west_band = east_band = -math.inf
    for k in range(1, rows + 1):
        x0, y0, x1, y1 = electrodes[f"ROW_{k:02d}"]
        cut = _crossings(ring, (y0 + y1) / 2)
        west_band = max(west_band, (x0 + OVERHANG - MARGIN) - cut[0])
        east_band = max(east_band, cut[-1] - (x1 - OVERHANG + MARGIN))
    xs = [point[0] for point in ring]
    column_xs = [point[0] for point in column["outline"]["points"]]
    return (
        hits[-1] - hits[0], max(xs) - min(xs), _funnel_depth(row), column_region["y"] - _root(column),
        _area_above(ring, _root(row)), _area_above(column["outline"]["points"], _root(column)),
        _tail_overlap(result), max(column_xs) - min(column_xs), west_band, east_band,
        row["construction"]["row_bus"]["tip_is_narrowest_relative"],
    )


def _edge_overhang(row) -> tuple:
    """The Row outline's overhang beyond the electrodes at the field's bottom edge (west, east; canonical frame)."""

    boxes = _rows(row).values()
    low = min(box[1] for box in boxes)
    hits = _crossings(row["outline"]["points"], low + EPSILON)
    return min(box[0] for box in boxes) - hits[0], hits[-1] - max(box[2] for box in boxes)


def _row_frame(row):
    """Our own: the frame of tests/fixtures/diagonal_bus_v1_bands.json, a board point turned tail down and taken from
    the active region's lower-left corner."""

    turn = _down(row)
    region = row["grid_registration"]["active_region"]
    corners = [turn((region["x"], region["y"])), turn((region["x"] + region["width"], region["y"] + region["height"]))]
    ox, oy = min(c[0] for c in corners), min(c[1] for c in corners)
    return lambda point: [turn(point)[0] - ox, turn(point)[1] - oy]


def _band_extents(row, ring=None) -> dict:
    """Our own: per Row net, the outline's west and east extent at its electrode's centre and just above its bottom (from
    the active region's lower-left corner, tail down): the format of tests/fixtures/diagonal_bus_v1_bands.json.
    ``ring``: another outline in that frame, measured at the same heights."""

    frame = _row_frame(row)
    if ring is None:
        ring = [frame(point) for point in row["outline"]["points"]]
    answer = {}
    for net, (x0, y0, x1, y1) in _rows(row).items():
        ys = sorted(frame(corner)[1] for corner in ((x0, y0), (x1, y1)))
        centre, low = _crossings(ring, (ys[0] + ys[1]) / 2), _crossings(ring, ys[0] + EPSILON)
        answer[net] = (centre[0], centre[-1], low[0], low[-1])
    return answer


def _column_body(result) -> list:
    """The Column board's own outline (the straight Column board of the design, before the shared outline) in the Row
    board's frame of _band_extents, through the stack: the body the shared outline may take beside the field."""

    row = result["boards"]["row"]
    design = result["design"]
    own = diagonal._column_board(design, PROFILE, diagonal._column_plan(design, PROFILE))
    frame, stacked = _row_frame(row), _stack_down(row)
    # The stack frame onto the Row frame (a rotation or a mirror and a shift), from three corners of ROW_01's electrode.
    x0, y0, x1, y1 = _rows(row)["ROW_01"]
    corners = [(x0, y0), (x1, y0), (x0, y1)]
    (r0, r1, r2), (s0, s1, s2) = [frame(c) for c in corners], [stacked(c) for c in corners]
    a, b, c, d = s1[0] - s0[0], s2[0] - s0[0], s1[1] - s0[1], s2[1] - s0[1]
    det = a * d - b * c
    inverse = ((d / det, -b / det), (-c / det, a / det))
    columns = [[r1[k] - r0[k] for k in range(2)], [r2[k] - r0[k] for k in range(2)]]

    def onto(point):
        u = inverse[0][0] * (point[0] - s0[0]) + inverse[0][1] * (point[1] - s0[1])
        v = inverse[1][0] * (point[0] - s0[0]) + inverse[1][1] * (point[1] - s0[1])
        return [r0[k] + u * columns[0][k] + v * columns[1][k] for k in range(2)]

    convert = _stack_down(own)
    return [onto(convert(point)) for point in own["outline"]["points"]]


def _receding(row) -> tuple:
    """Our own: whether the field recedes on the west and on the east (the Row frame): some row reaches farther out than
    the bottom row's electrode, so the lanes beside the rows below it follow the field inward."""

    frame = _row_frame(row)
    boxes = []
    for x0, y0, x1, y1 in _rows(row).values():
        corners = [frame(corner) for corner in ((x0, y0), (x1, y1))]
        boxes.append((min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners)))
    bottom = min(boxes, key=lambda box: box[1])
    return min(box[0] for box in boxes) < bottom[0] - EPSILON, max(box[2] for box in boxes) > bottom[2] + EPSILON


def _check_bands(test: unittest.TestCase, result, reference: dict) -> None:
    """The bands beside the field (``result`` built without the regularization, :func:`_plain`: the lanes' envelope; the
    regular outline only lies outside it, RegularOutlineTests) against diagonal-bus/1's at every row's centre and bottom: never farther out than its by
    more than BAND_TOLERANCE but where the boards' shared outline over the field takes the Column board's own body (the
    disk's lower corners, a Column body side moved out for its fillet); on a side where the field does not recede never
    farther in either (the lanes are its there), while on a receding side the lanes follow the field inward
    (_stray_from_field bounds them where it is measured).  The tip's width (ROW_01's centre) is never narrower than its
    (to the fixture's rounding)."""

    row = result["boards"]["row"]
    got, body = _band_extents(row), _band_extents(row, _column_body(result))
    chamfers = _chamfer_extents(row, max(result["design"]["matrix"]["pitch_x_mm"], result["design"]["matrix"]["pitch_y_mm"]))
    receding = _receding(row)
    test.assertEqual(sorted(got), sorted(reference["bands"]))
    for net, want in sorted(reference["bands"].items()):
        for value, expected, own, outward, side, index in zip(got[net], want, body[net], (-1, 1, -1, 1), (0, 1, 0, 1), range(4)):
            if (value - expected) * outward > BAND_TOLERANCE and not (chamfers.get(net) and chamfers[net][index] is not None
                                                                      and abs(value - chamfers[net][index]) <= 1e-5):
                test.assertAlmostEqual(value, own, delta=1e-5, msg=(net, got[net], want, "beyond diagonal-bus/1's but not the Column body's or F's chamfer"))
            if not receding[side]:
                test.assertGreaterEqual((value - expected) * outward, -BAND_TOLERANCE, (net, got[net], want))
    tip, want = got["ROW_01"], reference["bands"]["ROW_01"]
    test.assertGreaterEqual(tip[1] - tip[0], want[1] - want[0] - 2e-4)


def _chamfer_extents(row, pitch: float) -> dict:
    """Our own: per Row net, the extremes of F's chamfered notches (:func:`_notch_pockets`) at the heights of
    :func:`_band_extents` (None where none spans them): where the outline crosses a notch (diagonal-bus/6) it may lie
    beyond diagonal-bus/1's bands."""

    frame = _row_frame(row)
    pockets = [[frame(p) for p in [u, *between, v]] for u, v, between in _notch_pockets(row, pitch)]
    answer = {}
    for net, (x0, y0, x1, y1) in _rows(row).items():
        ys = sorted(frame(corner)[1] for corner in ((x0, y0), (x1, y1)))
        found = []
        for y in ((ys[0] + ys[1]) / 2, ys[0] + EPSILON):
            xs = [x for pocket in pockets for x in _crossings(pocket, y)]
            found += [min(xs), max(xs)] if xs else [None, None]
        answer[net] = (found[0], found[1], found[2], found[3])
    return answer


def _stray_from_field(row) -> float:
    """Our own: how far the Row traces stray from the field beside it, the largest distance from a point of a Row trace
    at or above the field's bottom edge (every 0.05 mm along it) to the nearest Row electrode."""

    boxes = list(_rows(row).values())
    turn = _down(row)
    low = min(min(turn(corner)[1] for corner in ((box[0], box[1]), (box[2], box[3]))) for box in boxes)
    worst = 0.0
    for route in row["layers"]["top_copper"]["routes"]:
        for a, b in zip(route["points"], route["points"][1:]):
            steps = max(1, int(math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) / 0.05))
            for step in range(steps + 1):
                point = (a[0] + (b[0] - a[0]) * step / steps, a[1] + (b[1] - a[1]) * step / steps)
                if turn(point)[1] < low - EPSILON:
                    continue
                nearest = min(math.sqrt(max(box[0] - point[0], 0.0, point[0] - box[2]) ** 2 + max(box[1] - point[1], 0.0, point[1] - box[3]) ** 2)
                              for box in boxes)
                worst = max(worst, nearest)
    return worst


def _x_at(path, y: float) -> float:
    """Our own: where a centre line (contact upward) crosses the height ``y``."""

    for a, b in zip(path, path[1:]):
        if min(a[1], b[1]) <= y <= max(a[1], b[1]) and a[1] != b[1]:
            return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
    raise AssertionError(f"the centre line does not cross {y}")


def _down(board):
    """A board's points turned so its tail points down (a rotation; the canonical frame up to a translation)."""

    side = board["tail"]["side"]

    def turn(point):
        x, y = float(point[0]), float(point[1])
        return {"bottom": [x, y], "top": [-x, -y], "left": [-y, x], "right": [y, -x]}[side]

    return turn


def _row_levels(row) -> list:
    """Per ROW_k (k = 1..R): the centre height, the electrode's bottom and F's width there, tail down."""

    turn = _down(row)
    answer = []
    for k in range(1, len(_rows(row)) + 1):
        x0, y0, x1, y1 = _rows(row)[f"ROW_{k:02d}"]
        corners = [turn(corner) for corner in ((x0, y0), (x1, y1))]
        xs, ys = sorted(corner[0] for corner in corners), sorted(corner[1] for corner in corners)
        answer.append(((ys[0] + ys[1]) / 2, ys[0], xs[1] - xs[0] - 2 * OVERHANG + 2 * MARGIN))
    return answer


def _narrowest_relative(row) -> bool:
    """Our own: no row whose part of F is at least as wide as ROW_01's has a narrower board than the tip."""

    turn = _down(row)
    ring = [turn(point) for point in row["outline"]["points"]]
    widths = []
    for centre, _, field in _row_levels(row):
        hits = _crossings(ring, centre)
        widths.append((hits[-1] - hits[0], field))
    tip, tip_field = widths[0]
    return all(width >= tip - EPSILON for width, field in widths if field >= tip_field - EPSILON)


def _flat_rows(row, design) -> list:
    """Our own: the rows whose lane, above the field's bottom window level (the electrodes' bottom less the overhang, the
    coverlay expansion and the window clearance: below it the fans start), has a segment more than the taper cap from
    the vertical."""

    turn = _down(row)
    bottom = min(level[1] for level in _row_levels(row))
    cut = bottom - (OVERHANG + EXPANSION + OPENING + design["routing"]["trace_width_mm"] / 2) - 0.01
    flat = []
    for route in row["layers"]["top_copper"]["routes"]:
        if route["segment"] != "fanout":
            continue
        points = [turn(point) for point in route["points"]]
        for a, b in zip(points, points[1:]):
            if max(a[1], b[1]) > cut and math.degrees(math.atan2(abs(b[0] - a[0]), abs(b[1] - a[1]))) > TAPER_CAP + 1e-9:
                flat.append(int(route["net"][4:]))
                break
    return sorted(flat)


def _net_paths(board) -> dict:
    """Our own: net -> its route's centre line from the contact to the electrode's end, tails down (the board's
    tail piece and fan-out piece chained at their shared end)."""

    turn = _down(board)
    pieces: dict = {}
    for route in board["layers"]["top_copper"]["routes"]:
        pieces.setdefault(route["net"], []).append([turn(point) for point in route["points"]])
    answer = {}
    for net, parts in sorted(pieces.items()):
        path, rest = list(parts[0]), parts[1:]
        while rest:
            for index, part in enumerate(rest):
                if math.dist(part[0], path[-1]) <= 1e-6:
                    path += part[1:]
                elif math.dist(part[-1], path[-1]) <= 1e-6:
                    path += list(reversed(part))[1:]
                elif math.dist(part[-1], path[0]) <= 1e-6:
                    path = part[:-1] + path
                elif math.dist(part[0], path[0]) <= 1e-6:
                    path = list(reversed(part))[:-1] + path
                else:
                    continue
                rest.pop(index)
                break
            else:
                raise AssertionError(f"{net}: its route pieces do not chain")
        if path[0][1] > path[-1][1]:
            path.reverse()  # from the contact (lowest) up to the electrode's end
        answer[net] = path
    return answer


def _bends_below(path, level: float) -> int:
    """Our own: the vertices of a centre line strictly below ``level`` where it turns by more than 1 degree."""

    count = 0
    for a, b, c in zip(path, path[1:], path[2:]):
        ux, uy, vx, vy = b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1]
        if b[1] < level - 1e-9 and abs(math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy))) > 1.0:
            count += 1
    return count


def _below_field(board) -> dict:
    """Our own: net -> ``(bends below the lowest electrode's bottom, slanted pieces below it, straight into the tail)``:
    the last is whether the piece that runs down into the tail root (the first one reaching above it from the contact)
    is vertical, so after its last bend every trace runs straight down to its contact."""

    turn = _down(board)
    lowest = min(min(turn(corner)[1] for corner in ((box[0], box[1]), (box[2], box[3]))) for box in _rows(board).values())
    tail = board["tail"]["bounds"]
    root = max(turn(corner)[1] for corner in ((tail["x"], tail["y"]), (tail["x"] + tail["width"], tail["y"] + tail["height"])))
    answer = {}
    for net, path in _net_paths(board).items():
        slanted = 0
        for a, b in zip(path, path[1:]):  # the contact upward
            if min(a[1], b[1]) < lowest - 1e-9:
                slanted += abs(b[0] - a[0]) > 1e-6
        into = next(abs(b[0] - a[0]) <= 1e-6 for a, b in zip(path, path[1:]) if max(a[1], b[1]) > root + 1e-6)
        answer[net] = (_bends_below(path, lowest), slanted, into)
    return answer


def _zip_member(data: bytes, name: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return archive.read(name)


def _outside(a, b, box) -> list:
    """Our own: the parts of the segment a-b outside the box (Liang-Barsky)."""

    dx, dy = b[0] - a[0], b[1] - a[1]
    enter, leave = 0.0, 1.0
    for p, q in ((-dx, a[0] - box[0]), (dx, box[2] - a[0]), (-dy, a[1] - box[1]), (dy, box[3] - a[1])):
        if abs(p) < 1e-15:
            if q < 0:
                return [(a, b)]
            continue
        if p < 0:
            enter = max(enter, q / p)
        else:
            leave = min(leave, q / p)
    if enter >= leave:
        return [(a, b)]
    parts = []
    if enter > 1e-12:
        parts.append((a, (a[0] + dx * enter, a[1] + dy * enter)))
    if leave < 1 - 1e-12:
        parts.append(((a[0] + dx * leave, a[1] + dy * leave), b))
    return parts


def _window_problems(result) -> list:
    """Our own: the stacked route parts of each board, outside their own electrode grown by the coverlay expansion,
    the opening-to-trace rule and half their width, whose copper reaches the other board's electrode openings (the
    merged field window or one per electrode)."""

    problems = []
    for key, other in (("row", "column"), ("column", "row")):
        board, peer = result["boards"][key], result["boards"][other]
        convert, peer_convert = stack_frame(board), stack_frame(peer)
        rings = []
        for opening in peer["layers"]["top_coverlay_openings"]:
            if opening["kind"] not in ("electrode_field_opening", "sensor_electrode_opening"):
                continue
            if opening.get("shape") == "polygon":
                ring = [peer_convert(point) for point in opening["points"]]
            else:
                x0, y0, x1, y1 = bounds(opening)
                ring = [peer_convert(point) for point in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            rings.append((ring, (min(p[0] for p in ring), min(p[1] for p in ring), max(p[0] for p in ring), max(p[1] for p in ring))))
        own = {}
        for electrode in board["layers"]["top_copper"]["electrodes"]:
            x0, y0, x1, y1 = bounds(electrode)
            corners = [convert(point) for point in ((x0, y0), (x1, y1))]
            own[electrode["net"]] = (min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners), max(c[1] for c in corners))
        for route in board["layers"]["top_copper"]["routes"]:
            radius = route["width_mm"] / 2
            grow = EXPANSION + OPENING + radius
            box = own[route["net"]]
            zone = (box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow)
            points = [convert(point) for point in route["points"]]
            for a, b in zip(points, points[1:]):
                for c, d in _outside(a, b, zone):
                    for ring, (x0, y0, x1, y1) in rings:
                        if min(c[0], d[0]) > x1 + radius or max(c[0], d[0]) < x0 - radius or min(c[1], d[1]) > y1 + radius or max(c[1], d[1]) < y0 - radius:
                            continue
                        if point_in_polygon(c, ring) or point_in_polygon(d, ring) or min(segment_distance(c, d, p, q) for p, q in edges(ring)) <= radius + EPSILON:
                            problems.append((key, route["net"]))
    return problems


def _runs_off_the_contact_columns(result) -> float:
    """Our own: the longest run of one Row net's copper on one Column net's (parallel segments whose copper overlaps
    across them, their runs summed per net pair), in the stack turned so the tails point down, but for the stacked
    contact columns: vertical runs across the width both tails share, where a contact column of one tail lies on one of
    the other's (both at the 0.5 mm contact pitch) from the tails up to the traces' last bends."""

    row, column = result["boards"]["row"], result["boards"]["column"]

    def segments(board):
        convert = _stack_down(board)
        answer = []
        for route in board["layers"]["top_copper"]["routes"]:
            points = [convert(point) for point in route["points"]]
            answer.extend((route["net"], a, b, route["width_mm"] / 2) for a, b in zip(points, points[1:]) if math.dist(a, b) > 1e-9)
        return answer

    row_tail, column_tail = _tails_down(result)
    shared = (max(row_tail[0], column_tail[0]), min(row_tail[2], column_tail[2]))
    runs: dict = {}
    for row_net, a, b, row_radius in segments(row):
        length = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        if abs(ux) <= 1e-9 and shared[0] <= a[0] <= shared[1]:
            continue  # a stacked contact column
        for column_net, c, d, column_radius in segments(column):
            vx, vy = d[0] - c[0], d[1] - c[1]
            if abs(ux * vy - uy * vx) > 1e-6 * math.hypot(vx, vy):
                continue
            along = sorted(((c[0] - a[0]) * ux + (c[1] - a[1]) * uy, (d[0] - a[0]) * ux + (d[1] - a[1]) * uy))
            offset = abs(((c[0] + d[0]) / 2 - a[0]) * uy - ((c[1] + d[1]) / 2 - a[1]) * ux)
            width = min(row_radius, offset + column_radius) - max(-row_radius, offset - column_radius)
            run = min(length, along[1]) - max(0.0, along[0])
            if width > EPSILON and run > EPSILON:
                runs[(row_net, column_net)] = runs.get((row_net, column_net), 0.0) + run
    return max(runs.values(), default=0.0)


def _fan_crossing_angle(result):
    """Our own: the least angle (degrees) at which a Row trace's centre line below the field (a fan; the stack turned so
    the tails point down) crosses a Column trace's centre line, or ``None`` without a crossing."""

    def segments(board):
        convert = _stack_down(board)
        answer = []
        for route in board["layers"]["top_copper"]["routes"]:
            points = [convert(point) for point in route["points"]]
            answer.extend((a, b) for a, b in zip(points, points[1:]) if math.dist(a, b) > 1e-9)
        return answer

    def side(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

    bottom = _field_bottom(result["boards"]["row"])  # the field's bottom edge, tails down in the stack
    smallest = None
    columns = segments(result["boards"]["column"])
    for a, b in segments(result["boards"]["row"]):
        if max(a[1], b[1]) > bottom + EPSILON:
            continue
        for c, d in columns:
            if side(a, b, c) * side(a, b, d) < 0 and side(c, d, a) * side(c, d, b) < 0:
                u, v = (b[0] - a[0], b[1] - a[1]), (d[0] - c[0], d[1] - c[1])
                cosine = abs(u[0] * v[0] + u[1] * v[1]) / (math.sqrt(u[0] ** 2 + u[1] ** 2) * math.sqrt(v[0] ** 2 + v[1] ** 2))
                angle = math.degrees(math.acos(min(1.0, cosine)))
                smallest = angle if smallest is None else min(smallest, angle)
    return smallest


def _funnel(row) -> tuple:
    """Our own, with both: ``(midway between the two innermost lanes' rays just below the field, midway between their
    contacts)``, tails down; the near lanes come first in the contact order."""

    paths, order = _net_paths(row), row["tail"]["row_contact_order"]
    level = min(level[1] for level in _row_levels(row)) - 0.1
    inner = len([net for net in order if int(net[4:]) % 2 == 1]) - 1
    rays = [_x_at(paths[net], level) for net in order[inner: inner + 2]]
    contacts = [paths[net][0][0] for net in order[inner: inner + 2]]
    return (rays[0] + rays[1]) / 2, (contacts[0] + contacts[1]) / 2


def _band_side(row) -> int:
    """Our own, one side: the side of the field where the band runs, tail down (-1 west, +1 east): where every lane leaves
    its electrode (its route's end against the electrode's centre).  Not where a lane runs below the field: on a field
    receding on the band's side the lanes follow it inward, ROW_01's past the tail's centre."""

    turn = _down(row)
    sides = set()
    for net, path in _net_paths(row).items():
        box = _rows(row)[net]
        centre = turn(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2))[0]
        sides.add(-1 if path[-1][0] < centre else 1)
    if len(sides) != 1:
        raise AssertionError(f"the lanes leave their electrodes on both sides: {sorted(sides)}")
    return sides.pop()


def _contact_problems(result) -> list:
    """Our own: the Row tail's contacts against diagonal-bus/10's rule.  By position from the tail's canonical left (tail
    down, as engine.layout numbers them) the rows take positions 1..R in the contact order (folded with both), a reader
    tail's others are unconnected; one-sided with a reader tail, the rows' contacts lie at the tail's end beside the band
    (the side where the lanes leave their electrodes, :func:`_band_side`), or at its far end where mirrored.  Lists what
    does not hold."""

    row = result["boards"]["row"]
    turn = _down(row)
    pads = sorted(row["layers"]["top_copper"]["pads"], key=lambda pad: pad["position"])
    order = row["tail"]["row_contact_order"]
    problems = []
    if [pad["net"] for pad in pads[: len(order)]] != order:
        problems.append(("order", [pad["net"] for pad in pads[: len(order)]], order))
    if any(pad["kind"] != "connector_nc_pad" for pad in pads[len(order):]):
        problems.append(("unconnected", [pad["net"] for pad in pads[len(order):]]))
    xs = [turn(((bounds(pad)[0] + bounds(pad)[2]) / 2, (bounds(pad)[1] + bounds(pad)[3]) / 2))[0] for pad in pads]
    if any(b - a < 0.5 - EPSILON for a, b in zip(xs, xs[1:])):
        problems.append(("positions", "not from the canonical left"))
    design = result["design"]
    if design["routing"]["row_sides"] != "both" and len(pads) > len(order):
        # The rows' contacts on the band's side of the unused ones, or (mirrored) on the other.
        at_band = ((xs[0] + xs[len(order) - 1]) / 2 - (xs[len(order)] + xs[-1]) / 2) * _band_side(row) > 0
        if at_band == _flipped(design):
            problems.append(("end", "mirrored, the rows' contacts at the band's end" if at_band else "the rows' contacts away from the band"))
    return problems


def _tail_overlap(result) -> float:
    """Our own: the stacked tails' overlap across them (tails down; 0 when the rectangles do not meet)."""

    row_tail, column_tail = _tails_down(result)
    if min(row_tail[3], column_tail[3]) <= max(row_tail[1], column_tail[1]):
        return 0.0
    return max(0.0, min(row_tail[2], column_tail[2]) - max(row_tail[0], column_tail[0]))


def _half(value) -> int:
    """A coordinate in half layout-grid steps (the stack frame's centre may lie half a step off the grid)."""

    return int(round(float(value) * 2_000_000))


def _field_bottom(board) -> float:
    """Our own: the taxel field's bottom edge (the active region's edge toward the tails), tails down in the stack
    frame (whose origin is the field's centre)."""

    region = board["grid_registration"]["active_region"]
    return -(region["height"] if board["tail"]["side"] in ("bottom", "top") else region["width"]) / 2


def _shared_level(board) -> float:
    """Our own: the level, tails down in the stack frame, down to which the boards share one outline (diagonal-bus/8):
    the board's tail root, where its tail leaves the shared body's bottom edge (both boards' tails root there)."""

    convert, tail = _stack_down(board), board["tail"]["bounds"]
    corners = [convert(corner) for corner in ((tail["x"], tail["y"]), (tail["x"] + tail["width"], tail["y"] + tail["height"]))]
    return max(corner[1] for corner in corners)


def _shared_depth(board) -> float:
    """Our own: how far below the taxel field the boards share one outline (the tails' roots)."""

    return _field_bottom(board) - _shared_level(board)


def _stack_copper(board) -> str:
    """Our own: a digest of the board's copper, coverlay openings and stiffeners in the stack frame (half grid steps)."""

    turn = _stack_down(board)
    copper = board["layers"]["top_copper"]

    def points(items):
        return [[_half(c) for c in turn(point)] for point in items]

    def box(item):
        x0, y0, x1, y1 = bounds(item)
        corners = [turn(corner) for corner in ((x0, y0), (x1, y1))]
        return [_half(min(c[0] for c in corners)), _half(min(c[1] for c in corners)), _half(max(c[0] for c in corners)), _half(max(c[1] for c in corners))]

    items = [["route", route["net"], route["segment"], route["width_mm"], points(route["points"])] for route in copper["routes"]]
    items += [[kind, item["net"], item["kind"], box(item)] for kind in ("electrodes", "pads") for item in copper[kind]]
    items += [["opening", item["kind"], item.get("net"), points(item["points"]) if "points" in item else box(item)]
              for item in board["layers"]["top_coverlay_openings"]]
    items += [["stiffener", points(item["points"])] for item in board["layers"]["bottom_stiffener"]]
    items.sort(key=lambda item: json.dumps(item))
    return hashlib.sha256(json.dumps(items, separators=(",", ":")).encode("ascii")).hexdigest()


def _outline_below(board, depth: float) -> str:
    """Our own: a digest of the outline's vertices more than ``depth`` below the shared level (stack frame, tails down;
    a vertex within a grid step of that depth counts as above it)."""

    turn = _stack_down(board)
    level = _shared_level(board)
    below = sorted([_half(x), _half(y)] for x, y in (turn(point) for point in board["outline"]["points"]) if y < level - depth - EPSILON)
    return hashlib.sha256(json.dumps(below, separators=(",", ":")).encode("ascii")).hexdigest()


def _clip_above(ring, level: float) -> list:
    """Our own: the part of a ring above the height ``level`` (a vertex within a nanometre of it, or an edge lying on
    it, counts as below), cut along the level."""

    clipped = []
    for a, b in edges(ring):
        inside_a, inside_b = a[1] > level + 1e-9, b[1] > level + 1e-9
        if inside_a:
            clipped.append(list(a))
        if inside_a != inside_b:
            t = (level - a[1]) / (b[1] - a[1])
            clipped.append([a[0] + (b[0] - a[0]) * t, level])
    return clipped


def _shared_problems(result) -> list:
    """Our own: where the two outlines differ over the field in the stack (tails down, above F's bottom): the vertices
    of either outline's part there that the other's lacks (half grid steps), and a difference of their areas."""

    row, column = result["boards"]["row"], result["boards"]["column"]
    level = _shared_level(row)
    parts = {}
    for key, board in (("row", row), ("column", column)):
        turn = _stack_down(board)
        parts[key] = _clip_above([turn(point) for point in board["outline"]["points"]], level)
    found = sorted({(_half(x), _half(y)) for x, y in parts["row"]} ^ {(_half(x), _half(y)) for x, y in parts["column"]})[:5]
    areas = [abs(math.fsum(p[0] * q[1] - q[0] * p[1] for p, q in edges(part))) / 2 for part in parts.values()]
    if abs(areas[0] - areas[1]) > 1e-6:
        found.append(("area", areas[0], areas[1]))
    return found


# Regular outlines (diagonal-bus/5): no vertex of either outline outside its fillets and its tail turns by less than this
# (degrees); the fillets are the profile's radius and its halvings (the rolling circle halves the radius where it does
# not fit).
REGULAR_TURN = 5.0
FILLET_RADII = tuple(0.5 / 2 ** k for k in range(6))
# The tails' tip corners are convex arcs of this radius (the profile's tail_tip_corner_radius_mm): their vertices, within
# it of the tail's tip edge, turn by the arc step and are no flat vertices.
TIP_RADIUS = 0.3


def _circumradius(a, b, c) -> float:
    cross = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    sides = math.dist(a, b) * math.dist(b, c) * math.dist(c, a)
    return math.inf if cross == 0.0 else sides / (2 * cross)


def _fillet_flags(ring, level: float = -math.inf) -> list:
    """Our own: per vertex of a ring, whether it lies on a concave fillet of a fillet radius: three consecutive vertices
    around a concave one on such a circle (within 2 %), a single-step arc (a concave end turning by asin(chord / 2r) to
    its partner: tangent there, and the partner, a convex vertex the arc touches), or a concave vertex next to an arc
    vertex (a touch point of an arc the next fillet cut short or absorbed).  On and below the height ``level`` (the shared
    level, where a board's own outline leaves the shared one) a single-step arc's partner is on it only where it turns as
    its other tangent end does, or by REGULAR_TURN or more: a join's fillet that absorbed a step's convex corner (a side
    reaching the level a few micrometres outside a tail's edge and stepping back) leaves that vertex flat."""

    count = len(ring)
    turns = [math.radians(turn) for turn in turns_degrees(ring)]  # positive: convex
    on_arc = [False] * count
    for index in range(count):
        a, b, c = ring[index - 1], ring[index], ring[(index + 1) % count]
        if turns[index] < 0 and any(abs(_circumradius(a, b, c) - radius) <= 0.02 * radius for radius in FILLET_RADII):
            on_arc[index - 1] = on_arc[index] = on_arc[(index + 1) % count] = True
    flags = list(on_arc)
    for index in range(count):
        if turns[index] >= 0:
            continue
        shortest = min(math.dist(ring[index], ring[index - 1]), math.dist(ring[index], ring[(index + 1) % count]))
        tolerance = 2e-6 / shortest + 1e-5  # the turn of a vertex on the layout grid
        for other in ((index - 1) % count, (index + 1) % count):
            chord = math.dist(ring[index], ring[other])
            if any(chord < 2 * radius and abs(-turns[index] - math.asin(chord / (2 * radius))) <= tolerance for radius in FILLET_RADII):
                flags[index] = True
                flags[other] = (flags[other] or ring[other][1] > level + EPSILON or abs(turns[other] - turns[index]) <= tolerance
                                or abs(turns[other]) >= math.radians(REGULAR_TURN))
        if on_arc[index - 1] or on_arc[(index + 1) % count]:
            flags[index] = True
    return flags


def _flat_vertices(board, low: float) -> tuple:
    """Our own: a board's vertices (stack frame, tails down) above the height ``low`` that turn by less than
    REGULAR_TURN and lie on no fillet, ``[(spot, above the shared level, (x, y, turn))]``, and the spots (half grid
    steps) of its fillets' vertices.  A vertex on the shared level within a grid step of the straight line through its
    neighbours is no corner (where a board leaves the shared outline on a straight side) and is taken out first."""

    turn, level = _stack_down(board), _shared_level(board)
    ring = [turn(point) for point in board["outline"]["points"]]
    ring = [point for index, point in enumerate(ring)
            if abs(point[1] - level) > EPSILON or point_segment_distance(point, ring[index - 1], ring[(index + 1) % len(ring)]) > EPSILON]
    flat, fillets = [], set()
    for point, angle, on_fillet in zip(ring, turns_degrees(ring), _fillet_flags(ring, level)):
        spot = (_half(point[0]), _half(point[1]))
        if on_fillet:
            fillets.add(spot)
        elif point[1] > low + EPSILON and abs(angle) < REGULAR_TURN:
            flat.append((spot, point[1] > level + EPSILON, (round(point[0], 6), round(point[1], 6), round(angle, 4))))
    return flat, fillets


def _irregular(result) -> list:
    """Our own: the vertices of either outline (in the stack frame, tails down) above its tail's tip corners (TIP_RADIUS
    above its tip edge) that turn by less than REGULAR_TURN and lie on no fillet (:func:`_flat_vertices`): ``(board, x,
    y, turn)``, those on and below the shared level among them (where a board leaves the shared outline: its joins and
    its tail).  A vertex above the shared level is on both outlines, and lies on a fillet where either shows it.  A vertex
    on the level where the other board's outline runs on below it (the shared side flush with that board's tail) starts
    a step in to this board's own narrower tail: a real step, however narrow (two tails a few micrometres apart), whose
    fillet may take its corner."""

    found = {key: _flat_vertices(result["boards"][key], tail[1] + TIP_RADIUS) for key, tail in zip(("row", "column"), _tails_down(result))}
    fillets = found["row"][1] | found["column"][1]
    level = _shared_level(result["boards"]["row"])
    rings = {key: _stack_ring(result["boards"][key]) for key in ("row", "column")}

    def step(key, where) -> bool:
        other = rings["column" if key == "row" else "row"]
        return abs(where[1] - level) <= EPSILON and any(
            min(a[1], b[1]) < level - EPSILON and point_segment_distance(where[:2], a, b) <= EPSILON for a, b in edges(other))

    return [(key, *where) for key in ("row", "column") for spot, above, where in found[key][0]
            if not (above and spot in fillets) and not step(key, where)]


def _hull(points) -> list:
    """Our own convex hull (monotone chain, counter-clockwise, collinear points dropped)."""

    points = sorted(set((round(x, 9), round(y, 9)) for x, y in points))

    def half(ordered):
        chain = []
        for p in ordered:
            while len(chain) >= 2 and ((chain[-1][0] - chain[-2][0]) * (p[1] - chain[-1][1]) - (chain[-1][1] - chain[-2][1]) * (p[0] - chain[-1][0])) <= 1e-12:
                chain.pop()
            chain.append(p)
        return chain

    return half(points)[:-1] + half(points[::-1])[:-1]


def _field_corners(board) -> list:
    """Our own: F (the board's active outline, P, grown by the field margin as a box, slab by slab) in the board's frame,
    as its y-slabs ``(low, high, x0, x1)`` bottom to top (the boxes' union, neighbouring equal slabs merged)."""

    polygon = board["grid_registration"]["active_outline"]
    levels = sorted({y for _, y in polygon})
    boxes = []
    for low, high in zip(levels, levels[1:]):
        middle = (low + high) / 2
        xs = [a[0] + (middle - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) for a, b in edges(polygon) if (a[1] > middle) != (b[1] > middle)]
        boxes.append((low - MARGIN, high + MARGIN, min(xs) - MARGIN, max(xs) + MARGIN))
    cuts = sorted({value for box in boxes for value in box[:2]})
    slabs = []
    for low, high in zip(cuts, cuts[1:]):
        over = [box for box in boxes if box[0] <= low + 1e-9 and box[1] >= high - 1e-9]
        slab = (low, high, min(box[2] for box in over), max(box[3] for box in over))
        if slabs and slabs[-1][1] == low and slabs[-1][2:] == slab[2:]:
            slabs[-1] = (slabs[-1][0], high, slab[2], slab[3])
        else:
            slabs.append(slab)
    return slabs


def _notch_pockets(board, pitch: float) -> list:
    """Our own: F's shallow notches, the pockets between consecutive corners of F's convex hull on either side whose
    staircase lies no deeper inside the hull's edge than a step of two cells (2 p / sqrt 5): ``(u, v, staircase between)``
    per pocket (the ones the outline must cross on the hull's edge, diagonal-bus/6)."""

    slabs = _field_corners(board)
    hull = _hull([(x, y) for low, high, x0, x1 in slabs for x in (x0, x1) for y in (low, high)])
    pockets = []
    depth = 2 * pitch / math.sqrt(5)
    for column in (2, 3):
        stairs = []
        for slab in reversed(slabs):
            for point in ((round(slab[column], 9), round(slab[1], 9)), (round(slab[column], 9), round(slab[0], 9))):
                if not stairs or stairs[-1] != point:
                    stairs.append(point)
        on_hull = [index for index, point in enumerate(stairs) if point in hull]
        for first, second in zip(on_hull, on_hull[1:]):
            u, v, between = stairs[first], stairs[second], stairs[first + 1:second]
            length = math.hypot(v[0] - u[0], v[1] - u[1])
            if between and length > 0 and max(abs((v[0] - u[0]) * (p[1] - u[1]) - (v[1] - u[1]) * (p[0] - u[0])) / length for p in between) <= depth + 1e-6:
                pockets.append((u, v, between))
    return pockets


def _staircase_problems(result) -> list:
    """Our own (P5-diagonal-bus.md section 16): a masked field's shallow notches (:func:`_notch_pockets`) are crossed on the
    hull's edge, not on a staircase: per board, the edge's ends and middle lie on or inside the outline, and no outline
    vertex lies inside the pocket (by more than a grid step)."""

    found = []
    pitch = max(result["design"]["matrix"]["pitch_x_mm"], result["design"]["matrix"]["pitch_y_mm"])
    for key, board in result["boards"].items():
        ring = board["outline"]["points"]
        for u, v, between in _notch_pockets(board, pitch):
            middle = ((u[0] + v[0]) / 2, (u[1] + v[1]) / 2)
            for p in (u, v, middle):
                if not point_in_polygon(p, ring) and min(point_segment_distance(p, a, b) for a, b in edges(ring)) > EPSILON:
                    found.append((key, "notch's chamfer outside the outline", p))
            pocket = [u, *between, v]
            for p in ring:
                if point_in_polygon(p, pocket) and min(point_segment_distance(p, a, b) for a, b in edges(pocket)) > EPSILON:
                    found.append((key, "outline vertex inside a notch", tuple(p)))
    return found[:5]


# Convex sides (diagonal-bus/9, P5-diagonal-bus.md section 24): a dent of a side from its tip corner down to its widest
# point is bridged by the side's hull where no deeper than a step of this many cells (2 p / sqrt 5).
CONVEX_STEP_CELLS = 2


def _convex_depth(design: dict) -> float:
    matrix = design["matrix"]
    return CONVEX_STEP_CELLS * max(matrix["pitch_x_mm"], matrix["pitch_y_mm"]) / math.sqrt(CONVEX_STEP_CELLS ** 2 + 1)


def _side_dents(ring, level: float, west: bool) -> tuple:
    """Our own: one side of a stack ring (tails down) from its tip corner down to its widest point above ``level``, its
    hull (the hull's corners, in order) and per dent between two corners of the hull ``(first, last, depth)``: the
    deepest point of the side between them inside the hull's edge.  ``(points, hull, dents)``, the east side mirrored."""

    points = _side_walk(ring, level, west)[0][:-1]  # its vertices above the level (the last point lies on it)
    least = min(x for x, _ in points)
    widest = next(k for k, point in enumerate(points) if point[0] <= least + 1e-6)
    stretch = points[:widest + 1]
    hull: list = []
    for k, point in enumerate(stretch):
        while len(hull) >= 2:
            a, b = stretch[hull[-2]], stretch[hull[-1]]
            if (b[0] - a[0]) * (point[1] - b[1]) - (b[1] - a[1]) * (point[0] - b[0]) <= 0.0:
                hull.pop()
            else:
                break
        hull.append(k)
    dents = []
    for u, v in zip(hull, hull[1:]):
        if v > u + 1:
            a, b = stretch[u], stretch[v]
            length = math.dist(a, b)
            depth = max(((b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])) / length for q in stretch[u + 1:v])
            dents.append((u, v, depth))
    return stretch, hull, dents


# The side without the bus (diagonal-bus/11, P5-diagonal-bus.md section 27.8): a dent of its flank deeper than this (mm) is
# a notch; shallower ones are the fillets' own (a rolling circle absorbing a convex corner next to a concave one leaves
# a few micrometres; the video's notches are 0.19-0.53 mm deep, a ledge of the margin and half a cell).
FLANK_DENT_MM = 0.02
# A concave run at the field's outline corner is that corner's own fillet where its edges in and out meet within this (mm)
# of F's bottom (the side bending out there to a wider tail; the lines made regular move a few micrometres).
FLANK_CORNER_MM = 0.05


def _flank_problems(result, least: float = FLANK_DENT_MM) -> list:
    """Our own (diagonal-bus/11, P5-diagonal-bus.md section 27.8): with one side, the shared outline's side without the
    bus (stack frame, tails down) turns in below the field's outline corner (its outermost vertex on F's bottom, or where
    it runs straight on past it) on no notch: the stretch from that corner (past its own fillet, a side bending out
    there to a wider tail: the concave run's edges meet on F's bottom) down to the tail root's fillet (the vertices back
    from the side's point on the level that do not turn convex) has no dent from the corner deeper than ``least`` inside
    the stretch's hull, but where bridging it would leave the corner turning by less than REGULAR_TURN (a tail a
    fraction of a millimetre wider than F: the side all but straight there).  The video's notch (section 27.8): the
    Column fan-out's body corner, its ledge in to the outermost route and that route's turn into the V, beside the field
    on the side without the bus.  Dents farther down (a step where the V meets the lanes' fans) are the residuals of
    P5-diagonal-bus.md section 27.8, counted by the harness, not checked here."""

    sides = result["design"]["routing"].get("row_sides")
    if sides not in ("left", "right"):
        return []
    row = result["boards"]["row"]
    level, bottom, radius = _shared_level(row), _field_bottom(row) - MARGIN, FILLET_RADII[0]
    points, after, _ = _side_walk(_stack_ring(row), level, sides == "right")  # the side without the bus, as a west side
    count = len(points)
    turns = [0.0] + [_turn_degrees((b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1]))
                     for a, b, c in zip(points, points[1:], points[2:] + [after])]
    on = [k for k, point in enumerate(points) if abs(point[1] - bottom) <= EPSILON]
    if on:
        corner = min(on, key=lambda k: (points[k][0], -k))
        start, first = points[corner], corner + 1
        arriving = (points[corner][0] - points[corner - 1][0], points[corner][1] - points[corner - 1][1])
    else:
        first = next(k for k, point in enumerate(points) if point[1] < bottom)
        a, b = points[first - 1], points[first]
        start, arriving = (a[0] + (b[0] - a[0]) * (bottom - a[1]) / (b[1] - a[1]), bottom), (b[0] - a[0], b[1] - a[1])
    # Bending out at the corner itself, the side's concave run there is that corner's own fillet: the run's edges in and
    # out meet on F's bottom (within FLANK_CORNER_MM).
    near = next(k for k, point in enumerate(points) if point[1] <= bottom + radius + EPSILON)
    if turns[near] < -1e-6 and (not on or near <= corner):
        k = near
        while k < count - 1 and turns[k] <= 1e-6:
            k += 1
        (a, b), (c, d) = (points[near - 1], points[near]), (points[k - 1], points[k])
        across = (b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])
        if across != 0.0:
            t = ((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0])) / across
            if abs(a[1] + t * (b[1] - a[1]) - bottom) <= FLANK_CORNER_MM:
                first = max(first, k)
    end = count - 2
    while end >= first and turns[end] <= 1e-6:
        end -= 1
    if not any(turns[k] < -1e-6 for k in range(first, end)):
        return []
    stretch = [start] + points[first:end + 1]
    hull: list = []
    for k, point in enumerate(stretch):
        while len(hull) >= 2:
            a, b = stretch[hull[-2]], stretch[hull[-1]]
            if (b[0] - a[0]) * (point[1] - b[1]) - (b[1] - a[1]) * (point[0] - b[0]) <= 0.0:
                hull.pop()
            else:
                break
        hull.append(k)
    found = []
    for u, v in zip(hull[:2], hull[1:2]):  # the dent from the corner
        if v == u + 1:
            continue
        a, b = stretch[u], stretch[v]
        direction = (b[0] - a[0], b[1] - a[1])
        depth = max((direction[0] * (q[1] - a[1]) - direction[1] * (q[0] - a[0])) / math.hypot(*direction) for q in stretch[u + 1:v])
        if depth <= max(least, EPSILON):
            continue
        if abs(_turn_degrees(arriving, direction)) < REGULAR_TURN:
            continue
        found.append(("east" if sides == "left" else "west", "a notch below the field's outline corner on the side without the bus", round(depth, 6), a, b))
    return found


def _convex_problems(result) -> list:
    """Our own (diagonal-bus/9): on each side of the shared outline (stack frame, tails down) from the tip corner down to
    the widest point, no dent (a run inside the hull of the side's vertices) at most a step of CONVEX_STEP_CELLS cells
    deep, but where bridging it would leave the tip corner or the widest point turning by less than REGULAR_TURN (the
    hull's edge nearly along the top edge or the next edge below); with one side, the side without the bus convex from
    the field's outline corner down to the tail root (diagonal-bus/11, :func:`_flank_problems`)."""

    row = result["boards"]["row"]
    level = _shared_level(row)
    bound = _convex_depth(result["design"])
    found = []
    ring = _stack_ring(row)
    for west in (True, False):
        stretch, hull, dents = _side_dents(ring, level, west)
        points, after, edge_end = _side_walk(ring, level, west)
        for u, v, depth in dents:
            if depth > bound + 1e-6:
                continue
            a, b = stretch[u], stretch[v]
            direction = (b[0] - a[0], b[1] - a[1])
            if u == 0:
                top_edge = (a[0] - edge_end[0], a[1] - edge_end[1])
                if abs(_turn_degrees(top_edge, direction)) < REGULAR_TURN:
                    continue
            if v == len(stretch) - 1:
                following = points[v + 1] if v + 1 < len(points) else after
                if abs(_turn_degrees(direction, (following[0] - b[0], following[1] - b[1]))) < REGULAR_TURN:
                    continue
            found.append(("west" if west else "east", "a dent no deeper than the bound kept", round(depth, 6), a, b))
    found += _flank_problems(result)
    return found[:5]


def _check_clean(test: unittest.TestCase, result: dict) -> None:
    """Every DRC record, strict record 14, route-route at the trace space, the registration with every stack key (the
    fans' crossings at 5 degrees or more), and our own: at most two bends per Row and per Column trace below its field,
    straight down into the tail after them, no trace over the other board's field window, Row-on-Column runs of
    RUN_BOUND_MM at most off the stacked contact columns, the tails stacked on one side, both centred on the field (the
    Row tail within a nanometre in every side mode, :func:`_contact_problems`), and both outlines regular
    (:func:`_irregular`)."""

    test.assertTrue(result["ok"], [issue["code"] + " " + issue["message"][:160] for issue in result["validation"]["errors"]][:3])
    design = result["design"]
    space = design["routing"]["trace_space_mm"]
    for key, board in result["boards"].items():
        checks = board["verification"]["checks"]
        test.assertTrue(board["verification"]["all_checks_passed"], [name for name, record in checks.items() if not record["passed"]])
        strict = checks["coverlay_opening_to_trace"]
        test.assertEqual(strict.get("semantics"), "strict", key)
        test.assertGreaterEqual(strict["measured_mm"], 0.15 - EPSILON, key)
        test.assertIn("taxel_mask", board["grid_registration"])
        test.assertEqual(board["construction"]["mask_class"], {"row": "diagonal", "column": "straight"})
    route_route = result["boards"]["row"]["verification"]["checks"]["route_route_clearance"]["measured_mm"]
    test.assertTrue(route_route is None or route_route >= space - EPSILON, route_route)  # None: one row, no pair
    record = result["boards"]["row"]["verification"]["registration"]
    test.assertTrue(record["passed"])
    test.assertLessEqual(set(STACK_KEYS), set(record))
    test.assertEqual((record["trace_over_other_electrode_count"], record["trace_over_other_window_count"]), (0, 0))
    for key in GONE_KEYS:
        test.assertNotIn(key, record)
    # The fans cross the Column copper at the entry-angle guard or more (our own, on the centre lines below the field;
    # beside it a band may cross a raised Column stub at any angle: the boards overlap there, reported only); runs of a
    # Row net on a Column net are reported.
    test.assertTrue(record["trace_crossing_min_angle_deg"] is None or record["trace_crossing_min_angle_deg"] > 0.0)
    fans = _fan_crossing_angle(result)
    test.assertTrue(fans is None or fans >= FAN_CROSSING_DEG - EPSILON, fans)
    test.assertGreaterEqual(record["trace_overlap_mm"], 0.0)
    # Our own: the bends below each field, the window, the runs above the tail roots.
    for key in ("row", "column"):
        for net, (bends, slanted, into) in _below_field(result["boards"][key]).items():
            test.assertLessEqual(bends, 2, (key, net))
            test.assertLessEqual(slanted, 1, (key, net))
            test.assertTrue(into, (key, net))  # straight down into the tail after the last bend
    test.assertEqual(_window_problems(result), [])
    test.assertLessEqual(_runs_off_the_contact_columns(result), RUN_BOUND_MM)
    # The stacked tails: one exit side, both centred on the field (the stack's origin; diagonal-bus/10, the user's request
    # of the plan's section 27: the tails within the sensor's width), the Row tail in every side mode within a nanometre
    # (the layout grid's step: its corner rounded to it), its contacts the positions 1..R from its canonical left; their
    # overlap, the narrower tail's width.
    row, column = result["boards"]["row"], result["boards"]["column"]
    test.assertEqual(row["tail"]["side"], column["tail"]["side"])
    test.assertIs(record["tail_sides_match"], True)
    row_tail, column_tail = _tails_down(result)
    test.assertAlmostEqual((column_tail[0] + column_tail[2]) / 2, 0.0, delta=EPSILON)
    test.assertAlmostEqual((row_tail[0] + row_tail[2]) / 2, 0.0, delta=CENTRED_NM)
    test.assertAlmostEqual(record["tail_overlap_width_mm"], _tail_overlap(result), delta=EPSILON)
    test.assertAlmostEqual(_tail_overlap(result), min(row_tail[2] - row_tail[0], column_tail[2] - column_tail[0]), delta=2 * CENTRED_NM)
    bus = row["construction"]["row_bus"]
    test.assertEqual(bus["tails"], "stacked")
    test.assertEqual(bus["tail_position"], "centred")
    test.assertEqual(_contact_problems(result), [])
    test.assertEqual(result["manifest"]["row_bus"], ROW_BUS_VERSION)
    # One outline down to the tail roots (diagonal-bus/8): both tails leave the shared body's bottom edge, below the
    # field's bottom; by our own predicate, and its records; both outlines regular; a masked field's notches crossed on
    # F's hull (diagonal-bus/6).
    row_tail, column_tail = _tails_down(result)
    test.assertAlmostEqual(row_tail[3], column_tail[3], delta=EPSILON)
    depth = _shared_depth(row)
    test.assertGreater(depth, MARGIN)
    test.assertEqual(_shared_problems(result), [])
    test.assertEqual(_irregular(result), [])
    test.assertEqual(_convex_problems(result), [])
    if "mask" in design["matrix"]:
        test.assertEqual(_staircase_problems(result), [])
    test.assertAlmostEqual(bus["shared_outline_below_field_mm"], depth, delta=EPSILON)
    test.assertEqual(column["construction"]["shared_outline_below_field_mm"], bus["shared_outline_below_field_mm"])
    test.assertEqual((record["outlines_coincide_over_field"], record["shared_outline_below_field_mm"], record["outline_deviation_over_field_mm"]),
                     (True, bus["shared_outline_below_field_mm"], 0.0))
    # The record's relative narrow tip and flat lanes, by our own predicates.
    test.assertEqual(bus["tip_is_narrowest_relative"], _narrowest_relative(row))
    test.assertEqual(bus["flat_lane_rows"], _flat_rows(row, design))


# --------------------------------------------------------------------------
# The named corpus.
# --------------------------------------------------------------------------


class NamedCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = {key: generate_design(_named(*key)) for key in PINNED}
        cls.plain = {key: _plain(_named(*key)) for key in PINNED}

    def test_every_build_is_clean(self) -> None:
        for key, result in sorted(self.results.items()):
            with self.subTest(case=key):
                _check_clean(self, result)
                route_route = result["boards"]["row"]["verification"]["checks"]["route_route_clearance"]["measured_mm"]
                # The lanes run at the bundle pitch: exactly on axis-parallel runs, plus the 2 nm slant allowance on slants.
                self.assertAlmostEqual(route_route, 0.1016, delta=2.5e-6, msg="the lanes run at the bundle pitch")

    def test_pinned_values(self) -> None:
        for key, expected in sorted(PINNED.items()):
            with self.subTest(case=key):
                measured = _measure(self.results[key])
                for index, (got, want) in enumerate(zip(measured, expected)):
                    if isinstance(want, bool):
                        self.assertEqual(got, want, index)
                    else:
                        self.assertAlmostEqual(got, want, delta=0.01, msg=index)

    def test_the_bands_and_the_roots_against_the_first_construction(self) -> None:
        # Beside a field that does not recede the bands are diagonal-bus/1's (its lanes, turned down on the field's bottom
        # edge): at every row's centre and bottom the outline lies within 0.15 mm of its (tests/fixtures/diagonal_bus_v1_bands.json),
        # the tip no narrower, and at the field's bottom edge the overhang no smaller.  Nowhere does it lie farther out but
        # where the shared outline takes the Column board's own body (the disk's lower corners, 20 mm beyond its bottom
        # rows); beside the disk, which recedes below its equator, the lanes follow the field inward
        # (test_the_lanes_follow_a_receding_field).  With both the Row root is never more than 1.0 mm deeper than its, here
        # 6.3-13.2 mm shallower; and never deeper than diagonal-bus/2's but by the entry-angle guard's allowance and, one-
        # sided, the centred Row tail's cost (V2_ALLOWANCE).
        for key, (west, east, root) in sorted(V1.items()):
            with self.subTest(case=key):
                row = self.results[key]["boards"]["row"]
                got = _edge_overhang(row)
                for value, want, receding in zip(got, (west, east), _receding(row)):
                    if not receding:
                        self.assertGreaterEqual(value - want, -BAND_TOLERANCE, got)
                self.assertEqual(_receding(row), (key[0] == "disk", key[0] == "disk"))
                _check_bands(self, self.plain[key], V1_BANDS[f"{key[0]}|{key[1]}"])
                measured = _measure(self.results[key])[2]
                if key[1] == "both":
                    self.assertLess(measured, root - 6.0)
                self.assertLessEqual(measured, V2_ROOTS[key] + V2_ALLOWANCE.get(key, 0.001))

    def test_the_bus_record_agrees_with_the_outline(self) -> None:
        for key, result in sorted(self.results.items()):
            with self.subTest(case=key):
                row, column = result["boards"]["row"], result["boards"]["column"]
                bus = row["construction"]["row_bus"]
                measured = _measure(result)
                design = result["design"]
                near, far = (measured[9], measured[8]) if _flipped(design) else (measured[8], measured[9])
                self.assertAlmostEqual(bus["tip_width_mm"], measured[0], delta=EPSILON)
                self.assertAlmostEqual(bus["band_mm"]["near"], near, delta=EPSILON)
                self.assertAlmostEqual(bus["band_mm"]["far"], far, delta=EPSILON)
                self.assertAlmostEqual(bus["widest_mm"], measured[1], delta=EPSILON)
                tip = _rows(row)["ROW_01"]
                field = tip[2] - tip[0] - 2 * OVERHANG + 2 * MARGIN
                self.assertAlmostEqual(bus["tip_excess_mm"], measured[0] - field, delta=EPSILON)
                self.assertEqual(bus["tip_is_narrowest_relative"], _narrowest_relative(row))
                both = key[1] == "both"
                self.assertEqual(bus["kind"], ROW_BUS_VERSION)
                self.assertEqual((bus["sides"], bus["split"]), (key[1], "alternate" if both else None))
                self.assertEqual(bus["near_side"], "right" if both else key[1])
                self.assertEqual(bus["contact_order"], row["tail"]["row_contact_order"])
                self.assertEqual(bus["tail_position"], "centred")
                self.assertEqual(bus["lane_angle_deg"]["far"] is None, not both)
                for side in ("near", "far"):
                    angles = bus["lane_angle_deg"][side]
                    if angles is not None:
                        self.assertLessEqual(0.0, angles[0])
                        self.assertLessEqual(angles[0], angles[1])
                        self.assertLessEqual(angles[1], 90.0)
                # The fans: one run per side and way, every row in one, at a cap of 60-85 degrees off the Column entry angle.
                rows = sorted(k for fan in bus["fans"] for k in fan["rows"])
                self.assertEqual(len(rows), len(set(rows)))
                entry = column["construction"]["entry_taper_angle_deg"]
                for fan in bus["fans"]:
                    self.assertIn(fan["move"], ("west", "east"))
                    self.assertTrue(60.0 <= fan["angle_deg"] <= 85.0 and abs(fan["angle_deg"] - entry) > 5.0, (fan["angle_deg"], entry))
                    self.assertGreater(fan["height_mm"], 0.0)
                self.assertEqual(bus["tails"], "stacked")
                # The board drops the straight channel's records, diagonal-bus/1's and diagonal-bus/2's (the Column tail
                # beside the Row tail); the Column board is the straight one.
                for absent in ("channel_width_mm", "merger_taper_angle_deg", "merger_height_mm", "bend_stagger_mm"):
                    self.assertNotIn(absent, row["construction"])
                for absent in ("corridor_top_mm", "jog", "expansion", "column_tail", "column_tail_side", "column_tail_shift_mm", "column_neck_mm"):
                    self.assertNotIn(absent, bus)
                for absent in ("stub_drop_mm", "tail_shift_mm", "neck_mm"):
                    self.assertNotIn(absent, column["construction"])

    def test_the_funnel_and_the_tails(self) -> None:
        # diagonal-bus/10 (the plan's section 27): the Row tail centred on the field in every side mode, as the Column tail,
        # so the narrower tail lies wholly on the wider one (_check_clean).  With both the near and far contacts part on the
        # field's centre line, half a contact pitch east of it with 30 near rows and 29 far ones (the soft finger), and on
        # these symmetric fields midway between the innermost lanes (the funnel's V).  With one side the whole bundle fans
        # inward under the field in one run (no lane runs straight down into its contact).  Both leave on one side, and
        # each ends its own tail length below its root.
        for key, result in sorted(self.results.items()):
            with self.subTest(case=key):
                row, column = result["boards"]["row"], result["boards"]["column"]
                bus = row["construction"]["row_bus"]
                row_tail, column_tail = _tails_down(result)
                self.assertAlmostEqual((row_tail[0] + row_tail[2]) / 2, (column_tail[0] + column_tail[2]) / 2, delta=CENTRED_NM)
                overlap = _tail_overlap(result)
                self.assertAlmostEqual(overlap, min(row_tail[2] - row_tail[0], column_tail[2] - column_tail[0]), delta=2 * CENTRED_NM)
                if key[1] == "both":
                    rays, contacts = _funnel(row)
                    region = row["grid_registration"]["active_region"]
                    centre = _down(row)((region["x"] + region["width"] / 2, region["y"] + region["height"] / 2))[0]
                    rows = len(bus["near_rows"]) + len(bus["far_rows"])
                    self.assertAlmostEqual(contacts - centre, (len(bus["near_rows"]) - rows / 2) * 0.5, delta=CENTRED_NM)
                    if key[0] in ("rectangle", "soft finger"):
                        self.assertAlmostEqual(contacts, rays, delta=0.25 + 1e-5)
                else:
                    self.assertEqual([(fan["move"], len(fan["rows"])) for fan in bus["fans"]], [("east", len(bus["near_rows"]))])
                    self.assertTrue(all(bends == 2 for bends, _, _ in _below_field(row).values()))
                for board in (row, column):
                    bounds_ = board["tail"]["bounds"]
                    self.assertAlmostEqual(bounds_["height"], board["tail"]["length_mm"], delta=EPSILON)
                self.assertAlmostEqual(row["verification"]["registration"]["tail_overlap_width_mm"], overlap, delta=EPSILON)

    def test_the_two_sided_tip_is_the_rectangles(self) -> None:
        # The tip carries ROW_01's lane only: P's top row + 1.0 margin + 0.067 at 2 mm / 4 mil (the straight channel: 31.052);
        # the regular outline 1 micrometre wider (two flat vertices of the lane's start below the tip's corner merged), and
        # the straight sides 0.435 mm wider (diagonal-bus/7: each side one line from the tip corner down to F's bottom,
        # tangent to the band's long side there; the tip corners 0.14 and 0.24 mm out).
        for name in ("rectangle", "soft finger"):
            self.assertAlmostEqual(_measure(self.results[(name, "both")])[0], 11 * 2.0 + 1.4 + 1.0 + 0.067 + 0.435, delta=0.001)
            self.assertAlmostEqual(_measure(self.plain[(name, "both")])[0], 11 * 2.0 + 1.4 + 1.0 + 0.067, delta=0.001)
        # Below the field the boards overlap freely: the far fans cross the Column fan-out at any angle, reported only.
        record = self.results[("rectangle", "both")]["boards"]["row"]["verification"]["registration"]
        self.assertGreater(record["trace_crossing_count"], 0)
        self.assertLess(record["trace_crossing_min_angle_deg"], 89.9)
        self.assertTrue(record["passed"])

    def test_the_lanes_leave_on_a_slant_or_are_listed_flat(self) -> None:
        # A lane leaves its electrode's end on a slant (16.7 degrees from the vertical on the rectangle: toward the own
        # zone's outer-bottom corner, the bottom row's too, turned down on the field's bottom edge) unless the keep-out
        # of the rows below reaches its height, and construction.row_bus.flat_lane_rows lists exactly the rows with a band
        # segment beyond the 85-degree taper cap (our own predicate, _check_clean).  None on the named corpus: the
        # stacked Column copper is no keep-out, so the disk's rows below its equator no longer escape flat across the
        # raised Column stubs.
        for key, result in sorted(self.results.items()):
            with self.subTest(case=key):
                row = result["boards"]["row"]
                flat = row["construction"]["row_bus"]["flat_lane_rows"]
                self.assertEqual(flat, FLAT_ROWS.get(key, []))
                self.assertEqual(flat, _flat_rows(row, result["design"]))
                slopes = {}
                for route in row["layers"]["top_copper"]["routes"]:
                    if route["segment"] == "fanout":
                        end, before = route["points"][-1], route["points"][-2]
                        slopes[route["net"]] = math.degrees(math.atan2(abs(before[0] - end[0]), abs(before[1] - end[1])))
                self.assertLessEqual(slopes["ROW_01"], TAPER_CAP, "the tip's lane leaves on a slant")
                for net, slope in slopes.items():
                    if int(net[4:]) not in flat:
                        self.assertLessEqual(slope, TAPER_CAP, net)
                if key[0] == "rectangle":
                    self.assertEqual({round(slope, 3) for slope in slopes.values()}, {16.729})

    def test_the_lanes_follow_a_receding_field(self) -> None:
        # Our own: the Row traces beside the field keep within their bundle (the lanes of the larger side at the bundle
        # pitch) and STRAY_ALLOWANCE of a Row electrode on the whole named corpus: on the disk, which recedes below its
        # equator, the lanes follow it inward down to its bottom edge, nested at the bundle pitch (3.43, 5.49 and 4.81 mm
        # with both, left and right; diagonal-bus/4's first build 11.10, 12.81, 12.82), and turn into the funnel there.
        for key, result in sorted(self.results.items()):
            with self.subTest(case=key):
                row = result["boards"]["row"]
                bus = row["construction"]["row_bus"]
                lanes = max(len(bus["near_rows"]), len(bus["far_rows"] or []))
                self.assertLessEqual(_stray_from_field(row), lanes * 0.2032 + STRAY_ALLOWANCE)
                if key[0] == "disk":
                    self.assertLess(_stray_from_field(row), {"both": 3.5, "left": 5.5, "right": 4.9}[key[1]])


# --------------------------------------------------------------------------
# Sides and contact order.
# --------------------------------------------------------------------------


def _stack_ring(board) -> list:
    """A board's outline in the stack frame turned so the tails point down."""

    turn = _stack_down(board)
    return [turn(point) for point in board["outline"]["points"]]


def _stack_down(board):
    """The stack frame (seen from outside the stack) turned so the tails point down."""

    convert, turn = stack_frame(board), _down(board)
    return lambda point: turn(convert(point))


def _tails_down(result) -> tuple:
    """Both tails' rectangles in the stack frame turned so the tails point down."""

    answer = []
    for key in ("row", "column"):
        board = result["boards"][key]
        convert, tail = _stack_down(board), board["tail"]["bounds"]
        corners = [convert(corner) for corner in ((tail["x"], tail["y"]), (tail["x"] + tail["width"], tail["y"] + tail["height"]))]
        answer.append((min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners), max(c[1] for c in corners)))
    return tuple(answer)


def _leaving_sides(result) -> dict:
    """ROW_k -> 'left' or 'right': the end of its electrode its lane leaves, seen from outside the stack with the
    tails down."""

    row = result["boards"]["row"]
    convert = _stack_down(row)
    electrodes = {net: [convert(corner) for corner in ((box[0], box[1]), (box[2], box[3]))] for net, box in _rows(row).items()}
    answer = {}
    for route in row["layers"]["top_copper"]["routes"]:
        if route["segment"] != "fanout":
            continue
        end = convert(route["points"][-1])
        x0, x1 = sorted(corner[0] for corner in electrodes[route["net"]])
        answer[route["net"]] = "left" if abs(end[0] - x0) <= abs(end[0] - x1) else "right"
    return answer


class SideAndOrderTests(unittest.TestCase):
    def test_the_sides_are_seen_from_outside_the_stack(self) -> None:
        mask = [[3, 6], [2, 7], [1, 7], [1, 7], [2, 7], [3, 5]]
        for top in ("rows", "columns"):
            near = "right" if top == "rows" else "left"
            for sides in SIDES:
                with self.subTest(top=top, sides=sides):
                    result = generate_design(_request(6, 7, mask, sides=sides, top=top))
                    _check_clean(self, result)
                    leaving = _leaving_sides(result)
                    for k in range(1, 7):
                        expected = sides if sides != "both" else (near if k % 2 else ("left" if near == "right" else "right"))
                        self.assertEqual(leaving[f"ROW_{k:02d}"], expected, k)
                    # In every side mode the Row tail lies centred on the Column tail (diagonal-bus/10; under the band on
                    # its side before), the lanes on the side asked.
                    row_tail, column_tail = _tails_down(result)
                    bus = result["boards"]["row"]["construction"]["row_bus"]
                    self.assertAlmostEqual(row_tail[0] + row_tail[2], column_tail[0] + column_tail[2], delta=2 * CENTRED_NM)
                    if sides != "both":
                        self.assertEqual(bus["near_side"], sides)

    def test_the_tails_on_every_side(self) -> None:
        # Built tail down and turned with its boards (engine.layout.apply_tail_side): seen from outside the stack with
        # the tails down, the sides, the tails' order, the record and every stack key are those of bottom tails, and
        # the turned bundle exports (its read-backs pass).
        mask = [[3, 6], [2, 7], [1, 7], [1, 7], [2, 7], [3, 5]]
        for top in ("rows", "columns"):
            for sides in SIDES:
                bottom = generate_design(_request(6, 7, mask, sides=sides, top=top))
                for tail in ("top", "left", "right"):
                    with self.subTest(top=top, sides=sides, tail=tail):
                        request = _request(6, 7, mask, sides=sides, top=top)
                        request["tail"].update(row_side=tail, column_side=tail)
                        result = generate_design(request)
                        _check_clean(self, result)
                        self.assertEqual(result["boards"]["row"]["tail"]["side"], tail)
                        self.assertEqual(_leaving_sides(result), _leaving_sides(bottom))
                        for turned, upright in zip(_tails_down(result), _tails_down(bottom)):
                            for got, want in zip(turned, upright):
                                self.assertAlmostEqual(got, want, delta=EPSILON)
                        self.assertEqual(result["boards"]["row"]["construction"]["row_bus"], bottom["boards"]["row"]["construction"]["row_bus"])
                        record, expected = (item["boards"]["row"]["verification"]["registration"] for item in (result, bottom))
                        for key in STACK_KEYS:
                            if isinstance(expected[key], float):
                                self.assertAlmostEqual(record[key], expected[key], delta=EPSILON, msg=key)
                            else:
                                self.assertEqual(record[key], expected[key], key)
        request = _request(6, 7, mask, sides="both")
        request["tail"].update(row_side="left", column_side="left")
        result = generate_design(request)
        manifest = json.loads(_zip_member(build_exports(result)["project_review_bundle_zip"], "manifest.json"))
        entry = manifest["diagonal_row_bus"]
        self.assertEqual(entry["row_contact_order"], result["boards"]["row"]["tail"]["row_contact_order"])
        self.assertEqual(entry["construction"]["tails"], "stacked")
        for gone in ("column_stub_drop_mm", "column_tail_shift_mm", "column_neck_mm"):
            self.assertNotIn(gone, entry)

    def test_the_contact_order_folds_and_follows_the_pads(self) -> None:
        for sides, flipped in (("both", False), ("right", False), ("left", True)):
            for order in ("ascending", "descending"):
                with self.subTest(sides=sides, order=order):
                    request = _request(9, 5, sides=sides, pins=(12, None))
                    request["channel_order"] = {"rows": order, "columns": "ascending"}
                    result = generate_design(request)
                    _check_clean(self, result)
                    row = result["boards"]["row"]
                    if sides == "both":
                        expected = ["ROW_01", "ROW_03", "ROW_05", "ROW_07", "ROW_09", "ROW_08", "ROW_06", "ROW_04", "ROW_02"]
                    else:
                        expected = [f"ROW_{k:02d}" for k in (range(9, 0, -1) if flipped else range(1, 10))]
                    self.assertEqual(row["tail"]["row_contact_order"], expected)
                    pads = sorted(row["layers"]["top_copper"]["pads"], key=lambda pad: pad["position"])
                    self.assertEqual([pad["net"] for pad in pads], expected + [f"NC_{pin:02d}" for pin in ((10, 11, 12) if order == "ascending" else (3, 2, 1))])
                    # channel_order only renumbers the pins along the contacts.
                    pins = [pad["pin"] for pad in pads]
                    self.assertEqual(pins, list(range(1, 13)) if order == "ascending" else list(range(12, 0, -1)))
                    xs = [bounds(pad)[0] for pad in pads]
                    self.assertEqual(xs, sorted(xs), "positions run from the tail's canonical left")
                    # Each contact's tail piece starts at it and its net's fan-out reaches its electrode.
                    for pad in pads[:9]:
                        box = bounds(pad)
                        tails = [route for route in row["layers"]["top_copper"]["routes"] if route["net"] == pad["net"] and route["segment"] == "tail"]
                        self.assertEqual(len(tails), 1)
                        self.assertTrue(box[0] <= tails[0]["points"][0][0] <= box[2])


# --------------------------------------------------------------------------
# Corpora: random, fine pitch, readers, narrow fields, the judge's regressions.
# --------------------------------------------------------------------------


def _random_mask(rows: int, columns: int, rng: random.Random):
    """A row- and column-convex mask spanning the R x C grid (the design workflow judge's generator), or None."""

    steps = [0, 0, 0, 1, 1, 2, 3]
    for _ in range(100):
        valley, peak = rng.randrange(rows), rng.randrange(rows)
        low, high = [0] * rows, [columns - 1] * rows
        for k in range(valley - 1, -1, -1):
            low[k] = min(columns - 1, low[k + 1] + rng.choice(steps))
        for k in range(valley + 1, rows):
            low[k] = min(columns - 1, low[k - 1] + rng.choice(steps))
        for k in range(peak - 1, -1, -1):
            high[k] = max(0, high[k + 1] - rng.choice(steps))
        for k in range(peak + 1, rows):
            high[k] = max(0, high[k - 1] - rng.choice(steps))
        spans = list(zip(low, high))
        if any(a > b for a, b in spans):
            continue
        if any(spans[k + 1][0] > spans[k][1] or spans[k + 1][1] < spans[k][0] for k in range(rows - 1)):
            continue
        if min(a for a, _ in spans) != 0 or max(b for _, b in spans) != columns - 1:
            continue
        return [[a + 1, b + 1] for a, b in spans]
    return None


def _corpus(seed: int, count: int, pitches=(0.8, 1.0, 1.25, 1.5, 2.0, 2.0, 2.5, 3.0, 4.0), fills=(0.5, 0.6, 0.7, 0.8)) -> list:
    """Seeded valid designs: 2-32 x 2-32, both role mappings, masks (80 %) and rectangles, both sides (half) or one."""

    rng = random.Random(seed)
    answer = []
    while len(answer) < count:
        rows, columns = rng.randint(2, 32), rng.randint(2, 32)
        pitch, fill = rng.choice(pitches), rng.choice(fills)
        trace, space = rng.choice([0.1016, 0.1016, 0.127, 0.2]), rng.choice([0.1016, 0.1016, 0.127, 0.2])
        top = rng.choice(["rows", "columns"])
        mask = None if rng.random() < 0.2 else _random_mask(rows, columns, rng)
        sides = rng.choice(["both", "both", "left", "right"])
        request = _request(rows, columns, mask, sides=sides, pitch=pitch, cell=round(pitch * fill, 6), trace=trace, space=space, top=top)
        if check_design(request)["ok"]:
            answer.append(request)
    return answer


class CorpusTests(unittest.TestCase):
    def test_a_seeded_random_corpus_builds_clean(self) -> None:
        # 100 designs here; the design workflow judge's 400-design corpus ran clean (PROGRESS.md).
        corpus = _corpus(5, 100)
        self.assertEqual({request["routing"]["row_sides"] for request in corpus}, set(SIDES))
        self.assertEqual({request["role_mapping"]["top"] for request in corpus}, {"rows", "columns"})
        self.assertTrue(any("mask" in request["matrix"] for request in corpus) and any("mask" not in request["matrix"] for request in corpus))
        for index, request in enumerate(corpus):
            with self.subTest(design=index):
                _check_clean(self, generate_design(request))

    def test_fine_pitches_build_clean_and_warn_of_close_windows(self) -> None:
        corpus = _corpus(6, 30, pitches=(0.6, 0.7, 0.8, 0.9), fills=(0.4, 0.5, 0.55, 0.6))
        warned = 0
        for index, request in enumerate(corpus):
            with self.subTest(design=index):
                result = generate_design(request)
                _check_clean(self, result)
                record = result["boards"]["row"]["verification"]["registration"]
                close = [key for key in ("row_trace_to_column_window_mm", "column_trace_to_row_window_mm")
                         if record[key] is not None and record[key] < 0.15 - EPSILON]
                warnings = [issue for issue in result["validation"]["warnings"] if issue["code"] == "W_STACK_TRACE_WINDOW"]
                self.assertEqual(len(warnings), len(close))
                for issue in warnings:
                    self.assertRegex(issue["field"], r"^boards\.(row|column)\.layers\.top_copper\.routes$")
                warned += bool(warnings)
        self.assertEqual(warned, FINE_WARNED)

    def test_reader_tails_keep_their_contacts_at_the_far_end(self) -> None:
        for pins, rows, columns, pitch in ((16, 12, 10, 2.0), (32, 24, 20, 1.5), (48, 40, 30, 1.25), (64, 48, 48, 1.25), (64, 8, 6, 2.0)):
            for sides in SIDES:
                for top in ("rows", "columns"):
                    with self.subTest(pins=pins, rows=rows, sides=sides, top=top):
                        request = _request(rows, columns, sides=sides, pitch=pitch, cell=round(pitch * 0.6, 3), top=top, pins=(pins, pins))
                        result = generate_design(request)
                        _check_clean(self, result)
                        for key, count in (("row", rows), ("column", columns)):
                            pads = sorted(result["boards"][key]["layers"]["top_copper"]["pads"], key=lambda pad: pad["position"])
                            self.assertEqual(len(pads), pins)
                            self.assertEqual([pad["kind"] for pad in pads], ["connector_pad"] * count + ["connector_nc_pad"] * (pins - count))
                        self.assertEqual(sorted(result["boards"]["row"]["tail"]["row_contact_order"]), [f"ROW_{k:02d}" for k in range(1, rows + 1)])

    def test_narrow_fields_and_tiny_ones(self) -> None:
        cases = (
            # A narrow field with columns on top: a tail far wider than the field, lanes fanning out and in.
            ("31 x 2", _request(31, 2, sides="both", top="columns", trace=0.2)),
            ("25 x 2", _request(25, 2, sides="right", top="columns")),
            # Tiny fields: the tails stacked on fields narrower than either tail.
            ("2 x 2 both", _request(2, 2, sides="both")),
            ("2 x 2 left", _request(2, 2, sides="left")),
            ("2 x 2 right", _request(2, 2, sides="right", top="columns")),
            ("1 x 4", _request(1, 4, sides="both", pins=(None, 64))),
            ("3 x 4 reader", _request(3, 4, sides="left", pins=(None, 16))),
            # Inside its own zone a lane keeps the trace space from the next row's electrode (0.2 / 0.2 mm, 0.3 mm row gap).
            ("trace space 0.2", _request(16, 9, sides="both", pitch=1.0, cell=0.7, trace=0.2, space=0.2, top="columns")),
            # The strict record 14 at 1.25 / 0.8 mm (the own zone's corner keeps the lane off the window ring).
            ("1.25 / 0.8", _request(12, 10, [[5, 10], [3, 10], [1, 10], [1, 9], [1, 8], [2, 8], [2, 7], [3, 7], [4, 7], [4, 6], [5, 6], [5, 5]], sides="both", pitch=1.25, cell=0.8)),
        )
        for name, request in cases:
            with self.subTest(case=name):
                _check_clean(self, generate_design(request))

    def test_the_regressions_root_near_the_first_construction(self) -> None:
        # The regression designs (tests/fixtures/diagonal_bus_regressions.json).  The design workflow judge's outliers: a
        # funnel with every lane on one contact level went 82-84 mm deep on the wide 0.2 / 0.2 mm fields, a tail under the
        # near band 51-113 mm on the narrow ones.  The reviews': the bands of the onion and the tip moved by a raised
        # corner (rv:186, fine:028; its thin rows turn down just outside the Column windows' keep-out, no warning), mirrored
        # reader tails whose lanes crossed the whole tail (reader:029, edge:035, wide:138), tail sides slanting out from
        # above the field (rv:063, reader:015), diagonal-bus/2's fallback beside the Column tail taken for a little depth
        # at a much wider board (reader:011, reader:014) or needed (fine:052; the funnel now, the Column fan-out not
        # moved), and a very wide field of 3 rows, where the entry-angle guard keeps the fans at 79 degrees (wide:071).
        # Every Row funnel (its traces' last bends, _funnel_depth; since diagonal-bus/8 the tails root at the deeper of
        # the two boards' roots) stays within 1.0 mm of diagonal-bus/1's Row root (or its allowance) and no deeper than
        # diagonal-bus/2's (or its allowance: rv:186, whose straight Column fan-out enters at 60 degrees; and one-sided
        # the centred Row tail's cost, REGRESSION_CENTRED_COST), the bands (before the outline is
        # made regular; the regular outline has no flat vertex) no more than 0.15 mm inside its and the tip no narrower (rv:186's 0.24 mm wider on the Column body's side moved out for its fillet,
        # now shared), the thin rows' Row traces 0.15 mm from the Column windows, no flat lane; every design's Row tail
        # centred on the field (_check_clean; diagonal-bus/10).
        for name, entry in sorted(REGRESSIONS.items()):
            if name.startswith("_"):
                continue
            with self.subTest(case=name):
                result = generate_design(copy.deepcopy(entry["design"]))
                _check_clean(self, result)
                row = result["boards"]["row"]
                root = _funnel_depth(row)
                self.assertLessEqual(root, entry["row_root_v1_mm"] + entry.get("row_root_allowance_mm", 1.0))
                self.assertLessEqual(root, entry["row_root_v2_mm"] + entry.get("row_root_v2_allowance_mm", 0.001) + REGRESSION_CENTRED_COST.get(name, 0.0))
                if "row_root_prototypes_mm" in entry:
                    self.assertLess(root, min(entry["row_root_prototypes_mm"].values()) + 10.0)
                _check_bands(self, _plain(entry["design"]), V1_BANDS[name])
                self.assertEqual(_irregular(result), [])
                if name in ("rv:186", "fine:028"):
                    self.assertGreaterEqual(row["verification"]["registration"]["row_trace_to_column_window_mm"], OPENING - EPSILON)
                # No lane leaves flat: fine:052's lanes follow its receding field inward down to the edge no flatter than
                # the 85-degree taper cap (unheld, row 2's would lean 86.5 degrees from the vertical).
                self.assertEqual(row["construction"]["row_bus"]["flat_lane_rows"], [])


# --------------------------------------------------------------------------
# The centred Row tail (diagonal-bus/10, the plan's section 27).
# --------------------------------------------------------------------------


def _inner_flank(result) -> tuple:
    """Our own, one side: ``(F's bottom, F's inner side there, the Row tail's inner side, its root, the outline's inner
    side from F's bottom down to the root as (x, y) pairs, outward positive)`` in the Row board's frame turned tail
    down (canonical; the inner flank is east of the field, west where mirrored)."""

    row = result["boards"]["row"]
    turn = _down(row)
    sign = -1.0 if _flipped(result["design"]) else 1.0
    ring = [turn(point) for point in row["outline"]["points"]]
    boxes = list(_rows(row).values())
    bottom = min(box[1] for box in boxes) - MARGIN
    field = (max(box[2] for box in boxes) - OVERHANG + MARGIN) if sign > 0 else -(min(box[0] for box in boxes) + OVERHANG - MARGIN)
    tail = row["tail"]["bounds"]
    corners = [turn(corner) for corner in ((tail["x"], tail["y"]), (tail["x"] + tail["width"], tail["y"] + tail["height"]))]
    side = max(sign * corner[0] for corner in corners)
    root = max(corner[1] for corner in corners)
    heights = [bottom - 1e-4] + [point[1] for point in ring if root + 1e-4 < point[1] < bottom - 1e-4] + [root + 1e-4]
    walk = [(max(sign * x for x in _crossings(ring, y)), y) for y in sorted(set(heights), reverse=True)]
    return bottom, field, side, root, walk


class CentredTailTests(unittest.TestCase):
    """The user's request of 2026-10-26 (P5-diagonal-bus.md section 27): "some tails are not within the sensor's width".
    The Row tail lies centred on the field in every side mode, as the Column tail (diagonal-bus/10): within the field
    wherever it is narrower, centred on it where wider; its contacts are the tail's positions 1..R from its canonical left
    (at its far end from the band where mirrored); one side's inner flank slants out below F's bottom to a tail wider than
    F's bottom where that is 45 degrees or steeper (_check_clean holds the centre and the contacts on every build)."""

    def test_an_asymmetric_field_in_every_side_mode(self) -> None:
        # A field whose side recedes toward its bottom row (the video's grippers' faces alike): the lanes of that side follow
        # it inward, so the innermost lanes' midway lies 7.96 mm off the field's centre line, where diagonal-bus/9 parted the
        # funnel's contacts (its one-sided tails under the band 3.47 and 11.76 mm off it, the latter 2.8 mm beyond the
        # field).  The Row tail lies centred on the field, within it, in every side mode and both role mappings.
        mask = [[1, 12], [1, 12], [1, 11], [1, 10], [1, 9], [1, 8], [1, 7], [1, 6], [1, 5], [1, 4]]
        for top in ("rows", "columns"):
            for sides in SIDES:
                with self.subTest(top=top, sides=sides):
                    result = generate_design(_request(10, 12, mask, sides=sides, top=top))
                    _check_clean(self, result)
                    row = result["boards"]["row"]
                    row_tail, column_tail = _tails_down(result)
                    half = row["grid_registration"]["active_region"]["width"] / 2
                    self.assertAlmostEqual((row_tail[0] + row_tail[2]) / 2, 0.0, delta=CENTRED_NM)
                    self.assertTrue(-half < row_tail[0] < row_tail[2] < half, (row_tail, half))
                    if sides == "both":
                        rays, contacts = _funnel(row)
                        region = row["grid_registration"]["active_region"]
                        centre = _down(row)((region["x"] + region["width"] / 2, region["y"] + region["height"] / 2))[0]
                        self.assertAlmostEqual(contacts, centre, delta=CENTRED_NM)
                        self.assertGreater(abs(rays - centre), 2.0)  # the innermost lanes' midway lies well off it

    def test_a_reader_tail_wider_than_the_field(self) -> None:
        # A 64-pin reader tail (32.5 mm) under a 24.5 mm field: centred, 4.0 mm beyond the field on each side, in every
        # side mode; the rows take its positions 1..8 (_contact_problems: at the band's end, or mirrored at the far end),
        # the others unconnected.  Below F's bottom the outline slants out to the tail at 45 degrees from the vertical or
        # steeper, or steps out once: no long flat edge (the fillets' short arcs aside), but where the lanes themselves
        # reach beyond F's side: mirrored, the rows' contacts lie at the tail's far end, under the inner flank and 3 mm
        # beyond F's side there, and the side runs from F's bottom corner straight to the lanes' envelope (a chord at 55
        # degrees, its lower end on the envelope of the outermost contact's lane).
        for sides in SIDES:
            with self.subTest(sides=sides):
                result = generate_design(_request(8, 20, sides=sides, pitch=1.25, cell=0.75, pins=(64, None)))
                _check_clean(self, result)
                row = result["boards"]["row"]
                row_tail, _ = _tails_down(result)
                half = row["grid_registration"]["active_region"]["width"] / 2
                self.assertAlmostEqual(row_tail[2] - row_tail[0], 63 * 0.5 + 2 * 0.5, delta=EPSILON)
                self.assertAlmostEqual(-row_tail[0] - half, row_tail[2] - half, delta=2 * CENTRED_NM)
                self.assertGreater(row_tail[2] - half, 3.9)
                pads = sorted(row["layers"]["top_copper"]["pads"], key=lambda pad: pad["position"])
                self.assertEqual([pad["kind"] for pad in pads], ["connector_pad"] * 8 + ["connector_nc_pad"] * 56)
                turn = _down(row)
                ring = [turn(point) for point in row["outline"]["points"]]
                low = min(box[1] for box in _rows(row).values())
                tail = row["tail"]["bounds"]
                root = max(turn(corner)[1] for corner in ((tail["x"], tail["y"]), (tail["x"] + tail["width"], tail["y"] + tail["height"])))
                copper = [(turn(c), turn(d)) for route in row["layers"]["top_copper"]["routes"] for c, d in zip(route["points"], route["points"][1:])]
                for a, b in edges(ring):
                    if max(a[1], b[1]) < low - MARGIN - EPSILON and min(a[1], b[1]) > root + EPSILON and abs(b[1] - a[1]) > 1e-6 and math.dist(a, b) > 1.0:
                        if abs(b[0] - a[0]) > abs(b[1] - a[1]) + 1e-6:
                            self.assertTrue(_flipped(result["design"]), (a, b))
                            lower = min((a, b), key=lambda point: point[1])
                            self.assertLess(min(point_segment_distance(lower, c, d) for c, d in copper), 0.6, (a, b))

    def test_one_sides_inner_flank_slants_out_to_a_wider_tail(self) -> None:
        # The soft finger one-sided: its 30 mm Row tail (59 contacts) under its 23.4 mm field reaches 2.8 mm beyond F's
        # inner side.  The inner flank leaves F's bottom corner on F's side (no ledge out to the tail along F's bottom, as
        # the prototype of section 27 left) and widens monotonically down to the tail's side (the innermost lane's contact
        # column inside it), no edge of it flatter than 45 degrees from the vertical but the fillets' arcs.
        for sides in ("left", "right"):
            with self.subTest(sides=sides):
                result = generate_design(_named("soft finger", sides))
                _check_clean(self, result)
                bottom, field, side, root, walk = _inner_flank(result)
                self.assertGreater(side - field, 2.5)
                self.assertLess(walk[0][0] - field, 0.05)
                self.assertAlmostEqual(walk[-1][0], side, delta=EPSILON)
                for (x0, y0), (x1, y1) in zip(walk, walk[1:]):
                    self.assertGreaterEqual(x1, x0 - EPSILON, (x0, y0, x1, y1))
                    if math.dist((x0, y0), (x1, y1)) > 0.3:
                        self.assertLessEqual(x1 - x0, y0 - y1 + 1e-6, (x0, y0, x1, y1))

    def test_one_sides_inner_flank_on_fields_where_each_part_of_its_rule_decides(self) -> None:
        # The review of section 27 (the plan's 27.3): the inner flank's rule, each part on fields where it decides the
        # outline (our own measures, tails down, outward positive; the hold: the copper-to-edge rule plus half a finger
        # width, 0.428 mm).  (1) Where the slant from F's bottom corner out to the tail's side at the hold is 45 degrees
        # or steeper (here 0.69-0.88 of the drop: a slant only within half of it would step out instead, ledges of 1.1-5.3
        # mm, the fin's 25.5 and 29.2 mm2), the outline does not step out across F's bottom.  (2) The slant meets the
        # tail's side at the hold, not at the root: just above the hold the side lies within 45 degrees of the tail's
        # side, and on a 29 x 3 with a 32-pin reader tail on its near side the slant is one straight line down to the
        # hold (0.28 mm off it ending at the root).  (3) The side is monotone from the top down to its widest level and
        # from the tail up to it: the fin's narrowing field one-sided and the fine corpus's first design narrow by 2.8,
        # 4.4 and 0.16 mm below F's bottom without the fill, then widen to the tail.
        hold = round(PROFILE["routing"]["copper_to_edge_mm"] + PROFILE["routing"]["finger_trace_width_mm"] / 2 + PROFILE["outline"]["offset_allowance_mm"], 6)
        fin, fine = SHARED_REGRESSIONS["flush"]["fin 59x12 both"]["design"], _corpus(6, 30, pitches=(0.6, 0.7, 0.8, 0.9), fills=(0.4, 0.5, 0.55, 0.6))[0]

        def sided(design, sides):
            design = copy.deepcopy(design)
            design["routing"]["row_sides"] = sides
            return design

        cases = {
            "31 x 2": lambda sides: _request(31, 2, sides=sides, top="columns", trace=0.2),
            "29 x 3": lambda sides: _request(29, 3, sides=sides, pitch=2.5, cell=1.5, trace=0.127, space=0.127, pins=(32, None), tails=(20.0, 7.5)),
            "12 x 2": lambda sides: _request(12, 2, sides=sides, pitch=1.5, cell=0.9),
            "fin": lambda sides: sided(fin, sides),
            "fine6:000": lambda sides: sided(fine, sides),
        }
        for name, make in cases.items():
            for sides in ("left", "right"):
                with self.subTest(case=name, sides=sides):
                    result = generate_design(make(sides))
                    _check_clean(self, result)
                    bottom, _, side, root, walk = _inner_flank(result)
                    row = result["boards"]["row"]
                    turn, sign = _down(row), (-1.0 if _flipped(result["design"]) else 1.0)
                    ring = [turn(point) for point in row["outline"]["points"]]

                    def at(y):
                        return max(sign * x for x in _crossings(ring, y))

                    held = root + hold
                    # (3) unimodal: no valley below F's bottom.
                    xs = [x for x, _ in walk]
                    peak = max(range(len(xs)), key=lambda index: (xs[index], -index))
                    self.assertTrue(all(b >= a - 1e-6 for a, b in zip(xs[: peak + 1], xs[1: peak + 1])), walk)
                    self.assertTrue(all(b <= a + 1e-6 for a, b in zip(xs[peak:], xs[peak + 1:])), walk)
                    # (2) the tail's side holds straight for the hold, the side just above it within 45 degrees of it.
                    self.assertAlmostEqual(at(held - 1e-3), side, delta=1e-6)
                    self.assertLessEqual(side - at(held + 0.1), 0.1 + 1e-6)
                    if name in ("31 x 2", "29 x 3", "12 x 2", "fin"):
                        # (1) a slant of 45 degrees or steeper (our own run and drop): no step across F's bottom.
                        run, drop = side - at(bottom + 2e-3), bottom - held
                        self.assertLessEqual(run, drop, (run, drop))
                        self.assertLess(at(bottom - 2e-3) - at(bottom + 2e-3), 0.01)
                    if (name, sides) == ("29 x 3", "right"):
                        top = (at(bottom - 1.0), bottom - 1.0)
                        for x, y in walk:
                            if held + 0.05 < y < top[1]:
                                self.assertAlmostEqual(x, side + (top[0] - side) * (y - held) / (top[1] - held), delta=0.01)

    def test_a_tail_side_beyond_the_envelope_reaches_it_below_fs_bottom(self) -> None:
        # _side_chain's rule on its own (the plan's section 12.2): a tail side beyond the envelope above it slants out to it
        # from F's bottom at the highest, or, where that would lie flatter than 45 degrees, runs straight down and steps
        # out once above the tail's hold.  diagonal-bus/9's one-sided tail under the band met it on every build (ROW_01 ran
        # straight down past F's bottom into its contact); with the Row tail centred an outermost lane runs straight down
        # only where its contact lies exactly under its ray, so the rule is checked here on a lane's envelope straight down
        # from above F's bottom (y 0) past the hold (the root at -8, the hold 0.6 mm), F's side 2 mm inside it.
        pieces = [[[0.0, 0.0], [0.0, 10.0]], [[-2.0, 10.0], [-2.0, -10.0]]]
        self.assertEqual(diagonal._side_chain(pieces, -8.0, 0.6, 10.0, -2.3, -1, 0.0), [[-2.0, 10.0], [-2.0, 0.0], [-2.3, -7.4], [-2.3, -8.0]])
        self.assertEqual(diagonal._side_chain(pieces, -8.0, 0.6, 10.0, -12.0, -1, 0.0), [[-2.0, 10.0], [-2.0, -7.4], [-12.0, -7.4], [-12.0, -8.0]])
        mirrored = [[[-x, y] for x, y in piece] for piece in pieces]
        self.assertEqual(diagonal._side_chain(mirrored, -8.0, 0.6, 10.0, 2.3, 1, 0.0), [[2.0, 10.0], [2.0, 0.0], [2.3, -7.4], [2.3, -8.0]])

    def test_reader_contacts_beside_a_band_on_a_receding_field(self) -> None:
        # The review of section 27 (the plan's 27.3): _contact_problems guessed the band's side from ROW_01's lane below the
        # field against the tail's centre; on a field receding on the band's side the lanes follow it inward, past the
        # centred tail's centre, so the guess failed four of 700 seeded one-sided reader designs (these) and would have
        # passed a real wrong-end bug on them.  The side is now where the lanes leave their electrodes (_band_side): the
        # designs check clean, and built with the bus's side flipped (the band on the other side of the field, the rows at
        # the other end) each one's contacts are reported at the wrong end.
        cases = (
            _request(8, 8, [[k, 8] for k in range(1, 9)], sides="left", cell=1.0, trace=0.25, pins=(26, None), tails=(20.0, 7.5)),
            _request(16, 6, [[1, 6], [1, 5], [1, 4], [1, 3], [1, 2]] + [[1, 1]] * 11, sides="right", cell=1.0, trace=0.15, pins=(48, None), tails=(12.0, 20.0)),
            _request(8, 4, [[1, 4], [1, 4], [2, 4], [2, 4], [3, 4], [3, 4], [4, 4], [4, 4]], sides="left", trace=0.127, pins=(16, None), tails=(20.0, 30.0)),
            _request(6, 3, [[1, 3], [2, 3], [3, 3], [3, 3], [3, 3], [3, 3]], sides="left", pitch=5.0, cell=3.0, trace=0.15, pins=(48, None), tails=(30.0, 7.5)),
        )
        near = diagonal.near_side
        for index, request in enumerate(cases):
            with self.subTest(design=index):
                result = generate_design(request)
                _check_clean(self, result)
                row = result["boards"]["row"]
                level = min(level[1] for level in _row_levels(row)) - 0.1
                xs = [_down(row)(((bounds(pad)[0] + bounds(pad)[2]) / 2, 0.0))[0] for pad in row["layers"]["top_copper"]["pads"]]
                # ROW_01's lane below the field lies on the other side of the tail's centre than its band.
                self.assertLess((_x_at(_net_paths(row)["ROW_01"], level) - (min(xs) + max(xs)) / 2) * _band_side(row), 0)
                diagonal._pair_text.cache_clear()
                try:
                    with mock.patch.object(diagonal, "near_side", lambda design: "left" if near(design) == "right" else "right"):
                        wrong = generate_design(copy.deepcopy(request))
                finally:
                    diagonal._pair_text.cache_clear()
                self.assertEqual([problem[0] for problem in _contact_problems(wrong)], ["end"])

    def test_one_sides_rays_over_straight_column_copper(self) -> None:
        # The review of section 27 (the plan's 27.3): one side's lanes run straight down beside the field to their fans under
        # it (diagonal-bus/10, deeper than under the band), where a straight Column trace may lie under one: a 64-pin
        # Column tail wider than the Row tail, its contact columns rising to the Column V (ROW_06 on COL_02, 0.0 mm under
        # the band), and a Column trace dropping beside a narrowing field (ROW_13 on COL_24, 1.06 mm): straight on straight
        # as the stacked contact columns, reported (trace_overlap_mm), the longest runs measured, within RUN_BOUND_MM.
        cases = (
            (_request(32, 3, sides="right", pitch=4.0, cell=3.2, trace=0.15, space=0.2, top="columns", pins=(None, 64), tails=(30.0, 30.0)), 5.667),
            (_request(35, 38, [[1 + k // 2, 38 - k // 2] for k in range(35)], sides="right", pitch=4.0, cell=2.0, trace=0.15, space=0.2, tails=(12.0, 30.0)), 5.529),
        )
        for request, run in cases:
            with self.subTest(rows=request["matrix"]["rows"]):
                result = generate_design(request)
                _check_clean(self, result)
                self.assertAlmostEqual(_runs_off_the_contact_columns(result), run, delta=1e-3)
                self.assertGreater(run, 5.5)

    def test_the_mirrored_contacts(self) -> None:
        # One-sided with a 64-pin reader tail narrower than the field (8 x 27 at 1.25 mm): the tail centred, the rows'
        # contacts its positions 1..8 from the canonical left, beside the band on ROW_01's side with both and, mirrored
        # (turned back from the far side), at the tail's far end from the band; every lane fans inward under the field.
        # diagonal-bus/9 put the outermost contact used under ROW_01's lane (the unused ones outward beyond the band,
        # mirrored).
        for sides in ("left", "right"):
            with self.subTest(sides=sides):
                request = _request(8, 27, sides=sides, pitch=1.25, cell=0.75, pins=(64, 64))
                result = generate_design(request)
                _check_clean(self, result)
                row = result["boards"]["row"]
                pads = sorted(row["layers"]["top_copper"]["pads"], key=lambda pad: pad["position"])
                self.assertEqual([pad["kind"] for pad in pads], ["connector_pad"] * 8 + ["connector_nc_pad"] * 56)
                self.assertEqual(row["tail"]["row_contact_order"], [f"ROW_{k:02d}" for k in (range(8, 0, -1) if _flipped(request) else range(1, 9))])
                level = min(box[1] for box in _rows(row).values()) - 0.1
                band = _x_at(_net_paths(row)["ROW_01"], level)
                xs = [(bounds(pad)[0] + bounds(pad)[2]) / 2 for pad in pads]
                centre = (xs[0] + xs[-1]) / 2
                at_band = max(xs[:8]) < centre if band < centre else min(xs[:8]) > centre
                self.assertEqual(at_band, not _flipped(request), (band, centre, xs[:8]))
                self.assertEqual({fan["move"] for fan in row["construction"]["row_bus"]["fans"]}, {"east"})
                self.assertEqual(_contact_problems(result), [])


# --------------------------------------------------------------------------
# The stack keys of the registration, and the DRC gate.
# --------------------------------------------------------------------------


def _from_stack(board, point):
    """A stack-frame point back in the board's frame (the inverse of engine.drc.stack_frame)."""

    region = board["grid_registration"]["active_region"]
    centre_x, centre_y = region["x"] + region["width"] / 2, region["y"] + region["height"] / 2
    flip = board.get("physical_side") == "top" and board["tail"]["side"] in ("bottom", "top")
    return [centre_x - point[0] if flip else centre_x + point[0], centre_y + point[1]]


class StackRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = generate_design(_named("rectangle", "both"))

    def _registration(self, edit):
        row, column = copy.deepcopy(self.result["boards"]["row"]), copy.deepcopy(self.result["boards"]["column"])
        edit(row, column)
        return verify_registration(row, column, PROFILE)

    def _fields(self, outcome) -> list:
        return sorted((issue["code"], issue["field"]) for issue in outcome["errors"])

    def _add_row_piece(self, row, start, end) -> None:
        points = [_from_stack(row, start), _from_stack(row, end)]
        row["layers"]["top_copper"]["routes"].append({"net": "ROW_01", "kind": "polyline", "segment": "fanout", "width_mm": 0.1016, "points": points})

    def _column_box(self, net):
        column = self.result["boards"]["column"]
        convert = stack_frame(column)
        box = _rows(column)[net]
        corners = [convert(corner) for corner in ((box[0], box[1]), (box[2], box[3]))]
        return (min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners), max(c[1] for c in corners))

    def _gap_y(self, row) -> float:
        boxes = _rows(row)
        return (stack_frame(row)([0.0, boxes["ROW_10"][1]])[1] + stack_frame(row)([0.0, boxes["ROW_11"][3]])[1]) / 2

    def test_the_built_pair_registers(self) -> None:
        outcome = self._registration(lambda row, column: None)
        self.assertEqual((outcome["errors"], outcome["warnings"]), ([], []))
        self.assertTrue(outcome["measurements"]["passed"])

    def test_stacked_tails_register(self) -> None:
        # The tails are stacked: here the Column tail (12 contacts) lies wholly on the Row tail (32), and a tail moved
        # off the other one, widened onto it or lengthened under the other board registers clean (no tail gap, no tail
        # clearance); the overlap across the tails is reported.
        self.assertEqual(self._registration(lambda row, column: None)["measurements"]["tail_overlap_width_mm"], 6.5)

        def aside(row, column):
            row["tail"]["bounds"]["x"] += 30.0

        def widen(row, column):
            column["tail"]["bounds"]["x"] -= 10.0
            column["tail"]["bounds"]["width"] += 20.0

        def lengthen(row, column):
            column["tail"]["bounds"]["height"] += 10.0

        for edit, overlap in ((aside, 0.0), (widen, 16.5), (lengthen, 6.5)):
            with self.subTest(edit=edit.__name__):
                outcome = self._registration(edit)
                self.assertEqual((outcome["errors"], outcome["warnings"]), ([], []))
                self.assertTrue(outcome["measurements"]["passed"])
                self.assertAlmostEqual(outcome["measurements"]["tail_overlap_width_mm"], overlap, delta=EPSILON)
                for key in GONE_KEYS:
                    self.assertNotIn(key, outcome["measurements"])

    def test_tails_on_two_sides(self) -> None:
        # Both tails leave through one exit side (E_ROW_BUS_TAILS refuses the design otherwise); a hand-edited pair
        # whose Column tail leaves on the opposite side fails the registration.
        def opposite(row, column):
            column["tail"]["side"] = "top"

        outcome = self._registration(opposite)
        record = outcome["measurements"]
        self.assertIs(record["tail_sides_match"], False)
        self.assertFalse(record["passed"])
        self.assertIn(("E_REGISTRATION", "boards.column.tail.side"), self._fields(outcome))
        self.assertIn("stacks both tails on one side", " ".join(issue["message"] for issue in outcome["errors"]))

    def test_outlines_that_differ_over_the_field(self) -> None:
        # Down to the recorded level (the tails' roots, diagonal-bus/8) the two outlines are one in the stack: a Column
        # outline vertex moved there fails the registration (outlines_coincide_over_field, E_REGISTRATION on the Column
        # outline), with the distance reported; one moved below the level (its tail's tip) does not; a Row board without
        # the record, or recording a level the outlines do not share down to, fails too.
        built = self._registration(lambda row, column: None)["measurements"]
        self.assertEqual((built["outlines_coincide_over_field"], built["outline_deviation_over_field_mm"]), (True, 0.0))
        self.assertGreater(built["shared_outline_below_field_mm"], MARGIN)

        def vertex(column, top: bool) -> int:
            convert = _stack_down(column)
            points = column["outline"]["points"]
            return (max if top else min)(range(len(points)), key=lambda index: (convert(points[index])[1], index))

        def raised(row, column):
            index = vertex(column, True)
            point = column["outline"]["points"][index]
            column["outline"]["points"][index] = [point[0], point[1] + 0.05]

        def tip(row, column):
            index = vertex(column, False)
            point = column["outline"]["points"][index]
            column["outline"]["points"][index] = [point[0], point[1] - 0.05]

        def unrecorded(row, column):
            del row["construction"]["row_bus"]["shared_outline_below_field_mm"]

        def deeper(row, column):
            row["construction"]["row_bus"]["shared_outline_below_field_mm"] += 3.0

        outcome = self._registration(raised)
        record = outcome["measurements"]
        self.assertIs(record["outlines_coincide_over_field"], False)
        self.assertAlmostEqual(record["outline_deviation_over_field_mm"], 0.05, delta=1e-6)
        self.assertFalse(record["passed"])
        self.assertEqual(self._fields(outcome), [("E_REGISTRATION", "boards.column.outline")])
        self.assertIn("differ by 0.050000 mm", outcome["errors"][0]["message"])
        outcome = self._registration(tip)
        self.assertEqual((outcome["errors"], outcome["warnings"]), ([], []))
        self.assertIs(outcome["measurements"]["outlines_coincide_over_field"], True)
        outcome = self._registration(unrecorded)
        self.assertEqual((outcome["measurements"]["shared_outline_below_field_mm"], outcome["measurements"]["outline_deviation_over_field_mm"]), (None, None))
        self.assertEqual(self._fields(outcome), [("E_REGISTRATION", "boards.row.construction.row_bus.shared_outline_below_field_mm")])
        outcome = self._registration(deeper)
        self.assertGreater(outcome["measurements"]["outline_deviation_over_field_mm"], 1.0)
        self.assertEqual(self._fields(outcome), [("E_REGISTRATION", "boards.column.outline")])

    def test_crossings_and_runs_outside_the_field_are_reported_only(self) -> None:
        # Outside the taxel field the boards may overlap: a Column stub turned to cross the Row fans at a slant, and a
        # Row piece laid on a Column stub below the field, register clean; their crossings and runs are reported.
        def slant(row, column):
            # A Column piece across the near band's fans below the field, 53 degrees from the vertical.
            low = min(box[1] for box in _rows(row).values())
            bottom = stack_frame(row)([0.0, low])[1]
            points = [_from_stack(column, [10.0, bottom - 1.5]), _from_stack(column, [14.0, bottom - 4.5])]
            column["layers"]["top_copper"]["routes"].append({"net": "COL_06", "kind": "polyline", "segment": "fanout", "width_mm": 0.1016, "points": points})

        outcome = self._registration(slant)
        self.assertEqual((outcome["errors"], outcome["warnings"]), ([], []))
        self.assertGreater(outcome["measurements"]["trace_crossing_count"], self.result["boards"]["row"]["verification"]["registration"]["trace_crossing_count"])
        self.assertLess(outcome["measurements"]["trace_crossing_min_angle_deg"], 60.0)

        def along(row, column):
            stub = next(route for route in column["layers"]["top_copper"]["routes"] if route["net"] == "COL_03" and route["segment"] == "fanout")
            convert = stack_frame(column)
            a, b = convert(stub["points"][-1]), convert(stub["points"][-2])  # the stub: its top at the electrode, its bend below
            self._add_row_piece(row, [a[0], a[1] - 0.45], [a[0], b[1]])

        outcome = self._registration(along)
        self.assertEqual((outcome["errors"], outcome["warnings"]), ([], []))
        self.assertGreater(outcome["measurements"]["trace_overlap_mm"], 0.3)

    def test_a_trace_over_a_column_electrode(self) -> None:
        def over(row, column):
            x0, _, x1, _ = self._column_box("COL_06")
            y = self._gap_y(row)
            self._add_row_piece(row, [x0 - 0.5, y], [x1 + 0.5, y])

        outcome = self._registration(over)
        record = outcome["measurements"]
        self.assertEqual((record["trace_over_other_electrode_count"], record["trace_over_other_window_count"]), (1, 1))
        self.assertEqual(self._fields(outcome), [("E_REGISTRATION", "boards.row.layers.top_copper.routes")])
        self.assertIn("COL_06", outcome["errors"][0]["message"])

    def test_a_trace_over_column_electrodes_counts_once_and_fails_without_windows(self) -> None:
        # One route part across three Column electrodes is one part over the electrodes (and one over the window).
        def across(row, column):
            boxes = [self._column_box(net) for net in ("COL_05", "COL_06", "COL_07")]
            y = self._gap_y(row)
            self._add_row_piece(row, [min(box[0] for box in boxes) - 0.5, y], [max(box[2] for box in boxes) + 0.5, y])

        outcome = self._registration(across)
        record = outcome["measurements"]
        self.assertEqual((record["trace_over_other_electrode_count"], record["trace_over_other_window_count"]), (1, 1))
        self.assertEqual(self._fields(outcome), [("E_REGISTRATION", "boards.row.layers.top_copper.routes")])

        # A Column board without its electrode openings (a hand-edited pair): a trace over an electrode still fails.
        def no_windows(row, column):
            across(row, column)
            column["layers"]["top_coverlay_openings"] = [
                opening for opening in column["layers"]["top_coverlay_openings"]
                if opening["kind"] not in ("electrode_field_opening", "sensor_electrode_opening")
            ]

        outcome = self._registration(no_windows)
        record = outcome["measurements"]
        self.assertEqual((record["trace_over_other_electrode_count"], record["trace_over_other_window_count"]), (1, 0))
        self.assertFalse(record["passed"])
        self.assertEqual(self._fields(outcome), [("E_REGISTRATION", "boards.row.layers.top_copper.routes")])
        self.assertIn("1 over a column electrode", outcome["errors"][0]["message"])

    def test_a_trace_over_the_column_field_window_only(self) -> None:
        # Between two Column electrodes, inside the Column board's merged field window: over its window, over no
        # electrode, an error (W_STACK_TRACE_WINDOW only warns of a trace near the window).
        def between(row, column):
            right = self._column_box("COL_06")
            left = self._column_box("COL_05") if self._column_box("COL_05")[2] < right[0] else self._column_box("COL_07")
            x = (min(left[2], right[2]) + max(left[0], right[0])) / 2
            y = self._gap_y(row)
            self._add_row_piece(row, [x, y + 0.6], [x, y - 0.6])

        outcome = self._registration(between)
        record = outcome["measurements"]
        self.assertEqual((record["trace_over_other_electrode_count"], record["trace_over_other_window_count"]), (0, 1))
        self.assertEqual(self._fields(outcome), [("E_REGISTRATION", "boards.row.layers.top_copper.routes")])
        self.assertIn("field window", outcome["errors"][0]["message"])

        # With one opening per electrode (bridges of the coverlay rule or more) the same piece runs in a bridge: no
        # window over it, and it passes 0.15 mm from the windows' edges less a grid step: a warning.
        def per_electrode(row, column):
            between(row, column)
            openings = column["layers"]["top_coverlay_openings"]
            field = next(opening for opening in openings if opening["kind"] == "electrode_field_opening")
            openings.remove(field)
            for electrode in column["layers"]["top_copper"]["electrodes"]:
                x0, y0, x1, y1 = bounds(electrode)
                openings.append({"kind": "sensor_electrode_opening", "net": electrode["net"], "nets": [electrode["net"]],
                                 "opening_for": "column_electrode", "anchor": "lower_left", "x": x0 - EXPANSION, "y": y0 - EXPANSION,
                                 "width_mm": x1 - x0 + 2 * EXPANSION, "height_mm": y1 - y0 + 2 * EXPANSION})

        outcome = self._registration(per_electrode)
        record = outcome["measurements"]
        self.assertEqual((record["trace_over_other_electrode_count"], record["trace_over_other_window_count"]), (0, 0))
        self.assertEqual(outcome["errors"], [])
        self.assertAlmostEqual(record["row_trace_to_column_window_mm"], (0.6 - 2 * EXPANSION) / 2 - 0.1016 / 2, delta=EPSILON)
        self.assertEqual([issue["code"] for issue in outcome["warnings"]], ["W_STACK_TRACE_WINDOW"])

    def test_the_gate_keeps_a_diagonal_board_masked(self) -> None:
        # A diagonal board is measured by the masked records even without its mask records: strict record 14
        # stays strict (today's own-net skip would make it vacuous next to the merged window), and the margin
        # record fails for want of the crossing region.
        row = copy.deepcopy(self.result["boards"]["row"])
        for key in ("taxel_mask", "active_outline", "active_taxel_count"):
            del row["grid_registration"][key]
        checks = verify_board(row, PROFILE, self.result["design"])["measurements"]["checks"]
        self.assertEqual(checks["coverlay_opening_to_trace"]["semantics"], "strict")
        self.assertFalse(checks["active_field_margin"]["passed"])
        self.assertEqual(checks["active_field_margin"]["where"], "active_outline")
        # Without the row_bus record, the same board is an unmasked one again.
        del row["construction"]["row_bus"]
        checks = verify_board(row, PROFILE, self.result["design"])["measurements"]["checks"]
        self.assertNotIn("semantics", checks["coverlay_opening_to_trace"])


# --------------------------------------------------------------------------
# The Column board: the straight one's copper under the shared outline.
# --------------------------------------------------------------------------


# The surface profile with the Column fan-out's taper cap at the Column V's (diagonal-bus/8): the straight Column board
# of a design built with it has the bus's Column V.
V_CAP = 80.0
CAPPED = {**PROFILE, "fanout": {**PROFILE["fanout"], "maximum_taper_angle_deg": V_CAP}}


def _column_paths(board) -> str:
    """Our own: a digest of a board's copper in the stack frame (half grid steps) by its nets' centre lines (each net's
    route pieces chained from its contact to its electrode, collinear vertices dropped, the widths left out), its pads
    and electrodes, coverlay openings and stiffeners: where its traces widen into the tail is left out."""

    turn = _stack_down(board)
    copper = board["layers"]["top_copper"]

    def box(item):
        x0, y0, x1, y1 = bounds(item)
        corners = [turn(corner) for corner in ((x0, y0), (x1, y1))]
        return [_half(min(c[0] for c in corners)), _half(min(c[1] for c in corners)), _half(max(c[0] for c in corners)), _half(max(c[1] for c in corners))]

    items = []
    for net, path in _net_paths(board).items():
        points = [path[0]] + [b for a, b, c in zip(path, path[1:], path[2:])
                              if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9] + [path[-1]]
        stacked = _stack_down(board)
        items.append(["path", net, [[_half(v) for v in stacked(_up(board, point))] for point in points]])
    items += [[kind, item["net"], item["kind"], box(item)] for kind in ("electrodes", "pads") for item in copper[kind]]
    items += [["opening", item["kind"], item.get("net"), [[_half(c) for c in turn(point)] for point in item["points"]] if "points" in item else box(item)]
              for item in board["layers"]["top_coverlay_openings"]]
    items += [["stiffener", [[_half(c) for c in turn(point)] for point in item["points"]]] for item in board["layers"]["bottom_stiffener"]]
    items.sort(key=lambda item: json.dumps(item))
    return hashlib.sha256(json.dumps(items, separators=(",", ":")).encode("ascii")).hexdigest()


def _up(board, point):
    """Our own: a point of _net_paths (the board turned tail down) turned back to the board's own frame."""

    side = board["tail"]["side"]
    x, y = float(point[0]), float(point[1])
    return {"bottom": [x, y], "top": [-x, -y], "left": [y, -x], "right": [-y, x]}[side]


class ColumnBoardTests(unittest.TestCase):
    def test_the_column_board_is_the_straight_one_with_the_capped_v_under_the_shared_outline(self) -> None:
        # In every side mode the Column board is the straight Column board of the same design without routing.row_sides
        # (its tail centred under its fan-out, no shift, no neck, no stub drop) planned with its V capped at 80 degrees
        # (diagonal-bus/8; built here with the surface profile's taper cap at 80) or, where that roots the tails deeper,
        # the profile's own V (built with the surface profile), its tail's root lowered to the shared body's bottom
        # edge: the straight board with a tail as much longer has the same tip, contacts and stiffener, and its traces
        # the same centre lines (the bus board's widen into the tail lower, at its root).  Over the field
        # and its fan-out the Column board takes the shared outline (never narrower than the straight one), and it
        # keeps the classes and the masked records of the bus.
        designs = [(name, _named(name, sides)) for name in ("rectangle", "soft finger", "crank") for sides in SIDES]
        designs += [(f"corpus {index}", request) for index, request in enumerate(_corpus(11, 12))]
        compared = {"masked": 0, "unmasked": 0, "lowered": 0, "capped": 0, "own V": 0}
        for name, request in designs:
            with self.subTest(case=name, sides=request["routing"]["row_sides"], top=request["role_mapping"]["top"]):
                result = generate_design(copy.deepcopy(request))
                _check_clean(self, result)
                ours = result["boards"]["column"]
                capped = ours["construction"]["entry_taper_angle_deg"] <= V_CAP + 1e-6
                compared["capped" if capped else "own V"] += 1
                profile = CAPPED if capped else PROFILE
                straight_request = copy.deepcopy(request)
                del straight_request["routing"]["row_sides"]
                plain = generate_design(copy.deepcopy(straight_request), profile=profile)
                if not plain["ok"]:
                    continue  # a mask the straight Row channel refuses (E_MASK_ROUTING): no straight pair to compare with
                region, plain_region = ours["grid_registration"]["active_region"], plain["boards"]["column"]["grid_registration"]["active_region"]
                lowered = (region["y"] - _root(ours)) - (plain_region["y"] - _root(plain["boards"]["column"]))
                self.assertGreaterEqual(lowered, -EPSILON)
                key = "top_length_mm" if straight_request["role_mapping"]["top"] == "columns" else "bottom_length_mm"
                straight_request["tail"][key] = round(straight_request["tail"][key] + lowered, 6)
                straight = generate_design(straight_request, profile=profile)
                self.assertTrue(straight["ok"], straight["validation"]["errors"][:2])
                theirs = straight["boards"]["column"]
                self.assertEqual(_column_paths(ours), _column_paths(theirs))
                self.assertEqual(ours["construction"]["entry_taper_angle_deg"], theirs["construction"]["entry_taper_angle_deg"])
                self.assertGreaterEqual(ours["metrics"]["outline_width_mm"], theirs["metrics"]["outline_width_mm"] - EPSILON)
                self.assertEqual(ours["tail"]["length_mm"], request["tail"][key])
                masked = "mask" in result["design"]["matrix"]
                self.assertEqual(ours["construction"]["mask_class"], {"row": "diagonal", "column": "straight"})
                self.assertIn("taxel_mask", ours["grid_registration"])
                compared["masked" if masked else "unmasked"] += 1
                compared["lowered"] += lowered > 0.01
        self.assertGreaterEqual(min(compared.values()), 3, compared)


def _forced_cap(design: dict, capped: bool) -> dict:
    """The design built with its Column V planned at most COLUMN_V_CAP_DEG (``capped``) or at the profile's own caps,
    instead of the construction's choice of the two (the pair cache cleared around it)."""

    original = diagonal._column_plan
    diagonal._pair_text.cache_clear()
    try:
        with mock.patch.object(diagonal, "_column_plan", side_effect=lambda plan_design, profile, _capped=True: original(plan_design, profile, capped)):
            return generate_design(copy.deepcopy(design))
    finally:
        diagonal._pair_text.cache_clear()


# The Column V rule's tie (diagonal-bus/8, the plan's section 20.1): the two plans' roots equal on the layout grid (the
# construction compares them with its float guard, diagonal._NOISE_MM; they are rounded to the nanometre grid).  The test
# compares the shared levels, on that grid too, with the construction's tolerance (0.001 mm before diagonal-bus/10, which
# took the soft finger one-sided, its profile's V 0.971 um higher, for a tie).
V_TIE_MM = diagonal._NOISE_MM


class ColumnVCapTests(unittest.TestCase):
    def test_the_v_is_capped_where_that_roots_the_tails_no_deeper(self) -> None:
        # diagonal-bus/8 (the plan's section 20): a Column V at most COLUMN_V_CAP_DEG (80 degrees) leaves the Row fans the
        # profile's steepest cap, 85 degrees, outside the entry-angle guard (a V at the profile's own caps, 84 degrees on
        # the rectangle with both, leaves them 78).  The construction takes it wherever it roots the tails no deeper than
        # the V at the profile's own caps, and that one otherwise (a fan below 85 degrees gains nothing from the cap: the
        # caps are whole degrees and those within 5 degrees of the entry angle are excluded).  On the named corpus each
        # build is one of the two, byte for byte: the capped one where its tails' roots lie no deeper (with both the
        # rectangle's 5.251 -> 4.730 mm below the field, the crank's 9.503 -> 6.480, the equilateral's 8.033 -> 5.401;
        # since diagonal-bus/10 one side's fans run inward under the field too and take 85 degrees: the rectangle's 8.556
        # -> 7.986, the crank's 12.808 -> 9.736, the equilateral's 10.507 -> 7.841), the other where they lie higher (the
        # disk with both 4.808 -> 3.919; the soft finger one-sided by 0.971 um).  A tie is equal roots on the layout
        # grid, as the construction's (_build: a nanometre's difference decides).
        self.assertEqual(diagonal.COLUMN_V_CAP_DEG, 80.0)
        taken = {"capped": 0, "own": 0}
        for key in sorted(PINNED):
            design = _named(*key)
            with self.subTest(case=key):
                result = generate_design(copy.deepcopy(design))
                capped, own = _forced_cap(design, True), _forced_cap(design, False)
                self.assertLessEqual(capped["boards"]["column"]["construction"]["entry_taper_angle_deg"], diagonal.COLUMN_V_CAP_DEG + 1e-6)
                levels = [build["boards"]["row"]["construction"]["row_bus"]["shared_outline_below_field_mm"] for build in (result, capped, own)]
                chosen = "capped" if levels[1] <= levels[2] + V_TIE_MM else "own"
                self.assertEqual(result["boards"], (capped if chosen == "capped" else own)["boards"])
                self.assertLessEqual(levels[0], min(levels[1:]) + V_TIE_MM)
                taken[chosen] += capped["boards"] != own["boards"]
                if chosen == "capped" and key[0] not in ("soft finger", "disk"):
                    self.assertEqual({fan["angle_deg"] for fan in result["boards"]["row"]["construction"]["row_bus"]["fans"]}, {85.0})
        self.assertGreaterEqual(min(taken.values()), 3, taken)


# --------------------------------------------------------------------------
# One outline over the field.
# --------------------------------------------------------------------------


def _own_outlines(design: dict) -> dict:
    """The design built with each board's own outline (made regular and filleted, the construction's tails and copper):
    ``_share_outline`` but for its choice of the level, the pair cache cleared around it (the registration then fails:
    the outlines differ)."""

    original = diagonal._share_outline

    def own(geo, owns, column, plan, level, probe=False):
        if probe:
            return original(geo, owns, column, plan, level, probe=True)
        rules = geo.rules
        row, smallest = engine_geometry.fillet_concave_corners(owns[0], rules.fillet_radius, arc_step_rad=rules.arc_step)
        column_ring, _ = engine_geometry.fillet_concave_corners(owns[1], rules.fillet_radius, arc_step_rad=rules.arc_step)
        column["outline"]["points"] = [[round(x, 6), round(y, 6)] for x, y in column_ring]
        return [[round(x, 6), round(y, 6)] for x, y in row], smallest

    diagonal._pair_text.cache_clear()
    try:
        with mock.patch.object(diagonal, "_share_outline", side_effect=own):
            return generate_design(copy.deepcopy(design))
    finally:
        diagonal._pair_text.cache_clear()


def write_shared_fixture() -> None:
    """Rewrite tests/fixtures/diagonal_bus_shared_outline.json from the engine: per case its boards' digests built each with
    its own outline (:func:`_own_outlines`)."""

    path = ROOT / "tests" / "fixtures" / "diagonal_bus_shared_outline.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["_note"] = (
        "The boards of diagonal-bus/10 (claude/specs/masked-field/P5-diagonal-bus.md, sections 14, 15, 20 and 27: the Row tail "
        "centred on the field) each with its own "
        "outline (made regular and filleted; tests/test_diagonal_bus.py _own_outlines, written by write_shared_fixture): per "
        "design, the digests of each board's copper, coverlay openings and stiffeners in the stack frame (half layout-grid "
        "steps) and of its outline's vertices more than 1.0 mm below the shared level (the tails' roots, tails down); the "
        "shared outline keeps all of them. Named designs are built by tests/test_diagonal_bus.py (_named); the others carry "
        "their design: regressions of the design workflow judge's corpus and the user's CAD fits (the soft finger 59 x 12 "
        "and the crank 32 x 32)."
    )
    for key, entry in document["cases"].items():
        result = _own_outlines(entry.get("design") or _named(*key.split("|")))
        entry["copper"] = {board: _stack_copper(result["boards"][board]) for board in ("row", "column")}
        entry["below"] = {board: _outline_below(result["boards"][board], JOIN_DEPTH) for board in ("row", "column")}
    path.write_text(json.dumps(document, indent=1, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(document['cases'])} cases to {path}")


class SharedOutlineTests(unittest.TestCase):
    def test_the_shared_outline_keeps_the_copper_and_the_own_shapes(self) -> None:
        # tests/fixtures/diagonal_bus_shared_outline.json holds the digests of the boards built each with its own outline
        # (_own_outlines; written by write_shared_fixture, diagonal-bus/8): per board its copper, coverlay openings and
        # stiffeners in the stack, and its outline's vertices more than JOIN_DEPTH below the shared level (its tail).  On
        # the named corpus (every side mode), the judge's corpus designs the first prototypes of the shared outline
        # failed (a level micrometres below the boards' corners, the fillets of a tail stepping out beside the field,
        # own concave corners just below the level) and the user's CAD fits (the soft finger 59 x 12 with 5 mil traces
        # and 20 mm tails, the crank 32 x 32), the boards keep all of them, the outlines coincide down to the tail roots
        # and every check passes (_check_clean).  Since diagonal-bus/8 the level is the tails' roots: below it each
        # board has only its tail, so a board keeps its own tail.
        self.assertEqual(len(SHARED), 40)
        for key, entry in sorted(SHARED.items()):
            with self.subTest(case=key):
                design = entry.get("design") or _named(*key.split("|"))
                result = generate_design(copy.deepcopy(design))
                _check_clean(self, result)
                for board in ("row", "column"):
                    self.assertEqual(_stack_copper(result["boards"][board]), entry["copper"][board], board)
                    self.assertEqual(_outline_below(result["boards"][board], JOIN_DEPTH), entry["below"][board], board)

    def test_the_shared_outline_is_the_union_down_to_the_tail_roots(self) -> None:
        # From the tip down to the tails' roots (diagonal-bus/8: the shared level, below the taxel field by the funnel or
        # the Column V and their fillets into the tails) the outline is the union of the two boards' own: the Column
        # board takes the Row board's bands and funnel (its width is the Row board's: 24.4 mm before on the soft finger,
        # 48.4 on the disk), the one-sided disk's Row board the Column body's lower corners (PINNED: 20 mm beyond its own
        # west side).  Below it each board is its own tail.
        for key, before, gain in ((("soft finger", "both"), 24.4, 4.0), (("soft finger", "left"), 24.4, 4.0), (("disk", "left"), 48.4, 2.5)):
            with self.subTest(case=key):
                result = generate_design(_named(*key))
                row, column = result["boards"]["row"], result["boards"]["column"]
                level = _shared_level(row)
                self.assertGreater(_field_bottom(row) - level, MARGIN + 1.0)  # the funnel and the fan-out are shared too
                widths = {}
                for name, board in (("row", row), ("column", column)):
                    turn = _stack_down(board)
                    ring = [turn(point) for point in board["outline"]["points"]]
                    heights = [point[1] for point in ring if point[1] > level + EPSILON] + [level + 0.01]
                    cuts = [_crossings(ring, y - 1e-4) for y in heights]
                    widths[name] = (max(cut[-1] - cut[0] for cut in cuts if cut), _crossings(ring, level - 0.6))
                    # The field's windows lie well above the level.
                    electrodes = [turn(corner) for item in board["layers"]["top_copper"]["electrodes"]
                                  for corner in ((bounds(item)[0], bounds(item)[1]), (bounds(item)[2], bounds(item)[3]))]
                    self.assertGreater(min(point[1] for point in electrodes) - EXPANSION, level + 0.1)
                self.assertAlmostEqual(widths["row"][0], widths["column"][0], delta=EPSILON)  # one width down to the roots
                self.assertGreater(widths["column"][0], before + gain)  # the Column board under the Row bands
                # Below the level each board is its own tail (just below its fillets into it).
                for name, tail in zip(("row", "column"), _tails_down(result)):
                    self.assertEqual(len(widths[name][1]), 2)
                    self.assertAlmostEqual(widths[name][1][0], tail[0], delta=1e-5)
                    self.assertAlmostEqual(widths[name][1][1], tail[2], delta=1e-5)

    def test_both_tails_leave_the_shared_bottom_edge(self) -> None:
        # Both boards' outlines cross the height just above the tails' roots at the same two points, the shared body's
        # bottom edge, which spans both tails (each tail keeps its width and position: they part below it); just below
        # their fillets into it each board is its tail.  reader:004 (15 x 4 at 1.25 mm, a 16-pin Column tail 8.5 mm wide
        # under a 4.5 mm field, the 16-pin Row tail centred on it since diagonal-bus/10, under its band to the west
        # before): the Column tail steps out from its body, and the shared bottom edge runs from the Row tail's west side
        # to the Column tail's east one, the two tails' common width.
        cases = {"reader:004": SHARED["reader:004"]["design"], "soft finger|both": _named("soft finger", "both"),
                 "rectangle|left": _named("rectangle", "left"), "crank|right": _named("crank", "right")}
        for key, design in cases.items():
            with self.subTest(case=key):
                result = generate_design(copy.deepcopy(design))
                _check_clean(self, result)
                row_tail, column_tail = _tails_down(result)
                level = _shared_level(result["boards"]["row"])
                above = [_crossings(_stack_ring(result["boards"][board]), level + 1e-3) for board in ("row", "column")]
                self.assertEqual(len(above[0]), 2)
                self.assertAlmostEqual(above[0][0], above[1][0], delta=EPSILON)
                self.assertAlmostEqual(above[0][1], above[1][1], delta=EPSILON)
                self.assertLessEqual(above[0][0], min(row_tail[0], column_tail[0]) + 1e-5)
                self.assertGreaterEqual(above[0][1], max(row_tail[2], column_tail[2]) - 1e-5)
                for board, tail in zip(("row", "column"), (row_tail, column_tail)):
                    below = _crossings(_stack_ring(result["boards"][board]), level - 0.6)
                    self.assertAlmostEqual(below[0], tail[0], delta=1e-5)
                    self.assertAlmostEqual(below[-1], tail[2], delta=1e-5)
                if key == "reader:004":
                    self.assertAlmostEqual(above[0][0], row_tail[0], delta=1e-5)
                    self.assertAlmostEqual(above[0][1], column_tail[2], delta=1e-5)
                    self.assertGreater(column_tail[2] - column_tail[0], 8.0)


# --------------------------------------------------------------------------
# Regular outlines (diagonal-bus/5).
# --------------------------------------------------------------------------


def _outside_by(inner, outer) -> float:
    """Our own: the largest distance by which a vertex or an edge's midpoint of the ring ``inner`` lies outside the ring
    ``outer`` (0.0 where none does)."""

    worst = 0.0
    for a, b in edges(inner):
        for point in (a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)):
            if not point_in_polygon(point, outer):
                worst = max(worst, min(point_segment_distance(point, c, d) for c, d in edges(outer)))
    return worst


def _ring_turns(ring) -> list:
    return [abs(turn) for turn in turns_degrees(ring)]


# The fillets of an outline built over a merged run are the same circles stepped at other angles (a few micrometres off
# the other's chords): the outline built without the regularization lies inside the regular one within this (mm).
FILLET_STEP = 0.005
# The user's CAD fits (the soft finger 59 x 12 and the crank 32 x 32 with both, tests/fixtures/
# diagonal_bus_shared_outline.json): (Row, Column) outline vertices and flat vertices (_irregular) without the
# regularization (diagonal-bus/4's outlines but at F's bottom) and with it.
USER_VERTICES = {
    "soft_59x12|both": ((68, 90), 4, (62, 84), (50, 72)),
    "crank_32x32_masked|both": ((93, 93), 30, (76, 76), (63, 63)),
}
# (diagonal-bus/6: the crank's notches at the tip are chamfered, 325 / 349 -> 310 / 334 vertices without the
# regularization and 89 / 115 -> 74 / 100 with it.  diagonal-bus/7: the straight sides, the last pair: the soft finger's
# two sides, the crank's ROW_01 side (its long side keeps its polyline).  diagonal-bus/8: the boards share one outline
# down to their tails, the union of their own outlines before their fillets, filleted once: the Column board carries the
# Row funnel, and both boards' vertex counts differ only by their tails; the crank's flat vertices without the
# regularization 462 -> 30, two filleted outlines' crossings gone.  diagonal-bus/10, the Row tail centred on the field:
# the crank's Row tail lies exactly on its Column tail, 0.049 mm east of it before (the funnel's split midway between the
# innermost lanes), so the shared bottom edge no longer steps between their sides: 4 vertices fewer on each board.)
# How much the regular outline widens the tip (ROW_01's centre) and the board (its widest) against the outline built
# without the regularization, on the named corpus with both (mm).  The equilateral's slanted side becomes one straight
# edge from just below the tip down to F's bottom (its flat turns add up to under 5 degrees), touching the old one at its
# middle: 0.57 mm wider at the tip, still the narrowest relative to the field; the rectangle, the soft finger and the
# crank widen by 0.3-0.4 mm at F's bottom, where the band's long side meets the short drop to the funnel at 2.9 degrees
# (the soft finger's 0.410 -> 0.406 with diagonal-bus/10: its Row tail on the field's centre line, 0.2 mm from where its
# funnel's split midway between the innermost lanes put it).
GROWTH = {
    "rectangle": (0.001, 0.330), "soft finger": (0.001, 0.406), "crank": (0.001, 0.330), "equilateral": (0.574, 0.0),
    "disk": (0.0, 0.025),
}


class RegularOutlineTests(unittest.TestCase):
    def test_the_flat_runs_become_straight_edges_outside_them(self) -> None:
        # Without the regularization the outlines carry runs of vertices turning by under 5 degrees (diagonal-bus/4's:
        # the crank's slanted side, 247 of the Row outline's 325 vertices); with it none is left (_check_clean, on every
        # corpus), and each board's outline contains the one built without it (to the fillets' steps), keeps its copper
        # and its relative narrow tip.  The user's CAD fits and the named corpus with both; the counts and the growth
        # are the regularization's own (the build without the straight sides, diagonal-bus/6's), the containment and the
        # copper the full build's.
        designs = {key: SHARED[key]["design"] for key in USER_VERTICES}
        designs.update({f"{name}|both": _named(name, "both") for name in GROWTH})
        for key, design in designs.items():
            with self.subTest(case=key):
                full, regular, plain = generate_design(copy.deepcopy(design)), _unstraight(design), _plain(design)
                _check_clean(self, full)
                self.assertEqual(_irregular(regular), [])
                self.assertTrue(_irregular(plain), "without the regularization the outlines have flat vertices")
                for board in ("row", "column"):
                    ours, theirs = full["boards"][board], plain["boards"][board]
                    self.assertEqual(_stack_copper(ours), _stack_copper(theirs))
                    self.assertLessEqual(_outside_by(_stack_ring(theirs), _stack_ring(ours)), FILLET_STEP, board)
                bus, before = regular["boards"]["row"]["construction"]["row_bus"], plain["boards"]["row"]["construction"]["row_bus"]
                self.assertIs(bus["tip_is_narrowest_relative"], True)
                self.assertIs(full["boards"]["row"]["construction"]["row_bus"]["tip_is_narrowest_relative"], True)
                if key in USER_VERTICES:
                    counts, flat, regular_counts, straight_counts = USER_VERTICES[key]
                    self.assertEqual(tuple(len(plain["boards"][board]["outline"]["points"]) for board in ("row", "column")), counts)
                    self.assertEqual(len(_irregular(plain)), flat)
                    self.assertEqual(tuple(len(regular["boards"][board]["outline"]["points"]) for board in ("row", "column")), regular_counts)
                    self.assertEqual(tuple(len(full["boards"][board]["outline"]["points"]) for board in ("row", "column")), straight_counts)
                    self.assertAlmostEqual(bus["tip_width_mm"], before["tip_width_mm"], delta=0.002)
                else:
                    tip, widest = GROWTH[key.split("|")[0]]
                    self.assertAlmostEqual(bus["tip_width_mm"] - before["tip_width_mm"], tip, delta=0.002)
                    self.assertAlmostEqual(bus["widest_mm"] - before["widest_mm"], widest, delta=0.002)

    def test_a_bent_edge_becomes_one_straight_edge_outside_the_bend(self) -> None:
        # A 20 x 10 rectangle whose top edge bends up by 2 degrees at x = 12 (a convex vertex: 4 degrees of turn) and down
        # by 1.5 degrees at x = 6 (a concave one): the top becomes one edge on or above both bends, through the outer one
        # (the hull edge over the middle of the run), its corners where it meets the sides.
        rise = 8 * math.tan(math.radians(2.0))
        ring = [[0.0, 0.0], [20.0, 0.0], [20.0, 10.0], [12.0, 10.0 + rise], [6.0, 10.0 + rise - 6 * math.tan(math.radians(0.5))], [0.0, 10.0]]
        out = diagonal._regular(ring, ())
        self.assertEqual(len(out), 4)
        self.assertEqual([point for point in out if point[1] < 10.0 - 1e-9 and point[1] > 1e-9], [])
        self.assertLessEqual(_outside_by(ring, out), 1e-9)
        self.assertGreater(min(_ring_turns(out)), REGULAR_TURN)
        self.assertTrue(any(abs(point[0] - 12.0) < 1e-9 for point in ring) and point_segment_distance(ring[3], out[2], out[3]) < 1e-9)
        # A roof's ridge turns by twice its slope: at the threshold or more it stays a corner, flatter it goes (one edge
        # through the ridge); a flatter vertex at an anchor stays as it is.
        bent = [[0.0, 0.0], [20.0, 0.0], [20.0, 10.0], [10.0, 10.0 + 10 * math.tan(math.radians((REGULAR_TURN + 0.02) / 2))], [0.0, 10.0]]
        self.assertEqual(diagonal._regular(bent, ()), bent)
        flat = [[0.0, 0.0], [20.0, 0.0], [20.0, 10.0], [10.0, 10.0 + 10 * math.tan(math.radians((REGULAR_TURN - 0.02) / 2))], [0.0, 10.0]]
        roof = diagonal._regular(flat, ())
        self.assertEqual(len(roof), 4)
        self.assertLessEqual(_outside_by(flat, roof), 1e-9)
        self.assertEqual(diagonal._regular(ring, {tuple(ring[3]), tuple(ring[4])}), ring)
        # A vertex within a grid step of the next is one corner with it.
        twin = [[0.0, 0.0], [20.0, 0.0], [20.0, 10.0], [10.0, 10.0], [10.0 + 4e-7, 10.0 + 5e-7], [0.0, 10.0]]
        self.assertEqual(len(diagonal._regular(twin, ())), 4)

    def test_a_smooth_curve_becomes_a_polygon_of_corners(self) -> None:
        # A circle of 100 vertices (3.6 degrees each, 360 in all): a polygon whose corners turn by 5 degrees or more, the
        # circle inside it, within a few hundredths of a millimetre of it at radius 10 mm.
        circle = [[10 * math.cos(2 * math.pi * k / 100), 10 * math.sin(2 * math.pi * k / 100)] for k in range(100)]
        out = diagonal._regular(circle, ())
        self.assertLess(len(out), 72)
        self.assertGreater(min(_ring_turns(out)), REGULAR_TURN)
        self.assertLessEqual(_outside_by(circle, out), 1e-9)
        self.assertLess(max(math.hypot(*point) for point in out), 10.2)
        # A regular 70-gon turns by 5.14 degrees at every vertex: it stays.
        polygon = [[10 * math.cos(2 * math.pi * k / 70), 10 * math.sin(2 * math.pi * k / 70)] for k in range(70)]
        self.assertEqual(diagonal._regular(polygon, ()), polygon)
        self.assertEqual(diagonal.REGULAR_TURN_DEG, REGULAR_TURN)


# Straight sides (diagonal-bus/7, the plan's section 17): on each side of the shared outline the stretch from the tip
# corner down to its widest point, and from there down to F's bottom, is one straight line where one line encloses it
# lying no more than this (mm) outside it anywhere.
SIDE_STRAIGHTEN = 1.0
# The user's CAD fit of the rounded 30 x 38 mm plate with corner radius 4 mm (P5-diagonal-bus.md section 16: the full 14
# x 18 field, proposal 1 with field containment): its design.
R4_PLATE = {
    "schema_version": "tactile-fpc-design/v1", "template_id": "surface_matrix_v1", "project_name": "Surface 18x14",
    "matrix": {"rows": 18, "columns": 14, "pitch_x_mm": 2, "pitch_y_mm": 2, "taxel_width_mm": 1.4, "taxel_height_mm": 1.4},
    "tail": {"top_length_mm": 15.895, "bottom_length_mm": 18.5, "row_side": "bottom", "column_side": "bottom"},
    "connector": {"row_pins": None, "column_pins": None}, "role_mapping": {"top": "rows", "bottom": "columns"},
    "channel_order": {"rows": "ascending", "columns": "ascending"},
    "routing": {"trace_width_mm": 0.127, "trace_space_mm": 0.127, "row_sides": "both"},
}
# How far each side's tip corner moves out (mm, stack frame, tails down: west, east), the outline's vertices (Row,
# Column) without the straight sides and with them, on the user's cases with both: the r4 plate's corner moves 0.238 and
# 0.110 mm (from 2.591 to 2.353 and 30.991 to 31.101 in the Row board's frame), the board 0.232 and 0.187 mm wider at
# ROW_01; the crank's long side keeps its polyline (no line within 1.0 mm).  Rewritten by section 24 (diagonal-bus/9):
# the crank's long side is then made convex, its kink below the tip corner bridged by the hull's edge from the tip corner
# (0.358 mm deep as filleted, under the 1.79 mm bound at 2 mm), whose corner turning 4.6 degrees merges with the long
# slant (section 15): its tip corner moves 0.806 mm out along the top edge, the vertices 74 -> 67.  diagonal-bus/10:
# 4 vertices fewer on each board (80 / 67 -> 76 / 63; the Row tail on the Column tail exactly, USER_VERTICES).
TIP_MOVES = {
    "r4 plate": ((0.110, 0.238), (70, 92), (58, 80)),
    "soft_59x12|both": ((0.111, 0.238), (62, 84), (50, 72)),
    "crank_32x32_masked|both": ((0.806, 0.238), (76, 76), (63, 63)),
}


def _side_walk(ring, level: float, west: bool) -> tuple:
    """Our own: one side of a ring (stack frame, tails down, either orientation) from its tip corner down to the height
    ``level``, the east side mirrored (x negated) so that both are west sides: ``(points top down with the side's point
    on the level last, the next vertex below that point, the top edge's other end)``."""

    points = [(x if west else -x, y) for x, y in ring]
    count = len(points)
    top = max(y for _, y in points)
    start = min((index for index, point in enumerate(points) if point[1] >= top - 1e-9), key=lambda index: (points[index][0], index))
    step = 1 if points[(start + 1) % count][1] < top - 1e-9 else -1
    side, index = [points[start]], start
    while True:
        index = (index + step) % count
        point = points[index]
        if point[1] <= level + 1e-9:
            if point[1] >= level - 1e-9:
                return side + [point], points[(index + step) % count], points[(start - step) % count]
            a = side[-1]
            return side + [(a[0] + (point[0] - a[0]) * (level - a[1]) / (point[1] - a[1]), level)], point, points[(start - step) % count]
        side.append(point)


def _turn_degrees(direction, after) -> float:
    """Our own: the signed turn (degrees) from one direction to the next, positive to the left (on a west side walked
    down: toward the inside, a convex corner)."""

    return math.degrees(math.atan2(direction[0] * after[1] - direction[1] * after[0], direction[0] * after[0] + direction[1] * after[1]))


def _on_line(direction, pivot, point) -> bool:
    """Our own: whether ``point`` lies within a nanometre of the line through ``pivot`` along ``direction``."""

    return abs(direction[0] * (point[1] - pivot[1]) - direction[1] * (point[0] - pivot[0])) / math.hypot(*direction) <= 1e-6


def _meets_below(direction, end, after) -> bool:
    """Our own: a line arriving at a side's point on the level runs on straight into the side below it (``after``: the
    next vertex there within a nanometre of the line) or meets it at a convex corner of REGULAR_TURN or more."""

    run = (after[0] - end[0], after[1] - end[1])
    if _on_line(direction, end, after) and direction[0] * run[0] + direction[1] * run[1] > 0:
        return True
    return _turn_degrees(direction, run) >= REGULAR_TURN


def _enclosing_line(stretch, corner, edge_end):
    """Our own: the line through the stretch's last point (its widest) with every point of the stretch on or inside it
    (east of it, within a nanometre), if one exists within SIDE_STRAIGHTEN of every point and of the tip corner along the
    top edge: ``(direction down to the widest point, the tip corner on it)``, else None."""

    pivot = stretch[-1]
    for p in [p for p in stretch[:-1] if p[1] > pivot[1] + 1e-9]:
        direction = (pivot[0] - p[0], pivot[1] - p[1])
        x_at = lambda y: pivot[0] + direction[0] * (y - pivot[1]) / direction[1]
        if all(q[0] >= x_at(q[1]) - 1e-6 for q in stretch):  # a point at the widest point's height lies east of it
            top = corner[1]
            tip = (x_at(top), top)
            length = math.hypot(*direction)
            gap = max(abs(direction[0] * (q[1] - pivot[1]) - direction[1] * (q[0] - pivot[0])) / length for q in stretch)
            if gap > SIDE_STRAIGHTEN + 1e-6 or corner[0] - tip[0] > SIDE_STRAIGHTEN + 1e-6 or (edge_end[0] - corner[0]) * (tip[0] - corner[0]) > 1e-12:
                return None
            return direction, tip
    return None


def _straight_plan(result) -> dict:
    """Our own (P5-diagonal-bus.md section 17), on a build without the straight sides: per side (``west``, ``east``,
    stack frame) whether its stretch from the tip corner down to its widest point (``upper``) and from there down to the
    shared level (``lower``) becomes one straight line: a line through the widest point encloses the upper stretch, the
    chord to the level point the lower one (heading in no flatter than 45 degrees), each within SIDE_STRAIGHTEN; a line
    ending on the level other than along the side's last edge there meets each board's side below that point straight
    on or convex by REGULAR_TURN or more; the widest point, above the level, stays a corner of REGULAR_TURN or more (the
    lower line given up first)."""

    row, column = result["boards"]["row"], result["boards"]["column"]
    level = _shared_level(row)
    plan = {}
    for name, west in (("west", True), ("east", False)):
        points, _, edge_end = _side_walk(_stack_ring(row), level, west)
        last = len(points) - 1
        least = min(x for x, _ in points)
        widest = next(k for k, point in enumerate(points) if point[0] <= least + 1e-6)
        end = points[-1]
        afters = []
        for board in (row, column):
            own, following, _ = _side_walk(_stack_ring(board), level, west)
            if abs(own[-1][0] - end[0]) <= 1e-6:
                afters.append(following)
        upper = lower = None
        if widest >= 2:
            line = _enclosing_line(points[:widest + 1], points[0], edge_end)
            if line is not None and (widest < last or _on_line(line[0], end, points[last - 1]) or all(_meets_below(line[0], end, after) for after in afters)):
                upper = line[0]
        if last - widest >= 2:
            pivot = points[widest]
            chord = (end[0] - pivot[0], end[1] - pivot[1])
            length = math.hypot(*chord)
            inner = points[widest + 1:last]
            x_at = lambda y: pivot[0] + chord[0] * (y - pivot[1]) / chord[1]
            if (chord[1] < 0 and (chord[0] <= 0 or chord[0] <= -chord[1]) and all(q[0] >= x_at(q[1]) - 1e-6 for q in inner)
                    and max(abs(chord[0] * (q[1] - pivot[1]) - chord[1] * (q[0] - pivot[0])) / length for q in inner) <= SIDE_STRAIGHTEN + 1e-6
                    and (_on_line(chord, end, points[last - 1]) or all(_meets_below(chord, end, after) for after in afters))):
                lower = chord
        if widest < last:
            before = (points[widest][0] - points[widest - 1][0], points[widest][1] - points[widest - 1][1]) if widest else None
            following = (points[widest + 1][0] - points[widest][0], points[widest + 1][1] - points[widest][1])
            for choice in ((upper, lower), (upper, None), (None, lower), (None, None)):
                arriving = choice[0] if choice[0] is not None else before
                if choice == (None, None) or arriving is None or abs(_turn_degrees(arriving, choice[1] if choice[1] is not None else following)) >= REGULAR_TURN:
                    upper, lower = choice
                    break
        plan[name] = (upper is not None, lower is not None, points, widest)
    return plan


def _straight_problems(result, before) -> list:
    """Our own: where the outline (stack frame) breaks the straight-side rule against the build without it (``before``,
    :func:`_straight_plan`): a stretch that becomes one line keeps a vertex between its ends; a stretch that does not
    differs from the old; the widest point moves; a new vertex lies more than SIDE_STRAIGHTEN outside the old outline,
    or the old outline outside the new by more than a nanometre."""

    found = []
    row = result["boards"]["row"]
    level = _shared_level(row)
    for name, (upper, lower, old, widest) in _straight_plan(before).items():
        new, _, _ = _side_walk(_stack_ring(row), level, name == "west")
        anchor = old[widest]
        at = [k for k, point in enumerate(new) if abs(point[0] - anchor[0]) <= 1e-6 and abs(point[1] - anchor[1]) <= 1e-6]
        if not at:
            found.append((name, "the widest point moved", anchor))
            continue
        w = at[0]
        if upper and w != 1:
            found.append((name, "a vertex between the tip corner and the widest point", new[1:w]))
        if not upper and any(math.dist(p, q) > 1e-6 for p, q in zip(new[:w + 1], old[:widest + 1])) or not upper and w != widest:
            found.append((name, "the upper stretch changed without a line", w, widest))
        if lower and len(new) - 1 - w != 1:
            found.append((name, "a vertex between the widest point and the level", new[w + 1:-1]))
        if not lower and (len(new) - w != len(old) - widest or any(math.dist(p, q) > 1e-6 for p, q in zip(new[w:-1], old[widest:-1]))):
            found.append((name, "the lower stretch changed without a line"))
    for key in ("row", "column"):
        ours, theirs = _stack_ring(result["boards"][key]), _stack_ring(before["boards"][key])
        if _outside_by(theirs, ours) > 1e-6:
            found.append((key, "the old outline outside the new", _outside_by(theirs, ours)))
        for a, b in edges(ours):
            for t in (k / 16 for k in range(16)):
                point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                if not point_in_polygon(point, theirs) and min(point_segment_distance(point, c, d) for c, d in edges(theirs)) > SIDE_STRAIGHTEN + 1e-6:
                    found.append((key, "more than SIDE_STRAIGHTEN outside the old outline", point))
                    break
    return found[:5]


class StraightSideTests(unittest.TestCase):
    """The user's request (P5-diagonal-bus.md section 17): on each side of the shared outline the stretch from the tip
    corner down to the widest point becomes one straight line where one line encloses it within SIDE_STRAIGHTEN (the tip
    corner moving out for it), and the stretch from there down to F's bottom likewise; curved sides keep their polyline.
    Both boards carry it (one outline over the field), the copper and every outline more than JOIN_DEPTH below the
    level are the build's without it (diagonal-bus/6's), the old outline lies inside the new one."""

    def _cases(self) -> dict:
        cases = {"r4 plate": R4_PLATE}
        cases.update({key: SHARED[key]["design"] for key in ("soft_59x12|both", "crank_32x32_masked|both")})
        cases.update({f"{name}|{sides}": _named(name, sides) for name in ("rectangle", "soft finger", "crank", "equilateral", "disk") for sides in SIDES})
        cases.update({name: entry["design"] for name, entry in sorted(REGRESSIONS.items()) if not name.startswith("_")})
        return cases

    def test_the_sides_from_the_tip_are_straight_where_a_line_encloses_them(self) -> None:
        straightened = kept = 0
        for key, design in self._cases().items():
            with self.subTest(case=key):
                # The straight sides on the build without the convex sides (diagonal-bus/8's outline; section 24's own
                # predicate, _convex_problems, holds on the full build through _check_clean).
                full, result, before = generate_design(copy.deepcopy(design)), _unconvex(design), _unstraight(design)
                _check_clean(self, full)
                self.assertEqual(_straight_problems(result, before), [])
                plan = _straight_plan(before)
                straightened += sum(upper for upper, _, _, _ in plan.values())
                kept += sum(not upper and widest >= 2 for upper, _, _, widest in plan.values())
                for board in ("row", "column"):
                    self.assertEqual(_stack_copper(result["boards"][board]), _stack_copper(before["boards"][board]), board)
                    self.assertEqual(result["boards"][board]["layers"], before["boards"][board]["layers"], board)
                    self.assertEqual(_outline_below(result["boards"][board], JOIN_DEPTH), _outline_below(before["boards"][board], JOIN_DEPTH), board)
                bus, old = result["boards"]["row"]["construction"]["row_bus"], before["boards"]["row"]["construction"]["row_bus"]
                self.assertIs(bus["tip_is_narrowest_relative"], old["tip_is_narrowest_relative"])
                self.assertAlmostEqual(bus["widest_mm"], old["widest_mm"], delta=EPSILON)
                self.assertGreaterEqual(bus["tip_width_mm"], old["tip_width_mm"] - EPSILON)
        # Most sides with a stretch to straighten take the line; the curved ones (the disk, the crank's long side, the
        # equilateral's step to the Column body) keep their polyline.
        self.assertEqual((straightened, kept), (STRAIGHTENED, KEPT))

    def test_the_users_cases(self) -> None:
        # The r4 plate (the user's picture: a vertical stub, a concave R0.5 fillet and a 1.1 mm jog at 17 degrees below
        # each tip corner), the soft finger and the crank with both: each side with the line runs from the tip corner,
        # moved out, straight down to F's bottom; no vertex turns between them.
        for key, (moves, counts, straight_counts) in TIP_MOVES.items():
            design = R4_PLATE if key == "r4 plate" else SHARED[key]["design"]
            with self.subTest(case=key):
                result, before = generate_design(copy.deepcopy(design)), _unstraight(design)
                level = _shared_level(result["boards"]["row"])
                plan = _straight_plan(before)
                for name, move in zip(("west", "east"), moves):
                    new, _, _ = _side_walk(_stack_ring(result["boards"]["row"]), level, name == "west")
                    old, _, _ = _side_walk(_stack_ring(before["boards"]["row"]), level, name == "west")
                    self.assertAlmostEqual(old[0][0] - new[0][0], move, delta=0.001, msg=name)
                    if plan[name][0]:
                        # The tip corner and the widest point (the funnel's top, by F's bottom): one line.
                        least = min(x for x, _ in new)
                        self.assertEqual(next(k for k, point in enumerate(new) if point[0] <= least + 1e-6), 1, name)
                self.assertEqual(tuple(len(before["boards"][board]["outline"]["points"]) for board in ("row", "column")), counts)
                self.assertEqual(tuple(len(result["boards"][board]["outline"]["points"]) for board in ("row", "column")), straight_counts)
                self.assertEqual(_shared_problems(result), [])

    def test_the_rule_on_its_own(self) -> None:
        # A ring like the r4 plate's west side: the tip corner, a vertical stub, a concave bend out, a jog and the long
        # slant to the level, running on below it along the slant: one line from the tip corner, moved out, along the
        # slant (the stretch's supporting line through the level point) and on below the level, the point on the level
        # and everything below it as they were; with the stub 1.1 mm inside the slant's line there is no line within the
        # bound.
        level, run = -0.5, -2.5
        slope = (-0.876 + 3.056) / (33.731 - level)
        ring = [[-0.5, 35.9], [-0.5, 35.03], [-0.544, 34.825], [-0.868, 33.774], [-0.876, 33.731], [-3.056, level],
                [-3.056 - slope * (level - run), run], [30.0, run], [30.0, 35.9]]
        own = [list(point) for point in ring]
        out = diagonal._straight_sides([list(point) for point in ring], level, run, [own])
        self.assertEqual(out[1:], ring[5:])
        tip = out[0]
        self.assertAlmostEqual(tip[1], 35.9, delta=1e-9)
        self.assertAlmostEqual(tip[0], -0.876 + slope * (35.9 - 33.731), delta=1e-9)  # the slant's line, 0.238 mm out
        self.assertLessEqual(-0.5 - tip[0], SIDE_STRAIGHTEN)
        self.assertLessEqual(_outside_by(ring, out), 1e-9)
        for point in ring[:5]:
            self.assertLessEqual(point_segment_distance(point, tip, ring[5]), SIDE_STRAIGHTEN)
        deep = [[0.4, 35.9], [0.4, 35.03], [0.356, 34.825]] + [list(point) for point in ring[3:]]
        self.assertEqual(diagonal._straight_sides(deep, level, run, [deep]), deep)
        self.assertEqual(diagonal.SIDE_STRAIGHTEN_MM, SIDE_STRAIGHTEN)
        # The bound is measured to the outline as the board has it, its concave corners filleted (P5-diagonal-bus.md
        # section 20.1): a staircase of 1.6 mm steps under a 45-degree line through its outer corners lies 1.131 mm inside
        # the line at its sharp inner corners, 0.922 mm as filleted (R0.5): one edge from the tip corner to the widest point
        # against the filleted ring, the staircase kept against the sharp one (the Column board's column ends stepping out
        # beyond the Row field's chamfer, fine:002).
        stairs = [[0.0, 10.0], [0.0, 8.4], [-1.6, 8.4], [-1.6, 6.8], [-3.2, 6.8], [-3.2, 5.2], [-4.8, 5.2], [-4.8, 3.6], [-6.4, 3.6],
                  [-6.4, level], [-6.4, run], [30.0, run], [30.0, 10.0]]
        rounded = [[round(x, 6), round(y, 6)] for x, y in diagonal._filleted([list(point) for point in stairs], diagonal.Rules(PROFILE))[0]]
        self.assertGreater(max(point_segment_distance(point, stairs[0], stairs[8]) for point in stairs[:9]), SIDE_STRAIGHTEN + 0.1)
        self.assertLess(max(point_segment_distance(point, stairs[0], stairs[8]) for point in rounded if point[1] >= 3.6 and point[0] <= 0.0), SIDE_STRAIGHTEN - 0.05)
        out = diagonal._straight_sides([list(point) for point in stairs], level, run, [stairs], rounded)
        self.assertEqual(len(out), 6)
        self.assertLessEqual(math.dist(out[0], stairs[0]), 1e-9)
        self.assertEqual(out[1:], stairs[8:])
        self.assertEqual(diagonal._straight_sides([list(point) for point in stairs], level, run, [stairs]), stairs)


class ConvexSideTests(unittest.TestCase):
    """The user's request (P5-diagonal-bus.md section 24): a slanted side down a staircase one straight line from the tip
    corner, its S-shaped kink beside a narrow tip gone: each side's stretch from the tip corner down to its widest point
    becomes its convex hull (field F and the lanes) wherever a dent lies no deeper than a step of CONVEX_STEP_CELLS cells
    (2 p / sqrt 5) inside the hull's edge; a deeper pocket keeps its outline, the convex bend into the funnel stays.  Both
    boards carry it, the copper is untouched, the old outline lies inside the new one, no board is wider."""

    # The construction's own constant.
    def test_the_constants(self) -> None:
        self.assertEqual(diagonal.CHAMFER_STEP_CELLS, CONVEX_STEP_CELLS)
        self.assertEqual(ROW_BUS_VERSION, "diagonal-bus/11")

    def test_the_rule_on_its_own(self) -> None:
        # A west side like the crank's before section 24: the tip corner, a vertical stub, a jog out at 22 degrees, the long
        # 45-degree slant down to the widest point, then the side down to the level.  The hull's edge from the tip corner
        # to the widest point bridges the kink (1.73 mm deep at the stub's foot as sharp, less as filleted); deeper than
        # the bound it stays, and so does a dent holding an anchor.
        level = -0.5
        ring = [[0.0, 40.0], [0.0, 37.5], [-1.5, 36.9], [-2.5, 35.9], [-37.5, 0.9], [-37.5, level], [-37.5, -2.5], [30.0, -2.5],
                [30.0, 40.0]]
        rules = diagonal.Rules(PROFILE)
        rounded = [[round(x, 6), round(y, 6)] for x, y in diagonal._filleted([list(p) for p in ring], rules)[0]]
        bound = _convex_depth({"matrix": {"pitch_x_mm": 2.0, "pitch_y_mm": 2.0}})
        out, widest = diagonal._convex_sides([list(p) for p in ring], level, rounded, set(), bound)
        self.assertEqual(out, [ring[0]] + ring[4:])
        self.assertEqual(widest, [tuple(ring[4])])
        self.assertLessEqual(_outside_by(ring, out), 1e-9)
        # The dent's depth as filleted, under the bound; as sharp the stub's foot lies 1.73 mm inside the edge.
        self.assertAlmostEqual(_side_dents(ring, level, True)[2][0][2], 1.7303, places=3)
        self.assertEqual(diagonal._convex_sides([list(p) for p in ring], level, rounded, set(), 1.0), (ring, []))
        # A deeper pocket (the stub 4 mm long) stays; an anchor in the dent keeps it too.
        deep = [[0.0, 42.0], [0.0, 37.5]] + [list(p) for p in ring[2:-1]] + [[30.0, 42.0]]
        rounded_deep = [[round(x, 6), round(y, 6)] for x, y in diagonal._filleted([list(p) for p in deep], rules)[0]]
        self.assertEqual(diagonal._convex_sides([list(p) for p in deep], level, rounded_deep, set(), bound), (deep, []))
        self.assertEqual(diagonal._convex_sides([list(p) for p in ring], level, rounded, {(-1.5, 36.9)}, bound), (ring, []))
        # The east side alike (the ring mirrored).
        mirrored = diagonal._mirrored(ring)
        out, widest = diagonal._convex_sides(mirrored, level, diagonal._mirrored(rounded), set(), bound)
        self.assertEqual(out, diagonal._mirrored([ring[0]] + ring[4:]))
        self.assertEqual(widest, [(37.5, 0.9)])

    def test_the_named_corpus_and_the_users_cases(self) -> None:
        # Against the build without the convex sides (diagonal-bus/8's outline, the same level): the old outline inside the
        # new one, no point of the new one farther out than the bound, the widest the same, the tip no narrower, the copper,
        # the layers and the outlines below the joins the same; every build clean (_check_clean holds _convex_problems).
        cases = {key: SHARED[key]["design"] for key in ("soft_59x12|both", "crank_32x32_masked|both")}
        cases.update({f"{name}|{sides}": _named(name, sides) for name in ("rectangle", "soft finger", "crank", "equilateral", "disk") for sides in SIDES})
        cases.update({name: entry["design"] for name, entry in sorted(REGRESSIONS.items()) if not name.startswith("_")})
        changed = []
        for key, design in cases.items():
            with self.subTest(case=key):
                result, before = generate_design(copy.deepcopy(design)), _unconvex(design)
                _check_clean(self, result)
                bound = _convex_depth(result["design"])
                for board in ("row", "column"):
                    ours, theirs = _stack_ring(result["boards"][board]), _stack_ring(before["boards"][board])
                    self.assertLessEqual(_outside_by(theirs, ours), 1e-6, board)
                    self.assertLessEqual(_outside_by(ours, theirs), bound + 1e-6, board)
                    self.assertEqual(_stack_copper(result["boards"][board]), _stack_copper(before["boards"][board]), board)
                    self.assertEqual(result["boards"][board]["layers"], before["boards"][board]["layers"], board)
                    self.assertEqual(_outline_below(result["boards"][board], JOIN_DEPTH), _outline_below(before["boards"][board], JOIN_DEPTH), board)
                bus, old = result["boards"]["row"]["construction"]["row_bus"], before["boards"]["row"]["construction"]["row_bus"]
                self.assertAlmostEqual(bus["widest_mm"], old["widest_mm"], delta=EPSILON)
                self.assertGreaterEqual(bus["tip_width_mm"], old["tip_width_mm"] - EPSILON)
                if result["boards"]["row"]["outline"] != before["boards"]["row"]["outline"]:
                    changed.append(key)
        # The sides that change: a kink or a short step bridged (the rectangles' sides are the lanes' slants, straight
        # already but where a one-sided band starts below the tip).
        self.assertEqual(changed, CONVEX_CHANGED)


class ConvexFlankTests(unittest.TestCase):
    """The multi-gripper video's notch (P5-diagonal-bus.md section 27.8, the user's "更加clean和直接"): with one side, the
    side without the bus came down the field's side, stepped in on a small rounded notch just below the field (the Column
    board's body corner, its ledge in to the outermost route and that route's turn into the V) and sloped to the centred
    tail.  Its stretch from the field's outline corner down to the last convex corner before the tail is now its convex
    hull (diagonal-bus/11, ``_convex_flank``): both boards carry it, the copper and the tails' roots are untouched, the old
    outline lies on or inside the new one, the area added lies below F's bottom on that side, no board is wider, every
    corner stays regular; with both sides nothing changes."""

    def test_the_rule_on_its_own(self) -> None:
        # A ring like the video's WidowX 7 x 7 in the construction's frame (the east side the flank): down the field's side
        # to F's corner (20.5, -0.5), the ledge in to the Column route at 19.5, down, its turn and the slope to the tail's
        # corner (12, -2.2), the tail down to the level and on below it.  The notch is bridged: one edge from F's corner to
        # the route's turn; an anchor in it keeps it.
        rules = diagonal.Rules(PROFILE)
        level = -3.0
        ring = [[-2.0, 20.0], [-2.0, -0.5], [8.0, -2.2], [8.0, level], [8.0, -5.0], [12.0, -5.0], [12.0, level], [12.0, -2.2], [18.5, -1.6],
                [19.5, -1.0], [19.5, -0.5], [20.5, -0.5], [20.5, 20.0]]
        out, held = diagonal._convex_flank([list(p) for p in ring], level, set(), -0.5, rules)
        self.assertEqual(out, ring[:9] + ring[11:])
        self.assertEqual(held, {(20.5, -0.5)})
        self.assertLessEqual(_outside_by(ring, out), 1e-9)
        self.assertIsNone(diagonal._convex_flank([list(p) for p in ring], level, {(19.5, -1.0)}, -0.5, rules))
        # The hull's edge from F's corner nearly along a long slope (0.65 degrees off it): its end moves back along the
        # slope's line to meet it at 6 degrees; the slope's line and the tail's corner stay.
        level = -5.0
        long = [[-2.0, 20.0], [-2.0, -0.5], [-1.0, -0.6], [-1.0, level], [-1.0, -7.0], [2.0, -7.0], [2.0, level], [2.0, -4.0], [19.0, -0.8],
                [19.2, -0.75], [19.2, -0.5], [20.5, -0.5], [20.5, 20.0]]
        out, held = diagonal._convex_flank([list(p) for p in long], level, set(), -0.5, rules)
        moved = out[8]
        self.assertEqual((out[:8] + out[9:], held), (long[:8] + long[11:], {(20.5, -0.5)}))
        self.assertLessEqual(abs((moved[0] - 2.0) * (-0.8 + 4.0) - (moved[1] + 4.0) * (19.0 - 2.0)) / math.hypot(17.0, 3.2), 1e-6)  # on it
        self.assertAlmostEqual(abs(_turn_degrees((moved[0] - 20.5, moved[1] + 0.5), (2.0 - moved[0], -4.0 - moved[1]))), 6.0, places=3)
        self.assertLessEqual(_outside_by(long, out), 1e-6)  # the moved end on the layout grid
        # Moved back so, the edge from the corner would leave the side above it (here 80 degrees from the horizontal, the
        # bridge 5.5 degrees off it, the slope 1 degree off the bridge) turning 0.5 degrees: that choice is passed over and a
        # stretch a corner shorter is bridged (the ledge's corner alone), every corner of the side 5 degrees or more.
        west = [[-0.868241, 20.0], [-0.868241, 4.424039], [0.0, -0.5], [0.6, -0.5], [0.6, -1.2], [0.801715, -3.390891], [2.505807, -9.14381],
                [2.505807, -10.0], [2.505807, -12.0], [10.0, -12.0], [10.0, -10.0], [10.0, 20.0]]
        out, held = diagonal._convex_flank(diagonal._mirrored(west), -10.0, set(), -0.5, rules)
        self.assertEqual((out, held), (diagonal._mirrored(west[:3] + west[4:]), {(0.0, -0.5)}))
        turns = dict(zip(map(tuple, out), turns_degrees(out)))
        self.assertTrue(all(abs(turns[(-x, y)]) >= REGULAR_TURN for x, y in west[1:7] if x != 0.6 or y != -0.5), turns)

    def test_the_videos_designs_and_the_regressions(self) -> None:
        # The video's WidowX 250 and Robotiq 3F one-sided (frames 46 and 54 of each) and the corpora's kinds
        # (tests/fixtures/diagonal_bus_shared_regressions.json, 'flank'): against the build without the convex flank at the
        # same level, the notch gone (our own predicate, in _check_clean), the old outline on or inside the new one, the
        # new beyond it only below F's bottom on the side without the bus, the copper, the layers, the tails below the
        # joins, the widest, the tip and the level the same, the area added pinned.
        for name, entry in sorted(SHARED_REGRESSIONS["flank"].items()):
            with self.subTest(case=name):
                design = entry["design"]
                result, before = generate_design(copy.deepcopy(design)), _unflanked(design)
                _check_clean(self, result)
                self.assertEqual(bool(_flank_problems(before)), entry["notch"])
                self.assertEqual(entry["side"], "east" if design["routing"]["row_sides"] == "left" else "west")
                for board in ("row", "column"):
                    ours, theirs = _stack_ring(result["boards"][board]), _stack_ring(before["boards"][board])
                    self.assertLessEqual(_outside_by(theirs, ours), 1e-6, board)
                    bottom = _field_bottom(result["boards"][board]) - MARGIN
                    beyond = [point for point in ours if not point_in_polygon(point, theirs)
                              and min(point_segment_distance(point, a, b) for a, b in edges(theirs)) > 1e-6]
                    # (or within a fillet radius above it: the fillet of a corner there bending out to a wider tail)
                    self.assertTrue(all(point[1] < bottom + FILLET_RADII[0] and (point[0] > 0) == (entry["side"] == "east") for point in beyond),
                                    (board, beyond[:3]))
                    self.assertEqual(_stack_copper(result["boards"][board]), _stack_copper(before["boards"][board]), board)
                    self.assertEqual(result["boards"][board]["layers"], before["boards"][board]["layers"], board)
                    self.assertEqual(_outline_below(result["boards"][board], JOIN_DEPTH), _outline_below(before["boards"][board], JOIN_DEPTH), board)
                bus, old = result["boards"]["row"]["construction"]["row_bus"], before["boards"]["row"]["construction"]["row_bus"]
                for key in ("widest_mm", "tip_width_mm", "shared_outline_below_field_mm"):
                    self.assertAlmostEqual(bus[key], old[key], delta=EPSILON, msg=key)
                added = _area_above(_stack_ring(result["boards"]["row"]), -1e9) - _area_above(_stack_ring(before["boards"]["row"]), -1e9)
                self.assertAlmostEqual(added, entry["added_mm2"], delta=1e-3)
                self.assertEqual(len(result["boards"]["row"]["outline"]["points"]), entry["row_vertices"])

    def test_both_sides_have_no_flank(self) -> None:
        # With both sides the lanes cover either side: the convex flank is never asked for.
        for name in ("widowx_250 7x7 left", "robotiq_3f 6x6 left"):
            design = copy.deepcopy(SHARED_REGRESSIONS["flank"][name]["design"])
            design["routing"]["row_sides"] = "both"
            diagonal._pair_text.cache_clear()
            try:
                with mock.patch.object(diagonal, "_convex_flank", side_effect=AssertionError("both sides have no flank")):
                    _check_clean(self, generate_design(design))
            finally:
                diagonal._pair_text.cache_clear()

    def test_the_named_corpus_and_the_regressions(self) -> None:
        # One-sided: the build changes where the build without the convex flank has the notch (our own predicate) and
        # nowhere else, the old outline on or inside the new one, the copper the same.
        cases = {f"{name}|{sides}": _named(name, sides) for name in ("rectangle", "soft finger", "crank", "equilateral", "disk") for sides in ("left", "right")}
        cases.update({name: entry["design"] for name, entry in sorted(REGRESSIONS.items()) if not name.startswith("_")
                      and entry["design"]["routing"].get("row_sides") in ("left", "right")})
        changed = []
        for key, design in cases.items():
            with self.subTest(case=key):
                result, before = generate_design(copy.deepcopy(design)), _unflanked(design)
                _check_clean(self, result)
                if result["boards"]["row"]["outline"] != before["boards"]["row"]["outline"]:
                    changed.append(key)
                    self.assertNotEqual(_flank_problems(before, least=0.0), [])
                for board in ("row", "column"):
                    self.assertLessEqual(_outside_by(_stack_ring(before["boards"][board]), _stack_ring(result["boards"][board])), 1e-6, board)
                    self.assertEqual(result["boards"][board]["layers"], before["boards"][board]["layers"], board)
        self.assertEqual(changed, FLANK_CHANGED)


class SharedOutlineRegressionTests(unittest.TestCase):
    """The shared outline down to the tail roots (diagonal-bus/8, the plan's section 20.1) keeps sections 16 and 17 and
    meets a flush tail straight (tests/fixtures/diagonal_bus_shared_regressions.json)."""

    def test_the_sides_stay_straight_over_the_other_boards_staircase(self) -> None:
        # The design workflow judge's one-sided masked fine-pitch designs (fine:002 left and fine:011 right in their own
        # side mode, four more in others): the Column board's column ends step out beyond the Row field's chamfered
        # corner (section 16), so the union's side from the tip corner down to its widest point is a staircase; with the
        # straight sides' bound measured to its sharp inner corners (1.106 mm on fine:002) it stayed a filleted staircase,
        # measured to the outline as filleted (0.898 mm) it is one straight edge (section 17), as at 74e90cd: the same tip.
        for key, entry in sorted(SHARED_REGRESSIONS["straight"].items()):
            with self.subTest(case=key):
                full, result, before = generate_design(copy.deepcopy(entry["design"])), _unconvex(entry["design"]), _unstraight(entry["design"])
                _check_clean(self, full)
                self.assertEqual(_straight_problems(result, before), [])
                self.assertTrue(_straight_plan(before)[entry["side"]][0])
                row = result["boards"]["row"]
                for board in ("row", "column"):
                    side, _, _ = _side_walk(_stack_ring(result["boards"][board]), _shared_level(row), entry["side"] == "west")
                    least = min(x for x, _ in side)
                    self.assertEqual(next(k for k, point in enumerate(side) if point[0] <= least + EPSILON), 1, board)
                self.assertAlmostEqual(row["construction"]["row_bus"]["tip_width_mm"], entry["tip_width_mm"], delta=EPSILON)

    def test_a_side_meets_a_flush_tail_straight(self) -> None:
        # A tail flush with the shared outline's side: the funnel narrowing into a Row tail as wide as the union at the
        # level (the regressions' Row tails, centred since diagonal-bus/10, under the band before), or a Column tail wider
        # than the Row tail (the 2 x 61).  The union's points on the level stay while it is made regular, it runs on below
        # the level along the flush tail's side, and a tail corner a side meets at a slant stays a corner of the union: a
        # flat run merges into the tail's edge (the rectangular generator's 27 x 60 and 2 x 61, whose slanted side reached
        # the level 5.5 um outside the tail's edge and stepped back over 0.074 mm: vertices turning +4.97 and -4.24
        # degrees), or the corner is filleted on both boards and the level lowered below the fillet (rand:123, a
        # 1.36-degree concave corner left sharp); rand:238 was E_ROW_BUS_INFEASIBLE (the outlines parted at the level).
        # Since diagonal-bus/10 the fin face's third proposal with both (59 x 12, its 30 mm Row tail centred under the
        # 23.4 mm field, the union running straight down into both of the tail's edges) holds the last two: run on along
        # its last edge the union leaves 0.30- and 0.74-degree vertices at the level, its root corners merged it is
        # infeasible.  The union's points on the level are held by a seeded design of section 27.3's review (r2712:0469, a
        # 10 x 1 at 5 mm with 11 Row pins: its 6 mm Row tail centred under the 2.5 mm field, the union's fillets into the
        # tail's edges ending 58 nm above the level): merged, a side reaches the level 83 nm outside the tail's edge and
        # steps back (a 0.52-degree vertex on the Row board).  Both boards end the shared side on the flush tail's edge,
        # the board of that tail runs straight down it, and no vertex of either outline on or below the level turns by
        # under 5 degrees outside a fillet.
        for key, entry in sorted(SHARED_REGRESSIONS["flush"].items()):
            with self.subTest(case=key):
                result = generate_design(copy.deepcopy(entry["design"]))
                _check_clean(self, result)
                self.assertEqual(_irregular(result), [])
                west = entry["side"] == "west"
                tails = dict(zip(("row", "column"), _tails_down(result)))
                edges_ = {board: tail[0] if west else -tail[2] for board, tail in tails.items()}
                flush = min(edges_, key=lambda board: (edges_[board], board != entry.get("tail", "row")))
                edge = edges_[flush]
                level = _shared_level(result["boards"]["row"])
                for board in ("row", "column"):
                    side, following, _ = _side_walk(_stack_ring(result["boards"][board]), level, west)
                    self.assertAlmostEqual(side[-1][0], edge, delta=EPSILON, msg=board)
                    if board == flush:
                        self.assertAlmostEqual(following[0], edge, delta=EPSILON)
                        self.assertLess(following[1], level - 1.0)


# --------------------------------------------------------------------------
# The contract: the field, its codes, the identity extra, the pair cache.
# --------------------------------------------------------------------------


def _issues(result) -> list:
    return [(issue["code"], issue["field"]) for issue in result["validation"]["errors"]]


class ContractTests(unittest.TestCase):
    def test_the_values_and_their_codes(self) -> None:
        for value in ("up", "Both", 3, True, [], {"side": "left"}):
            with self.subTest(value=value):
                result = check_design(_request(4, 4, sides=value))
                self.assertEqual(_issues(result), [("E_ROW_SIDES", "routing.row_sides")])
                self.assertIsNone(result["design"]["routing"]["row_sides"])
                self.assertNotIn("row_bus", result["identity"])
        for value in SIDES:
            result = check_design(_request(4, 4, sides=value))
            self.assertTrue(result["ok"])
            self.assertEqual(result["design"]["routing"]["row_sides"], value)
        # null and "channel" are the straight channel on the surface template: the key is left out, so the build id is
        # the one without it ("channel" is recorded as normalized away).
        plain = check_design(_request(4, 4, sides=None))
        for value in (None, "channel"):
            with self.subTest(value=value):
                request = _request(4, 4, sides=None)
                request["routing"]["row_sides"] = value
                checked = check_design(request)
                self.assertTrue(checked["ok"])
                self.assertNotIn("row_sides", checked["design"]["routing"])
                self.assertEqual(checked["identity"]["build_id"], plain["identity"]["build_id"])
                self.assertNotIn("routing.row_sides", checked["validation"]["normalization"]["defaults_applied"])
                normalized = [entry for entry in checked["validation"]["normalization"]["values_normalized"] if entry["field"] == "routing.row_sides"]
                self.assertEqual(normalized, [] if value is None else [
                    {"field": "routing.row_sides", "from": "channel", "to": None, "reason": "the straight Row channel is this template's default"}])

    def test_the_generic_template_takes_the_field_and_defaults_to_the_bus(self) -> None:
        # P5-diagonal-bus.md section 18: the generic template accepts every value and always carries one (its default
        # both; channel for opposite tails or a strip of one row or column), recorded in defaults_applied; the bus adds
        # its version to the identity, the channel not.  Section 20: the bus takes CAD mode's rule set (tails of 7.5 mm
        # or more), the straight channel the generic profile's (7.0 mm).  tests/test_generic_bus.py builds them.
        request = _request(4, 4, sides="both")
        request["template_id"] = "generic_matrix_v1"
        for value in (*SIDES, "channel"):
            with self.subTest(value=value):
                request["routing"]["row_sides"] = value
                request["tail"]["bottom_length_mm"] = 7.5
                result = check_design(request)
                self.assertEqual(_issues(result), [])
                self.assertEqual(result["design"]["routing"]["row_sides"], value)
                self.assertEqual("row_bus" in result["identity"], value != "channel")
                self.assertNotIn("routing.row_sides", result["validation"]["normalization"]["defaults_applied"])
                request["tail"]["bottom_length_mm"] = 7.0
                self.assertEqual(_issues(check_design(request)), [] if value == "channel" else [("E_TAIL_LENGTH", "tail.bottom_length_mm")])
        for supplied in ({}, {"row_sides": None}):
            for tails, matrix, expected in ((("bottom", "bottom"), (4, 4), "both"), (("bottom", "top"), (4, 4), "channel"),
                                            (("left", "right"), (4, 4), "channel"), (("top", "top"), (1, 4), "channel"),
                                            (("top", "top"), (4, 1), "channel"), (("right", "right"), (2, 2), "both")):
                with self.subTest(supplied=supplied, tails=tails, matrix=matrix):
                    checked = check_design({"matrix": {"rows": matrix[0], "columns": matrix[1]}, "tail": {"row_side": tails[0], "column_side": tails[1]},
                                            "routing": dict(supplied)})
                    self.assertTrue(checked["ok"], checked["validation"]["errors"][:2])
                    self.assertEqual(checked["design"]["routing"]["row_sides"], expected)
                    self.assertEqual(checked["validation"]["normalization"]["defaults_applied"][-1], "routing.row_sides")
                    self.assertEqual("row_bus" in checked["identity"], expected != "channel")
        # A generic design built by hand without the key is the straight channel (as before the default).
        design = check_design({"matrix": {"rows": 4, "columns": 4}})["design"]
        del design["routing"]["row_sides"]
        self.assertEqual(validate_design(design)["errors"], [])
        self.assertNotIn("row_bus", template_identity(design))

    def test_opposite_tails_and_the_masks_a_straight_channel_refuses(self) -> None:
        for template in (SURFACE, "generic_matrix_v1"):
            for row_side, column_side in (("bottom", "top"), ("left", "right")):
                request = _request(4, 4, sides="left")
                request["template_id"] = template
                request["tail"].update(row_side=row_side, column_side=column_side, bottom_length_mm=7.5)
                self.assertEqual(_issues(check_design(request)), [("E_ROW_BUS_TAILS", "routing.row_sides")])
                self.assertIn("set routing.row_sides to 'channel'", check_design(request)["validation"]["errors"][0]["message"])
                request["routing"]["row_sides"] = "channel"
                self.assertEqual(_issues(check_design(request)), [])
        # A quarter turn is E_TAIL_SIDE_PARALLEL's alone (the electrodes would be parallel), with or without the bus.
        for sides in ("both", None):
            request = _request(6, 5, sides=sides)
            request["tail"].update(row_side="bottom", column_side="left")
            self.assertEqual(_issues(check_design(request)), [("E_TAIL_SIDE_PARALLEL", "tail.column_side")])
        # The straight classes refuse a mask whose rows stop short of the channel; the diagonal bus builds it.
        lower_left = [[1, row] for row in range(1, 9)]
        self.assertEqual(_issues(check_design(_request(8, 8, lower_left, sides=None))), [("E_MASK_ROUTING", "matrix.mask[0]")])
        for sides in SIDES:
            with self.subTest(sides=sides):
                result = generate_design(_request(8, 8, lower_left, sides=sides))
                _check_clean(self, result)
                self.assertEqual(mask_class(result["design"], PROFILE), ({"row": "diagonal", "column": "straight"}, None))
        self.assertEqual(mask_class(check_design(_request(4, 4, sides="both"))["design"], PROFILE), ({"row": "diagonal", "column": "straight"}, None))

    def test_an_infeasible_bus_builds_no_boards(self) -> None:
        diagonal._pair_text.cache_clear()
        with mock.patch.object(diagonal, "_construct", side_effect=diagonal.RowBusInfeasible("ROW_03 and ROW_05 come closer than the bundle pitch below the field.")):
            result = generate_design(_request(5, 5, sides="both"))
        diagonal._pair_text.cache_clear()
        self.assertFalse(result["ok"])
        self.assertEqual(result["boards"], {})
        self.assertEqual(_issues(result), [("E_ROW_BUS_INFEASIBLE", "routing.row_sides")])
        self.assertIn("bundle pitch", result["validation"]["errors"][0]["message"])

    def test_the_identity_extra(self) -> None:
        masked = generate_design(_named("equilateral", "both"))
        plain = generate_design(_request(5, 5, sides="left"))
        straight = generate_design(_request(5, 5, sides=None))
        self.assertEqual(ROW_BUS_VERSION, "diagonal-bus/11")
        self.assertEqual(IDENTITY_EXTRAS, ("template", "mask", "row_bus"))
        self.assertEqual(template_identity(masked["design"]), {"template": "surface-matrix/1", "mask": "field-mask/1", "row_bus": ROW_BUS_VERSION})
        self.assertEqual(template_identity(plain["design"]), {"template": "surface-matrix/1", "row_bus": ROW_BUS_VERSION})
        self.assertEqual(template_identity(straight["design"]), {"template": "surface-matrix/1"})
        self.assertNotIn("row_bus", straight["manifest"])
        for result, extras in ((masked, ("template", "mask", "row_bus")), (plain, ("template", "row_bus"))):
            manifest = result["manifest"]
            self.assertEqual(manifest["row_bus"], ROW_BUS_VERSION)
            hashed = {"design_sha256": manifest["design_sha256"], "profile_sha256": manifest["profile_sha256"],
                      "generator": manifest["generator"], "exporter": manifest["exporter"], **{key: manifest[key] for key in extras}}
            self.assertEqual(manifest["build_sha256"], hashlib.sha256(_canonical_json(hashed).encode("utf-8")).hexdigest())
            self.assertEqual(manifest["build_id"], check_design(result["design"])["identity"]["build_id"])
            self.assertTrue(direct_gerber._build_hash_recipe(manifest).endswith(", ".join(extras) + "}"))
            self.assertEqual(direct_gerber._identity_fields(manifest)["row_bus"], ROW_BUS_VERSION)
        self.assertNotEqual(plain["manifest"]["build_id"], straight["manifest"]["build_id"])

    def test_the_schema_and_the_catalogue(self) -> None:
        from engine import design_schema, input_limits, issue_codes

        surface = design_schema(PROFILE)["properties"]["routing"]
        generic = design_schema()["properties"]["routing"]
        for routing in (surface, generic):
            self.assertEqual(routing["properties"]["row_sides"]["type"], ["string", "null"])
            self.assertEqual(routing["properties"]["row_sides"]["enum"], ["left", "right", "both", "channel", None])
            self.assertEqual(routing["description"], "routing section: trace_width_mm, trace_space_mm; optional: row_sides.")
        self.assertEqual((surface["properties"]["row_sides"]["default"], generic["properties"]["row_sides"]["default"]), (None, "both"))
        self.assertEqual(input_limits(PROFILE)["routing.row_sides"]["default"], None)
        self.assertEqual(input_limits()["routing.row_sides"]["default"], "both")
        self.assertIn("'channel' where the tails leave on opposite sides or the field is a single row or column", generic["properties"]["row_sides"]["description"])
        self.assertIn("Null, absent or 'channel': the straight Row channel", surface["properties"]["row_sides"]["description"])
        self.assertIn("whole-degree caps of 60-85 degrees", generic["properties"]["row_sides"]["description"])
        for profile in (PROFILE, load_profile("generic_matrix_v1")):
            rules = [rule for rule in design_schema(profile)["x-cross-field-rules"] if rule.startswith("routing.row_sides")]
            self.assertEqual(len(rules), 1)
        catalogue = issue_codes()
        sources = {code: entry["source"] for kind in ("errors", "warnings") for code, entry in catalogue[kind].items()}
        self.assertEqual({code: sources[code] for code in ("E_ROW_SIDES", "E_ROW_BUS_TAILS", "E_ROW_BUS_INFEASIBLE", "W_STACK_TRACE_WINDOW")},
                         {"E_ROW_SIDES": "input", "E_ROW_BUS_TAILS": "input", "E_ROW_BUS_INFEASIBLE": "build", "W_STACK_TRACE_WINDOW": "drc"})
        # The served meanings state the rules the registration applies (the field window, one exit side; the tails stacked).
        meaning = catalogue["errors"]["E_REGISTRATION"]["meaning"]
        self.assertIn("over the other board's electrodes or its field window", meaning)
        self.assertIn("tails that leave on different sides", meaning)
        self.assertIn("stacked tails may overlap", meaning)
        for gone in ("degrees", "closer than", "within"):
            self.assertNotIn(gone, meaning)
        self.assertIn("diagonal-bus/11", catalogue["errors"]["E_ROW_BUS_INFEASIBLE"]["meaning"])
        self.assertIn("stacked where they meet", design_schema(PROFILE)["properties"]["routing"]["properties"]["row_sides"]["description"])
        self.assertIn("The Row tail is centred on the field in every side mode", design_schema(PROFILE)["properties"]["routing"]["properties"]["row_sides"]["description"])
        self.assertIn("share one outline down to their tail roots", design_schema(PROFILE)["properties"]["routing"]["properties"]["row_sides"]["description"])
        self.assertIn("at most 80 degrees", design_schema(PROFILE)["properties"]["routing"]["properties"]["row_sides"]["description"])
        self.assertIn("no corner turns by less than 5 degrees but on a fillet", design_schema(PROFILE)["properties"]["routing"]["properties"]["row_sides"]["description"])
        self.assertIn("each side from the tip corner down to its widest point is one straight line where one line encloses it within 1 mm",
                      design_schema(PROFILE)["properties"]["routing"]["properties"]["row_sides"]["description"])
        self.assertIn("E_TAIL_SIDE_PARALLEL", catalogue["errors"]["E_ROW_BUS_TAILS"]["meaning"])

    def test_lanes_closer_than_the_bundle_pitch_below_the_field_are_infeasible(self) -> None:
        # The construction's own check below the bands (none of the corpora meets it): adjacent lanes' centre lines,
        # here 0.1 mm apart at 4 mil (bundle pitch 0.2032 mm), name the pair; a clash builds no boards.
        design = check_design(_request(6, 5, sides="both"))["design"]
        geo = diagonal._Geo(design, diagonal.Rules(PROFILE), False)
        lines = {1: [[0.0, 0.0], [0.0, -5.0]], 3: [[0.1, 0.0], [0.1, -5.0]], 5: [[0.4, 0.0], [0.4, -5.0]]}
        self.assertEqual(diagonal._fan_clash([1, 3, 5], lines, geo), (1, 3))
        self.assertIsNone(diagonal._fan_clash([1, 5], lines, geo))
        diagonal._pair_text.cache_clear()
        with mock.patch.object(diagonal, "_fan_clash", return_value=(3, 5)):
            result = generate_design(_request(6, 5, sides="both"))
        diagonal._pair_text.cache_clear()
        self.assertEqual(_issues(result), [("E_ROW_BUS_INFEASIBLE", "routing.row_sides")])
        self.assertIn("ROW_03 and ROW_05 come closer than the bundle pitch below the field", result["validation"]["errors"][0]["message"])

    def test_lanes_that_cannot_turn_down_on_the_field_raise_the_bottom_corner(self) -> None:
        # The safety net of the cut (none of the 1369 designs of the reviews needs it): where a lane cannot turn down on
        # the field's bottom edge, the bottom row's corner is raised onto it before the onion is built, and the boards
        # build clean with two bends per Row trace below the field.
        diagonal._pair_text.cache_clear()
        calls = []

        def blocked(*args, **kwargs):
            calls.append(1)
            raise diagonal._CutBlocked("ROW_32's lane cannot turn down on the field's bottom edge.")

        with mock.patch.object(diagonal, "_cut_at_field", side_effect=blocked):
            result = generate_design(_named("rectangle", "left"))
        diagonal._pair_text.cache_clear()
        self.assertEqual(len(calls), 1)
        _check_clean(self, result)
        # The cut lanes keep the bands of diagonal-bus/1; the raised corner moves its onion (outward, a little here).
        cut = generate_design(_named("rectangle", "left"))["boards"]["row"]
        self.assertNotEqual(_band_extents(result["boards"]["row"]), _band_extents(cut))

    def test_the_pair_is_built_once_and_each_caller_gets_its_own_copy(self) -> None:
        design = check_design(_request(6, 5, sides="both"))["design"]
        diagonal._pair_text.cache_clear()
        with mock.patch.object(diagonal, "_construct", wraps=diagonal._construct) as construct:
            first = diagonal.build_row_board(design, PROFILE)
            column = diagonal.build_column_board(design, PROFILE)
            first["outline"]["points"].clear()
            again = diagonal.build_row_board(design, PROFILE)
        self.assertEqual(construct.call_count, 1)
        self.assertTrue(again["outline"]["points"])
        self.assertEqual(column["role"], "columns")


# --------------------------------------------------------------------------
# Determinism.
# --------------------------------------------------------------------------


def _notched(rows: int, columns: int, cut: int) -> list:
    """A rows x columns mask missing a staircase of ``cut`` cells at each corner (1-based spans, ROW_01 first)."""

    spans = []
    for k in range(rows):
        edge = min(k, rows - 1 - k)
        spans.append([1 + max(0, cut - edge), columns - max(0, cut - edge)])
    return spans


def _staircase(design: dict) -> dict:
    """The design built with F's own staircase in place of its hull and without the convex sides (diagonal-bus/5's
    outline: the convex sides would bridge its notches too), the pair cache cleared."""

    diagonal._pair_text.cache_clear()
    pieces = lambda slabs, depth: ([[[start, low], [start, high]] for low, high, start, _ in slabs], [[[end, low], [end, high]] for low, high, _, end in slabs])
    try:
        with mock.patch.object(diagonal, "_hull_sides", side_effect=pieces), mock.patch.object(diagonal, "_convex_sides", side_effect=_no_convex):
            return generate_design(copy.deepcopy(design))
    finally:
        diagonal._pair_text.cache_clear()


class ChamferTests(unittest.TestCase):
    """The user's decision (P5-diagonal-bus.md section 16): where a masked field misses cells at a corner, both boards
    cross the notch on F's convex hull (a chamfer, or a polygon following F), never a staircase; the copper is the
    staircase build's, its outline inside the chamfered one."""

    def test_notched_fields_on_every_side(self) -> None:
        for cut, sides, top in ((1, "both", "rows"), (2, "both", "columns"), (1, "left", "rows"), (2, "right", "rows"), (3, "both", "rows")):
            design = _request(18, 14, _notched(18, 14, cut), sides=sides, top=top)
            with self.subTest(cut=cut, sides=sides, top=top):
                result = generate_design(design)
                _check_clean(self, result)
                self.assertEqual(_staircase_problems(result), [])
                old = _staircase(design)
                self.assertTrue(old["ok"])
                self.assertNotEqual(_staircase_problems(old), [])  # the staircase build has outline vertices inside the hull
                for key in ("row", "column"):
                    self.assertEqual(old["boards"][key]["layers"], result["boards"][key]["layers"])
                    self.assertLessEqual(_outside_by(old["boards"][key]["outline"]["points"], result["boards"][key]["outline"]["points"]), FILLET_STEP)

    def test_a_full_field_keeps_its_outline(self) -> None:
        # No notch, no hull: an unmasked diagonal design never calls it.
        design = _request(18, 14, sides="both")
        with mock.patch.object(diagonal, "_hull_sides", side_effect=AssertionError("hull of a full field")):
            diagonal._pair_text.cache_clear()
            try:
                self.assertTrue(generate_design(design)["ok"])
            finally:
                diagonal._pair_text.cache_clear()


def _digest_builds() -> str:
    """The boards of the named corpus with both sides and the mirrored crank and disk, hashed."""

    boards = []
    for key in (*((name, "both") for name in ("rectangle", "soft finger", "crank", "equilateral", "disk")), ("crank", "left"), ("disk", "left")):
        result = generate_design(_named(*key))
        boards.append([result["manifest"]["build_id"], result["boards"]])
    return hashlib.sha256(_canonical_json(boards).encode("utf-8")).hexdigest()


class DeterminismTests(unittest.TestCase):
    def test_the_pinned_digest(self) -> None:
        # The same on Python 3.9.6 and 3.12 (both ran this test), and with any hash seed (below).
        self.assertEqual(_digest_builds(), DIGEST)

    def test_the_digest_with_other_hash_seeds(self) -> None:
        code = "import sys; sys.path.insert(0, 'tests'); import test_diagonal_bus as t; print(t._digest_builds())"
        for seed in ("0", "123"):
            with self.subTest(seed=seed):
                environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
                output = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
                self.assertEqual(output.stdout.strip(), DIGEST)

    def test_the_construction_sums_no_floats_and_iterates_no_sets(self) -> None:
        functions = [value for _, value in sorted(vars(diagonal).items()) if inspect.isfunction(value) and value.__module__ == diagonal.__name__]
        functions += [value for _, value in sorted(vars(diagonal._Geo).items()) if inspect.isfunction(value)]
        # The registration's stack keys and the contract of the field.
        functions += [drc._row_bus_kind, drc._row_bus_record, drc._row_bus_registration, drc._field_outline, drc._stacked_tail,
                      drc._stacked_trace_windows, drc._segment_ring_gap, drc._trace_crossings, core._normalize_row_sides, core._row_sides_message,
                      engine_geometry.clip_ring_above, engine_geometry.ring_deviation, engine_geometry.fillet_concave_corners]
        self.assertGreater(len(functions), 20)
        for function in functions:
            with self.subTest(function=function.__qualname__):
                self.assertEqual(_determinism_problems(function), [])
        tree = ast.parse((ROOT / "engine" / "diagonal.py").read_text(encoding="utf-8"))
        used = sorted({node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "math"})
        # No hypot or dist (CPython's own, whose last bit moved in 3.10); the hull work is integer (engine.bus).
        # sqrt: correctly rounded everywhere.
        self.assertEqual(used, ["atan2", "cos", "degrees", "pi", "sin", "sqrt"])
        imports = sorted({node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
                         | {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names})
        self.assertEqual(imports, ["", "__future__", "bus", "functools", "geometry", "json", "layout", "math", "typing"])


FINE_WARNED = 2
# diagonal-bus/10 (the plan's section 27, the user's request: "some tails are not within the sensor's width"): the
# one-sided regressions' funnels, their whole bundles fanning inward to the Row tail centred under the field, lie deeper
# than diagonal-bus/2's bound by this much (measured: edge:035 0.253 mm, reader:029 1.382, rv:063 0.846, rv:186 2.424,
# wide:138 0.654; mirrored reader tails among them, whose rows' contacts lie at the tail's far end from the band).
REGRESSION_CENTRED_COST = {"edge:035": 0.26, "reader:029": 1.39, "rv:063": 0.85, "rv:186": 2.43, "wide:138": 0.66}
# diagonal-bus/8 (one outline down to the tail roots, the Column V capped at 80 degrees, the plan's section 20): Python
# 3.9.6 and 3.12 alike.  Re-pinned by section 23 (the surface profile's tails to 200 mm): the build ids change with the
# profile's digest, the boards not (before: 9c368137...).  Rewritten by section 24 (diagonal-bus/9, convex sides): the
# build ids, and the crank's, the equilateral's and the disk's outlines (ConvexSideTests); Python 3.9.6 and 3.12 alike
# (before: ad1d5a01...).  Rewritten by section 27 (diagonal-bus/10, the Row tail centred on the field, the user's request
# "some tails are not within the sensor's width"): the build ids, the Row tails of every build (with both by up to 0.2
# mm), the mirrored crank's and disk's whole Row and Column boards below the field (one side's fans inward under it);
# Python 3.9.6 and 3.12 alike (before: 1dafc17e...).  Rewritten by section 27.8 (diagonal-bus/11, the convex flank, the
# multi-gripper video's notch): the build ids, and the one-sided builds' outlines on the side without the bus (the notch
# below the field's outline corner bridged; the copper, the tails and the roots the same); Python 3.9.6 and 3.12 alike
# (before: dfd99419...).  Re-pinned by the profile revision 2026-10-29 (the gold-finger thickness order option and the
# coverlay-window notes): the build ids change with the profiles' digests, the boards not (before: 7e03aa07...).
# Re-pinned by the profile revision 2026-11-06 (the order: JLC's 2-layer 0.2 mm FPC, the bottom copper empty): the build
# ids change with the profiles' digests, the boards not (before: 82d8a2c9...).
DIGEST = "6c34e7e9562aaeb3c4cb228d3675aa105d03b45e2b09ca61f01df7d2cd79d809"
# StraightSideTests: the sides whose upper stretch takes the line and those that keep their polyline (the named corpus,
# the regressions and the user's cases).  diagonal-bus/10 (the Row tail centred): 19, 34 -> 21, 36: reader:011's and
# reader:015's west sides take the line (their stretch down to the widest point within 1.0 mm of one now), and the inner
# flanks of the soft finger one-sided, rv:186 and wide:138, whose centred tails reach beyond F's side (the slant below F's
# bottom, their widest point), keep their polyline.
STRAIGHTENED, KEPT = 21, 36
# ConvexSideTests: the cases whose outline the convex sides change (section 24): a kink beside a narrow tip or a short
# step bridged.  The rectangle and the soft finger in every side mode keep theirs (straight sides already).  Since
# diagonal-bus/10 (the Row tail centred) reader:011's side keeps it too: its funnel's split on the field's centre line, its
# side from the tip corner down to its widest point has no dent left to bridge.
# The one-sided named builds and regressions whose flank the convex flank changes (diagonal-bus/11: the Column fan-out's
# notch below the field's outline corner bridged, 0.12-0.40 mm deep, adding 0.14-1.06 mm2): every one of them.
FLANK_CHANGED = ["rectangle|left", "rectangle|right", "soft finger|left", "soft finger|right", "crank|left", "crank|right", "equilateral|left",
                 "equilateral|right", "disk|left", "disk|right", "fine:028", "reader:015", "reader:029", "rv:063", "rv:186"]
CONVEX_CHANGED = ["crank_32x32_masked|both", "crank|both", "crank|left", "equilateral|both", "equilateral|left", "equilateral|right", "disk|both",
                  "disk|left", "disk|right", "edge:035", "rand:034", "rand:087", "reader:014", "reader:029", "rv:063", "rv:186"]


if __name__ == "__main__":
    if "--write-shared-fixture" in sys.argv[1:]:
        write_shared_fixture()
    else:
        unittest.main()
