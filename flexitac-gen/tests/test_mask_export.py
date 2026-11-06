"""The exports of a masked taxel field (``matrix.mask``, masked-field phase P3).

A masked build exports like any other: the polygon field window of each
masked board is one region of the negative GTS and is read back against its
ring, the order notes state the taxel field, and the review bundle adds
``taxels.csv`` (every R x C readout position with its nets, contact pins and
whether it is active) and the review manifest's ``taxel_map``.  These tests
export masked builds with a polygon window, with per-electrode windows, turned
to the right with the columns on top, and with opposite tails, decode what was
written, refuse malformed polygon windows, show that the read-back catches a
wrong window, taxel map or order note, pin the archive digests (Python 3.9 and
3.12) and take the HTTP route and the CLI.  An unmasked build gains nothing:
its archives keep their bytes (tests/test_golden_default.py), and a full mask
is the unmasked build.
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

from engine import check_design, generate_design
from engine.geometry import rect_bounds
from exporters import ExportError, artifact_filenames, build_exports, direct_gerber
from exporters.ipc356 import read_netlist

try:
    from test_api_http import HttpTestCase
    from test_mask_layout import _straight_mask
    import defaults_of_before
except ImportError:  # run as tests.test_mask_export
    from tests.test_api_http import HttpTestCase
    from tests.test_mask_layout import _straight_mask
    from tests import defaults_of_before


def setUpModule() -> None:
    # The default electrodes of before (1.4 mm at 2 mm, fill 0.7): this module's pinned numbers were measured with them
    # (tests/defaults_of_before.py; the user's decision of 2026-11-06 made the default fill 0.5).
    defaults_of_before.start()


ROOT = Path(__file__).resolve().parents[1]
SURFACE = "surface_matrix_v1"
SPARSE = {"pitch_x_mm": 3.0, "pitch_y_mm": 3.0, "taxel_width_mm": 1.0, "taxel_height_mm": 1.0}
GTS = "Gerber_TopSolderMaskLayer.GTS"
TAXEL_COLUMNS = ["row", "column", "row_net", "column_net", "row_pin", "column_pin", "active"]
# A right triangle 10 x 10: ROW_r spans COL_(11-r)..COL_10 (55 taxels).
TRIANGLE = [[10 - row, 10] for row in range(10)]
# sha256 of the three archives (top ZIP, bottom ZIP, review bundle) of each case, the same on Python 3.9.6 and 3.12
# and under any hash seed (measured 2026-10-21).  Re-pinned by P5-diagonal-bus.md section 23 (2026-10-25, the surface
# profile's tails to 200 mm): the build ids, the manifests and the bundle's profile.json change, every other member holds.
# Re-pinned by the profile revision 2026-10-29 (the gold-finger thickness order option and the coverlay-window notes): the
# build ids, the manifests, ORDER_NOTES.txt and the bundle's profile.json change, every other member holds.
# Re-pinned by the profile revision 2026-11-06 (the order: JLC's 2-layer 0.2 mm FPC, the bottom copper empty): the build
# ids, the manifests, ORDER_NOTES.txt (the order block and the FlexiTac fabrication guide cited) and the bundle's
# profile.json change; the designs, boards, layouts and validation, the Gerber layers and netlists but their identity
# headers, jlcpcb.json, taxels.csv, pinout.csv and the previews hold.
DIGESTS = {
    "triangle": (
        "34af536f8dfbae74a1f57dc53d91541f529687533d7010e0c3f58f6e254ad8e1",
        "603f200dad28f484a50684cd622e0e629a1008f5259aae98ac574914517a0be0",
        "557b56c7566a367ce1a9ff1400bc63291e531847522a60f3d397a46bbb9fb1b3",
    ),
    "per-electrode windows": (
        "1e181ae4a3b7430cffc82896321309131f489ab9b0c70e34e9d9a36402430c4b",
        "5659e037b4e0d78dc36ff0af79e082fa63416608ca6be06be08a96cee368e287",
        "b67247b79e8fb6cd3893a6adfc889acfc48e6a883012efbc91a03d26b748bc82",
    ),
    "turned, columns on top": (
        "b5e9eb8dc4d7a4442fbb5659925a6487217c4bb3142634946793f35678b20188",
        "4658009b9a04b086178911df4c50e4bfd91df2f4d53b0e6343e4ae76547962a3",
        "18c6143040ac18a09cd1f1bb9b46830ec304d8f7ce107dcb7050d1ec81c2a9be",
    ),
    "opposite tails": (
        "77e22017fecbbb1a31478e8e74c126d372770f8af490a78e318eb05768ffef1f",
        "6e3bea128a28ae336aeb74078090b0b7d93c6e52f408df6b63a0a43c23828936",
        "c7a97b5ee1b5745d191a856509c95580ec3c98fae77307db768c8a081194cad6",
    ),
}


def _request(rows: int, columns: int, mask=None, matrix=None, **sections) -> dict:
    request = {"template_id": SURFACE, "matrix": {"rows": rows, "columns": columns, **(matrix or {})}, **sections}
    if mask is not None:
        request["matrix"]["mask"] = mask
    return request


def _straight(request: dict, far) -> dict:
    """``request`` with a mask of the straight classes (tests/test_mask_layout.py ``_straight_mask``)."""

    checked = check_design(request)
    assert checked["ok"], checked["validation"]["errors"][:3]
    return dict(request, matrix=dict(request["matrix"], mask=_straight_mask(checked["design"], far)))


def _cases() -> dict:
    return {
        "triangle": _request(10, 10, TRIANGLE),
        "per-electrode windows": _straight(_request(10, 12, matrix=SPARSE), lambda row: 2 + row),
        "turned, columns on top": _straight(
            _request(
                8, 9, tail={"row_side": "right", "column_side": "right"}, role_mapping={"top": "columns", "bottom": "rows"},
                channel_order={"rows": "descending", "columns": "ascending"}, connector={"row_pins": 12},
            ),
            lambda row: row,
        ),
        "opposite tails": _straight(_request(8, 9, tail={"row_side": "bottom", "column_side": "top"}), lambda row: row),
    }


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


def _field_window(board: dict) -> dict:
    (window,) = [opening for opening in board["layers"]["top_coverlay_openings"] if opening.get("shape") == "polygon"]
    return window


class MaskedExportTests(unittest.TestCase):
    """What a masked export contains, decoded from the archives."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.results, cls.exports = {}, {}
        for name, request in _cases().items():
            result = generate_design(request)
            assert result["ok"], (name, result["validation"]["errors"][:3])
            cls.results[name] = result
            cls.exports[name] = build_exports(result)
        cls.unmasked = generate_design(_request(10, 10))
        cls.unmasked_exports = build_exports(cls.unmasked)

    def test_a_masked_build_exports_the_usual_members_and_the_taxel_map(self) -> None:
        plain = {key: sorted(_members(data)) for key, data in self.unmasked_exports.items()}
        for name, exports in self.exports.items():
            with self.subTest(case=name):
                result = self.results[name]
                self.assertEqual(set(exports), set(direct_gerber.ARTIFACT_KEYS))
                for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
                    # The board ZIPs keep their members (the stiffener layer's name aside, the same as unmasked).
                    self.assertEqual(sorted(_members(exports[key])), plain[key])
                bundle = _members(exports["project_review_bundle_zip"])
                names = artifact_filenames(result)
                zips = {f"gerbers/{names[key]}": exports[key] for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip")}
                expected = {*(member for member in plain["project_review_bundle_zip"] if not member.startswith("gerbers/")), *zips, "taxels.csv"}
                self.assertEqual(set(bundle), expected)
                self.assertEqual({name: bundle[name] for name in zips}, zips)

    def test_the_gts_writes_each_polygon_window_as_its_ring(self) -> None:
        polygons = 0
        for name, exports in self.exports.items():
            result = self.results[name]
            for board in result["boards"].values():
                with self.subTest(case=name, board=board["id"]):
                    gts = _members(exports[f"{board['physical_side']}_fpc_gerber_zip"])[GTS].decode("ascii")
                    regions = direct_gerber._decode_gerber(GTS, gts)["regions"]
                    openings = board["layers"]["top_coverlay_openings"]
                    self.assertEqual(len(regions), len(openings))
                    for region, opening in zip(regions, openings):
                        if opening.get("shape") == "polygon":
                            polygons += 1
                            ring = [tuple(point) for point in opening["points"]]
                            # One G36/G37 region over the ring, closed on its first vertex; a staircase, not a box.
                            self.assertEqual(region, [*ring, ring[0]])
                            self.assertGreater(len(ring), 4)
                            self.assertEqual(opening["kind"], "electrode_field_opening")
                        else:
                            x0, y0, x1, y1 = (round(value, 6) for value in rect_bounds(opening))
                            self.assertEqual(region, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
                    self.assertNotIn("G36*\nG37*", gts)
        # Two boards of three cases have a polygon window; per-electrode windows stay rectangles.
        self.assertEqual(polygons, 6)
        sparse = self.results["per-electrode windows"]["boards"]
        self.assertEqual({opening.get("shape") for board in sparse.values() for opening in board["layers"]["top_coverlay_openings"]}, {None})

    def test_taxels_csv_lists_every_readout_position(self) -> None:
        for name, exports in self.exports.items():
            with self.subTest(case=name):
                result = self.results[name]
                bundle = _members(exports["project_review_bundle_zip"])
                mask = result["design"]["matrix"]["mask"]
                rows, columns = result["design"]["matrix"]["rows"], result["design"]["matrix"]["columns"]
                records = _csv(bundle["taxels.csv"])
                self.assertEqual(records[0], TAXEL_COLUMNS)
                self.assertTrue(bundle["taxels.csv"].endswith(b"\n") and b"\r" not in bundle["taxels.csv"])
                # R x C lines, ROW-major.
                self.assertEqual([(int(record[0]), int(record[1])) for record in records[1:]],
                                 [(row, column) for row in range(1, rows + 1) for column in range(1, columns + 1)])
                active = {(int(record[0]), int(record[1])) for record in records[1:] if record[6] == "1"}
                self.assertEqual({record[6] for record in records[1:]}, {"0", "1"})
                self.assertEqual(active, {(row, column) for row, (first, last) in enumerate(mask, 1) for column in range(first, last + 1)})
                self.assertEqual(len(active), _active(mask))
                for board in result["boards"].values():
                    self.assertEqual(board["metrics"]["active_taxel_count"], len(active))
                # The nets and pins are pinout.csv's (the contact of each channel on its board).
                pinout = {(record[2], record[1]): record[0] for record in _csv(bundle["pinout.csv"])[1:]}
                for record in records[1:]:
                    row, column = int(record[0]), int(record[1])
                    self.assertEqual(record[2:4], [f"ROW_{row:02d}", f"COL_{column:02d}"])
                    self.assertEqual(record[4:6], [pinout[("rows", record[2])], pinout[("columns", record[3])]])
        # The descending rows put ROW_01 on the last channel contact: the pins are the pads', not the indices.
        turned = _csv(_members(self.exports["turned, columns on top"]["project_review_bundle_zip"])["taxels.csv"])
        self.assertNotEqual(turned[1][4], "1")

    def test_the_review_manifest_describes_the_taxel_map(self) -> None:
        for name, exports in self.exports.items():
            with self.subTest(case=name):
                result = self.results[name]
                bundle = _members(exports["project_review_bundle_zip"])
                manifest = json.loads(bundle["manifest.json"])
                matrix = result["design"]["matrix"]
                self.assertEqual(manifest["taxel_map"], {
                    "file": "taxels.csv", "columns": TAXEL_COLUMNS, "active": _active(matrix["mask"]),
                    "total": matrix["rows"] * matrix["columns"],
                    "frame": (
                        "the readout's ROW_r x COL_c positions, ROW-major, pins as on the contact pads; "
                        "a position with active 0 has no electrode crossing and always reads 0"
                    ),
                })
                digest = {"sha256": hashlib.sha256(bundle["taxels.csv"]).hexdigest(), "bytes": len(bundle["taxels.csv"])}
                self.assertEqual(manifest["bundle_files"]["taxels.csv"], digest)
                self.assertEqual((manifest["template"], manifest["mask"]), ("surface-matrix/1", "field-mask/1"))
                self.assertEqual(manifest["canonical_design"]["matrix"]["mask"], matrix["mask"])

    def test_the_order_notes_state_the_taxel_field(self) -> None:
        for name, exports in self.exports.items():
            result = self.results[name]
            matrix = result["design"]["matrix"]
            line = f"Taxel field: {_active(matrix['mask'])} of {matrix['rows']} x {matrix['columns']} crossings (masked):"
            notes = [_members(exports[key])["ORDER_NOTES.txt"].decode("utf-8") for key in direct_gerber.ARTIFACT_KEYS]
            for key, text in zip(direct_gerber.ARTIFACT_KEYS, notes):
                with self.subTest(case=name, archive=key):
                    flat = " ".join(text.split())
                    self.assertEqual(flat.count(line), 1)
                    # Once for the build: after the profile, before the first board.
                    self.assertLess(flat.index("Profile:"), flat.index(line))
                    self.assertLess(flat.index(line), flat.index("Board "))
                    self.assertIn("the other positions have no crossing and read 0.", flat)
                    # A cited URL (the FlexiTac fabrication guide's, profile revision 2026-11-06) cannot wrap: it stands whole on its own line.
                    self.assertTrue(all(len(row) <= 78 or row.strip().startswith("https://") for row in text.splitlines()))

    def test_the_netlist_tests_each_masked_electrode_at_its_far_end(self) -> None:
        for name, exports in self.exports.items():
            result = self.results[name]
            for board in result["boards"].values():
                with self.subTest(case=name, board=board["id"]):
                    copper = board["layers"]["top_copper"]
                    netlist = _members(exports[f"{board['physical_side']}_fpc_gerber_zip"])["netlist.ipc"].decode("ascii")
                    _, records = read_netlist(netlist)
                    lands = [record for record in records if record["refdes"] != "J1"]
                    self.assertEqual(len(records), len(copper["pads"]) + len(copper["electrodes"]))
                    self.assertEqual(len(lands), len(copper["electrodes"]))
                    junction = {route["net"]: route["points"][-1] for route in copper["routes"] if route["segment"] == "fanout"}
                    for land in lands:
                        (electrode,) = [item for item in copper["electrodes"] if item["net"] == land["net"]]
                        x0, y0, x1, y1 = rect_bounds(electrode)
                        # On the electrode's copper (within the netlist's 0.001 mm), at the end the fan-out does not reach.
                        self.assertTrue(x0 - 1e-3 <= land["x"] <= x1 + 1e-3 and y0 - 1e-3 <= land["y"] <= y1 + 1e-3, land)
                        end = junction[land["net"]]
                        long_axis = 0 if x1 - x0 >= y1 - y0 else 1
                        length, width = max(x1 - x0, y1 - y0), min(x1 - x0, y1 - y0)
                        # The fan-out ends on the electrode's near end; the square land is centred a half width from the far end.
                        self.assertIn(round(end[long_axis], 6), (round((x0, y0)[long_axis], 6), round((x1, y1)[long_axis], 6)))
                        self.assertAlmostEqual(abs(land[("x", "y")[long_axis]] - end[long_axis]), length - width / 2, delta=1e-3)

    def test_an_unmasked_build_has_no_taxel_map_and_a_full_mask_is_the_unmasked_build(self) -> None:
        bundle = _members(self.unmasked_exports["project_review_bundle_zip"])
        self.assertNotIn("taxels.csv", bundle)
        self.assertNotIn("taxel_map", json.loads(bundle["manifest.json"]))
        for key in direct_gerber.ARTIFACT_KEYS:
            self.assertNotIn("Taxel field", _members(self.unmasked_exports[key])["ORDER_NOTES.txt"].decode("utf-8"))
        full = generate_design(_request(10, 10, [[1, 10]] * 10))
        self.assertEqual(full["manifest"]["build_id"], self.unmasked["manifest"]["build_id"])
        exports = build_exports(full)
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            self.assertEqual(exports[key], self.unmasked_exports[key])
        # The review bundles differ only where the request is recorded: validation.json reports the full mask
        # normalized away (docs/PHASE2_DIRECT_GERBER.md), and the manifest lists that file's digest.
        given, plain = _members(exports["project_review_bundle_zip"]), _members(self.unmasked_exports["project_review_bundle_zip"])
        self.assertEqual(sorted(given), sorted(plain))
        self.assertEqual([name for name in sorted(given) if given[name] != plain[name]], ["manifest.json", "validation.json"])
        normalized = json.loads(given["validation.json"])["normalization"]["values_normalized"]
        self.assertEqual([entry["field"] for entry in normalized], ["matrix.mask"])

    def test_masked_archives_are_pinned(self) -> None:
        for name, exports in self.exports.items():
            with self.subTest(case=name):
                digests = tuple(hashlib.sha256(exports[key]).hexdigest() for key in direct_gerber.ARTIFACT_KEYS)
                self.assertEqual(digests, DIGESTS[name])

    def test_the_exporter_document_quotes_the_triangle(self) -> None:
        text = " ".join((ROOT / "docs" / "PHASE2_DIRECT_GERBER.md").read_text(encoding="utf-8").split())
        sizes = re.search(r"gives a (\d+)-byte top ZIP, a (\d+)-byte bottom ZIP and a (\d+)-byte bundle", text).groups()
        self.assertEqual(tuple(map(int, sizes)), tuple(len(self.exports["triangle"][key]) for key in direct_gerber.ARTIFACT_KEYS))
        (quoted,) = re.findall(r'"(Taxel field: [^"]+)"', text)
        notes = _members(self.exports["triangle"]["project_review_bundle_zip"])["ORDER_NOTES.txt"].decode("utf-8")
        self.assertIn(quoted, " ".join(notes.split()))


class MaskedExportCheckTests(unittest.TestCase):
    """The exporter's form checks of polygon windows and its read-back of the masked members."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = generate_design(_request(10, 10, TRIANGLE))
        assert cls.result["ok"], cls.result["validation"]["errors"][:3]

    def _refused(self, change, fragment: str) -> None:
        tampered = copy.deepcopy(self.result)
        change(tampered["boards"]["row"])
        with self.assertRaises(ExportError) as caught:
            build_exports(tampered)
        self.assertIn(fragment, str(caught.exception))

    def test_malformed_polygon_windows_are_refused_before_regeneration(self) -> None:
        def window(board):
            return _field_window(board)

        def crossed(board):  # a rectilinear ring whose fourth edge crosses its first
            x, y = window(board)["points"][0]
            window(board)["points"] = [[x, y], [x + 4.0, y], [x + 4.0, y + 2.0], [x + 1.0, y + 2.0], [x + 1.0, y - 1.0], [x, y - 1.0]]

        def bump(board, delta):
            window(board)["points"][3][0] += delta

        def diagonal(board):  # one vertex moved along both axes: two slanted edges, still simple
            point = window(board)["points"][3]
            point[0] = round(point[0] + 0.3, 6)
            point[1] = round(point[1] + 0.3, 6)

        cases = (
            ("a self-intersecting ring", crossed, "is not a simple polygon"),
            ("a polygon of another kind", lambda board: window(board).update(kind="sensor_electrode_opening"),
             "only the merged field window (electrode_field_opening) may be a polygon, not 'sensor_electrode_opening'"),
            ("the gang window as a polygon", lambda board: board["layers"]["top_coverlay_openings"][1].update(shape="polygon"),
             "only the merged field window (electrode_field_opening) may be a polygon, not 'connector_contact_opening'"),
            ("another shape", lambda board: window(board).update(shape="rectangle"), "shape must be 'polygon' (a rectangle has none), not 'rectangle'"),
            ("rectangle fields", lambda board: window(board).update(anchor="lower_left", x=1.0), "carries the rectangle fields anchor, x"),
            ("an unmasked board", lambda board: board["grid_registration"].pop("taxel_mask"), "belongs to a masked board"),
            ("a clockwise ring", lambda board: window(board)["points"].reverse(), "is not counter-clockwise"),
            ("a vertex off the grid", lambda board: bump(board, 3e-7), "off the 1e-6 mm layout grid"),
            ("a slanted edge", diagonal, "is neither horizontal nor vertical"),
            ("three vertices", lambda board: window(board).update(points=window(board)["points"][:3]), "must have at least 4 points"),
            ("a closed ring", lambda board: window(board)["points"].append(list(window(board)["points"][0])), "zero-length edge"),
            ("a non-finite vertex", lambda board: window(board)["points"][0].__setitem__(0, float("nan")), "not finite"),
        )
        for name, change, fragment in cases:
            with self.subTest(case=name):
                self._refused(change, fragment)
        # The untouched result exports.
        self.assertEqual(set(build_exports(self.result)), set(direct_gerber.ARTIFACT_KEYS))

    def test_the_read_back_catches_a_wrong_field_window(self) -> None:
        original = direct_gerber._region

        def bounding_box(points):
            xs, ys = [float(point[0]) for point in points], [float(point[1]) for point in points]
            return original([[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]])

        def written(change):
            def masked_regions(openings):
                lines = []
                for opening in openings:
                    region = change(opening["points"]) if opening.get("shape") == "polygon" else original(direct_gerber.rect_corners(opening))
                    lines.extend(region)
                return lines
            return masked_regions

        def moved(points):
            return original([[point[0] + (3e-6 if index == 5 else 0.0), point[1]] for index, point in enumerate(points)])

        for name, change, fragment in (
            ("the bounding rectangle", bounding_box, f"{GTS} region 1 has 5 vertices, expected"),
            ("a vertex 3 microns off", moved, f"{GTS} region 1 has a vertex at"),
        ):
            with self.subTest(case=name):
                with mock.patch.object(direct_gerber, "_masked_coverlay_regions", written(change)):
                    with self.assertRaises(ExportError) as caught:
                        build_exports(self.result)
                self.assertIn("Read-back of top_rows_fpc failed", str(caught.exception))
                self.assertIn(fragment, str(caught.exception))

    def test_the_read_back_catches_a_wrong_taxel_map(self) -> None:
        original = direct_gerber._taxels

        def flipped(line: int):
            def taxels(build):
                lines = original(build).split("\n")
                lines[line] = lines[line][:-1] + ("0" if lines[line].endswith("1") else "1")
                return "\n".join(lines)
            return taxels

        def pins_swapped(build):
            lines = original(build).split("\n")
            fields = lines[1].split(",")
            fields[4], fields[5] = fields[5], str(int(fields[5]) + 1)
            return "\n".join([lines[0], ",".join(fields), *lines[2:]])

        def column_major(build):
            lines = original(build).rstrip("\n").split("\n")
            body = sorted(lines[1:], key=lambda line: (int(line.split(",")[1]), int(line.split(",")[0])))
            return "\n".join([lines[0], *body]) + "\n"

        for name, patch, fragment in (
            ("an inactive position marked active", flipped(1), "taxels.csv line 2"),
            ("an active position marked inactive", flipped(10), "taxels.csv line 11"),
            ("a wrong pin", pins_swapped, "taxels.csv line 2"),
            ("column-major", column_major, "taxels.csv line 3"),
            ("a missing line", lambda build: original(build).rsplit("\n", 2)[0] + "\n", "header and 10 x 10 position lines"),
        ):
            with self.subTest(case=name):
                with mock.patch.object(direct_gerber, "_taxels", patch):
                    with self.assertRaises(ExportError) as caught:
                        build_exports(self.result)
                self.assertIn("Read-back of the review bundle failed", str(caught.exception))
                self.assertIn(fragment, str(caught.exception))
        # A masked bundle without the taxel map, or an unmasked one with it, is refused too.
        with mock.patch.object(direct_gerber, "_taxel_map_files", lambda build: {}):
            with self.assertRaisesRegex(ExportError, "taxels.csv must be written exactly for a masked build"):
                build_exports(self.result)
        with mock.patch.object(direct_gerber, "_taxel_map_files", lambda build: {"taxels.csv": b"row\n"}):
            with self.assertRaisesRegex(ExportError, "taxels.csv must be written exactly for a masked build"):
                build_exports(generate_design(_request(4, 5)))

    def test_the_order_notes_check_needs_the_taxel_field_line(self) -> None:
        original = direct_gerber._taxel_field_notes
        for name, patch in (
            ("no line", lambda boards: []),
            ("the positions counted", lambda boards: [line.replace("Taxel field: 55 of", "Taxel field: 100 of") for line in original(boards)]),
        ):
            with self.subTest(case=name):
                with mock.patch.object(direct_gerber, "_taxel_field_notes", patch):
                    with self.assertRaises(ExportError) as caught:
                        build_exports(self.result)
                self.assertIn("ORDER_NOTES.txt does not state 'Taxel field: 55 of 10 x 10 crossings (masked)'", str(caught.exception))


class MaskedExportRouteTests(HttpTestCase):
    def test_the_export_routes_take_a_masked_design(self) -> None:
        design = generate_design(_request(10, 10, TRIANGLE))["design"]
        bundle = self.request("POST", "/api/export/project", design)
        self.assertEqual(bundle.status, 200, bundle.body[:300])
        self.assertEqual(bundle.headers["content-type"], "application/zip")
        members = _members(bundle.body)
        self.assertEqual(json.loads(members["manifest.json"])["taxel_map"]["active"], 55)
        top = self.request("POST", "/api/export/top-gerber", design)
        self.assertEqual(top.status, 200, top.body[:300])
        self.assertIn("G36*", _members(top.body)[GTS].decode("ascii"))


class MaskedExportCliTests(unittest.TestCase):
    def test_the_cli_exports_a_masked_design(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "masked.json").write_text(json.dumps(_request(10, 10, TRIANGLE)), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / "cli.py"), "export", "masked.json", "--out", "out"], capture_output=True, cwd=directory,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=300,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout[-500:] + completed.stderr[-500:])
            summary = json.loads(completed.stdout)
            bundle = next(path for path in summary["files"].values() if path.endswith("-project-review.zip"))
            self.assertEqual(_csv(_members(Path(bundle).read_bytes())["taxels.csv"])[0], TAXEL_COLUMNS)


if __name__ == "__main__":
    unittest.main()
