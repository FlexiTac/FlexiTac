"""CAD-mode requests: one function per route, shared by the HTTP server and the CLI.

Every request is self-contained: it carries the mesh bytes and a JSON
header, and the reply is computed from them alone (no mesh is kept between
requests).  The wire format of the HTTP routes is::

    4 bytes   big-endian length L of the JSON header
    L bytes   the JSON header (UTF-8)
    rest      the mesh file (binary or ASCII STL)

The JSON header holds ``unit`` (optional: m, cm, mm, in; default: the
guess), ``name`` (optional) and the route's own fields.
"""

from __future__ import annotations

import copy
import hashlib
import math
import re
import struct
import threading
from collections import OrderedDict
from typing import Any, Mapping

from . import chart as chart_module
from . import select
from .errors import SurfaceError
from .mesh import Mesh, dist2, hypot2, read_stl

FORMAT_VERSION = "tactile-surface/v1"
MAX_HEADER_BYTES = 8 * 1024 * 1024
MAX_NUMBER_DIGITS = 4300
# A match may start only where a run of digits starts: searching from every digit of a
# shorter run costs the square of its length (seconds on a header of long numbers).
_LONG_NUMBER = re.compile(rb"(?<![0-9])[0-9]{%d}" % (MAX_NUMBER_DIGITS + 1))
SIDE_ANGLE_DEG = 1.0


def split_body(body: bytes) -> tuple:
    """(header bytes, mesh bytes) of a framed surface request."""

    if len(body) < 4:
        raise SurfaceError("E_SURFACE_REQUEST", "The body must start with the 4-byte length of its JSON header.")
    length = struct.unpack(">I", body[:4])[0]
    if length > MAX_HEADER_BYTES or 4 + length > len(body):
        raise SurfaceError("E_SURFACE_REQUEST", f"The JSON header length {length} does not fit the body.")
    header = body[4 : 4 + length]
    # Python before 3.11 parses a long integer literal in quadratic time while
    # holding the interpreter: refuse one before parsing (3.11+ caps it anyway).
    if _LONG_NUMBER.search(header):
        raise SurfaceError("E_SURFACE_REQUEST", f"The JSON header holds a number with more than {MAX_NUMBER_DIGITS} digits.")
    return header, body[4 + length :]


def frame(header: Mapping[str, Any], mesh_bytes: bytes) -> bytes:
    """Build a framed request body (clients, tests and the CLI)."""

    import json

    encoded = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded + mesh_bytes


MESH_CACHE_SIZE = 4
# Meshes beyond this many facets in all are evicted (the newest one always stays).  A
# facet holds about 600 bytes; its edges' bend measurements (surface.bend, filled by the
# surface preset, the fit and the map) about 300 bytes each, so two count as one facet.
MESH_CACHE_FACETS = 1_500_000
_MESH_CACHE: "OrderedDict[tuple, Mesh]" = OrderedDict()
_GUESSED_UNITS: "OrderedDict[str, str]" = OrderedDict()
_MESH_LOCK = threading.Lock()


def load_mesh(header: Mapping[str, Any], mesh_bytes: bytes) -> Mesh:
    """The parsed mesh of a request, from a small in-memory cache keyed by the bytes' SHA-256.

    The routes are stateless (every request carries the mesh); the cache only
    saves re-parsing the same file for its select, fit and map requests.
    Nothing is written to disk.
    """

    unit = header.get("unit")
    if unit is not None and not isinstance(unit, str):
        raise SurfaceError("E_SURFACE_UNIT", "unit must be a string.")
    name = header.get("name", "")
    if not isinstance(name, str):
        raise SurfaceError("E_SURFACE_REQUEST", "name must be a string.")
    sha256 = hashlib.sha256(mesh_bytes).hexdigest()
    with _MESH_LOCK:
        # The key is the resolved unit: no unit means the guessed one.
        key = (sha256, unit if unit is not None else _GUESSED_UNITS.get(sha256))
        mesh = _MESH_CACHE.get(key)
        if mesh is not None:
            _MESH_CACHE.move_to_end(key)
    if mesh is None:
        mesh = read_stl(mesh_bytes, unit=unit)
        with _MESH_LOCK:
            if unit is None:
                _GUESSED_UNITS[sha256] = mesh.unit
                while len(_GUESSED_UNITS) > 64:
                    _GUESSED_UNITS.popitem(last=False)
            _MESH_CACHE[(sha256, mesh.unit)] = mesh
    with _MESH_LOCK:
        # On every request: the cached meshes' bend measurements grow after they are parsed.
        while len(_MESH_CACHE) > 1 and (
            len(_MESH_CACHE) > MESH_CACHE_SIZE or sum(_cache_weight(m) for m in _MESH_CACHE.values()) > MESH_CACHE_FACETS
        ):
            _MESH_CACHE.popitem(last=False)
    if name and mesh.name != name[:200]:
        mesh = copy.copy(mesh)
        mesh.name = name[:200]
    return mesh


