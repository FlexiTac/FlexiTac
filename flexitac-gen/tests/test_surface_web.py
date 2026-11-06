"""CAD mode in the browser (SPEC C-D1, C-D4): static checks of web/ that need no browser.

- The vendored three.js files keep the SHA-256 recorded in web/vendor/three/NOTICE.md
  (only OrbitControls.js is patched, to import ./three.module.js); the coin photo and the
  UMI finger (CAD mode's default part) keep the SHA-256 of their NOTICE.md.
- index.html loads web/cad/main.js as a module next to the classic app.js; the CAD
  controls live outside #designForm and carry no name/data-field of the design form;
  the mode switch is a radio group, not a tablist; the CAD SVG has no aria-label; the
  3D view has a role, the live regions are only the status lines.
- The guide's switch and the two folds beyond the basic flow are named "Advanced
  Customization", the form's fold inside it "More options" as the fit's (the user's
  request of 2026-11-04), as are main.js's two lines naming them.
- app.js dispatches only the two document events of the CAD hook and owns the design
  template ("fpc:mode", "fpc:template-info", "fpc:apply-design"; "fpc:board-art", the boards'
  art for the sensor on the part, since 2026-11-05); web/cad/ neither patches fetch nor posts
  to the generator or the validator itself.
- web/cad/main.js does not import three.js (viewer.js and onpart.js do, lazily, and studio.js,
  the studio both draw in since 2026-11-05); drape.js, the sensor on the part's geometry, is pure
  (no three.js, no DOM).
- The stacked card's second figure, the sensor on the part (the user's request of
  2026-11-05), is a sibling of #stackedPreview after it, a .stacked-canvas lightbox of its
  own, with none of the left figure's hooks (data-assembly-mode, its hint) and no SVG.
- No legend or notes under the stacked card's figures (the user's request of 2026-11-06,
  "这部分的解释说明可以去掉"), in either mode, nor the board cards' layer legends (the same
  day, "这个部分也可以去掉,没必要的介绍"): their markup, builders and styles gone.
- Every figure's controls in its frame, top left in one row, no bar above it (the user's
  request of 2026-11-06): the board cards' "3D view" and "2D view" tabs (in that order, the
  2D view selected) and the 2D view's zoom, its level alone in sight; the registration's
  "3D view" and "2D view", the sensor on the part's Exploded and Assembled; Reset view over
  the top right of both stacked figures; the drag hints hidden, each its view's description.
- The fit options of the Configure step are fit options of surface.fit, with its choices
  and defaults; the selection presets, candidate lists, template ids, caps and limits
  copied into web/cad/ are the server's.
- The 3D views' light (app.js lightBoard, lightView; 2026-11-05): app.js's copies of
  onpart.js's lights, studio, coverlay and edge bands' shade are onpart.js's, the sweep's
  tints in styles.css the coverlay's, nothing flattens the views' 3D elements, and the
  light's paths are the outline less its cutouts.

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
# The Library's 3D view's modules too (2026-11-05: its view and stage, ES modules of web/cad/ the Library loads).
CAD_SCRIPTS = ("main.js", "viewer.js", "api.js", "stl.js", "border.js", "drape.js", "onpart.js", "studio.js", "library_view.js", "library_stage.js")


class _Tree(HTMLParser):
    """index.html as nested nodes: each a dict of its tag, attributes, children and text."""

    def __init__(self) -> None:
        super().__init__()
        self.root = {"tag": None, "attrs": {}, "children": [], "text": ""}
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "children": [], "text": ""}
        self._stack[-1]["children"].append(node)
        if tag not in _Page.VOID:
            self._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self._stack[-1]["children"].append({"tag": tag, "attrs": dict(attrs), "children": [], "text": ""})

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index]["tag"] == tag:
                del self._stack[index:]
                break

    def handle_data(self, data):
        for node in self._stack[1:]:
            node["text"] += data


def _nodes(node):
    for child in node["children"]:
        yield child
        yield from _nodes(child)


def _classes(node) -> set:
    return set(node["attrs"].get("class", "").split())


def _one(node, test):
    found = [child for child in _nodes(node) if test(child)]
    assert len(found) == 1, (len(found), [child["attrs"] for child in found][:4])
    return found[0]


def _elements(node) -> list:
    # Its element children (the markup's comments are not nodes).
    return [child for child in node["children"]]


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
        # The look's choice first, in <head> before the style sheets (web/theme.js, 2026-11-06: no flash of the light page).
        self.assertEqual(scripts, [("static/theme.js", None), ("static/backend.js", None), ("static/app.js", None), ("static/cad/main.js", "module")])

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

    def test_the_sensor_on_the_part_sits_beside_the_stacked_view(self) -> None:
        # The user's request of 2026-11-05: the second figure is a sibling of #stackedPreview (the video tools pin and
        # measure that one, the pin-1 checks count its rings and boards), after it (theme_checks reads the first
        # .stacked-canvas), and borrows none of its hooks.
        order = [attributes.get("id") for _, attributes, _ in self.page.elements if attributes.get("id") in ("stackedPreview", "sensorOnPart")]
        self.assertEqual(order, ["stackedPreview", "sensorOnPart"])
        pane = [(attributes, ancestors) for _, attributes, ancestors in self.page.elements if attributes.get("id") == "sensorOnPart"][0]
        self.assertIn("stacked-canvas", pane[0]["class"].split())
        self.assertNotIn("stackedPreview", pane[1])
        self.assertEqual(pane[0].get("tabindex"), "0")
        figure = [index for index, (tag, attributes, _) in enumerate(self.page.elements) if "is-on-part" in attributes.get("class", "").split()]
        self.assertEqual(len(figure), 1)
        inside = []
        for tag, attributes, ancestors in self.page.elements[figure[0] + 1:]:
            if tag == "details":
                break  # #drcPanel, after the stacked card
            inside.append((tag, attributes))
        for tag, attributes in inside:
            with self.subTest(tag=tag, id=attributes.get("id")):
                self.assertNotEqual(tag, "svg")
                for name in ("data-assembly-mode", "data-cad-view", "data-zoom"):
                    self.assertNotIn(name, attributes)
                self.assertNotEqual(attributes.get("role"), "tablist")
                self.assertFalse({"three-d-pane", "view-pane", "zoom-pane"} & set(attributes.get("class", "").split()))
                self.assertNotEqual(attributes.get("id"), "orbitHint")
        reset = [attributes for tag, attributes in inside if attributes.get("id") == "onPartReset"]
        self.assertEqual([(item.get("type"), "disabled" in item) for item in reset], [("button", True)])
        self.assertEqual(sorted(attributes.get("data-on-part-mode") for _, attributes in inside if "data-on-part-mode" in attributes), ["assembled", "exploded"])

    def test_the_stacked_card_has_no_legend_or_notes(self) -> None:
        # The user's request of 2026-11-06 ("这部分的解释说明可以去掉"): the layers' keys under both figures, the explode's
        # note and "About this view" gone from the page, in both modes (Rectangular showed the same keys and notes), with
        # what only built or styled them; the figures, their pin-1 rings and coin and the header line stay (the board
        # cards' own legends went too on 2026-11-06: test_the_board_cards_have_no_layer_legend).
        ids = {attributes.get("id") for _, attributes, _ in self.page.elements}
        for gone in ("assemblyLegend", "onPartLegend", "assemblyMore", "assemblyNotes", "assemblyRowBus"):
            self.assertNotIn(gone, ids)
        self.assertTrue({"stackedPreview", "sensorOnPart", "assemblyHeader"} <= ids)
        card = [index for index, (tag, attributes, _) in enumerate(self.page.elements) if "stacked-review" in attributes.get("class", "").split()]
        self.assertEqual(len(card), 1)
        for tag, attributes, ancestors in self.page.elements[card[0] + 1:]:
            if tag == "details" and attributes.get("id") == "drcPanel":
                break
            self.assertNotEqual(tag, "details", attributes)
        sources = {name: (WEB / name).read_text(encoding="utf-8") for name in ("index.html", "app.js", "cad/main.js", "styles.css", "theme.css")}
        for name, text in sources.items():
            for word in ("assemblyLegend", "onPartLegend", "assemblyMore", "assemblyNotes", "assemblyRowBus", "About this view",
                         "assembly-legend", "assembly-key", "assembly-note", "assembly-more", "on-part-key", "renderOnPartLegend",
                         "rowBusNote", "swatch-pi", "swatch-film", "swatch-part", "coin-key", "upper-key", "lower-key"):
                with self.subTest(file=name, word=word):
                    self.assertIsNone(re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", text))

    def test_the_board_cards_have_no_layer_legend(self) -> None:
        # The user's request of 2026-11-06 ("这个部分也可以去掉,没必要的介绍"): the Row and Column FPC cards' layer legends
        # (top copper, the coverlay's windows, the PI stiffener, pin 1, the coin) gone in both modes and both looks, with
        # their builder, its names of the windows and their swatches; each card ends with its preview, rounded as the
        # card's foot; the drawings keep their coin and pin-1 ring.
        ids = {attributes.get("id") for _, attributes, _ in self.page.elements}
        self.assertFalse({"rowLegend", "columnLegend"} & ids)
        self.assertEqual([attributes for _, attributes, _ in self.page.elements if "layer-legend" in attributes.get("class", "").split()], [])
        tree = _Tree()
        tree.feed((WEB / "index.html").read_text(encoding="utf-8"))
        for key in ("row", "column"):
            card = _one(tree.root, lambda node: node["attrs"].get("id") == f"{key}Card")
            self.assertEqual([child["tag"] if child["tag"] == "header" else child["attrs"].get("class") for child in _elements(card)], ["header", "canvas-wrap"])
        app = (WEB / "app.js").read_text(encoding="utf-8")
        for gone in ("function legend(", "OPENING_NAMES", "Legend`", "swatch", "Coin for scale", "Top copper", "PI stiffener (bottom side)"):
            with self.subTest(gone=gone):
                self.assertNotIn(gone, app)
        board = re.search(r"function renderBoard\(key, board\) \{(.*?)\n  \}", app, re.S).group(1)
        for kept in ("addPin1Ring(flat);", "addPin1Ring(tilted);", "addCoin(flat);", 'coinPlane("oblique-coin")'):
            self.assertIn(kept, board)
        for name in ("styles.css", "theme.css"):
            text = (WEB / name).read_text(encoding="utf-8")
            with self.subTest(file=name):
                self.assertIsNone(re.search(r"\.(?:layer-legend|swatch)(?![\w-])|\.swatch-", text))
        self.assertIn(".board-card > .canvas-wrap { border-radius:0 0 calc(var(--r-lg) - 1px) calc(var(--r-lg) - 1px); }",
                      (WEB / "theme.css").read_text(encoding="utf-8"))

    def test_the_registration_has_no_caption(self) -> None:
        # The user's request of 2026-11-06 ("“Exploded 3D registration review…” 小字去掉"): the small caption at the stacked
        # view's bottom left ("Exploded 3D registration review · visual spacing only · thickness at least 2 px", in the
        # plan view "Plan view · upper board mirrored and translucent, ...") gone in both modes and both views, with what
        # only built, styled or avoided it: renderAssembly's paragraph, setAssemblyMode's texts, styles.css's and
        # theme.css's rules, the split's room for it (test_web_theme) and separatePin1Rings' rule keeping the pin-1 rings
        # off it.  The rings keep every other rule (apart, off the other triangle, each round its own, in the view); the
        # board cards' oblique view keeps its own caption (it says the thickness is drawn at least 2 px).
        sources = {name: (WEB / name).read_text(encoding="utf-8") for name in ("index.html", "app.js", "cad/main.js", "styles.css", "theme.css")}
        for name, text in sources.items():
            for word in ("assembly-caption", "registration review", "visual spacing only", "Plan view ·", "as seen through from above ·"):
                with self.subTest(file=name, word=word):
                    self.assertNotIn(word, text)
        app = sources["app.js"]
        render = _js_function(app, "renderAssembly")[2]
        self.assertIn('target.replaceChildren(scene, svgEl("svg", {class: "pin1-overlay", "aria-hidden": "true", focusable: "false"}));', render)
        self.assertNotIn("caption", _js_function(app, "setAssemblyMode")[2])
        rings = _js_function(app, "separatePin1Rings")[2]
        self.assertNotIn("caption", rings)
        for kept in ("const apart = (a, b) =>", "const clear = (ring, box) =>", "const own = (ring, mine, other) =>", "const holds = (ring, mine) =>",
                     "const shown = (ring, slack) => ring.x - ring.rx >= frame.left + slack && ring.x + ring.rx <= frame.right - slack\n"
                     "      && ring.y - ring.ry >= frame.top + slack && ring.y + ring.ry <= frame.bottom - slack;",
                     "&& own(upper, triangles[0], triangles[1]) && own(lower, triangles[1], triangles[0]) && shown(upper, slack) && shown(lower, slack);"):
            with self.subTest(kept=kept):
                self.assertIn(kept, rings)
        self.assertRegex(sources["styles.css"], r'\.three-d-pane::after \{ content:"Rigid oblique tilt of the top view [^"]*thickness at least 2 px";')


class FigureControlsTests(unittest.TestCase):
    """The figures' controls in their frames (the user's request of 2026-11-06: "这个可以把button做进示意图框里面放在左侧排列
    更简洁; 同时字可以更简略; 而且可以统一, 3d view/2d view"), in both modes (Rectangular has the board cards and the
    registration); tools/browser/ui_checks.py part_figure_controls and cad_checks part_on_part measure them."""

    @classmethod
    def setUpClass(cls) -> None:
        tree = _Tree()
        tree.feed((WEB / "index.html").read_text(encoding="utf-8"))
        cls.root = tree.root
        cls.app = (WEB / "app.js").read_text(encoding="utf-8")
        cls.styles = (WEB / "styles.css").read_text(encoding="utf-8")

    def by_id(self, identifier):
        return _one(self.root, lambda node: node["attrs"].get("id") == identifier)

    def test_the_board_cards_controls_sit_in_their_previews_frame(self) -> None:
        # No bar above the preview: its frame (.canvas-wrap) holds the controls first, the tabs ("3D view" before "2D view",
        # the 2D view selected and in the tab order, as the card opens) and the 2D view's zoom (− + Reset, its level).
        self.assertFalse([node for node in _nodes(self.root) if "preview-bar" in _classes(node)])
        for key in ("row", "column"):
            with self.subTest(card=key):
                card = self.by_id(f"{key}Card")
                frame = _one(card, lambda node: "canvas-wrap" in _classes(node))
                children = _elements(frame)
                self.assertEqual([child["attrs"].get("class") for child in children[:1]], ["figure-tools"])
                self.assertEqual([child["attrs"].get("id") for child in children[1:]], [f"{key}Preview", f"{key}Preview3d"])
                tabs, zoom = _elements(children[0])
                self.assertEqual((tabs["attrs"].get("role"), zoom["attrs"].get("id")), ("tablist", f"{key}ZoomTools"))
                self.assertEqual([(tab["attrs"]["id"], tab["text"], tab["attrs"].get("aria-selected"), tab["attrs"].get("tabindex"), tab["attrs"].get("data-mode"))
                                  for tab in _elements(tabs)],
                                 [(f"{key}Tab3d", "3D view", "false", "-1", "3d"), (f"{key}Tab2d", "2D view", "true", None, "2d")])
                self.assertEqual([(node["tag"], node["attrs"].get("data-zoom"), node["text"]) for node in _elements(zoom)],
                                 [("button", "out", "−"), ("button", "in", "+"), ("button", "reset", "Reset"), ("output", None, "1.0×")])
                self.assertEqual(_elements(zoom)[3]["attrs"].get("id"), f"{key}ZoomLevel")

    def test_the_stacked_figures_controls_sit_in_their_frames(self) -> None:
        # The registration: its switch "3D view" (Exploded, as it opens) and "2D view" (the plan) over its frame's top left,
        # Reset view over its top right (shown with the 3D view), the drag hint hidden and still the view's description.
        registration = _one(self.root, lambda node: {"stack-figure", "is-registration"} <= _classes(node))
        tools, pane, reset, hint = _elements(registration)
        self.assertEqual((tools["attrs"].get("class"), pane["attrs"].get("id"), reset["attrs"].get("id"), hint["attrs"].get("id")),
                         ("figure-tools", "stackedPreview", "stackedReset", "orbitHint"))
        switch = _elements(tools)
        self.assertEqual(len(switch), 1)
        self.assertEqual([(button["attrs"].get("data-assembly-mode"), button["text"], button["attrs"].get("aria-pressed")) for button in _elements(switch[0])],
                         [("exploded", "3D view", "true"), ("plan", "2D view", "false")])
        self.assertEqual((reset["tag"], reset["attrs"].get("type"), reset["attrs"].get("class"), "hidden" in reset["attrs"], reset["text"]),
                         ("button", "button", "figure-reset", True, "Reset view"))
        self.assertEqual((pane["attrs"].get("aria-describedby"), hint["tag"], "hidden" in hint["attrs"], hint["text"]),
                         ("orbitHint", "p", True, "Drag to turn · arrow keys · double-click or 0 to reset"))
        # The sensor on the part: Exploded and Assembled (no title: the frame shows the part; its name the pane's), its
        # Reset view as the registration's, its hint hidden.
        on_part = _one(self.root, lambda node: {"stack-figure", "is-on-part"} <= _classes(node))
        tools, pane, reset, hint = _elements(on_part)
        self.assertEqual((tools["attrs"].get("class"), pane["attrs"].get("id"), reset["attrs"].get("id"), hint["attrs"].get("id")),
                         ("figure-tools", "sensorOnPart", "onPartReset", "onPartHint"))
        self.assertEqual([(button["attrs"].get("data-on-part-mode"), button["text"], button["attrs"].get("aria-pressed")) for button in _elements(_elements(tools)[0])],
                         [("exploded", "Exploded", "true"), ("assembled", "Assembled", "false")])
        self.assertEqual((reset["attrs"].get("class"), "disabled" in reset["attrs"], "hidden" in reset["attrs"], reset["text"]), ("figure-reset", True, True, "Reset view"))
        self.assertEqual((pane["attrs"].get("aria-label"), pane["attrs"].get("aria-describedby"), "hidden" in hint["attrs"]), ("Sensor on the part", "onPartHint", True))
        # The old labels, the bars' title and hints gone.
        page = (WEB / "index.html").read_text(encoding="utf-8")
        for gone in ("2D top view", "Oblique view (rigid tilt)", ">Exploded 3D<", "Plan view (registration)", "on-part-title", "orbit-hint",
                     "on-part-reset", "preview-bar"):
            with self.subTest(gone=gone):
                self.assertNotIn(gone, page)
        theme = (WEB / "theme.css").read_text(encoding="utf-8")
        for gone in ("on-part-title", "orbit-hint", "on-part-reset", "preview-bar"):
            with self.subTest(gone=gone):
                self.assertIsNone(re.search(rf"\.{gone}(?![\w-])", self.styles + theme))

    def test_the_controls_overlay_the_frames_top_corners(self) -> None:
        # styles.css: the controls over the frame's top left, 12 px in, wrapping inside it; Reset view over its top right; the
        # sensor on the part's pane a transparent band at its top for them (its canvas, inset 0, below it; the Library's
        # shots set border 0).
        rule = lambda selector: re.search(rf"(?m)^{re.escape(selector)} \{{([^}}]*)\}}", self.styles).group(1)
        tools = rule(".figure-tools")
        for declaration in ("position:absolute", "top:12px", "left:12px", "flex-wrap:wrap", "max-width:calc(100% - 24px)"):
            self.assertIn(declaration, tools)
        for declaration in ("position:absolute", "top:12px", "right:12px"):
            self.assertIn(declaration, rule(".figure-reset"))
        self.assertIn("border-top:40px solid transparent", rule(".stacked-canvas.on-part-view"))
        self.assertIn("position:relative", rule(".canvas-wrap,.stack-figure"))
        # The phone's tighter controls keep 24 px targets.
        narrow = self.styles[self.styles.index("@container figure-frame (max-width:379.98px)"):]
        narrow = narrow[:narrow.index("} }") + 3]
        self.assertIn("min-width:24px", narrow)
        self.assertFalse([value for value in re.findall(r"min-(?:width|height):(\d+)px", narrow) if int(value) < 24])

    def test_the_zoom_level_shows_the_level_alone(self) -> None:
        # app.js updateZoomReadout: "1.2×" in sight, the scale on screen in its tooltip and, for a screen reader, its text.
        readout = re.search(r"function updateZoomReadout\(pane\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn("const level = `${(zoom.base.w / view.w).toFixed(1)}×`; const scale = matrix ? ` · ${matrix.a.toFixed(1)} px/mm` : \"\";", readout)
        self.assertIn('output.replaceChildren(level, ...(scale ? [el("span", {className: "cad-sr-only"}, scale)] : []));', readout)
        self.assertIn("output.title = level + scale;", readout)

    def test_the_registration_s_reset_view_does_what_0_does(self) -> None:
        # attachOrbit's way home (0, a double click) is the button's too; it is shown while the 3D view is drawn.
        self.assertIn("const reset = () => { if (active()) turn(home, true); };", self.app)
        self.assertIn('target.addEventListener("dblclick", reset);', self.app)
        self.assertIn('$("stackedReset").addEventListener("click", () => orbitResets.get($("stackedPreview"))?.());', self.app)
        mode = re.search(r"function setAssemblyMode\(mode\) \{(.*?)\n  \}", self.app, re.S).group(1)
        self.assertIn('$("stackedReset").hidden = mode === "plan" || !target.querySelector(".assembly-camera");', mode)
        self.assertNotIn("orbitHint", self.app)


class ScriptTests(unittest.TestCase):
    def test_app_js_dispatches_the_two_cad_events_once(self) -> None:
        source = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertEqual(source.count("document.dispatchEvent("), 2)
        # app.js owns the template (payload() sends state.design.template_id): CAD mode asks through events.
        for event in ("fpc:mode", "fpc:template-info", "fpc:apply-design", "fpc:board-art"):
            with self.subTest(event=event):
                self.assertEqual(source.count(f'document.addEventListener("{event}"'), 1)
        # The art is answered by an async function: whatever fails is the promise's rejection (the video tools stop at
        # any page error), never an error thrown out of the listener.
        self.assertIn("event.detail.result = boardArt(event.detail);", source)
        self.assertIn("async function boardArt(detail) {", source)
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
        # The sensor on the part (2026-11-05): onpart.js imports three.js as viewer.js does, main.js only loads it
        # dynamically; its geometry, drape.js, imported by main.js, touches neither three.js nor the DOM.
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        self.assertIn('from "../vendor/three/three.module.js"', onpart)
        self.assertIn('from "../vendor/three/OrbitControls.js"', onpart)
        self.assertIn('import("./onpart.js")', main)
        self.assertNotRegex(main, r'(?m)^import .*onpart\.js', "onpart.js must not be imported statically")
        self.assertIn('import * as D from "./drape.js";', main)
        drape = (CAD / "drape.js").read_text(encoding="utf-8")
        for word in ("vendor/three", "THREE", "document.", "window."):
            self.assertNotIn(word, drape, word)
        self.assertNotRegex(drape, r"(?m)^import .*onpart", "drape.js stays pure: it never imports the 3D view")
        # The studio both draw in (studio.js, the user's request of 2026-11-05): three.js only, imported by the two views,
        # never by main.js (it would load three.js with the page).
        studio = (CAD / "studio.js").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'(?m)^import .* from "([^"]+)";$', studio), ["../vendor/three/three.module.js"])
        self.assertNotRegex(main, r"(?m)^import .*studio\.js")
        for name in ("viewer.js", "onpart.js"):
            with self.subTest(imports=name):
                self.assertRegex((CAD / name).read_text(encoding="utf-8"), r'(?m)^import \{[^}]*\blookOf\b[^}]*\} from "\./studio\.js";$')
        for name in CAD_SCRIPTS:
            with self.subTest(file=name):
                self.assertNotRegex((CAD / name).read_text(encoding="utf-8"), r"from\s+['\"]three['\"]")

    def test_the_on_part_view_measures_for_the_checks_only(self) -> None:
        # The review of 2026-11-05: the sensor on the part's reads of its own pixels (a render and a gl.readPixels each,
        # which stalls the GPU and says so in the console) and its comparison with the map run with ?probe only (the
        # browser checks open the page with it), never on a visitor's page.
        main = (CAD / "main.js").read_text(encoding="utf-8")
        self.assertIn('const ON_PART_PROBE = new URLSearchParams(location.search).has("probe");', main)
        self.assertEqual(main.count("D.metrics("), 1)
        self.assertIn("ON_PART_PROBE ? D.metrics(", main)
        self.assertIn("probe: ON_PART_PROBE", main)
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        guarded = []
        for name in ("faces", "pixels"):
            with self.subTest(function=name):
                start, end, body = _js_function(onpart, name)
                statements = [line.strip() for line in body.splitlines() if line.strip() and not line.strip().startswith("//")]
                self.assertTrue(statements[0].startswith("if (!probe"), statements[0])
                guarded.append((start, end))
        reads = [match.start() for match in re.finditer(r"\.readPixels\(", onpart)]
        self.assertTrue(reads)
        for index in reads:
            self.assertTrue(any(start < index < end for start, end in guarded), onpart[index - 80:index])
        # The 3D view's reads of its look (2026-11-05: viewer.js pixels, answering "fpc:view-look"), with ?probe only too.
        viewer = (CAD / "viewer.js").read_text(encoding="utf-8")
        start, end, body = _js_function(viewer, "pixels")
        statements = [line.strip() for line in body.splitlines() if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(statements[0], "if (!probe || !groups.mesh) return null;")
        reads = [match.start() for match in re.finditer(r"\.readPixels\(", viewer)]
        self.assertTrue(reads)
        self.assertTrue(all(start < index < end for index in reads))
        self.assertIn("export function createViewer(host, {onClick = null, probe = false} = {}) {", viewer)
        self.assertIn('module.createViewer($("cadView"), {onClick: onViewClick, probe: ON_PART_PROBE})', main)
        self.assertEqual(main.count('addEventListener("fpc:view-look"'), 1)
        self.assertIn('  if (ON_PART_PROBE) document.addEventListener("fpc:view-look", event => { if (event.detail) event.detail.result = cad.viewer?.pixels() ?? null; });',
                      main)

    def test_the_on_part_view_reuses_its_buffers_and_keeps_the_mode_clicked(self) -> None:
        # The review of 2026-11-05: Exploded / Assembled copies the other positions into each sheet's own buffer (a new
        # attribute per toggle left its GL buffer to the garbage collector); show() draws in the mode setMode last set
        # (it had put back the mode of its start over a click made while the art loaded); every sheet's alpha test is
        # coverage (the outlines antialiased by the MSAA).
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        set_mode = _js_function(onpart, "setMode")[2]
        self.assertIn("attribute.copyArray(", set_mode)
        self.assertNotIn("new THREE.BufferAttribute", set_mode)
        self.assertIn("async function show({stack, positions, probes}) {", onpart)
        self.assertNotRegex(_js_function(onpart, "show")[2], r"view\.mode\s*=")
        main = (CAD / "main.js").read_text(encoding="utf-8")
        self.assertIn("view.show({stack, positions: part, probes})", main)
        # The part it is drawn on (the review of 2026-11-06): the STL, or a whole gripper's sample's finger alone (its first
        # facets) while the fit's selection lies on them, the part's box and the drape's vertices the same part's.
        draw = _js_function(main, "drawOnPart")[2]
        self.assertIn("const part = figurePart();", draw)
        self.assertIn("vertices: {positions: part, scale: cad.inspect.mesh.scale_to_mm}", draw)
        self.assertIn("partBox: partBox(part)", draw)
        figure = _js_function(main, "figurePart")[2]
        for text in ("cad.defaultFile && cad.entry?.sample?.gripper ? cad.entry.sample.partFacets || 0 : 0",
                     "chart.every(facet => facet < facets)", "positions.subarray(0, 9 * facets)", "return positions;"):
            self.assertIn(text, figure)
        materials = re.findall(r"coverage\(new THREE\.Mesh\w+Material\(\{[^}]*alphaTest: ALPHA_TEST", onpart)
        self.assertEqual(len(materials), onpart.count("alphaTest:"))
        self.assertGreaterEqual(len(materials), 2)
        self.assertIn("material.alphaToCoverage = true;", onpart)

    def test_the_on_part_view_keeps_what_lies_behind_an_outline_opaque_and_grabs(self) -> None:
        # The review of 2026-11-05: a covered sample takes the sheet's colour and keeps the larger alpha (the coverage's
        # alpha, written as it was, had let the pane's grey through round every outline over the part), the sheets drawn
        # after the part and back to front as the camera sees them, so what lies behind an outline is there first; and
        # the figure's cursor grab, as over the left figure (OrbitControls had written "auto" inline over styles.css's).
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        coverage = _js_function(onpart, "coverage")[2]
        for text in ("blendSrc: THREE.OneFactor, blendDst: THREE.ZeroFactor", "blendEquationAlpha: THREE.MaxEquation",
                     "blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneFactor"):
            self.assertIn(text, coverage)
        self.assertIn("group.renderOrder = outside ? LAYER_ORDER[group.userData.sheet] : 4 - LAYER_ORDER[group.userData.sheet];",
                      _js_function(onpart, "render")[2])
        self.assertIn("const LAYER_ORDER = {bottom: 1, film: 2, top: 3};", onpart)
        self.assertGreater(onpart.index('controls.cursorStyle = "grab";'), onpart.index("new OrbitControls("))

    def test_the_on_part_view_opens_as_the_left_figure(self) -> None:
        # The user's decision of 2026-11-05 (初始角度和左边的对齐): the sensor on the part's Exploded home looks at the
        # stack as the left figure opens.  Its two angles have one source: drape.js's tilt and spin are app.js's
        # ORBIT_HOME and styles.css's .assembly-camera defaults (its coin's too), so a change to either figure's opening
        # angles fails here; homeDirection turns the left's rotateX(tilt) rotateZ(spin) into the world (the bottom FPC's
        # SVG y the world's -y), Assembled the same spin nearer the normal; the camera's up the stack's normal (HOME_UP),
        # set before OrbitControls takes it as the axis it turns about and framed about it (frameView); the arrow keys
        # turn it as the left figure's turn it (a drag that way).  cad_checks part_on_part measures both on screen.
        drape = (CAD / "drape.js").read_text(encoding="utf-8")
        app = (WEB / "app.js").read_text(encoding="utf-8")
        css = (WEB / "styles.css").read_text(encoding="utf-8")
        constants = dict(re.findall(r"(?m)^export const ((?:HOME|ASSEMBLED)_\w+) = ([^;]+);$", drape))
        home = re.search(r"\bconst ORBIT_HOME = \{tilt: (-?[\d.]+), spin: (-?[\d.]+)\};", app)
        self.assertTrue(home)
        self.assertIn("function attachOrbit(target, {home = ORBIT_HOME,", app)
        rules = re.findall(r"(?m)^\.assembly-camera \{([^}]*)\}", css)
        self.assertEqual(len(rules), 1, rules)
        camera = re.findall(r"rotateX\(var\(--orbit-tilt,\s*(-?[\d.]+)deg\)\)\s*rotateZ\(var\(--orbit-spin,\s*(-?[\d.]+)deg\)\)", rules[0])
        coin = re.search(r"(?m)^\.assembly-camera \.coin-plane \{[^}]*--coin-tilt:\s*var\(--orbit-tilt,\s*(-?[\d.]+)deg\);\s*"
                         r"--coin-spin:\s*var\(--orbit-spin,\s*(-?[\d.]+)deg\)", css)
        self.assertEqual(len(camera), 1, rules[0])
        self.assertTrue(coin)
        ours = (float(constants["HOME_TILT_DEG"]), float(constants["HOME_SPIN_DEG"]))
        for name, values in (("app.js ORBIT_HOME", home.groups()), ("styles.css .assembly-camera", camera[0]), ("styles.css its coin", coin.groups())):
            with self.subTest(source=name):
                self.assertEqual(ours, tuple(float(value) for value in values))
        self.assertEqual(constants["ASSEMBLED_SPIN_DEG"], "HOME_SPIN_DEG")
        self.assertLess(float(constants["ASSEMBLED_TILT_DEG"]), ours[0])
        self.assertEqual(constants["HOME_UP"], "[0, 0, 1]")
        self.assertNotIn("HOME_AZIMUTH_DEG", drape)
        self.assertIn("return [Math.sin(spin) * Math.sin(tilt), -Math.cos(spin) * Math.sin(tilt), Math.cos(tilt)];",
                      _js_function(drape, "homeDirection")[2])
        self.assertIn("export function frameView(view, direction, aspect, cameraUp = HOME_UP) {", drape)
        self.assertIn("let right = unit3(cross3(cameraUp, d));", _js_function(drape, "frameView")[2])
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        self.assertEqual(onpart.count("camera.up.set("), 1)
        self.assertIn("  camera.up.set(...HOME_UP);\n", onpart)
        self.assertLess(onpart.index("camera.up.set(...HOME_UP);"), onpart.index("new OrbitControls("))
        self.assertIn("frameView(home, direction.toArray(), width / height, camera.up.toArray());", _js_function(onpart, "place")[2])
        # The keys as a drag that way, as the left figure's: its ArrowLeft raises its spin and ArrowUp its tilt, where
        # OrbitControls' rotateLeft lowers its azimuth (the spin) and rotateUp its polar angle (the tilt).
        self.assertIn("ArrowLeft: [0, 1], ArrowRight: [0, -1], ArrowUp: [1, 0], ArrowDown: [-1, 0]", app)
        self.assertIn("const turn = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1]}[event.key];", onpart)
        self.assertIn("else if (turn[0]) controls.rotateLeft(turn[0] * KEY_TURN_DEG * DEG);\n    else controls.rotateUp(turn[1] * KEY_TURN_DEG * DEG);", onpart)

    def test_the_on_part_view_draws_in_the_shared_studio(self) -> None:
        # The look of 2026-11-05 (its look lab): the figure's lights hung on the camera, Khronos PBR Neutral tone mapping
        # on a canvas still transparent over the pane's light gradient (no scene background or environment: the studio is
        # the sheets' envMap), and the studio a fallback path: none, with a single warning, where its shader edit, its
        # half-float render targets or its making fail; made again when a lost context comes back.  Every edit of
        # three.js's shader text goes through patched().  Since the user's request of 2026-11-05 (the 3D view in the same
        # light) the lights, the studio, the tone mapping and the warnings are studio.js's, each drawing its own warnings
        # (lookOf: "On the part: ...", "3D view: ..."), and the 3D view's old lights (addViewLights) are gone.
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        viewer = (CAD / "viewer.js").read_text(encoding="utf-8")
        studio = (CAD / "studio.js").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'(?m)^import .* from "\./viewer\.js";$', onpart), ['import {PART_RGB} from "./viewer.js";'])
        self.assertNotIn("addViewLights", onpart + viewer)
        self.assertEqual(re.findall(r'(?m)^import .* from "([^"]+)";$', onpart),
                         ["../vendor/three/three.module.js", "../vendor/three/OrbitControls.js", "./viewer.js", "./studio.js", "./drape.js"])
        self.assertIn('import {lookOf, measure, studioLights, toneMap} from "./studio.js";', onpart)
        self.assertIn('const {patched, reflections, reflectionsOnly, studioFor} = lookOf("On the part", {studied: "on-part studio",\n'
                      '  without: "the film and the boards are drawn"});', onpart)
        create = _js_function(onpart, "createOnPartView")[2]
        self.assertIn("const lights = studioLights(scene, camera);", create)
        self.assertIn("const look = {environment: studioFor(renderer), rotation: new THREE.Euler(), filmLamp: {value: new THREE.Vector3()}};", create)
        self.assertIn("toneMap(renderer);", create)
        tone = [line.strip() for line in _js_function(studio, "toneMap")[2].splitlines() if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(tone, ["renderer.toneMapping = THREE.NeutralToneMapping;", "renderer.toneMappingExposure = TONE_EXPOSURE;"])
        self.assertIn("new THREE.WebGLRenderer({antialias: true, alpha: true})", create)
        self.assertIn("renderer.setClearColor(0x000000, 0);", create)
        for word in ("scene.background", "scene.environment", "shadowMap", "castShadow"):
            self.assertNotIn(word, onpart + studio, word)
        # The lights, the studio and the tone mapping are studio.js's alone (moved there as they were).
        for name in ("LIGHTS", "STUDIO", "TONE_EXPOSURE"):
            with self.subTest(constant=name):
                self.assertRegex(studio, rf"(?m)^export const {name} = ")
                self.assertNotRegex(onpart + viewer, rf"(?m)^const {name} = ")
        for word in ("new THREE.PMREMGenerator(", "new THREE.HemisphereLight(", "new THREE.DirectionalLight(", "new THREE.PointLight(",
                     "THREE.NeutralToneMapping"):
            self.assertNotIn(word, onpart, word)
            self.assertEqual(studio.count(word), 1, word)
        # One warning, once a cause, each drawing its own set of causes (lookOf's).
        self.assertEqual(studio.count("console.warn("), 1)
        self.assertEqual((onpart + viewer).count("console.warn("), 0)
        look_of = _js_function(studio, "lookOf")[2]
        self.assertEqual(look_of.count("const warned = new Set();"), 1)
        self.assertEqual(studio.count("new Set()"), 1)
        warn = _js_function(studio, "warnOnce")[2]
        self.assertIn("console.warn(`${who}: ${message}`);", warn)
        statements = [line.strip() for line in warn.splitlines() if line.strip()]
        self.assertEqual(statements[:2], ["if (warned.has(key)) return;", "warned.add(key);"])
        self.assertEqual(re.findall(r'lookOf\("([^"]+)", \{studied: "([^"]+)"', onpart + viewer), [("On the part", "on-part studio"), ("3D view", "3d-view studio")])
        studio_for = _js_function(studio, "studioFor")[2]
        statements = [line.strip() for line in studio_for.splitlines() if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(statements[0], "if (!reflections) return null;")
        self.assertEqual(statements[2], 'if (!(extensions.has("EXT_color_buffer_float") || extensions.has("EXT_color_buffer_half_float"))) {')
        self.assertTrue(statements[3].startswith('warnOnce("studio", ') and statements[4] == "return null;", statements[3:5])
        self.assertRegex(studio_for, r'catch \(error\) \{\s*warnOnce\("studio", [^;]*;\s*return null;')
        self.assertEqual(studio_for.count("return null;"), 3)
        # The review of 2026-11-05: the studio's measure after its build's try (inside it, a measure that threw had thrown
        # away a studio made), each measure guarded (measure: User Timing Level 3's options throw in an older browser).
        built = studio_for[studio_for.index("try {"):studio_for.index("} catch (error) {")]
        self.assertNotIn("measure", built)
        self.assertRegex(studio_for, r'\}\n\s*measure\(studied, started\);\n\s*return target;\s*$')
        self.assertEqual(studio.count("performance.measure"), 1)
        self.assertEqual((onpart + viewer).count("performance.measure"), 0)
        measure = [line.strip() for line in _js_function(studio, "measure")[2].splitlines() if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(measure, ["try {", "performance.measure?.(name, {start: started});", "} catch {", "}"])
        self.assertEqual(re.findall(r'measure\("([\w -]+)", started\);', onpart), ["on-part contact"])
        # A lost context's objects dropped, never disposed, when it comes back (three.js has made its state again by then:
        # a dispose had it delete the lost context's GL objects in the new one, Chrome's INVALID_OPERATION warnings); the
        # studio made again before main.js draws the figure again.
        restored = onpart[onpart.index('addEventListener("webglcontextrestored"'):]
        handler = restored[:restored.index("\n    onContext(true);\n")]
        code = "\n".join(line for line in handler.splitlines() if not line.strip().startswith("//"))
        self.assertIn("look.environment = studioFor(renderer);", code)
        self.assertIn("clear({lost: true});", code)
        self.assertNotIn("dispose", code)
        self.assertLess(code.index("look.environment = studioFor(renderer);"), code.index("clear({lost: true});"))
        clear_sheets = _js_function(onpart, "clearSheets")[2]
        for text in ("if (!lost) dispose(view.sheets);", "if (!lost) view.textures.forEach(map => map.dispose());",
                     "if (view.contact && !lost) view.contact.map.dispose();", "view.contact = null;"):
            self.assertIn(text, clear_sheets, text)
        self.assertEqual(clear_sheets.count("dispose("), 3)
        self.assertIn("if (!lost) view.part.geometry.dispose();", _js_function(onpart, "clearPart")[2])
        clear = _js_function(onpart, "clear")[2]
        self.assertIn("clearSheets(lost);", clear)
        self.assertIn("if (part || lost || (view.partPositions && view.partPositions !== keep)) clearPart(lost);", clear)
        self.assertNotRegex(onpart + studio + viewer, r"(?:vertex|fragment)Shader\.replace\(")
        self.assertIn("out = out.replace(find, replacement);", _js_function(studio, "patched")[2])
        # The sheets' reflections only through studio.js (its patch, its anchor's check).
        self.assertIn("fragment = reflectionsOnly(fragment);", _js_function(onpart, "reflective")[2])
        self.assertIn("  reflections,\n", onpart[onpart.index("const PATCHES = {"):])

    def test_the_3d_view_draws_in_the_studio_with_its_markers_unlit(self) -> None:
        # The user's request of 2026-11-05 ("you only added the new light and shade to the last 3D figure; add it to every
        # 3D view"): the 3D view's part in the sensor on the part's studio (studio.js: its lights hung on the camera, its
        # studio mirrored without its diffuse light, Khronos PBR Neutral), its facets' meaning colours (paint) lit as a
        # matte surface; every marker drawn unlit in its own colour, past the tone mapping; the studio made once a
        # renderer (never a model: no PMREM render target per load) and again when a lost context comes back, the lost one
        # dropped, not disposed; on a software renderer alone (SwiftShader: the look's fragments cost 2 to 3 times the old
        # Lambert's) a drag's frames drawn with the part's diffuse light only, the look again as it ends.  Picking is the
        # geometry's: the part stays non-indexed in file order.
        viewer = (CAD / "viewer.js").read_text(encoding="utf-8")
        self.assertIn('import {LIGHTS, lookOf, studioLights, toneMap} from "./studio.js";', viewer)
        self.assertIn('const {reflectionsOnly, studioFor} = lookOf("3D view", {studied: "3d-view studio", without: "the part is drawn"});', viewer)
        create = _js_function(viewer, "createViewer")[2]
        for text in ("toneMap(renderer);", "const lights = studioLights(scene, camera);",
                     "const look = {environment: studioFor(renderer), rotation: new THREE.Euler()};",
                     'scene.background = new THREE.Color(0xf5f5f7);'):
            self.assertIn(text, create, text)
        for word in ("HemisphereLight", "DirectionalLight", "PointLight", "AmbientLight", "MeshPhongMaterial", "scene.environment", "shadowMap",
                     "setAnimationLoop"):
            self.assertNotIn(word, viewer, word)
        studio = (CAD / "studio.js").read_text(encoding="utf-8")
        for word in ("requestAnimationFrame", "setAnimationLoop", "setInterval", "setTimeout"):
            self.assertNotIn(word, studio, word)
        # The part: matte, the studio's reflections only, turned with the camera; made with each model, the studio not.
        part = _js_function(viewer, "partMaterial")[2]
        self.assertIn("new THREE.MeshStandardMaterial({vertexColors: true, color: new THREE.Color(gain, gain, gain), ...matte,", part)
        self.assertIn("envMap: look.environment?.texture || null,", part)
        self.assertIn("material.envMapRotation = look.rotation;", part)
        self.assertIn("material.onBeforeCompile = shader => { shader.fragmentShader = reflectionsOnly(shader.fragmentShader); };", part)
        look = re.search(r"(?m)^const VIEW_LOOK = \{gain: ([\d.]+), roughness: ([\d.]+), metalness: 0, envMapIntensity: ([\d.]+)\};$", viewer)
        self.assertTrue(look and 1 <= float(look.group(1)) <= 1.5 and float(look.group(2)) >= 0.5 and 0 < float(look.group(3)) <= 1.5, look)
        self.assertIn("const mesh = new THREE.Mesh(geometry, partMaterial(look));", _js_function(viewer, "setMesh")[2])
        self.assertEqual(viewer.count("studioFor(renderer)"), 2)
        render = _js_function(viewer, "render")[2]
        statements = [line.strip() for line in render.splitlines() if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(statements, ["placeHandles();", "look.rotation.setFromQuaternion(camera.quaternion);", "lights.turn();",
                                      "lights.place(camera.position.distanceTo(controls.target));", "renderer.render(scene, camera);"])
        # The markers: unlit, past the tone mapping, each made by markerMaterial or lineMaterial.
        self.assertIn("const markerMaterial = parameters => new THREE.MeshBasicMaterial({...parameters, toneMapped: false});", viewer)
        self.assertIn("const lineMaterial = parameters => new THREE.LineBasicMaterial({...parameters, toneMapped: false});", viewer)
        self.assertEqual(viewer.count("new THREE.MeshBasicMaterial("), 1)
        self.assertEqual(viewer.count("new THREE.LineBasicMaterial("), 1)
        self.assertNotRegex(viewer, r"new THREE\.(?!MeshStandardMaterial|MeshLambertMaterial|MeshNormalMaterial|MeshBasicMaterial|LineBasicMaterial)\w*Material\(")
        # A drag's material: the diffuse light alone, on a software renderer only, swapped in at a drag's start and out at
        # its end (OrbitControls' turn, a border handle's drag), never in render().
        self.assertEqual(viewer.count("new THREE.MeshLambertMaterial("), 1)
        self.assertIn("new THREE.MeshLambertMaterial(", _js_function(viewer, "diffuseMaterial")[2])
        self.assertIn("  dragMaterial = SOFTWARE_RENDERER.test(info.renderer) ? diffuseMaterial() : null;\n", viewer)
        self.assertEqual(len(re.findall(r"(?<!function )\bdiffuseMaterial\(\)", viewer)), 1)
        self.assertRegex(viewer, r"(?m)^const SOFTWARE_RENDERER = /SwiftShader\|llvmpipe\b")
        swap = [line.strip() for line in _js_function(viewer, "dragging")[2].splitlines() if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(swap, ["const part = groups.mesh;", "if (!dragMaterial || !part) return;", "part.material = on ? dragMaterial : part.userData.look;",
                                "if (!on) requestRender();"])
        for text in ('controls.addEventListener("start", () => dragging(true));', 'controls.addEventListener("end", () => dragging(false));'):
            self.assertIn(text, create, text)
        self.assertIn("dragging(true);", _js_function(viewer, "startDrag")[2])
        self.assertIn("dragging(false);", _js_function(viewer, "endDrag")[2])
        self.assertIn("mesh.userData.look = mesh.material;", _js_function(viewer, "setMesh")[2])
        self.assertIn("node.userData.look?.dispose();", _js_function(viewer, "dispose")[2])
        self.assertGreaterEqual(viewer.count("markerMaterial({"), 8)
        self.assertGreaterEqual(viewer.count("lineMaterial({"), 2)
        # A lost context: the studio made again for the part's material, the lost one dropped, never disposed; drawn again.
        restored = viewer[viewer.index('canvas.addEventListener("webglcontextrestored", () => {'):]
        handler = restored[:restored.index("\n  });\n")]
        self.assertEqual([line.strip() for line in handler.splitlines()[1:]],
                         ["look.environment = studioFor(renderer);", "if (groups.mesh) groups.mesh.userData.look.envMap = look.environment?.texture || null;",
                          "requestRender();"])
        # Picking: the raycaster's faceIndex is the STL facet id (non-indexed, in file order).
        set_mesh = _js_function(viewer, "setMesh")[2]
        self.assertIn("// Non-indexed and in file order: the raycaster's faceIndex is the STL facet id.", set_mesh)
        self.assertNotIn("setIndex", set_mesh)

    def test_the_on_part_view_s_edges_contact_shade_and_film_face(self) -> None:
        # The look of 2026-11-05: each layer's edge band drawn from the front only (wound outward: the far side's culled);
        # the contact shade's footprint made on the first Assembled of a drawing only and drawn in Assembled only (the
        # layers float clear of the part when exploded); the film's face not drawn assembled (both boards cover it; on
        # SwiftShader it cost 8-17 ms a frame); render() builds nothing (the studio and the footprint are made once) and
        # each sheet's positions are drawn dynamic, copied in place.
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        band = _js_function(onpart, "bandMaterial")[2]
        self.assertEqual(band.count("new THREE.MeshStandardMaterial("), 2)
        self.assertEqual(band.count("side: THREE.FrontSide"), 2)
        self.assertNotRegex(band, r"DoubleSide|BackSide")
        sheet_mesh = _js_function(onpart, "sheetMesh")[2]
        self.assertIn("new THREE.Mesh(band.geometry, bandMaterial(", sheet_mesh)
        self.assertIn(".setUsage(THREE.DynamicDrawUsage)", sheet_mesh)
        ensure = _js_function(onpart, "ensureContact")[2]
        statements = [line.strip() for line in ensure.splitlines() if line.strip() and not line.strip().startswith("//")]
        self.assertEqual(statements[0], 'if (view.contact !== null || view.mode !== "assembled" || !view.sheets || !PATCHES.contact) return;')
        # No footprint (contactField's null) is kept as false until the next drawing (clearSheets), not made again at each
        # Assembled (the review of 2026-11-05).
        self.assertIn("view.contact = field || false;\n    if (!field) return;", ensure)
        self.assertRegex(onpart, r"contact: null, shadeOff: false")
        # The core from CONTACT.innerMm inside the footprint's edge out (the WXAI sock's light line between the stack's
        # edge band and its shade, the review of 2026-11-05), inside only on an edge facing the camera, as its band (the
        # part seen past an edge facing away, beside the wrap's knuckle, not darkened); the halo outside the footprint only.
        inner = re.search(r"\binnerMm: ([\d.]+),", onpart)
        self.assertTrue(inner and 0.3 <= float(inner.group(1)) <= 0.5, inner)
        field = _js_function(onpart, "contactField")[2]
        self.assertIn("const inner = eroded(cover, width, height, Math.max(1, Math.round(CONTACT.innerMm * k)));", field)
        self.assertIn("data[4 * t] = Math.round(255 * Math.max(0, core[t] - Math.min(cover[t], inner[t])));", field)
        # The band along the rings' own edge, eroded before the cells turned from the normal leave the footprint.
        self.assertLess(field.index("const inner = eroded("), field.index("if (!Number.isFinite(lift[t])) cover[t] = 0;"))
        self.assertIn("data[4 * t + 1] = Math.round(255 * Math.max(0, halo[t] - cover[t]));", field)
        shade = onpart[onpart.index("const CONTACT_FRAGMENT_EDITS = ["):onpart.index("// Whether each patch finds its text")]
        self.assertIn("float inside = 1.0 - smoothstep( 0.0, ${CONTACT.insideHalo.toFixed(3)}, footprint.g );", shade)
        self.assertIn("core *= mix( 1.0, smoothstep( 0.0, 1e-3, dot( outward, cameraPosition.xy - vContactWorld.xy ) ), inside );", shade)
        self.assertIn("float occlusion = ( contactStrength.x * core + contactStrength.y * footprint.g ) * within * footprint.a;", shade)
        self.assertIn("contact.contactStep.value.set(2 / field.size[0], 2 / field.size[1]);", ensure)
        render = _js_function(onpart, "render")[2]
        self.assertIn('if (view.mode === "assembled" && view.contact && !view.shadeOff) contact.contactStrength.value.set(...CONTACT.strength);\n'
                      "    else contact.contactStrength.value.set(0, 0);", render)
        self.assertEqual(onpart.count("contactStrength.value.set("), 2)
        for word in ("studioFor(", "contactField(", "bandOf(", "new THREE."):
            self.assertNotIn(word, render, word)
        film_face = _js_function(onpart, "filmFace")[2]
        self.assertIn('if (film) film.children[0].visible = view.mode !== "assembled";', film_face)
        for name in ("show", "setMode"):
            with self.subTest(function=name):
                body = _js_function(onpart, name)[2]
                self.assertIn("filmFace();\n", body)
                self.assertIn("ensureContact();\n", body)
                self.assertLess(body.index("ensureContact();"), body.index("place(true);"))

    def test_the_on_part_film_has_a_lamp_of_its_own(self) -> None:
        # The user's of 2026-11-05 (再调一下你说的黑色压阻膜): at the left figure's Exploded home the film mirrored the room
        # between the studio's softboxes, nearly a flat black again.  Its own lamp: a light of its shader alone
        # (FILM_LAMP_EDITS through patched(), three.js's RE_Direct, put in by filmLit for the film's material only: the
        # boards, the edge bands, the part, the 3D view and the studio's lights draw as before), aimed for each drawing
        # from the Exploded home (filmLampAt, never from the camera as it is: a turned view keeps it; kept for the drawing
        # and the aspect, dropped with the drawing) and hung on the camera by place() in camera distances, as the studio's
        # sheen lamp; never each frame.
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        others = (CAD / "studio.js").read_text(encoding="utf-8") + (CAD / "viewer.js").read_text(encoding="utf-8")
        self.assertRegex(onpart, r"(?m)^const FILM_LAMP = \{aim: [\d.]+, out: [\d.]+, intensity: [\d.]+\};$")
        lamp = onpart[onpart.index("const FILM_LAMP_EDITS = ["):onpart.index("// The contact shade on the part:")]
        self.assertIn("filmLight.direction = normalize( filmLamp - geometryPosition );", lamp)
        self.assertIn("filmLight.color = vec3( ${FILM_LAMP.intensity.toFixed(3)} );", lamp)
        self.assertIn("RE_Direct( filmLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );", lamp)
        self.assertIn('["#include <common>", "#include <common>\\nuniform vec3 filmLamp;"]]', lamp)
        self.assertIn('  filmLamp: patched(THREE.ShaderLib.physical.fragmentShader, FILM_LAMP_EDITS, "the film\'s lamp") !== null,\n', onpart)
        lit = _js_function(onpart, "filmLit")[2]
        self.assertIn('const lit = PATCHES.filmLamp ? patched(shader.fragmentShader, FILM_LAMP_EDITS, "the film\'s lamp") : null;', lit)
        self.assertIn("if (lit !== null) { shader.fragmentShader = lit; shader.uniforms.filmLamp = look.filmLamp; }", lit)
        self.assertLess(lit.index("reflected.call(material, shader, renderer);"), lit.index("const lit = "))
        self.assertIn("return filmLit(reflective(coverage(new THREE.MeshPhysicalMaterial(", _js_function(onpart, "filmMaterial")[2])
        self.assertEqual(len(re.findall(r"\bfilmLit\(", onpart)), 2)
        for name in ("boardMaterial", "bandMaterial", "partMaterial", "reflective", "coverage", "render"):
            with self.subTest(function=name):
                self.assertNotRegex(_js_function(onpart, name)[2], r"filmLit|filmLamp|FILM_LAMP")
        self.assertNotRegex(others, r"filmLit|filmLamp|FILM_LAMP")
        place = _js_function(onpart, "place")[2]
        self.assertIn("lights.place(distance);\n    look.filmLamp.value.copy(filmLampAt(width / height)).multiplyScalar(distance);\n", place)
        aim = "\n".join(line for line in _js_function(onpart, "filmLampAt")[2].splitlines() if not line.strip().startswith("//"))
        self.assertIn("if (view.filmAim?.stack === view.stack && view.filmAim.aspect === aspect) return view.filmAim.at;", aim)
        self.assertIn('const z = new THREE.Vector3(...homeDirection("exploded"));', aim)
        self.assertIn("frameView(view.stack.home.exploded, z.toArray(), aspect, HOME_UP);", aim)
        self.assertIn("const p = view.stack.sheets.film.positions;", aim)
        self.assertIn("const aim = middle.clone().lerp(top, FILM_LAMP.aim);", aim)
        self.assertIn("const normal = new THREE.Vector3(up.dot(x), up.dot(y), up.dot(z));", aim)
        self.assertIn("const at = aim.addScaledVector(mirror, FILM_LAMP.out * distance).divideScalar(distance);", aim)
        self.assertIn("view.filmAim = {stack: view.stack, aspect, at};", aim)
        self.assertNotRegex(aim, r"\bcamera\b|controls|view\.mode")
        self.assertIn("view.filmAim = null;", _js_function(onpart, "clear")[2])
        self.assertRegex(onpart, r"centre: null, filmAim: null\};")

    def test_the_on_part_view_s_shader_edits_match_the_vendored_three_js(self) -> None:
        # The review of 2026-11-05: patched() checks only that the text it looks for is there; the GLSL it puts in uses
        # three.js 0.186.1's own names, which a later three.js could rename and keep the anchors: a GLSL compile error in
        # a visitor's browser (the part or the sheets not drawn), not the warning and fallback.  Here every anchor of
        # the patched() calls of onpart.js and of studio.js (the studio's reflections-only patch, which the 3D view's part
        # takes too since 2026-11-05; viewer.js edits no shader text of its own) is in the shader text it edits, once, and
        # every name the inserted code uses is declared before it runs: an upgrade of the vendored three.js fails in this
        # suite first.
        sources = {name: (CAD / name).read_text(encoding="utf-8") for name in ("onpart.js", "studio.js")}
        onpart = "\n".join(sources.values())
        viewer = (CAD / "viewer.js").read_text(encoding="utf-8")
        self.assertNotRegex(viewer, r"\bpatched\(|_EDITS\b|\.replace\(")
        self.assertEqual(viewer.count("reflectionsOnly("), 1)
        module = (VENDOR / "three.module.js").read_text(encoding="utf-8")
        chunks = _three_shader_chunks()
        # The program's prefixes for a built-in material (WebGLProgram's, not a RawShaderMaterial's): vertex, fragment.
        program = module[module.index("\t} else {\n\n\t\tprefixVertex = ["):]
        prefixes = [program[program.index(f"prefix{kind} = ["):] for kind in ("Vertex", "Fragment")]
        prefixes = [text[:text.index("].filter( filterEmptyLine )")] for text in prefixes]
        for name in ("standard", "physical"):
            with self.subTest(shader_lib=name):
                self.assertRegex(module, rf"(?s)(?:\t{name}: \{{|ShaderLib\.{name} = \{{)\n(?:(?!\n\t\}}).)*?vertexShader: ShaderChunk\.meshphysical_vert,"
                                         r"\s*fragmentShader: ShaderChunk\.meshphysical_frag")
        vertex, fragment = chunks["meshphysical_vert"], chunks["meshphysical_frag"]
        targets = {"THREE.ShaderChunk.lights_fragment_maps": chunks["lights_fragment_maps"], "THREE.ShaderLib.physical.fragmentShader": fragment,
                   "THREE.ShaderLib.standard.fragmentShader": fragment, "THREE.ShaderLib.standard.vertexShader": vertex,
                   "shader.fragmentShader": fragment, "shader.vertexShader": vertex, "fragment": fragment}
        edits = {}
        for source in sources.values():
            for name in re.findall(r"(?m)^const (\w+_EDITS) = \[", source):
                start = source.index(f"const {name} = [")
                edits[name] = re.findall(r'(?:= \[|\],\s*)\["([^"]+)", ', source[start:source.index("]];", start) + 3])
        self.assertEqual(sorted(edits), ["CONTACT_FRAGMENT_EDITS", "CONTACT_VERTEX_EDITS", "COVERAGE_EDITS", "FILM_LAMP_EDITS", "REFLECTIONS_EDITS",
                                         "TINT_EDITS"])
        calls = re.findall(r"\bpatched\(([\w.]+), (\w+_EDITS|\[\[\"(?:[^\"\\]|\\.)*\")", onpart)
        self.assertGreaterEqual(len(calls), 11)
        self.assertEqual(len(re.findall(r"\bpatched\(([\w.]+), (\w+_EDITS|\[\[\")", sources["studio.js"])), 3)
        anchors = set()
        for target, what in calls:
            with self.subTest(target=target, edits=what):
                self.assertIn(target, targets)
                for anchor in edits[what] if what in edits else [json.loads(what[2:])]:
                    self.assertEqual(targets[target].count(anchor), 1, anchor)
                    anchors.add(anchor)
        self.assertEqual(anchors, {"#include <alphatest_fragment>", "iblIrradiance += getIBLIrradiance( geometryNormal );", "#include <lights_fragment_maps>",
                                   "#include <aomap_fragment>", "#include <common>", "#include <worldpos_vertex>", "#include <opaque_fragment>",
                                   "#include <lights_fragment_end>"})
        # The names the inserted GLSL uses (each in onpart.js), declared before the anchor it runs at.
        main = fragment.index("void main() {")

        def before(text, declaration, anchor):
            # The declaration (whole words) in the text before the anchor.
            found = re.search(rf"(?<![\w.]){re.escape(declaration)}(?!\w)", text)
            return found is not None and found.start() < text.index(anchor)

        for name, declared in (("diffuseColor", before(fragment, "vec4 diffuseColor", "#include <alphatest_fragment>")
                                and before(fragment, "vec4 diffuseColor", "#include <aomap_fragment>")),
                               ("alphaTest", "uniform float alphaTest;" in chunks["alphatest_pars_fragment"]
                                and before(fragment, "#include <alphatest_pars_fragment>", "void main() {")),
                               ("USE_ALPHATEST", "parameters.alphaTest ? '#define USE_ALPHATEST' : ''," in prefixes[1]),
                               ("reflectedLight.directSpecular", before(fragment, "ReflectedLight reflectedLight", "#include <aomap_fragment>")
                                and before(fragment, "#include <lights_fragment_end>", "#include <aomap_fragment>")
                                and re.search(r"struct ReflectedLight \{[^}]*\bvec3 directSpecular;[^}]*\bvec3 indirectSpecular;", chunks["common"]) is not None),
                               ("reflectedLight.indirectSpecular", re.search(r"struct ReflectedLight \{[^}]*\bvec3 indirectSpecular;", chunks["common"]) is not None),
                               ("outgoingLight", before(fragment, "vec3 outgoingLight", "#include <opaque_fragment>")),
                               ("transformed", before(chunks["begin_vertex"] + "\n#end", "vec3 transformed", "#end") and before(vertex, "#include <begin_vertex>", "#include <worldpos_vertex>")),
                               ("modelMatrix", "'uniform mat4 modelMatrix;'," in prefixes[0]),
                               ("cameraPosition", "'uniform vec3 cameraPosition;'," in prefixes[1]),
                               ("#include <common>", fragment.index("#include <common>") < main and vertex.index("#include <common>") < vertex.index("void main() {")),
                               # The film's own lamp (FILM_LAMP_EDITS, 2026-11-05): one more light as three.js takes its own.
                               ("IncidentLight", re.search(r"struct IncidentLight \{[^}]*\bvec3 color;[^}]*\bvec3 direction;[^}]*\bbool visible;", chunks["common"]) is not None),
                               ("RE_Direct", "#define RE_Direct\t\t\t\tRE_Direct_Physical" in chunks["lights_physical_pars_fragment"]
                                and before(fragment, "#include <lights_physical_pars_fragment>", "void main() {")),
                               ("material", "PhysicalMaterial material;" in chunks["lights_physical_fragment"]
                                and before(fragment, "#include <lights_physical_fragment>", "#include <lights_fragment_end>")),
                               *((name, f"vec3 {name} = " in chunks["lights_fragment_begin"] and before(fragment, "#include <lights_fragment_begin>", "#include <lights_fragment_end>"))
                                 for name in ("geometryPosition", "geometryNormal", "geometryViewDir", "geometryClearcoatNormal"))):
            with self.subTest(name=name):
                self.assertIn(name, onpart)
                self.assertTrue(declared, name)

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


def _three_shader_chunks() -> dict:
    """three.js's ShaderChunk as the vendored three.module.js defines it, {name: GLSL}: each chunk a string constant on one
    line (a JSON string), named in ShaderChunk's table."""
    source = (VENDOR / "three.module.js").read_text(encoding="utf-8")
    strings = dict(re.findall(r'(?m)^(?:var|const) ([\w$]+) = ("(?:[^"\\\n]|\\.)*");$', source))
    table = source[source.index("const ShaderChunk = {"):]
    table = table[:table.index("\n};")]
    return {name: json.loads(strings[constant]) for name, constant in re.findall(r"(?m)^\t(\w+): ([\w$]+),?$", table)}


