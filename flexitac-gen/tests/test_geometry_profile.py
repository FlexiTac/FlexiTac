"""Profile-as-source-of-truth, limits, coverlay, overhang and anchor regressions.

Covers audit M7 (engine/profile part), M9 (minimum electrode width, board
size), L6 (coverlay bridges), L7 (electrode overhang) and M11 (anchors).
"""

from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine import generate_design, load_profile, validate_design
from engine import profile as profile_module
from engine.geometry import rect_bounds
from engine.layout import column_plan
from exporters import ExportError, build_exports

try:
    from geometry_checks import straight_channel
except ImportError:  # run as tests.test_geometry_profile
    from tests.geometry_checks import straight_channel


def _issues(profile) -> dict[str, str]:
    return {issue["field"]: issue["code"] for issue in profile_module.profile_issues(profile)}


class ProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profile()

    def test_bundled_profile_is_consistent_and_records_its_sources(self) -> None:
        self.assertEqual(profile_module.profile_issues(self.profile), [])
        source = self.profile["sources"]["jlcpcb_flex_capabilities"]
        self.assertEqual(source["url"], "https://jlcpcb.com/capabilities/flex-pcb-capabilities")
        self.assertEqual(source["fetched"], "2026-10-12")
        self.assertEqual(self.profile["routing"]["copper_to_edge_mm"], 0.3)
        self.assertIn(self.profile["stackup"]["stiffener_thickness_mm"], self.profile["fabrication"]["pi_stiffener_thickness_options_mm"])
        # Dead keys are gone; formerly hard-coded rules now live here.
        self.assertNotIn("trace_pitch_mm", self.profile["routing"])
        self.assertNotIn("stiffener_inset_mm", self.profile["tail"])
        for section, key in (
            ("fanout", "minimum_slot_width_mm"), ("fanout", "maximum_slot_height_mm"), ("routing", "min_pad_space_mm"),
            ("limits", "large_matrix_warning_taxels"), ("outline", "offset_allowance_mm"), ("drc", "numeric_epsilon_mm"),
        ):
            self.assertIn(key, self.profile[section])

    def test_inconsistent_profiles_are_reported_field_by_field(self) -> None:
        cases = (
            (("routing", "copper_to_edge_mm", 0.2), "profile.routing.copper_to_edge_mm"),
            (("stackup", "stiffener_thickness_mm", 0.3), "profile.stackup.stiffener_thickness_mm"),
            (("tail", "stiffener_end_clearance_mm", 1.5), "profile.tail.minimum_length_mm"),
            # A steeper merger taper widens the Column tail 0.69 mm before its
            # root, leaving less than the straight clearance on a 7 mm tail.
            (("fanout", "maximum_taper_angle_deg", 75.0), "profile.tail.minimum_length_mm"),
            (("fanout", "maximum_channels_per_lane", 8), "profile.limits.maximum_columns"),
            (("connector", "pad_width_mm", 0.32), "profile.connector.pad_width_mm"),
            (("connector", "contact_center_to_side_edge_mm", 0.6), "profile.connector.contact_center_to_side_edge_mm"),
            (("coverlay", "coverlay_min_bridge_mm", 0.3), "profile.coverlay.coverlay_min_bridge_mm"),
            (("routing", "min_electrode_width_mm", 0.05), "profile.routing.min_electrode_width_mm"),
            # Re-audit N4: 0.1 mm electrodes (the old rule) are below JLC's 1 oz minimum of 0.1016 mm.
            (("routing", "min_electrode_width_mm", 0.1), "profile.routing.min_electrode_width_mm"),
            (("routing", "finger_trace_width_mm", "wide"), "profile.routing.finger_trace_width_mm"),
            # Fingers 0.41 mm wide at the 0.5 mm pitch leave 0.09 mm, below the 1 oz spacing minimum.
            (("routing", "finger_trace_width_mm", 0.41), "profile.routing.finger_trace_width_mm"),
            # The 18 um copper minimum (3.5 mil) applied to the ordered 1 oz copper.
            (("limits", "minimum_trace_width_mm", 0.0889), "profile.limits.minimum_trace_width_mm"),
            (("limits", "minimum_trace_space_mm", 0.0889), "profile.limits.minimum_trace_space_mm"),
            (("limits", "maximum_trace_width_mm", 0.3), "profile.limits.maximum_trace_width_mm"),
            (("limits", "maximum_trace_space_mm", 0.3), "profile.connector.pad_pitch_mm"),
            (("limits", "maximum_trace_space_mm", 0.05), "profile.limits.minimum_trace_space_mm"),
            (("fabrication", "single_sided_min_trace_width_mm", [0.0889]), "profile.fabrication.single_sided_min_trace_width_mm"),
            (("stackup", "construction", " "), "profile.stackup.construction"),
        )
        # The generic profile builds the straight Row channel (the diagonal Row bus takes the surface profile,
        # P5-diagonal-bus.md section 20).
        for (section, key, value), field in cases:
            profile = copy.deepcopy(self.profile)
            profile[section][key] = value
            with self.subTest(field=field):
                self.assertIn(field, _issues(profile))
                validation = validate_design(generate_design(straight_channel())["design"], profile)
                self.assertTrue(validation["errors"])
                self.assertTrue(all(issue["code"].startswith("E_PROFILE_") for issue in validation["errors"]))
                with mock.patch("engine.core.load_profile", return_value=profile):
                    self.assertFalse(generate_design(straight_channel())["ok"])

    def test_the_trace_minimum_is_the_one_of_the_profiles_copper(self) -> None:
        # T-D2: JLC's minimum trace width/spacing depends on the copper:
        # 3.5/3.5 mil for 18 um, 4/4 mil for 35 um (the ordered 1 oz build).
        self.assertEqual(self.profile["stackup"]["copper_thickness_mm"], 0.035)
        self.assertEqual(profile_module.fabrication_minimum(self.profile), (0.1016, 0.1016))
        thin = copy.deepcopy(self.profile)
        thin["stackup"]["copper_thickness_mm"] = 0.018
        self.assertEqual(profile_module.fabrication_minimum(thin), (0.0889, 0.0889))
        # With 18 um copper a 0.0889 mm trace limit is within JLC's capability
        # (the stack-up then no longer adds up to the ordered 0.11 mm, a separate issue).
        thin["limits"]["minimum_trace_width_mm"] = 0.0889
        self.assertNotIn("profile.limits.minimum_trace_width_mm", _issues(thin))
        self.assertIn("profile.stackup", _issues(thin))
        unlisted = copy.deepcopy(self.profile)
        unlisted["stackup"]["copper_thickness_mm"] = 0.07
        with self.assertRaises(ValueError):
            profile_module.fabrication_minimum(unlisted)

    def test_loading_a_broken_profile_fails_with_a_clear_error(self) -> None:
        broken = copy.deepcopy(self.profile)
        broken["routing"]["copper_to_edge_mm"] = 0.1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text(json.dumps(broken), encoding="utf-8")
            with mock.patch.object(profile_module, "PROFILE_PATH", path):
                with self.assertRaisesRegex(profile_module.ProfileError, "routing.copper_to_edge_mm"):
                    profile_module.load_profile()

    def test_maximum_channels_per_lane_sets_the_lane_split(self) -> None:
        profile = copy.deepcopy(self.profile)
        profile["fanout"]["maximum_channels_per_lane"] = 8
        profile["limits"]["maximum_columns"] = 16
        self.assertEqual(profile_module.profile_issues(profile), [])
        design = generate_design(straight_channel())["design"]
        for columns, groups in ((8, [8]), (12, [6, 6]), (16, [8, 8])):
            changed = copy.deepcopy(design)
            changed["matrix"].update(columns=columns, pitch_x_mm=3.0)
            self.assertEqual(column_plan(changed, profile)["groups"], groups)
        too_many = copy.deepcopy(design)
        self.assertIn("E_COLUMNS_RANGE", {issue["code"] for issue in validate_design(too_many, profile)["errors"]})


