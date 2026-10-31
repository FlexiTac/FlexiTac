"""Chirality, pin 1 and the stack view for every tail side and both role mappings (audit H4, M5; D23).

The expectations are derived from first principles, not from the engine's
transforms: each board is built with its tail pointing down (-Y) and then
turned as a whole, without mirroring, so that the tail exits the requested
side.  Seen from the copper side with the tail pointing down, contact
position 1 is the leftmost contact, ``ROW_01`` the Row electrode farthest
from the tail and ``COL_01`` the leftmost Column electrode; pin 1 is position
1 for ``ascending`` and position P for ``descending``.  A rotation keeps that
handedness on every side; a mirror (audit mutants f1, f2 and t) reverses it.

The vectors used below, in each board's Gerber frame (mm, Y up):
``OUT`` points from the board toward its tail, ``UP = -OUT`` from the tail
into the board, and ``RIGHT`` is ``UP`` turned a quarter turn clockwise (the
direction in which contact positions increase).
"""

from __future__ import annotations

import csv
import io
import itertools
import unittest
import zipfile

from engine import generate_design as _engine_generate_design
from exporters import artifact_filenames, build_exports

try:
    import geometry_checks as gc
except ImportError:  # run as a package
    from tests import geometry_checks as gc

try:
    from geometry_checks import straight_channel
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel


def generate_design(design=None, *args, **kwargs):
    """``engine.generate_design`` on the straight Row channel, which these tests measure (the generic template's default is
    the diagonal Row bus since claude/specs/masked-field/P5-diagonal-bus.md section 18; geometry_checks.straight_channel)."""

    return _engine_generate_design(straight_channel(design), *args, **kwargs)

OUT = {"bottom": (0.0, -1.0), "right": (1.0, 0.0), "top": (0.0, 1.0), "left": (-1.0, 0.0)}
OPPOSITE = {"bottom": "top", "top": "bottom", "left": "right", "right": "left"}
ROWS, COLUMNS = 3, 5
# Two isolated NC contacts on each tail.
ROW_PINS, COLUMN_PINS = 5, 7
CONTACT = (0.3, 4.0)
EPS = 1e-6


def _up(side: str) -> tuple[float, float]:
    out = OUT[side]
    return (-out[0], -out[1])


def _right(side: str) -> tuple[float, float]:
    up = _up(side)
    return (up[1], -up[0])


def _dot(point, vector) -> float:
    return point[0] * vector[0] + point[1] * vector[1]


def _center(box) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _design(row_side: str, column_side: str, top: str, order: str) -> dict:
    return {
        "matrix": {"rows": ROWS, "columns": COLUMNS},
        "connector": {"row_pins": ROW_PINS, "column_pins": COLUMN_PINS},
        "tail": {"row_side": row_side, "column_side": column_side},
        "role_mapping": {"top": top, "bottom": "columns" if top == "rows" else "rows"},
        "channel_order": {"rows": order, "columns": order},
    }


def _expected_contacts(stem: str, channels: int, pins: int, order: str) -> list[tuple[int, str]]:
    """``(pin, net)`` of the contact positions 1..P (channel k at position k)."""

    answer = []
    for position in range(1, pins + 1):
        pin = position if order == "ascending" else pins - position + 1
        answer.append((pin, f"{stem}_{position:02d}" if position <= channels else f"NC_{pin:02d}"))
    return answer


def _netlist_contacts(text: str) -> list[dict]:
    """J1 test records of an IPC-D-356A netlist (fixed columns, read independently of the exporter)."""

    records = []
    for line in text.splitlines():
        if line.startswith("327") and line[20:26].strip() == "J1":
            records.append({"net": line[3:17].strip(), "pin": int(line[27:31]), "x": int(line[42:49]) * 0.001, "y": int(line[50:57]) * 0.001})
    return records


def _members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


