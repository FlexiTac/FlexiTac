"""CAD mode: STL reading, welding, orientation and covered walls (surface.mesh)."""

from __future__ import annotations

import json
import math
import re
import shutil
import struct
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from surface import mesh as mesh_module
from surface.errors import SURFACE_ERROR_CODES, SurfaceError
from surface.mesh import binary_stl, read_stl

try:
    import surface_fixtures as F
except ImportError:  # run as a package
    from tests import surface_fixtures as F

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "asset"
STL_JS = ROOT / "web" / "cad" / "stl.js"


def _quad(a, b, c, d) -> list:
    return [(a, b, c), (a, c, d)]


def _pocket_block() -> list:
    """A 40 x 40 x 20 block with an open pocket [10, 30]^2 x [10, 20] in its top: one closed shell, outward."""

    outer = [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0), (0.0, 40.0)]
    inner = [(10.0, 10.0), (30.0, 10.0), (30.0, 30.0), (10.0, 30.0)]
    triangles = []
    for i in range(4):
        j = (i + 1) % 4
        triangles += _quad((*outer[i], 20.0), (*outer[j], 20.0), (*inner[j], 20.0), (*inner[i], 20.0))  # top rim
        triangles += _quad((*outer[i], 0.0), (*outer[j], 0.0), (*outer[j], 20.0), (*outer[i], 20.0))  # outer walls
        triangles += _quad((*inner[i], 20.0), (*inner[j], 20.0), (*inner[j], 10.0), (*inner[i], 10.0))  # pocket walls
    triangles += _quad((0.0, 0.0, 0.0), (0.0, 40.0, 0.0), (40.0, 40.0, 0.0), (40.0, 0.0, 0.0))  # bottom
    triangles += _quad((10.0, 10.0, 10.0), (30.0, 10.0, 10.0), (30.0, 30.0, 10.0), (10.0, 30.0, 10.0))  # pocket floor
    return triangles


def _grid_box(n: int, size=(100.0, 100.0, 10.0), origin=(0.0, 0.0, 0.0)) -> list:
    """A closed box whose top and bottom faces are n x n grids (its walls n x 1 strips), outward."""

    (x0, y0, z0), (sx, sy, sz) = origin, size
    hx, hy, zb, zt = sx / n, sy / n, z0, z0 + sz
    triangles = []
    for i in range(n):
        for j in range(n):
            a, b = (x0 + i * hx, y0 + j * hy), (x0 + (i + 1) * hx, y0 + j * hy)
            c, d = (x0 + (i + 1) * hx, y0 + (j + 1) * hy), (x0 + i * hx, y0 + (j + 1) * hy)
            triangles += _quad((*a, zt), (*b, zt), (*c, zt), (*d, zt)) + _quad((*a, zb), (*d, zb), (*c, zb), (*b, zb))
        u0, u1 = x0 + i * hx, x0 + (i + 1) * hx
        v0, v1 = y0 + i * hy, y0 + (i + 1) * hy
        triangles += _quad((u0, y0, zb), (u1, y0, zb), (u1, y0, zt), (u0, y0, zt))  # -y
        triangles += _quad((u1, y0 + sy, zb), (u0, y0 + sy, zb), (u0, y0 + sy, zt), (u1, y0 + sy, zt))  # +y
        triangles += _quad((x0, v1, zb), (x0, v0, zb), (x0, v0, zt), (x0, v1, zt))  # -x
        triangles += _quad((x0 + sx, v0, zb), (x0 + sx, v1, zb), (x0 + sx, v1, zt), (x0 + sx, v0, zt))  # +x
    return triangles


def _tilted_sheet(n: int, size: float, tilt_deg: float, offset) -> list:
    """A flat n x n sheet tilted about x, turned 37 degrees about z and moved to ``offset``."""

    t, r = math.radians(tilt_deg), math.radians(37.0)

    def point(x, y):
        X, Y, Z = x, y * math.cos(t), y * math.sin(t)
        return (offset[0] + math.cos(r) * X - math.sin(r) * Y, offset[1] + math.sin(r) * X + math.cos(r) * Y, offset[2] + Z)

    h = size / n
    triangles = []
    for i in range(n):
        for j in range(n):
            triangles += _quad(point(i * h, j * h), point((i + 1) * h, j * h), point((i + 1) * h, (j + 1) * h), point(i * h, (j + 1) * h))
    return triangles


def _rotated(triangles, degrees) -> list:
    """The triangles turned about x, then y, then z (degrees)."""

    a, b, c = (math.radians(d) for d in degrees)

    def turn(p):
        x, y, z = p
        y, z = y * math.cos(c) - z * math.sin(c), y * math.sin(c) + z * math.cos(c)
        x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
        return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), z)

    return [tuple(turn(p) for p in t) for t in triangles]


def _other_diagonals(box) -> list:
    """F.box triangles with every face split along its other diagonal."""

    triangles = []
    for (a, b, c), (_, _, d) in zip(box[::2], box[1::2]):
        triangles += [(a, b, d), (b, c, d)]
    return triangles


def _uv_sphere(radius: float, rings: int, segments: int) -> list:
    """A uv sphere computed point by point: its south-pole and seam vertices are float noise apart (not welded)."""

    def point(i, j):
        t, f = math.pi * i / rings, 2 * math.pi * j / segments
        return (radius * math.sin(t) * math.cos(f), radius * math.sin(t) * math.sin(f), radius * math.cos(t))

    triangles = []
    for i in range(rings):
        for j in range(segments):
            a, b, c, d = point(i, j), point(i, j + 1), point(i + 1, j), point(i + 1, j + 1)
            if i > 0:
                triangles.append((a, c, b))
            if i < rings - 1:
                triangles.append((b, c, d))
    return triangles


