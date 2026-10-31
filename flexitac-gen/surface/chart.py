"""Flatten a selected patch into a 2D chart (millimetres), with its distortion.

A flat FPC can lie on a surface without stretching only where the surface
is developable (zero Gaussian curvature).  The chart is built in this order:

1. **planar**: all patch vertices within ``PLANAR_TOLERANCE_MM`` of the
   area-weighted plane: orthogonal projection (strain below 1e-4 in
   practice).
2. **developable**: rigid unfolding across shared edges in breadth-first
   order (each facet keeps its exact shape).  Exact when no vertex is placed
   twice at different points (``conflict``) and no facet stretches (the
   Gauss image is then a curve: normals vary in one direction only).
   Covers creased pads, extrusions, cylinders and cones.
3. **curved**: least-squares conformal map (LSCM), then as-rigid-as-possible
   (ARAP) iterations, which leave a measured stretch per facet.

The chart frame is the patch frame of the plan: seen from outside (looking
against the outward normal) ``u`` points right and ``v`` up.  Per facet the
two singular values of the 3D-to-2D map are kept; ``strain`` is the larger
of ``|s1 - 1|`` and ``|s2 - 1|``.
"""

from __future__ import annotations

import hashlib
import math
import threading
from array import array
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from . import solve
from .errors import SurfaceError
from .mesh import Mesh, add, cross, dist2, dot, hypot2, norm, plane_axes, scale, sub, unit

PLANAR_TOLERANCE_MM = 0.05
UNFOLD_CONFLICT_MM = 0.01
# An unfolding is exact only if no facet stretches either: where it meets
# itself on a doubly curved patch of small facets, a conflict well under
# UNFOLD_CONFLICT_MM can still stretch the facets there by percents.  Every
# facet edge must keep its 3D length to UNFOLD_STRAIN of it plus the float32
# spacing at the selection's largest coordinate (UNFOLD_FLOAT32 of it, the
# resolution of a binary STL).  Edge lengths, not the singular values: a
# needle facet (its apex a micron off its long edge) turns 0.1 nm of
# placement into a "strain" of 1e-4, and float32 rounding 3 m from the
# origin stretches 0.02 mm fillet strips by 1e-3, without either being
# curved.  On the doubly curved caps tried, edges change by 0.4 to 4%.
# Developable meshes unfold to about 1e-13 near the origin (the crank pad,
# float32 cylinders); 1e-4 is also the smallest strain limit a fit takes.
UNFOLD_STRAIN = 1e-4
UNFOLD_FLOAT32 = 2.0 ** -23
# Gauss image: the normals of a developable patch spread along one direction.
GAUSS_RANK_RATIO = 0.25
GAUSS_MIN_SPREAD = 1e-6
GAUSS_HIDDEN_SPREAD = 0.05
MAX_CHART_VERTICES = 200_000
# Curved patches are flattened by LSCM + ARAP in pure Python (two sparse
# factorizations, see surface.solve): about 0.3 s at 1,000 vertices and 1.5 s at
# 2,900 on CPython 3.9 (0.2 s and 0.9 s on 3.12); a strain-limited fit flattens
# up to seven smaller disks again, about twice that.  The factors fill in faster
# than the vertex count grows, so larger curved selections are refused.
MAX_SOLVE_VERTICES = 3000


@dataclass
class Chart:
    """A flattened patch: uv per mesh vertex and the distortion per facet."""

    facets: tuple
    vertices: tuple
    uv: dict
    kind: str
    method: str
    normal: tuple
    origin: tuple
    axes: tuple
    loops: list
    outer: int
    strain: dict
    stats: dict = field(default_factory=dict)

    def facet_uv(self, facet: int, mesh: Mesh) -> list:
        return [self.uv[v] for v in mesh.facets[facet]]

    def outline(self) -> list:
        """The outer boundary in uv, counter-clockwise."""

        return [self.uv[v] for v in self.loops[self.outer]]

    def holes(self) -> list:
        return [[self.uv[v] for v in loop] for i, loop in enumerate(self.loops) if i != self.outer]


# --------------------------------------------------------------------------
# Patch topology
# --------------------------------------------------------------------------


