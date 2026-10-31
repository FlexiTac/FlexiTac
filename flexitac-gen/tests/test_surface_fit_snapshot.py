"""The raster search's rectangles keep their builds (masked-field P0 snapshot; Whole board's since section 26.16).

The masked taxel field (claude/specs/masked-field/PLAN.md) adds a ``shape``
option to the fit (P4): ``fill`` searches masked fields, ``rectangle`` must
stay today's search byte for byte.  This snapshot pins today's fit, with
today's options and ``shape: rectangle`` (given explicitly: ``fill`` is the
default from phase P4b on), on the soft finger through its mount end (the replica, and
the real mesh when the ``asset/`` meshes are present; each also with
``template: generic``, the rectangular mode's 49x7), the crank tip pad (when
``asset/`` is present) and three synthetic plates (a right triangle, an
equilateral triangle and a disk; ``max_taxels`` once on the right triangle):
per proposal its rank, build id, metrics, the digest of its outlines on the
chart (``outlines_uv``) and the field frame of its placement.  A later
phase may add metric keys (the masked field's ``positions``, ``sampled``);
every key recorded here keeps its value.

``tests/fixtures/surface_fit_rectangle_snapshot.json`` was written by this
module (``python3 -B tests/test_surface_fit_snapshot.py --write-fixture``)
from the working tree of 2026-10-21 before the masked field: branch
fpc-customizer-audit-fixes at 858064a plus the uncommitted CAD-mode work
(the plan asks for a baseline from a commit; none was approved when it was
written, so the working tree is the baseline; the CAD-mode commits made later
that day, up to 78daa9d, hold that tree's code and tests unchanged).  The
generic-template and real-mesh soft-finger cases were added the same day by
running this module in a copy of the frozen pre-mask tree, which reproduced
every other case byte for byte.  It must not be rewritten to make a failure
pass.

The generic template's build ids changed once, deliberately, with the
diagonal Row bus as that template's default (claude/specs/masked-field/
P5-diagonal-bus.md section 18): a generic proposal fits the whole stack with
the straight Row channel, so its design now names ``routing.row_sides``
``channel`` (absent, the generic template builds the bus), which is part of
the hashed design.  ``GENERIC_BUILD_IDS`` maps the fixture's generic build
ids to today's; every other recorded value of those proposals (metrics,
outlines, placement) holds as written.

The surface template's build ids changed once, deliberately, with
P5-diagonal-bus.md section 23 (2026-10-25): the surface profile's maximum
tail length 80 -> 200 mm, and the profile's canonical digest is part of every
surface build id.  ``SURFACE_BUILD_IDS`` maps the fixture's surface build ids
to today's (31 ids, measured on Python 3.9.6 and 3.12, any hash seed); every
other recorded value of those proposals (ranks, metrics, outlines, placement)
holds as written, and the generic-template cases (the standard profile) keep
theirs.  The profile revision 2026-10-29 (the gold-finger thickness order
option and the coverlay-window notes) moved them again: the mapping's values
are today's ids (31, every other recorded value as written).

Since P5-diagonal-bus.md section 26.16 (the user's decision of 2026-10-26:
what CAD mode generates depends only on the selected area) CAD mode has no
``shape: rectangle`` and no generic template, so the fits this snapshot was
written from are no longer requests.  The raster search they ran
(:func:`surface.fit.search` and :func:`surface.fit.realize`) stays: Whole
board (``containment: board``, :mod:`surface.fill`) merges its rectangles
with the masked fields.  So the snapshot now pins those rectangles among the
whole-board fit's proposals (the same options with ``containment: board``
and 20 proposals): every recorded rectangle is proposed, in its recorded
order, with its build id (as mapped above), its recorded metrics, its
outlines and its field frame (2026-10-27: all five of every case, each
after the case's masked fields).  The generic
template's cases stay in the fixture as written; they are not run.  The
fixture is not rewritten (nothing here writes it any more).
"""

from __future__ import annotations

import hashlib
import json
import math
import unittest
from pathlib import Path
from typing import Any

from surface import fit, select
from surface.mesh import read_stl

try:
    import surface_fixtures as F
