"""SVG top view (audit H2, SVG part; decision D18).

The preview is the copper-side top view in the Gerber frame: the layout
coordinates are drawn inside one Y-flip group, so a Gerber point (x, y)
appears at screen (x, T - y).  The tests parse the SVG and apply its
transform themselves.
"""

from __future__ import annotations

import io
import itertools
import re
import unittest
import xml.etree.ElementTree as ET
import zipfile

from engine import generate_design
from engine.geometry import rect_bounds
from exporters import build_exports

NS = "{http://www.w3.org/2000/svg}"
EPS = 1e-6


class _Svg:
    def __init__(self, text: str) -> None:
        self.text = text
        self.root = ET.fromstring(text)
        self.view_box = tuple(map(float, self.root.get("viewBox").split()))
        group = self.root.find(NS + "g")
        self.matrix = tuple(map(float, re.fullmatch(r"matrix\(([^)]*)\)", group.get("transform")).group(1).split()))
        self.group = group

    def screen(self, x: float, y: float) -> tuple[float, float]:
        a, b, c, d, e, f = self.matrix
        return (a * x + c * y + e, b * x + d * y + f)

    def screen_box(self, box) -> tuple[float, float, float, float]:
        (x0, y0), (x1, y1) = self.screen(box[0], box[1]), self.screen(box[2], box[3])
        return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

    def rects(self, css_class: str) -> list[tuple[float, float, float, float]]:
        boxes = []
        for rect in self.group.iter(NS + "rect"):
            if rect.get("class") == css_class:
                x, y, w, h = (float(rect.get(key)) for key in ("x", "y", "width", "height"))
                boxes.append(self.screen_box((x, y, x + w, y + h)))
        return boxes


def _center(box) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


