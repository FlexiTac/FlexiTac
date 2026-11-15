"""tools/mesh_decimate.py: the quadric decimator of the Library's showcase (2026-11-12), on small fixtures.

The fixtures are made here by arithmetic alone (dyadic coordinates, a rational circle), so they are the same floats on
every host: a box of flat faces in 1 mm squares, an open paraboloid cap, a tube.

- The decimation: the box comes down to its twelve triangles with no deviation, closed as it was; the cap keeps its
  border, vertex for vertex and edge for edge (a cut stays as it is); every vertex kept is a vertex of the input, bit
  for bit; no face left turns more than 15 degrees from the normal it had (followed through the collapses by this
  module's own bookkeeping).
- The same bytes on every run and every Python: two runs equal, and the cap's and the gated cap's SHA-256 pinned
  (computed on 3.10 and 3.12; CI runs 3.9 and 3.12).
- The gate: a collapse sequence made with a looser tolerance is cut back to a prefix whose measured deviation is
  within the tolerance both ways, the whole of it beyond; a sequence already within it is kept whole.
- The deviation: exact on planes a known distance apart, one way infinite where a surface has no counterpart within
  the bound; Surface.distance against a point-to-triangle distance written another way here, on a few thousand
  points.
- The file: a binary STL read and written (float32 corners, unit normals, the header), what is no binary STL
  refused; weld() merging corners within 0.0001 mm and dropping a face of two corners; components() by shared edges,
  with ``pairs`` only through an edge of exactly two faces.
- The module needs the standard library alone and holds no host path.
"""

from __future__ import annotations

import ast
import hashlib
import math
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "tools"))
import mesh_decimate  # noqa: E402

COS_15 = 0.9659258262890683
# The decimated cap and the gated cap as binary STL (headers b"decimated" and b"gated"), on every Python.
CAP_SHA256 = "f7d8e6a1b9eed1e0513ea5c7369a3c976fb54650dd502779e1f816722f8d6804"
GATED_SHA256 = "8cb6ef7b27319bb61121c77d36178cead0ba720180e59255534ae46aaa3c91b9"
STDLIB = {"__future__", "argparse", "hashlib", "heapq", "json", "math", "struct", "sys", "pathlib"}


def grid(origin, u, v, nu: int, nv: int) -> list:
    """A parallelogram of nu x nv cells from ``origin`` along ``u`` and ``v``, two triangles a cell."""

    def point(i, j):
        return tuple(origin[k] + i * u[k] + j * v[k] for k in range(3))

    out = []
    for i in range(nu):
        for j in range(nv):
            a, b, c, d = point(i, j), point(i + 1, j), point(i + 1, j + 1), point(i, j + 1)
            out += [a + b + c, a + c + d]
    return out


def box(low, high, step: float = 1.0) -> list:
    """A closed box, its six faces in squares of ``step``, the normals outward."""

    n = [int(round((high[k] - low[k]) / step)) for k in range(3)]
    x, y, z = (step, 0.0, 0.0), (0.0, step, 0.0), (0.0, 0.0, step)
    return (grid(low, y, x, n[1], n[0]) + grid((low[0], low[1], high[2]), x, y, n[0], n[1])
            + grid(low, x, z, n[0], n[2]) + grid((low[0], high[1], low[2]), z, x, n[2], n[0])
            + grid(low, z, y, n[2], n[1]) + grid((high[0], low[1], low[2]), y, z, n[1], n[2]))


def cap(half: float = 8.0, step: float = 0.5, depth: float = 32.0) -> list:
    """An open paraboloid cap z = (x^2 + y^2) / depth over a square of half-side ``half``."""

    def point(i, j):
        x, y = -half + i * step, -half + j * step
        return (x, y, (x * x + y * y) / depth)

    n = int(round(2 * half / step))
    out = []
    for i in range(n):
        for j in range(n):
            a, b, c, d = point(i, j), point(i + 1, j), point(i + 1, j + 1), point(i, j + 1)
            out += [a + b + c, a + c + d]
    return out


