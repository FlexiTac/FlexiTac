"""Gently curved faces (the user's decisions of 2026-11-17; docs/CAD_MODE.md "Gently curved faces").

The user's report of 2026-11-17 on the Unitree Dex3-1 fingertip (a jagged selection, a diamond of taxels with gaps, the
purple marks inside the dome) had five root causes (the study's RC1-RC5), each pinned here:

- RC1: the select presets stopped at sharp edges, not at stretch: a click on a smooth dome took the whole cap (refused)
  or a staircase cone.  Now the Surface click at the strain limit selects, on a doubly curved face, the face when it
  fits whole, else the largest patch round the dome within it, the same symmetric patch from any click on that patch
  (a click off it: the largest round the click), never one beyond the limit, its outline drawn clean; planar and
  developable faces as before (StretchSelectionTests; the review of 2026-11-17's findings 1, 3, 4 and 5).
- RC2: the fit silently replaced a curved selection beyond the limit by a geodesic disk round the click (about a third
  of it, never drawn).  Now it fits the whole selection or refuses it, saying how much fits round the click (Shrink to
  fit); the region fitted is the region drawn (WholeSelectionTests).
- RC3: the disk was sized by the worst single facet of an ARAP chart.  Now a curved chart is the least-max-stretch one
  (surface.solve.bounded: about the least possible on analytic caps, a^2 / 12), on which the lattice is laid, and it is
  judged by the stretch the sheet keeps on the part: the relaxed sheet's (ARAP's chart: soft tape creeps to it, a^2 / 8
  at a cap's rim; the review of 2026-11-17's finding 2), smoothed over 1 mm (SolverTests).
- RC4: a diamond field of whole facets, turned against the base.  An elongated doubly curved selection lays its lattice
  along its axis, unturned (WholeSelectionTests).
- RC5: the exits and purple marks were the hidden disk's.  Now the boards leave the surface on the selection's own
  edge (WholeSelectionTests).

The user's feedback of 2026-11-17 on the preview (a stepped, lopsided selection on the dome, its flattest part only) and their
choice of 1 % on curved faces: a face's mirror planes are found on the mesh and every patch the stretch search tries is taken
with its mirror image where the two make one piece, so the dome's patch is symmetric and the same from every click on it, its
field symmetric and centred (MirrorSymmetryTests; the page's 1 % is test_surface_web's and the browser checks').

The charts are pinned by digest (the same on Python 3.9 to 3.12 and in Pyodide 0.27.8, measured 2026-11-17), and the
stack the bend rules follow is the order profile's (StackTests).  Under Whole board the taxel field keeps the laminated
field's bend rule and the boards around it take one board's (the lead's decision of 2026-11-18, WholeBoardBendTests).
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import unittest
from pathlib import Path

from engine import generate_design
from surface import api, fieldfit, fill, fit, place, select, solve
from surface import chart as chart_module
from surface.errors import SurfaceError

try:
    import surface_fixtures as F
except ImportError:  # run as a package
    from tests import surface_fixtures as F

ROOT = Path(__file__).resolve().parents[1]
MESHES = ROOT / "web" / "library" / "meshes"
# The Dex3-1's fingertip, a fixture of its own since the hand left the Library (2026-11-17; its notice beside it).
DEX3 = ROOT / "tests" / "fixtures" / "unitree-dex3.stl"
# The user's selection of 2026-11-17 (Custom 30 / 30 / 4 on the palmar dome) and their base point.
USER_OPS = [{"op": "grow", "mode": "add", "seed_facet": 10926, "theta_d_deg": 30, "theta_c_deg": 30, "min_radius_mm": 4}]
USER_BASE = {"point_xyz": [20.9517275, -7.7360475, 7.490045]}
# The page's options of a click (Generate sensor), at the default tier.
PAGE = {"pitch_mm": 2, "fill": 0.5, "row_sides": "both", "tail_extension_mm": 20, "max_rows": 32, "max_columns": 32, "containment": "field",
        "strain_limit": 0.003}
# Clicks on the Dex3-1's palmar dome within its patch at 0.3 % (its base, its middle, either side of its mirror plane z = 0)
# and clicks off it (its side, its tip end, the far side: the review of 2026-11-17's finding 3).
DOME_CLICKS = (10926, 8826, 7923, 11741)
OFF_CLICKS = (7888, 7891, 11576, 13484)


def click(seed: int, budget: float = 0.003) -> list:
    """The page's click with the Surface preset at a strain limit (web/cad/main.js growOp)."""

    return [{"op": "grow", "mode": "add", "seed_facet": seed, "preset": "surface", "stretch_budget": budget}]


def uv_digest(chart) -> str:
    digest = hashlib.sha256()
    for vertex in sorted(chart.uv):
        digest.update(struct.pack("<idd", vertex, *chart.uv[vertex]))
    return digest.hexdigest()[:16]


class _Dex3:
    """The Dex3-1 fingertip's mesh and bytes, read once."""

    _cache: dict = {}

    @classmethod
    def get(cls) -> tuple:
        if not cls._cache:
            data = DEX3.read_bytes()
            cls._cache["value"] = (data, api.load_mesh({}, data))
        return cls._cache["value"]


def cone_band(radius_low: float, radius_high: float, height: float, sweep_deg: float, segments: int, rows: int) -> list:
    """An open band of a cone (outward normals): radius_low at z 0 to radius_high at z height, over sweep_deg."""

    def point(i: int, j: int) -> tuple:
        phi = math.radians(sweep_deg) * j / segments
        r = radius_low + (radius_high - radius_low) * i / rows
        return (r * math.cos(phi), r * math.sin(phi), height * i / rows)

    triangles = []
    for i in range(rows):
        for j in range(segments):
            a, b, c, d = point(i, j), point(i, j + 1), point(i + 1, j), point(i + 1, j + 1)
            triangles.append((a, b, d))
            triangles.append((a, d, c))
    return triangles


def saddle(radius: float, half: float, step_x: float, step_y: float) -> list:
    """z = (x^2 - y^2) / 2R over a square of half-width ``half``, quads of step_x by step_y split in two (step_x 4 and
    step_y 0.25: a CAD exporter's long strips)."""

    nx, ny = int(round(2 * half / step_x)), int(round(2 * half / step_y))

    def point(i: int, j: int) -> tuple:
        x, y = -half + 2 * half * i / nx, -half + 2 * half * j / ny
        return (x, y, (x * x - y * y) / (2 * radius))

    triangles = []
    for i in range(nx):
        for j in range(ny):
            a, b, c, d = point(i, j), point(i + 1, j), point(i, j + 1), point(i + 1, j + 1)
            triangles += [(a, b, d), (a, d, c)]
    return triangles


def concave_turns(outline: list, degrees: float = 30.0) -> int:
    """The outline's (counter-clockwise) turns inwards of more than ``degrees``: its staircase's inner corners."""

    count = 0
    for k in range(len(outline)):
        a, b, c = outline[k - 1], outline[k], outline[(k + 1) % len(outline)]
        u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
        if math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]) < -math.radians(degrees):
            count += 1
    return count


def judged(mesh, patch) -> float:
    """The patch's stretch as the fit judges it (0 on a planar or developable chart, which the fit masks facet by facet)."""

    chart = chart_module.build_chart(mesh, patch)
    return chart_module.judged_stretch(chart, mesh) if chart.kind == "curved" else 0.0