class LayoutChiralityTests(unittest.TestCase):
    """The layout model of both boards, 4 shared tail sides x 2 role mappings x 2 channel orders."""

    def test_contacts_electrodes_and_tails_keep_their_handedness_on_every_side(self) -> None:
        for side, top, order in itertools.product(OUT, ("rows", "columns"), ("ascending", "descending")):
            result = generate_design(_design(side, side, top, order))
            self.assertTrue(result["ok"], result["validation"]["errors"])
            up, right = _up(side), _right(side)
            for key, board in result["boards"].items():
                with self.subTest(side=side, top=top, order=order, board=key):
                    role = board["role"]
                    stem, channels, pins = ("ROW", ROWS, ROW_PINS) if role == "rows" else ("COL", COLUMNS, COLUMN_PINS)
                    self.assertEqual(board["tail"]["side"], side)
                    self.assertEqual(board["physical_side"], "top" if role == top else "bottom")
                    self.assertEqual(board["id"], f"{board['physical_side']}_{role}_fpc")
                    copper = board["layers"]["top_copper"]
                    outline = board["outline"]["points"]
                    middle = _center(gc.bounds({"anchor": "lower_left", **_bbox(outline)}))
                    # The contacts are at the requested edge, their long side along UP.
                    contacts = sorted(copper["pads"], key=lambda pad: _dot(_center(gc.bounds(pad)), right))
                    for pad in contacts:
                        box = gc.bounds(pad)
                        self.assertGreater(_dot(_center(box), OUT[side]), _dot(middle, OUT[side]) + 1.0)
                        along_up = abs(_dot((box[2] - box[0], box[3] - box[1]), up))
                        self.assertAlmostEqual(along_up, CONTACT[1], delta=EPS)
                    # Positions increase along RIGHT; pins follow channel_order; channel k sits at position k.
                    self.assertEqual([pad["position"] for pad in contacts], list(range(1, pins + 1)))
                    self.assertEqual([(pad["pin"], pad["net"]) for pad in contacts], _expected_contacts(stem, channels, pins, order))
                    electrodes = copper["electrodes"]
                    if role == "rows":
                        # ROW_01 is the electrode farthest from the tail; rows run along RIGHT.
                        ranked = sorted(electrodes, key=lambda electrode: -_dot(_center(gc.bounds(electrode)), up))
                        long_axis = right
                    else:
                        ranked = sorted(electrodes, key=lambda electrode: _dot(_center(gc.bounds(electrode)), right))
                        long_axis = up
                    self.assertEqual([electrode["net"] for electrode in ranked], [f"{stem}_{k:02d}" for k in range(1, channels + 1)])
                    for electrode in electrodes:
                        box = gc.bounds(electrode)
                        extent = (box[2] - box[0], box[3] - box[1])
                        self.assertGreater(abs(_dot(extent, long_axis)), abs(_dot(extent, (long_axis[1], -long_axis[0]))))
                    # The Row tail is flush with the board's start along RIGHT; the Column tail is centred on the taxel field.
                    tail = board["tail"]["bounds"]
                    active = board["grid_registration"]["active_region"]
                    offset = _dot(_center(_box(tail)), right) - _dot(_center(_box(active)), right)
                    if role == "rows":
                        self.assertLess(offset, -1.0)
                        self.assertAlmostEqual(min(_dot(point, right) for point in outline), min(_dot(c, right) for c in _corners(tail)), delta=EPS)
                    else:
                        self.assertAlmostEqual(offset, 0.0, delta=EPS)

    def test_mixed_sides_half_a_turn_apart_reverse_one_index_direction(self) -> None:
        # API only (the UI shares one connector side): the boards stay orthogonal
        # and register, but in the shared frame one board's channel order runs
        # the other way, and the tails exit opposite edges.
        for row_side, top in itertools.product(OUT, ("rows", "columns")):
            column_side = OPPOSITE[row_side]
            result = generate_design(_design(row_side, column_side, top, "ascending"))
            self.assertTrue(result["ok"], result["validation"]["errors"])
            with self.subTest(row_side=row_side, column_side=column_side, top=top):
                row, column = result["boards"]["row"], result["boards"]["column"]
                registration = row["verification"]["registration"]
                self.assertTrue(registration["passed"], registration)
                self.assertTrue(registration["orthogonal"])
                # In the Row board's frame the Column board's RIGHT points the other way.
                right = _right(row_side)
                self.assertEqual(_right(column_side), (-right[0], -right[1]))
                columns = sorted(column["layers"]["top_copper"]["electrodes"], key=lambda electrode: _dot(_center(gc.bounds(electrode)), right))
                self.assertEqual([electrode["net"] for electrode in columns], [f"COL_{k:02d}" for k in range(COLUMNS, 0, -1)])
                self.assertEqual(column["tail"]["side"], column_side)