def _js_function(source: str, name: str) -> tuple:
    """(start, end, body) of ``function name(`` in a script: its body between its braces (strings and line comments
    skipped: an apostrophe in a comment, "three.js's", opens no string)."""
    match = re.search(rf"(?:async )?function {name}\(", source)
    if not match:
        raise AssertionError(f"function {name} not found")
    # The body's brace: the first one after the parameters' closing parenthesis (a parameter may destructure).
    index, depth = match.end(), 1
    while depth:
        depth += {"(": 1, ")": -1}.get(source[index], 0)
        index += 1
    start = source.index("{", index)
    depth, quote, index = 0, None, start
    while True:
        char = source[index]
        if quote:
            if char == "\\":
                index += 1
            elif char == quote:
                quote = None
        elif source.startswith("//", index):
            index = source.index("\n", index)
        elif char in "\"'`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if not depth:
                return match.start(), index + 1, source[start + 1:index]
        index += 1


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


class _Names(HTMLParser):
    """The text of #guideCustomize and of each <details id>'s own <summary>, its hint left out."""

    def __init__(self) -> None:
        super().__init__()
        self.names: dict = {}
        self._details: list = []
        self._into = None
        self._text: list = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if self._into is not None and tag == "span":
            if self._skip or "hint" in (attributes.get("class") or "").split():
                self._skip += 1
        elif tag == "details":
            self._details.append(attributes.get("id"))
        elif tag == "summary" and self._details and self._details[-1]:
            self._into = self._details[-1]
        elif tag == "button" and attributes.get("id") == "guideCustomize":
            self._into = "guideCustomize"

    def handle_endtag(self, tag):
        if self._into is not None and tag == "span" and self._skip:
            self._skip -= 1
        elif self._into is not None and tag in ("summary", "button"):
            self.names[self._into] = " ".join("".join(self._text).split())
            self._into, self._text = None, []
        elif tag == "details" and self._details:
            self._details.pop()

    def handle_data(self, data):
        if self._into is not None and not self._skip:
            self._text.append(data)


