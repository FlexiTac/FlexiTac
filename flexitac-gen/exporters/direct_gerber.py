"""Pure-stdlib Direct Gerber review-candidate exporter.

This module deliberately accepts the already-derived in-memory geometry from
``engine.generate_design``.  It does not open an EasyEDA project, KiCad board,
or a prior Gerber at runtime.  The output is consequently fast and
deterministic, but it is *not* an EasyEDA-native export and is never a
manufacturing approval.  Each package must still be reviewed in JLCPCB before
ordering, especially its outline, coverlay openings and PI stiffeners.

The exporter does not take the result's geometry on trust.  Before writing,
the result must be a valid, self-consistent build (identity digests,
profile, validation, well-formed boards), and the engine regenerates the
boards from the result's canonical design and profile, which runs the
whole-board DRC again: the result's boards, DRC records, previews, manifest
and design warnings must be exactly what the engine gives, so the files
written are bound to the build identity they carry.  After writing, every
Gerber, ``jlcpcb.json`` and netlist is decoded again and compared with the
layout, ``ORDER_NOTES.txt`` is checked against the order requirements and
the board it describes, and every ZIP is re-opened (D17).  Any failure,
malformed input included, raises :class:`ExportError` and nothing else.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import textwrap
from typing import Any, Mapping, Sequence
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from engine import REQUEST_WARNING_CODES, BuildCache, default_design, design_mask, generate_design
from engine import core as engine_core
from engine.drc import ring_is_simple
from engine.geometry import ANCHORS, ceil6, rect_bounds, rect_corners
from engine.layout import LAYOUT_FORMAT, row_bus
from engine.profile import STIFFENER_THICKNESS_OPTIONS, copper_weight_oz, fabrication_minimum, order_requirements, profile_issues

from .ipc356 import UNITS as NETLIST_UNITS
from .ipc356 import netlist_text, read_netlist

EXPORTER_VERSION = "direct-gerber-pure-stdlib/0.3.0"
EXPORT_MANIFEST_FORMAT = "tactile-fpc-export-manifest/v2"
BOARD_MANIFEST_FORMAT = "tactile-fpc-board-manifest/v1"
VALIDATION_FORMAT = "tactile-fpc-validation/v1"
ARTIFACT_KEYS = ("top_fpc_gerber_zip", "bottom_fpc_gerber_zip", "project_review_bundle_zip")
_DIRECT_STATUS = "direct_gerber_jlc_review_candidate"
_GTL = "Gerber_TopLayer.GTL"
_GTS = "Gerber_TopSolderMaskLayer.GTS"
_GKO = "Gerber_BoardOutlineLayer.GKO"
_JLC_METADATA = "jlcpcb.json"
_NETLIST = "netlist.ipc"
_MANIFEST = "manifest.json"
# Plain-text ordering note, as EasyEDA ships one with its Gerber exports.
_ORDER_NOTES = "ORDER_NOTES.txt"
# EasyEDA Pro writes one stiffener layer per side, material and thickness,
# e.g. Gerber_BottomStiffenerLayer_pib_0.2.GBSL.  Only bottom stiffeners
# (opposite the top-copper contacts) and the materials whose orderable
# thicknesses the profile lists (engine.profile) are supported.
_STIFFENER_SIDES = {"bottom": ("Bottom", "b", "GBSL")}
_STIFFENER_MATERIALS = {"polyimide": "pi"}
_NET_STEMS = {"rows": "ROW", "columns": "COL"}
# Netlist reference designators: the tail contacts, and each electrode's far end.
_CONTACT_REFDES = "J1"
_PINOUT_COLUMNS = ("pin", "net", "role", "logical_index", "contact_center_x_mm", "contact_center_y_mm", "physical_side")
# Route pieces of layout v3: each net has a wide tail piece and a thin fan-out piece.
_ROUTE_SEGMENTS = ("tail", "fanout")
# Board-manifest fields repeated for each Gerber ZIP in the review manifest.
_REPORT_KEYS = (
    "board_id", "physical_side", "role", "status", "production_ready", "easyeda_native_export",
    "requires_final_jlc_review", "stiffeners", "netlist", "geometry_counts",
)
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_MILS_PER_MM = 39.37007874015748
# Format limits and drawing conventions (not design rules): FSLAX46Y46 holds
# 4 integer digits, the read-back allows two least-significant digits
# (D17), the outline is drawn with a 0.1 mm line, region-only layers
# select a tiny aperture for conservative RS-274X readers, and the order
# notes wrap at 78 columns (a file name longer than that stays whole, on a
# line of its own).
_MAX_COORDINATE_MM = 10_000.0
_READBACK_TOLERANCE_MM = 2e-6
_OUTLINE_APERTURE_MM = 0.1
_REGION_APERTURE_MM = 0.01
_THICKNESS_MATCH_MM = 1e-9
_NOTE_COLUMNS = 78
_BOARD_ID = re.compile(r"[a-z0-9][a-z0-9_]{0,31}\Z")
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_CHANNEL_NET = re.compile(r"(ROW|COL)_([0-9]{2,})\Z")
_NC_NET = re.compile(r"NC_([0-9]{2,})\Z")
# A masked board's merged field window is a ring (layout v3 ``shape: "polygon"``) without the
# rectangle fields; its vertices lie on the 1e-6 mm layout grid up to float noise.
_POLYGON_SHAPE = "polygon"
_RECT_FIELDS = ("anchor", "x", "y", "width_mm", "height_mm")
_GRID_NOISE_MM = 1e-9
# The review bundle's taxel map of a masked build: every R x C readout position, ROW-major.
_TAXELS = "taxels.csv"
_TAXEL_COLUMNS = ("row", "column", "row_net", "column_net", "row_pin", "column_pin", "active")


class ExportError(ValueError):
    """Raised when an unvalidated or malformed geometry is sent to export."""


def build_exports(result: Mapping[str, Any], *, cache: BuildCache | None = None) -> dict[str, bytes]:
    """Build independent direct-Gerber candidate ZIPs and a review bundle.

    The keys are stable (:data:`ARTIFACT_KEYS`); :func:`artifact_filenames`
    gives the download name of each:

    ``top_fpc_gerber_zip``
        Gerber ZIP for the independently manufactured FPC physically placed on
        top of the sensor stack.
    ``bottom_fpc_gerber_zip``
        Gerber ZIP for the independently manufactured FPC physically placed on
        the bottom of the sensor stack.
    ``project_review_bundle_zip``
        Audit material: canonical input, profile, validation report, derived
        geometry, pinout, order notes, export manifest, separate top/bottom
        SVG previews and both Gerber ZIPs.

    The Gerber ZIPs contain ``GTL``, ``GTS``, ``GKO``, one stiffener layer per
    side, material and thickness, ``jlcpcb.json``, an IPC-D-356A
    ``netlist.ipc``, ``ORDER_NOTES.txt`` (the profile's JLCPCB order options
    with their reasons) and a ``manifest.json``.  Members are stored
    uncompressed with fixed timestamps.  They are explicitly Direct Gerber /
    JLC review candidates; no return value represents an EasyEDA-native or
    production-ready artifact.

    The boards are regenerated from the result's design and profile and must
    equal the result's; ``cache`` (the engine :class:`~engine.BuildCache` the
    result was generated with) lets that regeneration reuse the engine's own
    boards of the build, as the server and the CLI do.

    A masked taxel field (``matrix.mask``) exports like any build: its
    polygon field window is one GTS region (read back against the ring), its
    order notes state the taxel field, and its review bundle adds
    ``taxels.csv`` (every R x C position with its nets, pins and whether it
    is active) and the review manifest's ``taxel_map``.  Unmasked archives
    do not change.

    A diagonal Row bus (``routing.row_sides``, construction
    ``diagonal-bus/7``) exports the same way.  Its folded Row contact order
    is on the pads, so ``pinout.csv``, ``netlist.ipc`` and ``taxels.csv``
    give each row the pin of its contact; its boards carry the masked
    records, so its bundle always has ``taxels.csv`` (every position active
    without a mask, and then no taxel-field line in the order notes); and
    the review manifest's ``diagonal_row_bus`` records the Row board's
    ``construction.row_bus`` (its tails ``stacked``, the level down to which
    both boards share one outline), its ``tail.row_contact_order`` with the
    pins of those contacts, read back against ``pinout.csv``, and the Column
    board (the straight one's copper, its tail centred).  Archives of the
    straight Row channel do not change.
    """

    try:
        return _build_exports(result, cache)
    except ExportError:
        raise
    except Exception as error:  # nothing, malformed input included, escapes as another exception type
        raise ExportError(f"Direct Gerber export failed (internal error or malformed input; {type(error).__name__}: {error}).") from error


def artifact_filenames(result: Mapping[str, Any]) -> dict[str, str]:
    """Download names keyed like :func:`build_exports` (D17).

    ``{build_id}-{side}-{role}-direct-gerber.zip`` for each board and
    ``{build_id}-project-review.zip``; build ids are ASCII ``[a-z0-9-]``.
    The review manifest records exactly these names.
    """

    try:
        build_id = result["manifest"]["build_id"]
        roles = {board["physical_side"]: board["role"] for board in result["boards"].values()}
    except (TypeError, KeyError, AttributeError) as error:
        raise ExportError("Artifact names need a generate_design result with a manifest and two boards.") from error
    if not isinstance(build_id, str) or not _SLUG.fullmatch(build_id) or len(build_id) > 100:
        raise ExportError("The result has no valid build id.")
    if set(roles) != {"top", "bottom"} or sorted(map(str, roles.values())) != ["columns", "rows"]:
        raise ExportError("Artifact names need one top and one bottom board, one rows and one columns.")
    names = {f"{side}_fpc_gerber_zip": f"{build_id}-{side}-{roles[side]}-direct-gerber.zip" for side in ("top", "bottom")}
    names["project_review_bundle_zip"] = f"{build_id}-project-review.zip"
    return names


def _build_exports(result: Any, cache: BuildCache | None) -> dict[str, bytes]:
    build = _checked_build(result, cache)
    names = build["artifact_names"] = artifact_filenames(result)
    zips: dict[str, bytes] = {}
    reports: dict[str, dict[str, Any]] = {}
    for side in ("top", "bottom"):
        board = build["boards_by_side"][side]
        groups = build["stiffener_groups"][side] = _stiffener_groups(board, build["profile"])
        files, board_manifest = _board_files(board, groups, build)
        _verify_board_files(board, files, groups, build)
        data = _deterministic_zip(files)
        _verify_zip(data, files)
        key = f"{side}_fpc_gerber_zip"
        zips[key] = data
        reports[key] = {
            "filename": names[key],
            "sha256": _sha256(data),
            "bytes": len(data),
            **{name: board_manifest[name] for name in _REPORT_KEYS},
            "files": _file_digests(files),
        }
    bundle = _review_bundle(build, names, zips, reports)
    return {**zips, "project_review_bundle_zip": bundle}


# --------------------------------------------------------------------------
# Input checks: a valid, self-consistent build with well-formed boards.
# --------------------------------------------------------------------------


def _checked_build(result: Any, cache: BuildCache | None) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise ExportError("Direct Gerber export requires a generate_design result object.")
    if result.get("ok") is not True:
        raise ExportError("Direct Gerber export is blocked because design validation did not pass.")
    parts = {key: result.get(key) for key in ("design", "manifest", "boards", "profile", "validation")}
    if not all(isinstance(part, Mapping) for part in parts.values()):
        raise ExportError("Result is missing its canonical design, manifest, profile, validation or board geometry.")
    design, manifest, board_map, profile, validation = parts.values()
    if manifest.get("geometry_valid") is not True:
        raise ExportError("Direct Gerber export is blocked because geometry is not valid.")
    errors, warnings = validation.get("errors"), validation.get("warnings")
    if not isinstance(errors, list) or not isinstance(warnings, list) or not all(map(_is_issue, warnings)):
        raise ExportError("Result validation must hold lists of errors and warnings.")
    if errors:
        raise ExportError("Direct Gerber export is blocked because the result carries validation errors.")
    if not isinstance(validation.get("normalization", {}), Mapping):
        raise ExportError("Result validation.normalization must be an object.")
    issues = profile_issues(profile)
    if issues:
        details = "; ".join(f"{issue['field']}: {issue['message']}" for issue in issues[:3])
        raise ExportError(f"The result's manufacturing profile is inconsistent: {details}")
    texts = {name: _json_text(part, f"Result {name}") for name, part in parts.items() if name != "boards"}
    _check_identity(texts["design"], texts["profile"], profile, manifest)
    checks = manifest.get("checks")
    design_warnings = [issue for issue in warnings if issue["code"] not in REQUEST_WARNING_CODES]
    if not isinstance(checks, Mapping) or checks.get("error_count") != 0 or checks.get("warning_count") != len(design_warnings):
        raise ExportError("Result manifest checks do not match its validation (error and design-warning counts).")

    if set(board_map) != {"row", "column"}:
        raise ExportError("Exactly two independently manufacturable FPC boards (row, column) are required.")
    boards = [board_map["row"], board_map["column"]]
    if not all(isinstance(board, Mapping) for board in boards):
        raise ExportError("Board geometry must be objects.")
    for board in boards:
        _check_board(board, profile)
    if [board["role"] for board in boards] != ["rows", "columns"]:
        raise ExportError("Boards must contain one rows FPC (row) and one columns FPC (column).")
    if {board["physical_side"] for board in boards} != {"top", "bottom"}:
        raise ExportError("Boards must have one top and one bottom physical-stack assignment.")
    if len({board["id"] for board in boards}) != 2:
        raise ExportError("Board ids must be distinct.")
    derived = result.get("derived_layout")
    layout = _json_text({"format": LAYOUT_FORMAT, "units": "mm", "boards": dict(board_map)}, "Result boards")
    if derived is not None and _json_text(derived, "Result derived_layout") != layout:
        raise ExportError("Result derived_layout does not match its boards.")
    regenerated = _regenerated_boards(texts["design"], texts["profile"], manifest, validation, board_map, cache)
    return {
        "design": design,
        "design_json": texts["design"],
        "profile_json": texts["profile"],
        "manifest": manifest,
        "profile": profile,
        "validation": validation,
        "layout_json": _json_text({"format": LAYOUT_FORMAT, "units": "mm", "boards": regenerated}, "Regenerated boards"),
        "boards_by_side": {board["physical_side"]: board for board in regenerated.values()},
        "drc_version": str(regenerated["row"]["verification"]["drc_version"]),
        "stiffener_groups": {},
        "order_requirements": order_requirements(profile, default_design()),
        # The taxel map's row spans in net indices (None: a straight Row channel without a mask, no taxel map).
        "taxel_mask": _taxel_spans(design),
    }


def _taxel_spans(design: Mapping[str, Any]) -> tuple[tuple[int, int], ...] | None:
    """The row spans of a build's taxel map (``taxels.csv``): the field mask's, or the full field's for a
    diagonal Row bus without a mask, whose boards carry the masked records (engine.diagonal); else None."""

    mask = design_mask(design)
    if mask is None and row_bus(design):
        return ((1, int(design["matrix"]["columns"])),) * int(design["matrix"]["rows"])
    return mask


def _check_identity(design_json: str, profile_json: str, profile: Mapping[str, Any], manifest: Mapping[str, Any]) -> None:
    """The manifest identity must describe this design, profile, generator and exporter (D14)."""

    design_sha256 = _sha256(design_json.encode("utf-8"))
    profile_sha256 = _sha256(profile_json.encode("utf-8"))
    # The boards are regenerated by this engine, so the build must name its generator.
    generator = engine_core.GENERATOR_VERSION
    expected = {
        "design_sha256": design_sha256, "profile_sha256": profile_sha256, "generator": generator,
        "exporter": EXPORTER_VERSION, "layout_format": LAYOUT_FORMAT,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ExportError(f"Result manifest {key} does not match the result (expected {value}).")
    identity = {"design_sha256": design_sha256, "profile_sha256": profile_sha256, "generator": generator, "exporter": EXPORTER_VERSION}
    # A template other than the generic one adds its version, a field mask its own (engine.core.template_identity).
    identity.update(engine_core.template_identity(json.loads(design_json)))
    build_sha256 = _sha256(_canonical_json(identity).encode("utf-8"))
    slug = manifest.get("slug")
    if manifest.get("build_sha256") != build_sha256 or not isinstance(slug, str) or not _SLUG.fullmatch(slug) or len(slug) > 64:
        raise ExportError("Result manifest build_sha256 or slug does not match the build identity.")
    if manifest.get("build_id") != f"{slug}-{build_sha256[:12]}":
        raise ExportError("Result manifest build_id does not match the build identity.")
    if manifest.get("profile") != {"id": profile.get("id"), "revision": profile.get("revision")}:
        raise ExportError("Result manifest profile id/revision does not match the profile.")


def _check_board(board: Mapping[str, Any], profile: Mapping[str, Any]) -> None:
    required = ("id", "role", "physical_side", "units", "outline", "layers", "tail", "grid_registration", "verification", "svg")
    missing = [key for key in required if key not in board]
    if missing:
        raise ExportError(f"Board geometry is incomplete (missing {', '.join(missing)}).")
    board_id = board["id"]
    if not isinstance(board_id, str) or not _BOARD_ID.fullmatch(board_id):
        raise ExportError("Board id must be a short lowercase ASCII identifier ([a-z0-9_]).")
    if not _member(board["role"], _NET_STEMS) or not _member(board["physical_side"], ("top", "bottom")):
        raise ExportError(f"{board_id}: role must be rows or columns and physical_side top or bottom.")
    if board["units"] != "mm" or not isinstance(board["svg"], str) or not isinstance(board["verification"], Mapping):
        raise ExportError(f"{board_id}: units must be mm, with an SVG preview and a verification record.")
    outline, layers = board["outline"], board["layers"]
    if not isinstance(outline, Mapping) or not isinstance(layers, Mapping):
        raise ExportError(f"{board_id}: outline and layers must be objects.")
    _check_ring(outline.get("points"), f"{board_id} outline")
    cutouts = outline.get("cutouts", [])
    if not isinstance(cutouts, list):
        raise ExportError(f"{board_id}: routed cutouts must be a list.")
    for index, cutout in enumerate(cutouts, start=1):
        _check_ring(cutout, f"{board_id} routed cutout {index}")
    copper = layers.get("top_copper")
    openings = layers.get("top_coverlay_openings")
    stiffeners = layers.get("bottom_stiffener")
    if not isinstance(copper, Mapping) or not isinstance(openings, list) or not isinstance(stiffeners, list):
        raise ExportError(f"{board_id}: top copper, coverlay openings and stiffeners are required.")
    if not all(isinstance(copper.get(key), list) and copper[key] for key in ("electrodes", "routes", "pads")):
        raise ExportError(f"{board_id}: a sensor FPC needs electrodes, routes and connector pads.")
    if not openings or not stiffeners:
        raise ExportError(f"{board_id}: a sensor FPC needs coverlay openings and at least one stiffener.")
    for rect in [*copper["electrodes"], *copper["pads"], *_rect_openings(openings, board)]:
        _check_rect(rect, f"{board_id} copper/coverlay rectangle")
    stem = _NET_STEMS[board["role"]]
    pins = []
    for pad in copper["pads"]:
        pin, net, kind = pad.get("pin"), pad.get("net"), pad.get("kind")
        if not _is_count(pin):
            raise ExportError(f"{board_id}: connector pins must be positive integers.")
        expected = _channel_index(net, stem) is not None if kind == "connector_pad" else kind == "connector_nc_pad" and _nc_pin(net) == pin
        if not expected:
            raise ExportError(f"{board_id}: contact pin {pin} needs a {stem}_<n> net or, unused, NC_<pin> (got {net!r}).")
        pins.append(pin)
    if sorted(pins) != list(range(1, len(pins) + 1)):
        raise ExportError(f"{board_id}: connector pins must be 1..{len(pins)}, each used once.")
    for electrode in copper["electrodes"]:
        if _channel_index(electrode.get("net"), stem) is None:
            raise ExportError(f"{board_id}: electrode nets must be {stem}_<n>.")
    # The minimum of the profile's copper (1 oz: 4 mil, 0.1016 mm).
    minimum_trace = fabrication_minimum(profile)[0]
    for route in copper["routes"]:
        if not isinstance(route, Mapping) or _channel_index(route.get("net"), stem) is None:
            raise ExportError(f"{board_id}: routes must be objects on {stem}_<n> nets.")
        if not _member(route.get("segment"), _ROUTE_SEGMENTS):
            raise ExportError(f"{board_id}: route {route['net']} must be a {' or '.join(_ROUTE_SEGMENTS)} piece (layout v3 segment).")
        width = route.get("width_mm")
        if not _finite(width) or float(width) < minimum_trace:
            raise ExportError(f"{board_id}: route width must be at least the fabrication minimum {minimum_trace:g} mm of the profile's copper.")
        _check_points(route.get("points"), 2, f"{board_id} route {route['net']}")
    for opening in openings:
        nets = opening.get("nets")
        if not isinstance(opening.get("kind"), str) or not isinstance(nets, list) or not all(isinstance(net, str) for net in nets):
            raise ExportError(f"{board_id}: coverlay openings need a kind and a list of nets.")
    for stiffener in stiffeners:
        _check_stiffener(stiffener, profile, board_id)


def _check_stiffener(stiffener: Any, profile: Mapping[str, Any], board_id: str) -> None:
    """Side, material and thickness come from each stiffener object (D10)."""

    if not isinstance(stiffener, Mapping):
        raise ExportError(f"{board_id}: stiffener geometry must be an object.")
    side, material, thickness = stiffener.get("side"), stiffener.get("material"), stiffener.get("thickness_mm")
    if not _member(side, _STIFFENER_SIDES):
        raise ExportError(
            f"{board_id}: stiffener side {side!r} is not exported; only bottom stiffeners (opposite the top-copper contacts) are supported."
        )
    if not _member(material, _STIFFENER_MATERIALS) or material not in STIFFENER_THICKNESS_OPTIONS:
        raise ExportError(f"{board_id}: stiffener material {material!r} is not supported; supported: {', '.join(_STIFFENER_MATERIALS)}.")
    if _thickness_option(material, thickness, profile) is None:
        key = STIFFENER_THICKNESS_OPTIONS[material]
        raise ExportError(
            f"{board_id}: stiffener thickness {thickness!r} mm is not a JLC {material} option "
            f"{profile['fabrication'][key]} (profile fabrication.{key})."
        )
    _check_ring(stiffener.get("points"), f"{board_id} stiffener")


def _check_rect(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise ExportError(f"{label} must be an object.")
    if not _member(value.get("anchor"), ANCHORS):
        raise ExportError(f"{label} has no supported anchor (center or lower_left).")
    for key in ("x", "y", "width_mm", "height_mm"):
        if not _finite(value.get(key)):
            raise ExportError(f"{label} has a non-finite {key}.")
    if not float(value["width_mm"]) > 0 or not float(value["height_mm"]) > 0:
        raise ExportError(f"{label} has non-positive dimensions.")
    _check_points(rect_corners(value), 4, label)
    if len({_gerber_point(point) for point in rect_corners(value)}) != 4:
        raise ExportError(f"{label} collapses below the 1e-6 mm Gerber resolution.")


def _check_ring(points: Any, label: str) -> None:
    """A simple polygon of at least three points without zero-length edges at Gerber resolution.

    Every ring becomes a region or a closed profile contour, which must not
    cross or touch itself (audit GERBER-12); the engine's DRC checks the
    outline and cutouts the same way, and this also covers stiffeners.
    """

    _check_points(points, 3, label)
    emitted = [_gerber_point(point) for point in points]
    if any(first == second for first, second in zip(emitted, emitted[1:] + emitted[:1])):
        raise ExportError(f"{label} has a zero-length edge at the 1e-6 mm Gerber resolution.")
    if not ring_is_simple([[float(x), float(y)] for x, y in points]):
        raise ExportError(f"{label} is not a simple polygon (it crosses, touches or folds back on itself).")


def _rect_openings(openings: Sequence[Any], board: Mapping[str, Any]) -> list[Any]:
    """The coverlay openings to check as rectangles; an opening with a ``shape`` is checked as a polygon here."""

    rectangles = []
    for opening in openings:
        if isinstance(opening, Mapping) and "shape" in opening:
            _check_polygon_opening(opening, board)
        else:
            rectangles.append(opening)
    return rectangles


def _check_polygon_opening(opening: Mapping[str, Any], board: Mapping[str, Any]) -> None:
    """A polygon coverlay opening is the field window of a masked board, written as one GTS region.

    It says ``shape: "polygon"``, is the board's merged
    ``electrode_field_opening`` on a board with a taxel mask
    (``grid_registration.taxel_mask``), carries no rectangle fields (a reader
    that knows only rectangles must fail instead of exposing another area),
    and its ``points`` are a simple, counter-clockwise, rectilinear ring of at
    least four vertices on the 1e-6 mm grid, given open (the region closes it).
    """

    label = f"{board['id']} polygon coverlay opening"
    if opening["shape"] != _POLYGON_SHAPE:
        raise ExportError(f"{label}: shape must be 'polygon' (a rectangle has none), not {opening['shape']!r}.")
    if opening.get("kind") != "electrode_field_opening":
        raise ExportError(f"{label}: only the merged field window (electrode_field_opening) may be a polygon, not {opening.get('kind')!r}.")
    registration = board["grid_registration"]
    if not isinstance(registration, Mapping) or "taxel_mask" not in registration:
        raise ExportError(f"{label}: a polygon field window belongs to a masked board (grid_registration.taxel_mask).")
    present = [key for key in _RECT_FIELDS if key in opening]
    if present:
        raise ExportError(f"{label} carries the rectangle fields {', '.join(present)}.")
    points = opening.get("points")
    _check_points(points, 4, label)
    _check_ring(points, label)
    if any(abs(float(value) - round(float(value), 6)) > _GRID_NOISE_MM for point in points for value in point):
        raise ExportError(f"{label} has a vertex off the 1e-6 mm layout grid.")
    # Exact integer arithmetic on the emitted 1e-6 mm coordinates.
    emitted = [_gerber_point(point) for point in points]
    twice_area = 0
    for index, first in enumerate(emitted):
        second = emitted[(index + 1) % len(emitted)]
        if first[0] != second[0] and first[1] != second[1]:
            raise ExportError(f"{label} edge {index + 1} is neither horizontal nor vertical (from {_xy(points[index])}).")
        twice_area += first[0] * second[1] - second[0] * first[1]
    if twice_area <= 0:
        raise ExportError(f"{label} is not counter-clockwise.")


def _check_points(points: Any, minimum: int, label: str) -> None:
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes)) or len(points) < minimum:
        raise ExportError(f"{label} must have at least {minimum} points.")
    for point in points:
        if not isinstance(point, Sequence) or isinstance(point, (str, bytes)) or len(point) != 2:
            raise ExportError(f"{label} has an invalid point.")
        if not all(_finite(value) and abs(float(value)) < _MAX_COORDINATE_MM for value in point):
            raise ExportError(f"{label} has a coordinate that is not finite or outside +/-{_MAX_COORDINATE_MM:g} mm (Gerber FS 4.6).")


def _regenerated_boards(
    design_json: str,
    profile_json: str,
    manifest: Mapping[str, Any],
    validation: Mapping[str, Any],
    board_map: Mapping[str, Any],
    cache: BuildCache | None,
) -> dict[str, Any]:
    """Regenerate the boards from the result's canonical design and profile.

    Generation runs the whole-board DRC again, and the result must be exactly
    what the engine gives: its manifest, design warnings and both boards
    (geometry, DRC records, previews, metrics).  A substituted, re-assigned
    or edited board, or a stale or edited DRC record, is refused with the
    path of its first difference, so the geometry written is the geometry of
    the build identity it carries.  A build cache returns the engine's own
    earlier generation of the same identity.  Returns the regenerated boards.
    """

    try:
        fresh = generate_design(json.loads(design_json), profile=json.loads(profile_json), cache=cache)
    except Exception as error:
        raise ExportError(f"The engine could not regenerate the result's design ({type(error).__name__}: {error}).") from error
    errors = fresh["validation"]["errors"]
    if not fresh["ok"]:
        first = errors[0]
        raise ExportError(
            f"Regenerating the result's design fails validation ({len(errors)} error(s)); "
            f"first {first['code']} at {first['field']}: {first['message']}"
        )
    if _canonical_json(fresh["design"]) != design_json:
        raise ExportError("Result design is not the canonical design (the engine normalizes it differently).")
    difference = _first_difference(manifest, fresh["manifest"])
    if difference is not None:
        raise ExportError(f"Result manifest{difference} does not match the build regenerated from its design and profile.")
    given, expected = (
        [issue for issue in warnings if issue["code"] not in REQUEST_WARNING_CODES]
        for warnings in (validation["warnings"], fresh["validation"]["warnings"])
    )
    if _canonical_json(given) != _canonical_json(expected):
        raise ExportError("Result validation warnings are not the design warnings the engine reports for its design.")
    for name in ("row", "column"):
        difference = _first_difference(board_map[name], fresh["boards"][name])
        if difference is None:
            continue
        if difference.startswith(".verification"):
            board_id = fresh["boards"][name]["id"]
            raise ExportError(f"The DRC record of {board_id} does not match a fresh check of its geometry (boards.{name}{difference}).")
        raise ExportError(
            f"Result boards.{name}{difference} does not match the geometry the engine generates for its design and profile."
        )
    return fresh["boards"]


def _first_difference(given: Any, expected: Any) -> str | None:
    """JSON path of the first difference (``None`` if canonically equal), with both values at a leaf."""

    if _canonical_json(given) == _canonical_json(expected):
        return None
    given, expected = json.loads(_canonical_json(given)), json.loads(_canonical_json(expected))
    path = ""
    while True:
        if isinstance(given, dict) and isinstance(expected, dict):
            key = next(
                key for key in sorted(set(given) | set(expected))
                if key not in given or key not in expected or _canonical_json(given[key]) != _canonical_json(expected[key])
            )
            path += f".{key}"
            if key not in given or key not in expected:
                return path + (" (missing)" if key not in given else " (unexpected)")
            given, expected = given[key], expected[key]
        elif isinstance(given, list) and isinstance(expected, list) and len(given) == len(expected):
            index = next(index for index, pair in enumerate(zip(given, expected)) if _canonical_json(pair[0]) != _canonical_json(pair[1]))
            path += f"[{index}]"
            given, expected = given[index], expected[index]
        elif isinstance(given, (dict, list, str)) or isinstance(expected, (dict, list, str)):
            return path
        else:
            return f"{path} ({_canonical_json(given)}, expected {_canonical_json(expected)})"


# --------------------------------------------------------------------------
# Board ZIP members.
# --------------------------------------------------------------------------


def _board_files(
    board: Mapping[str, Any], groups: Sequence[Mapping[str, Any]], build: Mapping[str, Any]
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """The members of a board ZIP and its manifest.json content."""

    build_id = build["manifest"]["build_id"]
    files = {
        _GTL: _top_copper_gerber(board, build_id),
        _GTS: _coverlay_gerber(board, build_id),
        _GKO: _outline_gerber(board, build_id),
    }
    for group in groups:
        files[group["gerber"]] = _stiffener_gerber(board, group, build_id)
    files[_JLC_METADATA] = _canonical_json(_jlcpcb_metadata(board, groups)).encode("utf-8") + b"\n"
    files[_NETLIST] = _netlist(board, build_id).encode("ascii")
    files[_ORDER_NOTES] = _order_notes(build, [(board, groups)])
    manifest = _board_manifest(board, files, groups, build)
    files[_MANIFEST] = _canonical_json(manifest).encode("utf-8") + b"\n"
    return files, manifest


def _top_copper_gerber(board: Mapping[str, Any], build_id: str) -> bytes:
    copper = board["layers"]["top_copper"]
    routes = copper["routes"]
    # One aperture per emitted diameter: widths equal at 1e-6 mm share it.
    widths = sorted({_decimal(route["width_mm"]) for route in routes})
    aperture_codes = {width: 10 + index for index, width in enumerate(widths)}
    lines = _gerber_header("Copper,L1,Top", "Positive", f"{board['id']} top copper", build_id)
    lines.extend(f"%ADD{aperture_codes[width]}C,{width}*%" for width in widths)
    lines.append("G01*")
    for route in routes:
        lines.append(f"D{aperture_codes[_decimal(route['width_mm'])]}*")
        lines.extend(_stroke(route["points"]))
    # Every layout rectangle carries its anchor (pads ``center``, electrodes
    # and openings ``lower_left``); ``rect_corners`` is the one interpreter.
    for rectangle in [*copper["electrodes"], *copper["pads"]]:
        lines.extend(_region(rect_corners(rectangle)))
    return _gerber_text(lines)


def _coverlay_gerber(board: Mapping[str, Any], build_id: str) -> bytes:
    lines = _gerber_header("Soldermask,Top", "Negative", f"{board['id']} coverlay openings", build_id)
    # Select a small aperture even though the actual geometry is regions.
    # This keeps the file valid for conservative RS-274X readers which expect
    # a current aperture before any graphics command.
    lines.extend((f"%ADD10C,{_decimal(_REGION_APERTURE_MM)}*%", "G01*", "D10*"))
    # The GTS is declared negative: its filled regions are the intentional
    # coverlay clearances (sensor electrodes and connector contacts), not
    # copper or a fictional soldermask coating.
    if _has_polygon_opening(board):  # a masked board's field window
        return _gerber_text([*lines, *_masked_coverlay_regions(board["layers"]["top_coverlay_openings"])])
    for opening in board["layers"]["top_coverlay_openings"]:
        lines.extend(_region(rect_corners(opening)))
    return _gerber_text(lines)


def _has_polygon_opening(board: Mapping[str, Any]) -> bool:
    return any(opening.get("shape") == _POLYGON_SHAPE for opening in board["layers"]["top_coverlay_openings"])


def _masked_coverlay_regions(openings: Sequence[Mapping[str, Any]]) -> list[str]:
    """The GTS regions of a masked board, in layout order: the polygon field
    window as one region over its ring, every other opening over its
    anchored rectangle."""

    lines: list[str] = []
    for opening in openings:
        if opening.get("shape") == _POLYGON_SHAPE:
            ring = opening["points"]
        else:
            ring = rect_corners(opening)
        lines.extend(_region(ring))
    return lines


def _outline_gerber(board: Mapping[str, Any], build_id: str) -> bytes:
    lines = _gerber_header("Profile,NP", "Positive", f"{board['id']} closed board outline", build_id)
    lines.extend((f"%ADD10C,{_decimal(_OUTLINE_APERTURE_MM)}*%", "G01*", "D10*"))
    for points in _outline_contours(board):
        lines.extend(_stroke([*points, points[0]]))
    return _gerber_text(lines)


def _stiffener_gerber(board: Mapping[str, Any], group: Mapping[str, Any], build_id: str) -> bytes:
    description = f"{board['id']} {group['side']} {group['material']} stiffener {group['thickness']} mm"
    lines = _gerber_header(f"Other,{group['side_name']}Stiffener", "Positive", description, build_id)
    lines.extend((f"%ADD10C,{_decimal(_REGION_APERTURE_MM)}*%", "G01*", "D10*"))
    for index in group["indices"]:
        lines.extend(_region(board["layers"]["bottom_stiffener"][index]["points"]))
    return _gerber_text(lines)


def _gerber_header(file_function: str, polarity: str, description: str, build_id: str) -> list[str]:
    # X2 attributes in comment form (L9).  SameCoordinates carries the build id
    # (D17); its scope is one board ZIP, a fabrication data set of its own:
    # the two boards of a build share the identifier, not a coordinate frame.
    return [
        f"G04 Direct Gerber JLC review candidate: {description}*",
        f"G04 #@! TF.GenerationSoftware,TactileFPC,direct-gerber,{_version_number()}*",
        f"G04 #@! TF.SameCoordinates,{build_id}*",
        f"G04 #@! TF.FileFunction,{file_function}*",
        f"G04 #@! TF.FilePolarity,{polarity}*",
        "%FSLAX46Y46*%",
        "%MOMM*%",
        "%LPD*%",
    ]


def _gerber_text(lines: list[str]) -> bytes:
    return ("\n".join([*lines, "M02*"]) + "\n").encode("ascii")


def _stroke(points: Sequence[Sequence[float]]) -> list[str]:
    start, *remaining = points
    lines = [f"{_xy(start)}D02*"]
    lines.extend(f"{_xy(point)}D01*" for point in remaining)
    return lines


def _region(points: Sequence[Sequence[float]]) -> list[str]:
    closed = [*points, points[0]]
    return ["G36*", *_stroke(closed), "G37*"]


def _outline_contours(board: Mapping[str, Any]) -> list[Sequence[Sequence[float]]]:
    return [board["outline"]["points"], *board["outline"].get("cutouts", [])]


def _stiffener_groups(board: Mapping[str, Any], profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Stiffeners grouped into one Gerber per side, material and thickness, in layout order.

    ``indices`` are the positions of a group's stiffeners in the board's list.
    """

    groups: dict[str, dict[str, Any]] = {}
    for index, stiffener in enumerate(board["layers"]["bottom_stiffener"]):
        side, material = stiffener["side"], stiffener["material"]
        side_name, side_code, extension = _STIFFENER_SIDES[side]
        code = _STIFFENER_MATERIALS[material]
        thickness = _thickness_option(material, stiffener["thickness_mm"], profile)
        name = f"Gerber_{side_name}StiffenerLayer_{code}{side_code}_{thickness}.{extension}"
        group = groups.setdefault(
            name,
            {"gerber": name, "side": side, "side_name": side_name, "material": material, "code": code, "thickness": thickness, "indices": []},
        )
        group["indices"].append(index)
    return list(groups.values())


def _group_of(groups: Sequence[Mapping[str, Any]]) -> dict[int, Mapping[str, Any]]:
    return {index: group for group in groups for index in group["indices"]}


def _thickness_option(material: str, thickness: Any, profile: Mapping[str, Any]) -> str | None:
    """The profile's orderable thickness matching ``thickness``, as file-name text ("0.225")."""

    options = profile["fabrication"].get(STIFFENER_THICKNESS_OPTIONS[material])
    if not _finite(thickness) or not isinstance(options, list):
        return None
    for option in options:
        if _finite(option) and abs(float(thickness) - float(option)) <= _THICKNESS_MATCH_MM:
            return f"{float(option):.6f}".rstrip("0").rstrip(".")
    return None


def _jlcpcb_metadata(board: Mapping[str, Any], groups: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    group_of = _group_of(groups)
    stiffeners = []
    for index, stiffener in enumerate(board["layers"]["bottom_stiffener"], start=1):
        group = group_of[index - 1]
        points = stiffener["points"]
        flattened: list[Any] = []
        for point in [*points, points[0]]:
            flattened.extend((_mil(point[0]), _mil(point[1])))
        # The JLC FPC metadata path form is a sequence containing one linear
        # path: x0, y0, "L", x1, y1, ... .  Coordinates are mils while the
        # Gerber itself remains in millimetres, matching JLC's existing schema.
        path = [flattened[:2] + ["L"] + flattened[2:]]
        stiffeners.append(
            {
                "id": f"direct_{group['code']}_{index:02d}",
                "gerber": group["gerber"],
                "layer": group["side"],
                "material": group["code"],
                "thickness": group["thickness"],
                "path": [path],
            }
        )
    return {"fpcStiffeners": stiffeners}


def _netlist(board: Mapping[str, Any], build_id: str) -> str:
    comments = (
        f"IPC-D-356A netlist, {board['physical_side']} {board['role']} FPC, TactileFPC direct-gerber {_version_number()}",
        f"Build {build_id}",
        "Millimetres in the Gerber frame. J1-<pin>: tail contact (pin as on the pad);",
        "ROW-<n> / COL-<n>: square land at the far end of electrode n.",
    )
    parameters = (("JOB", build_id), ("TITLE", board["id"]), ("UNITS", NETLIST_UNITS), ("VER", "IPC-D-356A"), ("IMAGE", "PRIMARY"))
    try:
        return netlist_text(comments, parameters, _test_points(board))
    except ValueError as error:
        raise ExportError(f"{board['id']} {_NETLIST}: {error}") from error


def _test_points(board: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One SMD test point per contact (its pin as on the pad; NC contacts are
    their own nets) and one at the far end of each electrode, so a probe pair
    per net tests continuity from contact to electrode end."""

    copper = board["layers"]["top_copper"]
    stem = _NET_STEMS[board["role"]]
    points = []
    for pad in sorted(copper["pads"], key=lambda pad: pad["pin"]):
        x0, y0, x1, y1 = rect_bounds(pad)
        center = ((x0 + x1) / 2, (y0 + y1) / 2)
        points.append(_test_point(pad["net"], _CONTACT_REFDES, pad["pin"], center, x1 - x0, y1 - y0))
    # Where each net's fan-out piece meets its electrode (not the tail-piece junction).
    junction = {route["net"]: route["points"][-1] for route in copper["routes"] if route["segment"] == "fanout"}
    for electrode in sorted(copper["electrodes"], key=lambda electrode: _channel_index(electrode["net"], stem)):
        x0, y0, x1, y1 = rect_bounds(electrode)
        size = min(x1 - x0, y1 - y0)
        end = junction[electrode["net"]]
        # A square land of the strip width at the end away from the route.
        if x1 - x0 >= y1 - y0:
            near_low = abs(end[0] - x0) <= abs(end[0] - x1)
            center = (x1 - size / 2 if near_low else x0 + size / 2, (y0 + y1) / 2)
        else:
            near_low = abs(end[1] - y0) <= abs(end[1] - y1)
            center = ((x0 + x1) / 2, y1 - size / 2 if near_low else y0 + size / 2)
        points.append(_test_point(electrode["net"], stem, _channel_index(electrode["net"], stem), center, size, size))
    return points


def _test_point(net: str, refdes: str, pin: Any, center: Sequence[float], width: float, height: float) -> dict[str, Any]:
    return {"net": net, "refdes": refdes, "pin": pin, "x": center[0], "y": center[1], "width": width, "height": height}


def _board_manifest(
    board: Mapping[str, Any], files: Mapping[str, bytes], groups: Sequence[Mapping[str, Any]], build: Mapping[str, Any]
) -> dict[str, Any]:
    manifest = build["manifest"]
    copper = board["layers"]["top_copper"]
    return {
        "format": BOARD_MANIFEST_FORMAT,
        **_identity_fields(manifest),
        "board_id": board["id"],
        "physical_side": board["physical_side"],
        "role": board["role"],
        "units": "mm",
        "status": _DIRECT_STATUS,
        "production_ready": False,
        "easyeda_native_export": False,
        "requires_final_jlc_review": True,
        "files": _file_digests(files),
        "stiffeners": [
            {
                "gerber": group["gerber"],
                "side": group["side"],
                "material": group["material"],
                "thickness_mm": float(group["thickness"]),
                "count": len(group["indices"]),
            }
            for group in groups
        ],
        "netlist": {
            "file": _NETLIST,
            "format": "IPC-D-356A",
            "units": NETLIST_UNITS,
            "nets": len({pad["net"] for pad in copper["pads"]}),
            "test_points": len(copper["pads"]) + len(copper["electrodes"]),
        },
        "geometry_counts": {
            "outline_vertices": len(board["outline"]["points"]),
            "routed_cutouts": len(board["outline"].get("cutouts", [])),
            "electrodes": len(copper["electrodes"]),
            "routes": len(copper["routes"]),
            "connector_pads": len(copper["pads"]),
            "coverlay_openings": len(board["layers"]["top_coverlay_openings"]),
            "stiffeners": len(board["layers"]["bottom_stiffener"]),
        },
        "order_notes": _ORDER_NOTES,
        "order_requirements": _order_records(build),
    }


def _order_records(build: Mapping[str, Any]) -> list[dict[str, Any]]:
    return json.loads(_canonical_json(build["order_requirements"]))


def _upload_checks(groups: Sequence[Mapping[str, Any]]) -> list[str]:
    """What to verify in the JLCPCB upload of boards with these stiffener groups."""

    return [
        "Verify the independent board outline after JLCPCB upload.",
        "Verify all top-coverlay openings after JLCPCB upload.",
        *(
            f"Verify each {group['code'].upper()} stiffener in {gerber} is detected at {group['thickness']} mm after JLCPCB upload."
            for gerber, group in sorted({group["gerber"]: group for group in groups}.items())
        ),
    ]


def _order_notes(build: Mapping[str, Any], boards: Sequence[tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]]) -> bytes:
    """ORDER_NOTES.txt: the JLCPCB order options of the profile and why, for these boards.

    Plain UTF-8 text with LF line ends, like the ordering note EasyEDA puts
    in its Gerber exports; every figure comes from the order requirements,
    the boards and their stiffener groups.
    """

    manifest, profile, names = build["manifest"], build["profile"], build["artifact_names"]
    records = build["order_requirements"]
    lines = ["TactileFPC order notes", "", f"Build: {manifest['build_id']}", f"Profile: {profile['id']}, revision {profile['revision']}"]
    lines.extend(_taxel_field_notes(boards))
    for board, groups in boards:
        tail = board["tail"]
        lines.append("")
        lines.extend(_note(
            f"Board {board['id']}: {board['role']} FPC, {board['physical_side']} of the stack; "
            f"{tail['connector_pins']} contacts at {tail['connector_pitch_mm']:g} mm pitch; tail {tail['width_mm']:g} mm wide, "
            f"{tail['length_mm']:g} mm long ({tail['side']} side); {_trace_widths(board)}.",
        ))
        fanout = next(route["width_mm"] for route in board["layers"]["top_copper"]["routes"] if route["segment"] == "fanout")
        lines.extend(_note(_trace_tolerance(float(fanout), profile), "  ", "    "))
        lines.extend(_note(f"Archive: {names[board['physical_side'] + '_fpc_gerber_zip']}", "  ", "    "))
        for group in groups:
            lines.extend(_note(f"Stiffener layer: {group['gerber']} ({group['material']} {group['thickness']} mm, {group['side']} side)", "  ", "    "))
        lines.extend(_note(_coverlay_window_note(board, profile), "  ", "    "))
        for note in _row_contact_notes(board):
            lines.extend(_note(note, "  ", "    "))
    lines.append("")
    lines.extend(_note(
        "Direct Gerber / JLC review candidate, not an EasyEDA-native export and not production approval. Upload each "
        "board ZIP to JLCPCB on its own as a flexible PCB, set the order options below and review the upload before ordering."
    ))
    for kind, title in (("order_option", "Order options"), ("review_note", "Review notes")):
        lines.extend(("", title, "-" * len(title)))
        for record in records:
            if record["kind"] == kind:
                lines.extend(_note(f"{record['topic']}: {record['requirement']}.", "- ", "  "))
                lines.extend(_note(f"Why: {record['reason']}", "  ", "  "))
    lines.extend(("", "After the JLCPCB upload", "-" * len("After the JLCPCB upload")))
    for check in _upload_checks([group for _, groups in boards for group in groups]):
        lines.extend(_note(check, "- ", "  "))
    lines.extend(("", "Sources", "-" * len("Sources")))
    for key in _cited_sources(records):
        lines.extend(_note(f"{key}: {_source_text(profile, key)}", "- ", "  "))
    return ("\n".join(lines) + "\n").encode("utf-8")


# How the order notes name a board's coverlay windows (engine.layout's opening kinds).
_WINDOW_NAMES = {"electrode_field_opening": "electrode field", "sensor_electrode_opening": "electrode", "connector_contact_opening": "contacts"}


def _coverlay_window_note(board: Mapping[str, Any], profile: Mapping[str, Any]) -> str:
    """The ORDER_NOTES.txt line of a board's coverlay windows: each kind with its size (the per-electrode windows by
    their count and the largest), then those longer than JLC's general length of one opening
    (``coverlay.coverlay_opening_general_max_length_mm``), longest side by longest side."""

    limit = float(profile["coverlay"]["coverlay_opening_general_max_length_mm"])
    sizes: dict[str, list[tuple[float, float]]] = {}
    for opening in board["layers"]["top_coverlay_openings"]:
        if opening.get("shape") == _POLYGON_SHAPE:
            xs, ys = [point[0] for point in opening["points"]], [point[1] for point in opening["points"]]
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        else:
            x0, y0, x1, y1 = rect_bounds(opening)
        sizes.setdefault(opening["kind"], []).append((round(x1 - x0, 6), round(y1 - y0, 6)))
    windows, longer = [], []
    for kind, boxes in sizes.items():
        name = _WINDOW_NAMES.get(kind, kind.replace("_", " "))
        width, height = max(boxes, key=lambda box: (max(box), box))
        size = f"{width:g} x {height:g} mm"
        windows.append(f"{name} {size}" if len(boxes) == 1 else f"{len(boxes)} {name} windows up to {size}")
        over = [max(box) for box in boxes if max(box) > limit + _READBACK_TOLERANCE_MM]
        if over:
            longest = f"{max(over):g} mm"
            longer.append(f"the {name} window ({longest})" if len(boxes) == 1 else f"{len(over)} {name} windows (up to {longest})")
    verdict = f"longer than JLC's general {limit:g} mm for one opening: {', '.join(longer)}" if longer else (
        f"none longer than JLC's general {limit:g} mm for one opening")
    return f"Coverlay windows: {', '.join(windows)}; {verdict}."


def _row_contact_notes(board: Mapping[str, Any]) -> list[str]:
    """The ORDER_NOTES.txt line of a diagonal Row bus's Row board: its folded contact order, pin by pin, from the pads
    (none for the straight Row channel, whose pin k carries ROW_k, nor for the Column board)."""

    order = board["tail"].get("row_contact_order")
    if order is None:
        return []
    contacts = sorted(board["layers"]["top_copper"]["pads"], key=lambda pad: pad["position"])[: len(order)]
    pins = ", ".join(f"pin {pad['pin']} {pad['net']}" for pad in contacts)
    return [
        f"Row pin order (diagonal Row bus, {_row_bus_fold(board)}): {pins}. Pin k carries ROW_k only where listed; pinout.csv, "
        "netlist.ipc and taxels.csv follow the pads."
    ]


def _row_bus_fold(board: Mapping[str, Any]) -> str:
    """How the order note names a diagonal Row bus's contact order: ``folded`` with both sides (the odd rows on one, the
    even ones back), ``one side`` with one (the rows in turn)."""

    return "folded" if board["construction"]["row_bus"]["sides"] == "both" else "one side"


def _taxel_field_notes(boards: Sequence[tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]]) -> list[str]:
    """The ORDER_NOTES.txt line of a masked build, from its boards' taxel mask (none for an unmasked build, nor
    for the full field a diagonal Row bus without a mask records)."""

    registration = boards[0][0]["grid_registration"]
    if "taxel_mask" not in registration:
        return []
    mask = registration["taxel_mask"]
    if registration["active_taxel_count"] == mask["rows"] * mask["columns"]:
        return []
    return _note(
        f"{_taxel_field(registration['active_taxel_count'], mask['rows'], mask['columns'])}: the electrodes, their "
        "coverlay windows and the outlines follow the mask; the other positions have no crossing and read 0."
    )


def _taxel_field_phrases(build: Mapping[str, Any]) -> list[str]:
    """What ORDER_NOTES.txt must state of a masked build, from its design's mask (nothing when unmasked, nor for
    the full field of a diagonal Row bus without a mask)."""

    mask = build["taxel_mask"]
    if mask is None:
        return []
    active = 0
    for first, last in mask:
        active += last - first + 1
    columns = int(build["design"]["matrix"]["columns"])
    if active == len(mask) * columns:
        return []
    return [_taxel_field(active, len(mask), columns)]


def _taxel_field(active: int, rows: int, columns: int) -> str:
    return f"Taxel field: {active} of {rows} x {columns} crossings (masked)"


def _trace_widths(board: Mapping[str, Any]) -> str:
    """The board's route widths as ORDER_NOTES.txt states them (from its route pieces)."""

    widths = {route["segment"]: route["width_mm"] for route in board["layers"]["top_copper"]["routes"]}
    space = round(board["construction"]["fanout_bundle_pitch_mm"] - widths["fanout"], 6)
    return f"fan-out traces {widths['fanout']:g} mm at {space:g} mm spacing, {widths['tail']:g} mm in the tail"


