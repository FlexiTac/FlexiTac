"""Masked taxel fields for CAD mode: the fit option ``shape: fill``.

The readout stays an R x C matrix of ROW and COL lines, but each Row
electrode spans only its active columns and each Column electrode only its
active rows (``matrix.mask``, docs/API.md "Field mask"); the boards'
outlines and coverlay windows follow the taxels, so a triangular face takes
a triangle of taxels.  This module proposes masked fields of the engine's
straight construction classes (claude/specs/masked-field/PLAN.md, phase P4)
and merges them with the rectangular fields of :func:`surface.fit.search`:
a masked field must win by strictly more taxels (``never worse``).

**The straight class, seen from outside the part** (base frame, tails
down).  Rows keep their order (ROW_01 on top).  The Row channel runs along
one side of the field (on the right for ``rows_top``, on the left for
``columns_top``); the search works in a frame turned so that the channel is
on the left (the Row board then appears in its canonical frame and the
Column board mirrored, for either role mapping).  Lattice column ``i0`` is
the channel-most column (slot 0, held by the top row); the board's channel
edge is ``x_out = edge(i0) - d``, with ``d`` a breakpoint of the lane
taper in ``[W_1, W_1 + pitch)`` (``engine.row_taper``: ``W_k`` is the
smallest x of ROW_k's channel-side crossing edge).  Going down, the j-th row
starts at slot ``tau_j = ceil((W_j - d) / pitch)``, so the engine rebuilds
exactly this mask with its board edge at or inside ``x_out`` (condition A),
and ends at the largest column whose Row region ``[x_out, far + margin]``
over the row's band is free; the far ends never recede going down (the
running minimum from the floor up), so a column that stops above the floor
lies in the Row channel's taper zone (condition B).  Below the floor, the
bottom zone (both boards' bodies and fan-outs down to the deeper tail root)
must be free and both tails must reach the exit (at most
``80 - tail_extension_mm`` on the surface).

**Exact free space.**  :class:`FreeSpace` decides strips of the frame from
the outline, holes and obstacles themselves (no raster): a vertical segment
across a strip is free when it is inside the outline at the strip's middle
and no boundary, hole, obstacle or bend segment comes within the edge
margin of the strip at its x.  So the search loses no cell to quantization
(the rectangle search's raster loses the soft finger's 45 x 8).

**Search.**  Each role mapping is searched on its own (its own pruning
threshold, phases, turned exits and fine frames), so ``role_mapping: auto``
searches all that either role does alone.  Per role, per frame (each exit
unturned; with ``rotation: auto`` also the role's two best exits turned by
10-30 degrees), per lattice phase (stage 1: 0 and p/2 in x and y, the far
side snapped to the far free extreme, the top row snapped to the top free
extreme and the phases of the role's three best rectangles there, placed
far whatever the placement option; stage 2, on the role's two best
frames: quarters and eighths of the pitch around the best phase) and
routing, every top row and channel edge is walked down.  Frames and pool
are ranked without the placement term (:func:`search_rank`), so the
placement option never changes which lattices are searched; each mask
keeps its highest and its lowest field, and the option picks one first.  With several
pitches (``max_taxels``, ``max_area``) the first is searched on every
frame and the others on the role's two best frames.  The best candidates
are generated (``engine.generate_design``) and their real outlines checked
exactly (:func:`surface.fit.check_containment`); a candidate that leaves
the surface is peeled (the far-end cell of the row nearest the failure, or
the top row) and retried up to :data:`PEEL_RETRIES` times.  One masked
proposal per readout, and none that an earlier proposal beats or equals
in taxels on no more Row and Column lines (:func:`dominated`).

**Size and readers.**  Masked fields take the rectangles' caps,
``max_rows`` x ``max_columns`` (the user's decision, P5-diagonal-bus.md
section 21: coverage of the selection first; 32 x 32 before).  A named
reader caps the walk at its lines, either way round
(:func:`surface.reader.walk_caps`: ``16x16`` at 16 x 16, ``32x16`` at
16 x 32 and at 32 x 16), ``auto`` at the largest reader's 48 x 48
(:func:`surface.reader.field_caps`), and the rectangles at the readouts it
holds.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from engine import design_mask, generate_design, row_taper
from engine.geometry import point_in_polygon, round6, segments_intersect
from engine.layout import _body_side, column_plan, row_plan, tail_width

from . import border as border_module
from . import fit
from . import reader as reader_module
from .errors import SurfaceError

MAX_REALIZE_ATTEMPTS_FILL = 90
PEEL_RETRIES = 3
# Masked candidates kept for realize (distinct masks), and accepted per searched lattice.
MASKED_POOL = 48
ACCEPTED_PER_SEARCH = 6
# Stage 2 (fine phases) runs on this many (frame, role) pairs; default routing (when 'auto') on this many lattices.
FINE_FRAMES = 2
# A walk restarts with its channel edge moved inward (to a lower row's band) at most this often.
MAX_RESTARTS = 2
DEFAULT_ROUTING_LATTICES = 4
# The placements of the rectangles whose lattice phases seed the masked search, whatever the option (seed_origins).
SEED_PLACEMENTS = ("far",)
_NOISE = 1e-9


# --------------------------------------------------------------------------
# Exact free space of one frame
# --------------------------------------------------------------------------


class FreeSpace:
    """The usable surface of one base frame, decided exactly from the outline, holes and obstacles.

    It also serves as the ``region`` of :func:`surface.fit.check_containment`
    and of the tails' run to the exit (``outline``, ``exit_edges``,
    ``exit_y``, ``exits``).
    """

    def __init__(self, chart: Any, frame: Any, obstacles: Mapping[str, Any], margin: float, exit_edges: Sequence[int]) -> None:
        self.frame = frame
        # The edge margin, plus the rectangle fit's 0.1 um inset: a board corner that touches the surface's
        # edge in the search stays on it after rounding (check_containment decides points on the edge either way).
        self.margin = float(margin) + fit.EDGE_INSET_MM
        outline = [frame.to_base(p) for p in chart.outline()]
        self.outline = outline
        self.exits = fit.ExitOutline(outline, exit_edges)
        self.exit_edges = self.exits.exit_edges
        count = len(outline)
        tops = [outline[k][1] for i in self.exit_edges if 0 <= i < count for k in (i, (i + 1) % count)]
        self.exit_top = max(tops) if tops else -math.inf
        holes = [[frame.to_base(p) for p in hole] for hole in obstacles["holes"]]
        blocked = [[frame.to_base(p) for p in polygon] for key in ("strained", "covered") for polygon in obstacles[key]]
        blocked = [polygon for polygon in blocked if len(polygon) >= 3]
        # (ax, ay, bx, by, kind, group, exit): kind 0 the outline and holes (even-odd inside), 1 a blocked
        # polygon (its group), 2 a bend segment.
        segments = []
        count = len(outline)
        for index in range(count):
            (ax, ay), (bx, by) = outline[index], outline[(index + 1) % count]
            segments.append((ax, ay, bx, by, 0, 0, index in self.exit_edges))
        for hole in holes:
            for k in range(len(hole)):
                (ax, ay), (bx, by) = hole[k - 1], hole[k]
                segments.append((ax, ay, bx, by, 0, 0, False))
        for group, polygon in enumerate(blocked):
            for k in range(len(polygon)):
                (ax, ay), (bx, by) = polygon[k - 1], polygon[k]
                segments.append((ax, ay, bx, by, 1, group, False))
        for a, b, _ in obstacles["bends"]:
            (ax, ay), (bx, by) = frame.to_base(a), frame.to_base(b)
            segments.append((ax, ay, bx, by, 2, 0, False))
        self.segments = segments
        xs = [p[0] for p in outline]
        ys = [p[1] for p in outline]
        self.x0, self.x1, self.y0, self.y1 = min(xs), max(xs), min(ys), max(ys)
        # Segments in buckets over y (a strip looks at a few of them).
        self._bucket_base = self.y0
        self._bucket_height = max(0.25, (self.y1 - self.y0) / 1024)
        self._buckets: dict = {}
        for index, (ax, ay, bx, by, _, _, _) in enumerate(segments):
            for key in range(self._bucket(min(ay, by)), self._bucket(max(ay, by)) + 1):
                self._buckets.setdefault(key, []).append(index)
        self._strips: dict = {}
        # The user's border (surface.border; field-only containment, the surface template): a lattice cell is free only
        # when its taxel square lies inside it (surface.fieldfit.lattice), and the lattice spans only where one may.
        self.border = None
        if obstacles.get("border") is not None:
            self.border = border_module.FrameBorder(obstacles["border"], frame)
            field_margin = float(fit.load_profile_cached("surface")["routing"]["active_edge_clearance_mm"])
            self.x0, self.x1, self.y0, self.y1 = self.border.bounds(self.x0, self.x1, self.y0, self.y1, self.margin, field_margin)

    def _bucket(self, y: float) -> int:
        return int(math.floor((y - self._bucket_base) / self._bucket_height))

    def exit_y(self, x: float) -> Any:
        return self.exits.exit_y(x)

    def _near(self, low: float, high: float) -> list:
        found = set()
        for key in range(self._bucket(low), self._bucket(high) + 1):
            found.update(self._buckets.get(key, ()))
        return sorted(found)

    def intervals(self, y0: float, y1: float) -> list:
        """The free x-intervals ``[(a, b)]`` of the strip ``y0 <= y <= y1`` (sorted, disjoint).

        x is free when the vertical segment from (x, y0) to (x, y1) lies on the
        surface, at least the edge margin from its edge, the holes, the
        obstacles and the bends (a box margin, so a little more than the
        Euclidean one): inside the outline at the strip's middle, and no
        segment within the margin of the strip at x (an x-range of each
        segment clipped to the strip grown by the margin, grown by the margin).
        """

        key = (y0, y1)
        found = self._strips.get(key)
        if found is not None:
            return found
        margin = self.margin
        low, high = y0 - margin, y1 + margin
        middle = (y0 + y1) / 2
        crossings = []
        interiors: dict = {}
        blocked = []
        for index in self._near(low, high):
            ax, ay, bx, by, kind, group, _ = self.segments[index]
            if kind != 2 and (ay <= middle < by or by <= middle < ay):
                x = ax + (middle - ay) * (bx - ax) / (by - ay)
                if kind == 0:
                    crossings.append(x)
                else:
                    interiors.setdefault(group, []).append(x)
            clipped = _clip_x(ax, ay, bx, by, low, high)
            if clipped is not None:
                blocked.append((clipped[0] - margin, clipped[1] + margin))
        crossings.sort()
        inside = [(crossings[k], crossings[k + 1]) for k in range(0, len(crossings) - 1, 2)]
        for group in sorted(interiors):
            xs = sorted(interiors[group])
            blocked.extend((xs[k], xs[k + 1]) for k in range(0, len(xs) - 1, 2))
        found = _subtract(inside, _union(blocked))
        if len(self._strips) > 200_000:
            self._strips.clear()
        self._strips[key] = found
        return found

    def rect_free(self, x0: float, x1: float, y0: float, y1: float) -> bool:
        for a, b in self.intervals(y0, y1):
            if a <= x0 and x1 <= b:
                return True
            if a > x0:
                break
        return False

    def tail_exit(self, x0: float, x1: float, root: float, cap: float) -> Any:
        """The lowest exit y under a tail ``x0..x1`` whose root is at ``root``, or None.

        The tail runs from its root straight down across the exit: the exit
        lies below its whole width, the part on the surface is at most
        ``cap`` long, and no edge (other than the exit), hole, obstacle or
        bend comes within the edge margin of it.
        """

        lowest = self.exits.lowest_exit_y(x0, x1)
        if lowest is None or root - lowest > cap + 1e-9 or root < lowest - 1e-9:
            return None
        margin = self.margin
        low, high = lowest - margin, root + margin
        left, right = x0 - margin, x1 + margin
        for index in self._near(low, high):
            ax, ay, bx, by, _, _, exit = self.segments[index]
            if exit:
                continue
            clipped = _clip_x(ax, ay, bx, by, low, high)
            if clipped is not None and clipped[0] <= right and clipped[1] >= left:
                return None
        return lowest


def _clip_x(ax: float, ay: float, bx: float, by: float, low: float, high: float) -> Any:
    """The x-range of the segment's part within ``low <= y <= high``, or None."""

    if max(ay, by) < low or min(ay, by) > high:
        return None
    if ay == by:
        return (min(ax, bx), max(ax, bx))
    xs = []
    for y in (max(low, min(ay, by)), min(high, max(ay, by))):
        xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
    return (min(xs), max(xs))