except ImportError:  # run as a package
    from tests import surface_fixtures as F

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "surface_fit_rectangle_snapshot.json"
ASSETS = Path(__file__).resolve().parents[1] / "asset"
CRANK = ASSETS / "crank_gripper" / "tip_left.stl"
SOFT_FINGER = ASSETS / "soft_gripper_finger.stl"
# The soft finger's mount end: a point on its x = 0 face and the base point.
SOFT_SEED = (0.0, -12.9, -62.7)
SOFT_BASE = {"point_xyz": [0.0, -12.9, -3.0]}
# The cases that need the asset/ meshes.
ASSET_CASES = {"crank_tip_pad", "soft_finger_asset_mount_end", "soft_finger_asset_mount_end_generic"}
# The generic template's cases (CAD options before section 26.16): kept in the fixture, not run.
GENERIC_CASES = {"soft_finger_mount_end_generic", "soft_finger_asset_mount_end_generic"}
# The fit the rectangles are found in since section 26.16: Whole board, enough proposals to list them after the masks.
BOARD = {"containment": "board", "proposals": 20}
# The generic-template proposals' build ids before section 18 -> with routing.row_sides "channel" (the module docstring).
GENERIC_BUILD_IDS = {
    "surface-49x7-cd15e8dd7eef": "surface-49x7-2276551269ff",
    "surface-48x7-951d1cf52383": "surface-48x7-7803555d5f7a",
    "surface-47x7-30264d0571d3": "surface-47x7-38b9a4a08aca",
    "surface-47x7-055425f22794": "surface-47x7-ae3b863e36dd",
    "surface-46x7-1d42b9f518ab": "surface-46x7-eb5c50239698",
    "surface-45x7-8d62cf1b9244": "surface-45x7-10987e34cbe9",
}
# The surface-template proposals' build ids before section 23 -> today's: with the surface profile's 200 mm tails (the
# module docstring), and again with the profile revision 2026-10-29 (the gold-finger thickness order option and the
# coverlay-window notes: the profile's digest moves every surface build id; every other recorded value holds).
SURFACE_BUILD_IDS = {
    "surface-44x8-6bd1c5396ff8": "surface-44x8-31192a48fa1b",
    "surface-50x7-e8798c3ba815": "surface-50x7-f3119e1c4b9c",
    "surface-43x8-4ec47321d5cc": "surface-43x8-bb37b5684eff",
    "surface-49x7-b7de8f7e4235": "surface-49x7-1cf74690f828",
    "surface-48x7-64cac5f65a98": "surface-48x7-20ba82623210",
    "surface-44x8-81635c0115dd": "surface-44x8-a199db13f921",
    "surface-17x18-b4476fbe2f96": "surface-17x18-21423b07822f",
    "surface-18x17-cfd7562f2065": "surface-18x17-80302b6483f8",
    "surface-16x19-152f7f052c52": "surface-16x19-3214fce84ce3",
    "surface-19x16-0349ca18b2aa": "surface-19x16-a4181e59af49",
    "surface-15x20-436d77e60df2": "surface-15x20-f217a8f4b01d",
    "surface-13x14-570e71061a69": "surface-13x14-3bf6153ee656",
    "surface-14x13-e0d74734ef82": "surface-14x13-c68025dca87e",
    "surface-10x18-f9ad3d58ec9a": "surface-10x18-ebe630da1f37",
    "surface-9x20-6c0783f9c25c": "surface-9x20-4ae86c882003",
    "surface-12x15-e9cb9e4c34e6": "surface-12x15-946a8d6df26a",
    "surface-12x13-4a12e44faaeb": "surface-12x13-bbf4cc454260",
    "surface-13x12-77f1a15c6d5a": "surface-13x12-49987e4e1b57",
    "surface-11x14-241f52b2a67c": "surface-11x14-da5e34f0d7f9",
    "surface-14x11-8d175fe185b4": "surface-14x11-959e8baaa0c0",
    "surface-10x15-46d59e2505b1": "surface-10x15-c6b0747258fc",
    "surface-19x12-fd3c866aee25": "surface-19x12-e40105f7434a",
    "surface-18x12-839dd57f01ea": "surface-18x12-636596e9b1fb",
    "surface-19x11-881a9d3e9657": "surface-19x11-97f3ebf171c8",
    "surface-17x12-5348eb9d783d": "surface-17x12-cd37920027f8",
    "surface-20x10-ae575be77eca": "surface-20x10-d8b47977ff1e",
    "surface-18x35-75c3febd94f7": "surface-18x35-5623452db72b",
    "surface-21x30-b45e7622dba7": "surface-21x30-69c60bd034fa",
    "surface-17x37-93c1cf7a5e96": "surface-17x37-6e2ba4991fe3",
    "surface-19x33-42de258b7737": "surface-19x33-9ececf1f88aa",
    "surface-16x39-9a5a68b41c9c": "surface-16x39-3acba9ce32a2",
}
# The placement's field frame: where the taxel field sits on the chart.
PLACEMENT_KEYS = ("base_side", "base_kind", "exit_edges", "base_angle_deg", "field_origin_base", "field_origin_uv", "field_x_uv", "field_y_uv", "bottom_board")
_PLATES = {
    "right_triangle_plate": [(0.0, 0.0), (60.0, 0.0), (0.0, 60.0)],
    "equilateral_plate": [(0.0, 0.0), (60.0, 0.0), (30.0, 51.9615)],
    "disk_plate": F.ellipse_outline(25.0, 25.0, 72),
}


