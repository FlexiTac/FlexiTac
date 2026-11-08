"""Machine-readable contract (audit M14; decisions D10, D15).

The JSON Schema (draft 2020-12), the form limits and the display rules are
generated from the profile; the issue catalogue lists every code the engine
can emit.  The schema is exercised with a small validator for exactly the
keywords it uses (the independent ``jsonschema`` check runs outside the
stdlib suite).
"""

from __future__ import annotations

import copy
import re
import unittest
from pathlib import Path

import app
from engine import check_design, default_design, design_schema, input_limits, issue_codes, load_profile

ROOT = Path(__file__).resolve().parents[1]
_ANNOTATIONS = {"$schema", "title", "description", "default", "deprecated"}
_ASSERTIONS = {"type", "properties", "additionalProperties", "enum", "const", "minimum", "maximum", "minLength", "maxLength", "pattern"}


def _keywords(schema, found=None):
    found = set() if found is None else found
    for key, value in schema.items():
        if key.startswith("x-"):
            continue
        found.add(key)
        if key == "properties":
            for child in value.values():
                _keywords(child, found)
    return found


def _type_ok(value, kind) -> bool:
    if kind == "null":
        return value is None
    if kind == "string":
        return isinstance(value, str)
    if kind == "object":
        return isinstance(value, dict)
    if isinstance(value, bool):
        return False
    if kind == "integer":
        return isinstance(value, int) or (isinstance(value, float) and value.is_integer())
    return kind == "number" and isinstance(value, (int, float))