def _union(intervals: list) -> list:
    intervals.sort()
    merged: list = []
    for a, b in intervals:
        if merged and a <= merged[-1][1]:
            if b > merged[-1][1]:
                merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def _subtract(inside: list, blocked: list) -> list:
    free = []
    k = 0
    for a, b in inside:
        start = a
        while k < len(blocked) and blocked[k][1] <= start:
            k += 1
        j = k
        while j < len(blocked) and blocked[j][0] < b:
            if blocked[j][0] > start:
                free.append((start, blocked[j][0]))
            start = max(start, blocked[j][1])
            j += 1
        if start < b:
            free.append((start, b))
    return free


# --------------------------------------------------------------------------
# The lane taper, the bottom zone and the field region of a masked candidate
# --------------------------------------------------------------------------

_TAPERS: dict = {}
_BOTTOMS: dict = {}


def taper(pitch: float, options: Mapping[str, Any], routing: str, profile: Mapping[str, Any], rows: int) -> dict:
    """``W_k`` (k = 1..rows) of the routing, its breakpoints in ``[W_1, W_1 + pitch)`` and their start slots.

    From the engine's :func:`engine.row_taper` of a plan of at least two
    rows (one row takes the contact-aligned lane, never used by a mask).
    ``taus[i][j]`` is the start slot of the (j+1)-th row from the top for the
    channel width ``breakpoints[i]``, as the engine computes it, and
    ``starts[i][j]`` the field start ``active_x`` the engine takes for the top
    j+1 rows (at most the breakpoint: the board edge lies at or inside the
    channel edge the search assumed).
    """

    key = (pitch, options["fill"], options["template"], routing, rows)
    found = _TAPERS.get(key)
    if found is None:
        design = fit.design_for(max(2, rows), 1, pitch, pitch, options, "rows_top", routing)
        widths = row_taper(design, profile)[:rows]
        step = round6(pitch)
        first = widths[0]
        points = sorted({round6(width - round6(math.floor((width - first) / step + _NOISE) * step)) for width in widths})
        points = [point for point in points if first - _NOISE <= point < first + step - _NOISE]
        taus = [[max(0, math.ceil(round6(width - point) / step - _NOISE)) for width in widths] for point in points]
        margin = float(profile["routing"]["active_edge_clearance_mm"])
        starts = []
        for slots in taus:
            running, prefix = margin, []
            for width, slot in zip(widths, slots):
                running = max(running, round6(width - round6(slot * step)))
                prefix.append(running)
            starts.append(prefix)
        found = {"widths": widths, "breakpoints": points, "taus": taus, "starts": starts}
        _TAPERS[key] = found
    return found


