"""STL input for CAD mode: read, check, weld and build the facet topology.

Pure standard library.  Facet ids are the facets' order in the file, so a
facet picked in the browser (a non-indexed three.js geometry in file order)
is the same facet here.  Vertices are welded on their exact stored values
(float32 in a binary STL): the crank tip's shortest edge is 0.4 um, and a
1 um weld tolerance already merges distinct vertices there.

Coordinates are converted to millimetres with the unit scale and stay in the
STL's own frame; nothing is recentred.
"""

from __future__ import annotations

import bisect
import hashlib
import heapq
import math
import re
import struct
from dataclasses import dataclass, field
from typing import Any, Sequence

from .errors import SurfaceError

UNIT_SCALES_MM = {"m": 1000.0, "cm": 10.0, "mm": 1.0, "in": 25.4}
MAX_FACETS = 1_000_000
# Coordinates (after the unit scale) are at most this far from the origin
# (1000 km): an ASCII STL can hold any finite number, and squares of 1e154 or
# more overflow the geometry.
MAX_COORDINATE_MM = 1e9
# A part smaller than this (largest extent) is most likely read in the wrong unit.
SMALL_PART_MM = 2.0
# A binary STL is 80 header bytes, a uint32 count, then 50 bytes per facet.
_BINARY_HEADER = 84
_BINARY_FACET = 50
# Below this area (mm2) a facet has no usable normal.
DEGENERATE_AREA_MM2 = 1e-12
# Covered-facet detection: nearly coplanar, opposite-facing facets that overlap.
# The lengths and the area are for parts of at least _COVER_FULL_SIZE_MM
# (bounding-box diagonal); a smaller part (a file in metres read as mm) scales
# them down with its size.
_PLANE_NORMAL_QUANTUM = 0.05
_PLANE_OFFSET_QUANTUM_MM = 0.05
_PLANE_DISTANCE_MM = 0.05
_OPPOSITE_COS = 0.9995  # the normals are opposite within about 1.8 degrees
_OVERLAP_MIN_AREA_MM2 = 1e-4
_COVER_CELL_MM = 0.5
_COVER_FULL_SIZE_MM = 20.0
_PAIRWISE_LIMIT = 4096
_GRID_CELLS_PER_FACET = 64
# At most this many overlapping pairs are clipped; a pathological file (many
# facets stacked on one spot) stops the search there, with a warning.
MAX_COVER_PAIRS = 400_000
# A boundary vertex this close to another facet's boundary edge splits it (a
# T-junction, common in CAD exports): the facets on both sides are linked.
T_JUNCTION_TOLERANCE_MM = 1e-3
MAX_CRACK_EDGES = 200_000
# Vertex tests and grid-cell visits of the T-junction search, over the whole file.
MAX_CRACK_TESTS = 2_000_000
# An edge is walked in at most about _CRACK_STEPS pieces on a grid whose
# cells are _CRACK_LEVEL times larger per level; a cell holding more than
# _CRACK_CROWDED boundary vertices is walked again on the finer grid, down to
# cells of _CRACK_FINEST_MM, where it is a spot where too many open edges meet
# (skipped, with a warning).
_CRACK_STEPS = 16
_CRACK_LEVEL = 8
_CRACK_CROWDED = 64
_CRACK_FINEST_MM = 10 * T_JUNCTION_TOLERANCE_MM
# The grids are shifted by this fraction of a cell, so that faces at round
# coordinates (z = 0) do not lie on cell boundaries.
_CRACK_PHASE = 1 / math.pi
# Box comparisons, open-edge twin tests and ray-facet tests to tell cavities
# from parts, over the whole file.
MAX_NESTING_TESTS = 2_000_000
_NESTING_PROBES = 3
# Facets round a non-manifold edge within this angle lie on one another
# (coincident walls); the same angle as _OPPOSITE_COS.
_TIE_ANGLE = math.acos(_OPPOSITE_COS)
# A facet covered over at least this fraction of its area is hidden.
HIDDEN_FRACTION = 0.99

Vector = tuple  # (x, y, z)


@dataclass
class Mesh:
    """A welded triangle mesh in millimetres, in the STL's own frame."""

    name: str
    sha256: str
    source_format: str
    unit: str
    unit_guess: str
    scale_mm: float
    vertices: list
    facets: list
    normals: list
    areas: list
    centroids: list
    neighbors: list
    shell: list
    degenerate: frozenset
    hidden: frozenset
    covered: dict
    boundary_edges: list
    stats: dict
    # T-junction links: (f, g) -> (edge of f, edge of g), two collinear edges that overlap.
    cracks: dict = field(default_factory=dict)
    # A boundary edge (start, end) of a facet -> the vertices of other facets lying on it, in order.
    edge_splits: dict = field(default_factory=dict)
    # surface.bend's per-edge measurements, filled on demand (at most one per edge).
    bend_cache: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def facet_count(self) -> int:
        return len(self.facets)

    def usable(self, facet: int) -> bool:
        """True for a facet that may be selected: not degenerate, not hidden."""

        return facet not in self.degenerate and facet not in self.hidden

    def facet_points(self, facet: int) -> tuple:
        a, b, c = self.facets[facet]
        return self.vertices[a], self.vertices[b], self.vertices[c]

    def summary(self) -> dict[str, Any]:
        """The mesh facts a client shows before anything is selected."""

        return {
            "name": self.name,
            "sha256": self.sha256,
            "format": self.source_format,
            "unit": self.unit,
            "unit_guess": self.unit_guess,
            "scale_to_mm": self.scale_mm,
            **{k: v for k, v in self.stats.items() if not k.startswith("_")},
        }


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------


def read_stl(data: bytes, *, name: str = "", unit: str | None = None, max_facets: int = MAX_FACETS) -> Mesh:
    """Parse an STL (binary or ASCII), weld it and build its topology.

    ``unit`` is the unit of the file's coordinates; ``None`` takes the guess
    (largest extent under 2 means metres, otherwise millimetres).
    """

    if not isinstance(data, (bytes, bytearray)):
        raise SurfaceError("E_SURFACE_REQUEST", "The STL must be bytes.")
    data = bytes(data)
    if unit is not None and unit not in UNIT_SCALES_MM:
        raise SurfaceError("E_SURFACE_UNIT", f"Unit {unit!r} is not one of {', '.join(UNIT_SCALES_MM)}.")
    triangles, source_format = _triangles(data, max_facets)
    if not triangles:
        raise SurfaceError("E_SURFACE_MESH_EMPTY")
    raw_vertices: list = []
    index: dict = {}
    facets: list = []
    for triangle in triangles:
        ids = []
        for point in triangle:
            key = point
            found = index.get(key)
            if found is None:
                found = len(raw_vertices)
                index[key] = found
                raw_vertices.append(key)
            ids.append(found)
        facets.append((ids[0], ids[1], ids[2]))
    lows = [min(point[axis] for point in raw_vertices) for axis in range(3)]
    highs = [max(point[axis] for point in raw_vertices) for axis in range(3)]
    guess = _unit_guess(lows, highs)
    chosen = unit or guess
    scale = UNIT_SCALES_MM[chosen]
    # The extreme coordinates bound every other one (scaling is monotonic).
    if max(abs(value) for value in lows + highs) * scale > MAX_COORDINATE_MM:
        _refuse_far_coordinate(triangles, scale)
    vertices = [(x * scale, y * scale, z * scale) for x, y, z in raw_vertices]
    return _build(
        name=name,
        sha256=hashlib.sha256(data).hexdigest(),
        source_format=source_format,
        unit=chosen,
        unit_guess=guess,
        scale=scale,
        vertices=vertices,
        facets=facets,
    )


def _refuse_far_coordinate(triangles: Sequence, scale: float) -> None:
    for index, triangle in enumerate(triangles):
        for point in triangle:
            for value in point:
                if abs(value) * scale > MAX_COORDINATE_MM:
                    raise SurfaceError(
                        "E_SURFACE_MESH_NONFINITE",
                        f"Triangle {index} has a coordinate of {value * scale:.3g} mm; at most "
                        f"{MAX_COORDINATE_MM:.0e} mm from the origin is accepted.",
                    )


