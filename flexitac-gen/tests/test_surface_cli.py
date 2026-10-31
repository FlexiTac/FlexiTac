"""CAD mode on the command line: ``cli.py surface`` as a subprocess."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    import surface_fixtures as F
except ImportError:  # run as a package
    from tests import surface_fixtures as F

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> tuple:
    completed = subprocess.run(
        [sys.executable, "-B", str(ROOT / "cli.py"), "surface", *args], capture_output=True, text=True, timeout=600, cwd=ROOT
    )
    return completed.returncode, json.loads(completed.stdout)


class SurfaceCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.part = Path(cls.directory.name) / "finger.stl"
        cls.part.write_bytes(F.stl_bytes(F.soft_finger_replica()))

    def test_fit_writes_the_proposal_files_and_map_reuses_the_placement(self) -> None:
        out = Path(self.directory.name) / "out"
        options = Path(self.directory.name) / "options.json"
        options.write_text(json.dumps({"pitch_mm": 3.0, "rotation": "none", "proposals": 1}))
        status, document = run("fit", str(self.part), "--pick", "0,-12.9,-62.7", "--base", "0,-12.9,-3", "--options", str(options), "--out", str(out))
        self.assertEqual(status, 0, document)
        self.assertTrue(document["ok"])
        stem = document["build_id"]
        for key in ("design", "placement", "taxel_map", "wrap_template", "top_fpc_gerber_zip", "bottom_fpc_gerber_zip", "project_review_bundle_zip"):
            self.assertTrue(Path(document["files"][key]).is_file(), key)
        self.assertTrue(Path(document["files"]["placement"]).name.startswith(stem))
        status, mapped = run("map", str(self.part), "--placement", document["files"]["placement"])
        self.assertEqual(status, 0, mapped)
        self.assertEqual(mapped["taxel_count"], document["metrics"]["taxels"])

    def test_errors_and_exit_statuses(self) -> None:
        status, document = run("fit", str(self.part))
        self.assertEqual((status, document["code"]), (2, "E_CLI_INPUT"))
        status, document = run("inspect", str(Path(self.directory.name) / "missing.stl"))
        self.assertEqual((status, document["code"]), (2, "E_CLI_INPUT"))
        bad = Path(self.directory.name) / "bad.stl"
        bad.write_bytes(b"not an stl")
        status, document = run("inspect", str(bad))
        self.assertEqual((status, document["code"]), (1, "E_SURFACE_MESH_FORMAT"))
        status, document = run("inspect", str(self.part))
        self.assertEqual((status, document["mesh"]["facets"]), (0, 108))

    def test_map_failures_inputs_and_units(self) -> None:
        directory = Path(self.directory.name)
        options = directory / "fit-options.json"
        options.write_text(json.dumps({"pitch_mm": 3.0, "rotation": "none", "proposals": 1}))
        status, fitted = run("fit", str(self.part), "--pick", "0,-12.9,-62.7", "--base", "0,-12.9,-3", "--options", str(options))
        self.assertEqual(status, 0, fitted)
        placement = fitted["proposals"][0]["placement"]
        # A placement moved off the face (30 mm along the exit: the tails miss it, whose reach is no number)
        # maps with ok false and exit status 1.
        moved = dict(placement, field_origin_base=[placement["field_origin_base"][0] + 30.0, placement["field_origin_base"][1]])
        path = directory / "moved.json"
        path.write_text(json.dumps(moved))
        status, mapped = run("map", str(self.part), "--placement", str(path))
        self.assertEqual((status, mapped["ok"]), (1, False))
        # Picked side numbers are kept as they are.
        status, side = run("fit", str(self.part), "--pick", "0,-12.9,-62.7", "--base", "0", "--options", str(options))
        self.assertEqual([b["side"] for b in side["bases"]], [0], side)
        # Bad input: a NaN pick, a file that is not strict JSON, a unit that changes the scale.
        status, document = run("select", str(self.part), "--pick", "nan,nan,nan")
        self.assertEqual((status, document["code"]), (2, "E_CLI_INPUT"))
        broken = directory / "broken.json"
        broken.write_text('{"pitch_mm": NaN}')
        status, document = run("fit", str(self.part), "--pick", "0,-12.9,-62.7", "--options", str(broken))
        self.assertEqual((status, document["code"]), (2, "E_CLI_INVALID_JSON"))
        self.assertIn("broken.json", document["error"])
        status, mm = run("inspect", str(self.part), "--unit", "mm")
        status_cm, cm = run("inspect", str(self.part), "--unit", "cm")
        self.assertEqual((status, status_cm, cm["mesh"]["unit"]), (0, 0, "cm"))
        self.assertAlmostEqual(cm["mesh"]["extent_mm"][2], 10 * mm["mesh"]["extent_mm"][2], places=3)

    def fitted_placement(self) -> dict:
        """A fit proposal's placement for the replica's contact face (fitted once)."""

        cached = getattr(type(self), "_placement", None)
        if cached is None:
            options = Path(self.directory.name) / "placement-options.json"
            options.write_text(json.dumps({"pitch_mm": 3.0, "rotation": "none", "proposals": 1}))
            status, fitted = run("fit", str(self.part), "--pick", "0,-12.9,-62.7", "--base", "0,-12.9,-3", "--options", str(options))
            self.assertEqual(status, 0, fitted)
            cached = type(self)._placement = fitted["proposals"][0]["placement"]
        return json.loads(json.dumps(cached))

    def test_map_takes_the_given_options_over_the_placements(self) -> None:
        directory = Path(self.directory.name)
        placement = directory / "options-placement.json"
        placement.write_text(json.dumps(self.fitted_placement()))
        status, mapped = run("map", str(self.part), "--placement", str(placement))
        # The default fit (containment field from masked-field phase P5e on) checks the taxel field F.
        clearance = next(r for r in mapped["verification"] if r["rule"] == "field_clearance")
        self.assertEqual((status, clearance["required"]), (0, 0.0))
        # As over HTTP: --options replaces the fit's own (a 15 mm margin cannot hold on this face); without
        # containment the design's own (its diagonal Row bus: field) is taken.
        options = directory / "map-options.json"
        options.write_text(json.dumps({"edge_margin_mm": 15.0, "strain_limit": 0.0001}))
        status, mapped = run("map", str(self.part), "--placement", str(placement), "--options", str(options))
        records = {r["rule"]: r for r in mapped["verification"]}
        self.assertEqual((status, mapped["ok"]), (1, False))
        self.assertEqual((records["field_clearance"]["required"], records["strain_under_field"]["required"]), (15.0, 0.0001))
        options.write_text(json.dumps({"edge_margin_mm": 15.0, "strain_limit": 0.0001, "containment": "board"}))
        status, mapped = run("map", str(self.part), "--placement", str(placement), "--options", str(options))
        records = {r["rule"]: r for r in mapped["verification"]}
        self.assertEqual((status, records["board_clearance"]["required"], records["strain_under_boards"]["required"]), (1, 15.0, 0.0001))

    def test_the_options_cad_mode_no_longer_has(self) -> None:
        # P5-diagonal-bus.md section 26.16: a fit naming shape rectangle, the generic template or a rectangle preference is
        # refused (exit 1, E_SURFACE_REQUEST, the reason named: rectangles are the rectangular mode's); a saved placement
        # that names them as a fit then accepted them maps as fitted (the map fits nothing; the options name the
        # containment, field, so shape and template default nothing here; with the generic template that fit refused
        # containment field: section 26.18).
        directory = Path(self.directory.name)
        options = directory / "removed-options.json"
        for removed in ({"shape": "rectangle"}, {"template": "generic"}, {"rectangle_preference_pct": 5}):
            with self.subTest(options=removed):
                options.write_text(json.dumps(dict(removed, pitch_mm=3.0, rotation="none", proposals=1)))
                status, document = run("fit", str(self.part), "--pick", "0,-12.9,-62.7", "--base", "0,-12.9,-3", "--options", str(options))
                self.assertEqual((status, document["code"]), (1, "E_SURFACE_REQUEST"))
                self.assertIn("rectangular mode", document["error"])
        placement = self.fitted_placement()
        placement["options"].update(shape="rectangle", template="surface", rectangle_preference_pct=30)
        path = directory / "saved-placement.json"
        path.write_text(json.dumps(placement))
        status, mapped = run("map", str(self.part), "--placement", str(path))
        self.assertEqual((status, mapped["ok"], mapped["build_id"]), (0, True, placement["build_id"]))
        placement["options"].update(template="generic")
        path.write_text(json.dumps(placement))
        status, document = run("map", str(self.part), "--placement", str(path))
        self.assertEqual((status, document["code"]), (1, "E_SURFACE_REQUEST"))
        self.assertIn("on the generic template", document["error"])

    def test_a_deeply_nested_placement_is_refused_and_every_reply_is_one_json_document(self) -> None:
        import cli

        # map echoes the placement's keys, so a placement nested beyond place.MAX_PLACEMENT_DEPTH is
        # refused: 40 levels (every loader reads them) and 1100 where the loader reads them (beyond
        # the indenting encoder; near 3.12's loader limit, beyond the C encoder too).
        for depth in (40, 1100):
            text = json.dumps(self.fitted_placement())[:-1] + ', "note": ' + "[" * depth + "]" * depth + "}"
            path = Path(self.directory.name) / f"deep-placement-{depth}.json"
            path.write_text(text)
            try:
                json.loads(text)
                loads = True
            except RecursionError:  # an older Python's loader refuses it: an input error there
                loads = False
            for pretty in ((), ("--pretty",)):
                status, mapped = run(*pretty, "map", str(self.part), "--placement", str(path))
                if loads:
                    self.assertEqual((status, mapped["code"]), (1, "E_SURFACE_REQUEST"), mapped)
                    self.assertIn("levels deep", mapped["error"])
                else:
                    self.assertEqual((status, mapped["code"]), (2, "E_CLI_INVALID_JSON"))
        # --pretty falls back to the compact C encoder where it goes deeper than the indenting one.
        document: list = []
        for _ in range(1099):
            document = [document]
        try:
            compact = json.dumps(document)
        except RecursionError:  # 3.9's C encoder stops at the same depth: main reports E_CLI_INTERNAL
            compact = None
        if compact is not None:
            self.assertEqual(cli._dumps(document, True), compact)
        # A reply that no encoder writes is still one JSON document: exit 3, E_CLI_INTERNAL.
        out = io.StringIO()
        with mock.patch("surface.api.inspect", lambda *args: {"ok": True, "extent": math.nan}), contextlib.redirect_stdout(out):
            status = cli.main(["surface", "inspect", str(self.part)])
        self.assertEqual((status, json.loads(out.getvalue())["code"]), (3, "E_CLI_INTERNAL"))

    def test_internal_errors_are_exit_3_and_a_pick_parses_the_mesh_once(self) -> None:
        import cli
        from surface import api, mesh as mesh_module

        def in_process(*args: str) -> tuple:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = cli.main(["surface", *args])
            return status, json.loads(out.getvalue())

        def broken(*args, **kwargs):
            raise ValueError("cannot convert float NaN to integer")

        # A ValueError inside CAD mode is a bug (exit 3), not an argument error (exit 2).
        with mock.patch.object(api, "inspect", broken):
            status, document = in_process("inspect", str(self.part))
        self.assertEqual((status, document["code"]), (3, "E_CLI_INTERNAL"))
        status, document = in_process("fit", str(self.part), "--pick", "0,-12.9,-62.7", "--base", "\u00b2")
        self.assertEqual((status, document["code"]), (2, "E_CLI_INPUT"))
        # A side index too long for int() (3.11+) is still an argument error, on every Python.
        status, document = in_process("fit", str(self.part), "--pick", "0,-12.9,-62.7", "--base", "9" * 5000)
        self.assertEqual((status, document["code"]), (2, "E_CLI_INPUT"))
        # --pick finds its facet on the mesh the route then reuses: one parse.
        box = Path(self.directory.name) / "pick-box.stl"
        box.write_bytes(F.stl_bytes(F.box((30.0, 20.0, 10.0))))
        sha256 = hashlib.sha256(box.read_bytes()).hexdigest()
        for key in [key for key in api._MESH_CACHE if key[0] == sha256]:
            api._MESH_CACHE.pop(key)
        parses = []
        parse = mesh_module.read_stl

        def counting(*args, **kwargs):
            parses.append(1)
            return parse(*args, **kwargs)

        with mock.patch.object(mesh_module, "read_stl", counting), mock.patch.object(api, "read_stl", counting):
            status, document = in_process("select", str(box), "--pick", "15,10,10")
        self.assertEqual((status, document["selection"]["kind"], len(parses)), (0, "planar", 1))


if __name__ == "__main__":
    unittest.main()
