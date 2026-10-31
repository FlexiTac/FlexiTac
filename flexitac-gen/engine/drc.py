"""Whole-board design-rule check run on the emitted (rotated) layout.

The check is deterministic, stdlib-only and independent of how the geometry
was constructed: it reads only the board's layers, outline and tail record,
and from the design only its routing values (the bundle trace width and the
trace space the routes must keep; a pair with a wide tail piece keeps the
finger-section spacing, the contact pitch less the finger width, as the
contacts' own traces do).
Candidate pairs come from a sort-and-sweep over bounding boxes expanded by
the largest rule, so every pair that can violate a rule is examined and the
violation counters are exact.  Rule comparisons use the profile's numerical
epsilon (``drc.numeric_epsilon_mm``) and no other tolerance; the generator
places every feature a rule meets exactly on the 1e-6 mm layout grid, so the
rounding of the emitted coordinates never consumes that epsilon.  The one
derived requirement is the concave fillet radius, which allows the sagitta
of the profile's polygonal arcs (``R * cos(arc step / 2)``).
"""

from __future__ import annotations

import math
from typing import Any, Iterator, Mapping, Sequence

from .geometry import (
    band_ring,
    bounds_corners,
    bounds_of,
    box_gap,
    clip_ring_above,
    clip_segment_outside_box,
    is_orthogonally_convex,
    is_rectilinear,
    point_box_distance,
    point_in_polygon,
    point_segment_distance,
    polygon_edges,
    rect_bounds,
    rect_corners,
    ring_deviation,
    round6,
    segment_box_distance,
    segment_distance,
    segment_parts_off_box_boundary,
    segments_intersect,
    signed_area,
    turn_angle,
)
from .diagonal import ROW_BUS_VERSION
from .layout import BOARD_KEYS, Rules, bundle_values

DRC_VERSION = "whole-board-v3"
# Extra search reach (beyond each rule) used only to report measured minima.
_REPORT_REACH_MM = 2.0
# Floating-point guards (not manufacturing rules): zero-length edges, flat
# vertices, and the 1e-6 mm coordinate rounding of a fillet arc's chords.
_TINY_MM = 1e-12
_FLAT_TURN_RAD = 1e-9
_ARC_CHORD_SLACK_MM = 1e-5


def _bbox_pairs(first: Sequence[tuple], second: Sequence[tuple] | None, margin: float) -> Iterator[tuple[int, int]]:
    """Yield index pairs whose boxes are within ``margin`` (sort-and-sweep on x)."""

    same = second is None
    entries = [(box[0], 0, index, box) for index, box in enumerate(first)]
    if not same:
        entries += [(box[0], 1, index, box) for index, box in enumerate(second)]
    entries.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
    active: tuple[list, list] = ([], [])
    for x0, group, index, box in entries:
        other = group if same else 1 - group
        kept = []
        for other_index, other_box in active[other]:
            if other_box[2] + margin < x0:
                continue
            kept.append((other_index, other_box))
            if other_box[1] - margin <= box[3] and box[1] - margin <= other_box[3]:
                if same or group == 1:
                    yield (other_index, index)
                else:
                    yield (index, other_index)
        active[other][:] = kept
        active[group].append((index, box))


class _Item:
    """One copper feature: a route segment (capsule) or a pad/electrode box."""

    __slots__ = ("kind", "net", "first", "second", "box", "radius", "bbox", "ref", "piece")

    def __init__(self, kind: str, net: str, *, first=None, second=None, box=None, radius: float = 0.0, ref=None, piece=None) -> None:
        self.kind = kind
        self.net = net
        self.piece = piece  # a route's segment (tail or fanout)
        self.first = first
        self.second = second
        self.box = box
        self.radius = radius
        self.ref = ref
        if box is not None:
            self.bbox = box
        else:
            self.bbox = (
                min(first[0], second[0]) - radius,
                min(first[1], second[1]) - radius,
                max(first[0], second[0]) + radius,
                max(first[1], second[1]) + radius,
            )

    def gap(self, other: "_Item") -> float:
        if self.box is None and other.box is None:
            return segment_distance(self.first, self.second, other.first, other.second) - self.radius - other.radius
        if self.box is None:
            return segment_box_distance(self.first, self.second, other.box) - self.radius
        if other.box is None:
            return segment_box_distance(other.first, other.second, self.box) - other.radius
        return box_gap(self.box, other.box)

    def edge_distance(self, start: Sequence[float], end: Sequence[float]) -> float:
        if self.box is None:
            return segment_distance(self.first, self.second, start, end) - self.radius
        return segment_box_distance(start, end, self.box)

    def anchor_point(self) -> list[float]:
        if self.box is None:
            return [(self.first[0] + self.second[0]) / 2, (self.first[1] + self.second[1]) / 2]
        return [(self.box[0] + self.box[2]) / 2, (self.box[1] + self.box[3]) / 2]


class _Check:
    """Minimum (or maximum) measurement of one rule with an exact violation count."""

    def __init__(self, rule: str, required: float | None, *, maximum: bool = False) -> None:
        self.rule = rule
        self.required = required
        self.maximum = maximum
        self.measured: float | None = None
        self.where: Any = None
        self.violations = 0

    def add(self, value: float, where: Any, epsilon: float, required: float | None = None) -> None:
        """Measure ``value``; it violates the record's rule, or ``required`` when given."""

        # The extreme is tracked at the reported resolution: among values equal
        # there the first location in the (deterministic) sweep order is kept,
        # so float noise, which differs between Python versions, never moves it.
        if self.measured is None or (
            round6(value) > round6(self.measured) if self.maximum else round6(value) < round6(self.measured)
        ):
            self.measured = value
            self.where = where
        limit = self.required if required is None else required
        if limit is not None:
            failed = value > limit + epsilon if self.maximum else value < limit - epsilon
            if failed:
                self.violations += 1

    def fail(self, where: Any = None) -> None:
        self.violations += 1
        if self.where is None:
            self.where = where

    def record(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "required_mm": None if self.required is None else round6(self.required),
            "measured_mm": None if self.measured is None else round6(self.measured),
            "comparison": "max<=" if self.maximum else "min>=",
            "violation_count": self.violations,
            "passed": self.violations == 0,
            "where": self.where,
        }


