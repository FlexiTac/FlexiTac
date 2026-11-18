"""The FlexiTac hardware's own order files in the site (the user's request of 2026-11-17: "把instruction里面的fpc gerber也
都放到这边可以直接download；另外 所有的card加上一条：ordering and fabrication：放上instruction link；reading board download ...
小于32x16的sensor用32x16的board，小于32x32大于16的，用32x32的board"; his answers to the plan: "copy into site, reading board可以
打包成一个zip：gerber，bom，pick and place", "tail C", "gen也加入reading board").

- tools/flexitac_downloads.py: the original pad's two FPC Gerber ZIPs in web/vendor/flexitac-v2/ and one bundle per
  reading board in web/vendor/flexitac-reader/, every file at its pinned SHA-256 and size, each bundle its members (a
  Gerber ZIP, a BOM, a pick-and-place; no schematic) stored in name order with fixed metadata and re-derived byte for
  byte; what --check refuses; the folders' budgets; a write from the guide's files; the site build's gate.
- The notices (each folder's NOTICE.md: the source, the date read, the CC BY-NC 4.0 statement of Columbia University,
  every SHA-256, the EasyEDA each board's Gerbers name) and the README's licence section.
- web/boards.js: the rule (run under node where there is one) at its edges (16 x 32, its swap, 17 x 32, 32 x 32,
  33 x 8), the Library's sensors by it (42 on the 32 x 16 board, 16 on the 32 x 32, none larger), the engine's
  readers' own (surface/reader.py holds), its files the tool's pins, its guide the generator's; tailsBoard (Gen's step
  3, the review of 2026-11-17) the board of a design's tails: its lines' while each tail is one pin per line, else the
  board with those connectors (each board's BOM's two FFC connectors; surface/reader.py of_design), at its edges.
- The pages: every sensor's window ("Ordering and fabrication", "Reading board", no Reader row), the showcase's
  downloads (the pad's two FPC ZIPs, its reading board's row), Gen's step 3 (both modes; the guide linked once, the
  board by the tails), the board's dot never starting a line, its ZIP named in full for a screen reader, boards.js
  loaded before library.js and app.js; every download boards.js names exists in the published tree.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
VENDOR = WEB / "vendor"
sys.path.append(str(ROOT / "tools"))
import build_static_site  # noqa: E402
import export_public  # noqa: E402
import flexitac_downloads as D  # noqa: E402
import flexitac_v2  # noqa: E402

sys.path.insert(0, str(ROOT))
from surface import reader  # noqa: E402

READER = VENDOR / D.READER_FOLDER
BOARDS_JS = (WEB / "boards.js").read_text(encoding="utf-8")
LIBRARY_JS = (WEB / "library.js").read_text(encoding="utf-8")
APP_JS = (WEB / "app.js").read_text(encoding="utf-8")
GEN = (WEB / "gen.html").read_text(encoding="utf-8")
GUIDE = "https://docs.google.com/document/d/1bvz6AL7BUkhj4Dj7n9DFXTjnGIX4-ziN8-smiCKpVZU/edit?tab=t.0#heading=h.kk7d14qme9db"
# The rule's edges (the user's words: below 32 x 16 the 32 x 16 board, below 32 x 32 and above 16 the 32 x 32 board).
EDGES = {(16, 32): "32x16", (32, 16): "32x16", (12, 32): "32x16", (1, 1): "32x16", (16, 16): "32x16", (17, 32): "32x32",
         (32, 17): "32x32", (17, 17): "32x32", (32, 32): "32x32", (33, 8): None, (8, 33): None, (33, 33): None, (0, 5): None}
# Gen's step 3 (tailsBoard, the review of 2026-11-17): (rows, columns, row pins, column pins) -> [board, why there is
# none], or None for no sensor.  The pins empty (None) or each its lines': one pin per line, the lines' board (tail C);
# else the board with those connectors (Gen by Surface's Reader, Rectangular's connector pins).
TAILS = {(32, 12, None, None): ["32x16", None], (12, 32, None, None): ["32x16", None], (26, 27, None, None): ["32x32", None],
         (33, 8, None, None): [None, "more than 32 lines"], (12, 32, 12, 32): ["32x16", None], (12, 32, None, 32): ["32x16", None],
         (32, 12, 32, 16): ["32x16", None], (12, 32, 16, 32): ["32x16", None], (12, 32, 16, None): ["32x16", None],
         (32, 12, 32, 32): ["32x32", None], (12, 32, 32, 32): ["32x32", None], (32, 32, 32, 32): ["32x32", None],
         (16, 12, 16, 16): [None, "tails for another reader"], (32, 12, 48, 48): [None, "tails for another reader"],
         (20, 20, None, 32): [None, "tails for another reader"], (12, 32, 16, 33): [None, "tails for another reader"],
         (12, 32, 8, None): None, (12, 32, 16.5, None): None, (12, 32, 0, None): None, (None, 32, None, None): None, (12, 0, None, None): None}


def rule(rows: int, columns: int):
    """The rule as the task states it, a second reader of it (boards.js is checked against it under node)."""

    large, small = max(rows, columns), min(rows, columns)
    if rows < 1 or columns < 1:
        return None
    return "32x16" if large <= 32 and small <= 16 else "32x32" if large <= 32 else None


def node_boards(cases: list, tails: list = ()) -> dict:
    """boards.js run under node in a context of its own: readingBoard of each [rows, columns], tailsBoard of each
    [rows, columns, row pins, column pins] ([board, why] or null), its window object."""

    driver = ("const vm = require('vm'), fs = require('fs'); const ctx = {window: {}}; vm.createContext(ctx);"
              "vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), ctx); const B = ctx.window.FlexiTacBoards;"
              "const cases = JSON.parse(process.argv[2]), tails = JSON.parse(process.argv[3]);"
              "console.log(JSON.stringify({ids: cases.map(([r, c]) => (B.readingBoard(r, c) || {id: null}).id), guide: B.GUIDE, notice: B.NOTICE,"
              "tails: tails.map(t => { const seen = B.tailsBoard(...t); return seen && [seen.board && seen.board.id, seen.why]; }),"
              "boards: Object.values(B.BOARDS).map(b => [b.id, b.label, b.file, b.bytes, B.href(b), b.pins]), fpc: B.FPC.map(f => [f.kind, f.label, f.href, f.file, f.bytes]),"
              "frozen: Object.isFrozen(ctx.window.FlexiTacBoards) && Object.values(B.BOARDS).every(b => Object.isFrozen(b.pins))}));")
    run = subprocess.run(["node", "-e", driver, str(WEB / "boards.js"), json.dumps(cases), json.dumps(list(tails))], capture_output=True, text=True, timeout=60)
    if run.returncode != 0:
        raise AssertionError(run.stderr)
    return json.loads(run.stdout)


def bom_rows(name: str, payload: bytes) -> list:
    """A board's BOM as rows of {column: text}: EasyEDA's tab-separated UTF-16 CSV, or the first sheet of its .xlsx."""

    if name.endswith(".csv"):
        lines = [line.split("\t") for line in payload.decode("utf-16").splitlines() if line.strip()]
        return [dict(zip(lines[0], line)) for line in lines[1:]]
    with zipfile.ZipFile(io.BytesIO(payload)) as sheet:
        strings = [re.sub(r"<[^>]+>", "", item) for item in re.findall(r"<si>(.*?)</si>", sheet.read("xl/sharedStrings.xml").decode("utf-8"), re.S)]
        cells = re.findall(r"<c ([^>]*?)/?>(?:<v>([^<]*)</v>)?", sheet.read("xl/worksheets/sheet1.xml").decode("utf-8"))
    table: dict = {}
    for attributes, value in cells:
        column, row = re.search(r'\br="([A-Z]+)(\d+)"', attributes).groups()
        kind = re.search(r'\bt="(\w+)"', attributes)
        table.setdefault(int(row), {})[column] = strings[int(value)] if kind and kind.group(1) == "s" and value else value
    header = table.pop(min(table))
    return [{header[column]: text for column, text in row.items() if column in header} for _, row in sorted(table.items())]


def connector_pins(rows: list) -> dict:
    """The FFC connectors a BOM lists: designator -> positions (from the footprint: '..._32P-P0.50_...' or '...-16SBB...')."""

    pins = {}
    for row in rows:
        footprint = row.get("Footprint", "")
        found = re.search(r"_(\d+)P-P0\.50_|-(\d+)SBB", footprint)
        if footprint.startswith("FFC-SMD") and found:
            for designator in row["Designator"].split(","):
                pins[designator.strip()] = int(found.group(1) or found.group(2))
    return pins


class FilesTests(unittest.TestCase):
    def test_the_served_files_are_the_pinned_ones(self) -> None:
        self.assertEqual(D.check(), [])
        # The FPC ZIPs are the ones tools/flexitac_v2.py reads (the showcase's geometry): one pin for both tools.
        self.assertEqual({name: pin[0] for name, pin in D.FPC_FILES.items()}, dict(flexitac_v2.SOURCES.values()))
        for name, (digest, size) in D.FPC_FILES.items():
            data = (VENDOR / D.FPC_FOLDER / name).read_bytes()
            self.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), (digest, size))
        self.assertEqual(sorted(path.name for path in READER.iterdir()), sorted(["NOTICE.md", *(record["bundle"][0] for record in D.BOARDS.values())]))

    def test_each_bundle_is_the_user_s_three_files_stored_in_order_with_fixed_metadata(self) -> None:
        for board, record in D.BOARDS.items():
            with self.subTest(board=board):
                data = (READER / record["bundle"][0]).read_bytes()
                self.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), record["bundle"][1:])
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    infos = archive.infolist()
                    self.assertEqual([info.filename for info in infos], sorted(record["files"]))
                    for info in infos:
                        self.assertEqual((info.compress_type, info.date_time, info.create_system, info.external_attr >> 16),
                                         (zipfile.ZIP_STORED, D.ZIP_TIME, 3, 0o100644))
                    files = {info.filename: archive.read(info) for info in infos}
                self.assertEqual(D.bundle(files), data, "the bundle is re-derived from its members byte for byte")
                self.assertEqual(D.bundle(dict(reversed(list(files.items())))), data, "whatever the order given")
                # Gerber, BOM, pick and place (the user's three; not the schematic).
                kinds = sorted("gerber" if name.startswith("Gerber_") else "bom" if name.startswith("BOM_") else "placement"
                               if name.startswith("PickAndPlace_") else name for name in files)
                self.assertEqual(kinds, ["bom", "gerber", "placement"])
                self.assertFalse([name for name in files if re.search(r"schematic|\.pdf$", name, re.I)])
                for name, payload in files.items():
                    self.assertEqual((hashlib.sha256(payload).hexdigest(), len(payload)), record["files"][name])
                    if name.startswith("Gerber_"):
                        with zipfile.ZipFile(io.BytesIO(payload)) as gerbers:
                            layers = {Path(member).suffix for member in gerbers.namelist()}
                        self.assertLessEqual({".GTL", ".GBL", ".GKO", ".GTS", ".GBS", ".DRL"}, layers, "a two-layer board's Gerbers and drills")
                    elif name.endswith(".xlsx"):
                        with zipfile.ZipFile(io.BytesIO(payload)) as sheet:
                            self.assertIn("xl/workbook.xml", sheet.namelist())
                    else:
                        self.assertTrue(payload.startswith(b"\xff\xfe"), "EasyEDA's CSV, UTF-16 as exported")
                        self.assertIn("Designator", payload.decode("utf-16"))

    def test_check_names_each_fault(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            vendor = Path(folder) / "vendor"
            for name in (D.FPC_FOLDER, D.READER_FOLDER):
                shutil.copytree(VENDOR / name, vendor / name)
            self.assertEqual(D.check(vendor=vendor), [])
            top = vendor / D.FPC_FOLDER / "Gerber_Top_FPC_2026-03-02.zip"
            small = vendor / D.READER_FOLDER / "FlexiTac_reading_board_32x16.zip"
            large = vendor / D.READER_FOLDER / "FlexiTac_reading_board_32x32.zip"
            kept = {path: path.read_bytes() for path in (top, small, large)}
            top.write_bytes(kept[top][:100] + bytes([kept[top][100] ^ 1]) + kept[top][101:])
            self.assertEqual([problem.split(" is ")[0] for problem in D.check(vendor=vendor)], ["web/vendor/flexitac-v2/Gerber_Top_FPC_2026-03-02.zip"])
            top.write_bytes(kept[top])
            # A bundle of the right members in another order (or compressed) is not the derivation, nor at its pin.
            files = D.members(kept[small], "32x16")
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name in sorted(files, reverse=True):
                    archive.writestr(name, files[name])
            small.write_bytes(stream.getvalue())
            self.assertIn("holds", " ".join(D.check(vendor=vendor)))
            # A member changed: refused by its pin.
            changed = dict(files, **{"Gerber_16_32.zip": files["Gerber_16_32.zip"] + b"\0"})
            small.write_bytes(D.bundle(changed))
            self.assertIn("Gerber_16_32.zip is 46876 bytes", " ".join(D.check(vendor=vendor)))
            # A member more (the schematic, say).
            small.write_bytes(D.bundle(dict(files, **{"Schematic.pdf": b"%PDF"})))
            self.assertIn("Schematic.pdf", " ".join(D.check(vendor=vendor)))
            small.write_bytes(kept[small])
            large.unlink()
            self.assertEqual(D.check(vendor=vendor), ["web/vendor/flexitac-reader/FlexiTac_reading_board_32x32.zip is missing"])
            large.write_bytes(kept[large])
            with mock.patch.dict(D.BUDGETS, {D.READER_FOLDER: 1000}):
                self.assertRegex(" ".join(D.check(vendor=vendor)), r"web/vendor/flexitac-reader/ is \d+ bytes, over its budget of 1000")
            self.assertEqual(D.check(vendor=vendor), [])

    def test_the_folders_stay_within_their_budgets(self) -> None:
        for folder, budget in D.BUDGETS.items():
            size = sum(path.stat().st_size for path in (VENDOR / folder).rglob("*") if path.is_file())
            with self.subTest(folder=folder):
                self.assertLessEqual(size, budget)
                self.assertGreater(size, budget - 50_000, "the budget is near the folder as committed")

    def test_a_write_from_the_guide_s_files_gives_the_served_bytes_and_refuses_another_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            sources, vendor = Path(folder) / "sources", Path(folder) / "vendor"
            sources.mkdir()
            for name in D.FPC_FILES:
                shutil.copyfile(VENDOR / D.FPC_FOLDER / name, sources / name)
            for board, record in D.BOARDS.items():
                for name, payload in D.members((READER / record["bundle"][0]).read_bytes(), board).items():
                    (sources / name).write_bytes(payload)
            said = D.write(sources, vendor)
            self.assertEqual(len(said), 4)
            self.assertTrue(all(line.startswith("wrote web/vendor/") for line in said), said)
            for path in vendor.rglob("*"):
                if path.is_file():
                    self.assertEqual(path.read_bytes(), (VENDOR / path.relative_to(vendor)).read_bytes(), path)
            self.assertTrue(all(" is unchanged " in line for line in D.write(sources, vendor)))
            self.assertEqual(D.check(sources), [])
            (sources / "BOM_32_32.xlsx").write_bytes(b"another sheet")
            with self.assertRaisesRegex(D.DownloadsError, "the source BOM_32_32.xlsx is 13 bytes"):
                D.read(sources)
            (sources / "BOM_32_32.xlsx").unlink()
            self.assertEqual(D.check(sources), [f"the source BOM_32_32.xlsx is missing in {sources}"])

    def test_the_command_line_check(self) -> None:
        run = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "flexitac_downloads.py"), "--check"], capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("re-derived from its members", run.stdout)

    def test_the_site_build_checks_and_records_them(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            static = Path(folder) / "static"
            build_static_site.copy_web(static)
            served = build_static_site.hardware(static)
            self.assertEqual(sorted(served), sorted([*(f"static/vendor/{D.FPC_FOLDER}/{name}" for name in D.FPC_FILES),
                                                     *(f"static/vendor/{D.READER_FOLDER}/{record['bundle'][0]}" for record in D.BOARDS.values())]))
            # Every download boards.js names is published, at its pin (its hrefs are relative to the page: static/...):
            # each board's bundle and the pad's two ZIPs as node reads them, or by their text where node is not installed.
            if shutil.which("node"):
                seen = node_boards([])
                hrefs = [row[4] for row in seen["boards"]] + [row[2] for row in seen["fpc"]]
                notice = seen["notice"]
            else:
                hrefs = [f"static/vendor/{D.READER_FOLDER}/{name}" for name in re.findall(r'file: "(FlexiTac_reading_board_\w+\.zip)"', BOARDS_JS)]
                hrefs += [f"static/vendor/{D.FPC_FOLDER}/{name}" for name in re.findall(r'href: `\$\{FPC\}([^`]+)`', BOARDS_JS)]
                notice = f"static/vendor/{D.READER_FOLDER}/NOTICE.md"
            self.assertEqual(sorted(hrefs), sorted(served))
            self.assertTrue((Path(folder) / notice).is_file(), notice)
            for path, digest in served.items():
                self.assertEqual(hashlib.sha256((Path(folder) / path).read_bytes()).hexdigest(), digest)
            (static / "vendor" / D.READER_FOLDER / "FlexiTac_reading_board_32x32.zip").write_bytes(b"x")
            with self.assertRaisesRegex(build_static_site.BuildError, "FlexiTac hardware's files are not the pinned ones"):
                build_static_site.hardware(static)
        self.assertIn("    shelf = library(static, jobs=jobs)\n    served = hardware(static)\n", Path(build_static_site.__file__).read_text(encoding="utf-8"))

    def test_the_tool_and_the_files_are_public(self) -> None:
        self.assertIn("tools/flexitac_downloads.py", export_public.PUBLIC)
        self.assertIn("web", export_public.PUBLIC)
        source = (ROOT / "tools" / "flexitac_downloads.py").read_text(encoding="utf-8")
        imported = set(re.findall(r"^(?:import|from) (\w+)", source, re.M))
        self.assertLessEqual(imported, {"__future__", "argparse", "hashlib", "io", "sys", "zipfile", "pathlib"}, "standard library only")


class NoticeTests(unittest.TestCase):
    def test_the_reading_boards_notice(self) -> None:
        text = " ".join((READER / "NOTICE.md").read_text(encoding="utf-8").split())
        for words in ("Binghao Huang and Yunzhu Li", "Columbia University", "https://github.com/FlexiTac/FlexiTac",
                      "FlexiTac © 2026 by Columbia University is licensed under CC BY-NC 4.0",
                      "https://creativecommons.org/licenses/by-nc/4.0/", "**not** under this repository's Apache-2.0 licence",
                      "https://docs.google.com/document/d/1bvz6AL7BUkhj4Dj7n9DFXTjnGIX4-ziN8-smiCKpVZU/", "on 2026-11-17", "unchanged",
                      "`default-src 'self'`", "the schematic is not"):
            with self.subTest(words=words):
                self.assertIn(words, text)
        for record in D.BOARDS.values():
            name, digest, size = record["bundle"]
            self.assertIn(f"`{name}` ({size:,} bytes)", text)
            self.assertIn(f"`{digest}`", text)
            for member, (member_digest, member_size) in record["files"].items():
                self.assertIn(f"`{member}` ({member_size:,} bytes, SHA-256 `{member_digest}`)", text)
        self.assertNotRegex(text, "/" + "home/|/" + "tmp/")

    def test_the_reading_boards_notice_names_the_easyeda_of_their_gerbers(self) -> None:
        # The review of 2026-11-17: the 32 x 16 board's Gerbers are EasyEDA (Standard) exports, the 32 x 32 board's EasyEDA
        # Pro's, as each top copper's header says.
        heads = {"32x16": "G04 EasyEDA v6.5.51, 2026-04-03 00:14:50*", "32x32": "G04 EasyEDA Pro v3.2.109, 2026-04-02 18:50:05*"}
        for board, record in D.BOARDS.items():
            files = D.members((READER / record["bundle"][0]).read_bytes(), board)
            [name] = [name for name in files if name.startswith("Gerber_")]
            with zipfile.ZipFile(io.BytesIO(files[name])) as gerbers:
                head = gerbers.read("Gerber_TopLayer.GTL").decode("ascii").splitlines()
            self.assertIn(heads[board], head[:4], board)
        text = " ".join((READER / "NOTICE.md").read_text(encoding="utf-8").split())
        self.assertIn("The boards were laid out by hand in EasyEDA (the 32 x 16 board's Gerbers are EasyEDA v6.5.51 exports of 2026-04-03, "
                      "the 32 x 32 board's EasyEDA Pro v3.2.109 exports of 2026-04-02, as their headers say)", text)

    def test_the_pad_s_notice_tables_its_two_zips(self) -> None:
        text = (VENDOR / D.FPC_FOLDER / "NOTICE.md").read_text(encoding="utf-8")
        for name, (digest, size) in D.FPC_FILES.items():
            self.assertRegex(text, rf"\| `{re.escape(name)}` \|[^\n]*\| unchanged \({size:,} bytes\) \| `{digest}` \|")

    def test_the_readme_names_the_folder_and_its_licence(self) -> None:
        section = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split("\n## License\n", 1)[1].split())
        self.assertRegex(section, r"`web/vendor/flexitac-reader/`[^.]*CC BY-NC 4\.0[^.]*Columbia University")
        self.assertIn("(web/vendor/flexitac-reader/NOTICE.md)", section)


class RuleTests(unittest.TestCase):
    def test_the_rule_as_stated(self) -> None:
        self.assertEqual({case: rule(*case) for case in EDGES}, EDGES)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_boards_js_at_the_edges_and_on_every_library_sensor(self) -> None:
        entries = json.loads((WEB / "library" / "entries.json").read_text(encoding="utf-8"))["variants"]
        cases = [list(case) for case in EDGES] + [[2.5, 3], [None, 4], ["12", 32]]
        cases += [[variant["rows"], variant["columns"]] for variant in entries.values()]
        seen = node_boards(cases)
        self.assertTrue(seen["frozen"])
        self.assertEqual(seen["ids"][:len(EDGES)], list(EDGES.values()))
        self.assertEqual(seen["ids"][len(EDGES):len(EDGES) + 3], [None, None, None], "only whole numbers of lines")
        library = seen["ids"][len(EDGES) + 3:]
        self.assertEqual(library, [rule(variant["rows"], variant["columns"]) for variant in entries.values()])
        # Today (2026-11-17): 42 sensors on the 32 x 16 board, 16 on the 32 x 32, none larger (other cards to come).
        counts = {board: library.count(board) for board in ("32x16", "32x32", None)}
        self.assertEqual(counts[None], 0)
        self.assertGreaterEqual(counts["32x16"], 42)
        self.assertGreaterEqual(counts["32x32"], 16)
        # Its files are the tool's pins; its guide is the generator's.
        self.assertEqual(seen["boards"], [[board, board.replace("x", " × "), record["bundle"][0], record["bundle"][2],
                                           f"static/vendor/{D.READER_FOLDER}/{record['bundle'][0]}", sorted(reader.READERS[board])]
                                          for board, record in D.BOARDS.items()])
        self.assertEqual([row[3:] for row in seen["fpc"]], [[name, size] for name, (_, size) in D.FPC_FILES.items()])
        self.assertEqual([row[:3] for row in seen["fpc"]], [["top-gerber", "Top FPC Gerber ZIP", "static/vendor/flexitac-v2/Gerber_Top_FPC_2026-03-02.zip"],
                                                             ["bottom-gerber", "Bottom FPC Gerber ZIP", "static/vendor/flexitac-v2/Gerber_Bottom_FPC_2026-03-02.zip"]])
        self.assertEqual((seen["guide"], seen["notice"]), (GUIDE, "static/vendor/flexitac-reader/NOTICE.md"))

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_the_rule_is_the_engine_s_readers(self) -> None:
        # A sensor's board is the first of the two readers of surface/reader.py that holds its lines (either electrode set
        # on either connector), 1 to 40 lines a side.
        cases = [[rows, columns] for rows in range(1, 41) for columns in range(1, 41)]
        expected = [next((name for name in ("32x16", "32x32") if reader.holds(rows, columns, name)), None) for rows, columns in cases]
        # The cases that differ (a short message where they do: a diff of 1600 entries takes minutes).
        self.assertEqual([[case, seen, want] for case, seen, want in zip(cases, node_boards(cases)["ids"], expected) if seen != want], [])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_gen_s_board_follows_the_tails(self) -> None:
        # The review of 2026-11-17: a Reader chosen in Gen by Surface (or connector pins in Rectangular) sizes the tails to
        # its connectors, so step 3 names the board with those connectors, not the lines' board.
        seen = node_boards([], [list(case) for case in TAILS])
        self.assertEqual(dict(zip(TAILS, seen["tails"])), TAILS)
        # Every reader the fit offers, on every readout it holds up to 48 lines a side: the tails the engine sizes
        # (reader.connector) plug into the board with those pins (reader.of_design), the lines' board where each tail is
        # one pin per line (tail C), none for the 16 x 16 and 48 x 48 readers' own tails.
        cases, expected = [], []
        for name in reader.READERS:
            for rows in range(1, 49, 3):
                for columns in range(1, 49, 5):
                    if not reader.holds(rows, columns, name):
                        continue
                    pins = reader.connector(rows, columns, name)
                    cases.append([rows, columns, pins["row_pins"], pins["column_pins"]])
                    if (pins["row_pins"], pins["column_pins"]) == (rows, columns):
                        board = rule(rows, columns)
                        expected.append([board, None if board else "more than 32 lines"])
                    else:
                        board = reader.of_design("auto", pins["row_pins"], pins["column_pins"])
                        board = board if board in D.BOARDS else None
                        expected.append([board, None if board else "tails for another reader"])
        self.assertGreater(len(cases), 300)
        self.assertEqual([[case, seen, want] for case, seen, want in zip(cases, node_boards([], cases)["tails"], expected) if seen != want], [])

    def test_each_board_s_pins_are_its_bom_s_connectors(self) -> None:
        # boards.js's pins (and surface/reader.py's 32x16 and 32x32) are the two FFC connectors each board's BOM lists:
        # FPC1 and FPC2, 0.5 mm, 16 and 32 positions on the 32 x 16 board, 32 and 32 on the 32 x 32.
        for board, record in D.BOARDS.items():
            with self.subTest(board=board):
                files = D.members((READER / record["bundle"][0]).read_bytes(), board)
                [name] = [name for name in files if name.startswith("BOM_")]
                pins = sorted(connector_pins(bom_rows(name, files[name])).values())
                self.assertEqual(pins, sorted(reader.READERS[board]))
                self.assertIn(f'pins: Object.freeze([{pins[0]}, {pins[1]}])', BOARDS_JS)

    def test_boards_js_by_its_text(self) -> None:
        # Where node is not installed the test above is skipped: the rule's line and the pins by their text.
        self.assertIn('return large <= 32 && small <= 16 ? BOARDS["32x16"] : large <= 32 ? BOARDS["32x32"] : null;', BOARDS_JS)
        self.assertIn("const [large, small] = [Math.max(rows, columns), Math.min(rows, columns)];", BOARDS_JS)
        for board, record in D.BOARDS.items():
            self.assertIn(f'file: "{record["bundle"][0]}", bytes: {record["bundle"][2]}', BOARDS_JS)
        for name, (_, size) in D.FPC_FILES.items():
            self.assertIn(f'file: "{name}", bytes: {size}', BOARDS_JS)
        self.assertIn(f'GUIDE: "{GUIDE}"', BOARDS_JS)
        # tailsBoard: the lines' board while each tail is one pin per line, else the board with those connectors.
        for words in ("const pins = [rowPins ?? rows, columnPins ?? columns];", "if (pins[0] === rows && pins[1] === columns) {",
                      "const board = Object.values(BOARDS).find(item => item.pins.join() === sorted) || null;",
                      'return {board, why: board ? null : "tails for another reader"};', "    tailsBoard,\n"):
            with self.subTest(words=words):
                self.assertIn(words, BOARDS_JS)
        if shutil.which("node"):
            self.assertEqual(subprocess.run(["node", "--check", str(WEB / "boards.js")], capture_output=True).returncode, 0)


class PageTests(unittest.TestCase):
    def test_both_pages_load_boards_js_before_their_own_script(self) -> None:
        index = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertLess(index.index('<script src="static/boards.js" defer></script>'), index.index('<script src="static/library.js" defer></script>'))
        self.assertLess(GEN.index('<script src="static/boards.js" defer></script>'), GEN.index('<script src="static/app.js" defer></script>'))

    def test_every_sensor_window_has_the_two_rows_and_no_reader_row(self) -> None:
        self.assertNotIn('["Reader", ', LIBRARY_JS)
        self.assertNotIn("one tail pin per line)", LIBRARY_JS)
        for words in ('el("dt", {}, "Ordering and fabrication")', 'el("dt", {}, "Reading board")', '"FlexiTac fabrication guide"',
                      '"none (more than 32 lines)"', "boardRow(HARDWARE.readingBoard(rows, columns))", "orderFacts(variant.rows, variant.columns)",
                      'target: "_blank", rel: "noopener noreferrer"}, "FlexiTac fabrication guide"', "download: board.file",
                      'el("a", {href: HARDWARE.NOTICE, target: "_blank", rel: "noopener"}, LICENCE)',
                      # The board's pieces: the dot never starts a line (the review of 2026-11-17), its ZIP named in full.
                      '[el("span", {}, board.label), "\\u00a0· ",', '"aria-label": `Reading board ${board.label}, ${size}`}, size), "\\u00a0· ",'):
            with self.subTest(words=words):
                self.assertIn(words, LIBRARY_JS)
        # Per sensor from its rows and columns alone: no field of entries.json names a board.
        entries = (WEB / "library" / "entries.json").read_text(encoding="utf-8")
        self.assertNotIn("reading_board", entries)

    def test_the_showcase_window_offers_the_pad_s_files(self) -> None:
        # The pad's two FPC ZIPs in the download pills (one line under the tutorial), its reading board in the sensors' own
        # row, its licence there (the review of 2026-11-17: three pills had wrapped two and one); the sources as before.
        page = LIBRARY_JS.split("  function renderShowcase() {", 1)[1].split("\n  }\n", 1)[0]
        for words in ("const files = HARDWARE ? HARDWARE.FPC.map(item => [item.href, item.file, item.label, item.kind]) : [];",
                      'el("a", {className: "lib-pill", href, download: file, "data-hardware": kind}, label)',
                      "HARDWARE?.readingBoard(data.sensor?.rows, data.sensor?.columns)",
                      'board ? el("dl", {className: "lib-order"}, boardRow(board)) : null,',
                      'el("a", {href: BASE + source.notice, target: "_blank", rel: "noopener"}, "notice"), ")"])))));'):
            with self.subTest(words=words):
                self.assertIn(words, page)
        self.assertNotIn("Reading board", page)
        self.assertLess(page.index('"data-hardware": kind'), page.index("boardRow(board)"))
        showcase = json.loads((WEB / "library" / "showcase.json").read_text(encoding="utf-8"))
        self.assertEqual(rule(showcase["sensor"]["rows"], showcase["sensor"]["columns"]), "32x16", "the original 12 x 32 pad reads on the 32 x 16 board")

    def test_gen_s_step_3_names_the_board_in_both_modes(self) -> None:
        downloads = GEN.split('<section class="downloads"', 1)[1].split("</section>\n        </div>", 1)[0]
        board = downloads.split('<dl class="order-board" id="orderBoard">', 1)[1].split("</dl>", 1)[0]
        self.assertIn("<dt>Ordering and fabrication</dt>", board)
        self.assertIn(f'<a href="{GUIDE}" target="_blank" rel="noopener noreferrer">FlexiTac fabrication guide</a>', board)
        self.assertIn('<dt>Reading board</dt><dd id="readingBoard"></dd>', board)
        # Over the ordering notes, after the build's downloads (one section for Gen by Surface and Rectangular).
        self.assertLess(downloads.index('id="orderBoard"'), downloads.index('id="manufacturingNote"'))
        self.assertEqual(GEN.count('class="downloads"'), 1)
        for words in ("function showBoard()", 'const number = id => ($(id).value.trim() === "" ? null : Number($(id).value));',
                      'boards.tailsBoard(number("rows"), number("columns"), number("rowPins"), number("columnPins"))',
                      '[seen ? `none (${seen.why})` : "—"]', "    showBoard();\n  }\n",
                      '[el("span", {}, board.label), "\\u00a0· ",', '"aria-label": `Reading board ${board.label}, ${size}`}, size), "\\u00a0· ",'):
            with self.subTest(words=words):
                self.assertIn(words, APP_JS)
        # The guide linked once in step 3 (the Ordering notes' line of 2026-11-06 is the row now: the review of 2026-11-17).
        self.assertEqual(downloads.count(GUIDE), 1)
        self.assertNotIn("order-guide", GEN)


if __name__ == "__main__":
    unittest.main()
