"""CAD mode: fitting a sensor design to a surface (surface.fit) and mapping it onto the part (surface.place)."""

from __future__ import annotations

import copy
import math
import random
import types
import unittest
from pathlib import Path

from engine import generate_design
from engine.geometry import segment_distance, segments_intersect
from surface import api, bend, fit, place, select
from surface import chart as chart_module
from surface.errors import SurfaceError

try:
    import surface_fixtures as F
except ImportError:  # run as a package
    from tests import surface_fixtures as F

ASSETS = Path(__file__).resolve().parents[1] / "asset"
# The whole stack on the surface (containment board): the fit these tests pinned before masked-field phase P5e made
# field-only containment the default with shape fill.
BOARD = {"containment": "board"}
# The fill these tests' fits were measured at: the default 0.7 until the user's decision of 2026-11-06 made it 0.5
# (tests/defaults_of_before.py); each names it, beside the options it tests.
MEASURED = {"fill": 0.7}


class _Replica:
    """The soft-finger replica, its contact-face selection and the fit through the mount end."""

    _cache: dict = {}

    @classmethod
    def get(cls, options: dict | None = None, base: object = None) -> tuple:
        key = repr((options, base))
        if key not in cls._cache:
            triangles = F.soft_finger_replica()
            data = F.stl_bytes(triangles)
            mesh = F.mesh(triangles)
            seed = select.nearest_facet(mesh, (0.0, -12.9, -62.7))
            selection = {"ops": [{"op": "grow", "seed_facet": seed}]}
            header = {"selection": selection, "base": base or {"point_xyz": [0.0, -12.9, -3.0]}, "options": {**MEASURED, **(options or {})}}
            cls._cache[key] = (data, mesh, selection, fit.fit_route(header, data))
        return cls._cache[key]


def _board_rectangle(options: dict | None = None) -> tuple:
    """The replica's whole-board full rectangle: ``(data, mesh, selection, proposal)``, the first unmasked proposal of the
    whole-board fit (containment board, 20 proposals) with ``options``.  At 2 mm the 44 x 8 these tests pinned with shape
    rectangle (the raster search, :func:`surface.fit.search`), the same build and placement: Whole board merges that
    search's rectangles with its masked fields, and CAD mode has no rectangle shape since P5-diagonal-bus.md section
    26.16."""

    data, mesh, selection, result = _Replica.get(dict(BOARD, proposals=20, **(options or {})))
    return data, mesh, selection, next(p for p in result["proposals"] if "mask" not in p["design"]["matrix"])


