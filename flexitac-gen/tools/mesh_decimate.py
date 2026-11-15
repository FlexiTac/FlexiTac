#!/usr/bin/env python3
"""Decimate a triangle mesh with quadric error metrics: the standard library only, the same bytes on every run.

The Library's showcase (tools/library_showcase.py) ships a vendor's model decimated to within 0.1 mm; this module is
the decimation and the proof of that number.  It needs nothing outside the standard library and gives the same bytes
on every run, host and Python (3.9 and later):

- weld(): the corners of a binary STL's triangles merged where their coordinates agree to 0.0001 mm (the integers
  round(x * 10000)), numbered in the file's order, each standing where the first of its corners stood; a triangle
  left with two corners in one place is dropped.
- collapses(): Garland and Heckbert's quadrics (one plane quadric a face, summed at its three corners, unweighted,
  so a cost is a sum of squared distances in mm^2) with half-edge collapses: a vertex moves onto a neighbour, which
  stays where it is, so every vertex of the result is a vertex of the input bit for bit (no solve, no new float).
  The cheapest collapse first (heapq over (cost, the vertex that goes, the vertex that stays, their stamps): the ties
  fall to the vertex numbers, the file's order).  A collapse is made only if its cost is at most the tolerance
  squared, its edge lies between exactly two faces and keeps the surface's topology (the link condition), the vertex
  that goes is on no open or non-manifold edge (a cut's border stays as it is) and no face it leaves turns more than
  15 degrees from the normal it had in the input, or to nothing.
- deviation(): the two-way distance between two surfaces, measured: the exact distance to the other surface's
  nearest triangle (Ericson's closest point; a grid of cells holds the triangles near each) from every vertex,
  every edge's middle, every triangle's centre and a barycentric grid about 0.5 mm apart on each larger triangle
  (at most 32 steps a side), of each surface in turn; infinite beyond the bound it is asked for.
- decimate(): the collapses as far as they go, then the gate: the deviation of the result is measured both ways and,
  where it exceeds the tolerance, the longest prefix of the collapse sequence within it is kept (bisection), as
  tools/library_scenes.py gates its own bodies.  The report holds the measured numbers.
- stl_bytes(): a binary STL, each normal a unit vector from its corners, under a header of at most 80 bytes.

The arithmetic is IEEE double addition, multiplication, division and square root in a fixed order (no sum(), no
library sine: the 15 degrees are their cosine written out; no ** either: a float's power is the C library's pow(),
which is not x * x on every host), and no result depends on a set's or a dictionary's order (what is iterated in an
order that matters is sorted).  tests/test_mesh_decimate.py pins the bytes of small fixtures.

    python3 tools/mesh_decimate.py in.stl out.stl --tolerance 0.1 [--header TEXT]
"""

from __future__ import annotations

import argparse
import heapq
import math
import struct
import sys
from pathlib import Path

# The corners merged where round(coordinate * WELD_SCALE) agree (0.0001 mm).
WELD_SCALE = 10000.0
# cos(15 degrees): a face a collapse leaves faces within 15 degrees of its input normal.
TURN_COSINE = 0.9659258262890683
# The deviation's probes: a barycentric grid about this far apart on each triangle longer than it, PROBE_STEPS at most.
PROBE_SPACING_MM = 0.5
PROBE_STEPS = 32
# The deviation is measured up to this many tolerances (beyond: infinite).
BOUND_TOLERANCES = 4.0


class MeshError(Exception):
    pass


# -- binary STL -----------------------------------------------------------------------------------------------------

def read_stl(data: bytes) -> list:
    """The triangles of a binary STL, [(x0, y0, z0, x1, y1, z1, x2, y2, z2)] as its float32 coordinates."""

    if len(data) < 84:
        raise MeshError("not a binary STL (shorter than its header)")
    (count,) = struct.unpack_from("<I", data, 80)
    if len(data) != 84 + 50 * count:
        raise MeshError("not a binary STL (its length is not 84 + 50 bytes a facet)")
    return [record[3:12] for record in struct.iter_unpack("<12fH", data[84:])]


def unit_normal(a, b, c) -> tuple:
    """(nx, ny, nz, length): the unit normal of the triangle a, b, c and its cross product's length (twice its area);
    zeros for a triangle of no area."""

    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length <= 1e-12:
        return (0.0, 0.0, 0.0, 0.0)
    return (nx / length, ny / length, nz / length, length)