def verify_board(board: Mapping[str, Any], profile: Mapping[str, Any], design: Mapping[str, Any]) -> dict[str, Any]:
    """Run the whole-board DRC; return ``{errors, warnings, measurements}``.

    ``design`` is the canonical design the board was built from; its
    ``routing`` sets the route rule (``trace_space_mm``) and the width every
    fan-out piece must have (``trace_width_mm``).  A route pair with a tail
    piece must keep the finger-section spacing instead (the contact pitch
    less the finger width, which no trace space exceeds); the
    ``route_route_clearance`` record reports those pairs as its
    ``finger_section``.
    """

    rules = Rules(profile)
    trace_width, trace_space, _ = bundle_values(design)
    epsilon = rules.epsilon
    role = str(board["role"])
    key = BOARD_KEYS[role]
    copper = board["layers"]["top_copper"]
    routes = list(copper["routes"])
    pads = list(copper["pads"])
    electrodes = list(copper["electrodes"])
    openings = list(board["layers"]["top_coverlay_openings"])
    stiffeners = list(board["layers"]["bottom_stiffener"])
    outline = [list(map(float, point)) for point in board["outline"]["points"]]
    cutouts = [[list(map(float, point)) for point in cutout] for cutout in board["outline"].get("cutouts", [])]
    route_rule = trace_space
    finger_rule = max(route_rule, rules.pitch - rules.finger_width)
    finger_section = _Check("finger_section", finger_rule)
    pair_rules = {
        ("route", "route"): ("route_route_clearance", route_rule),
        ("pad", "route"): ("pad_trace_clearance", rules.pad_to_trace),
        ("pad", "pad"): ("pad_pad_clearance", rules.pad_space),
        ("electrode", "electrode"): ("electrode_electrode_clearance", rules.electrode_gap),
        ("electrode", "route"): ("electrode_route_clearance", route_rule),
        ("electrode", "pad"): ("electrode_pad_clearance", route_rule),
    }
    checks: dict[str, _Check] = {name: _Check(name, value) for name, value in pair_rules.values()}

    items: list[_Item] = []
    route_segment_count = 0
    for route_index, route in enumerate(routes):
        radius = float(route["width_mm"]) / 2
        points = [list(map(float, point)) for point in route["points"]]
        segments = [(a, b) for a, b in zip(points, points[1:]) if math.dist(a, b) > 0]
        if not segments:
            segments = [(points[0], points[0])]  # a dot is still copper
        for segment_index, (start, end) in enumerate(segments):
            route_segment_count += 1
            items.append(
                _Item("route", route["net"], first=start, second=end, radius=radius, ref=(route_index, segment_index), piece=route.get("segment"))
            )
    for pad in pads:
        items.append(_Item("pad", pad["net"], box=rect_bounds(pad), ref=pad["pin"]))
    for electrode in electrodes:
        items.append(_Item("electrode", electrode["net"], box=rect_bounds(electrode), ref=electrode["net"]))

    # Inter-net copper clearance for every pair type.  Pairs are gathered
    # well beyond the largest rule so the reported minima are real measured
    # values; every pair that could violate a rule is inside this reach.
    largest_rule = max(finger_rule, *(value for _, value in pair_rules.values())) + _REPORT_REACH_MM
    route_pair = {"overlaps": 0, "violations": 0, "center": math.inf, "gap": math.inf, "pair": None}
    for first_index, second_index in _bbox_pairs([item.bbox for item in items], None, largest_rule + epsilon):
        first, second = items[first_index], items[second_index]
        if first.net == second.net:
            continue
        kinds = tuple(sorted((first.kind, second.kind)))
        name, required = pair_rules[kinds]
        # A wide tail piece keeps the finger-section spacing to every other net's route.
        finger = kinds == ("route", "route") and "tail" in (first.piece, second.piece)
        if finger:
            required = finger_rule
        gap = first.gap(second)
        checks[name].add(gap, sorted([first.net, second.net]), epsilon, required)
        if finger:
            finger_section.add(gap, sorted([first.net, second.net]), epsilon)
        if kinds == ("route", "route"):
            if gap < -epsilon:
                route_pair["overlaps"] += 1
            if gap < required - epsilon:
                route_pair["violations"] += 1
            if round6(gap) < round6(route_pair["gap"]):  # the first pair among equal reported gaps, as in _Check
                route_pair.update(
                    gap=gap,
                    center=gap + first.radius + second.radius,
                    pair={
                        "nets": [first.net, second.net],
                        "segments": [first.piece, second.piece],
                        "segment_indices": [first.ref[1], second.ref[1]],
                    },
                )

    # Copper to the outer outline and to routed cutouts; containment.
    edge_check = _Check("copper_to_outline", rules.copper_to_edge)  # pads and electrodes
    cutout_check = _Check("copper_to_cutout", rules.copper_to_cutout)
    route_edge = _Check("route_to_outline", rules.copper_to_edge)
    containment = _Check("copper_inside_outline", None)
    edges = [(start, end, "outline") for start, end in polygon_edges(outline)]
    for cutout in cutouts:
        edges += [(start, end, "cutout") for start, end in polygon_edges(cutout)]
    edge_boxes = [bounds_of([start, end]) for start, end, _ in edges]
    nearest: list[dict[str, float]] = [{} for _ in items]
    reach = max(rules.copper_to_edge, rules.copper_to_cutout) + rules.margin + _REPORT_REACH_MM
    for item_index, edge_index in _bbox_pairs([item.bbox for item in items], edge_boxes, reach):
        start, end, kind = edges[edge_index]
        distance = items[item_index].edge_distance(start, end)
        if distance < nearest[item_index].get(kind, math.inf):
            nearest[item_index][kind] = distance
    for item, distances in zip(items, nearest):
        where = [item.kind, item.net]
        if "outline" in distances:
            (route_edge if item.kind == "route" else edge_check).add(distances["outline"], where, epsilon)
        if "cutout" in distances:
            cutout_check.add(distances["cutout"], where, epsilon)
        point = item.anchor_point()
        if not point_in_polygon(point, outline) or any(point_in_polygon(point, cutout) for cutout in cutouts):
            containment.fail(where)
    # A masked board (grid_registration.taxel_mask) measures records 11 to 15
    # on its crossing region and polygon windows; every other board as before.
    # A diagonal Row bus board is masked whatever it carries (the gate).
    masked = "taxel_mask" in board["grid_registration"] or _row_bus_kind(board) == ROW_BUS_VERSION
    margin_check = (_masked_field_margin if masked else _active_field_margin)(board, outline, cutouts, edges, rules)
    checks.update({check.rule: check for check in (edge_check, cutout_check, route_edge, containment, margin_check)})

    # Coverlay: openings inside the outline, bridge rule, opening-to-trace,
    # and every contact/electrode fully exposed by an opening of its net.
    checks.update((_masked_coverlay_checks if masked else _coverlay_checks)(items, routes, pads, electrodes, openings, outline, cutouts, rules))

    # Stiffener, outline quality, cutouts, neck and concave corners.
    stiffener_check = _Check("stiffener_inside_outline", None)
    for index, stiffener in enumerate(stiffeners):
        polygon = [list(map(float, point)) for point in stiffener["points"]]
        if not _polygon_inside_polygon(polygon, outline, epsilon) or any(_polygons_overlap(polygon, cutout, epsilon) for cutout in cutouts):
            stiffener_check.fail(index)
    # Exact count of crossing/touching non-adjacent edge pairs plus folded-back
    # vertices over the outline and every cutout.
    simple = _Check("outline_simple", 0.0, maximum=True)
    hits = [(_self_intersections(ring), name) for ring, name in ((outline, "outline"), *((cutout, "cutout") for cutout in cutouts))]
    simple.measured = float(sum(count for count, _ in hits))
    simple.violations = sum(count for count, _ in hits)
    simple.where = next((name for count, name in hits if count), "outline")
    # Each routed cutout lies strictly inside the outline: the measured value
    # is the narrowest board bridge between the cutout and the outer edge.
    cutout_inside = _Check("cutouts_inside_outline", None)
    for index, cutout in enumerate(cutouts):
        bridge_width = min(segment_distance(a, b, c, d) for a, b in polygon_edges(cutout) for c, d in polygon_edges(outline))
        if not all(point_in_polygon(point, outline) for point in cutout):
            bridge_width = -bridge_width
        cutout_inside.add(bridge_width, index, epsilon)
        if bridge_width <= epsilon:
            cutout_inside.fail(index)
    corner = _Check("unfilleted_concave_turn_deg", math.degrees(rules.max_concave_turn), maximum=True)
    # A filleted corner is a run of small concave steps along an arc; its
    # effective radius (run length over interior turn) must reach the fillet
    # radius less the sagitta allowance of the polygonal arc.  A tiny fillet
    # passes the per-vertex turn limit but not this one.
    fillet = _Check("concave_fillet_radius", rules.fillet_radius * math.cos(rules.arc_step / 2))
    longest_step = 2 * rules.fillet_radius * math.sin(rules.arc_step / 2) + _ARC_CHORD_SLACK_MM
    # A concave board corner is a right turn of the counter-clockwise outline
    # or a left turn (convex corner) of a counter-clockwise hole.
    for ring, name, board_side in ((outline, "outline", -1.0), *((cutout, "cutout", 1.0) for cutout in cutouts)):
        sign = (1.0 if signed_area(ring) > 0 else -1.0) * board_side
        for vertex, turn in _ring_turns(ring):
            if turn * sign > 0:
                corner.add(math.degrees(turn * sign), [name, vertex], epsilon)
        for radius, vertex in _concave_runs(ring, sign, longest_step, rules.max_concave_turn):
            fillet.add(radius, [name, [round6(vertex[0]), round6(vertex[1])]], epsilon)
    if corner.measured is None:
        corner.measured = 0.0
    neck = _neck_check(board, outline, rules)
    checks.update({check.rule: check for check in (stiffener_check, simple, cutout_inside, corner, fillet, neck)})
    checks.update(_stiffener_zone_checks(board, outline, stiffeners, rules))

    # Connectivity, electrode width, connector tail and board size.
    checks["connectivity"] = _connectivity(routes, pads, electrodes, epsilon)
    width_check = _Check("min_electrode_width", rules.min_electrode_width)
    for electrode in electrodes:
        width_check.add(min(float(electrode["width_mm"]), float(electrode["height_mm"])), electrode["net"], epsilon)
    checks["min_electrode_width"] = width_check
    checks["route_width"] = _route_width(routes, trace_width, rules)
    checks.update(_connector_checks(board, outline, pads, rules))
    min_x, min_y, max_x, max_y = bounds_of(outline)
    short_side, long_side = sorted((max_x - min_x, max_y - min_y))
    limits = profile["limits"]
    short_check = _Check("board_short_side", float(limits["maximum_outline_short_side_mm"]), maximum=True)
    short_check.add(short_side, "outline", epsilon)
    long_check = _Check("board_long_side", float(limits["maximum_outline_long_side_mm"]), maximum=True)
    long_check.add(long_side, "outline", epsilon)
    checks.update({"board_short_side": short_check, "board_long_side": long_check})

    records = {name: check.record() for name, check in checks.items()}
    # The finger-section pairs, which route_route_clearance counts against their own rule.
    finger_record = finger_section.record()
    records["route_route_clearance"]["finger_section"] = {
        key: finger_record[key] for key in ("required_mm", "measured_mm", "violation_count", "where")
    }
    errors = [
        {"code": code, "field": f"boards.{key}.{part}", "message": _message(key, records[name])}
        for name, (code, part) in _ERRORS.items()
        if not records[name]["passed"]
    ]
    rr = records["route_route_clearance"]
    measurements = {
        "drc_version": DRC_VERSION,
        "numeric_epsilon_mm": epsilon,
        "route_segment_count": route_segment_count,
        "minimum_inter_net_center_distance_mm": None if math.isinf(route_pair["center"]) else round6(route_pair["center"]),
        "minimum_inter_net_copper_clearance_mm": rr["measured_mm"],
        "minimum_required_inter_net_copper_clearance_mm": round6(route_rule),
        "closest_inter_net_route_pair": route_pair["pair"],
        "inter_net_copper_overlap_segment_pair_count": route_pair["overlaps"],
        "inter_net_clearance_violation_segment_pair_count": route_pair["violations"],
        "minimum_route_to_outline_copper_clearance_mm": records["route_to_outline"]["measured_mm"],
        "minimum_copper_to_outline_mm": _smallest(records["copper_to_outline"]["measured_mm"], records["route_to_outline"]["measured_mm"]),
        "minimum_required_outline_copper_clearance_mm": round6(rules.copper_to_edge),
        "minimum_copper_to_cutout_mm": records["copper_to_cutout"]["measured_mm"],
        "route_clearance_passed": rr["passed"],
        "outline_containment_passed": all(
            records[name]["passed"] for name in ("copper_to_outline", "route_to_outline", "copper_inside_outline", "outline_simple")
        ),
        "cutout_clearance_passed": records["copper_to_cutout"]["passed"] and records["cutouts_inside_outline"]["passed"],
        "all_checks_passed": all(record["passed"] for record in records.values()),
        "checks": records,
    }
    return {"errors": errors, "warnings": [], "measurements": measurements}


def _active_field_margin(
    board: Mapping[str, Any], outline: list[list[float]], cutouts: list, edges: list, rules: Rules
) -> _Check:
    """Record 11 of an unmasked board: the margin from the outline and cutout edges to the active region."""

    epsilon = rules.epsilon
    # The taxel field keeps the full active-edge margin of board material on
    # every side, including below the Column field where the fan-out starts.
    active = board["grid_registration"]["active_region"]
    active_box = (active["x"], active["y"], active["x"] + active["width"], active["y"] + active["height"])
    margin_check = _Check("active_field_margin", rules.margin)
    margin_check.add(min(segment_box_distance(start, end, active_box) for start, end, _ in edges), "active_region", epsilon)
    active_center = [(active_box[0] + active_box[2]) / 2, (active_box[1] + active_box[3]) / 2]
    if not point_in_polygon(active_center, outline) or any(point_in_polygon(active_center, cutout) for cutout in cutouts):
        margin_check.fail("active_region")
    return margin_check


def _coverlay_checks(
    items: list, routes: list, pads: list, electrodes: list, openings: list, outline: list[list[float]], cutouts: list, rules: Rules
) -> dict[str, _Check]:
    """Records 12 to 15 of an unmasked board, whose openings are rectangles.

    ``coverlay_opening_to_trace`` skips every route of a net the opening
    exposes (the merged field window and the gang window expose them all).
    """

    epsilon = rules.epsilon
    opening_boxes = [rect_bounds(opening) for opening in openings]
    inside = _Check("coverlay_openings_inside_outline", None)
    for opening, box in zip(openings, opening_boxes):
        if not _box_inside_polygon(box, outline, epsilon) or any(_box_touches_polygon(box, cutout, epsilon) for cutout in cutouts):
            inside.fail(opening["kind"])
    bridge = _Check("coverlay_bridge", rules.min_bridge)
    for first_index, second_index in _bbox_pairs(opening_boxes, None, rules.min_bridge + _REPORT_REACH_MM):
        bridge.add(box_gap(opening_boxes[first_index], opening_boxes[second_index]), [openings[first_index]["kind"], openings[second_index]["kind"]], epsilon)
    to_trace = _Check("coverlay_opening_to_trace", rules.opening_to_trace)
    route_items = [item for item in items if item.kind == "route"]
    for opening_index, item_index in _bbox_pairs(opening_boxes, [item.bbox for item in route_items], rules.opening_to_trace + _REPORT_REACH_MM):
        item = route_items[item_index]
        if item.net in openings[opening_index]["nets"]:
            continue
        to_trace.add(segment_box_distance(item.first, item.second, opening_boxes[opening_index]) - item.radius, [openings[opening_index]["kind"], item.net], epsilon)
    exposure = _Check("contact_exposure", 0.0)
    for feature in [*pads, *electrodes]:
        box = rect_bounds(feature)
        margins = [
            min(box[0] - other[0], box[1] - other[1], other[2] - box[2], other[3] - box[3])
            for opening, other in zip(openings, opening_boxes)
            if feature["net"] in opening["nets"]
        ]
        if margins:
            exposure.add(max(margins), feature["net"], epsilon)
        else:
            exposure.fail(feature["net"])  # no opening of its net at all
    return {check.rule: check for check in (inside, bridge, to_trace, exposure)}