def _errors(schema, value, path="$"):
    """Draft 2020-12 semantics of the keywords in ``_ASSERTIONS``."""

    kinds = schema.get("type")
    if kinds is not None and not any(_type_ok(value, kind) for kind in ([kinds] if isinstance(kinds, str) else kinds)):
        return [f"{path}: type"]
    problems = []
    if "const" in schema and value != schema["const"]:
        problems.append(f"{path}: const")
    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{path}: enum")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            problems.append(f"{path}: minimum")
        if "maximum" in schema and value > schema["maximum"]:
            problems.append(f"{path}: maximum")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", len(value)):
            problems.append(f"{path}: length")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            problems.append(f"{path}: pattern")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                problems += _errors(properties[key], item, f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                problems.append(f"{path}.{key}: additionalProperties")
    return problems


class SchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profile()
        self.schema = design_schema(self.profile)

    def test_schema_is_a_strict_draft_2020_12_document_from_the_profile(self) -> None:
        schema = self.schema
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(_keywords(schema) - _ANNOTATIONS, _ASSERTIONS)
        self.assertIs(schema["additionalProperties"], False)
        sections = ("matrix", "tail", "connector", "role_mapping", "channel_order")
        for section in sections:
            self.assertIs(schema["properties"][section]["additionalProperties"], False, section)
        limits = self.profile["limits"]
        matrix = schema["properties"]["matrix"]["properties"]
        self.assertEqual((matrix["rows"]["minimum"], matrix["rows"]["maximum"]), (limits["minimum_rows"], limits["maximum_rows"]))
        self.assertEqual(matrix["pitch_x_mm"]["minimum"], limits["minimum_pitch_mm"])
        self.assertEqual(matrix["taxel_width_mm"]["minimum"], self.profile["routing"]["min_electrode_width_mm"])
        tail = schema["properties"]["tail"]["properties"]
        # The generic template's bounds that the diagonal Row bus's profile sets otherwise are the bus's (its default,
        # built with the surface profile, P5-diagonal-bus.md section 20), the straight channel's own under x-channel.
        bus = load_profile("surface_matrix_v1")
        self.assertEqual(tail["top_length_mm"]["minimum"], bus["tail"]["minimum_length_mm"])
        self.assertEqual(tail["top_length_mm"]["x-channel"], {"minimum": self.profile["tail"]["minimum_length_mm"]})
        self.assertEqual(matrix["columns"]["maximum"], bus["limits"]["maximum_columns"])
        self.assertEqual(matrix["columns"]["x-channel"], {"maximum": self.profile["limits"]["maximum_columns"]})
        self.assertEqual(schema["x-row-bus-profile"]["id"], bus["id"])
        connector = schema["properties"]["connector"]["properties"]
        for key in ("row_pins", "column_pins"):
            self.assertEqual(connector[key]["type"], ["integer", "null"])
            self.assertEqual(connector[key]["maximum"], self.profile["connector"]["maximum_pins"])
        self.assertEqual(schema["properties"]["project_name"]["maxLength"], limits["maximum_project_name_length"])
        # A missing name follows the matrix size, so the schema states no fixed default for it.
        self.assertNotIn("default", schema["properties"]["project_name"])
        self.assertEqual(schema["properties"]["matrix"]["properties"]["rows"]["default"], default_design()["matrix"]["rows"])
        self.assertEqual(schema["x-profile"]["id"], self.profile["id"])
        # Generated, not copied: other limits give another schema.
        changed = copy.deepcopy(self.profile)
        changed["limits"]["maximum_rows"] = 48
        changed["connector"]["maximum_pins"] = 50
        other = design_schema(changed)
        self.assertEqual(other["properties"]["matrix"]["properties"]["rows"]["maximum"], 48)
        self.assertEqual(other["properties"]["connector"]["properties"]["row_pins"]["maximum"], 50)
        self.assertEqual(other["properties"]["rows"]["maximum"], 48)  # the flat alias follows its target

    def test_schema_accepts_engine_inputs_and_rejects_unknown_keys(self) -> None:
        browser = {"name": "Tactile FPC 12x32", "rows": 12, "columns": 32, "pitch_x_mm": 2, "pitch_y_mm": 2,
                   "row_electrode_width_mm": 1.4, "column_electrode_width_mm": 1.4, "top_tail_length_mm": 12,
                   "bottom_tail_length_mm": 12, "connector_side": "bottom", "row_fpc_position": "top", "scan_order": "forward"}
        accepted = (default_design(), browser, {}, {"matrix": {"rows": 12.0}}, {"connector": {"row_pins": None, "column_pins": 40}},
                    {"tail": {"length_mm": 9}, "taxel_size_mm": 1.0, "scan_order": "reverse"},
                    {"project_name": "  Demo  "}, {"name": "触觉传感器 😀"})
        for design in accepted:
            with self.subTest(accepted=design):
                self.assertEqual(_errors(self.schema, design), [])
                self.assertTrue(check_design(design)["ok"])
        rejected = (
            {"colums": 3}, {"matrix": {"colums": 3}}, {"design": default_design()}, {"connector": {"pins": 9}},
            {"row_fpc_position": "middle"}, {"matrix": {"rows": 65}}, {"connector": {"row_pins": 65}},
            {"template_id": None}, {"schema_version": "tactile-fpc-design/v2"}, {"matrix": {"pitch_x_mm": 0.5}},
            {"tail": {"row_side": "middle"}}, {"project_name": "   "}, {"matrix": {"rows": True}}, {"matrix": {"rows": 12.5}},
            {"project_name": "a\x01b"}, {"project_name": "bad\x7fname"}, {"name": "x\x85y"}, {"project_name": "\ud800x"},
            {"connector": None},
        )
        for design in rejected:
            with self.subTest(rejected=design):
                self.assertNotEqual(_errors(self.schema, design), [])
                self.assertFalse(check_design(design)["ok"])

    def test_schema_valid_requests_pass_every_single_field_rule(self) -> None:
        # The schema is the conservative side of the contract: a request that
        # validates passes every per-field engine rule; the engine is more
        # lenient only by grid rounding (half a step), by trimming names, by
        # ignoring an overridden alias and, on the generic template, by the
        # diagonal Row bus's tails up to the surface profile's maximum (200 mm
        # since P5-diagonal-bus.md section 23; the schema and the browser's
        # form keep the generic profile's 80 mm).
        cross_field = {"E_ELECTRODE_GAP", "E_TAIL_SIDE_PARALLEL", "E_CONNECTOR_PINS", "E_BOARD_SIZE"}
        half_step = 5e-7
        tail_schema = self.schema["properties"]["tail"]["properties"]
        bus_tails = load_profile("surface_matrix_v1")["limits"]["maximum_tail_length_mm"]
        self.assertEqual((tail_schema["top_length_mm"]["maximum"], bus_tails), (self.profile["limits"]["maximum_tail_length_mm"], 200.0))

        def bus_tail(design) -> bool:
            # A tail length (nested or a flat alias) past the schema's maximum, within the bus's (the generic default
            # builds the bus).
            if len(design) != 1:
                return False
            (key, value), = design.items()
            spec = self.schema["properties"].get(key, {}) if "tail" in key else {}
            if key == "tail" and isinstance(value, dict) and len(value) == 1:
                (key, value), = value.items()
                spec = tail_schema.get(key, {})
            maximum = spec.get("maximum")
            return isinstance(value, (int, float)) and maximum is not None and maximum < value <= bus_tails
        cases = []
        for scope in ("matrix", "tail", "connector", None):
            properties = self.schema["properties"] if scope is None else self.schema["properties"][scope]["properties"]
            for key, spec in properties.items():
                if "minimum" not in spec:
                    continue
                for bound in (spec["minimum"], spec["maximum"]):
                    for delta in (-1.0, -0.5, -6e-7, -4e-7, -1e-9, 0.0, 1e-9, 4e-7, 6e-7, 0.5, 1.0):
                        value = bound + delta
                        cases.append(({key: value} if scope is None else {scope: {key: value}}, value - bound))
        names = ("Demo", "  Demo  ", "\tDemo\n", "Demo\n", "a\x01b", "a\x7fb", "x\x9f", "\ud800", "\U0001f600", "\ufeff",
                 "\u3000x\u3000", " ", "", "\u2028x", "x" * 80, " " + "x" * 80, "x" * 81, "\x1c", "De\nmo", "触觉传感器")
        cases += [({"project_name": name}, None) for name in names]
        cases += [({"pitch_x_mm": 99, "matrix": {"pitch_x_mm": 2}}, None), ({"name": "\x01", "project_name": "Demo"}, None),
                  ({"rows": [1], "row_num": 4}, None), ({"row_fpc_position": "middle", "role_mapping": {"top": "rows", "bottom": "columns"}}, None)]
        for design, offset in cases:
            with self.subTest(design=design):
                schema_ok = _errors(self.schema, design) == []
                errors = check_design(design)["validation"]["errors"]
                single_field = [issue for issue in errors if issue["code"] not in cross_field and issue["field"] != "role_mapping"]
                if schema_ok:
                    self.assertEqual(single_field, [])
                elif not errors:
                    shadowed = {entry["alias"] for entry in check_design(design)["validation"]["normalization"]["aliases_shadowed"]}
                    if shadowed:
                        lenient = all(problem.split(":")[0].split(".")[1] in shadowed for problem in _errors(self.schema, design))
                    elif offset is not None:
                        lenient = abs(offset) <= half_step or bus_tail(design)
                    else:
                        lenient = _errors(self.schema, {"project_name": design["project_name"].strip()}) == []
                    self.assertTrue(lenient, "the engine accepts what the schema rejects beyond the documented leniency")

    def test_issue_catalogue_lists_every_code_the_engine_emits(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "engine").glob("*.py")) if path.name != "schema.py")
        emitted = set(re.findall(r"\"([EW]_[A-Z_]+)\"", source))
        catalogue = issue_codes()
        listed = set(catalogue["errors"]) | set(catalogue["warnings"])
        self.assertTrue(emitted, "no codes found")
        self.assertEqual(emitted - listed, set(), "codes missing from engine.schema")
        self.assertEqual(listed - emitted, set(), "catalogue lists codes the engine never emits")
        self.assertEqual(self.schema["x-error-codes"], catalogue["errors"])
        self.assertEqual(self.schema["x-warning-codes"], catalogue["warnings"])
        for table in catalogue.values():
            for code, entry in table.items():
                self.assertEqual(set(entry), {"source", "meaning"}, code)