def stl_bytes(triangles: list, header: bytes) -> bytes:
    """A binary STL of ``triangles`` (9 floats each): float32 corners, each normal the unit normal of its corners,
    attribute 0, under ``header`` (at most 80 bytes, padded with spaces)."""

    if len(header) > 80:
        raise MeshError(f"an STL header of {len(header)} bytes: {header!r}")
    out = bytearray(header.ljust(80, b" "))
    out += struct.pack("<I", len(triangles))
    pack = struct.Struct("<12fH").pack
    for t in triangles:
        nx, ny, nz, _ = unit_normal(t[0:3], t[3:6], t[6:9])
        out += pack(nx, ny, nz, *t, 0)
    return bytes(out)


# -- the mesh -------------------------------------------------------------------------------------------------------

def weld(triangles: list, scale=WELD_SCALE) -> tuple:
    """(positions, faces): the triangles' corners merged where their coordinates times ``scale`` round to the same
    integers (``scale`` None: where they are the same floats), numbered in the file's order, each at its first
    corner's coordinates; faces [a, b, c] of vertex numbers in the file's order, without those left with two corners
    in one place."""

    index, positions, faces = {}, [], []
    for t in triangles:
        face = []
        for k in (0, 3, 6):
            point = (t[k], t[k + 1], t[k + 2])
            key = point if scale is None else (round(point[0] * scale), round(point[1] * scale), round(point[2] * scale))
            number = index.get(key)
            if number is None:
                number = index[key] = len(positions)
                positions.append(point)
            face.append(number)
        if face[0] != face[1] and face[1] != face[2] and face[0] != face[2]:
            faces.append(face)
    return positions, faces


def triangles_of(positions: list, faces: list) -> list:
    """The faces as triangles of 9 floats."""

    return [positions[a] + positions[b] + positions[c] for a, b, c in faces]


def components(faces: list, pairs: bool = False) -> list:
    """The faces' connected components, [[face number, ...]] each in rising order, in the order of their first faces:
    two faces are connected where they share an edge (two that only touch at a vertex are not); with ``pairs``, only
    through an edge that exactly two faces share (two solids glued along an edge or a face stay apart)."""

    parent = list(range(len(faces)))

    def root(k: int) -> int:
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    owners = {}
    for number, (a, b, c) in enumerate(faces):
        for i, j in ((a, b), (b, c), (c, a)):
            owners.setdefault((i, j) if i < j else (j, i), []).append(number)
    for key in sorted(owners):
        held = owners[key]
        if pairs and len(held) != 2:
            continue
        for number in held[1:]:
            one, two = root(held[0]), root(number)
            if one != two:
                parent[max(one, two)] = min(one, two)
    groups = {}
    for number in range(len(faces)):
        groups.setdefault(root(number), []).append(number)
    return [groups[key] for key in sorted(groups)]


# -- the collapses ---------------------------------------------------------------------------------------------------