class EmittedChiralityTests(unittest.TestCase):
    """The same handedness read back from the Gerber ZIPs and the pinout, independently of the layout JSON."""

    def test_emitted_contacts_netlist_and_pinout_agree_on_pin_1(self) -> None:
        for side, top, order in itertools.product(OUT, ("rows", "columns"), ("ascending", "descending")):
            result = generate_design(_design(side, side, top, order))
            self.assertTrue(result["ok"], result["validation"]["errors"])
            exports = build_exports(result)
            names = artifact_filenames(result)
            pinout = list(csv.DictReader(io.StringIO(_members(exports["project_review_bundle_zip"])["pinout.csv"].decode("ascii"))))
            right = _right(side)
            for physical_side in ("top", "bottom"):
                role = top if physical_side == "top" else ("columns" if top == "rows" else "rows")
                stem, channels, pins = ("ROW", ROWS, ROW_PINS) if role == "rows" else ("COL", COLUMNS, COLUMN_PINS)
                key = f"{physical_side}_fpc_gerber_zip"
                with self.subTest(side=side, top=top, order=order, physical_side=physical_side):
                    self.assertIn(f"-{physical_side}-{role}-direct-gerber.zip", names[key])
                    members = _members(exports[key])
                    _, regions = gc.decode_gerber(members["Gerber_TopLayer.GTL"].decode("ascii"))
                    boxes = [_bbox_of(region) for region in regions if len(region) == 4]
                    contacts = [box for box in boxes if sorted((round(box[2] - box[0], 6), round(box[3] - box[1], 6))) == list(CONTACT)]
                    self.assertEqual(len(contacts), pins)
                    contacts.sort(key=lambda box: _dot(_center(box), right))
                    records = _netlist_contacts(members["netlist.ipc"].decode("ascii"))
                    self.assertEqual(len(records), pins)
                    found = []
                    for box in contacts:
                        x, y = _center(box)
                        record = next(record for record in records if abs(record["x"] - x) <= 5e-4 and abs(record["y"] - y) <= 5e-4)
                        found.append((record["pin"], record["net"]))
                    self.assertEqual(found, _expected_contacts(stem, channels, pins, order))
                    # pinout.csv names the same pin at the same contact centre.
                    rows = [row for row in pinout if row["physical_side"] == physical_side]
                    self.assertEqual({row["role"] for row in rows}, {role})
                    for (pin, net), box in zip(found, contacts):
                        row = next(row for row in rows if int(row["pin"]) == pin)
                        self.assertEqual(row["net"], net)
                        self.assertAlmostEqual(float(row["contact_center_x_mm"]), _center(box)[0], delta=EPS)
                        self.assertAlmostEqual(float(row["contact_center_y_mm"]), _center(box)[1], delta=EPS)
                    # The contacts sit at the tail edge of the emitted outline.
                    strokes, _ = gc.decode_gerber(members["Gerber_BoardOutlineLayer.GKO"].decode("ascii"))
                    outline = max(strokes, key=len)
                    tip = max(_dot(point, OUT[side]) for point in outline)
                    for box in contacts:
                        self.assertAlmostEqual(tip - max(_dot(corner, OUT[side]) for corner in _corners(_dict(box))), 0.3, delta=EPS)

    def test_channel_order_assigns_pins_without_moving_copper(self) -> None:
        # D23: channel_order is the pin assignment recorded in netlist.ipc and
        # pinout.csv; the artwork is the same apart from the build id that every
        # Gerber header names (TF.SameCoordinates).
        layers = (".GTL", ".GTS", ".GKO", ".GBSL")
        builds = {}
        for order in ("ascending", "descending"):
            result = generate_design(_design("bottom", "bottom", "rows", order))
            self.assertTrue(result["ok"], result["validation"]["errors"])
            exports = build_exports(result)
            build_id = result["manifest"]["build_id"]
            builds[order] = {
                (key, name): data.replace(build_id.encode("ascii"), b"<build>")
                for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip")
                for name, data in _members(exports[key]).items()
            }
        ascending, descending = builds["ascending"], builds["descending"]
        self.assertEqual(set(ascending), set(descending))
        for (key, name), data in ascending.items():
            with self.subTest(archive=key, member=name):
                if name.endswith(layers) or name == "jlcpcb.json":
                    self.assertEqual(data, descending[(key, name)])
                elif name == "netlist.ipc":
                    self.assertNotEqual(data, descending[(key, name)])


