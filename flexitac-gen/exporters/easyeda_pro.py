"""Native EasyEDA Pro (JLCEDA Pro) projects of a build: one ``.epro2`` per board.

The Direct Gerber exporter (``direct_gerber``) writes our own Gerbers.  This
module writes the same boards as native EasyEDA Pro projects instead, so the
user imports them into EasyEDA Pro (pro.easyeda.com in a browser, or the
desktop app: File > Import > EasyEDA/JLCEDA (Professional)), checks them there
and lets EasyEDA write the Gerbers and the order.  Nothing here writes a
Gerber or claims to be EasyEDA: the files are project sources that EasyEDA
itself turns into fabrication data.

The format follows the EasyEDA Pro file format V3 (a ZIP holding
``project2.json`` and one ``.epru`` log whose lines are ``head||body``) as the
user's own JLCEDA exports write it (``fpc_design/source/original_jlceda/``;
the environment records are copied from them, ``easyeda_pro_template.json``),
and the project shape of the earlier source-independent writer that EasyEDA
Pro imported with its pads (``fpc_design/easyeda/tools/``): archive-local
FOOTPRINT, DEVICE, BOARD, SCH and SCH_PAGE documents beside the PCB, because
Pro drops free PCB pads and pads whose component has no schematic channel.

Mapping of one board (docs/EASYEDA_EXPORT.md):

* routes (centre line and width): ``POLY`` tracks, ``polyType`` NORMAL, on
  the Top Layer (1) with their net;
* electrodes and tail contacts (rectangles): ``RECT`` pads of two
  archive-local footprints (electrodes ``E1``, contacts ``J1``), placed by a
  ``COMPONENT`` at the origin with a ``PAD_NET`` per pad; a track would round
  the rectangle's ends, a pad keeps its corners and its net;
* coverlay openings: ``FILL`` on the Top Solder Mask Layer (5), as the
  originals draw them (``R`` for rectangles, a closed ``L`` ring for a masked
  field window); every pad has a zero mask expansion, so the openings are
  exactly ours;
* the outline and every routed cutout: closed ``POLY`` rings, ``polyType``
  BOARD_OUTLINE, on the Board Outline Layer (11), 0.1 mm wide like our GKO;
* stiffeners: ``FPC_FILL`` on the Bottom Stiffener Layer (59), material
  ``Polyimide``, thickness in mm from the stiffener (the profile's option);
* FPC mode: the stiffener layers 58 and 59 in use (EasyEDA's own
  ``setPcbType(2)`` sets exactly these), with the originals' layer table;
  the physical stack (``LAYER_PHYS``) has the profile's thicknesses;
* design rules: the originals' rule set with the clearances and track widths
  of the board's own DRC (``verification.checks``), so EasyEDA's DRC checks
  what ours checked.

Coordinates are mils (EasyEDA's unit) in our millimetre frame (Y up, no
offset), rounded to 1e-6 mil.  Everything is deterministic: UUIDs are digests
of the build identity, the board and this exporter's version, the ZIPs are
stored (no zlib) with fixed timestamps, and the bytes are the same on Python
3.9 and 3.12.  Before returning, every project is read back and compared with
the layout; any failure raises :class:`~exporters.direct_gerber.ExportError`.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import math
import textwrap
from pathlib import Path
from typing import Any, Mapping, Sequence
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from engine.geometry import rect_bounds

from . import direct_gerber
from .direct_gerber import ExportError, artifact_filenames

EASYEDA_EXPORTER_VERSION = "easyeda-pro-epro2/0.1.0"
EASYEDA_MANIFEST_FORMAT = "tactile-fpc-easyeda-export/v1"
EASYEDA_ARCHIVE_KEY = "easyeda_pro_zip"
EASYEDA_FOLDER = "easyeda_pro"
README_NAME = "README_EASYEDA.txt"
MANIFEST_NAME = "manifest.json"

# EasyEDA Pro layer ids (the originals' layer table, easyeda_pro_template.json).
LAYER_TOP = 1
LAYER_TOP_SILK = 3
LAYER_TOP_COVERLAY = 5  # Top Solder Mask Layer: the FPC coverlay openings
LAYER_OUTLINE = 11
LAYER_TOP_STIFFENER = 58
LAYER_BOTTOM_STIFFENER = 59
FPC_MODE_LAYERS = (LAYER_TOP_STIFFENER, LAYER_BOTTOM_STIFFENER)
STIFFENER_LAYERS = {"bottom": LAYER_BOTTOM_STIFFENER}
# Our stiffener materials as EasyEDA Pro names them (an unknown name is reset to Polyimide on load).
STIFFENER_MATERIALS = {"polyimide": "Polyimide"}
# EasyEDA Pro's PI stiffener thicknesses (mm); it resets any other value to 0.2 mm on load.
EASYEDA_PI_THICKNESSES_MM = (0.1, 0.15, 0.2, 0.225, 0.25)
# Indices of the 13 x 13 Safe Clearance table (EasyEDA Pro's row labels).
SAFE_TRACK, SAFE_SMD_PAD, SAFE_BOARD_OUTLINE = 0, 1, 11

MIL_PER_MM = 1000.0 / 25.4
OUTLINE_WIDTH_MM = 0.1  # the 12-pin original's L11 width and our GKO aperture
COVERLAY_FILL_WIDTH = 0.2  # mil, the originals' L5 FILL stroke (no effect on the region)
EDITOR_VERSION = "3.2.149.88089769"  # the EasyEDA Pro release the earlier writer's projects were imported into
DOCUMENT_EDIT_VERSION = "3.2.149"
DOCUMENT_TYPES = ("FOOTPRINT", "FOOTPRINT", "BOARD", "SCH", "SCH_PAGE", "DEVICE", "DEVICE", "PCB")
RULE_TEMPLATE_NAME = "JLCPCB Capability(Two Layers Board)"
_UPDATE_TIME = 315532800000  # 1980-01-01T00:00:00Z in ms, the ZIP timestamp
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_TEMPLATE = Path(__file__).with_name("easyeda_pro_template.json")
_READBACK_TOLERANCE_MM = 2e-6
_NET_BODY = {"netType": None, "specialColor": None, "retLine": True, "differentialName": None, "isPositiveNet": False, "equalLengthGroupName": None}
_RULE_SELECTOR = {"ruleOrder": 4, "ruleKeyValue": {}, "copperValue": {"COPPER": "Copper_copperRegion"}, "innerPlaneValue": {"PLANE": "Plane_innerPlane"}}
_SAFE_RULES = ("copperThickness1oz", "copperThickness2oz", "Plane_innerPlane", "Copper_copperRegion")
_TRACK_RULES = ("copperThickness1oz", "copperThickness2oz")
# The two footprints of a board: key, designator, title suffix.
_FOOTPRINTS = (("electrodes", "E1", "electrodes"), ("contacts", "J1", "contacts"))
_NOTE_COLUMNS = 78


def build_easyeda_exports(result: Mapping[str, Any], *, cache: Any = None) -> dict[str, bytes]:
    """The EasyEDA Pro archive of a valid build: ``{"easyeda_pro_zip": bytes}``.

    The archive (named by :func:`easyeda_filenames`) holds, under
    ``easyeda_pro/``, one native ``.epro2`` project per board (the Row FPC
    and the Column FPC are manufactured separately), ``README_EASYEDA.txt``
    (the steps in EasyEDA Pro and the order options) and ``manifest.json``.
    The result is checked and regenerated exactly as by
    :func:`~exporters.direct_gerber.build_exports` (``cache``: the engine
    :class:`~engine.BuildCache` of the result); its Direct Gerber archives
    do not change.  Raises :class:`ExportError` and nothing else.
    """

    try:
        return _build(result, cache)
    except ExportError:
        raise
    except Exception as error:  # nothing, malformed input included, escapes as another exception type
        raise ExportError(f"EasyEDA Pro export failed (internal error or malformed input; {type(error).__name__}: {error}).") from error


def easyeda_filenames(result: Mapping[str, Any]) -> dict[str, str]:
    """``{"easyeda_pro_zip": "<build_id>-easyeda-pro.zip"}``, plus the member name of each board's
    project under ``top_epro2`` and ``bottom_epro2`` (``easyeda_pro/<build_id>-<side>-<role>.epro2``)."""

    names = artifact_filenames(result)  # validates the build id and the boards
    build_id = names["project_review_bundle_zip"][: -len("-project-review.zip")]
    roles = {board["physical_side"]: board["role"] for board in result["boards"].values()}
    files = {EASYEDA_ARCHIVE_KEY: f"{build_id}-easyeda-pro.zip"}
    for side in ("top", "bottom"):
        files[f"{side}_epro2"] = f"{EASYEDA_FOLDER}/{_project_title(build_id, side, roles[side])}.epro2"
    return files


# --------------------------------------------------------------------------
# The archive.
# --------------------------------------------------------------------------


def _build(result: Any, cache: Any) -> dict[str, bytes]:
    build = direct_gerber._checked_build(result, cache)
    names = easyeda_filenames(result)
    template = _template()
    files: dict[str, bytes] = {}
    reports = []
    for side in ("top", "bottom"):
        board = build["boards_by_side"][side]
        project = _BoardProject(board, build, template)
        data = project.archive()
        summary = verify_project(data, board, build["profile"])
        files[names[f"{side}_epro2"]] = data
        reports.append({"file": names[f"{side}_epro2"], "sha256": _sha256(data), "bytes": len(data), **project.report(), "read_back": summary})
    files[f"{EASYEDA_FOLDER}/{README_NAME}"] = _readme(build, reports)
    files[f"{EASYEDA_FOLDER}/{MANIFEST_NAME}"] = _canonical(_manifest(build, reports)).encode("utf-8") + b"\n"
    data = direct_gerber._deterministic_zip(files)
    direct_gerber._verify_zip(data, files)
    return {EASYEDA_ARCHIVE_KEY: data}


def _manifest(build: Mapping[str, Any], reports: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    manifest = build["manifest"]
    return {
        "format": EASYEDA_MANIFEST_FORMAT,
        "exporter": EASYEDA_EXPORTER_VERSION,
        "build_id": manifest["build_id"],
        "build_sha256": manifest["build_sha256"],
        "design_sha256": manifest["design_sha256"],
        "profile": dict(manifest["profile"]),
        "easyeda_native_project": True,
        "gerbers_written_by": "EasyEDA Pro, on export from these projects (none are included here)",
        "units": {"coordinates": "mil (0.0254 mm), our millimetre frame", "stiffener_thickness": "mm"},
        "boards": list(reports),
    }


def _readme(build: Mapping[str, Any], reports: Sequence[Mapping[str, Any]]) -> bytes:
    manifest = build["manifest"]
    lines = [
        "TactileFPC: EasyEDA Pro projects",
        "",
        f"Build: {manifest['build_id']}",
        f"Profile: {manifest['profile']['id']}, revision {manifest['profile']['revision']}",
        "",
    ]
    lines.extend(_wrap(
        "Each .epro2 file below is a native EasyEDA Pro (JLCEDA Pro) project with one PCB: the Row FPC and the "
        "Column FPC are manufactured separately, so import, check and order each on its own. EasyEDA itself writes "
        "the Gerbers of these projects; these files contain no Gerber."
    ))
    for report in reports:
        lines.append("")
        lines.extend(_wrap(
            f"{report['file'].rpartition('/')[2]}: board {report['board_id']}, {report['role']} FPC, "
            f"{report['physical_side']} of the stack; {report['net_count']} nets, {report['contact_count']} contacts "
            f"(pads of J1), {report['electrode_count']} electrodes (pads of E1), {report['track_count']} tracks, "
            f"{report['coverlay_opening_count']} coverlay openings, {report['outline_contour_count']} outline contour(s); "
            + "; ".join(
                f"{group['count']} FPC stiffener(s) {group['material']} {group['thickness_mm']:g} mm on the {group['layer']}"
                for group in report["stiffeners"]
            )
            + "."
        ))
    steps = (
        "Open https://pro.easyeda.com in a web browser (nothing to install) and log in; the EasyEDA Pro desktop "
        "app works the same way.",
        "File > Import > EasyEDA/JLCEDA (Professional): the item reads EasyEDA(Professional)... (JLCEDA(Professional)... "
        "in the Chinese edition). Choose one .epro2 file and import it as a new project; open its PCB (menu names can "
        "differ slightly between EasyEDA versions).",
        "Check the board: the board type is FPC (the Top and Bottom Stiffener Layers are in the layer list); the "
        "FPC stiffener objects on the Bottom Stiffener Layer show Material Polyimide and the thickness above in their "
        "properties; the copper (tracks and pads) is on the Top Layer, the coverlay openings on the Top Solder Mask "
        "Layer and the outline on the Board Outline Layer.",
        "Run the design rule check (Design > Check DRC): it should report 0 errors. The rules are this board's own "
        "clearances.",
        "Order from EasyEDA (Order PCB...), or export the Gerbers there (Export > PCB Fabrication File(Gerber)...) "
        "and upload that ZIP to jlcpcb.com as a Flex PCB; EasyEDA's ZIP carries "
        "Gerber_BottomStiffenerLayer_pib_<thickness>.GBSL and jlcpcb.json, from which JLC reads the PI stiffener.",
        "Set the order options below, then repeat with the other .epro2 file.",
        "Optional: compare EasyEDA's Gerber ZIP with our Direct Gerber ZIP of the same board: python3 "
        "tools/compare_easyeda_gerbers.py <EasyEDA Gerber ZIP> <our direct-gerber ZIP>.",
    )
    lines.extend(("", "Steps", "-----"))
    for index, step in enumerate(steps, start=1):
        lines.extend(_wrap(step, f"{index}. ", "   "))
    lines.extend(("", "Order options (the profile's)", "-----------------------------"))
    for record in build["order_requirements"]:
        if record["kind"] == "order_option":
            lines.extend(_wrap(f"{record['topic']}: {record['requirement']}.", "- ", "  "))
    lines.append("")
    lines.extend(_wrap(
        "These projects are review candidates like the Direct Gerber ZIPs: no file here is a production "
        "approval. Review each board in EasyEDA and in the JLCPCB order before paying."
    ))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _wrap(text: str, first: str = "", rest: str = "") -> list[str]:
    return textwrap.wrap(text, width=_NOTE_COLUMNS, initial_indent=first, subsequent_indent=rest, break_on_hyphens=False, break_long_words=False)


# --------------------------------------------------------------------------
# One board's project.
# --------------------------------------------------------------------------


class _Log:
    """The ``.epru`` log: ``head||body`` lines joined by ``|\\n``, tickets counted across the documents."""

    def __init__(self, client: str, user: Mapping[str, str]) -> None:
        self.lines: list[str] = []
        self.ticket = 0
        self.client, self.user = client, dict(user)
        self.placeholders = 0

    def document(self, doc_type: str, uuid: str) -> None:
        self.ticket += 1
        self.placeholders = 0
        body = {
            "docType": doc_type, "client": self.client, "uuid": uuid, "updateTime": _UPDATE_TIME,
            "version": str(_UPDATE_TIME), "editVersion": DOCUMENT_EDIT_VERSION, "user": dict(self.user),
        }
        self.lines.append(_compact({"type": "DOCHEAD", "ticket": self.ticket}) + "||" + _compact(body))

    def add(self, kind: str, ident: Any, body: Mapping[str, Any]) -> None:
        self.ticket += 1
        head = {"type": kind, "ticket": self.ticket, "id": ident if isinstance(ident, str) else _compact(ident)}
        self.lines.append(_compact(head) + "||" + _compact(body))

    def reserve(self, data_type: str, first: int) -> None:
        """An ``ELE_PLACEHOLDER`` before the first ``e<first>`` of ``data_type``.

        EasyEDA numbers the elements of each type from 0 in log order and a
        placeholder takes ``max`` numbers, so ``max = first`` makes the
        numbers of a contiguous block ``e<first>``... equal their ids, as in
        EasyEDA's own files.
        """

        self.placeholders += 1
        self.add("ELE_PLACEHOLDER", f"placeholder{self.placeholders}", {"dataType": data_type, "max": first})

    def text(self) -> bytes:
        return "|\n".join(self.lines).encode("utf-8")


class _BoardProject:
    def __init__(self, board: Mapping[str, Any], build: Mapping[str, Any], template: Mapping[str, Any]) -> None:
        self.board, self.build, self.template = board, build, template
        self.profile = build["profile"]
        manifest = build["manifest"]
        self.title = _project_title(manifest["build_id"], board["physical_side"], board["role"])
        seed = f"{manifest['build_sha256']}:{board['id']}:{EASYEDA_EXPORTER_VERSION}"
        self.uuid = lambda *parts, length=32: _digest(seed, *parts)[:length]
        copper = board["layers"]["top_copper"]
        self.routes = list(copper["routes"])
        self.electrodes = list(copper["electrodes"])
        self.contacts = sorted(copper["pads"], key=lambda pad: pad["pin"])
        self.openings = list(board["layers"]["top_coverlay_openings"])
        self.stiffeners = list(board["layers"]["bottom_stiffener"])
        self.contours = [board["outline"]["points"], *board["outline"].get("cutouts", [])]
        self.nets = _ordered_nets([*(item["net"] for item in self.electrodes), *(pad["net"] for pad in self.contacts), *(route["net"] for route in self.routes)])
        self.footprint_pads = {"electrodes": self.electrodes, "contacts": self.contacts}
        self.docs = {
            "footprints": {key: self.uuid("footprint", key) for key, _, _ in _FOOTPRINTS},
            "devices": {key: self.uuid("device", key) for key, _, _ in _FOOTPRINTS},
            "board": self.uuid("board", length=16),
            "sch": self.uuid("sch"),
            "sch_page": self.uuid("sch-page"),
            "pcb": self.uuid("pcb"),
        }
        self.stiffener_thickness = [_stiffener_thickness(stiffener, self.profile, board["id"]) for stiffener in self.stiffeners]

    # -- archive ---------------------------------------------------------------------------------

    def archive(self) -> bytes:
        project = {"title": self.title, "cbb_project": False, "editorVersion": EDITOR_VERSION, "introduction": "", "description": self._description(), "tags": "[]"}
        files = (
            ("IMAGE/", b""),
            ("project2.json", json.dumps(project, ensure_ascii=False, indent=2).encode("utf-8")),
            (f"{self.title}.epru", self.log()),
        )
        stream = io.BytesIO()
        with ZipFile(stream, "w", compression=ZIP_STORED, strict_timestamps=True) as archive:
            for name, data in files:
                info = ZipInfo(filename=name, date_time=_ZIP_TIMESTAMP)
                info.compress_type = ZIP_STORED
                info.create_system = 3
                info.external_attr = (0o40755 << 16 | 0x10) if name.endswith("/") else 0o100644 << 16
                archive.writestr(info, data)
        return stream.getvalue()

    def _description(self) -> str:
        board = self.board
        return f"TactileFPC {board['role']} FPC ({board['physical_side']} of the stack), board {board['id']}; {EASYEDA_EXPORTER_VERSION}."

    def report(self) -> dict[str, Any]:
        groups: dict[tuple[str, float, str], int] = {}
        for stiffener, thickness in zip(self.stiffeners, self.stiffener_thickness):
            key = (STIFFENER_MATERIALS[stiffener["material"]], thickness, "Bottom Stiffener Layer")
            groups[key] = groups.get(key, 0) + 1
        return {
            "board_id": self.board["id"],
            "role": self.board["role"],
            "physical_side": self.board["physical_side"],
            "title": self.title,
            "documents": {"pcb": self.docs["pcb"], "board": self.docs["board"], "footprints": dict(self.docs["footprints"])},
            "net_count": len(self.nets),
            "electrode_count": len(self.electrodes),
            "contact_count": len(self.contacts),
            "track_count": len(self.routes),
            "coverlay_opening_count": len(self.openings),
            "outline_contour_count": len(self.contours),
            "stiffeners": [{"material": material, "thickness_mm": thickness, "layer": layer, "count": count} for (material, thickness, layer), count in groups.items()],
            "layers": {
                "tracks": LAYER_TOP, "pads": LAYER_TOP, "coverlay_openings": LAYER_TOP_COVERLAY,
                "outline": LAYER_OUTLINE, "stiffeners": LAYER_BOTTOM_STIFFENER,
            },
        }

    def log(self) -> bytes:
        identity = _digest(self.uuid("client"))
        log = _Log(identity[:16], {"uuid": identity[16:48], "nickname": "TactileFPC", "username": "tactilefpc", "avatar": "/image/avatar-default.png"})
        pad_ids = {}
        for key, designator, suffix in _FOOTPRINTS:
            pad_ids[key] = self._footprint(log, key, suffix)
        log.document("BOARD", self.docs["board"])
        log.add("META", "META", {"title": self.title, "zIndex": 2})
        log.document("SCH", self.docs["sch"])
        log.add("META", "META", {"title": self.title, "board": self.docs["board"], "zIndex": None})
        self._schematic_page(log)
        for index, (key, designator, suffix) in enumerate(_FOOTPRINTS, start=1):
            self._device(log, key, designator, suffix, index)
        self._pcb(log, pad_ids)
        return log.text()

    # -- library documents --------------------------------------------------------------------

    def _footprint(self, log: _Log, key: str, suffix: str) -> list[str]:
        footprint = self.template["footprint"]
        pads = self.footprint_pads[key]
        log.document("FOOTPRINT", self.docs["footprints"][key])
        log.add("CANVAS", "CANVAS", dict(footprint["canvas"]))
        log.add("LAYER", ["LAYER", LAYER_TOP], dict(footprint["layer_top"]))
        log.add("ACTIVE_LAYER", "ACTIVE_LAYER", {"layerId": LAYER_TOP})
        log.add("META", "META", {"title": self._footprint_title(suffix), "description": f"Archive-local {suffix} of TactileFPC board {self.board['id']}", "tags": [], "source": ""})
        log.reserve("PAD", 1)
        ids = []
        for number, pad in enumerate(pads, start=1):
            ids.append(f"e{number}")
            log.add("PAD", f"e{number}", _pad_body(pad, number))
        attribute = len(pads) + 1
        log.reserve("ATTR", attribute)
        log.add("ATTR", f"e{attribute}", {
            "groupId": 0, "parentId": "", "layerId": LAYER_TOP_SILK, "x": None, "y": None, "key": "Footprint", "value": self._footprint_title(suffix),
            "keyVisible": False, "valueVisible": False, "fontFamily": "default", "fontSize": 50, "strokeWidth": 8, "bold": False, "italic": False,
            "origin": "LEFT_BOTTOM", "angle": 0, "reverse": False, "expansion": 0, "mirror": False, "locked": False, "zIndex": attribute,
        })
        return ids

    def _footprint_title(self, suffix: str) -> str:
        return f"{self.board['id']}_{suffix}"

    def _schematic_page(self, log: _Log) -> None:
        log.document("SCH_PAGE", self.docs["sch_page"])
        log.add("CANVAS", "CANVAS", dict(self.template["sch_page"]["canvas"]))
        log.add("META", "META", {"title": "P1", "schematic": self.docs["sch"], "zIndex": 1})
        log.reserve("COMPONENT", 1)
        for index, (key, _, suffix) in enumerate(_FOOTPRINTS, start=1):
            log.add("COMPONENT", f"e{index}", {
                "locked": False, "zIndex": 10 + index, "partId": f"{self._footprint_title(suffix)}.1", "groupId": "",
                "x": 200 * index, "y": 0, "rotation": 0, "isMirror": False, "attrs": {},
            })
        number = len(_FOOTPRINTS) + 1
        log.reserve("ATTR", number)
        for index, (key, designator, _) in enumerate(_FOOTPRINTS, start=1):
            values = (
                ("Designator", designator, True), ("Footprint", self.docs["footprints"][key], False), ("Device", self.docs["devices"][key], False),
                ("Reuse Block", "", False), ("Group ID", "", False), ("Channel ID", "", False), ("Name", "", True), ("Unique ID", f"gge{index}", False),
            )
            for name, value, visible in values:
                log.add("ATTR", f"e{number}", {
                    "groupId": "", "locked": False, "zIndex": number, "parentId": f"e{index}", "key": name, "value": value,
                    "keyVisible": None if visible else False, "valueVisible": visible, "x": None, "y": None, "rotation": 0,
                    "color": None, "fillColor": None, "fontFamily": None, "fontSize": None, "strikeout": None, "underline": None,
                    "italic": None, "fontWeight": None, "align": None, "version": "2.0",
                })
                number += 1

    def _device(self, log: _Log, key: str, designator: str, suffix: str, index: int) -> None:
        log.document("DEVICE", self.docs["devices"][key])
        log.add("META", "META", {
            "title": self._footprint_title(suffix), "tags": [], "source": "", "images": [""],
            "attributes": {
                "Convert to PCB": "yes", "Add into BOM": "no", "Designator": designator, "Symbol": "",
                "Footprint": self.docs["footprints"][key], "Description": f"TactileFPC {suffix} of board {self.board['id']} (archive-local)",
            },
        })

    # -- the PCB --------------------------------------------------------------------------------

    def _pcb(self, log: _Log, pad_ids: Mapping[str, Sequence[str]]) -> None:
        pcb = self.template["pcb"]
        log.document("PCB", self.docs["pcb"])
        log.add("CANVAS", "CANVAS", dict(pcb["canvas"]))
        for layer_id, body in pcb["layers"]:
            body = dict(body)
            if layer_id in FPC_MODE_LAYERS:
                body.update(use=True, show=True)  # FPC mode (setPcbType(2) in EasyEDA Pro)
            log.add("LAYER", ["LAYER", layer_id], body)
        log.add("META", "META", {"title": self.title, "parent": "", "board": self.docs["board"], "zIndex": None})
        log.add("ACTIVE_LAYER", "ACTIVE_LAYER", {"layerId": LAYER_TOP})
        for net in self.nets:
            log.add("NET", ["NET", net], dict(_NET_BODY))
        log.add("RULE_TEMPLATE", "RULE_TEMPLATE", {"name": RULE_TEMPLATE_NAME})
        for name, body in pcb["primitives"]:
            log.add("PRIMITIVE", ["PRIMITIVE", name], dict(body))
        for layer_id, body in pcb["silk_opts"]:
            log.add("SILK_OPTS", ["SILK_OPTS", layer_id], dict(body))
        preference = dict(pcb["preference"])
        preference["lastTrackWidth"] = _mil(max(float(route["width_mm"]) for route in self.routes))
        log.add("PREFERENCE", "PREFERENCE", preference)
        for layer_id, body in self._layer_phys():
            log.add("LAYER_PHYS", ["LAYER_PHYS", layer_id], body)
        for rule_id, body in self._rules():
            log.add("RULE", ["RULE", *rule_id], body)
        for net in self.nets:
            log.add("RULE_SELECTOR", ["RULE_SELECTOR", ["NET", net]], copy.deepcopy(_RULE_SELECTOR))
        log.add("PANELIZE", "PANELIZE", copy.deepcopy(pcb["panelize"]))

        number = 1
        log.reserve("POLY", number)
        for route in self.routes:
            log.add("POLY", f"e{number}", {
                "partitionId": "", "groupId": 0, "netName": route["net"], "layerId": LAYER_TOP, "width": _mil(route["width_mm"]),
                "path": _polyline_path(route["points"]), "locked": False, "zIndex": number, "polyType": "NORMAL",
            })
            number += 1
        for contour in self.contours:
            log.add("POLY", f"e{number}", {
                "partitionId": "", "groupId": 0, "netName": "", "layerId": LAYER_OUTLINE, "width": _mil(OUTLINE_WIDTH_MM),
                "path": _ring_path(contour), "locked": False, "zIndex": number, "polyType": "BOARD_OUTLINE",
            })
            number += 1
        log.reserve("FILL", number)
        for opening in self.openings:
            path = [_ring_path(opening["points"])] if opening.get("shape") == "polygon" else [_rect_path(rect_bounds(opening))]
            log.add("FILL", f"e{number}", {
                "partitionId": "", "groupId": 0, "netName": "", "layerId": LAYER_TOP_COVERLAY, "width": COVERLAY_FILL_WIDTH, "fillStyle": "SOLID",
                "path": path, "locked": False, "zIndex": number, "isBridgingCopper": False, "networkList": [], "refs": [],
            })
            number += 1
        log.reserve("FPC_FILL", number)
        for stiffener, thickness in zip(self.stiffeners, self.stiffener_thickness):
            log.add("FPC_FILL", f"e{number}", {
                "partitionId": "", "groupId": 0, "layerId": STIFFENER_LAYERS[stiffener["side"]], "material": STIFFENER_MATERIALS[stiffener["material"]],
                "thickness": thickness, "path": [_ring_path(stiffener["points"])], "locked": False, "zIndex": number,
            })
            number += 1
        log.reserve("COMPONENT", number)
        for index, (key, designator, suffix) in enumerate(_FOOTPRINTS, start=1):
            component = f"e{number}"
            log.add("COMPONENT", component, {
                "partitionId": "", "groupId": 0, "layerId": LAYER_TOP, "x": 0, "y": 0, "angle": 0,
                "attrs": {"Name": "", "Unique ID": f"gge{index}", "Reuse Block": "", "Group ID": "", "Channel ID": f"$1e{index}"},
                "locked": False, "zIndex": number,
            })
            for pad_number, (pad, pad_id) in enumerate(zip(self.footprint_pads[key], pad_ids[key]), start=1):
                log.add("PAD_NET", ["PAD_NET", component, str(pad_number), pad_id], {"partitionId": "", "padNet": pad["net"], "padLen": 0})
            attribute = len(pad_ids[key]) + 1
            for offset, (name, value) in enumerate((("Footprint", self.docs["footprints"][key]), ("Designator", designator), ("Device", self.docs["devices"][key]))):
                log.add("ATTR", f"{component}-e{attribute + offset}", {
                    "partitionId": "", "groupId": 0, "parentId": component, "layerId": LAYER_TOP_SILK, "x": 0, "y": 0, "key": name, "value": value,
                    "keyVisible": False, "valueVisible": False, "fontFamily": "default", "fontSize": 45, "strokeWidth": 6, "bold": False, "italic": False,
                    "origin": "LEFT_BOTTOM", "angle": 0, "reverse": False, "expansion": 0, "mirror": False, "locked": False, "zIndex": None,
                })
            number += 1

    def _layer_phys(self) -> list[tuple[int, dict[str, Any]]]:
        """The originals' physical-stack records with the profile's thicknesses (mil): the coverlay (PI and
        adhesive) as the Top Solder Mask, the copper, the polyimide core as the dielectric, the profile's
        placeholder bottom copper and no bottom coverlay."""

        stack = self.profile["stackup"]
        thickness = {
            LAYER_TOP_COVERLAY: float(stack["coverlay_thickness_mm"]) + float(stack["coverlay_adhesive_thickness_mm"]),
            LAYER_TOP: float(stack["copper_thickness_mm"]),
            361: float(stack["core_polyimide_thickness_mm"]),
            2: float(stack["bottom_copper_placeholder_thickness_mm"]),
            6: 0.0,
        }
        records = []
        for layer_id, body in self.template["pcb"]["layer_phys"]:
            body = dict(body)
            if layer_id in thickness:
                body["thickness"] = _mil(thickness[layer_id])
            if layer_id == 361:  # the dielectric: the profile's polyimide core (core_polyimide_thickness_mm)
                body.update(material="Polyimide", permittivity=3.4, lossTangent=0.008)
            records.append((layer_id, body))
        return records

    def _rules(self) -> list[tuple[list[str], dict[str, Any]]]:
        clearance = board_clearances_mil(self.board)
        widths = [float(route["width_mm"]) for route in self.routes]
        epsilon = float(self.board["verification"]["numeric_epsilon_mm"])
        narrowest = min(min(widths), direct_gerber.fabrication_minimum(self.profile)[0])
        track = {
            "stroMin": _floor_mil(narrowest - epsilon),
            "stroDef": _mil(self.profile["routing"]["finger_trace_width_mm"]),
            "stroMax": max(100, math.ceil(max(widths) * MIL_PER_MM)),
        }
        rules = []
        for rule_id, body in self.template["pcb"]["rules"]:
            body = copy.deepcopy(body)
            context = body["ruleContext"]
            kind, name = rule_id
            if kind == "SAFE" and name in _SAFE_RULES:
                for table in context["safeSpacing"]:
                    content = table["content"]
                    content[SAFE_TRACK][SAFE_TRACK] = clearance["track_track"]
                    content[SAFE_SMD_PAD][SAFE_TRACK] = clearance["track_pad"]
                    content[SAFE_SMD_PAD][SAFE_SMD_PAD] = clearance["pad_pad"]
                    content[SAFE_BOARD_OUTLINE][SAFE_TRACK] = clearance["outline"]
                    content[SAFE_BOARD_OUTLINE][SAFE_SMD_PAD] = clearance["outline"]
            elif kind == "TRACK" and name in _TRACK_RULES:
                for entry in context["track"]["content"]:
                    entry.update(track)
            elif kind == "SOLDER":
                # Our coverlay openings are drawn on L5; a pad adds no opening of its own beyond its copper.
                context.update(padTopExpan=0, padBotExpan=0, testPointTopExpan=0, testPointBotExpan=0)
            rules.append((list(rule_id), body))
        return rules


def board_clearances_mil(board: Mapping[str, Any]) -> dict[str, float]:
    """EasyEDA's Safe Clearance values (mil) of a board, from the rules its DRC applied.

    Track-track is the route clearance; track-pad the smaller of the
    pad-trace and electrode-route clearances (electrodes and contacts are
    both SMD pads in EasyEDA); pad-pad the smallest of the pad, electrode and
    electrode-pad clearances; the board outline (cutouts included) the
    smallest copper-to-edge rule.  Each is floored to 1e-4 mil after taking
    off the DRC's numeric tolerance, so EasyEDA's DRC accepts what ours did.
    """

    verification = board["verification"]
    checks = verification["checks"]
    epsilon = float(verification["numeric_epsilon_mm"])

    def required(name: str) -> float:
        value = checks[name]["required_mm"]
        if not direct_gerber._finite(value) or float(value) <= 0:
            raise ExportError(f"{board['id']}: the DRC record {name} has no positive required_mm for EasyEDA's design rules.")
        return float(value)

    millimetres = {
        "track_track": required("route_route_clearance"),
        "track_pad": min(required("pad_trace_clearance"), required("electrode_route_clearance")),
        "pad_pad": min(required("pad_pad_clearance"), required("electrode_electrode_clearance"), required("electrode_pad_clearance")),
        "outline": min(required("copper_to_outline"), required("copper_to_cutout"), required("route_to_outline")),
    }
    return {key: _floor_mil(value - epsilon) for key, value in millimetres.items()}


def _pad_body(pad: Mapping[str, Any], number: int) -> dict[str, Any]:
    x0, y0, x1, y1 = rect_bounds(pad)
    return {
        "groupId": 0, "netName": "", "layerId": LAYER_TOP, "num": str(number),
        "centerX": _mil((x0 + x1) / 2), "centerY": _mil((y0 + y1) / 2), "padAngle": 0, "hole": None,
        "defaultPad": {"padType": "RECT", "width": _mil(x1 - x0), "height": _mil(y1 - y0), "radius": 0},
        "specialPad": [], "padOffsetX": 0, "padOffsetY": 0, "relativeAngle": None, "plated": True, "padType": "NORMAL",
        # Zero mask expansion: the pad's own opening is its copper, inside our L5 coverlay openings.
        "topSolderExpansion": 0, "bottomSolderExpansion": 0, "topPasteExpansion": 0, "bottomPasteExpansion": 0,
        "locked": False, "zIndex": number, "connectMode": None, "spokeSpace": None, "spokeWidth": None, "spokeAngle": None,
        "unusedInnerLayers": [], "padLen": 0,
    }


def _stiffener_thickness(stiffener: Mapping[str, Any], profile: Mapping[str, Any], board_id: str) -> float:
    """The FPC_FILL thickness (mm): the profile's one stiffener value (``stackup.stiffener_material`` and
    ``stackup.stiffener_thickness_mm``), which the stiffener must carry and EasyEDA Pro must offer."""

    stack = profile["stackup"]
    if stiffener.get("side") not in STIFFENER_LAYERS or stiffener.get("material") not in STIFFENER_MATERIALS:
        raise ExportError(f"{board_id}: only bottom polyimide stiffeners are exported to EasyEDA Pro.")
    option = direct_gerber._thickness_option(stack["stiffener_material"], stack["stiffener_thickness_mm"], profile)
    if option is None:
        raise ExportError(f"{board_id}: the profile's stiffener thickness {stack['stiffener_thickness_mm']!r} mm is not one of its options.")
    thickness = float(option)
    if stiffener["material"] != stack["stiffener_material"] or abs(float(stiffener["thickness_mm"]) - thickness) > 1e-9:
        raise ExportError(
            f"{board_id}: a stiffener of {stiffener['material']} {stiffener['thickness_mm']!r} mm is not the profile's "
            f"{stack['stiffener_material']} {thickness:g} mm (stackup.stiffener_material, stackup.stiffener_thickness_mm)."
        )
    if not any(abs(thickness - value) <= 1e-9 for value in EASYEDA_PI_THICKNESSES_MM):
        raise ExportError(
            f"{board_id}: EasyEDA Pro offers PI stiffeners of {', '.join(f'{value:g}' for value in EASYEDA_PI_THICKNESSES_MM)} mm, "
            f"not {thickness:g} mm (it would reset the thickness to 0.2 mm)."
        )
    return thickness


def _ordered_nets(nets: Sequence[str]) -> list[str]:
    """Channel nets in index order (ROW_/COL_), then NC_<pin> in pin order, each once."""

    def key(net: str) -> tuple[int, int, str]:
        stem, _, number = net.rpartition("_")
        return (1 if stem == "NC" else 0, int(number) if number.isdigit() else 0, net)

    return sorted(set(nets), key=key)


def _project_title(build_id: str, side: str, role: str) -> str:
    return f"{build_id}-{side}-{role}"


# --------------------------------------------------------------------------
# Geometry encoding.
# --------------------------------------------------------------------------


def _num(value: float) -> float | int:
    """A JSON number at 1e-6 (integers without a fraction, no negative zero)."""

    rounded = round(float(value), 6)
    if rounded == 0:
        return 0
    if rounded.is_integer() and abs(rounded) < 2.0 ** 53:
        return int(rounded)
    return rounded


def _mil(millimetres: float) -> float | int:
    return _num(float(millimetres) * MIL_PER_MM)


def _floor_mil(millimetres: float) -> float | int:
    return _num(math.floor(float(millimetres) * MIL_PER_MM * 10000.0) / 10000.0)


def _open_ring(points: Sequence[Sequence[float]]) -> list[list[float]]:
    ring = [[float(x), float(y)] for x, y in points]
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring.pop()
    return ring


def _twice_area(ring: Sequence[Sequence[float]]) -> float:
    return math.fsum(ring[index][0] * ring[(index + 1) % len(ring)][1] - ring[(index + 1) % len(ring)][0] * ring[index][1] for index in range(len(ring)))


def _clockwise(points: Sequence[Sequence[float]]) -> list[list[float]]:
    """The ring clockwise in our Y-up frame from the same first vertex: EasyEDA's outer contour."""

    ring = _open_ring(points)
    if _twice_area(ring) > 0:
        ring = [ring[0], *reversed(ring[1:])]
    return ring


