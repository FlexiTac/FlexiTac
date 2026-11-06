"""CAD mode's field-only containment (fit option ``containment: field``, masked-field phases P5d and P5e).

Only the taxel field F (the crossing region P and its 0.5 mm margin) must
lie on the selected surface; the Row bands, the Column fan-out and both tails
may leave it, and every proposal is a diagonal Row bus (``routing.row_sides``,
the fit option ``row_sides``).  ``surface/fieldfit.py`` finds the largest
row- and column-convex field of free cells per lattice exactly (a dynamic
program) and the largest full rectangle, prunes the lattices with exact
bounds, ranks the fields (more taxels, a turned field only with 3 % more
than the best unturned one, with several exits the narrowest tip within 3
taxels of the most), builds the winners and checks their F
(claude/specs/masked-field/P5-diagonal-bus.md, sections 4 and 6).

Pinned here: the DP, the rectangle search, the capped windows, the early
exit and the quadrant bound against brute force and a reference DP of our
own; the lattice against the exact free space; the plan's targets on the
soft finger (with and without readers), the crank tip pad, the right
triangle, the equilateral triangle and the disk, never worse than
``containment: board``, every proposal DRC-clean, registered and mapped
with every record passing, F's clearance; the turn threshold, the narrow
tip, the reader caps; the map's records and its routing report; the options;
the peel; the P5c carry-overs (``field_footprint`` and ``E_BOARD_SIZE`` on
the diagonal boards); the fit's cost against the board fit's; determinism.
Phase P5e: field-only containment is the default with ``shape: fill``, a map
without the option takes the design's own, a fit that finds no field says
why, and the browser client (``web/``) sends, shows and keeps the Row traces
and the containment (tools/browser/cad_checks.py runs it).

The P5d/P5e reviews' fixes (2026-10-22, :class:`ReviewFixTests`): a turned
field never prunes the unturned search (every turned proposal has 3 % more
taxels than the best unturned field of the whole lattice universe); phase 0
on the usable edge and the quarter phases on every exit (narrow strips and
small plates are never worse than the board fit, auto finds the best exit);
the bases tried; the narrow tip choosing the exit, not the field; both
tails ending together, the nearer the extension past the edge (since
section 27.3 on one line across the boards); the overhang across, where
the surface is, against our own scanlines, and the holes out of the share;
the Row pins by pin under a reversed scan order; a straight design mapped
with field-only containment; a fillet's inner edges and the base edge in
``W_BAND_EDGE_RADIUS``; the work budget (a round-hole plate at 1.5 mm keeps
its fields at about twice the board fit's cost); the early exit, the
rectangle threshold and the runs beside a column against references; and
the browser client's fixes (the stale Generate, the badge and the CSV of a
full field, the pins from the pads, one map request at a time).

The user's decision of 2026-10-23 (P5-diagonal-bus.md section 16): the
corner tolerance (F's margin at the field's four corners may leave the
surface by 0.5 mm, the taxels never: the rounded plates' full rectangles,
the taxels on the surface by our own check, straight sides keeping the full
margin, the lattice's zones and the DP against brute force;
:class:`CornerToleranceTests`).  Its rectangle preference and the
rectangles of ``shape: rectangle`` are gone with the user's decision of
2026-10-26 (P5-diagonal-bus.md section 26.16: CAD mode fits the selected
area; :class:`CadWithoutRectanglesTests`).

The user's rule of 2026-10-25 (section 24, :class:`ConvexCornerTests`): the
corner tolerance at every convex corner of F, an aligned or a concave end
keeping its margin (the DP exact for it against brute force, F's parts and
the map's records with it), the crank pad's staircase one cell longer at its
doubled rows (683 -> 696) and its hypotenuse one straight line.

The user's correction of 2026-10-25 (section 21, :class:`CoverageFirstTests`):
coverage of the selection first.  Shaped fields take the rectangles' caps
(64 x 64; 32 x 32 before): the fin-gripper face's masked 59 x 12 following
its taper, the tails at its mount end.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
import os
import random
import re
import subprocess
import sys
import time
import unittest
from pathlib import Path

from engine import ROW_BUS_VERSION, check_design, design_mask, field_footprint, generate_design, load_profile
from engine.geometry import point_in_polygon
from surface import fieldfit, fill, fit, place, select
from surface.errors import SurfaceError
from surface.mesh import read_stl

try:
    import surface_fixtures as F
    from test_mask_layout import _determinism_problems
    import defaults_of_before
except ImportError:  # run as a package
    from tests import surface_fixtures as F
    from tests.test_mask_layout import _determinism_problems
    from tests import defaults_of_before


def setUpModule() -> None:
    # The default electrodes of before (1.4 mm at 2 mm, fill 0.7): this module's pinned numbers were measured with them
    # (tests/defaults_of_before.py; the user's decision of 2026-11-06 made the default fill 0.5).
    defaults_of_before.start()


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "asset"
CRANK = ASSETS / "crank_gripper" / "tip_left.stl"
SOFT_FINGER = ASSETS / "soft_gripper_finger.stl"
CRANK_PAD = (1.812, -213.721, 138.929)
SOFT_SEED = (0.0, -12.9, -62.7)
SOFT_BASE = {"point_xyz": [0.0, -12.9, -3.0]}
PLATES = {
    "right_triangle": [(0.0, 0.0), (70.0, 0.0), (0.0, 70.0)],
    "equilateral": [(0.0, 0.0), (60.0, 0.0), (30.0, 51.9615)],
    "disk": F.ellipse_outline(25.0, 25.0, 72),
    "rectangle": [(0.0, 0.0), (40.0, 0.0), (40.0, 24.0), (0.0, 24.0)],
    # The reviews' plates: a turned field 1.9 % above the unturned one at 3 mm, the turn cases, narrow and small surfaces.
    "parallelogram": [(0.0, 0.0), (40.0, 0.0), (60.0, 30.0), (20.0, 30.0)],
    "tri_a": [(0.0, 0.0), (50.0, 0.0), (20.0, 40.0)],
    "strip_2.6": [(0.0, 0.0), (2.6, 0.0), (2.6, 40.0), (0.0, 40.0)],
    "strip_3.2": [(0.0, 0.0), (3.2, 0.0), (3.2, 60.0), (0.0, 60.0)],
    "square_3": [(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)],
    "triangle_8": [(0.0, 0.0), (8.0, 0.0), (0.0, 8.0)],
    "sliver": [(0.0, 0.0), (60.0, 0.0), (60.0, 2.2), (0.0, 2.2)],
}


def _rounded(width: float, height: float, radius: float, segments: int = 12) -> list:
    """A rectangle with rounded corners (each a quarter circle of ``segments`` chords), counter-clockwise."""

    points = []
    for cx, cy, start in ((width - radius, radius, -90), (width - radius, height - radius, 0), (radius, height - radius, 90), (radius, radius, 180)):
        for k in range(segments + 1):
            angle = math.radians(start + 90 * k / segments)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


# The user's corner tolerance (P5-diagonal-bus.md section 16): 30 x 38 mm plates with rounded corners, a square whose
# full field fits only with the whole margin on its straight sides, and a square with one cut corner (the rectangle
# preference).
PLATES.update({f"rounded_{radius:g}": _rounded(30.0, 38.0, radius) for radius in (2.0, 3.0, 4.0, 5.0)})
PLATES["square_25.6"] = [(0.0, 0.0), (25.6, 0.0), (25.6, 25.6), (0.0, 25.6)]
PLATES["slanted"] = [(0.0, 0.0), (10.0, 0.0), (30.0, 34.641016), (20.0, 34.641016)]
# A square just holding 12 x 12 at 2 mm (24.4 mm and its 0.1 um insets), bitten 0.8 mm square at one corner: the bite
# reaches into the corner taxel itself (P), not into the margin's middle beside it, so only the taxels' own check refuses
# the full field there.
PLATES["bitten_square"] = [(0.0, 0.0), (24.41, 0.0), (24.41, 23.61), (23.61, 23.61), (23.61, 24.41), (0.0, 24.41)]
PLATES["cut_square"] = [(0.0, 0.0), (50.0, 0.0), (50.0, 45.0), (45.0, 50.0), (0.0, 50.0)]
# The user's fin-gripper variant (P5-diagonal-bus.md section 21; outputs/umi_tip_variants/umi_trap_h75_tip11.8.stl, not
# committed): its flat face as measured (outline_uv), 119.36 mm long, 45.36 mm straight and 25.8 mm wide from the mount
# end, then a 74.33 mm taper to a 12 mm tip.
PLATES["fin"] = [(-52.71, -12.9), (-7.35, -12.9), (66.65, -6.0), (66.65, 6.0), (-7.35, 12.9), (-52.71, 12.9)]
# The fin stretched 2.6 times along its length (310.3 mm, the same 25.8 mm mount end and 12 mm tip): long enough that a
# capped field at its tip would need tails past the surface's 200 mm (the review of P5-diagonal-bus.md section 27.4).
PLATES["fin_2.6"] = [(2.6 * x, y) for x, y in PLATES["fin"]]
# Symmetric faces (P5-diagonal-bus.md section 22): an isosceles triangle (symmetric about its 50 mm base only) and the
# 150 mm face tapering from 40 to 20 mm (symmetric about its two ends; coverage first put its field on a long side).
PLATES["isosceles"] = [(0.0, 0.0), (50.0, 0.0), (25.0, 60.0)]
PLATES["long_taper"] = [(0.0, 0.0), (150.0, 10.0), (150.0, 30.0), (0.0, 40.0)]
# The taxels from the fingertip (P5-diagonal-bus.md section 26): a pointed fingertip (Unitree-like: 24 mm wide, its sides
# straight to 30 mm, then a point at 48 mm), a fin-like taper (40 mm at the exit to 14 mm at its tip, 60 mm long) and a
# slanted edge (a right trapezoid, 30 mm at the exit to 18 mm).
PLATES["pointed"] = [(0.0, 0.0), (24.0, 0.0), (24.0, 30.0), (12.0, 48.0), (0.0, 30.0)]
PLATES["taper"] = [(0.0, 0.0), (40.0, 0.0), (27.0, 60.0), (13.0, 60.0)]
PLATES["slanted_edge"] = [(0.0, 0.0), (30.0, 0.0), (30.0, 50.0), (12.0, 50.0)]
# Per rounded plate: the first proposal's taxels and the cells its field misses (0: the full 14 x 18 rectangle).  Before
# the tolerance: 252 / 0, 250 / 2, 248 / 4, 246 / 6.
ROUNDED = {"rounded_2": (252, 0), "rounded_3": (252, 0), "rounded_4": (252, 0), "rounded_5": (248, 4)}
# The first proposal's corner overhang (the map's field_corner_overhang, mm; 0, 0.238459, 0.371574 and 0 before section 26,
# whose tip-first fields lie 0.5-0.7 mm nearer the far end on r2, r3 and r5).
# r3's 0.185287 before section 26.18, whose eighth row phases put its tip-first field another 0.25 mm nearer the far end.
ROUNDED_OVERHANG = {"rounded_2": 0.180847, "rounded_3": 0.31848, "rounded_4": 0.371574, "rounded_5": 0.337359}
# The 40 x 24 mm rectangle plate's first field: full, as any rectangular selection's (section 26.16: a full field is a masked
# field with every position).
RECTANGULAR_FIELD = (19, 11, 209)
FIELD = {"shape": "fill", "containment": "field"}
BOARD = {"shape": "fill", "containment": "board"}
# The plan's targets (thresholds just under the measured values: soft finger 708, crank 666, right triangle 559,
# equilateral 333 unturned, disk 436) and the readers' fills of the soft finger (48 x 12, 32 x 12).
TARGETS = {"soft_finger": 700, "crank": 650, "right_triangle": 550, "equilateral": 330, "disk": 430}
ASSET_CASES = {"soft_finger", "crank", "crank_auto"}
# The user's threshold of 20 % (P5-diagonal-bus.md section 26.19): 44 mm wide plates, 58 and 59 mm long, with a 2 mm square
# hole on their axis 42-44 mm up from their bottom edge, the exit (side 0): no symmetric row crosses the hole, an asymmetric
# field passes beside it.
AXIS_HOLE = {"axis_hole_58": 58.0, "axis_hole_59": 59.0}
# The records of a map with containment field, in order (a masked field adds taxel_mask_matches_design).
FIELD_RULES = [
    "taxels_on_surface", "taxel_surface_distance", "neighbour_spacing_error", "field_clearance", "field_corner_overhang", "strain_under_field",
    "field_bend_radius", "tail_top_length_mm", "tail_bottom_length_mm", "row_tail_reach", "column_tail_reach",
]


class _Fits:
    """Fits of the fixtures, each run once: ``(data, selection, result, seconds)``."""

    _cache: dict = {}

    @classmethod
    def case(cls, name: str) -> tuple:
        if name == "soft_finger":
            return SOFT_FINGER.read_bytes(), SOFT_SEED, SOFT_BASE
        if name == "crank":
            return CRANK.read_bytes(), CRANK_PAD, {"side": 6}  # the exit on the pad's 70 mm leg
        if name == "crank_auto":
            return CRANK.read_bytes(), CRANK_PAD, "auto"
        if name == "holed_plate":
            return F.stl_bytes(F.holed_plate()), (5.0, 5.0, 3.0), "auto"
        if name == "round_hole":
            return F.stl_bytes(F.round_holed_plate()), (5.0, 5.0, 3.0), "auto"
        if name == "bracket":
            return F.stl_bytes(F.filleted_bracket(0.8, 4)), (20.0, 20.0, 0.0), "auto"
        if name in AXIS_HOLE:
            return F.stl_bytes(F.holed_plate((44.0, AXIS_HOLE[name]), ((21.0, 42.0), (23.0, 44.0)))), (1.0, 1.0, 3.0), {"side": 0}
        outline = PLATES[name]
        centre = (math.fsum(p[0] for p in outline) / len(outline), math.fsum(p[1] for p in outline) / len(outline), 3.0)
        return F.stl_bytes(F.plate(outline, 3.0)), centre, "auto"

    @classmethod
    def get(cls, test: unittest.TestCase, name: str, options: dict, base=None) -> tuple:
        """A fit's ``(data, selection, result, seconds)``; ``base`` other than the case's, and E_SURFACE_NO_FIT as the
        SurfaceError in place of the result."""

        if name in ASSET_CASES and not (SOFT_FINGER.exists() and CRANK.exists()):
            test.skipTest("asset/ meshes are not committed")
        key = (name, repr(sorted(options.items())), repr(base))
        if key not in cls._cache:
            data, point, default = cls.case(name)
            seed = select.nearest_facet(read_stl(data), point)
            selection = {"ops": [{"op": "grow", "seed_facet": seed}]}
            started = time.perf_counter()
            try:
                result = fit.fit_route({"selection": selection, "base": default if base is None else base, "options": options}, data)
            except SurfaceError as error:
                if error.code != "E_SURFACE_NO_FIT":
                    raise
                result = error
            cls._cache[key] = (data, selection, result, time.perf_counter() - started)
        return cls._cache[key]


def _shapes(result: dict) -> list:
    return [(p["metrics"]["rows"], p["metrics"]["columns"], p["metrics"]["taxels"]) for p in result["proposals"]]


def _frame(placement: dict) -> fit.BaseFrame:
    return fit.BaseFrame({"from_uv": placement["base_from_uv"], "to_uv": placement["base_to_uv"], "inward_uv": placement["base_inward_uv"]},
                         placement["base_angle_deg"])


# --------------------------------------------------------------------------
# References of our own: the definition (brute force) and a plain DP
# --------------------------------------------------------------------------


def _ends(free: list) -> list:
    """maxb of a row of free flags: the end of each cell's free run, or -1."""

    ends = []
    for a in range(len(free)):
        if not free[a]:
            ends.append(-1)
            continue
        b = a
        while b + 1 < len(free) and free[b + 1]:
            b += 1
        ends.append(b)
    return ends


def _is_convex(selection: list) -> bool:
    """The definition: rows consecutive, one run each, consecutive runs share a column, each column's rows consecutive."""

    rows = [(j, run) for j, run in enumerate(selection) if run is not None]
    if not rows:
        return False
    indices = [j for j, _ in rows]
    if indices != list(range(indices[0], indices[-1] + 1)):
        return False
    for (_, (a1, b1)), (_, (a2, b2)) in zip(rows, rows[1:]):
        if a2 > b1 or a1 > b2:
            return False
    columns: dict = {}
    for j, (a, b) in rows:
        for c in range(a, b + 1):
            columns.setdefault(c, []).append(j)
    return all(found == list(range(found[0], found[-1] + 1)) for found in columns.values())


def _free(selection: list, plain: list, up: list, zones: list = None, band: list = None) -> bool:
    """Every run free: the top row by ``plain``, the others by ``up``; with ``zones`` (``fieldfit.lattice``) every
    corner zone of F held free but at its convex corners (section 24): a run's bottom left zone is left out where no
    row lies below it or the row below starts right of it, its bottom right zone where that row ends left of it, its
    top zones likewise against the row above (an aligned or a concave end holds its zone).  With ``band`` (the lattice's
    filler band at sparse pitches, section 26b) every run by ``plain`` and the filler between consecutive runs ``(a',
    b')`` and ``(a, b)`` over their common extent: ``band[j][max(a, a')] >= min(b, b')`` (``up`` not read)."""

    rows = [j for j, run in enumerate(selection) if run is not None]
    if band is not None:
        if not all(plain[j][selection[j][0]] >= selection[j][1] for j in rows):
            return False
        for j in rows[:-1]:
            (a1, b1), (a2, b2) = selection[j], selection[j + 1]
            if band[j][max(a1, a2)] < min(b1, b2):
                return False
    elif not all((plain if j == rows[-1] else up)[j][selection[j][0]] >= selection[j][1] for j in rows):
        return False
    for j in rows:
        flags = zones[j] if zones else None
        if flags is None:
            continue
        a, b = selection[j]
        below = selection[j - 1] if j != rows[0] else None
        above = selection[j + 1] if j != rows[-1] else None
        needed = (below is not None and below[0] <= a, below is not None and below[1] >= b,
                  above is not None and above[0] <= a, above is not None and above[1] >= b)
        if any(need and not flags[k][(a, b, a, b)[k]] for k, need in enumerate(needed)):
            return False
    return True


def _brute(plain: list, up: list, caps: tuple = (99, 99), rectangle: bool = False, zones: list = None, symmetric: bool = False,
           band: list = None, top: int = None) -> int:
    """The definition: the most cells of a row- and column-convex set of free runs within the caps (``symmetric``: every
    run its own mirror image, first + last = columns - 1; ``band``: :func:`_free`'s filler over the common extent;
    ``top``: only sets whose top run lies in that row)."""

    columns = len(plain[0])
    options = [[None] + [(a, b) for a in range(columns) for b in range(a, columns) if plain[j][a] >= b and (not symmetric or a + b == columns - 1)]
               for j in range(len(plain))]
    best = 0
    for selection in itertools.product(*options):
        if top is not None and (selection[top] is None or any(run is not None for run in selection[top + 1:])):
            continue
        if not _is_convex(selection) or not _free(selection, plain, up, zones, band):
            continue
        runs = [run for run in selection if run is not None]
        if rectangle and len(set(runs)) != 1:
            continue
        width = max(b for _, b in runs) - min(a for a, _ in runs) + 1
        if len(runs) > caps[0] or width > caps[1]:
            continue
        best = max(best, sum(b - a + 1 for a, b in runs))
    return best


def _tip(plain: list, up: list, cap: int, zones: list = None, runs: list = None) -> tuple:
    """The lattice's rows a capped field takes (section 23): the ``cap`` rows down from the farthest row with a free run
    (``runs``: a free run among these ``(a, b)``), as ``(plain, up, zones)`` of those rows; empty lists when none is free."""

    free = [j for j in range(len(plain)) if any(plain[j][a] >= b for a, b in runs)] if runs is not None else \
        [j for j in range(len(plain)) if any(end >= a for a, end in enumerate(plain[j]))]
    if not free:
        return [], [], None
    low, high = max(0, free[-1] - cap + 1), free[-1]
    return plain[low:high + 1], up[low:high + 1], zones[low:high + 1] if zones else zones


def _reference(plain: list, up: list) -> int:
    """A plain DP over the four monotonicity phases with every transition tried (O(rows x C^4))."""

    best = 0
    previous: dict = {}
    columns = len(plain[0])
    for j in range(len(plain)):
        current: dict = {}
        for a in range(columns):
            for b in range(a, columns):
                if plain[j][a] < b:
                    continue
                size = b - a + 1
                for widening_left, widening_right in ((True, True), (False, True), (True, False), (False, False)):
                    value = size if widening_left and widening_right else None
                    for (a2, b2, left2, right2), held in previous.items():
                        if a > b2 or a2 > b:
                            continue
                        if widening_left and not (left2 and a <= a2):
                            continue
                        if not widening_left and a < a2:
                            continue
                        if widening_right and not (right2 and b >= b2):
                            continue
                        if not widening_right and b > b2:
                            continue
                        if value is None or held + size > value:
                            value = held + size
                    if value is None:
                        continue
                    best = max(best, value)
                    if up[j][a] >= b:
                        current[(a, b, widening_left, widening_right)] = value
        previous = current
    return best


def _random_grid(rng: random.Random, rows: int, columns: int, density: float, sparse: bool) -> tuple:
    plain, up = [], []
    for _ in range(rows):
        free = [rng.random() < density for _ in range(columns)]
        plain.append(_ends(free))
        up.append(_ends([flag and rng.random() < 0.8 for flag in free]) if sparse and rng.random() < 0.5 else list(plain[-1]))
    return plain, up


class FieldSearchTests(unittest.TestCase):
    def test_the_dp_matches_brute_force_on_random_grids(self) -> None:
        rng = random.Random(7)
        for trial in range(300):
            plain, up = _random_grid(rng, rng.randint(1, 4), rng.randint(1, 5), 0.8, sparse=True)
            with self.subTest(trial=trial, plain=plain, up=up):
                count, spans = fieldfit.best_convex(plain, up, 0, len(plain[0]) - 1, 0, len(plain) - 1)
                self.assertEqual(count, _brute(plain, up))
                if count:
                    selection = [None] * len(plain)
                    for j, a, b in spans:
                        selection[j] = (a, b)
                    self.assertTrue(_is_convex(selection) and _free(selection, plain, up))
                    self.assertEqual(sum(b - a + 1 for _, a, b in spans), count)

    def test_the_dp_matches_a_reference_dp_on_larger_grids(self) -> None:
        rng = random.Random(11)
        for trial in range(40):
            plain, up = _random_grid(rng, rng.randint(5, 9), rng.randint(5, 8), rng.choice((0.7, 0.85, 0.95)), sparse=True)
            with self.subTest(trial=trial):
                self.assertEqual(fieldfit.best_convex(plain, up, 0, len(plain[0]) - 1, 0, len(plain) - 1)[0], _reference(plain, up))

    def test_caps_thresholds_and_rectangles_match_brute_force(self) -> None:
        rng = random.Random(5)
        for trial in range(250):
            plain, up = _random_grid(rng, rng.randint(1, 4), rng.randint(1, 5), 0.8, sparse=True)
            caps = (rng.randint(1, 4), rng.randint(1, 5))
            grid = {"plain": plain, "up": up, "rows": len(plain), "columns": len(plain[0])}
            tip = _tip(plain, up, caps[0])
            want = _brute(tip[0], tip[1], caps) if tip[0] else 0  # the cap's rows at the far end (section 23)
            with self.subTest(trial=trial, caps=caps):
                self.assertEqual(fieldfit.search_shaped(grid, caps[0], caps[1], 0)[0], want)
                # With a threshold the search gives the same field when it beats it, else nothing.
                threshold = rng.randint(0, 8)
                self.assertEqual(fieldfit.search_shaped(grid, caps[0], caps[1], threshold)[0], want if want > threshold else 0)
                self.assertEqual(fieldfit.best_convex(plain, up, 0, len(plain[0]) - 1, 0, len(plain) - 1, threshold)[0],
                                 _brute(plain, up) if _brute(plain, up) > threshold else 0)
                self.assertEqual(fieldfit.best_rectangle(plain, up, caps[0], caps[1])[0], _brute(plain, up, caps, rectangle=True))

    def test_the_bounds_hold(self) -> None:
        # The lattice bound, each window's bound and the quadrant bound of a window around a blocked cell never
        # fall below the best field there.
        rng = random.Random(3)
        quadrants = 0
        for trial in range(120):
            plain, up = _random_grid(rng, rng.randint(3, 8), rng.randint(3, 8), 0.85, sparse=False)
            rows, columns = len(plain), len(plain[0])
            runs = [fieldfit.row_intervals(ends) for ends in plain]
            cap = (rng.randint(2, rows), rng.randint(2, columns))
            self.assertGreaterEqual(fieldfit.lattice_bound(plain, *cap), fieldfit.search_shaped(
                {"plain": plain, "up": up, "rows": rows, "columns": columns}, cap[0], cap[1], 0)[0])
            for bound, row_lo, col_lo, row_hi, col_hi in fieldfit.window_bounds(runs, rows, columns, *cap):
                best = fieldfit.best_convex(plain, up, col_lo, col_hi, row_lo, row_hi)[0]
                with self.subTest(trial=trial, window=(row_lo, col_lo, row_hi, col_hi)):
                    self.assertGreaterEqual(bound, best)
                    tighter = fieldfit.quadrant_bound(runs, row_lo, col_lo, row_hi, col_hi)
                    if tighter is not None:
                        quadrants += 1
                        self.assertGreaterEqual(tighter, best)
        self.assertGreater(quadrants, 50)

    def test_a_hole_takes_a_quadrant(self) -> None:
        # A free 9 x 9 grid with its centre blocked: the field gives up a closed quadrant at it (the 9 x 9 less a 5 x 5
        # corner, 56), and the quadrant bound says so where the rows' bound says 76.
        free = [[not (r == 4 and c == 4) for c in range(9)] for r in range(9)]
        plain = [_ends(row) for row in free]
        runs = [fieldfit.row_intervals(ends) for ends in plain]
        self.assertEqual(fieldfit.best_convex(plain, plain, 0, 8, 0, 8)[0], 56)
        self.assertEqual(fieldfit.window_bounds(runs, 9, 9, 9, 9)[0][0], 76)
        self.assertEqual(fieldfit.quadrant_bound(runs, 0, 0, 8, 8), 56)

    def test_the_lattice_agrees_with_the_free_space(self) -> None:
        # Without the corner tolerance each run is free exactly when its grown crossing strips lie in one free interval of
        # the surface (with it, CornerToleranceTests.test_the_lattice_leaves_out_only_the_corner_zones).
        triangles = F.holed_plate()
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (5.0, 5.0, 3.0))
        from surface import api as api_module

        _, chart = api_module.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": seed}]})
        options = fit.parse_options({})
        side = fit.choose_bases("auto", api_module.boundary_sides(mesh, chart), mesh, chart)[0]
        obstacles = fit.surface_obstacles(mesh, chart, options)
        rng = random.Random(9)
        checked = 0
        for angle, pitch, margin in ((0.0, 2.0, 0.5), (20.0, 1.3, 0.5), (0.0, 4.0, 0.5)):
            frame = fit.BaseFrame(side, angle)
            space = fill.FreeSpace(chart, frame, obstacles, 0.0, side["edges"])
            width = fit._electrode(pitch, 0.7)
            grid = fieldfit.lattice(space, pitch, width, margin, (rng.random() * pitch, rng.random() * pitch), tolerance=0.0)
            self.assertEqual(all(up is plain for up, plain in zip(grid["up"], grid["plain"])), pitch - width <= 2 * margin)
            for _ in range(300):
                j, a = rng.randrange(grid["rows"]), rng.randrange(grid["columns"])
                b = rng.randrange(a, grid["columns"])
                y = grid["y0"] + j * pitch
                x0, x1 = grid["x0"] + a * pitch - margin, grid["x0"] + b * pitch + width + margin
                strip = space.rect_free(x0, x1, round(y - margin, 9), round(y + width + margin, 9))
                with self.subTest(angle=angle, pitch=pitch, row=j, run=(a, b)):
                    self.assertEqual(grid["plain"][j][a] >= b, strip)
                    if pitch - width > 2 * margin:
                        # A row below another also holds the filler band up to the next row's grown strip.
                        self.assertEqual(grid["up"][j][a] >= b, space.rect_free(x0, x1, round(y - margin, 9), round(y + pitch - margin, 9)))
                checked += strip
        self.assertGreater(checked, 100)

    def test_the_caps_follow_the_reader(self) -> None:
        def caps(**options) -> tuple:
            return fieldfit.caps(fit.parse_options(options))

        # Shaped fields take the rectangles' caps (P5-diagonal-bus.md section 21; 32 x 32 before).
        self.assertEqual(caps(), ([(64, 64)], [(64, 64)]))
        self.assertEqual(caps(reader="auto"), ([(48, 48)], [(48, 48)]))
        self.assertEqual(caps(reader="48x48"), ([(48, 48)], [(48, 48)]))
        self.assertEqual(caps(reader="32x16"), ([(16, 32), (32, 16)], [(16, 32), (32, 16)]))
        self.assertEqual(caps(reader="16x16"), ([(16, 16)], [(16, 16)]))
        self.assertEqual(caps(max_rows=20, max_columns=40), ([(20, 40)], [(20, 40)]))
        self.assertEqual(caps(reader="auto", max_rows=20), ([(20, 48)], [(20, 48)]))

    def test_the_ladder(self) -> None:
        self.assertEqual(fieldfit.ladder(fit.parse_options({})), [2.0])
        self.assertEqual(fieldfit.ladder(fit.parse_options({"objective": "max_taxels", "min_pitch_mm": 1.5})), [1.5, 1.51, 1.52, 1.53])
        self.assertEqual(fieldfit.ladder(fit.parse_options({"objective": "max_area"})), fit.max_area_pitches(1.0))


def _candidate(value: int, angle: float = 0.0, tip: float = 10.0, order: int = 0, pitch: float = 2.0) -> dict:
    candidate = {"rows": 4, "columns": 4, "cells": ((0, 3),) * 4, "taxels": value, "full": True, "value": value, "tip_mm": tip,
                 "pitch": pitch, "angle_deg": angle, "order": order, "phase": (0.0, 0.0), "field_origin": (0.0, 0.0)}
    candidate["rank"] = fieldfit.field_rank(candidate)
    return candidate


class RankTests(unittest.TestCase):
    def test_an_unturned_lattice_is_pruned_by_unturned_fields_only(self) -> None:
        # A turned field is proposed only with 3 % over the best unturned one, so the unturned search must find that one
        # (and its alternatives) whatever the turned frames hold: their fields do not raise its threshold.
        search = fieldfit._Search(fit.parse_options(FIELD), fit.load_profile_cached("surface"), False)
        unturned, turned = _candidate(100), _candidate(110, angle=20.0)
        turned["rows"] = 5
        search.add(unturned)
        search.add(turned)
        self.assertEqual(search.unturned, 100)
        self.assertEqual(search.threshold(False, 2.0), 97)  # 97 % of the best unturned field
        self.assertEqual(search.threshold(True, 2.0), 106)  # 97 % of the turned 110 (above 103 % of the unturned 100, less one)

    def test_a_turned_field_needs_three_percent_more_taxels(self) -> None:
        unturned = _candidate(300)
        for value, kept in ((308, False), (309, True), (400, True)):
            with self.subTest(turned=value):
                found = fieldfit.ordered([unturned, _candidate(value, angle=20.0)], auto_exit=False)
                self.assertEqual([c["angle_deg"] for c in found], [20.0, 0.0] if kept else [0.0])
        # Turned fields only: nothing unturned to beat.
        self.assertEqual(len(fieldfit.ordered([_candidate(50, angle=10.0)], auto_exit=False)), 1)

    def test_the_parallelogram_keeps_its_unturned_field(self) -> None:
        # At 3 mm the parallelogram, turned 30 degrees against its base, took 107 taxels, 1.9 % more than the unturned 105:
        # the fit proposed the unturned field, and without the threshold the turned one.  With the corner tolerance (P5
        # section 16) the unturned field holds 115 (its first and last rows reach into the acute corners), and no turned
        # field comes near it, with the threshold or without.  (The equilateral plate, whose 339 turned taxels beat 333 by
        # 1.8 % before phase 0 lay on the usable edge, held 340 unturned, now 341.)
        # Since section 24 (the tolerance at every convex corner: its slanted sides' staircases) 121.
        _, _, result, _ = _Fits.get(self, "parallelogram", PARALLELOGRAM)
        self.assertEqual(result["proposals"][0]["metrics"]["taxels"], 121)
        self.assertTrue(all(p["metrics"]["angle_deg"] == 0.0 for p in result["proposals"]))
        turned = _turned_parallelogram(self)
        self.assertEqual((turned["proposals"][0]["metrics"]["taxels"], turned["proposals"][0]["metrics"]["angle_deg"]), (121, 0.0))
        # 341 before its symmetric lattices, 342 before section 24, 353 before section 26.18 (now the tip-first 349 on an
        # eighth row phase, 0.25 mm nearer its apex, the 353 next).
        self.assertEqual(_shapes(_Fits.get(self, "equilateral", FIELD)[2])[:2], [(25, 27, 349), (25, 27, 353)])

    def test_several_exits_rank_the_fields_within_three_taxels_by_their_tip(self) -> None:
        wide, narrow, far = _candidate(669, tip=64.4, order=5), _candidate(666, tip=14.4, order=6), _candidate(662, tip=8.4, order=7)
        self.assertEqual([c["tip_mm"] for c in fieldfit.ordered([wide, narrow, far], auto_exit=True)], [14.4, 64.4, 8.4])
        self.assertEqual([c["tip_mm"] for c in fieldfit.ordered([wide, narrow, far], auto_exit=False)], [64.4, 14.4, 8.4])
        # Within 3 taxels or 1 % of the most, whichever is more: the crank's 666 against the cut corner's 670 (4 taxels,
        # 0.6 %), not a field 7 below 670.
        self.assertEqual(fieldfit.tip_slack(2.0, False, 670), 6)
        wide = _candidate(670, tip=64.4, order=5)
        self.assertEqual([c["tip_mm"] for c in fieldfit.ordered([wide, narrow], auto_exit=True)], [14.4, 64.4])
        self.assertEqual([c["tip_mm"] for c in fieldfit.ordered([wide, _candidate(663, tip=14.4, order=6)], auto_exit=True)], [64.4, 14.4])
        # max_area: the tolerance is three cells' area at the field's pitch.
        self.assertEqual(fieldfit.tip_slack(2.0, True), 12_000_000)
        # The tip chooses the exit, not the field: one exit's fields keep their rank (the full 256 before the masked
        # 254 of the same readout, which it then dominates), its exit ordered by the tip of its best field.
        full, masked, other = _candidate(256, tip=32.5, order=1), _candidate(254, tip=29.2, order=1), _candidate(255, tip=30.0, order=0)
        masked["full"] = False
        masked["rank"] = fieldfit.field_rank(masked)
        self.assertEqual([c["value"] for c in fieldfit.ordered([masked, full, other], auto_exit=True)], [255, 256, 254])
        other["tip_mm"] = 33.0
        self.assertEqual([c["value"] for c in fieldfit.ordered([masked, full, other], auto_exit=True)], [256, 254, 255])

    def test_the_crank_pad_prefers_its_narrow_tip(self) -> None:
        # With exit auto the pad's cut corner holds the most taxels, 670 with the corner tolerance (669 before), with F
        # 64.4 mm wide at ROW_01; the 70 mm leg holds 666 with F 14.4 mm wide there (a 14.5 mm board tip), within 1 % of
        # the most, and the fit proposes that one (the user's answer).  With shaped fields up to 64 x 64 (section 21) the
        # cut corner holds 686 (F 68.4 mm wide at ROW_01), the leg 683 of 34 x 34 (F 12.4 mm there), still within 1 %.
        # With the corner tolerance at every convex corner (section 24): the cut corner 699, the leg 696 (F still 12.4 mm
        # wide at ROW_01), within 1 %.  Since section 26 the leg's tip-first field goes first (688, 98.9 % of the 696,
        # reaching 0.5 mm nearer the fingertip) and the 696 next; the exit is the narrow tip's, as before.
        _, _, result, _ = _Fits.get(self, "crank_auto", FIELD)
        first = result["proposals"][0]
        self.assertEqual((first["metrics"]["taxels"], first["placement"]["base_side"]), (688, 6))
        self.assertEqual((result["proposals"][1]["metrics"]["taxels"], result["proposals"][1]["placement"]["base_side"]), (696, 6))
        self.assertLess(first["metrics"]["row_bus"]["tip_width_mm"], 17.0)
        data, point, base = _Fits.case("crank_auto")
        mesh = read_stl(data)
        from surface import api as api_module

        _, chart = api_module.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, point)}]})
        options = fit.parse_options(FIELD)
        bases = fit.choose_bases(base, api_module.boundary_sides(mesh, chart), mesh, chart)
        found = fieldfit.search_fields(chart, bases, options, fit.load_profile_cached("surface"), fit.surface_obstacles(mesh, chart, options), [])
        self.assertEqual(max(c["taxels"] for c in found), 699)
        self.assertGreater(next(c for c in found if c["taxels"] == 699)["tip_mm"], 60.0)
        self.assertEqual(fieldfit.ordered(found, auto_exit=False)[0]["taxels"], 699)


