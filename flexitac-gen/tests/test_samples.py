"""Gen by Surface's samples (web/samples/, the step guide's "Try a sample"; the user's request of 2026-11-06): static
checks that need no browser.

- The palette (index.html #samplePalette): inside the step guide, after its three steps, a heading, a hint and eight
  tiles in samples.json's order, each a button of its own (draggable, described by the hint, titled, its name shown,
  its kind for a screen reader) with its thumbnail (alt empty, not draggable itself, the file's size), the hint saying
  click or tap by the pointer; two columns, of compact tiles on a laptop's window (the guide's column a flex column
  whose palette, not its steps, gives way), beside the steps on a narrow page, one sideways row on a phone; tiles of
  24 px and more, focus rings inside the scrollers' padding, the styles in the theme's tokens (the review of 2026-11-06).
- samples.json: eight samples, two UMI finger tips, four other fingers of distinct Library parts and two whole
  grippers; each sample's Library sensor in web/library/entries.json; a finger's mesh the Library's own; each whole
  gripper's mesh record (bytes, facets, SHA-256, unit) its file's, its 'assembled' the Library part it starts with;
  the UMI tips' thumbnails drawn looking at their contact face (the Library selection's normal), where they differ.
- The files: every file of web/samples/ a third-party file of NOTICE.md's table (re-hashed) or one of this project's
  own (NOTICE.md, samples.json, the thumbnails); each licence text the Library's copy; the thumbnails WebP of their
  recorded size; the folder within its budget (BUDGET_BYTES), each thumbnail within THUMB_BYTES; no deny-list name.
- The whole grippers: each STL starts with its Library part's facets, record for record, so the Library sensor's
  selection names the same facets; that selection grows over exactly the Library fit's facets (the finger's contact
  face) and the engine's fit of the page's request (the Library's, named as the gripper's file) gives the Library's
  proposal #1 build; with the scenes line's files present (web/library/scenes/<part>.json and its bodies) each STL is
  the assembly of that scene, byte for byte.
- main.js: the samples' index and drag type, the drop on the 3D view's whole window taking a sample before a file,
  ./?sample=<id> read and written, a whole gripper's fit asked of the server (its shipped fit the request alone), a
  sample's build waiting for one under way, the build settling its own state, a sample holding the model shown until
  its mesh is in hand, the sample on its way live, the one shown framed again, the tiles wired; viewer.js's markers
  sized from a whole gripper's finger; tools/sample_grippers.py private, tools/browser/sample_thumbs.py public;
  Python 3.9.

The browser checks are tools/browser/sample_checks.py.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import re
import struct
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
SAMPLES = WEB / "samples"
LIBRARY = WEB / "library"
sys.path.insert(0, str(ROOT))

try:
    from test_web_theme import parse_css
except ImportError:  # run as a package
    from tests.test_web_theme import parse_css

FORMAT = "flexitac-samples/v1"
# The folder's budget: the two whole grippers (about 296 KB), the thumbnails (about 9 KB), the licence texts, the
# notice and the index (the set of 2026-11-06: 330 KB); each thumbnail at most THUMB_BYTES.
BUDGET_BYTES = 360_000
THUMB_BYTES = 8_000
THUMB_SIZE = (240, 110)
OWN = {"NOTICE.md", "samples.json"}
DENIED_NAME = re.compile(r"robotiq|xarm|ufactory", re.IGNORECASE)


def webp_size(data: bytes):
    """(width, height) of a WebP file's canvas, or None: its RIFF header, then the VP8X, VP8L or VP8 layout."""

    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP" or struct.unpack("<I", data[4:8])[0] + 8 != len(data):
        return None
    chunk, body = data[12:16], data[20:]
    if chunk == b"VP8X":
        return 1 + int.from_bytes(body[4:7], "little"), 1 + int.from_bytes(body[7:10], "little")
    if chunk == b"VP8L" and body[0] == 0x2F:
        bits = int.from_bytes(body[1:5], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8 " and body[3:6] == b"\x9d\x01\x2a":
        return int.from_bytes(body[6:8], "little") & 0x3FFF, int.from_bytes(body[8:10], "little") & 0x3FFF
    return None


def records(data: bytes) -> list:
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * count, "not a binary STL"
    return [data[84 + 50 * index:134 + 50 * index] for index in range(count)]


def assemble(name: str, scene: dict, part: bytes, bodies: dict) -> bytes:
    """A scene's whole gripper as tools/sample_grippers.py writes it (redone here: the tool is private): the part, the
    mate, the bodies, each facet under its matrix (float32, a mirror's winding kept outward, the identity's bytes)."""

    unpack = struct.Struct("<12fH")

    def f32(value):
        return struct.unpack("<f", struct.pack("<f", value))[0]

    def moved(record, matrix):
        rotation = [row[:3] for row in matrix[:3]]
        shift = [row[3] for row in matrix[:3]]
        if all(rotation[i][j] == (1.0 if i == j else 0.0) for i in range(3) for j in range(3)) and shift == [0.0, 0.0, 0.0]:
            return record
        values = unpack.unpack(record)
        det = (rotation[0][0] * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
               - rotation[0][1] * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
               + rotation[0][2] * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0]))
        turn = lambda v, o: [rotation[i][0] * v[0] + rotation[i][1] * v[1] + rotation[i][2] * v[2] + o[i] for i in range(3)]  # noqa: E731
        normal = turn(values[0:3], [0.0, 0.0, 0.0])
        length = math.sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2])
        normal = [c / length for c in normal] if length > 0 else [0.0, 0.0, 0.0]
        points = [turn(values[3 + 3 * k:6 + 3 * k], shift) for k in range(3)]
        if det < 0:
            points = [points[0], points[2], points[1]]
        return unpack.pack(*[f32(v) for v in normal + points[0] + points[1] + points[2]], 0)

    out = list(records(part))
    if scene["mate"]["part"]:
        out += [moved(record, scene["mate"]["matrix"]) for record in records(part)]
    for body in scene["bodies"]:
        out += [moved(record, body["matrix"]) for record in records(bodies[body["mesh"]])]
    header = f"FlexiTac-Gen sample {name}: assembled from the Library scene of {scene['part']}".encode("ascii")[:80]
    return header.ljust(80, b" ") + struct.pack("<I", len(out)) + b"".join(out)


