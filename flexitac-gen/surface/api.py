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
    return {
        "ok": True,
        "format": FORMAT_VERSION,
        "mesh": {"sha256": mesh.sha256, "unit": mesh.unit, "facets": mesh.facet_count},
        "selection": describe_selection(mesh, facets, chart),
    }


def fit(header: Mapping[str, Any], mesh_bytes: bytes, cache: Any = None) -> dict:
    """Propose sensor designs for the selection (see ``surface.fit``)."""

    from . import fit as fit_module

    return fit_module.fit_route(header, mesh_bytes, cache=cache)


def map_placement(header: Mapping[str, Any], mesh_bytes: bytes, cache: Any = None) -> dict:
    """Map a generated design onto the part: taxel map, overlay and wrap template (see ``surface.place``)."""

    from . import place

    return place.map_route(header, mesh_bytes, cache=cache)


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
        "sides": boundary_sides(mesh, chart),
        "stats": _round_tree(stats),
    }


def boundary_sides(mesh: Mesh, chart) -> list:
    """The outer boundary split into straight sides (segments within 1 degree of the side's first).

    Each side gives its uv end points, 3D end points, length and the inward
    unit normal in uv; a side is a candidate base (tail exit) edge.
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
