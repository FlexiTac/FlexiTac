"""CAD mode's masked fields (fit option ``shape: fill``, masked-field phase P4) and its readers.

``shape: fill`` (surface/fill.py) proposes masked fields of the engine's
straight construction classes, merged with the rectangles of the raster
search (:func:`surface.fit.search`, ``shape: rectangle``'s own proposals
before P5-diagonal-bus.md section 26.16; a mask must win by more taxels),
at most ``max_rows``
x ``max_columns`` like the rectangles (32 x 32 until P5-diagonal-bus.md
section 21); the map lists only the active crossings and adds the readout; the reader option
(surface/reader.py) sizes the tails for a 16x16, 32x16 (FlexiTac), 32x32 or
48x48 reader and reports its lines (claude/specs/masked-field/PLAN.md,
section 8).  Pinned here: the taxels on the synthetic plates, the crank tip
pad and the soft finger, every masked proposal
DRC-clean and mapped with every record passing, the exact free space
against check_containment, the peel, the metrics and the field polygon, the
readers' pins and frame indices, the web client's handling of the mask and
the determinism of the new code.  From the P4 reviews: a named reader caps
the masked walk at its lines, the metrics and the map name the same reader,
the placement option and the role mapping do not change the count the
search finds, the proposals carry one mask per readout and none that an
earlier one dominates, and the web client keeps the mask through a mode
switch and shows its issues with a way back to the full field.  On the
receding fields of the
disk and the wide ellipse (the default field fits with ``routing.row_sides``)
the diagonal Row bus's lanes follow the field inward, with no flat lane
(claude/specs/masked-field/P5-diagonal-bus.md, section 14.2).
"""

from __future__ import annotations

import copy
import math
import random
import re
import time
import unittest
from pathlib import Path
from typing import Any

from engine import design_mask, generate_design
from engine.geometry import point_in_polygon, segment_distance
from surface import fill, fit, place, select
from surface import reader as reader_module
from surface.errors import SurfaceError
from surface.mesh import read_stl

try:
    import surface_fixtures as F
    from test_diagonal_bus import _stray_from_field
    from test_mask_layout import _determinism_problems
    import defaults_of_before
except ImportError:  # run as a package
    from tests import surface_fixtures as F
    from tests.test_diagonal_bus import _stray_from_field
    from tests.test_mask_layout import _determinism_problems
    from tests import defaults_of_before


def setUpModule() -> None:
    # The default electrodes of before (1.4 mm at 2 mm, fill 0.7): this module's pinned numbers were measured with them
    # (tests/defaults_of_before.py; the user's decision of 2026-11-06 made the default fill 0.5).
    defaults_of_before.start()


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "asset"
CRANK = ASSETS / "crank_gripper" / "tip_left.stl"
SOFT_SEED = (0.0, -12.9, -62.7)
SOFT_BASE = {"point_xyz": [0.0, -12.9, -3.0]}
PLATES = {
    "right_triangle": [(0.0, 0.0), (60.0, 0.0), (0.0, 60.0)],
    "equilateral": [(0.0, 0.0), (60.0, 0.0), (30.0, 51.9615)],
    "disk": F.ellipse_outline(25.0, 25.0, 72),
    "wide_ellipse": F.ellipse_outline(40.0, 18.0, 72),
    "wide_plate": [(0.0, 0.0), (90.0, 0.0), (90.0, 60.0), (0.0, 60.0)],
}


class _Fits:
    """Fits of the fixtures, each run once: ``(data, selection, result, seconds)``."""

    _cache: dict = {}

    @classmethod
    def case(cls, name: str) -> tuple:
        if name == "soft_finger":
            return F.stl_bytes(F.soft_finger_replica()), SOFT_SEED, SOFT_BASE
        if name == "crank":
            return CRANK.read_bytes(), (1.812, -213.721, 138.929), "auto"
        if name == "holed_plate":
            return F.stl_bytes(F.holed_plate()), (5.0, 5.0, 3.0), "auto"
        outline = PLATES[name]
        centre = (math.fsum(p[0] for p in outline) / len(outline), math.fsum(p[1] for p in outline) / len(outline), 3.0)
        return F.stl_bytes(F.plate(outline, 3.0)), centre, "auto"

    @classmethod
    def get(cls, name: str, options: dict, base: Any = None) -> tuple:
        """The fit of fixture ``name`` with ``options``, at its own base or at ``base`` (``{"side": n}``, ...)."""

        key = (name, repr(sorted(options.items())), repr(base))
        if key not in cls._cache:
            data, point, own = cls.case(name)
            base = own if base is None else base
            seed = select.nearest_facet(read_stl(data), point)
            selection = {"ops": [{"op": "grow", "seed_facet": seed}]}
            started = time.perf_counter()
            result = fit.fit_route({"selection": selection, "base": base, "options": options}, data)
            cls._cache[key] = (data, selection, result, time.perf_counter() - started)
        return cls._cache[key]


def _shapes(result: dict) -> list:
    return [(p["metrics"]["rows"], p["metrics"]["columns"], p["metrics"]["taxels"]) for p in result["proposals"]]


# containment board explicitly: the whole stack on the surface (P4's search; phase P5e makes field-only the default).
FILL = {"shape": "fill", "containment": "board"}
# The right-triangle plate's fill proposals (rows, columns, taxels).
RIGHT_TRIANGLE_FILL = [(24, 26, 325), (23, 26, 324), (22, 26, 322), (21, 26, 319), (20, 26, 315)]