class FieldFitTests(unittest.TestCase):
    def _check(self, name: str, options: dict) -> list:
        """Every proposal: DRC-clean and registered, its F on the surface, mapped with every record passing."""

        data, selection, result, _ = _Fits.get(self, name, options)
        self.assertTrue(result["proposals"])
        for proposal in result["proposals"]:
            metrics = proposal["metrics"]
            with self.subTest(fixture=name, proposal=proposal["rank"]):
                design = proposal["design"]
                self.assertEqual(design["routing"]["row_sides"], fit.parse_options(options)["row_sides"])
                generated = generate_design(design)
                self.assertTrue(generated["ok"], generated["validation"]["errors"][:3])
                self.assertEqual(generated["manifest"]["build_id"], proposal["build_id"])
                self.assertTrue(all(board["verification"]["all_checks_passed"] for board in generated["boards"].values()))
                self.assertEqual(generated["boards"]["row"]["construction"]["row_bus"]["kind"], ROW_BUS_VERSION)
                self.assertGreaterEqual(metrics["min_clearance_mm"], 0.0)
                self.assertEqual(metrics["containment"], "field")
                # Our own: P inside the surface's outline, F's corners off it by at most the 0.5 mm corner tolerance.
                if "strain_limited" not in proposal["placement"]:
                    self.assertEqual(_corner_problems(data, selection, proposal), [])
                mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": design}, data)
                self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
                rules = [record["rule"] for record in mapped["verification"]]
                masked = design_mask(design) is not None
                self.assertEqual(rules, FIELD_RULES + (["taxel_mask_matches_design"] if masked else []))
                self.assertEqual(mapped["taxel_count"], metrics["taxels"])
                clearance = next(r for r in mapped["verification"] if r["rule"] == "field_clearance")
                self.assertGreaterEqual(clearance["measured"], 0.0)
                self.assertEqual(mapped["readout"]["row_contact_order"], generated["boards"]["row"]["tail"]["row_contact_order"])
                # The Row nets by pin, from the pads (the taxels' row_pin), in the map and the proposal.
                pads = sorted((pad["pin"], pad["net"]) for pad in generated["boards"]["row"]["layers"]["top_copper"]["pads"]
                              if pad.get("kind") == "connector_pad" and pad["net"].startswith("ROW_"))
                self.assertEqual(mapped["readout"]["row_pin_order"], [net for _, net in pads])
                self.assertEqual(metrics["row_bus"]["row_pin_order"], mapped["readout"]["row_pin_order"])
                self.assertEqual({r["row_net"]: r["row_pin"] for r in mapped["taxels"]}, {net: pin for pin, net in pads if any(r["row_net"] == net for r in mapped["taxels"])})
                for key in ("row", "column"):
                    report = mapped["routing_on_surface"][key]
                    self.assertTrue(0.0 < report["on_surface"] <= 1.0)
                    # The fit's report, from the unrounded field origin.
                    self.assertAlmostEqual(report["on_surface"], metrics["routing_on_surface"][key]["on_surface"], delta=2e-4)
                    for side, value in report["overhang_mm"].items():
                        self.assertAlmostEqual(value, metrics["routing_on_surface"][key]["overhang_mm"][side], delta=2e-3)
        return result["proposals"]

    def test_the_soft_finger(self) -> None:
        # The contact face through its mount end: today's 44 x 8 (352) becomes the full 59 x 12 rectangle (708), the 48x48
        # reader takes 48 x 12 and the FlexiTac 32 x 12 (the plan's 576 and 384).  Since shaped fields take the reader's
        # 48 x 48 (section 21) the 48x48 reader's first proposal was a masked field turned 30 degrees, 620 of 48 x 38 (7.6 %
        # over the unturned 576); the face is symmetric about its exit, so since section 22 no frame is turned there and
        # the symmetric 48 x 12 = 576 is the proposal.
        _, _, result, _ = _Fits.get(self, "soft_finger", FIELD)
        self.assertGreaterEqual(result["proposals"][0]["metrics"]["taxels"], TARGETS["soft_finger"])
        large = _Fits.get(self, "soft_finger", dict(FIELD, reader="48x48"))[2]["proposals"]
        self.assertEqual([(*shape, abs(p["metrics"]["angle_deg"])) for shape, p in zip(_shapes({"proposals": large}), large)],
                         [(48, 12, 576, 0.0)])
        self.assertTrue(large[0]["metrics"]["symmetry"]["field"])
        self.assertEqual(_shapes(_Fits.get(self, "soft_finger", dict(FIELD, reader="32x16"))[2])[0], (32, 12, 384))
        for options in (FIELD, dict(FIELD, reader="48x48"), dict(FIELD, reader="32x16")):
            self._check("soft_finger", options)

    def test_the_soft_fingers_tails_end_20_mm_past_its_base_edge(self) -> None:
        # The user's case: with both the tails are stacked, the Column tail (6.5 mm) centred under the 25.8 mm face and
        # on the Row tail (30 mm, wider than the face) under the funnel.  Measured on the proposal's outlines against
        # the face's base edge (its line continued beside it), both boards end the asked 20 mm past it (to the
        # micrometre the tails' lengths are rounded up to); the board above each tail root reaches past the edge as far as
        # the root lies (the overhang report's exit), and since diagonal-bus/8 both tails root on the shared body's bottom
        # edge, 7.49 mm past it (the funnel's root below the fillets into the tails; the funnel 7.2 mm and the Column
        # fan-out 2.1 mm before); 7.0 mm since section 22, the symmetric field centred along the face too (0.98 mm from the
        # base edge, 0.50 mm before); 6.74 mm since section 26.18 (the symmetric tip-first 708 on an eighth row phase, 0.25
        # mm nearer the far end).
        data, selection, result, _ = _Fits.get(self, "soft_finger", FIELD)
        proposal = result["proposals"][0]
        frame = _frame(proposal["placement"])
        outline = [frame.to_base(p) for p in _chart_outline(data, selection)]
        face = (min(p[0] for p in outline), max(p[0] for p in outline))
        generated = generate_design(proposal["design"])
        tails = fieldfit.tails_of(generated, proposal["placement"]["field_origin_base"])
        self.assertTrue(face[0] < tails["column"][0] < tails["column"][1] < face[1], (tails["column"], face))
        self.assertTrue(tails["row"][0] < tails["column"][0] < tails["column"][1] < tails["row"][1], tails)
        self.assertAlmostEqual(tails["row"][2], tails["column"][2], delta=1e-6)
        for key in ("row", "column"):
            with self.subTest(board=key):
                points = [frame.to_base(p) for p in proposal["outlines_uv"][key]]
                self.assertAlmostEqual(-min(frame.height_above_base(p) for p in points), 20.0, delta=2e-3)
                exit_ = proposal["metrics"]["routing_on_surface"][key]["overhang_mm"]["exit"]
                self.assertAlmostEqual(exit_, -tails[key][2], delta=0.01)
                self.assertTrue(6.65 < exit_ < 6.85, exit_)
        self.assertAlmostEqual(proposal["metrics"]["tail_reach_mm"], 20.0, delta=2e-3)
        bus = proposal["metrics"]["row_bus"]
        self.assertEqual((bus["tail_position"], bus["tails"]), ("centred", "stacked"))
        for gone in ("column_tail_side", "column_tail_shift_mm", "column_neck_mm"):
            self.assertNotIn(gone, bus)
        # One outline down to the tail roots (diagonal-bus/4 over the field, diagonal-bus/8 down to the roots): the Column
        # board reaches as far off the surface's sides as the Row board's bands (6.98 and 7.10 mm with the field centred on
        # the face since section 22, where the straight sides cross the base edge; 7.65 and 6.37 mm with it 0.70 mm off;
        # none with diagonal-bus/3), and lies 73 % on the surface (95 % before diagonal-bus/4, 77 % with the outline shared
        # over the field only).
        row = generated["boards"]["row"]
        depth = row["grid_registration"]["active_region"]["y"] - (row["tail"]["bounds"]["y"] + row["tail"]["bounds"]["height"])
        self.assertAlmostEqual(bus["shared_outline_below_field_mm"], depth, delta=1e-6)
        report = proposal["metrics"]["routing_on_surface"]
        for side in ("left", "right"):
            self.assertAlmostEqual(report["column"]["overhang_mm"][side], report["row"]["overhang_mm"][side], delta=1e-3)
            self.assertGreater(report["column"]["overhang_mm"][side], 6.0)
        # Centred: the bands reach as far on both sides but for one lane (59 rows: the two bands one lane apart).
        self.assertLess(abs(report["row"]["overhang_mm"]["left"] - report["row"]["overhang_mm"]["right"]), 0.2)
        self.assertEqual(proposal["metrics"]["symmetry"], {"face": True, "deviation_mm": 0.0, "axis_mm": 12.9, "field": True, "field_offset_mm": 0.0})
        self.assertTrue(0.7 < report["column"]["on_surface"] < 0.75, report["column"]["on_surface"])

    def test_the_crank_tip_pad(self) -> None:
        _, _, result, _ = _Fits.get(self, "crank", FIELD)
        self.assertGreaterEqual(result["proposals"][0]["metrics"]["taxels"], TARGETS["crank"])
        self._check("crank", FIELD)

    def test_the_plates(self) -> None:
        for name in ("right_triangle", "equilateral", "disk"):
            with self.subTest(fixture=name):
                _, _, result, _ = _Fits.get(self, name, FIELD)
                self.assertGreaterEqual(result["proposals"][0]["metrics"]["taxels"], TARGETS[name])
                self._check(name, FIELD)

    def test_field_is_never_worse_than_board(self) -> None:
        names = ["right_triangle", "equilateral", "disk", "holed_plate"] + (["soft_finger", "crank"] if SOFT_FINGER.exists() and CRANK.exists() else [])
        for name in names:
            with self.subTest(fixture=name):
                proposals = _Fits.get(self, name, FIELD)[2]["proposals"]
                field = proposals[0]["metrics"]["taxels"]
                board = _Fits.get(self, name, BOARD)[2]["proposals"][0]["metrics"]["taxels"]
                if name == "holed_plate":
                    # Section 26.17 put the holed plate's symmetric 247 first (around its hole, under the whole board's 330);
                    # since section 26.19 (the user's threshold of 20 %) its turned 396 first again, 60 % more.
                    self.assertEqual((field, proposals[0]["metrics"]["symmetry"]["field"]), (396, False))
                self.assertGreaterEqual(field, board)
                self.assertGreater(field, board)  # on every fixture here the field holds more (the plan: 352 -> 708 ...)

    def test_the_holed_plate_and_the_routing_over_its_hole(self) -> None:
        proposals = self._check("holed_plate", FIELD)
        data, selection, result, _ = _Fits.get(self, "holed_plate", FIELD)
        mapped = place.map_route({"selection": selection, "placement": proposals[0]["placement"], "design": proposals[0]["design"]}, data)
        codes = [warning["code"] for warning in mapped["routing_on_surface"]["warnings"]]
        self.assertIn("W_ROUTING_HOLE", codes)
        # The plate's sides are square edges: a band hanging over one creases (radius 0 against 10 x 0.11 mm).
        edge = next(w for w in mapped["routing_on_surface"]["warnings"] if w["code"] == "W_BAND_EDGE_RADIUS")
        self.assertEqual((edge["measured_mm"], edge["limit_mm"]), (0.0, 1.1))

    def test_a_reader_caps_every_proposal(self) -> None:
        for reader, (sense, drive) in (("32x16", (16, 32)), ("16x16", (16, 16))):
            with self.subTest(reader=reader):
                _, _, result, _ = _Fits.get(self, "right_triangle", dict(FIELD, reader=reader))
                for rows, columns, _ in _shapes(result):
                    self.assertTrue((rows <= sense and columns <= drive) or (rows <= drive and columns <= sense), (rows, columns))
                for proposal in result["proposals"]:
                    self.assertEqual(proposal["metrics"]["reader"], reader)

    def test_the_row_sides_option(self) -> None:
        for sides in ("left", "right"):
            with self.subTest(sides=sides):
                _, _, result, _ = _Fits.get(self, "disk", dict(FIELD, row_sides=sides))
                self.assertEqual(_shapes(result)[0], _shapes(_Fits.get(self, "disk", FIELD)[2])[0])
                for proposal in result["proposals"]:
                    self.assertEqual(proposal["design"]["routing"]["row_sides"], sides)
                    self.assertEqual(proposal["metrics"]["row_bus"]["sides"], sides)
                self._check("disk", dict(FIELD, row_sides=sides))

    def test_a_turned_proposal_maps(self) -> None:
        # A slanted strip's field turned 30 degrees against its 10 mm base: 74 taxels against 54 unturned.
        data, selection, result, _ = _Fits.get(self, "slanted", FIELD, {"side": 0})
        proposal = result["proposals"][0]
        self.assertEqual((proposal["metrics"]["taxels"], proposal["metrics"]["angle_deg"]), (74, -30.0))
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])

    def test_columns_on_top(self) -> None:
        # The top board seen from outside is turned over: COL_01 on the right, so the mask reads mirrored; the field and
        # its taxels are the rows-on-top ones.
        data, selection, result, _ = _Fits.get(self, "right_triangle", dict(FIELD, role_mapping="columns_top"))
        rows_top = _Fits.get(self, "right_triangle", FIELD)[2]
        self.assertEqual(_shapes(result)[0], _shapes(rows_top)[0])
        self.assertEqual(result["proposals"][0]["design"]["role_mapping"], {"top": "columns", "bottom": "rows"})
        mask, mirrored = design_mask(result["proposals"][0]["design"]), design_mask(rows_top["proposals"][0]["design"])
        columns = result["proposals"][0]["metrics"]["columns"]
        self.assertEqual(list(mask), [(columns + 1 - last, columns + 1 - first) for first, last in mirrored])
        self._check("right_triangle", dict(FIELD, role_mapping="columns_top"))

    def test_the_tails_reach_beyond_the_surface(self) -> None:
        # Each tail ends tail_extension_mm beyond the surface's lowest edge under it (or beside it): 20 mm by default,
        # the 7.5 mm template minimum with 6.5.
        for extension in (20.0, 6.5):
            with self.subTest(extension=extension):
                data, selection, result, _ = _Fits.get(self, "right_triangle", dict(FIELD, tail_extension_mm=extension))
                for proposal in result["proposals"]:
                    mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
                    for key in ("row", "column"):
                        reach = next(r for r in mapped["verification"] if r["rule"] == f"{key}_tail_reach")["measured"]
                        self.assertTrue(reach is None or reach >= extension - 1e-3, (key, reach))
                    self.assertGreaterEqual(min(proposal["metrics"]["row_tail_mm"], proposal["metrics"]["column_tail_mm"]), 7.5)

    def test_the_field_fit_costs_at_most_a_few_board_fits(self) -> None:
        # The plan's budget is 6 s per part.  Wall-clock limits fail on a loaded machine, so both fits run here after a
        # warm-up, in CPU time, the least of two interleaved fits each (_timed_fits), and only their ratio is checked
        # (field-only costs about 0.4-2 times the board fit).  The search's ratio: section 26's tip passes are bounded by
        # their own meter (they complete here; TipFirstTests' budget test pins the meter), so their time is measured apart.
        for name in ("right_triangle", "disk"):
            with self.subTest(fixture=name):
                data, selection, _, _ = _Fits.get(self, name, FIELD)
                _Fits.get(self, name, BOARD)
                seconds, passes, result = _timed_fits(data, selection, {"board": BOARD, "field": FIELD})
                self.assertLess(seconds["field"] - passes["field"], 3.0 * seconds["board"] + 1.0, (seconds, passes))
                self.assertTrue(all(base.get("tip_complete") in (None, True) for base in result["field"]["bases"]))

    def test_the_field_fit_is_deterministic(self) -> None:
        data, selection, first, _ = _Fits.get(self, "disk", FIELD)
        again = fit.fit_route({"selection": selection, "base": "auto", "options": FIELD}, data)
        self.assertEqual(_fingerprint(again), _fingerprint(first))
        self.assertEqual(_fingerprint(first), FINGERPRINTS["disk"])

    def test_the_fingerprint_with_other_hash_seeds(self) -> None:
        code = ("import sys; sys.path.insert(0, 'tests'); import defaults_of_before; defaults_of_before.start(cleanup=False); "
                "import test_field_fit as t; print(t._fingerprint_of('equilateral'))")
        for seed in ("0", "123"):
            with self.subTest(seed=seed):
                environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
                output = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
                self.assertEqual(output.stdout.strip(), FINGERPRINTS["equilateral"])


PARALLELOGRAM = dict(FIELD, pitch_mm=3.0)


def _turned_parallelogram(test: unittest.TestCase) -> dict:
    """The parallelogram's field fit at 3 mm without the turn threshold (run once)."""

    key = ("parallelogram", "without the turn threshold")
    if key not in _Fits._cache:
        data, selection, _, _ = _Fits.get(test, "parallelogram", PARALLELOGRAM)
        saved = fieldfit.TURN_GAIN
        try:
            fieldfit.TURN_GAIN = (100, 100)
            _Fits._cache[key] = fit.fit_route({"selection": selection, "base": "auto", "options": PARALLELOGRAM}, data)
        finally:
            fieldfit.TURN_GAIN = saved
    return _Fits._cache[key]


def _chart_outline(data: bytes, selection: dict) -> list:
    from surface import api as api_module

    _, chart = api_module.selection_chart(read_stl(data), selection)
    return chart.outline()


def _timed_fit(data: bytes, selection: dict, options: dict) -> tuple:
    """A fit (base auto): ``(seconds, the tip passes' seconds, result)``, in CPU seconds of this process
    (``time.process_time``: the fit runs here, single-threaded, so other processes' load does not count as it does in
    wall-clock time); section 26's passes (:func:`surface.fieldfit.tip_pass`) are bounded by their own work meter, not by
    the search's."""

    from unittest import mock

    spent = [0.0]
    original = fieldfit.tip_pass

    def timed(*args, **kwargs):
        started = time.process_time()
        try:
            return original(*args, **kwargs)
        finally:
            spent[0] += time.process_time() - started

    started = time.process_time()
    with mock.patch.object(fieldfit, "tip_pass", timed):
        result = fit.fit_route({"selection": selection, "base": "auto", "options": options}, data)
    return time.process_time() - started, spent[0], result


def _timed_fits(data: bytes, selection: dict, runs: dict, rounds: int = 2) -> tuple:
    """The fits of ``runs`` (label: options) interleaved ``rounds`` times (:func:`_timed_fit`): per label the least
    seconds, its passes' seconds and its result.  The ratio tests fail on a loaded machine with wall-clock time and one
    fit each (2026-10-27, at a load of about 40: the round-hole plate's search 7.9 s against 3 x 2.0 + 1 s); CPU time
    and the least of two interleaved fits bound the work, not the machine's other load."""

    best: dict = {}
    for _ in range(rounds):
        for label, options in runs.items():
            found = _timed_fit(data, selection, options)
            if label not in best or found[0] - found[1] < best[label][0] - best[label][1]:
                best[label] = found
    return ({label: found[0] for label, found in best.items()}, {label: found[1] for label, found in best.items()},
            {label: found[2] for label, found in best.items()})


