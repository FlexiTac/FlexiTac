"""The exports of a diagonal Row bus (``routing.row_sides``, masked-field phase P5c).

A diagonal-bus build exports the members of a masked build; nothing new is
drawn.  Its Row contacts carry the folded order of the lanes
(``tail.row_contact_order``), so ``pinout.csv``, the ``J1`` records of
``netlist.ipc`` and ``taxels.csv`` give each row the pin of its contact; its
boards always carry the masked records, so the bundle always has
``taxels.csv`` (every position active without a mask, and then no
taxel-field line in the order notes); and the review manifest's
``diagonal_row_bus`` records the Row board's ``construction.row_bus`` (its
tails stacked, the level down to which both boards share one outline) and
its contact order with the pins of those contacts, read back against
``pinout.csv`` (claude/specs/masked-field/P5-diagonal-bus.md, P5c and
sections 12-14).  These tests export both sides with ascending and descending Row pins
and NC contacts, one side on each side (one mirrored), and a mask outside
the straight classes, and decode what was written with expectations of
their own (the folded pins computed by hand, the far-end lands from the
geometry); they show the read-back catching an unfolded pinout, a record
that disagrees with the construction and a missing taxel map, pin the
archives (Python 3.9 and 3.12, any hash seed), pin the straight Row
channel's archives as they were before this phase, check the figures the
documents quote, and take the HTTP route and the CLI.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from engine import ROW_BUS_VERSION, generate_design
from engine.geometry import rect_bounds
from exporters import ExportError, artifact_filenames, build_exports, direct_gerber
from exporters.ipc356 import read_netlist

try:
    from test_api_http import HttpTestCase
    from test_diagonal_bus import _crossings, _funnel_depth, _request, _root, _rows
    from test_mask_layout import _determinism_problems
    import defaults_of_before
except ImportError:  # run as tests.test_diagonal_export
    from tests.test_api_http import HttpTestCase
    from tests.test_diagonal_bus import _crossings, _funnel_depth, _request, _root, _rows
    from tests.test_mask_layout import _determinism_problems
    from tests import defaults_of_before


def setUpModule() -> None:
    # The default electrodes of before (1.4 mm at 2 mm, fill 0.7): this module's pinned numbers were measured with them
    # (tests/defaults_of_before.py; the user's decision of 2026-11-06 made the default fill 0.5).
    defaults_of_before.start()


ROOT = Path(__file__).resolve().parents[1]
SURFACE = "surface_matrix_v1"
TAXEL_COLUMNS = ["row", "column", "row_net", "column_net", "row_pin", "column_pin", "active"]
RECORD_KEYS = {"kind", "row_board", "construction", "row_contact_order", "row_contact_pins", "column_board", "frame"}
# A diamond outside the straight classes (E_MASK_ROUTING without routing.row_sides): 25 of 7 x 7 taxels.
DIAMOND = [[4, 4], [3, 5], [2, 6], [1, 7], [2, 6], [3, 5], [4, 4]]


def _case(rows: int, columns: int, mask=None, *, sides: str, top: str = "rows", order: str = "ascending", pins=(None, None)) -> dict:
    request = _request(rows, columns, mask, sides=sides, top=top, pins=pins)
    request["channel_order"] = {"rows": order, "columns": "ascending"}
    return request


def _cases() -> dict:
    return {
        "both": _case(9, 5, sides="both", pins=(12, None)),
        "both, descending, columns on top": _case(9, 5, sides="both", top="columns", order="descending", pins=(12, None)),
        # Rows on top: ROW_01's side with both is the stack's right, so left is built mirrored.
        "left, mirrored": _case(9, 5, sides="left"),
        "right": _case(9, 5, sides="right"),
        "diamond, both": _case(7, 7, DIAMOND, sides="both"),
    }


def _expected_order(rows: int, sides: str, top: str) -> list:
    """The Row nets at contact positions 1..R, by hand: ``both`` folds (near band outside in, far band inside
    out); one side runs ROW_01..ROW_R, reversed when it is the side opposite the Row tail's (built mirrored)."""

    if sides == "both":
        return [f"ROW_{k:02d}" for k in [*range(1, rows + 1, 2), *range(rows - rows % 2, 0, -2)]]
    near = "right" if top == "rows" else "left"
    order = range(rows, 0, -1) if sides != near else range(1, rows + 1)
    return [f"ROW_{k:02d}" for k in order]


def _expected_pins(request: dict) -> dict:
    """``{ROW_k: pin}``: contact position p carries the p-th net of the order; pin = p ascending, P + 1 - p descending."""

    rows = request["matrix"]["rows"]
    count = request["connector"]["row_pins"] or rows
    order = _expected_order(rows, request["routing"]["row_sides"], request["role_mapping"]["top"])
    descending = request["channel_order"]["rows"] == "descending"
    return {net: (count + 1 - position if descending else position) for position, net in enumerate(order, start=1)}


