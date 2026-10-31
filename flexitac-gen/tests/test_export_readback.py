"""Export self-check and input hardening (audit L8; decision D17).

The exporter regenerates the boards from the result's own design and profile
(which re-runs the whole-board DRC) and refuses a result that differs from
that generation, decodes every file it wrote (GTL, GTS, GKO, stiffener
layers, jlcpcb.json, netlist) and compares it with the layout, re-opens every
ZIP, and raises ExportError, never another exception, for anything malformed.
"""

from __future__ import annotations

import copy
import hashlib
import io
import itertools
import json
import math
import random
import types
import unittest
import zipfile
from unittest import mock

import engine.drc as drc
import engine.geometry as geometry
from engine import BuildCache, generate_design as _engine_generate_design, result_view
from engine.drc import verify_board, verify_registration
from exporters import ExportError, build_exports, direct_gerber, ipc356

try:
    from geometry_checks import straight_channel
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel


def generate_design(design=None, *args, **kwargs):
    """``engine.generate_design`` on the straight Row channel, which these tests measure (the generic template's default is
    the diagonal Row bus since claude/specs/masked-field/P5-diagonal-bus.md section 18; geometry_checks.straight_channel)."""

    return _engine_generate_design(straight_channel(design), *args, **kwargs)

# Values that are wrong almost anywhere in a generate_design result.
_BAD_VALUES = (None, "x", "", [], {}, [[]], {"x": 1}, float("nan"), float("inf"), -1, 0, True, 1e308, 10**400, 1e-9)


