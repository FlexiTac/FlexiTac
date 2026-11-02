"""The EasyEDA Pro projects of a build (exporters/easyeda_pro.py, docs/EASYEDA_EXPORT.md).

Each board becomes one native ``.epro2`` (a ZIP of ``project2.json`` and an
``.epru`` log of ``head||body`` lines), all in a separate archive so the
Direct Gerber archives keep their bytes.  These tests read what was written,
for the default design, a CAD fit of the soft finger (the replica of
``asset/soft_gripper_finger.stl``: a diagonal Row bus on the surface
template), a masked field (a polygon coverlay window) and the straight Row
channel with a routed cutout: the archive and log structure like the user's
JLCEDA exports, every record's field set against theirs
(tests/fixtures/easyeda_original_field_sets.json, recomputed from the
originals when they are present), the layers and FPC mode, the PI
stiffeners against the profile, the nets and pads of every line, EasyEDA's
element numbering, the design rules against the board's own DRC, a
geometry cross-check of every layer against our own Gerbers
(tools/compare_easyeda_gerbers.py, which these tests also check, against
EasyEDA's own export of the user's verified project when present), the
read-back, the refusals, determinism (pinned digests, the same on Python
3.9 and 3.12 and under any hash seed), the HTTP route and the web button.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from engine import default_design, generate_design
from engine.geometry import rect_bounds
from exporters import ARTIFACT_KEYS, ExportError, build_easyeda_exports, build_exports, easyeda_filenames
from exporters import easyeda_pro
from exporters.easyeda_pro import DOCUMENT_TYPES, read_epro2

try:
    import surface_fixtures as F
    from geometry_checks import straight_channel
    from test_api_http import HttpTestCase
    from test_mask_export import TRIANGLE, _request
except ImportError:  # run as a package
    from tests import surface_fixtures as F
    from tests.geometry_checks import straight_channel
    from tests.test_api_http import HttpTestCase
    from tests.test_mask_export import TRIANGLE, _request

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT.parent / "fpc_design" / "source" / "original_jlceda" / "epro2"
ORIGINAL_NAMES = ("ProDoc_12pin_2mm_64mm_V2_2026-09-08.epro2", "ProDoc_32pin_2mm_24mm_2026-09-08.epro2")
# The user's project as EasyEDA Pro saved it after its native import, and EasyEDA's Gerber export of it.
NATIVE = ROOT.parent / "fpc_design" / "easyeda" / "epro2_based_native_jlc_candidate" / "FPC_Sensor_Epro2Based_EasyEDAProNative_StandardizedRouting_PI0p20mm_2026-09-13"
NATIVE_PAIRS = (
    ("easyeda_pro/verified_v3_local/12pin/ProDoc_12pin_2mm_64mm_V2_2026-09-08_EasyEDAProV3_2026-09-13.epro2", "jlcpcb_gerber/12pin/Gerber_ProDoc_12pin_2mm_64mm_V2_EasyEDAPro_2026-09-13.zip"),
    ("easyeda_pro/verified_v3_local/32pin/ProDoc_32pin_2mm_24mm_2026-09-08_EasyEDAProV3_2026-09-13.epro2", "jlcpcb_gerber/32pin/Gerber_ProDoc_32pin_2mm_24mm_EasyEDAPro_2026-09-13.zip"),
)
FIELD_SETS = json.loads((ROOT / "tests" / "fixtures" / "easyeda_original_field_sets.json").read_text(encoding="utf-8"))
PROJECT_KEYS = ["cbb_project", "description", "editorVersion", "introduction", "tags", "title"]
SOFT_SEED = (0.0, -12.9, -62.7)
SOFT_BASE = {"point_xyz": [0.0, -12.9, -3.0]}
# sha256 of the EasyEDA Pro archive of each case, the same on Python 3.9.6 and 3.12 and under any hash seed.  The default
# and the soft finger rewritten by P5-diagonal-bus.md section 24 (diagonal-bus/9): their build ids change with the
# construction's version (the bus), their boards not.  The soft finger again by section 26 (tip first): the replica's 708
# lies 0.018 mm nearer its tip (the tip-first field of its lattices, as many taxels), its tails as much longer; and by
# section 26.18 (a symmetric group's eighth row phases): the 708 another 0.25 mm nearer its tip, its tails 13.014 -> 13.264
# mm.  Rewritten by section 27 (diagonal-bus/10, the Row tail centred on the field): their build ids, and their Row tails
# moved onto the field's centre line (the default's by 0.048 mm), their fans and outlines with them.  The soft finger
# re-pinned on the merge of the two (2026-10-27): section 26's field with section 27's tails.  The default re-pinned by
# section 27.7 (the rectangular mode's default tails 12 / 12 mm: its Column board 4.5 mm longer; before: b56ef743...).
# Both rewritten by section 27.8 (diagonal-bus/11, one side's convex flank): their build ids change with the
# construction's version, their boards not (both sides; before: 9628c953..., c573b4ed...).  All four re-pinned by the
# profile revision 2026-10-29 (the gold-finger thickness order option, listed in README_EASYEDA.txt's order options, and the
# coverlay-window notes): their build ids change with the profiles' digests, their boards not (before: a12b04c8...,
# 6d7035e5..., a1e63ad3..., 31569177...).
DIGESTS = {
    "default": "15c169e4766f340c8d1a8d42d673579ce514c0117f84e2a1b85f3b82468878e5",
    "soft finger": "d25579132032ab5fde9f76bde77bac91c7fe7cd26d0edbc472510a85d92bde08",
    "masked triangle": "76152d5f71b4b219fde4721f54e3140dca0d1ed459c924d0c7903d451c978151",
    "straight channel with a cutout": "5a00b531a7a7417598392bc88dd191c917c2f691097ba54b370809f8221674c2",
}


def _compare_tool():
    spec = importlib.util.spec_from_file_location("compare_easyeda_gerbers", ROOT / "tools" / "compare_easyeda_gerbers.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = _compare_tool()


def _soft_finger_design() -> dict:
    from surface import fit, select
    from surface.mesh import read_stl

    data = F.stl_bytes(F.soft_finger_replica())
    seed = select.nearest_facet(read_stl(data), SOFT_SEED)
    result = fit.fit_route({"selection": {"ops": [{"op": "grow", "seed_facet": seed}]}, "base": SOFT_BASE, "options": {"shape": "fill"}}, data)
    return result["proposals"][0]["design"]


_BUILDS: dict = {}


def _builds() -> dict:
    """Each case's result, Direct Gerber archives, EasyEDA archive and its projects (built once)."""

    if not _BUILDS:
        cases = {
            "default": default_design(),
            "soft finger": _soft_finger_design(),
            "masked triangle": _request(10, 10, TRIANGLE),
            "straight channel with a cutout": straight_channel({"columns": 32}),
        }
        for name, design in cases.items():
            result = generate_design(design)
            assert result["ok"], (name, result["validation"]["errors"][:3])
            archive = build_easyeda_exports(result)["easyeda_pro_zip"]
            names = easyeda_filenames(result)
            with zipfile.ZipFile(io.BytesIO(archive)) as opened:
                projects = {side: opened.read(names[f"{side}_epro2"]) for side in ("top", "bottom")}
            boards = {board["physical_side"]: board for board in result["boards"].values()}
            _BUILDS[name] = {"result": result, "direct": build_exports(result), "archive": archive, "names": names, "projects": projects, "boards": boards}
    return _BUILDS


