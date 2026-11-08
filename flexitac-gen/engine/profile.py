"""Locked manufacturing profile: loading and internal-consistency checks."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = _ROOT / "profiles" / "jlc_fpc_standard_v1.json"
SURFACE_PROFILE_PATH = _ROOT / "profiles" / "jlc_fpc_surface_v1.json"
# Every design template has its own locked profile file (profile_path).  The
# generic file names no template (its bytes, and so its digest in every
# generic build id, predate the surface template); any other profile names
# its template in a top-level ``template_id``.
GENERIC_TEMPLATE_ID = "generic_matrix_v1"
SURFACE_TEMPLATE_ID = "surface_matrix_v1"
TEMPLATE_IDS = (GENERIC_TEMPLATE_ID, SURFACE_TEMPLATE_ID)
# Optional geometry policies (see engine.layout.Rules): the first value of
# each is the generic behaviour, taken when the key is absent, so only a
# profile that sets a key is checked for it.
POLICIES = {
    ("routing", "row_channel"): ("contact_aligned", "tight"),
    ("fanout", "bus_angle"): ("cap", "shortest"),
    ("fanout", "column_convergence"): ("bundle", "direct"),
}

# Every numeric rule the engine reads; each must be a positive finite number.
_REQUIRED = {
    "fabrication": (
        "copper_to_board_edge_mm", "copper_to_slot_mm", "outline_tolerance_mm", "outline_tolerance_on_request_mm",
        "gold_finger_to_board_edge_mm", "trace_width_tolerance_fraction",
        "exposed_pad_to_trace_mm", "coverlay_expansion_mm", "coverlay_min_bridge_mm", "coverlay_opening_to_trace_mm",
        "maximum_outline_short_side_mm", "maximum_outline_long_side_mm", "recommended_pi_stiffener_mm",
        "recommended_pi_stiffener_fpc_thickness_mm", "recommended_pi_stiffener_connector_thickness_mm",
        "gold_finger_thickness_tolerance_mm",
    ),
    "stackup": (
        "core_polyimide_thickness_mm", "copper_thickness_mm", "coverlay_thickness_mm", "coverlay_adhesive_thickness_mm",
        "stiffener_thickness_mm",
    ),
    "routing": (
        "finger_trace_width_mm", "min_pad_space_mm", "min_pad_to_trace_mm", "min_electrode_gap_mm",
        "min_electrode_width_mm", "copper_to_edge_mm", "copper_to_cutout_mm", "active_edge_clearance_mm",
        "electrode_overhang_mm",
    ),
    "connector": (
        "pad_pitch_mm", "pad_width_mm", "contact_length_mm", "contact_tip_clearance_mm",
        "contact_center_to_side_edge_mm", "tail_tip_corner_radius_mm", "tail_width_tolerance_mm",
        "contact_width_tolerance_mm", "contact_zone_thickness_mm", "contact_zone_thickness_tolerance_mm", "maximum_pins",
    ),
    "coverlay": ("coverlay_expansion_mm", "coverlay_min_bridge_mm", "coverlay_opening_to_trace_mm", "coverlay_opening_general_max_length_mm"),
    "tail": ("minimum_length_mm", "stiffener_length_mm", "stiffener_end_clearance_mm"),
    "outline": (
        "outline_fillet_radius_mm", "arc_segment_max_angle_deg", "maximum_unfilleted_concave_turn_deg",
        "offset_allowance_mm",
    ),
    "fanout": (
        "maximum_channels_per_lane", "maximum_lanes", "slot_width_mm", "minimum_slot_width_mm", "slot_height_fraction",
        "minimum_slot_height_mm", "maximum_slot_height_mm", "lane_to_slot_clearance_mm", "maximum_taper_angle_deg",
    ),
    "drc": ("numeric_epsilon_mm",),
    "limits": (
        "minimum_rows", "maximum_rows", "minimum_columns", "maximum_columns", "minimum_pitch_mm", "maximum_pitch_mm",
        "minimum_trace_width_mm", "maximum_trace_width_mm", "minimum_trace_space_mm", "maximum_trace_space_mm",
        "maximum_tail_length_mm", "maximum_outline_short_side_mm", "maximum_outline_long_side_mm",
        "high_fill_factor_warning", "large_matrix_warning_taxels", "maximum_project_name_length",
    ),
    "order": ("fpc_layers", "fpc_thickness_mm", "outline_tolerance_mm", "reference_contact_window_margin_mm", "reference_field_window_length_mm"),
}
_INTEGER_KEYS = {
    ("connector", "maximum_pins"), ("fanout", "maximum_channels_per_lane"), ("fanout", "maximum_lanes"),
    ("limits", "minimum_rows"), ("limits", "maximum_rows"), ("limits", "minimum_columns"),
    ("limits", "maximum_columns"), ("limits", "large_matrix_warning_taxels"), ("limits", "maximum_project_name_length"),
    ("order", "fpc_layers"),
}
# Stiffeners the generator builds and the exporter writes: on the bottom,
# opposite the top-copper contacts, in a material whose orderable
# thicknesses the fabrication section lists (JLC publishes PI options).
STIFFENER_SIDES = ("bottom",)
STIFFENER_THICKNESS_OPTIONS = {"polyimide": "pi_stiffener_thickness_options_mm"}
STIFFENER_MATERIAL_NAMES = {"polyimide": "PI"}
# The generator writes one copper layer (stackup.construction single_copper_flexible).
COPPER_LAYERS = 1
# JLC's finished FPC thicknesses per ordered layer count (fabrication), for the boards' one copper layer.
_FPC_THICKNESS_OPTIONS = {COPPER_LAYERS: "single_layer_fpc_thickness_options_mm", COPPER_LAYERS + 1: "two_layer_fpc_thickness_options_mm"}
# The layers of the ordered FPC (stackup), and those left under the contacts,
# where the coverlay is open, before the stiffener is added.
_FPC_LAYERS = ("core_polyimide_thickness_mm", "copper_thickness_mm", "coverlay_thickness_mm", "coverlay_adhesive_thickness_mm")
_CONTACT_LAYERS = ("core_polyimide_thickness_mm", "copper_thickness_mm")
# JLC's minimum trace width and spacing per single-sided copper thickness: lists
# parallel to fabrication.single_sided_copper_thicknesses_mm.
_COPPER_MINIMUMS = ("single_sided_min_trace_width_mm", "single_sided_min_trace_space_mm")
# Profile texts the order notes cite (ORDER_NOTES.txt "Sources").
_ORDER_SOURCES = (
    ("jlcpcb_flex_capabilities", "url"), ("jlcpcb_flex_capabilities", "fetched"), ("jlcpcb_flex_capabilities", "trace_rules_rechecked"),
    ("flexitac_fabrication_guide", "url"), ("flexitac_fabrication_guide", "fetched"),
    ("jlcpcb_gold_finger_stiffeners", "url"), ("jlcpcb_gold_finger_stiffeners", "fetched"),
    ("jlcpcb_fpc_design_clearance", "url"), ("jlcpcb_fpc_design_clearance", "fetched"),
    ("reader_connectors", "rows"), ("reader_connectors", "columns"), ("reference_design",),
)


class ProfileError(ValueError):
    """Raised when the bundled manufacturing profile is internally inconsistent."""


def load_profile(template_id: str = GENERIC_TEMPLATE_ID) -> dict[str, Any]:
    """Load a fresh, validated copy of a template's bundled, locked FPC manufacturing profile.

    ``template_id`` is ``generic_matrix_v1`` (the default,
    ``profiles/jlc_fpc_standard_v1.json``) or ``surface_matrix_v1``
    (``profiles/jlc_fpc_surface_v1.json``); another value raises
    ``ValueError``.
    """

    path = profile_path(template_id)
    with path.open("r", encoding="utf-8") as profile_file:
        profile = json.load(profile_file)
    issues = profile_issues(profile)
    if not issues and profile_template(profile) != template_id:
        issues = [{"field": "profile.template_id", "message": f"names template {profile_template(profile)!r}, not {template_id!r}."}]
    if issues:
        details = "; ".join(f"{issue['field']}: {issue['message']}" for issue in issues)
        raise ProfileError(f"{path.name} is inconsistent: {details}")
    return profile


def profile_path(template_id: str = GENERIC_TEMPLATE_ID) -> Path:
    """The locked profile file of a design template (``PROFILE_PATH`` or ``SURFACE_PROFILE_PATH``); ``ValueError`` for another value."""

    if template_id == GENERIC_TEMPLATE_ID:
        return PROFILE_PATH
    if template_id == SURFACE_TEMPLATE_ID:
        return SURFACE_PROFILE_PATH
    raise ValueError(f"unknown design template {template_id!r}; the templates are {', '.join(map(repr, TEMPLATE_IDS))}")


def profile_template(profile: Any) -> str:
    """The design template a profile belongs to: its ``template_id``, else (the generic file) ``generic_matrix_v1``."""

    template = profile.get("template_id") if isinstance(profile, Mapping) else None
    return template if isinstance(template, str) else GENERIC_TEMPLATE_ID


def fabrication_minimum(profile: Mapping[str, Any]) -> tuple[float, float]:
    """JLC's minimum trace width and spacing for the profile's copper.

    ``fabrication`` lists the minimums per single-sided copper thickness
    (``single_sided_min_trace_width_mm`` / ``_space_mm``, parallel to
    ``single_sided_copper_thicknesses_mm``); the one that applies is the
    entry of ``stackup.copper_thickness_mm`` (1 oz: 4/4 mil, 0.1016 mm).
    Raises ``ValueError`` when the profile does not list that copper.
    """

    fab = profile["fabrication"]
    copper = float(profile["stackup"]["copper_thickness_mm"])
    lists = [fab["single_sided_copper_thicknesses_mm"], *(fab[key] for key in _COPPER_MINIMUMS)]
    for thickness, width, space in zip(*lists):
        if abs(float(thickness) - copper) <= 1e-9:
            return float(width), float(space)
    raise ValueError(f"the profile lists no trace minimum for {copper:g} mm copper")


def copper_weight_oz(profile: Mapping[str, Any]) -> float:
    """The weight (oz) of the profile's copper, from fabrication.single_sided_copper_weights_oz."""

    fab = profile["fabrication"]
    copper = float(profile["stackup"]["copper_thickness_mm"])
    for thickness, weight in zip(fab["single_sided_copper_thicknesses_mm"], fab["single_sided_copper_weights_oz"]):
        if abs(float(thickness) - copper) <= 1e-9:
            return float(weight)
    raise ValueError(f"the profile lists no copper weight for {copper:g} mm copper")