def _cache_weight(mesh: Mesh) -> int:
    """A cached mesh's memory in facets: its facets and its bend measurements (two per facet's worth)."""

    return mesh.facet_count + len(mesh.bend_cache) // 2


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


def inspect(header: Mapping[str, Any], mesh_bytes: bytes, cache: Any = None) -> dict:
    """Mesh facts and the candidate surfaces (flat and smooth presets)."""

    _keys(header, {"unit", "name"}, "inspect")
    mesh = load_mesh(header, mesh_bytes)
    return {
        "ok": True,
        "format": FORMAT_VERSION,
        # Floats are rounded to 1e-6 like every other reply.
        "mesh": _round_tree(mesh.summary()),
        "hidden_facets": sorted(mesh.hidden),
        "candidates": {
            preset: _round_tree(select.candidates(mesh, preset=preset)) for preset in ("surface", "flat", "smooth")
        },
    }


def select_surface(header: Mapping[str, Any], mesh_bytes: bytes, cache: Any = None) -> dict:
    """Apply the selection operations and flatten the result into a chart."""

    _keys(header, {"unit", "name", "selection"}, "select")
    mesh = load_mesh(header, mesh_bytes)
    facets, chart = selection_chart(mesh, header.get("selection"))
    selection = describe_selection(mesh, facets, chart)
    if chart.kind == "curved":
        # How far a curved selection stretches on the part (2026-11-17): the fit refuses it beyond the strain limit
        # (``smooth_max``, the relaxed sheet's stretch smoothed over 1 mm; ``facet_max`` its largest facet's), so the page
        # can say so, and offer Shrink to fit, as soon as it is selected; ``centre_facet``, the facet nearest its area
        # centroid, which the page clicks again at the other strain limit (the dome's patch from its own middle, the
        # user's feedback of 2026-11-17: symmetric at either limit, whichever click on it made it).
        selection["stretch"] = {"smooth_max": _r(chart_module.judged_stretch(chart, mesh), 9), "facet_max": _r(chart_module.relaxed_max(chart, mesh), 9),
                                "centre_facet": centre_facet(mesh, chart.facets, select.click_face(mesh, header["selection"]["ops"]))}
    return {
        "ok": True,
        "format": FORMAT_VERSION,
        "mesh": {"sha256": mesh.sha256, "unit": mesh.unit, "facets": mesh.facet_count},
        "selection": selection,
    }


def fit(header: Mapping[str, Any], mesh_bytes: bytes, cache: Any = None) -> dict:
    """Propose sensor designs for the selection (see ``surface.fit``)."""

    from . import fit as fit_module

    return fit_module.fit_route(header, mesh_bytes, cache=cache)


def map_placement(header: Mapping[str, Any], mesh_bytes: bytes, cache: Any = None) -> dict:
    """Map a generated design onto the part: taxel map, overlay and wrap template (see ``surface.place``)."""

    from . import place

    return place.map_route(header, mesh_bytes, cache=cache)


