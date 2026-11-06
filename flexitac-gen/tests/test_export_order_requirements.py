"""JLCPCB order requirements of the profile (stage G, approved 2026-10-14).

The profile's ``order`` block, the stack-up of the ordered build and the
sources they cite are validated on load; the
resolved order requirements (``engine.profile.order_requirements``) are the
same everywhere a person orders or reviews boards: ORDER_NOTES.txt in each
board ZIP and in the review bundle, both manifests, ``/api/default`` and the
browser's manufacturing note.  The exporter refuses notes that drop an entry
or state contact figures the boards do not have.
"""

from __future__ import annotations

import ast
import copy
import io
import json
import re
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import app
from engine import default_design, generate_design, load_profile
from engine import profile as profile_module
from engine.profile import order_requirements
from exporters import ExportError, artifact_filenames, build_exports
from exporters import direct_gerber

ROOT = Path(__file__).resolve().parents[1]
NOTES = "ORDER_NOTES.txt"
# 0.025 mm core + 0.035 mm copper + 0.225 mm stiffener under the open coverlay.
DEFAULT_ZONE_MM = 0.285
# The approved defaults (2026-10-14), restated: 1-layer 0.11 mm FPC (JLC's 1 oz
# copper build), 0.225 mm PI at the contacts, +/-0.05 mm outline on request,
# ENIG, and the review notes (the trace note since the necked routing of 2026-10-15).
# Profile revision 2026-10-29: the gold-finger thickness of the contact zone ordered in total (JLC's
# gold-finger stiffener ordering guide), and the coverlay windows against JLC's general 20 mm for one opening.
DEFAULT_REQUIREMENTS = {
    "fpc_thickness": "2 layer, 0.2 mm FPC thickness (finished, without the stiffener), the bottom copper layer empty",
    "copper_weight": "1 oz (0.035 mm)",
    "pi_stiffener": "PI 0.225 mm on the bottom side at the contacts (the 6 mm zone from the tip)",
    "gold_finger_thickness": (
        "Yes, Gold Fingers Thickness 0.3 mm (the stiffened contact zone in total, from the contact surface to the outer "
        "surface of the stiffener)"
    ),
    "outline_tolerance": "+/-0.05 mm (special request; JLC's default is +/-0.1 mm)",
    "surface_finish": "ENIG",
    "finger_width": "ask JLC to hold the 0.3 mm contacts within +/-0.05 mm, or measure them on delivery",
    "trace_widths": (
        "the fan-out traces are 0.127 mm wide by default (routing.trace_width_mm, at least 0.1016 mm) "
        "and widen to 0.254 mm in the tail, which the stiffener edge flexes"
    ),
    "contact_zone": "the tail is about 0.285 mm thick at the contacts; measure it on delivery",
    "contact_start": "the contacts start 0.3 mm from the tip",
    "contact_window": "the gang coverlay window leaves 0.05 mm beyond the outer contacts",
    "coverlay_windows": (
        "check them on the upload: JLC advises one opening no longer than 20 mm, and the merged electrode-field window "
        "and the gang contact window are one opening each (each board's lines in ORDER_NOTES.txt give its windows and "
        "those longer)"
    ),
}
# The default 12 x 32 board's coverlay windows (each board's line of ORDER_NOTES.txt): a window per electrode (the 1.0 mm
# electrodes of the default fill 0.5 since the user's decision of 2026-11-06 leave 0.8 mm bridges; the 1.4 mm ones of
# before, 0.4 mm, so one merged electrode-field window of 64 x 23.6 mm) and the gang window of its contacts.
DEFAULT_WINDOW_LINES = {
    "rows": "Coverlay windows: 12 electrode windows up to 63.6 x 1.2 mm, contacts 5.9 x 4.4 mm; longer than JLC's general "
            "20 mm for one opening: 12 electrode windows (up to 63.6 mm).",
    "columns": "Coverlay windows: 32 electrode windows up to 1.2 x 23.6 mm, contacts 15.9 x 4.4 mm; longer than JLC's "
               "general 20 mm for one opening: 32 electrode windows (up to 23.6 mm).",
}


def _members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _flat(text: str) -> str:
    return " ".join(text.split())


def _issues(profile) -> dict[str, str]:
    return {issue["field"]: issue["code"] for issue in profile_module.profile_issues(profile)}


