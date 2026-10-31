"""Column-board outline, containment, feasibility and offset regressions.

Covers audit C2 (outer electrodes/openings at the outline), H3 (0.3 mm JLC
copper-to-edge), M1 (stiffener inside the outline), M2 (no shoulder notch,
neck never narrower than the tail), H1 (fan-out scales with pitch), L5
(single-lane fan-out never wider than the body) and M8 (true offset), plus
review finding F2 (rolling-circle fillets keep the full radius), the D5
body-side steps (zero or at least one fillet radius, Row and Column), the
F1 layout-grid invariant and the 2026-10-15 bundle: the fan-out converges
into bundles at the design's trace width + space and the outline follows it.
"""

from __future__ import annotations

import math
import unittest

from engine import generate_design as _engine_generate_design, load_profile
from engine.geometry import fillet_concave_corners, offset_polyline
from engine.layout import column_plan

try:
    import geometry_checks as gc
except ImportError:  # run as ``python -m unittest tests.test_geometry_column``
    from tests import geometry_checks as gc

try:
    from geometry_checks import straight_channel
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel


def generate_design(design=None, *args, **kwargs):
    """``engine.generate_design`` on the straight Row channel, which these tests measure (the generic template's default is
    the diagonal Row bus since claude/specs/masked-field/P5-diagonal-bus.md section 18; geometry_checks.straight_channel)."""

    return _engine_generate_design(straight_channel(design), *args, **kwargs)

EPS = 1e-6
# (columns, pitch_x, column electrode width): edge cases of both lane modes.
COLUMN_CASES = (
    (1, 0.6, 0.35),
    (1, 5.0, 4.75),
    (2, 1.0, 0.75),
    (4, 5.0, 4.75),
    (8, 0.6, 0.1016),
    (16, 0.6, 0.35),
    (16, 2.0, 1.4),
    (17, 0.9, 0.5),
    (17, 1.3, 1.05),
    (20, 1.2, 0.95),
    (32, 0.75, 0.5),
    (32, 2.0, 1.4),
)


def _column_board(columns: int, pitch: float, width: float, **extra):
    design = {"matrix": {"columns": columns, "pitch_x_mm": pitch, "taxel_width_mm": width}}
    design.update(extra)
    result = generate_design(design)
    return result, result["boards"].get("column")


def _body_steps(board, profile) -> tuple[float, float]:
    """``(left, right)``: how far each body side stands out beyond the tail and
    the route envelope below the body (negative: they stand out beyond it).

    The board must have its tail at the bottom (the build frame).  The route
    envelope is each route vertex below the body offset by half the widest
    route (the finger traces), the copper-to-edge rule and the offset
    allowance, as the outline is built.
    """

    radius = profile["outline"]["outline_fillet_radius_mm"]
    widest = max(route["width_mm"] for route in board["layers"]["top_copper"]["routes"])
    envelope = widest / 2 + profile["routing"]["copper_to_edge_mm"] + profile["outline"]["offset_allowance_mm"]
    bottom = board["grid_registration"]["active_region"]["y"] - profile["routing"]["active_edge_clearance_mm"]
    # Above the fillets at the body bottom only the body sides remain.
    body = [x for x, y in board["outline"]["points"] if y > bottom + radius + EPS]
    below = [x for route in board["layers"]["top_copper"]["routes"] for x, y in route["points"] if y < bottom - EPS]
    tail = board["tail"]["bounds"]
    left = min([tail["x"], *(x - envelope for x in below)])
    right = max([tail["x"] + tail["width"], *(x + envelope for x in below)])
    return left - min(body), max(body) - right


class ColumnOutlineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_profile()
        cls.cases = []
        for columns, pitch, width in COLUMN_CASES:
            result, board = _column_board(columns, pitch, width)
            cls.cases.append(((columns, pitch, width), result, board))

    def test_every_case_generates(self) -> None:
        for case, result, _ in self.cases:
            with self.subTest(case=case):
                self.assertTrue(result["ok"], result["validation"]["errors"])

    def test_electrodes_openings_and_stiffener_stay_inside_the_outline(self) -> None:
        margin = self.profile["routing"]["active_edge_clearance_mm"]
        for case, _, board in self.cases:
            outline = board["outline"]["points"]
            with self.subTest(case=case):
                for electrode in board["layers"]["top_copper"]["electrodes"]:
                    self.assertTrue(gc.polygon_inside(gc.box_polygon(gc.bounds(electrode)), outline), electrode["net"])
                active = board["grid_registration"]["active_region"]
                grown = (active["x"] - margin, active["y"] - margin, active["x"] + active["width"] + margin, active["y"] + active["height"] + margin)
                # The body keeps the full margin on all four sides of the taxel field,
                # including below it where the fan-out starts (audit C2).
                self.assertTrue(gc.polygon_inside(gc.box_polygon(grown), outline))
                for opening in board["layers"]["top_coverlay_openings"]:
                    self.assertTrue(gc.polygon_inside(gc.box_polygon(gc.bounds(opening)), outline), opening["kind"])
                for stiffener in board["layers"]["bottom_stiffener"]:
                    self.assertTrue(gc.polygon_inside(stiffener["points"], outline))

    def test_all_copper_keeps_the_jlc_copper_to_edge_rule(self) -> None:
        rule = self.profile["routing"]["copper_to_edge_mm"]
        self.assertGreaterEqual(rule, self.profile["fabrication"]["copper_to_board_edge_mm"])
        for case, _, board in self.cases:
            with self.subTest(case=case):
                self.assertGreaterEqual(gc.min_copper_to_outline(board), rule - EPS)
                for cutout in board["outline"]["cutouts"]:
                    for kind, net, geometry in gc.copper(board):
                        probe = geometry[1] if geometry[0] == "segment" else geometry[1][:2]
                        self.assertFalse(gc.point_in_polygon(probe, cutout), (kind, net))

    def test_tail_shoulder_has_no_notch_and_the_neck_is_never_narrower_than_the_tail(self) -> None:
        limit = self.profile["outline"]["maximum_unfilleted_concave_turn_deg"]
        for case, _, board in self.cases:
            outline = board["outline"]["points"]
            tail = board["tail"]
            with self.subTest(case=case):
                turns = gc.turns_degrees(outline)
                # Concave corners are filleted (only arc-sized steps remain) and
                # no convex spike sharper than a right angle exists (old barb: 73°).
                self.assertLessEqual(-min(turns), limit + 1e-9)
                self.assertLessEqual(max(turns), 90.0 + 1e-6)
                neck = tail["neck_bounds"]
                center = neck["x"] + neck["width"] / 2
                widths = [
                    gc.cross_section(outline, level, center)
                    for level in gc.levels_between(outline, neck["y"], neck["y"] + neck["height"])
                ]
                self.assertGreaterEqual(min(widths), tail["width_mm"] - EPS)
        default = generate_design()["boards"]["column"]
        self.assertEqual(default["construction"]["minimum_concave_fillet_radius_mm"], self.profile["outline"]["outline_fillet_radius_mm"])

    def test_fanout_transitions_scale_so_wide_pitches_generate(self) -> None:
        # Every one of these failed the fixed 16 mm transitions (32 columns
        # stopped at 2.177 mm, 16 columns at 5.08 mm).
        space = generate_design()["design"]["routing"]["trace_space_mm"]
        heights = []
        for columns, pitch in ((32, 2.2), (32, 2.5), (32, 3.0), (24, 3.0), (17, 4.0), (16, 6.0), (16, 10.0), (12, 10.0), (32, 6.0)):
            result, board = _column_board(columns, pitch, 1.4)
            with self.subTest(columns=columns, pitch=pitch):
                self.assertTrue(result["ok"], result["validation"]["errors"])
                construction = board["construction"]
                self.assertLessEqual(construction["entry_taper_angle_deg"], self.profile["fanout"]["maximum_taper_angle_deg"])
                routes = [item for item in gc.copper(board) if item[0] == "route"]
                gaps = [
                    gc.segment_distance(a[2][1], a[2][2], b[2][1], b[2][2]) - a[2][3] - b[2][3]
                    for i, a in enumerate(routes)
                    for b in routes[i + 1 :]
                    if a[1] != b[1]
                ]
                self.assertGreaterEqual(min(gaps), space - EPS)
                if columns == 32:
                    heights.append(construction["entry_transition_height_mm"])
        self.assertEqual(heights, sorted(heights))
        self.assertGreater(heights[-1], heights[0])

    def test_narrow_two_lane_fanout_spreads_wider_than_the_body(self) -> None:
        # Since 2026-10-15 (before, E_DUAL_LANE_WIDTH asked for a wider pitch): when
        # two lanes and the minimum slot need more width than the body has, the
        # lanes spread beyond it; the slot keeps its minimum and the body its margins.
        # With the default 0.254 mm bundle pitch both lanes fit every legal field
        # (the user's 16 x 17 at 0.6 mm included); the widest bundle (0.254 mm
        # traces, 0.246 mm spacing: the 0.5 mm contact pitch) still spreads.
        fanout = self.profile["fanout"]
        margin = self.profile["routing"]["active_edge_clearance_mm"]
        radius = self.profile["outline"]["outline_fillet_radius_mm"]
        envelope = (
            self.profile["routing"]["finger_trace_width_mm"] / 2
            + self.profile["routing"]["copper_to_edge_mm"]
            + self.profile["outline"]["offset_allowance_mm"]
        )
        widest = {"trace_width_mm": self.profile["limits"]["maximum_trace_width_mm"], "trace_space_mm": self.profile["limits"]["maximum_trace_space_mm"]}
        pitch_of_bundle = round(widest["trace_width_mm"] + widest["trace_space_mm"], 6)
        # The last three: odd column counts where one body side is flush with the fan-out
        # and the other stands a full fillet radius or more inside it.
        for columns, pitch, width in ((17, 0.6, 0.35), (17, 0.6, 0.1016), (18, 0.7, 0.45), (24, 0.65, 0.4), (32, 0.6, 0.35), (32, 0.62, 0.37),
                                      (17, 0.68, 0.1016), (17, 0.7, 0.45), (19, 0.65, 0.4)):
            result, board = _column_board(columns, pitch, width, routing=widest)
            with self.subTest(columns=columns, pitch=pitch, width=width):
                self.assertTrue(result["ok"], result["validation"]["errors"])
                self.assertTrue(board["verification"]["all_checks_passed"])
                self.assertEqual(board["tail"]["fanout_lane_count"], 2)
                self.assertAlmostEqual(board["construction"]["slot_bounds"]["width"], fanout["minimum_slot_width_mm"], places=6)
                body = (columns - 1) * pitch + width + 2 * margin
                active = board["grid_registration"]["active_region"]
                body_section = gc.cross_section(
                    board["outline"]["points"], active["y"] + active["height"] / 2, active["x"] + active["width"] / 2
                )
                self.assertGreaterEqual(body_section, body - EPS)
                self.assertLess(body_section, body + 2 * radius)
                # Below the body: both lanes at the bundle pitch, each side of the slot, plus the envelope.
                left, right = board["tail"]["fanout_lane_channel_counts"]
                self.assertEqual(board["construction"]["fanout_bundle_pitch_mm"], pitch_of_bundle)
                spread = (
                    fanout["minimum_slot_width_mm"]
                    + 2 * fanout["lane_to_slot_clearance_mm"]
                    + (left - 1 + right - 1) * pitch_of_bundle
                    + 2 * envelope
                )
                self.assertGreater(spread, body + EPS)
                # The outline is as wide as the spread, or up to one fillet radius wider where
                # a body side moves out to a full fillet radius beyond the fan-out below it.
                width_of_board = board["metrics"]["outline_width_mm"]
                self.assertGreaterEqual(width_of_board, spread - EPS)
                self.assertLessEqual(width_of_board, spread + radius + EPS)
                # The size pre-check (E_BOARD_SIZE) sees the same width as the built outline.
                self.assertAlmostEqual(column_plan(result["design"], self.profile)["outline_size"][0], width_of_board, places=5)
                # Each body side on its own is flush with the fan-out below it or stands at least a
                # full fillet radius from it: with an odd column count the first lane carries one
                # route more, so the two sides spread one bundle pitch apart.
                for step in _body_steps(board, self.profile):
                    self.assertTrue(abs(step) <= 2 * EPS or abs(step) >= radius - 2 * EPS, step)
        # Where both lanes fit, nothing changes: the outline is as wide as the body.
        # The default bundle fits 17 columns at 0.6 mm (the spread case above).
        for columns, pitch, width in ((17, 1.0, 0.7), (17, 0.6, 0.35), (32, 0.6, 0.35)):
            result, board = _column_board(columns, pitch, width)
            with self.subTest(columns=columns, pitch=pitch, bundle="default"):
                self.assertTrue(result["ok"], result["validation"]["errors"])
                self.assertGreaterEqual(board["construction"]["slot_bounds"]["width"], fanout["minimum_slot_width_mm"])
                active = board["grid_registration"]["active_region"]
                section = gc.cross_section(board["outline"]["points"], active["y"] + active["height"] / 2, active["x"] + active["width"] / 2)
                self.assertAlmostEqual(board["metrics"]["outline_width_mm"], section, places=6)

    def test_single_lane_fanout_is_never_wider_than_the_body(self) -> None:
        margin = self.profile["routing"]["active_edge_clearance_mm"]
        radius = self.profile["outline"]["outline_fillet_radius_mm"]
        for columns, pitch, width in ((16, 0.6, 0.35), (12, 0.6, 0.35), (16, 1.0, 0.7), (16, 3.0, 1.4)):
            result, board = _column_board(columns, pitch, width)
            with self.subTest(columns=columns, pitch=pitch):
                self.assertTrue(result["ok"], result["validation"]["errors"])
                # The body holds the taxel field plus its margins; a side moves
                # out (by less than one fillet radius) only where the step to the
                # fan-out would be too narrow for a full fillet.
                body = (columns - 1) * pitch + width + 2 * margin
                active = board["grid_registration"]["active_region"]
                body_section = gc.cross_section(
                    board["outline"]["points"], active["y"] + active["height"] / 2, active["x"] + active["width"] / 2
                )
                self.assertGreaterEqual(body_section, body - EPS)
                self.assertLess(body_section, body + 2 * radius)
                # Nothing below the body (the fan-out) sticks out beyond it.
                self.assertAlmostEqual(board["metrics"]["outline_width_mm"], body_section, places=6)
                # One bundle at the design's trace width + space (D6's deck pitch is gone).
                routing = result["design"]["routing"]
                self.assertEqual(board["construction"]["fanout_bundle_pitch_mm"], round(routing["trace_width_mm"] + routing["trace_space_mm"], 6))

    def test_body_steps_leave_room_for_full_fillets(self) -> None:
        # Each case once had a body-side step narrower than the 0.5 mm fillet:
        # a narrow outer electrode stub (0.497 mm), a dual-lane bundle envelope
        # 0.136 mm inside the body side, a tail 0.223 mm narrower per side
        # than the body, a tail 0.0113 mm wider per side than the body, and
        # Row bodies 0.1016 mm and 0.154 mm wider and 0.192 mm narrower than
        # their tails (the 0.254 mm bundle pitch of 2026-10-15 changed the
        # bundle and Row cases: a 0.6 mm lane pitch made them 0.047, 0.1, 0.4
        # and 0.2 mm).  D5: a body side is flush with what lies below it or
        # stands at least one fillet radius out (stage-T reviewer finding: the
        # full fillets alone did not show a missing side move).
        radius = self.profile["outline"]["outline_fillet_radius_mm"]
        cases = (
            ({"columns": 16, "pitch_x_mm": 0.6, "taxel_width_mm": 0.35}, {}, "column", (0.5, 0.5)),
            ({"columns": 20, "pitch_x_mm": 0.9, "taxel_width_mm": 0.6}, {}, "column", (0.5, 0.5)),
            ({"columns": 2, "pitch_x_mm": 2.219, "taxel_width_mm": 0.7269}, {"column_pins": 7}, "column", (0.5, 0.5)),
            ({"columns": 15, "pitch_x_mm": 0.991, "taxel_width_mm": 0.6034}, {"column_pins": 31}, "column", (0.0, 0.0)),
            ({"rows": 1, "columns": 1, "taxel_width_mm": 0.1016, "taxel_height_mm": 0.1016}, {"row_pins": 4}, "row", (0.0, 0.5)),
            ({"rows": 2, "columns": 2, "pitch_x_mm": 0.6, "taxel_width_mm": 0.3}, {"row_pins": 6}, "row", (0.0, 0.5)),
            ({"rows": 3, "columns": 1, "pitch_x_mm": 0.6, "taxel_width_mm": 0.3}, {"row_pins": 6}, "row", (0.0, 0.0)),
        )
        for matrix, connector, subject, steps in cases:
            result = generate_design({"matrix": matrix, "connector": connector})
            with self.subTest(matrix=matrix, connector=connector):
                self.assertTrue(result["ok"], result["validation"]["errors"])
                for key, board in result["boards"].items():
                    # None: the step vanished, so the board has no concave corner left.
                    self.assertIn(board["construction"]["minimum_concave_fillet_radius_mm"], (None, radius), board["id"])
                    self.assertTrue(board["verification"]["all_checks_passed"], board["id"])
                    measured = _body_steps(board, self.profile)
                    for step in measured:
                        self.assertTrue(abs(step) <= 2 * EPS or abs(step) >= radius - 2 * EPS, (board["id"], measured))
                    if key == subject:
                        self.assertEqual(tuple(round(step, 4) for step in measured), steps, board["id"])

    def test_rotated_tails_keep_the_same_clearances(self) -> None:
        reference = None
        for side in ("bottom", "right", "top", "left"):
            result, board = _column_board(17, 1.3, 1.05, connector_side=side)
            with self.subTest(side=side):
                self.assertTrue(result["ok"], result["validation"]["errors"])
                clearance = round(gc.min_copper_to_outline(board), 6)
                reference = clearance if reference is None else reference
                self.assertEqual(clearance, reference)


