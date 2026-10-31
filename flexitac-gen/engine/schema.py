"""Machine-readable input contract: JSON Schema, UI limits and issue codes.

Everything here is generated from the locked profile and the field and alias
tables of :mod:`engine.core`, so the schema an agent reads, the limits the
form uses and the rules the engine enforces cannot drift apart.  Each profile
belongs to one design template (``engine.profile.profile_template``): the
schema and limits of a profile are those of its template, with its defaults
(``design_schema(load_profile("surface_matrix_v1"))`` for the surface
template).  The generic template builds its default, the diagonal Row bus,
with the surface profile (``engine.core.rules_template``): its bounds that
differ (columns, tail lengths) are the bus's, the straight Row channel's
under ``channel`` (``x-channel`` in the JSON Schema).  Cross-field
rules (electrode gap, role mapping, tail sides, connector size, board size)
are listed in ``x-cross-field-rules`` and enforced by the engine, which
reports them with the codes in ``x-error-codes``.
"""

from __future__ import annotations

import json
import math
from typing import Any, Mapping

from .core import (
    ALIASES,
    CANONICAL_FIELDS,
    CHANNEL_ORDERS,
    DESIGN_SECTIONS,
    GRID_DECIMALS,
    MASK_INACTIVE_GAP_WARNING_MM,
    MASK_TEMPLATES,
    OPTIONAL_FIELDS,
    ROW_BUS_DEFAULT_TEMPLATES,
    ROW_SIDES_VALUES,
    ROLES,
    SCHEMA_VERSION,
    TAIL_SIDES,
    TEMPLATE_VERSIONS,
    _GENERIC_CHANNEL_BOTTOM_TAIL_MM,
    _canonical_json,
    _sha256,
    default_design,
)
from .diagonal import CHANNEL, COLUMN_V_CAP_DEG, REGULAR_TURN_DEG, ROW_BUS_VERSION, ROW_SIDES, SIDE_STRAIGHTEN_MM
from .geometry import round6
from .profile import SURFACE_TEMPLATE_ID, copper_weight_oz, fabrication_minimum, load_profile, profile_template

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
# project_name: no control characters or unpaired surrogates (E_PROJECT_NAME)
# and at least one other non-space character.  Written with escapes that
# ECMA-262 (u flag) and Python's re read alike.
_NAME_CHARACTER = "[^\\x00-\\x1f\\x7f-\\x9f\\ud800-\\udfff]"
PROJECT_NAME_PATTERN = f"^{_NAME_CHARACTER}*[^\\s\\x00-\\x1f\\x7f-\\x9f\\ud800-\\udfff]{_NAME_CHARACTER}*$"

