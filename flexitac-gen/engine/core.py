"""Pure-stdlib tactile-FPC parameter validation and geometry generation.

This module is deliberately EDA-format agnostic.  It creates a single,
auditable layout object consumed by preview and export adapters, so preview
images, projects and Gerbers can all be derived from the same geometry.
Board geometry lives in :mod:`engine.layout`, the whole-board DRC in
:mod:`engine.drc` and the locked profile checks in :mod:`engine.profile`.

Requests are strict: every key must belong to ``tactile-fpc-design/v1`` or
one of its documented aliases (:data:`ALIASES`), canonical nested fields win
over aliases, and numbers are canonicalised on the 1e-6 mm layout grid before
validation and hashing, so equivalent requests share one design and one
build identity.

A design names its template (``template_id``), and each template has its own
locked profile (:func:`engine.profile.profile_path`):
``generic_matrix_v1`` (the default, the rectangular app) and
``surface_matrix_v1`` (CAD mode: the same sections, built with the tight
geometry policies and limits of ``profiles/jlc_fpc_surface_v1.json``).  A
surface build adds its template version to the hashed build identity, so
generic builds keep their ids byte for byte.

A surface design may also carry a field mask, ``matrix.mask`` (the row spans
of its taxels; :data:`OPTIONAL_FIELDS`): it is not a canonical field, the
full rectangle is normalized away, and a masked design adds
:data:`MASK_VERSION` to its identity, so unmasked builds keep their ids.
``routing.row_sides`` (``left``, ``right`` or ``both``) builds the diagonal
Row bus (:mod:`engine.diagonal`) and adds its construction version as
``row_bus``; ``channel`` builds the straight Row channel.  It is accepted on
both templates (:data:`ROW_SIDES_VALUES`).  On the generic template it is
always set: absent or null it defaults to ``both``, or to ``channel`` where
the tails leave on opposite sides (the bus stacks both tails on one side),
recorded in ``validation.normalization.defaults_applied``.  On the surface
template it is optional: absent, null or ``channel`` is the straight Row
channel and leaves the key out, so those designs keep their build ids.
"""

from __future__ import annotations

import difflib
import hashlib
import html
import json
import math
import re
import threading
from collections import OrderedDict
from typing import Any, Callable, Iterable, Mapping

from .diagonal import CHANNEL, ROW_BUS_VERSION, ROW_SIDES, RowBusInfeasible, row_sides as bus_sides
from .drc import verify_board, verify_registration
from .geometry import bounds_of, rect_bounds, round6
from .layout import (
    LAYOUT_FORMAT,
    TAIL_TURNS,
    apply_physical_assignment,
    apply_tail_side,
    build_column_board,
    build_row_board,
    feasibility_errors,
    floor4,
)
from .profile import (
    GENERIC_TEMPLATE_ID,
    SURFACE_TEMPLATE_ID,
    copper_weight_oz,
    fabrication_minimum,
    load_profile,
    profile_issues,
    profile_path,
    profile_template,
)


SCHEMA_VERSION = "tactile-fpc-design/v1"
# The default template (generic_matrix_v1); the surface template is
# SURFACE_TEMPLATE_ID (surface_matrix_v1).
TEMPLATE_ID = GENERIC_TEMPLATE_ID
# The templates and the version each adds to the hashed build identity: none
# for the generic template, whose build ids predate the others; a change of
# the surface geometry bumps its version, never the generic ids.
TEMPLATE_VERSIONS: dict[str, str | None] = {TEMPLATE_ID: None, SURFACE_TEMPLATE_ID: "surface-matrix/1"}
# The default bottom tail of the generic template's diagonal Row bus (the
# rectangular mode): 12 mm, the top tail's length, so the stacked Row and Column
# tails end together as the form opens (the user's decision of 2026-10-27,
# P5-diagonal-bus.md section 27.7: "矩形模式默认 tail 长度是否改成 12/12 ：可以；可以加个门槛"; the
# surface profile's tail.minimum_length_mm, 7.5 mm, from section 20 until then).
# The surface template's preset keeps that minimum
# (_SURFACE_DEFAULT_BOTTOM_TAIL_MM; CAD mode sizes every tail itself, its
# shortest surface.fit.TAIL_MIN_MM, 7.5 mm); the generic template's straight Row
# channel keeps its own profile's 7.0 mm (_GENERIC_CHANNEL_BOTTOM_TAIL_MM).
_GENERIC_DEFAULT_BOTTOM_TAIL_MM = 12.0
_SURFACE_DEFAULT_BOTTOM_TAIL_MM = 7.5
_GENERIC_CHANNEL_BOTTOM_TAIL_MM = 7.0
# Optional fields: not canonical fields, each accepted on the templates of
# OPTIONAL_FIELD_TEMPLATES.  ``matrix.mask`` is the field mask, one [first, last]
# pair of 1-based COL indices per ROW_01..ROW_R (docs/API.md "Field mask"),
# never defaulted and absent from the canonical design unless given (so it cannot
# touch the identity of a design without it).  ``routing.row_sides`` selects the
# Row traces (ROW_SIDES_VALUES): the diagonal Row bus and its sides
# (engine.diagonal.ROW_SIDES) or the straight Row channel (``channel``).  The
# generic template always sets it (its default, ``both``, or ``channel`` with
# opposite tails: _default_row_sides); the surface template leaves it out for
# the straight channel, so its designs without the bus keep their build ids.
OPTIONAL_FIELDS = ("matrix.mask", "routing.row_sides")
MASK_TEMPLATES = frozenset({SURFACE_TEMPLATE_ID})
ROW_SIDES_VALUES = (*ROW_SIDES, CHANNEL)
# The templates on which routing.row_sides defaults to the bus (always set in the canonical design).
ROW_BUS_DEFAULT_TEMPLATES = frozenset({GENERIC_TEMPLATE_ID})
OPTIONAL_FIELD_TEMPLATES = {"matrix.mask": MASK_TEMPLATES, "routing.row_sides": frozenset({GENERIC_TEMPLATE_ID, SURFACE_TEMPLATE_ID})}
# Added to the hashed identity of masked designs only; it moves only for a fix
# of geometry that masked designs already build.
MASK_VERSION = "field-mask/1"
# The keys template_identity may add to the identity, in the manifests and exports;
# ``row_bus`` is engine.diagonal.ROW_BUS_VERSION, for designs built as the bus (routing.row_sides
# left, right or both) on either template.
IDENTITY_EXTRAS = ("template", "mask", "row_bus")
# An inactive crossing of a masked field is max(pitch - electrode width) less
# the electrode overhang from the electrodes beside it (at a step of the
# mask); below this a stack misregistration may make it read (a warning).
MASK_INACTIVE_GAP_WARNING_MM = 0.15
# Mask issues listed individually; the rest are counted in one more issue.
_MASK_REPORT_LIMIT = 20
GENERATOR_VERSION = "deterministic-sensor-core/0.4.0"
MANIFEST_FORMAT = "tactile-fpc-manifest/v2"
# Design numbers are taken on the layout grid: 6 decimals of a millimetre,
# the resolution of the emitted JSON and Gerber coordinates (geometry.round6).
GRID_DECIMALS = 6
# Integers beyond the I-JSON range (RFC 7493) are not portable JSON numbers.
MAX_JSON_INTEGER = 2**53 - 1
_EPSILON = 1e-9
# Unknown keys listed individually; the rest are counted in one more error.
_UNKNOWN_FIELD_REPORT_LIMIT = 20

TAIL_SIDES = ("bottom", "top", "left", "right")
ROLES = ("rows", "columns")
CHANNEL_ORDERS = ("ascending", "descending")

