"""CAD mode's border of the taxels (surface/border.py; claude/specs/cad-mode/BORDER-EDITOR-PLAN.md, sections 2.4, 3, 6).

The user's decisions (section 6): the border is edited in the 3D view and
kept in the selection chart's uv; any simple polygon (a corner drag gives
any quadrilateral); it may reach beyond the surface, but no taxel lies
outside the surface; the exit is an edge of the border; the border
constrains only the taxels (F on the surface as before, the routing free).

Pinned here: the validation (E_SURFACE_BORDER: the request's shape, fewer
than 3 vertices, not simple, under 1 mm2, off the surface, the base and the
exit edge), the exact orientation predicate, the lattice's cell predicate
against brute force; a border inside a large plate placing every taxel
inside it (as many as the border holds), a border partly beyond the
surface (the taxels where both hold), a quadrilateral and a non-convex
border, the border's exits (``border_edge``, ``auto`` over its longest
edges, an edge inside the surface, a clockwise border), the map's
``taxels_inside_border`` record (passing, and failing with a taxel
outside), the fit's and the map's echo, the selection's ``facets_uv``
against its ``outline_uv``, a strain-limited fit carrying the border onto
its disk, the design's taxel squares against the build's, and determinism
(any hash seed, Python 3.12 and 3.9.6 alike where both are installed).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path

from engine import generate_design
from engine.geometry import point_in_polygon, segments_intersect
from surface import api, border, fieldfit, fill, fit, place, select
from surface.errors import SURFACE_ERROR_CODES, SurfaceError
from surface.mesh import read_stl

try:
    import surface_fixtures as F
except ImportError:  # run as a package
    from tests import surface_fixtures as F

ROOT = Path(__file__).resolve().parents[1]
PLATE = [(0.0, 0.0), (60.0, 0.0), (60.0, 40.0), (0.0, 40.0)]
OPTIONS = {"pitch_mm": 2.0}
WIDTH = fit._electrode(2.0, fit.DEFAULT_OPTIONS["fill"])  # the crossing at 2 mm: 1.0 mm (fill 0.5; 1.4 at 0.7 before 2026-11-06)


class _Plate:
    """A plate's mesh, selection and select reply (cached), and fits with a border (cached by request)."""

    _cache: dict = {}

    @classmethod
    def get(cls, outline=None) -> tuple:
        outline = PLATE if outline is None else outline
        key = ("plate", tuple(outline))
        if key not in cls._cache:
            data = F.stl_bytes(F.plate(outline, 3.0))
            mesh = read_stl(data)
            centre = (math.fsum(p[0] for p in outline) / len(outline), math.fsum(p[1] for p in outline) / len(outline), 3.0)
            selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, centre)}]}
            reply = api.select_surface({"selection": selection}, data)["selection"]
            cls._cache[key] = (data, selection, reply)
        return cls._cache[key]

    @classmethod
    def fit(cls, uv, base="auto", options=None, outline=None) -> dict:
        data, selection, _ = cls.get(outline)
        options = OPTIONS if options is None else options
        key = ("fit", tuple(map(tuple, uv)), repr(base), repr(sorted(options.items())), repr(outline))
        if key not in cls._cache:
            cls._cache[key] = fit.fit_route({"selection": selection, "base": base, "border": {"uv": [list(p) for p in uv]}, "options": options}, data)
        return cls._cache[key]


def _box(reply: dict) -> tuple:
    """The selection's uv extent ``(u0, v0, u1, v1)``."""

    us = [p[0] for p in reply["outline_uv"]]
    vs = [p[1] for p in reply["outline_uv"]]
    return min(us), min(vs), max(us), max(vs)


def _frame(placement: dict) -> fit.BaseFrame:
    side = {"from_uv": placement["base_from_uv"], "to_uv": placement["base_to_uv"], "inward_uv": placement["base_inward_uv"]}
    return fit.BaseFrame(side, placement["base_angle_deg"])


def _corners_uv(proposal: dict) -> list:
    """Each taxel square's four corners in the chart's uv, from the build (the map's own electrodes)."""

    result = generate_design(proposal["design"])
    frame = _frame(proposal["placement"])
    squares = border.build_squares(result, proposal["placement"]["field_origin_base"])
    return [[frame.to_chart(p) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))] for _, _, x0, y0, x1, y1 in squares]


def _in_convex(point, polygon, slack: float = 1e-7) -> bool:
    """A point in a convex counter-clockwise polygon (half-planes), up to ``slack`` mm."""

    n = len(polygon)
    for k in range(n):
        (ax, ay), (bx, by) = polygon[k], polygon[(k + 1) % n]
        length = math.hypot(bx - ax, by - ay)
        if ((bx - ax) * (point[1] - ay) - (by - ay) * (point[0] - ax)) / length < -slack:
            return False
    return True


def _square_in_polygon(polygon, x0, y0, x1, y1) -> bool:
    """Brute force (any simple polygon, general position): the square's corners inside, no polygon vertex inside the
    square, no polygon edge crossing a side of the square."""

    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if not all(point_in_polygon(p, polygon) for p in corners):
        return False
    if any(x0 < p[0] < x1 and y0 < p[1] < y1 for p in polygon):
        return False
    sides = [(corners[k - 1], corners[k]) for k in range(4)]
    return not any(segments_intersect(a, b, polygon[k - 1], polygon[k]) for a, b in sides for k in range(len(polygon)))


def _star(rng: random.Random, count: int, centre=(0.0, 0.0), low=4.0, high=12.0) -> list:
    """A random star-shaped simple polygon, counter-clockwise."""

    return [(centre[0] + r * math.cos(2 * math.pi * k / count), centre[1] + r * math.sin(2 * math.pi * k / count))
            for k, r in enumerate(rng.uniform(low, high) for _ in range(count))]


