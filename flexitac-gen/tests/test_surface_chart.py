"""CAD mode: surface selection (surface.select) and flattening into a chart (surface.chart)."""

from __future__ import annotations

import math
import random
import unittest
from pathlib import Path
from unittest import mock

from surface import api
from surface import chart as chart_module
from surface import select, solve
from surface.errors import SurfaceError

try:
    import surface_fixtures as F
except ImportError:  # run as a package
    from tests import surface_fixtures as F

ASSETS = Path(__file__).resolve().parents[1] / "asset"


def area(mesh, facets) -> float:
    return math.fsum(mesh.areas[f] for f in facets)


class SelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mesh = F.mesh(F.soft_finger_replica())
        self.seed = select.nearest_facet(self.mesh, (0.0, -12.9, -62.7))

    def test_flat_preset_stops_at_the_fillet_and_tight_limits_give_the_exact_face(self) -> None:
        flat = select.grow(self.mesh, self.seed, **_preset("flat"))
        exact = select.grow(self.mesh, self.seed, 2.5, 2.5)
        self.assertAlmostEqual(area(self.mesh, exact), 119.365 * 25.8, places=3)
        # The flat preset also takes the fillet's first strip (3 degrees off the face).
        self.assertGreater(area(self.mesh, flat), area(self.mesh, exact))
        self.assertLess(area(self.mesh, flat), area(self.mesh, exact) + 0.5 * 25.8)
        smooth = select.grow(self.mesh, self.seed, **_preset("smooth"))
        self.assertGreater(area(self.mesh, smooth), 2 * area(self.mesh, exact))

    def test_the_surface_preset_leaves_out_tight_blends(self) -> None:
        # The default click: the contact face without its R3 fillet strip (a 3 mm bend).
        face = select.apply_operations(self.mesh, [{"op": "grow", "seed_facet": self.seed}])
        self.assertAlmostEqual(area(self.mesh, face), 119.365 * 25.8, places=3)
        # A cylinder of radius 5 mm is kept whole; one of radius 3 mm is too tight for the stack.
        for radius, whole in ((5.0, True), (3.0, False)):
            band = F.mesh(F.cylinder_band(radius, 20.0, segments=24, closed=False, sweep_deg=180.0))
            seed = select.nearest_facet(band, (radius, 0.2, 10.0))
            region = select.apply_operations(band, [{"op": "grow", "seed_facet": seed}])
            self.assertEqual(len(region) == band.facet_count, whole, radius)

    def test_tight_blends_and_creases_bound_the_surface_preset_at_any_tessellation(self) -> None:
        face = 119.365 * 25.8
        for segments in (15, 60):  # 6 and 1.5 degrees per fillet strip
            mesh = F.mesh(F.extrude(F.soft_finger_profile(fillet_segments=segments), 25.8))
            seed = select.nearest_facet(mesh, (0.0, -12.9, -62.7))
            region = select.apply_operations(mesh, [{"op": "grow", "seed_facet": seed}])
            self.assertAlmostEqual(area(mesh, region), face, places=3, msg=segments)
        # Three strips (30 degrees each): the first, 1.55 mm wide and turned by
        # 15 degrees, is a flat chamfer a sheet can follow; the 30 degree crease
        # after it is not crossed.
        mesh = F.mesh(F.extrude(F.soft_finger_profile(fillet_segments=3), 25.8))
        seed = select.nearest_facet(mesh, (0.0, -12.9, -62.7))
        region = select.apply_operations(mesh, [{"op": "grow", "seed_facet": seed}])
        strip = 2 * 3.0 * math.sin(math.radians(15.0)) * 25.8
        self.assertAlmostEqual(area(mesh, region), face + strip, places=3)
        # A 25 degree roof ridge between two wide faces: a sheet bent at 4 mm would
        # lift off it by about 0.1 mm, so growth stops there; a 10 degree ridge is crossed.
        for ridge_deg, crossed in ((25.0, False), (10.0, True)):
            rise = 30.0 * math.tan(math.radians(ridge_deg / 2))
            mesh = F.mesh(F.extrude([(0.0, 0.0), (60.0, 0.0), (60.0, 10.0), (30.0, 10.0 + rise), (0.0, 10.0)], 30.0))
            seed = select.nearest_facet(mesh, (15.0, -15.0, 10.0 + rise / 2))
            region = select.apply_operations(mesh, [{"op": "grow", "seed_facet": seed}])
            roof = 2 * 30.0 * math.hypot(30.0, rise)
            self.assertAlmostEqual(area(mesh, region), roof if crossed else roof / 2, places=3, msg=ridge_deg)

    def test_growth_does_not_depend_on_the_seed_within_the_region(self) -> None:
        exact = select.grow(self.mesh, self.seed, 2.5, 2.5)
        for other in sorted(exact):
            self.assertEqual(select.grow(self.mesh, other, 2.5, 2.5), exact)

    def test_a_180_degree_cone_admits_the_facets_opposite_the_seed(self) -> None:
        # Two antipodal unit normals can have a dot product of -1.0000000000000002,
        # just below cos(180 deg) = -1: every seed still grows the whole band.
        for segments, preset in ((16, "smooth"), (24, "surface")):
            band = F.mesh(F.cylinder_band(10.0, 20.0, segments=segments, closed=True))
            for seed in range(band.facet_count):
                region = select.apply_operations(band, [{"op": "grow", "seed_facet": seed, "preset": preset}])
                self.assertEqual(len(region), band.facet_count, (segments, preset, seed))

    def test_operations_replay_add_subtract_cleanup(self) -> None:
        ops = [
            {"op": "grow", "seed_facet": self.seed, "preset": "smooth"},
            {"op": "grow", "mode": "subtract", "seed_facet": self.seed, "theta_d_deg": 2.5, "theta_c_deg": 2.5},
            {"op": "cleanup", "min_island_mm2": 1.0},
        ]
        result = select.apply_operations(self.mesh, ops)
        exact = select.grow(self.mesh, self.seed, 2.5, 2.5)
        self.assertFalse(result & exact)
        self.assertEqual(select.apply_operations(self.mesh, ops), result)
        facets = sorted(exact)[:3]
        self.assertEqual(select.apply_operations(self.mesh, [{"op": "facets", "facets": facets}]), set(facets))

    def test_disk_selection_grows_with_the_radius(self) -> None:
        small = select.disk(self.mesh, self.seed, 5.0)
        large = select.disk(self.mesh, self.seed, 60.0)
        self.assertIn(self.seed, small)
        self.assertTrue(small <= large)

    def test_malformed_operations_are_rejected(self) -> None:
        bad = [
            [],
            [{"op": "explode"}],
            [{"op": "grow"}],
            [{"op": "grow", "seed_facet": True}],
            [{"op": "grow", "seed_facet": 10**9}],
            [{"op": "grow", "seed_facet": self.seed, "theta_d_deg": 500}],
            [{"op": "grow", "seed_facet": self.seed, "extra": 1}],
            [{"op": "facets", "facets": ["a"]}],
            [{"op": "grow", "seed_facet": self.seed, "mode": "xor"}],
        ]
        for ops in bad:
            with self.subTest(ops=ops):
                with self.assertRaises(SurfaceError) as raised:
                    select.apply_operations(self.mesh, ops)
                self.assertIn(raised.exception.code, ("E_SURFACE_REQUEST", "E_SURFACE_FACET"))
        with self.assertRaises(SurfaceError) as raised:
            select.apply_operations(self.mesh, [{"op": "grow", "seed_facet": self.seed}, {"op": "grow", "mode": "subtract", "seed_facet": self.seed}])
        self.assertEqual(raised.exception.code, "E_SURFACE_SELECTION_EMPTY")

    def test_candidates_list_the_large_regions_first(self) -> None:
        found = select.candidates(self.mesh)
        self.assertGreaterEqual(len(found), 3)
        self.assertEqual(found, sorted(found, key=lambda c: (-c["area_mm2"], c["seed_facet"])))
        # The back wall, the contact face and the two equal side caps are the largest flat regions.
        normals = [tuple(round(c, 2) for c in item["mean_normal"]) for item in found[:4]]
        self.assertIn((-1.0, 0.0, 0.0), normals)
        caps = [item["area_mm2"] for item in found[:4] if abs(item["mean_normal"][1]) > 0.99]
        self.assertEqual(len(caps), 2)
        self.assertAlmostEqual(caps[0], caps[1], places=6)