def centre_facet(mesh: Mesh, facets, face=None) -> int:
    """The facet whose centroid is nearest the facets' area centroid (the lowest id on a tie); of those in ``face`` (the
    click's face, :func:`surface.select.click_face`) when any is: a hole the stretch selection filled with the part's
    facets bent tighter than the face's blend radius (surface.select.fill_holes) holds none a click grows the face from."""

    ordered = sorted(facets)
    total = math.fsum(mesh.areas[f] for f in ordered)
    mid = [math.fsum(mesh.centroids[f][k] * mesh.areas[f] for f in ordered) / total for k in range(3)]
    candidates = [f for f in ordered if face is not None and f in face] or ordered
    return min(candidates, key=lambda f: (math.fsum((mesh.centroids[f][k] - mid[k]) ** 2 for k in range(3)), f))


def selection_chart(mesh: Mesh, selection: Any) -> tuple:
    if not isinstance(selection, Mapping):
        raise SurfaceError("E_SURFACE_REQUEST", "selection must be an object with 'ops'.")
    unknown = sorted(set(selection) - {"ops"})
    if unknown:
        raise SurfaceError("E_SURFACE_REQUEST", f"selection has unknown keys: {', '.join(unknown)}.")
    ops = selection.get("ops")
    facets = select.apply_operations(mesh, ops)
    seed = next((op.get("seed_facet") for op in ops if isinstance(op, Mapping) and op.get("op") in ("grow", "disk")), None)
    try:
        chart = chart_module.build_chart(mesh, facets, seed=seed)
    except SurfaceError as error:
        # The client can show which facets could not be flattened.
        error.details.setdefault("facets", sorted(facets))
        raise
    # A band opened along a seam drops the seam's facets from the selection.
    return set(chart.facets), chart


def describe_selection(mesh: Mesh, facets, chart) -> dict:
    stats = {k: v for k, v in chart.stats.items() if not k.startswith("_")}
    ordered = sorted(facets)
    return {
        "facets": ordered,
        # Per facet (aligned with ``facets``) its three vertices' uv in mesh order: the browser maps uv and 3D points
        # barycentrically inside a facet (the border editor, surface.border).
        "facets_uv": [[[_r(u), _r(v)] for u, v in chart.facet_uv(facet, mesh)] for facet in ordered],
        "area_mm2": _r(stats["area_mm2"]),
        "kind": chart.kind,
        "method": chart.method,
        "normal": [_r(x, 9) for x in chart.normal],
        "outline_uv": [[_r(x), _r(y)] for x, y in chart.outline()],
        "holes_uv": [[[_r(x), _r(y)] for x, y in hole] for hole in chart.holes()],
        "outline_xyz": [[_r(c) for c in mesh.vertices[v]] for v in chart.loops[chart.outer]],
        "sides": boundary_sides(mesh, chart, mirror_traces(mesh, chart)),
        "stats": _round_tree(stats),
    }


def mirror_traces(mesh: Mesh, chart) -> list:
    """A doubly curved selection's mirror planes' traces in its chart (surface.chart.mirror_traces; the review of
    2026-11-17, findings 2 and 4), or none: only a curved chart stretched beyond the curved chart's gate
    (surface.fit.AXIS_MIN_STRETCH, the page's own: a planar, developable or nearly flat face, every face of the Library,
    is fitted as before) whose selection is its own mirror image (surface.select.mirror_maps).  Kept on the chart."""

    from . import fit as fit_module

    if chart.kind != "curved":
        return []
    cached = chart.stats.get("_mirror")
    if cached is None:
        cached = []
        if chart_module.judged_stretch(chart, mesh) > fit_module.AXIS_MIN_STRETCH:
            cached = chart_module.mirror_traces(mesh, chart, select.mirror_maps(mesh, chart.facets))
        chart.stats["_mirror"] = cached
    return cached