def _rule(mapped: dict, rule: str) -> dict:
    return next(record for record in mapped["verification"] if record["rule"] == rule)


def _map(proposal: dict, placement=None) -> dict:
    data, selection, _ = _Plate.get()
    return place.map_route({"selection": selection, "placement": proposal["placement"] if placement is None else placement,
                            "design": proposal["design"]}, data)


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


class ValidationTests(unittest.TestCase):
    def assertBorderError(self, call, fragment: str = "") -> SurfaceError:
        with self.assertRaises(SurfaceError) as raised:
            call()
        self.assertEqual(raised.exception.code, "E_SURFACE_BORDER", raised.exception.message)
        self.assertIn(fragment, raised.exception.message)
        return raised.exception

    def test_the_code_is_catalogued(self) -> None:
        self.assertIn("E_SURFACE_BORDER", SURFACE_ERROR_CODES)

    def test_malformed_borders_are_refused(self) -> None:
        square = [[0, 0], [10, 0], [10, 10], [0, 10]]
        cases = [
            (None, '{"uv"'), ([[0, 0], [1, 0], [1, 1]], '{"uv"'), ({"uv": square, "edges": 1}, '{"uv"'), ({"points": square}, '{"uv"'),
            ({"uv": "0,0 1,0 1,1"}, "list"), ({"uv": [[0, 0], [10, 0]]}, "at least 3"), ({"uv": []}, "at least 3"),
            ({"uv": [[0, 0], [10, 0], [10]]}, "uv[2]"), ({"uv": [[0, 0], [10, 0], "10,10"]}, "uv[2]"),
            ({"uv": [[0, 0], [10, 0], [True, 10]]}, "uv[2][0]"), ({"uv": [[0, 0], [10, 0], [10, float("nan")]]}, "uv[2][1]"),
            ({"uv": [[0, 0], [10, 0], [10, float("inf")]]}, "uv[2][1]"), ({"uv": [[0, 0], [2e7, 0], [0, 10]]}, "uv[1][0]"),
            ({"uv": [[0, 0], [10, 0], [None, 10]]}, "uv[2][0]"),
            ({"uv": [[k, (k * 7) % 5] for k in range(border.MAX_VERTICES + 1)]}, f"at most {border.MAX_VERTICES}"),
        ]
        for raw, fragment in cases:
            with self.subTest(raw=str(raw)[:60]):
                self.assertBorderError(lambda: border.parse(raw), fragment)

    def test_polygons_that_are_not_simple_are_refused(self) -> None:
        cases = {
            "bow tie": ([[0, 0], [10, 10], [10, 0], [0, 10]], "edges 0 and 2 cross"),
            "repeated closing vertex": ([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]], "coincide"),
            "repeated vertex": ([[0, 0], [10, 0], [10, 0], [10, 10]], "coincide"),
            "fold back": ([[0, 0], [10, 0], [5, 0], [5, 10]], "fold back"),
            "spike back along an edge": ([[0, 0], [10, 0], [10, 10], [10, 5], [0, 10]], "fold back"),
            "vertex on another edge": ([[0, 0], [10, 0], [10, 10], [5, 0], [0, 10]], "touch"),
            "two loops through one point": ([[0, 0], [5, 5], [10, 0], [10, 10], [5, 5], [0, 10]], "touch"),
            "collinear triangle": ([[0, 0], [5, 0], [10, 0]], "fold back"),
        }
        for name, (uv, fragment) in cases.items():
            with self.subTest(case=name):
                self.assertBorderError(lambda: border.parse({"uv": uv}), fragment)

    def test_a_tiny_border_is_refused_and_one_mm2_is_kept(self) -> None:
        self.assertBorderError(lambda: border.parse({"uv": [[0, 0], [0.9, 0], [0.9, 1.0], [0, 1.0]]}), "at least 1 mm2")
        self.assertEqual(len(border.parse({"uv": [[0, 0], [1, 0], [1, 1], [0, 1]]})), 4)
        # A clockwise border is taken too (its inward normals still point into it).
        self.assertEqual(border.parse({"uv": [[0, 0], [0, 10], [10, 10], [10, 0]]}), [(0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0)])

    def test_the_orientation_is_exact(self) -> None:
        # Shewchuk's example: points near the line through (12, 12) and (24, 24), a float's step apart.
        step = 2.0 ** -53
        for i in range(48):
            for j in range(48):
                p, q, r = (0.5 + i * step, 0.5 + j * step), (12.0, 12.0), (24.0, 24.0)
                exact = (Fraction(q[0]) - Fraction(p[0])) * (Fraction(r[1]) - Fraction(p[1])) - (Fraction(q[1]) - Fraction(p[1])) * (Fraction(r[0]) - Fraction(p[0]))
                self.assertEqual(border.orient(p, q, r), (exact > 0) - (exact < 0), (i, j))

    def test_the_base_must_be_an_edge_of_the_border(self) -> None:
        data, selection, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [[u0 + 5, v0 + 5], [u0 + 25, v0 + 5], [u0 + 25, v0 + 25], [u0 + 5, v0 + 25]]
        for base in ({"side": 0}, {"point_xyz": [30.0, 0.0, 3.0]}, {"arc": {"point_xyz": [30.0, 0.0, 3.0]}}, "left", {"border_edge": 0, "side": 1}):
            with self.subTest(base=base):
                self.assertBorderError(lambda: fit.fit_route({"selection": selection, "base": base, "border": {"uv": uv}}, data), "edge of it")
        for base in ({"border_edge": 4}, {"border_edge": -1}, {"border_edge": True}, {"border_edge": "1"}, {"border_edge": 1.0}):
            with self.subTest(base=base):
                self.assertBorderError(lambda: fit.fit_route({"selection": selection, "base": base, "border": {"uv": uv}}, data), "0..3")
        self.assertBorderError(lambda: fit.fit_route({"selection": selection, "base": {"border_edge": 0}}, data), "give the border")

    def test_an_exit_edge_needs_three_mm(self) -> None:
        data, selection, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        # Edge 1 is 2 mm long.
        uv = [[u0 + 5, v0 + 5], [u0 + 25, v0 + 5], [u0 + 25, v0 + 7], [u0 + 15, v0 + 25], [u0 + 5, v0 + 25]]
        self.assertBorderError(lambda: fit.fit_route({"selection": selection, "base": {"border_edge": 1}, "border": {"uv": uv}}, data), "3 mm")
        # auto skips it.
        result = _Plate.fit(uv, options=dict(OPTIONS, rotation="none"))
        self.assertNotIn(1, {item["side"] for item in result["bases"]})

    def test_a_border_off_the_surface_is_refused(self) -> None:
        data, selection, reply = _Plate.get()
        u0, v0, u1, v1 = _box(reply)
        for uv in ([[u1 + 1, v0], [u1 + 11, v0], [u1 + 11, v0 + 10], [u1 + 1, v0 + 10]],
                   # touching the surface along an edge only
                   [[u1, v0], [u1 + 10, v0], [u1 + 10, v0 + 10], [u1, v0 + 10]]):
            with self.subTest(uv=uv):
                self.assertBorderError(lambda: fit.fit_route({"selection": selection, "border": {"uv": uv}}, data), "does not overlap")

    def test_an_edge_with_no_surface_across_it_is_no_exit(self) -> None:
        data, selection, reply = _Plate.get()
        u0, v0, u1, v1 = _box(reply)
        # An L whose arm reaches beyond the surface across u: edge 2 (u1 + 30 -> u1 + 20 at v0 + 20) faces no surface.
        uv = [[u1 - 10, v0 + 10], [u1 + 30, v0 + 10], [u1 + 30, v0 + 20], [u1 + 20, v0 + 20], [u1 + 20, v0 + 30], [u1 - 10, v0 + 30]]
        error = self.assertBorderError(lambda: fit.fit_route({"selection": selection, "base": {"border_edge": 2}, "border": {"uv": uv}}, data),
                                       "no surface across")
        self.assertIn("Border edge 2", error.message)
        sides = border.bases("auto", border.parse({"uv": uv}), api.selection_chart(read_stl(data), selection)[1])
        self.assertNotIn(2, [side["index"] for side in sides])

    def test_a_border_needs_field_containment(self) -> None:
        data, selection, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [[u0 + 5, v0 + 5], [u0 + 25, v0 + 5], [u0 + 25, v0 + 25], [u0 + 5, v0 + 25]]
        self.assertBorderError(lambda: fit.fit_route({"selection": selection, "border": {"uv": uv}, "options": {"containment": "board"}}, data),
                               "containment field")
        # The generic template and shape rectangle (with or without a border) are no CAD options since P5-diagonal-bus.md
        # section 26.16: refused before the border is looked at.
        for options in ({"template": "generic"}, {"shape": "rectangle", "containment": "board"}):
            with self.subTest(options=options), self.assertRaises(SurfaceError) as raised:
                fit.fit_route({"selection": selection, "border": {"uv": uv}, "options": options}, data)
            self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")
        # Without containment a border takes field-only containment (the default).
        result = _Plate.fit(uv, options={"pitch_mm": 2.0, "rotation": "none"})
        self.assertEqual(result["request"]["options"]["containment"], "field")
        self.assertTrue(all(p["metrics"]["containment"] == "field" for p in result["proposals"]))

    def test_a_border_too_small_for_a_taxel_says_so(self) -> None:
        data, selection, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        # 0.1 mm narrower than a crossing.
        uv = [[u0 + 10, v0 + 10], [u0 + 13.3, v0 + 10], [u0 + 13.3, v0 + 9.9 + WIDTH], [u0 + 10, v0 + 9.9 + WIDTH]]
        with self.assertRaises(SurfaceError) as raised:
            fit.fit_route({"selection": selection, "border": {"uv": uv}, "options": OPTIONS}, data)
        self.assertEqual(raised.exception.code, "E_SURFACE_NO_FIT")
        self.assertIn("inside the border", raised.exception.message)

    def test_unknown_header_keys_are_still_refused(self) -> None:
        data, selection, _ = _Plate.get()
        with self.assertRaises(SurfaceError) as raised:
            fit.fit_route({"selection": selection, "borders": {"uv": [[0, 0], [1, 0], [1, 1]]}}, data)
        self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")