class StackViewTests(unittest.TestCase):
    """The assembly of docs/INTEGRATION.md: the physical bottom board face up, the physical top board
    turned over (copper down) about its tail axis, both registered on the taxel field and seen from above."""

    def _stack(self, side: str, top: str) -> dict[str, dict]:
        result = generate_design(_design(side, side, top, "ascending"))
        self.assertTrue(result["ok"], result["validation"]["errors"])
        views = {}
        for board in result["boards"].values():
            active = board["grid_registration"]["active_region"]
            origin = _center(_box(active))
            # Turning over about the tail axis mirrors the coordinate across UP.
            mirror = board["physical_side"] == "top"
            right = _right(side)

            def view(point, origin=origin, mirror=mirror, right=right):
                u, r = _dot((point[0] - origin[0], point[1] - origin[1]), _up(side)), _dot((point[0] - origin[0], point[1] - origin[1]), right)
                return (-r if mirror else r, u)  # (along RIGHT, along UP) seen from above

            copper = board["layers"]["top_copper"]
            views[board["role"]] = {
                "board": board,
                "tail": view(_center(_box(board["tail"]["bounds"]))),
                "contacts": sorted(((view(_center(gc.bounds(pad))), pad["pin"]) for pad in copper["pads"]), key=lambda item: item[0][0]),
                "electrodes": {electrode["net"]: view(_center(gc.bounds(electrode))) for electrode in copper["electrodes"]},
                "field": (active["width"], active["height"]) if side in ("bottom", "top") else (active["height"], active["width"]),
            }
        return views

    def test_both_tails_exit_the_connector_side_and_the_taxel_grids_coincide(self) -> None:
        for side, top in itertools.product(OUT, ("rows", "columns")):
            with self.subTest(side=side, top=top):
                views = self._stack(side, top)
                rows, columns = views["rows"], views["columns"]
                self.assertEqual(rows["field"], columns["field"])
                for view in (rows, columns):
                    self.assertLess(view["tail"][1], -view["field"][1] / 2)  # beyond the field, toward the tail side
                # Row electrodes run across the stack, Column electrodes along it.
                row_ys = sorted(center[1] for center in rows["electrodes"].values())
                column_xs = sorted(center[0] for center in columns["electrodes"].values())
                self.assertEqual(len(set(round(y, 6) for y in row_ys)), ROWS)
                self.assertEqual(len(set(round(x, 6) for x in column_xs)), COLUMNS)

    def test_the_turned_over_board_is_mirrored_across_its_tail_axis(self) -> None:
        for side in OUT:
            with self.subTest(side=side, top="rows"):
                views = self._stack(side, "rows")
                rows, columns = views["rows"], views["columns"]
                # Rows on top: the Row tail moves to the opposite corner (its own
                # top view has it at the start of RIGHT), the row order is
                # unchanged and the contacts read reversed: pin 1 is the last
                # contact along RIGHT as seen from above.
                self.assertGreater(rows["tail"][0], 1.0)
                ranked = sorted(rows["electrodes"], key=lambda net: -rows["electrodes"][net][1])
                self.assertEqual(ranked, [f"ROW_{k:02d}" for k in range(1, ROWS + 1)])
                self.assertEqual([pin for _, pin in rows["contacts"]], list(range(ROW_PINS, 0, -1)))
                # The face-up Column board looks like its own top view: COL_01 first along RIGHT, pin 1 first.
                ordered = sorted(columns["electrodes"], key=lambda net: columns["electrodes"][net][0])
                self.assertEqual(ordered, [f"COL_{k:02d}" for k in range(1, COLUMNS + 1)])
                self.assertEqual([pin for _, pin in columns["contacts"]], list(range(1, COLUMN_PINS + 1)))
            with self.subTest(side=side, top="columns"):
                views = self._stack(side, "columns")
                rows, columns = views["rows"], views["columns"]
                # Columns on top: COL_01 is the last Column electrode along RIGHT (on
                # the right for bottom tails); the face-up Row board keeps its tail first.
                ordered = sorted(columns["electrodes"], key=lambda net: columns["electrodes"][net][0])
                self.assertEqual(ordered, [f"COL_{k:02d}" for k in range(COLUMNS, 0, -1)])
                self.assertEqual([pin for _, pin in columns["contacts"]], list(range(COLUMN_PINS, 0, -1)))
                self.assertLess(rows["tail"][0], -1.0)
                self.assertEqual([pin for _, pin in rows["contacts"]], list(range(1, ROW_PINS + 1)))


def _box(bounds: dict) -> tuple[float, float, float, float]:
    return (bounds["x"], bounds["y"], bounds["x"] + bounds["width"], bounds["y"] + bounds["height"])


def _bbox(points) -> dict:
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return {"x": min(xs), "y": min(ys), "width_mm": max(xs) - min(xs), "height_mm": max(ys) - min(ys)}


def _bbox_of(points) -> tuple[float, float, float, float]:
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _dict(box) -> dict:
    return {"x": box[0], "y": box[1], "width": box[2] - box[0], "height": box[3] - box[1]}


def _corners(bounds: dict) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = _box(bounds)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


if __name__ == "__main__":
    unittest.main()
