"""Exported artifacts (audit M6 bundle and names, M7 exporter part, M10, L9, L10; decisions D10, D17).

Stiffener layers come from the stiffener objects; each board ZIP carries an
IPC-D-356A netlist and a manifest; the review bundle is complete and can be
verified on its own; artifact names carry the build id everywhere; ZIP
members are stored; every Gerber has its X2 attributes.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import http.client
import io
import json
import math
import os
import re
import subprocess
import sys
import threading
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import app
from engine import GENERATOR_VERSION, REQUEST_WARNING_CODES, generate_design, load_profile
from engine import core as engine_core
from engine.drc import DRC_VERSION
from exporters import EXPORTER_VERSION, ExportError, artifact_filenames, build_exports

try:
    import geometry_checks as gc
except ImportError:  # run as ``python -m unittest tests.test_export_artifacts``
    from tests import geometry_checks as gc

ROOT = Path(__file__).resolve().parents[1]
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
GERBER_SUFFIXES = (".GTL", ".GTS", ".GKO", ".GBSL")
NC_DESIGN = {"rows": 3, "columns": 4, "connector": {"row_pins": 6, "column_pins": 9}}
_STROKE = re.compile(r"X(-?\d+)Y(-?\d+)D0([12])\*")
_APERTURE = re.compile(r"%ADD(\d+)C,([0-9.]+)\*%")
_SELECTION = re.compile(r"D(\d+)\*")


def _members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _generate(design=None) -> dict:
    result = generate_design(design)
    if not result["ok"]:
        raise AssertionError(result["validation"]["errors"])
    return result


def _center(rect) -> tuple[float, float]:
    x0, y0, x1, y1 = gc.bounds(rect)
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def _read_ipc356(text: str) -> tuple[dict[str, str], list[dict]]:
    """A small IPC-D-356A reader: parameters and test records by their fixed columns."""

    parameters: dict[str, str] = {}
    records: list[dict] = []
    ended = False
    for line in text.splitlines():
        if len(line) > 80 or ended:
            raise AssertionError(f"line beyond column 80 or after the 999 record: {line!r}")
        if line.startswith("C"):
            continue
        if line.startswith("P"):
            name, _, value = line[3:].partition(" ")
            parameters[name] = value.strip()
        elif line[:3] in ("317", "327", "367"):
            if parameters.get("UNITS") != "CUST 1":
                raise AssertionError("test records before a metric (CUST 1) unit")
            records.append(
                {
                    "type": line[:3],
                    "net": line[3:17].strip(),
                    "refdes": line[20:26].strip(),
                    "dash": line[26],
                    "pin": line[27:31].strip(),
                    "midpoint": line[31] == "M",
                    "hole": line[32:38].strip(),
                    "access": line[38:41],
                    "x": int(line[42:49]) / 1000,
                    "y": int(line[50:57]) / 1000,
                    "width": int(line[58:62]) / 1000,
                    "height": int(line[63:67]) / 1000,
                    "rotation": line[67:71],
                    "soldermask": line[72:74],
                }
            )
        elif line == "999":
            ended = True
        else:
            raise AssertionError(f"unknown IPC-D-356A record {line!r}")
    if not ended:
        raise AssertionError("no 999 end-of-job record")
    return parameters, records


def _copper_items(gtl: str) -> list[tuple]:
    """Emitted copper as ('segment', a, b, radius) and ('box', bounds)."""

    apertures: dict[str, float] = {}
    items: list[tuple] = []
    radius = 0.0
    region = None
    last = None
    for line in gtl.splitlines():
        stroke, aperture, selection = _STROKE.fullmatch(line), _APERTURE.fullmatch(line), _SELECTION.fullmatch(line)
        if aperture:
            apertures[aperture[1]] = float(aperture[2])
        elif selection:
            radius = apertures[selection[1]] / 2
        elif line == "G36*":
            region = []
        elif line == "G37*":
            xs, ys = [p[0] for p in region], [p[1] for p in region]
            items.append(("box", (min(xs), min(ys), max(xs), max(ys))))
            region = None
        elif stroke:
            point = (int(stroke[1]) / 1e6, int(stroke[2]) / 1e6)
            if region is not None:
                region.append(point)
            elif stroke[3] == "1":
                items.append(("segment", last, point, radius))
            last = point
    return items


def _gap(first: tuple, second: tuple) -> float:
    if first[0] == "box" and second[0] == "box":
        a, b = first[1], second[1]
        return math.hypot(max(0.0, b[0] - a[2], a[0] - b[2]), max(0.0, b[1] - a[3], a[1] - b[3]))
    if first[0] == "box":
        first, second = second, first
    if second[0] == "box":
        return gc.segment_box_distance(first[1], first[2], second[1]) - first[3]
    return gc.segment_distance(first[1], first[2], second[1], second[2]) - first[3] - second[3]


def _components(items: list[tuple]) -> list[int]:
    parent = list(range(len(items)))

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if _gap(items[i], items[j]) <= 1e-6:
                parent[root(i)] = root(j)
    return [root(index) for index in range(len(items))]


class StiffenerTests(unittest.TestCase):
    """Side, material, thickness, layer name and metadata come from each stiffener object (M7, D10)."""

    def _with_thickness(self, thickness: float) -> dict:
        profile = copy.deepcopy(load_profile())
        stackup = profile["stackup"]
        stackup["stiffener_thickness_mm"] = thickness
        # Stage G: the profile also checks the contact zone against the
        # connector (on the 2-layer order, since the user's decision of
        # 2026-11-06, JLC's rule: the ordered FPC + the stiffener); describe a
        # connector that takes this one, so every JLC option still reaches the exporter.
        profile["connector"]["contact_zone_thickness_mm"] = round(profile["order"]["fpc_thickness_mm"] + thickness, 6)
        # The generic profile builds the straight Row channel (the diagonal Row bus takes the surface profile, whose
        # stack-up and fabrication sections are the same; P5-diagonal-bus.md section 20).
        with mock.patch("engine.core.load_profile", return_value=profile):
            return generate_design({"routing": {"row_sides": "channel"}})

    def test_every_jlc_pi_option_names_its_layer_and_metadata(self) -> None:
        options = load_profile()["fabrication"]["pi_stiffener_thickness_options_mm"]
        self.assertIn(0.225, options)
        for thickness in options:
            result = self._with_thickness(thickness)
            self.assertTrue(result["ok"], result["validation"]["errors"])
            exports = build_exports(result)
            layer = f"Gerber_BottomStiffenerLayer_pib_{thickness:g}.GBSL"
            if thickness == 0.225:
                self.assertEqual(layer, "Gerber_BottomStiffenerLayer_pib_0.225.GBSL")
            review = json.loads(_members(exports["project_review_bundle_zip"])["manifest.json"])
            requirement = f"Verify each PI stiffener in {layer} is detected at {thickness:g} mm after JLCPCB upload."
            self.assertIn(requirement, review["review_requirements"])
            for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
                with self.subTest(thickness=thickness, artifact=key):
                    members = _members(exports[key])
                    self.assertEqual([name for name in members if name.endswith(".GBSL")], [layer])
                    self.assertIn(f"stiffener {thickness:g} mm*", members[layer].decode("ascii").splitlines()[0])
                    (entry,) = json.loads(members["jlcpcb.json"])["fpcStiffeners"]
                    self.assertEqual(
                        (entry["gerber"], entry["layer"], entry["material"], entry["thickness"]),
                        (layer, "bottom", "pi", f"{thickness:g}"),
                    )
                    (stiffener,) = json.loads(members["manifest.json"])["stiffeners"]
                    self.assertEqual((stiffener["gerber"], stiffener["thickness_mm"], stiffener["material"]), (layer, thickness, "polyimide"))
                    self.assertEqual(review["artifacts"][key]["stiffeners"], [stiffener])

    def test_a_thickness_jlc_does_not_offer_is_refused(self) -> None:
        # The engine reports a non-JLC profile thickness, so nothing is exported ...
        blocked = self._with_thickness(0.3)
        self.assertEqual(
            [(issue["code"], issue["field"]) for issue in blocked["validation"]["errors"]],
            [("E_PROFILE_FAB_LIMIT", "profile.stackup.stiffener_thickness_mm")],
        )
        with self.assertRaises(ExportError):
            build_exports(blocked)
        # ... and the exporter refuses a valid result whose profile or
        # stiffener objects were edited to one.
        base = _generate()
        edited = copy.deepcopy(base)
        edited["profile"]["stackup"]["stiffener_thickness_mm"] = 0.3
        with self.assertRaisesRegex(ExportError, "profile.stackup.stiffener_thickness_mm"):
            build_exports(edited)
        for field, value, fragment in (
            ("thickness_mm", 0.3, "not a JLC polyimide option"),
            ("thickness_mm", 0.2 + 1e-6, "not a JLC polyimide option"),
            ("thickness_mm", "0.2", "not a JLC polyimide option"),
            ("material", "fr4", "material 'fr4' is not supported"),
            ("side", "top", "only bottom stiffeners"),
        ):
            tampered = copy.deepcopy(base)
            tampered["boards"]["column"]["layers"]["bottom_stiffener"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ExportError, fragment):
                build_exports(tampered)

    def test_a_stiffener_side_or_material_the_exporter_cannot_write_fails_generation(self) -> None:
        # Generation and export agree (audit M7): a profile asking for a top or
        # a non-PI stiffener is a profile error, never ok=true and then a refusal.
        for key, value, code in (
            ("stiffener_side", "top", "E_PROFILE_INCONSISTENT"),
            ("stiffener_material", "fr4", "E_PROFILE_FAB_LIMIT"),
            ("stiffener_material", "stainless_steel", "E_PROFILE_FAB_LIMIT"),
        ):
            profile = copy.deepcopy(load_profile())
            profile["stackup"][key] = value
            with mock.patch("engine.core.load_profile", return_value=profile):
                result = generate_design({"routing": {"row_sides": "channel"}})  # the generic profile's Row traces
            with self.subTest(key=key, value=value):
                self.assertFalse(result["ok"])
                self.assertEqual(
                    [(issue["code"], issue["field"]) for issue in result["validation"]["errors"]], [(code, f"profile.stackup.{key}")]
                )
                with self.assertRaises(ExportError):
                    build_exports(result)

    def test_several_stiffeners_get_one_layer_per_thickness(self) -> None:
        # The extra stiffeners come from the generator (a patched board
        # builder), since the exporter regenerates the boards it writes (D17):
        # one of another thickness (0.15 mm; the connector zone's is the
        # thinnest option, 0.1 mm, since the user's decision of 2026-11-06),
        # one as thick as the connector-zone stiffener.
        build_column_board = engine_core.build_column_board
        profile_thickness = load_profile()["stackup"]["stiffener_thickness_mm"]
        self.assertNotEqual(profile_thickness, 0.15)

        def with_fanout_stiffeners(design, profile):
            board = build_column_board(design, profile)
            active = board["grid_registration"]["active_region"]
            cx, cy = active["x"] + active["width"] / 2, active["y"] + active["height"] / 2
            connector = board["layers"]["bottom_stiffener"][0]
            for offset, thickness in ((-6.0, 0.15), (6.0, connector["thickness_mm"])):
                square = [[cx + offset - 1, cy - 1], [cx + offset + 1, cy - 1], [cx + offset + 1, cy + 1], [cx + offset - 1, cy + 1]]
                board["layers"]["bottom_stiffener"].append(dict(connector, zone="fanout", thickness_mm=thickness, points=square))
            return board

        with mock.patch.object(engine_core, "build_column_board", with_fanout_stiffeners):
            result = _generate()
            exports = build_exports(result)
            # An edited result is still refused: its boards are not the generator's.
            edited = copy.deepcopy(result)
            edited["boards"]["column"]["layers"]["bottom_stiffener"][2]["thickness_mm"] = 0.25
            with self.assertRaisesRegex(ExportError, r"boards\.column\.layers\.bottom_stiffener\[2\]\.thickness_mm"):
                build_exports(edited)
        board = result["boards"]["column"]
        self.assertTrue(board["verification"]["all_checks_passed"])
        self.assertEqual(len(board["layers"]["bottom_stiffener"]), 3)
        members = _members(exports[f"{board['physical_side']}_fpc_gerber_zip"])
        other, thick = "Gerber_BottomStiffenerLayer_pib_0.15.GBSL", f"Gerber_BottomStiffenerLayer_pib_{profile_thickness:g}.GBSL"
        self.assertEqual(sorted(name for name in members if name.endswith(".GBSL")), sorted([other, thick]))
        stiffeners = board["layers"]["bottom_stiffener"]
        _, other_regions = gc.decode_gerber(members[other].decode("ascii"))
        _, thick_regions = gc.decode_gerber(members[thick].decode("ascii"))
        self.assertEqual(len(other_regions), 1)
        self.assertTrue(gc.same_ring(other_regions[0], stiffeners[1]["points"], 2e-6))
        self.assertEqual(len(thick_regions), 2)
        self.assertTrue(gc.same_ring(thick_regions[0], stiffeners[0]["points"], 2e-6))
        self.assertTrue(gc.same_ring(thick_regions[1], stiffeners[2]["points"], 2e-6))
        entries = json.loads(members["jlcpcb.json"])["fpcStiffeners"]
        self.assertEqual(
            [(entry["id"], entry["gerber"], entry["thickness"]) for entry in entries],
            [("direct_pi_01", thick, f"{profile_thickness:g}"), ("direct_pi_02", other, "0.15"), ("direct_pi_03", thick, f"{profile_thickness:g}")],
        )
        manifest = json.loads(members["manifest.json"])
        self.assertEqual([(item["gerber"], item["count"]) for item in manifest["stiffeners"]], [(thick, 2), (other, 1)])
        review = json.loads(_members(exports["project_review_bundle_zip"])["manifest.json"])
        self.assertTrue(any(other in line for line in review["review_requirements"]))
        # The board's order notes name each of its stiffener layers with its thickness.
        notes = " ".join(members["ORDER_NOTES.txt"].decode("utf-8").split())
        for layer, thickness in ((thick, f"{profile_thickness:g}"), (other, "0.15")):
            self.assertIn(f"Stiffener layer: {layer} (polyimide {thickness} mm, bottom side)", notes)


class NetlistTests(unittest.TestCase):
    """IPC-D-356A netlist per board: one SMD test point per contact with the pad's pin (M10)."""

    CASES = (
        {},
        dict(NC_DESIGN, scan_order="forward"),
        dict(NC_DESIGN, scan_order="reverse", connector_side="right"),
        {"rows": 5, "columns": 17, "connector": {"column_pins": 40}, "connector_side": "top", "row_fpc_position": "bottom"},
        {"rows": 2, "columns": 9, "connector_side": "left"},
    )

    def test_one_test_point_per_contact_with_the_pad_pins(self) -> None:
        nc_nets = 0
        for design in self.CASES:
            result = _generate(design)
            exports = build_exports(result)
            for board in result["boards"].values():
                with self.subTest(design=design, board=board["id"]):
                    members = _members(exports[f"{board['physical_side']}_fpc_gerber_zip"])
                    parameters, records = _read_ipc356(members["netlist.ipc"].decode("ascii"))
                    self.assertEqual(
                        (parameters["UNITS"], parameters["JOB"], parameters["TITLE"]),
                        ("CUST 1", result["manifest"]["build_id"], board["id"]),
                    )
                    fields = ("type", "dash", "midpoint", "hole", "access", "rotation", "soldermask")
                    for record in records:
                        # SMD lands on the primary (copper) side, exposed there (S2: mask on the secondary side only).
                        self.assertEqual(tuple(record[field] for field in fields), ("327", "-", False, "", "A01", "R000", "S2"))
                    copper = board["layers"]["top_copper"]
                    pads = copper["pads"]
                    contacts = {int(record["pin"]): record for record in records if record["refdes"] == "J1"}
                    self.assertEqual(len(contacts), len([record for record in records if record["refdes"] == "J1"]))
                    self.assertEqual(set(contacts), {pad["pin"] for pad in pads})
                    for pad in pads:
                        record = contacts[pad["pin"]]
                        x0, y0, x1, y1 = gc.bounds(pad)
                        self.assertEqual(record["net"], pad["net"])
                        measured = (record["x"], record["y"], record["width"], record["height"])
                        for value, expected in zip(measured, (*_center(pad), x1 - x0, y1 - y0)):
                            self.assertAlmostEqual(value, expected, delta=0.0005 + 1e-9)
                    by_net: dict[str, list] = {}
                    for record in records:
                        by_net.setdefault(record["net"], []).append(record)
                    self.assertEqual(len(by_net), len(pads))
                    stem = "ROW" if board["role"] == "rows" else "COL"
                    electrodes = {electrode["net"]: electrode for electrode in copper["electrodes"]}
                    ends = {route["net"]: route["points"][-1] for route in copper["routes"]}
                    for pad in pads:
                        net_records = by_net[pad["net"]]
                        if pad["kind"] == "connector_nc_pad":
                            # NC contacts are their own nets, named after their own pin.
                            nc_nets += 1
                            self.assertEqual(pad["net"], f"NC_{pad['pin']:02d}")
                            self.assertEqual([record["refdes"] for record in net_records], ["J1"])
                            continue
                        # Contact plus the far end of its electrode: continuity is testable.
                        self.assertEqual(sorted(record["refdes"] for record in net_records), sorted(["J1", stem]))
                        land = next(record for record in net_records if record["refdes"] == stem)
                        self.assertEqual(int(land["pin"]), int(pad["net"].split("_")[1]))
                        box = gc.bounds(electrodes[pad["net"]])
                        half = land["width"] / 2
                        self.assertTrue(box[0] - 1e-3 <= land["x"] - half and land["x"] + half <= box[2] + 1e-3)
                        self.assertTrue(box[1] - 1e-3 <= land["y"] - half and land["y"] + half <= box[3] + 1e-3)
                        middle = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
                        edge_middles = ((box[0], middle[1]), (box[2], middle[1]), (middle[0], box[1]), (middle[0], box[3]))
                        far = max(edge_middles, key=lambda point: math.dist(point, ends[pad["net"]]))
                        self.assertLessEqual(max(abs(land["x"] - far[0]), abs(land["y"] - far[1])), half + 1e-3)
        self.assertGreater(nc_nets, 0)

    def test_netlist_nets_are_the_emitted_copper_connectivity(self) -> None:
        for design in (NC_DESIGN, {"rows": 3, "columns": 17, "connector_side": "right"}):
            result = _generate(design)
            exports = build_exports(result)
            for board in result["boards"].values():
                with self.subTest(design=design, board=board["id"]):
                    members = _members(exports[f"{board['physical_side']}_fpc_gerber_zip"])
                    items = _copper_items(members["Gerber_TopLayer.GTL"].decode("ascii"))
                    roots = _components(items)
                    _, records = _read_ipc356(members["netlist.ipc"].decode("ascii"))
                    component_of_net: dict[str, set] = {}
                    for record in records:
                        point = (record["x"], record["y"])
                        hits = {roots[index] for index, item in enumerate(items) if _gap(item, ("segment", point, point, 0.0)) <= 1e-3}
                        self.assertEqual(len(hits), 1, record)
                        component_of_net.setdefault(record["net"], set()).update(hits)
                    # Each net is one copper island and islands are not shared between nets.
                    self.assertTrue(all(len(found) == 1 for found in component_of_net.values()))
                    self.assertEqual(len({next(iter(found)) for found in component_of_net.values()}), len(component_of_net))
                    self.assertEqual(len(set(roots)), len(component_of_net))


