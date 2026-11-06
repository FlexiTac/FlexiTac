"""The diagonal Row bus in the rectangular generator, a subset of CAD mode (claude/specs/masked-field/P5-diagonal-bus.md
sections 18-20).

The generic template (``generic_matrix_v1``, the rectangular mode) builds the diagonal Row bus with ``both`` by
default.  Since section 20 (``diagonal-bus/8``) a bus design on it is built with CAD mode's rule set, the surface
profile (``engine.core.rules_template``), by the one construction, so it builds exactly the boards the same design
builds on the surface template; ``routing.row_sides`` ``channel`` keeps the straight Row channel on the generic profile
byte for byte (tests/test_generic_identity_guard.py).

These tests build through ``generate_design`` and check:

- the equivalence: on a named generic corpus (the default design, the user's 13 x 32, 16 x 16, 32 x 32, 12 x 32 with
  32- and 64-pin connectors, every tail side, the Row FPC at the bottom, scan order reverse; ``both``, ``left`` and
  ``right``) and a seeded random generic corpus, the generic build equals the surface-template build of the same design:
  its boards byte for byte (outlines, layers, tails, constructions, verification and previews), its validation issues,
  its profile (the surface one) and its manifest but for the identity (the build id and hashes and the template
  version);
- every bus build clean by the predicates of tests/test_diagonal_bus.py (``_check_clean``: every DRC record, the stack
  registration, at most two bends per Row and per Column trace below the field, the stacked tails, both centred on the
  field (the Row tail since diagonal-bus/10, the plan's section 27), one outline down to the tails' roots, the regular
  outlines, the relative narrow tip; ``_straight_problems``: the straight sides), the Column V at 85 degrees at most (80
  on the named corpus) and the Row fans at 60-85 outside the entry-angle guard;
- the rule set: the 0.5 mm field margin, up to 64 columns, tails from 7.5 mm (the default bottom tail 12 mm with the
  bus since the plan's section 27.7, the top tail's length, 7.5 mm before; 7.0 with the straight channel); the straight
  channel's own (32 columns, 7.0 mm tails, the 0.75 mm margin, two Column lanes round a slot, the 60-degree cap);
- the default's figures, the folded Row pin order in pinout.csv and ORDER_NOTES.txt of the exports;
- determinism: a pinned digest of the named corpus, the same on Python 3.9.6 and 3.12 and with any hash seed.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import random
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

from engine import REQUEST_WARNING_CODES, check_design, generate_design, load_profile, rules_template, validate_design
from engine import diagonal
from engine.core import _canonical_json
from exporters import build_exports

try:
    import test_diagonal_bus as T
    import defaults_of_before
except ImportError:  # run as tests.test_generic_bus
    from tests import test_diagonal_bus as T
    from tests import defaults_of_before


def setUpModule() -> None:
    # The default electrodes of before (1.4 mm at 2 mm, fill 0.7): this module's pinned numbers were measured with them
    # (tests/defaults_of_before.py; the user's decision of 2026-11-06 made the default fill 0.5).
    defaults_of_before.start()


ROOT = Path(__file__).resolve().parents[1]
GENERIC = "generic_matrix_v1"
SURFACE = "surface_matrix_v1"
STANDARD, CAD = load_profile(GENERIC), load_profile(SURFACE)
SIDES = ("both", "left", "right")
# The named corpus: the default design and the rectangular generator's choices (request overrides of the default).
NAMED = {
    "default": {},
    "13x32": {"matrix": {"rows": 13, "columns": 32}},
    "16x16": {"matrix": {"rows": 16, "columns": 16}},
    "32x32": {"matrix": {"rows": 32, "columns": 32}},
    "12x32 pins 32/64": {"connector": {"row_pins": 32, "column_pins": 64}},
    "12x32 pins 64/64": {"connector": {"row_pins": 64, "column_pins": 64}},
    "tails top": {"tail": {"row_side": "top", "column_side": "top"}},
    "tails left": {"tail": {"row_side": "left", "column_side": "left"}},
    "tails right": {"tail": {"row_side": "right", "column_side": "right"}},
    "Row FPC bottom": {"role_mapping": {"top": "columns", "bottom": "rows"}},
    "scan reverse": {"channel_order": {"rows": "descending", "columns": "descending"}},
    "32x32 pins 64/64, Row FPC bottom, 20 mm tails": {"matrix": {"rows": 32, "columns": 32}, "connector": {"row_pins": 64, "column_pins": 64},
                                                     "role_mapping": {"top": "columns", "bottom": "rows"},
                                                     "tail": {"top_length_mm": 20.0, "bottom_length_mm": 20.0}},
}
# The default design (both): the Column V at 80 degrees (the cap, 79.999381: the whole-degree cap that makes it lowest,
# within the grid's bends), so the Row fans keep 85; its tip the field's width (64.9 mm, the 0.5 mm margin; the straight
# sides 0.001 mm); both boards one outline down to the tails' roots, 5.866 mm below the field (the Column V's
# root lowered below the union's fillets into the tails), the Row board the Column board's width.  diagonal-bus/7 on the
# standard profile: fans 85, Row 67.941387 x 41.142779 mm, Column 67.889607 x 52.989032 mm (two lanes round a slot).
DEFAULT_BUS = {"fans": [85.0, 85.0], "tip_width_mm": 64.900857, "widest_mm": 67.919595, "row_outline_mm": (67.919595, 41.765841),
               "column_outline_mm": (67.919595, 41.765841), "column_entry_deg": 79.999381, "shared_mm": 5.865841}
# The boards of the named corpus with both, left and right, hashed (Python 3.9.6 and 3.12 alike).  Re-pinned by
# P5-diagonal-bus.md section 23 (the surface profile's tails to 200 mm): the build ids change with the profile's digest,
# the boards not (before: 76b286c0...).  Rewritten by section 24 (diagonal-bus/9): the build ids change with the
# construction's version, the boards of the named generic corpus not (before: 8305ecb6...).  Rewritten by section 27
# (diagonal-bus/10, the Row tail centred on the field, the user's request "some tails are not within the sensor's
# width"): the build ids, and the boards whose Row tail moves (one-sided ones under the field, the Column V capped there
# too; with both by up to 0.05 mm; the reader tails' rows at the centred tail's canonical left) (before: 4bfdcddc...).
# Re-pinned by section 27.7 (the rectangular mode's default tails 12 / 12 mm): the six requests hashed leave the bottom
# tail to the default, so each builds a 12 mm bottom tail (the Row FPC's with it at the bottom) (before: c48e2688...).
# Rewritten by section 27.8 (diagonal-bus/11, one side's convex flank: the multi-gripper video's notch below the field's
# outline corner on the side without the bus bridged): the build ids, and the one-sided boards' outlines there (each
# 0.234 mm2 larger; the copper, the tails and the roots the same) (before: 9922e93e...).  Re-pinned by the profile
# revision 2026-10-29 (the gold-finger thickness order option and the coverlay-window notes): the build ids change with
# the profiles' digests, the boards not (before: 4d4bf0e4...).  Re-pinned by the profile revision 2026-11-06 (the order:
# JLC's 2-layer 0.2 mm FPC, the bottom copper empty): the build ids change with the profiles' digests, the boards not
# (before: 4ea89555...).
DIGEST = "6b1f66e0a4b50f841c84a2fcf42f914782f8f43517f747664ec7c1047d552ba4"
# The manifest's identity: the build id and its hashes, and the surface template's version.
IDENTITY = {"build_id", "build_sha256", "design_sha256", "template"}


def _request(overrides: dict, sides: str | None) -> dict:
    request = copy.deepcopy(overrides)
    if sides is not None:
        request.setdefault("routing", {})["row_sides"] = sides
    return request


def _on_the_surface(result: dict) -> dict:
    """The surface-template build of a generic result's design (the same design, ``template_id`` the surface one)."""

    design = copy.deepcopy(result["design"])
    design["template_id"] = SURFACE
    return generate_design(design)