class ReaderTests(unittest.TestCase):
    def test_reader_choices_and_the_flexitac_alias(self) -> None:
        self.assertEqual(fit.parse_options({})["reader"], "none")
        for value in reader_module.READER_CHOICES:
            self.assertEqual(fit.parse_options({"reader": value})["reader"], value)
        self.assertEqual(fit.parse_options({"reader": "flexitac"})["reader"], "32x16")
        with self.assertRaises(SurfaceError) as raised:
            fit.parse_options({"reader": "64x64"})
        self.assertEqual(raised.exception.message, "options.reader must be one of none, auto, 16x16, 32x16, 32x32, 48x48.")

    def test_the_legacy_connector_option_is_a_reader(self) -> None:
        # Placements saved before the reader option carry options.connector: they keep mapping.
        self.assertEqual(fit.parse_options({"connector": "flexitac"})["reader"], "32x16")
        self.assertEqual(fit.parse_options({"connector": "channels"})["reader"], "none")
        self.assertNotIn("connector", fit.parse_options({"connector": "flexitac"}))
        self.assertEqual(fit.parse_options({"connector": "flexitac", "reader": "flexitac"})["reader"], "32x16")
        for options in ({"connector": "flexitac", "reader": "16x16"}, {"connector": "sixteen"}, {"connector": None}):
            with self.subTest(options=options):
                with self.assertRaises(SurfaceError) as raised:
                    fit.parse_options(options)
                self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")

    def test_the_tails_are_sized_to_the_reader(self) -> None:
        cases = {
            ("16x16", 10, 12): {"row_pins": 16, "column_pins": 16},
            ("32x16", 10, 20): {"row_pins": 16, "column_pins": 32},
            ("32x16", 20, 10): {"row_pins": 32, "column_pins": 16},
            ("flexitac", 16, 32): {"row_pins": 16, "column_pins": 32},
            ("32x32", 30, 5): {"row_pins": 32, "column_pins": 32},
            ("48x48", 40, 48): {"row_pins": 48, "column_pins": 48},
            ("none", 40, 48): {"row_pins": None, "column_pins": None},
            ("channels", 4, 4): {"row_pins": None, "column_pins": None},
        }
        for (reader, rows, columns), expected in cases.items():
            with self.subTest(reader=reader, rows=rows, columns=columns):
                self.assertEqual(fit.connector_for(rows, columns, reader), expected)
        # A readout the reader cannot take is dropped with the reader's name.
        self.assertEqual(reader_module.rejection(17, 3, "16x16"), "more lines than the 16 x 16 reader")
        self.assertEqual(reader_module.rejection(20, 20, "32x16"), "more lines than the FlexiTac reader (16 + 32)")
        self.assertEqual(reader_module.rejection(49, 2, "auto"), "more lines than the largest reader (48 x 48)")
        self.assertIsNone(reader_module.rejection(64, 64, "none"))

    def test_auto_takes_the_smallest_reader_that_holds_the_readout(self) -> None:
        expected = {(10, 10): "16x16", (16, 16): "16x16", (10, 20): "32x16", (20, 10): "32x16", (20, 20): "32x32",
                    (32, 32): "32x32", (40, 20): "48x48", (48, 48): "48x48", (49, 3): None}
        for (rows, columns), name in expected.items():
            with self.subTest(rows=rows, columns=columns):
                self.assertEqual(reader_module.choose(rows, columns, "auto"), name)
        self.assertEqual(fit.connector_for(20, 20, "auto"), {"row_pins": 32, "column_pins": 32})

    def test_reader_lines_and_the_frame_index_follow_the_reader(self) -> None:
        # Square readers: the Row lines are sensed (FPC1), the Column lines driven (FPC2).
        self.assertEqual(reader_module.lines("32x32", 3, 5, 32), {"sense_line": "SR3", "drive_line": "SC5", "sense_connector": "FPC1 (32-pin)",
                                                                 "drive_connector": "FPC2 (32-pin)", "frame_index": 4 * 32 + 2})
        self.assertEqual(reader_module.lines("48x48", 48, 48, 48)["frame_index"], 48 * 48 - 1)
        self.assertEqual(reader_module.lines("16x16", 16, 1, 16)["frame_index"], 15)
        # The FlexiTac (32x16) is the map's reader_lines of before, either electrode set on the 16-pin tail.
        for row_pins, column_pins, row_pin, column_pin in ((16, 32, 3, 30), (32, 16, 30, 3)):
            pins = {"row_pins": row_pins, "column_pins": column_pins}
            self.assertEqual(reader_module.lines("32x16", row_pin, column_pin, row_pins), place.reader_lines(row_pin, column_pin, pins))
        self.assertEqual(reader_module.lines("32x16", 3, 30, 16)["frame_index"], 29 * 16 + 2)
        # Which reader a design's tails fit, for the fit option the placement carries.
        self.assertEqual(reader_module.of_design("none", 16, 32), "32x16")
        self.assertIsNone(reader_module.of_design("none", 16, 16))
        self.assertEqual(reader_module.of_design("auto", 48, 48), "48x48")
        self.assertEqual(reader_module.of_design("auto", 32, 16), "32x16")
        self.assertIsNone(reader_module.of_design("16x16", 16, 32))
        self.assertEqual(reader_module.summary("32x32", 32)["frame_index"], "(SC - 1) x 32 + (SR - 1)")

    def test_a_square_reader_is_reported_in_the_metrics_and_the_map(self) -> None:
        data, selection, result, _ = _Fits.get("soft_finger", {"reader": "16x16", "pitch_mm": 3.0, "rotation": "none", "proposals": 2})
        proposal = result["proposals"][0]
        self.assertEqual(proposal["metrics"]["reader"], "16x16")
        self.assertEqual(proposal["design"]["connector"], {"row_pins": 16, "column_pins": 16})
        self.assertLessEqual(max(proposal["metrics"]["rows"], proposal["metrics"]["columns"]), 16)
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        self.assertTrue(mapped["ok"])
        self.assertEqual(mapped["reader"]["name"], "16x16")
        self.assertEqual(mapped["reader"]["sense_board"], "row")
        indices = [t["reader"]["frame_index"] for t in mapped["taxels"]]
        self.assertEqual(len(indices), len(set(indices)))
        self.assertTrue(all(0 <= i < 256 for i in indices))
        first = next(t for t in mapped["taxels"] if (t["row"], t["column"]) == (1, 1))
        self.assertEqual(first["reader"]["frame_index"], (first["column_pin"] - 1) * 16 + first["row_pin"] - 1)
        # Without a reader the map reports none (and, as before, no lines unless the tails are 16 and 32 pins).
        data, selection, result, _ = _Fits.get("soft_finger", {"pitch_mm": 3.0, "rotation": "none", "proposals": 2})
        unread = place.map_route({"selection": selection, "placement": result["proposals"][0]["placement"], "design": result["proposals"][0]["design"]}, data)
        self.assertIsNone(unread["reader"])
        self.assertIsNone(result["proposals"][0]["metrics"]["reader"])


    def test_a_named_reader_caps_the_masked_walk_at_its_lines(self) -> None:
        self.assertEqual(reader_module.walk_caps("none", 32, 32), [(32, 32)])
        self.assertEqual(reader_module.walk_caps("auto", 32, 20), [(32, 20)])
        self.assertEqual(reader_module.walk_caps("16x16", 32, 32), [(16, 16)])
        self.assertEqual(reader_module.walk_caps("32x16", 32, 32), [(16, 32), (32, 16)])
        self.assertEqual(reader_module.walk_caps("32x16", 10, 32), [(10, 32)])  # (10, 16) lies within (10, 32)
        self.assertEqual(reader_module.walk_caps("48x48", 32, 32), [(32, 32)])
        # The review's case: reader 16x16 found 193 (a turned 16 x 16) where max_rows/max_columns 16 find 235.
        # Both are 16 x 16 readouts with 16-pin tails, so the reader finds what the caps find.
        # (P4's search: containment board.)
        read = _Fits.get("right_triangle", {"reader": "16x16", "proposals": 1, "containment": "board"})[2]["proposals"][0]
        capped = _Fits.get("right_triangle", {"max_rows": 16, "max_columns": 16, "proposals": 1, "containment": "board"})[2]["proposals"][0]
        self.assertEqual(_shapes({"proposals": [read]}), [(16, 16, 235)])
        self.assertEqual(_shapes({"proposals": [capped]}), [(16, 16, 235)])
        # The same mask at the same place (the tails differ: the reader's 16-pin connectors, or one contact per line).
        self.assertEqual(read["design"]["matrix"], capped["design"]["matrix"])
        self.assertEqual(read["placement"]["field_origin_base"], capped["placement"]["field_origin_base"])
        self.assertEqual((read["metrics"]["reader"], capped["metrics"]["reader"]), ("16x16", None))

    def test_the_metrics_and_the_map_name_the_same_reader(self) -> None:
        # With reader none, a 16 x 32 readout has tails of 16 and 32 pins: the map reads them as the FlexiTac
        # (as before the reader option), and so does the proposal.  The fit leaves by the plate's 90 mm side 0: since
        # P5-diagonal-bus.md section 23 the caps no longer choose the exit, and without them the narrow tip takes a
        # 60 mm side, where 16 rows take 29 columns.
        self.assertEqual(reader_module.of_readout(16, 32, "none"), "32x16")
        self.assertEqual(reader_module.of_readout(32, 16, "none"), "32x16")
        self.assertIsNone(reader_module.of_readout(16, 31, "none"))
        self.assertIsNone(reader_module.of_readout(16, 16, "none"))
        for rows, columns in ((10, 10), (16, 16), (10, 20), (20, 20), (40, 20), (49, 3)):
            for option in ("auto", "16x16", "32x16", "32x32", "48x48"):
                with self.subTest(rows=rows, columns=columns, option=option):
                    self.assertEqual(reader_module.of_readout(rows, columns, option), reader_module.choose(rows, columns, option))
        data, selection, result, _ = _Fits.get("wide_plate", {"max_rows": 16, "max_columns": 32, "rotation": "none", "proposals": 1},
                                               {"side": 0})
        self.assertEqual(next(base["chord_mm"] for base in result["bases"] if base["side"] == 0), 90.0)
        proposal = result["proposals"][0]
        self.assertEqual((proposal["metrics"]["rows"], proposal["metrics"]["columns"]), (16, 32))
        self.assertEqual(proposal["design"]["connector"], {"row_pins": None, "column_pins": None})
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        self.assertEqual(proposal["metrics"]["reader"], "32x16")
        self.assertEqual(mapped["reader"]["name"], proposal["metrics"]["reader"])