def collapses(positions: list, faces: list, tolerance: float) -> list:
    """The collapse sequence [(gone, kept)] of the mesh (weld()'s), the cheapest first: vertex ``gone`` moves onto its
    neighbour ``kept`` (the module's docstring has the conditions).  The mesh itself is not changed: replay() applies
    a prefix of the sequence."""

    count = len(positions)
    faces = [list(face) for face in faces]
    around = [set() for _ in range(count)]
    quadric = [[0.0] * 10 for _ in range(count)]
    normals, edges = [], {}
    for number, (a, b, c) in enumerate(faces):
        nx, ny, nz, length = unit_normal(positions[a], positions[b], positions[c])
        normals.append((nx, ny, nz))
        for v in (a, b, c):
            around[v].add(number)
        for i, j in ((a, b), (b, c), (c, a)):
            key = (i, j) if i < j else (j, i)
            edges[key] = edges.get(key, 0) + 1
        if length == 0.0:
            continue
        p = positions[a]
        d = -(nx * p[0] + ny * p[1] + nz * p[2])
        q = (nx * nx, nx * ny, nx * nz, nx * d, ny * ny, ny * nz, ny * d, nz * nz, nz * d, d * d)
        for v in (a, b, c):
            held = quadric[v]
            for k in range(10):
                held[k] += q[k]
    # A vertex on an open or non-manifold edge never goes (a neighbour may still come onto it).
    locked = [False] * count
    for (i, j), owners in edges.items():
        if owners != 2:
            locked[i] = locked[j] = True
    alive = [True] * count
    stamp = [0] * count
    limit = tolerance * tolerance

    def cost(kept: int, gone: int) -> float:
        one, two = quadric[kept], quadric[gone]
        x, y, z = positions[kept]
        q = [one[k] + two[k] for k in range(10)]
        return (q[0] * x * x + 2 * q[1] * x * y + 2 * q[2] * x * z + 2 * q[3] * x + q[4] * y * y + 2 * q[5] * y * z
                + 2 * q[6] * y + q[7] * z * z + 2 * q[8] * z + q[9])

    heap = []
    for i, j in sorted(edges):
        for kept, gone in ((i, j), (j, i)):
            if not locked[gone]:
                value = cost(kept, gone)
                if value <= limit:
                    heap.append((max(value, 0.0), gone, kept, 0, 0))
    heapq.heapify(heap)

    def neighbours(v: int) -> set:
        out = set()
        for number in around[v]:
            out.update(faces[number])
        out.discard(v)
        return out

    sequence = []
    while heap:
        _, gone, kept, stamp_gone, stamp_kept = heapq.heappop(heap)
        if not (alive[gone] and alive[kept]) or stamp[gone] != stamp_gone or stamp[kept] != stamp_kept:
            continue
        shared = around[gone] & around[kept]
        if len(shared) != 2:
            continue
        thirds = set()
        for number in shared:
            thirds.update(faces[number])
        thirds -= {gone, kept}
        if len(thirds) != 2 or (neighbours(gone) & neighbours(kept)) != thirds:
            continue
        target = positions[kept]
        turned = False
        for number in around[gone] - shared:
            a, b, c = (target if v == gone else positions[v] for v in faces[number])
            nx, ny, nz, length = unit_normal(a, b, c)
            was = normals[number]
            if length == 0.0 or nx * was[0] + ny * was[1] + nz * was[2] < TURN_COSINE:
                turned = True
                break
        if turned:
            continue
        for number in shared:
            for v in faces[number]:
                around[v].discard(number)
        for number in around[gone]:
            face = faces[number]
            face[face.index(gone)] = kept
            around[kept].add(number)
        around[gone] = set()
        alive[gone] = False
        one, two = quadric[kept], quadric[gone]
        for k in range(10):
            one[k] += two[k]
        stamp[kept] += 1
        sequence.append((gone, kept))
        for v in sorted(neighbours(kept)):
            for into, out in ((kept, v), (v, kept)):
                if not locked[out]:
                    value = cost(into, out)
                    if value <= limit:
                        heapq.heappush(heap, (max(value, 0.0), out, into, stamp[out], stamp[into]))
    return sequence


def replay(faces: list, sequence: list, count: int) -> list:
    """The faces after the first ``count`` collapses of ``sequence``: each vertex that went replaced by the one it
    went onto (followed to the end), the faces left with two corners in one place dropped; the file's order kept."""

    onto = {}
    for gone, kept in sequence[:count]:
        onto[gone] = kept

    def last(v: int) -> int:
        path = []
        while v in onto:
            path.append(v)
            v = onto[v]
        for step in path:
            onto[step] = v
        return v

    out = []
    for face in faces:
        a, b, c = last(face[0]), last(face[1]), last(face[2])
        if a != b and b != c and a != c:
            out.append([a, b, c])
    return out


# -- the deviation, measured ------------------------------------------------------------------------------------------

