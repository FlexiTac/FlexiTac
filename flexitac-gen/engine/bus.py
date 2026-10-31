"""Integer-nanometre primitives of the diagonal Row bus (``diagonal-bus/7``).

Every lane of the bus is the *west* convex chain (the taut string) from its
start, an electrode end, down to its target around a set of obstacle points;
the far side is built in the mirrored frame (x -> -x).  The next lane out
keeps east of the lane's keep-out: the mitred outer offset of the lane and
its continuation (the ray down from its last corner; diagonal-bus/1 also
continued lanes with corridor runs and jogs, which the primitives keep),
and a box around its start (claude/specs/masked-field/P5-diagonal-bus.md,
section 2.3).  A lane that follows a receding field turns inward once, at
its westmost corner, and its offset is cut there (:func:`lane_offset`), so
lanes nested around that turn keep the pitch without spreading outward.

All hull work is in integer nanometres, the 1e-6 mm grid of the layout
(``NM`` per mm), so the orientation tests are exact.  The only floats are
the positions of offset vertices, from IEEE operations and the correctly
rounded ``math.sqrt`` alone (no ``hypot`` or ``atan2``, whose last bit may
differ between Python versions and platforms), each rounded to the grid away
from the chain; the results are identical on every Python version.

Conventions: a point is an ``(x, y)`` tuple of ints, a box an
``(x0, y0, x1, y1)`` tuple of ints with ``x0 <= x1`` and ``y0 <= y1``; a
chain runs from the top (its start) down to the bottom (its target), and
"outside" is west (-x).
"""

from __future__ import annotations

import math
from typing import Iterable, NamedTuple, Optional, Sequence

NM = 1_000_000  # nm per mm: the layout grid
# Slanted offsets are built two grid steps farther than asked (engine.layout's _DIAGONAL_ALLOWANCE_MM): the grid
# rounding of the next lane's end points cannot bring a slanted section closer than the distance.
SLANT_ALLOWANCE_NM = 2
# Floating-point guard: an offset coordinate this close to a grid value is that value (not a manufacturing rule).
_GRID_NOISE_NM = 1e-6


def to_nm(value_mm: float) -> int:
    """A millimetre value on the 1e-6 mm grid as integer nanometres."""

    return int(round(value_mm * NM))


def to_mm(value_nm: int) -> float:
    """Integer nanometres as millimetres on the 1e-6 mm grid."""

    return round(value_nm / NM, 6)


def nm_box(x0: float, y0: float, x1: float, y1: float) -> tuple:
    """A box given in millimetres, in nanometres."""

    return (to_nm(x0), to_nm(y0), to_nm(x1), to_nm(y1))


def cross(o: Sequence[int], a: Sequence[int], b: Sequence[int]) -> int:
    """The exact orientation of ``o -> a -> b``: positive for a left (counter-clockwise) turn, 0 when collinear."""

    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def west_chain(start: Sequence[int], target: Sequence[int], obstacles: Iterable[Sequence[int]]) -> list:
    """The west convex chain from ``start`` (top) down to ``target`` (bottom) around ``obstacles``.

    Only obstacle points strictly between the two heights take part.  The
    chain keeps every such point on its east side or on it: Andrew's
    monotone chain over the points sorted by descending y, then ascending
    x, which pops a vertex unless it lies strictly west of the line from
    its predecessor to the next point (``cross <= 0``), so collinear points
    are dropped and every interior vertex is a strict left turn.  The
    points are deduplicated and sorted, so their order and repeats never
    reach the result.  With ``target`` below ``start`` the chain's heights
    strictly decrease.
    """

    start = (start[0], start[1])
    target = (target[0], target[1])
    top, bottom = start[1], target[1]
    points = sorted({(p[0], p[1]) for p in obstacles if bottom < p[1] < top}, key=lambda p: (-p[1], p[0]))
    chain = [start]
    for point in [*points, target]:
        while len(chain) >= 2 and cross(chain[-2], chain[-1], point) <= 0:
            chain.pop()
        chain.append(point)
    return chain


