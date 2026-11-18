"""Flattening solvers for curved charts, in pure Python.

- **LSCM** in the symmetric form of Mullen et al. (2008): minimise the
  conformal energy ``E_D - A`` (cotangent Dirichlet energy minus the
  signed area of the chart), with two boundary vertices pinned at their 3D
  distance.
- **ARAP** (Liu et al. 2008): local steps fit one rotation per triangle
  (trigonometry-free 2x2 closed form), global steps solve one cotangent
  Laplacian per coordinate.  The stretch left over is reported per facet by
  ``chart.singular_values``.
- **Least max stretch** (since 2026-11-17, :func:`bounded`): a flat PI/Cu
  sheet fails at its largest stretch, so a chart ARAP leaves stretched beyond
  ``BOUNDED_FROM`` is re-solved for the least maximum stretch, ARAP's local
  step replaced by a projection onto bounded distortion (the section below).

They solve sparse symmetric positive definite systems by an LDL^T
factorization in minimum-degree order; ARAP and the least-max-stretch rounds
share one factorization of their Laplacian for all their global steps.  Should a pivot not come out positive (a degenerate
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


# --------------------------------------------------------------------------
# Least max stretch (the user's decisions of 2026-11-17 on gently curved faces)
# --------------------------------------------------------------------------
# ARAP minimises the squared deviation from isometry, which leaves the largest
# stretch at the boundary at about twice the least possible (a spherical cap of
# half-angle a: ARAP's 12 steps reach 1 - sin a / a, the least is about a^2 / 12).
# A flat sheet fails at its largest stretch, so a curved chart is the one of
# least maximum stretch.  ``bounded`` keeps ARAP's global step (the same
# cotangent Laplacian, factored once) and replaces its local step: each
# triangle's Jacobian is projected onto the singular values within
# [1 - eps, 1 + eps] (bounded distortion, Kovalsky et al. 2015; eps 0 is ARAP's
# rotation), eps a fraction of the best maximum so far.  A round of
# BOUNDED_STEPS steps that does not lower the maximum is undone and the next
# aims less low.  The rounds stop once two in a row have lowered the best
# maximum by less than BOUNDED_STOP of it (or after BOUNDED_ROUNDS): a 15-degree
# cap of R 30 mm ends 1.18 x its least stretch, the Dex3-1 fingertip's face of
# the user's report (2026-11-17) at 0.82 % against ARAP's 1.79 %.  A chart that
# ARAP leaves within BOUNDED_FROM (a nearly developable face: the Franka
# Hand's pad, 0.002 %) is kept as ARAP made it.
#
# RELAXED: the chart is where the lattice is laid, not the strain the sheet
# keeps on the part.  A sheet on soft tape (the user's adhesive, 2026-11-17)
# creeps to its elastic state, whatever map it was cut by: ARAP's (its energy
# is the sheet's at Poisson's ratio 0, and the rim's hoop strain a^2 / 8 of a
# cap does not depend on that ratio).  Twelve steps from LSCM reach it: on the
# Dex3-1's patches and on caps of 10 to 20 degrees, 50, 200 and 800 steps move
# the smoothed maximum by under 1 % (2026-11-17).  So the fit judges a curved
# selection by ARAP's chart (surface.chart.judged_stretch), 1.2 to 1.7 x the
# least-max-stretch chart's: the 0.3 % default keeps the copper elastic on the
# part, as the gate of before did.  Slivers (aspect over
# SLIVER_ASPECT) keep ARAP's rotation and do not count in the maximum.  The
# order of every sum is fixed, so the chart is the same on every Python and in
# Pyodide (the module docstring).

BOUNDED_FROM = 5e-4
BOUNDED_STEPS = 20
BOUNDED_SHRINK = 0.8
BOUNDED_STOP = 0.01
BOUNDED_ROUNDS = 40
SLIVER_ASPECT = 20.0


def least_stretch(mesh: Mesh, region: Sequence[int], vertex_ids: Sequence[int], boundary: Sequence[int], initial=None,
                  least: bool = True) -> tuple:
    """(uv for every vertex of the patch, method, relaxed): LSCM (unless ``initial`` is given: ARAP from there), ARAP,
    then :func:`bounded` unless ARAP stretches the patch by BOUNDED_FROM at most (or ``least`` is false: the ARAP chart,
    for a stretch alone).  ``relaxed`` is ARAP's uv, the sheet relaxed on the part (RELAXED below), as solved."""

    index, triangles, _ = _triangles(mesh, region, vertex_ids)
    points = [mesh.vertices[v] for v in vertex_ids]
    if initial is None:
        uv = lscm(points, triangles, [index[v] for v in boundary])
        method = "lscm+arap"
    else:
        uv = [tuple(initial[v]) for v in vertex_ids]
        method = "arap"
    frames = _frames(points, triangles)
    uv = arap(points, triangles, uv, ARAP_ITERATIONS, frames)
    relaxed = {vertex_ids[i]: uv[i] for i in range(len(vertex_ids))}
    if least and _max_stretch(uv, triangles, frames[0]) > BOUNDED_FROM:
        uv = bounded(points, triangles, uv, frames=frames)
        method += "+bounded"
    return {vertex_ids[i]: uv[i] for i in range(len(vertex_ids))}, method, relaxed