# Every issue code the engine emits: code -> (source, meaning).
ERROR_CODES: dict[str, tuple[str, str]] = {
    # Request structure and normalization.
    "E_DESIGN_TYPE": ("request", "The design is not a JSON object."),
    "E_UNKNOWN_FIELD": ("request", "A key outside tactile-fpc-design/v1 and its aliases; field is its JSON path. Wrapper objects such as {\"design\": {...}} are rejected the same way."),
    "E_MATRIX_OBJECT": ("request", "matrix is not an object."),
    "E_TAIL_OBJECT": ("request", "tail is not an object."),
    "E_CONNECTOR_OBJECT": ("request", "connector is not an object."),
    "E_ROUTING_OBJECT": ("request", "routing is not an object."),
    "E_SCHEMA_VERSION": ("request", f"schema_version is present but is not {SCHEMA_VERSION!r}."),
    "E_TEMPLATE_UNSUPPORTED": (
        "request",
        f"template_id is not one of {', '.join(map(repr, TEMPLATE_VERSIONS))} (null included), or the profile given belongs to another template.",
    ),
    "E_PROJECT_NAME": ("input", "project_name is not a non-empty string of at most limits.maximum_project_name_length characters after trimming, or contains control characters."),
    # Input rules.
    "E_ROWS_INTEGER": ("input", "matrix.rows is not an integer (an integral float such as 12.0 is accepted)."),
    "E_ROWS_RANGE": ("input", "matrix.rows is outside limits.minimum_rows..maximum_rows."),
    "E_COLUMNS_INTEGER": ("input", "matrix.columns is not an integer (an integral float such as 32.0 is accepted)."),
    "E_COLUMNS_RANGE": ("input", "matrix.columns is outside limits.minimum_columns..maximum_columns."),
    "E_COLUMNS_LANE_CAPACITY": ("input", "matrix.columns exceeds fanout.maximum_lanes x fanout.maximum_channels_per_lane."),
    "E_NUMERIC": ("input", "A millimetre field is not a finite number (NaN, Infinity, strings, booleans and integers beyond 2^53 included)."),
    "E_PITCH_RANGE": ("input", "A pitch is outside limits.minimum_pitch_mm..maximum_pitch_mm."),
    "E_TAXEL_SIZE": ("input", "An electrode width is negative."),
    "E_ELECTRODE_WIDTH": ("input+drc", "An electrode is narrower than routing.min_electrode_width_mm."),
    "E_ELECTRODE_GAP": ("input", "taxel width + routing.min_electrode_gap_mm exceeds the pitch; the message gives the largest legal width."),
    "E_TAIL_LENGTH": ("input", "A tail length is outside tail.minimum_length_mm..limits.maximum_tail_length_mm."),
    "E_TAIL_SIDE": ("input", "A tail side (or the connector_side alias) is not bottom, top, left or right."),
    "E_TAIL_SIDE_PARALLEL": ("input", "tail.column_side is a quarter turn from tail.row_side, which makes the electrodes parallel; the message lists the allowed sides."),
    "E_ROLE_MAPPING": ("input", "A role_mapping position is not rows or columns (field role_mapping.top/.bottom), both positions name one role (field role_mapping), or the row_fpc_position alias is invalid."),
    "E_CHANNEL_ORDER": ("input", "A channel order (or the scan_order alias) is not ascending/descending (forward/reverse for scan_order)."),
    "E_CONNECTOR_PINS": ("input", "A connector size is not null or an integer between the channel count and connector.maximum_pins."),
    "E_TRACE_WIDTH": ("input", "routing.trace_width_mm is outside limits.minimum_trace_width_mm..maximum_trace_width_mm."),
    "E_TRACE_SPACE": ("input", "routing.trace_space_mm is outside limits.minimum_trace_space_mm..maximum_trace_space_mm."),
    # The field mask (matrix.mask, surface template only).
    "E_MASK_TYPE": ("request", "matrix.mask is not null or an array of [first, last] integer pairs (field matrix.mask, or matrix.mask[i] for one entry)."),
    "E_MASK_ROWS": ("input", "matrix.mask does not have one [first, last] pair per row (matrix.rows)."),
    "E_MASK_RANGE": ("input", "A row's span (field matrix.mask[i]) is not 1 <= first <= last <= matrix.columns."),
    "E_MASK_DISCONNECTED": ("input", "Two consecutive rows share no column (field matrix.mask[i], the lower row)."),
    "E_MASK_COLUMN_EMPTY": ("input", "A column has no taxel: the mask must span every column of matrix.columns."),
    "E_MASK_COLUMN_GAP": ("input", "A column's taxels are not consecutive rows."),
    # The Row traces (routing.row_sides): the diagonal Row bus or the straight Row channel.
    "E_ROW_SIDES": (
        "input",
        f"routing.row_sides is not one of {', '.join(map(repr, ROW_SIDES_VALUES))} (absent or null: the template's default, "
        f"'both' on generic_matrix_v1, the straight Row channel on surface_matrix_v1).",
    ),
    "E_ROW_BUS_TAILS": (
        "input",
        "routing.row_sides 'left', 'right' or 'both' with tail.row_side and tail.column_side opposite: the diagonal Row bus puts "
        "both tails on one side (a quarter turn is E_TAIL_SIDE_PARALLEL; 'channel' takes opposite tails).",
    ),
    # Feasibility (before geometry).
    "E_BOARD_SIZE": ("feasibility+drc", "An outline exceeds the fabrication maximum (either orientation); the message lists verified bounds that fit."),
    "E_MASK_ROUTING": (
        "feasibility",
        "The boards of this mask cannot be built yet (field matrix.mask, or matrix.mask[i] naming the first row a straight construction refuses, with the fix).",
    ),
    "E_ROW_BUS_INFEASIBLE": (
        "build",
        f"The diagonal Row bus ({ROW_BUS_VERSION}) cannot order or place its lanes (field routing.row_sides); no boards are built.",
    ),
    # Locked profile consistency.
    "E_PROFILE_MISSING": ("profile", "A profile section or rule is missing or not a positive finite number."),
    "E_PROFILE_FAB_LIMIT": ("profile", "A profile design rule is looser than the published fabrication capability."),
    "E_PROFILE_INCONSISTENT": ("profile", "Profile rules contradict each other."),
    "E_PROFILE_PAD_SPACE": ("profile", "Connector contacts or their leads violate the pad spacing rules."),
    "E_PROFILE_ROUTE_SPACE": ("profile", "Routes at the contact pitch cannot keep the largest trace space the limits allow."),
    # Whole-board DRC on the generated layout (field is a boards.<row|column>.* path).
    "E_ROUTE_CLEARANCE": ("drc", "Route-to-route clearance between different nets."),
    "E_PAD_TRACE_CLEARANCE": ("drc", "Contact-to-other-net route clearance."),
    "E_PAD_CLEARANCE": ("drc", "Contact-to-contact clearance."),
    "E_ELECTRODE_CLEARANCE": ("drc", "Electrode-to-electrode clearance."),
    "E_ELECTRODE_ROUTE_CLEARANCE": ("drc", "Electrode-to-other-net route clearance."),
    "E_ELECTRODE_PAD_CLEARANCE": ("drc", "Electrode-to-contact clearance."),
    "E_COPPER_EDGE_CLEARANCE": ("drc", "Copper-to-board-edge clearance."),
    "E_ROUTE_EDGE_CLEARANCE": ("drc", "Route-to-board-edge clearance."),
    "E_COPPER_OUTLINE": ("drc", "Copper outside the outline."),
    "E_COPPER_CUTOUT_CLEARANCE": ("drc", "Copper-to-routed-slot clearance."),
    "E_ACTIVE_MARGIN": ("drc", "Board material around the active field below routing.active_edge_clearance_mm."),
    "E_COVERLAY_OUTLINE": ("drc", "A coverlay opening crosses the outline."),
    "E_COVERLAY_BRIDGE": ("drc", "A coverlay bridge narrower than coverlay.coverlay_min_bridge_mm."),
    "E_COVERLAY_TRACE_CLEARANCE": ("drc", "A coverlay opening too close to another net's trace."),
    "E_CONTACT_EXPOSURE": ("drc", "The contact window does not expose the contacts as required."),
    "E_STIFFENER_OUTLINE": ("drc", "The stiffener leaves the outline."),
    "E_STIFFENER_ZONE": ("drc", "The stiffened connector zone or the straight flexible tail beyond it is wrong."),
    "E_OUTLINE_SELF_INTERSECTION": ("drc", "The outline is not a simple polygon."),
    "E_CUTOUT_OUTLINE": ("drc", "A routed slot is not inside the outline."),
    "E_CONCAVE_CORNER": ("drc", "An unfilleted or too tightly filleted concave outline corner."),
    "E_NECK_WIDTH": ("drc", "The board is narrower than the tail between tail and body."),
    "E_CONNECTIVITY": ("drc", "A net's tail and fan-out pieces do not join its contact, each other and its electrode, or an NC contact touches copper."),
    "E_ROUTE_WIDTH": ("drc", "A route piece is not its width (fan-out: routing.trace_width_mm, tail: routing.finger_trace_width_mm) or is below the copper's fabrication minimum."),
    "E_CONNECTOR_TAIL": ("drc", "Tail width or contact geometry differs from the connector model."),
    "E_REGISTRATION": (
        "drc",
        "Row and Column electrodes are not orthogonal or their taxel grids differ; for a diagonal Row bus also a stacked trace "
        "over the other board's electrodes or its field window, tails that leave on different sides, or outlines that "
        "differ over the taxel field, where the two boards share one outline (outside it the boards and their stacked "
        "tails may overlap).",
    ),
}
WARNING_CODES: dict[str, tuple[str, str]] = {
    "W_SCHEMA_VERSION_DEFAULTED": ("request", f"schema_version was missing; {SCHEMA_VERSION} was assumed."),
    "W_ALIAS_SHADOWED": ("request", "An alias was ignored because a nested field (or a higher-precedence alias) gave the same field another value."),
    "W_HIGH_FILL_FACTOR": ("input", "An electrode uses more than limits.high_fill_factor_warning of its pitch."),
    "W_LARGE_MATRIX": ("input", "rows x columns exceeds limits.large_matrix_warning_taxels."),
    "W_MASK_INACTIVE_GAP": (
        "input",
        f"The mask's inactive crossings are closer than {MASK_INACTIVE_GAP_WARNING_MM:g} mm to the electrodes beside them (the larger "
        "electrode gap less the overhang); a misregistered stack may make them read.",
    ),
    "W_STACK_TRACE_WINDOW": (
        "drc",
        "A diagonal Row bus pair has a stacked trace closer to the other board's field window than the coverlay "
        "opening-to-trace rule (fine pitches).",
    ),
}