class Surface:
    """A surface's triangles in a grid of cells: distance(point) is the exact distance to its nearest triangle where
    that is at most ``bound``, else infinite.  A triangle is held by every cell that a point within ``bound`` of it
    may fall in: the columns of its box (grown by the bound) along its normal's largest axis, each over the heights
    its plane takes there, the bound either way."""

    def __init__(self, triangles: list, bound: float, cell=None):
        self.bound = bound
        kept = []
        for t in triangles:
            nx, ny, nz, length = unit_normal(t[0:3], t[3:6], t[6:9])
            if length > 0.0:
                kept.append((t, (nx, ny, nz), -(nx * t[0] + ny * t[1] + nz * t[2])))
        if cell is None:
            sides = [max(max(t[k], t[k + 3], t[k + 6]) - min(t[k], t[k + 3], t[k + 6]) for k in range(3)) for t, _, _ in kept]
            cell = max(2.0 * bound, math.fsum(sides) / len(sides) if sides else 1.0, 1e-9)
        self.cell = cell
        self.cells = {}
        cells = self.cells
        for t, normal, offset in kept:
            low = [min(t[k], t[k + 3], t[k + 6]) - bound for k in range(3)]
            high = [max(t[k], t[k + 3], t[k + 6]) + bound for k in range(3)]
            first = [math.floor(low[k] / cell) for k in range(3)]
            last = [math.floor(high[k] / cell) for k in range(3)]
            size = [abs(value) for value in normal]
            w = size.index(max(size))
            u, v = (w + 1) % 3, (w + 2) % 3
            # Over one column the plane's height varies by half a cell's slope either way; a point within the bound of
            # the plane is within bound / |n_w| of its height.
            reach = (size[u] + size[v]) * cell / (2.0 * size[w]) + bound / size[w]
            # A record: the corners, the edges a -> b and a -> c, the plane.
            record = (t[0], t[1], t[2], t[3] - t[0], t[4] - t[1], t[5] - t[2], t[6] - t[0], t[7] - t[1], t[8] - t[2],
                      normal[0], normal[1], normal[2], offset)
            key = [0, 0, 0]
            for i in range(first[u], last[u] + 1):
                key[u] = i
                for j in range(first[v], last[v] + 1):
                    key[v] = j
                    height = -(offset + normal[u] * (i + 0.5) * cell + normal[v] * (j + 0.5) * cell) / normal[w]
                    bottom = max(first[w], math.floor((height - reach) / cell))
                    top = min(last[w], math.floor((height + reach) / cell))
                    for k in range(bottom, top + 1):
                        key[w] = k
                        held = cells.get((key[0], key[1], key[2]))
                        if held is None:
                            cells[(key[0], key[1], key[2])] = [record]
                        else:
                            held.append(record)

    def distance(self, point) -> float:
        px, py, pz = point
        cell = self.cell
        held = self.cells.get((math.floor(px / cell), math.floor(py / cell), math.floor(pz / cell)))
        if not held:
            return math.inf
        bound = self.bound
        best = math.inf
        for ax, ay, az, abx, aby, abz, acx, acy, acz, nx, ny, nz, offset in held:
            plane = nx * px + ny * py + nz * pz + offset
            if plane * plane >= best or plane > bound or plane < -bound:
                continue
            # Ericson, Real-Time Collision Detection 5.1.5: the closest point of the triangle a, b, c.
            apx, apy, apz = px - ax, py - ay, pz - az
            d1 = abx * apx + aby * apy + abz * apz
            d2 = acx * apx + acy * apy + acz * apz
            if d1 <= 0.0 and d2 <= 0.0:
                qx, qy, qz = ax, ay, az
            else:
                bpx, bpy, bpz = apx - abx, apy - aby, apz - abz
                d3 = abx * bpx + aby * bpy + abz * bpz
                d4 = acx * bpx + acy * bpy + acz * bpz
                if d3 >= 0.0 and d4 <= d3:
                    qx, qy, qz = ax + abx, ay + aby, az + abz
                else:
                    vc = d1 * d4 - d3 * d2
                    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
                        s = d1 / (d1 - d3)
                        qx, qy, qz = ax + s * abx, ay + s * aby, az + s * abz
                    else:
                        cpx, cpy, cpz = apx - acx, apy - acy, apz - acz
                        d5 = abx * cpx + aby * cpy + abz * cpz
                        d6 = acx * cpx + acy * cpy + acz * cpz
                        if d6 >= 0.0 and d5 <= d6:
                            qx, qy, qz = ax + acx, ay + acy, az + acz
                        else:
                            vb = d5 * d2 - d1 * d6
                            if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
                                s = d2 / (d2 - d6)
                                qx, qy, qz = ax + s * acx, ay + s * acy, az + s * acz
                            else:
                                va = d3 * d6 - d5 * d4
                                if va <= 0.0 and d4 - d3 >= 0.0 and d5 - d6 >= 0.0:
                                    s = (d4 - d3) / ((d4 - d3) + (d5 - d6))
                                    qx, qy, qz = ax + abx + s * (acx - abx), ay + aby + s * (acy - aby), az + abz + s * (acz - abz)
                                else:
                                    scale = 1.0 / (va + vb + vc)
                                    s, r = vb * scale, vc * scale
                                    qx, qy, qz = ax + abx * s + acx * r, ay + aby * s + acy * r, az + abz * s + acz * r
            dx, dy, dz = px - qx, py - qy, pz - qz
            squared = dx * dx + dy * dy + dz * dz
            if squared < best:
                best = squared
        distance = math.sqrt(best) if best < math.inf else math.inf
        return distance if distance <= bound else math.inf


