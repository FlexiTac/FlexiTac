"""The masked boards' builders (``matrix.mask``, masked-field phase P2).

A masked design of the straight construction classes is built from the
unmasked R x C plan with each electrode trimmed to its span: the Row field
slides toward the channel as far as the lane taper lets, each Row stub ends
at its own electrode, a Column whose taxels stop short of its tail runs its
stub straight down its own centre line, the outlines follow the crossings
(the Row body's far side, the Column body's top) and the merged coverlay
window becomes a polygon (claude/specs/masked-field/PLAN.md).  These tests
pin the two invariants of the plan (a full span gives today's boards byte
for byte; a mask whose rows all reach the Row channel and whose row next to
the Column tail is full keeps today's routes, contacts, gang window,
stiffener and tail) and measure the builders' geometry with predicates of
their own (``tests/geometry_checks.py``): electrode spans, stub ends, the
window rings and the crossing region P (by area and containment), the
outlines (simple, counter-clockwise, the 0.5 mm margin from P), the masked
keys, the SVG, the footprint, the crossings of the stacked boards in every
tail-side and role combination, determinism and the construction-class gate.
The masked semantics of DRC records 11-15 and of the registration are
tested in ``tests/test_mask_drc.py``; here every record and the
registration must pass on the corpus.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import math
import re
import textwrap
import time
import unittest

from engine import check_design, field_footprint, generate_design, load_profile, row_frame_spans, column_frame_spans, row_taper
from engine import core as engine_core
from engine import geometry as engine_geometry
from engine import layout
from exporters import direct_gerber
from surface import place
from engine.core import _canonical_json
from engine.layout import apply_tail_side, build_column_board, build_row_board

try:
    from geometry_checks import bounds, edges, inside_or_on, point_in_polygon, segment_box_distance, segment_distance, segments_cross
    import defaults_of_before
except ImportError:  # run as tests.test_mask_layout
    from tests.geometry_checks import bounds, edges, inside_or_on, point_in_polygon, segment_box_distance, segment_distance, segments_cross
    from tests import defaults_of_before


def setUpModule() -> None:
    # The default electrodes of before (1.4 mm at 2 mm, fill 0.7): this module's pinned numbers were measured with them
    # (tests/defaults_of_before.py; the user's decision of 2026-11-06 made the default fill 0.5).
    defaults_of_before.start()


SURFACE = "surface_matrix_v1"
PROFILE = load_profile(SURFACE)
TIGHT = {"trace_width_mm": 0.1016, "trace_space_mm": 0.1016}
FINE = {"pitch_x_mm": 0.6, "pitch_y_mm": 0.6, "taxel_width_mm": 0.35, "taxel_height_mm": 0.35}
SPARSE = {"pitch_x_mm": 3.0, "pitch_y_mm": 3.0, "taxel_width_mm": 1.0, "taxel_height_mm": 1.0}
ONE_MM = {"pitch_x_mm": 1.0, "pitch_y_mm": 1.0, "taxel_width_mm": 0.7, "taxel_height_mm": 0.7}
_SIDES = ("bottom", "right", "top", "left")
_OPPOSITE = {"bottom": "top", "top": "bottom", "left": "right", "right": "left"}
# The keys only a masked board has (docs/LAYOUT_SCHEMA.md).
MASK_KEYS = (
    ("grid_registration", "taxel_mask"), ("grid_registration", "active_outline"), ("grid_registration", "active_taxel_count"),
    ("construction", "mask_class"), ("metrics", "active_taxel_count"),
)
EPSILON = 1e-6


def _request(rows: int, columns: int, matrix=None, **sections) -> dict:
    return {"template_id": SURFACE, "matrix": {"rows": rows, "columns": columns, **(matrix or {})}, **sections}


def _design(request: dict) -> dict:
    checked = check_design(request)
    assert checked["ok"], checked["validation"]["errors"][:3]
    return checked["design"]


def _straight_mask(design: dict, far) -> list:
    """A mask of the straight classes: ROW_k spans the Row-frame slots [tau_k, far(k)].

    The top row reaches the Row channel (tau_1 = 0) and the rows below start where their lane taper
    leaves them (tau_k from row_taper); the far ends recede toward the side away from the Column tail,
    so the row next to the Column tail spans every column.  Returned in net indices.
    """

    rows, columns = design["matrix"]["rows"], design["matrix"]["columns"]
    pitch = design["matrix"]["pitch_x_mm"]
    taper = row_taper(design, PROFILE)
    start = max(0.5, taper[0])
    taus = [max(0, math.ceil(round(edge - start, 6) / pitch - 1e-9)) for edge in taper]
    equal = design["tail"]["row_side"] == design["tail"]["column_side"]
    his = [min(columns - 1, max(tau, far(row))) for row, tau in enumerate(taus, start=1)]
    order = range(rows - 2, -1, -1) if equal else range(1, rows)
    for index in order:
        his[index] = min(his[index], his[index + 1] if equal else his[index - 1])
    his[rows - 1 if equal else 0] = columns - 1
    slots = [(tau, max(tau, hi)) for tau, hi in zip(taus, his)]
    return [[columns - hi, columns - lo] if equal else [lo + 1, hi + 1] for lo, hi in slots]


def _masked(design: dict, mask) -> dict:
    masked = copy.deepcopy(design)
    masked["matrix"]["mask"] = [list(pair) for pair in mask]
    return masked


def _corpus() -> list:
    """(name, masked request): the shapes of the plan's P2 corpus that the straight classes take."""

    cases = [
        ("soft-finger taper 48x12 tight", _request(48, 12, routing=TIGHT), lambda row: 11),
        ("right triangle 20x16 tight", _request(20, 16, routing=TIGHT), lambda row: row),
        ("quarter disk 20x20", _request(20, 20), lambda row: int(math.floor(20 * math.sqrt(max(0.0, 1 - ((20 - row + 0.5) / 20) ** 2))))),
        ("L shape 12x12", _request(12, 12), lambda row: 3 if row <= 6 else 11),
        ("trapezoid 12x20", _request(12, 20), lambda row: 8 + row),
        ("p0.6 tight 16x24", _request(16, 24, FINE, routing=TIGHT), lambda row: 8 + row),
        ("sparse 3 mm 10x12 (per-electrode windows)", _request(10, 12, SPARSE), lambda row: 2 + row),
        ("opposite sides 12x16", _request(12, 16, tail={"row_side": "bottom", "column_side": "top"}), lambda row: 15 - row),
        ("right tails 12x16, Columns on top", _request(12, 16, tail={"row_side": "right", "column_side": "right"},
                                                     role_mapping={"top": "columns", "bottom": "rows"}), lambda row: 3 + row),
        ("40x6 tight, tail wider than the field", _request(40, 6, routing=TIGHT), lambda row: 2 if row < 20 else 5),
    ]
    answer = []
    for name, request, far in cases:
        mask = _straight_mask(_design(request), far)
        answer.append((name, dict(request, matrix=dict(request["matrix"], mask=mask))))
    return answer