# The versioned design: top-level scalars, then sections and their keys, in
# canonical order.
TOP_LEVEL_FIELDS = ("schema_version", "template_id", "project_name")
DESIGN_SECTIONS: dict[str, tuple[str, ...]] = {
    "matrix": ("rows", "columns", "pitch_x_mm", "pitch_y_mm", "taxel_width_mm", "taxel_height_mm"),
    "tail": ("top_length_mm", "bottom_length_mm", "row_side", "column_side"),
    "connector": ("row_pins", "column_pins"),
    "role_mapping": ("top", "bottom"),
    "channel_order": ("rows", "columns"),
    "routing": ("trace_width_mm", "trace_space_mm"),
}
CANONICAL_FIELDS = (*TOP_LEVEL_FIELDS, *(f"{section}.{key}" for section, keys in DESIGN_SECTIONS.items() for key in keys))
INTEGER_FIELDS = ("matrix.rows", "matrix.columns", "connector.row_pins", "connector.column_pins")
NUMBER_FIELDS = (
    "matrix.pitch_x_mm", "matrix.pitch_y_mm", "matrix.taxel_width_mm", "matrix.taxel_height_mm",
    "tail.top_length_mm", "tail.bottom_length_mm", "routing.trace_width_mm", "routing.trace_space_mm",
)
# Issue code of each field when its value has the wrong kind.
FIELD_CODES = {
    "schema_version": "E_SCHEMA_VERSION",
    "template_id": "E_TEMPLATE_UNSUPPORTED",
    "project_name": "E_PROJECT_NAME",
    "matrix.rows": "E_ROWS_INTEGER",
    "matrix.columns": "E_COLUMNS_INTEGER",
    **{field: "E_NUMERIC" for field in NUMBER_FIELDS},
    "tail.row_side": "E_TAIL_SIDE",
    "tail.column_side": "E_TAIL_SIDE",
    "connector.row_pins": "E_CONNECTOR_PINS",
    "connector.column_pins": "E_CONNECTOR_PINS",
    "role_mapping.top": "E_ROLE_MAPPING",
    "role_mapping.bottom": "E_ROLE_MAPPING",
    "channel_order.rows": "E_CHANNEL_ORDER",
    "channel_order.columns": "E_CHANNEL_ORDER",
}
_SECTION_CODES = {
    "matrix": "E_MATRIX_OBJECT",
    "tail": "E_TAIL_OBJECT",
    "connector": "E_CONNECTOR_OBJECT",
    "role_mapping": "E_ROLE_MAPPING",
    "channel_order": "E_CHANNEL_ORDER",
    "routing": "E_ROUTING_OBJECT",
}
_EXPECTED = {
    "schema_version": repr(SCHEMA_VERSION),
    "template_id": f"one of {', '.join(map(repr, TEMPLATE_VERSIONS))}",
    "project_name": "a non-empty string",
    "matrix.rows": "an integer",
    "matrix.columns": "an integer",
    **{field: "a finite number" for field in NUMBER_FIELDS},
    "tail.row_side": f"one of {', '.join(map(repr, TAIL_SIDES))}",
    "tail.column_side": f"one of {', '.join(map(repr, TAIL_SIDES))}",
    "connector.row_pins": "an integer or null",
    "connector.column_pins": "an integer or null",
    "role_mapping.top": f"one of {', '.join(map(repr, ROLES))}",
    "role_mapping.bottom": f"one of {', '.join(map(repr, ROLES))}",
    "channel_order.rows": f"one of {', '.join(map(repr, CHANNEL_ORDERS))}",
    "channel_order.columns": f"one of {', '.join(map(repr, CHANNEL_ORDERS))}",
}

# Accepted aliases (HTML form names and early prototype names) as
# ``(alias path, canonical targets, value map)``.  The list order is the
# precedence among aliases of one field; a canonical nested field always wins.
# Nested legacy names come first, because nested fields win over flat
# aliases, then specific flat names, then flat names that set two fields.  A
# value map turns an alias value into one value per target; ``None`` copies it.
ALIASES: tuple[tuple[str, tuple[str, ...], Mapping[str, tuple[str, ...]] | None], ...] = (
    ("tail.length_mm", ("tail.top_length_mm", "tail.bottom_length_mm"), None),
    ("matrix.column_electrode_width_mm", ("matrix.taxel_width_mm",), None),
    ("matrix.row_electrode_width_mm", ("matrix.taxel_height_mm",), None),
    ("name", ("project_name",), None),
    ("rows", ("matrix.rows",), None),
    ("row_num", ("matrix.rows",), None),
    ("columns", ("matrix.columns",), None),
    ("column_num", ("matrix.columns",), None),
    ("pitch_x_mm", ("matrix.pitch_x_mm",), None),
    ("pitch_y_mm", ("matrix.pitch_y_mm",), None),
    ("taxel_width_mm", ("matrix.taxel_width_mm",), None),
    ("column_electrode_width_mm", ("matrix.taxel_width_mm",), None),
    ("column_electrode_width", ("matrix.taxel_width_mm",), None),
    ("taxel_height_mm", ("matrix.taxel_height_mm",), None),
    ("row_electrode_width_mm", ("matrix.taxel_height_mm",), None),
    ("row_electrode_width", ("matrix.taxel_height_mm",), None),
    ("top_tail_length_mm", ("tail.top_length_mm",), None),
    ("bottom_tail_length_mm", ("tail.bottom_length_mm",), None),
    ("trace_width_mm", ("routing.trace_width_mm",), None),
    ("trace_space_mm", ("routing.trace_space_mm",), None),
    ("tail_length_mm", ("tail.top_length_mm", "tail.bottom_length_mm"), None),
    ("taxel_size_mm", ("matrix.taxel_width_mm", "matrix.taxel_height_mm"), None),
    ("connector_side", ("tail.row_side", "tail.column_side"), {side: (side, side) for side in TAIL_SIDES}),
    ("row_fpc_position", ("role_mapping.top", "role_mapping.bottom"), {"top": ("rows", "columns"), "bottom": ("columns", "rows")}),
    (
        "scan_order",
        ("channel_order.rows", "channel_order.columns"),
        {
            "forward": ("ascending", "ascending"),
            "reverse": ("descending", "descending"),
            "ascending": ("ascending", "ascending"),
            "descending": ("descending", "descending"),
        },
    ),
)
_ALIAS_TARGETS = {alias: targets for alias, targets, _ in ALIASES}
_ALIAS_SOURCES = {
    field: tuple(alias for alias, targets, _ in ALIASES if field in targets) for field in CANONICAL_FIELDS
}
_FLAT_ALIASES = frozenset(alias for alias in _ALIAS_TARGETS if "." not in alias)
_NESTED_ALIASES = frozenset(alias for alias in _ALIAS_TARGETS if "." in alias)
# Warnings about how a request was written, not about the design itself; the
# build manifest does not count them, so equivalent requests share it.
REQUEST_WARNING_CODES = frozenset({"W_SCHEMA_VERSION_DEFAULTED", "W_ALIAS_SHADOWED"})
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_UNSAFE_TEXT = re.compile("[\x00-\x1f\x7f-\x9f\ud800-\udfff]")


def default_design(template_id: str = TEMPLATE_ID) -> dict[str, Any]:
    """Return a fresh, UI-ready design form using the 12 × 32 / 2 mm preset.

    ``taxel_width_mm`` controls the width of the column electrode and
    ``taxel_height_mm`` controls the width of the row electrode.  Their
    overlap is the nominal tactile taxel area; it is not a promise of final
    pressure response, which also depends on the sensing stack and assembly.
    ``connector.row_pins`` / ``connector.column_pins`` select the ZIF
    connector size of each tail; ``None`` means one position per channel.
    ``routing`` sets the thin fan-out traces between the electrodes and the
    tail (5/5 mil, a 0.254 mm bundle pitch); in the tail the traces widen to
    the profile's finger width.  ``routing.row_sides`` ``both`` builds the
    diagonal Row bus on both sides (the generic template's default, built
    with CAD mode's rule set, :func:`rules_template`; both tails 12 mm, so
    the stacked tails end together, since the user's decision of 2026-10-27,
    the bottom tail that rule set's 7.5 mm minimum before; ``channel`` is the
    straight Row channel, whose default bottom tail is 7.0 mm).
    ``template_id`` ``surface_matrix_v1`` gives the same preset on the surface
    template, with the bottom tail at its profile's 7.5 mm minimum and no
    ``routing.row_sides`` (its straight Row channel); another template raises
    ``ValueError``.
    """

    if template_id not in TEMPLATE_VERSIONS:
        raise ValueError(f"unknown design template {template_id!r}; the templates are {', '.join(map(repr, TEMPLATE_VERSIONS))}")
    design = {
        "schema_version": SCHEMA_VERSION,
        "template_id": TEMPLATE_ID,
        "project_name": "Tactile FPC 12x32",
        "matrix": {
            "rows": 12,
            "columns": 32,
            "pitch_x_mm": 2.0,
            "pitch_y_mm": 2.0,
            "taxel_width_mm": 1.4,
            "taxel_height_mm": 1.4,
        },
        "tail": {
            "top_length_mm": 12.0,
            "bottom_length_mm": _GENERIC_DEFAULT_BOTTOM_TAIL_MM,
            "row_side": "bottom",
            "column_side": "bottom",
        },
        "connector": {
            "row_pins": None,
            "column_pins": None,
        },
        "role_mapping": {
            "top": "rows",
            "bottom": "columns",
        },
        "channel_order": {
            "rows": "ascending",
            "columns": "ascending",
        },
        "routing": {
            "trace_width_mm": 0.127,
            "trace_space_mm": 0.127,
            "row_sides": "both",
        },
    }
    if template_id == SURFACE_TEMPLATE_ID:
        design["template_id"] = SURFACE_TEMPLATE_ID
        design["tail"]["bottom_length_mm"] = _SURFACE_DEFAULT_BOTTOM_TAIL_MM
        del design["routing"]["row_sides"]
    return design


def template_of(design: Any) -> str:
    """The template whose profile builds ``design``: its ``template_id`` when it is a known one, else the generic template."""

    template = design.get("template_id") if isinstance(design, Mapping) else None
    return template if isinstance(template, str) and template in TEMPLATE_VERSIONS else TEMPLATE_ID