class DesignJSONError(ValueError):
    """A request document is not strict JSON; the message is safe to return to a client."""


def load_design_json(document: bytes | str) -> Any:
    """Parse a request document as strict JSON.

    UTF-8 only (a leading byte-order mark is ignored); NaN, Infinity and
    numbers that overflow a float are rejected, as are duplicate object keys,
    too deep nesting and over-long integer literals.  Raises
    :class:`DesignJSONError`, never another exception type.
    """

    if isinstance(document, bytes):
        try:
            document = document.decode("utf-8")
        except UnicodeDecodeError as error:
            raise DesignJSONError(f"the document is not valid UTF-8 (byte {error.start}).") from None
    if document.startswith("\ufeff"):
        document = document[1:]
    try:
        return json.loads(document, parse_constant=_reject_constant, parse_float=_finite_float, object_pairs_hook=_unique_keys)
    except DesignJSONError:
        raise
    except json.JSONDecodeError as error:
        raise DesignJSONError(f"invalid JSON: {error.msg} at line {error.lineno} column {error.colno}.") from None
    except RecursionError:
        raise DesignJSONError("the JSON document is nested too deeply.") from None
    except ValueError:
        # Python's limit on integer literal length.
        raise DesignJSONError("a JSON integer literal is too long.") from None


