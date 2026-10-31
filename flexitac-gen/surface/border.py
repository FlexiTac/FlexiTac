"""The user's border of the taxels in CAD mode (claude/specs/cad-mode/BORDER-EDITOR-PLAN.md, sections 2.4, 3 and 6).

The border is a simple polygon ``[[u, v], ...]`` in the selection chart's uv
(mm, the frame of the selection reply's ``outline_uv``), at least 3
vertices and 1 mm2, no repeated closing vertex; edge ``i`` runs from vertex
``i`` to vertex ``(i + 1) % n``.  The client draws it counter-clockwise; a
clockwise one is taken as well (an edge's inward normal always points into
the border).  The user's decisions (section 6):

- **Only the taxels.**  Every taxel square (the crossing of its Row and
  Column electrodes, P) lies inside the border and on the usable surface;
  F (P with its 0.5 mm margin) lies on the surface as without a border
  (the corner tolerance unchanged), and the routing (the Row bus, the
  Column fan-out, the tails) is free to leave both.  A border is fitted
  with field-only containment (``containment: field``, the surface
  template).
- **Beyond the surface.**  A border may reach beyond the surface; the taxels
  lie where both hold.  It must overlap the surface.
- **The exit is an edge of the border.**  ``base: {"border_edge": i}``, or
  ``auto``: the border's edges at least ``MIN_SIDE_MM`` long, longest first,
  at most :data:`AUTO_EDGES`.  The tails leave across the edge along its
  outward normal (its chord is the base side of the frame); where the edge
  lies inside the surface they cross the rest of the surface beyond it, so
  the exit segments are the surface's outline segments that the edge's
  span meets first beyond it (the lower envelope under the edge in its
  frame).  An edge with no surface across it is no exit.

The search keeps the field fit's DP exact (:func:`surface.fieldfit.lattice`):
a cell is free only when its taxel square lies inside the border, decided
exactly on the border's strips (:class:`FrameBorder`); the map checks every
taxel square of the build against the border (``taxels_inside_border``).
The predicates are robust: orientations are exact (a float filter, then
exact rationals), the strips are the closure of the polygon's vertical
sections (a square touching the border from inside lies inside it).
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping, Sequence

from .errors import SurfaceError, finite_number

CODE = "E_SURFACE_BORDER"
MAX_VERTICES = 2048
# A border's coordinates beyond this are damage (as for a placement's chart coordinates).
MAX_COORDINATE_MM = 1e7
MIN_AREA_MM2 = 1.0
# Less overlap with the surface than this is none.
MIN_OVERLAP_MM2 = 1e-6
# The map's check: the placement's field origin is rounded to 1e-6 mm.
INSIDE_TOLERANCE_MM = 1e-6
# base auto with a border: at most this many of its edges, longest first.
AUTO_EDGES = 6
# Shorter edges are no tail exit (surface.fit.MIN_SIDE_MM).
MIN_EDGE_MM = 3.0
_NOISE = 1e-9
# The float filter of the orientation test: Shewchuk's ccwerrboundA is (3 + 16 eps) eps, about 3.33e-16.
_ORIENT_BOUND = 4e-16


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def parse(raw: Any, where: str = "border") -> list:
    """The border's vertices ``[(u, v), ...]`` (floats), or E_SURFACE_BORDER: ``{"uv": [[u, v], ...]}``, 3 to
    :data:`MAX_VERTICES` finite vertices, a simple polygon of at least :data:`MIN_AREA_MM2`."""

    if not isinstance(raw, Mapping) or set(raw) != {"uv"}:
        raise SurfaceError(CODE, f'{where} must be {{"uv": [[u, v], ...]}}: a polygon in the selection chart\'s uv (mm).')
    uv = raw["uv"]
    if not isinstance(uv, (list, tuple)):
        raise SurfaceError(CODE, f"{where}.uv must be a list of [u, v] vertices.")
    if len(uv) < 3:
        raise SurfaceError(CODE, f"{where}.uv holds {len(uv)} vertices; a border needs at least 3.")
    if len(uv) > MAX_VERTICES:
        raise SurfaceError(CODE, f"{where}.uv holds {len(uv)} vertices; a border has at most {MAX_VERTICES}.")
    points = []
    for k, item in enumerate(uv):
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            raise SurfaceError(CODE, f"{where}.uv[{k}] must be [u, v] in mm.")
        points.append(tuple(finite_number(c, f"{where}.uv[{k}][{i}]", -MAX_COORDINATE_MM, MAX_COORDINATE_MM, code=CODE)
                            for i, c in enumerate(item)))
    problem = simple_problem(points)
    if problem is not None:
        raise SurfaceError(CODE, f"{where} is not a simple polygon: {problem}.")
    area = abs(signed_area(points))
    if area < MIN_AREA_MM2:
        raise SurfaceError(CODE, f"{where} encloses {area:.6g} mm2; a border needs at least {MIN_AREA_MM2:g} mm2.")
    return points


def echo(points: Sequence[Sequence[float]]) -> dict:
    """The border as the replies and the placement carry it."""

    return {"uv": [[float(u), float(v)] for u, v in points]}


def signed_area(points: Sequence[Sequence[float]]) -> float:
    """The polygon's signed area (positive counter-clockwise)."""

    n = len(points)
    return math.fsum(points[k][0] * points[(k + 1) % n][1] - points[(k + 1) % n][0] * points[k][1] for k in range(n)) / 2


