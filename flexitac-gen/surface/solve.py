"""Flattening solvers for curved charts, in pure Python.

- **LSCM** in the symmetric form of Mullen et al. (2008): minimise the
  conformal energy ``E_D - A`` (cotangent Dirichlet energy minus the
  signed area of the chart), with two boundary vertices pinned at their 3D
  distance.
- **ARAP** (Liu et al. 2008): local steps fit one rotation per triangle
  (trigonometry-free 2x2 closed form), global steps solve one cotangent
  Laplacian per coordinate.  A flat PI/Cu sheet cannot stretch, so the
  nearly isometric ARAP chart is what the fit uses; the stretch left over
  is reported per facet by ``chart.singular_values``.

Both solve sparse symmetric positive definite systems by an LDL^T
factorization in minimum-degree order; ARAP factors its Laplacian once for
all its global steps.  Should a pivot not come out positive (a degenerate
system), Jacobi-preconditioned conjugate gradients solve it instead.  CG
alone needed about 150 iterations for each of ARAP's 24 global steps: 8-12 s
for a chart of 2900 vertices on Python 3.12 and 3.9, against 0.9-1.5 s with
the factorizations.

Cotangent weights are clamped to ``[-COT_LIMIT, COT_LIMIT]`` (LSCM) and to
``[COT_FLOOR, COT_LIMIT]`` (ARAP) so that slivers of decimated meshes do not
ruin the conditioning.  Orders, iteration counts and tolerances are fixed,
every loop adds in a fixed order, and vector dot products are
``math.fsum`` (correctly rounded).  The built-in ``sum`` of floats is never
used: it became compensated in Python 3.12 (and ``math.hypot`` more
accurate in 3.10), which made curved charts differ in their last bits
between Python versions.  So the result is a deterministic function of the
input on any supported Python with IEEE doubles.
"""

from __future__ import annotations

import heapq
import math
from operator import mul
from typing import Any, Sequence

from .mesh import Mesh, cross, dot, norm, sub

COT_LIMIT = 1e4
COT_FLOOR = 1e-4
CG_TOLERANCE = 1e-10
ARAP_ITERATIONS = 12


def conformal_then_rigid(
    mesh: Mesh, region: Sequence[int], vertex_ids: Sequence[int], boundary: Sequence[int], initial=None,
    iterations: int = ARAP_ITERATIONS,
) -> dict:
    """uv for every vertex of the patch: LSCM (unless ``initial`` is given), then ARAP."""

    from .chart import oriented_facet, split_chain

    index = {v: i for i, v in enumerate(vertex_ids)}
    keep = set(vertex_ids)
    triangles = []
    for f in region:
        corners = oriented_facet(mesh, f)
        sides = [split_chain(mesh, corners[k], corners[(k + 1) % 3], keep) for k in range(3)]
        if all(len(side) == 2 for side in sides):
            triangles.append(tuple(index[v] for v in corners))
            continue
        # A facet with T-junction vertices on its edges: a fan from the corner
        # with the fewest of them on its own two edges ties those vertices in.
        ring = [v for side in sides for v in side[:-1]]
        corner = min(range(3), key=lambda k: (len(sides[k]) + len(sides[k - 1]), k))
        first = ring.index(corners[corner])
        ring = ring[first:] + ring[:first]
        for x, y in zip(ring[1:], ring[2:]):
            if _area3(mesh.vertices[ring[0]], mesh.vertices[x], mesh.vertices[y]) > 1e-12:
                triangles.append((index[ring[0]], index[x], index[y]))
    points = [mesh.vertices[v] for v in vertex_ids]
    if initial is None:
        loop = [index[v] for v in boundary]
        uv = lscm(points, triangles, loop)
    else:
        uv = [tuple(initial[v]) for v in vertex_ids]
    uv = arap(points, triangles, uv, iterations)
    return {vertex_ids[i]: uv[i] for i in range(len(vertex_ids))}


def _area3(a, b, c) -> float:
    return norm(cross(sub(b, a), sub(c, a))) / 2


