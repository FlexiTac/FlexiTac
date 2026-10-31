"""Fit the tactile sensor to a flattened surface: choose and place a design.

The board pair is the engine's ordinary rectangular design
(``tactile-fpc-design/v1``, both tails ``bottom``).  The fit chooses rows,
columns, pitch, electrode widths, routing, role mapping, connector pins and
tail lengths so that the sensor covers as much of the selected surface as
the settings allow, with the smallest margins:

- **Base edge.**  The tails leave the surface across one straight side of
  the chart's outer boundary (the *base edge*, picked by the user or tried
  automatically).  The chart is rotated so the base edge lies on y = 0 with
  the surface above it; the boards' tail-down frame is placed with +Y along
  +y, as seen from outside the part.
- **On-surface rule (user decision).**  With ``containment: board``
  everything above the tail roots (taxel field, Row channel, Row expansion,
  Column fan-out) and the tails up to the base edge lie on the surface; only
  the tails leave it.  The search uses the stack's bounding rectangle from
  the base edge to the top of the field (both boards, the top one mirrored
  as seen from outside), then the winners are generated and their real
  outlines checked exactly.  ``containment: field``, the default from
  masked-field phase P5e on, keeps only the taxel field on the surface
  instead, on the diagonal Row bus (:mod:`surface.fieldfit`, the user's
  routing decisions of 2026-10-21).
- **The selected area alone** (the user's decision of 2026-10-26,
  P5-diagonal-bus.md section 26.16).  What CAD mode generates depends only
  on the area selected: the field follows it (masked fields too, full
  rectangles where they rank) on the surface template.  It has no
  rectangle shape, no rectangle preference and no generic template: those
  are the rectangular mode's (rows, columns and the traces' parameters,
  without CAD); a fit naming them is refused (:data:`CAD_ONLY`).
- **Usable region.**  The chart outline inset by ``edge_margin_mm``
  (default 0: the board edges may reach the surface's edges), minus holes,
  partly covered facets, facets stretched beyond ``strain_limit`` and bends
  tighter than the stack may follow.
- **Search.**  A raster of the usable region (at most ``MAX_CELLS``) gives,
  for every width, the tallest base-anchored rectangle; rows 1..64,
  columns 1..64 (``MAX_COLUMNS``), both role mappings and both routings
  are enumerated with the engine's own plan functions, so the footprint is
  the engine's.  Ranking is deterministic.
"""

from __future__ import annotations

import bisect
import math
from collections import deque
from typing import Any, Mapping, Sequence

from engine import design_mask, generate_design, load_profile
from engine.geometry import point_in_polygon, segment_distance, segments_intersect
from engine.layout import column_plan, masked_row_plan, row_plan

from . import api as api_module
from . import bend
from . import border as border_module
from . import reader as reader_module
from .chart import Chart
from .errors import SurfaceError, finite_number
from .mesh import Mesh, dist2, dot, hypot2, norm, sub

FIT_FORMAT = "tactile-surface-fit/v1"
MAX_ROWS = 64
MAX_COLUMNS = 64  # the surface template's direct one-lane fan-out
# The fit option "template" -> the engine template id (CAD mode fits on "surface" only; "generic" names the template of a
# placement saved from a fit before section 26.16, which the map still maps).
TEMPLATES = {"surface": "surface_matrix_v1", "generic": "generic_matrix_v1"}
MIN_PITCH_MM = 0.6
MAX_PITCH_MM = 10.0
MIN_ELECTRODE_MM = 0.1016
MIN_GAP_MM = 0.25
MAX_CELLS = 160_000
TAIL_MIN_MM = {"surface": 7.5, "generic": 7.0}
# The profiles' limits.maximum_tail_length_mm: 200 mm on the surface template since P5-diagonal-bus.md section 23 (the
# user: a capped field stacks at the fingertip and its tails run down the face, "a longer tail is fine"; 80 before).
TAIL_MAX_MM = {"surface": 200.0, "generic": 80.0}
# The range of tail_extension_mm, the tail beyond the exit (unchanged by the surface's longer tails).
TAIL_EXTENSION_MAX_MM = 72.5
# The part of a tail beyond the exit holds at least the 6.0 mm stiffener and
# its 0.5 mm clearance (both templates' profiles), so the stiffened contact
# zone never lies on the part.
TAIL_REACH_MIN_MM = 6.5


def tails_too_long(template: str) -> str:
    """The rejection reason of a tail past the template's maximum."""

    return f"tails longer than {TAIL_MAX_MM[template]:g} mm"


ROUTINGS = {"default": (0.127, 0.127), "tight": (0.1016, 0.1016)}
STACK_THICKNESS_MM = 0.47  # estimated laminated field (two FPCs, film, laminate)
SINGLE_FPC_MM = 0.11
STATIC_BEND_FACTOR = 10.0  # JLC: 6-10 x thickness for a static bend
PITCH_STEP_MM = 0.01
MAX_AREA_PITCH_RATIO = 1.15  # objective max_area: the pitches searched, min_pitch_mm x 1.15^k
MAX_AREA_TURNED_PITCHES = 4  # ... and in the turned frames, those of the best 4 candidates unturned
# The stack is placed this far inside the usable cells (0.1 um): a side on the
# surface's edge stays inside it after rounding.
EDGE_INSET_MM = 1e-4

ROTATION_STEPS_DEG = (10.0, -10.0, 20.0, -20.0, 30.0, -30.0)
# Rounded outlines: tails may also leave through arcs of the boundary.
# Shorter straight sides are no tail exit (a tail is at least (pins + 1) x 0.5 mm wide).
MIN_SIDE_MM = 3.0
ARC_HALF_LENGTH_MM = 15.0
ARC_WHEN_SIDES_SHORTER_MM = 20.0
AUTO_ARCS = 8
STRAIN_BISECTIONS = 7  # distinct trial disks of the strain limit (limit_strain), at most
STRAIN_TOLERANCE = 0.01  # ... fewer once the radius is known to 1% or a disk stretches 99% of the limit
STRAIN_GROWTH = 1.5  # ... and until one exceeds the limit, at most 1.5 x the radius of the largest within it
STRAIN_SOLVE_VERTICES = 6000  # ... and none once the trials have flattened this many vertices

DEFAULT_OPTIONS: dict = {
    "objective": "fixed_pitch",  # fixed_pitch | max_taxels | max_area
    "pitch_mm": 2.0,
    "min_pitch_mm": 1.0,
    "fill": 0.7,
    "max_rows": MAX_ROWS,
    "max_columns": MAX_COLUMNS,
    "template": "surface",  # fixed: CAD mode builds on the surface template (CAD_ONLY)
    "edge_margin_mm": 0.0,
    "routing": "auto",  # auto | default | tight
    "role_mapping": "auto",  # auto | rows_top | columns_top
    "reader": "none",  # none | auto | 16x16 | 32x16 (FlexiTac, alias flexitac) | 32x32 | 48x48 (surface.reader)
    "shape": "fill",  # fixed: the field follows the selected area, masked fields too (CAD_ONLY)
    # field (the taxel field only, surface.fieldfit; the default) | board (the whole stack above the tail roots on the surface,
    # surface.fill)
    "containment": "field",
    "row_sides": "both",  # containment field: the diagonal Row bus's sides (routing.row_sides), both | left | right
    # containment field: the taxels stack from the fingertip (the end opposite the exit; P5-diagonal-bus.md section 26):
    # within 3 % of the most taxels on the exit the field reaching nearest the fingertip goes first (at a pointed tip it may
    # end in a single taxel), then in the place of the field it displaces that field's own tie of at least as many taxels
    # reaching nearest the fingertip; false keeps coverage first, a field giving its place only to such a tie
    "tip_first": True,
    "placement": "far",  # far | near | center
    "rotation": "auto",  # auto (turn up to 30 degrees against the base side) | none
    "tail_extension_mm": 20.0,
    "strain_limit": 0.003,  # copper's elastic limit (0.2-0.3 %); the research gate
    "proposals": 5,
}
# What CAD mode fits with, no longer a choice (the user's decision of 2026-10-26, P5-diagonal-bus.md section 26.16: "what CAD
# generates depends only on the area selected in CAD"; rectangles are the rectangular mode's, without CAD).  A fit may name
# these options with these values only (older clients): "template" and "shape" stay in the options as they were (echoed
# and saved, fixed); "rectangle_preference_pct" (0 was off) is dropped.  Any other value is refused with the reason
# (E_SURFACE_REQUEST).  The map fits nothing: a saved placement's are taken as fitted (parse_options ``mapping``), exactly
# what a fit accepted before section 26.16 (SAVED_VALUES, SAVED_GENERIC_MAX_COLUMNS); only place.map_options reads shape
# and template, to default the containment of a placement saved without it (board for shape rectangle or the generic
# template).
CAD_ONLY = {"template": "surface", "shape": "fill", "rectangle_preference_pct": 0}
# The values a fit accepted for them before section 26.16 (0024bdb): a placement saved then may hold these, nothing else.
SAVED_VALUES = {"template": ("surface", "generic"), "shape": ("rectangle", "fill"), "rectangle_preference_pct": (0.0, 100.0)}
# ... and on the generic template not with shape fill, containment field or more than this many columns named (that fit
# refused them, :func:`parse_options` ``mapping``; it set them itself when they were not named).
SAVED_GENERIC_MAX_COLUMNS = 32
_CAD_ONLY_REASON = ("CAD mode fits the field to the selected area (masked fields too) on the surface template; rectangular "
                    "fields and the generic template are the rectangular mode's (rows, columns and the traces' parameters, "
                    "without CAD).")


# --------------------------------------------------------------------------
# Route
# --------------------------------------------------------------------------