def rules_template(design: Any) -> str:
    """The template whose locked profile builds ``design``: the surface template's for a design built as the diagonal
    Row bus (``routing.row_sides`` ``left``, ``right`` or ``both``) on either template, else its own template
    (:func:`template_of`).

    The rectangular generator's bus is a subset of CAD mode's
    (claude/specs/masked-field/P5-diagonal-bus.md section 20): one rule set
    (the surface profile's: the 0.5 mm field margin, one Column fan-out lane
    for up to 64 columns, the 60-85 degree caps, tails of at least 7.5 mm)
    and one construction, so a generic bus design builds the boards the same
    design builds on the surface template.  The straight Row channel of the
    generic template keeps its own profile (jlc-fpc-standard-v1).
    """

    return SURFACE_TEMPLATE_ID if bus_sides(design) is not None else template_of(design)


def template_identity(design: Any) -> dict[str, str]:
    """The template part of a design's hashed build identity: ``{}`` for the generic template, else ``{"template": version}``.

    A design with a field mask (``matrix.mask``) adds ``"mask": MASK_VERSION``,
    and one built as the diagonal Row bus (``routing.row_sides`` ``left``,
    ``right`` or ``both``; engine.diagonal) ``"row_bus": ROW_BUS_VERSION``,
    on either template.
    """

    version = TEMPLATE_VERSIONS[template_of(design)]
    identity = {} if version is None else {"template": version}
    matrix = design.get("matrix") if isinstance(design, Mapping) else None
    if isinstance(matrix, Mapping) and matrix.get("mask") is not None:
        identity["mask"] = MASK_VERSION
    if bus_sides(design) is not None:
        identity["row_bus"] = ROW_BUS_VERSION
    return identity


