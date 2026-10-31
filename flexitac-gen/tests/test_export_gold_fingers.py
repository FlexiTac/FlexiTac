"""Gold fingers measured on the emitted Gerbers (stage G, 2026-10-14; audit C3, M1).

The contact tail of every exported board is decoded from its GTL, GTS, GKO
and GBSL (tests/geometry_checks.py, not the exporter's reader), turned into a
tail-down frame and measured against the reader-connector drawings
(THD0515-32CL-SN, TXGA FFC05001-16SBB124W5M): 0.5 mm pitch, the outer
contact centres one pitch from the tail sides, width 0.5 x (P + 1),
0.30 x 4.00 mm contacts from 0.30 mm behind the tip, R0.30 tip corners, one
coverlay window over the contacts, and the 6.0 mm PI stiffener flush with
the tip and both sides.  Contacts are found by their place, never by the
order of the regions in the file.
"""

from __future__ import annotations

import io
import json
import math
import unittest
import zipfile

from engine import generate_design, load_profile
from exporters import build_exports

try:
    import geometry_checks as gc
except ImportError:  # run as ``python -m unittest tests.test_export_gold_fingers``
    from tests import geometry_checks as gc

# Restated from the connector drawings (not read from the profile).
PITCH_MM = 0.5
FIRST_CENTER_FROM_SIDE_MM = 0.5
CONTACT_WIDTH_MM = 0.30
CONTACT_LENGTH_MM = 4.00
CONTACT_START_MM = 0.30
TIP_RADIUS_MM = 0.30
STIFFENER_LENGTH_MM = 6.0
THD0515_WIDTH_TOLERANCE_MM = 0.07
EPS = 2e-6  # two least-significant digits of FSLAX46Y46
SIDES = ("bottom", "right", "top", "left")
# Gerber frame -> a frame with the tail pointing down (-y): quarter turns, never mirrored.
_TO_TAIL_DOWN = {
    "bottom": lambda x, y: (x, y),
    "top": lambda x, y: (-x, -y),
    "left": lambda x, y: (-y, x),
    "right": lambda x, y: (y, -x),
}


def _members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _box(points) -> tuple[float, float, float, float]:
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _emitted_tail(board: dict, members: dict[str, bytes]) -> dict:
    """The decoded tail of one board ZIP in the tail-down frame."""

    turn = _TO_TAIL_DOWN[board["tail"]["side"]]

    def local(points):
        return [turn(*point) for point in points]

    _, copper = gc.decode_gerber(members["Gerber_TopLayer.GTL"].decode("ascii"))
    _, windows = gc.decode_gerber(members["Gerber_TopSolderMaskLayer.GTS"].decode("ascii"))
    contours, _ = gc.decode_gerber(members["Gerber_BoardOutlineLayer.GKO"].decode("ascii"))
    (layer,) = [name for name in members if name.endswith(".GBSL")]
    _, stiffeners = gc.decode_gerber(members[layer].decode("ascii"))
    # The outer contour is the one whose bounds hold every other (cutouts are inside).
    outline = local(max(contours, key=lambda contour: (lambda b: (b[2] - b[0]) * (b[3] - b[1]))(_box(contour)))[:-1])
    tip = min(point[1] for point in outline)
    regions = [_box(local(region)) for region in copper]
    # Contacts are the copper regions that start within a millimetre of the tip edge.
    contacts = sorted(box for box in regions if box[1] - tip < 1.0)
    return {
        "outline": outline, "tip": tip, "contacts": contacts, "windows": [_box(local(window)) for window in windows],
        "stiffeners": [local(region) for region in stiffeners], "layer": layer,
        "metadata": json.loads(members["jlcpcb.json"]),
    }