class _Segment(NamedTuple):
    a: tuple
    b: tuple
    dx: int
    dy: int
    length2: int  # dx * dx + dy * dy, exact
    length: float
    ux: float
    uy: float
    nx: float  # the west (right-hand) unit normal of the travel a -> b
    ny: float
    distance: int  # the offset of this segment: slanted ones carry SLANT_ALLOWANCE_NM more


def _segment(a: tuple, b: tuple, distance_nm: int) -> _Segment:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    length = math.sqrt(length2)
    ux, uy = dx / length, dy / length
    slanted = dx != 0 and dy != 0
    return _Segment(a, b, dx, dy, length2, length, ux, uy, uy, -ux, distance_nm + (SLANT_ALLOWANCE_NM if slanted else 0))


def _away(value: float, direction: float) -> int:
    """``value`` (nm) on the grid, rounded toward ``direction`` (away from the chain); within float noise of a grid
    value, or with no direction, the nearest grid value."""

    nearest = round(value)
    if direction == 0 or abs(value - nearest) < _GRID_NOISE_NM:
        return int(nearest)
    return math.floor(value) if direction < 0 else math.ceil(value)


def _vertex(base: tuple, ox: float, oy: float, direction_x: float, direction_y: float) -> tuple:
    """``base`` moved by the offset ``(ox, oy)``, each coordinate rounded away from the chain (``base`` is exact)."""

    return (base[0] + _away(ox, direction_x), base[1] + _away(oy, direction_y))


def mitred_offset(chain: Sequence[Sequence[int]], distance_nm: int) -> list:
    """The outer (west) offset vertices of a chain at ``distance_nm``, rounded to the grid away from it.

    Axis-parallel segments are offset by ``distance_nm`` exactly, slanted
    ones by ``distance_nm + SLANT_ALLOWANCE_NM``.  The first and the last
    vertex are the perpendicular ends; each join between them is
    :func:`_join`'s.  Repeated points are dropped; a chain of fewer than
    two distinct points has no offset.  Each coordinate is computed
    relative to its (exact) chain vertex and rounded away from the chain:
    along the normal at an end, along the bisector of the two normals at a
    join.
    """

    points: list = []
    for point in chain:
        point = (point[0], point[1])
        if not points or point != points[-1]:
            points.append(point)
    if len(points) < 2:
        return []
    segments = [_segment(a, b, distance_nm) for a, b in zip(points, points[1:])]
    first, last = segments[0], segments[-1]
    answer = [_vertex(first.a, first.nx * first.distance, first.ny * first.distance, first.nx, first.ny)]
    for one, two in zip(segments, segments[1:]):
        answer.extend(_join(one, two))
    answer.append(_vertex(last.b, last.nx * last.distance, last.ny * last.distance, last.nx, last.ny))
    return answer