def orient(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> int:
    """The exact sign of the turn a -> b -> c (1 counter-clockwise, -1 clockwise, 0 collinear)."""

    left = (b[0] - a[0]) * (c[1] - a[1])
    right = (b[1] - a[1]) * (c[0] - a[0])
    det = left - right
    bound = _ORIENT_BOUND * (abs(left) + abs(right))
    if det > bound:
        return 1
    if det < -bound:
        return -1
    ax, ay, bx, by, cx, cy = (Fraction(value) for value in (a[0], a[1], b[0], b[1], c[0], c[1]))
    exact = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    return (exact > 0) - (exact < 0)


def _on_segment(p: Sequence[float], a: Sequence[float], b: Sequence[float]) -> bool:
    """Whether p, collinear with a and b, lies on the closed segment ab."""

    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def segments_touch(a: Sequence[float], b: Sequence[float], c: Sequence[float], d: Sequence[float]) -> bool:
    """Whether the closed segments ab and cd share a point (exact)."""

    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    return (
        (o1 == 0 and _on_segment(c, a, b)) or (o2 == 0 and _on_segment(d, a, b))
        or (o3 == 0 and _on_segment(a, c, d)) or (o4 == 0 and _on_segment(b, c, d))
    )


def simple_problem(points: Sequence[Sequence[float]]) -> Any:
    """Why the closed polygon is not simple (repeated vertices, an edge folding back on the previous one, two edges that
    cross or touch), or None.  Exact; a sweep over x with the edges' boxes."""

    n = len(points)
    for i in range(n):
        if points[i][0] == points[(i + 1) % n][0] and points[i][1] == points[(i + 1) % n][1]:
            return f"vertices {i} and {(i + 1) % n} coincide"
    for i in range(n):
        p, q, r = points[i - 1], points[i], points[(i + 1) % n]
        # Collinear and pointing back: the signs of the coordinate differences are exact.
        if orient(p, q, r) == 0 and (q[0] - p[0]) * (r[0] - q[0]) + (q[1] - p[1]) * (r[1] - q[1]) < 0:
            return f"edges {(i - 1) % n} and {i} fold back on each other at vertex {i}"
    boxes = []
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        boxes.append((min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])))
    active: list = []
    for i in sorted(range(n), key=lambda k: (boxes[k][0], k)):
        x0, x1, y0, y1 = boxes[i]
        active = [j for j in active if boxes[j][1] >= x0]
        for j in active:
            if j == (i + 1) % n or i == (j + 1) % n:
                continue  # adjacent: only their common vertex (the fold-back test above)
            if boxes[j][3] < y0 or boxes[j][2] > y1:
                continue
            if segments_touch(points[i], points[(i + 1) % n], points[j], points[(j + 1) % n]):
                first, second = min(i, j), max(i, j)
                return f"edges {first} and {second} cross or touch"
        active.append(i)
    return None


