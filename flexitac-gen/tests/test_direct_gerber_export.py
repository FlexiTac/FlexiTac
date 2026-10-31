"""Tests for deterministic, source-independent Direct Gerber candidate exports."""

from __future__ import annotations

import hashlib
import io
import itertools
import json
import math
import re
import unittest
from typing import Any, Mapping
from zipfile import ZipFile

from engine import generate_design
from exporters import EXPORTER_VERSION, ExportError, artifact_filenames, build_exports


GERBER_LAYERS = {
    "Gerber_TopLayer.GTL",
    "Gerber_TopSolderMaskLayer.GTS",
    "Gerber_BoardOutlineLayer.GKO",
}
_VERTEX = re.compile(r"X(-?\d+)Y(-?\d+)D0([12])\*")
_APERTURE = re.compile(r"%ADD(\d+)C,([0-9.]+)\*%")
_SELECTION = re.compile(r"D(\d+)\*")
# Gerber coordinates are integers of 1e-6 mm, and the engine rounds rotated
# corners separately from pad centres, so allow two least-significant digits.
_TOLERANCE = 2e-6


def _stiffener_layer(thickness: float) -> str:
    """EasyEDA Pro's name of the bottom PI stiffener layer of one thickness."""

    return f"Gerber_BottomStiffenerLayer_pib_{thickness:g}.GBSL"


def _zip_members(data: bytes) -> dict[str, bytes]:
    with ZipFile(io.BytesIO(data)) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise AssertionError(f"bad ZIP member: {bad_member}")
        return {name: archive.read(name) for name in archive.namelist()}


def _decode_gerber(text: str) -> tuple[list, list, list]:
    """Decode the exporter's RS-274X subset into strokes, regions and polarities.

    Strokes are ``(aperture diameter, points)`` and regions are closed vertex
    lists, in millimetres.  Any other command fails loudly, so a format change
    cannot leave the geometric assertions with nothing to check.
    """

    apertures: dict[str, float] = {}
    strokes: list = []
    regions: list = []
    polarities: list[str] = []
    diameter = None
    contour = None
    for line in text.splitlines():
        vertex = _VERTEX.fullmatch(line)
        aperture = _APERTURE.fullmatch(line)
        selection = _SELECTION.fullmatch(line)
        if vertex:
            point = (int(vertex[1]) / 1_000_000, int(vertex[2]) / 1_000_000)
            if contour is not None:
                contour.append(point)
            elif vertex[3] == "2":
                strokes.append((diameter, [point]))
            else:
                strokes[-1][1].append(point)
        elif aperture:
            apertures[aperture[1]] = float(aperture[2])
        elif selection:
            diameter = apertures[selection[1]]
        elif line in ("%LPD*%", "%LPC*%"):
            polarities.append(line[3])
        elif line == "G36*":
            contour = []
        elif line == "G37*":
            regions.append(contour)
            contour = None
        elif not (line.startswith("G04 ") or line in ("%FSLAX46Y46*%", "%MOMM*%", "G01*", "M02*")):
            raise AssertionError(f"unexpected Gerber command: {line!r}")
    return strokes, regions, polarities