def _equivalent(test: unittest.TestCase, result: dict) -> None:
    """The generic build equals the surface-template build of the same design but for the identity."""

    surface = _on_the_surface(result)
    test.assertEqual(result["design"]["template_id"], GENERIC)
    test.assertEqual(result["boards"], surface["boards"])
    test.assertEqual(result["profile"], surface["profile"])
    test.assertEqual(result["profile"], CAD)
    for kind in ("errors", "warnings"):
        # The issues of the design (the request's own, a defaulted schema version, aside).
        test.assertEqual([issue for issue in result["validation"][kind] if issue["code"] not in REQUEST_WARNING_CODES], surface["validation"][kind])
    differ = {key for key in set(result["manifest"]) | set(surface["manifest"]) if result["manifest"].get(key) != surface["manifest"].get(key)}
    test.assertLessEqual(differ, IDENTITY)
    test.assertIn("template", differ)
    test.assertNotEqual(result["manifest"]["build_id"], surface["manifest"]["build_id"])


def _check(test: unittest.TestCase, result: dict, straight: bool = True) -> None:
    """``_check_clean``, the Column V (one lane straight into its contacts, no slot, at most the rule set's 85 degrees),
    the fans (60-85 degrees, outside the entry-angle guard) and, with ``straight``, the straight sides against the build
    without them."""

    T._check_clean(test, result)
    column = result["boards"]["column"]
    test.assertEqual(column["tail"]["fanout_lane_count"], 1)
    test.assertIsNone(column["construction"]["slot_bounds"])
    entry = column["construction"]["entry_taper_angle_deg"]
    test.assertLessEqual(entry, CAD["fanout"]["maximum_taper_angle_deg"] + 1e-6)
    bus = result["boards"]["row"]["construction"]["row_bus"]
    test.assertTrue(bus["tip_is_narrowest_relative"])
    test.assertEqual(bus["flat_lane_rows"], [])
    for fan in bus["fans"]:
        test.assertTrue(60.0 - 1e-9 <= fan["angle_deg"] <= 85.0 + 1e-9, fan)
        test.assertGreater(abs(fan["angle_deg"] - entry), diagonal.ENTRY_ANGLE_GUARD_DEG)
    if straight:
        # The straight sides on the build without the convex sides (section 24; _check_clean holds those).
        test.assertEqual(T._straight_problems(T._unconvex(result["design"]), T._unstraight(result["design"])), [])