def fit_route(header: Mapping[str, Any], mesh_bytes: bytes, cache: Any = None) -> dict:
    api_module._keys(header, {"unit", "name", "selection", "base", "options", "border"}, "fit")
    base = header.get("base", "auto")
    # The user's border (surface.border): checked before the mesh is read; its exits are edges of it.
    given = border_module.parse(header["border"]) if "border" in header else None
    if given is not None:
        border_module.check_base(base)
    elif isinstance(base, Mapping) and set(base) == {"border_edge"}:
        raise SurfaceError(border_module.CODE, "base.border_edge picks an edge of the border: give the border as well.")
    mesh = api_module.load_mesh(header, mesh_bytes)
    facets, chart = api_module.selection_chart(mesh, header.get("selection"))
    options = parse_options(header.get("options", {}))
    if given is not None:
        options = border_options(options)
    border = given
    limited = None
    picked = None
    if chart.kind == "curved" and chart.stats["strain_max"] > options["strain_limit"]:
        if isinstance(base, Mapping) and set(base) == {"side"}:
            # {side: n} numbers the sides of the selection the client was shown
            # (/select): pick it there, then find it on the strain-limited disk.
            loop = chart.loops[chart.outer]
            side = choose_bases(base, api_module.boundary_sides(mesh, chart), mesh, chart)[0]
            picked = (side, {frozenset((loop[i], loop[(i + 1) % len(loop)])) for i in side["edges"]})
        whole = chart
        facets, chart, limited = limit_strain(mesh, facets, chart, header.get("selection"), options["strain_limit"])
        if given is not None:
            # The border is drawn on the selection's chart: carried onto the disk's.
            border = border_module.carry(given, whole, chart)
    sides = api_module.boundary_sides(mesh, chart)
    report = None
    if border is not None:
        report = border_module.on_surface(border, chart)
        base_choices = border_module.bases(base, border, chart)
    elif picked is not None:
        base_choices = [side_on_chart(picked[0], picked[1], mesh, chart)]
    else:
        base_choices = choose_bases(base, sides, mesh, chart)
    try:
        # The search reads the border from the obstacles (surface_obstacles); the options echoed stay the user's.
        result = fit_chart(mesh, chart, sides, base_choices, dict(options, border=border) if border is not None else options, cache=cache)
    except SurfaceError as error:
        if border is None or error.code != "E_SURFACE_NO_FIT":
            raise
        raise SurfaceError(error.code, "No taxel fits inside the border on the surface: " + error.message, **error.details) from None
    if border is not None:
        _border_proposals(result, border, report)
    from .place import placement_record

    for proposal in result["proposals"]:
        proposal["placement"] = placement_record(proposal, mesh, header.get("selection"), options, limited)
        if given is not None:
            proposal["placement"]["border"] = border_module.echo(given)
    result["selection"] = api_module.describe_selection(mesh, facets, chart)
    if limited is not None:
        result["selection"]["strain_limited"] = limited
    result["mesh"] = {"sha256": mesh.sha256, "unit": mesh.unit, "facets": mesh.facet_count, "name": mesh.name}
    result["request"] = {"selection": header.get("selection"), "base": header.get("base", "auto"), "options": options}
    if given is not None:
        result["request"]["border"] = border_module.echo(given)
    return result


def border_options(options: dict) -> dict:
    """The options of a fit with a border: field-only containment (the border constrains only the taxels; the routing is
    free), the default; E_SURFACE_BORDER for ``containment: board``."""

    if options["containment"] == "field":
        return options
    raise SurfaceError(
        border_module.CODE,
        "A border constrains the taxels only, with the taxel field on the surface and the routing free: it needs "
        "containment field (not containment board).",
    )


def _border_proposals(result: dict, border: Sequence, report: Mapping[str, Any]) -> None:
    """A fit with a border: each proposal's taxel squares checked against it (the search keeps them inside; a proposal
    that leaves it is dropped), its metrics given the border's area and share on the surface."""

    kept = []
    for proposal in result["proposals"]:
        placement = proposal["placement"]
        side = {"from_uv": placement["base_from_uv"], "to_uv": placement["base_to_uv"], "inward_uv": placement["base_inward_uv"]}
        frame = BaseFrame(side, placement["base_angle_deg"])
        squares = border_module.design_squares(proposal["design"], placement["field_origin_base"])
        if border_module.outside(squares, border, frame):
            reason = "a taxel leaves the border"
            result["rejected"] = _rejected_list({**{item["reason"]: item["count"] for item in result["rejected"]}, reason: 1})
            continue
        proposal["metrics"].update(report)
        proposal["rank"] = len(kept) + 1
        kept.append(proposal)
    if not kept:
        raise SurfaceError("E_SURFACE_NO_FIT", "No taxel fits inside the border on the surface: every field found leaves the border.",
                           rejected=result["rejected"], bases=result["bases"])
    result["proposals"] = kept
    result["obstacles"].pop("border", None)


def limit_strain(mesh: Mesh, facets, chart: Chart, selection: Any, limit: float) -> tuple:
    """The largest geodesic disk of a curved selection that flattens within the strain limit.

    A flat sheet on a doubly curved surface stretches by about K rho^2 / 6
    over a patch of radius rho, so the sensor can only cover a disk around a
    centre.  The centre is the selection's first seed (or the facet nearest
    the selection's area centroid).  Every new trial disk is a curved solve,
    whose cost grows faster than its vertex count, so the radius is searched
    near the answer: regula falsi on (rho^2, strain) between the largest
    disk within the limit and the smallest beyond it (at first a disk of
    radius 0 and the whole selection), with the Illinois step against
    stagnation.  Until a trial disk exceeds the limit, a trial is at most
    STRAIN_GROWTH x the largest disk within it (no trial much larger than
    the answer); a trial outside these bounds halves them instead.  At most
    STRAIN_BISECTIONS distinct disks, fewer once STRAIN_TOLERANCE is reached,
    and no more once the trials have flattened STRAIN_SOLVE_VERTICES vertices.
    A trial radius that gives a disk already tried reuses its chart and does
    not count: on a coarse mesh the disk grows in steps, and a step can lie
    in a narrow band of radii.
    """

    from . import chart as chart_module
    from .select import disk

    centre = None
    ops = selection.get("ops") if isinstance(selection, Mapping) else None
    for op in ops or []:
        if isinstance(op, Mapping) and op.get("op") in ("grow", "disk") and op.get("mode", "add") == "add" and op.get("seed_facet") in facets:
            centre = op["seed_facet"]
            break
    if centre is None:
        total = math.fsum(mesh.areas[f] for f in facets)
        mid = tuple(math.fsum(mesh.centroids[f][k] * mesh.areas[f] for f in facets) / total for k in range(3))
        centre = min(sorted(facets), key=lambda f: norm(sub(mesh.centroids[f], mid)))
    far = max(norm(sub(mesh.vertices[v], mesh.centroids[centre])) for f in facets for v in mesh.facets[f])
    low, high = 0.0, far
    # How far each end's strain is from the limit (a disk of radius 0 does not
    # stretch); None when the disk beyond did not flatten at all.
    low_gap, high_gap = limit, chart.stats["strain_max"] - limit
    whole = True  # no trial disk beyond the limit yet: high is the whole selection
    kept = None  # the end the last trial left in place
    best = None
    solved: dict = {}  # region -> (vertices, chart or None), the distinct disks flattened
    for _ in range(3 * STRAIN_BISECTIONS):  # repeated disks cost no solve; this bounds the loop
        if len(solved) >= STRAIN_BISECTIONS or high - low <= STRAIN_TOLERANCE * high or (
            best is not None and best[3] >= (1 - STRAIN_TOLERANCE) * limit
        ):
            break
        radius = None
        if high_gap is not None:
            x = low * low + (high * high - low * low) * low_gap / (low_gap + high_gap)
            radius = math.sqrt(x)
        # Inside the bracket, half a percent clear of both ends, and while the whole
        # selection bounds it, at most STRAIN_GROWTH x the largest disk within the
        # limit (a trial beyond the limit bounds the cost itself); else halve that range.
        upper = min(high, STRAIN_GROWTH * low) if whole and low > 0 else high
        step = STRAIN_TOLERANCE * high / 2
        if radius is None or not low + step <= radius <= upper - step:
            radius = (low + upper) / 2
        region = disk(mesh, centre, radius, 180.0) & set(facets)
        if len(region) < 2:
            low, low_gap = radius, limit
            continue
        key = tuple(sorted(region))
        if key not in solved:
            vertices = len({v for f in region for v in mesh.facets[f]})
            if best is not None and math.fsum(v for v, _ in solved.values()) + vertices > STRAIN_SOLVE_VERTICES:
                break
            try:
                solved[key] = (vertices, chart_module.build_chart(mesh, region))
            except SurfaceError:
                solved[key] = (vertices, None)
        candidate = solved[key][1]
        if candidate is None:
            # No strain to interpolate from: the next trial halves the bracket.
            high, high_gap, whole, kept = radius, None, False, "low"
            continue
        strain = candidate.stats["strain_max"]
        # Illinois: an end kept twice in a row counts half as far from the limit, so
        # that a strain convex in rho^2 does not leave the other end creeping up to it.
        if strain <= limit:
            best = (region, candidate, radius, strain)
            if kept == "high" and high_gap is not None:
                high_gap /= 2
            low, low_gap, kept = radius, limit - strain, "high"
        else:
            if kept == "low":
                low_gap /= 2
            high, high_gap, whole, kept = radius, strain - limit, False, "low"
    if best is None:
        raise SurfaceError(
            "E_SURFACE_NOT_DEVELOPABLE",
            f"No part of the selection flattens within the strain limit {limit:g} (the full selection reaches "
            f"{chart.stats['strain_max']:.4f}); select a flatter or smaller area, or raise the limit.",
        )
    region, candidate, radius, _ = best
    info = {
        "centre_facet": centre,
        "radius_mm": round(radius, 6),
        "area_mm2": round(candidate.stats["area_mm2"], 6),
        "selected_area_mm2": round(chart.stats["area_mm2"], 6),
        "strain_max": round(candidate.stats["strain_max"], 9),
    }
    # Rebuild from the rounded radius, exactly as the map route will.
    region, candidate = limited_chart(mesh, facets, info)
    return region, candidate, info


def limited_chart(mesh: Mesh, facets, info: Mapping[str, Any]) -> tuple:
    """The chart of a strain-limited disk, from the placement's record (fit and map share it)."""

    from . import chart as chart_module
    from .select import disk

    region = disk(mesh, info["centre_facet"], info["radius_mm"], 180.0) & set(facets)
    if not region:
        raise SurfaceError("E_SURFACE_SELECTION_EMPTY", "The strain-limited disk of the placement is empty.")
    return region, chart_module.build_chart(mesh, region)


