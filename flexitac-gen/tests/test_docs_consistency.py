"""The documents against the code (audit M12: claims the code did not meet; L13: hygiene).

README.md, docs/*.md, claude/APP_HANDOFF.md and the tools READMEs quote the
default build, the versions, the issue catalogue, the DRC records, the HTTP
and CLI codes and limits, the profile, the export members, where pin 1 and
the first electrodes are on each tail side and in the stack, the test map and
the mutation catalogue.  These tests read those tables and quoted figures
(found by the phrase that quotes them) and compare them with the code and
with generated boards, and they run every Python snippet of the documents,
so a document cannot drift from the output without failing here.  Prose
without figures is not checked.  They also check that relative links resolve
inside the project, that no host-specific path is quoted and that
pyproject.toml declares Python 3.9 and no dependencies.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import unittest
import zipfile
from pathlib import Path

import app
import cli
import engine
import exporters
from engine import GENERATOR_VERSION, check_design, default_design, generate_design, input_limits, load_profile, result_view
from engine.drc import _ERRORS
from engine.profile import order_requirements
from engine.schema import ERROR_CODES, WARNING_CODES
from exporters import ARTIFACT_KEYS, EXPORTER_VERSION, build_exports

try:
    import geometry_checks as gc
except ImportError:  # run as a package
    from tests import geometry_checks as gc

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [
    ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), ROOT / "claude" / "APP_HANDOFF.md",
    ROOT / "tools" / "README.md", ROOT / "tools" / "browser" / "README.md",
]
HANDOFF = ROOT / "claude" / "APP_HANDOFF.md"
WORKFLOW = ROOT.parent / ".github" / "workflows" / "fpc-agentic-customization.yml"
EPS = 1e-6
_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_HEADING = re.compile(r"^(#+) (.*)$")
# Direction words of the tables in docs/INTEGRATION.md, as vectors of a top view (Y up).
_DIRECTIONS = {
    "bottom": (0.0, -1.0), "lower": (0.0, -1.0), "top": (0.0, 1.0), "upper": (0.0, 1.0),
    "left": (-1.0, 0.0), "leftmost": (-1.0, 0.0), "right": (1.0, 0.0), "rightmost": (1.0, 0.0),
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _prose(text: str) -> str:
    """Markdown as one line without emphasis and code marks, where quoted figures are looked up."""

    return re.sub(r"\s+", " ", text.replace("**", "").replace("`", ""))


def _quoted(test: unittest.TestCase, text: str, pattern: str, raw: bool = False) -> tuple:
    """The groups of the one phrase of ``text`` that matches ``pattern`` (as values unless ``raw``)."""

    found = re.findall(pattern, text)
    test.assertEqual(len(found), 1, f"expected one phrase matching {pattern!r}; reword the document or this test")
    groups = found[0] if isinstance(found[0], tuple) else (found[0],)
    return tuple(groups) if raw else tuple(_value(group) for group in groups)


def _table(text: str) -> list[list[str]]:
    """Cells of every Markdown table row in ``text`` (separator rows dropped)."""

    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and not set(line) <= set("|-: "):
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def _directions(cell: str) -> list[tuple[float, float]]:
    return [_DIRECTIONS[word] for word in re.findall(r"[a-z]+", cell.lower()) if word in _DIRECTIONS]


def _dot(point, vector) -> float:
    return point[0] * vector[0] + point[1] * vector[1]


def _middle(box) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _box(bounds: dict) -> tuple[float, float, float, float]:
    return (bounds["x"], bounds["y"], bounds["x"] + bounds["width"], bounds["y"] + bounds["height"])


def _corners(bounds: dict) -> list[tuple[float, float]]:
    x0, y0 = bounds["x"], bounds["y"]
    x1, y1 = x0 + bounds["width"], y0 + bounds["height"]
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _member_pattern(name: str):
    """A documented member name as a pattern: ``<t>`` is a thickness, ``<name>`` any file name."""

    return re.compile(re.escape(name).replace("<t>", r"[0-9.]+").replace("<name>", r"[^/]+"))


def _mutation_catalogue():
    """tools/mutation_check.py as a module (it only defines the catalogue and the runner)."""

    spec = importlib.util.spec_from_file_location("fpc_mutation_check", ROOT / "tools" / "mutation_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _section(text: str, heading: str) -> str:
    """The text below a heading, up to the next heading of the same or a higher level."""

    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = _HEADING.match(line)
        if match and match.group(2).strip() == heading:
            level = len(match.group(1))
            body = []
            for other in lines[index + 1:]:
                found = _HEADING.match(other)
                if found and len(found.group(1)) <= level:
                    break
                body.append(other)
            return "\n".join(body)
    raise AssertionError(f"heading {heading!r} not found")


def _rows(text: str) -> list[list[str]]:
    """Cells of the Markdown table rows in ``text`` (header and separator rows dropped)."""

    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
    return [row for row in rows if row and row[0].startswith("`")]


def _code(cell: str) -> str:
    return cell.strip().strip("`")


def _value(cell: str):
    """A table cell as a JSON-like value: numbers, true/false/null, lists 'a, b', else text."""

    cell = cell.strip().strip("`")
    if cell in ("true", "false", "null"):
        return json.loads(cell)
    if "," in cell:
        return [_value(part) for part in cell.split(",")]
    try:
        number = float(cell)
    except ValueError:
        return cell
    return int(number) if re.fullmatch(r"-?\d+", cell) else number


def _slug(heading: str) -> str:
    """GitHub-style anchor of a heading."""

    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return text.replace(" ", "-")


def _anchors(path: Path) -> set[str]:
    return {_slug(match.group(2)) for match in map(_HEADING.match, _text(path).splitlines()) if match}


class DocumentClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = generate_design()
        cls.profile = load_profile()

    def test_quoted_build_ids_and_versions_are_the_current_ones(self) -> None:
        build_id = self.result["manifest"]["build_id"]
        for path in DOCUMENTS:
            text = _text(path)
            with self.subTest(document=path.name):
                self.assertLessEqual(set(re.findall(r"tactile-fpc-12x32-[0-9a-f]{12}", text)), {build_id})
                self.assertLessEqual(set(re.findall(r"deterministic-sensor-core/[0-9.]+[0-9]", text)), {GENERATOR_VERSION})
                self.assertLessEqual(set(re.findall(r"direct-gerber-pure-stdlib/[0-9.]+[0-9]", text)), {EXPORTER_VERSION})
        for name in ("README.md", "docs/API.md", "docs/PHASE2_DIRECT_GERBER.md", "claude/APP_HANDOFF.md"):
            with self.subTest(document=name):
                self.assertIn(build_id, _text(ROOT / name))

    def test_issue_catalogue_table_lists_every_engine_code(self) -> None:
        rows = _rows(_section(_text(ROOT / "docs" / "LAYOUT_SCHEMA.md"), "Issue catalogue"))
        documented = {_code(row[0]): row[1] for row in rows}
        expected = {code: source for code, (source, _) in {**ERROR_CODES, **WARNING_CODES}.items()}
        self.assertEqual(documented, expected)

    def test_every_result_and_layout_key_is_documented(self) -> None:
        text = _text(ROOT / "docs" / "LAYOUT_SCHEMA.md")

        def named(heading: str) -> set[str]:
            # Every identifier inside a code span, e.g. `net, kind, anchor, x, y`, with and without its digits
            # (`trace_overlap_area_mm2`).
            spans = re.findall(r"`([^`]+)`", _section(text, heading))
            return {word for span in spans for pattern in (r"[A-Za-z_]+", r"[A-Za-z_][A-Za-z_0-9]*") for word in re.findall(pattern, span)}

        column = generate_design({"matrix": {"columns": 17}, "connector": {"row_pins": 14}})
        self.assertTrue(column["ok"], column["validation"]["errors"])
        # A diagonal Row bus (routing.row_sides): its boards' records and its registration's stack keys.
        diagonal = generate_design({"template_id": "surface_matrix_v1", "matrix": {"rows": 5, "columns": 4}, "routing": {"row_sides": "both"}})
        self.assertTrue(diagonal["ok"], diagonal["validation"]["errors"])
        boards = [*self.result["boards"].values(), *column["boards"].values(), *diagonal["boards"].values()]
        copper = [board["layers"]["top_copper"] for board in boards]
        expectations = {
            "The result object": set(self.result),
            "Board object": {key for board in boards for key in board},
            "`layers.top_copper`": {key for layer in copper for kind in ("electrodes", "routes", "pads") for item in layer[kind] for key in item},
            "`layers.top_coverlay_openings`": {key for board in boards for item in board["layers"]["top_coverlay_openings"] for key in item},
            "`layers.bottom_stiffener`": {key for board in boards for item in board["layers"]["bottom_stiffener"] for key in item},
            "`grid_registration`": {key for board in boards for key in board["grid_registration"]},
            "`tail`": {key for board in boards for key in board["tail"]},
            "`construction`": {key for board in boards for key in board["construction"]},
            "Verification": {key for board in boards for key in board["verification"]},
            "Registration record": set(self.result["boards"]["row"]["verification"]["registration"])
            | set(diagonal["boards"]["row"]["verification"]["registration"]),
            # construction.row_bus and the keys of its objects (band_mm, lane_angle_deg).
            "Diagonal Row bus": {
                name for key, value in diagonal["boards"]["row"]["construction"]["row_bus"].items()
                for name in (key, *(value if isinstance(value, dict) else ()))
            },
        }
        for heading, keys in expectations.items():
            with self.subTest(section=heading):
                self.assertLessEqual(keys, named(heading))

    def test_drc_record_table_matches_the_default_build(self) -> None:
        rows = _rows(_section(_text(ROOT / "docs" / "LAYOUT_SCHEMA.md"), "Whole-board DRC records"))
        documented = {_code(row[0]): row for row in rows}
        boards = (self.result["boards"]["row"], self.result["boards"]["column"])
        self.assertEqual(set(documented), set(boards[0]["verification"]["checks"]))
        for name, row in documented.items():
            with self.subTest(record=name):
                code, part = _ERRORS[name]
                self.assertEqual((_code(row[3]), _code(row[4])), (code, part))
                records = [board["verification"]["checks"][name] for board in boards]
                required = [record["required_mm"] for record in records]
                if required == [None, None]:
                    self.assertEqual(row[2], "pass/fail")
                else:
                    self.assertEqual([_value(part) for part in row[2].split("/")], required)
                self.assertEqual([_value(part) for part in row[5].split("/")], [record["measured_mm"] for record in records])

    def test_profile_tables_match_the_profile(self) -> None:
        sections = (
            (ROOT / "docs" / "LAYOUT_SCHEMA.md", "Profile rules used by the layout and the DRC"),
            (ROOT / "claude" / "APP_HANDOFF.md", "Locked profile"),
        )
        listed = set()
        for path, heading in sections:
            rows = _rows(_section(_text(path), heading))
            self.assertTrue(rows, heading)
            for row in rows:
                section, _, key = _code(row[0]).partition(".")
                with self.subTest(document=path.name, key=_code(row[0])):
                    self.assertIn(key, self.profile.get(section, {}))
                    self.assertEqual(_value(row[1]), self.profile[section][key])
                listed.add((path.name, section, key))
        # The handoff lists every rule value of the profile.
        every = {
            (section, key)
            for section, values in self.profile.items() if isinstance(values, dict) and section != "sources"
            for key in values if not (section == "fabrication" and key == "source")
        }
        self.assertEqual({(section, key) for name, section, key in listed if name == "APP_HANDOFF.md"}, every)

    def test_default_build_table_of_the_handoff_matches_the_output(self) -> None:
        rows = _rows(_section(_text(ROOT / "claude" / "APP_HANDOFF.md"), "Default build"))
        self.assertGreater(len(rows), 10)
        for row in rows:
            path = _code(row[0])
            for board, cell in zip((self.result["boards"]["row"], self.result["boards"]["column"]), row[1:3]):
                with self.subTest(path=path, board=board["id"]):
                    value = board
                    for key in path.split("."):
                        value = value.get(key, "—") if isinstance(value, dict) else "—"
                    self.assertEqual(value, _value(cell))

    def test_design_input_table_and_readme_ranges_match_the_input_limits(self) -> None:
        limits = input_limits(self.profile)
        rows = _rows(_section(_text(ROOT / "docs" / "API.md"), "Design input (`tactile-fpc-design/v1`)"))
        checked = 0
        for row in rows:
            field = _code(row[0])
            if field not in limits:
                continue  # rows naming two fields (role_mapping, channel_order) are prose
            spec = limits[field]
            with self.subTest(field=field):
                if "maximum" in spec:
                    numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", row[2].split(" and ")[0])]
                    self.assertEqual(numbers[-1], spec["maximum"])
                    if not spec.get("nullable"):
                        self.assertEqual(numbers[0], spec["minimum"])
                if "max_length" in spec:
                    self.assertEqual(_quoted(self, row[2], r"(\d+)-(\d+) characters after trimming"), (spec["min_length"], spec["max_length"]))
                # Enumerated values (field paths such as `tail.row_side` in a rule are not values).
                values = [span for span in re.findall(r"`([^`]+)`", row[2]) if "." not in span]
                allowed = spec.get("enum", [spec["const"]] if "const" in spec else None)
                if allowed is not None and values:
                    self.assertEqual(values, allowed)
                default = row[3].split(" (")[0].strip()
                if default and not default.startswith(("(", "`Tactile")):
                    self.assertEqual(_value(default), spec["default"])
                self.assertEqual(re.findall(r"`([^`]+)`", row[4]), spec["aliases"])
                checked += 1
        self.assertGreaterEqual(checked, 15)
        readme = _text(ROOT / "README.md")
        for text in (
            f"rows ({limits['matrix.rows']['minimum']}-{limits['matrix.rows']['maximum']})",
            f"columns ({limits['matrix.columns']['minimum']}-{limits['matrix.columns']['maximum']})",
            f"pitch ({limits['matrix.pitch_x_mm']['minimum']:g}-{limits['matrix.pitch_x_mm']['maximum']:g} mm)",
            f"({limits['tail.top_length_mm']['minimum']:g}-{limits['tail.top_length_mm']['maximum']:g} mm)",
            f"{len(self.result['boards']['row']['verification']['checks'])} records per board",
        ):
            self.assertIn(text, readme)

    def test_http_and_cli_code_tables_match_the_server_and_the_cli(self) -> None:
        text = _text(ROOT / "docs" / "API.md")
        for heading, codes in (("HTTP error codes", app.HTTP_ERROR_CODES), ("CLI error codes", cli.CLI_ERROR_CODES)):
            rows = _rows(_section(text, heading))
            documented = {_code(row[0]): row[1] for row in rows}
            with self.subTest(table=heading):
                self.assertEqual(set(documented), set(codes))
                for code, meaning in codes.items():
                    # Status (HTTP) or exit status (CLI) first, as in the code's own table.
                    self.assertEqual(documented[code].split(":")[0], meaning.split(":")[0], code)
                    # Every figure of the code's text (timeouts, sizes, limits) is quoted.
                    self.assertLessEqual(set(re.findall(r"\d+", meaning)), set(re.findall(r"\d+", documented[code])), code)


class ApiDocumentTests(unittest.TestCase):
    """docs/API.md: the entry points, the HTTP limits and the reply sizes it quotes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _text(ROOT / "docs" / "API.md")
        cls.prose = _prose(cls.text)

    def test_python_entry_points_exist_with_the_documented_parameters(self) -> None:
        checked = 0
        for row in _rows(_section(self.text, "Python entry points")):
            for span in re.findall(r"`([^`]+)`", row[0]):
                call = re.fullmatch(r"(\w+)\((.*)\)", span)
                if call is None:
                    continue
                name, arguments = call.groups()
                module = engine if name in engine.__all__ else exporters
                with self.subTest(function=name):
                    self.assertIn(name, module.__all__)
                    parameters = inspect.signature(getattr(module, name)).parameters
                    keyword_only = False
                    for argument in (part.strip() for part in arguments.split(",") if part.strip()):
                        if argument == "*":
                            keyword_only = True
                        elif re.fullmatch(r"\w+=\w+", argument):
                            # A named parameter with its default: the name, kind and default are the contract.
                            parameter, default = argument.split("=")
                            self.assertIn(parameter, parameters)
                            kind = inspect.Parameter.KEYWORD_ONLY if keyword_only else inspect.Parameter.POSITIONAL_OR_KEYWORD
                            self.assertEqual(parameters[parameter].kind, kind, parameter)
                            self.assertEqual(repr(parameters[parameter].default), default, parameter)
                    checked += 1
        self.assertGreaterEqual(checked, 10)
        self.assertEqual(set(check_design({})), {"ok", "design", "validation", "identity"})
        self.assertIn("{" + ", ".join(ARTIFACT_KEYS) + "}", self.prose)

    def test_http_limits_match_the_server(self) -> None:
        text = self.prose
        mib = app.MAX_DRAIN_BYTES / 2 ** 20
        self.assertEqual(_quoted(self, text, r"(\d+) s socket timeout per read and (\d+) s for the whole request"), (app.SOCKET_TIMEOUT_S, app.REQUEST_DEADLINE_S))
        self.assertEqual(_quoted(self, text, r"drains them for at most (\d+) s or (\d+) MiB"), (app.MAX_DRAIN_S, mib))
        self.assertEqual(_quoted(self, text, r"Idle connections that send nothing are closed after (\d+) s"), (app.SOCKET_TIMEOUT_S,))
        self.assertEqual(
            _quoted(self, text, r"Listen backlog (\d+); at most (\d+) generations or exports run at once, others get (\d+) E_HTTP_BUSY with Retry-After: (\d+)"),
            (app.AppServer.request_queue_size, app.MAX_CONCURRENT_GENERATIONS, 503, app.RETRY_AFTER_S),
        )
        self.assertEqual(_quoted(self, text, r"A build cache of (\d+) builds"), (app.BUILD_CACHE_SIZE,))
        self.assertEqual(_quoted(self, text, r"at most (\d+) KiB \(413\)"), (app.MAX_REQUEST_BYTES / 1024,))
        self.assertEqual(_quoted(self, text, r"More than about (\d+) simultaneous connection attempts"), (app.AppServer.request_queue_size,))
        self.assertEqual(_quoted(self, text, r"keeps sending for more than (\d+) s or (\d+) MiB"), (app.MAX_DRAIN_S, mib))
        for name, value in (*app.SECURITY_HEADERS, ("Server", app.AppHandler.server_version)):
            self.assertIn(f"{name}: {value}", text)
        port = inspect.signature(app.make_server).parameters["port"].default
        for path in (ROOT / "README.md", ROOT / "docs" / "API.md", HANDOFF):
            with self.subTest(document=path.name):
                self.assertEqual(set(re.findall(r"http://127\.0\.0\.1:(\d+)", _text(path))), {str(port)})

    def test_reply_sizes_of_the_default_design(self) -> None:
        result = generate_design({})
        sizes = tuple(
            round(len(json.dumps(result_view(result, view), ensure_ascii=True, separators=(",", ":"), allow_nan=False)) / 1000)
            for view in ("full", "compact")
        )
        self.assertEqual(_quoted(self, self.prose, r"the full view is about (\d+) kB and the compact view about (\d+) kB"), sizes)

    def test_core_manifest_fields_are_documented(self) -> None:
        manifest = generate_design({})["manifest"]
        named = set(re.findall(r"\w+", " ".join(re.findall(r"`([^`]+)`", _section(self.text, "Build identity")))))
        self.assertLessEqual(set(manifest) | set(manifest["checks"]) | set(manifest["profile"]), named)
        for key, value in (("production_ready", False), ("output_status", "geometry_only"), ("requires_final_jlc_review", True)):
            self.assertEqual(manifest[key], value)
            self.assertIn(f"{key}: {json.dumps(value)}", _prose(_section(self.text, "Build identity")))