class _Palette(HTMLParser):
    """The elements of index.html: each start tag's (tag, attributes, the ids of its open ancestors), and the text of
    each tile's spans."""

    VOID = {"input", "meta", "link", "br", "img", "hr", "source", "area", "base", "col", "embed", "param", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.elements, self.stack, self.tiles, self.span = [], [], [], None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.elements.append((tag, attributes, [a.get("id") for _, a in self.stack if a.get("id")]))
        if tag == "button" and "data-sample" in attributes:
            self.tiles.append({"button": attributes, "img": None, "spans": {}, "ancestors": [a.get("id") for _, a in self.stack if a.get("id")]})
        elif self.tiles and any(t == "button" and "data-sample" in a for t, a in self.stack):
            if tag == "img":
                self.tiles[-1]["img"] = attributes
            if tag == "span":
                self.span = attributes.get("class", "")
                self.tiles[-1]["spans"][self.span] = ""
        if tag not in self.VOID:
            self.stack.append((tag, attributes))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag == "span":
            self.span = None
        while self.stack:
            if self.stack.pop()[0] == tag:
                break

    def handle_data(self, data):
        if self.span is not None and self.tiles:
            self.tiles[-1]["spans"][self.span] += data


class SamplesDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads((SAMPLES / "samples.json").read_text(encoding="utf-8"))
        cls.samples = cls.index["samples"]
        cls.entries = json.loads((LIBRARY / "entries.json").read_text(encoding="utf-8"))

    def test_eight_samples_two_umi_tips_four_fingers_two_whole_grippers(self) -> None:
        self.assertEqual(self.index["format"], FORMAT)
        ids = [sample["id"] for sample in self.samples]
        self.assertEqual(len(ids), 8)
        self.assertEqual(len(set(ids)), 8)
        for sample in self.samples:
            with self.subTest(sample=sample["id"]):
                self.assertRegex(sample["id"], r"^[a-z0-9][a-z0-9.-]*$")
                self.assertIn(sample["library"], self.entries["variants"], "its sensor is a Library sensor")
                self.assertTrue(sample["name"] and sample["title"] and sample["kind"])
                self.assertLessEqual(len(sample["name"]), 15, "the name fits its tile on one line")
                self.assertIsNone(DENIED_NAME.search(json.dumps(sample)))
        parts = [self.entries["variants"][sample["library"]]["part"] for sample in self.samples]
        kinds = [("gripper" if "mesh" in sample else "umi" if parts[index].startswith("umi-") else "finger") for index, sample in enumerate(self.samples)]
        self.assertEqual(kinds, ["umi"] * 2 + ["finger"] * 4 + ["gripper"] * 2, "two UMI tips, four fingers, two whole grippers, in that order")
        umi = [self.entries["parts"][part].get("family") for part in parts[:2]]
        self.assertEqual(umi, ["umi-tapers", "umi-tapers"], "the UMI tips are two of the tapered family")
        self.assertEqual(len(set(parts[:2])), 2)
        self.assertNotEqual(parts[0].split("-tip")[0], parts[1].split("-tip")[0], "a trapezoid and a convex arc: two shapes")
        self.assertEqual(len(set(parts[2:6])), 4, "four distinct fingers")
        self.assertFalse(set(parts[2:6]) & set(parts[6:]), "the fingers are other parts than the whole grippers'")
        self.assertNotIn("trossen-widowx-ai", parts, "the Library's largest mesh (3.8 MB) is no sample")
        for sample, part in zip(self.samples, parts):
            with self.subTest(sample=sample["id"]):
                self.assertEqual(self.entries["variants"][sample["library"]]["pitch_mm"], 2, "each sample's sensor is its part's 2 mm one")
                if "mesh" not in sample:
                    self.assertEqual(sample["id"], part, "a finger sample is named as its Library part")

    def test_whole_gripper_records_match_their_files(self) -> None:
        grippers = [sample for sample in self.samples if "mesh" in sample]
        for sample in grippers:
            with self.subTest(sample=sample["id"]):
                mesh = sample["mesh"]
                data = (SAMPLES / mesh["file"]).read_bytes()
                self.assertEqual(mesh["name"], mesh["file"])
                self.assertEqual((mesh["bytes"], mesh["facets"], mesh["sha256"], mesh["unit"]),
                                 (len(data), (len(data) - 84) // 50, hashlib.sha256(data).hexdigest(), "mm"))
                part = self.entries["variants"][sample["library"]]["part"]
                self.assertEqual(sample["assembled"], {"part": f"library/meshes/{part}.stl", "scene": f"library/scenes/{part}.json"})
                self.assertEqual(self.entries["parts"][part]["mesh"]["file"], f"meshes/{part}.stl")

    def test_the_files_are_tabled_or_the_project_s_own_and_within_budget(self) -> None:
        notice = (SAMPLES / "NOTICE.md").read_text(encoding="utf-8")
        tabled = {}
        for line in notice.splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) == 5 and cells[0].startswith("`") and cells[4].startswith("`"):
                tabled[cells[0].strip("`")] = cells
        thumbs = {sample["thumb"]["src"] for sample in self.samples}
        grippers = {sample["mesh"]["file"] for sample in self.samples if "mesh" in sample}
        found, total = set(), 0
        for path in sorted(SAMPLES.rglob("*")):
            if not path.is_file():
                continue
            name = path.relative_to(SAMPLES).as_posix()
            found.add(name)
            total += path.stat().st_size
            with self.subTest(file=name):
                self.assertIsNone(DENIED_NAME.search(name))
                if name in OWN or name in thumbs:
                    continue
                self.assertIn(name, tabled, "a third-party file is a row of NOTICE.md's table")
                self.assertEqual(tabled[name][4].strip("`"), hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(set(tabled), found - OWN - thumbs, "every tabled file is here")
        self.assertEqual(grippers | {"licenses/mujoco_menagerie-franka_emika_panda.txt", "licenses/mujoco_menagerie-trossen_wx250s.txt"},
                         set(tabled))
        self.assertLessEqual(total, BUDGET_BYTES, "web/samples/ over its budget")
        for name in grippers:
            with self.subTest(gripper=name):
                row = tabled[name]
                self.assertRegex(row[1], r"mujoco_menagerie `f3b6013`")
                self.assertTrue(row[3].startswith("modified: assembled from"), row[3])
                self.assertIn("decimated", row[3])
                self.assertRegex(row[2], r"^(Apache-2\.0|BSD-3-Clause, Trossen Robotics), `licenses/[\w.-]+\.txt`$")
                self.assertIn(re.search(r"`(licenses/[\w.-]+\.txt)`", row[2]).group(1), tabled)
        for name in tabled:
            if name.startswith("licenses/"):
                with self.subTest(licence=name):
                    self.assertEqual((SAMPLES / name).read_bytes(), (LIBRARY / name).read_bytes(), "the Library's licence text")
        self.assertIn("f3b6013629c7b94f8ee93fd977b161fa8350f9bc", notice, "the source pinned to its commit")
        self.assertIn("section 4(b)", notice, "the Apache-2.0 file's change stated")

    def test_thumbnails_are_webp_of_their_size(self) -> None:
        for sample in self.samples:
            with self.subTest(sample=sample["id"]):
                thumb = sample["thumb"]
                self.assertEqual(thumb["src"], f"thumbs/{sample['id']}.webp")
                data = (SAMPLES / thumb["src"]).read_bytes()
                self.assertEqual(webp_size(data), (thumb["width"], thumb["height"]))
                self.assertEqual((thumb["width"], thumb["height"]), THUMB_SIZE)
                self.assertLessEqual(len(data), THUMB_BYTES)
                view = thumb["view"]
                self.assertEqual((len(view["dir"]), len(view["up"])), (3, 3))
                cross = [view["dir"][1] * view["up"][2] - view["dir"][2] * view["up"][1],
                         view["dir"][2] * view["up"][0] - view["dir"][0] * view["up"][2],
                         view["dir"][0] * view["up"][1] - view["dir"][1] * view["up"][0]]
                self.assertGreater(math.hypot(*cross), 0.1, "the view's up is not along its direction")

    def test_the_umi_tips_are_drawn_looking_at_their_contact_face(self) -> None:
        # The two tapered tips differ only in the contact face's outline toward the tip (the review of 2026-11-06: an
        # oblique side view had drawn one picture twice): each thumbnail looks within 25 degrees of the face's normal
        # (the Library fit's selection), the finger's length across the picture.
        for sample in self.samples[:2]:
            with self.subTest(sample=sample["id"]):
                fit = json.loads((LIBRARY / self.entries["variants"][sample["library"]]["fit"]).read_text(encoding="utf-8"))
                normal = fit["reply"]["selection"]["normal"]
                view = sample["thumb"]["view"]
                length = math.sqrt(view["dir"][0] ** 2 + view["dir"][1] ** 2 + view["dir"][2] ** 2)
                cosine = (view["dir"][0] * normal[0] + view["dir"][1] * normal[1] + view["dir"][2] * normal[2]) / length
                self.assertGreater(cosine, math.cos(math.radians(25)), (view, normal))
        self.assertEqual(self.samples[0]["thumb"]["view"], self.samples[1]["thumb"]["view"], "the two seen alike, so their outlines compare")

    def test_the_tools_private_and_public_and_python_3_9(self) -> None:
        spec = importlib.util.spec_from_file_location("fpc_export_public_samples", ROOT / "tools" / "export_public.py")
        export_public = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(export_public)
        covered = lambda path: any(path == root or path.startswith(root + "/") for root in export_public.PUBLIC)  # noqa: E731
        self.assertTrue(covered("web/samples/samples.json") and covered("tools/browser/sample_thumbs.py") and covered("tools/browser/sample_checks.py"))
        self.assertFalse(covered("tools/sample_grippers.py"), "the assembly tool is private (it reads the scenes line's files)")
        for path in (ROOT / "tests" / "test_samples.py", ROOT / "tools" / "browser" / "sample_thumbs.py", ROOT / "tools" / "browser" / "sample_checks.py",
                     ROOT / "tools" / "sample_grippers.py"):
            if path.is_file():
                with self.subTest(file=path.name):
                    ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 9))


class WholeGripperTests(unittest.TestCase):
    """Each whole gripper starts with its Library part, so the Library sensor's selection is that finger's face; the
    engine fits the page's request to the Library's own sensor."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.samples = [sample for sample in json.loads((SAMPLES / "samples.json").read_text(encoding="utf-8"))["samples"] if "mesh" in sample]
        cls.entries = json.loads((LIBRARY / "entries.json").read_text(encoding="utf-8"))

    def library(self, sample):
        variant = self.entries["variants"][sample["library"]]
        part = self.entries["parts"][variant["part"]]
        fit = json.loads((LIBRARY / variant["fit"]).read_text(encoding="utf-8"))
        return variant, (LIBRARY / part["mesh"]["file"]).read_bytes(), fit

    def test_two_whole_grippers(self) -> None:
        self.assertEqual(len(self.samples), 2)

    def test_each_starts_with_its_part_record_for_record(self) -> None:
        for sample in self.samples:
            with self.subTest(sample=sample["id"]):
                _, part, _ = self.library(sample)
                gripper = records((SAMPLES / sample["mesh"]["file"]).read_bytes())
                self.assertEqual(gripper[:len(records(part))], records(part))
                self.assertGreater(len(gripper), 2 * len(records(part)), "the other finger and the gripper's bodies follow")
                self.assertTrue((SAMPLES / sample["mesh"]["file"]).read_bytes()[:80].startswith(f"FlexiTac-Gen sample {sample['id']}".encode()))

    def test_the_library_selection_is_the_finger_s_face_and_the_fit_its_sensor(self) -> None:
        from surface import api

        for sample in self.samples:
            with self.subTest(sample=sample["id"]):
                variant, part, fit = self.library(sample)
                mesh = (SAMPLES / sample["mesh"]["file"]).read_bytes()
                request = dict(fit["request"], name=sample["mesh"]["name"])
                selection = api.select_surface({"name": request["name"], "selection": request["selection"]}, mesh)["selection"]
                self.assertEqual(selection["facets"], fit["reply"]["selection"]["facets"], "the same facets as on the finger alone")
                self.assertLess(max(selection["facets"]), len(records(part)), "all on the sensor finger")
                reply = json.loads(json.dumps(api.fit(request, mesh), allow_nan=False))
                self.assertTrue(reply["ok"])
                self.assertEqual(reply["mesh"]["sha256"], sample["mesh"]["sha256"])
                self.assertEqual(reply["proposals"][0]["build_id"], variant["build_id"], "the Library's sensor of the finger")

    def test_each_is_its_scene_s_assembly_when_the_scene_is_here(self) -> None:
        for sample in self.samples:
            with self.subTest(sample=sample["id"]):
                scene_path = WEB / sample["assembled"]["scene"]
                if not scene_path.is_file():
                    self.skipTest(f"{sample['assembled']['scene']} is not in this tree (the scenes line's)")
                scene = json.loads(scene_path.read_text(encoding="utf-8"))
                part = (WEB / sample["assembled"]["part"]).read_bytes()
                self.assertEqual(hashlib.sha256(part).hexdigest(), scene["part_mesh_sha256"])
                bodies = {}
                for body in scene["bodies"]:
                    data = (LIBRARY / body["mesh"]).read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), body["sha256"], body["mesh"])
                    bodies[body["mesh"]] = data
                self.assertEqual(assemble(sample["id"], scene, part, bodies), (SAMPLES / sample["mesh"]["file"]).read_bytes(),
                                 "re-assemble with tools/sample_grippers.py")

    def test_the_assembly_on_a_fixture(self) -> None:
        # A one-facet part, a body under a mirror and a mate turned 180 degrees: the identity keeps the bytes, a
        # mirror swaps the last two vertices, every value float32.
        facet = struct.pack("<12fH", 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 7)
        part = b"p".ljust(80, b" ") + struct.pack("<I", 1) + facet
        scene = {"part": "x", "mate": {"part": True, "matrix": [[-1, 0, 0, 0], [0, -1, 0, 10], [0, 0, 1, 0], [0, 0, 0, 1]]},
                 "bodies": [{"mesh": "b", "matrix": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0.1], [0, 0, 0, 1]]}]}
        out = records(assemble("s", scene, part, {"b": part}))
        self.assertEqual(out[0], facet)
        self.assertEqual(struct.unpack("<12f", out[1][:48])[3:], (0.0, 10.0, 0.0, -1.0, 10.0, 0.0, 0.0, 9.0, 0.0))
        mirrored = struct.unpack("<12f", out[2][:48])
        self.assertEqual(mirrored[3:], tuple(struct.unpack("<f", struct.pack("<f", v))[0] for v in (0, 0, 0.1, 0, 1, 0.1, 1, 0, 0.1)))
        self.assertEqual(mirrored[2], -1.0)


class PaletteMarkupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.page = _Palette()
        cls.page.feed(cls.html)
        cls.samples = json.loads((SAMPLES / "samples.json").read_text(encoding="utf-8"))["samples"]

    def test_the_palette_is_under_the_guide_s_steps(self) -> None:
        ids = [attributes.get("id") for _, attributes, _ in self.page.elements if attributes.get("id")]
        self.assertEqual(len(ids), len(set(ids)), "unique ids")
        palette = next((ancestors for _, attributes, ancestors in self.page.elements if attributes.get("id") == "samplePalette"), None)
        self.assertEqual(palette, ["flowGuide"], "the palette is the guide's child")
        self.assertLess(ids.index("cadGuide"), ids.index("samplePalette"), "after the three steps")
        order = [ids.index(name) for name in ("samplePalette", "samplePaletteTitle", "samplePaletteHint")]
        self.assertEqual(order, sorted(order))
        self.assertIn('aria-labelledby="samplePaletteTitle"', self.html)
        self.assertRegex(self.html, r'<h3 class="sample-palette-title" id="samplePaletteTitle">Try a sample</h3>')
        self.assertIn('id="samplePaletteHint">Drag onto the 3D view, or <span class="sample-hint-click">click</span>'
                      '<span class="sample-hint-tap">tap</span>.</p>', self.html)

    def test_eight_tiles_in_the_index_s_order(self) -> None:
        tiles = self.page.tiles
        self.assertEqual([tile["button"]["data-sample"] for tile in tiles], [sample["id"] for sample in self.samples])
        for tile, sample in zip(tiles, self.samples):
            with self.subTest(sample=sample["id"]):
                button, img = tile["button"], tile["img"]
                self.assertIn("samplePalette", tile["ancestors"])
                self.assertEqual((button.get("type"), button.get("class"), button.get("draggable"), button.get("aria-describedby"), button.get("title")),
                                 ("button", "sample", "true", "samplePaletteHint", sample["title"]))
                self.assertEqual((img.get("src"), img.get("width"), img.get("height"), img.get("alt"), img.get("draggable")),
                                 (f"static/samples/{sample['thumb']['src']}", str(sample["thumb"]["width"]), str(sample["thumb"]["height"]), "", "false"))
                self.assertEqual(tile["spans"], {"sample-name": sample["name"], "sample-kind cad-sr-only": f", {sample['kind']}"})

    def test_the_layouts_of_each_width_and_height_and_the_theme_s_tokens(self) -> None:
        styles, _ = parse_css((WEB / "styles.css").read_text(encoding="utf-8"))
        theme, _ = parse_css((WEB / "theme.css").read_text(encoding="utf-8"))

        def declared(rules, selector, conditions=()):
            out = {}
            for rule in rules:
                if selector in rule.selectors and tuple(rule.conditions) == tuple(conditions):
                    out.update({name: value for name, value, _ in rule.declarations})
            return out

        def px(value):
            return int(value.rstrip("px"))

        # Two columns of tiles, each a thumbnail over its name, on a tall desktop window.
        self.assertEqual(declared(styles, ".sample-grid")["grid-template-columns"], "repeat(2,minmax(0,1fr))")
        self.assertGreaterEqual(px(declared(styles, ".sample")["min-height"]), 24, "a target of 24 px and more")
        self.assertEqual(declared(styles, ".sample img")["aspect-ratio"].replace(" ", ""), "%d/%d" % (THUMB_SIZE[0] // 10, THUMB_SIZE[1] // 10))
        self.assertEqual(declared(styles, ".sample img")["pointer-events"], "none", "the tile, not its picture, is dragged")
        # Compact tiles (a thumbnail beside its name, two lines at most) on a laptop's window, a narrow page's and a phone's.
        compact = ("@media (min-width:981px) and (max-height:919px), (max-width:980px)",)
        tile = declared(styles, ".sample-grid .sample", compact)
        self.assertEqual(tile["flex-direction"], "row")
        self.assertGreaterEqual(px(tile["min-height"]), 24, "a target of 24 px and more")
        self.assertEqual(declared(styles, ".sample-grid .sample-name", compact)["-webkit-line-clamp"], "2")
        # Over 980 px the guide's column is a flex column: the palette's grid scrolls inside it when the window is too
        # short, never the steps; the scroller's padding holds the tiles' focus rings (2 px, 1 px off: 3 px out).
        wide = ("@media (min-width:981px)",)
        guide = declared(styles, 'body[data-mode="cad"] .flow-guide', wide)
        self.assertEqual((guide["display"], guide["flex-direction"]), ("flex", "column"))
        self.assertEqual(declared(styles, ".sample-palette", wide)["min-height"], "0")
        grid = declared(styles, ".sample-grid", wide)
        self.assertEqual((grid["overflow-y"], grid["padding"], grid["margin"]), ("auto", "3px", "0 -3px"))
        # From 760 to 980 px beside the steps (they keep their own width): two columns of four.
        side = ("@media (min-width:760px) and (max-width:980px)",)
        self.assertEqual(declared(styles, 'body[data-mode="cad"] .flow-guide', side)["grid-template-columns"], "max-content minmax(0,1fr)")
        self.assertEqual((declared(styles, ".sample-palette", side)["grid-column"], declared(styles, ".sample-palette", side)["grid-row"]), ("2", "2"))
        self.assertEqual(declared(styles, ".sample-grid", side)["padding"], "3px")
        # Under 760 px one row that scrolls sideways under the steps, its rings inside its padding.
        phone = declared(styles, ".sample-grid", ("@media (max-width:759px)",))
        self.assertEqual((phone["grid-auto-flow"], phone["overflow-x"], phone["padding"]), ("column", "auto", "3px"), "one row that scrolls sideways")
        self.assertGreaterEqual(px(phone["grid-auto-columns"]), 24)
        # The hint: click, or tap on a touch screen.
        self.assertEqual(declared(styles, ".sample-hint-tap")["display"], "none")
        coarse = ("@media (pointer:coarse)",)
        self.assertEqual((declared(styles, ".sample-hint-click", coarse)["display"], declared(styles, ".sample-hint-tap", coarse)["display"]), ("none", "inline"))
        # The theme: the tokens for the tile's colours, the action blue for the one shown, the focus ring, the lightbox
        # grey behind the thumbnail in either scheme (no dark rule of its own), nothing that moves.
        tile = declared(theme, ".sample")
        self.assertEqual((tile["background-color"], tile["color"]), ("var(--surface)", "var(--text)"))
        self.assertEqual(declared(theme, ".sample.is-current")["border-color"], "var(--accent)")
        self.assertEqual(declared(theme, ".sample:focus-visible")["outline"], "2px solid var(--focus)")
        self.assertEqual(declared(theme, ".sample img")["background"], "#f5f5f7")
        for rule in theme:
            for selector in rule.selectors:
                if "sample" in selector:
                    with self.subTest(selector=selector):
                        self.assertFalse(any("prefers-color-scheme" in condition for condition in rule.conditions))
                        self.assertFalse({name for name, _, _ in rule.declarations} & {"transition", "transform", "animation", "opacity"})


class SampleScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = (WEB / "cad" / "main.js").read_text(encoding="utf-8")

    def function(self, name: str) -> str:
        match = re.search(r"\n(?:async )?function %s\(.*?\n}\n" % re.escape(name), self.main, re.S)
        self.assertIsNotNone(match, name)
        return match.group(0)

    def test_the_index_the_drag_type_and_the_address(self) -> None:
        self.assertIn('const SAMPLES_INDEX = "static/samples/samples.json";', self.main)
        self.assertIn('const SAMPLE_TYPE = "application/x-flexitac-sample";', self.main)
        self.assertIn('const SAMPLE_ID = new URLSearchParams(location.search).get("sample") || "";', self.main)
        self.assertRegex(self.function("loadDefaultPart"), r"LIBRARY_ID \? await libraryPart\(LIBRARY_ID\) : SAMPLE_ID \? await samplePart\(SAMPLE_ID\)")
        self.assertIn('pairs.push(`sample=${encodeURIComponent(id)}`);', self.function("sampleAddress"))
        self.assertIn('!["part", "sample"].includes(pair.split("=")[0])', self.function("dropPartParameter"), "the user's own file drops ?sample too")

    def test_the_drop_takes_a_sample_before_a_file(self) -> None:
        # On the 3D view's whole window, the tools drawn over it too (the review of 2026-11-06), lit until the drag
        # leaves it.
        self.assertIn('const wrap = view.closest(".cad-view-wrap") || view;', self.main)
        self.assertIn('wrap.addEventListener("dragover", event => { event.preventDefault(); view.classList.add("is-dropping"); });', self.main)
        self.assertIn('wrap.addEventListener("dragleave", event => { if (!wrap.contains(event.relatedTarget)) view.classList.remove("is-dropping"); });', self.main)
        self.assertNotIn('view.addEventListener("drop"', self.main)
        drop = re.search(r'wrap\.addEventListener\("drop", event => \{.*?\n  \}\);', self.main, re.S).group(0)
        self.assertLess(drop.index("getData(SAMPLE_TYPE)"), drop.index("loadFile("))
        self.assertRegex(drop, r"if \(sample\) loadSample\(sample\);\s*else loadFile\(event\.dataTransfer\?\.files\?\.\[0\]\);")
        wire = self.function("wireSamples")
        for text in ('addEventListener("dragstart"', "setData(SAMPLE_TYPE, tile.dataset.sample)", 'addEventListener("click"', "loadSample(tile.dataset.sample)"):
            self.assertIn(text, wire)
        self.assertIn("prefers-reduced-motion: reduce", wire, "its scroll into sight respects reduced motion")

    def test_a_sample_loads_its_part_alone(self) -> None:
        # The user's request of 2026-11-06 ("测试用的sensor,不要托进去之后直接就生成好了 ... 只有最开始default的umi finger需要这样"):
        # a sample's part is loaded as the default file and nothing more, no fit fetched, no face selected, no sensor built;
        # the visitor clicks the face and presses Generate sensor, which the server fits (no shipped fit is the sample's).
        load = self.function("loadSample")
        for text in ("if (sampleLoading(id)) return;", "pending.load = cad.seq.load;", "leaveLibrary();", "{isDefault: true}", "sampleAddress(id);",
                     "cad.defaultFit = null;", "cad.entry = entry;", "libraryNote();", "const warning = `The sample ${name} was not loaded (${error.message}).`;",
                     'setStatus("warning", warning);'):
            self.assertIn(text, load)
        for text in ("buildDefaultSensor", "applyLibraryOptions", "autoSelect", "runSelect", "runFit", "oneStep", "generate(", "commitBorder", "part.fit", "fitError"):
            self.assertNotIn(text, load, "a sample builds nothing at once")
        self.assertLess(load.index("leaveLibrary();"), load.index("loadFile("))
        self.assertLess(load.index("cad.defaultFit = null;"), load.index("loadFile("))
        opened = self.function("loadDefaultPart")
        self.assertIn('  if (entry?.sample) cad.defaultBuild = "idle";\n', opened, "./?sample=<id> as the page opens: no build pending")
        self.assertIn("      if (!entry?.sample) await buildDefaultSensor();\n", opened, "the default part's and a Library sensor's built at once, a sample's not")
        self.assertIn("part.fit ? fetch(part.fit)", opened, "no fit fetched for a sample")
        lookup = self.function("sampleLookup")
        self.assertIn("const found = await libraryPart(sample.library, {fallback: false});", lookup)
        self.assertIn("{url: found.part.url, name: found.part.name}", lookup, "a Library finger's mesh, not its fit")
        self.assertNotIn("fit:", lookup)
        for gone in ("shippedFit", "ownMesh", "whenBuilt"):
            self.assertNotIn(gone, self.main, "dead with the samples' builds")
        self.assertIn("const shipped = cad.defaultFile && cad.defaultFit && canonical(header(extra)) === canonical(cad.defaultFit.request);", self.main)
        self.assertIn("sample: renderSamples(),", self.main, "the state dump says the sample shown and on its way")

    def test_a_model_loaded_has_no_face_selected(self) -> None:
        # The same request: the user's own file (or a sample) loads with no face selected, in quick mode too (it had its
        # largest flat face selected, autoSelect); the status asks for the face.  The default part's sensor alone is built.
        inspect = self.function("inspectMesh")
        self.assertNotIn("autoSelect", inspect)
        self.assertNotIn("candidates?.flat", inspect)
        self.assertIn('setStatus("ok", `${cad.fileName}: ${plural(reply.mesh.facets, "facet")}. Click the face the sensor goes on.`);', inspect)
        self.assertNotIn("autoSelect", self.function("loadFile"))
        self.assertEqual(self.main.count("autoSelect("), 3, "its definition, pickSurface's and a click's (onViewClick)")
        self.assertIn("const face = cad.inspect?.candidates?.flat?.[0];", self.function("buildDefaultSensor"), "the default part's face")

    def test_a_whole_gripper_s_selection_on_its_finger_is_seen_from_its_camera(self) -> None:
        # The visitor's selection on the Library finger of a whole gripper (its first facets) framed from the sample's
        # camera wherever the selection is framed: along the face's normal the camera would stand in the other finger.
        view = self.function("sampleView")
        self.assertIn("facets.every(facet => facet < sample.partFacets)", view)
        self.assertIn("cad.viewer.lookAt(centre, sample.camera, ", view)
        self.assertIn("return true;", view)
        self.assertIn("  if (sampleView()) return;\n", self.function("lookAtSelection"))
        self.assertIn('if (cad.selection) lookAtSelection(); else cad.viewer.view("iso", viewClear());', self.function("frameSample"))

    def test_a_build_settles_its_own_state_and_a_sample_keeps_the_model_shown_until_its_mesh_is_in_hand(self) -> None:
        # The review of 2026-11-06: a build superseded by the user's own file had stayed "running" (Generate sensor
        # disabled for good), and a sample that failed to load had stopped the shown one's build.
        build = self.function("buildDefaultSensor")
        self.assertIn("const run = (cad.buildRun = {});", build)
        self.assertIn("  } finally {\n    if (cad.buildRun === run) {\n      cad.buildRun = null;\n      if (!built) cad.defaultBuild = \"stopped\";", build)
        self.assertEqual(build.count("return true;"), 1)
        self.assertLess(build.index('cad.defaultBuild = "done";'), build.index("built = true;"))
        self.assertIn('if (!cad.buildRun) cad.defaultBuild = "stopped";', build, "a call no longer current says stopped, unless a later build runs")
        tail = self.function("loadDefaultPart")
        self.assertIn('  if (cad.defaultBuild === "pending") cad.defaultBuild = "stopped";\n', tail, "its tail leaves a build under way alone")
        self.assertNotIn('cad.defaultBuild === "running") cad.defaultBuild', tail)
        load = self.function("loadSample")
        # cad.seq.load moves before the fetch only for the default part still on its way (nothing shown yet); loadFile
        # takes it once the sample's mesh is in hand, and the sample answers to that one from then on.
        self.assertEqual(load.count("cad.seq.load +="), 1)
        self.assertLess(load.index('if (cad.defaultPart === "loading") cad.seq.load += 1;'), load.index("await sampleLookup(id)"))
        self.assertIn("const live = () => ticket === cad.sampleTicket && pending.load === cad.seq.load;", load)
        fetched = load.index("const bytes = await reply.blob();")
        self.assertLess(fetched, load.index("if (!live()) return;"))
        self.assertLess(load.index("if (!live()) return;"), load.index('if (cad.mode !== "cad") {', fetched), "Rectangular chosen meanwhile: not loaded")
        self.assertLess(load.index('if (cad.mode !== "cad") {', fetched), load.index("leaveLibrary();"))
        self.assertIn("if (cad.samplePending === pending) cad.samplePending = null;", load, "held until its part is loaded")
        # The one shown: framed again, not reloaded.
        self.assertIn("  if (sampleShown() === id) {\n", load)
        self.assertIn("frameSample();", load)
        self.assertLess(load.index("if (sampleShown() === id"), load.index("await sampleLookup(id)"))
        # Not loaded: the veil goes, the drop zone back if no model is shown, the warning; said again once the shown build
        # lands (the review's mutant, the veil left on for good, had passed every test).
        self.assertIn("  } catch (error) {\n    if (!live()) return;\n    setLoading(null);\n    if (!cad.mesh && !cad.viewerError) $(\"cadDrop\").hidden = false;\n", load)
        self.assertIn('whenSettled().then(() => {', load)
        self.assertIn("if (cad.buildRun || cad.stepRunning || cad.pendingBuild || cad.busy.size) {", load, "the visitor's Generate sensor too")
        self.assertIn("!(cad.buildRun || cad.stepRunning || cad.pendingBuild || cad.busy.size)", self.function("whenSettled"))
        self.assertIn("pending.load === cad.seq.load", self.function("sampleLoading"))
        self.assertIn("const pending = sampleLoading() ? cad.samplePending.id : null;", self.function("renderSamples"))

    def test_a_whole_gripper_s_markers_as_on_its_finger(self) -> None:
        viewer = (WEB / "cad" / "viewer.js").read_text(encoding="utf-8")
        self.assertIn("function setMarkScale(radiusMm) { markRadius = radiusMm > 0 ? radiusMm : null; }", viewer)
        self.assertIn("const marks = () => (markRadius > 0 ? Math.min(markRadius, model.radius) : model.radius);", viewer)
        self.assertIn("    markRadius = null;\n    model.facets = facets;", viewer, "each new mesh its own size again")
        self.assertEqual(viewer.count("marks() * 0."), 6, "the exit's, hover's and border's tubes, their dashes, the overlay's end markers")
        self.assertIsNone(re.search(r"model\.radius \* 0\.0(06|04|2|25)\b", viewer))
        self.assertIn("setMarkScale,", viewer)
        self.assertIn("cad.viewer.setMarkScale(sampleFingerRadius());", self.function("showMesh"))
        self.assertIn("partFacets: sample.mesh ? found.part.facets || 0 : 0", self.function("sampleLookup"))
        self.assertIn("facets: part.mesh.facets}", self.function("libraryPart"))
        self.assertIn("for (let i = 0; i < 9 * facets; i += 1) {", self.function("sampleFingerRadius"), "the finger's facets alone")


if __name__ == "__main__":
    unittest.main()