def bottom_model(rows: int, columns: int, pitch: float, options: Mapping[str, Any], routing: str, profile: Mapping[str, Any]) -> dict:
    """What a masked field of rows x columns needs below its floor, from the plans of the bounding field.

    Field-relative, in the search frame (Row board canonical, Column board
    mirrored): the Row board's parts depend on the field start ``a`` (the
    taper slide) and are given as rules; the Column board's are fixed.
    """

    key = (rows, columns, pitch, options["fill"], options["reader"], options["template"], routing)
    found = _BOTTOMS.get(key)
    if found is None:
        design = fit.design_for(rows, columns, pitch, pitch, options, "rows_top", routing)
        rp = row_plan(design, profile)
        cp = column_plan(design, profile)
        rules = rp["rules"]
        aw = rp["active"][2]
        cax, cay = cp["active"][0], cp["active"][1]
        envelope = cp["envelope"]
        channels = cp["channels"]
        hull_left = min(cp["tail_x"], cp["contact_x"][0] - envelope, cp["decks"][0] - envelope, cp["centers"][0] - envelope)
        hull_right = max(cp["tail_x"] + cp["tail_width"], cp["contact_x"][channels - 1] + envelope, cp["decks"][-1] + envelope, cp["centers"][-1] + envelope)
        left = min(cp["body"][0], hull_left, cp["tail_x"]) - cax
        right = max(cp["body"][2], hull_right, cp["tail_x"] + cp["tail_width"]) - cax
        found = {
            "aw": aw,
            "margin": rules.margin,
            "fillet": rules.fillet_radius,
            "row_root": rp["active"][1],
            "row_tail_width": rp["tail_width"],
            "row_contacts": tail_width(rows, rules),
            # Mirrored: x -> aw - x.
            "column_x": (aw - right, aw - left),
            "column_tail_x": (aw - (cp["tail_x"] + cp["tail_width"] - cax), aw - (cp["tail_x"] - cax)),
            "column_root": cay - cp["tail_top"],
        }
        _BOTTOMS[key] = found
    return found


def mask_digest(mask: Any) -> Any:
    """A short digest of a mask (None for the full rectangle)."""

    if mask is None:
        return None
    return hashlib.sha256(json.dumps([list(pair) for pair in mask], separators=(",", ":")).encode("ascii")).hexdigest()[:16]


def field_area(spans: Sequence, pitch: float, width: float) -> float:
    """Area of P (the crossing region: each row's crossing strip and the fillers between rows) of slot spans."""

    parts = []
    for j, (low, high) in enumerate(spans):
        parts.append(((high - low) * pitch + width) * width)
        if j:
            common = min(high, spans[j - 1][1]) - max(low, spans[j - 1][0])
            parts.append((common * pitch + width) * (pitch - width))
    return math.fsum(parts)


def polygon_area(points: Sequence) -> float:
    count = len(points)
    return abs(math.fsum(points[k][0] * points[(k + 1) % count][1] - points[(k + 1) % count][0] * points[k][1] for k in range(count))) / 2


def field_polygon(result: Mapping[str, Any], field_origin: Sequence[float]) -> list:
    """P of a masked build (the Row board's ``active_outline``) as seen from outside, in the base frame.

    Placed like the boards (:func:`surface.fit.board_outlines_base`): from
    the active region's lower-left corner, mirrored when the Row board is the
    physical top board, counter-clockwise.
    """

    board = result["boards"]["row"]
    registration = board["grid_registration"]
    grid = registration["active_region"]
    ax, ay, aw = grid["x"], grid["y"], grid["width"]
    mirrored = result["design"]["role_mapping"]["top"] == "rows"
    points = []
    for x, y in registration["active_outline"]:
        rx, ry = x - ax, y - ay
        if mirrored:
            rx = aw - rx
        points.append((rx + field_origin[0], ry + field_origin[1]))
    if mirrored:
        points.reverse()
    return points


# --------------------------------------------------------------------------
# The search
# --------------------------------------------------------------------------


class _Pool:
    """The best masked candidates found so far, per (mask, routing, role) the highest and the lowest field.

    Each role mapping keeps its own best ``size`` masks, and a role's search
    prunes on its own (:meth:`threshold`): with ``role_mapping: auto`` each
    role is searched as it is alone.  A mask found at several heights keeps
    its highest and its lowest field: the placement option takes one first
    (``far`` the highest, ``near`` the lowest), and the realize falls back
    on the other, so the count does not depend on the option.
    """

    def __init__(self, size: int) -> None:
        self.size = size
        self.items: dict = {}  # role -> {(rows, columns, digest, routing): [highest field, lowest field]}
        self._thresholds: dict = {}  # role -> threshold, until the role's next add

    def threshold(self, role: str) -> int:
        found = self._thresholds.get(role)
        if found is None:
            items = self.items.get(role, {})
            found = 0 if len(items) < self.size else sorted((held[0]["taxels"] for held in items.values()), reverse=True)[self.size - 1]
            self._thresholds[role] = found
        return found

    def add(self, candidate: dict) -> None:
        self._thresholds.pop(candidate["role"], None)
        items = self.items.setdefault(candidate["role"], {})
        key = (candidate["rows"], candidate["columns"], candidate["digest"], candidate["routing"])
        found = items.get(key, []) + [candidate]
        highest = min(found, key=lambda item: (-round(item["field_origin"][1], 6), search_rank(item)))
        lowest = min(found, key=lambda item: (round(item["field_origin"][1], 6), search_rank(item)))
        items[key] = [highest] if lowest is highest else [highest, lowest]
        if len(items) > 2 * self.size:
            # By search_rank: which masks stay does not depend on the placement option.
            kept = sorted(items.items(), key=lambda kv: search_rank(kv[1][0]))[: self.size]
            self.items[candidate["role"]] = dict(kept)

    def all(self) -> list:
        return [item for role in sorted(self.items) for held in self.items[role].values() for item in held]

    def best(self) -> list:
        return sorted(self.all(), key=lambda item: item["rank"])


class _Context:
    """What every lattice of one fit shares: options, caps, taper and bottom models, the pool."""

    def __init__(self, options: Mapping[str, Any], profile: Mapping[str, Any]) -> None:
        self.options = options
        self.profile = profile
        # The walk's caps: max_rows x max_columns, within a named reader's lines (either way round), auto the largest's.
        self.caps = reader_module.field_caps(options["reader"], options["max_rows"], options["max_columns"])
        self.rows_cap = max(rows for rows, _ in self.caps)
        self.columns_cap = max(columns for _, columns in self.caps)
        self.tail_cap = fit.TAIL_MAX_MM[options["template"]] - options["tail_extension_mm"]
        self.tail_reason = fit.tails_too_long(options["template"])
        self.pool = _Pool(MASKED_POOL)
        self.rejected: dict = {}
        self.searches = 0
        # A mask must beat this many taxels to be proposed before the rectangles (masked_candidates sets it).
        self.floor = 0

    def threshold(self, role: str) -> int:
        return max(self.floor, self.pool.threshold(role))

    def reject(self, reason: str) -> None:
        self.rejected[reason] = self.rejected.get(reason, 0) + 1


def _bands(space: FreeSpace, pitch: float, width: float, margin: float, phase_y: float) -> tuple:
    """``(Y0, bands)``: the lattice rows' y origin and each row's free intervals (actual x)."""

    origin = space.y0 + phase_y
    half = width / 2
    up = max(pitch / 2, half + margin)
    count = int(math.floor((space.y1 - origin) / pitch + _NOISE)) + 1
    bands = []
    for k in range(max(0, count)):
        y = origin + k * pitch
        bands.append(space.intervals(round(y - pitch / 2, 9), round(y + up, 9)))
    return origin, bands


def _mirror(bands: list) -> list:
    return [[(-b, -a) for a, b in reversed(intervals)] for intervals in bands]