def _fingerprint(result: dict) -> str:
    """A digest of a fit's proposals: build ids, placements, outlines on the chart and metrics (not the mesh's record
    and the selection's seed: the plates' STL bytes differ in the last bit between Pythons' libm)."""

    items = [[p["build_id"], {key: value for key, value in p["placement"].items() if key not in ("mesh", "selection")}, p["outlines_uv"],
              p["metrics"]] for p in result["proposals"]]
    return hashlib.sha256(json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _fingerprint_of(name: str, options: dict = FIELD) -> str:
    """The writer of :data:`FINGERPRINTS` (``options`` FIELD) and :data:`FINGERPRINTS_TIES` (``tip_first: false``)."""

    data, point, base = _Fits.case(name)
    seed = select.nearest_facet(read_stl(data), point)
    return _fingerprint(fit.fit_route({"selection": {"ops": [{"op": "grow", "seed_facet": seed}]}, "base": base, "options": options}, data))


def _coverage_alone(name: str, options: dict = FIELD, base=None) -> dict:
    """A fit without the tip step (:func:`surface.fieldfit.tip_on` false: the order of coverage alone, as 55ae8fe and
    before section 26), run once; ``base`` other than the case's."""

    from unittest import mock

    key = ("coverage alone", name, repr(sorted(options.items())), repr(base))
    if key not in _Fits._cache:
        data, point, default = _Fits.case(name)
        seed = select.nearest_facet(read_stl(data), point)
        with mock.patch.object(fieldfit, "tip_on", lambda options: False):
            _Fits._cache[key] = fit.fit_route({"selection": {"ops": [{"op": "grow", "seed_facet": seed}]}, "base": default if base is None else base,
                                               "options": options}, data)
    return _Fits._cache[key]


# _fingerprint of the field fits (Python 3.9.6 and 3.12, any hash seed; measured 2026-10-21, re-pinned 2026-10-22 for
# the reviews' fixes: phase 0 on the usable edge, the tails, the overhang, the Row pins, the edge warnings; and again
# for diagonal-bus/2, whose boards, build ids and routing reports change, the fields and their counts not; and for its
# review's fixes: diagonal-bus/1's bands, the overhang past the edge at the tail root, the metrics' row_bus keys; and
# for diagonal-bus/3, the stacked tails: the boards, build ids, tail lengths, routing reports and row_bus keys change,
# the fields and their counts not; and for diagonal-bus/4, one outline over the field: the Column board's outline, the
# build ids, the routing reports and the row_bus keys change, the fields and their counts not; and for the user's later
# decisions on it, no Column copper in the lanes' keep-out and lanes following a receding field inward: the disk's Row
# board, its root and tail lengths, the shared outline and the routing reports change, the fields and their counts not;
# and the shared outline's sub-grid vertices no longer filleted: both plates' outlines move by micrometres; and for
# diagonal-bus/5, regular outlines: both boards' outlines, the build ids and the routing reports change, the fields
# and their counts not; and for the corner tolerance and diagonal-bus/6 (P5-diagonal-bus.md section 16): the fields
# (the disk 436 -> 440, the equilateral 340 -> 341), the chamfered notches, the build ids and the reports change); and
# for diagonal-bus/7 (section 17), straight sides at the tip: both boards' outlines, the build ids and the reports
# change, the fields and their counts not; and for diagonal-bus/8 (section 20), one outline down to the tail roots and
# the Column V capped at 80 degrees where that roots the tails no deeper: both boards' copper and outlines, the tails'
# roots and lengths, the build ids and the reports change (the side overhang now also where an outline crosses the
# surface's lowest level), the fields and their counts not); and for section 21, coverage first: only the placement's
# recorded options change (rectangle_preference_pct 0 by default; the old tree with that option gives these digests), the
# fields, boards and reports not; and for section 22, symmetric fields on symmetric faces: the disk's and the
# equilateral's first fields are symmetric (the equilateral 341 -> 342), their alternatives and the metrics' symmetry
# record change (the isosceles triangle added: its symmetric base first); and for section 23, the surface profile's
# tails to 200 mm: only the build ids change (the profile's digest), the fields, placements, outlines and metrics not.
# Rewritten by section 24 (the corner tolerance at every convex corner; diagonal-bus/9's convex sides): the fields (the
# disk 440 -> 448, the equilateral 342 -> 353, the isosceles triangle's first now 341 on a leg, its symmetric base's 328
# third), the outlines, build ids and reports change; Python 3.9.6 and 3.12 alike.  Re-pinned by section 26 (tip first):
# every proposal's metrics gain ``tip`` and the placement's options ``tip_first``; the disk's first field is the tip-first
# 24 x 24 (24 x 23 before, as many taxels), the equilateral's second exit takes a tip-first 342 before its 346, the
# isosceles triangle's fields are unchanged; section 26's round 2 (the zero-cost ties, the tip-zone guard) changes none of
# these three.  FINGERPRINTS_BEFORE: the same fits without the tip step (``tip_on`` false, the option left out of the
# placement's record) equal 55ae8fe's digests, the former pins: sections 26a and 26b change nothing else on these faces.
# FINGERPRINTS_TIES: the same fits with ``tip_first: false`` (since round 2 coverage first with the zero-cost ties: the
# disk's 24 x 24, the isosceles triangle's symmetric 328 0.3 mm nearer its apex).  Re-pinned (both) by section 26.16, CAD
# mode without rectangles: only the placement's recorded options change (``rectangle_preference_pct`` no longer
# recorded); with it put back (0.0) the digests are the former pins, 878761982525..., bfb5ec9fcfab..., 1df826d115d2...
# and b14897ad3828..., 89aa9b8ad8b2..., 0def10f4a778... (the fields, boards and metrics unchanged; 26.16's reach first
# changes none of these three either).  Re-pinned by section 26.17 (round 3c's review: a lead's zero-cost tie takes the
# lead's place, metrics.tip.displaced names the proposal in that place): the disk's 24 x 23 is no longer proposed (with
# tip_first true and false: the 24 x 24 is its tie and takes its place), the isosceles triangle's tip-first 328, its lead's
# tie itself, reports itself as in the displaced field's place (displaced 3, None before); the equilateral and
# FINGERPRINTS_BEFORE unchanged.  Re-pinned (the isosceles triangle, all three) by the user's decision of 2026-10-27
# (section 26.17: a symmetric face's symmetric field first, whatever another field holds): its base's symmetric 328 first
# (its tip-first field, the lead's own tie; without the step the 328 the search kept), the legs' 341 and 337 after it;
# FINGERPRINTS_BEFORE's isosceles is therefore no longer 55ae8fe's (781f4e82166b...), the disk's and the equilateral's are.
# Re-pinned (the equilateral and the isosceles triangle) by section 26.18 (a symmetric group's tip pass on the eighth row
# phases, its slack p / 16): the equilateral's tip-first 349 an eighth phase nearer its apex first (its 353 next; its second
# exit's tip-first 342 gone, that exit's own tip-first field a 349 of the first's readout), the isosceles triangle's
# tip-first 322 reaching 57.15 mm first (its 328 next); FINGERPRINTS_TIES and FINGERPRINTS_BEFORE unchanged.
# Rewritten (all three, each face) by section 27 (diagonal-bus/10, the Row tail centred on the field; its tails ending
# together on the nearest line, sections 27.3 and 27.4), merged with the above on 2026-10-27: the build ids, the boards
# (the Row tails on the field's centre line, their fans and outlines), the tails' lengths and the reports change, the
# fields, their counts and the proposals' order not (each fit's fields are those of section 26.18); FINGERPRINTS_BEFORE's
# disk and equilateral are section 27's own pins of the fits before section 26 (main's fits with diagonal-bus/10), as
# they were 55ae8fe's before it.  Python 3.9.6 and 3.12 alike.  Re-pinned (all three sets) by section 27.8
# (diagonal-bus/11, one side's convex flank): only the build ids change (the construction's version); every proposal of
# these fits has both sides, whose outlines the flank leaves alone, and with the build ids masked the nine digests equal
# baf053c's (259c87f0..., 15045c65..., 8d763feb...; a236ba9f..., 5818cf55..., 3602dcba...; 996a9d55..., b9606291...,
# f169be4f... before).  Re-pinned (all three sets) by the profile revision 2026-10-29 (the gold-finger thickness order
# option and the coverlay-window notes): only the build ids change (the profiles' digests); with the build ids masked the
# nine digests equal 5803873's (dcbfc7a0..., 930da864..., c25e7eda...; c0035dd3..., 9562d8ba..., f4327fc8...; 27077910...,
# e984c742..., 238ee623... before).
FINGERPRINTS = {
    "disk": "1cbbf6d3dbad0522ef390850503173ebc9edf2d8aed62eddc9c93d2e2a1d9c82",
    "equilateral": "09dab2e90c09b5b562c6dabd6a81962dde6046768694d9fbed31fe38827de669",
    "isosceles": "67778c859fe1dd908b1c1ef255593bda429f31f2d05c91153d6a626d04302b63",
}
FINGERPRINTS_BEFORE = {
    "disk": "fd5535f96085be7d9d24ae5276c4c30209177f425e5fe62dbcc99799efa0b1a0",
    "equilateral": "3013c8b5f8abc5b7dfd87f5b5df187e6936984024f41271a79684ac61b822e0f",
    "isosceles": "9e7ff7bd187efdf49f03f6f06bbe9b775ee39631a8d9b217ba72098b65261d29",
}
FINGERPRINTS_TIES = {
    "disk": "7a82f11a11a1818506640588f42ea01f71c4becd8a53d5c6afce1f1fde80a867",
    "equilateral": "3c23a056c182886a00d2f9c51c79569adea48a7c149a7a78877cf670399c36fe",
    "isosceles": "3546804a51d120d2578738a7a55c097c5e4e4104b70d0f903ecb37e17da4c22b",
}


class FieldMapTests(unittest.TestCase):
    def test_board_containment_refuses_the_field_proposal(self) -> None:
        # The same placement under containment board: the boards leave the surface, so board_clearance fails.
        data, selection, result, _ = _Fits.get(self, "right_triangle", FIELD)
        proposal = result["proposals"][0]
        options = dict(proposal["placement"]["options"], containment="board")
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"], "options": options}, data)
        self.assertFalse(mapped["ok"])
        self.assertFalse(next(r for r in mapped["verification"] if r["rule"] == "board_clearance")["passed"])
        self.assertNotIn("routing_on_surface", mapped)

    def test_a_field_off_the_surface_fails_its_clearance(self) -> None:
        # Beside the surface, and across the exit edge (which is a wall for F: only the routing may cross it).
        data, selection, result, _ = _Fits.get(self, "right_triangle", FIELD)
        for shift in ((-3.0, 0.0), (0.0, -1.0)):
            with self.subTest(shift=shift):
                proposal = copy.deepcopy(result["proposals"][0])
                x, y = proposal["placement"]["field_origin_base"]
                proposal["placement"]["field_origin_base"] = [x + shift[0], y + shift[1]]
                mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
                failing = [r["rule"] for r in mapped["verification"] if not r["passed"]]
                self.assertIn("field_clearance", failing)
                self.assertIsNone(next(r for r in mapped["verification"] if r["rule"] == "field_clearance")["measured"])

    def test_the_readout_lists_the_folded_row_order(self) -> None:
        data, selection, result, _ = _Fits.get(self, "right_triangle", FIELD)
        proposal = result["proposals"][0]
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        rows = proposal["metrics"]["rows"]
        odd, even = list(range(1, rows + 1, 2)), list(range(2, rows + 1, 2))
        self.assertEqual(mapped["readout"]["row_contact_order"], [f"ROW_{k:02d}" for k in odd + list(reversed(even))])
        self.assertEqual(proposal["metrics"]["row_bus"]["row_contact_order"], mapped["readout"]["row_contact_order"])
        # The taxels' Row pins come from the pads: ROW_02 is on the last Row contact.
        pins = {record["row_net"]: record["row_pin"] for record in mapped["taxels"]}
        self.assertEqual(pins["ROW_01"], 1)
        self.assertEqual(pins["ROW_02"], rows)
        self.assertEqual(mapped["readout"]["row_pin_order"], mapped["readout"]["row_contact_order"])  # forward scan order
        # An unmasked diagonal bus has a readout too (every position active).
        data, selection, result, _ = _Fits.get(self, "rectangle", FIELD)
        proposal = result["proposals"][0]
        self.assertIsNone(design_mask(proposal["design"]))
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        rows, columns = proposal["metrics"]["rows"], proposal["metrics"]["columns"]
        self.assertEqual(mapped["readout"]["row_spans"], [[1, columns]] * rows)
        self.assertEqual(mapped["readout"]["active"], rows * columns)
        self.assertEqual(len(mapped["readout"]["row_contact_order"]), rows)
        self.assertNotIn("taxel_mask_matches_design", [r["rule"] for r in mapped["verification"]])

    def test_the_routing_report(self) -> None:
        data, selection, result, _ = _Fits.get(self, "disk", FIELD)
        proposal = result["proposals"][0]
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        report = mapped["routing_on_surface"]
        self.assertEqual(set(report), {"row", "column", "strain_max", "bend_radius_min_mm", "warnings"})
        for key in ("row", "column"):
            self.assertEqual(set(report[key]["overhang_mm"]), {"left", "right", "exit"})
            self.assertGreater(max(report[key]["overhang_mm"].values()), 0.0)  # both boards leave the disk
        codes = sorted({w["code"] for w in report["warnings"]})
        self.assertEqual(codes, ["W_BAND_EDGE_RADIUS"])
        # Our own share: sampled points of the Row board inside the disk.
        frame = _frame(proposal["placement"])
        outline = [frame.to_base(p) for p in _chart_outline(data, selection)]
        board = [frame.to_base(p) for p in proposal["outlines_uv"]["row"]]
        xs, ys = [p[0] for p in board], [p[1] for p in board]
        inside = total = 0
        steps = 120
        for i in range(steps):
            for k in range(steps):
                p = (min(xs) + (max(xs) - min(xs)) * (i + 0.5) / steps, min(ys) + (max(ys) - min(ys)) * (k + 0.5) / steps)
                if point_in_polygon(p, board):
                    total += 1
                    inside += point_in_polygon(p, outline)
        self.assertAlmostEqual(report["row"]["on_surface"], inside / total, delta=0.02)


class TailRunTests(unittest.TestCase):
    def test_a_tail_runs_down_to_the_surface_below_it(self) -> None:
        # A 40 x 30 mm surface with a notch in its bottom edge (10..20 mm, 5 mm deep): a tail's run is from its root down
        # to the lowest edge under its width, negative from a root beyond it, and beside the surface down to the base
        # side's line continued (y = 0 here, unrotated; the review of diagonal-bus/2: a Column tail moved beside the soft
        # finger's face was taken to root on the edge and ended 27.8 mm past it, not 20).
        outline = [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (20.0, 5.0), (20.0, 0.0), (40.0, 0.0), (40.0, 30.0), (0.0, 30.0)]
        lowest = fieldfit.bottoms(outline)
        self.assertEqual(fieldfit.surface_bottom(lowest, 12.0, 18.0), 5.0)
        self.assertEqual(fieldfit.surface_bottom(lowest, 5.0, 15.0), 0.0)
        self.assertIsNone(fieldfit.surface_bottom(lowest, 45.0, 50.0))
        runs = fieldfit.tail_runs(lowest, {"row": (12.0, 18.0, 9.0), "column": (25.0, 30.0, -3.0), "beside": (41.0, 44.0, 9.0)})
        self.assertEqual(runs, {"row": 4.0, "column": -3.0, "beside": 9.0})
        # A turned frame: its base side runs through the origin at -10 degrees, continued beside the surface too.
        turned = fit.BaseFrame({"from_uv": (0.0, 0.0), "to_uv": (40.0, 0.0), "inward_uv": (0.0, 1.0)}, 10.0)
        self.assertAlmostEqual(fieldfit.tail_runs(lowest, {"beside": (41.0, 44.0, 9.0)}, turned)["beside"], 9.0 + 44.0 * math.tan(math.radians(10.0)), places=9)
        # Both tails end on one line across the boards (the user's request of P5-diagonal-bus.md section 27.3: the stacked
        # tails' contacts line up), the nearest line on which each tail is at least the shortest tail long and ends at least
        # the extension past the edge under it (the review: the field fit's tails ended 36-41 mm past a 20 mm extension):
        # the roots above, the Column tail's end 20 mm past the base edge sets the line, the Row tail's over the notch ends
        # 25 mm past it.  The diagonal Row bus's two roots on one level (over the notch and beside it) give two equal tails,
        # the extension under the Row tail setting them (24 mm: the Column tail's root 15 mm past its edge ends 39 mm past
        # it; the old shared reach, its shortest tail's 22.5 mm past that edge, made both 26.5 mm, the video's rank-0
        # galaxea 26 x 10 re-tailed 22.989 mm where 18.101 does); the shortest tail sets the line where it ends farther (an
        # extension under it, 6.5 mm, or a root beyond its edge: the Row tail's 7.5 mm ends 22.5 mm past, the Column tail
        # reaches it, 14.5 mm).
        self.assertEqual(fieldfit.tail_lengths({"row": 4.0, "column": -3.0}, 20.0, 7.5, {"row": 9.0, "column": -3.0}), {"row": 29.0, "column": 17.0})
        self.assertEqual(fieldfit.tail_lengths({"row": -3.0, "column": 2.0}, 20.0, 7.5, {"row": 2.0, "column": 2.0}), {"row": 22.0, "column": 22.0})
        self.assertEqual(fieldfit.tail_lengths({"row": 4.0, "column": -15.0}, 20.0, 7.5, {"row": -2.0, "column": -2.0}), {"row": 24.0, "column": 24.0})
        self.assertEqual(fieldfit.tail_lengths({"row": 0.0, "column": 0.0}, 6.5, 7.5, {"row": -4.0, "column": -4.0}), {"row": 7.5, "column": 7.5})
        self.assertEqual(fieldfit.tail_lengths({"row": -15.0, "column": -16.0}, 20.0, 7.5, {"row": -2.0, "column": 5.0}), {"row": 7.5, "column": 14.5})
        # Lengths in micrometres, rounded up, whatever the roots' noise; a tail reaching the line from a root off the grid
        # too (it reaches the line, not 0.4 um short of it: the Row tail's 29.2345674 mm to the line set by the Column tail;
        # rounded down, 29.234, no other case told).
        self.assertEqual(fieldfit.tail_lengths({"row": 1.2345674, "column": 0.5}, 20.0, 7.5, {"row": -5.1234561, "column": -5.1234561}), {"row": 21.235, "column": 21.235})
        self.assertEqual(fieldfit.tail_lengths({"row": 4.0, "column": -3.0}, 20.0, 7.5, {"row": 9.2345674, "column": -3.0}), {"row": 29.235, "column": 17.0})
        # A tail end 6.5 mm below the notch's bottom, and one beside the surface 1.5 mm past the base side's line.
        self.assertEqual(fieldfit.tail_reach(lowest, [(12.0, -1.5), (18.0, -1.5), (18.0, 8.0), (12.0, 8.0)]), 6.5)
        self.assertEqual(fieldfit.tail_reach(lowest, [(42.0, -1.5), (48.0, -1.5), (48.0, 8.0), (42.0, 8.0)]), 1.5)


class FieldOptionTests(unittest.TestCase):
    def test_containment_and_row_sides(self) -> None:
        self.assertEqual(fit.parse_options({})["containment"], "field")  # the default with shape fill from P5e on
        self.assertEqual(fit.parse_options({})["row_sides"], "both")
        self.assertEqual(fit.parse_options(FIELD)["containment"], "field")
        for options, message in (
            ({"containment": "all"}, "options.containment must be one of board, field."),
            ({"row_sides": "top"}, "options.row_sides must be one of both, left, right."),
        ):
            with self.subTest(options=options):
                with self.assertRaises(SurfaceError) as raised:
                    fit.parse_options(options)
                self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")
                self.assertIn(message, raised.exception.message)
        # Board containment as asked (no shape or template decides it since section 26.16).
        self.assertEqual(fit.parse_options({"containment": "board"})["containment"], "board")

    def test_field_is_the_default_with_shape_fill(self) -> None:
        # Masked-field phase P5e: the default fit is the field-only one (the same proposals as an explicit field).
        self.assertEqual((fit.DEFAULT_OPTIONS["containment"], fit.DEFAULT_OPTIONS["shape"]), ("field", "fill"))
        default = _Fits.get(self, "right_triangle", {})[2]
        explicit = _Fits.get(self, "right_triangle", FIELD)[2]
        self.assertEqual([p["build_id"] for p in default["proposals"]], [p["build_id"] for p in explicit["proposals"]])
        self.assertEqual(default["request"]["options"]["containment"], "field")

    def test_a_map_without_containment_takes_the_designs(self) -> None:
        # Options without containment (a placement written before the option, or a map request's own options): a
        # diagonal Row bus maps with field-only containment, any other design with the whole board, as it was fitted.
        bus, straight = {"routing": {"row_sides": "both"}}, {"routing": {}}
        self.assertEqual(place.map_options({}, bus)["containment"], "field")
        self.assertEqual(place.map_options({}, straight)["containment"], "board")
        self.assertEqual(place.map_options({"shape": "rectangle"}, bus)["containment"], "board")
        self.assertEqual(place.map_options({"template": "generic"}, bus)["containment"], "board")
        self.assertEqual(place.map_options({"containment": "board"}, bus)["containment"], "board")
        self.assertEqual(place.map_options({"containment": "field"}, straight)["containment"], "field")
        for options, rule in ((BOARD, "board_clearance"), (FIELD, "field_clearance")):
            with self.subTest(options=options):
                data, selection, result, _ = _Fits.get(self, "right_triangle", options)
                proposal = result["proposals"][0]
                placement = dict(proposal["placement"], options={k: v for k, v in proposal["placement"]["options"].items() if k != "containment"})
                mapped = place.map_route({"selection": selection, "placement": placement, "design": proposal["design"]}, data)
                self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
                self.assertIn(rule, [r["rule"] for r in mapped["verification"]])

    def test_row_sides_does_not_touch_board_containment(self) -> None:
        board = _Fits.get(self, "right_triangle", BOARD)[2]
        sided = _Fits.get(self, "right_triangle", dict(BOARD, row_sides="left"))[2]
        self.assertEqual([p["build_id"] for p in sided["proposals"]], [p["build_id"] for p in board["proposals"]])
        self.assertTrue(all("row_sides" not in p["design"]["routing"] for p in board["proposals"]))


class PeelTests(unittest.TestCase):
    def test_the_peel_keeps_the_field_convex(self) -> None:
        candidate = _candidate(0)
        candidate.update(cells=((1, 3), (0, 4), (0, 4)), rows=3, columns=5, taxels=13, full=False, width=1.4, margin=0.5, peels=0)
        candidate["value"] = 13
        # A point right of the top row: its right end goes, the field keeps its origin.
        peeled = fieldfit.peel_field(candidate, (8.5, 5.5))
        self.assertEqual(peeled["cells"], ((1, 2), (0, 4), (0, 4)))
        self.assertEqual((peeled["taxels"], peeled["peels"], peeled["field_origin"]), (12, 1, (0.0, 0.0)))
        # A point left of the bottom row: its left end goes (the middle row still holds column 0).
        peeled = fieldfit.peel_field(candidate, (-1.0, 0.7))
        self.assertEqual(peeled["cells"], ((1, 3), (0, 4), (1, 4)))
        # A one-cell top row goes whole; the rows below then start at the top.
        single = dict(candidate, cells=((2, 2), (0, 4), (0, 4)), taxels=11, value=11)
        peeled = fieldfit.peel_field(single, (4.7, 5.0))
        self.assertEqual((peeled["rows"], peeled["cells"]), (2, ((0, 4), (0, 4))))
        self.assertTrue(fieldfit._convex([(1, 2), (0, 4), (0, 4)]))
        self.assertFalse(fieldfit._convex([(0, 1), (3, 4)]))
        self.assertFalse(fieldfit._convex([(0, 4), (2, 4), (0, 4)]))

    def test_a_field_whose_f_leaves_the_surface_is_peeled(self) -> None:
        data, selection, result, _ = _Fits.get(self, "right_triangle", FIELD)
        mesh = read_stl(data)
        from surface import api as api_module

        _, chart = api_module.selection_chart(mesh, selection)
        options = fit.parse_options(FIELD)
        bases = fit.choose_bases("auto", api_module.boundary_sides(mesh, chart), mesh, chart)
        obstacles = fit.surface_obstacles(mesh, chart, options)
        found = fieldfit.ordered(fieldfit.search_fields(chart, bases, options, fit.load_profile_cached("surface"), obstacles, []), True)
        # The symmetric field on the hypotenuse (section 22; since section 24 the second proposal, after the 595 on a leg).
        candidate = dict(next(found_one for found_one in found if found_one["symmetric"]))
        x, y = candidate["field_origin"]
        candidate["field_origin"] = (x, y - 1.0)  # F now crosses the exit edge
        rejected: dict = {}
        proposal, peeled = fieldfit.realize_field(candidate, chart, obstacles, options, fit.load_profile_cached("surface"), None, rejected)
        self.assertIsNone(proposal)
        self.assertIsNotNone(peeled)
        # A symmetric field (section 22): a row loses both its end cells.
        self.assertTrue(candidate["symmetric"])
        self.assertEqual((peeled["taxels"], peeled["peels"], peeled["symmetric"]), (candidate["taxels"] - 2, 1, True))
        self.assertTrue(fieldfit._convex(list(peeled["cells"])))
        asymmetric = dict(candidate, symmetric=False)
        peeled = fieldfit.realize_field(asymmetric, chart, obstacles, options, fit.load_profile_cached("surface"), None, {})[1]
        self.assertEqual((peeled["taxels"], peeled["peels"]), (candidate["taxels"] - 1, 1))
        # The third build is the last: a field peeled twice is not peeled again.
        twice = dict(candidate, peels=fieldfit.MAX_ATTEMPTS - 1)
        self.assertEqual(fieldfit.realize_field(twice, chart, obstacles, options, fit.load_profile_cached("surface"), None, rejected), (None, None))
        self.assertEqual(rejected, {"the taxel field leaves the surface": 1})


class DiagonalFootprintTests(unittest.TestCase):
    """The P5c carry-overs: field_footprint and E_BOARD_SIZE measure a diagonal Row bus on its boards."""

    PROFILE = load_profile("surface_matrix_v1")

    def _design(self, rows: int, columns: int, pitch: float, sides: str = "both", mask=None, role: str = "rows_top") -> dict:
        design = fit.design_for(rows, columns, pitch, pitch, fit.parse_options({}), role, "tight", (20.0, 12.0), mask)
        design["routing"]["row_sides"] = sides
        return design

    def test_the_footprint_is_the_diagonal_boards(self) -> None:
        cases = [self._design(12, 32, 2.0), self._design(9, 7, 1.5, "left", role="columns_top"), self._design(5, 8, 2.0, "right", mask=[[3, 6], [2, 7], [1, 8], [1, 8], [2, 7]])]
        for request in cases:
            result = generate_design(request)
            self.assertTrue(result["ok"], result["validation"]["errors"][:3])
            footprint = field_footprint(result["design"], self.PROFILE)
            for key, board in result["boards"].items():
                with self.subTest(sides=request["routing"]["row_sides"], board=key):
                    active, tail = board["grid_registration"]["active_region"], board["tail"]["bounds"]
                    root = tail["y"] + tail["height"]
                    above = [point for point in board["outline"]["points"] if point[1] >= root - 1e-9]
                    measured = {
                        "left": round(active["x"] - min(x for x, _ in above), 6),
                        "right": round(max(x for x, _ in above) - active["x"] - active["width"], 6),
                        "top": round(max(y for _, y in above) - active["y"] - active["height"], 6),
                        "bottom": round(active["y"] - root, 6),
                    }
                    self.assertEqual({side: footprint[key][side] for side in measured}, measured)
                    self.assertEqual(footprint[key]["tail"], {"x": round(tail["x"] - active["x"], 6), "width": tail["width"], "length": tail["height"]})
                    if "mask" in request["matrix"]:
                        ring = footprint["mask"][key]["outline"]
                        self.assertEqual(min(y for _, y in ring), round(root - active["y"], 6))
                        inside = [p for p in above if p[1] > root + 1e-6]
                        self.assertTrue(all(point_in_polygon((x - active["x"], y - active["y"]), ring) or
                                            min(math.dist((x - active["x"], y - active["y"]), q) for q in ring) < 1e-5 for x, y in inside))
        # The straight channel's plans differ: the bus's Row root lies far deeper.
        straight = dict(cases[0], routing={k: v for k, v in cases[0]["routing"].items() if k != "row_sides"})
        self.assertGreater(field_footprint(check_design(cases[0])["design"], self.PROFILE)["row"]["bottom"],
                           field_footprint(check_design(straight)["design"], self.PROFILE)["row"]["bottom"] + 3.0)

    def test_board_size_measures_the_diagonal_boards(self) -> None:
        # 64 x 8 at 7.235 mm: the bus's Row board is 490.076 mm long (490.075 before diagonal-bus/10 centred its Row
        # tail), over the 234 x 490 mm maximum (before phase P5d
        # validation passed such a design and the DRC refused the outline).  The advice is the bus's own, verified on its
        # boards.  The size is the bus's boards', not the straight Row channel's plan: at 7.232 mm the straight channel is
        # 490.112 mm long and refused, while the bus builds at 489.883 mm (diagonal-bus/8: one outline down to the tail
        # roots, the Row fans at 85 degrees beside the capped Column V).
        design = self._design(64, 8, 7.235)
        errors = check_design(design)["validation"]["errors"]
        row = next(e for e in errors if e["message"].startswith("The row FPC outline"))
        self.assertEqual((row["code"], row["field"]), ("E_BOARD_SIZE", "tail.top_length_mm"))
        self.assertIn("would be 70.263 x 490.076 mm (the diagonal Row bus)", row["message"])
        self.assertIn("Any one of: tail.top_length_mm <= 19.9237 mm; matrix.pitch_y_mm <= 7.2337 mm; matrix.rows <= 63.", row["message"])
        close = self._design(64, 8, 7.232)
        straight = dict(close, routing={k: v for k, v in close["routing"].items() if k != "row_sides"})
        self.assertEqual([e["code"] for e in check_design(straight)["validation"]["errors"]], ["E_BOARD_SIZE"])
        self.assertTrue(check_design(close)["ok"], check_design(close)["validation"]["errors"][:2])
        for section, key, value in (("tail", "top_length_mm", 19.9237), ("matrix", "pitch_y_mm", 7.2337)):
            with self.subTest(advice=key):
                fixed = copy.deepcopy(design)
                fixed[section][key] = value
                built = generate_design(fixed)
                self.assertTrue(built["ok"], built["validation"]["errors"][:2])
                ys = [y for _, y in built["boards"]["row"]["outline"]["points"]]
                self.assertLessEqual(max(ys) - min(ys), 490.0)
        # A bus that fits builds as before.
        self.assertTrue(check_design(self._design(32, 32, 2.0))["ok"])


class DeterminismTests(unittest.TestCase):
    def test_the_field_fit_code_sums_no_floats_and_iterates_no_sets(self) -> None:
        import inspect

        functions = [value for _, value in sorted(vars(fieldfit).items()) if inspect.isfunction(value) and value.__module__ == fieldfit.__name__]
        functions += [value for _, value in sorted(vars(fieldfit._Search).items()) if inspect.isfunction(value)]
        from engine import layout
        from exporters import direct_gerber

        functions += [layout._diagonal_footprint, layout._ring_above, layout._diagonal_size_errors, place.readout,
                      direct_gerber._row_contact_notes, direct_gerber._row_contact_phrases, direct_gerber._row_bus_fold,
                      place.row_pin_order, place.map_options]
        self.assertGreater(len(functions), 40)
        for function in functions:
            with self.subTest(function=f"{function.__module__}.{function.__qualname__}"):
                self.assertEqual(_determinism_problems(function), [])


class FieldWebClientTests(unittest.TestCase):
    """What the browser sends and shows for a field-only fit (tools/browser/cad_checks.py runs it)."""

    def setUp(self) -> None:
        self.app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.main = (ROOT / "web" / "cad" / "main.js").read_text(encoding="utf-8")
        self.html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    def _options(self, select_id: str) -> list:
        tag = re.search(rf'<select id="{select_id}"[^>]*>(.*?)</select>', self.html, re.S)
        self.assertIsNotNone(tag, select_id)
        return re.findall(r'<option value="([^"]*)">', tag.group(1))

    def test_generate_posts_the_row_sides_on_every_template(self) -> None:
        # The proposal's routing.row_sides goes with the form (else the build is not the proposal's), and since
        # P5-diagonal-bus.md section 18 the generic template takes the key too (its default both, the diagonal Row bus):
        # the Row traces select is shown and sent in both modes, its Straight channel as "channel" (the surface
        # template normalizes it away, so a whole-board proposal keeps its build id).
        body = re.search(r"function formBody\(\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn("const sides = rowSides();\n    if (sides) body.routing = {row_sides: sides};", body)
        sides = re.search(r"function rowSides\(\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn('return value("rowSides") || null;', sides)
        self.assertNotIn("MASK_TEMPLATE", sides)
        form = re.search(r"function setForm\(design\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn('rowSides: routing.row_sides ?? "channel"', form)
        self.assertNotIn("rowSides", re.search(r"function payload\(\) \{(.*?)\n  \}", self.app, re.S).group(1))
        visible = re.search(r"function syncRowSides\(\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn('$("rowSidesRow").hidden = false;', visible)
        self.assertIn('$("rowSides").disabled = false;', visible)
        template = re.search(r"function useTemplate\(id, entry\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn("syncRowSides();", template)
        # The form's select: the straight channel and the engine's sides, as routing.row_sides; shown from the start.
        from engine.core import ROW_SIDES_VALUES
        from engine.diagonal import CHANNEL, ROW_SIDES

        self.assertRegex(self.html, r'<select id="rowSides" name="row_sides" data-field="routing.row_sides">')
        self.assertEqual(self._options("rowSides"), [CHANNEL, *sorted(ROW_SIDES, key=["both", "left", "right"].index)])
        self.assertEqual(set(self._options("rowSides")), set(ROW_SIDES_VALUES))
        self.assertRegex(self.html, r'<div class="two-col" id="rowSidesRow">')
        self.assertRegex(self.html, r'<p class="hint" id="rowSidesHint">')

    def test_the_containment_and_row_traces_selects(self) -> None:
        # The fit's choices, the server's default first (test_surface_web checks every Configure select so).
        self.assertEqual(self._options("cadContainment"), ["field", "board"])
        self.assertEqual(self._options("cadRowSides"), ["both", "left", "right"])
        self.assertEqual((fit.DEFAULT_OPTIONS["containment"], fit.DEFAULT_OPTIONS["row_sides"]), ("field", "both"))
        # Containment is always the user's (CAD mode has no Field shape and no Board rules since section 26.16; a border
        # alone holds it at Field only); Row traces apply to Field only.
        sync = re.search(r"function syncContainment\(\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertNotIn("cadShape", sync)
        self.assertIn('const channel = containment.value !== "field";', sync)
        self.assertIn("  sides.disabled = channel;", sync)
        self.assertIn('$("cadContainment").addEventListener("change", syncContainment);', self.main)

    def test_the_proposal_card_and_the_flat_view(self) -> None:
        card = re.search(r"function renderCard\(\) \{(.*?)\n\}", self.main, re.S).group(1)
        for text in ("bus.tip_width_mm", "bus.band_mm", "report.row.on_surface", "report.column.on_surface", "overhang_mm"):
            self.assertIn(text, card)
        self.assertIn("renderCard();", re.search(r"function renderProposals\(\) \{(.*?)\n\}", self.main, re.S).group(1))
        self.assertIn('<section class="cad-card" id="cadProposalCard" aria-labelledby="cadProposalCardTitle" hidden>', self.html)
        # The flat view draws each board dotted, then solid clipped to the surface (outline less holes, even-odd).
        flat = re.search(r"function renderFlat\(\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertIn('const board = (list, className) => [shape(list, `${className} is-off`), shape(list, className, {"clip-path": "url(#cadFlatOn)"})];', flat)
        self.assertIn('"clip-rule": "evenodd"', flat)
        self.assertIn('...board(framed.column, "flat-column"), ...board(framed.row, "flat-row")', flat)
        css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".cad-flat-svg .flat-row.is-off {", css)
        self.assertIn(".cad-flat-svg .flat-column.is-off {", css)


def _exhaustive_unturned(test: unittest.TestCase, name: str, options: dict, base) -> int:
    """The most taxels of an unturned field in the search's lattice universe: every exit of the base, every quarter
    phase and the centred one, every cap, no pruning (the reviews' reference)."""

    from surface import api as api_module

    data, selection, _, _ = _Fits.get(test, name, options, base)
    mesh = read_stl(data)
    _, chart = api_module.selection_chart(mesh, selection)
    parsed = fit.parse_options(options)
    bases = fit.choose_bases(base, api_module.boundary_sides(mesh, chart), mesh, chart)
    obstacles = fit.surface_obstacles(mesh, chart, parsed)
    shaped, rectangles = fieldfit.caps(parsed)
    pitch = parsed["pitch_mm"]
    width = fit._electrode(pitch, parsed["fill"])
    best = 0
    for side in bases:
        space = fill.FreeSpace(chart, fit.BaseFrame(side, 0.0), obstacles, parsed["edge_margin_mm"], side["edges"])
        for phase in fieldfit.quarter_phases(pitch) + [fieldfit.centred_phase(space, pitch, width, 0.5)]:
            grid = fieldfit.lattice(space, pitch, width, 0.5, phase)
            if not grid["rows"] or not grid["columns"]:
                continue
            for rows_cap, columns_cap in shaped:
                best = max(best, fieldfit.search_shaped(grid, rows_cap, columns_cap, 0)[0])
            for rows_cap, columns_cap in rectangles:
                best = max(best, fieldfit.best_rectangle(grid["plain"], grid["up"], rows_cap, columns_cap, 0, grid["zones"])[0])
    return best


def _crossings(polygon: list, y: float) -> list:
    """The sorted x of a horizontal line's crossings with a polygon's edges (our own scanline)."""

    found = []
    for k in range(len(polygon)):
        (x0, y0), (x1, y1) = polygon[k - 1], polygon[k]
        if (y0 <= y < y1) or (y1 <= y < y0):
            found.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return sorted(found)


def _own_report(board: list, outline: list, holes: list, exits, centre: float, step: float = 0.02) -> dict:
    """Our own share on the surface (inside the outline, outside the holes, by scanlines) and the overhang: the farthest
    board corner, or point where the board's outline crosses the surface's lowest level, off the surface beside it (not
    past the exit under it, not below the surface's lowest point: the outline clipped there)."""

    ys = [p[1] for p in board]
    low, high = min(ys), max(ys)
    count = int(math.ceil((high - low) / step))
    total = on = bare = 0.0
    for k in range(count):
        y = low + (k + 0.5) * (high - low) / count
        spans = _crossings(board, y)
        surface = sorted(_crossings(outline, y) + [x for hole in holes for x in _crossings(hole, y)])
        rim = _crossings(outline, y)
        for a0, a1 in zip(spans[::2], spans[1::2]):
            total += a1 - a0
            for s0, s1 in zip(surface[::2], surface[1::2]):
                on += max(0.0, min(a1, s1) - max(a0, s0))
            for s0, s1 in zip(rim[::2], rim[1::2]):
                bare += max(0.0, min(a1, s1) - max(a0, s0))
    lowest = min(p[1] for p in outline)
    side = {"left": 0.0, "right": 0.0}
    crossings = [(a[0] + (b[0] - a[0]) * (lowest - a[1]) / (b[1] - a[1]), lowest) for a, b in zip(board, board[1:] + board[:1])
                 if (a[1] - lowest) * (b[1] - lowest) < 0]
    for p in board + crossings:
        exit_y = exits.exit_y(p[0])
        if point_in_polygon(p, outline) or (exit_y is not None and p[1] <= exit_y + 1e-6) or p[1] < lowest - 1e-6:
            continue
        distance = min(_segment_distance(p, outline[k - 1], outline[k]) for k in range(len(outline)))
        key = "left" if p[0] < centre else "right"
        side[key] = max(side[key], distance)
    return {"on_surface": on / total, "without_holes": bare / total, **side}


def _segment_distance(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


class ReviewFixTests(unittest.TestCase):
    """The P5d/P5e reviews' findings (2026-10-22)."""

    def test_a_turned_proposal_beats_every_unturned_field_by_three_percent(self) -> None:
        # The review: with a named exit the turned frames were searched before the unturned quarter phases and pruned
        # them, so a turned field 0-1 % above the best unturned one was proposed (the triangle's 45 at -20 degrees
        # against 45 unturned).  Now every turned proposal has 3 % more taxels than the best unturned field of the whole
        # lattice universe, and the unturned search finds that field exactly (rotation none's top proposal).
        for name, pitch, base in (("tri_a", 4.0, {"side": 2}), ("equilateral", 2.5, {"side": 0}), ("equilateral", 3.0, {"side": 0}),
                                  ("parallelogram", 3.0, "auto")):
            with self.subTest(plate=name, pitch=pitch, base=base):
                options = dict(FIELD, pitch_mm=pitch)
                result = _Fits.get(self, name, options, base)[2]
                square = _Fits.get(self, name, dict(options, rotation="none"), base)[2]
                unturned = _exhaustive_unturned(self, name, options, base)
                # The search finds the exhaustive optimum (rotation none's top proposal, or since section 22 the larger
                # asymmetric alternative after a symmetric field within 3 % of it).
                best = max(proposal["metrics"]["taxels"] for proposal in square["proposals"])
                self.assertGreaterEqual(best, unturned)
                if best > unturned:
                    # A lattice centred on a symmetric exit's axis (section 22) holds one more than the quarter and centred
                    # phases: the equilateral at 2.5 mm since section 24 (224 symmetric against 223).
                    self.assertTrue(any(p["metrics"]["taxels"] == best and p["metrics"]["symmetry"]["field"] for p in square["proposals"]))
                first = square["proposals"][0]["metrics"]
                # Since section 26.17 a symmetric face's symmetric field first (since 26.19 within 20 % of the most: the
                # equilateral at 3 mm, its symmetric tip-first 148 on side 0).
                self.assertTrue(first["taxels"] >= unturned or first["symmetry"]["field"], first)
                for proposal in result["proposals"]:
                    if proposal["metrics"]["angle_deg"] != 0.0:
                        self.assertGreaterEqual(proposal["metrics"]["taxels"] * fieldfit.TURN_GAIN[1], unturned * fieldfit.TURN_GAIN[0])
                if result["proposals"][0]["metrics"]["angle_deg"] == 0.0:
                    self.assertEqual(_shapes(result)[0], _shapes(square)[0])
        # A turned field that does beat it by 3 % is proposed: the slanted strip (no symmetric exit), 74 at -30 degrees
        # against 54 (test_a_turned_proposal_maps).  The soft finger's 32-row cap took 417 at 30 degrees against 384 (418
        # since section 21); its face is symmetric about its exit, so since section 22 that exit is not turned and the
        # symmetric 32 x 12 = 384 is the proposal.
        if SOFT_FINGER.exists():
            first = _Fits.get(self, "soft_finger", dict(FIELD, max_rows=32))[2]["proposals"][0]["metrics"]
            self.assertEqual((first["taxels"], abs(first["angle_deg"]), first["symmetry"]["field"]), (384, 0.0, True))

    def test_narrow_and_small_surfaces_are_never_worse_than_the_board_fit(self) -> None:
        # Phase 0 used to fail the usable edge by its 0.1 um inset and p/2 overshot the slack, so a 3.2 mm strip had no
        # field (and a false "no taxel field fits") where the board fit proposed 3 taxels.
        for name, pitch, least in (("strip_2.6", 2.0, 19), ("strip_3.2", 2.0, 29), ("square_3", 2.0, 1), ("triangle_8", 3.0, 1)):
            with self.subTest(plate=name, pitch=pitch):
                field = _Fits.get(self, name, dict(FIELD, pitch_mm=pitch))[2]
                board = _Fits.get(self, name, dict(BOARD, pitch_mm=pitch))[2]
                self.assertIsInstance(field, dict, field)
                best = max(p["metrics"]["taxels"] for p in field["proposals"])
                self.assertGreaterEqual(best, least)
                if isinstance(board, dict):
                    self.assertGreaterEqual(best, max(p["metrics"]["taxels"] for p in board["proposals"]))
        # Phase 0 puts the first crossing's grown strip on the usable edge.
        from surface import api as api_module

        data, selection, _, _ = _Fits.get(self, "right_triangle", FIELD)
        mesh = read_stl(data)
        _, chart = api_module.selection_chart(mesh, selection)
        options = fit.parse_options(dict(FIELD, edge_margin_mm=0.3))
        side = fit.choose_bases("auto", api_module.boundary_sides(mesh, chart), mesh, chart)[0]
        space = fill.FreeSpace(chart, fit.BaseFrame(side, 0.0), fit.surface_obstacles(mesh, chart, options), 0.3, side["edges"])
        grid = fieldfit.lattice(space, 2.0, 1.4, 0.5, (0.0, 0.0))
        self.assertAlmostEqual(grid["x0"] - space.x0, 0.3 + fit.EDGE_INSET_MM + 0.5, places=9)
        self.assertAlmostEqual(grid["y0"] - space.y0, 0.3 + fit.EDGE_INSET_MM + 0.5, places=9)

    def test_auto_finds_the_best_exit(self) -> None:
        # The review: the right triangle at 5 mm gave 78 with base auto, 81 on its hypotenuse alone (that frame kept
        # nothing at the coarse phases, so its quarter phases never ran).  Every exit now gets its quarter phases.
        options = dict(FIELD, pitch_mm=5.0)
        auto = _Fits.get(self, "right_triangle", options)[2]
        sides = sorted({base["side"] for base in auto["bases"]})
        self.assertEqual(len(sides), 3)
        named = [_Fits.get(self, "right_triangle", options, {"side": side})[2]["proposals"][0]["metrics"]["taxels"] for side in sides]
        self.assertEqual(max(p["metrics"]["taxels"] for p in auto["proposals"]), max(named))
        # Since section 26.17 the hypotenuse's symmetric 9 x 17 = 81 first (its own fit's first), the legs' 91 after it (12 %
        # more: within section 26.19's 20 %).
        self.assertEqual((auto["proposals"][0]["metrics"]["taxels"], auto["proposals"][0]["metrics"]["symmetry"]["field"]), (81, True))
        self.assertEqual(named, [91, 81, 91])

    def test_the_bases_tried_are_listed(self) -> None:
        # The review: details.bases was empty with E_SURFACE_NO_FIT under field containment, and on success the turned
        # frames that kept nothing were left out.  Every frame searched is listed, with the fields it kept.
        error = _Fits.get(self, "sliver", FIELD)[2]
        self.assertIsInstance(error, SurfaceError)
        self.assertIn("no taxel field fits the surface", error.message)
        self.assertTrue(error.details["bases"])
        self.assertTrue(all(base["field_candidates"] == 0 for base in error.details["bases"]))
        bases = _Fits.get(self, "right_triangle", FIELD)[2]["bases"]
        angles = sorted({base["angle_deg"] for base in bases})
        self.assertEqual(angles, sorted({0.0, *fit.ROTATION_STEPS_DEG}))
        self.assertIn(0, [base["field_candidates"] for base in bases])

    def test_the_narrow_tip_chooses_the_exit_not_the_field(self) -> None:
        # The review: with several exits the narrow tip sorted every field, so base auto put a masked 254 before the
        # full 256 of the same readout on the same exit, and proposed both.  The tip now orders the exits only.
        options = dict(FIELD, reader="16x16")
        auto = _Fits.get(self, "right_triangle", options)[2]
        side = auto["proposals"][0]["placement"]["base_side"]
        named = _Fits.get(self, "right_triangle", options, {"side": side})[2]
        self.assertEqual(_shapes(auto)[0], _shapes(named)[0])
        readouts = [(rows, columns) for rows, columns, _ in _shapes(auto)]
        self.assertEqual(len(readouts), len(set(readouts)))

    def test_both_tails_end_together_the_extension_past_the_edge(self) -> None:
        # The review: field-only tails ended 36-41 mm past a 20 mm extension, 5-9 mm apart.  Now the nearer end lies the
        # extension past the edge under it, or farther where the shortest tail (7.5 mm) ends farther, and both tails end
        # there, on one line across the boards (P5-diagonal-bus.md section 27.3: their roots on one level, both as long),
        # the other at least as far past the edge under it.
        for extension, sides in ((20.0, "both"), (20.0, "left"), (40.0, "both")):
            with self.subTest(extension=extension, sides=sides):
                data, selection, result, _ = _Fits.get(self, "right_triangle", dict(FIELD, tail_extension_mm=extension, row_sides=sides))
                proposal = result["proposals"][0]
                metrics = proposal["metrics"]
                mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
                reach = {key: next(r for r in mapped["verification"] if r["rule"] == f"{key}_tail_reach")["measured"] for key in ("row", "column")}
                self.assertEqual(metrics["row_tail_mm"], metrics["column_tail_mm"])
                self.assertAlmostEqual(min(reach.values()), metrics["tail_reach_mm"], delta=2e-3)
                self.assertGreaterEqual(metrics["tail_reach_mm"], extension - 1e-3)
                shortest = min(metrics["row_tail_mm"], metrics["column_tail_mm"])
                self.assertTrue(abs(metrics["tail_reach_mm"] - extension) < 2e-3 or shortest == fit.TAIL_MIN_MM["surface"], (metrics, shortest))
                if extension == 40.0:
                    self.assertAlmostEqual(metrics["tail_reach_mm"], 40.0, delta=2e-3)

    def test_the_overhang_is_across_where_the_surface_is(self) -> None:
        # The review: left and right counted every board corner off the surface, the tails' below the base edge too (the
        # disk's Row FPC "right 38.21" was its tail's end beside the arc exit, the soft finger's "right 46.2" its tail
        # beside the Column tail).  Now the corners below the surface's lowest point do not count; against our own
        # distances, and the share against our own scanlines with the holes left out.
        for name in ("disk", "holed_plate"):
            data, selection, result, _ = _Fits.get(self, name, FIELD)
            proposal = result["proposals"][0]
            frame = _frame(proposal["placement"])
            from surface import api as api_module

            _, chart = api_module.selection_chart(read_stl(data), selection)
            outline = [frame.to_base(p) for p in chart.outline()]
            holes = [[frame.to_base(chart.uv[v]) for v in loop] for index, loop in enumerate(chart.loops) if index != chart.outer]
            exits = fit.ExitOutline(outline, proposal["placement"]["exit_edges"])
            field = [frame.to_base(p) for p in proposal["outlines_uv"]["field"]]
            centre = (min(p[0] for p in field) + max(p[0] for p in field)) / 2
            for key in ("row", "column"):
                with self.subTest(plate=name, board=key):
                    board = [frame.to_base(p) for p in proposal["outlines_uv"][key]]
                    own = _own_report(board, outline, holes, exits, centre)
                    report = proposal["metrics"]["routing_on_surface"][key]
                    self.assertAlmostEqual(report["on_surface"], own["on_surface"], delta=1.5e-3)
                    for side in ("left", "right"):
                        self.assertAlmostEqual(report["overhang_mm"][side], own[side], delta=2e-3)
                    tail_end = min(p[1] for p in board)
                    self.assertLess(tail_end, min(p[1] for p in outline) - 5.0)  # the tails lie below, and do not count
                    if name == "holed_plate" and key == "row":
                        self.assertGreater(own["without_holes"] - own["on_surface"], 3e-3)  # the hole matters

    def test_the_row_pins_follow_the_scan_order(self) -> None:
        # The review: with Scan order Reverse the map's readout (and the browser's notes) listed the contact positions
        # as pins (ROW_01 first) while pin 1 carries ROW_02.  The readout's row_pin_order is by pin, from the pads.
        data, selection, result, _ = _Fits.get(self, "right_triangle", FIELD)
        proposal = result["proposals"][0]
        design = copy.deepcopy(proposal["design"])
        design["channel_order"] = {"rows": "descending", "columns": design.get("channel_order", {}).get("columns", "ascending")}
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": design}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        order, pins = mapped["readout"]["row_contact_order"], mapped["readout"]["row_pin_order"]
        self.assertEqual(order[:2], ["ROW_01", "ROW_03"])
        self.assertEqual(pins, list(reversed(order)))
        self.assertEqual(pins[0], "ROW_02")
        self.assertEqual({r["row_net"]: r["row_pin"] for r in mapped["taxels"]}["ROW_02"], 1)

    def test_a_straight_design_maps_with_field_containment(self) -> None:
        # The review: options {containment: field} on a straight-channel design crashed (KeyError active_outline, a
        # 500 over HTTP).  F of a full field is its active region.  (A whole-board full rectangle; shape rectangle's before
        # section 26.16.)
        data, selection, result, _ = _Fits.get(self, "rectangle", BOARD)
        proposal = next(p for p in result["proposals"] if design_mask(p["design"]) is None)
        self.assertNotIn("row_sides", proposal["design"]["routing"])
        for options in ({"containment": "field"}, {"containment": "field", "shape": "fill"}):
            with self.subTest(options=options):
                mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"], "options": options}, data)
                self.assertEqual([r["rule"] for r in mapped["verification"]], FIELD_RULES)
                self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
                self.assertIn("routing_on_surface", mapped)

    def test_the_edge_warning_sees_a_fillet_and_the_base_edge(self) -> None:
        # The review: the base edge was skipped (the bands, the bus and the fan-out cross it under field containment),
        # and only a boundary edge's own bend was measured (a tangent fillet's first edge shows about twice its radius).
        from surface import api as api_module, bend

        data, selection, result, _ = _Fits.get(self, "bracket", FIELD)
        proposal = result["proposals"][0]
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        warning = next(w for w in mapped["routing_on_surface"]["warnings"] if w["code"] == "W_BAND_EDGE_RADIUS")
        self.assertAlmostEqual(warning["side_mm"], 0.795, delta=0.002)  # the R0.8 fillet's inner edges
        self.assertIn("run it straight off the edge", warning["message"])
        mesh = read_stl(data)
        _, chart = api_module.selection_chart(mesh, selection)
        inside = set(chart.facets)
        first = min(bend.edge_radius(mesh, f, g, 1.1) for f in sorted(inside) for g in sorted(mesh.neighbors[f]) if g not in inside)
        self.assertGreater(first, 1.5)  # the fillet's first edge alone would not warn
        # The plates' square base edges: a board crossing them is told so.
        data, selection, result, _ = _Fits.get(self, "right_triangle", FIELD)
        proposal = result["proposals"][0]
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        warnings = {w["board"]: w for w in mapped["routing_on_surface"]["warnings"] if w["code"] == "W_BAND_EDGE_RADIUS"}
        # Both boards cross the side edges too: over the field the Column board has the Row board's outline (its bands).
        self.assertEqual((warnings["column"]["base_mm"], warnings["column"]["side_mm"]), (0.0, 0.0))
        self.assertEqual((warnings["row"]["base_mm"], warnings["row"]["side_mm"]), (0.0, 0.0))

    def test_the_search_stops_at_its_work_budget(self) -> None:
        # The review: on a 60 x 40 plate with a round hole at 1.5 mm the DP ran on almost every window (1704 runs,
        # 29-35 s against the board fit's 1-2 s).  The windows of a lattice larger than the caps now wait for the whole
        # lattice's DP, the DP stops once no state can still beat the threshold, and a deterministic count of its work
        # bounds the search (the meter below, exact): the plate keeps its fields at about 3 times the board fit's cost
        # (3.1 here, 3.6 on a GitHub runner 2.2 times slower, 2026-10-30, where 3 x the board + 1 s was too tight).  The
        # bound of 5 x + 1 s leaves the machines their spread and still fails the review's 15-25 times.
        # Section 26's tip passes (about 7 % of this fit) have their own meter, TIP_WORK_BUDGET cells per pass, and
        # complete here within it (deterministic): the bound is on the search, their time measured apart.  CPU time, the
        # least of two interleaved fits each (_timed_fits: once over the bound in wall-clock time at a load of about 40).
        options = dict(FIELD, pitch_mm=1.5)
        data, selection, result, _ = _Fits.get(self, "round_hole", options)
        # Section 26.17 put the plate's symmetric 390 first (around the hole), its larger fields (589) after it; since
        # section 26.19 (the user's threshold of 20 %: the 589 holds 51 % more) its turned 41 x 43 = 624 first.
        self.assertGreaterEqual(max(p["metrics"]["taxels"] for p in result["proposals"]), 525)
        self.assertEqual((result["proposals"][0]["metrics"]["taxels"], result["proposals"][0]["metrics"]["symmetry"]["field"]), (624, False))
        _Fits.get(self, "round_hole", dict(BOARD, pitch_mm=1.5))
        seconds, passes, results = _timed_fits(data, selection, {"board": dict(BOARD, pitch_mm=1.5), "field": options})
        timed = results["field"]
        self.assertLess(seconds["field"] - passes["field"], 5.0 * seconds["board"] + 1.0, (seconds, passes))
        self.assertEqual(passes["board"], 0.0)
        self.assertTrue(all(base["tip_complete"] for base in timed["bases"] if "tip_complete" in base))
        self.assertTrue(any("tip_work" in base for base in timed["bases"]))
        # The meter: the fixtures' searches stay under the budget (exact), a small budget stops the search.
        searches = []

        class Recorded(fieldfit._Search):
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                searches.append(self)

        saved = (fieldfit._Search, fieldfit.WORK_BUDGET)
        self.assertEqual(saved[1], 3_000_000)
        try:
            fieldfit._Search = Recorded
            for name in ("disk", "holed_plate"):
                plate, chosen, _, _ = _Fits.get(self, name, FIELD)
                fit.fit_route({"selection": chosen, "base": "auto", "options": FIELD}, plate)
                self.assertLess(searches[-1].meter[0], saved[1])
            # A small budget on the round-hole plate's lattices, larger than the caps: the search stops at the next
            # window past it (1496 cells past 300 000 here; with the windows unchecked a lattice runs on, 62 336 past),
            # and still proposes the fields found.
            fieldfit.WORK_BUDGET = 300_000
            small = fit.fit_route({"selection": selection, "base": "auto", "options": options}, data)
            self.assertTrue(small["proposals"])
            self.assertGreaterEqual(searches[-1].meter[0], 300_000)
            self.assertLess(searches[-1].meter[0], 300_000 + 32 * 32 * 32)
        finally:
            fieldfit._Search, fieldfit.WORK_BUDGET = saved

    def test_the_early_exit_holds_near_the_threshold(self) -> None:
        # The DP's early exit bounds each state by the runs above it within the ends its phase allows: it gives the
        # field exactly when it beats the threshold, nothing otherwise, on whole grids and windows (a reference DP).
        rng = random.Random(13)
        for trial in range(120):
            plain, up = _random_grid(rng, rng.randint(3, 9), rng.randint(3, 9), rng.choice((0.6, 0.8, 0.9, 0.97)), sparse=rng.random() < 0.5)
            rows, columns = len(plain), len(plain[0])
            c0 = rng.randint(0, columns - 1)
            c1 = rng.randint(c0, columns - 1)
            r0 = rng.randint(0, rows - 1)
            r1 = rng.randint(r0, rows - 1)
            clip = [[(min(end, c1) - c0 if end >= a + c0 else -1) for a, end in enumerate(row[c0:c1 + 1])] for row in plain[r0:r1 + 1]]
            clip_up = [[(min(end, c1) - c0 if end >= a + c0 else -1) for a, end in enumerate(row[c0:c1 + 1])] for row in up[r0:r1 + 1]]
            best = _reference(clip, clip_up)
            for threshold in sorted({0, max(best - 2, 0), max(best - 1, 0), best, best + 1}):
                with self.subTest(trial=trial, threshold=threshold):
                    self.assertEqual(fieldfit.best_convex(plain, up, c0, c1, r0, r1, threshold)[0], best if best > threshold else 0)
            # And the runs beside a column, by brute force.
            tops = fieldfit._row_tops(plain[r0], c0, c1)
            right_of, left_of = fieldfit._longest_beside(tops)
            runs = [(a, b) for a in range(len(tops)) for b in range(a, len(tops)) if tops[a] >= b]
            self.assertEqual(right_of, [max([b - a + 1 for a, b in runs if a >= k] or [0]) for k in range(len(tops))])
            self.assertEqual(left_of, [max([b - a + 1 for a, b in runs if b <= k] or [0]) for k in range(len(tops))])

    def test_the_rectangle_search_with_a_threshold(self) -> None:
        rng = random.Random(17)
        for trial in range(200):
            plain, up = _random_grid(rng, rng.randint(1, 5), rng.randint(1, 6), 0.8, sparse=True)
            caps = (rng.randint(1, 5), rng.randint(1, 6))
            want = _brute(plain, up, caps, rectangle=True)
            for threshold in sorted({0, max(want - 1, 0), want}):
                with self.subTest(trial=trial, threshold=threshold):
                    found = fieldfit.best_rectangle(plain, up, caps[0], caps[1], threshold)
                    self.assertEqual(found[0], want if want > threshold else 0)
                    if found[0]:
                        _, height, width, row, a = found
                        self.assertEqual(height * width, found[0])
                        self.assertTrue(all((plain if j == row + height - 1 else up)[j][a] >= a + width - 1 for j in range(row, row + height)))


class ReviewWebClientTests(unittest.TestCase):
    """The browser client's fixes of the P5d/P5e reviews (tools/browser/cad_checks.py drives them)."""

    def setUp(self) -> None:
        self.app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.main = (ROOT / "web" / "cad" / "main.js").read_text(encoding="utf-8")
        self.html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    def test_a_full_field_is_not_called_masked(self) -> None:
        # A diagonal Row bus records its full field's mask too: the badge and the CSV's readout rows are a masked
        # field's only (the default soft finger's 59 x 12 read "708 of 59 x 12 taxels active (masked field ...)").
        badge = re.search(r"function maskBadge\(result\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn("if (!mask || !(registration.active_taxel_count < mask.rows * mask.columns)) return null;", badge)
        csv = re.search(r"function csvText\(map\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertIn("if (!map.readout || !(map.readout.active < map.readout.positions)) return", csv)

    def test_the_row_pins_come_from_the_pads(self) -> None:
        # Scan order Reverse puts ROW_02 on pin 1: the map panel and the proposal card list the Row nets by pin (the stacked
        # view's note, which listed them from the pads too, went with its notes on 2026-11-06).
        self.assertNotIn("function rowPinOrder(", self.app)
        verify = re.search(r"function renderVerification\(\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertIn("const order = cad.map.readout?.row_pin_order || cad.map.readout?.row_contact_order;", verify)
        card = re.search(r"function renderCard\(\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertIn("const order = bus.row_pin_order || bus.row_contact_order || [];", card)
        # Short lists name every item when nothing would be left out (3 rows read "ROW_01, ROW_03, ROW_02, …, ROW_03").
        self.assertIn("const shortList = items => (items.length > 6 ? `${items.slice(0, 3).join(\", \")}, …, ${items.slice(-2).join(\", \")}` : items.join(\", \"));", self.main)
        self.assertNotIn("order.slice(0, 3)", self.main)

    def test_generate_waits_for_a_new_fit_when_the_settings_changed(self) -> None:
        # The review: after a fit with Row traces Both, Left and Generate built Both ("10 of 10 checks pass").
        generate = re.search(r"function renderGenerate\(\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertIn("button.disabled = !proposal || Boolean(cad.pendingBuild) || stale;", generate)
        stale = re.search(r"function fitStale\(\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertIn("return invalid.length > 0 || [...keys].some(key => options[key] !== cad.fitOptions[key]);", stale)
        self.assertIn('$("cadConfig").addEventListener("change", onConfigChange);', self.main)
        self.assertIn('$("cadConfig").addEventListener("input", onConfigChange);', self.main)

    def test_one_map_request_at_a_time(self) -> None:
        # The review: Fit again after a Generate sent the preview and the build's map together, and the server, which
        # takes one CAD request at a time, answered 503 ("The server is busy; retrying in 1 s").
        choose = re.search(r"function chooseProposal\(index, \{look = false\} = \{\}\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertIn("mapBuild(cad.lastResult, {look});\n  else previewProposal({look});", choose)

    def test_the_configure_step_says_why(self) -> None:
        # Disabled controls give their reason (a border holding Containment at Field only; the Surface board rules' reason
        # is gone with the Board rules, section 26.16), the tail extension takes the server's range, and Row traces show
        # the straight channel under Whole board.
        sync = re.search(r"function syncContainment\(\) \{(.*?)\n\}", self.main, re.S).group(1)
        self.assertIn("so while it is used Containment is Field only", sync)
        self.assertNotIn("Board rules", sync)
        self.assertIn("its 0.5 mm margin may leave the surface by up to 0.5 mm; the taxels never do", sync)
        self.assertIn("Left and right are seen from outside", sync)
        self.assertIn('<option value="channel" disabled>Straight channel (Whole board)</option>', self.html)
        low, high = fit.TAIL_REACH_MIN_MM, fit.TAIL_EXTENSION_MAX_MM
        self.assertIn(f'id="cadTailExtension" data-option="tail_extension_mm" value="20" min="{low:g}" max="{high:g}"', self.html)
        with self.assertRaises(SurfaceError):
            fit.parse_options({"tail_extension_mm": low - 0.5})
        self.assertEqual(fit.parse_options({"tail_extension_mm": high})["tail_extension_mm"], high)


# --------------------------------------------------------------------------
# The corner tolerance (P5-diagonal-bus.md section 16; its rectangle preference and rectangles with field containment gone
# with section 26.16)
# --------------------------------------------------------------------------


def _box_distance(p, a, b) -> float:
    """Our own: the least ``max(|dx|, |dy|)`` from a point to a segment (a convex function of the segment's parameter,
    found by ternary search)."""

    low, high = 0.0, 1.0
    value = lambda t: max(abs(p[0] - a[0] - t * (b[0] - a[0])), abs(p[1] - a[1] - t * (b[1] - a[1])))
    for _ in range(100):
        first, second = low + (high - low) / 3, high - (high - low) / 3
        if value(first) <= value(second):
            high = second
        else:
            low = first
    return min(value(0.0), value(1.0), value((low + high) / 2))


def _segments_cross(polygon, outline) -> bool:
    from engine.geometry import segments_intersect

    return any(segments_intersect(polygon[k - 1], polygon[k], outline[m - 1], outline[m]) for k in range(len(polygon)) for m in range(len(outline)))


def _corner_problems(data: bytes, selection: dict, proposal: dict) -> list:
    """Our own check of a field-only proposal: P (the taxels' region) wholly inside the surface's outline, and F's
    corners off it by at most 0.5 mm across x and across y."""

    generated = generate_design(proposal["design"])
    origin = proposal["placement"]["field_origin_base"]
    frame = _frame(proposal["placement"])
    outline = [frame.to_base(p) for p in _chart_outline(data, selection)]
    problems = []
    taxels = fill.field_polygon(generated, origin)
    if not all(point_in_polygon(p, outline) for p in taxels) or _segments_cross(taxels, outline):
        problems.append("P leaves the surface")
    body = fieldfit.field_body(generated, origin)
    for p in body:
        if not point_in_polygon(p, outline):
            off = min(_box_distance(p, outline[k - 1], outline[k]) for k in range(len(outline)))
            if off > fieldfit.CORNER_TOLERANCE_MM + 1e-6:
                problems.append(f"F's corner {p} is {off:.3f} mm off")
    return problems


class CornerToleranceTests(unittest.TestCase):
    """The user's corner tolerance: the taxels stay on the surface, F's margin may leave it by at most 0.5 mm at the
    field's four corners (section 16; at every convex corner of F since section 24, :class:`ConvexCornerTests`), every
    proposal mapped with ``field_corner_overhang``."""

    def test_the_rounded_plates(self) -> None:
        for name, (taxels, missing) in ROUNDED.items():
            with self.subTest(plate=name):
                proposals = FieldFitTests._check(self, name, FIELD)
                data, selection, _, _ = _Fits.get(self, name, FIELD)
                first = proposals[0]["metrics"]
                self.assertEqual((first["taxels"], first["rows"] * first["columns"] - first["taxels"]), (taxels, missing))
                self.assertEqual(sorted((first["rows"], first["columns"])), [14, 18])
                self.assertEqual(design_mask(proposals[0]["design"]) is None, missing == 0)
                for proposal in proposals:
                    self.assertEqual(_corner_problems(data, selection, proposal), [])
                mapped = place.map_route({"selection": selection, "placement": proposals[0]["placement"], "design": proposals[0]["design"]}, data)
                overhang = next(r for r in mapped["verification"] if r["rule"] == "field_corner_overhang")
                self.assertEqual((overhang["required"], overhang["comparison"], overhang["unit"]), (0.5, "max<=", "mm"))
                # Within the tolerance (since section 26 the tip-first fields at the far end: r2 and r5 used none before, their
                # fields 0.7 mm nearer the exit; r4 unchanged).
                self.assertLessEqual(overhang["measured"], fieldfit.CORNER_TOLERANCE_MM)
                self.assertAlmostEqual(overhang["measured"], ROUNDED_OVERHANG[name], places=5)

    def test_the_taxels_never_leave_the_surface(self) -> None:
        # The bitten square: its corner cell goes (143 of 12 x 12), the zones never reach into P.
        self.assertEqual(_shapes(_Fits.get(self, "bitten_square", FIELD)[2])[0], (12, 12, 143))
        for name in ("right_triangle", "equilateral", "disk", "holed_plate", "rounded_3", "rounded_5", "bitten_square", "cut_square"):
            data, selection, result, _ = _Fits.get(self, name, FIELD)
            for proposal in result["proposals"]:
                with self.subTest(plate=name, proposal=proposal["rank"]):
                    self.assertEqual(_corner_problems(data, selection, proposal), [])

    def test_the_counts_hold_or_improve(self) -> None:
        # Before the tolerance (diagonal-bus/5): right triangle 559, equilateral 340, disk 436, holed plate 375.  The right
        # triangle 560 -> 562 (34 x 33) with shaped fields up to 64 x 64 (section 21).  The most taxels of the proposals:
        # since section 22 the right triangle's first proposal is the symmetric 552 on its hypotenuse, the 562 next.
        # Since section 24 (the tolerance at every convex corner): 595 (on a leg, first), 353, 448 and 396.  Section 26.17
        # turned no symmetric exit with a symmetric field (the holed plate's most 376 unturned, its symmetric 247 first);
        # since section 26.19 an exit is not turned only when its symmetric field holds within 20 % of its best unturned
        # one, so the holed plate's sides are turned again (its symmetric 247 is 66 % of its 376): its turned 396.
        for name, before, now in (("right_triangle", 559, 595), ("equilateral", 340, 353), ("disk", 436, 448), ("holed_plate", 375, 396)):
            with self.subTest(plate=name):
                taxels = max(p["metrics"]["taxels"] for p in _Fits.get(self, name, FIELD)[2]["proposals"])
                self.assertGreaterEqual(taxels, before)
                self.assertEqual(taxels, now)

    def test_straight_edges_keep_the_full_margin(self) -> None:
        # 25.6 mm holds 12 crossings at 2 mm with the whole 0.5 mm margin on both sides (24.4 mm), 13 only with 0.4 mm
        # less on each: the tolerance does not widen a straight side.  Its F lies wholly on the square.
        data, selection, result, _ = _Fits.get(self, "square_25.6", FIELD)
        first = result["proposals"][0]
        self.assertEqual((first["metrics"]["rows"], first["metrics"]["columns"], first["metrics"]["taxels"]), (12, 12, 144))
        mapped = place.map_route({"selection": selection, "placement": first["placement"], "design": first["design"]}, data)
        self.assertEqual(next(r for r in mapped["verification"] if r["rule"] == "field_corner_overhang")["measured"], 0.0)
        body = fieldfit.field_body(generate_design(first["design"]), first["placement"]["field_origin_base"])
        outline = [_frame(first["placement"]).to_base(p) for p in _chart_outline(data, selection)]
        self.assertTrue(all(point_in_polygon(p, outline) for p in body))

    def test_the_lattice_leaves_out_only_the_corner_zones(self) -> None:
        # A row's run is free with its four zones left out; a zone is free on its own; tolerance 0 is F all round.
        from surface import api as api_module

        mesh = F.mesh(F.plate(PLATES["rounded_4"], 3.0))
        seed = select.nearest_facet(mesh, (15.0, 19.0, 3.0))
        _, chart = api_module.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": seed}]})
        options = fit.parse_options({})
        side = fit.choose_bases("auto", api_module.boundary_sides(mesh, chart), mesh, chart)[0]
        space = fill.FreeSpace(chart, fit.BaseFrame(side, 0.0), fit.surface_obstacles(mesh, chart, options), 0.0, side["edges"])
        pitch, width, margin = 2.0, 1.4, 0.5
        reach = fieldfit.corner_reach(margin, width)
        self.assertEqual((reach, fieldfit.corner_inset(margin)), (round(1.4 / 3, 9), 0.0))
        self.assertEqual((fieldfit.corner_reach(margin, width, 0.0), fieldfit.corner_inset(margin, 0.0)), (0.0, margin))
        self.assertEqual(fieldfit.corner_inset(margin, 0.2), 0.3)
        phase = fieldfit.centred_phase(space, pitch, width, margin)
        grid = fieldfit.lattice(space, pitch, width, margin, phase)
        strict = fieldfit.lattice(space, pitch, width, margin, phase, tolerance=0.0)
        self.assertEqual((grid["rows"], grid["columns"]), (14, 18))
        self.assertEqual(fieldfit.best_rectangle(grid["plain"], grid["up"], 64, 64, 0, grid["zones"])[0], 252)
        self.assertLess(fieldfit.best_rectangle(strict["plain"], strict["up"], 64, 64, 0, strict["zones"])[0], 252)
        self.assertTrue(all(zones is None for zones in strict["zones"]))
        x0, y0 = grid["x0"], grid["y0"]
        checked = 0
        for j in range(grid["rows"]):
            y = y0 + j * pitch
            for a in range(grid["columns"]):
                for b in range(a, grid["columns"]):
                    left, right = x0 + a * pitch, x0 + b * pitch + width
                    pieces = [(left, right, y, y + width), (left - margin, right + margin, y + reach, y + width - reach),
                              (left + reach, right - reach, y - margin, y), (left + reach, right - reach, y + width, y + width + margin)]
                    free = all(space.rect_free(x_low, x_high, round(low, 9), round(high, 9)) for x_low, x_high, low, high in pieces)
                    box = space.rect_free(left - margin, right + margin, round(y - margin, 9), round(y + width + margin, 9))
                    with self.subTest(row=j, run=(a, b)):
                        self.assertEqual(grid["plain"][j][a] >= b, free)
                        self.assertEqual(strict["plain"][j][a] >= b, box)
                    checked += free != box
            zones = grid["zones"][j]
            for c in range(grid["columns"]):
                xl, xr = x0 + c * pitch, x0 + c * pitch + width
                want = (space.rect_free(xl - margin, xl + reach, round(y - margin, 9), round(y + reach, 9)),
                        space.rect_free(xr - reach, xr + margin, round(y - margin, 9), round(y + reach, 9)),
                        space.rect_free(xl - margin, xl + reach, round(y + width - reach, 9), round(y + width + margin, 9)),
                        space.rect_free(xr - reach, xr + margin, round(y + width - reach, 9), round(y + width + margin, 9)))
                self.assertEqual(tuple(flags[c] for flags in zones) if zones is not None else (True,) * 4, want)
        self.assertGreater(checked, 0)  # runs the tolerance frees

    def test_the_dp_holds_the_zones_against_brute_force(self) -> None:
        # Every corner zone held but at F's convex corners (section 24; section 16 held a row's bottom zones with a row
        # below, its top zones with a row above): the DP and the rectangle search against the definition (_free) on
        # random grids.
        rng = random.Random(16)
        for trial in range(300):
            rows, columns = rng.randint(1, 4), rng.randint(1, 5)
            plain, up = _random_grid(rng, rows, columns, rng.choice((0.6, 0.85, 1.0)), rng.random() < 0.5)
            zones = [None if rng.random() < 0.3 else tuple([rng.random() < 0.7 for _ in range(columns)] for _ in range(4)) for _ in range(rows)]
            with self.subTest(trial=trial):
                count, spans = fieldfit.best_convex(plain, up, 0, columns - 1, 0, rows - 1, 0, None, zones)
                self.assertEqual(count, _brute(plain, up, zones=zones))
                self.assertEqual(fieldfit.best_rectangle(plain, up, 99, 99, 0, zones)[0], _brute(plain, up, rectangle=True, zones=zones))
                if count:
                    selection = [None] * rows
                    for j, a, b in spans:
                        selection[j] = (a, b)
                    self.assertTrue(_free(selection, plain, up, zones))

    def test_the_soft_finger_keeps_its_rectangle(self) -> None:
        # No extra column: the contact face's 59 x 12 (708), its straight sides keep the whole margin.
        _, _, result, _ = _Fits.get(self, "soft_finger", FIELD)
        metrics = result["proposals"][0]["metrics"]
        self.assertEqual(sorted((metrics["rows"], metrics["columns"])) + [metrics["taxels"]], [12, 59, 708])


class CoverageFirstTests(unittest.TestCase):
    """The user's correction of 2026-10-25 (P5-diagonal-bus.md section 21): CAD generation covers the selected region
    first.  Shaped fields take the rectangles' caps (64 x 64; 32 x 32 before); the rectangle preference, off by default
    since then, is gone with section 26.16."""

    def _proposals(self, options: dict) -> list:
        return _Fits.get(self, "fin", dict(FIELD, **options))[2]["proposals"]

    def test_the_fin_follows_its_taper(self) -> None:
        # Before: 8 x 47 = 376 along a long side, the tails leaving sideways (the 32 x 32 cap held the taper's field to
        # 371, and the preference compared exits).  Now a masked 59 x 12 along the face, unturned, its tails at the 25.8 mm
        # mount end and ROW_01 at the 12 mm tip: 569 with section 21 (0.2 mm off the face's axis), 568 since section 22,
        # every row its own mirror image (the real STL: the same fields); 572 since section 24 (the corner tolerance at
        # every convex corner of its staircases).
        proposals = FieldFitTests._check(self, "fin", FIELD)
        first = proposals[0]
        metrics, placement = first["metrics"], first["placement"]
        mask = design_mask(first["design"])
        self.assertIsNotNone(mask)
        self.assertEqual((metrics["rows"], metrics["columns"], metrics["taxels"], metrics["angle_deg"]), (59, 12, 572, 0.0))
        self.assertAlmostEqual(math.dist(placement["base_from_uv"], placement["base_to_uv"]), 25.8, delta=0.01)
        widths = [last - start + 1 for start, last in mask]
        self.assertEqual(widths, sorted(widths))  # narrowest at ROW_01 (the tip), widening toward the mount end
        self.assertEqual((widths[0], widths[-1]), (4, 12))
        self.assertTrue(_symmetric_rows(first) and metrics["symmetry"]["field"])
        tip = metrics["row_bus"]["tip_width_mm"]
        self.assertLess(tip, 12.0)
        self.assertEqual(min(p["metrics"]["row_bus"]["tip_width_mm"] for p in proposals), tip)
        # The fields along a long side hold about as many (570 on the 74.3 mm side next, 574 on the 45.36 mm side, within
        # 1 %): the narrow tip chose.  (Before section 24 the asymmetric 569 of the same readout came next.)  Since section
        # 26 the long side's tip-first field (560, 98.2 % of its 570, 0.5 mm nearer that side's far edge) leads that side's
        # fields, the 570 directly after it.  (Section 26.15's tip-zone guard turned the 560 down, the 570 then the 573
        # second and third; 26.16, reach first, takes the 560 again: re-pinned to round 1's.)
        self.assertEqual([(p["metrics"]["taxels"], p["metrics"]["symmetry"]["field"], p["metrics"]["tip"]["lead"]) for p in proposals[1:3]],
                         [(560, False, True), (570, False, False)])
        self.assertEqual(proposals[1]["metrics"]["tip"]["displaced"], 3)
        self.assertEqual(max(p["metrics"]["taxels"] for p in proposals), 574)

    def test_the_cut_square(self) -> None:
        # The 50 mm square with a 5 mm cut corner, its exit on a full side: the masked 24 x 24 holds 575 (574 before section
        # 24), the full 23 x 24 552 (96.0 %), proposed after it (coverage first; the rectangle preference that could put it
        # first is gone with section 26.16).  Since section 26 the tip-first 573 (one row nearer the far side) before the
        # 575.  (With the exit free, since section 24 a field of a lattice at 45 degrees to the square, exiting at its cut,
        # holds the most: 577, symmetric about the cut; no rectangle there.)
        result = _Fits.get(self, "cut_square", FIELD, {"side": 0})[2]
        self.assertEqual([(p["metrics"]["taxels"], design_mask(p["design"]) is None) for p in result["proposals"]][:3],
                         [(573, False), (575, False), (552, True)])
        free = _Fits.get(self, "cut_square", FIELD)[2]["proposals"][0]
        self.assertEqual((free["metrics"]["taxels"], free["placement"]["base_side"], free["metrics"]["symmetry"]["field"]), (577, 2, True))


class StackedTailEndTests(unittest.TestCase):
    """The user's request of 2026-10-27 (P5-diagonal-bus.md section 27.3): "现在几乎都是正确的，但是有些tail好像居左居右，尝试都居中吧；
    这样上下两个tail可以对在一起，更加clean和直接" (now almost everything is right, but some tails seem to sit left or right; try
    centring them all, so the upper and lower tails can line up together, cleaner and more direct).  The Row and Column
    tails are centred on one line (the field's centre line, diagonal-bus/10) and end together, on the nearest line across
    the boards on which each is at least the shortest tail long and ends at least the extension past the surface's
    lowest edge under it.  Before, each ended the extension past the edge under its own
    width, so the stacked contacts did not line up where those edges differ: on a slanted exit (the slanted plate's 16 x
    12, 1.732 mm apart) and on a turned field (the holed plate's at -20 degrees, 0.364 mm; section 26.17, merged on
    2026-10-27, turned no symmetric exit, so the right triangle's legs at -30 degrees under 12 rows, 4.619 mm; since section
    26.19 the holed plate's sides are turned again, its symmetric fields more than 20 % smaller); on an arc (the disk) both
    centred tails span its lowest point."""

    def test_the_tails_are_centred_on_one_line_and_end_together(self) -> None:
        apart = {}
        for name, caps in (("slanted", {}), ("holed_plate", {}), ("disk", {}), ("right_triangle", {"max_rows": 12})):
            for sides in ("both", "left", "right"):
                with self.subTest(face=name, sides=sides):
                    data, selection, result, _ = _Fits.get(self, name, dict(FIELD, row_sides=sides, **caps))
                    chart = _chart_outline(data, selection)
                    for proposal in result["proposals"]:
                        frame = _frame(proposal["placement"])
                        lowest = fieldfit.bottoms([frame.to_base(p) for p in chart])
                        tails = fieldfit.tails_of(generate_design(proposal["design"]), proposal["placement"]["field_origin_base"])
                        # Our own ends: each board's outline's lowest point in the board frame (the tails point down).
                        ends = {key: min(frame.to_base(p)[1] for p in proposal["outlines_uv"][key]) for key in ("row", "column")}
                        self.assertAlmostEqual((tails["row"][0] + tails["row"][1]) / 2, (tails["column"][0] + tails["column"][1]) / 2, delta=1e-6)
                        self.assertAlmostEqual(ends["row"], ends["column"], delta=1e-6)
                        edges = {key: fieldfit.bottom_beside(lowest, tails[key][0], tails[key][1], frame) for key in ("row", "column")}
                        reach = {key: edges[key] - ends[key] for key in ("row", "column")}
                        self.assertGreaterEqual(min(reach.values()), 20.0 - 1e-3, reach)
                        self.assertAlmostEqual(min(reach.values()), proposal["metrics"]["tail_reach_mm"], delta=2e-3)
                        self.assertEqual(proposal["metrics"]["row_tail_mm"], proposal["metrics"]["column_tail_mm"])
                        # The nearest such line: the nearer end just the extension past its edge, or both tails the shortest.
                        self.assertTrue(min(reach.values()) < 20.0 + 2e-3 or proposal["metrics"]["row_tail_mm"] == fit.TAIL_MIN_MM["surface"], reach)
                        apart[(name, sides, proposal["rank"])] = abs(edges["row"] - edges["column"])
        # The rule is exercised: the edges under the two tails differ on the slanted exit and the turned fields.
        self.assertGreater(max(value for key, value in apart.items() if key[0] == "slanted"), 1.7)
        self.assertGreater(max(value for key, value in apart.items() if key[0] == "right_triangle"), 4.5)
        # The slanted exit's field with both: the 16 x 12 = 59 (tails 15.896 mm, its edges 1.732 mm apart) until section 26
        # (merged on 2026-10-27) took its tip-first 17 x 12 = 62 (tails 14.636 mm, its edges 2.165 mm apart).
        slanted = _Fits.get(self, "slanted", dict(FIELD, row_sides="both"))[2]["proposals"]
        self.assertIn((17, 12, 14.636, 14.636), [(p["metrics"]["rows"], p["metrics"]["columns"], p["metrics"]["row_tail_mm"], p["metrics"]["column_tail_mm"]) for p in slanted])


class CapsKeepTheExitTests(unittest.TestCase):
    """The user's rule of 2026-10-25 (P5-diagonal-bus.md section 23): a smaller readout (``max_rows``, ``max_columns``, a
    reader) never moves the exit, and a capped field stacks at the far end from the edge the tails leave by (the
    fingertip), its tails running down the face to the exit, as near the far end as the tails' 200 mm allow."""

    LENGTH_MM = 119.36  # the fin plate from its 25.8 mm mount end to its 12 mm tip

    def _far(self, proposal: dict) -> float:
        """How far the field's last row (ROW_01) lies from the exit (mm, the exit's frame)."""

        matrix = proposal["design"]["matrix"]
        return proposal["placement"]["field_origin_base"][1] + (matrix["rows"] - 1) * matrix["pitch_y_mm"]

    def test_the_fin_keeps_its_mount_end_and_fills_its_tip(self) -> None:
        # Before: 14 x 59 = 567 on a 74.3 mm long side first (the 32-row cap held the mount end's field to 370), the
        # tails leaving sideways.  Now the exit stays the mount end and the 32 rows stack at the fingertip: 32 x 10 =
        # 254, symmetric, ROW_01 at the 12 mm tip (6 wide), widening toward the exit; the tails (68.2 mm) run down the
        # face from the field's end.  The long sides' fields stay alternatives.  Since section 24: 32 x 11 = 256 (ROW_01 5
        # wide, the last row 11), the tails 68.1 mm.  Since section 26 the tip-first field of section 23's window goes
        # first: 32 x 10 = 250 (97.7 % of the 256), its ROW_01 1.5 mm nearer the tip (117.0 mm from the exit), the
        # tails 69.7 mm; the 256 next.  Since section 26.18 (a symmetric group's eighth row phases) the 250 another 0.25 mm
        # nearer the tip (117.25 mm), its tails 69.9 mm.  Since diagonal-bus/10 centred the Row tail (section 27) the tails'
        # roots lie 4 um lower: the 250's tails 69.906 mm, the 256's 68.068 (69.91 and 68.072 before).
        proposals = FieldFitTests._check(self, "fin", dict(FIELD, max_rows=32))
        first = proposals[0]
        metrics, placement = first["metrics"], first["placement"]
        self.assertEqual((metrics["rows"], metrics["columns"], metrics["taxels"], metrics["angle_deg"]), (32, 10, 250, 0.0))
        self.assertAlmostEqual(math.dist(placement["base_from_uv"], placement["base_to_uv"]), 25.8, delta=0.01)
        self.assertTrue(_symmetric_rows(first) and metrics["symmetry"]["field"])
        widths = [last - start + 1 for start, last in design_mask(first["design"])]
        self.assertEqual((widths[-1], widths), (10, sorted(widths)))
        self.assertAlmostEqual(self._far(first), 117.25, delta=1e-3)  # within the margin and the crossing of the 119.36 mm tip
        self.assertEqual(first["design"]["tail"]["top_length_mm"], 69.906)
        self.assertEqual((proposals[1]["metrics"]["taxels"], proposals[1]["design"]["tail"]["top_length_mm"]), (256, 68.068))
        self.assertEqual((metrics["tip"]["lead"], metrics["tip"]["displaced"], metrics["tip"]["taxels_given"]), (True, 2, 6))
        # Without the cap the same exit: the caps never chose it.
        default = _Fits.get(self, "fin", FIELD)[2]["proposals"][0]["placement"]["base_side"]
        self.assertEqual(placement["base_side"], default)

    def test_tails_past_80_mm(self) -> None:
        # 16 rows: the field still at the tip, its tails 102.0 mm (the surface's 200 mm since section 23; at 80 mm the
        # mount end had no proposal and a long side's 14 x 59 came first).  Since section 26 the window's tip-first field,
        # 16 x 8 = 104 (98.1 % of the 106, 1 mm nearer the tip), its tails 103.0 mm; the 106 next, since round 2 the 106's
        # zero-cost tie, 0.5 mm nearer the tip than the 106 the search kept, its tails 102.5 mm.  (Section 26.15's tip-zone
        # guard turned the 104 down, the 106's tie first; 26.16, reach first, takes the 104 again: re-pinned to round 1's.)
        # Since section 26.18 (a symmetric group's eighth row phases) both 0.25 mm nearer the tip: the 104's tails 103.275
        # mm, the 106's tie's 102.775 mm.  Since diagonal-bus/10 centred the Row tail (section 27) the tails' roots lie 4 um
        # lower: 103.271 and 102.771 mm.
        proposals = FieldFitTests._check(self, "fin", dict(FIELD, max_rows=16))
        first = proposals[0]
        self.assertAlmostEqual(math.dist(first["placement"]["base_from_uv"], first["placement"]["base_to_uv"]), 25.8, delta=0.01)
        self.assertEqual((first["metrics"]["rows"], first["metrics"]["columns"], first["metrics"]["taxels"]), (16, 8, 104))
        self.assertGreater(self._far(first), self.LENGTH_MM - 5.0)
        self.assertEqual(first["design"]["tail"]["top_length_mm"], 103.271)
        self.assertEqual((proposals[1]["metrics"]["taxels"], proposals[1]["design"]["tail"]["top_length_mm"]), (106, 102.771))
        self.assertEqual(fit.TAIL_MAX_MM, {"surface": 200.0, "generic": 80.0})
        for template, profile in (("surface", "jlc_fpc_surface_v1.json"), ("generic", "jlc_fpc_standard_v1.json")):
            limits = json.loads((ROOT / "profiles" / profile).read_text(encoding="utf-8"))["limits"]
            self.assertEqual(limits["maximum_tail_length_mm"], fit.TAIL_MAX_MM[template])

    def test_the_200_mm_cap_searches_again_nearer_the_exit(self) -> None:
        # The fin stretched 2.6 times, 16 rows: stacked at its tip (ROW_01 307.5 mm from the mount end) the capped field,
        # 16 x 6, would need tails of 294.196 mm, 94.196 past the 200 mm; the field is refused, and the search runs again
        # with the rows that much nearer the exit (ROW_01 within 213.304 mm: ``reaching``, section 23).  The mount end
        # keeps its 16 rows, 16 x 9 = 144 with ROW_01 213.0 mm from it, the tails 199.433 mm; without the search again
        # the mount end proposes nothing and a long side's 14 x 64 comes first, its tails leaving sideways (the review of
        # section 27.4: no test held either).  Merged with section 26 (2026-10-27): the search's first field at the tip is
        # a 16 x 6 = 92 with ROW_01 306.5 mm out (307.5 with main's quick fix, whose rank put the farthest-reaching of
        # fields alike first, section 26.14), its tails 293.196 mm, 93.196 past the cap, so the search again reaches as far
        # (213.304 mm); the 144 is then its window's tip-first field, an eighth row phase nearer the tip (section 26.18):
        # ROW_01 213.25 mm out, its tails 199.683 mm.
        data, selection, result, _ = _Fits.get(self, "fin_2.6", dict(FIELD, max_rows=16))
        first = result["proposals"][0]
        metrics = first["metrics"]
        self.assertAlmostEqual(math.dist(first["placement"]["base_from_uv"], first["placement"]["base_to_uv"]), 25.8, delta=0.01)
        self.assertEqual((metrics["rows"], metrics["columns"], metrics["taxels"]), (16, 9, 144))
        self.assertAlmostEqual(self._far(first), 213.25, delta=1e-3)  # the placement's origin to 0.1 um
        self.assertEqual((first["design"]["tail"]["top_length_mm"], first["design"]["tail"]["bottom_length_mm"]), (199.683, 199.683))
        self.assertTrue(all(max(p["metrics"]["row_tail_mm"], p["metrics"]["column_tail_mm"]) <= fit.TAIL_MAX_MM["surface"] for p in result["proposals"]))
        generated = generate_design(first["design"])
        self.assertTrue(generated["ok"] and generated["manifest"]["build_id"] == first["build_id"], generated["validation"]["errors"][:3])
        # The first search of the mount end alone, with the caps: its first field and the refusal of its tails.
        mesh = read_stl(data)
        from surface import api as api_module

        _, chart = api_module.selection_chart(mesh, selection)
        options = fit.parse_options(dict(FIELD, max_rows=16))
        mount = [base for base in fit.choose_bases("auto", api_module.boundary_sides(mesh, chart), mesh, chart) if abs(base["chord_mm"] - 25.8) < 0.01]
        profile = fit.load_profile_cached("surface")
        obstacles = fit.surface_obstacles(mesh, chart, options)
        # The search's order as it is (section 26.16 removed the rectangle preference's step).
        queue = fieldfit.ordered(fieldfit.search_fields(chart, mount, options, profile, obstacles, []), False)
        tip = queue[0]
        self.assertEqual((tip["rows"], tip["columns"], tip["taxels"]), (16, 6, 92))
        self.assertAlmostEqual(tip["field_origin"][1] + (tip["rows"] - 1) * tip["pitch"], 306.5, delta=1e-3)
        self.assertAlmostEqual(fieldfit.tail_excess(tip, options, profile), 93.196, places=6)
        rejected: dict = {}
        self.assertEqual(fieldfit.realize_field(tip, chart, obstacles, options, profile, None, rejected), (None, None))
        self.assertEqual(rejected, {fit.tails_too_long("surface"): 1})
        self.assertEqual(fit.tails_too_long("surface"), "tails longer than 200 mm")

    def test_the_rows_stack_at_the_far_end_of_any_exit(self) -> None:
        # The 12 mm tip as the exit with 16 rows: the 16 rows at the far end (the 25.8 mm mount end, 12 wide), not the
        # rows next to the exit.
        proposals = _Fits.get(self, "fin", dict(FIELD, max_rows=16), base={"side": 2})[2]["proposals"]
        first = proposals[0]
        self.assertAlmostEqual(math.dist(first["placement"]["base_from_uv"], first["placement"]["base_to_uv"]), 12.0, delta=0.01)
        self.assertEqual((first["metrics"]["rows"], first["metrics"]["columns"], first["metrics"]["taxels"]), (16, 12, 192))
        self.assertGreater(self._far(first), self.LENGTH_MM - 5.0)

    def test_every_exit_of_the_fit_without_the_caps_keeps_its_fields(self) -> None:
        # Section 26.18 (round 4's review): every exit the fit without the caps has fields on is searched on its own with
        # the caps, in that fit's exit order (its symmetric exits first, section 26.17), so that no exit's capped fields
        # are pruned by another's.  Round 4 searched only that fit's first exit on its own and took the others from the
        # search of all exits at once: once the right triangle's symmetric hypotenuse came first, its fields pruned the
        # legs' lattices there (no field on either leg) and the fit proposed two fields only, the legs none (526d1cc, the
        # hypotenuse not yet first: five on a leg, the 12 x 44 = 255 turned -30 degrees first).  Now the hypotenuse's
        # fields, then a leg's (turned: an exit without a symmetric field may be), five proposals.
        cases = (
            (dict(FIELD, max_rows=12), [(1, 0.0, 12, 24, 156, True), (1, 0.0, 7, 12, 84, False), (0, -30.0, 12, 44, 255, False),
                                        (0, -30.0, 12, 43, 237, False), (0, -30.0, 5, 22, 110, False)]),
            (dict(FIELD, max_rows=16), [(1, 0.0, 16, 32, 272, True), (1, 0.0, 9, 16, 144, False), (0, -30.0, 16, 44, 382, False),
                                        (0, -30.0, 16, 43, 370, False), (0, -30.0, 7, 28, 196, False)]),
            (dict(FIELD, pitch_mm=3.0, reader="32x16"), [(1, 0.0, 16, 31, 256, True), (1, 0.0, 15, 30, 240, False), (1, 0.0, 8, 16, 128, False),
                                                         (0, 0.0, 22, 16, 232, False), (0, 0.0, 16, 16, 136, False)]),
            (dict(FIELD, pitch_mm=2.5, max_rows=16), [(1, 0.0, 16, 32, 272, True), (1, 0.0, 9, 16, 144, False), (0, -30.0, 16, 34, 301, False),
                                                      (0, -30.0, 15, 34, 287, False), (0, -30.0, 10, 16, 160, False)]),
        )
        for options, expected in cases:
            with self.subTest(options=options):
                proposals = _Fits.get(self, "right_triangle", options)[2]["proposals"]
                self.assertEqual([(p["placement"]["base_side"], p["placement"]["base_angle_deg"], p["metrics"]["rows"], p["metrics"]["columns"],
                                   p["metrics"]["taxels"], p["metrics"]["symmetry"]["field"]) for p in proposals], expected)
        # The reference's exit order, not the exits' own: the isosceles triangle's symmetric base (its third exit) first
        # under 12 rows, its legs after it.
        proposals = _Fits.get(self, "isosceles", dict(FIELD, max_rows=12))[2]["proposals"]
        self.assertEqual([(p["placement"]["base_side"], p["metrics"]["symmetry"]["field"]) for p in proposals[:2]], [(0, True), (0, True)])
        self.assertEqual(proposals[-1]["placement"]["base_side"], 2)
        reference = [{"order": 2}, {"order": 0}, {"order": 2}, {"order": 1}]
        self.assertEqual(fieldfit.own_exits(reference), [2, 0, 1])

    def test_an_exit_is_searched_on_its_own_when_the_proposals_reach_it(self) -> None:
        # The work budget (section 26.18): each exit of the fit without the caps is searched on its own when the proposals
        # reach its fields, so an exit whose fields would follow the last proposal is not searched, the proposals as with
        # every exit searched first.  The right triangle under 12 rows: its hypotenuse, then one leg (the other leg's
        # fields would follow the five); the fin under 32 rows: its mount end, then, once that end's fields gave four
        # proposals, its long side for the fifth (its 372).  Searched first, the fin's six exits cost about three times
        # the CPU with the 32x16 reader and with reader auto.
        from unittest import mock

        reaching = fieldfit.reaching
        for name, options, searched, last in (("right_triangle", dict(FIELD, max_rows=12), [1, 0], (0, 110)),
                                              ("fin", dict(FIELD, max_rows=32), [5, 2], (2, 372))):
            calls = []

            def counting(chart, bases, *args, **kwargs):
                calls.append(bases[0]["index"])
                return reaching(chart, bases, *args, **kwargs)

            data, selection, result, _ = _Fits.get(self, name, options)
            with self.subTest(face=name), mock.patch.object(fieldfit, "reaching", counting):
                again = fit.fit_route({"selection": selection, "base": "auto", "options": options}, data)
                self.assertEqual(calls, searched)
                self.assertEqual([p["build_id"] for p in again["proposals"]], [p["build_id"] for p in result["proposals"]])
                proposal = again["proposals"][-1]
                self.assertEqual((proposal["placement"]["base_side"], proposal["metrics"]["taxels"]), last)

    def test_the_helpers(self) -> None:
        self.assertEqual(fieldfit.tip_rows([[1, 1], [1, 1], [-1, -1], [-1, -1]], 4), (0, 1))
        self.assertEqual(fieldfit.tip_rows([[1, 1]] * 40, 16), (24, 39))
        self.assertEqual(fieldfit.tip_rows([[1, 1]] * 40, 16, far=20), (5, 20))
        self.assertIsNone(fieldfit.tip_rows([[-1, -1]], 4))
        self.assertEqual((fieldfit.tip_window(39, 16), fieldfit.tip_window(10, 16)), ((24, 39), (0, 10)))
        grid = {"plain": [[1, 1]] * 10, "y0": 1.0, "pitch": 2.0}
        self.assertEqual((fieldfit.far_row(grid, 9.0), fieldfit.far_row(grid, 9.5), fieldfit.far_row(grid, 0.5)), (4, 4, -1))
        # The shaped search with a cap: the rows at the far end (the fingertip), not the widest anywhere.
        plain = [[3, 3, 3, 3]] * 4 + [[1, 1, -1, -1]] * 2  # four rows 4 wide at the exit, then two 2 wide at the far end
        grid = {"plain": plain, "up": plain, "rows": 6, "columns": 4, "zones": None}
        count, spans = fieldfit.search_shaped(grid, 3, 4, 0)
        self.assertEqual((count, [row for row, _, _ in spans]), (8, [3, 4, 5]))
        self.assertEqual(fieldfit.search_shaped(grid, 3, 4, 0, far=3)[0], 12)  # held back to row 3 (the tails' reach)
        # The exits as without the caps: the capped fields of the reference's first exit first, its order kept.
        queue = [{"order": 1, "id": "a"}, {"order": 0, "id": "b"}, {"order": 2, "id": "c"}, {"order": 0, "id": "d"}]
        reference = [{"order": 0}, {"order": 0}, {"order": 1}]
        self.assertEqual([c["id"] for c in fieldfit.keep_exits(queue, reference)], ["b", "d", "a", "c"])
        free = fieldfit.uncapped(dict(fit.parse_options(FIELD), max_rows=32, reader="32x16"))
        self.assertEqual((free["max_rows"], free["max_columns"], free["reader"]), (fieldfit.UNCAPPED, fieldfit.UNCAPPED, "none"))


class _Chart:
    """A chart of our own for :func:`surface.fieldfit.exit_symmetry`: its outline (counter-clockwise uv)."""

    def __init__(self, outline: list) -> None:
        self._outline = [tuple(p) for p in outline]

    def outline(self) -> list:
        return list(self._outline)


def _side(a, b) -> dict:
    """An exit from ``a`` to ``b`` (the surface on its left)."""

    dx, dy = b[0] - a[0], b[1] - a[1]
    chord = math.hypot(dx, dy)
    return {"index": 0, "from_uv": list(a), "to_uv": list(b), "inward_uv": [-dy / chord, dx / chord], "chord_mm": chord, "edges": [0]}


def _moved(outline: list, angle: float, shift: tuple) -> list:
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    return [(x * c - y * s + shift[0], x * s + y * c + shift[1]) for x, y in outline]


def _symmetric_rows(proposal: dict) -> bool:
    """Every row of a proposal's field its own mirror image about the field's centre (the mask seen from outside, or
    a full field)."""

    mask = design_mask(proposal["design"])
    columns = proposal["metrics"]["columns"]
    return mask is None or all(first + last == columns + 1 for first, last in mask)


class SymmetryTests(unittest.TestCase):
    """The user's request of 2026-10-25 (P5-diagonal-bus.md section 22): "if the geometric face is symmetric, make the
    sensor symmetric too, as far as possible".  Per exit, the selection mirrored about the axis through the exit's chord
    midpoint must match itself within 0.05 mm; there the fit searches lattices centred on the axis for fields whose every
    row is its own mirror image (exactly, a DP of its own).  Since the user's decisions of 2026-10-27 (section 26.17: faces
    symmetric like the WidowX's take a centred sensor too; section 26.19: "可以加个门槛", a threshold of 20 %) each such
    exit's best symmetric field goes first unless a field that breaks the symmetry (asymmetric, or turned) holds at least
    1.2 times its taxels (section 22's rule with 20 % for its 3 %), decided on the search's fields before the tip step, and
    an exit whose symmetric field holds within it of its best unturned field is not turned."""

    def test_the_detection(self) -> None:
        trapezoid = [(0.0, 0.0), (40.0, 0.0), (30.0, 20.0), (10.0, 20.0)]
        none = {"holes": []}
        found = fieldfit.exit_symmetry(_Chart(trapezoid), _side((0.0, 0.0), (40.0, 0.0)), none)
        self.assertEqual((found["symmetric"], found["axis_mm"], found["deviation_mm"]), (True, 20.0, 0.0))
        # The slanted side is no axis.
        self.assertFalse(fieldfit.exit_symmetry(_Chart(trapezoid), _side((40.0, 0.0), (30.0, 20.0)), none)["symmetric"])
        # Turned and shifted, its sides split into several segments on one side only: still symmetric (the samples of the
        # mirror lie on the other side's segments, wherever its vertices are).
        split = [(0.0, 0.0), (13.3, 0.0), (40.0, 0.0), (37.1, 5.8), (30.0, 20.0), (10.0, 20.0)]
        moved = _moved(split, 37.0, (5.0, -3.0))
        found = fieldfit.exit_symmetry(_Chart(moved), _side(moved[0], moved[2]), none)
        self.assertTrue(found["symmetric"], found)
        self.assertLess(found["deviation_mm"], 1e-6)
        # A vertex moved 0.03 mm stays within the 0.05 mm tolerance, 0.1 mm does not (its mirror lies 0.1 mm from the top
        # side's mirror image, 0.089 mm from the slanted side's).
        for move, symmetric in ((0.03, True), (0.1, False)):
            bent = [(0.0, 0.0), (40.0, 0.0), (30.0 + move, 20.0), (10.0, 20.0)]
            found = fieldfit.exit_symmetry(_Chart(bent), _side((0.0, 0.0), (40.0, 0.0)), none)
            self.assertEqual(found["symmetric"], symmetric, found)
            self.assertTrue(0.85 * move < found["deviation_mm"] <= move + 1e-9, found)
        # A hole on the axis keeps it; moved 1 mm sideways it does not (the holes are mirrored too).
        hole = [(18.0, 8.0), (18.0, 12.0), (22.0, 12.0), (22.0, 8.0)]
        self.assertTrue(fieldfit.exit_symmetry(_Chart(trapezoid), _side((0.0, 0.0), (40.0, 0.0)), {"holes": [hole]})["symmetric"])
        shifted = [(x + 1.0, y) for x, y in hole]
        self.assertFalse(fieldfit.exit_symmetry(_Chart(trapezoid), _side((0.0, 0.0), (40.0, 0.0)), {"holes": [shifted]})["symmetric"])
        # A disk faceted at uneven angles (steps of 3-5 degrees, r 25 mm: sagitta at most 0.024 mm) about the chord of an
        # arc between two of its vertices; 8-12 degree facets (0.14 mm) are not.
        rng = random.Random(22)
        for low, high, symmetric in ((3.0, 5.0, True), (8.0, 12.0, False)):
            angles, angle = [], 0.0
            while angle < 360.0 - high:
                angles.append(angle)
                angle += rng.uniform(low, high)
            disk = [(25.0 * math.cos(math.radians(a)), 25.0 * math.sin(math.radians(a))) for a in angles]
            exit_ = fit.arc_exit(disk, 40.0, 15.0, "arc")
            found = fieldfit.exit_symmetry(_Chart(disk), exit_, none)
            self.assertEqual(found["symmetric"], symmetric, (low, high, found))
        # The plates: the fin about its two ends only, the isosceles triangle about its base only, the equilateral about
        # every side, the right triangle (an isosceles right triangle) about its hypotenuse, the crank pad about none.
        expected = {"fin": {25.8: True, 12.0: True, 45.36: False, 74.32: False}, "isosceles": {50.0: True, 65.0: False},
                    "equilateral": {60.0: True}, "right_triangle": {98.99: True, 70.0: False}}
        if CRANK.exists():
            expected["crank_auto"] = {}
        for name, by_chord in expected.items():
            with self.subTest(plate=name):
                bases = _Fits.get(self, name, FIELD)[2]["bases"]
                unturned = [base for base in bases if base["angle_deg"] == 0.0]
                for base in unturned:
                    self.assertEqual(base["symmetric"], by_chord.get(round(base["chord_mm"], 2), False), base)
                    self.assertEqual(base["symmetric_candidates"] > 0, base["symmetric"], base)

    def test_the_symmetric_runs_and_columns(self) -> None:
        self.assertEqual(fieldfit.symmetric_runs(5), [(2, 2), (1, 3), (0, 4)])
        self.assertEqual(fieldfit.symmetric_runs(4), [(1, 2), (0, 3)])
        self.assertEqual(fieldfit.symmetric_runs(1), [(0, 0)])
        mesh = F.mesh(F.plate(PLATES["fin"], 3.0))
        from surface import api as api_module

        _, chart = api_module.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (0.0, 0.0, 3.0))}]})
        options = fit.parse_options(FIELD)
        sides = api_module.boundary_sides(mesh, chart)
        mount = next(side for side in sides if abs(side["chord_mm"] - 25.8) < 0.01)
        frame = fit.BaseFrame(mount, 0.0)
        space = fill.FreeSpace(chart, frame, fit.surface_obstacles(mesh, chart, options), 0.0, mount["edges"])
        axis = fieldfit.exit_symmetry(chart, mount, {"holes": []})["axis"]
        self.assertAlmostEqual(axis, 12.9, places=6)
        pitch, width, margin = 2.0, 1.4, 0.5
        for even in (False, True):
            for phase in (0.0, 0.5, 1.0, 1.5):
                with self.subTest(even=even, phase=phase):
                    grid = fieldfit.symmetric_lattice(space, pitch, width, margin, axis, even, phase)
                    columns = grid["columns"]
                    self.assertEqual(columns % 2 == 0, even)
                    self.assertEqual(columns, 12 if even else 11)
                    # Column a's mirror image is column columns - 1 - a.
                    centres = [grid["x0"] + a * pitch + width / 2 for a in range(columns)]
                    for a in range(columns):
                        self.assertAlmostEqual(centres[a] + centres[columns - 1 - a], 2 * axis, places=9)
                    # On the symmetric face a run is free exactly when its mirror image is.
                    for j in range(grid["rows"]):
                        for a in range(columns):
                            for b in range(a, columns):
                                self.assertEqual(grid["plain"][j][a] >= b, grid["plain"][j][columns - 1 - b] >= columns - 1 - a)
        # The whole lattice's columns stay within phase 0's bounds: no symmetric lattice when the centre column does not fit.
        self.assertIsNone(fieldfit.symmetric_columns(space, 30.0, width, margin, axis, True))

    def test_the_symmetric_dp_against_brute_force(self) -> None:
        # The DP over half widths against the definition restricted to symmetric runs, with zones, caps and rectangles; and
        # the windows of a rows cap.
        rng = random.Random(22)
        for trial in range(400):
            rows, columns = rng.randint(1, 5), rng.randint(1, 7)
            plain, up = _random_grid(rng, rows, columns, rng.choice((0.6, 0.85, 1.0)), rng.random() < 0.5)
            zones = None if rng.random() < 0.4 else [None if rng.random() < 0.3 else tuple([rng.random() < 0.75 for _ in range(columns)] for _ in range(4))
                                                     for _ in range(rows)]
            cap = rng.choice((1, 2, 3, 99))
            with self.subTest(trial=trial):
                count, spans = fieldfit.best_symmetric(plain, up, columns, 0, rows - 1, cap, 0, zones)
                self.assertEqual(count, _brute(plain, up, (99, cap), zones=zones, symmetric=True))
                rectangle = fieldfit.best_symmetric(plain, up, columns, 0, rows - 1, cap, 0, zones, rectangle=True)[0]
                self.assertEqual(rectangle, _brute(plain, up, (99, cap), rectangle=True, zones=zones, symmetric=True))
                if count:
                    selection = [None] * rows
                    for j, a, b in spans:
                        self.assertEqual(a + b, columns - 1)
                        selection[j] = (a, b)
                    self.assertTrue(_is_convex(selection) and _free(selection, plain, up, zones))
                    self.assertEqual(sum(b - a + 1 for _, a, b in spans), count)
                rows_cap = rng.randint(1, 3)
                grid = {"plain": plain, "up": up, "zones": zones, "rows": rows, "columns": columns}
                # The cap's rows down from the farthest row with a free symmetric run within the width cap (section 23).
                tip = _tip(plain, up, rows_cap, zones, [(a, columns - 1 - a) for a in range(columns) if 0 < columns - 2 * a <= cap])
                self.assertEqual(fieldfit.search_symmetric(grid, rows_cap, cap, 0)[0],
                                 _brute(tip[0], tip[1], (rows_cap, cap), zones=tip[2], symmetric=True) if tip[0] else 0)
                self.assertEqual(fieldfit.search_symmetric(grid, rows_cap, cap, 0, rectangle=True)[0],
                                 _brute(tip[0], tip[1], (rows_cap, cap), rectangle=True, zones=tip[2], symmetric=True) if tip[0] else 0)
                # A threshold: nothing at or under it.
                self.assertEqual(fieldfit.best_symmetric(plain, up, columns, 0, rows - 1, cap, count, zones), (0, []))

    def test_mirror_symmetric(self) -> None:
        info = {"symmetric": True, "axis": 10.0, "axis_mm": 10.0, "deviation_mm": 0.0}
        # Five columns of a 2 mm pitch and a 1.4 mm crossing centred on x = 10: P from 5.3 to 14.7.
        field = {"cells": ((1, 3), (0, 4), (2, 2)), "columns": 5, "pitch": 2.0, "width": 1.4, "field_origin": (5.3, 0.0), "angle_deg": 0.0,
                 "symmetry": info}
        self.assertTrue(fieldfit.mirror_symmetric(field))
        self.assertFalse(fieldfit.mirror_symmetric(dict(field, cells=((1, 3), (0, 4), (2, 3)))))  # one row not its own mirror
        self.assertFalse(fieldfit.mirror_symmetric(dict(field, field_origin=(5.31, 0.0))))  # off the axis
        self.assertFalse(fieldfit.mirror_symmetric(dict(field, angle_deg=10.0)))  # turned
        self.assertFalse(fieldfit.mirror_symmetric(dict(field, symmetry=dict(info, symmetric=False))))  # the face is not

    def test_the_peel_keeps_a_symmetric_field_symmetric(self) -> None:
        info = {"symmetric": True, "axis": 4.7, "axis_mm": 4.7, "deviation_mm": 0.0}
        candidate = _candidate(0)
        candidate.update(cells=((1, 3), (0, 4), (0, 4)), rows=3, columns=5, taxels=13, value=13, full=False, width=1.4, margin=0.5, peels=0,
                         field_origin=(0.0, 0.0), symmetry=info)
        candidate["symmetric"] = fieldfit.mirror_symmetric(candidate)
        self.assertTrue(candidate["symmetric"])
        # A point right of the bottom row: both its ends go, the field stays centred.
        peeled = fieldfit.peel_field(candidate, (8.5, 0.7))
        self.assertEqual(peeled["cells"], ((1, 3), (0, 4), (1, 3)))
        self.assertTrue(peeled["symmetric"])
        # A point above the top row: its three cells shrink to one, still centred.
        peeled = fieldfit.peel_field(candidate, (4.7, 6.0))
        self.assertEqual((peeled["cells"], peeled["taxels"], peeled["symmetric"]), (((2, 2), (0, 4), (0, 4)), 11, True))

    def test_symmetric_faces_take_symmetric_fields(self) -> None:
        # The first proposal (rows, columns, taxels) and its exit's chord; every row its own mirror image, centred on the
        # face's axis; then the larger asymmetric field where there is one (before section 22 in brackets).
        cases = [
            # (937 on a long side; 924 next to its 40 mm exit before section 23: the 64-row cap binds on the 150 mm face, so
            # the rows stack at its 20 mm far end; 842 of 64 x 18 before section 24, then 844 of 64 x 17 and the 846 next;
            # since section 26 the tip-first 842 of 64 x 18 again, 1.5 mm nearer the 20 mm end, the 844 and the 846 next)
            ("long_taper", (64, 18, 842), 40.0, (64, 18, 846)),
            ("equilateral", (25, 27, 349), 60.0, None),  # (341; 342 before section 24; 353 before section 26.18's eighth row phases)
            # (440, 0.2 mm off the axis; 440 symmetric before section 24; 24 x 23 before section 26, the 24 x 24 one row
            # nearer the far end as many taxels)
            ("disk", (24, 24, 448), 28.68, None),
            # Since section 24 the cut square's cut: a lattice at 45 degrees to the square (574 on a side before).
            ("cut_square", (33, 33, 577), 7.07, None),
        ] + [(name, None, None, None) for name in ROUNDED]
        for name, shape, chord, larger in cases:
            with self.subTest(plate=name):
                proposals = FieldFitTests._check(self, name, FIELD)
                first = proposals[0]
                metrics = first["metrics"]
                if shape is not None:
                    self.assertEqual((metrics["rows"], metrics["columns"], metrics["taxels"]), shape)
                    self.assertAlmostEqual(first["placement"]["base_from_uv"] and math.dist(first["placement"]["base_from_uv"], first["placement"]["base_to_uv"]), chord, delta=0.01)
                else:
                    self.assertEqual(metrics["taxels"], ROUNDED[name][0])
                self.assertEqual(metrics["angle_deg"], 0.0)
                self.assertTrue(_symmetric_rows(first))
                symmetry = metrics["symmetry"]
                self.assertEqual((symmetry["face"], symmetry["field"], symmetry["field_offset_mm"]), (True, True, 0.0), symmetry)
                self.assertLessEqual(symmetry["deviation_mm"], fieldfit.SYMMETRY_TOLERANCE_MM)
                if larger is not None:
                    # Since section 26 after the field the tip-first one displaced (the long taper's 844).
                    self.assertEqual(_shapes({"proposals": proposals[1:2]}), [(64, 17, 844)])
                    second = proposals[2]["metrics"]
                    self.assertEqual((second["rows"], second["columns"], second["taxels"], second["symmetry"]["field"]), (*larger, False))

    def test_a_field_that_breaks_the_symmetry_leads_with_20_percent_more(self) -> None:
        # The user's decision of 2026-10-27 (section 26.19): the symmetric field leads unless a field that breaks the
        # symmetry holds at least 1.2 times its value; at exactly 1.2 times that field leads.  The rank alone, on one exit
        # and across exits, an asymmetric and a turned field, in taxels and (max_area) in area.
        def field(value: int, order: int, symmetric: bool, tip: float = 10.0, angle: float = 0.0) -> dict:
            candidate = dict(_candidate(value, angle=angle, tip=tip, order=order), symmetric=symmetric)
            candidate["rank"] = fieldfit.field_rank(candidate)
            return candidate

        self.assertEqual(fieldfit.SYMMETRY_GAIN, (120, 100))
        for other, leads in ((119, False), (120, True), (121, True)):
            with self.subTest(other=other):
                self.assertEqual(fieldfit.symmetric_leads(100, other), not leads)
                for order, auto_exit in ((0, False), (1, True)):  # on the symmetric field's exit, on another one
                    found = fieldfit.ordered([field(other, 0, False), field(100, order, True)], auto_exit)
                    self.assertEqual([c["value"] for c in found], [other, 100] if leads else [100, other])
                # A turned field (3 % over the best unturned one too).
                found = fieldfit.ordered([field(other, 0, False, angle=20.0), field(100, 0, True)], False)
                self.assertEqual([c["angle_deg"] for c in found], [20.0, 0.0] if leads else [0.0, 20.0])
        for area, leads in ((1_199_999, False), (1_200_000, True)):
            found = fieldfit.ordered([field(area, 0, False), field(1_000_000, 0, True)], False)
            self.assertEqual(found[0]["symmetric"], not leads)
        # Across exits (section 22's rule): the symmetric exits' leads within the threshold of the most of all the fields go
        # first, the narrow tip choosing among them; then each exit's best symmetric field before that exit's other fields
        # when it holds within the threshold of their best (exit 1's symmetric 100 against its 110, after exit 0's 130).
        most = field(110, 0, False)
        self.assertEqual([c["value"] for c in fieldfit.ordered([most, field(100, 1, True)], True)], [100, 110])
        self.assertEqual([c["value"] for c in fieldfit.ordered([field(130, 0, False), field(110, 1, False), field(100, 1, True)], True)], [130, 100, 110])
        self.assertEqual([c["value"] for c in fieldfit.ordered([field(130, 0, False), field(125, 1, False), field(100, 1, True)], True)], [130, 125, 100])
        narrow, wide = field(100, 1, True, tip=5.0), field(101, 2, True, tip=30.0)
        self.assertEqual([c["order"] for c in fieldfit.ordered([most, wide, narrow], True)], [1, 2, 0])  # the tip
        self.assertEqual([c["order"] for c in fieldfit.ordered([most, field(101, 2, True, tip=30.0), field(97, 1, True, tip=5.0)], True)], [2, 1, 0])

    def test_the_tip_never_flips_the_symmetric_decision(self) -> None:
        # Decided on the search's fields, before the tip step: the symmetric 100 leads an asymmetric 119 (19 % more), its
        # tip-first field a symmetric 97 reaching farther (97 % of the 100), and the 119, 22.7 % over that 97, still follows
        # it: symmetry costs under 20 %, the tip at most 3 % more of the best symmetric field.
        from unittest import mock

        lead = _tip_candidate(100, 40_000_000, symmetric=True)
        queue = fieldfit.ordered([_tip_candidate(119, 39_000_000, x=9.0, rows=11, columns=10), lead], False)
        self.assertEqual([c["value"] for c in queue], [100, 119])
        with mock.patch.object(fieldfit, "tip_pass", _FakePass([_tip_candidate(97, 41_000_000, x=1.0, symmetric=True)])):
            found = fieldfit.tip_first(queue, _tip_options())
        self.assertEqual([(c["value"], c["symmetric"], bool(c.get("tip_lead"))) for c in found], [(97, True, True), (100, True, False), (119, False, False)])
        self.assertEqual(found[0]["tip"]["given"], 3)

    def test_the_threshold_on_faces(self) -> None:
        # The axis-hole plates (AXIS_HOLE, exit their 44 mm bottom edge): no symmetric row crosses the hole (20 x 21 = 420
        # below it), an asymmetric field passes beside it.  58 mm long its 28 x 21 = 500 holds 19.0 % more: the symmetric
        # 420 first, the 500 next; 59 mm long its 29 x 21 = 510 holds 21.4 % more: the 510 first, the symmetric 420 still
        # proposed (third, after a 500).
        for name, shapes in (("axis_hole_58", [(20, 21, 420), (28, 21, 500)]), ("axis_hole_59", [(29, 21, 510), (28, 21, 500), (20, 21, 420)])):
            with self.subTest(plate=name):
                proposals = _Fits.get(self, name, FIELD)[2]["proposals"]
                self.assertEqual(_shapes({"proposals": proposals}), shapes)
                self.assertEqual([p["metrics"]["symmetry"]["field"] for p in proposals], [shape[2] == 420 for shape in shapes])
                self.assertTrue(_symmetric_rows(proposals[[shape[2] for shape in shapes].index(420)]))
        # The named faces.  Section 22's 3 % put a larger field that breaks the symmetry first on the holed plates, the
        # isosceles triangle (its leg's 341, 3.96 % over its base's symmetric 328) and the right triangle (595 on a leg, 3.3 %
        # over the hypotenuse's 576); section 26.17 put every symmetric field first (the holed plate's 247, the round-hole
        # plate's 209).  With 20 %: the holed plates' turned 396 and 344 first again (each plate's symmetric fields must hold
        # the hole's middle column: 62 % and 61 % of them, no longer among the five proposals), the triangles' symmetric
        # fields first (the isosceles triangle's tip-first 322, its 328 next; the right triangle's 576).
        cases = [("holed_plate", (31, 32, 396), False), ("round_hole", (30, 32, 344), False), ("isosceles", (28, 23, 322), True),
                 ("right_triangle", (24, 47, 576), True)]
        for name, first, symmetric in cases:
            with self.subTest(plate=name):
                proposals = _Fits.get(self, name, FIELD)[2]["proposals"]
                metrics = proposals[0]["metrics"]
                self.assertEqual((_shapes({"proposals": proposals[:1]})[0], metrics["symmetry"]["face"], metrics["symmetry"]["field"]), (first, True, symmetric))
                self.assertEqual(metrics["angle_deg"] != 0.0, not symmetric)
                if not symmetric:
                    self.assertFalse(any(p["metrics"]["symmetry"]["field"] for p in proposals))
        self.assertIn((22, 30, 341), _shapes(_Fits.get(self, "isosceles", FIELD)[2]))
        self.assertIn((34, 34, 595), _shapes(_Fits.get(self, "right_triangle", FIELD)[2]))
        # Under 12 rows the exits are those of the fit without the caps (section 23: the symmetry judged on the face as it
        # is): the isosceles triangle's base, its symmetric 328 within 20 % of a leg's 341, so its capped symmetric
        # tip-first 74 first as in section 26.17 (the leg's 12 x 29 = 223 turned 30 degrees fifth); the holed plate's capped
        # exit its 12 x 29 = 285 first, 22.8 % over that side's symmetric 8 x 29 = 232 (next).
        capped = _Fits.get(self, "isosceles", dict(FIELD, max_rows=12))[2]["proposals"]
        self.assertEqual([(p["metrics"]["taxels"], p["metrics"]["symmetry"]["field"]) for p in capped[:2]], [(74, True), (76, True)])
        self.assertEqual((capped[4]["metrics"]["taxels"], capped[4]["metrics"]["angle_deg"]), (223, 30.0))
        capped = _Fits.get(self, "holed_plate", dict(FIELD, max_rows=12))[2]["proposals"]
        self.assertEqual([(p["metrics"]["taxels"], p["metrics"]["symmetry"]["field"]) for p in capped[:2]], [(285, False), (232, True)])
        if CRANK.exists():
            # No symmetric exit: the crank pad's 688.
            for name in ("crank", "crank_auto"):
                first = _Fits.get(self, name, FIELD)[2]["proposals"][0]["metrics"]
                self.assertEqual((first["taxels"], first["symmetry"]["face"], first["symmetry"]["field"]), (688, False, False))

    def test_a_symmetric_exit_within_the_threshold_is_not_turned(self) -> None:
        # rotation auto: an exit whose best symmetric field holds within 20 % of its best unturned field takes no turned
        # frame (a turn breaks the symmetry): the 58 mm axis-hole plate, the isosceles triangle's base, the right
        # triangle's hypotenuse; beyond it, the exit is turned as any other: the 59 mm plate (21.4 %), the holed plates'
        # sides 0 and 2 (the turned 396 and 344 first).
        for name, turned in (("axis_hole_58", set()), ("axis_hole_59", {0}), ("isosceles", {1, 2}), ("right_triangle", {0, 2}),
                             ("holed_plate", {0, 2}), ("round_hole", {0, 2})):
            with self.subTest(plate=name):
                result = _Fits.get(self, name, FIELD)[2]
                symmetric = {base["side"] for base in result["bases"] if base["angle_deg"] == 0.0 and base.get("symmetric_candidates")}
                self.assertEqual({base["side"] for base in result["bases"] if base["angle_deg"] != 0.0}, turned)
                self.assertTrue(symmetric)
                if name in ("axis_hole_58", "isosceles", "right_triangle"):
                    self.assertEqual(symmetric & turned, set())
                else:
                    self.assertTrue(symmetric & turned)

    def test_a_border(self) -> None:
        # With the user's border (docs/CAD_BORDER.md) the region the taxels may take is the border's part on the surface:
        # the border's edges on the surface mirror onto its own, the surface's outline inside the border onto its own.
        from surface import api as api_module

        def fitted(outline: list, uv: list) -> tuple:
            data = F.stl_bytes(F.plate(outline, 3.0))
            mesh = read_stl(data)
            centre = (math.fsum(p[0] for p in outline) / len(outline), math.fsum(p[1] for p in outline) / len(outline), 3.0)
            selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, centre)}]}
            result = fit.fit_route({"selection": selection, "base": "auto", "border": {"uv": uv}, "options": {"pitch_mm": 2.0}}, data)
            bases = [base["symmetric"] for base in result["bases"] if base["angle_deg"] == 0.0]
            return data, selection, result, bases

        plate = [(0.0, 0.0), (60.0, 0.0), (60.0, 40.0), (0.0, 40.0)]  # its chart: u -20..20 across, v -30..30 along
        # An isosceles trapezoid inside the plate: symmetric about its two parallel edges, not its legs; the first field
        # symmetric, every taxel inside the border (the map's taxels_inside_border), the larger asymmetric 243 next.  Since
        # section 26 each exit's tip-first field before its lead: the symmetric 234 (98.3 % of the 238) first, then the 238,
        # then the leg's 239 (98.4 % of its 243) and the 243.
        data, selection, result, bases = fitted(plate, [[-15.0, -25.0], [15.0, -25.0], [8.0, 20.0], [-8.0, 20.0]])
        self.assertEqual(sorted(bases), [False, False, True, True])
        first = result["proposals"][0]
        self.assertEqual((first["metrics"]["taxels"], first["metrics"]["symmetry"]["field"]), (234, True))
        self.assertTrue(_symmetric_rows(first))
        self.assertEqual([(p["metrics"]["taxels"], p["metrics"]["symmetry"]["field"]) for p in result["proposals"][1:4]], [(238, True), (239, False), (243, False)])
        mapped = place.map_route({"selection": selection, "placement": first["placement"], "design": first["design"]}, data)
        self.assertTrue(mapped["ok"])
        self.assertTrue(next(r for r in mapped["verification"] if r["rule"] == "taxels_inside_border")["passed"])
        # A right trapezoid there: no exit symmetric.
        self.assertEqual(fitted(plate, [[-15.0, -25.0], [15.0, -25.0], [15.0, 20.0], [-8.0, 20.0]])[3], [False] * 4)
        # A rectangle reaching beyond the plate's sides, symmetric with it: every exit symmetric (the plate's sides inside
        # the border mirror onto each other).
        data, selection, result, bases = fitted(plate, [[-25.0, -10.0], [25.0, -10.0], [25.0, 10.0], [-25.0, 10.0]])
        self.assertEqual(bases, [True] * 4)
        self.assertTrue(result["proposals"][0]["metrics"]["symmetry"]["field"])
        # A square inside the right triangle (no symmetric field without the border on its legs): its 4 edges symmetric.
        corners = [(-23.333333, 23.333333), (-23.333333, -46.666667), (46.666667, 23.333333)]
        sides = [math.dist(corners[1], corners[2]), math.dist(corners[0], corners[2]), math.dist(corners[0], corners[1])]
        middle = [math.fsum(side * corner[k] for side, corner in zip(sides, corners)) / math.fsum(sides) for k in (0, 1)]
        square = [[middle[0] + dx, middle[1] + dy] for dx, dy in ((-10.0, -10.0), (10.0, -10.0), (10.0, 10.0), (-10.0, 10.0))]
        data, selection, result, bases = fitted(PLATES["right_triangle"], square)
        self.assertEqual(bases, [True] * 4)
        self.assertEqual((result["proposals"][0]["metrics"]["taxels"], result["proposals"][0]["metrics"]["symmetry"]["field"]), (100, True))

    def test_the_fingerprint_of_a_symmetric_fit(self) -> None:
        # The isosceles triangle's fit (a leg's 341 first since section 24): Python 3.9 and 3.12 (the suite runs on both)
        # and any hash seed give the same proposals.
        data, selection, result, _ = _Fits.get(self, "isosceles", FIELD)
        self.assertEqual(_fingerprint(result), FINGERPRINTS["isosceles"])
        code = ("import sys; sys.path.insert(0, 'tests'); import defaults_of_before; defaults_of_before.start(cleanup=False); "
                "import test_field_fit as t; print(t._fingerprint_of('isosceles'))")
        environment = dict(os.environ, PYTHONHASHSEED="7", PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
        output = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
        self.assertEqual(output.stdout.strip(), FINGERPRINTS["isosceles"])


# The crank pad's 683 (34 x 34) before section 24, ROW_01 first: the doubled rows (2, 9-12, 19-22, 29-32 one cell short of
# the staircase) are where an interior step corner's zone left the hypotenuse.
CRANK_683 = [[29, 34], [29, 34], [28, 34], [27, 34], [26, 34], [25, 34], [24, 34], [23, 34], [23, 34], [22, 34], [21, 34], [20, 34],
             [19, 34], [18, 34], [17, 34], [16, 34], [15, 34], [14, 34], [14, 34], [13, 34], [12, 34], [11, 34], [10, 34], [9, 34],
             [8, 34], [7, 34], [6, 34], [5, 34], [5, 34], [4, 34], [3, 34], [2, 34], [1, 34], [1, 34]]
# A triangle of free runs (bottom to top: cells 0-3, 1-3, 2-3) and, per blocked zone (row, kind, cell; kinds bottom left,
# bottom right, top left, top right), the largest field by section 24's rule and by section 16's (every interior zone held).
TRIANGLE = [[3, 3, 3, 3], [-1, 3, 3, 3], [-1, -1, 3, 3]]
TRIANGLE_CASES = (
    ((1, 2, 1), 9, 8),  # row 1's top left: a convex corner (row 2 starts right of it), left out
    ((0, 2, 0), 9, 8),  # row 0's top left: convex, left out
    ((1, 0, 1), 8, 8),  # row 1's bottom left: concave (row 0 reaches farther), held
    ((2, 0, 2), 8, 8),  # row 2's bottom left: concave, held
    ((1, 1, 3), 8, 7),  # row 1's bottom right: an aligned end (rows 0 and 1 both end at 3), held
    ((0, 3, 3), 8, 8),  # row 0's top right: aligned, held
)


def _zones_blocked(columns: int, rows: int, row: int, kind: int, cell: int) -> list:
    flags = [[True] * columns for _ in range(4)]
    flags[kind][cell] = False
    return [tuple(flags) if j == row else None for j in range(rows)]


def _side_problems(data: bytes, selection: dict, proposal: dict) -> list:
    """Our own check of section 24's rule on a built proposal: F's boundary (base frame) on the surface's outline but within
    the margin plus the corner reach of F's convex vertices (the convex corners of F; an aligned end makes no vertex, a
    concave one a concave vertex), sampled every 0.1 mm."""

    generated = generate_design(proposal["design"])
    origin = proposal["placement"]["field_origin_base"]
    outline = [_frame(proposal["placement"]).to_base(p) for p in _chart_outline(data, selection)]
    body = fieldfit.field_body(generated, origin)
    matrix = generated["design"]["matrix"]
    reach = min(0.5, min(matrix["taxel_width_mm"], matrix["taxel_height_mm"]) / 3)
    count = len(body)
    convex = [(body[k][0] - body[k - 1][0]) * (body[(k + 1) % count][1] - body[k][1])
              - (body[k][1] - body[k - 1][1]) * (body[(k + 1) % count][0] - body[k][0]) > 0 for k in range(count)]
    problems = []
    for k in range(count):
        a, b = body[k], body[(k + 1) % count]
        length = math.dist(a, b)
        start = 0.5 + reach if convex[k] else 0.0
        end = length - (0.5 + reach if convex[(k + 1) % count] else 0.0)
        steps = max(1, int((end - start) / 0.1))
        for i in range(steps + 1):
            t = (start + (end - start) * i / steps) / length if end > start else None
            if t is None:
                break
            point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if not point_in_polygon(point, outline) and min(_box_distance(point, outline[q - 1], outline[q]) for q in range(len(outline))) > 1e-6:
                problems.append((k, point))
                break
    return problems[:3]


class ConvexCornerTests(unittest.TestCase):
    """The user's rule of 2026-10-25 (P5-diagonal-bus.md section 24): the corner tolerance at every convex corner of F (a
    run's end the neighbouring row's run does not reach), not only at the field's four corners; an aligned or a concave
    end keeps its whole margin.  The DP exact for it (against brute force), F's check and the map's records with it, the
    crank pad's staircase one cell longer at its doubled rows, and its hypotenuse one straight line."""

    def test_the_rule_on_hand_made_grids(self) -> None:
        for (row, kind, cell), now, before in TRIANGLE_CASES:
            zones = _zones_blocked(4, 3, row, kind, cell)
            with self.subTest(zone=(row, kind, cell)):
                self.assertEqual(fieldfit.best_convex(TRIANGLE, TRIANGLE, 0, 3, 0, 2, 0, None, zones)[0], now)
                self.assertEqual(_brute(TRIANGLE, TRIANGLE, zones=zones), now)
                self.assertLessEqual(before, now)
        # Every interior zone blocked: the staircase still holds (its corners at its ends convex or concave as they are),
        # an aligned pair of runs not.
        blocked = [tuple([False] * 4 for _ in range(4)) for _ in range(3)]
        self.assertEqual(fieldfit.best_convex(TRIANGLE, TRIANGLE, 0, 3, 0, 2, 0, None, blocked)[0], _brute(TRIANGLE, TRIANGLE, zones=blocked))
        full = [[3, 3, 3, 3]] * 3
        self.assertEqual(fieldfit.best_convex(full, full, 0, 3, 0, 2, 0, None, blocked), (4, [(2, 0, 3)]))
        self.assertEqual(fieldfit.best_rectangle(full, full, 9, 9, 0, blocked)[0], 4)
        # The symmetric DP on a symmetric triangle (cells 0-4, 1-3, 2-2): the middle row's top zones convex, left out.
        sym = [[4] * 5, [-1, 3, 3, 3, -1], [-1, -1, 2, -1, -1]]
        zones = [None, tuple([True] * 5 if kind < 2 else [kind != 2 or c != 1 for c in range(5)] for kind in range(4)), None]
        self.assertEqual(fieldfit.best_symmetric(sym, sym, 5, 0, 2, 99, 0, zones)[0], 9)
        self.assertEqual(_brute(sym, sym, zones=zones, symmetric=True), 9)

    def test_the_tables_against_a_plain_dp(self) -> None:
        # The zone tables (section 24) against the definition on random staircases: grids whose runs shrink row by row,
        # zones blocked at random (the brute force of the module's other tests, on wider grids).
        rng = random.Random(24)
        for trial in range(120):
            rows, columns = rng.randint(2, 4), rng.randint(3, 6)
            plain = []
            for j in range(rows):
                low = rng.randint(0, columns - 1)
                plain.append([columns - 1 if a >= low else -1 for a in range(columns)])
            zones = [tuple([rng.random() < 0.6 for _ in range(columns)] for _ in range(4)) for _ in range(rows)]
            with self.subTest(trial=trial):
                count, spans = fieldfit.best_convex(plain, plain, 0, columns - 1, 0, rows - 1, 0, None, zones)
                self.assertEqual(count, _brute(plain, plain, zones=zones))
                if count:
                    selection = [None] * rows
                    for j, a, b in spans:
                        selection[j] = (a, b)
                    self.assertTrue(_free(selection, plain, plain, zones))

    def test_the_crank_gains_along_its_hypotenuse(self) -> None:
        # 683 -> 696: rows 2, 9-12, 19-22 and 29-32 one cell longer toward the hypotenuse (the doubled rows of the
        # staircase, held back by the zones at their interior step corners), the exit still the 70 mm leg.  Since section
        # 26 the 696 is the second proposal, after the tip-first 688 (TipFirstTests).
        data, selection, result, _ = _Fits.get(self, "crank", FIELD)
        first = result["proposals"][1]
        self.assertEqual(_shapes(result)[:2], [(34, 34, 688), (34, 34, 696)])
        mask = [list(run) for run in design_mask(first["design"])]
        longer = [k + 1 for k, (now, before) in enumerate(zip(mask, CRANK_683)) if now != before]
        self.assertEqual(longer, [2, 9, 10, 11, 12, 19, 20, 21, 22, 29, 30, 31, 32])
        self.assertTrue(all(now[0] == before[0] - 1 and now[1] == before[1] for now, before in zip(mask, CRANK_683) if now != before))
        mapped = place.map_route({"selection": selection, "placement": first["placement"], "design": first["design"]}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        overhang = next(r for r in mapped["verification"] if r["rule"] == "field_corner_overhang")
        self.assertTrue(0.3 < overhang["measured"] <= 0.5, overhang)
        # Every convex corner of the staircase has its zone: two per step of the hypotenuse and the field's corners.
        zones = fieldfit.corner_zones(generate_design(first["design"]))
        self.assertEqual(len(zones), 32)

    def test_every_proposal_keeps_f_on_the_surface(self) -> None:
        # P on the surface, F's convex corners off it by at most 0.5 mm, and F's boundary away from its convex corners (the
        # middle third of every side, an aligned or a concave end) on it; every proposal mapped with every record passing.
        for name in ("crank", "right_triangle", "equilateral", "isosceles", "fin", "disk", "holed_plate", "cut_square"):
            data, selection, result, _ = _Fits.get(self, name, FIELD)
            for proposal in result["proposals"]:
                with self.subTest(face=name, proposal=proposal["rank"]):
                    self.assertEqual(_corner_problems(data, selection, proposal), [])
                    self.assertEqual(_side_problems(data, selection, proposal), [])
                    mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
                    self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
                    records = {r["rule"]: r for r in mapped["verification"]}
                    self.assertLessEqual(records["field_corner_overhang"]["measured"], fieldfit.CORNER_TOLERANCE_MM)
                    self.assertTrue(records["field_clearance"]["passed"])

    def test_the_parts_leave_out_only_convex_corners(self) -> None:
        # A staircase with an aligned pair of runs (rows 2 and 3 alike): F's parts leave out the zones at the convex
        # corners only; the aligned ends' margin and every side's middle stay in.
        design = generate_design({"template_id": "surface_matrix_v1", "matrix": {"rows": 4, "columns": 4, "pitch_x_mm": 2.0, "pitch_y_mm": 2.0,
                                                                               "taxel_width_mm": 1.4, "taxel_height_mm": 1.4,
                                                                               "mask": [[3, 4], [2, 4], [2, 4], [1, 4]]},
                                  "routing": {"row_sides": "both"}})
        self.assertTrue(design["ok"], design["validation"]["errors"])
        slabs = fieldfit._p_slabs(design)
        corners = fieldfit.convex_corners(slabs)
        # P's slabs bottom to top: ROW_04 (cells 1-4); the filler, ROW_03 and ROW_02 (2-4, aligned: no step between them)
        # and their filler; the filler and ROW_01 (3-4).  The right side is straight: only the field's bottom and top right
        # corners are convex there; on the left every step's outer corner.
        self.assertEqual(len(slabs), 3)
        self.assertEqual(corners, [(True, True, True, False), (False, False, True, False), (False, False, True, True)])
        zones = fieldfit.corner_zones(design)
        self.assertEqual(len(zones), 6)
        parts = fieldfit.field_parts(design)
        margin = 0.5
        reach = round(1.4 / 3, 9)

        def covered(point) -> bool:
            return any(point_in_polygon(point, part) for part in parts)

        for (cx, cy), sx, sy, _, _ in zones:
            # Outside the corner (beyond both sides) a zone is left out; along the side past the reach it is held.
            self.assertFalse(covered((cx + sx * margin / 2, cy + sy * margin / 2)))
            self.assertTrue(covered((cx + sx * margin / 2, cy - sy * (reach + 0.05))))
        # The aligned ends of ROW_03 and ROW_02 (x = 2 mm from P's left): the margin beside them is held, ROW_03's
        # bottom left (a concave corner: ROW_04 reaches farther) too, but within the reach of ROW_02's top left corner.
        low, high, x0, _ = slabs[1]
        self.assertTrue(covered((x0 - margin / 2, 3.7)))
        self.assertTrue(covered((x0 - margin / 2, 2.1)))
        self.assertTrue(covered((x0 - margin / 2, high - reach - 0.05)))
        self.assertFalse(covered((x0 - margin / 2, high + margin / 2)))

    def test_the_crank_hypotenuse_is_one_line(self) -> None:
        # The Row board's outline (base frame, the exit at the bottom): from the tip corner down the hypotenuse one straight
        # edge to the convex bend into the funnel (the lanes turning down beside the full bottom rows); the side convex
        # all the way to the funnel arm (no S-shaped kink at the tip); the lanes inside it; and the convex sides grow the
        # board by little (against the build without them: diagonal-bus/8's outline of the same field).  The 696 field, the
        # second proposal since section 26 (the tip-first 688's narrower ROW_01 bends its hull 10.4 mm below the tip).
        from unittest import mock
        from engine import diagonal

        _, _, result, _ = _Fits.get(self, "crank", FIELD)
        first = result["proposals"][1]
        self.assertEqual(first["metrics"]["taxels"], 696)
        built = generate_design(first["design"])
        ring = fit.board_outlines_base(built, (0.0, 0.0))["row"]
        count = len(ring)
        top = max(y for _, y in ring)
        tip = min((k for k in range(count) if ring[k][1] > top - 1e-6), key=lambda k: ring[k][0])
        side = [tip]
        while ring[(side[-1] + 1) % count][0] <= ring[side[-1]][0] + 10.0 and len(side) < count:
            side.append((side[-1] + 1) % count)
            if ring[side[-1]][0] - ring[side[-2]][0] > 10.0:
                break
        points = [ring[k] for k in side]
        turns = [math.degrees(math.atan2((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]),
                                         (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]))) for a, b, c in zip(points, points[1:], points[2:])]
        self.assertTrue(all(turn > 0.0 for turn in turns), turns)  # convex: no S-kink
        # The first edge: the hypotenuse, more than 80 mm, at 45 degrees to the exit like the staircase.
        a, b = points[0], points[1]
        self.assertGreater(math.dist(a, b), 80.0)
        self.assertAlmostEqual(abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))), 134.7, delta=0.5)
        # The Row lanes inside the outline by the copper-to-edge rule (0.3 mm).
        origin = (0.0, 0.0)
        board = built["boards"]["row"]
        grid = board["grid_registration"]["active_region"]
        for route in board["layers"]["top_copper"]["routes"]:
            for x, y in route["points"]:
                point = (grid["width"] - (x - grid["x"]) + origin[0], y - grid["y"] + origin[1])
                self.assertTrue(point_in_polygon(point, ring))
        # Against the same field without the convex sides: the old outline inside the new, the new within the bound.
        diagonal._pair_text.cache_clear()
        try:
            with mock.patch.object(diagonal, "_convex_sides", lambda ring, level, rounded, anchors, depth: (ring, [])):
                plain = generate_design(first["design"])
        finally:
            diagonal._pair_text.cache_clear()
        old = fit.board_outlines_base(plain, (0.0, 0.0))["row"]
        self.assertTrue(all(point_in_polygon(p, ring) or min(_segment_distance(p, ring[k - 1], ring[k]) for k in range(count)) < 1e-6 for p in old))
        depth = 2 * 2.0 / math.sqrt(5)
        for k in range(count):
            p, q = ring[k], ring[(k + 1) % count]
            middle = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            if not point_in_polygon(middle, old):
                self.assertLessEqual(min(_segment_distance(middle, old[i - 1], old[i]) for i in range(len(old))), depth)
        self.assertEqual(board["layers"], plain["boards"]["row"]["layers"])


class CadWithoutRectanglesTests(unittest.TestCase):
    """The user's decision of 2026-10-26 (P5-diagonal-bus.md section 26.16): "what CAD generates depends only on the area
    selected in CAD"; the rectangular mode (rows, columns, the traces' parameters) is used on its own, without CAD.  CAD
    mode has no ``shape: rectangle``, no generic template and no rectangle preference (:data:`surface.fit.CAD_ONLY`): a
    fit naming them is refused, the values it fits with are accepted as before (older clients), and a saved placement
    naming them maps as fitted.  A full rectangle stays a field like any other, proposed where it ranks."""

    REMOVED = ({"shape": "rectangle"}, {"shape": "rectangle", "containment": "field"}, {"template": "generic"},
               {"template": "generic", "containment": "board"}, {"rectangle_preference_pct": 5}, {"rectangle_preference_pct": 100},
               {"rectangle_preference_pct": "0"}, {"rectangle_preference_pct": False}, {"shape": True}, {"template": "custom"})

    def test_the_options(self) -> None:
        self.assertEqual(fit.CAD_ONLY, {"template": "surface", "shape": "fill", "rectangle_preference_pct": 0})
        self.assertNotIn("rectangle_preference_pct", fit.DEFAULT_OPTIONS)
        self.assertFalse(hasattr(fit, "GENERIC_MAX_COLUMNS"))
        plain = fit.parse_options({})
        self.assertEqual((plain["template"], plain["shape"], plain["max_columns"]), ("surface", "fill", 64))
        # The values CAD mode fits with: accepted, the same options (the preference's 0, off, dropped).
        self.assertEqual(fit.parse_options({"template": "surface", "shape": "fill", "rectangle_preference_pct": 0}), plain)
        self.assertEqual(fit.parse_options({"rectangle_preference_pct": 0.0}), plain)
        for options in self.REMOVED:
            with self.subTest(options=options), self.assertRaises(SurfaceError) as raised:
                fit.parse_options(options)
            self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")
            self.assertIn("rectangular mode", raised.exception.message)
            self.assertIn(f"options.{next(iter(options))}", raised.exception.message)

    def test_a_fit_refuses_them_and_a_saved_placement_maps_as_fitted(self) -> None:
        data, selection, result, _ = _Fits.get(self, "right_triangle", FIELD)
        for options in self.REMOVED[:5]:
            with self.subTest(options=options), self.assertRaises(SurfaceError) as raised:
                fit.fit_route({"selection": selection, "options": options}, data)
            self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")
        proposal = result["proposals"][0]
        self.assertNotIn("rectangle_preference_pct", proposal["placement"]["options"])
        plain = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        # A placement saved before section 26.16 (its options as that fit echoed them, what it accepted: shape rectangle with
        # containment field named on the surface template), and a map request's own options naming them: the map fits
        # nothing (the design's template_id picks the template; shape and template only default a containment the options
        # do not name, test_a_saved_placement_holds_only_what_a_fit_accepted).
        saved = dict(proposal["placement"], options=dict(proposal["placement"]["options"], template="surface", shape="rectangle",
                                                         rectangle_preference_pct=30))
        for header in ({"placement": saved}, {"placement": proposal["placement"], "options": saved["options"]}):
            with self.subTest(header=sorted(header)):
                mapped = place.map_route(dict(header, selection=selection, design=proposal["design"]), data)
                self.assertTrue(mapped["ok"])
                self.assertEqual(mapped["verification"], plain["verification"])
                self.assertEqual(mapped["taxels"], plain["taxels"])
        self.assertEqual(fit.parse_options(saved["options"], mapping=True), fit.parse_options(proposal["placement"]["options"]))

    def test_a_saved_placement_holds_only_what_a_fit_accepted(self) -> None:
        # The map takes the three as a placement saved before section 26.16 holds them: exactly what a fit then accepted
        # (0024bdb: shape rectangle or fill, template surface or generic, a preference of 0-100 %; on the generic template
        # not shape fill, containment field or more than 32 columns named, which that fit set itself when they were not
        # named), anything else is E_SURFACE_REQUEST with that fit's message (round 4's map took the generic ones: 88 of
        # 9900 fuzzed option sets, section 26.18).
        self.assertEqual(fit.SAVED_VALUES, {"template": ("surface", "generic"), "shape": ("rectangle", "fill"),
                                            "rectangle_preference_pct": (0.0, 100.0)})
        self.assertEqual(fit.SAVED_GENERIC_MAX_COLUMNS, 32)
        plain = fit.parse_options({})
        for options in ({"shape": "rectangle"}, {"shape": "fill"}, {"template": "generic"}, {"template": "surface"},
                        {"rectangle_preference_pct": 0}, {"rectangle_preference_pct": 100}, {"rectangle_preference_pct": 37.5}):
            with self.subTest(options=options):
                self.assertEqual(fit.parse_options(options, mapping=True), plain)
        for options in ({"template": "generic", "shape": "rectangle", "containment": "board", "max_columns": 32},
                        {"template": "generic", "containment": "board"}, {"template": "surface", "shape": "fill", "max_columns": 64},
                        {"shape": "rectangle", "containment": "field", "max_columns": 40}):
            with self.subTest(options=options):
                parsed = fit.parse_options(options, mapping=True)
                self.assertEqual((parsed["template"], parsed["shape"]), ("surface", "fill"))
        for options, message in (({"shape": "circle"}, "options.shape must be one of rectangle, fill."), ({"shape": True}, "options.shape"),
                                 ({"template": {"id": "surface"}}, "options.template must be one of surface, generic."),
                                 ({"template": "custom"}, "options.template"),
                                 ({"rectangle_preference_pct": 500}, "options.rectangle_preference_pct must be a number within 0..100."),
                                 ({"rectangle_preference_pct": "abc"}, "options.rectangle_preference_pct must be a number."),
                                 ({"rectangle_preference_pct": False}, "options.rectangle_preference_pct must be a number."),
                                 ({"rectangle_preference_pct": -1}, "options.rectangle_preference_pct"),
                                 ({"template": "generic", "shape": "fill"}, "options.shape fill needs the surface template"),
                                 ({"template": "generic", "containment": "field"}, "options.containment field needs the surface template"),
                                 ({"template": "generic", "max_columns": 33, "containment": "board"}, "options.max_columns is at most 32"),
                                 ({"template": "generic", "shape": "rectangle", "max_columns": 64}, "options.max_columns is at most 32")):
            with self.subTest(options=options), self.assertRaises(SurfaceError) as raised:
                fit.parse_options(options, mapping=True)
            self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")
            self.assertIn(message, raised.exception.message)
        # place.map_options reads shape and template only to default the containment of options that name none (a
        # placement saved before the option, a map request's own): shape rectangle or the generic template took the whole
        # board, as such a fit did; the map then checks the board rules on a diagonal Row bus's proposal too.
        data, selection, result, _ = _Fits.get(self, "right_triangle", FIELD)
        proposal = result["proposals"][0]
        bare = {k: v for k, v in proposal["placement"]["options"].items() if k not in ("containment", "shape", "template")}
        for extra, containment, rule in (({}, "field", "field_clearance"), ({"shape": "fill", "template": "surface"}, "field", "field_clearance"),
                                         ({"shape": "rectangle"}, "board", "board_clearance"),
                                         ({"template": "generic", "max_columns": 32}, "board", "board_clearance")):
            with self.subTest(options=extra):
                options = fit.parse_options(place.map_options(dict(bare, **extra), proposal["design"]), mapping=True)
                self.assertEqual(options["containment"], containment)
                mapped = place.map_route({"selection": selection, "placement": dict(proposal["placement"], options=dict(bare, **extra)),
                                          "design": proposal["design"]}, data)
                self.assertIn(rule, [record["rule"] for record in mapped["verification"]])

    def test_a_rectangular_selection_takes_a_full_field(self) -> None:
        # A full field is a masked field with every position: on the 40 x 24 mm plate the fill fit's first proposal is the
        # full 19 x 11 = 209 (the rectangle the search's full candidates find, centred, symmetric), no mask.
        proposals = FieldFitTests._check(self, "rectangle", FIELD)
        first = proposals[0]
        self.assertIsNone(design_mask(first["design"]))
        self.assertEqual((first["metrics"]["rows"], first["metrics"]["columns"], first["metrics"]["taxels"]), RECTANGULAR_FIELD)


class RectangleCapTests(unittest.TestCase):
    """P5-diagonal-bus.md section 26a: the full rectangle's column cap applies to a run's end before its right zone flags are
    read (55ae8fe read the uncapped end's flags and returned a rectangle ending on a blocked zone on 21 of these 3000
    grids); and ``_make``'s corner count no longer shadows the candidate's kind."""

    def test_the_cap_before_the_zones_against_brute_force(self) -> None:
        rng = random.Random(5)
        binding = 0
        for trial in range(3000):
            rows, columns = rng.randint(1, 4), rng.randint(1, 5)
            plain, up = _random_grid(rng, rows, columns, rng.choice((0.6, 0.85, 1.0)), rng.random() < 0.5)
            zones = [None if rng.random() < 0.3 else tuple([rng.random() < 0.7 for _ in range(columns)] for _ in range(4)) for _ in range(rows)]
            caps = (rng.randint(1, 4), rng.randint(1, 5))
            binding += caps[1] < columns
            found = fieldfit.best_rectangle(plain, up, caps[0], caps[1], 0, zones)
            with self.subTest(trial=trial):
                self.assertEqual(found[0], _brute(plain, up, caps, rectangle=True, zones=zones))
                if found[0]:
                    _, height, width, row, a = found
                    selection = [None] * rows
                    for j in range(row, row + height):
                        selection[j] = (a, a + width - 1)
                    self.assertTrue(width <= caps[1] and _free(selection, plain, up, zones))
        self.assertGreater(binding, 1000)

    def test_a_capped_end_on_a_blocked_zone(self) -> None:
        # Two rows of 4 free cells; row 1's bottom right zone blocked at cell 1: with a cap of 2 columns the rectangle [0, 1]
        # needs that zone (an aligned end), so the 2 x 2 lies at [1, 2] (the zone of cell 2 free; 55ae8fe gave [0, 1]).
        plain = [[3, 3, 3, 3], [3, 3, 3, 3]]
        zones = [None, ([True] * 4, [True, False, True, True], [True] * 4, [True] * 4)]
        self.assertEqual(fieldfit.best_rectangle(plain, plain, 2, 2, 0, zones), (4, 2, 2, 0, 1))
        self.assertEqual(_brute(plain, plain, (2, 2), rectangle=True, zones=zones), 4)

    def test_the_candidate_keeps_its_kind(self) -> None:
        _, _, result, _ = _Fits.get(self, "rounded_4", FIELD)
        data, point, base = _Fits.case("rounded_4")
        mesh = read_stl(data)
        from surface import api as api_module

        _, chart = api_module.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, point)}]})
        options = fit.parse_options(FIELD)
        bases = fit.choose_bases(base, api_module.boundary_sides(mesh, chart), mesh, chart)
        found = fieldfit.search_fields(chart, bases, options, fit.load_profile_cached("surface"), fit.surface_obstacles(mesh, chart, options), [])
        self.assertTrue(found)
        self.assertTrue(all(candidate["kind"] in ("rectangle", "shaped") for candidate in found))
        self.assertTrue(any(candidate["corners"] for candidate in found))  # rows with zone flags (the old loop set kind 3 there)