def _projects():
    """(case, side, board, epro2 bytes, read project) of every board."""

    for name, build in _builds().items():
        for side in ("top", "bottom"):
            data = build["projects"][side]
            yield name, side, build["boards"][side], data, read_epro2(data)


def _log_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        (name,) = [name for name in archive.namelist() if name.endswith(".epru")]
        return archive.read(name).decode("utf-8")


def _pcb(project: dict) -> list:
    (pcb,) = [document for document in project["documents"] if document["docType"] == "PCB"]
    return pcb["records"]


def _records(project: dict, kind: str) -> list:
    return [(head, body) for head, body in _pcb(project) if head["type"] == kind]


def _field_sets(text: str) -> tuple[dict, dict]:
    bodies: dict = {}
    heads: dict = {}
    document = None
    for line in text.split("|\n"):
        head_text, body_text = line.split("||", 1)
        head, body = json.loads(head_text), json.loads(body_text)
        if head["type"] == "DOCHEAD":
            document = body["docType"]
        key = f"{document} {head['type']}"
        bodies.setdefault(key, set()).add(tuple(sorted(body)) if isinstance(body, dict) else ())
        heads.setdefault(key, set()).add(tuple(head))
    return bodies, heads


def _replace_log(data: bytes, edit) -> bytes:
    """``data`` with its .epru log passed through ``edit`` (text -> text), stored like the exporter's."""

    stream = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(stream, "w", zipfile.ZIP_STORED) as target:
        for info in source.infolist():
            content = source.read(info)
            if info.filename.endswith(".epru"):
                content = edit(content.decode("utf-8")).encode("utf-8")
            target.writestr(info, content)
    return stream.getvalue()