class StretchSelectionTests(unittest.TestCase):
    """RC1: a click selects by stretch on a doubly curved face, the same symmetric patch from anywhere on the dome."""

    def test_a_click_anywhere_on_a_dome_s_patch_selects_that_symmetric_patch(self) -> None:
        _, mesh = _Dex3.get()
        patches = {seed: frozenset(select.apply_operations(mesh, click(seed))) for seed in DOME_CLICKS}
        self.assertEqual(len(set(patches.values())), 1, {seed: len(patch) for seed, patch in patches.items()})
        patch = patches[DOME_CLICKS[0]]
        self.assertTrue(set(DOME_CLICKS) <= patch)
        # The Surface preset's own region there: the whole fingertip, with holes (refused: E_SURFACE_NOT_DISK).
        face = select.grow(mesh, 10926, 30.0, 180.0, 4.0)
        self.assertTrue(select.doubly_curved(mesh, face))
        self.assertLess(len(patch), len(face))
        self.assertTrue(patch <= face)
        # Mirror-symmetric as the hull is (z -> -z): every facet's mirror image is a facet of the patch.
        centres = {tuple(round(c, 4) for c in mesh.centroids[f]) for f in patch}
        mirrored = {(x, y, round(-z, 4) + 0.0) for x, y, z in centres}
        self.assertEqual(mirrored, {(x, y, z + 0.0) for x, y, z in centres})
        chart = chart_module.build_chart(mesh, patch)
        self.assertEqual((chart.kind, chart.stats["topology"]["disk"]), ("curved", True))
        stretch = chart_module.judged_stretch(chart, mesh)
        self.assertLessEqual(stretch, 0.003)
        self.assertGreater(stretch, 0.9 * 0.003)  # the regula falsi brings it close to the limit
        self.assertEqual((len(patch), round(chart.stats["area_mm2"], 3)), (438, 238.849))

    def test_a_click_off_the_dome_s_patch_selects_round_the_click(self) -> None:
        # The review of 2026-11-17 (finding 3): a click on the fingertip's side or tip end selected the palmar patch,
        # which did not hold it, and a second click there added nothing.  Now the patch round the click, within the limit.
        _, mesh = _Dex3.get()
        dome = frozenset(select.apply_operations(mesh, click(DOME_CLICKS[0])))
        for seed in OFF_CLICKS:
            for budget in (0.003, 0.01):
                with self.subTest(seed=seed, budget=budget):
                    patch = select.apply_operations(mesh, click(seed, budget))
                    self.assertIn(seed, patch)
                    self.assertLessEqual(judged(mesh, patch), budget)
                    if budget == 0.003:
                        self.assertNotIn(seed, dome)
                        self.assertNotEqual(frozenset(patch), dome)

    def test_a_patch_is_never_beyond_the_limit(self) -> None:
        # The review of 2026-11-17 (finding 1): when the first guess overshot and the next cone gave the same patch, the
        # patch beyond the limit came back (the fit then refused it, and Shrink to fit selected it again).  Now the
        # widest patch within the limit, at both tiers, Surface's click and Shrink to fit alike (preset stretch).
        cap = F.mesh(F.sphere_cap(30.0, 30.0, rings=24, segments=72))
        piper = api.load_mesh({}, (MESHES / "agilex-piper.stl").read_bytes())
        cases = {
            "cap 24 x 72": (cap, select.nearest_facet(cap, (0.0, 0.0, 30.0))),
            "saddle": (F.mesh(saddle(30.0, 10.0, 0.5, 0.5)), None),
            "saddle in strips": (F.mesh(saddle(30.0, 10.0, 4.0, 0.25)), None),
            "AgileX Piper 60": (piper, 60),
            "AgileX Piper 920": (piper, 920),
        }
        lat_long = F.mesh(F.sphere_cap(20.0, 25.0, rings=8, segments=24))
        cases["coarse cap 8 x 24"] = (lat_long, select.nearest_facet(lat_long, (0.0, 0.0, 20.0)))
        # Where the face reaches beyond both tiers, the patch reaches 0.7 of the limit: not a patch the search gave up on
        # (a cone giving the patch beyond the limit again is moved to a narrower patch of its own, not ended).
        near = {"cap 24 x 72", "saddle", "saddle in strips", "coarse cap 8 x 24"}
        for name, (mesh, seed) in cases.items():
            if seed is None:
                seed = select.nearest_facet(mesh, (0.0, 0.0, 0.0))
            for preset in ("surface", "stretch"):
                for budget in (0.003, 0.01):
                    with self.subTest(face=name, preset=preset, budget=budget):
                        patch = select.apply_operations(mesh, click(seed, budget) if preset == "surface" else
                                                        [{"op": "grow", "seed_facet": seed, "preset": "stretch", "stretch_budget": budget}])
                        self.assertIn(seed, patch)
                        self.assertLessEqual(judged(mesh, patch), budget)
                        if name in near:
                            self.assertGreater(judged(mesh, patch), 0.7 * budget)

    def test_a_face_within_the_limit_is_selected_whole(self) -> None:
        # The review of 2026-11-17 (finding 4): the AgileX Piper's facet 1008 grows a face of 24 facets within 1 %; a cone
        # grown from its centre did not reach the click (grow tests the bend of the facet it enters, and the click's own
        # facet is tighter than 4 mm), and a patch of 4 facets elsewhere came back.
        mesh = api.load_mesh({}, (MESHES / "agilex-piper.stl").read_bytes())
        face = select.grow(mesh, 1008, 30.0, 180.0, 4.0)
        self.assertTrue(select.doubly_curved(mesh, face))
        self.assertEqual(select.apply_operations(mesh, click(1008, 0.01)), face)
        self.assertIn(1008, select.apply_operations(mesh, click(1008, 0.003)))
        # The face's graph is undirected: the cone from any facet reaches the click.
        graph = select.face_graph(mesh, frozenset(face), 30.0, 4.0)
        self.assertTrue(all(f in graph[g] for f in graph for g in graph[f]))
        self.assertIn(1008, select.cone_grow(mesh, graph, 1014, mesh.normals[1014], 90.0))

    def test_the_outline_is_drawn_clean(self) -> None:
        # The review of 2026-11-17 (finding 5): the cone cut a staircase across the hull's long strips, three steps on each
        # long side (six inner corners at 0.3 %, eight at 1 %).  Filled to its convex outline: the tip end's step alone.
        _, mesh = _Dex3.get()
        for budget, most in ((0.003, 2), (0.01, 4)):
            with self.subTest(budget=budget):
                chart = chart_module.build_chart(mesh, select.apply_operations(mesh, click(DOME_CLICKS[0], budget)))
                self.assertLessEqual(concave_turns(chart.outline()), most)

    def test_the_tier_chosen_widens_the_patch(self) -> None:
        _, mesh = _Dex3.get()
        narrow = select.apply_operations(mesh, click(10926, 0.003))
        wide = select.apply_operations(mesh, click(8826, 0.01))
        self.assertTrue(narrow < wide)
        chart = chart_module.build_chart(mesh, wide)
        self.assertLessEqual(chart_module.judged_stretch(chart, mesh), 0.01)
        self.assertEqual((len(wide), round(chart.stats["area_mm2"], 3)), (788, 405.054))

    def test_a_dome_s_patch_is_centred_on_its_apex(self) -> None:
        # A 30-degree cap of R 30 mm: the patch within 0.3 % from the apex or a click near it; a click off it, its own.
        mesh = F.mesh(F.sphere_cap(30.0, 30.0, rings=12, segments=48))
        seeds = [select.nearest_facet(mesh, point) for point in ((0.0, 0.0, 30.0), (1.5, 1.0, 29.95), (-1.0, -2.0, 29.9))]
        patches = {frozenset(select.apply_operations(mesh, click(seed))) for seed in seeds}
        self.assertEqual(len(patches), 1)
        patch = patches.pop()
        self.assertTrue(set(seeds) <= patch)
        area = math.fsum(mesh.areas[f] for f in patch)
        for k in (0, 1):
            self.assertLess(abs(math.fsum(mesh.centroids[f][k] * mesh.areas[f] for f in patch) / area), 0.05)
        self.assertLessEqual(judged(mesh, patch), 0.003)
        self.assertLess(area, 0.5 * math.fsum(mesh.areas))
        off = select.nearest_facet(mesh, (9.0, 4.0, 28.3))
        self.assertNotIn(off, patch)
        self.assertIn(off, select.apply_operations(mesh, click(off)))

    def test_planar_and_developable_faces_select_as_the_surface_preset(self) -> None:
        cases = {
            "plate": (F.mesh(F.box((40.0, 30.0, 5.0))), (20.0, 15.0, 5.0)),
            "cylinder": (F.mesh(F.cylinder_band(12.0, 30.0, segments=36, closed=False, sweep_deg=150.0)), (12.0, 0.5, 15.0)),
            "cylinder in strips": (F.mesh(F.cylinder_band(12.0, 30.0, segments=12, closed=False, sweep_deg=150.0)), (12.0, 0.5, 15.0)),
            "cone": (F.mesh(cone_band(10.0, 20.0, 25.0, 120.0, 30, 8)), (15.0, 1.0, 12.5)),
            "leap tip": (api.load_mesh({}, (MESHES / "leap-hand.stl").read_bytes()), None),
        }
        for name, (mesh, point) in cases.items():
            with self.subTest(face=name):
                seed = 1124 if point is None else select.nearest_facet(mesh, point)
                plain = select.apply_operations(mesh, [{"op": "grow", "seed_facet": seed, "preset": "surface"}])
                self.assertFalse(select.doubly_curved(mesh, plain))
                for budget in (0.003, 0.01):
                    self.assertEqual(select.apply_operations(mesh, click(seed, budget)), plain)

    def test_the_total_curvature_is_the_region_s_own(self) -> None:
        # The Franka Hand's pad (22 facets on a box): the corners of the box beyond its edge brought it 0.76 sr when the
        # angle defects were smoothed over the whole mesh; its own interior 0.0002 sr.
        mesh = api.load_mesh({}, (MESHES / "franka-hand.stl").read_bytes())
        face = select.grow(mesh, 72, 30.0, 180.0, 4.0)
        self.assertLess(select.total_curvature(mesh, face), 1e-3)
        self.assertFalse(select.doubly_curved(mesh, face))
        # A 15-degree cap's total curvature is its Gauss image, 2 pi (1 - cos 15 degrees).
        cap = F.mesh(F.sphere_cap(20.0, 15.0, rings=10, segments=40))
        omega = select.total_curvature(cap, set(range(cap.facet_count)))
        self.assertAlmostEqual(omega, 2 * math.pi * (1 - math.cos(math.radians(15.0))), delta=0.3 * omega)

    def test_the_stretch_preset_and_its_budget(self) -> None:
        op = select._operation({"op": "grow", "seed_facet": 3, "preset": "stretch"}, 0)
        self.assertEqual((op["stretch"], op["stretch_budget"], op["theta_c_deg"]), ("always", 0.003, 90.0))
        op = select._operation({"op": "grow", "seed_facet": 3, "stretch_budget": 0.01}, 0)
        self.assertEqual((op["stretch"], op["stretch_budget"]), ("curved", 0.01))
        self.assertNotIn("stretch", select._operation({"op": "grow", "seed_facet": 3}, 0))
        for bad in (0.0, 0.5, "0.003", True):
            with self.assertRaises(SurfaceError):
                select._operation({"op": "grow", "seed_facet": 3, "stretch_budget": bad}, 0)


