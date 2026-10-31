"""Deterministic Row/Column FPC geometry.

Boards are built in a canonical frame with the connector tail pointing down
(-Y) and are then rotated as a whole by :func:`apply_tail_side`.  Every
dimension comes from the normalized design and the locked profile:

* the tail is a 0.5 mm-pitch ZIF tail sized for ``P`` connector positions,
  ``(P - 1) * pitch + 2 * side offset`` wide, with rounded tip corners, one
  contact per position (unused positions are isolated ``NC_<pin>`` contacts)
  and a stiffened connector zone flush with the tip and sides;
* the active (taxel crossing) field keeps ``active_edge_clearance_mm`` of
  board material on every side, and electrodes overhang it by
  ``electrode_overhang_mm``;
* every net is two route pieces: a thin fan-out piece (the design's
  ``routing.trace_width_mm``) from the electrode, converging into a bundle at
  the pitch ``trace width + trace space`` and expanding again to the 0.5 mm
  contact pitch, and a wide tail piece (``routing.finger_trace_width_mm``)
  straight down into its contact; the width changes below every bend;
* converging and expanding routes make bus-style bends: the routes that move
  the same way run parallel diagonals at the taper angle, the bundle pitch
  apart, with their bundle-side bends staggered by ``pitch * tan(angle / 2)``;
* the Column outline is the true offset of the outermost routes, never
  narrower than the tail, with rolling-circle fillets on concave corners.

A profile may set three optional geometry policies (the surface template's
profile does; the generic profile sets none and so keeps the rules above):
``routing.row_channel`` ``tight`` packs the Row channel against the board
edge and the field window and starts the field just above the expansion
(lanes that need no expansion run straight into their contacts);
``fanout.bus_angle`` ``shortest`` gives every bus transition the whole-degree
taper cap (``fanout.minimum_taper_angle_deg`` up to
``maximum_taper_angle_deg``) that makes it lowest, down to the tail root
where the traces widen; and ``fanout.column_convergence`` ``direct`` runs a
one-lane Column fan-out straight from the electrodes into the contact
columns, without a bundle or a straight stretch above the tail.

Design values and every origin that a zero-margin rule depends on (tail and
slot positions, deck origin, transition levels) are placed on the 1e-6 mm
layout grid, the resolution of the emitted JSON and Gerber coordinates, so
the rounding of the emitted geometry cannot break a rule that holds exactly.

A surface design may carry a field mask (``matrix.mask``): the row spans of
its taxels.  Its frames on each board and its construction classes are
here (:func:`design_mask`, :func:`row_frame_spans`,
:func:`column_frame_spans`, :func:`row_taper`, :func:`mask_class`).  The
masks of the straight classes are built (:func:`masked_row_plan`,
:func:`masked_column_plan`; claude/specs/masked-field/PLAN.md, phase P2):
the unmasked plans with each electrode trimmed to its span, the Row field
slid along the lane taper, per-row and raised Column stubs, outlines that
follow the crossings and polygon field windows; the feasibility check
refuses any other mask with E_MASK_ROUTING.  Every unmasked path is
unchanged: ``build_row_board`` and ``build_column_board`` hand a masked
design to the masked builders before anything else.

A design whose ``routing.row_sides`` is ``left``, ``right`` or ``both`` is
the diagonal Row bus (``diagonal-bus/8``, :mod:`engine.diagonal`;
claude/specs/masked-field/P5-diagonal-bus.md), on either template (the
generic template's default; ``channel`` is this module's straight Row
channel): both builders hand it to that module first, masked or not, and :func:`mask_class` gives it the classes ``{row: diagonal, column:
straight}``, so no mask of it is refused.  Its Column board is this
module's straight Column board (:func:`_masked_column_board`), its outline
shared with the Row board down to their tail roots, its V capped at
``engine.diagonal.COLUMN_V_CAP_DEG``.  On the generic template the bus is
built with the surface profile (``engine.core.rules_template``).
"""

from __future__ import annotations

import copy
import functools
import math
from typing import Any, Mapping, NamedTuple

from .geometry import (
    anchored_rect,
    arc_polygon_rounded_rect,
    band_ring,
    band_union,
    bounds_corners,
    bounds_of,
    ceil6,
    clean_polyline,
    convex_corner_arc,
    fillet_concave_corners,
    floor6,
    offset_polyline,
    rect_bounds,
    rect_union_slabs,
    rotate_quarter,
    round6,
)
from .profile import fabrication_minimum

LAYOUT_FORMAT = "tactile-fpc-layout/v3"
# Floating-point guard for comparisons of grid values (not a manufacturing rule).
_FLOAT_NOISE_MM = 1e-9
# Diagonal route sections are built this much farther apart than the bundle
# pitch: two layout-grid steps absorb the 1e-6 mm rounding of their end points,
# so a diagonal never comes closer than the pitch (not a manufacturing rule).
_DIAGONAL_ALLOWANCE_MM = 2e-6
# With a tight Row channel the innermost lane and the top expansion bend keep
# one more grid step than the coverlay opening-to-trace rule from the merged
# field window, so the rounding of the window edge cannot break the rule.
_WINDOW_ALLOWANCE_MM = 1e-6
BOARD_KEYS = {"rows": "row", "columns": "column"}
TAIL_TURNS = {"bottom": 0, "right": 1, "top": 2, "left": 3}


class Rules:
    """Flat, typed view of the profile values used by geometry and DRC."""

    def __init__(self, profile: Mapping[str, Any]) -> None:
        route = profile["routing"]
        conn = profile["connector"]
        cover = profile["coverlay"]
        fan = profile["fanout"]
        outline = profile["outline"]
        tail = profile["tail"]
        self.finger_width = float(route["finger_trace_width_mm"])
        self.half_finger = self.finger_width / 2
        self.min_trace_width, self.min_trace_space = fabrication_minimum(profile)
        self.pad_space = float(route["min_pad_space_mm"])
        self.pad_to_trace = float(route["min_pad_to_trace_mm"])
        self.electrode_gap = float(route["min_electrode_gap_mm"])
        self.min_electrode_width = float(route["min_electrode_width_mm"])
        self.copper_to_edge = float(route["copper_to_edge_mm"])
        self.copper_to_cutout = float(route["copper_to_cutout_mm"])
        self.margin = float(route["active_edge_clearance_mm"])
        self.overhang = float(route["electrode_overhang_mm"])
        self.pitch = float(conn["pad_pitch_mm"])
        self.contact_width = float(conn["pad_width_mm"])
        self.contact_length = float(conn["contact_length_mm"])
        self.tip_clearance = float(conn["contact_tip_clearance_mm"])
        self.side_offset = float(conn["contact_center_to_side_edge_mm"])
        self.tip_radius = float(conn["tail_tip_corner_radius_mm"])
        self.tail_width_tolerance = float(conn["tail_width_tolerance_mm"])
        self.maximum_pins = int(conn["maximum_pins"])
        self.expansion = float(cover["coverlay_expansion_mm"])
        self.min_bridge = float(cover["coverlay_min_bridge_mm"])
        self.opening_to_trace = float(cover["coverlay_opening_to_trace_mm"])
        self.minimum_tail = float(tail["minimum_length_mm"])
        self.stiffener_length = float(tail["stiffener_length_mm"])
        self.stiffener_end_clearance = float(tail["stiffener_end_clearance_mm"])
        self.fillet_radius = float(outline["outline_fillet_radius_mm"])
        self.arc_step = math.radians(float(outline["arc_segment_max_angle_deg"]))
        self.max_concave_turn = math.radians(float(outline["maximum_unfilleted_concave_turn_deg"]))
        self.offset_allowance = float(outline["offset_allowance_mm"])
        self.per_lane = int(fan["maximum_channels_per_lane"])
        self.max_lanes = int(fan["maximum_lanes"])
        self.slot_width = float(fan["slot_width_mm"])
        self.min_slot_width = float(fan["minimum_slot_width_mm"])
        self.slot_fraction = float(fan["slot_height_fraction"])
        self.min_slot_height = float(fan["minimum_slot_height_mm"])
        self.max_slot_height = float(fan["maximum_slot_height_mm"])
        self.lane_to_slot = float(fan["lane_to_slot_clearance_mm"])
        self.max_taper = math.radians(float(fan["maximum_taper_angle_deg"]))
        self.epsilon = float(profile["drc"]["numeric_epsilon_mm"])
        # Optional geometry policies (engine.profile.POLICIES); absent, the generic rules.
        self.row_channel = route.get("row_channel", "contact_aligned")
        self.bus_angle = fan.get("bus_angle", "cap")
        self.column_convergence = fan.get("column_convergence", "bundle")
        if self.bus_angle == "shortest":
            # Whole-degree caps from the minimum (a whole number, engine.profile)
            # up to the maximum, tried in ascending order; a fractional maximum
            # is tried last, so the steepest cap is always among them.
            lowest, highest = float(fan["minimum_taper_angle_deg"]), float(fan["maximum_taper_angle_deg"])
            degrees = [lowest + step for step in range(int(math.floor(highest - lowest + 1e-9)) + 1)]
            if highest - degrees[-1] > 1e-9:
                degrees.append(highest)
            self.taper_caps = [math.radians(degree) for degree in degrees]
        else:
            self.taper_caps = [self.max_taper]


# --------------------------------------------------------------------------
# Plans: every scalar of a board, cheap enough for validate_design.
# --------------------------------------------------------------------------


def tail_length_for_role(design: Mapping[str, Any], role: str) -> float:
    """Return the independent physical top/bottom tail length for a role (on the layout grid)."""

    physical_side = "top" if design["role_mapping"]["top"] == role else "bottom"
    return round6(design["tail"][f"{physical_side}_length_mm"])


def matrix_values(design: Mapping[str, Any]) -> tuple[int, int, float, float, float, float]:
    """``rows, columns, pitch_x, pitch_y, column width, row width`` on the layout grid."""

    matrix = design["matrix"]
    return (
        int(matrix["rows"]),
        int(matrix["columns"]),
        round6(matrix["pitch_x_mm"]),
        round6(matrix["pitch_y_mm"]),
        round6(matrix["taxel_width_mm"]),
        round6(matrix["taxel_height_mm"]),
    )


def connector_pins(design: Mapping[str, Any], role: str) -> int:
    """Connector positions of a role: ``connector.<row|column>_pins`` or the channel count."""

    channels = int(design["matrix"][role])
    connector = design.get("connector") or {}
    value = connector.get(f"{BOARD_KEYS[role]}_pins") if isinstance(connector, Mapping) else None
    return channels if value is None else int(value)


def bundle_values(design: Mapping[str, Any]) -> tuple[float, float, float]:
    """``trace width, trace space, bundle pitch`` of the design's fan-out traces (layout grid)."""

    routing = design["routing"]
    width, space = round6(routing["trace_width_mm"]), round6(routing["trace_space_mm"])
    return width, space, round6(width + space)


def bus_bends(pitch: float, rules: Rules) -> tuple[float, float]:
    """``(taper angle in rad, bend stagger)`` of a bus whose bundle pitch is ``pitch``.

    Neighbouring routes of a bus bend between the bundle and their diagonals
    at points ``pitch`` apart across and ``stagger`` apart along the bundle.
    The stagger is ``pitch * tan(angle / 2)`` rounded down to the layout grid
    (so it is exact and the angle stays within the taper cap); the angle is
    the one at which diagonals through such bend points lie ``pitch`` apart
    (plus the rounding allowance), as in a mitred bend of a bus.  The cap is
    the profile's ``fanout.maximum_taper_angle_deg``.
    """

    return _bus_at(pitch, rules.max_taper)


def _bus_at(pitch: float, cap: float) -> tuple[float, float]:
    """:func:`bus_bends` for the taper cap ``cap`` (rad)."""

    stagger = floor6(pitch * math.tan(cap / 2))
    reach = math.hypot(pitch, stagger)
    angle = math.atan2(stagger, pitch) + math.acos(min(1.0, (pitch + _DIAGONAL_ALLOWANCE_MM) / reach))
    return angle, stagger