def _trace_tolerance(width: float, profile: Mapping[str, Any]) -> str:
    """What JLC's trace-width tolerance can make of fan-out traces ``width`` mm wide (ORDER_NOTES.txt)."""

    fraction = float(profile["fabrication"]["trace_width_tolerance_fraction"])
    minimum = round(fabrication_minimum(profile)[0], 6)
    narrowest = round(width * (1 - fraction), 6)
    text = f"Trace tolerance: at JLC's -{fraction * 100:g}% the {width:g} mm fan-out traces may come out {narrowest:g} mm wide"
    copper = f"JLC's {minimum:g} mm minimum for {copper_weight_oz(profile):g} oz copper"
    if narrowest < minimum:
        # The narrowest design width that still comes out at the minimum.
        return f"{text}, below {copper} (traces at least {ceil6(minimum / (1 - fraction)):g} mm wide stay at or above it)."
    return f"{text}, not below {copper}."


def _note(text: str, first: str = "", rest: str = "") -> list[str]:
    # A figure stays on one line with its unit.
    lines = textwrap.wrap(
        text.replace(" mm", "\0mm"), width=_NOTE_COLUMNS, initial_indent=first, subsequent_indent=rest,
        break_on_hyphens=False, break_long_words=False,
    )
    return [line.replace("\0", " ") for line in lines]