class _Chart:
    def __init__(self, outline: list) -> None:
        self._outline = outline

    def outline(self) -> list:
        return list(self._outline)


class FreeSpaceTests(unittest.TestCase):
    """The fill search's exact free space against the realize's exact containment check."""

    OUTLINE = [(0.0, 0.0), (60.0, 0.0), (60.0, 25.0), (35.0, 25.0), (35.0, 45.0), (10.0, 50.0), (0.0, 30.0)]
    OBSTACLES = {
        "holes": [[(40.0, 5.0), (46.0, 5.0), (46.0, 11.0), (40.0, 11.0)]],
        "strained": [[(15.0, 35.0), (20.0, 35.0), (17.5, 40.0)]],
        "covered": [],
        "bends": [((5.0, 15.0), (25.0, 20.0), 1.0)],
    }

    def _space(self, margin: float = 0.0) -> tuple:
        frame = fit.BaseFrame({"from_uv": [0.0, 0.0], "to_uv": [60.0, 0.0], "inward_uv": [0.0, 1.0]})
        return fill.FreeSpace(_Chart(self.OUTLINE), frame, self.OBSTACLES, margin, [0]), frame

    def _walls(self) -> list:
        polygons = [self.OUTLINE, *self.OBSTACLES["holes"], *self.OBSTACLES["strained"]]
        walls = [(p[k - 1], p[k]) for p in polygons for k in range(len(p))]
        return walls + [(a, b) for a, b, _ in self.OBSTACLES["bends"]]

    def test_random_rectangles_agree_with_check_containment(self) -> None:
        space, frame = self._space()
        walls = self._walls()
        rng = random.Random(4)
        agree = checked = 0
        for _ in range(2500):
            x0, y0 = rng.uniform(-5.0, 62.0), rng.uniform(-5.0, 52.0)
            x1, y1 = x0 + rng.uniform(0.3, 14.0), y0 + rng.uniform(0.3, 14.0)
            square = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            centre = ((x0 + x1) / 2, (y0 + y1) / 2)
            # Within an obstacle with no edge across the rectangle is left out (the realize never meets it: the
            # search keeps every board off the obstacles' interiors), and so is anything within 2e-4 of a wall
            # (the free space keeps the rectangle fit's 1e-4 inset).
            if any(point_in_polygon(centre, polygon) for polygon in [*self.OBSTACLES["holes"], *self.OBSTACLES["strained"]]):
                continue
            if min(segment_distance(square[k - 1], square[k], a, b) for k in range(4) for a, b in walls) < 2e-4:
                continue
            exact = fit.check_containment({"row": square, "column": square}, space, frame, None, self.OBSTACLES, 0.0,
                                          tail_roots={"row": -1e9, "column": -1e9}) is not None
            checked += 1
            agree += exact == space.rect_free(x0, x1, y0, y1)
        self.assertEqual(agree, checked)
        self.assertGreater(checked, 1200)

    def test_with_an_edge_margin_a_free_rectangle_keeps_it(self) -> None:
        space, frame = self._space(1.5)
        rng = random.Random(9)
        free = 0
        for _ in range(800):
            x0, y0 = rng.uniform(-2.0, 60.0), rng.uniform(-2.0, 50.0)
            x1, y1 = x0 + rng.uniform(0.3, 10.0), y0 + rng.uniform(0.3, 10.0)
            if space.rect_free(x0, x1, y0, y1):
                free += 1
                square = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
                self.assertIsNotNone(fit.check_containment({"row": square, "column": square}, space, frame, None, self.OBSTACLES, 1.5,
                                                           tail_roots={"row": -1e9, "column": -1e9}), square)
        self.assertGreater(free, 100)

    def test_a_tail_crosses_the_exit_only(self) -> None:
        space, _ = self._space()
        self.assertAlmostEqual(space.tail_exit(20.0, 30.0, 12.0, 60.0), 0.0)
        self.assertIsNone(space.tail_exit(55.0, 61.0, 12.0, 60.0))  # beyond the exit's end
        self.assertIsNone(space.tail_exit(38.0, 42.0, 12.0, 60.0))  # across the hole
        self.assertIsNone(space.tail_exit(20.0, 30.0, 12.0, 11.0))  # longer than the cap on the surface
        self.assertIsNone(space.tail_exit(4.0, 8.0, 20.0, 60.0))  # across the bend