def parse_options(raw: Any, mapping: bool = False) -> dict:
    """The fit options, checked, with their defaults.  :data:`CAD_ONLY`: a fit may name ``template``, ``shape`` and
    ``rectangle_preference_pct`` with the values CAD mode fits with only; ``mapping`` (the map, which fits nothing) takes
    them as a placement saved before section 26.16 holds them: exactly what a fit then accepted (:data:`SAVED_VALUES`, and
    on the generic template none of shape fill, containment field or more than :data:`SAVED_GENERIC_MAX_COLUMNS` columns
    named), with that fit's messages."""

    if not isinstance(raw, Mapping):
        raise SurfaceError("E_SURFACE_REQUEST", "options must be an object.")
    raw = reader_module.normalize(raw)
    named: dict = {}  # the removed options a saved placement names (mapping)
    for key, value in CAD_ONLY.items():
        if key not in raw:
            continue
        given = named[key] = raw.pop(key)
        if isinstance(value, str):
            fitted, refusal = isinstance(given, str) and given == value, f"options.{key} must be {value}"
        else:
            fitted = not isinstance(given, bool) and isinstance(given, (int, float)) and given == value
            refusal = f"options.{key} is no longer an option"
        if mapping:
            saved = SAVED_VALUES[key]
            if isinstance(value, str) and (not isinstance(given, str) or given not in saved):
                raise SurfaceError("E_SURFACE_REQUEST", f"options.{key} must be one of {', '.join(saved)}.")
            if not isinstance(value, str):
                finite_number(given, f"options.{key}", *saved)
        elif not fitted:
            raise SurfaceError("E_SURFACE_REQUEST", f"{refusal}: {_CAD_ONLY_REASON}")
    unknown = sorted(set(raw) - set(DEFAULT_OPTIONS))
    if unknown:
        raise SurfaceError("E_SURFACE_REQUEST", f"Unknown fit options: {', '.join(unknown)}.")
    options = dict(DEFAULT_OPTIONS)
    options.update(raw)
    choices = {
        "objective": ("fixed_pitch", "max_taxels", "max_area"),
        "routing": ("auto", "default", "tight"),
        "role_mapping": ("auto", "rows_top", "columns_top"),
        "reader": reader_module.READER_CHOICES,
        "containment": ("board", "field"),
        "row_sides": ("both", "left", "right"),
        "placement": ("far", "near", "center"),
        "rotation": ("auto", "none"),
    }
    for key, allowed in choices.items():
        if not isinstance(options[key], str) or options[key] not in allowed:
            raise SurfaceError("E_SURFACE_REQUEST", f"options.{key} must be one of {', '.join(allowed)}.")
    numbers = {
        "pitch_mm": (MIN_PITCH_MM, MAX_PITCH_MM),
        "min_pitch_mm": (MIN_PITCH_MM, MAX_PITCH_MM),
        "fill": (0.05, 0.95),
        "edge_margin_mm": (0.0, 20.0),
        "tail_extension_mm": (TAIL_REACH_MIN_MM, TAIL_EXTENSION_MAX_MM),
        "strain_limit": (1e-4, 0.2),
    }
    for key, (low, high) in numbers.items():
        options[key] = finite_number(options[key], f"options.{key}", low, high)
    if not isinstance(options["tip_first"], bool):
        raise SurfaceError("E_SURFACE_REQUEST", "options.tip_first must be true or false.")
    for key, high in (("max_rows", MAX_ROWS), ("max_columns", MAX_COLUMNS), ("proposals", 20)):
        value = options[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= high:
            raise SurfaceError("E_SURFACE_REQUEST", f"options.{key} must be an integer within 1..{high}.")
    if mapping and named.get("template") == "generic":
        # What the fit refused on the generic template before section 26.16 (0024bdb): no placement saved then holds it.
        if "max_columns" in raw and options["max_columns"] > SAVED_GENERIC_MAX_COLUMNS:
            raise SurfaceError("E_SURFACE_REQUEST", f"options.max_columns is at most {SAVED_GENERIC_MAX_COLUMNS} on the generic template.")
        if named.get("shape") == "fill":
            raise SurfaceError("E_SURFACE_REQUEST", "options.shape fill needs the surface template: the generic template builds rectangular fields only.")
        if "containment" in raw and options["containment"] == "field":
            raise SurfaceError(
                "E_SURFACE_REQUEST",
                "options.containment field needs the surface template: the generic template keeps the whole stack on the surface.",
            )
    return options


def choose_bases(base: Any, sides: Sequence[Mapping[str, Any]], mesh: Mesh, chart: Chart) -> list:
    """The exits to try: one picked side or arc, or ('auto') the longer straight sides.

    An exit is a set of outer-boundary segments the tails may cross, with a
    direction (the inward normal of its chord).  A straight side is one
    exit; on a rounded outline without long sides, arcs of
    ``2 x ARC_HALF_LENGTH_MM`` around evenly spaced boundary points are tried
    as well.
    """

    if not sides:
        raise SurfaceError("E_SURFACE_BASE_EDGE", "The selection's boundary has no side.")
    if base == "auto":
        ranked = sorted(sides, key=lambda s: (-s["chord_mm"], s["index"]))
        chosen = [s for s in ranked if s["chord_mm"] >= MIN_SIDE_MM][:6]
        if not chosen or chosen[0]["chord_mm"] < ARC_WHEN_SIDES_SHORTER_MM:
            outline = chart.outline()
            perimeter = math.fsum(dist2(outline[i], outline[(i + 1) % len(outline)]) for i in range(len(outline)))
            for k in range(AUTO_ARCS):
                chosen.append(arc_exit(outline, perimeter * k / AUTO_ARCS, ARC_HALF_LENGTH_MM, f"arc{k}"))
        return chosen or ranked[:1]
    if isinstance(base, Mapping) and set(base) == {"arc"}:
        arc = base["arc"]
        if not isinstance(arc, Mapping) or "point_xyz" not in arc or set(arc) - {"point_xyz", "half_length_mm"}:
            raise SurfaceError("E_SURFACE_BASE_EDGE", "base.arc must be {point_xyz: [x, y, z], half_length_mm?}.")
        point = _point(arc["point_xyz"], "base.arc.point_xyz")
        half = finite_number(arc.get("half_length_mm", ARC_HALF_LENGTH_MM), "base.arc.half_length_mm", 1.0, 500.0, code="E_SURFACE_BASE_EDGE")
        return [arc_at_point(mesh, chart, point, half)]
    if isinstance(base, Mapping) and set(base) == {"side"}:
        index = base["side"]
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(sides):
            raise SurfaceError("E_SURFACE_BASE_EDGE", f"base.side must be 0..{len(sides) - 1}.")
        if sides[index]["chord_mm"] < MIN_SIDE_MM:
            raise SurfaceError(
                "E_SURFACE_BASE_EDGE",
                f"Side {index} is {sides[index]['chord_mm']:g} mm long; a tail exit needs at least {MIN_SIDE_MM:g} mm. "
                "Click the rounded edge instead (base.point_xyz gives an arc exit there).",
            )
        return [sides[index]]
    if isinstance(base, Mapping) and set(base) == {"point_xyz"}:
        point = _point(base["point_xyz"], "base.point_xyz")
        best = min(sides, key=lambda s: (_point_segment_3d(point, s["from_xyz"], s["to_xyz"]), s["index"]))
        if best["chord_mm"] < ARC_WHEN_SIDES_SHORTER_MM:
            # A click on a rounded edge: an arc around the nearest boundary point.
            return [arc_at_point(mesh, chart, point, ARC_HALF_LENGTH_MM)]
        return [best]
    raise SurfaceError("E_SURFACE_BASE_EDGE", "base must be 'auto', {'side': n}, {'point_xyz': [x, y, z]} or {'arc': {...}}.")


def side_on_chart(side: Mapping[str, Any], mesh_edges: set, mesh: Mesh, chart: Chart) -> dict:
    """A side of the whole selection on a chart of part of it (the strain-limited disk).

    The exit is the longest run of the chart's outer-boundary segments that
    are mesh edges of the side (``mesh_edges``: frozensets of two vertices);
    it keeps the side's number.  E_SURFACE_BASE_EDGE when the disk keeps less
    than MIN_SIDE_MM of it.
    """

    loop = chart.loops[chart.outer]
    n = len(loop)
    on_side = [frozenset((loop[k], loop[(k + 1) % n])) in mesh_edges for k in range(n)]
    runs = []
    for k in range(n):
        if on_side[k] and not on_side[k - 1]:
            run = [k]
            while on_side[(run[-1] + 1) % n] and len(run) < n:
                run.append((run[-1] + 1) % n)
            runs.append(run)
    if not runs and all(on_side):
        runs = [list(range(n))]
    points = [chart.uv[v] for v in loop]
    lengths = [dist2(points[k], points[(k + 1) % n]) for k in range(n)]
    best = max(runs, key=lambda run: (math.fsum(lengths[k] for k in run), -run[0]), default=None)
    first, last = (points[best[0]], points[(best[-1] + 1) % n]) if best else ((0.0, 0.0), (0.0, 0.0))
    dx, dy = last[0] - first[0], last[1] - first[1]
    chord = hypot2(dx, dy)
    if best is None or chord < MIN_SIDE_MM:
        kept = f"keeps {chord:.3g} mm of it" if best else "does not reach it"
        raise SurfaceError(
            "E_SURFACE_BASE_EDGE",
            f"Side {side['index']} of the selection: the disk that flattens within the strain limit {kept}, and a "
            f"tail exit needs at least {MIN_SIDE_MM:g} mm. Pick another side, a point on the disk's edge, or 'auto'.",
        )
    length = math.fsum(lengths[k] for k in best)
    # Rounded like surface.api.boundary_sides (counter-clockwise outer loop: the inside is on the left).
    return {
        "index": side["index"],
        "from_uv": [api_module._r(first[0]), api_module._r(first[1])],
        "to_uv": [api_module._r(last[0]), api_module._r(last[1])],
        "from_xyz": [api_module._r(c) for c in mesh.vertices[loop[best[0]]]],
        "to_xyz": [api_module._r(c) for c in mesh.vertices[loop[(best[-1] + 1) % n]]],
        "length_mm": api_module._r(length),
        "chord_mm": api_module._r(chord),
        "straight": abs(length - chord) <= 1e-6 * max(length, 1.0) + 1e-9,
        "inward_uv": [api_module._r(-dy / chord, 9), api_module._r(dx / chord, 9)],
        "edges": best,
    }


def _point(value: Any, where: str) -> tuple:
    if not (isinstance(value, list) and len(value) == 3):
        raise SurfaceError("E_SURFACE_BASE_EDGE", f"{where} must be [x, y, z] in mm.")
    return tuple(finite_number(c, f"{where}[{k}]", -1e7, 1e7, code="E_SURFACE_BASE_EDGE") for k, c in enumerate(value))


def arc_exit(outline: Sequence, centre_s: float, half: float, name: str) -> dict:
    """The boundary segments within ``half`` (along the boundary) of the point at arc length ``centre_s``."""

    n = len(outline)
    lengths = [dist2(outline[i], outline[(i + 1) % n]) for i in range(n)]
    perimeter = math.fsum(lengths)
    starts = []
    running = 0.0
    for length in lengths:
        starts.append(running)
        running += length
    chosen = []
    for i in range(n):
        middle = starts[i] + lengths[i] / 2
        gap = abs(middle - centre_s) % perimeter
        if min(gap, perimeter - gap) <= half:
            chosen.append(i)
    if not chosen:
        chosen = [min(range(n), key=lambda i: abs(starts[i] + lengths[i] / 2 - centre_s))]
    # Order the segments along the loop (the arc may wrap past index 0).
    chosen_set = set(chosen)
    first = next((i for i in chosen if (i - 1) % n not in chosen_set), chosen[0])
    ordered = [first]
    while (ordered[-1] + 1) % n in chosen_set and len(ordered) < len(chosen):
        ordered.append((ordered[-1] + 1) % n)
    a, b = outline[ordered[0]], outline[(ordered[-1] + 1) % n]
    dx, dy = b[0] - a[0], b[1] - a[1]
    chord = hypot2(dx, dy)
    inward = (-dy / chord, dx / chord) if chord > 0 else (0.0, 1.0)
    # Rounded like the straight sides (surface.api.boundary_sides): the reply and
    # the placement carry these values, and the map rebuilds the frame from them.
    return {
        "index": name,
        "kind": "arc",
        "from_uv": [round(a[0], 6), round(a[1], 6)],
        "to_uv": [round(b[0], 6), round(b[1], 6)],
        "inward_uv": [round(inward[0], 9), round(inward[1], 9)],
        "chord_mm": round(chord, 6),
        "length_mm": round(math.fsum(lengths[i] for i in ordered), 6),
        "edges": ordered,
    }


def arc_at_point(mesh: Mesh, chart: Chart, point: Sequence[float], half: float) -> dict:
    """An arc exit around the outer-boundary point nearest a 3D point."""

    loop = chart.loops[chart.outer]
    outline = chart.outline()
    n = len(loop)
    best = None
    running = 0.0
    for i in range(n):
        a, b = mesh.vertices[loop[i]], mesh.vertices[loop[(i + 1) % n]]
        ab = sub(b, a)
        length2 = dot(ab, ab)
        t = 0.0 if length2 == 0 else max(0.0, min(1.0, dot(sub(point, a), ab) / length2))
        distance = _point_segment_3d(point, a, b)
        along = running + t * dist2(outline[i], outline[(i + 1) % n])
        if best is None or distance < best[0]:
            best = (distance, along)
        running += dist2(outline[i], outline[(i + 1) % n])
    return arc_exit(outline, best[1], half, "arc")


def _point_segment_3d(p, a, b) -> float:
    ab = sub(b, a)
    length2 = dot(ab, ab)
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, dot(sub(p, a), ab) / length2))
    closest = (a[0] + ab[0] * t, a[1] + ab[1] * t, a[2] + ab[2] * t)
    return norm(sub(p, closest))