def _strip(board: dict) -> dict:
    board = copy.deepcopy(board)
    for section, key in MASK_KEYS:
        board[section].pop(key, None)
    return board


def _area(ring) -> float:
    return math.fsum(a[0] * b[1] - b[0] * a[1] for a, b in edges(ring)) / 2


def _box_area(box) -> float:
    return (box[2] - box[0]) * (box[3] - box[1])


def _parts(boxes: list, axis: int) -> list:
    """Bands (sorted along ``axis``) and the fillers between them over their common extent: an independent union."""

    along = 1 - axis
    parts = list(boxes)
    for first, second in zip(boxes, boxes[1:]):
        if second[axis] - first[axis + 2] > 1e-9:
            filler = [0.0] * 4
            filler[axis], filler[axis + 2] = first[axis + 2], second[axis]
            filler[along], filler[along + 2] = max(first[along], second[along]), min(first[along + 2], second[along + 2])
            parts.append(tuple(filler))
    return parts


def _assert_rectilinear_orthoconvex(case: unittest.TestCase, ring) -> None:
    case.assertGreater(_area(ring), 0.0)  # counter-clockwise
    for a, b in edges(ring):
        case.assertTrue(a[0] == b[0] or a[1] == b[1], (a, b))
    for axis in (0, 1):
        levels = sorted({point[axis] for point in ring})
        for low, high in zip(levels, levels[1:]):
            level = (low + high) / 2
            hits = [a[1 - axis] + (b[1 - axis] - a[1 - axis]) * (level - a[axis]) / (b[axis] - a[axis])
                    for a, b in edges(ring) if (a[axis] > level) != (b[axis] > level)]
            case.assertEqual(len(hits), 2, (axis, level))  # one interval on every line


def _assert_simple(case: unittest.TestCase, ring) -> None:
    """No two non-adjacent edges touch or cross (a sweep over the edges' x ranges)."""

    pairs = edges(ring)
    count = len(pairs)
    order = sorted(range(count), key=lambda index: min(pairs[index][0][0], pairs[index][1][0]))
    active: list = []
    for index in order:
        a, b = pairs[index]
        low = min(a[0], b[0])
        active = [other for other in active if max(pairs[other][0][0], pairs[other][1][0]) >= low - 1e-9]
        for other in active:
            if abs(index - other) in (1, count - 1):
                continue
            c, d = pairs[other]
            case.assertGreater(segment_distance(a, b, c, d), 1e-7, (a, b, c, d))
        active.append(index)


def _on_grid(points) -> bool:
    return all(abs(value - round(value, 6)) < 1e-12 for point in points for value in point)


def _stacked(board: dict, box) -> tuple:
    """A box of a turned board in the stack frame: on the active region's centre, the physical top board turned over."""

    region = board["grid_registration"]["active_region"]
    cx, cy = region["x"] + region["width"] / 2, region["y"] + region["height"] / 2
    x0, y0, x1, y1 = box[0] - cx, box[1] - cy, box[2] - cx, box[3] - cy
    if board["physical_side"] == "top":
        if board["tail"]["side"] in ("bottom", "top"):
            x0, x1 = -x1, -x0
        else:
            y0, y1 = -y1, -y0
    return (x0, y0, x1, y1)