def _position(request: dict, pin: int) -> int:
    """The contact position of a Row pin (positions count from 1; descending pins count from the far end)."""

    count = request["connector"]["row_pins"] or request["matrix"]["rows"]
    return count + 1 - pin if request["channel_order"]["rows"] == "descending" else pin


def _members(data: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _csv(data: bytes) -> list:
    return list(csv.reader(io.StringIO(data.decode("ascii"))))


def _active(mask) -> int:
    count = 0
    for first, last in mask:
        count += last - first + 1
    return count


class DiagonalExportTests(unittest.TestCase):
    """What a diagonal-bus export contains, decoded from the archives."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.requests = _cases()
        cls.results, cls.exports, cls.bundles = {}, {}, {}
        for name, request in cls.requests.items():
            result = generate_design(request)
            assert result["ok"], (name, result["validation"]["errors"][:3])
            cls.results[name] = result
            cls.exports[name] = build_exports(result)
            cls.bundles[name] = _members(cls.exports[name]["project_review_bundle_zip"])
        cls.channel = generate_design(_case(9, 5, sides=None, pins=(12, None)))
        cls.channel_exports = build_exports(cls.channel)

    def test_the_members_are_a_masked_builds(self) -> None:
        plain = {key: sorted(_members(data)) for key, data in self.channel_exports.items()}
        for name, exports in self.exports.items():
            with self.subTest(case=name):
                for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
                    self.assertEqual(sorted(_members(exports[key])), plain[key])
                names = artifact_filenames(self.results[name])
                zips = {f"gerbers/{names[key]}" for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip")}
                expected = {*(member for member in plain["project_review_bundle_zip"] if not member.startswith("gerbers/")), *zips, "taxels.csv"}
                self.assertEqual(set(self.bundles[name]), expected)

    def test_pinout_lists_the_folded_row_order(self) -> None:
        for name, request in self.requests.items():
            with self.subTest(case=name):
                records = _csv(self.bundles[name]["pinout.csv"])
                rows = [record for record in records[1:] if record[2] == "rows"]
                pins = {record[1]: int(record[0]) for record in rows if record[1].startswith("ROW_")}
                self.assertEqual(pins, _expected_pins(request))
                for record in rows:
                    if record[1].startswith("ROW_"):
                        self.assertEqual(record[3], str(int(record[1][4:])))  # logical_index is the row
                    else:
                        self.assertEqual((record[1], record[3]), (f"NC_{int(record[0]):02d}", ""))
                self.assertEqual([int(record[0]) for record in rows], sorted(int(record[0]) for record in rows))
                # The Column board keeps COL_c on pin c.
                columns = {record[1]: int(record[0]) for record in records[1:] if record[2] == "columns"}
                self.assertEqual(columns, {f"COL_{c:02d}": c for c in range(1, request["matrix"]["columns"] + 1)})
        both = _csv(self.bundles["both"]["pinout.csv"])
        self.assertEqual([int(next(r[0] for r in both if r[1] == f"ROW_{k:02d}")) for k in range(1, 10)], [1, 9, 2, 8, 3, 7, 4, 6, 5])
        descending = _expected_pins(self.requests["both, descending, columns on top"])
        self.assertEqual([descending[f"ROW_{k:02d}"] for k in range(1, 10)], [12, 4, 11, 5, 10, 6, 9, 7, 8])

    def test_the_netlist_carries_the_folded_order_and_lands_at_the_far_ends(self) -> None:
        for name, request in self.requests.items():
            result = self.results[name]
            row = result["boards"]["row"]
            with self.subTest(case=name):
                netlist = _members(self.exports[name][f"{row['physical_side']}_fpc_gerber_zip"])["netlist.ipc"].decode("ascii")
                _, records = read_netlist(netlist)
                contacts = {record["net"]: int(record["pin"]) for record in records if record["refdes"] == "J1" and record["net"].startswith("ROW_")}
                self.assertEqual(contacts, _expected_pins(request))
                copper = row["layers"]["top_copper"]
                fanout = {route["net"]: route["points"][-1] for route in copper["routes"] if route["segment"] == "fanout"}
                leaves = {}
                for land in (record for record in records if record["refdes"] == "ROW"):
                    (electrode,) = [item for item in copper["electrodes"] if item["net"] == land["net"]]
                    x0, y0, x1, y1 = rect_bounds(electrode)
                    size = y1 - y0
                    end = fanout[land["net"]][0]
                    self.assertIn(round(end, 6), (round(x0, 6), round(x1, 6)), "the lane leaves the electrode's end")
                    far = x1 if abs(end - x0) < abs(end - x1) else x0
                    self.assertAlmostEqual(abs(land["x"] - far), size / 2, delta=1e-3)
                    self.assertAlmostEqual(land["y"], (y0 + y1) / 2, delta=1e-3)
                    leaves[int(land["net"][4:])] = abs(end - x0) < abs(end - x1)
                odd = {leaves[k] for k in leaves if k % 2}
                even = {leaves[k] for k in leaves if not k % 2}
                self.assertEqual((len(odd), len(even)), (1, 1))
                # Both sides: the odd rows leave at one end, the even rows at the other; one side: all at one end.
                self.assertEqual(odd == even, request["routing"]["row_sides"] != "both")

    def test_taxels_csv_gives_every_position_its_pins(self) -> None:
        for name, request in self.requests.items():
            with self.subTest(case=name):
                result, bundle = self.results[name], self.bundles[name]
                rows, columns = request["matrix"]["rows"], request["matrix"]["columns"]
                mask = request["matrix"].get("mask") or [[1, columns]] * rows
                records = _csv(bundle["taxels.csv"])
                self.assertEqual(records[0], TAXEL_COLUMNS)
                self.assertEqual([(int(r[0]), int(r[1])) for r in records[1:]], [(i, j) for i in range(1, rows + 1) for j in range(1, columns + 1)])
                active = {(int(r[0]), int(r[1])) for r in records[1:] if r[6] == "1"}
                self.assertEqual(active, {(i, j) for i, (first, last) in enumerate(mask, 1) for j in range(first, last + 1)})
                pins = _expected_pins(request)
                for record in records[1:]:
                    self.assertEqual(record[2:4], [f"ROW_{int(record[0]):02d}", f"COL_{int(record[1]):02d}"])
                    self.assertEqual((int(record[4]), int(record[5])), (pins[record[2]], int(record[1])))
                taxel_map = json.loads(bundle["manifest.json"])["taxel_map"]
                self.assertEqual((taxel_map["active"], taxel_map["total"]), (_active(mask), rows * columns))
                for board in result["boards"].values():
                    self.assertEqual(board["grid_registration"]["taxel_mask"]["row_spans"], [list(span) for span in mask])
        # ROW_02 is read on the last Row contact of the folded order.
        second = [r for r in _csv(self.bundles["both"]["taxels.csv"])[1:] if r[2] == "ROW_02"]
        self.assertEqual({r[4] for r in second}, {"9"})

    def test_the_review_manifest_records_the_bus(self) -> None:
        for name, result in self.results.items():
            with self.subTest(case=name):
                bundle = self.bundles[name]
                manifest = json.loads(bundle["manifest.json"])
                record = manifest["diagonal_row_bus"]
                row, column = result["boards"]["row"], result["boards"]["column"]
                self.assertEqual(set(record), RECORD_KEYS)
                self.assertEqual(record["kind"], ROW_BUS_VERSION)
                self.assertEqual((record["row_board"], record["column_board"]), (row["id"], column["id"]))
                self.assertEqual(record["construction"], row["construction"]["row_bus"])
                self.assertEqual(record["row_contact_order"], row["tail"]["row_contact_order"])
                self.assertEqual(record["row_contact_order"], _expected_order(row["grid_registration"]["rows"], *(
                    result["design"]["routing"]["row_sides"], result["design"]["role_mapping"]["top"])))
                pins = _expected_pins(self.requests[name])
                self.assertEqual(record["row_contact_pins"], [pins[net] for net in record["row_contact_order"]])
                self.assertEqual(record["construction"]["tails"], "stacked")
                self.assertIn("pin k carries ROW_k only where the order puts it", record["frame"])
                self.assertIn("construction.tails stacked: both tails leave on one side", record["frame"])
                # One outline down to the tails' roots (diagonal-bus/8): the level is where both tails leave the shared body.
                tail = row["tail"]["bounds"]
                depth = round(row["grid_registration"]["active_region"]["y"] - (tail["y"] + tail["height"]), 6)
                self.assertEqual(record["construction"]["shared_outline_below_field_mm"], depth)
                self.assertGreater(depth, 0.5)
                self.assertIn("construction.shared_outline_below_field_mm: both boards have one outline in the stack", record["frame"])
                self.assertIn("their tails' roots", record["frame"])
                # The identity extra, its recipe, and both board manifests.
                self.assertEqual(manifest["row_bus"], ROW_BUS_VERSION)
                self.assertTrue(manifest["identity"]["build_sha256"].endswith(", row_bus}"))
                for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
                    self.assertEqual(json.loads(_members(self.exports[name][key])["manifest.json"])["row_bus"], ROW_BUS_VERSION)
                # derived-layout.json holds the boards with their records.
                layout = json.loads(bundle["derived-layout.json"])["boards"]
                self.assertEqual(layout["row"]["construction"]["row_bus"], row["construction"]["row_bus"])
                self.assertEqual(layout["row"]["tail"]["row_contact_order"], row["tail"]["row_contact_order"])
                self.assertEqual(layout["column"]["construction"], column["construction"])
                for gone in ("stub_drop_mm", "tail_shift_mm", "neck_mm"):
                    self.assertNotIn(gone, layout["column"]["construction"])

    def test_the_order_notes_state_a_masked_field_only(self) -> None:
        for name, exports in self.exports.items():
            masked = "mask" in self.requests[name]["matrix"]
            for key in direct_gerber.ARTIFACT_KEYS:
                with self.subTest(case=name, archive=key):
                    flat = " ".join(_members(exports[key])["ORDER_NOTES.txt"].decode("utf-8").split())
                    self.assertEqual(flat.count("Taxel field:"), 1 if masked else 0)
                    if masked:
                        self.assertIn("Taxel field: 25 of 7 x 7 crossings (masked):", flat)

    def test_the_order_notes_state_the_folded_row_pins(self) -> None:
        # Phase P5d: the Row board's notes (its ZIP's and the bundle's) list the contacts' pins with their Row nets, in the
        # folded order computed by hand ("one side" for a one-sided bus, whose rows run in turn: the P5d/P5e repair); the
        # Column board's ZIP has no such line, nor has a straight channel's bundle.
        for name, request in self.requests.items():
            pins = _expected_pins(request)
            fold = "folded" if request["routing"]["row_sides"] == "both" else "one side"
            line = f"Row pin order (diagonal Row bus, {fold}): " + ", ".join(
                f"pin {pin} {net}" for net, pin in sorted(pins.items(), key=lambda item: _position(request, item[1]))
            ) + "."
            row_side = "top" if request["role_mapping"]["top"] == "rows" else "bottom"
            for key in direct_gerber.ARTIFACT_KEYS:
                with self.subTest(case=name, archive=key):
                    flat = " ".join(_members(self.exports[name][key])["ORDER_NOTES.txt"].decode("utf-8").split())
                    expected = key == "project_review_bundle_zip" or key.startswith(row_side)
                    self.assertEqual(flat.count("Row pin order"), 1 if expected else 0)
                    if expected:
                        self.assertIn(line, flat)
        channel = " ".join(_members(self.channel_exports["project_review_bundle_zip"])["ORDER_NOTES.txt"].decode("utf-8").split())
        self.assertNotIn("Row pin order", channel)

    def test_the_straight_channel_build_has_no_bus_record(self) -> None:
        bundle = _members(self.channel_exports["project_review_bundle_zip"])
        manifest = json.loads(bundle["manifest.json"])
        self.assertNotIn("diagonal_row_bus", manifest)
        self.assertNotIn("row_bus", manifest)
        self.assertNotIn("taxels.csv", bundle)

    def test_the_new_exporter_code_sums_no_floats_and_iterates_no_sets(self) -> None:
        for function in (direct_gerber._taxel_spans, direct_gerber._row_bus_entry, direct_gerber._check_row_contacts):
            with self.subTest(function=function.__name__):
                self.assertEqual(_determinism_problems(function), [])


# sha256 of the three archives (top ZIP, bottom ZIP, review bundle) of each case of _cases(), the same on Python
# 3.9.6 and 3.12 and under any hash seed (measured 2026-10-21).  Re-pinned in phase P5d, whose order notes state
# the folded Row pin order (ORDER_NOTES.txt of the Row board's ZIP and of the bundle); the Column ZIPs kept theirs.
# The one-sided cases re-pinned again in the P5d/P5e repair (2026-10-22): their note says "one side", not "folded".
# Every case re-pinned for diagonal-bus/2 (2026-10-22, the tail redesign): both boards change, and the review
# manifest records the Column tail's shift and neck.  Re-pinned after its review (the lanes turned down on the field's
# edge, diagonal-bus/1's bands; the masked diamond kept its archives).  Every case re-pinned for diagonal-bus/3
# (2026-10-22, the stacked tails): the build ids change, the Column boards are the straight ones again and the Row
# roots rise, and the review manifest drops the Column tail's shift and neck.  Every case re-pinned for diagonal-bus/4
# (2026-10-22, one outline over the field): the build ids and the Column outline change (the masked diamond's Row
# outline too), and the review manifest records the shared level.  The masked diamond re-pinned again with the user's
# later decisions on diagonal-bus/4 (2026-10-22): it recedes below its widest row, so its lanes follow it inward (no
# Column copper in their keep-out), which moves its Row copper and both outlines; the other cases keep their archives.
# Every case re-pinned for diagonal-bus/5 (2026-10-23, regular outlines): the build ids change and both outlines lose
# their flat vertices (the copper is as it was); and for diagonal-bus/6 (the plan's section 16): the identity extra
# changes every build id, and the diamond's notches are crossed on chamfers (Python 3.9.6 and 3.12 alike).  Every case
# re-pinned for diagonal-bus/7 (2026-10-24, straight sides at the tip, the plan's section 17): the build ids change, and
# the sides from the tip corner down to F's bottom become one line where one encloses them within 1.0 mm (Python 3.9.6
# and 3.12 alike).  Every case re-pinned for diagonal-bus/8 (2026-10-24, the plan's section 20): one outline down to the
# tail roots, the Column V capped at 80 degrees where that roots the tails no deeper (the Row fans at up to 85), both
# tails rooted on the shared bottom edge (Python 3.9.6 and 3.12 alike).  Every case re-pinned for the plan's section 23
# (2026-10-25, the surface profile's tails to 200 mm): the build ids, the manifests and the bundle's profile.json change;
# every other member holds (Python 3.9.6 and 3.12 alike).  Every case rewritten by section 24 (2026-10-25,
# diagonal-bus/9, convex sides): the build ids change, and the diamond's and the one-sided cases' outlines where a side's
# dent is bridged by its hull (Python 3.9.6 and 3.12 alike).  Every case rewritten by section 27 (2026-10-27,
# diagonal-bus/10, the Row tail centred on the field, the user's request "some tails are not within the sensor's width"):
# the build ids change, the Row tails move onto the field's centre line (with both by up to 0.05 mm; one side from
# under the band, its fans inward under the field and both boards' outlines with them) (Python 3.9.6 and 3.12 alike).
# Every case rewritten by section 27.8 (2026-10-28, diagonal-bus/11, one side's convex flank, the multi-gripper video's
# notch): the build ids change, and the one-sided cases' outlines on the side without the bus (the notch below the
# field's outline corner bridged; the copper the same) (Python 3.9.6 and 3.12 alike).  Every case re-pinned by the
# profile revision 2026-10-29 (the gold-finger thickness order option and the coverlay-window notes): the build ids, the
# manifests, ORDER_NOTES.txt and the bundles' profile.json change; the Gerbers and every other member hold, the build id aside.
# Every case re-pinned by the profile revision 2026-11-06 (the order: JLC's 2-layer 0.2 mm FPC, the bottom copper empty):
# the build ids, the manifests, ORDER_NOTES.txt (the order block and the FlexiTac fabrication guide cited) and the
# bundles' profile.json change; the boards, the Gerbers, netlists and validation, the build id aside, and every other
# member hold (before: e3a015f3..., cae0ddac..., 79cc0f5c..., 2cb1554e..., c8222458... for the top ZIPs).
DIGESTS = {
    "both": (
        "87171f8212b2d2642770c7f9b8839543835867a8b9279d2d0ccee254743769e0",
        "81e551ebf029f1917c2000be3008349041edcebd4c91c56946260e3600a3d388",
        "4e466d2be8b10000b6eb0bf4e158afe7ec6949b8c5be96cae485262627eb58b2",
    ),
    "both, descending, columns on top": (
        "3bf5ab37385636f751702c11fd0f41130b9377379d94a6e43264185e88c039cf",
        "2ff6aeb2f755fb7221041f0885114819b86f9c945f86ee63acaaa6f1b87bf17f",
        "9b4794f996e2a7496af1d927f00bc5c513ccc6db8ffe77181aef548ee17cb00b",
    ),
    "left, mirrored": (
        "4d751c59976e21453b5eaecef3199505991fa140def637d70dfeb700fc3f3e7d",
        "ca54bbd8868e82cae4ace8ba0afa9b0ab587b777ba546f89e84e14984d532870",
        "cea09932fb16f6c55b18844969250e7edb45ae86dd5e18f8ac98bfd505b6dc45",
    ),
    "right": (
        "868a9496fd7caa1f9a1ef32faa3bd9fe6c403ffce167fd3fefa4c5d5bac97ebe",
        "4d0b7b159a213d45dc8a11dcf6244ba984bec758aa77690e91516b5f7fb0827d",
        "300345ea791351ee15efc5a45f8161880db300735452491e4ca240be0585ee06",
    ),
    "diamond, both": (
        "096fd6856c989cbbe5519730d03f2889e9a953c684ca4bfc2e28ee4fa88f7111",
        "4cf58f4a22e851caa5fee54a883050f21bf2071f7e8137b5b7be73985f2e9a13",
        "88250d4dfe395e2a517cf460a7b9df4a44bc682d27af603d4d260bc10821c4d7",
    ),
}


def _digests(name: str) -> tuple:
    exports = build_exports(generate_design(_cases()[name]))
    return tuple(hashlib.sha256(exports[key]).hexdigest() for key in direct_gerber.ARTIFACT_KEYS)


class DiagonalArchiveTests(unittest.TestCase):
    def test_diagonal_archives_are_pinned(self) -> None:
        for name in _cases():
            with self.subTest(case=name):
                self.assertEqual(_digests(name), DIGESTS[name])

    def test_the_archives_with_other_hash_seeds(self) -> None:
        code = "import sys; sys.path.insert(0, 'tests'); import test_diagonal_export as t; print(' '.join(t._digests('both')))"
        for seed in ("0", "123"):
            with self.subTest(seed=seed):
                environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
                output = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
                self.assertEqual(tuple(output.stdout.split()), DIGESTS["both"])


# The straight Row channel's archives, measured with the exporter before phase P5c (2026-10-21, Python 3.9.6 and
# 3.12): build id, then sha256 of the top ZIP, the bottom ZIP and the review bundle.  The default build's are in
# tests/test_golden_default.py and the masked ones in tests/test_mask_export.py.  The surface cases re-pinned by
# P5-diagonal-bus.md section 23 (2026-10-25, the surface profile's tails to 200 mm): their build ids, manifests and
# profile.json change, every other member holds; the generic case (the standard profile) keeps its archives.  Every
# case re-pinned by the profile revision 2026-10-29 of both profiles (the gold-finger thickness order option and the
# coverlay-window notes): the build ids, the manifests, ORDER_NOTES.txt and profile.json change, every other member holds
# (the build id aside).  Every case re-pinned by the profile revision 2026-11-06 of both profiles (the order: JLC's
# 2-layer 0.2 mm FPC, the bottom copper empty): the build ids, the manifests, ORDER_NOTES.txt and profile.json change,
# every other member holds (the build id aside; before: tactile-fpc-10x10-06ff5b60ff59, tactile-fpc-8x9-60ee5335903c,
# tactile-fpc-8x9-acbc69addeac, tactile-fpc-3x5-0f245ad84036).
CHANNEL = {
    "surface 10 x 10": (
        {"template_id": SURFACE, "matrix": {"rows": 10, "columns": 10}},
        ("tactile-fpc-10x10-2606dd95dd75", "f66d70ce6e445647d25d293f7dd9314a9b95bd235d930354c53e5876168b7da9",
         "7c52521399a51ff0858e9cf53faa5e025290c420096ea2436e4b8f4aa61dcf45", "b980eb99917404a92b8af02ece92d67651eb81237a0a8857f874118a0451cff4"),
    ),
    "surface turned, columns on top": (
        {"template_id": SURFACE, "matrix": {"rows": 8, "columns": 9}, "tail": {"row_side": "right", "column_side": "right"},
         "role_mapping": {"top": "columns", "bottom": "rows"}, "channel_order": {"rows": "descending", "columns": "ascending"},
         "connector": {"row_pins": 12}},
        ("tactile-fpc-8x9-f97b2164f700", "5996238a8faed9a58399908ad48ae4ebddd163c1724f493ba7a61d50ae282dcf",
         "1063c6a2354239f2fca69c248a85673085fd21a3d5f94c2f54f3cd4938d5532b", "12f5d1b3131d952282639e60310cabd653d34676cfd83ef5335127127e5c85e2"),
    ),
    "surface opposite tails": (
        {"template_id": SURFACE, "matrix": {"rows": 8, "columns": 9}, "tail": {"row_side": "bottom", "column_side": "top"}},
        ("tactile-fpc-8x9-7777f8a5147a", "93cde3ed489e650f87f63c099c2d19f4b3049ea87f248954a4fbb6cb1ca70ed2",
         "19cf857755cc5e9fce623aa548f94993647887bc66390ecc40af275be13d371b", "816d0b0153e28c56c251e2e295b7c6c173b0414b6a2a0d4092c1e69895ed9a9a"),
    ),
    # The generic template builds the diagonal Row bus by default since P5-diagonal-bus.md section 18: its straight
    # channel names routing.row_sides "channel", a new build id (it was tactile-fpc-3x5-1adb4c7f8a53), so the archives
    # were re-pinned once; their members but the identity carriers are the bytes measured before (test_generic_identity_guard).
    "generic 3 x 5, left tails, descending columns": (
        {"matrix": {"rows": 3, "columns": 5}, "tail": {"row_side": "left", "column_side": "left"},
         "channel_order": {"rows": "ascending", "columns": "descending"},
         "routing": {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016, "row_sides": "channel"}},
        ("tactile-fpc-3x5-4041f0e0d274", "1a22d8fd0c52c9203df45e3670cf37f5026089b3fef1b91b49a3f90f30b01714",
         "a8318294e657caee66ed1b18fd52dbef0c75f74c7f741d99bf7f0fbe93037879", "e9fe6514734673afeb0b320f299d1926592f1d6333aca6a35d67fbfc0ee471b3"),
    ),
}


class ChannelArchiveTests(unittest.TestCase):
    def test_the_straight_channel_archives_keep_their_bytes(self) -> None:
        for name, (request, expected) in CHANNEL.items():
            with self.subTest(case=name):
                result = generate_design(request)
                self.assertTrue(result["ok"], result["validation"]["errors"][:2])
                exports = build_exports(result)
                digests = tuple(hashlib.sha256(exports[key]).hexdigest() for key in direct_gerber.ARTIFACT_KEYS)
                self.assertEqual((result["manifest"]["build_id"], *digests), expected)


class DiagonalExportCheckTests(unittest.TestCase):
    """The read-back of a diagonal-bus bundle: the folded order in pinout.csv, the record and the taxel map."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = generate_design(_cases()["both"])
        assert cls.result["ok"], cls.result["validation"]["errors"][:3]

    def _refused(self, fragment: str) -> None:
        with self.assertRaises(ExportError) as caught:
            build_exports(self.result)
        self.assertIn("Read-back of the review bundle failed", str(caught.exception))
        self.assertIn(fragment, str(caught.exception))

    def test_an_unfolded_pinout_is_caught(self) -> None:
        original = direct_gerber._pinout

        def unfolded(build):
            # ROW_k on pin k: what a reader that assumes the straight channel's order would write.
            lines = original(build).split("\n")
            fields = [line.split(",") for line in lines]
            for item in fields[1:]:
                if len(item) > 3 and item[2] == "rows" and item[1].startswith("ROW_"):
                    item[0] = str(int(item[1][4:]))
            return "\n".join(",".join(item) for item in fields)

        with mock.patch.object(direct_gerber, "_pinout", unfolded):
            self._refused("pinout.csv lists the Row nets ['ROW_01', 'ROW_03'")

    def test_a_record_that_disagrees_with_the_construction_is_caught(self) -> None:
        original = direct_gerber._row_bus_entry

        def changed(change):
            def entry(build):
                answer = copy.deepcopy(original(build))
                change(answer["diagonal_row_bus"])
                return answer
            return entry

        def reported(record):
            record["construction"]["contact_order"] = list(reversed(record["construction"]["contact_order"]))

        def repeated(record):
            record["row_contact_order"][1] = "ROW_01"
            record["construction"]["contact_order"] = list(record["row_contact_order"])

        for name, change, fragment in (
            ("another reported order", reported, "is not the one construction.row_bus reports"),
            ("a row twice", repeated, "does not name every row once"),
        ):
            with self.subTest(case=name):
                with mock.patch.object(direct_gerber, "_row_bus_entry", changed(change)):
                    self._refused(fragment)

    def test_order_notes_without_the_folded_pins_are_caught(self) -> None:
        # The order notes must state the Row board's folded pins (phase P5d); without them, or with ROW_k on pin k, the
        # read-back of the Row board's ZIP refuses them.
        def unfolded(board):
            notes = original(board)
            return [re.sub(r"pin (\d+) ROW_\d+", lambda match: f"pin {match.group(1)} ROW_{int(match.group(1)):02d}", note) for note in notes]

        original = direct_gerber._row_contact_notes
        for name, replacement in (("missing", lambda board: []), ("unfolded", unfolded)):
            with self.subTest(case=name):
                with mock.patch.object(direct_gerber, "_row_contact_notes", replacement):
                    with self.assertRaises(ExportError) as caught:
                        build_exports(self.result)
                    self.assertIn("ORDER_NOTES.txt does not state 'Row pin order (diagonal Row bus, folded): pin 1 ROW_01, pin 2 ROW_03", str(caught.exception))

    def test_an_unmasked_bus_needs_its_taxel_map(self) -> None:
        with mock.patch.object(direct_gerber, "_taxel_map_files", lambda build: {}):
            self._refused("taxels.csv must be written exactly for a masked build")

    def test_a_tampered_contact_order_is_refused(self) -> None:
        tampered = copy.deepcopy(self.result)
        tampered["boards"]["row"]["tail"]["row_contact_order"].reverse()
        with self.assertRaisesRegex(ExportError, r"boards\.row\.tail\.row_contact_order\[0\] does not match the geometry"):
            build_exports(tampered)
        tampered = copy.deepcopy(self.result)
        tampered["boards"]["row"]["construction"]["row_bus"]["split"] = "halves"
        with self.assertRaisesRegex(ExportError, r"boards\.row\.construction\.row_bus\.split does not match the geometry"):
            build_exports(tampered)


class DiagonalDocumentTests(unittest.TestCase):
    """The figures docs/LAYOUT_SCHEMA.md, docs/PHASE2_DIRECT_GERBER.md and docs/INTEGRATION.md quote."""

    @staticmethod
    def _prose(name: str) -> str:
        return " ".join((ROOT / "docs" / name).read_text(encoding="utf-8").replace("`", "").replace("*", "").split())

    def _quoted(self, text: str, pattern: str) -> tuple:
        found = re.findall(pattern, text)
        self.assertEqual(len(found), 1, pattern)
        return tuple(float(value) for value in (found[0] if isinstance(found[0], tuple) else (found[0],)))

    def test_the_quoted_rectangle(self) -> None:
        layout = self._prose("LAYOUT_SCHEMA.md")
        quoted = self._quoted(
            layout,
            r"both makes the tip ([\d.]+) mm wide \(([\d.]+) mm with the straight channel\); the Row funnel's last bends lie ([\d.]+) mm "
            r"below the field and both tails root ([\d.]+) mm below it, on the shared body's bottom edge, the Column tail centred and "
            r"stacked under the Row tail\. One side, the fans' last bends lie ([\d.]+) mm and the tails root ([\d.]+) mm below the field\.",
        )
        measured = []
        for sides in ("both", None):
            result = generate_design(_request(32, 12, sides=sides))
            row = result["boards"]["row"]
            tip = _rows(row)["ROW_01"]
            hits = _crossings(row["outline"]["points"], (tip[1] + tip[3]) / 2)
            measured.append(round(hits[-1] - hits[0], 3))
            if sides == "both":
                both = result
        roots = []
        for result in (both, generate_design(_request(32, 12, sides="right"))):
            row, column = result["boards"]["row"], result["boards"]["column"]
            depth = round(row["grid_registration"]["active_region"]["y"] - _root(row), 3)
            # Both tails root on the shared body's bottom edge.
            self.assertEqual(round(column["grid_registration"]["active_region"]["y"] - _root(column), 3), depth)
            roots.append((round(_funnel_depth(row), 3), depth))
        self.assertEqual(quoted, (*measured, *roots[0], *roots[1]))
        bands = both["boards"]["row"]["construction"]["row_bus"]["band_mm"]
        integration = self._prose("INTEGRATION.md")
        self.assertEqual(self._quoted(integration, r"\(([\d.]+) and ([\d.]+) mm on the two sides of a 32 x 12 rectangle with both\)"),
                         (round(bands["near"], 2), round(bands["far"], 2)))

    def test_the_quoted_tails_and_pins(self) -> None:
        integration = self._prose("INTEGRATION.md")
        # The stacked tails: no gap or clearance is quoted any more, and the record and the registration keys named are
        # the built ones.
        for gone in ("tail_gap_mm", "row_board_to_column_tail_mm", "column_board_to_row_tail_mm", "tail_shift_mm", "neck_mm", "side by side"):
            self.assertNotIn(gone, integration)
        record = generate_design(_cases()["both"])["boards"]["row"]
        self.assertEqual(record["construction"]["row_bus"]["tails"], "stacked")
        self.assertIn("(construction.row_bus.tails stacked)", integration)
        for key in ("tail_sides_match", "tail_overlap_width_mm"):
            self.assertIn(key, record["verification"]["registration"])
            self.assertIn(key, integration)
        phase2 = self._prose("PHASE2_DIRECT_GERBER.md")
        (listed,) = re.findall(r"9 rows with both and ascending order put ROW_01\.\.ROW_09 on pins ([\d, ]+)\.", phase2)
        pins = _expected_pins(_cases()["both"])
        self.assertEqual([int(pin) for pin in listed.split(", ")], [pins[f"ROW_{k:02d}"] for k in range(1, 10)])
        record = json.loads(_members(build_exports(generate_design(_cases()["right"]))["project_review_bundle_zip"])["manifest.json"])["diagonal_row_bus"]
        section = phase2[phase2.index("A diagonal Row bus's manifest has row_bus"):]
        for key in sorted(record):
            self.assertIn(key, section[:900], key)
        for gone in ("column_tail_shift_mm", "column_neck_mm"):
            self.assertNotIn(gone, section[:900])


class DiagonalExportRouteTests(HttpTestCase):
    def test_the_export_route_takes_a_diagonal_bus(self) -> None:
        design = generate_design(_cases()["both"])["design"]
        bundle = self.request("POST", "/api/export/project", design)
        self.assertEqual(bundle.status, 200, bundle.body[:300])
        manifest = json.loads(_members(bundle.body)["manifest.json"])
        self.assertEqual(manifest["diagonal_row_bus"]["row_contact_order"][-1], "ROW_02")


class DiagonalExportCliTests(unittest.TestCase):
    def test_the_cli_exports_a_diagonal_bus(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "bus.json").write_text(json.dumps(_cases()["left, mirrored"]), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / "cli.py"), "export", "bus.json", "--out", "out"], capture_output=True, cwd=directory,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=300,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout[-500:] + completed.stderr[-500:])
            summary = json.loads(completed.stdout)
            bundle = _members(Path(next(path for path in summary["files"].values() if path.endswith("-project-review.zip"))).read_bytes())
            self.assertEqual(json.loads(bundle["manifest.json"])["diagonal_row_bus"]["row_contact_order"][0], "ROW_09")
            self.assertEqual(_csv(bundle["taxels.csv"])[0], TAXEL_COLUMNS)


if __name__ == "__main__":
    unittest.main()