# --------------------------------------------------------------------------
# Fit
# --------------------------------------------------------------------------


def fit_chart(mesh: Mesh, chart: Chart, sides: Sequence, bases: Sequence, options: Mapping[str, Any], cache: Any = None) -> dict:
    """The fit's proposals: ``containment: field`` the taxel field alone on the surface (:mod:`surface.fieldfit`), ``board``
    the whole stack above the tail roots (:mod:`surface.fill`: the masked fields merged with the rectangles of
    :func:`search`)."""

    if options.get("containment") == "field":
        from .fieldfit import fit_chart_field

        return fit_chart_field(mesh, chart, sides, bases, options, cache=cache)
    from .fill import fit_chart_fill

    return fit_chart_fill(mesh, chart, sides, bases, options, cache=cache)


def _reasons(rejected: Mapping[str, int]) -> str:
    if not rejected:
        return "nothing could be tried."
    return "; ".join(f"{reason} ({count})" for reason, count in sorted(rejected.items(), key=lambda kv: -kv[1])[:4]) + "."


def _rejected_list(rejected: Mapping[str, int]) -> list:
    return [{"reason": reason, "count": count} for reason, count in sorted(rejected.items(), key=lambda kv: (-kv[1], kv[0]))]


class BaseFrame:
    """Chart (u, v) to the base frame of one base side, optionally rotated.

    Unrotated, the base side lies on y = 0 (from x = 0 to its length) and the
    surface is above it.  ``angle_deg`` turns the board's axes against the
    side (the tails then cross it obliquely); the base side is then the line
    through the origin at ``-angle_deg``.
    """

    def __init__(self, side: Mapping[str, Any], angle_deg: float = 0.0) -> None:
        self.origin = tuple(side["from_uv"])
        self.angle_deg = angle_deg
        inward = side["inward_uv"]
        along = (inward[1], -inward[0])
        end = side["to_uv"]
        self.length = (end[0] - self.origin[0]) * along[0] + (end[1] - self.origin[1]) * along[1]
        c, s_ = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
        # Rotate the frame axes counter-clockwise by the angle (in the chart).
        self.ex = (along[0] * c + inward[0] * s_, along[1] * c + inward[1] * s_)
        self.ey = (-along[0] * s_ + inward[0] * c, -along[1] * s_ + inward[1] * c)
        # The base side in frame coordinates: from (0, 0) along `side_dir` for `length`.
        self.side_dir = (c, -s_)
        self.inward = (s_, c)

    def to_base(self, p: Sequence[float]) -> tuple:
        dx, dy = p[0] - self.origin[0], p[1] - self.origin[1]
        return (dx * self.ex[0] + dy * self.ex[1], dx * self.ey[0] + dy * self.ey[1])

    def to_chart(self, p: Sequence[float]) -> tuple:
        return (
            self.origin[0] + p[0] * self.ex[0] + p[1] * self.ey[0],
            self.origin[1] + p[0] * self.ex[1] + p[1] * self.ey[1],
        )

    def base_y(self, x: float) -> Any:
        """y of the base side above x (frame coordinates), or None outside the side."""

        dx, dy = self.side_dir
        if abs(dx) < 1e-12:
            return None
        t = x / dx
        if t < -1e-9 or t > self.length + 1e-9:
            return None
        return t * dy

    def height_above_base(self, p: Sequence[float]) -> float:
        """Signed distance of a frame point from the base line (positive on the surface side)."""

        return p[0] * self.inward[0] + p[1] * self.inward[1]

    def along_base(self, p: Sequence[float]) -> float:
        return p[0] * self.side_dir[0] + p[1] * self.side_dir[1]


# --------------------------------------------------------------------------
# Obstacles: what the sensor must not cover
# --------------------------------------------------------------------------


def surface_obstacles(mesh: Mesh, chart: Chart, options: Mapping[str, Any]) -> dict:
    """Chart polygons and segments the boards must avoid."""

    triangles = []
    # Facets stretched beyond the strain limit by the flattening.
    limit = options["strain_limit"]
    for facet, (s1, s2) in chart.strain.items():
        if max(abs(s1 - 1), abs(s2 - 1)) > limit:
            triangles.append([chart.uv[v] for v in mesh.facets[facet]])
    # Parts of facets covered by another shell (walls where two parts touch).
    covered = []
    for facet, polygons in mesh.covered.items():
        if facet not in chart.strain:
            continue
        for polygon in polygons:
            mapped = [_facet_point_to_uv(mesh, chart, facet, p) for p in polygon]
            if all(m is not None for m in mapped):
                covered.append(mapped)
    holes = chart.holes()
    bends = bend_segments(mesh, chart, STATIC_BEND_FACTOR * STACK_THICKNESS_MM)
    found = {"strained": triangles, "covered": covered, "holes": holes, "bends": bends}
    if options.get("border") is not None:
        # The user's border (surface.border, fit_route): not an obstacle, where the taxels may lie (surface.fill.FreeSpace).
        found["border"] = list(options["border"])
    return found


def _facet_point_to_uv(mesh: Mesh, chart: Chart, facet: int, point) -> Any:
    a, b, c = (mesh.vertices[v] for v in mesh.facets[facet])
    ua, ub, uc = (chart.uv[v] for v in mesh.facets[facet])
    v0, v1, v2 = sub(b, a), sub(c, a), sub(point, a)
    d00, d01, d11 = dot(v0, v0), dot(v0, v1), dot(v1, v1)
    d20, d21 = dot(v2, v0), dot(v2, v1)
    denominator = d00 * d11 - d01 * d01
    if denominator == 0:
        return None
    l1 = (d11 * d20 - d01 * d21) / denominator
    l2 = (d00 * d21 - d01 * d20) / denominator
    l0 = 1 - l1 - l2
    return (ua[0] * l0 + ub[0] * l1 + uc[0] * l2, ua[1] * l0 + ub[1] * l1 + uc[1] * l2)


def bend_segments(mesh: Mesh, chart: Chart, min_radius_mm: float) -> list:
    """Interior chart edges where the surface bends tighter than ``min_radius_mm``.

    The radius at an edge comes from :func:`surface.bend.edge_radius`: the
    strip width over the angle for a smooth bend, 0 for a crease that a sheet
    of this radius cannot follow.
    """

    segments = []
    in_chart = set(chart.facets)
    for f in chart.facets:
        for g in mesh.neighbors[f]:
            if g <= f or g not in in_chart:
                continue
            radius = bend.edge_radius(mesh, f, g, min_radius_mm)
            if radius < min_radius_mm:
                a, b = bend.edge_geometry(mesh, f, g)[3]
                segments.append((chart.uv[a], chart.uv[b], radius))
    return segments


# --------------------------------------------------------------------------
# Raster of the usable region in the base frame
# --------------------------------------------------------------------------


class ExitOutline:
    """The chart's outer boundary in the base frame, and the segments the tails may cross."""

    def __init__(self, outline: Sequence, exit_edges: Sequence[int]) -> None:
        self.outline = list(outline)
        # Segment i runs from point i to point i + 1.
        self.exit_edges = frozenset(exit_edges)
        self._vertex_xs: Any = None  # the exit vertices' x, sorted (lowest_exit_y)
        n = len(self.outline)
        xs = [p[0] for p in self.outline]
        self.x0, self.x1 = min(xs), max(xs)
        # Buckets over x, so exit_y looks at a few segments only.
        self._count = max(1, min(n, 4096))
        self._width = max((self.x1 - self.x0) / self._count, 1e-9)
        self._buckets: list = [[] for _ in range(self._count)]
        for i in range(n):
            (ax, _), (bx, _) = self.outline[i], self.outline[(i + 1) % n]
            if ax == bx:
                continue
            for k in range(self._bucket(min(ax, bx)), self._bucket(max(ax, bx)) + 1):
                self._buckets[k].append(i)

    def _bucket(self, x: float) -> int:
        return min(self._count - 1, max(0, int((x - self.x0) / self._width)))

    def exit_y(self, x: float) -> Any:
        """y where the vertical line at x first meets the outer boundary from below, if that is an exit segment."""

        if x < self.x0 or x > self.x1:
            return None
        lowest = None
        outline = self.outline
        n = len(outline)
        for i in self._buckets[self._bucket(x)]:
            (ax, ay), (bx, by) = outline[i], outline[(i + 1) % n]
            if (ax <= x < bx) or (bx <= x < ax):
                y = ay + (x - ax) * (by - ay) / (bx - ax)
                if lowest is None or (y, i) < lowest:
                    lowest = (y, i)
        if lowest is None or lowest[1] not in self.exit_edges:
            return None
        return lowest[0]

    def lowest_segment(self, x: float) -> Any:
        """``(y, segment)`` where the vertical line at x first meets the outer boundary from below, exit or not, or None."""

        if x < self.x0 or x > self.x1:
            return None
        lowest = None
        outline = self.outline
        n = len(outline)
        for i in self._buckets[self._bucket(x)]:
            (ax, ay), (bx, by) = outline[i], outline[(i + 1) % n]
            if (ax <= x < bx) or (bx <= x < ax):
                y = ay + (x - ax) * (by - ay) / (bx - ax)
                if lowest is None or (y, i) < lowest:
                    lowest = (y, i)
        return lowest

    def lowest_exit_y(self, x0: float, x1: float) -> Any:
        """The lowest exit y over x0..x1 (a tail's width), or None where the exit is missed.

        exit_y is linear between the exit segments' vertices, so it is read at
        both ends and at every vertex in between (just left of a vertex too,
        for a step): an arc bulges below the chord of the tail's two corners.
        """

        if self._vertex_xs is None:
            n = len(self.outline)
            self._vertex_xs = sorted({self.outline[k][0] for i in self.exit_edges if 0 <= i < n for k in (i, (i + 1) % n)})
        xs = [x0 + 1e-9, x1 - 1e-9]
        for x in self._vertex_xs[bisect.bisect_right(self._vertex_xs, x0 + 1e-9) : bisect.bisect_left(self._vertex_xs, x1 - 1e-9)]:
            xs += [x - 1e-9, x]
        lowest = None
        for x in xs:
            y = self.exit_y(x)
            if y is None:
                return None
            lowest = y if lowest is None else min(lowest, y)
        return lowest