class FillFitTests(unittest.TestCase):
    def _check_proposals(self, name: str, options: dict) -> list:
        data, selection, result, _ = _Fits.get(name, options)
        masked = []
        for proposal in result["proposals"]:
            metrics = proposal["metrics"]
            with self.subTest(fixture=name, proposal=proposal["rank"]):
                generated = generate_design(proposal["design"])
                self.assertTrue(generated["ok"], generated["validation"]["errors"][:3])
                self.assertEqual(generated["manifest"]["build_id"], proposal["build_id"])
                self.assertTrue(all(board["verification"]["all_checks_passed"] for board in generated["boards"].values()))
                mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
                self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
                self.assertEqual(mapped["taxel_count"], metrics["taxels"])
                self.assertEqual(metrics["positions"], metrics["rows"] * metrics["columns"])
                self.assertEqual(metrics["sampled"], round(metrics["taxels"] / metrics["positions"], 6))
                mask = design_mask(proposal["design"])
                if mask is None:
                    self.assertEqual(metrics["taxels"], metrics["positions"])
                    self.assertIsNone(metrics["mask_class"])
                    continue
                masked.append(proposal)
                # The rectangles' caps (section 21; 32 x 32 before).
                self.assertLessEqual(max(metrics["rows"], metrics["columns"]), fit.MAX_ROWS)
                active = 0
                for first, last in mask:
                    active += last - first + 1
                self.assertEqual(metrics["taxels"], active)
                self.assertLess(active, metrics["positions"])
                self.assertEqual(metrics["mask_class"], {"row": "straight", "column": "straight"})
                self.assertEqual(mapped["readout"]["active"], active)
                self.assertEqual(next(r for r in mapped["verification"] if r["rule"] == "taxel_mask_matches_design")["measured"], 0)
                self.assertEqual(mapped["wrap_svg"].count("<circle"), active)
                # The field outline is P, not the bounding rectangle: its area over the chart's is the coverage.
                frame = fit.BaseFrame({"from_uv": proposal["placement"]["base_from_uv"], "to_uv": proposal["placement"]["base_to_uv"],
                                       "inward_uv": proposal["placement"]["base_inward_uv"]}, proposal["placement"]["base_angle_deg"])
                field = [frame.to_base(p) for p in proposal["outlines_uv"]["field"]]
                self.assertGreater(len(field), 4)
                area = result["selection"]["area_mm2"]
                self.assertAlmostEqual(fill.polygon_area(field) / area, metrics["field_coverage"], places=5)
                self.assertLess(fill.polygon_area(field), metrics["field_mm"][0] * metrics["field_mm"][1] - 1.0)
        return masked

    def test_the_right_triangle_plate(self) -> None:
        # The rectangle: 182 taxels (13 x 14; shape rectangle's first before section 26.16).  A staircase triangle with
        # the lane taper on its channel side; one mask per readout, each with fewer Row lines than the ones before.
        _, _, result, _ = _Fits.get("right_triangle", FILL)
        self.assertEqual(_shapes(result), RIGHT_TRIANGLE_FILL)
        masked = self._check_proposals("right_triangle", FILL)
        self.assertEqual(len(masked), 5)

    def test_the_equilateral_and_disk_plates(self) -> None:
        # Today: 156 (12 x 13) and 228 (19 x 12).  The disk's best is turned 10 degrees against its arc exit.
        _, _, equilateral, _ = _Fits.get("equilateral", FILL)
        self.assertEqual(_shapes(equilateral)[0], (14, 18, 196))
        _, _, disk, _ = _Fits.get("disk", FILL)
        self.assertEqual(_shapes(disk)[0], (16, 17, 261))
        self.assertEqual(disk["proposals"][0]["placement"]["base_angle_deg"], -10.0)
        self.assertEqual(len(self._check_proposals("equilateral", FILL)), 5)
        self.assertEqual(len(self._check_proposals("disk", FILL)), 5)

    def test_the_crank_tip_pad(self) -> None:
        if not CRANK.exists():
            self.skipTest("asset/ meshes are not committed")
        # Today's rectangle: 306 (17 x 18); the straight class fills the right-angled pad.  Capped at 32 x 32 (until
        # section 21) it took 549 of 30 x 32, then 548, 545, 541 and the rectangle; with the rectangles' caps 549 of
        # 30 x 33 and four more masks, each trading a taxel or a few for fewer lines.
        _, _, result, _ = _Fits.get("crank", FILL)
        self.assertEqual(_shapes(result), [(30, 33, 549), (29, 33, 548), (30, 32, 546), (28, 33, 546), (29, 32, 543)])
        self.assertEqual(len(self._check_proposals("crank", FILL)), 5)

    def test_the_soft_finger_masks_its_taper_and_32_rows(self) -> None:
        # Masked fields stopped at 32 rows, so through the mount end the 44 x 8 rectangle (352) stayed first.  With the
        # rectangles' caps (section 21, coverage first) the lane taper takes the face's width over 50 rows: 470 of
        # 50 x 12, the rectangle (the raster search's best, shape rectangle's first before section 26.16) fifth.
        _, _, result, _ = _Fits.get("soft_finger", FILL)
        self.assertEqual(_shapes(result), [(50, 12, 470), (49, 12, 469), (50, 11, 450), (43, 12, 420), (44, 8, 352)])
        self.assertEqual(len(self._check_proposals("soft_finger", FILL)), 4)
        # Within 32 rows the lane taper takes columns the rectangle cannot: 334 against 32 x 9 (the rectangle third).
        _, _, capped, _ = _Fits.get("soft_finger", dict(FILL, max_rows=32))
        self.assertEqual(_shapes(capped), [(32, 12, 334), (32, 11, 316), (32, 9, 288), (31, 9, 279), (30, 9, 270)])
        self.assertEqual(len(self._check_proposals("soft_finger", dict(FILL, max_rows=32))), 2)

    def test_a_full_mask_keeps_the_rectangle_build_id(self) -> None:
        options = fit.parse_options(FILL)
        rectangle = fit.design_for(10, 12, 2.0, 2.0, options, "rows_top", "tight", (20.0, 20.0))
        full = fit.design_for(10, 12, 2.0, 2.0, options, "rows_top", "tight", (20.0, 20.0), mask=[(1, 12)] * 10)
        self.assertEqual(generate_design(full)["manifest"]["build_id"], generate_design(rectangle)["manifest"]["build_id"])
        self.assertEqual(fill.proposal_shape(10, 12, 120, None), (10, 12, False))

    def test_the_fill_fit_is_deterministic(self) -> None:
        data, selection, first, _ = _Fits.get("right_triangle", FILL)
        again = fit.fit_route({"selection": selection, "base": "auto", "options": FILL}, data)
        self.assertEqual([p["build_id"] for p in again["proposals"]], [p["build_id"] for p in first["proposals"]])
        self.assertEqual([p["placement"] for p in again["proposals"]], [p["placement"] for p in first["proposals"]])
        self.assertEqual([p["outlines_uv"] for p in again["proposals"]], [p["outlines_uv"] for p in first["proposals"]])

    def test_the_masked_stack_extent_slides_the_row_tail_with_the_taper(self) -> None:
        options = fit.parse_options(FILL)
        profile = fit.load_profile_cached("surface")
        rows, columns = 24, 26
        # Every ROW_k as long as the lane taper allows (a breakpoint between W_1 and W_1 + pitch).
        model = fill.taper(2.0, options, "tight", profile, rows)
        taus = model["taus"][len(model["breakpoints"]) // 2]
        self.assertGreater(taus[-1], 0)
        mask = [(1, columns - tau) for tau in taus]
        rectangle = fit.stack_extent(fit.design_for(rows, columns, 2.0, 2.0, options, "columns_top", "tight"), profile)
        masked = fit.stack_extent(fit.design_for(rows, columns, 2.0, 2.0, options, "columns_top", "tight", mask=mask), profile)
        # columns_top: the Row board is the bottom one, its channel on the left; the masked field starts closer to its edge.
        slide = rectangle["row_tail_x"][0] - masked["row_tail_x"][0]
        self.assertLess(masked["row_tail_x"][0], 0.0)
        self.assertGreater(-slide, 0.0)
        self.assertAlmostEqual(-slide, model["widths"][-1] - model["starts"][len(model["breakpoints"]) // 2][-1], places=6)
        self.assertEqual(masked["column_tail_x"], rectangle["column_tail_x"])
        self.assertEqual((masked["row_root"], masked["column_root"]), (rectangle["row_root"], rectangle["column_root"]))

    def test_a_candidate_off_the_surface_is_peeled_and_ranked_again(self) -> None:
        data, selection, result, _ = _Fits.get("right_triangle", FILL)
        mesh = read_stl(data)
        facets, chart = fit.api_module.selection_chart(mesh, selection)
        options = fit.parse_options(FILL)
        profile = fit.load_profile_cached("surface")
        obstacles = fit.surface_obstacles(mesh, chart, options)
        sides = fit.api_module.boundary_sides(mesh, chart)
        candidates, _ = fill.masked_candidates(chart, fit.choose_bases("auto", sides, mesh, chart), options, profile, obstacles, [], [])
        best = candidates[0]
        self.assertEqual(fill.realize_masked(best, chart, obstacles, options, profile, None, {})[0]["metrics"]["taxels"], best["taxels"])
        # Moved 1.2 mm toward its far side, the field's staircase leaves the triangle's hypotenuse.
        mirrored = best["lattice"]["side"] == "right"
        moved = dict(best, field_origin=(best["field_origin"][0] + (-1.2 if mirrored else 1.2), best["field_origin"][1]))
        rejected: dict = {}
        current, rounds = moved, 0
        while True:
            proposal, peeled = fill.realize_masked(current, chart, obstacles, options, profile, None, rejected)
            if peeled is None:
                break
            self.assertLess(peeled["taxels"], current["taxels"])
            self.assertGreater(peeled["rank"], current["rank"])
            self.assertEqual(peeled["peels"], rounds + 1)
            current, rounds = peeled, rounds + 1
        self.assertGreaterEqual(rounds, 1)
        self.assertLessEqual(rounds, fill.PEEL_RETRIES)
        if proposal is not None:
            self.assertLess(proposal["metrics"]["taxels"], best["taxels"])
        # The peel: a point beyond the far end of a row trims that row (and the rows above it recede).
        spans = best["spans"]
        row = len(spans) // 2
        pitch, width = best["pitch_x"], best["lattice"]["width"]
        far = spans[row][1] * pitch + width + 0.3
        aw = (best["columns"] - 1) * pitch + width
        y = (best["rows"] - row - 1) * pitch + width / 2
        point = (best["field_origin"][0] + (aw - far if mirrored else far), best["field_origin"][1] + y)
        trimmed = fill.peel(best, point, profile)
        self.assertEqual(trimmed["spans"][row], (spans[row][0], spans[row][1] - 1))
        self.assertTrue(all(trimmed["spans"][j][1] <= spans[row][1] - 1 for j in range(row)))
        self.assertEqual(trimmed["spans"][row + 1:], spans[row + 1:])
        self.assertIsNone(fill.peel(best, (best["field_origin"][0], best["field_origin"][1] - 3.0), profile))

    def test_one_mask_per_readout_and_no_proposal_an_earlier_one_dominates(self) -> None:
        names = ["right_triangle", "equilateral", "disk"] + (["crank"] if CRANK.exists() else [])
        for name in names:
            with self.subTest(fixture=name):
                _, _, result, _ = _Fits.get(name, FILL)
                keys = [(p["metrics"]["rows"], p["metrics"]["columns"], design_mask(p["design"]) is not None) for p in result["proposals"]]
                self.assertEqual(len(keys), len(set(keys)))
                counts = [p["metrics"]["taxels"] for p in result["proposals"]]
                self.assertEqual(counts, sorted(counts, reverse=True))
                # The review's case: 325 of 25 x 26 after 325 of 24 x 26 (one more Row line, nothing gained).
                for later, proposal in enumerate(result["proposals"]):
                    m = proposal["metrics"]
                    for earlier in result["proposals"][:later]:
                        e = earlier["metrics"]
                        self.assertFalse(e["taxels"] >= m["taxels"] and e["rows"] <= m["rows"] and e["columns"] <= m["columns"],
                                         (e["rows"], e["columns"], e["taxels"], m["rows"], m["columns"], m["taxels"]))
        self.assertTrue(fill.dominated(25, 26, 325, [{"metrics": {"rows": 24, "columns": 26, "taxels": 325}}]))
        self.assertFalse(fill.dominated(23, 26, 324, [{"metrics": {"rows": 24, "columns": 26, "taxels": 325}}]))
        self.assertFalse(fill.dominated(24, 26, 326, [{"metrics": {"rows": 24, "columns": 26, "taxels": 325}}]))

    def test_the_placement_option_does_not_change_the_count(self) -> None:
        # The review's case: on the holed plate the masked search found 330 (18 x 29) placed far but 305 (27 x 19)
        # near or centred, as its lattice phases came from the rectangles placed by the option.
        counts, heights = {}, {}
        for placement in ("far", "near", "center"):
            proposal = _Fits.get("holed_plate", {"placement": placement, "proposals": 1, "containment": "board"})[2]["proposals"][0]
            counts[placement] = _shapes({"proposals": [proposal]})[0]
            heights[placement] = proposal["placement"]["field_origin_base"][1]
        self.assertEqual(counts, {"far": (18, 29, 330), "near": (18, 29, 330), "center": (18, 29, 330)})
        # The mask keeps its highest and its lowest field: near takes the lower one.
        self.assertLess(heights["near"], heights["far"])

    def test_with_role_mapping_auto_each_role_is_searched_as_alone(self) -> None:
        # Each role prunes on its own masks, takes its own phases, turned exits, fine frames and lattices of the
        # other routing: auto's candidates of a role are exactly those of that role alone (on the holed plate the
        # two roles' best frames differ).
        data, point, _ = _Fits.case("holed_plate")
        mesh = read_stl(data)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, point)}]}
        _, chart = fit.api_module.selection_chart(mesh, selection)
        bases = fit.choose_bases("auto", fit.api_module.boundary_sides(mesh, chart), mesh, chart)
        profile = fit.load_profile_cached("surface")

        def pool(role_mapping: str) -> dict:
            options = fit.parse_options({"role_mapping": role_mapping, "rotation": "none"})
            obstacles = fit.surface_obstacles(mesh, chart, options)
            found, _ = fill.masked_candidates(chart, bases, options, profile, obstacles, [], [])
            by_role: dict = {}
            for candidate in sorted(found, key=fill.search_rank):
                by_role.setdefault(candidate["role"], []).append((candidate["rows"], candidate["columns"], candidate["digest"], candidate["routing"],
                                                                  tuple(round(v, 6) for v in candidate["field_origin"])))
            return by_role

        both = pool("auto")
        for role in ("rows_top", "columns_top"):
            with self.subTest(role=role):
                alone = pool(role)
                self.assertEqual(list(alone), [role])
                self.assertGreater(len(alone[role]), 10)
                self.assertEqual(both[role], alone[role])
        # A role's pruning threshold counts its own masks only, and a mask keeps its highest and its lowest field.
        pool_ = fill._Pool(3)
        for k in range(4):
            pool_.add({"role": "rows_top", "rows": 5, "columns": 5 + k, "digest": str(k), "routing": "tight", "taxels": 20 + k, "rank": (k,),
                       "field_origin": (0.0, 1.0)})
        self.assertEqual((pool_.threshold("rows_top"), pool_.threshold("columns_top")), (21, 0))
        for y in (2.0, 0.5, 1.5):
            pool_.add({"role": "rows_top", "rows": 5, "columns": 5, "digest": "0", "routing": "tight", "taxels": 20, "rank": (9,), "field_origin": (0.0, y)})
        self.assertEqual([item["field_origin"][1] for item in pool_.items["rows_top"][(5, 5, "0", "tight")]], [2.0, 0.5])
        self.assertEqual(pool_.threshold("rows_top"), 21)

    def test_role_mapping_auto_finds_what_either_role_finds(self) -> None:
        # The review's case: on a wide ellipse auto found 270 (25 x 12), rows_top or columns_top alone 272 (26 x 12).
        found = {}
        for role in ("auto", "rows_top", "columns_top"):
            found[role] = _shapes(_Fits.get("wide_ellipse", {"role_mapping": role, "proposals": 1, "containment": "board"})[2])[0]
        self.assertEqual(found["rows_top"], (26, 12, 272))
        self.assertEqual(found["columns_top"], (26, 12, 272))
        self.assertGreaterEqual(found["auto"][2], max(found["rows_top"][2], found["columns_top"][2]))


