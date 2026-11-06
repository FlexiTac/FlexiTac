"""Independent stdlib geometry used by the geometry regression tests.

These helpers deliberately re-implement the few predicates the tests need
instead of importing ``engine.geometry``/``engine.drc``, so a defect in the
engine's own measurements cannot hide itself.
"""

from __future__ import annotations

import math
import re
from typing import Any, Iterable, Mapping, Sequence

_GERBER_VERTEX = re.compile(r"X(-?\d+)Y(-?\d+)D0([12])\*")


def bounds(rect: Mapping[str, Any]) -> tuple[float, float, float, float]:
    x, y, w, h = (float(rect[key]) for key in ("x", "y", "width_mm", "height_mm"))
    if rect["anchor"] == "center":
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    assert rect["anchor"] == "lower_left", rect["anchor"]
    return (x, y, x + w, y + h)


def edges(polygon: Sequence[Sequence[float]]) -> list[tuple[Sequence[float], Sequence[float]]]:
    return [(polygon[index], polygon[(index + 1) % len(polygon)]) for index in range(len(polygon))]


def point_segment_distance(p: Sequence[float], a: Sequence[float], b: Sequence[float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _side(o, a, b) -> float:
    """Signed distance of ``b`` from the line ``o``-``a``."""

    length = math.hypot(a[0] - o[0], a[1] - o[1])
    return 0.0 if length == 0 else ((a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])) / length


def segments_cross(a, b, c, d, tolerance: float = 1e-9) -> bool:
    """Proper crossing; contacts within ``tolerance`` (flush edges) do not count."""

    def opposite(first: float, second: float) -> bool:
        return (first > tolerance and second < -tolerance) or (first < -tolerance and second > tolerance)

    return opposite(_side(a, b, c), _side(a, b, d)) and opposite(_side(c, d, a), _side(c, d, b))


def segment_distance(a, b, c, d) -> float:
    if segments_cross(a, b, c, d):
        return 0.0
    return min(point_segment_distance(a, c, d), point_segment_distance(b, c, d), point_segment_distance(c, a, b), point_segment_distance(d, a, b))


def segment_box_distance(a, b, box) -> float:
    x0, y0, x1, y1 = box
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in (a, b)):
        return 0.0
    return min(segment_distance(a, b, corners[i], corners[(i + 1) % 4]) for i in range(4))


def point_in_polygon(p, polygon) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in edges(polygon):
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (x2 - x1) * (p[1] - y1) / (y2 - y1):
            inside = not inside
    return inside


def inside_or_on(p, polygon, tolerance: float = 1e-6) -> bool:
    return point_in_polygon(p, polygon) or any(point_segment_distance(p, a, b) <= tolerance for a, b in edges(polygon))


def polygon_inside(inner: Sequence[Sequence[float]], outer: Sequence[Sequence[float]], tolerance: float = 1e-6) -> bool:
    """Inner polygon inside (or flush with) the outer one."""

    if not all(inside_or_on(p, outer, tolerance) for p in inner):
        return False
    if not all(inside_or_on(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), outer, tolerance) for a, b in edges(inner)):
        return False
    return not any(segments_cross(a, b, c, d) for a, b in edges(inner) for c, d in edges(outer))


def box_polygon(box) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = box
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def copper(board: Mapping[str, Any]) -> list[tuple[str, str, Any]]:
    """(kind, net, geometry) where geometry is ('segment', a, b, radius) or ('box', bounds)."""

    layer = board["layers"]["top_copper"]
    items = []
    for route in layer["routes"]:
        for a, b in zip(route["points"], route["points"][1:]):
            items.append(("route", route["net"], ("segment", a, b, route["width_mm"] / 2)))
    for pad in layer["pads"]:
        items.append(("pad", pad["net"], ("box", bounds(pad))))
    for electrode in layer["electrodes"]:
        items.append(("electrode", electrode["net"], ("box", bounds(electrode))))
    return items


def distance_to_edges(geometry, polygon) -> float:
    if geometry[0] == "segment":
        _, a, b, radius = geometry
        return min(segment_distance(a, b, c, d) for c, d in edges(polygon)) - radius
    return min(segment_box_distance(c, d, geometry[1]) for c, d in edges(polygon))