# --------------------------------------------------------------------------
# Strips, squares and areas
# --------------------------------------------------------------------------


def _union(intervals: list) -> list:
    intervals.sort()
    merged: list = []
    for a, b in intervals:
        if merged and a <= merged[-1][1]:
            if b > merged[-1][1]:
                merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def _subtract(inside: list, blocked: list) -> list:
    free = []
    k = 0
    for a, b in inside:
        start = a
        while k < len(blocked) and blocked[k][1] <= start:
            k += 1
        j = k
        while j < len(blocked) and blocked[j][0] < b:
            if blocked[j][0] > start:
                free.append((start, blocked[j][0]))
            start = max(start, blocked[j][1])
            j += 1
        if start < b:
            free.append((start, b))
    return free


def strip_intervals(edges: Sequence[Sequence[float]], y0: float, y1: float) -> list:
    """The x-intervals ``[(a, b)]`` where the vertical segment from (x, y0) to (x, y1) lies in the closed polygon of
    ``edges`` (``(ax, ay, bx, by)``, sorted, disjoint): inside it at the strip's middle (even-odd), less where an edge
    passes through the open strip, closed (a segment along an edge, or a square touching the border, is inside)."""

    middle = (y0 + y1) / 2
    crossings = []
    blocked = []
    for ax, ay, bx, by in edges:
        if (ay <= middle < by) or (by <= middle < ay):
            crossings.append(ax + (middle - ay) * (bx - ax) / (by - ay))
        if ay == by:
            if y0 < ay < y1:
                blocked.append((min(ax, bx), max(ax, bx)))
            continue
        low, high = max(y0, min(ay, by)), min(y1, max(ay, by))
        if low < high:
            xa = ax + (low - ay) * (bx - ax) / (by - ay)
            xb = ax + (high - ay) * (bx - ax) / (by - ay)
            blocked.append((min(xa, xb), max(xa, xb)))
    crossings.sort()
    inside = [(crossings[k], crossings[k + 1]) for k in range(0, len(crossings) - 1, 2)]
    return _subtract(inside, _union(blocked))