def profile_issues(profile: Any) -> list[dict[str, str]]:
    """Return structured internal-consistency errors of a manufacturing profile."""

    issues: list[dict[str, str]] = []

    def issue(code: str, field: str, message: str) -> None:
        issues.append({"code": code, "field": f"profile.{field}", "message": message})

    if not isinstance(profile, Mapping):
        issue("E_PROFILE_MISSING", "$", "The manufacturing profile must be a JSON object.")
        return issues
    for section, keys in _REQUIRED.items():
        block = profile.get(section)
        if not isinstance(block, Mapping):
            issue("E_PROFILE_MISSING", section, f"profile section {section!r} is missing.")
            continue
        for key in keys:
            value = block.get(key)
            if (section, key) in _INTEGER_KEYS:
                valid = isinstance(value, int) and not isinstance(value, bool) and value > 0
            else:
                valid = _number(value) and float(value) > 0
            if not valid:
                issue("E_PROFILE_MISSING", f"{section}.{key}", "must be a positive finite number.")
    if issues:
        return issues

    fab = profile["fabrication"]
    stack = profile["stackup"]
    route = profile["routing"]
    conn = profile["connector"]
    cover = profile["coverlay"]
    tail = profile["tail"]
    outline = profile["outline"]
    fan = profile["fanout"]
    limits = profile["limits"]
    # The gold-finger (tail) traces are the widest copper traces: no bundle
    # trace may be wider (checked below), so their half width sets every lead,
    # envelope and slot clearance.
    finger = float(route["finger_trace_width_mm"])
    half_trace = finger / 2
    pitch = float(conn["pad_pitch_mm"])
    pad = float(conn["pad_width_mm"])

    def at_least(code: str, field: str, value: float, floor: float, what: str) -> None:
        if value + 1e-12 < floor:
            issue(code, field, f"{what} is {value:.4f} mm but must be at least {floor:.4f} mm.")

    # Design rules may never be looser than the published fabrication capability,
    # here the trace minimums of the profile's copper (stackup.copper_thickness_mm).
    copper_options, weights = fab.get("single_sided_copper_thicknesses_mm"), fab.get("single_sided_copper_weights_oz")
    minimums = [fab.get(key) for key in _COPPER_MINIMUMS]
    listed_minimums = _thicknesses(copper_options) and all(_thicknesses(values) and len(values) == len(copper_options) for values in minimums)
    if not listed_minimums:
        issue(
            "E_PROFILE_MISSING",
            f"fabrication.{_COPPER_MINIMUMS[0]}",
            "fabrication must give the minimum trace width and spacing (single_sided_min_trace_width_mm, single_sided_min_trace_space_mm) "
            "for every fabrication.single_sided_copper_thicknesses_mm entry.",
        )
    elif _listed(stack["copper_thickness_mm"], copper_options):
        minimum_width, minimum_space = fabrication_minimum(profile)
        copper_text = f"{float(stack['copper_thickness_mm']):g} mm copper"
        at_least("E_PROFILE_FAB_LIMIT", "limits.minimum_trace_width_mm", limits["minimum_trace_width_mm"], minimum_width, f"minimum trace width ({copper_text})")
        at_least("E_PROFILE_FAB_LIMIT", "limits.minimum_trace_space_mm", limits["minimum_trace_space_mm"], minimum_space, f"minimum trace space ({copper_text})")
        at_least("E_PROFILE_FAB_LIMIT", "routing.finger_trace_width_mm", finger, minimum_width, f"finger trace width ({copper_text})")
        at_least("E_PROFILE_FAB_LIMIT", "routing.finger_trace_width_mm", pitch - finger, minimum_space, f"finger-section spacing, contact pitch less finger width ({copper_text})")
        at_least("E_PROFILE_FAB_LIMIT", "routing.min_electrode_width_mm", route["min_electrode_width_mm"], minimum_width, f"minimum electrode width ({copper_text})")
        for field in ("min_electrode_gap_mm", "min_pad_space_mm"):
            at_least("E_PROFILE_FAB_LIMIT", f"routing.{field}", route[field], minimum_space, f"{field} ({copper_text})")
    # The bundle (fan-out) trace inputs: their ranges, no wider than the fingers,
    # and width plus spacing within the contact pitch, where the bundle expands.
    for kind in ("width", "space"):
        if limits[f"minimum_trace_{kind}_mm"] > limits[f"maximum_trace_{kind}_mm"]:
            issue("E_PROFILE_INCONSISTENT", f"limits.minimum_trace_{kind}_mm", f"exceeds limits.maximum_trace_{kind}_mm.")
    if limits["maximum_trace_width_mm"] > finger + 1e-12:
        issue("E_PROFILE_INCONSISTENT", "limits.maximum_trace_width_mm", "a bundle trace would be wider than routing.finger_trace_width_mm.")
    at_least("E_PROFILE_FAB_LIMIT", "routing.copper_to_edge_mm", route["copper_to_edge_mm"], fab["copper_to_board_edge_mm"], "copper to board edge")
    at_least("E_PROFILE_FAB_LIMIT", "routing.copper_to_cutout_mm", route["copper_to_cutout_mm"], fab["copper_to_slot_mm"], "copper to routed slot")
    at_least("E_PROFILE_FAB_LIMIT", "routing.min_pad_to_trace_mm", route["min_pad_to_trace_mm"], fab["exposed_pad_to_trace_mm"], "pad to trace")
    for field in ("coverlay_expansion_mm", "coverlay_min_bridge_mm", "coverlay_opening_to_trace_mm"):
        at_least("E_PROFILE_FAB_LIMIT", f"coverlay.{field}", cover[field], fab[field], field)
    at_least("E_PROFILE_FAB_LIMIT", "connector.contact_tip_clearance_mm", conn["contact_tip_clearance_mm"], fab["gold_finger_to_board_edge_mm"], "contact to tip edge")
    for field in ("maximum_outline_short_side_mm", "maximum_outline_long_side_mm"):
        if limits[field] > fab[field] + 1e-9:
            issue("E_PROFILE_FAB_LIMIT", f"limits.{field}", f"exceeds the fabrication maximum {fab[field]} mm.")
    side, material = stack.get("stiffener_side"), stack.get("stiffener_material")
    if not isinstance(side, str) or not isinstance(material, str):
        issue("E_PROFILE_MISSING", "stackup.stiffener_side", "stiffener side/material are required.")
    else:
        if side not in STIFFENER_SIDES:
            issue(
                "E_PROFILE_INCONSISTENT",
                "stackup.stiffener_side",
                f"{side!r} would cover the top-copper contacts; stiffeners go on the {' or '.join(STIFFENER_SIDES)}.",
            )
        options_key = STIFFENER_THICKNESS_OPTIONS.get(material)
        if options_key is None:
            issue(
                "E_PROFILE_FAB_LIMIT",
                "stackup.stiffener_material",
                f"{material!r} has no orderable thickness list; supported: {', '.join(STIFFENER_THICKNESS_OPTIONS)}.",
            )
        else:
            options = fab.get(options_key)
            if not _thicknesses(options):
                issue("E_PROFILE_MISSING", f"fabrication.{options_key}", "must be a list of thicknesses.")
            elif not _listed(stack["stiffener_thickness_mm"], options):
                issue(
                    "E_PROFILE_FAB_LIMIT",
                    "stackup.stiffener_thickness_mm",
                    f"{stack['stiffener_thickness_mm']} mm is not a JLC {material} stiffener option {options}.",
                )
    strings = (
        (None, "id"), (None, "revision"), ("stackup", "construction"), ("fabrication", "surface_finish"), ("order", "surface_finish"),
    )
    for section, key in strings:
        value = profile.get(key) if section is None else profile[section].get(key)
        if not isinstance(value, str) or not value.strip():
            issue("E_PROFILE_MISSING", key if section is None else f"{section}.{key}", "must be a non-empty string.")

    # Order options (ORDER_NOTES.txt): JLC must offer each one, and together
    # they must hold the reader connectors' tail tolerances.
    order = profile["order"]
    # The generator writes COPPER_LAYERS copper layer: the boards are ordered as JLC's 1-layer FPC, or as its 2-layer FPC
    # with the bottom copper empty (the FlexiTac fabrication guide's 0.2 mm, the order since 2026-11-06).
    options_key = _FPC_THICKNESS_OPTIONS.get(order["fpc_layers"])
    fpc_options = fab.get(options_key) if options_key else None
    if options_key is None:
        issue(
            "E_PROFILE_INCONSISTENT", "order.fpc_layers",
            f"the generator writes {COPPER_LAYERS} copper layer, so the order needs {COPPER_LAYERS} or {COPPER_LAYERS + 1} (the bottom copper empty).",
        )
    elif not _thicknesses(fpc_options):
        issue("E_PROFILE_MISSING", f"fabrication.{options_key}", "must be a list of thicknesses.")
    elif not _listed(order["fpc_thickness_mm"], fpc_options):
        issue("E_PROFILE_FAB_LIMIT", "order.fpc_thickness_mm", f"{order['fpc_thickness_mm']} mm is not a JLC {order['fpc_layers']}-layer FPC thickness {fpc_options}.")
    elif order["fpc_layers"] != COPPER_LAYERS:
        # A 2-layer order is JLC's own build of the boards' one copper layer: the stack-up stays the boards' own build, a
        # 1-layer FPC of JLC's tables, so its layers add up to one of JLC's 1-layer thicknesses.
        single = fab.get("single_layer_fpc_thickness_options_mm")
        layers = round(math.fsum(float(stack[key]) for key in _FPC_LAYERS), 6)
        if not _thicknesses(single):
            issue("E_PROFILE_MISSING", "fabrication.single_layer_fpc_thickness_options_mm", "must be a list of thicknesses.")
        elif min(abs(layers - float(option)) for option in single) >= _half_step(single):
            issue(
                "E_PROFILE_INCONSISTENT",
                "stackup",
                f"the core, copper and coverlay layers add up to {layers:g} mm, none of JLC's 1-layer FPC thicknesses {single} "
                "(the boards' own build).",
            )
    else:
        # The stack-up describes the ordered build: its layers add up to the
        # ordered thickness, closer than half the step between JLC's options.
        layers = round(sum(float(stack[key]) for key in _FPC_LAYERS), 6)
        if abs(layers - float(order["fpc_thickness_mm"])) >= _half_step(fpc_options):
            issue(
                "E_PROFILE_INCONSISTENT",
                "stackup",
                f"the core, copper and coverlay layers add up to {layers:g} mm, not the ordered {order['fpc_thickness_mm']:g} mm FPC "
                "(order.fpc_thickness_mm).",
            )
    if not _thicknesses(copper_options) or not _thicknesses(weights) or len(weights) != len(copper_options):
        issue(
            "E_PROFILE_MISSING",
            "fabrication.single_sided_copper_weights_oz",
            "must give one copper weight per fabrication.single_sided_copper_thicknesses_mm entry.",
        )
    elif not _listed(stack["copper_thickness_mm"], copper_options):
        issue("E_PROFILE_FAB_LIMIT", "stackup.copper_thickness_mm", f"{stack['copper_thickness_mm']} mm is not a JLC single-sided copper {copper_options}.")
    # The contacts sit in the open coverlay window: the stiffener must give the
    # thickness both reader connectors take.  On a 1-layer order core, copper and
    # the stiffener make it.  On a 2-layer order it is JLC's rule, the ordered FPC
    # plus the stiffener (the user's decision of 2026-11-06, "建议把补强改成 0.1 mm"
    # -> "好的": 0.2 + 0.1 = 0.3 mm; the 0.225 mm stiffener of before gives 0.425).
    if order["fpc_layers"] > COPPER_LAYERS:
        contact_zone = round(math.fsum((float(order["fpc_thickness_mm"]), float(stack["stiffener_thickness_mm"]))), 6)
        made = "order.fpc_thickness_mm + stiffener, JLC's rule: thickness with stiffener = FPC thickness + stiffener thickness"
    else:
        contact_zone = round(sum(float(stack[key]) for key in _CONTACT_LAYERS) + float(stack["stiffener_thickness_mm"]), 6)
        made = "core + copper + stiffener under the open coverlay"
    if abs(contact_zone - conn["contact_zone_thickness_mm"]) > conn["contact_zone_thickness_tolerance_mm"] + 1e-9:
        issue(
            "E_PROFILE_INCONSISTENT",
            "stackup.stiffener_thickness_mm",
            f"gives a {contact_zone:g} mm contact zone ({made}), outside the "
            f"{conn['contact_zone_thickness_mm']:g} +/-{conn['contact_zone_thickness_tolerance_mm']:g} mm the reader connectors take.",
        )
    tolerance = float(order["outline_tolerance_mm"])
    at_least("E_PROFILE_FAB_LIMIT", "order.outline_tolerance_mm", tolerance, fab["outline_tolerance_on_request_mm"], "requested outline tolerance")
    if tolerance > conn["tail_width_tolerance_mm"] + 1e-12:
        issue(
            "E_PROFILE_INCONSISTENT",
            "order.outline_tolerance_mm",
            f"+/-{tolerance:g} mm can take the tail width outside connector.tail_width_tolerance_mm (+/-{conn['tail_width_tolerance_mm']:g} mm).",
        )
    if fab["outline_tolerance_on_request_mm"] > fab["outline_tolerance_mm"] + 1e-12:
        issue("E_PROFILE_INCONSISTENT", "fabrication.outline_tolerance_on_request_mm", "exceeds the default outline tolerance.")
    finish, ordered = fab.get("surface_finish"), order.get("surface_finish")
    if all(isinstance(value, str) and value.strip() for value in (finish, ordered)) and ordered != finish:
        issue("E_PROFILE_FAB_LIMIT", "order.surface_finish", f"{ordered!r} is not the JLC FPC surface finish {finish!r}.")
    pi_options = fab.get(STIFFENER_THICKNESS_OPTIONS["polyimide"])
    if _thicknesses(pi_options) and not _listed(fab["recommended_pi_stiffener_mm"], pi_options):
        issue("E_PROFILE_INCONSISTENT", "fabrication.recommended_pi_stiffener_mm", "is not a JLC PI stiffener option.")
    if not fab["trace_width_tolerance_fraction"] < 1:
        issue("E_PROFILE_INCONSISTENT", "fabrication.trace_width_tolerance_fraction", "must be a fraction below 1.")
    if not conn["contact_width_tolerance_mm"] < pad:
        issue("E_PROFILE_INCONSISTENT", "connector.contact_width_tolerance_mm", "must be smaller than connector.pad_width_mm.")
    if not conn["contact_zone_thickness_tolerance_mm"] < conn["contact_zone_thickness_mm"]:
        issue("E_PROFILE_INCONSISTENT", "connector.contact_zone_thickness_tolerance_mm", "must be smaller than connector.contact_zone_thickness_mm.")
    sources = profile.get("sources")
    for path in _ORDER_SOURCES:
        value = sources
        for key in path:
            value = value.get(key) if isinstance(value, Mapping) else None
        if not isinstance(value, str) or not value.strip():
            issue("E_PROFILE_MISSING", "sources." + ".".join(path), "must be a non-empty string (the order notes cite it).")
        elif path[0] == "reader_connectors" and " (" not in value.strip():
            issue("E_PROFILE_MISSING", "sources." + ".".join(path), "must name the part first, then ' (' and the drawing (the order notes name the part).")

    # Connector tail: (pins + 1) x pitch wide, contacts fully clear of the edges.
    if pitch - pad + 1e-12 < route["min_pad_space_mm"]:
        issue("E_PROFILE_PAD_SPACE", "connector.pad_width_mm", "adjacent connector contacts violate routing.min_pad_space_mm.")
    # Routes at the contact pitch: the finger traces, and the widest bundle traces
    # at their widest spacing, must keep the largest trace space a design may ask for.
    if pitch - finger + 1e-12 < limits["maximum_trace_space_mm"]:
        issue("E_PROFILE_ROUTE_SPACE", "connector.pad_pitch_mm", "finger traces at the contact pitch leave less than limits.maximum_trace_space_mm.")
    if limits["maximum_trace_width_mm"] + limits["maximum_trace_space_mm"] > pitch + 1e-12:
        issue("E_PROFILE_ROUTE_SPACE", "limits.maximum_trace_space_mm", "the widest bundle traces at their widest spacing do not fit the contact pitch.")
    if pitch - pad / 2 - half_trace + 1e-12 < route["min_pad_to_trace_mm"]:
        issue("E_PROFILE_PAD_SPACE", "routing.min_pad_to_trace_mm", "a contact lead would pass the neighbouring contact too closely.")
    side_offset = float(conn["contact_center_to_side_edge_mm"])
    at_least("E_PROFILE_INCONSISTENT", "connector.contact_center_to_side_edge_mm", side_offset - pad / 2, route["copper_to_edge_mm"], "contact to tail side")
    at_least("E_PROFILE_INCONSISTENT", "connector.contact_center_to_side_edge_mm", side_offset - half_trace - outline["offset_allowance_mm"], route["copper_to_edge_mm"], "lead to tail side")
    at_least("E_PROFILE_INCONSISTENT", "connector.contact_tip_clearance_mm", conn["contact_tip_clearance_mm"], route["copper_to_edge_mm"], "contact to tip edge")
    if abs(2 * side_offset - 2 * pitch) > conn["tail_width_tolerance_mm"] + 1e-12:
        issue("E_PROFILE_INCONSISTENT", "connector.contact_center_to_side_edge_mm", "the tail width no longer matches the connector formula pitch x (pins + 1).")
    if conn["tail_tip_corner_radius_mm"] > side_offset - pad / 2 + 1e-12:
        issue("E_PROFILE_INCONSISTENT", "connector.tail_tip_corner_radius_mm", "the rounded tip corner would reach the outer contacts.")
    if conn["maximum_pins"] < max(limits["maximum_rows"], limits["maximum_columns"]):
        issue("E_PROFILE_INCONSISTENT", "connector.maximum_pins", "must allow at least one contact per channel at the channel limits.")

    # Stiffened connector zone and tail.  The outline may start to widen
    # before the tail root: by one fillet radius at the Row tail-root fillet,
    # and on the Column board where the fillet meets the steepest merger taper
    # leaving the outer contact lead.  The stiffener plus its straight
    # clearance must still fit on the shortest tail.
    contact_end = conn["contact_tip_clearance_mm"] + conn["contact_length_mm"]
    at_least("E_PROFILE_INCONSISTENT", "tail.stiffener_length_mm", tail["stiffener_length_mm"], contact_end, "stiffened zone")
    fillet = float(outline["outline_fillet_radius_mm"])
    envelope = half_trace + route["copper_to_edge_mm"] + outline["offset_allowance_mm"]
    steepest = math.radians(min(float(fan["maximum_taper_angle_deg"]), 89.0))
    early = (envelope + fillet) * math.tan(steepest / 2) - (conn["contact_center_to_side_edge_mm"] - envelope) / math.tan(steepest)
    at_least(
        "E_PROFILE_INCONSISTENT",
        "tail.minimum_length_mm",
        tail["minimum_length_mm"],
        tail["stiffener_length_mm"] + tail["stiffener_end_clearance_mm"] + max(fillet, early),
        "minimum tail length",
    )
    at_least("E_PROFILE_INCONSISTENT", "tail.minimum_length_mm", tail["minimum_length_mm"], contact_end + cover["coverlay_expansion_mm"], "minimum tail length")
    if limits["maximum_tail_length_mm"] < tail["minimum_length_mm"]:
        issue("E_PROFILE_INCONSISTENT", "limits.maximum_tail_length_mm", "is below tail.minimum_length_mm.")

    # Active field margins hold the electrode overhang, its coverlay opening and the edge rule.
    margin = float(route["active_edge_clearance_mm"])
    at_least("E_PROFILE_INCONSISTENT", "routing.active_edge_clearance_mm", margin - route["electrode_overhang_mm"], route["copper_to_edge_mm"], "electrode overhang to edge")
    at_least("E_PROFILE_INCONSISTENT", "routing.active_edge_clearance_mm", margin - route["electrode_overhang_mm"] - cover["coverlay_expansion_mm"], 0.0, "electrode opening to edge")
    at_least("E_PROFILE_INCONSISTENT", "routing.min_electrode_gap_mm", route["min_electrode_gap_mm"], 0.0, "electrode gap")

    # Fan-out capacity, the bundle and the taper cap.
    if fan["maximum_lanes"] > 2:
        issue("E_PROFILE_INCONSISTENT", "fanout.maximum_lanes", "the generator implements one or two fan-out lanes.")
    if fan["maximum_lanes"] * fan["maximum_channels_per_lane"] < limits["maximum_columns"]:
        issue("E_PROFILE_INCONSISTENT", "limits.maximum_columns", "exceeds maximum_lanes x maximum_channels_per_lane.")
    # The fan-out converges from the electrode pitch into the bundle: the widest
    # bundle pitch must stay below the finest electrode pitch.
    if limits["maximum_trace_width_mm"] + limits["maximum_trace_space_mm"] >= limits["minimum_pitch_mm"]:
        issue("E_PROFILE_INCONSISTENT", "limits.minimum_pitch_mm", "the widest bundle pitch (trace width + space) reaches the finest electrode pitch.")
    if not fan["maximum_taper_angle_deg"] < 90:
        issue("E_PROFILE_INCONSISTENT", "fanout.maximum_taper_angle_deg", "must be below 90 degrees.")
    if fan["maximum_taper_angle_deg"] < 1:
        # A cap this flat leaves no bend stagger on the layout grid (and so no bus angle).
        issue("E_PROFILE_INCONSISTENT", "fanout.maximum_taper_angle_deg", "must be at least 1 degree.")
    at_least("E_PROFILE_INCONSISTENT", "fanout.lane_to_slot_clearance_mm", fan["lane_to_slot_clearance_mm"] - half_trace, route["copper_to_cutout_mm"], "lane to slot")
    if fan["minimum_slot_width_mm"] > fan["slot_width_mm"] or fan["minimum_slot_height_mm"] > fan["maximum_slot_height_mm"]:
        issue("E_PROFILE_INCONSISTENT", "fanout.minimum_slot_width_mm", "slot minimums exceed their maximums.")
    if 2 * outline["outline_fillet_radius_mm"] > min(fan["minimum_slot_width_mm"], fan["minimum_slot_height_mm"]):
        issue("E_PROFILE_INCONSISTENT", "outline.outline_fillet_radius_mm", "the slot cannot hold its corner fillets.")
    if outline["maximum_unfilleted_concave_turn_deg"] < outline["arc_segment_max_angle_deg"]:
        issue("E_PROFILE_INCONSISTENT", "outline.maximum_unfilleted_concave_turn_deg", "is smaller than one arc segment.")

    # The template and the optional geometry policies (absent: the generic behaviour).
    if "template_id" in profile and profile["template_id"] not in TEMPLATE_IDS:
        issue("E_PROFILE_INCONSISTENT", "template_id", f"must be one of {', '.join(map(repr, TEMPLATE_IDS))}.")
    for (section, key), allowed in POLICIES.items():
        if key in profile[section] and profile[section][key] not in allowed:
            issue("E_PROFILE_INCONSISTENT", f"{section}.{key}", f"must be one of {', '.join(map(repr, allowed))}.")
    if fan.get("bus_angle") == "shortest" or "minimum_taper_angle_deg" in fan:
        # The bus angle is searched over whole-degree caps from this one up to maximum_taper_angle_deg.
        lowest = fan.get("minimum_taper_angle_deg")
        if not (_number(lowest) and float(lowest) > 0):
            issue("E_PROFILE_MISSING", "fanout.minimum_taper_angle_deg", "must be a positive finite number (the first cap of the bus-angle search).")
        elif float(lowest) < 1 or float(lowest) != math.floor(float(lowest)):
            issue("E_PROFILE_INCONSISTENT", "fanout.minimum_taper_angle_deg", "must be a whole number of degrees, at least 1 (the caps tried are whole degrees).")
        elif lowest > fan["maximum_taper_angle_deg"]:
            issue("E_PROFILE_INCONSISTENT", "fanout.minimum_taper_angle_deg", "exceeds fanout.maximum_taper_angle_deg.")
    if fan.get("column_convergence") == "direct" and fan["maximum_lanes"] != 1:
        issue("E_PROFILE_INCONSISTENT", "fanout.column_convergence", "direct convergence is implemented for one fan-out lane (fanout.maximum_lanes 1).")

    # Matrix limits.
    if limits["minimum_rows"] > limits["maximum_rows"] or limits["minimum_columns"] > limits["maximum_columns"]:
        issue("E_PROFILE_INCONSISTENT", "limits", "minimum channel counts exceed the maximums.")
    if limits["minimum_pitch_mm"] > limits["maximum_pitch_mm"]:
        issue("E_PROFILE_INCONSISTENT", "limits.minimum_pitch_mm", "exceeds limits.maximum_pitch_mm.")
    at_least(
        "E_PROFILE_INCONSISTENT",
        "limits.minimum_pitch_mm",
        limits["minimum_pitch_mm"],
        route["min_electrode_width_mm"] + route["min_electrode_gap_mm"],
        "minimum pitch",
    )
    if limits["maximum_outline_short_side_mm"] > limits["maximum_outline_long_side_mm"]:
        issue("E_PROFILE_INCONSISTENT", "limits.maximum_outline_short_side_mm", "exceeds the long-side maximum.")
    if not math.isfinite(float(profile["drc"]["numeric_epsilon_mm"])) or profile["drc"]["numeric_epsilon_mm"] > 1e-3:
        issue("E_PROFILE_INCONSISTENT", "drc.numeric_epsilon_mm", "must be a small numerical tolerance (<= 0.001 mm).")
    return issues