def generate_design(
    data: Mapping[str, Any] | None = None, *, cache: "BuildCache | None" = None, profile: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Validate a high-level design and, when valid, generate two FPC layouts.

    The result has the stable shape used by the web application:

    ``{ok, design, profile, validation, boards:{row,column}, derived_layout, manifest}``

    Inputs may be partial; missing fields take the defaults of
    :func:`default_design`, and ``None`` (no request at all) is the default
    design; the HTTP API and cli.py reject a ``null`` document before it gets
    here.  The documented flat aliases (for example
    ``rows`` and ``taxel_size_mm``) are accepted, unknown keys are errors, and
    the returned design always uses the nested versioned schema.
    ``validation.normalization`` records the aliases applied or shadowed, the
    defaults used and the values rounded to the layout grid.  ``cache`` (a
    :class:`BuildCache`) reuses the boards of an identical build.  ``profile``
    replaces the locked manufacturing profile and is checked like it (an
    inconsistent one fails validation); the exporter regenerates a result
    with the result's own profile.  Without ``profile`` the design's template
    (``template_id``) picks the locked profile: ``generic_matrix_v1``
    ``profiles/jlc_fpc_standard_v1.json``, ``surface_matrix_v1``
    ``profiles/jlc_fpc_surface_v1.json``; a design built as the diagonal Row
    bus takes the surface profile on either template (:func:`rules_template`).
    """

    design, validation, profile = _prepare(data, profile)
    identity = _identity(design, profile)
    result: dict[str, Any] = {
        "ok": not validation["errors"],
        "design": design,
        "profile": profile,
        "validation": validation,
        "boards": {},
        "derived_layout": {"format": LAYOUT_FORMAT, "units": "mm", "boards": {}},
        "manifest": _manifest(identity, validation, {}, profile),
    }
    if not result["ok"]:
        return result

    def build() -> dict[str, Any]:
        return _build_boards(design, profile)

    built = build() if cache is None else cache.fetch(identity["build_sha256"], build)
    validation["errors"].extend(built["errors"])
    validation["warnings"].extend(built["warnings"])
    _deduplicate_issues(validation)
    result["ok"] = not validation["errors"]
    result["boards"] = built["boards"]
    # Kept as a named export boundary for serializers/download routes.  The
    # board mapping is shared in-memory; normal JSON encoding remains valid.
    result["derived_layout"] = {
        "format": LAYOUT_FORMAT,
        "units": "mm",
        "boards": result["boards"],
    }
    result["manifest"] = _manifest(identity, validation, result["boards"], profile)
    return result


def check_design(data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Normalize and validate a request (input rules and feasibility) without geometry.

    Returns ``{ok, design, validation, identity}``; ``identity`` holds the
    build id that :func:`generate_design` would give the same request.  The
    whole-board DRC runs only on generated geometry.  The design picks the
    profile, as in :func:`generate_design` (:func:`rules_template`).
    """

    design, validation, profile = _prepare(data)
    return {"ok": not validation["errors"], "design": design, "validation": validation, "identity": _identity(design, profile)}


def result_view(result: Mapping[str, Any], view: str = "full") -> dict[str, Any]:
    """Shape a :func:`generate_design` result for transport.

    ``full`` drops ``derived_layout``, which repeats ``boards`` (a client builds
    the derived-layout document as ``{format: manifest.layout_format, units:
    "mm", boards}``).  ``compact`` keeps the decision summary: ok, design,
    validation, manifest and, per board, its metrics and DRC measurements,
    without outline, layers or SVG.
    """

    if view == "full":
        return {key: value for key, value in result.items() if key != "derived_layout"}
    if view == "compact":
        keys = ("id", "role", "physical_side", "units", "tail", "grid_registration", "metrics", "verification")
        return {
            "ok": result["ok"],
            "design": result["design"],
            "validation": result["validation"],
            "manifest": result["manifest"],
            "boards": {name: {key: board[key] for key in keys if key in board} for name, board in result["boards"].items()},
        }
    raise ValueError(f"unknown result view {view!r}; use 'full' or 'compact'")


class BuildCache:
    """Small thread-safe LRU of generated boards keyed by build identity.

    Entries are kept as JSON text, so every caller gets its own copy and a
    cached build is indistinguishable from a fresh one.
    """

    def __init__(self, maxsize: int = 8) -> None:
        self.maxsize = maxsize
        self.hits = 0
        self.misses = 0
        self._entries: OrderedDict[str, str] = OrderedDict()
        self._lock = threading.Lock()

    def fetch(self, key: str, build: Callable[[], Any]) -> Any:
        """Return the entry for ``key``, calling ``build()`` once on a miss."""

        with self._lock:
            text = self._entries.get(key)
            if text is not None:
                self._entries.move_to_end(key)
                self.hits += 1
        if text is None:
            text = json.dumps(build(), separators=(",", ":"), allow_nan=False)
            with self._lock:
                self.misses += 1
                self._entries[key] = text
                self._entries.move_to_end(key)
                while len(self._entries) > self.maxsize:
                    self._entries.popitem(last=False)
        return json.loads(text)


def _build_boards(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """Build, orient, assign and check both boards: ``{boards, errors, warnings}``.

    A diagonal Row bus that cannot place its lanes builds no boards
    (``E_ROW_BUS_INFEASIBLE`` at ``routing.row_sides``).
    """

    try:
        row_board = build_row_board(design, profile)
        column_board = build_column_board(design, profile)
    except RowBusInfeasible as infeasible:
        return {"boards": {}, "errors": [_issue("E_ROW_BUS_INFEASIBLE", "routing.row_sides", f"{infeasible}")], "warnings": []}
    apply_tail_side(row_board, design["tail"]["row_side"])
    apply_tail_side(column_board, design["tail"]["column_side"])
    apply_physical_assignment(row_board, column_board, design["role_mapping"])
    boards = {"row": row_board, "column": column_board}
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    # The input-rule checks are necessary but cannot prove the emitted copper,
    # coverlay, stiffener and outline are mutually clear.  Run the whole-board
    # DRC after rotation/physical assignment so that every artifact and its
    # preview share the same checked geometry.
    for board in boards.values():
        verification = verify_board(board, profile, design)
        board["verification"] = verification["measurements"]
        errors.extend(verification["errors"])
        warnings.extend(verification["warnings"])
    registration = verify_registration(row_board, column_board, profile)
    for board in boards.values():
        board["verification"]["registration"] = registration["measurements"]
        board["svg"] = _svg_for_board(board)
    errors.extend(registration["errors"])
    warnings.extend(registration.get("warnings", []))
    return {"boards": boards, "errors": errors, "warnings": warnings}


def _prepare(data: Any, profile: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any], Mapping[str, Any]]:
    """Normalize and validate a request: ``(design, validation, profile)``.

    Without ``profile`` the normalized design picks its locked profile (:func:`rules_template`).
    """

    design, errors, warnings, report, flagged = _normalize_design(data)
    if profile is None:
        profile = load_profile(rules_template(design))
    checked = validate_design(design, profile)
    # A value rejected during normalization was replaced by null; do not
    # report it (or its section) a second time.
    errors += [
        issue for issue in checked["errors"]
        if issue["field"] not in flagged and not any(field.startswith(issue["field"] + ".") for field in flagged)
    ]
    validation = {"errors": errors, "warnings": warnings + checked["warnings"], "normalization": report}
    _deduplicate_issues(validation)
    return design, validation, profile


def validate_design(
    design: Mapping[str, Any], profile: Mapping[str, Any] | None = None
) -> dict[str, list[dict[str, str]]]:
    """Return DRC-style errors and warnings of a normalized design without generating EDA geometry.

    Numbers are checked on the 1e-6 mm layout grid the geometry is built on.
    Independent rules are all reported; the feasibility check runs only when
    every input rule passes.  Without ``profile`` the design picks the locked
    profile (:func:`rules_template`: its template's, the surface template's
    for the diagonal Row bus); a profile of another template is an error.
    """

    profile = load_profile(rules_template(design)) if profile is None else profile
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def error(code: str, message: str, field: str) -> None:
        errors.append({"code": code, "message": message, "field": field})

    def warning(code: str, message: str, field: str) -> None:
        warnings.append({"code": code, "message": message, "field": field})

    if not isinstance(design, Mapping):
        error("E_DESIGN_TYPE", "Design must be a JSON object.", "$")
        return {"errors": errors, "warnings": warnings}

    matrix = design.get("matrix")
    tail = design.get("tail")
    role_mapping = design.get("role_mapping")
    order = design.get("channel_order")
    connector = design.get("connector")
    if not isinstance(matrix, Mapping):
        error("E_MATRIX_OBJECT", "matrix must be an object.", "matrix")
        return {"errors": errors, "warnings": warnings}
    if not isinstance(tail, Mapping):
        error("E_TAIL_OBJECT", "tail must be an object.", "tail")
        return {"errors": errors, "warnings": warnings}

    if design.get("schema_version") != SCHEMA_VERSION:
        error("E_SCHEMA_VERSION", f"schema_version must be {SCHEMA_VERSION!r}.", "schema_version")
    template = design.get("template_id")
    if not (isinstance(template, str) and template in TEMPLATE_VERSIONS):
        error(
            "E_TEMPLATE_UNSUPPORTED",
            f"template_id must be one of {', '.join(map(repr, TEMPLATE_VERSIONS))}, the templates the deterministic core implements.",
            "template_id",
        )
    elif profile_template(profile) != rules_template(design):
        # The other rules would be the wrong template's: report only this.
        rules = rules_template(design)
        built = "its own profile" if rules == template else "the diagonal Row bus's profile"
        error(
            "E_TEMPLATE_UNSUPPORTED",
            f"template_id {template!r} is built with {built} ({profile_path(rules).name}); the profile given "
            f"belongs to {profile_template(profile)!r}.",
            "template_id",
        )
        return {"errors": errors, "warnings": warnings}

    issues = profile_issues(profile)
    if issues:
        errors.extend(issues)
        return {"errors": errors, "warnings": warnings}
    limits = profile["limits"]
    routing = profile["routing"]
    fanout = profile["fanout"]

    name = design.get("project_name")
    name_limit = int(limits["maximum_project_name_length"])
    if not isinstance(name, str) or not name.strip():
        error("E_PROJECT_NAME", "project_name must be a non-empty string.", "project_name")
    elif len(name.strip()) > name_limit:
        error(
            "E_PROJECT_NAME",
            f"project_name must be {name_limit} characters or fewer after trimming (limits.maximum_project_name_length).",
            "project_name",
        )
    elif _UNSAFE_TEXT.search(name):
        error("E_PROJECT_NAME", "project_name must not contain control characters or unpaired surrogates.", "project_name")

    rows = _count(matrix.get("rows"), "matrix.rows", ("E_ROWS_INTEGER", "E_ROWS_RANGE"), limits["minimum_rows"], limits["maximum_rows"], error)
    columns = _count(
        matrix.get("columns"), "matrix.columns", ("E_COLUMNS_INTEGER", "E_COLUMNS_RANGE"),
        limits["minimum_columns"], limits["maximum_columns"], error,
    )
    lane_capacity = int(fanout["maximum_lanes"]) * int(fanout["maximum_channels_per_lane"])
    if columns is not None and columns > lane_capacity:
        error(
            "E_COLUMNS_LANE_CAPACITY",
            f"matrix.columns must be at most {lane_capacity}: {fanout['maximum_lanes']} fan-out lanes of "
            f"{fanout['maximum_channels_per_lane']} channels.",
            "matrix.columns",
        )

    routing_section = design.get("routing")
    sections = {"matrix": matrix, "tail": tail, "routing": routing_section}
    if not isinstance(routing_section, Mapping):
        error("E_ROUTING_OBJECT", "routing must be an object with trace_width_mm and trace_space_mm.", "routing")
    grid: dict[str, float] = {}
    for field in NUMBER_FIELDS:
        section, _, key = field.partition(".")
        if not isinstance(sections[section], Mapping):
            continue
        value = sections[section].get(key)
        if _is_number(value):
            # Geometry is built on the 1e-6 mm layout grid; check the values it uses.
            grid[field] = round6(value)
        else:
            error("E_NUMERIC", f"{field} must be a finite number.", field)

    for field in ("matrix.pitch_x_mm", "matrix.pitch_y_mm"):
        if field in grid and not limits["minimum_pitch_mm"] <= grid[field] <= limits["maximum_pitch_mm"]:
            error(
                "E_PITCH_RANGE",
                f"{field} must be between {limits['minimum_pitch_mm']} and {limits['maximum_pitch_mm']} mm.",
                field,
            )
    minimum_width = float(routing["min_electrode_width_mm"])
    gap = float(routing["min_electrode_gap_mm"])
    for field, pitch_field in (("matrix.taxel_width_mm", "matrix.pitch_x_mm"), ("matrix.taxel_height_mm", "matrix.pitch_y_mm")):
        if field not in grid:
            continue
        size = grid[field]
        if size < 0:
            error("E_TAXEL_SIZE", f"{field} must be greater than zero.", field)
        elif size + _EPSILON < minimum_width:
            error(
                "E_ELECTRODE_WIDTH",
                f"{field} must be at least {minimum_width} mm (routing.min_electrode_width_mm).",
                field,
            )
        elif pitch_field in grid:
            pitch = grid[pitch_field]
            if size + gap > pitch + _EPSILON:
                error(
                    "E_ELECTRODE_GAP",
                    f"{field} leaves less than {gap} mm isolation at this pitch; it must be at most "
                    f"{floor4(pitch - gap):.4f} mm.",
                    field,
                )
            elif size / pitch > float(limits["high_fill_factor_warning"]):
                warning(
                    "W_HIGH_FILL_FACTOR",
                    f"{field} uses more than {float(limits['high_fill_factor_warning']):.0%} of its pitch; sensing isolation margin is small.",
                    field,
                )

    for field in ("tail.top_length_mm", "tail.bottom_length_mm"):
        if field in grid and not profile["tail"]["minimum_length_mm"] <= grid[field] <= limits["maximum_tail_length_mm"]:
            error(
                "E_TAIL_LENGTH",
                f"{field} must be between {profile['tail']['minimum_length_mm']} and {limits['maximum_tail_length_mm']} mm.",
                field,
            )

    # The thin bundle traces between the electrodes and the tail: from JLC's
    # minimum for the profile's copper up to the finger width (and spacing).
    fabrication = dict(zip(("width", "space"), fabrication_minimum(profile)))
    for kind, code in (("width", "E_TRACE_WIDTH"), ("space", "E_TRACE_SPACE")):
        field = f"routing.trace_{kind}_mm"
        low, high = limits[f"minimum_trace_{kind}_mm"], limits[f"maximum_trace_{kind}_mm"]
        if field in grid and not low <= grid[field] <= high:
            error(
                code,
                f"{field} must be between {low} and {high} mm (limits.minimum_trace_{kind}_mm..maximum_trace_{kind}_mm; "
                f"JLCPCB's minimum trace {kind} for {copper_weight_oz(profile):g} oz copper is {fabrication[kind]:g} mm).",
                field,
            )

    sides = {}
    for key in ("row_side", "column_side"):
        if _member(tail.get(key), TAIL_SIDES):
            sides[key] = tail[key]
        else:
            error("E_TAIL_SIDE", f"tail.{key} must be bottom, top, left, or right.", f"tail.{key}")
    if len(sides) == 2 and (TAIL_TURNS[sides["row_side"]] - TAIL_TURNS[sides["column_side"]]) % 2:
        # Each tail side rotates its whole board, so a quarter-turn difference
        # would leave the Row and Column electrodes parallel.
        allowed = [side for side, turns in TAIL_TURNS.items() if (turns - TAIL_TURNS[sides["row_side"]]) % 2 == 0]
        error(
            "E_TAIL_SIDE_PARALLEL",
            f"tail.column_side {sides['column_side']!r} is a quarter turn from tail.row_side {sides['row_side']!r}, "
            f"which makes the Row and Column electrodes parallel; use one of {allowed}.",
            "tail.column_side",
        )

    if not isinstance(role_mapping, Mapping):
        error("E_ROLE_MAPPING", "role_mapping must be an object with top and bottom.", "role_mapping")
    else:
        # Each position is checked on its own, so one bad value cannot hide the other.
        roles = {}
        for key in ("top", "bottom"):
            if _member(role_mapping.get(key), ROLES):
                roles[key] = role_mapping[key]
            else:
                error("E_ROLE_MAPPING", f"role_mapping.{key} must be rows or columns.", f"role_mapping.{key}")
        if len(roles) == 2 and roles["top"] == roles["bottom"]:
            error(
                "E_ROLE_MAPPING",
                "role_mapping must assign rows and columns exactly once across top and bottom.",
                "role_mapping",
            )
    if not isinstance(order, Mapping):
        error("E_CHANNEL_ORDER", "channel_order must be an object.", "channel_order")
    else:
        for role in ROLES:
            if not _member(order.get(role), CHANNEL_ORDERS):
                error(
                    "E_CHANNEL_ORDER",
                    f"channel_order.{role} must be ascending or descending.",
                    f"channel_order.{role}",
                )

    if connector is not None and not isinstance(connector, Mapping):
        error("E_CONNECTOR_OBJECT", "connector must be an object.", "connector")
    else:
        maximum_pins = int(profile["connector"]["maximum_pins"])
        for key, channels in (("row_pins", rows), ("column_pins", columns)):
            value = (connector or {}).get(key)
            if value is None:
                continue
            pins = _as_integer(value)
            if pins is None:
                error("E_CONNECTOR_PINS", f"connector.{key} must be an integer or null.", f"connector.{key}")
            elif not (1 if channels is None else channels) <= pins <= maximum_pins:
                lowest = "one contact per channel" if channels is not None else "at least one contact"
                error(
                    "E_CONNECTOR_PINS",
                    f"connector.{key} must be between {1 if channels is None else channels} ({lowest}) and {maximum_pins} "
                    "(connector.maximum_pins), or null for one position per channel.",
                    f"connector.{key}",
                )

    mask = matrix.get("mask")
    if mask is not None:
        if not (isinstance(template, str) and template in MASK_TEMPLATES):
            # The normalizer refuses the key on other templates; a design built elsewhere may carry it.
            errors.append(_unknown_field("matrix", "mask", mask))
        elif rows is not None and columns is not None:
            issues = _mask_issues(mask, rows, columns)
            errors.extend(issues)
            sizes = ("matrix.pitch_x_mm", "matrix.taxel_width_mm", "matrix.pitch_y_mm", "matrix.taxel_height_mm")
            if not issues and all(field in grid for field in sizes):
                pitch_x, width_x, pitch_y, width_y = (grid[field] for field in sizes)
                separation = round6(max(round6(pitch_x - width_x), round6(pitch_y - width_y)) - float(routing["electrode_overhang_mm"]))
                if separation < MASK_INACTIVE_GAP_WARNING_MM - _EPSILON:
                    warning(
                        "W_MASK_INACTIVE_GAP",
                        f"The mask's inactive crossings are {separation:g} mm from the electrodes beside them (the larger "
                        "electrode gap, pitch less width, less routing.electrode_overhang_mm); a stack misregistration of that "
                        f"much makes one read. Widen the electrode gaps to keep at least {MASK_INACTIVE_GAP_WARNING_MM:g} mm.",
                        "matrix.pitch_x_mm",
                    )

    row_sides = routing_section.get("row_sides") if isinstance(routing_section, Mapping) else None
    if row_sides is not None:
        if not _member(row_sides, ROW_SIDES_VALUES):
            error("E_ROW_SIDES", _row_sides_message(row_sides), "routing.row_sides")
        elif row_sides != CHANNEL and len(sides) == 2 and _opposite_tails(sides["row_side"], sides["column_side"]):
            # Opposite tails; a quarter turn is E_TAIL_SIDE_PARALLEL's.
            error(
                "E_ROW_BUS_TAILS",
                f"routing.row_sides {row_sides!r} builds the diagonal Row bus with both tails on one side; tail.row_side "
                f"{sides['row_side']!r} and tail.column_side {sides['column_side']!r} are opposite. Make them equal, or set "
                f"routing.row_sides to {CHANNEL!r} for the straight Row channel.",
                "routing.row_sides",
            )

    if rows is not None and columns is not None and rows * columns > int(limits["large_matrix_warning_taxels"]):
        warning(
            "W_LARGE_MATRIX",
            "Large matrices can produce substantial preview and Gerber files.",
            "matrix",
        )
    if not errors:
        errors.extend(feasibility_errors(design, profile))
    return {"errors": errors, "warnings": warnings}


def _count(value: Any, field: str, codes: tuple[str, str], minimum: int, maximum: int, error: Any) -> int | None:
    """An integer count (integral floats included) inside its range, else report it and return None."""

    count = _as_integer(value)
    if count is None:
        error(codes[0], f"{field} must be an integer.", field)
        return None
    if not minimum <= count <= maximum:
        error(codes[1], f"{field} must be between {minimum} and {maximum}.", field)
        return None
    return count


def _mask_issues(value: Any, rows: int, columns: int) -> list[dict[str, str]]:
    """The input rules of a field mask on a ``rows`` x ``columns`` grid (docs/API.md "Field mask").

    They make the field one connected piece, every row and every column a
    contiguous run, that spans the whole grid: each ROW and COL net keeps one
    rectangular electrode, and the electrode overhang (below the minimum
    electrode gap) leaves the crossings exactly the mask's taxels.
    """

    mask, issues = _mask_pairs(value)
    if mask is None:
        return issues
    if len(mask) != rows:
        return [_issue("E_MASK_ROWS", "matrix.mask", f"matrix.mask has {len(mask)} entries; it needs one [first, last] pair per row, {rows} for matrix.rows.")]
    for index, (first, last) in enumerate(mask):
        if not 1 <= first <= last <= columns:
            issues.append(_issue(
                "E_MASK_RANGE", f"matrix.mask[{index}]",
                f"ROW_{index + 1:02d} spans [{first}, {last}]; a span needs 1 <= first <= last <= {columns} (matrix.columns), so every row keeps a taxel.",
            ))
    if issues:
        return _capped(issues)
    for index in range(1, rows):
        (first, last), (next_first, next_last) = mask[index - 1], mask[index]
        if max(first, next_first) > min(last, next_last):
            issues.append(_issue(
                "E_MASK_DISCONNECTED", f"matrix.mask[{index}]",
                f"ROW_{index:02d} (COL_{first:02d}..COL_{last:02d}) and ROW_{index + 1:02d} (COL_{next_first:02d}..COL_{next_last:02d}) "
                "share no column; consecutive rows must overlap, so the field is one piece.",
            ))
    for column in range(1, columns + 1):
        active = [row for row, (first, last) in enumerate(mask, start=1) if first <= column <= last]
        if not active:
            issues.append(_issue(
                "E_MASK_COLUMN_EMPTY", "matrix.mask",
                f"COL_{column:02d} has no taxel; the mask spans every column of matrix.columns (lower it, or widen a row).",
            ))
        elif active[-1] - active[0] + 1 != len(active):
            missing = next(row for row in range(active[0], active[-1] + 1) if row not in active)
            issues.append(_issue(
                "E_MASK_COLUMN_GAP", "matrix.mask",
                f"COL_{column:02d} has taxels in ROW_{active[0]:02d}..ROW_{active[-1]:02d} but not in ROW_{missing:02d}; a column's "
                "taxels must be consecutive rows.",
            ))
    return _capped(issues)


def _mask_pairs(value: Any) -> tuple[list[list[int]] | None, list[dict[str, str]]]:
    """A field mask as ``[first, last]`` integer pairs (integral floats become ints), or ``(None, E_MASK_TYPE issues)``."""

    if not isinstance(value, (list, tuple)):
        message = f"matrix.mask must be null or an array of [first, last] column pairs, one per row (got {_describe(value)})."
        return None, [_issue("E_MASK_TYPE", "matrix.mask", message)]
    pairs: list[list[int]] = []
    issues: list[dict[str, str]] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, (list, tuple)):
            problem = f"got {_describe(entry)}"
        elif len(entry) != 2:
            problem = f"got an array of {len(entry)} values"
        else:
            pair = [_mask_index(item) for item in entry]
            if None not in pair:
                pairs.append(pair)
                continue
            problem = f"got {_describe(entry[pair.index(None)])}"
        field = f"matrix.mask[{index}]"
        issues.append(_issue("E_MASK_TYPE", field, f"{field} must be a [first, last] pair of integer column indices ({problem})."))
    return (None, _capped(issues)) if issues else (pairs, [])