class UsableRaster:
    """Cells of the usable region (base frame), and the tallest base-anchored rectangles."""

    def __init__(self, chart: Chart, frame: BaseFrame, obstacles: Mapping[str, Any], margin: float, exit_edges: Sequence[int]) -> None:
        self.frame = frame
        self.margin = margin
        outline = [frame.to_base(p) for p in chart.outline()]
        self.exits = ExitOutline(outline, exit_edges)
        self.outline = outline
        # The outer-loop segments the tails may cross (segment i: point i to point i + 1).
        self.exit_edges = self.exits.exit_edges
        xs = [p[0] for p in outline]
        ys = [p[1] for p in outline]
        self.x0, self.x1 = min(xs), max(xs)
        self.y0, self.y1 = min(ys), max(ys)
        area = max((self.x1 - self.x0) * (self.y1 - self.y0), 1e-9)
        self.h = max(0.02, math.sqrt(area / MAX_CELLS))
        # Only whole cells: the raster never reaches past the outline's bounding box.
        self.nx = max(0, int(math.floor((self.x1 - self.x0) / self.h + 1e-9)))
        self.ny = max(0, int(math.floor((self.y1 - self.y0) / self.h + 1e-9)))
        polygons = [outline] + [[frame.to_base(p) for p in hole] for hole in obstacles["holes"]]
        # A cell is inside when its bottom and top edges both lie inside the polygon.
        # The outermost lines sit a little inside, clear of rounding noise on the base side.
        eps = max(1e-6, self.h * 1e-3)
        lines = _scanlines(polygons, [self.y0 + j * self.h + (eps if j == 0 else 0.0) - (eps if j == self.ny else 0.0) for j in range(self.ny + 1)])
        inside = [[False] * self.nx for _ in range(self.ny)]
        for j in range(self.ny):
            row = inside[j]
            lower, upper = lines[j], lines[j + 1]
            for i in range(self.nx):
                left = self.x0 + i * self.h
                right = left + self.h
                if _covered(lower, left, right) and _covered(upper, left, right):
                    row[i] = True
        blocked = [[not cell for cell in row] for row in inside]
        for key in ("strained", "covered"):
            for polygon in obstacles[key]:
                self._block_polygon([frame.to_base(p) for p in polygon], blocked)
        for a, b, _ in obstacles["bends"]:
            self._block_segment(frame.to_base(a), frame.to_base(b), blocked)
        self._band = 0
        if margin > 0:
            # Clearance: the cell's centre at least margin + half a cell diagonal from
            # every blocked cell's centre, except in the band above the exit where the
            # tails leave (see _columns).
            distance = _distance_transform(blocked, self.h)
            need = margin + self.h * 0.7072
            self.free = [[not blocked[j][i] and distance[j][i] >= need for i in range(self.nx)] for j in range(self.ny)]
            self._band = int(math.ceil(need / self.h)) + 1
        else:
            self.free = [[not cell for cell in row] for row in blocked]
        self._blocked = blocked
        self._columns()

    def exit_y(self, x: float) -> Any:
        return self.exits.exit_y(x)

    def _block_polygon(self, polygon, blocked) -> None:
        """Block every cell the polygon touches (its extent within each row of cells)."""

        n = len(polygon)
        if n == 0:
            return
        for j in range(self.ny):
            low, high = self.y0 + j * self.h, self.y0 + (j + 1) * self.h
            xs = [p[0] for p in polygon if low <= p[1] <= high]
            for k in range(n):
                (ax, ay), (bx, by) = polygon[k - 1], polygon[k]
                for y in (low, high):
                    if (ay - y) * (by - y) < 0:
                        xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
            if xs:
                self._block_run(j, min(xs), max(xs), blocked)

    def _block_segment(self, a, b, blocked) -> None:
        """Block every cell the segment passes through (its x extent within each row of cells)."""

        (ax, ay), (bx, by) = a, b
        h, y0 = self.h, self.y0
        j0 = max(0, int(math.floor((min(ay, by) - y0) / h)))
        j1 = min(self.ny - 1, int(math.floor((max(ay, by) - y0) / h)))
        # Many bend lines (a finely exported blend) cross every raster: the row
        # loop stays lean (the same cells as clamping each row's two borders).
        dx, dy = bx - ax, by - ay
        x0, last, floor = self.x0, self.nx - 1, math.floor
        upper = ax if dy == 0 else ax + dx * min(max((y0 + j0 * h - ay) / dy, 0.0), 1.0)
        for j in range(j0, j1 + 1):
            if dy == 0:
                xa, xb = ax, bx
            else:
                xa, xb = upper, ax + dx * min(max((y0 + (j + 1) * h - ay) / dy, 0.0), 1.0)
                upper = xb
            if xb < xa:
                xa, xb = xb, xa
            i0 = max(0, int(floor((xa - x0) / h)))
            i1 = min(last, int(floor((xb - x0) / h)))
            if i1 >= i0:
                blocked[j][i0 : i1 + 1] = [True] * (i1 - i0 + 1)

    def _block_run(self, j: int, left: float, right: float, blocked) -> None:
        i0 = max(0, int(math.floor((left - self.x0) / self.h)))
        i1 = min(self.nx - 1, int(math.floor((right - self.x0) / self.h)))
        if i1 >= i0:
            blocked[j][i0 : i1 + 1] = [True] * (i1 - i0 + 1)

    def _columns(self) -> None:
        """Per column of cells: the first whole cell above the base side and the free run from there."""

        self.bottom = []
        self.up = []
        self._exit_pairs = []
        for i in range(self.nx):
            left = self.x0 + i * self.h
            ys = [self.exit_y(left + 1e-9), self.exit_y(left + self.h - 1e-9)]
            self._exit_pairs.append(ys)
            if any(y is None for y in ys):
                self.bottom.append(None)
                self.up.append(0)
                continue
            start = max(0, int(math.ceil((max(ys) - self.y0) / self.h - 1e-9)))
            # Near the exit the tails cross the margin band: those cells count as free.
            for j in range(start, min(start + self._band, self.ny)):
                if not self._blocked[j][i]:
                    self.free[j][i] = True
            run = 0
            while start + run < self.ny and self.free[start + run][i]:
                run += 1
            self.bottom.append(start)
            self.up.append(run)
        self._best: dict = {}

    def tallest(self, width_mm: float) -> tuple:
        """The tallest base-anchored rectangle of this width.

        Returns ``(height_mm, left_x_mm, slack_cells, bottom_y_mm, lowest_base_y_mm)``.
        Every column under the rectangle crosses the base side; the rectangle
        starts at the highest of their first whole cells and ends at the lowest
        top of their free runs.  Among equally tall positions the one centred
        in the widest run wins.
        """

        cells = max(1, int(math.ceil(width_mm / self.h - 1e-9)))
        if cells > self.nx:
            return (0.0, 0.0, 0, 0.0, 0.0)
        cached = self._best.get(cells)
        if cached is not None:
            return cached
        # Sliding windows: the highest bottom and the lowest top (monotonic deques).
        heights = []
        highest_bottom: deque = deque()
        lowest_top: deque = deque()
        missing = 0
        for i in range(self.nx):
            bottom_i = self.bottom[i]
            if bottom_i is None:
                missing += 1
                b_value, t_value = math.inf, -math.inf
            else:
                b_value, t_value = bottom_i, bottom_i + self.up[i]
            while highest_bottom and highest_bottom[-1][0] <= b_value:
                highest_bottom.pop()
            highest_bottom.append((b_value, i))
            while lowest_top and lowest_top[-1][0] >= t_value:
                lowest_top.pop()
            lowest_top.append((t_value, i))
            leaving = i - cells
            if leaving >= 0 and self.bottom[leaving] is None:
                missing -= 1
            start = i - cells + 1
            while highest_bottom[0][1] < start:
                highest_bottom.popleft()
            while lowest_top[0][1] < start:
                lowest_top.popleft()
            if start < 0:
                continue
            if missing:
                heights.append((-1, 0))
            else:
                bottom = highest_bottom[0][0]
                heights.append((lowest_top[0][0] - bottom, bottom))
        best = max((h for h, _ in heights), default=-1)
        if best <= 0:
            result = (0.0, 0.0, 0, 0.0, 0.0)
        else:
            ends = [k for k, (h, _) in enumerate(heights) if h == best]
            runs = []
            first = previous = ends[0]
            for k in ends[1:] + [None]:
                if k is not None and k == previous + 1:
                    previous = k
                    continue
                runs.append((first, previous))
                if k is not None:
                    first = previous = k
            lo, hi = max(runs, key=lambda r: (r[1] - r[0], -r[0]))
            k = (lo + hi) // 2
            left_cell = k
            bottom_cell = heights[k][1]
            window = range(left_cell, left_cell + cells)
            lowest_base = min(min(self._exit_pairs[i]) for i in window)
            result = (best * self.h, self.x0 + left_cell * self.h, hi - lo, self.y0 + bottom_cell * self.h, lowest_base)
        self._best[cells] = result
        return result


def _covered(intervals: Sequence, left: float, right: float) -> bool:
    for start, end in intervals:
        if start <= left + 1e-9 and right - 1e-9 <= end:
            return True
    return False


def _scanline(polygons: Sequence, y: float) -> list:
    """Intervals inside the polygons (even-odd) on the horizontal line y."""

    return _scanlines(polygons, [y])[0]


def _scanlines(polygons: Sequence, ys: Sequence[float]) -> list:
    """:func:`_scanline` on each of the increasing lines ``ys``.

    An edge table: each edge is listed on the lines it spans only, so a fine
    outline (thousands of segments) costs its crossings, not segments x lines.
    """

    spans: list = [[] for _ in ys]
    for polygon in polygons:
        n = len(polygon)
        for k in range(n):
            (x0, y0), (x1, y1) = polygon[k - 1], polygon[k]
            if y0 == y1:
                continue
            # The lines with min(y0, y1) <= y < max(y0, y1).
            for j in range(bisect.bisect_left(ys, min(y0, y1)), bisect.bisect_left(ys, max(y0, y1))):
                spans[j].append((x0, y0, x1, y1))
    result = []
    for y, edges in zip(ys, spans):
        crossings = sorted(x0 + (y - y0) * (x1 - x0) / (y1 - y0) for x0, y0, x1, y1 in edges)
        result.append([(crossings[k], crossings[k + 1]) for k in range(0, len(crossings) - 1, 2)])
    return result