def _search_lattice(context: _Context, lattice: dict, routing: str, tag: tuple) -> list:
    """Walk every top row and channel edge of one lattice (one side, one routing) under each of the walk's caps.

    Accepted candidates, best first: a named reader caps the walk at its
    lines, either way round (:func:`surface.reader.walk_caps`), so its
    readouts are searched as with ``max_rows`` and ``max_columns``.
    """

    model = taper(lattice["pitch"], context.options, routing, context.profile, context.rows_cap)
    role = lattice["role"]
    threshold = context.threshold(role)
    records = []
    for rows_cap, columns_cap in context.caps:
        records.extend(_walk(lattice, model, rows_cap, columns_cap, threshold))
    records.sort(key=lambda record: (-record[0], -record[1], record[3], record[2]))
    accepted = []
    taken = set()
    for count, top, floor, i0, index, ends in records:
        if count <= context.threshold(role) or len(accepted) >= ACCEPTED_PER_SEARCH:
            break
        candidate = _candidate(context, lattice, routing, tag, top, floor, i0, model, index, ends[:floor])
        if candidate is not None:
            # The same field may come from two caps' walks.
            key = (top, floor, i0, index, tuple(candidate["spans"]))
            if key in taken:
                continue
            taken.add(key)
            accepted.append(candidate)
            context.pool.add(candidate)
    return accepted


def _walk(lattice: dict, model: dict, rows_cap: int, columns_cap: int, threshold: int) -> list:
    """The walk's records ``(count, top, floor, i0, taper index, far ends)`` of one lattice under one cap."""

    pitch = lattice["pitch"]
    width = lattice["width"]
    half = width / 2
    margin = lattice["margin"]
    origin = lattice["x0"]  # lattice x of column 0 (search frame)
    bands = lattice["bands"]
    lefts = lattice["lefts"]
    widths = model["widths"]
    points = model["breakpoints"]
    taus_table = model["taus"]
    first = widths[0]
    records = []
    count_rows = len(bands)
    # An upper bound per top row: each band's most cells beyond the narrowest channel, over the rows a mask may take.
    caps = []
    for row in bands:
        most = 0
        for a, b in row:
            cells = int(math.floor((b - margin - half - origin) / pitch)) - int(math.ceil((a + first + half - origin) / pitch - 1e-12)) + 1
            if cells > most:
                most = cells
        caps.append(min(most, columns_cap))
    window = [0] * (count_rows + 1)
    for k in range(count_rows):
        window[k + 1] = window[k] + caps[k]
    for top in range(count_rows - 1, -1, -1):
        if window[top + 1] - window[max(0, top + 1 - rows_cap)] <= threshold:
            continue
        for start, end in bands[top]:
            x_out = start
            for _ in range(MAX_RESTARTS + 1):  # each restart moves the channel edge inward
                if x_out > end:
                    break
                i0 = int(math.ceil((x_out + first + half - origin) / pitch - 1e-12))
                if origin + i0 * pitch + half + margin > end:
                    break
                depth = origin + i0 * pitch - half - x_out
                index = bisect.bisect_right(points, depth + 1e-12) - 1
                if index < 0:
                    break
                taus = taus_table[index]
                limit = i0 + columns_cap - 1
                stack: list = []
                sum_e = 0
                sum_tau = 0
                ends: list = []
                previous = None
                restart = None
                for j in range(1, rows_cap + 1):
                    k = top - j + 1
                    if k < 0:
                        break
                    row = bands[k]
                    if len(row) == 1 and row[0][0] <= x_out <= row[0][1]:
                        right = row[0][1]
                    else:
                        position = bisect.bisect_right(lefts[k], x_out) - 1
                        if position < 0 or row[position][1] < x_out:
                            following = position + 1
                            if following < len(row):
                                restart = row[following][0]
                            break
                        right = row[position][1]
                    e = int(math.floor((right - margin - half - origin) / pitch))
                    if e > limit:
                        e = limit
                    s = i0 + taus[j - 1]
                    if s > e or (previous is not None and s > previous):
                        break
                    run = 1
                    while stack and stack[-1][0] >= e:
                        value, size = stack.pop()
                        sum_e -= value * size
                        run += size
                    stack.append((e, run))
                    sum_e += e * run
                    sum_tau += taus[j - 1]
                    ends.append(e)
                    previous = e
                    if j >= 2:
                        count = sum_e - j * (i0 - 1) - sum_tau
                        if count > threshold:
                            records.append((count, top, j, i0, index, ends))
                if restart is None or restart <= x_out:
                    break
                x_out = restart
    return records


def _candidate(context: _Context, lattice: dict, routing: str, tag: tuple, top: int, floor: int, i0: int, model: dict, index: int, ends: list) -> Any:
    """The masked candidate of one walk and floor, when its bottom zone and tails fit; else None."""

    options = context.options
    pitch, width, margin = lattice["pitch"], lattice["width"], lattice["margin"]
    half = width / 2
    taus = model["taus"][index]
    rows = floor
    # The floor row spans every column (its far end is the running minimum's start, below).
    columns = ends[-1] - i0 + 1
    if columns < 1 or rows < 1:
        return None
    reason = reader_module.rejection(rows, columns, options["reader"])
    if reason is not None:
        context.reject(reason)
        return None
    bottom = bottom_model(rows, columns, pitch, options, routing, context.profile)
    space = lattice["space"]
    y_floor = lattice["y0"] + (top - floor + 1) * pitch - half
    # Neither tail root may lie more than the tail cap above the exit's highest point.
    reach = space.exit_top + context.tail_cap + 1e-9
    if y_floor - bottom["row_root"] > reach or y_floor - bottom["column_root"] > reach:
        context.reject(context.tail_reason)
        return None
    start = model["starts"][index][rows - 1]
    aw = bottom["aw"]
    xb = _body_side(max(start + aw + bottom["margin"], bottom["row_contacts"]), bottom["row_tail_width"], 1.0, bottom["fillet"])
    mirrored = lattice["side"] == "right"
    left = lattice["x0"] + i0 * pitch - half  # the field's channel-side crossing edge (search frame)
    depth = max(bottom["row_root"], bottom["column_root"])
    zone_left = left + min(-start, bottom["column_x"][0])
    zone_right = left + max(xb - start, bottom["column_x"][1], bottom["row_tail_width"] - start)

    def actual(a: float, b: float) -> tuple:
        return (-b, -a) if mirrored else (a, b)

    zx0, zx1 = actual(zone_left, zone_right)
    if not space.rect_free(zx0, zx1, round(y_floor - depth, 9), round(y_floor, 9)):
        context.reject("bottom zone or fan-out leaves the surface (fill)")
        return None
    row_tail = actual(left - start, left - start + bottom["row_tail_width"])
    column_tail = actual(left + bottom["column_tail_x"][0], left + bottom["column_tail_x"][1])
    row_exit = space.tail_exit(row_tail[0], row_tail[1], y_floor - bottom["row_root"], context.tail_cap)
    column_exit = space.tail_exit(column_tail[0], column_tail[1], y_floor - bottom["column_root"], context.tail_cap)
    if row_exit is None or column_exit is None:
        context.reject("a tail misses the exit (fill)")
        return None
    # The far ends never recede going down: the running minimum from the floor up.
    lowest = [0] * rows
    current = ends[-1]
    for j in range(rows - 1, -1, -1):
        current = min(current, ends[j])
        lowest[j] = current
    spans = [(taus[j], lowest[j] - i0) for j in range(rows)]
    full = all(span == (0, columns - 1) for span in spans)
    field_x = -(left + aw) if mirrored else left
    mask = None if full else tuple((columns - high, columns - low) for low, high in spans)
    active = 0
    for low, high in spans:
        active += high - low + 1
    height = y_floor + half
    return {
        "rows": rows,
        "columns": columns,
        "pitch_x": pitch,
        "pitch_y": pitch,
        "grid_pitch": pitch,
        "role": lattice["role"],
        "routing": routing,
        "spans": spans,
        "mask": mask,
        "digest": mask_digest(mask),
        "taxels": active,
        "field_origin": (field_x, y_floor),
        "rank": masked_rank(options, pitch, width, lattice["frame"].angle_deg, routing, lattice["role"], spans, height, tag, i0),
        "tag": tag,
        "i0": i0,
        "angle_deg": lattice["frame"].angle_deg,
        "side": lattice["side_record"],
        "frame": lattice["frame"],
        "region": space,
        "lattice": lattice,
        "taper_index": index,
        "taper_rows": context.rows_cap,
        "options": options,
        "fill": True,
    }