def boundary_sides(mesh: Mesh, chart, traces=()) -> list:
    """The outer boundary split into straight sides (segments within 1 degree of the side's first).

    Each side gives its uv end points, 3D end points, length and the inward
    unit normal in uv; a side is a candidate base (tail exit) edge.  With a
    mirror plane's trace (:func:`mirror_traces`; of several, the one along
    the outline's long axis) the split is symmetric about it
    (:func:`_mirrored_runs`).
    """

    loop = chart.loops[chart.outer]
    points = [chart.uv[v] for v in loop]
    count = len(points)
    if count < 3:
        return []
    directions = []
    for i in range(count):
        a, b = points[i], points[(i + 1) % count]
        directions.append(math.atan2(b[1] - a[1], b[0] - a[0]))
    limit = math.radians(SIDE_ANGLE_DEG)

    def turn(i: int) -> float:
        d = directions[i] - directions[i - 1]
        return abs((d + math.pi) % (2 * math.pi) - math.pi)

    runs = None
    if traces:
        from . import fit as fit_module

        long = fit_module.principal_axes(chart)[0]
        trace = max(traces, key=lambda t: abs(t["direction"][0] * long[0] + t["direction"][1] * long[1]))
        runs = _mirrored_runs(points, directions, limit, trace)
    if runs is None:
        # Start at the first corner so no side wraps around the loop's start.  A
        # side ends at a corner, or where its direction has drifted more than the
        # limit from its first segment (a finely faceted fillet is many short sides,
        # not one side that swallows the straight edges next to it).
        corners = [i for i in range(count) if turn(i) > limit]
        start = corners[0] if corners else 0
        runs = []
        for step in range(count):
            i = (start + step) % count
            if not runs:
                runs.append([i])
                continue
            drift = directions[i] - directions[runs[-1][0]]
            drift = abs((drift + math.pi) % (2 * math.pi) - math.pi)
            if turn(i) > limit or drift > limit:
                runs.append([i])
            else:
                runs[-1].append(i)
    sides = []
    for indices in runs:
        first, last = points[indices[0]], points[(indices[-1] + 1) % count]
        length = math.fsum(dist2(points[j], points[(j + 1) % count]) for j in indices)
        dx, dy = last[0] - first[0], last[1] - first[1]
        chord = hypot2(dx, dy)
        # Counter-clockwise outer loop: the inside is on the left.
        inward = (-dy / chord, dx / chord) if chord > 0 else (0.0, 0.0)
        sides.append(
            {
                "index": len(sides),
                "from_uv": [_r(first[0]), _r(first[1])],
                "to_uv": [_r(last[0]), _r(last[1])],
                "from_xyz": [_r(c) for c in mesh.vertices[loop[indices[0]]]],
                "to_xyz": [_r(c) for c in mesh.vertices[loop[(indices[-1] + 1) % count]]],
                "length_mm": _r(length),
                "chord_mm": _r(chord),
                "straight": abs(length - chord) <= 1e-6 * max(length, 1.0) + 1e-9,
                "inward_uv": [_r(inward[0], 9), _r(inward[1], 9)],
                # Segment i of the outer loop runs from point i to point i + 1.
                "edges": list(indices),
            }
        )
    return sides