class FitTests(unittest.TestCase):
    def test_the_replica_takes_a_44_by_8_array_at_2_mm(self) -> None:
        # With the whole stack on the face (containment board) the surface template (tight margins) fits the full 44 x 8
        # at 2 mm through the mount end, with the field's far side 0.1 um inside the face's tip end (the rectangular mode's
        # generic rules, a CAD option before P5-diagonal-bus.md section 26.16, fit 49 x 7).  With shape fill (the default
        # from masked-field phase P4b on) the rectangle stayed first while masked fields stopped at 32 rows (334 taxels);
        # since they take the rectangles' caps (section 21, coverage first) a masked 50 x 12 (470) following the face's
        # taper ranks before it, and the rectangle follows among the whole board's proposals.
        _, _, _, fill = _Replica.get(BOARD)
        self.assertEqual((fill["request"]["options"]["shape"], fill["request"]["options"]["containment"]), ("fill", "board"))
        masked = fill["proposals"][0]
        self.assertEqual((masked["metrics"]["rows"], masked["metrics"]["columns"], masked["metrics"]["taxels"]), (50, 12, 470))
        self.assertIn("mask", masked["design"]["matrix"])
        data, mesh, selection, best = _board_rectangle()
        result = _Replica.get(dict(BOARD, proposals=20))[3]
        metrics = best["metrics"]
        self.assertEqual((metrics["rows"], metrics["columns"], metrics["pitch_x_mm"]), (44, 8, 2.0))
        self.assertEqual((metrics["taxels"], metrics["positions"], metrics["sampled"], metrics["mask_class"]), (44 * 8, 44 * 8, 1.0, None))
        # Re-pinned by the profile revision 2026-10-29 (the profile's digest in the build id; d0ff86bfafec before).
        # Re-pinned by the profile revision 2026-11-06 (the order: JLC's 2-layer 0.2 mm FPC, the bottom copper empty): the
        # profile's digest in the build id, the fit, its design, boards and layout as before (31192a48fa1b before).
        # Re-pinned by the profile revision 2026-11-06b (the PI stiffener 0.225 -> 0.1 mm, the user's later decision of
        # 2026-11-06): the profile's digest in the build id, the fit and its design as before (5d18c0e96e82 before).
        self.assertEqual(best["build_id"], "surface-44x8-7eaaa3f9a606")
        self.assertEqual(best["design"]["template_id"], "surface_matrix_v1")
        self.assertGreaterEqual(metrics["min_clearance_mm"], 0.0)
        # Proposals are ranked best first and every one is a generated, DRC-clean design.
        for fitted in (result, fill):
            counts = [p["metrics"]["taxels"] for p in fitted["proposals"]]
            self.assertEqual(counts, sorted(counts, reverse=True))
        for proposal in result["proposals"] + fill["proposals"]:
            generated = generate_design(proposal["design"])
            self.assertTrue(generated["ok"], generated["validation"]["errors"][:3])
            self.assertEqual(generated["manifest"]["build_id"], proposal["build_id"])
            self.assertEqual(generated["design"]["tail"]["row_side"], "bottom")
            for name in ("top_length_mm", "bottom_length_mm"):
                self.assertTrue(7.0 <= generated["design"]["tail"][name] <= 80.0)

    def test_the_default_keeps_only_the_taxel_field_on_the_face(self) -> None:
        # From masked-field phase P5e on, shape fill fits with containment field: only the taxel field lies on the
        # face (the Row traces' bands, the fan-out and the tails may leave it), on the diagonal Row bus: 59 x 12.
        data, mesh, selection, result = _Replica.get()
        self.assertEqual((result["request"]["options"]["containment"], result["request"]["options"]["row_sides"]), ("field", "both"))
        best = result["proposals"][0]
        metrics = best["metrics"]
        self.assertEqual((metrics["rows"], metrics["columns"], metrics["taxels"], metrics["containment"]), (59, 12, 708, "field"))
        self.assertEqual(best["design"]["routing"]["row_sides"], "both")
        self.assertEqual(best["placement"]["options"]["containment"], "field")
        self.assertGreaterEqual(metrics["min_clearance_mm"], 0.0)
        # More than the whole stack on the face takes: 708 against the masked 470 (twice the 44 x 8 rectangle's 352).
        self.assertGreater(metrics["taxels"], _Replica.get(BOARD)[3]["proposals"][0]["metrics"]["taxels"])
        self.assertGreater(metrics["taxels"], 2 * _board_rectangle()[3]["metrics"]["taxels"])
        for proposal in result["proposals"]:
            self.assertEqual(generate_design(proposal["design"])["manifest"]["build_id"], proposal["build_id"])

    def test_the_placement_document_carries_everything_the_map_needs(self) -> None:
        _, mesh, selection, result = _Replica.get()
        placement = result["proposals"][0]["placement"]
        self.assertEqual(placement["format"], place.PLACEMENT_FORMAT)
        self.assertEqual(placement["mesh"]["sha256"], mesh.sha256)
        self.assertEqual(placement["selection"], selection)
        self.assertEqual(placement["build_id"], result["proposals"][0]["build_id"])
        self.assertIn("base_angle_deg", placement)

    def test_no_fit_reports_its_reasons(self) -> None:
        # A 2.2 mm face: too small for one taxel with its margins (1.4 + 2 x 0.5 mm; the corner tolerance never widens a
        # side, P5-diagonal-bus.md section 16).  A 2.5 mm face takes a 1 x 1 field at the centred phase, 0.05 mm clear.
        triangles = F.box((2.2, 2.2, 2.2))
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (1.1, 1.1, 2.2))
        with self.assertRaises(SurfaceError) as raised:
            fit.fit_route({"selection": {"ops": [{"op": "grow", "seed_facet": seed}]}, "options": {"pitch_mm": 2.0, **MEASURED}}, data)
        self.assertEqual(raised.exception.code, "E_SURFACE_NO_FIT")
        self.assertTrue(raised.exception.details["rejected"])

    def test_options_are_strict(self) -> None:
        for options in (
            {"pitch_mm": 0.1}, {"objective": "best"}, {"max_rows": 65}, {"unknown": 1}, {"fill": True}, {"rotation": "spin"},
            {"template": "custom"}, {"template": "generic"}, {"shape": "rectangle"}, {"rectangle_preference_pct": 5},
        ):
            with self.subTest(options=options):
                with self.assertRaises(SurfaceError) as raised:
                    fit.parse_options(options)
                self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST")

    def test_the_options_table_of_cad_mode_md_matches_the_code(self) -> None:
        text = (Path(__file__).resolve().parents[1] / "docs" / "CAD_MODE.md").read_text(encoding="utf-8")
        section = text.split("## Options of the fit", 1)[1].split("\n## ", 1)[0]
        rows = [line.split("|")[1:4] for line in section.splitlines() if line.startswith("| `")]
        documented = {}
        for names, default, _ in rows:
            keys = [name.strip(" `") for name in names.split(",")]
            values = [value.strip(" `") for value in default.split(",")]
            for key, value in zip(keys, values if len(values) == len(keys) else values * len(keys)):
                documented[key] = value
        self.assertEqual(set(documented), set(fit.DEFAULT_OPTIONS))
        for key, value in fit.DEFAULT_OPTIONS.items():
            if isinstance(value, bool):
                self.assertEqual(documented[key], "true" if value else "false", key)
            elif isinstance(value, (int, float)):
                self.assertEqual(float(documented[key]), value, key)
            else:
                self.assertEqual(documented[key], value, key)

    def test_the_fit_is_deterministic(self) -> None:
        triangles = F.soft_finger_replica()
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (0.0, -12.9, -62.7))
        header = {"selection": {"ops": [{"op": "grow", "seed_facet": seed}]}, "base": {"side": 0}, "options": {"pitch_mm": 3.0, "rotation": "none"}}
        first = fit.fit_route(header, data)
        second = fit.fit_route(copy.deepcopy(header), data)
        self.assertEqual([p["build_id"] for p in first["proposals"]], [p["build_id"] for p in second["proposals"]])
        self.assertEqual(first["proposals"][0]["placement"], second["proposals"][0]["placement"])

    def test_flexitac_wiring_swaps_the_sets_when_one_has_more_than_16_lines(self) -> None:
        self.assertEqual(fit.connector_for(16, 32, "flexitac"), {"row_pins": 16, "column_pins": 32})
        self.assertEqual(fit.connector_for(30, 12, "flexitac"), {"row_pins": 32, "column_pins": 16})
        self.assertEqual(fit.connector_for(10, 10, "channels"), {"row_pins": None, "column_pins": None})

    def test_a_cylinder_strip_unrolls_and_takes_a_large_array(self) -> None:
        triangles = F.cylinder_band(15.0, 40.0, segments=30, closed=False, sweep_deg=150.0)
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (15.0, 0.5, 20.0))
        result = fit.fit_route({"selection": {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]}, "options": {"pitch_mm": 1.5, "rotation": "none"}}, data)
        self.assertEqual(result["selection"]["kind"], "developable")
        self.assertGreater(result["proposals"][0]["metrics"]["taxels"], 200)

    def test_max_taxels_grows_the_pitch_and_lists_each_shape_once(self) -> None:
        data, mesh, selection, result = _Replica.get({"objective": "max_taxels", "min_pitch_mm": 1.5, "rotation": "none"})
        shapes = [(p["metrics"]["rows"], p["metrics"]["columns"]) for p in result["proposals"]]
        self.assertEqual(len(shapes), len(set(shapes)), shapes)
        self.assertTrue(all(p["metrics"]["pitch_x_mm"] >= 1.5 for p in result["proposals"]))
        self.assertGreater(max(p["metrics"]["pitch_x_mm"] for p in result["proposals"]), 1.5)

    def test_the_clearance_of_an_edge_crossing_the_exit_counts_up_to_the_crossing(self) -> None:
        # The exit is the bottom side; the right side leans out.  The board's right edge
        # crosses the exit 0.1 mm from the corner, while its upper end is 1.6 mm clear.
        exits = fit.ExitOutline([(0.0, 0.0), (10.0, 0.0), (12.0, 10.0), (0.0, 10.0)], [0])
        frame = fit.BaseFrame({"from_uv": [0.0, 0.0], "to_uv": [10.0, 0.0], "inward_uv": [0.0, 1.0]})
        board = [(2.0, -5.0), (9.9, -5.0), (9.9, 8.0), (2.0, 8.0)]
        outlines = {"row": board, "column": board}
        none = {"holes": [], "strained": [], "covered": [], "bends": []}
        clearance = fit.check_containment(outlines, exits, frame, None, none, 0.0)
        self.assertAlmostEqual(clearance, 0.1, places=9)
        self.assertIsNone(fit.check_containment(outlines, exits, frame, None, none, 1.0))

    def test_bends_tighter_than_the_stack_allows_are_never_covered(self) -> None:
        # A 2 mm radius cylinder, finely faceted (1.1 degrees per edge): the field needs 4.7 mm.
        triangles = F.cylinder_band(2.0, 40.0, segments=160, closed=False, sweep_deg=180.0)
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (2.0, 0.01, 20.0))
        header = {"selection": {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]}, "options": {"pitch_mm": 1.0}}
        with self.assertRaises(SurfaceError) as raised:
            fit.fit_route(header, data)
        self.assertEqual(raised.exception.code, "E_SURFACE_NO_FIT")
        # A 25 degree ridge across a roof: no board straddles it.
        rise = 30.0 * math.tan(math.radians(12.5))
        triangles = F.extrude([(0.0, 0.0), (60.0, 0.0), (60.0, 10.0), (30.0, 10.0 + rise), (0.0, 10.0)], 30.0)
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (15.0, -15.0, 10.0 + rise / 2))
        selection = {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]}
        result = fit.fit_route({"selection": selection, "options": {"pitch_mm": 2.0, "proposals": 3}}, data)
        self.assertEqual(result["obstacles"]["bends"], 1)
        for proposal in result["proposals"]:
            mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
            self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
            radius = next(r for r in mapped["verification"] if r["rule"] == "field_bend_radius")
            self.assertIsNone(radius["measured"])

    def test_a_round_pad_without_straight_sides_exits_through_an_arc(self) -> None:
        triangles = F.plate(F.ellipse_outline(20.0, 20.0))
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (0.5, 0.5, 3.0))
        selection = {"ops": [{"op": "grow", "seed_facet": seed}]}
        for base in ("auto", {"point_xyz": [0.0, -20.0, 3.0]}, {"arc": {"point_xyz": [0.0, -20.0, 3.0], "half_length_mm": 15}}):
            with self.subTest(base=base):
                result = fit.fit_route({"selection": selection, "base": base, "options": {"pitch_mm": 2.0, "rotation": "none"}}, data)
                best = result["proposals"][0]
                self.assertEqual(best["placement"]["base_kind"], "arc")
                self.assertGreaterEqual(best["metrics"]["taxels"], 140)
                mapped = place.map_route({"selection": selection, "placement": best["placement"], "design": best["design"]}, data)
                self.assertTrue(mapped["ok"])

    def test_straight_sides_next_to_finely_faceted_corners_can_be_picked(self) -> None:
        # 60 x 30 mm with R10 corners at 0.9 degrees per segment: the 40 and 10 mm straight
        # sides stay sides of their own, and a corner's short pieces are no tail exit.
        outline = []
        for cx, cy, start in ((20.0, 5.0, 0.0), (-20.0, 5.0, 90.0), (-20.0, -5.0, 180.0), (20.0, -5.0, 270.0)):
            for k in range(101):
                angle = math.radians(start + 0.9 * k)
                outline.append((cx + 10.0 * math.cos(angle), cy + 10.0 * math.sin(angle)))
        triangles = F.plate(outline)
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (0.5, 0.5, 3.0))
        selection = {"ops": [{"op": "grow", "seed_facet": seed}]}
        from surface import api

        _, chart = api.selection_chart(mesh, selection)
        sides = api.boundary_sides(mesh, chart)
        # (A straight side takes the corner segments within 1 degree of it: at most 0.4 mm.)
        chords = sorted(s["chord_mm"] for s in sides if s["chord_mm"] >= 3.0)
        self.assertEqual(len(chords), 4)
        for chord, expected in zip(chords, (10.0, 10.0, 40.0, 40.0)):
            self.assertAlmostEqual(chord, expected, delta=0.4)
        long_side = next(s for s in sides if abs(s["chord_mm"] - 40.0) < 0.4 and s["from_xyz"][1] < 0)
        result = fit.fit_route({"selection": selection, "base": {"side": long_side["index"]}, "options": {"pitch_mm": 2.0, "rotation": "none"}}, data)
        self.assertGreater(result["proposals"][0]["metrics"]["taxels"], 100)
        short = next(s for s in sides if s["chord_mm"] < 3.0)
        with self.assertRaises(SurfaceError) as raised:
            fit.fit_route({"selection": selection, "base": {"side": short["index"]}}, data)
        self.assertEqual(raised.exception.code, "E_SURFACE_BASE_EDGE")

    def test_a_dome_is_cut_down_to_the_disk_that_flattens_within_the_strain_limit(self) -> None:
        triangles = F.sphere_cap(60.0, 25.0, rings=8, segments=32)
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (0.0, 0.0, 60.0))
        result = fit.fit_route({"selection": {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]}, "options": {"pitch_mm": 1.5, "rotation": "none"}}, data)
        limited = result["selection"]["strain_limited"]
        self.assertLessEqual(limited["strain_max"], 0.003)
        self.assertLess(limited["area_mm2"], limited["selected_area_mm2"])
        proposal = result["proposals"][0]
        self.assertGreater(proposal["metrics"]["taxels"], 0)
        # The map rebuilds the same strain-limited chart from the placement.
        self.assertEqual(proposal["placement"]["strain_limited"], limited)
        selection = {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]}
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])


