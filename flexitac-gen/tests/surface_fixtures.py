"""Synthetic meshes for the CAD-mode tests (no STL file is needed in the repository).

The soft-finger replica reproduces the contact face of
``asset/soft_gripper_finger.stl``: a 25.8 mm wide extrusion whose x = 0 face
runs 119.365 mm from an R3 base fillet to an R1 tip round, in millimetres.
"""

from __future__ import annotations

import math
from typing import Sequence

from surface.mesh import binary_stl, mesh_from_triangles


def box(size=(10.0, 20.0, 5.0), origin=(0.0, 0.0, 0.0)) -> list:
    x0, y0, z0 = origin
    x1, y1, z1 = x0 + size[0], y0 + size[1], z0 + size[2]
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    triangles = []
    for a, b, c, d in quads:
        triangles.append((p[a], p[b], p[c]))
        triangles.append((p[a], p[c], p[d]))
    return triangles


def extrude(profile_xz: Sequence[Sequence[float]], width: float) -> list:
    """A prism: the convex profile (x, z), counter-clockwise seen from +y, extruded from y = 0 to y = -width."""

    n = len(profile_xz)
    front = [(x, 0.0, z) for x, z in profile_xz]
    back = [(x, -width, z) for x, z in profile_xz]
    triangles = []
    for i in range(n):
        j = (i + 1) % n
        # Side quad, outward for a counter-clockwise profile seen from +y.
        triangles.append((front[i], back[i], back[j]))
        triangles.append((front[i], back[j], front[j]))
    for i in range(1, n - 1):
        triangles.append((front[0], front[i], front[i + 1]))
        triangles.append((back[0], back[i + 1], back[i]))
    return triangles


def soft_finger_profile(fillet_segments: int = 15, tip_segments: int = 8) -> list:
    """Convex x-z profile with the replica's contact face at x = 0 (z from -3 to -122.365)."""

    points = []
    # R3 base fillet centred (3, -3): from (0, -3) up to (3, 0).
    for k in range(fillet_segments + 1):
        angle = math.pi - (math.pi / 2) * k / fillet_segments
        points.append((3 + 3 * math.cos(angle), -3 + 3 * math.sin(angle)))
    points.append((37.0, 0.0))
    points.append((40.0, -3.0))
    # Back wall to the R1 tip round centred (1, -122.365).
    tip_start = -math.radians(30)
    for k in range(tip_segments + 1):
        angle = tip_start - (math.pi / 2 + math.radians(60)) * k / tip_segments
        points.append((1 + math.cos(angle), -122.365 + math.sin(angle)))
    points.append((0.0, -122.365))
    return points


def soft_finger_replica() -> list:
    return extrude(soft_finger_profile(), 25.8)


def sphere_cap(radius: float, cap_deg: float, rings: int = 8, segments: int = 24) -> list:
    def point(theta: float, phi: float) -> tuple:
        return (radius * math.sin(theta) * math.cos(phi), radius * math.sin(theta) * math.sin(phi), radius * math.cos(theta))

    limit = math.radians(cap_deg)
    triangles = []
    for i in range(rings):
        t0, t1 = limit * i / rings, limit * (i + 1) / rings
        for j in range(segments):
            # The last segment ends on the first one's angle exactly, so the seam welds
            # (2 pi itself gives sin = -2.4e-16, a different float32 vertex: a slit cap).
            p0, p1 = 2 * math.pi * j / segments, 2 * math.pi * ((j + 1) % segments) / segments
            a, b, c, d = point(t0, p0), point(t0, p1), point(t1, p0), point(t1, p1)
            if i == 0:
                triangles.append((a, c, d))
            else:
                triangles.append((a, c, d))
                triangles.append((a, d, b))
    return triangles


def cylinder_band(radius: float, height: float, segments: int = 24, closed: bool = True, sweep_deg: float = 360.0) -> list:
    """An open cylinder band (outward normals); ``closed`` wraps all the way round."""

    sweep = 2 * math.pi if closed else math.radians(sweep_deg)
    count = segments if closed else segments + 1
    ring = [(radius * math.cos(sweep * j / segments), radius * math.sin(sweep * j / segments)) for j in range(count)]
    triangles = []
    for j in range(segments):
        # A closed band reuses its first points at the seam, so the seam welds.
        (x0, y0), (x1, y1) = ring[j], ring[(j + 1) % len(ring)]
        a, b = (x0, y0, 0.0), (x1, y1, 0.0)
        c, d = (x0, y0, height), (x1, y1, height)
        triangles.append((a, b, d))
        triangles.append((a, d, c))
    return triangles