class ArchiveTests(unittest.TestCase):
    """The archive, each .epro2 and the .epru log, structured like the user's JLCEDA exports."""

    def test_the_archive_holds_one_project_per_board_and_the_readme(self) -> None:
        for name, build in _builds().items():
            with self.subTest(case=name):
                names = build["names"]
                build_id = build["result"]["manifest"]["build_id"]
                self.assertEqual(names["easyeda_pro_zip"], f"{build_id}-easyeda-pro.zip")
                with zipfile.ZipFile(io.BytesIO(build["archive"])) as archive:
                    infos = archive.infolist()
                    readme = archive.read("easyeda_pro/README_EASYEDA.txt").decode("utf-8")
                    manifest = json.loads(archive.read("easyeda_pro/manifest.json"))
                expected = sorted(["easyeda_pro/README_EASYEDA.txt", "easyeda_pro/manifest.json", names["top_epro2"], names["bottom_epro2"]])
                self.assertEqual([info.filename for info in infos], expected)
                self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED and info.date_time == (1980, 1, 1, 0, 0, 0) for info in infos))
                for side in ("top", "bottom"):
                    board = build["boards"][side]
                    self.assertEqual(names[f"{side}_epro2"], f"easyeda_pro/{build_id}-{side}-{board['role']}.epro2")
                    self.assertIn(names[f"{side}_epro2"].rpartition("/")[2], readme)
                for phrase in ("https://pro.easyeda.com", "File > Import > EasyEDA/JLCEDA (Professional)", "EasyEDA(Professional)...", "FPC",
                               "Design > Check DRC", "Order PCB...", "PCB Fabrication File(Gerber)...", "jlcpcb.com", "tools/compare_easyeda_gerbers.py"):
                    self.assertIn(phrase, re.sub(r"\s+", " ", readme))
                self.assertEqual(manifest["build_id"], build_id)
                self.assertEqual([board["sha256"] for board in manifest["boards"]], [hashlib.sha256(build["projects"][side]).hexdigest() for side in ("top", "bottom")])

    def test_each_project_is_an_epro2_with_one_log(self) -> None:
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    infos = archive.infolist()
                    self.assertIsNone(archive.testzip())
                title = project["project"]["title"]
                self.assertEqual([info.filename for info in infos], ["IMAGE/", "project2.json", f"{title}.epru"])
                self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED for info in infos))
                self.assertEqual(sorted(project["project"]), PROJECT_KEYS)
                self.assertEqual(project["project"]["tags"], "[]")
                self.assertEqual([document["docType"] for document in project["documents"]], list(DOCUMENT_TYPES))

    def test_log_lines_are_head_and_body_like_the_originals(self) -> None:
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                text = _log_text(data)
                self.assertFalse(text.endswith(("|", "\n")))
                tickets = []
                seen = set()
                for line in text.split("|\n"):
                    head_text, separator, body_text = line.partition("||")
                    self.assertEqual(separator, "||", line[:80])
                    head = json.loads(head_text)
                    body = json.loads(body_text)
                    self.assertIsInstance(body, dict)
                    if head["type"] == "DOCHEAD":
                        self.assertEqual(list(head), ["type", "ticket"])
                        seen = set()
                    else:
                        self.assertEqual(list(head), ["type", "ticket", "id"])
                        self.assertNotIn((head["type"], head["id"]), seen, line[:80])
                        seen.add((head["type"], head["id"]))
                    tickets.append(head["ticket"])
                self.assertEqual(tickets, list(range(1, len(tickets) + 1)))

    def test_every_record_has_a_field_set_of_the_originals(self) -> None:
        bodies, heads = FIELD_SETS["bodies"], FIELD_SETS["heads"]
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                found_bodies, found_heads = _field_sets(_log_text(data))
                for key, sets in found_bodies.items():
                    self.assertIn(key, bodies, f"{key}: a record type the originals do not have")
                    for keys in sets:
                        self.assertIn(list(keys), bodies[key], f"{key}: the field set {keys} is not one of the originals'")
                for key, sets in found_heads.items():
                    for keys in sets:
                        self.assertIn(list(keys), heads[key], key)

    @unittest.skipUnless(ORIGINALS.is_dir(), "the user's JLCEDA exports are not beside this copy of the project")
    def test_the_field_set_fixture_is_the_originals(self) -> None:
        bodies: dict = {}
        heads: dict = {}
        for name in ORIGINAL_NAMES:
            data = (ORIGINALS / name).read_bytes()
            found_bodies, found_heads = _field_sets(_log_text(data))
            for key, sets in found_bodies.items():
                bodies.setdefault(key, set()).update(sets)
            for key, sets in found_heads.items():
                heads.setdefault(key, set()).update(sets)
            self.assertEqual(sorted(read_epro2(data)["project"]), PROJECT_KEYS)
        self.assertEqual({key: sorted(list(keys) for keys in sets) for key, sets in bodies.items()}, FIELD_SETS["bodies"])
        self.assertEqual({key: sorted(list(keys) for keys in sets) for key, sets in heads.items()}, FIELD_SETS["heads"])

    @unittest.skipUnless(ORIGINALS.is_dir(), "the user's JLCEDA exports are not beside this copy of the project")
    def test_the_environment_template_is_the_originals(self) -> None:
        template = easyeda_pro._template()["pcb"]
        for name in ORIGINAL_NAMES:
            with self.subTest(original=name):
                records = _pcb(read_epro2((ORIGINALS / name).read_bytes()))

                def of(kind):
                    return [(json.loads(head["id"]) if head["id"].startswith("[") else head["id"], body) for head, body in records if head["type"] == kind]

                # The 12-pin export is the template's source; the 32-pin one shows other layers and names their ids.
                ignored = {"layerId"} if name == ORIGINAL_NAMES[0] else {"layerId", "show"}
                layers = [[key[1], {k: v for k, v in body.items() if k not in ignored}] for key, body in of("LAYER")]
                self.assertEqual(layers, [[layer, {k: v for k, v in body.items() if k not in ignored}] for layer, body in template["layers"]])
                self.assertEqual([[key[1], body] for key, body in of("PRIMITIVE")], template["primitives"])
                self.assertEqual([[key[1], body] for key, body in of("LAYER_PHYS")], template["layer_phys"])
                self.assertEqual([[key[1:], body] for key, body in of("RULE")], template["rules"])
                self.assertEqual(of("PANELIZE"), [("PANELIZE", template["panelize"])])
                self.assertEqual(of("CANVAS"), [("CANVAS", template["canvas"])])