def mesh_from_triangles(
    triangles: Sequence[Sequence[Sequence[float]]], *, name: str = "synthetic", unit: str = "mm"
) -> Mesh:
    """Build a mesh from triangles (tests and generated parts), as if read from a binary STL."""

    return read_stl(binary_stl(triangles), name=name, unit=unit)


def binary_stl(triangles: Sequence[Sequence[Sequence[float]]], header: bytes = b"") -> bytes:
    """Write triangles as a binary STL (float32, zero normals, zero attribute bytes)."""

    parts = [header[:80].ljust(80, b"\0"), struct.pack("<I", len(triangles))]
    for triangle in triangles:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = triangle
        parts.append(struct.pack("<12fH", 0.0, 0.0, 0.0, ax, ay, az, bx, by, bz, cx, cy, cz, 0))
    return b"".join(parts)


def _triangles(data: bytes, max_facets: int) -> tuple:
    count = struct.unpack("<I", data[80:84])[0] if len(data) >= _BINARY_HEADER else None
    if count is not None and _BINARY_HEADER + _BINARY_FACET * count == len(data):
        return _binary_triangles(data, count, max_facets), "binary"
    if _looks_ascii(data):
        return _ascii_triangles(data, max_facets), "ascii"
    if count is not None and _BINARY_HEADER + _BINARY_FACET * count > len(data):
        raise SurfaceError(
            "E_SURFACE_MESH_TRUNCATED",
            f"The binary STL announces {count} triangles ({_BINARY_HEADER + _BINARY_FACET * count} bytes) "
            f"but has {len(data)} bytes.",
        )
    if count is not None and count > 0 and (len(data) - _BINARY_HEADER) // _BINARY_FACET >= count:
        # Some exporters pad a binary STL; the announced triangles are complete.
        return _binary_triangles(memoryview(data)[: _BINARY_HEADER + _BINARY_FACET * count], count, max_facets), "binary"
    raise SurfaceError("E_SURFACE_MESH_FORMAT")


def _binary_triangles(data: bytes, count: int, max_facets: int) -> list:
    if count > max_facets:
        raise SurfaceError("E_SURFACE_MESH_TOO_LARGE", f"{count} triangles; at most {max_facets} are accepted.")
    triangles = []
    isfinite = math.isfinite
    for record in struct.iter_unpack("<12fH", memoryview(data)[_BINARY_HEADER:]):
        values = record[3:12]
        if not all(isfinite(value) for value in values):
            raise SurfaceError("E_SURFACE_MESH_NONFINITE", f"Triangle {len(triangles)} has a non-finite coordinate.")
        triangles.append((values[0:3], values[3:6], values[6:9]))
    return triangles


def _looks_ascii(data: bytes) -> bool:
    head = data[:512].lstrip(b"\xef\xbb\xbf").lstrip()
    return head[:5].lower() == b"solid" and b"\0" not in data[:512]


def _ascii_triangles(data: bytes, max_facets: int) -> list:
    try:
        data.decode("utf-8-sig")  # validity only; the tokens are read from the bytes
    except UnicodeDecodeError as exc:
        raise SurfaceError("E_SURFACE_MESH_FORMAT", "The ASCII STL is not valid ASCII/UTF-8.") from exc
    # Tokens are read one at a time: a large or malformed file never becomes a
    # list of millions of strings, and junk is refused at its first token.
    words = [_TOKEN.finditer(data, 3 if data.startswith(b"\xef\xbb\xbf") else 0)]
    triangles = []
    current = [next(words[0], None)]  # the current token's match

    def peek() -> Any:
        return None if current[0] is None else current[0].group().lower()

    def advance() -> None:
        current[0] = next(words[0], None)

    def expect(word: str) -> None:
        if peek() != word.encode("ascii"):
            found = "end of file" if current[0] is None else current[0].group()[:40].decode("utf-8", "replace")
            raise SurfaceError("E_SURFACE_MESH_FORMAT", f"Expected '{word}' in the ASCII STL, found {found!r}.")
        advance()

    def number() -> float:
        if current[0] is None:
            raise SurfaceError("E_SURFACE_MESH_FORMAT", "The ASCII STL ends inside a facet.")
        token = current[0].group()
        try:
            value = float(token)
        except ValueError as exc:
            raise SurfaceError("E_SURFACE_MESH_FORMAT", f"{token[:40].decode('utf-8', 'replace')!r} is not a number.") from exc
        if not math.isfinite(value):
            raise SurfaceError("E_SURFACE_MESH_NONFINITE", f"Triangle {len(triangles)} has a non-finite coordinate.")
        advance()
        return value

    # The last line break followed by a token (-1: the file is written on one line).
    content_end = len(data.rstrip())
    last_break = max(data.rfind(b"\n", 0, content_end), data.rfind(b"\r", 0, content_end))

    def expect_line(word: str, stops) -> None:
        # 'solid' or 'endsolid' and the rest of its line, the solid's name (ASCII
        # STL is line-oriented: the name may hold any word, 'solid' or 'facet' too).
        # With ``stops`` (a solid written on one line), the name is the words up
        # to the first of them.
        match = current[0]
        if peek() != word.encode("ascii"):
            expect(word)  # raises
        start = match.end()
        if stops:
            advance()
            while current[0] is not None and peek() not in stops:
                if current[0].end() - start > _MAX_NAME_BYTES:
                    raise SurfaceError("E_SURFACE_MESH_FORMAT", f"The solid's name after '{word}' in the ASCII STL is longer than {_MAX_NAME_BYTES} bytes.")
                advance()
            return
        line_end = _LINE_END.search(data, start, start + _MAX_NAME_BYTES + 1)
        end = len(data) if line_end is None else line_end.start()
        if end - start > _MAX_NAME_BYTES:
            raise SurfaceError("E_SURFACE_MESH_FORMAT", f"The '{word}' line of the ASCII STL is longer than {_MAX_NAME_BYTES} bytes.")
        words[0] = _TOKEN.finditer(data, end)
        advance()

    while current[0] is not None:
        # No line follows the word 'solid': the solid is written on one line.
        one_line = last_break < current[0].end()
        expect_line("solid", (b"facet", b"endsolid") if one_line else None)
        while peek() == b"facet":
            advance()
            expect("normal")
            number(), number(), number()
            expect("outer")
            expect("loop")
            corners = []
            for _ in range(3):
                expect("vertex")
                corners.append((number(), number(), number()))
            expect("endloop")
            expect("endfacet")
            triangles.append(tuple(corners))
            if len(triangles) > max_facets:
                raise SurfaceError("E_SURFACE_MESH_TOO_LARGE", f"More than {max_facets} triangles.")
        # The end line may repeat the solid's name.
        expect_line("endsolid", (b"solid",) if one_line else None)
    return triangles


_TOKEN = re.compile(rb"\S+")
_LINE_END = re.compile(rb"[\r\n]")
_MAX_NAME_BYTES = 4096


def _unit_guess(lows: Sequence[float], highs: Sequence[float]) -> str:
    extent = max(highs[axis] - lows[axis] for axis in range(3))
    return "m" if extent < 2.0 else "mm"


# --------------------------------------------------------------------------
# Topology
# --------------------------------------------------------------------------