def _join(one: _Segment, two: _Segment) -> list:
    """The offset vertices at the join of two consecutive segments.

    * Straight on: one vertex.
    * A convex join (a left turn, the offset on its outer side) up to a
      turn of 120 degrees (the mitre then stays within twice the distance
      of the vertex), and any concave join (a right turn): the
      intersection of the two offset lines, the mitre or the trim.
    * A sharper convex turn, or a reversal: a square join, each offset
      line carried on by its distance past the vertex (the mitre would
      grow without bound; a bevel would cut within the distance).
    * Two nearly parallel segments with different distances (an
      axis-parallel and a slanted one), whose offset lines meet farther
      than the larger distance along the first: a step, both
      perpendicular ends at the larger distance D (the turn's sine is
      then under (D - d) / D, so each end stays sqrt(D^2 - (D - d)^2) >= d
      from the other segment's line too).

    The turn's sine and cosine come from the exact cross and dot products
    of the integer directions, and the mitre's position along the first
    offset line from the half-angle form ``d0 sin / (1 + cos) +
    (d1 - d0) / sin``, so a nearly straight join stays exact to float
    noise.  Along a chain that only turns left (a west chain with its
    descent or corridor run) the offset therefore never comes nearer the
    chain than the distance.  After a right turn (a jog outward) whose
    first segment is shorter than ``d tan(turn / 2)``, the trim lies
    behind that segment's start and the vertex before it inside the jog's
    band: the polyline is then no outline, but the west hull of the
    vertices still holds every band (tests/test_bus.py).
    """

    vertex = one.b
    turn = one.dx * two.dy - one.dy * two.dx  # > 0: a left turn, convex for the west offset
    dot = one.dx * two.dx + one.dy * two.dy
    d0, d1 = one.distance, two.distance
    if turn == 0 and dot > 0:  # straight on: both sides have the same slant, so the same distance
        return [_vertex(vertex, one.nx * d0, one.ny * d0, one.nx, one.ny)]
    # A turn beyond 120 degrees, exactly: cos(turn) < -1/2, so the dot product is negative and its square more than a
    # quarter of the squared lengths' product.
    sharp = dot < 0 and 4 * dot * dot > one.length2 * two.length2
    if turn == 0 or (turn > 0 and sharp):
        first = (one.nx + one.ux, one.ny + one.uy)
        second = (two.nx - two.ux, two.ny - two.uy)
        return [
            _vertex(vertex, first[0] * d0, first[1] * d0, first[0], first[1]),
            _vertex(vertex, second[0] * d1, second[1] * d1, second[0], second[1]),
        ]
    reach = max(d0, d1)
    if d0 != d1 and (d1 - d0) * (d1 - d0) * one.length2 * two.length2 > turn * turn * reach * reach:
        return [_vertex(vertex, one.nx * reach, one.ny * reach, one.nx, one.ny), _vertex(vertex, two.nx * reach, two.ny * reach, two.nx, two.ny)]
    lengths = one.length * two.length
    sine, cosine = turn / lengths, dot / lengths
    along = d0 * sine / (1 + cosine) + (d1 - d0) / sine
    return [_vertex(vertex, one.nx * d0 + along * one.ux, one.ny * d0 + along * one.uy, one.nx + two.nx, one.ny + two.ny)]


def lane_keepout(chain: Sequence[Sequence[int]], follow: Sequence[int], distance_nm: int) -> list:
    """The points the next lane out keeps east of: the offset of ``chain`` continued to ``follow``
    (:func:`lane_offset`), then the four corners of a box of ``distance_nm`` around the chain's start.

    ``follow`` is the first point of the lane below its chain (the descent,
    or a corridor run or a jog): without it the offset would end square at
    the chain's last vertex, and a next lane that passes that vertex lower
    down could cut the join (the mitre of a descent after a slanted chain,
    the trim of a jog).
    """

    return lane_offset([*chain, follow], distance_nm) + box_corners(grow((chain[0][0], chain[0][1], chain[0][0], chain[0][1]), distance_nm))


def lane_offset(path: Sequence[Sequence[int]], distance_nm: int) -> list:
    """The outer (west) offset of a lane (its chain and the first point below it): :func:`mitred_offset`, but at the
    lane's westmost corner where it turns from moving west to moving east (a lane following a receding field inward).

    There the mitre is replaced by the two points where the two offset
    lines meet the vertical line ``distance_nm`` (and the slant allowance)
    west of the corner: the next lane out runs straight down along it, so
    lanes nested around the turn keep the distance without spreading outward
    by ``1 / cos(turn / 2)`` each.  Every point of that cut stays at least
    the distance from the lane (the corner is its nearest point).  The
    offsets on either side are :func:`mitred_offset`'s, ending square at the
    corner.
    """

    points: list = []
    for point in path:
        point = (point[0], point[1])
        if not points or point != points[-1]:
            points.append(point)
    for index in range(1, len(points) - 1):
        before, corner, after = points[index - 1], points[index], points[index + 1]
        if before[0] > corner[0] < after[0]:
            reach = distance_nm + SLANT_ALLOWANCE_NM
            x = corner[0] - reach

            def rise(other: tuple) -> int:
                # Where the offset line of the segment corner-other meets the vertical x, above or below the corner.
                dx, dy = abs(other[0] - corner[0]), abs(other[1] - corner[1])
                length = math.sqrt(dx * dx + dy * dy)
                distance = distance_nm + (SLANT_ALLOWANCE_NM if dy else 0)
                return math.ceil((distance - reach * dy / length) * length / dx)

            upper = mitred_offset(points[: index + 1], distance_nm)
            lower = mitred_offset(points[index:], distance_nm)
            return upper + [(x, corner[1] + rise(before)), (x, corner[1] - rise(after))] + lower
    return mitred_offset(points, distance_nm)


