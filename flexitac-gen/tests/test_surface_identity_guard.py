"""Unmasked surface designs keep their build identity and geometry (masked-field P0 guard).

The masked taxel field (``matrix.mask``, claude/specs/masked-field/PLAN.md)
adds an optional field, identity extras and masked constructions to the
surface template (``surface_matrix_v1``).  A surface design without a mask
must not change at all: not its design or build hash, not one byte of its
boards (geometry, DRC records, previews), not its manifest and not its
validation report.  ``test_generic_identity_guard`` does the same for the
generic template; this guard pins the 85 seeded surface requests of the
masked-field design workflow's contract probe (rows and columns 1-64,
pitches, fills, the three routings, every tail side, role mappings, channel
orders, connector sizes; tails from 7.5 mm) and a few fixed requests of its
own (aliases, a partial and an off-grid request, rejected designs and an
oversize one, whose size advice runs the planners).

``tests/fixtures/surface_identity_baseline.json`` was written by this module
(``python3 -B tests/test_surface_identity_guard.py --write-fixture``) from
the working tree of 2026-10-21 before the masked field: branch
fpc-customizer-audit-fixes at 858064a plus the uncommitted CAD-mode work
(the plan asks for a baseline from a commit; none was approved when it was
written, so the working tree is the baseline; the CAD-mode commits made later
that day, up to 78daa9d, hold that tree's code and tests unchanged).  Its
first 85 entries equal the contract probe's own snapshot, taken before any
mask work.  It must not be rewritten to make a failure pass: a difference
here means an unmasked surface build changed.  A deliberate surface change (which bumps the
template version) rewrites it from the reviewed engine.

It was rewritten by claude/specs/masked-field/P5-diagonal-bus.md section 23
(2026-10-25): the surface profile's maximum tail length 80 -> 200 mm (its
file hash ``SURFACE_PROFILE_FILE_SHA256`` re-pinned).  The profile's
canonical digest is part of every surface build id, so all 92 entries
changed their build ids and manifests, and the one refused for a 7.0 mm tail
its validation report (the E_TAIL_LENGTH message names the range 7.5-200
mm); every verdict, error code and board (layout digest) held.

It was rewritten by the profile revision 2026-10-29 (the gold-finger
thickness ordered in total and the coverlay windows against JLC's general
20 mm for one opening: two sources, a coverlay and an order value, the file
hash re-pinned): all entries changed their build ids and manifests; every
verdict, error code, board (layout digest) and validation report held.

It was rewritten by the user's decision of 2026-11-06 ("默认的pitch/trace大小,
现在都是0.7,直接都改成0.5": the default fill, electrode width / pitch, 0.7 ->
0.5, so the default electrodes 1.4 -> 1.0 mm at the 2 mm pitch).  The 10
requests that leave the electrode widths to the default (the probe's four
partial ones, this guard's two partial ones, its three rejected ones and its
oversize one) changed their designs, build ids and manifests, the 6 built ones
their layout digests and the oversize one its validation report (E_BOARD_SIZE quotes the outline's
size); every verdict and error code held.  The 82 others kept their records
byte for byte.

It was rewritten by the profile revision 2026-11-06 (the order: JLC's 2-layer
0.2 mm FPC, the bottom copper empty; the FlexiTac fabrication guide cited and
JLC's 2-layer thicknesses, the file hash re-pinned): all 92 entries changed
their build ids and manifests (of a manifest its build id, build digest,
profile revision and profile digest alone); every design, verdict, error code,
board (layout digest) and validation report held.

It was rewritten by the profile revision 2026-11-06b (the user's later decision
of 2026-11-06, "建议把补强改成 0.1 mm" -> "好的": the PI stiffener 0.225 -> 0.1
mm, the 2-layer 0.2 mm FPC + 0.1 mm the 0.3 mm gold fingers by JLC's rule; the
file hash re-pinned): all 92 entries changed their build ids and manifests,
and the 81 built ones their layout digests (each board carries the stiffener's
thickness, in ``fpc.stackup`` and its ``layers.bottom_stiffener``; with the
0.225 mm put back, tests/defaults_of_before.py ``stiffener``, every layout is
the one of before); every design, verdict, error code and validation report
held.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import unittest
from pathlib import Path
from typing import Any

from engine import check_design, generate_design

try:
    from test_generic_identity_guard import _pitch, _width, record
except ImportError:  # run as a package
    from tests.test_generic_identity_guard import _pitch, _width, record

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "surface_identity_baseline.json"
SURFACE_PROFILE = Path(__file__).resolve().parents[1] / "profiles" / "jlc_fpc_surface_v1.json"
# sha256 of the surface profile file's bytes (its canonical-JSON digest is in every surface build id).
SURFACE_PROFILE_FILE_SHA256 = "1ad3af57fdf5d243ffed6232ad47a0fdf898ad0f1957c9ffeebb4450694107af"
SURFACE = "surface_matrix_v1"
SEED = 20261020
RANDOM_COUNT = 80

_SIDES = ("bottom", "top", "left", "right")
_OPPOSITE = {"bottom": "top", "top": "bottom", "left": "right", "right": "left"}


def _random_request(rng: random.Random) -> dict[str, Any]:
    rows = rng.choice((1, 2, 64, rng.randint(1, 64), rng.randint(1, 24)))
    columns = rng.choice((1, 32, 64, rng.randint(1, 64), rng.randint(1, 32)))
    pitch_x = _pitch(rng)
    pitch_y = pitch_x if rng.random() < 0.5 else _pitch(rng)
    routing = rng.choice(((0.1016, 0.1016), (0.127, 0.127), (0.254, 0.246)))
    row_side = rng.choice(_SIDES)
    return {
        "schema_version": "tactile-fpc-design/v1", "template_id": SURFACE,
        "matrix": {"rows": rows, "columns": columns, "pitch_x_mm": pitch_x, "pitch_y_mm": pitch_y,
                   "taxel_width_mm": _width(rng, pitch_x), "taxel_height_mm": _width(rng, pitch_y)},
        "tail": {"top_length_mm": rng.choice((7.5, 12.0, round(rng.uniform(7.5, 80.0), 3))),
                 "bottom_length_mm": rng.choice((7.5, 12.0, round(rng.uniform(7.5, 80.0), 3))),
                 "row_side": row_side, "column_side": rng.choice((row_side, _OPPOSITE[row_side]))},
        "connector": {"row_pins": rng.choice((None, rng.randint(rows, 64))), "column_pins": rng.choice((None, rng.randint(columns, 64)))},
        "role_mapping": rng.choice(({"top": "rows", "bottom": "columns"}, {"top": "columns", "bottom": "rows"})),
        "channel_order": {"rows": rng.choice(("ascending", "descending")), "columns": rng.choice(("ascending", "descending"))},
        "routing": {"trace_width_mm": routing[0], "trace_space_mm": routing[1]},
    }


def requests(seed: int = SEED, count: int = RANDOM_COUNT) -> list[dict[str, Any]]:
    """The guarded requests: the contract probe's 5 fixed and ``count`` seeded ones, then this guard's fixed ones."""

    probe: list[dict[str, Any]] = [
        {"template_id": SURFACE},
        {"template_id": SURFACE, "matrix": {"rows": 16, "columns": 64}},
        {"template_id": SURFACE, "matrix": {"rows": 1, "columns": 1}},
        {"template_id": SURFACE, "matrix": {"rows": 64, "columns": 64, "pitch_x_mm": 0.6, "pitch_y_mm": 0.6, "taxel_width_mm": 0.35,
                                            "taxel_height_mm": 0.35},
         "routing": {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016}},
        {"template_id": SURFACE, "matrix": {"rows": 8, "columns": 8}, "connector": {"row_pins": 16, "column_pins": 32}},
    ]
    rng = random.Random(seed)
    probe += [_random_request(rng) for _ in range(count)]
    own: list[dict[str, Any]] = [
        # The browser's flat alias form on the surface template.
        {"template_id": SURFACE, "name": "Surface 16x48", "rows": 16, "columns": 48, "taxel_size_mm": 1.2, "tail_length_mm": 20,
         "connector_side": "left", "row_fpc_position": "bottom", "scan_order": "reverse"},
        # Partial and off-grid requests, rounded to the 1e-6 mm layout grid.
        {"template_id": SURFACE, "matrix": {"columns": 40}, "routing": {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016}},
        {"template_id": SURFACE, "project_name": "  Surface 9x58  ", "matrix": {"rows": 9, "columns": 58, "pitch_x_mm": 2.0000003},
         "tail": {"top_length_mm": 30.0000004}},
        # Rejected designs: the generic tail minimum, too many columns, a wrong kind.
        {"template_id": SURFACE, "tail": {"bottom_length_mm": 7.0}},
        {"template_id": SURFACE, "matrix": {"columns": 65}},
        {"template_id": SURFACE, "matrix": {"rows": "12"}},
        # Oversize: the size advice (bisection through the planners) is in the validation report.
        {"template_id": SURFACE, "matrix": {"rows": 64, "columns": 8, "pitch_y_mm": 8.0, "taxel_height_mm": 4.0}},
    ]
    return probe + own


def write_fixture() -> None:
    entries = [{"request": request, "expected": record(generate_design(request))} for request in requests()]
    document = {
        "format": "tactile-fpc-surface-guard/v1",
        "written_from": "engine of the profile revision 2026-11-06b (the PI stiffener 0.225 -> 0.1 mm, the 2-layer 0.2 mm FPC + 0.1 mm the "
                        "0.3 mm gold fingers by JLC's rule: in every build id and every built board's layout), 2026-11-06; before it, "
                        "the profile revision 2026-11-06 (the order: JLC's 2-layer 0.2 mm FPC, the bottom copper empty, "
                        "in every build id), 2026-11-06; before it, the user's decision of 2026-11-06 (the default fill 0.7 -> 0.5: "
                        "the default electrodes 1.4 -> 1.0 mm, in the requests that leave them to the default), 2026-11-06; before it, the profile revision 2026-10-29 "
                        "(the gold-finger thickness order option and the coverlay-window "
                        "notes, in every build id), 2026-10-29; before it, P5-diagonal-bus.md section 23's (the surface profile's tails "
                        "to 200 mm), 2026-10-25, and before that the "
                        "working tree of 2026-10-21 (858064a plus the uncommitted CAD-mode work), before the masked field",
        "seed": SEED,
        "random_count": RANDOM_COUNT,
        "profile_file_sha256": SURFACE_PROFILE_FILE_SHA256,
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


class SurfaceIdentityGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.results = [generate_design(entry["request"]) for entry in cls.fixture["entries"]]

    def test_the_surface_profile_file_is_unchanged(self) -> None:
        self.assertEqual(hashlib.sha256(SURFACE_PROFILE.read_bytes()).hexdigest(), SURFACE_PROFILE_FILE_SHA256)
        self.assertEqual(self.fixture["profile_file_sha256"], SURFACE_PROFILE_FILE_SHA256)

    def test_the_fixture_holds_the_seeded_requests(self) -> None:
        # The fixture is this module's output, not a hand-edited list.
        self.assertEqual([entry["request"] for entry in self.fixture["entries"]], requests(self.fixture["seed"], self.fixture["random_count"]))

    def test_every_unmasked_surface_request_keeps_its_build(self) -> None:
        for index, (entry, result) in enumerate(zip(self.fixture["entries"], self.results)):
            with self.subTest(index=index, build_id=entry["expected"]["build_id"]):
                self.assertEqual(record(result), entry["expected"])

    def test_check_design_gives_the_same_identities(self) -> None:
        for index, entry in enumerate(self.fixture["entries"][:40]):
            with self.subTest(index=index):
                checked = check_design(entry["request"])
                self.assertEqual(checked["identity"]["build_id"], entry["expected"]["build_id"])
                self.assertEqual(checked["design"]["template_id"], SURFACE)
                self.assertNotIn("mask", checked["design"]["matrix"])
                self.assertNotIn("mask", checked["identity"])

    def test_the_fixture_covers_the_surface_input_space(self) -> None:
        designs = [result["design"] for result in self.results]
        expected = [entry["expected"] for entry in self.fixture["entries"]]
        self.assertGreaterEqual(len(designs), 92)
        self.assertGreaterEqual(sum(item["ok"] for item in expected), 80)
        codes = {code for item in expected for code in item["error_codes"]}
        self.assertLessEqual({"E_BOARD_SIZE", "E_TAIL_LENGTH", "E_COLUMNS_RANGE", "E_ROWS_INTEGER"}, codes)
        self.assertEqual({design["template_id"] for design in designs}, {SURFACE})
        self.assertEqual({design["tail"]["row_side"] for design in designs}, set(_SIDES))
        self.assertTrue(any(design["tail"]["row_side"] != design["tail"]["column_side"] for design in designs))
        self.assertEqual({design["role_mapping"]["top"] for design in designs}, {"rows", "columns"})
        self.assertLessEqual({1, 64}, {design["matrix"]["rows"] for design in designs})
        self.assertLessEqual({1, 32, 64}, {design["matrix"]["columns"] for design in designs})
        self.assertTrue(any(design["connector"]["row_pins"] is not None for design in designs))
        routings = {(design["routing"]["trace_width_mm"], design["routing"]["trace_space_mm"]) for design in designs}
        self.assertLessEqual({(0.1016, 0.1016), (0.127, 0.127), (0.254, 0.246)}, routings)


if __name__ == "__main__":
    if "--write-fixture" in sys.argv[1:]:
        write_fixture()
    else:
        unittest.main()