def tube(radius: float = 10.0, length: float = 20.0, segments: int = 48, rings: int = 10) -> list:
    """An open tube about z: ``segments`` flats round a rational circle (no library sine), ``rings`` along."""

    quarter = segments // 4
    circle = []
    for k in range(segments):
        turns, rest = divmod(k, quarter)
        t = rest / quarter
        c, s = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)
        for _ in range(turns):
            c, s = -s, c
        circle.append((radius * c, radius * s))
    out = []
    for k in range(segments):
        (x0, y0), (x1, y1) = circle[k], circle[(k + 1) % segments]
        for ring in range(rings):
            z0, z1 = ring * length / rings, (ring + 1) * length / rings
            a, b, c, d = (x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)
            out += [a + b + c, a + c + d]
    return out


def as_file(triangles: list) -> list:
    """The triangles as a binary STL holds them (float32)."""

    return mesh_decimate.read_stl(mesh_decimate.stl_bytes(triangles, b"fixture"))


def edges_of(triangles: list) -> dict:
    """{an edge (two corners, sorted): how many triangles hold it}."""

    out = {}
    for t in triangles:
        corners = (t[0:3], t[3:6], t[6:9])
        for k in range(3):
            key = tuple(sorted((corners[k], corners[(k + 1) % 3])))
            out[key] = out.get(key, 0) + 1
    return out


def distance(point, triangle) -> float:
    """The distance from a point to a triangle, another way than the module's: the foot on the plane where it lies
    inside, else the nearest of the three edges' segments."""

    a, b, c = triangle[0:3], triangle[3:6], triangle[6:9]
    sub = lambda p, q: (p[0] - q[0], p[1] - q[1], p[2] - q[2])  # noqa: E731
    dot = lambda p, q: p[0] * q[0] + p[1] * q[1] + p[2] * q[2]  # noqa: E731
    cross = lambda p, q: (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])  # noqa: E731
    normal = cross(sub(b, a), sub(c, a))
    inside = all(dot(cross(sub(q, p), sub(point, p)), normal) >= 0 for p, q in ((a, b), (b, c), (c, a)))
    if inside:
        return abs(dot(sub(point, a), normal)) / math.sqrt(dot(normal, normal))
    best = math.inf
    for p, q in ((a, b), (b, c), (c, a)):
        along = sub(q, p)
        t = max(0.0, min(1.0, dot(sub(point, p), along) / dot(along, along)))
        best = min(best, math.dist(point, (p[0] + t * along[0], p[1] + t * along[1], p[2] + t * along[2])))
    return best