def _rectangle(contour: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Return the bounds of a closed four-corner region with axis-aligned edges."""

    edges = zip(contour, contour[1:])
    if len(contour) != 5 or contour[0] != contour[-1] or any((a[0] == b[0]) == (a[1] == b[1]) for a, b in edges):
        raise AssertionError(f"region is not a closed axis-aligned rectangle: {contour}")
    xs = [point[0] for point in contour]
    ys = [point[1] for point in contour]
    return (min(xs), min(ys), max(xs), max(ys))


def _lower_left_bounds(rectangle: Mapping[str, Any], grow: float = 0.0) -> tuple[float, float, float, float]:
    return (
        rectangle["x"] - grow,
        rectangle["y"] - grow,
        rectangle["x"] + rectangle["width_mm"] + grow,
        rectangle["y"] + rectangle["height_mm"] + grow,
    )


def _center_bounds(pad: Mapping[str, Any], grow: float = 0.0) -> tuple[float, float, float, float]:
    half_width = pad["width_mm"] / 2 + grow
    half_height = pad["height_mm"] / 2 + grow
    return (pad["x"] - half_width, pad["y"] - half_height, pad["x"] + half_width, pad["y"] + half_height)


def _point_box_distance(point: list[float], box: tuple[float, float, float, float]) -> float:
    x0, y0, x1, y1 = box
    return math.hypot(max(x0 - point[0], 0.0, point[0] - x1), max(y0 - point[1], 0.0, point[1] - y1))


def _point_segment_distance(point: tuple[float, float], start: list[float], end: list[float]) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_squared = dx * dx + dy * dy
    t = 0.0
    if length_squared:
        t = max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_squared))
    return math.hypot(point[0] - start[0] - t * dx, point[1] - start[1] - t * dy)


def _segment_box_distance(start: list[float], end: list[float], box: tuple[float, float, float, float]) -> float:
    x0, y0, x1, y1 = box
    # Liang-Barsky clipping: a non-empty parameter interval means contact.
    low, high = 0.0, 1.0
    dx, dy = end[0] - start[0], end[1] - start[1]
    for p, q in ((-dx, start[0] - x0), (dx, x1 - start[0]), (-dy, start[1] - y0), (dy, y1 - start[1])):
        if p == 0:
            if q < 0:
                break
        else:
            t = q / p
            if p < 0:
                low = max(low, t)
            else:
                high = min(high, t)
            if low > high:
                break
    else:
        return 0.0
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    return min(
        _point_box_distance(start, box),
        _point_box_distance(end, box),
        *(_point_segment_distance(corner, start, end) for corner in corners),
    )


def _contains(outer: tuple[float, float, float, float], inner: tuple[float, float, float, float]) -> bool:
    return (
        outer[0] - _TOLERANCE <= inner[0]
        and outer[1] - _TOLERANCE <= inner[1]
        and inner[2] <= outer[2] + _TOLERANCE
        and inner[3] <= outer[3] + _TOLERANCE
    )


def _box_gap(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> float:
    return math.hypot(
        max(0.0, second[0] - first[2], first[0] - second[2]),
        max(0.0, second[1] - first[3], first[1] - second[3]),
    )


class DirectGerberExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = generate_design()
        self.assertTrue(self.result["ok"], self.result["validation"])
        self.exports = build_exports(self.result)
        # The stiffener layer is named from the stiffener objects (the profile's PI thickness).
        self.stiffener_layer = _stiffener_layer(self.result["profile"]["stackup"]["stiffener_thickness_mm"])
        self.gerbers = GERBER_LAYERS | {self.stiffener_layer}

    def test_builds_two_independent_gerber_zips_and_review_bundle(self) -> None:
        self.assertEqual(
            set(self.exports),
            {"top_fpc_gerber_zip", "bottom_fpc_gerber_zip", "project_review_bundle_zip"},
        )
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            self.assertEqual(
                set(_zip_members(self.exports[key])), self.gerbers | {"jlcpcb.json", "netlist.ipc", "ORDER_NOTES.txt", "manifest.json"}
            )

        names = artifact_filenames(self.result)
        review = _zip_members(self.exports["project_review_bundle_zip"])
        self.assertEqual(
            set(review),
            {
                "design.json",
                "derived-layout.json",
                "manifest.json",
                "validation.json",
                "profile.json",
                "pinout.csv",
                "ORDER_NOTES.txt",
                "previews/top_fpc.svg",
                "previews/bottom_fpc.svg",
                # The default design is the diagonal Row bus (P5-diagonal-bus.md section 18), whose boards carry the
                # full field's taxel records: its taxel map.
                "taxels.csv",
                f"gerbers/{names['top_fpc_gerber_zip']}",
                f"gerbers/{names['bottom_fpc_gerber_zip']}",
            },
        )
        self.assertIn(b"<svg", review["previews/top_fpc.svg"])
        self.assertIn(b"<svg", review["previews/bottom_fpc.svg"])
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            self.assertEqual(review[f"gerbers/{names[key]}"], self.exports[key])

    def test_every_gerber_has_required_header_and_terminator(self) -> None:
        build_id = self.result["manifest"]["build_id"]
        for package_key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            members = _zip_members(self.exports[package_key])
            for filename in self.gerbers:
                text = members[filename].decode("ascii")
                self.assertIn("%FSLAX46Y46*%", text)
                self.assertIn("%MOMM*%", text)
                self.assertTrue(text.endswith("M02*\n"), filename)
                # X2 attributes (audit L9): vendor, application, version; one coordinate set per build.
                self.assertIn(f"G04 #@! TF.GenerationSoftware,TactileFPC,direct-gerber,{EXPORTER_VERSION.rpartition('/')[2]}*\n", text)
                self.assertIn(f"G04 #@! TF.SameCoordinates,{build_id}*\n", text)
            self.assertIn("TF.FileFunction,Copper,L1,Top", members["Gerber_TopLayer.GTL"].decode("ascii"))
            self.assertIn("TF.FilePolarity,Negative", members["Gerber_TopSolderMaskLayer.GTS"].decode("ascii"))
            self.assertIn("TF.FileFunction,Profile,NP", members["Gerber_BoardOutlineLayer.GKO"].decode("ascii"))

    def test_geometry_counts_match_the_same_derived_board_geometry(self) -> None:
        by_side = {board["physical_side"]: board for board in self.result["boards"].values()}
        for side, package_key in (("top", "top_fpc_gerber_zip"), ("bottom", "bottom_fpc_gerber_zip")):
            board = by_side[side]
            copper = board["layers"]["top_copper"]
            members = _zip_members(self.exports[package_key])
            gtl = members["Gerber_TopLayer.GTL"].decode("ascii")
            gts = members["Gerber_TopSolderMaskLayer.GTS"].decode("ascii")
            gbsl = members[self.stiffener_layer].decode("ascii")
            self.assertEqual(gtl.count("G36*"), len(copper["electrodes"]) + len(copper["pads"]))
            self.assertEqual(gts.count("G36*"), len(board["layers"]["top_coverlay_openings"]))
            self.assertEqual(gbsl.count("G36*"), len(board["layers"]["bottom_stiffener"]))
            # Every route is a real Gerber draw, never represented as a fill.
            self.assertGreaterEqual(gtl.count("D01*"), len(copper["routes"]))
            # Every outer contour and routed cutout is independently closed.
            expected_contours = 1 + len(board["outline"].get("cutouts", []))
            self.assertEqual(members["Gerber_BoardOutlineLayer.GKO"].decode("ascii").count("D02*"), expected_contours)

    def test_jlc_stiffener_metadata_comes_from_the_stiffener_objects(self) -> None:
        # The exporter derives layer, material, thickness and Gerber name from
        # each stiffener object (audit M7); the default is bottom PI at the
        # profile's thickness (0.225 mm since 2026-10-14).
        thickness = self.result["profile"]["stackup"]["stiffener_thickness_mm"]
        by_side = {board["physical_side"]: board for board in self.result["boards"].values()}
        for side, package_key in (("top", "top_fpc_gerber_zip"), ("bottom", "bottom_fpc_gerber_zip")):
            metadata = json.loads(_zip_members(self.exports[package_key])["jlcpcb.json"])
            stiffeners = metadata["fpcStiffeners"]
            (layout,) = by_side[side]["layers"]["bottom_stiffener"]
            self.assertEqual((layout["side"], layout["material"], layout["thickness_mm"]), ("bottom", "polyimide", thickness))
            self.assertEqual(len(stiffeners), 1)
            stiffener = stiffeners[0]
            self.assertEqual(stiffener["gerber"], _stiffener_layer(layout["thickness_mm"]))
            self.assertEqual(stiffener["layer"], layout["side"])
            self.assertEqual(stiffener["material"], "pi")
            self.assertEqual(stiffener["thickness"], f"{thickness:g}")
            linear_path = stiffener["path"][0][0]
            self.assertEqual(linear_path[2], "L")
            self.assertEqual(linear_path[:2], linear_path[-2:])

    def test_review_manifest_is_explicitly_not_native_or_production_ready(self) -> None:
        review = _zip_members(self.exports["project_review_bundle_zip"])
        manifest = json.loads(review["manifest.json"])
        self.assertEqual(manifest["status"], "direct_gerber_jlc_review_candidate")
        self.assertFalse(manifest["production_ready"])
        self.assertFalse(manifest["easyeda_native_export"])
        self.assertTrue(manifest["requires_final_jlc_review"])
        self.assertTrue(manifest["source_independent"])
        self.assertIn("prior Gerber", manifest["does_not_read"])

    def test_zip_bytes_are_deterministic(self) -> None:
        again = build_exports(generate_design())
        for key in self.exports:
            self.assertEqual(self.exports[key], again[key])
            self.assertEqual(
                hashlib.sha256(self.exports[key]).hexdigest(), hashlib.sha256(again[key]).hexdigest()
            )

    def test_invalid_design_is_never_exported(self) -> None:
        invalid = generate_design({"matrix": {"pitch_x_mm": 1.0, "taxel_width_mm": 0.9}})
        self.assertFalse(invalid["ok"])
        with self.assertRaises(ExportError):
            build_exports(invalid)

    def test_non_default_channel_counts_produce_matching_geometry(self) -> None:
        result = generate_design(
            {
                "matrix": {"rows": 3, "columns": 4, "pitch_x_mm": 2.0, "pitch_y_mm": 2.0,
                           "taxel_width_mm": 1.3, "taxel_height_mm": 1.3},
                "tail": {"length_mm": 9.0, "row_side": "right", "column_side": "left"},
            }
        )
        self.assertTrue(result["ok"], result["validation"])
        exports = build_exports(result)
        by_side = {board["physical_side"]: board for board in result["boards"].values()}
        for side, package_key in (("top", "top_fpc_gerber_zip"), ("bottom", "bottom_fpc_gerber_zip")):
            gtl = _zip_members(exports[package_key])["Gerber_TopLayer.GTL"].decode("ascii")
            copper = by_side[side]["layers"]["top_copper"]
            self.assertEqual(gtl.count("G36*"), len(copper["electrodes"]) + len(copper["pads"]))

    def _assert_regions(self, regions: list, expected: list, layer: str) -> None:
        """Match decoded regions to expected bounds by geometry, not file order."""

        emitted = [_rectangle(contour) for contour in regions]
        self.assertEqual(len(emitted), len(expected), f"{layer} region count")
        for name, bounds in expected:
            match = next((box for box in emitted if all(abs(a - b) <= _TOLERANCE for a, b in zip(box, bounds))), None)
            self.assertIsNotNone(match, f"{layer}: nothing emitted at {bounds} for {name}")
            emitted.remove(match)

    def test_emitted_copper_and_openings_match_the_layout_in_every_orientation(self) -> None:
        # Decode the emitted artwork rather than trusting the in-memory layout:
        # pads are centre-anchored, electrodes and coverlay openings lower-left.
        cases = [(self.result, self.exports)]
        for columns, side, row_position in itertools.product((4, 17), ("bottom", "right", "top", "left"), ("top", "bottom")):
            design = {"rows": 3, "columns": columns, "connector_side": side, "row_fpc_position": row_position}
            if columns == 4 and row_position == "bottom":
                # Larger connectors than channels add isolated NC contacts.
                design["connector"] = {"row_pins": 6, "column_pins": 9}
            result = generate_design(design)
            self.assertTrue(result["ok"], result["validation"])
            cases.append((result, build_exports(result)))
        profile = self.result["profile"]
        connector = profile["connector"]
        expansion = profile["coverlay"]["coverlay_expansion_mm"]
        pad_gap = profile["routing"]["min_pad_space_mm"]
        # Hold the designed contact-lead clearance (0.223 mm), which is above
        # the routing.min_pad_to_trace_mm rule; any drift towards the
        # neighbouring net fails.
        # The contact leads are the wide tail pieces (the gold-finger trace width).
        trace_width = profile["routing"]["finger_trace_width_mm"]
        pad_to_trace = connector["pad_pitch_mm"] - (connector["pad_width_mm"] + trace_width) / 2
        self.assertGreaterEqual(pad_to_trace, profile["routing"]["min_pad_to_trace_mm"])
        nc_boards = 0
        for result, exports in cases:
            columns = result["design"]["matrix"]["columns"]
            for board in result["boards"].values():
                with self.subTest(board=board["id"], side=board["tail"]["side"], columns=columns):
                    members = _zip_members(exports[f"{board['physical_side']}_fpc_gerber_zip"])
                    strokes, regions, polarities = _decode_gerber(members["Gerber_TopLayer.GTL"].decode("ascii"))
                    _, openings, opening_polarities = _decode_gerber(members["Gerber_TopSolderMaskLayer.GTS"].decode("ascii"))
                    outline, _, _ = _decode_gerber(members["Gerber_BoardOutlineLayer.GKO"].decode("ascii"))
                    self.assertEqual(polarities, ["D"])
                    self.assertEqual(opening_polarities, ["D"])
                    copper = board["layers"]["top_copper"]
                    electrodes, pads, routes = copper["electrodes"], copper["pads"], copper["routes"]
                    self.assertTrue(all(item["anchor"] == "lower_left" for item in electrodes))
                    self.assertTrue(all(item["anchor"] == "center" for item in pads))

                    # Emitted strokes are the layout routes in order, so stroke i carries routes[i]["net"].
                    self.assertEqual(len(strokes), len(routes))
                    for (diameter, points), route in zip(strokes, routes):
                        self.assertAlmostEqual(diameter, route["width_mm"], delta=_TOLERANCE, msg=route["net"])
                        self.assertEqual(len(points), len(route["points"]), route["net"])
                        for point, intended in zip(points, route["points"]):
                            self.assertLessEqual(math.dist(point, intended), _TOLERANCE, route["net"])
                    # Two pieces per net: the tail piece leaves the contact, the fan-out piece reaches the electrode.
                    tail_of = {route["net"]: stroke for stroke, route in zip(strokes, routes) if route["segment"] == "tail"}
                    fanout_of = {route["net"]: stroke for stroke, route in zip(strokes, routes) if route["segment"] == "fanout"}
                    self.assertEqual(set(tail_of), set(fanout_of))
                    for net, (_, points) in tail_of.items():
                        self.assertEqual(points[-1], fanout_of[net][1][0], net)  # the shared junction

                    self._assert_regions(
                        regions,
                        [(e["net"], _lower_left_bounds(e)) for e in electrodes] + [(p["net"], _center_bounds(p)) for p in pads],
                        "GTL",
                    )
                    self._assert_regions(
                        openings,
                        [(o["kind"], _lower_left_bounds(o)) for o in board["layers"]["top_coverlay_openings"]],
                        "GTS",
                    )
                    # Coverlay rules on the emitted windows (audit L6): every
                    # electrode keeps the full expansion, every contact is
                    # fully exposed, and no bridge is narrower than the rule.
                    windows = [_rectangle(contour) for contour in openings]
                    for electrode in electrodes:
                        grown = _lower_left_bounds(electrode, expansion)
                        self.assertTrue(any(_contains(window, grown) for window in windows), electrode["net"])
                    for pad in pads:
                        self.assertTrue(any(_contains(window, _center_bounds(pad)) for window in windows), pad["net"])
                    for first, second in itertools.combinations(windows, 2):
                        self.assertGreaterEqual(_box_gap(first, second), profile["coverlay"]["coverlay_min_bridge_mm"] - _TOLERANCE)
                    for electrode in electrodes:
                        end = fanout_of[electrode["net"]][1][-1]
                        self.assertLessEqual(_point_box_distance(end, _lower_left_bounds(electrode)), _TOLERANCE, electrode["net"])

                    edges = [segment for _, points in outline for segment in zip(points, points[1:])]
                    for pad in pads:
                        label = f"{pad['net']} pin {pad['pin']}"
                        box = _center_bounds(pad)
                        x0, y0, x1, y1 = box
                        if pad["net"].startswith("NC_"):
                            # Unused connector positions are isolated dummies.
                            nc_boards += 1
                            self.assertNotIn(pad["net"], tail_of, label)
                        else:
                            # Each trace starts at the middle of one pad edge.
                            midpoints = (((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1), (x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2))
                            start = tail_of[pad["net"]][1][0]
                            self.assertLessEqual(min(math.dist(start, midpoint) for midpoint in midpoints), _TOLERANCE, label)
                        for (diameter, points), route in zip(strokes, routes):
                            if route["net"] != pad["net"]:
                                gap = min(_segment_box_distance(a, b, box) for a, b in zip(points, points[1:])) - diameter / 2
                                self.assertGreaterEqual(gap, pad_to_trace - _TOLERANCE, f"{label} to {route['net']}")
                        edge_gap = min(_segment_box_distance(a, b, box) for a, b in edges)
                        self.assertGreaterEqual(edge_gap, profile["routing"]["copper_to_edge_mm"] - _TOLERANCE, label)
                    for first, second in itertools.combinations(pads, 2):
                        gap = _box_gap(_center_bounds(first), _center_bounds(second))
                        self.assertGreaterEqual(gap, pad_gap - _TOLERANCE, f"{first['net']} to {second['net']}")
        self.assertGreater(nc_boards, 0)


if __name__ == "__main__":
    unittest.main()
