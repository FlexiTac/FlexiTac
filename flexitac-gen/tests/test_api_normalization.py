"""Strict request normalization (audit H6, L3; decision D13).

Unknown keys and wrappers are errors with a JSON path, invalid alias values
are errors, ``validation.normalization`` reports aliases applied and
shadowed, nested fields win over flat aliases, and malformed values become
structured errors instead of exceptions.
"""

from __future__ import annotations

import json
import math
import unittest

from engine import check_design, default_design, generate_design, validate_design


def _issues(result, kind="errors"):
    return [(issue["code"], issue["field"]) for issue in result["validation"][kind]]


class UnknownFieldTests(unittest.TestCase):
    def test_unknown_keys_are_errors_with_their_json_path_at_every_level(self) -> None:
        cases = (
            ({"colums": 20}, "colums"),
            ({"matrix": {"colums": 20}}, "matrix.colums"),
            ({"tail": {"connector_side": "left"}}, "tail.connector_side"),
            ({"connector": {"pins": 16}}, "connector.pins"),
            ({"role_mapping": {"middle": "rows"}}, "role_mapping.middle"),
            ({"channel_order": {"scan_order": "reverse"}}, "channel_order.scan_order"),
            ({"Matrix": {"rows": 8}}, "Matrix"),
            ({"matrix": {"row count": 8}}, 'matrix["row count"]'),
            ({"a.b": 1}, '$["a.b"]'),
        )
        for data, field in cases:
            with self.subTest(data=data):
                result = generate_design(data)
                self.assertFalse(result["ok"])
                self.assertEqual(result["boards"], {})
                self.assertIn(("E_UNKNOWN_FIELD", field), _issues(result))

    def test_misspellings_get_a_suggestion(self) -> None:
        messages = {issue["field"]: issue["message"] for issue in check_design({"matrix": {"colums": 3}, "Matrix": {}, "row_side": "top"})["validation"]["errors"]}
        self.assertIn("did you mean matrix.columns?", messages["matrix.colums"])
        self.assertIn("did you mean matrix?", messages["Matrix"])
        self.assertIn("did you mean tail.row_side?", messages["row_side"])
        nested_alias = check_design({"matrix": {"row_num": 8}})["validation"]["errors"][0]
        self.assertEqual(nested_alias["field"], "matrix.row_num")
        self.assertIn("only at the top level", nested_alias["message"])

    def test_wrapped_designs_are_rejected_instead_of_silently_defaulted(self) -> None:
        inner = {"matrix": {"rows": 8, "columns": 16}}
        for wrapper in ("design", "params", "data"):
            with self.subTest(wrapper=wrapper):
                result = generate_design({wrapper: inner})
                self.assertFalse(result["ok"])
                error = result["validation"]["errors"][0]
                self.assertEqual((error["code"], error["field"]), ("E_UNKNOWN_FIELD", wrapper))
                self.assertIn("wrapped design", error["message"])
        # Posting a whole generate result (as an export body) is not the default design.
        whole = json.loads(json.dumps({key: value for key, value in generate_design({"rows": 4}).items() if key != "derived_layout"}))
        result = generate_design(whole)
        self.assertFalse(result["ok"])
        self.assertEqual(
            {field for code, field in _issues(result) if code == "E_UNKNOWN_FIELD"},
            {"ok", "design", "profile", "validation", "boards", "manifest"},
        )

    def test_unknown_field_errors_are_bounded(self) -> None:
        result = check_design({f"key_{index}": index for index in range(100)})
        unknown = [issue for issue in result["validation"]["errors"] if issue["code"] == "E_UNKNOWN_FIELD"]
        self.assertEqual(len(unknown), 21)
        self.assertEqual(unknown[-1]["field"], "$")
        self.assertIn("80 more unknown fields", unknown[-1]["message"])