# Rule -> (error code, path of the offending layer below ``boards.<row|column>``).
_ROUTES = "layers.top_copper.routes"
_PADS = "layers.top_copper.pads"
_ELECTRODES = "layers.top_copper.electrodes"
_OPENINGS = "layers.top_coverlay_openings"
_STIFFENERS = "layers.bottom_stiffener"
_ERRORS = {
    "route_route_clearance": ("E_ROUTE_CLEARANCE", _ROUTES),
    "pad_trace_clearance": ("E_PAD_TRACE_CLEARANCE", _PADS),
    "pad_pad_clearance": ("E_PAD_CLEARANCE", _PADS),
    "electrode_electrode_clearance": ("E_ELECTRODE_CLEARANCE", _ELECTRODES),
    "electrode_route_clearance": ("E_ELECTRODE_ROUTE_CLEARANCE", _ELECTRODES),
    "electrode_pad_clearance": ("E_ELECTRODE_PAD_CLEARANCE", _ELECTRODES),
    "copper_to_outline": ("E_COPPER_EDGE_CLEARANCE", "outline.points"),
    "route_to_outline": ("E_ROUTE_EDGE_CLEARANCE", _ROUTES),
    "copper_inside_outline": ("E_COPPER_OUTLINE", "outline.points"),
    "copper_to_cutout": ("E_COPPER_CUTOUT_CLEARANCE", "outline.cutouts"),
    "active_field_margin": ("E_ACTIVE_MARGIN", "outline.points"),
    "coverlay_openings_inside_outline": ("E_COVERLAY_OUTLINE", _OPENINGS),
    "coverlay_bridge": ("E_COVERLAY_BRIDGE", _OPENINGS),
    "coverlay_opening_to_trace": ("E_COVERLAY_TRACE_CLEARANCE", _OPENINGS),
    "contact_exposure": ("E_CONTACT_EXPOSURE", _OPENINGS),
    "stiffener_inside_outline": ("E_STIFFENER_OUTLINE", _STIFFENERS),
    "stiffener_zone": ("E_STIFFENER_ZONE", _STIFFENERS),
    "stiffener_end_clearance": ("E_STIFFENER_ZONE", _STIFFENERS),
    "outline_simple": ("E_OUTLINE_SELF_INTERSECTION", "outline.points"),
    "cutouts_inside_outline": ("E_CUTOUT_OUTLINE", "outline.cutouts"),
    "unfilleted_concave_turn_deg": ("E_CONCAVE_CORNER", "outline.points"),
    "concave_fillet_radius": ("E_CONCAVE_CORNER", "outline.points"),
    "neck_width": ("E_NECK_WIDTH", "outline.points"),
    "connectivity": ("E_CONNECTIVITY", _ROUTES),
    "min_electrode_width": ("E_ELECTRODE_WIDTH", _ELECTRODES),
    "route_width": ("E_ROUTE_WIDTH", _ROUTES),
    "tail_width": ("E_CONNECTOR_TAIL", "outline.points"),
    "contact_geometry": ("E_CONNECTOR_TAIL", _PADS),
    "board_short_side": ("E_BOARD_SIZE", "outline.points"),
    "board_long_side": ("E_BOARD_SIZE", "outline.points"),
}


def _smallest(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _message(key: str, record: Mapping[str, Any]) -> str:
    measured = record["measured_mm"]
    required = record["required_mm"]
    text = f"{key} board {record['rule']}: {record['violation_count']} violation(s)"
    if measured is not None:
        text += f", measured {measured:.6f}"
    if required is not None:
        text += f", {'at most' if record['comparison'] == 'max<=' else 'at least'} {required:.6f} required"
    if record["where"] is not None:
        text += f" (at {record['where']})"
    finger = record.get("finger_section")
    if finger and finger["violation_count"]:
        text += (
            f"; {finger['violation_count']} of them between a tail piece and another net's route, measured "
            f"{finger['measured_mm']:.6f}, at least {finger['required_mm']:.6f} required (finger section, at {finger['where']})"
        )
    return text + "."


def _on_boundary(point: Sequence[float], polygon: Sequence[Sequence[float]], epsilon: float) -> bool:
    return any(point_segment_distance(point, a, b) <= epsilon for a, b in polygon_edges(polygon))


def _inside_or_on(point: Sequence[float], polygon: Sequence[Sequence[float]], epsilon: float) -> bool:
    return point_in_polygon(point, polygon) or _on_boundary(point, polygon, epsilon)


def _proper_crossing(a, b, c, d, epsilon: float) -> bool:
    """Segments cross through each other's interiors (touching does not count)."""

    def side(p, q, r) -> float:
        length = math.dist(p, q)
        return 0.0 if length == 0 else ((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])) / length

    s1, s2, s3, s4 = side(a, b, c), side(a, b, d), side(c, d, a), side(c, d, b)
    return ((s1 > epsilon and s2 < -epsilon) or (s1 < -epsilon and s2 > epsilon)) and (
        (s3 > epsilon and s4 < -epsilon) or (s3 < -epsilon and s4 > epsilon)
    )


def _polygon_inside_polygon(inner: Sequence[Sequence[float]], outer: Sequence[Sequence[float]], epsilon: float) -> bool:
    if not all(_inside_or_on(point, outer, epsilon) for point in inner):
        return False
    # Edge midpoints catch an inner edge that bridges a notch of the outer polygon.
    if not all(_inside_or_on([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], outer, epsilon) for a, b in polygon_edges(inner)):
        return False
    if any(point_in_polygon(point, inner) and not _on_boundary(point, inner, epsilon) for point in outer):
        return False
    return not any(_proper_crossing(a, b, c, d, epsilon) for a, b in polygon_edges(inner) for c, d in polygon_edges(outer))


def _box_inside_polygon(box: tuple, polygon: Sequence[Sequence[float]], epsilon: float) -> bool:
    x0, y0, x1, y1 = box
    return _polygon_inside_polygon([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], polygon, epsilon)


def _box_touches_polygon(box: tuple, polygon: Sequence[Sequence[float]], epsilon: float) -> bool:
    if any(segment_box_distance(a, b, box) <= epsilon for a, b in polygon_edges(polygon)):
        return True
    center = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]
    return point_in_polygon(center, polygon) or point_box_distance(polygon[0], box) == 0


def _polygons_overlap(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]], epsilon: float) -> bool:
    if any(segment_distance(a, b, c, d) <= epsilon for a, b in polygon_edges(first) for c, d in polygon_edges(second)):
        return True
    return point_in_polygon(first[0], second) or point_in_polygon(second[0], first)


def _ring(polygon: Sequence[Sequence[float]]) -> list[Sequence[float]]:
    """Closed ring without repeated consecutive vertices (zero-length edges)."""

    points: list[Sequence[float]] = []
    for point in polygon:
        if not points or math.dist(point, points[-1]) > _TINY_MM:
            points.append(point)
    while len(points) > 1 and math.dist(points[0], points[-1]) <= _TINY_MM:
        points.pop()
    return points


def _ring_turns(polygon: Sequence[Sequence[float]]) -> list[tuple[Sequence[float], float]]:
    """``(vertex, signed turn in radians)`` at every vertex of a closed ring."""

    points = _ring(polygon)
    count = len(points)
    if count < 3:
        return []
    return [(points[index], turn_angle(points[index - 1], points[index], points[(index + 1) % count])) for index in range(count)]


def concave_corner_problems(outline: Sequence[Sequence[float]], rules: Rules) -> int:
    """How many vertices and runs of a counter-clockwise board outline fail records ``unfilleted_concave_turn_deg`` and
    ``concave_fillet_radius`` (as :func:`verify_board` measures them; engine.diagonal checks its joins with it)."""

    epsilon = rules.epsilon
    sign = (1.0 if signed_area(outline) > 0 else -1.0) * -1.0
    problems = sum(1 for _, turn in _ring_turns(outline) if turn * sign > rules.max_concave_turn + epsilon)
    longest_step = 2 * rules.fillet_radius * math.sin(rules.arc_step / 2) + _ARC_CHORD_SLACK_MM
    least = rules.fillet_radius * math.cos(rules.arc_step / 2)
    problems += sum(1 for radius, _ in _concave_runs(outline, sign, longest_step, rules.max_concave_turn) if radius < least - epsilon)
    return problems