def _mirrored_runs(points: list, directions: list, limit: float, trace: Mapping[str, Any]) -> Any:
    """The outline's sides split symmetrically about a mirror plane's trace (the review of 2026-11-17, finding 4: the
    Dex3-1 dome's base end was split at the plane into two halves, the auto base taking one), as runs of segment
    indices counter-clockwise, or None when the outline does not cross the trace twice.

    At each of its two crossings the segments that run within ``limit`` of square across the trace, walking out from
    it both ways, make one side (a segment the trace crosses is one of them); between them each half of the outline
    is split by the drift rule (:func:`boundary_sides`) walking from the first crossing, the other half the same way
    round, so its sides are the first half's mirror images."""

    count = len(points)
    (pu, pv), (du, dv) = trace["point"], trace["direction"]
    across = [(p[0] - pu) * dv - (p[1] - pv) * du for p in points]
    along = [(p[0] - pu) * du + (p[1] - pv) * dv for p in points]
    tiny = 1e-9 * max(1.0, max(abs(a) for a in along))
    crossings = []  # (along the trace, vertex or None, segment or None)
    for i in range(count):
        j = (i + 1) % count
        if abs(across[i]) <= tiny:
            crossings.append((along[i], i, None))
        elif abs(across[j]) > tiny and (across[i] < 0) != (across[j] < 0):
            t = across[i] / (across[i] - across[j])
            crossings.append((along[i] + t * (along[j] - along[i]), None, i))
    if len(crossings) != 2:
        return None
    crossings.sort()
    (_, first_vertex, first_segment), (_, last_vertex, last_segment) = crossings

    def walk(step: int) -> list:
        """The segments from the first crossing to the last, one way round, each with its direction walked that way."""

        if first_vertex is not None:
            k = first_vertex if step > 0 else (first_vertex - 1) % count
        else:
            k = (first_segment + step) % count
        found = []
        while True:
            if last_vertex is not None and (k if step > 0 else (k + 1) % count) == last_vertex:
                break
            if last_segment is not None and k == last_segment:
                break
            if first_segment is not None and k == first_segment or len(found) > count:
                return []
            direction = directions[k] if step > 0 else directions[k] + math.pi
            found.append((k, direction))
            k = (k + step) % count
        return found

    def gap(a: float, b: float) -> float:
        d = a - b
        return abs((d + math.pi) % (2 * math.pi) - math.pi)

    halves = [walk(1), walk(-1)]
    if not halves[0] or not halves[1]:
        return None
    # Square across the trace, walking away from it: on half h at the first crossing, and towards it at the last.
    # (across > 0 lies along (dv, -du).)
    away = [math.atan2(-du, dv) if (across[halves[h][0][0]] + across[(halves[h][0][0] + 1) % count]) > 0 else math.atan2(du, -dv)
            for h in (0, 1)]

    def leading(half: list, reference: float) -> int:
        n = 0
        while n < len(half) and gap(half[n][1], reference) <= limit:
            n += 1
        return n

    starts = [leading(halves[h], away[h]) for h in (0, 1)]
    ends = [leading([(k, d + math.pi) for k, d in reversed(halves[h])], away[h]) for h in (0, 1)]
    if any(starts[h] + ends[h] > len(halves[h]) for h in (0, 1)):
        # The central sides would meet: one side per half.
        starts = [min(starts[h], len(halves[h])) for h in (0, 1)]
        ends = [len(halves[h]) - starts[h] for h in (0, 1)]
    middles = []
    for h in (0, 1):
        runs: list = []
        for k, direction in halves[h][starts[h]:len(halves[h]) - ends[h]]:
            if runs and gap(direction, runs[-1][-1][1]) <= limit and gap(direction, runs[-1][0][1]) <= limit:
                runs[-1].append((k, direction))
            else:
                runs.append([(k, direction)])
        middles.append([[k for k, _ in run] for run in runs])
    # Counter-clockwise: the first crossing's side, the first half's runs, the last crossing's side, the second half's
    # runs (walked clockwise: each reversed, in reverse order).
    second = [list(reversed(run)) for run in reversed(middles[1])]
    head = [k for k, _ in reversed(halves[1][:starts[1]])] + ([first_segment] if first_segment is not None else [])
    head += [k for k, _ in halves[0][:starts[0]]]
    tail = [k for k, _ in halves[0][len(halves[0]) - ends[0]:]] + ([last_segment] if last_segment is not None else [])
    tail += [k for k, _ in reversed(halves[1][len(halves[1]) - ends[1]:])]
    runs = ([head] if head else []) + middles[0] + ([tail] if tail else []) + second
    if sorted(k for run in runs for k in run) != list(range(count)):
        return None
    return runs


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _keys(header: Mapping[str, Any], allowed: set, route: str) -> None:
    if not isinstance(header, Mapping):
        raise SurfaceError("E_SURFACE_REQUEST", "The JSON header must be an object.")
    unknown = sorted(set(header) - allowed)
    if unknown:
        raise SurfaceError("E_SURFACE_REQUEST", f"Unknown keys for {route}: {', '.join(unknown)}.")


def _r(value: float, digits: int = 6) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0 else rounded


def _round_tree(value: Any) -> Any:
    if isinstance(value, float):
        return _r(value)
    if isinstance(value, dict):
        return {k: _round_tree(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_round_tree(v) for v in value]
    return value