class EmittedGoldFingerTests(unittest.TestCase):
    """For 12, 16 and 32 pins, pins > channels, both role mappings and all four tail sides."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_profile()
        cases = [({"connector_side": side}, {"row": 12, "column": 32}) for side in SIDES]
        cases += [
            ({"rows": 16, "columns": 16}, {"row": 16, "column": 16}),
            # FlexiTac reader: 16-pin rows connector on 12 rows (NC_13..NC_16).
            ({"connector": {"row_pins": 16}, "connector_side": "right"}, {"row": 16, "column": 32}),
            # Pins > channels on both boards, the Column board on top.
            ({"rows": 3, "columns": 17, "connector": {"row_pins": 12, "column_pins": 32}, "connector_side": "top", "row_fpc_position": "bottom"},
             {"row": 12, "column": 32}),
            ({"rows": 5, "columns": 7, "connector": {"row_pins": 16, "column_pins": 12}, "connector_side": "left"}, {"row": 16, "column": 12}),
        ]
        cls.cases = []
        for design, pins in cases:
            result = generate_design(design)
            if not result["ok"]:
                raise AssertionError((design, result["validation"]["errors"]))
            exports = build_exports(result)
            for key, board in result["boards"].items():
                members = _members(exports[f"{board['physical_side']}_fpc_gerber_zip"])
                cls.cases.append((design, key, pins[key], board, _emitted_tail(board, members)))

    def test_the_drawing_values_are_the_profile_values(self) -> None:
        connector, tail = self.profile["connector"], self.profile["tail"]
        self.assertEqual(
            (connector["pad_pitch_mm"], connector["contact_center_to_side_edge_mm"], connector["pad_width_mm"],
             connector["contact_length_mm"], connector["contact_tip_clearance_mm"], connector["tail_tip_corner_radius_mm"],
             tail["stiffener_length_mm"], connector["tail_width_tolerance_mm"]),
            (PITCH_MM, FIRST_CENTER_FROM_SIDE_MM, CONTACT_WIDTH_MM, CONTACT_LENGTH_MM, CONTACT_START_MM, TIP_RADIUS_MM,
             STIFFENER_LENGTH_MM, THD0515_WIDTH_TOLERANCE_MM),
        )
        # Every case is covered: each side, 12/16/32 pins, NC contacts.
        self.assertEqual({board["tail"]["side"] for *_, board, _ in self.cases}, set(SIDES))
        self.assertLessEqual({12, 16, 32}, {pins for _, _, pins, _, _ in self.cases})
        self.assertTrue(any(board["tail"]["connector_channels"] < pins for _, _, pins, board, _ in self.cases))

    def test_contacts_pitch_and_tail_width(self) -> None:
        for design, key, pins, board, tail in self.cases:
            with self.subTest(design=design, board=key):
                contacts = tail["contacts"]
                self.assertEqual(len(contacts), pins)
                for box in contacts:
                    self.assertAlmostEqual(box[2] - box[0], CONTACT_WIDTH_MM, delta=EPS)
                    self.assertAlmostEqual(box[3] - box[1], CONTACT_LENGTH_MM, delta=EPS)
                    self.assertAlmostEqual(box[1] - tail["tip"], CONTACT_START_MM, delta=EPS)
                centers = [(box[0] + box[2]) / 2 for box in contacts]
                for first, second in zip(centers, centers[1:]):
                    self.assertAlmostEqual(second - first, PITCH_MM, delta=EPS)
                # The tail sides where the contacts are, across the middle of the contacts.
                level = tail["tip"] + CONTACT_START_MM + CONTACT_LENGTH_MM / 2
                crossings = sorted(
                    a[0] + (b[0] - a[0]) * (level - a[1]) / (b[1] - a[1])
                    for a, b in gc.edges(tail["outline"]) if (a[1] > level) != (b[1] > level)
                )
                left = max(x for x in crossings if x < centers[0])
                right = min(x for x in crossings if x > centers[-1])
                self.assertAlmostEqual(centers[0] - left, FIRST_CENTER_FROM_SIDE_MM, delta=EPS)
                self.assertAlmostEqual(right - centers[-1], FIRST_CENTER_FROM_SIDE_MM, delta=EPS)
                self.assertAlmostEqual(right - left, PITCH_MM * (pins + 1), delta=EPS)
                self.assertLessEqual(abs(right - left - PITCH_MM * (pins + 1)), THD0515_WIDTH_TOLERANCE_MM)
                self.assertAlmostEqual(right - left, board["tail"]["width_mm"], delta=EPS)
                # The sides are straight from the end of the tip arcs over the whole
                # stiffened zone, so over the whole contact length: the outline edges
                # on each side line cover that stretch without a gap.
                stretch = (tail["tip"] + TIP_RADIUS_MM, tail["tip"] + STIFFENER_LENGTH_MM)
                for edge_x in (left, right):
                    spans = sorted(
                        (min(a[1], b[1]), max(a[1], b[1])) for a, b in gc.edges(tail["outline"])
                        if abs(a[0] - edge_x) < EPS and abs(b[0] - edge_x) < EPS
                    )
                    covered = [list(spans[0])] if spans else []
                    for low, high in spans[1:]:
                        if low <= covered[-1][1] + EPS:
                            covered[-1][1] = max(covered[-1][1], high)
                        else:
                            covered.append([low, high])
                    self.assertTrue(
                        any(low <= stretch[0] + EPS and high >= stretch[1] - EPS for low, high in covered), (edge_x, stretch, covered)
                    )

    def test_rounded_tip_corners(self) -> None:
        step = math.radians(self.profile["outline"]["arc_segment_max_angle_deg"])
        for design, key, pins, board, tail in self.cases:
            with self.subTest(design=design, board=key):
                outline, tip = tail["outline"], tail["tip"]
                left = min(box[0] for box in tail["contacts"]) - (FIRST_CENTER_FROM_SIDE_MM - CONTACT_WIDTH_MM / 2)
                right = max(box[2] for box in tail["contacts"]) + (FIRST_CENTER_FROM_SIDE_MM - CONTACT_WIDTH_MM / 2)
                for corner_x, center_x in ((left, left + TIP_RADIUS_MM), (right, right - TIP_RADIUS_MM)):
                    center = (center_x, tip + TIP_RADIUS_MM)
                    near = [p for p in outline if abs(p[0] - corner_x) <= TIP_RADIUS_MM + EPS and p[1] <= tip + TIP_RADIUS_MM + EPS]
                    self.assertGreaterEqual(len(near), 2)
                    for point in near:
                        # Circumscribed arc vertices: on or just outside the true R0.30 arc.
                        distance = math.dist(point, center)
                        self.assertGreaterEqual(distance, TIP_RADIUS_MM - EPS)
                        self.assertLessEqual(distance, TIP_RADIUS_MM / math.cos(step / 2) + EPS)
                    # The arc meets the side edge and the tip edge, and the square corner is cut
                    # away: no vertex is nearer to it than the arc's circumscribed midpoint.
                    self.assertTrue(any(abs(p[0] - corner_x) <= EPS for p in near))
                    self.assertTrue(any(abs(p[1] - tip) <= EPS for p in near))
                    cut = math.sqrt(2) * TIP_RADIUS_MM - TIP_RADIUS_MM / math.cos(step / 2)
                    self.assertGreaterEqual(min(math.dist(p, (corner_x, tip)) for p in outline), cut - EPS)

    def test_one_coverlay_window_over_all_contacts(self) -> None:
        expansion = self.profile["coverlay"]["coverlay_expansion_mm"]
        for design, key, pins, board, tail in self.cases:
            with self.subTest(design=design, board=key):
                contacts = tail["contacts"]
                row = (min(b[0] for b in contacts), min(b[1] for b in contacts), max(b[2] for b in contacts), max(b[3] for b in contacts))
                (window,) = [w for w in tail["windows"] if w[0] <= row[0] + EPS and w[2] >= row[2] - EPS and w[1] - EPS <= row[1]]
                self.assertAlmostEqual(window[1], tail["tip"], delta=EPS)
                self.assertAlmostEqual(window[3], row[3] + expansion, delta=EPS)
                # The window stops where the R0.30 corners begin: 0.05 mm beside the outer contacts.
                side_margin = FIRST_CENTER_FROM_SIDE_MM - CONTACT_WIDTH_MM / 2 - TIP_RADIUS_MM
                self.assertAlmostEqual(row[0] - window[0], side_margin, delta=EPS)
                self.assertAlmostEqual(window[2] - row[2], side_margin, delta=EPS)

    def test_stiffener_flush_with_the_tip_and_both_sides(self) -> None:
        thickness = self.profile["stackup"]["stiffener_thickness_mm"]
        for design, key, pins, board, tail in self.cases:
            with self.subTest(design=design, board=key):
                (stiffener,) = tail["stiffeners"]
                x0, y0, x1, y1 = _box(stiffener)
                contacts = tail["contacts"]
                left = min(box[0] for box in contacts) - (FIRST_CENTER_FROM_SIDE_MM - CONTACT_WIDTH_MM / 2)
                right = max(box[2] for box in contacts) + (FIRST_CENTER_FROM_SIDE_MM - CONTACT_WIDTH_MM / 2)
                self.assertAlmostEqual(y0, tail["tip"], delta=EPS)
                self.assertAlmostEqual(y1 - y0, STIFFENER_LENGTH_MM, delta=EPS)
                self.assertAlmostEqual(x0, left, delta=EPS)
                self.assertAlmostEqual(x1, right, delta=EPS)
                # Flush: every stiffener vertex below its far edge is an outline vertex (the rounded tip included).
                for point in stiffener:
                    if point[1] < y1 - EPS:
                        self.assertTrue(any(math.dist(point, vertex) <= EPS for vertex in tail["outline"]), point)
                self.assertTrue(gc.polygon_inside(stiffener, tail["outline"], tolerance=EPS))
                # The layer name and jlcpcb.json carry the profile's PI thickness (0.225 mm by default).
                self.assertEqual(tail["layer"], f"Gerber_BottomStiffenerLayer_pib_{thickness:g}.GBSL")
                (entry,) = tail["metadata"]["fpcStiffeners"]
                self.assertEqual((entry["gerber"], entry["material"], entry["thickness"]), (tail["layer"], "pi", f"{thickness:g}"))


if __name__ == "__main__":
    unittest.main()