def _cited_sources(records: Sequence[Mapping[str, Any]]) -> list[str]:
    return list(dict.fromkeys(key for record in records for key in record["sources"]))


def _source_text(profile: Mapping[str, Any], key: str) -> str:
    """A cited source as text: a dotted key into the profile's sources block."""

    value: Any = profile["sources"]
    for part in key.split("."):
        value = value[part]
    if isinstance(value, Mapping):
        text = f"{value['url']} (fetched {value['fetched']})"
        return f"{text}; trace rules rechecked {value['trace_rules_rechecked']}" if "trace_rules_rechecked" in value else text
    return str(value)


def _identity_fields(manifest: Mapping[str, Any]) -> dict[str, Any]:
    keys = ("build_id", "build_sha256", "design_sha256", "profile_sha256", "generator", "exporter")
    # The identity extras (engine.core.template_identity: a template other than the generic one,
    # a field mask) are part of the hashed identity.
    extras = {key: manifest[key] for key in engine_core.IDENTITY_EXTRAS if key in manifest}
    return {**{key: manifest[key] for key in keys}, **extras, "profile": dict(manifest["profile"])}


def _build_hash_recipe(manifest: Mapping[str, Any]) -> str:
    extras = [key for key in engine_core.IDENTITY_EXTRAS if key in manifest]
    fields = ", ".join(["design_sha256", "profile_sha256", "generator", "exporter", *extras])
    return f"sha256 of the canonical JSON of {{{fields}}}"