def _cot(a, b, c) -> float:
    """Cotangent of the angle at ``c`` in triangle (a, b, c)."""

    u = sub(a, c)
    v = sub(b, c)
    sine = norm(cross(u, v))
    if sine == 0:
        return COT_LIMIT
    return dot(u, v) / sine


def lscm(points: Sequence, triangles: Sequence, boundary: Sequence[int]) -> list:
    n = len(points)
    rows: list = [dict() for _ in range(2 * n)]

    def add(i: int, j: int, value: float) -> None:
        row = rows[i]
        row[j] = row.get(j, 0.0) + value

    for i, j, k in triangles:
        for a, b, c in ((i, j, k), (j, k, i), (k, i, j)):
            w = max(-COT_LIMIT, min(COT_LIMIT, _cot(points[a], points[b], points[c]))) / 2
            for offset in (0, n):
                add(a + offset, a + offset, w)
                add(b + offset, b + offset, w)
                add(a + offset, b + offset, -w)
                add(b + offset, a + offset, -w)
    # Minus the area term: A = 1/2 sum over directed boundary edges (u_i v_j - u_j v_i).
    for position in range(len(boundary)):
        i = boundary[position]
        j = boundary[(position + 1) % len(boundary)]
        add(i, n + j, -0.5)
        add(n + j, i, -0.5)
        add(j, n + i, 0.5)
        add(n + i, j, 0.5)
    p0, p1 = _far_pair(points, boundary)
    distance = norm(sub(points[p1], points[p0]))
    fixed = {p0: 0.0, n + p0: 0.0, p1: distance, n + p1: 0.0}
    x = _solve_pinned(rows, fixed, [0.0] * (2 * n), max_iterations=max(200, 8 * n))
    return [(x[i], x[n + i]) for i in range(n)]


def arap(points: Sequence, triangles: Sequence, uv: Sequence, iterations: int) -> list:
    n = len(points)
    # Each triangle in its own plane (isometric 2D coordinates) and its cotangent weights.
    local = []
    weights = []
    for i, j, k in triangles:
        a, b, c = points[i], points[j], points[k]
        e1 = sub(b, a)
        l1 = norm(e1)
        normal = cross(e1, sub(c, a))
        nl = norm(normal)
        if l1 == 0 or nl == 0:
            local.append(((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)))
            weights.append((0.0, 0.0, 0.0))
            continue
        x_axis = (e1[0] / l1, e1[1] / l1, e1[2] / l1)
        y_axis = cross((normal[0] / nl, normal[1] / nl, normal[2] / nl), x_axis)
        ec = sub(c, a)
        local.append(((0.0, 0.0), (l1, 0.0), (dot(ec, x_axis), dot(ec, y_axis))))
        # Weight of edge (j,k) is cot at i, of (k,i) cot at j, of (i,j) cot at k.
        weights.append(
            tuple(
                max(COT_FLOOR, min(COT_LIMIT, _cot(points[p], points[q], points[r])))
                for p, q, r in ((j, k, i), (k, i, j), (i, j, k))
            )
        )
    rows: list = [dict() for _ in range(n)]
    for (i, j, k), (wi, wj, wk) in zip(triangles, weights):
        for a, b, w in ((j, k, wi), (k, i, wj), (i, j, wk)):
            rows[a][a] = rows[a].get(a, 0.0) + w
            rows[b][b] = rows[b].get(b, 0.0) + w
            rows[a][b] = rows[a].get(b, 0.0) - w
            rows[b][a] = rows[b].get(a, 0.0) - w
    anchor = 0
    # The same matrix and pinned vertex in every global step, for u and v.
    system = _pinned_system(rows, {anchor})
    current = [list(p) for p in uv]
    for _ in range(iterations):
        rhs_u = [0.0] * n
        rhs_v = [0.0] * n
        for (i, j, k), (wi, wj, wk), (xi, xj, xk) in zip(triangles, weights, local):
            pts = {i: xi, j: xj, k: xk}
            s00 = s01 = s10 = s11 = 0.0
            for a, b, w in ((j, k, wi), (k, i, wj), (i, j, wk)):
                du = current[a][0] - current[b][0]
                dv = current[a][1] - current[b][1]
                dx = pts[a][0] - pts[b][0]
                dy = pts[a][1] - pts[b][1]
                s00 += w * du * dx
                s01 += w * du * dy
                s10 += w * dv * dx
                s11 += w * dv * dy
            c, s = s00 + s11, s10 - s01
            length = math.sqrt(c * c + s * s)
            c, s = (c / length, s / length) if length > 0 else (1.0, 0.0)
            for a, b, w in ((j, k, wi), (k, i, wj), (i, j, wk)):
                dx = pts[a][0] - pts[b][0]
                dy = pts[a][1] - pts[b][1]
                ru = w * (c * dx - s * dy)
                rv = w * (s * dx + c * dy)
                rhs_u[a] += ru
                rhs_v[a] += rv
                rhs_u[b] -= ru
                rhs_v[b] -= rv
        fixed_u = {anchor: current[anchor][0]}
        fixed_v = {anchor: current[anchor][1]}
        new_u = _solve_pinned(rows, fixed_u, rhs_u, guess=[p[0] for p in current], max_iterations=max(100, 2 * n), system=system)
        new_v = _solve_pinned(rows, fixed_v, rhs_v, guess=[p[1] for p in current], max_iterations=max(100, 2 * n), system=system)
        current = [[new_u[i], new_v[i]] for i in range(n)]
    return [(p[0], p[1]) for p in current]