def min_copper_to_outline(board: Mapping[str, Any]) -> float:
    rings = [board["outline"]["points"], *board["outline"]["cutouts"]]
    return min(distance_to_edges(geometry, ring) for _, _, geometry in copper(board) for ring in rings)


def turns_degrees(polygon: Sequence[Sequence[float]]) -> list[float]:
    """Signed turn at every vertex, positive = convex for the polygon interior."""

    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in edges(polygon))
    sign = 1.0 if area > 0 else -1.0
    turns = []
    count = len(polygon)
    for index in range(count):
        a, v, b = polygon[index - 1], polygon[index], polygon[(index + 1) % count]
        ux, uy, wx, wy = v[0] - a[0], v[1] - a[1], b[0] - v[0], b[1] - v[1]
        turns.append(sign * math.degrees(math.atan2(ux * wy - uy * wx, ux * wx + uy * wy)))
    return turns


def cross_section(polygon: Sequence[Sequence[float]], level: float, center: float, axis: int = 1) -> float:
    """Width of the polygon interval that contains ``center`` on the line axis=level."""

    other = 1 - axis
    hits = sorted(
        a[other] + (b[other] - a[other]) * (level - a[axis]) / (b[axis] - a[axis])
        for a, b in edges(polygon)
        if (a[axis] > level) != (b[axis] > level)
    )
    for low, high in zip(hits[::2], hits[1::2]):
        if low - 1e-9 <= center <= high + 1e-9:
            return high - low
    return 0.0


def levels_between(polygon: Iterable[Sequence[float]], low: float, high: float, axis: int = 1) -> list[float]:
    values = {low, high, (low + high) / 2}
    values.update(float(p[axis]) for p in polygon if low <= p[axis] <= high)
    probes = []
    for value in sorted(values):
        for probe in (value - 1e-7, value + 1e-7):
            if low <= probe <= high:
                probes.append(probe)
    return probes


def decode_gerber(text: str) -> tuple[list[list[tuple[float, float]]], list[list[tuple[float, float]]]]:
    """Strokes (D02 move then D01 draws) and closed G36/G37 regions of the
    exporter's RS-274X subset, in millimetres (FSLAX46Y46, MOMM)."""

    assert "%FSLAX46Y46*%" in text and "%MOMM*%" in text
    strokes: list[list[tuple[float, float]]] = []
    regions: list[list[tuple[float, float]]] = []
    contour = None
    for line in text.splitlines():
        if line == "G36*":
            contour = []
        elif line == "G37*":
            assert contour and contour[0] == contour[-1], "open region"
            regions.append(contour[:-1])
            contour = None
        else:
            vertex = _GERBER_VERTEX.fullmatch(line)
            if not vertex:
                continue
            point = (int(vertex[1]) / 1_000_000, int(vertex[2]) / 1_000_000)
            if contour is not None:
                contour.append(point)
            elif vertex[3] == "2":
                strokes.append([point])
            else:
                strokes[-1].append(point)
    return strokes, regions


def same_ring(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]], tolerance: float) -> bool:
    """Same closed vertex cycle (any start vertex, same direction) within ``tolerance``."""

    if len(first) != len(second) or not first:
        return False
    for shift in range(len(second)):
        if all(math.dist(first[index], second[(index + shift) % len(second)]) <= tolerance for index in range(len(first))):
            return True
    return False


def straight_channel(design: Any = None) -> Any:
    """A request for the straight Row channel: ``design`` (None: the default design) with ``routing.row_sides``
    ``channel`` where it names none, on the generic template (whose default is the diagonal Row bus since
    claude/specs/masked-field/P5-diagonal-bus.md section 18; ``channel`` builds the boards of before byte for byte, with
    the electrodes the request builds with: the default's 1.0 mm since the user's decision of 2026-11-06, 1.4 before).
    Anything else (another template, a value given, not an object) is returned as it is."""

    if design is None:
        design = {}
    if not isinstance(design, Mapping) or design.get("template_id", "generic_matrix_v1") != "generic_matrix_v1":
        return design
    routing = design.get("routing")
    if routing is not None and not isinstance(routing, Mapping):
        return design
    if isinstance(routing, Mapping) and "row_sides" in routing:
        return design
    return {**design, "routing": {**(routing or {}), "row_sides": "channel"}}
