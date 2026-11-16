"""tools/library_split.py: a gripper's bodies shared out by material and given their looks (the user's request of
2026-11-12, docs/LIBRARY_VIEW.md "The looks"), on small fixtures built here and on the committed look files.

- the rules: connected components after welding (0.01 mm by default), recognised by their box and triangle count; the
  triangles inside a box (all three corners); "rest"; every triangle taken once, no component empty;
- the shapes the project draws (a box, a cylinder, a prism of a convex profile): closed, facing outward, the
  project's own by name and header;
- the looks: a base look by its name, a part's own look with its evidence, never under a base look's name;
- what is written: the component files (the body's facet records, sorted, under its header with "; split"), the scene
  (its bodies, looks, part_look, smooth_deg and the look file's words after its about; every other key as it was),
  NOTICE.md's rows; the same input gives the same bytes, from the unsplit body or from its components;
- --check: a changed component, scene, row or a stray body is caught; so is a look, a crease angle, a drawn body or
  a split's NOTICE row of a part that has no look file (the reviews of 2026-11-12);
- the pins: an unsplit body of other bytes is refused, never passed over for the components of the split before; a
  body of another header splits into files that --check and a second run leave alone (the reviews of 2026-11-12);
- the committed look files give the committed files, and the base looks are the table of docs/LIBRARY_VIEW.md.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import library_split  # noqa: E402
import library_write  # noqa: E402

LIBRARY = ROOT / "web" / "library"
IDENTITY = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
TURNED = [[-1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.0, -80.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
HEADER = "modified (decimated <= 0.5 mm, m to mm) by FlexiTac-Gen 2026, see NOTICE.md"
BASE = {"format": "flexitac-library-looks/v1", "about": "tiny", "looks": {
    "anodized-black": {"for": "a dark metal", "color": "#1c1d20", "metalness": 0.6, "roughness": 0.45, "env_intensity": 1.5},
    "steel-ground": {"for": "a rail", "color": "#b4b7ba", "metalness": 1, "roughness": 0.35},
    "rubber-black": {"for": "a pad", "color": "#232325", "metalness": 0, "roughness": 0.92}}}


def facet(a, b, c) -> bytes:
    return struct.pack("<12fH", 0, 0, 1, *a, *b, *c, 0)


def tetra(x: float, size: float = 1.0) -> list:
    """A closed tetrahedron at x: four facets sharing its four corners (one connected component)."""

    p = [(x, 0, 0), (x + size, 0, 0), (x, size, 0), (x, 0, size)]
    return [facet(p[0], p[2], p[1]), facet(p[0], p[1], p[3]), facet(p[0], p[3], p[2]), facet(p[1], p[2], p[3])]


def stl(records: list, header: str = HEADER) -> bytes:
    return header.encode("ascii").ljust(80, b" ") + struct.pack("<I", len(records)) + b"".join(records)


def lightness(color: str) -> float:
    """The relative luminance (linear, Rec. 709) of an sRGB "#rrggbb"."""

    linear = [(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
              for value in (int(color[index:index + 2], 16) / 255 for index in (1, 3, 5))]
    return math.fsum(weight * value for weight, value in zip((0.2126, 0.7152, 0.0722), linear))


def volume(data: bytes) -> float:
    """A closed mesh's signed volume (positive: its facets face outward)."""

    total = []
    for record in library_split.facets(data):
        a, b, c = library_split.corners(record)
        total.append((a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6)
    return math.fsum(total)


class Fixture:
    """A tiny library (one part "grip": a body of three tetrahedra, at x 0, 10 and 20, drawn on both fingers, and a
    second body kept whole) and its look files' folder."""

    BODY = "bodies/grip/body.stl"
    PLATE = "bodies/grip/plate.stl"

    def __init__(self, folder: Path):
        self.library = folder / "library"
        self.looks = folder / "looks"
        self.records = tetra(20) + tetra(0) + tetra(10)
        self.body = stl(self.records)
        self.plate = stl(tetra(50))
        for path, data in ((self.BODY, self.body), (self.PLATE, self.plate)):
            (self.library / path).parent.mkdir(parents=True, exist_ok=True)
            (self.library / path).write_bytes(data)
        entry = lambda path, data, matrix, finger: {"mesh": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),  # noqa: E731
                                                    "triangles": library_write.stl_triangles(data), "matrix": matrix, "finger": finger}
        self.scene = {"format": "flexitac-library-scene/v1", "part": "grip", "part_mesh_sha256": "0" * 64, "about": "A tiny gripper.",
                      "frame": "the part's file axes, mm", "approach": [0.0, 0.0, 1.0], "opening": {"q_mm": 40.0, "limit_mm": 40.0},
                      "mate": {"kind": "turned", "matrix": TURNED, "part": True},
                      "bodies": [entry(self.PLATE, self.plate, IDENTITY, None), entry(self.BODY, self.body, IDENTITY, "sensor"),
                                 entry(self.BODY, self.body, TURNED, "mate")],
                      "see_through": ["mate"], "picture": "on both fingers of the open gripper"}
        (self.library / "scenes").mkdir()
        (self.library / "scenes" / "grip.json").write_text(library_split.scene_text(self.scene), encoding="utf-8")
        row = lambda path, data: (f"| `{path}` | tiny `0123456`, {Path(path).name} | MIT, Tiny, `licenses/tiny.txt` | modified: decimated "  # noqa: E731
                                  f"(quadric error metrics, 0.40 mm) | `{hashlib.sha256(data).hexdigest()}` |")
        (self.library / "NOTICE.md").write_text("# Tiny\n\n| File | Source at commit | Licence and holder | Change | SHA-256 |\n| --- | --- | --- | --- | --- |\n"
                                                + row(self.PLATE, self.plate) + "\n" + row(self.BODY, self.body) + "\n\nAfter the table.\n", encoding="utf-8")
        self.looks.mkdir()
        (self.looks / "base.json").write_text(json.dumps(BASE), encoding="utf-8")
        self.recipe = {"format": "flexitac-library-look/v1", "part": "grip", "smooth_deg": 35, "part_look": "rubber-black",
                       "about": "drawn after two photos; the cap is the project's own drawing.",
                       "looks": {"rail-steel": {"base": "steel-ground", "roughness": 0.25, "evidence": "photo 6: the rail mirrors the lamp"}},
                       "bodies": {self.PLATE: {"sha256": hashlib.sha256(self.plate).hexdigest(), "look": None},
                                  self.BODY: {"sha256": hashlib.sha256(self.body).hexdigest(), "facets_sha256": library_split.facets_sha256(self.records),
                                              "components": [
                                                  {"name": "body-rail", "look": "rail-steel", "pick": [{"box": [[9.5, -0.5, -0.5], [11.5, 1.5, 1.5]]}]},
                                                  {"name": "body-hub", "look": "steel-ground",
                                                   "pick": [{"component": {"box": [[20, 0, 0], [21, 1, 1]], "triangles": 4}}]},
                                                  {"name": "cap", "look": "steel-ground", "draw": [{"cylinder": {"from": [0, 0, 1], "to": [0, 0, 2], "radius": 0.5}}]},
                                                  {"name": "body-can", "look": "anodized-black", "pick": "rest"}]}}}
        self.write()

    def write(self, **changes) -> None:
        self.recipe.update(changes)
        (self.looks / "grip.json").write_text(json.dumps(self.recipe), encoding="utf-8")

    def run(self, *arguments) -> tuple:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = library_split.main(["--library", str(self.library), "--looks", str(self.looks), *arguments])
        return code, out.getvalue(), err.getvalue()

    def files(self) -> dict:
        return {path.relative_to(self.library).as_posix(): path.read_bytes() for path in sorted(self.library.rglob("*")) if path.is_file()}

    def scene_now(self) -> dict:
        return json.loads((self.library / "scenes" / "grip.json").read_text(encoding="utf-8"))