class RecedingFieldTests(unittest.TestCase):
    def test_the_row_lanes_follow_the_disk_and_the_wide_ellipse_inward(self) -> None:
        # The default field fits (field containment, proposal 1) with both and left: the stacked Column copper is no
        # keep-out of the Row lanes and they follow the receding field inward to its bottom edge, so no lane leaves flat
        # and every Row trace beside the field lies within a few millimetres of a Row electrode (our own measure,
        # tests/test_diagonal_bus.py's _stray_from_field; measured 3.85 and 6.15 mm on the disk, 3.80 and 5.27 mm on the
        # wide ellipse, whose left side does not recede (with the corner tolerance, P5-diagonal-bus.md section 16, its
        # field of 472 taxels 3.61 and 5.56 mm, the disk's of 440 3.85 and 5.85); diagonal-bus/4's first build 11.42,
        # 13.76, 15.94 and 5.26 mm,
        # its lanes straight down the disk's widest rows and across the raised Column stubs).  The outline over the field
        # is the shared one: below the widest rows it keeps the Column board's own body (its traces drop straight down
        # beside the receding rows), so construction.row_bus.band_mm stays 20 mm on the disk, 40 mm on the ellipse.
        # Since shaped fields take the rectangles' caps (section 21) the wide ellipse's field is 503 of 38 x 17 along its
        # long axis, receding at both ends: 38 Row lanes beside it, 19 a side with both (5.14 mm) and 38 on the left
        # (9.39 mm), against 20 before (12 and 24 on the disk); the bounds grow with the lanes.  Since section 22 the
        # ellipse's first field is the symmetric 39 x 17 = 503 on the same arc (5.53 and 9.43 mm), the disk's symmetric 440.
        bounds = {("disk", "both"): 4.0, ("disk", "left"): 6.5, ("wide_ellipse", "both"): 5.75, ("wide_ellipse", "left"): 9.75}
        for (name, sides), bound in sorted(bounds.items()):
            with self.subTest(name=name, sides=sides):
                proposal = _Fits.get(name, {"row_sides": sides, "proposals": 1})[2]["proposals"][0]
                result = generate_design(proposal["design"])
                self.assertTrue(result["ok"], result["validation"]["errors"][:3])
                row = result["boards"]["row"]
                bus = row["construction"]["row_bus"]
                self.assertEqual(bus["flat_lane_rows"], [])
                self.assertLessEqual(_stray_from_field(row), bound)
                self.assertTrue(row["verification"]["registration"]["outlines_coincide_over_field"])