def _code_constants(path: Path) -> tuple[set, list]:
    """Float literals and string literals (docstrings aside) of a module."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        id(node.body[0].value) for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body
        and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)
    }
    constants = [node for node in ast.walk(tree) if isinstance(node, ast.Constant) and id(node) not in docstrings]
    numbers = {node.value for node in constants if isinstance(node.value, float)}
    texts = [node.value for node in constants if isinstance(node.value, str)]
    # f-string fragments are Constant nodes too (inside JoinedStr), so they are covered.
    return numbers, texts


class OrderBlockValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profile()

    def test_the_bundled_profile_records_the_approved_order(self) -> None:
        order, fabrication = self.profile["order"], self.profile["fabrication"]
        self.assertEqual(profile_module.profile_issues(self.profile), [])
        self.assertEqual((order["fpc_layers"], order["fpc_thickness_mm"], order["outline_tolerance_mm"], order["surface_finish"]), (2, 0.2, 0.05, "ENIG"))
        self.assertEqual(self.profile["stackup"]["stiffener_thickness_mm"], 0.225)
        # The boards' own 0.11 mm build (ordered as JLC's 2-layer 0.2 mm FPC, the bottom copper empty): 25 um PI core, 35 um (1 oz) copper, 25 um PI + 25 um adhesive coverlay.
        stackup = self.profile["stackup"]
        self.assertEqual(
            (stackup["core_polyimide_thickness_mm"], stackup["copper_thickness_mm"], stackup["coverlay_thickness_mm"],
             stackup["coverlay_adhesive_thickness_mm"]),
            (0.025, 0.035, 0.025, 0.025),
        )
        self.assertEqual((fabrication["single_sided_copper_thicknesses_mm"], fabrication["single_sided_copper_weights_oz"]), ([0.018, 0.035], [0.5, 1]))
        # JLC's recommendation for a 0.3 mm connector on a 0.11 mm FPC, which the profile follows.
        self.assertEqual(
            (fabrication["recommended_pi_stiffener_mm"], fabrication["recommended_pi_stiffener_fpc_thickness_mm"],
             fabrication["recommended_pi_stiffener_connector_thickness_mm"]),
            (self.profile["stackup"]["stiffener_thickness_mm"], 0.11, self.profile["connector"]["contact_zone_thickness_mm"]),
        )
        # The sources the order requirements cite: the JLC page and both connector drawings.
        # JLC's gold-finger stiffener ordering guide and its FPC design rules (fetched 2026-10-29), the JLC-accepted
        # reference design's field windows measured from its Gerbers.
        guide = " ".join(self.profile["sources"]["jlcpcb_gold_finger_stiffeners"]["quoted"])
        for fact in ("measured from the plated contact surface to the outer surface of the stiffener beneath it",
                     "enter the required total thickness in the \u201cGold Fingers Thickness\u201d field",
                     "we give the total thickness you specify the highest priority when selecting the stiffener thickness"):
            self.assertIn(fact, guide)
        rules = " ".join(self.profile["sources"]["jlcpcb_fpc_design_clearance"]["quoted"])
        self.assertIn("The solder-mask opening length should generally not exceed 20 mm", rules)
        self.assertEqual((self.profile["coverlay"]["coverlay_opening_general_max_length_mm"], order["reference_field_window_length_mm"]), (20.0, 63.373))
        self.assertIn("the 12-pin board's field window 23.368 x 63.373 mm", self.profile["sources"]["reference_design"])
        quoted = " ".join(self.profile["sources"]["jlcpcb_flex_capabilities"]["quoted"])
        for fact in ("+/-0.05 mm upon request", "1-layer 0.07 / 0.11 mm", "Surface finish: ENIG", "Trace width tolerance +/-20%",
                     "0.3 mm thick on a 0.11 mm FPC, a 0.225 mm stiffener", "inner PI thickness 25 um", "35 um (1 oz)",
                     "PI 25 um + adhesive 25 um on 1 oz copper", "35 um (1 oz) copper 4/4 mil", "gold finger area +/-0.03 mm"):
            self.assertIn(fact, quoted)
        readers = self.profile["sources"]["reader_connectors"]
        self.assertIn("contacts 0.30 +/-0.05 mm", readers["rows"])
        self.assertIn("0.30 +/-0.03 mm thick", readers["rows"])
        self.assertIn("FPC width 0.5*(N+1) +/-0.07", readers["columns"])
        self.assertIn("coverlay openings 0.051 mm beyond each contact", self.profile["sources"]["reference_design"])

    def test_an_order_jlc_cannot_build_or_the_connectors_cannot_take_is_refused(self) -> None:
        cases = (
            (("order", "fpc_thickness_mm", 0.1), "profile.order.fpc_thickness_mm", "E_PROFILE_FAB_LIMIT"),
            (("order", "outline_tolerance_mm", 0.1), "profile.order.outline_tolerance_mm", "E_PROFILE_INCONSISTENT"),
            (("order", "outline_tolerance_mm", 0.03), "profile.order.outline_tolerance_mm", "E_PROFILE_FAB_LIMIT"),
            (("order", "surface_finish", "HASL"), "profile.order.surface_finish", "E_PROFILE_FAB_LIMIT"),
            (("order", "surface_finish", " "), "profile.order.surface_finish", "E_PROFILE_MISSING"),
            (("order", "fpc_layers", 3), "profile.order.fpc_layers", "E_PROFILE_INCONSISTENT"),
            (("order", "fpc_layers", 1.0), "profile.order.fpc_layers", "E_PROFILE_MISSING"),
            (("order", "reference_contact_window_margin_mm", -0.051), "profile.order.reference_contact_window_margin_mm", "E_PROFILE_MISSING"),
            (("order", "reference_field_window_length_mm", 0.0), "profile.order.reference_field_window_length_mm", "E_PROFILE_MISSING"),
            (("coverlay", "coverlay_opening_general_max_length_mm", None), "profile.coverlay.coverlay_opening_general_max_length_mm", "E_PROFILE_MISSING"),
            (("fabrication", "outline_tolerance_on_request_mm", 0.2), "profile.order.outline_tolerance_mm", "E_PROFILE_FAB_LIMIT"),
            (("fabrication", "two_layer_fpc_thickness_options_mm", []), "profile.fabrication.two_layer_fpc_thickness_options_mm", "E_PROFILE_MISSING"),
            (("fabrication", "recommended_pi_stiffener_mm", 0.3), "profile.fabrication.recommended_pi_stiffener_mm", "E_PROFILE_INCONSISTENT"),
            (("fabrication", "trace_width_tolerance_fraction", 1.5), "profile.fabrication.trace_width_tolerance_fraction", "E_PROFILE_INCONSISTENT"),
            (("connector", "contact_zone_thickness_tolerance_mm", 0.3), "profile.connector.contact_zone_thickness_tolerance_mm", "E_PROFILE_INCONSISTENT"),
            (("connector", "contact_width_tolerance_mm", 0.3), "profile.connector.contact_width_tolerance_mm", "E_PROFILE_INCONSISTENT"),
            # The stack-up must be the ordered build, in JLC copper ...
            (("stackup", "core_polyimide_thickness_mm", 0.05), "profile.stackup", "E_PROFILE_INCONSISTENT"),
            (("stackup", "copper_thickness_mm", 0.018), "profile.stackup", "E_PROFILE_INCONSISTENT"),
            (("stackup", "copper_thickness_mm", 0.03), "profile.stackup.copper_thickness_mm", "E_PROFILE_FAB_LIMIT"),
            (("stackup", "coverlay_adhesive_thickness_mm", 0.0), "profile.stackup.coverlay_adhesive_thickness_mm", "E_PROFILE_MISSING"),
            (("fabrication", "single_sided_copper_weights_oz", [1]), "profile.fabrication.single_sided_copper_weights_oz", "E_PROFILE_MISSING"),
            (("fabrication", "gold_finger_thickness_tolerance_mm", None), "profile.fabrication.gold_finger_thickness_tolerance_mm", "E_PROFILE_MISSING"),
            # ... and give the contact zone the connectors take: 0.2 mm PI is a JLC option, but
            # 0.025 + 0.035 + 0.2 = 0.26 mm is thinner than 0.30 - 0.03 mm.
            (("stackup", "stiffener_thickness_mm", 0.2), "profile.stackup.stiffener_thickness_mm", "E_PROFILE_INCONSISTENT"),
            (("stackup", "stiffener_thickness_mm", 0.1), "profile.stackup.stiffener_thickness_mm", "E_PROFILE_INCONSISTENT"),
            (("connector", "contact_zone_thickness_mm", 0.33), "profile.stackup.stiffener_thickness_mm", "E_PROFILE_INCONSISTENT"),
        )
        for (section, key, value), field, code in cases:
            profile = copy.deepcopy(self.profile)
            profile[section][key] = value
            with self.subTest(key=f"{section}.{key}", value=value):
                self.assertEqual(_issues(profile).get(field), code)
                # The generic profile builds the straight Row channel (the diagonal Row bus takes the surface profile,
                # P5-diagonal-bus.md section 20; its order sections are the same).
                with mock.patch("engine.core.load_profile", return_value=profile):
                    result = generate_design({"routing": {"row_sides": "channel"}})
                self.assertFalse(result["ok"])
                self.assertIn(field, {issue["field"] for issue in result["validation"]["errors"]})
                with self.assertRaises(ExportError):
                    build_exports(result)

    def test_missing_order_section_or_cited_sources_are_reported(self) -> None:
        missing = copy.deepcopy(self.profile)
        del missing["order"]
        self.assertEqual(_issues(missing), {"profile.order": "E_PROFILE_MISSING"})
        for path in (("reference_design",), ("reader_connectors", "rows"), ("jlcpcb_flex_capabilities", "url"),
                     ("jlcpcb_gold_finger_stiffeners", "fetched"), ("jlcpcb_fpc_design_clearance", "url")):
            profile = copy.deepcopy(self.profile)
            parent = profile["sources"]
            for key in path[:-1]:
                parent = parent[key]
            del parent[path[-1]]
            with self.subTest(source=".".join(path)):
                self.assertEqual(_issues(profile), {"profile.sources." + ".".join(path): "E_PROFILE_MISSING"})
        # The notes name each reader connector by the text before " (" of its source.
        unnamed = copy.deepcopy(self.profile)
        unnamed["sources"]["reader_connectors"]["columns"] = "THD THD0515-32CL-SN: 0.5 mm pitch, bottom contact"
        self.assertEqual(_issues(unnamed), {"profile.sources.reader_connectors.columns": "E_PROFILE_MISSING"})


class OrderRequirementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profile()
        self.records = order_requirements(self.profile, default_design())

    def test_default_requirements_are_the_approved_ones(self) -> None:
        self.assertEqual({record["id"]: record["requirement"] for record in self.records}, DEFAULT_REQUIREMENTS)
        kinds = [(record["id"], record["kind"]) for record in self.records]
        self.assertEqual(
            [key for key, kind in kinds if kind == "order_option"],
            ["fpc_thickness", "copper_weight", "pi_stiffener", "gold_finger_thickness", "outline_tolerance", "surface_finish"],
        )
        self.assertEqual(
            [key for key, kind in kinds if kind == "review_note"],
            ["finger_width", "trace_widths", "contact_zone", "contact_start", "contact_window", "coverlay_windows"],
        )
        self.assertEqual([record["id"] for record in self.records if record["special_request"]], ["outline_tolerance"])
        reasons = {record["id"]: record["reason"] for record in self.records}
        self.assertIn("JLC recommends a 0.225 mm PI stiffener for a 0.3 mm thick connector on a 0.11 mm FPC.", reasons["pi_stiffener"])
        self.assertIn("0.3 +/-0.03 mm thick FPC at the contacts", reasons["pi_stiffener"])
        self.assertIn("The gold-finger thickness below takes priority when JLC chooses the stiffener under the gold fingers.", reasons["pi_stiffener"])
        self.assertIn("JLC gives the total gold-finger thickness the highest priority when it chooses the stiffener under the gold fingers",
                      reasons["gold_finger_thickness"])
        self.assertIn("may take another PI thickness there than the 0.225 mm above; it holds the gold-finger area to +/-0.03 mm.",
                      reasons["gold_finger_thickness"])
        self.assertIn("a longer opening can stretch and deform when the coverlay is laminated", reasons["coverlay_windows"])
        self.assertIn("reference design's electrode-field windows were up to 63.373 mm long.", reasons["coverlay_windows"])
        records = {record["id"]: record for record in self.records}
        self.assertEqual(
            records["gold_finger_thickness"]["values"],
            {"gold_fingers": True, "gold_finger_thickness_mm": 0.3, "connector_thickness_tolerance_mm": 0.03, "gold_finger_thickness_tolerance_mm": 0.03},
        )
        self.assertEqual(records["gold_finger_thickness"]["sources"][0], "jlcpcb_gold_finger_stiffeners")
        self.assertEqual(records["coverlay_windows"]["sources"], ["jlcpcb_fpc_design_clearance", "reference_design"])
        self.assertIn("THD THD0515-32CL-SN connector needs the tail width 0.5 x (N + 1) mm within +/-0.07 mm", reasons["outline_tolerance"])
        self.assertIn("JLC's laser-outline tolerance is +/-0.1 mm", reasons["outline_tolerance"])
        self.assertIn("+/-20% (0.24-0.36 mm for 0.3 mm contacts)", reasons["finger_width"])
        self.assertIn("TXGA FFC05001-16SBB124W5M drawing allows 0.3 +/-0.05 mm", reasons["finger_width"])
        # T-D9: JLC's 1 oz minimum and its tolerance applied to the default bundle trace.
        self.assertIn("minimum trace width and spacing for 1 oz copper is 4/4 mil (0.1016/0.1016 mm)", reasons["trace_widths"])
        self.assertIn("+/-20% lets a 0.127 mm trace come out at 0.1016 mm", reasons["trace_widths"])
        self.assertIn("no rule on necking or on the trace width near bends or stiffener edges", reasons["trace_widths"])
        self.assertIn("the 0.025 mm PI core and the 0.025 mm PI + 0.025 mm adhesive coverlay, the boards' own layers come to 0.11 mm; JLC builds them as the 0.2 mm 2-layer FPC", reasons["copper_weight"])
        self.assertIn("JLC's single-sided copper is 0.5 and 1 oz (0.018 and 0.035 mm)", reasons["copper_weight"])
        self.assertIn("0.025 mm PI core + 0.035 mm copper + the 0.225 mm PI stiffener where the coverlay is open, the stiffener's "
                      "adhesive not counted", reasons["contact_zone"])
        self.assertIn("take 0.3 +/-0.03 mm, JLC holds the gold-finger area to +/-0.03 mm and chooses the stiffener under the gold "
                      "fingers to the gold-finger thickness ordered.", reasons["contact_zone"])
        self.assertIn("closer than 0.2 mm to the board edge", reasons["contact_start"])
        self.assertIn("copper-to-edge minimum is 0.3 mm", reasons["contact_start"])
        self.assertIn("R0.3 mm tip corners", reasons["contact_window"])
        self.assertIn("reference design opened its coverlay 0.051 mm beyond each contact", reasons["contact_window"])
        # The window stops at the THD0515 drawing's R0.30 tip corners.
        self.assertIn("reader_connectors.columns", {record["id"]: record for record in self.records}["contact_window"]["sources"])
        cited = {key for record in self.records for key in record["sources"]}
        self.assertEqual(cited, {"jlcpcb_flex_capabilities", "flexitac_fabrication_guide", "jlcpcb_gold_finger_stiffeners", "jlcpcb_fpc_design_clearance",
                                 "reader_connectors.rows", "reader_connectors.columns", "reference_design"})

    def test_every_figure_follows_the_profile(self) -> None:
        # JLC's 0.07 mm build (0.5 oz copper, 12.5 um PI + 15 um adhesive coverlay)
        # with the 0.25 mm PI option: 0.025 + 0.018 + 0.25 = 0.293 mm at the contacts.
        profile = copy.deepcopy(self.profile)
        profile["stackup"].update(copper_thickness_mm=0.018, coverlay_thickness_mm=0.0125, coverlay_adhesive_thickness_mm=0.015)
        profile["stackup"]["stiffener_thickness_mm"] = 0.25
        profile["order"].update(fpc_layers=1, fpc_thickness_mm=0.07)
        profile["order"]["outline_tolerance_mm"] = 0.06
        profile["fabrication"]["trace_width_tolerance_fraction"] = 0.1
        profile["connector"]["tail_tip_corner_radius_mm"] = 0.25
        self.assertEqual(profile_module.profile_issues(profile), [])
        records = {record["id"]: record for record in order_requirements(profile, default_design())}
        self.assertEqual(records["fpc_thickness"]["requirement"], "1 layer, 0.07 mm FPC thickness (finished, without the stiffener)")
        self.assertEqual(records["copper_weight"]["requirement"], "0.5 oz (0.018 mm)")
        self.assertIn("With 0.018 mm copper, the 0.025 mm PI core and the 0.0125 mm PI + 0.015 mm adhesive coverlay make the 0.07 mm FPC",
                      records["copper_weight"]["reason"])
        self.assertTrue(records["pi_stiffener"]["requirement"].startswith("PI 0.25 mm"))
        # JLC's recommendation stays a quote; the note says what this profile does instead.
        self.assertIn("(this profile: 0.25 mm on 0.07 mm, for 0.3 mm)", records["pi_stiffener"]["reason"])
        self.assertEqual(records["contact_zone"]["requirement"], "the tail is about 0.293 mm thick at the contacts; measure it on delivery")
        held = copy.deepcopy(profile)
        held["fabrication"]["gold_finger_thickness_tolerance_mm"] = 0.005
        self.assertEqual(
            {record["id"]: record for record in order_requirements(held, default_design())}["contact_zone"]["requirement"],
            "the tail is about 0.293 mm thick at the contacts, within 0.3 +/-0.03 mm at JLC's tolerance",
        )
        self.assertTrue(records["outline_tolerance"]["requirement"].startswith("+/-0.06 mm (special request"))
        self.assertTrue(records["finger_width"]["requirement"].startswith("the 0.3 mm contacts are within +/-0.05 mm"))
        self.assertEqual(records["contact_window"]["values"]["contact_window_side_margin_mm"], 0.1)
        self.assertTrue(records["contact_window"]["reason"].startswith("The full 0.1 mm coverlay expansion."))
        # The gold-finger thickness and the window length follow the profile too.
        other = copy.deepcopy(self.profile)
        other["connector"]["contact_zone_thickness_mm"] = 0.31
        other["coverlay"]["coverlay_opening_general_max_length_mm"] = 25.0
        other["order"]["reference_field_window_length_mm"] = 31.242
        changed = {record["id"]: record for record in order_requirements(other, default_design())}
        self.assertTrue(changed["gold_finger_thickness"]["requirement"].startswith("Yes, Gold Fingers Thickness 0.31 mm"))
        self.assertIn("no longer than 25 mm", changed["coverlay_windows"]["requirement"])
        self.assertIn("up to 31.242 mm long", changed["coverlay_windows"]["reason"])
        # No figure or name of the requirements is a literal in the code that writes them.
        order, fabrication, connector = self.profile["order"], self.profile["fabrication"], self.profile["connector"]
        figures = {
            order["fpc_thickness_mm"], order["outline_tolerance_mm"], order["reference_contact_window_margin_mm"],
            self.profile["stackup"]["stiffener_thickness_mm"], fabrication["trace_width_tolerance_fraction"],
            self.profile["stackup"]["copper_thickness_mm"], self.profile["stackup"]["core_polyimide_thickness_mm"],
            fabrication["gold_finger_thickness_tolerance_mm"], DEFAULT_ZONE_MM,
            fabrication["outline_tolerance_on_request_mm"], fabrication["recommended_pi_stiffener_mm"],
            connector["contact_width_tolerance_mm"], connector["contact_zone_thickness_mm"], connector["contact_zone_thickness_tolerance_mm"],
            self.profile["coverlay"]["coverlay_opening_general_max_length_mm"], order["reference_field_window_length_mm"],
        }
        for path in (ROOT / "engine" / "profile.py", ROOT / "exporters" / "direct_gerber.py", ROOT / "app.py"):
            numbers, texts = _code_constants(path)
            with self.subTest(module=path.name):
                self.assertFalse(numbers & figures, sorted(numbers & figures))
                for name in ("ENIG", "THD0515", "FFC05001", "+/-0.", "0.11", "0.225", "0.035", "0.285", "20 mm", "63.373"):
                    self.assertFalse([text for text in texts if name in text], name)


class SurfacedEverywhereTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = generate_design()
        cls.exports = build_exports(cls.result)
        cls.records = order_requirements(cls.result["profile"], default_design())
        cls.names = artifact_filenames(cls.result)

    def _assert_notes(self, text: str, boards) -> None:
        flat = _flat(text)
        self.assertTrue(text.endswith("\n") and "\r" not in text)
        # A cited URL (the FlexiTac fabrication guide's) cannot wrap: it stands whole on its own line.
        self.assertTrue(all(len(line) <= 78 or line.strip().startswith("https://") for line in text.splitlines()), max(text.splitlines(), key=len))
        self.assertIn(f"Build: {self.result['manifest']['build_id']}", flat)
        for record in self.records:
            self.assertIn(_flat(f"{record['topic']}: {record['requirement']}."), flat)
            self.assertIn(_flat(f"Why: {record['reason']}"), flat)
        for board in boards:
            name = self.names[f"{board['physical_side']}_fpc_gerber_zip"]
            self.assertIn(f"Board {board['id']}:", flat)
            self.assertIn(f"Archive: {name}", flat)
            self.assertIn("Stiffener layer: Gerber_BottomStiffenerLayer_pib_0.225.GBSL (polyimide 0.225 mm, bottom side)", flat)
            self.assertIn(_flat(direct_gerber._coverlay_window_note(board, self.result["profile"])), flat)
            if board["role"] in DEFAULT_WINDOW_LINES:
                self.assertIn(_flat(DEFAULT_WINDOW_LINES[board["role"]]), flat)
        # The approved figures, as a person reading the file sees them.
        for board in boards:
            # The build's own trace widths, on the board's line, and what JLC's tolerance makes of them.
            self.assertIn("fan-out traces 0.127 mm at 0.127 mm spacing, 0.254 mm in the tail.", flat)
            self.assertIn(
                "Trace tolerance: at JLC's -20% the 0.127 mm fan-out traces may come out 0.1016 mm wide, "
                "not below JLC's 0.1016 mm minimum for 1 oz copper.", flat,
            )
        for phrase in ("2 layer, 0.2 mm FPC thickness", "Copper weight: 1 oz (0.035 mm).", "PI 0.225 mm",
                       "Outline tolerance: +/-0.05 mm (special request", "Surface finish: ENIG.",
                       "Contact-zone thickness: the tail is about 0.285 mm thick at the contacts",
                       "https://jlcpcb.com/capabilities/flex-pcb-capabilities (fetched 2026-10-12); trace rules rechecked 2026-10-15:",
                       "Gold fingers: Yes, Gold Fingers Thickness 0.3 mm",
                       "jlcpcb_gold_finger_stiffeners: https://jlcpcb.com/help/article/fpc-gold-finger-stiffeners-ordering-guide (fetched 2026-10-29)",
                       "jlcpcb_fpc_design_clearance: https://jlcpcb.com/help/article/fpc-design-clearance (fetched 2026-10-29)"):
            self.assertIn(phrase, flat)

    def test_every_board_zip_carries_its_order_notes_and_requirements(self) -> None:
        for board in self.result["boards"].values():
            key = f"{board['physical_side']}_fpc_gerber_zip"
            members = _members(self.exports[key])
            with self.subTest(board=board["id"]):
                self.assertIn(NOTES, members)
                text = members[NOTES].decode("utf-8")
                self._assert_notes(text, [board])
                other = next(b for b in self.result["boards"].values() if b is not board)
                self.assertNotIn(f"Board {other['id']}:", text)
                manifest = json.loads(members["manifest.json"])
                self.assertEqual(manifest["order_requirements"], self.records)
                self.assertEqual(manifest["order_notes"], NOTES)
                self.assertIn(NOTES, manifest["files"])

    def test_the_review_bundle_carries_the_notes_of_both_boards(self) -> None:
        bundle = _members(self.exports["project_review_bundle_zip"])
        text = bundle[NOTES].decode("utf-8")
        top, bottom = (next(b for b in self.result["boards"].values() if b["physical_side"] == side) for side in ("top", "bottom"))
        self._assert_notes(text, [top, bottom])
        self.assertLess(text.index(f"Board {top['id']}:"), text.index(f"Board {bottom['id']}:"))
        manifest = json.loads(bundle["manifest.json"])
        self.assertEqual(manifest["order_requirements"], self.records)
        self.assertIn(NOTES, manifest["bundle_files"])
        requirements = manifest["review_requirements"]
        for record in self.records:
            expected = (
                f"Set the JLCPCB order option '{record['topic']}' to {record['requirement']} for both boards ({NOTES})."
                if record["kind"] == "order_option" else f"Check '{record['topic']}' on both boards: {record['requirement']} ({NOTES})."
            )
            self.assertIn(expected, requirements)
        # The stiffener review item stays and names the 0.225 mm layer.
        self.assertIn("Verify each PI stiffener in Gerber_BottomStiffenerLayer_pib_0.225.GBSL is detected at 0.225 mm after JLCPCB upload.", requirements)
        self.assertIn("ORDER_NOTES.txt", manifest["export_verification"])

    def test_each_board_states_what_the_tolerance_makes_of_its_own_traces(self) -> None:
        # Reviewer finding (2026-10-15): the trace note quotes the 0.127 mm default
        # (it does not depend on the build); each board's lines give the build's
        # widths and, at JLC's -20%, whether its fan-out traces stay at JLC's minimum.
        result = generate_design({"routing": {"trace_width_mm": 0.1016, "trace_space_mm": 0.2}})
        self.assertTrue(result["ok"], result["validation"]["errors"])
        exports = build_exports(result)
        line = (
            "Trace tolerance: at JLC's -20% the 0.1016 mm fan-out traces may come out 0.08128 mm wide, below JLC's "
            "0.1016 mm minimum for 1 oz copper (traces at least 0.127 mm wide stay at or above it)."
        )
        for key, count in (("top_fpc_gerber_zip", 1), ("bottom_fpc_gerber_zip", 1), ("project_review_bundle_zip", 2)):
            members = _members(exports[key])
            flat = _flat(members[NOTES].decode("utf-8"))
            with self.subTest(artifact=key):
                self.assertEqual(flat.count("fan-out traces 0.1016 mm at 0.2 mm spacing, 0.254 mm in the tail."), count)
                self.assertEqual(flat.count(line), count)
                self.assertIn(_flat(f"Trace widths: {DEFAULT_REQUIREMENTS['trace_widths']}."), flat)
        # The widest bundle stays well above the minimum.
        wide = generate_design({"routing": {"trace_width_mm": 0.254, "trace_space_mm": 0.246}})
        flat = _flat(_members(build_exports(wide)["top_fpc_gerber_zip"])[NOTES].decode("utf-8"))
        self.assertIn("the 0.254 mm fan-out traces may come out 0.2032 mm wide, not below JLC's 0.1016 mm minimum", flat)

    def test_a_file_name_too_long_for_a_line_stays_whole_on_its_own_line(self) -> None:
        # Reviewer finding: the Archive lines of long builds ran past the 78-column wrap.
        result = generate_design({"project_name": "Very long tactile sensor project name for the left hand glove prototype"})
        self.assertTrue(result["ok"], result["validation"]["errors"])
        names = artifact_filenames(result)
        for key, data in build_exports(result).items():
            text = _members(data)[NOTES].decode("utf-8")
            with self.subTest(artifact=key):
                long_lines = [line for line in text.splitlines() if len(line) > 78 and not line.strip().startswith("https://")]
                self.assertTrue(long_lines)
                for line in long_lines:
                    self.assertEqual(line, "    " + line.strip())
                    self.assertIn(line.strip(), names.values())
                sides = ("top", "bottom") if key == "project_review_bundle_zip" else (key.split("_")[0],)
                for side in sides:
                    self.assertIn(f"Archive: {names[side + '_fpc_gerber_zip']}", _flat(text))

    def test_api_default_gives_the_browser_the_same_requirements(self) -> None:
        self.assertEqual(app.profile_for_ui()["order_requirements"], self.records)
        payload = json.loads(json.dumps(app.profile_for_ui(), ensure_ascii=True))
        self.assertEqual(payload["order_requirements"], self.records)

    def test_the_browser_renders_the_note_from_the_profile(self) -> None:
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("renderOrderRequirements(data.profile.order_requirements);", script)
        body = script[script.index("function renderOrderRequirements"):]
        body = body[: body.index("\n  }\n")]
        for name in ("orderOptions", "orderNotes", "entry.topic", "entry.requirement", "entry.reason", '"order_option"', '"review_note"'):
            self.assertIn(name, body)
        # The ordering notes, folded under "Ordering notes" (a details element since the clean interface of 2026-10-29).
        note = page[page.index('<details class="manufacturing-note"'):]
        note = note[: note.index("</section>")]
        for element in ('id="orderOptions"', 'id="orderNotes"'):
            self.assertIn(element, note)
        # No figure or text of a requirement is written into the note's markup or its renderer.
        for record in self.records:
            for text in (record["requirement"], record["reason"]):
                for figure in re.findall(r"\d+\.\d+", text) + ["ENIG", "THD0515", "FFC05001"]:
                    self.assertNotIn(figure, note + body, record["id"])


def _window_sizes(board) -> list[tuple[str, float, float]]:
    """The board's coverlay windows from its layout, independently of the exporter: kind, width and height in mm."""

    sizes = []
    for opening in board["layers"]["top_coverlay_openings"]:
        if opening.get("shape") == "polygon":
            xs, ys = [point[0] for point in opening["points"]], [point[1] for point in opening["points"]]
            sizes.append((opening["kind"], round(max(xs) - min(xs), 6), round(max(ys) - min(ys), 6)))
        else:
            sizes.append((opening["kind"], round(opening["width_mm"], 6), round(opening["height_mm"], 6)))
    return sizes