def _build(*, name, sha256, source_format, unit, unit_guess, scale, vertices, facets) -> Mesh:
    count = len(facets)
    normals: list = [(0.0, 0.0, 0.0)] * count
    areas = [0.0] * count
    centroids: list = [(0.0, 0.0, 0.0)] * count
    degenerate = set()
    for facet, (a, b, c) in enumerate(facets):
        pa, pb, pc = vertices[a], vertices[b], vertices[c]
        centroids[facet] = ((pa[0] + pb[0] + pc[0]) / 3, (pa[1] + pb[1] + pc[1]) / 3, (pa[2] + pb[2] + pc[2]) / 3)
        if a == b or b == c or a == c:
            degenerate.add(facet)
            continue
        cross = _cross(_sub(pb, pa), _sub(pc, pa))
        length = math.sqrt(cross[0] ** 2 + cross[1] ** 2 + cross[2] ** 2)
        if length / 2 <= DEGENERATE_AREA_MM2:
            degenerate.add(facet)
            continue
        areas[facet] = length / 2
        normals[facet] = (cross[0] / length, cross[1] / length, cross[2] / length)

    # The same triangle repeated (same vertices, same winding) is kept once.
    # The other copies count as degenerate: they have no edges and cannot be
    # selected.  A triangle repeated with the opposite winding is a
    # zero-thickness wall and stays (both copies are then hidden).
    seen_triangles: dict = {}
    duplicates = set()
    for facet, (a, b, c) in enumerate(facets):
        if facet in degenerate:
            continue
        low = min(a, b, c)
        rotated = (a, b, c) if a == low else (b, c, a) if b == low else (c, a, b)
        if rotated in seen_triangles:
            duplicates.add(facet)
        else:
            seen_triangles[rotated] = facet
    degenerate |= duplicates

    # Undirected edge -> [(facet, directed start)], over non-degenerate facets.
    edges: dict = {}
    for facet, (a, b, c) in enumerate(facets):
        if facet in degenerate:
            continue
        for start, end in ((a, b), (b, c), (c, a)):
            key = (start, end) if start < end else (end, start)
            edges.setdefault(key, []).append((facet, start))
    # A repeated triangle whose edges are all shared, one by several solids, may
    # be the contact face of a body wound inside-out against another (a part and
    # its mirror image): the copy takes part in the orientation, and is a
    # duplicate after all only if it still runs as the first one (below).
    pending = {}  # copy -> the facet it repeats
    for facet in sorted(duplicates):
        a, b, c = facets[facet]
        uses = [len(edges.get((s, e) if s < e else (e, s), ())) for s, e in ((a, b), (b, c), (c, a))]
        if min(uses) >= 2 and max(uses) >= 3:
            low = min(a, b, c)
            pending[facet] = seen_triangles[(a, b, c) if a == low else (b, c, a) if b == low else (c, a, b)]
    for facet in pending:
        degenerate.discard(facet)
        a, b, c = facets[facet]
        for start, end in ((a, b), (b, c), (c, a)):
            edges[(start, end) if start < end else (end, start)].append((facet, start))
    neighbor_lists: list = [set() for _ in range(count)]
    boundary = []  # (facet, start, end) of the edges used once
    same_direction = []  # linked pairs whose winding disagrees
    wedges = []  # the facets round each non-manifold edge, by angle
    for key, uses in edges.items():
        if len(uses) == 1:
            facet, start = uses[0]
            boundary.append((facet, start, key[1] if start == key[0] else key[0]))
        elif len(uses) == 2:
            (f, start_f), (g, start_g) = uses
            neighbor_lists[f].add(g)
            neighbor_lists[g].add(f)
            if start_f == start_g:
                same_direction.append((f, g))
        else:
            # Several solids meet at this edge (touching parts that share vertices).
            # Around the edge, each facet is linked to the next one by angle when
            # the two run along it in opposite directions: the pair bounds one
            # wedge, of material or of air.  The outer faces then continue across
            # the seam, the coincident walls are hidden below, and a file with
            # thousands of facets on one edge stays linear.
            wedges.append(_wedge_order(key, uses, facets, vertices))
    cracks, edge_splits, open_edges, crack_same, crack_warning = _link_cracks(boundary, vertices)
    for f, g in cracks:
        neighbor_lists[f].add(g)
    same_direction.extend(crack_same)
    boundary_edges = sorted(open_edges)
    open_uses = _open_uses(boundary, edge_splits, open_edges)

    xs = [p[0] for p in vertices]
    ys = [p[1] for p in vertices]
    zs = [p[2] for p in vertices]
    box_low, box_high = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
    magnitude = max(abs(c) for c in box_low + box_high)

    # The wedges are first linked as the file winds the facets, and the pieces
    # so joined oriented; then linked again with the oriented windings.  A body
    # wound inside-out next to another is so oriented on its own (no link is made
    # across walls that lie on one another and run the same way), and its outer
    # faces still continue across the seam once it is turned outward.
    links = [pair for ordered in wedges for pair in _wedge_pairs(ordered, None)]
    neighbors = _neighbors(neighbor_lists, links)
    # Bodies (for the cavities): facets joined through every edge they share,
    # whatever the winding; without non-manifold edges, the pieces themselves.
    chains = [(ordered[i][1], ordered[i + 1][1]) for ordered in wedges for i in range(len(ordered) - 1)]
    body = _components(_neighbors(neighbor_lists, links + chains), degenerate) if wedges else None
    pieces, flipped, ambiguous_pieces, nesting_tests, open_pieces = _orient_shells(
        facets, vertices, neighbors, degenerate, same_direction, magnitude,
        [[f for _, f, _ in ordered] for ordered in wedges], open_uses, body,
    )
    if wedges:
        _face_coincident_walls(wedges, pieces, flipped, open_pieces, ambiguous_pieces)
    # A repeated triangle still running as the first one is a duplicate after all.
    dropped = {facet for facet, first in pending.items() if (facet in flipped) == (first in flipped)}
    duplicates -= set(pending) - dropped
    degenerate |= dropped
    flipped -= dropped
    nonmanifold = 0
    oriented_links = []
    for ordered in wedges:
        if dropped:
            ordered = [entry for entry in ordered if entry[1] not in dropped]
        if len(ordered) == 2:
            oriented_links.append((ordered[0][1], ordered[1][1]))  # a plain edge again
        else:
            nonmanifold += 1
            oriented_links.extend(_wedge_pairs(ordered, flipped))
    if oriented_links != links:
        neighbors = _neighbors(neighbor_lists, oriented_links)
    shell = _components(neighbors, degenerate)
    # A shell is ambiguous when none of its pieces (as oriented) had an outside;
    # one joined only now from such pieces (a body repeated with another
    # triangulation) is oriented as a whole, as a cavity never.
    told = {shell[f] for f in range(count) if pieces[f] != -1 and pieces[f] not in ambiguous_pieces and shell[f] != -1}
    ambiguous = 0
    untold: dict = {}
    for facet, s in enumerate(shell):
        if s != -1 and s not in told:
            untold.setdefault(s, []).append(facet)
    for s in sorted(untold):
        members = untold[s]
        if not any(pieces[f] != pieces[members[0]] for f in members):
            ambiguous += 1  # one piece: as oriented above
            continue
        volume, limit = _enclosed_volume(members, [f in flipped for f in members], facets, vertices, magnitude)
        if abs(volume) <= limit:
            ambiguous += 1
        elif volume < 0:
            flipped.symmetric_difference_update(members)
    for facet in flipped:
        nx, ny, nz = normals[facet]
        normals[facet] = (-nx, -ny, -nz)

    extent = [box_high[k] - box_low[k] for k in range(3)]
    # The covered-wall tolerances shrink with a part smaller than _COVER_FULL_SIZE_MM.
    reach = min(1.0, math.sqrt(extent[0] ** 2 + extent[1] ** 2 + extent[2] ** 2) / _COVER_FULL_SIZE_MM)
    hidden, covered, cover_truncated = _covered_facets(facets, normals, areas, centroids, vertices, degenerate, reach)
    shells = (max(shell) + 1) if count and max(shell) >= 0 else 0
    volume = 0.0
    for facet, (a, b, c) in enumerate(facets):
        if facet in degenerate:
            continue
        term = _dot(vertices[a], _cross(vertices[b], vertices[c])) / 6
        volume += -term if facet in flipped else term
    stats = {
        "facets": count,
        "vertices": len(vertices),
        "bbox_mm": [*box_low, *box_high],
        "extent_mm": extent,
        "area_mm2": math.fsum(areas),
        "volume_mm3": volume,
        "shells": shells,
        "boundary_edges": len(boundary_edges),
        "nonmanifold_edges": nonmanifold,
        "reversed_facets": len(flipped),
        "orientation_ambiguous_shells": ambiguous,
        "degenerate_facets": len(degenerate) - len(duplicates),
        "duplicate_facets": len(duplicates),
        "t_junction_links": len(cracks) // 2,
        "hidden_facets": len(hidden),
        "partly_covered_facets": len(covered),
        "watertight": not boundary_edges and nonmanifold == 0,
        "_nesting_tests": nesting_tests,
    }
    warnings = []
    if max(extent) < SMALL_PART_MM:
        warnings.append(f"The part measures only {max(extent):.3g} mm across in unit '{unit}'; check the unit.")
    if cover_truncated:
        warnings.append(
            f"More than {MAX_COVER_PAIRS} facet pairs lie on top of each other; the search for covered "
            "walls stopped there, so some hidden facets may be shown as selectable."
        )
    if crack_warning:
        warnings.append(crack_warning)
    if nesting_tests > MAX_NESTING_TESTS:
        warnings.append(
            f"Telling cavities from parts took more than {MAX_NESTING_TESTS} tests; every shell was "
            "oriented as a part (outward), cavities too."
        )
    if warnings:
        stats["warning"] = " ".join(warnings)
    return Mesh(
        name=name,
        sha256=sha256,
        source_format=source_format,
        unit=unit,
        unit_guess=unit_guess,
        scale_mm=scale,
        vertices=vertices,
        facets=facets,
        normals=normals,
        areas=areas,
        centroids=centroids,
        neighbors=neighbors,
        shell=shell,
        degenerate=frozenset(degenerate),
        hidden=frozenset(hidden),
        covered=covered,
        boundary_edges=boundary_edges,
        stats=stats,
        cracks=cracks,
        edge_splits=edge_splits,
    )


