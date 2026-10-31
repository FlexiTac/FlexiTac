"""The masked boards' DRC and registration (``matrix.mask``, masked-field phase P2).

A masked board (``grid_registration.taxel_mask``) keeps the 30 records, and
five of them take their masked semantics (claude/specs/masked-field/PLAN.md):
``active_field_margin`` is measured from the crossing region P, which must
equal the region the electrodes give; ``coverlay_openings_inside_outline``,
``coverlay_bridge`` and ``contact_exposure`` take the polygon field window as
a ring; ``coverlay_opening_to_trace`` is strict (a route is exempt only near
its own contact or electrode).  A masked pair's registration adds the
taxel masks' identity, the crossings of the stacked boards against the mask
and the inactive crossings' separation, and measures each electrode against
its span of the masked grid.  These tests run the plan's corpus, tamper with
generated boards to show that each masked check fails where it must, run
every tail-side and role combination, a seeded property test of random
masks of the straight classes, a 64 x 64 build, and pin the DRC records of
five masked builds.  Unmasked boards keep today's semantics.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import math
import random
import re
import time
import unittest
from pathlib import Path

from engine import check_design, generate_design, load_profile
from engine import drc as engine_drc
from engine import geometry as engine_geometry
from engine.core import _canonical_json
from engine.drc import stack_frame, verify_board, verify_registration
from engine.geometry import rect_bounds

try:
    from geometry_checks import edges, point_in_polygon, point_segment_distance
    from test_mask_layout import _determinism_problems, _straight_mask
except ImportError:  # run as tests.test_mask_drc
    from tests.geometry_checks import edges, point_in_polygon, point_segment_distance
    from tests.test_mask_layout import _determinism_problems, _straight_mask

ROOT = Path(__file__).resolve().parents[1]
SURFACE = "surface_matrix_v1"
PROFILE = load_profile(SURFACE)
TIGHT = {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016}
FINE = {"pitch_x_mm": 0.6, "pitch_y_mm": 0.6, "taxel_width_mm": 0.35, "taxel_height_mm": 0.35}
SPARSE = {"pitch_x_mm": 3.0, "pitch_y_mm": 3.0, "taxel_width_mm": 1.0, "taxel_height_mm": 1.0}
ONE_MM = {"pitch_x_mm": 1.0, "pitch_y_mm": 1.0, "taxel_width_mm": 0.6, "taxel_height_mm": 0.6}
_SIDES = ("bottom", "right", "top", "left")
_OPPOSITE = {"bottom": "top", "top": "bottom", "left": "right", "right": "left"}
EPSILON = 1e-6
# Every masked registration key (docs/LAYOUT_SCHEMA.md, "Registration record").
MASKED_REGISTRATION_KEYS = (
    "taxel_mask_identical", "crossing_set_matches_mask", "wrong_crossing_count",
    "inactive_crossing_separation_mm", "inactive_crossings_separated",
)
# The masked registration's report of trace over trace in the stack (docs/LAYOUT_SCHEMA.md, "Registration record").
TRACE_OVERLAP_KEYS = ("trace_overlap_mm", "trace_overlap_nets", "trace_overlap_pairs", "trace_overlap_area_mm2")
# The strict record's clearance on every generated board of the surface profile: the gang window's corner
# beside the outer contact's tail piece (the finger width and the contact pitch fix it), above the rule.
GANG_CORNER_CLEARANCE = 0.214656


def _request(rows: int, columns: int, matrix=None, **sections) -> dict:
    return {"template_id": SURFACE, "matrix": {"rows": rows, "columns": columns, **(matrix or {})}, **sections}


def _masked_request(request: dict, far) -> dict:
    checked = check_design(request)
    assert checked["ok"], checked["validation"]["errors"][:3]
    mask = _straight_mask(checked["design"], far)
    return dict(request, matrix=dict(request["matrix"], mask=mask))


def _corpus() -> list:
    """(name, masked request): the plan's P2 DRC corpus, all of the straight classes."""

    disk = lambda size: (lambda row: int(math.floor(size * math.sqrt(max(0.0, 1 - ((size - row + 0.5) / size) ** 2)))))
    cases = (
        # ROW_k reaches slot k: one more than the hypotenuse, since the lane taper starts ROW_02 at slot 1.
        ("right triangle 30x29", _request(30, 29), lambda row: row),
        ("right triangle 20x16", _request(20, 16), lambda row: row),
        ("quarter disk 20x20", _request(20, 20), disk(20)),
        ("soft-finger taper 48x12 tight", _request(48, 12, routing=TIGHT), lambda row: 11),
        ("L shape 12x12", _request(12, 12), lambda row: 3 if row <= 6 else 11),
        ("trapezoid 12x20", _request(12, 20), lambda row: 8 + row),
        ("p0.6 tight 16x24", _request(16, 24, FINE, routing=TIGHT), lambda row: 8 + row),
        ("sparse 3 mm 10x12 (per-electrode windows)", _request(10, 12, SPARSE), lambda row: 2 + row),
        ("64x64 at 1 mm", _request(64, 64, ONE_MM, routing=TIGHT), lambda row: row),
    )
    return [(name, _masked_request(request, far)) for name, request, far in cases]


def _rule(board: dict, name: str) -> dict:
    return board["verification"]["checks"][name] if "verification" in board else None


def _check(board: dict, design: dict) -> dict:
    """The DRC records of a (tampered) board."""

    return verify_board(board, PROFILE, design)["measurements"]["checks"]


def _field_window(board: dict) -> dict:
    (window,) = [opening for opening in board["layers"]["top_coverlay_openings"] if opening.get("shape") == "polygon"]
    return window


def _ring_area(ring) -> float:
    return math.fsum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, [*ring[1:], ring[0]])) / 2


