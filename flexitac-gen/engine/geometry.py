"""Pure-stdlib 2D geometry shared by the layout builder, DRC, SVG and exporter.

All coordinates are millimetres in a Y-up frame.  Layout rectangles carry an
explicit ``anchor`` (``"center"`` for connector pads, ``"lower_left"`` for
electrodes and coverlay openings); :func:`rect_bounds` is the single place
that turns an anchored rectangle into bounds.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from typing import Any, Iterable, Mapping, Sequence

Bounds = tuple  # (min_x, min_y, max_x, max_y)

ANCHORS = ("center", "lower_left")
# Floating-point guards for predicates (not manufacturing rules).
_TINY = 1e-12
_CONCAVE_TURN_TINY = 1e-9  # rad: flatter vertices are straight within float noise
# Rolling-circle fillets search this many radii of boundary on each side of a
# corner and halve the radius at most this often where no circle fits.
_FILLET_REACH_RADII = 4.0
_FILLET_HALVINGS = 6
_AREA_NOISE = 1e-9  # relative rounding error of a polygon area


def rect_bounds(rect: Mapping[str, Any]) -> Bounds:
    """Return ``(min_x, min_y, max_x, max_y)`` for an anchored layout rectangle."""

    x = float(rect["x"])
    y = float(rect["y"])
    width = float(rect["width_mm"])
    height = float(rect["height_mm"])
    anchor = rect["anchor"]
    if anchor == "center":
        return (x - width / 2, y - height / 2, x + width / 2, y + height / 2)
    if anchor == "lower_left":
        return (x, y, x + width, y + height)
    raise ValueError(f"unsupported rectangle anchor: {anchor!r}")


def rect_corners(rect: Mapping[str, Any]) -> list[list[float]]:
    """Return the four corners of an anchored rectangle, counter-clockwise."""

    return bounds_corners(rect_bounds(rect))


def bounds_corners(bounds: Bounds) -> list[list[float]]:
    min_x, min_y, max_x, max_y = bounds
    return [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]


def anchored_rect(x0: float, y0: float, x1: float, y1: float, anchor: str) -> dict[str, Any]:
    """Express bounds as the ``x, y, width_mm, height_mm`` fields of ``anchor``."""

    if anchor == "center":
        x, y = (x0 + x1) / 2, (y0 + y1) / 2
    elif anchor == "lower_left":
        x, y = x0, y0
    else:
        raise ValueError(f"unsupported rectangle anchor: {anchor!r}")
    return {
        "anchor": anchor,
        "x": round6(x),
        "y": round6(y),
        "width_mm": round6(x1 - x0),
        "height_mm": round6(y1 - y0),
    }


def round6(value: float) -> float:
    """Snap to the 1e-6 mm layout grid (the emitted JSON/Gerber resolution)."""

    rounded = round(float(value), 6)
    return 0.0 if rounded == 0 else rounded


def ceil6(value: float) -> float:
    """Smallest 1e-6 mm grid value that is not below ``value`` (beyond float noise)."""

    snapped = round6(value)
    return snapped if snapped >= value - _TINY else round6(snapped + 1e-6)


def floor6(value: float) -> float:
    """Largest 1e-6 mm grid value that is not above ``value`` (beyond float noise)."""

    snapped = round6(value)
    return snapped if snapped <= value + _TINY else round6(snapped - 1e-6)


def rotate_quarter(point: Sequence[float], turns: int) -> list[float]:
    """Rotate a point counter-clockwise by ``turns`` quarter turns about the origin."""

    x, y = float(point[0]), float(point[1])
    turns %= 4
    if turns == 1:
        return [-y, x]
    if turns == 2:
        return [-x, -y]
    if turns == 3:
        return [y, -x]
    return [x, y]


def bounds_of(points: Iterable[Sequence[float]]) -> Bounds:
    points = list(points)
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def signed_area(points: Sequence[Sequence[float]]) -> float:
    total = 0.0
    for index, first in enumerate(points):
        second = points[(index + 1) % len(points)]
        total += float(first[0]) * float(second[1]) - float(second[0]) * float(first[1])
    return total / 2


def clean_polyline(points: Sequence[Sequence[float]], *, closed: bool = False, tolerance: float = 1e-9) -> list[list[float]]:
    """Drop repeated and collinear interior vertices."""

    answer: list[list[float]] = []
    for point in points:
        point = [float(point[0]), float(point[1])]
        if answer and math.dist(answer[-1], point) <= tolerance:
            continue
        answer.append(point)
    if closed and len(answer) > 1 and math.dist(answer[0], answer[-1]) <= tolerance:
        answer.pop()
    changed = True
    while changed and len(answer) > (3 if closed else 2):
        changed = False
        count = len(answer)
        indices = range(count) if closed else range(1, count - 1)
        for index in indices:
            before = answer[index - 1]
            current = answer[index]
            after = answer[(index + 1) % count]
            if _collinear_forward(before, current, after, tolerance):
                del answer[index]
                changed = True
                break
    return answer


def _collinear_forward(before: Sequence[float], current: Sequence[float], after: Sequence[float], tolerance: float) -> bool:
    """True when ``current`` lies on the chord ``before``-``after`` (within tolerance)."""

    cx, cy = after[0] - before[0], after[1] - before[1]
    chord = math.hypot(cx, cy)
    if chord <= _TINY:
        return False
    ax, ay = current[0] - before[0], current[1] - before[1]
    deviation = abs(ax * cy - ay * cx) / chord
    along = (ax * cx + ay * cy) / (chord * chord)
    return deviation <= tolerance and 0.0 < along < 1.0


def _unit(dx: float, dy: float) -> tuple[float, float]:
    length = math.hypot(dx, dy)
    if length <= _TINY:
        raise ValueError("zero-length segment")
    return dx / length, dy / length


def turn_angle(before: Sequence[float], current: Sequence[float], after: Sequence[float]) -> float:
    """Signed turning angle at ``current`` in radians (positive = left turn)."""

    ux, uy = _unit(current[0] - before[0], current[1] - before[1])
    vx, vy = _unit(after[0] - current[0], after[1] - current[1])
    return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)


def offset_polyline(
    points: Sequence[Sequence[float]], distance: float, *, left: bool, arc_step_rad: float
) -> list[list[float]]:
    """Return the true one-sided offset of an open polyline.

    Every segment is moved ``distance`` along its own normal.  On the convex
    side of a bend the gap is closed by a round join drawn as a circumscribed
    polygon, so no point of the result comes closer than ``distance`` to the
    bend vertex.  On the concave side the two offset lines are trimmed at
    their intersection.  The input must not fold back within ``distance`` of
    itself (true for the monotone fan-out routes built here).
    """

    pts = clean_polyline(points)
    if len(pts) < 2:
        raise ValueError("offset requires at least two distinct points")
    side = 1.0 if left else -1.0
    directions = [_unit(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    normals = [(-dy * side, dx * side) for dx, dy in directions]
    answer = [[pts[0][0] + normals[0][0] * distance, pts[0][1] + normals[0][1] * distance]]
    for index in range(1, len(pts) - 1):
        (ux, uy), (vx, vy) = directions[index - 1], directions[index]
        cross = ux * vy - uy * vx
        turn = math.atan2(cross, ux * vx + uy * vy)
        if abs(turn) <= 1e-12:
            continue
        vertex = pts[index]
        outer = turn < 0 if left else turn > 0
        if outer:
            sweep = abs(turn)
            steps = max(1, math.ceil(sweep / arc_step_rad - 1e-9))
            delta = sweep / steps
            radius = distance / math.cos(delta / 2)
            start = math.atan2(normals[index - 1][1], normals[index - 1][0])
            sign = 1.0 if turn > 0 else -1.0
            for step in range(steps):
                angle = start + sign * (step + 0.5) * delta
                answer.append([vertex[0] + radius * math.cos(angle), vertex[1] + radius * math.sin(angle)])
        else:
            (n0x, n0y), (n1x, n1y) = normals[index - 1], normals[index]
            p0x, p0y = vertex[0] + n0x * distance, vertex[1] + n0y * distance
            p1x, p1y = vertex[0] + n1x * distance, vertex[1] + n1y * distance
            along = ((p1x - p0x) * vy - (p1y - p0y) * vx) / cross
            answer.append([p0x + ux * along, p0y + uy * along])
    answer.append([pts[-1][0] + normals[-1][0] * distance, pts[-1][1] + normals[-1][1] * distance])
    return answer


def convex_corner_arc(
    corner: Sequence[float], incoming: Sequence[float], outgoing: Sequence[float], radius: float, arc_step_rad: float
) -> list[list[float]]:
    """Round a convex polygon corner with a circumscribed arc of ``radius``.

    ``incoming`` and ``outgoing`` are unit directions of the edges entering
    and leaving ``corner``.  The returned vertices replace the corner; all of
    them lie on or outside the true arc, so the rounded outline keeps every
    edge distance of the corner region.
    """

    ux, uy = incoming
    vx, vy = outgoing
    turn = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    if turn <= 0:
        raise ValueError("convex_corner_arc expects a left (convex) turn")
    tangent = radius * math.tan(turn / 2)
    first = [corner[0] - ux * tangent, corner[1] - uy * tangent]
    # The centre lies to the left of the incoming edge.
    center = [first[0] - uy * radius, first[1] + ux * radius]
    start = math.atan2(first[1] - center[1], first[0] - center[0])
    steps = max(1, math.ceil(turn / arc_step_rad - 1e-9))
    delta = turn / steps
    outer = radius / math.cos(delta / 2)
    return [
        [center[0] + outer * math.cos(start + (step + 0.5) * delta), center[1] + outer * math.sin(start + (step + 0.5) * delta)]
        for step in range(steps)
    ]


def fillet_concave_corners(
    points: Sequence[Sequence[float]], radius: float, *, arc_step_rad: float, fixed: Iterable[Sequence[float]] = (),
    min_turn_rad: float = _CONCAVE_TURN_TINY, touched: list[list[float]] | None = None,
) -> tuple[list[list[float]], float | None]:
    """Fillet the concave corners of a counter-clockwise polygon with a rolling circle.

    At each concave vertex the fillet is the arc of the ``radius`` circle
    that lies outside the polygon, touches its boundary on both sides of the
    vertex and contains none of it -- the boundary of a morphological
    closing.  The circle may touch beyond short edges and the convex round
    joins next to a corner, and one circle absorbs the nearby corners it
    covers.  Arc vertices lie on the circle, so fillets only add board
    material and never reduce a copper clearance.  Where no such circle fits
    ("where geometry allows") the radius is halved.  Returns the new polygon
    and the smallest radius used (``None`` without concave corners, ``0.0``
    if a corner had to stay sharp).  ``fixed``: vertices filleted already
    (a part of the outline shared with another board), never filleted again.
    ``min_turn_rad``: a vertex turning less than this is no corner (a
    caller on a grid passes the turn below which a fillet of ``radius``
    would not leave the corner's grid step).  ``touched``: a list that
    receives every fillet's vertices, its two touch points included (a
    touch on a convex vertex is that vertex), and every corner left sharp.
    """

    pts = clean_polyline(points, closed=True)
    start = tuple(pts[0]) if pts else None
    arcs: set[tuple[float, float]] = {tuple(point) for point in fixed}
    smallest: float | None = None
    while True:
        count = len(pts)
        turns = [turn_angle(pts[index - 1], pts[index], pts[(index + 1) % count]) for index in range(count)]
        corner = next(
            (index for index in range(count) if turns[index] < -min_turn_rad and tuple(pts[index]) not in arcs),
            None,
        )
        if corner is None:
            # Keep the input's first vertex first when it survives (stable output order).
            first = next((index for index, point in enumerate(pts) if tuple(point) == start), 0)
            return pts[first:] + pts[:first], smallest
        used, result = radius, None
        for _ in range(_FILLET_HALVINGS):
            result = _rolling_fillet(pts, turns, corner, used, arc_step_rad)
            if result is not None:
                break
            used /= 2
        if result is None:
            arcs.add(tuple(pts[corner]))  # nothing fits: the corner stays sharp
            used = 0.0
            if touched is not None:
                touched.append(list(pts[corner]))
        else:
            pts, arc = result
            arcs.update(tuple(point) for point in arc)
            if touched is not None:
                touched.extend(list(point) for point in arc)
        smallest = used if smallest is None else min(smallest, used)


def _rolling_fillet(
    pts: list[list[float]], turns: list[float], corner: int, radius: float, arc_step_rad: float
) -> tuple[list[list[float]], list[list[float]]] | None:
    """Splice the rolling-circle fillet of one concave vertex into ``pts``.

    Candidate circles touch one boundary primitive (edge or convex vertex)
    behind the corner and one ahead of it; the one nearest the corner whose
    open disk is free of boundary and lies outside the polygon wins.
    Returns ``(new polygon, arc vertices)`` or ``None`` when none fits.
    """

    count = len(pts)
    reach = _FILLET_REACH_RADII * radius
    limit = max(1, (count - 2) // 2)
    behind = _walk(pts, corner, -1, reach, limit)  # edge k runs pts[k] -> pts[k + 1]
    ahead = _walk(pts, corner, 1, reach, limit)
    first = [("edge", k) for k in behind] + [("vertex", k) for k in behind if turns[k] > 0]
    second = [("edge", k) for k in ahead] + [("vertex", (k + 1) % count) for k in ahead if turns[(k + 1) % count] > 0]
    vertex = pts[corner]
    candidates = []
    for one in first:
        for other in second:
            for center, touch_a, touch_b in _touching_circles(pts, one, other, radius):
                candidates.append((math.dist(center, vertex), center, touch_a, touch_b))
    candidates.sort(key=lambda candidate: candidate[0])
    area = signed_area(pts)
    for _, center, touch_a, touch_b in candidates:
        if not _disk_is_free(pts, center, radius) or point_in_polygon(center, pts):
            continue
        start = math.atan2(touch_a[0][1] - center[1], touch_a[0][0] - center[0])
        finish = math.atan2(touch_b[0][1] - center[1], touch_b[0][0] - center[0])
        sweep = (start - finish) % (2 * math.pi)  # clockwise: the boundary turns right
        if not _TINY < sweep <= math.pi + 1e-9:
            continue
        steps = max(1, math.ceil(sweep / arc_step_rad - 1e-9))
        arc = [list(touch_a[0])]
        arc += [
            [center[0] + radius * math.cos(start - sweep * step / steps), center[1] + radius * math.sin(start - sweep * step / steps)]
            for step in range(1, steps)
        ]
        arc.append(list(touch_b[0]))
        spliced = _splice(pts, touch_a, touch_b, arc)
        # Fillets only add material; the guard is relative because a nearly
        # flat corner adds less area than the shoelace sum's rounding error.
        if spliced is not None and signed_area(spliced) >= area - _AREA_NOISE * max(1.0, abs(area)):
            return clean_polyline(spliced, closed=True), arc
    return None


def _walk(pts: list[list[float]], corner: int, direction: int, reach: float, limit: int) -> list[int]:
    """Indices of the edges met walking from ``corner`` (back: -1, ahead: +1) up to ``reach``."""

    count = len(pts)
    edges, length = [], 0.0
    index = corner - 1 if direction < 0 else corner
    for _ in range(limit):
        edge = index % count
        edges.append(edge)
        length += math.dist(pts[edge], pts[(edge + 1) % count])
        if length >= reach:
            break
        index += direction
    return edges


def _touching_circles(pts: list[list[float]], one: tuple[str, int], other: tuple[str, int], radius: float):
    """Centres of ``radius`` circles touching two primitives on the exterior side.

    Yields ``(center, (touch point, edge, fraction), (touch point, edge,
    fraction))``; a touch at a vertex is fraction 0 of the edge it starts.
    """

    count = len(pts)

    def line(edge: int):
        a, b = pts[edge], pts[(edge + 1) % count]
        length = math.dist(a, b)
        if length <= _TINY:
            return None
        dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        # The exterior of a counter-clockwise polygon lies right of each edge.
        return a, (dx, dy), length, (a[0] + dy * radius, a[1] - dx * radius)

    def on_edge(edge: int, length: float, along: float):
        fraction = min(max(along / length, 0.0), 1.0)
        a, b = pts[edge], pts[(edge + 1) % count]
        point = (a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction)
        return (point, (edge + 1) % count, 0.0) if fraction >= 1.0 - _TINY else (point, edge, fraction)

    def at_vertex(index: int):
        return (tuple(pts[index]), index, 0.0)

    tolerance = 1e-9
    kinds = (one[0], other[0])
    if kinds == ("edge", "edge"):
        first, second = line(one[1]), line(other[1])
        if first is None or second is None:
            return
        _, (ux, uy), length_a, (ax, ay) = first
        _, (vx, vy), length_b, (bx, by) = second
        cross = ux * vy - uy * vx
        if abs(cross) <= _TINY:
            return
        wx, wy = bx - ax, by - ay
        along_a = (wx * vy - wy * vx) / cross
        along_b = (wx * uy - wy * ux) / cross
        if -tolerance <= along_a <= length_a + tolerance and -tolerance <= along_b <= length_b + tolerance:
            yield (ax + ux * along_a, ay + uy * along_a), on_edge(one[1], length_a, along_a), on_edge(other[1], length_b, along_b)
        return
    if kinds == ("vertex", "vertex"):
        p, q = pts[one[1]], pts[other[1]]
        distance = math.dist(p, q)
        if distance <= _TINY or distance > 2 * radius:
            return
        half = math.sqrt(max(0.0, radius * radius - distance * distance / 4))
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        nx, ny = -(q[1] - p[1]) / distance, (q[0] - p[0]) / distance
        for sign in (1.0, -1.0):
            yield (mx + sign * half * nx, my + sign * half * ny), at_vertex(one[1]), at_vertex(other[1])
        return
    # One edge and one vertex: the centre lies on the edge's offset line at
    # ``radius`` from the vertex.
    edge, point = (one[1], other[1]) if kinds[0] == "edge" else (other[1], one[1])
    parts = line(edge)
    if parts is None:
        return
    _, (ux, uy), length, (ox, oy) = parts
    q = pts[point]
    px, py = ox - q[0], oy - q[1]
    projection = px * ux + py * uy
    discriminant = projection * projection - (px * px + py * py) + radius * radius
    if discriminant < 0:
        return
    root = math.sqrt(discriminant)
    for along in (-projection - root, -projection + root):
        if -tolerance <= along <= length + tolerance:
            center = (ox + ux * along, oy + uy * along)
            touch_edge, touch_vertex = on_edge(edge, length, along), at_vertex(point)
            yield (center, touch_edge, touch_vertex) if kinds[0] == "edge" else (center, touch_vertex, touch_edge)


def _disk_is_free(pts: list[list[float]], center: Sequence[float], radius: float) -> bool:
    """No boundary point lies inside the open disk (touching is allowed)."""

    floor = radius - 1e-9
    count = len(pts)
    for index in range(count):
        a, b = pts[index], pts[(index + 1) % count]
        if (
            min(a[0], b[0]) - radius < center[0] < max(a[0], b[0]) + radius
            and min(a[1], b[1]) - radius < center[1] < max(a[1], b[1]) + radius
            and point_segment_distance(center, a, b) < floor
        ):
            return False
    return True


def _splice(pts: list[list[float]], touch_a, touch_b, arc: list[list[float]]) -> list[list[float]] | None:
    """Replace the boundary from ``touch_a`` (behind the corner) to ``touch_b`` with ``arc``."""

    count = len(pts)
    (_, edge_a, fraction_a), (_, edge_b, _) = touch_a, touch_b
    # Kept vertices run from the one after touch_b's edge start round to the
    # last one before touch_a (touch_a itself when it is a vertex).
    first = (edge_b + 1) % count
    last = edge_a if fraction_a > 0.0 else (edge_a - 1) % count
    kept = (last - first) % count + 1
    if kept >= count:  # nothing would be removed
        return None
    return [list(arc[-1]), *(pts[(first + step) % count] for step in range(kept)), *arc[:-1]]


def arc_polygon_rounded_rect(bounds: Bounds, radius: float, arc_step_rad: float) -> list[list[float]]:
    """Counter-clockwise rounded rectangle; arc vertices lie on the true arc."""

    min_x, min_y, max_x, max_y = bounds
    radius = min(radius, (max_x - min_x) / 2, (max_y - min_y) / 2)
    if radius <= 0:
        return bounds_corners(bounds)
    steps = max(1, math.ceil((math.pi / 2) / arc_step_rad - 1e-9))
    answer: list[list[float]] = []
    corners = (
        (max_x - radius, min_y + radius, -math.pi / 2),
        (max_x - radius, max_y - radius, 0.0),
        (min_x + radius, max_y - radius, math.pi / 2),
        (min_x + radius, min_y + radius, math.pi),
    )
    for center_x, center_y, start in corners:
        for step in range(steps + 1):
            angle = start + (math.pi / 2) * step / steps
            answer.append([center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)])
    return clean_polyline(answer, closed=True)


def point_segment_distance(point: Sequence[float], first: Sequence[float], second: Sequence[float]) -> float:
    dx = second[0] - first[0]
    dy = second[1] - first[1]
    length_squared = dx * dx + dy * dy
    if length_squared <= _TINY:
        return math.hypot(point[0] - first[0], point[1] - first[1])
    fraction = ((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / length_squared
    fraction = 0.0 if fraction < 0 else 1.0 if fraction > 1 else fraction
    return math.hypot(point[0] - first[0] - fraction * dx, point[1] - first[1] - fraction * dy)


def _orientation(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(a: Sequence[float], b: Sequence[float], c: Sequence[float], d: Sequence[float]) -> bool:
    """Inclusive segment intersection test (touching counts)."""

    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if ((o1 > 0 and o2 < 0) or (o1 < 0 and o2 > 0)) and ((o3 > 0 and o4 < 0) or (o3 < 0 and o4 > 0)):
        return True
    return (
        (o1 == 0 and _within_box(c, a, b))
        or (o2 == 0 and _within_box(d, a, b))
        or (o3 == 0 and _within_box(a, c, d))
        or (o4 == 0 and _within_box(b, c, d))
    )


def _within_box(point: Sequence[float], first: Sequence[float], second: Sequence[float]) -> bool:
    return (
        min(first[0], second[0]) <= point[0] <= max(first[0], second[0])
        and min(first[1], second[1]) <= point[1] <= max(first[1], second[1])
    )


def segment_distance(a: Sequence[float], b: Sequence[float], c: Sequence[float], d: Sequence[float]) -> float:
    if segments_intersect(a, b, c, d):
        return 0.0
    return min(
        point_segment_distance(a, c, d),
        point_segment_distance(b, c, d),
        point_segment_distance(c, a, b),
        point_segment_distance(d, a, b),
    )


def point_box_distance(point: Sequence[float], box: Bounds) -> float:
    min_x, min_y, max_x, max_y = box
    dx = max(min_x - point[0], 0.0, point[0] - max_x)
    dy = max(min_y - point[1], 0.0, point[1] - max_y)
    return math.hypot(dx, dy)


def segment_box_distance(first: Sequence[float], second: Sequence[float], box: Bounds) -> float:
    """Distance between a segment and a closed axis-aligned box (0 on contact)."""

    min_x, min_y, max_x, max_y = box
    if point_box_distance(first, box) == 0.0 or point_box_distance(second, box) == 0.0:
        return 0.0
    corners = ((min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y))
    for index in range(4):
        if segments_intersect(first, second, corners[index], corners[(index + 1) % 4]):
            return 0.0
    return min(
        point_box_distance(first, box),
        point_box_distance(second, box),
        *(point_segment_distance(corner, first, second) for corner in corners),
    )


def box_gap(first: Bounds, second: Bounds) -> float:
    dx = max(0.0, second[0] - first[2], first[0] - second[2])
    dy = max(0.0, second[1] - first[3], first[1] - second[3])
    return math.hypot(dx, dy)


def point_in_polygon(point: Sequence[float], polygon: Sequence[Sequence[float]]) -> bool:
    """Even-odd ray test; points on the boundary may report either value."""

    x, y = point
    inside = False
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        if (y1 > y) != (y2 > y):
            crossing = x1 + (x2 - x1) * (y - y1) / (y2 - y1)
            if x < crossing:
                inside = not inside
    return inside


def polygon_edges(polygon: Sequence[Sequence[float]]) -> list[tuple[Sequence[float], Sequence[float]]]:
    return [(polygon[index], polygon[(index + 1) % len(polygon)]) for index in range(len(polygon))]


def clip_ring_above(ring: Sequence[Sequence[float]], level: float, tolerance: float = 1e-9) -> list[list[float]]:
    """The part of a closed ring above ``level`` (a point within ``tolerance`` of it counts as on it, an edge lying on
    it as below it): one ring for a region whose part above the level is connected (a y-monotone one), its cut along
    the level."""

    answer = []
    count = len(ring)
    for index in range(count):
        a, b = ring[index], ring[(index + 1) % count]
        inside_a, inside_b = a[1] > level + tolerance, b[1] > level + tolerance
        if inside_a:
            answer.append([float(a[0]), float(a[1])])
        if inside_a != inside_b:
            fraction = (level - a[1]) / (b[1] - a[1])
            answer.append([a[0] + (b[0] - a[0]) * fraction, level])
    return clean_polyline(answer, closed=True) if len(answer) > 2 else answer


def ring_deviation(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]], reach: float) -> float:
    """The largest distance from a vertex of either ring to the other ring's boundary, up to ``reach`` (``reach`` for
    a vertex farther than that): 0 for two rings that coincide."""

    worst = 0.0
    for one, other in ((first, second), (second, first)):
        edges = polygon_edges(other)
        buckets: dict[tuple[int, int], list[int]] = {}
        for index, (a, b) in enumerate(edges):
            for cell_x in range(math.floor((min(a[0], b[0]) - reach) / reach), math.floor((max(a[0], b[0]) + reach) / reach) + 1):
                for cell_y in range(math.floor((min(a[1], b[1]) - reach) / reach), math.floor((max(a[1], b[1]) + reach) / reach) + 1):
                    buckets.setdefault((cell_x, cell_y), []).append(index)
        for point in one:
            best = reach
            for index in buckets.get((math.floor(point[0] / reach), math.floor(point[1] / reach)), ()):
                best = min(best, point_segment_distance(point, *edges[index]))
            worst = max(worst, best)
    return worst


# --------------------------------------------------------------------------
# Orthogonally convex regions (the masked taxel field, its windows and body).
# --------------------------------------------------------------------------


def band_union(bands: Sequence[Bounds], axis: int) -> list[Bounds]:
    """Bands and the fillers between them: the parts of an orthogonally convex region.

    ``bands`` are boxes ``(min_x, min_y, max_x, max_y)`` stacked along
    ``axis`` (1: rows stacked in y, 0: columns stacked in x), in that order,
    each overlapping the next across the other axis.  Between consecutive
    bands that do not touch, the filler spans the gap and the bands' common
    extent.  Returns the bands followed by the fillers, in order.
    """

    along = 1 - axis
    fillers = []
    for first, second in zip(bands, bands[1:]):
        if second[axis] - first[axis + 2] <= _TINY:
            continue
        low, high = max(first[along], second[along]), min(first[along + 2], second[along + 2])
        if high - low <= _TINY:
            raise ValueError("consecutive bands share no extent")
        filler = [0.0, 0.0, 0.0, 0.0]
        filler[axis], filler[axis + 2] = first[axis + 2], second[axis]
        filler[along], filler[along + 2] = low, high
        fillers.append(tuple(filler))
    return [*bands, *fillers]


def band_ring(bands: Sequence[Bounds], axis: int) -> list[list[float]]:
    """Counter-clockwise ring of :func:`band_union` (bands on the layout grid, stacked along ``axis``)."""

    return orthoconvex_ring(rect_union_slabs(band_union(bands, axis), axis), axis)


def rect_union_slabs(rects: Sequence[Bounds], axis: int) -> list[tuple[float, float, float, float]]:
    """The union of boxes as slabs stacked along ``axis``, one interval each.

    Returns ``[(low, high, start, end)]`` in ascending order: the slab spans
    ``[low, high]`` along ``axis`` (y for 1, x for 0) and ``[start, end]``
    across it; neighbouring slabs with the same interval are merged.  The
    boxes are on the 1e-6 mm layout grid; the union must be one interval at
    every level and have no gap (an orthogonally convex region), otherwise
    ``ValueError``.
    """

    across = 1 - axis
    levels = sorted({value for rect in rects for value in (rect[axis], rect[axis + 2])})
    slabs: list[tuple[float, float, float, float]] = []
    for low, high in zip(levels, levels[1:]):
        cover = sorted(
            (rect[across], rect[across + 2]) for rect in rects if rect[axis] <= low + _TINY and rect[axis + 2] >= high - _TINY
        )
        if not cover:
            raise ValueError("the region has a gap")
        start, end = cover[0]
        for first, last in cover[1:]:
            if first > end + _TINY:
                raise ValueError("the region is not one interval at every level")
            end = max(end, last)
        if slabs and slabs[-1][1] == low and slabs[-1][2] == start and slabs[-1][3] == end:
            slabs[-1] = (slabs[-1][0], high, start, end)
        else:
            slabs.append((low, high, start, end))
    return slabs


def orthoconvex_ring(slabs: Sequence[tuple[float, float, float, float]], axis: int) -> list[list[float]]:
    """Counter-clockwise ring of slabs from :func:`rect_union_slabs`, on the layout grid.

    For y-slabs (``axis`` 1) the ring rises along the right ends and comes
    down along the left ends; for x-slabs (``axis`` 0) it runs right along
    the bottoms and back along the tops.  Collinear vertices are dropped.
    """

    if axis == 1:
        forward = [point for low, high, _, end in slabs for point in ([end, low], [end, high])]
        back = [point for low, high, start, _ in reversed(slabs) for point in ([start, high], [start, low])]
    else:
        forward = [point for low, high, start, _ in slabs for point in ([low, start], [high, start])]
        back = [point for low, high, _, end in reversed(slabs) for point in ([high, end], [low, end])]
    return [[round6(x), round6(y)] for x, y in clean_polyline([*forward, *back], closed=True)]


def is_rectilinear(ring: Sequence[Sequence[float]], tolerance: float) -> bool:
    """Every edge of the closed ring is horizontal or vertical (within ``tolerance``)."""

    return all(abs(a[0] - b[0]) <= tolerance or abs(a[1] - b[1]) <= tolerance for a, b in polygon_edges(ring))


def is_orthogonally_convex(ring: Sequence[Sequence[float]]) -> bool:
    """Every horizontal and every vertical line meets the (simple) ring's region in at most one interval.

    Between consecutive vertex levels each line crosses the edges spanning
    that level; the region is one interval there exactly when two do.  The
    counts come from the edges' spans over the sorted levels (no pairwise
    scan), so a ring of ``n`` vertices costs ``O(n log n)``.
    """

    for axis in (0, 1):
        levels = sorted({float(point[axis]) for point in ring})
        counts = [0] * len(levels)
        for a, b in polygon_edges(ring):
            low, high = sorted((float(a[axis]), float(b[axis])))
            if high - low <= _TINY:
                continue
            counts[bisect_left(levels, low)] += 1
            counts[bisect_left(levels, high)] -= 1
        crossing = 0
        for count in counts[:-1]:
            crossing += count
            if crossing != 2:
                return False
    return True


def clip_segment_outside_box(first: Sequence[float], second: Sequence[float], box: Bounds) -> list[tuple[list[float], list[float]]]:
    """The parts of the segment ``first``-``second`` outside the closed box: none, one or two (Liang-Barsky).

    A segment that only touches the box stays whole; parts shorter than the
    float guard are dropped.
    """

    a = [float(first[0]), float(first[1])]
    b = [float(second[0]), float(second[1])]
    dx, dy = b[0] - a[0], b[1] - a[1]
    enter, leave = 0.0, 1.0
    for p, q in ((-dx, a[0] - box[0]), (dx, box[2] - a[0]), (-dy, a[1] - box[1]), (dy, box[3] - a[1])):
        if abs(p) <= _TINY:
            if q < 0:
                return [(a, b)]  # parallel to this side and outside it
            continue
        ratio = q / p
        if p < 0:
            enter = max(enter, ratio)
        else:
            leave = min(leave, ratio)
    if enter >= leave:
        return [(a, b)]
    parts = []
    length = math.hypot(dx, dy)
    if enter * length > _TINY:
        parts.append((a, [a[0] + dx * enter, a[1] + dy * enter]))
    if (1.0 - leave) * length > _TINY:
        parts.append(([a[0] + dx * leave, a[1] + dy * leave], b))
    return parts


def segment_parts_off_box_boundary(
    first: Sequence[float], second: Sequence[float], box: Bounds, tolerance: float
) -> list[tuple[Sequence[float], Sequence[float]]]:
    """The parts of an axis-parallel segment that do not lie on the boundary of ``box``.

    A segment on a side's line keeps the parts beyond that side's extent;
    any other segment is returned whole.
    """

    for axis in (0, 1):  # axis 1: a horizontal segment on the bottom or top side
        across = 1 - axis
        if abs(first[axis] - second[axis]) > tolerance:
            continue
        level = first[axis]
        if abs(level - box[axis]) > tolerance and abs(level - box[axis + 2]) > tolerance:
            continue
        low, high = sorted((float(first[across]), float(second[across])))
        cut_low, cut_high = max(low, box[across]), min(high, box[across + 2])
        if cut_high - cut_low <= tolerance:
            continue
        parts = []
        for start, end in ((low, cut_low), (cut_high, high)):
            if end - start > tolerance:
                point_a, point_b = [0.0, 0.0], [0.0, 0.0]
                point_a[axis] = point_b[axis] = float(level)
                point_a[across], point_b[across] = start, end
                parts.append((point_a, point_b))
        return parts
    return [(first, second)]