# --------------------------------------------------------------------------
# The lattice's cell predicate
# --------------------------------------------------------------------------


class CellPredicateTests(unittest.TestCase):
    def test_cells_inside_the_border_against_brute_force(self) -> None:
        rng = random.Random(20261024)
        frame = fit.BaseFrame({"from_uv": [0.0, 0.0], "to_uv": [1.0, 0.0], "inward_uv": [0.0, 1.0]}, 0.0)
        checked = inside = 0
        for trial in range(40):
            polygon = _star(rng, rng.randint(5, 14))
            held = border.FrameBorder(polygon, frame)
            pitch = rng.uniform(0.8, 2.5)
            width = pitch * rng.uniform(0.4, 0.8)
            x0 = -13.0 + rng.uniform(0, pitch)
            columns = int(26 / pitch)
            for row in range(int(26 / pitch)):
                y = -13.0 + rng.uniform(0, 0.01) + row * pitch
                flags = held.flags(y, x0, pitch, width, columns)
                for c in range(columns):
                    expected = _square_in_polygon(polygon, x0 + c * pitch, y, x0 + c * pitch + width, y + width)
                    self.assertEqual(flags[c], expected, (trial, row, c))
                    checked += 1
                    inside += expected
                ends = held.ends(y, x0, pitch, width, columns)
                for a in range(columns):
                    b = a
                    while b + 1 < columns and flags[b + 1] and flags[a]:
                        b += 1
                    self.assertEqual(ends[a], b if flags[a] else -1)
        self.assertGreater(inside, checked // 10)

    def test_the_lattice_caps_its_runs_with_the_border(self) -> None:
        # surface.fieldfit.lattice on a frame with a border: each row's run ends are the ones without it capped by the
        # border's, every capped run's taxel squares lie inside the border, and phase 0 puts the first crossing on the
        # border where it lies inside the surface.
        data, selection, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [(u0 + 4.3, v0 + 6.1), (u0 + 34.2, v0 + 3.7), (u0 + 30.9, v0 + 44.4), (u0 + 7.6, v0 + 31.2)]
        mesh = read_stl(data)
        chart = api.selection_chart(mesh, selection)[1]
        options = fit.parse_options(OPTIONS)
        obstacles = fit.surface_obstacles(mesh, chart, dict(options, border=uv))
        margin = float(fit.load_profile_cached("surface")["routing"]["active_edge_clearance_mm"])
        checked = 0
        for index in range(4):
            side = border.edge_side(uv, index, chart)
            for angle in (0.0, 20.0):
                frame = fit.BaseFrame(side, angle)
                space = fill.FreeSpace(chart, frame, obstacles, 0.0, side["edges"])
                polygon = [frame.to_base(p) for p in uv]
                held = space.border
                for phase in ((0.0, 0.0), (0.5, 1.5)):
                    grid = fieldfit.lattice(space, 2.0, WIDTH, margin, phase)
                    if phase == (0.0, 0.0):
                        self.assertAlmostEqual(grid["x0"], max(min(p[0] for p in polygon), min(p[0] for p in space.outline) + space.margin + margin), places=9)
                        self.assertAlmostEqual(grid["y0"], max(min(p[1] for p in polygon), min(p[1] for p in space.outline) + space.margin + margin), places=9)
                    space.border = None
                    free = fieldfit.lattice(space, 2.0, WIDTH, margin, phase)
                    space.border = held
                    for j in range(grid["rows"]):
                        y = grid["y0"] + j * 2.0
                        capped = held.ends(y, grid["x0"], 2.0, WIDTH, grid["columns"])
                        self.assertEqual(grid["plain"][j], list(map(min, free["plain"][j], capped)))
                        for a, b in enumerate(grid["plain"][j]):
                            for c in range(a, b + 1):
                                x = grid["x0"] + c * 2.0
                                self.assertTrue(_square_in_polygon(polygon, x + 1e-7, y + 1e-7, x + WIDTH - 1e-7, y + WIDTH - 1e-7), (index, angle, j, c))
                                checked += 1
        self.assertGreater(checked, 1000)

    def test_a_square_touching_the_border_from_inside_is_inside(self) -> None:
        frame = fit.BaseFrame({"from_uv": [0.0, 0.0], "to_uv": [1.0, 0.0], "inward_uv": [0.0, 1.0]}, 0.0)
        held = border.FrameBorder([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)], frame)
        self.assertTrue(held.square_inside(0.0, 0.0, 10.0, 10.0))
        self.assertTrue(held.square_inside(8.6, 8.6, 10.0, 10.0))
        self.assertFalse(held.square_inside(8.7, 8.7, 10.1, 10.1))
        self.assertTrue(held.square_inside(8.7, 8.7, 10.0 + 5e-7, 10.0 + 5e-7, border.INSIDE_TOLERANCE_MM))
        self.assertEqual(held.flags(0.0, 0.0, 2.0, 1.4, 6), [True] * 5 + [False])
        # A notch from above: the cells beside it are inside, the one under it is not.
        notched = border.FrameBorder([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (5.5, 10.0), (5.0, 1.0), (4.5, 10.0), (0.0, 10.0)], frame)
        self.assertEqual(notched.flags(0.0, 0.0, 2.0, 1.4, 5), [True, True, False, True, True])