class FoldNameTests(unittest.TestCase):
    def test_the_customize_folds_are_named_advanced_customization(self) -> None:
        # The user's request of 2026-11-04: the guide's switch and the two folds "Advanced Customization" ("Customize the
        # sensor" before), the form's fold inside it "More options" ("Advanced" before), as the fit's.
        parser = _Names()
        parser.feed((WEB / "index.html").read_text(encoding="utf-8"))
        names = parser.names
        self.assertEqual([names.get(key) for key in ("guideCustomize", "cadCustomize", "formCustomize")],
                         ["Advanced Customization"] * 3)
        self.assertEqual([names.get(key) for key in ("formAdvanced", "cadConfigMore")], ["More options"] * 2)
        main = (CAD / "main.js").read_text(encoding="utf-8")
        self.assertIn('"The sensor fails a check on the part: see Advanced Customization, On the part."', main)
        self.assertIn('"No sensor fits here: choose another face, or open Advanced Customization."', main)
        for name in ("index.html", "app.js", "cad/main.js", "theme.css", "styles.css"):
            with self.subTest(file=name):
                self.assertNotIn("Customize the sensor", (WEB / name).read_text(encoding="utf-8"))


def _js_object(source: str, name: str):
    """The object literal of ``const name = {...};`` in a script, as JSON reads it (its keys quoted, its line comments
    and trailing commas dropped): numbers, arrays and objects only."""
    match = re.search(rf"(?m)^\s*(?:export )?const {name} = \{{", source)
    if not match:
        raise AssertionError(f"const {name} not found")
    start = match.end() - 1
    depth, index = 0, start
    while True:
        depth += {"{": 1, "}": -1}.get(source[index], 0)
        index += 1
        if not depth:
            break
    text = re.sub(r"//[^\n]*", "", source[start:index])
    text = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', text)
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


