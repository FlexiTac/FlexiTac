#!/usr/bin/env python3
"""Mutation check: does the test suite notice known defects?

Each mutant is a small source edit that re-introduces a defect.  It is
applied to a fresh scratch copy of the project (with the CI workflow beside
it; the working tree is never touched) and the full stdlib suite runs
there; a failing suite *kills* the mutant.  The catalogue has two parts:

* ``audit/*``: the 36 baseline mutants of the 2026-10-12 audit (finding H4,
  ``claude/verification/2026-10-12-audit-report.md``) and the extras written
  while fixing C1, re-expressed for the current code.  The audit wrote them
  against the 0.1.x engine; each entry names the audit id and edits the code
  that now does the same job.  ``audit/x`` is the exception: its defect, the
  missing E_DUAL_LANE_WIDTH check, is the intended behaviour since
  2026-10-15, so it now drops the minimum slot of a narrow fan-out instead.
* ``E/*``, ``API/*``, ``X/*``, ``T/*``, ``G/*``: mutants of what the fix
  stages added (engine geometry and whole-board DRC, the API/HTTP/CLI
  surface, the exporter, the stage-T tests and documents, and the stage-G
  order requirements and gold fingers).
* ``S/*``: mutants of CAD mode (the ``surface`` package and its HTTP routes,
  2026-10-20).
* ``M/*``: mutants of the masked taxel field (``matrix.mask``,
  claude/specs/masked-field/PLAN.md), from phase P1 (2026-10-21): the
  contract, the identity, the frames and construction classes and the size
  advice; from phase P2: the class gate and the masked boards' builders
  (stub ends, lane taper, fillers, windows, the turn, the outlines and the
  registration keys), and their DRC and registration (the margin around
  the crossing region, the polygon window's records, the strict
  window-to-trace rule, the stack frame, the crossings and the masked grid),
  and from the P2 reviews' fixes (the masked grid across the electrodes,
  the window touching the outline or a cutout, P off the board, the trace
  overlap report, and the exporter and the map refusing masked builds).
  The ``DIAGONAL`` group holds the ``M/`` mutants of the diagonal Row bus
  (claude/specs/masked-field/P5-diagonal-bus.md), from phase P5a
  (2026-10-21): the integer-nanometre primitives of ``engine/bus.py``;
  and from phase P5b, re-expressed for the construction ``diagonal-bus/2``
  of ``engine/diagonal.py``: own zones, the bands' keep-out, starts, hold,
  the Row tail's root, contacts, sides, split, the DRC gate and the tail
  rules of the registration, and the contract (the identity extra, the
  generic refusal, E_ROW_BUS_INFEASIBLE); and from phase P5c: the exports
  (the taxel map and the order note of an unmasked bus, the review
  manifest's record of the bus and its read-back against ``pinout.csv``);
  and from the P5 reviews' fixes: the stack trace gap of the bands'
  keep-out, the flat lanes and the relative narrow tip of the record, and
  ``E_ROW_BUS_TAILS`` for opposite tails only; and from the tail redesign
  (P5f, 2026-10-22, the plan's section 12): the bottom row's corner on the
  field's edge, the fans' pitch, stagger, entry-angle guard and clash
  check, the contacts, the funnel's split, the one-sided tail under the
  band, and the registration's field window.  diagonal-bus/1's
  stack-rule mutants (the stub drop, D_clear, the jog, the bundle limit,
  the crossing floor, the overlap error, the corridor and descent gaps,
  the beside measure) are retired with it; and from the stacked tails
  (P5g, diagonal-bus/3, the plan's section 13): the Column board the
  straight one (no neck, its classes), the funnel's Row tail centred, and
  the registration's field and exit-side checks and its tail overlap,
  with diagonal-bus/2's side-by-side mutants (the fallback beside the
  Column tail, the Column tail's side and neck, the tail clearance and
  gap) retired; and from the shared outline (P5h, diagonal-bus/4, the
  plan's section 14): no shared outline, one cut at the field's edge or
  at the window level (retired with section 20), one of the Row board alone, sharp joins, no ear
  under a shared fillet, and the registration not checking it or passing
  a board without the level; and from the user's later decisions on it
  (the plan's section 14.2): the stacked Column copper back in the bands'
  keep-out (which retires P5b's mutant leaving it out), and the lanes of a
  receding field running straight down from their westmost point, ignoring
  the inner lanes at the field's edge, leaning past the taper cap, or
  spreading at their inward turn; and from the regular outlines (P5k,
  diagonal-bus/5, the plan's section 15): the outlines not made regular,
  the 5-degree threshold ignored, a merged run's edge its chord (cutting
  inside), the fillets not kept while the union is made regular (retired
  with section 20), the new corners left sharp, and the tails made regular too; and from the
  chamfered notches (diagonal-bus/6, the plan's section 16): the chamfer
  the hull of P (cutting inside F) and no chamfer at all; and from the
  straight sides (diagonal-bus/7, the plan's section 17): no straight
  sides, the 1.0 mm bound ignored, and the upper line the chord from the
  tip corner (not enclosing the side); and from the centred Row tail
  (diagonal-bus/10, the plan's section 27, 2026-10-27): the tail a contact
  pitch off the field's centre, the funnel's old split midway between the
  innermost lanes, one side's old tail under the band, the mirrored rows
  on the tail's near end, and one side's inner flank with its ledge along
  F's bottom back or slanting out however flat (P5f's and P5g's placement
  mutants retired with the code they mutated); and from its review (the
  plan's section 27.3): the inner flank slanting out only within half its
  drop, slanting to the tail's root instead of its hold, or not made
  monotone.  The ``FIELD_FIT`` group
  holds those of phase P5d: CAD mode's field-only containment
  (``surface/fieldfit.py``: the dispatch, the DP and its bounds, the
  fillers, the reader caps, the turn threshold, the narrow tip, F's walls,
  the tails' run, the mask's mirror, the sides) and its map (the records,
  the readout's contact order), and the P5c carry-overs
  (``field_footprint`` and ``E_BOARD_SIZE`` on the diagonal boards, the
  folded Row pins in ``ORDER_NOTES.txt``); and those of phase P5e: the
  default flip (``containment: field`` with ``shape: fill``), the map's
  containment taken from the design, the field fit's no-fit reason, and
  the browser client's Row traces and Containment (``formBody``, the
  template guard, ``setForm``, the select sync, the flat view's clip); and
  those of the P5d/P5e reviews' fixes (2026-10-22): the search (an
  unturned lattice pruned by unturned fields only, phase 0 on the usable
  edge, the quarter phases on every exit, the whole lattice first, the
  phase-aware early exit, the rectangle's pruning, the work budget, the
  frames tried, the narrow tip choosing the exit), the tails' ends
  (since the plan's section 27.3 on one line across the boards: each
  tail's own end back, and, from its review, the line pushed by the
  review's shared reach, whose mutant of each tail's own reach is
  retired with it, and from the review of 27.4 a tail reaching the line
  rounded down), the routing report (the overhang without the tails,
  the holes, a fillet's inner edges, the base edge), the map (a straight
  design's F, the Row pins by pin), the one-sided order note, and the
  browser client (the badge and the CSV of a full field, the pins from
  the pads, the stale Generate, one map request at a time); and those of
  the user's corner tolerance (the plan's section 16, 2026-10-23): the
  zones along F's whole sides (a general widening), the zones reaching
  into P (a corner taxel off the surface) and every row's corners tolerant
  (the rectangle preference's two retired with section 26.16); and
  those of the rectangular generator's diagonal Row bus (the plan's section
  18, 2026-10-24): the default flip off, the generic refusal back, the
  60-degree fans on the standard profile, ``channel`` ignored or kept on
  the surface template, the fans' start on the standard profile, the
  careful pass off (the three of the standard profile retired with section
  20), and the browser's Row traces select in Rectangular mode; and those
  of its one Column V (the plan's section 19): the bus's rule set reaching
  the straight channel's Column board and the Row fans' guard off the old
  60-degree Column entry; and those of the rectangular
  generator as a subset of CAD mode (diagonal-bus/8, the plan's section
  20): a rule of the rectangular generator's own (parity broken), the
  shared outline stopping at F's bottom, the tails' roots above the
  union's fillets, the Column V never or always capped, the straight
  channel's default tail, its served column bound, and the side overhang
  where a straight side crosses the surface's lowest level; and those of
  the user's correction, coverage first (the plan's section 21,
  2026-10-25): the shaped fields' and the masked walk's caps back at
  32 x 32 (retiring P4's M/fill-shaped-64) and reader auto uncapped (the
  rectangle preference's two retired with section 26.16); and those of
  symmetric faces (the plan's section 22, 2026-10-25): no face symmetric,
  an asymmetric row accepted as symmetric, the symmetric DP's runs shifted
  and a symmetric exit turned (a symmetric field first however few taxels
  it has retired with section 26.17, whose rule it was, and a defect again
  since section 26.19, M/sec26-symmetric-without-threshold); and those of
  the caps (the plan's section 23, 2026-10-25): the caps choosing the exit
  again, a capped field's rows taken next to the exit instead of at the
  fingertip, and the surface's tails held at 80 mm again, and from the
  review of the plan's section 27.4 (27.5) the 200 mm cap's search not run
  again nearer the exit and its refusal off; and those of the corner
  tolerance at every convex corner and the convex sides (the plan's
  section 24, diagonal-bus/9): aligned ends exempted in F's check or half
  in the DP, convex corners held in the DP (section 16's rule) or in F's
  check, the symmetric DP's old rule, no convex sides, and the hull's
  bound ignored; and those of the taxels from the fingertip (the plan's
  section 26, 2026-10-26): the rectangle's zones read before its column
  cap, the filler band between rows unchecked or held over the lower
  row's whole run, phase 2 without the band's start and phase 3 without
  its own band, the tip share ignored or measured from the lead, the
  slack a quarter pitch or none, the full guard removed, one group across
  the exits, the displaced lead dropped, the proposal key without the
  tip-first flag, a full lead's window ignored; its round 2 (26.15): the
  lead's zero-cost tie dropped, ``tip_first: false`` taking the share or
  skipping the step, the reach after the corner count, the centred phases
  dropped, the tails' reach ignored, the peel fallback removed or on the
  floor only; and its round 3c (26.16: reach first, CAD mode without
  rectangles): the pass dropping the lead's ties short of the tip-first
  field or stopping at its reach, a fit taking shape rectangle, the
  generic template or a rectangle preference silently, and the map
  refusing a saved placement that names them (the tip-first rectangles'
  three and round 2's tip-zone guard, tie-break, rectangle floor and
  column guard mutants retired with what they mutated, and with them
  P4's shape fill on the generic template, the browser's Field shape and
  Containment on the Rectangular board rules and the CAD fit's shape per
  pitch); and those of round 3c's review (26.17): the lead proposed
  beside its zero-cost tie, a tie peeled under the lead's taxels kept in
  its place, the displaced field's rank only when proposed itself, the
  taxels given counted from the lead and the map taking any value of the
  removed options; and those of the user's decision of 2026-10-27 (26.17:
  symmetric faces take a symmetric sensor): a symmetric field leading only
  within 3 % again and a symmetric group's tip share measured from every
  field; and round 3c's review's test gaps: T0 without its p / 8 slack, T0
  of exactly the lead's taxels and the pass's floor only at the farthest
  reach; and those of round 4's review (26.18): only the first exit of the
  fit without the caps searched on its own under them, those exits in their
  own order or all searched before the first field is built, a symmetric
  group's tip pass on the quarter row phases only and its slack a whole
  eighth phase, the taxels given counted from the share's M, the map taking
  on the generic template what a fit then refused, a tip-first tie taking
  the lead's place peeled under its taxels, the tie's peel check on a
  tip-first tie and a tie's equal peel refused (the verifier's MU4, MU19
  and MU13).  The ``BORDER`` group holds the
  ``S/`` mutants of CAD mode's border of the taxels (docs/CAD_BORDER.md,
  2026-10-25): the border ignored in the field fit's lattice, the map's
  ``taxels_inside_border`` never failing, and ``base.border_edge`` taken
  as the next edge.  The ``EASYEDA`` group holds the ``X/easyeda-`` mutants
  of the EasyEDA Pro projects (exporters/easyeda_pro.py,
  docs/EASYEDA_EXPORT.md, 2026-10-25): the stiffener's material name and a
  hard-coded thickness, a pad's net dropped, the outline and the coverlay
  on the wrong layers, FPC mode off, the pads' own mask openings, the
  track-to-pad rule without the electrodes, the rules rounded instead of
  floored, EasyEDA's element numbering off by one, a deflated project, the
  schematic channel broken, the routed cutouts dropped, the HTTP route and
  the web button, and the comparison tool's even-odd outline fill.

A mutant may be marked ``expect="survive"`` with the reason (an equivalent
change, or behaviour outside the stdlib suite); every other survivor is a
test gap.  A control mutant may name the only tests allowed to kill it
(``killers``); a kill by any other test is a false alarm.  Each mutant's
suite runs with ``FPC_MUTANT=<id>`` in its environment, so the suite's own
check that every catalogue edit applies skips itself in that copy.  This
script is a development tool: it lives outside ``tests/`` and is never
collected by ``unittest discover``.

Usage::

    python3 tools/mutation_check.py                 # every mutant, parallel
    python3 tools/mutation_check.py --list          # catalogue only
    python3 tools/mutation_check.py --check         # do all edits still apply?
    python3 tools/mutation_check.py --only audit/ T/chirality --jobs 8 --json out.json

Exit status: 0 when the baseline passes and every mutant not marked
``survive`` is killed; 1 when a mutant survives unexpectedly; 2 when the
baseline fails or an edit no longer applies (the catalogue needs updating).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple, Sequence

PROJECT = Path(__file__).resolve().parents[1]
WORKFLOW = PROJECT.parent / ".github" / "workflows" / "fpc-agentic-customization.yml"
# Seconds a mutant's suite run may take before it counts as a kill (--timeout).  One run of the whole suite took 670 to
# 1900 s on the development host on 2026-11-06, by its load (the baseline 1393 s), and up to about 1700 s on a GitHub
# runner, so the 900 s of before read every mutant KILLED by its timeout; 5400 s leaves room for a loaded host
# (tools/README.md).
SUITE_TIMEOUT = 5400.0
CORE = "engine/core.py"
LAYOUT = "engine/layout.py"
DRC = "engine/drc.py"
GEOMETRY = "engine/geometry.py"
PROFILE_PY = "engine/profile.py"
SCHEMA = "engine/schema.py"
PROFILE = "profiles/jlc_fpc_standard_v1.json"
GERBER = "exporters/direct_gerber.py"
IPC = "exporters/ipc356.py"
APP = "app.py"
CLI = "cli.py"
WEB = "web/app.js"


class Mutant(NamedTuple):
    id: str
    origin: str
    description: str
    edits: tuple  # ((relative path, old text, new text), ...); each old text must occur exactly once
    expect: str = "killed"
    reason: str = ""
    killers: tuple = ()  # test-name prefixes; when set, no other test may fail


def m(id: str, origin: str, description: str, *edits: tuple, expect: str = "killed", reason: str = "", killers: tuple = ()) -> Mutant:
    return Mutant(id, origin, description, tuple(edits), expect, reason, tuple(killers))


# --------------------------------------------------------------------------
# The audit's mutant set (H4), re-expressed for the current code.
# --------------------------------------------------------------------------

AUDIT = (
    m("audit/a_rev", "audit a (C1)", "pads written with lower-left semantics again (the original C1 defect)",
      (GERBER, "        lines.extend(_region(rect_corners(rectangle)))\n",
       '        lines.extend(_region(rect_corners(dict(rectangle, anchor="lower_left"))))\n')),
    m("audit/b", "audit b", "the model stores each contact's lower-left corner while it is read as its centre",
      (GEOMETRY, '    if anchor == "center":\n        x, y = (x0 + x1) / 2, (y0 + y1) / 2\n',
       '    if anchor == "center":\n        x, y = x0, y0\n')),
    m("audit/c", "audit c", "coverlay expansion negated (openings shrink instead of grow)",
      (LAYOUT, "    expansion = rules.expansion\n", "    expansion = -rules.expansion\n")),
    m("audit/d", "audit d", "route-to-route clearance violations raise no E_ROUTE_CLEARANCE",
      (DRC, '    "route_route_clearance": ("E_ROUTE_CLEARANCE", _ROUTES),\n', "")),
    m("audit/e", "audit e (H3)", "copper-to-edge rule 0 in the profile",
      (PROFILE, '"copper_to_edge_mm": 0.3,', '"copper_to_edge_mm": 0.0,')),
    m("audit/e2", "audit e (H3)", "copper-to-edge rule and the JLC capability both lowered to 0.2 mm (a consistent profile)",
      (PROFILE, '"copper_to_edge_mm": 0.3,', '"copper_to_edge_mm": 0.2,'),
      (PROFILE, '"copper_to_board_edge_mm": 0.3,', '"copper_to_board_edge_mm": 0.2,')),
    m("audit/f1", "audit f1", "quarter turn (right) is a mirror [y, x] instead of a rotation",
      (GEOMETRY, "    if turns == 1:\n        return [-y, x]\n", "    if turns == 1:\n        return [y, x]\n")),
    m("audit/f2", "audit f2", "quarter turn (right) rotates the wrong way: right behaves as left",
      (GEOMETRY, "    if turns == 1:\n        return [-y, x]\n", "    if turns == 1:\n        return [y, -x]\n")),
    m("audit/g", "audit g", "the Column board is never rotated or normalised to the origin",
      (CORE, '    apply_tail_side(column_board, design["tail"]["column_side"])\n', "    pass  # mutant\n")),
    m("audit/h", "audit h", "physical top/bottom tail lengths swapped between the roles",
      (LAYOUT, '    physical_side = "top" if design["role_mapping"]["top"] == role else "bottom"\n',
       '    physical_side = "bottom" if design["role_mapping"]["top"] == role else "top"\n')),
    m("audit/i", "audit i", "GTS written without any opening",
      (GERBER, '    for opening in board["layers"]["top_coverlay_openings"]:\n        lines.extend(_region(rect_corners(opening)))\n',
       "    for opening in []:\n        lines.extend(_region(rect_corners(opening)))\n")),
    m("audit/j", "audit j", "jlcpcb.json stiffener thickness hard-coded to 0.1",
      (GERBER, '                "thickness": group["thickness"],\n', '                "thickness": "0.1",\n')),
    m("audit/k", "audit k", "routed cutouts (the slot) missing from the GKO, writer and read-back alike",
      (GERBER, '    return [board["outline"]["points"], *board["outline"].get("cutouts", [])]\n',
       '    return [board["outline"]["points"]]\n')),
    m("audit/l", "audit l", "channel-order mapping inverted",
      (LAYOUT, '    return position if order == "ascending" else pins - position + 1\n',
       '    return pins - position + 1 if order == "ascending" else position\n')),
    m("audit/m1", "audit m1", "every electrode moved 0.5 mm toward an outline edge (Row +Y, Column -X)",
      (LAYOUT, '"row_electrode", (electrode_left, center_y - row_width / 2, electrode_right, center_y + row_width / 2)',
       '"row_electrode", (electrode_left, center_y - row_width / 2 + 0.5, electrode_right, center_y + row_width / 2 + 0.5)'),
      (LAYOUT, '"column_electrode", (middle - half, electrode_bottom, middle + half, electrode_top)',
       '"column_electrode", (middle - half - 0.5, electrode_bottom, middle + half - 0.5, electrode_top)')),
    m("audit/m2", "audit m2", "Column electrodes moved +0.5 mm in Y (route end leaves the electrode: open circuit)",
      (LAYOUT, '"column_electrode", (middle - half, electrode_bottom, middle + half, electrode_top)',
       '"column_electrode", (middle - half, electrode_bottom + 0.5, middle + half, electrode_top + 0.5)')),
    m("audit/n", "audit n", "route-to-edge violations raise no E_ROUTE_EDGE_CLEARANCE",
      (DRC, '    "route_to_outline": ("E_ROUTE_EDGE_CLEARANCE", _ROUTES),\n', "")),
    m("audit/o", "audit o", "copper outside the outline raises no E_COPPER_OUTLINE",
      (DRC, '    "copper_inside_outline": ("E_COPPER_OUTLINE", "outline.points"),\n', "")),
    m("audit/p", "audit p", "export gate on ok removed",
      (GERBER, '    if result.get("ok") is not True:\n        raise ExportError("Direct Gerber export is blocked because design validation did not pass.")\n',
       "    pass\n")),
    m("audit/p2", "audit p2", "export gates on ok and on geometry_valid removed",
      (GERBER, '    if result.get("ok") is not True:\n        raise ExportError("Direct Gerber export is blocked because design validation did not pass.")\n',
       "    pass\n"),
      (GERBER, '    if manifest.get("geometry_valid") is not True:\n        raise ExportError("Direct Gerber export is blocked because geometry is not valid.")\n',
       "    pass\n")),
    m("audit/q", "audit q", "ZIP member timestamps from the wall clock (non-deterministic)",
      (GERBER, "            info = ZipInfo(filename=name, date_time=_ZIP_TIMESTAMP)\n",
       '            info = ZipInfo(filename=name, date_time=__import__("time").localtime()[:6])\n')),
    m("audit/t", "audit t", "half turn (top) is a mirror [x, -y] instead of a rotation: right tail side, wrong chirality",
      (GEOMETRY, "    if turns == 2:\n        return [-x, -y]\n", "    if turns == 2:\n        return [x, -y]\n")),
    m("audit/u", "audit u", "SVG preview omits the connector pads",
      (CORE, "{routes}{electrodes}{pads}{_pin1_marker(board)}", "{routes}{electrodes}{_pin1_marker(board)}")),
    m("audit/v", "audit v", "static path containment check removed (directory traversal)",
      (APP, "            found = WEB_ROOT.resolve() in candidate.parents and candidate.is_file()\n",
       "            found = candidate.is_file()\n")),
    m("audit/w", "audit w", "route clearance-violation pair counter disabled",
      (DRC, '                route_pair["violations"] += 1\n', '                route_pair["violations"] += 0\n')),
    m("audit/x", "audit x", "a narrow two-lane fan-out drops the minimum slot (the audit removed the E_DUAL_LANE_WIDTH check; "
      "since 2026-10-15 such a fan-out spreads wider than the body instead, keeping the slot)",
      (LAYOUT, "        slot_width = max(min(rules.slot_width, available), rules.min_slot_width)\n",
       "        slot_width = min(rules.slot_width, available)\n")),
    m("audit/aa", "audit aa", "top and bottom Gerber ZIPs swapped",
      (GERBER, '        board = build["boards_by_side"][side]\n        groups = build',
       '        board = build["boards_by_side"]["bottom" if side == "top" else "top"]\n        groups = build')),
    m("audit/bb", "audit bb", "the contact window treats contact centres as lower-left corners (misregistered opening)",
      (LAYOUT, "    contact_boxes = [rect_bounds(pad) for pad in pads]\n",
       '    contact_boxes = [rect_bounds(dict(pad, anchor="lower_left")) for pad in pads]\n')),
    m("audit/cc", "audit cc", "design digest is a constant (build identity ignores the design)",
      (CORE, "    design_sha256 = _sha256(_canonical_json(design))\n", '    design_sha256 = _sha256("constant")\n')),
    m("audit/dd", "audit dd", "copper-to-slot violations raise no E_COPPER_CUTOUT_CLEARANCE",
      (DRC, '    "copper_to_cutout": ("E_COPPER_CUTOUT_CLEARANCE", "outline.cutouts"),\n', "")),
    m("audit/ee", "audit ee", "fan-out outline envelope shrunk onto the copper (no copper-to-edge allowance)",
      (LAYOUT, "    envelope = max(trace_width, rules.finger_width) / 2 + rules.copper_to_edge + rules.offset_allowance\n",
       "    envelope = max(trace_width, rules.finger_width) / 2 + rules.offset_allowance\n")),
    m("audit/ff", "audit ff", "route-space rule raised to 0.3 mm (the audit's Row rule 0.246 -> 0.3; since 2026-10-15 the "
      "rule is the design's trace space, which the bundle and the contact-pitch routes now violate)",
      (DRC, "    route_rule = trace_space\n", "    route_rule = max(trace_space, 0.3)\n")),
    m("audit/gg", "audit gg", "Gerber coordinates scaled by 1e5 instead of 1e6 (FSLAX46: geometry 10x too small)",
      (GERBER, "    scaled = int(round(float(value) * 1_000_000))\n", "    scaled = int(round(float(value) * 100_000))\n")),
    m("audit/hh", "audit hh", "jlcpcb.json mil conversion uses 25.4 per mm, writer and read-back alike",
      (GERBER, "_MILS_PER_MM = 39.37007874015748\n", "_MILS_PER_MM = 25.4\n")),
    m("audit/jj", "audit jj", "GKO contours not closed (last segment omitted)",
      (GERBER, "        lines.extend(_stroke([*points, points[0]]))\n", "        lines.extend(_stroke(list(points)))\n")),
    m("audit/ll", "audit ll", "route aperture written as the radius instead of the diameter",
      (GERBER, '    lines.extend(f"%ADD{aperture_codes[width]}C,{width}*%" for width in widths)\n',
       '    lines.extend(f"%ADD{aperture_codes[width]}C,{float(width) / 2:.6f}*%" for width in widths)\n')),
    m("audit/mm", "audit mm", "stiffener layer covers the whole board outline",
      (GERBER, '        lines.extend(_region(board["layers"]["bottom_stiffener"][index]["points"]))\n',
       '        lines.extend(_region(board["outline"]["points"]))\n')),
    # Extras written while fixing C1 (fix-c1/run_audit_mutants.py and mutate.py).
    m("audit/X_route_open", "C1 extra", "route strokes start at their second vertex (contact end dropped)",
      (GERBER, '        lines.extend(_stroke(route["points"]))\n', '        lines.extend(_stroke([route["points"][1], *route["points"][1:]]))\n')),
    m("audit/X_elec_centred", "C1 extra", "electrodes written with centre semantics (mirror image of C1)",
      (GERBER, "        lines.extend(_region(rect_corners(rectangle)))\n",
       '        lines.extend(_region(rect_corners(rectangle if rectangle["anchor"] == "center" else dict(rectangle, anchor="center"))))\n')),
    m("audit/X_elec_shift", "C1 extra", "emitted electrodes shifted +0.5 mm in X (GTL only)",
      (GERBER, "        lines.extend(_region(rect_corners(rectangle)))\n",
       '        lines.extend(_region(rect_corners(rectangle if rectangle["anchor"] == "center" else dict(rectangle, x=rectangle["x"] + 0.5))))\n')),
    m("audit/X_gts_elec_shift", "C1 extra", "GTS electrode openings shifted +0.5 mm in X (contact window untouched)",
      (GERBER, "        lines.extend(_region(rect_corners(opening)))\n",
       '        lines.extend(_region(rect_corners(opening if opening["kind"] == "connector_contact_opening" else dict(opening, x=opening["x"] + 0.5))))\n')),
    m("audit/X_pad_y_shift", "C1 extra", "emitted contacts shifted 0.1 mm along +Y (still touching their routes)",
      (GERBER, "        lines.extend(_region(rect_corners(rectangle)))\n",
       '        lines.extend(_region(rect_corners(rectangle if rectangle["anchor"] != "center" else dict(rectangle, y=rectangle["y"] + 0.1))))\n')),
    m("audit/X_engine_pad_and_route", "C1 extra", "contacts and their route ends moved 0.25 mm toward the tip (model and GTL agree)",
      (LAYOUT, "    center_y = tip + rules.tip_clearance + rules.contact_length / 2\n",
       "    center_y = tip + rules.tip_clearance - 0.25 + rules.contact_length / 2\n"),
      (LAYOUT, "    contact_top = tip + rules.tip_clearance + rules.contact_length\n    electrode_left",
       "    contact_top = tip + rules.tip_clearance - 0.25 + rules.contact_length\n    electrode_left"),
      (LAYOUT, "    contact_top = tip + rules.tip_clearance + rules.contact_length\n    electrode_bottom",
       "    contact_top = tip + rules.tip_clearance - 0.25 + rules.contact_length\n    electrode_bottom")),
    m("audit/X_pad_bowtie", "C1 extra", "contact regions written as bow ties (corner order swapped)",
      (GERBER, "        lines.extend(_region(rect_corners(rectangle)))\n",
       '        lines.extend(_region((lambda c: [c[0], c[2], c[1], c[3]])(rect_corners(rectangle)) if rectangle["anchor"] == "center" else rect_corners(rectangle)))\n')),
    m("audit/X_pads_clear_polarity", "C1 extra", "contacts written with clear polarity (%LPC*%)",
      (GERBER, "    for rectangle in [*copper[\"electrodes\"], *copper[\"pads\"]]:\n",
       "    lines.append(\"%LPC*%\")\n    for rectangle in [*copper[\"electrodes\"], *copper[\"pads\"]]:\n")),
    m("audit/X_row_pads_sideways", "C1 extra", "contacts shifted 0.02 mm sideways in the model (routes unchanged)",
      (LAYOUT, '        center_x = plan["tail_x"] + rules.side_offset + position * rules.pitch\n',
       '        center_x = plan["tail_x"] + rules.side_offset + position * rules.pitch + 0.02\n')),
    m("audit/X_pads_first", "C1 extra (control)", "identical artwork in another region order, writer and read-back alike: "
      "only the golden archive digests (the golden test and the digest table of PHASE2) may notice",
      (GERBER, "    for rectangle in [*copper[\"electrodes\"], *copper[\"pads\"]]:\n",
       "    for rectangle in [*copper[\"pads\"], *copper[\"electrodes\"]]:\n"),
      (GERBER, '    _same_regions(_GTL, gtl["regions"], [_corners(rect) for rect in [*copper["electrodes"], *copper["pads"]]])\n',
       '    _same_regions(_GTL, gtl["regions"], [_corners(rect) for rect in [*copper["pads"], *copper["electrodes"]]])\n'),
      killers=("test_golden_default.", "test_docs_consistency.ExportDocumentTests.test_determinism_table_matches_the_default_archives")),
)

# --------------------------------------------------------------------------
# Stage E: engine geometry and whole-board DRC.
# --------------------------------------------------------------------------

ENGINE = (
    m("E/fanout-spread-size", "fan-out spread (2026-10-15)", "the size pre-check leaves out a two-lane fan-out that spreads beyond the body",
      (LAYOUT, "    min_x = min(body_left, tail_x, hull_left)\n", "    min_x = min(body_left, tail_x)\n")),
    m("E/C2-margin", "C2", "no board margin below the Column taxel field",
      (LAYOUT, "    active_y = body_bottom + margin\n", "    active_y = body_bottom\n")),
    m("E/C3-width", "C3", "old tail width N*0.5 + 1.3 mm",
      (LAYOUT, "    return (pins - 1) * rules.pitch + 2 * rules.side_offset\n", "    return pins * rules.pitch + 1.3\n")),
    m("E/C3-contacts", "C3", "old 1.4 mm contacts (profile)",
      (PROFILE, '"contact_length_mm": 4.0,', '"contact_length_mm": 1.4,')),
    m("E/C3-row-pins", "C3", "connector.row_pins ignored (tail sized for the channel count)",
      (LAYOUT, '    return channels if value is None else int(value)\n', '    return channels\n')),
    m("E/H1-entry", "H1", "fixed 16 mm transitions: every diagonal drops 16 mm whatever its displacement (no longer parallel)",
      (LAYOUT, "            levels = [(route, rank * stagger, abs(shifts[route]) * cot) for rank, route in enumerate(run)]\n",
       "            levels = [(route, rank * stagger, 16.0) for rank, route in enumerate(run)]\n")),
    m("E/H5-electrode-route", "H5", "electrode-route clearance never fails",
      (DRC, '        ("electrode", "route"): ("electrode_route_clearance", route_rule),', '        ("electrode", "route"): ("electrode_route_clearance", -1.0),')),
    m("E/M1-stiffener", "M1", "stiffener spans the whole tail",
      (LAYOUT, "    top = tip + rules.stiffener_length\n", '    top = plan["tail_top"]\n')),
    m("E/M2-hull", "M2", "outline hull not seeded with the tail sides (notch at the shoulder)",
      (LAYOUT, "    current = start\n    answer = [[start, points[0][1]]]\n", "    current = points[0][0]\n    answer = [[current, points[0][1]]]\n")),
    m("E/M8-offset", "M8", "vertex-normal offset again (no round joins on the convex side)",
      (GEOMETRY, "        outer = turn < 0 if left else turn > 0\n", "        outer = False\n")),
    m("E/M9-width", "M9", "no minimum electrode width at validation",
      (CORE, "        elif size + _EPSILON < minimum_width:\n", "        elif False:\n")),
    m("E/M9-size", "M9", "board-size feasibility check removed",
      (LAYOUT, "        if _fits(plan, limits):\n            continue\n", "        continue\n")),
    m("E/M11-anchor", "M11", "centre anchors read as lower-left by every consumer",
      (GEOMETRY, '    if anchor == "center":\n        return (x - width / 2, y - height / 2, x + width / 2, y + height / 2)\n',
       '    if anchor == "center":\n        return (x, y, x + width, y + height)\n')),
    m("E/L4-epsilon", "L4", "0.5 um DRC tolerance instead of 1 nm (profile)",
      (PROFILE, '"numeric_epsilon_mm": 0.000001', '"numeric_epsilon_mm": 0.0005')),
    m("E/L5-deck", "L5", "single-lane bundle at a fixed 1.2 mm pitch (the old deck cap; wider than a fine-pitch field)",
      (LAYOUT, "        first = round6((centers[0] + centers[-1]) / 2 - (columns - 1) * bundle_pitch / 2)\n"
               "        decks = [round6(first + index * bundle_pitch) for index in range(columns)]\n",
       "        first = round6((centers[0] + centers[-1]) / 2 - (columns - 1) * 1.2 / 2)\n"
       "        decks = [round6(first + index * 1.2) for index in range(columns)]\n")),
    m("E/L6-merge", "L6", "coverlay windows never merge",
      (LAYOUT, "    if bridges and min(bridges) < rules.min_bridge - _FLOAT_NOISE_MM:\n", "    if False:\n")),
    m("E/L7-overhang", "L7", "Row electrodes do not overhang the taxel field",
      (LAYOUT, "    electrode_left = active_x - rules.overhang\n    electrode_right = active_x + active_width + rules.overhang\n",
       "    electrode_left = active_x\n    electrode_right = active_x + active_width\n")),
    m("E/I5-pruning", "I5", "pair checks pruned against the running minimum (inexact counters)",
      (DRC, "        gap = first.gap(second)\n        checks[name].add(",
       "        gap = first.gap(second)\n        if checks[name].measured is not None and gap > checks[name].measured:\n            continue\n        checks[name].add(")),
    m("E/parallel-sides", "VERIFY-GEO-1", "quarter-turn mixed tail sides accepted at validation",
      (CORE, '    if len(sides) == 2 and (TAIL_TURNS[sides["row_side"]] - TAIL_TURNS[sides["column_side"]]) % 2:\n', "    if False:\n")),
    m("E/field-path", "H1/D3", "DRC field paths name the role (boards.columns.*) again",
      (DRC, '{"code": code, "field": f"boards.{key}.{part}"', '{"code": code, "field": f"boards.{role}.{part}"')),
    m("E/active-margin", "D2", "active-field margin never checked",
      (DRC, '    margin_check = _Check("active_field_margin", rules.margin)\n', '    margin_check = _Check("active_field_margin", None)\n')),
    m("E/stiffener-zone", "D1", "stiffener zone never checked",
      (DRC, '    zone.add(deviation, "stiffener", rules.epsilon)\n', '    zone.add(0.0, "stiffener", rules.epsilon)\n')),
    m("E/stiffener-end", "M1 review F4", "stiffener end clearance measured to the nominal tail root",
      (DRC, '    end.add(straight, "stiffener", rules.epsilon)\n',
       '    end.add(max(along(tail_box[axis]), along(tail_box[axis + 2])) - finish, "stiffener", rules.epsilon)\n')),
    m("E/grid-always", "D11", "registration grid deviation always 0",
      (DRC, "    width = size[across] - (count - 1) * pitch\n    worst = 0.0\n", "    return 0.0\n")),
    m("E/side-offset", "D1", "outer-contact side offsets not checked",
      (DRC, "    worst = max(worst, abs(centers[0] - low - rules.side_offset), abs(high - centers[-1] - rules.side_offset))\n", "")),
    m("E/fold-back", "D11", "outline fold-backs not counted",
      (DRC, "    hits = sum(1 for _, turn in _ring_turns(points) if abs(turn) >= math.pi - 1e-9)\n", "    hits = 0\n")),
    m("E/exposure", "D7", "a contact without any opening is not an exposure failure",
      (DRC, '            exposure.fail(feature["net"])  # no opening of its net at all\n', "            pass\n")),
    m("E/connectivity-nc", "D11", "NC contacts may carry routes or electrodes",
      (DRC, "            if net_routes or net_electrodes or len(net_pads) != 1:\n", "            if len(net_pads) != 1:\n")),
    m("E/connectivity-end", "D11", "routes need not end on their electrode",
      (DRC, "            or point_box_distance(fanout[-1], rect_bounds(net_electrodes[0])) > epsilon\n", "")),
    m("E/F1-tail-grid", "review F1", "tail position not on the layout grid",
      (LAYOUT, "    tail_x = round6((body_width - width_of_tail) / 2)\n", "    tail_x = (body_width - width_of_tail) / 2\n")),
    m("E/F1-inputs", "review F1", "design inputs not taken on the layout grid",
      (LAYOUT, '        round6(matrix["pitch_x_mm"]),\n        round6(matrix["pitch_y_mm"]),\n',
       '        float(matrix["pitch_x_mm"]),\n        float(matrix["pitch_y_mm"]),\n'),
      expect="survive", reason="equivalent: generate_design canonicalises every number on the 1e-6 grid before the layout "
      "(stage A), so this second rounding is redundant; 300 random full-precision designs gave byte-identical results"),
    m("E/F1-heights", "review F1", "the fan-out's transition heights (the bends where a diagonal meets its route's own column) off the layout grid",
      (LAYOUT, "                    answer[route] = (ceil6(bundle_y + drop), bundle_y)\n", "                    answer[route] = (bundle_y + drop, bundle_y)\n"),
      (LAYOUT, "                    answer[route] = (bundle_y, floor6(bundle_y - drop))\n", "                    answer[route] = (bundle_y, bundle_y - drop)\n")),
    m("E/F2-reach", "review F2", "fillet search limited to the adjacent edges",
      (GEOMETRY, "_FILLET_REACH_RADII = 4.0\n", "_FILLET_REACH_RADII = 0.0\n")),
    m("E/F2-radius-rule", "review F2", "effective fillet radius rule removed",
      (DRC, "            fillet.add(radius, [name, [round6(vertex[0]), round6(vertex[1])]], epsilon)\n", "            pass\n")),
    m("E/F2-runs", "review F2", "concave runs not split at long edges",
      (DRC, '    fillet = _Check("concave_fillet_radius", rules.fillet_radius * math.cos(rules.arc_step / 2))\n'
            "    longest_step = 2 * rules.fillet_radius * math.sin(rules.arc_step / 2) + _ARC_CHORD_SLACK_MM\n",
       '    fillet = _Check("concave_fillet_radius", rules.fillet_radius * math.cos(rules.arc_step / 2))\n    longest_step = 1e9\n')),
    m("E/F3-field", "review F3", "grid mismatch reported at tail.column_side",
      (DRC, '                f"boards.{key}.layers.top_copper.electrodes",\n', '                "tail.column_side",\n')),
    m("E/F5-bound", "review F5", "electrode-gap bound rounded to nearest",
      (CORE, '                    f"{floor4(pitch - gap):.4f} mm.",\n', '                    f"{pitch - gap:.4f} mm.",\n')),
    m("E/F6-gbsl", "review F6", "GBSL regions shifted 0.5 mm, writer and read-back alike",
      (GERBER, '        lines.extend(_region(board["layers"]["bottom_stiffener"][index]["points"]))\n',
       '        lines.extend(_region([[x + 0.5, y] for x, y in board["layers"]["bottom_stiffener"][index]["points"]]))\n'),
      (GERBER, '        _same_regions(group["gerber"], layer["regions"], [stiffeners[index]["points"] for index in group["indices"]])\n',
       '        _same_regions(group["gerber"], layer["regions"], [[[x + 0.5, y] for x, y in stiffeners[index]["points"]] for index in group["indices"]])\n')),
    m("E/F7-nc-pins", "review F7", "NC pins numbered after the channels (not monotonic along the row)",
      (LAYOUT, '        pin = _pin_for_position(position + 1, plan["pins"], order)\n',
       '        pin = _pin_for_position(position + 1, len(nets), order) if position < len(nets) else position + 1\n')),
    m("E/body-side", "D5", "body sides never moved for fillet room (steps narrower than one fillet radius remain)",
      (LAYOUT, "    step = (side - hull) * outward\n", "    return side\n    step = (side - hull) * outward\n")),
    m("E/body-side-snap", "D5", "a body side just inside the tail or envelope below it is not made flush",
      (LAYOUT, "    if -radius < step < -1e-9:\n        return snap(hull)\n", "")),
    m("E/body-side-row", "D5", "the Row body side is never moved (a narrow step to the tail remains)",
      (LAYOUT, "    body_width = _body_side(field_right, width_of_tail, 1.0, rules.fillet_radius)\n",
       "    body_width = field_right\n")),
    m("E/bundle-pitch", "T-D3/T-D4", "bundles run 0.01 mm wider than trace width + space (still clean, but not the design's pitch)",
      (LAYOUT, "    return width, space, round6(width + space)\n", "    return width, space, round6(width + space + 0.01)\n")),
    m("E/bend-stagger", "T-D4", "bus bends without the stagger: neighbours turn at one height (diagonals closer than the pitch)",
      (LAYOUT, "            levels = [(route, rank * stagger, abs(shifts[route]) * cot) for rank, route in enumerate(run)]\n",
       "            levels = [(route, 0.0, abs(shifts[route]) * cot) for rank, route in enumerate(run)]\n")),
    m("E/stagger-side", "T-D4", "bus bends staggered the wrong way (falling toward the side the run moves to)",
      (LAYOUT, "            run = list(range(start, end + 1))[:: signs[start]]\n", "            run = list(range(start, end + 1))[:: -signs[start]]\n")),
    m("E/junction-drop", "T-D3", "the traces widen at the lowest bend, not below it (wide copper next to a bending neighbour)",
      (LAYOUT, "    return ceil6(max(0.0, (needed - rules.pitch * math.cos(angle)) / math.sin(angle)))\n", "    return 0.0\n")),
    m("E/junction-drop-mid", "T-D3 review", "the widening drop too short for bundle widths between 0.127 and 0.25 mm "
      "(the reviewer's MX1: a wide tail end within 0.246 mm of a neighbour's diagonal)",
      (LAYOUT, "    needed = rules.half_finger + trace_width / 2 + (rules.pitch - rules.finger_width) + _DIAGONAL_ALLOWANCE_MM\n",
       "    needed = rules.half_finger + trace_width / 2 + (rules.pitch - rules.finger_width) + _DIAGONAL_ALLOWANCE_MM\n"
       "    needed -= (trace_width - 0.127) / 2 if 0.127 < trace_width < 0.25 else 0.0\n")),
    m("E/bend-rounding", "T-D4 review", "the far bends of the diagonals rounded to the nearest grid value (short diagonals lean past the taper cap)",
      (LAYOUT, "                    answer[route] = (ceil6(bundle_y + drop), bundle_y)\n", "                    answer[route] = (round6(bundle_y + drop), bundle_y)\n"),
      (LAYOUT, "                    answer[route] = (bundle_y, floor6(bundle_y - drop))\n", "                    answer[route] = (bundle_y, round6(bundle_y - drop))\n")),
    m("E/junction-width", "T-D3", "the widening drop ignores the bundle trace width (too short for wide bundle traces)",
      (LAYOUT, "    needed = rules.half_finger + trace_width / 2 + (rules.pitch - rules.finger_width) + _DIAGONAL_ALLOWANCE_MM\n",
       "    needed = rules.half_finger + rules.pitch - rules.finger_width + _DIAGONAL_ALLOWANCE_MM\n")),
    m("E/envelope-width", "T-D5", "the outline envelope uses the bundle trace width, not the larger finger width",
      (LAYOUT, "    envelope = max(trace_width, rules.finger_width) / 2 + rules.copper_to_edge + rules.offset_allowance\n",
       "    envelope = trace_width / 2 + rules.copper_to_edge + rules.offset_allowance\n")),
    m("E/row-channel", "T-D6", "the Row channel keeps the old contact-pitch width (field position not from the bundle pitch)",
      (LAYOUT, "    channel_width = round6((rows - 1) * bundle_pitch + 2 * rules.side_offset)\n",
       "    channel_width = round6((rows - 1) * rules.pitch + 2 * rules.side_offset)\n")),
    m("E/row-expansion-margin", "T-D6", "the Row expansion reaches up to the active field (no active-field margin below the field)",
      (LAYOUT, "    active_y = round6(expansion_top + rules.margin)\n", "    active_y = round6(max(expansion_top, rules.margin))\n")),
    m("E/route-rule", "T-D7", "the route clearance rule is the JLC minimum, not the design's trace space",
      (DRC, "    route_rule = trace_space\n", "    route_rule = rules.min_trace_space\n")),
    m("E/finger-section-rule", "T-D3/T-D7 review", "route pairs with a tail piece held to the trace space only (no finger-section spacing in the DRC)",
      (DRC, "    finger_rule = max(route_rule, rules.pitch - rules.finger_width)\n", "    finger_rule = route_rule\n")),
    m("E/finger-section-pairs", "T-D3/T-D7 review", "only tail-to-tail pairs keep the finger-section spacing (not a tail end beside another net's fan-out piece)",
      (DRC, '        finger = kinds == ("route", "route") and "tail" in (first.piece, second.piece)\n',
       '        finger = kinds == ("route", "route") and first.piece == second.piece == "tail"\n')),
    m("E/route-width", "T-D7", "route_width never measures a deviation",
      (DRC, '        check.add(abs(width - widths[route["segment"]]), where, rules.epsilon)\n', "        check.add(0.0, where, rules.epsilon)\n")),
    m("E/route-width-minimum", "T-D7", "route_width does not check the copper's fabrication minimum",
      (DRC, "        if width < rules.min_trace_width - rules.epsilon:\n            check.fail(where)\n", "")),
    m("E/route-width-code", "T-D7", "a failing route_width record raises no E_ROUTE_WIDTH",
      (DRC, '    "route_width": ("E_ROUTE_WIDTH", _ROUTES),\n', "")),
    m("E/copper-minimum", "T-D2/N4", "the 18 um copper's trace minimum (3.5 mil) applied to the ordered 1 oz copper",
      (PROFILE_PY, "        if abs(float(thickness) - copper) <= 1e-9:\n            return float(width), float(space)\n",
       "        return float(width), float(space)\n")),
    m("E/finger-spacing", "T-D2", "profile check of the finger-section spacing (contact pitch - finger width) removed",
      (PROFILE_PY, '        at_least("E_PROFILE_FAB_LIMIT", "routing.finger_trace_width_mm", pitch - finger, minimum_space, f"finger-section spacing, contact pitch less finger width ({copper_text})")\n', "")),
    m("E/size-advice", "D3", "no two-field board-size advice",
      (LAYOUT, "    # No single change is enough: lower two fields together, in step.\n", "    return found\n")),
)

# --------------------------------------------------------------------------
# Stage A: normalization, identity, schema, SVG, HTTP and CLI.
# --------------------------------------------------------------------------

API = (
    m("API/unknown-top", "H6", "unknown top-level keys silently ignored",
      (CORE, "            else:\n                unknown.append((None, key, value))\n", "            else:\n                pass\n")),
    m("API/unknown-nested", "H6", "unknown nested keys silently ignored",
      (CORE, "                    else:\n                        unknown.append((key, sub_key, sub_value))\n", "                    else:\n                        pass\n")),
    m("API/flat-wins", "H6", "flat aliases beat nested fields",
      (CORE, "        present = [source for source in (field, *_ALIAS_SOURCES[field]) if source in supplied]\n",
       "        present = [source for source in (*_ALIAS_SOURCES[field], field) if source in supplied]\n")),
    m("API/invalid-alias", "H6", "invalid enumerated alias values ignored",
      (CORE, "        if mapped[alias] is None:\n            allowed", "        if False:\n            allowed")),
    m("API/shadowed-alias", "H6 review R2", "an invalid alias shadowed by a nested field is not an error",
      (CORE, "        if mapped[alias] is None:\n            allowed",
       "        if mapped[alias] is None and not all(target in supplied for target in targets):\n            allowed")),
    m("API/no-shadow-warning", "D13", "no W_ALIAS_SHADOWED",
      (CORE, "            if mapped.get(loser, ()) is not None and not same_value(field, source_value(loser, field), value):\n", "            if False:\n")),
    m("API/schema-version", "L3", "missing schema_version not warned",
      (CORE, '        if "schema_version" not in supplied:\n', "        if False:\n")),
    m("API/name-strip", "L3", "project_name length checked before trimming",
      (CORE, "    elif len(name.strip()) > name_limit:\n", "    elif len(name) > name_limit:\n")),
    m("API/integral-float", "L3", "integral floats stay floats",
      (CORE, "        if value.is_integer() and abs(value) <= MAX_JSON_INTEGER:\n            return int(value), None\n",
       "        if False:\n            return int(value), None\n")),
    m("API/grid-round", "D14", "numbers canonicalised to 5 decimals instead of the layout grid",
      (CORE, "            value = round6(value)  # the layout grid itself", "            value = round(value, 5)  # the layout grid itself")),
    m("API/profile-digest", "M6", "profile digest left out of the build hash",
      (CORE, '_canonical_json({"design_sha256": design_sha256, "profile_sha256": profile_sha256, **versions})',
       '_canonical_json({"design_sha256": design_sha256, **versions})')),
    m("API/exporter-version", "M6", "exporter version left out of the build hash",
      (CORE, '_canonical_json({"design_sha256": design_sha256, "profile_sha256": profile_sha256, **versions})',
       '_canonical_json({"design_sha256": design_sha256, "profile_sha256": profile_sha256, "generator": GENERATOR_VERSION})')),
    m("API/slug-fallback", "M6", "non-ASCII names collapse onto one slug",
      (CORE, '    return "tactile-fpc-" + hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()[:8]\n', '    return "tactile-fpc"\n')),
    m("API/request-warnings", "D14", "request warnings counted in the manifest",
      (CORE, '    design_warnings = [issue for issue in validation["warnings"] if issue["code"] not in REQUEST_WARNING_CODES]\n',
       '    design_warnings = list(validation["warnings"])\n')),
    m("API/cache-key", "L11 review R1", "build cache keyed by the design hash only",
      (CORE, 'cache.fetch(identity["build_sha256"], build)', 'cache.fetch(identity["design_sha256"], build)')),
    m("API/compact-layers", "D15", "compact view keeps the layers",
      (CORE, 'keys = ("id", "role", "physical_side", "units", "tail", "grid_registration", "metrics", "verification")',
       'keys = ("id", "role", "physical_side", "units", "tail", "grid_registration", "metrics", "verification", "layers")')),
    m("API/full-derived", "D15", "full view repeats derived_layout",
      (CORE, '        return {key: value for key, value in result.items() if key != "derived_layout"}\n', "        return dict(result)\n")),
    m("API/svg-flip", "H2", "SVG drawn without the Y flip (mirror of the Gerber)",
      (CORE, 'f\'<g transform="matrix(1 0 0 -1 0 {_svg_number(flip)})">\'', "f'<g transform=\"matrix(1 0 0 1 0 0)\">'")),
    m("API/active-region", "D18", "data-active-region not flipped",
      (CORE, '    active_region = (active["x"], flip - active["y"] - active["height"], active["width"], active["height"])\n',
       '    active_region = (active["x"], active["y"], active["width"], active["height"])\n')),
    m("API/pin1-marker", "D18", "pin-1 marker drawn at pin 2",
      (CORE, 'if pad.get("pin") == 1), None)', 'if pad.get("pin") == 2), None)')),
    m("API/label-fit", "H2 review", "view label not fitted to narrow boards",
      (CORE, "    label_size = min(label_size, (width + _SVG_PADDING_MM)", "    label_size = max(label_size, (width + _SVG_PADDING_MM)")),
    m("API/nan", "L1", "NaN accepted by the strict JSON reader",
      (SCHEMA, "parse_constant=_reject_constant, ", "")),
    m("API/duplicate-keys", "L1", "duplicate JSON keys accepted",
      (SCHEMA, ", object_pairs_hook=_unique_keys", "")),
    m("API/schema-open", "M14", "schema sections allow unknown keys",
      (SCHEMA, 'properties.setdefault(section, {"type": "object", "additionalProperties": False, "properties": {}})',
       'properties.setdefault(section, {"type": "object", "properties": {}})')),
    m("API/catalogue", "M14", "issue catalogue misses a DRC code",
      (SCHEMA, '    "E_NECK_WIDTH": ("drc", "The board is narrower than the tail between tail and body."),\n', "")),
    m("API/name-pattern", "M14 review", "schema name pattern accepts control characters",
      (SCHEMA, "pattern=PROJECT_NAME_PATTERN)", 'pattern="\\\\S")')),
    m("API/host-allow-list", "L2", "Host allow-list off",
      (APP, "        if name is not None and not self.server.host_allowed(name):\n", "        if False:\n")),
    m("API/configured-host", "L2 final review", "the configured --host is left out of the Host allow-list",
      (APP, "frozenset({*LOOPBACK_HOSTS, *bound, *self.extra_hosts})", "frozenset({*LOOPBACK_HOSTS, *self.extra_hosts})")),
    m("API/host-canonical", "L2 follow-up check", "the Host name is compared as the client wrote it",
      (APP, "        name = _bind_host_name(name)  # an IP literal in one notation, however the client wrote it\n", "")),
    m("API/allow-host-suffix", "L2 final review", "an --allow-host domain matches any name that ends with it, not only its subdomains",
      (APP, 'name.endswith("." + domain)', "name.endswith(domain)")),
    m("API/origin-any-https", "L2 final review", "any https:// Origin is taken as the request's own",
      (APP, 'origin in (f"http://{host.lower()}", f"https://{host.lower()}")',
       '(origin == f"http://{host.lower()}" or origin.startswith("https://"))')),
    m("API/origin-cross-loopback", "L2 final review", "an Origin naming any served host (another loopback name or port) is accepted",
      (APP, "self.server.extra_host(_host_header_name(authority))", "self.server.host_allowed(_host_header_name(authority))")),
    m("API/static-types", "final review FV-HTTP-01", "the UI files take their types from the host's mimetypes registry again",
      (APP, "        content_type = STATIC_TYPES.get(path.suffix.lower())\n", "        content_type = None\n")),
    m("API/port-range", "final review FV-HTTP-03", "--port accepts numbers outside 0-65535",
      (APP, "    if not 0 <= port <= 65535:\n", "    if port < 0:\n")),
    m("API/host-syntax", "L2", "Host syntax not validated",
      (APP, "not all(_HOST.match(host) for host in hosts)", "not all(True for host in hosts)")),
    m("API/origin", "L2", "Origin check off",
      (APP, "        if origins and (len(origins) != 1", "        if False and (len(origins) != 1")),
    m("API/content-type", "L2", "Content-Type check off",
      (APP, '    if media_type.strip().lower() != "application/json" or charset not in ("utf-8", "utf8"):\n', "    if False:\n")),
    m("API/csp", "L2", "Referrer-Policy header missing",
      (APP, '    ("Referrer-Policy", "no-referrer"),\n', "")),
    m("API/server-header", "L2", "Python version in the Server header",
      (APP, "        return self.server_version\n", "        return self.server_version + ' ' + self.sys_version\n")),
    m("API/semaphore", "D16", "no limit on concurrent generations",
      (APP, "        if not slots.acquire(blocking=False):\n", "        if not slots.acquire(blocking=True):\n")),
    m("API/chunked", "L1", "chunked bodies read as empty",
      (APP, '        if self.headers.get("Transfer-Encoding") is not None:\n            self._error(HTTPStatus.LENGTH_REQUIRED',
       '        if False:\n            self._error(HTTPStatus.LENGTH_REQUIRED')),
    m("API/timeout", "L1", "no socket timeout",
      (APP, "    timeout = SOCKET_TIMEOUT_S\n", "    timeout = None\n")),
    m("API/deadline", "L1 review", "no overall request deadline",
      (APP, "        self._reader.deadline = time.monotonic() + self.request_deadline\n", "        self._reader.deadline = None\n")),
    m("API/drain", "L1", "no lingering close after a rejected body",
      (APP, "        if self._unread_body or self._input_waiting():\n", "        if False:\n")),
    m("API/log-escape", "L1", "log lines not escaped",
      (APP, "        message = (format % args).translate(_LOG_ESCAPES)\n", "        message = format % args\n")),
    m("API/cache-bypass", "L11", "server generations bypass the build cache",
      (APP, "    result = generate_design(payload, cache=cache)\n", "    result = generate_design(payload)\n")),
    m("API/display-rule", "D10", "literal fan-out rule text",
      (APP, '    fan_out = f"≤{per_lane}: one lane"\n', '    fan_out = "≤16: one lane"\n')),
    m("API/cli-null", "M14 review", "CLI reads a null document as the default design",
      (CLI, "    if not isinstance(data, dict):\n", "    if data is not None and not isinstance(data, dict):\n")),
    m("API/cli-output", "M14 review", "CLI write failures escape as a traceback",
      (CLI, "    except OSError as error:\n        return 2, {**summary", "    except ValueError as error:\n        return 2, {**summary")),
    m("API/cli-batch-last", "M14 (stage-T review)", "a CLI batch exits with its last entry's status, not the largest",
      (CLI, "    status = max(code for code, _ in outcomes)\n", "    status = outcomes[-1][0]\n")),
    m("API/cache-size", "L11 (stage-T review)", "the server's build cache holds one build instead of 16",
      (APP, "BUILD_CACHE_SIZE = 16\n", "BUILD_CACHE_SIZE = 1\n")),
    m("API/trace-range", "T-D1", "routing.trace_width_mm / trace_space_mm ranges not enforced",
      (CORE, "        if field in grid and not low <= grid[field] <= high:\n", "        if False:\n")),
    m("API/trace-alias", "T-D1", "the flat trace_space_mm alias (the form's field) sets the trace width",
      (CORE, '    ("trace_space_mm", ("routing.trace_space_mm",), None),\n', '    ("trace_space_mm", ("routing.trace_width_mm",), None),\n')),
    m("API/trace-schema", "T-D1", "the JSON Schema and form limits allow bundle traces down to the 18 um minimum",
      (SCHEMA, '            "type": "number", "unit": "mm", "minimum": limits[f"minimum_trace_{kind}_mm"], "maximum": limits[f"maximum_trace_{kind}_mm"],\n',
       '            "type": "number", "unit": "mm", "minimum": 0.0889, "maximum": limits[f"maximum_trace_{kind}_mm"],\n')),
    m("API/svg-stroke-width", "N18", "the preview draws every route 0.254 mm wide (the stroke width written once, not per route)",
      (CORE, 'f\'<polyline class="route" stroke-width="{_svg_number(item["width_mm"])}" points=',
       'f\'<polyline class="route" stroke-width=".254" points=')),
    m("API/display-bundle", "T-D8", "the Bundle traces rule shows the profile's finger width instead of the design's bundle",
      (APP, '    width, space = float(bundle["trace_width_mm"]), float(bundle["trace_space_mm"])\n',
       '    width, space = float(routing["finger_trace_width_mm"]), float(bundle["trace_space_mm"])\n')),
    m("API/cli-codes", "M14", "CLI codes not listed by `schema`",
      (CLI, '_print(dict(design_schema(), **{"x-cli-error-codes": dict(CLI_ERROR_CODES)}), args.pretty)', "_print(design_schema(), args.pretty)")),
)

# --------------------------------------------------------------------------
# Stage X: exporter 0.2.0.
# --------------------------------------------------------------------------

EXPORT = (
    m("X/gbsl-name", "M7", "hard-coded 0.2 mm GBSL file name",
      (GERBER, '        name = f"Gerber_{side_name}StiffenerLayer_{code}{side_code}_{thickness}.{extension}"\n',
       '        name = "Gerber_BottomStiffenerLayer_pib_0.2.GBSL"\n')),
    m("X/deflate", "L10", "deflated ZIP members (bytes depend on zlib)",
      (GERBER, "from zipfile import ZIP_STORED, ZipFile, ZipInfo\n", "from zipfile import ZIP_DEFLATED as ZIP_STORED, ZipFile, ZipInfo\n")),
    m("X/same-coordinates", "L9", "TF.SameCoordinates missing, writer and read-back alike",
      (GERBER, '        f"G04 #@! TF.SameCoordinates,{build_id}*",\n', ""),
      (GERBER, '            "TF.SameCoordinates": build_id,\n', "")),
    m("X/software-version", "L9", "TF.GenerationSoftware without the version field, writer and read-back alike",
      (GERBER, '        f"G04 #@! TF.GenerationSoftware,TactileFPC,direct-gerber,{_version_number()}*",\n',
       '        "G04 #@! TF.GenerationSoftware,TactileFPC,direct-gerber*",\n'),
      (GERBER, '            "TF.GenerationSoftware": f"TactileFPC,direct-gerber,{_version_number()}",\n',
       '            "TF.GenerationSoftware": "TactileFPC,direct-gerber",\n')),
    m("X/netlist-position", "M10", "netlist contact pins from the position instead of the pin",
      (GERBER, '        points.append(_test_point(pad["net"], _CONTACT_REFDES, pad["pin"], center, x1 - x0, y1 - y0))\n',
       '        points.append(_test_point(pad["net"], _CONTACT_REFDES, pad["position"], center, x1 - x0, y1 - y0))\n')),
    m("X/netlist-nc", "M10", "NC contacts merged into one netlist net",
      (GERBER, '        points.append(_test_point(pad["net"], _CONTACT_REFDES,', '        points.append(_test_point("NC" if pad["net"].startswith("NC_") else pad["net"], _CONTACT_REFDES,')),
    m("X/netlist-far-end", "M10", "electrode test land at the near (route) end",
      (GERBER, "            center = (x1 - size / 2 if near_low else x0 + size / 2, (y0 + y1) / 2)\n",
       "            center = (x0 + size / 2 if near_low else x1 - size / 2, (y0 + y1) / 2)\n")),
    m("X/soldermask", "M10 review F5", "netlist soldermask code S1",
      (IPC, '_SOLDERMASK = "S2"', '_SOLDERMASK = "S1"')),
    m("X/pinout-pin", "M10", "pinout pin column from the position",
      (GERBER, '            writer.writerow((pad["pin"], pad["net"]', '            writer.writerow((pad["position"], pad["net"]')),
    m("X/pinout-index", "M10", "pinout logical index from the position",
      (GERBER, '            index = _channel_index(pad["net"], stem) if pad["kind"] == "connector_pad" else None\n',
       '            index = pad["position"] if pad["kind"] == "connector_pad" else None\n'),
      expect="survive", reason="equivalent: channel k always sits at position k (channel_order never moves copper)"),
    m("X/names", "M6", "artifact names without the build id",
      (GERBER, 'f"{build_id}-{side}-{roles[side]}-direct-gerber.zip"', 'f"tactile-fpc-{side}-{roles[side]}-direct-gerber.zip"')),
    m("X/manifest-names", "M6", "review manifest records other names than the downloads",
      (GERBER, '            "filename": names[key],\n', '            "filename": key + ".zip",\n')),
    m("X/identity", "L8", "identity of the result not checked",
      (GERBER, '    _check_identity(texts["design"], texts["profile"], profile, manifest)\n', "")),
    m("X/validation-counts", "M6", "validation.json counts request warnings as design warnings",
      (GERBER, '            "warning_count": len(warnings) - len(request),\n', '            "warning_count": len(warnings),\n')),
    m("X/bundle-zips", "M6", "review bundle without the Gerber ZIPs",
      (GERBER, '        files[f"gerbers/{names[key]}"] = data\n', "        pass\n")),
    m("X/bundle-profile", "M6", "review bundle without profile.json",
      (GERBER, '        "profile.json": build["profile_json"].encode("utf-8") + b"\\n",\n', "")),
    m("X/tolerance", "D17", "read-back tolerance 0.5 um instead of 2 nm",
      (GERBER, "_READBACK_TOLERANCE_MM = 2e-6\n", "_READBACK_TOLERANCE_MM = 5e-4\n")),
    m("X/board-manifest-id", "D17", "board manifest without the build id",
      (GERBER, '    keys = ("build_id", "build_sha256",', '    keys = ("build_sha256",')),
    m("X/coordinate-range", "L8", "no Gerber coordinate range check",
      (GERBER, "_MAX_COORDINATE_MM = 10_000.0\n", "_MAX_COORDINATE_MM = 1e12\n")),
    m("X/regenerate", "X review F1", "boards not compared with the engine's regeneration",
      (GERBER, '        difference = _first_difference(board_map[name], fresh["boards"][name])\n        if difference is None:',
       "        difference = None\n        if difference is None:")),
    m("X/manifest-compare", "X review F1", "manifest not compared with the regeneration",
      (GERBER, '    difference = _first_difference(manifest, fresh["manifest"])\n    if difference is not None:',
       "    difference = None\n    if difference is not None:")),
    m("X/ring-simple", "X review F2", "rings not checked for simplicity",
      (GERBER, "    if not ring_is_simple([[float(x), float(y)] for x, y in points]):\n", "    if False:\n")),
    m("X/generator", "X review", "generator version taken from the manifest",
      (GERBER, "    generator = engine_core.GENERATOR_VERSION\n", '    generator = manifest.get("generator")\n')),
    m("X/tie-break", "X review F3", "DRC extreme tie-break by raw float value",
      (DRC, "round6(value) > round6(self.measured) if self.maximum else round6(value) < round6(self.measured)",
       "value > self.measured if self.maximum else value < self.measured")),
    m("X/zip-readback", "D17", "board ZIPs not re-opened",
      (GERBER, "        data = _deterministic_zip(files)\n        _verify_zip(data, files)\n        key =", "        data = _deterministic_zip(files)\n        key =")),
    m("X/profile-top-stiffener", "X review F4", "profile accepts a top stiffener",
      (PROFILE_PY, "        if side not in STIFFENER_SIDES:\n", "        if False:\n")),
    m("X/one-aperture", "T-D3", "every route stroked with the first aperture (the fingers drawn at the bundle width), writer and read-back alike",
      (GERBER, "        lines.append(f\"D{aperture_codes[_decimal(route['width_mm'])]}*\")\n", '        lines.append("D10*")\n'),
      (GERBER, '    _same_strokes(_GTL, gtl["strokes"], [(float(route["width_mm"]), route["points"]) for route in copper["routes"]])\n',
       '    _same_strokes(_GTL, gtl["strokes"], [(float(min(r["width_mm"] for r in copper["routes"])), route["points"]) for route in copper["routes"]])\n')),
    m("X/trace-minimum", "T-D2", "the exporter accepts traces down to the 18 um minimum on 1 oz copper",
      (GERBER, "    minimum_trace = fabrication_minimum(profile)[0]\n", '    minimum_trace = min(profile["fabrication"]["single_sided_min_trace_width_mm"])\n')),
    m("X/trace-tolerance-line", "T-D9 review", "ORDER_NOTES.txt without each board's trace-tolerance line, writer and read-back alike",
      (GERBER, '        lines.extend(_note(_trace_tolerance(float(fanout), profile), "  ", "    "))\n', ""),
      (GERBER, '        phrases.append(_trace_tolerance(float(routing["trace_width_mm"]), profile))\n', "")),
    m("X/trace-tolerance-minimum", "T-D9 review", "the trace-tolerance line never says that traces come out below JLC's minimum",
      (GERBER, "    if narrowest < minimum:\n", "    if False:\n")),
    m("X/given-boards", "X review", "the given boards are written instead of the regenerated ones",
      (GERBER, '    return fresh["boards"]\n', "    return dict(board_map)\n"),
      expect="survive", reason="equivalent: the given boards were just required to be canonically equal to the regenerated ones"),
)

# --------------------------------------------------------------------------
# Stage T: the integration semantics, golden build, chirality, negative DRC
# flow, browser payload guard and documentation checks added with this tool.
# --------------------------------------------------------------------------

TESTS_AND_DOCS = (
    m("T/chirality-left", "D23/H4", "three quarter turns (left) mirrored [-y, -x]: left tail, wrong chirality",
      (GEOMETRY, "    if turns == 3:\n        return [y, -x]\n", "    if turns == 3:\n        return [-y, -x]\n")),
    m("T/row-lanes", "D23", "Row lanes reversed: ROW_01 leaves the far lane (routes cross)",
      (LAYOUT, '        lane_x = plan["lanes"][logical - 1]\n', '        lane_x = plan["lanes"][rows - logical]\n')),
    m("T/row-order", "D23", "ROW_01 is the electrode next to the tail instead of the far edge",
      (LAYOUT, "        physical_row = rows - logical\n", "        physical_row = logical - 1\n")),
    m("T/roles", "D23", "physical sides assigned the wrong way round (ids follow the swap)",
      (LAYOUT, "    for physical_side, role in mapping.items():\n", '    for physical_side, role in zip(("bottom", "top"), mapping.values()):\n')),
    m("T/default-tail", "golden", "default bottom tail 8 mm instead of 12 mm (the rectangular mode's 12 / 12, P5 section 27.7)",
      (CORE, '            "bottom_length_mm": _GENERIC_DEFAULT_BOTTOM_TAIL_MM,\n', '            "bottom_length_mm": 8.0,\n')),
    m("T/default-tail-surface", "golden", "the surface template's preset takes the generic template's 12 mm bottom tail (CAD mode's 7.5 mm minimum "
      "is its default)",
      (CORE, '        design["tail"]["bottom_length_mm"] = _SURFACE_DEFAULT_BOTTOM_TAIL_MM\n', "")),
    m("T/default-name", "golden", "default project name changed",
      (CORE, '        "project_name": "Tactile FPC 12x32",\n', '        "project_name": "Tactile FPC",\n')),
    m("T/generator-bump", "golden", "generator version bumped without updating the golden build",
      (CORE, 'GENERATOR_VERSION = "deterministic-sensor-core/0.4.0"\n', 'GENERATOR_VERSION = "deterministic-sensor-core/0.4.1"\n')),
    m("T/gerber-comment", "golden", "an extra comment line in every Gerber (geometry unchanged)",
      (GERBER, '        "%FSLAX46Y46*%",\n        "%MOMM*%",\n        "%LPD*%",\n    ]\n',
       '        "G04 extra*",\n        "%FSLAX46Y46*%",\n        "%MOMM*%",\n        "%LPD*%",\n    ]\n')),
    m("T/drc-gate", "H5", "post-generation DRC errors do not block the result",
      (CORE, '    validation["errors"].extend(built["errors"])\n', "    pass\n")),
    m("T/payload-key", "T-IDENTITY-GUARD", "browser payload gains a key the identity test does not mirror",
      (WEB, "      connector: connectorSection()\n", '      connector: connectorSection(), units: "mm"\n')),
    m("T/payload-connector", "T-IDENTITY-GUARD", "browser payload drops the nested connector section",
      (WEB, "      trace_width_mm: value(\"traceWidth\"), trace_space_mm: value(\"traceSpace\"),\n      connector: connectorSection()\n",
       "      trace_width_mm: value(\"traceWidth\"), trace_space_mm: value(\"traceSpace\")\n")),
    m("T/payload-version", "T-IDENTITY-GUARD", "browser payload drops schema_version",
      (WEB, "      schema_version: state.design?.schema_version, template_id: state.design?.template_id,\n",
       "      template_id: state.design?.template_id,\n")),
    m("T/doc-build-id", "M12", "README names a stale default build id",
      ("README.md", "tactile-fpc-12x32-48b9d43409a6", "tactile-fpc-12x32-ac8bac358de6")),
    m("T/doc-code", "M12", "an issue code missing from the documented catalogue",
      ("docs/LAYOUT_SCHEMA.md", "| `E_NECK_WIDTH` | drc |", "| `E_NECK_WIDTH_GONE` | drc |")),
    m("T/doc-check", "M12", "a DRC record missing from the documented list",
      ("docs/LAYOUT_SCHEMA.md", "| `concave_fillet_radius` |", "| `concave_fillet` |")),
    m("T/doc-profile", "M12", "a documented profile value no longer matches the profile",
      ("docs/LAYOUT_SCHEMA.md", "| `routing.copper_to_edge_mm` | 0.3 |", "| `routing.copper_to_edge_mm` | 0.2 |")),
    m("T/doc-key", "M11/M12", "a layout key missing from the schema document",
      ("docs/LAYOUT_SCHEMA.md", "`neck_bounds` (from", "`neck` (from")),
    m("T/doc-range", "M12", "README quotes a wrong input range",
      ("README.md", "rows (1-64)", "rows (1-128)")),
    m("T/doc-route", "M12", "a documented HTTP error code that the server does not have",
      ("docs/API.md", "| `E_HTTP_BUSY` |", "| `E_HTTP_OVERLOADED` |")),
    m("T/doc-side-table", "D23/M12", "INTEGRATION side table: the bottom-side Row tail at the wrong corner",
      ("docs/INTEGRATION.md", "| left edge | lower-left corner |", "| left edge | lower-right corner |")),
    m("T/doc-stack-table", "D19/M12", "INTEGRATION stack table: the face-up COL_01 on the wrong side",
      ("docs/INTEGRATION.md", "| face up: `COL_01` on the left, pin 1 leftmost |", "| face up: `COL_01` on the right, pin 1 leftmost |")),
    m("T/doc-flex", "D23/M12", "INTEGRATION: wrong straight flexible length beyond the stiffener",
      ("docs/INTEGRATION.md", "6.0 mm of straight", "1.5 mm of straight")),
    m("T/doc-thickness", "L7/M12", "INTEGRATION: wrong contact-zone thickness",
      ("docs/INTEGRATION.md", "= 0.285 mm thick", "= 0.30 mm thick")),
    m("T/doc-alias", "H6/M12", "API.md: an alias the engine does not accept",
      ("docs/API.md", "| `rows`, `row_num` |", "| `rows`, `row_count` |")),
    m("T/doc-enum", "M12", "API.md: a tail side value the engine does not accept",
      ("docs/API.md", "| `bottom`, `top`, `left`, `right` |", "| `bottom`, `top`, `left`, `up` |")),
    m("T/doc-name-length", "L3/M12", "API.md: wrong project-name length",
      ("docs/API.md", "1-80 characters after trimming", "1-64 characters after trimming")),
    m("T/doc-retry", "M12", "API.md: wrong Retry-After",
      ("docs/API.md", "`Retry-After: 1`", "`Retry-After: 9`")),
    m("T/doc-cache", "M12", "API.md: wrong build-cache size",
      ("docs/API.md", "A build cache of 16 builds", "A build cache of 64 builds")),
    m("T/doc-entry-point", "M12", "API.md: a keyword parameter the function does not have",
      ("docs/API.md", "`build_exports(result, *, cache=None)`", "`build_exports(result, *, cache=None, strict=None)`")),
    m("T/doc-netlist-row", "M10/M12", "PHASE2: board ZIP table without netlist.ipc",
      ("docs/PHASE2_DIRECT_GERBER.md", "| `netlist.ipc` | IPC-D-356A netlist (below) |\n", "")),
    m("T/doc-file-function", "M12", "PHASE2: wrong X2 file function of the coverlay layer",
      ("docs/PHASE2_DIRECT_GERBER.md", "| `Soldermask,Top`, declared", "| `Soldermask,Bot`, declared")),
    m("T/doc-anchor", "M11/M12", "LAYOUT_SCHEMA: contacts documented with the lower-left anchor",
      ("docs/LAYOUT_SCHEMA.md", "`connector_nc_pad`; `center` anchor", "`connector_nc_pad`; `lower_left` anchor")),
    m("T/doc-readme-members", "M12", "README: board ZIP members without netlist.ipc",
      ("README.md", "an IPC-D-356A `netlist.ipc`, ", "")),
    m("T/doc-snippet", "M12", "README: a Python snippet that no longer runs",
      ("README.md", "zips = build_exports(result)\n", "zips = build_exports(result, strict=True)\n")),
    m("T/doc-ci", "L13/M12", "README: CI described on Python versions the workflow does not run",
      ("README.md", "runs the suite on Python 3.9 and 3.12", "runs the suite on Python 3.8 and 3.12")),
    m("T/doc-test-count", "M12", "handoff: a stale test count",
      ("claude/APP_HANDOFF.md", " tests in 48 modules", "0 tests in 48 modules")),
    m("T/doc-mutation-summary", "M12", "handoff: a mutation summary that the catalogue does not give",
      ("claude/APP_HANDOFF.md", "3 equivalent (`E/F1-inputs`,", "4 equivalent (`E/F1-inputs`,")),
    m("F/stale-banner", "M4", "browser: the 'Form changed' banner is never shown",
      (WEB, '    $("staleBanner").hidden = !stale;\n', '    $("staleBanner").hidden = true;\n'),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    m("F/turn-over-axis", "M3/D19", "browser: the assembly turns the top board over about the wrong axis",
      (WEB, '    return board.tail?.side === "left" || board.tail?.side === "right" ? "x" : "y";\n',
       '    return board.tail?.side === "left" || board.tail?.side === "right" ? "y" : "x";\n'),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
)

# --------------------------------------------------------------------------
# Stage G: the 0.225 mm PI default, the profile's order requirements
# (ORDER_NOTES.txt, manifests, /api/default, the browser note) and the gold
# fingers measured on the emitted Gerbers.
# --------------------------------------------------------------------------

_REVIEW_LINES = (
    "            *(\n"
    "                f\"Set the JLCPCB order option '{record['topic']}' to {record['requirement']} for both boards ({_ORDER_NOTES}).\"\n"
    "                for record in records if record[\"kind\"] == \"order_option\"\n"
    "            ),\n"
)

GOLD_FINGERS = (
    m("G/stiffener-0.2", "G1", "default PI stiffener back to 0.2 mm (a consistent profile: the connector takes the thinner zone)",
      (PROFILE, '"stiffener_thickness_mm": 0.225', '"stiffener_thickness_mm": 0.2'),
      (PROFILE, '"contact_zone_thickness_mm": 0.3,', '"contact_zone_thickness_mm": 0.28,')),
    m("G/order-tolerance", "G2", "the default +/-0.1 mm outline tolerance ordered (wider than the THD0515 tail tolerance)",
      (PROFILE, '"outline_tolerance_mm": 0.05,', '"outline_tolerance_mm": 0.1,')),
    m("G/tolerance-check", "G2", "profile check accepts an outline tolerance wider than the connector's",
      (PROFILE_PY, '    if tolerance > conn["tail_width_tolerance_mm"] + 1e-12:\n', "    if False:\n")),
    m("G/thickness-check", "G2", "profile check accepts an FPC thickness JLC does not build",
      (PROFILE_PY, '    elif not _listed(order["fpc_thickness_mm"], fpc_options):\n', "    elif False:\n")),
    m("G/stackup-check", "G2", "profile check accepts a stack-up that does not add up to the ordered FPC thickness",
      (PROFILE_PY, '        if abs(layers - float(order["fpc_thickness_mm"])) >= _half_step(fpc_options):\n', "        if False:\n")),
    m("G/copper-check", "G2", "profile check accepts a copper JLC does not offer",
      (PROFILE_PY, '    elif not _listed(stack["copper_thickness_mm"], copper_options):\n', "    elif False:\n")),
    m("G/zone-check", "G1/G2", "profile check accepts a contact zone the reader connectors cannot take",
      (PROFILE_PY, '    if abs(contact_zone - conn["contact_zone_thickness_mm"]) > conn["contact_zone_thickness_tolerance_mm"] + 1e-9:\n',
       "    if False:\n")),
    m("G/copper-entry", "G2", "the copper weight listed as a review note, not as an order option",
      (PROFILE_PY, '"copper_weight", "order_option", "Copper weight"', '"copper_weight", "review_note", "Copper weight"')),
    m("G/finish-check", "G2", "profile check accepts a surface finish JLC does not offer",
      (PROFILE_PY, "for value in (finish, ordered)) and ordered != finish:\n", "for value in (finish, ordered)) and False:\n")),
    m("G/window-note", "G2", "the notes claim JLC's full coverlay expansion beside the outer contacts",
      (PROFILE_PY, '    margin = round(min(expansion, float(conn["contact_center_to_side_edge_mm"]) - width / 2 - radius), 6)\n',
       "    margin = round(expansion, 6)\n")),
    m("G/notes-member", "G2", "board ZIPs without ORDER_NOTES.txt, writer and read-back alike",
      (GERBER, "    files[_ORDER_NOTES] = _order_notes(build, [(board, groups)])\n", ""),
      (GERBER, "_JLC_METADATA, _NETLIST, _ORDER_NOTES, _MANIFEST,", "_JLC_METADATA, _NETLIST, _MANIFEST,"),
      (GERBER, "    _check_order_notes(files[_ORDER_NOTES], build, [(board, groups)])\n", "")),
    m("G/bundle-notes", "G2", "review bundle with the notes of the top board only",
      (GERBER, '    boards = [(build["boards_by_side"][side], build["stiffener_groups"][side]) for side in ("top", "bottom")]\n',
       '    boards = [(build["boards_by_side"][side], build["stiffener_groups"][side]) for side in ("top",)]\n')),
    m("G/notes-check", "D17", "ORDER_NOTES.txt not read back",
      (GERBER, '        found = flat.find(" ".join(phrase.split()), position)\n        if found < 0:\n',
       '        found = flat.find(" ".join(phrase.split()), position)\n        if False:\n')),
    m("G/claims-check", "D17", "the contact figures of the notes not checked against the board",
      (GERBER, "            if abs(figure - stated) > _READBACK_TOLERANCE_MM:\n", "            if False:\n")),
    m("G/stiffener-claim", "D17", "the stiffener zone of the notes not checked to start at the tip",
      (GERBER, "    if abs(stiffener_start) > _READBACK_TOLERANCE_MM:\n", "    if False:\n")),
    m("G/manifest-requirements", "G2", "board manifests without the order requirements, writer and read-back alike",
      (GERBER, '        "order_requirements": _order_records(build),\n    }\n', "    }\n"),
      (GERBER, '    if json.loads(files[_MANIFEST])["order_requirements"] != _order_records(build):\n', "    if False:\n")),
    m("G/review-lines", "G2", "review manifest without the order-option lines of review_requirements",
      (GERBER, _REVIEW_LINES, "")),
    m("G/api-order", "G2", "/api/default without the order requirements",
      (APP, '        "order_requirements": order_requirements(profile, default_design(template_id)),\n', "")),
    m("G/ui-order-note", "G2", "the browser does not render the manufacturing note",
      (WEB, "      renderOrderRequirements(data.profile.order_requirements);\n", "")),
    m("G/square-tip", "G3", "square tail tip corners (no R0.30 arcs)",
      (LAYOUT, "    left = convex_corner_arc([tail_x, tip], (0.0, -1.0), (1.0, 0.0), rules.tip_radius, rules.arc_step)\n"
               "    right = convex_corner_arc([tail_x + width, tip], (1.0, 0.0), (0.0, 1.0), rules.tip_radius, rules.arc_step)\n",
       "    left = [[tail_x, tip]]\n    right = [[tail_x + width, tip]]\n")),
    m("G/emitted-finger-width", "G3", "contacts emitted 0.05 mm wider than the layout, writer and read-back alike",
      (GERBER, "        lines.extend(_region(rect_corners(rectangle)))\n",
       '        lines.extend(_region(rect_corners(dict(rectangle, width_mm=rectangle["width_mm"] + 0.05) if rectangle["anchor"] == "center" else rectangle)))\n'),
      (GERBER, '    _same_regions(_GTL, gtl["regions"], [_corners(rect) for rect in [*copper["electrodes"], *copper["pads"]]])\n',
       '    _same_regions(_GTL, gtl["regions"], [_corners(dict(rect, width_mm=rect["width_mm"] + 0.05) if rect["anchor"] == "center" else rect) '
       'for rect in [*copper["electrodes"], *copper["pads"]]])\n')),
    m("G/doc-order", "G2/M12", "README quotes the default outline tolerance as the order",
      ("README.md", "PI stiffener at the contacts, a +/-0.05 mm", "PI stiffener at the contacts, a +/-0.1 mm")),
    m("G/doc-zone", "G1/M12", "README quotes the contact zone of the old stack-up",
      ("README.md", "0.285 mm thick with the 0.225 mm stiffener", "0.293 mm thick with the 0.225 mm stiffener")),
    m("G/doc-order-table", "G2/M12", "PHASE2: an order requirement missing from the table",
      ("docs/PHASE2_DIRECT_GERBER.md", "| `surface_finish` | order option | ENIG |\n", "")),
    # Profile revision 2026-10-29: the gold-finger thickness ordered in total (JLC's gold-finger stiffener ordering
    # guide) and the coverlay windows against JLC's general 20 mm for one opening (its FPC design rules).
    m("G/gold-finger-review-note", "order 2026-10-29", "the gold-finger thickness listed as a review note, not as an order option",
      (PROFILE_PY, '"gold_finger_thickness", "order_option", "Gold fingers"', '"gold_finger_thickness", "review_note", "Gold fingers"')),
    m("G/gold-finger-stiffener", "order 2026-10-29", "the gold-finger thickness ordered as the stiffener's, not the contact zone's",
      (PROFILE_PY, 'f"Yes, Gold Fingers Thickness {_g(zone)} mm', 'f"Yes, Gold Fingers Thickness {_g(stiffener)} mm')),
    m("G/window-key-unchecked", "order 2026-10-29", "the profile check does not require JLC's general length of one coverlay opening",
      (PROFILE_PY, '"coverlay_opening_to_trace_mm", "coverlay_opening_general_max_length_mm"),', '"coverlay_opening_to_trace_mm"),')),
    m("G/window-none-longer", "order 2026-10-29", "the coverlay-window line never names a window longer than JLC's 20 mm",
      (GERBER, "        if over:\n            longest = ", "        if False:\n            longest = ")),
    m("G/window-limit-doubled", "order 2026-10-29", "the coverlay-window line names only the windows longer than twice JLC's length",
      (GERBER, '    limit = float(profile["coverlay"]["coverlay_opening_general_max_length_mm"])\n',
       '    limit = 2 * float(profile["coverlay"]["coverlay_opening_general_max_length_mm"])\n')),
    m("G/window-line-dropped", "order 2026-10-29", "ORDER_NOTES.txt without each board's coverlay-window line, writer and read-back alike",
      (GERBER, '        lines.extend(_note(_coverlay_window_note(board, profile), "  ", "    "))\n', ""),
      (GERBER, "        phrases.append(_coverlay_window_note(board, profile))\n", "")),
    m("G/window-line-unchecked", "order 2026-10-29", "the read-back does not ask for each board's coverlay-window line",
      (GERBER, "        phrases.append(_coverlay_window_note(board, profile))\n", "")),
)

# --------------------------------------------------------------------------
# CAD mode (2026-10-20): the surface package and its HTTP routes.
# --------------------------------------------------------------------------

MESH = "surface/mesh.py"
SELECT = "surface/select.py"
CHART = "surface/chart.py"
FIT = "surface/fit.py"
PLACE = "surface/place.py"
BEND = "surface/bend.py"
SURFACE_API = "surface/api.py"
ERRORS = "surface/errors.py"
FILL = "surface/fill.py"
READER = "surface/reader.py"
CAD_MAIN = "web/cad/main.js"

SURFACE = (
    m("S/no-weld", "C-D2", "STL vertices not welded: every facet stands alone",
      (MESH, "            found = index.get(key)\n", "            found = None\n")),
    m("S/no-orientation", "C-D2", "an inside-out shell is not turned outward",
      (MESH, "            orientation.append((members, volume < 0, None))\n", "            orientation.append((members, False, None))\n")),
    m("S/no-hidden", "C-D5", "walls where two parts touch stay selectable",
      (MESH, "    hidden = {facet for facet, area in overlap_area.items() if area >= HIDDEN_FRACTION * areas[facet]}\n",
       "    hidden = set()\n")),
    m("S/no-cone", "C-D5", "the selection ignores the seed-normal limit (flat faces leak into fillets)",
      (SELECT, "            if seed_cone and dot(seed_normal, mesh.normals[other]) < cos_c:\n", "            if False:\n")),
    m("S/no-blend-barrier", "C-D5", "the surface preset keeps tight blends",
      (SELECT, "            if min_radius_mm > 0 and (\n", "            if False and (\n")),
    m("S/hinge-side", "C-D6", "unfolded facets laid on the wrong side of their hinge",
      (CHART, "    if side > 0:\n        perp = (-perp[0], -perp[1])\n", "    if side < 0:\n        perp = (-perp[0], -perp[1])\n")),
    m("S/chart-mirror", "C-D6", "the chart seen from inside the part (v reversed)",
      (CHART, "    v_axis = cross(normal, u_axis)\n    return u_axis, v_axis\n", "    v_axis = cross(u_axis, normal)\n    return u_axis, v_axis\n")),
    m("S/fit-mirror", "C-D7", "the physical top board not mirrored in the outside view of the fit",
      (FIT, "        return (aw - x1, y0, aw - x0, y1) if mirrored else box\n", "        return box\n")),
    m("S/map-mirror", "C-D9", "taxel columns not mirrored for a top Column board",
      (PLACE, "                column_x[electrode[\"net\"]] = aw - cx if mirrored else cx\n", "                column_x[electrode[\"net\"]] = cx\n")),
    m("S/no-mismatch-check", "C-D9", "a design edited after the fit is mapped anyway",
      (PLACE, "    if differing:\n        raise SurfaceError(\n            \"E_SURFACE_PLACEMENT_MISMATCH\",",
       "    if False:\n        raise SurfaceError(\n            \"E_SURFACE_PLACEMENT_MISMATCH\",")),
    m("S/no-strain-gate", "C-D8", "a curved selection is not cut down to its strain-limited disk",
      (FIT, '    if chart.kind == "curved" and chart.stats["strain_max"] > options["strain_limit"]:\n',
       "    if False:\n")),
    m("S/no-arc-exit", "C-D7", "rounded outlines get no arc exits (tails only across straight sides)",
      (FIT, "        if not chosen or chosen[0][\"chord_mm\"] < ARC_WHEN_SIDES_SHORTER_MM:\n", "        if False:\n"),
      (FIT, "        if best[\"chord_mm\"] < ARC_WHEN_SIDES_SHORTER_MM:\n", "        if False:\n")),
    m("S/surface-content-type", "C-D3", "surface routes accept any content type",
      (APP, "    if media_type != SURFACE_CONTENT_TYPE:\n", "    if False:\n")),
    # The fixes of the two surface/ reviews (stage F of claude/specs/cad-mode/PROGRESS.md).
    m("S/chart-raw-winding", "F-1", "the chart's handedness follows the file's winding (an inside-out STL gives a mirrored chart)",
      (CHART, "    signed = math.fsum(_tri_area(*[uv[v] for v in oriented_facet(mesh, f)]) * mesh.areas[f] for f in region)\n",
       "    signed = math.fsum(_tri_area(*[uv[v] for v in mesh.facets[f]]) * mesh.areas[f] for f in region)\n")),
    m("S/open-shell-origin", "F-3", "open shells oriented about the file's origin (moving the part flips its outside)",
      (MESH, "        a, b, c = (_sub(vertices[i], centre) for i in facets[facet])\n", "        a, b, c = (vertices[i] for i in facets[facet])\n")),
    m("S/no-cavity", "F-3", "a cavity's normals point into the material",
      (MESH, "            outward_flip = inverted != (depth % 2 == 1)\n", "            outward_flip = inverted\n")),
    m("S/keep-duplicates", "F-2", "repeated triangles are kept (the STL bomb)",
      (MESH, "            duplicates.add(facet)\n", "            pass\n")),
    m("S/no-crack-links", "F-9", "T-junctions split a face",
      (MESH, "    for f, g in cracks:\n", "    for f, g in ():\n")),
    m("S/no-crack-unfold", "F-9", "the unfolding does not cross T-junctions",
      (CHART, "                link = mesh.cracks.get((facet, other))\n", "                link = None\n")),
    m("S/no-crack-topology", "F-9", "T-junction pieces are not matched in the boundary loops",
      (CHART, "            chain = split_chain(mesh, start, end, vertex_set)\n", "            chain = [start, end]\n")),
    m("S/band-cut-first", "F-5", "a face with one hole is cut open as if it were a band",
      (CHART, '    if attempt["uv"] is None:\n', "    if True:\n")),
    m("S/pieces-allowed", "F-5", "a selection in several pieces is charted, the other pieces as holes",
      (CHART, "    if len(pieces) > 1:\n", "    if False:\n")),
    m("S/no-crease", "F-4", "creases between wide facets read as gentle bends",
      (BEND, "    return min_radius_mm * angle * angle / 8 > CREASE_LIFT_OFF_MM\n", "    return False\n")),
    m("S/gentle-skip", "F-4", "edges under 2 degrees count as flat (fine fillets vanish)",
      (BEND, "    if angle <= 0:\n", "    if angle <= math.radians(2.0):\n")),
    m("S/no-edge-inset", "F-8", "the stack sits on the surface's edge (rounding rejects the best proposals)",
      (FIT, "EDGE_INSET_MM = 1e-4\n", "EDGE_INSET_MM = 0.0\n")),
    # S/shape-by-pitch (fit_chart's rectangles: one proposal per array shape) retired with P5-diagonal-bus.md section 26.16:
    # CAD mode has no shape rectangle, so that loop is gone (Whole board and the field fit keep their own per-readout rule).
    m("S/crossing-clearance", "F-8", "an edge crossing the exit counts its clearance from its inner end only",
      (FIT, "                on_surface.append((inner, _exit_crossing(inner, outer, exit_segments)))\n",
       "                on_surface.append((inner, inner))\n")),
    m("S/short-side-exit", "F-7", "a straight side shorter than a tail is accepted as the exit",
      (FIT, '        if sides[index]["chord_mm"] < MIN_SIDE_MM:\n', "        if False:\n")),
    m("S/side-drift", "F-7", "a finely faceted fillet merges with the straight sides next to it",
      (SURFACE_API, "        if turn(i) > limit or drift > limit:\n", "        if turn(i) > limit:\n")),
    m("S/map-no-containment", "F-6", "the map does not check that the boards stay on the surface",
      (PLACE, '            "passed": clearance is not None,\n', '            "passed": True,\n')),
    m("S/map-no-tail-reach", "F-6", "tails that end on the part pass the map",
      (PLACE, "        reach = min(reach, y - tip)\n    return reach\n", "        reach = min(reach, y - tip)\n    return math.inf\n")),
    m("S/map-other-mesh", "F-6", "a placement maps onto another mesh",
      (PLACE, '    if fitted_mesh.get("sha256") != mesh.sha256 or fitted_mesh.get("unit") != mesh.unit:\n', "    if False:\n")),
    m("S/map-other-selection", "F-6", "a placement maps onto another selection",
      (PLACE, '    if selection != placement["selection"]:\n', "    if False:\n")),
    m("S/map-template-free", "F-6", "a design moved to another template keeps its placement",
      (PLACE, 'GEOMETRY_KEYS = ("template_id", "matrix",', 'GEOMETRY_KEYS = ("matrix",')),
    m("S/reader-swapped", "F-6", "FlexiTac sense and drive lines taken from the wrong connector",
      (PLACE, "    sense_index, drive_index = (row_pin, column_pin) if row_pins == 16 else (column_pin, row_pin)\n",
       "    sense_index, drive_index = (column_pin, row_pin) if row_pins == 16 else (row_pin, column_pin)\n")),
    m("S/chord-spacing", "F-6", "taxel spacing measured as a 3D chord (curved proposals fail their own map)",
      (PLACE, "    return math.fsum(norm(sub(points[k + 1], points[k])) for k in range(steps))\n", "    return norm(sub(points[-1], points[0]))\n")),
    m("S/no-placement-check", "F-6", "a damaged placement reaches the geometry (a crash, not a 422)",
      (PLACE, '    for key in ("base_from_uv", "base_inward_uv", "field_origin_base"):\n', "    for key in ():\n")),
    m("S/map-infinite-record", "F-6", "a missing measurement is written as an infinity (invalid JSON)",
      (PLACE, "    measured_value = measured if math.isfinite(measured) else None\n", "    measured_value = measured if measured != math.inf else None\n")),
    m("S/big-integer", "F-7", "an integer too large for a float crashes the request",
      (ERRORS, "    except OverflowError:\n        number = math.inf\n", "    except ZeroDivisionError:\n        number = math.inf\n")),
    m("S/long-number-header", "F-7", "a header number of thousands of digits is parsed (it freezes Python 3.9)",
      (SURFACE_API, "    if _LONG_NUMBER.search(header):\n", "    if False:\n")),
    m("S/mesh-cache-unit", "F-7", "the mesh cache ignores the unit (a mesh served at the wrong scale)",
      (SURFACE_API, "        key = (sha256, unit if unit is not None else _GUESSED_UNITS.get(sha256))\n", "        key = (sha256, _GUESSED_UNITS.get(sha256))\n")),
    m("S/shared-slot", "F-7", "CAD-mode requests take the rectangular mode's generation slots",
      (APP, "        slots = self.server.surface_slots\n", "        slots = self.server.generation_slots\n")),
    m("S/no-big-drain", "F-7", "a mesh just over the limit gets a TCP reset instead of its 413",
      (APP, "                self._drain = (size, MAX_SURFACE_DRAIN_S)\n", "                pass\n")),
    m("S/cli-map-status", "F-7", "cli.py surface map exits 0 when the map fails its checks",
      (CLI, '            return 0 if mapped["ok"] else 1, mapped\n', "            return 0, mapped\n")),
    m("S/centre-line-obstacles", "F-8", "obstacles block only the cells their centre line crosses (boards overlap their edges)",
      (FIT, "            low, high = self.y0 + j * self.h, self.y0 + (j + 1) * self.h\n            xs = [p[0]",
       "            low = high = self.y0 + (j + 0.5) * self.h\n            xs = [p[0]")),
    m("S/cli-nan-pick", "F-7", "cli.py surface takes a NaN pick (it picks facet 0)",
      (CLI, "    if len(parts) != 3 or not all(math.isfinite(part) for part in parts):\n", "    if len(parts) != 3:\n")),
    m("S/nesting-open-outer", "G-R4.1", "an open shell (a cup) makes the part standing in it a cavity",
      (MESH, "        if not closed:\n            del inside[j]\n", "        if False:\n            del inside[j]\n")),
    m("S/nesting-surface-probe", "G-R4.1", "cavities are told by parity from a shell's first vertex (a part touching a pocket wall is a cavity)",
      (MESH, "        probes[i] = _inner_probes(members, inverted, flip, facets, vertices)\n",
       "        probes[i] = [vertices[facets[members[0]][0]]]\n")),
    m("S/wedge-tie-links", "G-R4.2", "coincident walls running the same way are linked (an inside-out body joins its neighbour and stays inside-out)",
      (MESH, "    return entries, group, {g for g, value in balance.items() if abs(value) > 1}\n", "    return entries, group, set()\n")),
    m("S/coincident-walls-unfaced", "G-R4.2", "the contact face of a body turned outward keeps the file's winding (the walls are not hidden)",
      (MESH, "    if wedges:\n        _face_coincident_walls(", "    if False:\n        _face_coincident_walls(")),
    m("S/crack-walk-fine", "G-R4.3", "every open edge is walked on the finest T-junction grid (long edges cost their length)",
      (MESH, "        while length > _CRACK_STEPS * cell * _CRACK_LEVEL ** level:\n            level += 1\n",
       "        while False:\n            level += 1\n")),
    m("S/cover-no-saturation", "G-R4.4", "a facet already covered enough to be hidden is clipped again (stacked facets cost pairs x 2 clips)",
      (MESH, "            if first in saturated:\n                continue\n", "            if False:\n                continue\n")),
    m("S/far-coordinates", "G-R4.5", "huge finite ASCII coordinates reach the geometry (OverflowError, HTTP 500)",
      (MESH, "    if max(abs(value) for value in lows + highs) * scale > MAX_COORDINATE_MM:\n", "    if False:\n")),
    m("S/far-coordinates-unscaled", "G-R2.2", "the coordinate bound is checked before the unit scale",
      (MESH, "    if max(abs(value) for value in lows + highs) * scale > MAX_COORDINATE_MM:\n",
       "    if max(abs(value) for value in lows + highs) > MAX_COORDINATE_MM:\n")),
    m("S/nesting-shell-cap", "G-R4.6", "with more than 32 shells cavities are oriented outward",
      (MESH, "    if not oriented or len(bodies) < 2 or not outers:\n", "    if not oriented or len(bodies) < 2 or len(orientation) > 32 or not outers:\n")),
    m("S/crack-edges-silent", "G-R4.7", "more than MAX_CRACK_EDGES open edges skip the T-junction repair without a warning",
      (MESH, "        return {}, {}, every_edge, [], f\"More than {MAX_CRACK_EDGES} open edges; cracks (T-junctions) were not repaired.\"\n",
       "        return {}, {}, every_edge, [], None\n")),
    m("S/flat-sheet-noise", "G-R4.8", "a flat sheet far from the origin is oriented by its float32 rounding",
      (MESH, "    if limit < abs(volume) <= limit + noise * magnitude:", "    if False:")),
    m("S/ascii-name-tokens", "G-R4.10", "the solid's name is read as STL tokens (a name with 'solid' or 'facet' breaks the file)",
      (MESH, "        end = len(data) if line_end is None else line_end.start()\n", "        end = start\n")),
    m("S/cover-fixed-tolerance", "G-R2.6", "the covered-wall tolerances stay 0.05 mm on a tiny part (a file in metres read as mm)",
      (MESH, "    reach = min(1.0, math.sqrt(", "    reach = 1.0 or min(1.0, math.sqrt(")),
    m("S/crack-budget-wipes", "G-R5.2", "reaching the T-junction budget drops the repairs already found",
      (MESH, "    if not edge_splits:\n        return {}, {}, every_edge, [], warning\n",
       "    if stopped or not edge_splits:\n        return {}, {}, every_edge, [], warning\n")),
    m("S/cover-count-touching", "G-R5.3", "every pair of touching boxes counts against the covered-wall bound (a fine contact wall stays selectable)",
      (MESH, "        lift_g, lift_f = height(f, g), height(g, f)\n", "        return True\n")),
    m("S/nesting-unfiltered-rays", "G-R5.4", "every facet of an enclosing shell is tested against every probe ray",
      (MESH, "            first = bisect.bisect_left(ys, min(a[1], b[1], c[1]))\n            last = bisect.bisect_right(ys, max(a[1], b[1], c[1]))\n",
       "            first, last = 0, len(ys)\n")),
    m("S/coincident-walls-unpaired", "G-R4.2", "coincident walls facing the same way are turned round with no facet beside them to show a wrong winding (a repeated body is hidden)",
      (MESH, "            if not unpaired:\n                continue\n", "            if False:\n                continue\n")),
    m("S/contact-copies-dropped", "G-R4.2", "an inside-out body's contact facets repeating the other body's are dropped as duplicates (the body stays inside-out)",
      (MESH, "        if min(uses) >= 2 and max(uses) >= 3:\n", "        if False:\n")),
    m("S/wall-order-by-id", "G-R4.2", "coincident walls are paired in facet order (touching bodies turned in space split into two shells)",
      (MESH, "            if entries[i][2] == entries[k][2]:\n                entries[i], entries[after]", "            if False:\n                entries[i], entries[after]")),
    m("S/joined-pieces-unoriented", "G-R4.2", "a shell joined from pieces without an outside keeps the file's winding (a repeated body stays inside-out)",
      (MESH, "        elif volume < 0:\n            flipped.symmetric_difference_update(members)\n", "        elif False:\n            flipped.symmetric_difference_update(members)\n")),
    m("S/nesting-by-piece", "G-R4.2", "a body touching an inside-out body encloses nothing (its cavity is turned outward)",
      (MESH, "    body = _components(_neighbors(neighbor_lists, links + chains), degenerate) if wedges else None\n", "    body = None\n")),
    m("S/nesting-strict-box", "G-R4.1", "a part resting on a cavity's floor or wall is taken for a cavity",
      (MESH, "all(b[k] <= a[k] and a[k + 3] <= b[k + 3] for k in range(3))", "all(b[k] < a[k] and a[k + 3] < b[k + 3] for k in range(3))")),
    m("S/nesting-sweep-x", "G-R4.6", "the nesting candidates are swept along x only (parts side by side along y exhaust the budget)",
      (MESH, "    axis = min(sweeps)[1]\n", "    axis = 0\n")),
    m("S/crack-level-floor", "G-R4.3", "a cell crowded on the median edge's grid is skipped (a dense crack among long edges stays open)",
      (MESH, "                elif size / _CRACK_LEVEL >= _CRACK_FINEST_MM:\n", "                elif size > cell:\n")),
    m("S/flat-sheet-noise-wide", "G-R4.8", "the float32 allowance is 64 times the rounding (a curved sheet far from the origin loses its outside)",
      (MESH, "    noise = total * 2.0 ** -21\n", "    noise = total * 2.0 ** -18\n")),
    m("S/ascii-one-line", "G-R4.10", "a file written on one line is read by lines (its first line swallows the facets)",
      (MESH, "        one_line = last_break < current[0].end()\n", "        one_line = False\n")),
    m("S/nesting-exact-gaps", "G-R5.4", "an enclosing body with a gap of float noise is open (its cavities are turned outward)",
      (MESH, "        closed, used = _twinned(holes[j], vertices, MAX_NESTING_TESTS - tests)\n", "        closed, used = False, 0\n")),
    m("S/normals-cancel-refused", "G-R4.0", "a band whose normals cancel out exactly is refused instead of being cut open",
      (CHART, '        return {"vertex_ids": vertex_ids, "normal": None, "conflict": None, "uv": None}\n',
       '        raise SurfaceError("E_SURFACE_NOT_DEVELOPABLE")\n')),
    m("S/hinge-3d-length", "G-R3.4", "the unfolding divides the placed hinge by its 3D length (the error grows row by row on thin strips)",
      (CHART, "    ex = ((pb[0] - pa[0]) / placed, (pb[1] - pa[1]) / placed)\n", "    ex = ((pb[0] - pa[0]) / ab, (pb[1] - pa[1]) / ab)\n")),
    m("S/unfold-stretch-ignored", "G-R3.4", "an unfolding that nearly closes on a doubly curved patch counts as exact (its facets stretch by 1%)",
      (CHART, "    if conflict <= UNFOLD_CONFLICT_MM and _keeps_lengths(mesh, region, vertex_ids, uv):\n",
       "    if conflict <= UNFOLD_CONFLICT_MM:\n")),
    m("S/antipodal-cone", "G-R4.9", "a 180 degree cone still tests the seed normal (facets opposite the seed round out of a band)",
      (SELECT, "    seed_cone = theta_c_deg < 180.0\n", "    seed_cone = True\n")),
    m("S/solve-cg-only", "G-R5.0", "curved charts are solved by conjugate gradients alone (8-12 s at 2,900 vertices)",
      ("surface/solve.py", "    return free, reduced, coupled, diagonal, _factor(reduced)\n", "    return free, reduced, coupled, diagonal, None\n")),
    m("S/grid-bounding-box", "G-R5.1", "the point index holds each facet in every cell of its bounding box (hundreds per sliver of a fan)",
      (CHART, "            if cy == ay:\n", "            if True:\n")),
    m("S/seam-edge-facets-only", "G-R4.0", "a band is opened by removing the facets on its seam's edges (each inner seam vertex becomes a bowtie)",
      (CHART, "                            if z != v and frozenset((v, z)) not in seam_edges:\n", "                            if False:\n"),
      (CHART, "    sides = sorted((side(True), side(False)), key=lambda removed: math.fsum(mesh.areas[f] for f in removed))\n",
       "    sides = [side(True) | side(False)]\n")),
    m("S/unfold-singular-values", "G-R3.4", "the unfolding is tested on its singular values (a needle facet or float32 rounding makes a developable patch curved)",
      (CHART, "            if abs(dist2(uv[p], uv[q]) - length) > UNFOLD_STRAIN * length + floor:\n",
       "            if max(abs(s - 1) for s in singular_values(mesh, facet, uv)) > UNFOLD_STRAIN:\n")),
    m("S/unfold-no-float32", "G-R3.4", "the unfolding's edge lengths get no float32 allowance (fine fillets far from the origin count as curved)",
      (CHART, "    floor = UNFOLD_FLOAT32 * max(abs(x) for v in vertex_ids for x in mesh.vertices[v])\n", "    floor = 0.0\n")),
    m("S/index-drops-long", "G-R3.0", "the segment index registers a long segment in the cells filled so far (clearance overstated)",
      (FIT, "            keys = self._cells(a, b)\n", "            keys = self._keys(a, b, 0.0)\n")),
    m("S/arc-tail-corners", "G-R1.0/R3.2", "the tails are sized at their two corners (they reach less than the extension beyond an arc)",
      (FIT, "            xs += [x - 1e-9, x]\n", "            pass\n")),
    m("S/body-beyond-exit", "G-R1.1", "the containment check lets the field and the channels hang beyond the exit",
      (FIT, "        if tail_roots is not None and not _crosses_below(", "        if False and not _crosses_below(")),
    m("S/max-area-one-pitch", "G-R3.1", "max_area grows the min-pitch staircase only (fields 2-3x too small)",
      (FIT, "        pitches = max_area_pitches(pitch) if area else [pitch]\n", "        pitches = [pitch]\n")),
    m("S/tj-half-radius", "G-R3.3", "a strip split at a T-junction bends at half its radius",
      (BEND, "    if angle > 0:\n        width_f = _piece_width(", "    if False:\n        width_f = _piece_width(")),
    m("S/bends-unindexed", "G-R3.6", "every board edge is tested against every bend segment",
      (FIT, "            for c, d in bend_index.near(a, b, 0.0):\n", "            for c, d in bend_index.segments:\n")),
    m("S/scanline-all-edges", "G-R5.1", "the raster scans every outline segment on every line",
      (FIT, "        lines = _scanlines(polygons, [self.y0 + j * self.h + (eps if j == 0 else 0.0) - (eps if j == self.ny else 0.0) for j in range(self.ny + 1)])\n",
       "        lines = [_scanline(polygons, y) for y in [self.y0 + j * self.h + (eps if j == 0 else 0.0) - (eps if j == self.ny else 0.0) for j in range(self.ny + 1)]]\n")),
    m("S/side-renumbered", "G-R2.1", "{side: n} is read from the strain-limited disk's sides, not the selection's",
      (FIT, '        if isinstance(base, Mapping) and set(base) == {"side"}:\n            # {side: n} numbers',
       "        if False:\n            # {side: n} numbers")),
    m("S/strain-bisect-cold", "G-R5.0", "the strain limit bisects from half the selection (large cold solves)",
      (FIT, "            radius = math.sqrt(x)\n", "            radius = None\n")),
    m("S/strain-repeats-count", "G-R5.0", "a trial that repeats a disk already tried uses up the strain search",
      (FIT, "    for _ in range(3 * STRAIN_BISECTIONS):", "    for _ in range(STRAIN_BISECTIONS):")),
    m("S/placement-null-to", "G-R1.3", "an explicit null base_to_uv passes the placement check (a TypeError, not a 422)",
      (PLACE, "        if key not in placement and not required:\n", "        if placement.get(key) is None and not required:\n")),
    m("S/map-exit-edges-unbounded", "G-R2.0", "exit edges beyond the chart's outline reach the containment check (an IndexError, not a 422)",
      (PLACE, '    if any(edge >= segments for edge in placement["exit_edges"]):\n', "    if False:\n")),
    m("S/placement-inward-length", "G-R2.0", "a placement's inward vector of any length scales the base frame",
      (PLACE, "    if abs(hypot2(*inward) - 1) > 1e-6:\n", "    if hypot2(*inward) < 1e-9:\n")),
    m("S/placement-unbounded", "G-R3.5", "finite but huge placement coordinates overflow the frame and the grids (a crash, not a 422)",
      (PLACE, '            finite_number(c, f"placement.{key}[{k}]", -MAX_PLACEMENT_MM, MAX_PLACEMENT_MM)\n', '            finite_number(c, f"placement.{key}[{k}]")\n')),
    m("S/distance-box-grid", "G-R1.2", "the taxel distance check searches a grid of facet boxes (long strips: hundreds of facets per taxel)",
      (PLACE, "    selected = set(chart.facets)\n    worst = 0.0\n    for point, facet in hits:\n        if facet not in selected:\n            return math.inf\n"
              "        worst = max(worst, point_triangle_distance(point, *mesh.facet_points(facet)))\n    return worst\n",
       "    points = [point for point, _ in hits]\n    if not points:\n        return 0.0\n    boxes = {}\n    for facet in chart.facets:\n"
       "        pts = mesh.facet_points(facet)\n        boxes[facet] = [min(p[k] for p in pts) for k in range(3)] + [max(p[k] for p in pts) for k in range(3)]\n"
       "    sizes = sorted(max(b[3] - b[0], b[4] - b[1], b[5] - b[2]) for b in boxes.values())\n    cell = max(sizes[len(sizes) // 2], 0.5)\n    grid: dict = {}\n"
       "    for facet, b in boxes.items():\n        lo = [int(math.floor((b[k] - 1e-3) / cell)) for k in range(3)]\n        hi = [int(math.floor((b[k + 3] + 1e-3) / cell)) for k in range(3)]\n"
       "        for i in range(lo[0], hi[0] + 1):\n            for j in range(lo[1], hi[1] + 1):\n                for k in range(lo[2], hi[2] + 1):\n"
       "                    grid.setdefault((i, j, k), []).append(facet)\n    worst = 0.0\n    for point in points:\n"
       "        best = min((point_triangle_distance(point, *mesh.facet_points(f)) for f in grid.get(tuple(int(math.floor(c / cell)) for c in point), [])), default=math.inf)\n"
       "        worst = max(worst, best)\n    return worst\n")),
    m("S/distance-every-facet", "G-R5.1", "each taxel's distance is searched over every selected facet (sliver fans: taxels x facets)",
      (PLACE, "        worst = max(worst, point_triangle_distance(point, *mesh.facet_points(facet)))\n",
       "        worst = max(worst, min(point_triangle_distance(point, *mesh.facet_points(f)) for f in selected))\n")),
    m("S/strain-every-facet", "G-R5.5", "the strain under the boards runs the exact overlap test on every chart facet",
      (PLACE, "        if value <= worst:\n            break  # sorted: no facet further down raises the maximum\n", "        if False:\n            break\n")),
    m("S/spacing-fixed", "G-R1.4", "the spacing tolerance stays 0.5% under a raised strain limit (fit proposals fail their map)",
      (PLACE, '    spacing_limit = max(SPACING_TOLERANCE, options["strain_limit"] + SPACING_CHORD_ERROR)\n', "    spacing_limit = SPACING_TOLERANCE\n")),
    m("S/overlay-chord", "G-R1.5", "the 3D overlay stops at an arc exit's chord (the tails on the part are cut short)",
      (PLACE, "            hit = chart_point_to_3d(chart, mesh, frame.to_chart(p))\n",
       "            hit = chart_point_to_3d(chart, mesh, frame.to_chart(p)) if frame.height_above_base(p) >= -1e-9 else None\n")),
    m("S/cli-map-options", "G-R2.3", "cli.py surface map ignores --options (the placement's always win)",
      (CLI, '            if args.options is not None:\n                header["options"] = options', '            if False:\n                header["options"] = options')),
    m("S/cli-pretty-recursion", "G-R2.4", "cli.py --pretty fails on a placement nested too deeply for the indenting encoder",
      (CLI, "    except RecursionError:\n        if not pretty:\n            raise\n", "    except ZeroDivisionError:\n        if not pretty:\n            raise\n")),
    m("S/cli-value-error-input", "G-R2.2", "cli.py surface reports an internal ValueError as an input error (exit 2, not 3)",
      (CLI, '    except OSError as error:\n        return 2, _failure("E_CLI_INPUT", str(error))\n',
       '    except (OSError, ValueError) as error:\n        return 2, _failure("E_CLI_INPUT", str(error))\n')),
    m("S/cli-pick-parses-twice", "G-R5.6", "cli.py surface --pick parses the STL outside the mesh cache (twice in all)",
      (CLI, "            mesh = load_mesh(header, data)\n", '            mesh = __import__("surface.mesh", fromlist=["read_stl"]).read_stl(data, unit=args.unit)\n')),
    m("S/digit-guard-quadratic", "G-R2.5", "the header digit guard searches from every digit (quadratic in a run's length)",
      (SURFACE_API, '_LONG_NUMBER = re.compile(rb"(?<![0-9])[0-9]{%d}" % (MAX_NUMBER_DIGITS + 1))', '_LONG_NUMBER = re.compile(rb"[0-9]{%d}" % (MAX_NUMBER_DIGITS + 1))')),
    m("S/mesh-cache-bends", "G-R5.4", "the mesh cache bound ignores the meshes' bend measurements",
      (SURFACE_API, "    return mesh.facet_count + len(mesh.bend_cache) // 2\n", "    return mesh.facet_count\n")),
    m("S/cli-base-long-side", "G-R2.2", "cli.py --base converts any run of digits with int() (an internal error past 4300 digits on 3.11+)",
      (CLI, '        if len(text) <= MAX_NUMBER_DIGITS:\n            try:\n                return {"side": int(text)}\n            except ValueError:\n                pass\n',
       '        return {"side": int(text)}\n')),
    m("S/placement-depth", "G-R2.4", "map takes a placement nested at any depth (its echo is beyond the CLI's encoders: exit 3, not 1)",
      (PLACE, "    if _nesting(placement, MAX_PLACEMENT_DEPTH) > MAX_PLACEMENT_DEPTH:\n", "    if False:\n")),
    m("S/map-tails-unchecked", "G-R1.1", "the map's containment check lets the body cross the exit",
      (PLACE, ', options["edge_margin_mm"], tail_roots=tail_roots)\n', ', options["edge_margin_mm"])\n')),
)


# --------------------------------------------------------------------------
# The masked taxel field (matrix.mask): phase P1, the contract; phase P2, the builders.
# --------------------------------------------------------------------------

MASKED_FIELD = (
    m("M/full-mask-kept", "mask P1", "a full-rectangle mask is kept (the unmasked design gets another build id)",
      (CORE, "    if rows is not None and len(mask) == rows and all(pair == [1, columns] for pair in mask):\n", "    if False:\n")),
    m("M/mask-on-generic", "mask P1", "the generic template accepts matrix.mask",
      (CORE, "                    elif path in OPTIONAL_FIELDS and template_of(data) in OPTIONAL_FIELD_TEMPLATES[path]:\n",
       "                    elif path in OPTIONAL_FIELDS:\n")),
    m("M/identity-no-mask", "mask P1", "the field mask is missing from the hashed identity (a masked and an unmasked build could share an id)",
      (CORE, '        identity["mask"] = MASK_VERSION\n', "        pass\n")),
    m("M/no-column-gap-check", "mask P1", "a column whose taxels skip a row passes validation (E_MASK_COLUMN_GAP never raised)",
      (CORE, "        elif active[-1] - active[0] + 1 != len(active):\n", "        elif False:\n")),
    m("M/inactive-gap-silent", "mask P1", "no W_MASK_INACTIVE_GAP for inactive crossings closer than 0.15 mm",
      (CORE, "                if separation < MASK_INACTIVE_GAP_WARNING_MM - _EPSILON:\n", "                if False:\n")),
    m("M/size-advice-rows", "mask P1", "the size advice of a masked design lowers matrix.rows or matrix.columns (the mask no longer fits)",
      (LAYOUT, "        single = single[:3]\n", "        pass\n")),
    m("M/row-frame-sides-swapped", "mask P1", "the Row-frame slots of equal and opposite tail sides swapped",
      (LAYOUT, "    if _equal_sides(design):\n        return [(columns - last, columns - first) for first, last in _row_spans(design)]\n",
       "    if not _equal_sides(design):\n        return [(columns - last, columns - first) for first, last in _row_spans(design)]\n")),
    m("M/class-no-taper", "mask P1", "the straight Row channel ignores the lane taper (every row must reach the channel side)",
      (LAYOUT, "        tau = max(0, math.ceil(round6(edge - active_x) / pitch_x - _FLOAT_NOISE_MM))\n", "        tau = 0\n")),
    m("M/class-no-column-rule", "mask P1", "the straight Column fan-out takes columns whose stub passes a row on its far side",
      (LAYOUT, "        if 1 <= row <= rows and slot >= spans[row - 1][0]:\n", "        if False:\n")),
    m("M/export-template-only", "mask P1", "the exports name only the template among the identity extras (no mask)",
      (GERBER, "    extras = {key: manifest[key] for key in engine_core.IDENTITY_EXTRAS if key in manifest}\n",
       '    extras = {key: manifest[key] for key in ("template",) if key in manifest}\n')),
    # Phase P2, the builders: the straight Row channel and Column fan-out of masked designs.
    m("M/no-class-gate", "mask P2", "a mask outside the straight construction classes passes the feasibility check (no E_MASK_ROUTING)",
      (LAYOUT, "    _, issue = mask_class(design, profile)\n    if issue is not None:\n        errors.append(issue)\n",
       "    _, issue = mask_class(design, profile)\n    if False:\n        errors.append(issue)\n")),
    m("M/row-stub-common-end", "mask P2", "every Row stub ends at the field's common left end, short of a row that steps away from the channel",
      (LAYOUT, "        fanout += [[lanes[logical - 1], round6(center_y)], [start, round6(center_y)]]\n",
       "        fanout += [[lanes[logical - 1], round6(center_y)], [active_x - rules.overhang, round6(center_y)]]\n")),
    m("M/column-stub-common-end", "mask P2", "every Column stub ends at the field's common bottom, short of a raised column's electrode",
      (LAYOUT, "    fanout.append([center, bottom])\n", '    fanout.append([center, plan["active"][1] - rules.overhang])\n')),
    m("M/no-lane-taper", "mask P2", "the masked Row field keeps the unmasked start (no slide toward the channel along the lane taper)",
      (LAYOUT, "    if any(lo for lo, _ in spans):\n", "    if False:\n")),
    m("M/band-fillers-dropped", "mask P2", "no fillers between consecutive bands (the window ring, P and F lose the gaps between electrodes)",
      (GEOMETRY, "        fillers.append(tuple(filler))\n", "        pass\n")),
    m("M/window-no-expansion", "mask P2", "the polygon field window is the electrodes themselves, without the coverlay expansion",
      (LAYOUT, "    grow = rules.expansion\n", "    grow = 0.0\n")),
    m("M/full-span-polygon", "mask P2", "a merged window becomes a polygon even when every span is the same (not today's rectangle)",
      (LAYOUT, '    if field["kind"] != "electrode_field_opening" or all(span == spans[0] for span in spans):\n',
       '    if field["kind"] != "electrode_field_opening":\n')),
    m("M/polygon-window-unturned", "mask P2", "apply_tail_side leaves a polygon window's points in the canonical frame",
      (LAYOUT, '            rect["points"] = [convert(point) for point in rect["points"]]\n', "            pass\n")),
    m("M/active-outline-unturned", "mask P2", "apply_tail_side leaves grid_registration.active_outline in the canonical frame",
      (LAYOUT, '        registration["active_outline"] = [convert(point) for point in registration["active_outline"]]\n', "        pass\n")),
    m("M/row-body-no-bottom-width", "mask P2", "the Row body above the expansion follows the field only (not today's width where the field is as wide as its bottom row)",
      (LAYOUT, "        right = max(end, xb) if end >= reach - _FLOAT_NOISE_MM else end\n", "        right = end\n")),
    m("M/row-body-rectangle", "mask P2", "the masked Row body keeps the bottom row's width all the way up (no staircase)",
      (LAYOUT, "        right = max(end, xb) if end >= reach - _FLOAT_NOISE_MM else end\n", "        right = max(reach, xb)\n")),
    m("M/column-body-rectangle", "mask P2", "the masked Column body keeps the full height above every column (no staircase)",
      (LAYOUT, "    tops = [body_top if abs(end - full) <= _FLOAT_NOISE_MM else end for _, _, _, end in slabs]\n",
       "    tops = [body_top for _ in slabs]\n")),
    m("M/taxel-mask-frame-slots", "mask P2", "grid_registration.taxel_mask written in Row-frame slots instead of the readout's net indices",
      (LAYOUT, '        "row_spans": [[first, last] for first, last in mask],\n',
       '        "row_spans": [[lo + 1, hi + 1] for lo, hi in row_frame_spans(design)],\n')),
    # Phase P2, the DRC and registration of masked boards.
    m("M/margin-to-bounding-box", "mask P2", "the masked active-field margin measured to the crossing region's bounding box (0 on a staircase outline)",
      (DRC, '    region = [list(map(float, point)) for point in board["grid_registration"]["active_outline"]]\n',
       '    region = bounds_corners(bounds_of(board["grid_registration"]["active_outline"]))\n')),
    m("M/no-outline-equality", "mask P2", "grid_registration.active_outline need not be the region the electrodes give",
      (DRC, "    if not _same_ring(region, _electrode_region(board, rules), epsilon):\n", "    if False:\n")),
    m("M/window-shape-unchecked", "mask P2", "a polygon field window need not be simple, rectilinear and orthogonally convex",
      (DRC, "        sound = not is_polygon or (ring_is_simple(ring) and is_rectilinear(ring, epsilon) and is_orthogonally_convex(ring))\n",
       "        sound = True\n")),
    m("M/bridge-by-bounding-box", "mask P2", "the coverlay bridge to a polygon window measured to its bounding box (0 in its staircase's empty corner)",
      (DRC, "            gap = _ring_gap(rings[first_index], rings[second_index], reach)\n",
       "            gap = box_gap(ring_boxes[first_index], ring_boxes[second_index])\n")),
    m("M/strict-own-net-skip", "mask P2", "the masked window-to-trace rule skips every route of a net the window lists (today's unmasked rule: vacuous on the field window)",
      (DRC, "        opening_index, a, b = ring_edges[edge_index]\n",
       '        opening_index, a, b = ring_edges[edge_index]\n        if net in openings[opening_index]["nets"]:\n            continue\n')),
    m("M/strict-no-clip", "mask P2", "the masked window-to-trace rule does not clip a route at its own contact or electrode",
      (DRC, "        zones = [(box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow) for box in own]\n", "        zones = []\n")),
    m("M/strict-own-window-edges-kept", "mask P2", "the masked window-to-trace rule keeps the window edges on a route's own feature (the clip boundary then measures the rule itself)",
      (DRC, "            remaining = [piece for c, d in remaining for piece in segment_parts_off_box_boundary(c, d, window, epsilon)]\n",
       "            pass\n")),
    m("M/strict-inside-unchecked", "mask P2", "a route deep inside another electrode's part of a polygon window passes the window-to-trace rule",
      (DRC, "        if point_in_polygon(middles[part_index], rings[opening_index]):\n", "        if False:\n")),
    m("M/exposure-by-bounding-box", "mask P2", "an electrode's exposure measured to the polygon window's bounding box",
      (DRC, "                margins.append(_box_ring_margin(box, ring, nearest[opening_index].get(feature_index), epsilon))\n",
       "                other = bounds_of(ring)\n                margins.append(min(box[0] - other[0], box[1] - other[1], other[2] - box[2], other[3] - box[3]))\n")),
    m("M/stack-not-mirrored", "mask P2", "the stack frame does not turn the physical top board over",
      (DRC, "    flip_x, flip_y = top and across_tail, top and not across_tail\n", "    flip_x, flip_y = False, False\n")),
    m("M/no-crossing-test", "mask P2", "the stacked electrodes' crossings are never compared with the taxel mask",
      (DRC, "            if (overlap_x > epsilon and overlap_y > epsilon) != active:\n", "            if False:\n")),
    m("M/masked-grid-along-unchecked", "mask P2", "a masked electrode's ends are not checked against its span of the taxel grid",
      (DRC, "        worst = max(worst, abs(box[long_axis] - start), abs(box[long_axis + 2] - end))\n", "        pass\n")),
    m("M/taxel-masks-not-compared", "mask P2", "the two boards' taxel masks are not compared",
      (DRC, '        "taxel_mask_identical": masks[0] is not None and masks[0] == masks[1],\n', '        "taxel_mask_identical": True,\n')),
    m("M/inactive-separation-unchecked", "mask P2", "electrodes touching at an inactive crossing pass the registration",
      (DRC, '        "inactive_crossings_separated": separation is None or separation > epsilon,\n', '        "inactive_crossings_separated": True,\n')),
    # Phase P2, the reviews' fixes: the masked grid across the electrodes, record 12's touching and cutout rules,
    # P inside the outline and the trace overlap report (the exporter's refusal of masked builds,
    # M/export-masked-ungated, went with phase P3, which exports them, and the map's, M/map-masked-ungated, with
    # phase P4, which maps them).
    m("M/masked-grid-across-unchecked", "mask P2 review", "a masked electrode moved or widened across its length passes the registration",
      (DRC, "        worst = max(worst, abs(box[across] - origin[across] - index * pitch_across), abs(box[across + 2] - box[across] - cell_across))\n",
       "        pass\n")),
    m("M/window-touch-one-vertex", "mask P2 review", "a polygon window touching the outline is judged by one vertex (one on the outline fails it)",
      (DRC, "    if not any(near):\n        return point_in_polygon(inner[0], outer)\n", "    if True:\n        return point_in_polygon(inner[0], outer)\n")),
    m("M/window-cutouts-unchecked", "mask P2 review", "a polygon window may overlap a routed cutout",
      (DRC, "        if not sound or not _swept_inside(ring, outline, epsilon) or any(_rings_touch(ring, cutout, epsilon) for cutout in cutouts):\n",
       "        if not sound or not _swept_inside(ring, outline, epsilon):\n")),
    m("M/region-outside-unchecked", "mask P2 review", "a crossing region P off the board (no outline edge in reach) passes the active-field margin",
      (DRC, "    if not point_in_polygon(region[0], outline) or any(point_in_polygon(region[0], cutout) for cutout in cutouts):\n", "    if False:\n")),
    m("M/trace-overlap-unmeasured", "mask P2 review", "the registration reports no Row trace running on a Column trace in the stack",
      (DRC, "            runs.setdefault((row_net, column_net), []).append(run)\n            areas.append(run * width)\n", "            pass\n")),
    m("M/trace-overlap-crossings-counted", "mask P2 review", "the trace overlap report counts crossings at an angle as runs",
      (DRC, "        if abs(ux * vy - uy * vx) > _PARALLEL_RAD * math.hypot(vx, vy):\n            continue\n", "        pass\n")),
    # Phase P3, the exporter: the polygon field window in the GTS and its read-back, the form checks of polygon
    # openings, the taxel field of ORDER_NOTES.txt and taxels.csv with its read-back.
    m("M/gts-polygon-bounding-box", "mask P3", "the GTS writes a polygon field window as its bounding rectangle (the coverlay opens over the inactive corner)",
      (GERBER, '            ring = opening["points"]\n',
       '            xs, ys = [point[0] for point in opening["points"]], [point[1] for point in opening["points"]]\n'
       '            ring = [[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]]\n')),
    m("M/gts-polygon-unread", "mask P3", "the read-back compares a polygon field window's GTS region with itself instead of the ring",
      (GERBER, '    _same_regions(_GTS, gts["regions"], _opening_regions(board["layers"]["top_coverlay_openings"]))\n',
       '    _same_regions(_GTS, gts["regions"], [region[:-1] if opening.get("shape") == "polygon" else expected for region, opening, expected in '
       'zip(gts["regions"], board["layers"]["top_coverlay_openings"], _opening_regions(board["layers"]["top_coverlay_openings"]))])\n')),
    m("M/polygon-kind-unchecked", "mask P3", "any coverlay opening may be a polygon, the gang contact window included",
      (GERBER, '    if opening.get("kind") != "electrode_field_opening":\n', "    if False:\n")),
    m("M/polygon-on-unmasked-board", "mask P3", "a polygon field window passes the form check on a board without a taxel mask",
      (GERBER, '    if not isinstance(registration, Mapping) or "taxel_mask" not in registration:\n', "    if False:\n")),
    m("M/polygon-rect-fields-kept", "mask P3", "a polygon opening may carry rectangle fields (a reader that knows only rectangles then opens the box)",
      (GERBER, "    if present:\n", "    if False:\n")),
    m("M/polygon-ring-unchecked", "mask P3", "a polygon field window need not be a simple ring (a self-crossing region is written)",
      (GERBER, "    _check_ring(points, label)\n", "    pass\n")),
    m("M/polygon-off-grid", "mask P3", "a polygon window's vertices need not lie on the 1e-6 mm grid",
      (GERBER, "    if any(abs(float(value) - round(float(value), 6)) > _GRID_NOISE_MM for point in points for value in point):\n", "    if False:\n")),
    m("M/polygon-slanted-edges", "mask P3", "a polygon window may have edges that are neither horizontal nor vertical",
      (GERBER, "        if first[0] != second[0] and first[1] != second[1]:\n", "        if False:\n")),
    m("M/polygon-clockwise", "mask P3", "a clockwise polygon window passes the form check",
      (GERBER, "    if twice_area <= 0:\n", "    if False:\n")),
    m("M/taxels-active-inverted", "mask P3", "taxels.csv marks the active positions 0 and the inactive ones 1",
      (GERBER, "1 if first <= column <= last else 0))\n", "0 if first <= column <= last else 1))\n")),
    m("M/taxels-not-written", "mask P3", "a masked build's review bundle has no taxels.csv",
      (GERBER, '    return {} if build["taxel_mask"] is None else {_TAXELS: _taxels(build).encode("ascii")}\n', "    return {}\n")),
    m("M/taxels-unread", "mask P3", "taxels.csv is not read back against the boards",
      (GERBER, "        _check_taxel_map(files.get(_TAXELS), build)\n", "        pass\n")),
    m("M/taxel-note-unchecked", "mask P3", "ORDER_NOTES.txt need not state a masked build's taxel field",
      (GERBER, "    phrases += _taxel_field_phrases(build)\n", "    pass\n")),
    m("M/taxel-note-positions", "mask P3", "ORDER_NOTES.txt states the R x C positions as the taxel count",
      (GERBER, "_taxel_field(registration['active_taxel_count'], mask['rows'], mask['columns'])",
       "_taxel_field(mask['rows'] * mask['columns'], mask['rows'], mask['columns'])")),
    # Phase P4, CAD mode's masked fields (surface/fill.py, the fit option shape: fill), the masked map, the readers
    # (surface/reader.py) and the web client's mask.
    m("M/fill-taxels-positions", "mask P4", "a masked proposal counts its R x C positions as its taxels",
      (FILL, '            "taxels": active,\n            "pitch_x_mm": pitch,\n', '            "taxels": rows * columns,\n            "pitch_x_mm": pitch,\n')),
    m("M/fill-field-bounding-box", "mask P4", "a masked proposal's field outline is the bounding rectangle, not P",
      (FIT, "        outlines[\"field\"] = field_polygon(result, field_origin)\n", "        pass\n")),
    m("M/fill-no-peel", "mask P4", "a masked candidate whose real outline leaves the surface is dropped instead of peeled",
      (FILL, '    if point is not None and candidate.get("peels", 0) < PEEL_RETRIES:\n', "    if False:\n")),
    m("M/fill-mask-mirrored", "mask P4", "the masked candidate's row spans are written in slot order, not as COL indices (COL_c is slot C - c)",
      (FILL, "    mask = None if full else tuple((columns - high, columns - low) for low, high in spans)\n    active = 0\n",
       "    mask = None if full else tuple((low + 1, high + 1) for low, high in spans)\n    active = 0\n")),
    m("M/fill-no-edge-inset", "mask P4", "the exact free space lets a staircase corner touch the surface's edge (the realize decides it by float noise)",
      (FILL, "        self.margin = float(margin) + fit.EDGE_INSET_MM\n", "        self.margin = float(margin)\n")),
    m("M/fill-band-half-pitch", "mask P4", "a row's band ends half a pitch above it (the probe's band: a step's dilated corner is not checked)",
      (FILL, "    up = max(pitch / 2, half + margin)\n", "    up = pitch / 2\n")),
    m("M/fill-no-taper", "mask P4", "every masked row starts at the Row channel (no lane taper)",
      (FILL, "        taus = [[max(0, math.ceil(round6(width - point) / step - _NOISE)) for width in widths] for point in points]\n",
       "        taus = [[0 for width in widths] for point in points]\n")),
    m("M/fill-not-merged", "mask P4", "the fill fit proposes masks only (a rectangle with more taxels is lost: worse than shape rectangle)",
      (FILL, "    pool = [(_rectangle_rank(c), c) for c in rectangles] + [(c[\"rank\"], c) for c in masked]\n",
       "    pool = [(c[\"rank\"], c) for c in masked]\n")),
    m("M/fill-far-ends-unclipped", "mask P4", "the masked rows keep their own far ends (far ends that recede going down are out of the straight class)",
      (FILL, "        current = min(current, ends[j])\n", "        current = ends[j]\n")),
    # M/fill-shaped-64 (masked fields up to 64 rows against the 32 x 32 cap) retired with P5-diagonal-bus.md section 21:
    # shaped fields take the rectangles' caps (M/sec21-walk-cap-32 puts the old cap back).
    m("M/map-masked-all-crossings", "mask P4", "the map of a masked design lists every R x C position as a taxel",
      (PLACE, "            if min(rx1, cx1) - max(rx0, cx0) > 1e-9 and min(ry1, cy1) - max(ry0, cy0) > 1e-9:\n", "            if True:\n")),
    m("M/map-masked-mirror", "mask P4", "the map of a masked design places its taxels mirrored across the field",
      (PLACE, "            xs = [x + shift_x for x, _ in corners]\n", "            xs = [shift_x - x for x, _ in corners]\n")),
    m("M/map-mask-record-blind", "mask P4", "taxel_mask_matches_design compares the design's mask with itself",
      (PLACE, '    found = {(item["row"], item["column"]) for item in taxels}\n', "    found = expected\n")),
    m("M/map-taxels-positions", "mask P4", "the map of a masked design wants R x C taxels on the surface",
      (PLACE, "    if mask is not None:\n        count = 0\n", "    if False:\n        count = 0\n")),
    m("M/reader-frame-16", "mask P4", "every reader's frame index takes 16 sense lines per drive line (the FlexiTac's)",
      (READER, '        "frame_index": (drive_index - 1) * sense + (sense_index - 1),\n', '        "frame_index": (drive_index - 1) * 16 + (sense_index - 1),\n')),
    m("M/reader-auto-largest", "mask P4", "reader auto takes the largest reader instead of the smallest that holds the readout",
      (READER, "        return next((name for name in READERS if holds(rows, columns, name)), None)\n",
       "        return next((name for name in reversed(list(READERS)) if holds(rows, columns, name)), None)\n")),
    m("M/reader-sides-swapped", "mask P4", "the Row lines take the drive connector when they fit the sense one",
      (READER, '        return {"row_pins": sense, "column_pins": drive}\n', '        return {"row_pins": drive, "column_pins": sense}\n')),
    m("M/reader-legacy-connector", "mask P4", "the legacy option connector: flexitac no longer sizes the tails for the FlexiTac",
      (READER, "        options[\"reader\"] = LEGACY_CONNECTOR[legacy]\n", "        options[\"reader\"] = \"none\"\n")),
    # M/fill-generic-allowed (shape fill accepted on the generic template) retired with section 26.16: CAD mode has no
    # generic template (M/sec26-cad-only-accepted refuses it again if it came back).
    m("M/web-payload-drops-mask", "mask P4", "Generate posts the form without the proposal's mask (the build is not the proposal's)",
      (WEB, "    if (state.mask && state.design?.template_id === MASK_TEMPLATE) body.matrix = {mask: state.mask};\n",
       "    if (false) body.matrix = {mask: state.mask};\n")),
    m("M/web-rows-edit-keeps-mask", "mask P4", "a rows or columns edit keeps the mask (it no longer has a span per row)",
      (WEB, '    if (target && ["rows", "columns"].includes(target.id)) clearMask(`${target.id} changed`);\n', "")),
    # The fixes of the P4 reviews: the reader caps the walk, the search does not depend on the placement or the
    # role option, no dominated proposal, the metrics name the map's reader, and the web client's mask and shape.
    m("M/fill-reader-uncapped", "mask P4 review", "a named reader does not cap the masked walk (16x16 then finds fewer taxels than max_rows/max_columns 16)",
      (READER, "    if option not in READERS:\n        return [(rows_cap, columns_cap)]\n", "    if True:\n        return [(rows_cap, columns_cap)]\n")),
    m("M/reader-metrics-choose", "mask P4 review", "metrics.reader is the option's choice, so a 16 x 32 readout without a reader reads null where the map names the FlexiTac",
      (READER, "    return of_design(option, row_pins, column_pins)\n", "    return choose(rows, columns, option)\n")),
    m("M/fill-seeds-placed-by-option", "mask P4 review", "the masked search takes the rectangles' phases at the placement option only (the count then depends on it)",
      (FILL, "    for placement in SEED_PLACEMENTS:\n", "    for placement in (options[\"placement\"],):\n")),
    m("M/fill-seeds-any-role", "mask P4 review", "each role's lattices take the phases of the best rectangles of either role (auto then finds less than one role alone)",
      (FILL, '        found = [c for c in rectangles if c["side"]["index"] == side["index"] and c["angle_deg"] == angle and c["role"] == role]\n',
       '        found = [c for c in rectangles if c["side"]["index"] == side["index"] and c["angle_deg"] == angle]\n')),
    m("M/fill-threshold-across-roles", "mask P4 review", "a role's search prunes on the other role's masks too",
      (FILL, "        items = self.items.get(role, {})\n", "        items = {(r, key): item for r in sorted(self.items) for key, item in self.items[r].items()}\n")),
    m("M/fill-fine-frames-across-roles", "mask P4 review", "the fine phases run on the best frames of either role, for each role",
      (FILL, "        best_frames = sorted((item for item in frame_best.values() if item[3] == role), key=lambda item: search_rank(item[0]))[:FINE_FRAMES]\n",
       "        best_frames = sorted(frame_best.values(), key=lambda item: search_rank(item[0]))[:FINE_FRAMES]\n")),
    m("M/fill-dominated-kept", "mask P4 review", "the fill fit proposes a field an earlier proposal dominates (as many taxels on no more Row and Column lines)",
      (FILL, '        if metrics["taxels"] >= taxels and metrics["rows"] <= rows and metrics["columns"] <= columns:\n', "        if False:\n")),
    m("M/web-template-clears-mask", "mask P4 review", "a switch to the Rectangular mode drops the mask (back in CAD mode the form no longer builds the proposal)",
      (WEB, "    const kept = controls.map(control => [control, control.value]);\n",
       "    if (id !== MASK_TEMPLATE) clearMask(`the template changed to ${id}`);\n    const kept = controls.map(control => [control, control.value]);\n")),
    m("M/web-mask-issues-unshown", "mask P4 review", "the server's issues at matrix.mask are shown nowhere (no control carries them)",
      (WEB, "    state.maskIssues = maskIssuesOf(validation);\n", "    state.maskIssues = [];\n")),
    m("M/web-full-field-inert", "mask P4 review", "the mask note's 'Use the full field' does nothing",
      (WEB, '  $("clearMask").addEventListener("click", () => { clearMask("you chose the full field"); onFormEdit(null); });\n', "")),
    # M/web-shape-on-generic (Field shape enabled on the Rectangular board rules) retired with section 26.16: neither
    # control exists.
)


# --------------------------------------------------------------------------
# The diagonal Row bus (claude/specs/masked-field/P5-diagonal-bus.md): phase P5a, the primitives.
# --------------------------------------------------------------------------

BUS = "engine/bus.py"

DIAGONAL = (
    m("M/bus-pop-collinear", "mask P5a", "the west chain keeps collinear points (pops on cross < 0 only)",
      (BUS, "        while len(chain) >= 2 and cross(chain[-2], chain[-1], point) <= 0:\n",
       "        while len(chain) >= 2 and cross(chain[-2], chain[-1], point) < 0:\n")),
    m("M/bus-slant-no-allowance", "mask P5a", "slanted segments are offset by the distance alone, without the 2 nm allowance",
      (BUS, "ux, uy, uy, -ux, distance_nm + (SLANT_ALLOWANCE_NM if slanted else 0))\n", "ux, uy, uy, -ux, distance_nm)\n")),
    m("M/bus-keepout-no-continuation", "mask P5a", "a lane's keep-out leaves out its continuation (the next lane cuts the bend; D2 measured route-route 0.0476 on the disk)",
      (BUS, "    return lane_offset([*chain, follow], distance_nm) + box_corners(", "    return lane_offset(list(chain), distance_nm) + box_corners(")),
    m("M/bus-keepout-no-start-box", "mask P5a", "a lane's keep-out leaves out the box around its start (a lane from a narrower row above cuts the electrode end)",
      (BUS, "    return lane_offset([*chain, follow], distance_nm) + box_corners(grow((chain[0][0], chain[0][1], chain[0][0], chain[0][1]), distance_nm))\n",
       "    return lane_offset([*chain, follow], distance_nm)\n")),
    m("M/bus-round-nearest", "mask P5a", "offset vertices are rounded to the nearest grid value instead of away from the chain",
      (BUS, "    if direction == 0 or abs(value - nearest) < _GRID_NOISE_NM:\n", "    if True:\n")),
    m("M/bus-sharp-bevel", "mask P5a", "a convex turn beyond 120 degrees takes a bevel (it cuts within about half the distance of the vertex)",
      (BUS, "        first = (one.nx + one.ux, one.ny + one.uy)\n        second = (two.nx - two.ux, two.ny - two.uy)\n",
       "        first = (one.nx, one.ny)\n        second = (two.nx, two.ny)\n")),
)

DIAGONAL_ENGINE = "engine/diagonal.py"

DIAGONAL += (
    # Phase P5b, re-expressed for diagonal-bus/2 (section 12 of the plan): the bands, the contract, the DRC gate and the
    # tail rules of the registration.
    m("M/diag-own-zone-corner", "mask P5b", "a lane may leave its own zone short of its outer-bottom corner (the plan measured strict record 14 at 0.1389 at 1.25 / 0.8 mm)",
      (DIAGONAL_ENGINE, "        points.append(corner)\n", "")),
    m("M/diag-corner-start", "mask P5b", "a lane starts at its electrode end's top corner wherever nothing straddles the centre line from above",
      (DIAGONAL_ENGINE, "    if below and not above:\n        return (x, top)\n", "    if not above:\n        return (x, top)\n")),
    m("M/diag-no-hold", "mask P5b", "the Row tail's sides do not hold straight above the tail root (the plan measured route-to-outline 0.066)",
      (DIAGONAL_ENGINE, "    return round6(rules.copper_to_edge + rules.finger_width / 2 + rules.offset_allowance)\n", "    return 0.0\n")),
    m("M/diag-gate-off", "mask P5b", "the DRC no longer treats a diagonal-bus board as masked (without its mask records strict record 14 goes vacuous)",
      (DRC, '    masked = "taxel_mask" in board["grid_registration"] or _row_bus_kind(board) == ROW_BUS_VERSION\n',
       '    masked = "taxel_mask" in board["grid_registration"]\n')),
    m("M/diag-identity-extra", "mask P5b", "a design with routing.row_sides keeps the straight channel's identity (no row_bus extra)",
      (CORE, '        identity["row_bus"] = ROW_BUS_VERSION\n', "        pass\n")),
    m("M/diag-fold-order", "mask P5b", "the contacts keep ROW_01..ROW_R in order instead of the folded order of the lanes",
      (DIAGONAL_ENGINE, '    contact_order = [f"ROW_{k:02d}" for k in (reversed(order) if flip else order)]\n',
       '    contact_order = [f"ROW_{k:02d}" for k in range(1, geo.R + 1)]\n')),
    # M/diag-generic-accepted (routing.row_sides accepted on generic designs) retired with P5-diagonal-bus.md section 18,
    # which accepts it there: M/rect-generic-refused is its inverse.
    m("M/diag-own-zone-trace-space", "mask P5b", "inside its own zone a lane may come within the trace space of another row's electrode",
      (DIAGONAL_ENGINE, " + geo.electrode_points(k, deep, start[1])\n", "\n")),
    # M/diag-mirror-contacts (the mirrored build taking the tail's near end) re-expressed by M/sec27-mirror-dropped on
    # diagonal-bus/10's line (P5-diagonal-bus.md section 27).
    m("M/diag-no-flip", "mask P5b", "a one-sided bus is always built on ROW_01's side with both",
      (DIAGONAL_ENGINE, '    geo = _Geo(design, rules, flip=sides != "both" and sides != near)\n', "    geo = _Geo(design, rules, flip=False)\n")),
    m("M/diag-split-halves", "mask P5b", "both sides split the rows in halves instead of alternately",
      (DIAGONAL_ENGINE, "        near_rows = [k for k in range(1, geo.R + 1) if k % 2 == 1]\n        far_rows = [k for k in range(1, geo.R + 1) if k % 2 == 0]\n",
       "        near_rows = [k for k in range(1, geo.R + 1) if k <= (geo.R + 1) // 2]\n        far_rows = [k for k in range(1, geo.R + 1) if k > (geo.R + 1) // 2]\n")),
    m("M/diag-window-warning", "mask P5b", "no W_STACK_TRACE_WINDOW for a stacked trace closer to the other board's window than the opening-to-trace rule",
      (DRC, "        elif gap is not None and gap < rules.opening_to_trace - epsilon:\n", "        elif False:\n")),
    m("M/diag-trace-over-electrode", "mask P5b", "a stacked trace over the other board's electrode is not counted",
      (DRC, "        if segment_box_distance(c, d, box) - radius <= epsilon:\n", "        if False:\n")),
    m("M/diag-infeasible-uncaught", "mask P5b", "an infeasible bus raises out of generate_design instead of E_ROW_BUS_INFEASIBLE",
      (CORE, "    except RowBusInfeasible as infeasible:\n", "    except KeyError as infeasible:\n")),
    # Phase P5c, the exports: the taxel map and the order note of an unmasked bus, the review manifest's record of the
    # bus and its read-back against pinout.csv.
    m("M/export-bus-no-taxel-map", "mask P5c", "an unmasked diagonal Row bus gets no taxel map (its boards carry the full field's mask, so its export fails)",
      (GERBER, "    if mask is None and row_bus(design):\n", "    if False:\n")),
    m("M/export-full-field-noted", "mask P5c", "the order notes state an unmasked bus's full field as a masked taxel field, writer and read-back alike",
      (GERBER, '    if registration["active_taxel_count"] == mask["rows"] * mask["columns"]:\n        return []\n', ""),
      (GERBER, "    if active == len(mask) * columns:\n        return []\n", "")),
    m("M/export-bus-unrecorded", "mask P5c", "the review manifest leaves out the bus's record (construction.row_bus, the contact order and its pins)",
      (GERBER, "        **_row_bus_entry(build),\n", "")),
    m("M/export-row-contacts-unread", "mask P5c", "pinout.csv is not read back against the folded Row contact order",
      (GERBER, '        _check_row_contacts(files["pinout.csv"], build)\n', "        pass\n")),
    m("M/export-row-pins-by-position", "mask P5c", "the record numbers the Row contacts' pins by position (ascending pins), whatever channel_order says",
      (GERBER, '            "row_contact_pins": [pad["pin"] for pad in contacts[: len(order)]],\n',
       '            "row_contact_pins": list(range(1, len(order) + 1)),\n')),
    # The P5 reviews' fixes: the record's flat lanes and relative narrow tip, and opposite tails only (their mutant of
    # the stack trace gap kept from the raised Column stubs is retired with that keep-out, the plan's section 14.2).
    m("M/diag-flat-rows-unlisted", "mask P5 review", "construction.row_bus.flat_lane_rows never lists a row (the disk's enclosed rows escape flat)",
      (DIAGONAL_ENGINE, "            if any(math.atan2(abs(step[0]), abs(step[1])) > geo.cap + 1e-12 for step in steps):\n",
       "            if False:\n")),
    m("M/diag-tip-excess-clause", "mask P5 review", "the relative narrow tip is the plan's least-excess clause (false on the disk built on ROW_01's side)",
      (DIAGONAL_ENGINE, "    relative = all(\n        width >= widths[0] - 1e-6 for width, field in zip(widths, field_widths) if field >= field_widths[0] - 1e-6\n    )\n",
       "    relative = min(excesses) >= excesses[0] - 1e-6\n")),
    m("M/diag-tip-absolute", "mask P5 review", "the relative narrow tip ignores the field (every row's board against the tip's)",
      (DIAGONAL_ENGINE, " for width, field in zip(widths, field_widths) if field >= field_widths[0] - 1e-6\n", " for width in widths\n")),
    m("M/diag-tails-any-unequal", "mask P5 review", "E_ROW_BUS_TAILS for any unequal tail sides (a quarter turn gets it beside E_TAIL_SIDE_PARALLEL)",
      (CORE, '        elif row_sides != CHANNEL and len(sides) == 2 and _opposite_tails(sides["row_side"], sides["column_side"]):\n',
       '        elif row_sides != CHANNEL and len(sides) == 2 and sides["row_side"] != sides["column_side"]:\n')),
    # The tail redesign (diagonal-bus/2, the plan's section 12): every lane straight down below the field, the staggered
    # fans and their guards, the funnel under the body, the one-sided tail under the band, and the registration's field
    # window (its fallback beside the Column tail, the Column tail's side and neck and the 1.0 mm tail rules retired
    # with diagonal-bus/3's stacked tails).
    m("M/diag-cut-off", "mask P5f review", "the lanes keep diagonal-bus/1's corners up to 0.3 mm below the field (three bends below it)",
      (DIAGONAL_ENGINE, "    if not raised:\n        chains = _cut_at_field(", "    if False:\n        chains = _cut_at_field(")),
    m("M/diag-cut-into-keepout", "mask P5f review", "a lane turns down on the field's edge where its ray cuts the stacked Column windows' keep-out (thin rows)",
      (DIAGONAL_ENGINE, "                        if bus.segment_enters((x, 0), (x, low), box):\n                            x, moved = box[0], True\n",
       "                        if False:\n                            x, moved = box[0], True\n")),
    m("M/diag-raised-always", "mask P5f review", "the bottom row's corner is raised onto the field's edge before the onion (the bands move up to 0.48 mm, the tip changes)",
      (DIAGONAL_ENGINE, "        built = _build(design, profile, geo, near_rows, far_rows, raised=False)\n",
       "        built = _build(design, profile, geo, near_rows, far_rows, raised=True)\n")),
    m("M/diag-fan-pitch", "mask P5f", "the fans run a grid step closer than the bundle pitch (no allowance for their bends' rounding)",
      (DIAGONAL_ENGINE, "    step = geo.bp + _FAN_ALLOWANCE_MM\n", "    step = geo.bp - _GRID_STEP_MM\n")),
    m("M/diag-fan-unstaggered", "mask P5f", "every lane of a run turns into its fan at the window level (no stagger behind the front)",
      (DIAGONAL_ENGINE, "            s = max(s, previous + step)\n", "            s = s\n")),
    m("M/diag-fan-cap-entry-angle", "mask P5f", "the fans may run at the Column fan-out's entry angle (Row traces along Column traces)",
      (DIAGONAL_ENGINE, "    caps = [cap for cap in geo.caps if abs(math.degrees(cap) - entry) > ENTRY_ANGLE_GUARD_DEG + _NOISE_MM]\n",
       "    caps = list(geo.caps)\n")),
    m("M/diag-fan-clash-ignored", "mask P5f", "lanes closer than the bundle pitch below the field build anyway",
      (DIAGONAL_ENGINE, "    if clash is not None:\n        raise RowBusInfeasible(", "    if False:\n        raise RowBusInfeasible(")),
    m("M/diag-landing-off-by-one", "mask P5f", "the last lane of the contact order lands one contact pitch beyond its contact",
      (DIAGONAL_ENGINE, "    contact = {k: round6(tail_x + rules.side_offset + (first + index) * rules.pitch) for index, k in enumerate(order)}\n",
       "    contact = {k: round6(tail_x + rules.side_offset + (first + index + (index == len(order) - 1)) * rules.pitch) for index, k in enumerate(order)}\n")),
    # M/diag-off-centre-split (the funnel's split under the near band's innermost lane), M/diag-tail-not-flush (one side's
    # outer contact a pitch outside the outermost lane) and M/diag-reader-far-contacts (a mirrored reader tail's rows at its
    # far end from the band, the tail under the band) retired with diagonal-bus/10 (P5-diagonal-bus.md section 27): the
    # split midway between the innermost lanes and the tail under the band are gone (M/sec27-split-midway and
    # M/sec27-under-band put them back), and a mirrored reader tail's rows lie at its far end by the rule.
    m("M/diag-tail-side-slant", "mask P5f review", "a tail side beyond the envelope slants out to it however flat (a reader tail wider than the field and its bands, "
      "centred under it: a long diagonal edge out to its side)",
      (DIAGONAL_ENGINE, "        if len(chain) > 1 and abs(seed - chain[-2][0]) <= chain[-2][1] - chain[-1][1]:\n", "        if len(chain) > 1:\n")),
    m("M/diag-tail-slant-above-field", "mask P5f review", "a tail side's slant out to the tail starts above F's bottom (it moves the band beside the bottom rows)",
      (DIAGONAL_ENGINE, "        upper, lower = _split_at(chain, y_field)\n        if lower:\n            chain = upper + lower[1:]\n", "")),
    m("M/diag-window-uncounted", "mask P5f", "a stacked trace over the other board's field window (between its electrodes) is not counted",
      (DRC, "        if gap <= epsilon:\n            over_windows += 1\n", "")),
    m("M/diag-window-merged-only", "mask P5f", "the field window is the merged opening only: one opening per electrode is no window",
      (DRC, '        if opening["kind"] in ("electrode_field_opening", "sensor_electrode_opening")\n    ]\n',
       '        if opening["kind"] == "electrode_field_opening"\n    ]\n')),
    m("M/diag-electrode-gate", "mask P5f review", "a stacked trace over the other board's electrode fails the registration only when it also lies over a window",
      (DRC, "        if windows or electrodes:\n", "        if windows:\n")),
    m("M/diag-electrode-per-pair", "mask P5f review", "a trace part over three electrodes counts three times (the electrode count per pair, the window count per part)",
      (DRC, "            over.add(part_index)\n", "            over.add((part_index, electrode_index))\n")),
    # The stacked tails (diagonal-bus/3, the plan's section 13): the Column board is the straight one, the funnel's Row
    # tail centred under the body, and the registration keeps the field and one exit side, not a tail gap.
    m("M/diag-column-necked", "mask P5g", "the Column board's tail root lies 1.0 mm lower than the straight board's (diagonal-bus/2's neck)",
      (DIAGONAL_ENGINE, "    plan = dict(column_plan(design, column_profile(profile) if capped else profile))\n",
       "    plan = dict(column_plan(design, column_profile(profile) if capped else profile))\n"
       "    plan[\"tail_top\"], plan[\"tip\"] = round6(plan[\"tail_top\"] - 1.0), round6(plan[\"tip\"] - 1.0)\n")),
    m("M/diag-column-straight-classes", "mask P5g", "the Column board records the straight classes (its pair builds the diagonal Row bus)",
      (DIAGONAL_ENGINE, "    plan[\"mask_class\"] = CLASSES\n", "    plan[\"mask_class\"] = {\"row\": \"straight\", \"column\": \"straight\"}\n")),
    # M/diag-tail-off-centre-pitch (with both the Row tail a contact pitch off the funnel's split) retired with
    # diagonal-bus/10's centred tail (P5-diagonal-bus.md section 27): M/sec27-off-by-pitch, in every side mode.
    m("M/diag-registration-unchecked", "mask P5g", "the registration no longer fails a stacked trace over the other board's electrodes or field window",
      (DRC, "        if windows or electrodes:\n", "        if False:\n")),
    m("M/diag-tail-sides-unchecked", "mask P5g", "the registration accepts tails that leave on different sides",
      (DRC, "    if sides[0] != sides[1]:\n", "    if False:\n")),
    m("M/diag-tail-overlap-unreported", "mask P5g", "the registration reports no overlap of the stacked tails",
      (DRC, "    keys[\"tail_overlap_width_mm\"] = round6(width) if meet else 0.0\n", "    keys[\"tail_overlap_width_mm\"] = 0.0\n")),
    # One outline over the field (diagonal-bus/4, the plan's section 14): both boards take the union of their outlines
    # down to F's bottom, each its own below, and the registration checks that the two coincide there.
    m("M/diag-shared-none", "mask P5h", "each board keeps its own outline down to the tail roots (no shared outline; the Row board still records the level)",
      (DIAGONAL_ENGINE, "    ring, smallest = _share_outline(geo, owns, column, plan, level)\n",
       "    ring, smallest = fillet_concave_corners(owns[0], rules.fillet_radius, arc_step_rad=rules.arc_step)\n")),
    # M/diag-shared-level-field-edge and M/diag-shared-level-window (the shared outline cut at the field's bottom edge
    # or at its window level, above F's bottom) retired with P5-diagonal-bus.md section 20, whose level is the tails'
    # roots: M/sec20-shared-at-field cuts it at F's bottom, diagonal-bus/7's level.
    m("M/diag-shared-row-only", "mask P5h", "the shared outline is the Row board's alone (the Column body beyond it, the disk's lower corners, is cut off)",
      (DIAGONAL_ENGINE, "    shared, used = _union_above([own, upper], level, rules, corners, depth, flank=flank)\n",
       "    shared, used = _union_above([own], level, rules, corners, depth, flank=flank)\n")),
    m("M/diag-shared-joins-sharp", "mask P5h", "a board's steps in below the shared outline keep their concave corners sharp (no R0.5 fillet)",
      (DIAGONAL_ENGINE, "    fixed = list(shared) + [point for point in ring if tuple(point) not in joined]\n", "    fixed = list(path)\n")),
    m("M/diag-shared-no-ear", "mask P5h", "under the other board's fillet into a tail wider than the field a board steps in along the level (a cusp), not a fillet radius lower",
      (DIAGONAL_ENGINE, "            if dx > dy:\n", "            if False:\n")),
    m("M/diag-shared-unchecked", "mask P5h", "the registration does not check that the two outlines coincide over the field",
      (DRC, "    keys[\"outlines_coincide_over_field\"] = deviation is not None and deviation <= epsilon\n", "    keys[\"outlines_coincide_over_field\"] = True\n"),
      (DRC, "    elif deviation > epsilon:\n", "    elif False:\n")),
    m("M/diag-shared-unrecorded-passes", "mask P5h", "a Row board without the shared level registers clean (the outline check skipped)",
      (DRC, "    if deviation is None:\n        errors.append((", "    if False:\n        errors.append((")),
    # The Row lanes beside the field (diagonal-bus/4 with the user's later decisions, the plan's section 14.2): the
    # stacked Column copper is no keep-out, and on a receding field each lane follows the field inward.
    m("M/diag-copper-in-k", "mask P5h", "the stacked Column copper is back in the bands' keep-out (0.15 mm from the Column stubs: the disk's enclosed rows leave flat across them, its bands 22 mm wide)",
      (DIAGONAL_ENGINE, "    boxes = windows  # the stacked Column copper is no keep-out: the boards may overlap outside the field\n",
       "    boxes = list(windows)\n"
       "    for route in column[\"layers\"][\"top_copper\"][\"routes\"]:\n"
       "        points = [[round6(p[0] - plan[\"active\"][0]) if geo.flip else round6(geo.aw - round6(p[0] - plan[\"active\"][0])), round6(p[1] - plan[\"active\"][1])] for p in route[\"points\"]]\n"
       "        for a, b in zip(points, points[1:]):\n"
       "            grow = float(route[\"width_mm\"]) / 2 + ceil6(max(geo.ts, 0.15) + geo.tw / 2 + _GRID_STEP_MM)\n"
       "            if max(a[1], b[1]) > y_hug:\n"
       "                boxes.append(bus.nm_box(min(a[0], b[0]) - grow, max(min(a[1], b[1]), y_hug), max(a[0], b[0]) + grow, max(a[1], b[1])))\n")),
    m("M/diag-hug-off", "mask P5h", "on a receding field every lane runs straight down from its westmost point (diagonal-bus/1's skirt: the disk's bands 11 mm farther out, its Row root 4.5 mm deeper)",
      (DIAGONAL_ENGINE, "        if hug is not None and hug - reach > _HUG_MIN_NM and start[1] > low:\n", "        if False:\n")),
    m("M/diag-hug-no-inner-crossings", "mask P5h", "a lane following the field inward ignores where the inner lanes' offsets cross the field's bottom edge (it comes closer than the bundle pitch)",
      (DIAGONAL_ENGINE, "        edge = [point[0] for point in points if point[1] <= low] + _crossings(offsets, low)\n",
       "        edge = [point[0] for point in points if point[1] <= low]\n")),
    m("M/diag-hug-no-cap", "mask P5h", "a lane following the field inward may lean flatter than the taper cap toward the field's bottom edge",
      (DIAGONAL_ENGINE, "            hug = min([hug] + [x + y * run // _RUN_SCALE for x, y in [*points, start] if low < y <= start[1]])\n", "            pass\n")),
    m("M/bus-hug-turn-mitred", "mask P5h", "a lane's inward turn takes the mitre (the lanes nested around it spread outward by 1 / cos(turn / 2) each)",
      (BUS, "        if before[0] > corner[0] < after[0]:\n", "        if False:\n")),
    # Regular outlines (diagonal-bus/5, the plan's section 15): no corner flatter than 5 degrees but on a fillet or the
    # tail; a flatter run becomes one straight edge outside it.
    m("M/diag-regular-off", "mask P5k", "the outlines are not made regular (diagonal-bus/4's runs of flat vertices: the crank's slanted side, 247 of 325)",
      (DIAGONAL_ENGINE, "    points = [[float(point[0]), float(point[1])] for point in ring]\n",
       "    return [[float(point[0]), float(point[1])] for point in ring]\n")),
    m("M/diag-regular-threshold-ignored", "mask P5k", "only vertices that do not turn at all merge (the grid's noise): the soft finger's 3.6-degree corners stay",
      (DIAGONAL_ENGINE, "            if alive[index] and not fixed[index] and not stuck[index] and turns[index] < _REGULAR_TURN:\n",
       "            if alive[index] and not fixed[index] and not stuck[index] and turns[index] < 1e-6:\n")),
    m("M/diag-regular-chord", "mask P5k", "a merged run's straight edge is its chord, not moved outward (it cuts inside a convex run: 0.33 mm on the soft finger)",
      (DIAGONAL_ENGINE, "    # The lower hull in (along the chord, across it: negative outward), the points in order along the chord.\n",
       "    return head, chord\n")),
    # M/diag-regular-fillets-unanchored (the boards' fillets not kept while the union is made regular) retired with
    # P5-diagonal-bus.md section 20: the union is of the boards' outlines before their fillets, filleted once.
    m("M/diag-regular-corners-sharp", "mask P5k", "the union's corners that are a board's own are left sharp (not filleted: sharp concave corners)",
      (DIAGONAL_ENGINE, "    ring, smallest = _filleted(ring, rules)\n",
       "    ring, smallest = fillet_concave_corners(ring, rules.fillet_radius, arc_step_rad=rules.arc_step, fixed=[point for own in rings for point in own],\n"
       "                                            min_turn_rad=_SHARED_MIN_TURN / rules.fillet_radius)\n")),
    m("M/diag-regular-tail", "mask P5k", "the tails are made regular too (a side running on straight into the tail tilts the tail's side)",
      (DIAGONAL_ENGINE, "    return _regular(points, {tuple(point) for point in points if point[1] <= root + _NOISE_MM})\n",
       "    return _regular(points, ())\n")),
    # Chamfered notches (diagonal-bus/6, the plan's section 16).
    m("M/diag-chamfer-inside-f", "mask P5 sec16", "a notch's chamfer is the hull of P, not of F (it cuts inside F's corners)",
      (DIAGONAL_ENGINE, "    points = sorted({(x, y) for low, high, start, end in slabs for x in (start, end) for y in (low, high)})\n",
       "    points = sorted({(x, y) for low, high, start, end in slabs for x in (start + 0.5, end - 0.5) for y in (low + 0.5, high - 0.5)})\n")),
    m("M/diag-chamfer-off", "mask P5 sec16", "a masked field keeps F's staircase at its notches (diagonal-bus/5's outline)",
      (DIAGONAL_ENGINE, "    if any(row[\"lo\"] != 0 or row[\"hi\"] != geo.C - 1 for row in geo.rows):\n        # A masked field",
       "    if False:\n        # A masked field")),
    # Straight sides at the tip (diagonal-bus/7, the plan's section 17).
    m("M/diag-straight-off", "mask P5 sec17", "the sides keep their polyline below the tip corner (diagonal-bus/6's outline: the r4 plate's stub, fillet and jog)",
      (DIAGONAL_ENGINE, "    ring = _round_ring(_straight_sides(ring, level, run, rings, _round_ring(_filleted(ring, rules)[0])))\n", "")),
    m("M/diag-straight-bound-ignored", "mask P5 sec17", "a side becomes one line however far it lies from the old one or the tip corner moves (the disk's curved sides)",
      (DIAGONAL_ENGINE, "    return all(_cross(direction, _minus(point, pivot)) ** 2 <= bound for point in points)\n", "    return True\n"),
      (DIAGONAL_ENGINE, "    if length > SIDE_STRAIGHTEN_MM * SIDE_STRAIGHTEN_MM or (_dot(move, edge) < 0.0", "    if (_dot(move, edge) < 0.0")),
    m("M/diag-straight-not-enclosing", "mask P5 sec17", "the upper line is the chord from the tip corner to the widest point (it cuts inside the jog below the corner)",
      (DIAGONAL_ENGINE, "    pivot, direction = _fit(points, 0, widest, False, True)\n",
       "    pivot, direction = points[widest], _minus(points[widest], points[0])\n")),
    # The rectangular generator (P5-diagonal-bus.md section 18, 2026-10-24): the diagonal Row bus the generic template's
    # default, routing.row_sides "channel" for the straight Row channel on both templates, the 85-degree funnel fans
    # on the standard profile, and the browser's Row traces select in both modes.
    m("M/rect-default-channel", "mask P5 sec18", "the generic default stays the straight Row channel (the default flip off)",
      (CORE, '    return "both"\n\n\ndef _opposite_tails(', '    return CHANNEL\n\n\ndef _opposite_tails(')),
    m("M/rect-generic-refused", "mask P5 sec18", "the generic template refuses routing.row_sides again (E_UNKNOWN_FIELD for both, left, right and channel)",
      (CORE, '"routing.row_sides": frozenset({GENERIC_TEMPLATE_ID, SURFACE_TEMPLATE_ID})}', '"routing.row_sides": MASK_TEMPLATES}')),
    # M/rect-fans-60 (the generic bus's fans at the standard profile's single 60-degree cap) retired with
    # P5-diagonal-bus.md section 20: the generic bus has CAD mode's rule set (M/sec20-* below).
    m("M/rect-channel-ignored", "mask P5 sec18", "routing.row_sides channel is taken for a side of the bus (the straight channel is never built)",
      (DIAGONAL_ENGINE, "    return sides if isinstance(sides, str) and sides in ROW_SIDES else None\n",
       "    return sides if isinstance(sides, str) else None\n")),
    m("M/rect-surface-channel-kept", "mask P5 sec18", "the surface template keeps routing.row_sides channel in its design (a new build id for its straight channel)",
      (CORE, "    if raw == CHANNEL and not defaulted:\n", "    if False:\n")),
    # M/rect-fans-above-f and M/rect-no-careful-pass (the standard profile's own fan start and careful pass) retired
    # with section 20: neither rule exists without the standard profile's bus.
    m("M/rect-web-row-sides-surface-only", "mask P5 sec18", "the form sends the Row traces on the surface template only (Rectangular mode builds its default)",
      (WEB, '    return value("rowSides") || null;\n', '    return state.design?.template_id === MASK_TEMPLATE ? value("rowSides") || null : null;\n')),
    m("M/rect-web-row-sides-hidden", "mask P5 sec18", "the Row traces select stays hidden in Rectangular mode",
      (WEB, '    $("rowSidesRow").hidden = false;\n', '    $("rowSidesRow").hidden = state.design?.template_id !== MASK_TEMPLATE;\n')),
    # One Column V in the rectangular generator (diagonal-bus/8, P5-diagonal-bus.md section 19, 2026-10-24), folded into
    # section 20: the generic bus's Column board has CAD mode's one V.  M/colv-two-lanes, M/colv-lane-capacity-16 (the
    # override's two lanes and lane capacity) and M/colv-surface-version (a version per template) retired with it.
    m("M/colv-leak-channel", "mask P5 sec19", "the bus's rule set reaches the generic straight channel too (its Column board in one V: every generic channel build changes)",
      (CORE, "    return SURFACE_TEMPLATE_ID if bus_sides(design) is not None else template_of(design)\n", "    return SURFACE_TEMPLATE_ID\n")),
    m("M/colv-entry-guard-60", "mask P5 sec19", "the Row fans keep off the standard profile's 60-degree Column entry, not the Column V's own (they run along its diagonals)",
      (DIAGONAL_ENGINE, '    entry = plan["entry_angle_deg"]\n', "    entry = 60.0\n")),
    # The rectangular generator a subset of CAD mode (diagonal-bus/8, P5-diagonal-bus.md section 20, 2026-10-24): one rule
    # set and one construction on both templates, one outline down to the tail roots, the Column V capped at 80 degrees
    # where that roots the tails no deeper; the straight channel keeps the generic profile and its 7 mm default tail.
    m("M/sec20-generic-capped-always", "mask P5 sec20", "the rectangular generator keeps a rule of its own: its Column V always at the 80-degree cap "
      "(one-sided its boards differ from CAD mode's)",
      (DIAGONAL_ENGINE, "    plan = dict(column_plan(design, column_profile(profile) if capped else profile))\n",
       "    plan = dict(column_plan(design, column_profile(profile) if capped or design.get(\"template_id\") == \"generic_matrix_v1\" else profile))\n")),
    m("M/sec20-shared-at-field", "mask P5 sec20", "the shared outline stops at F's bottom (diagonal-bus/7's level): below it each board keeps its own body and "
      "the tails leave at their own depths",
      (DIAGONAL_ENGINE, "    level = root\n", "    level = round6(-rules.margin)\n")),
    m("M/sec20-level-above-fillets", "mask P5 sec20", "the tails' roots stay at the deeper of the boards' own roots, not lowered below the union's fillets "
      "into the tails",
      (DIAGONAL_ENGINE, "        root = floor6(top)\n", "        break\n")),
    m("M/sec20-cap-ignored", "mask P5 sec20", "the Column V is never capped (the profile's own caps: the Row funnel's fans 76-78 degrees, the tails 1.9-4.0 mm deeper)",
      (DIAGONAL_ENGINE, "    for capped in (True, False) if column_profile(profile) is not profile else (True,):\n", "    for capped in (False,):\n")),
    m("M/sec20-cap-always", "mask P5 sec20", "the Column V is always capped, also where the profile's own caps root the tails higher (one-sided)",
      (DIAGONAL_ENGINE, "    for capped in (True, False) if column_profile(profile) is not profile else (True,):\n", "    for capped in (True,):\n")),
    m("M/sec20-channel-bus-tail", "mask P5 sec20", "the generic straight channel's defaulted bottom tail is the bus's 12 mm (its builds change)",
      (CORE, '    if "tail.bottom_length_mm" in defaulted and template_of(design) == TEMPLATE_ID and bus_sides(design) is None:\n',
       '    if False:\n')),
    m("M/sec20-limits-bus-only", "mask P5 sec20", "the generic template's served limits drop the straight channel's own column bound (the form allows 64 columns with channel)",
      (SCHEMA, '        specs["matrix.columns"]["channel"] = {"maximum": channel_most}\n', "")),
    # The review of section 20 (P5-diagonal-bus.md section 20.1): the straight sides' bound measured to the outline as
    # filleted, and a side meeting a flush tail on the level straight or at a filleted corner.
    m("M/sec20-straight-bound-sharp", "mask P5 sec20", "the straight sides' bound is measured to the union's sharp concave corners (fine:002's chamfered side a "
      "filleted staircase again: 1.106 mm against 0.898 mm as filleted)",
      (DIAGONAL_ENGINE, "    ring = _round_ring(_straight_sides(ring, level, run, rings, _round_ring(_filleted(ring, rules)[0])))\n",
       "    ring = _round_ring(_straight_sides(ring, level, run, rings))\n")),
    m("M/sec20-level-points-merged", "mask P5 sec20", "the union's points on the level merge while it is made regular (a flush side reaches the level outside "
      "the tail's edge and steps back: 5.5 um and +4.97 / -4.24 degrees under diagonal-bus/9's one-sided tail; since the Row tail is "
      "centred, r2712:0469's fillets into its tail's edges, ending 58 nm above the level, 83 nm and 0.52 degrees)",
      (DIAGONAL_ENGINE, "    anchors = {tuple(point) for point in below}\n", "    anchors = set()\n")),
    m("M/sec20-run-on-last-edge", "mask P5 sec20", "the union runs on below the level along its last edge, not along a flush tail's side (rand:123's "
      "1.36-degree concave corner at the level left sharp)",
      (DIAGONAL_ENGINE, "        if best is None or _cross(best, direction) * side > 0.0:\n            best = direction\n    return best\n",
       "        if best is None or _cross(best, direction) * side > 0.0:\n            best = direction\n    return None\n")),
    m("M/sec20-root-corners-merged", "mask P5 sec20", "a tail's root corner a side meets at a slant merges while the union is made regular (its fillet chases "
      "the level down: E_ROW_BUS_INFEASIBLE)",
      (DIAGONAL_ENGINE, "    anchors |= {tuple(point) for point in ring if any(\n", "    anchors |= set() and {tuple(point) for point in ring if any(\n")),
    # The centred Row tail (diagonal-bus/10, P5-diagonal-bus.md section 27, the user's request: "some tails are not within
    # the sensor's width"): the Row tail centred on the field in every side mode, its rows at positions 1..R (mirrored, the
    # tail's far end), one side's inner flank slanting out to a tail wider than F's bottom.
    m("M/sec27-off-by-pitch", "mask P5 sec27", "the Row tail lies a contact pitch east of the field's centre (the tails stacked off each other's centre)",
      (DIAGONAL_ENGINE, "    tail_x, position = round6((geo.aw - width) / 2), \"centred\"\n",
       "    tail_x, position = round6((geo.aw - width) / 2 + rules.pitch), \"centred\"\n")),
    m("M/sec27-split-midway", "mask P5 sec27", "with both the funnel's contacts part midway between the innermost lanes again (diagonal-bus/9: the tail "
      "drifts off the field's centre on an asymmetric field)",
      (DIAGONAL_ENGINE, "    tail_x, position = round6((geo.aw - width) / 2), \"centred\"\n",
       "    tail_x, position = (round6(round6((x_band[near_rows[-1]] + x_band[far_rows[-1]]) / 2) - rules.side_offset - (len(near_rows) - 0.5) * rules.pitch)\n"
       "                        if two_sided else round6((geo.aw - width) / 2)), \"centred\"\n")),
    m("M/sec27-under-band", "mask P5 sec27", "with one side the Row tail lies under the band again (diagonal-bus/9: the outermost contact the rows use "
      "under the outermost lane, the tail beyond the sensor's width)",
      (DIAGONAL_ENGINE, "    tail_x, position = round6((geo.aw - width) / 2), \"centred\"\n",
       "    tail_x, position = (round6(x_band[order[0]] - rules.side_offset - first * rules.pitch) if not two_sided\n"
       "                        else round6((geo.aw - width) / 2)), \"centred\"\n")),
    m("M/sec27-mirror-dropped", "mask P5 sec27", "mirrored, the rows take the contacts of the tail's near end (turned back, a reader tail's last positions)",
      (DIAGONAL_ENGINE, "    first = pins - rows if geo.flip else 0\n", "    first = 0\n")),
    m("M/sec27-inner-ledge", "mask P5 sec27", "one side's inner flank steps out along F's bottom to a wider tail (the prototype's flat ledge) instead of "
      "slanting out to it",
      (DIAGONAL_ENGINE, "        slant = reach < tail_east - 1e-12 and tail_east - reach <= y_field - held\n", "        slant = False\n")),
    m("M/sec27-inner-slant-flat", "mask P5 sec27", "one side's inner flank slants out to a wider tail however flat (no step where the slant would lie flatter "
      "than 45 degrees)",
      (DIAGONAL_ENGINE, "        slant = reach < tail_east - 1e-12 and tail_east - reach <= y_field - held\n",
       "        slant = reach < tail_east - 1e-12 and y_field > held\n")),
    # The review of section 27 (P5-diagonal-bus.md section 27.3): each part of the inner flank's rule.
    m("M/sec27-inner-slant-half", "mask P5 sec27.3", "one side's inner flank slants out to a wider tail only within half its drop (26.6 degrees from the "
      "vertical; steeper than 45 it steps out along F's bottom: the fin's ledges of 25.5 and 29.2 mm2)",
      (DIAGONAL_ENGINE, "        slant = reach < tail_east - 1e-12 and tail_east - reach <= y_field - held\n",
       "        slant = reach < tail_east - 1e-12 and 2 * (tail_east - reach) <= y_field - held\n")),
    m("M/sec27-inner-slant-to-root", "mask P5 sec27.3", "one side's inner flank slants out to the tail's side at the tail root, not at the hold above it "
      "(a kink at the hold)",
      (DIAGONAL_ENGINE, "                x = max(x, reach + (tail_east - reach) * (y_field - y) / (y_field - held))\n",
       "                x = max(x, reach + (tail_east - reach) * (y_field - y) / (y_field - root))\n")),
    m("M/sec27-inner-unfilled", "mask P5 sec27.3", "one side's slanted inner flank is not made monotone (below F's bottom it narrows before it widens to "
      "the tail: the fin's waists of 2.8 and 4.4 mm)",
      (DIAGONAL_ENGINE, "        east_up = _unimodal(upper + lower[::-1], 1)[::-1] if slant else _running(lower, 1) + upper[::-1]\n",
       "        east_up = (upper + _running(lower[::-1], 1)[1:])[::-1] if slant else _running(lower, 1) + upper[::-1]\n")),
    # The video's notch (P5-diagonal-bus.md section 27.8, diagonal-bus/11): one side's flank without lanes convex from the
    # field's outline corner down to the tail (_convex_flank).
    m("M/sec27-flank-none", "mask P5 sec27.8", "one side's flank keeps the Column fan-out's notch below the field's outline corner (diagonal-bus/10's "
      "outline: the video's WidowX 250 and Robotiq 3F one-sided)",
      (DIAGONAL_ENGINE, "        convex = _convex_flank(ring, level, anchors, flank, rules)\n", "        convex = None\n")),
    m("M/sec27-flank-no-end-move", "mask P5 sec27.8", "a bridge from the field's outline corner meeting the next edge flatter than 5 degrees is not moved "
      "back along it, so the choice is passed over (gguard:045's notch above its 127 mm V slope kept)",
      (DIAGONAL_ENGINE, "            if abs(_turn(_minus(v, begin), out)) < _REGULAR_TURN:\n", "            if False:\n")),
    m("M/sec27-flank-unguarded", "mask P5 sec27.8", "a bridged flank is taken however it moves the fillets into the tail (r2711:0041's 50 nm inside the old "
      "fillet, a tiny field's tails' roots moved)",
      (DIAGONAL_ENGINE, "            if (abs(_tails_straight(filleted, level) - straight) <= _NOISE_MM and not any(outside(point, filleted) for point in flank)\n",
       "            if True or (abs(_tails_straight(filleted, level) - straight) <= _NOISE_MM and not any(outside(point, filleted) for point in flank)\n")),
    m("M/sec27-flank-corner-off-grid", "mask P5 sec27.8", "the field's outline corner sought within a nanometre's float noise of F's bottom, not on the layout grid "
      "(gguard:087's corner 1 nm above it missed, its notch kept)",
      (DIAGONAL_ENGINE, "    on = [k for k in range(len(points) - 1) if abs(points[k][1] - y_field) <= _GRID_STEP_MM]  # on the layout grid\n",
       "    on = [k for k in range(len(points) - 1) if abs(points[k][1] - y_field) <= _NOISE_MM]  # on the layout grid\n")),
    m("M/sec27-flank-point-kept", "mask P5 sec27.8", "the point put on F's bottom kept where the side runs on straight through it (r2712:0161: a concave "
      "micro-corner of its own, filleted, three vertices for one)",
      (DIAGONAL_ENGINE, "    if inserted and kept[1] is stretch[1]:\n", "    if False:\n")),
    m("M/sec27-flank-anchors-ignored", "mask P5 sec27.8", "a dent of the flank holding an anchor (a point on the level, a tail's root corner) is bridged",
      (DIAGONAL_ENGINE, "                    and not any(tuple(point) in anchors for point in dent)):\n", "                    ):\n")),
    m("M/sec27-flank-irregular", "mask P5 sec27.8", "a bridged flank is taken however flat its corners (rand5:074's corner turning 2.2 degrees)",
      (DIAGONAL_ENGINE, "            if all(abs(_turn(_minus(b, a), _minus(c, b))) >= _REGULAR_TURN for a, b, c in zip(run, run[1:], run[2:])):\n",
       "            if True:\n")),
)


# --------------------------------------------------------------------------
# Phase P5d: CAD mode's field-only containment (surface/fieldfit.py, the fit option containment: field), its map, and
# the P5c carry-overs (field_footprint and E_BOARD_SIZE on the diagonal boards, the folded Row pins in ORDER_NOTES.txt).
# --------------------------------------------------------------------------

FIELDFIT = "surface/fieldfit.py"

FIELD_FIT = (
    m("M/field-board-containment", "mask P5d", "containment: field fits the whole board as before (the soft finger falls to 352)",
      (FIT, '    if options.get("containment") == "field":\n', "    if False:\n")),
    m("M/field-dp-phases-swapped", "mask P5d", "the DP reads the narrowing-left phase from the narrowing-right table and back (killed by the brute force)",
      (FIELDFIT, "    return sub, left, right, holds, left_strict, right_strict\n", "    return sub, right, left, holds, right_strict, left_strict\n")),
    m("M/field-dp-carry-short", "mask P5d", "a run carries one cell less into the row above (the DP loses fields its brute force finds)",
      (FIELDFIT, "            carry = min(carries[a], top) - a + 1 if cur is not None else 0\n", "            carry = min(carries[a], top) - a if cur is not None else 0\n")),
    m("M/field-dp-early-exit", "mask P5d", "the DP stops when its best can only equal the threshold plus one",
      (FIELDFIT, "        if max(best >> _SHIFT, reach) <= threshold:\n", "        if max(best >> _SHIFT, reach) <= threshold + 1:\n")),
    m("M/field-quadrant-least", "mask P5d", "the quadrant bound takes the window less its largest quadrant (no bound: it prunes fields that hold)",
      (FIELDFIT, "                found = max(sides)\n", "                found = min(sides)\n")),
    m("M/field-rectangle-plain", "mask P5d", "a rectangle's lower rows are freed by their own strips, not with the filler band above them",
      (FIELDFIT, "            reach = list(map(min, reach, up[j1]))\n", "            reach = list(map(min, reach, plain[j1]))\n")),
    m("M/field-fillers-unchecked", "mask P5d", "at sparse pitches the filler band between rows is not checked",
      (FIELDFIT, "    sparse = pitch - width > 2 * margin + _NOISE\n", "    sparse = False\n")),
    m("M/field-reader-uncapped", "mask P5d", "a named reader does not cap the field search (the soft finger's 48x48 proposal is 59 x 12)",
      (FIELDFIT, '    found = reader_module.field_caps(options["reader"], options["max_rows"], options["max_columns"])\n',
       '    found = reader_module.field_caps("none", options["max_rows"], options["max_columns"])\n')),
    m("M/field-no-turn-gain", "mask P5d", "a turned field needs no more taxels than the best unturned one (the equilateral plate proposes 339 turned 30 degrees)",
      (FIELDFIT, "TURN_GAIN = (103, 100)\n", "TURN_GAIN = (100, 100)\n")),
    m("M/field-no-narrow-tip", "mask P5d", "with several exits the fields within three taxels are not ranked by their tip (the crank's 64.8 mm tip)",
      (FIELDFIT, "    if not auto_exit or not kept:\n", "    if True:\n")),
    m("M/field-walls-open", "mask P5d", "F may cross the exit edge (the fit's check of F treats it as an exit, not a wall)",
      (FIELDFIT, "        found = fit.ExitOutline(space.outline, [])\n", "        found = fit.ExitOutline(space.outline, space.exit_edges)\n")),
    m("M/field-map-exit-open", "mask P5d", "the map's field_clearance lets F cross the exit edge",
      (FIELDFIT, "    region = fit.ExitOutline(outline, [])\n", "    region = fit.ExitOutline(outline, exits.exit_edges)\n")),
    m("M/field-map-board-records", "mask P5d", "the map of a field-only placement checks the whole boards (board_clearance fails beside the surface)",
      (PLACE, '    if options["containment"] == "field":\n', "    if False:\n")),
    m("M/field-tail-run-ignored", "mask P5d", "a tail is sized from its root as if the surface ended there (its end may lie on the surface)",
      (FIELDFIT, "    return {key: root - bottom_beside(lowest, x0, x1, frame) for key, (x0, x1, root) in tails.items()}\n",
       "    return {key: 0.0 for key in tails}\n")),
    m("M/field-tail-beside-on-edge", "mask P5f review", "a tail beside the surface is sized as if its root lay on the base edge (the soft finger's Column tail ended 27.8 mm past it)",
      (FIELDFIT, "    return {key: root - bottom_beside(lowest, x0, x1, frame) for key, (x0, x1, root) in tails.items()}\n",
       "    return {key: (0.0 if surface_bottom(lowest, x0, x1) is None else root - bottom_beside(lowest, x0, x1, frame)) for key, (x0, x1, root) in tails.items()}\n")),
    m("M/field-reach-beside-unmeasured", "mask P5f review", "the tail reach record of a tail beside the surface is unmeasured (infinite, shown as a dash)",
      (FIELDFIT, "    if reach == math.inf:\n        reach = bottom_beside(lowest, left, right, frame) - tip\n", "")),
    m("M/sec27-tails-own-ends", "mask P5 sec27.3", "each tail ends the extension past the surface's lowest edge under its own width, not on one line with "
      "the other (the stacked contacts apart: the slanted plate's 16 x 12 by 1.732 mm, the holed plate's turned field by 0.364)",
      (FIELDFIT, "    end = min(roots[key] - alone[key] for key in runs)\n    return {key: round(math.ceil((roots[key] - end) * 1000 - 1e-6) / 1000, 3) for key in runs}\n",
       "    return {key: round(alone[key], 3) for key in runs}\n")),
    m("M/sec27-tails-shared-reach", "mask P5 sec27.3 review", "the line pushed by the shared reach of P5d's review: every tail ends as far past "
      "the edge under it as the deepest root's shortest tail would (runs of 4 and -15 mm: 26.5 mm where 24 do; the video's galaxea "
      "26 x 10 22.989 mm where 18.101 do)",
      (FIELDFIT, "    alone = {key: max(minimum, math.ceil((run + extension) * 1000 - 1e-6) / 1000) for key, run in runs.items()}\n",
       "    reach = max([extension] + [minimum - run for run in runs.values()])\n"
       "    alone = {key: max(minimum, math.ceil((run + reach) * 1000 - 1e-6) / 1000) for key, run in runs.items()}\n")),
    m("M/sec27-tails-reach-floored", "mask P5 sec27.5", "a tail reaching the line set by the other is rounded down to the micrometre, "
      "ending short of it (29.234 mm where the line lies 29.2345674 mm below its root)",
      (FIELDFIT, "    return {key: round(math.ceil((roots[key] - end) * 1000 - 1e-6) / 1000, 3) for key in runs}\n",
       "    return {key: round(math.floor((roots[key] - end) * 1000 + 1e-6) / 1000, 3) for key in runs}\n")),
    m("M/field-mask-unmirrored", "mask P5d", "with the columns on top the mask is not mirrored (COL_01 is on the right seen from outside)",
      (FIELDFIT, "    return [(columns - high, columns - low) for low, high in cells]\n", "    return [(low + 1, high + 1) for low, high in cells]\n")),
    m("M/field-row-sides-fixed", "mask P5d", "every proposal gets both sides whatever the option row_sides",
      (FIELDFIT, '    design["routing"]["row_sides"] = options["row_sides"]\n    result = generate_design(design, cache=cache)\n',
       '    design["routing"]["row_sides"] = "both"\n    result = generate_design(design, cache=cache)\n')),
    m("M/field-readout-unfolded", "mask P5d", "the map's readout does not list the Row contact order (the folded pins)",
      (PLACE, '            mapped_result["readout"]["row_contact_order"] = list(order)\n', "            pass\n")),
    m("M/footprint-straight-plans", "mask P5d", "field_footprint measures a diagonal Row bus on the straight channel's plans (the P5c carry-over)",
      (LAYOUT, "    if row_bus(design):\n        return _diagonal_footprint(design, profile)\n", "    if False:\n        return _diagonal_footprint(design, profile)\n")),
    m("M/board-size-straight-plans", "mask P5d", "E_BOARD_SIZE measures a diagonal Row bus on the straight channel's plans (64 x 4 at 7.1 mm passes validation)",
      (LAYOUT, "    if row_bus(design):\n        errors.extend(_diagonal_size_errors(design, profile, fallback))\n", ""),
      (LAYOUT, "    for role, planner, plan in () if row_bus(design) else (", "    for role, planner, plan in () if False else (")),
    m("M/board-size-advice-unverified", "mask P5d", "the diagonal bus's size advice is the straight plans' (bounds that leave the bus too large)",
      (LAYOUT, "        for values in _size_advice(design, profile, role, modelled):\n", "        for values in _size_advice(design, profile, role, planner):\n"),
      (LAYOUT, "            if changed is not None and _fits({\"outline_size\": changed}, limits):\n", "            if True:\n")),
    m("M/export-row-pins-unnoted", "mask P5d", "ORDER_NOTES.txt does not state the folded Row pins (and the read-back does not ask for them)",
      (GERBER, "        for note in _row_contact_notes(board):\n", "        for note in ():\n"),
      (GERBER, "        phrases += _row_contact_phrases(board)\n", "")),
    # Phase P5e: field-only containment the default with shape fill, the map's containment from the design, the field
    # fit's no-fit reason, and the browser client's Row traces and Containment (the Playwright checks run them too).
    m("M/field-not-default", "mask P5e", "the fit's default stays containment board (the soft finger's default fit falls to 352)",
      (FIT, '    "containment": "field",\n', '    "containment": "board",\n')),
    m("M/map-containment-fixed", "mask P5e", "a map without containment takes the fit's default, not the design's (a straight design maps with F's records)",
      (PLACE, '    if not isinstance(raw, Mapping) or "containment" in raw:\n        return raw\n', "    if True:\n        return raw\n")),
    m("M/field-no-fit-silent", "mask P5e", "a field-only fit that finds no field gives no reason (the browser's note lists nothing)",
      (FIELDFIT, "    if not queue:\n        # Not one crossing", "    if False:\n        # Not one crossing")),
    m("M/web-payload-drops-row-sides", "mask P5e", "Generate posts the form without the proposal's routing.row_sides (the build is not the proposal's)",
      (WEB, "    if (sides) body.routing = {row_sides: sides};\n", "")),
    # M/web-row-sides-on-generic (the form sends routing.row_sides on the generic template) retired with
    # P5-diagonal-bus.md section 18, which sends it there: M/rect-web-row-sides-surface-only is its inverse.
    m("M/web-row-sides-kept", "mask P5e", "a design without routing.row_sides leaves the form's Row traces as they were (a board proposal builds a bus)",
      (WEB, '      rowSides: routing.row_sides ?? "channel"\n', "      rowSides: routing.row_sides\n")),
    # M/web-containment-on-rectangle (Containment enabled on the Rectangular board rules) retired with section 26.16: no
    # Board rules.
    m("M/web-flat-unclipped", "mask P5e", "the flat view draws the boards solid everywhere (the parts off the surface are not told apart)",
      (CAD_MAIN, 'shape(list, className, {"clip-path": "url(#cadFlatOn)"})', "shape(list, className)")),
    # The P5d/P5e reviews' fixes (2026-10-22): the search (the turn threshold, phase 0, the quarter phases, the whole
    # lattice, the early exit, the rectangle's pruning, the work budget, the bases tried, the narrow tip), the tails, the
    # routing report (the overhang, the holes, the fillet and the base edge), the map (a straight design, the Row pins),
    # the order note of a one-sided bus, and the browser client (the badge, the CSV, the pins, the stale Generate, one
    # map request at a time).
    m("M/field-turned-prunes-unturned", "mask P5d review", "the turned fields raise an unturned lattice's threshold (they pruned the unturned field a turned one must beat)",
      (FIELDFIT, "            if kind and not turned:\n                continue\n", "")),
    m("M/field-phase-off-edge", "mask P5d review", "phase 0 puts the first crossing on the outline's extreme, not on the usable edge (a 2.6 mm strip holds no field)",
      (FIELDFIT, "    x0 = space.x0 + space.margin + phase[0] + margin\n    y0 = space.y0 + space.margin + phase[1] + margin\n",
       "    x0 = space.x0 + phase[0] + margin\n    y0 = space.y0 + phase[1] + margin\n")),
    m("M/field-quarter-found-only", "mask P5d review", "only the frames that kept a field at the coarse phases get the quarter phases (a narrow exit's field is missed)",
      (FIELDFIT, "            pitch = mine[0][1] if mine else pitches[0]\n", "            if not mine:\n                continue\n            pitch = mine[0][1]\n")),
    m("M/field-whole-lattice-unfit", "mask P5d review", "the whole lattice's field is taken even when it does not fit the caps",
      (FIELDFIT, "            if max(b for _, _, b in spans) - min(a for _, a, _ in spans) < columns_cap:\n", "            if True:\n")),
    m("M/field-early-exit-wrong-side", "mask P5d review", "the early exit bounds a left-narrowing state by the runs left of its left end (it stops too early)",
      (FIELDFIT, "                        value = (max(carried_keys) >> _SHIFT) + left_above[a]\n", "                        value = (max(carried_keys) >> _SHIFT) + right_above[a]\n")),
    m("M/field-rectangle-prune-height", "mask P5d review", "a bottom row stops growing when its widest run times the rows it has (not the rows it can take) cannot beat the best",
      (FIELDFIT, "            if widest <= 0 or min(widest, columns_cap) * tallest <= best[0]:\n", "            if widest <= 0 or min(widest, columns_cap) * height <= best[0]:\n")),
    m("M/field-budget-ignored", "mask P5d review", "the search has no work budget (the round-hole plate at 1.5 mm takes 30 s)",
      (FIELDFIT, "WORK_BUDGET = 3_000_000\n", "WORK_BUDGET = None\n")),
    m("M/field-budget-windows", "mask P5d review", "a lattice's windows go on past the work budget (only the next lattice stops)",
      (FIELDFIT, "        if bound <= floor or (budget is not None and meter[0] >= budget):\n", "        if bound <= floor:\n")),
    m("M/field-bases-found-only", "mask P5d review", "the fit lists only the frames that kept a field (E_SURFACE_NO_FIT lists no base)",
      (FIELDFIT, "        if key in tally:\n            record = {", "        if tally.get(key):\n            record = {")),
    m("M/field-narrow-tip-per-field", "mask P5d review", "the narrow tip sorts every field, not the exits (a masked 254 before the full 256 of its readout)",
      (FIELDFIT, '    near.sort(key=lambda candidate: (lead[candidate["order"]], candidate["rank"]))\n',
       '    near.sort(key=lambda candidate: (candidate["tip_mm"], candidate["rank"]))\n')),
    m("M/field-overhang-tails", "mask P5d review", "the tails' corners below the surface count as overhang beside it (the disk's Row FPC: its tail's end)",
      (FIELDFIT, "            if p[1] < lowest - 1e-6:\n                if y is None and not bottom.x0 <= p[0] <= bottom.x1 and p[1] >= root - 1e-6:\n"
                 "                    beyond = max(beyond, bottom_beside(bottom, p[0], p[0], frame) - p[1])\n                continue\n", "")),
    m("M/field-exit-corners-only", "mask P5f review", "the overhang past the base edge reads the outline's corners only (a neck as wide as its tail has none at its root)",
      (FIELDFIT, "        for p in polygon + at_root + at_lowest:\n", "        for p in polygon + at_lowest:\n")),
    m("M/field-overhang-lowest-skipped", "mask P5 sec20", "the side overhang skips where an outline crosses the surface's lowest level (a straight side running "
      "on past the base edge: the soft finger's 0.11 mm)",
      (FIELDFIT, "        for p in polygon + at_root + at_lowest:\n", "        for p in polygon + at_root:\n")),
    m("M/field-exit-beside-skipped", "mask P5f review", "a board beside the surface and past its lowest point does not count past the base edge (the soft finger's funnel read 0.0)",
      (FIELDFIT, "                if y is None and not bottom.x0 <= p[0] <= bottom.x1 and p[1] >= root - 1e-6:\n"
                 "                    beyond = max(beyond, bottom_beside(bottom, p[0], p[0], frame) - p[1])\n", "")),
    m("M/field-report-no-holes", "mask P5d review", "a board's share on the surface counts the holes as surface",
      (FIELDFIT, "    polygons = [space.outline, *holes]\n", "    polygons = [space.outline]\n")),
    m("M/field-wrap-no-rings", "mask P5d review", "the edge warning measures only the boundary edge (a R0.8 fillet's first edge shows 1.59 mm: no warning)",
      (FIELDFIT, "WRAP_RINGS = 3\n", "WRAP_RINGS = 0\n")),
    m("M/field-edges-skip-base", "mask P5d review", "the edge warning skips the base edge (the bands, the bus and the fan-out cross it)",
      (FIELDFIT, '            kind = "base" if i in exit_edges else "side"\n', '            if i in exit_edges:\n                continue\n            kind = "side"\n')),
    m("M/field-map-straight-crash", "mask P5d review", "F of a straight-channel design reads the active outline it has not (a 500 for a map with containment field)",
      (FIELDFIT, '    if "active_outline" in registration:\n        polygon = fill.field_polygon(result, (0.0, 0.0))\n',
       '    if True:\n        polygon = fill.field_polygon(result, (0.0, 0.0))\n')),
    m("M/field-row-pins-positions", "mask P5d review", "the readout's row_pin_order lists the contact positions (a reversed scan order puts ROW_02 on pin 1)",
      (PLACE, '            mapped_result["readout"]["row_pin_order"] = row_pin_order(pins["row"])\n', '            mapped_result["readout"]["row_pin_order"] = list(order)\n')),
    m("M/export-one-side-folded", "mask P5d review", "ORDER_NOTES.txt calls a one-sided bus's identity order folded",
      (GERBER, '    return "folded" if board["construction"]["row_bus"]["sides"] == "both" else "one side"\n', '    return "folded"\n')),
    m("M/web-badge-full", "mask P5e review", "a full diagonal-bus field gets the masked badge (\"708 of 59 x 12 taxels active (masked field ...)\")",
      (WEB, "    if (!mask || !(registration.active_taxel_count < mask.rows * mask.columns)) return null;\n", "    if (!mask) return null;\n")),
    m("M/web-map-pins-positions", "mask P5e review", "the map panel lists the Row contact positions as pins (wrong with Scan order Reverse)",
      (CAD_MAIN, "    const order = cad.map.readout?.row_pin_order || cad.map.readout?.row_contact_order;\n", "    const order = cad.map.readout?.row_contact_order;\n")),
    m("M/web-generate-stale", "mask P5e review", "Generate builds the proposal of the old settings after an option change",
      (CAD_MAIN, "  button.disabled = !proposal || Boolean(cad.pendingBuild) || stale;\n", "  button.disabled = !proposal || Boolean(cad.pendingBuild);\n")),
    m("M/web-two-maps", "mask P5e review", "choosing a generated proposal sends the preview and the build's map together (the server answers 503)",
      (CAD_MAIN, "  if (cad.lastResult?.ok && cad.lastResult.manifest.build_id === proposal.build_id) mapBuild(cad.lastResult, {look});\n  else previewProposal({look});\n",
       "  previewProposal({look});\n  if (cad.lastResult?.ok && cad.lastResult.manifest.build_id === proposal.build_id) mapBuild(cad.lastResult, {look});\n")),
    m("M/web-csv-full-readout", "mask P5e review", "the CSV of a full diagonal-bus field lists its readout positions with an active column",
      (CAD_MAIN, "  if (!map.readout || !(map.readout.active < map.readout.positions)) return", "  if (!map.readout) return")),
    # The corner tolerance, the rectangle preference and the chamfered notches (diagonal-bus/6, the plan's section 16).
    m("M/corner-general-widening", "mask P5 sec16", "the corner zones reach along F's whole sides (the tolerance widens every straight side: a 25.6 mm square takes 13 x 13)",
      (FIELDFIT, "    return round(min(margin, width / 3), 9)\n", "    return round(margin + width, 9)\n")),
    m("M/corner-taxels-off", "mask P5 sec16", "the zones reach into P too (a corner taxel's own corner may leave the surface: a square bitten 0.8 mm at a corner keeps 144)",
      (FIELDFIT, "        grow = -reach if (middle < y or middle > y + width) else 0.0\n", "        grow = -reach\n"),
      (FIELDFIT, "            grow = max(grow, inner)\n", "            grow = max(grow, inner) if inner > 0 else grow\n"),
      (FIELDFIT, "        across.append((x0, low, x1, high))\n",
       "        across.append((x0, low + (reach if k == 0 else 0.0), x1, high - (reach if k == count - 1 else 0.0)))\n"),
      (FIELDFIT, "        along.append((low, x0, high, x1))\n",
       "        along.append((low, x0 + (reach if k in (0, count - 1) else 0.0), high, x1 - (reach if k in (0, count - 1) else 0.0)))\n")),
    m("M/corner-zones-every-row", "mask P5 sec16", "the search leaves out every corner zone, at aligned and concave ends too (section 24 holds them: the DP and the rectangle "
      "search against brute force)",
      (FIELDFIT, "            below, own = zones[j - 1] if zones else None, zones[j] if zones else None\n", "            below, own = None, None\n"),
      (FIELDFIT, "            if j1 > j0 and zones and zones[j1] is not None:\n", "            if False:\n"),
      (FIELDFIT, "            if zones and zones[j1] is not None:\n", "            if False:\n")),
    # M/corner-preference-ignored and M/corner-preference-unbounded (the rectangle preference) retired with section 26.16:
    # CAD mode has no rectangle preference.
    # Coverage first (the user's correction, P5-diagonal-bus.md section 21): shaped fields take the rectangles' caps and
    # the rectangle preference is off by default, set only on the first field's exit and frame.
    m("M/sec21-shaped-cap-32", "mask P5 sec21", "the field fit's shaped fields are capped at 32 x 32 again (the fin's taper field 371 loses to a long side's fields)",
      (FIELDFIT, "    return list(found), list(found)\n", "    return [(min(rows, 32), min(columns, 32)) for rows, columns in found], list(found)\n")),
    m("M/sec21-walk-cap-32", "mask P5 sec21", "the board fit's masked walk is capped at 32 x 32 again (the soft finger's 44 x 8 rectangle first, not the masked 470)",
      (FILL, '        self.caps = reader_module.field_caps(options["reader"], options["max_rows"], options["max_columns"])\n',
       '        self.caps = reader_module.field_caps(options["reader"], min(options["max_rows"], 32), min(options["max_columns"], 32))\n')),
    m("M/sec21-auto-uncapped", "mask P5 sec21", "reader auto caps no field at the largest reader's 48 x 48 (fields no reader holds)",
      (READER, '    if option == "auto":\n        option = max(READERS', '    if False:\n        option = max(READERS')),
    # M/sec21-preference-across-exits and M/sec21-preference-default-5 retired with section 26.16 (no rectangle preference).
    # Symmetric sensors on symmetric faces (the user's request, P5-diagonal-bus.md section 22).
    m("M/sec22-symmetry-ignored", "mask P5 sec22", "no face is symmetric about its exit (the fin's 569 0.2 mm off its axis first, the soft finger's field off its centre)",
      (FIELDFIT, '    return {"symmetric": worst <= tolerance, "axis": axis,', '    return {"symmetric": False, "axis": axis,')),
    m("M/sec22-asymmetric-run-accepted", "mask P5 sec22", "a field centred on a symmetric exit's axis counts as symmetric with a row that is not its own mirror image",
      (FIELDFIT, '    if any(low + high != columns - 1 for low, high in candidate["cells"]):\n        return False\n', "")),
    m("M/sec22-symmetric-runs-shifted", "mask P5 sec22", "the symmetric DP's runs of an odd column count reach one column too far right (not their own mirror image)",
      (FIELDFIT, "    return [(centre - h, columns - 1 - centre + h) for h in range(centre + 1)]\n",
       "    return [(centre - h, min(columns - 1, columns - centre + h)) for h in range(centre + 1)]\n")),
    m("M/sec22-turned-on-symmetric-exit", "mask P5 sec26.19", "a symmetric exit is turned even when its symmetric field holds within 20 % of its "
      "best unturned field (the isosceles triangle's base, the right triangle's hypotenuse and the 58 mm axis-hole plate turned)",
      (FIELDFIT, "            for order, _, _ in best_frames(False, TURNED_EXITS, skipped):\n", "            for order, _, _ in best_frames(False, TURNED_EXITS):\n")),
    # M/sec22-symmetric-unbounded (a symmetric field first however few taxels it has) retired with section 26.17: the user's
    # decision of 2026-10-27 made that the rule (symmetric_leads and SYMMETRY_GAIN were gone); since section 26.19's
    # threshold it is a defect again, M/sec26-symmetric-without-threshold below.
    m("M/sec23-caps-choose-the-exit", "mask P5 sec23", "a smaller readout chooses the exit (the fin with max_rows 32: 14 x 59 on a long side first, the tails sideways)",
      (FIELDFIT, '    if info.get("capped"):\n', "    if False:\n")),
    m("M/sec23-rows-at-the-exit", "mask P5 sec23", "a capped field takes the rows next to the exit, not at the fingertip (the far end)",
      (FIELDFIT, "    return (max(0, last - cap + 1), last)\n", "    return (0, min(last, cap - 1))\n")),
    m("M/sec23-tails-at-80", "mask P5 sec23", "the surface's tails held at 80 mm again (the fin's 16 rows at the tip need 102 mm)",
      (FIT, 'TAIL_MAX_MM = {"surface": 200.0, "generic": 80.0}\n', 'TAIL_MAX_MM = {"surface": 80.0, "generic": 80.0}\n')),
    m("M/sec23-cap-not-searched-again", "mask P5 sec27.5", "a capped field whose tails would pass the 200 mm is not searched for again nearer "
      "the exit (the fin stretched 2.6 times: its mount end's 16 rows refused, a long side's 14 x 64 first)",
      (FIELDFIT, '    return max(0.0, max(lengths.values()) - fit.TAIL_MAX_MM[options["template"]])\n', "    return 0.0\n")),
    m("M/sec23-cap-not-refused", "mask P5 sec27.5", "the fit's own refusal of tails past the 200 mm off (its threshold 1000 mm higher): "
      "such a field goes to the engine, which refuses it with E_TAIL_LENGTH instead",
      (FIELDFIT, '    if max(lengths.values()) > fit.TAIL_MAX_MM[options["template"]] + 1e-9:\n        return (fit.tails_too_long(options["template"]), None)\n',
       '    if max(lengths.values()) > fit.TAIL_MAX_MM[options["template"]] + 1000.0:\n        return (fit.tails_too_long(options["template"]), None)\n')),
    # The corner tolerance at every convex corner and convex sides (the user's request, P5-diagonal-bus.md section 24).
    m("M/sec24-aligned-ends-exempt", "mask P5 sec24", "F's check leaves out the corner zones at aligned ends too (a straight side's margin may leave the surface)",
      (FIELDFIT, "        found.append((below is None or below[2] > x0 + _NOISE, below is None or below[3] < x1 - _NOISE,\n"
                 "                       above is None or above[2] > x0 + _NOISE, above is None or above[3] < x1 - _NOISE))\n",
       "        found.append((below is None or below[2] > x0 - _NOISE, below is None or below[3] < x1 + _NOISE,\n"
       "                       above is None or above[2] > x0 - _NOISE, above is None or above[3] < x1 + _NOISE))\n")),
    m("M/sec24-aligned-own-zone-dropped", "mask P5 sec24", "the DP takes an aligned predecessor without the run's own bottom left zone (aligned ends half exempted)",
      (FIELDFIT, "        x = a if bl[a] else a + 1\n", "        x = a\n")),
    m("M/sec24-convex-corners-held", "mask P5 sec24", "the DP holds a lower run's top zones at its convex corners too (section 16's rule: the crank 683, not 696)",
      (FIELDFIT, "        _masked(v0, n, tl, tr), _masked(list(map(max, v0, v1)), n, full, tr), _masked(list(map(max, v0, v2)), n, tl, full),\n"
                 "        list(map(max, v0, v1, v2, v3)), n, not all(tl), not all(tr))\n",
       "        _masked(v0, n, tl, tr), _masked(list(map(max, v0, v1)), n, tl, tr), _masked(list(map(max, v0, v2)), n, tl, tr),\n"
       "        _masked(list(map(max, v0, v1, v2, v3)), n, tl, tr), n, not all(tl), not all(tr))\n")),
    m("M/sec24-parts-four-corners", "mask P5 sec24", "F's check leaves out only the field's four corner zones (section 16's parts: the crank's 696 peeled back)",
      (FIELDFIT, "        found.append((below is None or below[2] > x0 + _NOISE, below is None or below[3] < x1 - _NOISE,\n"
                 "                       above is None or above[2] > x0 + _NOISE, above is None or above[3] < x1 - _NOISE))\n",
       "        found.append((below is None, below is None, above is None, above is None))\n")),
    m("M/sec24-symmetric-old-rule", "mask P5 sec24", "the symmetric DP holds every interior corner zone (a run over a narrower one its own bottom zones too)",
      (FIELDFIT, "                rising = [rising[h] if held[h] else (rising[h - 1] if h else -1) for h in range(count)]\n",
       "                rising = [rising[h] if held[h] else -1 for h in range(count)]\n")),
    m("M/sec24-no-convex-sides", "mask P5 sec24", "no convex sides (diagonal-bus/8's outline: the S-kink beside a narrow tip stays)",
      (DIAGONAL_ENGINE, "    convex, widest = _convex_sides(ring, level, _round_ring(_filleted(ring, rules)[0]), anchors, depth)\n",
       "    convex, widest = ring, []\n")),
    m("M/sec24-hull-unbounded", "mask P5 sec24", "convex sides bridge any dent however deep (a pocket of the staircase filled: the outline balloons)",
      (DIAGONAL_ENGINE, "            if deep <= depth + _NOISE_MM and corners_hold and not any(tuple(point) in anchors for point in points[u + 1:v]):\n",
       "            if corners_hold and not any(tuple(point) in anchors for point in points[u + 1:v]):\n")),
    # The taxels from the fingertip (the user's request of 2026-10-26, P5-diagonal-bus.md section 26): the rectangle's cap
    # before its zones (26a), the filler band over the common extent (26b), the tip-first fields (26c) and rectangles (26d).
    m("M/sec26-rectangle-zones-before-cap", "mask P5 sec26", "the full rectangle reads the right zones of a run's uncapped end (55ae8fe: a capped rectangle ends on a blocked zone)",
      (FIELDFIT, "                spans = [last[min(end, a + columns_cap - 1)] - a + 1 if end >= a and left_ok[a] else 0\n",
       "                spans = [last[end] - a + 1 if end >= a and left_ok[a] else 0\n")),
    m("M/sec26-filler-unchecked", "mask P5 sec26", "the filler band between rows at sparse pitches is not checked (a filler off the surface is left to the peel)",
      (FIELDFIT, "            filler = _free_ends(band, x0, pitch, width, margin, columns)\n", "            filler = [columns - 1] * columns\n")),
    m("M/sec26-filler-whole-run", "mask P5 sec26", "the shaped DP holds the filler over the lower row's whole run again (only runs holding it carry: 55ae8fe's model)",
      (FIELDFIT, "        carries = _row_tops(up[j], col_lo, col_hi) if band is None else tops\n", "        carries = _row_tops(up[j], col_lo, col_hi)\n")),
    m("M/sec26-filler-phase2-no-start", "mask P5 sec26", "phase 2 reads the filler band's run from the range's own start (a' may start left of b's free run of the band)",
      (FIELDFIT, "            t2[row + b] = beyond[b] if start[b] > x else ((right if tr[b] else right_strict)[x * n + b] if x <= b else -1)\n",
       "            t2[row + b] = ((right if tr[b] else right_strict)[x * n + b] if x <= b else -1)\n")),
    m("M/sec26-filler-phase3-own-band", "mask P5 sec26", "phase 3 drops the state's own band (a wider run below needs the filler over this run's cells)",
      (FIELDFIT, "            for b in range(a, min(limit, n - 1) + 1):\n", "            for b in range(a, n):\n")),
    m("M/sec26-share-ignored", "mask P5 sec26", "the tip pass keeps no field but the lead (the crank's 696 stays first, its tip gap 1.2 mm)",
      (FIELDFIT, "            pool.append(candidate)\n", "            continue\n")),
    m("M/sec26-share-from-lead", "mask P5 sec26", "the 3 % share is measured from the group's lead, not the exit's most (an asymmetric lead under the "
      "exit's most gives up more than 3 % of it)",
      (FIELDFIT, '    most = max([candidate["value"] for candidate in same] + [lead["value"]])\n', '    most = lead["value"]\n')),
    m("M/sec26-slack-quarter", "mask P5 sec26", "a reach within a quarter pitch of the farthest counts as reaching it (one-phase shifts hidden; "
      "an asymmetric group's slack since section 26.18, a symmetric group's its own)",
      (FIELDFIT, '    slack = int(round(lead["pitch"] * 1e6)) // TIP_SLACK\n', '    slack = int(round(lead["pitch"] * 1e6)) // 4\n')),
    m("M/sec26-slack-zero", "mask P5 sec26", "only the farthest reach leads (fields give up taxels for a tenth of a millimetre; an asymmetric "
      "group's slack since section 26.18)",
      (FIELDFIT, '    slack = int(round(lead["pitch"] * 1e6)) // TIP_SLACK\n', "    slack = 0\n")),
    m("M/sec26-full-guard-removed", "mask P5 sec26", "a full lead takes notched fields too (the rounded plates' full 252 turn into notched 250s)",
      (FIELDFIT, '    full = bool(lead["full"])\n    frame = {"order": lead["order"]', '    full = False\n    frame = {"order": lead["order"]')),
    m("M/sec26-group-across-exits", "mask P5 sec26", "one group per pitch and symmetry kind across the exits (a second exit's lead keeps its slot)",
      (FIELDFIT, '        group = (candidate["order"], candidate["pitch"], bool(candidate.get("symmetric")))\n',
       '        group = (candidate["pitch"], bool(candidate.get("symmetric")))\n')),
    m("M/sec26-displaced-dropped", "mask P5 sec26", "the tip-first field (and the lead's tie) replace the lead (the crank's 696 is no longer proposed)",
      (FIELDFIT, "        queue[at:at] = placed\n", "        queue[at:at + 1] = placed\n")),
    m("M/sec26-key-without-tip-lead", "mask P5 sec26", "the proposal key lacks the tip-first flag (a displaced lead of the same readout, the crank's 696, is dropped)",
      (FIELDFIT, '(bool(candidate["symmetric"]), lead)\n', '(bool(candidate["symmetric"]), False)\n'),
      (FIELDFIT, '(metrics["symmetry"]["field"], lead)\n', '(metrics["symmetry"]["field"], False)\n')),
    m("M/sec26-full-window-ignored", "mask P5 sec26", "a full lead's tip pass ignores section 23's window (its rectangles' rows read from the whole lattice, "
      "placed as the window's)",
      (FIELDFIT, "            for item in rectangles_by_top(plain[low:high + 1], up[low:high + 1], rows_cap, columns_cap, window_zones):\n",
       "            for item in rectangles_by_top(plain, up, rows_cap, columns_cap, zones):\n")),
    # M/sec26-rectangle-reference-farthest and M/sec26-rectangle-share-100 (shape rectangle's tip-first rectangle, 26d)
    # retired with section 26.16: CAD mode has no shape rectangle.  M/sec26-rectangle-window-ignored became
    # M/sec26-full-window-ignored (the same window on a full lead's pass).
    # Section 26's round 2 (26.15): the lead's zero-cost tie, tip_first false as the ties alone; and what round 1 left
    # unpinned (its review).  Its tip-zone guard and tie-break, shape rectangle's 80 % floor and column guard, and their
    # mutants (M/sec26-zone-guard-removed, M/sec26-zone-guard-lead-only, M/sec26-zone-tie-break-dropped,
    # M/sec26-tie-break-lead-dropped, M/sec26-rectangle-floor-70, M/sec26-rectangle-columns-unguarded,
    # M/sec26-rectangles-narrowest-ignored, M/sec26-symmetric-narrowest-ignored) retired with section 26.16 (reach first:
    # a pointed tip may end in a single taxel; no rectangle rule in CAD).
    m("M/sec26-tie-dropped", "mask P5 sec26", "the lead's zero-cost tie is not placed (the long taper's 844 stays 0.5 mm short of its tie)",
      (FIELDFIT, "        if _field_key(tie) != _field_key(lead):\n", "        if False:\n")),
    m("M/sec26-pass-drops-short-ties", "mask P5 sec26", "the tip pass keeps no tie of the lead short of the tip-first field's reach (T0 is the lead whenever T reaches "
      "farther: the long taper's 844 stays 0.5 mm short)",
      (FIELDFIT, "            if reach < farthest - slack and not (tie and reach >= tied - slack):\n", "            if reach < farthest - slack:\n")),
    m("M/sec26-pass-stops-at-farthest", "mask P5 sec26", "the tip pass stops at the tip-first field's reach (round 1's stop: a tie on a lattice reaching less is missed)",
      (FIELDFIT, "        if reach_top < tied - slack:\n", "        if reach_top < farthest - slack:\n")),
    m("M/sec26-false-takes-the-share", "mask P5 sec26", "tip_first false gives up taxels as true does (the 3 % share)",
      (FIELDFIT, '    return bool(options.get("tip_first", True)) and tip_on(options)\n', "    return tip_on(options)\n")),
    m("M/sec26-false-skips-the-step", "mask P5 sec26", "tip_first false skips the step (55ae8fe's order: no zero-cost ties, no metrics)",
      (FIELDFIT, '    return options.get("objective") != "max_area"\n', '    return bool(options.get("tip_first", True)) and options.get("objective") != "max_area"\n')),
    m("M/sec26-lead-reach-after-corners", "mask P5 sec26", "lead_rank puts the reach after the corner tolerance's count (a cornered field reaching farther no longer leads)",
      (FIELDFIT, "    return rank[:6] + (-tip_reach(candidate),) + rank[6:]\n", "    return rank[:7] + (-tip_reach(candidate),) + rank[7:]\n")),
    m("M/sec26-pass-no-centred", "mask P5 sec26", "the tip pass skips an asymmetric lead's centred phase (tri_a's 55 at 3.9 mm stays 0.58 mm short)",
      (FIELDFIT, "    if middle not in phases:\n        phases.append(middle)\n", "    if False:\n        phases.append(middle)\n")),
    m("M/sec26-pass-symmetric-no-centred", "mask P5 sec26", "the tip pass skips a symmetric lead's centred row phase (the equilateral's 342, the fin's 248 at 3 mm)",
      (FIELDFIT, "        if middle not in rows:\n            rows.append(middle)\n", "        if False:\n            rows.append(middle)\n")),
    m("M/sec26-pass-far-ignored", "mask P5 sec26", "the tip pass ignores the tails' reach (a field beyond the row the reach loop held the search to)",
      (FIELDFIT, "        far = None if search.reach is None else far_row(grid, search.reach)\n        for rows_cap, columns_cap in (rectangle_caps if full else shaped_caps):\n",
       "        far = None\n        for rows_cap, columns_cap in (rectangle_caps if full else shaped_caps):\n")),
    m("M/sec26-peel-fallback-removed", "mask P5 sec26", "a peeled tip-first field keeps the slot whatever it lost (below its floor, out of its lead)",
      (FIELDFIT, '        if peeled is not None and lead and not tip_peel_holds(candidate["tip"], peeled):\n', "        if False:\n")),
    m("M/sec26-peel-fallback-floor-only", "mask P5 sec26", "the peel fallback checks the floor only (a peel out of its lead or notched keeps the slot)",
      (FIELDFIT, '    return peeled["value"] >= tip["floor"] and tip_reach(peeled) >= tip["cut"] and (peeled["full"] or not tip["full"])\n',
       '    return peeled["value"] >= tip["floor"]\n')),
    # CAD mode without rectangles (the user's decision of 2026-10-26, P5-diagonal-bus.md section 26.16): a fit refuses
    # shape rectangle, the generic template and a rectangle preference; a saved placement naming them maps as fitted.
    m("M/sec26-cad-only-accepted", "mask P5 sec26.16", "a fit takes shape rectangle, the generic template and a rectangle preference silently (fitting the "
      "selected area as if they were not named)",
      (FIT, "        elif not fitted:\n", "        elif False:\n")),
    m("M/sec26-map-refuses-saved", "mask P5 sec26.16", "the map refuses a saved placement whose options name shape rectangle, the generic template or a "
      "rectangle preference (placements saved before section 26.16 no longer map)",
      (PLACE, '    options = parse_options(map_options(header.get("options", placement.get("options", {})), design), mapping=True)\n',
       '    options = parse_options(map_options(header.get("options", placement.get("options", {})), design))\n')),
    # Round 3c's review (P5-diagonal-bus.md section 26.17): the lead's zero-cost tie takes the lead's place, the displaced
    # field's rank and the taxels given are reported as documented, and a saved placement holds only what a fit accepted.
    m("M/sec26-tie-beside-the-lead", "mask P5 sec26.17", "the lead's tie no longer takes the lead's place: the lead is proposed after a tie of another "
      "readout too (round 3c: the right triangle's symmetric 272 on its hypotenuse pushed out of the five at 2.5 mm, 16 rows; "
      "since section 26.18 its leg's turned 160)",
      (FIELDFIT, '            placed[-1]["place"] = (id(lead), lead["value"])\n', "            pass\n")),
    m("M/sec26-tie-peel-holds", "mask P5 sec26.17", "a tie peeled under the lead's taxels is proposed in the lead's place (a tie gives up taxels; the lead follows it)",
      (FIELDFIT, '        if peeled is not None and candidate.get("tip_tie") and peeled["value"] < candidate["place"][1]:\n', "        if False:\n")),
    m("M/sec26-displaced-own-only", "mask P5 sec26.17", "metrics.tip.displaced names the displaced field's own proposal only (None where its tie took its place: "
      "round 3c's 376 of 738 tip-first fields on the 732 frames)",
      (FIELDFIT, "            tip[\"displaced\"] = None if root is None else places.get(root, ranks.get(root))\n",
       "            tip[\"displaced\"] = None if root is None else ranks.get(root)\n")),
    m("M/sec26-given-from-the-lead", "mask P5 sec26.17", "taxels_given counts from the displaced lead again (negative where the pass finds a larger field than the search)",
      (FIELDFIT, '            best["tip"] = dict(found, displaced=id(lead), given=found["most"] - best["value"])\n',
       '            best["tip"] = dict(found, displaced=id(lead), given=lead["value"] - best["value"])\n')),
    m("M/sec26-map-takes-any-saved-value", "mask P5 sec26.17", "the map takes any value of the removed options (shape circle, a preference of 500 %, a "
      "template object), not only what a fit accepted before section 26.16",
      (FIT, "        if mapping:\n            saved = SAVED_VALUES[key]\n", "        if mapping:\n            continue\n")),
    # The user's decisions of 2026-10-27: on a symmetric face the sensor is symmetric (section 26.17), unless a field that
    # breaks the symmetry holds at least 20 % more (section 26.19: SYMMETRY_GAIN, decided before the tip step, the rotation
    # with it); a symmetric group's tip share measured from its symmetric fields.
    m("M/sec26-symmetric-within-3-percent", "mask P5 sec26.19", "the threshold at section 22's 3 % again (the isosceles triangle's 341 on a leg "
      "before its base's symmetric 328, the 58 mm axis-hole plate's 500 before its symmetric 420)",
      (FIELDFIT, "SYMMETRY_GAIN = (120, 100)\n", "SYMMETRY_GAIN = (103, 100)\n")),
    m("M/sec26-symmetric-without-threshold", "mask P5 sec26.19", "every symmetric exit's best symmetric field first whatever another field holds "
      "(section 26.17's rule: the holed plates' symmetric 247 and 209 first again, not their turned 396 and 344)",
      (FIELDFIT, '    lead = by_tip(sorted((candidate for _, candidate in sorted(best.items()) if symmetric_leads(candidate["value"], most)),\n',
       '    lead = by_tip(sorted((candidate for _, candidate in sorted(best.items())),\n')),
    m("M/sec26-symmetric-threshold-boundary", "mask P5 sec26.19", "the symmetric field still leads a field that holds exactly 1.2 times its value "
      "(the lead's 20 % or more: at 20 % the other field leads)",
      (FIELDFIT, "    return symmetric * SYMMETRY_GAIN[0] > other * SYMMETRY_GAIN[1]\n", "    return symmetric * SYMMETRY_GAIN[0] >= other * SYMMETRY_GAIN[1]\n")),
    m("M/sec26-symmetric-threshold-after-tip", "mask P5 sec26.19", "the symmetric decision counts the tip's 3 %: taken on what the tip-first field "
      "may hold (97 % of the best symmetric field), not on the best symmetric field before the tip step (a symmetric 100 loses "
      "its lead to an asymmetric 119)",
      (FIELDFIT, '    lead = by_tip(sorted((candidate for _, candidate in sorted(best.items()) if symmetric_leads(candidate["value"], most)),\n',
       '    lead = by_tip(sorted((candidate for _, candidate in sorted(best.items()) if symmetric_leads(-(-candidate["value"] * TIP_SHARE[0] // TIP_SHARE[1]), most)),\n'),
      (FIELDFIT, '        if first is not None and id(first) not in placed and symmetric_leads(first["value"], top[candidate["order"]]):\n',
       '        if first is not None and id(first) not in placed and symmetric_leads(-(-first["value"] * TIP_SHARE[0] // TIP_SHARE[1]), top[candidate["order"]]):\n')),
    m("M/sec26-symmetric-never-turned", "mask P5 sec26.19", "an exit with a symmetric field is never turned (section 26.17's rule: the holed "
      "plates' sides unturned, their turned 396 and 344 not searched; the 59 mm axis-hole plate unturned)",
      (FIELDFIT, '            skipped = [order for order in sorted(mirrored) if symmetric_leads(max(c["value"] for c in mirrored[order]), best[order])]\n',
       "            skipped = sorted(mirrored)\n")),
    m("M/sec26-symmetric-share-from-all", "mask P5 sec26.17", "a symmetric group's tip share is measured from every field on its exit (round 3c: a "
      "symmetric field more than 3 % under an asymmetric one gives up nothing and never moves toward the tip)",
      (FIELDFIT, '    if lead.get("symmetric"):\n        same = [candidate for candidate in same if candidate.get("symmetric")]\n',
       '    if False:\n        same = [candidate for candidate in same if candidate.get("symmetric")]\n')),
    # Round 3c's review, its test gaps (section 26.17): T0's p / 8 slack, its ties of more taxels, the pass's floor within
    # the slack of the farthest reach.
    m("M/sec26-tie-slack-zero", "mask P5 sec26.17", "T0 is the farthest tie alone, no p / 8 slack (the taper's 20 x 13 at 3 mm with the 32x16 reader, "
      "not the denser 20 x 12 0.175 mm short)",
      (FIELDFIT, "    tie = min([candidate for candidate in ties if tip_reach(candidate) >= tied - slack], key=lead_rank)\n",
       "    tie = min([candidate for candidate in ties if tip_reach(candidate) >= tied], key=lead_rank)\n")),
    m("M/sec26-ties-equal-only", "mask P5 sec26.17", "T0 is of the fields with exactly the lead's taxels (tri_a's 8 x 6 = 48 under 12 rows, a tie with 6 "
      "more, not proposed with tip_first false)",
      (FIELDFIT, '    ties = [candidate for candidate in pool if candidate["value"] >= lead["value"]]\n',
       '    ties = [candidate for candidate in pool if candidate["value"] == lead["value"]]\n')),
    m("M/sec26-need-without-slack", "mask P5 sec26.17", "the pass runs a lattice at the floor only when it reaches the farthest reach itself (the "
      "disk's tip-first 16 x 23 = 318 under 16 rows, 0.05 mm short of it, missed: the 16 x 24 leads; the equilateral's 342 "
      "before section 26.18)",
      (FIELDFIT, '        need = floor if reach_top >= farthest - slack else lead["value"]\n', '        need = floor if reach_top >= farthest else lead["value"]\n')),
    # Round 4's review (P5-diagonal-bus.md section 26.18): every exit of the fit without the caps searched on its own under
    # them, a symmetric group's eighth row phases and its slack, the taxels given from the lead and its pass, the map on
    # the generic template, and the edges of the tie's place and peel (the verifier's MU4, MU19 and MU13).
    m("M/sec23-first-exit-alone", "mask P5 sec26.18", "only the first exit of the fit without the caps is searched on its own under them (round 4: the "
      "right triangle's hypotenuse prunes its legs' fields, two proposals under 12 rows)",
      (FIELDFIT, "            pending = own_exits(reference)\n", "            pending = own_exits(reference)[:1]\n")),
    m("M/sec23-own-exits-in-their-order", "mask P5 sec26.18", "the exits searched on their own go in their own order, not the fit's without the caps (the "
      "isosceles triangle's legs before its symmetric base under 12 rows)",
      (FIELDFIT, "            pending = own_exits(reference)\n", "            pending = sorted(own_exits(reference))\n")),
    m("M/sec23-own-exits-up-front", "mask P5 sec26.18", "every capped exit is searched on its own before the first field is built (the proposals the "
      "same, the work not: the fin under 32 rows searches its six exits, not two; the fin with reader auto 7.8 -> 25 s)",
      (FIELDFIT, "        if index == len(queue):\n            # The queue's end:", "        if index == len(queue) or pending:\n            # The queue's end:")),
    m("M/sec26-symmetric-tip-quarter-phases", "mask P5 sec26.18", "a symmetric group's tip pass takes the quarter row phases only (the isosceles "
      "triangle's tip-first 328 reaching 56.7 mm, not the 322 at 57.15 mm)",
      (FIELDFIT, "        rows += [round(k * pitch / TIP_ROW_PHASES, 6) for k in range(1, TIP_ROW_PHASES, 2)]\n", "")),
    m("M/sec26-symmetric-slack-eighth", "mask P5 sec26.18", "a symmetric group's slack is p / 8, a whole step of its row phases (the taper's 353 an "
      "eighth phase short of the farthest leads with 2 more taxels, not the 351)",
      (FIELDFIT, '    if lead.get("symmetric"):\n        slack = int(round(lead["pitch"] * 1e6)) // TIP_SYMMETRIC_SLACK\n', "")),
    m("M/sec26-given-from-the-exits-most", "mask P5 sec26.18", "taxels_given counts from the share's M again (the right triangle's 84 under 12 rows "
      "gives up 72, from its hypotenuse's symmetric 156 never in its place)",
      (FIELDFIT, '"most": max([lead["value"]] + [candidate["value"] for candidate in pool]),', '"most": max([most] + [candidate["value"] for candidate in pool]),')),
    m("M/sec26-map-takes-generic-fill", "mask P5 sec26.18", "the map takes on the generic template what a fit then refused (shape fill, containment "
      "field, more than 32 columns named: 88 of 9900 fuzzed option sets)",
      (FIT, '    if mapping and named.get("template") == "generic":\n', "    if False:\n")),
    m("M/sec26-tie-place-any-value", "mask P5 sec26.18", "a tip-first field that is the lead's tie takes the lead's place peeled under its taxels too "
      "(the disk's 24 x 23 lost behind the peeled 446; the verifier's MU4)",
      (FIELDFIT, '        if "place" in candidate and candidate["value"] >= candidate["place"][1]:\n', '        if "place" in candidate:\n')),
    m("M/sec26-tie-peel-check-on-tip-first", "mask P5 sec26.18", "the tie's peel check on a tip-first field that is the tie (its peel under the lead's "
      "taxels dropped though it still leads; the verifier's MU19)",
      (FIELDFIT, 'if peeled is not None and candidate.get("tip_tie") and peeled["value"] < candidate["place"][1]:',
       'if peeled is not None and "place" in candidate and peeled["value"] < candidate["place"][1]:')),
    m("M/sec26-tie-peel-equal-refused", "mask P5 sec26.18", "a tie's peel with exactly the lead's taxels gives the place back (tri_a's 7 x 6 = 42 "
      "under 12 rows; the verifier's MU13)",
      (FIELDFIT, 'peeled["value"] < candidate["place"][1]:\n            peeled = None  # a tie gives up no taxel',
       'peeled["value"] <= candidate["place"][1]:\n            peeled = None  # a tie gives up no taxel')),
)

# --------------------------------------------------------------------------
# CAD mode's border of the taxels (docs/CAD_BORDER.md, surface/border.py).
# --------------------------------------------------------------------------

BORDER_PY = "surface/border.py"

BORDER = (
    m("S/border-lattice-ignored", "CAD border", "the field fit's lattice ignores the border (its runs are not capped where a taxel square leaves it)",
      (FIELDFIT, '        if getattr(space, "border", None) is not None:\n            # The user\'s border (surface.border): a run\'s every taxel square inside it.\n',
       '        if False:\n            # The user\'s border (surface.border): a run\'s every taxel square inside it.\n')),
    m("S/border-record-not-required", "CAD border", "the map's taxels_inside_border record always passes (a taxel outside the border goes unnoticed)",
      (BORDER_PY, '        "passed": not found,\n', '        "passed": True,\n')),
    m("S/border-edge-wrong", "CAD border", "base.border_edge i is taken as the border's next edge (i + 1)",
      (BORDER_PY, '    side = edge_side(points, index, chart)\n    if not side["edges"]:\n        raise SurfaceError(CODE, f"Border edge {index} has no surface',
       '    side = edge_side(points, (index + 1) % n, chart)\n    if not side["edges"]:\n        raise SurfaceError(CODE, f"Border edge {index} has no surface')),
)

# --------------------------------------------------------------------------
# The EasyEDA Pro projects (docs/EASYEDA_EXPORT.md, exporters/easyeda_pro.py).
# --------------------------------------------------------------------------

EASYEDA_PY = "exporters/easyeda_pro.py"
COMPARE = "tools/compare_easyeda_gerbers.py"

EASYEDA = (
    m("X/easyeda-material", "EasyEDA export", "the stiffener material written as the format spec's 'PI' (EasyEDA Pro resets an unknown name to Polyimide)",
      (EASYEDA_PY, 'STIFFENER_MATERIALS = {"polyimide": "Polyimide"}', 'STIFFENER_MATERIALS = {"polyimide": "PI"}')),
    m("X/easyeda-thickness", "EasyEDA export", "the FPC_FILL thickness hard-coded to 0.2 mm instead of the profile's",
      (EASYEDA_PY, '"thickness": thickness, "path": [_ring_path(stiffener["points"])]', '"thickness": 0.2, "path": [_ring_path(stiffener["points"])]')),
    m("X/easyeda-net-dropped", "EasyEDA export", "the first pad of each footprint loses its net (PAD_NET)",
      (EASYEDA_PY, '{"partitionId": "", "padNet": pad["net"], "padLen": 0}', '{"partitionId": "", "padNet": pad["net"] if pad_number > 1 else "", "padLen": 0}')),
    m("X/easyeda-outline-layer", "EasyEDA export", "the board outline drawn on the Top Layer instead of the Board Outline Layer",
      (EASYEDA_PY, '"partitionId": "", "groupId": 0, "netName": "", "layerId": LAYER_OUTLINE,', '"partitionId": "", "groupId": 0, "netName": "", "layerId": LAYER_TOP,')),
    m("X/easyeda-coverlay-layer", "EasyEDA export", "the coverlay openings on the Bottom Solder Mask Layer",
      (EASYEDA_PY, "LAYER_TOP_COVERLAY = 5  #", "LAYER_TOP_COVERLAY = 6  #")),
    m("X/easyeda-fpc-mode", "EasyEDA export", "the stiffener layers 58 and 59 out of use (no FPC mode)",
      (EASYEDA_PY, "body.update(use=True, show=True)  # FPC mode", "body.update(use=False, show=False)  # FPC mode")),
    m("X/easyeda-pad-mask", "EasyEDA export", "the pads follow the solder-mask rule instead of a zero expansion",
      (EASYEDA_PY, '"topSolderExpansion": 0, "bottomSolderExpansion": 0, "topPasteExpansion": 0,', '"topSolderExpansion": None, "bottomSolderExpansion": None, "topPasteExpansion": 0,')),
    m("X/easyeda-track-pad-rule", "EasyEDA export", "the track-to-pad clearance from the contacts only (the electrodes, SMD pads too, forgotten)",
      (EASYEDA_PY, '"track_pad": min(required("pad_trace_clearance"), required("electrode_route_clearance")),', '"track_pad": required("pad_trace_clearance"),')),
    m("X/easyeda-rule-rounding", "EasyEDA export", "the design rules rounded to 1e-4 mil instead of floored (above our DRC's limit)",
      (EASYEDA_PY, "return _num(math.floor(float(millimetres) * MIL_PER_MM * 10000.0) / 10000.0)", "return _num(round(float(millimetres) * MIL_PER_MM, 4))")),
    m("X/easyeda-numbering", "EasyEDA export", "each placeholder reserves one number too many (element numbers no longer their ids)",
      (EASYEDA_PY, '{"dataType": data_type, "max": first})', '{"dataType": data_type, "max": first + 1})')),
    m("X/easyeda-deflate", "EasyEDA export", "the .epro2 members deflated (bytes depend on zlib)",
      (EASYEDA_PY, "                info.compress_type = ZIP_STORED\n                info.create_system = 3\n", "                info.compress_type = 8\n                info.create_system = 3\n")),
    m("X/easyeda-channel", "EasyEDA export", "the PCB components' Channel ID names the wrong schematic component",
      (EASYEDA_PY, '"Channel ID": f"$1e{index}"},', '"Channel ID": f"$1e{index + 1}"},')),
    m("X/easyeda-cutouts", "EasyEDA export", "the routed cutouts left out of the Board Outline Layer",
      (EASYEDA_PY, '        self.contours = [board["outline"]["points"], *board["outline"].get("cutouts", [])]\n', '        self.contours = [board["outline"]["points"]]\n')),
    m("X/easyeda-route", "EasyEDA export", "the HTTP route renamed (/api/export/easyeda)",
      (APP, 'EASYEDA_ROUTES = {"/api/export/easyeda-pro": "easyeda_pro_zip"}', 'EASYEDA_ROUTES = {"/api/export/easyeda": "easyeda_pro_zip"}')),
    m("X/easyeda-button", "EasyEDA export", "the web UI without its EasyEDA Pro download",
      ("web/index.html", '            <button type="button" data-export="easyeda-pro" disabled', '            <button type="button" data-export="easyeda" disabled')),
    m("X/easyeda-compare-outline", "EasyEDA export", "the comparison tool fills the outline from the outermost crossings (cutouts no longer holes)",
      (COMPARE, "    _pairs(segments, intervals)\n", "    _pairs({k: [min(xs), max(xs)] for k, xs in segments.items()}, intervals)\n")),
)

# --------------------------------------------------------------------------
# The sensor on the part beside the stacked view (the user's request of
# 2026-11-05): Gen by Surface's second figure, its gate and its art (the
# stdlib suite), and its geometry in web/cad/drape.js (the Playwright checks:
# tools/browser/mutants.py's "cad" kind kills both drape.js mutants with
# cad_checks.py part_on_part).  Its review of 2026-11-05: the checks' reads
# and its buffers (the stdlib suite), its antialiased outlines and its framing
# of a large part (the "cad" kind: part_on_part and part_crank_fill).  Its
# second review: the figure's cursor (the stdlib suite; its mutant of the
# split's room for the registration's caption went with the caption on
# 2026-11-06), and no seam round an outline over the part (the "cad" kind).  Its
# look of 2026-11-05 (the look lab's, merged): its own lights, the tone
# mapping, the studio's single warning and fallback, the edge bands drawn
# from the front, the contact shade made and drawn in Assembled only and the
# film's face not drawn there (the stdlib suite); the film no longer a flat
# black, the contact shade drawn at all and the edge bands drawn (the "cad"
# kind: part_on_part).  The look's fix round of 2026-11-05 (its review's
# minors): a lost context's objects dropped, not disposed, when it comes back
# (the stdlib suite, and the "cad" kind: part_on_part_studio's
# INVALID_OPERATION count), the measures out of the studio's try and guarded,
# a stack without a contact footprint looked for once a drawing (the stdlib
# suite, and the "cad" kind: part_on_part_patches), the shader edits' anchors
# in the vendored three.js (the stdlib suite), and the contact shade's core
# inside the footprint's edge on an edge facing the camera (the stdlib suite,
# and the "cad" kind: part_on_part_contact's shade along the WXAI sock's stack edge).
# The user's decision of 2026-11-05 (its Exploded home the left figure's as
# it opens): the home's tilt the left's, its spin's sign, the camera's up the
# stack's normal and the arrow keys' sense the left's (the stdlib suite:
# test_surface_web; the "cad" kind kills the last three with part_on_part's
# comparison with the left figure).
# The 3D view in the same light (the user's request of 2026-11-05): the
# figure's lights, studio, tone mapping and warnings moved to web/cad/studio.js
# (the figure drawing the same pixels), whose mutants above now edit it; the
# 3D view's part in the studio, its markers unlit, the studio made once a
# renderer and again (never disposed) when a lost context comes back, its
# reads with ?probe only and a drag's diffuse material on a software
# renderer only (the stdlib suite, and tools/browser/mutants.py's "cad" kind:
# cad_checks part_view_look).
# --------------------------------------------------------------------------

DRAPE = "web/cad/drape.js"
ONPART = "web/cad/onpart.js"
STUDIO = "web/cad/studio.js"
VIEWER = "web/cad/viewer.js"
ON_PART = (
    m("M/web-on-part-gate", "2026-11-05", "styles.css: the sensor on the part not hidden outside Gen by Surface (Rectangular mode shows an empty second figure)",
      ("web/styles.css", ".stack-figure.is-on-part { display:none; }", ".stack-figure.is-on-part { display:block; }")),
    m("M/web-board-art-listener", "2026-11-05", "app.js: no answer to fpc:board-art (the sensor on the part never gets the boards' art)",
      (WEB, '  document.addEventListener("fpc:board-art", event => { if (event.detail) event.detail.result = boardArt(event.detail); });\n', "")),
    m("F/on-part-mirror", "2026-11-05", "browser: the top FPC laid on the part unmirrored (its copper side's art as if seen from outside)",
      (DRAPE, "  const bx = isTop(art) ? ox + (Rx + Rw - sx) : ox + (sx - Rx);\n", "  const bx = isTop(art) ? ox + (sx - Rx) : ox + (sx - Rx);\n"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    m("F/on-part-texture-rows", "2026-11-05", "browser: the boards' art upside down on their sheets (the texture's rows not flipped)",
      (DRAPE, "  return [(sx - vx) / vw, 1 - (sy - vy) / vh];\n", "  return [(sx - vx) / vw, (sy - vy) / vh];\n"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    m("M/web-on-part-probe-gate", "2026-11-05 review", "main.js: the sensor on the part compared with the map on every page, not with ?probe only",
      (CAD_MAIN, "const metrics = ON_PART_PROBE ? D.metrics(stack, plan.map, result.boards) : {};", "const metrics = D.metrics(stack, plan.map, result.boards);")),
    m("M/web-on-part-buffers", "2026-11-05 review", "onpart.js: Exploded / Assembled gives each sheet a new position attribute (its old GL buffer left to the garbage collector)",
      (ONPART, "      attribute.copyArray(view.mode === \"assembled\" ? sheet.assembled : sheet.positions);\n",
       "      geometry.setAttribute(\"position\", new THREE.BufferAttribute(view.mode === \"assembled\" ? sheet.assembled : sheet.positions, 3));\n")),
    m("F/on-part-coverage", "2026-11-05 review", "browser: the sheets' alpha test not turned into coverage (their outlines in hard steps)",
      (ONPART, "function coverage(material) {\n  material.alphaToCoverage = true;\n", "function coverage(material) {\n  return material;\n  material.alphaToCoverage = true;\n"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    m("F/on-part-framing", "2026-11-05 review", "browser: the part framed within 1.3 times the sheets' radius again (the crank's tip runs off the pane)",
      (DRAPE, "export const PART_FRAME_SHARE = 3;\n", "export const PART_FRAME_SHARE = 1.3;\n"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    m("M/web-on-part-cursor", "2026-11-05 review 2", "onpart.js: OrbitControls' inline cursor left at auto (no grab over the figure)",
      (ONPART, '  controls.cursorStyle = "grab";\n', "")),
    m("F/on-part-seams", "2026-11-05 review 2", "browser: the sheets' coverage alpha written as it is (the pane seen through every outline over the part)",
      (ONPART, "  Object.assign(material, {blending: THREE.CustomBlending,", "  Object.assign(material, {blending: THREE.NormalBlending,"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    m("M/web-on-part-tone", "2026-11-05 look", "studio.js: ACES filmic tone mapping instead of Khronos PBR Neutral (the art's colours shifted; the 3D view's too)",
      (STUDIO, "  renderer.toneMapping = THREE.NeutralToneMapping;\n", "  renderer.toneMapping = THREE.ACESFilmicToneMapping;\n")),
    m("M/web-on-part-warn-once", "2026-11-05 look", "studio.js: the look's fallbacks warn on every shader compiled, not once a cause",
      (STUDIO, "    warned.add(key);\n", "")),
    m("M/web-on-part-studio-fallback", "2026-11-05 look", "studio.js: the studio made without half-float render targets (no fallback to the lights alone)",
      (STUDIO, '    if (!(extensions.has("EXT_color_buffer_float") || extensions.has("EXT_color_buffer_half_float"))) {\n', "    if (false) {\n")),
    m("M/web-on-part-bands-side", "2026-11-05 look", "onpart.js: the film's edge band drawn from both sides (its far wall over the stack)",
      (ONPART, "roughness: FILM_LOOK.roughness, side: THREE.FrontSide})", "roughness: FILM_LOOK.roughness, side: THREE.DoubleSide})")),
    m("M/web-on-part-contact-lazy", "2026-11-05 look", "onpart.js: the contact shade's footprint made on every drawing, Exploded too (34-55 ms of JS for a view not shown)",
      (ONPART, '    if (view.contact !== null || view.mode !== "assembled" || !view.sheets || !PATCHES.contact) return;\n',
       "    if (view.contact !== null || !view.sheets || !PATCHES.contact) return;\n")),
    m("M/web-on-part-contact-mode", "2026-11-05 look", "onpart.js: the contact shade drawn in Exploded too, once Assembled has made it",
      (ONPART, '    if (view.mode === "assembled" && view.contact && !view.shadeOff) contact', "    if (view.contact && !view.shadeOff) contact")),
    m("M/web-on-part-film-face", "2026-11-05 look", "onpart.js: the film's face drawn assembled, under both boards (8-17 ms a frame on SwiftShader for nothing)",
      (ONPART, '    if (film) film.children[0].visible = view.mode !== "assembled";\n', "    if (film) film.children[0].visible = true;\n")),
    m("M/web-on-part-restore-dispose", "2026-11-05 fixes", "onpart.js: the lost context's studio disposed when the context comes back (its GL objects deleted in the new one: INVALID_OPERATION)",
      (ONPART, "    look.environment = studioFor(renderer);\n    clear({lost: true});\n",
       "    look.environment?.dispose();\n    look.environment = studioFor(renderer);\n    clear({lost: true});\n")),
    m("M/web-on-part-restore-sheets", "2026-11-05 fixes", "onpart.js: the lost context's sheets and part disposed when the context comes back (INVALID_OPERATION in the new one)",
      (ONPART, "    clear({lost: true});\n", "    clear();\n")),
    m("M/web-on-part-measure-in-try", "2026-11-05 fixes", "studio.js: the studio's measure inside its build's try again (a measure that throws throws away the studio made)",
      (STUDIO, "      target = studio(renderer);\n    } catch (error) {", "      target = studio(renderer);\n      performance.measure?.(studied, {start: started});\n    } catch (error) {")),
    m("M/web-on-part-measure-unguarded", "2026-11-05 fixes", "studio.js: a measure unguarded (User Timing Level 3's options throw in an older browser, through show() and setMode())",
      (STUDIO, "  try {\n    performance.measure?.(name, {start: started});\n  } catch {\n    // No measure; nothing else lost.\n  }\n",
       "  performance.measure?.(name, {start: started});\n")),
    m("M/web-on-part-contact-none", "2026-11-05 fixes", "onpart.js: a stack without a contact footprint has it looked for again at every Assembled (35-60 ms of JS each time)",
      (ONPART, '    if (view.contact !== null || view.mode !== "assembled"', '    if (view.contact || view.mode !== "assembled"')),
    m("M/web-on-part-anchor", "2026-11-05 fixes", "onpart.js: the contact shade's anchor in three.js's text misspelt (no shade, and a warning, on every visitor's page)",
      (ONPART, '["#include <opaque_fragment>", `if ( contactStrength', '["#include <opaque_fragment >", `if ( contactStrength')),
    m("M/web-on-part-contact-inner", "2026-11-05 fixes", "onpart.js: the contact shade's core outside the footprint only again (the WXAI sock's light line between the stack's edge and its shade)",
      (ONPART, "Math.max(0, core[t] - Math.min(cover[t], inner[t]))", "Math.max(0, core[t] - cover[t])")),
    m("M/web-on-part-contact-facing", "2026-11-05 fixes", "onpart.js: the core inside the footprint on every edge, those facing away too (the part seen past them darkened, beside the wrap's knuckle)",
      (ONPART, "				core *= mix( 1.0, smoothstep( 0.0, 1e-3, dot( outward, cameraPosition.xy - vContactWorld.xy ) ), inside );\n", "")),
    m("M/web-on-part-contact-turned", "2026-11-05 fixes", "onpart.js: the core's band inside the footprint round the cells turned from the normal too (a dark frame beside the wrap's knuckle)",
      (ONPART, "  const inner = eroded(cover, width, height, Math.max(1, Math.round(CONTACT.innerMm * k)));\n  for (let t = 0; t < cover.length; t += 1) if (!Number.isFinite(lift[t])) cover[t] = 0;\n",
       "  for (let t = 0; t < cover.length; t += 1) if (!Number.isFinite(lift[t])) cover[t] = 0;\n  const inner = eroded(cover, width, height, Math.max(1, Math.round(CONTACT.innerMm * k)));\n")),
    m("M/web-on-part-home-left", "2026-11-05 alignment", "drape.js: the sensor on the part's Exploded home tilted its own way, not as the left figure opens (app.js ORBIT_HOME)",
      (DRAPE, "export const HOME_TILT_DEG = 57;\n", "export const HOME_TILT_DEG = 50;\n")),
    m("M/web-on-part-home-spin", "2026-11-05 alignment", "drape.js: the Exploded home turned the other way about the stack's normal (the spin's sign: the left figure's mirror image)",
      (DRAPE, "  return [Math.sin(spin) * Math.sin(tilt), -Math.cos(spin) * Math.sin(tilt), Math.cos(tilt)];\n",
       "  return [-Math.sin(spin) * Math.sin(tilt), -Math.cos(spin) * Math.sin(tilt), Math.cos(tilt)];\n")),
    m("M/web-on-part-camera-up", "2026-11-05 alignment", "onpart.js: the camera's up the world's y again (the left figure's roll out of reach, a drag turning about the field's y)",
      (ONPART, "  camera.up.set(...HOME_UP);\n", "  camera.up.set(0, 1, 0);\n")),
    m("M/web-on-part-keys", "2026-11-05 alignment", "onpart.js: the arrow keys turning the figure the other way from the left figure's (OrbitControls' own sense)",
      (ONPART, "    const turn = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1]}[event.key];\n",
       "    const turn = {ArrowLeft: [1, 0], ArrowRight: [-1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1]}[event.key];\n")),
    m("F/on-part-film-flat", "2026-11-05 look", "browser: the film a flat unlit black again (it reads as a hole cut in the stack)",
      (ONPART, "coverage(new THREE.MeshPhysicalMaterial({color: new THREE.Color(...rgb), map, alphaTest: ALPHA_TEST, side: THREE.DoubleSide, ...film,\n"
       "    sheenColor: new THREE.Color(...sheenRGB)}))",
       "coverage(new THREE.MeshBasicMaterial({color: new THREE.Color(...rgb), map, alphaTest: ALPHA_TEST, side: THREE.DoubleSide}))"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    m("F/on-part-contact-never", "2026-11-05 look", "browser: the contact shade never drawn (no line where the stack meets the part)",
      (ONPART, "strength: [0.85, 0.4], most: 0.85};", "strength: [0, 0], most: 0.85};"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    m("F/on-part-bands-off", "2026-11-05 look", "browser: the layers' edge bands not drawn (each sheet a paper-thin face again)",
      (ONPART, "    if (band?.geometry) {\n", "    if (false) {\n"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
    # The 3D view in the studio's light (2026-11-05; tests/test_surface_web.py, and the "cad" kind's part_view_look).
    m("M/web-view-own-lights", "2026-11-05 view look", "viewer.js: the 3D view's old lights again (a hemisphere and a sun) in place of the studio's",
      (VIEWER, "  camera.up.set(0, 0, 1);\n  const lights = studioLights(scene, camera);\n",
       "  camera.up.set(0, 0, 1);\n  scene.add(new THREE.HemisphereLight(0xffffff, 0x8899aa, 1.7));\n  const sun = new THREE.DirectionalLight(0xffffff, 1.3);\n"
       "  sun.position.set(0.3, 0.6, 1);\n  camera.add(sun);\n  scene.add(camera);\n  const lights = {place() {}, turn() {}};\n")),
    m("M/web-view-tone", "2026-11-05 view look", "viewer.js: the 3D view without the tone mapping (the studio's lights clip its faces toward the key)",
      (VIEWER, "  toneMap(renderer);\n  renderer.domElement.className = \"cad-canvas\";\n", "  renderer.domElement.className = \"cad-canvas\";\n")),
    m("M/web-view-markers-lit", "2026-11-05 view look", "viewer.js: the markers tone mapped (the border, the taxels and the handles off their own colours)",
      (VIEWER, "const markerMaterial = parameters => new THREE.MeshBasicMaterial({...parameters, toneMapped: false});",
       "const markerMaterial = parameters => new THREE.MeshBasicMaterial({...parameters});")),
    m("M/web-view-studio-per-model", "2026-11-05 view look", "viewer.js: the studio made again with each model (a PMREM render target per load, the last ones never disposed)",
      (VIEWER, "    const mesh = new THREE.Mesh(geometry, partMaterial(look));\n",
       "    look.environment = studioFor(renderer);\n    const mesh = new THREE.Mesh(geometry, partMaterial(look));\n")),
    m("M/web-view-restore-dispose", "2026-11-05 view look", "viewer.js: the lost context's studio disposed when it comes back (its GL objects deleted in the new one)",
      (VIEWER, "    look.environment = studioFor(renderer);\n    if (groups.mesh)",
       "    look.environment?.dispose();\n    look.environment = studioFor(renderer);\n    if (groups.mesh)")),
    m("M/web-view-restore-none", "2026-11-05 view look", "viewer.js: the studio not made again when a lost context comes back (the part mirrors a lost render target: black)",
      (VIEWER, "    look.environment = studioFor(renderer);\n    if (groups.mesh) groups.mesh.userData.look.envMap = look.environment?.texture || null;\n", "")),
    m("M/web-view-probe-gate", "2026-11-05 view look", "viewer.js: the 3D view's reads of its pixels without ?probe too (a render and a gl.readPixels each)",
      (VIEWER, "    if (!probe || !groups.mesh) return null;\n", "    if (!groups.mesh) return null;\n")),
    m("M/web-view-drag-everywhere", "2026-11-05 view look", "viewer.js: a drag's diffuse material on a GPU too (the look's reflections gone while turning, for nothing)",
      (VIEWER, "  dragMaterial = SOFTWARE_RENDERER.test(info.renderer) ? diffuseMaterial() : null;\n", "  dragMaterial = diffuseMaterial();\n")),
    # The film's own lamp (the user's of 2026-11-05, 再调一下你说的黑色压阻膜: tests/test_surface_web.py, and the "cad"
    # kind's part_on_part with the film's satin check at discriminating levels again).
    m("M/web-on-part-film-lamp-anchor", "2026-11-05 film", "onpart.js: the film's lamp's anchor in three.js's text misspelt (the film nearly a flat black again, and a warning, on every visitor's page)",
      (ONPART, '["#include <lights_fragment_end>", `{', '["#include <lights_fragment_end >", `{')),
    m("F/on-part-film-unlit", "2026-11-05 film", "browser: the film's own lamp out (at the left figure's home it mirrors the room between the softboxes: nearly a flat black)",
      (ONPART, "const FILM_LAMP = {aim: 1.5, out: 0.3, intensity: 0.2};", "const FILM_LAMP = {aim: 1.5, out: 0.3, intensity: 0};"),
      expect="survive", reason="out of scope: browser behaviour, checked by the Playwright scripts in tools/browser, not by the stdlib suite"),
)

MUTANTS = AUDIT + ENGINE + API + EXPORT + TESTS_AND_DOCS + GOLD_FINGERS + SURFACE + MASKED_FIELD + DIAGONAL + FIELD_FIT + BORDER + EASYEDA + ON_PART


# The Library's writer (tools/library_write.py, the user's requests of 2026-11-05): the request the page sends for each
# sensor and the product rules on its proposal #1, which tests/test_library.py checks on the committed fits.
LIBRARY_WRITE = "tools/library_write.py"
LIBRARY = (
    m("S/library-unit", "2026-11-05 Library", "the Library's writer sends a unit (the page sends none: its Auto unit, the engine's guess)",
      (LIBRARY_WRITE, '    request = {"name": part["mesh"]["name"][:200], "selection"',
       '    request = {"name": part["mesh"]["name"][:200], "unit": "mm", "selection"'), killers=("test_library.",)),
    m("S/library-numbers", "2026-11-05 Library", "the Library's writer keeps integral floats (20.0, which the browser writes 20)",
      (LIBRARY_WRITE, "    if isinstance(value, float) and value.is_integer():\n        return int(value)\n",
       "    if isinstance(value, float) and value.is_integer():\n        return value\n"), killers=("test_library.",)),
    m("S/library-tails-rule", "2026-11-05 Library", "the Library's product rules let tails off the centre of the base edge through",
      (LIBRARY_WRITE, '    if bus.get("tail_position") != "centred":\n', "    if False:\n"), killers=("test_library.",)),
    m("S/library-symmetry-rule", "2026-11-05 Library", "the Library's product rules let an off-centre sensor on a symmetric face through",
      (LIBRARY_WRITE, '    if symmetry.get("face") and not symmetry.get("field"):\n', "    if False:\n"), killers=("test_library.",)),
    m("S/library-round6", "2026-11-05 Library", "the Library's writer takes a base point that main.js choosePoint rounds (round6): the page would send another request",
      (LIBRARY_WRITE, "        if [round6(value) for value in point] != point:\n", "        if False:\n"), killers=("test_library.",)),
)
MUTANTS += LIBRARY
# The Library's page (2026-11-05): the site build's gate, the generator's ./?part, app.py's route.
LIBRARY_PAGE = (
    m("S/library-gate-reply", "2026-11-05 Library", "the site build publishes a Library sensor whose committed reply the engine no longer gives",
      ("tools/build_static_site.py", '    if reply != document["reply"] or not proposals or proposals[0]["build_id"] != variant["build_id"]:\n',
       '    if not proposals or proposals[0]["build_id"] != variant["build_id"]:\n'), killers=("test_library.",)),
    m("S/library-gate-request", "2026-11-05 Library", "the site build publishes a Library sensor whose fit's request the page no longer sends",
      ("tools/build_static_site.py", '    if library_write.canonical(document["request"]) != sent:\n', "    if False:\n"), killers=("test_library.",)),
    m("S/library-own-file", "2026-11-05 Library", "the user's own file keeps a Library sensor's ?part and options",
      (CAD_MAIN, "  if (!isDefault) leaveLibrary();  // the user's own file: a Library sensor's ?part and options go\n", ""), killers=("test_library.",)),
    m("S/library-route", "2026-11-05 Library", "app.py no longer serves library.html",
      (APP, '"/library.html": "library.html"}', '}'), killers=("test_library.",)),
)
MUTANTS += LIBRARY_PAGE
# The Library's tapered tips (2026-11-05): a family of parts as one card on its shelf's part.
LIBRARY_TAPERS = (
    m("S/library-family-grid", "2026-11-05 Library", "the Library's writer takes a family whose grid misses or adds a choice of its axes",
      (LIBRARY_WRITE, '    if sorted(record["grid"]) != sorted(keys):\n', "    if False:\n"), killers=("test_library.",)),
    m("S/library-family-start", "2026-11-05 Library", "a family's parts get entries of their own in entries.json's start (each gripper's default)",
      (LIBRARY_WRITE, "        if part_id in grippers:\n            document[\"start\"].append(default)\n",
       "        document[\"start\"].append(default)\n"), killers=("test_library.",)),
    m("S/library-tip-label", "2026-11-05 Library", "a tapered tip's file note names the part's title and pitch, not the tip",
      (LIBRARY_WRITE, '    return part.get("label") or f"{part[\'title\']}, {js_string(variant[\'pitch_mm\'])} mm"\n',
       '    return f"{part[\'title\']}, {js_string(variant[\'pitch_mm\'])} mm"\n'), killers=("test_library.",)),
)
MUTANTS += LIBRARY_TAPERS
# The Library's minors, fixed on the integration of 2026-11-05 (fpc-library merged into fpc-stack-on-part): the options
# leaveLibrary puts back, ./?part=<family>, the deny-list (the writer's, which the private importer takes: a
# mutant's file is public, since the public copy's CI runs --check), the UMI shelf's one-line heading.  Since the
# shelves' one wording (the user's decision of 2026-11-05) the writer has no branch for a shelf with families, so
# S/library-shelf-family (that branch off: the long range on the UMI shelf too) is retargeted to its regression: the
# two wordings again, the long range on every shelf without a family.
LIBRARY_MINORS = (
    m("S/library-options-written-only", "2026-11-05 integration", "the generator records only the Library options it wrote, so a restored form keeps them after the user's own file",
      (CAD_MAIN, "    if (!same(control.value)) control.value = value;\n    if (!same(controlDefault(control))) changed[control.id] = control.value;\n",
       "    if (!same(control.value)) { control.value = value; changed[control.id] = control.value; }\n"), killers=("test_library.",)),
    m("S/library-family-part", "2026-11-05 integration", "the generator's ./?part takes no family id (./?part=umi-tapers opens the UMI finger with a warning)",
      (CAD_MAIN, "index.parts[id].default\n      : Object.hasOwn(index.families || {}, id) ? index.families[id].default : \"\";",
       "index.parts[id].default : \"\";"), killers=("test_library.",)),
    m("S/library-deny-list", "2026-11-05 integration", "the Library's deny-list (the writer's, which the private importer takes) lacks an xArm split mesh the test's has",
      (LIBRARY_WRITE, '    "a61abac9746d0319a6e6ab82ba27a7d16afe6f303bc2bac863449b05c27c0661": "xArm (finger_l.stl)",\n', ""), killers=("test_library.",)),
    m("S/library-shelf-family", "2026-11-05 integration", "the shelf headings in two wordings again: 'from fine 1 mm to coarse 3 mm' on a shelf without a family, the range on the UMI finger's",
      (LIBRARY_WRITE, '    else:\n        text = f"{count} pitches, {js_string(pitches[0])} to {js_string(pitches[-1])} mm"\n',
       '    elif families:\n        text = f"{count} pitches, {js_string(pitches[0])} to {js_string(pitches[-1])} mm"\n'
       '    else:\n        text = f"{count} pitches, from fine {js_string(pitches[0])} mm to coarse {js_string(pitches[-1])} mm"\n'), killers=("test_library.",)),
)
MUTANTS += LIBRARY_MINORS
# The Library's polish of 2026-11-05 (the user's decisions of that day): a sensor's picture 3:1 in one column, so Open
# is in a 390 x 844 phone's first screen ("可压扁", it may be squashed), and one wording for every shelf heading, its
# families after the range ("最好统一", best unified).
LIBRARY_POLISH = (
    m("S/library-detail-shot", "2026-11-05 polish", "a sensor's picture 16:10 below 900 px again (the Tapered tips' Open 88 px below a 390 x 844 phone's first screen)",
      ("web/library.css", "@media (max-width:899px) { .lib-shot-detail { aspect-ratio:3 / 1; } }\n", ""), killers=("test_library.",)),
    m("S/library-shelf-families-unsaid", "2026-11-05 polish", "a shelf closing with families leaves them out of its heading (the UMI shelf's tapered tips unsaid)",
      (LIBRARY_WRITE, "    for family in families:\n        text += f\", and {family['title'].lower()}\"\n", ""), killers=("test_library.",)),
)
MUTANTS += LIBRARY_POLISH
# The 3D views' light (2026-11-05: the user's "the new light on every 3D view"; app.js lightBoard, lightView, styles.css
# .board-light, .board-shadow): the numbers app.js copies from web/cad/studio.js (the lights and the studio, onpart.js's
# until the merge of 2026-11-05) and web/cad/onpart.js (the coverlay, the edge bands; a classic script cannot import
# them), the sweep's tints from the coverlay's, nothing on the views' 3D elements that flattens them, the veils' paths the
# outline less its cutouts; each killed by test_surface_web alone on a scratch copy (tools/browser/mutants.py's
# part_view_light mutants see the light itself).
CSS = "web/styles.css"
VIEW_LIGHT = (
    m("M/web-view-light-key", "2026-11-05 views' light", "app.js: the 3D views' key light brighter than the sensor on the part's (the two figures lit apart)",
      (WEB, "    key: {at: [-0.5, 0.65, 0.55], intensity: 1.25},\n", "    key: {at: [-0.5, 0.65, 0.55], intensity: 1.5},\n")),
    m("M/web-view-light-softbox", "2026-11-05 views' light", "app.js: the key's softbox dimmer in the 3D views' studio than in the sensor on the part's",
      (WEB, "      {at: [-0.49, 0.78, 0.39], size: [6, 4], radiance: 1.2},   // key\n", "      {at: [-0.49, 0.78, 0.39], size: [6, 4], radiance: 1},     // key\n")),
    m("M/web-view-light-band", "2026-11-05 views' light", "app.js: the walls' shade not the sensor on the part's edge bands' (BAND.shade)",
      (WEB, "  const VIEW_BAND_SHADE = 0.82;\n", "  const VIEW_BAND_SHADE = 0.9;\n")),
    m("M/web-view-light-tint", "2026-11-05 views' light", "styles.css: the sweep in Photo a white veil, not tinted toward the art's amber",
      (CSS, 'body[data-look="photo"] .look-scope svg.board-light { --sheen:#ffbc90; }', 'body[data-look="photo"] .look-scope svg.board-light { --sheen:#ffffff; }')),
    m("M/web-view-light-flatten", "2026-11-05 views' light", "styles.css: an opacity on the stacked boards' faces (each flattened into one picture, its other side lost)",
      (CSS, ".assembly-face { position:relative; width:100%; height:100%; transform-style:preserve-3d; backface-visibility:visible; }",
       ".assembly-face { position:relative; width:100%; height:100%; transform-style:preserve-3d; backface-visibility:visible; opacity:.99; }")),
    m("M/web-view-light-outline-twice", "2026-11-05 views' light", "app.js: outlineRings deaf to its selector (the cutouts' rings the outline's again: an even-odd veil of one ring twice paints nothing)",
      (WEB, "    return [...(group?.querySelectorAll(`:scope > ${selector}`) || [])].map(polygon => {\n",
       '    return [...(group?.querySelectorAll(":scope > .outline") || [])].map(polygon => {\n')),
    m("M/web-view-light-unclipped", "2026-11-05 views' light", "app.js: the light's paths over their whole view box (the veils and the shadow painted outside the board)",
      (WEB, '      const d = rings.map(ring => `M${ring.map(([x, y]) => `${round6(x)} ${round6(y)}`).join("L")}Z`).join("");\n',
       '      const d = `M${box[0]} ${box[1]}h${box[2]}v${box[3]}h${-box[2]}Z`;\n')),
)
MUTANTS += VIEW_LIGHT
# The Library's pictures (the user's request of 2026-11-05: the cards show the finger with the sensor on it):
# tools/browser/library_shots.py shoots them into web/library/shots/, the writer's pictures() reads its manifest
# (entries.json's "image"), the site build's gate refuses a picture of another fit; tests/test_library.py's fixture of
# two tiny WebPs kills each.
LIBRARY_SHOTS = (
    m("S/library-picture-other-fit", "2026-11-05 pictures", "the Library pictures a sensor with a shot of another fit (the wrong sensor pictured)",
      (LIBRARY_WRITE, '        if (shot.get("fit_sha256"), shot.get("build_id")) != (variant["fit_sha256"], variant["build_id"]):\n',
       "        if False:\n"), killers=("test_library.",)),
    m("S/library-picture-sources-error", "2026-11-05 pictures", "a picture of older figure sources refused, not a warning (the public CI, which runs no browser, fails on every change of the figure)",
      (LIBRARY_WRITE, '        if shot.get("figure_sha256") != figure:\n            older.append(identifier)\n',
       '        if shot.get("figure_sha256") != figure:\n            problems.append((identifier, f"{identifier}: {RESHOOT}"))\n'), killers=("test_library.",)),
    m("S/library-picture-bytes", "2026-11-05 pictures", "a picture whose bytes are not the manifest's taken (only its WebP header read)",
      (LIBRARY_WRITE, "            if (record.get(\"path\"), record.get(\"bytes\"), record.get(\"sha256\")) != (relative, len(data), hashlib.sha256(data).hexdigest()):\n",
       "            if False:\n"), killers=("test_library.",)),
    m("S/library-picture-alpha", "2026-11-05 pictures", "a WebP of the extended layout read as having alpha whatever its flag (a picture on an opaque background taken)",
      (LIBRARY_WRITE, '        return 1 + int.from_bytes(body[4:7], "little"), 1 + int.from_bytes(body[7:10], "little"), bool(body[0] & 0x10)\n',
       '        return 1 + int.from_bytes(body[4:7], "little"), 1 + int.from_bytes(body[7:10], "little"), True\n'), killers=("test_library.",)),
    m("S/library-image-card", "2026-11-05 pictures", "entries.json's image names the 1280 x 800 Exploded picture as the grid's card (four times the card's pixels)",
      (LIBRARY_WRITE, '"card": files["card"][0], "width": SHOT_SIZE[0]', '"card": files["exploded"][0], "width": SHOT_SIZE[0]'), killers=("test_library.",)),
    m("S/library-gate-pictures", "2026-11-05 pictures", "the site build publishes the pictures of another fit (its gate's pictures unchecked)",
      ("tools/build_static_site.py", "    if unpictured:\n        raise BuildError(f\"the library's pictures are stale", "    if False:\n        raise BuildError(f\"the library's pictures are stale"),
      killers=("test_library.",)),
)
MUTANTS += LIBRARY_SHOTS
# The Library's pictures of 2026-11-05 (the user's request: the cards show the finger and the sensor on it, the
# generator's on-part figure): the contract's card file lazily and sized on the cards, the placeholder for a picture
# that does not load, and a sensor's page's Exploded | Assembled control (named for a screen reader, Exploded on each
# page opened, the phone's page tighter with it so Open stays in the first screen).  library_checks part_pictures and
# part_first_screen see each in the browser.
LIBRARY_JS = "web/library.js"
LIBRARY_PICTURES = (
    m("S/library-picture-eager", "2026-11-05 pictures", "the cards' pictures load at once, every card's as the page opens (not lazily)",
      (LIBRARY_JS, '      loading: kind === "detail" ? null : "lazy"});', "      loading: null});"), killers=("test_library.",)),
    m("S/library-picture-unsized", "2026-11-05 pictures", "a picture without its width and height (its box sized only when it arrives)",
      (LIBRARY_JS, 'el("img", {src: BASE + src, width, height, alt:', 'el("img", {src: BASE + src, alt:'), killers=("test_library.",)),
    m("S/library-picture-card-full", "2026-11-05 pictures", "the cards load the 1280 x 800 Exploded picture, not its 640 x 400 card file",
      (LIBRARY_JS, 'image?.[view]?.src : image?.exploded?.card;', 'image?.[view]?.src : image?.exploded?.src;'), killers=("test_library.",)),
    m("S/library-picture-broken", "2026-11-05 pictures", "a picture whose file does not load stays a broken image (no placeholder)",
      (LIBRARY_JS, "      shown.replaceWith(field(variant));\n      missed?.(view);\n", "      missed?.(view);\n"), killers=("test_library.",)),
    m("S/library-view-unnamed", "2026-11-05 pictures", "the Exploded | Assembled control without its legend (a screen reader hears two radios of no group)",
      (LIBRARY_JS, 'el("fieldset", {className: "lib-view"}, el("legend", {}, "View"),', 'el("fieldset", {className: "lib-view"},'), killers=("test_library.",)),
    m("S/library-view-kept", "2026-11-05 pictures", "a sensor's page opened anew keeps the view of the page before (Assembled where Exploded opens)",
      (LIBRARY_JS, "    state.picture = VIEWS[0][0];\n    setNote(\"\");", "    setNote(\"\");"), killers=("test_library.",)),
    m("S/library-view-phone-room", "2026-11-05 pictures", "the phone's page not tighter with the view control (the Tapered tips' Open 25 px below a 390 x 844 first screen)",
      ("web/library.css", "@media (max-width:899px) { .lib-detail:has(.lib-view) { padding-top:16px; } .lib-detail:has(.lib-view) .lib-detail-body { margin-top:12px; gap:16px; }\n"
       "  .lib-detail:has(.lib-view) .lib-info { gap:12px; } }\n", ""), killers=("test_library.",)),
)
MUTANTS += LIBRARY_PICTURES
# The Library's grid of 2026-11-06 (the user's requests: the grippers once each, four to a row, each card naming its
# pitches; the UMI finger's shelf alone, after the grippers' section): the shelved parts, a family's shelf, the back
# link, the columns and where they turn, the restore on Back against a back link, the history's mark, the order; each
# killed alone on a scratch copy by test_library (PageTests' grid pins); library_checks part_layout, part_grid and
# part_routes see each in the browser.
LIBRARY_GRID = (
    m("S/library-grid-shelves", "2026-11-06 grid", "every gripper on a shelf of its own again (the grippers' section empty)",
      (LIBRARY_JS, 'const SHELVED = ["umi-finray"];',
       'const SHELVED = ["umi-finray", "franka-hand", "widowx-250", "trossen-widowx-ai", "arx-x5", "i2rt-yam", "unitree-dex1", "makermods-metal"];'),
      killers=("test_library.",)),
    m("S/library-grid-family-shelf", "2026-11-06 grid", "a part a family closes gets no shelf unless SHELVED names it (its family's card unreachable)",
      (LIBRARY_JS, "const isShelved = part => SHELVED.includes(part) || familiesOf(part).length > 0;", "const isShelved = part => SHELVED.includes(part);"),
      killers=("test_library.",)),
    m("S/library-grid-back-shelf", "2026-11-06 grid", "a gripper's page's back link at #shelf-<part> (the older address, not its card)",
      (LIBRARY_JS, 'el("a", {className: "lib-back", href: `#${placeOf(home)}`}', 'el("a", {className: "lib-back", href: `#shelf-${home}`}'),
      killers=("test_library.",)),
    m("S/library-grid-three", "2026-11-06 grid", "the grippers three to a row (3 + 3 + 1)",
      ("web/library.css", ".lib-cards { display:grid; grid-template-columns:repeat(4,minmax(0,1fr));", ".lib-cards { display:grid; grid-template-columns:repeat(3,minmax(0,1fr));"),
      killers=("test_library.",)),
    m("S/library-grid-767", "2026-11-06 grid", "the grippers two to a row below 768 px, not 735 px (wider than the UMI shelf's cards from 735 to 767 px)",
      ("web/library.css", "@media (max-width:734px) { .lib-cards {", "@media (max-width:767px) { .lib-cards {"), killers=("test_library.",)),
    m("S/library-grid-wrong-card", "2026-11-06 grid", "a back link restores the grid with the card that opened the page focused, whichever card it names",
      (LIBRARY_JS, "(traversed || !target || target.contains(state.opener))", "(traversed || !target || true)"), killers=("test_library.",)),
    m("S/library-grid-history", "2026-11-06 grid", "Back and Forward not told from a link (the history entries unmarked)",
      (LIBRARY_JS, "const traversed = history.state?.library === true;", "const traversed = false;"), killers=("test_library.",)),
    m("S/library-grid-umi-first", "2026-11-06 grid", "the UMI finger's shelf before the grippers' section again",
      (LIBRARY_JS, "      ...(parts.length ? [grippers(parts)] : []),\n      ...shelvedParts().map(part => shelf(`shelf-${part}`, `${index.parts[part].title}.`, index.parts[part].shelf, index.parts[part].variants, familiesOf(part))));\n",
       "      ...shelvedParts().map(part => shelf(`shelf-${part}`, `${index.parts[part].title}.`, index.parts[part].shelf, index.parts[part].variants, familiesOf(part))),\n      ...(parts.length ? [grippers(parts)] : []));\n"),
      killers=("test_library.",)),
)
MUTANTS += LIBRARY_GRID
# The pictures served by app.py (the merge of 2026-11-05 of the shots tool and the Library's display): image/webp under
# nosniff, not the host's mimetypes' guess; test_library's RouteTests kills it.
LIBRARY_SERVED = (
    m("S/library-picture-type", "2026-11-05 pictures", "app.py: the Library's pictures sent as the host's mimetypes guesses (application/octet-stream under nosniff here)",
      (APP, '                ".webp": "image/webp"}\n', "                }\n"), killers=("test_library.",)),
)
MUTANTS += LIBRARY_SERVED
# The Library's set of pictures (2026-11-05, shot once on the integration with the approved look): every sensor
# pictured, which tools/library_write.py --check wants (test_library on a copy of the Library with one shot gone), and
# each drawing centred in its picture by the shots tool (frameView balances only the axis that binds).
LIBRARY_SHOT_SET = (
    m("S/library-picture-required", "2026-11-05 pictures", "library_write --check passes a sensor with no picture (the Library's card falls back to the field's drawing unnoticed)",
      (LIBRARY_WRITE, "    unshot = [identifier for identifier, image in images.items() if image is None and identifier not in broken]\n",
       "    unshot = []\n"), killers=("test_library.",)),
    m("S/library-shot-uncentred", "2026-11-05 pictures", "the shots tool leaves each drawing where frameView put it (the UMI finger 72 px left of the card's middle)",
      ("tools/browser/library_shots.py", "    return (right - left) // 2, (bottom - top) // 2\n", "    return 0, 0\n"), killers=("test_library.",)),
)
MUTANTS += LIBRARY_SHOT_SET
# The Library's 3D view (the user's requests of 2026-11-05: the grippers drawn whole, each sensor's page a 3D view to
# turn; docs/LIBRARY_VIEW.md): the writer's checks of each record's art and a gripper's stage (pictures()), of the
# grippers' scenes (scenes()), entries.json's view and the alt text of a whole gripper, and Gen by Surface's figure as it
# was (main.js passing no stage, onpart.js's homes hook) and library.js loading the view on a sensor's page only; each
# killed alone on a scratch copy by test_library (test_surface_web for main.js and onpart.js), the writer's on the tiny
# scenes and art it builds.
LIBRARY_VIEW = (
    m("S/library-view-art-build", "2026-11-05 3D view", "an art drawn from another build (or of another sensor) taken: the wrong boards on a sensor's page",
      (LIBRARY_WRITE, '    if (record.get("build_id"), document.get("id"), document.get("build_id")) != (variant["build_id"], identifier, variant["build_id"]):\n',
       "    if False:\n"), killers=("test_library.",)),
    m("S/library-view-art-bytes", "2026-11-05 3D view", "an art file whose bytes are not the record's taken (only its document compared)",
      (LIBRARY_WRITE, '    if (record.get("bytes"), record.get("sha256")) != (len(data), hashlib.sha256(data).hexdigest()):\n', "    if False:\n"),
      killers=("test_library.",)),
    m("S/library-view-unrecorded", "2026-11-05 3D view", "a record without its art accepted once the 3D view is required (a sensor page with no 3D view after the shoot)",
      (LIBRARY_WRITE, '        elif require_view:\n            broken.append(f"no 3D view: its record names no art: {fix}")\n',
       '        elif False:\n            broken.append(f"no 3D view: its record names no art: {fix}")\n'), killers=("test_library.",)),
    # The shoot of 2026-11-06 wrote every sensor's art and each gripper's stage and set VIEW_REQUIRED.
    m("S/library-view-transition", "2026-11-06 shoot", "the 3D view no longer required after the shoot (a record without its art, or a gripper's without its stage, pictured with no 3D view: a warning, not refused)",
      (LIBRARY_WRITE, "\nVIEW_REQUIRED = True\n", "\nVIEW_REQUIRED = False\n"), killers=("test_library.",)),
    m("S/library-view-scene-hash", "2026-11-05 3D view", "a gripper's stage of another scene taken (its scene_sha256 not compared: a picture of the old scene)",
      (LIBRARY_WRITE, '    if stage.get("scene_sha256") != scene_sha256(data, rules):\n', "    if False:\n"), killers=("test_library.",)),
    m("S/library-view-rules-hash", "2026-11-05 3D view", "the rules left out of scene_sha256 (a picture shot under other homes, explode or see-through taken)",
      (LIBRARY_WRITE, "             f\"{hashlib.sha256(canonical_json(rules).encode('ascii')).hexdigest()}  rules\\n\")\n", '             "")\n'),
      killers=("test_library.",)),
    m("S/library-view-older-error", "2026-11-05 3D view", "a picture of older 3D view modules refused, not a warning (the public CI, which runs no browser, fails on every change of the view)",
      (LIBRARY_WRITE, '            if shot.get("view_sha256") != view and identifier not in older:\n                older.append(identifier)\n',
       '            if shot.get("view_sha256") != view and identifier not in older:\n                problems.append((identifier, f"{identifier}: {RESHOOT}"))\n'),
      killers=("test_library.",)),
    m("S/library-view-rule", "2026-11-05 3D view", "a gripper's recorded stage numbers unchecked (a stack hidden by the other finger, or the stacks touching, taken)",
      (LIBRARY_WRITE, '    found = [f"its stage breaks a rule of {SCENES_INDEX}: {message}: {fix}"\n'
                      '             for message in stage_problems(stage.get("numbers"), rules.get("checks") or {}, see_through, rules.get("explode_stacks"))]\n',
       "    found = []\n"),
      killers=("test_library.",)),
    # The user's decision of 2026-11-06 (one stack exploded, the sensor finger's; the near finger see-through in both
    # views, its stack assembled): the new checks of the stage's numbers and the rules' two keys.
    m("S/library-view-stacks-floor", "2026-11-06 one explode", "the exploded stack's floor in mm to the other finger's stack unchecked (a small gripper's stacks 2 mm apart taken)",
      (LIBRARY_WRITE, '             ("clearance_mm.stacks", clearance.get("stacks"), ">=", "stacks_apart_min_mm", checks.get("stacks_apart_min_mm")),\n', ""),
      killers=("test_library.",)),
    m("S/library-view-screen-apart", "2026-11-06 one explode", "the two stacks' silhouettes apart on screen unchecked (I2RT's near stack and exploded top touching in the picture taken)",
      (LIBRARY_WRITE, '             ("stacks_apart_px", numbers["stacks_apart_px"], ">=", "stacks_apart_min_px", checks.get("stacks_apart_min_px"))]\n',
       "             ]\n"), killers=("test_library.",)),
    m("S/library-view-near-seen", "2026-11-06 one explode", "the near stack's share seen unchecked (the roles swapped, or the near stack hidden, taken)",
      (LIBRARY_WRITE, '        rules.append(("near_seen", numbers["near_seen"], ">=", "near_seen_min", checks.get("near_seen_min")))\n', "        pass\n"),
      killers=("test_library.",)),
    m("S/library-view-near-seen-null", "2026-11-06 one explode", "a near_seen taken with the mate's stack exploding too (a number where the record must say null)",
      (LIBRARY_WRITE, '            found.append(f"near_seen is {numbers[\'near_seen\']}, with the mate\'s stack exploding")\n', "            pass\n"),
      killers=("test_library.",)),
    m("S/library-view-explode-rules", "2026-11-06 one explode", "scenes.json's explode_stacks and see_through_modes unchecked (no sensor stack exploding, or an unknown mode, taken)",
      (LIBRARY_WRITE, '    if not (isinstance(stacks, list) and all(isinstance(name, str) for name in stacks) and len(set(stacks)) == len(stacks)\n'
                      '            and "sensor" in stacks and set(stacks) <= set(FINGERS)):\n', "    if False:\n"),
      (LIBRARY_WRITE, '    if not (isinstance(modes, list) and modes and all(isinstance(mode, str) for mode in modes) and len(set(modes)) == len(modes)\n'
                      '            and set(modes) <= set(CAMERA_MODES)):\n', "    if False:\n"),
      killers=("test_library.",)),
    m("S/library-view-umi-stage", "2026-11-05 3D view", "a stage recorded for the UMI finger or a tapered tip taken (their fingertip scene)",
      (LIBRARY_WRITE, "        if stage is not None and scene is None:\n", "        if False:\n"), killers=("test_library.",)),
    m("S/library-view-mirror-kind", "2026-11-05 3D view", "a scene's mate kind not its matrix's determinant (a mirror pair said to carry the same board)",
      (LIBRARY_WRITE, '        elif mate["kind"] != ("turned" if determinant(mate["matrix"]) > 0 else "mirror"):\n', "        elif False:\n"),
      killers=("test_library.",)),
    m("S/library-view-mesh-hash", "2026-11-05 3D view", "a scene's bodies not checked against their files (SHA-256, bytes, triangles)",
      (LIBRARY_WRITE, '        if (body["sha256"], body["bytes"], body["triangles"]) != (digest, len(data), stl_triangles(data)):\n', "        if False:\n"),
      killers=("test_library.",)),
    m("S/library-view-part-pin", "2026-11-05 3D view", "a scene drawn about another mesh of its part taken (part_mesh_sha256 unchecked)",
      (LIBRARY_WRITE, '    if document["part_mesh_sha256"] != parts["parts"][part_id]["mesh"]["sha256"]:\n', "    if False:\n"), killers=("test_library.",)),
    m("S/library-view-denied", "2026-11-05 3D view", "the deny-list not applied to the scenes' bodies (the MakerMods body, not cleared, could be committed)",
      (LIBRARY_WRITE, "        if digest in DENIED_SHA256 or DENIED_NAME.search(mesh):\n", "        if False:\n"), killers=("test_library.",)),
    m("S/library-view-alt", "2026-11-05 3D view", "a whole gripper's picture described as 'on the part' (its alt text not its scene's words)",
      (LIBRARY_WRITE, "            \"alt\": f\"{label_text} {picture or 'on the part'}\"}", "            \"alt\": f\"{label_text} on the part\"}"),
      killers=("test_library.",)),
    m("S/library-view-entry", "2026-11-05 3D view", "entries.json's view written for a sensor whose art is stale (its problems reported, its view kept)",
      (LIBRARY_WRITE, "            broken += art_problems(identifier, variant, art, library)\n",
       '            problems += [(identifier, f"{identifier}: {message}") for message in art_problems(identifier, variant, art, library)]\n'),
      killers=("test_library.",)),
    m("M/web-on-part-stage-main", "2026-11-05 3D view", "main.js: Gen by Surface's figure made with a stage (its homes and scene no longer drape.js's alone)",
      (CAD_MAIN, "{onViewChange: renderState, onContext: onPartContext, probe: ON_PART_PROBE});",
       "{onViewChange: renderState, onContext: onPartContext, probe: ON_PART_PROBE, stage: (internals, figure) => figure});"),
      killers=("test_surface_web.",)),
    m("S/library-view-lazy", "2026-11-05 3D view", "library.js: the 3D view's module (and three.js) loaded as the page loads, on the grid too, not on a sensor's page",
      (LIBRARY_JS, "const live = {host: null, view: null, load: null,", 'const live = {host: null, view: null, load: import("./cad/library_view.js"),'),
      killers=("test_library.",)),
    m("M/web-on-part-stage-home", "2026-11-05 3D view", "onpart.js: each mode's home drape.js's whatever a stage sets (the Library's grippers at the fingertip's angles)",
      ("web/cad/onpart.js", "  const homeVector = () => new THREE.Vector3(...(view.homes?.[view.mode] || homeDirection(view.mode)));\n",
       "  const homeVector = () => new THREE.Vector3(...homeDirection(view.mode));\n"), killers=("test_surface_web.",)),
)
MUTANTS += LIBRARY_VIEW
# The look light by default and dark on the header's toggle (the user's request of 2026-11-06, web/theme.js; its review
# of the same day): the page dark unless light is stored, a dark rule outranking more than it did under the system's
# scheme, the toggle's state unsaid, a page following the system's scheme by a color-scheme meta, another tab's clear()
# ignored; each killed alone by test_web_theme (ThemeToggleTests) on a scratch copy; theme_checks part_toggle sees the
# first, the third and the last in the browser.
THEME_JS = "web/theme.js"
THEME_TOGGLE = (
    m("M/web-theme-default-dark", "2026-11-06 theme", "theme.js: the page dark unless light is stored (a first visit, or one with cleared storage, opens dark)",
      (THEME_JS, '      return window.localStorage.getItem(THEME_KEY) === "dark" ? "dark" : "light";',
       '      return window.localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark";'), killers=("test_web_theme.",)),
    m("M/web-theme-hook-specificity", "2026-11-06 theme", "library.css: a dark rule on :root[data-theme] without :where() (it outranks the light rules it did not beat under the system's scheme)",
      ("web/library.css", ':where(:root[data-theme="dark"]) .lib .lib-card:hover {', ':root[data-theme="dark"] .lib .lib-card:hover {'),
      killers=("test_web_theme.",)),
    m("M/web-theme-no-pressed", "2026-11-06 theme", "theme.js: the toggle's aria-pressed never set (a screen reader hears Dark mode off in dark)",
      (THEME_JS, '    button.setAttribute("aria-pressed", String(theme === "dark"));\n', ""), killers=("test_web_theme.",)),
    m("M/web-theme-system-meta", "2026-11-06 theme", "index.html: a color-scheme meta of light and dark (a light visitor's first frame and form controls dark on a dark system)",
      ("web/index.html", '    <meta name="viewport" content="width=device-width, initial-scale=1" />\n',
       '    <meta name="viewport" content="width=device-width, initial-scale=1" />\n    <meta name="color-scheme" content="light dark" />\n'),
      killers=("test_web_theme.",)),
    m("M/web-theme-clear-ignored", "2026-11-06 theme", "theme.js: another tab's clear() of the storage ignored (this tab stays dark with nothing stored)",
      (THEME_JS, "    if (event.key === THEME_KEY || event.key === null) show(stored());", "    if (event.key === THEME_KEY) show(stored());"),
      killers=("test_web_theme.",)),
)
MUTANTS += THEME_TOGGLE
# A browser without Element.checkVisibility (the review of 2026-11-06: iOS and iPadOS before 17.4, where every build had
# failed in both modes): app.js's call unguarded again, and fitScene's clearance of the controls failing the build; each
# killed alone by test_surface_web (FigureControlsTests) on a scratch copy; cad_checks part_older_browser sees both in
# the browser.
OLDER_BROWSER = (
    m("M/web-check-visibility-unguarded", "2026-11-06 review", "app.js: boardDrawing calls Element.checkVisibility unguarded (every build fails where the browser lacks it)",
      (WEB, '[...svg.querySelectorAll(".outline, .view-label")].filter(rendered).map(node => {',
       '[...svg.querySelectorAll(".outline, .view-label")].filter(node => node.checkVisibility()).map(node => {'), killers=("test_surface_web.",)),
    m("M/web-fit-scene-throws", "2026-11-06 review", "app.js: an error of fitScene's clearance of the controls fails the build (no plain fit to fall back on)",
      (WEB, '    } catch (error) {\n      svg.style.paddingTop = "";\n      fit = fitWindow(svg, own);\n    }\n',
       "    } catch (error) {\n      throw error;\n    }\n"), killers=("test_surface_web.",)),
)
MUTANTS += OLDER_BROWSER
# The Library opened at an address of its own (the reviews of 2026-11-06): the grid's title painted before the sensor's
# page (theme.js's mark gone), the footer hidden for good (route()'s opened() gone); each killed alone by test_library
# (PageTests) on a scratch copy; library_checks part_routes sees both in the browser.
LIBRARY_PLACE = (
    m("S/library-place-unmarked", "2026-11-06 review", "theme.js: the Library opened at an address of its own unmarked (a frame of the grid's title over the footer before the sensor's page)",
      (THEME_JS, """  if (location.hash.length > 1 && document.querySelector('meta[name="flexitac-page"][content="library"]')) root.dataset.libPlace = "";\n""", ""),
      killers=("test_library.",)),
    m("S/library-place-kept", "2026-11-06 review", "library.js: the first route no longer clears the mark (the footer, its trademark line and its licences, hidden on every page opened at its address)",
      (LIBRARY_JS, "    if (!state.index) return;\n    opened();\n", "    if (!state.index) return;\n"), killers=("test_library.",)),
)
MUTANTS += LIBRARY_PLACE
# A card or a sample's tile Tabbed to that its scroller shows in part (the review of 2026-11-06): left cut, its scroller's
# focusin gone; each killed alone by test_library (PageTests) or test_samples (SampleScriptTests) on a scratch copy;
# library_checks part_layout and sample_checks part_keys see them in the browser.
TAB_REVEAL = (
    m("S/library-row-reveal", "2026-11-06 review", "library.js: a card Tabbed to that its row shows in part left cut (the row not moved to it)",
      (LIBRARY_JS, "      if (shift) track.scrollBy({left: shift});\n", ""), killers=("test_library.",)),
    m("M/web-sample-reveal", "2026-11-06 review", "main.js: a sample's tile Tabbed to that the palette's scroller shows in part left cut (no focusin)",
      (CAD_MAIN, '  document.querySelector("#samplePalette .sample-grid")?.addEventListener("focusin", revealTile);\n', ""),
      killers=("test_samples.",)),
)
MUTANTS += TAB_REVEAL
# A sample and the user's own file loaded with no face selected and nothing built, only the default UMI finger's (and a
# Library sensor's ?part) built at once (the user's request of 2026-11-06, "测试用的sensor,不要托进去之后直接就生成好了,
# 包括新拖进去的cad,不要直接显示哪个面被选择"): a sample's largest flat face selected and its sensor generated as it loads,
# and the user's own file's largest flat face selected as it loads; each killed alone by test_samples (SampleScriptTests)
# on a scratch copy; sample_checks part_drag sees the first and cad_checks part_one_step the second in the browser.  Its
# review: the build of the part before shown below a model loaded (its Gerber ZIPs ready), killed alone by test_samples
# on a scratch copy, sample_checks' sample_ok seeing it in the browser.
NO_AUTO = (
    m("M/web-sample-built-at-once", "2026-11-06 samples", "main.js: a sample dropped or pressed has a face selected and its sensor generated at once again",
      (CAD_MAIN, "    sampleAddress(id);\n    libraryNote();\n  } catch (error) {",
       "    sampleAddress(id);\n    libraryNote();\n    const face = cad.inspect.candidates?.flat?.[0];\n"
       "    if (face) { await autoSelect(face.seed_facet, face.preset || \"flat\"); await oneStep(); }\n  } catch (error) {"),
      killers=("test_samples.",)),
    m("M/web-file-largest-face", "2026-11-06 samples", "main.js: the user's own file has its largest flat face selected as it loads again (quick mode)",
      (CAD_MAIN, ". Click the face the sensor goes on.`);\n  }\n",
       ". Click the face the sensor goes on.`);\n    const face = reply.candidates?.flat?.[0];\n"
       "    if (quickMode() && !cad.defaultFile && face && !cad.facetMismatch) await autoSelect(face.seed_facet, face.preset || \"flat\");\n  }\n"),
      killers=("test_samples.",)),
    m("M/web-results-of-another-part", "2026-11-06 samples", "main.js: the build of the part before shown below a model loaded, its Gerber ZIPs ready (a sample dropped after the default part's build)",
      (CAD_MAIN, "  const shown = !cad.newPart && (cad.generated || cad.lastResult?.design?.template_id === SURFACE_TEMPLATE_ID);",
       "  const shown = cad.generated || cad.lastResult?.design?.template_id === SURFACE_TEMPLATE_ID;"),
      killers=("test_samples.",)),
)
MUTANTS += NO_AUTO
# The verification of 2026-11-06's small findings: the stacked card's last row square at its rounded foot, a shelf's card
# Tabbed to without room round it in the window, the phone's row of samples of two heights, the runner's default timeout
# below one run of the suite again; each killed alone on a scratch copy by the test named; cad_checks part_stack_feet,
# library_checks part_layout and sample_checks part_phones see the first three in the browser.
VERIFY_MINORS = (
    m("M/web-stack-foot-square", "2026-11-06 verification", "styles.css: the stacked card's last row square at its rounded foot (the figures' gradient's corners standing out of it)",
      (CSS, '.stack-figure.is-registration > .stacked-canvas,body[data-mode="cad"] .stack-figure.is-on-part > .stacked-canvas '
       "{ border-radius:0 0 var(--stack-foot,7px) var(--stack-foot,7px); }\n", ""), killers=("test_surface_web.",)),
    m("S/library-shelf-card-margin", "2026-11-06 verification", "library.css: a shelf's card Tabbed to without room round it in the window (at 390 px its focus ring cut at the window's bottom)",
      ("web/library.css", ".lib-track > .lib-card { scroll-margin:16px 0; }\n", ""), killers=("test_library.",)),
    m("M/web-sample-row-heights", "2026-11-06 verification", "styles.css: the phone's row of samples of two heights again (a two-line name's tile 32 px, the others 30 px)",
      (CSS, "  .sample-grid > li { display:flex; }\n  .sample-grid .sample { min-height:34px; padding-top:3px; padding-bottom:3px; }\n", ""),
      killers=("test_samples.",)),
    m("T/doc-suite-timeout", "2026-11-06 verification", "mutation_check.py: the default --timeout 900 s again, below one run of the suite (every mutant KILLED by its timeout)",
      ("tools/mutation_check.py", "\nSUITE_TIMEOUT = 5400.0\n", "\nSUITE_TIMEOUT = 900.0\n"), killers=("test_docs_consistency.",)),
)
MUTANTS += VERIFY_MINORS


# --------------------------------------------------------------------------
# Runner.
# --------------------------------------------------------------------------

_CATALOGUE_TEST = "HandoffTests.test_every_catalogue_edit_still_applies"
_FAILURE = re.compile(r"^(FAIL|ERROR): (\S+) \(([^)\s]*)\)", re.M)
_CACHES = shutil.ignore_patterns("__pycache__", "*.pyc", ".git")


def _ignored(directory: str, names: list) -> set:
    """What the scratch copy leaves out: caches, .git and the outputs a run wrote, but outputs/.gitkeep, which is
    committed and which test_static_site's public export asks for (the review of 2026-11-06: without it the baseline
    failed in every run and each kill read as a false alarm)."""

    left_out = set(_CACHES(directory, names))
    if Path(directory) == PROJECT / "outputs":
        left_out |= {name for name in names if name != ".gitkeep"}
    return left_out


def _problems(mutant: Mutant) -> list[str]:
    """Edits that no longer apply exactly once to the project."""

    problems = []
    texts: dict[str, str] = {}
    for path, old, new in mutant.edits:
        source = PROJECT / path
        if not source.is_file():
            problems.append(f"{path} does not exist")
            continue
        text = texts.setdefault(path, source.read_text(encoding="utf-8"))
        count = text.count(old)
        if count != 1:
            problems.append(f"{path}: the old text occurs {count} times")
        else:
            texts[path] = text.replace(old, new)
    return problems


def _prepare(directory: Path, mutant: Mutant | None) -> Path:
    copy = directory / "project"
    shutil.copytree(PROJECT, copy, ignore=_ignored)
    # The CI workflow sits beside the project, at the repository root; a document test reads it.
    if WORKFLOW.is_file():
        (directory / WORKFLOW.parent.relative_to(PROJECT.parent)).mkdir(parents=True)
        shutil.copy2(WORKFLOW, directory / WORKFLOW.relative_to(PROJECT.parent))
    if mutant is not None:
        for path, old, new in mutant.edits:
            target = copy / path
            target.write_text(target.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")
    return copy


def _run_suite(copy: Path, python: str, timeout: float, mutant_id: str | None = None) -> dict:
    environment = dict(os.environ, PYTHONPATH=str(copy), PYTHONDONTWRITEBYTECODE="1")
    environment.pop("PYTHONSTARTUP", None)
    environment.pop("FPC_MUTANT", None)
    if mutant_id is not None:
        # The suite's catalogue check skips itself here: this copy carries one edit on purpose.
        environment["FPC_MUTANT"] = mutant_id
    start = time.monotonic()
    try:
        completed = subprocess.run(
            [python, "-B", "-m", "unittest", "discover", "-s", "tests"],
            cwd=copy, env=environment, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "seconds": round(time.monotonic() - start, 1), "failed": [], "summary": f"timed out after {timeout:g} s"}
    output = completed.stderr
    failed = []
    for _, method, qualified in _FAILURE.findall(output):
        name = qualified if qualified.endswith("." + method) else f"{qualified}.{method}"
        if name not in failed:
            failed.append(name)
    lines = [line for line in output.splitlines() if line.startswith(("Ran ", "OK", "FAILED"))]
    return {"returncode": completed.returncode, "seconds": round(time.monotonic() - start, 1), "failed": failed, "summary": " ".join(lines[-2:])}


def _evaluate(mutant: Mutant | None, work: Path, python: str, timeout: float, keep: bool) -> dict:
    directory = Path(tempfile.mkdtemp(prefix="mutant-", dir=work))
    try:
        outcome = _run_suite(_prepare(directory, mutant), python, timeout, None if mutant is None else mutant.id)
    finally:
        if not keep:
            shutil.rmtree(directory, ignore_errors=True)
    if mutant is None:
        return {"id": "baseline", **outcome, "status": "PASSED" if outcome["returncode"] == 0 else "FAILED"}
    killed = outcome["returncode"] != 0  # a timeout (None) is a kill as well
    stray = [name for name in outcome["failed"] if mutant.killers and not name.startswith(mutant.killers)]
    # The suite's catalogue check skips itself in a mutated copy (FPC_MUTANT); if it failed there,
    # the handshake is broken and the kill says nothing about the mutant.
    stray += [name for name in outcome["failed"] if name.endswith(_CATALOGUE_TEST) and name not in stray]
    if killed and stray:
        status = "KILLED (false alarm)"
    elif killed:
        status = "KILLED" if mutant.expect == "killed" else "KILLED (expected to survive)"
    else:
        status = "SURVIVED (expected)" if mutant.expect == "survive" else "SURVIVED"
    return {
        "id": mutant.id, "origin": mutant.origin, "description": mutant.description, "expect": mutant.expect,
        "reason": mutant.reason, "status": status, **outcome,
    }


def _against_baseline(result: dict, base: dict) -> dict:
    """A kill whose failing tests all fail in the unmutated copy too says nothing about its mutant (a mutant without
    killers has no stray filter): it is reported SURVIVED (baseline failures only), never KILLED."""

    if base["status"] == "PASSED" or not result["status"].startswith("KILLED") or result["returncode"] is None:
        return result
    if result["failed"] and all(name in base["failed"] for name in result["failed"]):
        return dict(result, status="SURVIVED (baseline failures only)")
    return result


def _select(mutants: Sequence[Mutant], prefixes: Sequence[str]) -> list[Mutant]:
    if not prefixes:
        return list(mutants)
    return [mutant for mutant in mutants if any(mutant.id == prefix or mutant.id.startswith(prefix) for prefix in prefixes)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="+", default=[], metavar="ID", help="mutant ids or id prefixes (e.g. audit/ T/doc)")
    parser.add_argument("--list", action="store_true", help="print the catalogue and exit")
    parser.add_argument("--check", action="store_true", help="only check that every edit still applies")
    parser.add_argument("--jobs", type=int, default=max(1, min(16, (os.cpu_count() or 2) // 2)), help="parallel suite runs")
    parser.add_argument("--python", default=sys.executable, help="interpreter for the suite (default: this one)")
    parser.add_argument("--timeout", type=float, default=SUITE_TIMEOUT, help=f"seconds per suite run (default {SUITE_TIMEOUT:g})")
    parser.add_argument("--work", type=Path, default=None, help="scratch directory (default: the system temp directory)")
    parser.add_argument("--keep", action="store_true", help="keep the mutated copies")
    parser.add_argument("--json", type=Path, default=None, help="write the results as JSON")
    args = parser.parse_args(argv)

    selected = _select(MUTANTS, args.only)
    if not selected:
        parser.error("no mutant matches --only")
    if args.list:
        for mutant in selected:
            flag = "" if mutant.expect == "killed" else f"  [expected to survive: {mutant.reason}]"
            print(f"{mutant.id:28s} {mutant.origin:18s} {mutant.description}{flag}")
        print(f"{len(selected)} mutants")
        return 0
    ids = [mutant.id for mutant in MUTANTS]
    duplicates = sorted({identifier for identifier in ids if ids.count(identifier) > 1})
    stale = [(mutant.id, problem) for mutant in selected for problem in _problems(mutant)]
    if duplicates or stale:
        for identifier in duplicates:
            print(f"DUPLICATE ID {identifier}")
        for identifier, problem in stale:
            print(f"STALE {identifier}: {problem}")
        return 2
    if args.check:
        print(f"all {len(selected)} mutants apply")
        return 0

    if args.work is not None:
        args.work.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="fpc-mutation-", dir=args.work))
    print(f"{len(selected)} mutants, {args.jobs} jobs, {args.python}; scratch {work}", flush=True)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        baseline = pool.submit(_evaluate, None, work, args.python, args.timeout, args.keep)
        futures = [pool.submit(_evaluate, mutant, work, args.python, args.timeout, args.keep) for mutant in selected]
        base = baseline.result()
        print(f"baseline: {base['status']} ({base['summary']}, {base['seconds']} s)", flush=True)
        results = []
        for future in futures:
            result = _against_baseline(future.result(), base)
            results.append(result)
            failing = ", ".join(result["failed"][:2]) + (f" (+{len(result['failed']) - 2})" if len(result["failed"]) > 2 else "")
            print(f"{result['status']:28s} {result['id']:28s} {result['seconds']:6.1f} s  {failing or result['summary']}", flush=True)
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)

    killed = [result for result in results if result["status"].startswith("KILLED") and result["status"] != "KILLED (false alarm)"]
    expected_survivors = [result for result in results if result["status"] == "SURVIVED (expected)"]
    unexpected = [result for result in results if result["status"] in ("SURVIVED", "KILLED (false alarm)", "SURVIVED (baseline failures only)")]
    scored = len(results) - len(expected_survivors)
    print()
    print(f"baseline {base['status']}; {len(killed)}/{len(results)} killed; "
          f"{len(killed)}/{scored} of the mutants expected to be killed "
          f"({100.0 * len(killed) / max(1, scored):.1f}%); {len(unexpected)} unexpected result(s); "
          f"{time.monotonic() - started:.0f} s")
    for result in expected_survivors:
        print(f"  expected survivor {result['id']}: {result['reason']}")
    for result in unexpected:
        print(f"  UNEXPECTED {result['status']} {result['id']}: {result['description']}")
    if args.json is not None:
        args.json.write_text(json.dumps({"baseline": base, "results": results}, indent=1), encoding="utf-8")
    if base["status"] != "PASSED":
        return 2
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
