"""Surface selection on a mesh: replayable operations that yield a facet set.

A selection is a list of operations applied in order, so a client can store
it, send it again with the mesh, and get the same facets back:

- ``{"op": "grow", "mode": "add"|"subtract", "seed_facet": f, "preset":
  "surface"|"flat"|"smooth"|"stretch", "theta_d_deg", "theta_c_deg", "min_radius_mm",
  "stretch_budget"}`` (the preset gives the defaults; ``surface`` by default):
  breadth-first growth from the seed over facet adjacency.  A neighbour ``g``
  of an admitted facet ``f`` is admitted when the dihedral angle between ``f``
  and ``g`` is at most ``theta_d`` **and** ``g``'s normal is within
  ``theta_c`` of the seed's normal.  The admitted set is one connected
  component of a fixed graph, so it does not depend on the visiting order.
  ``theta_c`` 180 grows over a whole smooth region bounded by feature edges
  (curved surfaces); ``min_radius_mm`` also leaves out tight blends (fillets)
  that a flat sensor cannot follow.
  **By stretch** (the user's decisions of 2026-11-17, :func:`stretch_region`):
  preset ``stretch`` (``stretch_budget`` 0.003, the fit's default strain
  limit, unless named) selects, round the dome the seed lies on, the largest
  patch whose least-max-stretch chart a flat sheet covers within the budget;
  any other grow naming ``stretch_budget`` (the page's click: the Surface
  preset at the strain limit chosen) does so only where its grown region is
  doubly curved (:func:`doubly_curved`), and is the grown region itself on a
  planar or developable face.  On a mirror-symmetric face (:func:`mirror_maps`)
  the patch is its own mirror image wherever it reaches the mirror plane (the
  user's feedback of 2026-11-17: "finger应该是对称的").
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
    # By stretch (2026-11-17): within the Surface preset's region, the largest patch round its dome that flattens within
    # the budget (stretch_region); theta_c the widest cone of normals it may take round the dome's axis.
    "stretch": {"op": "grow", "theta_d_deg": 30.0, "theta_c_deg": 90.0, "min_radius_mm": 4.0, "stretch_budget": 0.003},
}
DEFAULT_PRESET = "surface"
# A grown region is doubly curved (a click on it selects by stretch) when its total curvature, the area of its Gauss
# image (total_curvature), is beyond that of a disk stretched by 0.025 % flat (Omega / 12 pi): the developable faces
# measured stay below a third of it (a 60-degree cone 0.0028 sr, a cylinder 0.0004 sr on fine, strip and skewed
# meshes), every Library face's region but the Unitree Dex3-1's dome below 1e-3 sr (the dome, back in the Library since
# 2026-11-18, doubly curved), a 10-degree cap of R 20 mm in 6 strips 0.011 sr.
DOUBLY_CURVED_SR = 12 * math.pi * 2.5e-4
# The angle defects of a triangulation are smoothed this many times within the region (curvature_passes), so that the
# defects of alternating sign of an irregular developable mesh cancel and smooth curvature stays.
CURVATURE_PASSES = 4
# The dome's cone: re-centred on the patch's own mean normal at most this many times (grow_mean).
MEAN_CONE_PASSES = 6
# ... and the hemisphere round the region's mean normal (dome_axis) at most this many times.
AXIS_PASSES = 6
# stretch_region: the face itself tried when its total curvature is within this many times 12 pi budget (a face's least
# stretch is about Omega / 12 pi when it is round, and less only when it is long and narrow: the Dex3-1's palmar dome
# 0.65 x, a strip 10 x longer than wide about 0.5 x; the fingertip's whole face, 1.06 sr, is 9 x the 0.3 % budget's),
WHOLE_FACE_SCREEN = 4.0
# ... the widest cone within 12 pi budget of total curvature, bisected this many times (the first guess),
OMEGA_BISECTIONS = 8
# ... then this many more patches, regula falsi on (theta^2, stretch) towards the budget, and up to STRETCH_MORE more
# while the widest patch within the budget stretches less than STRETCH_NEAR of it (none known yet, or a step across a
# non-monotone stretch: on a coarse or lat-long mesh the patch and its stretch grow in steps),
STRETCH_STEPS = 3
STRETCH_MORE = 8
STRETCH_NEAR = 0.9
# ... a first step out at most STRETCH_GROWTH x the cone; a cone whose patch is one judged at an end of the bracket moved
# to one of its own (_widest_within's between).
STRETCH_GROWTH = 2.0
# smooth_outline: notches filled and teeth cut this many times at most; convex_fill: only a region whose facets all face
# within this many degrees of its mean normal.
SMOOTH_OUTLINE_PASSES = 4
CONVEX_FILL_DEG = 60.0
# mirror_maps (the user's feedback of 2026-11-17: the finger is symmetric, the selection was not): a plane is a face's
# mirror plane when, for MIRROR_SHARE of the face's area, each facet's centroid mirrored lies on a facet of the face within
# MIRROR_TOLERANCE_MM (the symmetric-face rule's tolerance, surface.fieldfit.SYMMETRY_TOLERANCE_MM) whose normal is the
# mirrored normal within MIRROR_NORMAL_DEG; the planes tried pass through the face's area centroid, across the coordinate
# axes and its principal axes (one within MIRROR_SAME_DEG of a plane found is that plane).  The last MIRROR_CACHE faces'
# maps are kept on the mesh.
MIRROR_TOLERANCE_MM = 0.05
MIRROR_NORMAL_DEG = 10.0
MIRROR_SHARE = 0.99
MIRROR_SAME_DEG = 1.0
MIRROR_CACHE = 8
# ... a plane through the area centroid that fails is fitted to the face (_fitted_plane: MIRROR_FIT_PASSES steps on the
# facets that mirror within MIRROR_FIT_MM of it, at least MIRROR_FIT_SHARE of the area) and tried again: a feature on one
# side of a symmetric face (a hole, a slot, a boss) moves its centroid off the plane (the review of 2026-11-17, finding 3:
# a 4 mm2 hole, 0.4 % of a dome, lost its plane).
MIRROR_FIT_MM = 0.5
MIRROR_FIT_SHARE = 0.9
MIRROR_FIT_PASSES = 2
MAX_OPERATIONS = 256
CANDIDATE_MIN_AREA_MM2 = 25.0
CANDIDATE_LIMIT = 24


def facet_dihedral_ok(mesh: Mesh, f: int, g: int, cos_limit: float) -> bool:
    return dot(mesh.normals[f], mesh.normals[g]) >= cos_limit


def grow(mesh: Mesh, seed: int, theta_d_deg: float, theta_c_deg: float, min_radius_mm: float = 0.0, axis=None) -> set:
    """The seeded region: dihedral <= theta_d between neighbours and within theta_c of the seed.

    With ``min_radius_mm`` the facets whose local bend radius is smaller
    (tight blends) are left out, growth does not cross a crease that a sheet
    of that radius cannot follow (see :mod:`surface.bend`), and the region is
    the seed's component of what remains.  ``axis`` (a unit vector) takes the
    seed normal's place in the cone test (:func:`grow_mean`).
    """

    _check_seed(mesh, seed)
    cos_d = math.cos(math.radians(min(max(theta_d_deg, 0.0), 180.0)))
    cos_c = math.cos(math.radians(min(max(theta_c_deg, 0.0), 180.0)))
    # theta_c 180 admits every normal.  Its test is skipped: the dot product
    # of two antipodal unit normals can round to -1.0000000000000002, below
    # cos(180) = -1, which dropped the facets opposite some seeds of a band.
    seed_cone = theta_c_deg < 180.0
    seed_normal = mesh.normals[seed] if axis is None else axis
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


# --------------------------------------------------------------------------
# By stretch (the user's decisions of 2026-11-17 on gently curved faces)
# --------------------------------------------------------------------------
# A flat sheet on a doubly curved face stretches by about K rho^2 / 8 over a
# patch of radius rho once it relaxes on the part (a disk of total curvature
# Omega, the area of its Gauss image: about Omega / 8 pi).  The presets above stop
# at sharp edges, not at stretch: on a fingertip's dome the Surface preset takes
# the whole cap (refused: holes, beyond any strain limit) and a cone of normals
# cuts a staircase.  So a click on a doubly curved face selects the face when it
# fits the budget whole, else the largest patch round the dome that does (the
# stretch the sheet keeps on the part, surface.chart.judged_stretch), the same
# patch from any click on it; a click off that patch, the largest round the click.


def face_graph(mesh: Mesh, face, theta_d_deg: float, min_radius_mm: float) -> dict:
    """The edges :func:`grow` crosses within a grown face (its dihedral and bend tests) either way, each facet's
    neighbours across them (by id): worked out once for the many cones of :func:`stretch_region` (the bend tests are the
    costly part of a grow).

    Undirected: grow tests the bend of the facet it enters, and a face's facets all pass it but the seed, which grow
    starts from; a seed tighter than ``min_radius_mm`` is entered from its neighbours here, so a cone grown from any facet
    of the face reaches the facets grow reached from the seed (the AgileX Piper's facet 1008, 2026-11-17)."""

    cos_d = math.cos(math.radians(min(max(theta_d_deg, 0.0), 180.0)))
    linked: dict = {facet: set() for facet in face}
    for facet in sorted(face):
        for other in mesh.neighbors[facet]:
            if other not in face or not mesh.usable(other):
                continue
            if dot(mesh.normals[facet], mesh.normals[other]) < cos_d:
                continue
            # grow's bend tests, as it applies them.
            blocked = min_radius_mm > 0 and (
                bend.edge_radius(mesh, facet, other, min_radius_mm) == 0
                or bend.facet_radius(mesh, other, min_radius_mm, cos_d) < min_radius_mm
            )
            if not blocked:
                linked[facet].add(other)
                linked[other].add(facet)
    return {facet: sorted(linked[facet]) for facet in sorted(face)}


def cone_grow(mesh: Mesh, graph: dict, centre: int, axis, theta_c_deg: float) -> set:
    """:func:`grow` from ``centre`` within a face (its :func:`face_graph`), the cone of ``theta_c`` round ``axis``."""

    cos_c = math.cos(math.radians(min(max(theta_c_deg, 0.0), 180.0)))
    cone = theta_c_deg < 180.0
    region = {centre}
    queue = [centre]
    while queue:
        facet = queue.pop()
        for other in graph[facet]:
            if other in region or (cone and dot(axis, mesh.normals[other]) < cos_c):
                continue
            region.add(other)
            queue.append(other)
    return region


def grow_mean(mesh: Mesh, graph: dict, centre: int, axis, theta_c_deg: float) -> set:
    """The cone of ``theta_c`` round ``axis`` grown from ``centre`` within a face (:func:`cone_grow`), the cone then
    re-centred on the region's own area-weighted mean normal (and the facet nearest it the centre) until the region
    repeats (at most MEAN_CONE_PASSES; the last region otherwise)."""

    region = cone_grow(mesh, graph, centre, axis, theta_c_deg)
    seen = [frozenset(region)]
    for _ in range(MEAN_CONE_PASSES):
        axis = _mean_normal(mesh, region)
        if axis is None:
            break
        centre = _nearest_normal(mesh, region, axis)
        region = cone_grow(mesh, graph, centre, axis, theta_c_deg)
        key = frozenset(region)
        if key in seen:
            break
        seen.append(key)
    return region


def dome_axis(mesh: Mesh, face: set, seed: int, planes: Sequence = ()) -> tuple:
    """(axis, centre): the face's half seen from the click, by its mean normal, canonical for every click on it.

    From the face's area-weighted mean normal (the seed's own normal when the seed faces away from it), the axis
    becomes the mean normal of the face's facets in front of it (within 90 degrees) until that half repeats (at most
    AXIS_PASSES); the centre is the facet whose normal is nearest the axis (the lowest id on a tie).  Only the face (the
    seed's grown region) decides, so the clicks on a dome that grow the same face give one axis and centre; on a
    mirror-symmetric face they lie on its plane of symmetry: the axis is laid on each of its mirror ``planes``
    (:func:`mirror_maps`; its component across the plane, rounding's, taken out)."""

    axis = _mean_normal(mesh, face)
    if axis is None or dot(mesh.normals[seed], axis) <= 0:
        axis = mesh.normals[seed]
    seen: list = []
    for _ in range(AXIS_PASSES):
        half = frozenset(f for f in face if dot(mesh.normals[f], axis) > 0)
        if not half or half in seen:
            break
        seen.append(half)
        mean = _mean_normal(mesh, half)
        if mean is None:
            break
        axis = mean
    for _, normal, _ in planes:
        across = dot(axis, normal)
        laid = (axis[0] - across * normal[0], axis[1] - across * normal[1], axis[2] - across * normal[2])
        if norm(laid) > 1e-9:
            axis = _unit(laid)
    return axis, _nearest_normal(mesh, face, axis)


def _nearest_normal(mesh: Mesh, region, axis) -> int:
    return max(sorted(region), key=lambda f: dot(mesh.normals[f], axis))


def doubly_curved(mesh: Mesh, region) -> bool:
    """Whether a grown region is doubly curved: its total curvature beyond DOUBLY_CURVED_SR (planar and developable faces,
    whatever their tessellation, stay below it)."""

    return total_curvature(mesh, region) > DOUBLY_CURVED_SR


# --------------------------------------------------------------------------
# Mirror-symmetric faces (the user's feedback of 2026-11-17: "finger应该是对称的，但是你select的面不对称")
# --------------------------------------------------------------------------
# A cone of normals round an axis on the mirror plane is symmetric only up to the last bit of each facet's test, and a
# cone round a click off the plane is not symmetric at all; on a tessellation that is not itself symmetric (a quad grid's
# diagonals all one way) neither is.  So a face's mirror planes are found on the mesh, and every patch the stretch search
# tries is taken with its mirror image (mirror_closure) wherever the two make one piece.


def mirror_maps(mesh: Mesh, face) -> list:
    """The face's mirror planes, each ``(point, normal, pairs)``: ``pairs`` maps each facet to the facets it mirrors to or
    from (its centroid mirrored lies on the other within MIRROR_TOLERANCE_MM, the normals mirrored within
    MIRROR_NORMAL_DEG).  A plane counts when MIRROR_SHARE of the face's area mirrors onto it.

    The planes tried pass through the face's area centroid, across the coordinate axes (a part drawn in CAD is drawn
    symmetric about them; a tessellation that is not itself symmetric turns the principal axes a little) and then its
    principal axes (of its facets' centroids, by area: a mirror plane is across one, unless two of the moments are
    equal), each but within MIRROR_SAME_DEG of a plane found.  One that fails through the centroid is fitted to the
    facets that mirror nearly onto the face and tried again (:func:`_fitted_plane`)."""

    key = frozenset(face)
    cache = mesh.__dict__.setdefault("_mirror_maps", {})
    if key in cache:
        return cache[key]
    ordered = sorted(key)
    total = math.fsum(mesh.areas[f] for f in ordered)
    planes: list = []
    if total > 0 and len(ordered) > 1:
        centre = tuple(math.fsum(mesh.centroids[f][k] * mesh.areas[f] for f in ordered) / total for k in range(3))
        moments = [[math.fsum(mesh.areas[f] * (mesh.centroids[f][i] - centre[i]) * (mesh.centroids[f][j] - centre[j]) for f in ordered)
                    for j in range(3)] for i in range(3)]
        grid = _FacetGrid(mesh, ordered)
        loose: list = []  # the grid of the fitting passes, made when one is needed
        cos_n = math.cos(math.radians(MIRROR_NORMAL_DEG))
        same = math.cos(math.radians(MIRROR_SAME_DEG))
        for normal in [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)] + _principal_axes(moments):
            if any(abs(dot(normal, known)) > same for _, known, _ in planes):
                continue
            point = centre
            pairs = _mirror_pairs(mesh, ordered, total, centre, normal, grid, cos_n)
            if pairs is None:
                if not loose:
                    loose.append(_FacetGrid(mesh, ordered, MIRROR_FIT_MM))
                fitted = _fitted_plane(mesh, ordered, total, centre, normal, grid, loose[0], cos_n)
                if fitted is None or any(abs(dot(fitted[1], known)) > same for _, known, _ in planes):
                    continue
                point, normal, pairs = fitted
            if pairs is not None:
                planes.append((point, normal, pairs))
    cache[key] = planes
    while len(cache) > MIRROR_CACHE:
        cache.pop(next(iter(cache)))
    return planes


