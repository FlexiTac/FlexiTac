"""Generic designs keep their build identity and geometry (C-D10 byte-identity guard).

The surface template (``surface_matrix_v1``, 2026-10-20) adds geometry
policies and a second profile to the engine.  Designs of the generic template
(``generic_matrix_v1``) must not change at all: not their design or build
hash, not one byte of their boards (geometry, DRC records, previews), not
their manifest and not their validation report.  ``test_golden_default``
pins the default build only; this guard pins about 200 seeded generic
requests across the input space (rows 1-64, columns 1-32 on one and two
fan-out lanes, pitches, fills, routings, tail sides, role mappings, channel
orders, connector sizes, aliases, partial requests and rejected designs).

``tests/fixtures/generic_builds.json`` was written by this module
(``python3 -B tests/test_generic_identity_guard.py --write-fixture``) from
the engine at commit 858064a, before the surface template existed.  It must
not be rewritten to make a failure pass: a difference here means a generic
build changed.  A deliberate generic change (which bumps a version and the
golden values) rewrites it from the reviewed engine.

It was rewritten once, deliberately, by claude/specs/masked-field/
P5-diagonal-bus.md section 18 (2026-10-24): the generic template builds the
diagonal Row bus with ``both`` by default (``channel``, the straight Row
channel, for opposite tails or a single row or column), so the generic build
ids, the boards of the bus designs and the validation reports (the defaulted
``routing.row_sides``) changed.  The records of before are kept in
``tests/fixtures/generic_builds_straight_channel.json`` (the fixture as
written from 858064a, which held through 8a4b2f1): ``ChannelIdentityTests``
builds every one of those requests with ``routing.row_sides`` ``channel`` and
requires the same verdict, error codes, boards (layout digest) and
validation report, and ``tests/fixtures/generic_channel_exports.json`` (written
from 8a4b2f1 by the same requests' exports) every archive member but the
identity carriers (the manifests, the design and the nested archives; the
build id masked in the others): the straight channel is byte for byte the
generic geometry of before, only its identity moved.

It was rewritten again by P5-diagonal-bus.md section 20 (2026-10-24,
``diagonal-bus/8``): a bus design on the generic template is built with CAD
mode's rule set (the surface profile: tails of 7.5 mm or more, up to 64
columns, the 0.5 mm field margin) and construction (the Column V capped at
80 degrees, one outline down to the tails' roots), so the bus requests of the
guard changed their build ids, manifests and validation reports, and the ones
with a 7.0 mm tail are refused (E_TAIL_LENGTH); the straight-channel requests
kept their records byte for byte (the generic profile, its default bottom
tail 7.0 mm).

It was rewritten by P5-diagonal-bus.md section 23 (2026-10-25): the surface
profile's maximum tail length 80 -> 200 mm.  The surface profile's canonical
digest is part of every build id of a bus design on the generic template, so
the 75 bus requests of the guard changed their build ids and manifests, and
the 35 of them refused for a 7.0 mm tail their validation reports (the
E_TAIL_LENGTH message names the range 7.5-200 mm); their verdicts, error
codes and boards (layout digests) held.  The 125 straight-channel and other
requests kept their records byte for byte (the generic profile is unchanged).

It was rewritten by P5-diagonal-bus.md section 24 (2026-10-25,
``diagonal-bus/9``: convex sides, each side's dents from the tip corner down
to its widest point bridged by its hull).  The construction's version is part
of every bus design's build identity and of its layout
(``construction.row_bus.kind``), so the 75 bus requests changed their build
ids, manifests and layout digests (the built ones' outlines where a side has
such a dent); their verdicts and error codes held.  The 125 straight-channel
and other requests kept their records byte for byte.

It was rewritten by P5-diagonal-bus.md section 27 (2026-10-27,
``diagonal-bus/10``: the Row tail centred on the field in every side mode,
the user's request "some tails are not within the sensor's width").  The 75
bus requests changed their build ids and manifests, the 37 built ones their
layout digests (their Row tails, fans and outlines) and the one refused for
its size (64 x 23 at 2.831 x 9.895 mm) its validation report (E_BOARD_SIZE
quotes the outline's size); their verdicts and error codes held.  The 125
straight-channel and other requests kept their records byte for byte.

It was rewritten by P5-diagonal-bus.md section 27.7 (2026-10-27, the user's
decision "矩形模式默认 tail 长度是否改成 12/12 ：可以；可以加个门槛": the rectangular mode's
default tails 12 / 12 mm, the bottom tail 7.5 -> 12 mm, so the stacked tails
end together).  The 14 bus requests that leave the bottom tail to the default
(``default_design()`` itself, now naming 12 mm, the empty request and the
partial ones without a tail section) changed their designs, build ids and
manifests, the 12 built ones their layout digests (the bottom board's tail
4.5 mm longer) and the one refused for its size its validation report
(E_BOARD_SIZE quotes the outline's size); their verdicts and error codes
held.  The 186 others (the straight channel's 7.0 mm default, every request
naming its bottom tail) kept their records byte for byte.

It was rewritten by P5-diagonal-bus.md section 27.8 (2026-10-28,
``diagonal-bus/11``: one side's flank without lanes convex from the field's
outline corner down to the tail, the multi-gripper video's notch).  The 75
bus requests changed their build ids and manifests, the 37 built ones their
layout digests; every one of those 37 is the diagonal Row bus with both
sides, whose flanks have lanes, so with the version string put back each
layout is byte for byte the one of before (only
``construction.row_bus.kind`` moved); their verdicts, error codes and
validation reports held.  The 125 straight-channel and other requests kept
their records byte for byte.

It was rewritten by the profile revision 2026-10-29 of both profiles (the
gold-finger thickness ordered in total, from JLC's gold-finger stiffener
ordering guide, and the coverlay windows against JLC's general 20 mm for one
opening, from its FPC design rules: two sources, a coverlay and an order
value).  Both profiles' canonical digests are part of every build id, so the
requests changed their build ids and manifests; their verdicts, error codes,
boards (layout digests) and validation reports are checked below to have
held.  ``tests/fixtures/generic_channel_exports.json`` was rewritten in its
``ORDER_NOTES.txt`` and ``profile.json`` digests only (the two order notes
and the profile they quote); every other member kept its bytes.

It was rewritten by the user's decision of 2026-11-06 ("默认的pitch/trace大小,
现在都是0.7,直接都改成0.5": the default fill, electrode width / pitch, 0.7 ->
0.5, so the default electrodes 1.4 -> 1.0 mm at the 2 mm pitch).  The 6
requests that leave an electrode width to the default (``default_design()``
itself, now naming 1.0 mm, the empty request and four partial ones) changed
their designs, build ids and manifests, the 5 built ones their layout digests
and the one refused (its 1.9 mm Column electrode) nothing else; their
verdicts, error codes and validation reports held.  The 194 others kept their
records byte for byte.  ``ChannelIdentityTests`` builds the records of before
with the default electrodes of before (tests/defaults_of_before.py: 1.4 mm), so
the straight channel stays byte for byte the generic geometry of before.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import unittest
from pathlib import Path
from typing import Any

from engine import check_design, default_design, generate_design

try:
    import defaults_of_before
except ImportError:  # run as a package
    from tests import defaults_of_before

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "generic_builds.json"
# The records before section 18 (the straight Row channel everywhere) and the masked export members of 8a4b2f1.
CHANNEL_FIXTURE = FIXTURE.with_name("generic_builds_straight_channel.json")
CHANNEL_EXPORTS = FIXTURE.with_name("generic_channel_exports.json")
GENERIC_PROFILE = Path(__file__).resolve().parents[1] / "profiles" / "jlc_fpc_standard_v1.json"
# sha256 of the generic profile file's bytes (its canonical-JSON digest is in every build id).
GENERIC_PROFILE_FILE_SHA256 = "45805f86f365832038a97f59289f0fdbf242d35b77771ccdd9099a7a26ff10d7"
SEED = 20261020
RANDOM_COUNT = 188

_SIDES = ("bottom", "top", "left", "right")
_OPPOSITE = {"bottom": "top", "top": "bottom", "left": "right", "right": "left"}
_NAMES = (None, "Guard", "Finger pad", "触觉 sensor", "  spaced name  ", "x" * 80)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _width(rng: random.Random, pitch: float) -> float:
    """A legal electrode width at ``pitch`` (fill 0.2-0.95, at most pitch - 0.25)."""

    return round(min(max(0.1016, rng.uniform(0.2, 0.95) * pitch), pitch - 0.25), 4)


def _pitch(rng: random.Random) -> float:
    return round(rng.uniform(0.6, 3.5) if rng.random() < 0.75 else rng.uniform(0.6, 10.0), 3)


def _random_request(rng: random.Random, index: int) -> dict[str, Any]:
    rows = rng.choice((1, 2, 64, rng.randint(1, 64), rng.randint(1, 64), rng.randint(1, 24)))
    columns = rng.choice((1, 16, 17, 32, rng.randint(1, 32), rng.randint(1, 32)))
    pitch_x = _pitch(rng)
    pitch_y = pitch_x if rng.random() < 0.5 else _pitch(rng)
    routing = rng.choice(((0.1016, 0.1016), (0.127, 0.127), (0.254, 0.246), None))
    if routing is None:
        width = round(rng.uniform(0.1016, 0.254), 4)
        routing = (width, round(rng.uniform(0.1016, min(0.246, 0.5 - width)), 4))
    row_side = rng.choice(_SIDES)
    column_side = rng.choice((row_side, _OPPOSITE[row_side]))
    request: dict[str, Any] = {
        "schema_version": "tactile-fpc-design/v1",
        "template_id": "generic_matrix_v1",
        "matrix": {
            "rows": rows, "columns": columns, "pitch_x_mm": pitch_x, "pitch_y_mm": pitch_y,
            "taxel_width_mm": _width(rng, pitch_x), "taxel_height_mm": _width(rng, pitch_y),
        },
        "tail": {
            "top_length_mm": rng.choice((7.0, 80.0, round(rng.uniform(7.0, 80.0), 3))),
            "bottom_length_mm": rng.choice((7.0, 12.0, round(rng.uniform(7.0, 80.0), 3))),
            "row_side": row_side, "column_side": column_side,
        },
        "connector": {
            "row_pins": rng.choice((None, None, rng.randint(rows, 64))),
            "column_pins": rng.choice((None, None, rng.randint(columns, 64))),
        },
        "role_mapping": rng.choice(({"top": "rows", "bottom": "columns"}, {"top": "columns", "bottom": "rows"})),
        "channel_order": {"rows": rng.choice(("ascending", "descending")), "columns": rng.choice(("ascending", "descending"))},
        "routing": {"trace_width_mm": routing[0], "trace_space_mm": routing[1]},
    }
    name = rng.choice(_NAMES)
    if name is not None:
        request["project_name"] = name
    variant = rng.random()
    if variant < 0.08:
        # Partial request: the defaults fill the rest.
        for key in rng.sample(["tail", "connector", "role_mapping", "channel_order", "routing", "template_id", "schema_version"], 3):
            request.pop(key, None)
    elif variant < 0.12:
        # Off-grid values, rounded to the 1e-6 mm layout grid by the normalizer.
        request["matrix"]["pitch_x_mm"] = round(pitch_x + 3e-7, 9)
        request["tail"]["top_length_mm"] = round(request["tail"]["top_length_mm"] + 4e-7, 9)
    elif variant < 0.15:
        # Oversize: the size advice (bisection through the planners) is in the validation report.
        request["matrix"].update(rows=64, pitch_y_mm=8.0, taxel_height_mm=4.0)
    return request


def requests(seed: int = SEED, count: int = RANDOM_COUNT) -> list[dict[str, Any]]:
    """The guarded requests: fixed ones first, then ``count`` seeded random generic requests."""

    fixed: list[dict[str, Any]] = [
        default_design(),
        {},
        # The browser's flat alias form (the HTML form names).
        {"name": "Tactile FPC 12x32", "rows": 12, "columns": 32, "pitch_x_mm": 2, "pitch_y_mm": 2, "row_electrode_width_mm": 1.4,
         "column_electrode_width_mm": 1.4, "top_tail_length_mm": 12, "bottom_tail_length_mm": 7, "connector_side": "bottom",
         "row_fpc_position": "top", "scan_order": "forward"},
        {"rows": 16, "columns": 16, "taxel_size_mm": 1.2, "tail_length_mm": 20, "connector_side": "left", "row_fpc_position": "bottom",
         "scan_order": "reverse"},
        {"matrix": {"rows": 64, "columns": 32, "pitch_x_mm": 0.6, "pitch_y_mm": 0.6, "taxel_width_mm": 0.35, "taxel_height_mm": 0.35},
         "routing": {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016}},
        {"matrix": {"rows": 1, "columns": 1, "pitch_x_mm": 10, "pitch_y_mm": 10, "taxel_width_mm": 9.75, "taxel_height_mm": 9.75}},
        {"matrix": {"rows": 16, "columns": 32, "pitch_x_mm": 2, "pitch_y_mm": 2, "taxel_width_mm": 1.4, "taxel_height_mm": 1.4},
         "connector": {"row_pins": 16, "column_pins": 32}, "tail": {"top_length_mm": 20, "bottom_length_mm": 20}},
        {"matrix": {"columns": 17}, "connector": {"row_pins": 14}},
        {"matrix": {"rows": 32, "columns": 32, "pitch_x_mm": 2, "pitch_y_mm": 2}, "routing": {"trace_width_mm": 0.254, "trace_space_mm": 0.246}},
        {"matrix": {"rows": 64, "columns": 32, "pitch_x_mm": 7, "pitch_y_mm": 7, "taxel_width_mm": 5, "taxel_height_mm": 5}},
        {"matrix": {"rows": 3, "columns": 5}, "tail": {"row_side": "right", "column_side": "left"}},
        {"matrix": {"rows": 4, "columns": 4, "taxel_width_mm": 1.9}},
    ]
    rng = random.Random(seed)
    return fixed + [_random_request(rng, index) for index in range(count)]


def record(result: dict[str, Any]) -> dict[str, Any]:
    """What the guard freezes of one generate_design result: identity, layout, manifest and validation digests."""

    layout = {"format": result["derived_layout"]["format"], "units": result["derived_layout"]["units"], "boards": result["boards"]}
    return {
        "ok": result["ok"],
        "build_id": result["manifest"]["build_id"],
        "design_sha256": result["manifest"]["design_sha256"],
        "error_codes": sorted({issue["code"] for issue in result["validation"]["errors"]}),
        "layout_sha256": _sha256(layout),
        "manifest_sha256": _sha256(result["manifest"]),
        "validation_sha256": _sha256(result["validation"]),
    }


def write_fixture() -> None:
    entries = [{"request": request, "expected": record(generate_design(request))} for request in requests()]
    document = {
        "format": "tactile-fpc-generic-guard/v1",
        "written_from": "engine of the user's decision of 2026-11-06 (the default fill 0.7 -> 0.5: the default electrodes 1.4 -> 1.0 "
                        "mm, in the requests that leave them to the default), 2026-11-06; before it, the profile revision 2026-10-29 "
                        "(the gold-finger thickness order option and the coverlay-window "
                        "notes, in every build id), 2026-10-29; before it, P5-diagonal-bus.md section 27.8's (diagonal-bus/11: one side's "
                        "convex flank, in the generic bus's build ids and layouts), 2026-10-28, section 27.7's (the rectangular mode's default tails 12 / 12 "
                        "mm), section 27's (diagonal-bus/10: the Row tail centred on the field, in the "
                        "generic bus's build ids and layouts), section 24's (diagonal-bus/9: convex sides), section 23's (the surface profile's tails to 200 mm), section 20's (diagonal-bus/8: the generic bus built with CAD mode's "
                        "rule set and construction), section 18's (the diagonal Row bus the generic default) and "
                        "generic_builds_straight_channel.json",
        "seed": SEED,
        "random_count": RANDOM_COUNT,
        "profile_file_sha256": GENERIC_PROFILE_FILE_SHA256,
        "entries": entries,
    }
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with FIXTURE.open("w", encoding="utf-8") as handle:
        handle.write("{\n")
        for key in ("format", "written_from", "seed", "random_count", "profile_file_sha256"):
            handle.write(f"  {json.dumps(key)}: {json.dumps(document[key], ensure_ascii=True)},\n")
        handle.write('  "entries": [\n')
        lines = [f"    {json.dumps(entry, ensure_ascii=True, sort_keys=True, separators=(',', ':'))}" for entry in entries]
        handle.write(",\n".join(lines))
        handle.write("\n  ]\n}\n")
    print(f"wrote {len(entries)} entries to {FIXTURE}")


class GenericIdentityGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.results = [generate_design(entry["request"]) for entry in cls.fixture["entries"]]

    def test_the_generic_profile_file_is_unchanged(self) -> None:
        self.assertEqual(hashlib.sha256(GENERIC_PROFILE.read_bytes()).hexdigest(), GENERIC_PROFILE_FILE_SHA256)
        self.assertEqual(self.fixture["profile_file_sha256"], GENERIC_PROFILE_FILE_SHA256)

    def test_the_fixture_holds_the_seeded_requests(self) -> None:
        # The fixture is this module's output, not a hand-edited list.
        self.assertEqual([entry["request"] for entry in self.fixture["entries"]], requests(self.fixture["seed"], self.fixture["random_count"]))

    def test_every_generic_request_keeps_its_build(self) -> None:
        for index, (entry, result) in enumerate(zip(self.fixture["entries"], self.results)):
            with self.subTest(index=index, build_id=entry["expected"]["build_id"]):
                self.assertEqual(record(result), entry["expected"])

    def test_check_design_gives_the_same_identities(self) -> None:
        for index, entry in enumerate(self.fixture["entries"][:40]):
            with self.subTest(index=index):
                checked = check_design(entry["request"])
                self.assertEqual(checked["identity"]["build_id"], entry["expected"]["build_id"])
                self.assertEqual(checked["design"]["template_id"], "generic_matrix_v1")

    def test_the_fixture_covers_the_generic_input_space(self) -> None:
        designs = [result["design"] for result in self.results]
        expected = [entry["expected"] for entry in self.fixture["entries"]]
        self.assertGreaterEqual(len(designs), 200)
        # Section 20: the bus requests with a 7.0 mm tail are refused (CAD mode's rule set, tails of 7.5 mm or more): 151 of
        # 200 build, 37 of them the bus.
        self.assertGreaterEqual(sum(item["ok"] for item in expected), 150)
        self.assertGreaterEqual(sum(item["ok"] for item, design in zip(expected, designs) if design["routing"]["row_sides"] == "both"), 30)
        self.assertIn("E_BOARD_SIZE", {code for item in expected for code in item["error_codes"]})
        self.assertEqual({design["tail"]["row_side"] for design in designs}, set(_SIDES))
        self.assertTrue(any(design["tail"]["row_side"] != design["tail"]["column_side"] for design in designs))
        self.assertEqual({design["role_mapping"]["top"] for design in designs}, {"rows", "columns"})
        self.assertEqual({design["channel_order"]["rows"] for design in designs} | {design["channel_order"]["columns"] for design in designs},
                         {"ascending", "descending"})
        self.assertEqual({design["matrix"]["rows"] for design in designs} >= {1, 64}, True)
        self.assertEqual({design["matrix"]["columns"] for design in designs} >= {1, 16, 17, 32}, True)
        self.assertTrue(any(design["connector"]["row_pins"] is not None for design in designs))
        self.assertTrue(any(design["connector"]["column_pins"] is not None for design in designs))
        # Section 18: the default Row traces of the generic template, the bus (both) and the channel (opposite tails, strips).
        self.assertEqual({design["routing"]["row_sides"] for design in designs}, {"both", "channel"})
        routings = {(design["routing"]["trace_width_mm"], design["routing"]["trace_space_mm"]) for design in designs}
        self.assertLessEqual({(0.1016, 0.1016), (0.127, 0.127), (0.254, 0.246)}, routings)


def _channel(request: Any) -> Any:
    """A guarded request with ``routing.row_sides`` ``channel`` (where its routing is an object or absent)."""

    request = json.loads(json.dumps(request))
    if isinstance(request, dict):
        routing = request.get("routing")
        if routing is None:
            request["routing"] = {"row_sides": "channel"}
        elif isinstance(routing, dict):
            routing["row_sides"] = "channel"
    return request


def _masked(data: bytes, manifest: dict[str, Any]) -> bytes:
    for key in ("build_id", "build_sha256", "design_sha256"):
        data = data.replace(manifest[key].encode(), f"<{key}>".encode())
    return data


class ChannelIdentityTests(unittest.TestCase):
    """The straight Row channel under ``routing.row_sides`` ``channel`` is the generic geometry of before section 18."""

    def test_every_request_of_before_keeps_its_boards_and_report_on_the_channel(self) -> None:
        fixture = json.loads(CHANNEL_FIXTURE.read_text(encoding="utf-8"))
        # The same requests but the first, default_design(), which now names its Row traces (routing.row_sides both), its
        # 12 mm bottom tail (section 27.7; their rule set's 7.5 mm from section 20) and its 1.0 mm electrodes (the user's
        # decision of 2026-11-06, the default fill 0.5).
        guarded = requests(fixture["seed"], fixture["random_count"])
        self.assertEqual([entry["request"] for entry in fixture["entries"]][1:], guarded[1:])
        first = json.loads(json.dumps(guarded[0]))
        self.assertEqual(first["routing"].pop("row_sides"), "both")
        self.assertEqual(first["tail"]["bottom_length_mm"], 12.0)
        first["tail"]["bottom_length_mm"] = 7.0
        self.assertEqual((first["matrix"]["taxel_width_mm"], first["matrix"]["taxel_height_mm"]), (1.0, 1.0))
        first["matrix"].update(taxel_width_mm=1.4, taxel_height_mm=1.4)
        self.assertEqual(fixture["entries"][0]["request"], first)
        for index, entry in enumerate(fixture["entries"]):
            with self.subTest(index=index, build_id=entry["expected"]["build_id"]), defaults_of_before.electrodes():
                found = record(generate_design(_channel(entry["request"])))
                for key in ("ok", "error_codes", "layout_sha256", "validation_sha256"):
                    self.assertEqual(found[key], entry["expected"][key], key)
                if found["ok"]:
                    # The design names the channel, so its identity moved (once, with section 18).
                    self.assertNotEqual(found["build_id"], entry["expected"]["build_id"])

    def test_the_channel_exports_keep_their_layers(self) -> None:
        import io
        import zipfile

        from exporters import build_exports

        fixture = json.loads(CHANNEL_EXPORTS.read_text(encoding="utf-8"))
        self.assertEqual(len(fixture["entries"]), 8)
        for entry in fixture["entries"]:
            with self.subTest(request=entry["request"]), defaults_of_before.electrodes():
                result = generate_design(_channel(entry["request"]))
                expected = entry["expected"]
                self.assertEqual(result["ok"], expected["ok"])
                layout = {"format": result["derived_layout"]["format"], "units": "mm", "boards": result["boards"]}
                self.assertEqual(_sha256(layout), expected["layout_sha256"])
                self.assertEqual(_sha256(result["validation"]), expected["validation_sha256"])
                exports = build_exports(result)
                members = {}
                for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip", "project_review_bundle_zip"):
                    with zipfile.ZipFile(io.BytesIO(exports[key])) as archive:
                        for name in archive.namelist():
                            if not (name.endswith(".zip") or name in ("manifest.json", "design.json")):
                                members[f"{key}/{name}"] = hashlib.sha256(_masked(archive.read(name), result["manifest"])).hexdigest()
                self.assertEqual(members, expected["members"])
                self.assertTrue(any(name.endswith(".GTL") for name in members) and any(name.endswith("netlist.ipc") for name in members))


if __name__ == "__main__":
    if "--write-fixture" in sys.argv[1:]:
        write_fixture()
    else:
        unittest.main()
