"""Surface selection on a mesh: replayable operations that yield a facet set.

A selection is a list of operations applied in order, so a client can store
it, send it again with the mesh, and get the same facets back:

- ``{"op": "grow", "mode": "add"|"subtract", "seed_facet": f, "preset":
  "surface"|"flat"|"smooth", "theta_d_deg", "theta_c_deg", "min_radius_mm"}``
  (the preset gives the defaults; ``surface`` by default): breadth-first growth from the
  seed over facet adjacency.  A neighbour ``g`` of an admitted facet ``f``
  is admitted when the dihedral angle between ``f`` and ``g`` is at most
  ``theta_d`` **and** ``g``'s normal is within ``theta_c`` of the seed's
  normal.  The admitted set is one connected component of a fixed graph, so
  it does not depend on the visiting order.  ``theta_c`` 180 grows over a
  whole smooth region bounded by feature edges (curved surfaces);
  ``min_radius_mm`` also leaves out tight blends (fillets) that a flat
  sensor cannot follow.
- ``{"op": "disk", "mode", "seed_facet", "radius_mm", "theta_d_deg"}``:
  the facets whose centroid lies within ``radius_mm`` of the seed's
  centroid along the surface (Dijkstra over facet centroids), without
  crossing edges sharper than ``theta_d``.  Meant for domes and fingertips.
- ``{"op": "facets", "mode", "facets": [...]}``: explicit facets (a brush).
- ``{"op": "cleanup", "min_island_mm2": 1.0}``: keep the largest connected
  piece and pieces of at least ``min_island_mm2``, and fill unselected
  facets whose neighbours are all selected.

Hidden and degenerate facets are never selected.
"""

from __future__ import annotations

import heapq
import math
from typing import Any, Iterable, Mapping, Sequence

from . import bend
from .errors import SurfaceError, finite_number
from .mesh import Mesh, dot, norm, sub

PRESETS = {
    # Flat faces: stops at fillets that are faceted more finely than 4 degrees
    # (the soft finger's R3 fillet starts at 3.0 degrees, so its first strip joins
    # and is trimmed by the margin), keeps a 3.6 degree crease (the crank pad).
    "flat": {"op": "grow", "theta_d_deg": 10.0, "theta_c_deg": 4.0},
    # Smooth curved regions: grows until an edge sharper than 30 degrees.
    "smooth": {"op": "grow", "theta_d_deg": 30.0, "theta_c_deg": 180.0},
    # Any surface: a smooth region without its tight blends (bend radius under
    # 4 mm, e.g. fillets), which a flat sensor cannot follow anyway.
    "surface": {"op": "grow", "theta_d_deg": 30.0, "theta_c_deg": 180.0, "min_radius_mm": 4.0},
}
DEFAULT_PRESET = "surface"
MAX_OPERATIONS = 256
CANDIDATE_MIN_AREA_MM2 = 25.0
CANDIDATE_LIMIT = 24


def facet_dihedral_ok(mesh: Mesh, f: int, g: int, cos_limit: float) -> bool:
    return dot(mesh.normals[f], mesh.normals[g]) >= cos_limit


def grow(mesh: Mesh, seed: int, theta_d_deg: float, theta_c_deg: float, min_radius_mm: float = 0.0) -> set:
    """The seeded region: dihedral <= theta_d between neighbours and within theta_c of the seed.

    With ``min_radius_mm`` the facets whose local bend radius is smaller
    (tight blends) are left out, growth does not cross a crease that a sheet
    of that radius cannot follow (see :mod:`surface.bend`), and the region is
    the seed's component of what remains.
    """

    _check_seed(mesh, seed)
    cos_d = math.cos(math.radians(min(max(theta_d_deg, 0.0), 180.0)))
    cos_c = math.cos(math.radians(min(max(theta_c_deg, 0.0), 180.0)))
    # theta_c 180 admits every normal.  Its test is skipped: the dot product
    # of two antipodal unit normals can round to -1.0000000000000002, below
    # cos(180) = -1, which dropped the facets opposite some seeds of a band.
    seed_cone = theta_c_deg < 180.0
    seed_normal = mesh.normals[seed]
    region = {seed}
    queue = [seed]
    while queue:
        facet = queue.pop()
        for other in mesh.neighbors[facet]:
            if other in region or not mesh.usable(other):
                continue
            if dot(mesh.normals[facet], mesh.normals[other]) < cos_d:
                continue
            if min_radius_mm > 0 and (
                bend.edge_radius(mesh, facet, other, min_radius_mm) == 0
                or bend.facet_radius(mesh, other, min_radius_mm, cos_d) < min_radius_mm
            ):
                continue
            if seed_cone and dot(seed_normal, mesh.normals[other]) < cos_c:
                continue
            region.add(other)
            queue.append(other)
    return region


