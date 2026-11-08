"""The surface template ``surface_matrix_v1`` (CAD mode, decision C-D10).

The template is the generic design with its own locked profile,
``profiles/jlc_fpc_surface_v1.json``, whose optional geometry policies give
the smallest margins the research of 2026-10-20 proved DRC-clean ("V4"): a
0.5 mm field margin, a tight Row channel and expansion, a bus angle chosen
per transition among whole-degree caps of 60-85 degrees, a direct one-lane
Column fan-out for up to 64 columns and 7.5 mm minimum tails.  These tests
check the profile and its policies, the template dispatch and the input
limits, the build identity (generic ids untouched: see
``test_generic_identity_guard``), a DRC-clean sweep of over 300 seeded
designs, the footprint against the generic template, the exports and their
read-back, and pinned surface values.  A deliberate change of the surface
geometry bumps ``engine.core.TEMPLATE_VERSIONS`` and refreshes the pinned
values here.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import math
import random
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import engine.profile as profile_module
from engine import (
    BuildCache, default_design, design_schema, field_footprint, input_limits, load_profile,
)
from engine import check_design as _engine_check_design, generate_design as _engine_generate_design
from engine.core import OPTIONAL_FIELDS, SURFACE_TEMPLATE_ID, TEMPLATE_ID, TEMPLATE_VERSIONS
from engine.geometry import floor6
from engine.layout import Rules, _bends, _bus_at, _junction_drop, _transition, bus_bends, column_plan, row_plan
from engine.profile import profile_issues, profile_template
from exporters import ExportError, build_exports

try:
    import geometry_checks as gc
except ImportError:  # run as a package
    from tests import geometry_checks as gc

try:
    from geometry_checks import straight_channel
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel


def generate_design(design=None, *args, **kwargs):
    """``engine.generate_design`` with the generic template on its straight Row channel, which these tests compare with
    the surface template's (the generic default is the diagonal Row bus since claude/specs/masked-field/
    P5-diagonal-bus.md section 18; geometry_checks.straight_channel leaves surface designs as they are)."""

    return _engine_generate_design(straight_channel(design), *args, **kwargs)


def check_design(design=None, *args, **kwargs):
    """``engine.check_design`` likewise (:func:`generate_design`)."""

    return _engine_check_design(straight_channel(design), *args, **kwargs)


SURFACE = SURFACE_TEMPLATE_ID
GENERIC = TEMPLATE_ID
TIGHT = {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016}
SWEEP_SEED = 20261021
SWEEP_RANDOM = 300
_SIDES = ("bottom", "top", "left", "right")
_OPPOSITE = {"bottom": "top", "top": "bottom", "left": "right", "right": "left"}
_ROWS_TOP = {"top": "rows", "bottom": "columns"}
_COLUMNS_TOP = {"top": "columns", "bottom": "rows"}
# The profile keys in which the surface profile differs from the generic one (the tails' maximum since
# P5-diagonal-bus.md section 23: 200 mm, 80 on the generic profile).  Since the profile revision 2026-10-29 both profiles
# carry the same revision (and the same new sources, coverlay and order values), so the revision is no longer a difference.
SURFACE_PROFILE_CHANGES = {
    "id", "description", "template_id", "sources.surface_template",
    "routing.active_edge_clearance_mm", "routing.row_channel", "tail.minimum_length_mm",
    "fanout.maximum_channels_per_lane", "fanout.maximum_lanes", "fanout.maximum_taper_angle_deg",
    "fanout.minimum_taper_angle_deg", "fanout.bus_angle", "fanout.column_convergence", "limits.maximum_columns",
    "limits.maximum_tail_length_mm",
}


def _surface(matrix: dict | None = None, **sections) -> dict:
    """A surface request: ``matrix`` plus whole sections (``tail``, ``routing``, ...)."""

    request = {"template_id": SURFACE, **sections}
    if matrix is not None:
        request["matrix"] = matrix
    return request


def _square(rows: int, columns: int, pitch: float, fill: float = 0.7) -> dict:
    width = round(min(fill * pitch, pitch - 0.25), 4)
    return {"rows": rows, "columns": columns, "pitch_x_mm": pitch, "pitch_y_mm": pitch, "taxel_width_mm": width, "taxel_height_mm": width}


def _differences(first, second, path: str = "") -> set:
    if isinstance(first, dict) and isinstance(second, dict):
        keys = set(first) | set(second)
        return {found for key in keys for found in _differences(first.get(key, KeyError), second.get(key, KeyError), f"{path}.{key}" if path else key)}
    return set() if first == second else {path}


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _drc_failures(result: dict) -> list:
    return [
        f"{name}.{rule}" for name, board in result["boards"].items() for rule, record in board["verification"]["checks"].items()
        if not record["passed"]
    ] + [f"{name}.registration" for name, board in result["boards"].items() if not board["verification"]["registration"]["passed"]]


def sweep_requests(seed: int = SWEEP_SEED, count: int = SWEEP_RANDOM) -> list[dict]:
    """Fixed extreme surface designs, then ``count`` seeded random ones over the whole input space."""

    fixed = [
        _surface(_square(64, 64, 2.0), routing=TIGHT, tail={"top_length_mm": 20, "bottom_length_mm": 20}),
        _surface(_square(64, 8, 0.6, 0.55), routing=TIGHT),
        _surface(_square(64, 64, 0.6, 0.55), routing=TIGHT),
        _surface(_square(1, 1, 2.0)),
        _surface(_square(1, 1, 10.0, 0.9), routing={"trace_width_mm": 0.254, "trace_space_mm": 0.246}),
        _surface(_square(1, 64, 2.0), routing=TIGHT),
        _surface(_square(64, 1, 2.0), routing={"trace_width_mm": 0.254, "trace_space_mm": 0.246}),
        _surface(_square(16, 32, 2.0), routing=TIGHT, connector={"row_pins": 16, "column_pins": 32}),
        # "All swap": either electrode set on either reader connector.
        _surface(_square(32, 16, 2.0), routing=TIGHT, connector={"row_pins": 32, "column_pins": 16}, role_mapping=_COLUMNS_TOP),
        _surface(_square(12, 32, 2.0), tail={"row_side": "left", "column_side": "right"}, role_mapping=_COLUMNS_TOP),
        _surface(_square(5, 7, 3.0), tail={"row_side": "top", "column_side": "top"}, channel_order={"rows": "descending", "columns": "descending"}),
        _surface(_square(3, 2, 0.6, 0.5), connector={"row_pins": 64, "column_pins": 64}),
    ]
    rng = random.Random(seed)
    for index in range(count):
        rows, columns = rng.randint(1, 64), rng.randint(1, 64)
        pitch_x = round(rng.uniform(0.6, 3.5) if rng.random() < 0.8 else rng.uniform(0.6, 10.0), 3)
        pitch_y = pitch_x if rng.random() < 0.6 else round(rng.uniform(0.6, 6.0), 3)
        width = round(min(max(0.1016, rng.uniform(0.2, 0.95) * pitch_x), pitch_x - 0.25), 4)
        height = round(min(max(0.1016, rng.uniform(0.2, 0.95) * pitch_y), pitch_y - 0.25), 4)
        routing = rng.choice(((0.1016, 0.1016), (0.127, 0.127), (0.254, 0.246), None))
        if routing is None:
            trace = round(rng.uniform(0.1016, 0.254), 4)
            routing = (trace, round(rng.uniform(0.1016, min(0.246, 0.5 - trace)), 4))
        side = rng.choice(_SIDES)
        fixed.append(_surface(
            {"rows": rows, "columns": columns, "pitch_x_mm": pitch_x, "pitch_y_mm": pitch_y, "taxel_width_mm": width, "taxel_height_mm": height},
            project_name=f"Sweep {index}",
            tail={"top_length_mm": round(rng.uniform(7.5, 80.0), 3), "bottom_length_mm": round(rng.uniform(7.5, 80.0), 3),
                  "row_side": side, "column_side": rng.choice((side, _OPPOSITE[side]))},
            connector={"row_pins": rng.choice((None, None, rng.randint(rows, 64))), "column_pins": rng.choice((None, None, rng.randint(columns, 64)))},
            role_mapping=rng.choice((_ROWS_TOP, _COLUMNS_TOP)),
            channel_order={"rows": rng.choice(("ascending", "descending")), "columns": rng.choice(("ascending", "descending"))},
            routing={"trace_width_mm": routing[0], "trace_space_mm": routing[1]},
        ))
    return fixed


class SurfaceProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generic = load_profile()
        cls.surface = load_profile(SURFACE)

    def test_each_template_loads_its_own_consistent_profile(self) -> None:
        self.assertEqual(profile_issues(self.surface), [])
        self.assertEqual((self.generic["id"], profile_template(self.generic)), ("jlc-fpc-standard-v1", GENERIC))
        self.assertEqual((self.surface["id"], profile_template(self.surface)), ("jlc-fpc-surface-v1", SURFACE))
        self.assertNotIn("template_id", self.generic)
        self.assertEqual(load_profile(GENERIC), self.generic)
        self.assertEqual(set(TEMPLATE_VERSIONS), set(profile_module.TEMPLATE_IDS))
        for template in (None, "", "canonical_12x32", 1):
            with self.subTest(template=template), self.assertRaises(ValueError):
                load_profile(template)

    def test_the_surface_profile_is_the_generic_one_with_the_v4_rules(self) -> None:
        self.assertEqual(_differences(self.generic, self.surface), SURFACE_PROFILE_CHANGES)
        self.assertEqual(self.surface["routing"]["active_edge_clearance_mm"], 0.5)
        self.assertEqual(
            self.surface["routing"]["active_edge_clearance_mm"],
            self.surface["routing"]["electrode_overhang_mm"] + self.surface["fabrication"]["copper_to_board_edge_mm"],
        )
        fanout = self.surface["fanout"]
        self.assertEqual((fanout["maximum_lanes"], fanout["maximum_channels_per_lane"], self.surface["limits"]["maximum_columns"]), (1, 64, 64))
        self.assertEqual((fanout["minimum_taper_angle_deg"], fanout["maximum_taper_angle_deg"]), (60.0, 85.0))
        self.assertEqual((fanout["bus_angle"], fanout["column_convergence"], self.surface["routing"]["row_channel"]), ("shortest", "direct", "tight"))
        self.assertEqual(self.surface["tail"]["minimum_length_mm"], 7.5)
        self.assertEqual((self.surface["limits"]["maximum_tail_length_mm"], self.generic["limits"]["maximum_tail_length_mm"]), (200.0, 80.0))
        # The generic profile sets no policy: absent keys are the generic behaviour.
        for (section, key), allowed in profile_module.POLICIES.items():
            self.assertNotIn(key, self.generic[section])
            self.assertEqual(getattr(Rules(self.generic), key), allowed[0])

    def test_policy_keys_are_checked_only_when_present(self) -> None:
        def issues(edit) -> set:
            profile = copy.deepcopy(self.surface)
            edit(profile)
            return {(issue["code"], issue["field"]) for issue in profile_issues(profile)}

        self.assertEqual(issues(lambda p: p["routing"].update(row_channel="wide")), {("E_PROFILE_INCONSISTENT", "profile.routing.row_channel")})
        self.assertEqual(issues(lambda p: p["fanout"].update(bus_angle="steep")), {("E_PROFILE_INCONSISTENT", "profile.fanout.bus_angle")})
        self.assertEqual(issues(lambda p: p["fanout"].update(column_convergence=None)), {("E_PROFILE_INCONSISTENT", "profile.fanout.column_convergence")})
        self.assertEqual(issues(lambda p: p["fanout"].pop("minimum_taper_angle_deg")), {("E_PROFILE_MISSING", "profile.fanout.minimum_taper_angle_deg")})
        self.assertEqual(issues(lambda p: p["fanout"].update(minimum_taper_angle_deg=86.0)), {("E_PROFILE_INCONSISTENT", "profile.fanout.minimum_taper_angle_deg")})
        self.assertEqual(issues(lambda p: p.update(template_id="other")), {("E_PROFILE_INCONSISTENT", "profile.template_id")})
        self.assertIn(("E_PROFILE_INCONSISTENT", "profile.fanout.column_convergence"),
                      issues(lambda p: p["fanout"].update(maximum_lanes=2, maximum_channels_per_lane=32)))
        # The caps tried are whole degrees from at least 1 degree (a flatter cap has no bend stagger).
        for lowest in (0.0001, 0.5, 60.5):
            self.assertEqual(issues(lambda p: p["fanout"].update(minimum_taper_angle_deg=lowest)), {("E_PROFILE_INCONSISTENT", "profile.fanout.minimum_taper_angle_deg")})
        self.assertEqual(issues(lambda p: p["fanout"].update(minimum_taper_angle_deg=1.0, maximum_taper_angle_deg=84.5)), set())
        flat = copy.deepcopy(self.generic)
        flat["fanout"]["maximum_taper_angle_deg"] = 0.0001
        self.assertEqual({(issue["code"], issue["field"]) for issue in profile_issues(flat)}, {("E_PROFILE_INCONSISTENT", "profile.fanout.maximum_taper_angle_deg")})
        # The tail check at the 85 degree cap needs 7.344 mm.
        self.assertEqual(issues(lambda p: p["tail"].update(minimum_length_mm=7.3)), {("E_PROFILE_INCONSISTENT", "profile.tail.minimum_length_mm")})
        self.assertEqual(issues(lambda p: p["tail"].update(minimum_length_mm=7.35)), set())
        # Policies without the template are allowed (the template follows the profile file).
        generic = copy.deepcopy(self.generic)
        generic["routing"]["row_channel"] = "contact_aligned"
        generic["fanout"].update(bus_angle="cap", column_convergence="bundle")
        self.assertEqual(profile_issues(generic), [])

    def test_a_profile_file_of_another_template_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "surface.json"
            path.write_text(json.dumps(self.generic), encoding="utf-8")
            with mock.patch.object(profile_module, "SURFACE_PROFILE_PATH", path):
                with self.assertRaisesRegex(profile_module.ProfileError, "names template 'generic_matrix_v1'"):
                    load_profile(SURFACE)

    def test_the_angle_caps_and_the_transition_search(self) -> None:
        rules, generic = Rules(self.surface), Rules(self.generic)
        self.assertEqual([round(math.degrees(cap), 9) for cap in rules.taper_caps], [float(angle) for angle in range(60, 86)])
        self.assertEqual(generic.taper_caps, [generic.max_taper])
        pitch = 0.2032
        upper = [round(0.3518 + index * pitch, 6) for index in range(16)]
        lower = [round(0.5 + index * 0.5, 6) for index in range(16)]
        # The generic cap policy is bus_bends + _bends at the profile's cap.
        angle, stagger = bus_bends(pitch, generic)
        self.assertEqual(_transition(upper, lower, 0.0, False, pitch, generic), (_bends(upper, lower, 0.0, False, angle, stagger), angle, stagger))
        # The search keeps the lowest transition; a tie keeps the smaller cap.
        for top, below in ((0.0, False), (-0.5, True)):
            bends, angle, _ = _transition(upper, lower, top, below, pitch, rules)
            heights = []
            for cap in rules.taper_caps:
                levels = [y for bend in _bends(upper, lower, top, below, *_bus_at(pitch, cap)) if bend for y in bend]
                heights.append(round((top if below else max(levels)) - min(levels), 6))
            levels = [y for bend in bends if bend for y in bend]
            self.assertEqual(round((top if below else max(levels)) - min(levels), 6), min(heights))
            self.assertEqual(angle, _bus_at(pitch, rules.taper_caps[heights.index(min(heights))])[0])
            self.assertGreater(len(set(heights)), 1)
        straight = [0.5 * index for index in range(5)]
        bends, angle, _ = _transition(straight, straight, 0.0, False, pitch, rules)
        self.assertEqual((bends, angle), ([None] * 5, _bus_at(pitch, rules.taper_caps[0])[0]))
        # Where the traces widen below the transition, the search runs on down to that
        # junction: the widening drop grows with the angle, so two lanes take a flatter cap.
        upper, lower, trace = [0.3518, 0.555], [0.5, 1.0], 0.1016
        plain = _transition(upper, lower, 0.0, False, pitch, rules)
        joined = _transition(upper, lower, 0.0, False, pitch, rules, junction=trace)
        costs = []
        for cap in rules.taper_caps:
            angle, stagger = _bus_at(pitch, cap)
            levels = [y for bend in _bends(upper, lower, 0.0, False, angle, stagger) if bend for y in bend]
            costs.append(round(max(levels) - floor6(min(levels) - _junction_drop(trace, angle, rules)), 6))
        self.assertEqual(joined[1], _bus_at(pitch, rules.taper_caps[costs.index(min(costs))])[0])
        self.assertLess(joined[1], plain[1])
        self.assertEqual(_transition(upper, lower, 0.0, False, pitch, generic, junction=trace), _transition(upper, lower, 0.0, False, pitch, generic))
        # The bends depend on the routes' shifts only (the search is cached on them).
        moved = _transition([round(x + 3.0, 6) for x in upper], [round(x + 3.0, 6) for x in lower], 0.0, False, pitch, rules, junction=trace)
        self.assertEqual(moved, joined)
        # A fractional maximum is tried after the whole degrees.
        profile = copy.deepcopy(self.surface)
        profile["fanout"]["maximum_taper_angle_deg"] = 84.5
        self.assertEqual([round(math.degrees(cap), 9) for cap in Rules(profile).taper_caps][-3:], [83.0, 84.0, 84.5])


class SurfaceInputTests(unittest.TestCase):
    def test_the_surface_default_is_the_generic_preset_on_the_surface_template(self) -> None:
        design = default_design(SURFACE)
        # The generic template names its Row traces (routing.row_sides both, section 18); the surface default leaves them out.
        # Its bottom tail is the surface profile's 7.5 mm minimum; the generic default's 12 mm since P5-diagonal-bus.md
        # section 27.7 (the rectangular mode's tails 12 / 12, ending together; that minimum from section 20 until then).
        self.assertEqual(_differences(default_design(), design), {"template_id", "routing.row_sides", "tail.bottom_length_mm"})
        self.assertEqual(default_design()["tail"]["bottom_length_mm"], 12.0)
        self.assertEqual(design["tail"]["bottom_length_mm"], load_profile(SURFACE)["tail"]["minimum_length_mm"])
        self.assertEqual(default_design(), default_design(GENERIC))
        with self.assertRaises(ValueError):
            default_design("canonical_12x32")
        # A partial surface request takes the surface defaults.
        result = check_design({"template_id": SURFACE})
        self.assertTrue(result["ok"], result["validation"]["errors"])
        self.assertEqual(result["design"], design)
        self.assertEqual(generate_design({"template_id": SURFACE})["profile"]["id"], "jlc-fpc-surface-v1")

    def test_columns_up_to_64_on_the_surface_profile(self) -> None:
        # The surface template, and the generic template's diagonal Row bus (built with the surface profile since
        # P5-diagonal-bus.md section 20); the generic template's straight Row channel keeps 32 columns and 7.0 mm tails.
        def codes(request) -> list:
            return [issue["code"] for issue in check_design(request)["validation"]["errors"]]

        def bus_codes(request) -> list:  # the generic template's default Row traces, the bus
            return [issue["code"] for issue in _engine_check_design(request)["validation"]["errors"]]

        channel = {"row_sides": "channel"}
        self.assertEqual(codes(_surface(_square(16, 64, 2.0))), [])
        self.assertEqual(codes(_surface(_square(16, 65, 2.0))), ["E_COLUMNS_RANGE"])
        self.assertEqual(bus_codes({"matrix": _square(16, 64, 2.0)}), [])
        self.assertEqual(bus_codes({"matrix": _square(16, 65, 2.0)}), ["E_COLUMNS_RANGE"])
        self.assertIn("E_COLUMNS_RANGE", codes({"template_id": GENERIC, "matrix": _square(16, 33, 2.0), "routing": channel}))
        self.assertEqual(codes({"matrix": _square(16, 32, 2.0), "routing": channel}), [])
        # The surface tails start at 7.5 mm, the generic straight channel's at 7.0.
        self.assertEqual(codes(_surface(tail={"bottom_length_mm": 7.4})), ["E_TAIL_LENGTH"])
        self.assertEqual(bus_codes({"tail": {"bottom_length_mm": 7.4}}), ["E_TAIL_LENGTH"])
        self.assertEqual(codes({"tail": {"bottom_length_mm": 7.4}, "routing": channel}), [])
        # Rows and connector pins stay up to 64 on both.
        self.assertEqual(codes(_surface(_square(64, 64, 1.0), connector={"row_pins": 64, "column_pins": 64})), [])
        self.assertEqual(codes(_surface(connector={"row_pins": 65})), ["E_CONNECTOR_PINS"])

    def test_unknown_templates_and_mismatched_profiles_are_errors(self) -> None:
        for value in (None, "canonical_12x32", 1, "surface_matrix_v2"):
            with self.subTest(template_id=value):
                result = generate_design({"template_id": value})
                self.assertEqual([(issue["code"], issue["field"]) for issue in result["validation"]["errors"]], [("E_TEMPLATE_UNSUPPORTED", "template_id")])
        surface, generic = load_profile(SURFACE), load_profile()
        # The generic template's diagonal Row bus is built with the surface profile (P5-diagonal-bus.md section 20).
        for request, profile, built in (({"template_id": SURFACE}, generic, "its own profile"), ({"routing": {"row_sides": "channel"}}, surface, "its own profile"),
                                        ({}, generic, "the diagonal Row bus's profile")):
            with self.subTest(request=request):
                result = _engine_generate_design(request, profile=profile)
                self.assertFalse(result["ok"])
                self.assertEqual([issue["code"] for issue in result["validation"]["errors"]], ["E_TEMPLATE_UNSUPPORTED"])
                self.assertIn(f"is built with {built}", result["validation"]["errors"][0]["message"])
        self.assertTrue(_engine_generate_design({}, profile=surface)["ok"])

    def test_limits_and_schema_follow_the_profile_template(self) -> None:
        surface = load_profile(SURFACE)
        limits, generic = input_limits(surface), input_limits()
        # The generic template's bounds are its default's, the diagonal Row bus built with the surface profile; the
        # straight channel's own under "channel" (P5-diagonal-bus.md section 20).
        self.assertEqual((limits["matrix.columns"]["maximum"], generic["matrix.columns"]["maximum"]), (64, 64))
        self.assertEqual((limits["tail.bottom_length_mm"]["minimum"], generic["tail.bottom_length_mm"]["minimum"]), (7.5, 7.5))
        self.assertEqual((generic["matrix.columns"]["channel"], generic["tail.bottom_length_mm"]["channel"]), ({"maximum": 32}, {"minimum": 7.0, "default": 7.0}))
        self.assertNotIn("channel", limits["matrix.columns"])
        self.assertEqual((limits["template_id"]["const"], generic["template_id"]["const"]), (SURFACE, GENERIC))
        self.assertEqual(limits["tail.bottom_length_mm"]["default"], 7.5)
        self.assertEqual(limits["matrix.columns"]["description"], "Column electrodes, all in one fan-out lane of up to 64.")
        schema = design_schema(surface)
        self.assertEqual(schema["properties"]["template_id"]["const"], SURFACE)
        self.assertEqual(schema["properties"]["matrix"]["properties"]["columns"]["maximum"], 64)
        self.assertEqual(schema["x-profile"]["id"], "jlc-fpc-surface-v1")
        self.assertEqual(design_schema()["properties"]["template_id"]["const"], GENERIC)


class SurfaceIdentityTests(unittest.TestCase):
    # The surface default build (12 x 32 at 2 mm): pinned like the generic golden build.  Re-pinned by P5-diagonal-bus.md
    # section 23 (2026-10-25): the surface profile's tails to 200 mm, a new profile digest (before: fc86e20497d3, b9bf445b...).
    # Re-pinned by the profile revision 2026-10-29 (the gold-finger thickness order option and the coverlay-window notes):
    # a new profile digest and revision (before: 89ad79654dd6, 0cf8782b...).  Re-pinned by the user's decision of
    # 2026-11-06 (the default fill 0.7 -> 0.5): the default electrodes 1.4 -> 1.0 mm, a new design (before: 527bfeafd16e,
    # d580000c...).  Re-pinned by the profile revision 2026-11-06 (the order: JLC's 2-layer 0.2 mm FPC, the bottom copper
    # empty): a new profile digest and revision (before: 0fa31c3236be, 308eb329...); the design and the boards as before.
    # Re-pinned by the profile revision 2026-11-06b (the user's later decision of 2026-11-06: the PI stiffener 0.225 ->
    # 0.1 mm, the 2-layer 0.2 mm FPC + 0.1 mm the 0.3 mm gold fingers by JLC's rule): a new profile digest and revision
    # (before: e484a57c9a40, fb37953c...); the design as before, the boards with the stiffener's new thickness.
    DEFAULT_IDENTITY = {
        "build_id": "tactile-fpc-12x32-486988205e7c",
        "design_sha256": "87581f25ad863355e1fae87419798e53537e9a403ef900f0122e0a46ac1ff38a",
        "profile_sha256": "299b1ab7c76ab719153e638908798f493f70adaa1abf771e3dda878077ca8de9",
        "template": "surface-matrix/1",
        "profile": {"id": "jlc-fpc-surface-v1", "revision": "2026-11-06b"},
    }

    def test_the_same_matrix_in_both_templates_has_two_identities(self) -> None:
        request = {"matrix": _square(16, 32, 2.0), "routing": TIGHT, "tail": {"top_length_mm": 12, "bottom_length_mm": 12}}
        generic, surface = generate_design(request), generate_design(dict(request, template_id=SURFACE))
        self.assertTrue(generic["ok"] and surface["ok"])
        # The generic design names its straight channel (routing.row_sides channel); the surface design leaves it out.
        self.assertEqual(_differences(generic["design"], surface["design"]), {"template_id", "routing.row_sides"})
        for key in ("build_id", "build_sha256", "design_sha256", "profile_sha256"):
            self.assertNotEqual(generic["manifest"][key], surface["manifest"][key], key)
        self.assertNotIn("template", generic["manifest"])
        self.assertEqual(surface["manifest"]["template"], "surface-matrix/1")
        for key in ("generator", "exporter", "layout_format", "format"):
            self.assertEqual(generic["manifest"][key], surface["manifest"][key], key)
        self.assertEqual(
            {board["verification"]["drc_version"] for result in (generic, surface) for board in result["boards"].values()}, {"whole-board-v3"}
        )
        # The build hash covers the template version.
        manifest = surface["manifest"]
        basis = {key: manifest[key] for key in ("design_sha256", "profile_sha256", "generator", "exporter", "template")}
        self.assertEqual(_sha256(_canonical(basis)), manifest["build_sha256"])
        self.assertEqual(manifest["build_id"], f"{manifest['slug']}-{manifest['build_sha256'][:12]}")
        self.assertEqual(check_design(dict(request, template_id=SURFACE))["identity"]["build_id"], manifest["build_id"])

    def test_the_surface_default_identity_is_pinned_and_deterministic(self) -> None:
        cache = BuildCache()
        first, second = generate_design({"template_id": SURFACE}, cache=cache), generate_design(default_design(SURFACE), cache=cache)
        self.assertEqual(cache.hits, 1)
        for result in (first, second):
            self.assertEqual({key: result["manifest"][key] for key in self.DEFAULT_IDENTITY}, self.DEFAULT_IDENTITY)
        self.assertEqual(_canonical(first["boards"]), _canonical(second["boards"]))
        identity = check_design({"template_id": SURFACE})["identity"]
        self.assertEqual((identity["build_id"], identity["template"]), (self.DEFAULT_IDENTITY["build_id"], "surface-matrix/1"))
        self.assertNotIn("template", check_design({})["identity"])


class SurfaceGeometryTests(unittest.TestCase):
    def test_footprint_shrinks_against_the_generic_template(self) -> None:
        request = {"matrix": _square(16, 32, 2.0), "routing": TIGHT}
        generic = field_footprint(check_design(request)["design"], load_profile())
        surface = field_footprint(check_design(dict(request, template_id=SURFACE))["design"], load_profile(SURFACE))
        self.assertEqual(generic["field"], surface["field"])
        # The direct one-lane Column fan-out: 4.2 mm instead of 22.2 mm (two lanes at 60 degrees).
        self.assertLessEqual(surface["column"]["bottom"], 5.0)
        self.assertGreater(generic["column"]["bottom"], 20.0)
        # The tight channel and expansion, and the 0.5 mm margin elsewhere.
        self.assertLess(surface["row"]["left"], generic["row"]["left"] - 0.75)
        self.assertLess(surface["row"]["bottom"], generic["row"]["bottom"])
        for board, sides in (("row", ("right", "top")), ("column", ("left", "right", "top"))):
            for side in sides:
                self.assertEqual((surface[board][side], generic[board][side]), (0.5, 0.75), (board, side))

    def test_pinned_surface_values(self) -> None:
        # Research of 2026-10-20 (V4): 64 x 64 at 2 mm, minimum routing, 20 mm tails.
        result = generate_design(_surface(_square(64, 64, 2.0), routing=TIGHT, tail={"top_length_mm": 20, "bottom_length_mm": 20}))
        self.assertTrue(result["ok"], result["validation"]["errors"])
        row, column = result["boards"]["row"], result["boards"]["column"]
        self.assertEqual((row["metrics"]["outline_width_mm"], row["metrics"]["outline_height_mm"]), (141.554201, 156.833576))
        self.assertEqual((column["metrics"]["outline_width_mm"], column["metrics"]["outline_height_mm"]), (128.4, 155.024239))
        self.assertEqual(row["construction"]["channel_width_mm"], 13.154201)
        self.assertEqual((row["construction"]["merger_taper_angle_deg"], row["construction"]["merger_height_mm"]), (65.998885, 8.391487))
        self.assertEqual((column["construction"]["entry_taper_angle_deg"], column["construction"]["entry_transition_height_mm"]), (83.999342, 5.750659))
        self.assertEqual((column["construction"]["merger_taper_angle_deg"], column["construction"]["merger_height_mm"]), (0.0, 0.0))
        footprint = field_footprint(result["design"], result["profile"])
        self.assertEqual((footprint["row"]["left"], footprint["row"]["bottom"], footprint["column"]["bottom"]), (13.654201, 8.933576, 7.124239))
        self.assertEqual(column["tail"]["fanout_lane_count"], 1)
        self.assertEqual({route["fanout"] for route in column["layers"]["top_copper"]["routes"]}, {"single_lane_direct"})
        self.assertEqual({route["fanout"] for route in row["layers"]["top_copper"]["routes"]}, {"left_channel_non_crossing"})
        for board in (row, column):
            self.assertEqual(board["verification"]["checks"]["active_field_margin"]["measured_mm"], 0.5)

    def test_each_transition_takes_its_lowest_cap_down_to_the_junction(self) -> None:
        # The search compares the whole height down to where the traces widen: a steeper
        # cap can give lower bends but a longer widening drop, and then it loses.
        surface = load_profile(SURFACE)
        forced = {}
        for cap in range(60, 86):
            profile = copy.deepcopy(surface)
            profile["fanout"]["minimum_taper_angle_deg"] = profile["fanout"]["maximum_taper_angle_deg"] = float(cap)
            forced[cap] = profile

        def row_start(design, profile):
            return row_plan(design, profile)["active"][1]

        def column_root(design, profile):
            plan = column_plan(design, profile)
            return round(plan["active"][1] - plan["tail_top"], 6)

        # 2 rows (66 instead of 74 degrees) and 2 columns at 0.6 mm (60 instead of 85 degrees).
        for matrix, depth, planner, bends in ((_square(2, 4, 2.0), row_start, row_plan, "expansion_height"),
                                              (_square(4, 2, 0.6), column_root, column_plan, "entry_height")):
            with self.subTest(board=planner.__name__):
                design = check_design(_surface(matrix, routing=TIGHT))["design"]
                depths = {cap: depth(design, profile) for cap, profile in forced.items()}
                self.assertEqual(depth(design, surface), min(depths.values()))
                heights = {cap: planner(design, profile)[bends] for cap, profile in forced.items()}
                lowest_bends = min(heights, key=lambda cap: (heights[cap], cap))
                self.assertGreater(depths[lowest_bends], min(depths.values()))

    def test_the_tight_channel_keeps_its_rules(self) -> None:
        profile = load_profile(SURFACE)
        rules = Rules(profile)
        for trace in (0.1016, 0.127, 0.254):
            request = _surface(_square(16, 8, 2.0), routing={"trace_width_mm": trace, "trace_space_mm": 0.1016 if trace == 0.254 else trace})
            result = generate_design(request)
            self.assertTrue(result["ok"], result["validation"]["errors"])
            plan = row_plan(result["design"], profile)
            # Lane 1 at the copper-to-edge rule (and the outline allowance) from the board edge.
            self.assertAlmostEqual(plan["lanes"][0] - trace / 2, rules.copper_to_edge + rules.offset_allowance, delta=1e-6)
            # The innermost lane keeps the opening-to-trace rule from the merged field window.
            board = result["boards"]["row"]
            (window,) = [o for o in board["layers"]["top_coverlay_openings"] if o["kind"] == "electrode_field_opening"]
            self.assertGreaterEqual(round(window["x"] - (plan["lanes"][-1] + trace / 2), 6), rules.opening_to_trace)
            self.assertLess(window["x"] - (plan["lanes"][-1] + trace / 2), rules.opening_to_trace + 2e-6)
            # The Column fan-out converges straight into the contact columns.
            cplan = column_plan(result["design"], profile)
            self.assertEqual((cplan["convergence"], cplan["decks"]), ("direct", cplan["contact_x"][:8]))
            self.assertEqual(cplan["merger"], [None] * 8)
            # No straight stretch between convergence and contacts: the tail starts one widening drop below the lowest bend.
            lowest = min(y for bend in cplan["entry"] if bend for y in bend)
            angle = math.radians(cplan["entry_angle_deg"])
            self.assertEqual((cplan["deck_bottom"], cplan["tail_top"]), (cplan["deck_top"], floor6(lowest - _junction_drop(trace, angle, rules))))

    def test_lanes_that_need_no_expansion_run_straight(self) -> None:
        # One row, or a bundle pitch equal to the 0.5 mm contact pitch: the lanes sit
        # right above their contacts, and the field starts one margin above the tail root.
        profile, rules = load_profile(SURFACE), Rules(load_profile(SURFACE))
        wide = {"trace_width_mm": 0.254, "trace_space_mm": 0.246}
        for matrix, routing, pins in ((_square(64, 8, 2.0), wide, 64), (_square(16, 8, 2.0), wide, None), (_square(1, 4, 2.0), TIGHT, None)):
            request = _surface(matrix, routing=routing, connector={"row_pins": pins})
            with self.subTest(rows=matrix["rows"], routing=routing):
                result, generic = generate_design(request), generate_design(dict(request, template_id=GENERIC))
                self.assertTrue(result["ok"] and generic["ok"], result["validation"]["errors"])
                plan = row_plan(result["design"], profile)
                self.assertEqual(plan["lanes"], plan["contact_x"][:matrix["rows"]])
                self.assertEqual((plan["expansion"], plan["expansion_height"]), ([None] * matrix["rows"], 0.0))
                self.assertEqual(plan["active"][1], rules.margin)
                board = result["boards"]["row"]
                window = min(o["x"] for o in board["layers"]["top_coverlay_openings"] if o["kind"] in ("electrode_field_opening", "sensor_electrode_opening"))
                self.assertGreaterEqual(round(window - (plan["lanes"][-1] + routing["trace_width_mm"] / 2), 6), rules.opening_to_trace)
                self.assertEqual(_drc_failures(result), [])
                for key in ("outline_width_mm", "outline_height_mm"):
                    self.assertLessEqual(board["metrics"][key], generic["boards"]["row"]["metrics"][key], key)

    def test_field_footprint_matches_the_built_boards(self) -> None:
        requests = [
            _surface(_square(16, 32, 2.0), routing=TIGHT), _surface(_square(64, 8, 0.6, 0.55), routing=TIGHT),
            _surface(_square(3, 40, 1.5), connector={"row_pins": 64}), {"matrix": _square(12, 17, 2.0)}, {},
        ]
        for request in requests:
            result = generate_design(request)
            self.assertTrue(result["ok"], result["validation"]["errors"])
            footprint = field_footprint(result["design"], result["profile"])
            for key, board in result["boards"].items():
                with self.subTest(template=result["design"]["template_id"], board=key):
                    active, tail = board["grid_registration"]["active_region"], board["tail"]["bounds"]
                    root = tail["y"] + tail["height"]
                    above = [point for point in board["outline"]["points"] if point[1] >= root - 1e-9]
                    measured = {
                        "left": round(active["x"] - min(x for x, _ in above), 6),
                        "right": round(max(x for x, _ in above) - active["x"] - active["width"], 6),
                        "top": round(max(y for _, y in above) - active["y"] - active["height"], 6),
                        "bottom": round(active["y"] - root, 6),
                    }
                    self.assertEqual({side: footprint[key][side] for side in measured}, measured)
                    self.assertEqual(footprint[key]["tail"], {"x": round(tail["x"] - active["x"], 6), "width": tail["width"], "length": tail["height"]})
                    self.assertEqual(footprint["field"], {"width": active["width"], "height": active["height"]})

    def test_a_row_tail_wider_than_the_body_is_reported_as_the_tail(self) -> None:
        # 1 x 1 with a 64-pin Row tail: the tail's shoulder lies on the root line, far
        # beyond the body; the footprint's right side is the body's (above the fillet
        # into the shoulder), the tail is its own entry.
        result = generate_design(_surface(_square(1, 1, 2.0), connector={"row_pins": 64}))
        self.assertTrue(result["ok"], result["validation"]["errors"])
        footprint, board = field_footprint(result["design"], result["profile"])["row"], result["boards"]["row"]
        active, tail = board["grid_registration"]["active_region"], board["tail"]["bounds"]
        above = tail["y"] + tail["height"] + result["profile"]["outline"]["outline_fillet_radius_mm"] + 1e-6
        body = [point for point in board["outline"]["points"] if point[1] > above]
        self.assertEqual(footprint["right"], round(max(x for x, _ in body) - active["x"] - active["width"], 6))
        self.assertEqual(footprint["right"], 0.5)
        self.assertEqual(footprint["tail"], {"x": round(tail["x"] - active["x"], 6), "width": 32.5, "length": tail["height"]})
        self.assertGreater(footprint["tail"]["x"] + footprint["tail"]["width"], active["width"] + footprint["right"] + 25.0)


class SurfaceSweepTests(unittest.TestCase):
    """Over 300 seeded surface designs build DRC-clean; the others are only too large to fabricate."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.requests = sweep_requests()
        cls.results = [generate_design(request) for request in cls.requests]

    def test_every_buildable_design_is_drc_clean(self) -> None:
        built = 0
        for index, result in enumerate(self.results):
            with self.subTest(index=index, matrix=result["design"]["matrix"]):
                codes = {issue["code"] for issue in result["validation"]["errors"]}
                if not result["ok"]:
                    self.assertEqual(codes, {"E_BOARD_SIZE"})
                    continue
                built += 1
                self.assertEqual(_drc_failures(result), [])
                self.assertEqual(result["manifest"]["template"], "surface-matrix/1")
                for board in result["boards"].values():
                    margin = board["verification"]["checks"]["active_field_margin"]
                    self.assertEqual((margin["required_mm"], margin["measured_mm"] >= 0.5), (0.5, True))
                    for key in ("entry_taper_angle_deg", "merger_taper_angle_deg"):
                        self.assertLessEqual(board["construction"].get(key, 0.0), 85.0)
                    self.assertGreaterEqual(board["construction"].get("merger_taper_angle_deg", 60.0), 0.0)
                self.assertEqual(result["boards"]["column"]["tail"]["fanout_lane_count"], 1)
        self.assertGreaterEqual(built, 300)

    def test_the_sweep_covers_the_input_space(self) -> None:
        designs = [result["design"] for result in self.results if result["ok"]]
        self.assertEqual({design["tail"]["row_side"] for design in designs}, set(_SIDES))
        self.assertTrue(any(design["tail"]["row_side"] != design["tail"]["column_side"] for design in designs))
        self.assertEqual({design["role_mapping"]["top"] for design in designs}, {"rows", "columns"})
        self.assertEqual({design["channel_order"]["rows"] for design in designs}, {"ascending", "descending"})
        self.assertLessEqual({(1, 1), (64, 64), (64, 8), (1, 64), (64, 1)}, {(d["matrix"]["rows"], d["matrix"]["columns"]) for d in designs})
        self.assertGreaterEqual(sum(design["matrix"]["columns"] > 32 for design in designs), 100)
        routings = {(design["routing"]["trace_width_mm"], design["routing"]["trace_space_mm"]) for design in designs}
        self.assertLessEqual({(0.1016, 0.1016), (0.127, 0.127), (0.254, 0.246)}, routings)
        self.assertTrue(any(design["connector"]["row_pins"] == 64 for design in designs))
        self.assertEqual({design["matrix"]["pitch_x_mm"] for design in designs if design["matrix"]["pitch_x_mm"] in (0.6, 10.0)}, {0.6, 10.0})


class SurfaceExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        requests = (
            {"template_id": SURFACE},
            _surface(_square(32, 16, 2.0), routing=TIGHT, connector={"row_pins": 32, "column_pins": 16}, role_mapping=_COLUMNS_TOP,
                     tail={"row_side": "left", "column_side": "right"}),
            _surface(_square(1, 1, 2.0), tail={"row_side": "top", "column_side": "bottom"}),
        )
        cls.results = [generate_design(request) for request in requests]

    def test_exports_and_their_read_back_pass(self) -> None:
        for result in self.results:
            with self.subTest(build=result["manifest"]["build_id"]):
                self.assertTrue(result["ok"], result["validation"]["errors"])
                exports = build_exports(result)  # regenerates, re-checks and decodes every file it writes
                for board in result["boards"].values():
                    with zipfile.ZipFile(io.BytesIO(exports[f"{board['physical_side']}_fpc_gerber_zip"])) as archive:
                        outline = archive.read("Gerber_BoardOutlineLayer.GKO").decode("ascii")
                        copper = archive.read("Gerber_TopLayer.GTL").decode("ascii")
                    strokes, _ = gc.decode_gerber(outline)
                    self.assertTrue(gc.same_ring(strokes[0][:-1], board["outline"]["points"], 1e-6))
                    routes, _ = gc.decode_gerber(copper)
                    self.assertEqual(len(routes), len(board["layers"]["top_copper"]["routes"]))
                with zipfile.ZipFile(io.BytesIO(exports["project_review_bundle_zip"])) as archive:
                    manifest = json.loads(archive.read("manifest.json"))
                    design, profile = json.loads(archive.read("design.json")), json.loads(archive.read("profile.json"))
                self.assertEqual(manifest["build_id"], result["manifest"]["build_id"])
                # The bundle verifies its own identity: the recipe it states, from its own files.
                self.assertEqual(manifest["template"], "surface-matrix/1")
                self.assertEqual(manifest["identity"]["build_sha256"],
                                 "sha256 of the canonical JSON of {design_sha256, profile_sha256, generator, exporter, template}")
                basis = {
                    "design_sha256": _sha256(_canonical(design)), "profile_sha256": _sha256(_canonical(profile)),
                    "generator": manifest["generator"], "exporter": manifest["exporter"], "template": manifest["template"],
                }
                self.assertEqual(_sha256(_canonical(basis)), manifest["build_sha256"])
                self.assertTrue(manifest["build_id"].endswith("-" + manifest["build_sha256"][:12]))
                for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
                    with zipfile.ZipFile(io.BytesIO(exports[key])) as archive:
                        board_manifest = json.loads(archive.read("manifest.json"))
                    for field in ("build_id", "build_sha256", "design_sha256", "profile_sha256", "generator", "exporter", "template", "profile"):
                        self.assertEqual(board_manifest[field], manifest[field], (key, field))

    def test_a_result_without_its_template_identity_is_refused(self) -> None:
        result = copy.deepcopy(self.results[0])
        del result["manifest"]["template"]
        with self.assertRaises(ExportError):
            build_exports(result)
        result = copy.deepcopy(self.results[0])
        result["design"]["template_id"] = GENERIC
        with self.assertRaises(ExportError):
            build_exports(result)