class MaskDrcCorpusTests(unittest.TestCase):
    """The plan's corpus: every record and the registration pass, with the masked measurements."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.results = [(name, generate_design(request)) for name, request in _corpus()]

    def test_every_record_and_the_registration_pass(self) -> None:
        for name, result in self.results:
            with self.subTest(case=name):
                self.assertTrue(result["ok"], result["validation"]["errors"][:3])
                self.assertEqual(set(result["boards"]), {"row", "column"})
                for key, board in result["boards"].items():
                    checks = board["verification"]["checks"]
                    self.assertEqual(len(checks), 30, key)
                    self.assertEqual(sorted(rule for rule, record in checks.items() if not record["passed"]), [], key)
                    self.assertTrue(board["verification"]["all_checks_passed"])
                    registration = board["verification"]["registration"]
                    self.assertTrue(registration["passed"])
                    self.assertEqual(registration["wrong_crossing_count"], 0)

    def test_the_masked_measurements(self) -> None:
        for name, result in self.results:
            for key, board in result["boards"].items():
                with self.subTest(case=name, board=key):
                    checks = board["verification"]["checks"]
                    margin = checks["active_field_margin"]
                    # The margin around P is the rule at its closest point, never the bounding box's 0.
                    self.assertEqual((margin["measured_mm"], margin["where"], margin["region"]), (0.5, "active_outline", "taxel_mask"))
                    strict = checks["coverlay_opening_to_trace"]
                    self.assertEqual(strict["semantics"], "strict")
                    self.assertIsNotNone(strict["measured_mm"])
                    self.assertGreaterEqual(strict["measured_mm"], 0.15)
                    self.assertEqual(strict["measured_mm"], GANG_CORNER_CLEARANCE)
                    exposure = checks["contact_exposure"]
                    self.assertEqual(exposure["electrodes"]["measured_mm"], 0.1)  # the coverlay expansion
                    self.assertEqual(exposure["measured_mm"], 0.05)  # the gang window's side beside the outer contacts
                    self.assertGreaterEqual(checks["concave_fillet_radius"]["measured_mm"], 0.498097)
                    self.assertTrue(checks["coverlay_openings_inside_outline"]["passed"])
                    for rule in ("coverlay_openings_inside_outline", "coverlay_bridge"):
                        self.assertNotIn("semantics", checks[rule])

    def test_the_corpus_has_polygon_and_per_electrode_windows(self) -> None:
        kinds = {}
        for name, result in self.results:
            for board in result["boards"].values():
                for opening in board["layers"]["top_coverlay_openings"]:
                    kinds.setdefault((opening["kind"], opening.get("shape", "rectangle")), set()).add(name)
        self.assertIn(("electrode_field_opening", "polygon"), kinds)
        self.assertEqual(kinds[("sensor_electrode_opening", "rectangle")], {"sparse 3 mm 10x12 (per-electrode windows)"})

    def test_the_strict_rule_measures_the_field_window(self) -> None:
        # Without the gang window the strict record measures the field window alone: on p0.6 tight a stub
        # passes its neighbours' windows at pitch - cell / 2 - expansion - trace / 2.
        name, result = next(item for item in self.results if item[0] == "p0.6 tight 16x24")
        expected = round(0.6 - 0.35 / 2 - 0.1 - 0.1016 / 2, 6)
        for key, board in result["boards"].items():
            with self.subTest(board=key):
                board = copy.deepcopy(board)
                board["layers"]["top_coverlay_openings"] = [
                    opening for opening in board["layers"]["top_coverlay_openings"] if opening["kind"] != "connector_contact_opening"
                ]
                record = _check(board, result["design"])["coverlay_opening_to_trace"]
                self.assertEqual(record["measured_mm"], expected)
                self.assertEqual(record["where"][0], "electrode_field_opening")
                self.assertTrue(record["passed"])


class MaskDrcFailureTests(unittest.TestCase):
    """Each masked check fails on a board made wrong on purpose."""

    @classmethod
    def setUpClass(cls) -> None:
        corpus = dict(_corpus())
        cls.triangle = generate_design(corpus["right triangle 20x16"])
        cls.sparse = generate_design(corpus["sparse 3 mm 10x12 (per-electrode windows)"])

    def _board(self, key: str = "row", result=None) -> tuple:
        result = result or self.triangle
        return copy.deepcopy(result["boards"][key]), result["design"]

    def test_a_crossing_region_unlike_the_electrodes_fails(self) -> None:
        board, design = self._board()
        region = board["grid_registration"]["active_region"]
        cx, cy = region["x"] + region["width"] / 2, region["y"] + region["height"] / 2
        # A small square inside the field: far from the outline, but not the electrodes' region.
        board["grid_registration"]["active_outline"] = [[cx - 0.5, cy - 0.5], [cx + 0.5, cy - 0.5], [cx + 0.5, cy + 0.5], [cx - 0.5, cy + 0.5]]
        record = _check(board, design)["active_field_margin"]
        self.assertFalse(record["passed"])
        self.assertEqual(record["where"], "active_outline_mismatch")
        self.assertIsNone(record["measured_mm"])  # no outline edge within the margin and the report reach

    def test_a_crossing_region_too_close_to_the_outline_fails(self) -> None:
        board, design = self._board("column")
        # Grow every electrode and P by 0.05 toward the far end: P stays the electrodes' region, 0.45 from the outline.
        top = max(point[1] for point in board["grid_registration"]["active_outline"])
        board["grid_registration"]["active_outline"] = [[x, y + 0.05 if y == top else y] for x, y in board["grid_registration"]["active_outline"]]
        for electrode in board["layers"]["top_copper"]["electrodes"]:
            if abs(electrode["y"] + electrode["height_mm"] - 0.2 - top) < EPSILON:
                electrode["height_mm"] = round(electrode["height_mm"] + 0.05, 6)
        record = _check(board, design)["active_field_margin"]
        self.assertFalse(record["passed"])
        self.assertAlmostEqual(record["measured_mm"], 0.45, delta=EPSILON)
        self.assertEqual(record["where"], "active_outline")

    def test_a_crossing_region_outside_the_board_fails(self) -> None:
        board, design = self._board()
        # P and the electrodes moved 500 mm off the board together: P is still the electrodes' region and no
        # outline edge is within reach, so only the test that P lies inside the outline fails it.
        board["grid_registration"]["active_outline"] = [[x + 500.0, y] for x, y in board["grid_registration"]["active_outline"]]
        for electrode in board["layers"]["top_copper"]["electrodes"]:
            electrode["x"] = round(electrode["x"] + 500.0, 6)
        record = _check(board, design)["active_field_margin"]
        self.assertFalse(record["passed"])
        self.assertEqual((record["where"], record["violation_count"], record["measured_mm"]), ("active_outline", 1, None))

    def test_an_unsound_polygon_window_fails(self) -> None:
        board, design = self._board()
        ring = _field_window(board)["points"]
        count = len(ring)
        low_y = min(y for _, y in ring)
        start = min((index for index, (_, y) in enumerate(ring) if y == low_y), key=lambda index: ring[index][0])
        a, b = ring[start], ring[(start + 1) % count]  # the bottom edge, left to right (counter-clockwise)
        self.assertEqual(a[1], b[1])
        middle = round((a[0] + b[0]) / 2, 6)
        crossed = [list(point) for point in ring]
        crossed[start], crossed[(start + 1) % count] = crossed[(start + 1) % count], crossed[start]
        cases = {
            # A notch up into the bottom edge: rectilinear and simple, but not orthogonally convex.
            "notch": [*ring[:start + 1], [middle - 0.05, a[1]], [middle - 0.05, a[1] + 0.3], [middle + 0.05, a[1] + 0.3], [middle + 0.05, a[1]], *ring[start + 1:]],
            # The bottom-left corner cut on a diagonal: not rectilinear.
            "diagonal": [*ring[:start], [a[0], round(a[1] + 0.05, 6)], [round(a[0] + 0.05, 6), a[1]], *ring[start + 1:]],
            # The bottom edge's two ends swapped: the ring crosses itself.
            "crossed": crossed,
            # Pushed 0.25 mm toward the far side: it crosses the outline, 0.2 mm beyond it there.
            "outside": [[round(x + 0.25, 6), y] for x, y in ring],
        }
        for name, points in cases.items():
            with self.subTest(case=name):
                tampered = copy.deepcopy(board)
                _field_window(tampered)["points"] = points
                record = _check(tampered, design)["coverlay_openings_inside_outline"]
                self.assertFalse(record["passed"])
                self.assertEqual(record["where"], "electrode_field_opening")
        self.assertTrue(_check(board, design)["coverlay_openings_inside_outline"]["passed"])

    def test_a_polygon_window_may_touch_the_outline(self) -> None:
        # The window keeps 0.2 mm from the outline along the electrodes (overhang 0.2 + expansion 0.1 from P, which
        # keeps 0.5): pushed 0.2 mm that way its far side lies on the outline and passes, as a rectangle's would;
        # 0.25 mm crosses the outline.
        for key, axis in (("row", 0), ("column", 1)):
            board, design = self._board(key)
            outline = board["outline"]["points"]
            ring = _field_window(board)["points"]
            for push, passed in ((0.2, True), (0.25, False)):
                with self.subTest(board=key, push=push):
                    tampered = copy.deepcopy(board)
                    moved = [[round(point[0] + (push if axis == 0 else 0.0), 6), round(point[1] + (push if axis == 1 else 0.0), 6)] for point in ring]
                    _field_window(tampered)["points"] = moved
                    touching = [point for point in moved if any(point_segment_distance(point, a, b) <= EPSILON for a, b in edges(outline))]
                    self.assertEqual(bool(touching), passed)
                    record = _check(tampered, design)["coverlay_openings_inside_outline"]
                    self.assertEqual(record["passed"], passed)

    def test_a_polygon_window_must_keep_clear_of_the_cutouts(self) -> None:
        board, design = self._board("column")
        ring = _field_window(board)["points"]
        left = min(x for x, _ in ring)
        a, b = max(((p, q) for p, q in edges(ring) if p[0] == q[0] == left), key=lambda edge: abs(edge[0][1] - edge[1][1]))
        middle = round((a[1] + b[1]) / 2, 6)
        square = lambda x, size: [[x, middle], [round(x + size, 6), middle], [round(x + size, 6), round(middle + size, 6)], [x, round(middle + size, 6)]]
        for name, cutout, passed in (
            ("inside the window", square(round(left + 0.5, 6), 0.3), False),
            ("across its left side", square(round(left - 0.1, 6), 0.3), False),
            ("between it and the outline", square(round(left - 0.35, 6), 0.2), True),
        ):
            with self.subTest(case=name):
                tampered = copy.deepcopy(board)
                tampered["outline"]["cutouts"] = [cutout]
                self.assertTrue(point_in_polygon(cutout[0], board["outline"]["points"]))
                record = _check(tampered, design)["coverlay_openings_inside_outline"]
                self.assertEqual(record["passed"], passed)

    def test_the_bridge_to_a_polygon_window_follows_its_edges(self) -> None:
        board, design = self._board()
        ring = _field_window(board)["points"]
        # A small rectangular opening in the staircase's empty corner: inside the window's bounding box but
        # 0.6 mm from its nearest edge, then one 0.3 mm from it.
        top = max(y for _, y in ring)
        right = max(x for x, _ in ring)
        corner_y = max(y for x, y in ring if x == right)  # the top of the window's far column
        self.assertLess(corner_y, top - 2.0)
        base = {"kind": "sensor_electrode_opening", "net": "ROW_01", "nets": ["ROW_01"], "opening_for": "row_electrode", "anchor": "lower_left"}
        for gap, passed in ((0.6, True), (0.3, False)):
            with self.subTest(gap=gap):
                tampered = copy.deepcopy(board)
                tampered["layers"]["top_coverlay_openings"].append(dict(base, x=round(right - 0.4, 6), y=round(corner_y + gap, 6), width_mm=0.4, height_mm=0.4))
                record = _check(tampered, design)["coverlay_bridge"]
                self.assertAlmostEqual(record["measured_mm"], gap, delta=EPSILON)
                self.assertEqual(record["passed"], passed)
                self.assertEqual(sorted(record["where"]), ["electrode_field_opening", "sensor_electrode_opening"])

    def test_a_route_beside_or_inside_another_electrodes_window_fails(self) -> None:
        # The field window lists every net, so the unmasked own-net skip would pass both; the strict rule does not.
        for key in ("row", "column"):
            board, design = self._board(key)
            ring = _field_window(board)["points"]
            net = board["layers"]["top_copper"]["electrodes"][0]["net"]
            edges = list(zip(ring, [*ring[1:], ring[0]]))
            # The longest vertical edge on the window's left (lowest x) side.
            left = min(x for x, _ in ring)
            a, b = max((edge for edge in edges if edge[0][0] == edge[1][0] == left), key=lambda edge: abs(edge[0][1] - edge[1][1]))
            low, high = sorted((a[1], b[1]))
            width = 0.1016
            beside = [[round(left - 0.1 - width / 2, 6), round(low + (high - low) / 3, 6)], [round(left - 0.1 - width / 2, 6), round(high - (high - low) / 3, 6)]]
            # A short piece of the smallest electrode's net in the middle of the largest electrode (another
            # net's), deep inside the window: far from every edge, so only the inside test sees it.
            electrodes = sorted(board["layers"]["top_copper"]["electrodes"], key=lambda item: item["width_mm"] * item["height_mm"])
            x0, y0, x1, y1 = rect_bounds(electrodes[-1])
            cx, cy = round((x0 + x1) / 2, 6), round((y0 + y1) / 2, 6)
            inside = [[cx, cy], [round(cx + 0.01, 6), cy]] if key == "row" else [[cx, cy], [cx, round(cy + 0.01, 6)]]
            for name, route_net, points in (("beside", net, beside), ("inside", electrodes[0]["net"], inside)):
                with self.subTest(board=key, case=name):
                    tampered = copy.deepcopy(board)
                    tampered["layers"]["top_copper"]["routes"].append({"net": route_net, "segment": "fanout", "width_mm": width, "points": points})
                    record = _check(tampered, design)["coverlay_opening_to_trace"]
                    self.assertFalse(record["passed"])
                    if name == "beside":
                        self.assertAlmostEqual(record["measured_mm"], 0.1, delta=EPSILON)
                        self.assertEqual(record["where"], ["electrode_field_opening", net])
                    else:
                        self.assertGreaterEqual(record["measured_mm"], 0.15)  # every edge is far: the inside test fails it
                        self.assertEqual(record["violation_count"], 1)

    def test_an_electrode_outside_the_polygon_window_fails(self) -> None:
        board, design = self._board()
        window = _field_window(board)
        ring = window["points"]
        # Pull the window's top-right step 0.15 mm in: the top row's electrode then pokes 0.05 mm out of it,
        # while the window's bounding box still holds it.
        top = max(y for _, y in ring)
        far = max(x for x, y in ring if y == top)
        side = lambda x, y: x == far and y >= top - design["matrix"]["pitch_y_mm"] - EPSILON  # the top band's far side
        self.assertEqual(sum(1 for x, y in ring if side(x, y)), 2)
        window["points"] = [[round(x - 0.15, 6), y] if side(x, y) else [x, y] for x, y in ring]
        self.assertLess(_ring_area(window["points"]), _ring_area(ring))
        record = _check(board, design)["contact_exposure"]
        self.assertFalse(record["passed"])
        self.assertAlmostEqual(record["measured_mm"], -0.05, delta=EPSILON)
        self.assertAlmostEqual(record["electrodes"]["measured_mm"], -0.05, delta=EPSILON)
        self.assertEqual(record["where"], "ROW_01")

    def test_per_electrode_windows_keep_the_rectangle_rules(self) -> None:
        board, design = self._board("row", self.sparse)
        checks = _check(board, design)
        self.assertTrue(all(record["passed"] for record in checks.values()))
        self.assertEqual(checks["contact_exposure"]["electrodes"]["measured_mm"], 0.1)
        # Two neighbouring windows moved to 0.3 mm apart break the bridge rule.
        windows = sorted((opening for opening in board["layers"]["top_coverlay_openings"] if opening["kind"] == "sensor_electrode_opening"), key=lambda item: item["y"])
        lower, upper = windows[0], windows[1]
        upper["y"] = round(lower["y"] + lower["height_mm"] + 0.3, 6)
        record = _check(board, design)["coverlay_bridge"]
        self.assertFalse(record["passed"])
        self.assertAlmostEqual(record["measured_mm"], 0.3, delta=EPSILON)

    def test_unmasked_boards_keep_todays_semantics(self) -> None:
        plain = generate_design(_request(12, 16))
        for board in plain["boards"].values():
            checks = board["verification"]["checks"]
            # The own-net skip: the merged field window and the gang window list every net.
            self.assertIsNone(checks["coverlay_opening_to_trace"]["measured_mm"])
            self.assertEqual(checks["active_field_margin"]["where"], "active_region")
            for rule, key in (("coverlay_opening_to_trace", "semantics"), ("active_field_margin", "region"), ("contact_exposure", "electrodes")):
                self.assertNotIn(key, checks[rule])
            for key in (*MASKED_REGISTRATION_KEYS, *TRACE_OVERLAP_KEYS):
                self.assertNotIn(key, board["verification"]["registration"])


class MaskRegistrationTests(unittest.TestCase):
    """The stacked boards cross exactly at the mask's taxels."""

    def test_every_tail_side_and_role_combination(self) -> None:
        for row_side in _SIDES:
            for column_side in (row_side, _OPPOSITE[row_side]):
                for top in ("rows", "columns"):
                    request = _masked_request(
                        _request(9, 13, tail={"row_side": row_side, "column_side": column_side},
                                 role_mapping={"top": top, "bottom": "columns" if top == "rows" else "rows"}),
                        lambda row: 2 + row,
                    )
                    with self.subTest(row_side=row_side, column_side=column_side, top=top):
                        result = generate_design(request)
                        self.assertTrue(result["ok"], result["validation"]["errors"][:3])
                        registration = result["boards"]["row"]["verification"]["registration"]
                        self.assertEqual(registration, result["boards"]["column"]["verification"]["registration"])
                        self.assertEqual(
                            {key: registration[key] for key in MASKED_REGISTRATION_KEYS},
                            {"taxel_mask_identical": True, "crossing_set_matches_mask": True, "wrong_crossing_count": 0,
                             "inactive_crossing_separation_mm": 0.4, "inactive_crossings_separated": True},
                        )
                        self.assertEqual((registration["row_grid_deviation_mm"], registration["column_grid_deviation_mm"]), (0.0, 0.0))
                        self.assertTrue(registration["passed"])

    def _pair(self, request: dict) -> dict:
        result = generate_design(request)
        self.assertTrue(result["ok"])
        return result

    def test_a_board_built_with_mirrored_spans_is_refused(self) -> None:
        result = self._pair(_masked_request(_request(10, 12), lambda row: 2 + row))
        row_board, column_board = copy.deepcopy(result["boards"]["row"]), result["boards"]["column"]
        region = row_board["grid_registration"]["active_region"]
        mirror = 2 * region["x"] + region["width"]
        for electrode in row_board["layers"]["top_copper"]["electrodes"]:  # each span turned end for end in the field
            electrode["x"] = round(mirror - electrode["x"] - electrode["width_mm"], 6)
        outcome = verify_registration(row_board, column_board, PROFILE)
        record = outcome["measurements"]
        self.assertFalse(record["passed"])
        self.assertFalse(record["row_grid_matches"])
        self.assertTrue(record["column_grid_matches"])
        self.assertGreater(record["row_grid_deviation_mm"], 1.0)
        self.assertGreater(record["wrong_crossing_count"], 0)
        fields = [issue["field"] for issue in outcome["errors"]]
        self.assertEqual(fields, ["boards.row.layers.top_copper.electrodes", "boards.row.grid_registration.taxel_mask"])
        self.assertTrue(all(issue["code"] == "E_REGISTRATION" for issue in outcome["errors"]))
        self.assertIn("ROW_01 x COL_", outcome["errors"][1]["message"])

    def test_an_electrode_longer_than_its_span_is_refused(self) -> None:
        # One more pitch at the far end of the top row: it now overhangs a column that stops below it, so the
        # crossings still match the mask, but the electrode leaves the masked grid.
        result = self._pair(_masked_request(_request(10, 12), lambda row: 2 + row))
        row_board = copy.deepcopy(result["boards"]["row"])
        (top,) = [item for item in row_board["layers"]["top_copper"]["electrodes"] if item["net"] == "ROW_01"]
        top["width_mm"] = round(top["width_mm"] + 2.0, 6)
        record = verify_registration(row_board, result["boards"]["column"], PROFILE)["measurements"]
        self.assertEqual(record["wrong_crossing_count"], 0)
        self.assertAlmostEqual(record["row_grid_deviation_mm"], 2.0, delta=EPSILON)
        self.assertFalse(record["passed"])

    def test_an_electrode_off_the_grid_across_its_length_is_refused(self) -> None:
        # Across its length a masked electrode keeps today's place and width on the taxel grid: moved or widened
        # 0.05 mm, it still crosses exactly the mask's taxels, but leaves the grid.
        result = self._pair(_masked_request(_request(8, 8), lambda row: 1 + row))
        for key, net, field, delta in (
            ("row", "ROW_04", "y", 0.05), ("row", "ROW_04", "height_mm", 0.05), ("column", "COL_03", "x", -0.05), ("column", "COL_03", "width_mm", 0.05),
        ):
            with self.subTest(board=key, change=field):
                boards = {name: copy.deepcopy(board) for name, board in result["boards"].items()}
                (electrode,) = [item for item in boards[key]["layers"]["top_copper"]["electrodes"] if item["net"] == net]
                electrode[field] = round(electrode[field] + delta, 6)
                outcome = verify_registration(boards["row"], boards["column"], PROFILE)
                record = outcome["measurements"]
                self.assertEqual(record["wrong_crossing_count"], 0)
                self.assertAlmostEqual(record[f"{key}_grid_deviation_mm"], 0.05, delta=EPSILON)
                self.assertFalse(record[f"{key}_grid_matches"])
                self.assertFalse(record["passed"])
                self.assertEqual([(issue["code"], issue["field"]) for issue in outcome["errors"]], [("E_REGISTRATION", f"boards.{key}.layers.top_copper.electrodes")])

    def test_different_taxel_masks_are_refused(self) -> None:
        result = self._pair(_masked_request(_request(10, 12), lambda row: 2 + row))
        column_board = copy.deepcopy(result["boards"]["column"])
        column_board["grid_registration"]["taxel_mask"]["row_spans"][0] = [1, 12]
        outcome = verify_registration(result["boards"]["row"], column_board, PROFILE)
        self.assertFalse(outcome["measurements"]["taxel_mask_identical"])
        self.assertFalse(outcome["measurements"]["passed"])
        self.assertEqual([issue["field"] for issue in outcome["errors"]], ["boards.column.grid_registration.taxel_mask"])
        # One masked board beside an unmasked one is refused too.
        del column_board["grid_registration"]["taxel_mask"]
        record = verify_registration(result["boards"]["row"], column_board, PROFILE)["measurements"]
        self.assertFalse(record["taxel_mask_identical"])

    def test_the_inactive_crossings_separation(self) -> None:
        for matrix, expected in ((FINE, 0.05), ({"pitch_x_mm": 2.0, "pitch_y_mm": 2.0, "taxel_width_mm": 1.4, "taxel_height_mm": 1.4}, 0.4)):
            with self.subTest(matrix=matrix):
                result = self._pair(_masked_request(_request(8, 10, matrix, routing=TIGHT), lambda row: 2 + row))
                record = result["boards"]["row"]["verification"]["registration"]
                self.assertEqual(record["inactive_crossing_separation_mm"], expected)
                self.assertTrue(record["inactive_crossings_separated"])

    def test_electrodes_touching_at_an_inactive_crossing_are_refused(self) -> None:
        # ROW_01 lengthened to touch COL_(last + 1)'s side and that column lengthened to touch ROW_01's edge:
        # no crossing (no overlap of positive area), but any misregistration makes one.
        # Bottom tails on one side: ROW_01, the top row, ends at its first COL (its far end, +x on its board);
        # COL_(first - 1), beside it, starts at ROW_02 (its top end, +y on its board, is next to ROW_01).
        result = self._pair(_masked_request(_request(6, 8), lambda row: 1 + row))
        row_board, column_board = copy.deepcopy(result["boards"]["row"]), copy.deepcopy(result["boards"]["column"])
        self.assertEqual((row_board["tail"]["side"], column_board["tail"]["side"]), ("bottom", "bottom"))
        first, _ = row_board["grid_registration"]["taxel_mask"]["row_spans"][0]
        self.assertGreater(first, 1)
        row = next(item for item in row_board["layers"]["top_copper"]["electrodes"] if item["net"] == "ROW_01")
        column = next(item for item in column_board["layers"]["top_copper"]["electrodes"] if item["net"] == f"COL_{first - 1:02d}")
        # The gaps in the stack frame (a turn-over keeps lengths), closed by lengthening both electrodes.
        a = engine_drc._stacked_electrodes(row_board)["ROW_01"]
        b = engine_drc._stacked_electrodes(column_board)[column["net"]]
        gap_x, gap_y = max(b[0] - a[2], a[0] - b[2]), max(b[1] - a[3], a[1] - b[3])
        self.assertGreater(min(gap_x, gap_y), 0.0)
        row["width_mm"] = round(row["width_mm"] + gap_x, 6)
        column["height_mm"] = round(column["height_mm"] + gap_y, 6)
        outcome = verify_registration(row_board, column_board, PROFILE)
        record = outcome["measurements"]
        self.assertEqual(record["wrong_crossing_count"], 0)
        self.assertEqual(record["inactive_crossing_separation_mm"], 0.0)
        self.assertFalse(record["inactive_crossings_separated"])
        self.assertIn("boards.row.grid_registration.taxel_mask", [issue["field"] for issue in outcome["errors"]])

    def test_the_stack_frame(self) -> None:
        result = self._pair(_masked_request(_request(6, 8, role_mapping={"top": "rows", "bottom": "columns"}), lambda row: 1 + row))
        row_board, column_board = result["boards"]["row"], result["boards"]["column"]
        self.assertEqual((row_board["physical_side"], column_board["physical_side"]), ("top", "bottom"))
        def assert_maps(convert, center, expected) -> None:
            point = convert([center[0] + 1.0, center[1] + 2.0])
            self.assertTrue(all(abs(value - target) <= 1e-9 for value, target in zip(point, expected)), (point, expected))

        for board, mirrored in ((row_board, True), (column_board, False)):
            region = board["grid_registration"]["active_region"]
            center = (region["x"] + region["width"] / 2, region["y"] + region["height"] / 2)
            assert_maps(stack_frame(board), center, [-1.0 if mirrored else 1.0, 2.0])
            self.assertEqual(stack_frame(board)(list(center)), [0.0, 0.0])
            # The role mapping, when given, names the top board instead of physical_side.
            assert_maps(stack_frame(board, {"top": "columns", "bottom": "rows"}), center, [1.0 if mirrored else -1.0, 2.0])
        # Left and right tails turn the top board over about y.
        side = generate_design(_masked_request(_request(6, 8, tail={"row_side": "left", "column_side": "left"}, role_mapping={"top": "rows", "bottom": "columns"}), lambda row: 1 + row))
        board = side["boards"]["row"]
        region = board["grid_registration"]["active_region"]
        assert_maps(stack_frame(board), (region["x"] + region["width"] / 2, region["y"] + region["height"] / 2), [1.0, -2.0])