def _reject_constant(name: str) -> Any:
    raise DesignJSONError(f"{name} is not a JSON number.")


def _finite_float(text: str) -> float:
    value = float(text)
    if math.isinf(value):
        raise DesignJSONError(f"the number {text[:40]} is out of range.")
    return value


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DesignJSONError(f"duplicate object key {json.dumps(key, ensure_ascii=True)}.")
        result[key] = value
    return result


def _columns(profile: Mapping[str, Any]) -> tuple[int, str]:
    """``matrix.columns``' maximum under a profile and its fan-out lanes in words."""

    fanout = profile["fanout"]
    lanes, per_lane = int(fanout["maximum_lanes"]), int(fanout["maximum_channels_per_lane"])
    words = (
        f"up to {per_lane} use one fan-out lane, more use {lanes} lanes merging into one connector"
        if lanes > 1 else f"all in one fan-out lane of up to {per_lane}"
    )
    return min(int(profile["limits"]["maximum_columns"]), lanes * per_lane), words


def row_bus_profile(profile: Mapping[str, Any] | None = None) -> Mapping[str, Any] | None:
    """The profile the diagonal Row bus of a profile's template is built with where it is another one: the surface
    profile for the generic template (``engine.core.rules_template``), else ``None`` (the template's own)."""

    profile = load_profile() if profile is None else profile
    return load_profile(SURFACE_TEMPLATE_ID) if profile_template(profile) in ROW_BUS_DEFAULT_TEMPLATES else None