def _random_corpus(seed: int, count: int) -> list:
    """Seeded valid generic designs: 2-32 rows, 2-40 columns, pitch 1-4 mm, every tail side, both role mappings, reader
    tails, trace 4-8 mil, tails of 7.5 mm or more; both (half) or one side."""

    rng = random.Random(seed)
    answer = []
    while len(answer) < count:
        rows, columns = rng.randint(2, 32), rng.choice((rng.randint(2, 32), rng.randint(2, 40)))
        pitch = rng.choice((1.0, 1.25, 1.5, 2.0, 2.0, 2.5, 3.0, 4.0))
        fill = rng.choice((0.5, 0.6, 0.7, 0.8))
        side = rng.choice(("bottom", "top", "left", "right"))
        trace = rng.choice((0.1016, 0.127, 0.127, 0.2))
        request = {
            "matrix": {"rows": rows, "columns": columns, "pitch_x_mm": pitch, "pitch_y_mm": pitch,
                       "taxel_width_mm": round(pitch * fill, 4), "taxel_height_mm": round(pitch * fill, 4)},
            "tail": {"row_side": side, "column_side": side, "top_length_mm": rng.choice((7.5, 12.0, 20.0)),
                     "bottom_length_mm": rng.choice((7.5, 12.0))},
            "role_mapping": rng.choice(({"top": "rows", "bottom": "columns"}, {"top": "columns", "bottom": "rows"})),
            "channel_order": rng.choice(({"rows": "ascending", "columns": "ascending"}, {"rows": "descending", "columns": "descending"})),
            "connector": {"row_pins": rng.choice((None, None, max(rows, 32), 64)), "column_pins": rng.choice((None, max(columns, 32), 64))},
            "routing": {"trace_width_mm": trace, "trace_space_mm": trace, "row_sides": rng.choice(("both", "both", "left", "right"))},
        }
        if check_design(request)["ok"]:
            answer.append(request)
    return answer