def disk(mesh: Mesh, seed: int, radius_mm: float, theta_d_deg: float = 30.0) -> set:
    """Facets that reach within ``radius_mm`` of the seed's centroid along the surface.

    Distances run over mesh edges (Dijkstra from the seed facet's corners),
    without crossing an edge sharper than ``theta_d``.  A facet joins when
    one of its corners is within the radius, so on a coarse mesh the
    selection is coarse too (whole facets, slightly beyond the radius).
    """

    _check_seed(mesh, seed)
    cos_d = math.cos(math.radians(min(max(theta_d_deg, 0.0), 180.0)))
    centre = mesh.centroids[seed]
    # Facets reachable without crossing a sharp edge.
    allowed = grow(mesh, seed, theta_d_deg, 180.0) if theta_d_deg < 180.0 else None
    vertex_facets: dict = {}
    for facet in allowed if allowed is not None else range(mesh.facet_count):
        if not mesh.usable(facet):
            continue
        for vertex in mesh.facets[facet]:
            vertex_facets.setdefault(vertex, []).append(facet)
    best: dict = {}
    heap = []
    for vertex in mesh.facets[seed]:
        start = norm(sub(mesh.vertices[vertex], centre))
        best[vertex] = start
        heapq.heappush(heap, (start, vertex))
    done = set()
    while heap:
        distance, vertex = heapq.heappop(heap)
        if vertex in done or distance > best.get(vertex, math.inf) or distance > radius_mm:
            continue
        done.add(vertex)
        for facet in vertex_facets.get(vertex, ()):
            for other in mesh.facets[facet]:
                if other == vertex or other in done:
                    continue
                candidate = distance + norm(sub(mesh.vertices[vertex], mesh.vertices[other]))
                if candidate < best.get(other, math.inf):
                    best[other] = candidate
                    heapq.heappush(heap, (candidate, other))
    region = {seed}
    for vertex in done:
        region.update(vertex_facets.get(vertex, ()))
    del cos_d
    return region


def apply_operations(mesh: Mesh, operations: Sequence[Mapping[str, Any]]) -> set:
    """Replay a selection; raises SurfaceError for a malformed operation."""

    if not isinstance(operations, (list, tuple)) or not operations:
        raise SurfaceError("E_SURFACE_REQUEST", "selection.ops must be a non-empty list of operations.")
    if len(operations) > MAX_OPERATIONS:
        raise SurfaceError("E_SURFACE_REQUEST", f"At most {MAX_OPERATIONS} selection operations.")
    selected: set = set()
    for index, raw in enumerate(operations):
        op = _operation(raw, index)
        kind = op["op"]
        if kind == "cleanup":
            selected = cleanup(mesh, selected, op["min_island_mm2"])
            continue
        if kind == "grow":
            part = grow(mesh, op["seed_facet"], op["theta_d_deg"], op["theta_c_deg"], op["min_radius_mm"])
        elif kind == "disk":
            part = disk(mesh, op["seed_facet"], op["radius_mm"], op["theta_d_deg"])
        else:
            part = set()
            for facet in op["facets"]:
                _check_facet(mesh, facet)
                part.add(facet)
        if op["mode"] == "add":
            selected |= part
        else:
            selected -= part
    selected = {facet for facet in selected if mesh.usable(facet)}
    if not selected:
        raise SurfaceError("E_SURFACE_SELECTION_EMPTY")
    return selected