def _random_band(rng: random.Random, rows: int, columns: int) -> list:
    """A lattice's filler band per row (``fieldfit.lattice``'s ``band``: per cell the end of its free run)."""

    return [_ends([rng.random() < rng.choice((0.5, 0.8, 1.0)) for _ in range(columns)]) for _ in range(rows)]


class FillerBandTests(unittest.TestCase):
    """P5-diagonal-bus.md section 26b: at sparse pitches (p - w > 2 m) the engine's filler between two rows spans their
    common extent only, so the shaped DPs ask the filler band free there, ``band[j][max(a, a')] >= min(b, b')``, exactly
    (55ae8fe held it over the lower row's whole run: pointed fingertips stayed bare).  Full rectangles keep ``up``."""

    def test_the_dps_against_brute_force(self) -> None:
        rng = random.Random(26)
        changed = 0
        for trial in range(500):
            rows, columns = rng.randint(1, 4), rng.randint(1, 5)
            plain, _ = _random_grid(rng, rows, columns, rng.choice((0.6, 0.85, 1.0)), False)
            band = _random_band(rng, rows, columns)
            up = [list(map(min, ends, filler)) for ends, filler in zip(plain, band)]  # the band over the whole run
            zones = None if rng.random() < 0.4 else [None if rng.random() < 0.3 else tuple([rng.random() < 0.7 for _ in range(columns)] for _ in range(4))
                                                     for _ in range(rows)]
            cap = rng.randint(1, columns)
            with self.subTest(trial=trial, plain=plain, band=band, zones=zones):
                want = _brute(plain, up, zones=zones, band=band)
                changed += want != _brute(plain, up, zones=zones)
                per_row: list = []
                count, spans = fieldfit.best_convex(plain, up, 0, columns - 1, 0, rows - 1, 0, None, zones, band, per_row)
                self.assertEqual(count, want)
                if count:
                    selection = [None] * rows
                    for j, a, b in spans:
                        selection[j] = (a, b)
                    self.assertTrue(_is_convex(selection) and _free(selection, plain, up, zones, band))
                for top in range(rows):
                    found = per_row[top] if top < len(per_row) else None
                    self.assertEqual(found[0] if found else 0, _brute(plain, up, zones=zones, band=band, top=top))
                self.assertEqual(fieldfit.best_symmetric(plain, up, columns, 0, rows - 1, cap, 0, zones, False, band)[0],
                                 _brute(plain, up, (99, cap), zones=zones, symmetric=True, band=band))
                self.assertEqual(fieldfit.best_symmetric(plain, up, columns, 0, rows - 1, cap, 0, zones, True, band)[0],
                                 _brute(plain, up, (99, cap), rectangle=True, zones=zones, symmetric=True, band=band))
                # A full rectangle's rows share their runs: up (the band over the whole run) is exact there.
                self.assertEqual(fieldfit.best_rectangle(plain, up, 99, cap, 0, zones)[0], _brute(plain, up, (99, cap), rectangle=True, zones=zones, band=band))
                threshold = rng.randint(0, 6)
                self.assertEqual(fieldfit.best_convex(plain, up, 0, columns - 1, 0, rows - 1, threshold, None, zones, band)[0], want if want > threshold else 0)
        self.assertGreater(changed, 50)  # the common extent frees fields the whole run's band does not (65 of 500)

    def test_the_lattice_band(self) -> None:
        # band[j][c] >= d exactly when the filler band of row j (Y(j) + w + m to Y(j + 1) - m) is free from X(c) - m to
        # X(d) + w + m; 4 mm at fill 0.6 is sparse, 2 mm at fill 0.7 is not (no band, up is plain).
        from surface import api as api_module

        mesh = F.mesh(F.holed_plate())
        _, chart = api_module.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (5.0, 5.0, 3.0))}]})
        options = fit.parse_options({})
        side = fit.choose_bases("auto", api_module.boundary_sides(mesh, chart), mesh, chart)[0]
        space = fill.FreeSpace(chart, fit.BaseFrame(side, 0.0), fit.surface_obstacles(mesh, chart, options), 0.0, side["edges"])
        margin = 0.5
        dense = fieldfit.lattice(space, 2.0, fit._electrode(2.0, 0.7), margin, (0.0, 0.0))
        self.assertIsNone(dense["band"])
        pitch, width = 4.0, fit._electrode(4.0, 0.6)
        self.assertGreater(pitch - width, 2 * margin)
        rng = random.Random(4)
        checked = 0
        for phase in ((0.3, 0.2), (1.0, 3.0), (2.5, 0.7)):  # off the outline's extremes (rect_free is open there)
            grid = fieldfit.lattice(space, pitch, width, margin, phase)
            self.assertEqual(len(grid["band"]), grid["rows"])
            for j in range(grid["rows"]):
                self.assertEqual(grid["up"][j], list(map(min, grid["plain"][j], grid["band"][j])))
                y = grid["y0"] + j * pitch
                for _ in range(40):
                    c = rng.randrange(grid["columns"])
                    d = rng.randrange(c, grid["columns"])
                    free = space.rect_free(grid["x0"] + c * pitch - margin, grid["x0"] + d * pitch + width + margin, round(y + width + margin, 9),
                                           round(y + pitch - margin, 9))
                    with self.subTest(phase=phase, row=j, run=(c, d)):
                        self.assertEqual(grid["band"][j][c] >= d, free)
                    checked += not free
        self.assertGreater(checked, 20)  # the hole blocks some

    def test_a_pointed_tip_gains_its_row(self) -> None:
        # The pointed plate at 3.9 mm (sparse at fill 0.7): on the lattice at phase (p / 2, p / 4) the field reaches the last
        # free row (10) with the filler over the common extent; with the whole lower run's band it stopped a row short.
        from surface import api as api_module

        data, point, _ = _Fits.case("pointed")
        mesh = read_stl(data)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, point)}]}
        _, chart = api_module.selection_chart(mesh, selection)
        pitch = 3.9
        options = fit.parse_options(dict(FIELD, pitch_mm=pitch))
        bases = fit.choose_bases({"side": 0}, api_module.boundary_sides(mesh, chart), mesh, chart)
        obstacles = fit.surface_obstacles(mesh, chart, options)
        space = fill.FreeSpace(chart, fit.BaseFrame(bases[0], 0.0), obstacles, 0.0, bases[0]["edges"])
        grid = fieldfit.lattice(space, pitch, fit._electrode(pitch, 0.7), 0.5, (1.95, 0.975))
        last = max(j for j in range(grid["rows"]) if any(end >= a for a, end in enumerate(grid["plain"][j])))
        exact = fieldfit.best_convex(grid["plain"], grid["up"], 0, grid["columns"] - 1, 0, grid["rows"] - 1, 0, None, grid["zones"], grid["band"])
        whole = fieldfit.best_convex(grid["plain"], grid["up"], 0, grid["columns"] - 1, 0, grid["rows"] - 1, 0, None, grid["zones"])
        self.assertEqual((last, exact[1][-1][0], whole[1][-1][0]), (10, 10, 9))
        self.assertGreater(exact[0], whole[0])
        # Every field the search keeps is realized as found (F's exact check, the fillers included: no peel).
        profile = fit.load_profile_cached("surface")
        queue = fieldfit.ordered(fieldfit.search_fields(chart, bases, options, profile, obstacles, []), False)
        for candidate in queue[:6]:
            with self.subTest(field=(candidate["rows"], candidate["columns"], candidate["taxels"])):
                proposal, peeled = fieldfit.realize_field(candidate, chart, obstacles, options, profile, None, {})
                self.assertIsNotNone(proposal)
                self.assertIsNone(peeled)
                self.assertEqual(proposal["metrics"]["taxels"], candidate["taxels"])