class PcbTests(unittest.TestCase):
    """The PCB document of every board: layers, FPC mode, stiffeners, nets, pads, numbering, rules and stack."""

    def test_layers_and_fpc_mode(self) -> None:
        template_ids = [layer for layer, _ in easyeda_pro._template()["pcb"]["layers"]]
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                layers = {json.loads(head["id"])[1]: body for head, body in _records(project, "LAYER")}
                self.assertEqual(list(layers), template_ids)
                # FPC mode: EasyEDA's setPcbType(2) sets the two stiffener layers in use.
                self.assertTrue(layers[58]["use"] and layers[59]["use"])
                self.assertEqual((layers[58]["layerType"], layers[59]["layerType"]), ("TOP_STIFFENER", "BOTTOM_STIFFENER"))
                kinds = {}
                for head, body in _pcb(project):
                    if head["type"] in ("POLY", "FILL", "FPC_FILL", "PAD", "LINE"):
                        kinds.setdefault((head["type"], body.get("polyType")), set()).add(body["layerId"])
                self.assertEqual(kinds, {("POLY", "NORMAL"): {1}, ("POLY", "BOARD_OUTLINE"): {11}, ("FILL", None): {5}, ("FPC_FILL", None): {59}})
                for layer in (1, 5, 11, 59):
                    self.assertTrue(layers[layer]["use"], layer)
                outlines = [body for head, body in _records(project, "POLY") if body["polyType"] == "BOARD_OUTLINE"]
                self.assertEqual(len(outlines), 1 + len(board["outline"]["cutouts"]))
                self.assertTrue(all(body["width"] == 3.937008 and body["netName"] == "" for body in outlines))
                pads = [body for document in project["documents"] if document["docType"] == "FOOTPRINT" for head, body in document["records"] if head["type"] == "PAD"]
                self.assertTrue(all(pad["layerId"] == 1 and pad["hole"] is None and pad["defaultPad"]["padType"] == "RECT" for pad in pads))
        self.assertTrue(any(_builds()["straight channel with a cutout"]["boards"][side]["outline"]["cutouts"] for side in ("top", "bottom")))

    def test_stiffeners_are_the_profiles_pi(self) -> None:
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                profile = _builds()[name]["result"]["profile"]
                stack = profile["stackup"]
                self.assertEqual(stack["stiffener_material"], "polyimide")
                fills = [body for head, body in _records(project, "FPC_FILL")]
                self.assertEqual(len(fills), len(board["layers"]["bottom_stiffener"]))
                self.assertGreaterEqual(len(fills), 1)
                for body in fills:
                    self.assertEqual((body["layerId"], body["material"]), (59, "Polyimide"))
                    self.assertEqual(body["thickness"], float(stack["stiffener_thickness_mm"]))
                    self.assertIn(body["thickness"], easyeda_pro.EASYEDA_PI_THICKNESSES_MM)
                    self.assertIn(body["thickness"], profile["fabrication"]["pi_stiffener_thickness_options_mm"])
        # 0.225 mm (the profile's) is one of EasyEDA Pro's PI thicknesses, as on JLC's list.
        self.assertEqual(easyeda_pro.EASYEDA_PI_THICKNESSES_MM, (0.1, 0.15, 0.2, 0.225, 0.25))

    def test_every_line_is_its_own_net_with_its_pads_and_tracks(self) -> None:
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                copper = board["layers"]["top_copper"]
                stem = "ROW" if board["role"] == "rows" else "COL"
                geometry = easyeda_pro.pcb_geometry(project)
                lines = sorted({electrode["net"] for electrode in copper["electrodes"]})
                self.assertTrue(all(re.fullmatch(stem + r"_\d{2,}", net) for net in lines))
                nets = [json.loads(head["id"])[1] for head, _ in _records(project, "NET")]
                no_connect = sorted((pad["net"] for pad in copper["pads"] if pad["net"].startswith("NC_")), key=lambda net: int(net[3:]))
                self.assertEqual(nets, lines + no_connect)
                self.assertEqual([json.loads(head["id"])[1:] for head, _ in _records(project, "RULE_SELECTOR")], [[["NET", net]] for net in nets])
                designators = {component["id"]: component["designator"] for component in geometry["components"]}
                self.assertEqual(sorted(designators.values()), ["E1", "J1"])
                for net in lines:
                    contacts = [pad for pad in geometry["pads"] if pad["net"] == net and designators[pad["component"]] == "J1"]
                    electrodes = [pad for pad in geometry["pads"] if pad["net"] == net and designators[pad["component"]] == "E1"]
                    tracks = [track for track in geometry["tracks"] if track["net"] == net]
                    self.assertEqual(len(contacts), 1, net)
                    self.assertEqual(len(electrodes), sum(1 for electrode in copper["electrodes"] if electrode["net"] == net), net)
                    self.assertEqual(len(tracks), sum(1 for route in copper["routes"] if route["net"] == net), net)
                self.assertEqual(len(_records(project, "PAD_NET")), len(copper["electrodes"]) + len(copper["pads"]))
                pins = {pad["number"]: pad["net"] for pad in geometry["pads"] if designators[pad["component"]] == "J1"}
                self.assertEqual(pins, {str(pad["pin"]): pad["net"] for pad in copper["pads"]})

    def test_elements_are_numbered_like_easyedas(self) -> None:
        # EasyEDA numbers each element type from 0 in log order; a placeholder takes ``max`` numbers.
        numbered = {"PAD", "ATTR", "COMPONENT", "POLY", "FILL", "FPC_FILL", "LINE"}
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                for document in project["documents"]:
                    counters: dict = {}
                    for head, body in document["records"]:
                        if head["type"] == "ELE_PLACEHOLDER":
                            self.assertGreaterEqual(body["max"], 1)
                            counters[body["dataType"]] = counters.get(body["dataType"], 0) + body["max"]
                        elif head["type"] in numbered and re.fullmatch(r"e\d+", head["id"]):
                            self.assertIn(head["type"], counters, f"{document['docType']} {head['id']} has no placeholder before it")
                            self.assertEqual(head["id"], f"e{counters[head['type']]}")
                            counters[head["type"]] += 1

    def test_components_have_their_schematic_channel(self) -> None:
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                documents = {document["docType"]: document for document in project["documents"]}
                page = {(body["parentId"], body["key"]): body["value"] for head, body in documents["SCH_PAGE"]["records"] if head["type"] == "ATTR"}
                devices = {document["uuid"] for document in project["documents"] if document["docType"] == "DEVICE"}
                footprints = {document["uuid"] for document in project["documents"] if document["docType"] == "FOOTPRINT"}
                for index, component in enumerate(easyeda_pro.pcb_geometry(project)["components"], start=1):
                    self.assertEqual(component["attrs"]["Channel ID"], f"$1e{index}")
                    self.assertEqual(page[(f"e{index}", "Unique ID")], component["attrs"]["Unique ID"])
                    self.assertIn(component["footprint"], footprints)
                    self.assertEqual(page[(f"e{index}", "Footprint")], component["footprint"])
                    self.assertIn(page[(f"e{index}", "Device")], devices)
                metas = {kind: [body for head, body in documents[kind]["records"] if head["type"] == "META"][0] for kind in ("PCB", "SCH", "SCH_PAGE")}
                self.assertEqual(metas["PCB"]["board"], documents["BOARD"]["uuid"])
                self.assertEqual(metas["SCH"]["board"], documents["BOARD"]["uuid"])
                self.assertEqual(metas["SCH_PAGE"]["schematic"], documents["SCH"]["uuid"])

    def test_design_rules_are_the_boards_drc(self) -> None:
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                checks = board["verification"]["checks"]
                epsilon = board["verification"]["numeric_epsilon_mm"]

                def rule(*names):
                    millimetres = min(checks[check]["required_mm"] for check in names) - epsilon
                    return math.floor(millimetres / 0.0254 * 10000) / 10000

                rules = {tuple(json.loads(head["id"])[1:]): body for head, body in _records(project, "RULE")}
                self.assertEqual(len(rules), 16)
                for key in ("copperThickness1oz", "copperThickness2oz", "Plane_innerPlane", "Copper_copperRegion"):
                    content = rules[("SAFE", key)]["ruleContext"]["safeSpacing"][0]["content"]
                    self.assertEqual([len(row) for row in content], [*range(1, 12), 11, 12])  # rows: 11 objects, Board Outline, Hole
                    self.assertAlmostEqual(content[0][0], rule("route_route_clearance"), places=9)
                    self.assertAlmostEqual(content[1][0], rule("pad_trace_clearance", "electrode_route_clearance"), places=9)
                    self.assertAlmostEqual(content[1][1], rule("pad_pad_clearance", "electrode_electrode_clearance", "electrode_pad_clearance"), places=9)
                    self.assertAlmostEqual(content[11][0], rule("copper_to_outline", "copper_to_cutout", "route_to_outline"), places=9)
                    self.assertEqual(content[11][1], content[11][0])
                widths = [route["width_mm"] for route in board["layers"]["top_copper"]["routes"]]
                for key in ("copperThickness1oz", "copperThickness2oz"):
                    (track,) = rules[("TRACK", key)]["ruleContext"]["track"]["content"]
                    self.assertLessEqual(track["stroMin"], min(widths) / 0.0254)
                    self.assertGreaterEqual(track["stroMax"], max(widths) / 0.0254)
                solder = rules[("SOLDER", "solderMaskExpansion")]["ruleContext"]
                self.assertEqual((solder["padTopExpan"], solder["padBotExpan"]), (0, 0))
                pads = [body for document in project["documents"] if document["docType"] == "FOOTPRINT" for head, body in document["records"] if head["type"] == "PAD"]
                self.assertTrue(all(pad["topSolderExpansion"] == 0 and pad["bottomSolderExpansion"] == 0 for pad in pads))
                self.assertEqual([body["name"] for head, body in _records(project, "RULE_TEMPLATE")], ["JLCPCB Capability(Two Layers Board)"])

    def test_physical_stack_is_the_profiles(self) -> None:
        for name, side, board, data, project in _projects():
            with self.subTest(case=name, side=side):
                stack = _builds()[name]["result"]["profile"]["stackup"]
                physical = {json.loads(head["id"])[1]: body for head, body in _records(project, "LAYER_PHYS")}
                self.assertEqual(list(physical), [3, 7, 5, 1, 361, 2, 6, 8, 4])
                mil = 1 / 0.0254
                self.assertAlmostEqual(physical[1]["thickness"], stack["copper_thickness_mm"] * mil, places=5)
                self.assertAlmostEqual(physical[361]["thickness"], stack["core_polyimide_thickness_mm"] * mil, places=5)
                self.assertEqual(physical[361]["material"], "Polyimide")
                self.assertAlmostEqual(physical[5]["thickness"], (stack["coverlay_thickness_mm"] + stack["coverlay_adhesive_thickness_mm"]) * mil, places=5)