def _neighbors(neighbor_lists, links) -> list:
    """The sorted neighbour tuples: ``neighbor_lists`` plus the wedge ``links``."""

    extra: dict = {}
    for f, g in links:
        extra.setdefault(f, set()).add(g)
        extra.setdefault(g, set()).add(f)
    return [tuple(sorted(items | extra[f] if f in extra else items)) for f, items in enumerate(neighbor_lists)]


def _components(neighbors, degenerate) -> list:
    """The connected piece of every facet (-1 for degenerate facets), numbered by their lowest facet."""

    shell = [-1] * len(neighbors)
    current = 0
    for seed in range(len(neighbors)):
        if shell[seed] != -1 or seed in degenerate:
            continue
        shell[seed] = current
        queue = [seed]
        while queue:
            for other in neighbors[queue.pop()]:
                if shell[other] == -1:
                    shell[other] = current
                    queue.append(other)
        current += 1
    return shell


def _open_uses(boundary, edge_splits, open_edges) -> list:
    """The edges (or pieces of one, after the T-junction splits) that stay open, as (facet, edge)."""

    if not open_edges:
        return []
    open_set = set(open_edges)
    found = []
    for facet, s, e in boundary:
        chain = [s, *edge_splits.get((s, e), ()), e]
        for x, y in zip(chain, chain[1:]):
            key = (min(x, y), max(x, y))
            if key in open_set:
                found.append((facet, key))
    return found


def _face_coincident_walls(wedges, pieces, flipped, open_pieces, ambiguous) -> None:
    """Turn round a piece of coincident walls that leaves an oriented facet next to them unpaired.

    Two bodies touching over a whole face, one wound inside-out, leave each
    body's face a piece of its own (the walls are not linked, see
    :func:`_wedge_groups`), so that face keeps the file's winding when the
    rest of its body is turned outward.  Round an edge of the face, a facet
    next to the walls bounds a wedge with one of them and must run the other
    way: when a facet of a piece with an outside, next to two walls running
    the same way, runs as they do, one wall is wound the wrong way.  The walls
    lie on one another, so either may be turned: one open piece of the two
    (without an outside first, else the later) is turned round, once.  Walls
    running the same way that leave no such facet (a body repeated with
    another triangulation, a patch lying on a face) stay as they are.
    ``flipped`` is updated.
    """

    turned: set = set()
    members: dict = {}
    for ordered in wedges:
        entries, group, blocked = _wedge_groups(ordered, flipped)
        count = len(entries)
        for g in sorted(blocked):
            places = [i for i in range(count) if group[i] == g]
            both = sorted({pieces[entries[i][1]] for i in places})
            if len(places) != 2 or len(both) != 2 or turned.intersection(both):
                continue
            runs = entries[places[0]][2]
            beside = {(i + step) % count for i in places for step in (-1, 1)} - set(places)
            unpaired = {pieces[entries[i][1]] for i in beside if entries[i][2] == runs} - ambiguous - set(both)
            if not unpaired:
                continue
            candidates = [s for s in both if s in open_pieces and s not in unpaired]
            if not candidates:
                continue
            piece = max(candidates, key=lambda s: (s in ambiguous, s))
            if not members:
                for facet, s in enumerate(pieces):
                    members.setdefault(s, []).append(facet)
            flipped.symmetric_difference_update(members[piece])
            turned.add(piece)


def _orient_shells(facets, vertices, neighbors, degenerate, same_direction, magnitude, nonmanifold_uses, open_uses, body) -> tuple:
    """Group facets into shells and orient each one outward.

    Returns the shell id per facet (-1 for degenerate facets), the set of
    facets whose stored winding must be reversed for an outward normal, the
    shells whose outside could not be told (an open sheet that encloses no
    volume, such as a single flat or saddle-shaped sheet: its file winding is
    kept), the tests spent to tell the cavities (see :func:`_nesting`) and
    the shells that are not closed.  ``magnitude`` is the largest coordinate
    of the mesh; ``open_uses`` lists the open edges as (facet, edge), and
    ``body`` gives each facet's body (None: its shell).

    The signed volume is taken about the shell's own centroid.  For a closed
    shell any point gives the same result; for an open one (a box without its
    top, a cap) the centroid makes the answer independent of where the part
    sits in the file's frame.
    """

    count = len(facets)
    shell = [-1] * count
    disagree = set()
    for f, g in same_direction:
        disagree.add((f, g))
        disagree.add((g, f))
    flip = [False] * count
    flipped = set()
    ambiguous = set()
    orientation = []  # (members, inverted or None when ambiguous, flip)
    current = 0
    for seed in range(count):
        if shell[seed] != -1 or seed in degenerate:
            continue
        members = [seed]
        shell[seed] = current
        queue = [seed]
        while queue:
            facet = queue.pop()
            for other in neighbors[facet]:
                if shell[other] == -1:
                    shell[other] = current
                    flip[other] = flip[facet] != ((facet, other) in disagree)
                    members.append(other)
                    queue.append(other)
        volume, limit = _enclosed_volume(members, [flip[f] for f in members], facets, vertices, magnitude)
        if abs(volume) <= limit:
            ambiguous.add(current)
            orientation.append((members, None, flip))
        else:
            orientation.append((members, volume < 0, None))
        current += 1
    open_shells = {shell[f] for f, _ in open_uses}
    for uses in nonmanifold_uses:
        # A shell that uses a non-manifold edge an odd number of times is not closed there.
        times: dict = {}
        for f in uses:
            times[shell[f]] = times.get(shell[f], 0) + 1
        open_shells.update(s for s, n in times.items() if n % 2)
    # A shell inside an odd number of closed bodies is a cavity: its normals
    # point into the void, so it is oriented with negative volume.
    if body is None:
        body = shell  # no non-manifold edge: the bodies are the shells
    odd = {body[uses[0]] for uses in nonmanifold_uses if len(uses) % 2}
    nested, nesting_tests = _nesting(facets, vertices, orientation, flip, body, odd, open_uses)
    for (members, inverted, _), depth in zip(orientation, nested):
        if inverted is None:
            outward_flip = False  # the seed facet keeps its file winding
        else:
            outward_flip = inverted != (depth % 2 == 1)
        for facet in members:
            if flip[facet] != outward_flip:
                flipped.add(facet)
    return shell, flipped, ambiguous, nesting_tests, open_shells