class MapTests(unittest.TestCase):
    def test_every_taxel_lands_on_the_face_at_the_pitch(self) -> None:
        data, mesh, selection, result = _Replica.get()
        proposal = result["proposals"][0]
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        rows, columns = proposal["metrics"]["rows"], proposal["metrics"]["columns"]
        self.assertEqual(mapped["taxel_count"], rows * columns)
        for taxel in mapped["taxels"]:
            self.assertAlmostEqual(taxel["xyz_mm"][0], 0.0, places=6)  # on the x = 0 face
            self.assertTrue(-25.8 <= taxel["xyz_mm"][1] <= 0.0)
            self.assertTrue(-122.365 <= taxel["xyz_mm"][2] <= -3.0)
            self.assertEqual(taxel["normal"], [-1.0, 0.0, 0.0])
        self.assertTrue(mapped["wrap_svg"].startswith("<svg"))
        self.assertTrue(all(len(run) > 1 for runs in mapped["overlay"].values() for run in runs))

    def test_row_01_is_farthest_from_the_tails_and_col_01_follows_the_role_mapping(self) -> None:
        # Seen from outside (looking at the -x face along +x), u runs along +y... the chart axes
        # follow the mesh; check the convention in the base frame: ROW_01 farthest from the base
        # edge; COL_01 on the left (rows on top) or on the right (columns on top).  The maps, at 3 mm: a
        # rectangle's (every crossing; the whole board's first full rectangle), the masked field with the whole
        # board on the face (its crossings from the stacked electrodes), and the default fit's diagonal Row bus
        # (field-only containment): taxels of one row and of one column compared.
        for role in ("rows_top", "columns_top"):
            for shape, containment in (("rectangle", "board"), ("fill", "board"), ("fill", "field")):
                with self.subTest(role=role, shape=shape, containment=containment):
                    options = {"role_mapping": role, "pitch_mm": 3.0, "rotation": "none", "containment": containment}
                    if shape == "rectangle":
                        data, mesh, selection, proposal = _board_rectangle(options)
                    else:
                        data, mesh, selection, result = _Replica.get(options)
                        proposal = result["proposals"][0]
                    self.assertEqual("mask" in proposal["design"]["matrix"], (shape, containment) == ("fill", "board"))
                    self.assertEqual("row_sides" in proposal["design"]["routing"], containment == "field")
                    mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
                    taxels = {(t["row"], t["column"]): t for t in mapped["taxels"]}
                    rows = proposal["metrics"]["rows"]
                    top = sorted(column for row, column in taxels if row == 1)
                    column = top[0]
                    lowest = max(row for row, c in taxels if c == column)
                    frame = fit.BaseFrame(
                        {"from_uv": proposal["placement"]["base_from_uv"], "to_uv": proposal["placement"]["base_to_uv"], "inward_uv": proposal["placement"]["base_inward_uv"]},
                        proposal["placement"]["base_angle_deg"],
                    )
                    first = frame.to_base(taxels[(1, top[0])]["uv_mm"])
                    last_row = frame.to_base(taxels[(lowest, column)]["uv_mm"])
                    last_column = frame.to_base(taxels[(1, top[-1])]["uv_mm"])
                    self.assertGreater(len(top), 1)
                    self.assertGreater(lowest, rows // 2)
                    self.assertGreater(first[1], last_row[1])  # ROW_01 is farthest from the tails
                    if role == "rows_top":
                        self.assertLess(first[0], last_column[0])  # the lower COL index on the left seen from outside
                    else:
                        self.assertGreater(first[0], last_column[0])  # on the right

    def test_a_design_edited_after_the_fit_is_rejected(self) -> None:
        data, mesh, selection, result = _Replica.get()
        proposal = result["proposals"][0]
        edited = copy.deepcopy(proposal["design"])
        edited["matrix"]["rows"] -= 1
        with self.assertRaises(SurfaceError) as raised:
            place.map_route({"selection": selection, "placement": proposal["placement"], "design": edited}, data)
        self.assertEqual(raised.exception.code, "E_SURFACE_PLACEMENT_MISMATCH")
        # Tail lengths may change (they do not move the field).
        longer = copy.deepcopy(proposal["design"])
        longer["tail"]["top_length_mm"] = min(80.0, longer["tail"]["top_length_mm"] + 5)
        self.assertTrue(place.map_route({"selection": selection, "placement": proposal["placement"], "design": longer}, data)["taxel_count"] > 0)

    def test_a_masked_design_maps_only_with_the_placement_fitted_for_its_mask(self) -> None:
        # From masked-field phase P4 the map lists the active crossings of a masked design (here one the classes
        # build: ROW_01 drops COL_01); the mask is part of matrix, so a placement fitted without it is a mismatch.
        data, mesh, selection, proposal = _board_rectangle()
        masked = copy.deepcopy(proposal["design"])
        self.assertEqual(masked["template_id"], "surface_matrix_v1")
        rows, columns = masked["matrix"]["rows"], masked["matrix"]["columns"]
        masked["matrix"]["mask"] = [[2, columns], *([[1, columns]] * (rows - 1))]
        self.assertTrue(generate_design(masked)["ok"])
        with self.assertRaises(SurfaceError) as raised:
            place.map_route({"selection": selection, "placement": proposal["placement"], "design": masked}, data)
        self.assertEqual((raised.exception.code, raised.exception.details["fields"]), ("E_SURFACE_PLACEMENT_MISMATCH", ["matrix"]))
        placement = dict(proposal["placement"], design=masked)
        mapped = place.map_route({"selection": selection, "placement": placement, "design": masked}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        self.assertEqual(mapped["taxel_count"], rows * columns - 1)
        self.assertNotIn((1, 1), {(t["row"], t["column"]) for t in mapped["taxels"]})
        self.assertEqual(mapped["readout"], {"rows": rows, "columns": columns, "positions": rows * columns, "active": rows * columns - 1,
                                             "row_spans": masked["matrix"]["mask"], "inactive": "always 0"})
        record = next(r for r in mapped["verification"] if r["rule"] == "taxel_mask_matches_design")
        self.assertEqual((record["measured"], record["passed"]), (0, True))
        # A full mask is the unmasked design: it maps with the unmasked placement, without a readout.
        full = copy.deepcopy(proposal["design"])
        full["matrix"]["mask"] = [[1, columns]] * rows
        unmasked = place.map_route({"selection": selection, "placement": proposal["placement"], "design": full}, data)
        self.assertTrue(unmasked["ok"])
        self.assertNotIn("readout", unmasked)
        self.assertNotIn("taxel_mask_matches_design", [r["rule"] for r in unmasked["verification"]])

    def test_flexitac_taxels_carry_their_reader_lines(self) -> None:
        data, mesh, selection, result = _Replica.get({"connector": "flexitac", "pitch_mm": 3.0, "rotation": "none"})
        proposal = result["proposals"][0]
        mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
        indices = sorted(t["reader"]["frame_index"] for t in mapped["taxels"])
        self.assertEqual(len(indices), len(set(indices)))
        self.assertTrue(all(0 <= i < 512 for i in indices))
        # The reader scans connector pins: a descending channel order moves taxel (1, 1)
        # to the last pins, and its reader lines and frame index follow.
        sense_pins = 16 if proposal["design"]["connector"]["row_pins"] == 16 else 32
        for order in ("ascending", "descending"):
            design = copy.deepcopy(proposal["design"])
            design["channel_order"] = {"rows": order, "columns": order}
            mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": design}, data)
            first = next(t for t in mapped["taxels"] if (t["row"], t["column"]) == (1, 1))
            sense_pin, drive_pin = (first["row_pin"], first["column_pin"]) if sense_pins == 16 else (first["column_pin"], first["row_pin"])
            self.assertEqual((first["reader"]["sense_line"], first["reader"]["drive_line"]), (f"SR{sense_pin}", f"SC{drive_pin}"))
            self.assertEqual(first["reader"]["frame_index"], (drive_pin - 1) * 16 + sense_pin - 1)
            if order == "ascending":
                self.assertEqual((sense_pin, drive_pin), (1, 1))
            else:
                self.assertNotEqual((sense_pin, drive_pin), (1, 1))

    def test_the_map_checks_what_the_fit_promised(self) -> None:
        data, mesh, selection, proposal = _board_rectangle()

        def failed(placement, design) -> list:
            mapped = place.map_route({"selection": selection, "placement": placement, "design": design}, data)
            return [r["rule"] for r in mapped["verification"] if not r["passed"]]

        self.assertEqual(failed(proposal["placement"], proposal["design"]), [])
        import json

        # Every record is JSON (a missing measurement is null, never an infinity).
        short_tails = copy.deepcopy(proposal["design"])
        short_tails["tail"]["top_length_mm"] = short_tails["tail"]["bottom_length_mm"] = 7.5
        json.dumps(place.map_route({"selection": selection, "placement": proposal["placement"], "design": short_tails}, data), allow_nan=False)
        # Boards moved off the face (the field sits at its far end, the stack fills its width);
        # moved toward the exit they stay on it, with longer tails beyond it, until
        # more than the tails crosses it (R1.1).
        for dx, dy, leaves in ((0.0, 0.6, True), (0.6, 0.0, True), (-0.6, 0.0, True), (0.0, -1.0, False), (0.0, -30.4, True), (0.0, -31.9, True)):
            moved = copy.deepcopy(proposal["placement"])
            moved["field_origin_base"] = [moved["field_origin_base"][0] + dx, moved["field_origin_base"][1] + dy]
            self.assertEqual("board_clearance" in failed(moved, proposal["design"]), leaves, (dx, dy))
        # Tails cut to the template's minimum end on the face, short of the exit.
        short = copy.deepcopy(proposal["design"])
        short["tail"]["top_length_mm"] = short["tail"]["bottom_length_mm"] = 7.5
        self.assertTrue({"row_tail_reach", "column_tail_reach"} <= set(failed(proposal["placement"], short)))
        # The generic template has other margins: the placement does not hold for it.
        generic = copy.deepcopy(proposal["design"])
        generic["template_id"] = "generic_matrix_v1"
        with self.assertRaises(SurfaceError) as raised:
            place.map_route({"selection": selection, "placement": proposal["placement"], "design": generic}, data)
        # Its routing differs as well: the generic template always names its Row traces (routing.row_sides, P5-diagonal-bus.md
        # section 18), the surface design's straight channel leaves them out.
        self.assertEqual((raised.exception.code, raised.exception.details["fields"]), ("E_SURFACE_PLACEMENT_MISMATCH", ["template_id", "routing"]))

    def test_a_placement_maps_only_onto_its_own_mesh_and_selection(self) -> None:
        data, mesh, selection, result = _Replica.get()
        proposal = result["proposals"][0]
        moved = F.stl_bytes([tuple((p[0], p[1], p[2] + 1.0) for p in t) for t in F.soft_finger_replica()])
        flat = {"ops": [dict(selection["ops"][0], preset="flat")]}
        for header, body in (
            ({"selection": selection}, moved),
            ({"selection": selection, "unit": "cm"}, data),
            ({"selection": flat}, data),
        ):
            with self.assertRaises(SurfaceError) as raised:
                place.map_route(dict(header, placement=proposal["placement"], design=proposal["design"]), body)
            self.assertEqual(raised.exception.code, "E_SURFACE_PLACEMENT_MISMATCH", header)
        # Without a selection the placement's own is used.
        self.assertTrue(place.map_route({"placement": proposal["placement"], "design": proposal["design"]}, data)["ok"])

    def test_a_damaged_placement_is_a_request_error(self) -> None:
        data, mesh, selection, result = _Replica.get()
        proposal = result["proposals"][0]
        damages = [
            lambda p: p.pop("base_from_uv"),
            lambda p: p.update(field_origin_base=[1.0]),
            lambda p: p.update(base_inward_uv=[0.0, 0.0]),
            lambda p: p.update(base_angle_deg=float("nan")),
            lambda p: p.update(exit_edges=[]),
            lambda p: p.update(exit_edges=[True]),
            lambda p: p.update(strain_limited={"centre_facet": -1, "radius_mm": 5.0}),
            lambda p: p.pop("mesh"),
            lambda p: p.update(options=[]),
            lambda p: p.update(field_origin_base=[10 ** 400, 0.0]),
        ]
        for k, damage in enumerate(damages):
            placement = copy.deepcopy(proposal["placement"])
            damage(placement)
            with self.assertRaises(SurfaceError, msg=k) as raised:
                place.map_route({"selection": selection, "placement": placement, "design": proposal["design"]}, data)
            self.assertEqual(raised.exception.code, "E_SURFACE_REQUEST", k)

    def test_spacing_is_measured_along_curved_surfaces(self) -> None:
        # Pitch 2 on a radius of 5 mm: the 3D chord is 0.67% shorter than the pitch,
        # the path along the surface is not.
        triangles = F.cylinder_band(5.0, 40.0, segments=72, closed=False, sweep_deg=180.0)
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        seed = select.nearest_facet(mesh, (5.0, 0.05, 20.0))
        selection = {"ops": [{"op": "grow", "seed_facet": seed, "preset": "smooth"}]}
        result = fit.fit_route({"selection": selection, "options": {"pitch_mm": 2.0, "proposals": 2}}, data)
        for proposal in result["proposals"]:
            mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
            self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
            spacing = next(r for r in mapped["verification"] if r["rule"] == "neighbour_spacing_error")
            self.assertLess(spacing["measured"], 1e-3)


class ReviewFixTests(unittest.TestCase):
    """Regression tests of the fit and bend fixes of review F (findings R1-R5)."""

    NONE = {"holes": [], "strained": [], "covered": [], "bends": []}

    @staticmethod
    def _saddle(cells: int = 16) -> tuple:
        # z = (x^2 - y^2) / 160 over 40 x 40 mm: curved, beyond the default strain limit.
        def point(i, j):
            x, y = -20.0 + 40.0 * i / cells, -20.0 + 40.0 * j / cells
            return (x, y, (x * x - y * y) / 160.0)

        triangles = []
        for i in range(cells):
            for j in range(cells):
                a, b, c, d = point(i, j), point(i + 1, j), point(i + 1, j + 1), point(i, j + 1)
                triangles += [(a, b, c), (a, c, d)]
        return F.stl_bytes(triangles), F.mesh(triangles)

    def test_the_segment_index_keeps_long_segments_met_first(self) -> None:
        # R3.0: a long segment listed before short ones was registered in no cell.
        rng = random.Random(7)
        for trial in range(60):
            segments = []
            for _ in range(rng.randint(2, 40)):
                length = rng.choice([0.05, 0.3, 2.0, 60.0, 400.0]) * rng.random()
                x, y, angle = rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(0, 2 * math.pi)
                segments.append(((x, y), (x + length * math.cos(angle), y + length * math.sin(angle))))
            segments.sort(key=lambda s: -fit.dist2(*s))  # the long ones first
            index = fit._SegmentIndex(segments)
            for _ in range(20):
                q = (rng.uniform(-150, 150), rng.uniform(-150, 150))
                exact = min(segment_distance(q, q, c, d) for c, d in segments)
                self.assertAlmostEqual(index.point_distance(q), exact, places=9, msg=trial)
                a = (rng.uniform(-60, 60), rng.uniform(-60, 60))
                b = (a[0] + rng.uniform(-8, 8), a[1] + rng.uniform(-8, 8))
                near = index.near(a, b, 0.0)
                for segment in segments:
                    if segments_intersect(a, b, *segment):
                        self.assertIn(segment, near, trial)
        # In check_containment: the right wall (30 mm, listed first) next to a top split in 120 pieces.
        outline = [(0.0, 0.0), (40.0, 0.0), (40.0, 30.0)] + [(40.0 - k / 3, 30.0) for k in range(1, 120)] + [(0.0, 30.0)]
        exits = fit.ExitOutline(outline, [0])
        frame = fit.BaseFrame({"from_uv": [0.0, 0.0], "to_uv": [40.0, 0.0], "inward_uv": [0.0, 1.0]})
        board = [(5.0, -5.0), (39.0, -5.0), (39.0, 20.0), (5.0, 20.0)]
        outlines = {"row": board, "column": board}
        self.assertAlmostEqual(fit.check_containment(outlines, exits, frame, None, self.NONE, 0.0), 1.0, places=9)
        self.assertIsNone(fit.check_containment(outlines, exits, frame, None, self.NONE, 2.0))

    def test_arc_exit_tails_reach_their_extension_across_their_whole_width(self) -> None:
        # R1.0/R3.2: the tails were sized at their two corners; an arc sags below that chord.
        triangles = F.plate(F.ellipse_outline(20.0, 20.0))
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (0.5, 0.5, 3.0))}]}
        options = {"tail_extension_mm": 6.5, "proposals": 3, "rotation": "none"}
        result = fit.fit_route({"selection": selection, "base": "auto", "options": options}, data)
        for proposal in result["proposals"]:
            self.assertEqual(proposal["placement"]["base_kind"], "arc")
            mapped = place.map_route({"selection": selection, "placement": proposal["placement"], "design": proposal["design"]}, data)
            self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
            for rule in ("row_tail_reach", "column_tail_reach"):
                reach = next(r for r in mapped["verification"] if r["rule"] == rule)
                self.assertGreaterEqual(reach["measured"], 6.5)

    def test_the_overlay_follows_the_tails_below_an_arc_chord(self) -> None:
        # R1.5: below an arc exit's chord the surface goes on to the arc, and the tails lie on it there: the overlay
        # maps a polyline there (and splits it only off the surface, beyond the arc).
        triangles = F.plate(F.ellipse_outline(20.0, 20.0))
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (0.5, 0.5, 3.0))}]}
        for containment in ("board", "field"):
            with self.subTest(containment=containment):
                options = {"pitch_mm": 2.0, "rotation": "none", "proposals": 1, "containment": containment}
                placement = fit.fit_route({"selection": selection, "base": "auto", "options": options}, data)["proposals"][0]["placement"]
                self.assertEqual(placement["base_kind"], "arc")
                _, chart = api.selection_chart(mesh, selection)
                frame = fit.BaseFrame({"from_uv": placement["base_from_uv"], "to_uv": placement["base_to_uv"], "inward_uv": placement["base_inward_uv"]},
                                      placement["base_angle_deg"])
                chord = math.dist(placement["base_from_uv"], placement["base_to_uv"])
                # 2 mm below the chord's middle (the 30 mm arc of a 20 mm disk sags 5.4 mm), then 2 mm beyond the disk.
                below = [(chord / 2 - 1.0, -2.0), (chord / 2 + 1.0, -2.0)]
                self.assertLess(frame.height_above_base(below[0]), 0.0)
                runs = place.map_polyline(mesh, chart, frame, below, closed=False)
                self.assertEqual(len(runs), 1)
                self.assertGreater(len(runs[0]), 1)
                self.assertTrue(all(abs(point[2] - 3.0) < 1e-6 for point in runs[0]))
                self.assertEqual(place.map_polyline(mesh, chart, frame, [(chord / 2 - 1.0, -12.0), (chord / 2 + 1.0, -12.0)], closed=False), [])

    def test_only_the_tails_may_cross_the_exit(self) -> None:
        # R1.1: a board whose body hangs beyond the exit passed the containment check (containment board).
        data, mesh, selection, proposal = _board_rectangle()
        placement = proposal["placement"]
        generated = generate_design(proposal["design"])
        _, chart = api.selection_chart(mesh, selection)
        frame = fit.BaseFrame({"from_uv": placement["base_from_uv"], "to_uv": placement["base_to_uv"], "inward_uv": placement["base_inward_uv"]})
        exits = fit.ExitOutline([frame.to_base(p) for p in chart.outline()], placement["exit_edges"])
        obstacles = fit.surface_obstacles(mesh, chart, fit.parse_options(placement["options"]))
        extent = fit.stack_extent(generated["design"], fit.load_profile_cached("surface"))
        x, y = placement["field_origin_base"]
        roots = fit.tail_roots_base(generated, (x, y))
        self.assertAlmostEqual(roots["row"], y - extent["row_root"], places=9)
        self.assertAlmostEqual(roots["column"], y - extent["column_root"], places=9)
        for dy, on_surface in ((0.0, True), (-10.0, True), (-30.4, False), (-31.9, False)):
            origin = (x, y + dy)
            outlines = fit.board_outlines_base(generated, origin)
            checked = fit.check_containment(outlines, exits, frame, chart, obstacles, 0.0, tail_roots=fit.tail_roots_base(generated, origin))
            self.assertEqual(checked is not None, on_surface, dy)
            # Without the tail roots any part of a board may cross the exit (the old call).
            self.assertIsNotNone(fit.check_containment(outlines, exits, frame, chart, obstacles, 0.0))
        # A notch of the exit reaching up under the body (all board corners on the surface).
        outline = [(0.0, 0.0), (4.0, 0.0), (5.0, 3.0), (6.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)]
        exits = fit.ExitOutline(outline, [0, 1, 2, 3])
        frame = fit.BaseFrame({"from_uv": [0.0, 0.0], "to_uv": [20.0, 0.0], "inward_uv": [0.0, 1.0]})
        board = [(2.0, 1.0), (8.0, 1.0), (8.0, -10.0), (12.0, -10.0), (12.0, 1.0), (18.0, 1.0), (18.0, 15.0), (2.0, 15.0)]
        outlines = {"row": board, "column": board}
        self.assertIsNotNone(fit.check_containment(outlines, exits, frame, None, self.NONE, 0.0))
        self.assertIsNone(fit.check_containment(outlines, exits, frame, None, self.NONE, 0.0, tail_roots={"row": 1.0, "column": 1.0}))
        self.assertIsNone(fit.check_containment(outlines, exits, frame, None, self.NONE, 0.0, tail_roots={"row": 0.5, "column": 1.0}))
        straight = fit.ExitOutline([(0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)], [0])
        self.assertIsNotNone(fit.check_containment(outlines, straight, frame, None, self.NONE, 0.0, tail_roots={"row": 1.0, "column": 1.0}))

    def test_max_area_finds_a_larger_field_than_the_fixed_pitch_fits(self) -> None:
        # R3.1: max_area grew the pitch of the min-pitch staircase only.
        triangles = F.plate([(0.0, 0.0), (40.0, 0.0), (40.0, 30.0), (0.0, 30.0)])
        data = F.stl_bytes(triangles)
        mesh = F.mesh(triangles)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (20.0, 15.0, 3.0))}]}

        def largest(options: dict) -> float:
            result = fit.fit_route({"selection": selection, "base": {"point_xyz": [20.0, 0.0, 3.0]}, "options": dict(options, rotation="none")}, data)
            return max(p["metrics"]["field_mm"][0] * p["metrics"]["field_mm"][1] for p in result["proposals"])

        # Both containments: the board fit's pitch staircase and the field-only fit's ladder (the default).
        for containment in ("board", "field"):
            with self.subTest(containment=containment):
                best = largest({"objective": "max_area", "containment": containment})
                for pitch in (2.0, 3.0, 4.0):
                    self.assertGreaterEqual(best, largest({"pitch_mm": pitch, "containment": containment}), pitch)

    def test_a_t_junction_does_not_halve_the_bend_radius(self) -> None:
        # R3.3: a strip triangle split at a T-junction measured half the strip's width.
        triangles = F.with_t_junction(F.cylinder_sheet(8.0, 40.0, 15, 4, 180.0), 20)
        mesh = F.mesh(triangles)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (0.0, 8.0, 20.0)), "preset": "smooth"}]}
        _, chart = api.selection_chart(mesh, selection)
        self.assertEqual(len(chart.facets), mesh.facet_count)
        radii = [bend.edge_radius(mesh, f, g, 4.7) for f in chart.facets for g in mesh.neighbors[f] if g > f]
        self.assertAlmostEqual(min(radii), 8.0, delta=0.05)
        self.assertEqual(fit.bend_segments(mesh, chart, 4.7), [])
        self.assertTrue(all(bend.facet_radius(mesh, f, 4.0) > 7.9 for f in chart.facets))

    def test_bend_lines_are_indexed_in_the_containment_check(self) -> None:
        # R3.6: every board edge was tested against every bend segment of the surface.
        bends = [((100.0 + k * 0.01, 0.0), (100.0 + k * 0.01, 30.0), 1.0) for k in range(2000)]
        obstacles = dict(self.NONE, bends=bends)
        exits = fit.ExitOutline([(0.0, 0.0), (200.0, 0.0), (200.0, 40.0), (0.0, 40.0)], [0])
        frame = fit.BaseFrame({"from_uv": [0.0, 0.0], "to_uv": [200.0, 0.0], "inward_uv": [0.0, 1.0]})
        board = [(5.0, -5.0), (30.0, -5.0), (30.0, 20.0), (5.0, 20.0)]
        calls = [0]
        original = fit.segments_intersect

        def counting(*args):
            calls[0] += 1
            return original(*args)

        fit.segments_intersect = counting
        try:
            clearance = fit.check_containment({"row": board, "column": board}, exits, frame, None, obstacles, 0.0)
        finally:
            fit.segments_intersect = original
        self.assertAlmostEqual(clearance, 5.0, places=9)
        self.assertLess(calls[0], 200)

    def test_the_raster_lists_each_outline_segment_on_its_own_lines_only(self) -> None:
        # R5.1: the raster scanned every outline segment on every line (fan exports: 16000 segments).
        unpacked = [0]

        class Point(tuple):
            def __iter__(self):
                unpacked[0] += 1
                return tuple.__iter__(self)

        class Frame(fit.BaseFrame):
            def to_base(self, p):
                return Point(super().to_base(p))

        outline = F.ellipse_outline(30.0, 20.0, 2000)
        chart = types.SimpleNamespace(outline=lambda: outline)
        frame = Frame({"from_uv": [-30.0, -20.0], "to_uv": [30.0, -20.0], "inward_uv": [0.0, 1.0]})
        raster = fit.UsableRaster(chart, frame, self.NONE, 0.0, list(range(1500, 2000)))
        self.assertGreater(raster.ny, 100)
        self.assertGreater(sum(raster.up), 0)
        self.assertLess(unpacked[0], 20 * len(outline))
        # The same intervals as every segment tested on every line (even-odd), holes included.
        polygons = [[(x, y) for x, y in outline], [(-5.0, -5.0), (5.0, -5.0), (5.0, 5.0), (-5.0, 5.0)]]
        ys = [-19.5 + 0.37 * k for k in range(106)] + [5.0]
        for y in ys:
            crossings = sorted(
                x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                for polygon in polygons for (x0, y0), (x1, y1) in zip(polygon[-1:] + polygon[:-1], polygon)
                if (y0 <= y < y1) or (y1 <= y < y0)
            )
            expected = [(crossings[k], crossings[k + 1]) for k in range(0, len(crossings) - 1, 2)]
            self.assertEqual(fit._scanlines(polygons, [y - 1e-3, y])[1], expected, y)

    def test_a_picked_side_keeps_its_number_on_the_strain_limited_disk(self) -> None:
        # R2.1: {side: n} was read from the sides of the strain-limited disk, not the selection's.
        data, mesh = self._saddle()
        selection = {"ops": [{"op": "grow", "seed_facet": 256, "preset": "smooth"}]}  # at the y = -20 side
        selected = api.select_surface({"selection": selection}, data)["selection"]
        bottom = next(s for s in selected["sides"] if s["from_xyz"][1] == s["to_xyz"][1] == -20.0 and s["chord_mm"] > 20)
        top = next(s for s in selected["sides"] if s["from_xyz"][1] == s["to_xyz"][1] == 20.0 and s["chord_mm"] > 20)
        options = {"pitch_mm": 2.0, "rotation": "none", "proposals": 1}
        result = fit.fit_route({"selection": selection, "base": {"side": bottom["index"]}, "options": options}, data)
        self.assertIn("strain_limited", result["selection"])
        placement = result["proposals"][0]["placement"]
        self.assertEqual(placement["base_side"], bottom["index"])
        _, chart = fit.limited_chart(mesh, api.selection_chart(mesh, selection)[0], placement["strain_limited"])
        loop = chart.loops[chart.outer]
        for edge in placement["exit_edges"]:
            for v in (loop[edge], loop[(edge + 1) % len(loop)]):
                self.assertEqual(mesh.vertices[v][1], -20.0)  # on the picked side
        mapped = place.map_route({"selection": selection, "placement": placement, "design": result["proposals"][0]["design"]}, data)
        self.assertTrue(mapped["ok"], [r for r in mapped["verification"] if not r["passed"]])
        # The far side lies outside the disk: no exit there (and no other side in its place).
        with self.assertRaises(SurfaceError) as raised:
            fit.fit_route({"selection": selection, "base": {"side": top["index"]}, "options": options}, data)
        self.assertEqual(raised.exception.code, "E_SURFACE_BASE_EDGE")
        self.assertIn(f"Side {top['index']} ", raised.exception.message)

    def test_the_strain_limit_tries_disks_near_the_answer(self) -> None:
        # R5.0: the bisection's first trials were half and a quarter of the selection, each a cold solve.
        triangles = F.sphere_cap(60.0, 35.0, rings=12, segments=36)
        mesh = F.mesh(triangles)
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (0.0, 0.0, 60.0)), "preset": "smooth"}]}
        facets, chart = api.selection_chart(mesh, selection)
        trials = []
        original = chart_module.build_chart

        def recording(mesh_, region, **kwargs):
            built = original(mesh_, region, **kwargs)
            trials.append(len(built.vertices))
            return built

        chart_module.build_chart = recording
        try:
            region, limited, info = fit.limit_strain(mesh, facets, chart, selection, 0.003)
        finally:
            chart_module.build_chart = original
        self.assertLessEqual(limited.stats["strain_max"], 0.003)
        self.assertLessEqual(len(trials), fit.STRAIN_BISECTIONS + 1)
        self.assertLessEqual(max(trials), 1.5 * len(limited.vertices), trials)
        # A fine scan of the radius finds 223.00 mm2 on this (welded) cap.
        self.assertGreater(info["area_mm2"], 220.0)
        # A coarse dome grows its disk in steps, and trials that repeat a disk are free.
        # On this (welded) dome the largest disk within 2% is 209.34 mm2; the next one,
        # 272.08 mm2 at a radius of about 4.1 mm, stretches 2.25%.
        mesh = F.mesh(F.sphere_cap(30.0, 40.0, rings=3, segments=6))
        selection = {"ops": [{"op": "grow", "seed_facet": select.nearest_facet(mesh, (0.0, 0.0, 30.0)), "preset": "smooth"}]}
        facets, chart = api.selection_chart(mesh, selection)
        region, limited, info = fit.limit_strain(mesh, facets, chart, selection, 0.02)
        self.assertLessEqual(limited.stats["strain_max"], 0.02)
        self.assertGreater(info["area_mm2"], 209.0)