def order_requirements(profile: Mapping[str, Any], default_design: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The JLCPCB order options and review notes of a consistent profile.

    Each entry has ``id``, ``kind`` (``order_option``: set or request it on the
    JLCPCB order; ``review_note``: check it), ``topic``, ``requirement``,
    ``special_request``, ``reason``, ``sources`` (keys of the profile's
    ``sources`` block) and the figures it states as ``values``.  Every figure
    comes from the profile, except the default fan-out trace width of the
    trace note, which the caller passes as ``default_design``
    (``engine.default_design()``).  The exporter writes them to each board ZIP
    and the review bundle (``ORDER_NOTES.txt``, ``manifest.json``);
    ``/api/default`` gives them to the browser.  They do not depend on a
    build: each board's lines of ``ORDER_NOTES.txt`` give the build's own
    trace widths and what JLC's width tolerance makes of them.
    """

    fab, stack, conn, cover, tail, order = (
        profile[section] for section in ("fabrication", "stackup", "connector", "coverlay", "tail", "order")
    )
    readers = profile["sources"]["reader_connectors"]
    rows_part, columns_part = (readers[role].split(" (", 1)[0] for role in ("rows", "columns"))
    material = STIFFENER_MATERIAL_NAMES.get(stack["stiffener_material"], stack["stiffener_material"])
    stiffener, fpc = float(stack["stiffener_thickness_mm"]), float(order["fpc_thickness_mm"])
    two_layer = order["fpc_layers"] > COPPER_LAYERS
    # The boards' own layers: the ordered FPC on a 1-layer order, JLC's 2-layer build of them otherwise.
    own = round(core_layers(stack), 6) if two_layer else fpc
    core, copper = (float(stack[key]) for key in _CONTACT_LAYERS)
    coverlay, adhesive = float(stack["coverlay_thickness_mm"]), float(stack["coverlay_adhesive_thickness_mm"])
    copper_options, weights = fab["single_sided_copper_thicknesses_mm"], fab["single_sided_copper_weights_oz"]
    weight = copper_weight_oz(profile)
    zone, zone_tolerance = float(conn["contact_zone_thickness_mm"]), float(conn["contact_zone_thickness_tolerance_mm"])
    recommended = tuple(
        float(fab[key])
        for key in ("recommended_pi_stiffener_mm", "recommended_pi_stiffener_fpc_thickness_mm", "recommended_pi_stiffener_connector_thickness_mm")
    )
    follows = all(abs(a - b) <= 1e-9 for a, b in zip(recommended, (stiffener, own, zone)))
    tolerance, default_tolerance = float(order["outline_tolerance_mm"]), float(fab["outline_tolerance_mm"])
    special = tolerance < default_tolerance - 1e-12
    width, width_tolerance = float(conn["pad_width_mm"]), float(conn["contact_width_tolerance_mm"])
    fraction = float(fab["trace_width_tolerance_fraction"])
    width_exceeds = width * fraction > width_tolerance + 1e-12
    expansion, radius = float(cover["coverlay_expansion_mm"]), float(conn["tail_tip_corner_radius_mm"])
    # The gang window stops where the rounded tip corners begin (engine.layout).
    margin = round(min(expansion, float(conn["contact_center_to_side_edge_mm"]) - width / 2 - radius), 6)
    start = float(conn["contact_tip_clearance_mm"])
    # Under the open coverlay the contacts keep the core and the copper, plus the stiffener; on a 2-layer order the
    # thickness is JLC's rule, the ordered FPC plus the stiffener (profile_issues).
    contact_zone = round(math.fsum((fpc, stiffener)), 6) if two_layer else round(core + copper + stiffener, 6)
    finger_tolerance = float(fab["gold_finger_thickness_tolerance_mm"])
    zone_held = zone - zone_tolerance - 1e-9 <= contact_zone - finger_tolerance and contact_zone + finger_tolerance <= zone + zone_tolerance + 1e-9
    jlc, gold, clearance = "jlcpcb_flex_capabilities", "jlcpcb_gold_finger_stiffeners", "jlcpcb_fpc_design_clearance"
    # JLC's general length limit of one coverlay opening, and the longest field window of the JLC-accepted reference design.
    window_limit, reference_window = float(cover["coverlay_opening_general_max_length_mm"]), float(order["reference_field_window_length_mm"])
    # The coverlay bridge below which the electrode windows merge into one (engine.layout).
    bridge = float(cover["coverlay_min_bridge_mm"])
    bundle = float(default_design["routing"]["trace_width_mm"])
    finger = float(profile["routing"]["finger_trace_width_mm"])
    minimum_width, minimum_space = fabrication_minimum(profile)

    def entry(key: str, kind: str, topic: str, requirement: str, reason: str, sources: tuple, values: dict, request: bool = False) -> dict:
        return {
            "id": key, "kind": kind, "topic": topic, "requirement": requirement, "special_request": request,
            "reason": reason, "sources": list(sources), "values": values,
        }

    return [
        entry(
            "fpc_thickness", "order_option", "Layers and FPC thickness",
            f"{order['fpc_layers']} layer, {_g(fpc)} mm FPC thickness (finished, without the stiffener)"
            + (", the bottom copper layer empty" if two_layer else ""),
            (f"The FlexiTac fabrication guide orders {_g(fpc)} mm, one of JLC's 2-layer finished thicknesses "
             f"({_list(fab['two_layer_fpc_thickness_options_mm'])} mm); the boards have one copper layer, so the bottom one stays empty"
             + "." if two_layer else f"JLC's 1-layer finished thicknesses are {_list(fab['single_layer_fpc_thickness_options_mm'])} mm"
             + (f"; the {material} stiffener below is JLC's choice for {_g(fpc)} mm." if follows else ".")),
            (jlc, "flexitac_fabrication_guide") if two_layer else (jlc,), {"fpc_layers": order["fpc_layers"], "fpc_thickness_mm": fpc},
        ),
        entry(
            "copper_weight", "order_option", "Copper weight", f"{_g(weight)} oz ({_g(copper)} mm)",
            f"With {_g(copper)} mm copper, the {_g(core)} mm PI core and the {_g(coverlay)} mm PI + {_g(adhesive)} mm adhesive "
            + (f"coverlay, the boards' own layers come to {_g(own)} mm; JLC builds them as the "
               f"{_g(fpc)} mm {order['fpc_layers']}-layer FPC ordered above" if two_layer else f"coverlay make the {_g(fpc)} mm FPC ordered above")
            + f"; JLC's single-sided copper is {_list(weights)} oz "
            f"({_list(copper_options)} mm).",
            (jlc,),
            {
                "copper_weight_oz": weight, "copper_thickness_mm": copper, "core_polyimide_thickness_mm": core,
                "coverlay_thickness_mm": coverlay, "coverlay_adhesive_thickness_mm": adhesive,
            },
        ),
        entry(
            "pi_stiffener", "order_option", "Stiffener",
            f"{material} {_g(stiffener)} mm on the {stack['stiffener_side']} side at the contacts "
            f"(the {_g(tail['stiffener_length_mm'])} mm zone from the tip)",
            f"Both reader connectors take a {_g(zone)} +/-{_g(zone_tolerance)} mm thick FPC at the contacts"
            + (f", and by JLC's rule the thickness with a stiffener is the FPC thickness plus the stiffener thickness: the "
               f"{_g(fpc)} mm FPC ordered above + {_g(stiffener)} mm = {_g(contact_zone)} mm. JLC's recommended "
               f"{_g(recommended[0])} mm {material} stiffener for a {_g(recommended[2])} mm thick connector is for a "
               f"{_g(recommended[1])} mm FPC." if two_layer else
               f"; JLC recommends a {_g(recommended[0])} mm {material} stiffener for a {_g(recommended[2])} mm thick connector on a "
               f"{_g(recommended[1])} mm FPC" + ("." if follows else f" (this profile: {_g(stiffener)} mm on {_g(fpc)} mm, for {_g(zone)} mm)."))
            + " The gold-finger thickness below takes priority when JLC chooses the stiffener under the gold fingers.",
            (jlc, "reader_connectors.rows", "reader_connectors.columns", gold),
            {
                "material": stack["stiffener_material"], "side": stack["stiffener_side"], "thickness_mm": stiffener,
                "zone_length_mm": float(tail["stiffener_length_mm"]),
            },
        ),
        entry(
            "gold_finger_thickness", "order_option", "Gold fingers",
            f"Yes, Gold Fingers Thickness {_g(zone)} mm (the stiffened contact zone in total, from the contact surface to the "
            "outer surface of the stiffener)",
            f"Both reader connectors take a {_g(zone)} +/-{_g(zone_tolerance)} mm thick FPC at the contacts. JLC gives the total "
            "gold-finger thickness the highest priority when it chooses the stiffener under the gold fingers, so its PI "
            f"calculator may take another {material} thickness there than the {_g(stiffener)} mm above; it holds the gold-finger "
            f"area to +/-{_g(finger_tolerance)} mm.",
            (gold, jlc, "reader_connectors.rows", "reader_connectors.columns"),
            {
                "gold_fingers": True, "gold_finger_thickness_mm": zone, "connector_thickness_tolerance_mm": zone_tolerance,
                "gold_finger_thickness_tolerance_mm": finger_tolerance,
            },
        ),
        entry(
            "outline_tolerance", "order_option", "Outline tolerance",
            f"+/-{_g(tolerance)} mm" + (f" (special request; JLC's default is +/-{_g(default_tolerance)} mm)" if special else ""),
            f"The {columns_part} connector needs the tail width {_g(conn['pad_pitch_mm'])} x (N + 1) mm within "
            f"+/-{_g(conn['tail_width_tolerance_mm'])} mm; "
            f"JLC's laser-outline tolerance is +/-{_g(default_tolerance)} mm, +/-{_g(fab['outline_tolerance_on_request_mm'])} mm on request.",
            (jlc, "reader_connectors.columns"),
            {"outline_tolerance_mm": tolerance, "default_outline_tolerance_mm": default_tolerance, "tail_width_tolerance_mm": float(conn["tail_width_tolerance_mm"])},
            special,
        ),
        entry(
            "surface_finish", "order_option", "Surface finish", order["surface_finish"],
            f"The contacts are exposed gold fingers; {fab['surface_finish']} is JLC's flexible-PCB surface finish.",
            (jlc,), {"surface_finish": order["surface_finish"]},
        ),
        entry(
            "finger_width", "review_note", "Gold-finger width",
            (f"ask JLC to hold the {_g(width)} mm contacts within +/-{_g(width_tolerance)} mm, or measure them on delivery"
             if width_exceeds else f"the {_g(width)} mm contacts are within +/-{_g(width_tolerance)} mm at JLC's trace tolerance"),
            f"JLC's trace-width tolerance is +/-{_g(fraction * 100)}% ({_g(round(width * (1 - fraction), 6))}-"
            f"{_g(round(width * (1 + fraction), 6))} mm for {_g(width)} mm contacts); the {rows_part} drawing allows "
            f"{_g(width)} +/-{_g(width_tolerance)} mm.",
            (jlc, "reader_connectors.rows"),
            {"contact_width_mm": width, "trace_width_tolerance_fraction": fraction, "contact_width_tolerance_mm": width_tolerance},
        ),
        entry(
            "trace_widths", "review_note", "Trace widths",
            f"the fan-out traces are {_g(bundle)} mm wide by default (routing.trace_width_mm, at least {_g(minimum_width)} mm) "
            f"and widen to {_g(finger)} mm in the tail, which the stiffener edge flexes",
            f"JLC's minimum trace width and spacing for {_g(weight)} oz copper is {_mils(minimum_width)}/{_mils(minimum_space)} mil "
            f"({_g(minimum_width)}/{_g(minimum_space)} mm), and its trace-width tolerance of +/-{_g(fraction * 100)}% lets a {_g(bundle)} mm "
            f"trace come out at {_g(round(bundle * (1 - fraction), 6))} mm; JLC sets no rule on necking or on the trace width near "
            "bends or stiffener edges.",
            (jlc,),
            {
                "default_trace_width_mm": bundle, "finger_trace_width_mm": finger, "minimum_trace_width_mm": minimum_width,
                "minimum_trace_space_mm": minimum_space, "trace_width_tolerance_fraction": fraction,
            },
        ),
        entry(
            "contact_zone", "review_note", "Contact-zone thickness",
            f"the tail is about {_g(contact_zone)} mm thick at the contacts"
            + (f", within {_g(zone)} +/-{_g(zone_tolerance)} mm at JLC's tolerance" if zone_held else "; measure it on delivery"),
            (f"{_g(fpc)} mm FPC + the {_g(stiffener)} mm {material} stiffener by JLC's rule (thickness with stiffener = FPC "
             "thickness + stiffener thickness)" if two_layer else
             f"{_g(core)} mm PI core + {_g(copper)} mm copper + the {_g(stiffener)} mm {material} stiffener where the coverlay is open, "
             "the stiffener's adhesive not counted")
            + f"; both reader connectors take {_g(zone)} +/-{_g(zone_tolerance)} mm, JLC holds the "
            f"gold-finger area to +/-{_g(finger_tolerance)} mm and chooses the stiffener under the gold fingers to the gold-finger "
            "thickness ordered."
            + (" JLC says the finished thickness is less where an area has no copper or coverlay, as at the contacts (the coverlay "
               "open, the bottom copper empty), so measure it on delivery if it matters." if two_layer else ""),
            (jlc, "reader_connectors.rows", "reader_connectors.columns", gold),
            {
                "contact_zone_thickness_mm": contact_zone, "connector_thickness_mm": zone,
                "connector_thickness_tolerance_mm": zone_tolerance, "gold_finger_thickness_tolerance_mm": finger_tolerance,
            },
        ),
        entry(
            "contact_start", "review_note", "Contact start", f"the contacts start {_g(start)} mm from the tip",
            f"JLC cuts back gold fingers closer than {_g(fab['gold_finger_to_board_edge_mm'])} mm to the board edge, and its "
            f"laser-outline copper-to-edge minimum is {_g(fab['copper_to_board_edge_mm'])} mm.",
            (jlc,),
            {
                "contact_start_from_tip_mm": start, "gold_finger_to_board_edge_mm": float(fab["gold_finger_to_board_edge_mm"]),
                "copper_to_board_edge_mm": float(fab["copper_to_board_edge_mm"]),
            },
        ),
        entry(
            "contact_window", "review_note", "Contact window",
            f"the gang coverlay window leaves {_g(margin)} mm beyond the outer contacts",
            (f"Less than JLC's {_g(expansion)} mm coverlay expansion: the window stops where the R{_g(radius)} mm tip corners begin. "
             if margin < expansion - 1e-12 else f"The full {_g(expansion)} mm coverlay expansion. ")
            + f"The JLC-accepted reference design opened its coverlay {_g(order['reference_contact_window_margin_mm'])} mm beyond each contact.",
            (jlc, "reader_connectors.columns", "reference_design"),
            {
                "contact_window_side_margin_mm": margin, "coverlay_expansion_mm": expansion, "tail_tip_corner_radius_mm": radius,
                "reference_contact_window_margin_mm": float(order["reference_contact_window_margin_mm"]),
            },
        ),
        entry(
            "coverlay_windows", "review_note", "Coverlay windows",
            # engine.layout: a window per electrode, merged into one field window when a bridge between two would be
            # narrower than the rule (the default's 1.0 mm electrodes since the fill 0.5 of 2026-11-06 have their own).
            f"check them on the upload: JLC advises one opening no longer than {_g(window_limit)} mm; each board has a window "
            f"per electrode, or one merged electrode-field window when a coverlay bridge between two would be under "
            f"{_g(bridge)} mm, and one gang window over its contacts (each board's lines in ORDER_NOTES.txt give its "
            "windows and those longer)",
            "JLC's FPC design rules: a longer opening can stretch and deform when the coverlay is laminated, making bonding "
            "difficult or misaligning it. The JLC-accepted reference design's electrode-field windows were up to "
            f"{_g(reference_window)} mm long.",
            (clearance, "reference_design"),
            {
                "coverlay_opening_general_max_length_mm": window_limit, "coverlay_min_bridge_mm": bridge,
                "reference_field_window_length_mm": reference_window,
            },
        ),
    ]


def core_layers(stack: Mapping[str, Any]) -> float:
    """The boards' own FPC layers (core, copper, coverlay and its adhesive) in mm, the stiffener not counted."""

    return math.fsum(float(stack[key]) for key in _FPC_LAYERS)


def _g(value: Any) -> str:
    return f"{float(value):g}"


def _mils(value: Any) -> str:
    """A length in mils (1 mil = 0.0254 mm), as JLC states its trace rules."""

    return f"{round(float(value) / 0.0254, 2):g}"


def _list(values: Any) -> str:
    texts = [_g(value) for value in values]
    return texts[0] if len(texts) == 1 else ", ".join(texts[:-1]) + " and " + texts[-1]


def _half_step(options: Any) -> float:
    """Half the smallest gap between distinct options (unbounded for a single option)."""

    values = sorted({round(float(option), 9) for option in options})
    gaps = [high - low for low, high in zip(values, values[1:])]
    return min(gaps) / 2 if gaps else math.inf


def _thicknesses(values: Any) -> bool:
    return isinstance(values, list) and bool(values) and all(_number(value) and float(value) > 0 for value in values)


def _listed(value: Any, options: Any) -> bool:
    return any(abs(float(value) - float(option)) <= 1e-9 for option in options)


def _number(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except OverflowError:  # an integer beyond the float range
        return False