def _mask_index(value: Any) -> int | None:
    """A column index of a mask: an integer or integral float within the portable JSON range (not a bool)."""

    index = _as_integer(value)
    return index if index is not None and abs(index) <= MAX_JSON_INTEGER else None


def _capped(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    """At most _MASK_REPORT_LIMIT mask issues, plus one counting the rest."""

    if len(issues) <= _MASK_REPORT_LIMIT:
        return issues
    rest = issues[_MASK_REPORT_LIMIT:]
    return issues[:_MASK_REPORT_LIMIT] + [_issue(rest[0]["code"], "matrix.mask", f"{len(rest)} more matrix.mask issues are not listed.")]


# --------------------------------------------------------------------------
# Normalization: strict request -> versioned design.
# --------------------------------------------------------------------------


def _normalize_design(
    data: Any,
) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]], dict[str, Any], set[str]]:
    """Map a request onto the versioned schema.

    Returns ``(design, errors, warnings, report, flagged)``.  ``report`` is the
    ``validation.normalization`` record; ``flagged`` holds the canonical fields
    whose value was rejected here and replaced by null.
    """

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    report: dict[str, Any] = {"aliases_applied": [], "aliases_shadowed": [], "defaults_applied": [], "values_normalized": []}
    flagged: set[str] = set()
    # Missing fields take the defaults of the requested template.
    design = default_design(template_of(data))
    supplied: dict[str, Any] = {}
    unknown: list[tuple[str | None, Any, Any]] = []
    if data is not None and not isinstance(data, Mapping):
        errors.append(_issue("E_DESIGN_TYPE", "$", "Design must be a JSON object."))
    elif data is not None:
        for key, value in data.items():
            if key in DESIGN_SECTIONS:
                if not isinstance(value, Mapping):
                    errors.append(_issue(_SECTION_CODES[key], key, f"{key} must be an object."))
                    continue
                for sub_key, sub_value in value.items():
                    path = f"{key}.{sub_key}" if isinstance(sub_key, str) else ""
                    if sub_key in DESIGN_SECTIONS[key] or path in _NESTED_ALIASES:
                        supplied[path] = sub_value
                    elif path in OPTIONAL_FIELDS and template_of(data) in OPTIONAL_FIELD_TEMPLATES[path]:
                        supplied[path] = sub_value
                    else:
                        unknown.append((key, sub_key, sub_value))
            elif isinstance(key, str) and (key in TOP_LEVEL_FIELDS or key in _FLAT_ALIASES):
                supplied[key] = value
            else:
                unknown.append((None, key, value))
        if "schema_version" not in supplied:
            warnings.append(
                _issue("W_SCHEMA_VERSION_DEFAULTED", "schema_version", f"schema_version is missing; {SCHEMA_VERSION} is assumed.")
            )
    errors += [_unknown_field(*entry) for entry in unknown[:_UNKNOWN_FIELD_REPORT_LIMIT]]
    if len(unknown) > _UNKNOWN_FIELD_REPORT_LIMIT:
        errors.append(_issue("E_UNKNOWN_FIELD", "$", f"{len(unknown) - _UNKNOWN_FIELD_REPORT_LIMIT} more unknown fields are not listed."))

    # Enumerated aliases are checked even where a nested field shadows them.
    mapped: dict[str, tuple[str, ...] | None] = {}
    for alias, targets, values in ALIASES:
        if values is None or alias not in supplied:
            continue
        raw = supplied[alias]
        mapped[alias] = values[raw] if isinstance(raw, str) and raw in values else None
        if mapped[alias] is None:
            allowed = ", ".join(map(repr, values))
            errors.append(_issue(FIELD_CODES[targets[0]], alias, f"{alias} must be one of {allowed} (got {_describe(raw)})."))

    def source_value(source: str, field: str) -> Any:
        if source in mapped:
            values = mapped[source]
            return None if values is None else values[_ALIAS_TARGETS[source].index(field)]
        return supplied[source]

    def same_value(field: str, first: Any, second: Any) -> bool:
        # Equal once canonical (on the layout grid, trimmed) and as JSON, so true is not 1.
        (one, problem), (other, other_problem) = _canonical_value(field, first), _canonical_value(field, second)
        return problem is None and other_problem is None and _canonical_json(one) == _canonical_json(other)

    conflicts: dict[str, list[tuple[str, str]]] = {}
    for field in CANONICAL_FIELDS:
        present = [source for source in (field, *_ALIAS_SOURCES[field]) if source in supplied]
        if not present:
            report["defaults_applied"].append(field)
            continue
        winner = present[0]
        value = source_value(winner, field)
        if winner != field and not (winner in mapped and mapped[winner] is None):
            report["aliases_applied"].append({"alias": winner, "field": field})
        for loser in present[1:]:
            report["aliases_shadowed"].append({"alias": loser, "field": field, "by": winner})
            # An invalid enumerated alias is already an error; it is not warned about again.
            if mapped.get(loser, ()) is not None and not same_value(field, source_value(loser, field), value):
                conflicts.setdefault(loser, []).append((field, winner))
        if winner in mapped and mapped[winner] is None:
            flagged.add(field)
        _set_field(design, field, value)
    for alias, pairs in conflicts.items():
        winners = list(dict.fromkeys(winner for _, winner in pairs))
        warnings.append(
            _issue(
                "W_ALIAS_SHADOWED",
                alias,
                f"{alias} is ignored for {', '.join(field for field, _ in pairs)}: "
                f"{', '.join(winners)} {'takes' if len(winners) == 1 else 'take'} precedence.",
            )
        )

    defaulted = set(report["defaults_applied"])
    for field in CANONICAL_FIELDS:
        if field in flagged:
            continue
        value = _get_field(design, field)
        canonical, problem = _canonical_value(field, value)
        if problem is not None:
            errors.append(_issue(FIELD_CODES[field], field, f"{field} must be {_EXPECTED[field]} ({problem})."))
            flagged.add(field)
            canonical = None
        elif field not in defaulted and _changed(value, canonical):
            reason = "whitespace trimmed" if field == "project_name" else f"rounded to the {GRID_DECIMALS}-decimal layout grid"
            report["values_normalized"].append({"field": field, "from": value, "to": canonical, "reason": reason})
        _set_field(design, field, canonical)
    if "matrix.mask" in supplied:
        _normalize_mask(design, supplied["matrix.mask"], errors, report, flagged)
    _normalize_row_sides(design, supplied.get("routing.row_sides"), errors, report, flagged)
    if "tail.bottom_length_mm" in defaulted and template_of(design) == TEMPLATE_ID and bus_sides(design) is None:
        # The generic template's straight Row channel keeps its own profile's default bottom tail (the bus's is 12 mm),
        # canonical as every value (7.0 is the number 7).
        design["tail"]["bottom_length_mm"] = _canonical_value("tail.bottom_length_mm", _GENERIC_CHANNEL_BOTTOM_TAIL_MM)[0]
    if "project_name" in defaulted:
        rows, columns = design["matrix"]["rows"], design["matrix"]["columns"]
        if _as_integer(rows) is not None and _as_integer(columns) is not None:
            design["project_name"] = f"Tactile FPC {rows}x{columns}"
    return design, errors, warnings, report, flagged


