"""Map a generated design onto the part: taxel map, 3D overlay, wrap template, checks.

The placement comes from the fit (``surface.fit``): the field origin in the
base frame of the chosen base side, seen from outside the part.  Everything
on the surface is mapped through the chart (barycentric in the chart
triangle), so it lies on the mesh exactly; the tails beyond the base edge
are not mapped (they leave the surface).

Taxel ``(r, c)`` is the crossing of ``ROW_r`` and ``COL_c``.  Its centre is
taken from the generated electrodes: the across-axis centre of the Row
electrode and of the Column electrode, each converted to the outside view
(the physical top board is seen from its back, i.e. mirrored across the
field's vertical centre line).

A masked field (``matrix.mask``, the fit's ``shape: fill``) keeps its R x C
readout, but only the crossings whose copper overlaps in the stack are
taxels: the map lists those (checked against the design's mask, record
``taxel_mask_matches_design``) and adds ``readout``, the matrix the reader
scans, whose other positions always read 0.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from engine import design_mask, generate_design
from engine.drc import stack_frame
from engine.geometry import rect_bounds, rect_corners
from engine.layout import row_bus

from . import api as api_module
from . import bend
from . import border as border_module
from . import reader as reader_module
from .chart import Chart, chart_point_to_3d
from .errors import SurfaceError, finite_number
from .fit import (
    SINGLE_FPC_MM,
    STACK_THICKNESS_MM,
    STATIC_BEND_FACTOR,
    TAIL_MAX_MM,
    TAIL_MIN_MM,
    TAIL_REACH_MIN_MM,
    TEMPLATES,
    BaseFrame,
    ExitOutline,
    board_outlines_base,
    check_containment,
    parse_options,
    surface_obstacles,
    tail_roots_base,
)
from .mesh import Mesh, dist2, dot, hypot2, norm, sub

MAP_FORMAT = "tactile-taxel-map/v1"
PLACEMENT_FORMAT = "tactile-surface-placement/v1"
DENSIFY_MM = 0.5
# A placement's chart coordinates beyond this are damage: the frame transforms and the
# point grids would overflow on them (as for the 3D points of a request).
MAX_PLACEMENT_MM = 1e7
# The map reply echoes the placement, unknown keys included; beyond this nesting it is damage
# (a fit's placement nests 4-5 levels): the CLI's indenting encoder stops near a thousand
# levels and the C encoder near ten thousand, while 3.12's strict loader reads deeper.
MAX_PLACEMENT_DEPTH = 32
# Neighbour spacing differs from the pitch by the chart's stretch (at most the strain
# limit under the boards) and by the chords that measure it along the surface (about
# 0.1% over creases); 0.5% covers both at the default strain limit of 0.3%.
SPACING_TOLERANCE = 0.005
SPACING_CHORD_ERROR = 0.002
# The keys that decide the boards' geometry; the placement is only valid for the same values.
GEOMETRY_KEYS = ("template_id", "matrix", "role_mapping", "routing", "connector")


def map_route(header: Mapping[str, Any], mesh_bytes: bytes, cache: Any = None) -> dict:
    api_module._keys(header, {"unit", "name", "selection", "placement", "design", "options"}, "map")
    placement = validate_placement(header.get("placement"))
    mesh = api_module.load_mesh(header, mesh_bytes)
    fitted_mesh = placement["mesh"]
    if fitted_mesh.get("sha256") != mesh.sha256 or fitted_mesh.get("unit") != mesh.unit:
        raise SurfaceError(
            "E_SURFACE_PLACEMENT_MISMATCH",
            f"The placement was fitted on another mesh ({fitted_mesh.get('name') or 'unnamed'}, sha256 "
            f"{str(fitted_mesh.get('sha256'))[:12]}..., unit {fitted_mesh.get('unit')}); this one is "
            f"{mesh.sha256[:12]}... in {mesh.unit}. Fit again on this mesh.",
            fields=["mesh"],
        )
    selection = header.get("selection", placement["selection"])
    if selection != placement["selection"]:
        raise SurfaceError(
            "E_SURFACE_PLACEMENT_MISMATCH",
            "The selection differs from the one the placement was fitted on; fit again for this selection.",
            fields=["selection"],
        )
    # The user's border (surface.border) in the selection's chart, if the fit had one.
    given = border_module.parse(placement["border"], "placement.border") if "border" in placement else None
    border = given
    facets, chart = api_module.selection_chart(mesh, selection)
    limit = placement.get("strain_limited")
    if limit is not None:
        # The fit placed the boards on the strain-limited disk's chart: rebuild that chart.
        from .fit import limited_chart

        whole = chart
        facets, chart = limited_chart(mesh, facets, limit)
        if border is not None:
            border = border_module.carry(border, whole, chart)
    # The exit segments number the outline of the chart the fit used (the strain-limited disk's, if any).
    segments = len(chart.loops[chart.outer])
    if any(edge >= segments for edge in placement["exit_edges"]):
        raise SurfaceError(
            "E_SURFACE_REQUEST",
            f"placement.exit_edges must be segments of the selection's outline (0..{segments - 1}); fit again.",
        )
    design = header.get("design")
    if not isinstance(design, Mapping):
        raise SurfaceError("E_SURFACE_REQUEST", "design must be the design to map (the proposal's or the form's).")
    # The fit's own options (strain limit, edge margin, tail extension) unless given; the map fits nothing, so the options
    # CAD mode no longer has (fit.CAD_ONLY: template, shape, rectangle_preference_pct) are taken as the placement was fitted
    # with them, exactly what a fit then accepted (fit.SAVED_VALUES, on the generic template fit.SAVED_GENERIC_MAX_COLUMNS
    # and neither shape fill nor containment field named; the design's template_id picks the template); only map_options
    # reads shape and template, to default the containment of options that name none.
    options = parse_options(map_options(header.get("options", placement.get("options", {})), design), mapping=True)
    result = generate_design(dict(design), cache=cache)
    if not result["ok"]:
        codes = sorted({issue["code"] for issue in result["validation"]["errors"]})
        raise SurfaceError("E_SURFACE_REQUEST", "The design does not generate: " + ", ".join(codes[:5]) + ".")
    check_match(placement, result["design"])
    mapped = map_design(mesh, chart, placement, result, options, border)
    if given is not None:
        mapped["border"] = border_module.echo(given)
    # The placement of the mapped design (its tail lengths may differ from the proposal's).
    mapped["placement"] = dict(placement, design=result["design"], build_id=result["manifest"]["build_id"])
    return mapped


def map_options(raw: Any, design: Mapping[str, Any]) -> Any:
    """The fit options a map takes: without ``containment`` (a placement written before the option, or options given
    without it), the design's own: ``field`` for a diagonal Row bus (``routing.row_sides`` left, right or both: only
    field-only fits build it on the surface template), ``board`` otherwise (the straight Row channel, ``channel`` or
    none), whatever the fit's default."""

    if not isinstance(raw, Mapping) or "containment" in raw:
        return raw
    bus = row_bus(design)
    return dict(raw, containment="field" if bus and raw.get("shape", "fill") == "fill" and raw.get("template", "surface") == "surface" else "board")