class FrameBorder:
    """The border in one base frame (:class:`surface.fit.BaseFrame`): which taxel squares lie inside it.

    :class:`surface.fill.FreeSpace` holds one when the fit has a border, and
    :func:`surface.fieldfit.lattice` caps each row's free runs with
    :meth:`ends`: a run is free only when every cell's taxel square lies
    inside the border (and its F on the usable surface, as without one).
    """

    def __init__(self, points: Sequence[Sequence[float]], frame: Any) -> None:
        self.polygon = [frame.to_base(p) for p in points]
        n = len(self.polygon)
        self.edges = [(*self.polygon[k], *self.polygon[(k + 1) % n]) for k in range(n)]
        xs = [p[0] for p in self.polygon]
        ys = [p[1] for p in self.polygon]
        self.x0, self.x1, self.y0, self.y1 = min(xs), max(xs), min(ys), max(ys)
        self._height = max(0.25, (self.y1 - self.y0) / 256)
        self._buckets: dict = {}
        for index, (_, ay, _, by) in enumerate(self.edges):
            for key in range(self._bucket(min(ay, by)), self._bucket(max(ay, by)) + 1):
                self._buckets.setdefault(key, []).append(index)
        self._strips: dict = {}

    def _bucket(self, y: float) -> int:
        return int(math.floor((y - self.y0) / self._height))

    def bounds(self, x0: float, x1: float, y0: float, y1: float, inset: float, margin: float) -> tuple:
        """The lattice's extent of a frame with the border: the surface's extent ``x0..y1`` (less ``inset`` on the low
        sides, the lattice's own) cut to where a cell may lie inside the border, so that phase 0 puts the first
        crossing on the border where it lies inside the surface (the grown strip ``margin`` beyond it)."""

        return (max(x0, self.x0 - inset - margin), min(x1, self.x1 + margin), max(y0, self.y0 - inset - margin), min(y1, self.y1 + margin))

    def intervals(self, y0: float, y1: float) -> list:
        """:func:`strip_intervals` of the border on the strip ``y0..y1`` (cached)."""

        key = (y0, y1)
        found = self._strips.get(key)
        if found is None:
            near = set()
            for bucket in range(self._bucket(y0), self._bucket(y1) + 1):
                near.update(self._buckets.get(bucket, ()))
            found = strip_intervals([self.edges[index] for index in sorted(near)], y0, y1)
            if len(self._strips) > 100_000:
                self._strips.clear()
            self._strips[key] = found
        return found

    def flags(self, y: float, x0: float, pitch: float, width: float, columns: int) -> list:
        """Per cell of a lattice row (cell c: ``[x0 + c pitch, + width] x [y, y + width]``), whether its taxel square
        lies inside the border."""

        flags = [False] * columns
        for low, high in self.intervals(round(y, 9), round(y + width, 9)):
            first = max(0, int(math.ceil((low - x0) / pitch - _NOISE)))
            last = min(columns - 1, int(math.floor((high - width - x0) / pitch + _NOISE)))
            for c in range(first, last + 1):
                flags[c] = True
        return flags

    def ends(self, y: float, x0: float, pitch: float, width: float, columns: int) -> list:
        """Per cell of a lattice row, the end of its run of cells inside the border (every taxel square of ``[a, b]``
        inside it), or -1: what :func:`surface.fieldfit.lattice` takes the minimum with."""

        flags = self.flags(y, x0, pitch, width, columns)
        ends = [-1] * columns
        end = -1
        for c in range(columns - 1, -1, -1):
            if not flags[c]:
                end = -1
                continue
            if end < 0:
                end = c
            ends[c] = end
        return ends

    def square_inside(self, x0: float, y0: float, x1: float, y1: float, tolerance: float = 0.0) -> bool:
        """Whether the box lies inside the border, up to ``tolerance`` (the box shrunk by it all round)."""

        x0, y0, x1, y1 = x0 + tolerance, y0 + tolerance, x1 - tolerance, y1 - tolerance
        if x1 < x0:
            x0 = x1 = (x0 + x1) / 2
        if y1 < y0:
            y0 = y1 = (y0 + y1) / 2
        near = set()
        for bucket in range(self._bucket(y0), self._bucket(y1) + 1):
            near.update(self._buckets.get(bucket, ()))
        # A degenerate strip (y0 == y1) is the polygon's section at y0.
        return _within(strip_intervals([self.edges[index] for index in sorted(near)], y0, y1), x0, x1)


def _within(intervals: Sequence, x0: float, x1: float) -> bool:
    for low, high in intervals:
        if low <= x0 and x1 <= high:
            return True
    return False


def overlap_area(points: Sequence[Sequence[float]], outline: Sequence[Sequence[float]], holes: Sequence[Sequence[Sequence[float]]]) -> float:
    """The area of the polygon ``points`` on the surface (``outline`` less ``holes``), exact up to rounding.

    Between consecutive levels of every vertex of both and every crossing of
    their edges, the section of the overlap is a set of intervals whose
    ends move linearly: its width at the slab's middle times the slab's
    height is the slab's area.
    """

    surface = [list(outline)] + [list(hole) for hole in holes]
    border_edges = [(points[k - 1], points[k]) for k in range(len(points))]
    surface_edges = [(polygon[k - 1], polygon[k]) for polygon in surface for k in range(len(polygon))]
    low = max(min(p[1] for p in points), min(p[1] for p in outline))
    high = min(max(p[1] for p in points), max(p[1] for p in outline))
    if high <= low:
        return 0.0
    levels = {p[1] for p in points} | {p[1] for polygon in surface for p in polygon}
    # Crossings: the surface's edges in buckets over y (a border edge looks at the buckets it spans).
    height = max((high - low) / 1024, 1e-6)
    buckets: dict = {}
    for index, (a, b) in enumerate(surface_edges):
        for key in range(int(math.floor((min(a[1], b[1]) - low) / height)), int(math.floor((max(a[1], b[1]) - low) / height)) + 1):
            buckets.setdefault(key, []).append(index)
    for a, b in border_edges:
        lo, hi = max(low, min(a[1], b[1])), min(high, max(a[1], b[1]))
        if lo > hi:
            continue
        near = set()
        for key in range(int(math.floor((lo - low) / height)), int(math.floor((hi - low) / height)) + 1):
            near.update(buckets.get(key, ()))
        for index in sorted(near):
            c, d = surface_edges[index]
            if max(c[0], d[0]) < min(a[0], b[0]) or min(c[0], d[0]) > max(a[0], b[0]):
                continue
            dx, dy = b[0] - a[0], b[1] - a[1]
            fx, fy = d[0] - c[0], d[1] - c[1]
            det = dx * fy - dy * fx
            if det == 0:
                continue
            t = ((c[0] - a[0]) * fy - (c[1] - a[1]) * fx) / det
            s = ((c[0] - a[0]) * dy - (c[1] - a[1]) * dx) / det
            if 0.0 <= t <= 1.0 and 0.0 <= s <= 1.0:
                levels.add(a[1] + dy * t)
    ys = sorted(y for y in levels if low <= y <= high)
    ys = sorted({low, high, *ys})
    from .fit import _scanlines

    middles = [(ys[k] + ys[k + 1]) / 2 for k in range(len(ys) - 1)]
    mine = _scanlines([list(points)], middles)
    theirs = _scanlines(surface, middles)
    parts = []
    for k in range(len(middles)):
        parts.append(_common(mine[k], theirs[k]) * (ys[k + 1] - ys[k]))
    return math.fsum(parts)