class AliasTests(unittest.TestCase):
    def test_invalid_alias_values_are_errors_at_the_alias(self) -> None:
        for data, code in (
            ({"row_fpc_position": "Bottom"}, "E_ROLE_MAPPING"),
            ({"row_fpc_position": "middle"}, "E_ROLE_MAPPING"),
            ({"row_fpc_position": None}, "E_ROLE_MAPPING"),
            ({"row_fpc_position": ["top"]}, "E_ROLE_MAPPING"),
            ({"connector_side": "middle"}, "E_TAIL_SIDE"),
            ({"connector_side": ["bottom"]}, "E_TAIL_SIDE"),
            ({"scan_order": "backwards"}, "E_CHANNEL_ORDER"),
            ({"scan_order": {"rows": "reverse"}}, "E_CHANNEL_ORDER"),
        ):
            alias = next(iter(data))
            with self.subTest(data=data):
                result = generate_design(data)
                self.assertFalse(result["ok"])
                # Reported once, at the alias; the canonical fields it set are not reported again.
                self.assertEqual(_issues(result), [(code, alias)])
                self.assertIn("must be one of", result["validation"]["errors"][0]["message"])
        # Still an error when complete nested fields shadow the alias (and not also a shadow warning).
        for data, code in (
            ({"row_fpc_position": "middle", "role_mapping": {"top": "rows", "bottom": "columns"}}, "E_ROLE_MAPPING"),
            ({"connector_side": "middle", "tail": {"row_side": "bottom", "column_side": "bottom"}}, "E_TAIL_SIDE"),
            ({"scan_order": "backwards", "channel_order": {"rows": "ascending", "columns": "ascending"}}, "E_CHANNEL_ORDER"),
        ):
            alias = next(iter(data))
            with self.subTest(shadowed=data):
                result = generate_design(data)
                self.assertFalse(result["ok"])
                self.assertEqual(_issues(result), [(code, alias)])
                self.assertEqual(_issues(result, "warnings"), [("W_SCHEMA_VERSION_DEFAULTED", "schema_version")])
                self.assertEqual({entry["alias"] for entry in result["validation"]["normalization"]["aliases_shadowed"]}, {alias})

    def test_report_lists_applied_aliases_defaults_and_rounding(self) -> None:
        result = generate_design({"name": "  Demo  ", "rows": 4, "taxel_size_mm": 1.0, "pitch_x_mm": 2.0000004, "connector_side": "top"})
        self.assertTrue(result["ok"], result["validation"]["errors"])
        report = result["validation"]["normalization"]
        self.assertEqual(
            report["aliases_applied"],
            [
                {"alias": "name", "field": "project_name"},
                {"alias": "rows", "field": "matrix.rows"},
                {"alias": "pitch_x_mm", "field": "matrix.pitch_x_mm"},
                {"alias": "taxel_size_mm", "field": "matrix.taxel_width_mm"},
                {"alias": "taxel_size_mm", "field": "matrix.taxel_height_mm"},
                {"alias": "connector_side", "field": "tail.row_side"},
                {"alias": "connector_side", "field": "tail.column_side"},
            ],
        )
        self.assertEqual(report["aliases_shadowed"], [])
        self.assertIn("connector.row_pins", report["defaults_applied"])
        self.assertNotIn("matrix.rows", report["defaults_applied"])
        self.assertEqual(
            report["values_normalized"],
            [
                {"field": "project_name", "from": "  Demo  ", "to": "Demo", "reason": "whitespace trimmed"},
                {"field": "matrix.pitch_x_mm", "from": 2.0000004, "to": 2, "reason": "rounded to the 6-decimal layout grid"},
            ],
        )
        self.assertEqual(result["design"]["project_name"], "Demo")

    def test_nested_fields_win_over_flat_aliases_and_shadowing_is_reported(self) -> None:
        cases = (
            ({"tail_length_mm": 20.0, "tail": {"length_mm": 30.0}}, ("tail", "top_length_mm"), 30),
            ({"top_tail_length_mm": 20.0, "tail": {"length_mm": 30.0}}, ("tail", "top_length_mm"), 30),
            ({"column_electrode_width_mm": 1.0, "matrix": {"column_electrode_width_mm": 1.2}}, ("matrix", "taxel_width_mm"), 1.2),
            ({"taxel_size_mm": 1.0, "taxel_width_mm": 1.2}, ("matrix", "taxel_width_mm"), 1.2),
            ({"taxel_width_mm": 1.2, "column_electrode_width_mm": 1.0}, ("matrix", "taxel_width_mm"), 1.2),
            ({"rows": 4, "row_num": 8}, ("matrix", "rows"), 4),
            ({"columns": 4, "column_num": 8}, ("matrix", "columns"), 4),
            ({"rows": 8, "matrix": {"rows": 5}}, ("matrix", "rows"), 5),
            ({"scan_order": "reverse", "channel_order": {"rows": "ascending"}}, ("channel_order", "rows"), "ascending"),
            ({"row_fpc_position": "bottom", "role_mapping": {"top": "rows", "bottom": "columns"}}, ("role_mapping", "top"), "rows"),
        )
        for data, (section, key), expected in cases:
            with self.subTest(data=data):
                result = generate_design(data)
                self.assertTrue(result["ok"], result["validation"]["errors"])
                self.assertEqual(result["design"][section][key], expected)
                shadowed = result["validation"]["normalization"]["aliases_shadowed"]
                self.assertIn(f"{section}.{key}", {entry["field"] for entry in shadowed})
                self.assertIn("W_ALIAS_SHADOWED", {code for code, _ in _issues(result, "warnings")})
        # A flat alias still fills the nested field the request left out.
        partial = generate_design({"scan_order": "reverse", "channel_order": {"rows": "ascending"}})
        self.assertEqual(partial["design"]["channel_order"], {"rows": "ascending", "columns": "descending"})
        # Equal values are recorded as shadowed but are not a conflict warning.
        same = generate_design({"rows": 5, "matrix": {"rows": 5}})
        self.assertEqual(same["validation"]["normalization"]["aliases_shadowed"], [{"alias": "rows", "field": "matrix.rows", "by": "matrix.rows"}])
        self.assertNotIn("W_ALIAS_SHADOWED", {code for code, _ in _issues(same, "warnings")})
        # Values are compared once canonical: equal on the layout grid or after trimming is equal,
        # but true is not 1.
        for data, warned in (
            ({"pitch_x_mm": 2.0000004, "matrix": {"pitch_x_mm": 2}}, False),
            ({"name": "  Demo ", "project_name": "Demo"}, False),
            ({"rows": 4.0, "matrix": {"rows": 4}}, False),
            ({"pitch_x_mm": 2.000001, "matrix": {"pitch_x_mm": 2}}, True),
            ({"rows": True, "matrix": {"rows": 1}}, True),
            ({"rows": [1], "matrix": {"rows": 1}}, True),
        ):
            with self.subTest(data=data):
                result = check_design(data)
                self.assertEqual(len(result["validation"]["normalization"]["aliases_shadowed"]), 1)
                self.assertEqual("W_ALIAS_SHADOWED" in {code for code, _ in _issues(result, "warnings")}, warned)