def _far_pair(points: Sequence, candidates: Sequence[int]) -> tuple:
    """Two candidate vertices far apart (two sweeps; deterministic).

    Every choice is made on the positions, never on the vertex numbering, so
    the same surface gives the same pins whatever the file's facet order or
    winding (an inside-out file numbers its vertices differently).
    """

    first = min(candidates, key=lambda v: tuple(points[v]))
    a = max(candidates, key=lambda v: (norm(sub(points[v], points[first])), tuple(points[v])))
    b = max(candidates, key=lambda v: (norm(sub(points[v], points[a])), tuple(points[v])))
    if a == b:
        b = candidates[1] if candidates[0] == a else candidates[0]
    return (a, b) if a < b else (b, a)


def _pinned_system(rows: Sequence, fixed) -> tuple:
    """The free unknowns, their rows (the fixed columns split off), the Jacobi diagonal and the factors."""

    free = [i for i in range(len(rows)) if i not in fixed]
    position = {i: p for p, i in enumerate(free)}
    reduced = []
    coupled = []
    for i in free:
        row = []
        links = []
        for j, a in sorted(rows[i].items()):
            if j in fixed:
                links.append((j, a))
            else:
                row.append((position[j], a))
        reduced.append(row)
        coupled.append(links)
    diagonal = []
    for p, row in enumerate(reduced):
        d = 0.0
        for q, a in row:
            if q == p:
                d = a
        diagonal.append(d if d > 0 else 1.0)
    return free, reduced, coupled, diagonal, _factor(reduced)


def _solve_pinned(
    rows: Sequence, fixed: dict, rhs: Sequence[float], guess=None, max_iterations: int = 1000, system=None
) -> list:
    """Solve rows * x = rhs with some entries of x fixed (see the module docstring).

    ``system`` is ``_pinned_system(rows, fixed)``, passed when the same rows
    and fixed unknowns are solved again with other values.  ``guess`` and
    ``max_iterations`` serve the CG fallback.
    """

    free, reduced, coupled, diagonal, factors = system if system is not None else _pinned_system(rows, fixed)
    b = []
    for i, links in zip(free, coupled):
        value = rhs[i]
        for j, a in links:
            value -= a * fixed[j]
        b.append(value)
    if factors is not None:
        x = _ldl_solve(factors, b)
    else:
        x0 = [guess[i] for i in free] if guess is not None else [0.0] * len(free)
        x = _pcg(reduced, diagonal, b, x0, max_iterations)
    result = [0.0] * len(rows)
    for i, value in fixed.items():
        result[i] = value
    for p, i in enumerate(free):
        result[i] = x[p]
    return result