def _common(first: Sequence, second: Sequence) -> float:
    """The total length of two sorted, disjoint interval lists' overlap."""

    i = j = 0
    found = []
    while i < len(first) and j < len(second):
        low = max(first[i][0], second[j][0])
        high = min(first[i][1], second[j][1])
        if high > low:
            found.append(high - low)
        if first[i][1] < second[j][1]:
            i += 1
        else:
            j += 1
    return math.fsum(found)


def on_surface(points: Sequence[Sequence[float]], chart: Any) -> dict:
    """The border's area and its share on the surface (the chart's outline less its holes); E_SURFACE_BORDER when it
    does not overlap the surface."""

    area = abs(signed_area(points))
    overlap = overlap_area(points, chart.outline(), chart.holes())
    if overlap < MIN_OVERLAP_MM2:
        raise SurfaceError(CODE, "The border does not overlap the selected surface: draw it on the surface (the taxels lie where both hold).")
    return {"border_area_mm2": round(area, 6), "border_on_surface_share": round(min(1.0, overlap / area), 6)}


# --------------------------------------------------------------------------
# The exits: edges of the border
# --------------------------------------------------------------------------


def check_base(base: Any) -> None:
    """With a border the base is an edge of it: ``auto`` or ``{"border_edge": i}``."""

    if base == "auto" or (isinstance(base, Mapping) and set(base) == {"border_edge"}):
        return
    raise SurfaceError(CODE, "With a border the tails leave across an edge of it: base must be 'auto' or {'border_edge': i}.")


def edge_side(points: Sequence[Sequence[float]], index: int, chart: Any) -> dict:
    """Edge ``index`` of the border as a base side (:class:`surface.fit.BaseFrame`, the exit machinery): its chord with the
    border on the left (from vertex ``index`` to the next one, the other way round on a clockwise border), its inward
    normal, and ``edges``: the exit segments of the chart's outline (:func:`exit_segments`).  Rounded like
    :func:`surface.api.boundary_sides`."""

    from .api import _r
    from .fit import BaseFrame

    n = len(points)
    a, b = points[index], points[(index + 1) % n]
    if signed_area(points) < 0:
        a, b = b, a
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    side = {
        "index": index,
        "kind": "border",
        "from_uv": [_r(a[0]), _r(a[1])],
        "to_uv": [_r(b[0]), _r(b[1])],
        "length_mm": _r(length),
        "chord_mm": _r(length),
        "straight": True,
        "inward_uv": [_r(-dy / length, 9), _r(dx / length, 9)],
    }
    frame = BaseFrame(side, 0.0)
    side["edges"] = exit_segments([frame.to_base(p) for p in chart.outline()], frame.length)
    return side