def validate_placement(placement: Any) -> Mapping[str, Any]:
    """The placement document's shape, so that a damaged one is a 422 and never a crash."""

    if not isinstance(placement, Mapping):
        raise SurfaceError("E_SURFACE_REQUEST", "placement must be the placement object of a fit proposal.")
    if _nesting(placement, MAX_PLACEMENT_DEPTH) > MAX_PLACEMENT_DEPTH:
        raise SurfaceError("E_SURFACE_REQUEST", f"placement nests objects and arrays more than {MAX_PLACEMENT_DEPTH} levels deep.")

    def vector(key: str, required: bool = True) -> None:
        # Only a missing key is optional: an explicit null is damage like any other bad value.
        if key not in placement and not required:
            return
        value = placement.get(key)
        if not (isinstance(value, Sequence) and not isinstance(value, str) and len(value) == 2):
            raise SurfaceError("E_SURFACE_REQUEST", f"placement.{key} must be two finite numbers.")
        for k, c in enumerate(value):
            finite_number(c, f"placement.{key}[{k}]", -MAX_PLACEMENT_MM, MAX_PLACEMENT_MM)

    for key in ("base_from_uv", "base_inward_uv", "field_origin_base"):
        vector(key)
    vector("base_to_uv", required=False)
    # The base frame takes the inward normal as it is: any other length would scale the boards.
    inward = [float(c) for c in placement["base_inward_uv"]]
    if abs(hypot2(*inward) - 1) > 1e-6:
        raise SurfaceError("E_SURFACE_REQUEST", "placement.base_inward_uv must be a unit vector.")
    angle = placement.get("base_angle_deg", 0.0)
    if not _finite(angle) or abs(angle) > 90:
        raise SurfaceError("E_SURFACE_REQUEST", "placement.base_angle_deg must be a number within -90..90.")
    edges = placement.get("exit_edges")
    if not (isinstance(edges, list) and edges and all(isinstance(e, int) and not isinstance(e, bool) and e >= 0 for e in edges)):
        raise SurfaceError("E_SURFACE_REQUEST", "placement.exit_edges must be a non-empty list of outline segment numbers.")
    for key in ("design", "mesh"):
        if not isinstance(placement.get(key), Mapping):
            raise SurfaceError("E_SURFACE_REQUEST", f"placement.{key} is missing.")
    if "selection" not in placement:
        raise SurfaceError("E_SURFACE_REQUEST", "placement.selection is missing.")
    if "options" in placement and not isinstance(placement["options"], Mapping):
        raise SurfaceError("E_SURFACE_REQUEST", "placement.options must be an object.")
    limit = placement.get("strain_limited")
    if limit is not None:
        centre = limit.get("centre_facet") if isinstance(limit, Mapping) else None
        radius = limit.get("radius_mm") if isinstance(limit, Mapping) else None
        if not (isinstance(centre, int) and not isinstance(centre, bool) and centre >= 0 and _finite(radius) and radius > 0):
            raise SurfaceError("E_SURFACE_REQUEST", "placement.strain_limited must hold centre_facet and radius_mm.")
    return placement