class TopViewTests(unittest.TestCase):
    def test_the_tail_is_drawn_on_its_side_as_seen_on_screen_with_pin_1_marked(self) -> None:
        for side, row_position, order in itertools.product(("bottom", "top", "left", "right"), ("top", "bottom"), ("forward", "reverse")):
            result = generate_design({"rows": 4, "columns": 18, "connector_side": side, "row_fpc_position": row_position, "scan_order": order})
            self.assertTrue(result["ok"], result["validation"]["errors"])
            for board in result["boards"].values():
                with self.subTest(side=side, row_position=row_position, order=order, board=board["id"]):
                    svg = _Svg(board["svg"])
                    self.assertEqual(svg.root.get("data-view"), "top")
                    # A pure Y flip: a top view, not a mirror image.
                    self.assertEqual(svg.matrix[:4], (1.0, 0.0, 0.0, -1.0))
                    vx, vy, vw, vh = svg.view_box
                    outline = svg.screen_box(_bounds(board["outline"]["points"]))
                    self.assertTrue(vx <= outline[0] and outline[2] <= vx + vw and vy <= outline[1] and outline[3] <= vy + vh)
                    # Contacts are on the requested side of the board on screen.
                    pads = svg.rects("pad")
                    self.assertEqual(len(pads), len(board["layers"]["top_copper"]["pads"]))
                    contacts = [_center(box) for box in pads]
                    cx = sum(x for x, _ in contacts) / len(contacts)
                    cy = sum(y for _, y in contacts) / len(contacts)
                    middle = _center(outline)
                    observed = {"bottom": cy > middle[1], "top": cy < middle[1], "left": cx < middle[0], "right": cx > middle[0]}
                    self.assertTrue(observed[side], (side, observed))
                    self.assertEqual(sum(observed.values()), 2)
                    # Every drawn copper rectangle is the layout rectangle under the same mapping.
                    expected = sorted(svg.screen_box(rect_bounds(pad)) for pad in board["layers"]["top_copper"]["pads"])
                    for got, want in zip(sorted(pads), expected):
                        self.assertLess(max(abs(p - q) for p, q in zip(got, want)), EPS)
                    # data-active-region: the taxel field in user units after the flip.
                    active = board["grid_registration"]["active_region"]
                    box = svg.screen_box((active["x"], active["y"], active["x"] + active["width"], active["y"] + active["height"]))
                    region = tuple(map(float, svg.root.get("data-active-region").split()))
                    self.assertLess(max(abs(p - q) for p, q in zip(region, (box[0], box[1], box[2] - box[0], box[3] - box[1]))), EPS)
                    # The pin-1 marker sits beyond the tip, in line with the pin-1 contact.
                    marker = svg.group.find(NS + "polygon[@class='pin1-marker']")
                    self.assertIsNotNone(marker)
                    points = [svg.screen(*map(float, pair.split(","))) for pair in marker.get("points").split()]
                    pin1 = next(pad for pad in board["layers"]["top_copper"]["pads"] if pad["pin"] == 1)
                    pin1_center = _center(svg.screen_box(rect_bounds(pin1)))
                    axis = 0 if side in ("bottom", "top") else 1
                    self.assertLess(abs(points[0][axis] - pin1_center[axis]), EPS)
                    beyond = {"bottom": min(y for _, y in points) > outline[3], "top": max(y for _, y in points) < outline[1],
                              "left": max(x for x, _ in points) < outline[0], "right": min(x for x, _ in points) > outline[2]}
                    self.assertTrue(beyond[side])
                    self.assertIn(pin1["net"], marker.find(NS + "title").text)
                    self.assertIn("TOP VIEW &#183; copper side", svg.text)

    def test_default_boards_match_the_gerber_top_view_chirality(self) -> None:
        # In the copper-side top view of the default boards (tails at the
        # bottom, ascending order) pin 1 is the leftmost contact, ROW_01 is the
        # upper Row electrode and COL_01 the leftmost Column electrode.
        result = generate_design()
        for key, first in (("row", "ROW_01"), ("column", "COL_01")):
            board = result["boards"][key]
            svg = _Svg(board["svg"])
            pads = sorted(board["layers"]["top_copper"]["pads"], key=lambda pad: svg.screen(pad["x"], pad["y"])[0])
            self.assertEqual(pads[0]["pin"], 1)
            electrodes = board["layers"]["top_copper"]["electrodes"]
            screen = {electrode["net"]: _center(svg.screen_box(rect_bounds(electrode))) for electrode in electrodes}
            if key == "row":
                self.assertEqual(min(screen, key=lambda net: screen[net][1]), first)
            else:
                self.assertEqual(min(screen, key=lambda net: screen[net][0]), first)

    def test_the_view_label_fits_inside_the_view_box_and_clear_of_the_board(self) -> None:
        designs = (
            {"rows": 1, "columns": 1},
            {"rows": 4, "columns": 4},
            {"rows": 1, "columns": 1, "connector_side": "top"},
            {"rows": 1, "columns": 2, "connector_side": "left"},
            {"rows": 3, "columns": 20, "pitch_x_mm": 0.9, "taxel_width_mm": 0.4},
            {},
        )
        for data in designs:
            result = generate_design(data)
            self.assertTrue(result["ok"], result["validation"]["errors"])
            for board in result["boards"].values():
                with self.subTest(design=data, board=board["id"]):
                    svg = _Svg(board["svg"])
                    label = svg.root.find(NS + "text")
                    self.assertEqual(label.get("class"), "view-label")
                    size, x, y = (float(label.get(key)) for key in ("font-size", "x", "y"))
                    text = "".join(label.itertext())
                    self.assertTrue(text.startswith("TOP VIEW"))
                    vx, vy, vw, vh = svg.view_box
                    # A generous 0.6 em per character for sans-serif text (Chromium
                    # measures about 0.51 em), capitals up to 1 em, descenders 0.25 em.
                    box = (x, y - size, x + 0.6 * len(text) * size, y + 0.25 * size)
                    self.assertTrue(vx - EPS <= box[0] and box[2] <= vx + vw + EPS and vy - EPS <= box[1], (box, svg.view_box))
                    outline = svg.screen_box(_bounds(board["outline"]["points"]))
                    self.assertLess(box[3], outline[1])
                    marker = svg.group.find(NS + "polygon[@class='pin1-marker']")
                    marker_y = [svg.screen(*map(float, pair.split(",")))[1] for pair in marker.get("points").split()]
                    self.assertLess(box[3], min(marker_y))

    def test_each_route_piece_is_drawn_with_its_own_width(self) -> None:
        # Re-audit N18: the preview hard-coded a 0.254 mm stroke.  Since 2026-10-15
        # each net is a thin fan-out piece and a wide tail piece, drawn as such.
        result = generate_design({"routing": {"trace_width_mm": 0.1524, "trace_space_mm": 0.1}})
        for board in result["boards"].values():
            svg = _Svg(board["svg"])
            lines = [line for line in svg.group.iter(NS + "polyline") if line.get("class") == "route"]
            routes = board["layers"]["top_copper"]["routes"]
            with self.subTest(board=board["id"]):
                self.assertEqual(len(lines), len(routes))
                for line, route in zip(lines, routes):
                    self.assertEqual(float(line.get("stroke-width")), route["width_mm"], route["net"])
                    points = [tuple(map(float, pair.split(","))) for pair in line.get("points").split()]
                    self.assertEqual(points, [tuple(point) for point in route["points"]], route["net"])
                self.assertEqual({float(line.get("stroke-width")) for line in lines}, {0.1524, 0.254})
                # No style rule overrides the per-route widths.
                style = svg.root.find(NS + "style").text
                route_rule = re.search(r"\.route\{([^}]*)\}", style).group(1)
                self.assertNotIn("stroke-width", route_rule)

    def test_svg_is_ascii_xml_and_the_review_bundle_ships_the_same_svgs(self) -> None:
        result = generate_design({"project_name": "触觉传感器"})
        exports = build_exports(result)
        with zipfile.ZipFile(io.BytesIO(exports["project_review_bundle_zip"])) as archive:
            for board in result["boards"].values():
                board["svg"].encode("ascii")
                ET.fromstring(board["svg"])
                self.assertEqual(archive.read(f"previews/{board['physical_side']}_fpc.svg"), board["svg"].encode("utf-8"))


def _bounds(points) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


if __name__ == "__main__":
    unittest.main()