# --------------------------------------------------------------------------
# Review bundle.
# --------------------------------------------------------------------------


def _review_bundle(build: Mapping[str, Any], names: Mapping[str, str], zips: Mapping[str, bytes], reports: Mapping[str, Any]) -> bytes:
    files = {
        "design.json": build["design_json"].encode("utf-8") + b"\n",
        "profile.json": build["profile_json"].encode("utf-8") + b"\n",
        "validation.json": _canonical_json(_validation_report(build)).encode("utf-8") + b"\n",
        "derived-layout.json": build["layout_json"].encode("utf-8") + b"\n",
        "pinout.csv": _pinout(build).encode("ascii"),
        "previews/top_fpc.svg": build["boards_by_side"]["top"]["svg"].encode("utf-8"),
        "previews/bottom_fpc.svg": build["boards_by_side"]["bottom"]["svg"].encode("utf-8"),
    }
    boards = [(build["boards_by_side"][side], build["stiffener_groups"][side]) for side in ("top", "bottom")]
    files[_ORDER_NOTES] = _order_notes(build, boards)
    files.update(_taxel_map_files(build))
    try:
        _check_order_notes(files[_ORDER_NOTES], build, boards)
        _check_taxel_map(files.get(_TAXELS), build)
        _check_row_contacts(files["pinout.csv"], build)
    except (ValueError, KeyError, UnicodeDecodeError) as error:
        raise ExportError(f"Read-back of the review bundle failed: {error}") from error
    for key, data in zips.items():
        files[f"gerbers/{names[key]}"] = data
    files[_MANIFEST] = _canonical_json(_review_manifest(build, names, reports, files)).encode("utf-8") + b"\n"
    data = _deterministic_zip(files)
    _verify_zip(data, files)
    return data