class PinoutTests(unittest.TestCase):
    COLUMNS = ["pin", "net", "role", "logical_index", "contact_center_x_mm", "contact_center_y_mm", "physical_side"]

    def test_pinout_rows_are_the_contacts_of_both_boards(self) -> None:
        for design in ({}, dict(NC_DESIGN, scan_order="forward"), dict(NC_DESIGN, scan_order="reverse", connector_side="left")):
            result = _generate(design)
            text = _members(build_exports(result)["project_review_bundle_zip"])["pinout.csv"].decode("ascii")
            reader = csv.DictReader(io.StringIO(text))
            self.assertEqual(reader.fieldnames, self.COLUMNS)
            rows = list(reader)
            by_side = {board["physical_side"]: board for board in result["boards"].values()}
            counts = {side: len(board["layers"]["top_copper"]["pads"]) for side, board in by_side.items()}
            self.assertEqual([row["physical_side"] for row in rows], ["top"] * counts["top"] + ["bottom"] * counts["bottom"])
            for side, board in by_side.items():
                pads = sorted(board["layers"]["top_copper"]["pads"], key=lambda pad: pad["pin"])
                board_rows = [row for row in rows if row["physical_side"] == side]
                with self.subTest(design=design, board=board["id"]):
                    for row, pad in zip(board_rows, pads):
                        index = "" if pad["kind"] == "connector_nc_pad" else str(int(pad["net"].split("_")[1]))
                        center = _center(pad)
                        self.assertEqual(
                            (row["pin"], row["net"], row["role"], row["logical_index"]),
                            (str(pad["pin"]), pad["net"], board["role"], index),
                        )
                        self.assertAlmostEqual(float(row["contact_center_x_mm"]), center[0], delta=1e-6)
                        self.assertAlmostEqual(float(row["contact_center_y_mm"]), center[1], delta=1e-6)
                    # Pins run along the contact row: pin 1 at position 1 (ascending) or P (descending).
                    order = result["design"]["channel_order"][board["role"]]
                    first = pads[0]
                    self.assertEqual(first["position"], 1 if order == "ascending" else len(pads))


