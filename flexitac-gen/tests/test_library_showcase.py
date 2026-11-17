"""tools/library_showcase.py: the builder of the Library's showcase (the project owner's decision of 2026-11-12).

The vendor's own file is no file of this repository, so nothing here reads it: the committed meshes are proved by
their pinned SHA-256 (tools/library_write.py; tests/test_library.py ShowcaseTests has the guards), and the split is
run on a tiny gripper of boxes made here, laid out where the tool's rules look for the real one's bodies.

- --check without the sources: the thirteen committed meshes and the seven shapes the project draws at their pins,
  the committed scene the one the tool writes from them, the guards silent; a mesh or a scene that differs is named.
- What the project draws (the shell's screws, the holders' bolts and nuts, the block in the top slot, the extender
  boards and cable stubs): plain boxes and cylinders under the header of a shape the project drew, drawn again on
  every run, each where the models have its hole; a shape of other bytes than its pin is not written without --repin.
- A rebuild refuses another file: a source of other bytes under the pinned name, or none, stops the tool before it
  reads a triangle; a build of other bytes than the pinned ones writes nothing without --repin.
- The split, on the tiny gripper: the shell (the largest component), the frame, the flange (below y -35), the pins
  (under 7 mm in x and y), the four links by their boxes' centres, each finger's coupler cut open at y 96 and its
  pins; the sliver under the shell's face, the pad (glued to its rubber: one piece through an edge three faces share,
  two as the centres want them) and the pad's screw left out; a file without a flange or a fingertip refused;
  cut_below() keeping the winding and writing float32 corners.
- The pose: the links' angle that leaves the two sensors' centres 55 mm apart (24.35 degrees); the four-bar closes
  (each link's tip stays on its finger's pin); the holder's three holes land on the finger's; the left holder and the
  left finger are the right ones' mirror images across the gripper's middle plane; the part is the left finger (the
  right one's place turned half a turn about the gripper's axis), its straps' side the shell's face without the logo;
  the approach is the fingers' direction; every matrix the scene holds is rigid.
- The notices' rows as --notice prints them are rows the guards accept.
- The tool is the standard library's (with tools/library_write.py and tools/mesh_decimate.py) and holds no host path.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
LIBRARY = WEB / "library"
sys.path.append(str(ROOT / "tools"))
import library_showcase  # noqa: E402
import library_write  # noqa: E402
import mesh_decimate  # noqa: E402

STDLIB = {"__future__", "argparse", "hashlib", "json", "math", "struct", "sys", "pathlib", "library_split", "library_write", "mesh_decimate"}


def box(low, high, cells: int = 1) -> list:
    """A closed box of ``cells`` squares a side on each face (12 triangles with one), the normals outward."""

    def face(origin, u, v):
        out = []
        for i in range(cells):
            for j in range(cells):
                p = lambda a, b: tuple(origin[k] + (a * u[k] + b * v[k]) / cells for k in range(3))  # noqa: E731
                out += [p(i, j) + p(i + 1, j) + p(i + 1, j + 1), p(i, j) + p(i + 1, j + 1) + p(i, j + 1)]
        return out

    x, y, z = (high[0] - low[0], 0.0, 0.0), (0.0, high[1] - low[1], 0.0), (0.0, 0.0, high[2] - low[2])
    return (face(low, y, x) + face((low[0], low[1], high[2]), x, y) + face(low, x, z) + face((low[0], high[1], low[2]), z, x)
            + face(low, z, y) + face((high[0], low[1], low[2]), y, z))


def centred(x: float, y: float, half_x: float, half_y: float, z=(-3.0, 3.0)) -> list:
    return box((x - half_x, y - half_y, z[0]), (x + half_x, y + half_y, z[1]))


def tiny_gripper(flange: bool = True, fingertips: bool = True) -> dict:
    """{what: triangles} of a gripper of boxes in the vendor file's layout (the tool's GROUPS and thresholds)."""

    parts = {
        "shell": box((-50.0, -35.0, -28.0), (50.0, 63.0, 27.0), cells=2),
        "frame": box((-45.0, -35.5, -13.0), (45.0, 56.0, 13.0)),
        "sliver": box((-18.0, 27.5, -26.5), (18.0, 42.0, -26.25)),
        "pins": centred(35.0, 19.0, 2.5, 2.5) + centred(-35.0, 19.0, 2.5, 2.5),
        "link_r_outer": centred(36.9, 39.1, 4.0, 30.0),
        "link_r_inner": centred(18.5, 61.55, 3.0, 25.0),
        "link_l_outer": centred(-36.9, 39.1, 4.0, 30.0),
        "link_l_inner": centred(-18.5, 61.55, 3.0, 25.0),
    }
    if flange:
        parts["flange"] = box((-37.5, -41.5, -37.0), (37.5, -35.5, 37.0))
    for side, sign in (("r", 1.0), ("l", -1.0)):
        low, high = sorted((sign * 8.0, sign * 38.0))
        parts[f"finger_{side}_coupler"] = box((low, 68.0, -8.0), (high, 127.0, 8.0))          # its box's centre (23, 97.5)
        parts[f"finger_{side}_pins"] = centred(sign * 32.0, 74.0, 2.0, 2.0, z=(-12.0, 12.0))
        if fingertips:
            # The fingertip: the pad, a plate (its box's centre 10.5, 115) glued to its rubber (7, 115) along an edge (four
            # faces share it: two pieces of the closed file, one of the finger's), and one of its screws (13.8, 105).
            low, high = sorted((sign * 8.0, sign * 13.0))
            parts[f"finger_{side}_pad"] = box((low, 95.0, 0.0), (high, 135.0, 16.0))
            low, high = sorted((sign * 6.0, sign * 8.0))
            parts[f"finger_{side}_rubber"] = box((low, 95.0, -16.0), (high, 135.0, 0.0))
            parts[f"finger_{side}_screw"] = centred(sign * 13.8, 105.0, 3.8, 1.5)
    return parts


def soup(parts: dict) -> list:
    """The parts' triangles as one binary STL's (float32), interleaved so that no part is a run of the file."""

    held = [struct.unpack("<9f", struct.pack("<9f", *t)) for name in sorted(parts) for t in parts[name]]
    return held[::3] + held[1::3] + held[2::3]


def moved(matrix: list, point) -> list:
    return [math.fsum(matrix[row][axis] * point[axis] for axis in range(3)) + matrix[row][3] for row in range(3)]


class CheckTests(unittest.TestCase):
    def run_tool(self, **options) -> tuple:
        lines = []
        return library_showcase.run(out=lines.append, **options), lines

    def test_the_committed_showcase_checks_without_the_sources(self) -> None:
        status, lines = self.run_tool(check=True)
        self.assertEqual((status, lines), (0, ["library_showcase: 13 meshes and 7 drawn shapes at their pinned SHA-256, the scene and "
                                               "the notices current"]))
        # The pins are the writer's: the vendor's twelve, the holder and the seven drawn shapes, each a path under web/.
        pins = library_showcase.pins()
        self.assertEqual(len(pins), 20)
        self.assertEqual(sorted(pins), sorted([f"vendor/ufactory-g1/{name}.stl" for name, _, _ in library_showcase.MESHES]
                                              + ["library/bodies/flexitac-g1/umi-right-finger-holder.stl"]
                                              + [f"library/bodies/flexitac-g1/drawn-{name}.stl" for name in library_showcase.DRAWN]))
        for path, pinned in pins.items():
            with self.subTest(file=path):
                self.assertEqual(hashlib.sha256((WEB / path).read_bytes()).hexdigest(), pinned)
        self.assertEqual({f"{name}.stl" for name, _, _ in library_showcase.MESHES}, set(library_write.SHOWCASE_VENDOR_FILES))
        self.assertEqual(set(library_showcase.MESH_LOOKS), {name for name, _, _ in library_showcase.MESHES})
        # The scene: the tool's own, from the committed meshes, byte for byte.
        parts = json.loads((LIBRARY / "parts.json").read_text(encoding="utf-8"))
        text = library_showcase.scene_text(library_showcase.scene_document(library_showcase.committed(), parts))
        self.assertEqual((LIBRARY / library_write.SHOWCASE_SCENE).read_text(encoding="utf-8"), text)
        self.assertTrue(text.isascii() and text.endswith("}\n"))

    def test_the_looks_are_the_library_s_base_looks(self) -> None:
        # In a scene a base name always means the base's numbers (docs/LIBRARY_VIEW.md "The looks").  The showcase's
        # base looks: the numbers of the Library's table (tools/library_looks/base.json), held here and compared with
        # the table.  Its own looks: a base look under another name, the numbers that differ, the evidence.
        base = library_showcase.BASE_LOOKS
        self.assertEqual(base, {
            "pcb-green": {"color": "#1f6b3a", "metalness": 0, "roughness": 0.5},
            "plastic-white-gloss": {"color": "#e2e4e6", "metalness": 0, "roughness": 0.3, "clearcoat": 0.6, "clearcoat_roughness": 0.15},
            "plastic-white-satin": {"color": "#e6e8ea", "metalness": 0, "roughness": 0.45},
            "anodized-black": {"color": "#232428", "metalness": 0.6, "roughness": 0.45, "env_intensity": 2.4},
            "steel-polished": {"color": "#c8cacc", "metalness": 1, "roughness": 0.18},
            "tpu-orange": {"color": "#f2601c", "metalness": 0, "roughness": 0.6},
        })
        own = library_showcase.OWN_LOOKS
        # Its own looks: four of the gripper's own bodies, each judged at the home and turned round to the side the
        # owner's photo was taken from (the reviews of 2026-11-12, which found the base looks right at the home only:
        # the shell and the holders all but lost in the card's ground from the logo's side, the pins' flat ends white
        # discs, the screws a mid grey), the fingers' orange, the UMI rows' own (the merge of 2026-11-13), and two of what
        # the project draws behind the fingers.
        self.assertEqual({name: {key: value for key, value in look.items() if key != "evidence"} for name, look in own.items()},
                         {"shell-white-gloss": {"base": "plastic-white-gloss", "roughness": 0.1, "clearcoat": 1, "clearcoat_roughness": 0.02,
                                                "env_intensity": 0.7},
                          "print-white": {"base": "plastic-white-satin", "color": "#d8dadc"},
                          "steel-pin": {"base": "steel-polished", "color": "#a0a2a4", "roughness": 0.7, "env_intensity": 0.5},
                          "screw-black": {"base": "anodized-black", "metalness": 0, "roughness": 0.9, "env_intensity": 1.9},
                          "umi-tpu-orange": {"base": "tpu-orange", "color": "#e85a1c", "roughness": 0.85, "env_intensity": 0.3},
                          "pcb-yellow": {"base": "pcb-green", "color": "#a08616"},
                          "ffc-white": {"base": "plastic-white-satin", "color": "#dedcd8", "roughness": 0.5}})
        for name, look in own.items():
            with self.subTest(own=name):
                self.assertNotIn(name, base, "a base name means the base's numbers")
                self.assertIn("photo", look["evidence"])
                self.assertRegex(look["evidence"], r"#[0-9a-f]{6}", "the photo's colour")
        looks = library_showcase.LOOKS
        self.assertEqual(looks, {
            "shell-white-gloss": dict(base["plastic-white-gloss"], roughness=0.1, clearcoat=1, clearcoat_roughness=0.02, env_intensity=0.7),
            "print-white": dict(base["plastic-white-satin"], color="#d8dadc"),
            "anodized-black": base["anodized-black"],
            "steel-pin": dict(base["steel-polished"], color="#a0a2a4", roughness=0.7, env_intensity=0.5),
            "screw-black": dict(base["anodized-black"], metalness=0, roughness=0.9, env_intensity=1.9),
            "umi-tpu-orange": dict(base["tpu-orange"], color="#e85a1c", roughness=0.85, env_intensity=0.3),
            "pcb-yellow": dict(base["pcb-green"], color="#a08616"),
            "ffc-white": dict(base["plastic-white-satin"], color="#dedcd8", roughness=0.5),
        })
        # The shell keeps the base gloss white's colour (a glossy face is darker for less of the studio, not for a
        # greyer paint) and the screws the base black's; the gloss is a smoother skin under a full, sharper coat.
        for name in ("shell-white-gloss", "screw-black"):
            self.assertEqual(looks[name]["color"], base[own[name]["base"]]["color"], name)
        self.assertLess(looks["shell-white-gloss"]["roughness"], base["plastic-white-gloss"]["roughness"])
        self.assertLess(looks["shell-white-gloss"]["clearcoat_roughness"], base["plastic-white-gloss"]["clearcoat_roughness"])
        self.assertGreater(looks["shell-white-gloss"]["clearcoat"], base["plastic-white-gloss"]["clearcoat"])
        # No black of the showcase's is darker than the base table's (the Library's convention for blacks).
        self.assertGreaterEqual(min(int(looks[name]["color"][k:k + 2], 16) for name in looks for k in (1, 3, 5)), 0x16)
        self.assertEqual(list(looks), list(library_showcase.LOOK_ORDER))
        self.assertEqual(set(library_showcase.MESH_LOOKS.values()) | {library_showcase.HOLDER_LOOK, library_showcase.PART_LOOK}
                         | {look for _, look, _ in library_showcase.DRAWN.values()}, set(looks))
        for name in ("pcb-green", "plastic-white-gloss", "plastic-white-satin", "steel-polished", "tpu-orange"):
            self.assertNotIn(name, looks, "a base look nothing wears is not listed")
        self.assertNotIn("clearcoat", looks[library_showcase.PART_LOOK], "the part's own material takes no clear coat")
        self.assertEqual(library_write.looks_problems(looks, {name: name for name in looks}, {library_showcase.PART_LOOK}), [])
        scene = json.loads((LIBRARY / library_write.SHOWCASE_SCENE).read_text(encoding="utf-8"))
        self.assertEqual((scene["looks"], scene["part_look"], scene["smooth_deg"]), (looks, "umi-tpu-orange", 35))
        # The fingers wear the UMI rows' orange: the rules' look of that name, number for number.
        rules = json.loads((LIBRARY / library_write.SCENES_INDEX).read_text(encoding="utf-8"))["rules"]
        self.assertEqual(looks[library_showcase.PART_LOOK], rules["looks"][library_showcase.PART_LOOK])
        listed = json.loads((ROOT / "tools" / "library_looks" / "base.json").read_text(encoding="utf-8"))["looks"]
        for name, look in base.items():
            with self.subTest(look=name):
                self.assertEqual(look, {key: value for key, value in listed[name].items() if key != "for"})
        self.assertFalse(set(own) & set(listed))

    def test_a_committed_mesh_or_scene_that_differs_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            web = Path(folder) / "web"
            for relative in ("library/parts.json", "library/NOTICE.md", f"library/{library_write.SHOWCASE_SCENE}", "vendor/ufactory-g1/NOTICE.md",
                             *library_showcase.pins()):
                (web / relative).parent.mkdir(parents=True, exist_ok=True)
                (web / relative).write_bytes((WEB / relative).read_bytes())
            patched = [mock.patch.object(library_showcase, "WEB", web), mock.patch.object(library_showcase, "LIBRARY", web / "library")]
            with patched[0], patched[1]:
                scene = web / "library" / library_write.SHOWCASE_SCENE
                document = json.loads(scene.read_text(encoding="utf-8"))
                document["bodies"][3]["matrix"][0][3] += 1.0
                scene.write_text(library_showcase.scene_text(document), encoding="utf-8")
                status, lines = self.run_tool(check=True)
                self.assertEqual((status, lines[0]), (1, f"would change: web/library/{library_write.SHOWCASE_SCENE}"))
                self.assertEqual(scene.read_text(encoding="utf-8"), library_showcase.scene_text(document), "a check writes nothing")
                # Without --check the scene is written again from the committed meshes.
                status, lines = self.run_tool()
                self.assertEqual((status, lines), (0, [f"wrote: web/library/{library_write.SHOWCASE_SCENE}"]))
                self.assertEqual(scene.read_bytes(), (LIBRARY / library_write.SHOWCASE_SCENE).read_bytes())
                mesh = web / "vendor" / "ufactory-g1" / "body_pins.stl"
                mesh.write_bytes(b"M" + mesh.read_bytes()[1:])
                status, lines = self.run_tool(check=True)
                self.assertEqual((status, lines), (1, ["web/vendor/ufactory-g1/body_pins.stl is not the pinned file (SHA-256)",
                                                       "library_showcase: the committed meshes are not the pinned ones: rebuild with --sources DIR"]))
                mesh.unlink()
                status, lines = self.run_tool()
                self.assertEqual((status, lines[0]), (1, "web/vendor/ufactory-g1/body_pins.stl is missing"))

    def test_a_rebuild_refuses_another_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            sources = Path(folder)
            with self.assertRaisesRegex(library_showcase.ShowcaseError, "Gripper G1 3D File \\(With\\)\\.stl is not in the sources' folder"):
                library_showcase.build(sources, out=lambda line: None)
            other = mesh_decimate.stl_bytes(soup(tiny_gripper()), b"another gripper")
            (sources / library_showcase.SOURCE_NAME).write_bytes(other)
            with mock.patch.object(library_showcase, "split") as split, mock.patch.object(mesh_decimate, "read_stl") as read:
                with self.assertRaisesRegex(library_showcase.ShowcaseError, "is not the pinned file \\(SHA-256 6c59aabbd228\\.\\.\\.\\): another file is refused"):
                    library_showcase.build(sources, out=lambda line: None)
                self.assertFalse(split.called or read.called, "refused before a triangle is read")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(library_showcase.main(["--sources", folder]), 1)
            self.assertIn("library_showcase: Gripper G1 3D File (With).stl is not the pinned file", err.getvalue())
        self.assertEqual((library_showcase.SOURCE_NAME, library_showcase.SOURCE_SHA256, library_showcase.SOURCE_BYTES), library_write.SHOWCASE_SOURCE)
        self.assertEqual(library_showcase.HOLDER_SHA256, "80ebab13e5d84a4e83d80e4ff21fa660223fd98f0f83dc45055d7015b4e71c00")
        self.assertEqual(library_showcase.HANDUMI_COMMIT, "144827862d4e2d5cd2d331ce7eed1374d3c769df", "the Library's pinned handumi-hw commit")
        self.assertIn(library_showcase.HANDUMI_COMMIT, json.loads((LIBRARY / "parts.json").read_text(encoding="utf-8"))["parts"]["umi-finray"]["license"]["source"])

    def test_a_build_of_other_bytes_writes_nothing_without_repin(self) -> None:
        # A build stood in for (the real one needs the vendor's file): one mesh of other bytes than its pin.
        files = library_showcase.committed()
        changed = dict(files)
        path = "vendor/ufactory-g1/body_frame.stl"
        changed[path] = b"M" + files[path][1:]
        with tempfile.TemporaryDirectory() as folder:
            web = Path(folder) / "web"
            (web / "library").mkdir(parents=True)
            (web / "library" / "parts.json").write_bytes((LIBRARY / "parts.json").read_bytes())
            with mock.patch.object(library_showcase, "WEB", web), mock.patch.object(library_showcase, "LIBRARY", web / "library"), \
                    mock.patch.object(library_showcase, "build", return_value=(changed, {})):
                status, lines = self.run_tool(sources=folder)
                self.assertEqual(status, 1)
                self.assertEqual(lines[0], f"library_showcase: web/{path} is built as {hashlib.sha256(changed[path]).hexdigest()}, "
                                           f"not the pinned {library_write.SHOWCASE_VENDOR_FILES['body_frame.stl']}")
                self.assertIn("nothing written", lines[1])
                self.assertEqual([p for p in web.rglob("*") if p.is_file()], [web / "library" / "parts.json"])
                status, lines = self.run_tool(sources=folder, repin=True)
                self.assertEqual(status, 0)
                self.assertEqual((web / path).read_bytes(), changed[path])
                self.assertEqual(len([p for p in web.rglob("*.stl")]), 20)
            # The pinned build is written as it is, the scene with it.
            with mock.patch.object(library_showcase, "WEB", web), mock.patch.object(library_showcase, "LIBRARY", web / "library"), \
                    mock.patch.object(library_showcase, "build", return_value=(dict(files), {})):
                status, lines = self.run_tool(sources=folder)
                self.assertEqual((status, lines), (0, [f"wrote: web/library/{library_write.SHOWCASE_SCENE}, web/{path}"]))
                self.assertEqual((web / "library" / library_write.SHOWCASE_SCENE).read_bytes(), (LIBRARY / library_write.SHOWCASE_SCENE).read_bytes())


class DrawnTests(unittest.TestCase):
    """What the project draws for the showcase after the owner's photo of the gripper (DRAWN): plain shapes, the
    project's own, each where the models have its hole."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pose = library_showcase.pose()
        cls.matrices = library_showcase.matrices()
        cls.files = library_showcase.drawn_files()
        cls.placements = library_showcase.drawn_placements(cls.matrices)

    def test_each_shape_is_a_plain_shape_of_the_project_s_own(self) -> None:
        triangles = {"shell-screw": 64, "holder-bolt": 64, "holder-nut": 24, "slot-block": 12 + 96, "extender": 12, "extender-sockets": 24,
                     "cable-stub": 12}
        self.assertEqual(list(library_showcase.DRAWN), list(triangles))
        self.assertEqual(sorted(self.files), sorted(f"library/bodies/flexitac-g1/drawn-{name}.stl" for name in triangles))
        for name, count in triangles.items():
            path = library_showcase.drawn_path(name)
            data = self.files[f"library/{path}"]
            with self.subTest(shape=name):
                self.assertEqual(library_write.stl_triangles(data), count)
                self.assertTrue(library_write.own_body(path, data), "its header says the project drew it")
                self.assertLessEqual(len(name), 21, "its header fits an STL's 80 bytes")
                self.assertEqual(data, (LIBRARY / path).read_bytes(), "the committed file is the one drawn now")
                self.assertEqual(hashlib.sha256(data).hexdigest(), library_write.SHOWCASE_BODIES[path])
                what, look, shapes = library_showcase.DRAWN[name]
                self.assertTrue(what and look in library_showcase.LOOKS and shapes)
        # The same bytes on every run.
        self.assertEqual(library_showcase.drawn_files(), self.files)
        self.assertLess(sum(len(data) for data in self.files.values()), 20_000, "a few kilobytes of the bodies' budget")

    def test_the_screws_stand_in_the_shell_s_wells_and_the_bolts_in_the_holders_holes(self) -> None:
        placed = [name for name, _, _ in self.placements]
        self.assertEqual(placed, ["shell-screw"] * 12 + (["holder-bolt"] * 3 + ["holder-nut"] * 3) * 2 + ["slot-block"]
                         + ["extender", "extender-sockets", "cable-stub"] * 2)
        self.assertEqual([finger for _, _, finger in self.placements], [None] * 12 + ["sensor"] * 6 + ["mate"] * 6 + [None]
                         + ["sensor"] * 3 + ["mate"] * 3)
        part = self.pose["part"]
        # The twelve screws, in the vendor file's axes: six wells a face, mirrored across the middle plane; a head's
        # flat end on the well's floor (z 21.0) on the face without the logo, its outer end at z -24.3 on the logo's.
        at = [moved(library_showcase.product(part, matrix), (0.0, 0.0, 0.0)) for name, matrix, _ in self.placements if name == "shell-screw"]
        self.assertEqual(sorted((round(x, 6), round(y, 6), round(z, 6)) for x, y, z in at),
                         sorted([(sign * x, y, z) for (*holes, z) in library_showcase.SHELL_SCREWS for x, y in holes for sign in (1.0, -1.0)]))
        self.assertEqual({z for *_, z in library_showcase.SHELL_SCREWS}, {21.0, -24.3})
        for name, matrix, _ in self.placements:
            self.assertIsNone(library_write._rigid(library_showcase.rounded(matrix)), name)
        # Each holder's bolts through the soft finger's own three holes (its file's x and -z), heads on one flange and
        # nuts on the other, outside the finger's thickness (y -25.8 to 0).
        for name, side in (("holder-bolt", -1), ("holder-nut", 1)):
            ends = [moved(matrix, (0.0, 0.0, 0.0)) for kind, matrix, finger in self.placements if kind == name and finger == "sensor"]
            self.assertEqual(len(ends), 3)
            for end, (x, z) in zip(ends, library_showcase.FINGER_HOLES):
                with self.subTest(shape=name, hole=(x, z)):
                    self.assertLess(math.hypot(end[0] - x, end[2] + z), 0.01)
                    self.assertTrue(end[1] < -25.8 if side < 0 else end[1] > 0.0, end)
        # The mate's are the sensor finger's through the mate's matrix.
        mate = self.matrices["mate"]
        for kind in ("holder-bolt", "holder-nut", "extender", "extender-sockets", "cable-stub"):
            ours = [matrix for name, matrix, finger in self.placements if name == kind and finger == "sensor"]
            theirs = [matrix for name, matrix, finger in self.placements if name == kind and finger == "mate"]
            for one, other in zip(ours, theirs):
                self.assertLess(math.dist(moved(other, (1.0, 2.0, 3.0)), moved(mate, moved(one, (1.0, 2.0, 3.0)))), 1e-9)

    def test_the_board_stands_where_the_pad_s_tails_end(self) -> None:
        # Behind the finger (the reviews of 2026-11-12: neither tail ended in a socket of the board first drawn, and the
        # Top FPC's tab hung beside it).  The tails' ends are where the Library's view lays the placed pad (TAILS_PLANE,
        # TAIL_END, TAB_END: measured there, and held in the browser by showcase_checks.py part_tails); the board's
        # axes lie along their plane, so in those axes:
        board, cable = library_showcase.board_place(), library_showcase.cable_place()
        for matrix in (board, cable):
            self.assertIsNone(library_write._rigid(library_showcase.rounded(matrix)))
            self.assertAlmostEqual(library_write.determinant(matrix), 1.0, places=9)
        self.assertEqual(library_showcase.FINGER_PLACES, {"extender": "board", "extender-sockets": "board", "cable-stub": "cable"})
        self.assertEqual(set(library_showcase.FINGER_PLACES), set(library_showcase.FINGER_DRAWN))
        placed = {name: matrix for name, matrix, finger in self.placements if finger == "sensor" and name in library_showcase.FINGER_DRAWN}
        self.assertEqual(placed, {"extender": board, "extender-sockets": board, "cable-stub": cable})
        back = library_showcase.inverse(board)
        slope, at = library_showcase.TAILS_PLANE[1], library_showcase.TAILS_PLANE[0]
        self.assertAlmostEqual(math.degrees(math.atan(slope)), 21.7, places=1)

        def on_plane(y: float, z: float) -> tuple:
            return moved(back, (at + slope * z, y, z))

        (pcb,) = library_showcase.DRAWN["extender"][2]
        upper, lower = library_showcase.DRAWN["extender-sockets"][2]
        (stub,) = library_showcase.DRAWN["cable-stub"][2]

        def inside(point: tuple, shape: dict, margin: float = 0.0) -> bool:
            low, high = shape["box"]
            return all(low[k] + margin <= point[k] <= high[k] - margin for k in range(3))

        # - the wide tail's end, over its whole width, is inside the upper socket, 0.2 mm or more from its walls, and
        #   so is the whole of its stiffened end (4.4 mm of the finger's length before it); the tail enters the socket
        #   through its face toward the fingertip, above its floor;
        (y0, y1), z = library_showcase.TAIL_END
        for y in (y0, y1):
            for along in (z, z - 4.4):
                self.assertTrue(inside(on_plane(y, along), upper, 0.2), (y, along))
        self.assertLess(on_plane(y0, z - 6.0)[2], upper["box"][0][2], "the tail comes from outside the socket")
        self.assertLess(upper["box"][0][0], 0.0)
        self.assertGreater(upper["box"][1][0], 0.0)
        # - the socket is at the board's edge: it stands over the board's first millimetres and above its face;
        self.assertTrue(upper["box"][0][2] < pcb["box"][0][2] < upper["box"][1][2])
        self.assertGreater(upper["box"][1][0], pcb["box"][1][0])
        # - the Top FPC's tab's end, over its whole width, is inside the lower socket, 0.2 mm or more from its walls, and
        #   so are its last 3.5 mm along the finger; the tab enters the socket through its face toward the fingertip;
        #   the socket goes through the board (from under its underside, which is off the tails' plane, to above it)
        #   and stands within it, past the upper socket;
        (y0, y1), z = library_showcase.TAB_END
        for y in (y0, y1):
            for along in (z, z - 3.5):
                self.assertTrue(inside(on_plane(y, along), lower, 0.2), (y, along))
        self.assertLess(on_plane(y0, z - 6.0)[2], lower["box"][0][2], "the tab comes from outside the socket")
        self.assertTrue(lower["box"][0][0] < 0.0 < pcb["box"][0][0] < pcb["box"][1][0] < lower["box"][1][0])
        self.assertTrue(upper["box"][1][2] < lower["box"][0][2] < lower["box"][1][2] < pcb["box"][1][2])
        # - the board covers the strap that carries the tab across the back from the fold (the fold's side face at
        #   y -25.8, the strap 2.3 mm off it) and ends a little past the lower socket, so the cable leaves its edge;
        self.assertGreater(pcb["box"][0][0], 0.3)
        self.assertLess(pcb["box"][0][1], -25.8 - 2.3 - 0.5)
        self.assertLess(pcb["box"][1][2] - lower["box"][1][2], 1.0)
        # - the cable stub begins inside the lower socket and ends on the finger's flat back (x 40 of its file), above
        #   its base and within its thickness, between the holder's flanges: a stub that ends on the finger.
        start = moved(back, moved(cable, (0.0, 0.0, 0.0)))
        self.assertTrue(lower["box"][0][0] < start[0] < lower["box"][1][0] and lower["box"][0][2] < start[2] < lower["box"][1][2], start)
        low, high = stub["box"]
        end = moved(cable, (low[0], 0.0, high[2]))
        self.assertLess(math.hypot(end[0] - library_showcase.CABLE_TO[0], end[2] - library_showcase.CABLE_TO[2]), 0.05, end)
        self.assertTrue(40.0 < end[0] < 40.6 and -45.0 < end[2] < 0.0, end)
        self.assertTrue(-25.8 < low[1] < high[1] < 0.0)
        self.assertAlmostEqual(high[1] - low[1], 16.5, places=9, msg="the 32-way flat cable's width")
        # Every shape behind the finger stays within the reach of the photo's boards: off the finger's back by less
        # than 8 mm, across its thickness by no more than the strap's 2.3 mm and a millimetre.
        for kind in library_showcase.FINGER_DRAWN:
            for shape in library_showcase.DRAWN[kind][2]:
                low, high = shape["box"]
                corners = [moved(placed[kind], (x, y, z)) for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])]
                with self.subTest(shape=kind):
                    self.assertTrue(all(30.0 < x < 48.0 and -29.0 <= y <= 0.0 and -60.0 < z < 0.0 for x, y, z in corners), corners)

    def test_a_shape_of_other_bytes_is_not_written_without_repin(self) -> None:
        other = dict(library_showcase.DRAWN, **{"slot-block": ("a block", "anodized-black", [{"box": [[-1, 52, -1], [1, 57, 1]]}])})
        with tempfile.TemporaryDirectory() as folder:
            web = Path(folder) / "web"
            for relative in ("library/parts.json", *library_showcase.pins()):
                (web / relative).parent.mkdir(parents=True, exist_ok=True)
                (web / relative).write_bytes((WEB / relative).read_bytes())
            before = {path: path.read_bytes() for path in web.rglob("*") if path.is_file()}
            lines = []
            with mock.patch.object(library_showcase, "WEB", web), mock.patch.object(library_showcase, "LIBRARY", web / "library"), \
                    mock.patch.object(library_showcase, "DRAWN", other):
                status = library_showcase.run(out=lines.append)
                self.assertEqual(status, 1)
                self.assertRegex(lines[0], r"^library_showcase: web/library/bodies/flexitac-g1/drawn-slot-block\.stl is drawn as [0-9a-f]{64}, not the pinned 4c931930")
                self.assertIn("nothing written", lines[1])
                self.assertEqual({path: path.read_bytes() for path in web.rglob("*") if path.is_file()}, before)
                self.assertEqual(library_showcase.run(repin=True, out=lines.append), 0)
                self.assertNotEqual((web / "library" / library_showcase.drawn_path("slot-block")).read_bytes(),
                                    (LIBRARY / library_showcase.drawn_path("slot-block")).read_bytes())