def _distance_transform(blocked: Sequence[Sequence[bool]], h: float) -> list:
    """Euclidean distance (mm) from each cell centre to the nearest blocked cell centre.

    Felzenszwalb-Huttenlocher, two 1D passes; cells beyond the raster count as
    blocked, so the raster border is a boundary too.
    """

    ny = len(blocked)
    nx = len(blocked[0]) if ny else 0
    inf = float(nx * nx + ny * ny + 4)
    # Pass 1: along x, distance to the nearest blocked cell in the row (border blocked).
    column_pass = []
    for j in range(ny):
        row = blocked[j]
        f = [0.0 if row[i] else inf for i in range(nx)]
        # The raster border is blocked: one cell beyond each end.
        f = [0.0] + f + [0.0]
        column_pass.append(_dt1d(f)[1:-1])
    # Pass 2: along y, with the border blocked.
    result = [[0.0] * nx for _ in range(ny)]
    for i in range(nx):
        f = [0.0] + [column_pass[j][i] for j in range(ny)] + [0.0]
        d = _dt1d(f)[1:-1]
        for j in range(ny):
            result[j][i] = math.sqrt(d[j]) * h
    return result


def _dt1d(f: Sequence[float]) -> list:
    n = len(f)
    d = [0.0] * n
    v = [0] * n
    z = [0.0] * (n + 1)
    k = 0
    v[0] = 0
    z[0] = -math.inf
    z[1] = math.inf
    for q in range(1, n):
        while True:
            p = v[k]
            s = ((f[q] + q * q) - (f[p] + p * p)) / (2 * q - 2 * p)
            if s <= z[k]:
                k -= 1
                if k < 0:
                    k = 0
                    v[0] = q
                    z[0] = -math.inf
                    z[1] = math.inf
                    break
                continue
            k += 1
            v[k] = q
            z[k] = s
            z[k + 1] = math.inf
            break
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        p = v[k]
        d[q] = (q - p) * (q - p) + f[p]
    return d


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------


def design_for(rows: int, columns: int, pitch_x: float, pitch_y: float, options: Mapping[str, Any], role: str, routing: str,
               tails: tuple = (12.0, 7.0), mask: Any = None) -> dict:
    """An engine design for the candidate (tails ``bottom``); ``mask`` is its ``matrix.mask`` (net indices), if any."""

    fill = options["fill"]
    width_x = _electrode(pitch_x, fill)
    width_y = _electrode(pitch_y, fill)
    trace_width, trace_space = ROUTINGS[routing]
    design = {
        "template_id": TEMPLATES[options["template"]],
        "project_name": f"Surface {rows}x{columns}",
        "matrix": {
            "rows": rows, "columns": columns, "pitch_x_mm": pitch_x, "pitch_y_mm": pitch_y,
            "taxel_width_mm": width_x, "taxel_height_mm": width_y,
        },
        "tail": {"top_length_mm": tails[0], "bottom_length_mm": tails[1], "row_side": "bottom", "column_side": "bottom"},
        "role_mapping": {"top": "rows", "bottom": "columns"} if role == "rows_top" else {"top": "columns", "bottom": "rows"},
        "routing": {"trace_width_mm": trace_width, "trace_space_mm": trace_space},
        "connector": connector_for(rows, columns, options["reader"]),
    }
    if mask is not None:
        design["matrix"]["mask"] = [[int(first), int(last)] for first, last in mask]
    return design


def connector_for(rows: int, columns: int, mode: str) -> dict:
    """The design's connector pins for a reader option (surface.reader; ``channels``, ``flexitac`` as before)."""

    mode = reader_module.READER_ALIASES.get(mode, reader_module.LEGACY_CONNECTOR.get(mode, mode))
    return reader_module.connector(rows, columns, mode)


def _electrode(pitch: float, fill: float) -> float:
    width = round(pitch * fill, 3)
    width = min(width, round(pitch - MIN_GAP_MM, 4))
    return max(width, MIN_ELECTRODE_MM)


_EXTENT_CACHE: dict = {}
_EXTENT_CACHE_SIZE = 50_000


def cached_extent(rows, columns, pitch_x, pitch_y, options, role, routing, profile) -> dict:
    """``stack_extent`` of a candidate, cached: the same stacks recur for every base side and angle."""

    key = (rows, columns, pitch_x, pitch_y, options["fill"], options["reader"], options["template"], role, routing)
    found = _EXTENT_CACHE.get(key)
    if found is None:
        if len(_EXTENT_CACHE) >= _EXTENT_CACHE_SIZE:
            _EXTENT_CACHE.clear()
        found = stack_extent(design_for(rows, columns, pitch_x, pitch_y, options, role, routing), profile)
        _EXTENT_CACHE[key] = found
    return found


def stack_extent(design: Mapping[str, Any], profile: Mapping[str, Any]) -> dict:
    """Extents of both boards around the field, as seen from outside (field origin at 0, 0).

    The engine's plan functions give each board in its canonical frame
    (copper side up, tail down); the physical top board is seen from its back
    from outside, i.e. mirrored across the field's vertical centre line.
    Returns the union's x range and top, the depth of each tail root below the
    field, and the tails' x ranges.
    """

    # A masked field (surface.fill) has its straight Row channel with the lane taper; the Column plan's
    # extents are the bounding field's.
    rp = (row_plan if design_mask(design) is None else masked_row_plan)(design, profile)
    cp = column_plan(design, profile)
    role_top = design["role_mapping"]["top"]
    ax, ay, aw, ah = rp["active"]
    bx0, by0, bx1, by1 = rp["body"]
    row_boxes = [
        (bx0 - ax, by0 - ay, bx1 - ax, by1 - ay),
        (rp["tail_x"] - ax, -ay, rp["tail_x"] + rp["tail_width"] - ax, -ay),
    ]
    cax, cay, _, _ = cp["active"]
    cbx0, cby0, cbx1, cby1 = cp["body"]
    envelope = cp["envelope"]
    channels = cp["channels"]
    hull_left = min(cp["tail_x"], cp["contact_x"][0] - envelope, cp["decks"][0] - envelope, cp["centers"][0] - envelope)
    hull_right = max(
        cp["tail_x"] + cp["tail_width"], cp["contact_x"][channels - 1] + envelope, cp["decks"][-1] + envelope, cp["centers"][-1] + envelope
    )
    column_boxes = [
        (cbx0 - cax, cby0 - cay, cbx1 - cax, cby1 - cay),
        (hull_left - cax, cp["tail_top"] - cay, hull_right - cax, cby0 - cay),
    ]

    def outside(box, mirrored: bool) -> tuple:
        x0, y0, x1, y1 = box
        return (aw - x1, y0, aw - x0, y1) if mirrored else box

    boxes = [outside(b, role_top == "rows") for b in row_boxes] + [outside(b, role_top == "columns") for b in column_boxes]
    row_tail = outside((rp["tail_x"] - ax, 0, rp["tail_x"] + rp["tail_width"] - ax, 0), role_top == "rows")
    column_tail = outside((cp["tail_x"] - cax, 0, cp["tail_x"] + cp["tail_width"] - cax, 0), role_top == "columns")
    boxes += [row_tail, column_tail]
    x_min = min(b[0] for b in boxes)
    x_max = max(b[2] for b in boxes)
    row_root = ay
    column_root = cay - cp["tail_top"]
    return {
        "x_min": x_min,
        "x_max": x_max,
        "width": x_max - x_min,
        "top": max(b[3] for b in boxes),
        "row_root": row_root,
        "column_root": column_root,
        "root": max(row_root, column_root),
        "field": (aw, ah),
        "row_tail_x": (row_tail[0], row_tail[2]),
        "column_tail_x": (column_tail[0], column_tail[2]),
    }


_PROFILE_CACHE: dict = {}


def load_profile_cached(template: str = "surface") -> Any:
    """The locked profile of a fit template (read once; the plans only read it)."""

    if template not in _PROFILE_CACHE:
        _PROFILE_CACHE[template] = load_profile(TEMPLATES[template])
    return _PROFILE_CACHE[template]


def search(region: UsableRaster, options: Mapping[str, Any], profile: Mapping[str, Any], rejected: dict, pitches: Any = None) -> list:
    """Candidates for one base side, best first (``rank`` keys are comparable across sides).

    For a given pitch the footprint grows with rows and with columns, so the
    largest column count that fits never increases with the row count: a
    staircase walk finds, for every row count, its largest column count with
    O(rows + columns) evaluations per role mapping and routing.  For
    ``max_area`` the walk runs at every pitch of a geometric grid (or at
    ``pitches``): the largest field has fewer lines at a larger pitch, as the
    routing per line weighs less.
    """

    roles = ["rows_top", "columns_top"] if options["role_mapping"] == "auto" else [options["role_mapping"]]
    routings = ["default", "tight"] if options["routing"] == "auto" else [options["routing"]]
    pitch = round(options["pitch_mm"], 3) if options["objective"] == "fixed_pitch" else round(options["min_pitch_mm"], 3)
    area = options["objective"] == "max_area"
    if pitches is None:
        pitches = max_area_pitches(pitch) if area else [pitch]
    found = []
    for grid_pitch in pitches:
        for role in roles:
            for routing in routings:
                columns = options["max_columns"]
                if area:
                    # Skip the counts whose pitch alone spans more than the region.
                    columns = min(columns, int(math.floor((region.x1 - region.x0) / grid_pitch + 1e-9)) + 1)
                for rows in range(1, options["max_rows"] + 1):
                    if area and (rows - 1) * grid_pitch > region.y1 - region.y0:
                        break
                    item = None
                    while columns >= 1:
                        item = evaluate(region, rows, columns, grid_pitch, grid_pitch, options, role, routing, profile, rejected)
                        if item is not None:
                            break
                        columns -= 1
                    if columns < 1 or item is None:
                        break
                    item["grid_pitch"] = grid_pitch
                    found.append(item)
    if area:
        # Each shape once, at the largest grid pitch it fits (smaller ones only grow to it).
        largest: dict = {}
        for item in found:
            key = (item["rows"], item["columns"], item["role"], item["routing"])
            if key not in largest or item["pitch_x"] > largest[key]["pitch_x"]:
                largest[key] = item
        found = list(largest.values())
    found.sort(key=lambda c: c["rank"])
    if options["objective"] == "fixed_pitch":
        return found
    # Larger pitches for the best counts (the footprint grows with pitch).  The
    # candidate at the smallest pitch stays behind its grown version, in case
    # the grown one, which touches the bound, does not realize.
    keep = max(options["proposals"] * 3, 12)
    grown = []
    for item in found[:keep]:
        better = _grow_pitch(region, item["rows"], item["columns"], item["pitch_x"], options, item["role"], item["routing"], profile, rejected)
        if better is not None:
            better["grid_pitch"] = item["grid_pitch"]
            grown.append(better)
        grown.append(item)
    grown.sort(key=lambda c: c["rank"])
    return grown


def max_area_pitches(low: float) -> list:
    """The pitches of the max_area search: ``low`` x MAX_AREA_PITCH_RATIO^k up to MAX_PITCH_MM."""

    pitches = [low]
    while pitches[-1] * MAX_AREA_PITCH_RATIO < MAX_PITCH_MM:
        pitches.append(round(pitches[-1] * MAX_AREA_PITCH_RATIO, 2))
    return pitches


def _grow_pitch(region, rows, columns, p_low, options, role, routing, profile, rejected) -> Any:
    """The largest isotropic pitch (0.01 mm steps) at which the candidate still fits."""

    low, high = p_low, MAX_PITCH_MM
    best = None
    for _ in range(12):
        if high - low <= PITCH_STEP_MM:
            break
        middle = round((low + high) / 2, 2)
        item = evaluate(region, rows, columns, middle, middle, options, role, routing, profile, {})
        if item is not None:
            best, low = item, middle
        else:
            high = middle
    return best