def patch_topology(mesh: Mesh, facets: Iterable[int]) -> dict:
    """Boundary loops (directed, patch on the left), Euler characteristic, bowties."""

    region = sorted(set(facets))
    directed: dict = {}
    vertex_set = {v for facet in region for v in mesh.facets[facet]}
    edge_count = set()
    for facet in region:
        a, b, c = oriented_facet(mesh, facet)
        for start, end in ((a, b), (b, c), (c, a)):
            # An edge with another selected facet's vertex on it (a T-junction)
            # counts as its pieces, so the facets on both sides close up.
            chain = split_chain(mesh, start, end, vertex_set)
            for x, y in zip(chain, chain[1:]):
                directed[(x, y)] = facet
                edge_count.add((min(x, y), max(x, y)))
    boundary = [(start, end) for (start, end) in directed if (end, start) not in directed]
    # Walk loops over directed boundary edges; at a bowtie take edges in sorted order.
    outgoing: dict = {}
    for start, end in sorted(boundary):
        outgoing.setdefault(start, []).append(end)
    bowties = sorted(v for v, ends in outgoing.items() if len(ends) > 1)
    loops = []
    used = set()
    for start, end in sorted(boundary):
        if (start, end) in used:
            continue
        loop = [start]
        current, nxt = start, end
        while True:
            used.add((current, nxt))
            if nxt == start:
                break
            loop.append(nxt)
            options = [e for e in outgoing.get(nxt, ()) if (nxt, e) not in used]
            if not options:
                break
            current, nxt = nxt, options[0]
        loops.append(loop)
    euler = len(vertex_set) - len(edge_count) + len(region)
    return {
        "facets": len(region),
        "vertices": len(vertex_set),
        "edges": len(edge_count),
        "euler": euler,
        "loops": loops,
        "bowtie_vertices": bowties,
        "disk": euler == 1 and len(loops) == 1 and not bowties,
    }


def split_chain(mesh: Mesh, start: int, end: int, keep=None) -> list:
    """The edge from ``start`` to ``end`` with the T-junction vertices on it, in order.

    ``keep`` limits the inner vertices to a set (the vertices of a selection).
    """

    inner = mesh.edge_splits.get((start, end))
    if inner is None:
        inner = mesh.edge_splits.get((end, start))
        if inner is None:
            return [start, end]
        inner = inner[::-1]
    if keep is not None:
        inner = [v for v in inner if v in keep]
    return [start, *inner, end]


def oriented_facet(mesh: Mesh, facet: int) -> tuple:
    """The facet's vertex ids in counter-clockwise order seen from outside (outward normal)."""

    a, b, c = mesh.facets[facet]
    pa, pb, pc = mesh.vertices[a], mesh.vertices[b], mesh.vertices[c]
    if dot(cross(sub(pb, pa), sub(pc, pa)), mesh.normals[facet]) < 0:
        return (a, c, b)
    return (a, b, c)


# --------------------------------------------------------------------------
# Building the chart
# --------------------------------------------------------------------------


def cut_band(mesh: Mesh, facets: Iterable[int], seed: Any = None) -> tuple:
    """Open a band (a selection with two boundary loops, e.g. wrapped round a finger).

    The seam is the shortest edge path from the first loop's vertex farthest
    from the seed to the other loop.  The facets round the seam's vertices
    on one side of it are removed (the side of smaller area, unless only the
    other leaves a disk); the other side keeps the seam as its edge, which
    leaves one strip that can be flattened.  Returns (facets, seam info) or
    the facets unchanged when the selection is not a band.
    """

    region = set(facets)
    topology = patch_topology(mesh, region)
    if not (len(topology["loops"]) == 2 and topology["euler"] == 0 and not topology["bowtie_vertices"]):
        return region, None
    first, second = topology["loops"]
    targets = set(second)
    centre = mesh.centroids[seed] if seed is not None and seed in region else mesh.centroids[min(region)]
    start = max(first, key=lambda v: (norm(sub(mesh.vertices[v], centre)), -v))
    adjacency: dict = {}
    for facet in region:
        a, b, c = mesh.facets[facet]
        for x, y in ((a, b), (b, c), (c, a)):
            adjacency.setdefault(x, set()).add(y)
            adjacency.setdefault(y, set()).add(x)
    import heapq

    best = {start: 0.0}
    previous: dict = {}
    heap = [(0.0, start)]
    end = None
    while heap:
        distance, vertex = heapq.heappop(heap)
        if distance > best.get(vertex, math.inf):
            continue
        if vertex in targets:
            end = vertex
            break
        for other in sorted(adjacency.get(vertex, ())):
            candidate = distance + norm(sub(mesh.vertices[vertex], mesh.vertices[other]))
            if candidate < best.get(other, math.inf):
                best[other] = candidate
                previous[other] = vertex
                heapq.heappush(heap, (candidate, other))
    if end is None:
        return region, None
    path = [end]
    while path[-1] != start:
        path.append(previous[path[-1]])
    path.reverse()
    # The seam starts at the path's last vertex on the first loop (a stretch
    # along the loop itself cuts nothing).
    on_first = set(first)
    path = path[max(k for k, v in enumerate(path) if v in on_first):]
    seam_edges = {frozenset(pair) for pair in zip(path, path[1:])}
    # The facets round each seam vertex v, by the other end z of each edge v-z.
    fans: dict = {v: {} for v in path}
    for facet in sorted(region):
        for v in mesh.facets[facet]:
            if v in fans:
                for z in mesh.facets[facet]:
                    if z != v:
                        fans[v].setdefault(z, []).append(facet)

    def side(left: bool) -> set:
        # Removing only the facets that share a seam edge left the two sides
        # of each inner seam vertex meeting at that vertex alone (a bowtie):
        # take each seam vertex's whole fan on one side instead, walking round
        # the vertex from the facet on that side of a seam edge (oriented
        # x -> y on the left, seen from outside) without crossing the seam.
        removed = set()
        for x, y in zip(path, path[1:]):
            for facet in fans[x].get(y, ()):
                a, b, c = oriented_facet(mesh, facet)
                if ((x, y) in ((a, b), (b, c), (c, a))) != left:
                    continue
                for v in (x, y):
                    found, stack = {facet}, [facet]
                    while stack:
                        for z in mesh.facets[stack.pop()]:
                            if z != v and frozenset((v, z)) not in seam_edges:
                                for other in fans[v][z]:
                                    if other not in found:
                                        found.add(other)
                                        stack.append(other)
                    removed |= found
        return removed

    sides = sorted((side(True), side(False)), key=lambda removed: math.fsum(mesh.areas[f] for f in removed))
    removed = next((s for s in sides if s and patch_topology(mesh, region - s)["disk"]), sides[0])
    opened = region - removed
    return opened, {"seam_vertices": [mesh.vertices[v] for v in path], "removed_facets": sorted(removed), "removed_area_mm2": math.fsum(mesh.areas[f] for f in removed)}