def field_specs(profile: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Kind, bounds and meaning of every canonical design field, from the profile.

    On the generic template the bounds that the diagonal Row bus's profile
    sets otherwise (:func:`row_bus_profile`: ``matrix.columns``, the tail
    lengths) are the bus's, its default; each such field's ``channel`` holds
    the straight Row channel's (this profile's) bounds.
    """

    profile = load_profile() if profile is None else profile
    limits = profile["limits"]
    routing = profile["routing"]
    connector = profile["connector"]
    step = 10.0 ** -GRID_DECIMALS
    gap = float(routing["min_electrode_gap_mm"])
    pitch = {"type": "number", "unit": "mm", "minimum": limits["minimum_pitch_mm"], "maximum": limits["maximum_pitch_mm"], "step": step}
    width = {"type": "number", "unit": "mm", "minimum": routing["min_electrode_width_mm"], "maximum": round6(float(limits["maximum_pitch_mm"]) - gap), "step": step}
    template = profile_template(profile)
    bus = row_bus_profile(profile)
    # The bounds of the template's default construction: the bus's profile on the generic template.
    rules = profile if bus is None else bus
    length = {"type": "number", "unit": "mm", "minimum": rules["tail"]["minimum_length_mm"], "maximum": limits["maximum_tail_length_mm"], "step": step}
    most, words = _columns(rules)
    columns = f"Column electrodes, {words}."
    tails = ""
    if bus is not None:
        channel_most, channel_words = _columns(profile)
        columns = (
            f"Column electrodes. The diagonal Row bus (built with {bus['id']}): {words}; routing.row_sides {CHANNEL!r} (the "
            f"straight Row channel, {profile['id']}): at most {channel_most}, {channel_words}."
        )
        tails = (
            f" At least {rules['tail']['minimum_length_mm']:g} mm with the diagonal Row bus ({bus['id']}), "
            f"{profile['tail']['minimum_length_mm']:g} mm with routing.row_sides {CHANNEL!r} ({profile['id']})."
        )
    finger, pitch_mm = float(routing["finger_trace_width_mm"]), float(connector["pad_pitch_mm"])
    minimum_width, minimum_space = fabrication_minimum(profile)
    # JLC's trace minimums in mil, as its capabilities page states them (1 mil = 0.0254 mm).
    mils = f"{round(minimum_width / 0.0254, 2):g}/{round(minimum_space / 0.0254, 2):g} mil"

    def trace(kind: str, what: str) -> dict[str, Any]:
        return {
            "type": "number", "unit": "mm", "minimum": limits[f"minimum_trace_{kind}_mm"], "maximum": limits[f"maximum_trace_{kind}_mm"],
            "step": step, "description": what,
        }

    def pins(role: str) -> dict[str, Any]:
        minimum = limits[f"minimum_{role}"]
        return {
            "type": "integer", "nullable": True, "minimum": minimum, "maximum": connector["maximum_pins"], "step": 1,
            "description": f"{connector['pad_pitch_mm']:g} mm-pitch ZIF connector positions of the {role[:-1]} tail; null = one per channel. "
            f"At least matrix.{role}; unused positions get isolated NC contacts.",
        }

    specs: dict[str, dict[str, Any]] = {
        "schema_version": {"type": "string", "const": SCHEMA_VERSION, "description": "Design schema version; missing means this version (with a warning)."},
        "template_id": {
            "type": "string", "const": template,
            "description": (
                f"Design template of this schema; the templates are {', '.join(map(repr, TEMPLATE_VERSIONS))}, each with its own "
                "profile, limits and schema."
            ),
        },
        "project_name": {
            "type": "string", "min_length": 1, "max_length": int(limits["maximum_project_name_length"]),
            "description": (
                f"Free name without control characters, at most {int(limits['maximum_project_name_length'])} characters after trimming; "
                "a missing name becomes 'Tactile FPC <rows>x<columns>'. Names without ASCII letters or digits get a hash-based slug."
            ),
        },
        "matrix.rows": {
            "type": "integer", "minimum": limits["minimum_rows"], "maximum": limits["maximum_rows"], "step": 1,
            "description": "Row electrodes (channels of the Row FPC).",
        },
        "matrix.columns": {
            "type": "integer", "minimum": limits["minimum_columns"], "maximum": most, "step": 1,
            "description": columns,
        },
        "matrix.pitch_x_mm": dict(pitch, description="Column electrode pitch."),
        "matrix.pitch_y_mm": dict(pitch, description="Row electrode pitch."),
        "matrix.taxel_width_mm": dict(width, description=f"Column electrode width; at most pitch_x_mm - {gap:g} (routing.min_electrode_gap_mm)."),
        "matrix.taxel_height_mm": dict(width, description=f"Row electrode width; at most pitch_y_mm - {gap:g} (routing.min_electrode_gap_mm)."),
        "tail.top_length_mm": dict(length, description="Tail length of the FPC physically on top of the stack." + tails),
        "tail.bottom_length_mm": dict(
            length, description="Tail length of the FPC physically at the bottom of the stack." + tails
            + (f" Absent: {default_design()['tail']['bottom_length_mm']:g} mm with the bus, "
               f"{_GENERIC_CHANNEL_BOTTOM_TAIL_MM:g} mm with the straight Row channel." if bus is not None else "")
        ),
        "tail.row_side": {"type": "string", "enum": list(TAIL_SIDES), "description": "Side the Row FPC tail exits (the whole board is rotated)."},
        "tail.column_side": {"type": "string", "enum": list(TAIL_SIDES), "description": "Side the Column FPC tail exits; equal or opposite to tail.row_side."},
        "connector.row_pins": pins("rows"),
        "connector.column_pins": pins("columns"),
        "role_mapping.top": {"type": "string", "enum": list(ROLES), "description": "Board physically on top of the stack."},
        "role_mapping.bottom": {"type": "string", "enum": list(ROLES), "description": "Board physically at the bottom of the stack."},
        "channel_order.rows": {"type": "string", "enum": list(CHANNEL_ORDERS), "description": "Row pin assignment; ascending puts ROW_01 on pin 1."},
        "channel_order.columns": {"type": "string", "enum": list(CHANNEL_ORDERS), "description": "Column pin assignment; ascending puts COL_01 on pin 1."},
        "routing.trace_width_mm": trace(
            "width",
            f"Width of the thin fan-out traces between the electrodes and the tail, where they run as a bundle at width + spacing "
            f"pitch; JLCPCB's minimum for {copper_weight_oz(profile):g} oz copper is {mils} ({minimum_width:g} mm). In the tail the "
            f"traces widen to {finger:g} mm (routing.finger_trace_width_mm) at the {pitch_mm:g} mm contact pitch.",
        ),
        "routing.trace_space_mm": trace(
            "space",
            f"Copper gap between neighbouring fan-out traces in the bundle, at most the {round(pitch_mm - finger, 6):g} mm gap of the "
            f"{finger:g} mm gold-finger traces at the {pitch_mm:g} mm contact pitch (so width + spacing stays within that pitch); "
            f"JLCPCB's minimum for {copper_weight_oz(profile):g} oz copper is {mils} ({minimum_space:g} mm).",
        ),
    }
    if template in MASK_TEMPLATES:
        # The field mask: optional, no default (absent or null is the full rectangle).
        specs["matrix.mask"] = {
            "type": "mask", "nullable": True, "min_items": limits["minimum_rows"], "max_items": limits["maximum_rows"],
            "index_minimum": 1, "index_maximum": specs["matrix.columns"]["maximum"],
            "description": (
                "Field mask: one [first, last] pair of 1-based COL indices per row, ROW_01 first; taxel (r, c) is active when "
                "first <= c <= last of row r. Consecutive rows overlap, each column's taxels are consecutive rows and every "
                "column is used. Inactive positions have no crossing and read 0; null or the full rectangle is the unmasked field."
            ),
        }
    if bus is not None:
        # The straight Row channel's own bounds (this profile's) where the bus's differ.
        specs["matrix.columns"]["channel"] = {"maximum": channel_most}
        for field in ("tail.top_length_mm", "tail.bottom_length_mm"):
            specs[field]["channel"] = {"minimum": profile["tail"]["minimum_length_mm"]}
        specs["tail.bottom_length_mm"]["channel"]["default"] = _GENERIC_CHANNEL_BOTTOM_TAIL_MM
        absent = (
            f"On this template the bus is built with CAD mode's rule set ({bus['id']}: the same boards as on the surface "
            f"template), the straight Row channel with this template's profile ({profile['id']}). Null or absent: 'both', or "
            "'channel' where the tails leave on opposite sides or the field is a single row or column (recorded in "
            "validation.normalization.defaults_applied); the design always carries the value."
        )
    else:
        absent = "Null, absent or 'channel': the straight Row channel (the key is left out of the design, so its build id holds)."
    caps = (bus or profile)["fanout"]
    specs["routing.row_sides"] = {
        "type": "string", "enum": list(ROW_SIDES_VALUES), "nullable": True,
        "description": (
            f"Row traces: the diagonal Row bus ({ROW_BUS_VERSION}) or {CHANNEL!r}, the straight Row channel beside the "
            "field. The bus: the sides the row traces take, seen from outside the stack with the tails down; 'both' splits "
            "them (ROW_01, 03, ... on one side, the even rows on the other), meets them in a funnel and folds the Row contact "
            "order; 'left' or 'right' takes every row to that side, fanning in under the field. The Row tail is centred on the "
            "field in every side mode, as the Column tail, so it lies within the sensor's width wherever it is narrower than "
            f"the field. Its fans run at whole-degree caps of {caps.get('minimum_taper_angle_deg', caps['maximum_taper_angle_deg']):g}-"
            f"{caps['maximum_taper_angle_deg']:g} degrees. The Column traces converge in one V straight into their contacts, "
            f"at most {COLUMN_V_CAP_DEG:g} degrees where that roots the tails no deeper (so the fans keep their steepest "
            "cap), its tail centred. Both boards "
            "share one outline down to their tail roots: the tails leave one bottom edge (the shallower root moves down to "
            "the deeper), stacked where they meet. The outlines are regular: "
            f"no corner turns by less than {REGULAR_TURN_DEG:g} degrees but on a fillet (flatter runs become straight edges "
            "outside them), and each side from the tip corner down to its widest point is one straight line where one "
            f"line encloses it within {SIDE_STRAIGHTEN_MM:g} mm. Both tails must leave on one side. " + absent
        ),
    }
    return specs


def input_limits(profile: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Per-field limits for forms: the field specs plus default and accepted aliases.

    The limits and defaults are those of the profile's template (the generic
    one without a profile).
    """

    defaults = default_design(profile_template(profile))
    limits = {}
    for field, spec in field_specs(profile).items():
        section, _, key = field.partition(".")
        entry = dict(spec)
        entry["default"] = defaults[section].get(key) if field in OPTIONAL_FIELDS else defaults[section][key] if key else defaults[section]
        entry["aliases"] = [alias for alias, targets, _ in ALIASES if field in targets]
        limits[field] = entry
    return limits