class MaskedMapTests(unittest.TestCase):
    def test_the_map_lists_the_active_crossings_and_checks_them_against_the_mask(self) -> None:
        data, selection, result, _ = _Fits.get("right_triangle", FILL)
        proposal = result["proposals"][0]
        generated = generate_design(proposal["design"])
        taxels = place.taxel_centres(generated)
        mask = design_mask(generated["design"])
        expected = [(row, column) for row, (first, last) in enumerate(mask, start=1) for column in range(first, last + 1)]
        self.assertEqual([(t["row"], t["column"]) for t in taxels], expected)
        self.assertEqual(place.mask_record(generated["design"], taxels)["measured"], 0)
        record = place.mask_record(generated["design"], taxels[1:])
        self.assertEqual((record["measured"], record["passed"]), (1, False))
        # ROW_01 is farthest from the tails; the taxels sit on the pitch.
        rows = {t["row"]: t["y"] for t in taxels}
        self.assertTrue(all(rows[r] > rows[r + 1] for r in range(1, len(mask))))
        self.assertAlmostEqual(rows[1] - rows[2], 2.0, places=6)
        readout = place.readout(generated["design"], len(taxels))
        self.assertEqual((readout["positions"], readout["active"], readout["inactive"]), (len(mask) * generated["design"]["matrix"]["columns"], len(taxels), "always 0"))

    def test_an_edited_mask_does_not_take_the_placement(self) -> None:
        data, selection, result, _ = _Fits.get("right_triangle", FILL)
        proposal = result["proposals"][0]
        edited = copy.deepcopy(proposal["design"])
        first, last = edited["matrix"]["mask"][0]
        self.assertLess(first, last)
        edited["matrix"]["mask"][0] = [first + 1, last]  # ROW_01 one taxel shorter on the far side: still a straight-class mask
        self.assertTrue(generate_design(edited)["ok"])
        with self.assertRaises(SurfaceError) as raised:
            place.map_route({"selection": selection, "placement": proposal["placement"], "design": edited}, data)
        self.assertEqual(raised.exception.code, "E_SURFACE_PLACEMENT_MISMATCH")