def cleanup(mesh: Mesh, selected: Iterable[int], min_island_mm2: float) -> set:
    """Fill enclosed facets, then drop small islands (the largest piece always stays)."""

    region = {facet for facet in selected if mesh.usable(facet)}
    for _ in range(2):
        enclosed = set()
        for facet in region:
            for other in mesh.neighbors[facet]:
                if other in region or other in enclosed or not mesh.usable(other):
                    continue
                if all(n in region for n in mesh.neighbors[other]):
                    enclosed.add(other)
        if not enclosed:
            break
        region |= enclosed
    pieces = components(mesh, region)
    if not pieces:
        return region
    areas = [math.fsum(mesh.areas[f] for f in piece) for piece in pieces]
    largest = max(range(len(pieces)), key=lambda i: (areas[i], -min(pieces[i])))
    kept = set()
    for i, piece in enumerate(pieces):
        if i == largest or areas[i] >= min_island_mm2:
            kept |= piece
    return kept


def components(mesh: Mesh, region: Iterable[int]) -> list:
    """Connected pieces of a facet set (edge adjacency), ordered by their lowest facet id."""

    remaining = set(region)
    pieces = []
    for start in sorted(remaining):
        if start not in remaining:
            continue
        piece = {start}
        remaining.discard(start)
        queue = [start]
        while queue:
            facet = queue.pop()
            for other in mesh.neighbors[facet]:
                if other in remaining:
                    remaining.discard(other)
                    piece.add(other)
                    queue.append(other)
        pieces.append(piece)
    return pieces


def candidates(mesh: Mesh, *, preset: str = "flat", min_area_mm2: float = CANDIDATE_MIN_AREA_MM2, limit: int = CANDIDATE_LIMIT) -> list:
    """Segment the whole mesh with a preset and list the larger visible regions.

    Seeds are taken in order of decreasing facet area (ties: lower id), so the
    list is deterministic.  Each entry gives the seed facet that reproduces
    the region with that preset, its area, facet count and mean normal.
    """

    settings = PRESETS[preset]
    order = sorted((f for f in range(mesh.facet_count) if mesh.usable(f)), key=lambda f: (-mesh.areas[f], f))
    claimed: set = set()
    found = []
    for seed in order:
        if seed in claimed:
            continue
        region = grow(mesh, seed, settings["theta_d_deg"], settings["theta_c_deg"], settings.get("min_radius_mm", 0.0))
        claimed |= region
        area = math.fsum(mesh.areas[f] for f in region)
        if area < min_area_mm2:
            continue
        nx = math.fsum(mesh.normals[f][0] * mesh.areas[f] for f in region)
        ny = math.fsum(mesh.normals[f][1] * mesh.areas[f] for f in region)
        nz = math.fsum(mesh.normals[f][2] * mesh.areas[f] for f in region)
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        found.append(
            {
                "seed_facet": seed,
                "preset": preset,
                "area_mm2": area,
                "facets": len(region),
                "mean_normal": [nx / length, ny / length, nz / length],
                # A flat region has a mean normal of length ~1 (area-weighted).
                "flatness": length / area if area else 0.0,
            }
        )
    found.sort(key=lambda item: (-item["area_mm2"], item["seed_facet"]))
    return found[:limit]


def nearest_facet(mesh: Mesh, point: Sequence[float], direction: Sequence[float] | None = None) -> int:
    """The usable facet nearest a point (CLI picking); ties go to the lower id.

    With ``direction`` (a view ray), only facets facing against it count.
    """

    best = None
    for facet in range(mesh.facet_count):
        if not mesh.usable(facet):
            continue
        if direction is not None and dot(mesh.normals[facet], direction) >= 0:
            continue
        distance = point_triangle_distance(point, *mesh.facet_points(facet))
        key = (distance, facet)
        if best is None or key < best:
            best = key
    if best is None:
        raise SurfaceError("E_SURFACE_FACET", "The mesh has no selectable facet.")
    return best[1]


def point_triangle_distance(p, a, b, c) -> float:
    """Euclidean distance from a point to a triangle (Ericson, Real-Time Collision Detection 5.1.5)."""

    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0:
        return norm(ap)
    bp = sub(p, b)
    d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0 and d4 <= d3:
        return norm(bp)
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        t = d1 / (d1 - d3)
        return norm(sub(p, (a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2])))
    cp = sub(p, c)
    d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0 and d5 <= d6:
        return norm(cp)
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        t = d2 / (d2 - d6)
        return norm(sub(p, (a[0] + t * ac[0], a[1] + t * ac[1], a[2] + t * ac[2])))
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return norm(sub(p, (b[0] + t * (c[0] - b[0]), b[1] + t * (c[1] - b[1]), b[2] + t * (c[2] - b[2]))))
    denominator = 1.0 / (va + vb + vc)
    v, w = vb * denominator, vc * denominator
    closest = (a[0] + ab[0] * v + ac[0] * w, a[1] + ab[1] * v + ac[1] * w, a[2] + ab[2] * v + ac[2] * w)
    return norm(sub(p, closest))


