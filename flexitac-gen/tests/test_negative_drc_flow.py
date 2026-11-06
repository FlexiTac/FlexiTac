"""Post-generation DRC failures, end to end (audit H4: no test reached a DRC error branch; H5, D11).

Valid inputs pass the whole-board DRC by construction, so each case injects
one defect into a board as the layout builder returns it (before the board
is turned to its tail side and assigned) and follows the failure through
``generate_design``, the manifest, the exporter, the HTTP API and the CLI.
Every DRC-sourced code of the issue catalogue must come out of
``generate_design`` in at least one case: a new DRC rule needs a case here.
"""

from __future__ import annotations

import contextlib
import copy
import http.client
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import app
import cli
from engine import core, generate_design as _engine_generate_design
from engine.schema import ERROR_CODES
from exporters import ExportError, build_exports

try:
    from geometry_checks import straight_channel
    import defaults_of_before
except ImportError:  # run as a package
    from tests.geometry_checks import straight_channel
    from tests import defaults_of_before


def setUpModule() -> None:
    # The default electrodes of before (1.4 mm at 2 mm, fill 0.7): this module's pinned numbers were measured with them
    # (tests/defaults_of_before.py; the user's decision of 2026-11-06 made the default fill 0.5).
    defaults_of_before.start()


def generate_design(design=None, *args, **kwargs):
    """``engine.generate_design`` on the straight Row channel, which these tests measure (the generic template's default is
    the diagonal Row bus since claude/specs/masked-field/P5-diagonal-bus.md section 18; geometry_checks.straight_channel)."""

    return _engine_generate_design(straight_channel(design), *args, **kwargs)

BUILDERS = {"rows": "build_row_board", "columns": "build_column_board"}
BOARD_KEYS = {"rows": "row", "columns": "column"}
JSON_HEADERS = {"Content-Type": "application/json"}


# Each defect edits a board in the builder's canonical frame (tail down).

def _contact_toward_tip(board):
    # 0.2 mm from the tip edge instead of 0.3 mm.
    board["layers"]["top_copper"]["pads"][0]["y"] -= 0.1


def _pad_far_away(board):
    board["layers"]["top_copper"]["pads"][-1]["x"] += 500.0


def _pad_beside_electrode(board):
    electrode = board["layers"]["top_copper"]["electrodes"][0]
    pad = board["layers"]["top_copper"]["pads"][-1]
    pad["x"] = round(electrode["x"] + electrode["width_mm"] + 0.1 + pad["width_mm"] / 2, 6)
    pad["y"] = round(electrode["y"] + electrode["height_mm"] / 2, 6)


def _squeeze_pad(board):
    board["layers"]["top_copper"]["pads"][1]["x"] -= 0.1


def _widen_electrode(board):
    board["layers"]["top_copper"]["electrodes"][0]["width_mm"] += 0.5


def _fanout(board, net):
    return next(route for route in board["layers"]["top_copper"]["routes"] if route["net"] == net and route["segment"] == "fanout")


def _shift_lane(board):
    # ROW_02's channel lane runs 0.1 mm closer to ROW_01's (0.027 mm of the 0.127 mm bundle spacing).
    route = _fanout(board, "ROW_02")
    lane = route["points"][2][0]  # junction, expansion bend, then the lane
    route["points"] = [[x - 0.1, y] if abs(x - lane) < 1e-9 else [x, y] for x, y in route["points"]]


def _lane_to_edge(board):
    route = next(route for route in board["layers"]["top_copper"]["routes"] if route["net"] == "ROW_01")
    lane = route["points"][0][0]
    route["points"] = [[x - 0.2, y] if abs(x - lane) < 1e-9 else [x, y] for x, y in route["points"]]


def _lead_toward_neighbor(board):
    route = next(route for route in board["layers"]["top_copper"]["routes"] if route["net"] == "ROW_01")
    lane = route["points"][0][0]
    route["points"] = [[x + 0.15, y] if abs(x - lane) < 1e-9 else [x, y] for x, y in route["points"]]


def _stub_toward_neighbor(board):
    # 1.2 mm sideways leaves 0.0365 mm of COL_03's 0.127 mm stub to the next electrode.
    route = _fanout(board, "COL_03")
    route["points"][-1][0] += 1.2
    route["points"][-2][0] += 1.2