def _concave_runs(
    polygon: Sequence[Sequence[float]], sign: float, longest_step: float, unfilleted: float
) -> list[tuple[float, Sequence[float]]]:
    """``(effective radius, middle vertex)`` of every concave run turning more than ``unfilleted``.

    A run is a maximal sequence of consecutive board-concave vertices joined
    by edges no longer than one fillet-arc step.  Its effective radius is the
    run length over its interior turn (the end vertices count half), which a
    polygonal arc of radius ``R`` meets at ``R * sinc(step / 2)`` or more; a
    sharp corner (a single vertex) has radius 0.
    """

    points = _ring(polygon)
    count = len(points)
    if count < 3:
        return []
    turns = [sign * turn_angle(points[index - 1], points[index], points[(index + 1) % count]) for index in range(count)]
    concave = [turn > _FLAT_TURN_RAD for turn in turns]
    linked = [math.dist(points[index], points[(index + 1) % count]) <= longest_step for index in range(count)]

    def continues(index: int) -> bool:
        return concave[index] and concave[index - 1] and linked[index - 1]

    start = next((index for index in range(count) if not continues(index)), 0)
    runs: list[list[int]] = []
    for step in range(count):
        index = (start + step) % count
        if concave[index]:
            if step > 0 and continues(index):
                runs[-1].append(index)  # the previous vertex closes runs[-1]
            else:
                runs.append([index])
    answer = []
    for run in runs:
        total = sum(turns[index] for index in run)
        if total <= unfilleted:
            continue
        length = sum(math.dist(points[a], points[b]) for a, b in zip(run, run[1:]))
        interior = total - (turns[run[0]] + turns[run[-1]]) / 2
        radius = length / interior if len(run) > 1 and interior > _TINY_MM else 0.0
        answer.append((radius, points[run[len(run) // 2]]))
    return answer


def ring_is_simple(polygon: Sequence[Sequence[float]]) -> bool:
    """A closed ring of three or more vertices that neither touches nor crosses itself nor folds back."""

    return _self_intersections(polygon) == 0


def _self_intersections(polygon: Sequence[Sequence[float]]) -> int:
    """Non-adjacent edge pairs that touch or cross, plus vertices where the ring folds back."""

    points = _ring(polygon)
    if len(points) < 3:
        return 1
    edges = polygon_edges(points)
    count = len(edges)
    boxes = [bounds_of(edge) for edge in edges]
    hits = sum(1 for _, turn in _ring_turns(points) if abs(turn) >= math.pi - 1e-9)
    for first, second in _bbox_pairs(boxes, None, 0.0):
        if abs(first - second) in (1, count - 1):
            continue
        if segments_intersect(*edges[first], *edges[second]):
            hits += 1
    return hits


def _axis(side: str) -> tuple[int, float]:
    """(axis index along the tail, direction from the body toward the tip)."""

    return {"bottom": (1, -1.0), "top": (1, 1.0), "left": (0, -1.0), "right": (0, 1.0)}[side]


def _interval(polygon: Sequence[Sequence[float]], axis: int, level: float, center: float) -> tuple[float, float] | None:
    """Polygon interval containing ``center`` on the line axis=level, if any."""

    other = 1 - axis
    hits = []
    for a, b in polygon_edges(polygon):
        if (a[axis] > level) != (b[axis] > level):
            fraction = (level - a[axis]) / (b[axis] - a[axis])
            hits.append(a[other] + (b[other] - a[other]) * fraction)
    hits.sort()
    for low, high in zip(hits[::2], hits[1::2]):
        if low - 1e-9 <= center <= high + 1e-9:
            return low, high
    return None


def _cross_section(polygon: Sequence[Sequence[float]], axis: int, level: float, center: float) -> float:
    """Width of the polygon interval containing ``center`` on the line axis=level."""

    interval = _interval(polygon, axis, level, center)
    return 0.0 if interval is None else interval[1] - interval[0]


def _neck_check(board: Mapping[str, Any], outline: list[list[float]], rules: Rules) -> _Check:
    """The outer outline between tail and body is never narrower than the tail.

    This is the D5 shape rule against a waisted tail root, measured on the
    outer outline; the material beside a routed slot is covered by the
    cutout checks (``cutouts_inside_outline``, ``copper_to_cutout``).
    """

    tail = board["tail"]
    check = _Check("neck_width", float(tail["width_mm"]))
    neck = tail["neck_bounds"]
    axis, _ = _axis(tail["side"])
    low = (neck["y"] if axis == 1 else neck["x"])
    span = neck["height"] if axis == 1 else neck["width"]
    center = (neck["x"] + neck["width"] / 2) if axis == 1 else (neck["y"] + neck["height"] / 2)
    levels = {low + span * fraction for fraction in (0.0, 0.5, 1.0)}
    levels.update(point[axis] for point in outline if low <= point[axis] <= low + span)
    for level in sorted(levels):
        # Probe just inside the interval so a vertex level is not double counted.
        for probe in (level - 1e-7, level + 1e-7):
            if low - 1e-9 <= probe <= low + span + 1e-9:
                check.add(_cross_section(outline, axis, probe, center), round6(level), rules.epsilon)
    return check


def _route_width(routes: list, trace_width: float, rules: Rules) -> _Check:
    """Largest deviation of a route piece from its width: the design's bundle
    width for fan-out pieces, the finger width for tail pieces.  A piece of
    neither kind, or narrower than the copper's fabrication minimum, fails."""

    check = _Check("route_width", 0.0, maximum=True)
    widths = {"fanout": trace_width, "tail": rules.finger_width}
    for route in routes:
        width, where = float(route["width_mm"]), [route["net"], route.get("segment")]
        if route.get("segment") not in widths:
            check.fail(where)
            continue
        check.add(abs(width - widths[route["segment"]]), where, rules.epsilon)
        if width < rules.min_trace_width - rules.epsilon:
            check.fail(where)
    return check


def _connectivity(routes: list, pads: list, electrodes: list, epsilon: float) -> _Check:
    """Each channel net is one tail piece from its contact and one fan-out piece
    from the tail piece's end (the junction) to its electrode; NC contacts touch
    nothing and every routed or electrode net has a contact."""

    check = _Check("connectivity", 0.0, maximum=True)
    pad_of = {}
    for pad in pads:
        pad_of.setdefault(pad["net"], []).append(pad)
    electrode_of = {}
    for electrode in electrodes:
        electrode_of.setdefault(electrode["net"], []).append(electrode)
    route_of = {}
    for route in routes:
        route_of.setdefault(route["net"], []).append(route)
    failures = 0
    for net, net_pads in sorted(pad_of.items()):
        net_routes = route_of.get(net, [])
        net_electrodes = electrode_of.get(net, [])
        if net.startswith("NC_"):
            if net_routes or net_electrodes or len(net_pads) != 1:
                failures += 1
                check.fail(net)
            continue
        pieces = {route.get("segment"): route["points"] for route in net_routes}
        if len(net_pads) != 1 or len(net_electrodes) != 1 or len(net_routes) != 2 or set(pieces) != {"tail", "fanout"}:
            failures += 1
            check.fail(net)
            continue
        tail, fanout = pieces["tail"], pieces["fanout"]
        if (
            point_box_distance(tail[0], rect_bounds(net_pads[0])) > epsilon
            or math.dist(tail[-1], fanout[0]) > epsilon
            or point_box_distance(fanout[-1], rect_bounds(net_electrodes[0])) > epsilon
        ):
            failures += 1
            check.fail(net)
    for net in sorted(set(route_of) | set(electrode_of)):
        if net not in pad_of:
            failures += 1
            check.fail(net)
    check.measured = float(failures)
    return check


def _connector_checks(board: Mapping[str, Any], outline: list[list[float]], pads: list, rules: Rules) -> dict[str, _Check]:
    """Tail width at the contacts and contact size/position from the tip and sides."""

    tail = board["tail"]
    axis, toward_tip = _axis(tail["side"])
    other = 1 - axis
    expected = (int(tail["connector_pins"]) + 1) * rules.pitch
    width_check = _Check("tail_width", rules.tail_width_tolerance, maximum=True)
    contact_check = _Check("contact_geometry", 0.0, maximum=True)
    boxes = [rect_bounds(pad) for pad in pads]
    if len(boxes) != int(tail["connector_pins"]) or not boxes:
        width_check.fail("contacts")
        contact_check.fail({"contacts": len(boxes), "connector_pins": tail["connector_pins"]})
        return {"tail_width": width_check, "contact_geometry": contact_check}
    tip = min(point[axis] for point in outline) if toward_tip < 0 else max(point[axis] for point in outline)
    middle = tip - toward_tip * (rules.tip_clearance + rules.contact_length / 2)
    center = sum((box[other] + box[other + 2]) / 2 for box in boxes) / len(boxes)
    interval = _interval(outline, axis, middle, center)
    low, high = interval if interval is not None else (center, center)
    measured = high - low
    width_check.add(abs(measured - expected), {"measured_width_mm": round6(measured), "expected_mm": round6(expected)}, rules.epsilon)
    worst = 0.0
    for pad, box in zip(pads, boxes):
        length = box[axis + 2] - box[axis]
        width = box[other + 2] - box[other]
        start = (box[axis] - tip) if toward_tip < 0 else (tip - box[axis + 2])
        worst = max(worst, abs(length - rules.contact_length), abs(width - rules.contact_width), abs(start - rules.tip_clearance))
    centers = sorted((box[other] + box[other + 2]) / 2 for box in boxes)
    for first, second in zip(centers, centers[1:]):
        worst = max(worst, abs(second - first - rules.pitch))
    # The outer contact centres sit one connector offset from each tail side.
    worst = max(worst, abs(centers[0] - low - rules.side_offset), abs(high - centers[-1] - rules.side_offset))
    contact_check.add(worst, "contacts", rules.epsilon)
    return {"tail_width": width_check, "contact_geometry": contact_check}


def _stiffener_zone_checks(board: Mapping[str, Any], outline: list[list[float]], stiffeners: list, rules: Rules) -> dict[str, _Check]:
    """The connector-zone PI stiffener (``zone: connector``, exactly one) is
    flush with the tip and both tail sides, ``stiffener_length_mm`` long,
    followed by at least ``stiffener_end_clearance_mm`` of straight,
    full-width flexible tail before the outline starts to widen (tail-root
    fillet or fan-out).  Further stiffeners need only lie inside the outline
    (``stiffener_inside_outline``)."""

    tail = board["tail"]
    axis, toward_tip = _axis(tail["side"])
    other = 1 - axis
    zone = _Check("stiffener_zone", 0.0, maximum=True)
    end = _Check("stiffener_end_clearance", rules.stiffener_end_clearance)
    connector = [stiffener for stiffener in stiffeners if stiffener.get("zone") == "connector"]
    if len(connector) != 1:
        zone.fail({"connector_stiffeners": len(connector)})
        return {"stiffener_zone": zone, "stiffener_end_clearance": end}
    # Coordinates along the tail measured from the tip toward the body.
    def along(value: float) -> float:
        return -toward_tip * value

    box = bounds_of(connector[0]["points"])
    bounds = tail["bounds"]
    tail_box = (bounds["x"], bounds["y"], bounds["x"] + bounds["width"], bounds["y"] + bounds["height"])
    tip = min(along(point[axis]) for point in outline)
    start, finish = sorted((along(box[axis]), along(box[axis + 2])))
    deviation = max(
        abs(start - tip),
        abs(finish - start - rules.stiffener_length),
        abs(box[other] - tail_box[other]),
        abs(box[other + 2] - tail_box[other + 2]),
    )
    zone.add(deviation, "stiffener", rules.epsilon)
    straight = min(
        _straight_side_beyond(outline, axis, side, finish, along, rules.epsilon)
        for side in (tail_box[other], tail_box[other + 2])
    )
    end.add(straight, "stiffener", rules.epsilon)
    return {"stiffener_zone": zone, "stiffener_end_clearance": end}


def _straight_side_beyond(outline: Sequence[Sequence[float]], axis: int, side: float, level: float, along, epsilon: float) -> float:
    """How far the tail side line ``side`` continues straight past ``level`` toward the body.

    ``along`` maps a coordinate on ``axis`` to the distance toward the body.
    Outline edges lying on the side line are merged into straight spans; 0 if
    the side no longer runs straight at ``level``.
    """

    other = 1 - axis
    spans = sorted(
        tuple(sorted((along(a[axis]), along(b[axis]))))
        for a, b in polygon_edges(outline)
        if abs(a[other] - side) <= epsilon and abs(b[other] - side) <= epsilon
    )
    merged: list[list[float]] = []
    for low, high in spans:
        if merged and low <= merged[-1][1] + epsilon:
            merged[-1][1] = max(merged[-1][1], high)
        else:
            merged.append([low, high])
    for low, high in merged:
        if low - epsilon <= level <= high + epsilon:
            return high - level
    return 0.0


def verify_registration(row_board: Mapping[str, Any], column_board: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    """Cross-board check: orthogonal electrodes on identical taxel grids.

    Each failing sub-check gets its own error: parallel electrodes point at
    the tail sides (the only design input that rotates a board); a taxel
    field or grid mismatch names the board data and its measured deviation.
    """

    rules = Rules(profile)
    epsilon = rules.epsilon
    row_axis = _long_axis(row_board)
    column_axis = _long_axis(column_board)
    row_active = row_board["grid_registration"]["active_region"]
    column_active = column_board["grid_registration"]["active_region"]
    size_deviation = max(
        abs(row_active["width"] - column_active["width"]), abs(row_active["height"] - column_active["height"])
    )
    grid = row_board["grid_registration"]
    row_deviation = _grid_deviation(row_board, row_axis, int(grid["rows"]), float(grid["pitch_y_mm"]), rules)
    column_deviation = _grid_deviation(column_board, column_axis, int(grid["columns"]), float(grid["pitch_x_mm"]), rules)
    # A masked pair (grid_registration.taxel_mask) is registered on its masked taxel grid and crossings
    # instead: the deviations above assume electrodes that span the whole field.
    masked = "taxel_mask" in row_board["grid_registration"] or "taxel_mask" in column_board["grid_registration"]
    if masked:
        row_deviation, column_deviation, masked_keys, first_wrong = _masked_registration(row_board, column_board, row_axis, column_axis, rules)
    record = {
        "rule": "registration",
        "required_mm": epsilon,
        "row_electrode_axis": "x" if row_axis == 0 else "y",
        "column_electrode_axis": "x" if column_axis == 0 else "y",
        "orthogonal": row_axis != column_axis,
        "active_region_size_deviation_mm": round6(size_deviation),
        "identical_active_region": size_deviation <= epsilon,
        "row_grid_deviation_mm": None if row_deviation is None else round6(row_deviation),
        "row_grid_matches": row_deviation is not None and row_deviation <= epsilon,
        "column_grid_deviation_mm": None if column_deviation is None else round6(column_deviation),
        "column_grid_matches": column_deviation is not None and column_deviation <= epsilon,
    }
    if masked:
        record.update(masked_keys)
    # A diagonal Row bus pair (construction.row_bus) adds its stack keys, on orthogonal boards.
    diagonal = record["orthogonal"] and any(_row_bus_kind(board) == ROW_BUS_VERSION for board in (row_board, column_board))
    stack_errors: list[tuple[str, str]] = []
    warnings: list[dict[str, str]] = []
    if diagonal:
        stack_keys, stack_errors, stack_warnings = _row_bus_registration(row_board, column_board, record, rules)
        record.update(stack_keys)
        warnings = [{"code": "W_STACK_TRACE_WINDOW", "field": field, "message": message} for field, message in stack_warnings]
    record["passed"] = all(record[key] for key in ("orthogonal", "identical_active_region", "row_grid_matches", "column_grid_matches"))
    if masked:
        record["passed"] = record["passed"] and all(record[key] for key in _MASKED_REGISTRATION_CHECKS)
    if diagonal:
        record["passed"] = record["passed"] and not stack_errors
    errors = []

    def error(field: str, message: str) -> None:
        errors.append({"code": "E_REGISTRATION", "field": field, "message": message})

    if not record["orthogonal"]:
        # Grids cannot be compared on parallel boards.
        error(
            "tail.column_side",
            f"Row and Column electrodes both run along {record['row_electrode_axis']} in the shared assembly frame; "
            "tail.row_side and tail.column_side must be equal or opposite so the electrodes cross.",
        )
        return {"errors": errors, "warnings": warnings, "measurements": record}
    if not record["identical_active_region"]:
        error(
            "boards.column.grid_registration.active_region",
            f"The Row and Column taxel fields differ by {size_deviation:.6f} mm (at most {epsilon:g} mm allowed).",
        )
    for key, deviation, count, pitch in (
        ("row", row_deviation, grid["rows"], grid["pitch_y_mm"]),
        ("column", column_deviation, grid["columns"], grid["pitch_x_mm"]),
    ):
        if not record[f"{key}_grid_matches"]:
            measured = "a different electrode count" if deviation is None else f"{deviation:.6f} mm"
            error(
                f"boards.{key}.layers.top_copper.electrodes",
                f"The {key} electrodes deviate by {measured} from the {count} x {pitch:g} mm taxel grid with "
                f"{rules.overhang:g} mm overhang (at most {epsilon:g} mm allowed).",
            )
    if masked:
        for field, message in _masked_registration_errors(record, first_wrong, rules):
            error(field, message)
    for field, message in stack_errors:
        error(field, message)
    return {"errors": errors, "warnings": warnings, "measurements": record}


# The registration keys of a masked pair that must hold (besides the unmasked ones).
_MASKED_REGISTRATION_CHECKS = ("taxel_mask_identical", "crossing_set_matches_mask", "inactive_crossings_separated")


def _masked_registration_errors(record: Mapping[str, Any], first_wrong: list[str] | None, rules: Rules) -> list[tuple[str, str]]:
    """``(field, message)`` of each failing masked registration check."""

    answer = []
    if not record["taxel_mask_identical"]:
        answer.append((
            "boards.column.grid_registration.taxel_mask",
            "The Row and Column boards carry different taxel masks; both must be the design's matrix.mask.",
        ))
    if not record["crossing_set_matches_mask"]:
        answer.append((
            "boards.row.grid_registration.taxel_mask",
            f"The stacked electrodes cross at {record['wrong_crossing_count']} position(s) where the taxel mask "
            f"differs (first {first_wrong[0]} x {first_wrong[1]}): a crossing the mask does not have, or a taxel "
            "it has without one.",
        ))
    if not record["inactive_crossings_separated"]:
        answer.append((
            "boards.row.grid_registration.taxel_mask",
            f"An inactive crossing's electrodes are {record['inactive_crossing_separation_mm']:.6f} mm from overlapping "
            f"in the stack (more than {rules.epsilon:g} mm required).",
        ))
    return answer


def _long_axis(board: Mapping[str, Any]) -> int:
    """Axis (0 = x, 1 = y) along which the electrodes run.

    Electrodes overhang the taxel field only along their own length, so the
    axis is where the electrode field outgrows the active region; the aspect
    ratio is only a fallback (a 1 x 1 matrix can have wide, short strips).
    """

    boxes = [rect_bounds(electrode) for electrode in board["layers"]["top_copper"]["electrodes"]]
    active = board["grid_registration"]["active_region"]
    grow_x = (max(box[2] for box in boxes) - min(box[0] for box in boxes)) - active["width"]
    grow_y = (max(box[3] for box in boxes) - min(box[1] for box in boxes)) - active["height"]
    if abs(grow_x - grow_y) > 1e-9:
        return 0 if grow_x > grow_y else 1
    return 0 if boxes[0][2] - boxes[0][0] >= boxes[0][3] - boxes[0][1] else 1


def _grid_deviation(board: Mapping[str, Any], long_axis: int, count: int, pitch: float, rules: Rules) -> float | None:
    """Largest deviation from the taxel grid (``None`` for a wrong electrode count).

    Electrode ``i`` starts ``i * pitch`` into the taxel field across its
    length, all electrodes fill the field, and each overhangs it at both
    ends.  The layout places the field and pitch on the 1e-6 mm grid, so a
    generated board deviates only by floating-point noise.
    """

    across = 1 - long_axis
    active = board["grid_registration"]["active_region"]
    origin = (active["x"], active["y"])
    size = (active["width"], active["height"])
    boxes = sorted(
        (rect_bounds(electrode) for electrode in board["layers"]["top_copper"]["electrodes"]),
        key=lambda box: box[across],
    )
    if len(boxes) != count:
        return None
    width = size[across] - (count - 1) * pitch
    worst = 0.0
    for index, box in enumerate(boxes):
        deviations = (
            box[across] - origin[across] - index * pitch,
            box[across + 2] - box[across] - width,
            origin[long_axis] - box[long_axis] - rules.overhang,
            box[long_axis + 2] - box[long_axis] - size[long_axis] - 2 * rules.overhang,
        )
        worst = max(worst, *(abs(deviation) for deviation in deviations))
    return worst


# --------------------------------------------------------------------------
# Masked boards (grid_registration.taxel_mask): records 11 to 15 and the
# registration of a masked pair (claude/specs/masked-field/PLAN.md, phase P2).
# --------------------------------------------------------------------------
#
# A masked board keeps the 30 records and their names.  Records 11 to 15
# measure the crossing region P (grid_registration.active_outline) instead
# of the bounding active region, take the polygon field window as a ring,
# and record 14 is strict: a route is exempt only near its own contact or
# electrode, not wherever an opening lists its net.  Every polygon test is
# a sweep over edge boxes (_bbox_pairs), never all pairs.


class _MaskedCheck(_Check):
    """A record of a masked board: the record's fields plus the masked semantics' own keys (``extra``)."""

    def __init__(self, rule: str, required: float | None, *, extra: Mapping[str, Any] | None = None) -> None:
        super().__init__(rule, required)
        self.extra: dict[str, Any] = dict(extra or {})

    def record(self) -> dict[str, Any]:
        return {**super().record(), **self.extra}


def _edge_boxes(edges: Sequence[tuple]) -> list[tuple]:
    return [bounds_of([edge[0], edge[1]]) for edge in edges]


def _opening_ring(opening: Mapping[str, Any]) -> list[list[float]]:
    """The boundary of a coverlay opening: a polygon window's points or a rectangle's corners (counter-clockwise)."""

    if opening.get("shape") == "polygon":
        return [list(map(float, point)) for point in opening["points"]]
    return rect_corners(opening)


def _masked_field_margin(
    board: Mapping[str, Any], outline: list[list[float]], cutouts: list, edges: list, rules: Rules
) -> _Check:
    """Record 11 of a masked board: the active-edge margin around the crossing region P.

    P (``grid_registration.active_outline``) must keep the margin from every
    outline and cutout edge (swept edge pairs, measured up to the report
    reach), lie inside the outline and outside the cutouts, and equal the
    region the board's own electrodes give (each without its overhang, plus
    the fillers between consecutive electrodes; ``where`` is
    ``active_outline_mismatch`` otherwise).  ``region`` is ``taxel_mask``.
    """

    epsilon = rules.epsilon
    record = _MaskedCheck("active_field_margin", rules.margin, extra={"region": "taxel_mask"})
    if "active_outline" not in board["grid_registration"]:
        record.fail("active_outline")  # a diagonal Row bus board without its masked records
        return record
    region = [list(map(float, point)) for point in board["grid_registration"]["active_outline"]]
    region_edges = polygon_edges(region)
    reach = rules.margin + _REPORT_REACH_MM + epsilon
    nearest = None
    for region_index, edge_index in _bbox_pairs(_edge_boxes(region_edges), _edge_boxes(edges), reach):
        start, end, _ = edges[edge_index]
        distance = segment_distance(*region_edges[region_index], start, end)
        if nearest is None or distance < nearest:
            nearest = distance
    if nearest is not None:
        record.add(nearest, "active_outline", epsilon)
    if not point_in_polygon(region[0], outline) or any(point_in_polygon(region[0], cutout) for cutout in cutouts):
        record.fail("active_outline")
    if not _same_ring(region, _electrode_region(board, rules), epsilon):
        record.violations += 1
        record.where = "active_outline_mismatch"
    return record


def _electrode_region(board: Mapping[str, Any], rules: Rules) -> list[list[float]] | None:
    """P from the board's electrodes: each without its overhang, plus the fillers between consecutive ones.

    ``None`` when the electrodes give no orthogonally convex region (a gap
    between them, or two that share no extent).
    """

    boxes = [rect_bounds(electrode) for electrode in board["layers"]["top_copper"]["electrodes"]]
    if not boxes:
        return None
    along = _long_axis(board)
    stacked = 1 - along
    strips = []
    for box in boxes:
        strip = list(box)
        strip[along] += rules.overhang
        strip[along + 2] -= rules.overhang
        strips.append(tuple(round6(value) for value in strip))
    strips.sort(key=lambda strip: (strip[stacked], strip[along]))
    try:
        return band_ring(strips, stacked)
    except ValueError:
        return None


def _same_ring(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]] | None, epsilon: float) -> bool:
    """The two closed rings have the same vertices in the same cyclic order (from any start)."""

    if second is None or len(first) != len(second) or not first:
        return False
    count = len(first)
    close = lambda a, b: abs(a[0] - b[0]) <= epsilon and abs(a[1] - b[1]) <= epsilon
    start = next((index for index, point in enumerate(second) if close(point, first[0])), None)
    return start is not None and all(close(first[index], second[(start + index) % count]) for index in range(count))


def _masked_coverlay_checks(
    items: list, routes: list, pads: list, electrodes: list, openings: list, outline: list[list[float]], cutouts: list, rules: Rules
) -> dict[str, _Check]:
    """Records 12 to 15 of a masked board, whose merged field window may be a polygon.

    - 12 ``coverlay_openings_inside_outline``: a polygon window is simple,
      rectilinear and orthogonally convex; every opening lies inside the
      outline (swept edge pairs) and clear of the cutouts.
    - 13 ``coverlay_bridge``: the gap between two openings, a polygon's by
      its edges (swept), with 0 for openings that overlap or nest.
    - 14 ``coverlay_opening_to_trace`` (``semantics: strict``): every route
      piece outside its own contacts and electrodes (those of its net that an
      end of the piece touches) grown by expansion + rule + half its width
      keeps the rule from every opening's edges, less the edges lying on its
      own features' windows, and lies outside every opening.
    - 15 ``contact_exposure``: the margin of each contact and electrode
      inside an opening of its net, to a polygon's edges; ``electrodes``
      holds the electrodes' own minimum (the coverlay expansion by
      construction).
    """

    epsilon = rules.epsilon
    rings = [_opening_ring(opening) for opening in openings]
    ring_boxes = [bounds_of(ring) for ring in rings]
    polygon = [opening.get("shape") == "polygon" for opening in openings]

    inside = _MaskedCheck("coverlay_openings_inside_outline", None)
    for opening, ring, is_polygon in zip(openings, rings, polygon):
        sound = not is_polygon or (ring_is_simple(ring) and is_rectilinear(ring, epsilon) and is_orthogonally_convex(ring))
        if not sound or not _swept_inside(ring, outline, epsilon) or any(_rings_touch(ring, cutout, epsilon) for cutout in cutouts):
            inside.fail(opening["kind"])

    bridge = _MaskedCheck("coverlay_bridge", rules.min_bridge)
    reach = rules.min_bridge + _REPORT_REACH_MM
    for first_index, second_index in _bbox_pairs(ring_boxes, None, reach):
        if polygon[first_index] or polygon[second_index]:
            gap = _ring_gap(rings[first_index], rings[second_index], reach)
        else:
            gap = box_gap(ring_boxes[first_index], ring_boxes[second_index])
        if gap is not None:
            bridge.add(gap, [openings[first_index]["kind"], openings[second_index]["kind"]], epsilon)

    to_trace = _strict_opening_to_trace(routes, pads, electrodes, openings, rings, ring_boxes, rules)
    exposure = _masked_exposure(pads, electrodes, openings, rings, polygon, rules)
    return {check.rule: check for check in (inside, bridge, to_trace, exposure)}


def _swept_inside(inner: Sequence[Sequence[float]], outer: Sequence[Sequence[float]], epsilon: float) -> bool:
    """``inner`` lies inside ``outer`` (both simple rings; touching allowed), from swept edge pairs.

    No inner edge may cross an outer edge.  When the boundaries stay apart,
    one inner vertex inside ``outer`` decides; where they touch, every inner
    vertex and edge midpoint must be inside or on ``outer`` and no outer
    vertex strictly inside ``inner``, as for the rectangles of an unmasked
    board.
    """

    inner_edges, outer_edges = polygon_edges(inner), polygon_edges(outer)
    near: list[list[int]] = [[] for _ in inner_edges]
    for inner_index, outer_index in _bbox_pairs(_edge_boxes(inner_edges), _edge_boxes(outer_edges), epsilon):
        a, b = inner_edges[inner_index]
        c, d = outer_edges[outer_index]
        if _proper_crossing(a, b, c, d, epsilon):
            return False
        if segment_distance(a, b, c, d) <= epsilon:
            near[inner_index].append(outer_index)
    if not any(near):
        return point_in_polygon(inner[0], outer)

    def inside_or_on(point: Sequence[float], candidates: Sequence[int]) -> bool:
        if any(point_segment_distance(point, *outer_edges[index]) <= epsilon for index in candidates):
            return True
        return point_in_polygon(point, outer)

    count = len(inner)
    for index in range(count):
        a, b = inner_edges[index]
        if not inside_or_on(a, near[index] + near[index - 1]):
            return False
        if not inside_or_on([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], near[index]):
            return False
    low_x, low_y, high_x, high_y = bounds_of(inner)
    return not any(
        low_x < point[0] < high_x and low_y < point[1] < high_y and point_in_polygon(point, inner) and not _on_boundary(point, inner, epsilon)
        for point in outer
    )


def _rings_touch(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]], epsilon: float) -> bool:
    """The two rings' regions touch or overlap (swept edge pairs, then one vertex of each)."""

    first_edges, second_edges = polygon_edges(first), polygon_edges(second)
    for first_index, second_index in _bbox_pairs(_edge_boxes(first_edges), _edge_boxes(second_edges), epsilon):
        if segment_distance(*first_edges[first_index], *second_edges[second_index]) <= epsilon:
            return True
    return point_in_polygon(first[0], second) or point_in_polygon(second[0], first)


def _ring_gap(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]], reach: float) -> float | None:
    """The gap between two openings' regions: 0 when they overlap or nest, else the nearest edges' distance.

    ``None`` when no edges are within ``reach`` (swept edge pairs).
    """

    if point_in_polygon(first[0], second) or point_in_polygon(second[0], first):
        return 0.0
    first_edges, second_edges = polygon_edges(first), polygon_edges(second)
    nearest = None
    for first_index, second_index in _bbox_pairs(_edge_boxes(first_edges), _edge_boxes(second_edges), reach):
        distance = segment_distance(*first_edges[first_index], *second_edges[second_index])
        if nearest is None or distance < nearest:
            nearest = distance
    return nearest