@unittest.skipUnless((ASSETS / "crank_gripper" / "tip_left.stl").exists(), "asset/ meshes are not committed")
class AssetFitTests(unittest.TestCase):
    def test_the_crank_pad(self) -> None:
        from surface.mesh import read_stl

        data = (ASSETS / "crank_gripper" / "tip_left.stl").read_bytes()
        mesh = read_stl(data)
        seed = select.nearest_facet(mesh, (1.812, -213.721, 138.929))
        selection = {"ops": [{"op": "grow", "seed_facet": seed}]}
        result = fit.fit_route({"selection": selection, "base": {"side": 6}, "options": {"rotation": "none", **MEASURED}}, data)
        best = result["proposals"][0]
        # shape fill with containment field (the defaults from masked-field phase P5e on): 666 of 32 x 32 on the
        # diagonal Row bus, 683 of 34 x 34 since shaped fields take the rectangles' caps (P5-diagonal-bus.md section
        # 21), 696 since the corner tolerance at every convex corner (section 24), the tip-first 688 (0.5 mm nearer the
        # tip) before it since section 26; containment board, the whole stack on the pad: a staircase triangle, 546 of 30 x
        # 32 (shape rectangle's 17 x 18 = 306 of before is no CAD option since section 26.16).
        self.assertEqual((best["metrics"]["rows"], best["metrics"]["columns"], best["metrics"]["taxels"]), (34, 34, 688))
        self.assertEqual(result["proposals"][1]["metrics"]["taxels"], 696)
        self.assertEqual((best["metrics"]["containment"], best["design"]["routing"]["row_sides"]), ("field", "both"))
        mapped = place.map_route({"selection": selection, "placement": best["placement"], "design": best["design"]}, data)
        self.assertTrue(mapped["ok"])
        self.assertEqual(mapped["taxel_count"], 688)
        board = fit.fit_route({"selection": selection, "base": {"side": 6}, "options": {"rotation": "none", "containment": "board", **MEASURED}},
                              data)["proposals"][0]
        self.assertEqual((board["metrics"]["rows"], board["metrics"]["columns"], board["metrics"]["taxels"]), (30, 32, 546))
        mapped = place.map_route({"selection": selection, "placement": board["placement"], "design": board["design"]}, data)
        self.assertEqual((mapped["ok"], mapped["taxel_count"]), (True, 546))


if __name__ == "__main__":
    unittest.main()