class SplitTests(unittest.TestCase):
    def test_the_tiny_gripper_splits_into_the_twelve_meshes(self) -> None:
        parts = tiny_gripper()
        result = library_showcase.split(soup(parts))
        self.assertEqual(list(result), [name for name, _, _ in library_showcase.MESHES])
        as_set = lambda triangles: {struct.unpack("<9f", struct.pack("<9f", *t)) for t in triangles}  # noqa: E731
        for mesh, part in (("body_shell", "shell"), ("body_frame", "frame"), ("body_flange", "flange"), ("body_pins", "pins"),
                           ("link_r_outer", "link_r_outer"), ("link_r_inner", "link_r_inner"), ("link_l_outer", "link_l_outer"),
                           ("link_l_inner", "link_l_inner"), ("finger_r_pins", "finger_r_pins"), ("finger_l_pins", "finger_l_pins")):
            with self.subTest(mesh=mesh):
                self.assertEqual(as_set(result[mesh]), as_set(parts[part]))
                self.assertEqual(len(result[mesh]), len(parts[part]))
        self.assertEqual(len(result["body_shell"]), 48, "the largest component")
        # The couplers: the stock finger cut at y 96, open there; the fingertip (the pad and its screw) gone.
        for side in "rl":
            coupler = result[f"finger_{side}_coupler"]
            with self.subTest(coupler=side):
                heights = [t[k] for t in coupler for k in (1, 4, 7)]
                self.assertEqual((min(heights), max(heights)), (68.0, 96.0))
                self.assertEqual(len(coupler), 2 + 4 * 3, "the bottom whole, each side's two triangles cut into three, no top")
                edges = {}
                for t in coupler:
                    corners = (t[0:3], t[3:6], t[6:9])
                    for k in range(3):
                        key = tuple(sorted((corners[k], corners[(k + 1) % 3])))
                        edges[key] = edges.get(key, 0) + 1
                border = [edge for edge, count in edges.items() if count == 1]
                self.assertTrue(border and all(a[1] == 96.0 and b[1] == 96.0 for a, b in border), "the cut is left open")
        everything = {t for held in result.values() for t in held}
        for left_out in ("sliver", "finger_r_pad", "finger_r_rubber", "finger_r_screw", "finger_l_pad", "finger_l_rubber", "finger_l_screw"):
            self.assertFalse(as_set(parts[left_out]) & everything, left_out)
        # Each mesh's triangles in the file's order.
        order = {t: number for number, t in enumerate(soup(parts))}
        for mesh in ("body_shell", "link_l_inner", "finger_r_pins"):
            numbers = [order[t] for t in result[mesh]]
            self.assertEqual(numbers, sorted(numbers), mesh)

    def test_another_file_is_refused_by_what_it_lacks(self) -> None:
        with self.assertRaisesRegex(library_showcase.ShowcaseError, "the body's flange not found: another file\\?"):
            library_showcase.split(soup(tiny_gripper(flange=False)))
        with self.assertRaisesRegex(library_showcase.ShowcaseError, "finger_r: the fingertip \\(the pad and its screws\\) not found"):
            library_showcase.split(soup(tiny_gripper(fingertips=False)))
        parts = tiny_gripper()
        del parts["link_l_inner"]
        with self.assertRaisesRegex(library_showcase.ShowcaseError, "link_l_inner not found"):
            library_showcase.split(soup(parts))

    def test_two_solids_glued_on_an_edge_are_two_pieces_of_the_closed_file(self) -> None:
        # The stock pad is a plate glued to its rubber: the vendor's file joins them along edges that four faces share.
        # The first step takes them apart (only an edge of exactly two faces joins; each goes by its own box's centre),
        # the second, on a finger's own triangles, takes them as one piece (the fingertip that is dropped).
        plate = box((8.0, 95.0, 0.0), (13.0, 135.0, 16.0))
        rubber = box((6.0, 95.0, -16.0), (8.0, 135.0, 0.0))
        both = soup({"a": plate, "b": rubber})
        self.assertEqual(sorted(len(piece) for piece in library_showcase.pieces(both, None, pairs=True)), [12, 12])
        self.assertEqual([len(piece) for piece in library_showcase.pieces(both, mesh_decimate.WELD_SCALE)], [24])
        centres = sorted((library_showcase.box(library_showcase.taken(both, [piece]))) for piece in library_showcase.pieces(both, None, pairs=True))
        self.assertEqual([((low[0] + high[0]) / 2, (low[1] + high[1]) / 2) for low, high in centres], [(7.0, 115.0), (10.5, 115.0)])

    def test_a_cut_keeps_the_winding_and_writes_float32(self) -> None:
        triangle = (0.0, 95.0, 0.0, 3.0, 95.0, 0.0, 0.0, 98.0, 0.3)
        below = library_showcase.cut_below([triangle], 96.0)
        self.assertEqual(len(below), 2, "two corners below: a quadrilateral, fanned")
        was = mesh_decimate.unit_normal(triangle[0:3], triangle[3:6], triangle[6:9])
        for t in below:
            now = mesh_decimate.unit_normal(t[0:3], t[3:6], t[6:9])
            self.assertAlmostEqual(math.fsum(was[k] * now[k] for k in range(3)), 1.0, places=6)
            self.assertLessEqual(max(t[1], t[4], t[7]), 96.0)
            self.assertEqual(t, struct.unpack("<9f", struct.pack("<9f", *t)), "every corner a float32")
        self.assertIn((0.0, 96.0, library_showcase.float32(0.1)), {t[k:k + 3] for t in below for k in (0, 3, 6)})
        above = (0.0, 97.0, 0.0, 1.0, 97.0, 0.0, 0.0, 98.0, 0.0)
        whole = (0.0, 90.0, 0.0, 1.0, 90.0, 0.0, 0.0, 96.0, 0.0)
        self.assertEqual(library_showcase.cut_below([above, whole, triangle], 96.0), [whole] + below, "those wholly below first, as they are")
        self.assertEqual(len(library_showcase.cut_below([(0.0, 95.0, 0.0, 3.0, 99.0, 0.0, 0.0, 99.0, 1.0)], 96.0)), 1, "one corner below: a triangle")


class PoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pose = library_showcase.pose()
        cls.matrices = library_showcase.matrices()

    def test_the_sensors_centres_are_55_mm_apart(self) -> None:
        self.assertAlmostEqual(math.degrees(self.pose["angle"]), 24.3524, places=3)
        centre = library_showcase.SENSOR_CENTRE
        self.assertAlmostEqual(math.dist(centre, moved(self.matrices["mate"], centre)), 55.0, places=9)
        # In the vendor file's axes: each 27.5 mm from the middle plane, the fingers 22.90 mm out of their 39.70.
        self.assertAlmostEqual(moved(self.pose["finger"], centre)[0], 27.5, places=9)
        self.assertAlmostEqual(moved(self.pose["part"], centre)[0], -27.5, places=9)
        self.assertAlmostEqual(self.pose["shift"][0], 22.905, places=3)
        self.assertAlmostEqual(self.pose["shift"][1], -3.648, places=3)
        self.assertAlmostEqual(self.pose["limit"][0], 39.699, places=3)
        self.assertAlmostEqual(self.pose["limit"][1], -13.959, places=3)
        # The Tactile Demo's reference pose: 30 degrees is (27.851924, -5.855205) mm.
        reference = library_showcase.finger_shift(math.radians(30))
        self.assertAlmostEqual(reference[0], 27.851924, places=5)
        self.assertAlmostEqual(reference[1], -5.855205, places=5)
        self.assertEqual(library_showcase.finger_shift(0.0), (0.0, 0.0))

    def test_the_four_bar_closes(self) -> None:
        # Each link turns about its pivot on the body; its tip stays on its finger's pin, which only translates.
        for side, sign in (("r", 1.0), ("l", -1.0)):
            for name, pivot in (("outer", library_showcase.PIVOT_OUTER), ("inner", library_showcase.PIVOT_INNER)):
                tip = (sign * (pivot[0] + library_showcase.LINK[0]), pivot[1] + library_showcase.LINK[1], 0.0)
                on_link = moved(self.matrices[f"link_{side}_{name}"], tip)
                on_finger = moved(self.matrices[f"finger_{side}_coupler"], tip)
                with self.subTest(link=f"{side}_{name}"):
                    self.assertLess(math.dist(on_link, on_finger), 1e-9)
                    # And the pivot stays on the body.
                    at = (sign * pivot[0], pivot[1], 0.0)
                    self.assertLess(math.dist(moved(self.matrices[f"link_{side}_{name}"], at), moved(self.matrices["body_shell"], at)), 1e-9)

    def test_the_finger_is_bolted_to_the_holder_by_its_three_holes(self) -> None:
        self.assertLess(self.pose["residual"], 0.005)
        self.assertAlmostEqual(self.pose["lean"], 0.9256, places=3)
        for hole, (x, z) in zip(library_showcase.HOLDER_HOLES, library_showcase.FINGER_HOLES):
            # The holder's hole (through its z) in the finger's file: the finger's hole (x, -z), through its thickness.
            # The part is the left finger: its holder is the mirrored one.
            at = moved(self.matrices["holder_l"], (hole[0], hole[1], 0.0))
            self.assertLess(math.hypot(at[0] - x, at[2] + z), 0.01)
        # The holder sits on the cut: its base (y 71.2 of its file) at the vendor file's y 96, its contact side at x 6.
        on_cut = moved(library_showcase.product(self.pose["part"], self.matrices["holder_r"]), (40.0, 71.2, 0.0))
        self.assertAlmostEqual(on_cut[0] - self.pose["shift"][0], 6.0, places=9)
        self.assertAlmostEqual(on_cut[1] - self.pose["shift"][1], library_showcase.CUT_Y, places=9)

    def test_the_left_side_is_the_mirror_image(self) -> None:
        mate = self.matrices["mate"]
        self.assertAlmostEqual(library_write.determinant(mate), -1.0, places=12)
        twice = library_showcase.product(mate, mate)
        self.assertLess(max(abs(twice[i][j] - (1.0 if i == j else 0.0)) for i in range(4) for j in range(4)), 1e-9, "a mirror is its own inverse")
        self.assertEqual(self.matrices["holder_l"], library_showcase.product(mate, self.matrices["holder_r"]))
        # Across the gripper's middle plane (x = 0 of the vendor's file): the part (the left finger) and its mate (the
        # right one) are each other's poses there, and so are their bodies.
        finger = self.pose["part"]
        for point in ((0.0, 0.0, 0.0), (10.0, -5.0, -60.0)):
            left = moved(finger, point)
            right = moved(finger, moved(mate, point))
            self.assertLess(math.dist(left, (-right[0], right[1], right[2])), 1e-9)
            self.assertLess(left[0], 0, "the part is the gripper's left finger")
        for part in ("coupler", "pins"):
            right = moved(library_showcase.product(finger, self.matrices[f"finger_r_{part}"]), (23.0, 80.0, 1.0))
            left = moved(library_showcase.product(finger, self.matrices[f"finger_l_{part}"]), (-23.0, 80.0, 1.0))
            self.assertLess(math.dist(left, (-right[0], right[1], right[2])), 1e-9)

    def test_the_part_is_the_left_finger_its_straps_toward_the_face_without_the_logo(self) -> None:
        # The owner's photo of the gripper, taken from the logo's side, shows both fingers' straps on the far side.  The
        # pad's placed record rolls its tails over the finger's side face at file y -25.8 (wrap "left": the viewer's
        # left with the fingertip up); with the part the gripper's LEFT finger that face looks along the vendor file's
        # +z, the shell's face without the logo (the logo's is at z -28.6), and the pad faces the gap (+x).
        self.assertEqual((library_showcase.PART_SIDE, library_showcase.MATE_SIDE), ("l", "r"))
        part, right = self.pose["part"], self.pose["finger"]
        self.assertEqual(part, library_showcase.product(library_showcase.HALF_TURN_Y, right))
        centre = library_showcase.SENSOR_CENTRE
        at = moved(part, centre)
        out = moved(part, (centre[0] - 1.0, centre[1], centre[2]))      # a step along the face's outward normal (file -x)
        self.assertGreater(out[0] - at[0], 0.99, "the pad looks at the gap")
        strap = moved(part, (centre[0], -25.8, centre[2]))
        self.assertAlmostEqual(strap[2], 12.9, places=6)
        self.assertAlmostEqual(moved(part, (centre[0], 0.0, centre[2]))[2], -12.9, places=6)
        placed = json.loads((WEB / "vendor" / "flexitac-v2" / "umi-finray.placed.json").read_text(encoding="utf-8"))
        self.assertEqual((placed["wrap"]["side"], placed["face"]["x"]), ("left", [0, 1, 0]), "the tails leave toward file -y")
        # The same finger as the mirror image of the right one: it is its own mirror image through its thickness.
        mirrored = library_showcase.product(library_showcase.MIRROR_X, right)
        for point in ((0.0, 0.0, 0.0), (10.0, -5.0, -60.0)):
            twin = (point[0], -25.8 - point[1], point[2])
            self.assertLess(math.dist(moved(part, point), moved(mirrored, twin)), 1e-9)
        # The camera: the rules', the grippers' homes (the user's request of 2026-11-16: "最上面的xarm gripper的空间朝向也要跟
        # 下面的这些家爪都对齐"; an override of its own, from the side without the logo, until then), and since the review of
        # that day the near finger see-through as every gripper's (drawn solid, it hid its own pad whole from there).
        self.assertFalse(hasattr(library_showcase, "CAMERA"))
        scene = json.loads((WEB / "library" / "scenes" / "flexitac-g1.json").read_text(encoding="utf-8"))
        self.assertNotIn("camera", scene)
        self.assertIn("The camera is the rules', the grippers' homes", scene["about"])
        self.assertIn("The near finger is drawn see-through, as every gripper's near finger is", scene["about"])
        self.assertNotIn("No finger is drawn see-through", scene["about"])
        self.assertEqual(library_showcase.SEE_THROUGH, ["mate"])
        self.assertEqual(scene["see_through"], ["mate"])

    def test_the_scene_s_matrices_are_rigid_and_its_approach_the_fingers_way(self) -> None:
        approach = self.matrices["approach"]
        self.assertAlmostEqual(math.fsum(value * value for value in approach), 1.0, places=12)
        # The vendor file's +y (along the fingers) in the finger's file; the finger's own length is its -z, leaned 0.93 degrees.
        along = moved(self.matrices["body_shell"], (0.0, 1.0, 0.0))
        origin = moved(self.matrices["body_shell"], (0.0, 0.0, 0.0))
        self.assertLess(math.dist([along[k] - origin[k] for k in range(3)], approach), 1e-12)
        self.assertAlmostEqual(math.degrees(math.acos(-approach[2])), 0.9256, places=3)
        scene = json.loads((LIBRARY / library_write.SHOWCASE_SCENE).read_text(encoding="utf-8"))
        self.assertLessEqual(abs(math.fsum(value * value for value in scene["approach"]) - 1), library_write.UNIT_TOL)
        for body in scene["bodies"]:
            self.assertIsNone(library_write._rigid(body["matrix"]), body["mesh"])
            self.assertEqual(body["matrix"], library_showcase.rounded(body["matrix"]), "nine decimals")
        self.assertIsNone(library_write._rigid(scene["mate"]["matrix"]))
        inverse = library_showcase.inverse(self.pose["part"])
        back = library_showcase.product(inverse, self.pose["part"])
        self.assertLess(max(abs(back[i][j] - (1.0 if i == j else 0.0)) for i in range(4) for j in range(4)), 1e-12)