# --------------------------------------------------------------------------
# Fits with a border
# --------------------------------------------------------------------------


def _expected_count(width_mm: float, height_mm: float, pitch: float = 2.0, crossing: float = WIDTH) -> int:
    def along(extent: float) -> int:
        return int(math.floor((extent - crossing) / pitch + 1e-9)) + 1

    return along(width_mm) * along(height_mm)


class InsideTests(unittest.TestCase):
    def test_a_border_inside_a_large_plate_places_every_taxel_inside_it(self) -> None:
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [(u0 + 10, v0 + 10), (u0 + 35, v0 + 10), (u0 + 35, v0 + 28), (u0 + 10, v0 + 28)]
        result = _Plate.fit(uv)
        self.assertTrue(result["proposals"])
        # As many as the 25 x 18 mm border holds at 2 mm (the surface around it holds many more).
        self.assertEqual(result["proposals"][0]["metrics"]["taxels"], _expected_count(25.0, 18.0))
        for proposal in result["proposals"]:
            with self.subTest(rank=proposal["rank"]):
                for corners in _corners_uv(proposal):
                    self.assertTrue(all(_in_convex(p, uv) for p in corners), corners)
                metrics = proposal["metrics"]
                self.assertEqual((metrics["border_area_mm2"], metrics["border_on_surface_share"]), (450.0, 1.0))
                self.assertEqual(proposal["placement"]["border"], border.echo(uv))
                self.assertEqual(proposal["placement"]["base_kind"], "border")
                mapped = _map(proposal)
                self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
                record = _rule(mapped, "taxels_inside_border")
                self.assertEqual((record["measured"], record["passed"]), (0, True))
                self.assertEqual(mapped["border"], border.echo(uv))
        self.assertEqual(result["request"]["border"], border.echo(uv))
        self.assertNotIn("border", result["obstacles"])
        self.assertNotIn("border", result["request"]["options"])

    def test_the_field_touches_the_border_inside_the_surface(self) -> None:
        # P may come up to the border where it lies inside the surface (only F's margin must stay on the surface).
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        # 12 x 9 crossings exactly: 11 and 8 pitches and a crossing across.
        right, top = u0 + 32 + WIDTH, v0 + 26 + WIDTH
        uv = [(u0 + 10, v0 + 10), (right, v0 + 10), (right, top), (u0 + 10, top)]
        result = _Plate.fit(uv, options=dict(OPTIONS, rotation="none"))
        self.assertEqual(result["proposals"][0]["metrics"]["taxels"], 12 * 9)
        corners = [p for square in _corners_uv(result["proposals"][0]) for p in square]
        for k, (low, high) in enumerate(((u0 + 10, right), (v0 + 10, top))):
            self.assertAlmostEqual(min(p[k] for p in corners), low, places=5)
            self.assertAlmostEqual(max(p[k] for p in corners), high, places=5)

    def test_a_border_partly_beyond_the_surface_holds_taxels_where_both_hold(self) -> None:
        _, _, reply = _Plate.get()
        u0, v0, u1, v1 = _box(reply)
        uv = [(u0 + 10, v1 - 15), (u0 + 30, v1 - 15), (u0 + 30, v1 + 25), (u0 + 10, v1 + 25)]
        result = _Plate.fit(uv)
        outline = [tuple(p) for p in reply["outline_uv"]]
        # P inside the border and F (P and its 0.5 mm margin) on the surface: 20 mm across, 14.5 mm along.
        self.assertEqual(result["proposals"][0]["metrics"]["taxels"], _expected_count(20.0, 14.5))
        for proposal in result["proposals"]:
            with self.subTest(rank=proposal["rank"]):
                for corners in _corners_uv(proposal):
                    self.assertTrue(all(_in_convex(p, uv) and _in_convex(p, outline) for p in corners), corners)
                self.assertEqual(proposal["metrics"]["border_area_mm2"], 800.0)
                self.assertEqual(proposal["metrics"]["border_on_surface_share"], 0.375)
                mapped = _map(proposal)
                self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])

    def test_a_quadrilateral_border(self) -> None:
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [(u0 + 4, v0 + 6), (u0 + 34, v0 + 3), (u0 + 30, v0 + 44), (u0 + 7, v0 + 31)]
        result = _Plate.fit(uv)
        self.assertGreater(result["proposals"][0]["metrics"]["taxels"], 100)
        for proposal in result["proposals"]:
            with self.subTest(rank=proposal["rank"]):
                for corners in _corners_uv(proposal):
                    self.assertTrue(all(_in_convex(p, uv) for p in corners), corners)
                mapped = _map(proposal)
                self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        # The field follows the quadrilateral: a masked field among the proposals.
        self.assertTrue(any(p["design"]["matrix"].get("mask") for p in result["proposals"]))

    def test_a_non_convex_border(self) -> None:
        # An arrow: the taxels stay out of its notch (per square, against brute force on the build in its base frame).
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [(u0 + 5, v0 + 5), (u0 + 35, v0 + 5), (u0 + 35, v0 + 40), (u0 + 20, v0 + 22), (u0 + 5, v0 + 40)]
        result = _Plate.fit(uv)
        self.assertGreater(result["proposals"][0]["metrics"]["taxels"], 100)
        for proposal in result["proposals"]:
            with self.subTest(rank=proposal["rank"]):
                frame = _frame(proposal["placement"])
                polygon = [frame.to_base(p) for p in uv]
                squares = border.build_squares(generate_design(proposal["design"]), proposal["placement"]["field_origin_base"])
                for _, _, x0, y0, x1, y1 in squares:
                    self.assertTrue(_square_in_polygon(polygon, x0 + 1e-7, y0 + 1e-7, x1 - 1e-7, y1 - 1e-7), (x0, y0, x1, y1))
                mapped = _map(proposal)
                self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])

    def test_the_design_squares_are_the_builds(self) -> None:
        # The fit checks its proposals from the design (no rebuild); the map from the build: both give the same squares.
        # Eight proposals: since P5-diagonal-bus.md section 26 the tip-first fields take two of the first five slots, the
        # full 13 x 12 sixth.
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [(u0 + 4, v0 + 6), (u0 + 34, v0 + 3), (u0 + 30, v0 + 44), (u0 + 7, v0 + 31)]
        seen = set()
        for options in (dict(OPTIONS, proposals=8), dict(OPTIONS, proposals=8, role_mapping="columns_top")):
            for proposal in _Plate.fit(uv, options=options)["proposals"]:
                origin = proposal["placement"]["field_origin_base"]
                built = border.build_squares(generate_design(proposal["design"]), origin)
                designed = border.design_squares(proposal["design"], origin)
                self.assertEqual([item[:2] for item in built], [item[:2] for item in designed])
                for first, second in zip(built, designed):
                    self.assertLess(max(abs(a - b) for a, b in zip(first[2:], second[2:])), 1e-9, (first, second))
                seen.add((proposal["design"]["role_mapping"]["top"], proposal["design"]["matrix"].get("mask") is not None))
        self.assertEqual(seen, {("rows", True), ("rows", False), ("columns", True), ("columns", False)})