class SplitCase(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.fixture = Fixture(Path(folder.name))


class RuleTests(unittest.TestCase):
    """The split rules on triangle soups."""

    def test_triangles_are_joined_through_welded_corners(self) -> None:
        # Two triangles whose nearest corners are 0.004 mm apart: one component welded at 0.01 mm, two at 0.001 mm; a
        # third triangle 1 mm away is its own at both.  The components come in the order of their first triangle.
        soup = [facet((0, 0, 0), (1, 0, 0), (0, 1, 0)), facet((5, 0, 0), (6, 0, 0), (5, 1, 0)), facet((1.004, 0, 0), (2, 0, 0), (1, 1, 0))]
        self.assertEqual(library_split.components(soup, 0.01), [[0, 2], [1]])
        self.assertEqual(library_split.components(soup, 0.001), [[0], [1], [2]])
        self.assertEqual(library_split.components(soup), library_split.components(soup, library_split.WELD_MM))
        self.assertEqual(library_split.WELD_MM, 0.01)
        self.assertEqual(library_split.components(tetra(0) + tetra(10) + tetra(0.5)), [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])
        # A chain: a joins b joins c through different corners.
        chain = [facet((0, 0, 0), (1, 0, 0), (0, 1, 0)), facet((9, 9, 9), (8, 9, 9), (9, 8, 9)), facet((1, 0, 0), (2, 0, 0), (8, 9, 9))]
        self.assertEqual(library_split.components(chain), [[0, 1, 2]])
        with self.assertRaisesRegex(library_split.SplitError, "weld_mm"):
            library_split.components(soup, 0)

    def test_a_box_takes_the_triangles_wholly_inside(self) -> None:
        soup = tetra(0) + tetra(10) + [facet((0.5, 0.5, 0.5), (1, 0.5, 0.5), (3, 0.5, 0.5))]
        groups = library_split.components(soup)
        self.assertEqual(library_split.picked({"box": [[0, 0, 0], [1, 1, 1]]}, soup, groups, "x"), {0, 1, 2, 3}, "the straddling facet is left")
        self.assertEqual(library_split.picked({"box": [[0, 0, 0], [3, 1, 1]]}, soup, groups, "x"), {0, 1, 2, 3, 8}, "the box is closed")
        self.assertEqual(library_split.picked({"box": [[40, 0, 0], [41, 1, 1]]}, soup, groups, "x"), set())
        for bad in ([[0, 0, 0]], [[1, 0, 0], [0, 1, 1]], [[0, 0, "0"], [1, 1, 1]], "box"):
            with self.subTest(box=bad), self.assertRaisesRegex(library_split.SplitError, "is not a box"):
                library_split.picked({"box": bad}, soup, groups, "x")

    def test_a_component_is_recognised_by_its_box_and_count(self) -> None:
        soup = tetra(0) + tetra(10) + tetra(20, 2)
        groups = library_split.components(soup)
        take = lambda rule: library_split.picked(rule, soup, groups, "x")  # noqa: E731
        self.assertEqual(take({"component": {"box": [[10, 0, 0], [11, 1, 1]]}}), {4, 5, 6, 7})
        self.assertEqual(take({"component": {"box": [[10.04, 0, -0.04], [11, 1, 1]], "triangles": 4}}), {4, 5, 6, 7}, "within 0.05 mm")
        self.assertEqual(take({"component": {"box": [[10.3, 0, 0], [11, 1, 1]], "tol_mm": 0.5}}), {4, 5, 6, 7})
        self.assertEqual(take({"components_inside": [[-1, -1, -1], [12, 2, 2]]}), set(range(8)))
        for rule, problem in (({"component": {"box": [[10.2, 0, 0], [11, 1, 1]]}}, "0 connected components have the box"),
                              ({"component": {"box": [[10, 0, 0], [11, 1, 1]], "triangles": 5}}, "0 connected components have the box .* and 5 triangles"),
                              ({"component": {"box": [[5, 0, 0], [6, 1, 1]], "tol_mm": 5}}, "2 connected components have the box"),
                              ({"component": {"triangles": 4}}, "a component rule is"),
                              ({"components_inside": [[30, 0, 0], [31, 1, 1]]}, "no connected component lies in the box"),
                              ({"plane": [1, 0, 0, 5]}, "'plane' is not a rule"),
                              ({"box": [[0, 0, 0], [1, 1, 1]], "component": {}}, "is not one rule")):
            with self.subTest(rule=rule), self.assertRaisesRegex(library_split.SplitError, problem):
                take(rule)

    def test_the_drawn_shapes_are_closed_and_face_outward(self) -> None:
        box = library_split.stl("x", library_split.drawn({"box": [[1, 2, 3], [3, 5, 7]]}, "x"))
        self.assertEqual(library_write.stl_triangles(box), 12)
        self.assertAlmostEqual(volume(box), 2 * 3 * 4, places=5)
        self.assertEqual(library_split.bounds(library_split.facets(box)), ([1, 2, 3], [3, 5, 7]))
        for axis, segments in (([0, 0, 3], 24), ([2, 0, 0], 8), ([1, 2, 2], 48)):
            with self.subTest(axis=axis):
                records = library_split.drawn({"cylinder": {"from": [1, 1, 1], "to": [1 + axis[0], 1 + axis[1], 1 + axis[2]], "radius": 2, "segments": segments}}, "x")
                self.assertEqual(len(records), 4 * segments)
                length = math.sqrt(math.fsum(v * v for v in axis))
                inscribed = segments / 2 * math.sin(2 * math.pi / segments) * 4 * length
                self.assertAlmostEqual(volume(library_split.stl("x", records)), inscribed, places=2)
                # Closed: every edge is used once each way.
                edges = {}
                for record in records:
                    a, b, c = library_split.corners(record)
                    for start, end in ((a, b), (b, c), (c, a)):
                        edges[(start, end)] = edges.get((start, end), 0) + 1
                self.assertTrue(all(count == 1 and edges.get((end, start)) == 1 for (start, end), count in edges.items()))
        self.assertEqual(len(library_split.drawn({"cylinder": {"from": [0, 0, 0], "to": [0, 0, 1], "radius": 1}}, "x")), 4 * library_split.SEGMENTS)
        for shape, problem in (({"box": [[0, 0, 0], [1, 1, 0]]}, "is flat"), ({"cylinder": {"from": [0, 0, 0], "to": [0, 0, 0], "radius": 1}}, "has no length"),
                               ({"cylinder": {"from": [0, 0, 0], "to": [0, 0, 1], "radius": 0}}, "a positive radius"),
                               ({"cylinder": {"from": [0, 0, 0], "to": [0, 0, 1], "radius": 1, "segments": 2}}, "3 to 96 segments"),
                               ({"sphere": {"radius": 1}}, "'sphere' is not a shape")):
            with self.subTest(shape=shape), self.assertRaisesRegex(library_split.SplitError, problem):
                library_split.drawn(shape, "x")
        # The project's own by its header (library_write reads it), and only under a drawn- name.
        data = library_split.stl(library_split.own_header("cap"), library_split.drawn({"box": [[0, 0, 0], [1, 1, 1]]}, "x"))
        self.assertTrue(library_write.own_body("bodies/grip/drawn-cap.stl", data))
        self.assertFalse(library_write.own_body("bodies/grip/cap.stl", data))
        with self.assertRaisesRegex(library_split.SplitError, "an STL's holds 80"):
            library_split.stl(library_split.own_header("a-name-too-long-for-the-header"), [])

    def test_a_prism_is_its_convex_profile_drawn_along_its_axis(self) -> None:
        # Since the MakerMods body of 2026-11-14: a chamfered block or a rail's rounded section in one shape, its corners
        # (y, z) about x, (z, x) about y and (x, y) about z, counter-clockwise seen from the axis's positive end.
        octagon = [[2, 0], [4, 0], [5, 1], [5, 3], [4, 4], [2, 4], [1, 3], [1, 1]]  # p 1..5, q 0..4
        area = 4 * 4 - 4 * 0.5
        for axis, low, high in (("x", [2, 1, 0], [7, 5, 4]), ("y", [0, 2, 1], [4, 7, 5]), ("z", [1, 0, 2], [5, 4, 7])):
            with self.subTest(axis=axis):
                records = library_split.drawn({"prism": {"axis": axis, "from": 2, "to": 7, "profile": octagon}}, "x")
                self.assertEqual(len(records), 2 * (8 - 2) + 2 * 8)
                self.assertAlmostEqual(volume(library_split.stl("x", records)), area * 5, places=4)
                self.assertEqual(library_split.bounds(records), (low, high))
                edges = {}
                for record in records:
                    a, b, c = library_split.corners(record)
                    for start, end in ((a, b), (b, c), (c, a)):
                        edges[(start, end)] = edges.get((start, end), 0) + 1
                self.assertTrue(all(count == 1 and edges.get((end, start)) == 1 for (start, end), count in edges.items()))
        triangle = library_split.drawn({"prism": {"axis": "z", "from": -1, "to": 0.5, "profile": [[0, 0], [2, 0], [0, 3]]}}, "x")
        self.assertEqual(len(triangle), 8)
        self.assertAlmostEqual(volume(library_split.stl("x", triangle)), 3 * 1.5, places=5)
        star = [[round(math.cos(4 * math.pi * k / 5), 6), round(math.sin(4 * math.pi * k / 5), 6)] for k in range(5)]
        for value, problem in (({"axis": "x", "from": 0, "to": 1, "profile": octagon[::-1]}, "does not turn left at its corner 1 "),
                               ({"axis": "x", "from": 0, "to": 1, "profile": [[0, 0], [1, 0], [2, 0], [0, 2]]}, "does not turn left at its corner 2 "),
                               ({"axis": "x", "from": 0, "to": 1, "profile": [[0, 0], [2, 0], [2, 0], [0, 2]]}, "does not turn left at its corner"),
                               ({"axis": "x", "from": 0, "to": 1, "profile": star}, "goes round more than once"),
                               ({"axis": "x", "from": 0, "to": 1, "profile": [[0, 0], [1, 0]]}, "is not 3 to 32 corners"),
                               ({"axis": "x", "from": 0, "to": 1, "profile": [[math.cos(k / 5.3), math.sin(k / 5.3)] for k in range(33)]},
                                "is not 3 to 32 corners"),
                               ({"axis": "x", "from": 0, "to": 1, "profile": [[0, 0], [1, 0], ["1", 1]]}, "is not 3 to 32 corners"),
                               ({"axis": "x", "from": 1, "to": 1, "profile": octagon}, "a from below its to"),
                               ({"axis": "w", "from": 0, "to": 1, "profile": octagon}, "an axis x, y or z"),
                               ({"axis": "x", "from": 0, "to": 1}, "a prism is"),
                               ({"axis": "x", "from": 0, "to": 1, "profile": octagon, "segments": 8}, "a prism is")):
            with self.subTest(value=value), self.assertRaisesRegex(library_split.SplitError, problem):
                library_split.drawn({"prism": value}, "x")
        # 32 corners, the most, are taken.
        circle = [[math.cos(2 * math.pi * k / 32), math.sin(2 * math.pi * k / 32)] for k in range(32)]
        self.assertEqual(len(library_split.drawn({"prism": {"axis": "y", "from": 0, "to": 1, "profile": circle}}, "x")), 2 * 30 + 2 * 32)

    def test_a_component_s_header_says_split(self) -> None:
        self.assertEqual(library_split.split_header(HEADER.encode("ascii").ljust(80, b" ")),
                         "modified (decimated, m to mm; split) by FlexiTac-Gen 2026, see NOTICE.md", "82 bytes with the bound: without it")
        self.assertEqual(library_split.split_header(b"modified (decimated <= 0.5 mm) by FlexiTac-Gen 2026, see NOTICE.md"),
                         "modified (decimated <= 0.5 mm; split) by FlexiTac-Gen 2026, see NOTICE.md")
        self.assertEqual(library_split.split_header(b"modified (m to mm) by FlexiTac-Gen 2026, see NOTICE.md".ljust(80, b" ")),
                         "modified (m to mm; split) by FlexiTac-Gen 2026, see NOTICE.md")
        again = library_split.split_header(HEADER.encode("ascii"))
        self.assertEqual(library_split.split_header(again.encode("ascii")), again, "a component's own header is kept")
        self.assertLessEqual(len(again), 80)
        for other in (b"solid something", b"modified (" + b"x" * 40 + b") by FlexiTac-Gen 2026, see NOTICE.md"):
            self.assertEqual(library_split.split_header(other), library_split.SPLIT_HEADER)
        # Its own fallback is a component's header too (the reviews of 2026-11-12: it had become "split by look; split"
        # when the tool read the components back, so --check failed on what the tool had just written).
        self.assertEqual(library_split.split_header(library_split.SPLIT_HEADER.encode("ascii").ljust(80, b" ")), library_split.SPLIT_HEADER)
        for header in (HEADER.encode("ascii"), b"solid something", b"modified (m to mm) by FlexiTac-Gen 2026, see NOTICE.md", b""):
            once = library_split.split_header(header)
            self.assertEqual(library_split.split_header(once.encode("ascii")), once, header)
        # The committed bodies' headers all take it.
        for path in sorted((LIBRARY / "bodies").rglob("*.stl")):
            header = path.read_bytes()[:80]
            if not header.startswith(b"FlexiTac-Gen: "):
                with self.subTest(body=path.name):
                    self.assertIn("split", library_split.split_header(header))
                    self.assertLessEqual(len(library_split.split_header(header)), 80)


class WriteTests(SplitCase):
    """One part written from its look file."""

    def test_the_bodies_are_shared_out_and_the_scene_follows(self) -> None:
        fixture = self.fixture
        before = fixture.scene_now()
        code, out, err = fixture.run()
        self.assertEqual((code, err), (0, ""), out)
        files = fixture.files()
        self.assertEqual(sorted(path for path in files if path.startswith("bodies/")),
                         ["bodies/grip/body-can.stl", "bodies/grip/body-hub.stl", "bodies/grip/body-rail.stl", "bodies/grip/drawn-cap.stl", "bodies/grip/plate.stl"])
        self.assertNotIn(Fixture.BODY, files, "the unsplit body leaves the library")
        self.assertEqual(files[Fixture.PLATE], fixture.plate, "a body kept whole keeps its file")
        # Each component: the body's records, sorted, under its header with "; split"; together all of them, once.
        taken = {name: library_split.facets(files[f"bodies/grip/{name}.stl"]) for name in ("body-rail", "body-hub", "body-can")}
        self.assertEqual(taken["body-rail"], sorted(tetra(10)))
        self.assertEqual(taken["body-hub"], sorted(tetra(20)))
        self.assertEqual(taken["body-can"], sorted(tetra(0)))
        self.assertEqual(sorted(record for records in taken.values() for record in records), sorted(fixture.records))
        for name in taken:
            self.assertEqual(files[f"bodies/grip/{name}.stl"][:80].rstrip(), b"modified (decimated, m to mm; split) by FlexiTac-Gen 2026, see NOTICE.md")
        self.assertEqual(files["bodies/grip/drawn-cap.stl"][:80].rstrip(), b"FlexiTac-Gen: cap, drawn by the project, not a vendor's part, mm")
        # The scene: each copy of the body by its components in the look file's order (the same matrix and finger), the
        # looks used with their numbers, part_look, smooth_deg, the look file's words after its about; every other key
        # and its order as it was.
        scene = fixture.scene_now()
        self.assertEqual(list(scene), ["format", "part", "part_mesh_sha256", "about", "frame", "approach", "opening", "mate", "bodies", "looks", "part_look",
                                       "smooth_deg", "see_through", "picture"])
        for key in before:
            if key not in ("bodies", "about"):
                self.assertEqual(scene[key], before[key], key)
        self.assertEqual(scene["about"], "A tiny gripper.  The looks: drawn after two photos; the cap is the project's own drawing.")
        names = ["body-rail", "body-hub", "drawn-cap", "body-can"]
        self.assertEqual([(body["mesh"], body["finger"], body.get("look")) for body in scene["bodies"]],
                         [(Fixture.PLATE, None, None)]
                         + [(f"bodies/grip/{name}.stl", finger, look) for finger in ("sensor", "mate")
                            for name, look in zip(names, ("rail-steel", "steel-ground", "steel-ground", "anodized-black"))])
        for body in scene["bodies"]:
            data = files[body["mesh"]]
            self.assertEqual((body["sha256"], body["bytes"], body["triangles"]), (hashlib.sha256(data).hexdigest(), len(data), library_write.stl_triangles(data)))
            self.assertEqual(body["matrix"], TURNED if body["finger"] == "mate" else IDENTITY)
        self.assertNotIn("look", scene["bodies"][0], "a body with no look is drawn in the part's grey")
        self.assertEqual(scene["looks"], {"anodized-black": {"color": "#1c1d20", "metalness": 0.6, "roughness": 0.45, "env_intensity": 1.5},
                                          "rail-steel": {"color": "#b4b7ba", "metalness": 1, "roughness": 0.25},
                                          "rubber-black": {"color": "#232325", "metalness": 0, "roughness": 0.92},
                                          "steel-ground": {"color": "#b4b7ba", "metalness": 1, "roughness": 0.35}})
        self.assertEqual((scene["part_look"], scene["smooth_deg"]), ("rubber-black", 35))
        used = {body["mesh"]: body["look"] for body in scene["bodies"] if "look" in body}
        used["part_look"] = scene["part_look"]
        self.assertEqual(library_write.looks_problems(scene["looks"], used, {scene["part_look"]}), [])
        # NOTICE.md: the split body's row by one row per picked component (its source, licence and change, the split's
        # note, the component's SHA-256); the drawn shape has none; everything else as it was.
        notice = files["NOTICE.md"].decode("utf-8")
        rows = {row[0]: row for row in library_write.NOTICE_ROW.findall(notice)}
        self.assertEqual(sorted(rows), ["bodies/grip/body-can.stl", "bodies/grip/body-hub.stl", "bodies/grip/body-rail.stl", "bodies/grip/plate.stl"])
        for name in ("body-rail", "body-hub", "body-can"):
            row = rows[f"bodies/grip/{name}.stl"]
            self.assertEqual(row[1:4], (" tiny `0123456`, body.stl ", " MIT, Tiny, `licenses/tiny.txt` ",
                                        " modified: decimated (quadric error metrics, 0.40 mm); split by look, its triangles unchanged (one of the 3 files of body.stl's) "))
            self.assertEqual(row[4], hashlib.sha256(files[f"bodies/grip/{name}.stl"]).hexdigest())
        self.assertTrue(notice.startswith("# Tiny\n\n| File |") and notice.endswith("\n\nAfter the table.\n"))
        self.assertLess(notice.index("plate.stl"), notice.index("body-rail.stl"))

    def test_the_same_input_gives_the_same_bytes(self) -> None:
        # Written again: nothing changes.  From the components alone (the unsplit body gone), with the facets pinned:
        # the same files.  From the unsplit body given aside (--source): the same files.  A changed rule is applied to
        # the components at hand and names them again.
        fixture = self.fixture
        self.assertEqual(fixture.run()[0], 0)
        first = fixture.files()
        code, out, _ = fixture.run()
        self.assertEqual((code, fixture.files()), (0, first))
        self.assertNotIn("wrote", out)
        self.assertEqual(fixture.run("--check")[0], 0)
        with tempfile.TemporaryDirectory() as aside:
            (Path(aside) / "bodies" / "grip").mkdir(parents=True)
            (Path(aside) / Fixture.BODY).write_bytes(fixture.body)
            for path in ("bodies/grip/body-rail.stl", "bodies/grip/body-hub.stl", "bodies/grip/body-can.stl"):
                (fixture.library / path).unlink()
            self.assertEqual(fixture.run()[0], 2, "neither the unsplit body nor its components")
            self.assertEqual(fixture.run("--source", aside)[0], 0)
            self.assertEqual(fixture.files(), first)
        # The facets' order in the unsplit body does not enter.
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        other = Fixture(Path(folder.name))
        other.records = list(reversed(other.records))
        other.body = stl(other.records)
        (other.library / Fixture.BODY).write_bytes(other.body)
        other.recipe["bodies"][Fixture.BODY]["sha256"] = hashlib.sha256(other.body).hexdigest()
        scene = other.scene_now()
        for body in scene["bodies"][1:]:
            body["sha256"] = hashlib.sha256(other.body).hexdigest()
        (other.library / "scenes" / "grip.json").write_text(library_split.scene_text(scene), encoding="utf-8")
        other.write()
        self.assertEqual(other.run()[0], 0)
        self.assertEqual({path: data for path, data in other.files().items() if path.startswith("bodies/")},
                         {path: data for path, data in first.items() if path.startswith("bodies/")})
        # Other names and another rule, from the components at hand.
        components = fixture.recipe["bodies"][Fixture.BODY]["components"]
        components[0] = {"name": "rail", "look": "rail-steel", "pick": [{"components_inside": [[9, -1, -1], [22, 2, 2]]}]}
        del components[1]
        fixture.write()
        code, out, err = fixture.run()
        self.assertEqual((code, err), (0, ""))
        files = fixture.files()
        self.assertEqual(sorted(path for path in files if path.startswith("bodies/")),
                         ["bodies/grip/body-can.stl", "bodies/grip/drawn-cap.stl", "bodies/grip/plate.stl", "bodies/grip/rail.stl"])
        self.assertEqual(library_split.facets(files["bodies/grip/rail.stl"]), sorted(tetra(10) + tetra(20)))
        self.assertEqual(files["bodies/grip/body-can.stl"], first["bodies/grip/body-can.stl"])
        self.assertEqual([body["mesh"] for body in fixture.scene_now()["bodies"]],
                         [Fixture.PLATE] + ["bodies/grip/rail.stl", "bodies/grip/drawn-cap.stl", "bodies/grip/body-can.stl"] * 2)
        self.assertEqual(len(re.findall(r"one of the 2 files of body\.stl's", files["NOTICE.md"].decode("utf-8"))), 2)
        self.assertEqual(fixture.run("--check")[0], 0)

    def test_a_body_of_another_header_splits_once(self) -> None:
        # A body whose header is not the bodies' convention (the rail the project drew has one): its components take
        # the tool's own header, and the files then are what the look file gives, from the components alone too.
        fixture = self.fixture
        fixture.body = stl(fixture.records, header="exported by some other tool")
        (fixture.library / Fixture.BODY).write_bytes(fixture.body)
        fixture.recipe["bodies"][Fixture.BODY]["sha256"] = hashlib.sha256(fixture.body).hexdigest()
        fixture.write()
        self.assertEqual(fixture.run()[0], 0)
        first = fixture.files()
        self.assertNotIn(Fixture.BODY, first, "the unsplit body left")
        for path in ("bodies/grip/body-rail.stl", "bodies/grip/body-hub.stl", "bodies/grip/body-can.stl"):
            self.assertEqual(first[path][:80].rstrip(b" "), library_split.SPLIT_HEADER.encode("ascii"), path)
        self.assertEqual(fixture.run("--check"), (0, "library_split: 1 look files, the bodies, scenes and NOTICE rows are what they give\n", ""))
        code, out, _ = fixture.run()
        self.assertEqual((code, fixture.files()), (0, first))
        self.assertNotIn("wrote", out)

    def test_an_unsplit_body_of_other_bytes_is_refused(self) -> None:
        # The scene builder made the body anew (other bytes): with the split's components still there the tool had
        # split those again and removed the new file as a stray.  It refuses instead: the look file is pinned anew.
        fixture = self.fixture
        self.assertEqual(fixture.run()[0], 0)
        good = fixture.files()
        fresh = stl(tetra(20) + tetra(0) + tetra(10.5))
        (fixture.library / Fixture.BODY).write_bytes(fresh)
        for arguments in ((), ("--check",)):
            code, out, err = fixture.run(*arguments)
            self.assertEqual(code, 2, arguments)
            self.assertIn("bodies/grip/body.stl is not the file its sha256 pins", err)
            self.assertIn("--pin", err)
            self.assertEqual(fixture.files(), dict(good, **{Fixture.BODY: fresh}), "nothing written, the new body not removed")
        (fixture.library / Fixture.BODY).unlink()
        with tempfile.TemporaryDirectory() as aside:
            (Path(aside) / "bodies" / "grip").mkdir(parents=True)
            (Path(aside) / Fixture.BODY).write_bytes(fresh)
            code, _, err = fixture.run("--source", aside)
            self.assertEqual((code, "is not the file its sha256 pins" in err), (2, True))
            (Path(aside) / Fixture.BODY).write_bytes(fixture.body)
            self.assertEqual(fixture.run("--source", aside, "--check")[0], 0)
        self.assertEqual(fixture.files(), good)

    def test_a_look_without_a_look_file_is_caught(self) -> None:
        # A drawn body's header only labels it: its look file's numbers draw it again.  So a scene with a drawn body, a
        # look or a crease angle, a drawn file or a split's rows, of a part without a look file, fail --check (the
        # reviews of 2026-11-12: a vendor's mesh under a drawn body's name and header had passed every check).
        fixture = self.fixture
        self.assertEqual(fixture.run("--check")[0], 1, "nothing written yet")
        (fixture.looks / "grip.json").rename(fixture.looks.parent / "grip.json")
        self.assertEqual(fixture.run("--check"), (0, "library_split: 0 look files, the bodies, scenes and NOTICE rows are what they give\n", ""), "an unsplit part")
        (fixture.looks.parent / "grip.json").rename(fixture.looks / "grip.json")
        self.assertEqual(fixture.run()[0], 0)
        (fixture.looks / "grip.json").rename(fixture.looks.parent / "grip.json")
        code, out, _ = fixture.run("--check")
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "scenes/grip.json has looks, part_look, smooth_deg, a body's look, bodies/grip/drawn-cap.stl, but grip has no look file "
            "(looks/grip.json): looks and drawn bodies are written from one",
            "bodies/grip/drawn-cap.stl: a body the project drew, but grip has no look file to draw it from",
            "NOTICE.md has rows of bodies/grip/body.stl's split, but grip has no look file",
            "library_split: 0 look files, 0 with files that differ, 3 looks or drawn bodies without a look file"])
        self.assertEqual(library_split.unowned(fixture.library, {"grip"}), [])
        # One loose thing is enough: a vendor's mesh named and labelled as a drawing, in a scene with no look.
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        other = Fixture(Path(folder.name))
        (other.looks / "grip.json").unlink()
        data = stl(tetra(70), header=library_split.own_header("thing"))
        (other.library / "bodies/grip/drawn-thing.stl").write_bytes(data)
        scene = other.scene_now()
        scene["bodies"].append({"mesh": "bodies/grip/drawn-thing.stl", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "triangles": 4,
                                "matrix": IDENTITY, "finger": None})
        (other.library / "scenes" / "grip.json").write_text(library_split.scene_text(scene), encoding="utf-8")
        self.assertTrue(library_write.own_body("bodies/grip/drawn-thing.stl", data), "the writer takes its header's word")
        code, out, _ = other.run("--check")
        self.assertEqual((code, len(out.splitlines())), (1, 3), out)
        self.assertIn("scenes/grip.json has bodies/grip/drawn-thing.stl, but grip has no look file", out)
        # The showcase's scene has its looks from tools/library_showcase.py (that tool's --check holds them to its own
        # table of the base looks): its looks are not loose, a body the project drew in it is.
        showcase = other.library / library_write.SHOWCASE_SCENE
        scene["bodies"].pop()
        scene.update(looks={"gold": {"color": "#c9a45c", "metalness": 1, "roughness": 0.35}}, part_look="gold", smooth_deg=35)
        showcase.write_text(library_split.scene_text(scene), encoding="utf-8")
        (other.library / "scenes" / "grip.json").unlink()
        (other.library / "bodies/grip/drawn-thing.stl").unlink()
        self.assertEqual(library_split.unowned(other.library, set()), [])
        showcase.rename(other.library / "scenes" / "other.json")
        self.assertEqual(len(library_split.unowned(other.library, set())), 1, "any other scene's looks are loose")
        (other.library / "scenes" / "other.json").rename(showcase)
        scene["bodies"].append({"mesh": "bodies/flexitac-g1/drawn-thing.stl"})
        showcase.write_text(library_split.scene_text(scene), encoding="utf-8")
        self.assertEqual(library_split.unowned(other.library, set(), other.looks),
                         ["scenes/flexitac-g1.json has bodies/flexitac-g1/drawn-thing.stl, but flexitac-g1 has no look file "
                          "(looks/flexitac-g1.json): looks and drawn bodies are written from one"])
        # The shapes tools/library_showcase.py draws for the showcase are that tool's, as its looks are: each pinned by
        # its SHA-256 in tools/library_write.py (SHOWCASE_BODIES; library_write.showcase() holds the files to the pins
        # and that tool's --check draws them again), so neither the scene's body nor the file is loose; a drawn file of
        # that folder that is not pinned still is.
        pinned = "bodies/flexitac-g1/drawn-shell-screw.stl"
        self.assertIn(pinned, library_write.SHOWCASE_BODIES)
        scene["bodies"][-1] = {"mesh": pinned}
        showcase.write_text(library_split.scene_text(scene), encoding="utf-8")
        (other.library / "bodies/flexitac-g1").mkdir(parents=True)
        (other.library / pinned).write_bytes(data)
        self.assertEqual(library_split.unowned(other.library, set(), other.looks), [])
        (other.library / "bodies/flexitac-g1/drawn-thing.stl").write_bytes(data)
        self.assertEqual(library_split.unowned(other.library, set(), other.looks),
                         ["bodies/flexitac-g1/drawn-thing.stl: a body the project drew, but flexitac-g1 has no look file to draw it from"])

    def test_check_catches_what_differs(self) -> None:
        fixture = self.fixture
        code, out, _ = fixture.run("--check")
        self.assertEqual(code, 1, "nothing written yet")
        self.assertIn("grip: bodies/grip/body-rail.stl is not what grip.json gives", out)
        self.assertIn("grip: scenes/grip.json is not what grip.json gives", out)
        self.assertIn("grip: NOTICE.md's rows of grip's bodies are not what grip.json gives", out)
        self.assertEqual(fixture.files()[Fixture.BODY], fixture.body, "--check writes nothing")
        self.assertEqual(fixture.run()[0], 0)
        self.assertEqual(fixture.run("--check"), (0, "library_split: 1 look files, the bodies, scenes and NOTICE rows are what they give\n", ""))
        good = fixture.files()

        def changed(path: str, edit) -> str:
            for relative, data in good.items():
                (fixture.library / relative).write_bytes(data)
            (fixture.library / path).write_bytes(edit(good[path]))
            code, out, _ = fixture.run("--check")
            (fixture.library / path).write_bytes(good[path])
            self.assertNotEqual(code, 0, path)
            return out

        flip = lambda data: data[:100] + bytes([data[100] ^ 1]) + data[101:]  # noqa: E731
        # A component's facet changed: its facets are no longer the pinned ones (the body's own triangles are the input).
        (fixture.library / "bodies/grip/body-rail.stl").write_bytes(flip(good["bodies/grip/body-rail.stl"]))
        code, out, err = fixture.run("--check")
        self.assertEqual(code, 2)
        self.assertIn("the facets of bodies/grip/body.stl are not the ones pinned", err)
        (fixture.library / "bodies/grip/body-rail.stl").write_bytes(good["bodies/grip/body-rail.stl"])
        self.assertIn("bodies/grip/body-rail.stl is not what grip.json gives", changed("bodies/grip/body-rail.stl", lambda data: b"another header".ljust(80, b" ") + data[80:]))
        self.assertIn("bodies/grip/drawn-cap.stl is not what grip.json gives", changed("bodies/grip/drawn-cap.stl", flip))
        self.assertIn("scenes/grip.json is not what grip.json gives", changed("scenes/grip.json", lambda data: data.replace(b'"smooth_deg": 35', b'"smooth_deg": 36')))
        self.assertIn("NOTICE.md's rows of grip's bodies are not what grip.json gives", changed("NOTICE.md", lambda data: data.replace(b"one of the 3 files", b"one of the 4 files")))
        (fixture.library / "bodies/grip/old.stl").write_bytes(stl(tetra(0)))
        code, out, _ = fixture.run("--check")
        self.assertEqual((code, "grip: bodies/grip/old.stl: a body grip.json does not give" in out), (1, True))
        self.assertEqual(fixture.run()[0], 0)
        self.assertFalse((fixture.library / "bodies/grip/old.stl").exists(), "a write removes the part's bodies its scene does not name")
        # A body kept whole that is not the pinned file.
        (fixture.library / Fixture.PLATE).write_bytes(stl(tetra(51)))
        code, _, err = fixture.run("--check")
        self.assertEqual((code, "bodies/grip/plate.stl is not the file its sha256 pins" in err), (2, True))

    def test_a_look_file_that_does_not_cover_its_part_is_refused(self) -> None:
        fixture = self.fixture
        body = fixture.recipe["bodies"][Fixture.BODY]
        good = json.loads(json.dumps(fixture.recipe))

        def refused(problem: str, edit) -> None:
            fixture.recipe = json.loads(json.dumps(good))
            edit(fixture.recipe)
            fixture.write()
            code, _, err = fixture.run()
            self.assertEqual(code, 2, problem)
            self.assertRegex(err, problem)
            self.assertEqual(fixture.files()[Fixture.BODY], fixture.body, "nothing written")

        components = lambda recipe: recipe["bodies"][Fixture.BODY]["components"]  # noqa: E731
        refused("4 triangles are taken by no component", lambda recipe: components(recipe).pop())
        refused("body-rail: takes no triangle", lambda recipe: components(recipe).insert(0, {"name": "all", "look": None, "pick": "rest"}))
        refused("the facets of bodies/grip/body.stl are not the ones pinned: \"facets_sha256\": \"" + body["facets_sha256"],
                lambda recipe: recipe["bodies"][Fixture.BODY].pop("facets_sha256"))
        refused("the scene's body bodies/grip/plate.stl is not in the look file", lambda recipe: recipe["bodies"].pop(Fixture.PLATE))
        refused("bodies/grip/other.stl has no sha256", lambda recipe: recipe["bodies"].update({"bodies/grip/other.stl": {"look": None}}))
        refused("'bodies/arx/body.stl' is not a body of bodies/grip/", lambda recipe: recipe["bodies"].update({"bodies/arx/body.stl": {"sha256": "0" * 64, "look": None}}))
        refused("body-rail names the look 'chrome', neither one of its looks nor a base look", lambda recipe: components(recipe)[0].update(look="chrome"))
        refused("its look 'rail-steel' has no evidence", lambda recipe: recipe["looks"]["rail-steel"].pop("evidence"))
        refused("its look 'steel-ground' takes a base look's name", lambda recipe: recipe["looks"].update({"steel-ground": recipe["looks"].pop("rail-steel")}))
        refused("its look 'rail-steel' is based on 'chrome', which is no base look", lambda recipe: recipe["looks"]["rail-steel"].update(base="chrome"))
        refused("its look 'rail-steel' has the roughness 2, not a number 0 to 1", lambda recipe: recipe["looks"]["rail-steel"].update(roughness=2))
        refused("is written twice", lambda recipe: components(recipe)[1].update(name="body-rail"))
        refused("a component of bodies/grip/body.stl is \\{name, look, pick or draw\\}", lambda recipe: components(recipe)[0].update(draw=[]))
        refused("the component 'Body Rail' of bodies/grip/body.stl is not named", lambda recipe: components(recipe)[0].update(name="Body Rail"))
        refused("grip.json is the look file of 'other'", lambda recipe: recipe.update(part="other"))
        refused("is not a flexitac-library-look/v1 document", lambda recipe: recipe.update(colours={}))
        fixture.recipe = good
        fixture.write()
        self.assertEqual(fixture.run("--only", "arx")[0], 2)
        self.assertEqual(fixture.run("--only", "grip")[0], 0)

    def test_a_dry_run_writes_elsewhere(self) -> None:
        fixture = self.fixture
        before = fixture.files()
        with tempfile.TemporaryDirectory() as out:
            code, said, _ = fixture.run("--out", out)
            self.assertEqual(code, 0)
            self.assertEqual(fixture.files(), before, "the library and its NOTICE.md as they were")
            written = sorted(path.relative_to(out).as_posix() for path in Path(out).rglob("*") if path.is_file())
            self.assertEqual(written, ["bodies/grip/body-can.stl", "bodies/grip/body-hub.stl", "bodies/grip/body-rail.stl", "bodies/grip/drawn-cap.stl",
                                       "bodies/grip/plate.stl", "scenes/grip.json"])
        # --pin and --components read a body.
        code, said, _ = fixture.run("--pin", Fixture.BODY)
        self.assertEqual(json.loads(said), {"sha256": hashlib.sha256(fixture.body).hexdigest(), "facets_sha256": library_split.facets_sha256(fixture.records), "triangles": 12})
        code, said, _ = fixture.run("--components", Fixture.BODY)
        self.assertEqual(said.splitlines()[1:], ["  c00: 4 triangles, box [20.00, 0.00, 0.00] to [21.00, 1.00, 1.00]",
                                                 "  c01: 4 triangles, box [0.00, 0.00, 0.00] to [1.00, 1.00, 1.00]",
                                                 "  c02: 4 triangles, box [10.00, 0.00, 0.00] to [11.00, 1.00, 1.00]"])