def evaluate(region: UsableRaster, rows, columns, pitch_x, pitch_y, options, role, routing, profile, rejected) -> Any:
    reason = reader_module.rejection(rows, columns, options["reader"])
    if reason is not None:
        rejected[reason] = rejected.get(reason, 0) + 1
        return None
    width_x = _electrode(pitch_x, options["fill"])
    width_y = _electrode(pitch_y, options["fill"])
    if width_x > pitch_x - MIN_GAP_MM + 1e-9 or width_y > pitch_y - MIN_GAP_MM + 1e-9:
        rejected["pitch too small for the electrode gap"] = rejected.get("pitch too small for the electrode gap", 0) + 1
        return None
    extent = cached_extent(rows, columns, pitch_x, pitch_y, options, role, routing, profile)
    height_needed = extent["root"] + extent["top"]
    # The stack keeps EDGE_INSET_MM inside the whole cells, so a board side on the
    # surface's edge never ends up outside it by rounding.
    tallest, left, slack, bottom, lowest_base = region.tallest(extent["width"] + 2 * EDGE_INSET_MM)
    if tallest + 1e-9 < height_needed + EDGE_INSET_MM:
        rejected["does not fit the surface"] = rejected.get("does not fit the surface", 0) + 1
        return None
    # Place the field: tail roots at least at the rectangle's bottom; 'far' pushes it up.
    lowest = bottom + extent["root"]
    highest = bottom + tallest - extent["top"] - EDGE_INSET_MM
    tail_cap = TAIL_MAX_MM[options["template"]] - options["tail_extension_mm"]
    # The tail on the surface runs from its root down to the base side.
    highest = min(highest, lowest_base + tail_cap + min(extent["row_root"], extent["column_root"]))
    if highest < lowest - 1e-9:
        reason = tails_too_long(options["template"])
        rejected[reason] = rejected.get(reason, 0) + 1
        return None
    if options["placement"] == "near":
        field_y = lowest
    elif options["placement"] == "center":
        field_y = (lowest + highest) / 2
    else:
        field_y = highest
    field_x = left + EDGE_INSET_MM - extent["x_min"]
    taxels = rows * columns
    aw, ah = extent["field"]
    min_pitch = min(pitch_x, pitch_y)
    objective = options["objective"]
    if objective == "max_area":
        primary = -(aw * ah)
    else:
        primary = -taxels
    rank = (
        primary,
        -min_pitch,
        abs(pitch_x - pitch_y),
        abs(region.frame.angle_deg),
        0 if routing == "default" else 1,
        0 if role == "rows_top" else 1,
        -slack,
        rows,
        columns,
    )
    return {
        "rows": rows,
        "columns": columns,
        "pitch_x": pitch_x,
        "pitch_y": pitch_y,
        "role": role,
        "routing": routing,
        "extent": extent,
        "field_origin": (field_x, field_y),
        "rank": rank,
        "taxels": taxels,
        "angle_deg": region.frame.angle_deg,
    }


# --------------------------------------------------------------------------
# Realize: generate the design and check the real outlines
# --------------------------------------------------------------------------


def realize(candidate: Mapping[str, Any], chart: Chart, obstacles: Mapping[str, Any], options: Mapping[str, Any], profile,
            cache, rejected: dict) -> Any:
    extent = candidate["extent"]
    field_x, field_y = candidate["field_origin"]
    extension = options["tail_extension_mm"]
    frame = candidate["frame"]

    region = candidate["region"]

    def run_to_base(tail_x: tuple, root_depth: float) -> float:
        # The tail reaches the exit across its whole width: measure at the exit's
        # lowest point under it (an arc sags below the chord of the tail's corners).
        lowest = region.exits.lowest_exit_y(field_x + tail_x[0], field_x + tail_x[1])
        if lowest is None:
            return math.inf
        return field_y - root_depth - lowest

    row_run = run_to_base(extent["row_tail_x"], extent["row_root"])
    column_run = run_to_base(extent["column_tail_x"], extent["column_root"])
    if math.inf in (row_run, column_run):
        rejected["a tail misses the base edge"] = rejected.get("a tail misses the base edge", 0) + 1
        return None
    minimum = TAIL_MIN_MM[options["template"]]
    row_tail = round(max(minimum, math.ceil((row_run + extension) * 1000) / 1000), 3)
    column_tail = round(max(minimum, math.ceil((column_run + extension) * 1000) / 1000), 3)
    role = candidate["role"]
    # tail.top_length_mm belongs to the physical top board.
    tails = (row_tail, column_tail) if role == "rows_top" else (column_tail, row_tail)
    if max(tails) > TAIL_MAX_MM[options["template"]] + 1e-9:
        reason = tails_too_long(options["template"])
        rejected[reason] = rejected.get(reason, 0) + 1
        return None
    design = design_for(candidate["rows"], candidate["columns"], candidate["pitch_x"], candidate["pitch_y"], options, role,
                        candidate["routing"], tails)
    result = generate_design(design, cache=cache)
    if not result["ok"]:
        codes = sorted({issue["code"] for issue in result["validation"]["errors"]})
        reason = "engine rejected the design (" + ", ".join(codes[:3]) + ")"
        rejected[reason] = rejected.get(reason, 0) + 1
        return None
    outlines = board_outlines_base(result, (field_x, field_y))
    clearance = check_containment(outlines, candidate["region"], frame, chart, obstacles, options["edge_margin_mm"],
                                  tail_roots=tail_roots_base(result, (field_x, field_y)))
    if clearance is None:
        rejected["real outline leaves the surface"] = rejected.get("real outline leaves the surface", 0) + 1
        return None
    manifest = result["manifest"]
    aw, ah = extent["field"]
    area = chart.stats["area_mm2"]
    placement = {
        "base_side": candidate["side"]["index"],
        "base_kind": candidate["side"].get("kind", "side"),
        "exit_edges": sorted(candidate["region"].exit_edges),
        "base_angle_deg": candidate["angle_deg"],
        "base_from_uv": candidate["side"]["from_uv"],
        "base_to_uv": candidate["side"]["to_uv"],
        "base_inward_uv": candidate["side"]["inward_uv"],
        "field_origin_base": [round(field_x, 6), round(field_y, 6)],
        "field_origin_uv": [round(c, 6) for c in frame.to_chart((field_x, field_y))],
        "field_x_uv": [round(c, 9) for c in frame.ex],
        "field_y_uv": [round(c, 9) for c in frame.ey],
        "seen_from": "outside",
        "bottom_board": result["design"]["role_mapping"]["bottom"],
    }
    return {
        "design": result["design"],
        "build_id": manifest["build_id"],
        "build_sha256": manifest["build_sha256"],
        "placement": placement,
        "metrics": {
            "rows": candidate["rows"],
            "columns": candidate["columns"],
            "taxels": candidate["taxels"],
            "pitch_x_mm": candidate["pitch_x"],
            "pitch_y_mm": candidate["pitch_y"],
            "field_mm": [round(aw, 6), round(ah, 6)],
            "field_coverage": round(aw * ah / area, 6) if area else 0.0,
            "stack_width_mm": round(extent["width"], 6),
            "row_tail_mm": row_tail,
            "column_tail_mm": column_tail,
            "min_clearance_mm": round(clearance, 6),
            "role_mapping": role,
            "routing": candidate["routing"],
            "angle_deg": candidate["angle_deg"],
            # The readout: every position is a taxel of a rectangular field.
            "positions": candidate["rows"] * candidate["columns"],
            "sampled": 1.0,
            "mask_class": None,
            "reader": reader_module.of_readout(candidate["rows"], candidate["columns"], options["reader"]),
        },
        "outlines_uv": {name: [[round(c, 6) for c in frame.to_chart(p)] for p in pts] for name, pts in outlines.items()},
    }


def board_outlines_base(result: Mapping[str, Any], field_origin: Sequence[float]) -> dict:
    """Both board outlines (and the field rectangle) as seen from outside, in the base frame."""

    design = result["design"]
    top_role = design["role_mapping"]["top"]
    outlines = {}
    for key in ("row", "column"):
        board = result["boards"][key]
        grid = board["grid_registration"]["active_region"]
        ax, ay, aw = grid["x"], grid["y"], grid["width"]
        mirrored = (key == "row" and top_role == "rows") or (key == "column" and top_role == "columns")
        points = []
        for x, y in board["outline"]["points"]:
            rx, ry = x - ax, y - ay
            if mirrored:
                rx = aw - rx
            points.append((rx + field_origin[0], ry + field_origin[1]))
        if mirrored:
            points.reverse()
        outlines[key] = points
    grid = result["boards"]["row"]["grid_registration"]["active_region"]
    x0, y0 = field_origin
    outlines["field"] = [(x0, y0), (x0 + grid["width"], y0), (x0 + grid["width"], y0 + grid["height"]), (x0, y0 + grid["height"])]
    if "active_outline" in result["boards"]["row"]["grid_registration"]:
        # A masked field: its crossing region P (surface.fill), not the bounding rectangle.
        from .fill import field_polygon

        outlines["field"] = field_polygon(result, field_origin)
    return outlines


def tail_roots_base(result: Mapping[str, Any], field_origin: Sequence[float]) -> dict:
    """The y of each board's tail root in the base frame (``check_containment``'s ``tail_roots``).

    With the tails ``bottom``, a board's tail runs from its tip up to the top
    of ``tail.bounds``; the rest of the board (field, Row channel, Column
    fan-out) lies above that line, only the junction's fillets below it.  The
    same depths as :func:`stack_extent`'s ``row_root`` and ``column_root``.
    """

    roots = {}
    for key in ("row", "column"):
        board = result["boards"][key]
        bounds = board["tail"]["bounds"]
        roots[key] = field_origin[1] + bounds["y"] + bounds["height"] - board["grid_registration"]["active_region"]["y"]
    return roots