def _mirror_pairs(mesh: Mesh, ordered: list, total: float, centre, normal, grid, cos_n: float, tolerance: float = MIRROR_TOLERANCE_MM,
                  share: float = MIRROR_SHARE, found_pairs: Any = None) -> Any:
    """The facet pairs of one candidate plane, or None when less than ``share`` of the area mirrors within ``tolerance``
    (given up as soon as more than the rest is lost).  ``found_pairs``, a list, gets each ``(facet, its image's facet)``."""

    lost_most = (1 - share) * total
    lost = 0.0
    pairs: dict = {f: set() for f in ordered}
    for f in ordered:
        c = mesh.centroids[f]
        side = 2 * dot(sub(c, centre), normal)
        image = (c[0] - side * normal[0], c[1] - side * normal[1], c[2] - side * normal[2])
        n = mesh.normals[f]
        turn = 2 * dot(n, normal)
        mirrored = (n[0] - turn * normal[0], n[1] - turn * normal[1], n[2] - turn * normal[2])
        found = grid.nearest(image, tolerance)
        if found is None or dot(mirrored, mesh.normals[found]) < cos_n:
            lost += mesh.areas[f]
            if lost > lost_most:
                return None
            continue
        pairs[f].add(found)
        pairs[found].add(f)
        if found_pairs is not None:
            found_pairs.append((f, found))
    return {f: sorted(others) for f, others in pairs.items() if others}