# --------------------------------------------------------------------------
# The exits: edges of the border
# --------------------------------------------------------------------------


class ExitTests(unittest.TestCase):
    def test_each_edge_of_a_quadrilateral_as_the_exit(self) -> None:
        data, selection, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [(u0 + 4, v0 + 6), (u0 + 34, v0 + 3), (u0 + 30, v0 + 44), (u0 + 7, v0 + 31)]
        chart = api.selection_chart(read_stl(data), selection)[1]
        for index in range(4):
            with self.subTest(edge=index):
                result = _Plate.fit(uv, base={"border_edge": index}, options=dict(OPTIONS, rotation="none"))
                self.assertEqual({item["side"] for item in result["bases"]}, {index})
                a, b = uv[index], uv[(index + 1) % 4]
                length = math.hypot(b[0] - a[0], b[1] - a[1])
                inward = (-(b[1] - a[1]) / length, (b[0] - a[0]) / length)
                for proposal in result["proposals"]:
                    placement = proposal["placement"]
                    self.assertEqual((placement["base_side"], placement["base_kind"], placement["base_angle_deg"]), (index, "border", 0.0))
                    self.assertEqual(placement["base_from_uv"], [round(a[0], 6), round(a[1], 6)])
                    self.assertEqual(placement["base_to_uv"], [round(b[0], 6), round(b[1], 6)])
                    self.assertLess(math.dist(placement["base_inward_uv"], inward), 1e-8)
                    # The exit segments: the plate's sides that the edge's span meets first beyond it (the tails cross
                    # the rest of the surface beyond the edge, which lies inside it).
                    frame = _frame(placement)
                    outline = [frame.to_base(p) for p in chart.outline()]
                    self.assertEqual(placement["exit_edges"], border.exit_segments(outline, frame.length))
                    self.assertTrue(placement["exit_edges"])
                    lowest = fit.ExitOutline(outline, range(len(outline)))
                    for k in range(65):
                        y, segment = lowest.lowest_segment(frame.length * (k + 0.5) / 65.5)
                        self.assertIn(segment, placement["exit_edges"])
                        self.assertLess(y, 0.0)  # below the edge: the edge lies inside the surface
                    mapped = _map(proposal)
                    self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])

    def test_auto_tries_the_longest_edges_at_most_six(self) -> None:
        _, _, reply = _Plate.get()
        u0, v0, u1, v1 = _box(reply)
        cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
        # An octagon with edges of eight different lengths (all at least 3 mm).
        radii = [14.0, 17.0, 13.0, 19.0, 15.0, 12.0, 18.0, 16.0]
        uv = [(cu + r * math.cos(math.pi * k / 4), cv + r * math.sin(math.pi * k / 4)) for k, r in enumerate(radii)]
        lengths = [math.dist(uv[k], uv[(k + 1) % 8]) for k in range(8)]
        expected = sorted(range(8), key=lambda k: (-lengths[k], k))[:6]
        result = _Plate.fit(uv, options=dict(OPTIONS, rotation="none"))
        self.assertEqual([item["side"] for item in result["bases"]], expected)
        self.assertIn(result["proposals"][0]["placement"]["base_side"], expected)
        self.assertEqual([side["index"] for side in border.bases("auto", uv, api.selection_chart(read_stl(_Plate.get()[0]), _Plate.get()[1])[1])], expected)

    def test_a_clockwise_border_points_its_normals_inside(self) -> None:
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        ccw = [(u0 + 10, v0 + 10), (u0 + 35, v0 + 10), (u0 + 35, v0 + 28), (u0 + 10, v0 + 28)]
        cw = list(reversed(ccw))
        first = _Plate.fit(ccw, options=dict(OPTIONS, rotation="none"))
        second = _Plate.fit(cw, options=dict(OPTIONS, rotation="none"))
        self.assertEqual(first["proposals"][0]["metrics"]["taxels"], second["proposals"][0]["metrics"]["taxels"])
        for proposal in second["proposals"]:
            placement = proposal["placement"]
            middle = [(a + b) / 2 for a, b in zip(placement["base_from_uv"], placement["base_to_uv"])]
            probe = [middle[k] + placement["base_inward_uv"][k] for k in range(2)]
            self.assertTrue(_in_convex(probe, ccw))
            for corners in _corners_uv(proposal):
                self.assertTrue(all(_in_convex(p, ccw) for p in corners))

    def test_the_turned_frames_keep_the_border(self) -> None:
        # rotation auto turns the boards against the best edges; every proposal, turned or not, keeps its taxels inside.
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [(u0 + 4, v0 + 6), (u0 + 34, v0 + 3), (u0 + 30, v0 + 44), (u0 + 7, v0 + 31)]
        result = _Plate.fit(uv)
        self.assertTrue(any(item["angle_deg"] != 0.0 for item in result["bases"]))
        for proposal in result["proposals"]:
            for corners in _corners_uv(proposal):
                self.assertTrue(all(_in_convex(p, uv) for p in corners))