def _ring_path(points: Sequence[Sequence[float]]) -> list[Any]:
    ring = _clockwise(points)
    path: list[Any] = [_mil(ring[0][0]), _mil(ring[0][1]), "L"]
    for x, y in [*ring[1:], ring[0]]:
        path.extend((_mil(x), _mil(y)))
    return path


def _polyline_path(points: Sequence[Sequence[float]]) -> list[Any]:
    path: list[Any] = [_mil(points[0][0]), _mil(points[0][1]), "L"]
    for x, y in points[1:]:
        path.extend((_mil(x), _mil(y)))
    return path


def _rect_path(bounds: Sequence[float]) -> list[Any]:
    """EasyEDA's rectangle: ``R``, the upper-left corner (minimum x, maximum y), width, height, rotation, radius."""

    x0, y0, x1, y1 = bounds
    return ["R", _mil(x0), _mil(y1), _mil(x1 - x0), _mil(y1 - y0), 0, 0]


# --------------------------------------------------------------------------
# Reading a project back (the exporter's check, the tests and tools/compare_easyeda_gerbers.py).
# --------------------------------------------------------------------------


def read_epro2(data: bytes) -> dict[str, Any]:
    """The members of an ``.epro2`` and its log as documents.

    Returns ``{"names", "project", "documents"}``; each document is
    ``{"docType", "uuid", "head", "body", "records": [(head, body), ...]}``.
    Lines are ``head||body`` joined by ``|\\n`` (a trailing ``|`` is
    accepted, as EasyEDA's own logs vary).
    """

    with ZipFile(io.BytesIO(data)) as archive:
        if archive.testzip() is not None:
            raise ValueError("an .epro2 member fails its CRC")
        names = archive.namelist()
        logs = [name for name in names if name.endswith(".epru")]
        if "project2.json" not in names or len(logs) != 1:
            raise ValueError("an .epro2 holds project2.json and one .epru log")
        project = json.loads(archive.read("project2.json").decode("utf-8"))
        text = archive.read(logs[0]).decode("utf-8")
    return {"names": names, "project": project, "documents": parse_epru(text)}