class GeometryTests(unittest.TestCase):
    """Every layer of each project against our own Gerbers, by our own scanline fill."""

    def test_every_layer_agrees_with_our_gerbers(self) -> None:
        for name, build in _builds().items():
            for side in ("top", "bottom"):
                with self.subTest(case=name, side=side):
                    report = C.compare_zips(build["direct"][f"{side}_fpc_gerber_zip"], build["projects"][side], step=0.02)
                    self.assertTrue(report["ok"], json.dumps(report)[:1500])
                    self.assertEqual(report["offset_applied_mm"], [0.0, 0.0])
                    for layer in C.LAYERS:
                        entry = report["layers"][layer]
                        self.assertLess(entry["xor_mm2"], 1e-3, layer)
                        self.assertGreater(entry["ours"]["area_mm2"], 0, layer)
                        self.assertEqual(entry["easyeda"]["bbox_mm"], entry["ours"]["bbox_mm"], layer)
                    self.assertEqual(report["jlcpcb_stiffeners"]["ours"], [("bottom", "pi", "0.225")] * len(build["boards"][side]["layers"]["bottom_stiffener"]))

    def test_a_routed_cutout_is_a_hole_of_the_outline(self) -> None:
        build = _builds()["straight channel with a cutout"]
        (side,) = [side for side in ("top", "bottom") if build["boards"][side]["outline"]["cutouts"]]
        board = build["boards"][side]
        layers = C.project_layers(build["projects"][side])["layers"]
        with_hole = C.layer_summary(C.fill(layers["outline"], 0.02), 0.02)["area_mm2"]
        outer = [("poly", [tuple(point) for point in board["outline"]["points"]])]
        without = C.layer_summary(C.fill(outer, 0.02), 0.02)["area_mm2"]
        (cutout,) = board["outline"]["cutouts"]
        hole = abs(easyeda_pro._twice_area(cutout)) / 2
        self.assertAlmostEqual(without - with_hole, hole, delta=0.05 * hole)

    def test_a_missing_track_or_a_moved_stiffener_is_found(self) -> None:
        build = _builds()["default"]
        data = build["projects"]["top"]
        direct = build["direct"]["top_fpc_gerber_zip"]

        def drop_track(text):
            lines = text.split("|\n")
            index = next(i for i, line in enumerate(lines) if '"type":"POLY"' in line and '"polyType":"NORMAL"' in line)
            return "|\n".join(lines[:index] + lines[index + 1:])

        report = C.compare_zips(direct, _replace_log(data, drop_track), step=0.02)
        self.assertFalse(report["layers"]["copper"]["ok"])
        self.assertTrue(report["layers"]["outline"]["ok"])
        moved = _replace_log(data, lambda text: re.sub(r'("type":"FPC_FILL".*?"path":\[\[)(-?[\d.]+)', lambda m: m.group(1) + str(float(m.group(2)) + 40), text))
        report = C.compare_zips(direct, moved, step=0.02)
        self.assertFalse(report["layers"]["stiffener"]["ok"])
        self.assertFalse(report["ok"])

    def test_the_tool_reads_easyeda_style_gerbers(self) -> None:
        # EasyEDA's writer: 4.5 format, pads flashed with R and its RoundRect macro, fills as regions, G54D selects.
        build = _builds()["masked triangle"]
        for side in ("top", "bottom"):
            with self.subTest(side=side):
                geometry = easyeda_pro.pcb_geometry(read_epro2(build["projects"][side]))
                report = C.compare_zips(_easyeda_style_zip(geometry), build["direct"][f"{side}_fpc_gerber_zip"], step=0.02)
                self.assertTrue(report["ok"], json.dumps(report)[:1500])

    @unittest.skipUnless(NATIVE.is_dir(), "the user's EasyEDA-verified project is not beside this copy of the project")
    def test_the_reader_matches_easyedas_own_gerber_export(self) -> None:
        # The user's project as EasyEDA Pro saved it and EasyEDA's Gerbers of it: our reading of EasyEDA's records
        # (mils, Y up, R anchored at its upper-left corner, pads placed by their component) is EasyEDA's own.
        for project_path, gerber_path in NATIVE_PAIRS:
            with self.subTest(project=project_path):
                project = C.project_layers((NATIVE / project_path).read_bytes())
                native = C.read_zip((NATIVE / gerber_path).read_bytes())
                for layer in ("copper", "stiffener"):
                    first, second = C.fill(project["layers"][layer], 0.02), C.fill(native["layers"][layer], 0.02)
                    area = C.layer_summary(second, 0.02)["area_mm2"]
                    self.assertGreater(area, 100)
                    self.assertLess(C.compare_rows(first, second, 0.02), 1e-4 * area, layer)
                self.assertEqual(C._stiffener_records(project["jlcpcb"]), C._stiffener_records(native["jlcpcb"]))

    def test_the_command_line(self) -> None:
        build = _builds()["default"]
        with tempfile.TemporaryDirectory() as directory:
            paths = {}
            for key, data in (("top", build["direct"]["top_fpc_gerber_zip"]), ("bottom", build["direct"]["bottom_fpc_gerber_zip"]), ("project", build["projects"]["top"])):
                paths[key] = Path(directory) / f"{key}.zip"
                paths[key].write_bytes(data)
            report = Path(directory) / "report.json"
            run = [sys.executable, "-B", str(ROOT / "tools" / "compare_easyeda_gerbers.py")]
            same = subprocess.run([*run, str(paths["top"]), str(paths["project"]), "--json", str(report)], capture_output=True, text=True, timeout=120)
            self.assertEqual(same.returncode, 0, same.stdout + same.stderr)
            self.assertIn("RESULT: every layer agrees", same.stdout)
            self.assertTrue(json.loads(report.read_text())["ok"])
            different = subprocess.run([*run, str(paths["bottom"]), str(paths["top"]), "--align", "none"], capture_output=True, text=True, timeout=120)
            self.assertEqual(different.returncode, 1, different.stdout + different.stderr)
            broken = subprocess.run([*run, str(paths["top"]), str(Path(directory) / "missing.zip")], capture_output=True, text=True, timeout=120)
            self.assertEqual(broken.returncode, 2)