class IntegrationDocumentTests(unittest.TestCase):
    """docs/INTEGRATION.md: its two tables and its dimensions against generated boards.

    The positions are read from the layout's own coordinates (the copper-side
    top view, Y up), independently of the engine's transforms.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _text(ROOT / "docs" / "INTEGRATION.md")
        cls.prose = _prose(cls.text)
        cls.profile = load_profile()

    def _extreme(self, points: dict, vector, chosen, label) -> None:
        """``chosen`` is the one key of ``points`` farthest along ``vector``."""

        ranked = sorted(points, key=lambda key: _dot(points[key], vector))
        self.assertEqual(ranked[-1], chosen, label)
        self.assertGreater(_dot(points[ranked[-1]], vector), _dot(points[ranked[-2]], vector) + EPS, label)

    def test_side_table_matches_each_tail_side(self) -> None:
        rows = _rows(_section(self.text, "Each board on its own"))
        self.assertEqual([_code(row[0]) for row in rows], ["bottom", "right", "top", "left"])
        for row in rows:
            side = _code(row[0])
            # The table describes the straight Row channel (its Row tail at one end; the generic default is the diagonal Row
            # bus since P5-diagonal-bus.md section 18).
            result = generate_design({"matrix": {"rows": 3, "columns": 5}, "tail": {"row_side": side, "column_side": side},
                                      "routing": {"row_sides": "channel"}})
            self.assertTrue(result["ok"], result["validation"]["errors"])
            (out,), (pin_end,), (row_end,), (column_end,) = (_directions(cell) for cell in row[1:5])
            corner = _directions(row[5])
            with self.subTest(side=side):
                self.assertEqual(len(corner), 2)
                self.assertIn(out, corner)
                lateral = next(vector for vector in corner if vector != out)
                for board in result["boards"].values():
                    outline = board["outline"]["points"]
                    tail = _corners(board["tail"]["bounds"])
                    self.assertEqual(board["tail"]["side"], side)
                    # The tail reaches the edge of the board on the tail side.
                    self.assertAlmostEqual(max(_dot(c, out) for c in tail), max(_dot(p, out) for p in outline), delta=EPS)
                    copper = board["layers"]["top_copper"]
                    self._extreme({pad["pin"]: _middle(gc.bounds(pad)) for pad in copper["pads"]}, pin_end, 1, f"pin 1 of {board['id']}")
                    electrodes = {electrode["net"]: _middle(gc.bounds(electrode)) for electrode in copper["electrodes"]}
                    if board["role"] == "rows":
                        self._extreme(electrodes, row_end, "ROW_01", "ROW_01")
                        # The Row tail is flush with the board edge at one end only: a corner.
                        opposite = (-lateral[0], -lateral[1])
                        self.assertAlmostEqual(max(_dot(c, lateral) for c in tail), max(_dot(p, lateral) for p in outline), delta=EPS)
                        self.assertLess(max(_dot(c, opposite) for c in tail), max(_dot(p, opposite) for p in outline) - 1.0)
                    else:
                        self._extreme(electrodes, column_end, "COL_01", "COL_01")

    def test_stack_table_matches_the_turned_over_view(self) -> None:
        rows = [row for row in _rows(_section(self.text, "The assembly preview")) if re.match(r"`(rows|columns)`", row[0])]
        self.assertEqual(len(rows), 2)
        for row in rows:
            top = re.match(r"`(\w+)`", row[0]).group(1)
            design = {"matrix": {"rows": 3, "columns": 5}, "role_mapping": {"top": top, "bottom": "columns" if top == "rows" else "rows"},
                      "routing": {"row_sides": "channel"}}  # the table's straight Row channel
            result = generate_design(design)
            self.assertTrue(result["ok"], result["validation"]["errors"])
            views = {}
            for board in result["boards"].values():
                # Seen from above, registered on the taxel field; the physical top board is
                # turned over about its tail axis (vertical for bottom tails): X mirrored.
                active = board["grid_registration"]["active_region"]
                center = (active["x"] + active["width"] / 2, active["y"] + active["height"] / 2)
                sign = -1.0 if board["physical_side"] == "top" else 1.0

                def view(point, center=center, sign=sign):
                    return (sign * (point[0] - center[0]), point[1] - center[1])

                copper = board["layers"]["top_copper"]
                views[board["role"]] = {
                    "state": "turned over" if sign < 0 else "face up",
                    "tail": view(_middle(_box(board["tail"]["bounds"]))),
                    "pins": {pad["pin"]: view(_middle(gc.bounds(pad))) for pad in copper["pads"]},
                    "electrodes": {electrode["net"]: view(_middle(gc.bounds(electrode))) for electrode in copper["electrodes"]},
                }
            with self.subTest(top=top):
                for role, cell in (("rows", row[1]), ("columns", row[2])):
                    seen = views[role]
                    state, _, items = cell.partition(": ")
                    self.assertEqual(state, seen["state"], role)
                    for item in items.split(", "):
                        vectors = _directions(item)
                        if item.startswith("tail "):
                            for vector in vectors:
                                self.assertGreater(_dot(seen["tail"], vector), 1.0, (role, item))
                        elif item.startswith("pin 1 "):
                            self._extreme(seen["pins"], vectors[0], 1, (role, item))
                        else:
                            net = re.match(r"`((?:ROW|COL)_01)`", item).group(1)
                            self._extreme(seen["electrodes"], vectors[0], net, (role, item))
                # Taxel (1, 1) is the crossing of ROW_01 and COL_01.
                for vector in _directions(row[3]):
                    role, net = ("rows", "ROW_01") if vector[0] == 0.0 else ("columns", "COL_01")
                    self._extreme(views[role]["electrodes"], vector, net, ("taxel (1, 1)", row[3]))

    def test_reader_connectors_are_the_profiles_sources(self) -> None:
        rows = [row for row in _table(_section(self.text, "The reader connectors")) if row[0] in ("rows", "columns")]
        self.assertEqual(len(rows), 2)
        sources = self.profile["sources"]["reader_connectors"]
        pins = {}
        for row in rows:
            role, part = row[0], row[1].split(" (")[0]
            with self.subTest(role=role):
                self.assertIn(part, sources[role])
                self.assertIn(f"-{row[2]}", part)
                self.assertIn("bottom contact", row[3])
                self.assertIn("bottom contact", sources[role])
                # The contact and drawing figures are the ones the profile records for that connector.
                figures = {float(number) for number in re.findall(r"\d+(?:\.\d+)?", " ".join(row[3:]))}
                self.assertLessEqual(figures, {float(number) for number in re.findall(r"\d+(?:\.\d+)?", sources[role])})
            pins[role] = int(row[2])
        self.assertEqual(_quoted(self, self.prose, r"\((\d+) and (\d+) for the FlexiTac reader\)"), (pins["rows"], pins["columns"]))

    def test_quoted_dimensions_match_the_builds(self) -> None:
        default = generate_design(default_design())
        sixteen = generate_design({"connector": {"row_pins": 16}})
        flipped = generate_design({"role_mapping": {"top": "columns", "bottom": "rows"}})
        for result in (default, sixteen, flipped):
            self.assertTrue(result["ok"], result["validation"]["errors"])
        row, column = default["boards"]["row"], default["boards"]["column"]
        connector, stackup, text = self.profile["connector"], self.profile["stackup"], self.prose
        self.assertEqual(
            _quoted(
                self, text,
                r"width \(P \+ 1\) x ([\d.]+) mm, contacts ([\d.]+) x ([\d.]+) mm starting ([\d.]+) mm from the tip, "
                r"the outer contact centres ([\d.]+) mm from the tail sides, R([\d.]+) tip corners",
            ),
            (connector["pad_pitch_mm"], connector["pad_width_mm"], connector["contact_length_mm"], connector["contact_tip_clearance_mm"],
             connector["contact_center_to_side_edge_mm"], connector["tail_tip_corner_radius_mm"]),
        )
        self.assertEqual(_quoted(self, text, r"and a ([\d.]+) mm bottom PI stiffener flush with the tip and both sides"), (column["tail"]["stiffener_length_mm"],))
        self.assertEqual(_quoted(self, text, r"The default Column tail \((\d+) pins\) is ([\d.]+) mm wide"), (column["tail"]["connector_pins"], column["tail"]["width_mm"]))
        self.assertEqual(
            _quoted(self, text, r"The default Row tail has (\d+) positions \((\d+) rows\): ([\d.]+) mm wide, like the approved 12-pin reference tail"),
            (row["tail"]["connector_pins"], default["design"]["matrix"]["rows"], row["tail"]["width_mm"]),
        )
        reference = float(re.search(r"12-pin tail ([\d.]+) mm", self.profile["sources"]["reference_design"]).group(1))
        self.assertEqual(reference, row["tail"]["width_mm"])
        self.assertEqual(
            _quoted(self, text, r"The contacts start ([\d.]+) mm from the tip \(the JLC copper-to-edge rule; the gold-finger rule is ([\d.]+) mm\)"),
            (self.profile["fabrication"]["copper_to_board_edge_mm"], self.profile["fabrication"]["gold_finger_to_board_edge_mm"]),
        )
        self.assertEqual(connector["contact_tip_clearance_mm"], self.profile["fabrication"]["copper_to_board_edge_mm"])
        self.assertEqual(_quoted(self, text, r"the stiffened (\d+) mm zone is rigid"), (column["tail"]["stiffener_length_mm"],))
        self.assertEqual(_quoted(self, text, r"electrodes \(the default stays ([\d.]+) mm\)"), (default["design"]["matrix"]["taxel_width_mm"],))
        pins, width, first, last, first_nc, last_nc = _quoted(
            self, text, r"set connector\.row_pins to (\d+): the tail becomes ([\d.]+) mm wide with contacts (\d+)-(\d+) as isolated NC_(\d+)\.\.NC_(\d+) \(ascending\)"
        )
        board = sixteen["boards"]["row"]
        self.assertEqual((pins, width), (board["tail"]["connector_pins"], board["tail"]["width_mm"]))
        nc = sorted((pad["position"], pad["pin"], pad["net"]) for pad in board["layers"]["top_copper"]["pads"] if pad["kind"] == "connector_nc_pad")
        self.assertEqual(nc, [(pin, pin, f"NC_{pin:02d}") for pin in range(first, last + 1)])
        self.assertEqual((first_nc, last_nc, last), (first, last, pins))
        start, length = connector["contact_tip_clearance_mm"], connector["contact_length_mm"]
        self.assertEqual(_quoted(self, text, r"so ([\d.]+) mm of exposed contact spans ([\d.]+)-([\d.]+) mm from the tip"), (length, start, round(start + length, 2)))
        layers = (stackup["core_polyimide_thickness_mm"], stackup["copper_thickness_mm"], stackup["stiffener_thickness_mm"])
        self.assertEqual(
            _quoted(self, text, r"about ([\d.]+) \(core PI\) \+ ([\d.]+) \(copper\) \+ ([\d.]+) \(PI stiffener\) = ([\d.]+) mm thick"),
            (*layers, round(sum(layers), 3)),
        )
        option, total = _quoted(self, text, r"The ([\d.]+) mm JLC PI option, the default before, would give about ([\d.]+) mm")
        self.assertIn(option, self.profile["fabrication"]["pi_stiffener_thickness_options_mm"])
        self.assertEqual(total, round(layers[0] + layers[1] + option, 3))
        self.assertEqual(_quoted(self, text, r"contact-zone thickness against the connector \(([\d.]+) mm with the ([\d.]+) mm PI stiffener\)"), (round(sum(layers), 3), layers[2]))
        bottom, straight, stiffener, row_straight, twisted = _quoted(
            self, text,
            r"The default ([\d.]+) mm bottom tail leaves ([\d.]+) mm of straight, flexible Column tail beyond its (\d+) mm stiffener "
            r"\(the stiffener_end_clearance record; ([\d.]+) mm if the Row board is at the bottom\), still short for twisting a ([\d.]+) mm wide tail",
        )
        self.assertEqual((bottom, stiffener, twisted), (default["design"]["tail"]["bottom_length_mm"], column["tail"]["stiffener_length_mm"], column["tail"]["width_mm"]))
        self.assertEqual(straight, round(column["verification"]["checks"]["stiffener_end_clearance"]["measured_mm"], 2))
        self.assertEqual(flipped["boards"]["row"]["physical_side"], "bottom")
        self.assertEqual(row_straight, flipped["boards"]["row"]["verification"]["checks"]["stiffener_end_clearance"]["measured_mm"])
        self.assertEqual(_quoted(self, text, r"Lengthen tail\.bottom_length_mm \(up to (\d+) mm\)"), (self.profile["limits"]["maximum_tail_length_mm"],))
        self.assertEqual(_quoted(self, text, r"\(defaults (\d+) and ([\d.]+) mm;"), (default["design"]["tail"]["top_length_mm"], default["design"]["tail"]["bottom_length_mm"]))
        # The gang window stops at the straight part of the tip edge: its lateral expansion.
        (lateral,) = _quoted(self, text, r"the contact window leaves only ([\d.]+) mm of coverlay expansion beside the outer contacts")
        for board in (row, column):
            window = gc.bounds(next(o for o in board["layers"]["top_coverlay_openings"] if o["kind"] == "connector_contact_opening"))
            contacts = [gc.bounds(pad) for pad in board["layers"]["top_copper"]["pads"]]
            margins = (min(box[0] for box in contacts) - window[0], window[2] - max(box[2] for box in contacts))
            self.assertEqual(tuple(round(margin, 6) for margin in margins), (lateral, lateral), board["id"])


class ExportDocumentTests(unittest.TestCase):
    """docs/PHASE2_DIRECT_GERBER.md and README.md: archive members, headers and formats."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = generate_design(default_design())
        cls.exports = build_exports(cls.result)
        cls.members = {key: _members(data) for key, data in cls.exports.items()}
        cls.text = _text(ROOT / "docs" / "PHASE2_DIRECT_GERBER.md")

    def _assert_members(self, rows: list[list[str]], names: list[str]) -> None:
        patterns = [_member_pattern(name) for row in rows for name in re.findall(r"`([^`]+)`", row[0])]
        for name in names:
            self.assertEqual(sum(1 for pattern in patterns if pattern.fullmatch(name)), 1, f"{name} is not documented once")
        for pattern in patterns:
            self.assertTrue(any(pattern.fullmatch(name) for name in names), f"documented {pattern.pattern} is not in the archive")

    def test_board_zip_table_matches_both_board_zips(self) -> None:
        rows = _rows(_section(self.text, "Board ZIP"))
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            members = self.members[key]
            with self.subTest(archive=key):
                self._assert_members(rows, sorted(members))
                for row in rows:
                    (name,) = re.findall(r"`([^`]+)`", row[0])
                    member = next(found for found in members if _member_pattern(name).fullmatch(found))
                    if member.endswith((".GTL", ".GTS", ".GKO", ".GBSL")):
                        function = next(span for span in re.findall(r"`([^`]+)`", row[1]) if "," in span)
                        polarity = "Negative" if "negative" in row[1].lower() else "Positive"
                        lines = members[member].decode("ascii").splitlines()
                        self.assertIn(f"G04 #@! TF.FileFunction,{function}*", lines, member)
                        self.assertIn(f"G04 #@! TF.FilePolarity,{polarity}*", lines, member)
                    formats = re.findall(r"`(tactile-fpc-[a-z-]+/v\d+)`", row[1])
                    if formats:
                        self.assertEqual([json.loads(members[member])["format"]], formats, member)

    def test_gerber_header_lines_are_the_documented_ones(self) -> None:
        block = re.search(r"```text\n(.*?)```", _section(self.text, "Board ZIP"), re.S).group(1).splitlines()
        build_id = self.result["manifest"]["build_id"]
        expected = [re.escape(line).replace("<build_id>", re.escape(build_id)).replace(re.escape("..."), r"[^*]+") for line in block]
        self.assertEqual(len(expected), 4)
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            for name, data in self.members[key].items():
                if not name.endswith((".GTL", ".GTS", ".GKO", ".GBSL")):
                    continue
                lines = data.decode("ascii").splitlines()
                with self.subTest(archive=key, member=name):
                    # One descriptive comment, the X2 attributes, then format and unit.
                    self.assertRegex(lines[0], r"^G04 (?!#@!)")
                    for pattern, line in zip(expected, lines[1:5]):
                        self.assertRegex(line, f"^{pattern}$")
                    self.assertEqual(lines[5:7], ["%FSLAX46Y46*%", "%MOMM*%"])

    def test_review_bundle_table_matches_the_bundle(self) -> None:
        rows = _rows(_section(self.text, "Review bundle"))
        members = self.members["project_review_bundle_zip"]
        # A member of masked and diagonal Row bus builds only is in their bundles (the default's, the bus since
        # P5-diagonal-bus.md section 18), not in the straight Row channel's.
        masked_only = [row for row in rows if "masked and diagonal Row bus builds only" in row[1]]
        self.assertEqual([_code(row[0]) for row in masked_only], ["taxels.csv"])
        self._assert_members(rows, sorted(members))
        channel = generate_design({"routing": {"row_sides": "channel"}})
        self._assert_members([row for row in rows if row not in masked_only], sorted(_members(build_exports(channel)["project_review_bundle_zip"])))
        masked = generate_design({"template_id": "surface_matrix_v1", "matrix": {"rows": 3, "columns": 5, "mask": [[3, 5], [2, 5], [1, 5]]}})
        masked_members = _members(build_exports(masked)["project_review_bundle_zip"])
        self._assert_members(rows, sorted(masked_members))
        diagonal = generate_design({"template_id": "surface_matrix_v1", "matrix": {"rows": 3, "columns": 5}, "routing": {"row_sides": "both"}})
        self._assert_members(rows, sorted(_members(build_exports(diagonal)["project_review_bundle_zip"])))
        header = re.findall(r"`([^`]+)`", masked_only[0][1])[0]
        self.assertEqual(masked_members["taxels.csv"].decode("ascii").splitlines()[0], header.replace(" ", ""))
        self.assertEqual(json.loads(masked_members["manifest.json"])["taxel_map"]["columns"], header.split(", "))
        for row in rows:
            for format_name in re.findall(r"`(tactile-fpc-[a-z-]+/v\d+)`", row[1]):
                (name,) = re.findall(r"`([^`]+)`", row[0])
                self.assertEqual(json.loads(members[name])["format"], format_name, name)
        pinout = next(row for row in rows if _code(row[0]) == "pinout.csv")
        header = re.findall(r"`([^`]+)`", pinout[1])[0]
        records = list(csv.reader(io.StringIO(members["pinout.csv"].decode("ascii"))))
        self.assertEqual(records[0], header.split(", "))
        # "every contact of both boards, top board first, pins ascending"
        sides = [record[-1] for record in records[1:]]
        self.assertEqual(sides, sorted(sides, key=("top", "bottom").index))
        for side in ("top", "bottom"):
            pins = [int(record[0]) for record in records[1:] if record[-1] == side]
            self.assertEqual(pins, sorted(pins))
        self.assertEqual(len(records) - 1, sum(len(board["layers"]["top_copper"]["pads"]) for board in self.result["boards"].values()))

    def test_determinism_table_matches_the_default_archives(self) -> None:
        rows = _rows(_section(self.text, "Determinism"))
        names = exporters.artifact_filenames(self.result)
        expected = {names[key]: (len(data), hashlib.sha256(data).hexdigest()) for key, data in self.exports.items()}
        self.assertEqual({_code(row[0]): (int(row[1]), _code(row[2])) for row in rows}, expected)

    def test_readme_member_lists_match_the_archives(self) -> None:
        readme = _prose(_text(ROOT / "README.md"))
        (listed,) = _quoted(self, readme, r"one Direct Gerber ZIP per FPC \(([^)]*)\)", raw=True)
        items = [item.split()[-1] for item in listed.split(", ")]
        for key in ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip"):
            names = list(self.members[key])
            for name in names:
                self.assertEqual(sum(1 for item in items if name.endswith(item)), 1, name)
            self.assertEqual(len(items), len(names))
        (listed,) = _quoted(self, readme, r"a project review ZIP \(([^)]*)\)", raw=True)
        synonyms = {"derived layout": "derived-layout", "both Gerber ZIPs": "gerbers", "manifest with every digest": "manifest", "order notes": "ORDER_NOTES"}
        groups = {name.split("/")[0].rsplit(".", 1)[0] for name in self.members["project_review_bundle_zip"]}
        self.assertEqual(sorted(synonyms.get(item, item) for item in listed.split(", ")), sorted(groups))