def parse_epru(text: str) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        line = line[:-1] if line.endswith("|") else line
        if not line.strip():
            continue
        if "||" not in line:
            raise ValueError(f"an .epru line without '||': {line[:60]!r}")
        head_text, body_text = line.split("||", 1)
        head = json.loads(head_text)
        body = json.loads(body_text) if body_text.strip() else ""
        if head.get("type") == "DOCHEAD":
            documents.append({"docType": body["docType"], "uuid": body["uuid"], "head": head, "body": body, "records": []})
        elif not documents:
            raise ValueError("an .epru record before the first DOCHEAD")
        else:
            documents[-1]["records"].append((head, body))
    return documents


def _mm(value: Any) -> float:
    return float(value) / MIL_PER_MM


def path_rings(path: Any) -> list[list[tuple[float, float]]]:
    """The rings (mm) of an EasyEDA polygon path: one ``[x, y, "L", ...]`` ring, an ``R`` rectangle, or a list of them."""

    if not path:
        return []
    if isinstance(path[0], list):
        return [ring for part in path for ring in path_rings(part)]
    if path[0] == "R":
        x, y, width, height, rotation = (float(value) for value in path[1:6])
        corners = [(0.0, 0.0), (width, 0.0), (width, -height), (0.0, -height)]
        angle = math.radians(rotation)
        cos, sin = math.cos(angle), math.sin(angle)
        return [[(_mm(x + u * cos - v * sin), _mm(y + u * sin + v * cos)) for u, v in corners]]
    return [_path_points(path, closed=True)]