CHART_CACHE_SIZE = 8
# Charts beyond this many vertices in all are evicted (the newest one always stays).
CHART_CACHE_VERTICES = 600_000
_CHART_CACHE: "OrderedDict[tuple, Chart]" = OrderedDict()
_CHART_LOCK = threading.Lock()


def build_chart(mesh: Mesh, facets: Iterable[int], *, allow_curved: bool = True, seed: Any = None, initial: Any = None) -> Chart:
    """The chart of a selection (see the module docstring), from a small cache.

    Select, fit and map flatten the same selection of the same mesh, and the
    fit's strain limit flattens a few disks of it again; a curved solve
    takes about a second, so the last charts are kept (a chart is never
    changed after it is built, except for its lazily built point index).

    ``initial`` (uv by vertex id, e.g. a larger chart's) starts a curved
    solve's ARAP from there instead of from LSCM.  Such a chart is neither
    taken from nor put in the cache, which holds charts built from scratch.
    """

    region = tuple(sorted(set(facets)))
    if not region:
        raise SurfaceError("E_SURFACE_SELECTION_EMPTY")
    digest = hashlib.sha256(array("q", region).tobytes()).hexdigest()
    key = (mesh.sha256, mesh.unit, digest, bool(allow_curved), seed if isinstance(seed, int) and seed in region else None)
    if initial is not None:
        return _build_chart(mesh, region, allow_curved=allow_curved, seed=key[4], initial=initial)
    with _CHART_LOCK:
        chart = _CHART_CACHE.get(key)
        if chart is not None:
            _CHART_CACHE.move_to_end(key)
            return chart
    chart = _build_chart(mesh, region, allow_curved=allow_curved, seed=key[4])
    with _CHART_LOCK:
        _CHART_CACHE[key] = chart
        while len(_CHART_CACHE) > 1 and (
            len(_CHART_CACHE) > CHART_CACHE_SIZE or sum(len(c.vertices) for c in _CHART_CACHE.values()) > CHART_CACHE_VERTICES
        ):
            _CHART_CACHE.popitem(last=False)
    return chart