def cross_field_rules(profile: Mapping[str, Any]) -> list[str]:
    routing = profile["routing"]
    limits = profile["limits"]
    rules = [
        f"matrix.taxel_width_mm + {routing['min_electrode_gap_mm']} <= matrix.pitch_x_mm and matrix.taxel_height_mm + "
        f"{routing['min_electrode_gap_mm']} <= matrix.pitch_y_mm (E_ELECTRODE_GAP).",
        "role_mapping.top and role_mapping.bottom are 'rows' and 'columns' in either order (E_ROLE_MAPPING).",
        "tail.column_side equals tail.row_side or is opposite to it (E_TAIL_SIDE_PARALLEL).",
        "connector.row_pins >= matrix.rows and connector.column_pins >= matrix.columns when set (E_CONNECTOR_PINS).",
        f"Each board outline fits {limits['maximum_outline_short_side_mm']:g} x {limits['maximum_outline_long_side_mm']:g} mm "
        "in either orientation (E_BOARD_SIZE).",
        f"Numbers are taken on the 1e-{GRID_DECIMALS} mm layout grid (rounded to {GRID_DECIMALS} decimals) before validation and hashing, "
        "so the engine also accepts a value within half a grid step outside a bound.",
        "project_name is trimmed (spaces, tabs, line breaks) before its length and characters are checked, so the engine also "
        "accepts surrounding whitespace that maxLength or the pattern reject.",
        "Nested fields win over flat aliases; among aliases the specific names win (x-alias-precedence). An overridden alias is "
        "ignored with W_ALIAS_SHADOWED (the values of row_fpc_position, connector_side and scan_order are still checked); "
        "this schema checks every alias value.",
    ]
    if profile_template(profile) in MASK_TEMPLATES:
        rules.append(
            "matrix.mask, when set, has one [first, last] pair per matrix.rows (E_MASK_ROWS) with 1 <= first <= last <= "
            "matrix.columns (E_MASK_RANGE); consecutive rows share a column (E_MASK_DISCONNECTED), every column has a taxel "
            "(E_MASK_COLUMN_EMPTY) and each column's taxels are consecutive rows (E_MASK_COLUMN_GAP). The full rectangle is "
            "normalized away (the unmasked design)."
        )
    rules.append(
        f"routing.row_sides, when set, is one of {', '.join(map(repr, ROW_SIDES_VALUES))} (E_ROW_SIDES); "
        f"{', '.join(map(repr, ROW_SIDES))} need tail.row_side equal to tail.column_side (opposite sides: E_ROW_BUS_TAILS)."
    )
    bus = row_bus_profile(profile)
    if bus is not None:
        rules.append(
            f"The Row traces pick the rule set: the diagonal Row bus (routing.row_sides {', '.join(map(repr, ROW_SIDES))}; absent, "
            f"'both' unless the tails are opposite or the field is a strip) is built with {bus['id']} (this schema's bounds), "
            f"the straight Row channel ({CHANNEL!r}) with {profile['id']}: its bounds under each field's x-channel "
            "(matrix.columns: E_COLUMNS_RANGE, E_COLUMNS_LANE_CAPACITY; tail lengths: E_TAIL_LENGTH)."
        )
    return rules