def _stacked_runs(result: dict) -> dict:
    """``{(ROW net, COL net): (length, area)}`` of the axis-parallel trace runs of the stacked boards, measured here.

    Each board is moved to its active region's centre and the physical top board turned over about its tail
    axis; a Row and a Column segment along one axis run on each other where their copper overlaps across them.
    """

    traces = {}
    for key, board in result["boards"].items():
        region = board["grid_registration"]["active_region"]
        cx, cy = region["x"] + region["width"] / 2, region["y"] + region["height"] / 2
        top, across_tail = board["physical_side"] == "top", board["tail"]["side"] in ("bottom", "top")
        sign = (-1.0 if top and across_tail else 1.0, -1.0 if top and not across_tail else 1.0)
        traces[key] = [
            (route["net"], [sign[0] * (a[0] - cx), sign[1] * (a[1] - cy)], [sign[0] * (b[0] - cx), sign[1] * (b[1] - cy)], route["width_mm"] / 2)
            for route in board["layers"]["top_copper"]["routes"]
            for a, b in zip(route["points"], route["points"][1:])
        ]
    runs: dict = {}
    for row_net, a, b, row_radius in traces["row"]:
        for column_net, c, d, column_radius in traces["column"]:
            for axis in (0, 1):
                along = 1 - axis
                if a[axis] != b[axis] or c[axis] != d[axis] or a[along] == b[along] or c[along] == d[along]:
                    continue
                offset = abs(a[axis] - c[axis])
                width = min(row_radius, offset + column_radius) - max(-row_radius, offset - column_radius)
                length = min(max(a[along], b[along]), max(c[along], d[along])) - max(min(a[along], b[along]), min(c[along], d[along]))
                if width > EPSILON and length > EPSILON:
                    total = runs.get((row_net, column_net), ([], []))
                    total[0].append(length)
                    total[1].append(length * width)
                    runs[(row_net, column_net)] = total
    return {pair: (math.fsum(lengths), math.fsum(areas)) for pair, (lengths, areas) in runs.items()}