def mesh(triangles, unit: str = "mm", name: str = "synthetic"):
    return mesh_from_triangles(triangles, unit=unit, name=name)


def stl_bytes(triangles, scale: float = 1.0) -> bytes:
    scaled = [tuple(tuple(c * scale for c in p) for p in t) for t in triangles]
    return binary_stl(scaled)


def ascii_stl(triangles) -> bytes:
    lines = ["solid synthetic"]
    for a, b, c in triangles:
        lines += ["facet normal 0 0 0", "outer loop"]
        lines += [f"vertex {p[0]!r} {p[1]!r} {p[2]!r}" for p in (a, b, c)]
        lines += ["endloop", "endfacet"]
    lines.append("endsolid synthetic")
    return "\n".join(lines).encode("ascii")


def plate(outline_xy: Sequence[Sequence[float]], thickness: float = 3.0) -> list:
    """A prism whose convex top face (z = thickness) has the given outline (fan triangulated)."""

    n = len(outline_xy)
    top = [(x, y, thickness) for x, y in outline_xy]
    bottom = [(x, y, 0.0) for x, y in outline_xy]
    cx = sum(p[0] for p in outline_xy) / n
    cy = sum(p[1] for p in outline_xy) / n
    centre_top, centre_bottom = (cx, cy, thickness), (cx, cy, 0.0)
    triangles = []
    for i in range(n):
        j = (i + 1) % n
        triangles.append((centre_top, top[i], top[j]))
        triangles.append((centre_bottom, bottom[j], bottom[i]))
        triangles.append((bottom[i], bottom[j], top[j]))
        triangles.append((bottom[i], top[j], top[i]))
    return triangles


def ellipse_outline(a: float, b: float, segments: int = 72) -> list:
    return [(a * math.cos(2 * math.pi * k / segments), b * math.sin(2 * math.pi * k / segments)) for k in range(segments)]


def reversed_winding(triangles) -> list:
    """The same surface with every facet wound the other way (an inside-out export)."""

    return [(a, c, b) for a, b, c in triangles]


def t_junction_box(size=(30.0, 40.0, 10.0)) -> list:
    """A box whose top face has a T-junction: one half split at the middle of the shared diagonal."""

    triangles = box(size)
    x, y, z = size
    p00, p10, p11, p01 = (0.0, 0.0, z), (x, 0.0, z), (x, y, z), (0.0, y, z)
    middle = (x / 2, y / 2, z)
    # box() gives the top quad (4, 5, 6, 7) as triangles 2 and 3.
    return triangles[:2] + [(p00, p10, p11), (p00, middle, p01), (middle, p11, p01)] + triangles[4:]


def holed_plate(size=(60.0, 40.0), hole=((28.0, 18.0), (32.0, 22.0)), thickness=3.0) -> list:
    """A plate with one square through-hole; the top face (z = thickness) is a flat annulus."""

    (x0, y0), (x1, y1) = (0.0, 0.0), size
    (h0x, h0y), (h1x, h1y) = hole
    outer = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    inner = [(h0x, h0y), (h1x, h0y), (h1x, h1y), (h0x, h1y)]
    triangles = []
    for z, up in ((thickness, True), (0.0, False)):
        for i in range(4):
            j = (i + 1) % 4
            a, b = (*outer[i], z), (*outer[j], z)
            c, d = (*inner[j], z), (*inner[i], z)
            quad = [(a, b, c), (a, c, d)]
            triangles += quad if up else [(p, r, q) for p, q, r in quad]
    for loop, outward in ((outer, True), (inner, False)):
        for i in range(4):
            j = (i + 1) % 4
            a, b = (*loop[i], 0.0), (*loop[j], 0.0)
            c, d = (*loop[j], thickness), (*loop[i], thickness)
            quad = [(a, b, c), (a, c, d)]
            triangles += quad if outward else [(p, r, q) for p, q, r in quad]
    return triangles


