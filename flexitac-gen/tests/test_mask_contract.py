"""The field mask contract (``matrix.mask``, masked-field phase P1).

A masked taxel field keeps the R x C readout (every ROW and COL net and
pin) while each row electrode spans only its active columns and each column
electrode only its active rows (claude/specs/masked-field/PLAN.md).  Phase
P1 adds the contract without geometry: the surface template accepts
``matrix.mask`` (one ``[first, last]`` pair of 1-based COL indices per
row), normalizes it (null and the full rectangle are the unmasked design,
integral floats become ints), validates it (E_MASK_*), adds ``mask`` to the
hashed identity of masked designs only, describes it in the surface schema
and limits, keeps the size advice from changing rows or columns, and gives
the frames of the mask on each board and the construction classes the
straight Row channel and Column fan-out accept.  From phase P2 on the masked
boards of those classes are built (tests/test_mask_layout.py) and a mask
outside them stops at E_MASK_ROUTING; from phase P3 on they export
(tests/test_mask_export.py).  The
generic template and unmasked surface designs are unchanged
(``test_generic_identity_guard``, ``test_surface_identity_guard``).
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import math
import re
import unittest
import zipfile
from pathlib import Path

from engine import (
    MASK_VERSION, check_design, column_frame_spans, column_spans, design_mask, design_schema, generate_design, input_limits,
    issue_codes, load_profile, mask_class, row_frame_spans, row_taper, validate_design,
)
from engine.core import GENERATOR_VERSION, IDENTITY_EXTRAS, MASK_TEMPLATES, OPTIONAL_FIELDS, _canonical_json, template_identity
from engine.diagonal import ROW_BUS_VERSION
from engine.geometry import rect_bounds, rotate_quarter
from engine.layout import TAIL_TURNS, _size_advice, column_plan, row_plan
from engine.schema import ERROR_CODES, WARNING_CODES, cross_field_rules
from exporters import EXPORTER_VERSION, ExportError, build_exports
from exporters import direct_gerber

try:
    import defaults_of_before
except ImportError:  # run as a package
    from tests import defaults_of_before


def setUpModule() -> None:
    # The default electrodes of before (1.4 mm at 2 mm, fill 0.7): this module's pinned numbers were measured with them
    # (tests/defaults_of_before.py; the user's decision of 2026-11-06 made the default fill 0.5).
    defaults_of_before.start()


ROOT = Path(__file__).resolve().parents[1]
SURFACE = "surface_matrix_v1"
GENERIC = "generic_matrix_v1"
TIGHT = {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016}
TRIANGLE = [[3, 5], [2, 5], [1, 5]]  # 3 x 5: every row reaches COL_05
MASK_CODES = {code for code in {**ERROR_CODES, **WARNING_CODES} if code.startswith(("E_MASK_", "W_MASK_"))}
_SIDES = ("bottom", "top", "left", "right")
_OPPOSITE = {"bottom": "top", "top": "bottom", "left": "right", "right": "left"}
# Digests of the contract documents before the field mask (the frozen tree of 2026-10-21), without
# what the mask adds: the surface schema's matrix.mask, its cross-field rule and section note, and
# the issue catalogue, which every template shares (x-error-codes, x-warning-codes); nor what the
# diagonal Row bus adds the same way (routing.row_sides, P5b; tests/test_diagonal_bus.py; on the generic template too
# since P5-diagonal-bus.md section 18, its input limit as well).  The generic documents changed once more with section
# 20: its default, the diagonal Row bus, takes CAD mode's rule set, so its columns and tail bounds and their descriptions
# are the surface profile's, the straight channel's under x-channel (channel), with x-row-bus-profile and a cross-field
# rule (before: 6bacfee9... and b7243bac...).  And with section 23 (2026-10-25), the surface profile's tails to 200 mm:
# the surface schema and limits name the 200 mm maximum (before: 1888c416... and bd48020e...), the generic schema the
# surface profile's new digest in x-row-bus-profile (before: 638c3641...); the generic limits keep the generic profile's
# 80 mm.  And with section 27.7 (2026-10-27, the rectangular mode's default tails 12 / 12 mm): the generic schema's and
# limits' default bottom tail 12 mm and the schema's "Absent: 12 mm with the bus" (before: c3a4c028... and 2c2a931d...);
# the surface documents unchanged (its preset keeps 7.5 mm).  And with the profile revision 2026-10-29 (the gold-finger
# thickness order option and the coverlay-window notes): the generic schema's x-profile and x-row-bus-profile name both
# profiles' new revision and digest (before: a79e66ad...), the surface schema's x-profile the surface profile's (before:
# ebb2976c...); the limits unchanged.  And with the user's decision of 2026-11-06 (the default fill 0.7 -> 0.5): every
# schema's and limits' default electrode widths 1.0 mm (1.4 before: e495f1c6..., 8154a3c0..., 938f3f6f... and
# 13345dbc...).  Re-pinned by the profile revision 2026-11-06 (the order: JLC's 2-layer 0.2 mm FPC, the bottom copper
# empty): the generic schema's x-profile and x-row-bus-profile name both profiles' new revision and digest (before:
# 45c0b8e3...), the surface schema's x-profile the surface profile's (before: 61d8f76a...); the limits unchanged.
# Re-pinned by the profile revision 2026-11-06b (the user's later decision of 2026-11-06: the PI stiffener 0.225 ->
# 0.1 mm): the same three names of the profiles' revision and digest (before: 4babcb58... and d69de578...); the limits
# unchanged.
GENERIC_SCHEMA_SHA256 = "6e45123b7b0f1f68c7298545d19768d389da51a473e3f626076dbe4708a7f24a"
GENERIC_LIMITS_SHA256 = "8eb88e9e6031676226c4db419c7a6fe1b62b9b0c4dc4df7678ec73fea42233f8"
SURFACE_SCHEMA_SHA256 = "d74df56b506499c2cb57da74a154ab92cfa8c1f2e36d92f72714b0d33b851f4e"
SURFACE_LIMITS_SHA256 = "e143c63fbddc5ce488df0780f9f52755899a66a21d62fb472ffce1fbc55b0f5e"


def _surface(rows: int, columns: int, mask=None, **sections) -> dict:
    matrix = {"rows": rows, "columns": columns}
    if mask is not None:
        matrix["mask"] = mask
    return {"template_id": SURFACE, "matrix": matrix, **sections}


def _issues(result: dict, kind: str = "errors") -> list:
    return [(issue["code"], issue["field"]) for issue in result["validation"][kind]]


def _sha256(value) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _without_mask(schema: dict) -> dict:
    """A schema without what the field mask adds (see the digests above)."""

    schema = json.loads(json.dumps(schema))
    del schema["x-error-codes"], schema["x-warning-codes"]
    matrix = schema["properties"]["matrix"]
    matrix["properties"].pop("mask", None)
    matrix["description"] = matrix["description"].replace("; optional: mask.", ".")
    routing = schema["properties"]["routing"]
    routing["properties"].pop("row_sides", None)
    routing["description"] = routing["description"].replace("; optional: row_sides.", ".")
    schema["x-cross-field-rules"] = [
        rule for rule in schema["x-cross-field-rules"] if not rule.startswith(("matrix.mask", "routing.row_sides"))
    ]
    return schema


class MaskNormalizationTests(unittest.TestCase):
    def test_each_code_at_its_field(self) -> None:
        cases = (
            ("not an array", "x", [("E_MASK_TYPE", "matrix.mask")]),
            ("an object", {"0": [1, 5]}, [("E_MASK_TYPE", "matrix.mask")]),
            ("bad entries", [[1, 5], [True, 2], [1.5, 3], [1, 2, 3], 4, [2**53, 5]],
             [("E_MASK_TYPE", f"matrix.mask[{index}]") for index in range(1, 6)]),
            ("rows", [[1, 5], [1, 5]], [("E_MASK_ROWS", "matrix.mask")]),
            ("range", [[0, 5], [4, 3], [1, 6]], [("E_MASK_RANGE", "matrix.mask[0]"), ("E_MASK_RANGE", "matrix.mask[1]"), ("E_MASK_RANGE", "matrix.mask[2]")]),
            ("disconnected", [[1, 2], [3, 5], [3, 5]], [("E_MASK_DISCONNECTED", "matrix.mask[1]")]),
            ("empty column", [[1, 4], [1, 4], [1, 4]], [("E_MASK_COLUMN_EMPTY", "matrix.mask")]),
            ("column gap", [[1, 5], [1, 2], [1, 5]], [("E_MASK_COLUMN_GAP", "matrix.mask")] * 3),
            ("valid, of the straight classes", TRIANGLE, []),
        )
        for name, mask, expected in cases:
            with self.subTest(case=name):
                result = check_design(_surface(3, 5, mask))
                self.assertEqual(_issues(result), expected)
                self.assertEqual(result["ok"], not expected)
        # The messages name the nets.
        gap = check_design(_surface(3, 5, [[1, 5], [1, 2], [1, 5]]))["validation"]["errors"][0]["message"]
        self.assertIn("COL_03 has taxels in ROW_01..ROW_03 but not in ROW_02", gap)
        empty = check_design(_surface(3, 5, [[1, 4], [1, 4], [1, 4]]))["validation"]["errors"][0]["message"]
        self.assertIn("COL_05 has no taxel", empty)
        apart = check_design(_surface(3, 5, [[1, 2], [3, 5], [3, 5]]))["validation"]["errors"][0]["message"]
        self.assertIn("ROW_01 (COL_01..COL_02) and ROW_02 (COL_03..COL_05) share no column", apart)

    def test_null_and_full_masks_are_the_unmasked_design(self) -> None:
        plain = check_design(_surface(3, 5))
        built = generate_design(_surface(3, 5))
        self.assertTrue(built["ok"], built["validation"]["errors"][:3])
        for mask in (None, [[1, 5]] * 3, [[1.0, 5.0]] * 3, ((1, 5), (1, 5), (1, 5))):
            with self.subTest(mask=mask):
                request = _surface(3, 5)
                request["matrix"]["mask"] = mask
                result = check_design(request)
                self.assertTrue(result["ok"], result["validation"]["errors"])
                self.assertEqual(result["design"], plain["design"])
                self.assertNotIn("mask", result["design"]["matrix"])
                self.assertEqual(result["identity"], plain["identity"])
                normalized = result["validation"]["normalization"]["values_normalized"]
                if mask is None:
                    self.assertEqual(normalized, [])
                else:
                    self.assertEqual(normalized, [{"field": "matrix.mask", "from": json.loads(json.dumps(mask)), "to": None,
                                                   "reason": "the full rows x columns rectangle is the unmasked design"}])
                self.assertEqual(generate_design(request)["manifest"]["build_id"], built["manifest"]["build_id"])
        # The full check reads rows and columns after their aliases.
        aliased = check_design({"template_id": SURFACE, "rows": 3, "columns": 5, "matrix": {"mask": [[1, 5]] * 3}})
        self.assertEqual(aliased["identity"]["build_id"], plain["identity"]["build_id"])
        # A mask is never a default.
        self.assertNotIn("matrix.mask", plain["validation"]["normalization"]["defaults_applied"])

    def test_integral_floats_become_integers(self) -> None:
        result = check_design(_surface(3, 5, [[3.0, 5], [2, 5.0], [1, 5]]))
        self.assertEqual(result["design"]["matrix"]["mask"], TRIANGLE)
        self.assertEqual(json.dumps(result["design"]["matrix"]["mask"]), "[[3, 5], [2, 5], [1, 5]]")
        self.assertEqual(result["validation"]["normalization"]["values_normalized"], [
            {"field": "matrix.mask", "from": [[3.0, 5], [2, 5.0], [1, 5]], "to": TRIANGLE, "reason": "integral numbers written as integers"},
        ])
        self.assertEqual(result["identity"], check_design(_surface(3, 5, TRIANGLE))["identity"])
        self.assertEqual(check_design(_surface(3, 5, TRIANGLE))["validation"]["normalization"]["values_normalized"], [])

    def test_a_rejected_mask_becomes_null(self) -> None:
        result = check_design(_surface(3, 5, [[1, 5], "x", [1, 5]]))
        self.assertEqual(_issues(result), [("E_MASK_TYPE", "matrix.mask[1]")])
        self.assertIsNone(result["design"]["matrix"]["mask"])
        self.assertNotIn("mask", result["identity"])
        self.assertIn('matrix.mask[1] must be a [first, last] pair of integer column indices (got "x")', result["validation"]["errors"][0]["message"])

    def test_the_generic_template_refuses_a_mask(self) -> None:
        for request in ({"matrix": {"rows": 3, "columns": 5, "mask": TRIANGLE}}, {"template_id": GENERIC, "matrix": {"mask": None}}):
            with self.subTest(request=request):
                result = check_design(request)
                self.assertEqual(_issues(result), [("E_UNKNOWN_FIELD", "matrix.mask")])
                self.assertEqual(result["validation"]["errors"][0]["message"], "Unknown field matrix.mask; matrix.mask needs template_id 'surface_matrix_v1'.")
                self.assertNotIn("mask", result["design"]["matrix"])
                self.assertNotIn("mask", result["identity"])
        # A generic design built by hand that carries one is refused as well.
        design = check_design({"matrix": {"rows": 3, "columns": 5}})["design"]
        design["matrix"]["mask"] = TRIANGLE
        self.assertEqual([(issue["code"], issue["field"]) for issue in validate_design(design)["errors"]], [("E_UNKNOWN_FIELD", "matrix.mask")])
        self.assertEqual(OPTIONAL_FIELDS, ("matrix.mask", "routing.row_sides"))
        self.assertEqual(MASK_TEMPLATES, frozenset({SURFACE}))

    def test_mask_issues_are_capped(self) -> None:
        result = check_design(_surface(30, 5, [[0, 9]] * 30))
        errors = result["validation"]["errors"]
        self.assertEqual(len(errors), 21)
        self.assertEqual({issue["code"] for issue in errors}, {"E_MASK_RANGE"})
        self.assertEqual(errors[-1], {"code": "E_MASK_RANGE", "field": "matrix.mask", "message": "10 more matrix.mask issues are not listed."})
        typed = check_design(_surface(3, 5, ["x"] * 25))["validation"]["errors"]
        self.assertEqual(len(typed), 21)
        self.assertEqual(typed[-1]["message"], "5 more matrix.mask issues are not listed.")

    def test_the_construction_classes_gate_the_build(self) -> None:
        # A valid mask of the straight classes gets its boards; one outside them stops at E_MASK_ROUTING,
        # naming the first row the straight Row channel refuses, before any geometry.
        built = generate_design(_surface(3, 5, TRIANGLE))
        self.assertEqual(set(built["boards"]), {"row", "column"})
        self.assertNotIn("E_MASK_ROUTING", [code for code, _ in _issues(built)])
        lower_left = [[1, row] for row in range(1, 9)]
        result = generate_design(_surface(8, 8, lower_left))
        self.assertFalse(result["ok"])
        self.assertEqual(result["boards"], {})
        self.assertEqual(_issues(result), [("E_MASK_ROUTING", "matrix.mask[0]")])
        self.assertIn("ROW_01 ends at COL_01 on the Row-channel side, 7 column(s) short of COL_08", result["validation"]["errors"][0]["message"])
        with self.assertRaises(ExportError):
            build_exports(result)

    def test_the_inactive_gap_warning(self) -> None:
        fine = {"pitch_x_mm": 0.6, "pitch_y_mm": 0.6, "taxel_width_mm": 0.35, "taxel_height_mm": 0.35}
        request = _surface(3, 5, TRIANGLE)
        request["matrix"].update(fine)
        warnings = check_design(request)["validation"]["warnings"]
        gap = [issue for issue in warnings if issue["code"] == "W_MASK_INACTIVE_GAP"]
        self.assertEqual([issue["field"] for issue in gap], ["matrix.pitch_x_mm"])
        # max(0.6 - 0.35, 0.6 - 0.35) - 0.2 mm overhang.
        self.assertIn("are 0.05 mm from the electrodes beside them", gap[0]["message"])
        # Either gap is enough: a wider row gap clears it, the default 2.0/1.4 mm field (0.4 mm) as well.
        wider = copy.deepcopy(request)
        wider["matrix"].update(pitch_y_mm=1.0)
        for clear in (wider, _surface(3, 5, TRIANGLE)):
            self.assertNotIn("W_MASK_INACTIVE_GAP", {issue["code"] for issue in check_design(clear)["validation"]["warnings"]})
        # Unmasked designs never get it.
        plain = _surface(3, 5)
        plain["matrix"].update(fine)
        self.assertNotIn("W_MASK_INACTIVE_GAP", {issue["code"] for issue in check_design(plain)["validation"]["warnings"]})


class MaskIdentityTests(unittest.TestCase):
    def test_the_mask_is_in_the_identity_only_when_masked(self) -> None:
        masked, plain = generate_design(_surface(3, 5, TRIANGLE)), generate_design(_surface(3, 5))
        identity = check_design(_surface(3, 5, TRIANGLE))["identity"]
        self.assertEqual((identity["template"], identity["mask"]), ("surface-matrix/1", MASK_VERSION))
        self.assertEqual(MASK_VERSION, "field-mask/1")
        self.assertNotIn("mask", plain["manifest"])
        self.assertNotIn("mask", check_design(_surface(3, 5))["identity"])
        manifest = masked["manifest"]
        self.assertEqual((manifest["template"], manifest["mask"]), ("surface-matrix/1", MASK_VERSION))
        self.assertEqual(manifest["build_id"], identity["build_id"])
        hashed = {
            "design_sha256": _sha256(masked["design"]), "profile_sha256": _sha256(masked["profile"]), "generator": GENERATOR_VERSION,
            "exporter": EXPORTER_VERSION, "template": "surface-matrix/1", "mask": MASK_VERSION,
        }
        self.assertEqual(manifest["build_sha256"], _sha256(hashed))
        self.assertNotEqual(manifest["build_id"], plain["manifest"]["build_id"])
        self.assertEqual(template_identity(masked["design"]), {"template": "surface-matrix/1", "mask": MASK_VERSION})
        self.assertEqual(template_identity(plain["design"]), {"template": "surface-matrix/1"})
        # The generic default is the diagonal Row bus (P5-diagonal-bus.md section 18), one construction on both templates
        # (diagonal-bus/8, section 20; diagonal-bus/9 since section 24, diagonal-bus/10 since section 27, diagonal-bus/11
        # since section 27.8); its straight channel adds nothing.
        self.assertEqual(template_identity(check_design({})["design"]), {"row_bus": ROW_BUS_VERSION})
        surface_bus = check_design({"template_id": "surface_matrix_v1", "routing": {"row_sides": "both"}})["design"]
        self.assertEqual(template_identity(surface_bus), {"template": "surface-matrix/1", "row_bus": ROW_BUS_VERSION})
        self.assertEqual(ROW_BUS_VERSION, "diagonal-bus/11")
        self.assertEqual(template_identity(check_design({"routing": {"row_sides": "channel"}})["design"]), {})
        self.assertEqual(IDENTITY_EXTRAS, ("template", "mask", "row_bus"))

    def test_the_exporter_names_the_identity_extras(self) -> None:
        masked, plain = generate_design(_surface(3, 5, TRIANGLE)), generate_design(_surface(3, 5))
        fields = direct_gerber._identity_fields(masked["manifest"])
        self.assertEqual((fields["template"], fields["mask"]), ("surface-matrix/1", MASK_VERSION))
        recipe = "sha256 of the canonical JSON of {design_sha256, profile_sha256, generator, exporter, template"
        self.assertEqual(direct_gerber._build_hash_recipe(masked["manifest"]), recipe + ", mask}")
        self.assertEqual(direct_gerber._build_hash_recipe(plain["manifest"]), recipe + "}")
        self.assertNotIn("mask", direct_gerber._identity_fields(plain["manifest"]))
        # The exporter's own identity check recomputes the masked build hash.
        direct_gerber._check_identity(_canonical_json(masked["design"]), _canonical_json(masked["profile"]), masked["profile"], masked["manifest"])
        changed = dict(masked["manifest"], build_sha256=plain["manifest"]["build_sha256"])
        with self.assertRaises(ExportError):
            direct_gerber._check_identity(_canonical_json(masked["design"]), _canonical_json(masked["profile"]), masked["profile"], changed)


class MaskExportTests(unittest.TestCase):
    def test_masked_builds_export_from_phase_p3_on(self) -> None:
        # P2 refused every masked build; P3 writes the polygon window's region and the taxel map
        # (tests/test_mask_export.py), with a polygon field window and with per-electrode windows alike.
        sparse = {"pitch_x_mm": 3.0, "pitch_y_mm": 3.0, "taxel_width_mm": 1.0, "taxel_height_mm": 1.0}
        for name, matrix, window in (("polygon field window", {}, "polygon"), ("per-electrode windows", sparse, "rectangle")):
            with self.subTest(case=name):
                request = _surface(10, 10, [[10 - row, 10] for row in range(10)])
                request["matrix"].update(matrix)
                result = generate_design(request)
                self.assertTrue(result["ok"], result["validation"]["errors"][:2])
                shapes = {opening.get("shape", "rectangle") for opening in result["boards"]["row"]["layers"]["top_coverlay_openings"]}
                self.assertEqual(shapes, {window, "rectangle"} if window == "polygon" else {"rectangle"})
                exports = build_exports(result)
                self.assertEqual(set(exports), set(direct_gerber.ARTIFACT_KEYS))
                with zipfile.ZipFile(io.BytesIO(exports["project_review_bundle_zip"])) as bundle:
                    self.assertIn("taxels.csv", bundle.namelist())
        self.assertFalse(hasattr(direct_gerber, "_refuse_masked_field"))
        # The unmasked design exports without a taxel map.
        with zipfile.ZipFile(io.BytesIO(build_exports(generate_design(_surface(10, 10)))["project_review_bundle_zip"])) as bundle:
            self.assertNotIn("taxels.csv", bundle.namelist())


class MaskSchemaTests(unittest.TestCase):
    def test_the_surface_schema_and_limits_describe_the_mask(self) -> None:
        surface = load_profile(SURFACE)
        schema = design_schema(surface)["properties"]["matrix"]
        mask = schema["properties"]["mask"]
        self.assertEqual({key: mask[key] for key in mask if key != "description"}, {
            "type": ["array", "null"], "minItems": 1, "maxItems": 64, "default": None,
            "items": {"type": "array", "minItems": 2, "maxItems": 2, "items": {"type": "integer", "minimum": 1, "maximum": 64}},
        })
        self.assertIn("one [first, last] pair of 1-based COL indices per row", mask["description"])
        self.assertEqual(schema["description"], "matrix section: rows, columns, pitch_x_mm, pitch_y_mm, taxel_width_mm, taxel_height_mm; optional: mask.")
        limits = input_limits(surface)["matrix.mask"]
        self.assertEqual((limits["type"], limits["default"], limits["aliases"], limits["nullable"]), ("mask", None, [], True))
        self.assertEqual((limits["min_items"], limits["max_items"], limits["index_minimum"], limits["index_maximum"]), (1, 64, 1, 64))
        rules = [rule for rule in cross_field_rules(surface) if rule.startswith("matrix.mask")]
        self.assertEqual(len(rules), 1)
        for code in ("E_MASK_ROWS", "E_MASK_RANGE", "E_MASK_DISCONNECTED", "E_MASK_COLUMN_EMPTY", "E_MASK_COLUMN_GAP"):
            self.assertIn(code, rules[0])

    def test_the_contract_documents_change_only_by_the_mask(self) -> None:
        generic, surface = load_profile(), load_profile(SURFACE)
        self.assertNotIn("mask", design_schema(generic)["properties"]["matrix"]["properties"])
        self.assertNotIn("matrix.mask", input_limits(generic))
        self.assertEqual(_sha256(_without_mask(design_schema(generic))), GENERIC_SCHEMA_SHA256)
        self.assertEqual(_sha256({key: value for key, value in input_limits(generic).items() if key not in OPTIONAL_FIELDS}), GENERIC_LIMITS_SHA256)
        self.assertEqual(_sha256(_without_mask(design_schema(surface))), SURFACE_SCHEMA_SHA256)
        surface_limits = input_limits(surface).items()
        self.assertEqual(_sha256({key: value for key, value in surface_limits if key not in OPTIONAL_FIELDS}), SURFACE_LIMITS_SHA256)
        # The issue catalogue is shared by the templates and lists the mask codes.
        self.assertEqual(MASK_CODES, {"E_MASK_TYPE", "E_MASK_ROWS", "E_MASK_RANGE", "E_MASK_DISCONNECTED", "E_MASK_COLUMN_EMPTY",
                                      "E_MASK_COLUMN_GAP", "E_MASK_ROUTING", "W_MASK_INACTIVE_GAP"})
        catalogue = issue_codes()
        self.assertLessEqual(MASK_CODES, set(catalogue["errors"]) | set(catalogue["warnings"]))
        self.assertEqual(design_schema(generic)["x-error-codes"], catalogue["errors"])
        self.assertEqual(catalogue["errors"]["E_MASK_ROUTING"]["source"], "feasibility")

    def test_api_md_lists_every_mask_code(self) -> None:
        text = (ROOT / "docs" / "API.md").read_text(encoding="utf-8")
        lines = text.splitlines()
        start = lines.index("### Field mask (`matrix.mask`)")
        end = next(index for index in range(start + 1, len(lines)) if lines[index].startswith(("# ", "## ", "### ")))
        rows = [line.strip().strip("|").split("|") for line in lines[start:end] if line.startswith("| `")]
        self.assertEqual({row[0].strip().strip("`") for row in rows}, MASK_CODES)
        for row in rows:
            with self.subTest(code=row[0]):
                self.assertEqual(row[2].strip().split(" ")[0].strip("`"), (ERROR_CODES.get(row[0].strip().strip("`")) or WARNING_CODES[row[0].strip().strip("`")])[0])
        identity = text[text.index("## Build identity"):text.index("## HTTP server")]
        self.assertIn(f"`mask` (`{MASK_VERSION}`)", identity)


class MaskSizeAdviceTests(unittest.TestCase):
    def test_the_size_advice_never_changes_rows_or_columns_of_a_masked_design(self) -> None:
        oversize = {"rows": 64, "columns": 8, "pitch_y_mm": 8.0, "taxel_height_mm": 4.0}
        mask = [[2, 8]] + [[1, 8]] * 63
        plain = check_design({"template_id": SURFACE, "matrix": oversize})
        masked = check_design({"template_id": SURFACE, "matrix": dict(oversize, mask=mask)})
        # Both boards are too long; unmasked, fewer rows is one of the ways out.
        self.assertTrue(all("matrix.rows <= " in issue["message"] for issue in plain["validation"]["errors"]))
        self.assertEqual([issue["code"] for issue in masked["validation"]["errors"]], ["E_BOARD_SIZE", "E_BOARD_SIZE"])
        for issue in masked["validation"]["errors"][:2]:
            self.assertNotIn("matrix.rows", issue["message"])
            self.assertNotIn("matrix.columns", issue["message"])
            self.assertIn("matrix.pitch_y_mm <= ", issue["message"])
        profile = load_profile(SURFACE)
        for role in ("rows", "columns"):
            with self.subTest(role=role):
                advice = _size_advice(masked["design"], profile, role, row_plan if role == "rows" else column_plan)
                self.assertFalse({key for values in advice for key in values} & {("matrix", "rows"), ("matrix", "columns")})


class MaskFrameTests(unittest.TestCase):
    def _design(self, mask, row_side: str = "bottom", column_side: str = "bottom", rows: int = 3, columns: int = 5) -> dict:
        design = check_design({"template_id": SURFACE, "matrix": {"rows": rows, "columns": columns},
                               "tail": {"row_side": row_side, "column_side": column_side}})["design"]
        if mask is not None:
            design["matrix"]["mask"] = mask
        return design

    def test_hand_computed_frames(self) -> None:
        self.assertEqual(column_spans(TRIANGLE, 5), [(3, 3), (2, 3), (1, 3), (1, 3), (1, 3)])
        self.assertEqual(design_mask(self._design(TRIANGLE)), ((3, 5), (2, 5), (1, 5)))
        self.assertIsNone(design_mask(self._design(None)))
        # Equal tail sides: the Row channel faces COL_05, ROW_03 is next to the Column tail.
        equal = self._design(TRIANGLE)
        self.assertEqual(row_frame_spans(equal), [(0, 2), (0, 3), (0, 4)])
        self.assertEqual(column_frame_spans(equal), [(0, 0), (0, 1), (0, 2), (0, 2), (0, 2)])
        # Opposite sides: the Row channel faces COL_01, ROW_01 is next to the Column tail.
        opposite = self._design(TRIANGLE, "bottom", "top")
        self.assertEqual(row_frame_spans(opposite), [(2, 4), (1, 4), (0, 4)])
        self.assertEqual(column_frame_spans(opposite), [(2, 2), (1, 2), (0, 2), (0, 2), (0, 2)])
        # Unmasked: the full rectangle in every frame.
        self.assertEqual(row_frame_spans(self._design(None)), [(0, 4)] * 3)
        self.assertEqual(column_frame_spans(self._design(None, "left", "right")), [(0, 2)] * 5)

    def test_the_frames_match_the_stacked_boards(self) -> None:
        # Each net's slot measured on generated boards: the electrodes of both boards stacked on the
        # active field (the physical top board turned over about its tail axis), then taken back into
        # the Row and the Column board's canonical frames.
        masks = (TRIANGLE, [[1, 1], [1, 5], [5, 5]], [[2, 4], [1, 5], [1, 3]])
        for row_side in _SIDES:
            for column_side in (row_side, _OPPOSITE[row_side]):
                for top in ("rows", "columns"):
                    request = {"template_id": SURFACE, "matrix": {"rows": 3, "columns": 5}, "tail": {"row_side": row_side, "column_side": column_side},
                               "role_mapping": {"top": top, "bottom": "columns" if top == "rows" else "rows"}}
                    with self.subTest(row_side=row_side, column_side=column_side, top=top):
                        result = generate_design(request)
                        self.assertTrue(result["ok"], result["validation"]["errors"][:3])
                        stacked = {}
                        for board in result["boards"].values():
                            region = board["grid_registration"]["active_region"]
                            centre = (region["x"] + region["width"] / 2, region["y"] + region["height"] / 2)
                            for electrode in board["layers"]["top_copper"]["electrodes"]:
                                x0, y0, x1, y1 = rect_bounds(electrode)
                                point = [(x0 + x1) / 2 - centre[0], (y0 + y1) / 2 - centre[1]]
                                stacked[electrode["net"]] = self._turn_over(point, board)
                        row_board, column_board = result["boards"]["row"], result["boards"]["column"]
                        across = {c: self._canonical(stacked[f"COL_{c:02d}"], row_board)[0] for c in range(1, 6)}
                        along = {r: self._canonical(stacked[f"ROW_{r:02d}"], column_board)[1] for r in range(1, 4)}
                        column_slot = {c: rank for rank, c in enumerate(sorted(across, key=across.get))}  # from the Row channel
                        row_slot = {r: rank for rank, r in enumerate(sorted(along, key=along.get))}  # from the Column tail
                        for mask in masks:
                            design = copy.deepcopy(result["design"])
                            design["matrix"]["mask"] = mask
                            expected_rows = [(min(column_slot[c] for c in range(first, last + 1)), max(column_slot[c] for c in range(first, last + 1)))
                                             for first, last in mask]
                            runs = column_spans(mask, 5)
                            expected_columns = [(min(row_slot[r] for r in range(first, last + 1)), max(row_slot[r] for r in range(first, last + 1)))
                                                for first, last in runs]
                            self.assertEqual(row_frame_spans(design), expected_rows)
                            self.assertEqual(column_frame_spans(design), expected_columns)

    @staticmethod
    def _turn_over(point: list, board: dict) -> list:
        if board["physical_side"] != "top":
            return point
        return [-point[0], point[1]] if board["tail"]["side"] in ("bottom", "top") else [point[0], -point[1]]

    def _canonical(self, point: list, board: dict) -> list:
        return rotate_quarter(self._turn_over(point, board), -TAIL_TURNS[board["tail"]["side"]])


class MaskClassTests(unittest.TestCase):
    def test_the_lane_taper(self) -> None:
        profile = load_profile(SURFACE)
        for routing, first in ((TIGHT, 0.852601), ({}, 0.878001)):
            with self.subTest(routing=routing):
                design = check_design({"template_id": SURFACE, "routing": routing})["design"]
                plan = row_plan(design, profile)
                taper = row_taper(design, profile)
                self.assertEqual(taper[0], first)
                self.assertEqual(len(taper), plan["rows"])
                # Lane k plus the window gap (0.1 expansion, 0.15 opening-to-trace, half a trace, one grid
                # step) and the 0.2 mm overhang; the unmasked field starts at the last one.
                pitch = plan["bundle_pitch"]
                self.assertTrue(all(abs(b - a - pitch) < 1e-9 for a, b in zip(taper, taper[1:])))
                self.assertEqual(plan["active"][0], max(taper[-1], 0.5))
        # Other channels keep their full width: no taper.
        generic = load_profile()
        design = check_design({})["design"]
        self.assertEqual(row_taper(design, generic), [row_plan(design, generic)["active"][0]] * 12)

    def test_a_tapered_mask_is_straight(self) -> None:
        # The soft finger's taper: the top row reaches the channel side and the rows below step away
        # from it by the room their lanes need, tau_k = ceil((W_k - W_1) / pitch_x).
        profile = load_profile(SURFACE)
        design = check_design({"template_id": SURFACE, "matrix": {"rows": 40, "columns": 8}, "routing": TIGHT})["design"]
        taper = row_taper(design, profile)
        taus = [max(0, math.ceil(round((edge - taper[0]) / 2.0, 9) - 1e-9)) for edge in taper]
        self.assertEqual((taus[0], taus[-1]), (0, 4))
        mask = [[1, 8 - tau] for tau in taus]
        request = {"template_id": SURFACE, "matrix": {"rows": 40, "columns": 8, "mask": mask}, "routing": TIGHT}
        checked = check_design(request)
        self.assertEqual(_issues(checked), [])  # valid and of the straight classes
        self.assertEqual(mask_class(checked["design"], profile), ({"row": "straight", "column": "straight"}, None))
        self.assertEqual([lo for lo, _ in row_frame_spans(checked["design"])], taus)
        # One row stepping away a column more than its taper needs leaves the class (the last row of a step keeps
        # the columns contiguous).
        step = next(index for index in range(1, 39) if taus[index + 1] > taus[index])
        wider = copy.deepcopy(mask)
        wider[step][1] -= 1
        checked = check_design(dict(request, matrix=dict(request["matrix"], mask=wider)))
        self.assertEqual([issue["code"] for issue in checked["validation"]["errors"]], ["E_MASK_ROUTING"])  # a valid mask
        classes, issue = mask_class(checked["design"], profile)
        self.assertIsNone(classes)
        self.assertEqual(issue["field"], f"matrix.mask[{step}]")
        self.assertIn(f"ROW_{step + 1:02d} ends at COL_{wider[step][1]:02d} on the Row-channel side, 1 column(s) short of COL_{mask[step][1]:02d}",
                      issue["message"])
        self.assertEqual(_issues(checked), [("E_MASK_ROUTING", f"matrix.mask[{step}]")])
        self.assertEqual(checked["validation"]["errors"][0], issue)

    def test_triangles_by_their_right_angle_and_the_tail_sides(self) -> None:
        profile = load_profile(SURFACE)

        def classify(mask, column_side="bottom"):
            design = check_design({"template_id": SURFACE, "matrix": {"rows": 8, "columns": 8, "mask": mask},
                                   "tail": {"row_side": "bottom", "column_side": column_side}})["design"]
            return mask_class(design, profile)

        upright = [[9 - row, 8] for row in range(1, 9)]  # every row reaches COL_08, the floor spans all
        lower_left = [[1, row] for row in range(1, 9)]  # every row reaches COL_01
        inverted = [[row, 8] for row in range(1, 9)]  # the top row spans all
        self.assertEqual(classify(upright), ({"row": "straight", "column": "straight"}, None))
        # Equal sides put the Row channel at COL_08: rows ending at COL_01.. stop short of it (A).
        _, issue = classify(lower_left)
        self.assertEqual(issue["field"], "matrix.mask[0]")
        self.assertIn("ROW_01 ends at COL_01 on the Row-channel side, 7 column(s) short of COL_08 (6 more row(s) stop short)", issue["message"])
        # Opposite sides put it at COL_01, so the lower-left triangle passes A, but its Column tail is at ROW_01:
        # COL_02..COL_08 end before it and ROW_01 does not reach them (B).
        _, issue = classify(lower_left, "top")
        self.assertEqual(issue["field"], "matrix.mask[0]")
        self.assertIn("COL_02 ends at ROW_02, and ROW_01, next to it on the Column-tail side, ends at COL_01", issue["message"])
        self.assertIn("(6 more column(s) end so)", issue["message"])
        # An inverted triangle reaches the channel but not the Column tail (B).
        _, issue = classify(inverted)
        self.assertEqual(issue["field"], "matrix.mask[1]")
        self.assertIn("COL_01 ends at ROW_01, and ROW_02, next to it on the Column-tail side, ends at COL_02", issue["message"])
        # An isosceles triangle fails A at its top row.
        _, issue = classify([[5 - (row + 1) // 2, 4 + (row + 1) // 2] for row in range(1, 9)])
        self.assertEqual(issue["field"], "matrix.mask[0]")
        self.assertEqual(mask_class(check_design(_surface(3, 5))["design"], profile), (None, None))


if __name__ == "__main__":
    unittest.main()