def _tip_candidate(value: int, top: int, x: float = 0.0, order: int = 0, symmetric: bool = False, full: bool = False, angle: float = 0.0,
                   pitch: float = 2.0, rows: int = 10, columns: int = 12) -> dict:
    """A synthetic field (section 26's tests) whose top row's far edge lies ``top`` nm from its exit."""

    width = 1.4
    cells = ((0, columns - 1),) * rows if full else ((1, columns - 2),) + ((0, columns - 1),) * (rows - 1)
    candidate = {"rows": rows, "columns": columns, "cells": cells, "taxels": value, "full": full, "value": value, "tip_mm": 10.0,
                 "pitch": pitch, "width": width, "angle_deg": angle, "order": order, "phase": (0.0, 0.0), "symmetric": symmetric,
                 "field_origin": (x, top / 1e6 - (rows - 1) * pitch - width)}
    candidate["rank"] = fieldfit.field_rank(candidate)
    return candidate


class _FakePass:
    """``fieldfit.tip_pass`` on synthetic candidates: the lead and the fields of ``extra`` of its exit and symmetry kind at or
    above the floor (the DP's threshold), the farthest reach of those; it records the floors asked."""

    def __init__(self, extra: list) -> None:
        self.extra, self.floors = extra, []

    def __call__(self, lead, options, floor, slack) -> dict:
        self.floors.append(floor)
        pool = [lead] + [candidate for candidate in self.extra if candidate["value"] >= floor and candidate["order"] == lead["order"]
                         and bool(candidate.get("symmetric")) == bool(lead.get("symmetric"))]
        return {"pool": pool, "farthest": max(fieldfit.tip_reach(candidate) for candidate in pool), "complete": True, "work": 7}