def exit_segments(outline: Sequence[Sequence[float]], length: float) -> list:
    """The outline segments (base frame, segment i from point i to point i + 1) that the vertical lines over the base
    side's span ``0..length`` meet first from below: where the tails leave the surface beyond the edge.  Exact between
    the outline's vertices (simple: the lowest segment changes only at a vertex)."""

    from .fit import ExitOutline

    n = len(outline)
    lowest = ExitOutline(outline, range(n))
    xs = sorted({0.0, float(length), *(p[0] for p in outline if 0.0 < p[0] < length)})
    found = set()
    for left, right in zip(xs, xs[1:]):
        if right - left <= _NOISE:
            continue
        hit = lowest.lowest_segment((left + right) / 2)
        if hit is not None:
            found.add(hit[1])
    return sorted(found)


def bases(base: Any, points: Sequence[Sequence[float]], chart: Any) -> list:
    """The exits a fit with a border tries: the picked edge, or (``auto``) the edges at least :data:`MIN_EDGE_MM` long
    with surface across them, longest first, at most :data:`AUTO_EDGES`."""

    n = len(points)
    lengths = [math.hypot(points[(k + 1) % n][0] - points[k][0], points[(k + 1) % n][1] - points[k][1]) for k in range(n)]
    if base == "auto":
        chosen = []
        for index in sorted(range(n), key=lambda k: (-round(lengths[k], 9), k)):
            if lengths[index] < MIN_EDGE_MM:
                break
            side = edge_side(points, index, chart)
            if side["edges"]:
                chosen.append(side)
            if len(chosen) >= AUTO_EDGES:
                break
        if not chosen:
            raise SurfaceError(
                CODE,
                f"No edge of the border can be the tail exit: an exit is at least {MIN_EDGE_MM:g} mm long with surface across it "
                "(beyond it in the tails' direction).",
            )
        return chosen
    check_base(base)
    index = base["border_edge"]
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < n:
        raise SurfaceError(CODE, f"base.border_edge must be an edge of the border, 0..{n - 1}.")
    if lengths[index] < MIN_EDGE_MM:
        raise SurfaceError(CODE, f"Border edge {index} is {lengths[index]:.6g} mm long; a tail exit needs at least {MIN_EDGE_MM:g} mm.")
    side = edge_side(points, index, chart)
    if not side["edges"]:
        raise SurfaceError(CODE, f"Border edge {index} has no surface across it: the tails would not cross the surface beyond it.")
    return [side]


# --------------------------------------------------------------------------
# A strain-limited fit's chart
# --------------------------------------------------------------------------


def carry(points: Sequence[Sequence[float]], source: Any, target: Any) -> list:
    """The border in another chart of the same mesh (a strain-limited fit's disk): the rigid motion that best maps the
    common vertices' uv of ``source`` onto ``target``'s (least squares, no reflection: both charts are seen from
    outside)."""

    common = sorted(set(source.uv) & set(target.uv))
    if len(common) < 2:
        raise SurfaceError(CODE, "The strain-limited part of the selection shares too little with it to carry the border.")
    first = [source.uv[v] for v in common]
    second = [target.uv[v] for v in common]
    count = len(common)
    ax, ay = math.fsum(p[0] for p in first) / count, math.fsum(p[1] for p in first) / count
    bx, by = math.fsum(p[0] for p in second) / count, math.fsum(p[1] for p in second) / count
    along = math.fsum((p[0] - ax) * (q[0] - bx) + (p[1] - ay) * (q[1] - by) for p, q in zip(first, second))
    across = math.fsum((p[0] - ax) * (q[1] - by) - (p[1] - ay) * (q[0] - bx) for p, q in zip(first, second))
    angle = math.atan2(across, along)
    c, s = math.cos(angle), math.sin(angle)
    return [(round(bx + c * (u - ax) - s * (v - ay), 9), round(by + s * (u - ax) + c * (v - ay), 9)) for u, v in points]


# --------------------------------------------------------------------------
# The taxels against the border
# --------------------------------------------------------------------------