def _digest_builds() -> str:
    boards = []
    for name in ("default", "13x32", "16x16", "12x32 pins 32/64", "tails left", "Row FPC bottom"):
        for sides in SIDES:
            result = generate_design(_request(NAMED[name], sides))
            boards.append([result["manifest"]["build_id"], result["boards"]])
    return hashlib.sha256(_canonical_json(boards).encode("utf-8")).hexdigest()


class NamedGenericCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = {(name, sides): generate_design(_request(overrides, sides)) for name, overrides in NAMED.items() for sides in SIDES}

    def test_every_bus_build_is_clean(self) -> None:
        for key, result in sorted(self.results.items()):
            with self.subTest(case=key):
                self.assertEqual(result["design"]["template_id"], GENERIC)
                self.assertEqual(result["design"]["routing"]["row_sides"], key[1])
                _check(self, result)

    def test_the_generic_bus_is_cad_modes(self) -> None:
        # The same design on the surface template (CAD mode) builds the same boards: one rule set, one construction.
        for key, result in sorted(self.results.items()):
            with self.subTest(case=key):
                self.assertEqual(rules_template(result["design"]), SURFACE)
                _equivalent(self, result)

    def test_the_default_is_the_bus_with_both(self) -> None:
        # No routing.row_sides in the request: both, recorded as a default; the same build as asking for it.
        for name, overrides in NAMED.items():
            with self.subTest(case=name):
                result = generate_design(copy.deepcopy(overrides))
                self.assertEqual(result["design"]["routing"]["row_sides"], "both")
                self.assertIn("routing.row_sides", result["validation"]["normalization"]["defaults_applied"])
                self.assertEqual(result["manifest"]["build_id"], self.results[(name, "both")]["manifest"]["build_id"])
                self.assertEqual(result["manifest"]["row_bus"], diagonal.ROW_BUS_VERSION)
        default = self.results[("default", "both")]
        row, column = default["boards"]["row"], default["boards"]["column"]
        bus = row["construction"]["row_bus"]
        measured = {"fans": [fan["angle_deg"] for fan in bus["fans"]], "tip_width_mm": bus["tip_width_mm"], "widest_mm": bus["widest_mm"],
                    "row_outline_mm": (row["metrics"]["outline_width_mm"], row["metrics"]["outline_height_mm"]),
                    "column_outline_mm": (column["metrics"]["outline_width_mm"], column["metrics"]["outline_height_mm"]),
                    "column_entry_deg": column["construction"]["entry_taper_angle_deg"], "shared_mm": bus["shared_outline_below_field_mm"]}
        self.assertEqual(measured, DEFAULT_BUS)
        self.assertEqual((bus["sides"], bus["split"], bus["tail_position"], bus["tails"]), ("both", "alternate", "centred", "stacked"))
        self.assertEqual(row["tail"]["row_contact_order"], [f"ROW_{k:02d}" for k in (1, 3, 5, 7, 9, 11, 12, 10, 8, 6, 4, 2)])
        # Both tails 12 mm since the user's decision of 2026-10-27 (section 27.7): the stacked tails end together.
        self.assertEqual((default["design"]["tail"]["bottom_length_mm"], column["tail"]["length_mm"], row["tail"]["length_mm"]), (12.0, 12.0, 12.0))

    def test_the_column_v_keeps_the_fans_at_85_degrees(self) -> None:
        # The Column V runs at a whole-degree cap of at most 80 degrees (COLUMN_V_CAP_DEG), so the Row fans keep the rule
        # set's 85 degrees outside the 5-degree entry-angle guard: every named funnel takes 85, its tails' roots 1.9-5.8 mm
        # higher than with the V at the profile's own caps (82 degrees, the fans then 76).  Since diagonal-bus/10 (the Row
        # tail centred on the field, the plan's section 27) one side's fans run inward under the field too and take 85,
        # the tails 1.3-6.9 mm higher than with the V at 82 (under the band one fan at 60 degrees gained nothing and the V
        # at 82 was taken; tests/test_diagonal_bus.py ColumnVCapTests).
        self.assertEqual(diagonal.COLUMN_V_CAP_DEG, 80.0)
        self.assertEqual((CAD["fanout"]["minimum_taper_angle_deg"], CAD["fanout"]["maximum_taper_angle_deg"]), (60.0, 85.0))
        fans = [fan["angle_deg"] for result in self.results.values() for fan in result["boards"]["row"]["construction"]["row_bus"]["fans"]]
        self.assertEqual(set(fans), {85.0})
        for key, result in self.results.items():
            with self.subTest(case=key):
                entry = result["boards"]["column"]["construction"]["entry_taper_angle_deg"]
                self.assertAlmostEqual(entry, 80.0, delta=0.01)
                for fan in result["boards"]["row"]["construction"]["row_bus"]["fans"]:
                    self.assertGreater(abs(fan["angle_deg"] - entry), diagonal.ENTRY_ANGLE_GUARD_DEG)

    def test_the_rule_set_is_cad_modes(self) -> None:
        # The bus: the surface profile's rules (the 0.5 mm field margin, up to 64 columns, tails from 7.5 mm; the default
        # bottom tail 12 mm since section 27.7, 7.5 before); the straight channel: the generic profile's (32 columns, 7.0 mm
        # tails, the 0.75 mm margin).
        self.assertEqual((CAD["routing"]["active_edge_clearance_mm"], CAD["limits"]["maximum_columns"], CAD["tail"]["minimum_length_mm"]), (0.5, 64, 7.5))
        self.assertEqual((STANDARD["routing"]["active_edge_clearance_mm"], STANDARD["limits"]["maximum_columns"], STANDARD["tail"]["minimum_length_mm"]), (0.75, 32, 7.0))
        for key, result in self.results.items():
            with self.subTest(case=key):
                for board in result["boards"].values():
                    self.assertGreaterEqual(board["verification"]["checks"]["active_field_margin"]["measured_mm"], 0.5 - 1e-6)
        wide = generate_design({"matrix": {"rows": 8, "columns": 64, "pitch_x_mm": 1.0, "taxel_width_mm": 0.6}})
        self.assertTrue(wide["ok"], wide["validation"]["errors"][:2])
        _check(self, wide, straight=False)
        self.assertEqual(wide["manifest"]["profile"]["id"], CAD["id"])

        def codes(request):
            return [(issue["code"], issue["field"]) for issue in check_design(request)["validation"]["errors"]]

        self.assertIn(("E_COLUMNS_RANGE", "matrix.columns"), codes({"matrix": {"columns": 33}, "routing": {"row_sides": "channel"}}))
        self.assertEqual(codes({"tail": {"bottom_length_mm": 7.4}}), [("E_TAIL_LENGTH", "tail.bottom_length_mm")])
        self.assertEqual(codes({"tail": {"bottom_length_mm": 7.0}, "routing": {"row_sides": "channel"}}), [])
        # The default bottom tail follows the Row traces; given, it is kept (and checked against their rule set).
        self.assertEqual(check_design({})["design"]["tail"]["bottom_length_mm"], 12.0)
        self.assertEqual(check_design({"routing": {"row_sides": "channel"}})["design"]["tail"]["bottom_length_mm"], 7.0)
        self.assertEqual(check_design({"tail": {"row_side": "bottom", "column_side": "top"}})["design"]["tail"]["bottom_length_mm"], 7.0)
        self.assertEqual(check_design({"routing": {"row_sides": "channel"}, "tail": {"bottom_length_mm": 9.0}})["design"]["tail"]["bottom_length_mm"], 9.0)
        # The bus is built with the surface profile on either template; the generic profile given for it is refused.
        design = check_design({})["design"]
        self.assertEqual(validate_design(design, CAD)["errors"], [])
        self.assertEqual([issue["code"] for issue in validate_design(design, STANDARD)["errors"]], ["E_TEMPLATE_UNSUPPORTED"])
        channel = check_design({"routing": {"row_sides": "channel"}})["design"]
        self.assertEqual(rules_template(channel), GENERIC)
        self.assertEqual([issue["code"] for issue in validate_design(channel, CAD)["errors"]], ["E_TEMPLATE_UNSUPPORTED"])

    def test_the_straight_channel_stays_selectable(self) -> None:
        for name, overrides in NAMED.items():
            with self.subTest(case=name):
                result = generate_design(_request(overrides, "channel"))
                self.assertTrue(result["ok"], result["validation"]["errors"][:2])
                self.assertEqual(result["design"]["routing"]["row_sides"], "channel")
                self.assertEqual(result["profile"], STANDARD)
                self.assertNotIn("row_bus", result["manifest"])
                self.assertNotIn("row_bus", result["boards"]["row"]["construction"])
                self.assertNotIn("taxel_mask", result["boards"]["row"]["grid_registration"])
        channel = generate_design(_request(NAMED["default"], "channel"))["boards"]
        self.assertAlmostEqual(channel["row"]["construction"]["merger_taper_angle_deg"], 60.0, delta=0.01)
        self.assertAlmostEqual(channel["column"]["construction"]["merger_taper_angle_deg"], 60.0, delta=0.01)
        self.assertEqual(channel["column"]["tail"]["fanout_lane_count"], 2)
        self.assertIsNotNone(channel["column"]["construction"]["slot_bounds"])

    def test_the_exports_list_the_folded_row_pins(self) -> None:
        for sides, order in (("both", [1, 3, 5, 7, 9, 11, 12, 10, 8, 6, 4, 2]), ("right", list(range(1, 13))), ("left", list(range(12, 0, -1)))):
            with self.subTest(sides=sides):
                result = self.results[("default", sides)]
                self.assertEqual(result["boards"]["row"]["tail"]["row_contact_order"], [f"ROW_{k:02d}" for k in order])
                exports = build_exports(result)
                with zipfile.ZipFile(io.BytesIO(exports["project_review_bundle_zip"])) as archive:
                    pinout = archive.read("pinout.csv").decode("utf-8")
                    manifest = json.loads(archive.read("manifest.json"))
                    notes = archive.read("ORDER_NOTES.txt").decode("utf-8")
                rows = [line.split(",") for line in pinout.splitlines()[1:] if ",rows," in line and ",ROW_" in line]
                self.assertEqual([item[1] for item in sorted(rows, key=lambda item: int(item[0]))], [f"ROW_{k:02d}" for k in order])
                self.assertEqual(manifest["diagonal_row_bus"]["row_contact_order"], [f"ROW_{k:02d}" for k in order])
                self.assertIn("Row pin order (diagonal Row bus, " + ("folded" if sides == "both" else "one side"), notes)
                self.assertIn(f"Profile: {CAD['id']}", notes)


