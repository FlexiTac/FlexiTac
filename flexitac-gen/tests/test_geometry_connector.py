"""Connector tail regressions against the reader connectors (audit C3, M1).

THD0515-32CL-SN / FFC05001-16SBB: 0.5 mm pitch, FPC width 0.5 x (P + 1),
first contact centre one pitch from the side, 0.30 mm contacts 4.0 mm long
starting 0.30 mm from the tip, R0.30 tip corners, 6.0 mm stiffened zone.
"""

from __future__ import annotations

import copy
import io
import json
import math
import unittest
import zipfile
from unittest import mock

from engine import generate_design as _engine_generate_design, load_profile
from exporters import build_exports

try:
    import geometry_checks as gc
except ImportError:  # run as ``python -m unittest tests.test_geometry_connector``
    from tests import geometry_checks as gc

try:
    from geometry_checks import straight_channel
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel


def generate_design(design=None, *args, **kwargs):
    """``engine.generate_design`` on the straight Row channel, which these tests measure (the generic template's default is
    the diagonal Row bus since claude/specs/masked-field/P5-diagonal-bus.md section 18; geometry_checks.straight_channel)."""

    return _engine_generate_design(straight_channel(design), *args, **kwargs)

EPS = 1e-6


def _boards(**design):
    result = generate_design(design)
    if not result["ok"]:
        raise AssertionError(result["validation"]["errors"])
    return result


class ConnectorTailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_profile()
        cls.connector = cls.profile["connector"]

    def _tail_frame(self, board):
        """Tail side x-range and tip y of a board generated with its tail at the bottom."""

        outline = board["outline"]["points"]
        tip = min(point[1] for point in outline)
        pads = [gc.bounds(pad) for pad in board["layers"]["top_copper"]["pads"]]
        center = sum((pad[0] + pad[2]) / 2 for pad in pads) / len(pads)
        level = tip + self.connector["contact_tip_clearance_mm"] + self.connector["contact_length_mm"] / 2
        width = gc.cross_section(outline, level, center)
        hits = sorted(
            a[0] + (b[0] - a[0]) * (level - a[1]) / (b[1] - a[1])
            for a, b in gc.edges(outline)
            if (a[1] > level) != (b[1] > level)
        )
        left = max(hit for hit in hits if hit <= center)
        return tip, left, width, pads

    def test_tail_width_and_contacts_follow_the_connector_drawing(self) -> None:
        pitch = self.connector["pad_pitch_mm"]
        cases = (
            dict(rows=12, columns=32),
            dict(rows=12, columns=32, connector={"row_pins": 16, "column_pins": 32}),
            dict(rows=1, columns=1),
            dict(rows=3, columns=17, connector={"row_pins": 64, "column_pins": 40}),
        )
        for design in cases:
            result = _boards(**design)
            for board in result["boards"].values():
                pins = board["tail"]["connector_pins"]
                with self.subTest(design=design, board=board["id"]):
                    tip, left, width, pads = self._tail_frame(board)
                    self.assertAlmostEqual(width, (pins + 1) * pitch, delta=EPS)
                    self.assertLessEqual(abs(width - (pins + 1) * pitch), self.connector["tail_width_tolerance_mm"])
                    self.assertEqual(len(pads), pins)
                    centers = sorted((pad[0] + pad[2]) / 2 for pad in pads)
                    self.assertAlmostEqual(centers[0] - left, self.connector["contact_center_to_side_edge_mm"], delta=EPS)
                    for first, second in zip(centers, centers[1:]):
                        self.assertAlmostEqual(second - first, pitch, delta=EPS)
                    for pad in pads:
                        self.assertAlmostEqual(pad[2] - pad[0], self.connector["pad_width_mm"], delta=EPS)
                        self.assertAlmostEqual(pad[3] - pad[1], self.connector["contact_length_mm"], delta=EPS)
                        self.assertAlmostEqual(pad[1] - tip, self.connector["contact_tip_clearance_mm"], delta=EPS)

    def test_default_tails_match_the_reader_connector_drawings(self) -> None:
        # Values restated from the drawings (not read from the profile):
        # THD0515-32CL FPC width 0.5 x (32 + 1) = 16.5 +/- 0.07 mm, 0.30 mm
        # contacts exposed 4.00 mm from the tip, 2-R0.30 tip corners, 6.00 mm
        # thick zone; the 12-pin reference tail is 6.500 mm wide and the
        # 16-pin FFC05001 tail 0.5 x (16 + 1) = 8.5 mm with contacts >= 3.00 mm.
        for design, expected in (({}, {"row": 6.5, "column": 16.5}), ({"connector": {"row_pins": 16}}, {"row": 8.5, "column": 16.5})):
            result = _boards(**design)
            for key, width in expected.items():
                board = result["boards"][key]
                tail = board["tail"]
                with self.subTest(design=design, board=key):
                    self.assertAlmostEqual(tail["width_mm"], width, places=6)
                    _, _, measured, pads = self._tail_frame(board)
                    self.assertAlmostEqual(measured, width, delta=EPS)
                    self.assertEqual((tail["contact_width_mm"], tail["contact_length_mm"]), (0.3, 4.0))
                    self.assertEqual((tail["contact_start_from_tip_mm"], tail["first_contact_center_from_side_mm"]), (0.3, 0.5))
                    self.assertEqual((tail["tip_corner_radius_mm"], tail["stiffener_length_mm"]), (0.3, 6.0))
                    for pad in pads:
                        self.assertAlmostEqual(pad[3] - pad[1], 4.0, delta=EPS)
                        self.assertAlmostEqual(pad[2] - pad[0], 0.3, delta=EPS)

    def test_tail_tip_corners_are_rounded(self) -> None:
        radius = self.connector["tail_tip_corner_radius_mm"]
        step = math.radians(self.profile["outline"]["arc_segment_max_angle_deg"])
        board = generate_design()["boards"]["column"]
        tip, left, width, _ = self._tail_frame(board)
        outline = board["outline"]["points"]
        for corner_x, center_x in ((left, left + radius), (left + width, left + width - radius)):
            center = (center_x, tip + radius)
            near = [point for point in outline if abs(point[0] - corner_x) < radius + EPS and point[1] < tip + radius + EPS]
            self.assertGreaterEqual(len(near), 2)
            self.assertFalse(any(math.dist(point, (corner_x, tip)) < EPS for point in outline))
            for point in near:
                # Arc vertices are circumscribed: never inside the true R0.3 arc.
                distance = math.dist(point, center)
                self.assertGreaterEqual(distance, radius - EPS)
                self.assertLessEqual(distance, radius / math.cos(step / 2) + EPS)

    def test_unused_connector_positions_are_isolated_nc_contacts(self) -> None:
        for order in ("forward", "reverse"):
            self._check_nc_contacts(order)

    def _check_nc_contacts(self, scan_order: str) -> None:
        result = _boards(rows=3, columns=4, connector={"row_pins": 6, "column_pins": 9}, scan_order=scan_order)
        routing = self.profile["routing"]
        for board, channels, pins, stem in ((result["boards"]["row"], 3, 6, "ROW"), (result["boards"]["column"], 4, 9, "COL")):
            copper = board["layers"]["top_copper"]
            pads = sorted(copper["pads"], key=lambda pad: pad["position"])
            with self.subTest(order=scan_order, board=board["id"]):
                self.assertEqual([pad["position"] for pad in pads], list(range(1, pins + 1)))
                # Channel k always occupies position k (channel_order moves no
                # copper).  Connector pins run monotonically along the contact
                # row, from position 1 (ascending) or position P (descending),
                # and NC contacts are named after their own pin.
                expected = list(range(1, pins + 1)) if scan_order == "forward" else list(range(pins, 0, -1))
                self.assertEqual([pad["pin"] for pad in pads], expected)
                self.assertEqual([pad["net"] for pad in pads[:channels]], [f"{stem}_{index:02d}" for index in range(1, channels + 1)])
                self.assertEqual([pad["net"] for pad in pads[channels:]], [f"NC_{pin:02d}" for pin in expected[channels:]])
                self.assertEqual({pad["kind"] for pad in pads[channels:]}, {"connector_nc_pad"})
                routed = {route["net"] for route in copper["routes"]} | {electrode["net"] for electrode in copper["electrodes"]}
                for pad in pads[channels:]:
                    self.assertNotIn(pad["net"], routed)
                    box = gc.bounds(pad)
                    for route in copper["routes"]:
                        gap = min(gc.segment_box_distance(a, b, box) for a, b in zip(route["points"], route["points"][1:])) - route["width_mm"] / 2
                        self.assertGreaterEqual(gap, routing["min_pad_to_trace_mm"] - EPS)
                    for other in pads:
                        if other is not pad:
                            gap = math.hypot(
                                max(0.0, gc.bounds(other)[0] - box[2], box[0] - gc.bounds(other)[2]),
                                max(0.0, gc.bounds(other)[1] - box[3], box[1] - gc.bounds(other)[3]),
                            )
                            self.assertGreaterEqual(gap, routing["min_pad_space_mm"] - EPS)
                self.assertEqual(board["metrics"]["channel_count"], channels)
                self.assertEqual(board["metrics"]["contact_count"], pins)
                self.assertTrue(board["verification"]["checks"]["connectivity"]["passed"])

    def test_connector_pin_counts_are_validated(self) -> None:
        maximum = self.connector["maximum_pins"]
        for connector, field in (
            ({"row_pins": 11}, "connector.row_pins"),
            ({"row_pins": maximum + 1}, "connector.row_pins"),
            ({"column_pins": 31}, "connector.column_pins"),
            ({"column_pins": "32"}, "connector.column_pins"),
            ({"row_pins": True}, "connector.row_pins"),
            ({"row_pins": 16.5}, "connector.row_pins"),
        ):
            result = generate_design({"connector": connector})
            with self.subTest(connector=connector):
                self.assertFalse(result["ok"])
                errors = [issue for issue in result["validation"]["errors"] if issue["code"] == "E_CONNECTOR_PINS"]
                self.assertEqual([issue["field"] for issue in errors], [field])
        self.assertTrue(generate_design({"connector": {"row_pins": 16, "column_pins": maximum}})["ok"])
        bad = generate_design({"connector": "16 pins"})
        self.assertIn("E_CONNECTOR_OBJECT", {issue["code"] for issue in bad["validation"]["errors"]})

    def test_contact_window_is_one_gang_opening_from_the_tip_edge(self) -> None:
        expansion = self.profile["coverlay"]["coverlay_expansion_mm"]
        for design in ({}, {"connector": {"row_pins": 16}}, {"rows": 1, "columns": 1}):
            result = _boards(**design)
            for board in result["boards"].values():
                with self.subTest(design=design, board=board["id"]):
                    tip, left, width, pads = self._tail_frame(board)
                    nets = {pad["net"] for pad in board["layers"]["top_copper"]["pads"]}
                    windows = [
                        opening
                        for opening in board["layers"]["top_coverlay_openings"]
                        if any(gc.bounds(opening)[0] - EPS <= pad[0] and pad[2] <= gc.bounds(opening)[2] + EPS and gc.bounds(opening)[1] - EPS <= pad[1] and pad[3] <= gc.bounds(opening)[3] + EPS for pad in pads)
                    ]
                    self.assertEqual(len(windows), 1)
                    window = gc.bounds(windows[0])
                    self.assertEqual(set(windows[0]["nets"]), nets)
                    self.assertAlmostEqual(window[1], tip, delta=EPS)
                    contact_end = tip + self.connector["contact_tip_clearance_mm"] + self.connector["contact_length_mm"]
                    self.assertAlmostEqual(window[3], contact_end + expansion, delta=EPS)
                    for pad in pads:
                        self.assertTrue(window[0] - EPS <= pad[0] and pad[2] <= window[2] + EPS)
                    self.assertTrue(gc.polygon_inside(gc.box_polygon(window), board["outline"]["points"]))

    def test_stiffener_is_a_fixed_connector_zone_flush_with_the_tail(self) -> None:
        length = self.profile["tail"]["stiffener_length_mm"]
        stack = self.profile["stackup"]
        for tail in (7.0, 20.0, 80.0):
            result = _boards(tail_length_mm=tail)
            for board in result["boards"].values():
                with self.subTest(tail=tail, board=board["id"]):
                    (stiffener,) = board["layers"]["bottom_stiffener"]
                    points = stiffener["points"]
                    tip, left, width, _ = self._tail_frame(board)
                    xs = [point[0] for point in points]
                    ys = [point[1] for point in points]
                    self.assertAlmostEqual(max(ys) - min(ys), length, delta=EPS)
                    self.assertAlmostEqual(min(ys), tip, delta=EPS)
                    self.assertAlmostEqual(max(xs) - min(xs), width, delta=EPS)
                    self.assertTrue(gc.polygon_inside(points, board["outline"]["points"]))
                    # Flush: every stiffener vertex on the tip/side edges is an outline vertex.
                    outline = {tuple(point) for point in board["outline"]["points"]}
                    self.assertTrue(all(tuple(point) in outline for point in points if point[1] < max(ys) - EPS))
                    self.assertEqual(
                        (stiffener["side"], stiffener["material"], stiffener["thickness_mm"]),
                        (stack["stiffener_side"], stack["stiffener_material"], stack["stiffener_thickness_mm"]),
                    )
                    # After the stiffener, both tail sides stay straight (full
                    # width) for at least the clearance before the outline widens.
                    for side in (left, left + width):
                        spans = [
                            (min(a[1], b[1]), max(a[1], b[1]))
                            for a, b in gc.edges(board["outline"]["points"])
                            if abs(a[0] - side) < EPS and abs(b[0] - side) < EPS
                        ]
                        reach = max(high for low, high in spans if low - EPS <= max(ys) <= high + EPS)
                        self.assertGreaterEqual(reach - max(ys), self.profile["tail"]["stiffener_end_clearance_mm"] - EPS)
                    self.assertEqual(
                        board["verification"]["checks"]["stiffener_end_clearance"]["required_mm"],
                        self.profile["tail"]["stiffener_end_clearance_mm"],
                    )

    def test_emitted_stiffener_matches_the_layout_inside_the_outline(self) -> None:
        # Review finding F6: decode the emitted GBSL (and GKO) rather than the
        # in-memory layout; a GBSL shifted 0.5 mm out of the tail survived.
        mils_per_mm = 1 / 0.0254
        for design in ({}, {"connector_side": "right"}, {"connector_side": "top", "row_fpc_position": "bottom"},
                       {"rows": 3, "columns": 17, "connector_side": "left", "connector": {"row_pins": 9, "column_pins": 40}}):
            result = _boards(**design)
            exports = build_exports(result)
            for board in result["boards"].values():
                with self.subTest(design=design, board=board["id"]):
                    with zipfile.ZipFile(io.BytesIO(exports[f"{board['physical_side']}_fpc_gerber_zip"])) as archive:
                        names = archive.namelist()
                        gbsl = archive.read(next(name for name in names if name.endswith(".GBSL"))).decode("ascii")
                        gko = archive.read("Gerber_BoardOutlineLayer.GKO").decode("ascii")
                        metadata = json.loads(archive.read("jlcpcb.json"))
                    _, regions = gc.decode_gerber(gbsl)
                    strokes, _ = gc.decode_gerber(gko)
                    (stiffener,) = board["layers"]["bottom_stiffener"]
                    (region,) = regions
                    self.assertTrue(gc.same_ring(region, stiffener["points"], 2e-6))
                    outline = max(strokes, key=len)[:-1]  # the outer contour, closed back to its start
                    self.assertTrue(gc.polygon_inside(region, outline, tolerance=2e-6))
                    (entry,) = metadata["fpcStiffeners"]
                    path = entry["path"][0][0]
                    self.assertEqual(path[2], "L")
                    values = [value for value in path if value != "L"]
                    ring = [(x / mils_per_mm, y / mils_per_mm) for x, y in zip(values[0::2], values[1::2])][:-1]
                    self.assertTrue(gc.same_ring(ring, region, 2e-6))

    def test_tail_rules_are_independent_of_route_edge_rules(self) -> None:
        # Formerly one pad_edge_clearance_mm set the tail side margin, the tip
        # margin and the Row route-to-edge distance at once.
        self.assertNotIn("pad_edge_clearance_mm", self.connector)
        profile = copy.deepcopy(self.profile)
        profile["connector"]["contact_tip_clearance_mm"] = 0.35
        with mock.patch("engine.core.load_profile", return_value=profile):
            shifted = generate_design()
        base = generate_design()
        self.assertTrue(shifted["ok"], shifted["validation"]["errors"])
        for key in ("row", "column"):
            moved = shifted["boards"][key]
            fixed = base["boards"][key]
            self.assertAlmostEqual(
                moved["verification"]["checks"]["route_to_outline"]["measured_mm"],
                fixed["verification"]["checks"]["route_to_outline"]["measured_mm"],
            )
            first = min(gc.bounds(pad)[1] for pad in moved["layers"]["top_copper"]["pads"])
            self.assertAlmostEqual(first - min(point[1] for point in moved["outline"]["points"]), 0.35, delta=EPS)


if __name__ == "__main__":
    unittest.main()
