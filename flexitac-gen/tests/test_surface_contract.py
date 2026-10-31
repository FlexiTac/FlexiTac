"""CAD mode's contract details the API review of 2026-10-20 found untested.

Mesh caps and units, hidden seeds, the operation cap, partly covered walls;
the API's unknown keys, error details, inspect lists and header cap; and
what the fit options do on a face with a block standing on it (obstacles,
edge margin, tail extension, placement, rotation, objective, picked side).
The final review's request findings: damaged placements, the cost of the
map's checks on strips, fans and large faces, the spacing tolerance under
a raised strain limit, the overlay beyond an arc's chord, the digit guard
and the mesh cache's memory bound.
"""

from __future__ import annotations

import copy
import math
import struct
import time
import unittest
from unittest import mock

from engine import generate_design
from engine.geometry import point_in_polygon, segments_intersect
from surface import api, fit, place, select
from surface.chart import chart_point_to_3d
from surface.errors import SURFACE_ERROR_CODES, SurfaceError
from surface.mesh import read_stl

try:
    import surface_fixtures as F
except ImportError:  # run as a package
    from tests import surface_fixtures as F


class MeshAndSelectionContractTests(unittest.TestCase):
    def test_caps_units_and_hidden_seeds(self) -> None:
        box = F.box()
        with self.assertRaises(SurfaceError) as raised:
            read_stl(F.ascii_stl(box), unit="mm", max_facets=11)
        self.assertEqual(raised.exception.code, "E_SURFACE_MESH_TOO_LARGE")
        mm = read_stl(F.stl_bytes(box), unit="mm")
        cm = read_stl(F.stl_bytes(box), unit="cm")
        self.assertEqual((cm.scale_mm, cm.unit), (10.0, "cm"))
        self.assertAlmostEqual(cm.stats["extent_mm"][1], 10 * mm.stats["extent_mm"][1])
        # A part under 2 units is taken to be in metres, a larger one in millimetres.
        self.assertEqual(read_stl(F.stl_bytes(F.box((1.0, 1.9, 0.5)))).unit, "m")
        self.assertEqual(read_stl(F.stl_bytes(F.box((1.0, 2.1, 0.5)))).unit, "mm")
        # Hidden facets (the wall where two boxes touch) cannot seed a selection.
        two = F.mesh(F.box() + F.box(origin=(10.0, 0.0, 0.0)))
        hidden = min(two.hidden)
        with self.assertRaises(SurfaceError) as raised:
            select.apply_operations(two, [{"op": "grow", "seed_facet": hidden}])
        self.assertEqual(raised.exception.code, "E_SURFACE_FACET")
        ops = [{"op": "facets", "facets": [0]}] * (select.MAX_OPERATIONS + 1)
        with self.assertRaises(SurfaceError) as raised:
            select.apply_operations(two, ops)
        self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")
        with self.assertRaises(KeyError):
            SurfaceError("E_SURFACE_UNKNOWN")

    def test_a_wall_covered_over_most_of_its_area_is_still_partly_free(self) -> None:
        # A 10 x 10 box on a 10 x 16 face covers 62% of it: not hidden (under 99%), an obstacle.
        mesh = F.mesh(F.box((10.0, 16.0, 5.0)) + F.box((10.0, 10.0, 5.0), origin=(0.0, 0.0, 5.0)))
        top = [f for f in range(12) if abs(mesh.centroids[f][2] - 5.0) < 1e-9]
        self.assertTrue(all(f not in mesh.hidden for f in top))
        self.assertTrue(all(f in mesh.covered for f in top))


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        triangles = F.box((40.0, 30.0, 10.0)) + F.box((10.0, 10.0, 5.0), origin=(5.0, 5.0, 10.0))
        cls.data = F.stl_bytes(triangles)
        cls.mesh = F.mesh(triangles)
        cls.seed = select.nearest_facet(cls.mesh, (30.0, 20.0, 10.0))
        cls.selection = {"ops": [{"op": "grow", "seed_facet": cls.seed}]}

    def test_inspect_lists_hidden_facets_and_each_preset(self) -> None:
        two = F.box() + F.box(origin=(10.0, 0.0, 0.0))
        reply = api.inspect({"unit": "mm"}, F.stl_bytes(two))
        self.assertEqual(len(reply["hidden_facets"]), 4)
        soft = F.stl_bytes(F.soft_finger_replica())
        candidates = api.inspect({"unit": "mm"}, soft)["candidates"]
        self.assertEqual({item["preset"] for item in candidates["smooth"]}, {"smooth"})
        self.assertGreater(candidates["smooth"][0]["area_mm2"], candidates["flat"][0]["area_mm2"])

    def test_unknown_keys_and_select_error_details(self) -> None:
        for route, header in (
            (api.fit, {"selection": self.selection, "surprise": 1}),
            (api.map_placement, {"selection": self.selection, "placement": {}, "design": {}, "surprise": 1}),
            (api.select_surface, {"selection": dict(self.selection, more=1)}),
        ):
            with self.assertRaises(SurfaceError) as raised:
                route(header, self.data)
            self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST", header)
        # A selection that cannot be charted names its facets, for the browser to draw.
        tops = [f for f in range(self.mesh.facet_count) if abs(self.mesh.centroids[f][2] - 10.0) < 1e-9 and f not in self.mesh.hidden]
        far = [f for f in range(self.mesh.facet_count) if abs(self.mesh.centroids[f][2]) < 1e-9]
        with self.assertRaises(SurfaceError) as raised:
            api.select_surface({"selection": {"ops": [{"op": "facets", "facets": tops + far}]}}, self.data)
        self.assertEqual(raised.exception.details["facets"], sorted(set(tops + far) - self.mesh.hidden))

    def test_the_header_size_cap(self) -> None:
        saved = api.MAX_HEADER_BYTES
        api.MAX_HEADER_BYTES = 8
        try:
            body = struct.pack(">I", 9) + b"{" + b" " * 7 + b"}" + b"mesh"
            with self.assertRaises(SurfaceError):
                api.split_body(body)
            body = struct.pack(">I", 8) + b"{" + b" " * 6 + b"}" + b"mesh"
            self.assertEqual(api.split_body(body), (b"{      }", b"mesh"))
        finally:
            api.MAX_HEADER_BYTES = saved

    def test_the_digit_guard_takes_linear_time(self) -> None:
        # 400 runs of 4300 digits (1.7 MB): searching from every digit took seconds.
        header = b'{"x": [' + b",".join([b"1" * api.MAX_NUMBER_DIGITS] * 400) + b"]}"
        start = time.monotonic()
        self.assertEqual(api.split_body(struct.pack(">I", len(header)) + header + b"mesh"), (header, b"mesh"))
        self.assertLess(time.monotonic() - start, 1.0)
        # A longer run is still refused, wherever it stands.
        for header in (b'{"x": -' + b"9" * 4301 + b"}", b'{"x": [1, 22, ' + b"9" * 4400 + b"]}"):
            with self.assertRaises(SurfaceError):
                api.split_body(struct.pack(">I", len(header)) + header)

    def test_the_mesh_cache_counts_bend_measurements(self) -> None:
        first_bytes, second_bytes = F.stl_bytes(F.box((10.0, 20.0, 5.0))), F.stl_bytes(F.box((11.0, 20.0, 5.0)))
        saved = api.MESH_CACHE_FACETS
        first = api.load_mesh({"unit": "mm"}, first_bytes)
        try:
            api.MESH_CACHE_FACETS = 40
            second = api.load_mesh({"unit": "mm"}, second_bytes)
            # 12 + 12 facets: both stay.
            self.assertTrue((first.sha256, "mm") in api._MESH_CACHE)
            # The first mesh's bend measurements grow (40 of them weigh 20 facets): the next request evicts it.
            first.bend_cache.update({(k, k + 1): None for k in range(40)})
            self.assertIs(api.load_mesh({"unit": "mm"}, second_bytes), second)
            self.assertFalse((first.sha256, "mm") in api._MESH_CACHE, "the first mesh is still cached")
            self.assertTrue((second.sha256, "mm") in api._MESH_CACHE)
        finally:
            api.MESH_CACHE_FACETS = saved
            first.bend_cache.clear()
            api._MESH_CACHE.pop((first.sha256, "mm"), None)