class OrderDocumentTests(unittest.TestCase):
    """The order requirements (stage G) as README, PHASE2, INTEGRATION and the handoff quote them."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_profile()
        cls.records = order_requirements(cls.profile, default_design())

    def test_the_order_sentence_of_each_document_is_the_profiles(self) -> None:
        order, connector = self.profile["order"], self.profile["connector"]
        pattern = (
            r"[Oo]rder each board as a (\d+)-layer, ([\d.]+) mm FPC with ([\d.]+) oz copper and a ([\d.]+) mm PI stiffener at the contacts, "
            r"a \+/-([\d.]+) mm outline tolerance \(a special request\) and (\w+), and check that the ([\d.]+) mm gold fingers "
            r"come out within \+/-([\d.]+) mm \(JLC's trace tolerance is \+/-(\d+)%\)"
        )
        records = {record["id"]: record for record in self.records}
        expected = (
            order["fpc_layers"], order["fpc_thickness_mm"], records["copper_weight"]["values"]["copper_weight_oz"],
            self.profile["stackup"]["stiffener_thickness_mm"], order["outline_tolerance_mm"],
            order["surface_finish"], connector["pad_width_mm"], connector["contact_width_tolerance_mm"],
            round(self.profile["fabrication"]["trace_width_tolerance_fraction"] * 100),
        )
        special = {record["id"]: record["special_request"] for record in self.records}["outline_tolerance"]
        self.assertTrue(special)
        for path in (ROOT / "README.md", ROOT / "docs" / "PHASE2_DIRECT_GERBER.md", ROOT / "docs" / "INTEGRATION.md", HANDOFF):
            with self.subTest(document=path.name):
                self.assertEqual(_quoted(self, _prose(_text(path)), pattern), expected)

    def test_phase2_table_lists_every_order_requirement(self) -> None:
        rows = _rows(_section(_text(ROOT / "docs" / "PHASE2_DIRECT_GERBER.md"), "Order requirements"))
        self.assertEqual(
            [(_code(row[0]), row[1], row[2]) for row in rows],
            [(record["id"], record["kind"].replace("_", " "), record["requirement"]) for record in self.records],
        )
        # The quoted reasons carry the profile's and the sources' figures.
        prose = _prose(_section(_text(ROOT / "docs" / "PHASE2_DIRECT_GERBER.md"), "Order requirements"))
        figures = set(re.findall(r"\d+\.\d+", " ".join(record["reason"] for record in self.records)))
        self.assertLessEqual(figures, set(re.findall(r"\d+\.\d+", prose)))
        # The quoted trace-tolerance line of a board is the exporter's, for the width it names.
        line, width = _quoted(self, prose, r'"(Trace tolerance: at JLC\'s -\d+% the ([\d.]+) mm fan-out traces [^"]*)"', raw=True)
        self.assertEqual(line, exporters.direct_gerber._trace_tolerance(float(width), self.profile))


class LayoutDocumentTests(unittest.TestCase):
    """docs/LAYOUT_SCHEMA.md: kinds, anchors and fixed values against generated layouts."""

    @classmethod
    def setUpClass(cls) -> None:
        # The default (a window per electrode since its 1.0 mm electrodes of 2026-11-06) and 1.4 mm electrodes (the merged
        # field window of the default before).
        designs = ({}, {"connector": {"row_pins": 14}}, {"matrix": {"columns": 16}}, {"matrix": {"taxel_width_mm": 1.4, "taxel_height_mm": 1.4}})
        cls.results = [generate_design(design) for design in designs]
        cls.boards = [board for result in cls.results for board in result["boards"].values()]
        cls.text = _text(ROOT / "docs" / "LAYOUT_SCHEMA.md")
        cls.prose = _prose(cls.text)
        cls.profile = load_profile()

    def test_anchors_and_item_kinds_match_the_layout(self) -> None:
        for result in self.results:
            self.assertTrue(result["ok"], result["validation"]["errors"])
        copper = [board["layers"]["top_copper"] for board in self.boards]
        openings = [opening for board in self.boards for opening in board["layers"]["top_coverlay_openings"]]
        self.assertIn('"center": x, y is the centre (connector contacts)', self.prose)
        self.assertIn('"lower_left": x, y is the lower-left corner (electrodes and openings)', self.prose)
        self.assertEqual({pad["anchor"] for layer in copper for pad in layer["pads"]}, {"center"})
        self.assertEqual({electrode["anchor"] for layer in copper for electrode in layer["electrodes"]}, {"lower_left"})
        self.assertEqual({opening["anchor"] for opening in openings}, {"lower_left"})
        table = {row[0]: set(re.findall(r"`([^`]+)`", " ".join(row[1:]))) for row in _table(_section(self.text, "`layers.top_copper`"))}
        electrode, route, pad = table["electrode"], table["route"], table["pad (contact)"]
        self.assertTrue("lower_left" in electrode and "center" not in electrode)
        self.assertTrue("center" in pad and "lower_left" not in pad)
        self.assertLessEqual({item["kind"] for layer in copper for item in layer["electrodes"]}, electrode)
        self.assertLessEqual({item["kind"] for layer in copper for item in layer["pads"]}, pad)
        self.assertLessEqual({item["fanout"] for layer in copper for item in layer["routes"]}, route)
        self.assertLessEqual({f'kind: "{item["kind"]}"' for layer in copper for item in layer["routes"]}, route)
        kinds = {_code(row[0]) for row in _rows(_section(self.text, "`layers.top_coverlay_openings`")) if _code(row[0]).endswith("_opening")}
        self.assertEqual(kinds, {opening["kind"] for opening in openings})
        self.assertLessEqual({opening["opening_for"] for opening in openings}, {"row_electrode", "column_electrode", "connector_contacts"})
        self.assertIn("opening_for is the electrode kind or connector_contacts", self.prose)
        for board in self.boards:
            self.assertEqual(board["id"], f"{board['physical_side']}_{board['role']}_fpc")

    def test_fixed_values_match_the_layout(self) -> None:
        width, pitch, bridge, wide, wide_pitch, narrow = _quoted(
            self, self.prose, r"The default design \(([\d.]+) mm electrodes at ([\d.]+) mm pitch, bridges of ([\d.]+) mm\) gets one window per "
            r"electrode; with ([\d.]+) mm electrodes at ([\d.]+) mm pitch \(bridges of ([\d.]+) mm, the default until 2026-11-06\) it gets one "
            r"merged field window per board"
        )
        expansion = self.profile["coverlay"]["coverlay_expansion_mm"]
        for result, (cell, step, gap), kind, count in (
            (self.results[0], (width, pitch, bridge), "sensor_electrode_opening", None),
            (self.results[3], (wide, wide_pitch, narrow), "electrode_field_opening", 1),
        ):
            matrix = result["design"]["matrix"]
            self.assertEqual((cell, step), (matrix["taxel_width_mm"], matrix["pitch_x_mm"]))
            self.assertEqual(gap, round(step - cell - 2 * expansion, 6))
            self.assertEqual(gap >= self.profile["coverlay"]["coverlay_min_bridge_mm"], kind == "sensor_electrode_opening")
            for board in result["boards"].values():
                kinds = [o["kind"] for o in board["layers"]["top_coverlay_openings"]]
                self.assertEqual(kinds.count(kind), len(board["layers"]["top_copper"]["electrodes"]) if count is None else count)
        kind, zone, side, layer, material = _quoted(
            self, self.prose, r'kind: "(\w+)", zone \((\w+) for the connector-zone stiffener, exactly one per board\), side \((\w+)\), layer \((\w+)\), material \((\w+)\)'
        )
        (length,) = _quoted(self, self.prose, r"tail\.stiffener_length_mm \(([\d.]+) mm\) long")
        self.assertEqual(length, self.profile["tail"]["stiffener_length_mm"])
        (drc_version,) = _quoted(self, self.prose, r"verification holds drc_version \(([\w-]+)\)")
        for board in self.boards:
            (stiffener,) = [item for item in board["layers"]["bottom_stiffener"] if item["zone"] == zone]
            self.assertEqual((stiffener["kind"], stiffener["side"], stiffener["layer"], stiffener["material"]), (kind, side, layer, material))
            self.assertEqual((stiffener["thickness_mm"], stiffener["length_mm"]), (self.profile["stackup"]["stiffener_thickness_mm"], length))
            self.assertEqual(board["grid_registration"]["coordinate_system"], "active_region_lower_left")
            self.assertEqual(board["verification"]["drc_version"], drc_version)
        self.assertIn("| `coordinate_system` | `active_region_lower_left` |", self.text)

    def test_quoted_bundle_figures_match_the_layout(self) -> None:
        from engine.layout import row_plan

        # The finger-section spacing of the DRC, required and measured on the default build.
        rule, row, column = _quoted(
            self, self.prose,
            r"A route pair with a wide tail piece keeps the finger-section spacing instead, ([\d.]+) mm, as the traces between the "
            r"contacts do \(measured ([\d.]+) / ([\d.]+) mm on the default build\)",
        )
        records = [self.results[0]["boards"][key]["verification"]["checks"]["route_route_clearance"]["finger_section"] for key in ("row", "column")]
        self.assertEqual([record["required_mm"] for record in records], [rule, rule])
        self.assertEqual([record["measured_mm"] for record in records], [row, column])
        self.assertEqual(rule, round(self.profile["connector"]["pad_pitch_mm"] - self.profile["routing"]["finger_trace_width_mm"], 6))
        # The Row expansion height against the bundle pitch (the bus angle is the cap for every pitch).
        rows, *figures = _quoted(
            self, self.prose,
            r"For (\d+) rows it is ([\d.]+) mm high at the default ([\d.]+) mm pitch, ([\d.]+) mm at ([\d.]+) mm and ([\d.]+) mm at "
            r"([\d.]+) mm, and 0 at ([\d.]+) mm, where no lane moves",
        )
        default = default_design()["routing"]
        self.assertEqual(figures[1], round(default["trace_width_mm"] + default["trace_space_mm"], 6))
        widest_space = self.profile["limits"]["maximum_trace_space_mm"]
        for height, pitch in ((figures[0], figures[1]), (figures[2], figures[3]), (figures[4], figures[5]), (0.0, figures[6])):
            width = round(max(pitch / 2, pitch - widest_space), 6)
            design = check_design({"matrix": {"rows": rows}, "routing": {"trace_width_mm": width, "trace_space_mm": round(pitch - width, 6)}})
            with self.subTest(pitch=pitch):
                self.assertTrue(design["ok"], design["validation"]["errors"])
                self.assertEqual(row_plan(design["design"], self.profile)["expansion_height"], height)


class ReadmeAndPlanTests(unittest.TestCase):
    """Figures that README.md and docs/IMPLEMENTATION_PLAN.md quote from the profile and the default build."""

    def test_quoted_figures_match_the_profile_and_the_default(self) -> None:
        profile, design = load_profile(), default_design()
        connector, routing = profile["connector"], profile["routing"]
        readme = _prose(_text(ROOT / "README.md"))
        matrix = design["matrix"]
        self.assertEqual(matrix["pitch_x_mm"], matrix["pitch_y_mm"])
        self.assertEqual(matrix["taxel_width_mm"], matrix["taxel_height_mm"])
        self.assertEqual(
            _quoted(self, readme, r"Default: (\d+) x (\d+) at ([\d.]+) mm pitch with ([\d.]+) mm electrodes"),
            (matrix["rows"], matrix["columns"], matrix["pitch_x_mm"], matrix["taxel_width_mm"]),
        )
        # The fan-out traces (2026-10-15): the default, the ranges and JLC's rules.
        limits, bundle = profile["limits"], design["routing"]
        self.assertEqual(
            _quoted(self, readme, r"with ([\d.]+) mm electrodes and ([\d.]+) mm fan-out traces at ([\d.]+) mm spacing"),
            (matrix["taxel_width_mm"], bundle["trace_width_mm"], bundle["trace_space_mm"]),
        )
        self.assertEqual(
            _quoted(self, readme, r"\(routing\.trace_width_mm ([\d.]+)-([\d.]+) mm and routing\.trace_space_mm ([\d.]+)-([\d.]+) mm\)"),
            (limits["minimum_trace_width_mm"], limits["maximum_trace_width_mm"], limits["minimum_trace_space_mm"], limits["maximum_trace_space_mm"]),
        )
        self.assertEqual(
            _quoted(self, readme, r"bundle at the trace width \+ spacing \(([\d.]+) mm by default\) and expand again to the ([\d.]+) mm contact pitch"),
            (round(bundle["trace_width_mm"] + bundle["trace_space_mm"], 6), connector["pad_pitch_mm"]),
        )
        self.assertEqual(
            _quoted(self, readme, r"in the tail, they widen to the ([\d.]+) mm gold-finger width"), (routing["finger_trace_width_mm"],)
        )
        self.assertEqual(_quoted(self, readme, r"parallel (\d+) degree diagonals"), (profile["fanout"]["maximum_taper_angle_deg"],))
        minimum = engine.profile.fabrication_minimum(profile)
        self.assertEqual(_quoted(self, readme, r"so the minimum is ([\d.]+) mm for traces, spacing and electrodes alike"), (minimum[0],))
        self.assertEqual(minimum, (limits["minimum_trace_width_mm"], limits["minimum_trace_space_mm"]))
        self.assertEqual(routing["min_electrode_width_mm"], minimum[0])
        fraction = profile["fabrication"]["trace_width_tolerance_fraction"]
        self.assertEqual(
            _quoted(self, readme, r"JLC holds trace widths to \+/-(\d+)%, so a ([\d.]+) mm trace may come out at ([\d.]+) mm"),
            (round(fraction * 100), bundle["trace_width_mm"], round(bundle["trace_width_mm"] * (1 - fraction), 6)),
        )
        self.assertEqual(_quoted(self, readme, r"one fan-out bundle \(up to (\d+) columns\)"), (profile["fanout"]["maximum_channels_per_lane"],))
        self.assertEqual(
            _quoted(self, readme, r"tails for ([\d.]+) mm-pitch ZIF connectors, \(pins \+ 1\) x ([\d.]+) mm wide with ([\d.]+) x ([\d.]+) mm contacts, R([\d.]+) tip corners"),
            (connector["pad_pitch_mm"], connector["pad_pitch_mm"], connector["pad_width_mm"], connector["contact_length_mm"], connector["tail_tip_corner_radius_mm"]),
        )
        self.assertEqual(
            _quoted(self, readme, r"and a ([\d.]+) mm bottom PI stiffener; ([\d.]+) mm copper to every edge"),
            (profile["tail"]["stiffener_length_mm"], routing["copper_to_edge_mm"]),
        )
        result = generate_design(design)
        rows = result["boards"]["row"]["tail"]["connector_pins"]
        stackup = profile["stackup"]
        thickness = round(stackup["core_polyimide_thickness_mm"] + stackup["copper_thickness_mm"] + stackup["stiffener_thickness_mm"], 3)
        reader = int(re.search(r"-(\d+)", profile["sources"]["reader_connectors"]["rows"]).group(1))
        self.assertEqual(
            _quoted(self, readme, r"The default Row tail has (\d+) contacts; the FlexiTac reader's row connector has (\d+), so set connector\.row_pins to (\d+)"),
            (rows, reader, reader),
        )
        self.assertEqual(_quoted(self, readme, r"The contact zone is about ([\d.]+) mm thick with the ([\d.]+) mm stiffener"), (thickness, stackup["stiffener_thickness_mm"]))
        zone = {record["id"]: record for record in order_requirements(profile, default_design())}["contact_zone"]["values"]["contact_zone_thickness_mm"]
        self.assertEqual(thickness, zone)
        plan = _prose(_text(ROOT / "docs" / "IMPLEMENTATION_PLAN.md"))
        limits = profile["limits"]
        self.assertEqual(
            _quoted(
                self, plan,
                r"([\d.]+) mm gold-finger traces, a ([\d.]+)-([\d.]+) mm fan-out trace width, ([\d.]+)-([\d.]+) mm fan-out spacing and ([\d.]+) mm contact pitch",
            ),
            (routing["finger_trace_width_mm"], limits["minimum_trace_width_mm"], limits["maximum_trace_width_mm"],
             limits["minimum_trace_space_mm"], limits["maximum_trace_space_mm"], connector["pad_pitch_mm"]),
        )
        bundle = design["routing"]
        self.assertEqual(
            _quoted(self, plan, r"within these limits, ([\d.]+) / ([\d.]+) mm by default; JLC's minimum for the ordered 1 oz copper is 4/4 mil, ([\d.]+) mm"),
            (bundle["trace_width_mm"], bundle["trace_space_mm"], routing["min_electrode_width_mm"]),
        )
        self.assertEqual(
            _quoted(self, plan, r"width \(pins \+ 1\) x ([\d.]+) mm, ([\d.]+) x ([\d.]+) mm contacts from ([\d.]+) mm behind the tip, R([\d.]+) tip corners"),
            (connector["pad_pitch_mm"], connector["pad_width_mm"], connector["contact_length_mm"], connector["contact_tip_clearance_mm"], connector["tail_tip_corner_radius_mm"]),
        )
        self.assertEqual(
            _quoted(self, plan, r"\(([\d.]+) mm expansion, merged where a bridge would be under ([\d.]+) mm\) and ([\d.]+) mm copper-to-edge"),
            (profile["coverlay"]["coverlay_expansion_mm"], profile["coverlay"]["coverlay_min_bridge_mm"], routing["copper_to_edge_mm"]),
        )
        self.assertEqual(
            _quoted(self, plan, r"a bottom polyimide stiffener at ([\d.]+) mm over a ([\d.]+) mm connector zone"),
            (stackup["stiffener_thickness_mm"], profile["tail"]["stiffener_length_mm"]),
        )
        checks = len(result["boards"]["row"]["verification"]["checks"])
        self.assertEqual(_quoted(self, plan, r"whole-board DRC \((\d+) records per board\)"), (checks,))

    def test_ci_description_matches_the_workflow(self) -> None:
        if not WORKFLOW.is_file():
            self.skipTest("the CI workflow lives at the repository root, outside this copy of the project")
        workflow = _text(WORKFLOW)
        versions = tuple(re.findall(r'"([\d.]+)"', re.search(r"python-version: \[([^\]]*)\]", workflow).group(1)))
        for path in (ROOT / "README.md", HANDOFF):
            with self.subTest(document=path.name):
                self.assertEqual(_quoted(self, _prose(_text(path)), r"CI \([^)]*\) runs the suite on Python ([\d.]+) and ([\d.]+)", raw=True), versions)
        for command in ("python -B -m unittest discover -s tests", "python -B tools/mutation_check.py --check", "node --check web/app.js"):
            self.assertIn(command, workflow)


class HandoffTests(unittest.TestCase):
    """claude/APP_HANDOFF.md and tools/README.md: the test map and the mutation catalogue."""

    def test_test_map_matches_the_suite(self) -> None:
        section = _section(_text(HANDOFF), "Tests and tools")
        tests, modules = _quoted(self, _prose(section), r"(\d+) tests in (\d+) modules")
        names = sorted(path.stem for path in (ROOT / "tests").glob("test_*.py"))
        suite = unittest.TestLoader().discover(str(ROOT / "tests"), top_level_dir=str(ROOT / "tests"))
        self.assertEqual((tests, modules), (suite.countTestCases(), len(names)), "update the test count of claude/APP_HANDOFF.md")
        listed = {name for row in _rows(section) for name in re.findall(r"`(test_\w+)`", row[0])}
        self.assertEqual(listed, set(names), "every test module has a row in the handoff's test map")

    def test_every_catalogue_edit_still_applies(self) -> None:
        # CI runs tools/mutation_check.py --check; the suite checks the same, so a code change
        # that leaves a mutant's old text behind fails here before it is pushed.
        if os.environ.get("FPC_MUTANT"):
            self.skipTest(f"inside mutation_check.py, whose copy carries the edit of {os.environ['FPC_MUTANT']}")
        catalogue = _mutation_catalogue()
        # The runner knows this test by name: its failure in a mutant run marks a broken handshake.
        self.assertEqual(catalogue._CATALOGUE_TEST, f"{type(self).__name__}.{self._testMethodName}")
        ids = [mutant.id for mutant in catalogue.MUTANTS]
        self.assertEqual(sorted({identifier for identifier in ids if ids.count(identifier) > 1}), [], "duplicate mutant ids")
        # The public copy's CI (tools/export_public.py PUBLIC) runs this check too, so every edited file is a public one
        # (the integration's review of 2026-11-05: a mutant of the private tools/library_import.py was stale there).
        spec = importlib.util.spec_from_file_location("fpc_export_public", ROOT / "tools" / "export_public.py")
        export_public = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(export_public)
        private = sorted({path for mutant in catalogue.MUTANTS for path, _, _ in mutant.edits
                          if not any(path == root or path.startswith(root + "/") for root in export_public.PUBLIC)})
        self.assertEqual(private, [], "a mutant edits a file outside export_public.PUBLIC")
        stale = {mutant.id: catalogue._problems(mutant) for mutant in catalogue.MUTANTS}
        self.assertEqual({identifier: problems for identifier, problems in stale.items() if problems}, {})

    def test_mutation_summary_matches_the_catalogue(self) -> None:
        catalogue = _mutation_catalogue()
        survivors = [mutant for mutant in catalogue.MUTANTS if mutant.expect == "survive"]
        prose = _prose(_text(HANDOFF))
        # The catalogue's totals: the mutants expected killed (each run on its own when added; a full run is rare).
        total, killed = _quoted(self, prose, r"Catalogue of [\d-]+: (\d+) mutants, (\d+) expected killed")
        self.assertEqual((total, killed), (len(catalogue.MUTANTS), len(catalogue.MUTANTS) - len(survivors)))
        count, equivalent, equivalent_ids, browser, browser_ids = _quoted(
            self, prose, r"The (\d+) survivors are justified in the catalogue: (\d+) equivalent \(([^)]*)\) and (\d+) browser-only \(([^)]*)\)", raw=True
        )
        expected_equivalent = [mutant.id for mutant in survivors if mutant.reason.startswith("equivalent")]
        expected_browser = [mutant.id for mutant in survivors if mutant.reason.startswith("out of scope: browser")]
        self.assertEqual(int(count), len(survivors))
        self.assertEqual((int(equivalent), equivalent_ids.split(", ")), (len(expected_equivalent), expected_equivalent))
        self.assertEqual((int(browser), browser_ids.split(", ")), (len(expected_browser), expected_browser))
        # The audit's baseline set: one entry per audit mutant id (variants share it), C1 extras apart.
        baseline = {mutant.origin for mutant in catalogue.AUDIT if mutant.origin.startswith("audit ")}
        for path in (HANDOFF, ROOT / "tools" / "README.md"):
            with self.subTest(document=path.name):
                self.assertEqual(set(re.findall(r"audit's (\d+) baseline mutants", _prose(_text(path)))), {str(len(baseline))})


class SnippetTests(unittest.TestCase):
    def test_python_snippets_of_the_documents_run(self) -> None:
        for path in DOCUMENTS:
            for index, code in enumerate(re.findall(r"```python\n(.*?)```", _text(path), re.S)):
                with self.subTest(document=path.name, snippet=index):
                    # A snippet may use `design` for "your design".
                    exec(compile(code, f"{path.name} snippet {index}", "exec"), {"design": default_design()})


class HygieneTests(unittest.TestCase):
    def test_relative_links_resolve_inside_the_project(self) -> None:
        for path in DOCUMENTS:
            for target in _LINK.findall(_text(path)):
                if re.match(r"[a-z]+:", target) or target.startswith("<"):
                    continue
                file, _, anchor = target.partition("#")
                destination = (path.parent / file).resolve() if file else path
                if ROOT not in destination.parents and destination != ROOT:
                    continue  # outside the project (e.g. the workspace root): not checked here
                with self.subTest(document=path.name, link=target):
                    # Linked files must be committed with the documents (e.g. claude/verification/).
                    self.assertTrue(destination.exists(), f"{path.name} links to {destination}, which is missing: commit it or fix the link")
                    if anchor and destination.suffix == ".md":
                        self.assertIn(anchor, _anchors(destination))

    def test_documents_quote_no_host_specific_paths(self) -> None:
        # Home directories (POSIX, macOS, Windows drives with either slash) and the audit's scratch tree.
        host_specific = re.compile(r"/home/\w|/Users/\w|\b[A-Za-z]:[\\/]\w|/tmp/fpc_audit")
        for sample in ("/home/ubuntu/x", "/Users/me/x", "C:\\Users\\me", "D:/work/fpc", "/tmp/fpc_audit/x"):
            self.assertIsNotNone(host_specific.search(sample), sample)
        for path in DOCUMENTS:
            with self.subTest(document=path.name):
                self.assertIsNone(host_specific.search(_text(path)))

    def test_pyproject_declares_python_3_9_and_no_dependencies(self) -> None:
        text = _text(ROOT / "pyproject.toml")
        self.assertRegex(text, r'(?m)^requires-python = ">=3\.9"$')
        self.assertRegex(text, r"(?m)^dependencies = \[\]$")
        version = re.search(r'(?m)^version = "([0-9.]+)"$', text).group(1)
        self.assertEqual(version, GENERATOR_VERSION.rpartition("/")[2])


if __name__ == "__main__":
    unittest.main()