def _small_result() -> dict:
    result = generate_design({"rows": 3, "columns": 17, "connector": {"row_pins": 5}})
    if not result["ok"]:
        raise AssertionError(result["validation"]["errors"])
    return result


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TamperedEmissionTests(unittest.TestCase):
    """A writer defect is caught by the read-back, never shipped."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = _small_result()

    def assertReadBackFails(self, fragment: str = "Read-back") -> None:
        with self.assertRaises(ExportError) as caught:
            build_exports(self.result)
        self.assertIn(fragment, str(caught.exception))

    def test_untampered_exports_pass_the_read_back(self) -> None:
        self.assertEqual(set(build_exports(self.result)), {"top_fpc_gerber_zip", "bottom_fpc_gerber_zip", "project_review_bundle_zip"})

    def test_pads_written_with_lower_left_semantics_are_caught(self) -> None:
        # The audit C1 defect: centre-anchored pads emitted as lower-left boxes.
        def lower_left(rect):
            x, y, width, height = (float(rect[key]) for key in ("x", "y", "width_mm", "height_mm"))
            return [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]

        with mock.patch.object(direct_gerber, "rect_corners", lower_left):
            self.assertReadBackFails("Gerber_TopLayer.GTL region")

    def test_a_coordinate_three_microns_off_is_caught(self) -> None:
        original = direct_gerber._xy
        calls = itertools.count()

        def shifted(point):
            return original([point[0] + 3e-6, point[1]] if next(calls) == 40 else point)

        with mock.patch.object(direct_gerber, "_xy", shifted):
            self.assertReadBackFails("has a vertex at")

    def test_open_regions_are_caught(self) -> None:
        with mock.patch.object(direct_gerber, "_region", lambda points: ["G36*", *direct_gerber._stroke(points), "G37*"]):
            self.assertReadBackFails("open or degenerate region")

    def test_a_dropped_route_vertex_is_caught(self) -> None:
        original = direct_gerber._stroke

        def first_dropped(points):
            return original(points[1:]) if len(points) == 3 else original(points)

        with mock.patch.object(direct_gerber, "_stroke", first_dropped):
            self.assertReadBackFails("Gerber_TopLayer.GTL draw")

    def test_missing_x2_attributes_are_caught(self) -> None:
        original = direct_gerber._gerber_header

        def without_same_coordinates(*args):
            return [line for line in original(*args) if "SameCoordinates" not in line]

        with mock.patch.object(direct_gerber, "_gerber_header", without_same_coordinates):
            self.assertReadBackFails("X2 attributes")

    def test_stiffener_metadata_in_the_wrong_unit_is_caught(self) -> None:
        with mock.patch.object(direct_gerber, "_mil", lambda value: round(float(value), 4)):
            self.assertReadBackFails("jlcpcb.json entry 1")

    def test_a_netlist_location_off_by_ten_microns_is_caught(self) -> None:
        original = ipc356._test_record

        def moved(point):
            return original(dict(point, x=point["x"] + 0.01))

        with mock.patch.object(ipc356, "_test_record", moved):
            self.assertReadBackFails("netlist.ipc record")

    def test_zip_defects_are_caught(self) -> None:
        original = direct_gerber._deterministic_zip

        def dropped(files):
            return original({name: data for name, data in files.items() if name != max(files)})

        def deflated(files):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name in sorted(files):
                    archive.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), files[name], compress_type=zipfile.ZIP_DEFLATED)
            return stream.getvalue()

        def board_member_dropped(files):
            # Only the board ZIPs (the review bundle has no netlist): each is checked on its own.
            return dropped(files) if "netlist.ipc" in files else original(files)

        for writer, fragment in (
            (dropped, "member list"), (deflated, "is not stored as written"), (board_member_dropped, "member list"),
        ):
            with self.subTest(writer=writer.__name__), mock.patch.object(direct_gerber, "_deterministic_zip", writer):
                self.assertReadBackFails(fragment)


class TamperedResultTests(unittest.TestCase):
    """A result edited after generation, or with flipped flags, is refused."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = _small_result()

    def assertRefused(self, edit, fragment: str) -> None:
        tampered = copy.deepcopy(self.result)
        edit(tampered)
        with self.assertRaises(ExportError) as caught:
            build_exports(tampered)
        self.assertIn(fragment, str(caught.exception))

    def test_flipped_validity_flags_cannot_export_an_invalid_design(self) -> None:
        invalid = generate_design({"matrix": {"pitch_x_mm": 1.0, "taxel_width_mm": 0.9}})
        self.assertFalse(invalid["ok"])
        invalid["ok"] = True
        invalid["manifest"]["geometry_valid"] = True
        with self.assertRaisesRegex(ExportError, "validation errors"):
            build_exports(invalid)
        invalid["validation"]["errors"] = []
        with self.assertRaisesRegex(ExportError, "boards|checks do not match"):
            build_exports(invalid)

    def test_geometry_edits_are_refused(self) -> None:
        # The boards must be the engine's generation of the result's own design
        # and profile (D17): rule-breaking edits and edits the DRC would pass
        # alike are refused, with the path of the first difference.
        def row(result):
            return result["boards"]["row"]["layers"]

        def column(result):
            return result["boards"]["column"]

        def move_pad(result):
            row(result)["top_copper"]["pads"][0]["x"] += 50.0

        def short_routes(result):
            # ROW_03's tail piece ends at ROW_02's junction instead of its own.
            routes = row(result)["top_copper"]["routes"]
            routes[0]["points"][1] = list(routes[2]["points"][1])

        def move_electrode(result):
            row(result)["top_copper"]["electrodes"][0]["x"] = -11.95

        def move_stiffener(result):
            stiffener = column(result)["layers"]["bottom_stiffener"][0]
            stiffener["points"] = [[x + 40.0, y] for x, y in stiffener["points"]]

        def outline_spike(result):
            points = column(result)["outline"]["points"]
            points[1], points[2] = points[2], points[1]

        def second_connector_stiffener(result):
            stiffeners = column(result)["layers"]["bottom_stiffener"]
            stiffeners.append(copy.deepcopy(stiffeners[0]))

        for edit, path in (
            (move_pad, "boards.row.layers.top_copper.pads[0].x"),
            (short_routes, "boards.row.layers.top_copper.routes[0].points[1][0]"),
            (move_electrode, "boards.row.layers.top_copper.electrodes[0].x (-11.95, expected"),
            (move_stiffener, "boards.column.layers.bottom_stiffener[0].points[0][0]"),
            (outline_spike, "boards.column.outline.points[1][0]"),
            (second_connector_stiffener, "boards.column.layers.bottom_stiffener does not"),
        ):
            with self.subTest(edit=edit.__name__):
                self.assertRefused(edit, path)
                self.assertRefused(edit, "does not match the geometry the engine generates for its design and profile")

    def test_drc_clean_edits_are_refused(self) -> None:
        # Each edit passes the whole-board DRC, so only the binding of the
        # geometry to the build identity can refuse it (reviewer finding F1).
        def micron(result):
            # COL_02's electrode end 1 um sideways, still on the electrode (a bend of the
            # bundle has no slack: 1 um there breaks the 0.127 mm trace space).
            points = result["boards"]["column"]["layers"]["top_copper"]["routes"][3]["points"]
            points[-1][0] = round(points[-1][0] + 0.001, 6)

        def swapped_pieces(result):
            # COL_03's fan-out piece listed before its tail piece: the same copper.
            # (A width edit no longer passes the DRC: route_width, since 2026-10-15.)
            routes = result["boards"]["column"]["layers"]["top_copper"]["routes"]
            routes[4], routes[5] = routes[5], routes[4]

        def smaller_opening(result):
            opening = result["boards"]["row"]["layers"]["top_coverlay_openings"][0]
            opening["width_mm"] = round(opening["width_mm"] - 0.05, 6)

        def route_into_pad(result):
            points = result["boards"]["row"]["layers"]["top_copper"]["routes"][0]["points"]
            points[0][1] = round(points[0][1] - 0.001, 6)

        for edit, path in (
            (micron, "boards.column.layers.top_copper.routes[3].points[5][0]"),
            (swapped_pieces, "boards.column.layers.top_copper.routes[4].points does not match"),
            (smaller_opening, "boards.row.layers.top_coverlay_openings[0].width_mm"),
            (route_into_pad, "boards.row.layers.top_copper.routes[0].points[0][1]"),
        ):
            with self.subTest(edit=edit.__name__):
                tampered = copy.deepcopy(self.result)
                edit(tampered)
                row, column = tampered["boards"]["row"], tampered["boards"]["column"]
                profile = tampered["profile"]
                drc_errors = [*verify_board(row, profile, tampered["design"])["errors"], *verify_board(column, profile, tampered["design"])["errors"]]
                self.assertEqual(drc_errors + verify_registration(row, column, profile)["errors"], [])
                self.assertRefused(edit, path)

    def test_substituted_boards_and_previews_are_refused(self) -> None:
        other = generate_design({"rows": 4, "columns": 9, "connector": {"row_pins": 5}})
        swapped = generate_design({"rows": 3, "columns": 17, "connector": {"row_pins": 5}, "row_fpc_position": "bottom"})
        self.assertTrue(other["ok"] and swapped["ok"])

        def chimera(result):
            # A valid board pair of another design under this build identity (audit AGENT-7).
            result["boards"].update(copy.deepcopy(other["boards"]))

        def reassigned(result):
            # The same design with the other physical role mapping.
            result["boards"].update(copy.deepcopy(swapped["boards"]))

        def preview(result):
            result["boards"]["row"]["svg"] = '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'

        def metrics(result):
            result["boards"]["column"]["metrics"]["route_count"] += 1

        def construction(result):
            result["boards"]["column"]["construction"]["note"] = "edited"

        for edit, path in (
            (chimera, "boards.row.construction"),
            (reassigned, "boards.row.grid_registration.active_region.y"),
            (preview, "boards.row.svg does not"),
            (metrics, "boards.column.metrics.route_count (35, expected 34)"),
            (construction, "boards.column.construction.note (unexpected)"),
        ):
            with self.subTest(edit=edit.__name__):
                self.assertRefused(edit, path)
                self.assertRefused(edit, "does not match the geometry the engine generates")

    def test_a_self_consistent_identity_must_still_be_the_engine_build(self) -> None:
        def recompute_identity(result):
            manifest = result["manifest"]
            manifest["design_sha256"] = _sha(_canonical(result["design"]))
            identity = {key: manifest[key] for key in ("design_sha256", "profile_sha256", "generator", "exporter")}
            manifest["build_sha256"] = _sha(_canonical(identity))
            manifest["build_id"] = f"{manifest['slug']}-{manifest['build_sha256'][:12]}"

        def float_count(result):
            # Equal in value, but not the canonical design the engine normalizes it to.
            result["design"]["matrix"]["rows"] = 3.0
            recompute_identity(result)

        def foreign_slug(result):
            result["manifest"]["slug"] = "someone-else"
            result["manifest"]["build_id"] = "someone-else-" + result["manifest"]["build_sha256"][:12]

        def summary(result):
            result["manifest"]["board_summary"]["row"]["outline_width_mm"] += 1.0

        for edit, fragment in (
            (float_count, "not the canonical design"),
            (foreign_slug, "Result manifest.build_id"),
            (summary, "Result manifest.board_summary.row.outline_width_mm"),
        ):
            with self.subTest(edit=edit.__name__):
                self.assertRefused(edit, fragment)

    def test_design_warnings_must_be_the_engines(self) -> None:
        result = generate_design({"rows": 3, "columns": 4, "taxel_width_mm": 1.7})
        self.assertTrue(result["ok"], result["validation"]["errors"])
        warning = next(issue for issue in result["validation"]["warnings"] if issue["code"] == "W_HIGH_FILL_FACTOR")
        warning["message"] = "Edited after generation."
        with self.assertRaisesRegex(ExportError, "not the design warnings the engine reports"):
            build_exports(result)

    def test_the_regenerated_drc_verdict_is_enforced(self) -> None:
        def failing_registration(row, column, profile):
            answer = verify_registration(row, column, profile)
            return {**answer, "errors": [{"code": "E_REGISTRATION", "field": "tail.column_side", "message": "Injected."}]}

        expected = r"Regenerating the result's design fails validation \(1 error\(s\)\); first E_REGISTRATION"
        with mock.patch("engine.core.verify_registration", failing_registration), self.assertRaisesRegex(ExportError, expected):
            build_exports(self.result)

    def test_edited_drc_records_are_refused(self) -> None:
        def flag(result):
            result["boards"]["row"]["verification"]["all_checks_passed"] = False

        def measurement(result):
            result["boards"]["column"]["verification"]["checks"]["copper_to_outline"]["measured_mm"] = 9.9

        def registration(result):
            result["boards"]["row"]["verification"]["registration"]["orthogonal"] = False

        for edit in (flag, measurement, registration):
            with self.subTest(edit=edit.__name__):
                self.assertRefused(edit, "does not match a fresh check")

    def test_identity_must_describe_the_result(self) -> None:
        def design(result):
            result["design"]["matrix"]["rows"] = 4

        def profile(result):
            result["profile"]["fanout"]["maximum_taper_angle_deg"] = 59.0

        def exporter(result):
            result["manifest"]["exporter"] = "direct-gerber-pure-stdlib/0.1.1"

        def generator(result):
            # The exporter regenerates with this engine, so the build must be this generator's.
            result["manifest"]["generator"] = "deterministic-sensor-core/0.2.0"

        def build_id(result):
            result["manifest"]["build_id"] = "someone-else-000000000000"

        def warning_count(result):
            result["manifest"]["checks"]["warning_count"] = 3

        def layout(result):
            result["derived_layout"] = copy.deepcopy(result["derived_layout"])
            result["derived_layout"]["boards"]["row"]["tail"]["length_mm"] = 99.0

        for edit, fragment in (
            (design, "design_sha256"),
            (profile, "profile_sha256"),
            (exporter, "manifest exporter"),
            (generator, "manifest generator does not match the result (expected deterministic-sensor-core/0.4.0)"),
            (build_id, "build_id"),
            (warning_count, "checks do not match"),
            (layout, "derived_layout"),
        ):
            with self.subTest(edit=edit.__name__):
                self.assertRefused(edit, fragment)

    def test_out_of_format_values_are_refused_before_writing(self) -> None:
        def far(result):
            result["boards"]["row"]["outline"]["points"][0] = [12345.678, 0.0]

        def thin_route(result):
            result["boards"]["row"]["layers"]["top_copper"]["routes"][0]["width_mm"] = 1e-7

        def half_ounce_route(result):
            # Above JLC's 18 um minimum (0.0889 mm), below the 1 oz minimum of the ordered copper.
            result["boards"]["row"]["layers"]["top_copper"]["routes"][1]["width_mm"] = 0.095

        def unsegmented_route(result):
            result["boards"]["row"]["layers"]["top_copper"]["routes"][1]["segment"] = "bundle"

        def repeated_vertex(result):
            points = result["boards"]["column"]["outline"]["points"]
            points.insert(1, list(points[0]))

        def tiny_electrode(result):
            result["boards"]["row"]["layers"]["top_copper"]["electrodes"][0]["height_mm"] = 1e-7

        def injected_id(result):
            result["boards"]["row"]["id"] = "top*%ADD99C,1*%"

        def unicode_id(result):
            result["boards"]["row"]["id"] = "top_rows_fpc_é"

        def nc_net(result):
            pads = result["boards"]["row"]["layers"]["top_copper"]["pads"]
            next(pad for pad in pads if pad["kind"] == "connector_nc_pad")["net"] = "NC_99"

        def duplicate_pin(result):
            pads = result["boards"]["row"]["layers"]["top_copper"]["pads"]
            pads[1]["pin"] = pads[0]["pin"]

        def no_openings(result):
            result["boards"]["column"]["layers"]["top_coverlay_openings"] = []

        def bow_tie_stiffener(result):
            # Not caught by the DRC (zone and containment only): every region
            # contour the exporter writes must be simple (finding F2).
            points = result["boards"]["row"]["layers"]["bottom_stiffener"][0]["points"]
            points[0], points[1] = points[1], points[0]

        def bow_tie_cutout(result):
            cutout = result["boards"]["column"]["outline"]["cutouts"][0]
            cutout[0], cutout[1] = cutout[1], cutout[0]

        for edit, fragment in (
            (bow_tie_stiffener, "top_rows_fpc stiffener is not a simple polygon"),
            (bow_tie_cutout, "routed cutout 1 is not a simple polygon"),
            (far, "outside +/-10000 mm"),
            (thin_route, "fabrication minimum"),
            (half_ounce_route, "fabrication minimum 0.1016 mm of the profile's copper"),
            (unsegmented_route, "must be a tail or fanout piece"),
            (repeated_vertex, "zero-length edge"),
            (tiny_electrode, "collapses below"),
            (injected_id, "Board id"),
            (unicode_id, "Board id"),
            (nc_net, "NC_<pin>"),
            (duplicate_pin, "each used once"),
            (no_openings, "coverlay openings"),
        ):
            with self.subTest(edit=edit.__name__):
                self.assertRefused(edit, fragment)