def _easyeda_style_zip(geometry: dict) -> bytes:
    """A Gerber ZIP written the way EasyEDA Pro writes its own (tests of the compare tool)."""

    def coordinate(value):
        return str(int(round(value * 100000)))

    def header(apertures):
        return ["G04 EasyEDA-style test file*", "%FSLAX45Y45*%", "%MOMM*%",
                "%AMRoundRect*1,1,$1,$2,$3*1,1,$1,$4,$5*1,1,$1,0-$2,0-$3*1,1,$1,0-$4,0-$5*20,1,$1,$2,$3,$4,$5,0*20,1,$1,$4,$5,0-$2,0-$3,0*"
                "20,1,$1,0-$2,0-$3,0-$4,0-$5,0*20,1,$1,0-$4,0-$5,$2,$3,0*4,1,4,$2,$3,$4,$5,0-$2,0-$3,0-$4,0-$5,$2,$3,0*%", *apertures, "G75*"]

    def region(ring):
        lines = ["G36*", f"G01X{coordinate(ring[0][0])}Y{coordinate(ring[0][1])}D02*"]
        lines.extend(f"G01X{coordinate(x)}Y{coordinate(y)}D01*" for x, y in [*ring[1:], ring[0]])
        return [*lines, "G37*"]

    widths = sorted({round(track["width_mm"], 5) for track in geometry["tracks"]})
    apertures = [f"%ADD{10 + index}C,{width}*%" for index, width in enumerate(widths)]
    copper = header(apertures + ["%ADD30RoundRect,0X-0.15X2X0.15X2*%"])
    for track in geometry["tracks"]:
        copper.append(f"G54D{10 + widths.index(round(track['width_mm'], 5))}*")
        (x, y), *rest = track["points"]
        copper.append(f"G01X{coordinate(x)}Y{coordinate(y)}D02*")
        copper.extend(f"G01X{coordinate(px)}Y{coordinate(py)}D01*" for px, py in rest)
    for pad in geometry["pads"]:
        xs, ys = [point[0] for point in pad["ring"]], [point[1] for point in pad["ring"]]
        width, height = max(xs) - min(xs), max(ys) - min(ys)
        if abs(width - 0.3) < 1e-6 and abs(height - 4.0) < 1e-6:
            copper.extend(["G54D30*", f"G01X{coordinate((min(xs) + max(xs)) / 2)}Y{coordinate((min(ys) + max(ys)) / 2)}D03*"])
        else:
            copper.extend(region(pad["ring"]))
    mask = header(["%ADD10C,0.01*%"])
    for ring in geometry["coverlay"]:
        mask.extend(region(ring))
    outline = header(["%ADD10C,0.1*%", "G54D10*"])
    for ring in geometry["outline"]:
        outline.append(f"G01X{coordinate(ring[0][0])}Y{coordinate(ring[0][1])}D02*")
        outline.extend(f"G01X{coordinate(x)}Y{coordinate(y)}D01*" for x, y in [*ring[1:], ring[0]])
    stiffener = header([])
    for item in geometry["stiffeners"]:
        stiffener.extend(region(item["ring"]))
    files = {
        "Gerber_TopLayer.GTL": copper, "Gerber_TopSolderMaskLayer.GTS": mask, "Gerber_BoardOutlineLayer.GKO": outline,
        "Gerber_BottomStiffenerLayer_pib_0.225.GBSL": stiffener,
    }
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for member, lines in files.items():
            archive.writestr(member, "\n".join([*lines, "M02*"]) + "\n")
        archive.writestr("jlcpcb.json", json.dumps({"fpcStiffeners": [{"layer": "bottom", "material": "pi", "thickness": "0.225"} for _ in geometry["stiffeners"]]}))
    return stream.getvalue()