def _strict_opening_to_trace(
    routes: list, pads: list, electrodes: list, openings: list, rings: list, ring_boxes: list, rules: Rules
) -> _Check:
    """Record 14 of a masked board, strict: no route is exempt because an opening lists its net.

    A route piece's own features are the contacts and electrodes of its net
    that one of its ends touches.  The piece is clipped outside each own
    feature grown by the coverlay expansion, the rule and half its width;
    from the openings' edges, the parts lying on an own feature's window
    (the feature grown by the expansion) are dropped, which loses nothing
    since every remaining part of the piece is farther than the rule from
    that window.  What remains keeps the rule from the remaining edges and
    lies outside every opening.
    """

    epsilon = rules.epsilon
    record = _MaskedCheck("coverlay_opening_to_trace", rules.opening_to_trace, extra={"semantics": "strict"})
    features = [(item["net"], rect_bounds(item)) for item in [*pads, *electrodes]]
    parts = []  # (net, radius, start, end, own windows)
    for route in routes:
        radius = float(route["width_mm"]) / 2
        points = [list(map(float, point)) for point in route["points"]]
        ends = (points[0], points[-1])
        own = [box for net, box in features if net == route["net"] and any(point_box_distance(end, box) <= epsilon for end in ends)]
        grow = rules.expansion + rules.opening_to_trace + radius
        zones = [(box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow) for box in own]
        windows = [(box[0] - rules.expansion, box[1] - rules.expansion, box[2] + rules.expansion, box[3] + rules.expansion) for box in own]
        segments = [(a, b) for a, b in zip(points, points[1:]) if math.dist(a, b) > 0] or [(points[0], points[0])]
        for start, end in segments:
            pieces = [(start, end)]
            for zone in zones:
                pieces = [piece for a, b in pieces for piece in clip_segment_outside_box(a, b, zone)]
            parts.extend((route["net"], radius, a, b, windows) for a, b in pieces)
    ring_edges = [(index, a, b) for index, ring in enumerate(rings) for a, b in polygon_edges(ring)]
    part_boxes = [
        (min(a[0], b[0]) - radius, min(a[1], b[1]) - radius, max(a[0], b[0]) + radius, max(a[1], b[1]) + radius)
        for _, radius, a, b, _ in parts
    ]
    reach = rules.opening_to_trace + _REPORT_REACH_MM + epsilon
    for part_index, edge_index in _bbox_pairs(part_boxes, [bounds_of([a, b]) for _, a, b in ring_edges], reach):
        net, radius, start, end, windows = parts[part_index]
        opening_index, a, b = ring_edges[edge_index]
        remaining = [(a, b)]
        for window in windows:
            remaining = [piece for c, d in remaining for piece in segment_parts_off_box_boundary(c, d, window, epsilon)]
        for c, d in remaining:
            record.add(segment_distance(start, end, c, d) - radius, [openings[opening_index]["kind"], net], epsilon)
    # A part that keeps the rule from every remaining edge is wholly inside or outside each opening.
    middles = [[(a[0] + b[0]) / 2, (a[1] + b[1]) / 2] for _, _, a, b, _ in parts]
    for part_index, opening_index in _bbox_pairs([(x, y, x, y) for x, y in middles], ring_boxes, 0.0):
        if point_in_polygon(middles[part_index], rings[opening_index]):
            record.fail([openings[opening_index]["kind"], parts[part_index][0], "inside"])
    return record