def _review_manifest(
    build: Mapping[str, Any], names: Mapping[str, str], reports: Mapping[str, Any], files: Mapping[str, bytes]
) -> dict[str, Any]:
    manifest = build["manifest"]
    records = build["order_requirements"]
    groups = [group for side_groups in build["stiffener_groups"].values() for group in side_groups]
    return {
        "format": EXPORT_MANIFEST_FORMAT,
        **_identity_fields(manifest),
        "layout_format": manifest["layout_format"],
        "deterministic": True,
        "source_independent": True,
        "runtime_source_inputs": ["engine.generate_design result"],
        "does_not_read": ["EasyEDA project", "KiCad board", "prior Gerber"],
        "status": _DIRECT_STATUS,
        "production_ready": False,
        "easyeda_native_export": False,
        "requires_final_jlc_review": True,
        "review_requirements": [
            *_upload_checks(groups),
            *(
                f"Set the JLCPCB order option '{record['topic']}' to {record['requirement']} for both boards ({_ORDER_NOTES})."
                for record in records if record["kind"] == "order_option"
            ),
            *(f"Check '{record['topic']}' on both boards: {record['requirement']} ({_ORDER_NOTES})." for record in records if record["kind"] == "review_note"),
        ],
        "order_notes": _ORDER_NOTES,
        "order_requirements": _order_records(build),
        "identity": {
            "canonical_json": "json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) as UTF-8",
            "design_sha256": "sha256 of the canonical JSON in design.json (the file adds one newline)",
            "profile_sha256": "sha256 of the canonical JSON in profile.json (the file adds one newline)",
            "build_sha256": _build_hash_recipe(manifest),
            "build_id": "slug + '-' + the first 12 hex digits of build_sha256",
            "gerber_same_coordinates": "TF.SameCoordinates is build_id; its scope is one board ZIP (the two boards have separate frames)",
        },
        "checks": {
            "error_count": 0,
            "warning_count": manifest["checks"]["warning_count"],
            "drc_version": build["drc_version"],
            "boards_equal_engine_generation": True,
            "files_read_back": True,
        },
        "export_verification": (
            "The exporter required the result's manifest, design warnings and boards (DRC records and previews included) "
            "to equal the engine's generation of design.json under profile.json, whole-board DRC included, then decoded "
            "every Gerber, jlcpcb.json and netlist.ipc it wrote and compared them with derived-layout.json, and checked "
            "each ORDER_NOTES.txt against order_requirements and the contact figures it states against the boards."
        ),
        "validation": {"file": "validation.json", "format": VALIDATION_FORMAT},
        "pinout": {
            "file": "pinout.csv",
            "columns": list(_PINOUT_COLUMNS),
            "frame": "each board's Gerber frame, mm, Y up; pins as on the contact pads (pin 1 marked in the previews)",
        },
        **_taxel_map_entry(build),
        **_row_bus_entry(build),
        "canonical_design": dict(build["design"]),
        "artifacts": {
            **{key: dict(reports[key]) for key in ARTIFACT_KEYS[:2]},
            "project_review_bundle_zip": {"filename": names["project_review_bundle_zip"]},
        },
        "bundle_files": _file_digests(files),
    }