class NoticeTests(unittest.TestCase):
    def test_the_rows_it_prints_are_rows_the_guards_take(self) -> None:
        files = library_showcase.committed()
        reports = {path: {"triangles_in": 10 * library_write.stl_triangles(data), "triangles_out": library_write.stl_triangles(data),
                          "source_to_result_mm": 0.0612, "result_to_source_mm": 0.0584} for path, data in files.items()}
        text = library_showcase.notice(files, reports)
        rows = {row[0]: row for row in library_write.NOTICE_ROW.findall(text)}
        # (The shapes the project draws have no row: they are the project's own.)
        self.assertEqual(sorted(rows), sorted([*library_write.SHOWCASE_VENDOR_FILES, library_showcase.HOLDER_BODY]))
        self.assertEqual(set(library_write.SHOWCASE_BODIES) - set(rows), {library_showcase.drawn_path(name) for name in library_showcase.DRAWN})
        for name, pinned in library_write.SHOWCASE_VENDOR_FILES.items():
            with self.subTest(row=name):
                self.assertEqual((rows[name][2].strip(), rows[name][4]), (library_write.SHOWCASE_OWNER, pinned))
                change = library_write.SHOWCASE_CHANGE.fullmatch(rows[name][3].strip())
                self.assertEqual((change.group(1), "cut at the holder" in rows[name][3]), ("0.061", name.endswith("_coupler.stl")))
        holder = rows["bodies/flexitac-g1/umi-right-finger-holder.stl"]
        self.assertEqual(holder[4], library_write.SHOWCASE_BODIES["bodies/flexitac-g1/umi-right-finger-holder.stl"])
        self.assertIn(holder[0], (LIBRARY / "NOTICE.md").read_text(encoding="utf-8"))
        # The committed notices' rows are these, with the build's own measured numbers.
        committed = {row[0]: row for row in library_write.NOTICE_ROW.findall((WEB / "vendor" / "ufactory-g1" / "NOTICE.md").read_text(encoding="utf-8"))}
        for name in library_write.SHOWCASE_VENDOR_FILES:
            self.assertEqual([committed[name][k] for k in (0, 1, 2, 4)], [rows[name][k] for k in (0, 1, 2, 4)])
        for header in (library_showcase.HEADER, library_showcase.HEADER_CUT, library_showcase.HEADER_HOLDER):
            self.assertLessEqual(len(header.encode("ascii")), 80)
            self.assertIn("by FlexiTac-Gen 2026, see NOTICE.md", header)
        self.assertEqual((WEB / "vendor" / "ufactory-g1" / "finger_l_coupler.stl").read_bytes()[:80], library_showcase.HEADER_CUT.encode("ascii").ljust(80))
        self.assertEqual((WEB / "vendor" / "ufactory-g1" / "body_shell.stl").read_bytes()[:80], library_showcase.HEADER.encode("ascii").ljust(80))
        self.assertEqual((LIBRARY / "bodies" / "flexitac-g1" / "umi-right-finger-holder.stl").read_bytes()[:80],
                         library_showcase.HEADER_HOLDER.encode("ascii").ljust(80))


class ModuleTests(unittest.TestCase):
    def test_the_tool_is_the_standard_library_s_and_names_no_host(self) -> None:
        path = ROOT / "tools" / "library_showcase.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path), feature_version=(3, 9))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        self.assertLessEqual(imported, STDLIB)
        self.assertIn("from __future__ import annotations", source)
        self.assertNotRegex(source, r"/home/|/Users/|/tmp/|flexitac_vis")
        self.assertNotRegex(source, r"\bCAD\b", "the page's words are 3D model")
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertNotIn("sum", calls, "math.fsum")
        # The sources come from the command line alone.
        self.assertIn('"--sources"', source)
        self.assertEqual(library_showcase.TOLERANCE_MM, 0.1)


if __name__ == "__main__":
    unittest.main()