class CoverlayWindowNoteTests(unittest.TestCase):
    """Each board's line of ORDER_NOTES.txt gives its coverlay windows and those longer than JLC's general 20 mm for one
    opening (profile revision 2026-10-29), from the board's layout."""

    def _line(self, result, role):
        board = next(board for board in result["boards"].values() if board["role"] == role)
        notes = _members(build_exports(result)[f"{board['physical_side']}_fpc_gerber_zip"])[NOTES].decode("utf-8")
        # The line ends with its verdict: "... for one opening." or "... (N mm)."
        line = re.search(r"Coverlay windows: (.*?(?:opening|mm\)))\.", _flat(notes)).group(1)
        return board, line

    def test_the_boards_name_their_windows_and_the_long_merged_field_window(self) -> None:
        # The merged field window of 1.4 mm electrodes at 2 mm (0.4 mm bridges; the default until 2026-11-06).
        result = generate_design({"matrix": {"taxel_width_mm": 1.4, "taxel_height_mm": 1.4}})
        for role in ("rows", "columns"):
            board, line = self._line(result, role)
            sizes = dict((kind, (width, height)) for kind, width, height in _window_sizes(board))
            field, contacts = sizes["electrode_field_opening"], sizes["connector_contact_opening"]
            with self.subTest(role=role):
                self.assertTrue(line.startswith(f"electrode field {field[0]:g} x {field[1]:g} mm, contacts {contacts[0]:g} x {contacts[1]:g} mm;"), line)
                self.assertGreater(max(field), 20.0)
                self.assertIn(f"longer than JLC's general 20 mm for one opening: the electrode field window ({max(field):g} mm", line)
                self.assertNotIn("contacts window", line)

    def test_a_small_board_has_none_longer_and_wide_contacts_are_named(self) -> None:
        small = generate_design({"rows": 4, "columns": 4, "routing": {"row_sides": "channel"}})
        self.assertTrue(small["ok"], small["validation"]["errors"])
        for role in ("rows", "columns"):
            board, line = self._line(small, role)
            with self.subTest(role=role):
                self.assertTrue(all(max(width, height) <= 20.0 for _, width, height in _window_sizes(board)))
                self.assertTrue(line.endswith("none longer than JLC's general 20 mm for one opening"), line)
        # 44 Column contacts at 0.5 mm make a gang window longer than 20 mm.
        wide = generate_design({"rows": 2, "columns": 44})
        self.assertTrue(wide["ok"], wide["validation"]["errors"])
        board, line = self._line(wide, "columns")
        contacts = next((width, height) for kind, width, height in _window_sizes(board) if kind == "connector_contact_opening")
        self.assertGreater(max(contacts), 20.0)
        self.assertIn(f"the contacts window ({max(contacts):g} mm)", line)

    def test_per_electrode_windows_are_counted_with_the_largest(self) -> None:
        # At a 4 mm pitch the coverlay bridges hold, so each electrode has its own window: the Row board's three
        # are longer than 20 mm, the Column board's twelve are not.
        result = generate_design({"rows": 3, "columns": 12, "matrix": {"pitch_x_mm": 4.0, "pitch_y_mm": 4.0}, "routing": {"row_sides": "channel"}})
        self.assertTrue(result["ok"], result["validation"]["errors"])
        for role, count, longer in (("rows", 3, True), ("columns", 12, False)):
            board, line = self._line(result, role)
            windows = [(width, height) for kind, width, height in _window_sizes(board) if kind == "sensor_electrode_opening"]
            width, height = max(windows, key=lambda box: (max(box), box))
            with self.subTest(role=role):
                self.assertEqual(len(windows), count)
                self.assertIn(f"{count} electrode windows up to {width:g} x {height:g} mm", line)
                self.assertEqual(max(width, height) > 20.0, longer)
                if longer:
                    self.assertIn(f"longer than JLC's general 20 mm for one opening: {count} electrode windows (up to {max(width, height):g} mm", line)
                else:
                    self.assertTrue(line.endswith("none longer than JLC's general 20 mm for one opening"), line)