def _operation(raw: Any, index: int) -> dict:
    where = f"selection.ops[{index}]"
    if not isinstance(raw, Mapping):
        raise SurfaceError("E_SURFACE_REQUEST", f"{where} must be an object.")
    kind = raw.get("op")
    if not isinstance(kind, str):
        raise SurfaceError("E_SURFACE_REQUEST", f"{where}.op must be a string.")
    allowed = {
        "grow": {"op", "mode", "seed_facet", "theta_d_deg", "theta_c_deg", "min_radius_mm", "preset"},
        "disk": {"op", "mode", "seed_facet", "radius_mm", "theta_d_deg"},
        "facets": {"op", "mode", "facets"},
        "cleanup": {"op", "min_island_mm2"},
    }
    if kind not in allowed:
        raise SurfaceError("E_SURFACE_REQUEST", f"{where}.op must be one of {', '.join(sorted(allowed))}.")
    unknown = sorted(set(raw) - allowed[kind])
    if unknown:
        raise SurfaceError("E_SURFACE_REQUEST", f"{where} has unknown keys: {', '.join(unknown)}.")
    op: dict = {"op": kind}
    if kind == "cleanup":
        op["min_island_mm2"] = _number(raw.get("min_island_mm2", 1.0), f"{where}.min_island_mm2", 0.0, 1e9)
        return op
    mode = raw.get("mode", "add")
    if not isinstance(mode, str) or mode not in ("add", "subtract"):
        raise SurfaceError("E_SURFACE_REQUEST", f"{where}.mode must be add or subtract.")
    op["mode"] = mode
    if kind == "facets":
        facets = raw.get("facets")
        if not isinstance(facets, list) or not all(isinstance(f, int) and not isinstance(f, bool) for f in facets):
            raise SurfaceError("E_SURFACE_REQUEST", f"{where}.facets must be a list of facet ids.")
        op["facets"] = facets
        return op
    op["seed_facet"] = _integer(raw.get("seed_facet"), f"{where}.seed_facet")
    if kind == "grow":
        name = raw.get("preset", DEFAULT_PRESET)
        preset = PRESETS.get(name) if isinstance(name, str) else None
        if preset is None:
            raise SurfaceError("E_SURFACE_REQUEST", f"{where}.preset must be one of {', '.join(PRESETS)}.")
        op["theta_d_deg"] = _number(raw.get("theta_d_deg", preset["theta_d_deg"]), f"{where}.theta_d_deg", 0.0, 180.0)
        op["theta_c_deg"] = _number(raw.get("theta_c_deg", preset["theta_c_deg"]), f"{where}.theta_c_deg", 0.0, 180.0)
        op["min_radius_mm"] = _number(raw.get("min_radius_mm", preset.get("min_radius_mm", 0.0)), f"{where}.min_radius_mm", 0.0, 1e4)
    else:
        op["radius_mm"] = _number(raw.get("radius_mm"), f"{where}.radius_mm", 0.0, 1e6)
        op["theta_d_deg"] = _number(raw.get("theta_d_deg", 30.0), f"{where}.theta_d_deg", 0.0, 180.0)
    return op


def _number(value: Any, where: str, low: float, high: float) -> float:
    return finite_number(value, where, low, high)


def _integer(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SurfaceError("E_SURFACE_REQUEST", f"{where} must be an integer facet id.")
    return value


def _check_facet(mesh: Mesh, facet: int) -> None:
    if not 0 <= facet < mesh.facet_count:
        raise SurfaceError("E_SURFACE_FACET", f"Facet {facet} is outside 0..{mesh.facet_count - 1}.")


def _check_seed(mesh: Mesh, facet: int) -> None:
    _check_facet(mesh, facet)
    if facet in mesh.degenerate:
        raise SurfaceError("E_SURFACE_FACET", f"Facet {facet} is degenerate (no area).")
    if facet in mesh.hidden:
        raise SurfaceError("E_SURFACE_FACET", f"Facet {facet} is hidden inside the part.")