def _normalize_mask(design: dict[str, Any], raw: Any, errors: list, report: dict[str, Any], flagged: set[str]) -> None:
    """Canonical ``matrix.mask`` of a design whose canonical fields are set (rows and columns alias-resolved).

    ``null`` and the full rows x columns rectangle leave the key out (the
    unmasked design and its build id); integral floats become ints.  A value
    that is not an array of integer pairs is E_MASK_TYPE and becomes null,
    like a rejected leaf.  Ranges and shape are validate_design's.
    """

    if raw is None:
        return
    mask, problems = _mask_pairs(raw)
    if mask is None:
        errors.extend(problems)
        flagged.add("matrix.mask")
        design["matrix"]["mask"] = None
        return
    written = json.loads(_canonical_json(raw))  # the request's value, as JSON (not the caller's object)
    rows, columns = _as_integer(design["matrix"]["rows"]), _as_integer(design["matrix"]["columns"])
    if rows is not None and len(mask) == rows and all(pair == [1, columns] for pair in mask):
        report["values_normalized"].append(
            {"field": "matrix.mask", "from": written, "to": None, "reason": "the full rows x columns rectangle is the unmasked design"}
        )
        return
    design["matrix"]["mask"] = mask
    if _canonical_json(written) != _canonical_json(mask):
        report["values_normalized"].append(
            {"field": "matrix.mask", "from": written, "to": [list(pair) for pair in mask], "reason": "integral numbers written as integers"}
        )


def _normalize_row_sides(design: dict[str, Any], raw: Any, errors: list, report: dict[str, Any], flagged: set[str]) -> None:
    """Canonical ``routing.row_sides`` of a design whose canonical fields are set (``raw``: the request's value, ``None``
    when absent or null).

    ``left``, ``right`` and ``both`` (the diagonal Row bus) are kept.  On the
    generic template the key is always set: absent or null it takes
    :func:`_default_row_sides` (recorded in ``defaults_applied``), and
    ``channel`` is kept.  On the surface template absent, null and
    ``channel`` (recorded in ``values_normalized``) leave the key out: the
    straight Row channel and its build id.  Anything else is E_ROW_SIDES and
    becomes null, like a rejected leaf.
    """

    defaulted = template_of(design) in ROW_BUS_DEFAULT_TEMPLATES
    if raw is None:
        if defaulted:
            design["routing"]["row_sides"] = _default_row_sides(design)
            report["defaults_applied"].append("routing.row_sides")
        return
    if not _member(raw, ROW_SIDES_VALUES):
        errors.append(_issue("E_ROW_SIDES", "routing.row_sides", _row_sides_message(raw)))
        flagged.add("routing.row_sides")
        design["routing"]["row_sides"] = None
        return
    if raw == CHANNEL and not defaulted:
        report["values_normalized"].append(
            {"field": "routing.row_sides", "from": raw, "to": None, "reason": "the straight Row channel is this template's default"}
        )
        return
    design["routing"]["row_sides"] = raw