class SurfaceDocumentTests(unittest.TestCase):
    """docs/API.md and docs/LAYOUT_SCHEMA.md: the surface tables and figures against the code."""

    ROOT = Path(__file__).resolve().parents[1]

    @staticmethod
    def _section(text: str, heading: str) -> str:
        lines = text.splitlines()
        start = lines.index(heading) + 1
        level = heading.split(" ")[0]
        end = next((index for index in range(start, len(lines)) if lines[index].startswith(("# ", level + " ")) ), len(lines))
        return "\n".join(lines[start:end])

    @staticmethod
    def _rows(text: str) -> list:
        return [
            [cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in text.splitlines() if line.startswith("| `")
        ]

    def test_the_api_surface_table_lists_every_limit_that_differs(self) -> None:
        text = (self.ROOT / "docs" / "API.md").read_text(encoding="utf-8")
        section = self._section(text, "## Surface template (`surface_matrix_v1`)")
        # Against the generic template's straight Row channel, its own profile (its bus is the surface profile's).
        surface = input_limits(load_profile(SURFACE))
        generic = {field: {**spec, **spec.get("channel", {})} for field, spec in input_limits().items()}
        # Fields of the surface template alone (the field mask) and kinds without a range have
        # their own tables in the section; this one lists the shared fields whose range differs.
        differing = {
            field for field in surface
            if field in generic and (surface[field]["type"] in ("integer", "number") or "const" in surface[field])
            and any(surface[field].get(key) != generic[field].get(key) for key in ("minimum", "maximum", "default", "const"))
        }
        rows = {row[0].strip("`"): row for row in self._rows(section) if row[0].strip("`") in generic and row[0].strip("`") not in OPTIONAL_FIELDS}
        self.assertEqual(set(rows), differing)
        for field, row in rows.items():
            with self.subTest(field=field):
                spec = surface[field]
                if "const" in spec:
                    self.assertEqual(row[2].strip("`"), spec["const"])
                    self.assertEqual(row[3].strip("`"), spec["default"])
                else:
                    low, high = (float(value) for value in row[2].split("-"))
                    self.assertEqual((low, high), (spec["minimum"], spec["maximum"]))
                    self.assertEqual(float(row[3]), spec["default"])

    def test_the_quoted_footprint_figures(self) -> None:
        prose = " ".join((self.ROOT / "docs" / "API.md").read_text(encoding="utf-8").split())
        found = re.findall(
            r"Column fan-out below the field shrinks from ([\d.]+) mm \(two lanes at 60 degrees\) to ([\d.]+) mm, the Row channel from "
            r"([\d.]+) to ([\d.]+) mm, and every other margin from ([\d.]+) to ([\d.]+) mm", prose,
        )
        self.assertEqual(len(found), 1)
        request = {"matrix": _square(16, 32, 2.0), "routing": TIGHT}
        generic = field_footprint(check_design(request)["design"], load_profile())
        surface = field_footprint(check_design(dict(request, template_id=SURFACE))["design"], load_profile(SURFACE))
        quoted = tuple(float(value) for value in found[0])
        measured = (generic["column"]["bottom"], surface["column"]["bottom"], generic["row"]["left"], surface["row"]["left"])
        self.assertEqual(quoted[:4], tuple(round(value, 1) for value in measured))
        self.assertEqual(quoted[4:], (generic["column"]["top"], surface["column"]["top"]))
        layout = " ".join((self.ROOT / "docs" / "LAYOUT_SCHEMA.md").read_text(encoding="utf-8").split())
        self.assertIn(f"{round(surface['column']['bottom'], 1)} mm below the field for 16 x 32 taxels at 2 mm with 0.2032 mm bundles "
                      f"instead of {round(generic['column']['bottom'], 1)} mm with two lanes at 60 degrees", layout)
        lane = row_plan(check_design(dict(request, template_id=SURFACE))["design"], load_profile(SURFACE))["lanes"][0]
        self.assertIn(f"edge ({lane:g} mm at 0.1016 mm traces)", layout)
        # The Row field start of 64 rows per bundle pitch, on both templates.
        found = re.findall(
            r"For 64 rows the field starts ([\d.]+) mm above the tail root with ([\d.]+) mm bundles, ([\d.]+) mm with ([\d.]+) mm, "
            r"([\d.]+) mm with ([\d.]+) mm, ([\d.]+) mm with ([\d.]+) mm and ([\d.]+) mm with ([\d.]+) mm bundles "
            r"\(generic: ([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+) and ([\d.]+) mm\)", layout,
        )
        self.assertEqual(len(found), 1)
        values = [float(value) for value in found[0]]
        routings = {0.2032: (0.1016, 0.1016), 0.254: (0.127, 0.127), 0.4: (0.2, 0.2), 0.4999: (0.254, 0.2459), 0.5: (0.254, 0.246)}
        self.assertEqual(values[1:10:2], list(routings))
        for index, (trace, space) in enumerate(routings.values()):
            starts = []
            for template in (SURFACE, GENERIC):
                design = check_design({"template_id": template, "matrix": _square(64, 8, 2.0), "connector": {"row_pins": 64},
                                       "routing": {"trace_width_mm": trace, "trace_space_mm": space}})["design"]
                starts.append(row_plan(design, load_profile(template))["active"][1])
            self.assertEqual((values[2 * index], values[10 + index]), tuple(starts))
            self.assertLess(starts[0], starts[1])

    def test_the_layout_schema_surface_profile_table(self) -> None:
        text = (self.ROOT / "docs" / "LAYOUT_SCHEMA.md").read_text(encoding="utf-8")
        rows = self._rows(self._section(text, "## Surface template profile (`jlc-fpc-surface-v1`)"))
        surface = load_profile(SURFACE)
        listed = {}
        for row in rows:
            section, _, key = row[0].strip("`").partition(".")
            value = surface[section][key]
            listed[f"{section}.{key}"] = row[1]
            with self.subTest(key=row[0]):
                self.assertEqual(row[1], value if isinstance(value, str) else repr(value) if isinstance(value, float) else str(value))
        self.assertEqual(set(listed), SURFACE_PROFILE_CHANGES - {"id", "revision", "description", "template_id", "sources.surface_template"})


if __name__ == "__main__":
    unittest.main()