def elongated_dome(rx: float, ry: float, hx: float, hy: float, step: float) -> list:
    """z = -(x^2 / 2 rx + y^2 / 2 ry) over [-hx, hx] x [-hy, hy], mirror-symmetric about x = 0 and y = 0, its quads all
    split along one diagonal (a tessellation that is not itself symmetric, as a CAD exporter's often is not)."""

    nx, ny = int(round(2 * hx / step)), int(round(2 * hy / step))

    def point(i: int, j: int) -> tuple:
        x, y = -hx + 2 * hx * i / nx, -hy + 2 * hy * j / ny
        return (x, y, -(x * x / (2 * rx) + y * y / (2 * ry)))

    triangles = []
    for i in range(nx):
        for j in range(ny):
            a, b, c, d = point(i, j), point(i + 1, j), point(i, j + 1), point(i + 1, j + 1)
            triangles += [(a, b, d), (a, d, c)]
    return triangles


def mirrored(planes, region) -> set:
    """The facets the region's facets mirror to across the first plane (select.mirror_maps' pairs)."""

    pairs = planes[0][2]
    return {g for f in region for g in pairs.get(f, ())}


def own_mirror_image(mesh, region, normal=(0.0, 0.0, 1.0)) -> bool:
    """Whether a region is its own mirror image across a plane of the given normal: the region's own mirror planes
    (select.mirror_maps, through its centroid or fitted) hold it, every facet of it paired within it (its filled holes,
    off the face's map, too)."""

    for _, found, pairs in select.mirror_maps(mesh, region):
        if abs(dot3(found, normal)) > 1 - 1e-9:
            return set(pairs) == set(region) and all(g in region for f in region for g in pairs[f])
    return False


def dot3(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def holed(triangles: list, centre: tuple, radius: float) -> list:
    """The triangles whose centroid lies farther than ``radius`` from ``centre`` (x, y): a hole of the mesh, no facets."""

    return [t for t in triangles if math.dist([sum(p[k] for p in t) / 3 for k in range(2)], centre) > radius]


class MirrorSymmetryTests(unittest.TestCase):
    """The user's feedback of 2026-11-17 on the Dex3-1's dome ("finger应该是对称的，但是你select的面不对称"): on a
    mirror-symmetric face the stretch selection is mirror-symmetric (taken with its mirror image wherever it reaches the
    plane), the same from every click on the dome, its field centred and symmetric; a patch on one side of the plane is
    the mirror image of its mirror click's."""

    def test_the_mirror_planes_are_found_on_the_mesh(self) -> None:
        _, mesh = _Dex3.get()
        face = select.grow(mesh, 10926, 30.0, 180.0, 4.0)
        planes = select.mirror_maps(mesh, face)
        self.assertEqual([normal for _, normal, _ in planes], [(0.0, 0.0, 1.0)])  # the hull's mid-plane, z = 0
        self.assertAlmostEqual(planes[0][0][2], 0.0, places=9)
        pairs = planes[0][2]
        self.assertEqual(set(pairs), set(face))
        self.assertTrue(all(len(pairs[f]) == 1 and pairs[pairs[f][0]] == [f] for f in pairs))  # an involution here
        # A tessellation that is not itself symmetric: both planes of the elongated dome, within the tolerance.
        dome = F.mesh(elongated_dome(40.0, 15.0, 22.0, 11.0, 1.0))
        self.assertEqual([normal for _, normal, _ in select.mirror_maps(dome, set(range(dome.facet_count)))], [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)])
        # No plane: the dome's quarter (a corner of it).
        quarter = {f for f in range(dome.facet_count) if dome.centroids[f][0] > 3.0 and dome.centroids[f][1] > 2.0}
        self.assertEqual(select.mirror_maps(dome, quarter), [])
        # The principal axes: eigenvectors of a symmetric matrix.
        matrix = [[4.0, 1.0, 0.5], [1.0, 3.0, 0.25], [0.5, 0.25, 1.0]]
        for vector in select._principal_axes(matrix):
            product = [math.fsum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3)]
            value = math.fsum(product[i] * vector[i] for i in range(3))
            self.assertLess(max(abs(product[i] - value * vector[i]) for i in range(3)), 1e-12)

    def test_a_symmetric_dome_selects_a_symmetric_patch_from_every_click(self) -> None:
        # A cone of normals on a tessellation that is not symmetric leaves its rim lopsided (3 to 8 facets of the patch
        # without their mirror image); taken with its mirror image, the patch is symmetric about both planes, the same
        # from every click on it, and within the limit.
        mesh = F.mesh(elongated_dome(40.0, 15.0, 22.0, 11.0, 1.0))
        planes = select.mirror_maps(mesh, set(range(mesh.facet_count)))
        points = ((0.3, 0.2), (3.0, 1.5), (-4.0, -2.0), (1.0, -2.5))
        for budget in (0.003, 0.01):
            with self.subTest(budget=budget):
                seeds = [select.nearest_facet(mesh, (x, y, -(x * x / 80.0 + y * y / 30.0))) for x, y in points]
                patches = {frozenset(select.apply_operations(mesh, click(seed, budget))) for seed in seeds}
                self.assertEqual(len(patches), 1)
                patch = patches.pop()
                self.assertTrue(set(seeds) <= patch)
                for _, _, pairs in planes:
                    self.assertEqual({f for f in patch if not any(g in patch for g in pairs.get(f, ()))}, set())
                area = math.fsum(mesh.areas[f] for f in sorted(patch))
                for k in (0, 1):
                    self.assertLess(abs(math.fsum(mesh.centroids[f][k] * mesh.areas[f] for f in sorted(patch)) / area), 0.02)
                self.assertLessEqual(judged(mesh, patch), budget)
                self.assertGreater(judged(mesh, patch), 0.7 * budget)
        # A click off the dome's patch (at 0.3 %) whose own patch reaches a plane: symmetric about it.
        seed = select.nearest_facet(mesh, (6.0, -3.0, -(36.0 / 80.0 + 9.0 / 30.0)))
        patch = select.apply_operations(mesh, click(seed))
        self.assertIn(seed, patch)
        self.assertEqual({f for f in patch if not any(g in patch for g in planes[0][2].get(f, ()))}, set())  # about x = 0

    def test_every_click_on_the_dex3_dome_gives_one_symmetric_patch(self) -> None:
        # The default limit on a doubly curved face, 1 % (the user's choice of 2026-11-17): most of the palmar dome,
        # 405 mm2, the same from every click on it, its own mirror image.
        _, mesh = _Dex3.get()
        planes = select.mirror_maps(mesh, select.grow(mesh, 10926, 30.0, 180.0, 4.0))
        dome = frozenset(select.apply_operations(mesh, click(10926, 0.01)))
        for seed in DOME_CLICKS + (7891, 9177, 12648, 12483, 8427, 12124, 7999):
            with self.subTest(seed=seed):
                self.assertEqual(frozenset(select.apply_operations(mesh, click(seed, 0.01))), dome)
        self.assertEqual(mirrored(planes, dome), set(dome))
        self.assertEqual((len(dome), round(math.fsum(mesh.areas[f] for f in sorted(dome)), 3)), (788, 405.054))
        # A click on one side of the plane (the fingertip's sides) selects round itself: its mirror click the mirror image.
        for seed in (7888, 13484):
            with self.subTest(side=seed):
                patch = select.apply_operations(mesh, click(seed, 0.01))
                image = select.apply_operations(mesh, click(planes[0][2][seed][0], 0.01))
                self.assertEqual(mirrored(planes, patch), image)
                self.assertNotEqual(set(patch), image)
        # The tip end's patch reaches the plane: symmetric (its holes filled: own_mirror_image).
        tip = select.apply_operations(mesh, click(11576, 0.01))
        self.assertTrue(own_mirror_image(mesh, tip))

    def test_the_dex3_dome_s_field_is_centred_and_symmetric(self) -> None:
        # The page's click and Generate sensor (its base the auto exits): proposal #1 is the symmetric field, centred on
        # the dome's plane, at 1 % (82 taxels) and at Strict 0.3 % (48).
        data, _ = _Dex3.get()
        for budget, taxels in ((0.01, 82), (0.003, 48)):
            with self.subTest(budget=budget):
                selection = {"ops": click(10926, budget)}
                result = fit.fit_route({"selection": selection, "base": "auto", "options": dict(PAGE, strain_limit=budget)}, data)
                first = result["proposals"][0]
                symmetry = first["metrics"]["symmetry"]
                self.assertEqual((symmetry["face"], symmetry["field"], symmetry["field_offset_mm"]), (True, True, 0.0))
                self.assertLess(symmetry["deviation_mm"], 0.001)
                self.assertEqual(first["metrics"]["taxels"], taxels)