def _tip_options(**changes) -> dict:
    return dict(fit.parse_options(FIELD), **changes)


class TipFirstTests(unittest.TestCase):
    """The user's request of 2026-10-26 (P5-diagonal-bus.md section 26c): "the taxels stack from the fingertip as far as
    possible".  Shape fill, containment field: within 3 % of the most taxels on a group's exit (unturned, at its pitch,
    both symmetry kinds), the field reaching nearest the fingertip (within p / 8 of the farthest) takes the group's lead's
    slot, the lead next; exits, frames, pitches and symmetry kinds as before.  Since section 26's round 2 (26.15) the
    lead's zero-cost tie (:class:`TipTieTests`) and ``tip_first: false`` coverage first with those ties alone; since
    26.16 reach first (no tip-zone guard: a pointed tip may end in a single taxel); the order of coverage alone is the fit
    without the step (:func:`_coverage_alone`)."""

    def _queue(self, fake: _FakePass, queue: list, **options) -> list:
        from unittest import mock

        with mock.patch.object(fieldfit, "tip_pass", fake):
            return fieldfit.tip_first(queue, _tip_options(**options))

    def test_the_floor_and_the_share(self) -> None:
        # The floor: min(the lead, ceil(97 % of the most on its exit)), in integers: 97 % of 200 is 194 exactly (194 in the
        # pool, 193 not); of 201, 194.97, so 195.
        for most, floor in ((200, 194), (201, 195), (100, 97)):
            lead = _tip_candidate(most - 1, 40_000_000)
            fake = _FakePass([_tip_candidate(floor, 41_000_000, x=1.0), _tip_candidate(floor - 1, 42_000_000, x=2.0)])
            found = self._queue(fake, [lead, _tip_candidate(most, 39_000_000, x=3.0)])
            with self.subTest(most=most):
                self.assertEqual(fake.floors, [floor])
                self.assertEqual((found[0]["value"], found[0]["tip_lead"], found[1] is lead), (floor, True, True))
        # The lead itself below 97 % of the most (another readout, so another proposal): the floor is the lead's (it is
        # always in its pool).
        lead = _tip_candidate(90, 40_000_000, rows=11, columns=10)
        fake = _FakePass([])
        self._queue(fake, [_tip_candidate(100, 39_000_000, x=3.0, symmetric=True), lead], proposals=5)
        self.assertEqual(fake.floors, [97, 90])

    def test_the_share_is_measured_from_the_most(self) -> None:
        # An asymmetric lead at 97.5 % of the exit's most (a symmetric 1000): a field at 97.0 % of the most that reaches
        # farther leads; one at 96.9 % does not (97 % of the lead would let it in: the share is the most's).
        most = _tip_candidate(1000, 39_000_000, x=9.0, symmetric=True)
        for value, leads in ((970, True), (969, False)):
            lead = _tip_candidate(975, 40_000_000, rows=11, columns=10)
            fake = _FakePass([_tip_candidate(value, 41_000_000, x=1.0, rows=11, columns=10)])
            found = self._queue(fake, [most, lead])
            with self.subTest(value=value):
                self.assertEqual(fake.floors, [970, 970])
                self.assertEqual(found[1]["value"], value if leads else 975)

    def test_a_symmetric_lead_gives_up_at_most_3_percent_of_the_symmetric(self) -> None:
        # The user's decision of 2026-10-27 (section 26.17): a symmetric group's share is measured from the most of the
        # symmetric fields on its exit at its pitch, so symmetry itself is free and the tip costs at most 3 % of the best
        # symmetric field.  The symmetric 975 beside an asymmetric 1000 (2.5 % more): a symmetric 946 reaching farther
        # leads (97 % of 975), a 945 does not.  Round 3c measured it from the 1000 (floor 970): a symmetric field already
        # more than 3 % below could give up nothing and never moved toward the tip.
        most = _tip_candidate(1000, 39_000_000, x=9.0, rows=11, columns=10)
        for value, leads in ((946, True), (945, False)):
            lead = _tip_candidate(975, 40_000_000, symmetric=True)
            fake = _FakePass([_tip_candidate(value, 41_000_000, x=1.0, symmetric=True)])
            found = self._queue(fake, [lead, most])
            with self.subTest(value=value):
                self.assertEqual(fake.floors, [946, 970])
                self.assertEqual((found[0]["value"], bool(found[0].get("tip_lead"))), (value, True) if leads else (975, False))
                if leads:
                    self.assertEqual((found[0]["tip"]["most"], found[0]["tip"]["given"]), (975, 975 - value))

    def test_the_slack_is_an_eighth_of_a_pitch(self) -> None:
        # R the farthest reach in the pool (50 mm); at 2 mm the slack is 250 000 nm: a field reaching R - 250 000 is in the
        # lead (the most taxels of the lead first), one at R - 250 001 is not.
        lead = _tip_candidate(100, 49_000_000)
        far = _tip_candidate(97, 50_000_000, x=1.0)
        for reach, value in ((49_750_000, 99), (49_749_999, 97)):
            near = _tip_candidate(99, reach, x=2.0)
            found = self._queue(_FakePass([far, near]), [lead])
            with self.subTest(reach=reach):
                self.assertEqual((found[0]["value"], fieldfit.tip_reach(found[0])), (value, reach if value == 99 else 50_000_000))
                self.assertEqual(found[0]["tip"]["cut"], 50_000_000 - 250_000)
        # Fields alike in taxels and readout: the one reaching farther (a tie-break of the lead's rank, at no cost).
        twins = [_tip_candidate(99, 49_800_000, x=3.0), _tip_candidate(99, 49_900_000, x=4.0)]
        self.assertEqual(fieldfit.tip_reach(self._queue(_FakePass([far] + twins), [lead])[0]), 49_900_000)
        self.assertEqual(fieldfit.TIP_SLACK, 8)
        # The share: 3 % of the most.  (Section 26.16 removed shape rectangle's share and column guard and the tip-zone
        # guard: CAD mode has no rectangle rule, and a pointed tip may end in a single taxel.)
        self.assertEqual(fieldfit.TIP_SHARE, (97, 100))
        for gone in ("RECTANGLE_TIP_SHARE", "RECTANGLE_TIP_COLUMNS", "TIP_ZONE", "tip_zone_start", "tip_zone_cells", "tip_columns", "prefer_rectangle"):
            self.assertFalse(hasattr(fieldfit, gone), gone)

    def test_the_displaced_lead_follows(self) -> None:
        # The tip-first field takes the lead's slot, the lead directly after it, the rest in order; a copy of the tip-first
        # field further down goes; each group (exit, pitch, symmetry kind) of the first proposals has its own lead.
        lead, rest = _tip_candidate(100, 49_000_000), _tip_candidate(80, 40_000_000, x=6.0)
        other = _tip_candidate(99, 49_000_000, order=1, x=5.0, rows=11, columns=10)  # another exit (and readout: another proposal)
        tip, other_tip = _tip_candidate(98, 50_000_000, x=1.0), _tip_candidate(97, 50_000_000, order=1, x=2.0, rows=11, columns=10)
        copy_of_tip = dict(tip)
        found = self._queue(_FakePass([tip, other_tip]), [lead, rest, copy_of_tip, other])
        self.assertEqual([c["value"] for c in found], [98, 100, 80, 97, 99])  # the other exit's lead takes its own tip-first field
        self.assertTrue(found[0]["tip_lead"] and found[1] is lead and found[2] is rest and found[4] is other)
        self.assertEqual((found[3]["order"], found[3]["tip_lead"]), (1, True))
        self.assertEqual((found[0]["tip"]["displaced"], found[0]["tip"]["given"]), (id(lead), 2))
        self.assertFalse(any(c is copy_of_tip for c in found))
        # No field leads: the queue as it was.
        self.assertEqual(self._queue(_FakePass([]), [lead, rest]), [lead, rest])

    def test_turned_max_area_and_the_option_keep_the_order(self) -> None:
        def refuse(*args, **kwargs):
            raise AssertionError("no tip pass")

        from unittest import mock

        turned = _tip_candidate(100, 49_000_000, angle=20.0)
        queue = [turned, _tip_candidate(90, 30_000_000, x=1.0)]
        with mock.patch.object(fieldfit, "tip_pass", refuse):
            self.assertEqual(fieldfit.tip_first(queue[:1], _tip_options()), queue[:1])  # a turned lead
            self.assertEqual(fieldfit.tip_first(queue[1:], _tip_options(objective="max_area")), queue[1:])
            self.assertEqual(fieldfit.tip_first(queue[1:], _tip_options(), skip=(0,)), queue[1:])
        # tip_first false runs the pass at the lead's own value (its zero-cost ties alone, TipTieTests); 55ae8fe's order (the
        # option's meaning before section 26's round 2) is the fit without the step.
        fake = _FakePass([])
        self.assertEqual(self._queue(fake, queue[1:], tip_first=False), queue[1:])
        self.assertEqual(fake.floors, [90])
        self.assertTrue(fit.parse_options({})["tip_first"])
        self.assertFalse(fit.parse_options({"tip_first": False})["tip_first"])
        for bad in (0, 1, "true", None):
            with self.subTest(value=bad), self.assertRaises(SurfaceError):
                fit.parse_options({"tip_first": bad})

    def test_the_leads_are_the_proposals(self) -> None:
        # The leads are the first ``proposals`` fields the fit would propose (one per readout and kind, none dominated), not
        # the queue's first entries: screenshot 2's symmetric 6 x 6 lay behind fields its 7 x 6 dominates.
        big = _tip_candidate(38, 30_000_000, rows=7, columns=6)
        dominated = [_tip_candidate(37, 30_000_000, x=k, rows=7, columns=6) for k in range(1, 5)]
        symmetric = _tip_candidate(36, 27_000_000, x=9.0, symmetric=True, full=True, rows=6, columns=6)
        self.assertEqual(fieldfit.proposed([big] + dominated + [symmetric], 2), [big, symmetric])

    def test_the_passes_keep_the_group(self) -> None:
        # The real pass on the plates' leads: every pool field of the lead's exit, unturned, at its pitch, of its symmetry
        # kind, at least the floor, a full lead's full; the pool reaches at least as far as the lead.
        from surface import api as api_module

        for name in ("taper", "pointed", "rounded_2", "fin"):
            data, point, base = _Fits.case(name)
            mesh = read_stl(data)
            _, chart = api_module.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, point)}]})
            options = fit.parse_options(FIELD)
            bases = fit.choose_bases(base, api_module.boundary_sides(mesh, chart), mesh, chart)
            queue = fieldfit.ordered(fieldfit.search_fields(chart, bases, options, fit.load_profile_cached("surface"), fit.surface_obstacles(mesh, chart, options), []), len(bases) > 1)
            for lead in fieldfit.proposed(queue, 3):
                if lead["angle_deg"] != 0.0:
                    continue
                found = fieldfit.tip_pass(lead, options, lead["value"] - 5, int(round(lead["pitch"] * 1e6)) // 8)
                with self.subTest(face=name, lead=(lead["rows"], lead["columns"], lead["value"])):
                    self.assertTrue(found["complete"])
                    self.assertIs(found["pool"][0], lead)
                    for candidate in found["pool"]:
                        self.assertEqual((candidate["order"], candidate["angle_deg"], candidate["pitch"], bool(candidate["symmetric"])),
                                         (lead["order"], 0.0, lead["pitch"], bool(lead["symmetric"])))
                        self.assertGreaterEqual(candidate["value"], lead["value"] - 5)
                        self.assertTrue(candidate["full"] or not lead["full"])
                    self.assertGreaterEqual(found["farthest"], fieldfit.tip_reach(lead))

    def test_the_named_faces(self) -> None:
        # Section 26.9's numbers: the soft finger 708 (full, its tip gap under 1 mm), the crank 688 first (its tip gap 0.7
        # mm; 98.9 % of the 696, next), the long taper's tip-first 842 (64 x 18) before its 844, the rounded plates' full
        # 252 / 252 / 252 and r5's 248 (18 x 14 less its 4 corner cells) within the corner tolerance, the disk's 448 a row
        # nearer its far end (the 24 x 23 it displaced not proposed since section 26.17: the 24 x 24 is its tie and takes its
        # place), the holed plate's turned 396 (its symmetric 247 from section 26.17 to 26.19: the user's threshold of 20 %),
        # the fin's 572; every proposal DRC-clean, registered and mapped (FieldFitTests._check).
        cases = {"soft_finger": [(59, 12, 708)], "crank": [(34, 34, 688), (34, 34, 696)], "long_taper": [(64, 18, 842), (64, 17, 844)],
                 "rounded_2": [(18, 14, 252)], "rounded_3": [(18, 14, 252)], "rounded_4": [(18, 14, 252)], "rounded_5": [(18, 14, 248)],
                 "disk": [(24, 24, 448), (23, 24, 446)], "holed_plate": [(31, 32, 396)], "fin": [(59, 12, 572)]}
        for name, shapes in cases.items():
            if name in ASSET_CASES and not CRANK.exists():
                continue
            with self.subTest(face=name):
                proposals = FieldFitTests._check(self, name, FIELD)
                self.assertEqual(_shapes({"proposals": proposals})[:len(shapes)], shapes)
                first = proposals[0]
                self.assertEqual(sorted(first["metrics"]["tip"]), ["complete", "displaced", "farthest_mm", "lead", "reach_mm", "taxels_given"])
        soft = _Fits.get(self, "soft_finger", FIELD)[2]["proposals"][0]
        self.assertTrue(soft["metrics"]["symmetry"]["field"] and design_mask(soft["design"]) is None)
        crank = _Fits.get(self, "crank", FIELD)[2]["proposals"]
        self.assertEqual((crank[0]["metrics"]["tip"]["lead"], crank[0]["metrics"]["tip"]["displaced"], crank[0]["metrics"]["tip"]["taxels_given"]), (True, 2, 8))
        self.assertAlmostEqual(crank[0]["metrics"]["tip"]["reach_mm"] - crank[1]["metrics"]["tip"]["reach_mm"], 0.5, delta=1e-6)
        holed = _Fits.get(self, "holed_plate", FIELD)[2]["proposals"][0]
        self.assertEqual((holed["placement"]["base_side"], holed["metrics"]["angle_deg"], holed["metrics"]["tip"]["reach_mm"]), (0, -30.0, None))
        rounded = [_Fits.get(self, name, FIELD)[2]["proposals"][0] for name in ROUNDED]
        self.assertTrue(all(design_mask(p["design"]) is None for p in rounded[:3]))

    def test_the_tip_gaps(self) -> None:
        # The tip gap (the face's length along the exit's inward normal less the field's reach, measured on the map's
        # taxels by collect.py's rule): soft finger at most 1.0 mm, crank 0.7 mm, long taper 0.6 mm, disk 0.6 mm.
        for name, gap in (("soft_finger", 1.0), ("crank", 0.75), ("long_taper", 0.65), ("disk", 0.65)):
            if name in ASSET_CASES and not CRANK.exists():
                continue
            data, selection, result, _ = _Fits.get(self, name, FIELD)
            first = result["proposals"][0]
            frame = _frame(first["placement"])
            length = max(frame.to_base(p)[1] for p in _chart_outline(data, selection))
            frame0 = fit.BaseFrame({"from_uv": first["placement"]["base_from_uv"], "to_uv": first["placement"]["base_to_uv"],
                                    "inward_uv": first["placement"]["base_inward_uv"]}, 0.0)
            length = max(frame0.to_base(p)[1] for p in _chart_outline(data, selection))
            with self.subTest(face=name):
                self.assertLessEqual(length - first["metrics"]["tip"]["reach_mm"], gap)

    def test_the_exits_stay(self) -> None:
        # Proposal 1's exit, frame angle, pitch and symmetry kind with tip first equal those of coverage alone (the fit
        # without the step; exits chosen as before: the narrow tip, symmetry, section 23's caps), and with tip_first false
        # (its zero-cost ties, section 26's round 2) too, never with fewer taxels than coverage alone.
        names = ["isosceles", "equilateral", "disk", "long_taper", "holed_plate", "right_triangle", "cut_square", "fin", "taper", "slanted_edge",
                 "pointed", "rounded_3"] + (["crank_auto", "soft_finger"] if CRANK.exists() else [])
        for name in names:
            with self.subTest(face=name):
                now = _Fits.get(self, name, FIELD)[2]["proposals"][0]
                before = _coverage_alone(name)["proposals"][0]
                ties = _Fits.get(self, name, dict(FIELD, tip_first=False))[2]["proposals"][0]
                key = lambda p: (p["placement"]["base_side"], p["metrics"]["angle_deg"], p["metrics"]["pitch_x_mm"], p["metrics"]["symmetry"]["field"])
                self.assertEqual(key(now), key(before))
                self.assertEqual(key(ties), key(before))
                self.assertGreaterEqual(now["metrics"]["taxels"] * 100, before["metrics"]["taxels"] * 97)
                self.assertGreaterEqual(ties["metrics"]["taxels"], before["metrics"]["taxels"])
                if now["metrics"]["angle_deg"] == 0.0:
                    self.assertGreaterEqual(now["metrics"]["tip"]["reach_mm"], fieldfit.tip_reach(_candidate_of(before)) / 1e6 - 1e-9)
                    self.assertGreaterEqual(ties["metrics"]["tip"]["reach_mm"], fieldfit.tip_reach(_candidate_of(before)) / 1e6 - 1e-9)

    def test_the_tapered_plates(self) -> None:
        # The fin-like taper: the symmetric 351 (97.2 % of its 361) reaching 1.5 mm nearer the tip; the slanted edge: 267
        # before its 270; the pointed tip: its symmetric 205 a quarter pitch nearer the point, as many taxels (against
        # coverage alone, the fit without the step).  That 205 is its lead's zero-cost tie, so since section 26's round 2
        # tip_first false proposes it first too.
        for name, shapes in (("taper", [(29, 19, 351), (29, 19, 361)]), ("slanted_edge", [(24, 14, 267), (24, 14, 270)]),
                             ("pointed", [(23, 11, 205)])):
            with self.subTest(face=name):
                proposals = FieldFitTests._check(self, name, FIELD)
                self.assertEqual(_shapes({"proposals": proposals})[:len(shapes)], shapes)
                before = _coverage_alone(name)["proposals"][0]
                self.assertGreater(proposals[0]["metrics"]["tip"]["reach_mm"] * 1e6, fieldfit.tip_reach(_candidate_of(before)) + 1e5)
                self.assertTrue(proposals[0]["metrics"]["tip"]["lead"])
        ties = _Fits.get(self, "pointed", dict(FIELD, tip_first=False))[2]["proposals"][0]
        first = _Fits.get(self, "pointed", FIELD)[2]["proposals"][0]
        self.assertEqual((ties["build_id"], ties["metrics"]["tip"]["lead"]), (first["build_id"], False))

    def test_the_caps_window(self) -> None:
        # Section 23 with the tip: under max_rows 32 and 16 the fin keeps its mount end and its window (the rows down from
        # the far end), the tip-first field in the window (reaching 118.4 and 117.4 mm, within a crossing of the 119.36 mm
        # tip; 32 rows: the 250, its 256 next, nearer the exit), its tails within 200 mm.  16 rows: the 104, 1 mm nearer
        # the tip than the 106 (section 26.15's tip-zone guard took the 106's zero-cost tie at 117.4 mm instead; 26.16, reach
        # first, takes the 104 again: re-pinned to round 1's).  Since section 26.18 (a symmetric group's eighth row phases)
        # both 0.25 mm nearer the tip: 118.65 and 118.15 mm.
        for rows, reach, taxels in ((32, 118.6501, 250), (16, 118.1501, 104)):
            proposals = _Fits.get(self, "fin", dict(FIELD, max_rows=rows))[2]["proposals"]
            first = proposals[0]
            with self.subTest(rows=rows):
                self.assertEqual(first["placement"]["base_side"], _Fits.get(self, "fin", FIELD)[2]["proposals"][0]["placement"]["base_side"])
                self.assertEqual((first["metrics"]["rows"], first["metrics"]["taxels"], first["metrics"]["tip"]["lead"]), (rows, taxels, True))
                self.assertAlmostEqual(first["metrics"]["tip"]["reach_mm"], reach, delta=1e-6)
                self.assertLessEqual(max(first["design"]["tail"]["top_length_mm"], first["design"]["tail"]["bottom_length_mm"]), 200.0)
        proposals = _Fits.get(self, "fin", dict(FIELD, max_rows=32))[2]["proposals"]
        self.assertGreater(proposals[0]["metrics"]["tip"]["reach_mm"], proposals[1]["metrics"]["tip"]["reach_mm"])
        self.assertEqual(proposals[1]["metrics"]["taxels"], 256)

    def test_the_fin_at_a_coarse_pitch_reaches_its_tip(self) -> None:
        # From section 26.1's quick fix (its test kept where it still holds): at 3 mm the fin plate's 39 x 8 stays on the
        # 25.8 mm mount end and P's far edge passes 117.5 mm from it (the plate is 119.36 mm long; 117.35 before section
        # 26).  The tip-first 246 (99.2 % of the 248) reaches 118.85 mm, the 248 next at 117.73 mm since section 26's round 2:
        # the displaced 248's zero-cost tie, on the symmetric lattice's centred row phase (the quick fix's 248 there too),
        # 0.38 mm nearer the tip than the 248 the search kept (117.35 mm, not proposed: its tie took its readout).
        proposals = FieldFitTests._check(self, "fin", dict(FIELD, objective="fixed_pitch", pitch_mm=3.0))
        first = proposals[0]
        matrix = first["design"]["matrix"]
        far = first["placement"]["field_origin_base"][1] + (matrix["rows"] - 1) * matrix["pitch_y_mm"] + matrix["taxel_height_mm"]
        self.assertEqual((first["metrics"]["rows"], first["metrics"]["columns"]), (39, 8))
        self.assertAlmostEqual(math.dist(first["placement"]["base_from_uv"], first["placement"]["base_to_uv"]), 25.8, delta=0.01)
        self.assertGreater(far, 117.5)
        self.assertEqual(_shapes({"proposals": proposals})[:2], [(39, 8, 246), (39, 8, 248)])
        self.assertAlmostEqual(first["metrics"]["tip"]["reach_mm"], far, delta=1e-6)
        self.assertAlmostEqual(far - proposals[1]["metrics"]["tip"]["reach_mm"], 1.1201, delta=1e-6)
        self.assertEqual((proposals[1]["metrics"]["tip"]["lead"], proposals[1]["metrics"]["tip"]["taxels_given"]), (False, 0))

    def test_the_report(self) -> None:
        # metrics.tip on every proposal (lead or not); the bases record the passes' work and completion per exit.
        result = _Fits.get(self, "taper", FIELD, {"side": 0})[2]
        first, second = result["proposals"][:2]
        self.assertEqual(first["metrics"]["tip"]["lead"], True)
        self.assertEqual((first["metrics"]["tip"]["displaced"], first["metrics"]["tip"]["taxels_given"], first["metrics"]["tip"]["complete"]), (2, 10, True))
        self.assertAlmostEqual(first["metrics"]["tip"]["farthest_mm"], first["metrics"]["tip"]["reach_mm"], delta=0.25)
        self.assertEqual((second["metrics"]["tip"]["lead"], second["metrics"]["tip"]["farthest_mm"], second["metrics"]["tip"]["displaced"]), (False, None, None))
        base = next(b for b in result["bases"] if b["angle_deg"] == 0.0)
        self.assertGreater(base["tip_work"], 0)
        self.assertTrue(base["tip_complete"])
        # tip_first false (section 26's round 2): the step runs (the zero-cost ties), so every proposal has its metrics,
        # none a lead, and the exit's record its work (both absent before round 2).
        plain = _Fits.get(self, "taper", dict(FIELD, tip_first=False), {"side": 0})[2]
        self.assertEqual({p["metrics"]["tip"]["lead"] for p in plain["proposals"]}, {False})
        self.assertGreater(next(b for b in plain["bases"] if b["angle_deg"] == 0.0)["tip_work"], 0)

    def test_the_fingerprints_without_the_step_and_with_its_ties_alone(self) -> None:
        # Without the tip step (the option left out of the placement's record, and section 26.16's removed rectangle
        # preference put back as 55ae8fe recorded it, 0.0) the disk and the equilateral give 55ae8fe's digests, since
        # section 27 (diagonal-bus/10) those of section 27's own branch, main's fits with its tails (FINGERPRINTS_BEFORE:
        # sections 26a and 26b change nothing else on them; the isosceles triangle's symmetric base first since section
        # 26.17); tip_first false gives FINGERPRINTS_TIES (its zero-cost ties).
        # Python 3.9.6 and 3.12 alike (the suite runs on both).
        for name in ("disk", "equilateral", "isosceles"):
            with self.subTest(face=name):
                alone = copy.deepcopy(_coverage_alone(name))
                for proposal in alone["proposals"]:
                    proposal["placement"]["options"].pop("tip_first")
                    proposal["placement"]["options"]["rectangle_preference_pct"] = 0.0
                self.assertEqual(_fingerprint(alone), FINGERPRINTS_BEFORE[name])
                self.assertEqual(_fingerprint(_Fits.get(self, name, dict(FIELD, tip_first=False))[2]), FINGERPRINTS_TIES[name])

    def test_the_budget(self) -> None:
        # A tiny tip budget: each pass stops after its first lattice (deterministic), the bases say so, and the search's own
        # meter is untouched.
        data, selection, _, _ = _Fits.get(self, "taper", FIELD, {"side": 0})
        searches = []

        class Recorded(fieldfit._Search):
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                searches.append(self)

        saved = (fieldfit._Search, fieldfit.TIP_WORK_BUDGET)
        self.assertEqual(saved[1], 3_000_000)
        try:
            fieldfit._Search = Recorded
            full = fit.fit_route({"selection": selection, "base": {"side": 0}, "options": FIELD}, data)
            meters = [search.meter[0] for search in searches]
            fieldfit.TIP_WORK_BUDGET = 1
            searches.clear()
            small = [fit.fit_route({"selection": selection, "base": {"side": 0}, "options": FIELD}, data) for _ in range(2)]
            self.assertEqual([search.meter[0] for search in searches[:len(meters)]], meters)
        finally:
            fieldfit._Search, fieldfit.TIP_WORK_BUDGET = saved
        self.assertEqual(_fingerprint(small[0]), _fingerprint(small[1]))
        self.assertTrue(all(base.get("tip_complete") in (None, False) for base in small[0]["bases"]))
        self.assertFalse(next(b for b in small[0]["bases"] if b["angle_deg"] == 0.0)["tip_complete"])
        self.assertTrue(next(b for b in full["bases"] if b["angle_deg"] == 0.0)["tip_complete"])
        self.assertLess(next(b for b in small[0]["bases"] if b["angle_deg"] == 0.0)["tip_work"], next(b for b in full["bases"] if b["angle_deg"] == 0.0)["tip_work"])

    def test_the_per_row_dps_against_brute_force(self) -> None:
        # The row maxima (``per_row``) against the definition restricted to top row = L: best_convex on column and row
        # windows with zones and thresholds, best_symmetric with width caps (rectangles too), the full rectangles per top
        # row with zones and caps (rectangles_by_top, section 26a's cap order).
        rng = random.Random(2026)
        for trial in range(600):
            rows, columns = rng.randint(1, 4), rng.randint(1, 5)
            plain, up = _random_grid(rng, rows, columns, rng.choice((0.6, 0.85, 1.0)), rng.random() < 0.5)
            zones = None if rng.random() < 0.4 else [None if rng.random() < 0.3 else tuple([rng.random() < 0.7 for _ in range(columns)] for _ in range(4))
                                                     for _ in range(rows)]
            c0 = rng.randint(0, columns - 1)
            c1 = rng.randint(c0, columns - 1)
            r0 = rng.randint(0, rows - 1)
            r1 = rng.randint(r0, rows - 1)
            threshold = rng.choice((0, 0, rng.randint(1, 6)))
            clip = lambda grid: [[(min(end, c1) - c0 if end >= a + c0 else -1) for a, end in enumerate(row[c0:c1 + 1])] for row in grid[r0:r1 + 1]]  # noqa: E731
            clip_zones = None if zones is None else [None if flags is None else tuple(list(f[c0:c1 + 1]) for f in flags) for flags in zones[r0:r1 + 1]]
            per_row: list = []
            fieldfit.best_convex(plain, up, c0, c1, r0, r1, threshold, None, zones, None, per_row)
            with self.subTest(trial=trial):
                for top in range(r1 - r0 + 1):
                    want = _brute(clip(plain), clip(up), zones=clip_zones, top=top)
                    found = per_row[top] if top < len(per_row) else None
                    self.assertEqual(found[0] if found else 0, want if want > threshold else 0)
                    if found:
                        selection = [None] * (r1 - r0 + 1)
                        for j, a, b in found[1]:
                            selection[j - r0] = (a - c0, b - c0)
                        self.assertTrue(_is_convex(selection) and _free(selection, clip(plain), clip(up), clip_zones) and found[1][-1][0] == r0 + top)
                cap = rng.randint(1, columns)
                for rectangle in (False, True):
                    per_row = []
                    fieldfit.best_symmetric(plain, up, columns, r0, r1, cap, 0, zones, rectangle, None, per_row)
                    for top in range(r1 - r0 + 1):
                        found = per_row[top] if top < len(per_row) else None
                        self.assertEqual(found[0] if found else 0, _brute(plain[r0:r1 + 1], up[r0:r1 + 1], (99, cap), rectangle, zones[r0:r1 + 1] if zones else None,
                                                                           True, top=top))
                caps = (rng.randint(1, 4), rng.randint(1, 5))
                for top, found in enumerate(fieldfit.rectangles_by_top(plain, up, caps[0], caps[1], zones)):
                    self.assertEqual(found[0] if found else 0, _brute(plain, up, caps, rectangle=True, zones=zones, top=top))
                    if found:
                        count, height, width, row, a = found
                        self.assertEqual((row + height - 1, count), (top, height * width))


def _candidate_of(proposal: dict) -> dict:
    """What :func:`surface.fieldfit.tip_reach` reads of a proposal (an unturned field's origin, rows, pitch and width)."""

    matrix = proposal["design"]["matrix"]
    return {"field_origin": proposal["placement"]["field_origin_base"], "rows": matrix["rows"], "pitch": matrix["pitch_y_mm"], "width": matrix["taxel_height_mm"]}


def _lattice_field(runs: list, y0: float, x0: float = 0.0, length: float = 50.0) -> dict:
    """A synthetic unturned field made as the tip pass makes its fields (:func:`surface.fieldfit._make`): ``runs`` ``(a,
    b)`` per row from row 0 up, on a 2 mm lattice (1.4 mm taxels) whose row 0 lies ``y0`` mm from the exit and its column
    0 ``x0`` mm from the exit's start, on a 30 mm wide face reaching ``length`` mm from the exit."""

    import types

    region = types.SimpleNamespace(outline=[(0.0, 0.0), (30.0, 0.0), (30.0, length), (0.0, length)])
    grid = {"pitch": 2.0, "width": 1.4, "margin": 0.5, "x0": x0, "y0": y0, "phase": (x0, y0), "zones": None}
    frame = {"angle": 0.0, "side": {"index": 0}, "frame": None, "space": region, "order": 0, "symmetry": None}
    return fieldfit._make(fieldfit._PassSearch(None), grid, [(j, a, b) for j, (a, b) in enumerate(runs)], frame, "shaped")


def _queue_of(name: str, base=None, **options) -> tuple:
    """A face's fields in the fit's order before the tip step (:func:`surface.fieldfit.ordered` of its search) and the
    parsed options (FIELD with ``options``); ``base`` other than the case's."""

    from surface import api as api_module

    data, point, default = _Fits.case(name)
    mesh = read_stl(data)
    _, chart = api_module.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, point)}]})
    parsed = fit.parse_options(dict(FIELD, **options))
    bases = fit.choose_bases(default if base is None else base, api_module.boundary_sides(mesh, chart), mesh, chart)
    found = fieldfit.search_fields(chart, bases, parsed, fit.load_profile_cached("surface"), fit.surface_obstacles(mesh, chart, parsed), [])
    return fieldfit.ordered(found, len(bases) > 1), parsed