def _enclosed_volume(members, reversed_flags, facets, vertices, magnitude) -> tuple:
    """Six times the volume a shell encloses about its own centroid, and the limit up to which it encloses nothing.

    ``reversed_flags`` tells, per member, whether its winding is reversed;
    ``magnitude`` bounds the coordinates (the mesh's largest).
    """

    weights = []
    for facet in members:
        a, b, c = (vertices[i] for i in facets[facet])
        weights.append(_norm(_cross(_sub(b, a), _sub(c, a))))
    total = math.fsum(weights)
    centre = tuple(
        math.fsum(w * (vertices[facets[f][0]][k] + vertices[facets[f][1]][k] + vertices[facets[f][2]][k]) / 3 for w, f in zip(weights, members))
        / total
        for k in range(3)
    ) if total > 0 else (0.0, 0.0, 0.0)
    terms = []
    for facet, reverse in zip(members, reversed_flags):
        a, b, c = (_sub(vertices[i], centre) for i in facets[facet])
        term = _dot(a, _cross(b, c))
        terms.append(-term if reverse else term)
    volume = math.fsum(terms)
    # An enclosed volume far below the area's own scale: no outside to tell.
    # A flat sheet away from the origin still encloses the volume of its
    # float32 rounding (at most about 1.2 * total * magnitude * 2^-24 was
    # seen), which must not decide its outside.
    limit = 1e-6 * (total / 2) ** 1.5
    noise = total * 2.0 ** -21
    if limit < abs(volume) <= limit + noise * magnitude:  # the shell's own coordinates, when it matters
        limit += noise * _magnitude(members, facets, vertices)
    return volume, limit


def _magnitude(members, facets, vertices) -> float:
    """The largest coordinate (absolute) of the facets' vertices."""

    return max(abs(c) for f in members for v in facets[f] for c in vertices[v])


def _nesting(facets, vertices, orientation, flip, body, odd, open_uses) -> tuple:
    """For every shell, how many closed bodies (other than its own) enclose it.

    ``body`` gives each facet's body: facets joined through every edge they
    share, whatever the winding (two parts touching over a face are one
    body).  A body is closed when none of its edges is shared by an odd
    number of its facets (``odd`` lists the bodies that have one) and each of
    its open edges in ``open_uses`` has a twin within T_JUNCTION_TOLERANCE_MM
    (a gap of float noise, not a hole).  Only a shell whose bounding box lies
    inside the body's box (or on it) is tested.  The test is ray parity (+x)
    from a few points inside the shell (half-way through it, below its
    largest facets), by majority: a shell that only touches the body is not
    taken for a cavity.  One pass over each enclosing body's facets serves
    every shell inside it.  Returns ``(depths, tests)``, the box comparisons,
    twin and ray-facet tests made; beyond ``MAX_NESTING_TESTS`` every depth
    is 0.
    """

    depth = [0] * len(orientation)
    oriented = [i for i, (_, inverted, _) in enumerate(orientation) if inverted is not None]
    if not oriented or max(body) < 1:
        return depth, 0  # one body: no other one to enclose a shell
    bodies: dict = {}
    for facet, b in enumerate(body):
        if b != -1:
            bodies.setdefault(b, []).append(facet)
    outers = [j for j in sorted(bodies) if j not in odd]
    if not oriented or len(bodies) < 2 or not outers:
        return depth, 0
    boxes = {}
    for i in oriented:
        points = [vertices[v] for f in orientation[i][0] for v in facets[f]]
        boxes[i] = tuple(min(p[k] for p in points) for k in range(3)) + tuple(max(p[k] for p in points) for k in range(3))
    outer_boxes = {}
    for j in outers:
        points = [vertices[v] for f in bodies[j] for v in facets[f]]
        outer_boxes[j] = tuple(min(p[k] for p in points) for k in range(3)) + tuple(max(p[k] for p in points) for k in range(3))
    # The candidate pairs, by a sweep over the inner boxes' lowest coordinate
    # along the axis where the boxes overlap least.
    sweeps = []
    for axis in range(3):
        lows = sorted(boxes[i][axis] for i in oriented)
        sweeps.append((sum(bisect.bisect_right(lows, b[axis + 3]) - bisect.bisect_left(lows, b[axis]) for b in outer_boxes.values()), axis))
    axis = min(sweeps)[1]
    by_low = sorted(oriented, key=lambda i: (boxes[i][axis], i))
    lowest = [boxes[i][axis] for i in by_low]
    tests = 0
    inside: dict = {}  # enclosing body -> the shells inside its box
    for j in outers:
        b = outer_boxes[j]
        for index in range(bisect.bisect_left(lowest, b[axis]), len(by_low)):
            i = by_low[index]
            a = boxes[i]
            if a[axis] > b[axis + 3]:
                break
            tests += 1
            if tests > MAX_NESTING_TESTS:
                return [0] * len(orientation), tests
            if body[orientation[i][0][0]] != j and all(b[k] <= a[k] and a[k + 3] <= b[k + 3] for k in range(3)):
                inside.setdefault(j, []).append(i)
    holes: dict = {}
    for facet, edge in open_uses:
        if body[facet] in inside:
            holes.setdefault(body[facet], []).append(edge)
    for j in sorted(holes):
        closed, used = _twinned(holes[j], vertices, MAX_NESTING_TESTS - tests)
        tests += used
        if tests > MAX_NESTING_TESTS:
            return [0] * len(orientation), tests
        if not closed:
            del inside[j]
    probes = {}
    for i in sorted({i for shells in inside.values() for i in shells}):
        members, inverted, _ = orientation[i]
        probes[i] = _inner_probes(members, inverted, flip, facets, vertices)
    for j in sorted(inside):
        # Offsets off the float32 grid keep the rays away from edges and vertices.
        rays = sorted((p[1] + 1.2345e-7, p[2] + 2.3456e-7, p[0], i) for i in inside[j] for p in probes[i])
        ys = [ray[0] for ray in rays]
        crossings = [0] * len(rays)
        for facet in bodies[j]:
            a, b, c = (vertices[v] for v in facets[facet])
            first = bisect.bisect_left(ys, min(a[1], b[1], c[1]))
            last = bisect.bisect_right(ys, max(a[1], b[1], c[1]))
            if first == last:
                continue
            tests += last - first
            if tests > MAX_NESTING_TESTS:
                return [0] * len(orientation), tests
            # Barycentric coordinates of (y, z) in the triangle projected onto the yz plane.
            det = (b[1] - a[1]) * (c[2] - a[2]) - (c[1] - a[1]) * (b[2] - a[2])
            if det == 0:
                continue
            z_low, z_high = min(a[2], b[2], c[2]), max(a[2], b[2], c[2])
            for r in range(first, last):
                y, z, x, _ = rays[r]
                if z < z_low or z > z_high:
                    continue
                l1 = ((y - a[1]) * (c[2] - a[2]) - (c[1] - a[1]) * (z - a[2])) / det
                l2 = ((b[1] - a[1]) * (z - a[2]) - (y - a[1]) * (b[2] - a[2])) / det
                if l1 < 0 or l2 < 0 or l1 + l2 > 1:
                    continue
                if a[0] + l1 * (b[0] - a[0]) + l2 * (c[0] - a[0]) > x:
                    crossings[r] += 1
        ballots: dict = {}
        for (_, _, _, i), n in zip(rays, crossings):
            votes = ballots.setdefault(i, [0, 0])
            votes[0] += n % 2
            votes[1] += 1
        for i, (yes, total) in ballots.items():
            if 2 * yes > total:
                depth[i] += 1
    return depth, tests


def _twinned(edges, vertices, budget: int) -> tuple:
    """Whether every edge has a twin: another one whose ends lie within T_JUNCTION_TOLERANCE_MM of its own.

    Such open edges bound a gap of float noise between facets that should
    have been welded (it lets no ray through), not a hole.  Returns
    ``(closed, tests)``; past ``budget`` tests the answer is False.
    """

    tolerance = T_JUNCTION_TOLERANCE_MM
    size = 2 * tolerance  # a point within the tolerance lies in one of 8 cells round it

    def cells(point) -> list:
        ranges = [range(int(math.floor((c - tolerance) / size + _CRACK_PHASE)), int(math.floor((c + tolerance) / size + _CRACK_PHASE)) + 1) for c in point]
        return [(x, y, z) for x in ranges[0] for y in ranges[1] for z in ranges[2]]

    table: dict = {}
    for index, (s, e) in enumerate(edges):
        for v in (s, e):
            table.setdefault(tuple(int(math.floor(c / size + _CRACK_PHASE)) for c in vertices[v]), []).append(index)
    tests = 0
    for index, (s, e) in enumerate(edges):
        p, q = vertices[s], vertices[e]
        found = False
        for key in cells(p):
            for other in table.get(key, ()):
                tests += 1
                if tests > budget:
                    return False, tests
                r, t = vertices[edges[other][0]], vertices[edges[other][1]]
                if other != index and (
                    (_norm(_sub(p, r)) <= tolerance and _norm(_sub(q, t)) <= tolerance)
                    or (_norm(_sub(p, t)) <= tolerance and _norm(_sub(q, r)) <= tolerance)
                ):
                    found = True
                    break
            if found:
                break
        if not found:
            return False, tests
    return True, tests