class DeterminismTests(unittest.TestCase):
    def test_the_archives_are_pinned(self) -> None:
        for name, build in _builds().items():
            with self.subTest(case=name):
                again = build_easyeda_exports(build["result"])["easyeda_pro_zip"]
                self.assertEqual(again, build["archive"])
                self.assertEqual(hashlib.sha256(build["archive"]).hexdigest(), DIGESTS[name])

    def test_the_bytes_do_not_depend_on_the_hash_seed(self) -> None:
        code = (
            "import hashlib\nfrom engine import default_design, generate_design\nfrom exporters import build_easyeda_exports\n"
            "print(hashlib.sha256(build_easyeda_exports(generate_design(default_design()))['easyeda_pro_zip']).hexdigest())\n"
        )
        for seed in ("0", "12345"):
            with self.subTest(seed=seed):
                completed = subprocess.run(
                    [sys.executable, "-B", "-c", code], capture_output=True, text=True, cwd=ROOT, timeout=300,
                    env=dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1"),
                )
                self.assertEqual(completed.returncode, 0, completed.stderr[-500:])
                self.assertEqual(completed.stdout.strip(), DIGESTS["default"])


class RefusalTests(unittest.TestCase):
    def test_an_invalid_result_is_refused(self) -> None:
        for result in ({}, {"ok": False}, None, []):
            with self.subTest(result=result):
                with self.assertRaises(ExportError):
                    build_easyeda_exports(result)
        invalid = generate_design({"matrix": {"pitch_x_mm": 1.0, "taxel_width_mm": 0.9}})
        self.assertFalse(invalid["ok"])
        with self.assertRaises(ExportError):
            build_easyeda_exports(invalid)

    def test_a_changed_board_is_refused(self) -> None:
        result = copy.deepcopy(_builds()["default"]["result"])
        result["boards"]["row"]["layers"]["top_copper"]["routes"][0]["points"][0][0] += 0.5
        with self.assertRaises(ExportError) as caught:
            build_easyeda_exports(result)
        self.assertIn("does not match the geometry the engine generates", str(caught.exception))

    def test_the_thickness_is_the_profiles_one_value(self) -> None:
        # The user may order 0.25 mm after JLC's PI calculator: one profile value changes every FPC_FILL.
        result = _builds()["default"]["result"]
        profile = copy.deepcopy(result["profile"])
        profile["stackup"]["stiffener_thickness_mm"] = 0.25
        board = copy.deepcopy(result["boards"]["row"])
        for stiffener in board["layers"]["bottom_stiffener"]:
            stiffener["thickness_mm"] = 0.25
            self.assertEqual(easyeda_pro._stiffener_thickness(stiffener, profile, board["id"]), 0.25)
            stiffener["thickness_mm"] = 0.225
            with self.assertRaises(ExportError) as caught:
                easyeda_pro._stiffener_thickness(stiffener, profile, board["id"])
            self.assertIn("is not the profile's polyimide 0.25 mm", str(caught.exception))

    def test_a_thickness_easyeda_does_not_offer_is_refused(self) -> None:
        with mock.patch.object(easyeda_pro, "EASYEDA_PI_THICKNESSES_MM", (0.1, 0.15, 0.2, 0.25)):
            with self.assertRaises(ExportError) as caught:
                build_easyeda_exports(_builds()["default"]["result"])
        self.assertIn("would reset the thickness to 0.2 mm", str(caught.exception))

    def test_the_read_back_catches_a_changed_project(self) -> None:
        build = _builds()["default"]
        board, data = build["boards"]["top"], build["projects"]["top"]
        profile = build["result"]["profile"]
        self.assertEqual(easyeda_pro.verify_project(data, board, profile)["pads"], 24)
        edits = {
            "a net dropped": lambda text: text.replace('"padNet":"ROW_05"', '"padNet":""', 1),
            "a track moved": lambda text: re.sub(r'("netName":"ROW_12","layerId":1,"width":\d+,"path":\[)([\d.]+)', lambda m: m.group(1) + str(float(m.group(2)) + 1), text, count=1),
            "the stiffener thinner": lambda text: text.replace('"thickness":0.225', '"thickness":0.2'),
            "the stiffener on the top": lambda text: text.replace('"layerId":59,"material"', '"layerId":58,"material"'),
            "FPC mode off": lambda text: text.replace('"layerName":"Bottom Stiffener Layer","use":true', '"layerName":"Bottom Stiffener Layer","use":false'),
            "a coverlay opening dropped": lambda text: re.sub(r'\|\n\{"type":"FILL"[^\n]*', "", text, count=1),
            "the channel broken": lambda text: text.replace('"Channel ID":"$1e2"', '"Channel ID":"$1e9"'),
        }
        for name, edit in edits.items():
            with self.subTest(edit=name):
                changed = _replace_log(data, edit)
                self.assertNotEqual(changed, data)
                with self.assertRaises(ExportError):
                    easyeda_pro.verify_project(changed, board, profile)

    def test_the_direct_gerber_archives_are_unchanged(self) -> None:
        for name, build in _builds().items():
            with self.subTest(case=name):
                self.assertEqual(sorted(build["direct"]), sorted(ARTIFACT_KEYS))
                with zipfile.ZipFile(io.BytesIO(build["direct"]["project_review_bundle_zip"])) as bundle:
                    self.assertFalse([member for member in bundle.namelist() if "easyeda" in member.lower() or member.endswith(".epro2")])