class ArtifactNameTests(unittest.TestCase):
    def test_names_carry_the_build_id_and_match_the_manifest(self) -> None:
        for design in ({}, {"project_name": "触觉传感器", "row_fpc_position": "bottom", "rows": 4, "columns": 6}):
            result = _generate(design)
            build_id = result["manifest"]["build_id"]
            top = result["design"]["role_mapping"]["top"]
            bottom = result["design"]["role_mapping"]["bottom"]
            names = artifact_filenames(result)
            self.assertEqual(
                names,
                {
                    "top_fpc_gerber_zip": f"{build_id}-top-{top}-direct-gerber.zip",
                    "bottom_fpc_gerber_zip": f"{build_id}-bottom-{bottom}-direct-gerber.zip",
                    "project_review_bundle_zip": f"{build_id}-project-review.zip",
                },
            )
            bundle = _members(build_exports(result)["project_review_bundle_zip"])
            manifest = json.loads(bundle["manifest.json"])
            self.assertEqual({key: entry["filename"] for key, entry in manifest["artifacts"].items()}, names)
            self.assertTrue({f"gerbers/{names[key]}" for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip")} <= set(bundle))
        with self.assertRaises(ExportError):
            artifact_filenames({"manifest": {"build_id": 'x"; rm -rf'}, "boards": result["boards"]})

    def test_http_downloads_use_the_manifest_names(self) -> None:
        stderr = mock.patch("sys.stderr", io.StringIO())
        stderr.start()
        self.addCleanup(stderr.stop)
        server = app.AppServer(("127.0.0.1", 0))
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        # The browser posts the canonical design of a result; its own export
        # is the reference (the same request gives the same review bundle).
        result = _generate(_generate({"rows": 5, "columns": 7, "row_fpc_position": "bottom"})["design"])
        exports = build_exports(result)
        names = artifact_filenames(result)
        downloads = {}
        routes = (("top-gerber", "top_fpc_gerber_zip"), ("bottom-gerber", "bottom_fpc_gerber_zip"), ("project", "project_review_bundle_zip"))
        for route, key in routes:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=30)
            try:
                body = json.dumps(result["design"])
                connection.request("POST", f"/api/export/{route}", body=body, headers={"Content-Type": "application/json"})
                response = connection.getresponse()
                body = response.read()
                with self.subTest(route=route):
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.getheader("Content-Disposition"), f'attachment; filename="{names[key]}"')
                    self.assertIn(result["manifest"]["build_id"], names[key])
                    self.assertEqual(response.getheader("X-Build-Id"), result["manifest"]["build_id"])
                    self.assertEqual(body, exports[key])
                downloads[key] = body
            finally:
                connection.close()
        manifest = json.loads(_members(downloads["project_review_bundle_zip"])["manifest.json"])
        self.assertEqual({key: entry["filename"] for key, entry in manifest["artifacts"].items()}, names)