class MaskFullSpanTests(unittest.TestCase):
    """The masked builders given a full span reproduce today's boards byte for byte."""

    CASES = (
        ("default 12x32", _request(12, 32)),
        ("16x16 at 1 mm", _request(16, 16, ONE_MM)),
        ("0.1016 mm routing 12x16", _request(12, 16, routing=TIGHT)),
        ("48x12 tight", _request(48, 12, routing=TIGHT)),
        ("sparse 5x40 at 3 mm", _request(5, 40, SPARSE)),
        ("opposite tail sides 12x16", _request(12, 16, tail={"row_side": "bottom", "column_side": "top"})),
        ("40x3 tight: the contact row is wider than the field", _request(40, 3, routing=TIGHT)),
        ("1 x 1 with a 64-pin Row tail", _request(1, 1, connector={"row_pins": 64})),
    )

    def test_full_spans_give_todays_boards(self) -> None:
        for name, request in self.CASES:
            design = _design(request)
            rows, columns = design["matrix"]["rows"], design["matrix"]["columns"]
            full = _masked(design, [[1, columns]] * rows)
            for build in (build_row_board, build_column_board):
                with self.subTest(case=name, board=build.__name__):
                    today, masked = build(design, PROFILE), build(full, PROFILE)
                    self.assertEqual(json.dumps(_strip(masked)), json.dumps(today))
                    # The masked keys describe the full rectangle.
                    registration = masked["grid_registration"]
                    self.assertEqual(registration["taxel_mask"], {"format": "row_spans/v1", "rows": rows, "columns": columns, "row_spans": [[1, columns]] * rows})
                    self.assertEqual(registration["active_taxel_count"], rows * columns)
                    self.assertEqual(masked["metrics"]["active_taxel_count"], rows * columns)
                    self.assertEqual(masked["construction"]["mask_class"], {"row": "straight", "column": "straight"})
                    region = registration["active_region"]
                    x0, y0 = region["x"], region["y"]
                    x1, y1 = round(x0 + region["width"], 6), round(y0 + region["height"], 6)
                    self.assertEqual(sorted(map(tuple, registration["active_outline"])), sorted([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
                    # And through the turn to another tail side.
                    turned_today, turned = copy.deepcopy(today), copy.deepcopy(masked)
                    apply_tail_side(turned_today, "left")
                    apply_tail_side(turned, "left")
                    self.assertEqual(json.dumps(_strip(turned)), json.dumps(turned_today))
            footprint = field_footprint(full, PROFILE)
            self.assertEqual({key: value for key, value in footprint.items() if key != "mask"}, field_footprint(design, PROFILE))

    def test_a_channel_of_full_width_keeps_todays_boards(self) -> None:
        # The generic profile keeps the Row channel's full width (no lane taper): a full span is still today's board.
        generic = load_profile()
        design = _design(_request(12, 32))
        full = _masked(design, [[1, 32]] * 12)
        for build in (build_row_board, build_column_board):
            with self.subTest(board=build.__name__):
                self.assertEqual(json.dumps(_strip(build(full, generic))), json.dumps(build(design, generic)))


class MaskAnchoredTests(unittest.TestCase):
    """A mask whose rows all reach the Row channel and whose row next to the Column tail is full keeps today's copper."""

    def test_anchored_masks_keep_the_unmasked_routes(self) -> None:
        cases = (
            ("equal sides", _request(12, 16), lambda row: 3 + row),
            ("opposite sides", _request(12, 16, tail={"row_side": "bottom", "column_side": "top"}), lambda row: 16 - row),
            ("tight 24x20", _request(24, 20, routing=TIGHT), lambda row: row // 2 + 5),
        )
        for name, request, far in cases:
            design = _design(request)
            rows, columns = design["matrix"]["rows"], design["matrix"]["columns"]
            equal = design["tail"]["row_side"] == design["tail"]["column_side"]
            # Every row reaches the Row channel (Row-frame slot 0): COL_C with equal sides, COL_01 with opposite ones.
            spans = []
            for row in range(1, rows + 1):
                reach = min(columns, far(row) + 1)
                spans.append([columns - reach + 1, columns] if equal else [1, reach])
            spans[rows - 1 if equal else 0] = [1, columns]  # the row next to the Column tail is full
            for index in (range(rows - 2, -1, -1) if equal else range(1, rows)):  # columns stay contiguous
                neighbour = spans[index + 1] if equal else spans[index - 1]
                spans[index] = [max(spans[index][0], neighbour[0]), spans[index][1]] if equal else [1, min(spans[index][1], neighbour[1])]
            masked = _masked(design, spans)
            self.assertEqual([lo for lo, _ in row_frame_spans(masked)], [0] * rows)
            self.assertEqual([low for low, _ in column_frame_spans(masked)], [0] * columns)
            for build in (build_row_board, build_column_board):
                with self.subTest(case=name, board=build.__name__):
                    today, board = build(design, PROFILE), build(masked, PROFILE)
                    self.assertNotEqual(board["layers"]["top_copper"]["electrodes"], today["layers"]["top_copper"]["electrodes"])
                    for part in ("routes", "pads"):
                        self.assertEqual(board["layers"]["top_copper"][part], today["layers"]["top_copper"][part], part)
                    gang = [opening for opening in board["layers"]["top_coverlay_openings"] if opening["kind"] == "connector_contact_opening"]
                    self.assertEqual(gang, [opening for opening in today["layers"]["top_coverlay_openings"] if opening["kind"] == "connector_contact_opening"])
                    self.assertEqual(board["layers"]["bottom_stiffener"], today["layers"]["bottom_stiffener"])
                    self.assertEqual(board["tail"], today["tail"])
                    self.assertEqual(board["grid_registration"]["active_region"], today["grid_registration"]["active_region"])


class MaskGeometryTests(unittest.TestCase):
    """The builders' geometry on the corpus, measured independently."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = []
        for name, request in _corpus():
            design = _design(request)
            cls.cases.append((name, design, build_row_board(design, PROFILE), build_column_board(design, PROFILE)))

    def test_the_lane_taper_places_the_row_field(self) -> None:
        for name, design, row_board, _ in self.cases:
            with self.subTest(case=name):
                pitch = design["matrix"]["pitch_x_mm"]
                spans = row_frame_spans(design)
                taper = row_taper(design, PROFILE)
                start = max(0.5, max(round(edge - round(lo * pitch, 6), 6) for edge, (lo, _) in zip(taper, spans)))
                self.assertEqual(row_board["grid_registration"]["active_region"]["x"], start)
                # Every row starts at the slot its lane taper leaves, no farther.
                self.assertEqual([lo for lo, _ in spans], [max(0, math.ceil(round(edge - start, 6) / pitch - 1e-9)) for edge in taper])
                unmasked = build_row_board(_strip_mask(design), PROFILE)
                self.assertLessEqual(start, unmasked["grid_registration"]["active_region"]["x"])
                self.assertLessEqual(row_board["metrics"]["outline_width_mm"], unmasked["metrics"]["outline_width_mm"])
        # The soft finger's taper slides its field toward the channel: the board is narrower than the rectangle's.
        name, design, row_board, _ = self.cases[0]
        unmasked = build_row_board(_strip_mask(design), PROFILE)
        self.assertLess(row_board["metrics"]["outline_width_mm"], unmasked["metrics"]["outline_width_mm"] - 4.0, name)

    def test_electrode_spans_and_stub_ends(self) -> None:
        overhang = 0.2
        tapered = raised = 0
        for name, design, row_board, column_board in self.cases:
            tapered += sum(1 for lo, _ in row_frame_spans(design) if lo > 0)
            raised += sum(1 for low, _ in column_frame_spans(design) if low > 0)
            matrix = design["matrix"]
            px, py, cw, rw = matrix["pitch_x_mm"], matrix["pitch_y_mm"], matrix["taxel_width_mm"], matrix["taxel_height_mm"]
            rows, columns = matrix["rows"], matrix["columns"]
            unmasked = (build_row_board(_strip_mask(design), PROFILE), build_column_board(_strip_mask(design), PROFILE))
            with self.subTest(case=name, board="row"):
                region = row_board["grid_registration"]["active_region"]
                electrodes = {item["net"]: bounds(item) for item in row_board["layers"]["top_copper"]["electrodes"]}
                for row, (lo, hi) in enumerate(row_frame_spans(design), start=1):
                    box = electrodes[f"ROW_{row:02d}"]
                    expected = (region["x"] + lo * px - overhang, region["y"] + (rows - row) * py,
                                region["x"] + hi * px + cw + overhang, region["y"] + (rows - row) * py + rw)
                    self.assertTrue(all(abs(a - b) <= EPSILON for a, b in zip(box, expected)), (row, box, expected))
                self._assert_stubs(row_board, unmasked[0], electrodes, axis=1)
            with self.subTest(case=name, board="column"):
                region = column_board["grid_registration"]["active_region"]
                electrodes = {item["net"]: bounds(item) for item in column_board["layers"]["top_copper"]["electrodes"]}
                for column, (low, high) in enumerate(column_frame_spans(design), start=1):
                    box = electrodes[f"COL_{column:02d}"]
                    expected = (region["x"] + (column - 1) * px, region["y"] + low * py - overhang,
                                region["x"] + (column - 1) * px + cw, region["y"] + high * py + rw + overhang)
                    self.assertTrue(all(abs(a - b) <= EPSILON for a, b in zip(box, expected)), (column, box, expected))
                self._assert_stubs(column_board, unmasked[1], electrodes, axis=0)
        # The corpus has rows that step away from the channel and raised columns.
        self.assertGreater(tapered, 100)
        self.assertGreater(raised, 20)

    def _assert_stubs(self, board: dict, unmasked: dict, electrodes: dict, axis: int) -> None:
        """Each fan-out is today's up to its last point, which lies on its own electrode's near end."""

        today = {route["net"]: route for route in unmasked["layers"]["top_copper"]["routes"] if route["segment"] == "fanout"}
        for route in board["layers"]["top_copper"]["routes"]:
            if route["segment"] != "fanout":
                continue
            box, end = electrodes[route["net"]], route["points"][-1]
            near = (box[0], (box[1] + box[3]) / 2) if axis == 1 else ((box[0] + box[2]) / 2, box[1])
            self.assertTrue(abs(end[0] - near[0]) <= EPSILON and abs(end[1] - near[1]) <= EPSILON, (route["net"], end, near))
            self.assertEqual(route["points"][:-1], today[route["net"]]["points"][:-1], route["net"])
            # The last leg runs straight along the electrode's axis (a Row stub across, a Column stub up).
            before = route["points"][-2]
            self.assertEqual(before[1 if axis == 1 else 0], end[1 if axis == 1 else 0], route["net"])

    def test_window_rings_and_the_crossing_region(self) -> None:
        for name, design, row_board, column_board in self.cases:
            for key, board, axis in (("row", row_board, 1), ("column", column_board, 0)):
                with self.subTest(case=name, board=key):
                    boxes = sorted((bounds(item) for item in board["layers"]["top_copper"]["electrodes"]), key=lambda box: box[axis])
                    windows = [opening for opening in board["layers"]["top_coverlay_openings"] if opening["kind"] != "connector_contact_opening"]
                    if windows[0]["kind"] == "sensor_electrode_opening":
                        self.assertTrue(all("shape" not in opening for opening in windows))  # per-electrode windows stay rectangles
                    else:
                        (window,) = windows
                        self.assertEqual(window["shape"], "polygon")
                        self.assertEqual(set(window), {"kind", "shape", "net", "nets", "opening_for", "points"})
                        self.assertEqual(window["nets"], [item["net"] for item in board["layers"]["top_copper"]["electrodes"]])
                        ring = window["points"]
                        self.assertTrue(_on_grid(ring))
                        _assert_rectilinear_orthoconvex(self, ring)
                        _assert_simple(self, ring)
                        grown = [(x0 - 0.1, y0 - 0.1, x1 + 0.1, y1 + 0.1) for x0, y0, x1, y1 in boxes]
                        parts = _parts(grown, axis)
                        self.assertAlmostEqual(_area(ring), math.fsum(_box_area(part) for part in parts), delta=1e-6)
                        for part in parts:
                            corners = [(part[0], part[1]), (part[2], part[1]), (part[2], part[3]), (part[0], part[3])]
                            self.assertTrue(all(inside_or_on(corner, ring) for corner in corners), part)
                        # Every electrode keeps the 0.1 mm expansion inside the ring.
                        exposure = min(segment_box_distance(a, b, box) for box in boxes for a, b in edges(ring))
                        self.assertAlmostEqual(exposure, 0.1, delta=1e-6)
                    # P: the crossing strips (electrodes without the overhang) plus fillers.
                    strips = []
                    for x0, y0, x1, y1 in boxes:
                        strips.append((x0 + 0.2, y0, x1 - 0.2, y1) if axis == 1 else (x0, y0 + 0.2, x1, y1 - 0.2))
                    active = board["grid_registration"]["active_outline"]
                    self.assertTrue(_on_grid(active))
                    _assert_rectilinear_orthoconvex(self, active)
                    _assert_simple(self, active)
                    self.assertAlmostEqual(_area(active), math.fsum(_box_area(part) for part in _parts(strips, axis)), delta=1e-6)
                    for part in _parts(strips, axis):
                        self.assertTrue(inside_or_on(((part[0] + part[2]) / 2, (part[1] + part[3]) / 2), active), part)
            # Both boards' P have the same area (one region seen from each board).
            self.assertAlmostEqual(_area(row_board["grid_registration"]["active_outline"]), _area(column_board["grid_registration"]["active_outline"]), delta=1e-6)

    def test_outlines_follow_the_field(self) -> None:
        for name, design, row_board, column_board in self.cases:
            for key, board in (("row", row_board), ("column", column_board)):
                with self.subTest(case=name, board=key):
                    outline = board["outline"]["points"]
                    self.assertGreater(_area(outline), 0.0)
                    self.assertTrue(_on_grid(outline))
                    _assert_simple(self, outline)
                    active = board["grid_registration"]["active_outline"]
                    # The active-edge margin from P, exactly the rule at the closest point, and P inside.
                    margin = min(segment_distance(a, b, c, d) for a, b in edges(active) for c, d in edges(outline))
                    self.assertAlmostEqual(margin, 0.5, delta=EPSILON)
                    self.assertTrue(point_in_polygon(active[0], outline))
                    self.assertFalse(any(segments_cross(a, b, c, d) for a, b in edges(active) for c, d in edges(outline)))
                    # Field windows inside the outline, 0.2 mm (0.5 margin less overhang and expansion) from it.
                    for opening in board["layers"]["top_coverlay_openings"]:
                        if opening["kind"] == "connector_contact_opening":
                            continue
                        ring = opening.get("points") or _box_ring(bounds(opening))
                        self.assertTrue(all(point_in_polygon(point, outline) for point in ring))
                        gap = min(segment_distance(a, b, c, d) for a, b in edges(ring) for c, d in edges(outline))
                        self.assertGreaterEqual(gap, 0.2 - EPSILON)

    def test_the_bodies_follow_the_field(self) -> None:
        # The bodies are F, the crossings dilated by the 0.5 mm margin: above each column the Column body
        # ends at the highest crossing strip within 0.5 mm of its centre line plus the margin, and beside
        # each row the Row body's far side is the farthest strip within 0.5 mm of the row's centre line plus
        # the margin, or the bottom part's width for the rows reaching as far as the bottom row.  A fillet in
        # a concave step may add up to its radius.
        for name, design, row_board, column_board in self.cases:
            for key, board, axis in (("column", column_board, 0), ("row", row_board, 1)):
                with self.subTest(case=name, board=key):
                    outline = board["outline"]["points"]
                    along = 1 - axis  # the electrodes' length
                    strips = []
                    for electrode in board["layers"]["top_copper"]["electrodes"]:
                        box = list(bounds(electrode))
                        box[along] += 0.2
                        box[along + 2] -= 0.2
                        strips.append(box)
                    reach = max(strip[along + 2] for strip in strips)
                    for strip in strips:
                        level = (strip[axis] + strip[axis + 2]) / 2
                        expected = max(other[along + 2] for other in strips if other[axis] - 0.5 <= level <= other[axis + 2] + 0.5) + 0.5
                        measured = _ray(outline, level, axis)
                        self.assertGreaterEqual(measured, expected - EPSILON, strip)
                        if expected < reach + 0.5 - EPSILON or key == "column":
                            self.assertLessEqual(measured, expected + 0.5 + EPSILON, strip)

    def test_every_record_and_the_registration_pass(self) -> None:
        for name, request in _corpus():
            with self.subTest(case=name):
                result = generate_design(request)
                self.assertTrue(result["ok"], result["validation"]["errors"][:3])
                self.assertEqual(set(result["boards"]), {"row", "column"})
                for key, board in result["boards"].items():
                    checks = board["verification"]["checks"]
                    self.assertEqual(len(checks), 30)
                    self.assertEqual(sorted(rule for rule, record in checks.items() if not record["passed"]), [], key)
                    self.assertTrue(board["verification"]["registration"]["passed"], key)
                    self.assertGreaterEqual(checks["concave_fillet_radius"]["measured_mm"], 0.498097)
                    self.assertGreaterEqual(checks["copper_to_outline"]["measured_mm"], 0.3 - EPSILON)
                    self.assertGreaterEqual(checks["route_to_outline"]["measured_mm"], 0.3 - EPSILON)

    def test_the_masked_keys(self) -> None:
        for name, design, row_board, column_board in self.cases:
            with self.subTest(case=name):
                rows, columns = design["matrix"]["rows"], design["matrix"]["columns"]
                expected = {"format": "row_spans/v1", "rows": rows, "columns": columns, "row_spans": design["matrix"]["mask"]}
                count = 0
                for first, last in design["matrix"]["mask"]:
                    count += last - first + 1
                for board in (row_board, column_board):
                    self.assertEqual(board["grid_registration"]["taxel_mask"], expected)
                    self.assertEqual(board["grid_registration"]["active_taxel_count"], count)
                    self.assertEqual(board["metrics"]["active_taxel_count"], count)
                    self.assertEqual(board["construction"]["mask_class"], {"row": "straight", "column": "straight"})
                self.assertLess(count, rows * columns)
        # Unmasked boards carry none of them.
        plain = generate_design(_request(12, 16))
        for board in plain["boards"].values():
            for section, key in MASK_KEYS:
                self.assertNotIn(key, board[section])
            self.assertFalse(any("shape" in opening for opening in board["layers"]["top_coverlay_openings"]))
            self.assertNotIn("data-active-outline", board["svg"])


class MaskStackTests(unittest.TestCase):
    """Generated masked boards, turned to their tail sides and stacked."""

    def test_the_crossings_are_the_mask_in_every_combination(self) -> None:
        for row_side in _SIDES:
            for column_side in (row_side, _OPPOSITE[row_side]):
                for top in ("rows", "columns"):
                    request = _request(8, 11, tail={"row_side": row_side, "column_side": column_side},
                                       role_mapping={"top": top, "bottom": "columns" if top == "rows" else "rows"})
                    mask = _straight_mask(_design(request), lambda row: 3 + row)
                    with self.subTest(row_side=row_side, column_side=column_side, top=top):
                        result = generate_design(dict(request, matrix=dict(request["matrix"], mask=mask)))
                        boxes = {}
                        for board in result["boards"].values():
                            for electrode in board["layers"]["top_copper"]["electrodes"]:
                                boxes[electrode["net"]] = _stacked(board, bounds(electrode))
                        wrong = []
                        for row, (first, last) in enumerate(mask, start=1):
                            for column in range(1, 12):
                                a, b = boxes[f"ROW_{row:02d}"], boxes[f"COL_{column:02d}"]
                                crossing = min(a[2], b[2]) - max(a[0], b[0]) > EPSILON and min(a[3], b[3]) - max(a[1], b[1]) > EPSILON
                                if crossing != (first <= column <= last):
                                    wrong.append((row, column))
                        self.assertEqual(wrong, [])
                        # One crossing region, seen from both boards: equal point sets in the stack frame.
                        rings = []
                        for board in result["boards"].values():
                            points = [_stacked(board, (x, y, x, y))[:2] for x, y in board["grid_registration"]["active_outline"]]
                            rings.append(sorted((round(x, 6), round(y, 6)) for x, y in points))
                        self.assertEqual(rings[0], rings[1])

    def test_turned_boards_keep_their_windows_and_field(self) -> None:
        for side in _SIDES:
            request = _request(12, 16, tail={"row_side": side, "column_side": side})
            mask = _straight_mask(_design(request), lambda row: 3 + row)
            with self.subTest(side=side):
                result = generate_design(dict(request, matrix=dict(request["matrix"], mask=mask)))
                for key, board in result["boards"].items():
                    axis = (1 if key == "row" else 0) if side in ("bottom", "top") else (0 if key == "row" else 1)
                    boxes = sorted((bounds(item) for item in board["layers"]["top_copper"]["electrodes"]), key=lambda box: box[axis])
                    (window,) = [opening for opening in board["layers"]["top_coverlay_openings"] if opening.get("shape") == "polygon"]
                    ring = window["points"]
                    self.assertGreater(_area(ring), 0.0)
                    grown = [(x0 - 0.1, y0 - 0.1, x1 + 0.1, y1 + 0.1) for x0, y0, x1, y1 in boxes]
                    self.assertAlmostEqual(_area(ring), math.fsum(_box_area(part) for part in _parts(grown, axis)), delta=1e-6)
                    for box in grown:
                        self.assertTrue(all(inside_or_on(corner, ring) for corner in _box_ring(box)), (key, box))
                    along = 1 - axis
                    strips = []
                    for box in boxes:
                        strip = list(box)
                        strip[along] += 0.2
                        strip[along + 2] -= 0.2
                        strips.append(tuple(strip))
                    active = board["grid_registration"]["active_outline"]
                    self.assertGreater(_area(active), 0.0)
                    self.assertAlmostEqual(_area(active), math.fsum(_box_area(part) for part in _parts(strips, axis)), delta=1e-6)
                    for part in _parts(strips, axis):
                        self.assertTrue(all(inside_or_on(corner, active) for corner in _box_ring(part)), (key, part))
                    self.assertTrue(all(point_in_polygon(point, board["outline"]["points"]) for point in ring))

    def test_the_svg_draws_the_polygon_window_and_the_field(self) -> None:
        request = _request(12, 16)
        mask = _straight_mask(_design(request), lambda row: 3 + row)
        result = generate_design(dict(request, matrix=dict(request["matrix"], mask=mask)))
        for board in result["boards"].values():
            svg = board["svg"]
            (window,) = [opening for opening in board["layers"]["top_coverlay_openings"] if opening.get("shape") == "polygon"]
            points = " ".join(f"{_number(x)},{_number(y)}" for x, y in window["points"])
            self.assertIn(f'<polygon class="opening" points="{points}"/>', svg)
            ys = [y for _, y in board["outline"]["points"]]
            flip = min(ys) + max(ys)
            outline = " ".join(f"{_number(x)},{_number(flip - y)}" for x, y in board["grid_registration"]["active_outline"])
            self.assertIn(f'data-active-outline="{outline}"', svg)
            self.assertEqual(svg.count("<rect class=\"opening\""), 1)  # the gang window


class MaskFootprintTests(unittest.TestCase):
    def test_the_footprint_of_masked_boards(self) -> None:
        for name, request in _corpus():
            design = _design(request)
            footprint = field_footprint(design, PROFILE)
            self.assertEqual(set(footprint), {"field", "row", "column", "mask"})
            for key, build in (("row", build_row_board), ("column", build_column_board)):
                board = build(design, PROFILE)
                with self.subTest(case=name, board=key):
                    region, tail = board["grid_registration"]["active_region"], board["tail"]["bounds"]
                    root = tail["y"] + tail["height"]
                    above = [point for point in board["outline"]["points"] if point[1] >= root - 1e-9]
                    measured = {
                        "left": round(region["x"] - min(x for x, _ in above), 6),
                        "right": round(max(x for x, _ in above) - region["x"] - region["width"], 6),
                        "top": round(max(y for _, y in above) - region["y"] - region["height"], 6),
                        "bottom": round(region["y"] - root, 6),
                    }
                    self.assertEqual({side: footprint[key][side] for side in measured}, measured)
                    self.assertEqual(footprint[key]["tail"]["x"], round(tail["x"] - region["x"], 6))
                    ring = footprint["mask"][key]["outline"]
                    self.assertGreater(_area(ring), 0.0)
                    self.assertTrue(_on_grid(ring))
                    _assert_simple(self, ring)
                    if key == "row":
                        _assert_rectilinear_orthoconvex(self, ring)  # the Column ring has the fan-out's diagonals
                    # The body before the fillets: inside the built outline, which the fillets only grow.
                    body = [[x + region["x"], y + region["y"]] for x, y in ring]
                    self.assertTrue(all(inside_or_on(point, board["outline"]["points"]) for point in body))
                    self.assertEqual(round(max(x for x, _ in body), 6), round(max(x for x, _ in above), 6))
                    self.assertEqual(round(max(y for _, y in body), 6), round(max(y for _, y in above), 6))
                    self.assertEqual(round(min(y for _, y in body), 6), round(root, 6))
                    self.assertEqual(round(min(x for x, _ in body), 6), round(min(x for x, _ in above), 6))
                    # The fillets add material only within their radius of a concave corner or a root corner.
                    self.assertEqual(_beyond_the_fillets(board, body, root), [])
        # Unmasked designs have no mask block.
        self.assertNotIn("mask", field_footprint(_design(_request(12, 16)), PROFILE))

    def test_the_fillets_beside_the_tail_root(self) -> None:
        # Cut at the tail root, the ring turns the board's concave corners where the body meets the tail into
        # convex corners of its own: a Row tail wider than the body, and the Column fan-out's sides.  Their
        # fillets lie outside the ring, just above the root and within the fillet radius of those corners.
        radius = PROFILE["outline"]["outline_fillet_radius_mm"]
        cases = (
            ("row", _request(16, 7, {"mask": [[1, 7], [1, 7], [1, 6], [1, 6], [1, 5], [1, 5], [1, 4], [1, 4], [1, 4], [1, 3], [1, 3], [1, 3], [1, 3], [1, 3], [1, 1], [1, 1]]},
                             connector={"row_pins": 18}, tail={"row_side": "top", "column_side": "bottom"})),
            ("column", _request(2, 2, {"pitch_x_mm": 1.0, "pitch_y_mm": 1.0, "taxel_width_mm": 0.6, "taxel_height_mm": 0.6, "mask": [[1, 2], [2, 2]]},
                                tail={"row_side": "top", "column_side": "bottom"})),
        )
        for key, request in cases:
            with self.subTest(board=key):
                design = _design(request)
                board = (build_row_board if key == "row" else build_column_board)(design, PROFILE)
                region, tail = board["grid_registration"]["active_region"], board["tail"]["bounds"]
                root = tail["y"] + tail["height"]
                body = [[x + region["x"], y + region["y"]] for x, y in field_footprint(design, PROFILE)["mask"][key]["outline"]]
                outside = [point for point in board["outline"]["points"] if point[1] > root + 1e-9 and not inside_or_on(point, body)]
                self.assertTrue([point for point in outside if point[1] - root <= radius])
                self.assertEqual(_beyond_the_fillets(board, body, root), [])
                if key == "row":
                    # The wider tail's fillet is accounted for by the root corner alone.
                    concave = _ring_corners(body, root, root_corners=False)
                    beside_the_root = [point for point in outside if not any(math.dist(point, corner) <= radius + EPSILON for corner in concave)]
                    self.assertTrue(beside_the_root)
                    self.assertTrue(all(point[1] - root <= radius for point in beside_the_root))


class MaskClassGateTests(unittest.TestCase):
    def test_masks_outside_the_straight_classes_are_refused(self) -> None:
        upright = [[5 - (row + 1) // 2, 4 + (row + 1) // 2] for row in range(1, 9)]  # isosceles: fails the straight Row channel
        inverted = [[row, 8] for row in range(1, 9)]  # the floor is not full: fails the straight Column fan-out
        for name, mask, field, phrase in (
            ("upright", upright, "matrix.mask[0]", "ROW_01 ends at COL_05 on the Row-channel side"),
            ("inverted", inverted, "matrix.mask[1]", "COL_01 ends at ROW_01, and ROW_02, next to it on the Column-tail side"),
        ):
            with self.subTest(mask=name):
                result = generate_design(_request(8, 8, {"mask": mask}))
                self.assertEqual([(issue["code"], issue["field"]) for issue in result["validation"]["errors"]], [("E_MASK_ROUTING", field)])
                self.assertIn(phrase, result["validation"]["errors"][0]["message"])
                self.assertEqual(result["boards"], {})
                design = copy.deepcopy(result["design"])
                for build in (build_row_board, build_column_board):
                    with self.assertRaisesRegex(ValueError, f"^{re.escape(field)}: "):
                        build(design, PROFILE)
                with self.assertRaises(ValueError):
                    field_footprint(design, PROFILE)
        # A mask of the classes passes the feasibility check and is built.
        ok = generate_design(_request(8, 8, {"mask": [[9 - row, 8] for row in range(1, 9)]}))
        self.assertNotIn("E_MASK_ROUTING", [issue["code"] for issue in ok["validation"]["errors"]])
        self.assertEqual(set(ok["boards"]), {"row", "column"})


# Canonical-JSON digests of masked builds (both boards as generated, turned and assigned, without the DRC's
# measurements and the SVG), written on 2026-10-21 from the P2 builders: the same on Python 3.9.6 and 3.12 (the
# CI matrix).  A deliberate change of masked geometry updates them (and MASK_VERSION once masks are accepted).
DIGESTS = {
    "soft-finger taper 48x12 tight": "07fe0d8f07e0d2b81bb8b0f0effcfa616268d74af9dd4b5e56d6e49c6c5e1d9c",
    "quarter disk 20x20": "c053214092255e79305408fb6ec0a8689bb7fcd8a5cc9ff4ec08d23fe6cc64fe",
    "p0.6 tight 16x24": "4a39cfc9096cad029eaace380658794eafc88ff56e171a380c95e7ce541fe055",
    "sparse 3 mm 10x12 (per-electrode windows)": "1450f171bb840f6b5154f28c370cf650b9bde86d2d7a045c8133cb724ab3123f",
    "right tails 12x16, Columns on top": "26736680333a8b8638b9dc50075637bd95ccd9160ab58540afd374fe7b7f4a8e",
}


class MaskDeterminismTests(unittest.TestCase):
    def test_masked_builds_are_pinned(self) -> None:
        corpus = dict(_corpus())
        for name, digest in DIGESTS.items():
            with self.subTest(case=name):
                self.assertEqual(_layout_digest(generate_design(corpus[name])), digest)

    def test_the_masked_code_sums_no_floats(self) -> None:
        # Python 3.12's sum() of floats rounds differently from 3.9's; the masked code accumulates with loops or fsum.
        for function in MASKED_FUNCTIONS:
            with self.subTest(function=function.__name__):
                self.assertEqual([problem for problem in _determinism_problems(function) if "sum()" in problem], [])
        # Every function of the builders named for the mask is in the list.
        named = sorted(name for name, value in vars(layout).items() if inspect.isfunction(value) and value.__module__ == layout.__name__ and "mask" in name)
        self.assertEqual([name for name in named if getattr(layout, name) not in MASKED_FUNCTIONS], [])

    def test_the_masked_code_iterates_no_sets(self) -> None:
        # A set's order is the hash order (strings: PYTHONHASHSEED), so no set reaches an output unsorted: in the
        # masked functions and in every function of the engine, the exporter and the map that handles a mask, a
        # masked board's outline or a polygon window.
        modules = (layout, engine_geometry, engine_core, direct_gerber, place)
        handling = [
            value for module in modules for name, value in sorted(vars(module).items())
            if inspect.isfunction(value) and value.__module__ == module.__name__
            and re.search(r"mask|active_outline|\"polygon\"", inspect.getsource(value))
        ]
        self.assertGreater(len(handling), 30)

        def unordered(values):  # the detector itself: two ordered iterations of sets and one sum()
            seen = set(values)
            return [value for value in seen] + list({1, 2} | seen) + [sum(values)] + sorted(seen) + [len({3})]

        self.assertEqual(len([problem for problem in _determinism_problems(unordered) if "set" in problem]), 2)
        self.assertEqual(len([problem for problem in _determinism_problems(unordered) if "sum()" in problem]), 1)
        for function in [*MASKED_FUNCTIONS, *handling]:
            with self.subTest(function=f"{function.__module__}.{function.__name__}"):
                self.assertEqual([problem for problem in _determinism_problems(function) if "set" in problem], [])

    def test_a_64_by_64_masked_design_is_fast(self) -> None:
        request = _request(64, 64, {"pitch_x_mm": 1.0, "pitch_y_mm": 1.0, "taxel_width_mm": 0.6, "taxel_height_mm": 0.6}, routing=TIGHT)
        mask = _straight_mask(_design(request), lambda row: row)
        started = time.perf_counter()
        result = generate_design(dict(request, matrix=dict(request["matrix"], mask=mask)))
        self.assertLess(time.perf_counter() - started, 5.0)
        self.assertEqual(result["boards"]["row"]["metrics"]["active_taxel_count"], 1702)


# The functions masked-field phases P1-P4 added to the builders, the geometry, the SVG, the exporter and the map (the
# fit's own, surface/fill.py, are checked by tests/test_mask_fit.py).
MASKED_FUNCTIONS = (
    layout.design_mask, layout._row_spans, layout._equal_sides, layout.column_spans, layout.row_frame_spans, layout.column_frame_spans,
    layout.row_taper, layout.mask_class, layout._straight_classes, layout.masked_row_plan, layout._row_body_chain,
    layout.masked_column_plan, layout._column_top_chain, layout._build_masked_row_board, layout._build_masked_column_board, layout._masked_column_board,
    layout.masked_column_outline, layout._column_fanout, layout._column_side_chains, layout._masked_field_window, layout._mark_masked, layout._masked_body_ring,
    engine_geometry.band_union, engine_geometry.rect_union_slabs, engine_geometry.orthoconvex_ring, engine_geometry.band_ring,
    engine_geometry.is_rectilinear, engine_geometry.is_orthogonally_convex, engine_geometry.clip_segment_outside_box,
    engine_geometry.segment_parts_off_box_boundary, engine_core._svg_for_board, engine_core._mask_issues, engine_core._normalize_mask,
    direct_gerber._rect_openings, direct_gerber._check_polygon_opening, direct_gerber._has_polygon_opening,
    direct_gerber._masked_coverlay_regions, direct_gerber._opening_regions, direct_gerber._taxel_field_notes,
    direct_gerber._taxel_field_phrases, direct_gerber._taxel_map_files, direct_gerber._taxels, direct_gerber._contact_pins,
    direct_gerber._taxel_map_entry, direct_gerber._check_taxel_map, place.masked_taxel_centres, place.mask_record, place.readout,
)
# What an iteration may run over without an order: a set built here, or a name bound to one in the function.
_ORDERED_CONSUMERS = ("list", "tuple", "enumerate", "zip", "map", "filter", "reversed", "iter", "next", "dict")


def _determinism_problems(function) -> list:
    """The builtin ``sum()`` calls and the ordered iterations over a set in a function's source (by its syntax tree).

    A set is a set display or comprehension, a ``set()`` or ``frozenset()`` call, a union, intersection or
    difference of one, or a name assigned one in the function; it is iterated in order by a ``for`` loop, a
    list, generator or dict comprehension, a star, ``list()`` and the other order-keeping calls, ``join`` or
    ``extend``.  ``sorted()``, ``min()``, ``max()``, ``len()`` and membership tests are order-free.
    """

    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))

    def is_set(node, names) -> bool:
        if isinstance(node, (ast.Set, ast.SetComp)):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("set", "frozenset"):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.Sub, ast.BitXor)):
            return is_set(node.left, names) or is_set(node.right, names)
        return isinstance(node, ast.Name) and node.id in names

    names = sorted(
        target.id for node in ast.walk(tree) if isinstance(node, ast.Assign) and is_set(node.value, ())
        for target in node.targets if isinstance(target, ast.Name)
    )
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sum":
            problems.append(f"line {node.lineno}: builtin sum()")
        iterated = []
        if isinstance(node, ast.For):
            iterated.append(node.iter)
        elif isinstance(node, (ast.ListComp, ast.GeneratorExp, ast.DictComp)):
            iterated.extend(generator.iter for generator in node.generators)
        elif isinstance(node, ast.Starred):
            iterated.append(node.value)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _ORDERED_CONSUMERS:
                iterated.extend(node.args)
            elif isinstance(node.func, ast.Attribute) and node.func.attr in ("join", "extend"):
                iterated.extend(node.args)
        problems.extend(f"line {item.lineno}: a set iterated in order" for item in iterated if is_set(item, names))
    return problems


def _ring_corners(ring, root: float, root_corners: bool = True) -> list:
    """The concave corners of a counter-clockwise ring, and with ``root_corners`` its corners on the line ``y = root``."""

    count = len(ring)
    answer = []
    for index in range(count):
        a, b, c = ring[index - 1], ring[index], ring[(index + 1) % count]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if cross < 0 or (root_corners and abs(b[1] - root) <= EPSILON):
            answer.append(b)
    return answer


def _beyond_the_fillets(board: dict, ring, root: float) -> list:
    """The board's outline vertices above the tail root outside ``ring`` and farther than the fillet radius from its concave and root corners."""

    radius = PROFILE["outline"]["outline_fillet_radius_mm"]
    corners = _ring_corners(ring, root)
    return [
        point for point in board["outline"]["points"]
        if point[1] > root + 1e-9 and not inside_or_on(point, ring) and not any(math.dist(point, corner) <= radius + EPSILON for corner in corners)
    ]


def _layout_digest(result: dict) -> str:
    boards = {key: {name: value for name, value in board.items() if name not in ("verification", "svg")} for key, board in result["boards"].items()}
    return hashlib.sha256(_canonical_json(boards).encode("utf-8")).hexdigest()


def _strip_mask(design: dict) -> dict:
    plain = copy.deepcopy(design)
    del plain["matrix"]["mask"]
    return plain


def _ray(ring, level: float, axis: int) -> float:
    """The farthest crossing of the ring with the line ``x = level`` (``axis`` 0: the highest y) or ``y = level`` (1: the largest x)."""

    other = 1 - axis
    hits = [
        a[other] + (b[other] - a[other]) * (level - a[axis]) / (b[axis] - a[axis])
        for a, b in edges(ring)
        if (a[axis] > level) != (b[axis] > level)
    ]
    return max(hits)


def _box_ring(box) -> list:
    x0, y0, x1, y1 = box
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _number(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


if __name__ == "__main__":
    unittest.main()