def _route_into_slot_margin(board):
    slot = board["outline"]["cutouts"][0]
    left = min(point[0] for point in slot)
    route = _fanout(board, "COL_16")  # the left lane's route next to the slot
    route["points"] = [[left - 0.2, y] if abs(x - (left - 0.75)) < 1e-6 else [x, y] for x, y in route["points"]]


def _slot_to_edge(board):
    board["outline"]["cutouts"][0] = [[x - 26.0, y] for x, y in board["outline"]["cutouts"][0]]


def _narrow_body(board):
    right = max(x for x, _ in board["outline"]["points"])
    board["outline"]["points"] = [[x - 0.5 if x > right - 1.0 else x, y] for x, y in board["outline"]["points"]]


def _opening_out(board):
    board["layers"]["top_coverlay_openings"][0]["x"] -= 5.0


def _split_opening(board):
    opening = board["layers"]["top_coverlay_openings"][0]
    half = dict(opening, width_mm=round(opening["width_mm"] / 2 - 0.15, 6))
    other = dict(half, x=round(opening["x"] + opening["width_mm"] / 2 + 0.15, 6))
    board["layers"]["top_coverlay_openings"][0:1] = [half, other]


def _opening_beside_trace(board):
    opening = next(o for o in board["layers"]["top_coverlay_openings"] if o["kind"] == "sensor_electrode_opening")
    opening["x"] = round(opening["x"] + 1.1, 6)  # 0.0865 mm to the next column's 0.127 mm stub


def _shrink_gang_window(board):
    window = next(o for o in board["layers"]["top_coverlay_openings"] if o["kind"] == "connector_contact_opening")
    window["width_mm"] = round(window["width_mm"] - 0.3, 6)


def _shift_stiffener(board):
    stiffener = board["layers"]["bottom_stiffener"][0]
    stiffener["points"] = [[x - 0.5, y] for x, y in stiffener["points"]]


def _short_stiffener(board):
    stiffener = board["layers"]["bottom_stiffener"][0]
    top = max(y for _, y in stiffener["points"])
    stiffener["points"] = [[x, round(y - 1.0, 6) if y == top else y] for x, y in stiffener["points"]]


def _bow_tie(board):
    points = board["outline"]["points"]
    points[1], points[2] = points[2], points[1]


def _sharp_notch(board):
    # The old unfilleted tail-root corner of the Row board.
    tail = board["tail"]["bounds"]
    top, right = tail["y"] + tail["height"], tail["x"] + tail["width"]
    points = [p for p in board["outline"]["points"] if not (right - 1e-9 <= p[0] <= right + 0.6 and top - 0.6 <= p[1] <= top + 1e-9)]
    index = next(i for i, p in enumerate(points) if abs(p[0] - right) < 1e-9 and p[1] < top - 0.6) + 1
    points[index:index] = [[right, top], [right + 0.6, top]]
    board["outline"]["points"] = points


def _pinch_neck(board):
    board["tail"]["width_mm"] = board["tail"]["neck_bounds"]["width"] + 2.0


def _detach_route(board):
    route = board["layers"]["top_copper"]["routes"][3]
    route["points"][-1] = [route["points"][-1][0], route["points"][-1][1] - 0.15]


def _nc_route(board):
    # A route on an unused contact: NC contacts must touch nothing.
    pad = next(pad for pad in board["layers"]["top_copper"]["pads"] if pad["net"].startswith("NC_"))
    top = pad["y"] + pad["height_mm"] / 2
    board["layers"]["top_copper"]["routes"].append(
        {"net": pad["net"], "kind": "polyline", "segment": "tail", "width_mm": 0.254, "points": [[pad["x"], top], [pad["x"], top + 1.0]], "fanout": "stray"}
    )


def _wide_fanout(board):
    # COL_05's fan-out piece at the 0.254 mm finger width instead of the 0.127 mm bundle width.
    _fanout(board, "COL_05")["width_mm"] = 0.254


def _thin_electrode(board):
    board["layers"]["top_copper"]["electrodes"][2]["width_mm"] = 0.05


def _short_contact(board):
    board["layers"]["top_copper"]["pads"][0]["height_mm"] = 3.0


def _huge(board):
    board["outline"]["points"] = [[x * 8, y * 8] for x, y in board["outline"]["points"]]