def _masked_exposure(pads: list, electrodes: list, openings: list, rings: list, polygon: list, rules: Rules) -> _Check:
    """Record 15 of a masked board: each contact and electrode inside an opening of its net, by its margin.

    A rectangle's margin is the narrowest of its four sides, as on an
    unmasked board; a polygon's is the distance from the feature to its
    edges (swept), negative when the feature is not inside it.
    """

    epsilon = rules.epsilon
    features = [*pads, *electrodes]
    boxes = [rect_bounds(feature) for feature in features]
    nearest: dict[int, dict[int, float]] = {}
    for opening_index, ring in enumerate(rings):
        if not polygon[opening_index]:
            continue
        distances: dict[int, float] = {}
        ring_edges = polygon_edges(ring)
        for feature_index, edge_index in _bbox_pairs(boxes, _edge_boxes(ring_edges), _REPORT_REACH_MM):
            distance = segment_box_distance(*ring_edges[edge_index], boxes[feature_index])
            if distance < distances.get(feature_index, math.inf):
                distances[feature_index] = distance
        nearest[opening_index] = distances
    record = _MaskedCheck("contact_exposure", 0.0)
    electrode_record = _Check("electrodes", 0.0)
    for feature_index, (feature, box) in enumerate(zip(features, boxes)):
        margins = []
        for opening_index, (opening, ring) in enumerate(zip(openings, rings)):
            if feature["net"] not in opening["nets"]:
                continue
            if polygon[opening_index]:
                margins.append(_box_ring_margin(box, ring, nearest[opening_index].get(feature_index), epsilon))
            else:
                other = bounds_of(ring)
                margins.append(min(box[0] - other[0], box[1] - other[1], other[2] - box[2], other[3] - box[3]))
        if not margins:
            record.fail(feature["net"])  # no opening of its net
            continue
        record.add(max(margins), feature["net"], epsilon)
        if feature_index >= len(pads):
            electrode_record.add(max(margins), feature["net"], epsilon)
    electrodes_part = electrode_record.record()
    record.extra["electrodes"] = {"measured_mm": electrodes_part["measured_mm"], "where": electrodes_part["where"]}
    return record


def _box_ring_margin(box: tuple, ring: Sequence[Sequence[float]], distance: float | None, epsilon: float) -> float:
    """The margin of a box inside a ring: its distance to the ring's edges, negative when it is not inside.

    ``distance`` is the box's nearest edge distance when the sweep found an
    edge in reach (else every edge is measured).  A box apart from the
    boundary is inside or outside as a whole (its centre decides); one that
    touches it is inside when its corners are inside or on the ring and no
    ring vertex lies within it.
    """

    edges = polygon_edges(ring)
    if distance is None:
        distance = min(segment_box_distance(a, b, box) for a, b in edges)
    if distance > epsilon:
        center = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]
        return distance if point_in_polygon(center, ring) else -distance
    outside = [
        min(point_segment_distance(corner, a, b) for a, b in edges)
        for corner in bounds_corners(box)
        if not _inside_or_on(corner, ring, epsilon)
    ]
    if outside:
        return -max(outside)
    within = [
        min(point[0] - box[0], point[1] - box[1], box[2] - point[0], box[3] - point[1])
        for point in ring
        if box[0] + epsilon < point[0] < box[2] - epsilon and box[1] + epsilon < point[1] < box[3] - epsilon
    ]
    return -max(within) if within else distance


def stack_frame(board: Mapping[str, Any], role_mapping: Mapping[str, str] | None = None):
    """The stack frame of a board turned to its tail side: a function from board points to stack points.

    The active region's centre goes to the origin, and the physical top
    board, which lies copper side down on the film, is turned over about its
    tail axis (``x -> -x`` for bottom and top tails, ``y -> -y`` for left and
    right ones), so both boards of a pair land in one frame, seen from
    outside the stack (the bottom board's copper side).  The top board is
    ``role_mapping["top"]`` when given, else the board whose
    ``physical_side`` is ``top``.  For bottom tails this is CAD mode's
    outside view (``surface/place.py``: ``x' = width - x`` on the top board).
    """

    region = board["grid_registration"]["active_region"]
    center_x = float(region["x"]) + float(region["width"]) / 2
    center_y = float(region["y"]) + float(region["height"]) / 2
    top = role_mapping["top"] == board["role"] if role_mapping is not None else board.get("physical_side") == "top"
    across_tail = board["tail"]["side"] in ("bottom", "top")
    flip_x, flip_y = top and across_tail, top and not across_tail

    def convert(point: Sequence[float]) -> list[float]:
        x, y = float(point[0]) - center_x, float(point[1]) - center_y
        return [-x if flip_x else x, -y if flip_y else y]

    return convert