def _inner_probes(members, inverted, flip, facets, vertices) -> list:
    """Points inside a shell: below each of its largest facets, half-way to the shell's far side.

    From a facet's centroid a ray goes inward along the axis nearest the
    inward normal; the point half-way to the first other facet it meets lies
    inside the shell, away from its walls.  Without such a facet (an open
    shell) the centroid itself is taken.
    """

    def area2(facet: int) -> float:
        a, b, c = (vertices[v] for v in facets[facet])
        n = _cross(_sub(b, a), _sub(c, a))
        return _dot(n, n)

    probes = []
    for facet in heapq.nsmallest(_NESTING_PROBES, members, key=lambda f: (-area2(f), f)):
        a, b, c = (vertices[v] for v in facets[facet])
        centroid = tuple((a[k] + b[k] + c[k]) / 3 for k in range(3))
        normal = _cross(_sub(b, a), _sub(c, a))
        if flip[facet] != inverted:
            normal = _scale(normal, -1.0)  # now outward
        axis = max(range(3), key=lambda k: (abs(normal[k]), -k))
        step = -1.0 if normal[axis] > 0 else 1.0  # inward along the axis
        j, k = (axis + 1) % 3, (axis + 2) % 3
        y, z = centroid[j], centroid[k]
        near = math.inf
        for other in members:
            if other == facet:
                continue
            p, q, r = (vertices[v] for v in facets[other])
            if (p[j] > y and q[j] > y and r[j] > y) or (p[j] < y and q[j] < y and r[j] < y):
                continue
            if (p[k] > z and q[k] > z and r[k] > z) or (p[k] < z and q[k] < z and r[k] < z):
                continue
            det = (q[j] - p[j]) * (r[k] - p[k]) - (r[j] - p[j]) * (q[k] - p[k])
            if det == 0:
                continue
            l1 = ((y - p[j]) * (r[k] - p[k]) - (r[j] - p[j]) * (z - p[k])) / det
            l2 = ((q[j] - p[j]) * (z - p[k]) - (y - p[j]) * (q[k] - p[k])) / det
            if l1 < 0 or l2 < 0 or l1 + l2 > 1:
                continue
            distance = (p[axis] + l1 * (q[axis] - p[axis]) + l2 * (r[axis] - p[axis]) - centroid[axis]) * step
            if 0 < distance < near:
                near = distance
        point = list(centroid)
        if near < math.inf:
            point[axis] += step * near / 2
        probes.append(tuple(point))
    return probes


def _wedge_order(key, uses, facets, vertices) -> list:
    """The facets round a non-manifold edge by angle: ``(angle, facet, runs from key[0] to key[1])``."""

    p, q = vertices[key[0]], vertices[key[1]]
    axis = _unit(_sub(q, p))
    e1, e2 = _plane_axes(axis)
    ordered = []
    for facet, start in uses:
        third = next(v for v in facets[facet] if v != key[0] and v != key[1])
        d = _sub(vertices[third], p)
        ordered.append((math.atan2(_dot(d, e2), _dot(d, e1)), facet, start == key[0]))
    ordered.sort()
    return ordered


def _wedge_groups(ordered, flipped) -> tuple:
    """The facets round a non-manifold edge, in groups of coincident walls.

    Returns ``(entries, group, blocked)``: ``(angle, facet, runs from key[0]
    to key[1])`` with the facets in ``flipped`` (None: the file's winding)
    turned round, the group of each entry (facets within ``_TIE_ANGLE`` of
    each other lie on one another), and the groups where more facets run one
    way than the other.  Coincident walls have no telling order, so in such a
    group a body is wound inside-out and a link to any of its walls could join
    that body to another one.
    """

    entries = [(angle, f, forward != (flipped is not None and f in flipped)) for angle, f, forward in ordered]
    count = len(entries)
    group = [0] * count
    for i in range(1, count):
        group[i] = group[i - 1] + (entries[i][0] - entries[i - 1][0] > _TIE_ANGLE)
    if entries[0][0] + 2 * math.pi - entries[-1][0] <= _TIE_ANGLE:
        last = group[-1]
        group = [0 if g == last else g for g in group]  # the group across +-pi
    balance: dict = {}
    for (_, _, forward), g in zip(entries, group):
        balance[g] = balance.get(g, 0) + (1 if forward else -1)
    return entries, group, {g for g, value in balance.items() if abs(value) > 1}


def _wedge_pairs(ordered, flipped) -> list:
    """The facet pairs round a non-manifold edge that bound one wedge (adjacent by angle).

    Before the shells are oriented (``flipped`` None), no link is made to a
    group of coincident walls that run the same way (see
    :func:`_wedge_groups`); with the oriented windings, every such pair is.
    """

    entries, group, blocked = _wedge_groups(ordered, flipped)
    if flipped is not None:
        blocked = set()
    count = len(entries)
    # Two coincident walls running opposite ways have no telling order by
    # angle: the one running against the facet before them comes first, so
    # each body's facet beside the walls is linked to its own wall.
    for i in range(count):
        k, after = (i - 1) % count, (i + 1) % count
        if group[k] != group[i] == group[after] != group[(i + 2) % count] and entries[i][2] != entries[after][2]:
            if entries[i][2] == entries[k][2]:
                entries[i], entries[after] = entries[after], entries[i]
    pairs = []
    for i in range(count):
        _, f, forward_f = entries[i]
        _, g, forward_g = entries[(i + 1) % count]
        if group[i] in blocked or group[(i + 1) % count] in blocked:
            continue
        if f != g and forward_f != forward_g:
            pairs.append((f, g))
    return pairs