def box_corners(box: Sequence[int]) -> list:
    x0, y0, x1, y1 = box
    return [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]


def grow(box: Sequence[int], distance_nm: int) -> tuple:
    return (box[0] - distance_nm, box[1] - distance_nm, box[2] + distance_nm, box[3] + distance_nm)


def subtract(box: Sequence[int], hole: Sequence[int]) -> list:
    """``box`` minus ``hole`` as up to four boxes: below, above, left and right of it.

    Closed boxes; a hole that only touches the box leaves it whole.  The
    parts' interiors are disjoint, and they cover the box outside the
    hole's interior.
    """

    x0, y0, x1, y1 = box
    h0, k0, h1, k1 = hole
    if h0 >= x1 or h1 <= x0 or k0 >= y1 or k1 <= y0:
        return [(x0, y0, x1, y1)]
    parts = []
    if y0 < k0:
        parts.append((x0, y0, x1, k0))  # below
    if k1 < y1:
        parts.append((x0, k1, x1, y1))  # above
    ym0, ym1 = max(y0, k0), min(y1, k1)
    if x0 < h0:
        parts.append((x0, ym0, h0, ym1))  # left
    if h1 < x1:
        parts.append((h1, ym0, x1, ym1))  # right
    return parts


def clip_y(box: Sequence[int], low: int, high: int) -> Optional[tuple]:
    """The part of ``box`` between the heights ``low`` and ``high`` (closed; a line counts), or None."""

    x0, y0, x1, y1 = box
    y0, y1 = max(y0, low), min(y1, high)
    if y0 > y1:
        return None
    return (x0, y0, x1, y1)


def segment_enters(a: Sequence[int], b: Sequence[int], box: Sequence[int]) -> bool:
    """Whether the segment ``a``-``b`` reaches the open interior of ``box`` (touching its edge does not count).

    Exact: the segment's parameter interval inside each open slab of the box
    is a pair of fractions ``(numerator, denominator > 0)``, compared by
    cross-multiplying, and the segment enters where the two intervals and
    ``[0, 1]`` share a point.
    """

    low = high = None
    for start, end, near, far in ((a[0], b[0], box[0], box[2]), (a[1], b[1], box[1], box[3])):
        delta = end - start
        if delta == 0:
            if not near < start < far:
                return False
            continue
        if delta < 0:
            ends, delta = (start - near, start - far), -delta
        else:
            ends = (near - start, far - start)
        lower, upper = (min(ends), delta), (max(ends), delta)
        if low is None or lower[0] * low[1] > low[0] * lower[1]:
            low = lower
        if high is None or upper[0] * high[1] < high[0] * upper[1]:
            high = upper
    if low is None:
        return True  # a point strictly inside
    return low[0] * high[1] < high[0] * low[1] and low[0] < low[1] and high[0] > 0


def mirror(points: Iterable[Sequence[int]]) -> list:
    """Points mirrored about the y axis (x -> -x): the far side's frame and back."""

    return [(-p[0], p[1]) for p in points]


def mirror_box(box: Sequence[int]) -> tuple:
    return (-box[2], box[1], -box[0], box[3])