def _srgb(level: float) -> float:
    return 12.92 * level if level <= 0.0031308 else 1.055 * level ** (1 / 2.4) - 0.055


def _linear(level: float) -> float:
    return level / 12.92 if level <= 0.04045 else ((level + 0.055) / 1.055) ** 2.4


class ViewLightTests(unittest.TestCase):
    """The 3D views' light (app.js lightView, styles.css .board-light; the user's request of 2026-11-05: the light of the
    sensor on the part in every 3D view): app.js, a classic script, cannot import the ES modules' numbers (studio.js's
    lights and studio, which the 3D view shares since the merge of 2026-11-05, and onpart.js's coverlay and edge bands),
    so it copies them; these tests keep the copies equal.  The browser checks (tools/browser/ui_checks.py part_view_light)
    see the light."""

    def setUp(self) -> None:
        self.app = (WEB / "app.js").read_text(encoding="utf-8")
        self.onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        self.studio = (CAD / "studio.js").read_text(encoding="utf-8")
        self.styles = (WEB / "styles.css").read_text(encoding="utf-8")

    def test_the_views_take_the_sensor_on_the_part_s_lights_studio_and_coverlay(self) -> None:
        # The lights (all of them: the hemisphere, the key, the rim, the sheen lamp), the studio's room, distance and
        # panels (studio.js's since the merge of 2026-11-05, the sensor on the part's and the 3D view's), the coverlay's
        # gain, roughness and reflection, and the edge bands' shade (onpart.js's).
        self.assertEqual(_js_object(self.app, "VIEW_LIGHTS"), _js_object(self.studio, "LIGHTS"))
        studio = _js_object(self.studio, "STUDIO")
        self.assertEqual(_js_object(self.app, "VIEW_STUDIO"), {key: studio[key] for key in ("room", "distance", "panels")})
        look = _js_object(self.onpart, "BOARD_LOOK")
        copied = _js_object(self.app, "VIEW_BOARD_LOOK")
        self.assertEqual(copied, {key: look[key] for key in copied})
        self.assertEqual(sorted(copied), ["envMapIntensity", "gain", "roughness"])
        self.assertEqual(float(re.search(r"(?m)^  const VIEW_BAND_SHADE = ([\d.]+);$", self.app).group(1)), _js_object(self.onpart, "BAND")["shade"])
        # The light's reference is the stacked view's home (ORBIT_HOME), whose tilt the oblique views' home is within a
        # degree of.
        self.assertIn("const HOME_NORMAL = [0, Math.sin(ORBIT_HOME.tilt * DEG), Math.cos(ORBIT_HOME.tilt * DEG)];", self.app)

    def test_the_sweep_s_tints_are_the_coverlay_s(self) -> None:
        # styles.css --sheen in each look: BOARD_LOOK.tint of the way from white to the hue of its polyimide (the copper
        # side's outline fill: the server SVG's in Diagram, the photo's open PI in Photo), within one sRGB level.
        tint = _js_object(self.onpart, "BOARD_LOOK")["tint"]

        def sheen(pi: str) -> list:
            linear = [_linear(int(pi[k:k + 2], 16) / 255) for k in (1, 3, 5)]
            return [round(255 * _srgb(1 - tint + tint * value / max(linear))) for value in linear]

        for look, pi, selector in (("diagram", "#f4d7a1", r":is\(\.oblique-board,\.assembly-face\) > svg:is\(\.board-light,\.board-shadow\) \{[^}]*--sheen:(#\w{6});"),
                                   ("photo", "#df8401", r'body\[data-look="photo"\] \.look-scope svg\.board-light \{ --sheen:(#\w{6}); \}')):
            with self.subTest(look=look):
                found = re.search(selector, self.styles)
                self.assertIsNotNone(found, selector)
                value = found.group(1)
                self.assertLessEqual(max(abs(a - b) for a, b in zip(sheen(pi), [int(value[k:k + 2], 16) for k in (1, 3, 5)])), 1, (value, sheen(pi)))
        self.assertIn(".outline { fill:#df8401;", self.styles)

    def test_nothing_flattens_the_views_3d(self) -> None:
        # The light is on leaves (the veils, each side's SVG): a filter, an opacity, a blend mode or a clip on an element
        # that keeps its children in 3D (the oblique board, the stacked view's scene, camera, boards and faces, the coin's
        # plane) would flatten it into one picture.
        flat = {"filter": "none", "opacity": "1", "mix-blend-mode": "normal", "overflow": "visible", "isolation": "auto"}
        text = re.sub(r"/\*.*?\*/", "", self.styles, flags=re.S)
        for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
            for selector in selectors.split(","):
                last = re.split(r"\s+|>", selector.strip())[-1]
                if not re.search(r"\.(oblique-board|assembly-scene|assembly-camera|assembly-board|assembly-face|coin-plane)\b(?![-\w])", last):
                    continue
                for name, value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", body):
                    if name in flat:
                        with self.subTest(selector=selector.strip(), property=name):
                            self.assertEqual(value.strip(), flat[name])
        # The light's paths (each side's shade and sweep, the board's shadow): the outline less its cutouts, never the view
        # box (nothing painted outside the board).
        light = _js_function(self.app, "lightBoard")[2]
        self.assertIn('const rings = svg ? [...outlineRings(svg), ...outlineRings(svg, ".cutout")] : [];', light)
        self.assertIn('const d = rings.map(ring => `M${ring.map(([x, y]) => `${round6(x)} ${round6(y)}`).join("L")}Z`).join("");', light)
        paths = re.findall(r'svgEl\("path", \{([^}]*)\}', light)
        self.assertEqual(len(paths), 3, paths)
        for path in paths:
            self.assertRegex(path, r'(^|, )d, "fill-rule": "evenodd"')
        # outlineRings reads the selector it is given (the cutouts' rings are not the outline's again: an even-odd path of
        # one ring twice paints nothing).
        self.assertIn("return [...(group?.querySelectorAll(`:scope > ${selector}`) || [])].map(polygon => {", _js_function(self.app, "outlineRings")[2])


class AccessibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = _page()

    def test_the_3d_view_has_a_role_and_its_help(self) -> None:
        view = [attributes for _, attributes, _ in self.page.elements if attributes.get("id") == "cadView"][0]
        self.assertEqual(view.get("role"), "application")
        self.assertEqual(view.get("aria-describedby"), "cadHelp")
        # The help line takes no row (the user's request of 2026-11-06, "这行小字也去掉,可以缩减一行"): hidden as the page
        # opens, still the view's description, shown with the border editor's keys while the border is edited only.
        help_line = [(tag, attributes) for tag, attributes, _ in self.page.elements if attributes.get("id") == "cadHelp"]
        self.assertEqual([(tag, "hidden" in attributes) for tag, attributes in help_line], [("p", True)])
        main = (CAD / "main.js").read_text(encoding="utf-8")
        editing = main[main.index("function setEditing("): main.index("function afterBorderChange(")]
        self.assertIn('$("cadHelp").textContent = next ? EDIT_HELP : defaultHelp;', editing)
        self.assertIn('$("cadHelp").hidden = !next;', editing)
        self.assertEqual(main.count('$("cadHelp").hidden'), 1, "only the border editor shows it")
        # No rule of the line's gives it a display, which would outweigh [hidden].
        for name in ("styles.css", "theme.css"):
            rules = re.findall(r"\.cad-help\s*\{([^}]*)\}", (WEB / name).read_text(encoding="utf-8"))
            with self.subTest(file=name):
                self.assertTrue(rules)
                self.assertFalse([rule for rule in rules if "display" in rule])

    def test_only_the_status_lines_are_live(self) -> None:
        # <output> is a live region: the slider values and the state dump must not be.
        outputs = [attributes.get("id") for tag, attributes, ancestors in self.page.elements if tag == "output" and "cadWorkspace" in ancestors]
        self.assertEqual(outputs, ["cadStatus", "cadProbeOut"])
        state = [(tag, attributes) for tag, attributes, _ in self.page.elements if attributes.get("id") == "cadState"][0]
        self.assertEqual(state[0], "pre")
        self.assertIn("hidden", state[1])