# --------------------------------------------------------------------------
# The map's record
# --------------------------------------------------------------------------


class MapRecordTests(unittest.TestCase):
    def _proposal(self) -> tuple:
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        uv = [(u0 + 10, v0 + 10), (u0 + 35, v0 + 10), (u0 + 35, v0 + 28), (u0 + 10, v0 + 28)]
        return uv, _Plate.fit(uv)["proposals"][0]

    def test_the_record_fails_when_a_taxel_is_outside(self) -> None:
        uv, proposal = self._proposal()
        placement = copy.deepcopy(proposal["placement"])
        # The border's last edge moved 3 mm inward: the taxels beyond it leave it.
        u0 = uv[0][0]
        placement["border"] = border.echo([(u + 3.0 if u == u0 else u, v) for u, v in uv])
        mapped = _map(proposal, placement)
        record = _rule(mapped, "taxels_inside_border")
        self.assertFalse(record["passed"])
        self.assertFalse(mapped["ok"])
        self.assertGreater(record["measured"], 0)
        self.assertLessEqual(len(record["taxels"]), 16)
        # Every other record still passes: only the border fails.
        self.assertEqual([r["rule"] for r in mapped["verification"] if not r["passed"]], ["taxels_inside_border"])

    def test_the_record_holds_within_its_tolerance_only(self) -> None:
        # A border on the taxels' extent in the base frame, its low side lifted by a shift: the bottom row leaves it.
        _, proposal = self._proposal()
        frame = _frame(proposal["placement"])
        squares = border.build_squares(generate_design(proposal["design"]), proposal["placement"]["field_origin_base"])
        x0, y0 = min(item[2] for item in squares), min(item[3] for item in squares)
        x1, y1 = max(item[4] for item in squares), max(item[5] for item in squares)
        for shift, passed in ((0.0, True), (0.2 * border.INSIDE_TOLERANCE_MM, True), (3 * border.INSIDE_TOLERANCE_MM, False), (0.3, False)):
            with self.subTest(shift=shift):
                placement = copy.deepcopy(proposal["placement"])
                placement["border"] = border.echo([frame.to_chart(p) for p in ((x0, y0 + shift), (x1, y0 + shift), (x1, y1), (x0, y1))])
                record = _rule(_map(proposal, placement), "taxels_inside_border")
                self.assertEqual(record["passed"], passed, record)
                if not passed:
                    rows = {row for row, _ in record["taxels"]}
                    self.assertEqual(rows, {proposal["design"]["matrix"]["rows"]})  # the bottom row only

    def test_a_map_without_a_border_has_no_record(self) -> None:
        data, selection, _ = _Plate.get()
        result = fit.fit_route({"selection": selection, "options": dict(OPTIONS, rotation="none", max_rows=4, max_columns=4)}, data)
        proposal = result["proposals"][0]
        self.assertNotIn("border", proposal["placement"])
        mapped = _map(proposal)
        self.assertNotIn("taxels_inside_border", [r["rule"] for r in mapped["verification"]])
        self.assertNotIn("border", mapped)

    def test_a_damaged_border_in_the_placement_is_refused(self) -> None:
        _, proposal = self._proposal()
        for damage in ({"uv": [[0, 0], [1, 0]]}, {"uv": [[0, 0], [10, 10], [10, 0], [0, 10]]}, [[0, 0], [10, 0], [10, 10]], None):
            with self.subTest(damage=damage):
                placement = dict(proposal["placement"], border=damage)
                with self.assertRaises(SurfaceError) as raised:
                    _map(proposal, placement)
                self.assertEqual(raised.exception.code, "E_SURFACE_BORDER")
                self.assertIn("placement.border", raised.exception.message)