def _off_grid(board):
    # Every Column electrode 0.1 mm sideways: spacing intact, grid off the taxel field.
    for electrode in board["layers"]["top_copper"]["electrodes"]:
        electrode["x"] = round(electrode["x"] + 0.1, 6)


SEPARATE_OPENINGS = {"matrix": {"taxel_width_mm": 1.3, "taxel_height_mm": 1.3}}
NC_CONTACTS = {"connector": {"row_pins": 14}}
# (target code, role whose builder is patched, defect, design, field of the target error)
CASES = (
    ("E_ROUTE_CLEARANCE", "rows", _shift_lane, {}, "boards.row.layers.top_copper.routes"),
    ("E_PAD_TRACE_CLEARANCE", "rows", _lead_toward_neighbor, {}, "boards.row.layers.top_copper.pads"),
    ("E_PAD_CLEARANCE", "rows", _squeeze_pad, {}, "boards.row.layers.top_copper.pads"),
    ("E_ELECTRODE_CLEARANCE", "columns", _widen_electrode, {}, "boards.column.layers.top_copper.electrodes"),
    ("E_ELECTRODE_ROUTE_CLEARANCE", "columns", _stub_toward_neighbor, {}, "boards.column.layers.top_copper.electrodes"),
    ("E_ELECTRODE_PAD_CLEARANCE", "columns", _pad_beside_electrode, {}, "boards.column.layers.top_copper.electrodes"),
    ("E_COPPER_EDGE_CLEARANCE", "columns", _contact_toward_tip, {}, "boards.column.outline.points"),
    ("E_ROUTE_EDGE_CLEARANCE", "rows", _lane_to_edge, {}, "boards.row.layers.top_copper.routes"),
    ("E_COPPER_OUTLINE", "columns", _pad_far_away, {}, "boards.column.outline.points"),
    ("E_COPPER_CUTOUT_CLEARANCE", "columns", _route_into_slot_margin, {}, "boards.column.outline.cutouts"),
    ("E_ACTIVE_MARGIN", "rows", _narrow_body, {}, "boards.row.outline.points"),
    ("E_COVERLAY_OUTLINE", "columns", _opening_out, {}, "boards.column.layers.top_coverlay_openings"),
    ("E_COVERLAY_BRIDGE", "rows", _split_opening, {}, "boards.row.layers.top_coverlay_openings"),
    ("E_COVERLAY_TRACE_CLEARANCE", "columns", _opening_beside_trace, SEPARATE_OPENINGS, "boards.column.layers.top_coverlay_openings"),
    ("E_CONTACT_EXPOSURE", "rows", _shrink_gang_window, {}, "boards.row.layers.top_coverlay_openings"),
    ("E_STIFFENER_OUTLINE", "columns", _shift_stiffener, {}, "boards.column.layers.bottom_stiffener"),
    ("E_STIFFENER_ZONE", "rows", _short_stiffener, {}, "boards.row.layers.bottom_stiffener"),
    ("E_OUTLINE_SELF_INTERSECTION", "rows", _bow_tie, {}, "boards.row.outline.points"),
    ("E_CUTOUT_OUTLINE", "columns", _slot_to_edge, {}, "boards.column.outline.cutouts"),
    ("E_CONCAVE_CORNER", "rows", _sharp_notch, {}, "boards.row.outline.points"),
    ("E_NECK_WIDTH", "columns", _pinch_neck, {}, "boards.column.outline.points"),
    ("E_CONNECTIVITY", "columns", _detach_route, {}, "boards.column.layers.top_copper.routes"),
    ("E_CONNECTIVITY", "rows", _nc_route, NC_CONTACTS, "boards.row.layers.top_copper.routes"),
    ("E_ROUTE_WIDTH", "columns", _wide_fanout, {}, "boards.column.layers.top_copper.routes"),
    ("E_ELECTRODE_WIDTH", "columns", _thin_electrode, {}, "boards.column.layers.top_copper.electrodes"),
    ("E_CONNECTOR_TAIL", "rows", _short_contact, {}, "boards.row.layers.top_copper.pads"),
    ("E_BOARD_SIZE", "rows", _huge, {}, "boards.row.outline.points"),
    ("E_REGISTRATION", "columns", _off_grid, {}, "boards.column.layers.top_copper.electrodes"),
)