def _fitted_plane(mesh: Mesh, ordered: list, total: float, centre, normal, grid, loose, cos_n: float) -> Any:
    """``(point, normal, pairs)``: a candidate plane that fails through the face's centroid fitted to the face and tested
    again (``grid``); None when it still fails.  The fit: Gauss-Newton steps (MIRROR_FIT_PASSES) on each facet's mirrored
    centroid's distance to the plane of the facet it falls on, within MIRROR_FIT_MM (at least MIRROR_FIT_SHARE of the area
    must; ``loose`` their grid), by area; first the plane moved along its normal alone (a part drawn symmetric about a
    coordinate plane keeps that normal), then also turned.  A tessellation that is not symmetric moves no facet off the
    surface, which a fit to the facets' own centroids would (a quad grid's mirrored centroids fall on its diagonals)."""

    for turn in (False, True):
        point, axis = centre, normal
        for _ in range(MIRROR_FIT_PASSES):
            found: list = []
            if _mirror_pairs(mesh, ordered, total, point, axis, loose, cos_n, MIRROR_FIT_MM, MIRROR_FIT_SHARE, found) is None:
                return None
            k = min(range(3), key=lambda i: (abs(axis[i]), i))
            t1 = _unit(_cross(axis, tuple(1.0 if i == k else 0.0 for i in range(3))))
            t2 = _cross(axis, t1)
            rows = []
            for f, g in found:
                c, n = mesh.centroids[f], mesh.normals[g]
                off = sub(c, point)
                height = dot(off, axis)
                image = (c[0] - 2 * height * axis[0], c[1] - 2 * height * axis[1], c[2] - 2 * height * axis[2])
                residual = dot(sub(image, mesh.centroids[g]), n)
                along = dot(axis, n)
                jacobian = [2 * along]
                if turn:
                    jacobian += [-2 * (along * dot(off, t) + height * dot(t, n)) for t in (t1, t2)]
                rows.append((mesh.areas[f], jacobian, residual))
            size = len(rows[0][1]) if rows else 0
            if not size:
                return None
            normal_matrix = [[math.fsum(w * jac[i] * jac[j] for w, jac, _ in rows) for j in range(size)] for i in range(size)]
            right = [-math.fsum(w * jac[i] * r for w, jac, r in rows) for i in range(size)]
            scale = max(normal_matrix[i][i] for i in range(size))
            if scale <= 0:
                return None
            for i in range(size):
                normal_matrix[i][i] += 1e-9 * scale
            step = _solve(normal_matrix, right)
            if step is None:
                return None
            point = (point[0] + step[0] * axis[0], point[1] + step[0] * axis[1], point[2] + step[0] * axis[2])
            if turn:
                axis = _unit((axis[0] + step[1] * t1[0] + step[2] * t2[0], axis[1] + step[1] * t1[1] + step[2] * t2[1],
                              axis[2] + step[1] * t1[2] + step[2] * t2[2]))
        pairs = _mirror_pairs(mesh, ordered, total, point, axis, grid, cos_n)
        if pairs is not None:
            return point, axis, pairs
    return None