def _factor(rows: Sequence) -> Any:
    """LDL^T of a symmetric matrix (rows of (column, value)) in minimum-degree order, or None.

    The order eliminates the unknown with the fewest uneliminated neighbours
    first (ties: the lower index) and joins its neighbours into a clique,
    which is also the pattern of its column of L.  None when a pivot is not
    positive (the matrix is not positive definite as rounded).
    """

    n = len(rows)
    neighbours = [{q for q, _ in row if q != p} for p, row in enumerate(rows)]
    heap = [(len(neighbours[p]), p) for p in range(n)]
    heapq.heapify(heap)
    position = [-1] * n
    order = []
    pattern: list = [None] * n
    while heap:
        degree, p = heapq.heappop(heap)
        if position[p] >= 0 or degree != len(neighbours[p]):
            continue
        position[p] = len(order)
        order.append(p)
        clique = neighbours[p]
        pattern[p] = clique
        for q in clique:
            others = neighbours[q]
            others.discard(p)
            others |= clique
            others.discard(q)
            heapq.heappush(heap, (len(others), q))
    # Right-looking elimination; entry (q, r) lives in the row of whichever
    # of q and r is eliminated first.
    work = [dict() for _ in range(n)]
    pivots = [0.0] * n
    for p, row in enumerate(rows):
        for q, value in row:
            if q == p:
                pivots[p] = value
            elif position[q] > position[p]:
                work[p][q] = value
    columns: list = [None] * n
    for p in order:
        d = pivots[p]
        if not d > 0:
            return None
        cols = sorted(pattern[p], key=position.__getitem__)
        entries = work[p]
        factors = [entries.get(q, 0.0) / d for q in cols]
        for i, q in enumerate(cols):
            scaled = factors[i] * d
            pivots[q] -= scaled * factors[i]
            target = work[q]
            for j in range(i + 1, len(cols)):
                r = cols[j]
                target[r] = target.get(r, 0.0) - scaled * factors[j]
        columns[p] = list(zip(cols, factors))
        work[p] = None
    return order, columns, pivots


def _ldl_solve(factors: tuple, b: Sequence[float]) -> list:
    order, columns, pivots = factors
    x = list(b)
    for p in order:
        value = x[p]
        for q, factor in columns[p]:
            x[q] -= factor * value
    for p in order:
        x[p] /= pivots[p]
    for p in reversed(order):
        value = x[p]
        for q, factor in columns[p]:
            value -= factor * x[q]
        x[p] = value
    return x


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return math.fsum(map(mul, a, b))


def _pcg(rows: Sequence, diagonal: Sequence[float], b: Sequence[float], x: list, max_iterations: int) -> list:
    def multiply(vector: Sequence[float]) -> list:
        # Each row from left to right (its columns in ascending order): the
        # same bits on every Python, and over twice as fast as math.fsum.
        out = []
        for row in rows:
            total = 0.0
            for q, a in row:
                total += a * vector[q]
            out.append(total)
        return out

    x = list(x)
    r = [bi - ai for bi, ai in zip(b, multiply(x))]
    norm_b = math.sqrt(_dot(b, b)) or 1.0
    z = [ri / di for ri, di in zip(r, diagonal)]
    p = list(z)
    rz = _dot(r, z)
    for _ in range(max_iterations):
        if math.sqrt(_dot(r, r)) <= CG_TOLERANCE * norm_b:
            break
        ap = multiply(p)
        denominator = _dot(p, ap)
        if denominator <= 0:
            break
        alpha = rz / denominator
        x = [xi + alpha * pi for xi, pi in zip(x, p)]
        r = [ri - alpha * qi for ri, qi in zip(r, ap)]
        z = [ri / di for ri, di in zip(r, diagonal)]
        rz_new = _dot(r, z)
        beta = rz_new / rz if rz else 0.0
        rz = rz_new
        p = [zi + beta * pi for zi, pi in zip(z, p)]
    return x