class ArchiveAndAttributeTests(unittest.TestCase):
    def test_zip_members_are_stored_with_fixed_metadata(self) -> None:
        result = _generate(NC_DESIGN)
        exports = build_exports(result)
        archives = dict(exports)
        for name, data in _members(exports["project_review_bundle_zip"]).items():
            if name.startswith("gerbers/"):
                archives[name] = data
        self.assertEqual(len(archives), 5)
        for label, data in archives.items():
            with self.subTest(archive=label), zipfile.ZipFile(io.BytesIO(data)) as archive:
                infos = archive.infolist()
                self.assertEqual([info.filename for info in infos], sorted(info.filename for info in infos))
                self.assertIsNone(archive.testzip())
                for info in infos:
                    self.assertEqual(info.compress_type, zipfile.ZIP_STORED, info.filename)
                    self.assertEqual(info.compress_size, info.file_size, info.filename)
                    self.assertEqual(info.date_time, ZIP_TIME)
                    self.assertEqual((info.create_system, info.external_attr >> 16, info.flag_bits), (3, 0o100644, 0))

    def test_every_gerber_carries_its_x2_attributes(self) -> None:
        self.assertEqual(EXPORTER_VERSION, "direct-gerber-pure-stdlib/0.3.0")
        functions = {
            ".GTL": ("Copper,L1,Top", "Positive"),
            ".GTS": ("Soldermask,Top", "Negative"),
            ".GKO": ("Profile,NP", "Positive"),
            ".GBSL": ("Other,BottomStiffener", "Positive"),
        }
        result = _generate({"rows": 4, "columns": 20, "connector": {"row_pins": 8}})
        exports = build_exports(result)
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            for name, data in _members(exports[key]).items():
                if not name.endswith(GERBER_SUFFIXES):
                    continue
                with self.subTest(artifact=key, file=name):
                    attributes = {}
                    for line in data.decode("ascii").splitlines():
                        if line.startswith("G04 #@! TF."):
                            attribute, _, value = line[len("G04 #@! "):-1].partition(",")
                            self.assertNotIn(attribute, attributes)
                            attributes[attribute] = value
                    function, polarity = functions[name[name.rindex("."):]]
                    self.assertEqual(
                        attributes,
                        {
                            "TF.GenerationSoftware": "TactileFPC,direct-gerber,0.3.0",
                            "TF.SameCoordinates": result["manifest"]["build_id"],
                            "TF.FileFunction": function,
                            "TF.FilePolarity": polarity,
                        },
                    )


