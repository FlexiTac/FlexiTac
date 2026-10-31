"""Regression tests for the source-independent deterministic sensor core."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from engine import default_design, generate_design

try:
    from geometry_checks import straight_channel
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel


class SensorCoreTests(unittest.TestCase):
    def test_default_preset_generates_two_independent_fpcs(self) -> None:
        result = generate_design()

        self.assertTrue(result["ok"], result["validation"])
        self.assertEqual(set(result["boards"]), {"row", "column"})
        self.assertEqual(result["design"]["template_id"], "generic_matrix_v1")
        self.assertEqual(result["boards"]["row"]["physical_side"], "top")
        self.assertEqual(result["boards"]["column"]["physical_side"], "bottom")
        self.assertEqual(len(result["boards"]["row"]["layers"]["top_copper"]["electrodes"]), 12)
        self.assertEqual(len(result["boards"]["column"]["layers"]["top_copper"]["electrodes"]), 32)
        self.assertEqual(result["boards"]["row"]["grid_registration"]["active_region"]["width"], 63.4)
        self.assertEqual(result["boards"]["row"]["grid_registration"]["active_region"]["height"], 23.4)
        self.assertIn("<svg", result["boards"]["row"]["svg"])
        self.assertIs(result["derived_layout"]["boards"], result["boards"])

    def test_stiffener_is_a_bounded_bottom_pi_tail_feature_of_the_profile_thickness(self) -> None:
        result = generate_design()
        stackup = result["profile"]["stackup"]
        # The profile's PI thickness (0.225 mm since 2026-10-14), a JLC option.
        self.assertIn(stackup["stiffener_thickness_mm"], result["profile"]["fabrication"]["pi_stiffener_thickness_options_mm"])
        for board in result["boards"].values():
            stiffeners = board["layers"]["bottom_stiffener"]
            self.assertEqual(len(stiffeners), 1)
            stiffener = stiffeners[0]
            self.assertEqual(stiffener["layer"], "bottom_stiffener")
            self.assertEqual(stiffener["side"], "bottom")
            self.assertEqual(stiffener["material"], "polyimide")
            self.assertEqual(stiffener["thickness_mm"], stackup["stiffener_thickness_mm"])
            xs = [point[0] for point in stiffener["points"]]
            ys = [point[1] for point in stiffener["points"]]
            # Regression for the historical error where a tail stiffener was
            # accidentally expanded across the complete sensing board.
            self.assertLess(max(xs) - min(xs), board["metrics"]["outline_width_mm"])
            self.assertLess(max(ys) - min(ys), board["metrics"]["outline_height_mm"])

    def test_flat_web_form_aliases_normalize_to_schema(self) -> None:
        result = generate_design(
            {
                "name": "Demo 4 x 5",
                "rows": 4,
                "columns": 5,
                "pitch_x_mm": 2.5,
                "pitch_y_mm": 2.0,
                "row_electrode_width_mm": 1.0,
                "column_electrode_width_mm": 1.1,
                "tail_length_mm": 9.0,
                "connector_side": "right",
                "row_fpc_position": "bottom",
                "scan_order": "reverse",
            }
        )

        self.assertTrue(result["ok"], result["validation"])
        self.assertEqual(result["design"]["project_name"], "Demo 4 x 5")
        self.assertEqual(result["design"]["matrix"]["taxel_height_mm"], 1.0)
        self.assertEqual(result["design"]["matrix"]["taxel_width_mm"], 1.1)
        self.assertEqual(result["design"]["role_mapping"], {"top": "columns", "bottom": "rows"})
        self.assertEqual(result["boards"]["row"]["physical_side"], "bottom")
        self.assertEqual(result["boards"]["row"]["tail"]["side"], "right")
        self.assertEqual(result["boards"]["column"]["tail"]["side"], "right")
        self.assertTrue(result["manifest"]["build_id"].startswith("demo-4-x-5-"))

    def test_invalid_taxel_geometry_never_emits_layout(self) -> None:
        result = generate_design({"matrix": {"pitch_x_mm": 1.0, "taxel_width_mm": 0.9}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["boards"], {})
        self.assertTrue(any(issue["code"] == "E_ELECTRODE_GAP" for issue in result["validation"]["errors"]))
        self.assertFalse(result["manifest"]["geometry_valid"])
        self.assertFalse(result["manifest"]["production_ready"])

    def test_malformed_subobject_is_reported_without_crashing(self) -> None:
        result = generate_design({"matrix": "not an object", "role_mapping": ["rows", "columns"]})

        self.assertFalse(result["ok"])
        codes = {issue["code"] for issue in result["validation"]["errors"]}
        self.assertIn("E_MATRIX_OBJECT", codes)
        self.assertIn("E_ROLE_MAPPING", codes)

    def test_generation_is_deterministic_and_json_serializable(self) -> None:
        first = generate_design(default_design())
        second = generate_design(default_design())

        self.assertTrue(first["ok"])
        self.assertEqual(first["manifest"]["design_sha256"], second["manifest"]["design_sha256"])
        self.assertEqual(first["boards"], second["boards"])
        json.dumps(first, sort_keys=True, allow_nan=False)

    def test_flat_and_nested_inputs_have_the_same_canonical_design_digest(self) -> None:
        nested = generate_design(
            {
                "project_name": "Equivalent Input",
                "matrix": {
                    "rows": 4,
                    "columns": 5,
                    "pitch_x_mm": 2.5,
                    "pitch_y_mm": 2.0,
                    "taxel_width_mm": 1.1,
                    "taxel_height_mm": 1.0,
                },
                "tail": {"length_mm": 9.0, "row_side": "left", "column_side": "left"},
                "role_mapping": {"top": "columns", "bottom": "rows"},
                "channel_order": {"rows": "descending", "columns": "descending"},
            }
        )
        flat = generate_design(
            {
                "name": "Equivalent Input",
                "rows": 4,
                "columns": 5,
                "pitch_x_mm": 2.5,
                "pitch_y_mm": 2.0,
                "row_electrode_width_mm": 1.0,
                "column_electrode_width_mm": 1.1,
                "tail_length_mm": 9.0,
                "connector_side": "left",
                "row_fpc_position": "bottom",
                "scan_order": "reverse",
            }
        )

        self.assertTrue(nested["ok"], nested["validation"])
        self.assertTrue(flat["ok"], flat["validation"])
        self.assertEqual(nested["design"], flat["design"])
        self.assertEqual(nested["manifest"]["design_sha256"], flat["manifest"]["design_sha256"])

    def test_core_does_not_depend_on_caller_working_directory(self) -> None:
        original = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                os.chdir(temporary_directory)
                result = generate_design()
        finally:
            os.chdir(original)
        self.assertTrue(result["ok"], result["validation"])

    def test_manifest_is_never_a_manufacturing_approval(self) -> None:
        result = generate_design()
        manifest = result["manifest"]
        self.assertTrue(manifest["geometry_valid"])
        self.assertFalse(manifest["production_ready"])
        self.assertEqual(manifest["output_status"], "geometry_only")
        self.assertTrue(manifest["requires_final_jlc_review"])

    def test_column_tail_length_is_a_real_outline_and_connector_extension(self) -> None:
        # The default's diagonal Row bus takes CAD mode's rules: tails of 7.5 mm or more (P5-diagonal-bus.md section 20).
        short = generate_design({"tail_length_mm": 7.5})
        long = generate_design({"tail_length_mm": 20.0})
        self.assertTrue(short["ok"], short["validation"])
        self.assertTrue(long["ok"], long["validation"])
        short_board = short["boards"]["column"]
        long_board = long["boards"]["column"]
        self.assertEqual(short_board["tail"]["length_mm"], 7.5)
        self.assertEqual(long_board["tail"]["length_mm"], 20.0)
        self.assertAlmostEqual(
            long_board["metrics"]["outline_height_mm"] - short_board["metrics"]["outline_height_mm"],
            12.5,
        )
        short_pads = short_board["layers"]["top_copper"]["pads"]
        long_pads = long_board["layers"]["top_copper"]["pads"]
        self.assertEqual(len(short_pads), len(long_pads))
        # Boards are normalized at the connector end, so the pad coordinate
        # remains stable while the active sensor moves farther away from it.
        self.assertAlmostEqual(long_pads[0]["y"], short_pads[0]["y"])
        self.assertAlmostEqual(
            long_board["grid_registration"]["active_region"]["y"]
            - short_board["grid_registration"]["active_region"]["y"],
            12.5,
        )
        # The PI stiffener is a fixed connector zone flush with the tip (audit
        # M1): a longer tail adds flexible length, never stiff length.
        stiffener_length = short["profile"]["tail"]["stiffener_length_mm"]
        for board in (short_board, long_board):
            self.assertAlmostEqual(_polygon_height(board["layers"]["bottom_stiffener"][0]["points"]), stiffener_length)

    def test_top_and_bottom_tail_lengths_are_independent_physical_parameters(self) -> None:
        result = generate_design({"top_tail_length_mm": 7.5, "bottom_tail_length_mm": 20.0})
        self.assertTrue(result["ok"], result["validation"])
        self.assertEqual(result["boards"]["row"]["physical_side"], "top")
        self.assertEqual(result["boards"]["column"]["physical_side"], "bottom")
        self.assertEqual(result["boards"]["row"]["tail"]["length_mm"], 7.5)
        self.assertEqual(result["boards"]["column"]["tail"]["length_mm"], 20.0)

        swapped = generate_design(
            {
                "top_tail_length_mm": 7.5,
                "bottom_tail_length_mm": 20.0,
                "role_mapping": {"top": "columns", "bottom": "rows"},
            }
        )
        self.assertTrue(swapped["ok"], swapped["validation"])
        self.assertEqual(swapped["boards"]["row"]["tail"]["length_mm"], 20.0)
        self.assertEqual(swapped["boards"]["column"]["tail"]["length_mm"], 7.5)

    def test_over_16_columns_use_two_dense_lanes_and_one_connector(self) -> None:
        # The straight Row channel's Column board (the diagonal Row bus's converges in one V: test_generic_bus).
        for columns, expected_groups in ((20, [10, 10]), (32, [16, 16])):
            result = generate_design(straight_channel({"columns": columns}))
            self.assertTrue(result["ok"], result["validation"])
            board = result["boards"]["column"]
            self.assertEqual(board["tail"]["connector_channels"], columns)
            self.assertEqual(board["tail"]["fanout_lane_count"], 2)
            self.assertEqual(board["tail"]["fanout_lane_channel_counts"], expected_groups)
            self.assertEqual(len(board["layers"]["top_copper"]["pads"]), columns)
            self.assertEqual(len(board["outline"]["cutouts"]), 1)
            # Two pieces per net (tail and fan-out), both tagged with the lane.
            for segment in ("tail", "fanout"):
                groups = [route["fanout_group"] for route in board["layers"]["top_copper"]["routes"] if route["segment"] == segment]
                self.assertEqual(groups.count(1), expected_groups[0])
                self.assertEqual(groups.count(2), expected_groups[1])

    def test_compact_column_front_uses_short_safe_merger_profiles(self) -> None:
        single = generate_design(straight_channel({"columns": 16}))
        dual = generate_design(straight_channel({"columns": 32}))
        self.assertTrue(single["ok"], single["validation"])
        self.assertTrue(dual["ok"], dual["validation"])
        # The locked compact profile leaves the user-selected tail length
        # unchanged, but removes excess fixed lead-out/merger length.
        self.assertLess(single["boards"]["column"]["metrics"]["outline_height_mm"], 60.0)
        self.assertLess(dual["boards"]["column"]["metrics"]["outline_height_mm"], 80.0)
        dual_cutout = dual["boards"]["column"]["outline"]["cutouts"][0]
        self.assertAlmostEqual(_polygon_width(dual_cutout), 12.0)
        self.assertEqual(dual["boards"]["column"]["verification"]["inter_net_copper_overlap_segment_pair_count"], 0)

    def test_column_routes_are_contained_by_outline_and_clear_of_slot(self) -> None:
        result = generate_design({"columns": 32, "tail_length_mm": 7.5})
        self.assertTrue(result["ok"], result["validation"])
        board = result["boards"]["column"]
        outline = board["outline"]["points"]
        cutouts = board["outline"]["cutouts"]
        for route in board["layers"]["top_copper"]["routes"]:
            for first, second in zip(route["points"], route["points"][1:]):
                for index in range(101):
                    fraction = index / 100
                    point = [
                        first[0] + (second[0] - first[0]) * fraction,
                        first[1] + (second[1] - first[1]) * fraction,
                    ]
                    self.assertTrue(_inside_or_boundary(point, outline), (route["net"], point))
                    self.assertFalse(any(_strictly_inside(point, cutout) for cutout in cutouts), (route["net"], point))

    def test_post_generation_drc_proves_dense_column_merger_has_no_copper_overlap(self) -> None:
        result = generate_design(straight_channel({"columns": 32}))
        self.assertTrue(result["ok"], result["validation"])
        board = result["boards"]["column"]
        verification = result["boards"]["column"]["verification"]
        self.assertTrue(verification["route_clearance_passed"])
        self.assertTrue(verification["outline_containment_passed"])
        self.assertTrue(verification["cutout_clearance_passed"])
        self.assertEqual(verification["inter_net_copper_overlap_segment_pair_count"], 0)
        self.assertEqual(verification["inter_net_clearance_violation_segment_pair_count"], 0)
        self.assertGreaterEqual(
            verification["minimum_inter_net_copper_clearance_mm"],
            verification["minimum_required_inter_net_copper_clearance_mm"],
        )
        # The closest neighbours run in the bundle, exactly one bundle pitch apart.
        routing = result["design"]["routing"]
        bundle_pitch = round(routing["trace_width_mm"] + routing["trace_space_mm"], 6)
        self.assertEqual(verification["minimum_inter_net_center_distance_mm"], bundle_pitch)
        closest_pair = verification["closest_inter_net_route_pair"]
        self.assertIsNotNone(closest_pair)
        self.assertNotEqual(closest_pair["nets"][0], closest_pair["nets"][1])

        # Regression for the compact three-stage 32-channel topology:
        # both outer banks start inward immediately, run as two dense banks
        # around the slot, then merge to one connector at the tail.  The deck
        # is read where each route passes the slot's mid-height.
        routes = [route for route in board["layers"]["top_copper"]["routes"] if route["segment"] == "fanout"]
        slot = board["outline"]["cutouts"][0]
        slot_mid_y = (min(point[1] for point in slot) + max(point[1] for point in slot)) / 2
        left_outer = routes[0]
        right_outer = routes[-1]
        left_deck_x = _x_at_height(left_outer["points"], slot_mid_y)
        right_deck_x = _x_at_height(right_outer["points"], slot_mid_y)
        self.assertGreater(left_deck_x, left_outer["points"][-1][0])
        self.assertLess(right_deck_x, right_outer["points"][-1][0])
        left_deck = [_x_at_height(route["points"], slot_mid_y) for route in routes[:16]]
        right_deck = [_x_at_height(route["points"], slot_mid_y) for route in routes[16:]]
        self.assertTrue(all(abs(second - first - bundle_pitch) < 0.00001 for first, second in zip(left_deck, left_deck[1:])))
        self.assertTrue(all(abs(second - first - bundle_pitch) < 0.00001 for first, second in zip(right_deck, right_deck[1:])))
        self.assertLess(max(left_deck), min(point[0] for point in slot))
        self.assertGreater(min(right_deck), max(point[0] for point in slot))

    def test_row_outline_has_no_interior_edgecut_at_the_tail_body_junction(self) -> None:
        result = generate_design()
        self.assertTrue(result["ok"], result["validation"])
        row = result["boards"]["row"]
        # The generated DRC would flag any centreline intersection with the
        # outer loop.  This specifically protects the former erroneous
        # horizontal Edge.Cuts segment beneath the row fan-out.  The outline
        # now has rounded R0.3 tip corners and a filleted tail root (audit
        # C3/M2), so the check is structural rather than a vertex count.
        self.assertTrue(row["verification"]["outline_containment_passed"])
        self.assertTrue(row["verification"]["checks"]["outline_simple"]["passed"])
        tail = row["tail"]["bounds"]
        junction_y = tail["y"] + tail["height"]
        outline = row["outline"]["points"]
        for first, second in zip(outline, outline[1:] + outline[:1]):
            on_junction = abs(first[1] - junction_y) < 1e-9 and abs(second[1] - junction_y) < 1e-9
            # Any overlap of the edge's x-range with the tail span, including an
            # edge that starts exactly on a tail side.
            overlap = min(max(first[0], second[0]), tail["x"] + tail["width"]) - max(min(first[0], second[0]), tail["x"])
            self.assertFalse(on_junction and overlap > 1e-9, (first, second))


def _polygon_height(points: list[list[float]]) -> float:
    return max(point[1] for point in points) - min(point[1] for point in points)


def _x_at_height(points: list[list[float]], y: float) -> float:
    for first, second in zip(points, points[1:]):
        if min(first[1], second[1]) <= y <= max(first[1], second[1]) and first[1] != second[1]:
            return first[0] + (second[0] - first[0]) * (y - first[1]) / (second[1] - first[1])
    raise AssertionError(f"route does not reach y={y}")


def _polygon_width(points: list[list[float]]) -> float:
    return max(point[0] for point in points) - min(point[0] for point in points)


def _strictly_inside(point: list[float], polygon: list[list[float]]) -> bool:
    x, y = point
    inside = False
    for first, second in zip(polygon, polygon[1:] + polygon[:1]):
        x1, y1 = first
        x2, y2 = second
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _inside_or_boundary(point: list[float], polygon: list[list[float]]) -> bool:
    x, y = point
    for first, second in zip(polygon, polygon[1:] + polygon[:1]):
        x1, y1 = first
        x2, y2 = second
        cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        if abs(cross) < 0.000001 and min(x1, x2) - 0.000001 <= x <= max(x1, x2) + 0.000001 and min(y1, y2) - 0.000001 <= y <= max(y1, y2) + 0.000001:
            return True
    return _strictly_inside(point, polygon)


if __name__ == "__main__":
    unittest.main()