def _link_cracks(boundary, vertices) -> tuple:
    """Link facets across T-junctions: boundary edges that overlap along one line.

    A CAD exporter often leaves a vertex of one facet on the middle of
    another facet's edge.  Every boundary edge is split at the boundary
    vertices lying on it; two facets whose pieces coincide are linked.
    Returns ``(cracks, edge_splits, open_edges, same_direction, warning)``:
    ``cracks`` maps (f, g) to (edge of f, edge of g) both ways,
    ``edge_splits`` maps a split edge (start, end) to the vertices on it,
    ``open_edges`` lists the pieces that stay open (undirected),
    ``same_direction`` the linked pairs whose winding disagrees, and
    ``warning`` says which bound left cracks unrepaired (or is None).

    The boundary vertices are kept in grids of growing cells.  Each edge is
    walked on the grid that takes it in a few steps; a cell of that grid
    holding many vertices is walked again on the finer grids, so the work per
    edge follows the vertices near it, not its length.
    """

    every_edge = [(min(s, e), max(s, e)) for _, s, e in boundary]
    if not boundary:
        return {}, {}, [], [], None
    if len(boundary) > MAX_CRACK_EDGES:
        return {}, {}, every_edge, [], f"More than {MAX_CRACK_EDGES} open edges; cracks (T-junctions) were not repaired."
    lengths = sorted(_norm(_sub(vertices[e], vertices[s])) for _, s, e in boundary)
    cell = max(lengths[len(lengths) // 2], 10 * T_JUNCTION_TOLERANCE_MM)
    points = sorted({v for _, s, e in boundary for v in (s, e)})
    grids: dict = {}  # level -> (cell size, cell -> boundary vertices); below 0, finer than the median edge

    def grid(level: int) -> tuple:
        if level not in grids:
            size = cell * _CRACK_LEVEL ** level
            table: dict = {}
            for v in points:
                table.setdefault(tuple(int(math.floor(c / size + _CRACK_PHASE)) for c in vertices[v]), []).append(v)
            grids[level] = (size, table)
        return grids[level]

    edge_splits: dict = {}
    tests = 0
    crowded = stopped = False
    for _, s, e in boundary:
        S, E = vertices[s], vertices[e]
        d = _sub(E, S)
        length2 = _dot(d, d)
        if length2 == 0:
            continue
        length = math.sqrt(length2)
        level = 0
        while length > _CRACK_STEPS * cell * _CRACK_LEVEL ** level:
            level += 1
        near = set()
        spans = [(level, 0.0, 1.0)]
        while spans:
            level, t0, t1 = spans.pop()
            size, table = grid(level)
            busy = []
            cells = _cells_along(S, d, length, t0, t1, size)
            tests += len(cells)
            for key, span in cells.items():
                found = table.get(key)
                if not found:
                    continue
                if len(found) <= _CRACK_CROWDED:
                    near.update(found)
                elif size / _CRACK_LEVEL >= _CRACK_FINEST_MM:
                    busy.append(span)  # walked again on the finer grid
                else:
                    # Many boundary vertices on one small spot: not a CAD
                    # export's T-junctions.  The edge stays open there.
                    crowded = True
            for t0, t1 in _merged(busy):
                spans.append((level - 1, t0, t1))
        tests += len(near)
        if tests > MAX_CRACK_TESTS:
            stopped = True
            break
        inside = []
        margin = T_JUNCTION_TOLERANCE_MM / length
        for v in near:
            if v == s or v == e:
                continue
            offset = _sub(vertices[v], S)
            t = _dot(offset, d) / length2
            if not margin < t < 1 - margin:
                continue
            if _norm(_sub(offset, _scale(d, t))) <= T_JUNCTION_TOLERANCE_MM:
                inside.append((t, v))
        if inside:
            edge_splits[(s, e)] = [v for _, v in sorted(set(inside))]
    if stopped:
        warning = f"The search for cracks (T-junctions) stopped after {MAX_CRACK_TESTS} tests; some were not repaired."
    elif crowded:
        warning = "Too many open edges meet on one spot; cracks (T-junctions) there were not repaired."
    else:
        warning = None
    if not edge_splits:
        return {}, {}, every_edge, [], warning
    pieces: dict = {}
    for facet, s, e in boundary:
        chain = [s, *edge_splits.get((s, e), ()), e]
        for x, y in zip(chain, chain[1:]):
            pieces.setdefault((min(x, y), max(x, y)), []).append((facet, x, (s, e)))
    cracks: dict = {}
    same_direction = []
    open_edges = []
    for key, uses in pieces.items():
        if len(uses) == 1:
            open_edges.append(key)
            continue
        for i in range(len(uses)):
            for k in range(i + 1, min(len(uses), i + 3)):
                (f, start_f, edge_f), (g, start_g, edge_g) = uses[i], uses[k]
                if f == g or (f, g) in cracks:
                    continue
                cracks[(f, g)] = (edge_f, edge_g)
                cracks[(g, f)] = (edge_g, edge_f)
                if start_f == start_g:
                    same_direction.append((f, g))
    return cracks, edge_splits, open_edges, same_direction, warning


def _cells_along(start, direction, length, t0, t1, size) -> dict:
    """The grid cells (of ``size``) within the T-junction tolerance of the edge between t0 and t1.

    Maps each cell to the span of the edge (in t) that comes near it.  The
    edge is cut into pieces shorter than a cell; every cell meeting a
    piece's bounding box, grown by the tolerance, is taken.
    """

    steps = int((t1 - t0) * length / size) + 1
    pad = T_JUNCTION_TOLERANCE_MM
    cells: dict = {}
    for k in range(steps):
        ta = t0 + (t1 - t0) * k / steps
        tb = t0 + (t1 - t0) * (k + 1) / steps
        p, q = _add(start, _scale(direction, ta)), _add(start, _scale(direction, tb))
        low = [int(math.floor((min(p[i], q[i]) - pad) / size + _CRACK_PHASE)) for i in range(3)]
        high = [int(math.floor((max(p[i], q[i]) + pad) / size + _CRACK_PHASE)) for i in range(3)]
        for x in range(low[0], high[0] + 1):
            for y in range(low[1], high[1] + 1):
                for z in range(low[2], high[2] + 1):
                    span = cells.get((x, y, z))
                    cells[(x, y, z)] = (ta, tb) if span is None else (min(span[0], ta), max(span[1], tb))
    return cells


def _merged(spans) -> list:
    """Overlapping (t0, t1) spans joined, in order."""

    merged: list = []
    for t0, t1 in sorted(spans):
        if merged and t0 <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], t1))
        else:
            merged.append((t0, t1))
    return merged