def _sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def cases() -> dict[str, Any]:
    """``{name: (stl bytes, seed point, base, options)}`` of the surface template's cases (Whole board); the crank and the
    real soft finger only when their meshes are present."""

    replica = F.stl_bytes(F.soft_finger_replica())
    found: dict[str, Any] = {"soft_finger_mount_end": (replica, SOFT_SEED, SOFT_BASE, dict(BOARD))}
    if SOFT_FINGER.exists():
        found["soft_finger_asset_mount_end"] = (SOFT_FINGER.read_bytes(), SOFT_SEED, SOFT_BASE, dict(BOARD))
    if CRANK.exists():
        found["crank_tip_pad"] = (CRANK.read_bytes(), (1.812, -213.721, 138.929), "auto", dict(BOARD))
    for name, outline in _PLATES.items():
        centre = (math.fsum(p[0] for p in outline) / len(outline), math.fsum(p[1] for p in outline) / len(outline), 3.0)
        found[name] = (F.stl_bytes(F.plate(outline, 3.0)), centre, "auto", dict(BOARD))
    right = found["right_triangle_plate"]
    found["right_triangle_plate_max_taxels"] = (right[0], right[1], "auto", dict(BOARD, objective="max_taxels"))
    return found


def snapshot(case: tuple) -> list[dict[str, Any]]:
    data, seed_point, base, options = case
    seed = select.nearest_facet(read_stl(data), seed_point)
    result = fit.fit_route({"selection": {"ops": [{"op": "grow", "seed_facet": seed}]}, "base": base, "options": options}, data)
    return [
        {
            "rank": proposal["rank"],
            "build_id": proposal["build_id"],
            "metrics": proposal["metrics"],
            "outlines_uv_sha256": _sha256(proposal["outlines_uv"]),
            "placement": {key: proposal["placement"][key] for key in PLACEMENT_KEYS},
        }
        for proposal in result["proposals"]
    ]


class RectangleFitSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.cases = cases()

    def _check(self, name: str) -> None:
        # The fixture's rectangles among the whole-board proposals: every one, in its recorded order (after the masked
        # fields that rank first), each as recorded (its build id as mapped, every recorded metric, the outlines, the
        # field frame).
        if name not in self.cases:
            self.skipTest("asset/ meshes are not committed")
        expected = [dict(item, build_id=SURFACE_BUILD_IDS[item["build_id"]]) for item in self.fixture["cases"][name]]
        found = {item["build_id"]: item for item in snapshot(self.cases[name])}
        self.assertEqual([pinned["build_id"] for pinned in expected if pinned["build_id"] not in found], [])
        ranks = [found[pinned["build_id"]]["rank"] for pinned in expected]
        self.assertEqual(ranks, sorted(ranks))
        for pinned in expected:
            item = found[pinned["build_id"]]
            with self.subTest(build_id=pinned["build_id"]):
                # Every recorded metric keeps its value; a later phase may add keys.
                self.assertEqual({key: item["metrics"].get(key) for key in pinned["metrics"]}, pinned["metrics"])
                self.assertEqual(item["outlines_uv_sha256"], pinned["outlines_uv_sha256"])
                self.assertEqual(item["placement"], pinned["placement"])

    def test_the_soft_finger_mount_end(self) -> None:
        self._check("soft_finger_mount_end")

    def test_the_real_soft_finger_mount_end(self) -> None:
        self._check("soft_finger_asset_mount_end")

    def test_the_crank_tip_pad(self) -> None:
        self._check("crank_tip_pad")

    def test_the_right_triangle_plate(self) -> None:
        self._check("right_triangle_plate")

    def test_the_equilateral_plate(self) -> None:
        self._check("equilateral_plate")

    def test_the_disk_plate(self) -> None:
        self._check("disk_plate")

    def test_max_taxels_on_the_right_triangle_plate(self) -> None:
        self._check("right_triangle_plate_max_taxels")

    def test_the_snapshot_holds_every_case(self) -> None:
        self.assertEqual(set(self.fixture["cases"]), {"soft_finger_mount_end", "soft_finger_mount_end_generic", *ASSET_CASES, *_PLATES, "right_triangle_plate_max_taxels"})
        # The generic template's cases stay as written and are not run (no CAD option since section 26.16).
        self.assertLessEqual(GENERIC_CASES, set(self.fixture["cases"]))
        self.assertFalse(GENERIC_CASES & set(self.cases))
        # Today's figures (claude/specs/masked-field/PLAN.md, sections 3 (P4) and 5).
        best = {name: proposals[0]["metrics"] for name, proposals in self.fixture["cases"].items()}
        shapes = {name: (metrics["rows"], metrics["columns"]) for name, metrics in best.items() if name.startswith("soft_finger")}
        self.assertEqual(shapes, {"soft_finger_mount_end": (44, 8), "soft_finger_asset_mount_end": (44, 8), "soft_finger_mount_end_generic": (49, 7), "soft_finger_asset_mount_end_generic": (49, 7)})
        self.assertEqual({name: metrics["taxels"] for name, metrics in best.items() if name != "right_triangle_plate_max_taxels" and not name.startswith("soft_finger")},
                         {"crank_tip_pad": 306, "right_triangle_plate": 182, "equilateral_plate": 156, "disk_plate": 228})


if __name__ == "__main__":
    unittest.main()