def _taxel_map_files(build: Mapping[str, Any]) -> dict[str, bytes]:
    """``taxels.csv`` of a masked build (nothing for an unmasked one)."""

    return {} if build["taxel_mask"] is None else {_TAXELS: _taxels(build).encode("ascii")}


def _taxels(build: Mapping[str, Any]) -> str:
    """Every readout position of a masked build, ROW-major: its row and column
    index, the two nets, their contact pins, and ``active`` 1 where the
    design's mask puts a taxel (the electrodes cross), 0 where it does not
    (no crossing: the position always reads 0)."""

    contacts = {board["role"]: _contact_pins(board) for board in build["boards_by_side"].values()}
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(_TAXEL_COLUMNS)
    columns = int(build["design"]["matrix"]["columns"])
    for row, (first, last) in enumerate(build["taxel_mask"], start=1):
        row_net, row_pin = contacts["rows"][row]
        for column in range(1, columns + 1):
            column_net, column_pin = contacts["columns"][column]
            writer.writerow((row, column, row_net, column_net, row_pin, column_pin, 1 if first <= column <= last else 0))
    return stream.getvalue()


def _contact_pins(board: Mapping[str, Any]) -> dict[int, tuple[str, int]]:
    """``{logical index: (net, pin)}`` of a board's channel contacts."""

    stem = _NET_STEMS[board["role"]]
    pads = board["layers"]["top_copper"]["pads"]
    return {_channel_index(pad["net"], stem): (pad["net"], pad["pin"]) for pad in pads if pad["kind"] == "connector_pad"}


def _taxel_map_entry(build: Mapping[str, Any]) -> dict[str, Any]:
    """The review manifest's ``taxel_map`` of a masked build (nothing for an unmasked one)."""

    mask = build["taxel_mask"]
    if mask is None:
        return {}
    active = 0
    for first, last in mask:
        active += last - first + 1
    return {
        "taxel_map": {
            "file": _TAXELS,
            "columns": list(_TAXEL_COLUMNS),
            "active": active,
            "total": len(mask) * int(build["design"]["matrix"]["columns"]),
            "frame": (
                "the readout's ROW_r x COL_c positions, ROW-major, pins as on the contact pads; "
                "a position with active 0 has no electrode crossing and always reads 0"
            ),
        }
    }


def _row_bus_entry(build: Mapping[str, Any]) -> dict[str, Any]:
    """The review manifest's ``diagonal_row_bus`` of a diagonal Row bus build (nothing for the straight Row channel):
    the Row board's ``construction.row_bus``, its contact order (``tail.row_contact_order``) with the pins of those
    contacts, and the Column board's id."""

    boards = {board["role"]: board for board in build["boards_by_side"].values()}
    row, column = boards["rows"], boards["columns"]
    bus = row["construction"].get("row_bus")
    if bus is None:
        return {}
    order = list(row["tail"]["row_contact_order"])
    contacts = sorted(row["layers"]["top_copper"]["pads"], key=lambda pad: pad["position"])
    return {
        "diagonal_row_bus": {
            "kind": bus["kind"],
            "row_board": row["id"],
            "construction": json.loads(_canonical_json(bus)),
            "row_contact_order": order,
            "row_contact_pins": [pad["pin"] for pad in contacts[: len(order)]],
            "column_board": column["id"],
            "frame": (
                "row_contact_order: the Row nets at the Row tail's contact positions 1..N (position 1 at the left end of "
                "the contact row, copper side up with the tail down); row_contact_pins: the pins of those contacts, as on "
                "the pads and in pinout.csv; the order folds with both sides (ROW_01, ROW_03, ..., ROW_04, ROW_02), so "
                "pin k carries ROW_k only where the order puts it; construction.tails stacked: both tails leave on one side, "
                "the Row tail lying on the Column tail where they meet (the top board's over the bottom board's), the Column "
                "tail centred under its fan-out as on the straight Column board; they part to their own connectors; "
                "construction.shared_outline_below_field_mm: both boards have one outline in the stack (the top board turned "
                "over) from the tip down to this far below the taxel field, their tails' roots, so the films align by their "
                "edges; below it each board has only its own tail"
            ),
        }
    }


def _validation_report(build: Mapping[str, Any]) -> dict[str, Any]:
    """The full validation, with the manifest's error/warning counting made explicit."""

    validation = build["validation"]
    warnings = validation["warnings"]
    request = [issue for issue in warnings if issue["code"] in REQUEST_WARNING_CODES]
    return {
        "format": VALIDATION_FORMAT,
        "build_id": build["manifest"]["build_id"],
        "ok": True,
        "errors": list(validation["errors"]),
        "warnings": list(warnings),
        "normalization": validation.get("normalization", {}),
        "counts": {
            "error_count": len(validation["errors"]),
            "warning_count": len(warnings) - len(request),
            "request_warning_count": len(request),
        },
        "request_warning_codes": sorted(REQUEST_WARNING_CODES),
        "note": (
            "counts.error_count and counts.warning_count equal the manifest checks; the exporter derived them, and "
            "every design warning, again by regenerating design.json under profile.json. Warnings whose code is in "
            "request_warning_codes, and normalization, describe how the request was written (aliases, defaults, a "
            "defaulted schema version), not the design: the manifest does not count them, they are copied from the "
            "result as given, and equivalent requests that share one build can differ in them."
        ),
    }


def _pinout(build: Mapping[str, Any]) -> str:
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(_PINOUT_COLUMNS)
    for side in ("top", "bottom"):
        board = build["boards_by_side"][side]
        stem = _NET_STEMS[board["role"]]
        for pad in sorted(board["layers"]["top_copper"]["pads"], key=lambda pad: pad["pin"]):
            x0, y0, x1, y1 = rect_bounds(pad)
            index = _channel_index(pad["net"], stem) if pad["kind"] == "connector_pad" else None
            center = (f"{(x0 + x1) / 2:.6f}", f"{(y0 + y1) / 2:.6f}")
            writer.writerow((pad["pin"], pad["net"], board["role"], "" if index is None else index, *center, side))
    return stream.getvalue()


# --------------------------------------------------------------------------
# Read-back self-check (D17): decode what was written and compare it with the layout.
# --------------------------------------------------------------------------

_COORDINATE = re.compile(r"X(-?[0-9]{1,10})Y(-?[0-9]{1,10})D0([12])\*\Z")
_APERTURE = re.compile(r"%ADD([1-9][0-9]+)C,([0-9]+\.[0-9]+)\*%\Z")
_SELECT = re.compile(r"D([1-9][0-9]+)\*\Z")
_ATTRIBUTE = re.compile(r"G04 #@! (TF\.[A-Za-z]+),([^*%]*)\*\Z")
_COMMENT = re.compile(r"G04 [^*%]*\*\Z")


def _verify_board_files(
    board: Mapping[str, Any], files: Mapping[str, bytes], groups: Sequence[Mapping[str, Any]], build: Mapping[str, Any]
) -> None:
    try:
        _compare_board_files(board, files, groups, build)
    except (ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError) as error:
        raise ExportError(f"Read-back of {board['id']} failed: {error}") from error