def _build_chart(mesh: Mesh, region: tuple, *, allow_curved: bool, seed: Any, initial: Any = None) -> Chart:
    pieces = _pieces(mesh, region)
    if len(pieces) > 1:
        areas = sorted((round(math.fsum(mesh.areas[f] for f in piece), 3) for piece in pieces), reverse=True)
        raise SurfaceError(
            "E_SURFACE_NOT_DISK",
            f"The selection has {len(pieces)} separate pieces ({', '.join(f'{a:g}' for a in areas)} mm2); the "
            "array needs one connected surface. Remove the smaller pieces from the selection.",
            pieces=len(pieces),
            areas_mm2=areas,
        )
    topology = patch_topology(mesh, region)
    if not topology["loops"]:
        raise SurfaceError("E_SURFACE_NOT_DISK", "The selection is a closed surface (no boundary).")
    seam = None
    attempt = _exact_chart(mesh, region)
    if attempt["uv"] is None:
        # A band (two boundary loops round a finger) that does not unfold as it
        # is: open it along a seam and try again.  A face with one hole that
        # is flat or unfolds exactly is kept whole.
        opened, seam = cut_band(mesh, region, seed)
        if seam is not None and opened:
            region = tuple(sorted(opened))
            topology = patch_topology(mesh, region)
            attempt = _exact_chart(mesh, region)
        else:
            seam = None
    if attempt["normal"] is None:
        raise SurfaceError("E_SURFACE_NOT_DEVELOPABLE", "The selection's normals cancel out (a closed or folded surface).")
    vertex_ids, normal, origin, u_axis, v_axis = (attempt[k] for k in ("vertex_ids", "normal", "origin", "u_axis", "v_axis"))
    gauss = attempt["gauss"]
    stats: dict = {
        "area_mm2": math.fsum(mesh.areas[f] for f in region),
        "seam": None if seam is None else {"removed_facets": len(seam["removed_facets"]), "removed_area_mm2": seam["removed_area_mm2"]},
        "plane_deviation_mm": attempt["deviation"],
        "gauss_spread": gauss["spread"],
        "gauss_rank_ratio": gauss["rank_ratio"],
        "topology": {k: v for k, v in topology.items() if k != "loops"},
    }
    if attempt["conflict"] is not None:
        stats["unfold_conflict_mm"] = attempt["conflict"]
    uv = attempt["uv"]
    if uv is not None:
        kind, method = attempt["kind"], attempt["method"]
        if kind == "developable" and gauss["rank_ratio"] > GAUSS_RANK_RATIO and gauss["spread"] > GAUSS_HIDDEN_SPREAD:
            stats["warning"] = (
                "The facets unfold exactly, but their normals turn in two directions: a coarse "
                "tessellation may hide double curvature of the real part."
            )
    else:
        if not allow_curved:
            raise SurfaceError("E_SURFACE_NOT_DEVELOPABLE")
        if not topology["disk"]:
            raise SurfaceError(
                "E_SURFACE_NOT_DISK",
                f"The selection has {len(topology['loops'])} boundary loops, Euler characteristic "
                f"{topology['euler']} and {len(topology['bowtie_vertices'])} bowtie vertices; a curved "
                "selection must be one piece without holes.",
            )
        if len(vertex_ids) > MAX_SOLVE_VERTICES:
            raise SurfaceError(
                "E_SURFACE_MESH_TOO_LARGE",
                f"The curved selection has {len(vertex_ids)} vertices; curved surfaces are flattened up to "
                f"{MAX_SOLVE_VERTICES} vertices. Select a smaller area (for example with the disk tool).",
            )
        if initial is not None and all(v in initial for v in vertex_ids):
            uv = solve.conformal_then_rigid(mesh, region, vertex_ids, topology["loops"][0], initial=initial)
            kind, method = "curved", "arap"
        else:
            uv = solve.conformal_then_rigid(mesh, region, vertex_ids, topology["loops"][0])
            kind, method = "curved", "lscm+arap"
    uv = _orient(uv, mesh, region, vertex_ids, origin, u_axis, v_axis)
    strain = {f: singular_values(mesh, f, uv) for f in region}
    loops = topology["loops"]
    areas = [abs(_loop_area([uv[v] for v in loop])) for loop in loops]
    outer = max(range(len(loops)), key=lambda i: (areas[i], -i))
    for i, loop in enumerate(loops):
        signed = _loop_area([uv[v] for v in loop])
        if (i == outer and signed < 0) or (i != outer and signed > 0):
            loops[i] = list(reversed(loop))
    values = sorted(max(abs(s1 - 1), abs(s2 - 1)) for s1, s2 in strain.values())
    weights = {f: mesh.areas[f] for f in region}
    stats.update(
        {
            "chart_area_mm2": math.fsum(abs(_tri_area(*[uv[v] for v in oriented_facet(mesh, f)])) for f in region),
            "strain_max": values[-1] if values else 0.0,
            "strain_p95": _weighted_percentile(
                [(max(abs(s1 - 1), abs(s2 - 1)), weights[f]) for f, (s1, s2) in strain.items()], 0.95
            ),
            "flipped_facets": sum(1 for f in region if _tri_area(*[uv[v] for v in oriented_facet(mesh, f)]) <= 0),
        }
    )
    return Chart(
        facets=region,
        vertices=vertex_ids,
        uv=uv,
        kind=kind,
        method=method,
        normal=normal,
        origin=origin,
        axes=(u_axis, v_axis),
        loops=loops,
        outer=outer,
        strain=strain,
        stats=stats,
    )