def _path_points(path: Sequence[Any], closed: bool) -> list[tuple[float, float]]:
    values = [value for value in path if value != "L"]
    if any(isinstance(value, str) for value in values) or len(values) % 2:
        raise ValueError(f"only straight (L) EasyEDA paths are read: {list(path)[:8]}")
    points = [(_mm(values[index]), _mm(values[index + 1])) for index in range(0, len(values), 2)]
    if closed and len(points) > 1 and points[0] == points[-1]:
        points.pop()
    return points


def pcb_geometry(project: Mapping[str, Any]) -> dict[str, Any]:
    """The fabrication geometry (mm) of the PCB of a project read by :func:`read_epro2`.

    ``tracks`` (net, width, points of copper-layer POLY and LINE records),
    ``pads`` (net, layer, ring: a footprint pad placed by its component, the
    net from PAD_NET), ``outline`` (BOARD_OUTLINE rings), ``coverlay``
    (Top Solder Mask FILL rings), ``stiffeners`` (layer, material,
    thickness, ring), ``nets`` and ``layers`` (id -> body).
    """

    documents = project["documents"]
    pcbs = [document for document in documents if document["docType"] == "PCB"]
    if len(pcbs) != 1:
        raise ValueError(f"a project with one PCB document is expected, not {len(pcbs)}")
    footprints = {document["uuid"]: document for document in documents if document["docType"] == "FOOTPRINT"}
    records = pcbs[0]["records"]
    geometry: dict[str, Any] = {"tracks": [], "pads": [], "outline": [], "coverlay": [], "stiffeners": [], "nets": [], "layers": {}, "components": []}
    for head, body in records:
        kind = head["type"]
        if kind == "LAYER":
            geometry["layers"][json.loads(head["id"])[1]] = body
        elif kind == "NET":
            geometry["nets"].append(json.loads(head["id"])[1])
        elif kind == "POLY" and body.get("polyType") == "BOARD_OUTLINE":
            geometry["outline"].extend(path_rings(body["path"]) if isinstance(body["path"][0], list) or body["path"][0] == "R" else [_path_points(body["path"], True)])
        elif kind == "POLY" and body.get("layerId") in (1, 2):
            geometry["tracks"].append({"net": body["netName"], "layer": body["layerId"], "width_mm": _mm(body["width"]), "points": _path_points(body["path"], False)})
        elif kind == "LINE" and body.get("layerId") in (1, 2):
            points = [(_mm(body["startX"]), _mm(body["startY"])), (_mm(body["endX"]), _mm(body["endY"]))]
            geometry["tracks"].append({"net": body["netName"], "layer": body["layerId"], "width_mm": _mm(body["width"]), "points": points})
        elif kind == "FILL" and body.get("layerId") == LAYER_TOP_COVERLAY:
            geometry["coverlay"].extend(path_rings(body["path"]))
        elif kind == "FPC_FILL":
            for ring in path_rings(body["path"]):
                geometry["stiffeners"].append({"layer": body["layerId"], "material": body["material"], "thickness_mm": body["thickness"], "ring": ring})
    nets = {}
    for head, body in records:
        if head["type"] == "PAD_NET":
            _, component, number, pad_id = json.loads(head["id"])
            nets[(component, pad_id)] = (number, body["padNet"])
    for head, body in records:
        if head["type"] != "COMPONENT":
            continue
        attributes = {other["key"]: other["value"] for other_head, other in records if other_head["type"] == "ATTR" and other.get("parentId") == head["id"]}
        footprint = footprints.get(attributes.get("Footprint"))
        if footprint is None:
            raise ValueError(f"component {head['id']} has no footprint document in the project")
        geometry["components"].append({"id": head["id"], "designator": attributes.get("Designator"), "attrs": body["attrs"], "footprint": footprint["uuid"]})
        angle = math.radians(float(body.get("angle") or 0))
        cos, sin = math.cos(angle), math.sin(angle)
        x0, y0 = float(body["x"]), float(body["y"])
        for pad_head, pad in footprint["records"]:
            if pad_head["type"] != "PAD":
                continue
            shape = pad["defaultPad"]
            if shape.get("padType") != "RECT":
                raise ValueError(f"only RECT pads are read, not {shape.get('padType')}")
            half_width, half_height = float(shape["width"]) / 2, float(shape["height"]) / 2
            pad_angle = math.radians(float(pad.get("padAngle") or 0))
            pc, ps = math.cos(pad_angle), math.sin(pad_angle)
            ring = []
            for u, v in ((-half_width, -half_height), (half_width, -half_height), (half_width, half_height), (-half_width, half_height)):
                px = float(pad["centerX"]) + u * pc - v * ps
                py = float(pad["centerY"]) + u * ps + v * pc
                ring.append((_mm(x0 + px * cos - py * sin), _mm(y0 + px * sin + py * cos)))
            number, net = nets.get((head["id"], pad_head["id"]), (pad.get("num"), pad.get("netName") or ""))
            geometry["pads"].append({"net": net, "number": number, "component": head["id"], "layer": pad["layerId"], "ring": ring})
    return geometry