class VersionAndNameTests(unittest.TestCase):
    def test_schema_version_missing_is_defaulted_with_a_warning_and_other_values_are_errors(self) -> None:
        missing = generate_design({"rows": 4})
        self.assertTrue(missing["ok"])
        self.assertEqual(_issues(missing, "warnings"), [("W_SCHEMA_VERSION_DEFAULTED", "schema_version")])
        self.assertEqual(missing["design"]["schema_version"], "tactile-fpc-design/v1")
        self.assertEqual(_issues(generate_design(default_design()), "warnings"), [])
        for value in ("tactile-fpc-design/v2", None, 42, ""):
            with self.subTest(schema_version=value):
                result = generate_design({"schema_version": value})
                self.assertFalse(result["ok"])
                self.assertEqual(_issues(result), [("E_SCHEMA_VERSION", "schema_version")])

    def test_template_id_null_or_other_is_an_error(self) -> None:
        for value in (None, "canonical_12x32", 1):
            with self.subTest(template_id=value):
                result = generate_design({"template_id": value})
                self.assertFalse(result["ok"])
                self.assertEqual(_issues(result), [("E_TEMPLATE_UNSUPPORTED", "template_id")])
        self.assertTrue(generate_design({"template_id": "generic_matrix_v1"})["ok"])

    def test_project_name_length_is_checked_after_trimming(self) -> None:
        limit = generate_design()["profile"]["limits"]["maximum_project_name_length"]
        accepted = generate_design({"project_name": "  " + "x" * limit + "  "})
        self.assertTrue(accepted["ok"], accepted["validation"]["errors"])
        self.assertEqual(accepted["design"]["project_name"], "x" * limit)
        for name in ("x" * (limit + 1), "   ", "", 5, None, "bad\x1bname", "\ud800"):
            with self.subTest(name=name):
                self.assertEqual(_issues(generate_design({"project_name": name})), [("E_PROJECT_NAME", "project_name")])
        # validate_design applies the same rule to a design that was not normalized.
        design = generate_design()["design"]
        self.assertEqual(validate_design(dict(design, project_name="  " + "x" * limit + "  "))["errors"], [])
        self.assertEqual([issue["code"] for issue in validate_design(dict(design, project_name=" " + "x" * (limit + 1)))["errors"]], ["E_PROJECT_NAME"])

    def test_missing_name_follows_the_matrix(self) -> None:
        self.assertEqual(generate_design({"rows": 8, "columns": 16})["design"]["project_name"], "Tactile FPC 8x16")
        self.assertEqual(generate_design()["design"]["project_name"], "Tactile FPC 12x32")