def _pieces(mesh: Mesh, region: Sequence[int]) -> list:
    """Edge-connected pieces of the region."""

    remaining = set(region)
    pieces = []
    for start in region:
        if start not in remaining:
            continue
        remaining.discard(start)
        piece = [start]
        queue = deque([start])
        while queue:
            facet = queue.popleft()
            for other in mesh.neighbors[facet]:
                if other in remaining:
                    remaining.discard(other)
                    piece.append(other)
                    queue.append(other)
        pieces.append(piece)
    return pieces


def _exact_chart(mesh: Mesh, region: Sequence[int]) -> dict:
    """The planar projection or the rigid unfolding, when one of them is exact (uv None otherwise)."""

    vertex_ids = tuple(sorted({v for f in region for v in mesh.facets[f]}))
    if len(vertex_ids) > MAX_CHART_VERTICES:
        raise SurfaceError(
            "E_SURFACE_MESH_TOO_LARGE",
            f"The selection has {len(vertex_ids)} vertices; at most {MAX_CHART_VERTICES} can be flattened.",
        )
    fitted = _plane_fit(mesh, region, vertex_ids)
    if fitted is None:
        # The area-weighted normals cancel out exactly, as on a band round a
        # part with a symmetric tessellation (a prism's side walls, most
        # closed cylinders): no plane and no chart frame.  The caller opens a
        # band along a seam and tries again, and refuses anything else.
        return {"vertex_ids": vertex_ids, "normal": None, "conflict": None, "uv": None}
    normal, origin, deviation = fitted
    u_axis, v_axis = _chart_axes(normal)
    attempt = {
        "vertex_ids": vertex_ids,
        "normal": normal,
        "origin": origin,
        "u_axis": u_axis,
        "v_axis": v_axis,
        "deviation": deviation,
        "gauss": gauss_image(mesh, region),
        "conflict": None,
        "uv": None,
    }
    if deviation <= PLANAR_TOLERANCE_MM:
        attempt.update(uv={v: _project(mesh.vertices[v], origin, u_axis, v_axis) for v in vertex_ids}, kind="planar", method="projection")
        return attempt
    uv, conflict = unfold(mesh, region, u_axis, v_axis, origin)
    attempt["conflict"] = conflict
    if conflict <= UNFOLD_CONFLICT_MM and _keeps_lengths(mesh, region, vertex_ids, uv):
        # The tessellated surface is intrinsically flat: the sheet lies on it
        # exactly.  Holes are fine; a band round a part gives a large conflict.
        attempt.update(uv=uv, kind="developable", method="unfold")
    return attempt


def _keeps_lengths(mesh: Mesh, region: Sequence[int], vertex_ids: Sequence[int], uv: dict) -> bool:
    """Whether every facet edge keeps its 3D length in ``uv`` (see UNFOLD_STRAIN)."""

    floor = UNFOLD_FLOAT32 * max(abs(x) for v in vertex_ids for x in mesh.vertices[v])
    for facet in region:
        a, b, c = mesh.facets[facet]
        for p, q in ((a, b), (b, c), (c, a)):
            length = norm(sub(mesh.vertices[q], mesh.vertices[p]))
            if abs(dist2(uv[p], uv[q]) - length) > UNFOLD_STRAIN * length + floor:
                return False
    return True


def _plane_fit(mesh: Mesh, region: Sequence[int], vertex_ids: Sequence[int]) -> Any:
    """Area-weighted mean normal, area-weighted centroid, and the largest vertex distance.

    None when the normals cancel out exactly (no mean plane).
    """

    nx = math.fsum(mesh.normals[f][0] * mesh.areas[f] for f in region)
    ny = math.fsum(mesh.normals[f][1] * mesh.areas[f] for f in region)
    nz = math.fsum(mesh.normals[f][2] * mesh.areas[f] for f in region)
    normal = unit((nx, ny, nz))
    if normal == (0.0, 0.0, 0.0):
        return None
    total = math.fsum(mesh.areas[f] for f in region)
    cx = math.fsum(mesh.centroids[f][0] * mesh.areas[f] for f in region) / total
    cy = math.fsum(mesh.centroids[f][1] * mesh.areas[f] for f in region) / total
    cz = math.fsum(mesh.centroids[f][2] * mesh.areas[f] for f in region) / total
    origin = (cx, cy, cz)
    deviation = max(abs(dot(sub(mesh.vertices[v], origin), normal)) for v in vertex_ids)
    return normal, origin, deviation


def _chart_axes(normal: Sequence[float]) -> tuple:
    """u right and v up when looking against the normal (v = n x u, u = v x n)."""

    u_axis, _ = plane_axes(normal)
    v_axis = cross(normal, u_axis)
    return u_axis, v_axis


def _project(point, origin, u_axis, v_axis) -> tuple:
    d = sub(point, origin)
    return (dot(d, u_axis), dot(d, v_axis))