def bounded(points: Sequence, triangles: Sequence, uv: Sequence, *, frames=None, steps: int = BOUNDED_STEPS,
            rounds: int = BOUNDED_ROUNDS) -> list:
    """The least-max-stretch rounds from ``uv`` (an ARAP chart): the best uv seen.  ``frames`` as :func:`arap`'s."""

    n = len(points)
    local, weights, rows, system = frames if frames is not None else _frames(points, triangles)
    anchor = {0}
    # Per triangle, fixed for every step: its three edges (a, b, weight, the edge in the triangle's own frame), whether
    # it is a sliver, and its frame's terms for the exact Jacobian (l1, x2, y2, l1 y2).
    terms = []
    for (i, j, k), (wi, wj, wk), (xi, xj, xk) in zip(triangles, weights, local):
        pts = {i: xi, j: xj, k: xk}
        edges = tuple((a, b, w, pts[a][0] - pts[b][0], pts[a][1] - pts[b][1]) for a, b, w in ((j, k, wi), (k, i, wj), (i, j, wk)))
        l1, (x2, y2) = xj[0], xk
        terms.append((i, j, k, edges, _aspect(xj, xk) > SLIVER_ASPECT or l1 * y2 == 0, l1, x2, y2, l1 * y2))
    # u and v of every vertex (two flat lists: the inner loop reads them by index).
    cu = [p[0] for p in uv]
    cv = [p[1] for p in uv]
    factored = system[4] is not None

    def solve_step(eps: float) -> None:
        low, high = 1.0 - eps, 1.0 + eps
        rhs_u = [0.0] * n
        rhs_v = [0.0] * n
        for i, j, k, edges, rigid, l1, x2, y2, det in terms:
            s00 = s01 = s10 = s11 = 0.0
            for a, b, w, dx, dy in edges:
                du = cu[a] - cu[b]
                dv = cv[a] - cv[b]
                s00 += w * du * dx
                s01 += w * du * dy
                s10 += w * dv * dx
                s11 += w * dv * dy
            # ARAP's rotation (the polar factor of the weighted covariance): the target for eps 0 and for a sliver.
            c, sn = s00 + s11, s10 - s01
            length = math.sqrt(c * c + sn * sn)
            c, sn = (c / length, sn / length) if length > 0 else (1.0, 0.0)
            l00, l01, l10, l11 = c, -sn, sn, c
            if eps != 0 and not rigid:
                # The exact Jacobian J, its singular values clipped to [1 - eps, 1 + eps] (J = Q rot + R refl).
                q1u, q1v = cu[j] - cu[i], cv[j] - cv[i]
                q2u, q2v = cu[k] - cu[i], cv[k] - cv[i]
                j00, j01 = q1u * y2 / det, (q2u * l1 - q1u * x2) / det
                j10, j11 = q1v * y2 / det, (q2v * l1 - q1v * x2) / det
                e, f, g, h = (j00 + j11) / 2, (j00 - j11) / 2, (j10 + j01) / 2, (j10 - j01) / 2
                q = math.sqrt(e * e + h * h)
                if q > 0:
                    r = math.sqrt(f * f + g * g)
                    # min(max(t, low), high), without the built-ins' calls.
                    cx = q + r
                    cx = low if cx < low else cx
                    cx = high if cx > high else cx
                    cy = q - r
                    cy = low if cy < low else cy
                    cy = high if cy > high else cy
                    kq = (cx + cy) / 2 / q
                    kr = (cx - cy) / 2 / r if r > 0 else 0.0
                    l00, l01, l10, l11 = kq * e + kr * f, -kq * h + kr * g, kq * h + kr * g, kq * e - kr * f
            for a, b, w, dx, dy in edges:
                ru = w * (l00 * dx + l01 * dy)
                rv = w * (l10 * dx + l11 * dy)
                rhs_u[a] += ru
                rhs_v[a] += rv
                rhs_u[b] -= ru
                rhs_v[b] -= rv
        # The guess serves only the CG fallback of a system that did not factor.
        new_u = _solve_pinned(rows, {p: cu[p] for p in anchor}, rhs_u, guess=None if factored else list(cu), max_iterations=max(100, 2 * n), system=system)
        new_v = _solve_pinned(rows, {p: cv[p] for p in anchor}, rhs_v, guess=None if factored else list(cv), max_iterations=max(100, 2 * n), system=system)
        cu[:] = new_u
        cv[:] = new_v

    best = (list(zip(cu, cv)), _max_stretch(list(zip(cu, cv)), triangles, local))
    shrink = BOUNDED_SHRINK
    history = [best[1]]
    for _ in range(rounds):
        eps = shrink * best[1]
        for _ in range(steps):
            solve_step(eps)
        reached_uv = list(zip(cu, cv))
        reached = _max_stretch(reached_uv, triangles, local)
        if reached < best[1]:
            best = (reached_uv, reached)
        else:
            cu[:] = [p[0] for p in best[0]]
            cv[:] = [p[1] for p in best[0]]
            shrink = (1 + shrink) / 2
        history.append(best[1])
        if len(history) >= 3 and history[-3] - history[-1] < BOUNDED_STOP * history[-3]:
            break
    return best[0]