class ValueTests(unittest.TestCase):
    def test_integral_floats_are_accepted_for_integer_fields(self) -> None:
        result = generate_design({"matrix": {"rows": 12.0, "columns": 16.0}, "connector": {"row_pins": 16.0, "column_pins": 20.0}})
        self.assertTrue(result["ok"], result["validation"]["errors"])
        design = result["design"]
        for value in (design["matrix"]["rows"], design["matrix"]["columns"], design["connector"]["row_pins"], design["connector"]["column_pins"]):
            self.assertIs(type(value), int)
        self.assertEqual(result["boards"]["row"]["tail"]["connector_pins"], 16)
        for data, error in (
            ({"matrix": {"rows": 12.5}}, ("E_ROWS_INTEGER", "matrix.rows")),
            ({"matrix": {"rows": 12.0000001}}, ("E_ROWS_INTEGER", "matrix.rows")),
            ({"connector": {"row_pins": 16.5}}, ("E_CONNECTOR_PINS", "connector.row_pins")),
            ({"matrix": {"rows": True}}, ("E_ROWS_INTEGER", "matrix.rows")),
            ({"matrix": {"rows": "12"}}, ("E_ROWS_INTEGER", "matrix.rows")),
        ):
            with self.subTest(data=data):
                self.assertEqual(_issues(generate_design(data)), [error])

    def test_malformed_values_are_structured_errors_never_exceptions(self) -> None:
        huge = 10**400
        cases = (
            ({"matrix": {"pitch_x_mm": math.nan}}, ("E_NUMERIC", "matrix.pitch_x_mm")),
            ({"matrix": {"pitch_x_mm": math.inf}}, ("E_NUMERIC", "matrix.pitch_x_mm")),
            ({"matrix": {"taxel_height_mm": -math.inf}}, ("E_NUMERIC", "matrix.taxel_height_mm")),
            ({"matrix": {"rows": math.nan}}, ("E_ROWS_INTEGER", "matrix.rows")),
            ({"matrix": {"pitch_x_mm": huge}}, ("E_NUMERIC", "matrix.pitch_x_mm")),
            ({"matrix": {"rows": huge}}, ("E_ROWS_INTEGER", "matrix.rows")),
            ({"matrix": {"columns": -huge}}, ("E_COLUMNS_INTEGER", "matrix.columns")),
            ({"top_tail_length_mm": huge}, ("E_NUMERIC", "tail.top_length_mm")),
            ({"matrix": {"pitch_x_mm": 1e300}}, ("E_PITCH_RANGE", "matrix.pitch_x_mm")),
            ({"matrix": {"rows": 1e300}}, ("E_ROWS_RANGE", "matrix.rows")),
            ({"tail": {"row_side": ["left"]}}, ("E_TAIL_SIDE", "tail.row_side")),
            ({"tail": {"column_side": {}}}, ("E_TAIL_SIDE", "tail.column_side")),
            ({"channel_order": {"rows": {}}}, ("E_CHANNEL_ORDER", "channel_order.rows")),
            ({"role_mapping": {"top": ["rows"]}}, ("E_ROLE_MAPPING", "role_mapping.top")),
            ({"connector": {"row_pins": [16]}}, ("E_CONNECTOR_PINS", "connector.row_pins")),
            ({"matrix": {"rows": {1, 2}}}, ("E_ROWS_INTEGER", "matrix.rows")),
            ({"matrix": {"pitch_x_mm": b"2"}}, ("E_NUMERIC", "matrix.pitch_x_mm")),
            ({"project_name": object()}, ("E_PROJECT_NAME", "project_name")),
            ({"matrix": "not an object"}, ("E_MATRIX_OBJECT", "matrix")),
            ({"connector": "16 pins"}, ("E_CONNECTOR_OBJECT", "connector")),
            ({"role_mapping": ["rows", "columns"]}, ("E_ROLE_MAPPING", "role_mapping")),
            ({"channel_order": None}, ("E_CHANNEL_ORDER", "channel_order")),
            ({1: "x"}, ("E_UNKNOWN_FIELD", '$["1"]')),
        )
        deep: object = 1
        for _ in range(5000):
            deep = [deep]
        cases += (({"matrix": {"rows": deep}}, ("E_ROWS_INTEGER", "matrix.rows")),)
        for index, (data, error) in enumerate(cases):
            # (No repr of the data: the deep case exceeds repr's recursion limit.)
            with self.subTest(case=index, error=error):
                for run in (generate_design, check_design):
                    result = run(data)
                    self.assertFalse(result["ok"])
                    self.assertEqual(_issues(result), [error])
                    # The whole result stays strict JSON.
                    json.dumps(result, allow_nan=False)
        for data in ([], "design", 42):
            with self.subTest(data=data):
                self.assertEqual(_issues(generate_design(data)), [("E_DESIGN_TYPE", "$")])

    def test_validate_design_is_robust_on_raw_values(self) -> None:
        raw = {
            "schema_version": "tactile-fpc-design/v1", "template_id": "generic_matrix_v1", "project_name": "x",
            "matrix": {"rows": [1], "columns": 10**400, "pitch_x_mm": 10**400, "pitch_y_mm": math.nan, "taxel_width_mm": {}, "taxel_height_mm": None},
            "tail": {"top_length_mm": "7", "bottom_length_mm": -math.inf, "row_side": [], "column_side": {}},
            "connector": {"row_pins": [], "column_pins": 10**400},
            "role_mapping": {"top": [], "bottom": {}},
            "channel_order": {"rows": [], "columns": {}},
        }
        codes = {issue["code"] for issue in validate_design(raw)["errors"]}
        self.assertTrue({"E_ROWS_INTEGER", "E_COLUMNS_RANGE", "E_NUMERIC", "E_TAIL_SIDE", "E_ROLE_MAPPING", "E_CHANNEL_ORDER", "E_CONNECTOR_PINS"} <= codes)

    def test_independent_rules_are_reported_together(self) -> None:
        result = check_design({"matrix": {"pitch_x_mm": "wide"}, "tail": {"row_side": "middle"}, "channel_order": {"rows": "random"}})
        self.assertEqual(
            _issues(result),
            [("E_NUMERIC", "matrix.pitch_x_mm"), ("E_TAIL_SIDE", "tail.row_side"), ("E_CHANNEL_ORDER", "channel_order.rows")],
        )

    def test_role_mapping_positions_are_checked_independently(self) -> None:
        for data, expected in (
            # One rejected position does not hide an error in the other.
            ({"role_mapping": {"top": ["rows"], "bottom": "middle"}}, [("E_ROLE_MAPPING", "role_mapping.top"), ("E_ROLE_MAPPING", "role_mapping.bottom")]),
            ({"role_mapping": {"top": "middle"}}, [("E_ROLE_MAPPING", "role_mapping.top")]),
            ({"role_mapping": {"top": "columns"}}, [("E_ROLE_MAPPING", "role_mapping")]),
            ({"role_mapping": {"top": "rows", "bottom": "rows"}}, [("E_ROLE_MAPPING", "role_mapping")]),
        ):
            with self.subTest(data=data):
                self.assertEqual(_issues(check_design(data)), expected)


class CheckDesignTests(unittest.TestCase):
    def test_check_design_runs_input_rules_and_feasibility_without_geometry(self) -> None:
        valid = check_design({"rows": 8})
        self.assertEqual(set(valid), {"ok", "design", "validation", "identity"})
        self.assertTrue(valid["ok"])
        self.assertEqual(valid["identity"]["build_id"], generate_design({"rows": 8})["manifest"]["build_id"])
        too_big = check_design({"matrix": {"rows": 64, "pitch_y_mm": 10.0}})
        self.assertFalse(too_big["ok"])
        self.assertIn("E_BOARD_SIZE", {code for code, _ in _issues(too_big)})
        # 32 columns at 0.6 mm: the two-lane fan-out spreads wider than the body (no longer E_DUAL_LANE_WIDTH).
        narrow = check_design({"matrix": {"columns": 32, "pitch_x_mm": 0.6, "taxel_width_mm": 0.3}})
        self.assertEqual(_issues(narrow), [])
        self.assertTrue(narrow["ok"])


if __name__ == "__main__":
    unittest.main()