# --------------------------------------------------------------------------
# The selection's facets in uv
# --------------------------------------------------------------------------


class FacetsUvTests(unittest.TestCase):
    def _check(self, data: bytes, point) -> dict:
        mesh = read_stl(data)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, point)}]}
        reply = api.select_surface({"selection": selection}, data)["selection"]
        _, chart = api.selection_chart(mesh, selection)
        self.assertEqual(len(reply["facets_uv"]), len(reply["facets"]))
        for facet, corners in zip(reply["facets"], reply["facets_uv"]):
            expected = [[round(c, 6) + 0.0 for c in chart.uv[v]] for v in mesh.facets[facet]]
            self.assertEqual(len(corners), 3)
            for got, want in zip(corners, expected):
                self.assertLess(math.dist(got, want), 1e-6)
        # The facets tile the outline less its holes, every outline vertex a facet corner; seen from outside they turn
        # counter-clockwise like the outline.
        areas = [fill.polygon_area(corners) for corners in reply["facets_uv"]]
        signed = [border.signed_area(corners) for corners in reply["facets_uv"]]
        outline = fill.polygon_area(reply["outline_uv"]) - math.fsum(fill.polygon_area(hole) for hole in reply["holes_uv"])
        self.assertAlmostEqual(math.fsum(areas), outline, delta=1e-6 * max(1.0, outline))
        self.assertTrue(all(value > 0 for value in signed))
        self.assertGreater(border.signed_area(reply["outline_uv"]), 0)
        corners = {tuple(p) for triangle in reply["facets_uv"] for p in triangle}
        self.assertTrue(all(tuple(p) in corners for p in reply["outline_uv"]))
        self.assertTrue(all(tuple(p) in corners for hole in reply["holes_uv"] for p in hole))
        return reply

    def test_a_plate(self) -> None:
        self._check(F.stl_bytes(F.plate(PLATE, 3.0)), (30.0, 20.0, 3.0))

    def test_a_holed_plate(self) -> None:
        reply = self._check(F.stl_bytes(F.holed_plate()), (5.0, 5.0, 3.0))
        self.assertEqual(len(reply["holes_uv"]), 1)

    def test_a_curved_face(self) -> None:
        self._check(F.stl_bytes(F.soft_finger_replica()), (0.0, -12.9, -62.7))

    def test_the_fit_reply_carries_them_too(self) -> None:
        _, _, reply = _Plate.get()
        u0, v0, _, _ = _box(reply)
        result = _Plate.fit([(u0 + 10, v0 + 10), (u0 + 35, v0 + 10), (u0 + 35, v0 + 28), (u0 + 10, v0 + 28)])
        self.assertEqual(result["selection"]["facets_uv"], reply["facets_uv"])