def _default_row_sides(design: Mapping[str, Any]) -> str:
    """The generic template's default ``routing.row_sides``: ``both``, or ``channel`` where the tails leave on opposite
    sides (the diagonal Row bus stacks both tails on one side) or the field is a strip of one row or one column (a bus
    of one lane, or beside one column: built on request only, see docs/API.md); with an invalid side or count the
    other checks report."""

    tail = design["tail"]
    row_side, column_side = tail.get("row_side"), tail.get("column_side")
    if _member(row_side, TAIL_SIDES) and _member(column_side, TAIL_SIDES) and _opposite_tails(row_side, column_side):
        return CHANNEL
    if 1 in (_as_integer(design["matrix"].get("rows")), _as_integer(design["matrix"].get("columns"))):
        return CHANNEL
    return "both"


def _opposite_tails(row_side: str, column_side: str) -> bool:
    return (TAIL_TURNS[row_side] - TAIL_TURNS[column_side]) % 4 == 2


def _row_sides_message(value: Any) -> str:
    return (
        f"routing.row_sides must be one of {', '.join(map(repr, ROW_SIDES_VALUES))} (got {_describe(value)}): the sides of the "
        f"diagonal Row bus, seen from outside the stack with the tails down, or {CHANNEL!r} for the straight Row channel."
    )


def _canonical_value(field: str, value: Any) -> tuple[Any, str | None]:
    """Canonical JSON value of a leaf, or ``(None, problem)`` for values JSON cannot carry.

    Floats are rounded to the layout grid (count fields only lose a zero
    fraction) and integral results become ints, so ``2`` and ``2.0`` are one
    value.  Values of the right JSON kind but the wrong type are kept for
    validation to report.
    """

    if value is None or isinstance(value, (bool, str)):
        return (value.strip() if field == "project_name" and isinstance(value, str) else value), None
    if isinstance(value, int):
        if abs(value) > MAX_JSON_INTEGER:
            return None, f"got {_describe(value)}"
        return value, None
    if isinstance(value, float):
        if not math.isfinite(value):
            return None, f"got {_describe(value)}"
        if field not in INTEGER_FIELDS:
            value = round6(value)  # the layout grid itself, so geometry and identity agree
        if value.is_integer() and abs(value) <= MAX_JSON_INTEGER:
            return int(value), None
        return value, None
    return None, f"got {_describe(value)}"


def _changed(raw: Any, canonical: Any) -> bool:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw) != float(canonical)
    return raw != canonical


def _unknown_field(section: str | None, key: Any, value: Any) -> dict[str, str]:
    path = _path(section, key)
    hint = ""
    if isinstance(key, str):
        if section is None and isinstance(value, Mapping) and any(
            isinstance(inner, str) and (inner in DESIGN_SECTIONS or inner in TOP_LEVEL_FIELDS or inner in _FLAT_ALIASES) for inner in value
        ):
            hint = f"; it looks like a wrapped design: send the object inside {key!r} itself as the request"
        elif section is not None and key in _FLAT_ALIASES:
            hint = f"; {key!r} is accepted only at the top level, as an alias of {', '.join(_ALIAS_TARGETS[key])}"
        elif path in OPTIONAL_FIELDS:
            hint = f"; {path} needs template_id {' or '.join(map(repr, sorted(OPTIONAL_FIELD_TEMPLATES[path])))}"
        else:
            hint = _suggestion(section, key)
    return _issue("E_UNKNOWN_FIELD", path, f"Unknown field {path}{hint}.")


def _suggestion(section: str | None, key: str) -> str:
    names = list(DESIGN_SECTIONS[section]) if section else [*TOP_LEVEL_FIELDS, *DESIGN_SECTIONS, *sorted(_FLAT_ALIASES)]
    if section:
        names += [alias.split(".", 1)[1] for alias in sorted(_NESTED_ALIASES) if alias.startswith(section + ".")]
    close = difflib.get_close_matches(key, names, n=1, cutoff=0.7)
    if close:
        return f" (did you mean {_path(section, close[0])}?)"
    elsewhere = [f"{other}.{key}" for other, keys in DESIGN_SECTIONS.items() if other != section and key in keys]
    return f" (did you mean {elsewhere[0]}?)" if elsewhere else ""


def _path(section: str | None, key: Any) -> str:
    """JSON path of a key: dotted for identifiers, bracketed and JSON-quoted otherwise."""

    text = key if isinstance(key, str) else str(key)
    if isinstance(key, str) and _IDENTIFIER.match(key):
        return f"{section}.{key}" if section else key
    return f"{section or '$'}[{json.dumps(text, ensure_ascii=True)}]"


def _describe(value: Any) -> str:
    """Short, ASCII-safe description of a rejected value for messages."""

    if value is None or isinstance(value, bool):
        return json.dumps(value)
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if value != value else ("Infinity" if value > 0 else "-Infinity")
    if isinstance(value, int):
        return str(value) if abs(value) <= MAX_JSON_INTEGER else "an integer beyond the portable JSON range of +/-(2^53 - 1)"
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value if len(value) <= 40 else value[:40] + "...", ensure_ascii=True)
    if isinstance(value, Mapping):
        return "an object"
    if isinstance(value, (list, tuple)):
        return "an array"
    return f"a {type(value).__name__} value"


def _get_field(design: Mapping[str, Any], field: str) -> Any:
    section, _, key = field.partition(".")
    return design[section][key] if key else design[section]


def _set_field(design: dict[str, Any], field: str, value: Any) -> None:
    section, _, key = field.partition(".")
    if key:
        design[section][key] = value
    else:
        design[section] = value


def _issue(code: str, field: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message, "field": field}


# --------------------------------------------------------------------------
# Identity and manifest.
# --------------------------------------------------------------------------