def _stacked_electrodes(board: Mapping[str, Any]) -> dict[str, tuple]:
    """``{net: box}`` of the board's electrodes in the stack frame."""

    convert = stack_frame(board)
    return {
        electrode["net"]: bounds_of([convert(corner) for corner in rect_corners(electrode)])
        for electrode in board["layers"]["top_copper"]["electrodes"]
    }


# Two stacked trace segments run along each other when their directions differ by less than this (in radians):
# far below any bend of the fan-outs, far above what the 1e-6 mm grid does to the direction of a diagonal.
_PARALLEL_RAD = 1e-5


def _stacked_traces(board: Mapping[str, Any]) -> list[tuple[str, list[float], list[float], float]]:
    """``(net, start, end, half width)`` of each route segment of the board in the stack frame."""

    convert = stack_frame(board)
    answer = []
    for route in board["layers"]["top_copper"]["routes"]:
        points = [convert(point) for point in route["points"]]
        radius = float(route["width_mm"]) / 2
        answer.extend((route["net"], a, b, radius) for a, b in zip(points, points[1:]) if math.dist(a, b) > 0)
    return answer


def _trace_overlap(row_board: Mapping[str, Any], column_board: Mapping[str, Any], epsilon: float) -> dict[str, Any]:
    """Where a Row trace runs on a Column trace in the stack: reported, never a failure.

    Both traces lie under their coverlay with the film between, so they never
    touch, but a ROW and a COL net that run on each other couple
    capacitively along the run (a question for the film vendor).  A segment
    of each board runs on the other where the two are parallel (within
    ``_PARALLEL_RAD``) and their copper overlaps across them by a positive
    width; crossings at an angle (a Row stub over a raised Column stub) are
    not counted.  The keys: ``trace_overlap_mm``, the longest run of one Row
    net on one Column net (their runs summed; 0 when there is none),
    ``trace_overlap_nets`` (that pair, the first in net order on a tie, or
    ``None``), ``trace_overlap_pairs`` (the net pairs with a run) and
    ``trace_overlap_area_mm2`` (the copper both cover, every run).
    """

    row_traces, column_traces = _stacked_traces(row_board), _stacked_traces(column_board)

    def boxes(traces: list) -> list[tuple]:
        return [
            (min(a[0], b[0]) - radius, min(a[1], b[1]) - radius, max(a[0], b[0]) + radius, max(a[1], b[1]) + radius)
            for _, a, b, radius in traces
        ]

    runs: dict[tuple[str, str], list[float]] = {}
    areas = []
    for row_index, column_index in _bbox_pairs(boxes(row_traces), boxes(column_traces), 0.0):
        row_net, a, b, row_radius = row_traces[row_index]
        column_net, c, d, column_radius = column_traces[column_index]
        length = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        vx, vy = d[0] - c[0], d[1] - c[1]
        if abs(ux * vy - uy * vx) > _PARALLEL_RAD * math.hypot(vx, vy):
            continue
        # The Column segment's ends along the Row segment, and its middle's offset across it.
        along = sorted(((c[0] - a[0]) * ux + (c[1] - a[1]) * uy, (d[0] - a[0]) * ux + (d[1] - a[1]) * uy))
        offset = abs(((c[0] + d[0]) / 2 - a[0]) * uy - ((c[1] + d[1]) / 2 - a[1]) * ux)
        width = min(row_radius, offset + column_radius) - max(-row_radius, offset - column_radius)
        run = min(length, along[1]) - max(0.0, along[0])
        if width > epsilon and run > epsilon:
            runs.setdefault((row_net, column_net), []).append(run)
            areas.append(run * width)
    totals = sorted(((math.fsum(values), pair) for pair, values in runs.items()), key=lambda item: (-item[0], item[1]))
    longest, nets = totals[0] if totals else (0.0, None)
    return {
        "trace_overlap_mm": round6(longest),
        "trace_overlap_nets": None if nets is None else list(nets),
        "trace_overlap_pairs": len(totals),
        "trace_overlap_area_mm2": round6(math.fsum(areas)),
    }


def _masked_registration(
    row_board: Mapping[str, Any], column_board: Mapping[str, Any], row_axis: int, column_axis: int, rules: Rules
) -> tuple[float | None, float | None, dict[str, Any], list[str] | None]:
    """The registration of a masked pair, in the stack frame (:func:`stack_frame`).

    Returns ``(row deviation, column deviation, record keys, first wrong
    crossing)``.  The deviations generalize :func:`_grid_deviation`: across
    its length electrode ``i`` starts ``i * pitch`` into the taxel field and
    has the cell width, as there; along it, both ends overhang the outer
    taxels of its span (the other board's electrodes of the nets in its
    span, on their grid slots) by the overhang.  ``None`` for a wrong
    electrode count or a net missing.  The keys: ``taxel_mask_identical``;
    ``wrong_crossing_count`` (the R x C electrode pairs whose overlap, of
    positive width and height, differs from the mask) and
    ``crossing_set_matches_mask``; ``inactive_crossing_separation_mm`` (the
    smallest misregistration that makes an inactive pair overlap: over the
    inactive pairs the least of the larger of the x and y gaps) and
    ``inactive_crossings_separated`` (more than the epsilon, or no inactive
    pair); and the stacked traces' overlap (:func:`_trace_overlap`), which
    is reported only.
    """

    epsilon = rules.epsilon
    masks = [board["grid_registration"].get("taxel_mask") for board in (row_board, column_board)]
    mask = masks[0] if masks[0] is not None else masks[1]
    spans = [(int(first), int(last)) for first, last in mask["row_spans"]]
    rows, columns = len(spans), int(mask["columns"])
    row_boxes, column_boxes = _stacked_electrodes(row_board), _stacked_electrodes(column_board)
    row_nets = [f"ROW_{row:02d}" for row in range(1, rows + 1)]
    column_nets = [f"COL_{column:02d}" for column in range(1, columns + 1)]
    members = {
        "row": [column_nets[first - 1:last] for first, last in spans],
        "column": [[row_nets[row] for row, (first, last) in enumerate(spans) if first <= column <= last] for column in range(1, columns + 1)],
    }
    grid = row_board["grid_registration"]
    deviations = {}
    for key, board, axis, own_nets, boxes, partner_boxes, partners, pitch_across, pitch_along in (
        ("row", row_board, row_axis, row_nets, row_boxes, column_boxes, columns, float(grid["pitch_y_mm"]), float(grid["pitch_x_mm"])),
        ("column", column_board, column_axis, column_nets, column_boxes, row_boxes, rows, float(grid["pitch_x_mm"]), float(grid["pitch_y_mm"])),
    ):
        deviations[key] = _masked_grid_deviation(
            board, axis, own_nets, boxes, members[key], partner_boxes, (partners, pitch_across, pitch_along), rules
        )
    wrong, first_wrong, separation = 0, None, None
    for row, (first, last) in enumerate(spans):
        a = row_boxes.get(row_nets[row])
        for column in range(1, columns + 1):
            b = column_boxes.get(column_nets[column - 1])
            active = first <= column <= last
            if a is None or b is None:
                overlap_x = overlap_y = -math.inf
            else:
                overlap_x = min(a[2], b[2]) - max(a[0], b[0])
                overlap_y = min(a[3], b[3]) - max(a[1], b[1])
            if (overlap_x > epsilon and overlap_y > epsilon) != active:
                wrong += 1
                if first_wrong is None:
                    first_wrong = [row_nets[row], column_nets[column - 1]]
            if not active and a is not None and b is not None:
                distance = max(-overlap_x, -overlap_y)
                if separation is None or distance < separation:
                    separation = distance
    keys = {
        "taxel_mask_identical": masks[0] is not None and masks[0] == masks[1],
        "crossing_set_matches_mask": wrong == 0,
        "wrong_crossing_count": wrong,
        "inactive_crossing_separation_mm": None if separation is None else round6(separation),
        "inactive_crossings_separated": separation is None or separation > epsilon,
        **_trace_overlap(row_board, column_board, epsilon),
    }
    return deviations["row"], deviations["column"], keys, first_wrong


def _masked_grid_deviation(
    board: Mapping[str, Any],
    long_axis: int,
    nets: list[str],
    boxes: Mapping[str, tuple],
    members: list[list[str]],
    partner_boxes: Mapping[str, tuple],
    grid: tuple[int, float, float],
    rules: Rules,
) -> float | None:
    """Largest deviation of a masked board's electrodes from the masked taxel grid, in the stack frame.

    ``nets`` are the board's nets in index order, ``members`` the other
    board's nets in each one's span, ``grid`` the other board's electrode
    count and the pitches across and along this board's electrodes.
    """

    partners_count, pitch_across, pitch_along = grid

    across = 1 - long_axis
    convert = stack_frame(board)
    region = board["grid_registration"]["active_region"]
    field = bounds_of(
        [convert(corner) for corner in bounds_corners((region["x"], region["y"], region["x"] + region["width"], region["y"] + region["height"]))]
    )
    origin, size = (field[0], field[1]), (field[2] - field[0], field[3] - field[1])
    if len(boxes) != len(nets) or any(net not in boxes for net in nets):
        return None
    cell_across = size[across] - (len(nets) - 1) * pitch_across
    cell_along = size[long_axis] - (partners_count - 1) * pitch_along
    worst = 0.0
    for index, box in enumerate(sorted(boxes.values(), key=lambda box: box[across])):
        worst = max(worst, abs(box[across] - origin[across] - index * pitch_across), abs(box[across + 2] - box[across] - cell_across))
    for net, partners in zip(nets, members):
        if not partners or any(partner not in partner_boxes for partner in partners):
            return None
        slots = [round((partner_boxes[partner][long_axis] - origin[long_axis]) / pitch_along) for partner in partners]
        box = boxes[net]
        start = origin[long_axis] + min(slots) * pitch_along - rules.overhang
        end = origin[long_axis] + max(slots) * pitch_along + cell_along + rules.overhang
        worst = max(worst, abs(box[long_axis] - start), abs(box[long_axis + 2] - end))
    return worst


# --------------------------------------------------------------------------
# The diagonal Row bus (construction.row_bus, claude/specs/masked-field/
# P5-diagonal-bus.md, phase P5b): the gate and the stack keys of a pair.
# --------------------------------------------------------------------------


def _row_bus_kind(board: Mapping[str, Any]) -> Any:
    """``construction.row_bus.kind`` of a board, or ``None``."""

    return _row_bus_record(board).get("kind")


