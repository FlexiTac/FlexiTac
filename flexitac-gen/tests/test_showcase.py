"""The Library's showcase sensor: the original, hand-designed FlexiTac V2 pad (the user's request of 2026-11-12: the
original version at the top of the Library, hand-designed, not auto-generated).

- web/vendor/flexitac-v2/geometry.json (tools/flexitac_v2.py, from the official Gerbers): the pinned file; its
  invariants (12 sense and 32 drive lines at 2 mm on one origin, the slots between them, the A's window, the gold
  fingers at 0.5 mm, a trace from every electrode to a finger, the extents); the reader on small Gerbers of its own
  (flashes, strokes joined, regions; what it refuses); the rebuild from the ZIPs where FLEXITAC_V2_GERBERS names their
  folder; its notice (the licence the hardware repository states, the tutorial, the hashes).
- The two boards as the engine draws them (flexitac_v2.engine_boards, engine/core.py's SVG writer): which FPC is row
  and which column, which lies outward, one field on both.
- web/vendor/flexitac-v2/art.json.gz (tools/browser/flexitac_v2_art.py): a flexitac-library-art/v1 document of no
  build, of this geometry (the engine's SVG of each board is in it, element for element), in the Photo look as a
  generated sensor's, written deterministically (the file is library_write.art_bytes of its document).
- web/vendor/flexitac-v2/umi-finray.placed.json and web/cad/drape.js: the placed record (the face on the UMI finger,
  37 mm from the fingertip, the wrap), the wrap's checks (tools/browser/wrap_checks.js: the face its plane, no tear,
  where the tails land, the lift) run under node where there is one (tools/browser/showcase_checks.py runs the same
  text in Chromium), and what stays as it was: a generated sensor's stack is built with no mapper.
- docs/LIBRARY_VIEW.md names the placed record and the wrap, and the showcase's page (its document's format and keys,
  its pictures, the shots tool's --showcase); the Library's notice says what the showcase's drawn shapes are.  (The
  showcase's scene, document and page themselves: tests/test_library.py and tests/test_library_showcase.py.)
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
FOLDER = WEB / "vendor" / "flexitac-v2"
sys.path.append(str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import export_public  # noqa: E402
import flexitac_v2  # noqa: E402
import library_write  # noqa: E402
from engine import core  # noqa: E402

GEOMETRY = json.loads((FOLDER / "geometry.json").read_text(encoding="ascii"))
PLACED = json.loads((FOLDER / "umi-finray.placed.json").read_text(encoding="utf-8"))
ART_KEYS = ("role", "physical_side", "view_box", "region", "active_outline", "px", "front", "back")
HEADER = "%FSLAX45Y45*%\n%MOMM*%\n"
# A host's own path in a committed file (spelt in pieces: this file is read too).
HOST_PATH = re.compile("/" + "home/|/" + "Users/|/" + "tmp/")


def _layer(body: str) -> dict:
    return flexitac_v2.read_layer(HEADER + body + "M02*\n")


def _centres(boxes: list, axis: int) -> list:
    return sorted((box[axis] + box[axis + 2]) / 2 for box in boxes)


def _area(ring: list) -> float:
    return abs(math.fsum(ring[k][0] * ring[(k + 1) % len(ring)][1] - ring[(k + 1) % len(ring)][0] * ring[k][1] for k in range(len(ring)))) / 2


def _notice_rows() -> dict:
    rows = {}
    for line in (FOLDER / "NOTICE.md").read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("| `") and len(cells) == 5:
            rows[cells[0].strip("`")] = cells
    return rows


class GeometryTests(unittest.TestCase):
    def test_the_committed_geometry_is_the_pinned_one(self) -> None:
        self.assertEqual(flexitac_v2.check(), [])
        self.assertEqual(GEOMETRY["format"], flexitac_v2.FORMAT)
        self.assertEqual(GEOMETRY["units"], "mm")
        self.assertEqual({key: (item["file"], item["sha256"]) for key, item in GEOMETRY["source"].items()}, flexitac_v2.SOURCES)
        # Canonical: the file is the writer's text of its own document.
        self.assertEqual(flexitac_v2.geometry_text(GEOMETRY), (FOLDER / "geometry.json").read_text(encoding="ascii"))
        self.assertLessEqual((FOLDER / "geometry.json").stat().st_size, 20_000)

    def test_another_file_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "geometry.json"
            path.write_text(flexitac_v2.geometry_text(dict(GEOMETRY, name="another")), encoding="ascii")
            self.assertIn("not the pinned", flexitac_v2.check(path=path)[0])
            self.assertIn("missing", flexitac_v2.check(path=Path(folder) / "none.json")[0])
            # A folder without the ZIPs, or with other files under their names.
            self.assertIn("is not in the folder", flexitac_v2.check(Path(folder))[0])
            for name, _ in flexitac_v2.SOURCES.values():
                (Path(folder) / name).write_bytes(b"not the zip")
            self.assertIn("not the pinned", flexitac_v2.check(Path(folder))[0])

    @unittest.skipUnless(os.environ.get("FLEXITAC_V2_GERBERS"), "FLEXITAC_V2_GERBERS does not name the folder of the two Gerber ZIPs")
    def test_the_official_gerbers_give_the_committed_geometry(self) -> None:
        self.assertEqual(flexitac_v2.check(Path(os.environ["FLEXITAC_V2_GERBERS"])), [])

    def test_the_two_boards_lines_at_2_mm_on_one_origin(self) -> None:
        top, bottom = GEOMETRY["boards"]["top"], GEOMETRY["boards"]["bottom"]
        self.assertEqual((top["name"], top["role"], top["lines"]), ("Top FPC", "sense", 12))
        self.assertEqual((bottom["name"], bottom["role"], bottom["lines"]), ("Bottom FPC", "drive", 32))
        # 12 sense electrodes 0.6 x 63 mm along y at x = -11, -9, ... 11; 32 drive electrodes 23 x 0.6 mm at y = -31 ... 31
        # (hand-placed: within 0.1 um).
        self.assertEqual(len(top["electrodes"]), 12)
        self.assertEqual(len(bottom["electrodes"]), 32)
        for value, wanted in zip(_centres(top["electrodes"], 0), range(-11, 12, 2)):
            self.assertAlmostEqual(value, wanted, delta=1e-4)
        for value, wanted in zip(_centres(bottom["electrodes"], 1), range(-31, 32, 2)):
            self.assertAlmostEqual(value, wanted, delta=1e-4)
        for x0, y0, x1, y1 in top["electrodes"]:
            self.assertAlmostEqual(x1 - x0, 0.6, delta=1e-9)
            self.assertEqual((y0, y1), (-31.5, 31.5))
        for x0, y0, x1, y1 in bottom["electrodes"]:
            self.assertAlmostEqual(y1 - y0, 0.6, delta=1e-9)
            self.assertEqual((x0, x1), (-11.5, 11.5))
        self.assertEqual(flexitac_v2.PITCH_MM, 2.0)
        # One field on both: the electrodes' box, 23 x 63 mm about the origin.
        self.assertEqual(flexitac_v2.field(GEOMETRY), {"x": -11.5, "y": -31.5, "width": 23.0, "height": 63.0})

    def test_the_extents_are_the_gerbers(self) -> None:
        def box(points):
            return (min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points))

        top, bottom = GEOMETRY["boards"]["top"], GEOMETRY["boards"]["bottom"]
        self.assertEqual(box(top["outline"]), (-69.66862, -43.815, 11.87338, 32.2))
        self.assertEqual(box(bottom["outline"]), (-12.2, -34.0, 70.0, 32.004))
        self.assertEqual((len(top["outline"]), len(bottom["outline"])), (10, 12))
        self.assertAlmostEqual(_area(top["outline"]), 2142.75, delta=0.01)
        self.assertAlmostEqual(_area(bottom["outline"]), 3709.39, delta=0.01)
        # The tails: the Top FPC's 57.5 mm strip to -x ending in its 6.5 mm tab; the Bottom FPC's A to +x, its foot 16.5 mm.
        self.assertAlmostEqual(-12.12662 - box(top["outline"])[0], 57.542, delta=1e-6)
        self.assertEqual(box(bottom["outline"])[2] - 53.5, 16.5)

    def test_the_slots_and_the_window_are_the_cut_outs(self) -> None:
        top, bottom = GEOMETRY["boards"]["top"], GEOMETRY["boards"]["bottom"]
        # 22 slots 1 x 31 mm between the sense electrodes, in two rows either side of the supporting beam.
        self.assertEqual(len(top["slots"]), 22)
        self.assertEqual(top["windows"], [])
        for x0, y0, x1, y1 in top["slots"]:
            self.assertAlmostEqual(x1 - x0, 1.0, delta=2e-5)  # drawn by hand: 1.00001 mm in places
            self.assertAlmostEqual(y1 - y0, 31.0, delta=2e-5)
            self.assertAlmostEqual(((x0 + x1) / 2) % 2, 0, delta=1e-3)  # midway between two electrodes
        self.assertEqual(sorted({round(box[1], 4) for box in top["slots"]}), [-31.395, 0.4766])
        # 31 slots 23 x 1 mm between the drive electrodes, and the window of the A (5 corners, 688 mm2).
        self.assertEqual(len(bottom["slots"]), 31)
        for (x0, y0, x1, y1), wanted in zip(sorted(bottom["slots"], key=lambda box: box[1]), range(-30, 31, 2)):
            self.assertEqual((x0, x1), (-11.5, 11.5))
            self.assertAlmostEqual(y1 - y0, 1.0, delta=2e-5)
            self.assertAlmostEqual((y0 + y1) / 2, wanted, delta=1e-4)
        self.assertEqual(len(bottom["windows"]), 1)
        self.assertEqual(len(bottom["windows"][0]), 5)
        self.assertAlmostEqual(_area(bottom["windows"][0]), 688.38, delta=0.01)
        # Every cut-out lies inside its outline's box and off every electrode.
        for board in (top, bottom):
            xs = [p[0] for p in board["outline"]]
            ys = [p[1] for p in board["outline"]]
            for x0, y0, x1, y1 in board["slots"]:
                self.assertTrue(min(xs) < x0 < x1 < max(xs) and min(ys) < y0 < y1 < max(ys))
                for ex0, ey0, ex1, ey1 in board["electrodes"]:
                    self.assertTrue(x1 <= ex0 or ex1 <= x0 or y1 <= ey0 or ey1 <= y0)

    def test_the_gold_fingers_and_a_trace_from_every_electrode(self) -> None:
        for key, lines, tongue in (("top", 12, 6.5), ("bottom", 32, 16.5)):
            board = GEOMETRY["boards"][key]
            with self.subTest(board=key):
                fingers = board["fingers"]
                self.assertEqual(len(fingers), lines)
                centres = _centres(fingers, 0)
                for a, b in zip(centres, centres[1:]):
                    self.assertAlmostEqual(b - a, flexitac_v2.FINGER_PITCH_MM, delta=2e-4)
                for x0, y0, x1, y1 in fingers:
                    self.assertAlmostEqual(x1 - x0, 0.3, delta=1e-9)
                    self.assertAlmostEqual(y1 - y0, 3.0, delta=1e-4)
                # A 0.5 mm FFC tongue: (lines + 1) pitches wide.
                self.assertEqual(tongue, (lines + 1) * flexitac_v2.FINGER_PITCH_MM)
                self.assertEqual(board["trace_width"], 0.254)
                self.assertEqual(len(board["traces"]), lines)
                starts, ends = set(), set()
                for trace in board["traces"]:
                    start = [k for k, (x0, y0, x1, y1) in enumerate(board["electrodes"]) if x0 <= trace[0][0] <= x1 and y0 <= trace[0][1] <= y1]
                    end = [k for k, (x0, y0, x1, y1) in enumerate(fingers) if x0 <= trace[-1][0] <= x1 and y0 <= trace[-1][1] <= y1]
                    self.assertEqual((len(start), len(end)), (1, 1))
                    starts.add(start[0])
                    ends.add(end[0])
                self.assertEqual((len(starts), len(ends)), (lines, lines), "one trace for each electrode and each finger")

    def test_the_coverlay_and_the_stiffeners(self) -> None:
        top, bottom = GEOMETRY["boards"]["top"], GEOMETRY["boards"]["bottom"]
        # The coverlay is open over the whole field and the tongue, and round every pad.
        self.assertEqual(top["openings"][:2], [[-69.66862, -43.815, -63.16862, -41.1928], [-11.811, -31.623, 11.557, 31.75]])
        self.assertEqual((len(top["openings"]), len(bottom["openings"])), (2 + 24, 3 + 64))
        for board in (top, bottom):
            for x0, y0, x1, y1 in board["electrodes"] + board["fingers"]:
                self.assertTrue(any(ox0 <= x0 and oy0 <= y0 and x1 <= ox1 and y1 <= oy1 for ox0, oy0, ox1, oy1 in board["openings"]))
        self.assertEqual([item["thickness"] for item in top["stiffeners"]], [0.1, 0.1, 0.2, 0.2])
        self.assertEqual([item["thickness"] for item in bottom["stiffeners"]], [0.1, 0.1, 0.1, 0.1, 0.2, 0.2])
        # 0.2 mm under each gold end.
        for board in (top, bottom):
            thick = [item["points"] for item in board["stiffeners"] if item["thickness"] == 0.2]
            for x0, y0, x1, y1 in board["fingers"]:
                self.assertTrue(any(min(p[0] for p in ring) <= x0 and x1 <= max(p[0] for p in ring) and min(p[1] for p in ring) <= y0
                                    and y1 <= max(p[1] for p in ring) for ring in thick))


class ReaderTests(unittest.TestCase):
    def test_flashes_strokes_and_regions(self) -> None:
        layer = _layer("%ADD10C,0.254*%\n%ADD11R,0.3X2.99999*%\nG54D11*\nG01X100000Y-200000D03*\nG54D10*\nG01X0Y0D02*\nG01X100000Y0D01*\n"
                       "G01X100000Y50000D01*\nG36*\nG01X0Y0D02*\nG01X0Y100000D01*\nG01X100000Y100000D01*\nG01X0Y0D01*\nG37*\n")
        self.assertEqual(layer["apertures"], {10: ("C", (254000,)), 11: ("R", (300000, 2999990))})
        self.assertEqual(layer["flashes"], [(11, (1000000, -2000000))])
        self.assertEqual(layer["strokes"], [(10, [(0, 0), (1000000, 0), (1000000, 500000)])])
        self.assertEqual(layer["regions"], [[(0, 0), (0, 1000000), (1000000, 1000000), (0, 0)]])
        # A rectangle flashed: to 1e-6 mm (half of 2.99999 mm is 1.499995).
        self.assertEqual(flexitac_v2._flashed(layer["apertures"][11], (1000000, -2000000)), (850000, -3499995, 1150000, -500005))
        # EasyEDA's rounded rectangle: the corner circles' diameter round the rectangle through their centres.
        self.assertEqual(flexitac_v2._flashed(("RoundRect", (102010, -150000, 1500000, 150000, 1500000)), (0, 0)), (-201005, -1551005, 201005, 1551005))

    def test_strokes_are_joined_where_they_meet(self) -> None:
        # Within 0.01 mm one point (the join keeps the first piece's); a ring closes on itself.
        ring = flexitac_v2._joined([[(0, 0), (0, 10_000_000), (5_000_000, 10_000_000)], [(5_000_000, 10_004_000), (5_000_000, 0), (0, 0)]])
        self.assertEqual(ring, [[(0, 0), (0, 10_000_000), (5_000_000, 10_000_000), (5_000_000, 0), (0, 0)]])
        # Farther apart, two pieces; within a trace's half width, one trace with both points.
        pieces = [[(0, 0), (1_000_000, 0)], [(1_000_000, 127_000), (2_000_000, 127_000)]]
        self.assertEqual(len(flexitac_v2._joined(pieces)), 2)
        self.assertEqual(flexitac_v2._joined(pieces, 127_000), [[(0, 0), (1_000_000, 0), (1_000_000, 127_000), (2_000_000, 127_000)]])
        self.assertEqual(flexitac_v2._ring([(0, 0), (2, 0), (4, 0), (4, 3), (0, 3), (0, 0)]), [(0, 0), (4, 0), (4, 3), (0, 3)])
        self.assertEqual(flexitac_v2._ring([(0, 3), (4, 3), (4, 0), (0, 0)]), [(0, 0), (4, 0), (4, 3), (0, 3)], "counter-clockwise from its least point")

    def test_what_these_gerbers_do_not_use_is_refused(self) -> None:
        for body, word in (("%FSLAX26Y26*%\n", "number format"), ("%MOIN*%\n", "unit"), ("%LPC*%\n", "polarity"),
                           ("%ADD10C,0.1*%\nG54D10*\nG01X0Y0D02*\nG02X10Y10I5J5D01*\n", "arcs")):
            with self.subTest(body=body):
                with self.assertRaises(flexitac_v2.GeometryError) as raised:
                    _layer(body)
                self.assertIn(word, str(raised.exception))

    def test_the_tool_is_public_stdlib_and_python_3_9(self) -> None:
        self.assertIn("tools/flexitac_v2.py", export_public.PUBLIC)
        allowed = {"__future__", "argparse", "hashlib", "io", "json", "re", "sys", "zipfile", "decimal", "pathlib"}
        for path in (ROOT / "tools" / "flexitac_v2.py", ROOT / "tools" / "browser" / "flexitac_v2_art.py", ROOT / "tools" / "browser" / "showcase_checks.py",
                     Path(__file__)):
            with self.subTest(file=path.name):
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(path), feature_version=(3, 9))
                self.assertIn("from __future__ import annotations", source)
                # No host path in a committed file.
                self.assertIsNone(HOST_PATH.search(source.replace("/tmp/fpc-browser-venv", "").replace("/tmp/art.json.gz", "").replace("/tmp/showcase", "")))
                if path.name == "flexitac_v2.py":
                    imported = {(node.module or "").split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
                                for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                                for alias in (node.names if isinstance(node, ast.Import) else [None])}
                    self.assertLessEqual(imported, allowed)
                    self.assertNotRegex(source, r"(?<![.\w])sum\(")


class NoticeTests(unittest.TestCase):
    def test_the_notice_states_the_design_its_licence_and_its_source(self) -> None:
        text = " ".join((FOLDER / "NOTICE.md").read_text(encoding="utf-8").split())
        for words in ("Binghao Huang and Yunzhu Li", "Columbia University", "https://github.com/FlexiTac/FlexiTac",
                      "FlexiTac © 2026 by Columbia University is licensed under CC BY-NC 4.0",
                      "https://creativecommons.org/licenses/by-nc/4.0/", "not** under this repository's Apache-2.0 licence",
                      "https://docs.google.com/document/d/1bvz6AL7BUkhj4Dj7n9DFXTjnGIX4-ziN8-smiCKpVZU/", "hand-designed",
                      "The ZIPs themselves are not in this repository"):
            with self.subTest(words=words):
                self.assertIn(words, text)
        for name, digest in flexitac_v2.SOURCES.values():
            self.assertIn(f"`{name}` (SHA-256 `{digest}`)", text)
        self.assertIsNone(HOST_PATH.search(text))
        self.assertNotRegex(text, r"\bCAD\b")

    def test_each_file_is_tabled_with_its_hash_or_the_projects_own(self) -> None:
        rows = _notice_rows()
        self.assertEqual(sorted(rows), ["art.json.gz", "geometry.json"])
        for name, cells in rows.items():
            with self.subTest(file=name):
                self.assertEqual(cells[4].strip("`"), hashlib.sha256((FOLDER / name).read_bytes()).hexdigest())
                self.assertIn("CC BY-NC 4.0, Columbia University", cells[2])
                self.assertTrue(cells[3].startswith("modified:"))
        # The folder holds these, the notice and the project's own placed record (named in the notice), and no Gerber.
        self.assertEqual(sorted(path.name for path in FOLDER.iterdir()), ["NOTICE.md", "art.json.gz", "geometry.json", "umi-finray.placed.json"])
        self.assertIn("`umi-finray.placed.json` is this project's own", " ".join((FOLDER / "NOTICE.md").read_text(encoding="utf-8").split()))
        self.assertTrue(any("web/vendor/flexitac-v2".startswith(root) or root == "web" for root in export_public.PUBLIC))

    def test_the_readme_s_licence_section_names_the_folder_and_its_licence(self) -> None:
        # The folder is published with web/ (the site build, the public export) and is the only vendored material that is
        # not free for commercial use: the README's licence summary says so beside the other vendored folders.
        section = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split("\n## License\n", 1)[1].split())
        self.assertIn("three.js (MIT), the UMI finger (Apache-2.0) and the US Mint photo of the quarter (public domain)", section)
        self.assertRegex(section, r"`web/vendor/flexitac-v2/`[^.]*CC BY-NC 4.0[^.]*Columbia University[^.]*non-commercial[^.]*not Apache-2\.0")
        self.assertIn("(web/vendor/flexitac-v2/NOTICE.md)", section)


class EngineBoardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.boards = flexitac_v2.engine_boards(GEOMETRY)

    def test_which_fpc_is_which_board(self) -> None:
        # As the real pad lies on the finger: the Top FPC (12 lines along the finger) under the film, its copper outward;
        # the Bottom FPC (32 lines across it) the outer layer, turned over.
        row, column = self.boards["row"], self.boards["column"]
        self.assertEqual((row["id"], row["role"], row["physical_side"]), ("flexitac-v2-bottom", "rows", "top"))
        self.assertEqual((column["id"], column["role"], column["physical_side"]), ("flexitac-v2-top", "columns", "bottom"))
        self.assertEqual((len(row["layers"]["top_copper"]["electrodes"]), len(column["layers"]["top_copper"]["electrodes"])), (32, 12))
        self.assertEqual((len(row["outline"]["cutouts"]), len(column["outline"]["cutouts"])), (31 + 1, 22))
        self.assertEqual(row["outline"]["cutouts"][-1], GEOMETRY["boards"]["bottom"]["windows"][0])
        region = {"x": -11.5, "y": -31.5, "width": 23.0, "height": 63.0}
        self.assertEqual((row["grid_registration"]["active_region"], column["grid_registration"]["active_region"]), (region, region))
        # Of the stiffeners only the 0.2 mm ones under the gold ends are drawn (two rectangles each): the 0.1 mm ones, the
        # strip under the Top FPC's traces below the field and the patches at the A's corners, would be painted as a
        # connector's opaque stiffener, where the real pad is amber.  geometry.json keeps them all.
        for key, source in (("row", "bottom"), ("column", "top")):
            drawn = self.boards[key]["layers"]["bottom_stiffener"]
            self.assertEqual([item["thickness_mm"] for item in drawn], [0.2, 0.2])
            self.assertEqual([item["points"] for item in drawn], [item["points"] for item in GEOMETRY["boards"][source]["stiffeners"] if item["thickness"] == 0.2])
            self.assertEqual(len(GEOMETRY["boards"][source]["stiffeners"]) - len(drawn), {"bottom": 4, "top": 2}[source])
            region = self.boards[key]["grid_registration"]["active_region"]
            for item in drawn:
                xs, ys = [point[0] for point in item["points"]], [point[1] for point in item["points"]]
                self.assertTrue(min(xs) > region["x"] + region["width"] + 20 or max(xs) < region["x"] - 20, "far from the field")
                self.assertLess(max(ys), region["y"] + 5)
        # No pin is numbered: the engine draws no pin-1 marker.
        for board in self.boards.values():
            self.assertFalse(any("pin" in pad for pad in board["layers"]["top_copper"]["pads"]))

    def test_the_engine_draws_them_as_a_generated_board(self) -> None:
        for key, lines, slots in (("row", 32, 32), ("column", 12, 22)):
            with self.subTest(board=key):
                svg = core._svg_for_board(self.boards[key])
                self.assertEqual(svg.count('class="electrode"'), lines)
                self.assertEqual(svg.count('class="pad"'), lines)
                self.assertEqual(svg.count('class="route"'), lines)
                self.assertEqual(svg.count('class="cutout"'), slots)
                self.assertEqual(svg.count('class="outline"'), 1)
                self.assertEqual(svg.count('class="stiffener"'), len(self.boards[key]["layers"]["bottom_stiffener"]))
                self.assertNotIn("pin1-marker\"", svg.split("</style>")[1])
                self.assertIn('stroke-width="0.254"', svg)
                # The field after the SVG's Y flip: the same 23 x 63 mm, x from -11.5.
                found = re.search(r'data-active-region="([^"]+)"', svg)
                x, _, width, height = [float(value) for value in found.group(1).split()]
                self.assertEqual((x, width, height), (-11.5, 23.0, 63.0))


class ArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = (FOLDER / "art.json.gz").read_bytes()
        cls.art = library_write.read_art(cls.data)
        cls.boards = flexitac_v2.engine_boards(GEOMETRY)

    def test_it_is_an_art_document_of_no_build_in_the_photo_look(self) -> None:
        art = self.art
        self.assertEqual(sorted(art), ["boards", "build_id", "format", "id", "look", "max_px", "px_per_mm"])
        self.assertEqual((art["format"], art["id"], art["build_id"], art["look"], art["px_per_mm"], art["max_px"]),
                         (library_write.ART_FORMAT, "flexitac-v2", None, "photo", library_write.ART_PX_PER_MM, library_write.ART_MAX_PX))
        self.assertEqual(sorted(art["boards"]), ["column", "row"])
        for key, board in art["boards"].items():
            with self.subTest(board=key):
                self.assertEqual(sorted(board), sorted(ART_KEYS + ("outline",)))
                self.assertEqual((board["role"], board["physical_side"]), (self.boards[key]["role"], self.boards[key]["physical_side"]))
                self.assertEqual(board["outline"], {"points": self.boards[key]["outline"]["points"], "cutouts": self.boards[key]["outline"]["cutouts"]})
                self.assertEqual(board["region"][0], -11.5)
                self.assertEqual(board["region"][2:], [23, 63])
                self.assertIsNone(board["active_outline"])
                # 12 px per mm of its view box.
                self.assertEqual(board["px"], [round(board["view_box"][2] * 12), round(board["view_box"][3] * 12)])

    def test_it_is_written_deterministically(self) -> None:
        # The file is the canonical JSON of its document, gzip with no name and time 0.
        self.assertEqual(library_write.art_bytes(self.art), self.data)
        self.assertEqual(self.data[:8], b"\x1f\x8b\x08\x00\x00\x00\x00\x00")
        # The header's OS byte is 3 on every Python (before 3.11 gzip.compress writes 255 there).
        self.assertEqual(self.data[9], 3)
        self.assertLessEqual(len(self.data), 20_000)

    def test_it_is_the_engine_s_drawing_of_this_geometry_in_the_generator_s_look(self) -> None:
        generated = library_write.read_art((WEB / "library" / "art" / "umi-finray-2mm.json.gz").read_bytes())
        for key in ("row", "column"):
            with self.subTest(board=key):
                svg = core._svg_for_board(self.boards[key])
                front, back = self.art["boards"][key]["front"], self.art["boards"][key]["back"]
                # Every element the engine draws is in the copper side's document, as the engine wrote it.
                group = svg.split('<g transform="', 1)[1].split('">', 1)[1].rsplit("</g>", 1)[0]
                elements = re.findall(r"<(?:polygon|rect|polyline)[^>]*/>", group)
                self.assertGreater(len(elements), 80)
                for element in elements:
                    self.assertIn(element, front)
                view_box = re.search(r'viewBox="([^"]+)"', svg).group(1)
                self.assertIn(f'viewBox="{view_box}"', front)
                self.assertIn(f'viewBox="{view_box}"', back)
                # The same styles as a generated sensor's art: the engine's own and the page's Photo look, text for text.
                def styles(document):
                    return re.findall(r"<style>(.*?)</style>", document, re.S)
                self.assertEqual(styles(front), styles(generated["boards"][key]["front"]))
                self.assertEqual(styles(back), styles(generated["boards"][key]["back"]))
                for layer in ("lk-gap", "lk-edge", "lk-stiff", "lk-gold", "lk-grain"):
                    self.assertIn(f'class="lk {layer}"', front)
                self.assertIn('class="board-back"', back)
                self.assertNotIn("view-label", front.split("</style>")[-1])


def _stl_positions(path: Path) -> list:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    return [struct.unpack_from("<3f", data, 84 + 50 * k + 12 + 12 * corner) for k in range(count) for corner in range(3)]


class PlacedTests(unittest.TestCase):
    def test_the_record_places_the_pad_on_the_umi_finger_as_the_real_one_is_mounted(self) -> None:
        drape = (WEB / "cad" / "drape.js").read_text(encoding="utf-8")
        self.assertEqual(PLACED["format"], re.search(r'export const PLACED_FORMAT = "([^"]+)";', drape).group(1))
        self.assertEqual(sorted(PLACED), ["about", "art", "face", "format", "frame", "id", "mesh", "scene", "sensor", "wrap"])
        mesh = (WEB / "library" / PLACED["mesh"]["file"]).resolve()
        self.assertEqual(mesh, WEB / "vendor" / "umi" / "UMI-Soft-Gripper-Finger.stl")
        self.assertEqual(PLACED["mesh"]["sha256"], hashlib.sha256(mesh.read_bytes()).hexdigest())
        self.assertEqual(PLACED["mesh"]["unit"], "mm")
        self.assertEqual((WEB / "library" / PLACED["art"]).resolve(), FOLDER / "art.json.gz")
        self.assertEqual(PLACED["sensor"], library_write.read_art((FOLDER / "art.json.gz").read_bytes())["id"])
        self.assertIsNone(PLACED["scene"])
        self.assertEqual(PLACED["wrap"], {"side": "left", "radius_mm": 2})
        # The face: unit axes at right angles; its plane the finger's outermost along its normal; the origin in the middle
        # of the finger's width, 37 mm from the fingertip (the finger's end along y).
        origin, x, y = PLACED["face"]["origin"], PLACED["face"]["x"], PLACED["face"]["y"]
        normal = [x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0]]
        self.assertEqual((math.hypot(*x), math.hypot(*y), math.fsum(a * b for a, b in zip(x, y))), (1.0, 1.0, 0.0))
        points = [[c - o for c, o in zip(point, origin)] for point in _stl_positions(mesh)]
        along = lambda axis: [math.fsum(a * b for a, b in zip(point, axis)) for point in points]  # noqa: E731
        self.assertAlmostEqual(max(along(normal)), 0.0, delta=1e-6)
        self.assertAlmostEqual(max(along(y)), 37.0, delta=1e-5)
        self.assertAlmostEqual(max(along(x)), 12.9, delta=1e-5)
        self.assertAlmostEqual(min(along(x)), -12.9, delta=1e-5)
        # The pad's field and both boards' bodies lie on the flat of the face (it runs from 1 to 120 mm from the tip).
        top = GEOMETRY["boards"]["top"]["outline"]
        self.assertLess(max(point[1] for point in top), 37 - 1)
        self.assertGreater(min(point[1] for point in top), 37 - 120)

    def test_a_generated_sensor_s_stack_takes_no_mapper(self) -> None:
        # The stack builder's mapper argument is the placed stack's alone: Gen by Surface and a sensor of entries.json
        # call it without one, so their drawings are the ones they were.
        drape = (WEB / "cad" / "drape.js").read_text(encoding="utf-8")
        self.assertIn("export function buildStack({selection, vertices, placement, arts, boards, partBox, mapper: placedMapper = null}) {", drape)
        self.assertIn("const mapper = frame && (placedMapper || chartMapper(selection, vertices));", drape)
        self.assertEqual(drape.count("placedMapper"), 5)
        self.assertEqual(len(re.findall(r"buildStack\(\{[^}]*mapper", drape)), 2, "its own signature, and placedStack's call alone gives one")
        main = (WEB / "cad" / "main.js").read_text(encoding="utf-8")
        view = (WEB / "cad" / "library_view.js").read_text(encoding="utf-8")
        self.assertNotRegex(main, r"mapper:|placedStack|wrapMapper|liftedNormals|film_seen")
        self.assertEqual(len(re.findall(r"\bbuildStack\(", main)), 1)
        self.assertIn("placed ? placedStack({placed, ...laid}) : buildStack({selection: fit.reply.selection, placement: proposal.placement, ...laid})", view)
        # What the figure and the stage do for a placed stack hangs on keys only a placed stack has.
        onpart = (WEB / "cad" / "onpart.js").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"liftedNormals", onpart)), 10)
        # An exploded placed sheet's edge band stands across its own normals there (bandOf's lifted), a generated
        # sheet's and every assembled one across the sheet's normals as before.
        self.assertIn("  const lifted = sheet.liftedNormals ? new Float32Array(3 * m) : null;\n", onpart)
        self.assertIn('  const top = band.surface[mode]; const n = mode !== "assembled" && band.lifted ? band.lifted : band.normals;\n', onpart)
        self.assertEqual(onpart.count("band.lifted"), 2)
        self.assertEqual(len(re.findall(r"film_seen", onpart)), 2)
        self.assertIn('    if (film) film.children[0].visible = view.mode !== "assembled";\n', onpart)
        stage = (WEB / "cad" / "library_stage.js").read_text(encoding="utf-8")
        self.assertIn("      if (stack.respace) stack.respace(step);\n      else for (const name of LAYERS) {", stage)
        self.assertIn("hidden: still && film && !stack.film_seen};", stage)
        self.assertEqual((stage.count("stack.respace"), stage.count("film_seen")), (2, 2))
        self.assertIn('import {buildStack} from "./drape.js";\nimport {placedStack} from "./drape.js";\n', view)
        # A placed record's mesh unit is one the page knows, or the record is refused (a fit's is the server's own).
        self.assertIn("    const scale = UNIT_SCALES_MM[placed ? placed.mesh.unit : fit.reply.mesh.unit];\n", view)
        self.assertIn("    if (placed && !(scale > 0)) throw new Error(`the placed record's mesh unit ", view)
        self.assertIn(json.loads((FOLDER / "umi-finray.placed.json").read_text(encoding="utf-8"))["mesh"]["unit"],
                      re.search(r"(?m)^const UNIT_SCALES_MM = \{([^}]*)\};$", view).group(1).replace(":", " ").split())

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_the_wrap_on_the_finger(self) -> None:
        driver = (
            'import * as D from "./drape.mjs";\nimport {parseStl} from "./stl.mjs";\nimport {readFileSync} from "node:fs";\n'
            'import {gunzipSync} from "node:zlib";\n'
            + (ROOT / "tools" / "browser" / "wrap_checks.js").read_text(encoding="utf-8")
            + "const [mesh, placed, art] = process.argv.slice(2);\nconst bytes = readFileSync(mesh);\n"
            "const positions = parseStl(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)).positions;\n"
            'console.log(JSON.stringify(wrapChecks(D, positions, JSON.parse(readFileSync(placed, "utf8")), JSON.parse(gunzipSync(readFileSync(art)).toString("utf8")))));\n'
        )
        with tempfile.TemporaryDirectory() as folder:
            source = (WEB / "cad" / "drape.js").read_text(encoding="utf-8")
            self.assertIn('from "./border.js";', source)
            (Path(folder) / "drape.mjs").write_text(source.replace('from "./border.js";', 'from "./border.mjs";'), encoding="utf-8")
            shutil.copy(WEB / "cad" / "border.js", Path(folder) / "border.mjs")
            shutil.copy(WEB / "cad" / "stl.js", Path(folder) / "stl.mjs")
            (Path(folder) / "driver.mjs").write_text(driver, encoding="utf-8")
            run = subprocess.run(["node", "driver.mjs", str(WEB / "vendor" / "umi" / "UMI-Soft-Gripper-Finger.stl"), str(FOLDER / "umi-finray.placed.json"),
                                  str(FOLDER / "art.json.gz")], cwd=folder, capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = json.loads(run.stdout)
        self.assertEqual(out["problems"], [])
        # The face is its plane to the last bit; nothing tears; a level line and the roll up to the fold line keep their
        # lengths (a 0.02 mm step's chord over the 2 mm turns is 4.2e-6 short).
        self.assertEqual(out["face_error_mm"], 0)
        self.assertLess(out["stretch"], 1.5)
        self.assertLess(out["level"], 1e-5)
        self.assertLess(out["rigid"], 1e-5)
        # The exploded sheets' normals are the lifted sheet's own (5.4 degrees off at most, at a turn's start), and on a
        # part thinner than the bend the two quarter turns are one half turn without a tear.
        self.assertLess(out["lean_deg"], 15)
        self.assertLess(out["thin_level"], 1e-5)
        self.assertGreater(out["steps"], 100_000)
        self.assertAlmostEqual(out["edge_mm"], 12.9, delta=1e-5)
        self.assertAlmostEqual(out["width_mm"], 25.8, delta=1e-5)
        self.assertAlmostEqual(out["tip_mm"], 37.0, delta=1e-5)
        # The straps cross the side face; both gold ends lie behind the finger above its base.
        self.assertEqual(out["straps"], {"upper_arm": True, "lower_arm": True, "top_tail": True})
        row, column = out["landing"]["row"], out["landing"]["column"]
        self.assertTrue(row["end_behind"] and column["end_behind"])
        self.assertTrue(66 <= row["end_tip_mm"][0] and row["end_tip_mm"][1] <= 71.1, row)
        self.assertTrue(70 <= column["end_tip_mm"][0] and column["end_tip_mm"][1] <= 81, column)
        # The stack: exploded by the lift over the finger's width, the Bottom FPC outermost, the film seen through the slots.
        stack = out["stack"]
        self.assertEqual((stack["explode"], stack["film_seen"], stack["bottom"], stack["top"]), ("lift", True, "column", "row"))
        self.assertAlmostEqual(stack["gap_mm"], 0.55 * 25.8, delta=1e-5)
        self.assertEqual(stack["nest_mm"], 0.25)


class DocumentTests(unittest.TestCase):
    def test_the_view_s_document_names_the_placed_record_and_the_wrap(self) -> None:
        text = " ".join((ROOT / "docs" / "LIBRARY_VIEW.md").read_text(encoding="utf-8").split())
        for words in ("## A placed sensor", "flexitac-library-placed/v1", "`wrapMapper(placed, vertices)`", "`placedStack({placed, vertices, arts, boards, partBox})`", "`lifted(h)`", "`respace(step)`",
                      "show({base, id, placed, mode})", "vendor/flexitac-v2/umi-finray.placed.json", "tools/browser/showcase_checks.py",
                      "tools/browser/flexitac_v2_art.py", "`film_seen`", "`liftedNormals`", '"build_id": null'):
            with self.subTest(words=words):
                self.assertIn(words, text)
        self.assertIsNone(HOST_PATH.search(text))
        for document in (ROOT / "tools" / "README.md", ROOT / "tools" / "browser" / "README.md"):
            with self.subTest(document=document.name):
                self.assertIn("flexitac_v2", document.read_text(encoding="utf-8"))
        self.assertIn("`showcase_checks.py`", (ROOT / "tools" / "browser" / "README.md").read_text(encoding="utf-8"))

    def test_the_view_s_document_names_the_showcase_s_page(self) -> None:
        # The showcase's page (2026-11-12): its document's format and every key, its pictures, the shots tool's mode and
        # the writer's check are in the normative document; the tools' documents name the mode and the page's check.
        text = " ".join((ROOT / "docs" / "LIBRARY_VIEW.md").read_text(encoding="utf-8").split())
        for words in ("## The showcase's page", library_write.SHOWCASE_FORMAT, "`library/showcase.json`", "library_shots.py --showcase",
                      "`showcase_page(parts, library)`", "library.html#flexitac-g1", "Original FlexiTac · Hand-designed, pre-agent", "1280 x 1600", "800 x 1000",
                      "The part is the gripper's left finger", "Its camera is its own", "No finger is see-through", "`library/bodies/flexitac-g1/drawn-<name>.stl`",
                      *(f"`{key}`" for key in library_write.SHOWCASE_KEYS if key not in ("format", "title", "label", "text")), "`title`, `label`, `text`"):
            with self.subTest(words=words):
                self.assertIn(words, text)
        for key in library_write.SHOWCASE_SHOT_KEYS:
            with self.subTest(shot=key):
                self.assertIn(f"`{key}`", text)
        browser = (ROOT / "tools" / "browser" / "README.md").read_text(encoding="utf-8")
        self.assertIn("library_shots.py --showcase", browser)
        self.assertIn("`part_page`", browser)
        self.assertIn("library_shots.py --showcase", (ROOT / "tools" / "README.md").read_text(encoding="utf-8"))
        # The Library's notice says what the showcase's drawn shapes and pictures are, and links both notices.
        notice = " ".join((ROOT / "web" / "library" / "NOTICE.md").read_text(encoding="utf-8").split())
        for words in ("drawn-shell-screw.stl", "drawn-cable-stub.stl", "neither UFACTORY's nor HandUMI's geometry", "(../vendor/ufactory-g1/NOTICE.md)",
                      "(../vendor/flexitac-v2/NOTICE.md)", "`showcase.json`"):
            with self.subTest(notice=words):
                self.assertIn(words, notice)


if __name__ == "__main__":
    unittest.main()