class CommittedTests(unittest.TestCase):
    """The committed look files and the base looks."""

    def test_the_committed_files_are_what_the_look_files_give(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = library_split.main(["--check"])
        self.assertEqual(code, 0, out.getvalue())
        found = library_split.recipes()
        parts = json.loads((LIBRARY / "parts.json").read_text(encoding="utf-8"))
        self.assertLessEqual(set(found), set(library_write.gripper_parts(parts)), "a look file per gripper part, named after it")
        # Every look, crease angle and drawn body of the library has its look file (--check's own read, here by name).
        self.assertEqual(library_split.unowned(LIBRARY, set(found)), [])
        # A body whose triangles stay in one file is that file's "one file", not "one of the 1 files" (the verification
        # of 2026-11-13: the Franka's finger); the registry reads both wordings.
        notice = (LIBRARY / "NOTICE.md").read_text(encoding="utf-8")
        self.assertNotIn("one of the 1 files", notice)
        self.assertIn("(the one file of finger_0.stl's)", notice)
        self.assertEqual(library_split.registry(notice)["bodies/franka-hand/finger_0.stl"], ["bodies/franka-hand/finger-body.stl"])
        for path in sorted((LIBRARY / "scenes").glob("*.json")):
            scene = json.loads(path.read_text(encoding="utf-8"))
            if path.relative_to(LIBRARY).as_posix() == library_write.SHOWCASE_SCENE:
                showcase = scene["looks"]  # tools/library_showcase.py's, from its own table of the base looks
            elif any(key in scene for key in ("looks", "part_look", "smooth_deg")):
                self.assertIn(path.stem, found, f"{path.name} has looks: its part needs a look file")
        # A part's own looks keep the convention for blacks (below): none darker than the base table's darkest.
        base = library_split.base_looks()
        floor = lightness("#1c1c1c")
        for name, look in showcase.items():
            with self.subTest(part="the showcase", look=name):
                self.assertGreaterEqual(lightness(look["color"]), floor)
        for part, (_, recipe) in found.items():
            for name, look in library_split.resolved_looks(recipe, base, f"{part}.json").items():
                with self.subTest(part=part, look=name):
                    self.assertGreaterEqual(lightness(look["color"]), floor)

    def test_the_tool_is_public_and_python_3_9(self) -> None:
        # The public copy's CI runs this module: the tool and the look files go with it, and both parse as Python 3.9.
        import ast

        import export_public

        covered = lambda relative: any(relative == path or relative.startswith(path + "/") for path in export_public.PUBLIC)  # noqa: E731
        for path in ("tools/library_split.py", "tools/library_looks/base.json", "tools/library_looks/any-part.json", "tools/library_write.py"):
            self.assertTrue(covered(path), path)
        for path in (ROOT / "tools" / "library_split.py", Path(__file__)):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 9))
        source = (ROOT / "tools" / "library_split.py").read_text(encoding="utf-8")
        imports = sorted(set(re.findall(r"(?m)^(?:import|from) ([\w.]+)", source)))
        self.assertEqual(imports, ["__future__", "argparse", "hashlib", "json", "library_write", "math", "pathlib", "re", "struct", "sys"], "standard library only")
        self.assertNotRegex(source, r"(?<![\w.])sum\(", "math.fsum over floats")
        self.assertIn("`library_split.py`", (ROOT / "tools" / "README.md").read_text(encoding="utf-8"))

    def test_the_base_looks_are_the_documented_table(self) -> None:
        # tools/library_looks/base.json is the data; docs/LIBRARY_VIEW.md's table shows the same names and numbers.
        base = library_split.base_looks()
        self.assertGreaterEqual(set(base), {"anodized-black", "anodized-natural", "steel-ground", "steel-polished", "plastic-black-satin", "plastic-black-matte",
                                            "plastic-white-gloss", "rubber-black", "print-black", "tpu-orange", "brass", "pcb-green"})
        document = (ROOT / "docs" / "LIBRARY_VIEW.md").read_text(encoding="utf-8")
        rows = re.findall(r"(?m)^\| `([a-z0-9-]+)` \| `(#[0-9a-f]{6})` \| ([\d.]+) \| ([\d.]+) \| ([^|]*) \| ([^|]*) \|", document)
        self.assertEqual([row[0] for row in rows], list(base), "the table's rows in the file's order")
        for name, color, metalness, roughness, coat, intensity in rows:
            look = {"color": color, "metalness": float(metalness), "roughness": float(roughness)}
            if coat.strip() != "-":
                look["clearcoat"], look["clearcoat_roughness"] = (float(value) for value in coat.split("/"))
            if intensity.strip() != "-":
                look["env_intensity"] = float(intensity)
            with self.subTest(look=name):
                self.assertEqual(look, base[name])
        # No black of the table is darker than the film (velostat, linear 0.014: sRGB about #1e1e1f), so a black body
        # stays apart from it; the part's own looks have no clear coat.
        for name, look in base.items():
            self.assertGreaterEqual(min(int(look["color"][index:index + 2], 16) for index in (1, 3, 5)), 0x1c, name)


if __name__ == "__main__":
    unittest.main()
