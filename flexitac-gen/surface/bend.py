"""How tightly the surface bends at each mesh edge: one model for selection, fit and map.

A flat sheet laid on a tessellated surface bends at the edges between
facets.  Two cases are told apart:

- **A smooth bend** (a fillet or a cylinder tessellated into strips): the
  surface turns by the edge's dihedral angle over the strip width, so the
  local radius is the narrower strip's width across the edge divided by the
  angle.  This holds for any tessellation density: a fine one has small
  angles over narrow strips.  A strip's width is that of the flat piece
  (coplanar facets) at the edge, so a strip split at a T-junction or into
  slivers keeps its width.
- **A crease** (an edge between two facets that are flat on both sides):
  a sheet bent at its own minimum radius ``R`` around a crease of angle
  ``theta`` lifts off the corner by about ``R * theta**2 / 8``.  An edge
  whose lift-off exceeds ``CREASE_LIFT_OFF_MM`` counts as radius 0, so it
  blocks a sheet of that radius: 16.7 degrees for the 4.7 mm field stack,
  34 degrees for a single 0.11 mm FPC.  The crank pad's 1.74 and 3.6 degree
  steps and a 30-segment cylinder's 12 degree edges stay passable.

The per-edge geometry is cached on the mesh (bounded by its edge count);
the thresholds are applied per call.
"""

from __future__ import annotations

import math

from .mesh import Mesh, cross, dot, norm, sub

CREASE_LIFT_OFF_MM = 0.05
# The bend at an edge belongs to the narrower facet: a facet wider than this
# ratio times its neighbour is a flat face next to a blend, not a blend.
STRIP_RATIO = 1.5
# Facets of one strip (the two triangles of a quad) share its radius.
PARTNER_DEG = 0.1
# The flat piece measured at an edge (see _piece_width) holds at most this many facets.
PIECE_FACETS = 64


def edge_geometry(mesh: Mesh, f: int, g: int):
    """(angle in rad, width of f, width of g, (vertex a, vertex b)) for neighbours f and g, or None.

    The widths are those of the flat pieces of f and g across the shared
    edge (:func:`_piece_width`).  Facets linked across a T-junction share the
    overlapping part of their two edges.
    """

    key = (f, g) if f < g else (g, f)
    cache = mesh.bend_cache
    if key in cache:
        found = cache[key]
    else:
        found = _measure(mesh, key[0], key[1])
        cache[key] = found
    if found is None or f < g:
        return found
    angle, width_low, width_high, shared = found
    return angle, width_high, width_low, shared


def _measure(mesh: Mesh, f: int, g: int):
    shared = [v for v in mesh.facets[f] if v in mesh.facets[g]]
    if len(shared) == 2:
        a, b = shared
        length = norm(sub(mesh.vertices[a], mesh.vertices[b]))
        if length == 0:
            return None
        width_f = 2 * mesh.areas[f] / length
        width_g = 2 * mesh.areas[g] / length
    else:
        link = mesh.cracks.get((f, g))
        if link is None:
            return None
        (s, e), (s2, e2) = link
        origin = mesh.vertices[s]
        direction = sub(mesh.vertices[e], origin)
        span = dot(direction, direction)
        if span == 0:
            return None
        along = sorted((dot(sub(mesh.vertices[v], origin), direction) / span, v) for v in (s, e, s2, e2))
        a, b = along[1][1], along[2][1]
        if a == b:
            return None
        width_f = 2 * mesh.areas[f] / norm(sub(mesh.vertices[e], mesh.vertices[s]))
        width_g = 2 * mesh.areas[g] / norm(sub(mesh.vertices[e2], mesh.vertices[s2]))
    angle = math.acos(max(-1.0, min(1.0, dot(mesh.normals[f], mesh.normals[g]))))
    if angle > 0:
        width_f = _piece_width(mesh, f, a, b, width_f, angle)
        width_g = _piece_width(mesh, g, a, b, width_g, angle)
    return angle, width_f, width_g, (a, b)


def _piece_width(mesh: Mesh, facet: int, a: int, b: int, width: float, angle: float) -> float:
    """The width across the edge ab of the flat piece that ``facet`` belongs to.

    The piece is the facets coplanar with ``facet`` (within half the edge's
    angle and PARTNER_DEG) that reach the edge's end points through each
    other; its width is its farthest vertex from the edge's line on the
    facet's side.  A strip triangle split at a T-junction or into slivers is
    narrower than its strip, which sets the bend radius.
    """

    pa = mesh.vertices[a]
    axis = sub(mesh.vertices[b], pa)
    length = norm(axis)
    if length == 0:
        return width
    across = cross(mesh.normals[facet], axis)
    # Towards the facet: the side of its vertex farthest from the line.
    side = max((dot(sub(mesh.vertices[v], pa), across) for v in mesh.facets[facet]), key=abs)
    if side == 0:
        return width
    sign = 1.0 if side > 0 else -1.0
    limit = math.cos(min(math.radians(PARTNER_DEG), angle / 2))
    normal = mesh.normals[facet]
    piece = {facet}
    queue = [facet]
    while queue and len(piece) < PIECE_FACETS:
        current = queue.pop(0)
        for other in mesh.neighbors[current]:
            if other in piece or dot(mesh.normals[other], normal) < limit:
                continue
            if a not in mesh.facets[other] and b not in mesh.facets[other]:
                continue
            piece.add(other)
            queue.append(other)
    best = width
    for member in sorted(piece):
        for v in mesh.facets[member]:
            best = max(best, sign * dot(sub(mesh.vertices[v], pa), across) / length)
    return best


def is_crease(angle: float, min_radius_mm: float) -> bool:
    """True when a sheet of ``min_radius_mm`` cannot follow a crease of ``angle`` (rad)."""

    return min_radius_mm * angle * angle / 8 > CREASE_LIFT_OFF_MM


def edge_radius(mesh: Mesh, f: int, g: int, min_radius_mm: float) -> float:
    """The bend radius a sheet of ``min_radius_mm`` meets at the edge between f and g (0 at a crease)."""

    found = edge_geometry(mesh, f, g)
    if found is None:
        return math.inf
    angle, width_f, width_g, _ = found
    if angle <= 0:
        return math.inf
    if is_crease(angle, min_radius_mm):
        return 0.0
    return min(width_f, width_g) / angle


def facet_radius(mesh: Mesh, facet: int, min_radius_mm: float, cos_feature: float = -1.0) -> float:
    """The tightest smooth bend at the facet (creases and feature edges excluded).

    The facet takes the bends at its edges where it is the narrower side
    (within ``STRIP_RATIO``), and those of its coplanar partners.
    """

    smallest = _own_radius(mesh, facet, min_radius_mm, cos_feature)
    partner = math.cos(math.radians(PARTNER_DEG))
    for other in mesh.neighbors[facet]:
        if dot(mesh.normals[facet], mesh.normals[other]) >= partner:
            smallest = min(smallest, _own_radius(mesh, other, min_radius_mm, cos_feature))
    return smallest


def _own_radius(mesh: Mesh, facet: int, min_radius_mm: float, cos_feature: float) -> float:
    smallest = math.inf
    for other in mesh.neighbors[facet]:
        found = edge_geometry(mesh, facet, other)
        if found is None:
            continue
        angle, own, neighbour, _ = found
        if angle <= 0 or math.cos(angle) < cos_feature or is_crease(angle, min_radius_mm):
            continue
        if own > STRIP_RATIO * neighbour:
            continue
        smallest = min(smallest, min(own, neighbour) / angle)
    return smallest