def _saddle(offset: float, n: int = 10, size: float = 20.0) -> list:
    """An open, slightly curved and tilted sheet, moved by ``offset`` along the diagonal."""

    def point(i, j):
        x, y = -size / 2 + size * i / n, -size / 2 + size * j / n
        return (x + offset, y + offset, 0.02 * (x * x - y * y) + 0.3 * x + offset)

    triangles = []
    for i in range(n):
        for j in range(n):
            triangles += _quad(point(i, j), point(i + 1, j), point(i + 1, j + 1), point(i, j + 1))
    return triangles


def _dense_crack(n: int, size: float, at) -> list:
    """A size x size square: its left half one quad, its right half a fan whose left edge is cut into n pieces."""

    x, y = at
    half, apex = x + size / 2, (x + size, y + size / 2, 0.0)
    triangles = _quad((x, y, 0.0), (half, y, 0.0), (half, y + size, 0.0), (x, y + size, 0.0))
    for i in range(n):
        triangles.append(((half, y + size * i / n, 0.0), apex, (half, y + size * (i + 1) / n, 0.0)))
    triangles += [((half, y, 0.0), (x + size, y, 0.0), apex), ((half, y + size, 0.0), apex, (x + size, y + size, 0.0))]
    return triangles


def _ascii(triangles, open_line: str = "solid part", close_line: str = "endsolid part", newline: str = "\n") -> bytes:
    lines = [open_line]
    for a, b, c in triangles:
        lines += ["facet normal 0 0 0", "outer loop"] + [f"vertex {p[0]!r} {p[1]!r} {p[2]!r}" for p in (a, b, c)] + ["endloop", "endfacet"]
    lines.append(close_line)
    return newline.join(lines).encode("utf-8")


def _top_normal_z(mesh, point) -> float:
    from surface.select import nearest_facet

    return mesh.normals[nearest_facet(mesh, point)][2]


class ReadTests(unittest.TestCase):
    def test_binary_and_ascii_give_the_same_mesh(self) -> None:
        triangles = F.box()
        binary = read_stl(F.stl_bytes(triangles), unit="mm")
        text = read_stl(F.ascii_stl(triangles), unit="mm")
        self.assertEqual((binary.source_format, text.source_format), ("binary", "ascii"))
        self.assertEqual(binary.facets, text.facets)
        self.assertEqual(binary.vertices, text.vertices)
        self.assertEqual(binary.stats["vertices"], 8)
        self.assertTrue(binary.stats["watertight"])
        self.assertAlmostEqual(binary.stats["volume_mm3"], 1000.0, places=6)
        self.assertAlmostEqual(binary.stats["area_mm2"], 2 * (200 + 50 + 100), places=6)

    def test_a_binary_file_with_a_solid_header_is_binary(self) -> None:
        data = binary_stl(F.box(), header=b"solid looks like ascii")
        self.assertEqual(read_stl(data, unit="mm").source_format, "binary")

    def test_units_are_guessed_and_can_be_overridden(self) -> None:
        metres = F.stl_bytes(F.box((0.01, 0.02, 0.005)))
        mesh = read_stl(metres)
        self.assertEqual((mesh.unit_guess, mesh.unit, mesh.scale_mm), ("m", "m", 1000.0))
        self.assertAlmostEqual(mesh.stats["extent_mm"][1], 20.0, places=4)
        millimetres = read_stl(F.stl_bytes(F.box()))
        self.assertEqual(millimetres.unit_guess, "mm")
        inches = read_stl(F.stl_bytes(F.box()), unit="in")
        self.assertAlmostEqual(inches.stats["extent_mm"][0], 254.0, places=4)
        with self.assertRaises(SurfaceError) as raised:
            read_stl(metres, unit="furlong")
        self.assertEqual(raised.exception.code, "E_SURFACE_UNIT")

    def test_bad_files_are_rejected_with_their_code(self) -> None:
        cases = {
            b"": "E_SURFACE_MESH_FORMAT",
            b"not an stl at all": "E_SURFACE_MESH_FORMAT",
            b"\0" * 80 + struct.pack("<I", 0): "E_SURFACE_MESH_EMPTY",
            b"\0" * 80 + struct.pack("<I", 5) + b"\0" * 50: "E_SURFACE_MESH_TRUNCATED",
            b"solid x\nfacet normal 0 0 0\nouter loop\nvertex 0 0 0\nvertex 1 0\nendloop\nendfacet\nendsolid": "E_SURFACE_MESH_FORMAT",
            b"solid x\nfacet normal 0 0 0\nouter loop\nvertex 0 0 0\nvertex 1 0 nan\nvertex 0 1 0\nendloop\nendfacet\nendsolid": "E_SURFACE_MESH_NONFINITE",
        }
        nan = bytearray(F.stl_bytes(F.box()))
        nan[84 + 12 : 84 + 16] = struct.pack("<f", math.nan)
        cases[bytes(nan)] = "E_SURFACE_MESH_NONFINITE"
        for data, code in cases.items():
            with self.subTest(data=data[:40]):
                with self.assertRaises(SurfaceError) as raised:
                    read_stl(data, unit="mm")
                self.assertEqual(raised.exception.code, code)
                self.assertIn(raised.exception.code, SURFACE_ERROR_CODES)
        with self.assertRaises(SurfaceError) as raised:
            read_stl(F.stl_bytes(F.box()), unit="mm", max_facets=11)
        self.assertEqual(raised.exception.code, "E_SURFACE_MESH_TOO_LARGE")

    def test_padded_binary_files_are_accepted(self) -> None:
        data = F.stl_bytes(F.box()) + b"\0" * 7
        self.assertEqual(read_stl(data, unit="mm").stats["facets"], 12)

    def test_ascii_solid_names_run_to_the_end_of_their_line(self) -> None:
        # The name may hold any word, 'solid' and 'facet' too (G-R4.10).
        for name in ("Solid Body 1", "Gripper solid finger", "facet test", "part vertex 1 2 3 vertex 4 5 6", ""):
            for newline in ("\n", "\r\n", "\r"):
                with self.subTest(name=name, newline=newline):
                    data = _ascii(F.box(), f"solid {name}", f"endsolid {name}", newline)
                    self.assertEqual(read_stl(data, unit="mm").facets, read_stl(F.stl_bytes(F.box()), unit="mm").facets)
        two = _ascii(F.box(), "solid a solid", "endsolid a solid") + b"\n" + _ascii(F.box((1.0, 1.0, 1.0)), "solid b", "endsolid b")
        self.assertEqual(read_stl(two, unit="mm").stats["facets"], 24)
        self.assertEqual(read_stl(_ascii(F.box(), "solid " + "n" * 4090, "endsolid"), unit="mm").stats["facets"], 12)
        with self.assertRaises(SurfaceError) as raised:
            read_stl(_ascii(F.box(), "solid " + "n" * 5000, "endsolid"), unit="mm")
        self.assertEqual(raised.exception.code, "E_SURFACE_MESH_FORMAT")

    def test_an_ascii_file_written_on_one_line_is_read_by_words(self) -> None:
        # No line follows 'solid': the name runs to 'facet' or 'endsolid', and after 'endsolid' to the
        # next 'solid' (G-R4.10).
        box = read_stl(F.stl_bytes(F.box()), unit="mm").facets
        for separator, end in ((" ", b""), ("\t", b"\n"), (" ", b"\r\n \r\n")):
            with self.subTest(separator=separator, end=end):
                self.assertEqual(read_stl(_ascii(F.box(), "solid part", "endsolid part", separator) + end, unit="mm").facets, box)
        two = _ascii(F.box(), "solid a", "endsolid a", " ") + b" " + _ascii(F.box((1.0, 1.0, 1.0)), "solid b", "endsolid b", " ")
        self.assertEqual(read_stl(two, unit="mm").stats["facets"], 24)
        with self.assertRaises(SurfaceError) as raised:
            read_stl(_ascii(F.box(), "solid " + "n " * 2100, "endsolid", " "), unit="mm")
        self.assertIn("longer than 4096 bytes", raised.exception.message)

    def test_coordinates_beyond_the_bound_are_refused(self) -> None:
        # Squares of 1e154 or more overflow (G-R4.5); the bound applies after the unit scale (G-R2.2).
        cases = [F.ascii_stl([tuple(tuple(c * factor for c in p) for p in t) for t in F.box()]) for factor in (1e76, 1e150, 1e200)]
        cases.append(F.stl_bytes(F.box(), scale=1e30))
        for data in cases:
            with self.subTest(data=data[:60]):
                with self.assertRaises(SurfaceError) as raised:
                    read_stl(data, unit="mm")
                self.assertEqual(raised.exception.code, "E_SURFACE_MESH_NONFINITE")
        far = F.ascii_stl([tuple(tuple(c + 1e7 for c in p) for p in t) for t in F.box()])
        self.assertAlmostEqual(read_stl(far, unit="mm").stats["bbox_mm"][0], 1e7)
        with self.assertRaises(SurfaceError) as raised:
            read_stl(far, unit="m")
        self.assertEqual(raised.exception.code, "E_SURFACE_MESH_NONFINITE")