# --------------------------------------------------------------------------
# A strain-limited fit
# --------------------------------------------------------------------------


class StrainLimitedTests(unittest.TestCase):
    def test_carry_is_the_identity_on_the_same_chart(self) -> None:
        data, selection, _ = _Plate.get()
        chart = api.selection_chart(read_stl(data), selection)[1]
        points = [(1.25, -3.5), (7.0, 2.0), (-4.0, 9.5)]
        for got, want in zip(border.carry(points, chart, chart), points):
            self.assertLess(math.dist(got, want), 1e-9)

    def test_a_dome_carries_the_border_onto_its_disk(self) -> None:
        triangles = F.sphere_cap(60.0, 25.0, rings=8, segments=32)
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (0.0, 0.0, 60.0))
        selection = {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]}
        whole = api.select_surface({"selection": selection}, data)["selection"]
        # A 16 x 12 mm rectangle around the top of the dome, in the selection's chart (what the browser shows).
        cu = math.fsum(p[0] for p in whole["outline_uv"]) / len(whole["outline_uv"])
        cv = math.fsum(p[1] for p in whole["outline_uv"]) / len(whole["outline_uv"])
        uv = [(cu - 8, cv - 6), (cu + 8, cv - 6), (cu + 8, cv + 6), (cu - 8, cv + 6)]
        result = fit.fit_route({"selection": selection, "border": {"uv": [list(p) for p in uv]}, "options": {"pitch_mm": 1.5, "rotation": "none"}}, data)
        self.assertIn("strain_limited", result["selection"])
        _, chart = api.selection_chart(mesh, selection)
        _, disk = fit.limited_chart(mesh, set(chart.facets), result["selection"]["strain_limited"])
        carried = border.carry(uv, chart, disk)
        for proposal in result["proposals"]:
            self.assertEqual(proposal["placement"]["border"], border.echo(uv))
            frame = _frame(proposal["placement"])
            squares = border.design_squares(proposal["design"], proposal["placement"]["field_origin_base"])
            self.assertEqual(border.outside(squares, carried, frame), [])
            # At most what the 16 x 12 mm border holds at 1.5 mm (rows and columns either way round).
            crossing = fit._electrode(1.5, fit.DEFAULT_OPTIONS["fill"])
            self.assertLessEqual(proposal["metrics"]["taxels"], _expected_count(16.0, 12.0, 1.5, crossing))
            mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
            self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
            self.assertTrue(_rule(mapped, "taxels_inside_border")["passed"])


# --------------------------------------------------------------------------
# Determinism
# --------------------------------------------------------------------------


SAMPLE_OUTLINE = [(0.0, 0.0), (48.0, 0.0), (48.0, 32.0), (0.0, 32.0)]
SAMPLE_BORDER = [(-12.5, -18.0), (10.0, -14.5), (13.0, 9.25), (-9.0, 15.5), (-14.0, 1.0)]


def sample_fingerprint() -> str:
    """A digest of a fit with a border on a plate whose coordinates are exact in binary (the same STL bytes on every
    Python): the proposals' build ids, placements, outlines and metrics, and the map's records of the first."""

    data = F.stl_bytes(F.plate(SAMPLE_OUTLINE, 2.0))
    mesh = read_stl(data)
    selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (24.0, 16.0, 2.0))}]}
    result = fit.fit_route({"selection": selection, "border": {"uv": [list(p) for p in SAMPLE_BORDER]}, "options": {"pitch_mm": 2.5}}, data)
    items = [[p["build_id"], {key: value for key, value in p["placement"].items() if key not in ("mesh",)}, p["outlines_uv"], p["metrics"]]
             for p in result["proposals"]]
    first = result["proposals"][0]
    mapped = place.map_route({"selection": selection, "placement": first["placement"], "design": first["design"]}, data)
    items.append([mapped["verification"], mapped["taxels"], result["bases"], result["selection"]["facets_uv"]])
    return hashlib.sha256(json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _interpreters() -> list:
    """This Python and the others installed that run the suite (3.9 and 3.12): the determinism sample runs on each."""

    found = [sys.executable]
    for name in ("/usr/bin/python3", shutil.which("python3.12"), shutil.which("python3.9")):
        if name and os.path.exists(name) and os.path.realpath(name) not in {os.path.realpath(item) for item in found}:
            version = subprocess.run([name, "-c", "import sys; print(sys.version_info[:2] >= (3, 9))"], capture_output=True, text=True)
            if version.returncode == 0 and version.stdout.strip() == "True":
                found.append(name)
    return found


class DeterminismTests(unittest.TestCase):
    def test_the_fit_and_map_with_a_border_are_deterministic(self) -> None:
        self.assertEqual(sample_fingerprint(), sample_fingerprint())

    def test_the_same_on_every_python_and_hash_seed(self) -> None:
        expected = sample_fingerprint()
        code = "import sys; sys.path.insert(0, 'tests'); import test_border as t; print(t.sample_fingerprint())"
        runs = [(name, seed) for name in _interpreters() for seed in ("0", "123")]
        versions = set()
        for name, seed in runs:
            with self.subTest(python=name, seed=seed):
                environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
                output = subprocess.run([name, "-B", "-c", code], cwd=ROOT, env=environment, capture_output=True, text=True)
                self.assertEqual(output.returncode, 0, output.stderr[-2000:])
                self.assertEqual(output.stdout.strip(), expected)
                versions.add(subprocess.run([name, "-c", "import sys; print(sys.version_info[:2])"], capture_output=True, text=True).stdout.strip())
        self.assertTrue(versions)


if __name__ == "__main__":
    unittest.main()