class ReviewBundleTests(unittest.TestCase):
    def test_bundle_is_complete_and_verifiable_on_its_own(self) -> None:
        # Everything below uses the bundle bytes only, as a third party would.
        bundle = _members(build_exports(_generate({"rows": 6, "columns": 18, "connector": {"row_pins": 8}}))["project_review_bundle_zip"])
        manifest = json.loads(bundle["manifest.json"])
        self.assertEqual(manifest["format"], "tactile-fpc-export-manifest/v2")
        self.assertEqual((manifest["generator"], manifest["exporter"]), (GENERATOR_VERSION, EXPORTER_VERSION))
        counts = json.loads(bundle["validation.json"])["counts"]
        self.assertEqual(
            manifest["checks"],
            {
                "error_count": 0, "warning_count": counts["warning_count"], "drc_version": DRC_VERSION,
                "boards_equal_engine_generation": True, "files_read_back": True,
            },
        )
        documents = ("design.json", "profile.json", "validation.json", "pinout.csv", "derived-layout.json")
        for member in (*documents, "previews/top_fpc.svg", "previews/bottom_fpc.svg"):
            self.assertIn(member, bundle)
        design, profile = json.loads(bundle["design.json"]), json.loads(bundle["profile.json"])
        self.assertEqual(manifest["design_sha256"], _sha(_canonical(design).encode()))
        self.assertEqual(manifest["design_sha256"], _sha(bundle["design.json"].rstrip(b"\n")))
        self.assertEqual(manifest["profile_sha256"], _sha(_canonical(profile).encode()))
        # The default design's diagonal Row bus is built with the surface profile (P5-diagonal-bus.md section 20).
        self.assertEqual(profile, load_profile("surface_matrix_v1"))
        self.assertEqual(manifest["profile"], {"id": profile["id"], "revision": profile["revision"]})
        # The generic default is the diagonal Row bus (P5-diagonal-bus.md section 18): its version is hashed too.
        identity = {key: manifest[key] for key in ("design_sha256", "profile_sha256", "generator", "exporter", "row_bus")}
        self.assertEqual(manifest["build_sha256"], _sha(_canonical(identity).encode()))
        self.assertTrue(manifest["build_id"].endswith("-" + manifest["build_sha256"][:12]))
        self.assertEqual(set(manifest["bundle_files"]), set(bundle) - {"manifest.json"})
        for name, entry in manifest["bundle_files"].items():
            self.assertEqual((entry["sha256"], entry["bytes"]), (_sha(bundle[name]), len(bundle[name])), name)
        layout = json.loads(bundle["derived-layout.json"])
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            artifact = manifest["artifacts"][key]
            data = bundle[f"gerbers/{artifact['filename']}"]
            self.assertEqual((artifact["sha256"], artifact["bytes"]), (_sha(data), len(data)))
            inner = _members(data)
            self.assertEqual(set(artifact["files"]), set(inner))
            for name, entry in artifact["files"].items():
                self.assertEqual(entry["sha256"], _sha(inner[name]), name)
            board_manifest = json.loads(inner["manifest.json"])
            for field in ("build_id", "build_sha256", "design_sha256", "profile_sha256", "generator", "exporter", "profile"):
                self.assertEqual(board_manifest[field], manifest[field], field)
            self.assertEqual(set(board_manifest["files"]), set(inner) - {"manifest.json"})
            board = next(board for board in layout["boards"].values() if board["id"] == board_manifest["board_id"])
            self.assertEqual((board["physical_side"], board["role"]), (board_manifest["physical_side"], board_manifest["role"]))
            self.assertEqual(key, f"{board['physical_side']}_fpc_gerber_zip")

    def test_validation_report_explains_the_manifest_counts(self) -> None:
        # A flat request (schema version defaulted) with a high fill factor.
        flat = generate_design({"rows": 4, "columns": 5, "taxel_width_mm": 1.7})
        self.assertTrue(flat["ok"], flat["validation"]["errors"])
        codes = [issue["code"] for issue in flat["validation"]["warnings"]]
        self.assertIn("W_SCHEMA_VERSION_DEFAULTED", codes)
        self.assertIn("W_HIGH_FILL_FACTOR", codes)
        exports = build_exports(flat)
        report = json.loads(_members(exports["project_review_bundle_zip"])["validation.json"])
        self.assertEqual(report["warnings"], flat["validation"]["warnings"])
        self.assertEqual(report["normalization"], flat["validation"]["normalization"])
        self.assertEqual((report["build_id"], report["errors"]), (flat["manifest"]["build_id"], []))
        self.assertEqual(report["request_warning_codes"], sorted(REQUEST_WARNING_CODES))
        request = [code for code in codes if code in REQUEST_WARNING_CODES]
        self.assertEqual(
            report["counts"],
            {"error_count": 0, "warning_count": flat["manifest"]["checks"]["warning_count"], "request_warning_count": len(request)},
        )
        self.assertEqual(report["counts"]["warning_count"] + len(request), len(codes))
        review = json.loads(_members(exports["project_review_bundle_zip"])["manifest.json"])
        self.assertEqual(review["checks"]["warning_count"], report["counts"]["warning_count"])
        # The same design written canonically has no request warning, the same
        # build and byte-identical Gerbers.
        canonical = generate_design(flat["design"])
        self.assertEqual(canonical["manifest"]["build_id"], flat["manifest"]["build_id"])
        again = build_exports(canonical)
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            self.assertEqual(again[key], exports[key])
        counts = json.loads(_members(again["project_review_bundle_zip"])["validation.json"])["counts"]
        self.assertEqual((counts["warning_count"], counts["request_warning_count"]), (report["counts"]["warning_count"], 0))


class DeterminismTests(unittest.TestCase):
    DESIGNS = ({}, {"rows": 5, "columns": 17, "connector": {"row_pins": 8}, "connector_side": "left", "scan_order": "reverse"})
    SCRIPT = (
        "import hashlib, json, sys\n"
        "from engine import generate_design\n"
        "from exporters import build_exports\n"
        "designs = json.loads(sys.argv[1])\n"
        "digests = [{key: hashlib.sha256(data).hexdigest() for key, data in build_exports(generate_design(design)).items()} for design in designs]\n"
        "print(json.dumps(digests))\n"
    )

    def test_bytes_are_identical_across_processes_and_hash_seeds(self) -> None:
        expected = [{key: _sha(data) for key, data in build_exports(generate_design(design)).items()} for design in self.DESIGNS]
        for seed in ("0", "4242"):
            environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
            completed = subprocess.run(
                [sys.executable, "-B", "-c", self.SCRIPT, json.dumps(self.DESIGNS)],
                cwd=str(ROOT), env=environment, capture_output=True, text=True, timeout=300, check=True,
            )
            with self.subTest(seed=seed):
                self.assertEqual(json.loads(completed.stdout), expected)


if __name__ == "__main__":
    unittest.main()