class TopologyTests(unittest.TestCase):
    def test_an_inside_out_shell_is_oriented_outward(self) -> None:
        inverted = [(a, c, b) for a, b, c in F.box()]
        mesh = read_stl(F.stl_bytes(inverted), unit="mm")
        self.assertEqual(mesh.stats["reversed_facets"], 12)
        self.assertAlmostEqual(mesh.stats["volume_mm3"], 1000.0, places=6)
        # The -z face's normals point down (outward).
        bottom = [f for f in range(12) if abs(mesh.centroids[f][2]) < 1e-9]
        self.assertEqual(len(bottom), 2)
        for facet in bottom:
            self.assertAlmostEqual(mesh.normals[facet][2], -1.0)

    def test_walls_where_two_shells_touch_are_hidden(self) -> None:
        # Two boxes sharing the plane x = 10 over the full 20 x 5 mm face.
        triangles = F.box() + F.box(origin=(10.0, 0.0, 0.0))
        mesh = read_stl(F.stl_bytes(triangles), unit="mm")
        # The boxes share the seam's vertices: one connected assembly.
        self.assertEqual(mesh.stats["shells"], 1)
        self.assertGreater(mesh.stats["nonmanifold_edges"], 0)
        hidden_area = math.fsum(mesh.areas[f] for f in mesh.hidden)
        self.assertAlmostEqual(hidden_area, 2 * 100.0, places=6)
        for facet in mesh.hidden:
            self.assertAlmostEqual(abs(mesh.centroids[facet][0] - 10.0), 0.0, places=9)
            self.assertFalse(mesh.usable(facet))
        # The outer y = 0 faces of both boxes continue across the seam.
        from surface.select import grow, nearest_facet

        seed = nearest_facet(mesh, (5.0, 0.0, 2.5))
        region = grow(mesh, seed, 10.0, 4.0)
        self.assertAlmostEqual(math.fsum(mesh.areas[f] for f in region), 2 * 50.0, places=6)

    def test_a_partly_covered_wall_keeps_its_free_part(self) -> None:
        # A small box on top of a large one: the large top face is covered only in part.
        triangles = F.box((40.0, 40.0, 5.0)) + F.box((10.0, 10.0, 5.0), origin=(5.0, 5.0, 5.0))
        mesh = read_stl(F.stl_bytes(triangles), unit="mm")
        top = [f for f in range(12) if abs(mesh.centroids[f][2] - 5.0) < 1e-9]
        self.assertTrue(all(f not in mesh.hidden for f in top))
        covered = math.fsum(
            abs(sum((p[0] * q[1] - q[0] * p[1]) for p, q in zip(poly, poly[1:] + poly[:1]))) / 2
            for f in top
            for poly in mesh.covered.get(f, [])
        )
        self.assertAlmostEqual(covered, 100.0, places=6)

    def test_an_open_shell_is_oriented_the_same_wherever_it_sits(self) -> None:
        # A box without its top: the outside does not depend on the part's position.
        open_box = [t for t in F.box((10.0, 20.0, 10.0)) if not all(abs(p[2] - 10.0) < 1e-9 for p in t)]
        normals = []
        for shift in (0.0, 100.0, -250.0):
            moved = [tuple((p[0], p[1], p[2] + shift) for p in t) for t in open_box]
            for triangles in (moved, F.reversed_winding(moved)):
                mesh = read_stl(F.stl_bytes(triangles), unit="mm")
                front = next(f for f in range(mesh.facet_count) if abs(mesh.centroids[f][1]) < 1e-9)
                normals.append(tuple(round(c, 9) for c in mesh.normals[front]))
                self.assertEqual(mesh.stats["orientation_ambiguous_shells"], 0)
        self.assertEqual(set(normals), {(0.0, -1.0, 0.0)})
        # A single flat sheet encloses nothing: its file winding is kept and reported.
        sheet = F.box()[2:4]
        for triangles, z in ((sheet, 1.0), (F.reversed_winding(sheet), -1.0)):
            mesh = read_stl(F.stl_bytes(triangles), unit="mm")
            self.assertEqual(mesh.stats["orientation_ambiguous_shells"], 1)
            self.assertAlmostEqual(mesh.normals[0][2], z)

    def test_a_cavity_keeps_its_normals_pointing_into_the_void(self) -> None:
        outer = F.box((20.0, 20.0, 20.0))
        void = F.reversed_winding(F.box((4.0, 4.0, 4.0), origin=(8.0, 8.0, 8.0)))
        for inner, reversed_count in ((void, 0), (F.reversed_winding(void), 12)):
            mesh = read_stl(F.stl_bytes(outer + inner), unit="mm")
            self.assertEqual(mesh.stats["shells"], 2)
            self.assertEqual(mesh.stats["reversed_facets"], reversed_count)
            self.assertAlmostEqual(mesh.stats["volume_mm3"], 8000.0 - 64.0, places=6)

    def test_a_part_inside_an_open_shell_is_not_a_cavity(self) -> None:
        # Only a closed shell encloses anything (G-R4.1).
        cup = [t for t in F.box((40.0, 40.0, 20.0)) if not all(abs(p[2] - 20.0) < 1e-9 for p in t)]
        block = F.box((5.0, 5.0, 5.0), origin=(10.0, 10.0, 5.0))
        for inner, reversed_count in ((block, 0), (F.reversed_winding(block), 12)):
            mesh = read_stl(F.stl_bytes(cup + inner), unit="mm")
            self.assertEqual(mesh.stats["shells"], 2)
            self.assertEqual(mesh.stats["reversed_facets"], reversed_count)
            self.assertAlmostEqual(_top_normal_z(mesh, (12.5, 12.5, 10.0)), 1.0)

    def test_a_part_touching_a_pocket_wall_is_not_a_cavity(self) -> None:
        # The block's first vertex lies on the pocket's +x wall and floor (its +x face comes first in
        # the file): the parity is taken from points inside the block (G-R4.1).
        block = F.box((5.0, 6.0, 4.0), origin=(25.0, 12.0, 10.0))
        mesh = read_stl(F.stl_bytes(_pocket_block() + block[6:8] + block[:6] + block[8:]), unit="mm")
        self.assertEqual(mesh.stats["shells"], 2)
        self.assertEqual(mesh.stats["reversed_facets"], 0)
        self.assertAlmostEqual(_top_normal_z(mesh, (27.5, 15.0, 14.0)), 1.0)
        self.assertAlmostEqual(mesh.stats["volume_mm3"], 28000.0 + 120.0, places=6)

    def test_a_part_resting_in_a_cavity_is_not_a_cavity(self) -> None:
        # Its box touches the cavity's box: a box on the other's faces counts as inside, and the
        # parity decides (G-R4.1).
        outer = F.box((100.0, 100.0, 100.0))
        void = F.reversed_winding(F.box((60.0, 60.0, 60.0), origin=(20.0, 20.0, 20.0)))
        for origin in ((30.0, 30.0, 20.0), (20.0, 30.0, 30.0), (70.0, 30.0, 30.0)):
            with self.subTest(origin=origin):
                mesh = read_stl(F.stl_bytes(outer + void + F.box((10.0, 10.0, 10.0), origin=origin)), unit="mm")
                self.assertEqual(mesh.stats["reversed_facets"], 0)
                self.assertAlmostEqual(mesh.stats["volume_mm3"], 1e6 - 216000.0 + 1000.0, places=4)

    def test_a_float_noise_gap_does_not_open_an_enclosing_body(self) -> None:
        # The sphere's south-pole and seam vertices are about 1e-15 mm apart: its open edges have twins,
        # so it still encloses its cavity; a missing facet is a hole (G-R5.4).
        sphere = _uv_sphere(20.0, 12, 16)
        void = F.box((4.0, 4.0, 4.0), origin=(-2.0, -2.0, -2.0))  # written outward
        alone = read_stl(F.stl_bytes(sphere), unit="mm")
        self.assertGreater(alone.stats["boundary_edges"], 0)
        mesh = read_stl(F.stl_bytes(sphere + void), unit="mm")
        self.assertEqual(mesh.stats["reversed_facets"], alone.stats["reversed_facets"] + 12)
        self.assertAlmostEqual(mesh.stats["volume_mm3"], alone.stats["volume_mm3"] - 64.0, places=4)
        holed = read_stl(F.stl_bytes(sphere[1:] + void), unit="mm")
        self.assertEqual(holed.stats["reversed_facets"], read_stl(F.stl_bytes(sphere[1:]), unit="mm").stats["reversed_facets"])

    def test_many_parts_side_by_side_stay_within_the_nesting_budget(self) -> None:
        # 600 parts whose boxes overlap along x but not along y: the candidate sweep runs along y (G-R4.6).
        outer = F.box((20.0, 20.0, 20.0))
        void = F.reversed_winding(F.box((4.0, 4.0, 4.0), origin=(8.0, 8.0, 8.0)))
        parts = [t for k in range(600) for t in F.box((1.0, 1.0, 1.0), origin=(30.0 + k * 1e-3, 3.0 * k, 0.0))]
        with mock.patch.object(mesh_module, "MAX_NESTING_TESTS", 50_000):
            mesh = read_stl(F.stl_bytes(outer + void + parts), unit="mm")
        self.assertEqual(mesh.stats["reversed_facets"], 0)
        self.assertNotIn("warning", mesh.stats)
        self.assertLess(mesh.stats["_nesting_tests"], 5_000)

    def test_an_inside_out_body_sharing_a_face_is_turned_outward(self) -> None:
        # The coincident contact walls run the same way: no link across them (G-R4.2).
        from surface.select import grow, nearest_facet

        a, b = F.box((10.0, 10.0, 5.0)), F.box((10.0, 10.0, 5.0), origin=(10.0, 0.0, 0.0))
        for triangles in (a + F.reversed_winding(b), F.reversed_winding(a) + b, a + F.reversed_winding(F.box((30.0, 10.0, 5.0), origin=(10.0, 0.0, 0.0)))):
            mesh = read_stl(F.stl_bytes(triangles), unit="mm")
            self.assertEqual(mesh.stats["reversed_facets"], 12)
            self.assertEqual((mesh.stats["shells"], mesh.stats["hidden_facets"]), (1, 4))
            for x in (5.0, 15.0):
                self.assertAlmostEqual(_top_normal_z(mesh, (x, 5.0, 5.0)), 1.0)
            # The top faces continue across the seam.
            top = grow(mesh, nearest_facet(mesh, (5.0, 5.0, 5.0)), 10.0, 4.0)
            self.assertAlmostEqual(math.fsum(mesh.areas[f] for f in top), mesh.stats["extent_mm"][0] * 10.0, places=6)

    def test_an_inside_out_body_repeating_the_contact_facets_is_turned_outward(self) -> None:
        # Its contact facets repeat the other body's triangle for triangle (a part and its mirror
        # image): they are kept, turned with their body and hidden (G-R4.2).
        from surface.select import grow, nearest_facet

        a, b = F.box((10.0, 10.0, 5.0)), F.box((10.0, 10.0, 5.0), origin=(0.0, 0.0, 5.0))
        part = F.box((10.0, 6.0, 4.0))
        mirrored = [tuple((20.0 - p[0], p[1], p[2]) for p in t) for t in part]  # inside-out, as mirroring leaves it
        cases = (
            (a + F.reversed_winding(b), (5.0, 5.0, 10.0), (5.0, 0.0, 2.5), 100.0),
            (F.reversed_winding(a) + b, (5.0, 5.0, 0.0), (5.0, 0.0, 2.5), 100.0),
            (part + mirrored, (15.0, 3.0, 4.0), (5.0, 3.0, 4.0), 120.0),
        )
        for triangles, outer, seed, area in cases:
            with self.subTest(outer=outer):
                mesh = read_stl(F.stl_bytes(triangles), unit="mm")
                stats = mesh.stats
                self.assertEqual((stats["duplicate_facets"], stats["hidden_facets"], stats["reversed_facets"], stats["shells"]), (0, 4, 12, 1))
                self.assertAlmostEqual(_top_normal_z(mesh, outer), 1.0 if outer[2] > 0 else -1.0)
                region = grow(mesh, nearest_facet(mesh, seed), 10.0, 4.0)
                self.assertAlmostEqual(math.fsum(mesh.areas[f] for f in region), area, places=6)

    def test_coincident_walls_facing_the_same_way_stay_as_written(self) -> None:
        # A body repeated with another triangulation, and a patch lying on a face: no facet beside the
        # walls shows a wrong winding, so no wall is turned round (and none hidden) (G-R4.2).
        box, again = F.box(), _other_diagonals(F.box())
        patch = [t for t in again if all(abs(p[2] - 5.0) < 1e-9 for p in t)]
        cases = ((box + again, 0), (F.reversed_winding(box + again), 24), (box + patch, 0), (patch + box, 0))
        for triangles, reversed_count in cases:
            with self.subTest(facets=len(triangles), reversed=reversed_count):
                mesh = read_stl(F.stl_bytes(triangles), unit="mm")
                stats = mesh.stats
                self.assertEqual(
                    (stats["reversed_facets"], stats["hidden_facets"], stats["shells"], stats["orientation_ambiguous_shells"]), (reversed_count, 0, 1, 0)
                )
                top = [f for f in range(mesh.facet_count) if abs(mesh.centroids[f][2] - 5.0) < 1e-9]
                self.assertEqual(len(top), 4)
                for facet in top:
                    self.assertTrue(mesh.usable(facet))
                    self.assertAlmostEqual(mesh.normals[facet][2], 1.0)

    def test_touching_bodies_turned_in_space_stay_one_shell(self) -> None:
        # Rounding breaks the angle tie of the coincident walls either way; each body's facet next to
        # them is linked to its own wall whatever the order (G-R4.2).
        a, b = F.box((10.0, 10.0, 5.0)), F.box((10.0, 10.0, 5.0), origin=(10.0, 0.0, 0.0))
        for degrees in ((5, 5, 15), (5, 15, 45), (35, 25, 65)):
            for triangles in (a + b, a + F.reversed_winding(b)):
                with self.subTest(degrees=degrees, facets=len(triangles)):
                    mesh = read_stl(F.stl_bytes(_rotated(triangles, degrees)), unit="mm")
                    self.assertEqual((mesh.stats["shells"], mesh.stats["hidden_facets"]), (1, 4))

    def test_a_cavity_in_a_body_touching_an_inside_out_body_faces_its_void(self) -> None:
        # The bodies touching over a face make one closed body for the cavity test (G-R4.2, G-R4.1).
        a = F.box((20.0, 20.0, 20.0))
        void = F.reversed_winding(F.box((6.0, 6.0, 6.0), origin=(7.0, 7.0, 7.0)))
        b = F.reversed_winding(F.box((20.0, 20.0, 20.0), origin=(20.0, 0.0, 0.0)))
        for triangles in (a + void + b, b + a + void):
            mesh = read_stl(F.stl_bytes(triangles), unit="mm")
            self.assertEqual((mesh.stats["shells"], mesh.stats["reversed_facets"], mesh.stats["hidden_facets"]), (2, 12, 4))
            self.assertAlmostEqual(mesh.stats["volume_mm3"], 16000.0 - 216.0, places=6)
            self.assertAlmostEqual(_top_normal_z(mesh, (10.0, 10.0, 13.0)), -1.0)  # the void's ceiling

    def test_cavities_are_found_among_many_shells(self) -> None:
        # No shell count turns the cavity test off (G-R4.6).
        outer = F.box((20.0, 20.0, 20.0))
        void = F.reversed_winding(F.box((4.0, 4.0, 4.0), origin=(8.0, 8.0, 8.0)))
        parts = [t for k in range(31) for t in F.box((1.0, 1.0, 1.0), origin=(30.0 + 2 * k, 0.0, 0.0))]
        mesh = read_stl(F.stl_bytes(outer + void + parts), unit="mm")
        self.assertEqual(mesh.stats["shells"], 33)
        self.assertEqual(mesh.stats["reversed_facets"], 0)
        self.assertAlmostEqual(mesh.stats["volume_mm3"], 8000.0 - 64.0 + 31.0, places=6)

    def test_one_pass_over_an_enclosing_shell_serves_all_parts_inside(self) -> None:
        # 31 cavities in a finely tessellated part: about one test per facet of the part, not one
        # pass of it per cavity (G-R5.4).
        part = _grid_box(60)
        voids = [t for k in range(31) for t in F.box((2.0, 2.0, 2.0), origin=(5.0 + 3 * k, 2.5 + 3 * k, 4.0))]
        mesh = read_stl(F.stl_bytes(part + voids), unit="mm")
        self.assertEqual((mesh.stats["shells"], mesh.stats["reversed_facets"]), (32, 31 * 12))
        self.assertLess(mesh.stats["_nesting_tests"], 3 * len(part))
        self.assertNotIn("_nesting_tests", mesh.summary())

    def test_a_flat_sheet_far_from_the_origin_keeps_its_winding(self) -> None:
        # The float32 rounding of a tilted plane at 3 m encloses a volume above the old threshold (G-R4.8).
        sheet = _tilted_sheet(4, 40.0, 31.0, (3000.0, 2000.0, 1000.0))
        for triangles in (sheet, F.reversed_winding(sheet)):
            mesh = read_stl(F.stl_bytes(triangles), unit="mm")
            self.assertEqual((mesh.stats["orientation_ambiguous_shells"], mesh.stats["reversed_facets"]), (1, 0))

    def test_a_curved_sheet_far_from_the_origin_keeps_its_outside(self) -> None:
        # A slightly curved sheet encloses far more than its float32 rounding: it is oriented by its
        # volume wherever it sits, whatever the file's winding (G-R4.8).
        for offset in (0.0, 1000.0):
            sheet = _saddle(offset)
            upward = set()
            for triangles in (sheet, F.reversed_winding(sheet)):
                mesh = read_stl(F.stl_bytes(triangles), unit="mm")
                self.assertEqual(mesh.stats["orientation_ambiguous_shells"], 0)
                upward.add(mesh.normals[0][2] > 0)
            self.assertEqual(len(upward), 1, offset)

    def test_a_small_part_keeps_its_walls(self) -> None:
        # A part in metres read as mm: the covered-wall tolerances shrink with it, so its sides
        # 0.04 mm apart are not taken for touching walls, and the unit is questioned (G-R2.6).
        part = F.stl_bytes(F.box((0.04, 0.2, 0.03)))
        small = read_stl(part, unit="mm")
        self.assertEqual((small.stats["hidden_facets"], small.stats["partly_covered_facets"]), (0, 0))
        self.assertIn("check the unit", small.stats["warning"])
        metres = read_stl(part, unit="m")
        self.assertEqual(metres.stats["hidden_facets"], 0)
        self.assertNotIn("warning", metres.stats)

    def test_a_t_junction_does_not_split_a_face(self) -> None:
        from surface import chart as chart_module
        from surface.select import grow, nearest_facet

        mesh = read_stl(F.stl_bytes(F.t_junction_box()), unit="mm")
        self.assertTrue(mesh.stats["watertight"])
        self.assertEqual(mesh.stats["t_junction_links"], 2)
        top = grow(mesh, nearest_facet(mesh, (5.0, 30.0, 10.0)), 10.0, 4.0)
        self.assertAlmostEqual(math.fsum(mesh.areas[f] for f in top), 1200.0, places=6)
        chart = chart_module.build_chart(mesh, top)
        self.assertEqual((chart.kind, len(chart.loops), chart.stats["topology"]["disk"]), ("planar", 1, True))
        self.assertAlmostEqual(chart_module._loop_area(chart.outline()), 1200.0, places=6)

    def test_pathological_files_stay_fast(self) -> None:
        import time

        # The same triangle 3000 times, and 3000 different triangles on one edge.
        one = F.box()[0]
        fan = [((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (5.0, math.cos(k / 500), math.sin(k / 500))) for k in range(3000)]
        for triangles in (F.box() + [one] * 3000, fan):
            started = time.perf_counter()
            mesh = read_stl(F.stl_bytes(triangles), unit="mm")
            self.assertLess(time.perf_counter() - started, 5.0)
            self.assertLessEqual(max(len(n) for n in mesh.neighbors), 4)
        self.assertEqual(read_stl(F.stl_bytes(F.box() + [one] * 3000), unit="mm").stats["duplicate_facets"], 3000)

    def test_the_mesh_is_a_deterministic_function_of_the_bytes(self) -> None:
        data = F.stl_bytes(F.soft_finger_replica())
        first, second = read_stl(data, unit="mm"), read_stl(data, unit="mm")
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual((first.vertices, first.facets, first.normals), (second.vertices, second.facets, second.normals))


class BoundTests(unittest.TestCase):
    """Pathological files stay bounded, and ordinary ones stay within the bounds."""

    def test_long_open_edges_among_tiny_ones_stay_fast(self) -> None:
        # 0.01 mm triangles set a fine grid; 50 mm edges are walked on a coarser one (G-R4.3).
        triangles = [((1.0 * k, 0.0, 0.0), (1.0 * k + 0.01, 0.0, 0.0), (1.0 * k, 0.01, 0.0)) for k in range(400)]
        triangles += [((0.0, 5.0 + k, 5.0), (50.0, 5.0 + k, 5.0), (0.0, 5.5 + k, 5.0)) for k in range(100)]
        started = time.perf_counter()
        mesh = read_stl(F.stl_bytes(triangles), unit="mm")
        self.assertLess(time.perf_counter() - started, 2.0)
        self.assertEqual(mesh.stats["boundary_edges"], 1500)
        self.assertNotIn("warning", mesh.stats)

    def test_a_dense_crack_among_long_open_edges_is_repaired(self) -> None:
        # 100 crack vertices on 2 mm, with a median open edge of 50 mm: a cell crowded on the median's
        # grid is walked again on finer ones before it counts as one spot (G-R4.3).
        from surface.select import grow, nearest_facet

        long = [((0.0, 10.0 + k, 0.0), (50.0, 10.0 + k, 0.0), (0.0, 10.5 + k, 0.0)) for k in range(300)]
        mesh = read_stl(F.stl_bytes(long + _dense_crack(100, 2.0, (200.0, 0.0))), unit="mm")
        self.assertEqual(mesh.stats["t_junction_links"], 100)
        self.assertNotIn("warning", mesh.stats)
        patch = grow(mesh, nearest_facet(mesh, (200.5, 1.0, 0.0)), 10.0, 4.0)
        self.assertAlmostEqual(math.fsum(mesh.areas[f] for f in patch), 4.0, places=6)

    def test_stacked_facets_are_clipped_once(self) -> None:
        # Hundreds of coplanar facets of both orientations on one spot: a hidden facet is not clipped again (G-R4.4).
        triangles = []
        for k in range(150):
            d = k * 1e-4
            triangles += [((d, 0.0, 0.0), (10.0, d, 0.0), (0.0, 10.0, 0.0)), ((d, 0.0, 0.0), (0.0, 10.0 - d, 0.0), (10.0, 0.0, 0.0))]
        with mock.patch.object(mesh_module, "_coplanar_overlap", wraps=mesh_module._coplanar_overlap) as clip:
            mesh = read_stl(F.stl_bytes(triangles), unit="mm")
        self.assertEqual(mesh.stats["hidden_facets"], 300)
        self.assertLessEqual(clip.call_count, 2 * len(triangles))

    def test_a_finely_tessellated_contact_wall_counts_only_overlapping_pairs(self) -> None:
        # Two stacked boxes with 20 x 20 and 17 x 17 grids on the contact faces: about 3,300 pairs
        # overlap, 5,800 touch by their boxes.  Only the first count against the bound (G-R5.3).
        triangles = _grid_box(20, (20.0, 20.0, 5.0)) + _grid_box(17, (20.0, 20.0, 5.0), (0.0, 0.0, 5.0))
        with mock.patch.object(mesh_module, "MAX_COVER_PAIRS", 4500):
            mesh = read_stl(F.stl_bytes(triangles), unit="mm")
        wall = [f for f in range(mesh.facet_count) if abs(mesh.centroids[f][2] - 5.0) < 1e-9]
        self.assertEqual(len(wall), 2 * (20 * 20 + 17 * 17))
        self.assertTrue(all(f in mesh.hidden for f in wall))
        self.assertNotIn("warning", mesh.stats)

    def test_too_many_open_edges_give_a_warning(self) -> None:
        # The T-junction search is not silently skipped (G-R4.7).
        soup = [((100.0 + k, 0.0, 0.0), (100.6 + k, 0.0, 0.0), (100.0 + k, 0.6, 0.0)) for k in range(10)]
        with mock.patch.object(mesh_module, "MAX_CRACK_EDGES", 20):
            mesh = read_stl(F.stl_bytes(F.t_junction_box() + soup), unit="mm")
        self.assertEqual(mesh.stats["t_junction_links"], 0)
        self.assertIn("More than 20 open edges", mesh.stats["warning"])

    def test_unrelated_open_parts_leave_a_crack_repaired(self) -> None:
        # 400 separate open triangles after a cracked box: the search spends a few tests per edge, and
        # when its budget runs out the repairs found so far stay, with a warning that says so (G-R5.2).
        from surface.select import grow, nearest_facet

        soup = []
        for k in range(400):
            x, y = 100.0 + (k % 20) * 1.0, (k // 20) * 1.0
            soup.append(((x, y, 0.0), (x + 0.6, y, 0.0), (x, y + 0.6, 0.0)))
        for budget, warned in ((10_000, False), (1_000, True)):
            with mock.patch.object(mesh_module, "MAX_CRACK_TESTS", budget):
                mesh = read_stl(F.stl_bytes(F.t_junction_box() + soup), unit="mm")
            self.assertEqual(mesh.stats["t_junction_links"], 2)
            top = grow(mesh, nearest_facet(mesh, (5.0, 30.0, 10.0)), 10.0, 4.0)
            self.assertAlmostEqual(math.fsum(mesh.areas[f] for f in top), 1200.0, places=6)
            if warned:
                self.assertIn(f"stopped after {budget} tests", mesh.stats["warning"])
                self.assertNotIn("one spot", mesh.stats["warning"])
            else:
                self.assertNotIn("warning", mesh.stats)


class BrowserParserTests(unittest.TestCase):
    """web/cad/stl.js reads the facets the server reads (G-R4.10)."""

    CASES = {
        "plain": _ascii(F.box()[:3]),
        "solid word": _ascii(F.box()[:3], "solid Gripper solid finger", "endsolid Gripper solid finger"),
        "Solid Body 1, CRLF": _ascii(F.box()[:3], "solid Solid Body 1", "endsolid Solid Body 1", "\r\n"),
        "facet word, CR": _ascii(F.box()[:3], "solid facet test", "endsolid facet test", "\r"),
        "BOM, unicode name": b"\xef\xbb\xbf" + _ascii(F.box()[:3], "solid Gr\u00fc\u00dfe \u5f62", "endsolid"),
        "two solids": _ascii(F.box()[:3], "solid a", "endsolid a") + b"\n" + _ascii(F.box()[3:5], "solid b solid", "endsolid b solid"),
        "name of 4096 bytes": _ascii(F.box()[:3], "solid " + "\u00e9" * 2047 + "n", "endsolid"),
        "name of 4097 bytes": _ascii(F.box()[:3], "solid " + "\u00e9" * 2048, "endsolid"),
        "one line": _ascii(F.box()[:3], newline=" "),
        "one line, tabs, a newline at the end": _ascii(F.box()[:3], newline="\t") + b"\n",
        "one line, two solids": _ascii(F.box()[:3], "solid a", "endsolid a", " ") + b" " + _ascii(F.box()[3:5], "solid b", "endsolid b", " "),
        "no-break space in a number": _ascii(F.box()[:3]).replace(b"vertex 0.0", b"vertex \xc2\xa00.0", 1),
        "inf in a normal": _ascii(F.box()[:3]).replace(b"facet normal 0 0 0", b"facet normal inf 0 0", 1),
    }
    REFUSED = {"name of 4097 bytes", "no-break space in a number", "inf in a normal"}

    def test_the_name_limit_is_the_server_limit(self) -> None:
        found = re.search(r"const MAX_NAME_BYTES = (\d+);", STL_JS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual(int(found.group(1)), mesh_module._MAX_NAME_BYTES)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_both_parsers_read_the_same_facets(self) -> None:
        driver = (
            'import {parseStl} from "./stl.mjs";\nimport {readFileSync} from "node:fs";\nconst out = [];\n'
            "for (const path of process.argv.slice(2)) {\n  const bytes = readFileSync(path);\n"
            "  try { out.push(Array.from(parseStl(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)).positions)); }\n"
            "  catch (error) { out.push(null); }\n}\nconsole.log(JSON.stringify(out));\n"
        )
        with tempfile.TemporaryDirectory() as folder:
            shutil.copy(STL_JS, Path(folder) / "stl.mjs")
            (Path(folder) / "driver.mjs").write_text(driver, encoding="utf-8")
            paths = []
            for index, data in enumerate(self.CASES.values()):
                paths.append(str(Path(folder) / f"case{index}.stl"))
                Path(paths[-1]).write_bytes(data)
            run = subprocess.run(["node", "driver.mjs", *paths], cwd=folder, capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        browser = json.loads(run.stdout)
        for (label, data), positions in zip(self.CASES.items(), browser):
            with self.subTest(case=label):
                try:
                    mesh = read_stl(data, unit="mm")
                except SurfaceError:
                    self.assertIsNone(positions)
                    continue
                self.assertEqual(positions, [c for f in mesh.facets for v in f for c in mesh.vertices[v]])
        self.assertEqual({label for label, positions in zip(self.CASES, browser) if positions is None}, self.REFUSED)


@unittest.skipUnless((ASSETS / "soft_gripper_finger.stl").exists(), "asset/ meshes are not committed")
class AssetTests(unittest.TestCase):
    def test_the_example_meshes(self) -> None:
        soft = read_stl((ASSETS / "soft_gripper_finger.stl").read_bytes())
        self.assertEqual((soft.unit, soft.stats["facets"], soft.stats["vertices"]), ("m", 1944, 936))
        self.assertAlmostEqual(soft.stats["volume_mm3"], 46981.4, delta=0.1)
        crank = read_stl((ASSETS / "crank_gripper" / "tip_left.stl").read_bytes())
        self.assertEqual((crank.stats["facets"], crank.stats["shells"]), (8000, 2))
        self.assertGreater(crank.stats["hidden_facets"], 0)


if __name__ == "__main__":
    unittest.main()