class MaskTraceOverlapTests(unittest.TestCase):
    """The registration reports where a Row trace runs on a Column trace in the stack (never a failure)."""

    def test_the_soft_finger_taper(self) -> None:
        # With both tails on one side, the lane taper puts raised Column stubs over the Row lanes: COL_12, at the
        # channel side and active only in ROW_01, runs 83.8 mm on ROW_07's lane, 0.018 mm off its centre line.
        request = dict(_corpus())["soft-finger taper 48x12 tight"]
        for tail, expected in (({"row_side": "bottom", "column_side": "bottom"}, True), ({"row_side": "bottom", "column_side": "top"}, False)):
            with self.subTest(tail=tail):
                result = generate_design(_masked_request(dict(request, tail=tail, matrix={k: v for k, v in request["matrix"].items() if k != "mask"}), lambda row: 11))
                self.assertTrue(result["ok"], result["validation"]["errors"][:3])
                registration = result["boards"]["row"]["verification"]["registration"]
                self.assertTrue(registration["passed"])
                runs = _stacked_runs(result)
                self.assertEqual(bool(runs), expected)
                if not expected:
                    self.assertEqual({key: registration[key] for key in TRACE_OVERLAP_KEYS},
                                     {"trace_overlap_mm": 0.0, "trace_overlap_nets": None, "trace_overlap_pairs": 0, "trace_overlap_area_mm2": 0.0})
                    continue
                (nets, (length, _)), = sorted(runs.items(), key=lambda item: (-item[1][0], item[0]))[:1]
                self.assertEqual(nets, ("ROW_07", "COL_12"))
                self.assertAlmostEqual(length, 83.826, delta=1e-3)
                self.assertEqual(registration["trace_overlap_nets"], list(nets))
                self.assertAlmostEqual(registration["trace_overlap_mm"], length, delta=EPSILON)
                self.assertEqual(registration["trace_overlap_pairs"], len(runs))
                self.assertAlmostEqual(registration["trace_overlap_area_mm2"], math.fsum(area for _, area in runs.values()), delta=EPSILON)

    def test_the_corpus_against_an_independent_measure(self) -> None:
        # Every run of the corpus is axis-parallel, so the measure above sees all of them.
        for name, request in _corpus():
            with self.subTest(case=name):
                result = generate_design(request)
                registration = result["boards"]["row"]["verification"]["registration"]
                runs = _stacked_runs(result)
                longest = max((length for length, _ in runs.values()), default=0.0)
                self.assertAlmostEqual(registration["trace_overlap_mm"], longest, delta=EPSILON)
                self.assertEqual(registration["trace_overlap_pairs"], len(runs))
                self.assertAlmostEqual(registration["trace_overlap_area_mm2"], math.fsum(area for _, area in runs.values()), delta=EPSILON)
                self.assertTrue(registration["passed"])

    def test_a_column_trace_moved_onto_a_row_lane(self) -> None:
        # Opposite tails have no run; a Column trace laid on a Row lane (in the stack frame) is one.
        result = generate_design(_masked_request(_request(10, 12, tail={"row_side": "bottom", "column_side": "top"}), lambda row: 2 + row))
        row_board, column_board = result["boards"]["row"], copy.deepcopy(result["boards"]["column"])
        self.assertEqual(result["boards"]["row"]["verification"]["registration"]["trace_overlap_pairs"], 0)
        lane = max(
            ((net, a, b) for net, a, b, _ in engine_drc._stacked_traces(row_board) if a[0] == b[0]), key=lambda item: abs(item[1][1] - item[2][1])
        )
        # A Column route whose stacked image is that lane: the Column board is the bottom one (not turned over).
        self.assertEqual(column_board["physical_side"], "bottom")
        region = column_board["grid_registration"]["active_region"]
        cx, cy = region["x"] + region["width"] / 2, region["y"] + region["height"] / 2
        points = [[round(point[0] + cx, 6), round(point[1] + cy, 6)] for point in (lane[1], lane[2])]
        column_board["layers"]["top_copper"]["routes"].append({"net": "COL_05", "segment": "fanout", "width_mm": 0.127, "points": points})
        record = verify_registration(row_board, column_board, PROFILE)["measurements"]
        self.assertEqual((record["trace_overlap_nets"], record["trace_overlap_pairs"]), ([lane[0], "COL_05"], 1))
        self.assertAlmostEqual(record["trace_overlap_mm"], abs(lane[1][1] - lane[2][1]), delta=EPSILON)
        self.assertAlmostEqual(record["trace_overlap_area_mm2"], abs(lane[1][1] - lane[2][1]) * 0.127, delta=EPSILON)
        self.assertTrue(record["passed"])  # reported, never a failure