class OrderNotesSelfCheckTests(unittest.TestCase):
    """The exporter's read-back of ORDER_NOTES.txt (D17 for the new member)."""

    @classmethod
    def setUpClass(cls) -> None:
        # The merged field window of 1.4 mm electrodes (the default until 2026-11-06), whose line the edits change.
        cls.result = generate_design({"rows": 3, "columns": 17, "row_electrode_width_mm": 1.4, "column_electrode_width_mm": 1.4,
                                      "connector": {"row_pins": 5}, "connector_side": "left"})
        assert cls.result["ok"], cls.result["validation"]["errors"]

    def test_notes_that_drop_or_change_an_entry_are_refused(self) -> None:
        original = direct_gerber._order_notes
        edits = (
            ("0.2 mm FPC thickness", "0.12 mm FPC thickness"),
            ("not below JLC's", "below JLC's"),
            ("Surface finish: ENIG.", "Surface finish: HASL."),
            ("Gerber_BottomStiffenerLayer_pib_0.225.GBSL", "Gerber_BottomStiffenerLayer_pib_0.2.GBSL"),
            ("reader_connectors.columns:", "reader_connectors:"),
            ("Gold Fingers Thickness 0.3 mm", "Gold Fingers Thickness 0.35 mm"),
            ("Coverlay windows: electrode field", "Coverlay windows: field"),
        )
        for old, new in edits:
            def edited(build, boards, old=old, new=new):
                return original(build, boards).replace(old.encode(), new.encode(), 1)

            with self.subTest(edit=old), mock.patch.object(direct_gerber, "_order_notes", edited):
                with self.assertRaisesRegex(ExportError, "ORDER_NOTES.txt does not state"):
                    build_exports(self.result)
        with mock.patch.object(direct_gerber, "_order_notes", lambda build, boards: original(build, boards).replace(b"\n", b"\r\n")):
            with self.assertRaisesRegex(ExportError, "ORDER_NOTES.txt is not plain text"):
                build_exports(self.result)
        # The bundle's notes (both boards) are read back as well.
        def bundle_without_the_bottom_board(build, boards):
            text = original(build, boards)
            return text.replace(f"Board {boards[1][0]['id']}:".encode(), b"Board removed:") if len(boards) == 2 else text

        with mock.patch.object(direct_gerber, "_order_notes", bundle_without_the_bottom_board):
            with self.assertRaisesRegex(ExportError, "Read-back of the review bundle failed: ORDER_NOTES.txt does not state"):
                build_exports(self.result)

    def test_stated_contact_figures_must_hold_for_the_boards(self) -> None:
        resolve = direct_gerber.order_requirements
        for key, name, value in (
            ("contact_window", "contact_window_side_margin_mm", 0.1),
            ("contact_start", "contact_start_from_tip_mm", 0.2),
            ("finger_width", "contact_width_mm", 0.25),
            ("pi_stiffener", "thickness_mm", 0.2),
            ("pi_stiffener", "zone_length_mm", 5.0),
            ("trace_widths", "finger_trace_width_mm", 0.3),
        ):
            def stated(profile, default, key=key, name=name, value=value):
                records = resolve(profile, default)
                next(record for record in records if record["id"] == key)["values"][name] = value
                return records

            with self.subTest(claim=name), mock.patch.object(direct_gerber, "order_requirements", stated):
                with self.assertRaisesRegex(ExportError, f"ORDER_NOTES.txt states {key} {name}"):
                    build_exports(self.result)

    def test_the_stated_stiffener_must_be_the_boards_connector_zone_stiffener(self) -> None:
        records = order_requirements(self.result["profile"], default_design())
        for key, board in self.result["boards"].items():
            direct_gerber._check_order_claims(board, records)
            side = board["tail"]["side"]
            axis = 0 if side in ("left", "right") else 1
            away = 0.1 if side in ("bottom", "left") else -0.1  # away from the tip, along the tail
            shifted = copy.deepcopy(board)
            (stiffener,) = [item for item in shifted["layers"]["bottom_stiffener"] if item["zone"] == "connector"]
            stiffener["points"] = [[point[0] + (away if axis == 0 else 0.0), point[1] + (away if axis == 1 else 0.0)] for point in stiffener["points"]]
            with self.subTest(board=key, edit="shifted"), self.assertRaisesRegex(ValueError, "states the stiffener zone from the tip"):
                direct_gerber._check_order_claims(shifted, records)
            other = copy.deepcopy(board)
            other["layers"]["bottom_stiffener"][0]["material"] = "fr4"
            with self.subTest(board=key, edit="material"), self.assertRaisesRegex(ValueError, "states a bottom polyimide stiffener"):
                direct_gerber._check_order_claims(other, records)
            none = copy.deepcopy(board)
            none["layers"]["bottom_stiffener"][0]["zone"] = "fanout"
            with self.subTest(board=key, edit="zone"), self.assertRaisesRegex(ValueError, "one connector-zone stiffener"):
                direct_gerber._check_order_claims(none, records)

    def test_a_board_manifest_without_the_requirements_is_refused(self) -> None:
        original = direct_gerber._board_manifest

        def without(*args):
            manifest = original(*args)
            manifest["order_requirements"] = manifest["order_requirements"][:-1]
            return manifest

        with mock.patch.object(direct_gerber, "_board_manifest", without):
            with self.assertRaisesRegex(ExportError, "does not list the profile's order requirements"):
                build_exports(self.result)


if __name__ == "__main__":
    unittest.main()