def masked_rank(options: Mapping[str, Any], pitch: float, width: float, angle: float, routing: str, role: str, spans: Sequence,
                height: float, tag: tuple, i0: int) -> tuple:
    """A masked candidate's rank in the merged pool (smaller first; see :func:`_rectangle_rank`).

    ``(-taxels (max_area: -area of P), -pitch, 0, |angle|, default before
    tight, rows_top before columns_top, 1 (masked; 0 for a full mask),
    positions (a denser readout first), the placement (far: the higher
    field first), the lattice, its channel-most column)``.
    """

    rows, columns = len(spans), max(high for _, high in spans) + 1
    active = 0
    for low, high in spans:
        active += high - low + 1
    full = active == rows * columns
    primary = -field_area(spans, pitch, width) if options["objective"] == "max_area" else -active
    placement = options["placement"]
    place_term = -height if placement == "far" else (height if placement == "near" else 0.0)
    return (
        primary,
        -pitch,
        0.0,
        abs(angle),
        0 if routing == "default" else 1,
        0 if role == "rows_top" else 1,
        0 if full else 1,
        rows * columns,
        round(place_term, 6),
        tag[0],
        tag[1],
        i0,
    )


def _lattices(space: FreeSpace, side_record: Mapping[str, Any], frame: Any, pitch: float, width: float, margin: float,
              roles: Sequence[str], phases_x: Sequence, phases_y: Sequence, bands_cache: dict) -> list:
    """The lattices of one frame: per y phase (bands), x phase and role."""

    found = []
    for phase_y in phases_y:
        key = (pitch, phase_y)
        if key not in bands_cache:
            y0, bands = _bands(space, pitch, width, margin, phase_y)
            mirrored = _mirror(bands)
            bands_cache[key] = (y0, bands, [[a for a, _ in row] for row in bands], mirrored, [[a for a, _ in row] for row in mirrored])
        y0, bands, lefts, mirrored, mirrored_lefts = bands_cache[key]
        for phase_x in phases_x:
            x0 = space.x0 + phase_x
            for role in roles:
                side = "right" if role == "rows_top" else "left"
                found.append({
                    "space": space, "frame": frame, "side_record": side_record, "pitch": pitch, "width": width, "margin": margin,
                    "side": side, "role": role, "y0": y0, "x0": -x0 if side == "right" else x0,
                    "bands": mirrored if side == "right" else bands, "lefts": mirrored_lefts if side == "right" else lefts,
                    "phase": (phase_x, phase_y),
                })
    return found


def _phase(value: float, pitch: float) -> float:
    return round(value - math.floor(value / pitch + _NOISE) * pitch, 6) % round(pitch, 6)


def _coarse_phases(space: FreeSpace, pitch: float, width: float, margin: float, seeds: Sequence) -> tuple:
    """Stage-1 phases: 0 and p/2, the far sides and the top row snapped to the free extremes, the rectangles' phases."""

    half = width / 2
    edge = space.margin
    xs = [0.0, round(pitch / 2, 6), _phase(space.x1 - edge - half - margin - space.x0, pitch), _phase(edge + half + margin, pitch)]
    ys = [0.0, round(pitch / 2, 6), _phase(space.y1 - edge - half - margin - space.y0, pitch)]
    for field_x, field_y in seeds:
        xs.append(_phase(field_x + half - space.x0, pitch))
        ys.append(_phase(field_y + half - space.y0, pitch))
    return sorted(set(xs)), sorted(set(ys))


def _fine_phases(best: tuple, pitch: float) -> tuple:
    """Stage-2 phases: quarters of the pitch, and eighths around the best phase."""

    xs = {round(k * pitch / 4, 6) for k in range(4)}
    ys = {round(k * pitch / 4, 6) for k in range(4)}
    for k in (-1, 1):
        xs.add(_phase(best[0] + k * pitch / 8, pitch))
        ys.add(_phase(best[1] + k * pitch / 8, pitch))
    xs.add(best[0])
    ys.add(best[1])
    return sorted(xs), sorted(ys)


def masked_candidates(chart: Any, bases: Sequence, options: Mapping[str, Any], profile: Mapping[str, Any], obstacles: Mapping[str, Any],
                      rectangles: Sequence, per_base: list) -> tuple:
    """The masked candidates of a fit (best first) and the rejection counts of their search.

    The lattices searched do not depend on the placement option (the
    rectangles' phases are taken placed far, :func:`seed_origins`, and the
    frames and the pool by :func:`search_rank`, which leaves the placement
    out; a mask keeps its highest and its lowest field), and each
    role mapping gets its own turned exits, fine phases and lattices of the
    other routing, so ``role_mapping: auto`` searches all that either role
    alone does.
    """

    context = _Context(options, profile)
    if context.rows_cap < 2 or context.columns_cap < 1:
        return [], context.rejected
    if options["objective"] != "max_area":
        # A mask ranks before a rectangle only with more taxels: below the rectangles that will be
        # proposed (two spare for a rectangle that does not realize), it would never be shown.
        counts = []
        for candidate in sorted(rectangles, key=lambda c: c["rank"]):
            shape = (candidate["rows"], candidate["columns"])
            if all(shape != seen for seen, _ in counts):
                counts.append((shape, candidate["rows"] * candidate["columns"]))
        if len(counts) >= options["proposals"] + 2:
            context.floor = counts[options["proposals"] + 1][1]
    roles = ["rows_top", "columns_top"] if options["role_mapping"] == "auto" else [options["role_mapping"]]
    routings = ["default", "tight"] if options["routing"] == "auto" else [options["routing"]]
    first_routing = "tight" if "tight" in routings else routings[0]
    pitches = _pitches(options, rectangles)
    spaces: dict = {}
    bands_cache: dict = {}
    # The best candidate of each (exit, turn, role, pitch) searched, by search_rank.
    frame_best: dict = {}

    def space_of(side: Mapping[str, Any], angle: float) -> tuple:
        key = (str(side["index"]), angle)
        if key not in spaces:
            frame = fit.BaseFrame(side, angle)
            spaces[key] = (FreeSpace(chart, frame, obstacles, options["edge_margin_mm"], side["edges"]), frame)
            bands_cache[key] = {}
        return spaces[key][0], spaces[key][1], bands_cache[key]

    def seeds(side: Mapping[str, Any], angle: float, role: str) -> list:
        found = [c for c in rectangles if c["side"]["index"] == side["index"] and c["angle_deg"] == angle and c["role"] == role]
        found.sort(key=lambda c: c["rank"])
        origins = []
        for candidate in found[:3]:
            origins.extend(seed_origins(candidate, options, profile))
        return origins

    def run(side: Mapping[str, Any], angle: float, pitch: float, phases: tuple, routing: str, stage: int, only_roles: Sequence[str]) -> list:
        space, frame, cache = space_of(side, angle)
        width = fit._electrode(pitch, options["fill"])
        margin = float(profile["routing"]["active_edge_clearance_mm"])
        lattices = _lattices(space, side, frame, pitch, width, margin, only_roles, phases[0], phases[1], cache)
        accepted = []
        for number, lattice in enumerate(lattices):
            context.searches += 1
            found = _search_lattice(context, lattice, routing, (stage, number))
            accepted.extend(found)
            key = (str(side["index"]), angle, lattice["role"], pitch)
            if found:
                best = min(found, key=search_rank)
                held = frame_best.get(key)
                if held is None or search_rank(best) < search_rank(held[0]):
                    frame_best[key] = (best, side, angle, lattice["role"], lattice["phase"], pitch)
        return accepted

    totals: dict = {}

    def tally(side: Mapping[str, Any], angle: float, found: Sequence) -> None:
        totals[(str(side["index"]), angle)] = totals.get((str(side["index"]), angle), 0) + len(found)

    margin = float(profile["routing"]["active_edge_clearance_mm"])
    # The frames of the further pitches (max_taxels, max_area): each role's best frames at the first pitch.
    further: Any = None
    for pitch in pitches:
        width = fit._electrode(pitch, options["fill"])
        if width > pitch - fit.MIN_GAP_MM + 1e-9:
            continue
        if further is not None:
            for role in roles:
                for side, angle in further[role]:
                    space, _, _ = space_of(side, angle)
                    phases = _coarse_phases(space, pitch, width, margin, seeds(side, angle, role))
                    tally(side, angle, run(side, angle, pitch, phases, first_routing, 1, [role]))
            continue
        # Stage 1: every exit unturned (and, with rotation auto, each role's two best exits turned), each
        # role with the phases of its own rectangles.
        for role in roles:
            side_best = []
            for order, side in enumerate(bases):
                space, _, _ = space_of(side, 0.0)
                phases = _coarse_phases(space, pitch, width, margin, seeds(side, 0.0, role))
                found = run(side, 0.0, pitch, phases, first_routing, 1, [role])
                tally(side, 0.0, found)
                if found:
                    side_best.append((min(search_rank(c) for c in found), order, side))
            if options["rotation"] == "auto":
                for _, _, side in sorted(side_best, key=lambda item: (item[0], item[1]))[:2]:
                    for angle in fit.ROTATION_STEPS_DEG:
                        space, _, _ = space_of(side, angle)
                        phases = _coarse_phases(space, pitch, width, margin, seeds(side, angle, role))
                        tally(side, angle, run(side, angle, pitch, phases, first_routing, 1, [role]))
        further = {}
        for role in roles:
            ranked = sorted((item for item in frame_best.values() if item[3] == role), key=lambda item: search_rank(item[0]))
            further[role] = [(item[1], item[2]) for item in ranked[:FINE_FRAMES]]
    # Stage 2: finer phases on each role's best (frame, pitch) pairs.
    for role in roles:
        best_frames = sorted((item for item in frame_best.values() if item[3] == role), key=lambda item: search_rank(item[0]))[:FINE_FRAMES]
        for best, side, angle, _, phase, pitch in best_frames:
            tally(side, angle, run(side, angle, pitch, _fine_phases(phase, pitch), first_routing, 2, [role]))
    # The other routing on each role's best lattices (default traces rank first at an equal count).
    for routing in routings:
        if routing == first_routing:
            continue
        ranked = sorted(context.pool.all(), key=search_rank)
        for role in roles:
            done = set()
            for candidate in ranked:
                lattice = candidate["lattice"]
                if lattice["role"] != role:
                    continue
                key = (id(lattice["space"]), lattice["phase"], lattice["pitch"])
                if key in done:
                    continue
                done.add(key)
                if len(done) > DEFAULT_ROUTING_LATTICES:
                    break
                context.searches += 1
                found = _search_lattice(context, lattice, routing, (3, len(done)))
                tally(candidate["side"], candidate["angle_deg"], found)
    for entry in per_base:
        key = (str(entry["side"]), entry["angle_deg"])
        if key in totals:
            entry["masked_candidates"] = totals.pop(key)
    for (side, angle), count in sorted(totals.items()):
        index = next((s["index"] for s in bases if str(s["index"]) == side), side)
        chord = next((s["chord_mm"] for s in bases if str(s["index"]) == side), None)
        per_base.append({"side": index, "angle_deg": angle, "chord_mm": chord, "candidates": 0, "masked_candidates": count})
    return context.pool.best(), context.rejected