def _bends(upper: list, lower: list, top: float, bus_below: bool, angle: float, stagger: float) -> list:
    """Bend heights of routes that run down from x ``upper[i]`` to x ``lower[i]``.

    Returns, per route, ``(upper bend y, lower bend y)``, or ``None`` for a
    route that runs straight.  The routes moving the same way form a run
    (a sub-bus) of parallel diagonals at ``angle`` from the vertical.  On the
    bundle side of the run (below when ``bus_below``: the routes converge into
    the bundle; above: they expand out of it) neighbouring bends are
    ``stagger`` apart, rising toward the side the run moves to, so the
    diagonals keep the bundle pitch; on the other side each route bends where
    its diagonal meets its own x.  The highest bend of every run lies at
    ``top`` (at most a grid step lower).  Every bend is on the layout grid:
    the bundle-side bends exactly, the others rounded away from the bundle,
    so that no diagonal, however short, leans further from the vertical
    than ``angle``.
    """

    cot = 1.0 / math.tan(angle)
    shifts = [round6(b - a) for a, b in zip(upper, lower)]
    signs = [(shift > _FLOAT_NOISE_MM) - (shift < -_FLOAT_NOISE_MM) for shift in shifts]
    answer: list = [None] * len(shifts)
    start = 0
    while start < len(shifts):
        end = start
        while end + 1 < len(shifts) and signs[end + 1] == signs[start]:
            end += 1
        if signs[start]:
            # Ranked from the back of the move: a right-moving run from its left end.
            run = list(range(start, end + 1))[:: signs[start]]
            levels = [(route, rank * stagger, abs(shifts[route]) * cot) for rank, route in enumerate(run)]
            highest = max(level + (drop if bus_below else 0.0) for _, level, drop in levels)
            base = floor6(top - highest)
            for route, level, drop in levels:
                bundle_y = round6(base + level)
                if bus_below:
                    answer[route] = (ceil6(bundle_y + drop), bundle_y)
                else:
                    answer[route] = (bundle_y, floor6(bundle_y - drop))
        start = end + 1
    return answer


def _transition(
    upper: list, lower: list, top: float, bus_below: bool, pitch: float, rules: Rules, junction: float | None = None
) -> tuple[list, float, float]:
    """``(bends, angle, stagger)`` of one bus transition (see :func:`_bends`).

    With the generic ``cap`` policy the bus runs at the profile's taper cap.
    With ``shortest`` (``fanout.bus_angle``) every cap of ``rules.taper_caps``
    is tried in ascending order and the lowest transition wins: its height
    from its highest bend (or ``top`` when the bus is below) down to its
    lowest bend, and, when ``junction`` gives the trace width because the
    traces widen below this transition, on down to that junction (the
    widening drop of :func:`_junction_drop` grows with the angle).  A tie
    keeps the smaller cap.  Bends and drops are layout-grid values, so the
    comparison is exact and the choice is deterministic.
    """

    if rules.bus_angle != "shortest":
        angle, stagger = bus_bends(pitch, rules)
        return _bends(upper, lower, top, bus_below, angle, stagger), angle, stagger
    # The bends depend on the routes' shifts only (see _bends): the search is cached on them.
    shifts = tuple(round6(b - a) for a, b in zip(upper, lower))
    caps = tuple(rules.taper_caps)
    drops = None if junction is None else _cap_drops(junction, pitch, caps, _DropRules(rules.half_finger, rules.pitch, rules.finger_width))
    bends, angle, stagger = _shortest_transition(shifts, top, bus_below, pitch, caps, drops)
    return list(bends), angle, stagger


class _DropRules(NamedTuple):
    """The rules :func:`_junction_drop` reads, hashable (a cache key)."""

    half_finger: float
    pitch: float
    finger_width: float


@functools.lru_cache(maxsize=256)
def _cap_drops(trace_width: float, pitch: float, caps: tuple, rules: _DropRules) -> tuple:
    """:func:`_junction_drop` at the bus angle of every cap."""

    return tuple(_junction_drop(trace_width, _bus_at(pitch, cap)[0], rules) for cap in caps)


@functools.lru_cache(maxsize=1024)
def _shortest_transition(shifts: tuple, top: float, bus_below: bool, pitch: float, caps: tuple, drops: tuple | None) -> tuple[tuple, float, float]:
    """The search of :func:`_transition` for routes that move by ``shifts``,
    cached: a planner search (the size advice, a surface fit) meets the same
    transitions again, since the Row expansion does not depend on the columns
    nor the Column fan-out on the rows.  ``drops`` are the junction drops of
    the caps, or ``None``."""

    best: tuple | None = None
    origins = [0.0] * len(shifts)
    for index, cap in enumerate(caps):
        angle, stagger = _bus_at(pitch, cap)
        bends = _bends(origins, list(shifts), top, bus_below, angle, stagger)
        levels = [y for bend in bends if bend for y in bend]
        if levels:
            lowest = min(levels) if drops is None else floor6(min(levels) - drops[index])
            height = round6((top if bus_below else max(levels)) - lowest)
        else:
            height = 0.0
        if best is None or height < best[0] - _FLOAT_NOISE_MM:
            best = (height, bends, angle, stagger)
    return tuple(best[1]), best[2], best[3]


def _junction_drop(trace_width: float, angle: float, rules: Rules) -> float:
    """How far below the lowest bend the traces widen to the finger width.

    There every route runs straight at the contact pitch.  A widened (tail)
    trace end keeps the finger-section spacing (contact pitch less finger
    width) to a neighbour whose diagonal leaves its contact column at the
    lowest bend: the diagonal passes ``pitch * cos(angle) + drop *
    sin(angle)`` from the end.
    """

    needed = rules.half_finger + trace_width / 2 + (rules.pitch - rules.finger_width) + _DIAGONAL_ALLOWANCE_MM
    return ceil6(max(0.0, (needed - rules.pitch * math.cos(angle)) / math.sin(angle)))


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def tail_width(pins: int, rules: Rules) -> float:
    return (pins - 1) * rules.pitch + 2 * rules.side_offset


def _body_side(side: float, hull: float, outward: float, radius: float) -> float:
    """Move a body side outward so its step to the fan-out or tail below is
    either zero or at least one fillet radius (room for a full fillet).
    A moved side is snapped outward to the layout grid."""

    step = (side - hull) * outward
    snap = ceil6 if outward > 0 else floor6
    if 1e-9 < step < radius:
        return snap(hull + outward * radius)
    if -radius < step < -1e-9:
        return snap(hull)
    return side


