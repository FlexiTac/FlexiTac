"""Whole-board DRC regressions (audit H5, I5, L4, L11, VERIFY-GEO-1, H1 field paths).

Also covers the stage-E review findings F1 (no post-generation failures from
coordinate rounding), F2 (tiny fillets are sharp corners), F3 (registration
errors name the failing sub-check) and F4 (straight tail after the stiffener).
"""

from __future__ import annotations

import copy
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

from engine import generate_design as _engine_generate_design, load_profile
from engine.drc import verify_board, verify_registration
from engine.layout import apply_tail_side

try:
    from geometry_checks import straight_channel
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel


def generate_design(design=None, *args, **kwargs):
    """``engine.generate_design`` on the straight Row channel, which these tests measure (the generic template's default is
    the diagonal Row bus since claude/specs/masked-field/P5-diagonal-bus.md section 18; geometry_checks.straight_channel)."""

    return _engine_generate_design(straight_channel(design), *args, **kwargs)

ROOT = Path(__file__).resolve().parents[1]
SIDES = ("bottom", "right", "top", "left")


def _codes(errors) -> set[str]:
    return {issue["code"] for issue in errors}


def _edited(board, mutate):
    board = copy.deepcopy(board)
    mutate(board)
    return board


class WholeBoardDrcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_profile()
        cls.result = generate_design()
        cls.row = cls.result["boards"]["row"]
        cls.column = cls.result["boards"]["column"]

    def _mutated(self, board, mutate):
        board = copy.deepcopy(board)
        mutate(board)
        return verify_board(board, self.profile, self.result["design"])

    def test_default_boards_record_every_rule_with_its_measurement(self) -> None:
        expected = {
            "route_route_clearance", "pad_trace_clearance", "pad_pad_clearance", "electrode_electrode_clearance",
            "electrode_route_clearance", "electrode_pad_clearance", "copper_to_outline", "route_to_outline",
            "copper_inside_outline", "copper_to_cutout", "active_field_margin", "coverlay_openings_inside_outline",
            "coverlay_bridge", "coverlay_opening_to_trace", "contact_exposure", "stiffener_inside_outline",
            "stiffener_zone", "stiffener_end_clearance", "outline_simple", "cutouts_inside_outline",
            "unfilleted_concave_turn_deg", "concave_fillet_radius", "neck_width", "connectivity", "min_electrode_width", "route_width",
            "tail_width", "contact_geometry", "board_short_side", "board_long_side",
        }
        for board in (self.row, self.column):
            checks = board["verification"]["checks"]
            self.assertEqual(set(checks), expected)
            for name, record in checks.items():
                with self.subTest(board=board["id"], check=name):
                    self.assertTrue(record["passed"], record)
                    self.assertEqual(record["violation_count"], 0)
                    self.assertIn("required_mm", record)
                    self.assertIn("measured_mm", record)
            self.assertTrue(board["verification"]["all_checks_passed"])
            self.assertTrue(board["verification"]["registration"]["passed"])
        column = self.column["verification"]["checks"]
        # The bundle runs at exactly the design's trace space (0.127 mm by default), on both boards.
        space = self.result["design"]["routing"]["trace_space_mm"]
        for board in (self.row, self.column):
            record = board["verification"]["checks"]["route_route_clearance"]
            self.assertEqual((record["required_mm"], record["measured_mm"]), (space, space))
            # The wide tail pieces keep the finger-section spacing, exactly, between neighbouring contacts.
            self.assertEqual(record["finger_section"], {"required_mm": 0.246, "measured_mm": 0.246, "violation_count": 0, "where": record["finger_section"]["where"]})
            self.assertEqual(board["verification"]["closest_inter_net_route_pair"]["segments"], ["fanout", "fanout"])
            self.assertEqual(board["verification"]["checks"]["route_width"]["measured_mm"], 0.0)
        self.assertGreaterEqual(column["route_to_outline"]["measured_mm"], 0.3)
        self.assertEqual(column["copper_to_outline"]["measured_mm"], 0.3)  # contacts sit exactly 0.3 mm from the tip
        # Thin (0.127 mm) bundle traces 0.75 mm from the slot sides.
        self.assertEqual(column["copper_to_cutout"]["measured_mm"], 0.6865)
        self.assertEqual(self.row["verification"]["checks"]["pad_trace_clearance"]["measured_mm"], 0.223)
        self.assertEqual(self.row["verification"]["checks"]["pad_pad_clearance"]["measured_mm"], 0.2)
        # The taxel field keeps exactly the 0.75 mm margin on both boards.
        for board in (self.row, self.column):
            checks = board["verification"]["checks"]
            self.assertEqual(checks["active_field_margin"]["measured_mm"], 0.75)
            self.assertEqual(checks["stiffener_zone"]["measured_mm"], 0.0)
            # Full R0.5 fillets drawn in 10 degree steps (vertices on the arc).
            self.assertGreaterEqual(checks["concave_fillet_radius"]["measured_mm"], 0.5 * math.cos(math.radians(5)))
        # Straight, full-width flexible tail after the 6.0 mm stiffener, up to
        # where the outline widens (audit review F4: the old record claimed the
        # nominal tail).  Row (12 mm tail): the R0.5 tail-root fillet starts
        # 0.5 mm below the body.  Column (7 mm tail, up to where the traces
        # widen): the outer route bends outward ``drop`` above that, and the
        # fillet at its envelope starts (0.428 + 0.5) tan(phi / 2) - (0.5 -
        # 0.428) / tan(phi) below the bend, phi being the merger taper angle.
        self.assertAlmostEqual(self.row["verification"]["checks"]["stiffener_end_clearance"]["measured_mm"], 12.0 - 6.0 - 0.5, places=6)
        phi = math.radians(self.column["construction"]["merger_taper_angle_deg"])
        early = 0.928 * math.tan(phi / 2) - 0.072 / math.tan(phi)
        outer = next(r for r in self.column["layers"]["top_copper"]["routes"] if r["net"] == "COL_01" and r["segment"] == "fanout")
        drop = outer["points"][1][1] - outer["points"][0][1]
        self.assertGreater(drop, 0.2)
        self.assertAlmostEqual(self.column["verification"]["checks"]["stiffener_end_clearance"]["measured_mm"], 1.0 + drop - early, places=5)

    def test_violation_counters_are_exact_on_synthetic_layouts(self) -> None:
        def with_routes(routes):
            def mutate(board):
                board["layers"]["top_copper"]["routes"] = routes
            return mutate

        width = self.profile["routing"]["finger_trace_width_mm"]
        # Three parallel nets 0.30 mm apart: two violating pairs (the old
        # running-minimum pruning reported one).
        parallel = [{"net": f"SYN_{i}", "width_mm": width, "points": [[20.0, 30.0 + 0.3 * i], [40.0, 30.0 + 0.3 * i]]} for i in range(3)]
        report = self._mutated(self.row, with_routes(parallel))["measurements"]
        self.assertEqual(report["inter_net_clearance_violation_segment_pair_count"], 2)
        self.assertEqual(report["checks"]["route_route_clearance"]["violation_count"], 2)
        # Unequal violating gaps (0.046 and 0.096 mm): both count, although the
        # second is larger than the minimum already found.
        unequal = [{"net": f"SYN_U{i}", "width_mm": width, "points": [[20.0, y], [40.0, y]]} for i, y in enumerate((30.0, 30.3, 30.65))]
        report = self._mutated(self.row, with_routes(unequal))["measurements"]
        self.assertEqual(report["checks"]["route_route_clearance"]["violation_count"], 2)
        self.assertEqual(report["inter_net_clearance_violation_segment_pair_count"], 2)
        # One horizontal net crossed by ten others: ten overlapping pairs (old: one).
        crossing = [{"net": "SYN_H", "width_mm": width, "points": [[20.0, 30.0], [40.0, 30.0]]}]
        crossing += [{"net": f"SYN_V{i}", "width_mm": width, "points": [[21.0 + 1.5 * i, 28.0], [21.0 + 1.5 * i, 32.0]]} for i in range(10)]
        report = self._mutated(self.row, with_routes(crossing))["measurements"]
        self.assertEqual(report["inter_net_copper_overlap_segment_pair_count"], 10)
        # Mixed widths: the thick pair overlaps whichever route order is used
        # (the old pruning on centre distance returned a false pass).
        mixed = [
            {"net": "SYN_A", "width_mm": 0.1, "points": [[20.0, 30.0], [40.0, 30.0]]},
            {"net": "SYN_B", "width_mm": 0.1, "points": [[20.0, 30.3], [40.0, 30.3]]},
            {"net": "SYN_C", "width_mm": 0.6, "points": [[20.0, 32.0], [40.0, 32.0]]},
            {"net": "SYN_D", "width_mm": 0.6, "points": [[20.0, 32.45], [40.0, 32.45]]},
        ]
        for routes in (mixed, list(reversed(mixed))):
            report = self._mutated(self.row, with_routes(routes))
            self.assertIn("E_ROUTE_CLEARANCE", _codes(report["errors"]))
            self.assertAlmostEqual(report["measurements"]["checks"]["route_route_clearance"]["measured_mm"], -0.15, places=6)

    def test_tail_pieces_keep_the_finger_section_spacing(self) -> None:
        # T-D3: a route pair with a wide tail piece keeps the finger-section
        # spacing (contact pitch less finger width, 0.246 mm), not only the
        # design's trace space; route_route_clearance counts such a pair against
        # that rule and reports those pairs as its finger_section.
        finger = self.profile["routing"]["finger_trace_width_mm"]
        finger_space = round(self.profile["connector"]["pad_pitch_mm"] - finger, 6)
        space = self.result["design"]["routing"]["trace_space_mm"]

        def routes(*specs):
            return [
                {"net": f"SYN_{index}", "segment": segment, "width_mm": width, "points": [[20.0, y], [40.0, y]]}
                for index, (segment, width, y) in enumerate(specs)
            ]

        cases = (
            # Two tail pieces 0.45 mm apart: a 0.196 mm gap, wider than the 0.127 mm trace space.
            (routes(("tail", finger, 30.0), ("tail", finger, 30.45)), 1, 0.196),
            # A tail piece and a fan-out piece: 0.38 - 0.127 - 0.0635 = 0.1895 mm.
            (routes(("tail", finger, 30.0), ("fanout", 0.127, 30.38)), 1, 0.1895),
            # The same gap between two fan-out pieces needs only the trace space.
            (routes(("fanout", finger, 30.0), ("fanout", finger, 30.45)), 0, None),
        )
        for synthetic, violations, measured in cases:
            def mutate(board, synthetic=synthetic):
                board["layers"]["top_copper"]["routes"] = synthetic

            report = self._mutated(self.row, mutate)
            record = report["measurements"]["checks"]["route_route_clearance"]
            with self.subTest(routes=[(route["segment"], route["width_mm"]) for route in synthetic]):
                self.assertEqual(record["required_mm"], space)
                self.assertGreater(record["measured_mm"], space)  # the trace space alone passes
                self.assertEqual((record["violation_count"], record["passed"]), (violations, not violations))
                self.assertEqual(record["finger_section"]["required_mm"], finger_space)
                self.assertEqual(record["finger_section"]["violation_count"], violations)
                self.assertEqual(report["measurements"]["inter_net_clearance_violation_segment_pair_count"], violations)
                pair = report["measurements"]["closest_inter_net_route_pair"]
                self.assertEqual(dict(zip(pair["nets"], pair["segments"])), {route["net"]: route["segment"] for route in synthetic})
                if measured is None:
                    self.assertIsNone(record["finger_section"]["measured_mm"])
                    self.assertNotIn("E_ROUTE_CLEARANCE", _codes(report["errors"]))
                else:
                    self.assertAlmostEqual(record["finger_section"]["measured_mm"], measured, places=6)
                    message = next(issue["message"] for issue in report["errors"] if issue["code"] == "E_ROUTE_CLEARANCE")
                    self.assertIn("between a tail piece and another net's route", message)
                    self.assertIn(f"at least {finger_space:.6f} required (finger section", message)

    def test_each_rule_fires_on_a_mutated_layout_with_a_board_field_path(self) -> None:
        def move_electrode(board):
            electrode = board["layers"]["top_copper"]["electrodes"][0]
            electrode["x"] = round(electrode["x"] - 0.6, 6)

        def squeeze_pad(board):
            pad = board["layers"]["top_copper"]["pads"][1]
            pad["x"] = round(pad["x"] - 0.1, 6)

        def widen_electrode(board):
            board["layers"]["top_copper"]["electrodes"][0]["width_mm"] += 0.5

        def opening_out(board):
            board["layers"]["top_coverlay_openings"][0]["x"] -= 5.0

        def split_opening(board):
            opening = board["layers"]["top_coverlay_openings"][0]
            half = dict(opening, width_mm=round(opening["width_mm"] / 2 - 0.15, 6))
            other = dict(half, x=round(opening["x"] + opening["width_mm"] / 2 + 0.15, 6))
            board["layers"]["top_coverlay_openings"][0:1] = [half, other]

        def shift_stiffener(board):
            stiffener = board["layers"]["bottom_stiffener"][0]
            stiffener["points"] = [[x - 0.5, y] for x, y in stiffener["points"]]

        def bow_tie(board):
            points = board["outline"]["points"]
            points[1], points[2] = points[2], points[1]

        def detach_route(board):
            route = board["layers"]["top_copper"]["routes"][3]
            route["points"][-1] = [route["points"][-1][0] - 0.0, route["points"][-1][1] - 0.15]

        def thin_electrode(board):
            electrode = board["layers"]["top_copper"]["electrodes"][2]
            electrode["width_mm"] = 0.05

        def short_contact(board):
            board["layers"]["top_copper"]["pads"][0]["height_mm"] = 3.0

        def huge(board):
            board["outline"]["points"] = [[x * 8, y * 8] for x, y in board["outline"]["points"]]

        def sharp_notch(board):
            # Re-introduce the old unfilleted tail-root corner of the row board.
            tail = board["tail"]["bounds"]
            top = tail["y"] + tail["height"]
            right = tail["x"] + tail["width"]
            points = [point for point in board["outline"]["points"] if not (right - 1e-9 <= point[0] <= right + 0.6 and top - 0.6 <= point[1] <= top + 1e-9)]
            index = next(i for i, point in enumerate(points) if abs(point[0] - right) < 1e-9 and point[1] < top - 0.6) + 1
            points[index:index] = [[right, top], [right + 0.6, top]]
            board["outline"]["points"] = points

        def pinch_neck(board):
            neck = board["tail"]["neck_bounds"]
            board["tail"]["width_mm"] = neck["width"] + 2.0

        def slot_to_edge(board):
            board["outline"]["cutouts"][0] = [[x - 26.0, y] for x, y in board["outline"]["cutouts"][0]]

        def route_into_slot_margin(board):
            slot = board["outline"]["cutouts"][0]
            left = min(point[0] for point in slot)
            # COL_16 is the left lane's route next to the slot.
            route = next(r for r in board["layers"]["top_copper"]["routes"] if r["net"] == "COL_16" and r["segment"] == "fanout")
            route["points"] = [[left - 0.2, y] if abs(x - (left - 0.75)) < 1e-6 else [x, y] for x, y in route["points"]]

        def shrink_gang_window(board):
            window = next(o for o in board["layers"]["top_coverlay_openings"] if o["kind"] == "connector_contact_opening")
            window["width_mm"] = round(window["width_mm"] - 0.3, 6)

        def lead_toward_neighbor(board):
            # ROW_01 runs in the leftmost lane; push it 0.15 mm towards contact 2.
            route = next(route for route in board["layers"]["top_copper"]["routes"] if route["net"] == "ROW_01")
            x0 = route["points"][0][0]
            route["points"] = [[x + 0.15, y] if abs(x - x0) < 1e-9 else [x, y] for x, y in route["points"]]

        def stub_toward_neighbor(board):
            route = next(r for r in board["layers"]["top_copper"]["routes"] if r["net"] == "COL_03" and r["segment"] == "fanout")
            # 1.2 mm sideways leaves 0.0365 mm of the 0.127 mm stub to the neighbouring electrode.
            route["points"][-1][0] += 1.2
            route["points"][-2][0] += 1.2

        def opening_beside_trace(board):
            opening = next(o for o in board["layers"]["top_coverlay_openings"] if o["kind"] == "sensor_electrode_opening")
            # 1.1 mm sideways leaves 0.0865 mm to the next column's 0.127 mm stub.
            opening["x"] = round(opening["x"] + 1.1, 6)

        def wide_fanout(board):
            # A fan-out piece drawn at the finger width instead of the bundle width.
            route = next(r for r in board["layers"]["top_copper"]["routes"] if r["segment"] == "fanout")
            route["width_mm"] = self.profile["routing"]["finger_trace_width_mm"]

        def thin_tail(board):
            # A tail piece at the 18 um copper minimum (0.0889 mm), below 1 oz copper's 0.1016 mm.
            route = next(r for r in board["layers"]["top_copper"]["routes"] if r["segment"] == "tail")
            route["width_mm"] = 0.0889

        def unsegmented(board):
            board["layers"]["top_copper"]["routes"][0].pop("segment")

        def below_copper_minimum(board):
            # Every fan-out piece 0.095 mm wide, as a design asking for 0.095 mm would draw it:
            # its own width, but below the 1 oz minimum (0.1016 mm).
            for route in board["layers"]["top_copper"]["routes"]:
                if route["segment"] == "fanout":
                    route["width_mm"] = 0.095

        def pad_far_away(board):
            board["layers"]["top_copper"]["pads"][-1]["x"] += 500.0

        def pad_beside_electrode(board):
            electrode = board["layers"]["top_copper"]["electrodes"][0]
            pad = board["layers"]["top_copper"]["pads"][-1]
            pad["x"] = round(electrode["x"] + electrode["width_mm"] + 0.1 + pad["width_mm"] / 2, 6)
            pad["y"] = round(electrode["y"] + electrode["height_mm"] / 2, 6)

        def fold_back(board):
            # A zero-width spike: the outline runs 1 mm past a corner and returns.
            points = board["outline"]["points"]
            (ax, ay), (bx, by) = points[0], points[1]
            length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
            points[2:2] = [[bx + (bx - ax) / length, by + (by - ay) / length], [bx, by]]

        def contacts_off_center(board):
            # Same pitch, but the contact row is no longer centred on the tail.
            for pad in board["layers"]["top_copper"]["pads"]:
                pad["x"] = round(pad["x"] + 0.04, 6)

        def narrow_body(board):
            # Pull the far body edge 0.5 mm towards the taxel field.
            right = max(x for x, _ in board["outline"]["points"])
            board["outline"]["points"] = [[x - 0.5 if x > right - 1.0 else x, y] for x, y in board["outline"]["points"]]

        def _stiffener_far_end(board, delta):
            stiffener = board["layers"]["bottom_stiffener"][0]
            top = max(y for _, y in stiffener["points"])
            stiffener["points"] = [[x, round(y + delta, 6) if y == top else y] for x, y in stiffener["points"]]

        def short_stiffener(board):
            _stiffener_far_end(board, -1.0)  # 5 mm: shorter than the connector's 6 mm zone

        def long_stiffener(board):
            _stiffener_far_end(board, 0.6)  # leaves 0.4 mm of flexible tail before the fan-out

        separate = generate_design({"matrix": {"taxel_width_mm": 1.3, "taxel_height_mm": 1.3}})["boards"]["column"]
        cases = (
            (self.column, pad_far_away, "E_COPPER_OUTLINE", "boards.column.outline.points"),
            (self.column, pad_beside_electrode, "E_ELECTRODE_PAD_CLEARANCE", "boards.column.layers.top_copper.electrodes"),
            (self.column, slot_to_edge, "E_CUTOUT_OUTLINE", "boards.column.outline.cutouts"),
            (self.column, route_into_slot_margin, "E_COPPER_CUTOUT_CLEARANCE", "boards.column.outline.cutouts"),
            (self.row, shrink_gang_window, "E_CONTACT_EXPOSURE", "boards.row.layers.top_coverlay_openings"),
            (self.row, lead_toward_neighbor, "E_PAD_TRACE_CLEARANCE", "boards.row.layers.top_copper.pads"),
            (self.column, stub_toward_neighbor, "E_ELECTRODE_ROUTE_CLEARANCE", "boards.column.layers.top_copper.electrodes"),
            (separate, opening_beside_trace, "E_COVERLAY_TRACE_CLEARANCE", "boards.column.layers.top_coverlay_openings"),
            (self.column, move_electrode, "E_COPPER_EDGE_CLEARANCE", "boards.column.outline.points"),
            (self.row, squeeze_pad, "E_PAD_CLEARANCE", "boards.row.layers.top_copper.pads"),
            (self.column, widen_electrode, "E_ELECTRODE_CLEARANCE", "boards.column.layers.top_copper.electrodes"),
            (self.column, opening_out, "E_COVERLAY_OUTLINE", "boards.column.layers.top_coverlay_openings"),
            (self.row, split_opening, "E_COVERLAY_BRIDGE", "boards.row.layers.top_coverlay_openings"),
            (self.column, shift_stiffener, "E_STIFFENER_OUTLINE", "boards.column.layers.bottom_stiffener"),
            (self.row, bow_tie, "E_OUTLINE_SELF_INTERSECTION", "boards.row.outline.points"),
            (self.row, fold_back, "E_OUTLINE_SELF_INTERSECTION", "boards.row.outline.points"),
            (self.column, detach_route, "E_CONNECTIVITY", "boards.column.layers.top_copper.routes"),
            (self.column, wide_fanout, "E_ROUTE_WIDTH", "boards.column.layers.top_copper.routes"),
            (self.row, thin_tail, "E_ROUTE_WIDTH", "boards.row.layers.top_copper.routes"),
            (self.row, unsegmented, "E_ROUTE_WIDTH", "boards.row.layers.top_copper.routes"),
            (self.column, thin_electrode, "E_ELECTRODE_WIDTH", "boards.column.layers.top_copper.electrodes"),
            (self.row, short_contact, "E_CONNECTOR_TAIL", "boards.row.layers.top_copper.pads"),
            (self.column, contacts_off_center, "E_CONNECTOR_TAIL", "boards.column.layers.top_copper.pads"),
            (self.row, huge, "E_BOARD_SIZE", "boards.row.outline.points"),
            (self.row, sharp_notch, "E_CONCAVE_CORNER", "boards.row.outline.points"),
            (self.column, pinch_neck, "E_NECK_WIDTH", "boards.column.outline.points"),
            (self.row, narrow_body, "E_ACTIVE_MARGIN", "boards.row.outline.points"),
            (self.row, short_stiffener, "E_STIFFENER_ZONE", "boards.row.layers.bottom_stiffener"),
            (self.column, long_stiffener, "E_STIFFENER_ZONE", "boards.column.layers.bottom_stiffener"),
        )
        # The DRC takes the bundle width from the design: this one bypassed validation.
        thin_design = copy.deepcopy(self.result["design"])
        thin_design["routing"]["trace_width_mm"] = 0.095
        thin = verify_board(_edited(self.row, below_copper_minimum), self.profile, thin_design)
        self.assertEqual(thin["measurements"]["checks"]["route_width"]["measured_mm"], 0.0)
        self.assertIn(("E_ROUTE_WIDTH", "boards.row.layers.top_copper.routes"), {(e["code"], e["field"]) for e in thin["errors"]})
        for board, mutate, code, field in cases:
            with self.subTest(code=code):
                errors = self._mutated(board, mutate)["errors"]
                self.assertIn((code, field), {(issue["code"], issue["field"]) for issue in errors})
                # Field paths name the real result keys (boards.row / boards.column).
                self.assertTrue(all(issue["field"].startswith(("boards.row.", "boards.column.")) for issue in errors))

    def test_a_tiny_fillet_is_a_sharp_corner(self) -> None:
        # Review finding F2: a 0.01 mm fillet drawn in 10 degree steps passes
        # the per-vertex turn limit; its effective radius must fail.
        board = copy.deepcopy(self.row)
        tail = board["tail"]["bounds"]
        top, right = tail["y"] + tail["height"], tail["x"] + tail["width"]
        radius = self.profile["outline"]["outline_fillet_radius_mm"]
        points = board["outline"]["points"]
        arc = [i for i, (x, y) in enumerate(points) if right - 1e-9 <= x <= right + radius + 1e-9 and top - radius - 1e-9 <= y <= top + 1e-9]
        self.assertEqual(arc, list(range(arc[0], arc[0] + len(arc))))
        tiny = 0.01
        replacement = [
            [round(right + tiny + tiny * math.cos(math.radians(180 - 10 * step)), 6), round(top - tiny + tiny * math.sin(math.radians(180 - 10 * step)), 6)]
            for step in range(10)
        ]
        board["outline"]["points"] = points[: arc[0]] + replacement + points[arc[-1] + 1 :]
        report = verify_board(board, self.profile, self.result["design"])
        checks = report["measurements"]["checks"]
        self.assertTrue(checks["unfilleted_concave_turn_deg"]["passed"], checks["unfilleted_concave_turn_deg"])
        self.assertFalse(checks["concave_fillet_radius"]["passed"])
        self.assertLess(checks["concave_fillet_radius"]["measured_mm"], 2 * tiny)
        self.assertIn(("E_CONCAVE_CORNER", "boards.row.outline.points"), {(e["code"], e["field"]) for e in report["errors"]})
        # A routed slot whose corners are 0.005 mm arcs: four short runs of
        # small turns joined by long edges, each a sharp corner of the board.
        column = copy.deepcopy(self.column)
        x0, y0, width, height = (column["construction"]["slot_bounds"][key] for key in ("x", "y", "width", "height"))
        tiny = 0.005
        corners = ((x0 + width - tiny, y0 + tiny, -90), (x0 + width - tiny, y0 + height - tiny, 0), (x0 + tiny, y0 + height - tiny, 90), (x0 + tiny, y0 + tiny, 180))
        column["outline"]["cutouts"] = [[
            [round(cx + tiny * math.cos(math.radians(start + 10 * step)), 6), round(cy + tiny * math.sin(math.radians(start + 10 * step)), 6)]
            for cx, cy, start in corners
            for step in range(10)
        ]]
        checks = verify_board(column, self.profile, self.result["design"])["measurements"]["checks"]
        self.assertTrue(checks["unfilleted_concave_turn_deg"]["passed"], checks["unfilleted_concave_turn_deg"])
        self.assertFalse(checks["concave_fillet_radius"]["passed"])
        self.assertLess(checks["concave_fillet_radius"]["measured_mm"], 2 * tiny)

    def test_self_intersection_count_is_exact(self) -> None:
        from engine.drc import _self_intersections

        self.assertEqual(_self_intersections([[0.0, 0.0], [4.0, 0.0], [0.0, 3.0]]), 0)
        self.assertEqual(_self_intersections([[0.0, 0.0], [2.0, 2.0], [2.0, 0.0], [0.0, 2.0]]), 1)  # bow tie
        # A zero-area ring has no non-adjacent edge pair at all; it folds back at
        # (0, 0) and (4, 0).
        self.assertEqual(_self_intersections([[0.0, 0.0], [4.0, 0.0], [2.0, 0.0]]), 2)

    def test_missing_openings_are_reported_with_finite_values(self) -> None:
        board = copy.deepcopy(self.row)
        board["layers"]["top_coverlay_openings"] = []
        report = verify_board(board, self.profile, self.result["design"])
        self.assertIn("E_CONTACT_EXPOSURE", _codes(report["errors"]))
        json.dumps(report, allow_nan=False)  # every recorded measurement stays finite

    def test_repeated_outline_vertices_are_not_defects(self) -> None:
        board = copy.deepcopy(self.row)
        points = board["outline"]["points"]
        points.insert(3, list(points[3]))
        points.append(list(points[0]))
        report = verify_board(board, self.profile, self.result["design"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["measurements"]["checks"]["outline_simple"]["violation_count"], 0)

    def test_route_to_edge_has_no_hidden_tolerance(self) -> None:
        # Pull the outer left lane of the row board to 0.2995 mm copper from the
        # edge: the former 5 um tolerance passed such boards (audit L4).
        board = copy.deepcopy(self.row)
        route = next(route for route in board["layers"]["top_copper"]["routes"] if route["points"][0][0] == min(r["points"][0][0] for r in board["layers"]["top_copper"]["routes"]))
        shift = route["points"][0][0] - (0.127 + 0.2995)
        route["points"] = [[x - shift, y] if abs(x - route["points"][0][0]) < 1e-9 else [x, y] for x, y in route["points"]]
        report = verify_board(board, self.profile, self.result["design"])
        self.assertIn("E_ROUTE_EDGE_CLEARANCE", _codes(report["errors"]))
        self.assertAlmostEqual(report["measurements"]["checks"]["route_to_outline"]["measured_mm"], 0.2995, places=6)


class RegistrationTests(unittest.TestCase):
    def test_quarter_turn_mixed_sides_are_rejected_and_others_register(self) -> None:
        for row_side in SIDES:
            for column_side in SIDES:
                for mapping in ({"top": "rows", "bottom": "columns"}, {"top": "columns", "bottom": "rows"}):
                    result = generate_design({"tail": {"row_side": row_side, "column_side": column_side}, "role_mapping": mapping})
                    quarter = (SIDES.index(row_side) - SIDES.index(column_side)) % 2 == 1
                    with self.subTest(row_side=row_side, column_side=column_side, mapping=mapping["top"]):
                        if quarter:
                            self.assertFalse(result["ok"])
                            self.assertEqual(result["boards"], {})
                            errors = result["validation"]["errors"]
                            self.assertEqual([(e["code"], e["field"]) for e in errors], [("E_TAIL_SIDE_PARALLEL", "tail.column_side")])
                        else:
                            self.assertTrue(result["ok"], result["validation"]["errors"])
                            registration = result["boards"]["row"]["verification"]["registration"]
                            self.assertTrue(registration["orthogonal"])
                            self.assertTrue(registration["identical_active_region"])
                            self.assertNotEqual(registration["row_electrode_axis"], registration["column_electrode_axis"])

    def test_registration_requires_the_electrodes_on_the_taxel_field(self) -> None:
        profile = load_profile()
        result = generate_design()
        row = copy.deepcopy(result["boards"]["row"])
        for electrode in row["layers"]["top_copper"]["electrodes"]:
            electrode["y"] = round(electrode["y"] + 0.1, 6)  # spacing intact, grid shifted off the field
        report = verify_registration(row, result["boards"]["column"], profile)
        self.assertTrue(report["measurements"]["orthogonal"])
        self.assertFalse(report["measurements"]["row_grid_matches"])
        self.assertAlmostEqual(report["measurements"]["row_grid_deviation_mm"], 0.1, places=6)
        # Each failing sub-check names the board data it measured (review
        # finding F3: grid errors used to point at tail.column_side).
        self.assertEqual(
            [(issue["code"], issue["field"]) for issue in report["errors"]],
            [("E_REGISTRATION", "boards.row.layers.top_copper.electrodes")],
        )
        self.assertIn("0.100000 mm", report["errors"][0]["message"])
        column = copy.deepcopy(result["boards"]["column"])
        for electrode in column["layers"]["top_copper"]["electrodes"]:
            electrode["height_mm"] = round(electrode["height_mm"] - 0.2, 6)  # no overhang at the far end
        report = verify_registration(result["boards"]["row"], column, profile)
        self.assertFalse(report["measurements"]["column_grid_matches"])
        self.assertEqual([issue["field"] for issue in report["errors"]], ["boards.column.layers.top_copper.electrodes"])
        resized = copy.deepcopy(result["boards"]["column"])
        resized["grid_registration"]["active_region"]["width"] += 0.05
        report = verify_registration(result["boards"]["row"], resized, profile)
        self.assertFalse(report["measurements"]["identical_active_region"])
        self.assertAlmostEqual(report["measurements"]["active_region_size_deviation_mm"], 0.05, places=6)
        self.assertIn("boards.column.grid_registration.active_region", [issue["field"] for issue in report["errors"]])

    def test_registration_check_catches_parallel_boards(self) -> None:
        profile = load_profile()
        result = generate_design()
        column = copy.deepcopy(result["boards"]["column"])
        apply_tail_side(column, "right")  # bypasses validation on purpose
        report = verify_registration(result["boards"]["row"], column, profile)
        self.assertFalse(report["measurements"]["orthogonal"])
        # Parallel electrodes are the one registration failure a design input
        # (the tail sides) causes; grids are not compared on parallel boards.
        self.assertEqual([(issue["code"], issue["field"]) for issue in report["errors"]], [("E_REGISTRATION", "tail.column_side")])


class FeasibilityTests(unittest.TestCase):
    def test_legal_inputs_generate_clean_boards_or_fail_with_field_bounds(self) -> None:
        # Audit H1: most of the legal pitch range used to fail only after
        # generation, with DRC errors naming no design field.
        design_fields = {"matrix.pitch_x_mm", "matrix.pitch_y_mm", "matrix.rows", "matrix.columns", "tail.top_length_mm", "tail.bottom_length_mm"}
        outcomes = {"ok": 0, "rejected": 0}
        narrowest = load_profile()["routing"]["min_electrode_width_mm"]
        for columns in (1, 16, 17, 32):
            for pitch in (0.6, 0.75, 1.0, 1.5, 2.5, 4.0, 7.0, 10.0):
                for width in (narrowest, round(pitch - 0.25, 6)):
                    result = generate_design({"matrix": {"columns": columns, "pitch_x_mm": pitch, "taxel_width_mm": width}})
                    with self.subTest(columns=columns, pitch=pitch, width=width):
                        if result["ok"]:
                            outcomes["ok"] += 1
                            for board in result["boards"].values():
                                self.assertTrue(board["verification"]["all_checks_passed"], board["id"])
                        else:
                            outcomes["rejected"] += 1
                            self.assertEqual(result["boards"], {})
                            for error in result["validation"]["errors"]:
                                self.assertEqual(error["code"], "E_BOARD_SIZE")
                                self.assertIn(error["field"], design_fields)
                                self.assertRegex(error["message"], re.escape(error["field"]) + r" (<=|must be at least) [0-9]")
        self.assertGreater(outcomes["ok"], outcomes["rejected"])

    def test_high_precision_inputs_never_fail_after_generation(self) -> None:
        # Review finding F1: inputs with more than 6 decimals (computed
        # values) failed only after generation, because rules met exactly were
        # checked on independently rounded coordinates.  The geometry is now
        # built from the inputs taken on the 1e-6 mm layout grid.
        rng = random.Random(20261014)
        designs = [
            {"matrix": {"taxel_width_mm": 1.2999995, "taxel_height_mm": 1.2999995}},
            {"matrix": {"rows": 1, "columns": 4, "pitch_x_mm": 7.531631, "pitch_y_mm": 8.239666, "taxel_width_mm": 6.83163, "taxel_height_mm": 7.989666},
             "tail": {"top_length_mm": 75.340375, "bottom_length_mm": 80.0}},
            {"matrix": {"rows": 36, "columns": 26, "pitch_x_mm": 1.599718, "pitch_y_mm": 3.522238, "taxel_width_mm": 0.384507, "taxel_height_mm": 1.669912},
             "tail": {"top_length_mm": 8.900976, "bottom_length_mm": 7.0}, "connector": {"column_pins": 57}, "role_mapping": {"top": "columns", "bottom": "rows"}},
            # Coverlay bridges of exactly 0.5 mm (kept separate) and one grid step less (merged).
            {"matrix": {"columns": 5, "pitch_x_mm": 3.248274, "taxel_width_mm": 2.548274}},
            {"matrix": {"columns": 5, "pitch_x_mm": 3.248274, "taxel_width_mm": 2.548275}},
        ]
        for _ in range(24):
            px, py = rng.uniform(0.6, 4.0), rng.uniform(0.6, 4.0)
            side = rng.choice(SIDES)
            designs.append(
                {
                    "matrix": {"rows": rng.randint(1, 64), "columns": rng.randint(1, 32), "pitch_x_mm": px, "pitch_y_mm": py,
                               "taxel_width_mm": rng.uniform(0.1016, px - 0.25), "taxel_height_mm": rng.uniform(0.1016, py - 0.25)},
                    "tail": {"top_length_mm": rng.uniform(7.0, 40.0), "bottom_length_mm": rng.uniform(7.0, 40.0),
                             "row_side": side, "column_side": rng.choice((side, SIDES[(SIDES.index(side) + 2) % 4]))},
                    "connector": {"row_pins": None, "column_pins": rng.choice((None, 64))},
                    # Bundle traces anywhere in their range, at full precision.
                    "routing": {"trace_width_mm": rng.uniform(0.1016, 0.254), "trace_space_mm": rng.uniform(0.1016, 0.246)},
                }
            )
        # Values that round in opposite directions: 0.2499999998 mm of raw gap
        # becomes 0.249999 mm on the grid, so validation (on grid values)
        # rejects it before any geometry, with a bound that works.
        halfway = generate_design({"matrix": {"columns": 8, "pitch_x_mm": 1.2000004999, "taxel_width_mm": 0.9500005001}})
        self.assertEqual([(e["code"], e["field"]) for e in halfway["validation"]["errors"]], [("E_ELECTRODE_GAP", "matrix.taxel_width_mm")])
        self.assertEqual(halfway["boards"], {})
        generated = 0
        for design in designs:
            result = generate_design(design)
            with self.subTest(design=design):
                self.assertEqual([issue for issue in result["validation"]["errors"] if issue["field"].startswith("boards.")], [])
                if result["ok"]:
                    generated += 1
                    for board in result["boards"].values():
                        self.assertTrue(board["verification"]["all_checks_passed"], board["id"])
                    grid = result["boards"]["column"]["grid_registration"]
                    self.assertEqual(grid["pitch_x_mm"], round(result["design"]["matrix"]["pitch_x_mm"], 6))
        self.assertGreaterEqual(generated, 20)
        kinds = lambda design: sorted(o["kind"] for o in generate_design(design)["boards"]["column"]["layers"]["top_coverlay_openings"])
        self.assertEqual(kinds(designs[3]).count("sensor_electrode_opening"), 5)
        self.assertIn("electrode_field_opening", kinds(designs[4]))


class SpeedAndDeterminismTests(unittest.TestCase):
    def _best_time(self, design) -> float:
        best = float("inf")
        for _ in range(2):
            start = time.perf_counter()
            result = generate_design(design)
            best = min(best, time.perf_counter() - start)
            self.assertTrue(result["ok"], result["validation"]["errors"])
        return best

    def test_generation_including_drc_is_fast(self) -> None:
        self.assertLess(self._best_time({}), 1.5)
        heavy = {
            "matrix": {"rows": 64, "columns": 32, "pitch_x_mm": 3.0, "pitch_y_mm": 3.0},
            "tail": {"top_length_mm": 80.0, "bottom_length_mm": 80.0},
            "connector": {"row_pins": 64, "column_pins": 64},
        }
        self.assertLess(self._best_time(heavy), 5.0)

    def test_layout_json_is_identical_across_hash_seeds(self) -> None:
        script = (
            "import json, sys; sys.path.insert(0, %r); from engine import generate_design; "
            "r = generate_design({'rows': 5, 'columns': 17, 'connector': {'row_pins': 9}, 'connector_side': 'left'}); "
            "sys.stdout.write(json.dumps(r, sort_keys=True))" % str(ROOT)
        )
        outputs = set()
        for seed in ("0", "1", "4242"):
            environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
            outputs.add(subprocess.run([sys.executable, "-B", "-c", script], env=environment, capture_output=True, check=True).stdout)
        self.assertEqual(len(outputs), 1)
        self.assertTrue(json.loads(outputs.pop())["ok"])


if __name__ == "__main__":
    unittest.main()