def gauss_image(mesh: Mesh, region: Sequence[int]) -> dict:
    """How the normals spread: ``rank_ratio`` near 0 means along one direction (developable)."""

    total = math.fsum(mesh.areas[f] for f in region)
    mean = unit(tuple(math.fsum(mesh.normals[f][k] * mesh.areas[f] for f in region) / total for k in range(3)))
    u_axis, v_axis = plane_axes(mean)
    # Local differences between neighbouring normals capture the Gauss map's
    # direction field better than a global covariance on long curved strips.
    sxx = sxy = syy = 0.0
    in_region = set(region)
    for f in region:
        for g in mesh.neighbors[f]:
            if g <= f or g not in in_region:
                continue
            d = sub(mesh.normals[g], mesh.normals[f])
            # Rotate the difference into the local tangent plane of f.
            tu, tv = plane_axes(mesh.normals[f])
            x, y = dot(d, tu), dot(d, tv)
            # Express in a global 2D frame so directions are comparable.
            gx = dot(add(scale(tu, x), scale(tv, y)), u_axis)
            gy = dot(add(scale(tu, x), scale(tv, y)), v_axis)
            sxx += gx * gx
            sxy += gx * gy
            syy += gy * gy
    trace = sxx + syy
    if trace <= GAUSS_MIN_SPREAD:
        return {"spread": trace, "rank_ratio": 0.0}
    disc = math.sqrt(max((sxx - syy) ** 2 / 4 + sxy * sxy, 0.0))
    high = trace / 2 + disc
    low = max(trace / 2 - disc, 0.0)
    return {"spread": trace, "rank_ratio": low / high if high > 0 else 0.0}


def unfold(mesh: Mesh, region: Sequence[int], u_axis, v_axis, origin) -> tuple:
    """Rigid breadth-first unfolding; returns (uv, largest placement conflict in mm)."""

    in_region = set(region)
    start = max(region, key=lambda f: (mesh.areas[f], -f))
    uv: dict = {}
    # The first facet keeps its exact shape: projected onto its own plane,
    # with axes taken from the chart axes projected into that plane.
    own = mesh.normals[start]
    fu = sub(u_axis, scale(own, dot(u_axis, own)))
    fu = unit(fu) if norm(fu) > 1e-9 else plane_axes(own)[0]
    fv = cross(own, fu)
    centre = mesh.centroids[start]
    for v in mesh.facets[start]:
        uv[v] = _project(mesh.vertices[v], centre, fu, fv)
    placed = {start}
    conflict = 0.0
    queue = deque([start])
    while queue:
        facet = queue.popleft()
        for other in mesh.neighbors[facet]:
            if other in placed or other not in in_region:
                continue
            shared = [v for v in mesh.facets[other] if v in mesh.facets[facet]]
            if len(shared) == 2:
                a, b = shared
                opposite = next(v for v in mesh.facets[facet] if v not in shared)
            else:
                # A T-junction: the two facets' edges lie on one line.  The
                # other facet's edge ends are placed on that line first.
                link = mesh.cracks.get((facet, other))
                if link is None:
                    continue
                (s, e), (a, b) = link
                for v in (a, b):
                    point = _on_line(mesh, s, e, v, uv)
                    if v in uv:
                        conflict = max(conflict, dist2(point, uv[v]))
                    else:
                        uv[v] = point
                opposite = next(v for v in mesh.facets[facet] if v not in (s, e))
            c = next(v for v in mesh.facets[other] if v not in (a, b))
            point = _hinge(mesh, a, b, c, uv[a], uv[b], uv[opposite])
            if c in uv:
                conflict = max(conflict, dist2(point, uv[c]))
            else:
                uv[c] = point
            placed.add(other)
            queue.append(other)
    missing = [v for f in region for v in mesh.facets[f] if v not in uv]
    if missing:
        raise SurfaceError("E_SURFACE_NOT_DISK", "The selection is not connected across edges.")
    return uv, conflict


def _on_line(mesh: Mesh, s: int, e: int, v: int, uv: dict) -> tuple:
    """uv of vertex ``v``, which lies on the line through placed vertices ``s`` and ``e``."""

    S, E = mesh.vertices[s], mesh.vertices[e]
    d = sub(E, S)
    t = dot(sub(mesh.vertices[v], S), d) / dot(d, d)
    return (uv[s][0] + t * (uv[e][0] - uv[s][0]), uv[s][1] + t * (uv[e][1] - uv[s][1]))