def _nesting(value: Any, limit: int) -> int:
    """How many levels of objects and arrays a JSON value nests (iterative; stops once beyond ``limit``)."""

    deepest = 0
    stack = [(value, 1)]
    while stack and deepest <= limit:
        item, level = stack.pop()
        deepest = max(deepest, level)
        children = item.values() if isinstance(item, Mapping) else item
        stack.extend((child, level + 1) for child in children if isinstance(child, (Mapping, list, tuple)))
    return deepest


def _finite(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except OverflowError:
        return False


def check_match(placement: Mapping[str, Any], design: Mapping[str, Any]) -> None:
    """The design must keep the geometry the placement was fitted for (tail lengths may differ)."""

    fitted = placement["design"]
    differing = [key for key in GEOMETRY_KEYS if fitted.get(key) != design.get(key)]
    for side in ("row_side", "column_side"):
        if design["tail"][side] != "bottom":
            differing.append(f"tail.{side}")
    if differing:
        raise SurfaceError(
            "E_SURFACE_PLACEMENT_MISMATCH",
            "The design differs from the fitted one in " + ", ".join(differing) + "; fit again for this design.",
            fields=differing,
        )


def placement_record(proposal: Mapping[str, Any], mesh: Mesh, selection: Any, options: Mapping[str, Any], limited: Any = None) -> dict:
    """The sidecar placement document of a proposal (what the browser stores and sends back)."""

    placement = dict(proposal["placement"])
    if limited is not None:
        placement["strain_limited"] = dict(limited)
    placement["format"] = PLACEMENT_FORMAT
    placement["design"] = proposal["design"]
    placement["build_id"] = proposal["build_id"]
    placement["mesh"] = {"sha256": mesh.sha256, "unit": mesh.unit, "facets": mesh.facet_count, "name": mesh.name}
    placement["selection"] = selection
    placement["options"] = dict(options)
    return placement


# --------------------------------------------------------------------------
# Mapping
# --------------------------------------------------------------------------


def map_design(mesh: Mesh, chart: Chart, placement: Mapping[str, Any], result: Mapping[str, Any], options: Mapping[str, Any],
               border: Any = None) -> dict:
    """The map of a placed design; ``border`` the user's border in ``chart``'s uv (surface.border), if the fit had one."""

    side = {
        "from_uv": placement["base_from_uv"],
        "to_uv": placement.get("base_to_uv", placement["base_from_uv"]),
        "inward_uv": placement["base_inward_uv"],
    }
    frame = BaseFrame(side, placement.get("base_angle_deg", 0.0))
    origin = placement["field_origin_base"]
    outlines = board_outlines_base(result, origin)
    design = result["design"]
    taxels = taxel_centres(result)
    pins = pin_maps(result)
    reader = reader_module.of_design(options["reader"], pins["row_pins"], pins["column_pins"])
    records = []
    mapped = []
    misses = 0
    for item in taxels:
        base = (origin[0] + item["x"], origin[1] + item["y"])
        uv = frame.to_chart(base)
        hit = chart_point_to_3d(chart, mesh, uv)
        if hit is None:
            misses += 1
            continue
        point, facet = hit
        normal = mesh.normals[facet]
        record = {
            "row": item["row"],
            "column": item["column"],
            "row_net": item["row_net"],
            "column_net": item["column_net"],
            "row_pin": pins["row"].get(item["row_net"]),
            "column_pin": pins["column"].get(item["column_net"]),
            "uv_mm": [_r(uv[0]), _r(uv[1])],
            "xyz_mm": [_r(c) for c in point],
            "normal": [_r(c, 9) for c in normal],
            "facet": facet,
        }
        lines = reader_record(record["row_pin"], record["column_pin"], pins, reader)
        if lines is not None:
            record["reader"] = lines
        records.append(record)
        mapped.append((item, point, facet))
    overlay = {}
    for name, polygon in outlines.items():
        overlay[name] = map_polyline(mesh, chart, frame, polygon, closed=True)
    exits = ExitOutline([frame.to_base(p) for p in chart.outline()], placement["exit_edges"])
    routing = None
    if options["containment"] == "field":
        # Only the taxel field must lie on the surface (surface.fieldfit): F's records, the routing reported.
        from .fieldfit import verify_field

        verification, routing = verify_field(mesh, chart, frame, exits, outlines, records, mapped, result, misses, options, origin)
    else:
        verification = verify(mesh, chart, frame, exits, outlines, records, mapped, design, misses, options, tail_roots=tail_roots_base(result, origin))
    masked = design_mask(design) is not None
    if masked:
        verification.append(mask_record(design, taxels))
    if border is not None:
        # The border constrains the taxels: every taxel square of the build inside it (required).
        verification.append(border_module.record(result, border, frame, origin))
    mapped_result = {
        "ok": all(record["passed"] for record in verification),
        "format": MAP_FORMAT,
        "mesh": {"sha256": mesh.sha256, "unit": mesh.unit, "scale_to_mm": mesh.scale_mm, "frame": "stl", "units": "mm"},
        "build_id": result["manifest"]["build_id"],
        "taxel_count": len(records),
        "taxels": records,
        "reader": reader_module.summary(reader, pins["row_pins"]),
        "overlay": overlay,
        "stack": {
            "bottom_board": design["role_mapping"]["bottom"],
            "top_board": design["role_mapping"]["top"],
            "glued_to_part": design["role_mapping"]["bottom"],
            "contact_offset_mm": STACK_THICKNESS_MM,
            "note": f"Positions are on the part's surface; the sensor's outer surface is about {STACK_THICKNESS_MM} mm further out along the normal.",
        },
        "verification": verification,
        "wrap_svg": wrap_template(chart, frame, outlines, taxels, origin),
    }
    order = result["boards"]["row"]["tail"].get("row_contact_order")
    if masked or order is not None:
        mapped_result["readout"] = readout(design, len(records))
        if order is not None:
            # A diagonal Row bus folds the Row pins (engine.diagonal): the Row nets at the tail's contact positions 1..N,
            # and by pin from the pads (the scan order numbers the pins: reversed, pin 1 is the last contact).
            mapped_result["readout"]["row_contact_order"] = list(order)
            mapped_result["readout"]["row_pin_order"] = row_pin_order(pins["row"])
    if routing is not None:
        mapped_result["routing_on_surface"] = routing
    return mapped_result


def readout(design: Mapping[str, Any], active: int) -> dict:
    """The readout matrix of a masked field (or of a diagonal Row bus's full one): the reader scans R x C positions; the
    inactive ones always read 0."""

    rows, columns = int(design["matrix"]["rows"]), int(design["matrix"]["columns"])
    spans = design_mask(design) or ((1, columns),) * rows
    return {
        "rows": rows,
        "columns": columns,
        "positions": rows * columns,
        "active": active,
        "row_spans": [[int(first), int(last)] for first, last in spans],
        "inactive": "always 0",
    }


def row_pin_order(row_pins: Mapping[str, Any]) -> list:
    """The Row nets by connector pin, pin 1 first, from the Row board's pads (:func:`pin_maps`: net -> pin)."""

    return [net for net, _ in sorted(((net, pin) for net, pin in row_pins.items() if net.startswith("ROW_")), key=lambda item: item[1])]


def mask_record(design: Mapping[str, Any], taxels: Sequence) -> dict:
    """``taxel_mask_matches_design``: the crossings whose copper overlaps are exactly the design's mask."""

    expected = {(row, column) for row, (first, last) in enumerate(design_mask(design), start=1) for column in range(first, last + 1)}
    found = {(item["row"], item["column"]) for item in taxels}
    return _record("taxel_mask_matches_design", 0, len(expected ^ found), "max<=", "count",
                   "the stacked electrodes cross exactly at the taxels of the design's mask (the other positions read 0)")


def reader_record(row_pin: Any, column_pin: Any, pins: Mapping[str, Any], reader: Any) -> Any:
    """A taxel's reader lines (:mod:`surface.reader`): the FlexiTac's as :func:`reader_lines`, the others alike."""

    if reader is None:
        return None
    if reader == reader_module.FLEXITAC:
        return reader_lines(row_pin, column_pin, pins)
    return reader_module.lines(reader, row_pin, column_pin, pins["row_pins"])


def taxel_centres(result: Mapping[str, Any]) -> list:
    """Taxel centres in the outside-view field frame (field lower-left at 0, 0)."""

    design = result["design"]
    if design_mask(design) is not None:
        return masked_taxel_centres(result)
    top = design["role_mapping"]["top"]
    rows = design["matrix"]["rows"]
    columns = design["matrix"]["columns"]
    row_y = {}
    column_x = {}
    for key in ("row", "column"):
        board = result["boards"][key]
        grid = board["grid_registration"]["active_region"]
        ax, ay, aw = grid["x"], grid["y"], grid["width"]
        mirrored = (key == "row" and top == "rows") or (key == "column" and top == "columns")
        for electrode in board["layers"]["top_copper"]["electrodes"]:
            x0, y0, x1, y1 = rect_bounds(electrode)
            if key == "row":
                row_y[electrode["net"]] = (y0 + y1) / 2 - ay
            else:
                cx = (x0 + x1) / 2 - ax
                column_x[electrode["net"]] = aw - cx if mirrored else cx
    items = []
    for r in range(1, rows + 1):
        row_net = f"ROW_{r:02d}"
        for c in range(1, columns + 1):
            column_net = f"COL_{c:02d}"
            items.append({"row": r, "column": c, "row_net": row_net, "column_net": column_net, "x": column_x[column_net], "y": row_y[row_net]})
    return items


def masked_taxel_centres(result: Mapping[str, Any]) -> list:
    """The taxels of a masked field: the crossings whose stacked copper overlaps, outside view, field lower-left at 0, 0.

    Both boards in the stack frame (:func:`engine.drc.stack_frame`: the
    active region's centre at the origin, the physical top board turned
    over), shifted by half the active region; a Row and a Column electrode
    whose boxes overlap (by more than 1e-9 mm both ways) make a taxel at the
    Column electrode's centre x and the Row electrode's centre y.
    """

    design = result["design"]
    roles = design["role_mapping"]
    boxes: dict = {}
    for key in ("row", "column"):
        board = result["boards"][key]
        convert = stack_frame(board, roles)
        grid = board["grid_registration"]["active_region"]
        shift_x, shift_y = grid["width"] / 2, grid["height"] / 2
        for electrode in board["layers"]["top_copper"]["electrodes"]:
            corners = [convert(corner) for corner in rect_corners(electrode)]
            xs = [x + shift_x for x, _ in corners]
            ys = [y + shift_y for _, y in corners]
            boxes[electrode["net"]] = (min(xs), min(ys), max(xs), max(ys))
    items = []
    for r in range(1, int(design["matrix"]["rows"]) + 1):
        row_net = f"ROW_{r:02d}"
        rx0, ry0, rx1, ry1 = boxes[row_net]
        for c in range(1, int(design["matrix"]["columns"]) + 1):
            column_net = f"COL_{c:02d}"
            cx0, cy0, cx1, cy1 = boxes[column_net]
            if min(rx1, cx1) - max(rx0, cx0) > 1e-9 and min(ry1, cy1) - max(ry0, cy0) > 1e-9:
                items.append({"row": r, "column": c, "row_net": row_net, "column_net": column_net, "x": (cx0 + cx1) / 2, "y": (ry0 + ry1) / 2})
    return items


def pin_maps(result: Mapping[str, Any]) -> dict:
    maps = {}
    for key in ("row", "column"):
        board = result["boards"][key]
        maps[key] = {pad["net"]: pad["pin"] for pad in board["layers"]["top_copper"]["pads"] if pad.get("kind") == "connector_pad"}
        maps[key + "_pins"] = board["tail"]["connector_pins"]
    return maps


def reader_lines(row_pin: Any, column_pin: Any, pins: Mapping[str, Any]) -> Any:
    """FlexiTac reader lines when the tails are sized 16/32 (either electrode set on either connector).

    The reader scans connector pins: sense line SR<n> is pin n of the 16-pin
    tail (FPC1), drive line SC<n> pin n of the 32-pin tail (FPC2), whatever
    the channel order put on them.
    """

    row_pins, column_pins = pins["row_pins"], pins["column_pins"]
    if {row_pins, column_pins} != {16, 32} or row_pin is None or column_pin is None:
        return None
    sense_index, drive_index = (row_pin, column_pin) if row_pins == 16 else (column_pin, row_pin)
    return {
        "sense_line": f"SR{sense_index}",
        "drive_line": f"SC{drive_index}",
        "sense_connector": "FPC1 (16-pin)",
        "drive_connector": "FPC2 (32-pin)",
        # The RevB.1 frame layout: payload[SC * 16 + SR], both 0-based.
        "frame_index": (drive_index - 1) * 16 + (sense_index - 1),
    }


def map_polyline(mesh: Mesh, chart: Chart, frame: BaseFrame, polygon: Sequence, closed: bool) -> list:
    """Map a base-frame polyline onto the surface; parts off the surface split it into runs."""

    points = list(polygon) + ([polygon[0]] if closed and polygon else [])
    runs = []
    current: list = []
    for k in range(len(points) - 1):
        a, b = points[k], points[k + 1]
        steps = max(1, int(math.ceil(dist2(a, b) / DENSIFY_MM)))
        for s in range(steps + (1 if k == len(points) - 2 else 0)):
            t = s / steps
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            # Off the chart is off the surface.  The base line is no limit: below an arc exit's
            # chord the surface goes on to the arc, and the tails lie on it there.
            hit = chart_point_to_3d(chart, mesh, frame.to_chart(p))
            if hit is None:
                if len(current) > 1:
                    runs.append(current)
                current = []
                continue
            current.append([_r(c) for c in hit[0]])
    if len(current) > 1:
        runs.append(current)
    return runs


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------


def verify(mesh: Mesh, chart: Chart, frame: BaseFrame, exits, outlines, records_out, mapped, design, misses: int, options, tail_roots=None) -> list:
    rows, columns = design["matrix"]["rows"], design["matrix"]["columns"]
    # A masked field's taxels are the positions of its mask (the readout's other positions have no crossing).
    mask = design_mask(design)
    count = rows * columns
    if mask is not None:
        count = 0
        for first, last in mask:
            count += last - first + 1
    records = []
    records.append(_record("taxels_on_surface", count, len(records_out), "min>=", "count", "every taxel maps onto the selection"))
    # In 3D, from the facets' corners (not from the chart): each taxel's distance to the selected facet it maps onto.
    records.append(_record("taxel_surface_distance", 1e-6, _surface_distance(mesh, chart, [(p, f) for _, p, f in mapped]), "max<=", "mm", "mapped taxels lie on the selected surface"))
    # Neighbour spacing along the surface (the chart segment between two taxels, mapped to 3D).
    pitch_x, pitch_y = design["matrix"]["pitch_x_mm"], design["matrix"]["pitch_y_mm"]
    index = {(record["row"], record["column"]): record["uv_mm"] for record in records_out}
    error = 0.0
    for (r, c), uv in index.items():
        for (dr, dc, pitch) in ((0, 1, pitch_x), (1, 0, pitch_y)):
            other = index.get((r + dr, c + dc))
            if other is not None:
                length = _surface_length(mesh, chart, uv, other)
                if length is not None:
                    error = max(error, abs(length - pitch) / pitch)
    spacing_limit = max(SPACING_TOLERANCE, options["strain_limit"] + SPACING_CHORD_ERROR)
    records.append(_record("neighbour_spacing_error", spacing_limit, error, "max<=", "ratio", "taxel spacing along the surface equals the pitch"))
    # The boards on the surface: inside its outline (only the tails cross the exit), clear of holes and obstacles.
    obstacles = surface_obstacles(mesh, chart, options)
    clearance = check_containment(outlines, exits, frame, chart, obstacles, options["edge_margin_mm"], tail_roots=tail_roots)
    records.append(
        {
            "rule": "board_clearance",
            "required": _r(options["edge_margin_mm"]),
            "measured": None if clearance is None else _r(clearance, 9),
            "comparison": "min>=",
            "unit": "mm",
            "passed": clearance is not None,
            "what": "the boards lie on the surface (only the tails cross the exit), clear of its edge, holes and obstacles",
        }
    )
    # Strain of the chart under the boards (every facet a board touches).
    limit = options["strain_limit"]
    strain = _strain_under(chart, mesh, frame, (outlines["row"], outlines["column"]))
    records.append(_record("strain_under_boards", limit, strain, "max<=", "ratio", "the sheet does not stretch beyond the limit"))
    # Bends under the field (stack) and under the boards (single FPC).
    field_limit = STATIC_BEND_FACTOR * STACK_THICKNESS_MM
    board_limit = STATIC_BEND_FACTOR * SINGLE_FPC_MM
    field_radius = _min_bend_radius(mesh, chart, frame, outlines["field"], field_limit)
    board_radius = min(
        _min_bend_radius(mesh, chart, frame, outlines["row"], board_limit),
        _min_bend_radius(mesh, chart, frame, outlines["column"], board_limit),
    )
    records.append(_record("field_bend_radius", field_limit, field_radius, "min>=", "mm", "static bend of the laminated field (10 x 0.47 mm)"))
    records.append(_record("board_bend_radius", board_limit, board_radius, "min>=", "mm", "static bend of a single FPC (10 x 0.11 mm)"))
    tails = design["tail"]
    template = "surface" if design.get("template_id") == TEMPLATES["surface"] else "generic"
    low, high = TAIL_MIN_MM[template], TAIL_MAX_MM[template]
    for name in ("top_length_mm", "bottom_length_mm"):
        within = low - 1e-9 <= tails[name] <= high + 1e-9
        records.append(
            {
                "rule": f"tail_{name}",
                "required": [low, high],
                "measured": _r(tails[name]),
                "comparison": "within",
                "unit": "mm",
                "passed": within,
                "what": f"within the template's {low:g}-{high:g} mm",
            }
        )
    # Each tail reaches beyond the exit by at least the stiffened contact zone.
    for name in ("row", "column"):
        records.append(_record(f"{name}_tail_reach", TAIL_REACH_MIN_MM, _tail_reach(exits, outlines[name]), "min>=", "mm", "the tail's stiffened end (6.0 + 0.5 mm) lies beyond the exit"))
    return records


def _tail_reach(exits, polygon: Sequence) -> float:
    """How far the tail's end lies beyond the exit (below it in the base frame); -inf if it misses the exit."""

    tip = min(p[1] for p in polygon)
    xs = [p[0] for p in polygon if p[1] <= tip + 0.5]
    left, right = min(xs), max(xs)
    reach = math.inf
    steps = 8
    for k in range(steps + 1):
        x = left + (right - left) * k / steps
        y = exits.exit_y(min(max(x, left + 1e-9), right - 1e-9) if right > left else x)
        if y is None:
            return -math.inf
        reach = min(reach, y - tip)
    return reach


def _surface_length(mesh: Mesh, chart: Chart, a: Sequence[float], b: Sequence[float], steps: int = 8) -> Any:
    """Length on the part of the chart segment from a to b (None if it leaves the chart)."""

    points = []
    for k in range(steps + 1):
        t = k / steps
        hit = chart_point_to_3d(chart, mesh, (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        if hit is None:
            return None
        points.append(hit[0])
    return math.fsum(norm(sub(points[k + 1], points[k])) for k in range(steps))


def _surface_distance(mesh: Mesh, chart: Chart, hits: Sequence) -> float:
    """The largest distance from a mapped point to the selected facet it maps onto (3D, from the facet's corners).

    It bounds the point's distance to the selected surface from above.  Only
    the point's own facet is measured: a search for the nearest facet tested
    every facet whose box holds the point, thousands per point on long strips
    (a cylinder exported as full-height facets) or sliver fans.
    """

    from .select import point_triangle_distance

    selected = set(chart.facets)
    worst = 0.0
    for point, facet in hits:
        if facet not in selected:
            return math.inf
        worst = max(worst, point_triangle_distance(point, *mesh.facet_points(facet)))
    return worst


def _record(rule: str, required: float, measured: float, comparison: str, unit: str, what: str) -> dict:
    if comparison == "max<=":
        passed = measured <= required + 1e-12
    else:
        passed = measured >= required - 1e-12
    # No measurement (nothing to measure, or a tail that misses the exit) is null in JSON.
    measured_value = measured if math.isfinite(measured) else None
    return {
        "rule": rule,
        "required": _r(required),
        "measured": None if measured_value is None else _r(measured_value, 9),
        "comparison": comparison,
        "unit": unit,
        "passed": passed,
        "what": what,
    }


def _strain_under(chart: Chart, mesh: Mesh, frame: BaseFrame, polygons: Sequence) -> float:
    """The largest stretch of a chart facet that a board outline (base frame) overlaps, exactly; 0 if none does.

    The facets are tried from the most stretched down, so the first one under
    a board gives the answer: the exact overlap test runs on a few facets, not
    on every facet of a large chart.
    """

    shapes = []
    for polygon in polygons:
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        shapes.append((polygon, (min(xs), min(ys), max(xs), max(ys)), [(polygon[k - 1], polygon[k]) for k in range(len(polygon))]))
    stretch = []
    for facet in chart.facets:
        s1, s2 = chart.strain[facet]
        stretch.append((max(abs(s1 - 1), abs(s2 - 1)), facet))
    stretch.sort(key=lambda item: (-item[0], item[1]))
    worst = 0.0
    for value, facet in stretch:
        if value <= worst:
            break  # sorted: no facet further down raises the maximum
        triangle = [frame.to_base(chart.uv[v]) for v in mesh.facets[facet]]
        if any(_overlaps(triangle, shape) for shape in shapes):
            worst = value
    return worst


def _overlaps(triangle: Sequence, shape: tuple) -> bool:
    """Whether a triangle and a polygon (with its box and edges) overlap: a corner inside, crossing edges, or the polygon inside."""

    from engine.geometry import point_in_polygon, segments_intersect

    polygon, box, edges = shape
    if (
        max(p[0] for p in triangle) < box[0] or min(p[0] for p in triangle) > box[2]
        or max(p[1] for p in triangle) < box[1] or min(p[1] for p in triangle) > box[3]
    ):
        return False
    return (
        any(point_in_polygon(p, polygon) for p in triangle)
        or any(segments_intersect(triangle[k - 1], triangle[k], a, b) for k in range(3) for a, b in edges)
        or point_in_polygon(polygon[0], triangle)
    )


def _min_bend_radius(mesh: Mesh, chart: Chart, frame: BaseFrame, polygon_base: Sequence, min_radius_mm: float) -> float:
    """The tightest bend (surface.bend) at an edge under the polygon, for a sheet of ``min_radius_mm``."""

    from engine.geometry import point_in_polygon, segments_intersect

    smallest = math.inf
    in_chart = set(chart.facets)
    for f in chart.facets:
        for g in mesh.neighbors[f]:
            if g <= f or g not in in_chart:
                continue
            radius = bend.edge_radius(mesh, f, g, min_radius_mm)
            if radius >= smallest or radius == math.inf:
                continue
            va, vb = bend.edge_geometry(mesh, f, g)[3]
            a = frame.to_base(chart.uv[va])
            b = frame.to_base(chart.uv[vb])
            crosses = point_in_polygon(a, polygon_base) or point_in_polygon(b, polygon_base) or any(
                segments_intersect(a, b, polygon_base[k - 1], polygon_base[k]) for k in range(len(polygon_base))
            )
            if crosses:
                smallest = radius
    return smallest


# --------------------------------------------------------------------------
# Wrap template (1:1 SVG, mm)
# --------------------------------------------------------------------------


def wrap_template(chart: Chart, frame: BaseFrame, outlines: Mapping[str, Sequence], taxels: Sequence, origin: Sequence[float]) -> str:
    """A 1:1 SVG of the flattened surface with both boards and the taxel centres (base frame, y up)."""

    surface = [frame.to_base(p) for p in chart.outline()]
    everything = surface + [p for polygon in outlines.values() for p in polygon]
    xs = [p[0] for p in everything]
    ys = [p[1] for p in everything]
    pad = 3.0
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    width, height = x1 - x0, y1 - y0

    def path(points: Sequence) -> str:
        return " ".join(f"{'M' if i == 0 else 'L'}{p[0] - x0:.3f},{y1 - p[1]:.3f}" for i, p in enumerate(points)) + " Z"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}mm" height="{height:.3f}mm" viewBox="0 0 {width:.3f} {height:.3f}" data-view="wrap-template">',
        f'<path d="{path(surface)}" fill="none" stroke="#555" stroke-width="0.15"/>',
        f'<path d="{path(outlines["column"])}" fill="none" stroke="#1f77b4" stroke-width="0.12"/>',
        f'<path d="{path(outlines["row"])}" fill="none" stroke="#d62728" stroke-width="0.12" stroke-dasharray="0.6 0.3"/>',
        f'<path d="{path(outlines["field"])}" fill="none" stroke="#2ca02c" stroke-width="0.1"/>',
        f'<line x1="{0 - x0:.3f}" y1="{y1 - 0:.3f}" x2="{frame.length * frame.side_dir[0] - x0:.3f}" y2="{y1 - frame.length * frame.side_dir[1]:.3f}" stroke="#000" stroke-width="0.2"/>',
    ]
    for item in taxels:
        cx = origin[0] + item["x"] - x0
        cy = y1 - (origin[1] + item["y"])
        parts.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="0.15" fill="#2ca02c"/>')
    for x, y in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 1), (x1 - 1, y1 - 1)):
        sx, sy = x - x0, y1 - y
        parts.append(f'<path d="M{sx - 1:.3f},{sy:.3f} L{sx + 1:.3f},{sy:.3f} M{sx:.3f},{sy - 1:.3f} L{sx:.3f},{sy + 1:.3f}" stroke="#000" stroke-width="0.1"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def _r(value: float, digits: int = 6) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0 else rounded