class TrueOffsetTests(unittest.TestCase):
    STEP = math.radians(10)

    def _distance_to(self, point, polyline) -> float:
        return min(gc.point_segment_distance(point, a, b) for a, b in zip(polyline, polyline[1:]))

    def _check(self, polyline, distance, left) -> None:
        offset = offset_polyline(polyline, distance, left=left, arc_step_rad=self.STEP)
        samples = [
            (a[0] + (b[0] - a[0]) * k / 20, a[1] + (b[1] - a[1]) * k / 20)
            for a, b in zip(offset, offset[1:])
            for k in range(21)
        ]
        distances = [self._distance_to(point, polyline) for point in samples]
        self.assertGreaterEqual(min(distances), distance - 1e-9)
        self.assertLessEqual(max(distances), distance / math.cos(self.STEP / 2) + 1e-9)

    def test_offset_keeps_the_full_distance_at_every_corner(self) -> None:
        # The former vertex-normal offset kept only 0.3329 of 0.385 mm at the
        # 39° deck-to-entry corner of the default board.
        deck_corner = [[16.7, 20.0], [16.7, 28.125], [1.45, 46.75]]
        for left in (True, False):
            self._check(deck_corner, 0.385, left)
        for angle in (10, 39, 45, 60, 90, 120):
            turn = math.radians(angle)
            polyline = [[0.0, 0.0], [0.0, 5.0], [5.0 * math.sin(turn), 5.0 + 5.0 * math.cos(turn)]]
            for left in (True, False):
                with self.subTest(angle=angle, left=left):
                    self._check(polyline, 0.427, left)

    def test_rolling_circle_fillet_keeps_the_full_radius(self) -> None:
        area = lambda ring: abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in gc.edges(ring))) / 2
        # A plain right-angle corner: the arc vertices lie on the R circle
        # centred one radius off both edges, from tangent point to tangent point.
        corner = [[0.0, 0.0], [3.0, 0.0], [3.0, 1.0], [1.0, 1.0], [1.0, 3.0], [0.0, 3.0]]
        filleted, smallest = fillet_concave_corners(corner, 0.5, arc_step_rad=self.STEP)
        self.assertEqual(smallest, 0.5)
        arc = [point for point in filleted if 1.0 + 1e-9 < point[0] or 1.0 + 1e-9 < point[1]]
        arc = [point for point in arc if point[0] <= 1.5 + 1e-9 and point[1] <= 1.5 + 1e-9]
        self.assertEqual(len(arc), 10)  # 90 degrees in 10 degree steps, both tangent points included
        for point in arc:
            self.assertAlmostEqual(math.dist(point, (1.5, 1.5)), 0.5, places=12)
        self.assertTrue(gc.polygon_inside(corner, filleted))
        # A notch whose 2 mm floor is narrower than the 3 mm circle: the
        # rolling circle (a morphological closing) bridges the floor with one
        # full-radius arc between the two walls instead of shrinking two
        # fillets (the old per-vertex fillets fell to 1.277 mm).
        notch = [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [6.0, 10.0], [6.0, 5.0], [4.0, 5.0], [1.0, 10.0], [0.0, 10.0]]
        filleted, smallest = fillet_concave_corners(notch, 1.5, arc_step_rad=self.STEP)
        self.assertEqual(smallest, 1.5)
        # Centre: 1.5 from the wall x = 6 and from the slanted wall through
        # (4, 5) and (1, 10), whose inward normal is (5, 3) / sqrt(34).
        center = (4.5, 5.0 + (1.5 * math.sqrt(34.0) - 2.5) / 3.0)
        self.assertGreater(center[1] - 1.5, 5.0)  # the circle clears the floor
        added = [point for point in filleted if point not in notch]
        self.assertGreater(len(added), 2)
        for point in added:
            self.assertAlmostEqual(math.dist(point, center), 1.5, places=9)
        self.assertNotIn([6.0, 5.0], filleted)
        self.assertNotIn([4.0, 5.0], filleted)
        # Fillets only add board material inside the notch.
        self.assertGreater(area(filleted), area(notch))
        self.assertTrue(gc.polygon_inside(notch, filleted))

    def test_fillet_circle_may_touch_a_convex_vertex(self) -> None:
        # A concave corner whose incoming edge is a 0.2 mm step from a convex
        # corner: the R0.5 circle touches the convex vertex itself, not an edge.
        # Mirrored, the vertex lies ahead of the corner instead of behind it.
        step = [[0.0, 0.0], [1.2, 0.0], [1.2, 1.0], [1.0, 1.0], [1.0, 3.0], [0.0, 3.0]]
        mirrored = [[y, x] for x, y in reversed(step)]
        for polygon, center, vertex in ((step, (1.5, 1.4), (1.2, 1.0)), (mirrored, (1.4, 1.5), (1.0, 1.2))):
            with self.subTest(vertex=vertex):
                filleted, smallest = fillet_concave_corners(polygon, 0.5, arc_step_rad=self.STEP)
                self.assertEqual(smallest, 0.5)
                self.assertIn(list(vertex), filleted)
                added = [point for point in filleted if point not in polygon]
                self.assertTrue(added)
                for point in added:
                    self.assertAlmostEqual(math.dist(point, center), 0.5, places=9)
                self.assertTrue(gc.polygon_inside(polygon, filleted))

    def test_construction_origins_and_levels_are_on_the_layout_grid(self) -> None:
        # Review finding F1: rules met exactly by construction survive the
        # 1e-6 mm rounding of the emitted geometry only if every origin and
        # level they depend on is a grid value (inputs with any precision).
        profile = load_profile()
        for matrix in (
            {"rows": 12, "columns": 32},
            {"rows": 7, "columns": 9, "pitch_x_mm": 1.7528527850036792, "pitch_y_mm": 1.83737533, "taxel_width_mm": 0.118252019, "taxel_height_mm": 0.97824412},
            {"rows": 40, "columns": 20, "pitch_x_mm": 1.278990099175886, "pitch_y_mm": 3.1195267979, "taxel_width_mm": 0.700965786, "taxel_height_mm": 1.243385022},
        ):
            design = generate_design({"matrix": matrix, "tail": {"bottom_length_mm": 30.33961120541838}, "connector": {"column_pins": 41}})["design"]
            plan = column_plan(design, profile)
            values = [plan["tail_x"], plan["tip"], plan["merger_base"], plan["deck_bottom"], plan["deck_top"], plan["entry_top"],
                      plan["tail_top"], plan["pitch_x"], plan["column_width"], plan["tail_length"], *plan["active"], *plan["contact_x"],
                      *plan["decks"], *plan["centers"], plan["bundle_pitch"], plan["stagger"]]
            values += list(plan["slot"] or ())
            # Every bend of the convergence and the expansion lies on the grid.
            values += [y for bend in plan["entry"] + plan["merger"] if bend for y in bend]
            with self.subTest(matrix=matrix):
                for value in values:
                    self.assertAlmostEqual(value, round(value, 6), places=12)

    def test_concave_corner_next_to_a_round_join_gets_a_full_fillet(self) -> None:
        # Reviewer reproducer: the entry-taper envelope crosses the tail side
        # on the round join around the stub bend, 0.005 mm from the concave
        # vertex.  A fillet capped by the adjacent chord came out at 0.0106 mm.
        design = {
            "matrix": {"rows": 20, "columns": 8, "pitch_x_mm": 2.2, "pitch_y_mm": 8.380366, "taxel_width_mm": 0.1016, "taxel_height_mm": 7.627066},
            "tail": {"top_length_mm": 19.7996, "bottom_length_mm": 72.58826, "row_side": "left", "column_side": "right"},
            "connector": {"row_pins": 64, "column_pins": 31},
            "channel_order": {"rows": "descending", "columns": "descending"},
        }
        result = generate_design(design)
        self.assertTrue(result["ok"], result["validation"]["errors"])
        radius = load_profile()["outline"]["outline_fillet_radius_mm"]
        for board in result["boards"].values():
            with self.subTest(board=board["id"]):
                self.assertEqual(board["construction"]["minimum_concave_fillet_radius_mm"], radius)
                record = board["verification"]["checks"]["concave_fillet_radius"]
                self.assertTrue(record["passed"], record)
                self.assertGreaterEqual(record["measured_mm"], radius * math.cos(self.STEP / 2))

    def test_offset_of_a_full_fanout_route(self) -> None:
        board = generate_design()["boards"]["column"]
        tail, fanout = (route["points"] for route in board["layers"]["top_copper"]["routes"][:2])
        self.assertEqual(tail[-1], fanout[0])  # COL_01: the tail piece, then the fan-out piece
        route = [*tail, *fanout[1:]]
        self._check(route, 0.428, True)
        self._check(route, 0.428, False)


if __name__ == "__main__":
    unittest.main()