class DecimationTests(unittest.TestCase):
    def test_a_flat_faced_box_comes_down_to_its_corners(self) -> None:
        triangles = as_file(box((0.0, 0.0, 0.0), (16.0, 8.0, 4.0)))
        self.assertEqual(len(triangles), 896)
        result, report = mesh_decimate.decimate(triangles, 0.01)
        self.assertEqual((report["triangles_in"], report["triangles_out"], report["kept"]), (896, 12, report["collapses"]))
        self.assertLess(max(report["source_to_result_mm"], report["result_to_source_mm"]), 1e-9)
        # Still closed (every edge between two triangles), its eight corners the box's, its normals outward.
        self.assertEqual(set(edges_of(result).values()), {2})
        corners = {t[k:k + 3] for t in result for k in (0, 3, 6)}
        self.assertEqual(corners, {(x, y, z) for x in (0.0, 16.0) for y in (0.0, 8.0) for z in (0.0, 4.0)})
        for t in result:
            normal = mesh_decimate.unit_normal(t[0:3], t[3:6], t[6:9])
            centre = [(t[k] + t[k + 3] + t[k + 6]) / 3 for k in range(3)]
            self.assertGreater(math.fsum(normal[k] * (centre[k] - (8.0, 4.0, 2.0)[k]) for k in range(3)), 0)

    def test_an_open_surface_keeps_its_border(self) -> None:
        triangles = as_file(cap())
        result, report = mesh_decimate.decimate(triangles, 0.05)
        self.assertLess(report["triangles_out"], 0.6 * report["triangles_in"])
        self.assertLessEqual(max(report["source_to_result_mm"], report["result_to_source_mm"]), 0.05)
        border = {edge for edge, count in edges_of(triangles).items() if count == 1}
        self.assertEqual(len(border), 4 * 32)
        self.assertEqual({edge for edge, count in edges_of(result).items() if count == 1}, border, "the border, edge for edge")
        # Every vertex kept is a vertex of the input, bit for bit.
        self.assertLessEqual({t[k:k + 3] for t in result for k in (0, 3, 6)}, {t[k:k + 3] for t in triangles for k in (0, 3, 6)})
        # The numbers the report gives, measured again here another way: every input vertex to the result.
        worst = max(min(distance(t[k:k + 3], other) for other in result) for t in triangles[::7] for k in (0, 3, 6))
        self.assertLessEqual(worst, 0.05)
        self.assertLessEqual(worst, report["source_to_result_mm"] + 1e-12)

    def test_no_face_turns_more_than_fifteen_degrees(self) -> None:
        for name, triangles, tolerance in (("tube", as_file(tube()), 0.1), ("cap", as_file(cap()), 0.5)):
            positions, faces = mesh_decimate.weld(triangles)
            sequence = mesh_decimate.collapses(positions, faces, tolerance)
            self.assertGreater(len(sequence), 100, name)
            onto = dict(sequence)

            def last(vertex: int) -> int:
                while vertex in onto:
                    vertex = onto[vertex]
                return vertex

            kept = 0
            for face in faces:
                moved = [last(vertex) for vertex in face]
                if len(set(moved)) < 3:
                    continue
                kept += 1
                was = mesh_decimate.unit_normal(*(positions[vertex] for vertex in face))
                now = mesh_decimate.unit_normal(*(positions[vertex] for vertex in moved))
                self.assertGreaterEqual(math.fsum(was[k] * now[k] for k in range(3)), COS_15 - 1e-12, name)
            self.assertEqual(kept, len(mesh_decimate.replay(faces, sequence, len(sequence))))
        # The tube: its flats merge along it, never round it past the fifteen degrees (two flats are 7.5 degrees).
        result, report = mesh_decimate.decimate(as_file(tube()), 0.1)
        self.assertEqual(report["triangles_out"], 96)
        self.assertLess(max(report["source_to_result_mm"], report["result_to_source_mm"]), 1e-9)

    def test_the_same_bytes_on_every_run_and_every_python(self) -> None:
        triangles = as_file(cap())
        one = mesh_decimate.stl_bytes(mesh_decimate.decimate(triangles, 0.05)[0], b"decimated")
        two = mesh_decimate.stl_bytes(mesh_decimate.decimate(list(triangles), 0.05)[0], b"decimated")
        self.assertEqual(one, two)
        self.assertEqual(hashlib.sha256(one).hexdigest(), CAP_SHA256, f"another result on Python {sys.version.split()[0]}")

    def test_the_gate_keeps_the_longest_prefix_within_the_tolerance(self) -> None:
        triangles = as_file(cap())
        positions, faces = mesh_decimate.weld(triangles)
        loose = mesh_decimate.collapses(positions, faces, 0.5)
        whole = mesh_decimate.triangles_of(positions, mesh_decimate.replay(faces, loose, len(loose)))
        self.assertGreater(max(mesh_decimate.deviation(triangles, whole, 2.0)), 0.05, "the loose sequence goes beyond the tolerance")
        result, report = mesh_decimate.gate(triangles, positions, faces, loose, 0.05)
        self.assertEqual(report["collapses"], len(loose))
        self.assertTrue(0 < report["kept"] < len(loose))
        self.assertLessEqual(max(report["source_to_result_mm"], report["result_to_source_mm"]), 0.05)
        self.assertEqual(result, mesh_decimate.triangles_of(positions, mesh_decimate.replay(faces, loose, report["kept"])))
        self.assertEqual((report["source_to_result_mm"], report["result_to_source_mm"]), mesh_decimate.deviation(triangles, result, 0.2))
        self.assertEqual(hashlib.sha256(mesh_decimate.stl_bytes(result, b"gated")).hexdigest(), GATED_SHA256)
        # A sequence within the tolerance is kept whole; no collapse at all is the input.
        tight = mesh_decimate.collapses(positions, faces, 0.05)
        self.assertEqual(mesh_decimate.gate(triangles, positions, faces, tight, 0.05)[1]["kept"], len(tight))
        same, report = mesh_decimate.gate(triangles, positions, faces, [], 0.05)
        self.assertEqual((same, report["kept"]), (triangles, 0))
        self.assertLess(max(report["source_to_result_mm"], report["result_to_source_mm"]), 1e-12)

    def test_a_replay_is_the_sequence_s_prefix(self) -> None:
        faces = [[0, 1, 2], [1, 3, 2], [2, 3, 4]]
        self.assertEqual(mesh_decimate.replay(faces, [(1, 0), (3, 2)], 0), faces)
        self.assertEqual(mesh_decimate.replay(faces, [(1, 0), (3, 2)], 1), [[0, 3, 2], [2, 3, 4]])
        self.assertEqual(mesh_decimate.replay(faces, [(1, 0), (3, 2)], 2), [])
        # A vertex that went onto one that went later is followed to the end.
        self.assertEqual(mesh_decimate.replay([[0, 1, 5], [3, 4, 5]], [(1, 3), (3, 4)], 2), [[0, 4, 5]])