def issue_codes() -> dict[str, dict[str, dict[str, str]]]:
    """The issue-code catalogue: ``{errors: {code: {source, meaning}}, warnings: {...}}``."""

    return {
        kind: {code: {"source": source, "meaning": meaning} for code, (source, meaning) in table.items()}
        for kind, table in (("errors", ERROR_CODES), ("warnings", WARNING_CODES))
    }


def design_schema(profile: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """JSON Schema (draft 2020-12) of a ``tactile-fpc-design/v1`` request, from the profile limits.

    All fields are optional (defaults apply) and unknown keys are rejected at
    every level; the deprecated aliases are listed, so requests that use them
    validate too.  A request that validates passes every single-field rule of
    the engine; the rules in ``x-cross-field-rules`` are checked by the engine
    only.  The engine is slightly more lenient at four edges: it rounds
    numbers to the 1e-6 mm grid before range checks, trims project_name before
    checking its length and characters, ignores (with W_ALIAS_SHADOWED) an
    alias that a nested field or a higher-precedence alias overrides (values
    of the enumerated aliases are always checked), and on the generic template
    takes the diagonal Row bus's tails up to the surface profile's maximum
    (200 mm, P5-diagonal-bus.md section 23; the schema keeps this profile's).
    On the generic template the other bounds are those of its default, the
    diagonal Row bus (built with the surface profile, ``x-row-bus-profile``);
    the straight Row channel's own (``x-channel`` of a field: shorter tails,
    fewer columns) are cross-field rules.  ``x-*`` keywords are annotations.
    """

    profile = load_profile() if profile is None else profile
    specs = field_specs(profile)
    defaults = default_design(profile_template(profile))
    properties: dict[str, Any] = {}
    for field in CANONICAL_FIELDS:
        section, _, key = field.partition(".")
        schema = _x_channel(_json_schema(specs[field]), specs[field])
        if field != "project_name":  # a missing name follows the matrix size, so it has no fixed default
            schema["default"] = defaults[section][key] if key else defaults[section]
        if key:
            properties.setdefault(section, {"type": "object", "additionalProperties": False, "properties": {}})
            properties[section]["properties"][key] = schema
        else:
            properties[field] = schema
    for alias, targets, values in ALIASES:
        schema = _x_channel(_json_schema(specs[targets[0]]), specs[targets[0]]) if values is None else {"type": "string", "enum": list(values)}
        schema["deprecated"] = True
        schema["description"] = f"Alias of {', '.join(targets)}; used only where a higher-precedence source is absent."
        section, _, key = alias.partition(".")
        if key:
            properties[section]["properties"][key] = schema
        else:
            properties[alias] = schema
    for field in OPTIONAL_FIELDS:
        if field in specs:
            # Optional: absent or null is the template's default (the full rectangle; the Row traces of the template).
            section, _, key = field.partition(".")
            properties[section]["properties"][key] = dict(_json_schema(specs[field]), default=defaults[section].get(key))
    for section, keys in DESIGN_SECTIONS.items():
        optional = [field.partition(".")[2] for field in OPTIONAL_FIELDS if field in specs and field.startswith(section + ".")]
        properties[section]["description"] = f"{section} section: {', '.join(keys)}" + (f"; optional: {', '.join(optional)}." if optional else ".")
    bus = row_bus_profile(profile)
    extra = {} if bus is None else {"x-row-bus-profile": {"id": bus["id"], "revision": bus["revision"], "sha256": _sha256(_canonical_json(bus))}}
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "title": f"Tactile FPC design ({SCHEMA_VERSION})",
        "description": (
            "Request accepted by POST /api/validate, /api/generate and /api/export/*, and by cli.py. "
            "Missing fields take the defaults; unknown keys are rejected with E_UNKNOWN_FIELD. "
            "A request that validates passes every single-field engine rule; x-cross-field-rules are checked by the engine."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "x-profile": {"id": profile["id"], "revision": profile["revision"], "sha256": _sha256(_canonical_json(profile))},
        **extra,
        "x-alias-precedence": [alias for alias, _, _ in ALIASES],
        "x-cross-field-rules": cross_field_rules(profile),
        "x-error-codes": issue_codes()["errors"],
        "x-warning-codes": issue_codes()["warnings"],
    }


def _json_schema(spec: Mapping[str, Any]) -> dict[str, Any]:
    kind = spec["type"]
    schema: dict[str, Any] = {"description": spec["description"]}
    if kind in ("integer", "number"):
        schema["type"] = [kind, "null"] if spec.get("nullable") else kind
        schema["minimum"] = spec["minimum"]
        schema["maximum"] = spec["maximum"]
        return schema
    if kind == "mask":
        # Draft 2020-12 "integer" accepts 3.0, as the engine does.
        index = {"type": "integer", "minimum": spec["index_minimum"], "maximum": spec["index_maximum"]}
        schema.update(
            type=["array", "null"], minItems=spec["min_items"], maxItems=spec["max_items"],
            items={"type": "array", "minItems": 2, "maxItems": 2, "items": index},
        )
        return schema
    schema["type"] = ["string", "null"] if spec.get("nullable") else "string"
    if "const" in spec:
        schema["const"] = spec["const"]
    if "enum" in spec:
        schema["enum"] = list(spec["enum"]) + ([None] if spec.get("nullable") else [])
    if "max_length" in spec:
        schema.update(minLength=spec["min_length"], maxLength=spec["max_length"], pattern=PROJECT_NAME_PATTERN)
    return schema


def _x_channel(schema: dict[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    """A field's JSON Schema with its straight Row channel bounds (``channel``, :func:`field_specs`) as ``x-channel``."""

    if "channel" in spec:
        schema["x-channel"] = dict(spec["channel"])
    return schema