def search_rank(candidate: Mapping[str, Any]) -> tuple:
    """A masked candidate's rank without its placement term: how the search picks its frames and lattices.

    The placement option (far, near, center) only chooses among fields of
    equal rank otherwise; it never changes which lattices are searched.
    """

    rank = candidate["rank"]
    return rank[:8] + rank[9:]


def seed_origins(candidate: Mapping[str, Any], options: Mapping[str, Any], profile: Mapping[str, Any]) -> list:
    """A rectangle candidate's field origins at :data:`SEED_PLACEMENTS`: the masked search's seeds.

    The rectangle search places a field by the placement option; the masked
    search takes the phases of the far placement whatever the option (its
    walk starts at the top row), so its lattices do not depend on it.  The
    option then chooses among the fields of equal rank (each mask keeps its
    highest and its lowest field, :class:`_Pool`) the one farthest from or
    nearest to the exit.  (Seeds placed near as well found the same counts
    on the review's 33 meshes, for 10-20% more search.)
    """

    origins = []
    for placement in SEED_PLACEMENTS:
        if placement == options["placement"]:
            origins.append(candidate["field_origin"])
            continue
        item = fit.evaluate(candidate["region"], candidate["rows"], candidate["columns"], candidate["pitch_x"], candidate["pitch_y"],
                            dict(options, placement=placement), candidate["role"], candidate["routing"], profile, {})
        origins.append(candidate["field_origin"] if item is None else item["field_origin"])
    return origins


def _pitches(options: Mapping[str, Any], rectangles: Sequence) -> list:
    """The pitches of the masked search.

    ``fixed_pitch``: the pitch.  ``max_taxels``: the smallest pitch and the
    next three 0.01 mm steps (the count is not monotone in the pitch).
    ``max_area``: the grid pitches of the four best rectangles.  The first
    pitch is searched on every frame, the others on each role's
    :data:`FINE_FRAMES` best frames of the first.
    """

    if options["objective"] == "fixed_pitch":
        return [round(options["pitch_mm"], 3)]
    low = round(options["min_pitch_mm"], 3)
    if options["objective"] == "max_taxels":
        return [round(low + k * fit.PITCH_STEP_MM, 3) for k in range(4) if low + k * fit.PITCH_STEP_MM <= fit.MAX_PITCH_MM + 1e-9]
    found = []
    for candidate in sorted(rectangles, key=lambda c: c["rank"]):
        pitch = round(candidate.get("grid_pitch", candidate["pitch_x"]), 3)
        if pitch not in found:
            found.append(pitch)
        if len(found) >= fit.MAX_AREA_TURNED_PITCHES:
            break
    return found or [low]


# --------------------------------------------------------------------------
# The fit with shape: fill
# --------------------------------------------------------------------------