class LimitTests(unittest.TestCase):
    def test_minimum_electrode_width_is_enforced(self) -> None:
        # Re-audit N4: 0.1016 mm (4 mil, JLC's 1 oz minimum); 0.1 mm passed until 2026-10-15.
        for field, value in (("taxel_width_mm", 0.099), ("taxel_height_mm", 1e-9), ("taxel_width_mm", 0.1), ("taxel_height_mm", 0.1015)):
            result = generate_design({"matrix": {field: value}})
            with self.subTest(field=field):
                self.assertFalse(result["ok"])
                self.assertEqual(
                    [(issue["code"], issue["field"]) for issue in result["validation"]["errors"]],
                    [("E_ELECTRODE_WIDTH", f"matrix.{field}")],
                )
        narrow = generate_design({"matrix": {"taxel_width_mm": 0.1016, "taxel_height_mm": 0.1016}})
        self.assertTrue(narrow["ok"], narrow["validation"]["errors"])

    def test_electrode_gap_bound_can_be_applied_as_printed(self) -> None:
        # Review finding F5: the bound was rounded to nearest, so "at most
        # 0.9500 mm" could itself be rejected.  It is floored now, and the
        # check uses the 1e-6 mm grid values the geometry is built from.
        for pitch in (1.2, 1.23456789, 0.987654321, 3.14159265, 0.6000004):
            matrix = {"columns": 8, "pitch_x_mm": pitch}
            result = generate_design({"matrix": dict(matrix, taxel_width_mm=pitch - 0.2)})
            with self.subTest(pitch=pitch):
                self.assertEqual([issue["code"] for issue in result["validation"]["errors"]], ["E_ELECTRODE_GAP"])
                error = result["validation"]["errors"][0]
                self.assertEqual(error["field"], "matrix.taxel_width_mm")
                bound = float(re.search(r"at most ([0-9.]+) mm", error["message"]).group(1))
                self.assertTrue(generate_design({"matrix": dict(matrix, taxel_width_mm=bound)})["ok"])
                above = generate_design({"matrix": dict(matrix, taxel_width_mm=round(bound + 0.0001, 4))})
                self.assertIn("E_ELECTRODE_GAP", {issue["code"] for issue in above["validation"]["errors"]})

    def test_board_size_limit_is_a_field_level_error_with_a_working_bound(self) -> None:
        wide = {"rows": 63, "columns": 31, "pitch_x_mm": 10.0, "pitch_y_mm": 10.0, "taxel_width_mm": 9.75, "taxel_height_mm": 9.75}
        cases = (
            {"matrix": {"rows": 64, "pitch_y_mm": 10.0}},
            {"matrix": {"rows": 64, "columns": 10, "pitch_x_mm": 10.0, "pitch_y_mm": 10.0}, "tail": {"top_length_mm": 80.0, "bottom_length_mm": 80.0}},
            # Column 316.9 x 259.6 mm with an 80 mm tail: fits neither orientation (the diagonal Row bus's boards, CAD mode's
            # rule set since P5-diagonal-bus.md section 20: one outline down to their tails, the Column V at 80 degrees).
            {"matrix": {"rows": 16, "columns": 32, "pitch_x_mm": 10.0, "pitch_y_mm": 10.0}, "tail": {"bottom_length_mm": 80.0}},
            # 9.75 mm taxels pin both pitches at 10 mm: the advice scales a pitch
            # with its taxel size, or lowers the row count.
            {"matrix": wide, "tail": {"top_length_mm": 7.5, "bottom_length_mm": 66.44}},
        )
        for design in cases:
            result = generate_design(design)
            with self.subTest(design=design):
                self.assertFalse(result["ok"])
                errors = [issue for issue in result["validation"]["errors"] if issue["code"] == "E_BOARD_SIZE"]
                self.assertTrue(errors)
                fixed = copy.deepcopy(result["design"])
                bounds = {}
                for error in errors:
                    # The first alternative names the error field first and every
                    # field it lowers with an explicit bound.
                    first = error["message"].split("Any one of: ", 1)[1].split("; ")[0].rstrip(".")
                    assignments = re.findall(r"(\w+)\.(\w+) <= ([0-9.]+)", first)
                    self.assertTrue(assignments, error["message"])
                    self.assertEqual("{}.{}".format(*assignments[0][:2]), error["field"])
                    for section, key, bound in assignments:
                        # Both boards' bounds on one field: the smaller holds for both.
                        value = int(bound) if key in ("rows", "columns") else float(bound)
                        bounds[(section, key)] = min(bounds.get((section, key), value), value)
                for (section, key), value in bounds.items():
                    fixed[section][key] = value
                repaired = generate_design(fixed)
                self.assertTrue(repaired["ok"], repaired["validation"]["errors"])
                for board in repaired["boards"].values():
                    short, long = sorted((board["metrics"]["outline_width_mm"], board["metrics"]["outline_height_mm"]))
                    self.assertLessEqual(short, 234.0)
                    self.assertLessEqual(long, 490.0)
        # When no single field is enough the advice lowers two fields in step.
        # With the bundled profiles one row always fits, so a profile with an
        # 80 mm short side takes that branch: the 327.3 mm wide 31-column
        # Column board (the diagonal Row bus's, on the surface profile it is
        # built with) must stay within 80 mm in height, which one row with the
        # 66.44 mm tail misses.
        narrow = copy.deepcopy(load_profile("surface_matrix_v1"))  # the diagonal Row bus's rule set (section 20)
        narrow["limits"]["maximum_outline_short_side_mm"] = 80.0
        result = generate_design({"matrix": wide, "tail": {"top_length_mm": 7.5, "bottom_length_mm": 66.44}}, profile=narrow)
        column_error = next(
            issue for issue in result["validation"]["errors"] if issue["code"] == "E_BOARD_SIZE" and "column FPC" in issue["message"]
        )
        self.assertEqual(column_error["field"], "tail.bottom_length_mm")
        alternatives = column_error["message"].split("Any one of: ", 1)[1].rstrip(".").split("; ")
        scaled = ({"matrix.pitch_x_mm", "matrix.taxel_width_mm"}, {"matrix.pitch_y_mm", "matrix.taxel_height_mm"})
        for alternative in alternatives:
            assignments = re.findall(r"(\w+)\.(\w+) <= ([0-9.]+)", alternative)
            fields = {f"{section}.{key}" for section, key, _ in assignments}
            with self.subTest(alternative=alternative):
                self.assertGreaterEqual(len(fields), 2)
                self.assertNotIn(fields, scaled)  # not one pitch scaled with its taxel size
                fixed = copy.deepcopy(result["design"])
                for section, key, bound in assignments:
                    fixed[section][key] = int(bound) if key in ("rows", "columns") else float(bound)
                again = generate_design(fixed, profile=narrow)["validation"]["errors"]
                self.assertLessEqual({issue["code"] for issue in again}, {"E_BOARD_SIZE"})  # feasibility ran; a Row board error may be left
                self.assertEqual([issue for issue in again if "column FPC" in issue["message"]], [])

    def test_large_matrix_warning_threshold_is_reachable(self) -> None:
        warned = generate_design({"matrix": {"rows": 64, "pitch_y_mm": 0.8, "taxel_height_mm": 0.5}})
        self.assertIn("W_LARGE_MATRIX", {issue["code"] for issue in warned["validation"]["warnings"]})
        self.assertNotIn("W_LARGE_MATRIX", {issue["code"] for issue in generate_design()["validation"]["warnings"]})