def _solve(matrix: list, right: list) -> Any:
    """x with matrix x = right (Gaussian elimination with partial pivoting, at most 3 x 3), or None when singular."""

    n = len(right)
    a = [row[:] + [right[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: (abs(a[r][col]), -r))
        if a[pivot][col] == 0:
            return None
        a[col], a[pivot] = a[pivot], a[col]
        for r in range(col + 1, n):
            factor = a[r][col] / a[col][col]
            for c in range(col, n + 1):
                a[r][c] -= factor * a[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (a[r][n] - math.fsum(a[r][c] * x[c] for c in range(r + 1, n))) / a[r][r]
    return x


def _principal_axes(m: list) -> list:
    """The eigenvectors of a symmetric 3 x 3 matrix (cyclic Jacobi rotations, in a fixed order)."""

    a = [row[:] for row in m]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(32):
        scale = abs(a[0][0]) + abs(a[1][1]) + abs(a[2][2])
        if abs(a[0][1]) + abs(a[0][2]) + abs(a[1][2]) <= 1e-15 * scale:
            break
        for p, q in ((0, 1), (0, 2), (1, 2)):
            if a[p][q] == 0.0:
                continue
            theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
            t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1))
            c = 1 / math.sqrt(t * t + 1)
            s = t * c
            # A <- J^T A J and V <- V J, J the identity but J[p][p] = J[q][q] = c, J[p][q] = s, J[q][p] = -s.
            for k in range(3):
                a[k][p], a[k][q] = c * a[k][p] - s * a[k][q], s * a[k][p] + c * a[k][q]
                v[k][p], v[k][q] = c * v[k][p] - s * v[k][q], s * v[k][p] + c * v[k][q]
            for k in range(3):
                a[p][k], a[q][k] = c * a[p][k] - s * a[q][k], s * a[p][k] + c * a[q][k]
    return [_unit((v[0][k], v[1][k], v[2][k])) for k in range(3)]


class _FacetGrid:
    """The facets of a face in a grid of cells as wide as their median extent (each in the cells its box, grown by the
    mirror tolerance or ``grow_by``, overlaps): the facet nearest a point, within that distance, in the point's own cell."""

    def __init__(self, mesh: Mesh, ordered: list, grow_by: float = MIRROR_TOLERANCE_MM) -> None:
        self.mesh = mesh
        extents = sorted(max(max(p[k] for p in mesh.facet_points(f)) - min(p[k] for p in mesh.facet_points(f)) for k in range(3))
                         for f in ordered)
        self.size = max(extents[len(extents) // 2], 4 * grow_by)
        self.cells: dict = {}
        for f in ordered:
            points = mesh.facet_points(f)
            low = [math.floor((min(p[k] for p in points) - grow_by) / self.size) for k in range(3)]
            high = [math.floor((max(p[k] for p in points) + grow_by) / self.size) for k in range(3)]
            for i in range(low[0], high[0] + 1):
                for j in range(low[1], high[1] + 1):
                    for k in range(low[2], high[2] + 1):
                        self.cells.setdefault((i, j, k), []).append(f)

    def nearest(self, point, within: float) -> Any:
        cell = tuple(math.floor(point[k] / self.size) for k in range(3))
        best = None
        for f in self.cells.get(cell, ()):
            distance = point_triangle_distance(point, *self.mesh.facet_points(f))
            if distance <= within and (best is None or (distance, f) < best):
                best = (distance, f)
        return None if best is None else best[1]


def mirror_closure(mesh: Mesh, region, planes: Sequence) -> set:
    """The region with its mirror image across each of the face's mirror planes (:func:`mirror_maps`) that it reaches:
    taken with its image when the two make one piece (the region reaches the plane), as it is otherwise (a patch on one
    side of the plane, whose mirror image is the patch a click there selects)."""

    region = set(region)
    for _ in range(2):
        changed = False
        for _, _, pairs in planes:
            closed = set(region)
            queue = sorted(region)
            while queue:
                facet = queue.pop()
                for other in pairs.get(facet, ()):
                    if other not in closed:
                        closed.add(other)
                        queue.append(other)
            if closed != region and len(components(mesh, closed)) == 1:
                region = closed
                changed = True
        if not changed:
            break
    return region


def stretch_region(mesh: Mesh, seed: int, theta_d_deg: float, theta_c_deg: float, min_radius_mm: float, budget: float,
                   face=None) -> set:
    """The largest patch of the seed's face that the sheet covers within ``budget`` (the strain limit), by stretch.

    ``face`` is the seed's grown region (the Surface preset's: theta_d, every normal, min_radius), computed when not
    given; the patch lies within it and holds the seed.  The stretch is the one the sheet keeps on the part, as the fit
    judges it (surface.chart.judged_stretch: the relaxed sheet's, smoothed; a planar or developable patch 0).

    1. The face itself, when it fits the budget whole (tried when its total curvature is within WHOLE_FACE_SCREEN x
       12 pi budget: a face far beyond it cannot fit).
    2. Else the widest patch within the budget round the dome (:func:`dome_axis`, the cone re-centred by
       :func:`grow_mean`): the same patch from any click on the dome.
    3. When that patch does not hold the click (a click on the face's side or far end), the widest within the budget
       round the click: the cone round its own normal, grown from it.

    Each search widens the cone of normals up to ``theta_c`` (at most 90 degrees; :func:`smooth_outline` cuts its teeth
    and fills its notches) by :func:`_widest_within`.  On a mirror-symmetric face (:func:`mirror_maps`, the user's feedback
    of 2026-11-17) the dome's axis lies on each mirror plane and every patch tried is taken with its mirror image where
    the two make one piece (:func:`mirror_closure`): the dome's patch is symmetric, and so is a click's that reaches the
    plane (the fingertip's tip end); a click's patch on one side of the plane is the mirror image of its mirror click's."""

    from . import chart as chart_module

    if face is None:
        face = grow(mesh, seed, theta_d_deg, 180.0, min_radius_mm)
    face = frozenset(face)
    stretches: dict = {}

    def stretch_of(region: frozenset) -> float:
        found = stretches.get(region)
        if found is None:
            try:
                chart = chart_module.build_chart(mesh, region, least=False)
                if chart.kind != "curved":
                    found = 0.0
                elif not chart_module.patch_topology(mesh, region)["disk"]:
                    # A curved patch with a hole (a ring): its chart opens it along a seam on one side, leaving out facets
                    # the selection draws (the review of 2026-11-17, finding 1); never taken.
                    found = math.inf
                else:
                    found = chart_module.judged_stretch(chart, mesh)
            except SurfaceError:
                found = math.inf
            stretches[region] = found
        return found

    if total_curvature(mesh, face) <= WHOLE_FACE_SCREEN * 12 * math.pi * budget and stretch_of(face) <= budget:
        return set(face)
    widest = min(max(theta_c_deg, 0.0), 90.0)
    graph = face_graph(mesh, face, theta_d_deg, min_radius_mm)
    planes = mirror_maps(mesh, face)
    axis, centre = dome_axis(mesh, face, seed, planes)
    patch = _widest_within(mesh, graph, face, centre, axis, widest, budget, theta_d_deg, stretch_of, planes, recentre=True)
    if seed not in patch:
        patch = _widest_within(mesh, graph, face, seed, mesh.normals[seed], widest, budget, theta_d_deg, stretch_of, planes, recentre=False)
    if not math.isfinite(stretch_of(frozenset(patch))):
        # Nothing wider than the centre's own patch within the budget, and that one not a sheet (the review of
        # 2026-11-17, finding 6): the click's facet alone, which the fit takes.
        return {seed}
    return patch


def _widest_within(mesh: Mesh, graph: dict, face: frozenset, centre: int, axis, widest: float, budget: float,
                   theta_d_deg: float, stretch_of, planes: Sequence = (), *, recentre: bool) -> set:
    """The widest cone round ``axis`` grown from ``centre`` (re-centred by :func:`grow_mean` when ``recentre``, outline
    smoothed) whose patch stays within ``budget``, at most ``widest`` degrees.

    First the widest cone whose total curvature is within 12 pi budget (OMEGA_BISECTIONS bisections; a disk of constant
    curvature flattens with a least stretch of Omega / 12 pi), then regula falsi on (theta^2, stretch) between the
    widest cone within the budget (at first theta 0: the centre alone, which does not stretch) and the narrowest beyond
    it (the Illinois step against stagnation; STRETCH_STEPS more patches, up to STRETCH_MORE more while the widest
    within the budget stretches less than STRETCH_NEAR of it).  A trial cone whose patch is one already judged at an end
    of the bracket is moved, by bisection, to one of its own: on a coarse or lat-long mesh the patch grows in steps, and
    the cone just under a patch beyond the budget gives that patch again (the review of 2026-11-17: the patch beyond the
    budget came back).  The widest patch within the budget is the answer, never one beyond it; the centre's own patch
    when no wider one is within it (no field may fit there).  Each patch is taken with its mirror image across the
    face's mirror ``planes`` (:func:`mirror_closure`) before and after its outline is drawn clean, and the holes it
    encloses filled (:func:`fill_holes`)."""

    regions: dict = {}

    def region_at(theta: float) -> frozenset:
        found = regions.get(theta)
        if found is None:
            grown = grow_mean(mesh, graph, centre, axis, theta) if recentre else cone_grow(mesh, graph, centre, axis, theta)
            grown = mirror_closure(mesh, grown, planes)
            found = regions[theta] = frozenset(fill_holes(mesh, mirror_closure(mesh, smooth_outline(mesh, grown, theta_d_deg, centre, face), planes)))
        return found

    def between(low: float, high: float, proposal: float, high_judged: bool) -> Any:
        """A cone in (low, high) whose patch is neither low's nor (when judged) high's: the proposal; else, when the
        proposal gives high's patch, the widest cone under it that does not (OMEGA_BISECTIONS + 4 bisections for where
        high's patch begins), and when it gives low's, the narrowest over it that does not; None when there is none."""

        region = region_at(proposal)
        if not (high_judged and region == region_at(high)) and region != region_at(low):
            return proposal
        downwards = high_judged and region == region_at(high)
        a, b = (low, proposal) if downwards else (proposal, high)
        found = None
        for _ in range(OMEGA_BISECTIONS + 4):
            middle = (a + b) / 2
            if (region_at(middle) == region_at(high)) if downwards else (region_at(middle) == region_at(low)):
                b, a = (middle, a) if downwards else (b, middle)
            else:
                found = middle
                a, b = (middle, b) if downwards else (a, middle)
        if found is None or region_at(found) == region_at(low) or (high_judged and region_at(found) == region_at(high)):
            return None
        return found

    # The first guess: the widest cone whose total curvature is within 12 pi budget.
    limit = 12 * math.pi * budget
    low, high = 0.0, widest
    if total_curvature(mesh, region_at(high)) <= limit:
        low = high
    else:
        for _ in range(OMEGA_BISECTIONS):
            middle = (low + high) / 2
            if total_curvature(mesh, region_at(middle)) <= limit:
                low = middle
            else:
                high = middle
    theta = low if low > 0 else widest / (2 ** OMEGA_BISECTIONS)
    # The ends of the bracket, each with its distance from the budget (halved by the Illinois step when the other end
    # is kept twice in a row).
    within, gap_within = (0.0, 0.0), budget
    beyond, gap_beyond = None, None
    last = None
    steps = 0
    while True:
        value = stretch_of(region_at(theta))
        steps += 1
        side = "within" if value <= budget else "beyond"
        if side == "within" and theta > within[0]:
            within, gap_within = (theta, value), budget - value
        elif side == "beyond" and (beyond is None or theta < beyond[0]):
            beyond, gap_beyond = (theta, value), (value - budget if math.isfinite(value) else None)
        if side == last:
            if side == "within" and gap_beyond is not None:
                gap_beyond /= 2
            elif side == "beyond":
                gap_within /= 2
        last = side
        if steps > STRETCH_STEPS + STRETCH_MORE or (steps > STRETCH_STEPS and within[1] >= STRETCH_NEAR * budget):
            break
        if beyond is None:
            if within[0] >= widest:
                break
            # Out: theta^2 in proportion to the room left (a cap's stretch grows about as theta^2).
            factor = math.sqrt(budget / within[1]) if within[1] > 0 else STRETCH_GROWTH
            following = min(widest, within[0] * min(STRETCH_GROWTH, factor))
            top = widest
        else:
            top = beyond[0]
            if gap_beyond is None:
                following = (within[0] + top) / 2
            else:
                x0, x1 = within[0] * within[0], top * top
                following = math.sqrt(x0 + (x1 - x0) * gap_within / (gap_within + gap_beyond))
        following = between(within[0], top, following, beyond is not None)
        if following is None:
            break
        theta = following
    return set(region_at(within[0]))


def fill_holes(mesh: Mesh, region) -> set:
    """A patch that is not a disk with the holes it encloses filled: each piece of the part's other usable facets (across
    edges) that the patch surrounds, smaller than the patch and off the mesh's own open edges (beyond a patch's outer edge
    lies the rest of a closed part, larger, or an open mesh's edge).  The review of 2026-11-17 (finding 1): two slivers
    on the Dex3-1's mirror plane by its tip end (left out of the face as bent tighter than 4 mm, by their width alone)
    made a click's patch a ring, which its chart opened along a seam on one side (a slit, lopsided); a LEAP Hand click's
    ring did the same (its chart refused, finding 6).  A hole the mesh has no facets in stays (the patch is then judged
    beyond any limit: :func:`stretch_region`)."""

    from . import chart as chart_module

    region = set(region)
    if not region or chart_module.patch_topology(mesh, region)["disk"]:
        return region
    limit = math.fsum(mesh.areas[f] for f in sorted(region))
    cache = mesh.__dict__.setdefault("_open_vertices", [])
    if not cache:
        cache.append(frozenset(v for edge in mesh.boundary_edges for v in edge))
    edge_vertices = cache[0]
    outside: set = set()  # facets of pieces that are not holes
    filled = set(region)
    for facet in sorted(region):
        for start in mesh.neighbors[facet]:
            if start in filled or start in outside or not mesh.usable(start):
                continue
            piece, queue, area, enclosed = {start}, [start], mesh.areas[start], True
            while queue and enclosed:
                f = queue.pop()
                if any(v in edge_vertices for v in mesh.facets[f]):
                    enclosed = False
                    break
                for g in mesh.neighbors[f]:
                    if g in region or g in piece:
                        continue
                    if g in outside or not mesh.usable(g):
                        enclosed = False
                        break
                    piece.add(g)
                    queue.append(g)
                    area += mesh.areas[g]
                if area >= limit:
                    enclosed = False
            if enclosed:
                filled |= piece
            else:
                outside |= piece
    return filled


def total_curvature(mesh: Mesh, region) -> float:
    """The area of the region's Gauss image: the sum of |angle defect| over its interior vertices (every facet round them
    selected), the defects smoothed CURVATURE_PASSES times within those vertices first.

    Each pass keeps half of a vertex's defect and shares half among its interior neighbours (the total is kept), so the
    defects of alternating sign that an irregular triangulation of a developable surface leaves cancel over about as many
    edges, and smooth curvature stays.  Only the region's own vertices take part: a sharp corner of the part beyond the
    region's edge adds nothing (the Franka Hand's pad, 0.0002 sr, not the 0.76 sr its box's corners would bring)."""

    cache = mesh.__dict__.setdefault("_vertex_curvature", {})
    if not cache:
        around: dict = {}
        angles: dict = {}
        for f in range(mesh.facet_count):
            if not mesh.usable(f):
                continue
            points = mesh.facet_points(f)
            for k, v in enumerate(mesh.facets[f]):
                around.setdefault(v, []).append(f)
                a, b, c = points[k], points[(k + 1) % 3], points[(k + 2) % 3]
                u, w = sub(b, a), sub(c, a)
                lu, lw = norm(u), norm(w)
                if lu > 0 and lw > 0:
                    angles[v] = angles.get(v, 0.0) + math.acos(max(-1.0, min(1.0, dot(u, w) / (lu * lw))))
        # A vertex on the mesh's own boundary (an edge at it with one facet) has no angle defect to speak of.
        edge_count: dict = {}
        for v, facets in around.items():
            for f in facets:
                for w in mesh.facets[f]:
                    if w != v:
                        edge_count[(v, w)] = edge_count.get((v, w), 0) + 1
        closed = {v: all(edge_count[(v, w)] == 2 for f in around[v] for w in mesh.facets[f] if w != v) for v in around}
        cache["around"] = around
        cache["defect"] = {v: 2 * math.pi - angles.get(v, 0.0) for v in around if closed[v]}
        cache["neighbours"] = {v: sorted({w for f in around[v] for w in mesh.facets[f] if w != v}) for v in around}
    around, defect, neighbours = cache["around"], cache["defect"], cache["neighbours"]
    inside = set(region)
    interior = sorted(v for v in {v for f in inside for v in mesh.facets[f]} if v in defect and all(f in inside for f in around[v]))
    members = set(interior)
    links = {v: [w for w in neighbours[v] if w in members] for v in interior}
    values = {v: defect[v] for v in interior}
    for _ in range(CURVATURE_PASSES):
        spread = {v: (values[v] / 2 if links[v] else values[v]) for v in interior}
        for v in interior:
            if links[v]:
                share = values[v] / 2 / len(links[v])
                for w in links[v]:
                    spread[w] += share
        values = spread
    return math.fsum(abs(values[v]) for v in interior)


def smooth_outline(mesh: Mesh, region, theta_d_deg: float, keep: int, allowed=None) -> set:
    """The outline drawn clean: the region filled to its convex outline (:func:`convex_fill`), its notches filled (a facet
    of ``allowed`` with two selected neighbours across edges of at most ``theta_d``) and its teeth cut (a facet with one
    selected neighbour, ``keep`` never), then its holes filled and its largest piece kept."""

    cos_d = math.cos(math.radians(min(max(theta_d_deg, 0.0), 180.0)))
    region = convex_fill(mesh, region, cos_d, allowed)
    for _ in range(SMOOTH_OUTLINE_PASSES):
        notches = set()
        for f in sorted(region):
            for g in mesh.neighbors[f]:
                if g in region or g in notches or not mesh.usable(g) or (allowed is not None and g not in allowed):
                    continue
                inside = [h for h in mesh.neighbors[g] if h in region]
                if len(inside) >= 2 and all(dot(mesh.normals[g], mesh.normals[h]) >= cos_d for h in inside):
                    notches.add(g)
        region |= notches
        teeth = {f for f in region if f != keep and sum(1 for h in mesh.neighbors[f] if h in region) <= 1}
        region -= teeth
        if not notches and not teeth:
            break
    if not region:
        return region
    region = cleanup(mesh, region, math.inf)
    return region if allowed is None else region & set(allowed)


def convex_fill(mesh: Mesh, region, cos_d: float, allowed=None) -> set:
    """The region and the facets of ``allowed`` (connected to it across edges of at most theta_d, cos_d its cosine) whose
    centroids lie within its convex outline, seen along its mean normal: a cone of normals cuts a staircase across a CAD
    exporter's long strips (the Dex3-1's hull: the steps of the outline of 2026-11-17), filled to the line the iso-line
    of the cone follows.  Only a region whose facets all face within CONVEX_FILL_DEG of its mean normal (a patch a sheet
    covers, seen without folds) is filled; the outline is the convex hull of its vertices, computed once."""

    region = set(region)
    axis = _mean_normal(mesh, region) if region else None
    limit = math.cos(math.radians(CONVEX_FILL_DEG))
    if axis is None or any(dot(mesh.normals[f], axis) < limit for f in region):
        return region
    # A frame of the plane across the axis (the coordinate axis least along it, crossed with it).
    k = min(range(3), key=lambda i: (abs(axis[i]), i))
    pick = tuple(1.0 if i == k else 0.0 for i in range(3))
    first = _unit(_cross(axis, pick))
    second = _cross(axis, first)

    def seen(point) -> tuple:
        return (dot(point, first), dot(point, second))

    hull = _hull(sorted({seen(mesh.vertices[v]) for f in region for v in mesh.facets[f]}))
    if len(hull) < 3:
        return region
    queue = sorted(region)
    while queue:
        facet = queue.pop()
        for other in mesh.neighbors[facet]:
            if other in region or not mesh.usable(other) or (allowed is not None and other not in allowed):
                continue
            if dot(mesh.normals[facet], mesh.normals[other]) < cos_d or dot(mesh.normals[other], axis) < limit:
                continue
            if _inside_convex(hull, seen(mesh.centroids[other])):
                region.add(other)
                queue.append(other)
    return region


def _cross(a, b) -> tuple:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a) -> tuple:
    length = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    return (a[0] / length, a[1] / length, a[2] / length)


def _hull(points: Sequence) -> list:
    """The convex hull of sorted 2D points, counter-clockwise (Andrew's monotone chain), collinear points left out."""

    def turn(o, a, b) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    for p in points:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in reversed(points):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _inside_convex(hull: Sequence, point) -> bool:
    """Whether a point lies within a counter-clockwise convex polygon (on its edge counts)."""

    n = len(hull)
    for i in range(n):
        a, b = hull[i], hull[(i + 1) % n]
        if (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0]) < 0:
            return False
    return True


def _mean_normal(mesh: Mesh, region) -> Any:
    ordered = sorted(region)
    total = [math.fsum(mesh.normals[f][k] * mesh.areas[f] for f in ordered) for k in range(3)]
    length = math.sqrt(total[0] * total[0] + total[1] * total[1] + total[2] * total[2])
    return None if length == 0 else (total[0] / length, total[1] / length, total[2] / length)


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


def click_face(mesh: Mesh, operations: Any) -> Any:
    """The face a selection of one grow (a click) grows on: its seed's region at every normal (the stretch selection's
    face, :func:`stretch_region`), or None for any other selection."""

    if not isinstance(operations, (list, tuple)) or len(operations) != 1:
        return None
    op = _operation(operations[0], 0)
    if op["op"] != "grow" or op["mode"] != "add":
        return None
    return grow(mesh, op["seed_facet"], op["theta_d_deg"], 180.0, op["min_radius_mm"])


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
        if kind == "grow" and op.get("stretch") == "always":
            part = stretch_region(mesh, op["seed_facet"], op["theta_d_deg"], op["theta_c_deg"], op["min_radius_mm"], op["stretch_budget"])
        elif kind == "grow":
            part = grow(mesh, op["seed_facet"], op["theta_d_deg"], op["theta_c_deg"], op["min_radius_mm"])
            if op.get("stretch") == "curved" and doubly_curved(mesh, part):
                part = stretch_region(mesh, op["seed_facet"], op["theta_d_deg"], min(op["theta_c_deg"], 90.0), op["min_radius_mm"],
                                      op["stretch_budget"], face=part)
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
        "grow": {"op", "mode", "seed_facet", "theta_d_deg", "theta_c_deg", "min_radius_mm", "preset", "stretch_budget"},
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
        # By stretch: always with preset stretch (its budget unless named), else only when named and the region grown is
        # doubly curved (absent otherwise, so every other grow is the one of before).
        budget = raw.get("stretch_budget", preset.get("stretch_budget"))
        if budget is not None:
            op["stretch_budget"] = _number(budget, f"{where}.stretch_budget", 1e-4, 0.2)
            op["stretch"] = "always" if "stretch_budget" in preset else "curved"
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