class GenuineResultTests(unittest.TestCase):
    """An untampered result exports wherever and however it was produced."""

    DESIGNS = (
        {},
        {"rows": 3, "columns": 17, "connector": {"row_pins": 5}, "connector_side": "top"},
        {"rows": 40, "columns": 7, "pitch_x_mm": 1.3, "pitch_y_mm": 1.3, "taxel_width_mm": 0.78, "taxel_height_mm": 0.78},
        {"rows": 1, "columns": 1, "connector_side": "left"},
    )

    def test_drc_records_do_not_depend_on_float_noise(self) -> None:
        # Python versions differ in the last bits of sum(), hypot() and dist();
        # the DRC record (minima and their locations) must not, or a result
        # saved on one interpreter would be refused on another (finding F3).
        for design, seed in itertools.product(self.DESIGNS, range(3)):
            result = generate_design(design)
            self.assertTrue(result["ok"], result["validation"]["errors"])
            noisy_math, noisy_sum = _noisy(random.Random(seed))
            with mock.patch.object(drc, "math", noisy_math), mock.patch.object(geometry, "math", noisy_math), mock.patch.object(
                drc, "sum", noisy_sum, create=True
            ):
                fresh = {name: verify_board(board, result["profile"], result["design"])["measurements"] for name, board in result["boards"].items()}
                registration = verify_registration(result["boards"]["row"], result["boards"]["column"], result["profile"])["measurements"]
            for name, board in result["boards"].items():
                with self.subTest(design=design, seed=seed, board=name):
                    self.assertEqual(_canonical(dict(fresh[name], registration=registration)), _canonical(board["verification"]))

    def test_saved_viewed_and_cached_results_export_the_same_bytes(self) -> None:
        cache = BuildCache()
        result = generate_design(self.DESIGNS[1], cache=cache)
        reference = build_exports(result)
        saved = json.loads(json.dumps(result))
        for label, variant, options in (
            ("saved as JSON", saved, {}),
            ("full view without derived_layout", result_view(result, "full"), {}),
            ("with the build cache", result, {"cache": cache}),
        ):
            with self.subTest(variant=label):
                self.assertEqual(build_exports(variant, **options), reference)
        self.assertEqual((cache.misses, cache.hits), (1, 1))