class CoverlayOverhangAnchorTests(unittest.TestCase):
    def test_coverlay_openings_merge_when_bridges_would_be_removed(self) -> None:
        profile = load_profile()
        bridge = profile["coverlay"]["coverlay_min_bridge_mm"]
        # 2.0 mm pitch, 1.4 mm electrodes (the default until the user's decision of 2026-11-06): 0.4 mm bridges.
        merged = generate_design({"matrix": {"taxel_width_mm": 1.4, "taxel_height_mm": 1.4}})
        for board in merged["boards"].values():
            kinds = [opening["kind"] for opening in board["layers"]["top_coverlay_openings"]]
            self.assertEqual(sorted(kinds), ["connector_contact_opening", "electrode_field_opening"])
        # The default since: 1.0 mm electrodes, 0.8 mm bridges, a window per electrode.
        for board in generate_design()["boards"].values():
            kinds = [opening["kind"] for opening in board["layers"]["top_coverlay_openings"]]
            self.assertEqual(kinds.count("sensor_electrode_opening"), len(board["layers"]["top_copper"]["electrodes"]))
            self.assertNotIn("electrode_field_opening", kinds)
        separate = generate_design({"matrix": {"taxel_width_mm": 1.3, "taxel_height_mm": 1.3}})  # exactly 0.5 mm bridges
        for board in separate["boards"].values():
            openings = board["layers"]["top_coverlay_openings"]
            electrode_openings = [opening for opening in openings if opening["kind"] == "sensor_electrode_opening"]
            self.assertEqual(len(electrode_openings), len(board["layers"]["top_copper"]["electrodes"]))
            boxes = [rect_bounds(opening) for opening in openings]
            for index, first in enumerate(boxes):
                for second in boxes[index + 1 :]:
                    gap = max(second[0] - first[2], first[0] - second[2], second[1] - first[3], first[1] - second[3])
                    self.assertGreaterEqual(gap, bridge - 1e-6)

    def test_electrodes_overhang_the_taxel_field(self) -> None:
        overhang = load_profile()["routing"]["electrode_overhang_mm"]
        result = generate_design()
        for key, axis in (("row", 0), ("column", 1)):
            board = result["boards"][key]
            active = board["grid_registration"]["active_region"]
            self.assertEqual((active["width"], active["height"]), (63.0, 23.0))  # the default 1.0 mm electrodes
            field = board["grid_registration"]["electrode_field"]
            low, size = (active["x"], active["width"]) if axis == 0 else (active["y"], active["height"])
            for electrode in board["layers"]["top_copper"]["electrodes"]:
                box = rect_bounds(electrode)
                self.assertAlmostEqual(box[axis], low - overhang, places=6)
                self.assertAlmostEqual(box[axis + 2], low + size + overhang, places=6)
            self.assertAlmostEqual((field["width"], field["height"])[axis], size + 2 * overhang, places=6)

    def test_every_rectangle_carries_an_anchor(self) -> None:
        result = generate_design({"connector_side": "left", "connector": {"row_pins": 14}})
        self.assertEqual(result["derived_layout"]["format"], "tactile-fpc-layout/v3")
        for board in result["boards"].values():
            copper = board["layers"]["top_copper"]
            self.assertEqual({item["anchor"] for item in copper["pads"]}, {"center"})
            self.assertEqual({item["anchor"] for item in copper["electrodes"]}, {"lower_left"})
            self.assertEqual({item["anchor"] for item in board["layers"]["top_coverlay_openings"]}, {"lower_left"})
        pad = dict(result["boards"]["row"]["layers"]["top_copper"]["pads"][0])
        self.assertEqual(rect_bounds(pad)[0], pad["x"] - pad["width_mm"] / 2)
        del pad["anchor"]
        with self.assertRaises(KeyError):
            rect_bounds(pad)
        with self.assertRaises(ValueError):
            rect_bounds(dict(pad, anchor="upper_right"))
        tampered = copy.deepcopy(result)
        del tampered["boards"]["row"]["layers"]["top_copper"]["pads"][0]["anchor"]
        with self.assertRaises(ExportError):
            build_exports(tampered)


if __name__ == "__main__":
    unittest.main()