def probes(triangles: list, spacing: float = PROBE_SPACING_MM, steps: int = PROBE_STEPS) -> set:
    """The points a surface is measured at: every vertex, every edge's middle, every triangle's centre, and on each
    triangle longer than ``spacing`` a barycentric grid about that far apart (``steps`` a side at most)."""

    points = set()
    for t in triangles:
        a, b, c = t[0:3], t[3:6], t[6:9]
        points.add(a)
        points.add(b)
        points.add(c)
        points.add(((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0, (a[2] + b[2] + c[2]) / 3.0))
        longest = 0.0
        for p, q in ((a, b), (b, c), (c, a)):
            points.add(((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0, (p[2] + q[2]) / 2.0))
            dx, dy, dz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            if length > longest:
                longest = length
        if longest > spacing:
            n = min(steps, math.ceil(longest / spacing))
            ux, uy, uz = (b[0] - a[0]) / n, (b[1] - a[1]) / n, (b[2] - a[2]) / n
            vx, vy, vz = (c[0] - a[0]) / n, (c[1] - a[1]) / n, (c[2] - a[2]) / n
            for i in range(n + 1):
                for j in range(n + 1 - i):
                    points.add((a[0] + i * ux + j * vx, a[1] + i * uy + j * vy, a[2] + i * uz + j * vz))
    return points


def one_way(source: list, target: list, bound: float) -> float:
    """The greatest distance from ``source``'s probes to the surface ``target`` (mm); infinite beyond ``bound``."""

    surface = Surface(target, bound)
    worst = 0.0
    for point in probes(source):
        distance = surface.distance(point)
        if distance > worst:
            worst = distance
            if worst == math.inf:
                break
    return worst


def deviation(one: list, other: list, bound: float) -> tuple:
    """(``one`` to ``other``, ``other`` to ``one``): the two one-way deviations (mm), each infinite beyond ``bound``."""

    return one_way(one, other, bound), one_way(other, one, bound)


# -- the decimation and its gate ---------------------------------------------------------------------------------------

def gate(triangles: list, positions: list, faces: list, sequence: list, tolerance: float) -> tuple:
    """(triangles, report) of the longest prefix of ``sequence`` whose surface is within ``tolerance`` of
    ``triangles`` both ways, measured (deviation()); the whole sequence where it is.  report: {triangles_in,
    triangles_out, collapses (the sequence's), kept (the prefix's), source_to_result_mm, result_to_source_mm}."""

    bound = BOUND_TOLERANCES * tolerance

    def measured(count: int) -> tuple:
        result = triangles_of(positions, replay(faces, sequence, count))
        return result, deviation(triangles, result, bound)

    low, high = 0, len(sequence)
    result, (forth, back) = measured(high)
    if max(forth, back) > tolerance:
        # No collapse at all is the welded input (within 0.0001 mm of the file's corners).
        best = (0,) + measured(0)
        high -= 1
        while low < high:
            middle = (low + high + 1) // 2
            candidate, numbers = measured(middle)
            if max(numbers) <= tolerance:
                low, best = middle, (middle, candidate, numbers)
            else:
                high = middle - 1
        high, result, (forth, back) = best
        if max(forth, back) > tolerance:
            raise MeshError(f"the welded surface itself is {max(forth, back):.4f} mm from the file's, beyond {tolerance} mm")
    return result, {"triangles_in": len(triangles), "triangles_out": len(result), "collapses": len(sequence), "kept": high,
                    "source_to_result_mm": forth, "result_to_source_mm": back}


def decimate(triangles: list, tolerance: float) -> tuple:
    """(triangles, report): ``triangles`` (9 floats each, as read_stl gives them) decimated by collapses() as far as
    they go and gated by gate(): the result within ``tolerance`` of the input both ways, measured."""

    positions, faces = weld(triangles)
    return gate(triangles, positions, faces, collapses(positions, faces, tolerance), tolerance)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="a binary STL")
    parser.add_argument("target", type=Path, help="the decimated binary STL to write")
    parser.add_argument("--tolerance", type=float, required=True, metavar="MM", help="the two-way deviation allowed")
    parser.add_argument("--header", default=None, help="the STL's header text (80 bytes at most)")
    args = parser.parse_args(argv)
    try:
        triangles = read_stl(args.source.read_bytes())
        result, report = decimate(triangles, args.tolerance)
        header = (args.header or f"decimated <= {args.tolerance:g} mm by tools/mesh_decimate.py").encode("ascii")
        args.target.write_bytes(stl_bytes(result, header))
    except (MeshError, OSError, UnicodeError) as error:
        print(f"mesh_decimate: {error}", file=sys.stderr)
        return 1
    print(f"{args.source.name}: {report['triangles_in']} -> {report['triangles_out']} triangles, {report['kept']} of "
          f"{report['collapses']} collapses, the source within {report['source_to_result_mm']:.4f} mm of the result and the "
          f"result within {report['result_to_source_mm']:.4f} mm of the source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
