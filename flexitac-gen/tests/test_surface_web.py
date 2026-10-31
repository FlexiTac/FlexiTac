"""CAD mode in the browser (SPEC C-D1, C-D4): static checks of web/ that need no browser.

- The vendored three.js files keep the SHA-256 recorded in web/vendor/three/NOTICE.md
  (only OrbitControls.js is patched, to import ./three.module.js); the coin photo and the
  UMI finger (CAD mode's default part) keep the SHA-256 of their NOTICE.md.
- index.html loads web/cad/main.js as a module next to the classic app.js; the CAD
  controls live outside #designForm and carry no name/data-field of the design form;
  the mode switch is a radio group, not a tablist; the CAD SVG has no aria-label; the
  3D view has a role, the live regions are only the status lines.
- app.js dispatches only the two document events of the CAD hook and owns the design
  template ("fpc:mode", "fpc:template-info", "fpc:apply-design"); web/cad/ neither
  patches fetch nor posts to the generator or the validator itself.
- web/cad/main.js does not import three.js (viewer.js does, lazily).
- The fit options of the Configure step are fit options of surface.fit, with its choices
  and defaults; the selection presets, candidate lists, template ids, caps and limits
  copied into web/cad/ are the server's.

The behaviour is checked in a browser by tools/browser/cad_checks.py.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
VENDOR = WEB / "vendor" / "three"
CAD = WEB / "cad"
CAD_SCRIPTS = ("main.js", "viewer.js", "api.js", "stl.js", "border.js")


class _Page(HTMLParser):
    """Elements with their attributes and the stack of enclosing ids."""

    VOID = {"input", "meta", "link", "br", "img", "hr", "source", "area", "base", "col", "embed", "param", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.elements: list = []
        self._stack: list = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.elements.append((tag, attributes, [entry[1] for entry in self._stack if entry[1]]))
        if tag not in self.VOID:
            self._stack.append((tag, attributes.get("id")))

    def handle_startendtag(self, tag, attrs):
        self.elements.append((tag, dict(attrs), [entry[1] for entry in self._stack if entry[1]]))

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                break


def _page() -> _Page:
    parser = _Page()
    parser.feed((WEB / "index.html").read_text(encoding="utf-8"))
    return parser


class VendoredThreeTests(unittest.TestCase):
    def test_vendored_files_match_the_notice(self) -> None:
        notice = (VENDOR / "NOTICE.md").read_text(encoding="utf-8")
        rows = dict(re.findall(r"^\| `([\w.]+)` \|[^|]*\| `([0-9a-f]{64})` \|$", notice, re.MULTILINE))
        self.assertEqual(sorted(rows), ["LICENSE", "OrbitControls.js", "three.core.js", "three.module.js"])
        for name, digest in rows.items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((VENDOR / name).read_bytes()).hexdigest(), digest)

    def test_vendored_coin_photo_matches_its_notice(self) -> None:
        # The coin for scale's face (app.js COIN.photo): the photo app.js names, with the SHA-256 of its NOTICE.
        coin = WEB / "vendor" / "coin"
        rows = dict(re.findall(r"^\| `([\w.-]+)` \|[^|]*\| `([0-9a-f]{64})` \|$", (coin / "NOTICE.md").read_text(encoding="utf-8"), re.MULTILINE))
        self.assertEqual(sorted(rows), ["us-quarter-obverse.jpg"])
        self.assertEqual(hashlib.sha256((coin / "us-quarter-obverse.jpg").read_bytes()).hexdigest(), rows["us-quarter-obverse.jpg"])
        self.assertIn('"static/vendor/coin/us-quarter-obverse.jpg"', (WEB / "app.js").read_text(encoding="utf-8"))

    def test_vendored_umi_finger_matches_its_notice(self) -> None:
        # CAD mode's default part (web/cad/main.js DEFAULT_PART): the HandUMI finger and its licence, as the NOTICE says.
        umi = WEB / "vendor" / "umi"
        rows = dict(re.findall(r"^\| `([\w.-]+)` \|[^|]*\| `([0-9a-f]{64})` \|$", (umi / "NOTICE.md").read_text(encoding="utf-8"), re.MULTILINE))
        self.assertEqual(sorted(rows), ["LICENSE", "UMI-Soft-Gripper-Finger.stl"])
        for name, digest in rows.items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((umi / name).read_bytes()).hexdigest(), digest)
        self.assertIn('url: "static/vendor/umi/UMI-Soft-Gripper-Finger.stl"', (CAD / "main.js").read_text(encoding="utf-8"))

    def test_the_default_parts_shipped_fit_is_the_engines(self) -> None:
        # CAD mode ships the default part's fit (main.js DEFAULT_PART.fit): its reply must be the engine's for its request
        # (re-run tools/browser/write_default_fit.py after a change of the fit, the template or the page's defaults).
        from surface import api

        umi = WEB / "vendor" / "umi"
        shipped = json.loads((umi / "default-fit.json").read_text(encoding="utf-8"))
        mesh = (umi / "UMI-Soft-Gripper-Finger.stl").read_bytes()
        self.assertEqual(shipped["mesh_sha256"], hashlib.sha256(mesh).hexdigest())
        self.assertEqual(shipped["request"]["name"], "UMI-Soft-Gripper-Finger.stl")
        reply = json.loads(json.dumps(api.fit(shipped["request"], mesh), allow_nan=False))
        self.assertEqual(reply, shipped["reply"], "the shipped fit is stale: re-run tools/browser/write_default_fit.py")
        first = reply["proposals"][0]
        self.assertEqual((first["metrics"]["rows"], first["metrics"]["columns"]), (32, 12))
        main = (CAD / "main.js").read_text(encoding="utf-8")
        self.assertIn('fit: "static/vendor/umi/default-fit.json", tipSide: 2, borderMm: 65', main)

    def test_orbit_controls_imports_the_vendored_module(self) -> None:
        source = (VENDOR / "OrbitControls.js").read_text(encoding="utf-8")
        self.assertIn("} from './three.module.js';", source)
        self.assertNotRegex(source, r"from\s+['\"]three['\"]")


class PageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = _page()

    def test_scripts(self) -> None:
        scripts = [(attributes.get("src"), attributes.get("type")) for tag, attributes, _ in self.page.elements if tag == "script"]
        self.assertEqual(scripts, [("static/backend.js", None), ("static/app.js", None), ("static/cad/main.js", "module")])

    def test_cad_controls_stay_out_of_the_design_form(self) -> None:
        for tag, attributes, ancestors in self.page.elements:
            identifier = attributes.get("id") or ""
            in_form = "designForm" in ancestors
            in_cad = "cadWorkspace" in ancestors or identifier == "cadWorkspace" or "modePicker" in ancestors
            with self.subTest(tag=tag, id=identifier):
                self.assertFalse(in_form and (in_cad or identifier.startswith("cad")))
                if in_cad:
                    self.assertNotIn("data-field", attributes)
                    if tag in ("input", "select"):
                        # A name is only used to group radios.
                        self.assertTrue("name" not in attributes or attributes.get("type") == "radio", attributes)

    def test_workspace_is_hidden_until_cad_mode(self) -> None:
        workspace = [attributes for tag, attributes, _ in self.page.elements if attributes.get("id") == "cadWorkspace"]
        self.assertEqual(len(workspace), 1)
        self.assertIn("hidden", workspace[0])
        ancestors = [ancestors for _, attributes, ancestors in self.page.elements if attributes.get("id") == "cadWorkspace"][0]
        self.assertIn("workbench", ancestors)

    def test_mode_switch_is_a_radio_group_not_a_tablist(self) -> None:
        radios = [attributes for tag, attributes, ancestors in self.page.elements if tag == "input" and "modePicker" in ancestors]
        self.assertEqual([(radio.get("type"), radio.get("name"), radio.get("value")) for radio in radios],
                         [("radio", "appMode", "rect"), ("radio", "appMode", "cad")])
        tablists = [ancestors for tag, attributes, ancestors in self.page.elements if attributes.get("role") == "tablist"]
        self.assertEqual(len(tablists), 2)
        self.assertFalse(any("cadWorkspace" in ancestors or "modePicker" in ancestors for ancestors in tablists))

    def test_no_labelled_svg_in_cad_mode(self) -> None:
        # tools/browser/ui_checks.py expects exactly the six labelled board SVGs.
        for tag, attributes, ancestors in self.page.elements:
            if tag == "svg" and "cadWorkspace" in ancestors:
                self.assertNotIn("aria-label", attributes)

    def test_ids_are_unique(self) -> None:
        ids = [attributes["id"] for _, attributes, _ in self.page.elements if "id" in attributes]
        self.assertEqual(sorted({identifier for identifier in ids if ids.count(identifier) > 1}), [])


class ScriptTests(unittest.TestCase):
    def test_app_js_dispatches_the_two_cad_events_once(self) -> None:
        source = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertEqual(source.count("document.dispatchEvent("), 2)
        # app.js owns the template (payload() sends state.design.template_id): CAD mode asks through events.
        for event in ("fpc:mode", "fpc:template-info", "fpc:apply-design"):
            with self.subTest(event=event):
                self.assertEqual(source.count(f'document.addEventListener("{event}"'), 1)
        self.assertIn("template_id: state.design?.template_id", source)
        self.assertIn("/api/default?template=", source)
        self.assertEqual(source.count('new CustomEvent("fpc:result", {detail: result})'), 1)
        self.assertEqual(source.count('new CustomEvent("fpc:cleared")'), 1)
        show = source[source.index("function showResult"): source.index("function showFailure")]
        self.assertIn('"fpc:result"', show)
        clear = source[source.index("function clearBoards"): source.index("// -- zoom and pan")]
        self.assertIn('"fpc:cleared"', clear)

    def test_three_is_loaded_lazily_by_the_viewer_only(self) -> None:
        main = (CAD / "main.js").read_text(encoding="utf-8")
        self.assertNotIn("vendor/three", main)
        self.assertIn('import("./viewer.js")', main)
        self.assertNotRegex(main, r'^import .*viewer\.js', "viewer.js must not be imported statically")
        viewer = (CAD / "viewer.js").read_text(encoding="utf-8")
        self.assertIn('from "../vendor/three/three.module.js"', viewer)
        self.assertIn('from "../vendor/three/OrbitControls.js"', viewer)
        for name in CAD_SCRIPTS:
            with self.subTest(file=name):
                self.assertNotRegex((CAD / name).read_text(encoding="utf-8"), r"from\s+['\"]three['\"]")

    def test_cad_code_never_posts_to_the_generator(self) -> None:
        for name in CAD_SCRIPTS:
            source = (CAD / name).read_text(encoding="utf-8")
            with self.subTest(file=name):
                # Neither the plain path nor an escaped one (a regex), and no fetch patch (the old template shim).
                self.assertNotRegex(source, r"api\\?/(generate|validate)")
                self.assertNotRegex(source, r"window\.fetch\s*=")
        main = (CAD / "main.js").read_text(encoding="utf-8")
        self.assertIn('askApp("fpc:apply-design"', main)
        self.assertIn('new CustomEvent("fpc:mode"', main)

    def test_surface_requests_use_the_framed_content_type(self) -> None:
        source = (CAD / "api.js").read_text(encoding="utf-8")
        import app

        self.assertIn(f'SURFACE_CONTENT_TYPE = "{app.SURFACE_CONTENT_TYPE}"', source)
        self.assertIn("setUint32(0, json.length, false)", source)  # big-endian header length

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_node_check(self) -> None:
        version = subprocess.run(["node", "--version"], capture_output=True, text=True, check=False).stdout.strip()
        major = int(re.match(r"v(\d+)", version).group(1)) if re.match(r"v(\d+)", version) else 0
        if major < 22:
            self.skipTest(f"node {version} does not detect ES modules for --check")
        for name in CAD_SCRIPTS:
            with self.subTest(file=name):
                run = subprocess.run(["node", "--check", str(CAD / name)], capture_output=True, text=True, check=False)
                self.assertEqual(run.returncode, 0, run.stderr)


class FitOptionTests(unittest.TestCase):
    def test_configure_controls_are_fit_options_with_its_choices(self) -> None:
        from surface import fit

        page = _page()
        main = (CAD / "main.js").read_text(encoding="utf-8")
        options = {}
        current = None
        choices: dict = {}
        for tag, attributes, ancestors in page.elements:
            if "cadConfig" not in ancestors:
                continue
            if "data-option" in attributes:
                current = attributes["data-option"]
                options[current] = (tag, attributes)
                choices[current] = []
            elif tag == "option" and current is not None and options[current][0] == "select" and "disabled" not in attributes:
                # A disabled option is a display state, never chosen nor sent (Row traces' "Straight channel" under
                # Whole board, the P5d/P5e repair).
                choices[current].append(attributes.get("value"))
        self.assertTrue(set(options) <= set(fit.DEFAULT_OPTIONS), sorted(set(options) - set(fit.DEFAULT_OPTIONS)))
        # No control for what CAD mode fits with and no longer chooses (P5-diagonal-bus.md section 26.16: the field
        # follows the selected area; rectangles and the generic template are the rectangular mode's).
        self.assertFalse(set(options) & set(fit.CAD_ONLY), sorted(set(options) & set(fit.CAD_ONLY)))
        for key, (tag, attributes) in options.items():
            with self.subTest(option=key):
                if tag == "select":
                    try:
                        fit.parse_options({key: "__not_a_choice__"})
                    except Exception as error:  # noqa: BLE001 - the message names the choices
                        allowed = re.search(r"must be one of (.+)\.$", str(error))
                        self.assertIsNotNone(allowed, str(error))
                        self.assertEqual(sorted(choices[key]), sorted(allowed.group(1).split(", ")))
                    self.assertEqual(choices[key][0], fit.DEFAULT_OPTIONS[key], "the first choice is the server's default")
                else:
                    # The defaults are the server's (main.js lowers Max columns to the form limits of the template),
                    # but Max rows and Max columns: the user's default of 2026-10-30 (main.js FIT_DEFAULT_MAX, 32), within
                    # the server's default, which stays their maximum.
                    value = float(attributes["value"])
                    if key in ("max_rows", "max_columns"):
                        self.assertEqual(value, float(_js_constant(main, "FIT_DEFAULT_MAX")))
                        self.assertEqual(float(attributes["max"]), fit.DEFAULT_OPTIONS[key])
                    else:
                        self.assertEqual(value, fit.DEFAULT_OPTIONS[key])
                    self.assertEqual(fit.parse_options({key: int(value) if attributes.get("step") == "1" else value})[key], value)


def _js_constant(source: str, name: str) -> str:
    match = re.search(rf"^(?:export )?const {name} = (.+?);$", source, re.MULTILINE)
    if not match:
        raise AssertionError(f"const {name} not found")
    return match.group(1)


class ServerCopyTests(unittest.TestCase):
    """Values web/cad/ copies from the server stay the server's."""

    def setUp(self) -> None:
        self.main = (CAD / "main.js").read_text(encoding="utf-8")
        self.page = _page()

    def _options(self, select_id: str) -> list:
        values = []
        inside = False
        for tag, attributes, ancestors in self.page.elements:
            if attributes.get("id") == select_id:
                inside = True
                continue
            if inside and tag == "option" and select_id in ancestors:
                values.append(attributes.get("value"))
        return values

    def _radios(self, name: str) -> list:
        return [attributes.get("value") for tag, attributes, _ in self.page.elements if tag == "input" and attributes.get("name") == name]

    def test_presets_are_the_selection_presets(self) -> None:
        from surface import select

        expected = {name: [preset["theta_d_deg"], preset["theta_c_deg"], preset.get("min_radius_mm", 0.0)] for name, preset in select.PRESETS.items()}
        literal = _js_constant(self.main, "PRESETS")
        found = {name: [float(value) for value in values.split(",")] for name, values in re.findall(r"(\w+): \[([^\]]+)\]", literal)}
        self.assertEqual(found, expected)
        self.assertEqual(sorted(value for value in self._options("cadPreset") if value != "custom"), sorted(select.PRESETS))
        self.assertIn("custom", self._options("cadPreset"))

    def test_candidate_lists_are_the_inspect_candidates(self) -> None:
        from surface import api
        from tests.surface_fixtures import box, stl_bytes

        reply = api.inspect({}, stl_bytes(box()))
        # No candidate list on the page since 2026-10-30: the state dump names the kinds (the browser checks pick by them).
        kinds = re.search(r'candidates: Object\.fromEntries\(\[([^\]]+)\]', self.main).group(1)
        self.assertEqual(sorted(re.findall(r'"(\w+)"', kinds)), sorted(reply["candidates"]))
        self.assertEqual(self._radios("cadCandidateKind"), [])

    def test_template_ids_caps_and_arcs_are_the_fit_module_values(self) -> None:
        from surface import fit

        # CAD mode fits on the surface template only (section 26.16): its id, and no Board rules select.
        self.assertEqual(_js_constant(self.main, "SURFACE_TEMPLATE_ID"), f'"{fit.TEMPLATES[fit.CAD_ONLY["template"]]}"')
        self.assertEqual(self._options("cadTemplate"), [])
        self.assertEqual(int(_js_constant(self.main, "FIT_MAX_ROWS")), fit.MAX_ROWS)
        self.assertEqual(int(_js_constant(self.main, "FIT_MAX_COLUMNS")), fit.MAX_COLUMNS)
        self.assertEqual(float(_js_constant(self.main, "ARC_HALF_LENGTH_MM")), fit.ARC_HALF_LENGTH_MM)
        self.assertEqual(float(_js_constant(self.main, "ARC_WHEN_SIDES_SHORTER_MM")), fit.ARC_WHEN_SIDES_SHORTER_MM)

    def test_cad_mode_has_no_rectangle_controls(self) -> None:
        # The user's decision of 2026-10-26 (P5-diagonal-bus.md section 26.16): no Field shape, no Board rules, no Largest
        # rectangle border tool; what CAD mode generates depends on the selected area only.
        html = (CAD.parent / "index.html").read_text(encoding="utf-8")
        border = (CAD / "border.js").read_text(encoding="utf-8")
        for control in ("cadShape", "cadTemplate", "cadBorderRect"):
            self.assertNotIn(f'id="{control}"', html)
            self.assertNotIn(f'"{control}"', self.main)
        for source in (html, self.main, border):
            for text in ("Largest rectangle", "Field shape", "Board rules", "Rectangular board rules", "largestRectangle", "syncShape"):
                self.assertNotIn(text, source)
        ids = {attributes.get("id") for _, attributes, _ in self.page.elements}
        self.assertTrue({"cadBorderReset", "cadBorderInset", "cadContainment", "cadRowSides"} <= ids)

    def test_size_limits_are_the_server_limits(self) -> None:
        import app
        from surface import mesh

        stl = (CAD / "stl.js").read_text(encoding="utf-8")
        self.assertEqual(int(_js_constant(stl, "MAX_FACETS").replace("_", "")), mesh.MAX_FACETS)
        api_js = (CAD / "api.js").read_text(encoding="utf-8")
        self.assertEqual(eval(_js_constant(api_js, "MAX_SURFACE_BYTES"), {}), app.MAX_SURFACE_BYTES)  # noqa: S307 - a product of literals


class AccessibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = _page()

    def test_the_3d_view_has_a_role_and_its_help(self) -> None:
        view = [attributes for _, attributes, _ in self.page.elements if attributes.get("id") == "cadView"][0]
        self.assertEqual(view.get("role"), "application")
        self.assertEqual(view.get("aria-describedby"), "cadHelp")

    def test_only_the_status_lines_are_live(self) -> None:
        # <output> is a live region: the slider values and the state dump must not be.
        outputs = [attributes.get("id") for tag, attributes, ancestors in self.page.elements if tag == "output" and "cadWorkspace" in ancestors]
        self.assertEqual(outputs, ["cadStatus", "cadProbeOut"])
        state = [(tag, attributes) for tag, attributes, _ in self.page.elements if attributes.get("id") == "cadState"][0]
        self.assertEqual(state[0], "pre")
        self.assertIn("hidden", state[1])


if __name__ == "__main__":
    unittest.main()