def _hinge(mesh: Mesh, a: int, b: int, c: int, pa, pb, opposite) -> tuple:
    """Place c so that triangle (a, b, c) keeps its 3D shape, across edge ab from ``opposite``."""

    A, B, C = mesh.vertices[a], mesh.vertices[b], mesh.vertices[c]
    ab = norm(sub(B, A))
    ac = norm(sub(C, A))
    bc = norm(sub(C, B))
    placed = dist2(pa, pb)
    if ab == 0 or placed == 0:
        return pa
    x = (ac * ac - bc * bc + ab * ab) / (2 * ab)
    y = math.sqrt(max(ac * ac - x * x, 0.0))
    # The placed edge's direction, a unit vector.  Divided by the 3D length
    # instead, it scaled the new facet about pa by the placed edge's length
    # error; a sliver hands that on to its short edge times its aspect ratio,
    # so on thin strips the error grew row by row (1.4 m over 40 rows).
    ex = ((pb[0] - pa[0]) / placed, (pb[1] - pa[1]) / placed)
    # The perpendicular pointing away from the already placed triangle.
    perp = (-ex[1], ex[0])
    side = (opposite[0] - pa[0]) * perp[0] + (opposite[1] - pa[1]) * perp[1]
    if side > 0:
        perp = (-perp[0], -perp[1])
    return (pa[0] + ex[0] * x + perp[0] * y, pa[1] + ex[1] * x + perp[1] * y)


def _orient(uv: dict, mesh: Mesh, region, vertex_ids, origin, u_axis, v_axis) -> dict:
    """Rotate and translate the chart to best match the projection onto the mean plane.

    Keeps orientation (no reflection unless the chart came out mirrored, which
    is fixed first), so u right and v up hold when looking from outside.
    """

    projected = {v: _project(mesh.vertices[v], origin, u_axis, v_axis) for v in vertex_ids}
    signed = math.fsum(_tri_area(*[uv[v] for v in oriented_facet(mesh, f)]) * mesh.areas[f] for f in region)
    if signed < 0:
        uv = {v: (p[0], -p[1]) for v, p in uv.items()}
    # Procrustes (rotation only) between uv and the projection.
    cu = (math.fsum(uv[v][0] for v in vertex_ids) / len(vertex_ids), math.fsum(uv[v][1] for v in vertex_ids) / len(vertex_ids))
    cp = (
        math.fsum(projected[v][0] for v in vertex_ids) / len(vertex_ids),
        math.fsum(projected[v][1] for v in vertex_ids) / len(vertex_ids),
    )
    sxx = sxy = 0.0
    for v in vertex_ids:
        x, y = uv[v][0] - cu[0], uv[v][1] - cu[1]
        px, py = projected[v][0] - cp[0], projected[v][1] - cp[1]
        sxx += x * px + y * py
        sxy += x * py - y * px
    length = hypot2(sxx, sxy)
    c, s = (sxx / length, sxy / length) if length > 0 else (1.0, 0.0)
    return {
        v: (cp[0] + c * (p[0] - cu[0]) - s * (p[1] - cu[1]), cp[1] + s * (p[0] - cu[0]) + c * (p[1] - cu[1]))
        for v, p in uv.items()
    }


def singular_values(mesh: Mesh, facet: int, uv: dict) -> tuple:
    """Singular values of the linear map from the 3D triangle to its chart triangle."""

    a, b, c = mesh.facets[facet]
    A, B, C = mesh.vertices[a], mesh.vertices[b], mesh.vertices[c]
    e1 = sub(B, A)
    e2 = sub(C, A)
    l1 = norm(e1)
    if l1 == 0:
        return (1.0, 1.0)
    x_axis = scale(e1, 1 / l1)
    n = cross(e1, e2)
    nn = norm(n)
    if nn == 0:
        return (1.0, 1.0)
    y_axis = cross(scale(n, 1 / nn), x_axis)
    # 3D triangle in its own plane.
    p1 = (l1, 0.0)
    p2 = (dot(e2, x_axis), dot(e2, y_axis))
    q1 = (uv[b][0] - uv[a][0], uv[b][1] - uv[a][1])
    q2 = (uv[c][0] - uv[a][0], uv[c][1] - uv[a][1])
    det = p1[0] * p2[1] - p2[0] * p1[1]
    if det == 0:
        return (1.0, 1.0)
    # J * [p1 p2] = [q1 q2]  =>  J = [q1 q2] * inv([p1 p2])
    inv = ((p2[1] / det, -p2[0] / det), (-p1[1] / det, p1[0] / det))
    j00 = q1[0] * inv[0][0] + q2[0] * inv[1][0]
    j01 = q1[0] * inv[0][1] + q2[0] * inv[1][1]
    j10 = q1[1] * inv[0][0] + q2[1] * inv[1][0]
    j11 = q1[1] * inv[0][1] + q2[1] * inv[1][1]
    # Singular values of a 2x2 matrix.
    e = (j00 + j11) / 2
    f = (j00 - j11) / 2
    g = (j10 + j01) / 2
    h = (j10 - j01) / 2
    q = hypot2(e, h)
    r = hypot2(f, g)
    return (q + r, abs(q - r))