def fit_chart_fill(mesh: Any, chart: Any, sides: Sequence, bases: Sequence, options: Mapping[str, Any], cache: Any = None) -> dict:
    """:func:`surface.fit.fit_chart` with masked fields: the rectangles and the masks, merged and realized best first."""

    profile = fit.load_profile_cached(options["template"])
    obstacles = fit.surface_obstacles(mesh, chart, options)
    rectangles = []
    rejected: dict = {}
    per_base: list = []

    def run(side: Mapping[str, Any], angle: float, pitches: Any = None) -> list:
        frame = fit.BaseFrame(side, angle)
        region = fit.UsableRaster(chart, frame, obstacles, options["edge_margin_mm"], side["edges"])
        found = fit.search(region, options, profile, rejected, pitches)
        per_base.append({"side": side["index"], "angle_deg": angle, "chord_mm": side["chord_mm"], "candidates": len(found)})
        for item in found:
            item["side"] = side
            item["frame"] = frame
            item["region"] = region
        return found

    # The rectangles, as surface.fit.fit_chart searches them ("never worse").
    best_per_side = []
    for side in bases:
        found = run(side, 0.0)
        rectangles.extend(found)
        if found:
            best_per_side.append((found[0]["rank"], len(best_per_side), side, found))
    if options["rotation"] == "auto":
        for _, _, side, found in sorted(best_per_side, key=lambda item: (item[0], item[1]))[:2]:
            pitches = sorted({c["grid_pitch"] for c in found[: fit.MAX_AREA_TURNED_PITCHES]}) if options["objective"] == "max_area" else None
            for angle in fit.ROTATION_STEPS_DEG:
                rectangles.extend(run(side, angle, pitches))
    masked, masked_rejected = masked_candidates(chart, bases, options, profile, obstacles, rectangles, per_base)
    for reason, count in masked_rejected.items():
        rejected[reason] = rejected.get(reason, 0) + count
    pool = [(_rectangle_rank(c), c) for c in rectangles] + [(c["rank"], c) for c in masked]
    pool.sort(key=lambda item: item[0])
    # (rank, order, candidate): a peeled candidate goes back in at its own rank.
    queue = [(rank, order, candidate) for order, (rank, candidate) in enumerate(pool)]
    proposals = []
    shapes = set()
    seen = set()
    attempts = 0
    index = 0
    while index < len(queue):
        candidate = queue[index][2]
        index += 1
        if attempts >= MAX_REALIZE_ATTEMPTS_FILL:
            break
        # One masked proposal per readout (masks of one readout differ by a few cells), and none that an
        # earlier proposal beats or equals in taxels on no more Row and Column lines.
        shape = proposal_shape(candidate["rows"], candidate["columns"], candidate["taxels"], candidate.get("mask"))
        if shape in shapes or dominated(candidate["rows"], candidate["columns"], candidate["taxels"], proposals):
            continue
        key = (candidate["side"]["index"], candidate["angle_deg"], *shape, candidate["pitch_x"], candidate["pitch_y"], candidate["role"],
               candidate["routing"], tuple(round(v, 6) for v in candidate["field_origin"]))
        if key in seen:
            continue
        seen.add(key)
        attempts += 1
        if candidate.get("fill"):
            proposal, peeled = realize_masked(candidate, chart, obstacles, options, profile, cache, rejected)
            if peeled is not None:
                bisect.insort(queue, (peeled["rank"], len(queue), peeled), index)
        else:
            proposal = fit.realize(candidate, chart, obstacles, options, profile, cache, rejected)
        if proposal is not None:
            metrics = proposal["metrics"]
            found = proposal_shape(metrics["rows"], metrics["columns"], metrics["taxels"], design_mask(proposal["design"]))
            if found in shapes or dominated(metrics["rows"], metrics["columns"], metrics["taxels"], proposals):
                continue
            shapes.add(found)
            shapes.add(shape)
            proposal["rank"] = len(proposals) + 1
            proposals.append(proposal)
        if len(proposals) >= options["proposals"]:
            break
    if not proposals:
        raise SurfaceError(
            "E_SURFACE_NO_FIT",
            "No sensor design fits the selected surface with these settings: " + fit._reasons(rejected),
            rejected=fit._rejected_list(rejected),
            bases=per_base,
        )
    return {
        "ok": True,
        "format": fit.FIT_FORMAT,
        "proposals": proposals,
        "bases": per_base,
        "rejected": fit._rejected_list(rejected),
        "obstacles": {k: len(v) for k, v in obstacles.items()},
    }


def proposal_shape(rows: int, columns: int, taxels: int, mask: Any) -> tuple:
    """The key of one proposal: the readout and whether the field is masked (one mask per readout).

    ``taxels`` is not part of it: two masks of one readout differ by a few
    cells, and the better one comes first.
    """

    return (rows, columns, mask is not None)


def dominated(rows: int, columns: int, taxels: int, proposals: Sequence) -> bool:
    """Whether a proposal so far has at least ``taxels`` taxels on no more Row lines and no more Column lines.

    Such a field would add nothing to the list: the earlier one is as good
    in every respect a reader sees.  A rectangle is never dominated (a mask
    has fewer taxels than its readout's positions).
    """

    for proposal in proposals:
        metrics = proposal["metrics"]
        if metrics["taxels"] >= taxels and metrics["rows"] <= rows and metrics["columns"] <= columns:
            return True
    return False


def _rectangle_rank(candidate: Mapping[str, Any]) -> tuple:
    """A rectangle's rank in the merged pool: its own rank with the masked candidates' keys spliced in.

    ``(primary, -pitch, |pitch_x - pitch_y|, |angle|, routing, role, 0 (no
    mask), positions, 0.0, -slack, rows, columns)``; a mask with as many
    taxels at the same pitch, angle, routing and role ranks after it.
    """

    rank = candidate["rank"]
    candidate.setdefault("taxels", candidate["rows"] * candidate["columns"])
    return (*rank[:6], 0, candidate["rows"] * candidate["columns"], 0.0, *rank[6:])


# --------------------------------------------------------------------------
# Realize a masked candidate: generate, check the real outlines, peel and retry
# --------------------------------------------------------------------------


def realize_masked(candidate: Mapping[str, Any], chart: Any, obstacles: Mapping[str, Any], options: Mapping[str, Any], profile: Mapping[str, Any],
                   cache: Any, rejected: dict) -> tuple:
    """Generate a masked candidate and check its real outlines: ``(proposal, None)``, ``(None, peeled)`` or ``(None, None)``.

    A candidate whose real outline leaves the surface is peeled
    (:func:`peel`) at most :data:`PEEL_RETRIES` times; the peeled candidate
    has fewer taxels, so the fit ranks it again among the others.
    """

    outcome = _realize_once(candidate, chart, obstacles, options, profile, cache)
    if isinstance(outcome, dict):
        return outcome, None
    reason, point = outcome
    peeled = None
    if point is not None and candidate.get("peels", 0) < PEEL_RETRIES:
        peeled = peel(candidate, point, profile)
    if peeled is None:
        rejected[reason] = rejected.get(reason, 0) + 1
        return None, None
    peeled["peels"] = candidate.get("peels", 0) + 1
    return None, peeled


def _realize_once(candidate: Mapping[str, Any], chart: Any, obstacles: Mapping[str, Any], options: Mapping[str, Any], profile: Mapping[str, Any],
                  cache: Any) -> Any:
    """A proposal, or ``(reason, failure point or None)``."""

    region = candidate["region"]
    frame = candidate["frame"]
    field_x, field_y = candidate["field_origin"]
    extension = options["tail_extension_mm"]
    role = candidate["role"]
    rows, columns, pitch = candidate["rows"], candidate["columns"], candidate["pitch_x"]
    mask = candidate["mask"]
    probe = fit.design_for(rows, columns, pitch, pitch, options, role, candidate["routing"], mask=mask)
    try:
        extent = fit.stack_extent(probe, profile)
    except ValueError:
        return ("the mask is outside the straight classes (fill)", None)

    def run_to_base(tail_x: tuple, root_depth: float) -> float:
        lowest = region.exits.lowest_exit_y(field_x + tail_x[0], field_x + tail_x[1])
        if lowest is None:
            return math.inf
        return field_y - root_depth - lowest

    row_run = run_to_base(extent["row_tail_x"], extent["row_root"])
    column_run = run_to_base(extent["column_tail_x"], extent["column_root"])
    if math.inf in (row_run, column_run):
        return ("a tail misses the base edge", None)
    minimum = fit.TAIL_MIN_MM[options["template"]]
    row_tail = round(max(minimum, math.ceil((row_run + extension) * 1000) / 1000), 3)
    column_tail = round(max(minimum, math.ceil((column_run + extension) * 1000) / 1000), 3)
    tails = (row_tail, column_tail) if role == "rows_top" else (column_tail, row_tail)
    if max(tails) > fit.TAIL_MAX_MM[options["template"]] + 1e-9:
        return (fit.tails_too_long(options["template"]), None)
    design = fit.design_for(rows, columns, pitch, pitch, options, role, candidate["routing"], tails, mask=mask)
    result = generate_design(design, cache=cache)
    if not result["ok"]:
        codes = sorted({issue["code"] for issue in result["validation"]["errors"]})
        return ("engine rejected the design (" + ", ".join(codes[:3]) + ")", None)
    outlines = fit.board_outlines_base(result, (field_x, field_y))
    roots = fit.tail_roots_base(result, (field_x, field_y))
    clearance = fit.check_containment(outlines, region, frame, chart, obstacles, options["edge_margin_mm"], tail_roots=roots)
    if clearance is None:
        point = containment_failure(outlines, region, frame, obstacles, options["edge_margin_mm"], roots)
        return ("real outline leaves the surface", point)
    manifest = result["manifest"]
    registration = result["boards"]["row"]["grid_registration"]
    aw, ah = extent["field"]
    area = chart.stats["area_mm2"]
    masked = design_mask(result["design"]) is not None
    region_area = polygon_area(outlines["field"]) if masked else aw * ah
    active = registration["active_taxel_count"] if masked else rows * columns
    placement = {
        "base_side": candidate["side"]["index"],
        "base_kind": candidate["side"].get("kind", "side"),
        "exit_edges": sorted(region.exit_edges),
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
            "rows": rows,
            "columns": columns,
            "taxels": active,
            "pitch_x_mm": pitch,
            "pitch_y_mm": pitch,
            "field_mm": [round(aw, 6), round(ah, 6)],
            "field_coverage": round(region_area / area, 6) if area else 0.0,
            "stack_width_mm": round(extent["width"], 6),
            "row_tail_mm": row_tail,
            "column_tail_mm": column_tail,
            "min_clearance_mm": round(clearance, 6),
            "role_mapping": role,
            "routing": candidate["routing"],
            "angle_deg": candidate["angle_deg"],
            "positions": rows * columns,
            "sampled": round(active / (rows * columns), 6),
            "mask_class": result["boards"]["row"]["construction"].get("mask_class") if masked else None,
            "reader": reader_module.of_readout(rows, columns, options["reader"]),
        },
        "outlines_uv": {name: [[round(c, 6) for c in frame.to_chart(p)] for p in pts] for name, pts in outlines.items()},
    }