def check_containment(outlines: Mapping[str, Sequence], region: Any, frame: BaseFrame, chart: Chart, obstacles, margin: float,
                      tail_roots: Any = None) -> Any:
    """Smallest clearance of the board outlines to the surface edge and obstacles, or None.

    The boards must lie inside the chart's outer boundary, except where their
    tails cross the exit segments and continue beyond them.  ``region`` is
    the fit's raster or an :class:`ExitOutline` (the map's check).  The
    clearance covers the part of every board edge on the surface (an edge
    that crosses the exit counts up to the crossing) against the non-exit
    boundary, the holes and the obstacles.

    ``tail_roots`` (:func:`tail_roots_base`) checks that only the tails cross
    the exit: every part of a board beyond it lies at or below that board's
    tail root.  Without it, any part of a board may cross the exit.
    """

    context = _containment_context(region, frame, obstacles)
    outline = region.outline
    edges, exit_segments, exit_index = context["edges"], context["exit_segments"], context["exit_index"]
    obstacle_polygons, bend_index = context["obstacle_polygons"], context["bend_index"]
    clearance = math.inf
    on_surface = []  # the board edges' parts on the surface

    def inside(p) -> bool:
        return point_in_polygon(p, outline)

    def beyond_exit(p) -> bool:
        y = region.exit_y(p[0])
        return y is not None and p[1] <= y + 1e-6

    for name in ("row", "column"):
        polygon = list(outlines[name])
        flags = [inside(p) for p in polygon]
        for p, flag in zip(polygon, flags):
            if not flag and not beyond_exit(p):
                return None
        if tail_roots is not None and not _crosses_below(polygon, flags, tail_roots[name] + 1e-6, exit_index):
            return None
        for k in range(len(polygon)):
            a, b = polygon[k - 1], polygon[k]
            for c, d in edges.near(a, b, 0.0):
                if segments_intersect(a, b, c, d):
                    return None
            if flags[k - 1] and flags[k]:
                on_surface.append((a, b))
            elif flags[k - 1] or flags[k]:
                # The edge leaves through the exit: its part on the surface ends at the crossing.
                inner, outer = (a, b) if flags[k - 1] else (b, a)
                on_surface.append((inner, _exit_crossing(inner, outer, exit_segments)))
            for c, d in bend_index.near(a, b, 0.0):
                if segments_intersect(a, b, c, d):
                    return None
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        box = (min(xs), min(ys), max(xs), max(ys))
        for obstacle, (ox0, oy0, ox1, oy1) in obstacle_polygons:
            if ox1 < box[0] or ox0 > box[2] or oy1 < box[1] or oy0 > box[3]:
                continue
            if any(point_in_polygon(q, polygon) for q in obstacle):
                return None
            for k in range(len(polygon)):
                a, b = polygon[k - 1], polygon[k]
                for m in range(len(obstacle)):
                    if segments_intersect(a, b, obstacle[m - 1], obstacle[m]):
                        return None
        # A bend segment that crosses no board edge lies wholly inside or outside the board.
        for c, d in bend_index.segments:
            if box[0] <= c[0] <= box[2] and box[1] <= c[1] <= box[3] and point_in_polygon(c, polygon):
                return None
    # Nothing crosses any more, so the smallest distance between the boards' parts on
    # the surface and what they must keep clear of is reached at a vertex of one side.
    clear_index = context["clear_index"]
    if on_surface and clear_index.segments:
        board_index = _SegmentIndex(on_surface)
        corners = sorted({q for segment in on_surface for q in segment})
        # The boards' extreme corners first: they bound the search for all the others.
        extremes = {min(corners), max(corners), min(corners, key=lambda q: (q[1], q[0])), max(corners, key=lambda q: (q[1], q[0]))}
        for p in sorted(extremes):
            clearance = min(clearance, clear_index.point_distance(p))
        for p in corners:
            clearance = min(clearance, clear_index.point_distance(p, clearance))
        for p in context["clear_points"]:
            clearance = min(clearance, board_index.point_distance(p, clearance))
    if clearance < margin - 1e-6:
        return None
    return clearance if clearance != math.inf else 0.0


def _containment_context(region: Any, frame: BaseFrame, obstacles: Mapping[str, Any]) -> dict:
    """What check_containment checks the boards against, in the base frame, built once per region.

    The fit realizes many candidates in the same few frames: the walls, the exit, the obstacles and the bend segments (with
    their indexes) are the same for all of them.
    """

    cached = getattr(region, "_containment", None)
    if cached is not None and cached[0] is obstacles and cached[1] is frame:
        return cached[2]
    outline = region.outline
    n = len(outline)
    exits = region.exit_edges
    edges = _SegmentIndex([(outline[i], outline[(i + 1) % n]) for i in range(n) if i not in exits])
    exit_segments = [(outline[i], outline[(i + 1) % n]) for i in sorted(exits)]
    polygons = [[frame.to_base(p) for p in poly] for key in ("holes", "strained", "covered") for poly in obstacles[key]]
    bend_segments_base = [(frame.to_base(a), frame.to_base(b)) for a, b, _ in obstacles["bends"]]
    keep_clear = list(edges.segments) + [(polygon[m - 1], polygon[m]) for polygon in polygons for m in range(len(polygon))]
    keep_clear += bend_segments_base
    context = {
        "edges": edges,
        "exit_segments": exit_segments,
        "exit_index": _SegmentIndex(exit_segments),
        "obstacle_polygons": [
            (polygon, (min(p[0] for p in polygon), min(p[1] for p in polygon), max(p[0] for p in polygon), max(p[1] for p in polygon)))
            for polygon in polygons if polygon
        ],
        "bend_index": _SegmentIndex(bend_segments_base),
        "clear_index": _SegmentIndex(keep_clear),
        "clear_points": sorted({q for segment in keep_clear for q in segment}),
    }
    region._containment = (obstacles, frame, context)
    return context


def _crosses_below(polygon: Sequence, flags: Sequence[bool], root: float, exit_index: Any) -> bool:
    """True when a board meets the exit only at or below ``root`` (its tail root line).

    The board's part beyond the exit is bounded by its vertices beyond the
    exit, the points where its edges cross the exit and the exit's vertices
    inside the board: when all of these lie at or below the line, so does
    that part (an edge crossing the exit twice or a notch in the exit as well).
    """

    if any(not flag and p[1] > root for p, flag in zip(polygon, flags)):
        return False
    for k in range(len(polygon)):
        a, b = polygon[k - 1], polygon[k]
        if a[1] <= root and b[1] <= root:
            continue
        for c, d in exit_index.near(a, b, 0.0):
            if segments_intersect(a, b, c, d) and _highest_common_y(a, b, c, d) > root:
                return False
    xs = [p[0] for p in polygon]
    x0, x1, top = min(xs), max(xs), max(p[1] for p in polygon)
    for c, d in exit_index.segments:
        for q in (c, d):
            if root < q[1] <= top and x0 <= q[0] <= x1 and point_in_polygon(q, polygon):
                return False
    return True


def _highest_common_y(a, b, c, d) -> float:
    """The highest y that the intersecting segments ab and cd share."""

    dx, dy = b[0] - a[0], b[1] - a[1]
    fx, fy = d[0] - c[0], d[1] - c[1]
    det = dx * fy - dy * fx
    if det == 0:
        # Collinear: y is monotonic along the line, so the overlap ends at the lower of the two tops.
        return min(max(a[1], b[1]), max(c[1], d[1]))
    t = min(max(((c[0] - a[0]) * fy - (c[1] - a[1]) * fx) / det, 0.0), 1.0)
    return a[1] + dy * t


class _SegmentIndex:
    """Segments in a uniform grid: the ones near a segment, and the distance to the nearest."""

    # A segment crossing more cells than this is checked by every query instead.
    LONG_CELLS = 4096

    def __init__(self, segments: Sequence) -> None:
        self.segments = list(segments)
        lengths = sorted(dist2(a, b) for a, b in self.segments) or [1.0]
        # The median length, but at least a quarter of the mean: a few thousand long
        # segments among short ones (bend lines across a fine blend) then take a
        # few cells each on average, not hundreds.
        self.cell = max(lengths[len(lengths) // 2], 0.05, math.fsum(lengths) / (4 * len(lengths)))
        self.grid: dict = {}
        self.long: list = []
        for index, (a, b) in enumerate(self.segments):
            # Every cell the segment passes through.  (Not _keys: its shortcut for
            # large queries returns the cells filled so far, which would drop a long
            # segment met early from the cells it crosses.)
            keys = self._cells(a, b)
            if keys is None:
                self.long.append(index)
                continue
            for key in keys:
                self.grid.setdefault(key, []).append(index)

    def _cells(self, a, b) -> Any:
        """The cells of the segment's extent within each row of cells (a superset), or None beyond LONG_CELLS."""

        cell = self.cell
        (ax, ay), (bx, by) = a, b
        # A hair wider than the segment: a point on a cell border is found from both sides.
        eps = cell * 1e-6
        j0, j1 = int(math.floor((min(ay, by) - eps) / cell)), int(math.floor((max(ay, by) + eps) / cell))
        i0, i1 = int(math.floor((min(ax, bx) - eps) / cell)), int(math.floor((max(ax, bx) + eps) / cell))
        if (j1 - j0 + 1) + (i1 - i0 + 1) > self.LONG_CELLS:
            return None
        keys = []
        dx, dy = bx - ax, by - ay
        for j in range(j0, j1 + 1):
            if dy == 0:
                left, right = min(ax, bx), max(ax, bx)
            else:
                # The segment's x at the row's lower and upper borders (clamped to its ends).
                xa = ax + dx * min(max((j * cell - eps - ay) / dy, 0.0), 1.0)
                xb = ax + dx * min(max(((j + 1) * cell + eps - ay) / dy, 0.0), 1.0)
                left, right = (xa, xb) if xa <= xb else (xb, xa)
            keys.extend((i, j) for i in range(max(i0, int(math.floor((left - eps) / cell))), min(i1, int(math.floor((right + eps) / cell))) + 1))
        return keys

    def _keys(self, a, b, pad: float):
        cell = self.cell
        i0, i1 = int(math.floor((min(a[0], b[0]) - pad) / cell)), int(math.floor((max(a[0], b[0]) + pad) / cell))
        j0, j1 = int(math.floor((min(a[1], b[1]) - pad) / cell)), int(math.floor((max(a[1], b[1]) + pad) / cell))
        if (i1 - i0 + 1) * (j1 - j0 + 1) > 4 * len(self.grid) + 64:
            return list(self.grid)  # a query larger than the grid: every occupied cell
        return [(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)]

    def near(self, a, b, pad: float) -> list:
        found = set(self.long)
        for key in self._keys(a, b, pad):
            found.update(self.grid.get(key, ()))
        return [self.segments[index] for index in sorted(found)]

    def point_distance(self, p, limit: float = math.inf) -> float:
        """Distance from point p to the nearest indexed segment (exact), or inf when none is within ``limit``."""

        if not self.segments:
            return math.inf
        pad = min(self.cell, limit)
        while True:
            best = min((segment_distance(p, p, c, d) for c, d in self.near(p, p, pad)), default=math.inf)
            if best <= pad:
                return best
            if pad >= limit or pad > 1e7:
                return best if best <= limit else math.inf
            # Every segment within ``best`` lies inside the box grown by it.
            pad = min(best if best != math.inf else pad * 8, limit)


def _exit_crossing(inner, outer, exit_segments) -> tuple:
    """Where the segment from ``inner`` (on the surface) to ``outer`` crosses the exit."""

    best = None
    dx, dy = outer[0] - inner[0], outer[1] - inner[1]
    for (cx, cy), (ex, ey) in exit_segments:
        fx, fy = ex - cx, ey - cy
        det = dx * fy - dy * fx
        if det == 0:
            continue
        t = ((cx - inner[0]) * fy - (cy - inner[1]) * fx) / det
        s = ((cx - inner[0]) * dy - (cy - inner[1]) * dx) / det
        if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= s <= 1 + 1e-9 and (best is None or t < best):
            best = t
    if best is None:
        return outer
    best = min(max(best, 0.0), 1.0)
    return (inner[0] + dx * best, inner[1] + dy * best)