def _noisy(generator: random.Random):
    """``math`` and ``sum`` stand-ins whose float results move by one or two units in the last place."""

    def wobble(value: float) -> float:
        return value * (1 + generator.choice((-2, -1, 1, 2)) * 2.0**-52)

    noisy = types.SimpleNamespace(**{name: getattr(math, name) for name in dir(math) if not name.startswith("_")})
    noisy.hypot = lambda *values: wobble(math.hypot(*values))
    noisy.dist = lambda first, second: wobble(math.dist(first, second))

    def noisy_sum(values, start=0):
        values = list(values)
        if all(isinstance(value, int) for value in values) and isinstance(start, int):
            return sum(values, start)
        return wobble(math.fsum(values) + start)

    return noisy, noisy_sum


class MalformedInputTests(unittest.TestCase):
    """Whatever the input, the only exception is ExportError (audit L8)."""

    def test_non_results_raise_export_error(self) -> None:
        nested: list = []
        for _ in range(100_000):
            nested = [nested]
        result = _small_result()
        deep = dict(result, design=nested)
        empty_parts = {
            "ok": True, "design": {}, "manifest": {"geometry_valid": True}, "boards": {}, "profile": {},
            "validation": {"errors": [], "warnings": []},
        }
        for value in (None, [], "result", 42, {}, {"ok": True}, empty_parts, deep, dict(result, boards={"row": None, "column": None})):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(ExportError):
                    build_exports(value)

    def test_a_profile_number_beyond_the_float_range_is_a_profile_error(self) -> None:
        # Reported by the profile check itself, not by the catch-all for internal errors.
        result = _small_result()
        result["profile"]["routing"]["finger_trace_width_mm"] = 10**400
        with self.assertRaisesRegex(ExportError, "manufacturing profile is inconsistent: profile.routing.finger_trace_width_mm"):
            build_exports(result)

    def test_unexpected_internal_errors_surface_as_export_error(self) -> None:
        # The explicit checks catch every corruption tried so far; whatever slips
        # past them still reaches the caller as an ExportError.
        with mock.patch.object(direct_gerber, "_pinout", side_effect=KeyError("pin")):
            with self.assertRaisesRegex(ExportError, "KeyError"):
                build_exports(_small_result())

    def test_random_corruptions_raise_only_export_error(self) -> None:
        base = generate_design({"rows": 2, "columns": 3})
        self.assertTrue(base["ok"])
        gerbers = {key: data for key, data in build_exports(base).items() if key != "project_review_bundle_zip"}
        generator = random.Random(20261014)
        outcomes = {"refused": 0, "exported": 0}
        for trial in range(150):
            corrupted = copy.deepcopy(base)
            path = _corrupt(corrupted, generator)
            with self.subTest(trial=trial, path=path):
                try:
                    exports = build_exports(corrupted)
                except ExportError:
                    outcomes["refused"] += 1
                else:
                    # Unless the value was already there, only the request's
                    # normalization record (copied into validation.json) may
                    # differ; the Gerbers never do.
                    if _canonical(corrupted) != _canonical(base):
                        self.assertEqual(path[:2], ["validation", "normalization"])
                    self.assertEqual({key: exports[key] for key in gerbers}, gerbers)
                    outcomes["exported"] += 1
        self.assertGreater(outcomes["refused"], 100, outcomes)


def _corrupt(result: dict, generator: random.Random) -> list:
    """Replace one random leaf or container below boards/manifest/validation with a bad value."""

    node = result
    path: list = []
    key = generator.choice(["boards", "boards", "boards", "manifest", "validation", "design"])
    while True:
        path.append(key)
        child = node[key]
        containers = isinstance(child, (dict, list)) and len(child) > 0
        if not containers or generator.random() < 0.15:
            break
        node = child
        key = generator.choice(list(child)) if isinstance(child, dict) else generator.randrange(len(child))
    node[key] = copy.deepcopy(generator.choice(_BAD_VALUES))
    return path


if __name__ == "__main__":
    unittest.main()