@contextlib.contextmanager
def _defective(role: str, defect):
    """Patch one layout builder so that every board it returns carries ``defect``."""

    real = getattr(core, BUILDERS[role])

    def build(design, profile):
        board = real(design, profile)
        defect(board)
        return board

    with mock.patch.object(core, BUILDERS[role], build):
        yield


class DrcFailureFlowTests(unittest.TestCase):
    def test_every_drc_code_comes_out_of_generate_design(self) -> None:
        drc_codes = {code for code, (source, _) in ERROR_CODES.items() if "drc" in source}
        self.assertEqual({case[0] for case in CASES}, drc_codes, "add a case for each DRC-sourced code")
        for code, role, defect, design, field in CASES:
            with self.subTest(code=code, defect=defect.__name__):
                with _defective(role, defect):
                    result = generate_design(copy.deepcopy(design))
                errors = result["validation"]["errors"]
                self.assertFalse(result["ok"])
                self.assertIn((code, field), {(issue["code"], issue["field"]) for issue in errors})
                # Only the defect fails: every error is a whole-board DRC finding, none names a design field.
                self.assertTrue(all(issue["field"].startswith("boards.") for issue in errors), errors)
                # The failing geometry is still returned for inspection, with its records.
                self.assertEqual(set(result["boards"]), {"row", "column"})
                manifest = result["manifest"]
                self.assertFalse(manifest["geometry_valid"])
                self.assertEqual(manifest["checks"]["error_count"], len(errors))
                board = result["boards"][BOARD_KEYS[role]]
                verification = board["verification"]
                if code == "E_REGISTRATION":
                    self.assertFalse(verification["registration"]["passed"])
                else:
                    self.assertFalse(verification["all_checks_passed"])
                    failed = [record for record in verification["checks"].values() if not record["passed"]]
                    self.assertTrue(failed and all(record["violation_count"] > 0 for record in failed), failed)
                # The exporter refuses at its first gate, the result's own verdict.
                with self.assertRaisesRegex(ExportError, "design validation did not pass"):
                    build_exports(result)

    def test_a_drc_failure_blocks_http_exports_and_cli_exports(self) -> None:
        stderr = mock.patch("sys.stderr", io.StringIO())
        stderr.start()
        self.addCleanup(stderr.stop)
        with _defective("columns", _contact_toward_tip):
            server = app.AppServer(("127.0.0.1", 0))
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                generated = _post(port, "/api/generate", {})
                self.assertEqual(generated[0], 200)
                body = json.loads(generated[1])
                self.assertFalse(body["ok"])
                self.assertIn("E_COPPER_EDGE_CLEARANCE", {issue["code"] for issue in body["validation"]["errors"]})
                self.assertEqual(set(body["boards"]), {"row", "column"})
                # /api/validate runs the input rules and feasibility only: no geometry, so no DRC.
                self.assertTrue(json.loads(_post(port, "/api/validate", {})[1])["ok"])
                for route in ("top-gerber", "bottom-gerber", "project"):
                    status, data = _post(port, f"/api/export/{route}", body["design"])
                    reply = json.loads(data)
                    with self.subTest(route=route):
                        self.assertEqual((status, reply["ok"], reply["code"]), (422, False, "E_EXPORT_BLOCKED"))
                        self.assertIn("E_COPPER_EDGE_CLEARANCE", {issue["code"] for issue in reply["validation"]["errors"]})
                        self.assertFalse(reply["manifest"]["geometry_valid"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(5)
            with tempfile.TemporaryDirectory() as directory:
                design = Path(directory) / "design.json"
                design.write_text("{}", encoding="utf-8")
                code, generated = _cli("generate", "--compact", str(design))
                self.assertEqual((code, generated["ok"]), (1, False))
                self.assertIn("E_COPPER_EDGE_CLEARANCE", {issue["code"] for issue in generated["validation"]["errors"]})
                code, exported = _cli("export", "--out", str(Path(directory) / "out"), str(design))
                self.assertEqual((code, exported["ok"], exported["code"]), (1, False, "E_EXPORT_BLOCKED"))
                self.assertFalse((Path(directory) / "out").exists())


def _post(port: int, path: str, payload) -> tuple[int, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    try:
        connection.request("POST", path, body=json.dumps(payload), headers=JSON_HEADERS)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def _cli(*args: str) -> tuple[int, dict]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = cli.main(list(args))
    return code, json.loads(output.getvalue())


if __name__ == "__main__":
    unittest.main()