def containment_failure(outlines: Mapping[str, Sequence], region: Any, frame: Any, obstacles: Mapping[str, Any], margin: float,
                        tail_roots: Mapping[str, float]) -> Any:
    """Where a board leaves the surface (base frame): the first offending point, or None when none is found.

    The checks of :func:`surface.fit.check_containment` in its order: a
    vertex off the surface, a part beyond the exit above its tail root (the
    lowest board point is returned: below the floor), an edge crossing the
    outline or a bend, an obstacle, and the corner nearest a wall closer
    than the edge margin.
    """

    context = fit._containment_context(region, frame, obstacles)
    outline = region.outline
    for name in ("row", "column"):
        polygon = list(outlines[name])
        flags = [point_in_polygon(p, outline) for p in polygon]
        for p, flag in zip(polygon, flags):
            if not flag:
                y = region.exit_y(p[0])
                if y is None or p[1] > y + 1e-6:
                    return p
        if not fit._crosses_below(polygon, flags, tail_roots[name] + 1e-6, context["exit_index"]):
            return min(polygon, key=lambda q: (q[1], q[0]))
        for k in range(len(polygon)):
            a, b = polygon[k - 1], polygon[k]
            for index in (context["edges"], context["bend_index"]):
                for c, d in index.near(a, b, 0.0):
                    if segments_intersect(a, b, c, d):
                        return _crossing(a, b, c, d)
        for obstacle, _ in context["obstacle_polygons"]:
            for q in obstacle:
                if point_in_polygon(q, polygon):
                    return q
            for k in range(len(polygon)):
                for m in range(len(obstacle)):
                    if segments_intersect(polygon[k - 1], polygon[k], obstacle[m - 1], obstacle[m]):
                        return _crossing(polygon[k - 1], polygon[k], obstacle[m - 1], obstacle[m])
    if margin > 0 and context["clear_index"].segments:
        worst = None
        for name in ("row", "column"):
            for p in outlines[name]:
                if not point_in_polygon(p, outline):
                    continue
                distance = context["clear_index"].point_distance(p, margin)
                if distance < margin - 1e-6 and (worst is None or distance < worst[0]):
                    worst = (distance, p)
        if worst is not None:
            return worst[1]
    return None


def _crossing(a, b, c, d) -> tuple:
    dx, dy = b[0] - a[0], b[1] - a[1]
    fx, fy = d[0] - c[0], d[1] - c[1]
    det = dx * fy - dy * fx
    if det == 0:
        return tuple(a)
    t = min(max(((c[0] - a[0]) * fy - (c[1] - a[1]) * fx) / det, 0.0), 1.0)
    return (a[0] + dx * t, a[1] + dy * t)


def peel(candidate: Mapping[str, Any], point: Sequence[float], profile: Mapping[str, Any]) -> Any:
    """The candidate less the cell nearest a failure point, or None.

    A point below the floor (the bottom zone, the tails) rejects the
    candidate; above the field it drops the top row; beside the field on
    its far side or over it, the far-end cell of the nearest row goes (and
    the rows above recede with it); on the channel side the top row goes.
    Start slots follow the lane taper of the new row order.
    """

    pitch = candidate["pitch_x"]
    lattice = candidate["lattice"]
    width = lattice["width"]
    half = width / 2
    margin = lattice["margin"]
    spans = [list(span) for span in candidate["spans"]]
    rows, columns = candidate["rows"], candidate["columns"]
    field_x, field_y = candidate["field_origin"]
    aw = (columns - 1) * pitch + width
    ah = (rows - 1) * pitch + width
    fx, fy = point[0] - field_x, point[1] - field_y
    mirrored = lattice["side"] == "right"
    sx = aw - fx if mirrored else fx  # search frame: the channel on the left, slot 0 at 0
    if fy < -margin - 1e-9:
        return None
    drop_top = fy > ah + margin or sx < 0
    if not drop_top:
        # The row whose dilated box (with its fillets) reaches the point and whose far end is nearest it.
        reach = half + margin + float(profile["outline"]["outline_fillet_radius_mm"]) + 1e-6
        near = [j for j in range(1, rows + 1) if abs(fy - ((rows - j) * pitch + half)) <= reach]
        if not near:
            return None
        j = min(near, key=lambda r: (abs(sx - (spans[r - 1][1] * pitch + width + margin)), r))
        low, high = spans[j - 1]
        spans[j - 1][1] = high - 1
        if spans[j - 1][1] < low:
            if j != 1:
                return None
            drop_top = True
            spans[j - 1][1] = high
        else:
            for i in range(j - 1):
                spans[i][1] = min(spans[i][1], spans[j - 1][1])
    if drop_top:
        spans = spans[1:]
        rows -= 1
        if rows < 2:
            return None
        # The lane taper of the new row order, for the same channel width: the start slots move up a rank.
        model = taper(pitch, candidate["options"], candidate["routing"], profile, candidate["taper_rows"])
        depth = model["breakpoints"][candidate["taper_index"]]
        step = round6(pitch)
        for j in range(rows):
            spans[j][0] = max(0, math.ceil(round6(model["widths"][j] - depth) / step - _NOISE))
    for j in range(rows):
        if spans[j][0] > spans[j][1] or (j and spans[j][0] > spans[j - 1][1]):
            return None
    new_columns = max(high for _, high in spans) + 1
    if new_columns < 1 or any(low < 0 for low, _ in spans) or min(low for low, _ in spans) != 0:
        return None
    shift = columns - new_columns
    full = all(tuple(span) == (0, new_columns - 1) for span in spans)
    mask = None if full else tuple((new_columns - high, new_columns - low) for low, high in spans)
    active = 0
    for low, high in spans:
        active += high - low + 1
    peeled = dict(candidate)
    spans = [tuple(span) for span in spans]
    peeled.update(
        rows=rows,
        columns=new_columns,
        spans=spans,
        mask=mask,
        digest=mask_digest(mask),
        taxels=active,
        field_origin=(field_x + shift * pitch if mirrored else field_x, field_y),
        rank=masked_rank(candidate["options"], pitch, width, candidate["angle_deg"], candidate["routing"], candidate["role"], spans,
                         field_y + half, candidate["tag"], candidate["i0"]),
    )
    return peeled