def _compare_board_files(
    board: Mapping[str, Any], files: Mapping[str, bytes], groups: Sequence[Mapping[str, Any]], build: Mapping[str, Any]
) -> None:
    build_id = build["manifest"]["build_id"]
    copper = board["layers"]["top_copper"]
    stiffeners = board["layers"]["bottom_stiffener"]
    expected_names = {_GTL, _GTS, _GKO, _JLC_METADATA, _NETLIST, _ORDER_NOTES, _MANIFEST, *(group["gerber"] for group in groups)}
    if set(files) != expected_names:
        raise ValueError(f"members {sorted(files)} are not {sorted(expected_names)}")

    def decoded(name: str, function: str, polarity: str) -> dict[str, Any]:
        layer = _decode_gerber(name, files[name].decode("ascii"))
        attributes = {
            "TF.GenerationSoftware": f"TactileFPC,direct-gerber,{_version_number()}",
            "TF.SameCoordinates": build_id,
            "TF.FileFunction": function,
            "TF.FilePolarity": polarity,
        }
        if layer["attributes"] != attributes:
            raise ValueError(f"{name} X2 attributes {layer['attributes']} are not {attributes}")
        return layer

    gtl = decoded(_GTL, "Copper,L1,Top", "Positive")
    _same_strokes(_GTL, gtl["strokes"], [(float(route["width_mm"]), route["points"]) for route in copper["routes"]])
    _same_regions(_GTL, gtl["regions"], [_corners(rect) for rect in [*copper["electrodes"], *copper["pads"]]])
    gts = decoded(_GTS, "Soldermask,Top", "Negative")
    _same_strokes(_GTS, gts["strokes"], [])
    _same_regions(_GTS, gts["regions"], _opening_regions(board["layers"]["top_coverlay_openings"]))
    gko = decoded(_GKO, "Profile,NP", "Positive")
    _same_strokes(_GKO, gko["strokes"], [(_OUTLINE_APERTURE_MM, [*ring, ring[0]]) for ring in _outline_contours(board)])
    _same_regions(_GKO, gko["regions"], [])
    for group in groups:
        layer = decoded(group["gerber"], f"Other,{group['side_name']}Stiffener", "Positive")
        _same_strokes(group["gerber"], layer["strokes"], [])
        _same_regions(group["gerber"], layer["regions"], [stiffeners[index]["points"] for index in group["indices"]])

    metadata = json.loads(files[_JLC_METADATA])
    entries = metadata["fpcStiffeners"]
    if set(metadata) != {"fpcStiffeners"} or len(entries) != len(stiffeners):
        raise ValueError(f"{_JLC_METADATA} does not list one entry per stiffener")
    group_of = _group_of(groups)
    for index, (entry, stiffener) in enumerate(zip(entries, stiffeners), start=1):
        group = group_of[index - 1]
        fields = (entry["id"], entry["gerber"], entry["layer"], entry["material"], entry["thickness"])
        if fields != (f"direct_{group['code']}_{index:02d}", group["gerber"], group["side"], group["code"], group["thickness"]):
            raise ValueError(f"{_JLC_METADATA} entry {index} {fields} does not describe its stiffener")
        (path,) = entry["path"][0]
        if path[2] != "L" or len(path) != 2 * len(stiffener["points"]) + 3:
            raise ValueError(f"{_JLC_METADATA} entry {index} is not one closed linear path")
        values = [value for position, value in enumerate(path) if position != 2]
        ring = [(x / _MILS_PER_MM, y / _MILS_PER_MM) for x, y in zip(values[0::2], values[1::2])]
        _same_points(f"{_JLC_METADATA} entry {index}", ring, [*stiffener["points"], stiffener["points"][0]])

    parameters, records = read_netlist(files[_NETLIST].decode("ascii"))
    if (parameters.get("JOB"), parameters.get("TITLE")) != (build_id, board["id"]):
        raise ValueError(f"{_NETLIST} JOB/TITLE do not name this build and board")
    expected = _test_points(board)
    if len(records) != len(expected):
        raise ValueError(f"{_NETLIST} has {len(records)} test records, expected {len(expected)}")
    step = 0.0005 + _READBACK_TOLERANCE_MM  # half the 0.001 mm netlist resolution
    for record, point in zip(records, expected):
        if (record["net"], record["refdes"], record["pin"]) != (point["net"], point["refdes"], str(point["pin"])) or any(
            abs(record[key] - point[key]) > step for key in ("x", "y", "width", "height")
        ):
            raise ValueError(f"{_NETLIST} record {record} does not match test point {point}")

    listed = json.loads(files[_MANIFEST])["files"]
    if listed != _file_digests({name: data for name, data in files.items() if name != _MANIFEST}):
        raise ValueError(f"{_MANIFEST} does not list the digests of the other members")
    if json.loads(files[_MANIFEST])["order_requirements"] != _order_records(build):
        raise ValueError(f"{_MANIFEST} does not list the profile's order requirements")
    _check_order_notes(files[_ORDER_NOTES], build, [(board, groups)])
    _check_order_claims(board, build["order_requirements"])


def _check_order_notes(
    data: bytes, build: Mapping[str, Any], boards: Sequence[tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]]
) -> None:
    """ORDER_NOTES.txt states, in this order and whitespace aside, the build and
    profile, each board with its archive and stiffener layers, every order
    requirement with its reason, the upload checks and every cited source."""

    text = data.decode("utf-8")
    if not text.endswith("\n") or "\r" in text or any(line != line.rstrip() for line in text.split("\n")):
        raise ValueError(f"{_ORDER_NOTES} is not plain text with LF line ends")
    profile, names, records = build["profile"], build["artifact_names"], build["order_requirements"]
    phrases = [f"Build: {build['manifest']['build_id']}", f"Profile: {profile['id']}, revision {profile['revision']}"]
    phrases += _taxel_field_phrases(build)
    for board, groups in boards:
        tail = board["tail"]
        phrases += [f"Board {board['id']}:", f"{tail['connector_pins']} contacts", f"{tail['width_mm']:g} mm wide"]
        # The widths of the build's design (routing) and of the profile's finger traces.
        routing = build["design"]["routing"]
        phrases.append(
            f"fan-out traces {routing['trace_width_mm']:g} mm at {routing['trace_space_mm']:g} mm spacing, "
            f"{profile['routing']['finger_trace_width_mm']:g} mm in the tail"
        )
        phrases.append(_trace_tolerance(float(routing["trace_width_mm"]), profile))
        phrases.append(f"Archive: {names[board['physical_side'] + '_fpc_gerber_zip']}")
        phrases += [f"Stiffener layer: {group['gerber']} ({group['material']} {group['thickness']} mm" for group in groups]
        phrases.append(_coverlay_window_note(board, profile))
        phrases += _row_contact_phrases(board)
    for kind in ("order_option", "review_note"):
        for record in records:
            if record["kind"] == kind:
                phrases += [f"{record['topic']}: {record['requirement']}.", f"Why: {record['reason']}"]
    phrases += _upload_checks([group for _, groups in boards for group in groups])
    phrases += [f"{key}: {_source_text(profile, key)}" for key in _cited_sources(records)]
    flat, position = " ".join(text.split()), 0
    for phrase in phrases:
        found = flat.find(" ".join(phrase.split()), position)
        if found < 0:
            raise ValueError(f"{_ORDER_NOTES} does not state {phrase!r} in its place")
        position = found + len(" ".join(phrase.split()))


def _row_contact_phrases(board: Mapping[str, Any]) -> list[str]:
    """What ORDER_NOTES.txt must state of a diagonal Row bus's Row board: its contacts' pins with the nets of
    ``tail.row_contact_order`` (position k holds the k-th net of the order)."""

    order = board["tail"].get("row_contact_order")
    if order is None:
        return []
    contacts = sorted(board["layers"]["top_copper"]["pads"], key=lambda pad: pad["position"])[: len(order)]
    return [f"Row pin order (diagonal Row bus, {_row_bus_fold(board)}): " + ", ".join(f"pin {pad['pin']} {net}" for pad, net in zip(contacts, order)) + "."]


def _check_taxel_map(data: bytes | None, build: Mapping[str, Any]) -> None:
    """``taxels.csv`` read back against the boards: present exactly for a
    masked build and a diagonal Row bus (whose boards carry the full field's
    mask when it has none), one line per readout position in ROW-major
    order, the nets of the boards' electrodes with the pins of their
    contacts, and ``active`` exactly where both boards' taxel masks put a
    taxel, as many as each board's ``active_taxel_count``."""

    boards = {board["role"]: board for board in build["boards_by_side"].values()}
    registrations = [boards[role]["grid_registration"] for role in ("rows", "columns")]
    masked = build["taxel_mask"] is not None
    if (data is not None) != masked or any(("taxel_mask" in registration) != masked for registration in registrations):
        raise ValueError(f"{_TAXELS} must be written exactly for a masked build, whose boards both carry its taxel mask")
    if data is None:
        return
    mask = registrations[0]["taxel_mask"]
    if registrations[1]["taxel_mask"] != mask:
        raise ValueError(f"the boards' taxel masks differ, so {_TAXELS} has no one readout")
    rows, columns, spans = mask["rows"], mask["columns"], mask["row_spans"]
    nets, pins = {}, {}
    for role, board in boards.items():
        stem = _NET_STEMS[role]
        for electrode in board["layers"]["top_copper"]["electrodes"]:
            nets[(stem, _channel_index(electrode["net"], stem))] = electrode["net"]
        for pad in board["layers"]["top_copper"]["pads"]:
            pins[pad["net"]] = str(pad["pin"])
    records = list(csv.reader(io.StringIO(data.decode("ascii"))))
    if not records or records[0] != list(_TAXEL_COLUMNS) or len(records) != rows * columns + 1:
        raise ValueError(f"{_TAXELS} does not have its header and {rows} x {columns} position lines")
    active = 0
    for index, record in enumerate(records[1:]):
        row, column = index // columns + 1, index % columns + 1
        row_net, column_net = nets[("ROW", row)], nets[("COL", column)]
        flag = "1" if spans[row - 1][0] <= column <= spans[row - 1][1] else "0"
        if record != [str(row), str(column), row_net, column_net, pins[row_net], pins[column_net], flag]:
            raise ValueError(f"{_TAXELS} line {index + 2} {record} does not describe position ({row}, {column}) of the boards")
        active += flag == "1"
    if any(registration["active_taxel_count"] != active for registration in registrations):
        raise ValueError(f"{_TAXELS} lists {active} active positions, the boards count others")


def _check_row_contacts(data: bytes, build: Mapping[str, Any]) -> None:
    """``pinout.csv`` read back against a diagonal Row bus's contact order (nothing to check for the straight
    Row channel): the order the construction reports (``construction.row_bus.contact_order``) is the Row
    tail's (``tail.row_contact_order``), it names every row once, and ``pinout.csv`` lists each of its nets
    at the pin of the contact at its position (pin k carries ROW_k only where the folded order puts it)."""

    entry = _row_bus_entry(build).get("diagonal_row_bus")
    if entry is None:
        return
    order, pins = entry["row_contact_order"], entry["row_contact_pins"]
    if order != entry["construction"]["contact_order"]:
        raise ValueError(f"the Row tail's contact order {order} is not the one construction.row_bus reports")
    if sorted(order) != [f"ROW_{index:02d}" for index in range(1, len(order) + 1)]:
        raise ValueError(f"the Row contact order {order} does not name every row once")
    listed = {record[1]: record[0] for record in list(csv.reader(io.StringIO(data.decode("ascii"))))[1:] if record[2] == "rows"}
    found = [listed.get(net) for net in order]
    if found != [str(pin) for pin in pins]:
        raise ValueError(f"pinout.csv lists the Row nets {order} at the pins {found}, not at their contacts' pins {pins}")