def design_squares(design: Mapping[str, Any], origin: Sequence[float]) -> list:
    """The taxel squares ``(row, column, x0, y0, x1, y1)`` of a fitted design in its base frame, from its matrix and mask:
    the lattice cell of each crossing (ROW_01 on top, COL_01 on the left with the rows on top and on the right with the
    columns on top, as :func:`surface.fieldfit.mask_for` numbers them; the field's lower-left corner at ``origin``)."""

    from engine import design_mask

    matrix = design["matrix"]
    rows, columns = int(matrix["rows"]), int(matrix["columns"])
    pitch_x, pitch_y = float(matrix["pitch_x_mm"]), float(matrix["pitch_y_mm"])
    width, height = float(matrix["taxel_width_mm"]), float(matrix["taxel_height_mm"])
    spans = design_mask(design) or ((1, columns),) * rows
    rows_top = design["role_mapping"]["top"] == "rows"
    squares = []
    for row, (first, last) in enumerate(spans, start=1):
        y = origin[1] + (rows - row) * pitch_y
        for column in range(int(first), int(last) + 1):
            x = origin[0] + ((column - 1) if rows_top else (columns - column)) * pitch_x
            squares.append((row, column, x, y, x + width, y + height))
    return squares


def build_squares(result: Mapping[str, Any], origin: Sequence[float]) -> list:
    """The taxel squares ``(row, column, x0, y0, x1, y1)`` of a build in its base frame: the overlap of each crossing Row
    and Column electrode (both boards in the stack frame, :func:`engine.drc.stack_frame`, seen from outside; the field's
    lower-left corner at ``origin``), as :func:`surface.place.masked_taxel_centres` finds the taxels."""

    from engine.drc import stack_frame
    from engine.geometry import rect_corners

    design = result["design"]
    roles = design["role_mapping"]
    boxes: dict = {}
    for key in ("row", "column"):
        board = result["boards"][key]
        convert = stack_frame(board, roles)
        grid = board["grid_registration"]["active_region"]
        shift_x, shift_y = grid["width"] / 2 + origin[0], grid["height"] / 2 + origin[1]
        for electrode in board["layers"]["top_copper"]["electrodes"]:
            corners = [convert(corner) for corner in rect_corners(electrode)]
            xs = [x + shift_x for x, _ in corners]
            ys = [y + shift_y for _, y in corners]
            boxes[electrode["net"]] = (min(xs), min(ys), max(xs), max(ys))
    squares = []
    for row in range(1, int(design["matrix"]["rows"]) + 1):
        rx0, ry0, rx1, ry1 = boxes[f"ROW_{row:02d}"]
        for column in range(1, int(design["matrix"]["columns"]) + 1):
            cx0, cy0, cx1, cy1 = boxes[f"COL_{column:02d}"]
            x0, x1, y0, y1 = max(rx0, cx0), min(rx1, cx1), max(ry0, cy0), min(ry1, cy1)
            if x1 - x0 > 1e-9 and y1 - y0 > 1e-9:
                squares.append((row, column, x0, y0, x1, y1))
    return squares


def outside(squares: Sequence, points: Sequence[Sequence[float]], frame: Any, tolerance: float = INSIDE_TOLERANCE_MM) -> list:
    """The ``(row, column)`` of the squares (base frame) that do not lie inside the border (chart uv) up to ``tolerance``."""

    border = FrameBorder(points, frame)
    return [(row, column) for row, column, x0, y0, x1, y1 in squares if not border.square_inside(x0, y0, x1, y1, tolerance)]


def record(result: Mapping[str, Any], points: Sequence[Sequence[float]], frame: Any, origin: Sequence[float]) -> dict:
    """The map's ``taxels_inside_border`` record: how many taxel squares of the build leave the border (required 0)."""

    found = outside(build_squares(result, origin), points, frame)
    entry = {
        "rule": "taxels_inside_border",
        "required": 0,
        "measured": len(found),
        "comparison": "max<=",
        "unit": "count",
        "passed": not found,
        "what": "every taxel square (the crossing of its Row and Column electrodes) lies inside the border",
    }
    if found:
        entry["taxels"] = [[row, column] for row, column in found[:16]]
    return entry