class ChartTests(unittest.TestCase):
    def test_a_planar_face_is_projected_exactly(self) -> None:
        mesh = F.mesh(F.soft_finger_replica())
        seed = select.nearest_facet(mesh, (0.0, -12.9, -62.7))
        chart = chart_module.build_chart(mesh, select.grow(mesh, seed, 2.5, 2.5))
        self.assertEqual((chart.kind, chart.method), ("planar", "projection"))
        self.assertAlmostEqual(chart.stats["chart_area_mm2"], 119.365 * 25.8, places=3)
        self.assertLess(chart.stats["strain_max"], 1e-9)
        self.assertGreater(chart_module._loop_area(chart.outline()), 0)  # counter-clockwise
        sides = api.boundary_sides(mesh, chart)
        self.assertEqual(sorted(round(s["chord_mm"], 3) for s in sides), [25.8, 25.8, 119.365, 119.365])
        # Seen from outside (looking along +x at the -x face) u points right and v up.
        u_axis, v_axis = chart.axes
        normal = chart.normal
        self.assertAlmostEqual(normal[0], -1.0)
        cross = (u_axis[1] * v_axis[2] - u_axis[2] * v_axis[1], u_axis[2] * v_axis[0] - u_axis[0] * v_axis[2], u_axis[0] * v_axis[1] - u_axis[1] * v_axis[0])
        self.assertAlmostEqual(sum(a * b for a, b in zip(cross, normal)), 1.0)

    def test_a_wrapped_extrusion_unrolls_without_stretch(self) -> None:
        mesh = F.mesh(F.soft_finger_replica())
        seed = select.nearest_facet(mesh, (0.0, -12.9, -62.7))
        region = select.grow(mesh, seed, 30.0, 100.0)
        chart = chart_module.build_chart(mesh, region)
        self.assertEqual((chart.kind, chart.method), ("developable", "unfold"))
        self.assertAlmostEqual(chart.stats["chart_area_mm2"], area(mesh, region), places=6)
        self.assertLess(chart.stats["strain_max"], 1e-9)
        self.assertEqual(chart.stats["flipped_facets"], 0)

    def test_a_sphere_cap_is_curved_and_its_stretch_is_measured(self) -> None:
        mesh = F.mesh(F.sphere_cap(20.0, 40.0, rings=6, segments=20))
        seed = select.nearest_facet(mesh, (0.0, 0.0, 20.0))
        chart = chart_module.build_chart(mesh, select.grow(mesh, seed, 40.0, 180.0))
        self.assertEqual((chart.kind, chart.method), ("curved", "lscm+arap"))
        self.assertEqual(chart.stats["flipped_facets"], 0)
        self.assertGreater(chart.stats["strain_max"], 0.005)
        self.assertLess(chart.stats["strain_max"], 0.2)
        self.assertAlmostEqual(chart.stats["chart_area_mm2"] / chart.stats["area_mm2"], 1.0, delta=0.02)

    def test_a_closed_band_is_opened_along_a_seam(self) -> None:
        mesh = F.mesh(F.cylinder_band(10.0, 20.0, segments=24, closed=True))
        seed = select.nearest_facet(mesh, (10.0, 0.0, 10.0))
        region = select.grow(mesh, seed, 30.0, 180.0)
        self.assertEqual(len(region), mesh.facet_count)
        chart = chart_module.build_chart(mesh, region, seed=seed)
        self.assertEqual(chart.kind, "developable")
        self.assertIsNotNone(chart.stats["seam"])
        self.assertLess(chart.stats["strain_max"], 1e-9)
        # The facets along the seam are dropped; the rest unrolls to its full area.
        self.assertAlmostEqual(chart.stats["chart_area_mm2"], area(mesh, chart.facets), places=6)
        self.assertGreater(area(mesh, chart.facets), 0.9 * area(mesh, region))

    def test_a_band_whose_normals_cancel_out_is_opened_along_a_seam(self) -> None:
        # A box's side walls and closed cylinders of 8 and 36 segments: their
        # area-weighted normals sum to exactly zero, so there is no mean plane.
        box = F.mesh(F.box((10.0, 20.0, 5.0)))
        walls = [f for f in range(box.facet_count) if abs(box.normals[f][2]) < 1e-9]
        cases = [(box, walls, walls[0])]
        for segments in (8, 36):
            band = F.mesh(F.cylinder_band(10.0, 20.0, segments=segments, closed=True))
            cases.append((band, list(range(band.facet_count)), select.nearest_facet(band, (10.0, 0.0, 10.0))))
        for mesh, region, seed in cases:
            self.assertEqual([math.fsum(mesh.normals[f][k] * mesh.areas[f] for f in region) for k in range(3)], [0.0] * 3)
            chart = chart_module.build_chart(mesh, region, seed=seed)
            self.assertEqual((chart.kind, len(chart.loops)), ("developable", 1))
            self.assertIsNotNone(chart.stats["seam"])
            self.assertLess(chart.stats["strain_max"], 1e-9)
            self.assertAlmostEqual(chart.stats["chart_area_mm2"], area(mesh, chart.facets), places=6)

    def test_a_band_of_several_rows_is_opened_along_one_side_of_its_seam(self) -> None:
        # The seam crosses inner vertices here.  Removing the facets on its edges left
        # the two sides of each inner seam vertex meeting at that vertex alone (bowties,
        # so E_SURFACE_NOT_DISK); the seam vertices' fans on one side go instead, one
        # column of the band.  The first three bands' normals cancel out exactly.
        for sides, rows in ((6, 5), (12, 3), (36, 2), (24, 4)):
            mesh = F.mesh(_prism_band(sides, 10.0, 20.0, rows))
            chart = chart_module.build_chart(mesh, range(mesh.facet_count), seed=0)
            self.assertEqual((chart.kind, len(chart.loops), chart.stats["seam"]["removed_facets"]), ("developable", 1, 2 * rows), sides)
            self.assertTrue(chart.stats["topology"]["disk"])
            self.assertLess(chart.stats["strain_max"], 1e-9)
            self.assertAlmostEqual(area(mesh, chart.facets), area(mesh, range(mesh.facet_count)) * (sides - 1) / sides, places=3)
            self.assertAlmostEqual(chart.stats["chart_area_mm2"], area(mesh, chart.facets), places=6)

    def test_thin_strips_unfold_exactly_over_many_rows(self) -> None:
        # Strips much narrower than their rows are long: an unfolding that scaled each
        # facet by its placed edge's length error gained error at every row (2 um of
        # conflict over 20 rows of the R10 sheet, 1.4 m over 40 rows of the R20 one).
        for radius, strips, rows in ((10.0, 40, 20), (20.0, 60, 40)):
            mesh = F.mesh(F.cylinder_sheet(radius, 40.0, strips, rows, 180.0))
            chart = chart_module.build_chart(mesh, range(mesh.facet_count))
            self.assertEqual((chart.kind, chart.method), ("developable", "unfold"), radius)
            self.assertLess(chart.stats["unfold_conflict_mm"], 1e-9)
            self.assertLess(chart.stats["strain_max"], 1e-9)
            self.assertAlmostEqual(chart.stats["chart_area_mm2"], area(mesh, chart.facets), places=6)

    def test_a_doubly_curved_patch_whose_unfolding_nearly_closes_is_curved(self) -> None:
        # A 5 degree cap of a 60 mm sphere in thin facets: the unfolding meets itself
        # within 6 um, under UNFOLD_CONFLICT_MM, but stretches the facets there by 2%;
        # LSCM + ARAP stretch them by 0.1%.  It stays curved 2 m from the origin, where
        # edge lengths may also change by the float32 spacing there, 0.2 um.
        for offset in ((0.0, 0.0, 0.0), (1500.0, 1000.0, -800.0)):
            mesh = F.mesh(_tilted(_welded_cap(60.0, 5.0, 4, 100), offset))
            chart = chart_module.build_chart(mesh, range(mesh.facet_count))
            self.assertLess(chart.stats["unfold_conflict_mm"], chart_module.UNFOLD_CONFLICT_MM)
            self.assertEqual((chart.kind, chart.stats["flipped_facets"]), ("curved", 0), offset)
            self.assertLess(chart.stats["strain_max"], 2e-3)

    def test_needle_facets_and_float32_rounding_leave_a_developable_patch_exact(self) -> None:
        # Two needle facets (apex 0.01 um off the long edge) in a cylinder sheet, and a
        # fine fillet 2 m from the origin, both with two holes: the unfoldings keep every
        # edge length, though the singular values of the needles' map are off by 4e-3 and
        # those of the fillet's float32-rounded 0.04 mm strips by 4e-4.  Tested on those,
        # both went to the curved solve, which refuses holes (E_SURFACE_NOT_DISK).
        needles = _tilted(_needle_sheet(10.0, 24, 4, {(10, 1), (17, 2)}, 1e-5, skip={(5, 1), (14, 2)}), (0.0, 0.0, 0.0))
        fillet = _tilted(F.cylinder_sheet(1.0, 8.0, 40, 3, 90.0, skip={(13, 1), (26, 1)}), (1500.0, 1000.0, -800.0))
        for name, triangles in (("needles", needles), ("fillet", fillet)):
            mesh = F.mesh(triangles)
            chart = chart_module.build_chart(mesh, range(mesh.facet_count))
            self.assertEqual((chart.kind, chart.method, len(chart.holes())), ("developable", "unfold", 2), name)
            self.assertLess(chart.stats["unfold_conflict_mm"], 1e-4)
            self.assertGreater(chart.stats["strain_max"], 1e-4)
            self.assertEqual(chart.stats["flipped_facets"], 0)

    def test_the_point_index_of_a_sliver_fan_holds_each_facet_along_its_length(self) -> None:
        # A face with a finely divided round edge, triangulated as a fan from its centre:
        # each sliver is in the cells its triangle meets, not in every cell of its
        # bounding box (127 entries per facet here, 911 at 16,000 slivers).
        mesh = F.mesh(F.plate(F.ellipse_outline(30.0, 20.0, 2000)))
        seed = select.nearest_facet(mesh, (0.1, 0.2, 3.0))
        chart = chart_module.build_chart(mesh, select.grow(mesh, seed, 10.0, 4.0))
        index = chart_module._grid(chart, mesh)
        self.assertLess(sum(len(bucket) for bucket in index["buckets"].values()), 40 * len(chart.facets))
        # locate finds what a scan of every facet finds: at random points (some off
        # the face), at the corners and on the edges.
        mesh = F.mesh(F.plate(F.ellipse_outline(30.0, 20.0, 300)))
        seed = select.nearest_facet(mesh, (0.1, 0.2, 3.0))
        chart = chart_module.build_chart(mesh, select.grow(mesh, seed, 10.0, 4.0))
        rng = random.Random(7)
        points = [(rng.uniform(-31.0, 31.0), rng.uniform(-21.0, 21.0)) for _ in range(300)]
        for facet in chart.facets[::7]:
            p, q, r = chart.facet_uv(facet, mesh)
            points += [p, ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2), ((q[0] + r[0]) / 2, (q[1] + r[1]) / 2)]
        for point in points:
            self.assertEqual(chart_module.locate(chart, mesh, point), _locate_by_scan(chart, mesh, point), point)

    def test_an_open_cylinder_band_unrolls_to_its_arc_length(self) -> None:
        mesh = F.mesh(F.cylinder_band(10.0, 20.0, segments=12, closed=False, sweep_deg=120.0))
        seed = select.nearest_facet(mesh, (10.0, 0.5, 10.0))
        chart = chart_module.build_chart(mesh, select.grow(mesh, seed, 30.0, 180.0))
        self.assertEqual(chart.kind, "developable")
        xs = [p[0] for p in chart.outline()]
        ys = [p[1] for p in chart.outline()]
        chord = 2 * 10.0 * math.sin(math.radians(10.0 / 2))  # 12 segments over 120 degrees
        self.assertAlmostEqual(sorted([max(xs) - min(xs), max(ys) - min(ys)])[1], max(20.0, 12 * chord), places=6)

    def test_charts_are_deterministic(self) -> None:
        mesh = F.mesh(F.sphere_cap(20.0, 30.0, rings=4, segments=12))
        seed = select.nearest_facet(mesh, (0.0, 0.0, 20.0))
        region = select.grow(mesh, seed, 40.0, 180.0)
        first = chart_module.build_chart(mesh, region)
        second = chart_module.build_chart(mesh, region)
        self.assertEqual(first.uv, second.uv)

    def test_chart_points_map_back_onto_the_surface(self) -> None:
        mesh = F.mesh(F.cylinder_band(10.0, 20.0, segments=12, closed=False, sweep_deg=120.0))
        seed = select.nearest_facet(mesh, (10.0, 0.5, 10.0))
        chart = chart_module.build_chart(mesh, select.grow(mesh, seed, 30.0, 180.0))
        for facet in chart.facets:
            uv = [chart.uv[v] for v in mesh.facets[facet]]
            centre = (sum(p[0] for p in uv) / 3, sum(p[1] for p in uv) / 3)
            point, found = chart_module.chart_point_to_3d(chart, mesh, centre)
            self.assertEqual(found, facet)
            expected = mesh.centroids[facet]
            self.assertLess(math.dist(point, expected), 1e-9)

    def test_an_inside_out_stl_gives_the_same_chart(self) -> None:
        cases = [
            (F.soft_finger_replica(), (0.0, -12.9, -62.7), (2.5, 2.5), "planar"),
            (F.soft_finger_replica(), (0.0, -12.9, -62.7), (30.0, 100.0), "developable"),
            (F.cylinder_band(10.0, 20.0, segments=24, closed=True), (10.0, 0.0, 10.0), (30.0, 180.0), "developable"),
            (F.sphere_cap(20.0, 40.0, rings=6, segments=20), (0.0, 0.0, 20.0), (40.0, 180.0), "curved"),
        ]
        for triangles, pick, limits, kind in cases:
            charts = []
            for version in (triangles, F.reversed_winding(triangles)):
                mesh = F.mesh(version)
                seed = select.nearest_facet(mesh, pick)
                chart = chart_module.build_chart(mesh, select.grow(mesh, seed, *limits), seed=seed)
                self.assertEqual((chart.kind, chart.stats["flipped_facets"]), (kind, 0))
                charts.append({mesh.vertices[v]: p for v, p in chart.uv.items()})
            self.assertEqual(charts[0].keys(), charts[1].keys())
            self.assertLess(max(math.dist(charts[0][k], charts[1][k]) for k in charts[0]), 1e-6, kind)

    def test_a_face_with_one_hole_is_kept_whole(self) -> None:
        mesh = F.mesh(F.holed_plate())
        seed = select.nearest_facet(mesh, (10.0, 10.0, 3.0))
        top = select.grow(mesh, seed, 10.0, 4.0)
        chart = chart_module.build_chart(mesh, top, seed=seed)
        self.assertEqual((chart.kind, chart.stats["seam"], len(chart.loops)), ("planar", None, 2))
        self.assertEqual(len(chart.facets), len(top))
        self.assertAlmostEqual(chart.stats["chart_area_mm2"], 2400.0 - 16.0, places=6)
        self.assertEqual(len(chart.holes()), 1)
        # A cylindrical sheet with one hole unrolls exactly, hole and all.
        sheet = F.mesh(F.cylinder_sheet(10.0, 20.0, 12, 6, 120.0, skip={(6, 3)}))
        seed = select.nearest_facet(sheet, (10.0, 0.5, 2.0))
        region = select.grow(sheet, seed, 30.0, 180.0)
        self.assertEqual(len(region), sheet.facet_count)
        chart = chart_module.build_chart(sheet, region, seed=seed)
        self.assertEqual((chart.kind, chart.stats["seam"], len(chart.holes())), ("developable", None, 1))
        self.assertLess(chart.stats["strain_max"], 1e-9)

    def test_a_selection_in_separate_pieces_is_refused(self) -> None:
        mesh = F.mesh(F.box((40.0, 40.0, 5.0)) + F.box((10.0, 10.0, 5.0), origin=(60.0, 0.0, 0.0)))
        tops = [f for f in range(mesh.facet_count) if abs(mesh.centroids[f][2] - 5.0) < 1e-9]
        with self.assertRaises(SurfaceError) as raised:
            chart_module.build_chart(mesh, tops)
        self.assertEqual((raised.exception.code, raised.exception.details["pieces"]), ("E_SURFACE_NOT_DISK", 2))

    def test_a_fold_reached_only_through_a_t_junction_unfolds(self) -> None:
        # Two plates meet at a 10 degree fold; the far plate's vertex (10, 5) lies on the
        # near plate's fold edge, so the plates are joined by that T-junction alone.
        h = 10.0 * math.tan(math.radians(10.0))
        near = [((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 10.0, 0.0)), ((0.0, 0.0, 0.0), (10.0, 10.0, 0.0), (0.0, 10.0, 0.0))]
        far = [
            ((10.0, 0.0, 0.0), (20.0, 0.0, h), (10.0, 5.0, 0.0)),
            ((10.0, 5.0, 0.0), (20.0, 0.0, h), (20.0, 10.0, h)),
            ((10.0, 5.0, 0.0), (20.0, 10.0, h), (10.0, 10.0, 0.0)),
        ]
        mesh = F.mesh(near + far)
        self.assertEqual(mesh.stats["t_junction_links"], 2)
        region = select.grow(mesh, 0, 30.0, 180.0)
        self.assertEqual(len(region), 5)
        chart = chart_module.build_chart(mesh, region, seed=0)
        self.assertEqual((chart.kind, chart.method, len(chart.loops)), ("developable", "unfold", 1))
        self.assertLess(chart.stats["strain_max"], 1e-9)
        self.assertAlmostEqual(chart.stats["chart_area_mm2"], area(mesh, region), places=9)

    def test_t_junctions_on_curved_surfaces_flatten_like_the_clean_mesh(self) -> None:
        cases = [
            (F.cylinder_sheet(10.0, 20.0, 12, 6, 120.0), (10.0, 0.5, 2.0), "developable"),
            (F.sphere_cap(20.0, 40.0, rings=6, segments=20), (0.0, 0.0, 20.0), "curved"),
        ]
        for triangles, pick, kind in cases:
            areas = []
            for version in (triangles, F.with_t_junction(triangles, len(triangles) // 2)):
                mesh = F.mesh(version)
                seed = select.nearest_facet(mesh, pick)
                region = select.grow(mesh, seed, 40.0, 180.0)
                self.assertEqual(len(region), mesh.facet_count)
                chart = chart_module.build_chart(mesh, region, seed=seed)
                self.assertEqual((chart.kind, len(chart.loops), chart.stats["flipped_facets"]), (kind, 1, 0))
                areas.append(chart.stats["chart_area_mm2"])
            self.assertAlmostEqual(areas[0], areas[1], delta=1e-3 * areas[0])


class SolveTests(unittest.TestCase):
    def test_a_curved_solve_factors_each_matrix_once(self) -> None:
        # LSCM and ARAP factor their matrices once each, ARAP for all its global
        # steps; conjugate gradients alone took 8-12 s at 2,900 vertices.
        mesh = F.mesh(_welded_cap(20.0, 40.0, 6, 24))
        calls = []
        factor = solve._factor

        def counting(rows):
            calls.append(len(rows))
            return factor(rows)

        with mock.patch.object(solve, "_factor", counting), mock.patch.object(solve, "_pcg", side_effect=AssertionError("CG")):
            chart = chart_module._build_chart(mesh, tuple(range(mesh.facet_count)), allow_curved=True, seed=None)
        self.assertEqual(chart.kind, "curved")
        vertices = len(chart.vertices)
        self.assertEqual(calls, [2 * vertices - 4, vertices - 1])  # two vertices pinned, then one

    def test_a_curved_chart_can_start_from_a_larger_charts_uv(self) -> None:
        # The fit's strain limit flattens disks of a curved selection again: their
        # ARAP can start from the selection's chart instead of from LSCM.  Such
        # charts stay out of the cache, which holds charts built from scratch.
        mesh = F.mesh(_welded_cap(20.0, 40.0, 6, 24))
        whole = chart_module.build_chart(mesh, range(mesh.facet_count))
        disk = select.disk(mesh, 0, 8.0, 180.0)
        cached = list(chart_module._CHART_CACHE)
        warm = chart_module.build_chart(mesh, disk, initial=whole.uv)
        self.assertEqual(list(chart_module._CHART_CACHE), cached)
        cold = chart_module.build_chart(mesh, disk)
        self.assertEqual((warm.kind, warm.method, cold.method, warm.stats["flipped_facets"]), ("curved", "arap", "lscm+arap", 0))
        self.assertAlmostEqual(warm.stats["strain_max"], cold.stats["strain_max"], delta=0.1 * cold.stats["strain_max"])

    def test_the_factorization_solves_a_pinned_laplacian(self) -> None:
        # A weighted path 0-1-...-9 with unknown 0 pinned at 2.
        rows = [dict() for _ in range(10)]
        for i in range(9):
            for a, b in ((i, i + 1), (i + 1, i)):
                rows[a][a] = rows[a].get(a, 0.0) + i + 1.0
                rows[a][b] = rows[a].get(b, 0.0) - i - 1.0
        rhs = [math.sin(i) for i in range(10)]
        x = solve._solve_pinned(rows, {0: 2.0}, rhs)
        self.assertEqual(x[0], 2.0)
        for i in range(1, 10):
            self.assertAlmostEqual(math.fsum(a * x[j] for j, a in rows[i].items()), rhs[i], places=9)

    def test_a_system_without_positive_pivots_falls_back_to_cg(self) -> None:
        # The third unknown is in no equation: no factorization; CG leaves it at 0.
        rows = [{0: 2.0, 1: -1.0}, {0: -1.0, 1: 2.0}, {}]
        self.assertIsNone(solve._factor([sorted(row.items()) for row in rows]))
        for got, want in zip(solve._solve_pinned(rows, {}, [1.0, 0.0, 0.0]), (2 / 3, 1 / 3, 0.0)):
            self.assertAlmostEqual(got, want, places=9)


@unittest.skipUnless((ASSETS / "crank_gripper" / "tip_left.stl").exists(), "asset/ meshes are not committed")
class AssetChartTests(unittest.TestCase):
    def test_the_example_surfaces(self) -> None:
        from surface.mesh import read_stl

        soft = read_stl((ASSETS / "soft_gripper_finger.stl").read_bytes())
        seed = select.nearest_facet(soft, (0.0, -12.9, -62.7))
        face = select.grow(soft, seed, **_preset("flat"))
        self.assertAlmostEqual(area(soft, face), 3087.71, delta=0.01)
        self.assertEqual(chart_module.build_chart(soft, face).kind, "planar")
        crank = read_stl((ASSETS / "crank_gripper" / "tip_left.stl").read_bytes())
        seed = select.nearest_facet(crank, (1.812, -213.721, 138.929))
        pad = select.grow(crank, seed, **_preset("flat"))
        self.assertEqual(len(pad), 14)
        self.assertAlmostEqual(area(crank, pad), 2957.317, delta=0.01)
        chart = chart_module.build_chart(crank, pad)
        self.assertEqual((chart.kind, chart.method), ("developable", "unfold"))
        self.assertLess(chart.stats["strain_max"], 1e-9)


def _preset(name: str) -> dict:
    preset = select.PRESETS[name]
    return {"theta_d_deg": preset["theta_d_deg"], "theta_c_deg": preset["theta_c_deg"]}


def _welded_cap(radius: float, cap_deg: float, rings: int, segments: int) -> list:
    """A spherical cap round +z whose rings close on themselves (one pole vertex)."""

    def point(i: int, j: int) -> tuple:
        theta = math.radians(cap_deg) * i / rings
        phi = 2 * math.pi * (j % segments) / segments
        return (radius * math.sin(theta) * math.cos(phi), radius * math.sin(theta) * math.sin(phi), radius * math.cos(theta))

    triangles = []
    for i in range(rings):
        for j in range(segments):
            a, b, c, d = point(i, j), point(i, j + 1), point(i + 1, j), point(i + 1, j + 1)
            triangles += [(a, c, d)] if i == 0 else [(a, c, d), (a, d, b)]
    return triangles


def _prism_band(sides: int, radius: float, height: float, rows: int) -> list:
    """The side walls of a regular prism, ``rows`` facet rows high, welded all the way round."""

    ring = [(radius * math.cos(2 * math.pi * j / sides), radius * math.sin(2 * math.pi * j / sides)) for j in range(sides)]
    triangles = []
    for j in range(sides):
        (x0, y0), (x1, y1) = ring[j], ring[(j + 1) % sides]
        for k in range(rows):
            a, b = (x0, y0, height * k / rows), (x1, y1, height * k / rows)
            c, d = (x0, y0, height * (k + 1) / rows), (x1, y1, height * (k + 1) / rows)
            triangles += [(a, b, d), (a, d, c)]
    return triangles


def _needle_sheet(radius: float, segments: int, rows: int, needles, gap: float, skip=()) -> list:
    """A 120 degree cylinder sheet 12 mm tall (F.cylinder_sheet); each cell in ``needles``
    is a fan round a point ``gap`` mm above the middle of its bottom edge, in the cell's
    plane, so the facet on that edge is a needle."""

    def point(i: int, k: int) -> tuple:
        angle = math.radians(120.0) * i / segments
        return (radius * math.cos(angle), radius * math.sin(angle), 12.0 * k / rows)

    triangles = []
    for i in range(segments):
        for k in range(rows):
            if (i, k) in skip:
                continue
            a, b, c, d = point(i, k), point(i + 1, k), point(i + 1, k + 1), point(i, k + 1)
            if (i, k) in needles:
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, a[2] + gap)
                triangles += [(a, b, m), (b, c, m), (c, d, m), (d, a, m)]
            else:
                triangles += [(a, b, c), (a, c, d)]
    return triangles


def _tilted(triangles, offset) -> list:
    """The triangles turned 37 degrees about (1, 1, 0.3), then moved by ``offset`` (off the axes,
    so their float32 coordinates round)."""

    length = math.sqrt(2.09)
    axis = (1 / length, 1 / length, 0.3 / length)
    c, s = math.cos(math.radians(37.0)), math.sin(math.radians(37.0))

    def turn(p) -> tuple:
        along = axis[0] * p[0] + axis[1] * p[1] + axis[2] * p[2]
        across = (axis[1] * p[2] - axis[2] * p[1], axis[2] * p[0] - axis[0] * p[2], axis[0] * p[1] - axis[1] * p[0])
        return tuple(p[k] * c + across[k] * s + axis[k] * along * (1 - c) + offset[k] for k in range(3))

    return [tuple(turn(p) for p in triangle) for triangle in triangles]


def _locate_by_scan(chart, mesh, point):
    """chart.locate without its index: the best of all facets, ties to the first."""

    best = None
    for facet in chart.facets:
        p, q, r = chart.facet_uv(facet, mesh)
        whole = chart_module._tri_area(p, q, r)
        if whole == 0:
            continue
        l1 = chart_module._tri_area(p, point, r) / whole
        l2 = chart_module._tri_area(p, q, point) / whole
        l0 = 1 - l1 - l2
        if best is None or min(l0, l1, l2) > best[0]:
            best = (min(l0, l1, l2), facet, (l0, l1, l2))
    if best is None or best[0] < -1e-9:
        return None
    return best[1], best[2]


if __name__ == "__main__":
    unittest.main()