class WebClientTests(unittest.TestCase):
    """What the browser sends and shows for a masked field (tools/browser/cad_checks.py runs it)."""

    def setUp(self) -> None:
        self.app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.main = (ROOT / "web" / "cad" / "main.js").read_text(encoding="utf-8")

    def test_generate_posts_the_proposals_mask_with_the_form(self) -> None:
        body = re.search(r"function formBody\(\) \{(.*?)\n  \}", self.app, re.S)
        self.assertIsNotNone(body)
        self.assertIn("const body = payload();", body.group(1))
        self.assertIn("if (state.mask && state.design?.template_id === MASK_TEMPLATE) body.matrix = {mask: state.mask};", body.group(1))
        self.assertIn('const MASK_TEMPLATE = "surface_matrix_v1";', self.app)
        self.assertIn("const payloadText = () => JSON.stringify(formBody());", self.app)
        self.assertIn("    const sent = formBody();\n", self.app)
        apply = re.search(r"async function applyDesign\(design\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertLess(apply.index("setForm(design);"), apply.index("state.mask = design.matrix?.mask ?? null;"))

    def test_a_rows_or_columns_edit_clears_the_mask_and_a_mode_switch_keeps_it(self) -> None:
        edit = re.search(r"function onFormEdit\(target\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn('if (target && ["rows", "columns"].includes(target.id)) clearMask(`${target.id} changed`);', edit)
        clear = re.search(r"function clearMask\(reason\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn("state.mask = null;", clear)
        self.assertIn("Masked field from Gen by Surface cleared", clear)
        # The review's case: CAD -> Rectangular -> CAD dropped the mask, so the unchanged form no longer built the
        # proposal.  The template switch keeps it (formBody sends it on the surface template only) and redraws the note.
        template = re.search(r"function useTemplate\(id, entry\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertNotIn("clearMask(", template)
        self.assertIn("showMaskNote();", template)
        note = re.search(r"function showMaskNote\(\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn("state.design?.template_id !== MASK_TEMPLATE ? `Masked field from Gen by Surface (${shape}) kept for Gen by Surface", note)

    def test_mask_issues_show_in_the_note_with_a_way_back_to_the_full_field(self) -> None:
        # The review's case: a routing edit left a mask the engine cannot route (E_MASK_ROUTING at matrix.mask[8]);
        # the status said "marked in the form" but no control was marked and nothing could drop the mask.
        messages = re.search(r"function applyServerMessages\(validation, text\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn("state.maskIssues = maskIssuesOf(validation);\n    showMaskNote();", messages)
        issues = re.search(r"function maskIssuesOf\(validation\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn(r'.filter(issue => /^matrix\.mask(\[|$)/.test(String(issue.field)))', issues)
        note = re.search(r"function showMaskNote\(\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn('$("maskNote").classList.toggle("is-invalid", issues.some(issue => issue.kind === "error"));', note)
        self.assertIn('$("maskIssues").replaceChildren(', note)
        self.assertIn('$("clearMask").hidden = !mask;', note)
        self.assertIn('$("clearMask").addEventListener("click", () => { clearMask("you chose the full field"); onFormEdit(null); });', self.app)
        self.assertIn("the masked field from Gen by Surface does not fit the changed form", self.app)
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        for element in ('<div class="hint mask-note" id="maskNote" hidden>', '<ul class="mask-issues" id="maskIssues" hidden></ul>',
                        '<button type="button" id="clearMask" hidden>Use the full field</button>'):
            self.assertIn(element, html)

    def test_the_cad_workspace_shows_n_of_r_by_c(self) -> None:
        self.assertIn("return m.taxels < positions ? `${m.taxels} of ${m.rows} × ${m.columns}` : `${m.rows} × ${m.columns}`;", self.main)
        self.assertIn('["Sampled", "cad-opt"]', self.main)
        # The CSV lists every readout position of a masked field only (a diagonal Row bus's full field keeps the plain rows).
        self.assertIn("if (!map.readout || !(map.readout.active < map.readout.positions)) return", self.main)


class DeterminismTests(unittest.TestCase):
    def test_the_fit_code_sums_no_floats_and_iterates_no_sets(self) -> None:
        import inspect

        functions = [value for module in (fill, reader_module) for _, value in sorted(vars(module).items())
                     if inspect.isfunction(value) and value.__module__ == module.__name__]
        functions += [value for _, value in sorted(vars(fill.FreeSpace).items()) if inspect.isfunction(value)]
        functions += [place.masked_taxel_centres, place.mask_record, place.readout, place.reader_record, place.verify]
        self.assertGreater(len(functions), 30)
        for function in functions:
            with self.subTest(function=f"{function.__module__}.{function.__qualname__}"):
                self.assertEqual(_determinism_problems(function), [])


if __name__ == "__main__":
    unittest.main()