class EasyedaRouteTests(HttpTestCase):
    def test_the_export_route(self) -> None:
        build = _builds()["default"]
        reply = self.request("POST", "/api/export/easyeda-pro", build["result"]["design"])
        self.assertEqual(reply.status, 200, reply.body[:300])
        self.assertEqual(reply.headers["content-type"], "application/zip")
        self.assertEqual(reply.headers["content-disposition"], f'attachment; filename="{build["names"]["easyeda_pro_zip"]}"')
        self.assertEqual(reply.headers["x-build-id"], build["result"]["manifest"]["build_id"])
        self.assertEqual(reply.body, build["archive"])
        blocked = self.assertError(self.request("POST", "/api/export/easyeda-pro", {"matrix": {"pitch_x_mm": 1.0, "taxel_width_mm": 0.9}}), 422, "E_EXPORT_BLOCKED")
        self.assertIn("validation", blocked)
        wrong = self.request("GET", "/api/export/easyeda-pro")
        self.assertEqual((wrong.status, wrong.headers.get("allow")), (405, "POST"))


class WebTests(unittest.TestCase):
    def test_the_download_button_sits_with_the_other_downloads(self) -> None:
        # In the downloads section: the two Gerber ZIPs in sight, the other files (the EasyEDA Pro projects first) under
        # "More files" since 2026-11-02.
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        downloads = re.search(r'<section class="downloads".*?</section>', html, re.S).group(0)
        actions = re.search(r'<div class="download-actions">(.*?)</div>', downloads, re.S).group(1)
        self.assertIn('data-export="bottom-gerber"', actions)
        more = re.search(r'<details class="more-files" id="moreFiles">(.*?)</details>', downloads, re.S).group(1)
        self.assertRegex(more, r'<div class="download-actions">\s*<button type="button" data-export="easyeda-pro" disabled[^>]*>EasyEDA Pro projects ZIP</button>')
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('if (kind === "easyeda-pro") return `${id}-easyeda-pro.zip`;', script)
        self.assertIn('document.querySelectorAll("[data-export]")', script)


if __name__ == "__main__":
    unittest.main()