def _local_frames(points: Sequence, triangles: Sequence) -> tuple:
    """Each triangle in its own plane (isometric 2D coordinates) and its clamped cotangent weights, as :func:`arap`'s."""

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
        weights.append(
            tuple(
                max(COT_FLOOR, min(COT_LIMIT, _cot(points[p], points[q], points[r])))
                for p, q, r in ((j, k, i), (k, i, j), (i, j, k))
            )
        )
    return local, weights


def _frames(points: Sequence, triangles: Sequence) -> tuple:
    """(local, weights, rows, system): each triangle in its own plane and its cotangent weights (:func:`_local_frames`),
    the cotangent Laplacian's rows and its factorization with vertex 0 pinned: the same matrix in every global step of
    ARAP and of :func:`bounded`, for u and v, factored once."""

    n = len(points)
    local, weights = _local_frames(points, triangles)
    rows: list = [dict() for _ in range(n)]
    for (i, j, k), (wi, wj, wk) in zip(triangles, weights):
        for a, b, w in ((j, k, wi), (k, i, wj), (i, j, wk)):
            rows[a][a] = rows[a].get(a, 0.0) + w
            rows[b][b] = rows[b].get(b, 0.0) + w
            rows[a][b] = rows[a].get(b, 0.0) - w
            rows[b][a] = rows[b].get(a, 0.0) - w
    return local, weights, rows, _pinned_system(rows, {0})


def _jacobian(current, i, j, k, xj, xk) -> Any:
    """The triangle's Jacobian (its local frame to uv), or None for a degenerate triangle."""

    l1 = xj[0]
    x2, y2 = xk
    det = l1 * y2
    if det == 0:
        return None
    q1u, q1v = current[j][0] - current[i][0], current[j][1] - current[i][1]
    q2u, q2v = current[k][0] - current[i][0], current[k][1] - current[i][1]
    return (q1u * y2 / det, (q2u * l1 - q1u * x2) / det, q1v * y2 / det, (q2v * l1 - q1v * x2) / det)


def _aspect(xj, xk) -> float:
    l1 = xj[0]
    x2, y2 = xk
    if l1 == 0 or y2 == 0:
        return math.inf
    # Squared lengths (no math.hypot, whose last bit changed in Python 3.10).
    longest = max(l1 * l1, x2 * x2 + y2 * y2, (x2 - l1) * (x2 - l1) + y2 * y2)
    return longest / abs(l1 * y2)


def _max_stretch(current, triangles, local) -> float:
    """The largest stretch of the triangles (their exact Jacobians), slivers (aspect over SLIVER_ASPECT) left out."""

    worst = 0.0
    for (i, j, k), (_, xj, xk) in zip(triangles, local):
        if _aspect(xj, xk) > SLIVER_ASPECT:
            continue
        jac = _jacobian(current, i, j, k, xj, xk)
        if jac is None:
            continue
        j00, j01, j10, j11 = jac
        e, f, g, h = (j00 + j11) / 2, (j00 - j11) / 2, (j10 + j01) / 2, (j10 - j01) / 2
        q = math.sqrt(e * e + h * h)
        r = math.sqrt(f * f + g * g)
        worst = max(worst, abs(q + r - 1), abs(abs(q - r) - 1))
    return worst


def _triangles(mesh: Mesh, region: Sequence[int], vertex_ids: Sequence[int]) -> tuple:
    """(vertex index, solver triangles, the facet of each triangle): T-junction facets as fans."""

    from .chart import oriented_facet, split_chain

    index = {v: i for i, v in enumerate(vertex_ids)}
    keep = set(vertex_ids)
    triangles = []
    owners = []
    for f in region:
        corners = oriented_facet(mesh, f)
        sides = [split_chain(mesh, corners[k], corners[(k + 1) % 3], keep) for k in range(3)]
        if all(len(side) == 2 for side in sides):
            triangles.append(tuple(index[v] for v in corners))
            owners.append(f)
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
                owners.append(f)
    return index, triangles, owners


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


def arap(points: Sequence, triangles: Sequence, uv: Sequence, iterations: int, frames=None) -> list:
    """ARAP's ``iterations`` local/global steps from ``uv``; ``frames`` is :func:`_frames` of the same triangles (built
    when not given; :func:`least_stretch` shares them with :func:`bounded`)."""

    n = len(points)
    local, weights, rows, system = frames if frames is not None else _frames(points, triangles)
    anchor = 0
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