def verify_project(data: bytes, board: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """Read a board's ``.epro2`` back and compare it with the board's layout; raise ExportError on a difference.

    Checked: the stored members, the document sequence and links (PCB and
    SCH to BOARD, SCH_PAGE to SCH, each DEVICE to its FOOTPRINT, each PCB
    component's Unique ID and Channel ID to the schematic page), FPC mode,
    every track, pad and net, every coverlay opening, the outline contours
    and every stiffener with its layer, material and thickness, at the
    read-back tolerance of the Direct Gerber exporter (2e-6 mm).
    """

    label = f"{board['id']} EasyEDA project"
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if [info.filename for info in infos][:2] != ["IMAGE/", "project2.json"] or len(infos) != 3 or not infos[2].filename.endswith(".epru"):
                raise ExportError(f"{label}: the members must be IMAGE/, project2.json and one .epru log.")
            if any(info.compress_type != ZIP_STORED or info.date_time != _ZIP_TIMESTAMP for info in infos):
                raise ExportError(f"{label}: every member must be stored with the fixed timestamp.")
        project = read_epro2(data)
    except ExportError:
        raise
    except Exception as error:
        raise ExportError(f"{label}: the archive does not read back ({type(error).__name__}: {error}).") from error
    documents = project["documents"]
    if tuple(document["docType"] for document in documents) != DOCUMENT_TYPES:
        raise ExportError(f"{label}: the documents must be {', '.join(DOCUMENT_TYPES)}.")
    by_type: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        by_type.setdefault(document["docType"], []).append(document)

    def meta(document: Mapping[str, Any]) -> dict[str, Any]:
        (body,) = [body for head, body in document["records"] if head["type"] == "META"]
        return body

    board_uuid = by_type["BOARD"][0]["uuid"]
    if meta(by_type["PCB"][0]).get("board") != board_uuid or meta(by_type["SCH"][0]).get("board") != board_uuid:
        raise ExportError(f"{label}: the PCB and the schematic must belong to the BOARD document.")
    page = by_type["SCH_PAGE"][0]
    if meta(page).get("schematic") != by_type["SCH"][0]["uuid"]:
        raise ExportError(f"{label}: the schematic page must belong to the SCH document.")
    footprint_uuids = {document["uuid"] for document in by_type["FOOTPRINT"]}
    device_footprints = {document["uuid"]: meta(document)["attributes"].get("Footprint") for document in by_type["DEVICE"]}
    if set(device_footprints.values()) != footprint_uuids:
        raise ExportError(f"{label}: each DEVICE must name one of the archive's footprints.")
    page_attributes = {(body["parentId"], body["key"]): body["value"] for head, body in page["records"] if head["type"] == "ATTR"}
    geometry = pcb_geometry(project)
    for component in geometry["components"]:
        channel = component["attrs"].get("Channel ID", "")
        page_component = channel[2:] if channel.startswith("$1") else None
        if (
            page_component is None
            or page_attributes.get((page_component, "Unique ID")) != component["attrs"].get("Unique ID")
            or device_footprints.get(page_attributes.get((page_component, "Device"))) != component["footprint"]
        ):
            raise ExportError(f"{label}: component {component['id']} has no schematic channel to its device and footprint.")
    layers = geometry["layers"]
    if not all(layers.get(layer, {}).get("use") is True for layer in FPC_MODE_LAYERS):
        raise ExportError(f"{label}: the stiffener layers 58 and 59 must be in use (FPC mode).")

    copper = board["layers"]["top_copper"]
    routes = copper["routes"]
    tracks = geometry["tracks"]
    if len(tracks) != len(routes):
        raise ExportError(f"{label}: {len(tracks)} tracks for {len(routes)} routes.")
    for index, (track, route) in enumerate(zip(tracks, routes)):
        if track["net"] != route["net"] or track["layer"] != LAYER_TOP or abs(track["width_mm"] - float(route["width_mm"])) > _READBACK_TOLERANCE_MM:
            raise ExportError(f"{label}: track {index + 1} is not route {route['net']} on the Top Layer at {route['width_mm']} mm.")
        _same_points(f"{label} track {index + 1}", track["points"], route["points"])
    expected_pads = [*copper["electrodes"], *sorted(copper["pads"], key=lambda pad: pad["pin"])]
    pads = geometry["pads"]
    if len(pads) != len(expected_pads):
        raise ExportError(f"{label}: {len(pads)} pads for {len(expected_pads)} electrodes and contacts.")
    for pad, expected in zip(pads, expected_pads):
        x0, y0, x1, y1 = rect_bounds(expected)
        if pad["net"] != expected["net"] or pad["layer"] != LAYER_TOP:
            raise ExportError(f"{label}: pad {pad['component']}/{pad['number']} has net {pad['net']!r}, expected {expected['net']!r}.")
        _same_points(f"{label} pad {expected['net']}", pad["ring"], [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    expected_nets = _ordered_nets([*(pad["net"] for pad in expected_pads), *(route["net"] for route in routes)])
    if geometry["nets"] != expected_nets:
        raise ExportError(f"{label}: the NET records are not the board's nets.")
    openings = board["layers"]["top_coverlay_openings"]
    if len(geometry["coverlay"]) != len(openings):
        raise ExportError(f"{label}: {len(geometry['coverlay'])} coverlay openings for {len(openings)}.")
    for ring, opening in zip(geometry["coverlay"], openings):
        if opening.get("shape") == "polygon":
            expected_ring = _clockwise(opening["points"])
        else:
            x0, y0, x1, y1 = rect_bounds(opening)
            expected_ring = [(x0, y1), (x1, y1), (x1, y0), (x0, y0)]
        _same_points(f"{label} coverlay opening {opening['kind']}", ring, expected_ring)
    contours = [board["outline"]["points"], *board["outline"].get("cutouts", [])]
    if len(geometry["outline"]) != len(contours):
        raise ExportError(f"{label}: {len(geometry['outline'])} outline contours for {len(contours)}.")
    for ring, contour in zip(geometry["outline"], contours):
        _same_points(f"{label} outline contour", ring, _clockwise(contour))
    stiffeners = board["layers"]["bottom_stiffener"]
    if len(geometry["stiffeners"]) != len(stiffeners):
        raise ExportError(f"{label}: {len(geometry['stiffeners'])} FPC stiffeners for {len(stiffeners)}.")
    for found, stiffener in zip(geometry["stiffeners"], stiffeners):
        thickness = _stiffener_thickness(stiffener, profile, board["id"])
        if (found["layer"], found["material"], found["thickness_mm"]) != (STIFFENER_LAYERS[stiffener["side"]], STIFFENER_MATERIALS[stiffener["material"]], thickness):
            raise ExportError(f"{label}: an FPC stiffener is not {STIFFENER_MATERIALS[stiffener['material']]} {thickness:g} mm on layer {STIFFENER_LAYERS[stiffener['side']]}.")
        _same_points(f"{label} FPC stiffener", found["ring"], _clockwise(stiffener["points"]))
    return {
        "documents": len(documents),
        "pcb_records": len(by_type["PCB"][0]["records"]),
        "tracks": len(tracks),
        "pads": len(pads),
        "coverlay_openings": len(geometry["coverlay"]),
        "outline_contours": len(geometry["outline"]),
        "fpc_stiffeners": len(geometry["stiffeners"]),
    }


def _same_points(label: str, points: Sequence[Sequence[float]], expected: Sequence[Sequence[float]]) -> None:
    if len(points) != len(expected):
        raise ExportError(f"{label}: {len(points)} vertices, expected {len(expected)}.")
    for point, target in zip(points, expected):
        if abs(point[0] - float(target[0])) > _READBACK_TOLERANCE_MM or abs(point[1] - float(target[1])) > _READBACK_TOLERANCE_MM:
            raise ExportError(f"{label}: a vertex at ({point[0]:.6f}, {point[1]:.6f}), expected ({float(target[0]):.6f}, {float(target[1]):.6f}).")


# --------------------------------------------------------------------------
# Small helpers.
# --------------------------------------------------------------------------


def _template() -> dict[str, Any]:
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