class SymmetricFollowupTests(unittest.TestCase):
    """The independent review of the symmetric, larger selections (2026-11-17): a click's patch is a disk (a ring's
    chart opened it along a seam on one side: lopsided, slit), its holes filled; a face's mirror plane found though a
    feature on one side moves its centroid; the dome's axis on the plane; a tessellation that is not itself symmetric
    still gives a symmetric field; the sides and the auto exits laid on the plane; a lopsided dome no plane."""

    RINGS = (8817, 8348, 12232, 13536, 14019, 9145, 14370)  # clicks by the tip end whose patches were rings

    def test_a_click_s_patch_is_a_disk_and_its_own_mirror_image_where_it_reaches_the_plane(self) -> None:
        # Finding 1: two slivers on the Dex3-1's mid-plane by its tip end, left out of the face (bent tighter than 4 mm by
        # their width alone), made these clicks' patches rings; the chart opened each along a seam on one side.  Filled
        # now: a disk, its own mirror image, every facet drawn charted (8817 the real click of the review's screenshot).
        data, mesh = _Dex3.get()
        face = select.grow(mesh, 10926, 30.0, 180.0, 4.0)
        for budget, seeds in ((0.01, self.RINGS), (0.003, self.RINGS[:3])):
            for seed in seeds:
                with self.subTest(budget=budget, seed=seed):
                    reply = api.select_surface({"selection": {"ops": click(seed, budget)}}, data)["selection"]
                    facets = set(reply["facets"])
                    self.assertEqual(facets, select.apply_operations(mesh, click(seed, budget)))
                    self.assertTrue(chart_module.patch_topology(mesh, facets)["disk"])
                    self.assertIsNone(reply["stats"]["seam"])
                    self.assertTrue(own_mirror_image(mesh, facets))
                    self.assertLessEqual(reply["stretch"]["smooth_max"], budget)
        filled = select.apply_operations(mesh, click(8817, 0.01))
        self.assertEqual(len(filled - face), 2)  # the two slivers
        self.assertEqual((len(filled), round(math.fsum(mesh.areas[f] for f in sorted(filled)), 3)), (332, 98.388))

    def test_the_leap_hand_s_rings_are_filled_too(self) -> None:
        # Finding 6: these clicks on the LEAP Hand's doubly curved faces were refused (E_SURFACE_NOT_DISK: a ring opened
        # into pieces); each selects a disk now.
        data = (MESHES / "leap-hand.stl").read_bytes()
        mesh = api.load_mesh({}, data)
        for budget, seeds in ((0.01, (18, 19, 37, 38, 138, 315, 316, 317, 545)), (0.003, (218, 236))):
            for seed in seeds:
                with self.subTest(budget=budget, seed=seed):
                    reply = api.select_surface({"selection": {"ops": click(seed, budget)}}, data)["selection"]
                    self.assertIn(seed, reply["facets"])
                    self.assertTrue(chart_module.patch_topology(mesh, reply["facets"])["disk"])
                    self.assertIsNone(reply["stats"]["seam"])

    def test_a_hole_without_facets_is_never_enclosed(self) -> None:
        # An open mesh's own hole cannot be filled: a patch round it is a ring, never taken (the widest disk instead).
        triangles = holed(elongated_dome(40.0, 15.0, 22.0, 11.0, 1.0), (6.0, 0.0), 0.9)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (0.3, 0.2, 0.0))
        patch = select.apply_operations(mesh, click(seed, 0.01))
        self.assertIn(seed, patch)
        self.assertTrue(chart_module.patch_topology(mesh, patch)["disk"])
        self.assertLessEqual(judged(mesh, patch), 0.01)
        self.assertEqual(len(patch), 146)  # stopped short of the hole (532 facets round it on the dome without it)

    def test_a_one_sided_hole_keeps_the_mirror_planes(self) -> None:
        # Finding 3: a hole of 4 or 8 mm2 on one side of the dome (0.4 and 0.7 % of it), outside the patch, moved the
        # face's centroid off its planes and lost them.  Fitted to the face, both planes are found, square as drawn, and
        # every click on the dome selects one symmetric patch.
        for radius in (1.0, 1.5):
            with self.subTest(radius=radius):
                mesh = F.mesh(holed(elongated_dome(40.0, 15.0, 22.0, 11.0, 1.0), (18.0, 9.0), radius))
                planes = select.mirror_maps(mesh, set(range(mesh.facet_count)))
                self.assertEqual([normal for _, normal, _ in planes], [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)])
                self.assertLess(abs(planes[0][0][0]), 1e-3)  # fitted (the centroid lies 0.08 to 0.2 mm off x = 0)
                seeds = [select.nearest_facet(mesh, (x, y, -(x * x / 80.0 + y * y / 30.0))) for x, y in ((0.3, 0.2), (-4.0, -2.0))]
                patches = {frozenset(select.apply_operations(mesh, click(seed, 0.01))) for seed in seeds}
                self.assertEqual(len(patches), 1)
                patch = patches.pop()
                for _, _, pairs in planes:
                    self.assertTrue(all(any(g in patch for g in pairs.get(f, ())) for f in patch))
        # No false plane: a dome lopsided across y (y > 0 of radius 15, y < 0 of 11) is symmetric about x = 0 only.
        lopsided = [tuple((x, y, -(x * x / 80.0 + y * y / (30.0 if y > 0 else 22.0))) for x, y, _ in t)
                    for t in elongated_dome(40.0, 15.0, 22.0, 11.0, 1.0)]
        mesh = F.mesh(lopsided)
        self.assertEqual([normal for _, normal, _ in select.mirror_maps(mesh, set(range(mesh.facet_count)))], [(1.0, 0.0, 0.0)])

    def test_the_dome_s_axis_lies_on_its_planes(self) -> None:
        # The axis laid on each mirror plane (its component across the plane, rounding's, taken out): a cap beyond a
        # hemisphere whose half in front of the axis is cut along a ring of facets split one way.
        mesh = F.mesh(F.sphere_cap(10.0, 110.0, rings=11, segments=36))
        face = set(range(mesh.facet_count))
        planes = select.mirror_maps(mesh, face)
        self.assertEqual(len(planes), 2)
        for point in ((0.5, 0.3, 10.0), (6.0, 2.0, 7.0), (-5.0, -6.0, 4.0)):
            axis, _ = select.dome_axis(mesh, face, select.nearest_facet(mesh, point), planes)
            self.assertEqual([dot3(axis, normal) for _, normal, _ in planes], [0.0, 0.0])

    def test_a_patch_is_taken_with_its_mirror_image_before_its_outline_is_drawn(self) -> None:
        # A click off the plane whose cone of normals is lopsided: taken with its mirror image before its outline is
        # drawn clean as well as after (smooth_outline's convex fill and teeth on the lopsided cone give other facets).
        mesh = F.mesh(elongated_dome(25.0, 25.0, 15.0, 15.0, 1.0))
        seed = select.nearest_facet(mesh, (-8.0, -3.0, -(64.0 + 9.0) / 50.0))
        self.assertEqual(len(select.apply_operations(mesh, click(seed, 0.003))), 152)

    def test_a_tessellation_that_is_not_symmetric_gives_a_symmetric_field(self) -> None:
        # Finding 2: the elongated dome's quads split one way leave its outline a notch on one side only (0.76 mm off its
        # mirror image); the fit's symmetric-face rule read the outline alone.  The selection is its own mirror image, so
        # the plane's trace is the axis, the outline allowed a facet: proposal #1 symmetric and centred.
        triangles = elongated_dome(40.0, 15.0, 22.0, 11.0, 1.0)
        data = F.stl_bytes(triangles)
        mesh = api.load_mesh({}, data)
        seed = min(range(mesh.facet_count), key=lambda f: mesh.centroids[f][0] ** 2 + mesh.centroids[f][1] ** 2)
        result = fit.fit_route({"selection": {"ops": click(seed, 0.01)}, "base": "auto", "options": dict(PAGE, strain_limit=0.01)}, data)
        symmetry = result["proposals"][0]["metrics"]["symmetry"]
        self.assertEqual((symmetry["face"], symmetry["field"], symmetry["field_offset_mm"]), (True, True, 0.0))
        self.assertGreater(symmetry["deviation_mm"], fieldfit.SYMMETRY_TOLERANCE_MM)
        self.assertEqual(result["proposals"][0]["metrics"]["taxels"], 59)

    def test_the_sides_and_the_exits_are_laid_on_the_plane(self) -> None:
        # Finding 4: the select reply's sides split the dome's base end at the plane into two halves (the page's auto
        # base drew one), and the auto arc's edges ran farther up one long side.  Now every side's mirror image is a
        # side (the base end one side across the plane), and the auto fit's exit is a side or an arc centred on it.
        data, mesh = _Dex3.get()
        for budget, taxels in ((0.01, 82), (0.003, 48)):
            with self.subTest(budget=budget):
                selection = api.select_surface({"selection": {"ops": click(10926, budget)}}, data)["selection"]
                ends = [(tuple(side["from_xyz"]), tuple(side["to_xyz"])) for side in selection["sides"]]
                for a, b in ends:
                    image = ((b[0], b[1], -b[2]), (a[0], a[1], -a[2]))
                    self.assertLess(min(max(math.dist(image[0], c), math.dist(image[1], d)) for c, d in ends), 1e-5)
                crossing = [side for side in selection["sides"] if side["from_xyz"][2] < 0 < side["to_xyz"][2] or side["to_xyz"][2] < 0 < side["from_xyz"][2]]
                self.assertEqual(len(crossing), 2)  # the base end's and the tip end's, each one side
                result = fit.fit_route({"selection": {"ops": click(10926, budget)}, "base": "auto", "options": dict(PAGE, strain_limit=budget)}, data)
                first = result["proposals"][0]
                self.assertEqual(first["metrics"]["taxels"], taxels)
                outline = result["selection"]["outline_xyz"]
                points = [outline[k % len(outline)] for e in first["placement"]["exit_edges"] for k in (e, e + 1)]
                self.assertLess(max(min(math.dist((x, y, -z), q) for q in points) for x, y, z in points), 0.05)
                (u0, v0), (u1, v1) = first["placement"]["base_from_uv"], first["placement"]["base_to_uv"]
                self.assertLess(abs(v0 + v1), 0.001)  # the chord centred on the trace (v = 0 in this chart)
        # The auto arcs of an elongated dome turned onto the plane are centred on it: one exit per end, its edges mirrored.
        _, chart = api.selection_chart(mesh, {"ops": click(10926, 0.01)})
        traces = api.mirror_traces(mesh, chart)
        self.assertEqual(len(traces), 1)
        arcs = [base for base in fit.choose_bases("auto", api.boundary_sides(mesh, chart, traces), mesh, chart) if base.get("kind") == "arc"]
        turned = [fit.axis_exit(chart, arc, traces, recentre=True) for arc in arcs]
        along = traces[0]["direction"]
        on_plane = [base for base in turned if abs(base["inward_uv"][0] * along[1] - base["inward_uv"][1] * along[0]) < 1e-9]
        self.assertGreater(len(on_plane), 1)
        self.assertEqual(len({(tuple(b["from_uv"]), tuple(b["to_uv"]), tuple(b["edges"])) for b in on_plane}), 2)

    def test_the_tier_changed_selects_the_dome_again_from_its_middle(self) -> None:
        # The page's tier change clicks the select reply's centre_facet at the other limit: the dome's patch at that
        # limit, whichever click on the dome made the selection (main.js onTierChange).
        data, mesh = _Dex3.get()
        dome = {budget: select.apply_operations(mesh, click(10926, budget)) for budget in (0.01, 0.003)}
        for seed, budget, other in ((8826, 0.01, 0.003), (11741, 0.003, 0.01)):
            with self.subTest(seed=seed, budget=budget):
                middle = api.select_surface({"selection": {"ops": click(seed, budget)}}, data)["selection"]["stretch"]["centre_facet"]
                self.assertEqual(select.apply_operations(mesh, click(middle, other)), dome[other])
        # By the tip end the patch's filled holes (the part's facets bent tighter than 4 mm) hold its centroid's nearest
        # facet; the middle is the face's own, so the other limit selects a patch of the face, not that facet alone.
        face = select.grow(mesh, 10926, 30.0, 180.0, 4.0)
        tip = api.select_surface({"selection": {"ops": click(11576, 0.01)}}, data)["selection"]
        self.assertGreater(len(set(tip["facets"]) - face), 2)
        self.assertNotIn(api.centre_facet(mesh, tip["facets"]), face)
        middle = tip["stretch"]["centre_facet"]
        self.assertIn(middle, face)
        self.assertGreater(math.fsum(mesh.areas[f] for f in sorted(select.apply_operations(mesh, click(middle, 0.003)))), 20.0)