def _row_bus_registration(
    row_board: Mapping[str, Any], column_board: Mapping[str, Any], record: Mapping[str, Any], rules: Rules
) -> tuple[dict[str, Any], list[tuple[str, str]], list[tuple[str, str]]]:
    """The stack keys of a diagonal Row bus pair: ``(keys, errors, warnings)`` as ``(field, message)`` pairs.

    Outside the taxel field the two boards may overlap freely (two separate
    FPCs on either side of the film): outlines, the tails (stacked, one on the
    other where they meet; they part to their own connectors), and traces
    over traces at any angle.  The field and the tails' exit side are
    checked, in the stack frame (:func:`stack_frame`):

    - ``trace_over_other_electrode_count``, ``trace_over_other_window_count``:
      route parts (outside their own electrode grown by the coverlay
      expansion, the opening-to-trace rule and half their width, as strict
      record 14) whose copper reaches an electrode of the other board, or its
      field window (the union of its electrode openings, the merged field
      window or one opening per electrode); both must be 0.
    - ``row_trace_to_column_window_mm``, ``column_trace_to_row_window_mm``:
      the nearest such part to the other board's field window (``None``
      beyond the report reach); below the opening-to-trace rule a warning
      (W_STACK_TRACE_WINDOW).
    - ``trace_crossing_count``, ``trace_crossing_pairs`` and
      ``trace_crossing_min_angle_deg``: the Row and Column trace segments
      whose copper overlaps at an angle, the net pairs among them and their
      least angle (``None`` without a crossing); reported only, as the masked
      keys' ``trace_overlap_mm`` (copper running along the other board's).
    - ``tail_sides_match``: both tails leave through the same exit side (the
      design's E_ROW_BUS_TAILS rule, on the built pair); it must hold.
    - ``tail_overlap_width_mm``: the width across the tails of the two tails'
      rectangles' overlap (0 when they do not meet); reported only.
    - ``shared_outline_below_field_mm``: the Row board's
      ``construction.row_bus.shared_outline_below_field_mm``, how far below the
      taxel field (the active region's edge toward the tails) the boards share
      one outline; ``outline_deviation_over_field_mm``: the largest distance
      from a vertex of either outline's part beyond that level (away from the
      tails) to the other's, up to the report reach (``None`` without the
      record); ``outlines_coincide_over_field``: that distance is within the
      layout grid (the profile's epsilon); it must hold.

    The crossing set equals the mask by the masked keys.
    """

    epsilon = rules.epsilon
    keys: dict[str, Any] = {}
    errors: list[tuple[str, str]] = []
    warnings: list[tuple[str, str]] = []
    over_electrodes = over_windows = 0
    for key, board, other, other_key in (("row", row_board, column_board, "column"), ("column", column_board, row_board, "row")):
        electrodes, windows, gap, where = _stacked_trace_windows(board, other, rules)
        over_electrodes += electrodes
        over_windows += windows
        keys[f"{key}_trace_to_{other_key}_window_mm"] = None if gap is None else round6(gap)
        if windows or electrodes:
            errors.append((
                f"boards.{key}.layers.top_copper.routes",
                f"Stacked {key} trace parts run over the {other_key} board: {windows} over its field window, {electrodes} over "
                f"a {other_key} electrode (first {where}); outside its own electrode's zone a trace keeps off the other board's "
                "electrodes and their windows.",
            ))
        elif gap is not None and gap < rules.opening_to_trace - epsilon:
            warnings.append((
                f"boards.{key}.layers.top_copper.routes",
                f"A stacked {key} trace passes {gap:.6f} mm from the {other_key} board's field window (at {where}); the "
                f"target is the {rules.opening_to_trace:g} mm coverlay opening-to-trace rule.",
            ))
    keys["trace_over_other_electrode_count"] = over_electrodes
    keys["trace_over_other_window_count"] = over_windows
    crossings, pairs, smallest = _trace_crossings(row_board, column_board, epsilon)
    keys["trace_crossing_count"] = crossings
    keys["trace_crossing_pairs"] = pairs
    keys["trace_crossing_min_angle_deg"] = None if smallest is None else round6(smallest)
    if record.get("trace_overlap_mm") is None:
        keys["trace_overlap_mm"] = _trace_overlap(row_board, column_board, epsilon)["trace_overlap_mm"]
    sides = (row_board["tail"]["side"], column_board["tail"]["side"])
    keys["tail_sides_match"] = sides[0] == sides[1]
    if sides[0] != sides[1]:
        errors.append((
            "boards.column.tail.side",
            f"The Row tail leaves {sides[0]} and the Column tail {sides[1]}; the diagonal Row bus stacks both tails on one side.",
        ))
    row_tail, column_tail = _stacked_tail(row_board), _stacked_tail(column_board)
    across = 0 if sides[0] in ("bottom", "top") else 1
    meet = all(min(row_tail[axis + 2], column_tail[axis + 2]) > max(row_tail[axis], column_tail[axis]) for axis in (0, 1))
    width = min(row_tail[across + 2], column_tail[across + 2]) - max(row_tail[across], column_tail[across])
    keys["tail_overlap_width_mm"] = round6(width) if meet else 0.0
    depth = _row_bus_record(row_board).get("shared_outline_below_field_mm")
    depth = float(depth) if isinstance(depth, (int, float)) and not isinstance(depth, bool) else None
    deviation = None if depth is None else ring_deviation(
        _field_outline(row_board, depth), _field_outline(column_board, depth), _REPORT_REACH_MM
    )
    keys["shared_outline_below_field_mm"] = depth
    keys["outline_deviation_over_field_mm"] = None if deviation is None else round6(deviation)
    keys["outlines_coincide_over_field"] = deviation is not None and deviation <= epsilon
    if deviation is None:
        errors.append((
            "boards.row.construction.row_bus.shared_outline_below_field_mm",
            "The Row board records no level down to which the two boards share one outline; the diagonal Row bus gives both "
            "boards one outline over the taxel field.",
        ))
    elif deviation > epsilon:
        errors.append((
            "boards.column.outline",
            f"The Row and Column outlines differ by {deviation:.6f} mm in the stack from the tip down to {depth:g} mm below the "
            f"taxel field; the diagonal Row bus gives both boards one outline there (within {epsilon:g} mm).",
        ))
    return keys, errors, warnings


def _row_bus_record(board: Mapping[str, Any]) -> Mapping[str, Any]:
    """``construction.row_bus`` of a board, or an empty mapping."""

    construction = board.get("construction")
    row_bus = construction.get("row_bus") if isinstance(construction, Mapping) else None
    return row_bus if isinstance(row_bus, Mapping) else {}


# A stack-frame point turned so the board's tail points down (the tail side's quarter turns back).
_TAILS_DOWN = {
    "bottom": lambda x, y: [x, y],
    "top": lambda x, y: [-x, -y],
    "left": lambda x, y: [-y, x],
    "right": lambda x, y: [y, -x],
}


def _field_outline(board: Mapping[str, Any], depth: float) -> list[list[float]]:
    """The board's outline in the stack frame, tails down, beyond ``depth`` below the taxel field (its part away from
    the tails)."""

    convert = stack_frame(board)
    side = board["tail"]["side"]
    turn = _TAILS_DOWN[side]
    region = board["grid_registration"]["active_region"]
    half = float(region["height"] if side in ("bottom", "top") else region["width"]) / 2
    return clip_ring_above([turn(*convert(point)) for point in board["outline"]["points"]], -half - depth)


def _stacked_tail(board: Mapping[str, Any]) -> tuple:
    """The tail's rectangle (tip to root) in the stack frame."""

    convert = stack_frame(board)
    bounds = board["tail"]["bounds"]
    return bounds_of([convert(corner) for corner in bounds_corners((bounds["x"], bounds["y"], bounds["x"] + bounds["width"], bounds["y"] + bounds["height"]))])


def _stacked_trace_windows(board: Mapping[str, Any], other: Mapping[str, Any], rules: Rules) -> tuple[int, int, float | None, Any]:
    """``(parts over the other board's electrodes, parts over its field window, nearest window gap or None, where)`` of
    a board's traces in the stack.

    Each route segment is clipped outside its own electrode grown by the
    coverlay expansion, the opening-to-trace rule and its half width (the
    lane's own zone); a part counts once however many electrodes it
    reaches.  The other board's field window is the union of its electrode
    openings (the merged field window, polygon or rectangle, or one opening
    per electrode).  The window gap is measured up to the report reach.
    """

    epsilon = rules.epsilon
    convert = stack_frame(board)
    own = _stacked_electrodes(board)
    electrodes = _stacked_electrodes(other)
    others = sorted(electrodes.items())
    other_convert = stack_frame(other)
    windows = [
        [other_convert(point) for point in _opening_ring(opening)]
        for opening in other["layers"]["top_coverlay_openings"]
        if opening["kind"] in ("electrode_field_opening", "sensor_electrode_opening")
    ]
    parts = []
    for route in board["layers"]["top_copper"]["routes"]:
        radius = float(route["width_mm"]) / 2
        points = [convert(point) for point in route["points"]]
        box = own.get(route["net"])
        grow = rules.expansion + rules.opening_to_trace + radius
        zone = None if box is None else (box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow)
        for a, b in zip(points, points[1:]):
            if math.dist(a, b) <= 0:
                continue
            pieces = [(a, b)] if zone is None else clip_segment_outside_box(a, b, zone)
            parts.extend((route["net"], radius, c, d) for c, d in pieces)
    part_boxes = [
        (min(c[0], d[0]) - radius, min(c[1], d[1]) - radius, max(c[0], d[0]) + radius, max(c[1], d[1]) + radius)
        for _, radius, c, d in parts
    ]
    gaps: dict[int, float] = {}
    for part_index, window_index in _bbox_pairs(part_boxes, [bounds_of(ring) for ring in windows], rules.opening_to_trace + _REPORT_REACH_MM + epsilon):
        _, radius, c, d = parts[part_index]
        gap = _segment_ring_gap(c, d, windows[window_index]) - radius
        if part_index not in gaps or gap < gaps[part_index]:
            gaps[part_index] = gap
    over_windows, nearest, where = 0, None, None
    for part_index, gap in sorted(gaps.items()):
        if nearest is None or round6(gap) < round6(nearest):
            nearest, where = gap, [parts[part_index][0], "field window"]
        if gap <= epsilon:
            over_windows += 1
    over, first = set(), None
    for part_index, electrode_index in sorted(_bbox_pairs(part_boxes, [box for _, box in others], epsilon)):
        net, radius, c, d = parts[part_index]
        other_net, box = others[electrode_index]
        if segment_box_distance(c, d, box) - radius <= epsilon:
            over.add(part_index)
            if first is None:
                first = [net, other_net]
    return len(over), over_windows, nearest, first or where


def _segment_ring_gap(a: Sequence[float], b: Sequence[float], ring: Sequence[Sequence[float]]) -> float:
    """The distance from the segment ``a``-``b`` to the region of a closed ring (0 when it reaches it)."""

    if point_in_polygon(a, ring) or point_in_polygon(b, ring):
        return 0.0
    return min(segment_distance(a, b, p, q) for p, q in polygon_edges(ring))


def _trace_crossings(row_board: Mapping[str, Any], column_board: Mapping[str, Any], epsilon: float) -> tuple[int, int, float | None]:
    """``(crossing segment pairs, net pairs, least angle in degrees or None)`` of the stacked Row and Column traces.

    Two segments cross where their copper overlaps and they are not
    parallel (within ``_PARALLEL_RAD``); the angle between them is in
    ``[0, 90]`` degrees.
    """

    row_traces, column_traces = _stacked_traces(row_board), _stacked_traces(column_board)

    def boxes(traces: list) -> list[tuple]:
        return [
            (min(a[0], b[0]) - radius, min(a[1], b[1]) - radius, max(a[0], b[0]) + radius, max(a[1], b[1]) + radius)
            for _, a, b, radius in traces
        ]

    count, pairs, smallest = 0, set(), None
    for row_index, column_index in _bbox_pairs(boxes(row_traces), boxes(column_traces), 0.0):
        row_net, a, b, row_radius = row_traces[row_index]
        column_net, c, d, column_radius = column_traces[column_index]
        if segment_distance(a, b, c, d) >= row_radius + column_radius - epsilon:
            continue
        ux, uy, vx, vy = b[0] - a[0], b[1] - a[1], d[0] - c[0], d[1] - c[1]
        cross, dot = abs(ux * vy - uy * vx), abs(ux * vx + uy * vy)
        if cross <= _PARALLEL_RAD * math.hypot(ux, uy) * math.hypot(vx, vy):
            continue  # a run along the other trace: the overlap's
        angle = math.degrees(math.atan2(cross, dot))
        count += 1
        pairs.add((row_net, column_net))
        smallest = angle if smallest is None else min(smallest, angle)
    return count, len(pairs), smallest