class FitContractTests(unittest.TestCase):
    """The fit's options do what they say, on a 40 x 30 mm face with a 10 mm block standing on it."""

    @classmethod
    def setUpClass(cls) -> None:
        ApiContractTests.setUpClass.__func__(cls)
        cls.results = {}

    def fitted(self, **options) -> dict:
        key = repr(sorted(options.items()))
        if key not in self.results:
            header = {"selection": self.selection, "base": options.pop("base", "auto"), "options": dict(options, proposals=3)}
            self.results[key] = fit.fit_route(header, self.data)
        return self.results[key]

    def mapped(self, proposal) -> dict:
        return place.map_route({"selection": self.selection, "placement": proposal["placement"], "design": proposal["design"]}, self.data)

    def test_the_block_is_never_covered_and_the_margin_holds(self) -> None:
        result = self.fitted(pitch_mm=1.5, rotation="none")
        self.assertGreater(result["obstacles"]["covered"], 0)
        for proposal in result["proposals"]:
            mapped = self.mapped(proposal)
            self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
            for taxel in mapped["taxels"]:
                x, y, _ = taxel["xyz_mm"]
                self.assertFalse(5.0 < x < 15.0 and 5.0 < y < 15.0, taxel)
        for proposal in self.fitted(pitch_mm=1.5, rotation="none", edge_margin_mm=1.0)["proposals"]:
            self.assertGreaterEqual(proposal["metrics"]["min_clearance_mm"], 1.0 - 1e-6)

    def test_tails_reach_the_extension_beyond_the_exit(self) -> None:
        for extension in (20.0, 9.0):
            # The whole stack on the face (containment board): each tail crosses the exit and ends the extension beyond it.
            proposal = self.fitted(pitch_mm=2.0, rotation="none", tail_extension_mm=extension, containment="board")["proposals"][0]
            reach = [r["measured"] for r in self.mapped(proposal)["verification"] if r["rule"].endswith("_tail_reach")]
            self.assertEqual(len(reach), 2)
            for value in reach:
                self.assertGreaterEqual(value, extension - 1e-6)
                self.assertLess(value, extension + 0.01)
            # Field-only containment (the default from masked-field phase P5e on): a tail root may lie beyond the exit,
            # and each tail ends at least the extension beyond the face's edge below it.
            proposal = self.fitted(pitch_mm=2.0, rotation="none", tail_extension_mm=extension)["proposals"][0]
            self.assertEqual(proposal["metrics"]["containment"], "field")
            mapped = self.mapped(proposal)
            self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
            reach = [r["measured"] for r in mapped["verification"] if r["rule"].endswith("_tail_reach")]
            self.assertEqual(len(reach), 2)
            for value in reach:
                self.assertGreaterEqual(value, extension - 1e-6)

    def test_a_damaged_placement_is_refused_before_the_geometry(self) -> None:
        proposal = self.fitted(pitch_mm=2.0, rotation="none")["proposals"][0]
        segments = len(api.selection_chart(self.mesh, self.selection)[1].outline())

        def nested(depth: int) -> list:
            value: list = []
            for _ in range(depth - 1):
                value = [value]
            return value

        damages = {
            "null base_to_uv": {"base_to_uv": None},
            "exit edge past the outline": {"exit_edges": [segments]},
            "huge exit edge": {"exit_edges": [10 ** 30]},
            "base_from_uv overflows the frame": {"base_from_uv": [1e308, 1e308]},
            "huge integer inward vector": {"base_inward_uv": [10 ** 200, 0]},
            "field origin overflows the grids": {"field_origin_base": [1.7e308, -1.7e308], "base_inward_uv": [0.6, 0.8]},
            "inward vector not unit": {"base_inward_uv": [0.6, 0.6]},
            "short inward vector": {"base_inward_uv": [1e-5, 0.0]},
            # The disk's chart is one facet: three outline segments, fewer than the exit's number.
            "strain-limited disk without the exit": {"strain_limited": {"centre_facet": self.seed, "radius_mm": 1e-3}, "exit_edges": [3]},
            # The reply echoes the placement: nesting the encoders cannot write back is damage too.
            "an unknown key nested too deeply": {"note": nested(place.MAX_PLACEMENT_DEPTH)},
            "a known object nested too deeply": {"mesh": dict(proposal["placement"]["mesh"], name=nested(40))},
        }
        for name, change in damages.items():
            placement = copy.deepcopy(proposal["placement"])
            placement.update(change)
            with self.assertRaises(SurfaceError, msg=name) as raised:
                place.map_route({"selection": self.selection, "placement": placement, "design": proposal["design"]}, self.data)
            self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST", name)
        # A missing base_to_uv is optional (the frame then starts and ends at base_from_uv), and
        # an unknown key within the nesting bound is echoed.
        placement = {k: v for k, v in proposal["placement"].items() if k != "base_to_uv"}
        placement["note"] = nested(place.MAX_PLACEMENT_DEPTH - 1)
        mapped = place.map_route({"selection": self.selection, "placement": placement, "design": proposal["design"]}, self.data)
        self.assertEqual((mapped["ok"], mapped["placement"]["note"]), (True, placement["note"]))

    def test_placement_rotation_objective_and_side(self) -> None:
        # For the masked fields with the whole board on the face (containment board, phase P4) and those of field-only
        # containment (the default from phase P5e on).  (The rectangles of shape rectangle, the raster search's own
        # proposals, are gone with P5-diagonal-bus.md section 26.16; Whole board still merges them.)
        for containment in ("board", "field"):
            with self.subTest(containment=containment):
                extra = {"containment": containment}
                far = self.fitted(pitch_mm=2.0, rotation="none", **extra)["proposals"][0]
                near = self.fitted(pitch_mm=2.0, rotation="none", placement="near", **extra)["proposals"][0]
                self.assertEqual((far["metrics"]["rows"], far["metrics"]["columns"]), (near["metrics"]["rows"], near["metrics"]["columns"]))
                # A masked field takes the lowest of the heights the search found it at (here one: the face's bottom); the
                # count never depends on the placement (test_mask_fit).
                self.assertEqual(near["metrics"]["taxels"], far["metrics"]["taxels"])
                self.assertLessEqual(near["placement"]["field_origin_base"][1], far["placement"]["field_origin_base"][1])
                self.assertLessEqual(near["metrics"]["row_tail_mm"], far["metrics"]["row_tail_mm"])
                self.assertTrue(all(p["metrics"]["angle_deg"] == 0.0 for p in self.fitted(pitch_mm=2.0, rotation="none", **extra)["proposals"]))
                # max_area ranks by the field's area: a masked field's crossing region P (its coverage).  Section 26.17 put
                # a symmetric face's symmetric fields first with field containment whatever another field held (here the
                # symmetric 0.567 and 0.558 before an asymmetric 0.738); since section 26.19 (the user's threshold of 20 %,
                # in area with max_area) only within 1.2 times: the asymmetric 0.738 holds 30 % more, so the fields go by
                # area, the symmetric ones after the three proposals.
                proposals = self.fitted(objective="max_area", rotation="none", **extra)["proposals"]
                coverage = [p["metrics"]["field_coverage"] for p in proposals]
                lead = 0
                while lead < len(proposals) and (proposals[lead]["metrics"].get("symmetry") or {}).get("field"):
                    lead += 1
                self.assertEqual(lead, 0)
                self.assertEqual(coverage[:lead], sorted(coverage[:lead], reverse=True))
                self.assertEqual(coverage[lead:], sorted(coverage[lead:], reverse=True))
                sides = api.boundary_sides(self.mesh, api.selection_chart(self.mesh, self.selection)[1])
                for side in (0, len(sides) - 1):
                    result = self.fitted(pitch_mm=2.0, rotation="none", base={"side": side}, **extra)
                    self.assertEqual([b["side"] for b in result["bases"]], [side])
                    self.assertTrue(all(p["placement"]["base_side"] == side for p in result["proposals"]))