class MaskClassRuleTests(unittest.TestCase):
    """Masks outside the straight classes are refused, naming the first offending row or column and a fix."""

    def test_refusals_name_the_first_offending_row_or_column(self) -> None:
        opposite = {"row_side": "bottom", "column_side": "top"}
        cases = (
            # An upright (isosceles) triangle: its top rows stop short of the Row channel (fails A).
            ("upright, opposite tails", _request(8, 8, {"mask": [[5 - (row + 1) // 2, 4 + (row + 1) // 2] for row in range(1, 9)]}, tail=opposite),
             "matrix.mask[0]", "ROW_01 ends at COL_04 on the Row-channel side, 3 column(s) short of COL_01"),
            # An inverted triangle against the Column tail (fails B): COL_02's stub passes ROW_01 on its far side.
            ("inverted, opposite tails", _request(8, 8, {"mask": [[1, row] for row in range(1, 9)]}, tail=opposite),
             "matrix.mask[0]", "COL_02 ends at ROW_02, and ROW_01, next to it on the Column-tail side, ends at COL_01"),
            ("inverted, right tails", _request(8, 8, {"mask": [[row, 8] for row in range(1, 9)]}, tail={"row_side": "right", "column_side": "right"}),
             "matrix.mask[1]", "COL_01 ends at ROW_01, and ROW_02, next to it on the Column-tail side, ends at COL_02"),
            ("disk", _request(10, 10, {"mask": [[4, 7], [2, 9], [1, 10], [1, 10], [1, 10], [1, 10], [1, 10], [1, 10], [2, 9], [4, 7]]}),
             "matrix.mask[0]", "ROW_01 ends at COL_07 on the Row-channel side"),
        )
        for name, request, field, phrase in cases:
            with self.subTest(case=name):
                result = generate_design(request)
                errors = result["validation"]["errors"]
                self.assertEqual([(issue["code"], issue["field"]) for issue in errors], [("E_MASK_ROUTING", field)])
                self.assertIn(phrase, errors[0]["message"])
                self.assertRegex(errors[0]["message"], r"(Extend|add|drop) ")
                self.assertEqual(result["boards"], {})
        # The mirror image of the refused inverted triangle is of the classes, and builds clean.
        built = generate_design(_request(8, 8, {"mask": [[1, 9 - row] for row in range(1, 9)]}, tail=opposite))
        self.assertTrue(built["ok"], built["validation"]["errors"][:2])


def _random_case(rng: random.Random):
    """A random design and a random mask of the straight classes (``None`` when the draw is not one)."""

    rows, columns = (rng.choice((2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 64)) for _ in range(2))
    pitch = rng.choice((0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0))
    width = max(0.1016, min(round(rng.uniform(0.4, 0.8) * pitch, 3), round(pitch - 0.25, 3)))
    side = rng.choice(_SIDES)
    top = rng.choice(("rows", "columns"))
    request = _request(
        rows, columns, {"pitch_x_mm": pitch, "pitch_y_mm": pitch, "taxel_width_mm": width, "taxel_height_mm": width},
        routing={"trace_width_mm": rng.choice((0.1016, 0.127, 0.15, 0.2, 0.254)), "trace_space_mm": rng.choice((0.1016, 0.127, 0.15, 0.2, 0.246))},
        tail={"row_side": side, "column_side": _OPPOSITE[side] if rng.random() < 0.3 else side},
        role_mapping={"top": top, "bottom": "columns" if top == "rows" else "rows"},
    )
    base, step, every = rng.randint(0, columns - 1), rng.randint(0, 3), rng.randint(1, 3)
    checked = check_design(request)
    if not checked["ok"]:
        return None
    mask = _straight_mask(checked["design"], lambda row: base + (step * row) // every)
    if all(pair == [1, columns] for pair in mask):
        return None
    masked = dict(request, matrix=dict(request["matrix"], mask=mask))
    return masked if check_design(masked)["ok"] else None


class MaskDrcPropertyTests(unittest.TestCase):
    def test_random_masks_of_the_straight_classes_are_clean(self) -> None:
        # About 200 seeded random designs (sizes 2-64, pitch 0.6-5, fill 0.4-0.8, every routing, tail side and
        # role) with random masks of classes A and B: every record and the registration pass.
        rng = random.Random(20261021)
        built = draws = 0
        failures = []
        while built < 200:
            draws += 1
            self.assertLess(draws, 1000)
            request = _random_case(rng)
            if request is None:
                continue
            result = generate_design(request)
            built += 1
            registration = result["boards"]["row"]["verification"]["registration"] if result["boards"] else {}
            failed = {key: sorted(rule for rule, record in board["verification"]["checks"].items() if not record["passed"]) for key, board in result["boards"].items()}
            if not result["ok"] or any(failed.values()) or registration.get("wrong_crossing_count") != 0:
                failures.append((request["matrix"], request["routing"], request["tail"], failed, [issue["code"] for issue in result["validation"]["errors"]]))
                continue
            for board in result["boards"].values():
                checks = board["verification"]["checks"]
                self.assertEqual(checks["active_field_margin"]["measured_mm"], 0.5)
                self.assertEqual(checks["contact_exposure"]["electrodes"]["measured_mm"], 0.1)
                self.assertGreaterEqual(checks["coverlay_opening_to_trace"]["measured_mm"], 0.15)
        self.assertEqual(failures, [])


class MaskDrcPerformanceTests(unittest.TestCase):
    def test_a_64_by_64_masked_design_generates_and_checks_fast(self) -> None:
        request = _masked_request(_request(64, 64, ONE_MM, routing=TIGHT), lambda row: row)
        started = time.perf_counter()
        result = generate_design(request)
        self.assertLess(time.perf_counter() - started, 5.0)
        self.assertTrue(result["ok"], result["validation"]["errors"][:3])
        self.assertEqual(result["boards"]["row"]["verification"]["registration"]["wrong_crossing_count"], 0)


# SHA-256 of the canonical JSON of both boards' verification (the 30 records and the registration) of masked
# builds, written on 2026-10-21 from the P2 DRC and rewritten when the registration gained the trace overlap
# report (the same day): the same on Python 3.9.6 and 3.12 (the CI matrix).
VERIFICATION_DIGESTS = {
    "right triangle 30x29": "f83cd4a152b4860603c59a2fb4351f56b62f2f6e94029cf99ccbcc6d43b57ad4",
    "quarter disk 20x20": "9970ca24306110acdcf35b688002b98ba719fd133fd1613569a05eaec0dbbf21",
    "soft-finger taper 48x12 tight": "bb4183fac27109fc7f41dc51907d346e739c0217105344a5b85292d23d34d07d",
    "p0.6 tight 16x24": "bd97299773817cf27c72131ce7be9dd0ec4e61c246616ef03c17c0a40a9d89d2",
    "sparse 3 mm 10x12 (per-electrode windows)": "490871941d7921dc819ad8f420c57f4a5a018e1dcc3878c7e0707ed1d2613c0a",
}


def _verification_digest(result: dict) -> str:
    verification = {key: board["verification"] for key, board in sorted(result["boards"].items())}
    return hashlib.sha256(_canonical_json(verification).encode("utf-8")).hexdigest()


class MaskDrcDeterminismTests(unittest.TestCase):
    def test_masked_verification_is_pinned(self) -> None:
        corpus = dict(_corpus())
        for name, digest in VERIFICATION_DIGESTS.items():
            with self.subTest(case=name):
                self.assertEqual(_verification_digest(generate_design(corpus[name])), digest)

    def test_the_masked_checks_sum_no_floats(self) -> None:
        # Python 3.12's sum() of floats rounds differently from 3.9's; the masked checks use loops, min, max and fsum,
        # and iterate no set in order.
        functions = [
            engine_drc._edge_boxes, engine_drc._opening_ring, engine_drc._masked_field_margin, engine_drc._electrode_region, engine_drc._same_ring, engine_drc._masked_coverlay_checks,
            engine_drc._swept_inside, engine_drc._rings_touch, engine_drc._ring_gap, engine_drc._strict_opening_to_trace,
            engine_drc._masked_exposure, engine_drc._box_ring_margin, engine_drc.stack_frame, engine_drc._stacked_electrodes,
            engine_drc._masked_registration, engine_drc._masked_grid_deviation, engine_drc._masked_registration_errors,
            engine_drc._stacked_traces, engine_drc._trace_overlap,
            engine_geometry.is_rectilinear, engine_geometry.is_orthogonally_convex, engine_geometry.clip_segment_outside_box,
            engine_geometry.segment_parts_off_box_boundary,
        ]
        for function in functions:
            with self.subTest(function=function.__name__):
                self.assertEqual(_determinism_problems(function), [])
        # And so does every function of the DRC that handles a masked board or a polygon window.
        handling = [
            value for name, value in sorted(vars(engine_drc).items())
            if inspect.isfunction(value) and value.__module__ == engine_drc.__name__
            and re.search(r"mask|active_outline|\"polygon\"", inspect.getsource(value))
        ]
        self.assertGreater(len(handling), 10)
        for function in handling:
            with self.subTest(function=function.__name__):
                self.assertEqual([problem for problem in _determinism_problems(function) if "set" in problem], [])
        # Every function of the DRC named for the mask is in the list.
        named = sorted(name for name, value in vars(engine_drc).items() if inspect.isfunction(value) and value.__module__ == engine_drc.__name__ and "mask" in name)
        self.assertEqual([name for name in named if getattr(engine_drc, name) not in functions], [])


class MaskGeometryHelperTests(unittest.TestCase):
    def test_clipping_a_segment_outside_a_box(self) -> None:
        clip = engine_geometry.clip_segment_outside_box
        box = (0.0, 0.0, 1.0, 1.0)
        self.assertEqual(clip([-1.0, 0.5], [2.0, 0.5], box), [([-1.0, 0.5], [0.0, 0.5]), ([1.0, 0.5], [2.0, 0.5])])
        self.assertEqual(clip([0.2, 0.2], [0.8, 0.8], box), [])
        self.assertEqual(clip([-1.0, 2.0], [2.0, 2.0], box), [([-1.0, 2.0], [2.0, 2.0])])
        self.assertEqual(clip([0.5, 0.5], [0.5, 3.0], box), [([0.5, 1.0], [0.5, 3.0])])
        self.assertEqual(clip([-1.0, 1.0], [2.0, 1.0], box), [([-1.0, 1.0], [0.0, 1.0]), ([1.0, 1.0], [2.0, 1.0])])  # along a side

    def test_edge_parts_off_a_box(self) -> None:
        parts = engine_geometry.segment_parts_off_box_boundary
        box = (0.0, 0.0, 1.0, 1.0)
        self.assertEqual(parts([-1.0, 1.0], [2.0, 1.0], box, EPSILON), [([-1.0, 1.0], [0.0, 1.0]), ([1.0, 1.0], [2.0, 1.0])])
        self.assertEqual(parts([0.0, 0.2], [0.0, 0.8], box, EPSILON), [])
        self.assertEqual(parts([0.0, -1.0], [0.0, 0.5], box, EPSILON), [([0.0, -1.0], [0.0, 0.0])])
        self.assertEqual(parts([0.5, 0.5], [0.5, 2.0], box, EPSILON), [([0.5, 0.5], [0.5, 2.0])])  # not on a side

    def test_orthogonal_convexity(self) -> None:
        convex = engine_geometry.is_orthogonally_convex
        staircase = [[0, 0], [3, 0], [3, 1], [2, 1], [2, 2], [1, 2], [1, 3], [0, 3]]
        self.assertTrue(convex(staircase))
        self.assertTrue(engine_geometry.is_rectilinear(staircase, EPSILON))
        u_shape = [[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3], [0, 3]]
        self.assertFalse(convex(u_shape))
        self.assertFalse(engine_geometry.is_rectilinear([[0, 0], [2, 0], [1, 1]], EPSILON))


class MaskDrcDocsTests(unittest.TestCase):
    def test_the_masked_keys_are_documented(self) -> None:
        text = (ROOT / "docs" / "LAYOUT_SCHEMA.md").read_text(encoding="utf-8")
        result = generate_design(_corpus()[1][1])
        board = result["boards"]["row"]
        checks = board["verification"]["checks"]
        keys = [key for key in board["verification"]["registration"] if key in MASKED_REGISTRATION_KEYS]
        self.assertEqual(keys, list(MASKED_REGISTRATION_KEYS))
        self.assertEqual([key for key in board["verification"]["registration"] if key in TRACE_OVERLAP_KEYS], list(TRACE_OVERLAP_KEYS))
        for key in [*keys, *TRACE_OVERLAP_KEYS, "semantics", "region", "electrodes", "active_outline_mismatch", "stack_frame"]:
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", text)
        self.assertEqual(set(checks["contact_exposure"]["electrodes"]), {"measured_mm", "where"})


if __name__ == "__main__":
    unittest.main()