def row_plan(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    rules = Rules(profile)
    rows, columns, pitch_x, pitch_y, column_width, row_width = matrix_values(design)
    trace_width, _, bundle_pitch = bundle_values(design)
    pins = connector_pins(design, "rows")
    length = tail_length_for_role(design, "rows")
    active_width = (columns - 1) * pitch_x + column_width
    active_height = (rows - 1) * pitch_y + row_width
    # The left channel holds one lane per row at the bundle pitch; lane 1 (row
    # 1, the uppermost) is outermost, right above contact position 1.  The
    # active field keeps the full margin from the channel.  A tight channel
    # (routing.row_channel) puts lane 1 at the copper-to-edge rule from the
    # board edge and keeps the innermost lane the opening-to-trace rule from
    # the field window (which begins the overhang and the coverlay expansion
    # before the field), unless lanes right above their contacts need no
    # expansion at all (one row, or a bundle pitch equal to the contact
    # pitch): then those lanes run straight down into the contacts.
    tight = rules.row_channel == "tight"
    first_lane = ceil6(rules.copper_to_edge + trace_width / 2 + rules.offset_allowance) if tight else rules.side_offset
    lanes = [round6(first_lane + index * bundle_pitch) for index in range(rows)]
    contact_x = [round6(rules.side_offset + index * rules.pitch) for index in range(pins)]
    aligned = [round6(rules.side_offset + index * bundle_pitch) for index in range(rows)]
    if tight and all(abs(lane - contact) <= _FLOAT_NOISE_MM for lane, contact in zip(aligned, contact_x)):
        lanes = aligned
    window_gap = ceil6(rules.expansion + rules.opening_to_trace + trace_width / 2 + _WINDOW_ALLOWANCE_MM)
    if tight:
        active_x = max(round6(lanes[-1] + window_gap + rules.overhang), rules.margin)
        channel_width = round6(active_x - rules.margin)
    else:
        channel_width = round6((rows - 1) * bundle_pitch + 2 * rules.side_offset)
        active_x = channel_width + rules.margin
    # Below the active field (by the margin, or with a tight channel by the
    # window gap above the highest bend, and never closer than the margin to
    # the tail root) the lanes expand to the contact pitch; the lowest bend
    # leaves the widening drop above the tail root (y = 0), where the traces
    # widen to the finger width.
    expansion, angle, stagger = _transition(lanes, contact_x[:rows], 0.0, False, bundle_pitch, rules, junction=trace_width)
    heights = [y for bend in expansion if bend for y in bend]
    expansion_top = expansion_height = 0.0
    if heights:
        lift = ceil6(_junction_drop(trace_width, angle, rules) - min(heights))
        expansion = [None if bend is None else (round6(bend[0] + lift), round6(bend[1] + lift)) for bend in expansion]
        expansion_top = round6(max(heights) + lift)
        expansion_height = round6(max(heights) - min(heights))
    active_y = round6(expansion_top + rules.margin)
    if tight:
        active_y = max(round6(expansion_top + window_gap), rules.margin)
    body_height = active_y + active_height + rules.margin
    width_of_tail = tail_width(pins, rules)
    # The tail is flush with the left body side; the body also spans the
    # contacts the channel expands to, and its right side keeps a step of zero
    # or at least one fillet radius to the tail.
    field_right = max(active_x + active_width + rules.margin, tail_width(rows, rules))
    body_width = _body_side(field_right, width_of_tail, 1.0, rules.fillet_radius)
    return {
        "role": "rows",
        "rows": rows,
        "columns": columns,
        "pitch_x": pitch_x,
        "pitch_y": pitch_y,
        "row_width": row_width,
        "column_width": column_width,
        "pins": pins,
        "channels": rows,
        "tail_length": length,
        "active": (active_x, active_y, active_width, active_height),
        "body": (0.0, 0.0, body_width, body_height),
        "lanes": lanes,
        "contact_x": contact_x,
        "channel_width": channel_width,
        "trace_width": trace_width,
        "bundle_pitch": bundle_pitch,
        "angle_deg": math.degrees(angle) if heights else 0.0,
        "stagger": stagger,
        "expansion": expansion,
        "expansion_height": expansion_height,
        "tail_x": 0.0,
        "tail_width": width_of_tail,
        "tail_top": 0.0,
        "tip": -length,
        "outline_x": (0.0, max(body_width, width_of_tail)),
        "outline_size": (max(body_width, width_of_tail), body_height + length),
        "rules": rules,
    }


def column_plan(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    rules = Rules(profile)
    rows, columns, pitch_x, pitch_y, column_width, row_width = matrix_values(design)
    trace_width, _, bundle_pitch = bundle_values(design)
    pins = connector_pins(design, "columns")
    length = tail_length_for_role(design, "columns")
    active_width = (columns - 1) * pitch_x + column_width
    active_height = (rows - 1) * pitch_y + row_width
    margin = rules.margin
    body_width = active_width + 2 * margin
    body_bottom = 0.0
    active_x = margin
    active_y = body_bottom + margin
    body_top = active_y + active_height + margin
    # Each route leaves the middle of its electrode's bottom end (on the grid).
    first_center = round6(active_x + column_width / 2)
    centers = [round6(first_center + index * pitch_x) for index in range(columns)]
    width_of_tail = tail_width(pins, rules)
    tail_x = round6((body_width - width_of_tail) / 2)
    contact_x = [round6(tail_x + rules.side_offset + index * rules.pitch) for index in range(pins)]
    # Route centreline to the outline: the larger of the two route half widths.
    envelope = max(trace_width, rules.finger_width) / 2 + rules.copper_to_edge + rules.offset_allowance
    lane_count = 1 if columns <= rules.per_lane else 2
    slot = None
    if lane_count == 2:
        groups = [(columns + 1) // 2, columns // 2]
        slot_height = round6(_clamp(rules.slot_fraction * active_height, rules.min_slot_height, rules.max_slot_height))
        # Widest slot (up to fanout.slot_width_mm) that keeps both bundles and
        # their outline envelope inside the body width, but never narrower than
        # the minimum: on a narrow field the bundles then spread wider than the
        # body, and the outline follows them (a filleted shoulder below the body).
        available = body_width - 2 * (rules.lane_to_slot + (groups[0] - 1) * bundle_pitch + envelope)
        slot_width = max(min(rules.slot_width, available), rules.min_slot_width)
        slot_x = round6((body_width - slot_width) / 2)
        decks = [round6(slot_x - rules.lane_to_slot - (groups[0] - 1 - index) * bundle_pitch) for index in range(groups[0])]
        decks += [round6(slot_x + slot_width + rules.lane_to_slot + index * bundle_pitch) for index in range(groups[1])]
        deck_length = slot_height + rules.lane_to_slot
    else:
        groups = [columns]
        slot_height = slot_width = slot_x = 0.0
        # One bundle centred under the field (a middle route runs straight),
        # with a straight stretch of one pitch between the converging and the
        # expanding bends.
        first = round6((centers[0] + centers[-1]) / 2 - (columns - 1) * bundle_pitch / 2)
        decks = [round6(first + index * bundle_pitch) for index in range(columns)]
        deck_length = bundle_pitch
        if rules.column_convergence == "direct":
            # Or the routes converge straight into their contact columns
            # (fanout.column_convergence): no bundle, so no expansion either,
            # and no straight stretch between the two.
            decks = list(contact_x[:columns])
            deck_length = 0.0
    # Straight stubs leave the body edge before tapering, so the junction
    # between the body and the fan-out envelope can carry a full fillet.
    # The traces widen below the lowest transition with bends (the merger,
    # or the entry where no route expands): its angle search runs down to
    # that junction.
    expanding = any(abs(round6(contact - deck)) > _FLOAT_NOISE_MM for deck, contact in zip(decks, contact_x))
    entry_top = body_bottom - rules.fillet_radius
    entry, entry_angle, entry_stagger = _transition(
        centers, decks, entry_top, True, bundle_pitch, rules, junction=None if expanding else trace_width
    )
    deck_top = min([entry_top, *(bend[1] for bend in entry if bend)])
    deck_bottom = round6(deck_top - deck_length)
    merger, merger_angle, merger_stagger = _transition(decks, contact_x[:columns], deck_bottom, False, bundle_pitch, rules, junction=trace_width)
    merger_base = min([deck_bottom, *(bend[1] for bend in merger if bend)])
    entering, merging = any(entry), any(merger)
    # The lowest bends are the merger's, or the entry's where no route expands.
    angle, stagger = (merger_angle, merger_stagger) if merging else (entry_angle, entry_stagger)
    # The traces widen to the finger width in the tail, at the contact pitch
    # below every bend: the tail starts there.
    bends = [y for bend in entry + merger if bend for y in bend]
    lowest = min(bends) - _junction_drop(trace_width, angle, rules) if bends else deck_bottom
    tail_top = floor6(min(deck_bottom, lowest))
    tip = round6(tail_top - length)
    if lane_count == 2:
        slot = (slot_x, deck_bottom + rules.lane_to_slot / 2, slot_x + slot_width, deck_top - rules.lane_to_slot / 2)
    # Outermost extent of the fan-out below each body side (the outer routes'
    # straight runs set it); a narrow step there would cap the fillet, so the
    # body side moves out to a step of zero or one full fillet radius.
    hull_left = min(tail_x, contact_x[0] - envelope, decks[0] - envelope, centers[0] - envelope)
    hull_right = max(tail_x + width_of_tail, contact_x[columns - 1] + envelope, decks[-1] + envelope, centers[-1] + envelope)
    body_left = _body_side(0.0, hull_left, -1.0, rules.fillet_radius)
    body_right = _body_side(body_width, hull_right, 1.0, rules.fillet_radius)
    # A two-lane fan-out on a narrow field spreads beyond the body: the outline is that wide.
    min_x = min(body_left, tail_x, hull_left)
    max_x = max(body_right, tail_x + width_of_tail, hull_right)
    return {
        "role": "columns",
        "rows": rows,
        "columns": columns,
        "pitch_x": pitch_x,
        "pitch_y": pitch_y,
        "row_width": row_width,
        "column_width": column_width,
        "pins": pins,
        "channels": columns,
        "tail_length": length,
        "active": (active_x, active_y, active_width, active_height),
        "body": (body_left, body_bottom, body_right, body_top),
        "centers": centers,
        "contact_x": contact_x,
        "tail_x": tail_x,
        "tail_width": width_of_tail,
        "lane_count": lane_count,
        "groups": groups,
        "decks": decks,
        "trace_width": trace_width,
        "bundle_pitch": bundle_pitch,
        "envelope": envelope,
        "stagger": stagger,
        "entry": entry,
        "merger": merger,
        "slot": slot,
        "entry_top": entry_top,
        "deck_top": deck_top,
        "deck_bottom": deck_bottom,
        "merger_base": merger_base,
        "tail_top": tail_top,
        "tip": tip,
        # Every diagonal of a transition runs at its bus angle (0 where no route moves).
        "entry_angle_deg": math.degrees(entry_angle) if entering else 0.0,
        "merger_angle_deg": math.degrees(merger_angle) if merging else 0.0,
        "entry_height": round6(entry_top - deck_top) if entering else 0.0,
        "merger_height": round6(deck_bottom - merger_base) if merging else 0.0,
        "convergence": "direct" if lane_count == 1 and rules.column_convergence == "direct" else "bundle",
        "outline_x": (min_x, max_x),
        "outline_size": (max_x - min_x, body_top - tip),
        "rules": rules,
    }


def field_footprint(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """Board material around the taxel field of both boards, from the plans alone.

    ``design`` is a normalized, valid design (``check_design(...)["design"]``)
    and ``profile`` its template's profile; no geometry is built, so this is
    cheap enough for a search over designs.  Each board is measured in its
    canonical frame (copper side up, tail down, before the tail side turns
    it) from the active region, the taxel crossing field of
    ``field.width`` x ``field.height`` mm: ``left``, ``right`` and ``top`` are
    the outline's distances beyond the field's sides (above the tail root,
    including the Column fan-out), ``bottom`` the depth of the tail root
    below the field, and ``tail`` the tail's ``x`` (its left edge, from the
    field's left edge), ``width`` and ``length``.  All in mm on the layout
    grid.

    A masked design (``matrix.mask``) is measured on its masked plans
    (:func:`masked_row_plan`, :func:`masked_column_plan`; the field is the
    bounding R x C field) and adds ``mask``: per board, its ``outline``
    above the tail root before the fillets (a counter-clockwise ring, from
    the field's lower-left corner in the board's canonical frame).  The
    fillets only add board material, outside the ring and within the fillet
    radius (``outline.outline_fillet_radius_mm``) of one of its concave
    corners or of a corner on its tail-root edge: the ring is cut at the tail
    root, so a concave corner of the board where the body meets the tail (a
    tail wider than the body, the Column fan-out's sides) is a convex corner
    of the ring there.
    """

    if row_bus(design):
        return _diagonal_footprint(design, profile)
    answer: dict[str, Any] = {}
    masked = design_mask(design) is not None
    plans = (
        (("row", masked_row_plan(design, profile)), ("column", masked_column_plan(design, profile))) if masked
        else (("row", row_plan(design, profile)), ("column", column_plan(design, profile)))
    )
    for key, plan in plans:
        active_x, active_y, active_width, active_height = plan["active"]
        left, right = plan["outline_x"]
        if key == "row":
            right = plan["body"][2]  # the Row tail hangs below the body, flush with its left side
        answer.setdefault("field", {"width": round6(active_width), "height": round6(active_height)})
        answer[key] = {
            "left": round6(active_x - left),
            "right": round6(right - active_x - active_width),
            "top": round6(plan["body"][3] - active_y - active_height),
            "bottom": round6(active_y - plan["tail_top"]),
            "tail": {"x": round6(plan["tail_x"] - active_x), "width": round6(plan["tail_width"]), "length": round6(plan["tail_length"])},
        }
    if masked:
        answer["mask"] = {key: {"outline": _masked_body_ring(key, plan)} for key, plan in plans}
    return answer


def _diagonal_footprint(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """:func:`field_footprint` of a diagonal Row bus (:func:`row_bus`), measured on its built boards.

    The diagonal construction (:mod:`engine.diagonal`, which builds the pair
    once) has no plan apart from its geometry: each board's sides are its
    outline's extremes above the tail root, as for the plans, and a masked
    design's ``mask`` outline is the board's outline above the root (its
    fillets included).  A bus that cannot place its lanes raises
    ``RowBusInfeasible`` (a ``ValueError``).
    """

    from .diagonal import build_column_board as build_diagonal_column_board, build_row_board as build_diagonal_row_board

    answer: dict[str, Any] = {}
    boards = (("row", build_diagonal_row_board(design, profile)), ("column", build_diagonal_column_board(design, profile)))
    for key, board in boards:
        active = board["grid_registration"]["active_region"]
        tail = board["tail"]["bounds"]
        root = round6(tail["y"] + tail["height"])
        above = [point for point in board["outline"]["points"] if point[1] >= root - _FLOAT_NOISE_MM]
        answer.setdefault("field", {"width": round6(active["width"]), "height": round6(active["height"])})
        answer[key] = {
            "left": round6(active["x"] - min(x for x, _ in above)),
            "right": round6(max(x for x, _ in above) - active["x"] - active["width"]),
            "top": round6(max(y for _, y in above) - active["y"] - active["height"]),
            "bottom": round6(active["y"] - root),
            "tail": {"x": round6(tail["x"] - active["x"]), "width": round6(tail["width"]), "length": round6(tail["height"])},
        }
    if design_mask(design) is not None:
        answer["mask"] = {}
        for key, board in boards:
            active = board["grid_registration"]["active_region"]
            tail = board["tail"]["bounds"]
            ring = _ring_above(board["outline"]["points"], round6(tail["y"] + tail["height"]))
            answer["mask"][key] = {"outline": _round_ring([[x - active["x"], y - active["y"]] for x, y in ring])}
    return answer


def _ring_above(points: list, level: float) -> list[list[float]]:
    """The part of a counter-clockwise ring at or above ``y = level`` (the half-plane clip; one piece for a board above
    its tail root)."""

    clipped: list[list[float]] = []
    count = len(points)
    for index in range(count):
        (x0, y0), (x1, y1) = points[index - 1], points[index]
        inside0, inside1 = y0 >= level - _FLOAT_NOISE_MM, y1 >= level - _FLOAT_NOISE_MM
        if inside0 != inside1:
            clipped.append([round6(x0 + (x1 - x0) * (level - y0) / (y1 - y0)), level])
        if inside1:
            clipped.append([x1, y1])
    return clean_polyline(clipped, closed=True)


def _diagonal_size_errors(design: Mapping[str, Any], profile: Mapping[str, Any], fallback: tuple) -> list[dict[str, str]]:
    """``E_BOARD_SIZE`` of a diagonal Row bus, measured on its built boards (not on the straight channel's plans).

    The advice is searched on a model, the straight plan's outline plus the
    diagonal board's measured excess over it (its bands and its deeper tail
    root, which a smaller pitch or tail leaves about as they are; the Column
    plan the bus's own, its V capped, ``engine.diagonal.column_profile``),
    and each bound is kept only when the diagonal boards built with it fit.  A bus that cannot place its lanes is left to the
    build (``E_ROW_BUS_INFEASIBLE``).
    """

    from .diagonal import (
        RowBusInfeasible,
        build_column_board as build_diagonal_column_board,
        build_row_board as build_diagonal_row_board,
        column_profile,
    )

    limits = profile["limits"]
    builders = {"rows": build_diagonal_row_board, "columns": build_diagonal_column_board}

    def bus_column_plan(changed: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
        return column_plan(changed, column_profile(profile))

    def size(changed: Mapping[str, Any], role: str) -> Any:
        try:
            points = builders[role](changed, profile)["outline"]["points"]
        except RowBusInfeasible:
            return None
        xs, ys = [x for x, _ in points], [y for _, y in points]
        return (round6(max(xs) - min(xs)), round6(max(ys) - min(ys)))

    errors: list[dict[str, str]] = []
    for role, planner in (("rows", row_plan), ("columns", bus_column_plan)):
        measured = size(design, role)
        if measured is None or _fits({"outline_size": measured}, limits):
            continue
        straight = planner(design, profile)["outline_size"]
        excess = (measured[0] - straight[0], measured[1] - straight[1])

        def modelled(changed: Mapping[str, Any], profile: Mapping[str, Any], planner=planner, excess=excess) -> dict[str, Any]:
            width, height = planner(changed, profile)["outline_size"]
            return {"outline_size": (width + excess[0], height + excess[1])}

        advice = []
        for values in _size_advice(design, profile, role, modelled):
            changed = size(_with(design, values), role)
            if changed is not None and _fits({"outline_size": changed}, limits):
                advice.append(values)
        field = "{}.{}".format(*next(iter(advice[0]))) if advice else fallback[0]
        hint = "; ".join(_describe(values) for values in advice) or fallback[1]
        errors.append(
            {
                "code": "E_BOARD_SIZE",
                "field": field,
                "message": (
                    f"The {BOARD_KEYS[role]} FPC outline would be {measured[0]:.3f} x {measured[1]:.3f} mm (the diagonal Row bus), larger "
                    f"than the {limits['maximum_outline_short_side_mm']:g} x {limits['maximum_outline_long_side_mm']:g} mm fabrication "
                    f"maximum (either orientation). Any one of: {hint}."
                ),
            }
        )
    return errors


def _masked_body_ring(key: str, plan: Mapping[str, Any]) -> list[list[float]]:
    """A masked board's body above its tail root, before the fillets, from the field's lower-left corner."""

    if key == "row":
        ring = [[0.0, 0.0], *plan["right_chain"], [0.0, plan["body"][3]]]
    else:
        # The body above its bottom, and below it the fan-out sides down to the tail root.
        body_left, body_bottom, body_right, _ = plan["body"]
        root = plan["tail_top"]
        left, right = (
            [[_x_at(chain, root), root], *(point for point in chain if point[1] > root + _FLOAT_NOISE_MM)] for chain in _column_side_chains(plan)
        )
        ring = [[body_left, body_bottom], *reversed(left), *right, [body_right, body_bottom], *plan["top_chain"]]
    active_x, active_y = plan["active"][0], plan["active"][1]
    return _round_ring(clean_polyline([[x - active_x, y - active_y] for x, y in ring], closed=True))


# --------------------------------------------------------------------------
# Field mask (matrix.mask): its frames and construction classes.
# --------------------------------------------------------------------------
#
# A mask gives each ROW_01..ROW_R the first and last COL index of its taxels,
# in the readout's net indices (docs/API.md "Field mask").  Each board sees it
# in its own canonical frame (copper up, tail down): the Row board counts its
# x-slots from the Row channel, the Column board its row slots from its tail.
# Which net a slot holds depends on the tail sides only; the boards face each
# other, so the role mapping does not change it (docs/INTEGRATION.md).


def design_mask(design: Mapping[str, Any]) -> tuple[tuple[int, int], ...] | None:
    """The field mask of a design, ``((first, last), ...)`` per ROW_01..ROW_R, or ``None`` (the full rectangle)."""

    matrix = design.get("matrix") if isinstance(design, Mapping) else None
    mask = matrix.get("mask") if isinstance(matrix, Mapping) else None
    if mask is None:
        return None
    return tuple((int(first), int(last)) for first, last in mask)


def _row_spans(design: Mapping[str, Any]) -> tuple[tuple[int, int], ...]:
    """The mask's row spans, or the full rectangle's."""

    mask = design_mask(design)
    return ((1, int(design["matrix"]["columns"])),) * int(design["matrix"]["rows"]) if mask is None else mask


def _equal_sides(design: Mapping[str, Any]) -> bool:
    return design["tail"]["row_side"] == design["tail"]["column_side"]


def column_spans(mask: Any, columns: int) -> list[tuple[int, int]]:
    """``(rmin, rmax)`` per COL_01..COL_C: the first and last ROW index whose span holds the column.

    ``mask`` is valid (validate_design): every column has a contiguous run of rows.
    """

    spans: list[Any] = [None] * columns
    for row, (first, last) in enumerate(mask, start=1):
        for column in range(first, last + 1):
            run = spans[column - 1]
            spans[column - 1] = (row, row) if run is None else (run[0], row)
    return spans


def row_frame_spans(design: Mapping[str, Any]) -> list[tuple[int, int]]:
    """``(lo, hi)`` per ROW_01..ROW_R: its taxels as x-slots of the Row board's canonical frame.

    Slot 0 is next to the Row channel.  COL_c sits at slot ``C - c`` when
    both tails leave on one side (``tail.row_side == tail.column_side``) and
    at ``c - 1`` when they are opposite.  Unmasked, every row is ``(0, C - 1)``.
    """

    columns = int(design["matrix"]["columns"])
    if _equal_sides(design):
        return [(columns - last, columns - first) for first, last in _row_spans(design)]
    return [(first - 1, last - 1) for first, last in _row_spans(design)]


def column_frame_spans(design: Mapping[str, Any]) -> list[tuple[int, int]]:
    """``(b, t)`` per COL_01..COL_C: its taxels as row slots of the Column board's canonical frame.

    Slots count from the Column tail (slot 0 next to it).  ROW_r sits at slot
    ``R - r`` when both tails leave on one side and at ``r - 1`` when they are
    opposite; COL_c is always the Column frame's x-slot ``c - 1``.  Unmasked,
    every column is ``(0, R - 1)``.
    """

    rows = int(design["matrix"]["rows"])
    spans = column_spans(_row_spans(design), int(design["matrix"]["columns"]))
    if _equal_sides(design):
        return [(rows - last, rows - first) for first, last in spans]
    return [(first - 1, last - 1) for first, last in spans]


def row_taper(design: Mapping[str, Any], profile: Mapping[str, Any]) -> list[float]:
    """``W_k`` per ROW_k: the smallest x of its channel-side crossing edge in the Row board's canonical frame.

    From the plan of the bounding R x C field, never from a plan of fewer
    rows (one row takes the contact-aligned lane).  With a tight Row channel
    (``routing.row_channel``) the stub of ROW_k leaves its lane k, beside
    which only lanes 1..k run at its height, so its crossing edge keeps the
    window gap and the electrode overhang from that lane: ``W_k = lane_k +
    window gap + overhang``; the unmasked field starts at ``max(W_R,
    margin)``.  Any other channel keeps its full width and margin: every
    ``W_k`` is the unmasked field start.
    """

    plan = row_plan(design, profile)
    rules = plan["rules"]
    if rules.row_channel != "tight":
        return [plan["active"][0]] * plan["rows"]
    window_gap = ceil6(rules.expansion + rules.opening_to_trace + plan["trace_width"] / 2 + _WINDOW_ALLOWANCE_MM)
    return [round6(lane + window_gap + rules.overhang) for lane in plan["lanes"]]


def row_bus(design: Mapping[str, Any]) -> bool:
    """Whether a design is built as the diagonal Row bus: its ``routing.row_sides`` is ``left``, ``right`` or ``both``
    (:data:`engine.diagonal.ROW_SIDES`); ``channel`` or none is the straight Row channel."""

    from .diagonal import row_sides

    return row_sides(design) is not None


def mask_class(design: Mapping[str, Any], profile: Mapping[str, Any]) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    """The constructions of a masked design's boards: ``(classes, None)`` or ``(None, issue)``.

    ``classes`` is ``{"row": "straight", "column": "straight"}``; ``issue``
    is an ``E_MASK_ROUTING`` error naming the first row or column outside
    the classes the engine builds, and what brings it in.  An unmasked
    design gives ``(None, None)``.  The mask must be valid (validate_design).
    A design built as the diagonal Row bus (:func:`row_bus`), masked or not,
    gives ``{"row": "diagonal", "column": "straight"}``: the diagonal Row
    bus builds every valid mask.

    - Row board, straight channel (condition A): every row's stub runs
      straight from its lane, so ROW_k starts at the Row-frame slot
      ``tau_k`` that its lane taper ``W_k`` (:func:`row_taper`) leaves, no
      farther: ``active_x = max(margin, max_k (W_k - lo_k * pitch_x))`` and
      ``tau_k = ceil((W_k - active_x) / pitch_x)``, never below 0.  Every
      mask whose rows all reach the channel side holds.
    - Column board, straight fan-out (condition B): every column's stub runs
      straight to the Column tail, past the rows between its taxels and the
      tail on their Row-channel side only (its Row-frame slot below each
      row's ``lo``).  A row next to the Column tail that spans every column
      makes it hold.
    """

    if row_bus(design):
        return {"row": "diagonal", "column": "straight"}, None
    mask = design_mask(design)
    if mask is None:
        return None, None
    rows, columns = int(design["matrix"]["rows"]), int(design["matrix"]["columns"])
    pitch_x = round6(design["matrix"]["pitch_x_mm"])
    equal = _equal_sides(design)
    spans = row_frame_spans(design)
    taper = row_taper(design, profile)
    active_x = max(Rules(profile).margin, max(round6(edge - round6(lo * pitch_x)) for edge, (lo, _) in zip(taper, spans)))
    # By construction lo_k >= tau_k; a row fails A when it stops farther from the channel side.
    short = []
    for row, (edge, (lo, _)) in enumerate(zip(taper, spans), start=1):
        tau = max(0, math.ceil(round6(edge - active_x) / pitch_x - _FLOAT_NOISE_MM))
        if lo != tau:
            short.append((row, lo, tau))
    if short:
        row, lo, tau = short[0]
        end, reach = (columns - lo, columns - tau) if equal else (lo + 1, tau + 1)
        more = f" ({len(short) - 1} more row(s) stop short)" if len(short) > 1 else ""
        message = (
            f"ROW_{row:02d} ends at COL_{end:02d} on the Row-channel side, {lo - tau} column(s) short of COL_{reach:02d}{more}: "
            "a straight Row channel lets a row stop short of the channel side only by the room its lane taper needs. Extend "
            "those rows toward the channel side; a channel that follows the field's boundary is not built yet."
        )
        return None, {"code": "E_MASK_ROUTING", "field": f"matrix.mask[{row - 1}]", "message": message}
    # For a valid mask only the row next to a column's taxels, on the Column-tail side, can fail B:
    # the rows beyond it overlap it, so they lie on the channel side of the column as well.
    blocked = []
    for column, (first, last) in enumerate(column_spans(mask, columns), start=1):
        slot = columns - column if equal else column - 1
        row = last + 1 if equal else first - 1
        if 1 <= row <= rows and slot >= spans[row - 1][0]:
            blocked.append((column, last if equal else first, row))
    if blocked:
        column, end, row = blocked[0]
        far = mask[row - 1][0] if equal else mask[row - 1][1]
        more = f" ({len(blocked) - 1} more column(s) end so)" if len(blocked) > 1 else ""
        message = (
            f"COL_{column:02d} ends at ROW_{end:02d}, and ROW_{row:02d}, next to it on the Column-tail side, ends at "
            f"COL_{far:02d}, short of it on the far side{more}: a straight Column fan-out passes a row without its taxel only "
            "on that row's Row-channel side. Extend those rows to the far side; a row next to the Column tail that spans "
            "every column always allows it."
        )
        return None, {"code": "E_MASK_ROUTING", "field": f"matrix.mask[{row - 1}]", "message": message}
    return {"row": "straight", "column": "straight"}, None


# --------------------------------------------------------------------------
# Shared tail, contact, coverlay and stiffener construction.
# --------------------------------------------------------------------------


def _pin_for_position(position: int, pins: int, order: str) -> int:
    """Connector pin at a contact position (1-based, from the canonical left).

    Pins run monotonically along the contact row: pin 1 is position 1 for
    ``ascending`` and position ``pins`` for ``descending``.  Channel ``k``
    always sits at position ``k`` (channel_order never moves copper).
    """

    return position if order == "ascending" else pins - position + 1


def _tip_corners(tail_x: float, width: float, tip: float, rules: Rules) -> tuple[list, list]:
    """Circumscribed R arcs for the bottom-left and bottom-right tail tip corners."""

    left = convex_corner_arc([tail_x, tip], (0.0, -1.0), (1.0, 0.0), rules.tip_radius, rules.arc_step)
    right = convex_corner_arc([tail_x + width, tip], (1.0, 0.0), (0.0, 1.0), rules.tip_radius, rules.arc_step)
    return left, right


def _contacts(plan: Mapping[str, Any], nets: list[str], order: str, rules: Rules) -> list[dict[str, Any]]:
    """One centre-anchored contact per connector position; unused ones are NC."""

    tip = plan["tip"]
    center_y = tip + rules.tip_clearance + rules.contact_length / 2
    contacts = []
    for position in range(plan["pins"]):
        center_x = plan["tail_x"] + rules.side_offset + position * rules.pitch
        pin = _pin_for_position(position + 1, plan["pins"], order)
        if position < len(nets):
            net, kind = nets[position], "connector_pad"
        else:
            net, kind = f"NC_{pin:02d}", "connector_nc_pad"
        contacts.append(
            {
                "pin": pin,
                "net": net,
                "kind": kind,
                "position": position + 1,
                **anchored_rect(
                    center_x - rules.contact_width / 2,
                    center_y - rules.contact_length / 2,
                    center_x + rules.contact_width / 2,
                    center_y + rules.contact_length / 2,
                    "center",
                ),
            }
        )
    return contacts


def _openings(
    electrodes: list[dict[str, Any]], pads: list[dict[str, Any]], plan: Mapping[str, Any], rules: Rules
) -> list[dict[str, Any]]:
    """Coverlay openings: one per electrode, or one merged field window when the
    bridges between them would be narrower than the coverlay bridge rule, plus
    one gang window over all contacts from the tip edge."""

    expansion = rules.expansion
    boxes = [rect_bounds(electrode) for electrode in electrodes]
    axis = 1 if plan["role"] == "rows" else 0
    ordered = sorted(boxes, key=lambda box: box[axis])
    bridges = [second[axis] - first[axis + 2] - 2 * expansion for first, second in zip(ordered, ordered[1:])]
    openings: list[dict[str, Any]] = []
    # Electrodes sit on the 1e-6 mm grid, so a bridge is either exactly the
    # rule (kept, it passes the DRC) or at least one grid step below it.
    if bridges and min(bridges) < rules.min_bridge - _FLOAT_NOISE_MM:
        field = (
            min(box[0] for box in boxes) - expansion,
            min(box[1] for box in boxes) - expansion,
            max(box[2] for box in boxes) + expansion,
            max(box[3] for box in boxes) + expansion,
        )
        openings.append(
            {
                "kind": "electrode_field_opening",
                "net": None,
                "nets": [electrode["net"] for electrode in electrodes],
                "opening_for": electrodes[0]["kind"],
                **anchored_rect(*field, "lower_left"),
            }
        )
    else:
        for electrode, box in zip(electrodes, boxes):
            openings.append(
                {
                    "kind": "sensor_electrode_opening",
                    "net": electrode["net"],
                    "nets": [electrode["net"]],
                    "opening_for": electrode["kind"],
                    **anchored_rect(box[0] - expansion, box[1] - expansion, box[2] + expansion, box[3] + expansion, "lower_left"),
                }
            )
    contact_boxes = [rect_bounds(pad) for pad in pads]
    tail_x, width, tip = plan["tail_x"], plan["tail_width"], plan["tip"]
    # The gang window ends exactly on the straight part of the tip edge and
    # never enters the rounded tip corners.
    gang = (
        max(tail_x + rules.tip_radius, min(box[0] for box in contact_boxes) - expansion),
        tip,
        min(tail_x + width - rules.tip_radius, max(box[2] for box in contact_boxes) + expansion),
        max(box[3] for box in contact_boxes) + expansion,
    )
    openings.append(
        {
            "kind": "connector_contact_opening",
            "net": None,
            "nets": [pad["net"] for pad in pads],
            "opening_for": "connector_contacts",
            **anchored_rect(*gang, "lower_left"),
        }
    )
    return openings


def _stiffener(plan: Mapping[str, Any], profile: Mapping[str, Any], rules: Rules, corners: tuple[list, list]) -> dict[str, Any]:
    """Connector-zone PI stiffener flush with the tip and both tail sides."""

    tail_x, width, tip = plan["tail_x"], plan["tail_width"], plan["tip"]
    top = tip + rules.stiffener_length
    left, right = corners
    points = [[tail_x + width, top], [tail_x, top], *left, *right]
    stack = profile["stackup"]
    return {
        "kind": "polygon",
        "zone": "connector",
        "side": stack["stiffener_side"],
        "layer": "bottom_stiffener",
        "material": stack["stiffener_material"],
        "thickness_mm": stack["stiffener_thickness_mm"],
        "length_mm": rules.stiffener_length,
        "points": _round_ring(clean_polyline(points, closed=True)),
    }


def _route_pieces(net: str, tail: list, fanout: list, plan: Mapping[str, Any], extra: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The two route objects of a net: the tail piece (finger width) from its
    contact to the junction and the fan-out piece (bundle width) from the
    junction to its electrode.  Both run from the contact end."""

    return [
        {
            "net": net,
            "kind": "polyline",
            "segment": segment,
            "width_mm": width,
            "points": _round_points(clean_polyline(points)),
            **extra,
        }
        for segment, width, points in (("tail", plan["rules"].finger_width, tail), ("fanout", plan["trace_width"], fanout))
    ]


def _electrode(net: str, kind: str, bounds: tuple) -> dict[str, Any]:
    return {"net": net, "kind": kind, **anchored_rect(*bounds, "lower_left")}


def _round_points(points: list[list[float]]) -> list[list[float]]:
    return [[round6(x), round6(y)] for x, y in points]


def _round_ring(points: list[list[float]]) -> list[list[float]]:
    """Round a closed ring, dropping vertices that collapse onto their neighbour."""

    answer: list[list[float]] = []
    for point in _round_points(points):
        if not answer or point != answer[-1]:
            answer.append(point)
    while len(answer) > 1 and answer[0] == answer[-1]:
        answer.pop()
    return answer


def _bounds_dict(bounds: tuple) -> dict[str, float]:
    x0, y0, x1, y1 = bounds
    return {"x": round6(x0), "y": round6(y0), "width": round6(x1 - x0), "height": round6(y1 - y0)}


def _assemble(
    *,
    plan: Mapping[str, Any],
    design: Mapping[str, Any],
    profile: Mapping[str, Any],
    outline: list[list[float]],
    cutouts: list[list[list[float]]],
    electrodes: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    pads: list[dict[str, Any]],
    corners: tuple[list, list],
    tail_extra: Mapping[str, Any],
    construction: Mapping[str, Any],
) -> dict[str, Any]:
    rules = plan["rules"]
    active_x, active_y, active_width, active_height = plan["active"]
    electrode_boxes = [rect_bounds(electrode) for electrode in electrodes]
    electrode_field = bounds_of([corner for box in electrode_boxes for corner in bounds_corners(box)])
    tail_x, width, tip = plan["tail_x"], plan["tail_width"], plan["tip"]
    tail_bounds = (tail_x, tip, tail_x + width, plan["tail_top"])
    # From above the rounded tip up to the body: the board is never narrower
    # than the tail anywhere along this band.
    neck_bounds = (tail_x, tip + rules.tip_radius, tail_x + width, plan["body"][1])
    board = {
        "id": f"{BOARD_KEYS[plan['role']]}_fpc",
        "role": plan["role"],
        "physical_side": None,
        "units": "mm",
        "fpc": {
            "is_flexible": True,
            "construction": profile["stackup"]["construction"],
            "stackup": copy.deepcopy(profile["stackup"]),
        },
        "grid_registration": {
            "coordinate_system": "active_region_lower_left",
            "active_region": _bounds_dict((active_x, active_y, active_x + active_width, active_y + active_height)),
            "electrode_field": _bounds_dict(electrode_field),
            "rows": plan["rows"],
            "columns": plan["columns"],
            "pitch_x_mm": plan["pitch_x"],
            "pitch_y_mm": plan["pitch_y"],
        },
        "tail": {
            "length_mm": plan["tail_length"],
            "width_mm": round6(width),
            "side": "bottom",
            "connector_pins": plan["pins"],
            "connector_channels": plan["channels"],
            "connector_pitch_mm": rules.pitch,
            "contact_width_mm": rules.contact_width,
            "contact_length_mm": rules.contact_length,
            "contact_start_from_tip_mm": rules.tip_clearance,
            "first_contact_center_from_side_mm": rules.side_offset,
            "tip_corner_radius_mm": rules.tip_radius,
            "stiffener_length_mm": rules.stiffener_length,
            "bounds": _bounds_dict(tail_bounds),
            "neck_bounds": _bounds_dict(neck_bounds),
            **tail_extra,
        },
        "outline": {
            "kind": "polygon",
            "layer": "board_outline",
            "points": _round_ring(outline),
            "cutouts": [_round_ring(cutout) for cutout in cutouts],
        },
        "layers": {
            "top_copper": {"electrodes": electrodes, "routes": routes, "pads": pads},
            "top_coverlay_openings": _openings(electrodes, pads, plan, rules),
            "bottom_stiffener": [_stiffener(plan, profile, rules, corners)],
        },
        "construction": dict(construction),
        "metrics": {},
    }
    board["metrics"] = board_metrics(board)
    return board


# --------------------------------------------------------------------------
# Row board.
# --------------------------------------------------------------------------


def build_row_board(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    if row_bus(design):
        from .diagonal import build_row_board as build_diagonal_row_board

        return build_diagonal_row_board(design, profile)
    if design_mask(design) is not None:
        return _build_masked_row_board(design, profile)
    plan = row_plan(design, profile)
    rules = plan["rules"]
    rows = plan["rows"]
    active_x, active_y, active_width, active_height = plan["active"]
    _, _, body_width, body_height = plan["body"]
    width, tip = plan["tail_width"], plan["tip"]
    row_width = plan["row_width"]
    order = design["channel_order"]["rows"]
    # Logical row 1 is the upper sensor edge and uses the leftmost lane, so
    # the single-layer left-channel fan-out never crosses.
    nets = [f"ROW_{index:02d}" for index in range(1, rows + 1)]
    pads = _contacts(plan, nets, order, rules)
    contact_top = tip + rules.tip_clearance + rules.contact_length
    electrode_left = active_x - rules.overhang
    electrode_right = active_x + active_width + rules.overhang
    junction = plan["tail_top"]
    electrodes, routes = [], []
    for logical in range(1, rows + 1):
        physical_row = rows - logical
        center_y = active_y + physical_row * plan["pitch_y"] + row_width / 2
        lane_x = plan["lanes"][logical - 1]
        contact_x = plan["contact_x"][logical - 1]
        electrodes.append(
            _electrode(nets[logical - 1], "row_electrode", (electrode_left, center_y - row_width / 2, electrode_right, center_y + row_width / 2))
        )
        # Up the channel lane to the row, then right to the electrode's left end;
        # below the field the lane expands to its contact.
        fanout = [[contact_x, junction]]
        bend = plan["expansion"][logical - 1]
        if bend is not None:
            fanout += [[contact_x, bend[1]], [lane_x, bend[0]]]
        fanout += [[lane_x, round6(center_y)], [electrode_left, round6(center_y)]]
        tail = [[contact_x, contact_top], [contact_x, junction]]
        routes.append(_route_pieces(nets[logical - 1], tail, fanout, plan, {"fanout": "left_channel_non_crossing"}))
    electrodes.reverse()
    routes = [piece for pieces in reversed(routes) for piece in pieces]
    left, right = _tip_corners(0.0, width, tip, rules)
    outline = [[0.0, body_height], *left, *right, [width, 0.0], [body_width, 0.0], [body_width, body_height]]
    outline, smallest = fillet_concave_corners(outline, rules.fillet_radius, arc_step_rad=rules.arc_step)
    return _assemble(
        plan=plan,
        design=design,
        profile=profile,
        outline=outline,
        cutouts=[],
        electrodes=electrodes,
        routes=routes,
        pads=pads,
        corners=(left, right),
        tail_extra={},
        construction={
            "minimum_concave_fillet_radius_mm": None if smallest is None else round6(smallest),
            "fanout_bundle_pitch_mm": plan["bundle_pitch"],
            "bend_stagger_mm": plan["stagger"],
            "channel_width_mm": plan["channel_width"],
            "merger_taper_angle_deg": round6(plan["angle_deg"]),
            "merger_height_mm": plan["expansion_height"],
        },
    )


# --------------------------------------------------------------------------
# Column board.
# --------------------------------------------------------------------------


def _x_at(chain: list[list[float]], y: float) -> float:
    """X of a y-ascending chain at height ``y`` (clamped to its ends)."""

    if y <= chain[0][1]:
        return chain[0][0]
    for (x0, y0), (x1, y1) in zip(chain, chain[1:]):
        if y0 <= y <= y1:
            if y1 - y0 <= 1e-15:
                return min(x0, x1)
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return chain[-1][0]


def _monotone_hull(chain: list[list[float]], start: float, top: float, outward: float) -> list[list[float]]:
    """Running extreme of a y-ascending chain, seeded with the tail side ``start``.

    ``outward`` is -1 for the left side (running minimum of x) or +1 for the
    right side (running maximum).  The result never moves back inward as it
    rises, so the board widens monotonically from the tail to the body and
    is never narrower than the tail.
    """

    def further(a: float, b: float) -> bool:
        return (a - b) * outward > 1e-12

    points = [point for point in chain if point[1] < top - 1e-12]
    points.append([_x_at(chain, top), top])
    current = start
    answer = [[start, points[0][1]]]
    if further(points[0][0], current):
        current = points[0][0]
        answer.append([current, points[0][1]])
    for (previous_x, previous_y), (x, y) in zip(points, points[1:]):
        if not further(x, current):
            continue  # the envelope runs along or inside the hull: rise straight
        if further(current, previous_x):
            # The envelope re-crosses the hull inside this segment.
            fraction = (current - previous_x) / (x - previous_x)
            rise_to = previous_y + (y - previous_y) * fraction
        else:
            rise_to = previous_y  # the previous vertex lies on the hull
        answer.append([current, rise_to])
        answer.append([x, y])
        current = x
    if answer[-1][1] < top - 1e-12:
        answer.append([current, top])
    return clean_polyline(answer)


def build_column_board(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    if row_bus(design):
        from .diagonal import build_column_board as build_diagonal_column_board

        return build_diagonal_column_board(design, profile)
    if design_mask(design) is not None:
        return _build_masked_column_board(design, profile)
    plan = column_plan(design, profile)
    rules = plan["rules"]
    columns = plan["columns"]
    active_x, active_y, active_width, active_height = plan["active"]
    body_left, body_bottom, body_right, body_top = plan["body"]
    tail_x, width, tip = plan["tail_x"], plan["tail_width"], plan["tip"]
    order = design["channel_order"]["columns"]
    nets = [f"COL_{index:02d}" for index in range(1, columns + 1)]
    pads = _contacts(plan, nets, order, rules)
    contact_top = tip + rules.tip_clearance + rules.contact_length
    electrode_bottom = active_y - rules.overhang
    electrode_top = active_y + active_height + rules.overhang
    groups = plan["groups"]
    junction = plan["tail_top"]
    electrodes, routes, centrelines = [], [], []
    for index in range(columns):
        center = plan["centers"][index]
        deck = plan["decks"][index]
        contact = plan["contact_x"][index]
        # Up from the contact: the expansion out of the bundle, the bundle, the
        # convergence from the electrode's bottom end.
        fanout = [[contact, junction]]
        if plan["merger"][index] is not None:
            upper, lower = plan["merger"][index]
            fanout += [[contact, lower], [deck, upper]]
        if plan["entry"][index] is not None:
            upper, lower = plan["entry"][index]
            fanout += [[deck, lower], [center, upper]]
        fanout.append([center, electrode_bottom])
        tail = [[contact, contact_top], [contact, junction]]
        centrelines.append(clean_polyline([*tail, *fanout[1:]]))
        half = plan["column_width"] / 2
        middle = plan["active"][0] + index * plan["pitch_x"] + half
        electrodes.append(_electrode(nets[index], "column_electrode", (middle - half, electrode_bottom, middle + half, electrode_top)))
        extra = {
            "fanout": "dual_lane_slot_merger" if plan["lane_count"] == 2 else ("single_lane_direct" if plan["convergence"] == "direct" else "single_lane_merger"),
            "fanout_group": 1 if plan["lane_count"] == 1 or index < groups[0] else 2,
        }
        routes.extend(_route_pieces(nets[index], tail, fanout, plan, extra))
    # Outline: body rectangle (with the full margin below the active field),
    # then the outer-route envelopes joined monotonically to the tail band.
    left_env = offset_polyline(centrelines[0], plan["envelope"], left=True, arc_step_rad=rules.arc_step)
    right_env = offset_polyline(centrelines[-1], plan["envelope"], left=False, arc_step_rad=rules.arc_step)
    left_chain = _monotone_hull(left_env, tail_x, body_bottom, -1.0)
    right_chain = _monotone_hull(right_env, tail_x + width, body_bottom, 1.0)
    left_tip, right_tip = _tip_corners(tail_x, width, tip, rules)
    outline = [
        [body_left, body_top],
        [body_left, body_bottom],
        *reversed(left_chain),
        *left_tip,
        *right_tip,
        *right_chain,
        [body_right, body_bottom],
        [body_right, body_top],
    ]
    outline, smallest = fillet_concave_corners(clean_polyline(outline, closed=True), rules.fillet_radius, arc_step_rad=rules.arc_step)
    cutouts = []
    if plan["slot"] is not None:
        cutouts.append(arc_polygon_rounded_rect(plan["slot"], rules.fillet_radius, rules.arc_step))
    return _assemble(
        plan=plan,
        design=design,
        profile=profile,
        outline=outline,
        cutouts=cutouts,
        electrodes=electrodes,
        routes=routes,
        pads=pads,
        corners=(left_tip, right_tip),
        tail_extra={
            "fanout_lane_count": plan["lane_count"],
            "fanout_lane_channel_counts": groups,
        },
        construction={
            "minimum_concave_fillet_radius_mm": None if smallest is None else round6(smallest),
            "fanout_bundle_pitch_mm": plan["bundle_pitch"],
            "bend_stagger_mm": plan["stagger"],
            "entry_taper_angle_deg": round6(plan["entry_angle_deg"]),
            "entry_transition_height_mm": round6(plan["entry_height"]),
            "merger_taper_angle_deg": round6(plan["merger_angle_deg"]),
            "merger_height_mm": round6(plan["merger_height"]),
            "slot_bounds": None if plan["slot"] is None else _bounds_dict(plan["slot"]),
        },
    )


# --------------------------------------------------------------------------
# Masked boards (matrix.mask): the straight constructions.
# --------------------------------------------------------------------------
#
# A masked board is the unmasked R x C board of the same design with each
# electrode trimmed to its span (row_frame_spans, column_frame_spans):
# every net keeps its lane, contact and pin.  On the Row board the field
# slides toward the channel as far as the lane taper lets (row_taper), and
# each row's stub ends at its own electrode; on the Column board a column
# whose taxels stop short of the tail runs its stub straight down its own
# centre line from its raised electrode end to the unchanged entry bends.
# Both outlines follow the crossings: F, the crossing region P (each band's
# strip from its first to its last crossing edge, plus fillers between
# consecutive bands over their common span) dilated by the active-edge
# margin, gives the Row body's far side and the Column body's top.  The
# corners an unmasked board also has keep today's unrounded values, so a
# full span gives today's boards byte for byte; the steps are on the grid.
# The merged coverlay window becomes a polygon ring (the electrode windows
# plus fillers), unless every span is the same.


def _straight_classes(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, str]:
    """The construction classes of a masked design (:func:`mask_class`); ``ValueError`` outside them."""

    classes, issue = mask_class(design, profile)
    if issue is not None:
        raise ValueError(f"{issue['field']}: {issue['message']}")
    if classes is None:
        raise ValueError("the design has no field mask")
    return classes


def masked_row_plan(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """:func:`row_plan` of a masked design: the straight Row channel with the lane taper.

    The plan of the bounding R x C field (lanes, expansion, tail, height)
    with: ``spans`` (:func:`row_frame_spans`); the field's start ``active``
    x, ``max(margin, max_k (W_k - lo_k * pitch_x))`` with the lane taper
    ``W_k`` (:func:`row_taper`), the unmasked start when every row reaches
    the channel side; ``channel_width`` from it; ``right_chain``, the body's
    far side from its bottom corner ``[xb, 0]`` up to its top corner
    (:func:`_row_body_chain`); ``body``, ``outline_x`` and ``outline_size``
    of that body; and ``mask_class``.  The mask must be of the straight
    classes (:func:`mask_class`), else ``ValueError``.
    """

    classes = _straight_classes(design, profile)
    plan = dict(row_plan(design, profile))
    rules = plan["rules"]
    spans = row_frame_spans(design)
    active_x, active_y, active_width, active_height = plan["active"]
    if any(lo for lo, _ in spans):
        taper = row_taper(design, profile)
        active_x = max(rules.margin, max(round6(edge - round6(lo * plan["pitch_x"])) for edge, (lo, _) in zip(taper, spans)))
        if rules.row_channel == "tight":
            plan["channel_width"] = round6(active_x - rules.margin)
    plan["active"] = (active_x, active_y, active_width, active_height)
    plan["spans"] = spans
    chain = _row_body_chain(plan, spans)
    right = max(x for x, _ in chain)
    outer = max(right, plan["tail_width"])
    plan["right_chain"] = chain
    plan["body"] = (0.0, 0.0, right, plan["body"][3])
    plan["outline_x"] = (0.0, outer)
    plan["outline_size"] = (outer, plan["body"][3] + plan["tail_length"])
    plan["mask_class"] = classes
    return plan


def _row_body_chain(plan: Mapping[str, Any], spans: list[tuple[int, int]]) -> list[list[float]]:
    """The far side of a masked Row body: from its bottom corner ``[xb, 0]`` up to its top corner.

    F (the crossings dilated by the active-edge margin) as y-slabs gives the
    side.  Below the field the body holds the channel's expansion: its
    width ``xb`` is today's body-width rule taken from the bottom row's far
    crossing edge (at least the contact row the lanes expand to, and a step
    of zero or one fillet radius to the tail), and it keeps that width as
    high as the field reaches as far as its bottom row; above, the side
    follows F.  ``xb`` and the top keep today's unrounded values; the steps
    are on the layout grid.
    """

    rules = plan["rules"]
    rows = plan["rows"]
    active_x, active_y = plan["active"][0], plan["active"][1]
    pitch_x, pitch_y, cell_x, cell_y = plan["pitch_x"], plan["pitch_y"], plan["column_width"], plan["row_width"]
    margin = rules.margin
    dilated = []
    for row in range(rows, 0, -1):  # from the bottom row up
        lo, hi = spans[row - 1]
        low = active_y + (rows - row) * pitch_y
        dilated.append(
            (
                round6(active_x + lo * pitch_x - margin),
                round6(low - margin),
                round6(active_x + (hi * pitch_x + cell_x) + margin),
                round6(low + cell_y + margin),
            )
        )
    slabs = rect_union_slabs(band_union(dilated, 1), 1)
    far = spans[rows - 1][1]
    xb = _body_side(max(active_x + (far * pitch_x + cell_x) + margin, tail_width(rows, rules)), plan["tail_width"], 1.0, rules.fillet_radius)
    reach = slabs[0][3]
    chain = [[xb, 0.0]]
    x = xb
    for low, _, _, end in slabs:
        right = max(end, xb) if end >= reach - _FLOAT_NOISE_MM else end
        if abs(right - x) > _FLOAT_NOISE_MM:
            chain += [[x, low], [right, low]]
            x = right
    chain.append([x, plan["body"][3]])
    return chain


def masked_column_plan(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """:func:`column_plan` of a masked design: the straight Column fan-out with raised stubs.

    The plan of the bounding R x C field with ``spans``
    (:func:`column_frame_spans`), ``top_chain`` (the body's top from its
    right side to its left, :func:`_column_top_chain`) and ``mask_class``.
    The mask must be of the straight classes, else ``ValueError``.
    """

    classes = _straight_classes(design, profile)
    plan = dict(column_plan(design, profile))
    plan["spans"] = column_frame_spans(design)
    plan["top_chain"] = _column_top_chain(plan, plan["spans"])
    plan["mask_class"] = classes
    return plan


def _column_top_chain(plan: Mapping[str, Any], spans: list[tuple[int, int]]) -> list[list[float]]:
    """The top of a masked Column body, from ``[body_right, top]`` to ``[body_left, top]``.

    F's top as x-slabs, right to left, extended horizontally to the body
    sides where :func:`_body_side` moved them; below F the body keeps its
    full width down to its bottom (y = 0), where every stub, raised or not,
    enters its bends.  The full-height top keeps today's unrounded value;
    the steps are on the layout grid.
    """

    rules = plan["rules"]
    active_x, active_y = plan["active"][0], plan["active"][1]
    body_left, _, body_right, body_top = plan["body"]
    pitch_x, pitch_y, cell_x, cell_y = plan["pitch_x"], plan["pitch_y"], plan["column_width"], plan["row_width"]
    margin = rules.margin
    dilated = []
    for index, (low, high) in enumerate(spans):
        left = active_x + index * pitch_x
        dilated.append(
            (
                round6(left - margin),
                round6(active_y + low * pitch_y - margin),
                round6(left + cell_x + margin),
                round6(active_y + (high * pitch_y + cell_y) + margin),
            )
        )
    slabs = rect_union_slabs(band_union(dilated, 0), 0)
    full = round6(body_top)
    tops = [body_top if abs(end - full) <= _FLOAT_NOISE_MM else end for _, _, _, end in slabs]
    current = tops[-1]
    chain = [[body_right, current]]
    for (_, high, _, _), top in zip(reversed(slabs), reversed(tops)):
        if abs(top - current) > _FLOAT_NOISE_MM:
            chain += [[high, current], [high, top]]
            current = top
    chain.append([body_left, current])
    return chain


def _build_masked_row_board(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """The Row board of a masked design (the straight channel, :func:`masked_row_plan`)."""

    plan = masked_row_plan(design, profile)
    rules = plan["rules"]
    rows = plan["rows"]
    active_x, active_y = plan["active"][0], plan["active"][1]
    pitch_x, pitch_y, cell_x, cell_y = plan["pitch_x"], plan["pitch_y"], plan["column_width"], plan["row_width"]
    width, tip = plan["tail_width"], plan["tip"]
    nets = [f"ROW_{index:02d}" for index in range(1, rows + 1)]
    pads = _contacts(plan, nets, design["channel_order"]["rows"], rules)
    finger_top = tip + rules.tip_clearance + rules.contact_length
    junction = plan["tail_top"]
    lanes = plan["lanes"]
    electrodes, routes = [], []
    for logical, (lo, hi) in enumerate(plan["spans"], start=1):
        center_y = active_y + (rows - logical) * pitch_y + cell_y / 2
        start = active_x + lo * pitch_x - rules.overhang
        end = active_x + (hi * pitch_x + cell_x) + rules.overhang
        contact_x = plan["contact_x"][logical - 1]
        electrodes.append(_electrode(nets[logical - 1], "row_electrode", (start, center_y - cell_y / 2, end, center_y + cell_y / 2)))
        # Today's lane and expansion; the stub ends at the row's own electrode.
        fanout = [[contact_x, junction]]
        bend = plan["expansion"][logical - 1]
        if bend is not None:
            fanout += [[contact_x, bend[1]], [lanes[logical - 1], bend[0]]]
        fanout += [[lanes[logical - 1], round6(center_y)], [start, round6(center_y)]]
        tail = [[contact_x, finger_top], [contact_x, junction]]
        routes.append(_route_pieces(nets[logical - 1], tail, fanout, plan, {"fanout": "left_channel_non_crossing"}))
    electrodes.reverse()
    routes = [piece for pieces in reversed(routes) for piece in pieces]
    left_tip, right_tip = _tip_corners(0.0, width, tip, rules)
    outline = [[0.0, plan["body"][3]], *left_tip, *right_tip, [width, 0.0], *plan["right_chain"]]
    outline, smallest = fillet_concave_corners(outline, rules.fillet_radius, arc_step_rad=rules.arc_step)
    board = _assemble(
        plan=plan,
        design=design,
        profile=profile,
        outline=outline,
        cutouts=[],
        electrodes=electrodes,
        routes=routes,
        pads=pads,
        corners=(left_tip, right_tip),
        tail_extra={},
        construction={
            "minimum_concave_fillet_radius_mm": None if smallest is None else round6(smallest),
            "fanout_bundle_pitch_mm": plan["bundle_pitch"],
            "bend_stagger_mm": plan["stagger"],
            "channel_width_mm": plan["channel_width"],
            "merger_taper_angle_deg": round6(plan["angle_deg"]),
            "merger_height_mm": plan["expansion_height"],
        },
    )
    _masked_field_window(board, plan["spans"], rules, 1)
    _mark_masked(board, design, plan["mask_class"], rules, 1)
    return board


def _build_masked_column_board(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """The Column board of a masked design (the straight fan-out, :func:`masked_column_plan`)."""

    return _masked_column_board(design, profile, masked_column_plan(design, profile))


def _masked_column_board(design: Mapping[str, Any], profile: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    """The straight Column board of a masked design from its plan (:func:`masked_column_plan`, or the same plan with
    other ``mask_class``: the diagonal Row bus's Column board, :mod:`engine.diagonal`, on its design with the mask
    written out)."""

    rules = plan["rules"]
    columns = plan["columns"]
    active_x, active_y = plan["active"][0], plan["active"][1]
    pitch_x, pitch_y, cell_x, cell_y = plan["pitch_x"], plan["pitch_y"], plan["column_width"], plan["row_width"]
    tail_x, width, tip = plan["tail_x"], plan["tail_width"], plan["tip"]
    nets = [f"COL_{index:02d}" for index in range(1, columns + 1)]
    pads = _contacts(plan, nets, design["channel_order"]["columns"], rules)
    groups = plan["groups"]
    electrodes, routes = [], []
    for index, (low, high) in enumerate(plan["spans"]):
        bottom = active_y + low * pitch_y - rules.overhang
        top = active_y + (high * pitch_y + cell_y) + rules.overhang
        tail, fanout = _column_fanout(plan, index)
        half = cell_x / 2
        middle = active_x + index * pitch_x + half
        electrodes.append(_electrode(nets[index], "column_electrode", (middle - half, bottom, middle + half, top)))
        extra = {
            "fanout": "dual_lane_slot_merger" if plan["lane_count"] == 2 else ("single_lane_direct" if plan["convergence"] == "direct" else "single_lane_merger"),
            "fanout_group": 1 if plan["lane_count"] == 1 or index < groups[0] else 2,
        }
        routes.extend(_route_pieces(nets[index], tail, fanout, plan, extra))
    left_tip, right_tip = _tip_corners(tail_x, width, tip, rules)
    outline, smallest = fillet_concave_corners(masked_column_outline(plan), rules.fillet_radius, arc_step_rad=rules.arc_step)
    cutouts = []
    if plan["slot"] is not None:
        cutouts.append(arc_polygon_rounded_rect(plan["slot"], rules.fillet_radius, rules.arc_step))
    board = _assemble(
        plan=plan,
        design=design,
        profile=profile,
        outline=outline,
        cutouts=cutouts,
        electrodes=electrodes,
        routes=routes,
        pads=pads,
        corners=(left_tip, right_tip),
        tail_extra={
            "fanout_lane_count": plan["lane_count"],
            "fanout_lane_channel_counts": groups,
        },
        construction={
            "minimum_concave_fillet_radius_mm": None if smallest is None else round6(smallest),
            "fanout_bundle_pitch_mm": plan["bundle_pitch"],
            "bend_stagger_mm": plan["stagger"],
            "entry_taper_angle_deg": round6(plan["entry_angle_deg"]),
            "entry_transition_height_mm": round6(plan["entry_height"]),
            "merger_taper_angle_deg": round6(plan["merger_angle_deg"]),
            "merger_height_mm": round6(plan["merger_height"]),
            "slot_bounds": None if plan["slot"] is None else _bounds_dict(plan["slot"]),
        },
    )
    _masked_field_window(board, plan["spans"], rules, 0)
    _mark_masked(board, design, plan["mask_class"], rules, 0)
    return board


def masked_column_outline(plan: Mapping[str, Any]) -> list[list[float]]:
    """The masked Column board's outline before its fillets (counter-clockwise, its frame): the body's top chain, the
    fan-out sides (:func:`_column_side_chains`) and the tail with its rounded tip."""

    rules = plan["rules"]
    body_left, body_bottom, body_right, _ = plan["body"]
    left_chain, right_chain = _column_side_chains(plan)
    left_tip, right_tip = _tip_corners(plan["tail_x"], plan["tail_width"], plan["tip"], rules)
    top_chain = plan["top_chain"]
    outline = [
        top_chain[-1],
        [body_left, body_bottom],
        *reversed(left_chain),
        *left_tip,
        *right_tip,
        *right_chain,
        [body_right, body_bottom],
        *top_chain[:-1],
    ]
    return clean_polyline(outline, closed=True)


def _column_fanout(plan: Mapping[str, Any], index: int) -> tuple[list, list]:
    """``(tail, fanout)`` centrelines of a masked Column board's route ``index`` (from the contact end).

    Today's merger and entry bends; the stub then rises on the column's own
    centre line to its electrode's near end, raised by its first row slot.
    """

    rules = plan["rules"]
    low = plan["spans"][index][0]
    bottom = plan["active"][1] + low * plan["pitch_y"] - rules.overhang
    center, deck, contact = plan["centers"][index], plan["decks"][index], plan["contact_x"][index]
    junction = plan["tail_top"]
    fanout = [[contact, junction]]
    if plan["merger"][index] is not None:
        upper, lower = plan["merger"][index]
        fanout += [[contact, lower], [deck, upper]]
    if plan["entry"][index] is not None:
        upper, lower = plan["entry"][index]
        fanout += [[deck, lower], [center, upper]]
    fanout.append([center, bottom])
    tail = [[contact, plan["tip"] + rules.tip_clearance + rules.contact_length], [contact, junction]]
    return tail, fanout


def _column_side_chains(plan: Mapping[str, Any]) -> tuple[list, list]:
    """The masked Column outline's two fan-out sides (y ascending): the outer routes' envelopes joined
    monotonically to the tail up to the body bottom, as :func:`build_column_board` makes them."""

    rules = plan["rules"]
    tail_x, width, body_bottom = plan["tail_x"], plan["tail_width"], plan["body"][1]
    first, last = (_column_fanout(plan, index) for index in (0, plan["columns"] - 1))
    left_env = offset_polyline(clean_polyline([*first[0], *first[1][1:]]), plan["envelope"], left=True, arc_step_rad=rules.arc_step)
    right_env = offset_polyline(clean_polyline([*last[0], *last[1][1:]]), plan["envelope"], left=False, arc_step_rad=rules.arc_step)
    return _monotone_hull(left_env, tail_x, body_bottom, -1.0), _monotone_hull(right_env, tail_x + width, body_bottom, 1.0)


def _masked_field_window(board: dict[str, Any], spans: list[tuple[int, int]], rules: Rules, axis: int) -> None:
    """Give a masked board's merged field window the shape of its electrodes.

    The ring is the union of each electrode's window (the electrode plus
    the coverlay expansion) and, between consecutive electrodes (stacked
    along ``axis``), a filler over their common extent plus the expansion:
    ``{kind: "electrode_field_opening", shape: "polygon", net: null, nets,
    opening_for, points}``, with no rectangle fields, so a reader that knows
    only rectangles fails.  Per-electrode windows stay rectangles, and so
    does the merged window when every span is the same (today's form).
    """

    openings = board["layers"]["top_coverlay_openings"]
    field = openings[0]
    if field["kind"] != "electrode_field_opening" or all(span == spans[0] for span in spans):
        return
    grow = rules.expansion
    boxes = sorted(
        (
            (round6(x0 - grow), round6(y0 - grow), round6(x1 + grow), round6(y1 + grow))
            for x0, y0, x1, y1 in (rect_bounds(electrode) for electrode in board["layers"]["top_copper"]["electrodes"])
        ),
        key=lambda box: box[axis],
    )
    openings[0] = {
        "kind": "electrode_field_opening",
        "shape": "polygon",
        "net": None,
        "nets": field["nets"],
        "opening_for": field["opening_for"],
        "points": band_ring(boxes, axis),
    }


def _mark_masked(board: dict[str, Any], design: Mapping[str, Any], classes: Mapping[str, str], rules: Rules, axis: int) -> None:
    """The masked board's records: ``grid_registration`` ``taxel_mask``, ``active_outline`` and
    ``active_taxel_count``, ``construction.mask_class`` and ``metrics.active_taxel_count``.

    ``active_outline`` is P from the board's own electrodes (each without its
    overhang, plus the fillers between consecutive electrodes, stacked along
    ``axis``), a counter-clockwise ring on the layout grid.
    """

    mask = design_mask(design)
    along = 1 - axis
    strips = []
    for electrode in board["layers"]["top_copper"]["electrodes"]:
        box = list(rect_bounds(electrode))
        box[along] += rules.overhang
        box[along + 2] -= rules.overhang
        strips.append(tuple(round6(value) for value in box))
    strips.sort(key=lambda box: box[axis])
    registration = board["grid_registration"]
    registration["taxel_mask"] = {
        "format": "row_spans/v1",
        "rows": int(design["matrix"]["rows"]),
        "columns": int(design["matrix"]["columns"]),
        "row_spans": [[first, last] for first, last in mask],
    }
    registration["active_outline"] = band_ring(strips, axis)
    count = 0
    for first, last in mask:
        count += last - first + 1
    registration["active_taxel_count"] = count
    board["construction"]["mask_class"] = dict(classes)
    board["metrics"] = board_metrics(board)


# --------------------------------------------------------------------------
# Rotation, physical assignment, metrics.
# --------------------------------------------------------------------------


def apply_tail_side(board: dict[str, Any], side: str) -> None:
    """Rotate the complete board so the tail exits on ``side``; normalize to 0,0."""

    turns = TAIL_TURNS[side]
    outline = board["outline"]["points"]
    rotated = [rotate_quarter(point, turns) for point in outline]
    min_x = min(point[0] for point in rotated)
    min_y = min(point[1] for point in rotated)

    def convert(point: list[float]) -> list[float]:
        x, y = rotate_quarter(point, turns)
        return [round6(x - min_x), round6(y - min_y)]

    def convert_bounds(bounds: Mapping[str, float]) -> dict[str, float]:
        corners = bounds_corners((bounds["x"], bounds["y"], bounds["x"] + bounds["width"], bounds["y"] + bounds["height"]))
        return _bounds_dict(bounds_of([convert(corner) for corner in corners]))

    def convert_rect(rect: dict[str, Any]) -> None:
        box = bounds_of([convert(corner) for corner in bounds_corners(rect_bounds(rect))])
        rect.update(anchored_rect(*box, rect["anchor"]))

    board["outline"]["points"] = [convert(point) for point in outline]
    board["outline"]["cutouts"] = [[convert(point) for point in cutout] for cutout in board["outline"]["cutouts"]]
    copper = board["layers"]["top_copper"]
    for rect in [*copper["electrodes"], *copper["pads"], *board["layers"]["top_coverlay_openings"]]:
        if rect.get("shape") == "polygon":  # a masked board's field window
            rect["points"] = [convert(point) for point in rect["points"]]
        else:
            convert_rect(rect)
    for route in copper["routes"]:
        route["points"] = [convert(point) for point in route["points"]]
    for stiffener in board["layers"]["bottom_stiffener"]:
        stiffener["points"] = [convert(point) for point in stiffener["points"]]
    registration = board["grid_registration"]
    for key in ("active_region", "electrode_field"):
        registration[key] = convert_bounds(registration[key])
    if "active_outline" in registration:  # masked boards
        registration["active_outline"] = [convert(point) for point in registration["active_outline"]]
    for key in ("bounds", "neck_bounds"):
        board["tail"][key] = convert_bounds(board["tail"][key])
    slot = board["construction"].get("slot_bounds")
    if slot is not None:
        board["construction"]["slot_bounds"] = convert_bounds(slot)
    board["tail"]["side"] = side
    board["metrics"] = board_metrics(board)


def apply_physical_assignment(row_board: dict[str, Any], column_board: dict[str, Any], mapping: Mapping[str, str]) -> None:
    boards = {"rows": row_board, "columns": column_board}
    for physical_side, role in mapping.items():
        boards[role]["physical_side"] = physical_side
        boards[role]["id"] = f"{physical_side}_{role}_fpc"


def board_metrics(board: Mapping[str, Any]) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = bounds_of(board["outline"]["points"])
    copper = board["layers"]["top_copper"]
    channels = sum(1 for pad in copper["pads"] if pad["kind"] == "connector_pad")
    metrics = {
        "outline_width_mm": round6(max_x - min_x),
        "outline_height_mm": round6(max_y - min_y),
        "outline_bbox_mm": _bounds_dict((min_x, min_y, max_x, max_y)),
        "channel_count": channels,
        "contact_count": len(copper["pads"]),
        "electrode_count": len(copper["electrodes"]),
        "route_count": len(copper["routes"]),
        "coverlay_opening_count": len(board["layers"]["top_coverlay_openings"]),
        "stiffener_count": len(board["layers"]["bottom_stiffener"]),
        "routed_cutout_count": len(board["outline"].get("cutouts", [])),
    }
    registration = board.get("grid_registration") or {}
    if "active_taxel_count" in registration:  # masked boards
        metrics["active_taxel_count"] = registration["active_taxel_count"]
    return metrics


# --------------------------------------------------------------------------
# Feasibility: inputs inside the profile limits that cannot be built.
# --------------------------------------------------------------------------


def _with(design: Mapping[str, Any], values: Mapping[tuple[str, str], float]) -> dict[str, Any]:
    changed = {name: (dict(part) if isinstance(part, Mapping) else part) for name, part in design.items()}
    for (section, key), value in values.items():
        changed[section][key] = value
    return changed


def _fits(plan: Mapping[str, Any], limits: Mapping[str, Any]) -> bool:
    short_side, long_side = sorted(plan["outline_size"])
    return short_side <= float(limits["maximum_outline_short_side_mm"]) + 1e-9 and long_side <= float(limits["maximum_outline_long_side_mm"]) + 1e-9


# A size "move" lowers one field (or a pitch together with its taxel width)
# from its current value (t = 1) towards its lowest legal value (t = 0); it
# returns the rounded values that are reported, so every bound is verified.


def floor4(value: float) -> float:
    """Round a reported upper bound down to 4 decimals, so applying it always works."""

    return math.floor(value * 10000 + 1e-9) / 10000


def _linear_move(section: str, key: str, low: float, high: float, integer: bool):
    if integer:
        low, high = int(low), int(high)
        return lambda t: {(section, key): int(math.floor(low + (high - low) * t + 1e-9))}
    low = math.ceil(low * 10000 - 1e-9) / 10000
    return lambda t: {(section, key): max(low, floor4(low + (high - low) * t))}


def _scaled_pitch_move(pitch_key: str, width_key: str, pitch: float, width: float, low: float, rules: Rules):
    """Lower a pitch and keep its taxel fill (or the widest legal taxel)."""

    fill = width / pitch
    base = _linear_move("matrix", pitch_key, low, pitch, False)

    def values(t: float) -> dict[tuple[str, str], float]:
        answer = base(t)
        new_pitch = answer[("matrix", pitch_key)]
        answer[("matrix", width_key)] = max(rules.min_electrode_width, floor4(min(fill * new_pitch, new_pitch - rules.electrode_gap)))
        return answer

    return values


def _largest_step(move, accepts) -> dict[tuple[str, str], float] | None:
    """Values of ``move`` at the largest t in [0, 1] that ``accepts``."""

    if not accepts(move(0.0)):
        return None
    low, high = 0.0, 1.0
    for _ in range(40):
        middle = (low + high) / 2
        if accepts(move(middle)):
            low = middle
        else:
            high = middle
    return move(low)


def _describe(values: Mapping[tuple[str, str], float]) -> str:
    return " with ".join(
        f"{section}.{key} <= {value}" if isinstance(value, int) else f"{section}.{key} <= {value:.4f} mm"
        for (section, key), value in values.items()
    )


def _size_advice(design: Mapping[str, Any], profile: Mapping[str, Any], role: str, planner) -> list[dict[tuple[str, str], float]]:
    """Verified ways to bring one board inside the fabrication maximum."""

    rules = Rules(profile)
    limits = profile["limits"]
    matrix = design["matrix"]
    side = "top" if design["role_mapping"]["top"] == role else "bottom"
    minimum_pitch = float(limits["minimum_pitch_mm"])
    pitch_x, pitch_y = float(matrix["pitch_x_mm"]), float(matrix["pitch_y_mm"])
    width_x, width_y = float(matrix["taxel_width_mm"]), float(matrix["taxel_height_mm"])

    def accepts(values: Mapping[tuple[str, str], float]) -> bool:
        changed = _with(design, values)
        for pitch_key, width_key in (("pitch_x_mm", "taxel_width_mm"), ("pitch_y_mm", "taxel_height_mm")):
            pitch, width = round6(changed["matrix"][pitch_key]), round6(changed["matrix"][width_key])
            if width + rules.epsilon < rules.min_electrode_width or width + rules.electrode_gap > pitch + rules.epsilon:
                return False
        return _fits(planner(changed, profile), limits)

    scaled_floor = rules.min_electrode_width + rules.electrode_gap
    single = [
        _linear_move("tail", f"{side}_length_mm", rules.minimum_tail, float(design["tail"][f"{side}_length_mm"]), False),
        _linear_move("matrix", "pitch_y_mm", max(minimum_pitch, width_y + rules.electrode_gap), pitch_y, False),
        _linear_move("matrix", "pitch_x_mm", max(minimum_pitch, width_x + rules.electrode_gap), pitch_x, False),
        _linear_move("matrix", "rows", int(limits["minimum_rows"]), int(matrix["rows"]), True),
        _linear_move("matrix", "columns", int(limits["minimum_columns"]), int(matrix["columns"]), True),
    ]
    if design_mask(design) is not None:
        # A field mask has one span per row and names columns: fewer rows or columns would break it.
        # Pitch and tail moves keep it valid (it is in index space).
        single = single[:3]
    found = [values for values in (_largest_step(move, accepts) for move in single) if values is not None]
    scaled = [
        _scaled_pitch_move("pitch_y_mm", "taxel_height_mm", pitch_y, width_y, max(minimum_pitch, scaled_floor, rules.min_electrode_width * pitch_y / width_y), rules),
        _scaled_pitch_move("pitch_x_mm", "taxel_width_mm", pitch_x, width_x, max(minimum_pitch, scaled_floor, rules.min_electrode_width * pitch_x / width_x), rules),
    ]
    for plain, move in ((("matrix", "pitch_y_mm"), scaled[0]), (("matrix", "pitch_x_mm"), scaled[1])):
        if not any(plain in values for values in found):
            values = _largest_step(move, accepts)
            if values is not None:
                found.append(values)
    if found:
        return found
    # No single change is enough: lower two fields together, in step.
    moves = single + scaled
    for index, first in enumerate(moves):
        for second in moves[index + 1 :]:
            if set(first(1.0)) & set(second(1.0)):
                continue
            values = _largest_step(lambda t, a=first, b=second: {**a(t), **b(t)}, accepts)
            if values is not None:
                found.append(values)
                if len(found) == 3:
                    return found
    return found


def feasibility_errors(design: Mapping[str, Any], profile: Mapping[str, Any]) -> list[dict[str, str]]:
    """Field-level errors (with the feasible bound) for designs that cannot be built."""

    limits = profile["limits"]
    errors: list[dict[str, str]] = []
    # Without a verified bound: a masked design's rows and columns change only together with its mask.
    fallback = (
        ("matrix.mask", "reduce matrix.rows and matrix.columns, and matrix.mask with them") if design_mask(design) is not None
        else ("matrix.rows", "reduce matrix.rows and matrix.columns")
    )
    if row_bus(design):
        errors.extend(_diagonal_size_errors(design, profile, fallback))
    for role, planner, plan in () if row_bus(design) else (("rows", row_plan, row_plan(design, profile)), ("columns", column_plan, column_plan(design, profile))):
        if _fits(plan, limits):
            continue
        width, height = plan["outline_size"]
        advice = _size_advice(design, profile, role, planner)
        field = "{}.{}".format(*next(iter(advice[0]))) if advice else fallback[0]
        hint = "; ".join(_describe(values) for values in advice) or fallback[1]
        errors.append(
            {
                "code": "E_BOARD_SIZE",
                "field": field,
                "message": (
                    f"The {BOARD_KEYS[role]} FPC outline would be {width:.3f} x {height:.3f} mm, larger than the "
                    f"{limits['maximum_outline_short_side_mm']:g} x {limits['maximum_outline_long_side_mm']:g} mm fabrication "
                    f"maximum (either orientation). Any one of: {hint}."
                ),
            }
        )
    # A masked design builds when its mask is of a construction class the engine has (the straight Row
    # channel and Column fan-out, claude/specs/masked-field/PLAN.md phase P2); otherwise E_MASK_ROUTING
    # names the first row or column outside them and the fix.
    _, issue = mask_class(design, profile)
    if issue is not None:
        errors.append(issue)
    return errors