class DeviationTests(unittest.TestCase):
    def test_two_planes_are_their_distance_apart_both_ways(self) -> None:
        low = grid((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 10, 10)
        high = [tuple(value + (0.25 if k % 3 == 2 else 0.0) for k, value in enumerate(t)) for t in low]
        self.assertEqual(mesh_decimate.deviation(low, high, 1.0), (0.25, 0.25))
        self.assertLess(max(mesh_decimate.deviation(low, low, 1.0)), 1e-12)
        # Beyond the bound it is asked for: infinite.
        self.assertEqual(mesh_decimate.deviation(low, high, 0.2), (math.inf, math.inf))
        # One way only: a patch over the middle of the plane is near it, the plane's far corners are not near the patch.
        patch = grid((4.0, 4.0, 0.125), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 2, 2)
        self.assertEqual(mesh_decimate.deviation(patch, low, 1.0), (0.125, math.inf))
        # A coarse triangle over a fine surface is probed inside, not at its corners alone: a ridge under its middle.
        flat = [(0.0, 0.0, 0.0, 12.0, 0.0, 0.0, 0.0, 12.0, 0.0)]
        ridge = [(0.0, 0.0, 0.0, 12.0, 0.0, 0.0, 4.0, 4.0, 0.75), (12.0, 0.0, 0.0, 0.0, 12.0, 0.0, 4.0, 4.0, 0.75),
                 (0.0, 12.0, 0.0, 0.0, 0.0, 0.0, 4.0, 4.0, 0.75)]
        forth, back = mesh_decimate.deviation(flat, ridge, 2.0)
        self.assertGreater(forth, 0.6)
        self.assertEqual(back, 0.75)

    def test_the_surface_s_distance_is_the_point_to_triangle_distance(self) -> None:
        # A few thousand points about a cap, each against every triangle the slow way.
        triangles = as_file(cap(half=2.0, step=0.5))
        surface = mesh_decimate.Surface(triangles, 0.75)
        state, worst, measured = 12345, 0.0, 0
        for _ in range(3000):
            point = []
            for axis in range(3):
                state = (1103515245 * state + 12345) % 2 ** 31
                point.append((state / 2 ** 31) * (6.0 if axis < 2 else 2.0) - (3.0 if axis < 2 else 0.75))
            slow = min(distance(point, t) for t in triangles)
            fast = surface.distance(point)
            if slow <= 0.75:
                measured += 1
                worst = max(worst, abs(fast - slow))
            else:
                self.assertEqual(fast, math.inf)
        self.assertGreater(measured, 500)
        self.assertLess(worst, 1e-9)
        # A triangle of no area holds nothing; a surface of none is infinitely far.
        self.assertEqual(mesh_decimate.Surface([(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0)], 1.0).distance((0.5, 0.0, 0.0)), math.inf)

    def test_the_probes_are_the_corners_the_middles_the_centres_and_a_grid(self) -> None:
        small = mesh_decimate.probes([(0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.25, 0.0)])
        self.assertEqual(len(small), 7, "three corners, three edge middles, the centre")
        large = mesh_decimate.probes([(0.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 4.0, 0.0)])
        self.assertIn((1.0, 1.0, 0.0), large, "inside it, a grid at most 0.5 mm apart (twelve steps along its longest edge)")
        self.assertIn(len(large), (13 * 14 // 2, 13 * 14 // 2 + 1), "the grid's 91 points (its centre one of them, to a rounding)")
        huge = mesh_decimate.probes([(0.0, 0.0, 0.0, 400.0, 0.0, 0.0, 0.0, 400.0, 0.0)])
        self.assertLessEqual(len(huge), (mesh_decimate.PROBE_STEPS + 1) * (mesh_decimate.PROBE_STEPS + 2) // 2 + 4)


class FileTests(unittest.TestCase):
    def test_a_binary_stl_is_read_and_written(self) -> None:
        triangles = [(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 2.0, 0.0), (0.1, 0.2, 0.3, 1.5, 0.25, 0.0, 0.0, 1.0, 4.0)]
        data = mesh_decimate.stl_bytes(triangles, b"a header")
        self.assertEqual((len(data), data[:80], struct.unpack_from("<I", data, 80)[0]), (84 + 50 * 2, b"a header".ljust(80, b" "), 2))
        read = mesh_decimate.read_stl(data)
        self.assertEqual(read[0], triangles[0])
        self.assertEqual(read[1], struct.unpack("<9f", struct.pack("<9f", *triangles[1])), "float32 corners")
        # The normal: the corners' unit normal; attribute 0.
        self.assertEqual(struct.unpack_from("<3f", data, 84), (0.0, 0.0, 1.0))
        self.assertEqual(struct.unpack_from("<H", data, 84 + 48)[0], 0)
        normal = struct.unpack_from("<3f", data, 84 + 50)
        self.assertAlmostEqual(math.fsum(value * value for value in normal), 1.0, places=6)
        self.assertEqual(mesh_decimate.stl_bytes(read, b"a header"), data, "a file read and written is the file")
        self.assertEqual(mesh_decimate.stl_bytes([(0.0,) * 9], b"")[84:96], b"\0" * 12, "no area: a zero normal")
        for broken, problem in ((data[:-1], "84 \\+ 50 bytes a facet"), (b"solid x", "shorter than its header"), (data + b"\0", "84 \\+ 50 bytes a facet")):
            with self.assertRaisesRegex(mesh_decimate.MeshError, problem):
                mesh_decimate.read_stl(broken)
        with self.assertRaisesRegex(mesh_decimate.MeshError, "header of 81 bytes"):
            mesh_decimate.stl_bytes(triangles, b"x" * 81)

    def test_weld_merges_corners_within_a_tenth_of_a_micron(self) -> None:
        triangles = [(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0), (1.00004, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.00004, 0.0),
                     (0.0, 0.0, 0.0, 0.00004, 0.0, 0.0, 5.0, 5.0, 5.0)]
        positions, faces = mesh_decimate.weld(triangles)
        self.assertEqual(positions, [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 5.0, 5.0)])
        self.assertEqual(faces, [[0, 1, 2], [1, 3, 2]], "a corner stands where its first one stood; two corners in one place: dropped")
        self.assertEqual(mesh_decimate.triangles_of(positions, faces)[1], (1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0))
        # With no scale: the same floats only.
        positions, faces = mesh_decimate.weld(triangles, None)
        self.assertEqual((len(positions), len(faces)), (8, 3))

    def test_components_are_joined_by_shared_edges(self) -> None:
        # Two triangles on an edge, a third touching at a vertex only, a fourth apart.
        faces = [[0, 1, 2], [1, 3, 2], [3, 4, 5], [6, 7, 8]]
        self.assertEqual(mesh_decimate.components(faces), [[0, 1], [2], [3]])
        # Three faces on one edge (two solids glued there): one piece, or with pairs each its own.
        fan = [[0, 1, 2], [0, 1, 3], [0, 1, 4], [2, 0, 5]]
        self.assertEqual(mesh_decimate.components(fan), [[0, 1, 2, 3]])
        self.assertEqual(mesh_decimate.components(fan, pairs=True), [[0, 3], [1], [2]])
        self.assertEqual(mesh_decimate.components([]), [])
        # Two boxes: two components, whatever the order of their triangles.
        both = as_file(box((0.0, 0.0, 0.0), (2.0, 2.0, 2.0)) + box((5.0, 0.0, 0.0), (7.0, 2.0, 2.0)))
        positions, faces = mesh_decimate.weld(both[::2] + both[1::2])
        self.assertEqual(sorted(len(group) for group in mesh_decimate.components(faces)), [48, 48])


class ModuleTests(unittest.TestCase):
    def test_the_module_is_the_standard_library_s_alone(self) -> None:
        path = ROOT / "tools" / "mesh_decimate.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path), feature_version=(3, 9))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        self.assertLessEqual(imported, STDLIB)
        # No float sum() and no library sine or cosine: the same bytes on every host.
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertNotIn("sum", calls)
        used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "math"}
        self.assertLessEqual(used, {"sqrt", "floor", "ceil", "inf", "fsum"})
        # Nor a power: a float's ** is the C library's pow(), which is not x * x on every host (the review of
        # 2026-11-12: a probe's edge length was squared with ** 2, and with it the probes' count could differ).
        self.assertFalse([node.lineno for node in ast.walk(tree) if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, ast.Pow)])
        self.assertFalse([node.lineno for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "pow"])
        self.assertEqual(mesh_decimate.TURN_COSINE, COS_15)
        self.assertAlmostEqual(mesh_decimate.TURN_COSINE, math.cos(math.radians(15)), places=15)
        self.assertNotRegex(source, r"/home/|/Users/|/tmp/")

    def test_the_command_decimates_a_file(self) -> None:
        import contextlib
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / "in.stl", Path(folder) / "out.stl"
            source.write_bytes(mesh_decimate.stl_bytes(box((0.0, 0.0, 0.0), (4.0, 4.0, 4.0)), b"a box"))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(mesh_decimate.main([str(source), str(target), "--tolerance", "0.1", "--header", "a smaller box"]), 0)
            self.assertIn("in.stl: 192 -> 12 triangles", out.getvalue())
            self.assertEqual(target.read_bytes()[:80], b"a smaller box".ljust(80, b" "))
            self.assertEqual(len(mesh_decimate.read_stl(target.read_bytes())), 12)
            source.write_bytes(b"solid ascii\nendsolid\n")
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(mesh_decimate.main([str(source), str(target), "--tolerance", "0.1"]), 1)
            self.assertIn("mesh_decimate: not a binary STL", err.getvalue())


if __name__ == "__main__":
    unittest.main()