class MapVerificationTests(unittest.TestCase):
    """The map's checks: what they measure, and that they stay cheap on strips, fans and large faces."""

    @staticmethod
    def fitted(triangles, pick, preset: str = "surface", base: object = "auto", **options) -> tuple:
        data, mesh = F.stl_bytes(triangles), F.mesh(triangles)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, pick), "preset": preset}]}
        result = fit.fit_route({"selection": selection, "base": base, "options": dict({"proposals": 1}, **options)}, data)
        return data, mesh, selection, result

    def test_the_distance_check_measures_each_taxel_once(self) -> None:
        # A half cylinder exported as 60 mm strips, and a plate whose top is a fan of slivers:
        # a grid of facet boxes tested about a hundred facets per taxel on both.
        for name, triangles, pick, preset in (
            ("strips", F.cylinder_band(20.0, 60.0, segments=120, closed=False, sweep_deg=180.0), (0.0, 20.0, 30.0), "smooth"),
            ("fan", F.plate(F.ellipse_outline(30.0, 20.0, 400)), (0.0, 0.0, 3.0), "surface"),
        ):
            data, mesh, selection, result = self.fitted(triangles, pick, preset, pitch_mm=2.0, rotation="none")
            proposal = result["proposals"][0]
            calls = []
            measure = select.point_triangle_distance
            with mock.patch.object(select, "point_triangle_distance", lambda *a: calls.append(1) or measure(*a)):
                mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
            self.assertTrue(mapped["ok"], (name, [r for r in mapped["verification"] if not r["passed"]]))
            self.assertGreater(mapped["taxel_count"], 100, name)
            self.assertLessEqual(len(calls), mapped["taxel_count"], name)
        # On the fan: a point off its facet is measured, and a facet outside the selection is no surface.
        _, chart = api.selection_chart(mesh, selection)
        facet = chart.facets[0]
        centre = tuple(c + 0.25 * n for c, n in zip(mesh.centroids[facet], mesh.normals[facet]))
        self.assertAlmostEqual(place._surface_distance(mesh, chart, [(centre, facet)]), 0.25)
        selected = set(chart.facets)
        outside = next(f for f in range(mesh.facet_count) if f not in selected)
        self.assertEqual(place._surface_distance(mesh, chart, [(mesh.centroids[outside], outside)]), math.inf)

    def test_strain_under_the_boards_stops_at_the_most_stretched_facet(self) -> None:
        def brute(chart, mesh, frame, polygons) -> float:
            # Every facet a polygon overlaps (a corner inside, crossing edges, or the polygon inside).
            worst = 0.0
            for f in chart.facets:
                triangle = [frame.to_base(chart.uv[v]) for v in mesh.facets[f]]
                for polygon in polygons:
                    if (
                        any(point_in_polygon(p, polygon) for p in triangle)
                        or any(segments_intersect(triangle[k - 1], triangle[k], polygon[m - 1], polygon[m]) for k in range(3) for m in range(len(polygon)))
                        or point_in_polygon(polygon[0], triangle)
                    ):
                        worst = max(worst, max(abs(s - 1) for s in chart.strain[f]))
            return worst

        class Counting(fit.BaseFrame):
            calls = 0

            def to_base(self, p):
                Counting.calls += 1
                return super().to_base(p)

        def square(chart, fx: float, fy: float, half: float) -> list:
            xs = [p[0] for p in chart.uv.values()]
            ys = [p[1] for p in chart.uv.values()]
            cx, cy = min(xs) + fx * (max(xs) - min(xs)), min(ys) + fy * (max(ys) - min(ys))
            return [(cx - half, cy - half), (cx + half, cy - half), (cx + half, cy + half), (cx - half, cy + half)]

        # On a dome the stretch varies: the answer is the exhaustive one.
        dome = F.sphere_cap(60.0, 25.0, rings=8, segments=32)
        mesh = F.mesh(dome)
        _, chart = api.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (0.0, 0.0, 60.0)), "preset": "smooth"}]})
        frame = fit.BaseFrame({"from_uv": [0.0, 0.0], "to_uv": [1.0, 0.0], "inward_uv": [0.0, 1.0]})
        for polygons in ([square(chart, 0.5, 0.5, 4.0)], [square(chart, 0.15, 0.5, 3.0), square(chart, 0.8, 0.3, 2.0)], [square(chart, 3.0, 3.0, 1.0)]):
            self.assertEqual(place._strain_under(chart, mesh, frame, polygons), brute(chart, mesh, frame, polygons))
        # On a large flat sheet only a few facets get the exact test (all of them did).
        sheet = []
        for i in range(40):
            for j in range(40):
                a, b, c, d = (i, j, 0.0), (i + 1, j, 0.0), (i + 1, j + 1, 0.0), (i, j + 1, 0.0)
                sheet += [(a, b, c), (a, c, d)]
        mesh = F.mesh(sheet)
        _, chart = api.selection_chart(mesh, {"ops": [{"op": "grow", "seed_facet": 0}]})
        frame = Counting({"from_uv": [0.0, 0.0], "to_uv": [1.0, 0.0], "inward_uv": [0.0, 1.0]})
        polygons = [square(chart, 0.5, 0.5, 18.0)]
        Counting.calls = 0
        strain = place._strain_under(chart, mesh, frame, polygons)
        self.assertLess(Counting.calls, 3 * len(chart.facets) // 20)
        self.assertEqual(strain, brute(chart, mesh, frame, polygons))

    def test_the_spacing_tolerance_follows_the_strain_limit(self) -> None:
        # At a strain limit of 2% the sheet may stretch by 2% under the boards, and the spacing with it.
        data, _, selection, result = self.fitted(
            F.sphere_cap(60.0, 25.0, rings=8, segments=32), (0.0, 0.0, 60.0), "smooth", pitch_mm=1.5, strain_limit=0.02, proposals=2
        )
        for proposal in result["proposals"]:
            mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
            self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
            spacing = next(r for r in mapped["verification"] if r["rule"] == "neighbour_spacing_error")
            self.assertEqual(spacing["required"], 0.022)
        # At the default limit the tolerance stays 0.5%.
        data, _, selection, result = self.fitted(F.box((40.0, 30.0, 10.0)), (20.0, 15.0, 10.0), pitch_mm=2.0, rotation="none")
        proposal = result["proposals"][0]
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        self.assertEqual(next(r["required"] for r in mapped["verification"] if r["rule"] == "neighbour_spacing_error"), 0.005)

    def test_the_overlay_follows_the_tails_beyond_an_arc_chord(self) -> None:
        # A round pad with an arc exit: the surface goes on below the arc's chord to the rim.
        data, mesh, selection, result = self.fitted(
            F.plate(F.ellipse_outline(20.0, 20.0)), (0.5, 0.5, 3.0), base={"arc": {"point_xyz": [0.0, -20.0, 3.0]}}, pitch_mm=2.0, rotation="none"
        )
        proposal = result["proposals"][0]
        placement = proposal["placement"]
        self.assertEqual(placement["base_kind"], "arc")
        mapped = place.map_route({"selection": selection, "placement": placement, "design": proposal["design"]}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        _, chart = api.selection_chart(mesh, selection)
        frame = fit.BaseFrame({"from_uv": placement["base_from_uv"], "to_uv": placement["base_to_uv"], "inward_uv": placement["base_inward_uv"]}, placement["base_angle_deg"])
        outlines = fit.board_outlines_base(generate_design(proposal["design"]), placement["field_origin_base"])
        for name in ("row", "column"):
            # The lowest point of the board's outline on the part (sampled every 0.1 mm), against the overlay's.
            polygon = outlines[name]
            lowest = math.inf
            for k in range(len(polygon)):
                a, b = polygon[k - 1], polygon[k]
                steps = max(1, int(math.ceil(math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) / 0.1)))
                for s in range(steps + 1):
                    hit = chart_point_to_3d(chart, mesh, frame.to_chart((a[0] + (b[0] - a[0]) * s / steps, a[1] + (b[1] - a[1]) * s / steps)))
                    if hit is not None:
                        lowest = min(lowest, hit[0][1])
            overlay = [p for run in mapped["overlay"][name] for p in run]
            self.assertLess(min(p[1] for p in overlay) - lowest, place.DENSIFY_MM + 0.1, name)
            self.assertTrue(all(abs(p[2] - 3.0) < 1e-6 and p[0] ** 2 + p[1] ** 2 <= 400.0 + 1e-6 for p in overlay), name)


if __name__ == "__main__":
    unittest.main()