class LibraryViewTests(unittest.TestCase):
    """The Library's 3D view (docs/LIBRARY_VIEW.md; the user's request of 2026-11-05, each sensor's page in the Library a
    3D view to turn): one renderer, Gen by Surface's figure (onpart.js), whose stage option Gen by Surface never passes,
    the Library's art drawn at the figure's own raster, and the one private field of three.js the stage turns by."""

    def test_gen_by_surface_passes_no_stage(self) -> None:
        # main.js makes the figure as it did: no stage, so the figure is the object it was and its homes drape.js's.
        main = (CAD / "main.js").read_text(encoding="utf-8")
        calls = re.findall(r"createOnPartView\(([^;]*)\);", main)
        self.assertEqual(calls, ['$("sensorOnPart"), {onViewChange: renderState, onContext: onPartContext, probe: ON_PART_PROBE}'])
        self.assertNotIn("stage", calls[0])
        self.assertNotRegex(main, r"library_(view|stage)\.js", "Gen by Surface never loads the Library's view")

    def test_the_art_is_drawn_at_the_figures_raster(self) -> None:
        # The shots tool asks app.js for each sensor's art as main.js asks for Gen by Surface's (tools/library_write.py
        # ART_PX_PER_MM and ART_MAX_PX: main.js ON_PART_PX_PER_MM and onpart.js's texture cap).
        import sys

        sys.path.insert(0, str(ROOT / "tools"))
        try:
            import library_write
        finally:
            sys.path.remove(str(ROOT / "tools"))
        main = (CAD / "main.js").read_text(encoding="utf-8")
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"(?m)^const ON_PART_PX_PER_MM = (\d+);$", main), [str(library_write.ART_PX_PER_MM)])
        self.assertIn('askApp("fpc:board-art", {boards: result.boards, px_per_mm: ON_PART_PX_PER_MM, max_px: view.maxTexturePx});', main)
        self.assertEqual(re.findall(r"const maxTexturePx = Math\.min\((\d+), renderer\.capabilities\.maxTextureSize \|\| (\d+)\);", onpart),
                         [(str(library_write.ART_MAX_PX), str(library_write.ART_MAX_PX))])

    def test_orbit_controls_keeps_the_fields_the_stage_turns_by(self) -> None:
        # The stage rolls the camera's up to the face's normal and gives OrbitControls the axis it turns about through its
        # two private fields (the accepted risk of the design: re-check at a vendor upgrade); three.js 0.186.1 has them.
        orbit = (VENDOR / "OrbitControls.js").read_text(encoding="utf-8")
        self.assertIn("this._quat = new Quaternion().setFromUnitVectors( object.up, new Vector3( 0, 1, 0 ) );", orbit)
        self.assertIn("this._quatInverse = this._quat.clone().invert();", orbit)
        self.assertIn("_v.applyQuaternion( this._quat );", orbit)
        self.assertIn("_v.applyQuaternion( this._quatInverse );", orbit)
        self.assertIn("0.186.1", (VENDOR / "NOTICE.md").read_text(encoding="utf-8"))

    def test_the_figure_takes_an_inert_stage(self) -> None:
        # onpart.js's extension point (docs/LIBRARY_VIEW.md): an optional stage, null by default, called once at the end
        # with the figure's own objects, its return the view; and one hook, each mode's home view.homes' where a stage set
        # it, else drape.js's as before.  The figure itself never sets homes, so with no stage it is the object it was.
        onpart = (CAD / "onpart.js").read_text(encoding="utf-8")
        self.assertIn("export function createOnPartView(host, {onViewChange = () => {}, onContext = () => {}, probe = false, stage = null} = {}) {", onpart)
        self.assertIn("  const homeVector = () => new THREE.Vector3(...(view.homes?.[view.mode] || homeDirection(view.mode)));\n", onpart)
        code = "\n".join(line for line in onpart.splitlines() if not line.strip().startswith(("//", "*", "/*")))
        self.assertEqual(len(re.findall(r"\bhomes\b", code)), 1, "the figure reads view.homes once and never sets it")
        create = _js_function(onpart, "createOnPartView")[2]
        self.assertTrue(create.endswith(
            "  return stage ? stage({scene, camera, controls, renderer, canvas, look, partLook, view, place, render, requestRender, filmMaterial}, figure) : figure;\n"),
            create[-300:])
        self.assertEqual(len(re.findall(r"\bstage\b", code)), 3, "the option, its test and its call")

    def test_the_library_view_draws_from_the_sites_own_files(self) -> None:
        # The Library's view and stage (web/cad/library_view.js, library_stage.js): ES modules importing only their
        # neighbours and the vendored three.js by relative paths (no bare "three"), no request to the API or another site;
        # the stage fetches nothing (its scene is given per show) and turns by OrbitControls' two private fields alone.
        from surface.mesh import UNIT_SCALES_MM

        for name in ("library_view.js", "library_stage.js"):
            source = (CAD / name).read_text(encoding="utf-8")
            with self.subTest(module=name):
                imports = re.findall(r'(?m)^import .* from "([^"]+)";$', source)
                self.assertTrue(imports)
                self.assertEqual([path for path in imports if not re.match(r"\./[\w.-]+\.js$|\.\./vendor/three/[\w.-]+\.js$", path)], [])
                self.assertNotRegex(source, r"from\s+['\"]three['\"]")
                self.assertNotRegex(source, r"https?://")
                self.assertNotRegex(source, r"\bapi/")
                self.assertNotRegex(source, r"""fetch\(\s*[`"']/""")
                self.assertNotIn("import(", source, "nothing loaded lazily past the page's one import")
        view = (CAD / "library_view.js").read_text(encoding="utf-8")
        stage = (CAD / "library_stage.js").read_text(encoding="utf-8")
        self.assertIn('import {createOnPartView} from "./onpart.js";', view)
        self.assertIn('import {buildStack} from "./drape.js";', view)
        self.assertNotIn("fetch(", stage)
        self.assertNotIn("import.meta", stage)
        scales = re.search(r"(?m)^const UNIT_SCALES_MM = \{([^}]*)\};$", view)
        self.assertIsNotNone(scales)
        self.assertEqual({key: float(value) for key, value in re.findall(r"(\w+): ([\d.]+)", scales.group(1))}, UNIT_SCALES_MM)
        private = sorted(set(re.findall(r"\bcontrols\._(\w+)", view + stage)))
        self.assertEqual(private, ["quat", "quatInverse"])

if __name__ == "__main__":
    unittest.main()