def _identity(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """Build identity of a normalized design (D14).

    ``design_sha256`` hashes the canonical design; ``build_sha256`` hashes
    ``{design_sha256, profile_sha256, generator, exporter}`` (canonical JSON),
    so a change of profile content or of either version gives a new build id.
    A template other than the generic one adds its version as ``template``,
    and a masked design :data:`MASK_VERSION` as ``mask``
    (:func:`template_identity`), to both.
    """

    design_sha256 = _sha256(_canonical_json(design))
    profile_sha256 = _sha256(_canonical_json(profile))
    versions = {"generator": GENERATOR_VERSION, "exporter": _exporter_version(), **template_identity(design)}
    build_sha256 = _sha256(_canonical_json({"design_sha256": design_sha256, "profile_sha256": profile_sha256, **versions}))
    slug = _slugify(design.get("project_name"))
    return {
        "build_id": f"{slug}-{build_sha256[:12]}",
        "build_sha256": build_sha256,
        "design_sha256": design_sha256,
        "profile_sha256": profile_sha256,
        **versions,
        "slug": slug,
        "profile": {"id": profile["id"], "revision": profile["revision"]},
    }


def _exporter_version() -> str:
    # Imported here: the exporter depends on the engine, not the other way round.
    from exporters.direct_gerber import EXPORTER_VERSION

    return EXPORTER_VERSION


def _manifest(
    identity: Mapping[str, Any], validation: Mapping[str, Any], boards: Mapping[str, Any], profile: Mapping[str, Any]
) -> dict[str, Any]:
    design_warnings = [issue for issue in validation["warnings"] if issue["code"] not in REQUEST_WARNING_CODES]
    return {
        "format": MANIFEST_FORMAT,
        "generator": identity["generator"],
        "exporter": identity["exporter"],
        "layout_format": LAYOUT_FORMAT,
        "deterministic": True,
        "build_id": identity["build_id"],
        "build_sha256": identity["build_sha256"],
        "design_sha256": identity["design_sha256"],
        "profile_sha256": identity["profile_sha256"],
        "slug": identity["slug"],
        "profile": dict(identity["profile"]),
        **{key: identity[key] for key in IDENTITY_EXTRAS if key in identity},
        "geometry_valid": not validation["errors"],
        "production_ready": False,
        "output_status": "geometry_only",
        "requires_final_jlc_review": True,
        "board_summary": {
            name: {
                "id": board["id"],
                "role": board["role"],
                "physical_side": board["physical_side"],
                **board["metrics"],
            }
            for name, board in boards.items()
        },
        "checks": {
            "error_count": len(validation["errors"]),
            "warning_count": len(design_warnings),
            "single_copper_fpc": True,
            "polyimide_stiffener_thickness_mm": profile["stackup"]["stiffener_thickness_mm"],
            "source_independent": True,
        },
    }


# --------------------------------------------------------------------------
# SVG top view.
# --------------------------------------------------------------------------

# Preview presentation (not manufacturing rules): margin around the outline,
# view label size relative to the board, and the pin-1 marker beyond the tip.
_SVG_PADDING_MM = 1.0
_SVG_LABEL_FRACTION = 0.025
_SVG_MIN_LABEL_MM = 1.0
_SVG_LABEL = "TOP VIEW &#183; copper side &#183; &#9650; pin 1"
# Narrow boards get a smaller label, sized with a generous advance for
# sans-serif text (Chromium with DejaVu Sans measures about 0.51 em per character).
_SVG_LABEL_EM_PER_CHARACTER = 0.62
_PIN1_GAP_MM = 0.15
_PIN1_DEPTH_MM = 0.6
_PIN1_HALF_WIDTH_MM = 0.3


def _svg_for_board(board: Mapping[str, Any]) -> str:
    """Return a standalone, safe SVG top view (copper side) of a board.

    Layout coordinates are the Gerber frame (Y up); SVG is Y down.  The
    geometry is drawn inside one ``matrix(1 0 0 -1 0 T)`` group with ``T =
    ymin + ymax`` of the outline, so the screen shows the board as a Gerber
    viewer does, seen from the copper side.  ``data-active-region`` is the
    taxel crossing field as ``x y width height`` in SVG user units after the
    flip, so the browser can register boards without redoing the transform.
    A masked board (``grid_registration.active_outline``) adds
    ``data-active-outline``, the crossing region P as ``x,y`` points in the
    same flipped user units, and draws a polygon field window as a
    ``<polygon class="opening">``.  One user unit is one millimetre.
    """

    min_x, min_y, max_x, max_y = bounds_of(board["outline"]["points"])
    flip = min_y + max_y
    width, height = max_x - min_x, max_y - min_y
    label_size = max(_SVG_MIN_LABEL_MM, _SVG_LABEL_FRACTION * max(width, height))
    # The label starts at the board's left edge and must end inside the view box.
    label_size = min(label_size, (width + _SVG_PADDING_MM) / (_SVG_LABEL_EM_PER_CHARACTER * len(html.unescape(_SVG_LABEL))))
    # The label sits in a band above the padding, which keeps the pin-1 marker zone clear.
    band = 1.6 * label_size
    view_box = (min_x - _SVG_PADDING_MM, min_y - _SVG_PADDING_MM - band, width + 2 * _SVG_PADDING_MM, height + 2 * _SVG_PADDING_MM + band)
    active = board["grid_registration"]["active_region"]
    active_region = (active["x"], flip - active["y"] - active["height"], active["width"], active["height"])
    active_outline = board["grid_registration"].get("active_outline")
    outline_attribute = "" if active_outline is None else f' data-active-outline="{_svg_points([x, flip - y] for x, y in active_outline)}"'
    outline_points = _svg_points(board["outline"]["points"])
    cutouts = "".join(
        f'<polygon class="cutout" points="{_svg_points(points)}"/>'
        for points in board["outline"].get("cutouts", [])
    )
    stiffener = "".join(
        f'<polygon class="stiffener" points="{_svg_points(item["points"])}"/>'
        for item in board["layers"]["bottom_stiffener"]
    )
    openings = "".join(
        f'<polygon class="opening" points="{_svg_points(item["points"])}"/>' if item.get("shape") == "polygon" else _svg_rect(item, "opening")
        for item in board["layers"]["top_coverlay_openings"]
    )
    electrodes = "".join(
        _svg_rect(item, "electrode") for item in board["layers"]["top_copper"]["electrodes"]
    )
    # Each route piece is drawn with its own width (thin fan-out, wide tail pieces).
    routes = "".join(
        f'<polyline class="route" stroke-width="{_svg_number(item["width_mm"])}" points="{_svg_points(item["points"])}"/>'
        for item in board["layers"]["top_copper"]["routes"]
    )
    pads = "".join(_svg_rect(item, "pad") for item in board["layers"]["top_copper"]["pads"])
    label = html.escape(f"{board['physical_side'] or 'unassigned'} {board['role']} FPC, top view (copper side)")
    caption_x = view_box[0] + _SVG_PADDING_MM
    caption_y = view_box[1] + 1.25 * label_size  # baseline: capitals and descenders stay inside the band
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_svg_numbers(view_box)}" role="img" '
        f'aria-label="{label}" data-view="top" data-active-region="{_svg_numbers(active_region)}"{outline_attribute}><style>'
        ".outline{fill:#f4d7a1;stroke:#20252b;stroke-width:.18}.cutout{fill:#fbfcfa;stroke:#20252b;stroke-width:.18}.stiffener{fill:#667085;opacity:.55}"
        ".opening{fill:#fff5bf;stroke:#b88700;stroke-width:.05}.electrode,.pad{fill:#d9672b;stroke:#8a3214;stroke-width:.04}"
        ".route{fill:none;stroke:#d9672b;stroke-linejoin:round;stroke-linecap:round}"
        ".pin1-marker{fill:#b42318}.view-label{fill:#20252b;font-family:sans-serif}"
        "</style>"
        f'<g transform="matrix(1 0 0 -1 0 {_svg_number(flip)})">'
        f'<polygon class="outline" points="{outline_points}"/>{cutouts}{stiffener}{openings}{routes}{electrodes}{pads}{_pin1_marker(board)}'
        "</g>"
        f'<text class="view-label" x="{_svg_number(caption_x)}" y="{_svg_number(caption_y)}" font-size="{_svg_number(label_size)}">'
        f"{_SVG_LABEL}</text></svg>"
    )


def _pin1_marker(board: Mapping[str, Any]) -> str:
    """A triangle beyond the tail tip pointing at the pin-1 contact (layout coordinates)."""

    pad = next((pad for pad in board["layers"]["top_copper"]["pads"] if pad.get("pin") == 1), None)
    if pad is None:
        return ""
    min_x, min_y, max_x, max_y = rect_bounds(pad)
    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
    tail = board["tail"]["bounds"]
    side = board["tail"]["side"]
    gap, depth, half = _PIN1_GAP_MM, _PIN1_GAP_MM + _PIN1_DEPTH_MM, _PIN1_HALF_WIDTH_MM
    if side in ("bottom", "top"):
        edge, sign = (tail["y"], -1) if side == "bottom" else (tail["y"] + tail["height"], 1)
        points = [[center_x, edge + sign * gap], [center_x - half, edge + sign * depth], [center_x + half, edge + sign * depth]]
    else:
        edge, sign = (tail["x"], -1) if side == "left" else (tail["x"] + tail["width"], 1)
        points = [[edge + sign * gap, center_y], [edge + sign * depth, center_y - half], [edge + sign * depth, center_y + half]]
    title = html.escape(f"pin 1 ({pad.get('net')})")
    return f'<polygon class="pin1-marker" points="{_svg_points(points)}"><title>{title}</title></polygon>'


def _svg_rect(item: Mapping[str, Any], css_class: str) -> str:
    min_x, min_y, max_x, max_y = rect_bounds(item)
    return (
        f'<rect class="{css_class}" x="{_svg_number(min_x)}" y="{_svg_number(min_y)}" '
        f'width="{_svg_number(max_x - min_x)}" height="{_svg_number(max_y - min_y)}"/>'
    )


def _svg_points(points: Iterable[list[float]]) -> str:
    return " ".join(f"{_svg_number(point[0])},{_svg_number(point[1])}" for point in points)


def _svg_numbers(values: Iterable[float]) -> str:
    return " ".join(_svg_number(value) for value in values)


def _svg_number(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


# --------------------------------------------------------------------------
# Small helpers.
# --------------------------------------------------------------------------


def _as_integer(value: Any) -> int | None:
    """``value`` as an int if it is an integer or an integral float (not a bool)."""

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return None


def _is_number(value: Any) -> bool:
    """A finite JSON number (integers within the portable range, so float() cannot overflow)."""

    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return abs(value) <= MAX_JSON_INTEGER
    return isinstance(value, float) and math.isfinite(value)


def _member(value: Any, allowed: Iterable[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _deduplicate_issues(validation: dict[str, Any]) -> None:
    for key in ("errors", "warnings"):
        seen: set[tuple[str, str, str]] = set()
        values: list[dict[str, str]] = []
        for issue in validation[key]:
            issue_key = (issue["code"], issue["field"], issue["message"])
            if issue_key not in seen:
                seen.add(issue_key)
                values.append(issue)
        validation[key] = values


def _slugify(value: Any) -> str:
    """Return a portable deterministic artifact prefix without dependencies.

    Names without ASCII letters or digits (for example all-Chinese names) get
    ``tactile-fpc-`` plus 8 hex digits of the name's SHA-256, so they do not
    collapse onto one prefix.
    """

    text = value.strip() if isinstance(value, str) else ""
    pieces: list[str] = []
    previous_dash = False
    for char in text.lower():
        if char.isascii() and char.isalnum():
            pieces.append(char)
            previous_dash = False
        elif not previous_dash:
            pieces.append("-")
            previous_dash = True
    slug = "".join(pieces).strip("-")[:48].strip("-")
    if slug:
        return slug
    return "tactile-fpc-" + hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()[:8]