class UiProfileTests(unittest.TestCase):
    def test_limits_cover_every_field_including_the_connector(self) -> None:
        profile = load_profile()
        limits = input_limits(profile)
        self.assertEqual(set(limits), set(app.profile_for_ui()["limits"]))
        self.assertEqual(limits["connector.row_pins"]["maximum"], profile["connector"]["maximum_pins"])
        self.assertTrue(limits["connector.column_pins"]["nullable"])
        self.assertIsNone(limits["connector.column_pins"]["default"])
        self.assertEqual(limits["matrix.rows"]["aliases"], ["rows", "row_num"])
        self.assertEqual(limits["tail.top_length_mm"]["aliases"], ["tail.length_mm", "top_tail_length_mm", "tail_length_mm"])
        self.assertEqual(limits["matrix.pitch_x_mm"]["step"], 1e-6)
        self.assertEqual(limits["project_name"]["max_length"], profile["limits"]["maximum_project_name_length"])

    def test_display_rules_are_generated_from_the_profile(self) -> None:
        profile = load_profile()
        rules = app.display_rules(profile)
        self.assertEqual(rules["Column fan-out"], "≤16: one lane · 17–32: 2 lanes → one connector")
        # The bundle width and spacing come from the design (the default here), the rest from the profile.
        self.assertEqual(rules["Bundle traces"], "0.127 / 0.127 mm width / spacing (pitch 0.254 mm)")
        self.assertEqual(rules["Bundle range"], "width 0.1016–0.254 mm · spacing 0.1016–0.246 mm")
        self.assertEqual(rules["Gold-finger traces"], "0.254 mm at the 0.500 mm contact pitch, widened below every fan-out bend")
        self.assertEqual(rules["JLC trace minimum"], "0.1016 / 0.1016 mm for 1 oz copper (4/4 mil) · width ±20%")
        design = default_design()
        design["routing"] = {"trace_width_mm": 0.2, "trace_space_mm": 0.15}
        self.assertEqual(app.display_rules(profile, design)["Bundle traces"], "0.200 / 0.150 mm width / spacing (pitch 0.350 mm)")
        self.assertEqual(app.profile_for_ui(profile)["display_rules"], rules)
        changed = copy.deepcopy(profile)
        changed["fanout"]["maximum_channels_per_lane"] = 8
        changed["limits"]["maximum_columns"] = 16
        changed["stackup"]["stiffener_thickness_mm"] = 0.15
        changed["connector"]["maximum_pins"] = 40
        # The default copper is 0.035 mm (1 oz) since stage G; probe with the 0.5 oz value.
        changed["stackup"]["copper_thickness_mm"] = 0.018
        changed["routing"]["finger_trace_width_mm"] = 0.3
        other = app.display_rules(changed)
        self.assertEqual(other["Column fan-out"], "≤8: one lane · 9–16: 2 lanes → one connector")
        self.assertIn("0.150 mm", other["PI stiffener"])
        self.assertIn("up to 40 pins", other["Connector"])
        self.assertIn("0.018 mm", other["Copper construction"])
        self.assertIn(f"{profile['stackup']['copper_thickness_mm']:.3f} mm", rules["Copper construction"])
        self.assertEqual(other["JLC trace minimum"], "0.0889 / 0.0889 mm for 0.5 oz copper (3.5/3.5 mil) · width ±20%")
        self.assertIn("0.300 mm at the 0.500 mm contact pitch", other["Gold-finger traces"])
        single = copy.deepcopy(profile)
        single["fanout"]["maximum_lanes"] = 1
        single["fanout"]["maximum_channels_per_lane"] = 32
        self.assertEqual(app.display_rules(single)["Column fan-out"], "≤32: one lane")
        # No rule value is literal text in app.py.
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn(f"{profile['stackup']['stiffener_thickness_mm']:.3f} mm", rules["PI stiffener"])
        for literal in ("≤16", "17–32", "0.100 mm", "0.200 mm", "0.225 mm", "0.035 mm", "0.018 mm", "Single top copper", "Polyimide\"", "0.1016", "0.127", "0.254 mm", "4/4 mil"):
            self.assertNotIn(literal, source)


if __name__ == "__main__":
    unittest.main()