class RandomGenericCorpusTests(unittest.TestCase):
    def test_a_seeded_random_generic_corpus_builds_clean_and_as_in_cad_mode(self) -> None:
        corpus = _random_corpus(18, 40)
        self.assertEqual({request["routing"]["row_sides"] for request in corpus}, set(SIDES))
        self.assertEqual({request["tail"]["row_side"] for request in corpus}, {"bottom", "top", "left", "right"})
        self.assertEqual({request["role_mapping"]["top"] for request in corpus}, {"rows", "columns"})
        self.assertTrue(any(request["matrix"]["columns"] > 32 for request in corpus))
        for index, request in enumerate(corpus):
            with self.subTest(index=index, request=request):
                result = generate_design(request)
                _check(self, result, straight=index % 4 == 0)
                _equivalent(self, result)


class GenericDeterminismTests(unittest.TestCase):
    def test_the_pinned_digest(self) -> None:
        # The same on Python 3.9.6 and 3.12 (both ran this test), and with any hash seed (below).
        self.assertEqual(_digest_builds(), DIGEST)

    def test_the_digest_with_other_hash_seeds(self) -> None:
        code = ("import sys; sys.path.insert(0, 'tests'); import defaults_of_before; defaults_of_before.start(cleanup=False); "
                "import test_generic_bus as t; print(t._digest_builds())")
        for seed in ("0", "123"):
            with self.subTest(seed=seed):
                environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
                output = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
                self.assertEqual(output.stdout.strip(), DIGEST)


if __name__ == "__main__":
    unittest.main()