def _covered_facets(facets, normals, areas, centroids, vertices, degenerate, reach: float = 1.0) -> tuple:
    """Find facets that lie on another, opposite-facing facet: walls where two shells touch.

    Returns ``(hidden, covered, truncated)``: ``hidden`` holds the facets covered over
    at least ``HIDDEN_FRACTION`` of their area (they cannot be selected), and
    ``covered`` maps a partly covered facet to the covered polygons (3D,
    mm), which the fit treats as obstacles.  Decimated meshes put the two
    walls up to a few hundredths of a millimetre apart (the crank tip: about
    0.01 mm, with 0.005 mm of noise), hence the plane tolerance; ``reach``
    (at most 1) scales the tolerances down for a small part.
    """

    distance = _PLANE_DISTANCE_MM * reach
    quantum = _PLANE_OFFSET_QUANTUM_MM * reach
    min_area = _OVERLAP_MIN_AREA_MM2 * reach * reach

    # Group facets by plane (normal and offset quantized) and by orientation.  Only
    # groups where both orientations meet need pairwise work; inside a large group
    # a grid over the bounding boxes keeps it close to linear.
    positive: dict = {}
    negative: dict = {}
    main_axis: dict = {}
    for facet in range(len(facets)):
        if facet in degenerate:
            continue
        n = normals[facet]
        axis = max(range(3), key=lambda i: abs(n[i]))
        main_axis[facet] = axis
        sign = 1.0 if n[axis] > 0 else -1.0
        key_normal = tuple(int(round(sign * n[i] / _PLANE_NORMAL_QUANTUM)) for i in range(3))
        key_offset = int(math.floor(sign * _dot(n, centroids[facet]) / quantum))
        (positive if sign > 0 else negative).setdefault((key_normal, key_offset), []).append(facet)
    boxes: dict = {}

    def box(facet: int) -> tuple:
        found = boxes.get(facet)
        if found is None:
            points = [vertices[i] for i in facets[facet]]
            found = tuple(min(p[k] for p in points) - distance for k in range(3)) + tuple(
                max(p[k] for p in points) + distance for k in range(3)
            )
            boxes[facet] = found
        return found

    def seen_along(facet: int, axis: int) -> tuple:
        # The facet's corners seen along ``axis`` (that coordinate dropped), and
        # its edges as (corner, direction with the interior on the left, length).
        j, k = (axis + 1) % 3, (axis + 2) % 3
        corners = [(vertices[v][j], vertices[v][k]) for v in facets[facet]]
        sign = 1.0 if signed_area_2d(corners) >= 0 else -1.0
        edges = []
        for i in range(3):
            (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 3]
            ex, ey = (bx - ax) * sign, (by - ay) * sign
            edges.append((ax, ay, ex, ey, hypot2(ex, ey)))
        return corners, edges

    def height(facet: int, other: int) -> float:
        # How far the other facet's corners lie from the facet's plane.
        n, origin = normals[facet], vertices[facets[facet][0]]
        return max(abs(_dot(n, _sub(vertices[i], origin))) for i in facets[other])

    def overlapping(f: int, g: int, seen_f: tuple) -> bool:
        # Only pairs that can cover each other count (and are clipped): close
        # boxes, opposite normals, one within the plane tolerance of the
        # other's plane, and no edge of either triangle, seen along f's main
        # normal axis, with the other one entirely beyond it.  Seen so, a corner
        # off the plane moves by at most its height, which is the margin: a pair
        # whose clip has any area is always kept.
        bf, bg = box(f), box(g)
        if any(bf[k] > bg[k + 3] or bg[k] > bf[k + 3] for k in range(3)):
            return False
        if _dot(normals[f], normals[g]) > -_OPPOSITE_COS:
            return False
        lift_g, lift_f = height(f, g), height(g, f)
        if lift_g > distance and lift_f > distance:
            return False
        lift = max(lift_f, lift_g)
        corners_f, edges_f = seen_f  # seen_along(f, main_axis[f])
        corners_g, edges_g = seen_along(g, main_axis[f])
        for edges, corners in ((edges_f, corners_g), (edges_g, corners_f)):
            for ax, ay, ex, ey, length in edges:
                margin = lift * length
                if all(ex * (py - ay) - ey * (px - ax) < -margin for px, py in corners):
                    return False
        return True

    pairs = set()
    truncated = False
    for (key_normal, key_offset), group in sorted(positive.items()):
        if len(pairs) >= MAX_COVER_PAIRS:
            truncated = True
            break
        others = []
        for offset in (key_offset - 1, key_offset, key_offset + 1):
            others.extend(negative.get((key_normal, offset), ()))
        if not others:
            continue
        if len(group) * len(others) <= _PAIRWISE_LIMIT:
            for f in group:
                seen_f = seen_along(f, main_axis[f])
                for g in others:
                    if overlapping(f, g, seen_f):
                        pairs.add((f, g))
            continue
        extents = sorted(max(box(g)[k + 3] - box(g)[k] for k in range(3)) for g in others)
        cell = max(extents[len(extents) // 2], _COVER_CELL_MM * reach)
        grid: dict = {}
        for g in others:
            b = box(g)
            lo = [int(math.floor(b[k] / cell)) for k in range(3)]
            hi = [int(math.floor(b[k + 3] / cell)) for k in range(3)]
            if (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1) > _GRID_CELLS_PER_FACET:
                grid.setdefault("large", []).append(g)
                continue
            for i in range(lo[0], hi[0] + 1):
                for j in range(lo[1], hi[1] + 1):
                    for k in range(lo[2], hi[2] + 1):
                        grid.setdefault((i, j, k), []).append(g)
        large = grid.get("large", [])
        for f in group:
            b = box(f)
            lo = [int(math.floor(b[k] / cell)) for k in range(3)]
            hi = [int(math.floor(b[k + 3] / cell)) for k in range(3)]
            seen = set()
            seen_f = seen_along(f, main_axis[f])
            if (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1) > _GRID_CELLS_PER_FACET:
                candidates = others
            else:
                candidates = list(large)
                for i in range(lo[0], hi[0] + 1):
                    for j in range(lo[1], hi[1] + 1):
                        for k in range(lo[2], hi[2] + 1):
                            candidates.extend(grid.get((i, j, k), ()))
            for g in candidates:
                if g not in seen:
                    seen.add(g)
                    if overlapping(f, g, seen_f):
                        pairs.add((f, g))
            if len(pairs) >= MAX_COVER_PAIRS:
                truncated = True
                break
    overlap_area: dict = {}
    covered: dict = {}
    # A facet already covered enough to be hidden needs no more clipping: its
    # sum only grows, and a hidden facet's polygons are dropped.  Facets stacked
    # by the hundred then cost one clip each.
    saturated = set()
    for f, g in sorted(pairs):
        for first, second in ((f, g), (g, f)):
            if first in saturated:
                continue
            polygon = _coplanar_overlap(facets, vertices, normals, first, second, distance)
            if polygon is None:
                continue
            area = _polygon_area_3d(polygon, normals[first])
            if area <= min_area:
                continue
            overlap_area[first] = overlap_area.get(first, 0.0) + area
            covered.setdefault(first, []).append(polygon)
            if overlap_area[first] >= HIDDEN_FRACTION * areas[first]:
                saturated.add(first)
    hidden = {facet for facet, area in overlap_area.items() if area >= HIDDEN_FRACTION * areas[facet]}
    partly = {facet: polygons for facet, polygons in covered.items() if facet not in hidden}
    return hidden, partly, truncated


def _coplanar_overlap(facets, vertices, normals, f: int, g: int, distance: float = _PLANE_DISTANCE_MM):
    """The part of facet ``f`` that facet ``g`` (within ``distance`` of its plane) covers, as a 3D polygon, or None."""

    n = normals[f]
    origin = vertices[facets[f][0]]
    if any(abs(_dot(n, _sub(vertices[i], origin))) > distance for i in facets[g]):
        return None
    u, v = _plane_axes(n)
    tri_f = [_project(_sub(vertices[i], origin), u, v) for i in facets[f]]
    tri_g = [_project(_sub(vertices[i], origin), u, v) for i in facets[g]]
    clipped = clip_convex(tri_f, tri_g)
    if len(clipped) < 3:
        return None
    return [_add(origin, _add(_scale(u, x), _scale(v, y))) for x, y in clipped]


def clip_convex(subject: Sequence, clip: Sequence) -> list:
    """Sutherland-Hodgman: the part of convex polygon ``subject`` inside convex ``clip`` (2D)."""

    if signed_area_2d(clip) < 0:
        clip = list(reversed(clip))
    output = [tuple(p) for p in subject]
    for i in range(len(clip)):
        if not output:
            break
        a, b = clip[i], clip[(i + 1) % len(clip)]
        source, output = output, []

        def inside(p) -> bool:
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

        def crossing(p, q):
            ex, ey = b[0] - a[0], b[1] - a[1]
            dp = ex * (p[1] - a[1]) - ey * (p[0] - a[0])
            dq = ex * (q[1] - a[1]) - ey * (q[0] - a[0])
            t = dp / (dp - dq)
            return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))

        for j in range(len(source)):
            current, previous = source[j], source[j - 1]
            if inside(current):
                if not inside(previous):
                    output.append(crossing(previous, current))
                output.append(current)
            elif inside(previous):
                output.append(crossing(previous, current))
    return output


def signed_area_2d(points: Sequence) -> float:
    total = 0.0
    for i in range(len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        total += x0 * y1 - x1 * y0
    return total / 2


def _polygon_area_3d(polygon: Sequence, normal: Sequence[float]) -> float:
    total = (0.0, 0.0, 0.0)
    for i in range(len(polygon)):
        total = _add(total, _cross(polygon[i - 1], polygon[i]))
    return abs(_dot(total, normal)) / 2


# --------------------------------------------------------------------------
# Small vector helpers (also used by the other surface modules)
# --------------------------------------------------------------------------


def _sub(a: Sequence[float], b: Sequence[float]) -> Vector:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Sequence[float], b: Sequence[float]) -> Vector:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a: Sequence[float], s: float) -> Vector:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Sequence[float], b: Sequence[float]) -> Vector:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def hypot2(x: float, y: float) -> float:
    """sqrt(x^2 + y^2), the same on every Python (math.hypot changed in 3.10)."""

    return math.sqrt(x * x + y * y)


def dist2(a: Sequence[float], b: Sequence[float]) -> float:
    """Distance between two 2D points, the same on every Python (math.dist changed in 3.10)."""

    return hypot2(b[0] - a[0], b[1] - a[1])


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _unit(a: Sequence[float]) -> Vector:
    length = _norm(a)
    if length == 0:
        return (0.0, 0.0, 0.0)
    return (a[0] / length, a[1] / length, a[2] / length)


def _plane_axes(normal: Sequence[float]) -> tuple:
    """Two unit vectors spanning the plane normal to ``normal`` (deterministic)."""

    axis = min(range(3), key=lambda i: (abs(normal[i]), i))
    helper = [0.0, 0.0, 0.0]
    helper[axis] = 1.0
    u = _unit(_cross(normal, helper))
    v = _cross(normal, u)
    return u, v


def _project(point: Sequence[float], u: Sequence[float], v: Sequence[float]) -> tuple:
    return (_dot(point, u), _dot(point, v))


sub, add, scale, dot, cross, norm, unit, plane_axes = _sub, _add, _scale, _dot, _cross, _norm, _unit, _plane_axes