def cylinder_sheet(radius: float, height: float, segments: int, rows: int, sweep_deg: float, skip=()) -> list:
    """An open cylindrical sheet (outward normals), with the grid cells in ``skip`` left out (holes)."""

    def point(i: int, k: int) -> tuple:
        angle = math.radians(sweep_deg) * i / segments
        return (radius * math.cos(angle), radius * math.sin(angle), height * k / rows)

    triangles = []
    for i in range(segments):
        for k in range(rows):
            if (i, k) in skip:
                continue
            a, b, c, d = point(i, k), point(i + 1, k), point(i + 1, k + 1), point(i, k + 1)
            triangles += [(a, b, c), (a, c, d)]
    return triangles


def with_t_junction(triangles, index: int) -> list:
    """Split the neighbour across the first edge of triangle ``index`` at the edge's midpoint.

    Triangle ``index`` keeps its edge whole, so the midpoint becomes a
    T-junction on it (as in many CAD exports).
    """

    a, b, _ = triangles[index]
    middle = tuple((p + q) / 2 for p, q in zip(a, b))
    result = []
    for k, triangle in enumerate(triangles):
        if k != index and a in triangle and b in triangle:
            i = triangle.index(a)
            j = triangle.index(b)
            w = next(p for p in triangle if p != a and p != b)
            # Keep the winding: walk the triangle from the edge's first vertex.
            x, y = (a, b) if (j - i) % 3 == 1 else (b, a)
            result += [(x, middle, w), (middle, y, w)]
        else:
            result.append(triangle)
    return result


def round_holed_plate(size=(60.0, 40.0), centre=(30.0, 20.0), radius=6.0, segments=48, thickness=3.0) -> list:
    """A plate with one round through-hole; the top face (z = thickness) is a flat annulus.

    The outline is sampled on the rays from the hole's centre at the circle's angles and the rectangle's corners,
    so the annulus is quads between the two loops.
    """

    width, height = size
    cx, cy = centre
    angles = {round(2 * math.pi * k / segments, 12) for k in range(segments)}
    for x, y in ((width, height), (0.0, height), (0.0, 0.0), (width, 0.0)):
        angles.add(round(math.atan2(y - cy, x - cx) % (2 * math.pi), 12))
    outer, inner = [], []
    for angle in sorted(angles):
        dx, dy = math.cos(angle), math.sin(angle)
        reach = []
        if dx > 1e-12:
            reach.append((width - cx) / dx)
        if dx < -1e-12:
            reach.append(-cx / dx)
        if dy > 1e-12:
            reach.append((height - cy) / dy)
        if dy < -1e-12:
            reach.append(-cy / dy)
        outer.append((cx + min(reach) * dx, cy + min(reach) * dy))
        inner.append((cx + radius * dx, cy + radius * dy))
    count = len(outer)
    triangles = []
    for z, up in ((thickness, True), (0.0, False)):
        for i in range(count):
            j = (i + 1) % count
            a, b = (*outer[i], z), (*outer[j], z)
            c, d = (*inner[j], z), (*inner[i], z)
            quad = [(a, b, c), (a, c, d)]
            triangles += quad if up else [(p, r, q) for p, q, r in quad]
    for loop, outward in ((outer, True), (inner, False)):
        for i in range(count):
            j = (i + 1) % count
            a, b = (*loop[i], 0.0), (*loop[j], 0.0)
            c, d = (*loop[j], thickness), (*loop[i], thickness)
            quad = [(a, b, c), (a, c, d)]
            triangles += quad if outward else [(p, r, q) for p, q, r in quad]
    return triangles


def filleted_bracket(radius: float, segments: int, panel=40.0, flange=30.0, width=40.0, strips=8) -> list:
    """An open sheet: a flat panel (z = 0, x from 0 to ``panel``) that turns down by 90 degrees over a fillet of
    ``radius`` (``segments`` facets around) into a flange ``flange`` long; ``strips`` strips across its width."""

    profile = [(0.0, 0.0), (panel, 0.0)]
    for k in range(1, segments + 1):
        turn = math.radians(90.0) * k / segments
        profile.append((panel + radius * math.sin(turn), -radius + radius * math.cos(turn)))
    end_x, end_z = profile[-1]
    profile.append((end_x, end_z - flange))
    ys = [width * j / strips for j in range(strips + 1)]
    triangles = []
    for (x0, z0), (x1, z1) in zip(profile, profile[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            a, b, c, d = (x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0)
            triangles += [(a, b, c), (a, c, d)]
    return triangles