def _check_order_claims(board: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> None:
    """The contact and stiffener figures the order notes state hold for this board.

    Runs after the read-back has matched the emitted GTL, GTS, GKO and
    stiffener layers with the layout: the contact width across the row, the
    contact start from the tip edge, the gang window beyond the outer
    contacts on both sides, the connector-zone stiffener (material, side,
    thickness and length, starting at the tip) and the width of the tail
    (finger) traces.
    """

    values = {record["id"]: record["values"] for record in records}
    side = board["tail"]["side"]
    axis = 1 if side in ("bottom", "top") else 0  # along the tail; the contact row runs across it
    across = 1 - axis
    pads = [rect_bounds(pad) for pad in board["layers"]["top_copper"]["pads"]]
    windows = [rect_bounds(opening) for opening in board["layers"]["top_coverlay_openings"] if opening["kind"] == "connector_contact_opening"]
    if len(windows) != 1:
        raise ValueError(f"{_ORDER_NOTES} describes one gang contact window, {board['id']} has {len(windows)}")
    window, outline = windows[0], board["outline"]["points"]
    stiffeners = [item for item in board["layers"]["bottom_stiffener"] if item.get("zone") == "connector"]
    if len(stiffeners) != 1:
        raise ValueError(f"{_ORDER_NOTES} describes one connector-zone stiffener, {board['id']} has {len(stiffeners)}")
    stiffener, claimed = stiffeners[0], values["pi_stiffener"]
    if (stiffener["material"], stiffener["side"]) != (claimed["material"], claimed["side"]):
        raise ValueError(f"{_ORDER_NOTES} states a {claimed['side']} {claimed['material']} stiffener, {board['id']} has another")
    along = [point[axis] for point in stiffener["points"]]
    if side in ("bottom", "left"):
        start = min(pad[axis] for pad in pads) - min(point[axis] for point in outline)
        stiffener_start = min(along) - min(point[axis] for point in outline)
    else:
        start = max(point[axis] for point in outline) - max(pad[axis + 2] for pad in pads)
        stiffener_start = max(point[axis] for point in outline) - max(along)
    if abs(stiffener_start) > _READBACK_TOLERANCE_MM:
        raise ValueError(f"{_ORDER_NOTES} states the stiffener zone from the tip, {board['id']} starts it {round(stiffener_start, 6)} mm behind")
    measured = {
        ("finger_width", "contact_width_mm"): [pad[across + 2] - pad[across] for pad in pads],
        ("contact_start", "contact_start_from_tip_mm"): [start],
        ("contact_window", "contact_window_side_margin_mm"): [
            min(pad[across] for pad in pads) - window[across], window[across + 2] - max(pad[across + 2] for pad in pads),
        ],
        ("pi_stiffener", "thickness_mm"): [float(stiffener["thickness_mm"])],
        ("pi_stiffener", "zone_length_mm"): [max(along) - min(along)],
        ("trace_widths", "finger_trace_width_mm"): [
            float(route["width_mm"]) for route in board["layers"]["top_copper"]["routes"] if route["segment"] == "tail"
        ],
    }
    for (key, name), figures in measured.items():
        stated = values[key][name]
        for figure in figures:
            if abs(figure - stated) > _READBACK_TOLERANCE_MM:
                raise ValueError(f"{_ORDER_NOTES} states {key} {name} {stated} mm, but {board['id']} has {round(figure, 6)} mm")


def _decode_gerber(name: str, text: str) -> dict[str, Any]:
    """Strictly decode the exporter's RS-274X subset: one command per line.

    Returns X2 attributes, strokes ``(diameter, points)`` and closed regions
    in millimetres; anything else, a coordinate outside FS 4.6 or a missing
    format, unit, polarity or ``M02`` raises ``ValueError``.
    """

    if not text.endswith("\n"):
        raise ValueError(f"{name} does not end with a newline")
    attributes: dict[str, str] = {}
    apertures: dict[str, float] = {}
    strokes: list[tuple[float, list[tuple[float, float]]]] = []
    regions: list[list[tuple[float, float]]] = []
    header: list[str] = []
    diameter: float | None = None
    region: list[tuple[float, float]] | None = None
    linear = ended = False
    for line in text[:-1].split("\n"):
        coordinate, aperture, selection, attribute = (
            pattern.fullmatch(line) for pattern in (_COORDINATE, _APERTURE, _SELECT, _ATTRIBUTE)
        )
        if ended:
            raise ValueError(f"{name} has data after M02")
        if coordinate:
            if header != ["%FSLAX46Y46*%", "%MOMM*%", "%LPD*%"] or not linear:
                raise ValueError(f"{name} draws before its format, unit, polarity and G01")
            point = (int(coordinate[1]) / 1_000_000, int(coordinate[2]) / 1_000_000)
            if region is not None:
                if (coordinate[3] == "2") != (not region):
                    raise ValueError(f"{name} region contour does not start with one D02")
                region.append(point)
            elif coordinate[3] == "2":
                if diameter is None:
                    raise ValueError(f"{name} draws without a selected aperture")
                strokes.append((diameter, [point]))
            elif not strokes:
                raise ValueError(f"{name} has a D01 draw without a start point")
            else:
                strokes[-1][1].append(point)
        elif aperture:
            if aperture[1] in apertures:
                raise ValueError(f"{name} defines aperture D{aperture[1]} twice")
            apertures[aperture[1]] = float(aperture[2])
        elif selection:
            if selection[1] not in apertures or region is not None:
                raise ValueError(f"{name} selects an undefined aperture or selects inside a region")
            diameter = apertures[selection[1]]
        elif attribute:
            if attribute[1] in attributes:
                raise ValueError(f"{name} repeats {attribute[1]}")
            attributes[attribute[1]] = attribute[2]
        elif _COMMENT.fullmatch(line):
            continue
        elif line in ("%FSLAX46Y46*%", "%MOMM*%", "%LPD*%"):
            header.append(line)
        elif line == "G01*":
            linear = True
        elif line == "G36*" and region is None:
            region = []
        elif line == "G37*" and region is not None:
            if len(region) < 4 or region[0] != region[-1]:
                raise ValueError(f"{name} has an open or degenerate region")
            regions.append(region)
            region = None
        elif line == "M02*" and region is None:
            ended = True
        else:
            raise ValueError(f"{name} has an unexpected command {line!r}")
    if not ended or header != ["%FSLAX46Y46*%", "%MOMM*%", "%LPD*%"]:
        raise ValueError(f"{name} lacks its format, unit and polarity header or the M02 end")
    return {"attributes": attributes, "strokes": strokes, "regions": regions}


def _same_strokes(name: str, strokes: list, expected: list) -> None:
    if len(strokes) != len(expected):
        raise ValueError(f"{name} has {len(strokes)} draws, expected {len(expected)}")
    for index, ((diameter, points), (width, intended)) in enumerate(zip(strokes, expected), start=1):
        if abs(diameter - width) > _READBACK_TOLERANCE_MM:
            raise ValueError(f"{name} draw {index} uses a {diameter} mm aperture, expected {width} mm")
        _same_points(f"{name} draw {index}", points, intended)


def _same_regions(name: str, regions: list, expected: list) -> None:
    if len(regions) != len(expected):
        raise ValueError(f"{name} has {len(regions)} regions, expected {len(expected)}")
    for index, (contour, intended) in enumerate(zip(regions, expected), start=1):
        _same_points(f"{name} region {index}", contour, [*intended, intended[0]])


def _same_points(label: str, points: Sequence[Sequence[float]], intended: Sequence[Sequence[float]]) -> None:
    if len(points) != len(intended):
        raise ValueError(f"{label} has {len(points)} vertices, expected {len(intended)}")
    for point, target in zip(points, intended):
        if abs(point[0] - float(target[0])) > _READBACK_TOLERANCE_MM or abs(point[1] - float(target[1])) > _READBACK_TOLERANCE_MM:
            raise ValueError(f"{label} has a vertex at {tuple(point)}, expected {tuple(target)}")


def _corners(rect: Mapping[str, Any]) -> list[tuple[float, float]]:
    """Counter-clockwise corners from the anchored bounds (independent of the writer's rect_corners)."""

    x0, y0, x1, y1 = rect_bounds(rect)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _opening_regions(openings: Sequence[Mapping[str, Any]]) -> list[list[tuple[float, float]]]:
    """The GTS regions the layout asks for, in its order: a polygon field
    window's ring as listed (masked boards), a rectangle's anchored corners."""

    regions = []
    for opening in openings:
        if opening.get("shape") == _POLYGON_SHAPE:
            regions.append([(float(point[0]), float(point[1])) for point in opening["points"]])
        else:
            regions.append(_corners(opening))
    return regions


# --------------------------------------------------------------------------
# Deterministic ZIP and small helpers.
# --------------------------------------------------------------------------


def _deterministic_zip(files: Mapping[str, bytes]) -> bytes:
    """Stored (uncompressed) members in name order with fixed metadata, so the
    archive bytes depend on the member bytes only, never on zlib (L10)."""

    stream = io.BytesIO()
    with ZipFile(stream, "w", compression=ZIP_STORED, strict_timestamps=True) as archive:
        for name in sorted(files):
            info = ZipInfo(filename=name, date_time=_ZIP_TIMESTAMP)
            info.compress_type = ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name])
    return stream.getvalue()


def _verify_zip(data: bytes, files: Mapping[str, bytes]) -> None:
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if [info.filename for info in infos] != sorted(files):
                raise ExportError("ZIP read-back: the member list differs from the written files.")
            for info in infos:
                if info.compress_type != ZIP_STORED or info.date_time != _ZIP_TIMESTAMP or archive.read(info) != files[info.filename]:
                    raise ExportError(f"ZIP read-back: member {info.filename} is not stored as written.")
    except ExportError:
        raise
    except Exception as error:
        raise ExportError(f"ZIP read-back failed ({type(error).__name__}: {error}).") from error


def _file_digests(files: Mapping[str, bytes]) -> dict[str, dict[str, Any]]:
    return {name: {"sha256": _sha256(data), "bytes": len(data)} for name, data in sorted(files.items())}


def _version_number() -> str:
    return EXPORTER_VERSION.rpartition("/")[2]


def _channel_index(net: Any, stem: str) -> int | None:
    match = _CHANNEL_NET.fullmatch(net) if isinstance(net, str) else None
    if match is None or match[1] != stem or int(match[2]) < 1:
        return None
    return int(match[2])


def _nc_pin(net: Any) -> int | None:
    match = _NC_NET.fullmatch(net) if isinstance(net, str) else None
    return None if match is None else int(match[1])


def _is_issue(value: Any) -> bool:
    return isinstance(value, Mapping) and all(isinstance(value.get(key), str) for key in ("code", "field", "message"))


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _member(value: Any, allowed: Any) -> bool:
    return isinstance(value, str) and value in allowed


def _xy(point: Sequence[float]) -> str:
    return f"X{_gerber_coordinate(point[0])}Y{_gerber_coordinate(point[1])}"


def _gerber_point(point: Sequence[float]) -> tuple[int, int]:
    return (int(round(float(point[0]) * 1_000_000)), int(round(float(point[1]) * 1_000_000)))


def _gerber_coordinate(value: float) -> str:
    scaled = int(round(float(value) * 1_000_000))
    sign = "-" if scaled < 0 else ""
    return sign + (str(abs(scaled)).lstrip("0") or "0")


def _mil(value: float) -> float:
    return round(float(value) * _MILS_PER_MM, 4)


def _decimal(value: float) -> str:
    return f"{float(value):.6f}"


def _finite(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except OverflowError:  # an integer beyond the float range
        return False


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _json_text(value: Any, label: str) -> str:
    try:
        return _canonical_json(value)
    except (TypeError, ValueError, RecursionError) as error:
        raise ExportError(f"{label} is not finite JSON data ({type(error).__name__}: {error}).") from error