class WholeSelectionTests(unittest.TestCase):
    """RC2, RC4 and RC5: the whole selection fitted or refused, its lattice along its axis, the exits on its edge."""

    def test_the_user_s_selection_is_refused_at_either_tier_saying_how_much_fits(self) -> None:
        # Their selection stretches 1.19 % on the part (the relaxed sheet's, smoothed; 0.79 % on the least-max-stretch
        # chart, which the gate read until the review of 2026-11-17): over both tiers.
        data, mesh = _Dex3.get()
        for budget, area, shown in ((0.003, 238.849, "239 of its 431 mm2 round the click"), (0.01, 405.054, "405 of its 431 mm2 round the click")):
            with self.subTest(budget=budget):
                with self.assertRaises(SurfaceError) as raised:
                    fit.fit_route({"selection": {"ops": USER_OPS}, "base": USER_BASE, "options": dict(PAGE, strain_limit=budget)}, data)
                error = raised.exception
                self.assertEqual(error.code, "E_SURFACE_NOT_DEVELOPABLE")
                self.assertAlmostEqual(error.details["stretch"], 0.0119, delta=0.0002)
                self.assertGreater(error.details["stretch_facet_max"], error.details["stretch"])
                self.assertEqual(error.details["strain_limit"], budget)
                self.assertAlmostEqual(error.details["selected_area_mm2"], 431.443, places=3)
                self.assertEqual(error.details["shrink"]["seed_facet"], 10926)
                self.assertAlmostEqual(error.details["shrink"]["area_mm2"], area, places=3)
                self.assertLessEqual(error.details["shrink"]["stretch"], budget)
                self.assertIn(shown, error.message)

    def test_shrink_to_fit_is_fitted_whole(self) -> None:
        data, mesh = _Dex3.get()
        selected = api.select_surface({"selection": {"ops": USER_OPS}}, data)["selection"]
        self.assertGreater(selected["stretch"]["smooth_max"], 0.01)
        self.assertGreaterEqual(selected["stretch"]["facet_max"], selected["stretch"]["smooth_max"])
        # Shrink to fit at 1 %: preset stretch at the selection's click.
        shrunk = [{"op": "grow", "mode": "add", "seed_facet": 10926, "preset": "stretch", "stretch_budget": 0.01}]
        drawn = api.select_surface({"selection": {"ops": shrunk}}, data)["selection"]
        result = fit.fit_route({"selection": {"ops": shrunk}, "base": USER_BASE, "options": dict(PAGE, strain_limit=0.01)}, data)
        self.assertEqual(result["selection"]["facets"], drawn["facets"])  # no hidden disk: the region drawn is fitted
        self.assertNotIn("strain_limited", result["selection"])
        first = result["proposals"][0]
        self.assertNotIn("strain_limited", first["placement"])
        # The user's base point's arc turned onto the dome's plane and centred on it (the review of 2026-11-17's follow-up,
        # finding 4): the symmetric field, 82 taxels (83 asymmetric on the chord of before).
        self.assertEqual((first["metrics"]["rows"], first["metrics"]["columns"], first["metrics"]["taxels"]), (13, 8, 82))
        self.assertEqual((first["metrics"]["symmetry"]["face"], first["metrics"]["symmetry"]["field"]), (True, True))
        mapped = place.map_route({"selection": {"ops": shrunk}, "placement": first["placement"], "design": first["design"]}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        # The strain check passes on the smoothed stretch and reports the largest facet's too.
        record = next(r for r in mapped["verification"] if r["rule"] == "strain_under_field")
        self.assertLessEqual(record["measured"], 0.01)
        self.assertLess(record["measured"], record["measured_facet"])

    def test_the_boards_leave_the_surface_on_the_selection_s_own_edge(self) -> None:
        data, mesh = _Dex3.get()
        selection = {"ops": click(10926)}
        drawn = api.select_surface({"selection": selection}, data)["selection"]
        result = fit.fit_route({"selection": selection, "base": USER_BASE, "options": PAGE}, data)
        self.assertEqual(result["selection"]["facets"], drawn["facets"])
        first = result["proposals"][0]
        self.assertEqual(first["metrics"]["taxels"], 47)
        mapped = place.map_route({"selection": selection, "placement": first["placement"], "design": first["design"]}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        outline = drawn["outline_xyz"]
        segments = list(zip(outline, outline[1:] + outline[:1]))

        def to_outline(p) -> float:
            best = math.inf
            for a, b in segments:
                ab = [b[k] - a[k] for k in range(3)]
                ap = [p[k] - a[k] for k in range(3)]
                length2 = math.fsum(x * x for x in ab)
                t = 0.0 if length2 == 0 else max(0.0, min(1.0, math.fsum(ab[k] * ap[k] for k in range(3)) / length2))
                best = min(best, math.dist(p, [a[k] + t * ab[k] for k in range(3)]))
            return best

        ends = []
        for key in ("row", "column"):
            for run in mapped["overlay"][key]:
                if run[0] != run[-1]:
                    ends += [run[0], run[-1]]
        self.assertGreater(len(ends), 0)
        # A run ends where its board leaves the chart, densified every place.DENSIFY_MM: on the selection's outline.
        self.assertLess(max(to_outline(p) for p in ends), place.DENSIFY_MM + 0.05)

    def test_an_elongated_dome_lays_its_lattice_along_its_axis(self) -> None:
        data, mesh = _Dex3.get()
        _, chart = api.selection_chart(mesh, {"ops": click(10926)})
        self.assertTrue(fit.along_axis(mesh, chart))
        long, short, _, ratio = fit.principal_axes(chart)
        self.assertGreater(ratio, fit.AXIS_MOMENT_RATIO)
        searched = []
        original = fit.fit_chart

        def recording(mesh_, chart_, sides, bases, options, cache=None):
            searched.append((bases, options))
            return original(mesh_, chart_, sides, bases, options, cache=cache)

        fit.fit_chart = recording
        try:
            result = fit.fit_route({"selection": {"ops": click(10926)}, "base": USER_BASE, "options": dict(PAGE, rotation="auto")}, data)
        finally:
            fit.fit_chart = original
        # No turned field: the search runs unturned whatever the options say (and echoes the user's).
        self.assertEqual(searched[0][1]["rotation"], "none")
        self.assertEqual(result["request"]["options"]["rotation"], "auto")
        for proposal in result["proposals"]:
            self.assertEqual(proposal["metrics"].get("angle_deg", 0.0), 0.0)
        # The arc exit at the user's base point turned to the principal axis nearest its chord: the lattice along it.
        inward = result["proposals"][0]["placement"]["base_inward_uv"]
        self.assertEqual(result["proposals"][0]["placement"]["base_kind"], "arc")
        self.assertAlmostEqual(max(abs(inward[0] * d[0] + inward[1] * d[1]) for d in (long, short)), 1.0, places=6)
        chord = fit.choose_bases(USER_BASE, api.boundary_sides(mesh, chart), mesh, chart)[0]["inward_uv"]
        self.assertLess(max(abs(chord[0] * d[0] + chord[1] * d[1]) for d in (long, short)), 0.99)  # the chord's own is not

    def test_a_nearly_flat_pad_keeps_its_chord(self) -> None:
        # The Franka Hand's pad: a curved chart (0.07 mm off its plane) stretched 0.002 %: no axis frame, ARAP's chart kept.
        mesh = api.load_mesh({}, (MESHES / "franka-hand.stl").read_bytes())
        chart = chart_module.build_chart(mesh, select.grow(mesh, 72, 10.0, 4.0))
        self.assertEqual((chart.kind, chart.method), ("curved", "lscm+arap"))
        self.assertLess(chart.stats["strain_max"], solve.BOUNDED_FROM)
        self.assertFalse(fit.along_axis(mesh, chart))


class SolverTests(unittest.TestCase):
    """RC3: the least-max-stretch chart, about the least stretch possible, the same on every Python."""

    def test_least_max_stretch_on_analytic_caps(self) -> None:
        # A cap of half-angle a flattens with a least stretch of about a^2 / 12 (the radial map scaled between its
        # centre and its rim); ARAP's chart stretches about 1.5 times that.
        for radius, angle, rings, segments in ((20.0, 10.0, 10, 48), (30.0, 15.0, 12, 48), (30.0, 15.0, 6, 24)):
            with self.subTest(radius=radius, angle=angle, rings=rings):
                mesh = F.mesh(F.sphere_cap(radius, angle, rings=rings, segments=segments))
                chart = chart_module.build_chart(mesh, range(mesh.facet_count))
                self.assertEqual(chart.method, "lscm+arap+bounded")
                least = math.radians(angle) ** 2 / 12
                index, triangles, _ = solve._triangles(mesh, chart.facets, chart.vertices)
                points = [mesh.vertices[v] for v in chart.vertices]
                loop = chart_module.patch_topology(mesh, chart.facets)["loops"][0]
                arap = solve.arap(points, triangles, solve.lscm(points, triangles, [index[v] for v in loop]), solve.ARAP_ITERATIONS)
                arap_max = solve._max_stretch(arap, triangles, solve._local_frames(points, triangles)[0])
                self.assertGreater(chart.stats["strain_max"], 0.95 * least)
                self.assertLess(chart.stats["strain_max"], 1.15 * least)
                self.assertLess(chart.stats["strain_max"], 0.75 * arap_max)
                self.assertEqual(chart.stats["flipped_facets"], 0)

    def test_the_fit_judges_the_relaxed_sheet(self) -> None:
        # The review of 2026-11-17 (finding 2): a sheet on soft tape creeps to its elastic state, ARAP's chart, whatever
        # chart it was cut by: a cap's rim at a^2 / 8, 1.5 x the least-max-stretch chart's a^2 / 12.  The gate reads it.
        for radius, angle in ((20.0, 10.0), (30.0, 15.0)):
            with self.subTest(radius=radius, angle=angle):
                mesh = F.mesh(F.sphere_cap(radius, angle, rings=12, segments=48))
                chart = chart_module.build_chart(mesh, range(mesh.facet_count))
                rim = math.radians(angle) ** 2 / 8
                self.assertGreater(chart_module.relaxed_max(chart, mesh), 0.95 * rim)
                self.assertLess(chart_module.relaxed_max(chart, mesh), 1.05 * rim)
                self.assertLess(chart.stats["strain_max"], 0.75 * chart_module.relaxed_max(chart, mesh))
                # Judged: the relaxed sheet's, smoothed over 1 mm; a chart without the least-max-stretch rounds judges
                # the same, to the bit (the select's trial patches).
                smoothed = chart_module.smoothed_strain(chart, mesh)
                self.assertEqual(chart_module.judged_stretch(chart, mesh), max(smoothed.values()))
                self.assertIs(chart_module.build_chart(mesh, range(mesh.facet_count), least=False), chart)  # the full one serves
                with chart_module._CHART_LOCK:
                    chart_module._CHART_CACHE.clear()
                light = chart_module.build_chart(mesh, range(mesh.facet_count), least=False)
                self.assertEqual(light.method, "lscm+arap")
                self.assertEqual(repr(chart_module.judged_stretch(light, mesh)), repr(chart_module.judged_stretch(chart, mesh)))
                own = max(chart_module.facet_stretch(chart, f) for f in chart.facets)
                self.assertGreater(chart_module.judged_stretch(chart, mesh), 0.0)
                self.assertLess(own, chart_module.relaxed_max(chart, mesh))

    def test_the_rounds_stop_once_they_gain_under_one_percent(self) -> None:
        mesh = F.mesh(F.sphere_cap(30.0, 15.0, rings=6, segments=24))
        rounds = []
        original = solve._max_stretch

        def counting(current, triangles, local):
            rounds.append(original(current, triangles, local))
            return rounds[-1]

        solve._max_stretch = counting
        try:
            chart_module._build_chart(mesh, tuple(range(mesh.facet_count)), allow_curved=True, seed=None)
        finally:
            solve._max_stretch = original
        best = [min(rounds[1:k + 1]) for k in range(1, len(rounds))]  # rounds[0]: ARAP's, before the rounds
        self.assertLess(len(best), solve.BOUNDED_ROUNDS + 1)
        self.assertLess(best[-3] - best[-1], solve.BOUNDED_STOP * best[-3])
        self.assertTrue(all(best[k - 2] - best[k] >= solve.BOUNDED_STOP * best[k - 2] for k in range(2, len(best) - 1)))

    def test_the_charts_are_the_same_on_every_python(self) -> None:
        # Pinned on Python 3.12 (2026-11-17, the review's fixes) and the same on 3.9, 3.10, 3.11 and in Pyodide 0.27.8:
        # every sum of the solver and the selection runs in a fixed order, with no math.hypot and no built-in sum of floats.
        mesh = F.mesh(F.sphere_cap(30.0, 15.0, rings=12, segments=48))
        chart = chart_module.build_chart(mesh, range(mesh.facet_count))
        self.assertEqual(uv_digest(chart), "3fe6e659362f3e62")
        self.assertEqual(repr(chart_module.judged_stretch(chart, mesh)), "0.007319484849017734")
        _, dex3 = _Dex3.get()
        _, patch = api.selection_chart(dex3, {"ops": click(10926)})
        self.assertEqual(uv_digest(patch), "0b68981f627f3d70")
        self.assertEqual(repr(chart_module.judged_stretch(patch, dex3)), "0.0028997839891229276")


class StackTests(unittest.TestCase):
    """The stack the bend rules follow (the user's answers of 2026-11-17: 0.2 mm boards, laminated by the user)."""

    def test_the_stack_is_the_ordered_board_the_film_and_the_lamination(self) -> None:
        profile = json.loads((ROOT / "profiles" / "jlc_fpc_surface_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(fit.SINGLE_FPC_MM, profile["order"]["fpc_thickness_mm"])
        self.assertEqual(fit.SINGLE_FPC_MM, 0.2)
        self.assertEqual(fit.STACK_THICKNESS_MM, round(2 * fit.SINGLE_FPC_MM + fit.FILM_MM + 2 * fit.LAMINATE_MM, 6))
        self.assertEqual(fit.STACK_THICKNESS_MM, 0.65)
        self.assertEqual((place.FIELD_BEND, place.BOARD_BEND), ("10 x 0.65 mm", "10 x 0.2 mm"))

    def test_a_face_bent_tighter_than_the_field_is_refused_saying_so(self) -> None:
        # The review of 2026-11-17 (finding 6): a half cylinder of R 5 mm took 133 taxels at the 0.47 mm stack of before;
        # at 0.65 mm the field bends to 6.5 mm at the least, and the refusal says why.
        triangles = F.cylinder_band(5.0, 40.0, segments=96, closed=False, sweep_deg=180.0)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (5.0, 0.05, 20.0))
        with self.assertRaises(SurfaceError) as raised:
            fit.fit_route({"selection": {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]}, "options": {"pitch_mm": 2.0}},
                          F.stl_bytes(triangles))
        self.assertEqual(raised.exception.code, "E_SURFACE_NO_FIT")
        self.assertIn("bends tighter than the field's 6.5 mm (10 x 0.65 mm), to 5.0 mm", raised.exception.message)

    def test_the_map_s_bend_rules_follow_the_stack(self) -> None:
        data, mesh = _Dex3.get()
        selection = {"ops": click(10926)}
        result = fit.fit_route({"selection": selection, "base": USER_BASE, "options": PAGE}, data)
        first = result["proposals"][0]
        mapped = place.map_route({"selection": selection, "placement": first["placement"], "design": first["design"]}, data)
        field = next(r for r in mapped["verification"] if r["rule"] == "field_bend_radius")
        self.assertEqual(field["required"], 6.5)
        self.assertIn("10 x 0.65 mm", field["what"])
        self.assertEqual(mapped["stack"]["contact_offset_mm"], 0.65)


class WholeBoardBendTests(unittest.TestCase):
    """Whole board (``containment: board``) on the real stack (the lead's decision of 2026-11-18): the taxel field F keeps
    the laminated field's bend rule (10 x 0.65 mm), everything outside it (the Row channel and expansion, the Column fan-out,
    the tails) one board's (10 x 0.2 mm), as Field only checks the routing off the field.  On the roof, two creases of 18
    degrees across the face, 3 and 25 mm from its exit: tighter than the field may follow (14.2 degrees at 6.5 mm), not one
    board (25.6 degrees at 2 mm).  Since 56624a1 such bends had blocked the whole board (the soft finger's face, its crease
    0.3 mm above its mount end, fitted nothing at side 0)."""

    BASE = {"point_xyz": [0.0, -15.0, 10.0]}
    CREASES = (3.0, 25.0)  # mm from the exit, along the face
    _cache: dict = {}

    @classmethod
    def roof(cls) -> tuple:
        if "mesh" not in cls._cache:
            triangles = F.roof([(3.0, 18.0), (22.0, 0.0), (30.0, -18.0)])
            mesh = F.mesh(triangles)
            seed = select.nearest_facet(mesh, (12.85, -15.0, 11.0))
            cls._cache["mesh"] = (F.stl_bytes(triangles), mesh, {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]})
        return cls._cache["mesh"]

    @classmethod
    def fitted(cls, containment: str) -> dict:
        if containment not in cls._cache:
            data, _, selection = cls.roof()
            cls._cache[containment] = fit.fit_route({"selection": selection, "base": cls.BASE, "options": {"containment": containment}}, data)
        return cls._cache[containment]

    def test_the_boards_cross_bends_the_field_may_not(self) -> None:
        data, mesh, selection = self.roof()
        result = self.fitted("board")
        # The boards take one board's rule (no bend), F the laminated field's (both creases).
        self.assertEqual((result["obstacles"]["bends"], result["obstacles"]["field_bends"]), (0, 2))
        self.assertEqual([(p["metrics"]["taxels"], "mask" in p["design"]["matrix"]) for p in result["proposals"]],
                         [(190, True), (182, False), (177, True), (169, False), (164, True)])
        for proposal in result["proposals"]:
            built = generate_design(proposal["design"])
            origin = proposal["placement"]["field_origin_base"]
            self.assertEqual(proposal["placement"]["base_angle_deg"], 0.0)
            outlines = fit.board_outlines_base(built, origin)
            # Unturned, the creases lie across the face: F wholly beyond the far one, both boards (their tails past the
            # exit) across both.
            self.assertGreater(min(y for _, y in fieldfit.field_body(built, origin)), self.CREASES[1])
            self.assertLess(max(min(y for _, y in outlines[name]) for name in ("row", "column")), 0.0)
            mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
            records = {record["rule"]: record for record in mapped["verification"]}
            self.assertTrue(mapped["ok"], [rule for rule, record in records.items() if not record["passed"]])
            self.assertTrue(records["field_bend_radius"]["passed"])
            self.assertEqual(records["board_bend_radius"]["required"], 2.0)
            self.assertTrue(records["board_clearance"]["passed"])
        # Field only treats the routing so too, and its field as before: the same face, F beyond the far crease.
        field = self.fitted("field")
        self.assertEqual(field["obstacles"], {"strained": 0, "covered": 0, "holes": 0, "bends": 2})
        self.assertEqual(field["proposals"][0]["metrics"]["taxels"], 196)

    def test_a_bend_toward_the_exit_takes_no_taxels_away(self) -> None:
        # The roof's exit on its long side (y = 0): the creases run up the face to the exit, 30 and 52 mm along it.  Moved off
        # them only within the boards' room (up and down, from the channel's edge), F found no field beside them (132 taxels,
        # turned 10 degrees); the search with the boards off them as well, the whole board's rule before 2026-11-18, finds its
        # 182 (14 x 13, unturned) in the panel short of the near crease, which holds under one board's rule too.
        data, mesh, selection = self.roof()
        result = fit.fit_route({"selection": selection, "base": {"point_xyz": [12.85, 0.0, 11.0]}, "options": {"containment": "board"}}, data)
        self.assertEqual([(p["metrics"]["taxels"], "mask" in p["design"]["matrix"], p["placement"]["base_angle_deg"]) for p in result["proposals"]],
                         [(182, False, 0.0), (177, True, 0.0), (169, False, 0.0), (164, True, 0.0), (156, False, 0.0)])
        self.assertEqual((result["obstacles"]["bends"], result["obstacles"]["field_bends"]), (0, 2))
        _, chart = api.selection_chart(mesh, selection)
        obstacles = fit.surface_obstacles(mesh, chart, fit.parse_options({"containment": "board"}))
        for proposal in result["proposals"]:
            placement = proposal["placement"]
            side = {"from_uv": placement["base_from_uv"], "to_uv": placement["base_to_uv"], "inward_uv": placement["base_inward_uv"]}
            frame = fit.BaseFrame(side, placement["base_angle_deg"])
            self.assertEqual(sorted({round(frame.to_base(p)[0], 3) for a, b, _ in obstacles["field_bends"] for p in (a, b)}), [30.0, 52.0])
            built = generate_design(proposal["design"])
            self.assertLess(max(x for x, _ in fieldfit.field_body(built, placement["field_origin_base"])), 30.0)
            mapped = place.map_route({"selection": selection, "placement": placement, "design": proposal["design"]}, data)
            self.assertTrue(mapped["ok"], [record["rule"] for record in mapped["verification"] if not record["passed"]])

    def test_the_field_never_lies_over_them(self) -> None:
        data, mesh, selection = self.roof()
        # The search: every rectangle and every masked field it finds keeps F (the field and its 0.5 mm margin) off both
        # creases, though the boards would hold 25 rows from the near one (326 taxels with the field's rule dropped).
        options = fit.parse_options({"containment": "board", "rotation": "none"})
        _, chart = api.selection_chart(mesh, selection)
        bases = fit.choose_bases(self.BASE, api.boundary_sides(mesh, chart), mesh, chart)
        obstacles = fit.surface_obstacles(mesh, chart, options)
        profile = fit.load_profile_cached(options["template"])
        frame = fit.BaseFrame(bases[0], 0.0)
        levels = sorted(round(frame.to_base(p)[1], 4) for a, b, _ in obstacles["field_bends"] for p in (a, b))
        self.assertEqual(levels, [3.0, 3.0, 25.0, 25.0])
        region = fit.UsableRaster(chart, frame, obstacles, 0.0, bases[0]["edges"])
        rectangles = fit.search(region, options, profile, {})
        for candidate in rectangles:
            candidate.update(side=bases[0], frame=frame, region=region)
        masked, _ = fill.masked_candidates(chart, bases, options, profile, obstacles, rectangles, [])
        self.assertTrue(rectangles and masked)
        for candidate in rectangles + masked:
            low = candidate["field_origin"][1] - 0.5
            high = candidate["field_origin"][1] + (candidate["rows"] - 1) * candidate["pitch_y"] + fit._electrode(candidate["pitch_y"], options["fill"]) + 0.5
            for crease in self.CREASES:
                self.assertTrue(high < crease or low > crease, (candidate["rows"], candidate["columns"], candidate.get("mask") is not None, low, high))
        # The check of a built field: the first proposal's F where it is fitted, and moved over the far crease.
        proposal = self.fitted("board")["proposals"][0]
        built = generate_design(proposal["design"])
        placement = proposal["placement"]
        side = {"from_uv": placement["base_from_uv"], "to_uv": placement["base_to_uv"], "inward_uv": placement["base_inward_uv"]}
        frame = fit.BaseFrame(side, placement["base_angle_deg"])
        exits = fit.ExitOutline([frame.to_base(p) for p in chart.outline()], placement["exit_edges"])
        x, y = placement["field_origin_base"]
        self.assertIsNone(fit.field_bend_point(built, (x, y), exits, frame, obstacles, 0.0))
        lowered = (x, self.CREASES[1] - 3.0)
        point = fit.field_bend_point(built, lowered, exits, frame, obstacles, 0.0)
        self.assertIsNotNone(point)
        self.assertAlmostEqual(point[1], self.CREASES[1], places=5)
        # Field only has no such bends: its F is checked against "bends" (fieldfit), the routing reported.
        field_obstacles = fit.surface_obstacles(mesh, chart, fit.parse_options({}))
        self.assertNotIn("field_bends", field_obstacles)
        self.assertIsNone(fit.field_bend_point(built, lowered, exits, frame, field_obstacles, 0.0))

if __name__ == "__main__":
    unittest.main()