def _tri_area(p, q, r) -> float:
    return ((q[0] - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (q[1] - p[1])) / 2


def _loop_area(points: Sequence) -> float:
    total = 0.0
    for i in range(len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        total += x0 * y1 - x1 * y0
    return total / 2


def _weighted_percentile(values: Sequence, fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    total = math.fsum(w for _, w in ordered)
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= fraction * total:
            return value
    return ordered[-1][0]


def chart_point_to_3d(chart: Chart, mesh: Mesh, point: Sequence[float]) -> Any:
    """Map a chart point to the surface (barycentric in its chart triangle), or None."""

    hit = locate(chart, mesh, point)
    if hit is None:
        return None
    facet, (l0, l1, l2) = hit
    a, b, c = (mesh.vertices[v] for v in mesh.facets[facet])
    return (
        a[0] * l0 + b[0] * l1 + c[0] * l2,
        a[1] * l0 + b[1] * l1 + c[1] * l2,
        a[2] * l0 + b[2] * l1 + c[2] * l2,
    ), facet


def locate(chart: Chart, mesh: Mesh, point: Sequence[float]):
    """The chart facet containing ``point`` and its barycentric coordinates, or None."""

    index = _grid(chart, mesh)
    cell = index["cell"]
    key = (math.floor((point[0] - index["x0"]) / cell), math.floor((point[1] - index["y0"]) / cell))
    best = None
    for facet in index["buckets"].get(key, ()):
        p, q, r = chart.facet_uv(facet, mesh)
        area = _tri_area(p, q, r)
        if area == 0:
            continue
        l1 = _tri_area(p, point, r) / area
        l2 = _tri_area(p, q, point) / area
        l0 = 1 - l1 - l2
        worst = min(l0, l1, l2)
        if best is None or worst > best[0]:
            best = (worst, facet, (l0, l1, l2))
    if best is None or best[0] < -1e-9:
        return None
    return best[1], best[2]


def _grid(chart: Chart, mesh: Mesh) -> dict:
    """The point index of :func:`locate`: grid cells holding the facets whose triangle meets them.

    A facet is put in the cells its triangle overlaps (widened by a hair for
    locate's tolerance), row by row, not in every cell of its bounding box:
    a CAD face with a finely divided curved edge is often a fan of slivers,
    each in about length / cell cells instead of (length / cell)^2, which
    took hundreds of entries per facet and 119 MB at 16,000 slivers.
    """

    cached = chart.stats.get("_grid")
    if cached is not None:
        return cached
    xs = [p[0] for p in chart.uv.values()]
    ys = [p[1] for p in chart.uv.values()]
    x0, y0 = min(xs), min(ys)
    span = max(max(xs) - x0, max(ys) - y0, 1e-6)
    cell = max(span / max(int(math.sqrt(len(chart.facets))), 1), 1e-3)
    # A point within locate's barycentric tolerance (1e-9) of a facet lies
    # within about 1e-9 span of it.
    pad = 1e-6 * span
    buckets: dict = {}
    for facet in chart.facets:
        # The corners from the lowest v to the highest: a, b, c.
        (ax, ay), (bx, by), (cx, cy) = sorted(chart.facet_uv(facet, mesh), key=lambda p: (p[1], p[0]))
        for j in range(math.floor((ay - pad - y0) / cell), math.floor((cy + pad - y0) / cell) + 1):
            # The triangle's u range between the row's lines (widened by pad):
            # where they cut the long side a-c and the chain a-b-c, and b.
            low = max(y0 + j * cell - pad, ay)
            high = min(y0 + (j + 1) * cell + pad, cy)
            if low > high:
                continue
            if cy == ay:
                left, right = min(ax, bx, cx), max(ax, bx, cx)
            else:
                cuts = [ax + (y - ay) * (cx - ax) / (cy - ay) for y in (low, high)]
                for y in (low, high):
                    if y <= by:
                        cuts.append(bx if by == ay else ax + (y - ay) * (bx - ax) / (by - ay))
                    else:
                        cuts.append(bx if cy == by else bx + (y - by) * (cx - bx) / (cy - by))
                if low <= by <= high:
                    cuts.append(bx)
                left, right = min(cuts), max(cuts)
            for i in range(math.floor((left - pad - x0) / cell), math.floor((right + pad - x0) / cell) + 1):
                buckets.setdefault((i, j), []).append(facet)
    index = {"x0": x0, "y0": y0, "cell": cell, "buckets": buckets}
    chart.stats["_grid"] = index
    return index