def _flags(queue: list) -> list:
    """A queue as ``(taxels, reach nm, tip_lead, tip_tie)`` per field."""

    return [(candidate["value"], fieldfit.tip_reach(candidate), bool(candidate.get("tip_lead")), bool(candidate.get("tip_tie"))) for candidate in queue]


class TipTieTests(unittest.TestCase):
    """Section 26's lead's zero-cost tie T0 (26.15, kept by 26.16): of the pool's fields of at least the lead's taxels,
    reaching within p / 8 of the farthest such field, the best by :func:`surface.fieldfit.lead_rank`; it follows the
    tip-first field T and goes before the lead; ``tip_first: false`` takes T0 alone.  Reach first (the user's decision of
    2026-10-26, 26.16): T is the pool's best reaching within p / 8 of the farthest, whatever it leaves bare, so at a
    pointed tip it may end in a single taxel (26.15's tip-zone guard is gone).  The synthetic fields lie on a 2 mm lattice
    (:func:`_lattice_field`); the lead G, 10 x 10 = 100, reaches 46.0 mm."""

    def setUp(self) -> None:
        full = [(0, 9)] * 10
        self.lead = _lattice_field(full, 26.6)  # 100, 46.0 mm
        self.tie = _lattice_field(full, 26.8)  # 100, 46.2 mm (a phase 0.2 mm higher)
        self.spire = _lattice_field([(0, 9)] * 7 + [(0, 8)] * 3 + [(4, 4)], 26.6)  # 98, 48.0 mm, its top row one cell
        self.passing = _lattice_field([(0, 9)] * 9 + [(0, 8)], 27.6)  # 99, 47.0 mm

    def _queue(self, extra: list, **options) -> list:
        from unittest import mock

        with mock.patch.object(fieldfit, "tip_pass", _FakePass(extra)):
            return fieldfit.tip_first([self.lead], _tip_options(**options))

    def test_the_fields(self) -> None:
        fields = (self.lead, self.tie, self.spire, self.passing)
        self.assertEqual([(field["value"], fieldfit.tip_reach(field)) for field in fields],
                         [(100, 46_000_000), (100, 46_200_000), (98, 48_000_000), (99, 47_000_000)])
        self.assertEqual(self.spire["spans"][-1][1:], (4, 4))

    def test_the_tie_follows_the_tip_first_field(self) -> None:
        # T (the 99, 47.0 mm) first, T0 (the lead's tie, 0.2 mm nearer the tip) next, flagged tip_tie, then the lead.
        self.assertEqual(_flags(self._queue([self.tie, self.passing])),
                         [(99, 47_000_000, True, False), (100, 46_200_000, False, True), (100, 46_000_000, False, False)])
        # T and T0 the same field: once, as the tip-first field (it gives up nothing).
        self.assertEqual(_flags(self._queue([self.tie])), [(100, 46_200_000, True, False), (100, 46_000_000, False, False)])
        # Nothing reaches farther: the queue as it was.
        self.assertEqual(self._queue([]), [self.lead])

    def test_the_tie_takes_the_leads_place(self) -> None:
        # Section 26.17 (round 3c's review): T0 takes the lead's place (``place``: the lead it stands for and its taxels);
        # the lead follows only to be proposed should no field in its place be proposed with at least its taxels
        # (fit_chart_field).  When T is T0, T takes it; T alone (no tie) leaves the lead its own place.
        self.assertEqual([c.get("place") for c in self._queue([self.tie, self.passing])], [None, (id(self.lead), 100), None])
        self.assertEqual([c.get("place") for c in self._queue([self.tie])], [(id(self.lead), 100), None])
        self.assertEqual([c.get("place") for c in self._queue([self.passing])], [None, None])
        found = self._queue([self.tie, self.passing], tip_first=False)
        self.assertEqual([(bool(c.get("tip_tie")), c.get("place")) for c in found], [(True, (id(self.lead), 100)), (False, None)])

    def test_the_taxels_given_count_from_the_groups_most(self) -> None:
        # taxels_given counts from the most of the lead and its pass: the lead, or a larger field of the pass's own.  A 101
        # the pass finds reaching 47.0 mm leads and gives up nothing (round 3c counted from the lead's 100: -1); it is the
        # lead's tie too, so it takes the lead's place.  The 99 reaching as far gives up 1 of the 100.
        bigger = _lattice_field([(0, 9)] * 10 + [(0, 0)], 25.6)
        first = self._queue([bigger, self.tie])[0]
        self.assertEqual((first["value"], fieldfit.tip_reach(first), first["tip"]["most"], first["tip"]["given"], first["place"]),
                         (101, 47_000_000, 101, 0, (id(self.lead), 100)))
        first = self._queue([self.passing, self.tie])[0]
        self.assertEqual((first["value"], first["tip"]["most"], first["tip"]["given"]), (99, 100, 1))

    def test_the_taxels_given_are_what_the_tip_gave_up(self) -> None:
        # Section 26.18 (round 4's review): taxels_given counts from the most of the lead and its pass's fields (what the
        # tip-first field could have held in its place), not from the share's M (the most on the exit at the pitch, of
        # both kinds for an asymmetric group), which may be another readout's never proposed there.  An asymmetric 975
        # beside its exit's symmetric 1000: its tip-first 970 gives up 5 (round 4: 30).
        from unittest import mock

        lead = _tip_candidate(975, 40_000_000, rows=11, columns=10)
        fake = _FakePass([_tip_candidate(970, 41_000_000, x=1.0, rows=11, columns=10)])
        with mock.patch.object(fieldfit, "tip_pass", fake):
            found = fieldfit.tip_first([_tip_candidate(1000, 39_000_000, x=9.0, symmetric=True), lead], _tip_options())
        self.assertEqual(fake.floors, [970, 970])
        self.assertEqual((found[1]["value"], found[1]["tip"]["floor"], found[1]["tip"]["most"], found[1]["tip"]["given"]), (970, 970, 975, 5))
        # The real faces: the right triangle under 12 rows, its hypotenuse's asymmetric tip-first 7 x 12 = 84 as many
        # taxels as the 6 x 14 = 84 it displaces (round 4: 72, from the symmetric 156); the crank with base auto, its side
        # 5's tip-first 17 x 22 = 374, 13 more than the 19 x 19 = 361 it displaces (round 4: 325, from a 699 on that exit
        # never proposed there).
        cases = [("right_triangle", dict(FIELD, max_rows=12), 1, (7, 12, 84))]
        if CRANK.exists():
            cases.append(("crank_auto", FIELD, 4, (17, 22, 374)))
        for name, options, k, shape in cases:
            with self.subTest(face=name):
                proposal = _Fits.get(self, name, options)[2]["proposals"][k]
                tip = proposal["metrics"]["tip"]
                self.assertEqual((_shapes({"proposals": [proposal]})[0], tip["lead"], tip["taxels_given"]), (shape, True, 0))

    def test_a_tip_first_tie_peeled_under_the_lead_leaves_it_its_place(self) -> None:
        # A tip-first field that is the lead's tie itself (T is T0) takes the lead's place only with at least its taxels:
        # peeled under them (its peel still leading, tip_peel_holds) the peel is proposed as the tip-first field and the
        # lead right after it, in its own place.  The disk's tip-first 24 x 24 = 448 (its lead's, the 24 x 23 = 448's, tie)
        # peeled to 446: the peel first, the 24 x 23 second, as coverage alone proposes it (the peel neither dropped as a
        # tie's would be, nor taking the lead's place).
        from unittest import mock

        data, selection, _, _ = _Fits.get(self, "disk", FIELD)
        realize = fieldfit.realize_field
        peels = []

        def peeling(candidate, *args):
            if candidate.get("tip_lead") and "place" in candidate and not peels:
                peels.append(fieldfit.peel_field(candidate, (candidate["field_origin"][0], -1e3)))
                return None, peels[-1]
            return realize(candidate, *args)

        with mock.patch.object(fieldfit, "realize_field", peeling):
            proposals = fit.fit_route({"selection": selection, "base": "auto", "options": FIELD}, data)["proposals"]
        alone = _coverage_alone("disk")["proposals"]
        self.assertEqual((peels[0]["value"], peels[0]["place"][1]), (446, 448))
        self.assertEqual([(_shapes({"proposals": [p]})[0], p["metrics"]["tip"]["lead"]) for p in proposals[:2]], [((24, 24, 446), True), ((24, 23, 448), False)])
        self.assertEqual(proposals[1]["build_id"], alone[0]["build_id"])
        self.assertEqual(proposals[0]["metrics"]["tip"]["displaced"], 2)

    def test_a_tie_peeled_to_the_leads_taxels_keeps_its_place(self) -> None:
        # A tie gives up no taxel: its peel keeps the lead's place with at least the lead's taxels (equal ones too), and
        # gives it back under them (test_the_lead_takes_its_place_back).  tri_a under 12 rows with tip_first false: T0,
        # the 8 x 6 = 48, peeled cell by cell from its bottom row down to 42, the lead's (6 x 7 = 42) taxels: the 7 x 6 = 42
        # takes the lead's slot and the lead is not proposed.
        from unittest import mock

        options = dict(FIELD, max_rows=12, tip_first=False)
        data, selection, _, _ = _Fits.get(self, "tri_a", options)
        realize = fieldfit.realize_field
        peels = []

        def peeling(candidate, *args):
            if candidate.get("tip_tie") and candidate["value"] > candidate["place"][1]:
                peels.append(fieldfit.peel_field(candidate, (candidate["field_origin"][0], -1e3)))
                return None, peels[-1]
            return realize(candidate, *args)

        with mock.patch.object(fieldfit, "realize_field", peeling):
            proposals = fit.fit_route({"selection": selection, "base": "auto", "options": options}, data)["proposals"]
        self.assertEqual([peel["value"] for peel in peels], [47, 46, 45, 44, 43, 42])
        self.assertEqual(_shapes({"proposals": proposals})[1], (7, 6, 42))
        self.assertEqual(_shapes(_coverage_alone("tri_a", dict(FIELD, max_rows=12)))[1], (6, 7, 42))
        self.assertNotIn((6, 7, 42), _shapes({"proposals": proposals}))

    def test_the_tie_reaches_within_an_eighth_of_a_pitch_of_the_farthest_tie(self) -> None:
        # T0 is the best by lead_rank of the lead's ties reaching within p / 8 of the farthest of them, not the farthest one
        # alone (round 3c's review): on the taper at 3 mm with the 32x16 reader (fill 0.55) the symmetric group's T0 is the
        # denser 20 x 12 = 162 reaching 59.15 mm, 0.175 mm short of the 20 x 13 = 162 reaching farthest (lead_rank: fewer
        # readout positions first), with tip_first true and false alike.
        options = dict(FIELD, pitch_mm=3.0, reader="32x16", fill=0.55)
        for tip_first in (True, False):
            with self.subTest(tip_first=tip_first):
                metrics = _Fits.get(self, "taper", dict(options, tip_first=tip_first))[2]["proposals"][0]["metrics"]
                self.assertEqual((metrics["rows"], metrics["columns"], metrics["taxels"], metrics["symmetry"]["field"], metrics["tip"]["lead"]),
                                 (20, 12, 162, True, False))
                self.assertAlmostEqual(metrics["tip"]["reach_mm"], 59.1501, delta=1e-6)

    def test_a_tie_may_hold_more_taxels(self) -> None:
        # T0 is of the pool's fields with at least the lead's taxels, not exactly as many (round 3c's review): with
        # tip_first false tri_a under 12 rows proposes the 8 x 6 = 48 in place of coverage alone's 6 x 7 = 42 (a tie with 6
        # more taxels), the crank with base auto its side 5's 17 x 22 = 374 in place of the 19 x 19 = 361.
        cases = [("tri_a", dict(FIELD, max_rows=12), 1, (8, 6, 48), (6, 7, 42))]
        if CRANK.exists():
            cases.append(("crank_auto", FIELD, 3, (17, 22, 374), (19, 19, 361)))
        for name, options, k, tie, lead in cases:
            with self.subTest(face=name):
                self.assertEqual(_shapes(_Fits.get(self, name, dict(options, tip_first=False))[2])[k], tie)
                self.assertEqual(_shapes(_coverage_alone(name, options))[k], lead)

    def test_tip_first_false_takes_the_tie_alone(self) -> None:
        # tip_first false: the pass at the lead's own value (the floor 100), its zero-cost tie alone before it, never a
        # field with fewer taxels (the 99 and the 98, which tip_first true weighs: the 98 leads there, reaching farthest).
        from unittest import mock

        fake = _FakePass([self.tie, self.passing, self.spire])
        with mock.patch.object(fieldfit, "tip_pass", fake):
            found = fieldfit.tip_first([self.lead], _tip_options(tip_first=False))
        self.assertEqual(fake.floors, [100])
        self.assertEqual(_flags(found), [(100, 46_200_000, False, True), (100, 46_000_000, False, False)])
        self.assertEqual(_flags(self._queue([self.tie, self.passing, self.spire]))[0], (98, 48_000_000, True, False))

    def test_a_pointed_tip_may_end_in_a_single_taxel(self) -> None:
        # The user (2026-10-26): "if the gripper is very pointed, it can stick out just one taxel".  The spire (98, 2 % under
        # the lead, its top row one cell at 48.0 mm) reaches farthest: it leads, before the 99 reaching 47.0 mm (26.15's
        # tip-zone guard took the 99, which covers more of the face's outer 30 %), the lead next.
        self.assertEqual(_flags(self._queue([self.spire, self.passing])),
                         [(98, 48_000_000, True, False), (100, 46_000_000, False, False)])
        self.assertEqual(_flags(self._queue([self.spire])), [(98, 48_000_000, True, False), (100, 46_000_000, False, False)])
        # With the lead's tie in the pool: the spire, the tie, the lead.
        self.assertEqual(_flags(self._queue([self.spire, self.tie])),
                         [(98, 48_000_000, True, False), (100, 46_200_000, False, True), (100, 46_000_000, False, False)])
        first = self._queue([self.spire, self.passing])[0]
        self.assertEqual((first["spans"][-1][1:], first["tip"]["given"]), ((4, 4), 2))

    def test_a_real_pointed_tip(self) -> None:
        # The pointed plate (24 mm wide, its sides straight to 30 mm, a point at 48 mm): the first proposal, the symmetric
        # tip-first 23 x 11 = 205, ends at the point in a single taxel (ROW_01 one cell, 46.4 mm from the exit), 0.5 mm
        # nearer the tip than the asymmetric 208 next; on the plate's long side the tip-first 17 x 21 = 202 (97.6 % of the
        # 207 it displaces: within 3 %) reaches 1 mm farther than it, ROW_01 one cell too.  Section 26.15's tip-zone guard
        # could turn such a field down; reach first (26.16) takes it.
        proposals = _Fits.get(self, "pointed", FIELD)[2]["proposals"]
        self.assertEqual([(p["metrics"]["rows"], p["metrics"]["columns"], p["metrics"]["taxels"], p["metrics"]["tip"]["lead"]) for p in proposals],
                         [(23, 11, 205, True), (23, 11, 208, False), (22, 11, 205, False), (17, 21, 202, True), (17, 21, 207, False)])
        for tip, other in ((proposals[0], proposals[1]), (proposals[3], proposals[4])):
            with self.subTest(taxels=tip["metrics"]["taxels"]):
                first, last = design_mask(tip["design"])[0]
                self.assertEqual(last, first)  # ROW_01, at the tip: one cell
                self.assertGreater(tip["metrics"]["tip"]["reach_mm"], other["metrics"]["tip"]["reach_mm"])
        side = proposals[3]["metrics"]["tip"]
        self.assertEqual((side["displaced"], side["taxels_given"]), (5, 5))
        self.assertLessEqual(side["taxels_given"] * 100, 207 * 3)
        self.assertAlmostEqual(side["reach_mm"] - proposals[4]["metrics"]["tip"]["reach_mm"], 1.0, delta=1e-6)

    def test_the_reach_before_the_corners(self) -> None:
        # lead_rank: of fields alike in taxels, pitch, turn, fill and readout positions the farther first, before the
        # corner tolerance's count: the 99 reaching 49.9 mm with one corner on the tolerance leads, not the 99 at 49.8 mm
        # without (both within p / 8 of the 97 at 50 mm).
        cornered = dict(_tip_candidate(99, 49_900_000, x=2.0), corners=1)
        cornered["rank"] = fieldfit.field_rank(cornered)
        from unittest import mock

        fake = _FakePass([_tip_candidate(97, 50_000_000, x=1.0), cornered, _tip_candidate(99, 49_800_000, x=3.0)])
        with mock.patch.object(fieldfit, "tip_pass", fake):
            found = fieldfit.tip_first([_tip_candidate(100, 49_000_000)], _tip_options())
        self.assertEqual((found[0]["value"], fieldfit.tip_reach(found[0]), found[0].get("corners", 0)), (99, 49_900_000, 1))

    def test_the_long_taper(self) -> None:
        # A named face: the tip-first 842 (64 x 18) first, then the displaced 844's zero-cost tie, 0.5 mm nearer the tip
        # than the 844 the search kept (coverage alone's first, its tip gap 2.1 -> 1.6 mm), then the 846's tie likewise;
        # the 844 and the 846 themselves are not proposed (their ties took their readouts).
        proposals = _Fits.get(self, "long_taper", FIELD)[2]["proposals"]
        alone = _coverage_alone("long_taper")["proposals"]
        self.assertEqual(_shapes({"proposals": proposals})[:3], [(64, 18, 842), (64, 17, 844), (64, 18, 846)])
        self.assertEqual(_shapes({"proposals": alone})[:2], [(64, 17, 844), (64, 18, 846)])
        self.assertEqual([p["metrics"]["tip"]["lead"] for p in proposals[:3]], [True, False, False])
        for k in (0, 1):
            with self.subTest(taxels=alone[k]["metrics"]["taxels"]):
                gain = fieldfit.tip_reach(_candidate_of(proposals[k + 1])) - fieldfit.tip_reach(_candidate_of(alone[k]))
                self.assertEqual(gain, 500_000)

    def test_tip_first_false_keeps_coverage_alones_proposals(self) -> None:
        # Round 3c's review (section 26.17): T0 took the lead's proposal on the lead's readout only, so a tie of another
        # readout (or with more taxels) was proposed beside the lead and pushed another exit's field out of the five.  Now
        # T0 takes the lead's place: with tip_first false the proposals have coverage alone's length and its exits,
        # frames, pitches and symmetry kinds in its order, never fewer taxels, a lead's slot reaching at most p / 8 less
        # (its tie); with tip_first true they are these with the tip-first fields inserted (a T that is T0 itself in
        # T0's slot).  Round 3c lost the right triangle's symmetric 16 x 32 = 272 on its hypotenuse (2.5 mm, 16 rows),
        # tri_a's 12 x 17 = 113 turned -10 degrees (12 rows) and the crank's 16 x 26 = 344 on its side 5 (2.5 mm, 16 rows).
        # Since section 26.18 every exit of the fit without the caps is searched on its own under them, in that fit's exit
        # order: the right triangle's hypotenuse first, then a leg, the crank's side 4, then its side 7 (side 5's fields
        # after the five); a lead's tie beside it would push out the leg's 10 x 16 = 160 turned -30 degrees and side 7's
        # 10 x 20 = 200 turned -30 degrees.
        cases = [("right_triangle", dict(FIELD, pitch_mm=2.5, max_rows=16), (0, -30.0, 10, 16, 160)),
                 ("tri_a", dict(FIELD, max_rows=12), (0, -10.0, 12, 17, 113))]
        if CRANK.exists():
            cases.append(("crank_auto", dict(FIELD, pitch_mm=2.5, max_rows=16), (7, -30.0, 10, 20, 200)))

        def key(proposal: dict) -> tuple:
            placement, metrics = proposal["placement"], proposal["metrics"]
            return (placement["base_side"], placement["base_angle_deg"], metrics["pitch_x_mm"], metrics["symmetry"]["field"])

        for name, options, kept in cases:
            with self.subTest(face=name):
                false = _Fits.get(self, name, dict(options, tip_first=False))[2]["proposals"]
                alone = _coverage_alone(name, options)["proposals"]
                self.assertEqual([key(p) for p in false], [key(p) for p in alone])
                for ours, theirs in zip(false, alone):
                    self.assertGreaterEqual(ours["metrics"]["taxels"], theirs["metrics"]["taxels"])
                    if ours["build_id"] != theirs["build_id"]:
                        self.assertGreaterEqual(fieldfit.tip_reach(_candidate_of(ours)) + 250_000, fieldfit.tip_reach(_candidate_of(theirs)))
                self.assertIn(kept, [key(p)[:2] + (p["metrics"]["rows"], p["metrics"]["columns"], p["metrics"]["taxels"]) for p in false])
                true = _Fits.get(self, name, options)[2]["proposals"]
                tips = [p["metrics"] for p in true if p["metrics"]["tip"]["lead"]]
                rest = [p["build_id"] for p in true if not p["metrics"]["tip"]["lead"]]
                # Less the fields a tip-first field dominates (T0 when T is T0; a field of T's readout and taxels it reaches past).
                kept = [p["build_id"] for p in false if not fill.dominated(p["metrics"]["rows"], p["metrics"]["columns"], p["metrics"]["taxels"],
                                                                           [{"metrics": tip} for tip in tips])]
                self.assertEqual(rest, kept[:len(rest)])

    def test_the_displaced_fields_place(self) -> None:
        # metrics.tip.displaced: the rank of the proposal in the displaced field's place.  The long taper's tip-first 842
        # displaced the 844, whose tie took its place (proposal 2; round 3c: None, the 844 itself not proposed); the disk's
        # tip-first 24 x 24 is its lead's tie itself (as many taxels, a row nearer the far end): it takes the 24 x 23's
        # place, which is not proposed any more (round 3c proposed it second).
        long_taper = _Fits.get(self, "long_taper", FIELD)[2]["proposals"]
        self.assertEqual((long_taper[0]["metrics"]["tip"]["lead"], long_taper[0]["metrics"]["tip"]["displaced"]), (True, 2))
        disk = _Fits.get(self, "disk", FIELD)[2]["proposals"]
        tip = disk[0]["metrics"]["tip"]
        self.assertEqual((_shapes({"proposals": disk[:1]}), tip["lead"], tip["displaced"], tip["taxels_given"]), ([(24, 24, 448)], True, 1, 0))
        self.assertNotIn((24, 23, 448), _shapes({"proposals": disk}))

    def test_the_lead_takes_its_place_back(self) -> None:
        # A tie that is not built, or whose peel falls under the lead's taxels, gives the lead its place back (a tie gives
        # up no taxel): the long taper's 844 proposed after the tip-first 842 when its tie is peeled, the peel not.
        from unittest import mock

        data, selection, _, _ = _Fits.get(self, "long_taper", FIELD)
        realize = fieldfit.realize_field
        peels, built = [], []

        def peeling(candidate, *args):
            built.append(candidate)
            if candidate.get("tip_tie") and not peels:
                peels.append(fieldfit.peel_field(candidate, (candidate["field_origin"][0], 1e3)))
                return None, peels[-1]
            return realize(candidate, *args)

        with mock.patch.object(fieldfit, "realize_field", peeling):
            result = fit.fit_route({"selection": selection, "base": "auto", "options": FIELD}, data)
        alone = _coverage_alone("long_taper")["proposals"]
        self.assertLess(peels[0]["value"], 844)
        self.assertEqual([p["build_id"] for p in result["proposals"][1:2]], [alone[0]["build_id"]])
        self.assertFalse(any(candidate is peels[0] for candidate in built))
        self.assertEqual(result["proposals"][0]["metrics"]["tip"]["displaced"], 2)

    def test_tip_first_false_never_gives_up_a_taxel(self) -> None:
        # The real queues with tip_first false: no tip-first field; each zero-cost tie directly before the group lead it
        # stands for, on its exit, frame, pitch and symmetry kind, with at least its taxels and its reach less p / 8;
        # every other field where it was.
        firsts = {}
        for name in ("taper", "pointed", "fin", "disk"):
            queue, options = _queue_of(name, tip_first=False)
            found = fieldfit.tip_first(queue, options)
            firsts[name] = found[0]
            leads = [candidate for candidate in fieldfit.proposed(queue, options["proposals"]) if candidate["angle_deg"] == 0.0]
            ties = [k for k, candidate in enumerate(found) if candidate.get("tip_tie")]
            with self.subTest(face=name):
                self.assertFalse(any(candidate.get("tip_lead") for candidate in found))
                for k in ties:
                    tie, lead = found[k], found[k + 1]
                    self.assertTrue(any(lead is candidate for candidate in leads))
                    group = lambda c: (c["order"], c["angle_deg"], c["pitch"], bool(c["symmetric"]))  # noqa: E731
                    self.assertEqual(group(tie), group(lead))
                    self.assertGreaterEqual(tie["value"], lead["value"])
                    self.assertGreaterEqual(fieldfit.tip_reach(tie), fieldfit.tip_reach(lead) - int(round(lead["pitch"] * 1e6)) // 8)
                keys = {fieldfit._field_key(found[k]) for k in ties}
                self.assertEqual([c for c in found if not c.get("tip_tie")], [c for c in queue if fieldfit._field_key(c) not in keys])
        # The disk's first: the 24 x 24 = 448, its lead's (24 x 23) tie a row nearer its far end.
        disk = firsts["disk"]
        self.assertEqual(((disk["rows"], disk["columns"], disk["value"]), disk.get("tip_tie")), ((24, 24, 448), True))


class TipPassTests(unittest.TestCase):
    """Section 26's tip pass and fallback, pinned where nothing else did (round 2's review): the centred phase among the
    lattices it visits, the tails' reach it holds, and the slot a peeled tip-first field gives back."""

    def test_the_centred_phase(self) -> None:
        # The pass visits the centred phase as the search does: on the triangle tri_a at 3.9 mm its 9 x 11 = 55 on the
        # centred phase leads, 0.5849 mm nearer the tip than the quarter phases' 55 (no field would lead without it).  Since
        # section 26.17 its group follows the symmetric exit's group (the symmetric 10 x 9 = 50 first).
        queue, options = _queue_of("tri_a", pitch_mm=3.9)
        found = fieldfit.tip_first(queue, options)
        at = next(k for k, candidate in enumerate(found) if candidate.get("tip_lead") and not candidate["symmetric"])
        first, lead = found[at:at + 2]
        middle = fieldfit.centred_phase(first["region"], first["pitch"], first["width"], first["margin"])
        self.assertEqual(((first["rows"], first["columns"], first["value"]), first.get("tip_lead"), tuple(first["phase"])), ((9, 11, 55), True, tuple(middle)))
        self.assertEqual(((lead["rows"], lead["columns"], lead["value"]), fieldfit.tip_reach(first) - fieldfit.tip_reach(lead)), ((9, 11, 55), 584_900))

    def test_a_lattice_within_the_slack_runs_at_the_floor(self) -> None:
        # The pass runs a lattice at the floor when its farthest free row reaches within the slack of the farthest reach R
        # so far, at the lead's value (ties only) when it does not: on the disk under 16 rows the tip-first 16 x 23 = 318
        # reaches 44.13 mm, 0.05 mm short of R (a 16 x 24 = 318 at 44.18 mm, within p / 16, a symmetric group's slack),
        # and leads with a denser readout (as many taxels, fewer positions); a lattice short of R run at the lead's value
        # would miss it, and the 16 x 24 would lead.  (Round 4 pinned this on the equilateral's second exit, its 342 0.22
        # mm short of a 338; since section 26.18 that exit's tip-first field is a 349 of the first exit's readout.)
        first = _Fits.get(self, "disk", dict(FIELD, max_rows=16))[2]["proposals"][0]["metrics"]
        self.assertEqual((first["rows"], first["columns"], first["taxels"], first["tip"]["lead"]), (16, 23, 318, True))
        self.assertAlmostEqual(first["tip"]["reach_mm"], 44.128902, delta=1e-6)
        self.assertAlmostEqual(first["tip"]["farthest_mm"], 44.178802, delta=1e-6)

    def test_a_symmetric_lead_takes_the_eighth_row_phases(self) -> None:
        # Section 26.18 (round 4's review): a symmetric field's columns are fixed by its exit's axis, so its row phase alone
        # moves it toward the tip.  On the isosceles triangle's base (2 mm) the quarter phases' farthest symmetric field
        # within the share (97 % of the 328: 319) was a 322 reaching 56.90 mm, and the 328 at 56.70 mm took the lead within
        # p / 8 of it: 3.3 mm short of the 60 mm apex (1.65 pitches, severe; the leg's 341 first before section 26.17, 1.75
        # mm).  At 5 p / 8 the 322 reaches 57.15 mm (2.85 mm short), at 3 p / 4 a 318 reaches 57.40 mm, under the share.
        # The pass now takes the row phases k p / 8: the 322 at 57.15 mm leads, the 328 (the lead's tie) next.
        queue, options = _queue_of("isosceles")
        lead = next(c for c in fieldfit.proposed(queue, options["proposals"]) if c.get("symmetric"))
        rows = sorted({grid["phase"][1] for grid in fieldfit._tip_lattices(lead, options)})
        middle = fieldfit.centred_phase(lead["region"], lead["pitch"], lead["width"], lead["margin"])[1]
        self.assertEqual([phase for phase in rows if phase != middle], [round(k * 0.25, 6) for k in range(8)])
        self.assertEqual(fieldfit.TIP_ROW_PHASES, 8)
        proposals = _Fits.get(self, "isosceles", FIELD)[2]["proposals"]
        first, second = (p["metrics"] for p in proposals[:2])
        self.assertEqual([(m["rows"], m["columns"], m["taxels"], m["symmetry"]["field"], m["tip"]["lead"]) for m in (first, second)],
                         [(28, 23, 322, True, True), (28, 23, 328, True, False)])
        self.assertAlmostEqual(first["tip"]["reach_mm"], 57.1501, delta=1e-6)
        self.assertAlmostEqual(first["tip"]["farthest_mm"], 57.1501, delta=1e-6)
        self.assertEqual((first["tip"]["displaced"], first["tip"]["taxels_given"]), (2, 6))
        self.assertAlmostEqual(second["tip"]["reach_mm"], 56.7, delta=1e-6)
        # Under 12 rows the share, not the search: section 23's window at the apex holds at most 58 symmetric taxels (12
        # rows of a 45-degree point) against the floor 74 (97 % of the 76 a lower window holds), so the 74 reaching 53.9
        # mm leads at any row phase.
        capped = _Fits.get(self, "isosceles", dict(FIELD, max_rows=12))[2]["proposals"][0]["metrics"]
        self.assertEqual((capped["taxels"], capped["tip"]["lead"]), (74, True))
        self.assertAlmostEqual(capped["tip"]["reach_mm"], 53.9001, delta=1e-6)

    def test_a_symmetric_groups_slack_is_half_its_row_phase_step(self) -> None:
        # A symmetric group's slack is p / 16 (TIP_SYMMETRIC_SLACK), half its row phases' step as p / 8 is half the
        # quarter phases': a field an eighth phase short of the farthest does not count as reaching it.  The taper's
        # symmetric tip-first 351 reaches 59.4 mm; the 353 an eighth phase short (59.15 mm) would lead with p / 8.
        self.assertEqual(fieldfit.TIP_SYMMETRIC_SLACK, 16)
        first = _Fits.get(self, "taper", FIELD)[2]["proposals"][0]["metrics"]
        self.assertEqual((first["taxels"], first["symmetry"]["field"], first["tip"]["lead"]), (351, True, True))
        self.assertAlmostEqual(first["tip"]["reach_mm"], 59.4001, delta=1e-6)

    def test_the_pass_holds_the_tails_reach(self) -> None:
        # A lead whose tails held the search's rows nearer the exit (section 23's reach_limit, two rows below its own top
        # here): no field of the pass, on any lattice, reaches beyond that row (far).
        queue, options = _queue_of("taper", base={"side": 0})
        for lead in fieldfit.proposed(queue, 2):
            width = int(round(lead["width"] * 1e6))
            limit = (fieldfit.tip_reach(lead) - width) / 1e6 - 2 * lead["pitch"]
            held = dict(lead, reach_limit=limit)
            bound = int(round(limit * 1e6)) + width + 1
            with self.subTest(lead=(lead["rows"], lead["columns"], lead["value"])):
                found = fieldfit.tip_pass(held, options, 1, int(round(lead["pitch"] * 1e6)) // 8)
                self.assertEqual([fieldfit.tip_reach(c) for c in found["pool"] if c is not held and fieldfit.tip_reach(c) > bound], [])

    def test_a_full_lead_under_a_row_cap(self) -> None:
        # A full lead's pass takes full rectangles only, within section 23's window (the cap's rows at the far end): the
        # rounded plate r4 under max_rows 10 proposes full tip-first fields only, each its 10 rows reaching the far end
        # (36.7 / 36.9 mm on the 38 mm side, 28.7 / 28.9 mm on the 30 mm one), every proposal built and mapped.
        proposals = FieldFitTests._check(self, "rounded_4", dict(FIELD, max_rows=10))
        self.assertEqual([(p["metrics"]["rows"], p["metrics"]["columns"], p["metrics"]["taxels"], design_mask(p["design"]) is None, p["metrics"]["tip"]["lead"])
                          for p in proposals], [(10, 14, 140, True, True), (10, 13, 130, True, True), (10, 18, 180, True, True), (10, 17, 170, True, True)])
        self.assertEqual([round(p["metrics"]["tip"]["reach_mm"], 4) for p in proposals], [36.7, 36.9001, 28.7, 28.9001])

    def test_the_peel_fallback(self) -> None:
        # tip_peel_holds at its bounds (the tip-first field's report: floor, cut, full) ...
        tip = {"floor": 97, "cut": 49_750_000, "full": False}
        self.assertTrue(fieldfit.tip_peel_holds(tip, _tip_candidate(97, 49_750_000)))
        self.assertFalse(fieldfit.tip_peel_holds(tip, _tip_candidate(96, 49_750_000)))  # below its floor
        self.assertFalse(fieldfit.tip_peel_holds(tip, _tip_candidate(97, 49_749_999)))  # out of its lead
        self.assertFalse(fieldfit.tip_peel_holds(dict(tip, full=True), _tip_candidate(97, 49_750_000)))  # a full lead's, notched
        self.assertTrue(fieldfit.tip_peel_holds(dict(tip, full=True), _tip_candidate(97, 49_750_000, full=True)))
        # ... and in the fit: the taper's tip-first 351 (at its floor, 97 % of the 361) peeled at its far end falls under
        # the floor, so the 361 it displaced keeps the slot and the peel is not proposed.
        from unittest import mock

        data, selection, _, _ = _Fits.get(self, "taper", FIELD, {"side": 0})
        realize = fieldfit.realize_field
        peels = []

        def peeling(candidate, *args):
            if candidate.get("tip_lead") and not peels:
                peels.append(fieldfit.peel_field(candidate, (candidate["field_origin"][0], 1e3)))
                return None, peels[-1]
            return realize(candidate, *args)

        with mock.patch.object(fieldfit, "realize_field", peeling):
            result = fit.fit_route({"selection": selection, "base": {"side": 0}, "options": FIELD}, data)
        self.assertLess(peels[0]["value"], 351)
        first = result["proposals"][0]
        self.assertEqual((first["metrics"]["taxels"], first["metrics"]["tip"]["lead"]), (361, False))
        self.assertNotIn(peels[0]["taxels"], [p["metrics"]["taxels"] for p in result["proposals"] if p["metrics"]["tip"]["lead"]])


if __name__ == "__main__":
    unittest.main()
